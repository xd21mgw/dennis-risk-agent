#!/usr/bin/env python3
"""L5 value path candidate generator.

L5 consumes only L4 review candidates. It generates candidate_signal pair/path
tasks for L6 review. It does not access platforms, normal baseline, DataAgent,
Hive, or production policy systems.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path
from typing import Any


ALLOWED_L4_DECISIONS = {
    "strong_single_candidate",
    "semantic_unknown_but_strong_statistical_candidate",
    "weak_single_candidate",
    "normal_unobserved_need_baseline",
}
BLOCKED_L4_DECISIONS = {
    "reject_or_hold",
    "result_signal_not_feature",
    "identifier_anchor_not_feature",
}
EVIDENCE_BOUNDARY = "仅基于当前风险样本空间和 L4 review_candidates 的样本内 CNT / conversion 关系发现，未经过 Hive 大盘、偏白样本、历史召回、时序稳定性验证。"
PATTERN_EVIDENCE_BOUNDARY = EVIDENCE_BOUNDARY
PASS_DIRECTION_DECISIONS = {"pass_directional_relation", "pass_refinement_component_direction"}
BROAD_ANCHOR_FIELD_KEYS = {"brand", "os", "os_version", "province", "device_profile_context"}
CONTEXT_EVIDENCE_FIELD_KEYS = {"one_risk_label"}
HELD_ANCHOR_STATUSES = {"broad_anchor_hold", "need_finer_granularity", "context_only", "rejected_as_eval_anchor"}
L6_REPLAY_REQUIRED_REASON = "impact_and_false_positive_validation_required"
MAX_EXPERIMENTAL_TOTAL_FEATURE_COUNT = 3
DEFAULT_MAX_DISCOVERY_ONLY_COUNT = 2
HARD_MAX_DISCOVERY_ONLY_COUNT = 3
PURE_DISCOVERY_MAX_FEATURE_COUNT = 2


def load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: str | Path, value: Any) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_l4_review_candidates(path: str | Path) -> list[dict[str, Any]]:
    payload = load_json(path)
    if isinstance(payload, dict):
        if "l5_input_candidates" in payload:
            return payload.get("l5_input_candidates", [])
        return payload.get("l4_review_candidates", [])
    if isinstance(payload, list):
        return payload
    return []


def load_knowledge_base(path: str | Path | None = None) -> dict[str, Any]:
    if path is None:
        path = Path(__file__).with_name("l5_knowledge_base_v0_1.json")
    kb = load_json(path)
    for key in (
        "field_pair_prior_config",
        "natural_determination_map",
        "value_granularity_rules",
        "global_thresholds",
        "threshold_overrides",
        "top_k_selection",
        "llm_judgement_prompt_contract",
    ):
        kb.setdefault(key, [] if key.endswith("_config") or key.endswith("_map") else {})
    return kb


def canonical_value_key(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    low = text.lower()
    if low in {"false", "0.0"}:
        return "0"
    if low in {"true", "1.0"}:
        return "1"
    return low


def load_normal_baseline(baseline_dir: str | Path | None = None) -> dict[str, Any]:
    if baseline_dir is None:
        baseline_dir = Path("/tmp/normal_baseline_layered_v0_2")
    baseline_dir = Path(baseline_dir)
    out: dict[str, Any] = {
        "normal_baseline_status": "missing",
        "baseline_dir": str(baseline_dir),
        "fields": {},
    }
    dist_path = baseline_dir / "normal_discrete_field_distribution.json"
    if not dist_path.exists():
        return out
    try:
        rows = load_json(dist_path)
    except (OSError, json.JSONDecodeError):
        return out
    fields: dict[str, dict[str, Any]] = {}
    for row in rows if isinstance(rows, list) else []:
        field_path = row.get("field_path")
        if not field_path:
            continue
        top_values = row.get("top_values", []) or []
        value_rates = {canonical_value_key(v.get("value")): v for v in top_values}
        entropy = 0.0
        for item in top_values:
            ratio = float(item.get("ratio") or 0.0)
            if ratio > 0:
                entropy -= ratio * math.log2(ratio)
        other_ratio = float(row.get("other_value_ratio") or 0.0)
        if other_ratio > 0:
            entropy -= other_ratio * math.log2(other_ratio)
        distinct = int(row.get("distinct_value_count") or 0)
        max_entropy = math.log2(max(distinct, 2))
        normalized_entropy = entropy / max_entropy if max_entropy else None
        fields[field_path] = {
            "normal_field_non_null_count": row.get("covered_entity_count"),
            "normal_field_distinct_count": distinct,
            "normal_field_entropy": round(entropy, 6),
            "normal_field_entropy_normalized": round(normalized_entropy, 6) if normalized_entropy is not None else None,
            "coverage_ratio": row.get("coverage_ratio"),
            "value_rates": value_rates,
            "full_value_distribution_stored": row.get("full_value_distribution_stored", False),
        }
    out["normal_baseline_status"] = "available"
    out["fields"] = fields
    out["field_count"] = len(fields)
    return out


def normal_stats_for(field_path: str, value: Any, baseline: dict[str, Any] | None) -> dict[str, Any]:
    if not baseline or baseline.get("normal_baseline_status") != "available":
        return {
            "normal_baseline_status": "missing",
            "normal_field_non_null_count": None,
            "normal_field_distinct_count": None,
            "normal_field_entropy": None,
            "normal_value_count": None,
            "normal_value_rate": None,
        }
    fields = baseline.get("fields", {})
    profile = fields.get(field_path)
    if not profile:
        return {
            "normal_baseline_status": "field_missing",
            "normal_field_non_null_count": None,
            "normal_field_distinct_count": None,
            "normal_field_entropy": None,
            "normal_value_count": None,
            "normal_value_rate": None,
        }
    value_item = profile.get("value_rates", {}).get(canonical_value_key(value))
    return {
        "normal_baseline_status": "value_found" if value_item else "value_missing_from_top_values",
        "normal_field_non_null_count": profile.get("normal_field_non_null_count"),
        "normal_field_distinct_count": profile.get("normal_field_distinct_count"),
        "normal_field_entropy": profile.get("normal_field_entropy"),
        "normal_field_entropy_normalized": profile.get("normal_field_entropy_normalized"),
        "normal_value_count": value_item.get("count") if value_item else None,
        "normal_value_rate": value_item.get("ratio") if value_item else None,
        "normal_coverage_ratio": profile.get("coverage_ratio"),
    }


def load_prior_overlay(path: str | Path | None) -> dict[str, Any]:
    empty = {
        "field_family_map": [],
        "field_pair_prior_seed_library": [],
        "natural_relation_seed_library": [],
        "leakage_field_map": [],
        "over_general_field_map": [],
        "unique_id_field_map": [],
        "field_role_map": [],
    }
    if not path:
        return empty
    p = Path(path)
    if not p.exists():
        return empty
    payload = load_json(p)
    for key, default in empty.items():
        payload.setdefault(key, default)
    return payload


def load_field_prior_kb(path: str | Path | None = None) -> dict[str, Any]:
    if path is None:
        path = Path(__file__).with_name("l5_field_prior_kb.json")
    p = Path(path)
    if not p.exists():
        return {
            "field_family_map": [],
            "field_role_map": [],
            "field_pair_prior": [],
            "natural_relation_map": [],
            "leakage_field_map": [],
            "over_general_field_map": [],
            "unique_id_field_map": [],
        }
    payload = load_json(p)
    for key in (
        "field_family_map",
        "field_role_map",
        "field_pair_prior",
        "natural_relation_map",
        "leakage_field_map",
        "over_general_field_map",
        "unique_id_field_map",
    ):
        payload.setdefault(key, [])
    return payload


def load_value_relation_overlay(path: str | Path | None) -> dict[str, Any]:
    if not path:
        return {"value_relation_prior_overlay": []}
    p = Path(path)
    if not p.exists():
        return {"value_relation_prior_overlay": []}
    payload = load_json(p)
    payload.setdefault("value_relation_prior_overlay", [])
    return payload


def attach_prior_overlay(kb: dict[str, Any], overlay: dict[str, Any] | None, field_prior_kb: dict[str, Any] | None = None, value_relation_overlay: dict[str, Any] | None = None) -> dict[str, Any]:
    kb = dict(kb)
    kb["_prior_overlay"] = overlay or load_prior_overlay(None)
    kb["_field_prior_kb"] = field_prior_kb or load_field_prior_kb(None)
    kb["_value_relation_overlay"] = value_relation_overlay or load_value_relation_overlay(None)
    return kb


def field_key(field_path: str) -> str:
    """Normalize a field path to a rough semantic key for priors/thresholds."""
    path = str(field_path or "").lower()
    last = path.split(".")[-1]
    compact = path.replace("_", "").replace("-", "")
    if "ip24" in compact:
        return "ip24"
    if "oneipinfo" in compact and ("ip" in last or "asn" in last or "isp" in last):
        return last
    if "devicemodel" in compact or last in {"model", "phone_model", "phonemodel"}:
        return "device_model"
    if "deviceid" in compact or last in {"device_id", "did", "uuid", "token", "userid", "user_id"}:
        return last if last in {"device_id", "did", "uuid", "token"} else "device_id"
    if last in {"province", "city", "country", "os", "os_version"}:
        return last
    if last == "brand" or "brand" in compact:
        return "brand"
    if "manufacturer" in compact:
        return "manufacturer"
    if "osversion" in compact or last == "os_version":
        return "os_version"
    if "sdklevel" in compact or last == "sdk_level":
        return "sdk_level"
    if "cpuinfo.arch" in path or last in {"arch", "cpu_arch"}:
        return "cpu_arch"
    if last == "abi":
        return "abi"
    if "accessibility" in compact:
        return "accessibility_service"
    if "sensorlist" in compact:
        return "sensor"
    if "weapon_one_risk" in path:
        return "one_risk_label"
    return last


def validate_l4_candidate(candidate: dict[str, Any]) -> list[dict[str, Any]]:
    violations: list[dict[str, Any]] = []
    candidate_id = candidate.get("candidate_id")
    checks = [
        ("missing_candidate_id", bool(candidate_id)),
        ("missing_field_path", bool(candidate.get("field_path"))),
        ("missing_value_or_pattern", candidate.get("field_value_or_pattern") not in (None, "")),
    ]
    sample_ids = candidate.get("risk_hit_sample_ids")
    checks.append(("missing_risk_hit_sample_ids", isinstance(sample_ids, list) and len(sample_ids) > 0))
    support_count = candidate.get("support_count", candidate.get("risk_hit_count", 0))
    try:
        support_ok = int(support_count or 0) > 0
    except (TypeError, ValueError):
        support_ok = False
    checks.append(("invalid_support_count", support_ok))
    decision = candidate.get("l4_decision") or candidate.get("validation_status")
    checks.append(("l4_status_not_allowed", decision in ALLOWED_L4_DECISIONS))
    if decision in BLOCKED_L4_DECISIONS:
        checks.append(("l4_blocked_decision", False))
    if candidate.get("normal_value_distribution_reliable") is False and candidate.get("normal_value_lookup_status") == "normal_value_distribution_incomplete":
        checks.append(("normal_value_distribution_unreliable", False))
    if (
        candidate.get("feature_type") == "raw_field"
        and candidate.get("value_type") in {"count", "duration", "score", "ratio"}
    ):
        checks.append(("continuous_value_requires_numeric_bucket", False))
    if candidate.get("feature_type") == "derived_feature":
        definition_present = (
            candidate.get("feature_definition_status") == "present"
            and bool(candidate.get("feature_definition"))
        )
        checks.append(("derived_feature_commonality_not_high", candidate.get("commonality_level") == "high"))
        checks.append(("derived_feature_missing_feature_definition", definition_present))
        checks.append(("derived_feature_missing_traceable_source", bool(candidate.get("source_fields") or candidate.get("source_events"))))
        checks.append(("derived_feature_missing_commonality_evidence", bool(candidate.get("commonality_evidence"))))
        if candidate.get("l5_usage") == "audit_only":
            checks.append(("derived_feature_audit_only_not_l5_input", False))
    for reason, ok in checks:
        if not ok:
            violations.append({
                "candidate_id": candidate_id,
                "violation_type": reason,
                "field_path": candidate.get("field_path"),
                "value_or_pattern": candidate.get("field_value_or_pattern"),
                "l4_decision": decision,
            })
    return violations


def classify_value_type(field_path: str, candidate: dict[str, Any]) -> str:
    key = field_key(field_path)
    role = str(candidate.get("field_role") or "")
    if "identifier" in role or key in {"device_id", "did", "uuid"}:
        return "identity_or_device_value"
    if key in {"ip24", "ip", "asn", "isp", "district"}:
        return "network_value"
    if key in {"accessibility_service", "sensor", "cpu_arch", "brand", "device_model", "one_risk_label"}:
        return "environment_value"
    if "action" in key or "behavior" in role:
        return "behavior_value"
    if "policy" in key or "strategy" in key:
        return "strategy_value"
    if candidate.get("l4_decision") == "strong_single_candidate":
        return "direct_risk_value"
    return "unknown"


def eval_request() -> dict[str, Any]:
    return {
        "need_candidate_eval": True,
        "eval_status": "not_run",
        "eval_required_fields": [
            "global_base_rate",
            "white_sample_rate",
            "risk_white_lift",
            "historical_recall",
            "temporal_stability",
            "false_positive_proxy",
        ],
        "suggested_eval_types": [
            "white_sample_contrast",
            "global_base_rate",
            "temporal_stability",
            "historical_recall",
            "risk_concentration_proxy",
        ],
    }


def normalized_baseline_mode(value: Any) -> str:
    return "baseline_supported" if str(value or "") == "baseline_supported" else "discovery_only"


def strategy_draft_type_for_modes(modes: list[Any]) -> str:
    clean = [normalized_baseline_mode(mode) for mode in modes]
    if clean and all(mode == "baseline_supported" for mode in clean):
        return "formal_strategy_draft"
    return "experimental_strategy_draft"


def strategy_fields_for_nodes(nodes: list[dict[str, Any]]) -> dict[str, Any]:
    modes = [node.get("baseline_mode") for node in nodes]
    clean_modes = [normalized_baseline_mode(mode) for mode in modes]
    discovery_only_count = sum(1 for mode in clean_modes if mode == "discovery_only")
    baseline_supported_count = sum(1 for mode in clean_modes if mode == "baseline_supported")
    return {
        "baseline_mode": "baseline_supported" if clean_modes and all(mode == "baseline_supported" for mode in clean_modes) else "discovery_only",
        "strategy_draft_type": strategy_draft_type_for_modes(modes),
        "total_feature_count": len(nodes),
        "discovery_only_count": discovery_only_count,
        "baseline_supported_count": baseline_supported_count,
        "experimental_strategy_bounds": {
            "total_feature_count_max": MAX_EXPERIMENTAL_TOTAL_FEATURE_COUNT,
            "default_discovery_only_count_max": DEFAULT_MAX_DISCOVERY_ONLY_COUNT,
            "hard_max_discovery_only_count": HARD_MAX_DISCOVERY_ONLY_COUNT,
            "pure_discovery_only_feature_count_max": PURE_DISCOVERY_MAX_FEATURE_COUNT,
        },
        "requires_l6_replay": True,
        "l6_replay_required_reason": L6_REPLAY_REQUIRED_REASON,
    }


def experimental_combo_filter_reason(candidate: dict[str, Any]) -> str:
    if candidate.get("strategy_draft_type") != "experimental_strategy_draft":
        return ""
    try:
        total_count = int(candidate.get("total_feature_count") or 0)
    except (TypeError, ValueError):
        total_count = 0
    try:
        discovery_count = int(candidate.get("discovery_only_count") or 0)
    except (TypeError, ValueError):
        discovery_count = 0
    try:
        baseline_count = int(candidate.get("baseline_supported_count") or 0)
    except (TypeError, ValueError):
        baseline_count = 0
    if total_count > MAX_EXPERIMENTAL_TOTAL_FEATURE_COUNT:
        return f"experimental_strategy_total_feature_count>{MAX_EXPERIMENTAL_TOTAL_FEATURE_COUNT}"
    if discovery_count > HARD_MAX_DISCOVERY_ONLY_COUNT:
        return f"experimental_strategy_discovery_only_count>{HARD_MAX_DISCOVERY_ONLY_COUNT}"
    if baseline_count == 0 and discovery_count > PURE_DISCOVERY_MAX_FEATURE_COUNT:
        return f"pure_discovery_only_feature_count>{PURE_DISCOVERY_MAX_FEATURE_COUNT}"
    if discovery_count > DEFAULT_MAX_DISCOVERY_ONLY_COUNT and baseline_count < 1:
        return f"discovery_only_count>{DEFAULT_MAX_DISCOVERY_ONLY_COUNT}_without_baseline_supported_anchor"
    return ""


def pattern_eval_request() -> dict[str, Any]:
    return {
        "need_candidate_eval": True,
        "eval_target_type": "pattern_level",
        "eval_status": "not_run",
        "eval_required_fields": [
            "global_base_rate",
            "white_sample_rate",
            "risk_white_lift",
            "historical_recall",
            "temporal_stability",
            "false_positive_proxy",
        ],
        "suggested_eval_types": [
            "pattern_base_rate",
            "white_sample_contrast",
            "historical_recall",
            "temporal_stability",
            "risk_concentration_proxy",
        ],
    }


def field_family_proxy(field_key_value: str) -> str:
    if field_key_value in {"brand", "os", "os_version", "province", "city", "country", "isp"}:
        return "over_general"
    if field_key_value in {"device_id", "did", "uuid", "token", "user_id"}:
        return "unique_identifier"
    if field_key_value in {"policy", "strategy", "punish", "decision", "result"}:
        return "label_leakage"
    if field_key_value in {"accessibility_service", "sensor", "one_risk_label", "cpu_arch", "device_model"}:
        return "explainable_environment"
    if field_key_value in {"ip24", "asn"}:
        return "anchor_candidate"
    return "unknown"


def overlay_items(kb: dict[str, Any], key: str) -> list[dict[str, Any]]:
    overlay = kb.get("_prior_overlay") or {}
    legacy = overlay.get(key, []) or []
    field_kb = kb.get("_field_prior_kb") or {}
    mapped_key = {
        "field_pair_prior_seed_library": "field_pair_prior",
        "natural_relation_seed_library": "natural_relation_map",
    }.get(key, key)
    return list(field_kb.get(mapped_key, []) or []) + list(legacy)


def overlay_field_match(node_or_field: dict[str, Any] | str, kb: dict[str, Any], map_name: str) -> dict[str, Any] | None:
    if isinstance(node_or_field, dict):
        field_path = str(node_or_field.get("field_path") or "")
        key = str(node_or_field.get("field_key") or "")
    else:
        field_path = str(node_or_field)
        key = field_key(field_path)
    for item in overlay_items(kb, map_name):
        item_field = item.get("field_path") or item.get("field_key")
        if item_field in {field_path, key}:
            return item
    return None


def overlay_field_pair_match(anchor: dict[str, Any], target: dict[str, Any], kb: dict[str, Any]) -> dict[str, Any] | None:
    a_path = anchor.get("field_path")
    b_path = target.get("field_path")
    a_key = anchor.get("field_key")
    b_key = target.get("field_key")
    for item in overlay_items(kb, "field_pair_prior_seed_library"):
        item_a = item.get("anchor_field") or item.get("field_a") or item.get("field_path_a")
        item_b = item.get("target_field") or item.get("field_b") or item.get("field_path_b")
        if (item_a, item_b) in {(a_path, b_path), (a_key, b_key), (b_path, a_path), (b_key, a_key)}:
            return item
    return None


def value_relation_overlay_match(anchor: dict[str, Any], target: dict[str, Any], kb: dict[str, Any]) -> dict[str, Any] | None:
    overlay = kb.get("_value_relation_overlay") or {}
    items = overlay.get("value_relation_prior_overlay", []) or []
    a_field = anchor.get("field_path")
    b_field = target.get("field_path")
    a_value = canonical_value_key(anchor.get("value_or_pattern"))
    b_value = canonical_value_key(target.get("value_or_pattern"))
    for item in items:
        item_a_field = item.get("anchor_field")
        item_b_field = item.get("target_field")
        item_a_value = canonical_value_key(item.get("anchor_value"))
        item_b_value = canonical_value_key(item.get("target_value"))
        if (item_a_field, item_b_field, item_a_value, item_b_value) == (a_field, b_field, a_value, b_value):
            return item
        if (item_a_field, item_b_field, item_a_value, item_b_value) == (b_field, a_field, b_value, a_value):
            out = dict(item)
            out["matched_reversed"] = True
            return out
    return None


def field_role_source(node: dict[str, Any], kb: dict[str, Any]) -> str:
    if overlay_field_match(node, kb, "field_role_map"):
        return "llm_overlay"
    key = node.get("field_key")
    if field_family_proxy(str(key)) != "unknown":
        return "base_kb"
    return "missing"


def node_guard_reason(node: dict[str, Any], kb: dict[str, Any]) -> str:
    path = str(node.get("field_path") or "").lower()
    key = str(node.get("field_key") or "")
    if overlay_field_match(node, kb, "unique_id_field_map") or field_family_proxy(key) == "unique_identifier":
        return "unique_id_or_exact_anchor_not_recommended_as_anchor"
    if overlay_field_match(node, kb, "leakage_field_map") or any(x in path for x in ["policy", "punish", "decision", "result", "hitpolicies", "ban", "audit", "risk_label"]):
        return "label_or_post_action_not_recommended_as_anchor"
    if key == "one_risk_label" or "weapon_one_risk" in path or "onerisk" in path:
        return "oneRisk_label_is_confirming_signal_not_primary_anchor"
    if overlay_field_match(node, kb, "over_general_field_map") or key in {"brand", "os", "os_version", "province", "city", "country", "cpu_arch"} or any(x in path for x in ["resolution", "battery", "camera"]):
        normal_rate = node.get("normal_value_rate")
        if normal_rate is None or float(normal_rate or 0.0) > 0.10:
            return "common_profile_context_requires_low_normal_rate_before_anchor"
    return ""


def anchor_eligibility_for_node(node: dict[str, Any]) -> dict[str, Any]:
    """Classify whether a node can be used as an eval anchor.

    Directional relation can still be interesting even when the left side is
    too broad for Hive/Candidate Eval. This keeps the relation but routes it to
    drilldown instead of the main eval queue.
    """
    field_key_value = str(node.get("field_key") or "")
    path = str(node.get("field_path") or "").lower()
    reason = str(node.get("not_recommended_as_anchor_reason") or "")
    normal_rate = node.get("normal_value_rate")
    lift = node.get("risk_normal_lift")
    support = int(node.get("support_count") or 0)
    if field_key_value in CONTEXT_EVIDENCE_FIELD_KEYS or "weapon_one_risk" in path or "onerisk" in path:
        return {
            "status": "rejected_as_eval_anchor",
            "reason": "oneRisk_or_label_like_signal_is_evidence_node_only",
            "candidate_eval_eligible": False,
        }
    if "label_or_post_action" in reason:
        return {
            "status": "rejected_as_eval_anchor",
            "reason": reason,
            "candidate_eval_eligible": False,
        }
    if reason and ("unique_id" in reason or "oneRisk_label" in reason):
        return {
            "status": "rejected_as_eval_anchor",
            "reason": reason,
            "candidate_eval_eligible": False,
        }
    broad = (
        field_key_value in BROAD_ANCHOR_FIELD_KEYS
        or any(token in path for token in ["resolution", "battery", "camera"])
        or "device_profile_context" in path
    )
    if broad:
        if normal_rate is None:
            return {
                "status": "need_finer_granularity",
                "reason": "broad_anchor_missing_normal_value_rate",
                "candidate_eval_eligible": False,
                "drilldown_hint": "device_model / os_version / rom_version / device_environment_pattern",
            }
        if float(normal_rate) > 0.10 or lift is None or float(lift) < 5.0 or support < 3:
            return {
                "status": "broad_anchor_hold",
                "reason": "broad_anchor_requires_low_normal_rate_high_lift_and_support",
                "candidate_eval_eligible": False,
                "drilldown_hint": "device_model / os_version / rom_version / device_environment_pattern",
            }
    gate = node.get("anchor_quality_gate")
    if gate in {"preferred_anchor", "usable_anchor", "unknown_normal_proxy_anchor"}:
        return {
            "status": "eligible",
            "reason": "anchor_unit_eligible",
            "candidate_eval_eligible": True,
        }
    if gate == "weak_anchor":
        return {
            "status": "need_finer_granularity",
            "reason": "weak_anchor_requires_refinement_component",
            "candidate_eval_eligible": False,
            "drilldown_hint": "combine_with_refinement_component",
        }
    return {
        "status": "context_only",
        "reason": "not_suitable_as_eval_anchor",
        "candidate_eval_eligible": False,
    }


def value_penalties(node: dict[str, Any], kb: dict[str, Any] | None = None) -> dict[str, float]:
    key = node.get("field_key", "")
    path = str(node.get("field_path") or "").lower()
    penalties = {
        "uniqueness_penalty": 0.0,
        "over_generalization_penalty": 0.0,
        "label_leakage_penalty": 0.0,
        "post_action_penalty": 0.0,
    }
    kb = kb or {}
    if overlay_field_match(node, kb, "unique_id_field_map") or field_family_proxy(key) == "unique_identifier" or any(x in path for x in ["token", "uuid", "userid", "deviceid"]):
        penalties["uniqueness_penalty"] = 45.0
    if overlay_field_match(node, kb, "over_general_field_map") or field_family_proxy(key) == "over_general":
        penalties["over_generalization_penalty"] = 18.0
    if overlay_field_match(node, kb, "leakage_field_map") or any(x in path for x in ["policy", "punish", "decision", "result", "hitpolicies"]):
        penalties["label_leakage_penalty"] = 40.0
    if any(x in path for x in ["review", "ban", "appeal", "audit"]):
        penalties["post_action_penalty"] = 25.0
    return penalties


def safe_lift(risk_rate: float, normal_rate: Any) -> float | None:
    if normal_rate is None:
        return None
    normal = float(normal_rate or 0.0)
    if normal <= 0:
        return round(risk_rate / 0.001, 4)
    return round(risk_rate / normal, 4)


def anchor_quality_gate(normal_value_rate: Any, risk_normal_lift: Any, support_count: int, guard_reason: str) -> tuple[str, str]:
    if guard_reason:
        return "reject_as_anchor", guard_reason
    if normal_value_rate is None:
        return "unknown_normal_proxy_anchor", "normal_value_rate_missing_use_proxy_scoring"
    normal_rate = float(normal_value_rate or 0.0)
    lift = float(risk_normal_lift or 0.0)
    if normal_rate > 0.40:
        return "reject_as_anchor", "normal_value_rate_gt_0_40"
    if normal_rate > 0.20:
        return "weak_anchor", "normal_value_rate_0_20_to_0_40"
    if normal_rate > 0.10:
        if lift >= 8.0 and support_count >= 3:
            return "usable_anchor", "normal_value_rate_0_10_to_0_20_with_high_lift"
        return "weak_anchor", "normal_value_rate_0_10_to_0_20_without_enough_lift"
    if lift >= 5.0 and support_count >= 3:
        return "preferred_anchor", "normal_value_rate_le_0_10_with_enough_lift"
    return "usable_anchor", "normal_value_rate_le_0_10_but_lift_or_support_not_high"


def score_value_node(node: dict[str, Any], kb: dict[str, Any], normal_baseline: dict[str, Any] | None = None) -> dict[str, Any]:
    try:
        risk_hit_rate = float(node.get("risk_hit_rate") or 0.0)
    except (TypeError, ValueError):
        risk_hit_rate = 0.0
    support = int(node.get("support_count") or 0)
    normal_stats = normal_stats_for(node.get("field_path", ""), node.get("value_or_pattern"), normal_baseline)
    node.update(normal_stats)
    normal_entropy = normal_stats.get("normal_field_entropy_normalized")
    normal_value_rate = normal_stats.get("normal_value_rate")
    risk_normal_lift = safe_lift(risk_hit_rate, normal_value_rate)
    support_score = min(support, 6) / 6 * 25.0
    rate_score = risk_hit_rate * 40.0
    key = node.get("field_key", "")
    family = field_family_proxy(key)
    entropy_proxy = (float(normal_entropy) * 20.0) if normal_entropy is not None else 10.0
    normal_rarity_score = 0.0
    if normal_value_rate is not None:
        normal_rarity_score = max(0.0, min(25.0, (1.0 - min(float(normal_value_rate), 1.0)) * 25.0))
    explainability_proxy = 8.0 if family in {"explainable_environment", "anchor_candidate"} else 3.0
    granularity_status, granularity_reason = value_granularity_check(node, kb)
    granularity_score = {"pass": 10.0, "uncertain": 4.0, "too_fine": -10.0, "too_coarse": -25.0, "missing_value": -50.0}.get(granularity_status, 0.0)
    penalties = value_penalties(node, kb)
    guard_reason = node_guard_reason(node, kb)
    anchor_guard_penalty = 0.0
    if guard_reason:
        anchor_guard_penalty = 45.0 if "oneRisk" in guard_reason or "label" in guard_reason else 25.0
    lift_score = 0.0 if risk_normal_lift is None else min(20.0, math.log2(max(float(risk_normal_lift), 1.0)) * 5.0)
    anchor_score = (
        support_score
        + rate_score * 0.8
        + entropy_proxy
        + normal_rarity_score
        + lift_score
        + granularity_score
        - penalties["uniqueness_penalty"]
        - penalties["label_leakage_penalty"]
        - penalties["post_action_penalty"]
        - penalties["over_generalization_penalty"] * 0.8
        - anchor_guard_penalty
    )
    refinement_component_score = max(0.0, anchor_score * 0.75 + normal_rarity_score * 0.4 + entropy_proxy * 0.4)
    confirming_score = (
        support_score
        + rate_score * 0.7
        + explainability_proxy * 2.0
        + granularity_score
        - penalties["uniqueness_penalty"]
        - penalties["label_leakage_penalty"] * 0.8
        - penalties["post_action_penalty"] * 0.8
        - penalties["over_generalization_penalty"] * 0.4
    )
    next_node_score = max(0.0, round(max(refinement_component_score, confirming_score), 4))
    anchor_score = max(0.0, round(anchor_score, 4))
    anchor_gate, anchor_gate_reason = anchor_quality_gate(normal_value_rate, risk_normal_lift, support, guard_reason)
    if anchor_gate == "reject_as_anchor":
        anchor_score = min(anchor_score, 10.0)
    elif anchor_gate == "weak_anchor":
        anchor_score = min(anchor_score, 45.0)
    elif anchor_gate == "usable_anchor":
        anchor_score = min(anchor_score, 69.0)
    score = rate_score + support_score + entropy_proxy + explainability_proxy + granularity_score - sum(penalties.values())
    score = max(0.0, round(score, 4))
    if granularity_status in {"missing_value", "too_coarse"} or penalties["uniqueness_penalty"] >= 45.0 or penalties["label_leakage_penalty"] >= 40.0:
        role = "reject_node"
    elif anchor_gate == "preferred_anchor" and anchor_score >= 70:
        role = "preferred_anchor"
    elif anchor_gate == "usable_anchor" and anchor_score >= 55:
        role = "usable_anchor"
    elif anchor_gate == "weak_anchor":
        role = "weak_anchor"
    elif anchor_gate == "reject_as_anchor":
        role = "confirming_node" if guard_reason and next_node_score >= 50 else "reject_as_anchor"
    elif next_node_score >= 60 and (normal_rarity_score >= 15 or entropy_proxy >= 12) and not guard_reason:
        role = "refinement_component"
    elif next_node_score >= 50:
        role = "confirming_node" if guard_reason or family == "explainable_environment" else "next_node_candidate"
    elif score >= 48:
        role = "next_node_candidate"
    elif score >= 28:
        role = "context_node"
    else:
        role = "hold_node"
    if score >= 80:
        bucket = "S"
    elif score >= 65:
        bucket = "A"
    elif score >= 50:
        bucket = "B"
    elif score >= 30:
        bucket = "C"
    else:
        bucket = "D"
    return {
        "value_score": score,
        "anchor_score": anchor_score,
        "next_node_score": next_node_score,
        "ranking_bucket": bucket,
        "role_suggestion": role,
        "not_recommended_as_anchor_reason": guard_reason,
        "anchor_quality_gate": anchor_gate,
        "anchor_quality_reason": anchor_gate_reason,
        "normal_baseline_status": normal_stats.get("normal_baseline_status"),
        "normal_field_non_null_count": normal_stats.get("normal_field_non_null_count"),
        "normal_field_distinct_count": normal_stats.get("normal_field_distinct_count"),
        "normal_field_entropy": normal_stats.get("normal_field_entropy"),
        "normal_field_entropy_normalized": normal_stats.get("normal_field_entropy_normalized"),
        "normal_value_count": normal_stats.get("normal_value_count"),
        "normal_value_rate": normal_value_rate,
        "risk_value_rate": risk_hit_rate,
        "risk_normal_lift": risk_normal_lift,
        "field_role_source": field_role_source(node, kb),
        "scoring_inputs": {
            "support_count": support,
            "risk_hit_rate": risk_hit_rate,
            "normal_field_entropy_normalized": normal_entropy,
            "normal_value_rate": normal_value_rate,
            "risk_normal_lift": risk_normal_lift,
            "granularity_check": granularity_status,
            "field_family_proxy": family,
        },
        "ranking_reason": {
            "risk_hit_rate_score": round(rate_score, 4),
            "support_score": round(support_score, 4),
            "field_entropy_proxy": entropy_proxy,
            "normal_rarity_score": round(normal_rarity_score, 4),
            "risk_normal_lift_score": round(lift_score, 4),
            "anchor_guard_penalty": anchor_guard_penalty,
            "explainability_proxy": explainability_proxy,
            "granularity_check": granularity_status,
            "granularity_reason": granularity_reason,
            **penalties,
        },
        "eval_required_fields": eval_request()["eval_required_fields"],
        "global_value_rate": None,
        "white_value_rate": None,
        "risk_white_lift": None,
        "temporal_stability_score": None,
        "historical_recall_score": None,
        "true_precision_proxy": None,
    }


def rank_value_nodes(nodes: list[dict[str, Any]], kb: dict[str, Any], normal_baseline: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    for node in nodes:
        node.update(score_value_node(node, kb, normal_baseline))
    ranked = sorted(nodes, key=lambda n: (n["value_score"], n["support_count"], n.get("risk_hit_rate") or 0.0), reverse=True)
    for idx, node in enumerate(ranked, 1):
        node["value_rank"] = idx
    anchor_ranked = sorted(nodes, key=lambda n: (n.get("anchor_score", 0.0), n["support_count"], n.get("risk_hit_rate") or 0.0), reverse=True)
    for idx, node in enumerate(anchor_ranked, 1):
        node["anchor_rank"] = idx
    next_ranked = sorted(nodes, key=lambda n: (n.get("next_node_score", 0.0), n["support_count"], n.get("risk_hit_rate") or 0.0), reverse=True)
    for idx, node in enumerate(next_ranked, 1):
        node["next_node_rank"] = idx
    return nodes


def build_value_nodes(candidates: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    nodes: list[dict[str, Any]] = []
    violations: list[dict[str, Any]] = []
    for idx, candidate in enumerate(candidates, 1):
        bad = validate_l4_candidate(candidate)
        if bad:
            violations.extend(bad)
            continue
        sample_ids = sorted({str(x) for x in candidate.get("risk_hit_sample_ids", [])})
        support_count = int(candidate.get("support_count", candidate.get("risk_hit_count", len(sample_ids))) or len(sample_ids))
        field_path = str(candidate.get("field_path"))
        node_id = f"node_{idx:04d}_{candidate.get('candidate_id')}"
        nodes.append({
            "node_id": node_id,
            "source_candidate_id": candidate.get("candidate_id"),
            "field_path": field_path,
            "field_key": field_key(field_path),
            "value_or_pattern": candidate.get("field_value_or_pattern"),
            "feature_type": candidate.get("feature_type", "raw_field"),
            "candidate_value": candidate.get("candidate_value", candidate.get("field_value_or_pattern")),
            "feature_name": candidate.get("feature_name") or field_path,
            "candidate_source": candidate.get("candidate_source"),
            "proposal_source": candidate.get("proposal_source"),
            "proposal_type": candidate.get("proposal_type"),
            "quality_bucket": candidate.get("quality_bucket"),
            "baseline_status": candidate.get("baseline_status"),
            "next_step_suggestion": candidate.get("next_step_suggestion"),
            "lineage": candidate.get("lineage"),
            "audit_tags": candidate.get("audit_tags") or [],
            "merge_group_id": candidate.get("merge_group_id"),
            "representative_feature_id": candidate.get("representative_feature_id"),
            "merged_from_feature_ids": candidate.get("merged_from_feature_ids") or [],
            "source_fields": candidate.get("source_fields") or [field_path],
            "source_events": candidate.get("source_events") or [],
            "feature_definition": candidate.get("feature_definition") or {},
            "feature_definition_status": candidate.get("feature_definition_status"),
            "commonality_family": candidate.get("commonality_family"),
            "commonality_level": candidate.get("commonality_level"),
            "commonality_evidence": candidate.get("commonality_evidence") or [],
            "bucket_label": candidate.get("bucket_label"),
            "bucket_range": candidate.get("bucket_range"),
            "baseline_mode": normalized_baseline_mode(candidate.get("baseline_mode")),
            "normal_hit_rate": candidate.get("normal_hit_rate") if normalized_baseline_mode(candidate.get("baseline_mode")) == "baseline_supported" else None,
            "lift": candidate.get("lift") if normalized_baseline_mode(candidate.get("baseline_mode")) == "baseline_supported" else None,
            "l5_usage": candidate.get("l5_usage") or strategy_draft_type_for_modes([candidate.get("baseline_mode")]),
            "requires_l6_replay": True,
            "l6_replay_required_reason": L6_REPLAY_REQUIRED_REASON,
            "risk_hit_sample_ids": sample_ids,
            "support_count": support_count,
            "risk_hit_rate": candidate.get("risk_hit_rate"),
            "value_type": candidate.get("value_type") or classify_value_type(field_path, candidate),
            "l4_decision": candidate.get("l4_decision"),
            "evidence_boundary": EVIDENCE_BOUNDARY,
        })
    return nodes, violations


def build_inverted_indexes(nodes: list[dict[str, Any]]) -> dict[str, dict[str, list[str]]]:
    sample_to_nodes: defaultdict[str, list[str]] = defaultdict(list)
    node_to_samples: dict[str, list[str]] = {}
    field_to_nodes: defaultdict[str, list[str]] = defaultdict(list)
    for node in nodes:
        node_id = node["node_id"]
        node_to_samples[node_id] = list(node["risk_hit_sample_ids"])
        field_to_nodes[node["field_path"]].append(node_id)
        for sample_id in node["risk_hit_sample_ids"]:
            sample_to_nodes[sample_id].append(node_id)
    return {
        "sample_id_to_value_node_ids": dict(sample_to_nodes),
        "value_node_id_to_sample_ids": node_to_samples,
        "field_path_to_value_node_ids": dict(field_to_nodes),
    }


def value_granularity_check(node: dict[str, Any], kb: dict[str, Any]) -> tuple[str, str]:
    value = str(node.get("value_or_pattern") or "").strip()
    rules = kb.get("value_granularity_rules", {})
    if value == "":
        return "missing_value", "value_or_pattern is missing"
    if value.lower() in {str(v).lower() for v in rules.get("coarse_values", [])}:
        return "too_coarse", "value_or_pattern is too broad"
    if node.get("field_key") == "ip24" and value.endswith(".*"):
        return "pass", "ip24 pattern is scoped"
    if node.get("field_key") in rules.get("too_fine_field_tokens", []) and int(node.get("support_count") or 0) < int(rules.get("too_fine_min_support", 3)):
        return "too_fine", "fine-grained value has insufficient support"
    return "pass", "granularity accepted"


def natural_relation(anchor: dict[str, Any], target: dict[str, Any], kb: dict[str, Any]) -> dict[str, Any]:
    a = anchor["field_key"]
    b = target["field_key"]
    for item in overlay_items(kb, "natural_relation_seed_library"):
        item_a = item.get("from_field")
        item_b = item.get("to_field")
        if (item_a, item_b) in {(anchor.get("field_path"), target.get("field_path")), (a, b), (target.get("field_path"), anchor.get("field_path")), (b, a)}:
            return {**item, "judgement_source": item.get("judgement_source", "llm_seed_or_static_seed")}
    for item in kb.get("natural_determination_map", []):
        if item.get("from_field") == a and item.get("to_field") == b:
            return dict(item)
        if item.get("from_field") == b and item.get("to_field") == a:
            out = dict(item)
            out["matched_reversed"] = True
            return out
    return {"relation": "unknown", "action": "none"}


def field_pair_prior(anchor: dict[str, Any], target: dict[str, Any], kb: dict[str, Any]) -> dict[str, Any]:
    a = anchor["field_key"]
    b = target["field_key"]
    value_overlay = value_relation_overlay_match(anchor, target, kb)
    if value_overlay:
        confidence = value_overlay.get("confidence", "low")
        prior = value_overlay.get("prior", "value_relation_uncertain")
        mapped_prior = {
            "value_conditioned_unusual_relation": "normally_unrelated",
            "value_conditioned_common_relation": "normally_strong_related",
            "value_relation_context_only": "normally_weak_related",
            "value_relation_uncertain": "uncertain",
        }.get(prior, "uncertain")
        if confidence == "low":
            mapped_prior = "uncertain"
        return {
            "anchor_field": a,
            "target_field": b,
            "prior": mapped_prior,
            "value_relation_prior": prior,
            "recommended_usage": value_overlay.get("recommended_usage"),
            "confidence": confidence,
            "reason": value_overlay.get("reason", "run-level value relation overlay"),
            "judgement_source": value_overlay.get("judgement_source", "human_seed"),
            "need_human_review": value_overlay.get("need_human_review", True),
            "scope": "value_relation",
            "run_id": value_overlay.get("run_id"),
            "source_task_ids": value_overlay.get("source_task_ids", []),
        }
    for item in kb.get("field_pair_prior_config", []):
        if item.get("anchor_field") == a and item.get("target_field") == b:
            return {**item, "judgement_source": "config"}
        if item.get("anchor_field") == b and item.get("target_field") == a:
            return {**item, "matched_reversed": True, "judgement_source": "config"}
    overlay = overlay_field_pair_match(anchor, target, kb)
    if overlay:
        confidence = overlay.get("confidence", "low")
        if confidence == "low":
            return {
                "anchor_field": a,
                "target_field": b,
                "prior": "uncertain",
                "confidence": confidence,
                "reason": overlay.get("reason", "low confidence overlay kept uncertain"),
                "judgement_source": overlay.get("judgement_source", "llm_seed_or_static_seed"),
                "need_human_review": overlay.get("need_human_review", True),
            }
        return {
            "anchor_field": a,
            "target_field": b,
            "prior": overlay.get("prior") or overlay.get("judgement") or "uncertain",
            "confidence": confidence,
            "reason": overlay.get("reason", "overlay field-pair prior"),
            "judgement_source": overlay.get("judgement_source", "field_prior_kb"),
            "need_human_review": overlay.get("need_human_review", True),
            "scope": overlay.get("scope", "field_pair"),
        }
    return {
        "anchor_field": a,
        "target_field": b,
        "prior": "uncertain",
        "reason": "no configured field pair prior",
        "judgement_source": "rule_default",
    }


def thresholds_for(anchor: dict[str, Any], kb: dict[str, Any]) -> dict[str, Any]:
    global_thresholds = kb.get("global_thresholds", {})
    overrides = kb.get("threshold_overrides", {})
    field = anchor.get("field_key")
    if field in overrides:
        return {
            "threshold_source": "anchor_override",
            "min_support_samples": global_thresholds.get("min_support_samples", 3),
            "min_pair_conversion_rate": overrides[field].get("min_pair_conversion_rate", global_thresholds.get("min_pair_conversion_rate", 0.7)),
            "min_refinement_component_conversion_rate": overrides[field].get("min_refinement_component_conversion_rate", overrides[field].get("min_secondary_anchor_conversion_rate", global_thresholds.get("min_refinement_component_conversion_rate", global_thresholds.get("min_secondary_anchor_conversion_rate", 0.5)))),
            "min_path_conversion_rate": overrides[field].get("min_path_conversion_rate", global_thresholds.get("min_path_conversion_rate", 0.6)),
            "max_path_length": global_thresholds.get("max_path_length", 3),
        }
    return {
        "threshold_source": "global",
        "min_support_samples": global_thresholds.get("min_support_samples", 3),
        "min_pair_conversion_rate": global_thresholds.get("min_pair_conversion_rate", 0.7),
        "min_refinement_component_conversion_rate": global_thresholds.get("min_refinement_component_conversion_rate", global_thresholds.get("min_secondary_anchor_conversion_rate", 0.5)),
        "min_path_conversion_rate": global_thresholds.get("min_path_conversion_rate", 0.6),
        "max_path_length": global_thresholds.get("max_path_length", 3),
    }


def decide_pair(shared_count: int, pair_rate: float, granularity: list[dict[str, str]], natural: dict[str, Any], prior: dict[str, Any], thresholds: dict[str, Any]) -> str:
    if any(g["status"] == "missing_value" for g in granularity):
        return "reject_contract_violation"
    if any(g["status"] == "too_coarse" for g in granularity):
        return "reject_bad_granularity"
    if any(g["status"] == "too_fine" for g in granularity) and shared_count < thresholds["min_support_samples"]:
        return "hold_low_support"
    if natural.get("action") == "skip_as_trivial" or prior.get("prior") == "naturally_related":
        return "skip_as_trivial"
    if shared_count < thresholds["min_support_samples"]:
        return "hold_low_support"
    if pair_rate < thresholds["min_pair_conversion_rate"]:
        return "hold_low_conversion"
    return "pass_to_path_expansion"


def direction_anchor_block_reason(anchor: dict[str, Any], natural: dict[str, Any], prior: dict[str, Any]) -> str:
    if natural.get("action") == "skip_as_trivial" or prior.get("prior") == "naturally_related":
        return "natural_trivial_relation"
    if anchor.get("role_suggestion") == "reject_node":
        return "anchor_reject_node"
    reason = str(anchor.get("not_recommended_as_anchor_reason") or "")
    if any(token in reason for token in ["unique_id", "label_or_post_action", "oneRisk_label"]):
        return reason
    return ""


def is_refinement_component_target(target: dict[str, Any]) -> bool:
    if target.get("role_suggestion") == "reject_node":
        return False
    reason = str(target.get("not_recommended_as_anchor_reason") or "")
    if any(token in reason for token in ["unique_id", "label_or_post_action", "oneRisk_label"]):
        return False
    if target.get("anchor_quality_gate") not in {"preferred_anchor", "usable_anchor", "unknown_normal_proxy_anchor"}:
        return False
    entropy = target.get("normal_field_entropy_normalized")
    rate = target.get("normal_value_rate")
    lift = target.get("risk_normal_lift")
    if entropy is None or rate is None or lift is None:
        return target.get("anchor_quality_gate") == "unknown_normal_proxy_anchor" and float(target.get("anchor_score") or 0.0) >= 60
    return float(entropy) >= 0.5 and float(rate) <= 0.1 and float(lift) >= 5


def build_direction_view(
    direction_name: str,
    anchor: dict[str, Any],
    target: dict[str, Any],
    shared_count: int,
    natural: dict[str, Any],
    prior: dict[str, Any],
    thresholds: dict[str, Any],
) -> dict[str, Any]:
    anchor_support = int(anchor.get("support_count") or 0)
    target_support = int(target.get("support_count") or 0)
    directional_conversion = shared_count / anchor_support if anchor_support else 0.0
    reverse_conversion = shared_count / target_support if target_support else 0.0
    min_support = int(thresholds.get("min_support_samples", 3))
    min_conversion = float(thresholds.get("min_pair_conversion_rate", 0.7))
    refinement_min_conversion = float(thresholds.get("min_refinement_component_conversion_rate", 0.5))
    block_reason = direction_anchor_block_reason(anchor, natural, prior)
    if shared_count < min_support:
        decision = "hold_low_support"
        reason = f"cnt_intersection<{min_support}"
    elif block_reason:
        decision = "blocked_direction_anchor"
        reason = block_reason
    elif directional_conversion >= min_conversion:
        decision = "pass_directional_relation"
        reason = f"directional_conversion>={min_conversion}"
    elif directional_conversion >= refinement_min_conversion and is_refinement_component_target(target):
        decision = "pass_refinement_component_direction"
        reason = "refinement_component_direction_retained_for_composite_anchor_eval"
    else:
        decision = "hold_low_conversion"
        reason = f"directional_conversion<{min_conversion}"
    eval_anchor = anchor_eligibility_for_node(anchor)
    return {
        "direction": direction_name,
        "anchor_node_id": anchor.get("node_id"),
        "target_node_id": target.get("node_id"),
        "anchor_field": anchor.get("field_path"),
        "anchor_field_key": anchor.get("field_key"),
        "anchor_value": anchor.get("value_or_pattern"),
        "target_field": target.get("field_path"),
        "target_field_key": target.get("field_key"),
        "target_value": target.get("value_or_pattern"),
        "cnt_anchor": anchor_support,
        "cnt_target": target_support,
        "cnt_intersection": shared_count,
        "directional_conversion": directional_conversion,
        "reverse_conversion": reverse_conversion,
        "anchor_score": anchor.get("anchor_score"),
        "next_node_score": target.get("next_node_score"),
        "anchor_quality_gate": anchor.get("anchor_quality_gate"),
        "target_anchor_quality_gate": target.get("anchor_quality_gate"),
        "anchor_normal_value_rate": anchor.get("normal_value_rate"),
        "anchor_risk_normal_lift": anchor.get("risk_normal_lift"),
        "target_normal_value_rate": target.get("normal_value_rate"),
        "target_risk_normal_lift": target.get("risk_normal_lift"),
        "field_role_anchor": anchor.get("role_suggestion"),
        "field_role_target": target.get("role_suggestion"),
        "natural_relation_guard": natural,
        "field_pair_prior": prior,
        "leakage_guard": value_penalties(anchor).get("label_leakage_penalty", 0) > 0,
        "unique_id_guard": value_penalties(anchor).get("uniqueness_penalty", 0) > 0,
        "over_general_guard": value_penalties(anchor).get("over_generalization_penalty", 0) > 0,
        "direction_decision": decision,
        "direction_reason": reason,
        "eval_anchor_eligibility": eval_anchor.get("status"),
        "eval_anchor_eligibility_reason": eval_anchor.get("reason"),
        "eval_anchor_candidate_eval_eligible": eval_anchor.get("candidate_eval_eligible"),
        "drilldown_hint": eval_anchor.get("drilldown_hint"),
        "held_or_drilldown_reason": None if eval_anchor.get("candidate_eval_eligible") else eval_anchor.get("reason"),
    }


def relation_strength_from_directions(directions: dict[str, dict[str, Any]]) -> str:
    passed = {name for name, view in directions.items() if view.get("direction_decision") in PASS_DIRECTION_DECISIONS}
    if passed == {"A_to_B", "B_to_A"}:
        return "bidirectional"
    if passed == {"A_to_B"}:
        return "forward_only"
    if passed == {"B_to_A"}:
        return "reverse_only"
    return "none"


def role_compatibility(anchor: dict[str, Any], target: dict[str, Any]) -> float:
    if anchor.get("role_suggestion") == "preferred_anchor" and target.get("role_suggestion") in {"next_node_candidate", "preferred_anchor", "refinement_component", "confirming_node", "context_node"}:
        return 8.0
    if anchor.get("role_suggestion") == "reject_node" or target.get("role_suggestion") == "reject_node":
        return -50.0
    return 2.0


def pair_penalties(anchor: dict[str, Any], target: dict[str, Any], prior: dict[str, Any], natural: dict[str, Any], kb: dict[str, Any] | None = None) -> dict[str, float]:
    penalties = {
        "uncertainty_penalty": 0.0,
        "overfit_penalty": 0.0,
        "leakage_penalty": 0.0,
        "uniqueness_penalty": 0.0,
        "over_generalization_penalty": 0.0,
    }
    if prior.get("prior") == "uncertain" or prior.get("confidence") == "medium":
        penalties["uncertainty_penalty"] = 10.0
    if prior.get("confidence") == "low":
        penalties["uncertainty_penalty"] = max(penalties["uncertainty_penalty"], 16.0)
    usage = prior.get("recommended_usage")
    if usage == "context_only":
        penalties["over_generalization_penalty"] += 12.0
    if usage == "reject":
        penalties["overfit_penalty"] += 35.0
    if natural.get("action") == "skip_as_trivial":
        penalties["overfit_penalty"] += 40.0
    for node in (anchor, target):
        vp = value_penalties(node, kb)
        penalties["leakage_penalty"] += vp["label_leakage_penalty"] + vp["post_action_penalty"]
        penalties["uniqueness_penalty"] += vp["uniqueness_penalty"]
        penalties["over_generalization_penalty"] += vp["over_generalization_penalty"] * 0.5
    return penalties


def score_pair(anchor: dict[str, Any], target: dict[str, Any], pair: dict[str, Any], kb: dict[str, Any]) -> dict[str, Any]:
    prior = pair["field_pair_prior"]
    natural = pair["natural_relation_guard"]
    shared = pair["shared_support_count"]
    pair_rate = pair["pair_conversion_rate"]
    reverse_rate = pair["reverse_conversion_rate"]
    prior_bonus = {
        "normally_unrelated": 14.0,
        "normally_weak_related": 10.0,
        "normally_strong_related": 2.0,
        "uncertain": 0.0,
        "naturally_related": -35.0,
    }.get(prior.get("prior"), 0.0)
    explanation_proxy = 8.0 if pair["structure_interpretation"] != "uncertain_structure" else 2.0
    shared_support_score = min(shared, 6) / 6 * 20.0
    conversion_score = pair_rate * 22.0 + reverse_rate * 10.0
    anchor_component = float(anchor.get("anchor_score") or 0.0) * 0.32
    next_component = float(target.get("next_node_score") or 0.0) * 0.24
    penalties = pair_penalties(anchor, target, prior, natural, kb)
    anchor_guard_penalty = 0.0
    if anchor.get("not_recommended_as_anchor_reason"):
        anchor_guard_penalty = 22.0
    score = (
        anchor_component
        + next_component
        + shared_support_score
        + conversion_score
        + prior_bonus
        + explanation_proxy
        + role_compatibility(anchor, target)
        - anchor_guard_penalty
        - sum(penalties.values())
    )
    score = max(0.0, round(score, 4))
    path_gain = round((pair_rate * shared) - max(0, anchor.get("support_count", 0) - shared) * 0.2, 4)
    if pair["pair_decision"] != "pass_to_path_expansion":
        stop_reason = pair["pair_decision"]
    elif pair_rate >= 0.9 and explanation_proxy >= 8.0 and prior.get("prior") != "uncertain":
        stop_reason = "ab_sufficient_for_l6_eval"
    elif prior.get("prior") == "uncertain":
        stop_reason = "ab_allowed_but_uncertain_prior_no_path_expansion"
    else:
        stop_reason = "try_next_node_if_available"
    return {
        "pair_score": score,
        "relation_score": score,
        "anchor_score_component": round(anchor_component, 4),
        "next_node_score_component": round(next_component, 4),
        "path_gain": path_gain,
        "explanation_proxy": explanation_proxy,
        "role_compatibility": role_compatibility(anchor, target),
        **penalties,
        "ab_stop_or_continue_reason": stop_reason,
        "role_in_path": {
            anchor["node_id"]: "anchor",
            target["node_id"]: "refinement_component" if target.get("role_suggestion") == "refinement_component" and pair_rate >= 0.7 else "confirming" if target.get("role_suggestion") == "confirming_node" else "constraining" if pair_rate >= 0.8 else "context",
        },
        "anchor_not_recommended_reason": anchor.get("not_recommended_as_anchor_reason"),
        "global_value_rate": None,
        "white_value_rate": None,
        "risk_white_lift": None,
        "temporal_stability_score": None,
        "historical_recall_score": None,
        "true_precision_proxy": None,
        "eval_required_fields": eval_request()["eval_required_fields"],
    }


def build_pair_candidates(nodes: list[dict[str, Any]], kb: dict[str, Any]) -> list[dict[str, Any]]:
    pairs: list[dict[str, Any]] = []
    for left, right in combinations(nodes, 2):
        if left["field_path"] == right["field_path"]:
            continue
        if (right.get("anchor_score", 0.0), right.get("support_count", 0)) > (left.get("anchor_score", 0.0), left.get("support_count", 0)):
            anchor, target = right, left
        else:
            anchor, target = left, right
        shared = sorted(set(anchor["risk_hit_sample_ids"]) & set(target["risk_hit_sample_ids"]))
        shared_count = len(shared)
        anchor_support = int(anchor.get("support_count") or 0)
        target_support = int(target.get("support_count") or 0)
        pair_rate = shared_count / anchor_support if anchor_support else 0.0
        reverse_rate = shared_count / target_support if target_support else 0.0
        granularity = []
        for node in (anchor, target):
            status, reason = value_granularity_check(node, kb)
            granularity.append({"node_id": node["node_id"], "status": status, "reason": reason})
        natural = natural_relation(anchor, target, kb)
        prior = field_pair_prior(anchor, target, kb)
        thresholds = thresholds_for(anchor, kb)
        decision = decide_pair(shared_count, pair_rate, granularity, natural, prior, thresholds)
        reverse_thresholds = thresholds_for(target, kb)
        directions = {
            "A_to_B": build_direction_view("A_to_B", anchor, target, shared_count, natural, prior, thresholds),
            "B_to_A": build_direction_view("B_to_A", target, anchor, shared_count, natural, prior, reverse_thresholds),
        }
        selected_directions = [
            name for name, view in directions.items()
            if view.get("direction_decision") in PASS_DIRECTION_DECISIONS
        ]
        pair = {
            "l5_candidate_id": f"pair_{len(pairs)+1:05d}",
            "relation_id": f"rel_{len(pairs)+1:05d}",
            "candidate_type": "value_pair",
            "candidate_kind": "value_relation_candidate",
            "relation_level": "value_level",
            **strategy_fields_for_nodes([anchor, target]),
            "feature_names": [anchor.get("feature_name"), target.get("feature_name")],
            "feature_types": [anchor.get("feature_type"), target.get("feature_type")],
            "candidate_sources": [anchor.get("candidate_source"), target.get("candidate_source")],
            "proposal_sources": [anchor.get("proposal_source"), target.get("proposal_source")],
            "proposal_types": [anchor.get("proposal_type"), target.get("proposal_type")],
            "quality_buckets": [anchor.get("quality_bucket"), target.get("quality_bucket")],
            "baseline_statuses": [anchor.get("baseline_status"), target.get("baseline_status")],
            "next_step_suggestions": [anchor.get("next_step_suggestion"), target.get("next_step_suggestion")],
            "lineage": [anchor.get("lineage"), target.get("lineage")],
            "audit_tags": [anchor.get("audit_tags"), target.get("audit_tags")],
            "value_types": [anchor.get("value_type"), target.get("value_type")],
            "feature_definitions": [anchor.get("feature_definition"), target.get("feature_definition")],
            "bucket_labels": [anchor.get("bucket_label"), target.get("bucket_label")],
            "bucket_ranges": [anchor.get("bucket_range"), target.get("bucket_range")],
            "risk_hit_rates": [anchor.get("risk_hit_rate"), target.get("risk_hit_rate")],
            "commonality_families": [anchor.get("commonality_family"), target.get("commonality_family")],
            "commonality_levels": [anchor.get("commonality_level"), target.get("commonality_level")],
            "commonality_evidence": [anchor.get("commonality_evidence"), target.get("commonality_evidence")],
            "source_candidate_ids": [anchor.get("source_candidate_id"), target.get("source_candidate_id")],
            "anchor_value_node": anchor["node_id"],
            "target_value_node": target["node_id"],
            "anchor_field": anchor["field_key"],
            "target_field": target["field_key"],
            "anchor_score": anchor.get("anchor_score"),
            "next_node_score": target.get("next_node_score"),
            "anchor_role": anchor.get("role_suggestion"),
            "target_role": target.get("role_suggestion"),
            "anchor_quality_gate": anchor.get("anchor_quality_gate"),
            "anchor_quality_reason": anchor.get("anchor_quality_reason"),
            "target_anchor_quality_gate": target.get("anchor_quality_gate"),
            "target_anchor_quality_reason": target.get("anchor_quality_reason"),
            "anchor_field_role_source": anchor.get("field_role_source"),
            "target_field_role_source": target.get("field_role_source"),
            "anchor_normal_field_entropy": anchor.get("normal_field_entropy"),
            "anchor_normal_value_rate": anchor.get("normal_value_rate"),
            "anchor_risk_normal_lift": anchor.get("risk_normal_lift"),
            "target_normal_field_entropy": target.get("normal_field_entropy"),
            "target_normal_value_rate": target.get("normal_value_rate"),
            "target_risk_normal_lift": target.get("risk_normal_lift"),
            "shared_sample_ids": shared,
            "shared_support_count": shared_count,
            "anchor_support_count": anchor_support,
            "target_support_count": target_support,
            "pair_conversion_rate": pair_rate,
            "reverse_conversion_rate": reverse_rate,
            "field_pair_prior": prior,
            "natural_relation_guard": natural,
            "value_granularity_check": granularity,
            "threshold_source": thresholds["threshold_source"],
            "threshold_values": thresholds,
            "pair_decision": decision,
            "directional_metrics": directions,
            "selected_directions": selected_directions,
            "primary_direction": selected_directions[0] if selected_directions else "A_to_B",
            "relation_strength": relation_strength_from_directions(directions),
            "value_path": [anchor["value_or_pattern"], target["value_or_pattern"]],
            "field_path_sequence": [anchor["field_path"], target["field_path"]],
            "value_node_ids": [anchor["node_id"], target["node_id"]],
            "evidence_boundary": EVIDENCE_BOUNDARY,
            "structure_interpretation": interpret_structure([anchor, target], prior),
        }
        pair.update(score_pair(anchor, target, pair, kb))
        pair["relation_expression"] = pair_relation_expression(pair)
        pair["observed_metrics"] = pair_observed_metrics(pair)
        pair["thresholds"] = pair_thresholds(pair)
        pairs.append(pair)
    ranked_pairs = sorted(pairs, key=lambda p: (p.get("pair_score", 0.0), p.get("shared_support_count", 0)), reverse=True)
    for idx, pair in enumerate(ranked_pairs, 1):
        pair["pair_rank"] = idx
    return pairs


def interpret_structure(nodes: list[dict[str, Any]], prior: dict[str, Any]) -> str:
    keys = {n["field_key"] for n in nodes}
    if "ip24" in keys or any(k in keys for k in {"asn", "isp"}):
        return "shared_infrastructure_pattern"
    if keys & {"device_model", "brand", "cpu_arch", "sensor", "accessibility_service", "one_risk_label"}:
        return "device_environment_binding"
    if any("action" in k for k in keys):
        return "behavior_environment_binding"
    if any("policy" in k or "strategy" in k for k in keys):
        return "strategy_signal_binding"
    if prior.get("prior") == "uncertain":
        return "uncertain_structure"
    return "uncertain_structure"


def node_text(node: dict[str, Any]) -> str:
    return f"{node.get('field_path', '')}={node.get('value_or_pattern', '')}".lower()


def is_low_activity_device_signal(node: dict[str, Any]) -> bool:
    text = node_text(node)
    tokens = [
        "onerisklaunchless10",
        "launchless10",
        "nolockscreen",
        "nosim",
        "onerisknosim",
        "lockscreenlong",
        "startshort",
        "onedayreset",
        "oneriskonedayreset",
        "factoryreset",
    ]
    return any(token.lower() in text for token in tokens)


def is_registration_packaging_signal(node: dict[str, Any]) -> bool:
    text = node_text(node)
    tokens = [
        "nickname",
        "avatar",
        "profile",
        "bio",
        "signature",
        "bind",
        "register",
        "registration",
        "after_registration",
        "modify",
        "change",
    ]
    return any(token in text for token in tokens)


def expand_paths(pairs: list[dict[str, Any]], nodes: list[dict[str, Any]], kb: dict[str, Any]) -> list[dict[str, Any]]:
    pass_pairs = [
        p for p in pairs
        if p["pair_decision"] == "pass_to_path_expansion"
        and p.get("field_pair_prior", {}).get("prior") != "uncertain"
    ]
    by_anchor: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for pair in pass_pairs:
        by_anchor[pair["anchor_value_node"]].append(pair)
    node_by_id = {n["node_id"]: n for n in nodes}
    paths: list[dict[str, Any]] = []
    max_len = int(kb.get("global_thresholds", {}).get("max_path_length", 3))
    if max_len < 3:
        return paths
    frontier: list[dict[str, Any]] = []
    for first in pass_pairs:
        frontier.append({
            "node_ids": list(first["value_node_ids"]),
            "support": set(first["shared_sample_ids"]),
            "layer_rates": [first["pair_conversion_rate"]],
            "last_node": first["target_value_node"],
        })
    while frontier:
        current = frontier.pop(0)
        if len(current["node_ids"]) >= max_len:
            continue
        for next_pair in by_anchor.get(current["last_node"], []):
            next_node = next_pair["target_value_node"]
            if next_node in current["node_ids"]:
                continue
            next_support = current["support"] & set(next_pair["shared_sample_ids"])
            threshold = next_pair["threshold_values"]["min_path_conversion_rate"]
            previous_support = len(current["support"])
            layer_rate = len(next_support) / previous_support if previous_support else 0.0
            path_nodes = current["node_ids"] + [next_node]
            layer_rates = current["layer_rates"] + [layer_rate]
            if layer_rate < threshold:
                paths.append(build_path_record(
                    path_nodes,
                    node_by_id,
                    next_support,
                    layer_rates,
                    "pruned",
                    "hold_low_conversion",
                    previous_support_count=previous_support,
                    threshold_values=next_pair["threshold_values"],
                    threshold_source=next_pair["threshold_source"],
                ))
                continue
            record = build_path_record(
                path_nodes,
                node_by_id,
                next_support,
                layer_rates,
                "pass_to_l6",
                None,
                previous_support_count=previous_support,
                threshold_values=next_pair["threshold_values"],
                threshold_source=next_pair["threshold_source"],
            )
            paths.append(record)
            frontier.append({
                "node_ids": path_nodes,
                "support": next_support,
                "layer_rates": layer_rates,
                "last_node": next_node,
            })
    ranked_paths = sorted(paths, key=lambda p: (p.get("path_score", 0.0), p.get("support_count", 0)), reverse=True)
    for idx, path in enumerate(ranked_paths, 1):
        path["path_rank"] = idx
    return paths


def build_path_record(node_ids: list[str], node_by_id: dict[str, dict[str, Any]], support: set[str], layer_rates: list[float], decision: str, prune_reason: str | None, previous_support_count: int | None = None, threshold_values: dict[str, Any] | None = None, threshold_source: str | None = None) -> dict[str, Any]:
    nodes = [node_by_id[n] for n in node_ids]
    support_count = len(support)
    min_layer = min(layer_rates) if layer_rates else 0.0
    cross_field_bonus = min(len({n["field_key"] for n in nodes}), 4) * 4.0
    explanation_bonus = 8.0 if interpret_structure(nodes, {"prior": "configured"}) != "uncertain_structure" else 2.0
    incremental_path_gain = [round(rate * support_count, 4) for rate in layer_rates]
    path_score = max(0.0, round(support_count * 8.0 + min_layer * 35.0 + cross_field_bonus + explanation_bonus - max(0, len(nodes) - 3) * 4.0, 4))
    record = {
        "l5_candidate_id": "path_" + "_".join(str(i + 1) for i in range(len(node_ids))) + "_" + str(abs(hash(tuple(node_ids))) % 100000),
        "candidate_type": "value_path",
        "candidate_kind": "value_relation_candidate",
        "relation_level": "value_level",
        **strategy_fields_for_nodes(nodes),
        "feature_names": [n.get("feature_name") for n in nodes],
        "feature_types": [n.get("feature_type") for n in nodes],
        "value_types": [n.get("value_type") for n in nodes],
        "feature_definitions": [n.get("feature_definition") for n in nodes],
        "bucket_labels": [n.get("bucket_label") for n in nodes],
        "bucket_ranges": [n.get("bucket_range") for n in nodes],
        "risk_hit_rates": [n.get("risk_hit_rate") for n in nodes],
        "commonality_families": [n.get("commonality_family") for n in nodes],
        "commonality_levels": [n.get("commonality_level") for n in nodes],
        "commonality_evidence": [n.get("commonality_evidence") for n in nodes],
        "source_candidate_ids": [n.get("source_candidate_id") for n in nodes],
        "value_nodes": node_ids,
        "field_path_sequence": [n["field_path"] for n in nodes],
        "value_sequence": [n["value_or_pattern"] for n in nodes],
        "support_sample_ids": sorted(support),
        "support_count": support_count,
        "layer_conversion_rates": layer_rates,
        "min_layer_conversion_rate": min_layer,
        "previous_path_support_count": previous_support_count,
        "last_incremental_conversion_rate": layer_rates[-1] if layer_rates else None,
        "incremental_path_gain": incremental_path_gain,
        "path_score": path_score,
        "path_decision": decision,
        "prune_reason": prune_reason,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "structure_interpretation": interpret_structure(nodes, {"prior": "uncertain"}),
        "role_in_path": {node_id: ("anchor" if idx == 0 else "confirming" if idx == len(node_ids) - 1 else "constraining") for idx, node_id in enumerate(node_ids)},
        "eval_required_fields": eval_request()["eval_required_fields"],
        "global_value_rate": None,
        "white_value_rate": None,
        "risk_white_lift": None,
        "temporal_stability_score": None,
        "historical_recall_score": None,
        "true_precision_proxy": None,
        "candidate_signal_level": "candidate_signal",
        "threshold_values": threshold_values or {},
        "threshold_source": threshold_source,
    }
    record["relation_expression"] = path_relation_expression(record)
    record["observed_metrics"] = path_observed_metrics(record)
    record["thresholds"] = path_thresholds(record)
    record["conditional_gain_audit"] = conditional_gain_audit_for_path(node_ids, node_by_id, min_support=int((threshold_values or {}).get("min_support_samples", 3)))
    return record


def conditional_gain_audit_for_path(node_ids: list[str], node_by_id: dict[str, dict[str, Any]], min_support: int = 3) -> dict[str, Any]:
    if len(node_ids) < 3:
        return {"conditional_gain_status": "not_applicable"}
    prefix_ids = node_ids[:-1]
    target_id = node_ids[-1]
    target_samples = set(node_by_id[target_id].get("risk_hit_sample_ids", []))
    full_prefix = set(node_by_id[prefix_ids[0]].get("risk_hit_sample_ids", []))
    for node_id in prefix_ids[1:]:
        full_prefix &= set(node_by_id[node_id].get("risk_hit_sample_ids", []))
    full_with_target = full_prefix & target_samples
    if len(full_prefix) < min_support:
        return {
            "target_node": target_id,
            "conditional_gain_status": "insufficient_support",
            "prefix_support_count": len(full_prefix),
        }
    p_full = len(full_with_target) / len(full_prefix) if full_prefix else 0.0
    subpath_predictability: dict[str, float] = {}
    max_pred = 0.0
    labels = [chr(ord("A") + idx) for idx in range(len(prefix_ids))]
    for idx, node_id in enumerate(prefix_ids):
        samples = set(node_by_id[node_id].get("risk_hit_sample_ids", []))
        pred = len(samples & target_samples) / len(samples) if samples else 0.0
        subpath_predictability[labels[idx]] = pred
        max_pred = max(max_pred, pred)
    for i in range(len(prefix_ids)):
        for j in range(i + 1, len(prefix_ids)):
            samples = set(node_by_id[prefix_ids[i]].get("risk_hit_sample_ids", [])) & set(node_by_id[prefix_ids[j]].get("risk_hit_sample_ids", []))
            pred = len(samples & target_samples) / len(samples) if samples else 0.0
            key = f"{labels[i]}_{labels[j]}"
            subpath_predictability[key] = pred
            max_pred = max(max_pred, pred)
    gain = p_full - max_pred
    if len(full_with_target) < min_support:
        status = "insufficient_support"
    elif gain >= 0.2:
        status = "incremental_gain_candidate"
    else:
        status = "no_incremental_gain"
    return {
        "target_node": target_id,
        "p_target_given_full_path": round(p_full, 6),
        "max_subpath_predictability": round(max_pred, 6),
        "conditional_gain": round(gain, 6),
        "subpath_predictability": {k: round(v, 6) for k, v in subpath_predictability.items()},
        "conditional_gain_status": status,
    }


def sample_jaccard(left: list[str], right: list[str]) -> float:
    a = set(left)
    b = set(right)
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b) if (a | b) else 0.0


def hard_filter_reason(candidate: dict[str, Any]) -> str:
    combo_reason = experimental_combo_filter_reason(candidate)
    if combo_reason:
        return combo_reason
    if candidate.get("candidate_type") == "value_pair":
        decision = candidate.get("pair_decision")
        if decision == "reject_contract_violation":
            return "contract violation"
        if decision == "reject_bad_granularity":
            return "bad granularity"
        if decision == "skip_as_trivial":
            return "natural trivial pair"
        if decision == "hold_low_support":
            return "support below threshold"
        if decision == "hold_low_conversion":
            return "conversion below threshold"
        if candidate.get("uniqueness_penalty", 0) > 0:
            return "unique ID pair"
        if candidate.get("leakage_penalty", 0) > 0:
            return "label or post-action leakage"
        if decision != "pass_to_path_expansion":
            return str(decision)
    if candidate.get("candidate_type") == "value_path":
        if candidate.get("path_decision") != "pass_to_l6":
            return candidate.get("prune_reason") or "path not passed"
    return ""


def candidate_eval_block_reason(candidate: dict[str, Any]) -> str:
    if candidate.get("candidate_type") == "value_pair":
        decision = candidate.get("pair_decision")
        if candidate.get("selected_directions"):
            if decision in {"reject_contract_violation", "reject_bad_granularity", "skip_as_trivial"}:
                return hard_filter_reason(candidate)
            if candidate.get("uniqueness_penalty", 0) > 0:
                return "unique ID pair"
            if candidate.get("leakage_penalty", 0) > 0:
                return "label or post-action leakage"
            return ""
        return hard_filter_reason(candidate)
    return hard_filter_reason(candidate)


def score_for_selection(candidate: dict[str, Any]) -> float:
    if candidate.get("candidate_type") == "value_path":
        return float(candidate.get("path_score") or 0.0)
    return float(candidate.get("pair_score") or 0.0)


def strict_l6_anchor_eligibility(candidate: dict[str, Any]) -> tuple[bool, str]:
    """Final strict L6 gate.

    Candidate Eval can keep broader exploration, but strict L6 is a small
    human-review queue and must not include anchors that need drilldown.
    """
    if candidate.get("candidate_type") == "value_pair":
        direction = candidate.get("primary_direction") or "A_to_B"
        view = (candidate.get("directional_metrics") or {}).get(direction, {})
        eligibility = view.get("eval_anchor_eligibility")
        if eligibility == "eligible":
            return True, "strict_anchor_eligible"
        return False, f"strict anchor ineligible: eval_anchor_eligibility={eligibility or 'missing'}"
    if candidate.get("candidate_type") == "value_path":
        role = candidate.get("role_in_path") or {}
        first_node_id = (candidate.get("value_nodes") or [None])[0]
        if role.get(first_node_id) == "anchor":
            return True, "strict_path_anchor_eligible"
        return False, "strict path anchor eligibility missing"
    return False, "unsupported strict candidate type"


def score_for_candidate_eval(candidate: dict[str, Any]) -> float:
    if candidate.get("candidate_type") == "value_path":
        return score_for_selection(candidate)
    views = [
        (candidate.get("directional_metrics") or {}).get(direction, {})
        for direction in candidate.get("selected_directions", [])
    ]
    if not views:
        return score_for_selection(candidate)
    scores = []
    for view in views:
        score = (
            float(view.get("directional_conversion") or 0.0) * 40.0
            + min(int(view.get("cnt_intersection") or 0), 6) / 6 * 20.0
            + float(view.get("anchor_score") or 0.0) * 0.18
            + float(view.get("next_node_score") or 0.0) * 0.18
        )
        if view.get("direction_decision") == "pass_refinement_component_direction":
            score += 8.0
        if candidate.get("relation_strength") == "reverse_only":
            score += 24.0
        scores.append(score)
    return round(max(scores), 4)


def support_samples_for_selection(candidate: dict[str, Any]) -> list[str]:
    if candidate.get("candidate_type") == "value_path":
        return candidate.get("support_sample_ids", [])
    return candidate.get("shared_sample_ids", [])


def candidate_anchor_id(candidate: dict[str, Any]) -> str:
    return str(candidate.get("anchor_value_node") or (candidate.get("value_nodes") or ["path"])[0])


def field_pair_group(candidate: dict[str, Any]) -> str:
    if candidate.get("candidate_type") == "value_path":
        return "->".join(candidate.get("field_path_sequence", []))
    return f"{candidate.get('anchor_field')}->{candidate.get('target_field')}"


def field_family_for_path(field_path: str, key: str | None = None) -> str:
    text = (str(field_path or "") + " " + str(key or "")).lower()
    if "accessibility" in text:
        return "accessibility"
    if "onerisk" in text or "weapon_one_risk" in text:
        return "oneRisk"
    if "sensor" in text:
        return "sensor"
    if "ip" in text or "asn" in text or "district" in text or "scene" in text:
        return "network"
    if "lockscreen" in text:
        return "lock_screen_state"
    if "microphone" in text or "microphone" in text:
        return "microphone_state"
    if "battery" in text:
        return "battery_state"
    if "charging" in text:
        return "charging_state"
    if "volumn" in text or "volume" in text:
        return "volume_state"
    if "adb" in text:
        return "debug_state"
    if "launch" in text:
        return "low_activity_state"
    if any(x in text for x in ["cpu", "brand", "model", "resolution", "dpi", "camera", "api"]):
        return "device_profile"
    if "inputdevice" in text or "input_method" in text:
        return "input_method"
    return "other"


def candidate_target_field_path(candidate: dict[str, Any]) -> str:
    fields = candidate.get("field_path_sequence") or []
    return str(fields[1] if len(fields) > 1 else fields[-1] if fields else "")


def candidate_target_family(candidate: dict[str, Any]) -> str:
    return field_family_for_path(candidate_target_field_path(candidate), str(candidate.get("target_field") or ""))


def eval_queue_duplicate_relation(candidate: dict[str, Any], selected: list[dict[str, Any]], jaccard_threshold: float) -> tuple[str, dict[str, Any] | None, float | None]:
    for chosen in selected:
        score = sample_jaccard(support_samples_for_selection(candidate), support_samples_for_selection(chosen))
        if score < jaccard_threshold:
            continue
        if candidate_anchor_id(candidate) != candidate_anchor_id(chosen):
            continue
        same_target_path = candidate_target_field_path(candidate) == candidate_target_field_path(chosen)
        same_target_family = candidate_target_family(candidate) == candidate_target_family(chosen)
        if same_target_path or same_target_family:
            return "duplicate", chosen, score
        return "cross_family_overlap", chosen, score
    return "", None, None


def relation_nodes_from_fields(field_paths: list[str], values: list[Any]) -> list[dict[str, Any]]:
    roles = [chr(ord("A") + idx) for idx in range(len(field_paths))]
    return [
        {
            "role": role,
            "field_path": field_path,
            "value_or_pattern": values[idx] if idx < len(values) else None,
        }
        for idx, (role, field_path) in enumerate(zip(roles, field_paths))
    ]


def pair_relation_expression(pair: dict[str, Any]) -> dict[str, Any]:
    return {
        "relation_type": "value_relation",
        "path_length": 2,
        "nodes": relation_nodes_from_fields(pair.get("field_path_sequence", []), pair.get("value_path", [])),
        "logic": [
            "CNT(A_AND_B) >= min_pair_support",
            "CNT(A_AND_B) / CNT(A) >= min_pair_conversion_rate",
        ],
    }


def pair_observed_metrics(pair: dict[str, Any]) -> dict[str, Any]:
    return {
        "cnt_a": pair.get("anchor_support_count"),
        "cnt_b": pair.get("target_support_count"),
        "cnt_ab": pair.get("shared_support_count"),
        "conversion_ab_over_a": pair.get("pair_conversion_rate"),
        "reverse_conversion_ab_over_b": pair.get("reverse_conversion_rate"),
    }


def pair_thresholds(pair: dict[str, Any]) -> dict[str, Any]:
    values = pair.get("threshold_values", {})
    return {
        "min_pair_support": values.get("min_support_samples"),
        "min_pair_conversion_rate": values.get("min_pair_conversion_rate"),
        "threshold_source": pair.get("threshold_source"),
    }


def direction_relation_expression(pair: dict[str, Any], direction: str) -> dict[str, Any]:
    view = (pair.get("directional_metrics") or {}).get(direction, {})
    return {
        "relation_type": "value_relation",
        "path_length": 2,
        "selected_direction": direction,
        "nodes": [
            {
                "role": "anchor",
                "field_path": view.get("anchor_field"),
                "value_or_pattern": view.get("anchor_value"),
            },
            {
                "role": "target",
                "field_path": view.get("target_field"),
                "value_or_pattern": view.get("target_value"),
            },
        ],
        "logic": [
            "CNT(anchor_AND_target) >= min_pair_support",
            "CNT(anchor_AND_target) / CNT(anchor) >= min_pair_conversion_rate",
        ],
    }


def direction_observed_metrics(pair: dict[str, Any], direction: str) -> dict[str, Any]:
    view = (pair.get("directional_metrics") or {}).get(direction, {})
    return {
        "cnt_anchor": view.get("cnt_anchor"),
        "cnt_target": view.get("cnt_target"),
        "cnt_intersection": view.get("cnt_intersection"),
        "directional_conversion": view.get("directional_conversion"),
        "reverse_conversion": view.get("reverse_conversion"),
    }


def anchor_unit_for_direction(pair: dict[str, Any], direction: str) -> dict[str, Any]:
    view = (pair.get("directional_metrics") or {}).get(direction, {})
    anchor_component = {
        "field_path": view.get("anchor_field"),
        "value_or_pattern": view.get("anchor_value"),
        "node_id": view.get("anchor_node_id"),
        "role": "anchor_component",
    }
    evidence_node = {
        "field_path": view.get("target_field"),
        "value_or_pattern": view.get("target_value"),
        "node_id": view.get("target_node_id"),
        "role": "evidence_node",
    }
    return {
        "anchor_unit": {
            "anchor_unit_type": "atomic_anchor",
            "components": [anchor_component],
            "normal_joint_rate": view.get("anchor_normal_value_rate"),
            "normal_joint_rate_status": "single_field_normal_rate",
        },
        "anchor_unit_type": "atomic_anchor",
        "anchor_components": [anchor_component],
        "refinement_components": [],
        "evidence_nodes": [evidence_node],
        "relation_form": "atomic_anchor_to_evidence",
        "eval_anchor_eligibility": view.get("eval_anchor_eligibility"),
        "drilldown_hint": view.get("drilldown_hint"),
        "held_or_drilldown_reason": view.get("held_or_drilldown_reason"),
        "overfit_risk": False,
        "normal_joint_rate": view.get("anchor_normal_value_rate"),
        "normal_joint_rate_status": "single_field_normal_rate",
        "conditional_gain_audit": {"conditional_gain_status": "not_applicable"},
    }


def path_relation_expression(path: dict[str, Any]) -> dict[str, Any]:
    length = len(path.get("field_path_sequence", []))
    full = "_AND_".join(chr(ord("A") + idx) for idx in range(length))
    previous = "_AND_".join(chr(ord("A") + idx) for idx in range(max(0, length - 1)))
    return {
        "relation_type": "value_relation",
        "path_length": length,
        "nodes": relation_nodes_from_fields(path.get("field_path_sequence", []), path.get("value_sequence", [])),
        "logic": [
            f"CNT({full}) >= min_path_support",
            f"CNT({full}) / CNT({previous}) >= min_next_hop_conversion_rate",
        ],
    }


def path_observed_metrics(path: dict[str, Any]) -> dict[str, Any]:
    support_count = path.get("support_count")
    previous_support = path.get("previous_path_support_count")
    incremental = path.get("last_incremental_conversion_rate")
    return {
        "cnt_previous_path": previous_support,
        "cnt_full_path": support_count,
        "incremental_conversion_over_previous_path": incremental,
        "support_count": support_count,
        "min_layer_conversion_rate": path.get("min_layer_conversion_rate"),
        "layer_conversion_rates": path.get("layer_conversion_rates"),
    }


def path_thresholds(path: dict[str, Any]) -> dict[str, Any]:
    values = path.get("threshold_values", {})
    return {
        "min_path_support": values.get("min_support_samples"),
        "min_next_hop_conversion_rate": values.get("min_path_conversion_rate"),
        "threshold_source": path.get("threshold_source"),
    }


def select_top_k(pair_candidates: list[dict[str, Any]], path_candidates: list[dict[str, Any]], kb: dict[str, Any]) -> list[dict[str, Any]]:
    cfg = kb.get("top_k_selection", {})
    max_tasks = int(cfg.get("max_l6_tasks", 100))
    per_anchor_max = int(cfg.get("per_anchor_max_tasks", 10))
    per_field_pair_max = int(cfg.get("per_field_pair_max_tasks", 20))
    uncertain_limit = int(cfg.get("include_uncertain_prior_limit", 20))
    jaccard_threshold = float(cfg.get("near_duplicate_jaccard_threshold", 0.85))
    min_score = float(cfg.get("min_pair_score", 0.0))
    max_path_tasks = int(cfg.get("max_path_tasks", 20))

    all_candidates = pair_candidates + path_candidates
    for candidate in all_candidates:
        reason = hard_filter_reason(candidate)
        strict_ok, strict_reason = strict_l6_anchor_eligibility(candidate)
        candidate["selection_decision"] = "selected_top_k"
        candidate["selection_reason"] = "eligible"
        candidate["diversity_group"] = field_pair_group(candidate)
        candidate["duplicate_group_id"] = None
        if reason:
            candidate["selection_decision"] = "rejected_by_ranking"
            candidate["selection_reason"] = reason
        elif not strict_ok:
            candidate["selection_decision"] = "filtered_strict_ineligible_anchor"
            candidate["selection_reason"] = strict_reason
        elif score_for_selection(candidate) < min_score:
            candidate["selection_decision"] = "filtered_low_score"
            candidate["selection_reason"] = f"score below min_pair_score={min_score}"

    eligible = [
        c for c in all_candidates
        if c.get("selection_decision") == "selected_top_k"
    ]
    eligible.sort(key=lambda c: (score_for_selection(c), len(support_samples_for_selection(c))), reverse=True)

    selected: list[dict[str, Any]] = []
    anchor_counts: Counter[str] = Counter()
    field_pair_counts: Counter[str] = Counter()
    uncertain_count = 0
    path_count = 0
    duplicate_seq = 0
    for candidate in eligible:
        if len(selected) >= max_tasks:
            candidate["selection_decision"] = "filtered_low_rank"
            candidate["selection_reason"] = "outside max_l6_tasks"
            continue
        anchor = candidate_anchor_id(candidate)
        group = field_pair_group(candidate)
        if anchor_counts[anchor] >= per_anchor_max:
            candidate["selection_decision"] = "filtered_anchor_quota"
            candidate["selection_reason"] = f"per_anchor_max_tasks={per_anchor_max}"
            continue
        if field_pair_counts[group] >= per_field_pair_max:
            candidate["selection_decision"] = "filtered_field_pair_quota"
            candidate["selection_reason"] = f"per_field_pair_max_tasks={per_field_pair_max}"
            continue
        if candidate.get("candidate_type") == "value_path" and path_count >= max_path_tasks:
            candidate["selection_decision"] = "filtered_low_rank"
            candidate["selection_reason"] = f"max_path_tasks={max_path_tasks}"
            continue
        prior = candidate.get("field_pair_prior", {})
        if prior.get("prior") == "uncertain" and uncertain_count >= uncertain_limit:
            candidate["selection_decision"] = "hold_uncertain_prior"
            candidate["selection_reason"] = f"include_uncertain_prior_limit={uncertain_limit}"
            continue
        near_duplicate = None
        for chosen in selected:
            if sample_jaccard(support_samples_for_selection(candidate), support_samples_for_selection(chosen)) >= jaccard_threshold:
                near_duplicate = chosen
                break
        if near_duplicate is not None:
            duplicate_seq += 1
            candidate["selection_decision"] = "filtered_near_duplicate"
            candidate["selection_reason"] = f"sample_ids jaccard >= {jaccard_threshold}"
            candidate["duplicate_group_id"] = f"dup_{duplicate_seq:04d}_{near_duplicate.get('l5_candidate_id')}"
            continue
        selected.append(candidate)
        anchor_counts[anchor] += 1
        field_pair_counts[group] += 1
        if prior.get("prior") == "uncertain":
            uncertain_count += 1
        if candidate.get("candidate_type") == "value_path":
            path_count += 1

    selected_ids = {c.get("l5_candidate_id") for c in selected}
    for candidate in all_candidates:
        if candidate.get("selection_decision") == "selected_top_k" and candidate.get("l5_candidate_id") not in selected_ids:
            candidate["selection_decision"] = "filtered_low_rank"
            candidate["selection_reason"] = "not selected after diversity constraints"
    return selected


def candidate_eval_tier(candidate: dict[str, Any]) -> str | None:
    if candidate_eval_block_reason(candidate):
        return None
    if candidate.get("candidate_type") == "value_path" and candidate.get("path_decision") != "pass_to_l6":
        return None
    selected_views = [
        (candidate.get("directional_metrics") or {}).get(direction, {})
        for direction in candidate.get("selected_directions", [])
    ]
    selected_views = [
        view for view in selected_views
        if view.get("eval_anchor_eligibility") == "eligible"
    ]
    if not selected_views and candidate.get("candidate_type") == "value_pair":
        return None
    if any(view.get("direction_decision") == "pass_refinement_component_direction" for view in selected_views):
        return "tier_2_usable_anchor"
    for view in selected_views:
        anchor_field = str(view.get("anchor_field") or "").lower()
        normal_rate = view.get("anchor_normal_value_rate", view.get("normal_value_rate"))
        # Direction views do not duplicate all normal stats under short names.
        if normal_rate is None:
            normal_rate = candidate.get("anchor_normal_value_rate") if view.get("direction") == "A_to_B" else candidate.get("target_normal_value_rate")
        lift = candidate.get("anchor_risk_normal_lift") if view.get("direction") == "A_to_B" else candidate.get("target_risk_normal_lift")
        if (
            view.get("direction_decision") == "pass_directional_relation"
            and normal_rate is not None
            and lift is not None
            and float(normal_rate) <= 0.1
            and float(lift) >= 5
            and "onerisk" not in anchor_field
            and "weapon_one_risk" not in anchor_field
        ):
            return "tier_2_usable_anchor"
    if any(view.get("anchor_quality_gate") in {"weak_anchor", "reject_as_anchor"} for view in selected_views):
        return "tier_3_exploration"
    if candidate.get("target_anchor_quality_gate") == "weak_anchor":
        return "tier_3_exploration"
    gate = candidate.get("anchor_quality_gate")
    prior = (candidate.get("field_pair_prior") or {}).get("prior")
    if gate == "preferred_anchor":
        return "tier_1_strong_anchor"
    if gate == "usable_anchor":
        return "tier_2_usable_anchor"
    if gate in {"weak_anchor", "unknown_normal_proxy_anchor"} or prior == "uncertain":
        return "tier_3_exploration"
    return "tier_3_exploration"


def select_candidate_eval_queue(pair_candidates: list[dict[str, Any]], path_candidates: list[dict[str, Any]], kb: dict[str, Any]) -> list[dict[str, Any]]:
    cfg = kb.get("top_k_selection", {}).get("candidate_eval_queue", {})
    max_tasks = int(cfg.get("max_candidate_eval_tasks", 250))
    min_score = float(cfg.get("min_candidate_eval_score", 25.0))
    per_anchor_max = int(cfg.get("per_anchor_max_tasks", 20))
    per_field_pair_max = int(cfg.get("per_field_pair_max_tasks", 60))
    jaccard_threshold = float(cfg.get("near_duplicate_jaccard_threshold", kb.get("top_k_selection", {}).get("near_duplicate_jaccard_threshold", 0.85)))
    tier_caps = {
        "tier_1_strong_anchor": int(cfg.get("tier_1_max_tasks", 100)),
        "tier_2_usable_anchor": int(cfg.get("tier_2_max_tasks", 120)),
        "tier_3_exploration": int(cfg.get("tier_3_max_tasks", 50)),
    }
    tier_order = {
        "tier_1_strong_anchor": 0,
        "tier_2_usable_anchor": 1,
        "tier_3_exploration": 2,
    }

    all_candidates = pair_candidates + path_candidates
    eligible: list[dict[str, Any]] = []
    for candidate in all_candidates:
        tier = candidate_eval_tier(candidate)
        if candidate.get("candidate_type") == "value_pair":
            candidate["candidate_eval_selected_directions"] = [
                direction
                for direction in candidate.get("selected_directions", [])
                if ((candidate.get("directional_metrics") or {}).get(direction, {})).get("eval_anchor_eligibility") == "eligible"
            ]
        candidate["candidate_eval_tier"] = tier
        candidate["candidate_eval_queue_decision"] = "not_eligible"
        candidate["candidate_eval_queue_reason"] = candidate_eval_block_reason(candidate) or "not selected for eval queue"
        if not tier:
            continue
        candidate["candidate_eval_score"] = score_for_candidate_eval(candidate)
        if candidate["candidate_eval_score"] < min_score:
            candidate["candidate_eval_queue_decision"] = "filtered_low_eval_score"
            candidate["candidate_eval_queue_reason"] = f"score below min_candidate_eval_score={min_score}"
            continue
        eligible.append(candidate)

    eligible.sort(
        key=lambda c: (
            tier_order.get(c.get("candidate_eval_tier"), 9),
            -score_for_candidate_eval(c),
            -len(support_samples_for_selection(c)),
        ),
    )

    selected: list[dict[str, Any]] = []
    anchor_counts: Counter[str] = Counter()
    field_pair_counts: Counter[str] = Counter()
    tier_counts: Counter[str] = Counter()
    deferred: list[dict[str, Any]] = []

    def try_select(candidate: dict[str, Any], enforce_tier_cap: bool = True) -> bool:
        if len(selected) >= max_tasks:
            candidate["candidate_eval_queue_decision"] = "filtered_eval_queue_limit"
            candidate["candidate_eval_queue_reason"] = f"max_candidate_eval_tasks={max_tasks}"
            return False
        anchor = candidate_anchor_id(candidate)
        group = field_pair_group(candidate)
        tier = str(candidate.get("candidate_eval_tier"))
        if anchor_counts[anchor] >= per_anchor_max:
            candidate["candidate_eval_queue_decision"] = "filtered_eval_anchor_quota"
            candidate["candidate_eval_queue_reason"] = f"candidate_eval per_anchor_max_tasks={per_anchor_max}"
            return False
        if field_pair_counts[group] >= per_field_pair_max:
            candidate["candidate_eval_queue_decision"] = "filtered_eval_field_pair_quota"
            candidate["candidate_eval_queue_reason"] = f"candidate_eval per_field_pair_max_tasks={per_field_pair_max}"
            return False
        if enforce_tier_cap and tier_counts[tier] >= tier_caps.get(tier, max_tasks):
            candidate["candidate_eval_queue_decision"] = "deferred_eval_tier_cap"
            candidate["candidate_eval_queue_reason"] = f"{tier} cap reached"
            deferred.append(candidate)
            return False
        duplicate_type, related, overlap = eval_queue_duplicate_relation(candidate, selected, jaccard_threshold)
        candidate["duplicate_related"] = False
        candidate["duplicate_related_to"] = None
        candidate["candidate_eval_jaccard_to_related"] = overlap
        if duplicate_type == "duplicate" and related is not None:
            candidate["candidate_eval_queue_decision"] = "filtered_eval_near_duplicate"
            candidate["candidate_eval_queue_reason"] = f"same anchor and same target family/path with sample_ids jaccard >= {jaccard_threshold}"
            candidate["duplicate_related"] = True
            candidate["duplicate_related_to"] = related.get("l5_candidate_id")
            return False
        if duplicate_type == "cross_family_overlap" and related is not None:
            candidate["duplicate_related"] = True
            candidate["duplicate_related_to"] = related.get("l5_candidate_id")
            candidate["candidate_eval_queue_reason"] = "cross_family_overlap_retained_for_eval"
        selected.append(candidate)
        anchor_counts[anchor] += 1
        field_pair_counts[group] += 1
        tier_counts[tier] += 1
        candidate["candidate_eval_queue_decision"] = "selected_candidate_eval_queue"
        if candidate.get("candidate_eval_queue_reason") != "cross_family_overlap_retained_for_eval":
            candidate["candidate_eval_queue_reason"] = "selected for Candidate Eval queue"
        return True

    for candidate in eligible:
        try_select(candidate, enforce_tier_cap=True)
    for candidate in deferred:
        if len(selected) >= max_tasks:
            break
        if candidate.get("candidate_eval_queue_decision") == "selected_candidate_eval_queue":
            continue
        try_select(candidate, enforce_tier_cap=False)
    for idx, candidate in enumerate(selected, 1):
        candidate["candidate_eval_rank"] = idx
    return selected


def candidate_eval_item_from_candidate(candidate: dict[str, Any], selected_direction: str | None = None) -> dict[str, Any]:
    item = l6_task_from_path(candidate) if candidate.get("candidate_type") == "value_path" else l6_task_from_pair(candidate)
    suffix = f"_{selected_direction}" if selected_direction else ""
    item["task_id"] = f"candidate_eval_{candidate['l5_candidate_id']}{suffix}"
    if selected_direction and candidate.get("candidate_type") == "value_pair":
        view = (candidate.get("directional_metrics") or {}).get(selected_direction, {})
        item["selected_direction"] = selected_direction
        item["primary_anchor_side"] = "original_A" if selected_direction == "A_to_B" else "original_B"
        item["relation_expression"] = direction_relation_expression(candidate, selected_direction)
        item["observed_metrics"] = direction_observed_metrics(candidate, selected_direction)
        item["direction_decision"] = view.get("direction_decision")
        item["direction_reason"] = view.get("direction_reason")
        item["value_path"] = [view.get("anchor_value"), view.get("target_value")]
        item["field_path_sequence"] = [view.get("anchor_field"), view.get("target_field")]
        item["conversion_metrics"]["pair_conversion_rate"] = view.get("directional_conversion")
        item["conversion_metrics"]["reverse_conversion_rate"] = view.get("reverse_conversion")
        item["anchor_score"] = view.get("anchor_score")
        item["next_node_score"] = view.get("next_node_score")
        item["anchor_quality_gate"] = view.get("anchor_quality_gate")
        item["target_anchor_quality_gate"] = view.get("target_anchor_quality_gate")
        item.update(anchor_unit_for_direction(candidate, selected_direction))
        item["original_order"] = {
            "original_A": candidate.get("field_path_sequence", [None, None])[0],
            "original_B": candidate.get("field_path_sequence", [None, None])[1],
            "original_A_to_B": (candidate.get("directional_metrics") or {}).get("A_to_B", {}).get("directional_conversion"),
            "original_B_to_A": (candidate.get("directional_metrics") or {}).get("B_to_A", {}).get("directional_conversion"),
        }
    item["candidate_eval_tier"] = candidate.get("candidate_eval_tier")
    item["candidate_eval_rank"] = candidate.get("candidate_eval_rank")
    item["candidate_eval_queue_decision"] = candidate.get("candidate_eval_queue_decision")
    item["candidate_eval_queue_reason"] = candidate.get("candidate_eval_queue_reason")
    item["candidate_eval_score"] = candidate.get("candidate_eval_score")
    item["duplicate_related"] = candidate.get("duplicate_related", False)
    item["duplicate_related_to"] = candidate.get("duplicate_related_to")
    item["candidate_eval_jaccard_to_related"] = candidate.get("candidate_eval_jaccard_to_related")
    item["strict_l6_selected"] = candidate.get("selection_decision") == "selected_top_k"
    item["eval_request"]["eval_target_type"] = "value_relation"
    return item


def held_or_drilldown_item_from_candidate(candidate: dict[str, Any], selected_direction: str) -> dict[str, Any]:
    item = candidate_eval_item_from_candidate(candidate, selected_direction)
    view = (candidate.get("directional_metrics") or {}).get(selected_direction, {})
    item["task_id"] = f"held_drilldown_{candidate['l5_candidate_id']}_{selected_direction}"
    item["candidate_eval_queue_decision"] = "held_or_drilldown"
    item["candidate_eval_queue_reason"] = view.get("held_or_drilldown_reason") or "anchor_unit_not_eligible_for_main_eval"
    item["held_or_drilldown_reason"] = view.get("held_or_drilldown_reason") or item.get("held_or_drilldown_reason")
    item["candidate_eval_tier"] = "held_or_drilldown"
    item["strict_l6_selected"] = False
    return item


def select_held_or_drilldown_queue(pair_candidates: list[dict[str, Any]], max_items: int = 300) -> list[dict[str, Any]]:
    held: list[dict[str, Any]] = []
    for candidate in pair_candidates:
        for direction in candidate.get("selected_directions", []):
            if direction in candidate.get("candidate_eval_selected_directions", []):
                continue
            view = (candidate.get("directional_metrics") or {}).get(direction, {})
            status = view.get("eval_anchor_eligibility")
            if status not in HELD_ANCHOR_STATUSES:
                continue
            anchor_family = field_family_for_path(str(view.get("anchor_field") or ""), str(view.get("anchor_field_key") or ""))
            normal_rate = view.get("anchor_normal_value_rate")
            if anchor_family in {"microphone_state", "lock_screen_state"}:
                continue
            if status == "need_finer_granularity" and normal_rate is not None and float(normal_rate) > 0.20:
                continue
            if view.get("direction_decision") not in PASS_DIRECTION_DECISIONS:
                continue
            held.append(held_or_drilldown_item_from_candidate(candidate, direction))
            if len(held) >= max_items:
                return held
    return held


def can_be_anchor_component(node: dict[str, Any]) -> bool:
    eligibility = anchor_eligibility_for_node(node)
    status = eligibility.get("status")
    key = str(node.get("field_key") or "")
    path = str(node.get("field_path") or "").lower()
    broad_component = status == "broad_anchor_hold" and (
        key in BROAD_ANCHOR_FIELD_KEYS or any(token in path for token in ["resolution", "battery", "camera"])
    )
    if status != "eligible" and not broad_component:
        return False
    reason = str(node.get("not_recommended_as_anchor_reason") or "")
    if any(token in reason for token in ["oneRisk_label", "label_or_post_action", "unique_id"]):
        return False
    if int(node.get("support_count") or 0) < 3 or node.get("role_suggestion") == "reject_node":
        return False
    if broad_component:
        return True
    return node.get("role_suggestion") != "confirming_node"


def can_be_evidence_node(node: dict[str, Any]) -> bool:
    if int(node.get("support_count") or 0) < 3:
        return False
    if node.get("role_suggestion") in {"reject_node", "reject_as_anchor"}:
        return False
    if field_family_proxy(str(node.get("field_key") or "")) == "unique_identifier":
        return False
    reason = str(node.get("not_recommended_as_anchor_reason") or "")
    return bool(reason) or node.get("role_suggestion") in {"confirming_node", "context_node", "next_node_candidate", "weak_anchor"}


def composite_relation_expression(record: dict[str, Any]) -> dict[str, Any]:
    components = record.get("anchor_components", [])
    evidence = record.get("evidence_nodes", [])
    return {
        "relation_type": "value_relation",
        "path_length": len(components) + len(evidence),
        "anchor_unit_type": record.get("anchor_unit_type"),
        "nodes": [
            {
                "role": "anchor_component",
                "field_path": item.get("field_path"),
                "value_or_pattern": item.get("value_or_pattern"),
            }
            for item in components
        ] + [
            {
                "role": "evidence_node",
                "field_path": item.get("field_path"),
                "value_or_pattern": item.get("value_or_pattern"),
            }
            for item in evidence
        ],
        "logic": [
            "CNT(anchor_component_1_AND_anchor_component_2) >= min_pair_support",
            "CNT(anchor_unit_AND_evidence_node) / CNT(anchor_unit) >= min_pair_conversion_rate",
        ],
    }


def build_composite_anchor_candidates(nodes: list[dict[str, Any]], kb: dict[str, Any], max_records: int = 100) -> list[dict[str, Any]]:
    min_support = int(kb.get("global_thresholds", {}).get("min_support_samples", 3))
    min_conversion = float(kb.get("global_thresholds", {}).get("min_pair_conversion_rate", 0.7))
    anchor_nodes = [node for node in nodes if can_be_anchor_component(node)]
    evidence_nodes = [node for node in nodes if can_be_evidence_node(node)]
    records: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for left, right in combinations(anchor_nodes, 2):
        if left.get("field_path") == right.get("field_path"):
            continue
        anchor_samples = set(left.get("risk_hit_sample_ids", [])) & set(right.get("risk_hit_sample_ids", []))
        if len(anchor_samples) < min_support:
            continue
        for evidence in evidence_nodes:
            if evidence.get("node_id") in {left.get("node_id"), right.get("node_id")}:
                continue
            full_samples = anchor_samples & set(evidence.get("risk_hit_sample_ids", []))
            if len(full_samples) < min_support:
                continue
            conversion = len(full_samples) / len(anchor_samples) if anchor_samples else 0.0
            if conversion < min_conversion:
                continue
            key = (str(left.get("node_id")), str(right.get("node_id")), str(evidence.get("node_id")))
            if key in seen:
                continue
            seen.add(key)
            components = [
                {"node_id": left.get("node_id"), "field_path": left.get("field_path"), "value_or_pattern": left.get("value_or_pattern"), "role": "anchor_component"},
                {"node_id": right.get("node_id"), "field_path": right.get("field_path"), "value_or_pattern": right.get("value_or_pattern"), "role": "refinement_component"},
            ]
            evidence_item = {"node_id": evidence.get("node_id"), "field_path": evidence.get("field_path"), "value_or_pattern": evidence.get("value_or_pattern"), "role": "evidence_node"}
            score = round(
                (float(left.get("anchor_score") or 0.0) + float(right.get("anchor_score") or 0.0)) * 0.22
                + float(evidence.get("next_node_score") or 0.0) * 0.22
                + conversion * 35.0
                + min(len(full_samples), 6) / 6 * 20.0,
                4,
            )
            record = {
                "task_id": f"candidate_eval_composite_anchor_{len(records)+1:05d}",
                "source_l5_candidate_id": f"composite_anchor_{len(records)+1:05d}",
                "candidate_type": "value_composite_anchor",
                "candidate_kind": "value_relation_candidate",
                "relation_level": "value_level",
                "anchor_unit": {
                    "anchor_unit_type": "composite_anchor",
                    "components": components,
                    "normal_joint_rate": None,
                    "normal_joint_rate_status": "need_hive_eval",
                },
                "anchor_unit_type": "composite_anchor",
                "anchor_components": components,
                "refinement_components": [components[1]],
                "evidence_nodes": [evidence_item],
                "relation_form": "composite_anchor_to_evidence",
                "field_path_sequence": [left.get("field_path"), right.get("field_path"), evidence.get("field_path")],
                "value_path": [left.get("value_or_pattern"), right.get("value_or_pattern"), evidence.get("value_or_pattern")],
                "support_sample_ids": sorted(full_samples),
                "support_count": len(full_samples),
                "conversion_metrics": {
                    "anchor_unit_support_count": len(anchor_samples),
                    "anchor_unit_to_evidence_conversion": conversion,
                    "relation_score": score,
                },
                "observed_metrics": {
                    "cnt_anchor_unit": len(anchor_samples),
                    "cnt_evidence": evidence.get("support_count"),
                    "cnt_anchor_unit_and_evidence": len(full_samples),
                    "conversion_evidence_over_anchor_unit": conversion,
                },
                "thresholds": {
                    "min_pair_support": min_support,
                    "min_pair_conversion_rate": min_conversion,
                    "threshold_source": "global",
                },
                "relation_expression": None,
                "eval_anchor_eligibility": "eligible",
                "drilldown_hint": None,
                "held_or_drilldown_reason": None,
                "overfit_risk": False,
                "normal_joint_rate": None,
                "normal_joint_rate_status": "need_hive_eval",
                "conditional_gain_audit": {
                    "conditional_gain_status": "not_applicable",
                    "reason": "composite_anchor_to_single_evidence",
                },
                "candidate_eval_tier": "tier_2_usable_anchor",
                "candidate_eval_queue_decision": "selected_candidate_eval_queue",
                "candidate_eval_queue_reason": "composite_anchor_unit_retained_for_eval",
                "candidate_eval_score": score,
                "strict_l6_selected": False,
                "evidence_boundary": EVIDENCE_BOUNDARY,
                "eval_request": eval_request(),
                "candidate_signal_level": "candidate_signal",
            }
            record["relation_expression"] = composite_relation_expression(record)
            records.append(record)
            if len(records) >= max_records:
                return records
    return records


def is_high_quality_anchor_node(node: dict[str, Any]) -> bool:
    entropy = node.get("normal_field_entropy_normalized")
    normal_rate = node.get("normal_value_rate")
    lift = node.get("risk_normal_lift")
    support = int(node.get("support_count") or 0)
    if entropy is None or normal_rate is None or lift is None:
        return False
    return float(entropy) >= 0.4 and float(normal_rate) <= 0.2 and float(lift) >= 3.0 and support >= 3


def build_anchor_funnel_audit(nodes: list[dict[str, Any]], pair_candidates: list[dict[str, Any]], selected: list[dict[str, Any]], eval_queue: list[dict[str, Any]]) -> dict[str, Any]:
    selected_anchor_ids = {candidate_anchor_id(c) for c in selected}
    eval_anchor_ids = {candidate_anchor_id(c) for c in eval_queue}
    pairs_by_anchor: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for pair in pair_candidates:
        pairs_by_anchor[candidate_anchor_id(pair)].append(pair)

    high_quality_rows = []
    for node in nodes:
        if not is_high_quality_anchor_node(node):
            continue
        related_pairs = pairs_by_anchor.get(node["node_id"], [])
        pass_pairs = [p for p in related_pairs if p.get("pair_decision") == "pass_to_path_expansion"]
        high_quality_rows.append({
            "node_id": node.get("node_id"),
            "field_path": node.get("field_path"),
            "value": node.get("value_or_pattern"),
            "anchor_score": node.get("anchor_score"),
            "anchor_quality_gate": node.get("anchor_quality_gate"),
            "normal_field_entropy_normalized": node.get("normal_field_entropy_normalized"),
            "normal_value_rate": node.get("normal_value_rate"),
            "risk_normal_lift": node.get("risk_normal_lift"),
            "support_count": node.get("support_count"),
            "related_pair_count": len(related_pairs),
            "pass_pair_count": len(pass_pairs),
            "in_strict_l6": node["node_id"] in selected_anchor_ids,
            "in_candidate_eval_queue": node["node_id"] in eval_anchor_ids,
            "likely_kill_reason": "retained_for_eval" if node["node_id"] in eval_anchor_ids else "no_pass_pair_or_filtered_by_selection",
        })

    return {
        "high_quality_anchor_node_count": len(high_quality_rows),
        "high_quality_anchor_in_strict_l6_count": sum(1 for r in high_quality_rows if r["in_strict_l6"]),
        "high_quality_anchor_in_candidate_eval_queue_count": sum(1 for r in high_quality_rows if r["in_candidate_eval_queue"]),
        "high_quality_anchor_missing_from_eval_count": sum(1 for r in high_quality_rows if not r["in_candidate_eval_queue"]),
        "high_quality_anchor_rows": high_quality_rows[:100],
    }


def build_candidate_reduction_summary(pair_candidates: list[dict[str, Any]], path_candidates: list[dict[str, Any]]) -> dict[str, Any]:
    all_candidates = pair_candidates + path_candidates
    anchor_gate_distribution = Counter(c.get("anchor_quality_gate") for c in pair_candidates)
    normal_gate_filtered = Counter()
    for c in pair_candidates:
        reason = c.get("anchor_quality_reason") or ""
        gate = c.get("anchor_quality_gate")
        if gate in {"weak_anchor", "reject_as_anchor"} and "normal_value_rate" in reason:
            normal_gate_filtered[reason] += 1
    return {
        "pair_decision_distribution": dict(Counter(c.get("pair_decision") for c in pair_candidates)),
        "strict_selection_distribution": dict(Counter(c.get("selection_decision") for c in all_candidates)),
        "candidate_eval_queue_distribution": dict(Counter(c.get("candidate_eval_queue_decision") for c in all_candidates)),
        "anchor_quality_gate_distribution": dict(anchor_gate_distribution),
        "normal_value_rate_gate_distribution": dict(normal_gate_filtered),
        "min_pair_score_filtered_count": sum(1 for c in all_candidates if c.get("selection_decision") == "filtered_low_score"),
        "uncertain_limit_filtered_count": sum(1 for c in all_candidates if c.get("selection_decision") == "hold_uncertain_prior"),
        "duplicate_suppression_filtered_count": sum(1 for c in all_candidates if c.get("selection_decision") == "filtered_near_duplicate"),
        "strict_duplicate_suppression_count": sum(1 for c in all_candidates if c.get("selection_decision") == "filtered_near_duplicate"),
        "strict_ineligible_anchor_filtered_count": sum(1 for c in all_candidates if c.get("selection_decision") == "filtered_strict_ineligible_anchor"),
        "eval_duplicate_suppression_count": sum(1 for c in all_candidates if c.get("candidate_eval_queue_decision") == "filtered_eval_near_duplicate"),
        "cross_family_overlap_retained_count": sum(1 for c in all_candidates if c.get("candidate_eval_queue_reason") == "cross_family_overlap_retained_for_eval"),
        "per_anchor_quota_filtered_count": sum(1 for c in all_candidates if c.get("selection_decision") == "filtered_anchor_quota"),
        "per_field_pair_quota_filtered_count": sum(1 for c in all_candidates if c.get("selection_decision") == "filtered_field_pair_quota"),
        "hard_reject_count": sum(1 for c in all_candidates if c.get("selection_decision") == "rejected_by_ranking"),
    }


def candidate_eval_tier_distribution(candidate_eval_tasks: list[dict[str, Any]]) -> dict[str, int]:
    counts = Counter(t.get("candidate_eval_tier") for t in candidate_eval_tasks)
    return {
        "tier_1_strong_anchor": counts.get("tier_1_strong_anchor", 0),
        "tier_2_usable_anchor": counts.get("tier_2_usable_anchor", 0),
        "tier_3_exploration": counts.get("tier_3_exploration", 0),
    }


def selected_task_id(candidate: dict[str, Any]) -> str:
    return f"l6_task_{candidate['l5_candidate_id']}"


def nodes_for_candidate(candidate: dict[str, Any], node_by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    node_ids = candidate.get("value_node_ids") or candidate.get("value_nodes") or []
    return [node_by_id[node_id] for node_id in node_ids if node_id in node_by_id]


def pattern_template_for(nodes: list[dict[str, Any]], candidate: dict[str, Any]) -> dict[str, Any] | None:
    keys = {node.get("field_key") for node in nodes}
    has_network = bool(keys & {"ip24", "asn", "isp"})
    has_device_model = "device_model" in keys
    has_environment = bool(keys & {"accessibility_service", "sensor", "cpu_arch", "device_model", "one_risk_label"})
    has_low_activity = any(is_low_activity_device_signal(node) for node in nodes)
    has_accessibility = "accessibility_service" in keys
    has_strategy = any(node.get("value_type") == "strategy_value" for node in nodes) or any(
        "policy" in node_text(node) or "strategy" in node_text(node) for node in nodes
    )
    has_packaging = any(is_registration_packaging_signal(node) for node in nodes)

    if has_network and has_device_model:
        return {
            "pattern_type": "network_anchor_device_concentration",
            "pattern_name": "低占比网络锚点 + 设备型号集中",
            "pattern_expression": {
                "anchor_role": "low_global_rate_network_anchor",
                "binding_role": "device_model_concentration",
                "pattern_logic": "anchor + binding",
            },
            "pattern_reason": "value-level 候选同时包含网络锚点和具体设备型号，适合后续验证是否存在网络空间内设备型号集中。",
            "abstracted_field_roles": ["network_anchor", "device_model_concentration"],
            "abstraction_confidence": "high",
        }
    if has_environment and has_low_activity:
        return {
            "pattern_type": "environment_anchor_low_activity_device",
            "pattern_name": "异常环境锚点 + 低活跃设备信号",
            "pattern_expression": {
                "anchor_role": "environment_anchor",
                "confirmation_role": "low_activity_device_signal",
                "pattern_logic": "anchor + optional_confirmation",
            },
            "pattern_reason": "value-level 候选包含设备/环境锚点和低活跃设备标签，适合后续验证该结构在偏白样本中的基线。",
            "abstracted_field_roles": ["environment_anchor", "low_activity_device_signal"],
            "abstraction_confidence": "medium",
        }
    if has_device_model and has_accessibility:
        return {
            "pattern_type": "device_environment_behavior_binding",
            "pattern_name": "设备环境集中 + 自动化/账号包装行为",
            "pattern_expression": {
                "anchor_role": "device_environment_signal",
                "binding_role": "automation_or_packaging_behavior",
                "pattern_logic": "environment + behavior_binding",
            },
            "pattern_reason": "value-level 候选包含具体设备环境和无障碍服务类行为线索，适合后续验证是否为自动化/包装行为结构。",
            "abstracted_field_roles": ["device_environment_signal", "behavior_binding"],
            "abstraction_confidence": "medium",
        }
    if has_strategy and has_environment:
        return {
            "pattern_type": "strategy_signal_environment_binding",
            "pattern_name": "策略弱信号 + 环境共性绑定",
            "pattern_expression": {
                "anchor_role": "weak_strategy_signal",
                "binding_role": "device_or_network_environment",
                "pattern_logic": "weak_signal + environment_binding",
            },
            "pattern_reason": "value-level 候选包含策略弱信号和环境字段，适合后续验证是否只是后验标签或真实环境绑定。",
            "abstracted_field_roles": ["weak_strategy_signal", "environment_binding"],
            "abstraction_confidence": "low",
        }
    if has_packaging:
        return {
            "pattern_type": "account_packaging_after_registration",
            "pattern_name": "注册后短时账号包装行为",
            "pattern_expression": {
                "pattern_type": "account_packaging_after_registration",
                "required_roles": ["behavior_packaging_signal"],
                "optional_roles": ["device_environment_signal", "weak_strategy_signal"],
            },
            "pattern_reason": "value-level 候选包含注册/资料包装相关字段，适合后续验证短时账号包装模式。",
            "abstracted_field_roles": ["behavior_packaging_signal"],
            "abstraction_confidence": "medium" if len(nodes) >= 2 else "low",
        }
    if candidate.get("structure_interpretation") == "uncertain_structure":
        return None
    return None


def pattern_relation_expression(template: dict[str, Any]) -> dict[str, Any]:
    roles = template.get("abstracted_field_roles", [])
    nodes = [
        {"role": chr(ord("A") + idx), "abstract_role": role}
        for idx, role in enumerate(roles[:4])
    ]
    path_length = len(nodes)
    if path_length <= 2:
        logic = [
            "CNT(A_AND_B) >= min_pair_support",
            "CNT(A_AND_B) / CNT(A) >= min_pair_conversion_rate",
        ]
    else:
        full = "_AND_".join(chr(ord("A") + idx) for idx in range(path_length))
        previous = "_AND_".join(chr(ord("A") + idx) for idx in range(path_length - 1))
        logic = [
            f"CNT({full}) >= min_path_support",
            f"CNT({full}) / CNT({previous}) >= min_next_hop_conversion_rate",
        ]
    return {
        "relation_type": "pattern_relation",
        "path_length": path_length,
        "nodes": nodes,
        "logic": logic,
    }


def pattern_observed_metrics(candidate: dict[str, Any]) -> dict[str, Any]:
    if candidate.get("candidate_type") == "value_pair":
        return pair_observed_metrics(candidate)
    if candidate.get("candidate_type") == "value_path":
        return path_observed_metrics(candidate)
    return {}


def pattern_thresholds(candidate: dict[str, Any]) -> dict[str, Any]:
    if candidate.get("candidate_type") == "value_pair":
        return pair_thresholds(candidate)
    if candidate.get("candidate_type") == "value_path":
        return path_thresholds(candidate)
    return {}


def build_pattern_candidates(selected: list[dict[str, Any]], nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    node_by_id = {node["node_id"]: node for node in nodes}
    patterns: list[dict[str, Any]] = []
    seen: set[tuple[str, tuple[str, ...]]] = set()
    for candidate in selected:
        candidate_nodes = nodes_for_candidate(candidate, node_by_id)
        if not candidate_nodes:
            continue
        template = pattern_template_for(candidate_nodes, candidate)
        if not template:
            continue
        source_value_candidate_ids = [str(node.get("source_candidate_id")) for node in candidate_nodes]
        dedupe_key = (template["pattern_type"], tuple(sorted(source_value_candidate_ids)))
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        support_sample_ids = support_samples_for_selection(candidate)
        support_count = len(set(support_sample_ids))
        in_sample_hit_rate = support_count / 6 if support_count else 0.0
        score = score_for_selection(candidate)
        confidence_bonus = {"high": 10.0, "medium": 5.0, "low": 0.0}.get(template["abstraction_confidence"], 0.0)
        pattern_score = round(score * 0.7 + support_count * 5.0 + confidence_bonus, 4)
        pattern_id = f"pattern_{len(patterns)+1:04d}_{template['pattern_type']}"
        patterns.append({
            "pattern_candidate_id": pattern_id,
            "candidate_kind": "pattern_relation_candidate",
            "relation_level": "pattern_level",
            "pattern_type": template["pattern_type"],
            "pattern_name": template["pattern_name"],
            "baseline_mode": candidate.get("baseline_mode"),
            "strategy_draft_type": candidate.get("strategy_draft_type"),
            "requires_l6_replay": True,
            "l6_replay_required_reason": L6_REPLAY_REQUIRED_REASON,
            "source_value_candidate_ids": source_value_candidate_ids,
            "source_task_ids": [selected_task_id(candidate)],
            "source_l5_candidate_ids": [candidate.get("l5_candidate_id")],
            "source_field_paths": [node.get("field_path") for node in candidate_nodes],
            "abstracted_field_roles": template["abstracted_field_roles"],
            "pattern_expression": template["pattern_expression"],
            "relation_expression": pattern_relation_expression(template),
            "observed_metrics": pattern_observed_metrics(candidate),
            "thresholds": pattern_thresholds(candidate),
            "pattern_reason": template["pattern_reason"],
            "support_sample_ids": sorted(set(support_sample_ids)),
            "support_count": support_count,
            "in_sample_hit_rate": in_sample_hit_rate,
            "pattern_score": pattern_score,
            "abstraction_confidence": template["abstraction_confidence"],
            "evidence_boundary": PATTERN_EVIDENCE_BOUNDARY,
            "eval_request": pattern_eval_request(),
            "candidate_signal_level": "candidate_signal",
        })
    return patterns


def l6_task_from_pair(pair: dict[str, Any]) -> dict[str, Any]:
    primary_direction = pair.get("primary_direction") or "A_to_B"
    anchor_unit = anchor_unit_for_direction(pair, primary_direction)
    return {
        "task_id": selected_task_id(pair),
        "source_l5_candidate_id": pair["l5_candidate_id"],
        "candidate_type": "value_pair",
        "candidate_kind": "value_relation_candidate",
        "relation_level": "value_level",
        "baseline_mode": pair.get("baseline_mode"),
        "strategy_draft_type": pair.get("strategy_draft_type"),
        "total_feature_count": pair.get("total_feature_count"),
        "discovery_only_count": pair.get("discovery_only_count"),
        "baseline_supported_count": pair.get("baseline_supported_count"),
        "experimental_strategy_bounds": pair.get("experimental_strategy_bounds"),
        "requires_l6_replay": True,
        "l6_replay_required_reason": L6_REPLAY_REQUIRED_REASON,
        "feature_names": pair.get("feature_names"),
        "feature_types": pair.get("feature_types"),
        "value_types": pair.get("value_types"),
        "feature_definitions": pair.get("feature_definitions"),
        "bucket_labels": pair.get("bucket_labels"),
        "bucket_ranges": pair.get("bucket_ranges"),
        "risk_hit_rates": pair.get("risk_hit_rates"),
        "commonality_families": pair.get("commonality_families"),
        "commonality_evidence": pair.get("commonality_evidence"),
        "source_candidate_ids": pair.get("source_candidate_ids"),
        "relation_expression": pair.get("relation_expression"),
        "directional_metrics": pair.get("directional_metrics"),
        "selected_directions": pair.get("selected_directions"),
        "primary_direction": pair.get("primary_direction"),
        "relation_strength": pair.get("relation_strength"),
        "observed_metrics": pair.get("observed_metrics"),
        "thresholds": pair.get("thresholds"),
        "value_path": pair["value_path"],
        "field_path_sequence": pair["field_path_sequence"],
        "support_sample_ids": pair["shared_sample_ids"],
        "support_count": pair["shared_support_count"],
        "conversion_metrics": {
            "pair_conversion_rate": pair["pair_conversion_rate"],
            "reverse_conversion_rate": pair["reverse_conversion_rate"],
            "pair_score": pair.get("pair_score"),
            "relation_score": pair.get("relation_score"),
            "pair_rank": pair.get("pair_rank"),
            "path_gain": pair.get("path_gain"),
            "anchor_score_component": pair.get("anchor_score_component"),
            "next_node_score_component": pair.get("next_node_score_component"),
        },
        "anchor_score": pair.get("anchor_score"),
        "next_node_score": pair.get("next_node_score"),
        "anchor_role": pair.get("anchor_role"),
        "target_role": pair.get("target_role"),
        "anchor_quality_gate": pair.get("anchor_quality_gate"),
        "anchor_quality_reason": pair.get("anchor_quality_reason"),
        "target_anchor_quality_gate": pair.get("target_anchor_quality_gate"),
        "target_anchor_quality_reason": pair.get("target_anchor_quality_reason"),
        "anchor_field_role_source": pair.get("anchor_field_role_source"),
        "target_field_role_source": pair.get("target_field_role_source"),
        "anchor_normal_field_entropy": pair.get("anchor_normal_field_entropy"),
        "anchor_normal_value_rate": pair.get("anchor_normal_value_rate"),
        "anchor_risk_normal_lift": pair.get("anchor_risk_normal_lift"),
        "target_normal_field_entropy": pair.get("target_normal_field_entropy"),
        "target_normal_value_rate": pair.get("target_normal_value_rate"),
        "target_risk_normal_lift": pair.get("target_risk_normal_lift"),
        "anchor_not_recommended_reason": pair.get("anchor_not_recommended_reason"),
        "field_pair_prior_summary": pair["field_pair_prior"],
        "natural_relation_guard_summary": pair["natural_relation_guard"],
        "granularity_check_summary": pair["value_granularity_check"],
        "threshold_source": pair["threshold_source"],
        "threshold_values": pair["threshold_values"],
        "selection_decision": pair.get("selection_decision"),
        "selection_reason": pair.get("selection_reason"),
        "diversity_group": pair.get("diversity_group"),
        "role_in_path": pair.get("role_in_path"),
        **anchor_unit,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "eval_request": eval_request(),
        "in_sample_only_metrics": {
            "global_value_rate": None,
            "white_value_rate": None,
            "risk_white_lift": None,
            "temporal_stability_score": None,
            "historical_recall_score": None,
            "true_precision_proxy": None,
        },
        "recommended_l6_checks": [
            "check_normal_baseline_again",
            "check_false_positive_risk",
            "check_business_semantic_reason",
            "check_strategy_action_feasibility",
            "check_historical_replay_if_available",
            "check_manual_review_sample",
        ],
        "related_pattern_candidate_ids": [],
        "candidate_signal_level": "candidate_signal",
    }


def l6_task_from_path(path: dict[str, Any]) -> dict[str, Any]:
    fields = path.get("field_path_sequence", [])
    values = path.get("value_sequence", [])
    anchor_component = {
        "field_path": fields[0] if fields else None,
        "value_or_pattern": values[0] if values else None,
        "role": "anchor_component",
    }
    evidence_nodes = [
        {"field_path": field, "value_or_pattern": values[idx] if idx < len(values) else None, "role": "evidence_node"}
        for idx, field in enumerate(fields[1:], 1)
    ]
    return {
        "task_id": selected_task_id(path),
        "source_l5_candidate_id": path["l5_candidate_id"],
        "candidate_type": "value_path",
        "candidate_kind": "value_relation_candidate",
        "relation_level": "value_level",
        "baseline_mode": path.get("baseline_mode"),
        "strategy_draft_type": path.get("strategy_draft_type"),
        "total_feature_count": path.get("total_feature_count"),
        "discovery_only_count": path.get("discovery_only_count"),
        "baseline_supported_count": path.get("baseline_supported_count"),
        "experimental_strategy_bounds": path.get("experimental_strategy_bounds"),
        "requires_l6_replay": True,
        "l6_replay_required_reason": L6_REPLAY_REQUIRED_REASON,
        "feature_names": path.get("feature_names"),
        "feature_types": path.get("feature_types"),
        "value_types": path.get("value_types"),
        "feature_definitions": path.get("feature_definitions"),
        "bucket_labels": path.get("bucket_labels"),
        "bucket_ranges": path.get("bucket_ranges"),
        "risk_hit_rates": path.get("risk_hit_rates"),
        "commonality_families": path.get("commonality_families"),
        "commonality_evidence": path.get("commonality_evidence"),
        "source_candidate_ids": path.get("source_candidate_ids"),
        "relation_expression": path.get("relation_expression"),
        "observed_metrics": path.get("observed_metrics"),
        "thresholds": path.get("thresholds"),
        "value_path": path["value_sequence"],
        "field_path_sequence": path["field_path_sequence"],
        "support_sample_ids": path["support_sample_ids"],
        "support_count": path["support_count"],
        "conversion_metrics": {
            "layer_conversion_rates": path["layer_conversion_rates"],
            "min_layer_conversion_rate": path["min_layer_conversion_rate"],
            "path_score": path.get("path_score"),
            "path_rank": path.get("path_rank"),
            "incremental_path_gain": path.get("incremental_path_gain"),
        },
        "field_pair_prior_summary": "see_l5_execution_candidates",
        "natural_relation_guard_summary": "see_l5_execution_candidates",
        "granularity_check_summary": "see_l5_execution_candidates",
        "threshold_source": "see_l5_execution_candidates",
        "selection_decision": path.get("selection_decision"),
        "selection_reason": path.get("selection_reason"),
        "diversity_group": path.get("diversity_group"),
        "role_in_path": path.get("role_in_path"),
        "anchor_unit": {
            "anchor_unit_type": "atomic_anchor",
            "components": [anchor_component],
            "normal_joint_rate": None,
            "normal_joint_rate_status": "not_available_for_path",
        },
        "anchor_unit_type": "atomic_anchor",
        "anchor_components": [anchor_component],
        "refinement_components": [],
        "evidence_nodes": evidence_nodes,
        "relation_form": "atomic_anchor_to_evidence_chain",
        "eval_anchor_eligibility": None,
        "drilldown_hint": None,
        "held_or_drilldown_reason": None,
        "overfit_risk": len(fields) > 3,
        "normal_joint_rate": None,
        "normal_joint_rate_status": "need_hive_eval",
        "conditional_gain_audit": path.get("conditional_gain_audit"),
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "eval_request": eval_request(),
        "in_sample_only_metrics": {
            "global_value_rate": None,
            "white_value_rate": None,
            "risk_white_lift": None,
            "temporal_stability_score": None,
            "historical_recall_score": None,
            "true_precision_proxy": None,
        },
        "recommended_l6_checks": [
            "check_normal_baseline_again",
            "check_false_positive_risk",
            "check_business_semantic_reason",
            "check_strategy_action_feasibility",
            "check_historical_replay_if_available",
            "check_manual_review_sample",
        ],
        "related_pattern_candidate_ids": [],
        "candidate_signal_level": "candidate_signal",
    }


def build_prior_seed_input(nodes: list[dict[str, Any]], pairs: list[dict[str, Any]], kb: dict[str, Any], normal_baseline: dict[str, Any] | None) -> dict[str, Any]:
    unique_fields = []
    seen_fields = set()
    for node in nodes:
        field_path = node.get("field_path")
        if field_path in seen_fields:
            continue
        seen_fields.add(field_path)
        unique_fields.append({
            "field_path": field_path,
            "field_key": node.get("field_key"),
            "field_role_source": node.get("field_role_source"),
            "normal_field_distinct_count": node.get("normal_field_distinct_count"),
            "normal_field_entropy": node.get("normal_field_entropy"),
            "normal_baseline_status": node.get("normal_baseline_status"),
            "sample_values": [node.get("value_or_pattern")],
        })
    unique_pairs = []
    seen_pairs = set()
    for pair in pairs:
        key = tuple(pair.get("field_path_sequence", []))
        if key in seen_pairs:
            continue
        seen_pairs.add(key)
        unique_pairs.append({
            "field_path_sequence": list(key),
            "field_key_sequence": [pair.get("anchor_field"), pair.get("target_field")],
            "prior": pair.get("field_pair_prior", {}).get("prior"),
            "judgement_source": pair.get("field_pair_prior", {}).get("judgement_source"),
        })
    return {
        "purpose": "batch_prior_seed_for_l5_overlay",
        "llm_runtime_policy": "offline_batch_only_do_not_call_llm_in_l5_main_loop",
        "unique_field_list": unique_fields,
        "unique_field_pair_list": unique_pairs,
        "normal_baseline_status": (normal_baseline or {}).get("normal_baseline_status", "missing"),
        "existing_knowledge_base_summary": {
            "field_pair_prior_count": len(kb.get("field_pair_prior_config", [])),
            "natural_relation_count": len(kb.get("natural_determination_map", [])),
        },
        "overlay_output_schema": {
            "field_family_map": [],
            "field_pair_prior_seed_library": [],
            "natural_relation_seed_library": [],
            "leakage_field_map": [],
            "over_general_field_map": [],
            "unique_id_field_map": [],
            "field_role_map": [],
        },
    }


def build_promotion_candidates(nodes: list[dict[str, Any]], selected: list[dict[str, Any]], kb: dict[str, Any]) -> list[dict[str, Any]]:
    promotions: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for node in nodes:
        if node.get("field_role_source") == "base_kb" and node.get("anchor_quality_gate") in {"preferred_anchor", "reject_as_anchor"}:
            key = ("field_prior", node.get("field_path", ""))
            if key in seen:
                continue
            seen.add(key)
            promotions.append({
                "promotion_type": "field_prior",
                "source": "static_seed",
                "candidate": {
                    "scope": "field",
                    "field_path": node.get("field_path"),
                    "judgement": node.get("role_suggestion"),
                    "confidence": "medium",
                    "judgement_source": "static_seed",
                    "need_human_review": True,
                },
                "reason": "Field role was useful in L5 scoring; human review required before long-term KB promotion.",
                "required_review": "human_review",
                "promotion_decision": "pending",
            })
    for candidate in selected:
        prior = candidate.get("field_pair_prior", {})
        if prior.get("scope") == "value_relation":
            promotions.append({
                "promotion_type": "value_relation_prior",
                "source": prior.get("judgement_source", "human_seed"),
                "candidate": {
                    "scope": "value_relation",
                    "field_path_sequence": candidate.get("field_path_sequence"),
                    "value_path": candidate.get("value_path"),
                    "prior": prior.get("value_relation_prior"),
                    "recommended_usage": prior.get("recommended_usage"),
                    "confidence": prior.get("confidence"),
                    "need_human_review": True,
                },
                "reason": "Run-level value prior matched selected relation; keep run-level until repeated runs or Candidate Eval confirms.",
                "required_review": "candidate_eval",
                "promotion_decision": "pending",
            })
        elif prior.get("scope") == "field_pair" and prior.get("confidence") == "high":
            promotions.append({
                "promotion_type": "field_pair_prior",
                "source": prior.get("judgement_source", "field_prior_kb"),
                "candidate": {
                    "scope": "field_pair",
                    "field_path_sequence": candidate.get("field_path_sequence"),
                    "judgement": prior.get("prior"),
                    "confidence": prior.get("confidence"),
                    "need_human_review": prior.get("need_human_review", True),
                },
                "reason": "High-confidence field-pair prior affected selected relation; review before permanent KB update.",
                "required_review": "human_review",
                "promotion_decision": "pending",
            })
    return promotions


def overlay_example() -> dict[str, Any]:
    return {
        "field_family_map": [
            {
                "field_path": "weapon_android.raw_data.accessibilityServiceList",
                "judgement": "accessibility_environment_signal",
                "confidence": "medium",
                "judgement_source": "static_seed",
                "reason": "Accessibility service list is an environment/automation-related field family.",
                "need_human_review": True,
            }
        ],
        "field_pair_prior_seed_library": [
            {
                "anchor_field": "weapon_android.raw_data.accessibilityServiceList",
                "target_field": "weapon_android.weapon_one_risk",
                "prior": "normally_weak_related",
                "confidence": "medium",
                "judgement_source": "static_seed",
                "reason": "Accessibility environment and oneRisk labels are not natural deterministic fields; review required.",
                "need_human_review": True,
            }
        ],
        "natural_relation_seed_library": [],
        "leakage_field_map": [],
        "over_general_field_map": [
            {
                "field_path": "weapon_android.raw_data.resolution",
                "judgement": "over_general_profile_context",
                "confidence": "medium",
                "judgement_source": "static_seed",
                "reason": "Resolution is commonly a broad device profile context field.",
                "need_human_review": True,
            }
        ],
        "unique_id_field_map": [],
        "field_role_map": [
            {
                "field_path": "weapon_android.weapon_one_risk",
                "judgement": "weak_risk_signal_or_confirming_node",
                "confidence": "medium",
                "judgement_source": "static_seed",
                "reason": "oneRisk labels are factual/risk-adjacent labels and should not automatically be primary anchors.",
                "need_human_review": True,
            }
        ],
    }


def run_l5(l4_review_candidates: list[dict[str, Any]], kb: dict[str, Any], normal_baseline: dict[str, Any] | None = None) -> dict[str, Any]:
    nodes, violations = build_value_nodes(l4_review_candidates)
    nodes = rank_value_nodes(nodes, kb, normal_baseline)
    indexes = build_inverted_indexes(nodes)
    pairs = build_pair_candidates(nodes, kb)
    seen_granularity_violations: set[tuple[str, str]] = set()
    for pair in pairs:
        for check in pair.get("value_granularity_check", []):
            if check.get("status") not in {"missing_value", "too_coarse"}:
                continue
            key = (check.get("node_id", ""), check.get("status", ""))
            if key in seen_granularity_violations:
                continue
            seen_granularity_violations.add(key)
            node = next((n for n in nodes if n["node_id"] == check.get("node_id")), {})
            violations.append({
                "candidate_id": node.get("source_candidate_id"),
                "violation_type": f"bad_granularity_{check.get('status')}",
                "field_path": node.get("field_path"),
                "value_or_pattern": node.get("value_or_pattern"),
                "reason": check.get("reason"),
            })
    paths = expand_paths(pairs, nodes, kb)
    selected = select_top_k(pairs, paths, kb)
    candidate_eval_queue = select_candidate_eval_queue(pairs, paths, kb)
    held_or_drilldown_queue = select_held_or_drilldown_queue(pairs)
    composite_anchor_candidates: list[dict[str, Any]] = []
    pattern_candidates = build_pattern_candidates(selected, nodes)
    pair_tasks = [l6_task_from_pair(p) for p in selected if p.get("candidate_type") == "value_pair"]
    path_tasks = [l6_task_from_path(p) for p in selected if p.get("candidate_type") == "value_path"]
    tasks = pair_tasks + path_tasks
    candidate_eval_tasks = []
    for candidate in candidate_eval_queue:
        if candidate.get("candidate_type") == "value_pair":
            directions = candidate.get("candidate_eval_selected_directions") or [candidate.get("primary_direction") or "A_to_B"]
            for direction in directions:
                candidate_eval_tasks.append(candidate_eval_item_from_candidate(candidate, direction))
        else:
            candidate_eval_tasks.append(candidate_eval_item_from_candidate(candidate))
    max_eval_tasks = int(kb.get("top_k_selection", {}).get("candidate_eval_queue", {}).get("max_candidate_eval_tasks", 300))
    remaining_eval_slots = max(0, max_eval_tasks - len(candidate_eval_tasks))
    if remaining_eval_slots:
        composite_anchor_candidates = build_composite_anchor_candidates(nodes, kb, max_records=min(100, remaining_eval_slots))
    candidate_eval_tasks.extend(composite_anchor_candidates)
    patterns_by_task: defaultdict[str, list[str]] = defaultdict(list)
    for pattern in pattern_candidates:
        for task_id in pattern.get("source_task_ids", []):
            patterns_by_task[task_id].append(pattern["pattern_candidate_id"])
    for task in tasks:
        task["related_pattern_candidate_ids"] = patterns_by_task.get(task["task_id"], [])
    promotion_candidates = build_promotion_candidates(nodes, selected, kb)
    selected_priors = [c.get("field_pair_prior", {}) for c in selected]
    candidate_reduction_summary = build_candidate_reduction_summary(pairs, paths)
    anchor_funnel_audit = build_anchor_funnel_audit(nodes, pairs, selected, candidate_eval_queue)
    eval_tier_distribution = candidate_eval_tier_distribution(candidate_eval_tasks)
    summary = {
        "input_l4_review_candidate_count": len(l4_review_candidates),
        "value_node_count": len(nodes),
        "contract_violation_count": len(violations),
        "pair_candidate_count": len(pairs),
        "pair_decision_distribution": dict(Counter(p["pair_decision"] for p in pairs)),
        "pair_selection_distribution": dict(Counter(p.get("selection_decision") for p in pairs)),
        "path_candidate_count": len(paths),
        "path_decision_distribution": dict(Counter(p["path_decision"] for p in paths)),
        "path_selection_distribution": dict(Counter(p.get("selection_decision") for p in paths)),
        "conditional_gain_status_distribution": dict(Counter((p.get("conditional_gain_audit") or {}).get("conditional_gain_status", "not_applicable") for p in paths)),
        "selected_top_k_count": len(selected),
        "selected_value_relation_candidate_count": len(selected),
        "l6_task_count": len(tasks),
        "candidate_eval_queue_count": len(candidate_eval_tasks),
        "held_or_drilldown_queue_count": len(held_or_drilldown_queue),
        "atomic_anchor_count": sum(1 for task in candidate_eval_tasks if task.get("anchor_unit_type") == "atomic_anchor"),
        "composite_anchor_count": sum(1 for task in candidate_eval_tasks if task.get("anchor_unit_type") == "composite_anchor"),
        "three_component_anchor_count": sum(1 for task in candidate_eval_tasks if task.get("anchor_unit_type") == "three_component_anchor"),
        "broad_anchor_hold_count": sum(1 for task in held_or_drilldown_queue if task.get("eval_anchor_eligibility") == "broad_anchor_hold"),
        "need_finer_granularity_count": sum(1 for task in held_or_drilldown_queue if task.get("eval_anchor_eligibility") == "need_finer_granularity"),
        "overfit_risk_count": sum(1 for task in candidate_eval_tasks + held_or_drilldown_queue if task.get("overfit_risk")),
        "candidate_eval_tier_distribution": eval_tier_distribution,
        "forward_direction_selected_count": sum(1 for task in candidate_eval_tasks if task.get("selected_direction") == "A_to_B"),
        "reverse_direction_selected_count": sum(1 for task in candidate_eval_tasks if task.get("selected_direction") == "B_to_A"),
        "bidirectional_relation_count": sum(1 for c in candidate_eval_queue if c.get("relation_strength") == "bidirectional"),
        "refinement_component_direction_count": sum(1 for task in candidate_eval_tasks if task.get("direction_decision") == "pass_refinement_component_direction"),
        "hold_low_conversion_rescued_count": sum(
            1 for c in candidate_eval_queue
            if c.get("pair_decision") == "hold_low_conversion" and c.get("selected_directions")
        ),
        "strict_duplicate_suppression_count": candidate_reduction_summary["strict_duplicate_suppression_count"],
        "eval_duplicate_suppression_count": candidate_reduction_summary["eval_duplicate_suppression_count"],
        "cross_family_overlap_retained_count": candidate_reduction_summary["cross_family_overlap_retained_count"],
        "pattern_candidate_count": len(pattern_candidates),
        "pattern_relation_candidate_count": len(pattern_candidates),
        "pattern_type_distribution": dict(Counter(p["pattern_type"] for p in pattern_candidates)),
        "normal_baseline_status": (normal_baseline or {}).get("normal_baseline_status", "missing"),
        "normal_baseline_field_count": (normal_baseline or {}).get("field_count"),
        "prior_overlay_status": "loaded" if any((kb.get("_prior_overlay") or {}).get(k) for k in ["field_pair_prior_seed_library", "field_role_map", "leakage_field_map", "over_general_field_map", "unique_id_field_map"]) else "missing",
        "field_prior_kb_status": "loaded" if any((kb.get("_field_prior_kb") or {}).get(k) for k in ["field_pair_prior", "field_role_map", "leakage_field_map", "over_general_field_map", "unique_id_field_map"]) else "missing",
        "value_relation_overlay_status": "loaded" if (kb.get("_value_relation_overlay") or {}).get("value_relation_prior_overlay") else "missing",
        "value_relation_overlay_hit_count": sum(1 for p in selected_priors if p.get("scope") == "value_relation"),
        "field_level_prior_hit_count": sum(1 for p in selected_priors if p.get("scope") == "field_pair" or p.get("judgement_source") in {"config", "field_prior_kb", "static_seed", "human_seed"}),
        "selected_uncertain_prior_count": sum(1 for p in selected_priors if p.get("prior") == "uncertain"),
        "candidate_eval_uncertain_prior_count": sum(1 for c in candidate_eval_queue if (c.get("field_pair_prior") or {}).get("prior") == "uncertain"),
        "promotion_candidate_count": len(promotion_candidates),
        "overlay_need_human_review_count": sum(
            1
            for values in (kb.get("_prior_overlay") or {}).values()
            if isinstance(values, list)
            for item in values
            if isinstance(item, dict) and item.get("need_human_review")
        ),
        "candidate_signal_level": "candidate_signal",
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "pattern_evidence_boundary": PATTERN_EVIDENCE_BOUNDARY,
        "candidate_reduction_summary": candidate_reduction_summary,
        "anchor_funnel_audit_summary": {
            k: v for k, v in anchor_funnel_audit.items() if k != "high_quality_anchor_rows"
        },
    }
    return {
        "value_nodes": nodes,
        "inverted_indexes": indexes,
        "pair_candidates": pairs,
        "path_candidates": paths,
        "composite_anchor_candidates": composite_anchor_candidates,
        "pattern_candidates": pattern_candidates,
        "l6_tasks": tasks,
        "candidate_eval_queue": candidate_eval_tasks,
        "held_or_drilldown_queue": held_or_drilldown_queue,
        "contract_violations": violations,
        "prior_seed_input": build_prior_seed_input(nodes, pairs, kb, normal_baseline),
        "promotion_candidates": promotion_candidates,
        "anchor_funnel_audit": anchor_funnel_audit,
        "candidate_reduction_summary": candidate_reduction_summary,
        "summary": summary,
    }


def build_summary_md(result: dict[str, Any]) -> str:
    summary = result["summary"]
    lines = [
        "# L5 Relation Candidate Generation Summary",
        "",
        f"- input_l4_review_candidate_count: {summary['input_l4_review_candidate_count']}",
        f"- value_node_count: {summary['value_node_count']}",
        f"- contract_violation_count: {summary['contract_violation_count']}",
        f"- pair_candidate_count: {summary['pair_candidate_count']}",
        f"- path_candidate_count: {summary['path_candidate_count']}",
        f"- selected_top_k_count: {summary['selected_top_k_count']}",
        f"- selected_value_relation_candidate_count: {summary['selected_value_relation_candidate_count']}",
        f"- l6_task_count: {summary['l6_task_count']}",
        f"- candidate_eval_queue_count: {summary['candidate_eval_queue_count']}",
        f"- held_or_drilldown_queue_count: {summary['held_or_drilldown_queue_count']}",
        f"- atomic_anchor_count: {summary['atomic_anchor_count']}",
        f"- composite_anchor_count: {summary['composite_anchor_count']}",
        f"- three_component_anchor_count: {summary['three_component_anchor_count']}",
        f"- broad_anchor_hold_count: {summary['broad_anchor_hold_count']}",
        f"- need_finer_granularity_count: {summary['need_finer_granularity_count']}",
        f"- overfit_risk_count: {summary['overfit_risk_count']}",
        f"- forward_direction_selected_count: {summary['forward_direction_selected_count']}",
        f"- reverse_direction_selected_count: {summary['reverse_direction_selected_count']}",
        f"- bidirectional_relation_count: {summary['bidirectional_relation_count']}",
        f"- refinement_component_direction_count: {summary['refinement_component_direction_count']}",
        f"- hold_low_conversion_rescued_count: {summary['hold_low_conversion_rescued_count']}",
        f"- strict_duplicate_suppression_count: {summary['strict_duplicate_suppression_count']}",
        f"- eval_duplicate_suppression_count: {summary['eval_duplicate_suppression_count']}",
        f"- cross_family_overlap_retained_count: {summary['cross_family_overlap_retained_count']}",
        f"- pattern_relation_candidate_count: {summary['pattern_relation_candidate_count']}",
        f"- normal_baseline_status: {summary['normal_baseline_status']}",
        f"- normal_baseline_field_count: {summary['normal_baseline_field_count']}",
        f"- prior_overlay_status: {summary['prior_overlay_status']}",
        f"- field_prior_kb_status: {summary['field_prior_kb_status']}",
        f"- value_relation_overlay_status: {summary['value_relation_overlay_status']}",
        f"- value_relation_overlay_hit_count: {summary['value_relation_overlay_hit_count']}",
        f"- field_level_prior_hit_count: {summary['field_level_prior_hit_count']}",
        f"- selected_uncertain_prior_count: {summary['selected_uncertain_prior_count']}",
        f"- candidate_eval_uncertain_prior_count: {summary['candidate_eval_uncertain_prior_count']}",
        f"- promotion_candidate_count: {summary['promotion_candidate_count']}",
        f"- overlay_need_human_review_count: {summary['overlay_need_human_review_count']}",
        "- candidate_signal_level: candidate_signal",
        f"- evidence_boundary: {EVIDENCE_BOUNDARY}",
        f"- pattern_evidence_boundary: {PATTERN_EVIDENCE_BOUNDARY}",
        "",
        "## Relation Candidate Contract",
        "",
        "- value-level relation candidate: concrete field/value relation from L4 review candidates.",
        "- pattern-level relation candidate: abstract role/structure relation from selected value-level relations.",
        "- anchor_unit is the subspace-cutting unit. It can be atomic_anchor or a max-2-component composite_anchor.",
        "- refinement_component replaces the old secondary-anchor wording and only helps form/refine anchor_unit.",
        "- evidence_node is the risk explanation/confirmation node after anchor_unit.",
        "- A&&B and A->B share the same CNT(A_AND_B) and conversion metrics; direction is an evaluation view, not a separate candidate family.",
        "- Multi-hop relations use incremental next-hop CNT / conversion logic.",
        "",
        "## Pair Decision Distribution",
        "",
        markdown_table([{"pair_decision": k, "count": v} for k, v in summary["pair_decision_distribution"].items()]),
        "",
        "## Pair Selection Distribution",
        "",
        markdown_table([{"selection_decision": k, "count": v} for k, v in summary["pair_selection_distribution"].items()]),
        "",
        "## Candidate Eval Queue Distribution",
        "",
        markdown_table([{"candidate_eval_tier": k, "count": v} for k, v in summary["candidate_eval_tier_distribution"].items()]),
        "",
        "## Candidate Reduction Summary",
        "",
        markdown_table([{"reason": k, "count": v} for k, v in summary["candidate_reduction_summary"].items() if isinstance(v, int)]),
        "",
        "## Anchor Funnel Audit Summary",
        "",
        markdown_table([{"metric": k, "value": v} for k, v in summary["anchor_funnel_audit_summary"].items()]),
        "",
        "## Path Decision Distribution",
        "",
        markdown_table([{"path_decision": k, "count": v} for k, v in summary["path_decision_distribution"].items()]),
        "",
        "## Path Selection Distribution",
        "",
        markdown_table([{"selection_decision": k, "count": v} for k, v in summary["path_selection_distribution"].items()]),
        "",
        "## Conditional Gain Status Distribution",
        "",
        markdown_table([{"conditional_gain_status": k, "count": v} for k, v in summary["conditional_gain_status_distribution"].items()]),
        "",
        "## Pattern Type Distribution",
        "",
        markdown_table([{"pattern_type": k, "count": v} for k, v in summary["pattern_type_distribution"].items()]),
        "",
        "## Not Done",
        "",
        "- No platform access.",
        "- No DataAgent/Hive.",
        "- No L6/L7 execution.",
        "- No unpredictability-anom.",
        "- No production rule or strategy recommendation.",
    ]
    return "\n".join(lines) + "\n"


def build_anchor_funnel_audit_md(result: dict[str, Any]) -> str:
    audit = result.get("anchor_funnel_audit", {})
    rows = []
    for row in audit.get("high_quality_anchor_rows", [])[:80]:
        rows.append({
            "field_path": row.get("field_path"),
            "value": str(row.get("value"))[:48],
            "anchor_score": row.get("anchor_score"),
            "anchor_gate": row.get("anchor_quality_gate"),
            "normal_entropy": row.get("normal_field_entropy_normalized"),
            "normal_value_rate": row.get("normal_value_rate"),
            "risk_normal_lift": row.get("risk_normal_lift"),
            "support": row.get("support_count"),
            "pass_pairs": row.get("pass_pair_count"),
            "strict_l6": row.get("in_strict_l6"),
            "eval_queue": row.get("in_candidate_eval_queue"),
            "likely_kill_reason": row.get("likely_kill_reason"),
        })
    reduction = result.get("candidate_reduction_summary", {})
    lines = [
        "# L5 Anchor Funnel Audit",
        "",
        "## Summary",
        "",
        markdown_table([{"metric": k, "value": v} for k, v in audit.items() if k != "high_quality_anchor_rows"]),
        "",
        "## Reduction Reasons",
        "",
        markdown_table([{"reason": k, "count": v} for k, v in reduction.items() if isinstance(v, int)]),
        "",
        "## High Quality Anchor Rows",
        "",
        markdown_table(rows),
    ]
    return "\n".join(lines) + "\n"


def markdown_table(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "None."
    headers = list(rows[0])
    out = ["|" + "|".join(headers) + "|", "|" + "|".join(["---"] * len(headers)) + "|"]
    for row in rows:
        out.append("|" + "|".join(str(row.get(h, "")).replace("|", "/") for h in headers) + "|")
    return "\n".join(out)


def build_anchor_scoring_audit_md(result: dict[str, Any]) -> str:
    nodes = sorted(result.get("value_nodes", []), key=lambda n: n.get("anchor_score", 0.0), reverse=True)
    rows = []
    for node in nodes[:80]:
        rows.append({
            "field_path": node.get("field_path"),
            "value": str(node.get("value_or_pattern"))[:48],
            "anchor_score": round(float(node.get("anchor_score") or 0.0), 1),
            "next_node_score": round(float(node.get("next_node_score") or 0.0), 1),
            "role_suggestion": node.get("role_suggestion"),
            "normal_entropy": node.get("normal_field_entropy"),
            "normal_value_rate": node.get("normal_value_rate"),
            "risk_normal_lift": node.get("risk_normal_lift"),
            "not_anchor_reason": node.get("not_recommended_as_anchor_reason"),
            "normal_status": node.get("normal_baseline_status"),
            "field_role_source": node.get("field_role_source"),
        })
    lines = [
        "# L5 Anchor Scoring Audit",
        "",
        f"- normal_baseline_status: {result['summary'].get('normal_baseline_status')}",
        f"- normal_baseline_field_count: {result['summary'].get('normal_baseline_field_count')}",
        "",
        "This audit ranks value nodes by `anchor_score`. `next_node_score` may remain high for confirming or secondary-anchor nodes even when A-position anchor score is low.",
        "",
        markdown_table(rows),
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate L5 value pair/path candidate signals from L4 review candidates.")
    parser.add_argument("--input-l4-review", required=True)
    parser.add_argument("--knowledge-base")
    parser.add_argument("--normal-baseline-dir", default="/tmp/normal_baseline_layered_v0_2")
    parser.add_argument("--prior-overlay")
    parser.add_argument("--field-prior-kb")
    parser.add_argument("--value-relation-overlay")
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    kb = load_knowledge_base(args.knowledge_base)
    value_overlay_path = args.value_relation_overlay
    if value_overlay_path is None:
        default_value_overlay = Path(__file__).with_name("l5_value_relation_prior_overlay.json")
        value_overlay_path = default_value_overlay if default_value_overlay.exists() else None
    kb = attach_prior_overlay(
        kb,
        load_prior_overlay(args.prior_overlay),
        load_field_prior_kb(args.field_prior_kb),
        load_value_relation_overlay(value_overlay_path),
    )
    normal_baseline = load_normal_baseline(args.normal_baseline_dir)
    candidates = load_l4_review_candidates(args.input_l4_review)
    result = run_l5(candidates, kb, normal_baseline)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "l6_next_tasks_from_l5.json", {
        "l6_next_tasks": result["l6_tasks"],
        "summary": result["summary"],
    })
    write_json(output_dir / "candidate_eval_queue_from_l5.json", {
        "candidate_eval_queue": result["candidate_eval_queue"],
        "summary": {
            "candidate_eval_queue_count": len(result["candidate_eval_queue"]),
            "candidate_eval_tier_distribution": result["summary"]["candidate_eval_tier_distribution"],
            "candidate_eval_uncertain_prior_count": result["summary"]["candidate_eval_uncertain_prior_count"],
            "forward_direction_selected_count": result["summary"]["forward_direction_selected_count"],
            "reverse_direction_selected_count": result["summary"]["reverse_direction_selected_count"],
            "bidirectional_relation_count": result["summary"]["bidirectional_relation_count"],
            "refinement_component_direction_count": result["summary"]["refinement_component_direction_count"],
            "hold_low_conversion_rescued_count": result["summary"]["hold_low_conversion_rescued_count"],
            "atomic_anchor_count": result["summary"]["atomic_anchor_count"],
            "composite_anchor_count": result["summary"]["composite_anchor_count"],
            "three_component_anchor_count": result["summary"]["three_component_anchor_count"],
            "eval_duplicate_suppression_count": result["summary"]["eval_duplicate_suppression_count"],
            "cross_family_overlap_retained_count": result["summary"]["cross_family_overlap_retained_count"],
            "evidence_boundary": EVIDENCE_BOUNDARY,
        },
    })
    write_json(output_dir / "held_or_drilldown_queue_from_l5.json", {
        "held_or_drilldown_queue": result["held_or_drilldown_queue"],
        "summary": {
            "held_or_drilldown_queue_count": len(result["held_or_drilldown_queue"]),
            "broad_anchor_hold_count": result["summary"]["broad_anchor_hold_count"],
            "need_finer_granularity_count": result["summary"]["need_finer_granularity_count"],
            "evidence_boundary": EVIDENCE_BOUNDARY,
        },
    })
    write_json(output_dir / "l5_execution_candidates.json", {
        "value_nodes": result["value_nodes"],
        "pair_candidates": result["pair_candidates"],
        "path_candidates": result["path_candidates"],
        "composite_anchor_candidates": result["composite_anchor_candidates"],
        "pattern_candidates": result["pattern_candidates"],
        "summary": result["summary"],
    })
    write_json(output_dir / "l5_pattern_candidates.json", {
        "l5_pattern_candidates": result["pattern_candidates"],
        "summary": {
            "pattern_candidate_count": len(result["pattern_candidates"]),
            "pattern_type_distribution": result["summary"]["pattern_type_distribution"],
            "evidence_boundary": PATTERN_EVIDENCE_BOUNDARY,
        },
    })
    write_json(output_dir / "l5_contract_violations.json", {
        "contract_violations": result["contract_violations"],
        "summary": {"contract_violation_count": len(result["contract_violations"])},
    })
    write_json(output_dir / "l5_knowledge_base_snapshot.json", kb)
    write_json(output_dir / "l5_prior_seed_input.json", result["prior_seed_input"])
    write_json(output_dir / "llm_field_pair_prior_overlay.example.json", overlay_example())
    write_json(output_dir / "l5_prior_promotion_candidates.json", {
        "promotion_candidates": result["promotion_candidates"],
        "summary": {
            "promotion_candidate_count": len(result["promotion_candidates"]),
            "boundary": "Run-level value overlay is not promoted automatically. Human review or Candidate Eval is required.",
        },
    })
    write_json(output_dir / "l5_anchor_funnel_audit.json", {
        "anchor_funnel_audit": result["anchor_funnel_audit"],
        "candidate_reduction_summary": result["candidate_reduction_summary"],
    })
    (output_dir / "l5_summary.md").write_text(build_summary_md(result), encoding="utf-8")
    (output_dir / "l5_run_log.md").write_text(build_summary_md(result), encoding="utf-8")
    (output_dir / "l5_anchor_scoring_audit.md").write_text(build_anchor_scoring_audit_md(result), encoding="utf-8")
    (output_dir / "l5_anchor_funnel_audit.md").write_text(build_anchor_funnel_audit_md(result), encoding="utf-8")
    print(json.dumps(result["summary"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
