#!/usr/bin/env python3
"""Build an isolated runtime preview snapshot.

This script performs local file copying only. It does not access platforms,
DataAgent, Hive, auth state, gateway config, or TOOLS.
"""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ALLOWLIST = REPO_ROOT / "runtime_preview" / "runtime_file_allowlist.yaml"
DEFAULT_SNAPSHOT_ROOT = REPO_ROOT / "outputs" / "runtime_preview_snapshot"

PREVIEW_RUNTIME_FILES = [
    "runtime_preview/AGENTS.md",
    "runtime_preview/README.md",
    "runtime_preview/preview_runner_prompt.md",
    "runtime_preview/live_source_allowlist.yaml",
    "runtime_preview/expected_output_contract.yaml",
    "runtime_preview/online_effect_preview_cases.yaml",
]

FORBIDDEN_PATH_PATTERNS = [
    "run_logs/**",
    "outputs/**",
    "archives/**",
    ".ks_sso/**",
    "TOOLS.md",
    "old patch",
    "local-file-in-chat",
]

FORBIDDEN_EXACT_NAMES = {"TOOLS.md"}
FORBIDDEN_PARTS = {"run_logs", "outputs", "archives", ".ks_sso"}
FORBIDDEN_SUBSTRINGS = {"old patch", "local-file-in-chat"}

ROOT_AGENTS_TEMPLATE = """# Runtime Preview Snapshot Guard

This directory is `runtime_preview_only`.

Default behavior:

- Any direct risk case question defaults to `live_readonly_preview`.
- Batch, expansion, strategy recommendation, and methodology questions default to `offline_preview` / `plan_mode` unless the user explicitly authorizes sampled readonly lookup.
- This is replay, not design.

Mandatory reads inside this snapshot:

- `runtime_preview/preview_runner_prompt.md`
- `runtime_preview/live_source_allowlist.yaml`
- `runtime_preview/expected_output_contract.yaml`

Hard boundaries:

- Read only files inside this snapshot.
- Do not read the full repo.
- Do not read `run_logs`, historical `outputs`, `archives`, old patches, `.ks_sso`, or `TOOLS.md`.
- Do not add sources, patch rules, debug auth, repair runners, hand-build cookie/header, or probe arbitrary URLs.
- `live_readonly_preview` may use only readonly sources listed in `runtime_preview/live_source_allowlist.yaml`.
- Source failure must be recorded in `source_quality` and degrade to partial evidence card.
- Preview output is not a formal platform conclusion.

Required preview output:

- `route_decision`
- `execution_mode`
- `source_plan`
- `source_completion_matrix`
- `evidence_card`
- `source_quality`
- `routing_metadata`
- `expected_user_answer`
- `uncertainty_due_to_missing_runtime_info`
- `contract_compliance_check`

If contract is insufficient, output `PREVIEW_BLOCKED_INSUFFICIENT_CONTRACT`.
If contract conflicts, output `PREVIEW_BLOCKED_CONTRACT_CONFLICT`.
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


def parse_key_value(text: str) -> tuple[str, Any] | None:
    if ":" not in text:
        return None
    key, value = text.split(":", 1)
    return key.strip(), parse_scalar(value)


def simple_allowlist_load(text: str) -> dict[str, Any]:
    """Parse the small allowlist shape without requiring PyYAML."""
    files: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    in_files = False

    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        stripped = line.strip()
        if not stripped:
            continue
        if stripped == "files:":
            in_files = True
            continue
        if in_files and stripped.startswith("- "):
            current = {}
            files.append(current)
            remainder = stripped[2:].strip()
            if remainder:
                parsed = parse_key_value(remainder)
                if parsed:
                    key, value = parsed
                    current[key] = value
            continue
        if in_files and current is not None:
            parsed = parse_key_value(stripped)
            if parsed:
                key, value = parsed
                current[key] = value

    return {"snapshot_runtime_file_allowlist": {"files": files}}


def load_allowlist(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore

        loaded = yaml.safe_load(text)
        if isinstance(loaded, dict):
            return loaded
    except ModuleNotFoundError:
        return simple_allowlist_load(text)
    except Exception:
        return simple_allowlist_load(text)
    return simple_allowlist_load(text)


def normalize_rel_path(path_value: str) -> str:
    path = Path(path_value)
    if path.is_absolute():
        raise ValueError(f"absolute path is not allowed: {path_value}")
    normalized = path.as_posix()
    if normalized.startswith("../") or "/../" in normalized or normalized == "..":
        raise ValueError(f"parent traversal is not allowed: {path_value}")
    return normalized


def is_forbidden_path(rel_path: str) -> bool:
    path = Path(rel_path)
    if path.name in FORBIDDEN_EXACT_NAMES:
        return True
    if any(part in FORBIDDEN_PARTS for part in path.parts):
        return True
    lower = rel_path.lower()
    return any(marker in lower for marker in FORBIDDEN_SUBSTRINGS)


def extract_allowlist_files(config: dict[str, Any]) -> list[dict[str, Any]]:
    root = config.get("snapshot_runtime_file_allowlist", config)
    files = root.get("files", [])
    if not isinstance(files, list):
        raise ValueError("allowlist must contain a files list")
    normalized: list[dict[str, Any]] = []
    for item in files:
        if not isinstance(item, dict) or "path" not in item:
            raise ValueError(f"invalid allowlist item: {item!r}")
        rel_path = normalize_rel_path(str(item["path"]))
        normalized.append(
            {
                "path": rel_path,
                "required": bool(item.get("required", False)),
                "missing_status": str(item.get("missing_status", "missing_candidate")),
            }
        )
    return normalized


def copy_file(rel_path: str, snapshot_root: Path) -> bool:
    source = REPO_ROOT / rel_path
    if not source.is_file():
        return False
    destination = snapshot_root / rel_path
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    return True


def write_root_agents(snapshot_root: Path) -> None:
    (snapshot_root / "AGENTS.md").write_text(ROOT_AGENTS_TEMPLATE, encoding="utf-8")


def write_manifest(
    snapshot_root: Path,
    *,
    copied_files: list[str],
    missing_files: list[dict[str, str]],
    created_at: str,
) -> None:
    lines = [
        "# Runtime Preview Snapshot Manifest",
        "",
        f"- created_at: `{created_at}`",
        f"- source_repo_root: `{REPO_ROOT}`",
        "- snapshot_mode: `runtime_preview_only`",
        "",
        "## Copied Files",
        "",
    ]
    for rel_path in copied_files:
        lines.append(f"- `{rel_path}`")
    if not copied_files:
        lines.append("- none")

    lines += [
        "",
        "## Missing Files",
        "",
    ]
    for item in missing_files:
        lines.append(f"- `{item['path']}`: `{item['status']}`")
    if not missing_files:
        lines.append("- none")

    lines += [
        "",
        "## Forbidden Sources",
        "",
    ]
    for pattern in FORBIDDEN_PATH_PATTERNS:
        lines.append(f"- `{pattern}`")

    lines += [
        "",
        "## Machine Summary",
        "",
        "```json",
        json.dumps(
            {
                "copied_files": copied_files,
                "missing_files": missing_files,
                "forbidden_sources": FORBIDDEN_PATH_PATTERNS,
                "created_at": created_at,
                "source_repo_root": str(REPO_ROOT),
                "snapshot_mode": "runtime_preview_only",
            },
            ensure_ascii=False,
            indent=2,
        ),
        "```",
        "",
    ]
    (snapshot_root / "SNAPSHOT_MANIFEST.md").write_text("\n".join(lines), encoding="utf-8")


def build_snapshot(allowlist_path: Path, snapshot_root: Path) -> dict[str, Any]:
    config = load_allowlist(allowlist_path)
    allowlist_items = extract_allowlist_files(config)
    all_items = allowlist_items + [
        {"path": path, "required": True, "missing_status": "missing_candidate"}
        for path in PREVIEW_RUNTIME_FILES
    ]

    forbidden_items = [item["path"] for item in all_items if is_forbidden_path(item["path"])]
    if forbidden_items:
        return {
            "status": "failed_closed",
            "reason": "allowlist_contains_forbidden_path",
            "forbidden_items": forbidden_items,
            "forbidden_sources": FORBIDDEN_PATH_PATTERNS,
        }

    if snapshot_root.exists():
        shutil.rmtree(snapshot_root)
    snapshot_root.mkdir(parents=True, exist_ok=True)

    copied_files: list[str] = []
    missing_files: list[dict[str, str]] = []
    for item in all_items:
        rel_path = item["path"]
        if copy_file(rel_path, snapshot_root):
            copied_files.append(rel_path)
        else:
            missing_files.append({"path": rel_path, "status": item["missing_status"]})

    write_root_agents(snapshot_root)
    copied_files.append("AGENTS.md")

    created_at = datetime.now(timezone.utc).isoformat()
    write_manifest(
        snapshot_root,
        copied_files=sorted(copied_files),
        missing_files=missing_files,
        created_at=created_at,
    )
    copied_files.append("SNAPSHOT_MANIFEST.md")

    return {
        "status": "created",
        "snapshot_root": str(snapshot_root),
        "copied_files": sorted(copied_files),
        "missing_files": missing_files,
        "forbidden_sources": FORBIDDEN_PATH_PATTERNS,
        "created_at": created_at,
        "source_repo_root": str(REPO_ROOT),
        "snapshot_mode": "runtime_preview_only",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build runtime preview snapshot.")
    parser.add_argument("--allowlist", default=str(DEFAULT_ALLOWLIST), help="Path to runtime file allowlist YAML.")
    parser.add_argument("--snapshot-root", default=str(DEFAULT_SNAPSHOT_ROOT), help="Output snapshot directory.")
    args = parser.parse_args()

    result = build_snapshot(Path(args.allowlist), Path(args.snapshot_root))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status") == "created" else 2


if __name__ == "__main__":
    raise SystemExit(main())
