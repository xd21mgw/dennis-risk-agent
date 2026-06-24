#!/usr/bin/env python3
"""Export timing summaries from existing browser-backed batch checkpoints.

This exporter is intentionally provenance-first: it only reports timing that is
present in checkpoint `timing_trace` objects. It does not change scheduling,
does not call platforms, and does not split mixed chunk wait time across
individual actions.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


SENSITIVE_TEXT_RE = re.compile(r"(authorization|cookie|header|password|session|token)", re.IGNORECASE)
PRIMARY_ACTIONS = {
    "archives_user_profile",
    "weapon_inventory",
    "archives_user_analysis",
    "archives_photo_search",
}


def _load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_json(path: str | Path, payload: Any) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _safe_string(value: Any) -> str:
    text = str(value or "")
    return SENSITIVE_TEXT_RE.sub("[REDACTED]", text)


def _safe_list(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    return [_safe_string(value) for value in values]


def _as_int(value: Any, default: int = 0) -> int:
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    return default


def _as_optional_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    return None


def _round_batch_from_name(path: Path) -> tuple[int, int] | None:
    match = re.search(r"round_(\d+)_batch_(\d+)", path.name)
    if not match:
        return None
    return int(match.group(1)), int(match.group(2))


def _checkpoint_dir_for_file(path: Path) -> Path:
    return path.parent


def discover_done_files(inputs: list[str | Path], *, final_per_round: bool = True) -> list[Path]:
    """Find done checkpoint files and optionally keep only final checkpoint per round."""
    files: list[Path] = []
    for item in inputs:
        path = Path(item)
        if path.is_file():
            files.append(path)
            continue
        if path.is_dir():
            files.extend(sorted(path.rglob("*_done.json")))
    files = sorted({path.resolve() for path in files})
    if not final_per_round:
        return files

    latest: dict[tuple[Path, int], tuple[int, Path]] = {}
    passthrough: list[Path] = []
    for path in files:
        parsed = _round_batch_from_name(path)
        if parsed is None:
            passthrough.append(path)
            continue
        round_index, batch_index = parsed
        key = (_checkpoint_dir_for_file(path), round_index)
        if key not in latest or batch_index > latest[key][0]:
            latest[key] = (batch_index, path)
    return sorted(passthrough + [path for _, path in latest.values()])


def _derive_batch_run_id(files: list[Path]) -> str:
    if not files:
        return "unknown_batch_run"
    path = files[0]
    for part in path.parts:
        if part.startswith("dennis"):
            return _safe_string(part)
    return _safe_string(path.parent.name)


def _row_from_chunk(chunk: dict[str, Any], *, file_path: Path, batch_run_id: str) -> dict[str, Any]:
    raw_actions = chunk.get("actions")
    actions = _safe_list(raw_actions)
    unique_actions = sorted(set(actions))
    source_group = _safe_string(chunk.get("source_group") or "+".join(unique_actions) or "unknown_source_group")
    chunk_id = _safe_string(chunk.get("chunk_id") or "")

    wait_ms = _as_optional_int(chunk.get("wait_ms"))
    action_count = _as_int(chunk.get("action_count"), default=len(actions))
    completed_count = _as_int(chunk.get("completed_count"))
    timeout_count = _as_int(chunk.get("timeout_count"))
    blocked_count = _as_int(chunk.get("blocked_count"))
    partial_count = _as_int(chunk.get("partial_count"))
    pending_count = _as_int(chunk.get("pending_count"))
    auth_failed_count = _as_int(chunk.get("auth_failed_count"))
    status_count = completed_count + timeout_count + blocked_count + partial_count + pending_count + auth_failed_count
    source_gap_count = timeout_count + blocked_count + partial_count + pending_count + auth_failed_count

    missing_fields: list[str] = []
    timing_precision = "unknown"
    instrumentation_gap = False
    user_count: int | None = None
    source_action = "unknown_action"

    if len(unique_actions) == 1:
        source_action = unique_actions[0]
        timing_precision = "action_level"
        user_count = action_count
        if wait_ms is None:
            instrumentation_gap = True
            missing_fields.append("wait_ms")
    elif unique_actions:
        source_action = "mixed_actions"
        timing_precision = "group_only"
        instrumentation_gap = True
        missing_fields.extend([
            "per_action_wait_ms",
            "per_action_status_count",
            "per_action_user_count",
        ])
        if wait_ms is None:
            missing_fields.append("wait_ms")
    else:
        source_action = "unknown_action"
        timing_precision = "unknown"
        instrumentation_gap = True
        missing_fields.extend(["actions", "source_action"])
        if wait_ms is None:
            missing_fields.append("wait_ms")

    if chunk.get("per_source_elapsed_ms") is None and len(unique_actions) > 1:
        if "per_source_elapsed_ms" not in missing_fields:
            missing_fields.append("per_source_elapsed_ms")

    return {
        "batch_run_id": batch_run_id,
        "source_group": source_group,
        "source_action": source_action,
        "actions_in_chunk": actions,
        "chunk_id": chunk_id,
        "user_count": user_count,
        "action_count": action_count,
        "status_count": status_count,
        "completed_count": completed_count,
        "timeout_count": timeout_count,
        "auth_failed_count": auth_failed_count,
        "blocked_count": blocked_count,
        "partial_count": partial_count,
        "pending_count": pending_count,
        "source_gap_count": source_gap_count,
        "wait_ms": wait_ms,
        "batch_elapsed_ms": _as_optional_int(chunk.get("batch_elapsed_ms")),
        "start_time": _safe_string(chunk.get("service_wait_started_at") or chunk.get("submit_started_at") or ""),
        "end_time": _safe_string(chunk.get("service_returned_at") or chunk.get("submit_finished_at") or ""),
        "timing_precision": timing_precision,
        "instrumentation_gap": instrumentation_gap,
        "missing_fields": sorted(set(missing_fields)),
        "provenance": {
            "source_file": str(file_path),
            "json_path": "timing_trace.chunks[]",
            "wait_ms_source": "timing_trace.chunks[].wait_ms",
            "status_count_source": "timing_trace.chunks[] aggregate status counts",
            "note": (
                "single-action chunk wait_ms is treated as action-level timing"
                if timing_precision == "action_level"
                else "trace only exposes chunk/group wait; wait_ms is not attributed to individual actions"
            ),
        },
    }


def _iter_chunks(files: list[Path], batch_run_id: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    globals_: list[dict[str, Any]] = []
    for path in files:
        data = _load_json(path)
        trace = data.get("timing_trace") or {}
        global_timing = trace.get("global") or {}
        globals_.append({
            "source_file": str(path),
            "total_elapsed_ms": _as_int(global_timing.get("total_elapsed_ms")),
            "browser_wait_ms": _as_int(global_timing.get("batch_wait_ms")),
            "plan_build_ms": _as_int(global_timing.get("plan_build_ms")),
            "batch_submit_ms": _as_int(global_timing.get("batch_submit_ms")),
            "artifact_build_ms": _as_int(global_timing.get("artifact_build_ms")),
            "checkpoint_write_ms": _as_int(global_timing.get("checkpoint_write_ms")),
        })
        for chunk in trace.get("chunks") or []:
            if isinstance(chunk, dict):
                rows.append(_row_from_chunk(chunk, file_path=path, batch_run_id=batch_run_id))
    return rows, globals_


def _summarize_source_groups(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for row in rows:
        key = row["source_group"]
        item = grouped.setdefault(key, {
            "source_group": key,
            "chunk_count": 0,
            "action_count": 0,
            "completed_count": 0,
            "timeout_count": 0,
            "auth_failed_count": 0,
            "source_gap_count": 0,
            "wait_ms": 0,
            "instrumentation_gap_count": 0,
            "timing_precision": Counter(),
        })
        item["chunk_count"] += 1
        item["action_count"] += row["action_count"]
        item["completed_count"] += row["completed_count"]
        item["timeout_count"] += row["timeout_count"]
        item["auth_failed_count"] += row["auth_failed_count"]
        item["source_gap_count"] += row["source_gap_count"]
        item["wait_ms"] += row["wait_ms"] or 0
        item["instrumentation_gap_count"] += 1 if row["instrumentation_gap"] else 0
        item["timing_precision"][row["timing_precision"]] += 1
    output = []
    for item in grouped.values():
        precision_counter = item.pop("timing_precision")
        item["timing_precision_counts"] = dict(precision_counter)
        output.append(item)
    return sorted(output, key=lambda item: (-item["wait_ms"], item["source_group"]))


def _primary_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for row in rows:
        actions = set(row.get("actions_in_chunk") or [])
        source_group = str(row.get("source_group") or "")
        chunk_id = str(row.get("chunk_id") or "")
        is_primary = bool(actions & PRIMARY_ACTIONS) or "primary" in chunk_id or any(action in source_group for action in PRIMARY_ACTIONS)
        if not is_primary:
            continue
        item = dict(row)
        if row["timing_precision"] == "group_only":
            item["source_group"] = "primary"
            item["original_source_group"] = row["source_group"]
        output.append(item)
    return output


def _instrumentation_gap_summary(rows: list[dict[str, Any]], primary_rows: list[dict[str, Any]]) -> dict[str, Any]:
    missing_counter: Counter[str] = Counter()
    for row in rows:
        if row.get("instrumentation_gap"):
            missing_counter.update(row.get("missing_fields") or [])
    final_chunks_with_null_per_source = sum(
        1
        for row in rows
        if row.get("timing_precision") == "group_only" and "per_source_elapsed_ms" in (row.get("missing_fields") or [])
    )
    mixed_primary_gap_count = sum(1 for row in primary_rows if row.get("timing_precision") == "group_only")
    return {
        "instrumentation_gap": any(row.get("instrumentation_gap") for row in rows),
        "instrumentation_gap_row_count": sum(1 for row in rows if row.get("instrumentation_gap")),
        "missing_field_counts": dict(missing_counter),
        "mixed_primary_chunk_gap_count": mixed_primary_gap_count,
        "per_source_elapsed_ms_present_but_null_group_chunk_count": final_chunks_with_null_per_source,
        "notes": [
            "mixed primary chunk cannot be split into archives_user_profile / weapon_inventory / archives_user_analysis / archives_photo_search timing",
            "per_source_elapsed_ms is present but null in scanned group-only chunks",
            "minimal runtime instrumentation is required only if true per-action timing is needed",
        ],
    }


def _timeout_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_group = defaultdict(int)
    by_action = defaultdict(int)
    for row in rows:
        by_group[row["source_group"]] += row["timeout_count"]
        by_action[row["source_action"]] += row["timeout_count"]
    return {
        "total_timeout_count": sum(row["timeout_count"] for row in rows),
        "by_source_group": dict(sorted(by_group.items(), key=lambda item: (-item[1], item[0]))),
        "by_source_action": dict(sorted(by_action.items(), key=lambda item: (-item[1], item[0]))),
    }


def _source_gap_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_group = defaultdict(int)
    by_action = defaultdict(int)
    for row in rows:
        by_group[row["source_group"]] += row["source_gap_count"]
        by_action[row["source_action"]] += row["source_gap_count"]
    return {
        "total_source_gap_count": sum(row["source_gap_count"] for row in rows),
        "by_source_group": dict(sorted(by_group.items(), key=lambda item: (-item[1], item[0]))),
        "by_source_action": dict(sorted(by_action.items(), key=lambda item: (-item[1], item[0]))),
    }


def build_timing_summary(
    inputs: list[str | Path],
    *,
    batch_run_id: str | None = None,
    final_per_round: bool = True,
) -> dict[str, Any]:
    files = discover_done_files(inputs, final_per_round=final_per_round)
    run_id = _safe_string(batch_run_id or _derive_batch_run_id(files))
    rows, global_rows = _iter_chunks(files, run_id)
    primary = _primary_rows(rows)
    summary = {
        "schema_version": "batch_action_timing_summary_v1",
        "batch_run_id": run_id,
        "input_files": [str(path) for path in files],
        "total_elapsed_ms": sum(row["total_elapsed_ms"] for row in global_rows),
        "browser_wait_ms": sum(row["browser_wait_ms"] for row in global_rows),
        "global_timing_rows": global_rows,
        "source_group_timing_summary": _summarize_source_groups(rows),
        "action_timing_summary": rows,
        "primary_action_timing_summary": primary,
        "primary_action_breakdown_possible": (
            "partial"
            if any(row.get("timing_precision") == "group_only" for row in primary)
            else ("true" if primary else "unknown")
        ),
        "primary_action_breakdown_blocker": (
            "per_action_wait_ms_missing"
            if any(row.get("timing_precision") == "group_only" for row in primary)
            else None
        ),
        "timeout_summary": _timeout_summary(rows),
        "source_gap_summary": _source_gap_summary(rows),
        "instrumentation_gap_summary": _instrumentation_gap_summary(rows, primary),
    }
    return summary


def _table_row(values: list[Any]) -> str:
    return "|" + "|".join(str(value) for value in values) + "|"


def render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Batch Action Timing Summary",
        "",
        f"- batch_run_id: `{summary['batch_run_id']}`",
        f"- total_elapsed_ms: `{summary['total_elapsed_ms']}`",
        f"- browser_wait_ms: `{summary['browser_wait_ms']}`",
        f"- primary_action_breakdown_possible: `{summary['primary_action_breakdown_possible']}`",
        f"- primary_action_breakdown_blocker: `{summary.get('primary_action_breakdown_blocker')}`",
        "",
        "## Source group timing summary",
        "",
        _table_row(["source_group", "chunks", "actions", "completed", "timeout", "gap", "wait_ms", "gap_rows"]),
        _table_row(["---", "---:", "---:", "---:", "---:", "---:", "---:", "---:"]),
    ]
    for row in summary.get("source_group_timing_summary", []):
        lines.append(_table_row([
            row["source_group"],
            row["chunk_count"],
            row["action_count"],
            row["completed_count"],
            row["timeout_count"],
            row["source_gap_count"],
            row["wait_ms"],
            row["instrumentation_gap_count"],
        ]))

    lines.extend([
        "",
        "## Action timing summary",
        "",
        _table_row(["source_group", "source_action", "chunk_id", "precision", "completed", "timeout", "gap", "wait_ms", "instrumentation_gap"]),
        _table_row(["---", "---", "---", "---", "---:", "---:", "---:", "---:", "---"]),
    ])
    for row in summary.get("action_timing_summary", []):
        lines.append(_table_row([
            row["source_group"],
            row["source_action"],
            row["chunk_id"],
            row["timing_precision"],
            row["completed_count"],
            row["timeout_count"],
            row["source_gap_count"],
            row["wait_ms"],
            str(row["instrumentation_gap"]).lower(),
        ]))

    gap = summary.get("instrumentation_gap_summary", {})
    lines.extend([
        "",
        "## Instrumentation gap summary",
        "",
        f"- instrumentation_gap: `{str(gap.get('instrumentation_gap')).lower()}`",
        f"- instrumentation_gap_row_count: `{gap.get('instrumentation_gap_row_count')}`",
        f"- mixed_primary_chunk_gap_count: `{gap.get('mixed_primary_chunk_gap_count')}`",
        f"- per_source_elapsed_ms_present_but_null_group_chunk_count: `{gap.get('per_source_elapsed_ms_present_but_null_group_chunk_count')}`",
        "",
    ])
    for note in gap.get("notes", []):
        lines.append(f"- {note}")
    lines.extend(["", "### Missing field counts", ""])
    for key, value in sorted((gap.get("missing_field_counts") or {}).items()):
        lines.append(f"- `{key}`: `{value}`")
    return "\n".join(lines) + "\n"


def write_timing_summary(summary: dict[str, Any], output_dir: str | Path) -> tuple[Path, Path]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    json_path = out / "batch_action_timing_summary.json"
    md_path = out / "batch_action_timing_summary.md"
    _write_json(json_path, summary)
    md_path.write_text(render_markdown(summary), encoding="utf-8")
    return json_path, md_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export batch action timing summary from local checkpoint timing_trace files.")
    parser.add_argument("--input", action="append", required=True, help="Checkpoint file or directory. Can be repeated.")
    parser.add_argument("--output-dir", required=True, help="Directory for batch_action_timing_summary.json/md.")
    parser.add_argument("--batch-run-id", default=None)
    parser.add_argument("--all-checkpoints", action="store_true", help="Do not de-duplicate to final checkpoint per round.")
    args = parser.parse_args(argv)

    summary = build_timing_summary(
        args.input,
        batch_run_id=args.batch_run_id,
        final_per_round=not args.all_checkpoints,
    )
    json_path, md_path = write_timing_summary(summary, args.output_dir)
    print(json.dumps({
        "batch_run_id": summary["batch_run_id"],
        "json_path": str(json_path),
        "md_path": str(md_path),
        "action_timing_rows": len(summary["action_timing_summary"]),
        "instrumentation_gap": summary["instrumentation_gap_summary"]["instrumentation_gap"],
        "primary_action_breakdown_possible": summary["primary_action_breakdown_possible"],
    }, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
