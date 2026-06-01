#!/usr/bin/env python3
"""Build local Dennis Agent runtime snapshots.

Currently supports `--mode full_runtime`. The builder copies only files listed
in `runtime_required_file_manifest_v1.yaml`, skips excluded paths, and writes a
runtime-local AGENTS.md plus RUNTIME_MANIFEST.md.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = REPO_ROOT / "computer_use_poc" / "runtime_required_file_manifest_v1.yaml"
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "outputs" / "full_runtime"


FULL_RUNTIME_AGENTS = """# Dennis Risk Agent Full Runtime

当前目录是 `full_runtime`，不是 preview，不是 minimal guard，也不是 contract checker。

## Runtime Goal

本目录用于在本地模拟线上真实 dennis-risk-agent 用户体感。裸问单 case 风控问题时，默认按 dennis-risk-agent runtime 执行：先做路由和 source plan，再按已登记只读 source 采集 evidence，最后输出用户可读判断。

## Default Inference

- 用户给纯数字 ID，且上下文是 case / ATO / 账号安全 / 策略命中 / 用户风险研判时，默认按 `user_id_candidate` 处理。
- 发生实体类型推断时，`routing_metadata.boundary_flags` 必须包含 `entity_type_inferred`，并输出 confidence 与 caveat。
- 只有用户明确提到 sourceId / eventId，或上下文强匹配，才推断 `source_id_candidate` / `event_id_candidate`。
- 用户未给时间窗时，按 source playbook / default window 做 bounded_time_range inference，并标 `time_window_inferred=true`。
- 默认窗口不代表全量历史，不得把默认窗口 no_data 当全量无风险结论。
- 不要因缺少实体类型或时间窗就机械 blocked；先做合理推断，再标 caveat 和 missing_evidence。

## Explicit Source

- 策略命中问题属于 explicit source，不能静默跳过。
- 用户明确问策略命中、RCP / 天师、被哪些策略拦、eventId 为什么被阻止时，策略 source 是 explicit target source。
- explicit target source 不得因其他 source 已完成或字段缺省被静默跳过。
- 544963630 类问题默认 `entity_type=user_id_candidate`、`time_window_inferred=true`，并尝试 tianshi_strategy_hit / rcp_event_list 只读 source；失败进入 source_quality。

## Source Failure Policy

- source 失败必须进入 `source_quality`。
- `no_data` / `blocked` / `timeout` / `auth_failed` / `parse_error` / `tool_gap` 不能作为无风险反证。
- source 失败后输出 partial evidence card 和 next_action，不裸 timeout。

## Controlled Case Execution

- 执行类风险 case 必须使用 `python3 computer_use_poc/runtime_case_execution_runner.py --task ato_single_case --user-id <user_id> --mode dry_run|live --format json`。
- live mode 只能调用本机 browser-backed `/actions/batch` 或 `/actions/multi_source_plan`，不得直接调用平台 URL。
- `sso_session_runner`、`archives_profile_runner`、Weapon runner、单独 `browser_backed_service_client --action`、curl 和 ad-hoc browser fetch 只允许 debug / manual diagnostic / unit test，不得作为 case execution fallback。
- `body_missing`、`body_truncated`、`response_too_large`、`platform_not_enabled`、`auth_failed`、`timeout`、`platform_error`、`parse_error`、`service_unavailable` 进入 Dennis-generated source_quality_matrix / missing_evidence，不触发旧 runner fallback。

## Safety Boundary

- 不读取 source repo 的 `run_logs/**`。
- 不读取 source repo 的历史 `outputs/**` 或 sibling output directories。
- 不读取 `.ks_sso/**`。
- 不读取 `TOOLS.md`。
- 不读取 old patch / local-file-in-chat。
- 不追逐未列入 `RUNTIME_MANIFEST.md` 的旧依赖。
- 不主动搜索 `skills/**` 或旧 runtime summaries，除非该路径已复制进本目录并列入 `RUNTIME_MANIFEST.md`。
- 不 debug 认证 / SmartSSOSession / sso_session_runner。
- 不手拼 Cookie / Header。
- 不访问未登记 source。
- DataAgent / Hive 仍需逐次授权；没有本次明确授权时只输出 query plan。

## Output Policy

1. 先输出用户可读的一句话判断或当前状态。
2. 再输出 evidence card。
3. 再输出 source_completion_matrix / source_quality。
4. 普通用户回答默认不输出完整 `routing_metadata` YAML。

完整 `routing_metadata` 只允许在 debug / run log / regression / 用户明确要求内部过程字段时输出。
内部记录仍可保留 route / capability / execution_mode / evidence_mode / source_quality /
sensitive_output / direct_tool_bypass 等字段约束，但不得污染普通用户正文。
"""


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if value in {"true", "True"}:
        return True
    if value in {"false", "False"}:
        return False
    if value in {"null", "None", "~"}:
        return None
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    return value


def simple_manifest_load(text: str) -> dict[str, Any]:
    data: dict[str, Any] = {}
    current_section: str | None = None
    current_key: str | None = None

    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        stripped = line.strip()
        if not stripped:
            continue
        indent = len(line) - len(line.lstrip(" "))

        if indent == 0 and stripped.endswith(":"):
            current_section = stripped[:-1]
            data[current_section] = {}
            current_key = None
            continue
        if indent == 0 and ":" in stripped:
            key, value = stripped.split(":", 1)
            data[key.strip()] = parse_scalar(value)
            continue
        if current_section is None:
            continue
        if indent == 2 and stripped.endswith(":"):
            current_key = stripped[:-1]
            section = data.setdefault(current_section, {})
            if isinstance(section, dict):
                section[current_key] = []
            continue
        if indent >= 4 and stripped.startswith("- ") and current_key:
            section = data.setdefault(current_section, {})
            if isinstance(section, dict):
                section.setdefault(current_key, []).append(parse_scalar(stripped[2:]))

    return data


def load_manifest(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore

        loaded = yaml.safe_load(text)
        if isinstance(loaded, dict):
            return loaded
    except ModuleNotFoundError:
        return simple_manifest_load(text)
    except Exception:
        return simple_manifest_load(text)
    return simple_manifest_load(text)


def normalize_rel_path(value: str) -> str:
    path = Path(value)
    if path.is_absolute():
        raise ValueError(f"absolute path is not allowed: {value}")
    normalized = path.as_posix()
    if normalized in {"", "."} or normalized.startswith("../") or "/../" in normalized:
        raise ValueError(f"invalid relative path: {value}")
    return normalized


def match_any(rel_path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(rel_path, pattern) for pattern in patterns)


def expand_globs(patterns: list[str], excluded: list[str]) -> list[str]:
    results: list[str] = []
    for pattern in patterns:
        normalized_pattern = normalize_rel_path(pattern)
        for path in REPO_ROOT.glob(normalized_pattern):
            if not path.is_file():
                continue
            rel_path = path.relative_to(REPO_ROOT).as_posix()
            if match_any(rel_path, excluded):
                continue
            results.append(rel_path)
    return sorted(set(results))


def copy_file(rel_path: str, output_root: Path) -> None:
    source = REPO_ROOT / rel_path
    destination = output_root / rel_path
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def write_runtime_agents(output_root: Path) -> None:
    (output_root / "AGENTS.md").write_text(FULL_RUNTIME_AGENTS, encoding="utf-8")


def write_runtime_manifest(
    output_root: Path,
    *,
    copied_files: list[str],
    generated_files: list[str],
    missing_required: list[str],
    missing_optional: list[str],
    excluded_patterns: list[str],
    created_at: str,
) -> None:
    lines = [
        "# Full Runtime Manifest",
        "",
        f"- created_at: `{created_at}`",
        f"- source_repo_root: `{REPO_ROOT}`",
        "- runtime_mode: `full_runtime`",
        "",
        "## Generated Files",
        "",
    ]
    lines.extend(f"- `{item}`" for item in generated_files)
    lines += ["", "## Copied Files", ""]
    lines.extend(f"- `{item}`" for item in copied_files)
    if not copied_files:
        lines.append("- none")
    lines += ["", "## Missing Required", ""]
    lines.extend(f"- `{item}`" for item in missing_required)
    if not missing_required:
        lines.append("- none")
    lines += ["", "## Missing Optional", ""]
    lines.extend(f"- `{item}`" for item in missing_optional)
    if not missing_optional:
        lines.append("- none")
    lines += ["", "## Excluded Patterns", ""]
    lines.extend(f"- `{item}`" for item in excluded_patterns)
    lines += [
        "",
        "## Machine Summary",
        "",
        "```json",
        json.dumps(
            {
                "runtime_mode": "full_runtime",
                "created_at": created_at,
                "source_repo_root": str(REPO_ROOT),
                "generated_files": generated_files,
                "copied_files": copied_files,
                "missing_required": missing_required,
                "missing_optional": missing_optional,
                "excluded_patterns": excluded_patterns,
            },
            ensure_ascii=False,
            indent=2,
        ),
        "```",
        "",
    ]
    (output_root / "RUNTIME_MANIFEST.md").write_text("\n".join(lines), encoding="utf-8")


def build_full_runtime(manifest: dict[str, Any], output_root: Path) -> dict[str, Any]:
    full_runtime = manifest.get("full_runtime_required", {})
    excluded_root = manifest.get("excluded_files", {})
    excluded_patterns = list(excluded_root.get("patterns", []))

    files = [normalize_rel_path(item) for item in full_runtime.get("files", [])]
    optional_files = [normalize_rel_path(item) for item in full_runtime.get("optional_files", [])]
    generated_files = [normalize_rel_path(item) for item in full_runtime.get("generated_files", [])]
    glob_files = expand_globs(list(full_runtime.get("globs", [])), excluded_patterns)
    optional_glob_files = expand_globs(list(full_runtime.get("optional_globs", [])), excluded_patterns)

    requested_files = sorted(set(files + glob_files + optional_glob_files))
    optional_set = set(optional_files + optional_glob_files)

    forbidden_requested = [item for item in requested_files + optional_files if match_any(item, excluded_patterns)]
    if forbidden_requested:
        return {
            "status": "failed_closed",
            "reason": "manifest_requested_excluded_files",
            "forbidden_requested": sorted(set(forbidden_requested)),
        }

    if output_root.exists():
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    copied_files: list[str] = []
    missing_required: list[str] = []
    missing_optional: list[str] = []

    for rel_path in requested_files:
        source = REPO_ROOT / rel_path
        if source.is_file():
            copy_file(rel_path, output_root)
            copied_files.append(rel_path)
        elif rel_path in optional_set:
            missing_optional.append(rel_path)
        else:
            missing_required.append(rel_path)

    for rel_path in optional_files:
        if rel_path in requested_files:
            continue
        source = REPO_ROOT / rel_path
        if source.is_file():
            copy_file(rel_path, output_root)
            copied_files.append(rel_path)
        else:
            missing_optional.append(rel_path)

    write_runtime_agents(output_root)
    created_at = datetime.now(timezone.utc).isoformat()
    write_runtime_manifest(
        output_root,
        copied_files=sorted(set(copied_files)),
        generated_files=sorted(set(generated_files)),
        missing_required=sorted(set(missing_required)),
        missing_optional=sorted(set(missing_optional)),
        excluded_patterns=excluded_patterns,
        created_at=created_at,
    )

    status = "created" if not missing_required else "created_with_missing_required"
    return {
        "status": status,
        "runtime_mode": "full_runtime",
        "output_root": str(output_root),
        "generated_files": sorted(set(generated_files)),
        "copied_files_count": len(set(copied_files)),
        "missing_required": sorted(set(missing_required)),
        "missing_optional": sorted(set(missing_optional)),
        "excluded_patterns": excluded_patterns,
        "created_at": created_at,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Dennis runtime snapshot.")
    parser.add_argument("--mode", choices=["full_runtime"], required=True)
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
    args = parser.parse_args()

    manifest = load_manifest(Path(args.manifest))
    result = build_full_runtime(manifest, Path(args.output_root))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status") == "created" else 2


if __name__ == "__main__":
    raise SystemExit(main())
