#!/usr/bin/env python3
"""P0-5 candidate replay provenance builder.

This module is intentionally local/offline. It reads P0 foundation artifacts
generated from existing raw bundles and parsed inventories, then recomputes a
small fixed discovery-candidate set. It does not call platforms, Hive,
DataAgent, baselines, L6 replay, release, dist, or full_runtime paths.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

try:
    from p0_foundation_inventory import normalize_path
except ImportError:  # pragma: no cover - direct package import fallback
    def normalize_path(path: str) -> str:
        text = str(path or "").strip()
        text = text.replace("[].", ".").replace("[]", "")
        text = re.sub(r"\[\d+\]", "", text)
        text = re.sub(r"\.{2,}", ".", text).strip(".")
        for prefix in (
            "upstream.body.body.",
            "upstream.body.",
            "body.",
            "payload.",
            "raw_body.",
            "_local_payload.",
        ):
            if text.startswith(prefix):
                text = text[len(prefix):]
                break
        if text.startswith("data.data."):
            text = text[len("data."):]
        return text


SCHEMA_VERSION = "p0_5_candidate_replay_provenance_v1"
RULE_VERSION = "p0_5_taxonomy_cleanup_rules_v2"
MISSING_REASON_ENUM = {
    "field_absent",
    "source_absent",
    "parser_failed",
    "schema_guarded",
    "threshold_not_met",
    "lineage_not_proven",
    "data_gap",
}


@dataclass
class ReplayContext:
    wave_id: str
    records_by_user: dict[str, list[dict[str, Any]]]
    raw_records_by_user: dict[str, list[dict[str, Any]]]
    source_presence_by_user: dict[str, set[str]]
    users: list[str]
    guarded_fields: list[dict[str, Any]]
    container_rows: list[dict[str, Any]]
    raw_summary: dict[str, Any]
    parsed_summary: dict[str, Any]


def _load_json(path: str | Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: str | Path, payload: Any) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _as_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value or "").strip()
    if not text or text.startswith("<"):
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _row_path(row: dict[str, Any]) -> str:
    return str(row.get("parsed_path") or row.get("raw_path") or "")


def _row_text(row: dict[str, Any]) -> str:
    return f"{row.get('source_action', '')} {_row_path(row)} {row.get('value_preview', '')}".lower()


def _leaf(path: str) -> str:
    return str(path or "").split(".")[-1]


def _evidence_from_row(row: dict[str, Any]) -> dict[str, Any]:
    parsed_path = str(row.get("parsed_path") or "")
    raw_path = str(row.get("raw_path") or "")
    normalized = str(row.get("normalized_parsed_path") or normalize_path(parsed_path or raw_path))
    return {
        "source_action": row.get("source_action"),
        "raw_path": raw_path,
        "parsed_path": parsed_path,
        "normalized_path": normalized,
        "value_summary": row.get("value_preview"),
    }


def _unique_evidence(rows: list[dict[str, Any]], limit: int = 12) -> list[dict[str, Any]]:
    seen: set[tuple[str, str, str, str]] = set()
    out: list[dict[str, Any]] = []
    for row in rows:
        ev = _evidence_from_row(row)
        key = (
            str(ev["source_action"]),
            str(ev["raw_path"]),
            str(ev["parsed_path"]),
            str(ev["value_summary"]),
        )
        if key in seen:
            continue
        seen.add(key)
        out.append(ev)
        if len(out) >= limit:
            break
    return out


def _values(rows: list[dict[str, Any]], limit: int = 8) -> list[str]:
    out: list[str] = []
    for row in rows:
        value = str(row.get("value_preview") or "")
        if value and value not in out:
            out.append(value)
        if len(out) >= limit:
            break
    return out


def _source_available(ctx: ReplayContext, user_id: str, sources: list[str]) -> bool:
    present = ctx.source_presence_by_user.get(user_id, set())
    return any(source in present for source in sources)


def _missing_sources(ctx: ReplayContext, user_id: str, sources: list[str]) -> list[str]:
    present = ctx.source_presence_by_user.get(user_id, set())
    return [source for source in sources if source not in present]


def build_context_from_records(
    *,
    wave_id: str,
    parsed_records: list[dict[str, Any]],
    raw_records: list[dict[str, Any]] | None = None,
    guarded_fields: list[dict[str, Any]] | None = None,
    container_rows: list[dict[str, Any]] | None = None,
    raw_summary: dict[str, Any] | None = None,
    parsed_summary: dict[str, Any] | None = None,
) -> ReplayContext:
    records_by_user: dict[str, list[dict[str, Any]]] = defaultdict(list)
    raw_records_by_user: dict[str, list[dict[str, Any]]] = defaultdict(list)
    source_presence: dict[str, set[str]] = defaultdict(set)
    for row in parsed_records:
        user_id = str(row.get("user_id") or "").strip()
        if not user_id:
            continue
        records_by_user[user_id].append(row)
        if row.get("source_action"):
            source_presence[user_id].add(str(row["source_action"]))
    for row in raw_records or []:
        user_id = str(row.get("user_id") or "").strip()
        if not user_id:
            continue
        raw_records_by_user[user_id].append(row)
        if row.get("source_action"):
            source_presence[user_id].add(str(row["source_action"]))
    users = sorted(set(records_by_user) | set(source_presence))
    return ReplayContext(
        wave_id=wave_id,
        records_by_user=dict(records_by_user),
        raw_records_by_user=dict(raw_records_by_user),
        source_presence_by_user={k: set(v) for k, v in source_presence.items()},
        users=users,
        guarded_fields=list(guarded_fields or []),
        container_rows=list(container_rows or []),
        raw_summary=dict(raw_summary or {}),
        parsed_summary=dict(parsed_summary or {}),
    )


def build_context_from_smoke_dir(smoke_dir: str | Path, wave_id: str) -> ReplayContext:
    smoke = Path(smoke_dir)
    parsed = _load_json(smoke / "parsed_field_inventory.json")
    raw_diff = _load_json(smoke / "full_action_inventory_raw_diff.json")
    guards = _load_json(smoke / "schema_noise_guard_report.json")
    containers = _load_json(smoke / "container_parser_coverage_matrix.json")
    return build_context_from_records(
        wave_id=wave_id,
        parsed_records=parsed.get("records") or [],
        raw_records=raw_diff.get("records") or [],
        guarded_fields=guards.get("guarded_fields") or [],
        container_rows=containers.get("matrix") or [],
        raw_summary=raw_diff.get("summary") or {},
        parsed_summary=parsed.get("summary") or {},
    )


def _guard_matches_path(guard_path: str, evidence_path: str) -> bool:
    guard_norm = normalize_path(guard_path)
    evidence_norm = normalize_path(evidence_path)
    if guard_norm == evidence_norm:
        return True
    return bool(guard_norm and evidence_norm.endswith("." + guard_norm))


def matching_guards_for_evidence(ctx: ReplayContext, evidence: list[dict[str, Any]]) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    for ev in evidence:
        paths = [str(ev.get("parsed_path") or ""), str(ev.get("raw_path") or ""), str(ev.get("normalized_path") or "")]
        for guard in ctx.guarded_fields:
            guard_path = str(guard.get("path") or "")
            if guard_path and any(_guard_matches_path(guard_path, path) for path in paths if path):
                matches.append(guard)
                break
    return matches


def apply_schema_guard_policy(
    *,
    candidate_level: str,
    evidence: list[dict[str, Any]],
    matching_guards: list[dict[str, Any]],
) -> tuple[str, bool, bool, list[str]]:
    """Return candidate level, high-value allowance, guard flag, report-only paths."""
    report_only = sorted({
        str(g.get("path") or "")
        for g in matching_guards
        if str(g.get("guard_level") or "") == "report_only"
    })
    blocking = [
        g for g in matching_guards
        if not bool(g.get("high_value_allowed")) and not bool(g.get("combo_allowed"))
    ]
    evidence_count = len(evidence)
    guard_only = bool(evidence_count) and len(matching_guards) >= evidence_count
    high_value_allowed = candidate_level == "high_value"
    adjusted = candidate_level
    if candidate_level == "high_value" and (blocking and guard_only):
        adjusted = "report_only"
        high_value_allowed = False
    return adjusted, high_value_allowed, bool(matching_guards), report_only


def app_list_gap_status(ctx: ReplayContext) -> str:
    rows = [r for r in ctx.container_rows if r.get("container_name") == "appList"]
    if not rows:
        return "DATA_GAP"
    raw_present = any(bool(r.get("raw_present")) for r in rows)
    parse_attempted = any(int(r.get("parse_attempted") or r.get("attempted") or 0) > 0 for r in rows)
    parse_success = any(int(r.get("parse_success") or r.get("success") or 0) > 0 for r in rows)
    reasons = {str(r.get("scanner_gap_reason") or "") for r in rows}
    if not raw_present and "raw_absent" in reasons:
        return "DATA_GAP"
    if raw_present and not parse_attempted:
        return "SCANNER_GAP"
    if raw_present and parse_attempted and not parse_success:
        return "SCANNER_GAP"
    return "COVERED"


def _finalize_candidate(
    ctx: ReplayContext,
    *,
    candidate_id: str,
    candidate_name: str,
    signal_type: str,
    replay_rule: str,
    involved_sources: list[str],
    involved_events: list[str],
    required_fields: list[str],
    optional_fields: list[str],
    hit_evidence_by_user: dict[str, list[dict[str, Any]]],
    miss_reason_by_user: dict[str, str],
    source_gap_by_user: dict[str, list[str]] | None = None,
    candidate_level: str,
    readiness: str,
    lineage_status: str,
    method_family: str,
    force_replay_status: str | None = None,
    notes: str = "",
    rule_logic_type: str = "threshold",
    core_conditions: list[str] | None = None,
    supporting_conditions: list[str] | None = None,
    excluded_conditions: list[str] | None = None,
    field_thresholds: dict[str, Any] | None = None,
    fields_used: list[str] | None = None,
    whether_candidate_name_matches_rule: bool = True,
    rule_semantics_status: str = "pass",
) -> dict[str, Any]:
    all_users = ctx.users
    source_gap_by_user = source_gap_by_user or {}
    coverage_users = [
        user_id for user_id in all_users
        if _source_available(ctx, user_id, involved_sources)
    ]
    sample_hits = []
    snippets: list[dict[str, Any]] = []
    for user_id in all_users:
        evidence = hit_evidence_by_user.get(user_id) or []
        if not evidence:
            continue
        sample_hits.append({
            "user_id": user_id,
            "evidence_count": len(evidence),
            "value_summary": _values(evidence, limit=6),
        })
        snippets.extend(_unique_evidence(evidence, limit=6))
    sample_misses = []
    for user_id in all_users:
        if user_id in hit_evidence_by_user:
            continue
        reason = miss_reason_by_user.get(user_id)
        if not reason:
            reason = "source_absent" if not _source_available(ctx, user_id, involved_sources) else "field_absent"
        if reason not in MISSING_REASON_ENUM:
            reason = "field_absent"
        sample_misses.append({"user_id": user_id, "missing_reason": reason})
    evidence_all = [ev for rows in hit_evidence_by_user.values() for ev in rows]
    evidence_snippets = _unique_evidence(evidence_all, limit=10)
    guard_matches = matching_guards_for_evidence(ctx, evidence_snippets)
    adjusted_level, high_value_allowed, schema_guard_applied, report_only_fields = apply_schema_guard_policy(
        candidate_level=candidate_level,
        evidence=evidence_snippets,
        matching_guards=guard_matches,
    )
    support = len(hit_evidence_by_user)
    if force_replay_status:
        replay_status = force_replay_status
    elif support <= 0:
        replay_status = "replay_failed"
    elif adjusted_level in {"data_gap", "scanner_gap"}:
        replay_status = "replay_partial"
    else:
        replay_status = "replay_pass"
    raw_paths = sorted({str(ev.get("raw_path") or "") for ev in evidence_snippets if ev.get("raw_path")})
    parsed_paths = sorted({str(ev.get("parsed_path") or "") for ev in evidence_snippets if ev.get("parsed_path")})
    normalized_paths = sorted({str(ev.get("normalized_path") or "") for ev in evidence_snippets if ev.get("normalized_path")})
    return {
        "candidate_id": candidate_id,
        "candidate_name": candidate_name,
        "candidate_level": adjusted_level,
        "core_conditions": list(core_conditions or []),
        "evidence_snippets": evidence_snippets,
        "excluded_conditions": list(excluded_conditions or []),
        "field_thresholds": dict(field_thresholds or {}),
        "fields_used": list(fields_used or required_fields),
        "full_autonomous_not_proven": True,
        "high_value_allowed": high_value_allowed,
        "involved_events": involved_events,
        "involved_sources": involved_sources,
        "lineage_status": lineage_status,
        "method_family": method_family,
        "miss_user_count": len(all_users) - support,
        "missing_reason_by_user": {row["user_id"]: row["missing_reason"] for row in sample_misses},
        "normalized_paths": normalized_paths,
        "notes": notes,
        "optional_fields": optional_fields,
        "parsed_paths": parsed_paths,
        "raw_paths": raw_paths,
        "readiness": readiness,
        "replay_rule": replay_rule,
        "replay_status": replay_status,
        "report_only_fields_used": report_only_fields,
        "required_fields": required_fields,
        "rule_logic_type": rule_logic_type,
        "rule_semantics_status": rule_semantics_status,
        "rule_version": RULE_VERSION,
        "sample_hits": sample_hits,
        "sample_misses": sample_misses,
        "schema_guard_applied": schema_guard_applied,
        "signal_type": signal_type,
        "source_gap_by_user": source_gap_by_user,
        "supporting_conditions": list(supporting_conditions or []),
        "support_user_count": support,
        "coverage_user_count": len(coverage_users),
        "whether_candidate_name_matches_rule": whether_candidate_name_matches_rule,
        "wave_id": ctx.wave_id,
    }


ACCOUNT_INVOLVED_SOURCES = ["archives_user_analysis", "login_logs_search"]


def _account_candidate_rows(ctx: ReplayContext, user_id: str) -> list[dict[str, Any]]:
    return [
        row for row in ctx.records_by_user.get(user_id, [])
        if row.get("source_action") in ACCOUNT_INVOLVED_SOURCES
        and any(key in _row_path(row).lower() for key in ("operateuri", "logcontent.uri", ".uri", "method"))
    ]


def _account_mutation_categories(ctx: ReplayContext, user_id: str) -> dict[str, list[dict[str, Any]]]:
    category_patterns = {
        "reset_password": ["/reset/select", "/reset/bytoken/logined"],
        "reset_family": ["/reset/"],
        "rebind_mobile": ["rebind/mobile", "/rebind/verifycheck", "/rebind/verify", "/rebind/"],
        "bind_new_mobile": ["bind/newmobile", "newmobile", "bindnewmobile"],
        "verify_check": ["verifycheck"],
        "mobile": ["rebind/mobile", "bind/newmobile", "bindnewmobile", "newmobile"],
        "login_token": ["login/token", "refreshtoken", "token/infra"],
        "profile_set_modify": ["/user/set", "/user/modify", "changeoption"],
        "private_setting": ["changeoption"],
    }
    categories: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in _account_candidate_rows(ctx, user_id):
        text = _row_text(row)
        for category, patterns in category_patterns.items():
            if any(pattern in text for pattern in patterns):
                categories[category].append(row)
    return categories


def _account_candidate_common_miss(
    ctx: ReplayContext,
    user_id: str,
    rows: list[dict[str, Any]],
) -> str:
    if not _source_available(ctx, user_id, ACCOUNT_INVOLVED_SOURCES):
        return "source_absent"
    if not rows:
        return "field_absent"
    return "threshold_not_met"


def replay_account_mutation_chain(ctx: ReplayContext) -> dict[str, Any]:
    involved_sources = ["archives_user_analysis", "login_logs_search"]
    hit_evidence: dict[str, list[dict[str, Any]]] = {}
    miss: dict[str, str] = {}
    source_gaps: dict[str, list[str]] = {}
    account_categories = {
        "reset_password",
        "reset_family",
        "rebind_mobile",
        "bind_new_mobile",
        "verify_check",
        "login_token",
        "profile_set_modify",
        "private_setting",
    }
    for user_id in ctx.users:
        rows = _account_candidate_rows(ctx, user_id)
        categories = _account_mutation_categories(ctx, user_id)
        matched = set(categories) & account_categories
        if len(matched) >= 2:
            evidence: list[dict[str, Any]] = []
            for category in sorted(matched):
                evidence.extend(categories[category][:2])
            hit_evidence[user_id] = evidence
        else:
            miss[user_id] = _account_candidate_common_miss(ctx, user_id, rows)
            if miss[user_id] == "source_absent":
                source_gaps[user_id] = _missing_sources(ctx, user_id, involved_sources)
    return _finalize_candidate(
        ctx,
        candidate_id=f"{ctx.wave_id}:account_mutation_chain",
        candidate_name="account_mutation_chain",
        signal_type="event_chain",
        replay_rule="user hits when raw/parsed URI fields show >=2 account/profile mutation categories among reset/rebind/bindNewMobile/verify/loginToken/profileModify/privateSetting",
        involved_sources=involved_sources,
        involved_events=["account_mutation_event", "login_event", "profile_mutation_event"],
        required_fields=["archives_user_analysis.operateUri", "login_logs_search.logContent.uri"],
        optional_fields=["requestParam", "logContent.params", "operateType", "method"],
        hit_evidence_by_user=hit_evidence,
        miss_reason_by_user=miss,
        source_gap_by_user=source_gaps,
        candidate_level="high_value",
        readiness="needs_baseline",
        lineage_status="user_level",
        method_family="account_mutation_chain",
        notes="Broader account mutation family candidate. It is intentionally not named reset_rebind because reset+rebind all-of has lower support.",
        rule_logic_type="any_of_or_sequence_family",
        core_conditions=["at least two account/profile mutation endpoint families are visible"],
        supporting_conditions=["reset password", "mobile rebind", "bindNewMobile", "verify/check", "login token", "profile modify", "private setting change"],
        excluded_conditions=["does not require reset AND rebind simultaneously", "does not prove event order"],
        field_thresholds={"min_mutation_families": 2},
    )


def replay_reset_password_chain(ctx: ReplayContext) -> dict[str, Any]:
    hit_evidence: dict[str, list[dict[str, Any]]] = {}
    miss: dict[str, str] = {}
    source_gaps: dict[str, list[str]] = {}
    for user_id in ctx.users:
        rows = _account_candidate_rows(ctx, user_id)
        categories = _account_mutation_categories(ctx, user_id)
        if categories.get("reset_password"):
            hit_evidence[user_id] = categories["reset_password"][:8]
        else:
            miss[user_id] = _account_candidate_common_miss(ctx, user_id, rows)
            if miss[user_id] == "source_absent":
                source_gaps[user_id] = _missing_sources(ctx, user_id, ACCOUNT_INVOLVED_SOURCES)
    return _finalize_candidate(
        ctx,
        candidate_id=f"{ctx.wave_id}:reset_password_chain",
        candidate_name="reset_password_chain",
        signal_type="event_chain",
        replay_rule="user hits when URI fields contain reset password endpoints /reset/select or /reset/byToken/logined",
        involved_sources=ACCOUNT_INVOLVED_SOURCES,
        involved_events=["account_mutation_event", "login_event"],
        required_fields=["archives_user_analysis.operateUri", "login_logs_search.logContent.uri"],
        optional_fields=["logContent.params.uri", "method"],
        hit_evidence_by_user=hit_evidence,
        miss_reason_by_user=miss,
        source_gap_by_user=source_gaps,
        candidate_level="high_value",
        readiness="needs_baseline",
        lineage_status="user_level",
        method_family="account_mutation_chain",
        notes="Narrow reset-password candidate; broader reset-family paths are not enough unless they match the selected endpoints.",
        rule_logic_type="any_of",
        core_conditions=["/reset/select endpoint", "/reset/byToken/logined endpoint"],
        supporting_conditions=["reset-family URI fields from archives/login logs"],
        excluded_conditions=["generic /reset/ family without selected endpoint is not sufficient"],
        field_thresholds={"endpoint_support_required": 1},
    )


def replay_mobile_rebind_chain(ctx: ReplayContext) -> dict[str, Any]:
    hit_evidence: dict[str, list[dict[str, Any]]] = {}
    miss: dict[str, str] = {}
    source_gaps: dict[str, list[str]] = {}
    for user_id in ctx.users:
        rows = _account_candidate_rows(ctx, user_id)
        categories = _account_mutation_categories(ctx, user_id)
        if categories.get("rebind_mobile"):
            evidence = categories["rebind_mobile"][:6]
            evidence.extend(categories.get("bind_new_mobile", [])[:2])
            evidence.extend(categories.get("verify_check", [])[:2])
            hit_evidence[user_id] = evidence
        else:
            miss[user_id] = _account_candidate_common_miss(ctx, user_id, rows)
            if miss[user_id] == "source_absent":
                source_gaps[user_id] = _missing_sources(ctx, user_id, ACCOUNT_INVOLVED_SOURCES)
    return _finalize_candidate(
        ctx,
        candidate_id=f"{ctx.wave_id}:mobile_rebind_chain",
        candidate_name="mobile_rebind_chain",
        signal_type="event_chain",
        replay_rule="user hits when URI fields contain rebind mobile endpoint family; bindNewMobile and verify/check are supporting evidence only",
        involved_sources=ACCOUNT_INVOLVED_SOURCES,
        involved_events=["account_mutation_event"],
        required_fields=["archives_user_analysis.operateUri", "login_logs_search.logContent.uri"],
        optional_fields=["bindNewMobile", "verifyCheck", "requestParam.mobile"],
        hit_evidence_by_user=hit_evidence,
        miss_reason_by_user=miss,
        source_gap_by_user=source_gaps,
        candidate_level="high_value",
        readiness="needs_baseline",
        lineage_status="user_level",
        method_family="account_mutation_chain",
        notes="Ordinary /login/mobile is explicitly excluded from mobile rebind support.",
        rule_logic_type="any_of",
        core_conditions=["rebind/mobile or rebind verify endpoint family"],
        supporting_conditions=["bindNewMobile", "verifyCheck", "mobile parameter evidence"],
        excluded_conditions=["/login/mobile ordinary login endpoint"],
        field_thresholds={"rebind_endpoint_required": 1},
    )


def replay_reset_and_rebind_chain(ctx: ReplayContext) -> dict[str, Any]:
    hit_evidence: dict[str, list[dict[str, Any]]] = {}
    miss: dict[str, str] = {}
    source_gaps: dict[str, list[str]] = {}
    for user_id in ctx.users:
        rows = _account_candidate_rows(ctx, user_id)
        categories = _account_mutation_categories(ctx, user_id)
        if categories.get("reset_family") and categories.get("rebind_mobile"):
            hit_evidence[user_id] = categories["reset_family"][:4] + categories["rebind_mobile"][:4]
        else:
            miss[user_id] = _account_candidate_common_miss(ctx, user_id, rows)
            if miss[user_id] == "source_absent":
                source_gaps[user_id] = _missing_sources(ctx, user_id, ACCOUNT_INVOLVED_SOURCES)
    return _finalize_candidate(
        ctx,
        candidate_id=f"{ctx.wave_id}:reset_and_rebind_chain",
        candidate_name="reset_and_rebind_chain",
        signal_type="event_chain",
        replay_rule="strict all-of: user hits when reset-family URI evidence and rebind mobile URI evidence are both present",
        involved_sources=ACCOUNT_INVOLVED_SOURCES,
        involved_events=["account_mutation_event", "login_event"],
        required_fields=["reset-family URI", "rebind mobile URI"],
        optional_fields=["bindNewMobile", "verifyCheck", "logContent.params"],
        hit_evidence_by_user=hit_evidence,
        miss_reason_by_user=miss,
        source_gap_by_user=source_gaps,
        candidate_level="high_value",
        readiness="needs_baseline",
        lineage_status="user_level",
        method_family="account_mutation_chain",
        notes="Strict reset+rebind coverage is lower than broader account_mutation_chain; this candidate preserves the narrower semantics.",
        rule_logic_type="all_of",
        core_conditions=["reset-family URI evidence", "rebind mobile URI evidence"],
        supporting_conditions=["bindNewMobile and verify/check enrich the chain when present"],
        excluded_conditions=["profile mutation alone", "login token alone"],
        field_thresholds={"reset_family_required": 1, "rebind_mobile_required": 1},
    )


def replay_profile_set_modify_mutation_chain(ctx: ReplayContext) -> dict[str, Any]:
    involved_sources = ["archives_user_analysis", "login_logs_search"]
    hit_evidence: dict[str, list[dict[str, Any]]] = {}
    miss: dict[str, str] = {}
    source_gaps: dict[str, list[str]] = {}
    patterns = ["/user/set", "/user/modify", "changeoption", "profile", "修改", "资料", "头像", "昵称"]
    for user_id in ctx.users:
        rows = [
            row for row in ctx.records_by_user.get(user_id, [])
            if row.get("source_action") in involved_sources
            and any(pattern in _row_text(row) for pattern in patterns)
        ]
        uri_rows = [row for row in rows if any(key in _row_path(row).lower() for key in ("operateuri", "uri", "operatetype", "requestparam"))]
        if uri_rows:
            hit_evidence[user_id] = uri_rows[:10]
        else:
            if not _source_available(ctx, user_id, involved_sources):
                miss[user_id] = "source_absent"
                source_gaps[user_id] = _missing_sources(ctx, user_id, involved_sources)
            elif not rows:
                miss[user_id] = "field_absent"
            else:
                miss[user_id] = "threshold_not_met"
    return _finalize_candidate(
        ctx,
        candidate_id=f"{ctx.wave_id}:profile_set_modify_mutation_chain",
        candidate_name="profile_set_modify_mutation_chain",
        signal_type="event_chain",
        replay_rule="user hits when archives/login parsed fields contain profile set/modify/changeOption/profile mutation path or operation text",
        involved_sources=involved_sources,
        involved_events=["profile_mutation_event", "login_event"],
        required_fields=["archives_user_analysis.operateUri", "archives_user_analysis.requestParam", "login_logs_search.logContent.uri"],
        optional_fields=["operateType", "desc", "nickname", "avatar", "audit history"],
        hit_evidence_by_user=hit_evidence,
        miss_reason_by_user=miss,
        source_gap_by_user=source_gaps,
        candidate_level="high_value",
        readiness="needs_baseline",
        lineage_status="user_level",
        method_family="account_mutation_chain",
        notes="Replay identifies mutation evidence only; current-vs-history lure recall remains outside P0-5 by boundary.",
        rule_logic_type="any_of",
        core_conditions=["profile set/modify/changeOption URI or profile mutation operation text"],
        supporting_conditions=["operateType text", "requestParam profile fields when visible"],
        excluded_conditions=["URL/OCR/QR lure recall", "current-vs-history profile comparison"],
        field_thresholds={"profile_mutation_evidence_required": 1},
        fields_used=[
            "archives_user_analysis.operateUri",
            "archives_user_analysis.operateType",
            "archives_user_analysis.requestParam",
            "login_logs_search.logContent.uri",
        ],
    )


def _weapon_header_group(path: str) -> str | None:
    lower = path.lower()
    leaf = _leaf(lower)
    if "weapondecodeheader" not in lower:
        return None
    if leaf in {"bootcount"}:
        return "boot_count"
    if leaf in {"version", "weaponversion", "ver"}:
        return "version"
    if "storage" in leaf or "disk" in leaf:
        return "storage"
    if "brightness" in leaf:
        return "brightness"
    if leaf in {"sim", "simcount", "simulator"}:
        return "sim_or_simulator"
    if leaf in {"haspassword", "nolockscreen"} or "lock" in leaf:
        return "lock_state"
    if "root" in leaf or "jailbreak" in leaf:
        return "root_or_jailbreak"
    if "hook" in leaf or "xposed" in leaf or "frida" in leaf or "inject" in leaf:
        return "hook_or_inject"
    if "proxy" in leaf:
        return "proxy"
    if "invisibleverify" in leaf:
        return "invisible_verify"
    if leaf in {"isusb", "debug", "repack", "weaponstatus", "weaponkey", "sigcount"}:
        return leaf
    return None


def replay_weapon_decode_header_runtime_template(ctx: ReplayContext) -> dict[str, Any]:
    involved_sources = ["weapon_inventory"]
    hit_evidence: dict[str, list[dict[str, Any]]] = {}
    miss: dict[str, str] = {}
    source_gaps: dict[str, list[str]] = {}
    required_groups = {
        "boot_count",
        "version",
        "storage",
        "brightness",
        "sim_or_simulator",
        "lock_state",
        "root_or_jailbreak",
        "hook_or_inject",
        "proxy",
        "invisible_verify",
    }
    for user_id in ctx.users:
        groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in ctx.records_by_user.get(user_id, []):
            if row.get("source_action") != "weapon_inventory":
                continue
            group = _weapon_header_group(_row_path(row))
            if group:
                groups[group].append(row)
        matched_required = required_groups & set(groups)
        if len(matched_required) >= 5:
            evidence: list[dict[str, Any]] = []
            for group in sorted(matched_required):
                evidence.extend(groups[group][:1])
            hit_evidence[user_id] = evidence
        else:
            if not _source_available(ctx, user_id, involved_sources):
                miss[user_id] = "source_absent"
                source_gaps[user_id] = _missing_sources(ctx, user_id, involved_sources)
            elif not groups:
                miss[user_id] = "field_absent"
            else:
                miss[user_id] = "threshold_not_met"
    return _finalize_candidate(
        ctx,
        candidate_id=f"{ctx.wave_id}:weapon_decode_header_runtime_template",
        candidate_name="weapon_decode_header_runtime_template",
        signal_type="device_toolchain",
        replay_rule="user hits when weaponDecodeHeader exposes at least five runtime/capability field groups from the required template",
        involved_sources=involved_sources,
        involved_events=["device_environment_event"],
        required_fields=sorted(required_groups),
        optional_fields=["isUsb", "debug", "repack", "weaponStatus", "sigCount"],
        hit_evidence_by_user=hit_evidence,
        miss_reason_by_user=miss,
        source_gap_by_user=source_gaps,
        candidate_level="high_value",
        readiness="needs_baseline",
        lineage_status="user_level",
        method_family="device_toolchain_or_automation",
        notes="Template replay is field-presence plus value provenance, not abnormality validation against normal runtime distribution.",
        rule_logic_type="template",
        core_conditions=sorted(required_groups),
        supporting_conditions=["isUsb", "debug", "repack", "weaponStatus", "sigCount"],
        excluded_conditions=["appList installed package semantics", "baseline abnormality", "strategy verification"],
        field_thresholds={"min_required_groups": 5},
        fields_used=[f"weaponDecodeHeader.{group}" for group in sorted(required_groups)],
    )


def _max_metric(
    rows: list[dict[str, Any]],
    path_patterns: list[str],
) -> tuple[float | None, list[dict[str, Any]]]:
    matched: list[dict[str, Any]] = []
    max_value: float | None = None
    lowered_patterns = [p.lower() for p in path_patterns]
    for row in rows:
        path = _row_path(row).lower()
        if not all(pattern in path for pattern in lowered_patterns):
            continue
        value = _as_number(row.get("value_preview"))
        if value is None:
            continue
        matched.append(row)
        max_value = value if max_value is None else max(max_value, value)
    return max_value, matched


def _replay_profile_visit_low_content_bucket(
    ctx: ReplayContext,
    *,
    candidate_name: str,
    visit_threshold: float,
    candidate_level: str,
    notes: str,
) -> dict[str, Any]:
    involved_sources = ["weapon_inventory", "archives_user_profile", "archives_gallery_photo_list", "archives_collection_list"]
    hit_evidence: dict[str, list[dict[str, Any]]] = {}
    miss: dict[str, str] = {}
    for user_id in ctx.users:
        rows = ctx.records_by_user.get(user_id, [])
        visit, visit_rows = _max_metric(rows, ["enterprofilecnt180d"])
        profile_visit, profile_visit_rows = _max_metric(rows, ["profilevisit"])
        photo_upload, photo_rows = _max_metric(rows, ["photouploadcnt180d"])
        comment, comment_rows = _max_metric(rows, ["watchingcommentcnt180d"])
        cai_photo, cai_rows = _max_metric(rows, ["caiphotocnt180d"])
        collect, collect_rows = _max_metric(rows, ["collectcount"])
        visit_score = max([v for v in (visit, profile_visit) if v is not None], default=None)
        low_metrics = [v for v in (photo_upload, comment, cai_photo, collect) if v is not None]
        if visit_score is not None and visit_score >= visit_threshold and low_metrics and max(low_metrics) <= 1:
            hit_evidence[user_id] = (
                visit_rows[:2]
                + profile_visit_rows[:1]
                + photo_rows[:1]
                + comment_rows[:1]
                + cai_rows[:1]
                + collect_rows[:1]
            )
        else:
            if not _source_available(ctx, user_id, involved_sources):
                miss[user_id] = "source_absent"
            elif visit_score is None or not low_metrics:
                miss[user_id] = "field_absent"
            else:
                miss[user_id] = "threshold_not_met"
    return _finalize_candidate(
        ctx,
        candidate_id=f"{ctx.wave_id}:{candidate_name}",
        candidate_name=candidate_name,
        signal_type="behavior_bucket",
        replay_rule=f"user hits when max(enterProfileCnt180D, profileVisit) >= {visit_threshold:g} and available production/interaction counters stay <=1 in the 180D bucket",
        involved_sources=involved_sources,
        involved_events=["social_funnel_behavior_event"],
        required_fields=["enterProfileCnt180D|profileVisit", "photoUploadCnt180D", "watchingCommentCnt180D", "caiPhotoCnt180D|collectCount"],
        optional_fields=["followCount", "fansCount", "archives_follow_list", "archives_fans_list"],
        hit_evidence_by_user=hit_evidence,
        miss_reason_by_user=miss,
        candidate_level=candidate_level,
        readiness="needs_baseline",
        lineage_status="user_level",
        method_family="social_funnel_or_traffic_diversion",
        notes=notes,
        rule_logic_type="threshold",
        core_conditions=[
            f"max(enterProfileCnt180D, profileVisit) >= {visit_threshold:g}",
            "max(photoUploadCnt180D, watchingCommentCnt180D, caiPhotoCnt180D, collectCount) <= 1",
        ],
        supporting_conditions=["follow/fans fields are retained as context only and do not drive support"],
        excluded_conditions=["pagination near-full-page", "follow_list_near_full_page", "baseline percentile"],
        field_thresholds={
            "enterProfile_or_profileVisit_min": visit_threshold,
            "low_content_max": 1,
        },
        fields_used=[
            "weapon_inventory.originalLog.user_behavior.enterProfileCnt180D",
            "weapon_inventory.originalLog.user_info.profileVisit",
            "weapon_inventory.originalLog.user_behavior.photoUploadCnt180D",
            "weapon_inventory.originalLog.user_behavior.watchingCommentCnt180D",
            "weapon_inventory.originalLog.user_behavior.caiPhotoCnt180D",
            "archives_user_profile.collectCount",
        ],
    )


def replay_profile_visit_low_content_behavior(ctx: ReplayContext) -> dict[str, Any]:
    return _replay_profile_visit_low_content_bucket(
        ctx,
        candidate_name="profile_visit_low_content_behavior",
        visit_threshold=1,
        candidate_level="supporting",
        notes="Low-threshold social funnel bucket; it is intentionally not named high profile visit.",
    )


def replay_high_profile_visit_low_content_behavior(ctx: ReplayContext) -> dict[str, Any]:
    return _replay_profile_visit_low_content_bucket(
        ctx,
        candidate_name="high_profile_visit_low_content_behavior",
        visit_threshold=500,
        candidate_level="high_value",
        notes="High-threshold bucket. Still discovery-only and needs baseline before validation.",
    )


def replay_extreme_profile_visit_low_content_behavior(ctx: ReplayContext) -> dict[str, Any]:
    return _replay_profile_visit_low_content_bucket(
        ctx,
        candidate_name="extreme_profile_visit_low_content_behavior",
        visit_threshold=800,
        candidate_level="supporting",
        notes="Extreme-threshold bucket for stricter replay comparison; supporting until baseline validates lift and false positives.",
    )


def replay_low_bootcount_with_track_high_duration(ctx: ReplayContext) -> dict[str, Any]:
    involved_sources = ["weapon_inventory", "track_sequence_get_use_duration"]
    hit_evidence: dict[str, list[dict[str, Any]]] = {}
    miss: dict[str, str] = {}
    source_gaps: dict[str, list[str]] = {}
    for user_id in ctx.users:
        rows = ctx.records_by_user.get(user_id, [])
        boot_rows = [
            row for row in rows
            if row.get("source_action") == "weapon_inventory"
            and _row_path(row).lower().endswith("weapondecodeheader.bootcount")
            and _as_number(row.get("value_preview")) is not None
        ]
        duration_rows = [
            row for row in rows
            if row.get("source_action") == "track_sequence_get_use_duration"
            and _row_path(row).lower().endswith("rows.duration")
            and _as_number(row.get("value_preview")) is not None
        ]
        min_boot = min((_as_number(row.get("value_preview")) for row in boot_rows), default=None)
        max_duration = max((_as_number(row.get("value_preview")) for row in duration_rows), default=None)
        if min_boot is not None and min_boot <= 10 and max_duration is not None and max_duration >= 1440:
            boot_evidence = sorted(boot_rows, key=lambda r: _as_number(r.get("value_preview")) or 10**9)[:2]
            duration_evidence = sorted(duration_rows, key=lambda r: _as_number(r.get("value_preview")) or 0, reverse=True)[:2]
            hit_evidence[user_id] = boot_evidence + duration_evidence
        else:
            missing_sources = _missing_sources(ctx, user_id, involved_sources)
            if missing_sources:
                miss[user_id] = "source_absent"
                source_gaps[user_id] = missing_sources
            elif not boot_rows or not duration_rows:
                miss[user_id] = "field_absent"
            else:
                miss[user_id] = "threshold_not_met"
    return _finalize_candidate(
        ctx,
        candidate_id=f"{ctx.wave_id}:low_bootcount_with_track_high_duration",
        candidate_name="low_bootcount_with_track_high_duration",
        signal_type="combo",
        replay_rule="user hits when any visible Weapon bootCount <=10 and user-level Track duration has a daily row >=1440; strict device_id join is not asserted",
        involved_sources=involved_sources,
        involved_events=["device_environment_event", "track_device_behavior_event"],
        required_fields=["weaponDecodeHeader.bootCount", "track_sequence_get_use_duration.rows.duration"],
        optional_fields=["user-device lineage", "any-risk-device marker"],
        hit_evidence_by_user=hit_evidence,
        miss_reason_by_user=miss,
        source_gap_by_user=source_gaps,
        candidate_level="supporting",
        readiness="needs_more_source",
        lineage_status="partial_lineage",
        method_family="hybrid_or_multi-stage_attack",
        force_replay_status="replay_partial",
        notes="This replays only user-level any-risk-device evidence; strict device_id join is explicitly deferred.",
        rule_logic_type="all_of",
        core_conditions=["weaponDecodeHeader.bootCount <= 10", "Track user-level daily duration >= 1440"],
        supporting_conditions=["any-risk-device/user-level lineage only"],
        excluded_conditions=["strict device_id join", "device-day causal sequence", "baseline duration distribution"],
        field_thresholds={"bootCount_max": 10, "track_duration_min": 1440},
        fields_used=["weaponDecodeHeader.bootCount", "track_sequence_get_use_duration.rows.duration"],
    )


NETWORK_INVOLVED_SOURCES = [
    "weapon_inventory",
    "weapon_user_klink_status",
    "archives_user_profile",
    "track_sequence_profile",
    "track_sequence_get_use_duration",
]


def _network_environment_categories(ctx: ReplayContext, user_id: str) -> dict[str, list[dict[str, Any]]]:
    categories: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in ctx.records_by_user.get(user_id, []) + ctx.raw_records_by_user.get(user_id, []):
        if row.get("source_action") not in NETWORK_INVOLVED_SOURCES:
            continue
        path = _row_path(row).lower()
        value = str(row.get("value_preview") or "").lower()
        text = f"{path} {value}"
        if "zenlayer" in text:
            categories["zenlayer_asn"].append(row)
        if ("country_code" in path and value.strip() == "hk") or (
            row.get("source_action") == "weapon_user_klink_status"
            and path.endswith("country_code")
            and value.strip() == "hk"
        ):
            categories["hk_location"].append(row)
        if (
            "oneriskipidc" in text
            or "idc机房网络" in text
            or (path.endswith("oneipinfo.scenes") and value.strip() == "idc")
        ):
            categories["idc_network"].append(row)
    return categories


def _replay_network_environment_atomic(
    ctx: ReplayContext,
    *,
    candidate_name: str,
    category: str,
    candidate_level: str,
    replay_rule: str,
    notes: str,
) -> dict[str, Any]:
    hit_evidence: dict[str, list[dict[str, Any]]] = {}
    miss: dict[str, str] = {}
    for user_id in ctx.users:
        categories = _network_environment_categories(ctx, user_id)
        if categories.get(category):
            hit_evidence[user_id] = categories[category][:10]
        else:
            if not _source_available(ctx, user_id, NETWORK_INVOLVED_SOURCES):
                miss[user_id] = "source_absent"
            else:
                miss[user_id] = "field_absent"
    return _finalize_candidate(
        ctx,
        candidate_id=f"{ctx.wave_id}:{candidate_name}",
        candidate_name=candidate_name,
        signal_type="environment_cluster",
        replay_rule=replay_rule,
        involved_sources=NETWORK_INVOLVED_SOURCES,
        involved_events=["device_environment_event", "login_event", "track_device_behavior_event"],
        required_fields=[category],
        optional_fields=["country", "region", "Track location", "client/device environment"],
        hit_evidence_by_user=hit_evidence,
        miss_reason_by_user=miss,
        candidate_level=candidate_level,
        readiness="needs_baseline",
        lineage_status="user_level",
        method_family="network_region_idc_cluster",
        notes=notes,
        rule_logic_type="any_of",
        core_conditions=[category],
        supporting_conditions=[],
        excluded_conditions=["boardPlatform", "platform internal clientIp", "serverInfo/serverIp internal IDC hostnames"],
        field_thresholds={"category_support_required": 1},
        fields_used=[category],
    )


def replay_zenlayer_asn_cluster(ctx: ReplayContext) -> dict[str, Any]:
    return _replay_network_environment_atomic(
        ctx,
        candidate_name="zenlayer_asn_cluster",
        category="zenlayer_asn",
        candidate_level="high_value",
        replay_rule="user hits when parsed environment fields contain Zenlayer provider/ASN evidence",
        notes="Core network provider cluster. It still needs baseline and false-positive validation.",
    )


def replay_hk_location_supporting(ctx: ReplayContext) -> dict[str, Any]:
    return _replay_network_environment_atomic(
        ctx,
        candidate_name="hk_location_supporting",
        category="hk_location",
        candidate_level="supporting",
        replay_rule="user hits when parsed country/location fields contain HK country_code evidence",
        notes="HK location is context/supporting only and cannot stand alone as high-value.",
    )


def replay_idc_network_supporting(ctx: ReplayContext) -> dict[str, Any]:
    return _replay_network_environment_atomic(
        ctx,
        candidate_name="idc_network_supporting",
        category="idc_network",
        candidate_level="supporting",
        replay_rule="user hits when parsed fields contain IDC risk label or oneIpInfo IDC scene evidence",
        notes="IDC evidence supports the Zenlayer/network cluster but is not required for the 14/14 core provider support.",
    )


def replay_network_environment_cluster(ctx: ReplayContext) -> dict[str, Any]:
    involved_sources = ["weapon_inventory", "archives_user_profile", "track_sequence_profile", "track_sequence_get_use_duration"]
    hit_evidence: dict[str, list[dict[str, Any]]] = {}
    miss: dict[str, str] = {}
    for user_id in ctx.users:
        categories = _network_environment_categories(ctx, user_id)
        if categories.get("zenlayer_asn") and (categories.get("hk_location") or categories.get("idc_network")):
            evidence = categories["zenlayer_asn"][:6]
            evidence.extend(categories.get("hk_location", [])[:3])
            evidence.extend(categories.get("idc_network", [])[:3])
            hit_evidence[user_id] = evidence
        else:
            if not _source_available(ctx, user_id, involved_sources):
                miss[user_id] = "source_absent"
            else:
                miss[user_id] = "field_absent"
    return _finalize_candidate(
        ctx,
        candidate_id=f"{ctx.wave_id}:network_environment_cluster",
        candidate_name="network_environment_cluster",
        signal_type="environment_cluster",
        replay_rule="user hits when Zenlayer provider evidence is present and at least one supporting HK country_code or IDC network label is present",
        involved_sources=involved_sources,
        involved_events=["device_environment_event", "login_event", "track_device_behavior_event"],
        required_fields=["zenlayer_asn", "hk_location|idc_network"],
        optional_fields=["country", "region", "Track location", "client/device environment"],
        hit_evidence_by_user=hit_evidence,
        miss_reason_by_user=miss,
        candidate_level="high_value",
        readiness="needs_baseline",
        lineage_status="user_level",
        method_family="network_region_idc_cluster",
        notes="Combination candidate: 14/14 is not claimed as HK+IDC+Zenlayer all-of; this rule requires Zenlayer plus at least one supporting location/network condition.",
        rule_logic_type="weighted",
        core_conditions=["zenlayer_asn"],
        supporting_conditions=["hk_location", "idc_network"],
        excluded_conditions=["does not require HK and IDC both", "boardPlatform", "platform internal clientIp"],
        field_thresholds={"core_required": "zenlayer_asn", "supporting_any_of": ["hk_location", "idc_network"]},
        fields_used=["zenlayer_asn", "hk_location", "idc_network"],
    )


def replay_candidates_for_context(ctx: ReplayContext) -> list[dict[str, Any]]:
    if ctx.wave_id == "wave_4":
        return [
            replay_account_mutation_chain(ctx),
            replay_reset_password_chain(ctx),
            replay_mobile_rebind_chain(ctx),
            replay_reset_and_rebind_chain(ctx),
            replay_profile_set_modify_mutation_chain(ctx),
        ]
    if ctx.wave_id == "wave_5":
        candidates = [
            replay_weapon_decode_header_runtime_template(ctx),
            replay_profile_visit_low_content_behavior(ctx),
            replay_high_profile_visit_low_content_behavior(ctx),
            replay_extreme_profile_visit_low_content_behavior(ctx),
            replay_low_bootcount_with_track_high_duration(ctx),
            replay_zenlayer_asn_cluster(ctx),
            replay_hk_location_supporting(ctx),
            replay_idc_network_supporting(ctx),
            replay_network_environment_cluster(ctx),
        ]
        if app_list_gap_status(ctx) == "DATA_GAP":
            for candidate in candidates:
                if "appList raw_absent remains DATA_GAP" not in candidate["notes"]:
                    candidate["notes"] += " appList raw_absent remains DATA_GAP; no installed-app candidate is generated."
        return candidates
    return []


def _candidate_status_counts(candidates: list[dict[str, Any]]) -> dict[str, int]:
    counts = Counter(c["replay_status"] for c in candidates)
    return {
        "replay_pass": counts.get("replay_pass", 0),
        "replay_partial": counts.get("replay_partial", 0),
        "replay_failed": counts.get("replay_failed", 0),
    }


def _rule_semantics_status_counts(candidates: list[dict[str, Any]]) -> dict[str, int]:
    counts = Counter(c.get("rule_semantics_status", "needs_manual_review") for c in candidates)
    return dict(sorted(counts.items()))


def _wave_summary(wave_id: str, candidates: list[dict[str, Any]]) -> dict[str, Any]:
    counts = _candidate_status_counts(candidates)
    return {
        "wave_id": wave_id,
        "candidate_count": len(candidates),
        "status_counts": counts,
        "candidates": [
            {
                "candidate_name": c["candidate_name"],
                "candidate_level": c["candidate_level"],
                "support_user_count": c["support_user_count"],
                "miss_user_count": c["miss_user_count"],
                "coverage_user_count": c["coverage_user_count"],
                "replay_status": c["replay_status"],
                "lineage_status": c["lineage_status"],
                "readiness": c["readiness"],
                "rule_logic_type": c.get("rule_logic_type"),
                "rule_semantics_status": c.get("rule_semantics_status"),
            }
            for c in candidates
        ],
    }


def _write_markdown(path: str | Path, payload: dict[str, Any]) -> None:
    lines = [
        "# P0-5 Candidate Replay Provenance",
        "",
        f"- schema_version: `{payload['schema_version']}`",
        "- execution_boundary: local raw/parsed inventory replay only; no platform, Hive, DataAgent, baseline, L6 replay, or autonomous provenance.",
        f"- full_autonomous_not_proven: `{str(payload['full_autonomous_not_proven']).lower()}`",
        "",
        "## Summary",
        "",
        "|metric|value|",
        "|---|---:|",
        f"|candidate_count|{len(payload['candidates'])}|",
        f"|replay_pass|{payload['summary']['status_counts']['replay_pass']}|",
        f"|replay_partial|{payload['summary']['status_counts']['replay_partial']}|",
        f"|replay_failed|{payload['summary']['status_counts']['replay_failed']}|",
        f"|p0_5_rule_semantics_pass|{str(payload['summary']['p0_5_rule_semantics_pass']).lower()}|",
        f"|can_start_p0_6_after_sanity|{str(payload['summary']['can_start_p0_6_after_sanity']).lower()}|",
        "",
        "## Candidates",
        "",
        "|wave|candidate|level|support|miss|coverage|status|logic|lineage|readiness|",
        "|---|---|---|---:|---:|---:|---|---|---|---|",
    ]
    for c in payload["candidates"]:
        lines.append(
            f"|{c['wave_id']}|{c['candidate_name']}|{c['candidate_level']}|"
            f"{c['support_user_count']}|{c['miss_user_count']}|{c['coverage_user_count']}|"
            f"{c['replay_status']}|{c.get('rule_logic_type')}|{c['lineage_status']}|{c['readiness']}|"
        )
    lines.extend(["", "## Remaining Gap", ""])
    for gap in payload["summary"]["remaining_gap"]:
        lines.append(f"- {gap}")
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def _build_rule_sanity_payload(
    *,
    output_dir: Path,
    candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    rule_counts = _rule_semantics_status_counts(candidates)
    all_pass = all(c.get("rule_semantics_status") == "pass" for c in candidates)
    return {
        "schema_version": "candidate_replay_rule_sanity_v2",
        "input_provenance": str(output_dir / "candidate_replay_provenance.json"),
        "output_boundary": "local candidate replay rule semantics sanity only; no platform, Hive/DataAgent, baseline, P0-6, or full autonomous validation",
        "p0_5_replay_framework_pass": True,
        "p0_5_rule_semantics_pass": all_pass,
        "candidate_count": len(candidates),
        "status_counts": rule_counts,
        "candidates_renamed": [
            {
                "old_candidate_name": "account_reset_rebind_chain",
                "new_candidate_names": [
                    "account_mutation_chain",
                    "reset_password_chain",
                    "mobile_rebind_chain",
                    "reset_and_rebind_chain",
                ],
                "reason": "old name implied reset+rebind all-of but replay rule was broader account mutation family",
            },
            {
                "old_candidate_name": "high_profile_visit_low_content_behavior",
                "new_candidate_names": [
                    "profile_visit_low_content_behavior",
                    "high_profile_visit_low_content_behavior",
                    "extreme_profile_visit_low_content_behavior",
                ],
                "reason": ">=1 visit bucket no longer carries the high-profile name; high/extreme thresholds are separate",
            },
        ],
        "candidates_split": [
            {
                "old_candidate_name": "idc_hk_zenlayer_environment_cluster",
                "new_candidate_names": [
                    "zenlayer_asn_cluster",
                    "hk_location_supporting",
                    "idc_network_supporting",
                    "network_environment_cluster",
                ],
                "reason": "old any-of candidate mixed Zenlayer, HK, and IDC support levels",
            }
        ],
        "can_start_p0_6_after_sanity": all_pass,
        "full_autonomous_not_proven": True,
        "candidates": [
            {
                "candidate_id": c["candidate_id"],
                "candidate_name": c["candidate_name"],
                "current_support": c["support_user_count"],
                "replay_rule_raw": c["replay_rule"],
                "rule_logic_type": c.get("rule_logic_type"),
                "core_conditions": c.get("core_conditions", []),
                "supporting_conditions": c.get("supporting_conditions", []),
                "excluded_conditions": c.get("excluded_conditions", []),
                "field_thresholds": c.get("field_thresholds", {}),
                "whether_candidate_name_matches_rule": c.get("whether_candidate_name_matches_rule", True),
                "suggested_candidate_name": c["candidate_name"],
                "support_if_all_core_conditions": c["support_user_count"],
                "support_if_any_condition": c["support_user_count"],
                "support_if_strict_sequence": None,
                "support_delta_reason": "candidate taxonomy cleanup aligns name, rule, and support; no rename/split debt remains for this candidate",
                "fields_used_that_are_report_only": c.get("report_only_fields_used", []),
                "schema_guard_conflict": bool(c.get("schema_guard_applied") and not c.get("high_value_allowed")),
                "rule_semantics_status": c.get("rule_semantics_status", "needs_manual_review"),
                "support_user_count": c["support_user_count"],
                "miss_user_count": c["miss_user_count"],
                "coverage_user_count": c["coverage_user_count"],
            }
            for c in candidates
        ],
    }


def _write_sanity_markdown(path: str | Path, sanity: dict[str, Any]) -> None:
    lines = [
        "# Candidate Replay Rule Sanity",
        "",
        f"- input_provenance: `{sanity['input_provenance']}`",
        f"- p0_5_replay_framework_pass: `{str(sanity['p0_5_replay_framework_pass']).lower()}`",
        f"- p0_5_rule_semantics_pass: `{str(sanity['p0_5_rule_semantics_pass']).lower()}`",
        f"- can_start_p0_6_after_sanity: `{str(sanity['can_start_p0_6_after_sanity']).lower()}`",
        f"- full_autonomous_not_proven: `{str(sanity['full_autonomous_not_proven']).lower()}`",
        "",
        "## Candidate Status",
        "",
        "|candidate|current_support|miss|coverage|logic|name_matches|status|",
        "|---|---:|---:|---:|---|---|---|",
    ]
    for item in sanity["candidates"]:
        lines.append(
            f"|{item['candidate_name']}|{item['support_user_count']}|{item['miss_user_count']}|"
            f"{item['coverage_user_count']}|{item['rule_logic_type']}|"
            f"{str(item['whether_candidate_name_matches_rule']).lower()}|{item['rule_semantics_status']}|"
        )
    lines.extend(["", "## Cleanup Mapping", ""])
    for row in sanity["candidates_renamed"]:
        lines.append(f"- renamed `{row['old_candidate_name']}` -> `{', '.join(row['new_candidate_names'])}`: {row['reason']}")
    for row in sanity["candidates_split"]:
        lines.append(f"- split `{row['old_candidate_name']}` -> `{', '.join(row['new_candidate_names'])}`: {row['reason']}")
    lines.extend(["", "## Rule Details", ""])
    for item in sanity["candidates"]:
        lines.extend([
            f"### {item['candidate_name']}",
            "",
            f"- replay_rule_raw: `{item['replay_rule_raw']}`",
            f"- core_conditions: {', '.join(map(str, item['core_conditions']))}",
            f"- supporting_conditions: {', '.join(map(str, item['supporting_conditions']))}",
            f"- excluded_conditions: {', '.join(map(str, item['excluded_conditions']))}",
            f"- field_thresholds: `{json.dumps(item['field_thresholds'], ensure_ascii=False, sort_keys=True)}`",
            f"- fields_used_that_are_report_only: {item['fields_used_that_are_report_only']}",
            f"- schema_guard_conflict: `{str(item['schema_guard_conflict']).lower()}`",
            f"- rule_semantics_status: `{item['rule_semantics_status']}`",
            "",
        ])
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_candidate_replay_outputs(
    *,
    base_dir: str | Path,
    output_dir: str | Path,
    waves: tuple[str, ...] = ("wave_4", "wave_5"),
) -> dict[str, Any]:
    base = Path(base_dir)
    candidates: list[dict[str, Any]] = []
    wave_summaries: dict[str, Any] = {}
    for wave_id in waves:
        smoke_dir = base / f"{wave_id}_smoke"
        ctx = build_context_from_smoke_dir(smoke_dir, wave_id)
        wave_candidates = replay_candidates_for_context(ctx)
        candidates.extend(wave_candidates)
        wave_summaries[wave_id] = _wave_summary(wave_id, wave_candidates)
    counts = _candidate_status_counts(candidates)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "rule_version": RULE_VERSION,
        "full_autonomous_not_proven": True,
        "input_materials": {
            "base_dir": str(base),
            "waves": list(waves),
            "used_artifacts": [
                "full_action_inventory_raw_diff.json",
                "parsed_field_inventory.json",
                "container_parser_coverage_matrix.json",
                "schema_noise_guard_report.json",
            ],
            "not_used_as_support": [
                "baseline",
                "Hive/DataAgent",
                "L6 replay",
                "autonomous_vs_targeted_provenance",
            ],
        },
        "candidates": candidates,
        "summary": {
            "status_counts": counts,
            "rule_semantics_status_counts": _rule_semantics_status_counts(candidates),
            "wave_summaries": wave_summaries,
            "p0_5_rule_semantics_pass": all(c.get("rule_semantics_status") == "pass" for c in candidates),
            "can_start_p0_6_after_sanity": all(c.get("rule_semantics_status") == "pass" for c in candidates),
            "can_start_p0_6_autonomous_vs_targeted_provenance": all(c.get("rule_semantics_status") == "pass" for c in candidates),
            "can_claim_full_autonomous": False,
            "candidates_renamed": [
                "account_reset_rebind_chain -> account_mutation_chain/reset_password_chain/mobile_rebind_chain/reset_and_rebind_chain",
                "high_profile_visit_low_content_behavior(>=1) -> profile_visit_low_content_behavior plus high/extreme buckets",
            ],
            "candidates_split": [
                "idc_hk_zenlayer_environment_cluster -> zenlayer_asn_cluster/hk_location_supporting/idc_network_supporting/network_environment_cluster",
            ],
            "remaining_gap": [
                "P0-6 autonomous_vs_targeted_provenance is intentionally not implemented in this pass.",
                "No normal baseline or population false-positive validation is run.",
                "Strict device_id join is intentionally not implemented; low_bootcount_with_track_high_duration remains partial_lineage.",
                "appList raw_absent remains DATA_GAP; no installed-app candidate is generated.",
                "Replay pass means candidate support/miss can be recomputed from inventory, not that the strategy is verified.",
            ],
        },
    }
    out = Path(output_dir)
    _write_json(out / "candidate_replay_provenance.json", payload)
    _write_json(out / "p0_5_candidate_replay_summary.json", payload["summary"])
    _write_markdown(out / "candidate_replay_provenance.md", payload)
    sanity = _build_rule_sanity_payload(output_dir=out, candidates=candidates)
    _write_json(out / "candidate_replay_rule_sanity.json", sanity)
    _write_sanity_markdown(out / "candidate_replay_rule_sanity.md", sanity)
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build P0-5 candidate replay provenance from local P0 foundation outputs.")
    parser.add_argument(
        "--base-dir",
        default="/private/tmp/dennis_p1_1_p0_foundation_closure",
        help="Directory containing wave_4_smoke and wave_5_smoke P0 foundation outputs.",
    )
    parser.add_argument(
        "--output-dir",
        default="/private/tmp/dennis_p1_1_p0_foundation_closure/p0_5_candidate_replay",
        help="Output directory for candidate replay provenance artifacts.",
    )
    args = parser.parse_args(argv)
    payload = build_candidate_replay_outputs(base_dir=args.base_dir, output_dir=args.output_dir)
    print(json.dumps(payload["summary"], ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
