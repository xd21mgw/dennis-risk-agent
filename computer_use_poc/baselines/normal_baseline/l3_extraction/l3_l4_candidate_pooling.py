#!/usr/bin/env python3
"""Pool L3 raw candidates into retained/watchlist sets and trim L4 review output."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from l3_extraction.candidate_protocol import apply_candidate_protocol, candidate_baseline_mode


DEFAULT_FOCUS_TERMS = {
    "oneRiskLaunchLess10",
    "oneRiskOneDayReset",
    "developer",
    "noLockScreen",
    "startShort",
    "acCharger",
    "lockScreenLong",
    "changeMachine_rule",
    "oneRiskNoSim",
    "oneRiskBatteryZero",
    "oneRiskAutoScript",
    "oneRiskClickPlugin",
    "accessibilitySvc",
    "accessibilityServiceList",
    "enabledAccessibilityServiceList",
    "sensorList.xiaomi",
    "sensorList.qualcomm",
    "cpuInfo.arch",
    "oneIpInfo.asn",
    "xm1",
    "xm3",
    "did",
    "device_id",
    "deviceId",
    "action_type",
    "serviceKess",
}

REVIEW_DECISIONS_ALWAYS = {
    "strong_single_candidate",
    "semantic_unknown_but_strong_statistical_candidate",
}

L5_ALLOWED_DECISIONS = {
    "strong_single_candidate",
    "semantic_unknown_but_strong_statistical_candidate",
    "weak_single_candidate",
    "normal_unobserved_need_baseline",
}

DISCOVERY_L5_GLOBAL_TOPK = 120
DISCOVERY_L5_PER_SOURCE_TOPK = 40
DISCOVERY_L5_PER_COMMONALITY_FAMILY_TOPK = 80
DISCOVERY_L5_PER_SOURCE_FIELD_FAMILY_TOPK = 16
DISCOVERY_L5_MIN_SUPPORT = 2

DEVICE_FACT_REVIEW_PATH_FRAGMENTS = (
    ".accessibilityServiceList",
    ".enabledAccessibilityServiceList",
    ".sensorList.",
    ".cpuInfo.",
    ".oneIpInfo.",
    ".vendorSecHw.",
    ".vendorIds.",
    ".cpuKernel.",
)

SOURCE_CONTEXT_REVIEW_EXCLUDED_SOURCES = {
    "rcp_fast_query_hbase",
    "rcp_event_detail",
}


def load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: str | Path, value: Any) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _candidate_text(candidate: dict[str, Any]) -> str:
    return " ".join(
        str(candidate.get(key) or "")
        for key in ("candidate_id", "source_name", "action_or_layer", "field_path", "field_value_or_pattern")
    )


def is_focus_candidate(candidate: dict[str, Any], focus_terms: Iterable[str] = DEFAULT_FOCUS_TERMS) -> bool:
    text = _candidate_text(candidate).lower()
    for term in focus_terms:
        term_l = term.lower()
        if "." in term_l:
            if all(part in text for part in term_l.split(".")):
                return True
        elif term_l in text:
            return True
    return False


def is_retained_candidate(candidate: dict[str, Any]) -> tuple[bool, str]:
    grain = str(candidate.get("candidate_grain") or "")
    if grain == "high_cardinality_anchor":
        return True, "high_cardinality_anchor_audit"
    try:
        hit_count = int(candidate.get("risk_hit_count") or 0)
    except (TypeError, ValueError):
        hit_count = 0
    try:
        hit_rate = float(candidate.get("risk_hit_rate") or 0.0)
    except (TypeError, ValueError):
        hit_rate = 0.0
    if hit_count >= 2:
        return True, "risk_hit_count>=2"
    if hit_rate >= 0.3:
        return True, "risk_hit_rate>=0.3"
    return False, "risk_commonality_below_threshold"


def _watchlist_reason(candidate: dict[str, Any]) -> str:
    if is_focus_candidate(candidate):
        return "user_focus_field_below_retained_threshold"
    if str(candidate.get("candidate_grain") or "") == "unsupported_complex_value":
        return "parser_needed"
    return ""


def ensure_unique_candidate_ids(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: Counter[str] = Counter()
    output: list[dict[str, Any]] = []
    for candidate in candidates:
        item = dict(candidate)
        original = str(item.get("candidate_id") or "candidate")
        seen[original] += 1
        item["original_candidate_id"] = item.get("original_candidate_id") or original
        if seen[original] > 1:
            item["candidate_id"] = f"{original}__dup{seen[original]:04d}"
        output.append(item)
    return output


def pool_l3_candidates(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    raw = ensure_unique_candidate_ids([dict(c) for c in candidates])
    retained: list[dict[str, Any]] = []
    watchlist: list[dict[str, Any]] = []
    dropped_count = 0
    retained_rules: Counter[str] = Counter()
    watchlist_rules: Counter[str] = Counter()

    for candidate in raw:
        keep, reason = is_retained_candidate(candidate)
        item = dict(candidate)
        if keep:
            item["pool"] = "retained"
            item["pool_decision"] = "retained_for_l4"
            item["pool_reason"] = reason
            retained.append(item)
            retained_rules[reason] += 1
            continue
        watch_reason = _watchlist_reason(item)
        if watch_reason:
            item["pool"] = "watchlist"
            item["pool_decision"] = "watchlist_not_l4_input"
            item["pool_reason"] = watch_reason
            watchlist.append(item)
            watchlist_rules[watch_reason] += 1
        else:
            dropped_count += 1

    return {
        "raw": raw,
        "retained": retained,
        "watchlist": watchlist,
        "dropped_count": dropped_count,
        "retained_rules": dict(retained_rules),
        "watchlist_rules": dict(watchlist_rules),
    }


def _counter_rows(counter: Counter[Any], key_name: str) -> list[dict[str, Any]]:
    return [{key_name: key, "count": count} for key, count in counter.most_common()]


def build_l3_filter_summary(pool: dict[str, Any]) -> str:
    raw = pool["raw"]
    retained = pool["retained"]
    watchlist = pool["watchlist"]
    lines = [
        "# L3 Candidate Filter Summary",
        "",
        f"- raw_candidate_count: {len(raw)}",
        f"- retained_candidate_count: {len(retained)}",
        f"- watchlist_candidate_count: {len(watchlist)}",
        f"- dropped_candidate_count: {pool['dropped_count']}",
        "",
        "## Rules",
        "",
        "- retained: `risk_hit_count >= 2` or `risk_hit_rate >= 0.3` or `candidate_grain=high_cardinality_anchor`",
        "- watchlist: below threshold but user-focus field or parser-needed field",
        "- dropped: below threshold and not watchlist-worthy",
        "- L3 does not use normal baseline and does not make L4 decisions.",
        "",
    ]
    sections = [
        ("Risk Hit Count Distribution", _counter_rows(Counter(c.get("risk_hit_count") for c in raw), "risk_hit_count")),
        ("Candidate Grain Distribution", _counter_rows(Counter(c.get("candidate_grain") for c in raw), "candidate_grain")),
        ("Source Distribution", _counter_rows(Counter(c.get("source_name") for c in raw), "source")),
        ("Action/Layer Distribution", _counter_rows(Counter(c.get("action_or_layer") for c in raw), "action_or_layer")),
        ("Retained Rule Hits", [{"rule": k, "count": v} for k, v in pool["retained_rules"].items()]),
        ("Watchlist Rule Hits", [{"rule": k, "count": v} for k, v in pool["watchlist_rules"].items()]),
    ]
    for title, rows in sections:
        lines.extend(["", f"## {title}", "", _markdown_table(rows)])
    return "\n".join(lines) + "\n"


def _markdown_table(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "None."
    headers = list(rows[0].keys())
    output = ["|" + "|".join(headers) + "|", "|" + "|".join(["---"] * len(headers)) + "|"]
    for row in rows:
        output.append("|" + "|".join(str(row.get(header, "")).replace("|", "\\|") for header in headers) + "|")
    return "\n".join(output)


def _field_family(path: str) -> str:
    parts = str(path or "").split(".")
    return ".".join(parts[:3]) if len(parts) >= 3 else str(path or "")


def _source_key(item: dict[str, Any]) -> str:
    return str(item.get("source_name") or item.get("source_action") or "unknown")


def _commonality_family_key(item: dict[str, Any]) -> str:
    return str(item.get("commonality_family") or "unknown")


def _discovery_rank_key(item: dict[str, Any]) -> tuple[float, int, int, int, str]:
    try:
        hit_rate = float(item.get("risk_hit_rate") or 0.0)
    except (TypeError, ValueError):
        hit_rate = 0.0
    try:
        hit_count = int(item.get("risk_hit_count") or 0)
    except (TypeError, ValueError):
        hit_count = 0
    feature_type = str(item.get("feature_type") or "")
    grain = str(item.get("candidate_grain") or "")
    feature_priority = {
        "raw_field": 3,
        "numeric_bucket": 2,
        "derived_feature": 1,
    }.get(feature_type, 0)
    grain_priority = {
        "label_value": 5,
        "enum_value": 4,
        "scalar_value": 3,
        "object_child_value": 3,
        "array_element": 2,
        "value_pattern": 1,
    }.get(grain, 0)
    return (hit_rate, hit_count, feature_priority, grain_priority, str(item.get("candidate_id") or ""))


def bound_discovery_l5_candidates(candidates: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], Counter[str]]:
    """Keep discovery_only as a bounded L5 supplement, not an unbounded input pool."""
    reasons: Counter[str] = Counter()
    selected: list[dict[str, Any]] = []
    source_counts: Counter[str] = Counter()
    commonality_counts: Counter[str] = Counter()
    source_family_counts: Counter[tuple[str, str]] = Counter()

    for item in sorted(candidates, key=_discovery_rank_key, reverse=True):
        source = _source_key(item)
        commonality = _commonality_family_key(item)
        family = _field_family(str(item.get("field_path") or ""))
        source_family = (source, family)
        if len(selected) >= DISCOVERY_L5_GLOBAL_TOPK:
            reasons["discovery_filtered_global_topk"] += 1
            continue
        if source_counts[source] >= DISCOVERY_L5_PER_SOURCE_TOPK:
            reasons["discovery_filtered_per_source_topk"] += 1
            continue
        if commonality_counts[commonality] >= DISCOVERY_L5_PER_COMMONALITY_FAMILY_TOPK:
            reasons["discovery_filtered_per_commonality_family_topk"] += 1
            continue
        if source_family_counts[source_family] >= DISCOVERY_L5_PER_SOURCE_FIELD_FAMILY_TOPK:
            reasons["discovery_filtered_duplicate_same_source_field_family"] += 1
            continue
        kept = dict(item)
        kept["l5_input_reason"] = "bounded_discovery_selected_for_l5"
        selected.append(kept)
        source_counts[source] += 1
        commonality_counts[commonality] += 1
        source_family_counts[source_family] += 1

    return selected, reasons


def _l3_by_candidate_id(candidates: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(c.get("candidate_id")): c for c in candidates}


def _review_reason(card: dict[str, Any], candidate: dict[str, Any]) -> str:
    decision = str(card.get("l4_decision") or "")
    if decision in REVIEW_DECISIONS_ALWAYS:
        return decision
    if decision == "weak_single_candidate":
        return "weak_with_risk_commonality"
    if decision == "normal_unobserved_need_baseline":
        return "unobserved_but_high_risk_commonality_or_focus_field"
    return ""


def is_l4_review_candidate(card: dict[str, Any], candidate: dict[str, Any]) -> tuple[bool, str]:
    if card.get("normal_value_lookup_status") == "normal_value_distribution_incomplete":
        return False, "normal_value_distribution_incomplete_for_low_cardinality_field"
    if str(card.get("source_name") or candidate.get("source_name") or "") in SOURCE_CONTEXT_REVIEW_EXCLUDED_SOURCES:
        return False, "source_context_field_not_review_candidate"
    decision = str(card.get("l4_decision") or "")
    if decision in REVIEW_DECISIONS_ALWAYS:
        return True, _review_reason(card, candidate)
    if decision == "weak_single_candidate":
        if int(card.get("risk_hit_count") or 0) >= 3 or float(card.get("risk_hit_rate") or 0.0) >= 0.5:
            return True, _review_reason(card, candidate)
    if decision == "normal_unobserved_need_baseline":
        field_path = str(card.get("field_name") or candidate.get("field_path") or "")
        is_reviewable_device_fact = (
            str(card.get("source_name") or candidate.get("source_name") or "") == "weapon_android"
            and any(fragment in field_path for fragment in DEVICE_FACT_REVIEW_PATH_FRAGMENTS)
        )
        if is_focus_candidate(candidate) or (
            is_reviewable_device_fact
            and (int(card.get("risk_hit_count") or 0) >= 5 or float(card.get("risk_hit_rate") or 0.0) >= 0.8)
        ):
            return True, _review_reason(card, candidate)
    return False, "not_review_main_output"


def _valid_metric(value: Any) -> bool:
    return value not in (None, "")


def _looks_too_coarse(value: Any) -> bool:
    text = str(value or "").strip().lower()
    return text in {"", "*", "none", "null", "unknown", "need_pattern_extractor:list_of_objects"}


def l5_input_decision(card: dict[str, Any], candidate: dict[str, Any], pool_item: dict[str, Any]) -> tuple[bool, str]:
    if pool_item.get("l5_usage") == "audit_only":
        return False, pool_item.get("l5_exclusion_reason") or "audit_only"
    if str(card.get("l4_decision") or "") not in L5_ALLOWED_DECISIONS:
        return False, f"l4_decision_not_l5_allowed:{card.get('l4_decision')}"
    if card.get("leakage_risk") not in (None, "", "none", "low"):
        return False, "label_or_post_action_leakage"
    if card.get("identifier_risk") not in (None, "", "none", "low"):
        return False, "identifier_or_unique_anchor"
    if str(candidate.get("candidate_grain") or "") == "high_cardinality_anchor":
        return False, "identifier_or_unique_anchor"
    if _looks_too_coarse(card.get("field_value_or_pattern") or candidate.get("field_value_or_pattern")):
        return False, "bad_granularity_too_coarse"
    for key in ("risk_hit_count", "risk_denominator", "risk_hit_rate"):
        if not _valid_metric(pool_item.get(key)):
            return False, f"missing_{key}"
    try:
        if int(pool_item.get("risk_hit_count") or 0) < DISCOVERY_L5_MIN_SUPPORT:
            return False, "insufficient_support"
    except (TypeError, ValueError):
        return False, "insufficient_support"
    if pool_item.get("baseline_mode") == "discovery_only":
        if pool_item.get("normal_hit_rate") is not None or pool_item.get("lift") is not None:
            return False, "discovery_only_normal_metrics_must_be_null"
        if pool_item.get("requires_l6_replay") is not True:
            return False, "missing_requires_l6_replay"
    if pool_item.get("feature_type") == "derived_feature":
        if pool_item.get("feature_definition_status") != "present" or not pool_item.get("feature_definition"):
            return False, "derived_feature_missing_feature_definition"
        if not (pool_item.get("source_fields") or pool_item.get("source_events")):
            return False, "derived_feature_missing_traceable_source"
        if not pool_item.get("commonality_evidence"):
            return False, "derived_feature_missing_commonality_evidence"
    return True, "l5_input_candidate"


def build_l4_review_outputs(cards: list[dict[str, Any]], retained_candidates: list[dict[str, Any]]) -> dict[str, Any]:
    l3_by_id = _l3_by_candidate_id(retained_candidates)
    review: list[dict[str, Any]] = []
    baseline_supported: list[dict[str, Any]] = []
    discovery_only: list[dict[str, Any]] = []
    baseline_l5_input: list[dict[str, Any]] = []
    discovery_l5_eligible: list[dict[str, Any]] = []
    l5_filter_reasons: Counter[str] = Counter()
    for card in cards:
        candidate = l3_by_id.get(str(card.get("candidate_id")), {})
        candidate = apply_candidate_protocol(candidate)
        mode = _l4_baseline_mode(card, candidate)
        candidate["baseline_mode"] = mode
        pool_item = _validated_candidate_card(card, candidate, mode)
        if mode == "baseline_supported":
            baseline_supported.append(pool_item)
        else:
            discovery_only.append(pool_item)
        l5_keep, l5_reason = l5_input_decision(card, candidate, pool_item)
        if l5_keep:
            item = dict(pool_item)
            item["l5_input_reason"] = "baseline_supported_selected_for_l5" if mode == "baseline_supported" else l5_reason
            if mode == "baseline_supported":
                baseline_l5_input.append(item)
            else:
                discovery_l5_eligible.append(item)
        else:
            l5_filter_reasons[l5_reason] += 1
        keep, reason = is_l4_review_candidate(card, candidate)
        if not keep:
            continue
        review.append({
            "candidate_id": card.get("candidate_id"),
            "source_name": card.get("source_name"),
            "action_or_layer": candidate.get("action_or_layer"),
            "field_path": card.get("field_name"),
            "field_value_or_pattern": card.get("field_value_or_pattern"),
            "candidate_grain": candidate.get("candidate_grain"),
            "risk_hit_sample_ids": candidate.get("risk_hit_sample_ids") or candidate.get("supporting_user_ids") or [],
            "supporting_user_ids": candidate.get("supporting_user_ids") or [],
            "supporting_device_ids": candidate.get("supporting_device_ids") or [],
            "support_count": card.get("risk_hit_count"),
            "risk_observed_count": card.get("risk_observed_count"),
            "risk_hit_count": card.get("risk_hit_count"),
            "risk_hit_rate": card.get("risk_hit_rate"),
            "normal_field_coverage_ratio": card.get("normal_field_coverage_ratio"),
            "normal_value_lookup_status": card.get("normal_value_lookup_status"),
            "normal_value_distribution_reliable": card.get("normal_value_distribution_reliable"),
            "normal_value_lookup_note": card.get("normal_value_lookup_note"),
            "normalized_value_key": card.get("normalized_value_key"),
            "normal_hit_rate": card.get("normal_hit_rate") if mode == "baseline_supported" else None,
            "statistical_strength": card.get("statistical_strength"),
            "semantic_clarity": card.get("semantic_clarity"),
            "field_role": candidate.get("field_role_hint"),
            "leakage_risk": card.get("leakage_risk"),
            "identifier_risk": card.get("identifier_risk"),
            "l4_decision": card.get("l4_decision"),
            "recommended_next_action": card.get("recommended_next_action"),
            "review_reason": reason,
            "feature_type": candidate.get("feature_type"),
            "value_type": candidate.get("value_type"),
            "feature_name": candidate.get("feature_name"),
            "source_fields": candidate.get("source_fields"),
            "source_events": candidate.get("source_events"),
            "feature_definition": candidate.get("feature_definition"),
            "feature_definition_status": candidate.get("feature_definition_status"),
            "commonality_family": candidate.get("commonality_family"),
            "commonality_evidence": candidate.get("commonality_evidence"),
            "bucket_label": candidate.get("bucket_label"),
            "bucket_range": candidate.get("bucket_range"),
            "candidate_value": candidate.get("candidate_value"),
            "risk_denominator": candidate.get("risk_denominator"),
            "baseline_mode": mode,
            "lift": _safe_lift(card.get("risk_hit_rate"), card.get("normal_hit_rate")) if mode == "baseline_supported" else None,
            "l5_usage": _l5_usage_for_candidate(candidate, mode),
            "l5_exclusion_reason": candidate.get("l5_exclusion_reason"),
            "requires_l6_replay": True,
            "l6_replay_required_reason": "impact_and_false_positive_validation_required",
            "eval_required_fields": candidate.get("eval_required_fields") or [],
        })
    bounded_discovery_l5_input, discovery_bound_reasons = bound_discovery_l5_candidates(discovery_l5_eligible)
    l5_filter_reasons.update(discovery_bound_reasons)
    l5_input = baseline_l5_input + bounded_discovery_l5_input

    return {
        "l4_review_candidates": review,
        "baseline_supported_candidates": baseline_supported,
        "discovery_only_candidates": discovery_only,
        "l5_input_candidates": l5_input,
        "l5_input_summary": {
            "l5_input_candidate_count": len(l5_input),
            "baseline_supported_l5_input_count": len(baseline_l5_input),
            "discovery_only_l5_eligible_before_bound_count": len(discovery_l5_eligible),
            "discovery_only_l5_input_count": len(bounded_discovery_l5_input),
            "formal_strategy_draft_count": sum(1 for item in l5_input if item.get("l5_usage") == "formal_strategy_draft"),
            "experimental_strategy_draft_count": sum(1 for item in l5_input if item.get("l5_usage") == "experimental_strategy_draft"),
            "discovery_l5_bounds": {
                "global_topk": DISCOVERY_L5_GLOBAL_TOPK,
                "per_source_topk": DISCOVERY_L5_PER_SOURCE_TOPK,
                "per_commonality_family_topk": DISCOVERY_L5_PER_COMMONALITY_FAMILY_TOPK,
                "per_source_field_family_topk": DISCOVERY_L5_PER_SOURCE_FIELD_FAMILY_TOPK,
                "min_support": DISCOVERY_L5_MIN_SUPPORT,
            },
            "filtered_reason_distribution": dict(l5_filter_reasons),
        },
        "l4_review_summary": build_l4_review_summary(cards, retained_candidates, review),
    }


def _safe_lift(risk_hit_rate: Any, normal_hit_rate: Any) -> float | None:
    if risk_hit_rate is None or normal_hit_rate in (None, ""):
        return None
    try:
        normal = float(normal_hit_rate)
        if normal <= 0:
            return None
        return round(float(risk_hit_rate) / normal, 4)
    except (TypeError, ValueError):
        return None


def _l4_baseline_mode(card: dict[str, Any], candidate: dict[str, Any]) -> str:
    status = str(card.get("normal_value_lookup_status") or "")
    if candidate_baseline_mode(candidate) != "baseline_supported":
        return "discovery_only"
    if status in {
        "value_matched",
        "value_not_found_in_top",
        "field_matched_but_value_not_evaluated",
        "normal_value_distribution_incomplete",
        "high_cardinality_skipped",
    }:
        return "baseline_supported"
    return "discovery_only"


def _l5_usage_for_candidate(candidate: dict[str, Any], mode: str) -> str:
    if (
        candidate.get("feature_type") == "derived_feature"
        and candidate.get("feature_definition_status") == "missing"
    ):
        return "audit_only"
    return "formal_strategy_draft" if mode == "baseline_supported" else "experimental_strategy_draft"


def _validated_candidate_card(card: dict[str, Any], candidate: dict[str, Any], mode: str) -> dict[str, Any]:
    risk_rate = card.get("risk_hit_rate")
    normal_hit_rate = card.get("normal_hit_rate") if mode == "baseline_supported" else None
    return {
        "candidate_id": card.get("candidate_id"),
        "source_name": card.get("source_name") or candidate.get("source_name"),
        "source_action": candidate.get("source_action") or candidate.get("action_or_layer"),
        "feature_type": candidate.get("feature_type"),
        "value_type": candidate.get("value_type"),
        "feature_name": candidate.get("feature_name") or card.get("field_name"),
        "source_fields": candidate.get("source_fields") or [card.get("field_name")],
        "source_events": candidate.get("source_events") or [],
        "feature_definition": candidate.get("feature_definition") or {},
        "feature_definition_status": candidate.get("feature_definition_status"),
        "commonality_family": candidate.get("commonality_family"),
        "commonality_evidence": candidate.get("commonality_evidence"),
        "bucket_label": candidate.get("bucket_label"),
        "bucket_range": candidate.get("bucket_range"),
        "candidate_value": candidate.get("candidate_value") or card.get("field_value_or_pattern"),
        "field_path": card.get("field_name"),
        "field_value_or_pattern": card.get("field_value_or_pattern"),
        "candidate_grain": candidate.get("candidate_grain"),
        "risk_hit_sample_ids": candidate.get("risk_hit_sample_ids") or candidate.get("supporting_user_ids") or [],
        "supporting_user_ids": candidate.get("supporting_user_ids") or [],
        "supporting_device_ids": candidate.get("supporting_device_ids") or [],
        "support_count": card.get("risk_hit_count"),
        "risk_observed_count": card.get("risk_observed_count"),
        "risk_hit_count": card.get("risk_hit_count"),
        "risk_denominator": card.get("risk_observed_count"),
        "risk_hit_rate": risk_rate,
        "baseline_mode": mode,
        "normal_hit_rate": normal_hit_rate,
        "lift": _safe_lift(risk_rate, normal_hit_rate) if mode == "baseline_supported" else None,
        "evidence_examples": candidate.get("evidence_examples") or [],
        "eval_required_fields": candidate.get("eval_required_fields") or [],
        "l5_usage": _l5_usage_for_candidate(candidate, mode),
        "l5_exclusion_reason": candidate.get("l5_exclusion_reason"),
        "requires_l6_replay": True,
        "l6_replay_required_reason": "impact_and_false_positive_validation_required",
        "l4_decision": card.get("l4_decision"),
        "normal_value_lookup_status": card.get("normal_value_lookup_status"),
        "normal_value_distribution_reliable": card.get("normal_value_distribution_reliable"),
        "leakage_risk": card.get("leakage_risk"),
        "identifier_risk": card.get("identifier_risk"),
    }


def build_l4_review_summary(cards: list[dict[str, Any]], retained_candidates: list[dict[str, Any]], review: list[dict[str, Any]]) -> dict[str, Any]:
    l3_by_id = _l3_by_candidate_id(retained_candidates)
    unobserved = [card for card in cards if card.get("baseline_lookup_status") == "unobserved_missing"]
    baseline_modes: Counter[str] = Counter()
    for card in cards:
        candidate = apply_candidate_protocol(l3_by_id.get(str(card.get("candidate_id")), {}))
        baseline_modes[_l4_baseline_mode(card, candidate)] += 1
    return {
        "l4_all_card_count": len(cards),
        "l4_review_candidate_count": len(review),
        "baseline_supported_candidate_count": baseline_modes.get("baseline_supported", 0),
        "discovery_only_candidate_count": baseline_modes.get("discovery_only", 0),
        "baseline_mode_distribution": dict(baseline_modes),
        "l4_decision_distribution": dict(Counter(card.get("l4_decision") for card in cards)),
        "source_distribution": dict(Counter(card.get("source_name") for card in cards)),
        "action_or_layer_distribution": dict(Counter(l3_by_id.get(str(card.get("candidate_id")), {}).get("action_or_layer") for card in cards)),
        "normal_value_lookup_status_distribution": dict(Counter(card.get("normal_value_lookup_status") for card in cards)),
        "normal_value_distribution_incomplete_summary": {
            "count": sum(1 for card in cards if card.get("normal_value_lookup_status") == "normal_value_distribution_incomplete"),
            "review_output_policy": "filtered_from_review_and_l5_input; retained_in_l4_all_cards",
            "top_field_families": dict(Counter(_field_family(card.get("field_name", "")) for card in cards if card.get("normal_value_lookup_status") == "normal_value_distribution_incomplete").most_common(20)),
        },
        "result_signal_summary": {
            "count": sum(1 for card in cards if card.get("l4_decision") == "result_signal_not_feature"),
            "review_output_policy": "summary_only_not_main_review",
        },
        "identifier_anchor_summary": {
            "count": sum(1 for card in cards if card.get("l4_decision") == "identifier_anchor_not_feature"),
            "review_output_policy": "summary_only_anchor_not_feature",
        },
        "reject_or_hold_summary": {
            "count": sum(1 for card in cards if card.get("l4_decision") == "reject_or_hold"),
            "top_field_families": dict(Counter(_field_family(card.get("field_name", "")) for card in cards if card.get("l4_decision") == "reject_or_hold").most_common(20)),
        },
        "normal_unobserved_summary": {
            "count": len(unobserved),
            "top_field_families": dict(Counter(_field_family(card.get("field_name", "")) for card in unobserved).most_common(20)),
        },
    }


def build_l4_review_markdown(review: list[dict[str, Any]], summary: dict[str, Any]) -> str:
    lines = [
        "# L4 Review Candidates",
        "",
        f"- l4_all_card_count: {summary['l4_all_card_count']}",
        f"- l4_review_candidate_count: {summary['l4_review_candidate_count']}",
        f"- l4_decision_distribution: `{summary['l4_decision_distribution']}`",
        "",
    ]
    grouped: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in review:
        grouped[str(item.get("l4_decision"))].append(item)
    for decision in sorted(grouped):
        rows = sorted(
            grouped[decision],
            key=lambda x: (float(x.get("risk_hit_rate") or 0), int(x.get("risk_hit_count") or 0)),
            reverse=True,
        )[:50]
        lines.extend(["", f"## {decision}", "", _markdown_table(rows)])
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Pool L3 candidates and build L4 review outputs")
    sub = parser.add_subparsers(dest="command", required=True)

    pool_cmd = sub.add_parser("pool-l3")
    pool_cmd.add_argument("--input", required=True)
    pool_cmd.add_argument("--raw-output", required=True)
    pool_cmd.add_argument("--retained-output", required=True)
    pool_cmd.add_argument("--watchlist-output", required=True)
    pool_cmd.add_argument("--summary-md", required=True)

    review_cmd = sub.add_parser("build-l4-review")
    review_cmd.add_argument("--l4-cards", required=True)
    review_cmd.add_argument("--retained-candidates", required=True)
    review_cmd.add_argument("--review-output", required=True)
    review_cmd.add_argument("--review-md", required=True)
    review_cmd.add_argument("--summary-md", required=True)

    args = parser.parse_args()
    if args.command == "pool-l3":
        candidates = load_json(args.input)
        pool = pool_l3_candidates(candidates)
        write_json(args.raw_output, pool["raw"])
        write_json(args.retained_output, pool["retained"])
        write_json(args.watchlist_output, pool["watchlist"])
        Path(args.summary_md).write_text(build_l3_filter_summary(pool), encoding="utf-8")
        print(f"raw={len(pool['raw'])} retained={len(pool['retained'])} watchlist={len(pool['watchlist'])} dropped={pool['dropped_count']}")
    elif args.command == "build-l4-review":
        cards_obj = load_json(args.l4_cards)
        cards = cards_obj.get("l4_candidate_validation_cards", cards_obj) if isinstance(cards_obj, dict) else cards_obj
        retained = load_json(args.retained_candidates)
        result = build_l4_review_outputs(cards, retained)
        write_json(args.review_output, result)
        Path(args.review_md).write_text(build_l4_review_markdown(result["l4_review_candidates"], result["l4_review_summary"]), encoding="utf-8")
        Path(args.summary_md).write_text(json.dumps(result["l4_review_summary"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"l4_all={len(cards)} review={len(result['l4_review_candidates'])}")


if __name__ == "__main__":
    main()
