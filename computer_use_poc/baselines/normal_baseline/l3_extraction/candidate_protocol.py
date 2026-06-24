"""Shared P0 candidate protocol helpers for L3/L4/L5.

The helpers are intentionally small and config-driven. They do not query
platforms, Hive, or DataAgent.
"""

from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASELINE_REGISTRY_PATH = ROOT / "baseline_registry_v0_1.json"

FEATURE_TYPES = {"raw_field", "numeric_bucket", "derived_feature"}
VALUE_TYPES = {"category", "boolean", "count", "duration", "score", "ratio", "sequence", "set", "compatibility", "unknown"}
BASELINE_MODES = {"baseline_supported", "discovery_only"}
BASELINE_STATUSES = {
    "normal_baseline_available",
    "baseline_missing",
    "lookup_unreliable",
    "not_applicable",
}
NEXT_STEP_SUGGESTIONS = {
    "baseline_build_needed",
    "replay_needed",
    "baseline_and_replay_needed",
    "report_only",
    "drop_low_value",
}
COMMONALITY_FAMILIES = {
    "field_value_commonality",
    "numeric_bucket_commonality",
    "behavior_pattern_commonality",
    "structure_relation_commonality",
    "expanded_feature_commonality",
}
COMMONALITY_LEVELS = {"high", "medium", "low"}
NUMERIC_BUCKETS = [
    ("<=1", None, 1.0),
    ("<=3", None, 3.0),
    ("<=7", None, 7.0),
    (">=10", 10.0, None),
    (">=30", 30.0, None),
    (">=100", 100.0, None),
]


def load_baseline_registry(path: str | Path | None = None) -> dict[str, Any]:
    path = Path(path or DEFAULT_BASELINE_REGISTRY_PATH)
    if not path.exists():
        return {"baseline_actions": []}
    return json.loads(path.read_text(encoding="utf-8"))


def action_key(source_name: str, source_action: str = "") -> str:
    source_name = str(source_name or "")
    source_action = str(source_action or "")
    return f"{source_name}.{source_action}" if source_action else source_name


def baseline_entry_for(candidate: dict[str, Any], registry: dict[str, Any] | None = None) -> dict[str, Any]:
    registry = registry or load_baseline_registry()
    source = str(candidate.get("source_name") or "")
    action = str(candidate.get("source_action") or candidate.get("action_or_layer") or "")
    keys = {action_key(source, action), source, action}
    field_path = str(candidate.get("field_path") or "")
    for entry in registry.get("baseline_actions", []):
        entry_keys = {
            str(entry.get("action_name") or ""),
            str(entry.get("field_source") or ""),
            action_key(str(entry.get("field_source") or ""), str(entry.get("action_name") or "")),
        }
        if not keys & entry_keys:
            continue
        prefixes = entry.get("field_path_prefixes") or []
        if prefixes and not any(field_path.startswith(prefix) for prefix in prefixes):
            continue
        return entry
    return {"baseline_available": False}


def candidate_baseline_mode(candidate: dict[str, Any], registry: dict[str, Any] | None = None) -> str:
    if candidate.get("feature_type") == "derived_feature":
        return "discovery_only"
    entry = baseline_entry_for(candidate, registry)
    if not entry.get("baseline_available"):
        return "discovery_only"
    if candidate.get("feature_type") == "numeric_bucket" and not entry.get("supports_numeric_bucket"):
        return "discovery_only"
    if candidate.get("feature_type") in {None, "raw_field"} and not entry.get("supports_value_distribution", True):
        return "discovery_only"
    return "baseline_supported"


def infer_value_type(value: Any, field_path: str = "") -> str:
    text = "" if value is None else str(value).strip()
    leaf = str(field_path or "").split(".")[-1].lower()
    if text.lower() in {"true", "false", "0", "1", "0.0", "1.0"} and leaf in {
        "frida", "root", "xposed", "emulator", "debug", "hook", "status", "result",
        "didtag", "androidos", "cs", "needcheck",
    }:
        return "boolean"
    if _numeric_value(value) is not None:
        if any(token in leaf for token in ("count", "cnt", "times", "num")):
            return "count"
        if any(token in leaf for token in ("time", "duration", "latency")):
            return "duration"
        if any(token in leaf for token in ("score", "risk")):
            return "score"
        if any(token in leaf for token in ("ratio", "rate")):
            return "ratio"
        return "count"
    if "," in text or "|" in text:
        return "sequence"
    return "category" if text else "unknown"


def _numeric_value(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        f = float(value)
        return f if math.isfinite(f) else None
    text = str(value).strip()
    if not re.fullmatch(r"-?\d+(\.\d+)?", text):
        return None
    try:
        return float(text)
    except ValueError:
        return None


def is_numeric_bucketable(value: Any, field_path: str = "") -> bool:
    if _numeric_value(value) is None:
        return False
    if infer_value_type(value, field_path) == "boolean":
        return False
    leaf = str(field_path or "").split(".")[-1].lower()
    if leaf in {"status", "result", "type", "action_type", "code", "didtag", "androidos"}:
        return False
    return True


def bucket_for_value(value: Any) -> dict[str, Any] | None:
    f = _numeric_value(value)
    if f is None:
        return None
    if f <= 1:
        label, low, high = "<=1", None, 1.0
    elif f <= 3:
        label, low, high = "<=3", None, 3.0
    elif f <= 7:
        label, low, high = "<=7", None, 7.0
    elif f >= 100:
        label, low, high = ">=100", 100.0, None
    elif f >= 30:
        label, low, high = ">=30", 30.0, None
    elif f >= 10:
        label, low, high = ">=10", 10.0, None
    else:
        label, low, high = "<=7", None, 7.0
    return {
        "bucket_label": label,
        "bucket_range": {"gte": low, "lte": high},
        "bucket_method": "fixed_threshold",
    }


def default_commonality_family(feature_type: Any) -> str:
    if feature_type == "numeric_bucket":
        return "numeric_bucket_commonality"
    if feature_type == "derived_feature":
        return "expanded_feature_commonality"
    return "field_value_commonality"


def feature_definition_status(feature_definition: Any) -> str:
    return "present" if bool(feature_definition) else "missing"


def commonality_level_for(item: dict[str, Any]) -> str:
    try:
        hit_count = int(item.get("risk_hit_count") or 0)
    except (TypeError, ValueError):
        hit_count = 0
    try:
        hit_rate = float(item.get("risk_hit_rate") or 0.0)
    except (TypeError, ValueError):
        hit_rate = 0.0
    try:
        denominator = int(item.get("risk_denominator") or item.get("risk_observed_count") or item.get("risk_sample_count") or 0)
    except (TypeError, ValueError):
        denominator = 0
    exact_rate = (hit_count / denominator) if denominator else hit_rate
    if (hit_rate >= 0.67 or exact_rate >= (2 / 3)) and hit_count >= 3:
        return "high"
    if hit_rate >= 0.5 and hit_count >= 3:
        return "medium"
    return "low"


def default_commonality_evidence(item: dict[str, Any]) -> list[dict[str, Any]]:
    if item.get("feature_type") == "derived_feature":
        return []
    evidence = {
        "evidence_type": default_commonality_family(item.get("feature_type")),
        "field_path": item.get("field_path"),
        "candidate_value": item.get("candidate_value") or item.get("field_value_or_pattern"),
        "risk_hit_count": item.get("risk_hit_count"),
        "risk_denominator": item.get("risk_denominator") or item.get("risk_observed_count") or item.get("risk_sample_count"),
        "risk_hit_rate": item.get("risk_hit_rate"),
    }
    return [evidence]


def apply_candidate_protocol(candidate: dict[str, Any], registry: dict[str, Any] | None = None) -> dict[str, Any]:
    item = dict(candidate)
    item.setdefault("feature_type", "raw_field")
    item.setdefault("value_type", infer_value_type(item.get("field_value_or_pattern"), item.get("field_path", "")))
    item.setdefault("feature_name", item.get("field_path"))
    item.setdefault("source_fields", [item.get("field_path")] if item.get("field_path") else [])
    item.setdefault("source_events", [])
    item.setdefault("feature_definition", {})
    item.setdefault("bucket_label", None)
    item.setdefault("bucket_range", None)
    item.setdefault("candidate_value", item.get("field_value_or_pattern"))
    item.setdefault("risk_denominator", item.get("risk_observed_count") or item.get("risk_sample_count"))
    item.setdefault("normal_hit_rate", item.get("normal_hit_rate"))
    item.setdefault("lift", item.get("lift"))
    item.setdefault("evidence_examples", [])
    item.setdefault("eval_required_fields", [])
    item.setdefault("commonality_family", default_commonality_family(item.get("feature_type")))
    if (
        item.get("feature_type") == "numeric_bucket"
        and item.get("commonality_family") == "field_value_commonality"
    ):
        item["commonality_family"] = "numeric_bucket_commonality"
    item.setdefault("feature_definition_status", feature_definition_status(item.get("feature_definition")))
    item.setdefault("commonality_evidence", default_commonality_evidence(item))
    item.setdefault("commonality_level", commonality_level_for(item))
    item.setdefault("candidate_family", item.get("commonality_family"))
    if item.get("feature_type") == "numeric_bucket":
        item.setdefault("candidate_source", "numeric_bucket")
    elif item.get("feature_type") == "derived_feature":
        item.setdefault("candidate_source", item.get("proposal_source") or "llm_derived")
    else:
        item.setdefault("candidate_source", "deterministic_field_value")
    item.setdefault("proposal_source", None)
    item.setdefault("proposal_type", None)
    item.setdefault("derived_feature_name", item.get("feature_name") if item.get("feature_type") == "derived_feature" else None)
    item.setdefault("derived_feature_definition", item.get("feature_definition") if item.get("feature_type") == "derived_feature" else None)
    item.setdefault("recompute_rule", (item.get("feature_definition") or {}).get("recompute_rule"))
    item.setdefault("evidence_summary", item.get("commonality_evidence"))
    item.setdefault("risk_hit_users", item.get("supporting_user_ids") or item.get("risk_hit_sample_ids") or [])
    item.setdefault("signal_type", item.get("value_type") or item.get("feature_type"))
    item.setdefault("semantic_strength", "unknown")
    item.setdefault("candidate_role", "feature_candidate")
    item.setdefault("quality_bucket", "medium_value_discovery" if item.get("feature_type") == "derived_feature" else None)
    item.setdefault("merge_group_id", None)
    item.setdefault("representative_feature_id", item.get("candidate_id"))
    item.setdefault("merged_from_feature_ids", [])
    item.setdefault("dropped_reason", None)
    item.setdefault("audit_reason", None)
    item.setdefault("ranking_reason", item.get("pool_reason"))
    item.setdefault("lineage", {
        "candidate_id": item.get("candidate_id"),
        "candidate_source": item.get("candidate_source"),
        "proposal_source": item.get("proposal_source"),
        "source_action": item.get("source_action") or item.get("action_or_layer"),
        "source_fields": item.get("source_fields") or [],
    })
    item.setdefault("audit_tags", [])
    if item.get("feature_type") == "derived_feature" and item.get("feature_definition_status") == "missing":
        item["l5_usage"] = "audit_only"
        item["l5_exclusion_reason"] = "derived_feature_missing_feature_definition"
    mode = candidate_baseline_mode(item, registry)
    item["baseline_mode"] = mode
    if mode == "discovery_only":
        item["normal_hit_rate"] = None
        item["lift"] = None
        item.setdefault("baseline_status", "baseline_missing" if item.get("feature_type") != "derived_feature" else "not_applicable")
        if item.get("candidate_role") in {"coverage_signal", "report_only"} or item.get("quality_bucket") in {"coverage_signal", "duplicate_or_low_value"}:
            item.setdefault("next_step_suggestion", "report_only")
        else:
            item.setdefault("next_step_suggestion", "baseline_and_replay_needed")
        item.setdefault("requires_l6_replay", True)
        item.setdefault("l6_replay_required_reason", "impact_and_false_positive_validation_required")
        item.setdefault("readiness", "needs_baseline_and_replay")
    else:
        item.setdefault("baseline_status", "normal_baseline_available")
        item.setdefault("next_step_suggestion", "replay_needed")
        item.setdefault("requires_l6_replay", True)
        item.setdefault("l6_replay_required_reason", "impact_and_false_positive_validation_required")
        item.setdefault("readiness", "needs_replay")
    return item
