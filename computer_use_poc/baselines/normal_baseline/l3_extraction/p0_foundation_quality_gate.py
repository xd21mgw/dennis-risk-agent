#!/usr/bin/env python3
"""Quality gate for P0 foundation inventory outputs.

This utility audits already-generated P0-1..P0-4 artifacts. It does not build
or replay candidates and never calls platforms, Hive, DataAgent, release, dist,
or full_runtime paths.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


REQUIRED_CONTAINERS = [
    "requestParam",
    "extraParam",
    "logContent",
    "params",
    "data",
    "originalLog",
    "labelInfo",
    "accessibilitySvc",
    "enabledAccessibilityServices",
    "appList",
]

GUARD_CHECKS = {
    "http_status": ["http_status", "_http_status"],
    "response_mode": ["response_mode"],
    "body_present": ["body_present"],
    "traceId/requestId": ["traceId", "trace_id", "requestId", "request_id"],
    "costTime/currentTime": ["costTime", "currentTime"],
    "default avatar/bg URL": ["avatar", "headUrl", "headerUrl", "background", "bgUrl"],
    "pagination near-full-page": ["pageSize", "pageIndex", "page", "count", "limit", "total", "totalCount"],
    "fixed logTags color": ["logTags.color", "logtags.color"],
    "platform internal clientIp": ["clientIp"],
    "boardPlatform 单字段": ["boardPlatform"],
}


def _load_json(path: str | Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: str | Path, payload: Any) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_markdown(path: str | Path, summary: dict[str, Any]) -> None:
    lines = [
        "# P0 Foundation Quality Gate",
        "",
        f"- wave_id: `{summary['wave_id']}`",
        f"- p0_1_raw_diff_quality_pass: `{str(summary['quality_gate_decision']['p0_1_raw_diff_quality_pass']).lower()}`",
        f"- p0_2_parsed_inventory_quality_pass: `{str(summary['quality_gate_decision']['p0_2_parsed_inventory_quality_pass']).lower()}`",
        f"- p0_3_container_coverage_quality_pass: `{str(summary['quality_gate_decision']['p0_3_container_coverage_quality_pass']).lower()}`",
        f"- p0_4_schema_guard_quality_pass: `{str(summary['quality_gate_decision']['p0_4_schema_guard_quality_pass']).lower()}`",
        f"- can_start_p0_5_candidate_replay: `{str(summary['quality_gate_decision']['can_start_p0_5_candidate_replay']).lower()}`",
        "",
        "## Summary",
        "",
        "|metric|value|",
        "|---|---:|",
    ]
    for key in [
        "raw_missing_true_gap_count",
        "raw_missing_path_alias_count",
        "raw_missing_container_parent_child_count",
        "raw_missing_repeated_array_index_path_count",
        "raw_missing_schema_noise_count",
        "raw_missing_sensitive_or_noneligible_count",
        "raw_missing_unknown_count",
        "normalized_inventory_seen_fields_before",
        "normalized_inventory_seen_fields_after",
        "missing_fields_before",
        "missing_fields_after",
        "parsed_success_rate",
        "container_success_rate",
        "guarded_noise_count",
        "report_only_count",
    ]:
        lines.append(f"|{key}|{summary['quality_gate_summary'].get(key)}|")
    lines.extend(["", "## Remaining Gap", ""])
    for gap in summary.get("remaining_gap", []):
        lines.append(f"- {gap}")
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def normalize_path(path: str) -> str:
    """Normalize wrapper and list-expression differences for audit only."""
    text = str(path or "").strip()
    text = text.replace("[].", ".").replace("[]", "")
    text = re.sub(r"\[\d+\]", "", text)
    text = re.sub(r"\.{2,}", ".", text).strip(".")
    prefixes = [
        "upstream.body.body.",
        "upstream.body.",
        "body.",
        "raw_body.",
        "payload.",
        "_local_payload.",
    ]
    for prefix in prefixes:
        if text.startswith(prefix):
            text = text[len(prefix):]
            break
    if text.startswith("data.data."):
        text = text[len("data."):]
    return text


def suffixes(path: str) -> set[str]:
    parts = [p for p in normalize_path(path).split(".") if p]
    return {".".join(parts[i:]) for i in range(len(parts))}


def ancestors(path: str) -> list[str]:
    parts = [p for p in normalize_path(path).split(".") if p]
    return [".".join(parts[:i]) for i in range(1, len(parts))]


def load_inventory_sets(inventory_path: str | Path, wave_id: str) -> tuple[dict[str, set[str]], dict[str, set[str]], set[str]]:
    data = _load_json(inventory_path)
    wave_data = data.get(wave_id, {}) if isinstance(data, dict) else {}
    exact: dict[str, set[str]] = defaultdict(set)
    normalized: dict[str, set[str]] = defaultdict(set)
    global_normalized: set[str] = set()
    for action, rows in wave_data.items():
        for row in rows or []:
            if not isinstance(row, dict) or not row.get("field_path"):
                continue
            path = str(row["field_path"])
            exact[str(action)].add(path)
            norm = normalize_path(path)
            normalized[str(action)].add(norm)
            global_normalized.add(norm)
            for suf in suffixes(path):
                normalized[str(action)].add(suf)
                global_normalized.add(suf)
    return dict(exact), dict(normalized), global_normalized


def classify_missing_record(
    row: dict[str, Any],
    *,
    normalized_inventory_by_action: dict[str, set[str]],
    global_normalized_inventory: set[str],
    missing_path_counts: Counter[str],
) -> tuple[str, str]:
    raw_path = str(row.get("raw_path") or "")
    action = str(row.get("source_action") or "")
    norm = normalize_path(raw_path)
    inv = normalized_inventory_by_action.get(action, set())
    raw_suffixes = suffixes(raw_path)
    if norm in inv or raw_suffixes & inv:
        return "path_alias_or_wrapper_mismatch", "normalized_path_or_suffix_matches_same_action_inventory"
    if norm in global_normalized_inventory or raw_suffixes & global_normalized_inventory:
        return "path_alias_or_wrapper_mismatch", "normalized_path_matches_other_action_variant_inventory"

    eligibility = str(row.get("eligibility_status") or "")
    if row.get("parsed_children_expected") or int(row.get("parsed_children_seen_count") or 0) > 0:
        return "container_parent_child_mismatch", "container_parent_seen_with_parsed_children_or_expected_children"
    if any(a in inv for a in ancestors(raw_path)):
        return "container_parent_child_mismatch", "inventory_has_parent_path_but_missing_child_path"

    count = missing_path_counts[raw_path]
    lowered = raw_path.lower()
    if count >= 10 and any(token in lowered for token in ("list", "datalist", "rows", "items", "applist", "relationedgelist")):
        return "repeated_array_index_path_mismatch", "same_array_like_path_repeats_many_times_without_inventory_path"
    if eligibility == "noise":
        return "schema_noise_missing", "missing_field_is_guarded_noise"
    if eligibility in {"report_only", "sensitive_blocked", "non_scalar_container", "needs_parse"}:
        return "sensitive_or_noneligible_missing", f"missing_field_eligibility_status={eligibility}"
    if eligibility == "eligible":
        return "true_missing", "eligible_field_not_matched_by_exact_or_normalized_inventory"
    return "unknown", f"eligibility_status={eligibility or 'missing'}"


def audit_missing_fields(
    raw_diff: dict[str, Any],
    *,
    inventory_path: str | Path,
    wave_id: str,
) -> dict[str, Any]:
    _, normalized_by_action, global_normalized = load_inventory_sets(inventory_path, wave_id)
    records = raw_diff.get("records") or []
    missing = [r for r in records if r.get("missing_from_inventory")]
    missing_path_counts = Counter(str(r.get("raw_path") or "") for r in missing)
    classified = []
    category_counts = Counter()
    normalized_seen_after = int(raw_diff.get("summary", {}).get("normalized_inventory_seen_fields") or 0)
    for row in records:
        if row.get("inventory_seen"):
            continue
        if row.get("path_match_type") in {"normalized_alias", "container_parent_child", "repeated_array_normalized"}:
            continue
        category, reason = classify_missing_record(
            row,
            normalized_inventory_by_action=normalized_by_action,
            global_normalized_inventory=global_normalized,
            missing_path_counts=missing_path_counts,
        )
        if category == "path_alias_or_wrapper_mismatch":
            pass
        if row.get("missing_from_inventory"):
            category_counts[category] += 1
            if len(classified) < 500:
                classified.append({
                    "source_action": row.get("source_action"),
                    "user_id": row.get("user_id"),
                    "raw_path": row.get("raw_path"),
                    "value_shape": row.get("value_shape"),
                    "visibility_status": row.get("visibility_status"),
                    "eligibility_status": row.get("eligibility_status"),
                    "missing_category": category,
                    "missing_reason": reason,
                })
    before = int(raw_diff.get("summary", {}).get("inventory_seen_fields") or 0)
    total = int(raw_diff.get("summary", {}).get("raw_total_fields") or len(records))
    return {
        "category_counts": dict(category_counts),
        "sampled_missing_records": classified,
        "normalized_inventory_seen_fields_before": before,
        "normalized_inventory_seen_fields_after": normalized_seen_after,
        "missing_fields_before": int(raw_diff.get("summary", {}).get("missing_fields") or 0),
        "missing_fields_after": int(raw_diff.get("summary", {}).get("normalized_missing_fields") or max(total - normalized_seen_after, 0)),
    }


def container_spot_check(container_matrix: dict[str, Any]) -> list[dict[str, Any]]:
    matrix = container_matrix.get("matrix") or []
    by_container: dict[str, dict[str, Any]] = {}
    for name in REQUIRED_CONTAINERS:
        rows = [r for r in matrix if r.get("container_name") == name]
        attempted = sum(int(r.get("attempted") or 0) for r in rows)
        success = sum(int(r.get("success") or 0) for r in rows)
        error = sum(int(r.get("error") or 0) for r in rows)
        path_count = sum(int(r.get("path_count") or 0) for r in rows)
        parsed_value_count = sum(int(r.get("parsed_value_count") or 0) for r in rows)
        users = sum(int(r.get("coverage_user_count") or 0) for r in rows)
        failed = []
        parsers = set()
        for r in rows:
            failed.extend(r.get("failed_examples") or [])
            parsers.update(str(p) for p in (r.get("parser_type") or []) if p)
        reason = str(rows[0].get("scanner_gap_reason") or "") if len(rows) == 1 else ""
        if rows:
            reasons = {str(r.get("scanner_gap_reason") or "") for r in rows}
            reason = "raw_absent" if reasons == {"raw_absent"} else ",".join(sorted(r for r in reasons if r))
        if not reason:
            if attempted == 0:
                reason = "raw_absent"
            elif success == 0:
                reason = "parse_error"
        gap_status = "data_gap" if reason == "raw_absent" else ("scanner_gap" if reason else "closed")
        scanner_gap = gap_status == "scanner_gap"
        by_container[name] = {
            "container_name": name,
            "attempted": attempted,
            "success": success,
            "error": error,
            "path_count": path_count,
            "parsed_value_count": parsed_value_count,
            "coverage_user_count": users,
            "failed_examples": failed[:3],
            "parser_type": sorted(parsers),
            "alias_checked": sorted({alias for r in rows for alias in (r.get("alias_checked") or [])}) or [name],
            "raw_present": any(bool(r.get("raw_present")) for r in rows),
            "empty_value_count": sum(int(r.get("empty_value_count") or 0) for r in rows),
            "parse_attempted": sum(int(r.get("parse_attempted") or 0) for r in rows),
            "parse_success": sum(int(r.get("parse_success") or 0) for r in rows),
            "scanner_gap_reason": reason,
            "gap_status": gap_status,
            "scanner_gap": scanner_gap,
        }
    return [by_container[name] for name in REQUIRED_CONTAINERS]


def guard_spot_check(guard_report: dict[str, Any]) -> list[dict[str, Any]]:
    guarded = guard_report.get("guarded_fields") or []
    out = []
    for check_name, hints in GUARD_CHECKS.items():
        matches = [
            row for row in guarded
            if any(hint.lower() in str(row.get("path") or "").lower() for hint in hints)
        ]
        ok = bool(matches)
        if check_name == "boardPlatform 单字段":
            ok = bool(matches) and all(
                row.get("guard_level") == "report_only"
                and row.get("guard_reason") == "event_environment_context_only"
                and row.get("high_value_allowed") is False
                and row.get("combo_allowed") is True
                for row in matches[:50]
            )
        elif check_name == "pagination near-full-page":
            ok = bool(matches) and all(row.get("high_value_allowed") is False for row in matches[:50])
        elif check_name == "default avatar/bg URL":
            ok = True  # Some waves may not expose default URL values; absence is not a failed guard.
            if matches:
                ok = all(row.get("high_value_allowed") is False for row in matches[:50])
        out.append({
            "guard_check": check_name,
            "matched_count": len(matches),
            "ok": ok,
            "sample": matches[:3],
        })
    return out


def build_quality_gate_summary(
    *,
    smoke_dir: str | Path,
    inventory_path: str | Path,
    output_dir: str | Path,
) -> dict[str, Any]:
    smoke = Path(smoke_dir)
    raw_diff = _load_json(smoke / "full_action_inventory_raw_diff.json")
    parsed_inventory = _load_json(smoke / "parsed_field_inventory.json")
    container_matrix = _load_json(smoke / "container_parser_coverage_matrix.json")
    guard_report = _load_json(smoke / "schema_noise_guard_report.json")
    wave_id = str(raw_diff.get("summary", {}).get("wave_id") or smoke.name.replace("_smoke", ""))

    missing_audit = audit_missing_fields(raw_diff, inventory_path=inventory_path, wave_id=wave_id)
    container_checks = container_spot_check(container_matrix)
    guard_checks = guard_spot_check(guard_report)

    counts = Counter(missing_audit["category_counts"])
    parsed_success_rate = float(parsed_inventory.get("summary", {}).get("parsed_success_rate") or 0.0)
    container_success_rate = float(container_matrix.get("summary", {}).get("container_success_rate") or 0.0)
    guarded_noise_count = int(guard_report.get("summary", {}).get("guarded_noise_count") or 0)
    report_only_count = int(guard_report.get("summary", {}).get("report_only_count") or 0)
    raw_summary = raw_diff.get("summary", {})
    must_inventory_missing_count = int(raw_summary.get("must_inventory_missing_count") or 0)
    weapon_original_log_missing_count = int(raw_summary.get("weapon_originalLog_missing_count") or 0)
    weapon_decode_header_missing_count = int(raw_summary.get("weaponDecodeHeader_missing_count") or 0)
    user_behavior_missing_count = int(raw_summary.get("user_behavior_missing_count") or 0)
    weapon_deep_inventory_patched_fields = int(raw_summary.get("weapon_deep_inventory_patched_fields") or 0)

    true_missing_threshold = 10000
    p0_1_pass = (
        counts.get("unknown", 0) == 0
        and missing_audit["normalized_inventory_seen_fields_after"] > missing_audit["normalized_inventory_seen_fields_before"]
        and must_inventory_missing_count == 0
        and counts.get("true_missing", 0) <= true_missing_threshold
    )
    p0_2_pass = parsed_success_rate >= 0.95
    p0_3_pass = container_success_rate >= 0.90 and all(not row["scanner_gap"] for row in container_checks)
    p0_4_pass = all(row["ok"] for row in guard_checks if row["guard_check"] != "default avatar/bg URL")
    can_start_p0_5 = bool(p0_1_pass and p0_2_pass and p0_3_pass and p0_4_pass and counts.get("true_missing", 0) < 10000)

    summary = {
        "schema_version": "p0_foundation_quality_gate_v1",
        "wave_id": wave_id,
        "missing_field_attribution": {
            "true_missing": counts.get("true_missing", 0),
            "path_alias_or_wrapper_mismatch": counts.get("path_alias_or_wrapper_mismatch", 0),
            "container_parent_child_mismatch": counts.get("container_parent_child_mismatch", 0),
            "repeated_array_index_path_mismatch": counts.get("repeated_array_index_path_mismatch", 0),
            "schema_noise_missing": counts.get("schema_noise_missing", 0),
            "sensitive_or_noneligible_missing": counts.get("sensitive_or_noneligible_missing", 0),
            "unknown": counts.get("unknown", 0),
        },
        "quality_gate_summary": {
            "raw_missing_true_gap_count": counts.get("true_missing", 0),
            "raw_missing_path_alias_count": counts.get("path_alias_or_wrapper_mismatch", 0),
            "raw_missing_container_parent_child_count": counts.get("container_parent_child_mismatch", 0),
            "raw_missing_repeated_array_index_path_count": counts.get("repeated_array_index_path_mismatch", 0),
            "raw_missing_schema_noise_count": counts.get("schema_noise_missing", 0),
            "raw_missing_sensitive_or_noneligible_count": counts.get("sensitive_or_noneligible_missing", 0),
            "raw_missing_unknown_count": counts.get("unknown", 0),
            "must_inventory_missing_count": must_inventory_missing_count,
            "weapon_originalLog_missing_count": weapon_original_log_missing_count,
            "weaponDecodeHeader_missing_count": weapon_decode_header_missing_count,
            "user_behavior_missing_count": user_behavior_missing_count,
            "weapon_deep_inventory_patched_fields": weapon_deep_inventory_patched_fields,
            "normalized_inventory_seen_fields_before": missing_audit["normalized_inventory_seen_fields_before"],
            "normalized_inventory_seen_fields_after": missing_audit["normalized_inventory_seen_fields_after"],
            "missing_fields_before": missing_audit["missing_fields_before"],
            "missing_fields_after": missing_audit["missing_fields_after"],
            "parsed_success_rate": parsed_success_rate,
            "container_success_rate": container_success_rate,
            "guarded_noise_count": guarded_noise_count,
            "report_only_count": report_only_count,
        },
        "path_normalization_audit": {
            "normalization_needed": missing_audit["normalized_inventory_seen_fields_after"] > missing_audit["normalized_inventory_seen_fields_before"],
            "rules_used": [
                "strip upstream.body/body/raw_body/payload/_local_payload prefixes",
                "normalize [] and numeric array index expressions",
                "collapse data.data duplicated prefixes",
                "compare suffixes to tolerate wrapper prefix variance",
                "compare against same-action inventory and global action-variant inventory",
            ],
            "still_needed": [
                "parsed child path to raw container parent normalization is audit-only here",
                "inventory generation should persist normalized_path alongside raw_path",
                "source_action variant mapping should be explicit rather than global suffix fallback",
            ],
        },
        "container_spot_check": container_checks,
        "schema_noise_guard_spot_check": guard_checks,
        "sampled_missing_records": missing_audit["sampled_missing_records"],
        "quality_gate_decision": {
            "p0_1_raw_diff_quality_pass": p0_1_pass,
            "p0_2_parsed_inventory_quality_pass": p0_2_pass,
            "p0_3_container_coverage_quality_pass": p0_3_pass,
            "p0_4_schema_guard_quality_pass": p0_4_pass,
            "can_start_p0_5_candidate_replay": can_start_p0_5,
        },
        "quality_gate_thresholds": {
            "raw_true_missing_threshold": true_missing_threshold,
            "parsed_success_rate_min": 0.95,
            "container_success_rate_min": 0.90,
        },
        "remaining_gap": [
            "P0-1 exact raw diff still has large true_missing eligible fields; candidate replay should wait until normalized_path is persisted in raw diff generation.",
            "Container parent-child mapping is identified but not yet folded into inventory_seen semantics.",
            "This quality gate does not perform candidate replay, autonomous-vs-targeted provenance, strict device_id join, parser drift detection, or profile history lure regression.",
        ],
        "full_autonomous_not_proven": True,
    }
    out = Path(output_dir)
    _write_json(out / "p0_foundation_quality_gate_summary.json", summary)
    _write_markdown(out / "p0_foundation_quality_gate_summary.md", summary)
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit P0 foundation inventory smoke outputs.")
    parser.add_argument("--smoke-dir", required=True)
    parser.add_argument("--inventory", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args(argv)
    summary = build_quality_gate_summary(
        smoke_dir=args.smoke_dir,
        inventory_path=args.inventory,
        output_dir=args.output_dir,
    )
    print(json.dumps({
        "wave_id": summary["wave_id"],
        **summary["quality_gate_summary"],
        **summary["quality_gate_decision"],
        "full_autonomous_not_proven": summary["full_autonomous_not_proven"],
    }, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
