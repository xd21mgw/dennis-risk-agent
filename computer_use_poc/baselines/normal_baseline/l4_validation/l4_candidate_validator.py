#!/usr/bin/env python3
"""l4_candidate_validator.py — Validate L3 single-point candidates against normal baseline.

L4 = L3 单点候选 + normal baseline 的验证层。

Input: enriched L3 candidates (from normal_baseline_enricher output)
Output: candidate validation cards with statistical_strength, semantic_clarity,
        leakage_risk, identifier_risk, l4_decision, and boundary markers.

L4 boundary rules:
  - L4 does NOT produce structure candidates (L5 responsibility)
  - L4 does NOT run unpredictability-anom (L5 responsibility)
  - L4 does NOT do historical recall (L6-A responsibility)
  - L4 does NOT do strategy recommendation (L6-B responsibility)
  - normal_observed_count=0 must produce confidence=low, not high
  - result signals (action=deny, policy_hit, risk_label) become result_signal_not_feature
  - ID/anchor fields (UUID-like, xm1/xm3, device_token) become identifier_anchor_not_feature
  - semantic_clarity=low/unknown candidates must not hardcode field meaning
  - normal baseline is L4's external asset, not L5's main flow
  - L4 output feeds L5; L5 does exact-value/structure typing
"""

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

ALIGNMENT_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "realtime_offline_field_alignment")
)
if ALIGNMENT_DIR not in sys.path:
    sys.path.insert(0, ALIGNMENT_DIR)

from field_alignment_resolver import (  # noqa: E402
    classify_field_role as registry_classify_field_role,
    resolve_field,
    resolve_source,
)

# ---- Constants ----

L4_VERSION = "v0_1_4_field_alignment"

# Fields that are confirmed result/leakage signals (conclusion labels)
# These are platform/model/policy risk JUDGMENTS, not device facts.
# v0.1.1: weaponRisk/weapon_risk REMOVED from this set.
# v0.1.1-hotfix: oneRisk* labels are FACTUAL descriptions, removed from here.
# v0.1.2: "action" and "result" REMOVED from this set — they are too
# context-dependent. Login logs' "action" = operation type (LOGIN, REFRESH),
# not enforcement action. Use SOURCE_AWARE_RESULT_SIGNALS instead.
RESULT_SIGNAL_FIELD_PATTERNS = {
    "risk_decision", "riskDecision", "action_result", "actionResult",
    "policy_code", "policyCode", "policy_hit", "policyHit",
    "event_type", "eventType", "enforcement_result", "enforcementResult",
    "risk_label", "riskLabel",
    "risk_score", "riskScore", "hit_strategy", "hitStrategy",
    "punish_type", "punishType",
    "is_black", "isBlack", "is_risk", "isRisk",
    "machine_account", "machineAccount",
    "model_decision", "modelDecision",
    "high_risk", "highRisk",
    "weaponRiskScore", "weapon_risk_score",
}

# v0.1.2: Source-aware result signal patterns.
# Some field names (like "action", "result", "decision") are ambiguous:
# they mean different things in different sources.
# Only mark them as result_signal in specific source/path contexts.
# If the field_path matches one of these prefix patterns → confirmed.
SOURCE_AWARE_RESULT_SIGNALS = {
    # "action" is a result signal ONLY in enforcement/policy/strategy contexts
    "action": [
        "tianshi_rcp.",
        "rcp_event.",
        "rcp_",
        "strategy.",
        "enforcement.",
        "punish.",
    ],
    # "result" is a result signal ONLY in enforcement/policy contexts
    "result": [
        "tianshi_rcp.",
        "rcp_event.",
        "enforcement.",
    ],
    # "decision" is a result signal ONLY in risk/model contexts
    "decision": [
        "tianshi_rcp.",
        "rcp_event.",
        "risk.",
        "model.",
    ],
}

# Sub-fields within weaponRisk / labelInfo / weapon_one_risk containers
# that are CONCLUSION labels = risk judgments by platform/model/policy.
# These should be tagged result_signal_not_feature.
# v0.1.1-hotfix: oneRisk* labels are NOT conclusions; they are factual
# descriptions (detected app present, IP in IDC, script detected, etc.).
# The oneRisk prefix only means "associated with risk", not "judged risky".
WEAPONRISK_CONCLUSION_SUBFIELDS = {
    # Risk score / level conclusions
    "riskScore", "risk_score", "riskLevel", "risk_level",
    "weaponRiskScore", "totalScore", "total_score",
    # Risk decision / judgment
    "riskDecision", "risk_decision", "machineAccount",
    "modelDecision", "model_decision",
    "highRisk", "high_risk",
    # Policy / strategy hits
    "hitStrategy", "hit_strategy", "policyHit", "policy_hit",
}

# Sub-fields within weaponRisk / labelInfo / weapon_one_risk containers
# that are FACTUAL device/environment labels = observed device state facts.
# These CAN be L3/L4 candidates; they are NOT result signals.
WEAPONRISK_FACTUAL_SUBFIELDS = {
    # SIM / carrier facts
    "noSim", "no_sim", "noSimCard", "no_sim_card",
    "oneRiskNoSim", "oneRiskNoSimCardIos", "oneRiskNoPasswordIos",
    # Device state facts
    "factoryReset", "factory_reset", "noLockScreen", "no_lock_screen",
    "noPassword", "no_password",
    # Usage facts
    "lowLaunchCount", "low_launch_count",
    "launchLess10", "launch_less_10",
    "oneRiskLaunchLess10", "oneRiskLaunchLess10Ios",
    "oneRiskUserAppCntLess10",
    "appCntLess10", "app_cnt_less_10",
    "firstLaunch", "first_launch",
    "oneRiskFirstLaunchIos",
    # Battery facts
    "batteryZero", "battery_zero",
    "oneRiskBatteryZero",
    # Device environment facts
    "root", "isRoot", "is_root",
    "emulator", "isEmulator", "is_emulator",
    "hook", "frida", "xposed",
    "accessibility_enabled", "accessibilityEnabled",
    "abnormalSensor", "abnormal_sensor",
    "deviceEnvFact",
    "refresh_12Day", "refresh12Day",
    "oneRiskRefresh_12Day",
    "apkInstall_5M", "apkInstall5M",
    "oneRiskApkInstall_5M",
    # v0.1.1-hotfix: oneRisk* labels are factual descriptions, not judgments
    # "MeetingTool" = detected meeting tool app installed (device fact)
    # "AutoScript" = detected auto-script framework present (device fact)
    # "ClickPlugin" = detected click plugin present (device fact)
    # "OnlineLoan" = detected online loan app installed (device fact)
    # "IpIDC" = IP address is in IDC range (network fact)
    # "AccSvcAbilityCnt" = accessibility service count threshold (device fact)
    "oneRiskMeetingTool", "oneRiskAutoScript",
    "oneRiskClickPlugin", "oneRiskOnlineLoan",
    "oneRiskIpIDC", "oneRiskAccSvcAbilityCnt",
}

# Container paths: if a field_path ends with one of these, the parent is
# a risk label container, and the last part is a sub-label.
WEAPONRISK_CONTAINER_SUFFIXES = [
    ".weaponRisk.", ".weapon_risk.",
    ".labelInfo.", ".label_info.",
    ".weapon_one_risk.",
]

# v0.1.3: normal_value_lookup_status enumeration
# Tracks whether the candidate's specific value was evaluated in the normal baseline.
NORMAL_VALUE_LOOKUP_STATUSES = {
    "value_matched",           # field_value found in baseline TOP-N distribution
    "value_not_found_in_top",  # field_value not in TOP-N but TOP-N may not be exhaustive
    "normal_value_distribution_incomplete",  # low-cardinality value lookup miss cannot be treated as normal_hit=0
    "pattern_not_supported",   # field_value is a pattern/range, not supported in v0.1.3
    "field_matched_but_value_not_evaluated",  # baseline has field coverage but no value-level contrast
    "field_unobserved",        # field not found in baseline at all
    "high_cardinality_skipped",# field is high cardinality, value contrast not feasible
    "source_or_schema_unresolved",  # source alias or schema mapping unresolved
}


def normalize_field_path(field_path: str, source_name: str = "") -> str:
    """Normalize field_path through realtime_offline_field_alignment."""
    return resolve_field(source_name, field_path).get("canonical_field_path", field_path)


def infer_source_name(field_path: str, provided_source: str = "") -> str:
    """Infer canonical source through realtime_offline_field_alignment."""
    if provided_source:
        return resolve_source(provided_source).get("canonical_source", provided_source)
    return resolve_field("", field_path).get("canonical_source", "")

# Fields that are confirmed ID/anchor fields
IDENTIFIER_FIELD_PATTERNS = {
    "did", "device_id", "deviceId", "device_id_str", "deviceIdStr",
    "xm1", "xm3", "xm", "trace_id", "traceId",
    "session_id", "sessionId", "token", "access_token", "accessToken",
    "request_id", "requestId", "transaction_id", "transactionId",
    "uuid", "uid", "user_id", "userId",
    "photo_id", "photoId", "comment_id", "commentId",
    "source_id", "sourceId", "event_id", "eventId",
}

# Field name substrings that suggest identifier
# v0.1.1: added "Id" matching uses word-boundary-aware logic in
# classify_identifier_risk to avoid false positives on bootId etc.
IDENTIFIER_SUBSTRINGS = ["_id", "_token", "Token"]

# Identifier-like suffixes that are actually device behavior/pattern fields,
# NOT pure anchors. These should NOT be auto-blocked as identifier_anchor.
IDENTIFIER_BEHAVIOR_EXEMPTIONS = {
    "bootId", "boot_id",  # bootId value = anchor; bootId_pattern/stability = behavior
    "sessionId", "session_id",  # session count/stability can be behavior
}

# Semantic clarity heuristics
KNOWN_FIELD_FAMILIES = {
    "device": {"phone_model", "phoneModel", "os_version", "osVersion", "app_version",
               "appVersion", "brand", "model", "arch", "cpu", "screen", "launch",
               "boot", "lock_screen", "sim", "root", "frida", "xposed",
               "accessibility", "automation", "script_risk", "install",
               "register", "registercnt", "bootid", "device_register",
               "device_register_cnt", "deviceregistercnt"},
    "network": {"ip", "city", "province", "asn", "isp", "network_type", "wifi",
                "vpn", "proxy", "cdn"},
    "login": {"login_type", "loginType", "login_source", "loginSource", "login_method",
              "loginMethod", "login_time", "loginTime", "kick_out", "token_status"},
    "behavior": {"action_type", "actionType", "action_time", "actionTime",
                 "task_type", "taskType", "reward_type", "rewardType",
                 "entry", "channel", "frontend_activity", "backend_action"},
    "content": {"publish_time", "publishDevice", "content_template", "media_type",
                "audit_result"},
}


def classify_normal_baseline_status(
    normal_observed_count: int,
    normal_hit_count: int,
    risk_hit_rate: float,
) -> str:
    """Classify the normal baseline observation status."""
    if normal_observed_count == 0:
        return "unobserved_missing"
    if 0 < normal_observed_count < 200:
        return "insufficient_sample"
    normal_hit_rate = normal_hit_count / normal_observed_count if normal_observed_count > 0 else 0.0
    if normal_hit_rate >= risk_hit_rate * 0.5:
        return "observed_negative"
    return "observed_positive"


def classify_statistical_strength(
    risk_hit_rate: float,
    normal_baseline_status: str,
    normal_hit_rate: Optional[float],
    normal_value_lookup_status: str = "",
) -> str:
    """Classify statistical strength of risk-normal separation.

    v0.1.3: If normal_value_lookup_status indicates value-level was not evaluated,
    statistical_strength must be capped at 'medium' (not 'high').
    'field_matched_but_value_not_evaluated' means we know the field exists in baseline
    but don't know the candidate value's hit rate → cannot claim strong separation.
    """
    if normal_baseline_status in ("unobserved_missing", "insufficient_sample"):
        return "unevaluable"
    if normal_hit_rate is None:
        return "unevaluable"
    # v0.1.3: value-level not evaluated → cap at medium
    if normal_value_lookup_status in (
        "field_matched_but_value_not_evaluated",
        "value_not_found_in_top",
        "normal_value_distribution_incomplete",
        "pattern_not_supported",
        "source_or_schema_unresolved",
    ):
        if normal_value_lookup_status == "normal_value_distribution_incomplete":
            return "unevaluable"
        delta = risk_hit_rate - normal_hit_rate
        if risk_hit_rate >= 0.3 and delta >= 0.1:
            return "medium"
        return "low"
    if normal_value_lookup_status == "high_cardinality_skipped":
        return "unevaluable"
    # Full value-level contrast available
    delta = risk_hit_rate - normal_hit_rate
    if risk_hit_rate >= 0.5 and normal_baseline_status == "observed_positive" and delta >= 0.3:
        return "high"
    if risk_hit_rate >= 0.3 and normal_baseline_status == "observed_positive" and delta >= 0.1:
        return "medium"
    return "low"


def classify_semantic_clarity(field_path: str, is_unknown_field: bool = False) -> str:
    """Classify semantic clarity of a field based on its path and known families."""
    if is_unknown_field:
        return "unknown"
    field_lower = field_path.lower()
    # Check known families
    for family, known_fields in KNOWN_FIELD_FAMILIES.items():
        for kf in known_fields:
            if kf.lower() in field_lower:
                return "high"
    # Check if field path has recognizable structure
    parts = field_path.split(".")
    last_part = parts[-1] if parts else ""
    # Very short or numeric-only names suggest unknown
    if len(last_part) <= 2 and last_part.isdigit():
        return "unknown"
    # If the last part matches common patterns
    common_suffixes = ["type", "name", "time", "count", "status", "version",
                       "model", "brand", "count", "rate", "ratio", "flag",
                       "enabled", "present", "detected"]
    for suffix in common_suffixes:
        if suffix in last_part.lower():
            return "medium"
    return "low"


def _is_inside_weaponrisk_container(field_path: str) -> bool:
    """Check if field_path is inside a weaponRisk/labelInfo/weapon_one_risk container."""
    path_lower = field_path.lower()
    for suffix in WEAPONRISK_CONTAINER_SUFFIXES:
        if suffix.lower() in path_lower:
            return True
    return False


def _get_container_subfield(field_path: str) -> str:
    """Extract the sub-label name from a container path.

    E.g. 'weapon_android.raw_data.weaponRisk.noSim' -> 'noSim'
    """
    for container in WEAPONRISK_CONTAINER_SUFFIXES:
        idx = field_path.lower().find(container.lower())
        if idx >= 0:
            # Everything after the container prefix
            after = field_path[idx + len(container):]
            # Take the first segment as the sub-label
            return after.split(".")[0] if after else ""
    return ""


def classify_leakage_risk(field_path: str, field_value: str = "", source_name: str = "") -> str:
    """Classify whether this field is a result/leakage signal.

    v0.1.1: weaponRisk / labelInfo containers are NOT blanket-blocked.
    v0.1.2: \"action\", \"result\", \"decision\" are source-aware — only confirmed
    in enforcement/policy/risk source contexts, not in login logs or device data.
    """
    registry_role = registry_classify_field_role(source_name, field_path)
    if registry_role.get("field_role") == "result_signal":
        return "confirmed"
    if registry_role.get("field_role") in {
        "factual_device_label",
        "factual_environment_label",
        "behavior_fact",
        "profile_fact",
        "identifier_anchor",
        "high_cardinality_anchor",
    }:
        return "none"

    parts = field_path.split(".")
    last_part = parts[-1] if parts else ""

    # Check if inside a weaponRisk/labelInfo container
    if _is_inside_weaponrisk_container(field_path):
        subfield = _get_container_subfield(field_path)
        if subfield in WEAPONRISK_CONCLUSION_SUBFIELDS:
            return "confirmed"
        if subfield in WEAPONRISK_FACTUAL_SUBFIELDS:
            return "none"  # factual label: eligible as candidate
        return "possible"

    # Standard check: exact match on last part
    if last_part in RESULT_SIGNAL_FIELD_PATTERNS:
        return "confirmed"

    # v0.1.2: Source-aware check for ambiguous fields (action/result/decision)
    if last_part in SOURCE_AWARE_RESULT_SIGNALS:
        allowed_prefixes = SOURCE_AWARE_RESULT_SIGNALS[last_part]
        path_lower = field_path.lower()
        for prefix in allowed_prefixes:
            if prefix.lower() in path_lower:
                return "confirmed"
        if source_name:
            for prefix in allowed_prefixes:
                if prefix.lower() in source_name.lower():
                    return "confirmed"
        # Ambiguous field in non-enforcement context → not a result signal
        return "none"

    # Check field value patterns that suggest result
    if field_value in ("deny", "blocked", "rejected", "hit", "true", "1"):
        for pattern in RESULT_SIGNAL_FIELD_PATTERNS:
            if pattern.lower() in field_path.lower():
                return "confirmed"

    # Check if path contains result-like substrings
    result_substrings = ["risk", "decision", "action", "enforcement", "punish", "hit"]
    for sub in result_substrings:
        if sub in field_path.lower() and last_part.lower() in RESULT_SIGNAL_FIELD_PATTERNS:
            return "confirmed"

    # weaponRisk as top-level field → confirmed (risk score container)
    if last_part.lower() in ("weaponrisk", "weapon_risk"):
        return "confirmed"

    # Possible leakage for score-like fields
    if "risk" in field_path.lower() and "score" in field_path.lower():
        return "possible"

    return "none"


def classify_identifier_risk(field_path: str, field_value_or_pattern: str = "") -> str:
    """Classify whether this field is an ID/anchor field.

    v0.1.1: bootId and other identifier-like fields that can also represent
    device behavior/patterns are handled with exemption logic:
    - If the field_value_or_pattern suggests a pattern/behavior metric
      (e.g., bootId_stability, bootId_reset_frequency),
      → identifier_risk is downgraded to 'none' or 'possible'.
    - If the field is a pure ID value, → confirmed or possible as before.
    """
    registry_role = registry_classify_field_role("", field_path)
    if registry_role.get("field_role") in {"identifier_anchor", "high_cardinality_anchor"}:
        if registry_role.get("confidence") == "medium":
            return "possible"
        return "confirmed"

    parts = field_path.split(".")
    last_part = parts[-1] if parts else ""

    if last_part in IDENTIFIER_FIELD_PATTERNS:
        # Check if it's a behavior/pattern variant
        if last_part in IDENTIFIER_BEHAVIOR_EXEMPTIONS:
            # bootId value = anchor; but bootId pattern/behavior metric = not anchor
            val_lower = (field_value_or_pattern or "").lower()
            pattern_keywords = ["pattern", "stability", "frequency", "cluster",
                                "reset", "count", "rate", "_cnt", "_ratio",
                                "change", "diff", "anomaly", "score"]
            for kw in pattern_keywords:
                if kw in val_lower or kw in last_part.lower():
                    return "possible"  # downgraded: behavior pattern, not pure anchor
            return "confirmed"  # pure ID value
        return "confirmed"

    # Check substrings (more targeted to avoid false positives)
    for sub in IDENTIFIER_SUBSTRINGS:
        if sub in last_part:
            return "possible"

    # Check for Id suffix but exclude known behavior fields
    if last_part.endswith("Id") or "Id" in last_part:
        if last_part in IDENTIFIER_BEHAVIOR_EXEMPTIONS:
            val_lower = (field_value_or_pattern or "").lower()
            pattern_keywords = ["pattern", "stability", "frequency", "cluster",
                                "reset", "count", "rate", "_cnt", "_ratio",
                                "change", "diff", "anomaly", "score"]
            for kw in pattern_keywords:
                if kw in val_lower or kw in last_part.lower():
                    return "possible"
            return "possible"  # bootId still possible even for value
        return "possible"

    return "none"


def decide_l4_decision(
    statistical_strength: str,
    semantic_clarity: str,
    leakage_risk: str,
    identifier_risk: str,
    normal_baseline_status: str,
    risk_observed_count: int,
) -> str:
    """Decide the L4 validation decision for a single candidate."""
    # Priority 1: Result signal check
    if leakage_risk in ("confirmed", "possible"):
        return "result_signal_not_feature"

    # Priority 2: Identifier check
    if identifier_risk in ("confirmed", "possible"):
        return "identifier_anchor_not_feature"

    # Priority 3: Normal unobserved
    if normal_baseline_status in ("unobserved_missing", "insufficient_sample"):
        return "normal_unobserved_need_baseline"

    # Priority 4: Reject/hold for very weak or tiny sample
    if statistical_strength == "low" and normal_baseline_status == "observed_negative":
        return "reject_or_hold"
    if risk_observed_count < 3:
        return "reject_or_hold"

    # Priority 5: Strong single candidate
    if (statistical_strength == "high"
            and semantic_clarity in ("high", "medium")
            and leakage_risk == "none"
            and identifier_risk == "none"
            and normal_baseline_status == "observed_positive"):
        return "strong_single_candidate"

    # Priority 6: Semantic unknown but strong statistical
    if (statistical_strength in ("high", "medium")
            and semantic_clarity in ("low", "unknown")
            and leakage_risk == "none"
            and identifier_risk == "none"):
        return "semantic_unknown_but_strong_statistical_candidate"

    # Priority 7: Weak single candidate
    if (statistical_strength == "medium"
            and leakage_risk == "none"
            and identifier_risk == "none"):
        return "weak_single_candidate"

    # Default: reject or hold
    return "reject_or_hold"


def compute_confidence(
    normal_observed_count: int,
    statistical_strength: str,
    l4_decision: str,
) -> str:
    """Compute confidence level. normal_observed_count=0 must produce low."""
    if normal_observed_count == 0:
        return "low"
    if l4_decision in ("result_signal_not_feature", "identifier_anchor_not_feature"):
        return "low"
    if statistical_strength == "high" and l4_decision == "strong_single_candidate":
        return "high"
    if statistical_strength in ("high", "medium") and l4_decision in (
        "weak_single_candidate",
        "semantic_unknown_but_strong_statistical_candidate",
    ):
        return "medium"
    return "low"


def compute_missing_evidence(
    l4_decision: str,
    normal_baseline_status: str,
    semantic_clarity: str,
    identifier_risk: str,
    high_cardinality: bool,
) -> List[str]:
    """Compute missing evidence list based on L4 decision."""
    missing = []
    if normal_baseline_status == "unobserved_missing":
        missing.append("normal_baseline_missing_for_this_field")
    if normal_baseline_status == "insufficient_sample":
        missing.append("normal_baseline_sample_insufficient")
    if semantic_clarity in ("low", "unknown"):
        missing.append("field_dictionary_or_semantic_mapping_needed")
    if identifier_risk == "possible":
        missing.append("identifier_uniqueness_verification_needed")
    if high_cardinality:
        missing.append("high_cardinality_field_distribution_detail_needed")
    if l4_decision == "normal_unobserved_need_baseline":
        missing.append("build_normal_baseline_for_source")
    if l4_decision == "semantic_unknown_but_strong_statistical_candidate":
        missing.append("semantic_mapping_before_feature_naming")
    if l4_decision == "result_signal_not_feature":
        missing.append("upstream_cause_feature_not_result_signal")
    if l4_decision == "identifier_anchor_not_feature":
        missing.append("generation_pattern_anomaly_evidence_if_used_as_feature")
    return missing


def compute_recommended_next_action(l4_decision: str) -> str:
    """Compute recommended next action based on L4 decision."""
    actions = {
        "strong_single_candidate": "enter_l5_evaluation; validate_with_larger_sample_and_stability_check",
        "weak_single_candidate": "enter_l5_evaluation; combine_with_other_signals_or_expand_sample",
        "semantic_unknown_but_strong_statistical_candidate": "field_dictionary_review_first; then_enter_l5; do_not_hardcode_field_meaning",
        "normal_unobserved_need_baseline": "build_normal_baseline_for_source; re_validate_after_baseline_available; do_not_output_high_confidence",
        "result_signal_not_feature": "use_as_signal_or_direction_only; find_upstream_cause_feature; do_not_use_as_primary_feature",
        "identifier_anchor_not_feature": "use_as_anchor_for_entity_resolution; do_not_use_as_risk_feature_unless_generation_pattern_anomaly_proven",
        "reject_or_hold": "hold_as_observation; do_not_enter_l5; revisit_if_new_evidence_or_larger_sample",
    }
    return actions.get(l4_decision, "no_action")


def validate_one_candidate(enriched: dict) -> dict:
    """Validate a single enriched L3 candidate and produce an L4 card."""
    # Extract fields from enriched candidate
    candidate_id = enriched.get("candidate_id", "unknown")
    raw_field_path = enriched.get("field_path", "")
    raw_source_name = enriched.get("source_name", "")
    source_name = raw_source_name
    field_value = str(enriched.get("field_value", ""))

    # v0.1.2: Normalize field_path using alias map
    field_path = normalize_field_path(raw_field_path, source_name)
    # v0.1.3: Apply source alias mapping
    if not source_name:
        source_name = infer_source_name(field_path, "")
    else:
        source_name = resolve_source(source_name).get("canonical_source", source_name)

    # v0.1.2: Track baseline lookup status
    baseline_hit = enriched.get("baseline_hit", False)
    if baseline_hit:
        baseline_lookup_status = "matched"
    elif raw_field_path != field_path and "." not in raw_field_path:
        # Field was a short name that we normalized → field_mapping_miss
        # (enricher didn't find it because it used the short name)
        baseline_lookup_status = "field_mapping_miss"
    elif source_name and raw_source_name and source_name != raw_source_name:
        # v0.1.3: Source alias mapping happened (e.g. login_logs_search → infra_user_action_log)
        # Enricher used original source_name, L4 uses mapped source_name
        # Mark as source_alias_resolved but enricher miss → needs re-lookup
        baseline_lookup_status = "source_alias_resolved_needs_relookup"
    else:
        # Canonical path but no baseline hit → true unobserved
        baseline_lookup_status = "unobserved_missing"

    # v0.1.3: high_cardinality must be determined early for normal_value_lookup_status
    high_cardinality = enriched.get("high_cardinality", False)

    # Risk-side stats
    risk_observed_count = enriched.get("risk_covered_count", enriched.get("risk_sample_count", 0))
    risk_hit_count = enriched.get("risk_value_count", 0)
    risk_hit_rate = enriched.get("risk_value_ratio", 0.0)

    # Normal-side stats
    normal_observed_count = enriched.get("normal_covered_count", 0) or 0
    normal_hit_count = enriched.get("normal_value_count", 0) or 0

    # v0.1.3: Determine normal_value_lookup_status
    # This tracks whether the candidate's specific value was evaluated.
    enricher_value_lookup = enriched.get("normal_value_lookup_status", "")
    if enricher_value_lookup:
        # Enricher already computed this (v0.1.3 enricher)
        normal_value_lookup_status = enricher_value_lookup
    else:
        # Infer from available data
        if high_cardinality:
            normal_value_lookup_status = "high_cardinality_skipped"
        elif not baseline_hit:
            if baseline_lookup_status == "source_alias_resolved_needs_relookup":
                normal_value_lookup_status = "source_or_schema_unresolved"
            else:
                normal_value_lookup_status = "field_unobserved"
        elif enriched.get("normal_value_ratio") is not None:
            # enricher found a specific value match
            normal_value_lookup_status = "value_matched"
        elif enriched.get("normal_value_count") is not None:
            # enricher evaluated value but it wasn't found in top-N
            normal_value_lookup_status = "value_not_found_in_top"
        elif normal_observed_count > 0 and not field_value:
            # Field exists in baseline but no specific value was provided for lookup
            normal_value_lookup_status = "field_matched_but_value_not_evaluated"
        else:
            normal_value_lookup_status = "field_matched_but_value_not_evaluated"

    # Compute normal_hit_rate
    # v0.1.3: Only use normal_hit_rate for decision-making if value-level was evaluated
    if normal_value_lookup_status == "normal_value_distribution_incomplete":
        normal_hit_rate = None
    elif normal_observed_count > 0 and enriched.get("normal_value_ratio") is not None:
        normal_hit_rate = enriched["normal_value_ratio"]
    elif normal_value_lookup_status == "value_matched":
        normal_hit_rate = normal_hit_count / normal_observed_count if normal_observed_count > 0 else None
    elif normal_value_lookup_status == "field_matched_but_value_not_evaluated":
        # v0.1.3: Field coverage exists but no value-level contrast.
        # Use top1_ratio as a conservative upper bound for normal prevalence.
        # If top1_ratio is high, the field is common → normal_hit_rate should be high.
        # If we don't have top1_ratio, set normal_hit_rate to a conservative estimate.
        top1 = enriched.get("normal_top1_ratio")
        if top1 is not None:
            normal_hit_rate = top1  # conservative: use top1 as proxy for "how common is ANY value"
        else:
            normal_hit_rate = None
    elif normal_observed_count > 0:
        normal_hit_rate = normal_hit_count / normal_observed_count
    else:
        normal_hit_rate = None

    # Baseline status
    normal_baseline_status = classify_normal_baseline_status(
        normal_observed_count, normal_hit_count, risk_hit_rate)

    # Override with enricher-provided normal_status if available
    enricher_status = enriched.get("normal_status")
    if enricher_status and normal_baseline_status == "unobserved_missing" and enricher_status not in (None, "high_cardinality_field"):
        # enricher found some data but we calculated 0; use enricher's status
        if normal_observed_count == 0 and enriched.get("baseline_hit", False):
            # baseline_hit=true but covered_count=0; use enricher_status for mapping
            pass  # keep our computed status

    # Statistical strength (v0.1.3: pass normal_value_lookup_status)
    statistical_strength = classify_statistical_strength(
        risk_hit_rate, normal_baseline_status, normal_hit_rate, normal_value_lookup_status)

    # Semantic clarity
    is_unknown = enriched.get("is_unknown_field", False)
    semantic_clarity = classify_semantic_clarity(field_path, is_unknown)

    # Leakage risk (v0.1.2: pass source_name for source-aware action/result/decision)
    leakage_risk = classify_leakage_risk(field_path, field_value, source_name)

    # Identifier risk (v0.1.1: pass field_value for behavior/pattern detection)
    identifier_risk = classify_identifier_risk(field_path, field_value)
    # high_cardinality already determined above for normal_value_lookup_status
    if high_cardinality and identifier_risk == "none":
        identifier_risk = "possible"

    # L4 decision
    l4_decision = decide_l4_decision(
        statistical_strength, semantic_clarity, leakage_risk, identifier_risk,
        normal_baseline_status, risk_observed_count)

    # Confidence
    confidence = compute_confidence(normal_observed_count, statistical_strength, l4_decision)

    # Missing evidence
    missing_evidence = compute_missing_evidence(
        l4_decision, normal_baseline_status, semantic_clarity,
        identifier_risk, high_cardinality)

    # Recommended next action
    recommended_next_action = compute_recommended_next_action(l4_decision)

    # Build card
    card = {
        "candidate_id": candidate_id,
        "field_name": field_path,
        "source_name": source_name,
        "field_value_or_pattern": field_value if field_value else None,
        "risk_observed_count": risk_observed_count,
        "risk_hit_count": risk_hit_count,
        "risk_hit_rate": risk_hit_rate,
        "normal_observed_count": normal_observed_count,
        "normal_hit_count": normal_hit_count,
        "normal_hit_rate": normal_hit_rate,
        "normal_baseline_status": normal_baseline_status,
        "statistical_strength": statistical_strength,
        "semantic_clarity": semantic_clarity,
        "leakage_risk": leakage_risk,
        "identifier_risk": identifier_risk,
        "l4_decision": l4_decision,
        "confidence": confidence,
        "not_final_conclusion": True,
        "candidate_type_hint": None,  # reserved for L5
        "missing_evidence": missing_evidence,
        "recommended_next_action": recommended_next_action,
        "baseline_scope": enriched.get("baseline_scope", "unknown"),
        "baseline_caveat": enriched.get("baseline_caveat", ""),
        "baseline_lookup_status": baseline_lookup_status,  # v0.1.2
        "normal_value_lookup_status": normal_value_lookup_status,  # v0.1.3
        "normal_value_distribution_reliable": enriched.get("normal_value_distribution_reliable"),
        "normal_value_lookup_note": enriched.get("normal_value_lookup_note"),
        "normalized_value_key": enriched.get("normalized_value_key"),
        "raw_value": enriched.get("raw_value"),
        "normal_field_coverage_ratio": enriched.get("normal_coverage_ratio"),  # v0.1.3
        "original_field_path": raw_field_path if raw_field_path != field_path else None,  # v0.1.2
    }
    return card


def batch_validate(enriched_candidates: List[dict]) -> dict:
    """Validate a batch of enriched L3 candidates and produce L4 cards."""
    cards = []
    for ec in enriched_candidates:
        card = validate_one_candidate(ec)
        cards.append(card)

    # Build summary
    decision_dist = {}
    strength_dist = {}
    status_dist = {}
    baseline_lookup_dist = {}  # v0.1.2
    for card in cards:
        d = card["l4_decision"]
        decision_dist[d] = decision_dist.get(d, 0) + 1
        s = card["statistical_strength"]
        strength_dist[s] = strength_dist.get(s, 0) + 1
        ns = card["normal_baseline_status"]
        status_dist[ns] = status_dist.get(ns, 0) + 1
        bls = card.get("baseline_lookup_status", "unknown")
        baseline_lookup_dist[bls] = baseline_lookup_dist.get(bls, 0) + 1

    # Count actionable candidates (those entering L5)
    l5_eligible = sum(1 for c in cards if c["l4_decision"] in (
        "strong_single_candidate",
        "weak_single_candidate",
        "semantic_unknown_but_strong_statistical_candidate",
    ))

    summary = {
        "l4_version": L4_VERSION,
        "input_candidate_count": len(enriched_candidates),
        "output_card_count": len(cards),
        "l5_eligible_count": l5_eligible,
        "l4_decision_distribution": decision_dist,
        "statistical_strength_distribution": strength_dist,
        "normal_baseline_status_distribution": status_dist,
        "baseline_lookup_status_distribution": baseline_lookup_dist,  # v0.1.2
        "normal_value_lookup_status_distribution": {  # v0.1.3
            k: v for k, v in
            {s: sum(1 for c in cards if c.get("normal_value_lookup_status") == s)
             for s in NORMAL_VALUE_LOOKUP_STATUSES}.items()
            if v > 0
        },
        "boundary_rules": [
            "L4 does NOT produce structure candidates (L5 responsibility)",
            "L4 does NOT run unpredictability-anom (L5 responsibility)",
            "L4 does NOT do historical recall (L6-A responsibility)",
            "L4 does NOT do strategy recommendation (L6-B responsibility)",
            "normal_observed_count=0 produces confidence=low",
            "result_signal fields become result_signal_not_feature",
            "identifier fields become identifier_anchor_not_feature",
            "normal baseline is L4 external asset, not L5 main flow",
        ],
    }

    return {
        "l4_candidate_validation_cards": cards,
        "l4_validation_summary": summary,
    }


# ---- CLI ----

def main():
    parser = argparse.ArgumentParser(
        description="L4 candidate validator: validate L3 candidates against normal baseline"
    )
    parser.add_argument("--input-enriched",
                        help="Enriched candidates JSON from normal_baseline_enricher")
    parser.add_argument("--input-enriched-key",
                        default="enriched_candidates",
                        help="Key in input JSON containing the candidate array (default: enriched_candidates)")
    parser.add_argument("--output",
                        help="Output file for L4 validation cards JSON")
    parser.add_argument("--output-md",
                        help="Output file for L4 validation cards Markdown")
    args = parser.parse_args()

    if not args.input_enriched:
        parser.print_help()
        print("\nERROR: --input-enriched is required.", file=sys.stderr)
        sys.exit(1)

    # Load enriched candidates
    with open(args.input_enriched, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Support both plain array and keyed object
    if isinstance(data, list):
        candidates = data
    elif isinstance(data, dict):
        candidates = data.get(args.input_enriched_key, [])
        if not candidates:
            # Try common keys
            for key in ["enriched_candidates", "candidates", "l3_candidates"]:
                if key in data and isinstance(data[key], list):
                    candidates = data[key]
                    break
    else:
        print("ERROR: Unexpected input format", file=sys.stderr)
        sys.exit(1)

    print("L4 candidate validator — batch validate mode")
    print("  input: %d enriched candidates" % len(candidates))

    result = batch_validate(candidates)

    # Output JSON
    output_json = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_json)
        print("  output JSON: %s" % args.output)
    else:
        print(output_json)

    # Output Markdown
    if args.output_md:
        md = render_cards_markdown(result)
        with open(args.output_md, "w", encoding="utf-8") as f:
            f.write(md)
        print("  output MD: %s" % args.output_md)

    # Print summary
    summary = result["l4_validation_summary"]
    print("\nL4 validation summary:")
    print("  Input: %d candidates" % summary["input_candidate_count"])
    print("  Output: %d cards" % summary["output_card_count"])
    print("  L5 eligible: %d" % summary["l5_eligible_count"])
    print("  Decision distribution: %s" % summary["l4_decision_distribution"])
    print("  Statistical strength: %s" % summary["statistical_strength_distribution"])
    print("  Normal baseline status: %s" % summary["normal_baseline_status_distribution"])


def render_cards_markdown(result: dict) -> str:
    """Render L4 validation cards as a Markdown table."""
    cards = result["l4_candidate_validation_cards"]
    summary = result["l4_validation_summary"]

    lines = []
    lines.append("# L4 Candidate Validation Cards")
    lines.append("")
    lines.append("L4 = L3 单点候选 + normal baseline 的验证层")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append("- Input: %d candidates" % summary["input_candidate_count"])
    lines.append("- Output: %d validation cards" % summary["output_card_count"])
    lines.append("- L5 eligible: %d" % summary["l5_eligible_count"])
    lines.append("- Decision distribution: %s" % json.dumps(summary["l4_decision_distribution"], ensure_ascii=False))
    lines.append("- Statistical strength: %s" % json.dumps(summary["statistical_strength_distribution"], ensure_ascii=False))
    lines.append("- Normal baseline status: %s" % json.dumps(summary["normal_baseline_status_distribution"], ensure_ascii=False))
    lines.append("")

    lines.append("## L4 Boundary Rules")
    lines.append("")
    for rule in summary["boundary_rules"]:
        lines.append("- %s" % rule)
    lines.append("")

    lines.append("## Validation Cards")
    lines.append("")
    lines.append("| # | candidate_id | field_name | field_value | risk_hit_rate | normal_hit_rate | baseline_status | stat_strength | semantic | leakage | identifier | l4_decision | confidence |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for i, card in enumerate(cards, 1):
        val = card.get("field_value_or_pattern") or "-"
        if len(val) > 20:
            val = val[:17] + "..."
        nhr = card.get("normal_hit_rate")
        nhr_str = "%.3f" % nhr if nhr is not None else "N/A"
        lines.append("| %d | %s | %s | %s | %.3f | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            i, card["candidate_id"],
            card["field_name"][-40:], val,
            card["risk_hit_rate"], nhr_str,
            card["normal_baseline_status"],
            card["statistical_strength"],
            card["semantic_clarity"],
            card["leakage_risk"],
            card["identifier_risk"],
            card["l4_decision"],
            card["confidence"],
        ))

    lines.append("")
    lines.append("## Card Details")
    lines.append("")
    for card in cards:
        lines.append("### %s" % card["candidate_id"])
        lines.append("")
        lines.append("- **Field**: %s" % card["field_name"])
        lines.append("- **Source**: %s" % card["source_name"])
        lines.append("- **Value/Pattern**: %s" % (card.get("field_value_or_pattern") or "(field-level)"))
        lines.append("- **Risk**: %d/%d observed, hit_rate=%.3f" % (
            card["risk_hit_count"], card["risk_observed_count"], card["risk_hit_rate"]))
        nhr = card.get("normal_hit_rate")
        lines.append("- **Normal**: %d/%d observed, hit_rate=%s" % (
            card["normal_hit_count"], card["normal_observed_count"],
            "%.3f" % nhr if nhr is not None else "N/A"))
        lines.append("- **Baseline status**: %s" % card["normal_baseline_status"])
        lines.append("- **Statistical strength**: %s" % card["statistical_strength"])
        lines.append("- **Semantic clarity**: %s" % card["semantic_clarity"])
        lines.append("- **Leakage risk**: %s" % card["leakage_risk"])
        lines.append("- **Identifier risk**: %s" % card["identifier_risk"])
        lines.append("- **L4 decision**: **%s**" % card["l4_decision"])
        lines.append("- **Confidence**: %s" % card["confidence"])
        missing_str = ", ".join(card["missing_evidence"]) if card["missing_evidence"] else "(none)"
        lines.append("- **Missing evidence**: %s" % missing_str)
        lines.append("- **Next action**: %s" % card["recommended_next_action"])
        lines.append("- **not_final_conclusion**: %s" % card["not_final_conclusion"])
        lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    main()
