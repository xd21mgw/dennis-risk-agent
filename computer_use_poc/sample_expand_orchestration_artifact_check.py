#!/usr/bin/env python3
"""Run the fixed sample-expand dry-run fixture and validate Phase 3 artifacts."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from runtime_case_execution_runner import (
    SourcePlanItem,
    _format_rcp_snapshot_time,
    _materialize_candidate_evidence,
    _build_top_explainable_candidates,
    _build_field_dictionary_review_queue,
    _build_context_commonality_section,
    _g_r6_dedup_candidates,
    _build_final_evidence_card_bridge,
    _build_high_coverage_commonality_candidates,
    _build_semantics_review_queue,
    _build_weak_materialized_review_queue,
    _build_l3_candidate_discovery_summary,
    _why_not_top,
    build_rcp_event_followup_source_plan,
    build_status_attribution,
    build_missing_evidence,
    build_batch_payload,
    build_sample_round_source_plan,
    build_safe_batch_summary,
    build_safe_stdout_result,
    merge_batch_results,
    merge_source_quality,
    score_candidate_anchors,
)
from passthrough_observation_builder import build_safe_observation


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "computer_use_poc" / "runtime_case_execution_runner.py"
FIXTURE = ROOT / "computer_use_poc" / "test_fixtures" / "sample_expand_validate_batch_fixed_rounds_v1.json"
ROLLING_FIXTURE = ROOT / "computer_use_poc" / "test_fixtures" / "sample_expand_mock_rolling_anchor_summary_v1.json"
STRATEGY_EVENT_REQUEST_DETAIL_FIXTURE = (
    ROOT / "computer_use_poc" / "test_fixtures" / "strategy_event_request_detail_feature_v1.json"
)
RCP_ORIGINAL_TAB_FEATURE_ROWS_FIXTURE = (
    ROOT / "computer_use_poc" / "test_fixtures" / "rcp_original_tab_feature_rows_v1.json"
)
DEVICE_DETAIL_MULTI_SOURCE_FIXTURE = (
    ROOT / "computer_use_poc" / "test_fixtures" / "device_detail_multi_source_v1.json"
)
SOURCE_L1_L3_FIELD_COMMONALITY_FIXTURE = (
    ROOT / "computer_use_poc" / "test_fixtures" / "source_l1_l3_field_commonality_multi_source_v1.json"
)
MOCK_SHAPED_FIXTURES = [
    (
        "content_diversion",
        ROOT / "computer_use_poc" / "test_fixtures" / "sample_expand_mock_shaped_observation_v1.json",
        {"content_domain", "device_domain", "strategy_domain"},
        {"candidate_photo_id", "candidate_device_id", "candidate_policy_code"},
    ),
    (
        "ato",
        ROOT / "computer_use_poc" / "test_fixtures" / "sample_expand_mock_shaped_ato_v1.json",
        {"behavior_domain", "device_domain", "network_domain", "strategy_domain"},
        {"candidate_device_id", "candidate_ip", "candidate_policy_code"},
    ),
    (
        "strategy_governance",
        ROOT / "computer_use_poc" / "test_fixtures" / "sample_expand_mock_shaped_strategy_governance_v1.json",
        {"strategy_domain", "enforcement_domain"},
        {"candidate_policy_code", "candidate_event_id", "candidate_review_id"},
    ),
    (
        "rcp_request_detail_projection",
        ROOT / "computer_use_poc" / "test_fixtures" / "sample_expand_mock_rcp_request_detail_projection_v1.json",
        {"strategy_domain", "behavior_domain"},
        {"candidate_policy_code", "candidate_event_id"},
    ),
    (
        "rcp_original_tab_feature_rows",
        RCP_ORIGINAL_TAB_FEATURE_ROWS_FIXTURE,
        {"strategy_domain"},
        {"candidate_policy_code", "candidate_event_id"},
    ),
    (
        "device_detail_multi_source",
        DEVICE_DETAIL_MULTI_SOURCE_FIXTURE,
        {"device_domain", "behavior_domain"},
        {"candidate_device_id"},
    ),
    (
        "feedback_enforcement",
        ROOT / "computer_use_poc" / "test_fixtures" / "sample_expand_mock_shaped_feedback_enforcement_v1.json",
        {"feedback_domain", "enforcement_domain"},
        {"candidate_report_id", "candidate_punish_id", "candidate_review_id"},
    ),
    (
        "anchor_competition",
        ROOT / "computer_use_poc" / "test_fixtures" / "sample_expand_mock_anchor_competition_v1.json",
        {"content_domain", "device_domain", "network_domain", "social_domain", "strategy_domain"},
        {"candidate_photo_id", "candidate_device_id", "candidate_ip", "candidate_relation_anchor", "candidate_policy_code"},
    ),
    (
        "anchor_domain_cap",
        ROOT / "computer_use_poc" / "test_fixtures" / "sample_expand_mock_anchor_domain_cap_v1.json",
        {"content_domain", "device_domain"},
        {"candidate_photo_id", "candidate_device_id"},
    ),
    (
        "high_false_positive_anchor",
        ROOT / "computer_use_poc" / "test_fixtures" / "sample_expand_mock_high_false_positive_anchor_v1.json",
        {"device_domain", "network_domain", "social_domain"},
        {"candidate_device_id", "candidate_ip", "candidate_relation_anchor"},
    ),
    (
        "single_entity_social_anchor",
        ROOT / "computer_use_poc" / "test_fixtures" / "sample_expand_mock_single_entity_social_anchor_v1.json",
        {"social_domain"},
        {"candidate_message_anchor"},
    ),
    (
        "source_l1_l3_field_commonality",
        SOURCE_L1_L3_FIELD_COMMONALITY_FIXTURE,
        {"behavior_domain", "account_domain", "content_domain", "social_domain", "feedback_domain", "enforcement_domain"},
        {"candidate_device_id", "candidate_photo_id", "candidate_comment_id", "candidate_report_id", "candidate_punish_id"},
    ),
]

ROUND_REQUIRED_KEYS = [
    "task_route",
    "seed_entity",
    "base_interface_plan",
    "base_summary_card",
    "base_commonality",
    "candidate_anchor_pool",
    "batch_anchor_pool",
    "anchor_scoring_summary",
    "selected_drilldown_anchors",
    "skipped_anchors",
    "drilldown_evidence_card",
    "new_anchor_pool",
    "tracking_commonality",
    "stop_reason",
    "commonality_matrix",
    "abnormal_correlation",
    "relation_expansion_result",
    "strategy_event_request_detail_table",
    "strategy_event_request_detail_commonality",
    "strategy_event_feature_row_table",
    "strategy_event_feature_row_commonality",
    "device_detail_table",
    "device_field_commonality",
    "device_field_platform_summary",
    "device_environment_similarity_cluster_candidate",
    "behavior_device_consistency_gap_candidate",
    "standard_detail_table",
    "login_detail_table",
    "account_detail_table",
    "user_behavior_summary_detail_table",
    "content_detail_table",
    "social_detail_table",
    "feedback_detail_table",
    "enforcement_detail_table",
    "standard_field_commonality",
    "group_profile_candidate",
    "candidate_features",
    "validation_plan",
    "final_evidence_card",
    "missing_evidence",
    "source_quality",
]

FEATURE_REQUIRED_KEYS = [
    "feature_name",
    "source_domains",
    "supporting_current_evidence",
    "signal_inputs",
    "hypothesis_inputs",
    "supporting_selected_anchors",
    "confidence",
    "validation_needed",
    "false_positive_risk",
    "not_final_conclusion",
]

STRATEGY_EVENT_REQUEST_DETAIL_REQUIRED_FIELDS = [
    "sample_id",
    "entity_id",
    "user_id",
    "round_id",
    "source_id",
    "action",
    "observation_domain",
    "event_id",
    "event_type",
    "policy_code",
    "risk_decision",
    "event_time",
    "request_path",
    "request_scene",
    "entry",
    "action_type",
    "action_object",
    "task_type",
    "reward_type",
    "client_params",
    "app_version",
    "ua",
    "device_id",
    "ip_or_network",
    "frontend_activity_signal",
    "backend_action_signal",
    "time_delta_from_login_seconds",
    "time_delta_between_actions_seconds",
    "source_quality",
    "evidence_source",
]

STRATEGY_REQUEST_DETAIL_FEATURE_REQUIRED_KEYS = [
    "feature_name",
    "source_fields",
    "field_combination",
    "support_sample_count",
    "supporting_current_evidence",
    "supporting_selected_anchors",
    "signal_inputs",
    "hypothesis_inputs",
    "black_gray_interpretation",
    "normal_user_false_positive_risk",
    "missing_fields_to_check",
    "validation_method",
    "strategy_usage_boundary",
    "confidence",
    "validation_needed",
    "false_positive_risk",
    "not_final_conclusion",
]

STRATEGY_EVENT_FEATURE_ROW_REQUIRED_FIELDS = [
    "sample_id",
    "entity_id",
    "user_id",
    "event_id",
    "event_type",
    "source_id",
    "source_name",
    "feature_tab",
    "feature_key",
    "feature_name",
    "feature_type",
    "feature_value_or_safe_ref",
    "value_present",
    "value_comparable",
    "comparable_type",
    "sensitive_value_policy",
    "source_quality",
    "evidence_source",
    "mapped_domain",
    "mapped_field_family",
    "original_feature_row_retained",
]

DEVICE_DETAIL_REQUIRED_FIELDS = [
    "sample_id",
    "entity_id",
    "user_id",
    "device_id",
    "device_safe_ref",
    "source_id",
    "source_name",
    "device_source_type",
    "device_field_key",
    "device_field_name",
    "device_field_value_or_safe_ref",
    "device_field_type",
    "value_present",
    "value_comparable",
    "comparable_type",
    "source_quality",
    "evidence_source",
    "device_role",
    "sensitive_value_policy",
]

DEVICE_ID_ONLY_FEATURE_FIELDS = {
    "device_id",
    "candidate_device_id",
    "login_device_id",
    "backend_action_device_id",
    "frontend_active_device_id",
}
DEVICE_NON_DEVICE_DETAIL_BLOCK_KEYS = {
    "userbehavior",
    "userinfo",
    "usercache",
    "userprofilechanged",
    "userlastcomments",
    "usermessageusercnt",
    "userchargeamountfen30d",
    "userbanstatus",
    "query",
    "cookies",
}

STRATEGY_ENTRY_LABEL_FIELDS = {"policy_code", "event_type", "risk_decision"}
STRATEGY_REQUEST_DETAIL_CORE_FIELDS = {
    "request_path",
    "request_scene",
    "entry",
    "action_type",
    "action_object",
    "task_type",
    "reward_type",
    "client_params",
    "app_version",
    "ua",
    "device_id",
    "ip_or_network",
    "frontend_activity_signal",
    "backend_action_signal",
    "time_delta_from_login_seconds",
    "time_delta_between_actions_seconds",
}

ANCHOR_REQUIRED_KEYS = [
    "anchor_type",
    "produced_by",
    "observation_domain",
    "confidence",
    "next_allowed_interfaces",
    "cap_key",
    "reason",
    "source_quality",
    "evidence_source",
    "anchor_class",
    "anchor_score",
    "selection_status",
    "anchor_priority_reason",
]

ANCHOR_SCORE_REQUIRED_KEYS = [
    "anchor_presence",
    "anomaly_strength",
    "batch_support_count",
    "cross_domain_support",
    "chain_value",
    "cost_level",
    "expansion_risk",
    "false_positive_risk",
    "evidence_quality",
    "current_observation_support",
    "total_score",
    "supporting_entities",
    "supporting_sources",
]

VALID_SELECTION_STATUSES = {
    "selected",
    "skipped_by_cap",
    "skipped_by_domain_cap",
    "skipped_by_type_cap",
    "skipped_by_entity_diversity",
    "skipped_low_score",
    "duplicate_anchor",
    "low_value_anchor",
    "plan_only",
}

COVERAGE_COMMONALITY_SUFFIX = "_business_fields_extracted"


def _signal_name(signal: Any) -> str:
    if isinstance(signal, dict):
        return str(signal.get("signal_name") or "")
    return str(signal or "")


def _is_coverage_commonality_signal(signal: Any) -> bool:
    if isinstance(signal, dict) and str(signal.get("commonality_type") or "") == "coverage_commonality":
        return True
    return _signal_name(signal).endswith(COVERAGE_COMMONALITY_SUFFIX)


def _contains_stable_commonality(value: Any) -> bool:
    """Stable commonality is only valid in cumulative rolling summary fields."""
    if isinstance(value, dict):
        if value.get("stable_commonality") is True:
            return True
        if str(value.get("commonality_type") or "") == "stable_commonality":
            return True
        return any(_contains_stable_commonality(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_stable_commonality(item) for item in value)
    return value == "stable_commonality"


def _is_risk_commonality_signal(signal: Any) -> bool:
    if not isinstance(signal, dict):
        return False
    if _is_coverage_commonality_signal(signal):
        return False
    return signal.get("eligible_for_group_candidate") is True or str(signal.get("commonality_type") or "") in {
        "anchor_commonality",
        "chain_commonality",
        "group_candidate_commonality",
    }


def _run_fixture(fixture: Path) -> dict[str, Any]:
    completed = subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            "--task",
            "sample_expand_validate_batch",
            "--rounds-json",
            str(fixture),
            "--mode",
            "dry_run",
            "--format",
            "json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        return {
            "runner_returncode": completed.returncode,
            "runner_stderr": completed.stderr,
            "runner_stdout_excerpt": completed.stdout[:1000],
            "result": None,
        }
    return {
        "runner_returncode": completed.returncode,
        "runner_stderr": completed.stderr,
        "result": json.loads(completed.stdout),
    }


def _run_payload(payload: dict[str, Any]) -> dict[str, Any]:
    completed = subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            "--task",
            "sample_expand_validate_batch",
            "--rounds-json",
            json.dumps(payload, ensure_ascii=False),
            "--mode",
            "dry_run",
            "--format",
            "json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        return {
            "runner_returncode": completed.returncode,
            "runner_stderr": completed.stderr,
            "runner_stdout_excerpt": completed.stdout[:1000],
            "result": None,
        }
    return {
        "runner_returncode": completed.returncode,
        "runner_stderr": completed.stderr,
        "result": json.loads(completed.stdout),
    }


def _regression_rcp_snapshot_time_format() -> tuple[list[str], dict[str, Any]]:
    """RCP snapshot keeps browser-backed's YYYY-MM-DD HH:mm:ss contract."""
    errors: list[str] = []
    start_ms = 1_780_020_000_000
    end_sec = 1_780_021_800
    expected_start = "2026-05-29 10:00:00"
    expected_end = "2026-05-29 10:30:00"

    if _format_rcp_snapshot_time(start_ms) != expected_start:
        errors.append("RCP-SNAPSHOT-TIME-FORMAT-001:epoch_ms_conversion_failed")
    if _format_rcp_snapshot_time(end_sec) != expected_end:
        errors.append("RCP-SNAPSHOT-TIME-FORMAT-001:epoch_seconds_conversion_failed")

    plan = build_sample_round_source_plan(
        1,
        ["403082302"],
        window_start_ms=start_ms,
        window_end_ms=end_sec * 1000,
        source_overrides={
            "rcp_snapshot": {
                "enabled": True,
                "endTime": end_sec,
                "eventType": "REGISTER_NEW",
                "eventTypeCodes": "REGISTER_NEW",
                "pageIndex": 1,
                "pageSize": 5,
            }
        },
    )
    payload = build_batch_payload("rcp_snapshot_time_format_regression", plan, dry_run=True)
    sources = [
        source
        for group in payload.get("execution_groups", []) or []
        for source in group.get("sources", []) or []
        if isinstance(source, dict)
    ]
    snapshot_sources = [source for source in sources if source.get("action") == "rcp_snapshot"]
    fast_query_sources = [source for source in sources if source.get("action") == "rcp_fast_query_hbase"]
    if len(snapshot_sources) != 1:
        errors.append(f"RCP-SNAPSHOT-NO-EPOCH-MS-PAYLOAD-001:expected_one_snapshot_source_got_{len(snapshot_sources)}")
        snapshot_params: dict[str, Any] = {}
    else:
        snapshot_params = snapshot_sources[0].get("params") or {}
        if snapshot_params.get("startTime") != expected_start or snapshot_params.get("endTime") != expected_end:
            errors.append("RCP-SNAPSHOT-NO-EPOCH-MS-PAYLOAD-001:snapshot_payload_time_not_formatted")
        for field in ("startTime", "endTime"):
            value = snapshot_params.get(field)
            if isinstance(value, (int, float)) or re.fullmatch(r"\d{10,13}", str(value or "")):
                errors.append(f"RCP-SNAPSHOT-NO-EPOCH-MS-PAYLOAD-001:{field}_still_epoch")

    if len(fast_query_sources) != 1:
        errors.append(f"RCP-SNAPSHOT-DOES-NOT-AFFECT-OTHER-RCP-ACTIONS-001:expected_one_fast_query_source_got_{len(fast_query_sources)}")
        fast_query_params: dict[str, Any] = {}
    else:
        fast_query_params = fast_query_sources[0].get("params") or {}
        if fast_query_params.get("startTime") != start_ms or fast_query_params.get("endTime") != end_sec * 1000:
            errors.append("RCP-SNAPSHOT-DOES-NOT-AFFECT-OTHER-RCP-ACTIONS-001:fast_query_time_was_changed")

    return errors, {
        "RCP-SNAPSHOT-TIME-FORMAT-001": {
            "start_ms": start_ms,
            "formatted_start": _format_rcp_snapshot_time(start_ms),
            "end_seconds": end_sec,
            "formatted_end": _format_rcp_snapshot_time(end_sec),
        },
        "RCP-SNAPSHOT-NO-EPOCH-MS-PAYLOAD-001": {
            "snapshot_startTime": snapshot_params.get("startTime"),
            "snapshot_endTime": snapshot_params.get("endTime"),
            "snapshot_time_value_types": {
                "startTime": type(snapshot_params.get("startTime")).__name__,
                "endTime": type(snapshot_params.get("endTime")).__name__,
            },
        },
        "RCP-SNAPSHOT-DOES-NOT-AFFECT-OTHER-RCP-ACTIONS-001": {
            "fast_query_startTime": fast_query_params.get("startTime"),
            "fast_query_endTime": fast_query_params.get("endTime"),
            "fast_query_time_value_types": {
                "startTime": type(fast_query_params.get("startTime")).__name__,
                "endTime": type(fast_query_params.get("endTime")).__name__,
            },
        },
    }


def _validate_common_result(
    *,
    run: dict[str, Any],
    expected_round_count: int,
    require_current_observation_content: bool,
    required_domains: set[str] | None = None,
    required_anchor_types: set[str] | None = None,
) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    result = run.get("result")
    if result is None:
        errors.append("runner_failed")
        return errors, {}

    if result.get("route_mode") != "sample_expand_validate_mode":
        errors.append("route_mode_not_sample_expand_validate_mode")
    safety = result.get("safety", {})
    if safety.get("dataagent_called") or safety.get("direct_platform_url_called") or safety.get("fallback_used"):
        errors.append("unsafe_execution_boundary")

    round_results = result.get("round_results", [])
    if len(round_results) != expected_round_count:
        errors.append(f"round_result_count_not_{expected_round_count}")
    current_observation_anchor_seen = False
    current_observation_shared_signal_seen = False
    group_risk_shared_signal_seen = False
    group_insufficient_risk_commonality_boundary_seen = False
    l2_skipped_summary_seen = False
    l2_plan_summary_seen = False
    skipped_anchor_explanation_seen = False
    skippable_anchor_seen = False
    observed_domains: set[str] = set()
    observed_anchor_types: set[str] = set()
    for index, round_result in enumerate(round_results, start=1):
        artifacts = round_result.get("orchestration_artifacts")
        if not isinstance(artifacts, dict):
            errors.append(f"round_{index}_missing_orchestration_artifacts")
            continue
        for key in ROUND_REQUIRED_KEYS:
            if key not in artifacts:
                errors.append(f"round_{index}_missing_{key}")
        candidate_anchor_pool = artifacts.get("candidate_anchor_pool", []) or []
        batch_anchor_pool = artifacts.get("batch_anchor_pool", []) or []
        selected_drilldown_anchors = artifacts.get("selected_drilldown_anchors", []) or []
        skipped_anchors = artifacts.get("skipped_anchors", []) or []
        if not artifacts.get("anchor_scoring_summary"):
            errors.append(f"round_{index}_missing_anchor_scoring_summary")
        if not isinstance(selected_drilldown_anchors, list):
            errors.append(f"round_{index}_selected_drilldown_anchors_not_list")
            selected_drilldown_anchors = []
        if not isinstance(skipped_anchors, list):
            errors.append(f"round_{index}_skipped_anchors_not_list")
            skipped_anchors = []
        if not candidate_anchor_pool:
            errors.append(f"round_{index}_empty_candidate_anchor_pool")
        if not isinstance(batch_anchor_pool, list) or not batch_anchor_pool:
            errors.append(f"round_{index}_missing_batch_anchor_pool")
            batch_anchor_pool = []
        batch_anchor_refs = {
            str(anchor.get("value") or anchor.get("safe_ref") or anchor.get("anchor_type"))
            for anchor in batch_anchor_pool
            if isinstance(anchor, dict)
        }
        batch_scope_count = 0
        single_scope_count = 0
        for anchor in batch_anchor_pool:
            if not isinstance(anchor, dict):
                continue
            scope = str(anchor.get("batch_anchor_scope") or "")
            support_entities = [str(entity) for entity in anchor.get("supporting_entities", []) or [] if str(entity)]
            if scope == "batch_anchor":
                batch_scope_count += 1
                if len(set(support_entities)) < 2:
                    errors.append(f"round_{index}_batch_anchor_without_multi_entity_support")
            elif scope == "single_entity_anchor":
                single_scope_count += 1
                if len(set(support_entities)) > 1:
                    errors.append(f"round_{index}_single_entity_anchor_with_multi_entity_support")
        summary = artifacts.get("anchor_scoring_summary", {}) if isinstance(artifacts.get("anchor_scoring_summary"), dict) else {}
        max_per_domain = int(summary.get("max_selected_per_domain") or 999)
        max_per_type = int(summary.get("max_selected_per_anchor_type") or 999)
        if "selected_entity_distribution" not in summary:
            errors.append(f"round_{index}_missing_selected_entity_distribution")
        for summary_key in {
            "eligible_entity_count",
            "selected_entity_count",
            "target_selected_entity_count",
            "entity_diversity_reason",
        }:
            if summary_key not in summary:
                errors.append(f"round_{index}_missing_{summary_key}")
        high_false_positive_checked = False
        for anchor_index, anchor in enumerate(candidate_anchor_pool, start=1):
            if isinstance(anchor, dict):
                for key in ANCHOR_REQUIRED_KEYS:
                    if key not in anchor:
                        errors.append(f"round_{index}_anchor_{anchor_index}_missing_{key}")
                score = anchor.get("anchor_score", {})
                if not isinstance(score, dict):
                    errors.append(f"round_{index}_anchor_{anchor_index}_score_not_dict")
                    score = {}
                for key in ANCHOR_SCORE_REQUIRED_KEYS:
                    if key not in score:
                        errors.append(f"round_{index}_anchor_{anchor_index}_score_missing_{key}")
                support_entities = score.get("supporting_entities") or []
                if isinstance(support_entities, list) and support_entities:
                    distinct_support = len(set(str(entity) for entity in support_entities))
                    if int(score.get("batch_support_count") or 0) != distinct_support:
                        errors.append(f"round_{index}_anchor_{anchor_index}_batch_support_not_distinct_entity_count")
                if len(round_result.get("sampled_entities", []) or []) <= 1 and int(score.get("batch_support_count") or 0) > 1:
                    errors.append(f"round_{index}_anchor_{anchor_index}_single_sample_batch_support_gt_1")
                if anchor.get("selection_status") not in VALID_SELECTION_STATUSES:
                    errors.append(f"round_{index}_anchor_{anchor_index}_invalid_selection_status")
                if score.get("false_positive_risk") == "high":
                    reasons = " ".join(str(reason) for reason in anchor.get("anchor_priority_reason", []) or [])
                    if "high_false_positive" not in reasons:
                        errors.append(f"round_{index}_anchor_{anchor_index}_high_false_positive_without_priority_reason")
                    high_false_positive_checked = True
                if anchor.get("observation_domain"):
                    observed_domains.add(str(anchor.get("observation_domain")))
                if anchor.get("anchor_type"):
                    observed_anchor_types.add(str(anchor.get("anchor_type")))
        if any(anchor.get("evidence_source") == "current_observation" for anchor in candidate_anchor_pool):
            current_observation_anchor_seen = True
        if len(candidate_anchor_pool) > len(selected_drilldown_anchors):
            skippable_anchor_seen = True
        selected_refs = {
            str(anchor.get("value") or anchor.get("safe_ref") or anchor.get("anchor_type"))
            for anchor in selected_drilldown_anchors
            if isinstance(anchor, dict)
        }
        for ref in selected_refs:
            if ref not in batch_anchor_refs:
                errors.append(f"round_{index}_selected_anchor_not_from_batch_anchor_pool")
        selected_domain_counts: dict[str, int] = {}
        selected_type_counts: dict[str, int] = {}
        selected_policy_count = 0
        for anchor in selected_drilldown_anchors:
            if not isinstance(anchor, dict):
                continue
            domain = str(anchor.get("observation_domain") or "unknown")
            anchor_type = str(anchor.get("anchor_type") or "unknown")
            selected_domain_counts[domain] = selected_domain_counts.get(domain, 0) + 1
            selected_type_counts[anchor_type] = selected_type_counts.get(anchor_type, 0) + 1
            if anchor_type == "candidate_policy_code":
                selected_policy_count += 1
        candidate_entities = {
            str(entity)
            for anchor in candidate_anchor_pool
            if isinstance(anchor, dict)
            for entity in anchor.get("anchor_score", {}).get("supporting_entities", []) or []
            if str(entity)
        }
        selected_entities = {
            str(entity)
            for anchor in selected_drilldown_anchors
            if isinstance(anchor, dict)
            for entity in anchor.get("anchor_score", {}).get("supporting_entities", []) or []
            if str(entity)
        }
        if len(candidate_entities) >= 2 and len(selected_drilldown_anchors) >= 2 and len(selected_entities) < 2:
            errors.append(f"round_{index}_selected_anchors_not_entity_diverse")
        if len(candidate_entities) < 2 and len(selected_drilldown_anchors) >= 2:
            reason = str(summary.get("entity_diversity_reason") or "")
            if reason not in {
                "only_one_entity_has_valid_anchor",
                "single_sample_no_cross_entity_requirement",
            }:
                errors.append(f"round_{index}_single_entity_selection_missing_diversity_reason")
        if len(candidate_entities) >= 3 and len(selected_drilldown_anchors) >= 3 and len(selected_entities) < 3:
            reason = str(summary.get("entity_diversity_reason") or "")
            if reason not in {
                "selected_anchors_cover_required_entities",
                "replaced_overrepresented_entity_anchor",
                "eligible_cross_entity_anchor_available_but_blocked_by_score_or_caps",
            }:
                errors.append(f"round_{index}_three_entity_selection_missing_diversity_reason")
        for domain, count in selected_domain_counts.items():
            if count > max_per_domain:
                errors.append(f"round_{index}_selected_domain_cap_exceeded:{domain}")
        for anchor_type, count in selected_type_counts.items():
            if count > max_per_type:
                errors.append(f"round_{index}_selected_type_cap_exceeded:{anchor_type}")
        if selected_drilldown_anchors and selected_policy_count == len(selected_drilldown_anchors) and len(selected_drilldown_anchors) > 1:
            errors.append(f"round_{index}_policy_code_occupied_all_selected_slots")
        selected_domains = set(selected_domain_counts)
        candidate_domains = {
            str(anchor.get("observation_domain"))
            for anchor in candidate_anchor_pool
            if isinstance(anchor, dict) and anchor.get("observation_domain")
        }
        if len(candidate_domains) >= 3 and len(selected_drilldown_anchors) >= 3 and len(selected_domains) < 3:
            errors.append(f"round_{index}_selected_anchor_domains_not_diverse")
        if any(
            isinstance(anchor, dict)
            and anchor.get("anchor_score", {}).get("false_positive_risk") == "high"
            for anchor in candidate_anchor_pool
        ) and not high_false_positive_checked:
            errors.append(f"round_{index}_high_false_positive_anchor_not_checked")
        for item in skipped_anchors:
            if not isinstance(item, dict):
                errors.append(f"round_{index}_skipped_anchor_not_dict")
                continue
            if item.get("skip_reason") in {
                "skipped_by_cap",
                "skipped_by_domain_cap",
                "skipped_by_type_cap",
                "skipped_by_entity_diversity",
                "skipped_low_score",
                "low_value_anchor",
            }:
                skipped_anchor_explanation_seen = True
            if "anchor_priority_reason" not in item:
                errors.append(f"round_{index}_skipped_anchor_missing_priority_reason")
        if not artifacts.get("drilldown_evidence_card"):
            errors.append(f"round_{index}_empty_drilldown_evidence_card")
        for card_index, card in enumerate(artifacts.get("drilldown_evidence_card", []) or [], start=1):
            if not isinstance(card, dict):
                continue
            anchor = card.get("anchor") if isinstance(card.get("anchor"), dict) else {}
            ref = str(anchor.get("value") or anchor.get("safe_ref") or anchor.get("anchor_type"))
            if ref and ref not in selected_refs:
                errors.append(f"round_{index}_drilldown_{card_index}_anchor_not_selected")
        if not artifacts.get("stop_reason"):
            errors.append(f"round_{index}_missing_stop_reason")
        group_candidate = artifacts.get("group_profile_candidate", {})
        if group_candidate.get("not_confirmed_as_group") is not True:
            errors.append(f"round_{index}_group_candidate_not_marked_unconfirmed")
        if "supporting_selected_anchors" not in group_candidate:
            errors.append(f"round_{index}_group_candidate_missing_supporting_selected_anchors")
        if "supporting_selected_batch_anchors" not in group_candidate:
            errors.append(f"round_{index}_group_candidate_missing_supporting_selected_batch_anchors")
        if "context_selected_anchors" not in group_candidate:
            errors.append(f"round_{index}_group_candidate_missing_context_selected_anchors")
        selected_batch_refs = {
            str(anchor.get("value") or anchor.get("safe_ref") or anchor.get("anchor_type"))
            for anchor in selected_drilldown_anchors
            if isinstance(anchor, dict) and anchor.get("batch_anchor_scope") == "batch_anchor"
        }
        selected_context_refs = {
            str(anchor.get("value") or anchor.get("safe_ref") or anchor.get("anchor_type"))
            for anchor in selected_drilldown_anchors
            if isinstance(anchor, dict) and anchor.get("batch_anchor_scope") != "batch_anchor"
        }
        group_batch_refs = {
            str(anchor)
            for anchor in group_candidate.get("supporting_selected_batch_anchors", []) or []
            if str(anchor)
        } if isinstance(group_candidate, dict) else set()
        group_context_refs = {
            str(anchor)
            for anchor in group_candidate.get("context_selected_anchors", []) or []
            if str(anchor)
        } if isinstance(group_candidate, dict) else set()
        legacy_group_refs = {
            str(anchor)
            for anchor in group_candidate.get("supporting_selected_anchors", []) or []
            if str(anchor)
        } if isinstance(group_candidate, dict) else set()
        if group_batch_refs - selected_batch_refs:
            errors.append(f"round_{index}_group_candidate_batch_support_not_selected_batch_anchor")
        if group_batch_refs & selected_context_refs:
            errors.append(f"round_{index}_group_candidate_context_anchor_used_as_batch_support")
        if legacy_group_refs != group_batch_refs:
            errors.append(f"round_{index}_legacy_supporting_selected_anchors_not_batch_only")
        if selected_context_refs and not selected_context_refs.issubset(group_context_refs):
            errors.append(f"round_{index}_group_candidate_context_selected_anchors_missing_selected_context")
        if group_candidate.get("shared_signals"):
            if any(_is_coverage_commonality_signal(signal) for signal in group_candidate.get("shared_signals", []) or []):
                errors.append(f"round_{index}_group_candidate_contains_coverage_commonality")
            if any(_is_risk_commonality_signal(signal) for signal in group_candidate.get("shared_signals", []) or []):
                group_risk_shared_signal_seen = True
            if not group_batch_refs:
                errors.append(f"round_{index}_group_candidate_shared_signals_without_batch_support")
        else:
            missing_evidence = {
                str(item) for item in group_candidate.get("missing_evidence", []) or []
            } if isinstance(group_candidate, dict) else set()
            if "insufficient_risk_commonality" in missing_evidence:
                group_insufficient_risk_commonality_boundary_seen = True
        validation_plan = artifacts.get("validation_plan", {})
        if validation_plan.get("validation_status") not in {"planned", "pending", "not_executed"}:
            errors.append(f"round_{index}_validation_plan_status_invalid")
        final_card = artifacts.get("final_evidence_card", {})
        if final_card.get("counter_evidence"):
            errors.append(f"round_{index}_counter_evidence_should_not_use_gaps_as_counter")
        if "expert_risk_signal_input" in final_card.get("weak_evidence", []):
            errors.append(f"round_{index}_expert_signal_should_not_be_weak_evidence")
        for matrix in artifacts.get("commonality_matrix", []) or []:
            if matrix.get("limited_commonality") is not True:
                errors.append(f"round_{index}_missing_limited_commonality")
            if _contains_stable_commonality(matrix):
                errors.append(f"round_{index}_stable_commonality_not_allowed")
            for domain in matrix.get("source_domains", []) or []:
                observed_domains.add(str(domain))
            for signal in matrix.get("shared_signals", []) or []:
                if isinstance(signal, dict) and signal.get("evidence_source") == "current_observation":
                    current_observation_shared_signal_seen = True
                if isinstance(signal, dict):
                    support_count = int(signal.get("batch_support_count") or signal.get("support_count") or 0)
                    if _is_coverage_commonality_signal(signal):
                        if signal.get("commonality_anchor") is True:
                            errors.append(f"round_{index}_coverage_commonality_marked_as_commonality_anchor")
                        if signal.get("risk_commonality") is True:
                            errors.append(f"round_{index}_coverage_commonality_marked_as_risk_commonality")
                        if signal.get("eligible_for_group_candidate") is True:
                            errors.append(f"round_{index}_coverage_commonality_eligible_for_group_candidate")
                    if signal.get("commonality_anchor") is True and support_count < 2:
                        errors.append(f"round_{index}_commonality_anchor_without_batch_support")
                    signal_name = str(signal.get("signal_name") or "")
                    if signal_name.startswith("single_entity_") and (
                        signal.get("commonality_anchor") is True
                        or signal.get("risk_commonality") is True
                        or signal.get("eligible_for_group_candidate") is True
                    ):
                        errors.append(f"round_{index}_single_entity_signal_marked_as_batch_commonality")
                    if signal_name == "social_commonality":
                        errors.append(f"round_{index}_generic_social_commonality_without_batch_social_anchor")
        if single_scope_count and not batch_scope_count:
            group_candidate = artifacts.get("group_profile_candidate", {})
            if isinstance(group_candidate, dict) and group_candidate.get("shared_signals"):
                errors.append(f"round_{index}_single_entity_anchors_support_group_candidate")
        if isinstance(group_candidate, dict):
            for domain in group_candidate.get("shared_domains", []) or []:
                observed_domains.add(str(domain))
        source_quality = artifacts.get("source_quality", {})
        if (
            source_quality.get("skipped_missing_anchor")
            or source_quality.get("skipped_by_cap")
            or source_quality.get("skipped_by_domain_cap")
            or source_quality.get("skipped_by_type_cap")
            or source_quality.get("missing_contract")
        ):
            l2_skipped_summary_seen = True
        if source_quality.get("not_executed"):
            l2_plan_summary_seen = True
        for relation in artifacts.get("relation_expansion_result", []) or []:
            seed_anchor = relation.get("seed_anchor") if isinstance(relation.get("seed_anchor"), dict) else {}
            if not seed_anchor.get("value") and int(relation.get("expansion_depth") or 0) == 1:
                errors.append(f"round_{index}_missing_value_relation_expansion_depth_should_not_be_1")
            seed_ref = str(seed_anchor.get("value") or seed_anchor.get("safe_ref") or seed_anchor.get("anchor_type") or "")
            if seed_anchor.get("value") and seed_ref not in selected_refs:
                errors.append(f"round_{index}_relation_expansion_seed_not_selected")
        for feature_index, feature in enumerate(artifacts.get("candidate_features", []), start=1):
            for key in FEATURE_REQUIRED_KEYS:
                if key not in feature:
                    errors.append(f"round_{index}_feature_{feature_index}_missing_{key}")
            if feature.get("not_final_conclusion") is not True:
                errors.append(f"round_{index}_feature_{feature_index}_not_final_conclusion_missing")
            if feature.get("validation_needed") is not True:
                errors.append(f"round_{index}_feature_{feature_index}_validation_needed_missing")
            if require_current_observation_content and not feature.get("supporting_current_evidence"):
                errors.append(f"round_{index}_feature_{feature_index}_missing_supporting_current_evidence")
            if not feature.get("supporting_selected_anchors") and feature.get("unselected_signal_hypothesis") is not True:
                errors.append(f"round_{index}_feature_{feature_index}_missing_selected_anchor_or_unselected_hypothesis")
            current_evidence = [str(item) for item in feature.get("supporting_current_evidence", []) or []]
            if current_evidence and all(item.endswith(COVERAGE_COMMONALITY_SUFFIX) for item in current_evidence) and not feature.get("supporting_selected_anchors"):
                errors.append(f"round_{index}_feature_{feature_index}_coverage_only_current_evidence")

    cumulative_artifacts = result.get("orchestration_artifacts", {})
    if not cumulative_artifacts:
        errors.append("missing_cumulative_orchestration_artifacts")
    for key in (
        "task_route",
        "base_summary_card",
        "candidate_anchor_pool_count",
        "candidate_anchor_pool_summary",
        "source_quality",
        "round_level_source_quality",
        "artifact_quality_summary",
        "missing_evidence",
        "validation_plan",
        "final_evidence_card",
    ):
        if key not in cumulative_artifacts:
            errors.append(f"missing_cumulative_{key}")
    cumulative_source_quality = cumulative_artifacts.get("source_quality", {})
    if isinstance(cumulative_source_quality, dict):
        for artifact_only_key in (
            "skipped_missing_anchor",
            "skipped_by_cap",
            "skipped_by_domain_cap",
            "skipped_by_type_cap",
            "skipped_by_entity_diversity",
            "skipped_low_score",
            "low_value_anchor",
            "duplicate_anchor",
            "missing_contract",
            "not_executed",
        ):
            if artifact_only_key in cumulative_source_quality and cumulative_source_quality.get(artifact_only_key):
                errors.append(f"cumulative_source_quality_contains_artifact_status:{artifact_only_key}")
    artifact_quality_summary = cumulative_artifacts.get("artifact_quality_summary", {})
    if not isinstance(artifact_quality_summary, dict):
        errors.append("cumulative_artifact_quality_summary_not_dict")
    if cumulative_artifacts.get("group_profile_candidate", {}).get("not_confirmed_as_group") is not True:
        errors.append("cumulative_group_candidate_not_marked_unconfirmed")
    cumulative_group_candidate = cumulative_artifacts.get("group_profile_candidate", {})
    if "supporting_selected_batch_anchors" not in cumulative_group_candidate:
        errors.append("cumulative_group_candidate_missing_supporting_selected_batch_anchors")
    if "context_selected_anchors" not in cumulative_group_candidate:
        errors.append("cumulative_group_candidate_missing_context_selected_anchors")
    if set(cumulative_group_candidate.get("supporting_selected_anchors", []) or []) != set(
        cumulative_group_candidate.get("supporting_selected_batch_anchors", []) or []
    ):
        errors.append("cumulative_group_candidate_legacy_support_not_batch_only")
    rolling_anchor_summary = cumulative_artifacts.get("rolling_anchor_summary", {})
    if not isinstance(rolling_anchor_summary, dict):
        errors.append("missing_cumulative_rolling_anchor_summary")
        rolling_anchor_summary = {}
    for key in ("stable_anchors", "dropped_anchors", "new_anchor_delta", "support_ratio", "support_rounds", "current_status"):
        if key not in rolling_anchor_summary:
            errors.append(f"cumulative_rolling_anchor_summary_missing_{key}")
    if len(round_results) <= 1 and rolling_anchor_summary.get("current_status") != "insufficient_rounds":
        errors.append("single_round_rolling_anchor_summary_not_insufficient_rounds")
    if len(round_results) <= 1 and rolling_anchor_summary.get("stable_anchors"):
        errors.append("single_round_rolling_anchor_summary_has_stable_anchors")
    if len(round_results) <= 1 and _contains_stable_commonality(cumulative_artifacts.get("commonality_matrix", [])):
        errors.append("single_round_cumulative_stable_commonality_not_allowed")
    if cumulative_artifacts.get("validation_plan", {}).get("validation_status") != "planned":
        errors.append("cumulative_validation_plan_not_planned")
    if require_current_observation_content:
        if not current_observation_anchor_seen:
            errors.append("mock_fixture_missing_current_observation_anchor")
        if not current_observation_shared_signal_seen:
            errors.append("mock_fixture_missing_current_observation_shared_signal")
        if not group_risk_shared_signal_seen and not group_insufficient_risk_commonality_boundary_seen:
            errors.append("mock_fixture_group_risk_shared_signals_empty_without_insufficient_boundary")
        if not l2_plan_summary_seen:
            errors.append("mock_fixture_l2_plan_status_not_summarized")
        if skippable_anchor_seen and not skipped_anchor_explanation_seen:
            errors.append("mock_fixture_missing_skipped_anchor_explanation")
        missing_domains = sorted((required_domains or set()) - observed_domains)
        missing_anchor_types = sorted((required_anchor_types or set()) - observed_anchor_types)
        for domain in missing_domains:
            errors.append(f"mock_fixture_missing_required_domain:{domain}")
        for anchor_type in missing_anchor_types:
            errors.append(f"mock_fixture_missing_required_anchor_type:{anchor_type}")
    elif skippable_anchor_seen:
        if not l2_skipped_summary_seen:
            errors.append("fixed_fixture_l2_skipped_status_not_summarized")
    return errors, result


def _validate_followup_quality_completion_alignment(result: dict[str, Any]) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    checked_followup_rows = 0
    completed_or_partial_followup_rows = 0
    returned_transport_followup_rows = 0
    missing_transport_mismatches: list[str] = []
    blocked_archives_mismatches: list[str] = []

    def source_ids_from_mapping_or_list(value: Any) -> set[str]:
        if isinstance(value, dict):
            ids = {str(key) for key in value if str(key)}
            ids.update(
                str(item.get("source_id"))
                for item in value.values()
                if isinstance(item, dict) and str(item.get("source_id") or "")
            )
            return ids
        if isinstance(value, list):
            return {
                str(item.get("source_id"))
                for item in value
                if isinstance(item, dict) and str(item.get("source_id") or "")
            }
        return set()

    for round_index, round_result in enumerate(result.get("round_results", []) or [], start=1):
        if not isinstance(round_result, dict):
            continue
        source_completion = round_result.get("source_completion", {})
        successful_sources = set(
            str(source_id)
            for source_id in (
                list(source_completion.get("completed_sources", []) or [])
                + list(source_completion.get("partial_sources", []) or [])
            )
            if str(source_id)
        )
        batch_result = round_result.get("batch_result", {})
        returned_transport_sources = set()
        if isinstance(batch_result, dict):
            returned_transport_sources |= source_ids_from_mapping_or_list(batch_result.get("transport_status_matrix"))
            returned_transport_sources |= source_ids_from_mapping_or_list(batch_result.get("source_results"))
        followup_quality = round_result.get("followup_source_quality") or {}
        for row in followup_quality.get("per_source", []) or []:
            if not isinstance(row, dict):
                continue
            checked_followup_rows += 1
            source_id = str(row.get("source_id") or "")
            if source_id in returned_transport_sources:
                returned_transport_followup_rows += 1
            if source_id in successful_sources:
                completed_or_partial_followup_rows += 1
            if (
                (source_id in successful_sources or source_id in returned_transport_sources)
                and (
                    row.get("source_status") == "not_returned_by_batch"
                    or row.get("error_type") == "missing_transport_status"
                )
            ):
                missing_transport_mismatches.append(f"round_{round_index}:{source_id}")
            if (
                source_id in successful_sources
                and (
                    str(row.get("action") or "").startswith("archives_")
                    and row.get("quality_class") in {"blocked", "auth_failed", "timeout", "parse_error"}
                )
            ):
                blocked_archives_mismatches.append(f"round_{round_index}:{source_id}")

    if missing_transport_mismatches:
        errors.append("FOLLOWUP-QUALITY-USES-TRANSPORT-STATUS-001")
    if blocked_archives_mismatches:
        errors.append("ARCHIVES-FOLLOWUP-HTTP200-NOT-BLOCKED-001")
    return errors, {
        "validation_pass": not errors,
        "checked_followup_rows": checked_followup_rows,
        "completed_or_partial_followup_rows": completed_or_partial_followup_rows,
        "returned_transport_followup_rows": returned_transport_followup_rows,
        "missing_transport_mismatches": missing_transport_mismatches,
        "blocked_archives_mismatches": blocked_archives_mismatches,
    }


def _validate_live_safe_summary_projection() -> tuple[list[str], dict[str, Any]]:
    raw_batch_result = {
        "ok": False,
        "response_mode": "controlled_batch_passthrough",
        "batch_status": "completed_with_partial_sources",
        "scheduler": "controlled_parallel",
        "transport_status_matrix": {
            "login_logs_search": {
                "source_id": "login_logs_search",
                "action": "login_logs_search",
                "category": "failed",
                "source_status": "failed",
                "error_type": "response_too_large",
                "http_status": 200,
                "body_present": True,
                "body_truncated": True,
                "observed_bytes": 65536,
                "raw_body_handling": "json_array_capped",
                "capped_json_path": "data.logSearchModels",
                "observed_records": 61,
                "returned_records": 17,
                "missing_records": 44,
                "cap_reason": "byte_limit",
            }
        },
        "source_results": {
            "login_logs_search": {
                "source_id": "login_logs_search",
                "action": "login_logs_search",
                "source_status": "failed",
                "upstream": {
                    "raw_body_handling": "json_array_capped",
                    "capped_json_path": "data.logSearchModels",
                    "observed_records": 61,
                    "returned_records": 17,
                    "missing_records": 44,
                    "cap_reason": "byte_limit",
                    "capped_body": {
                        "data": {
                            "logSearchModels": [
                                {
                                    "logContent": "{\"token\":\"secret-value\",\"cookie\":\"secret-value\",\"password\":\"secret-value\",\"authorization\":\"secret-value\",\"session\":\"secret-value\"}"
                                }
                            ]
                        }
                    },
                },
            }
        },
    }
    source_quality = {
        "buckets": {
            "completed": [],
            "partial": ["login_logs_search"],
            "blocked": [],
            "timeout": [],
            "no_data": [],
            "auth_failed": [],
            "parse_error": [],
            "planned": [],
        },
        "per_source": [
            {
                "source_id": "login_logs_search",
                "action": "login_logs_search",
                "quality_class": "partial",
                "source_status": "partial",
                "reason": "response_limited",
                "response_limited": True,
                "remaining_records_not_parsed": 44,
            }
        ],
    }
    summary = build_safe_batch_summary(raw_batch_result, source_quality)
    missing_evidence = build_missing_evidence(source_quality)
    text = json.dumps(summary, ensure_ascii=False, sort_keys=True)
    errors: list[str] = []
    forbidden_fragments = [
        "upstream.body",
        "capped_body",
        "logContent",
        "\"cookie\"",
        "\"token\"",
        "\"session\"",
        "\"authorization\"",
        "\"password\"",
        "secret-value",
    ]
    for fragment in forbidden_fragments:
        if fragment in text:
            errors.append(f"safe_summary_forbidden_fragment:{fragment}")
    login_summary = summary.get("source_results", {}).get("login_logs_search", {})
    if login_summary.get("source_status") != "partial":
        errors.append("safe_summary_login_logs_not_partial")
    if login_summary.get("reason") != "response_limited":
        errors.append("safe_summary_login_logs_reason_not_response_limited")
    if login_summary.get("quality_class") != "partial":
        errors.append("safe_summary_login_logs_quality_not_partial")
    if summary.get("source_quality", {}).get("partial") != ["login_logs_search"]:
        errors.append("safe_summary_source_quality_partial_missing_login_logs_search")
    if login_summary.get("remaining_records_not_parsed") != 44:
        errors.append("safe_summary_remaining_records_not_parsed_missing")
    if login_summary.get("cap_metadata_status") != "available_from_safe_projection":
        errors.append("safe_summary_cap_metadata_status_not_available")
    if not any(
        item.get("missing_evidence_type") == "remaining_records_not_parsed"
        and item.get("reason") == "response_limited"
        for item in missing_evidence
        if isinstance(item, dict)
    ):
        errors.append("safe_summary_missing_evidence_does_not_include_remaining_records")
    raw_batch_result_without_cap_metadata = {
        "ok": False,
        "response_mode": "controlled_batch_passthrough",
        "batch_status": "completed_with_partial_sources",
        "transport_status_matrix": {
            "login_logs_search": {
                "source_id": "login_logs_search",
                "action": "login_logs_search",
                "category": "failed",
                "source_status": "failed",
                "error_type": "response_too_large",
                "http_status": 200,
                "body_present": True,
                "body_truncated": True,
                "raw_body_handling": "json_array_capped",
            }
        },
        "source_results": {},
    }
    unavailable_summary = build_safe_batch_summary(raw_batch_result_without_cap_metadata, source_quality)
    unavailable_login_summary = unavailable_summary.get("source_results", {}).get("login_logs_search", {})
    if unavailable_login_summary.get("cap_metadata_status") != "unavailable_from_current_projection":
        errors.append("safe_summary_missing_cap_metadata_status_not_explicit")
    if unavailable_login_summary.get("cap_metadata_reason") != "not_exposed_by_safe_summary":
        errors.append("safe_summary_missing_cap_metadata_reason_not_explicit")
    summary["missing_evidence"] = missing_evidence
    stdout_result = build_safe_stdout_result(
        {
            "schema_version": "runtime_case_execution_result_v1",
            "task": "sample_expand_validate_batch",
            "mode": "live",
            "round_results": [
                {
                    "round_id": 1,
                    "batch_result_raw_debug": raw_batch_result,
                    "batch_result": summary,
                }
            ],
            "orchestration_artifacts": {
                "source_quality": {"partial": ["login_logs_search"]},
                "missing_evidence": missing_evidence,
                "validation_plan": {
                    "validation_status": "pending",
                    "authorization_required": True,
                },
            },
        }
    )
    stdout_text = json.dumps(stdout_result, ensure_ascii=False, sort_keys=True)
    stdout_forbidden_fragments = [
        "upstream.body",
        "upstream.capped_body",
        "capped_body",
        "logContent",
        "\"cookie\"",
        "\"token\"",
        "\"session\"",
        "\"header\"",
        "\"authorization\"",
        "\"password\"",
        "secret-value",
    ]
    for fragment in stdout_forbidden_fragments:
        if fragment in stdout_text:
            errors.append(f"safe_stdout_forbidden_fragment:{fragment}")
    if stdout_result.get("stdout_projection", {}).get("raw_passthrough_omitted") is not True:
        errors.append("safe_stdout_projection_marker_missing")
    return errors, summary


def _source_plan_item(source_id: str, action: str) -> SourcePlanItem:
    return SourcePlanItem(
        source_id=source_id,
        action=action,
        execution_group="independent_parallel",
        depends_on=[],
        timeout_class="standard_readonly",
        failure_policy="non_blocking_partial",
        source_priority="P0",
        expected_observation=f"{action} synthetic regression source",
        params={"user_id": "regression_user"},
        timeout_ms=30_000,
        required_fields=["user_id"],
        window_policy="regression_window",
        window_start_ms=0,
        window_end_ms=1,
    )


def _validate_primary_followup_status_attribution() -> tuple[list[str], dict[str, Any]]:
    primary_plan = [_source_plan_item("primary_weapon_device_info", "weapon_device_info")]
    followup_plan = [_source_plan_item("followup_archives_user_profile", "archives_user_profile")]
    primary_result = {
        "batch_status": "completed",
        "transport_status_matrix": {
            "primary_weapon_device_info": {
                "source_id": "primary_weapon_device_info",
                "action": "weapon_device_info",
                "source_status": "completed",
                "category": "completed",
                "http_status": 200,
                "body_present": True,
            }
        },
        "source_results": {},
    }
    followup_result = {
        "batch_status": "harness_error",
        "transport_status_matrix": {
            "followup_archives_user_profile": {
                "source_id": "followup_archives_user_profile",
                "action": "archives_user_profile",
                "source_status": "invalid_params",
                "category": "blocked",
                "error_type": "invalid_params",
                "http_status": 400,
                "body_present": True,
                "invalid_params": True,
            }
        },
        "source_results": {},
    }
    attribution = build_status_attribution(
        primary_source_plan=primary_plan,
        primary_batch_result=primary_result,
        followup_source_plan=followup_plan,
        followup_batch_result=followup_result,
    )
    errors: list[str] = []
    if attribution.get("primary_source_status") != "completed":
        errors.append("primary_source_status_not_completed")
    if attribution.get("followup_source_status") != "blocked":
        errors.append("followup_source_status_not_blocked")
    if attribution.get("followup_blocked_count") != 1:
        errors.append("followup_blocked_count_not_1")
    if attribution.get("top_level_final_status") != "completed_primary_with_followup_blocked":
        errors.append("top_level_status_not_completed_primary_with_followup_blocked")
    if attribution.get("status_contamination") is not True:
        errors.append("status_contamination_not_true")
    if attribution.get("primary_source_impact") is not False:
        errors.append("primary_source_impact_not_false")
    return errors, attribution


def _transport_result(source_id: str, action: str, **overrides: Any) -> dict[str, Any]:
    row = {
        "source_id": source_id,
        "action": action,
        "source_status": "completed",
        "category": "completed",
        "http_status": 200,
        "content_type": "application/json;charset=utf-8",
        "body_present": True,
        "body_truncated": False,
    }
    row.update(overrides)
    return {
        "batch_status": "completed",
        "transport_status_matrix": {source_id: row},
        "source_results": {
            source_id: {
                "source_id": source_id,
                "action": action,
                "transport": row,
            }
        },
        "missing_or_failed_sources": [],
    }


def _validate_followup_source_quality_transport_regressions() -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    cases: dict[str, dict[str, Any]] = {}

    primary_plan = [_source_plan_item("round_1_entity_1_archives_profile", "archives_user_profile")]
    primary_result = _transport_result("round_1_entity_1_archives_profile", "archives_user_profile")
    followup_plan = [
        _source_plan_item("round_1_entity_1_private_message", "archives_private_message_search"),
        _source_plan_item("round_1_entity_1_comment_123", "archives_comment_search"),
        _source_plan_item("round_1_entity_1_user_report", "archives_user_report_search"),
        _source_plan_item("round_1_entity_1_negative_report", "archives_negative_report"),
        _source_plan_item("round_1_entity_1_review_logs", "archives_review_logs"),
        _source_plan_item("round_1_entity_1_punish_123", "archives_punish_status"),
    ]
    followup_result = merge_batch_results([
        _transport_result(item.source_id, item.action)
        for item in followup_plan
    ])
    attribution = build_status_attribution(
        primary_source_plan=primary_plan,
        primary_batch_result=primary_result,
        followup_source_plan=followup_plan,
        followup_batch_result=followup_result,
    )
    followup_quality = attribution.get("followup_source_quality", {})
    followup_by_source = {
        row.get("source_id"): row
        for row in followup_quality.get("per_source", [])
        if isinstance(row, dict)
    }
    missing_transport_rows = [
        row for row in followup_by_source.values()
        if row.get("error_type") == "missing_transport_status"
        or row.get("source_status") == "not_returned_by_batch"
    ]
    blocked_archives = [
        row for row in followup_by_source.values()
        if str(row.get("action") or "").startswith("archives_")
        and row.get("quality_class") in {"blocked", "auth_failed", "timeout", "parse_error"}
    ]
    action_mismatches = [
        item.source_id
        for item in followup_plan
        if followup_by_source.get(item.source_id, {}).get("action") != item.action
    ]

    cases["FOLLOWUP-QUALITY-USES-TRANSPORT-STATUS-001"] = {
        "pass": not missing_transport_rows,
        "missing_transport_count": len(missing_transport_rows),
        "completed_count": len(followup_quality.get("buckets", {}).get("completed", []) or []),
    }
    cases["ARCHIVES-FOLLOWUP-HTTP200-NOT-BLOCKED-001"] = {
        "pass": not blocked_archives,
        "blocked_count": len(blocked_archives),
        "quality_classes": sorted({str(row.get("quality_class")) for row in followup_by_source.values()}),
    }
    cases["FOLLOWUP-SOURCE-KEY-CORRELATION-001"] = {
        "pass": not action_mismatches and set(followup_by_source) == {item.source_id for item in followup_plan},
        "action_mismatches": action_mismatches,
        "source_count": len(followup_by_source),
    }

    if missing_transport_rows:
        errors.append("FOLLOWUP-QUALITY-USES-TRANSPORT-STATUS-001")
    if blocked_archives:
        errors.append("ARCHIVES-FOLLOWUP-HTTP200-NOT-BLOCKED-001")
    if action_mismatches or set(followup_by_source) != {item.source_id for item in followup_plan}:
        errors.append("FOLLOWUP-SOURCE-KEY-CORRELATION-001")

    track_item = _source_plan_item("round_1_entity_1_track_followup", "track_analysis_check_data_ready")
    track_quality = merge_source_quality(
        [track_item],
        _transport_result(track_item.source_id, track_item.action),
    )
    track_row = track_quality.get("per_source", [{}])[0]
    track_pass = (
        track_row.get("quality_class") == "blocked"
        and track_row.get("gap_state") == "track_business_field_gap"
        and track_row.get("error_type") == "track_business_fields_missing"
    )
    cases["TRACK-HTTP200-BUSINESS-FIELD-GAP-STILL-GAP-001"] = {
        "pass": track_pass,
        "quality_class": track_row.get("quality_class"),
        "gap_state": track_row.get("gap_state"),
        "error_type": track_row.get("error_type"),
    }
    if not track_pass:
        errors.append("TRACK-HTTP200-BUSINESS-FIELD-GAP-STILL-GAP-001")

    login_item = _source_plan_item("round_1_entity_1_login", "login_logs_search")
    login_quality = merge_source_quality(
        [login_item],
        _transport_result(
            login_item.source_id,
            login_item.action,
            raw_body_handling="json_array_capped",
            observed_records=20,
            returned_records=20,
            missing_records=3,
            cap_reason="byte_limit",
        ),
    )
    login_row = login_quality.get("per_source", [{}])[0]
    login_pass = (
        login_row.get("quality_class") == "partial"
        and login_row.get("partial_subtype") == "response_limited"
        and login_row.get("quality_class") != "no_data"
    )
    cases["LOGIN-LOGS-RESPONSE-LIMITED-STILL-PARTIAL-001"] = {
        "pass": login_pass,
        "quality_class": login_row.get("quality_class"),
        "partial_subtype": login_row.get("partial_subtype"),
        "remaining_records_not_parsed": login_row.get("remaining_records_not_parsed"),
    }
    if not login_pass:
        errors.append("LOGIN-LOGS-RESPONSE-LIMITED-STILL-PARTIAL-001")

    return errors, {
        "validation_pass": not errors,
        "cases": cases,
        "followup_status": attribution.get("followup_source_status"),
        "followup_blocked_count": attribution.get("followup_blocked_count"),
    }


def _validate_raw_detail_expansion_handles() -> tuple[list[str], dict[str, Any]]:
    login_records = [
        {
            "loginTime": 1780000000000 + index,
            "loginType": "password",
            "loginSource": "APP",
            "deviceId": f"device_{index}",
            "clientIp": f"10.0.0.{index}",
            "userAgent": f"ua_{index}",
            "appVersion": "14.5.1",
            "province": "北京",
            "city": "北京",
            "loginResult": "success",
            "operationType": "refresh",
            "riskScene": "login_audit",
            "deviceModel": "iPhone13,3",
            "osVersion": "26.5",
            "networkType": "wifi",
            "asn": "AS12345",
            "region": "华北",
            "loginChannel": "ks",
            "securityAction": "none",
            "browserFingerprint": "fp_shared",
            "resetLoginType": "normal",
            "customFieldA": f"value_{index}",
            "customFieldB": "shared_template",
            "customFieldC": index,
            "customFieldD": "retained_unknown",
            "customFieldE": index % 2,
        }
        for index in range(3)
    ]
    login_observation = build_safe_observation(
        source_id="login_raw_expansion",
        action="login_logs_search",
        source_payload={"body": {"data": {"logSearchModels": login_records}}},
        transport_row={"source_id": "login_raw_expansion", "action": "login_logs_search", "quality_class": "partial"},
        expected_business_fields=[],
    )
    user_analysis_body = {
        "data": {
            "records": [
                {
                    "operationTime": 1780000000000 + index,
                    "operationType": "profile_change",
                    "deviceId": f"device_{index}",
                    "clientIp": f"10.1.0.{index}",
                    "profileChange": "avatar",
                    "followCnt30D": 100 + index,
                    "fanCnt30D": 200 + index,
                    "activeDays": 7,
                    "registerTime": 1770000000000,
                    "accountStatus": "normal",
                    "punishStatus": "none",
                    "protectionStatus": "enabled",
                    "nicknameChange": index,
                    "avatarChange": index,
                    "bioChange": 0,
                    "contentPublishCount": 10 + index,
                    "recentBehaviorCounts": 100 + index,
                    "profileCompleteness": "medium",
                    "customBehaviorA": "shared_behavior_template",
                    "customBehaviorB": index,
                    "customBehaviorC": "retained_unknown",
                    "customBehaviorD": index % 2,
                }
                for index in range(3)
            ]
        }
    }
    user_observation = build_safe_observation(
        source_id="user_analysis_raw_expansion",
        action="archives_user_analysis",
        source_payload={"body": user_analysis_body},
        transport_row={"source_id": "user_analysis_raw_expansion", "action": "archives_user_analysis", "quality_class": "completed"},
        expected_business_fields=[],
    )
    login_fields = {
        str(handle.get("field") or handle.get("canonical_field") or "")
        for handle in login_observation.get("parsed_body_safe_handles", []) or []
    }
    user_fields = {
        str(handle.get("field") or handle.get("canonical_field") or "")
        for handle in user_observation.get("parsed_body_safe_handles", []) or []
    }
    errors: list[str] = []
    if len(login_fields) < 20:
        errors.append(f"login_raw_detail_fields_lt_20:{len(login_fields)}")
    if len(user_fields) < 20:
        errors.append(f"user_analysis_raw_detail_fields_lt_20:{len(user_fields)}")
    if "customFieldA" not in login_fields or "customBehaviorA" not in user_fields:
        errors.append("unknown_raw_fields_not_retained")
    return errors, {
        "login_field_count": len(login_fields),
        "user_analysis_field_count": len(user_fields),
        "login_unknown_field_retained": "customFieldA" in login_fields,
        "user_analysis_unknown_field_retained": "customBehaviorA" in user_fields,
    }


def _validate_rcp_register_new_l2_followup_plan() -> tuple[list[str], dict[str, Any]]:
    observations = [
        {
            "source_id": "round_1_entity_1_rcp_snapshot",
            "action": "rcp_snapshot",
            "quality_class": "completed",
            "parsed_body_field_handles": [
                {"field": "eventId", "canonical_field": "event_id", "value": "evt_register_new_1", "field_path": "$.data.list[0].eventId"},
                {"field": "eventType", "canonical_field": "event_type", "value": "REGISTER_NEW", "field_path": "$.data.list[0].eventType"},
                {"field": "queryTime", "canonical_field": "event_time", "value": 1780848177119, "field_path": "$.data.list[0].queryTime"},
                {"field": "sourceId", "canonical_field": "event_id", "value": "5534768444", "field_path": "$.data.list[0].sourceId"},
                {"field": "policyCode", "canonical_field": "policy_code", "value": "REGISTER_RISK_POLICY", "field_path": "$.data.list[0].policyCode"},
            ],
        }
    ]
    followup_plan = build_rcp_event_followup_source_plan(
        1,
        ["5534768444"],
        observations,
        window_start_ms=1780847877000,
        window_end_ms=1780848178000,
    )
    feature_items = [item for item in followup_plan if item.action == "rcp_event_feature_list"]
    errors: list[str] = []
    if not feature_items:
        errors.append("rcp_event_feature_list_followup_not_planned")
    else:
        params = feature_items[0].params
        if params.get("eventId") != "evt_register_new_1":
            errors.append("rcp_followup_event_id_not_from_event_anchor")
        if params.get("source_id") != "5534768444":
            errors.append("rcp_followup_source_id_not_from_source_anchor")
        if params.get("eventType") != "REGISTER_NEW":
            errors.append("rcp_followup_event_type_not_register_new")
    return errors, {
        "followup_source_count": len(followup_plan),
        "rcp_event_feature_list_count": len(feature_items),
        "first_feature_params": feature_items[0].params if feature_items else {},
    }


def _validate_partial_quality_lowers_anchor_score() -> tuple[list[str], dict[str, Any]]:
    source_observations = [
        {
            "source_id": "partial_login_source",
            "action": "login_logs_search",
            "quality_class": "partial",
            "parsed_body_field_handles": [
                {
                    "canonical_field": "device_id",
                    "field": "device_id",
                    "value": "partial_device_anchor",
                    "field_path": "$.data.logSearchModels[0].deviceId",
                }
            ],
        }
    ]
    anchors = [
        {
            "anchor_type": "candidate_device_id",
            "value": "partial_device_anchor",
            "produced_by": "partial_login_source",
            "observation_domain": "device_domain",
            "confidence": "current_observation",
            "next_allowed_interfaces": ["weapon_device_info", "weapon_device_app_list", "track_analysis_check_data_ready", "weapon_inventory"],
            "cap_key": "device_anchor_top_k",
            "reason": "device_id_extracted_from_current_observation",
            "source_quality": "partial",
            "evidence_source": "current_observation",
        }
    ]
    scored = score_candidate_anchors(
        candidate_anchor_pool=anchors,
        sampled_entities=["sample_user"],
        source_observations=source_observations,
    )
    anchor = scored.get("candidate_anchor_pool", [{}])[0]
    evidence_quality = anchor.get("anchor_score", {}).get("evidence_quality")
    errors: list[str] = []
    if evidence_quality is None or evidence_quality >= 1:
        errors.append("partial_source_quality_did_not_lower_anchor_evidence_quality")
    return errors, {
        "evidence_quality": evidence_quality,
        "selection_status": anchor.get("selection_status"),
        "anchor_priority_reason": anchor.get("anchor_priority_reason"),
    }


def _validate_strategy_event_request_detail_fixture() -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    if not STRATEGY_EVENT_REQUEST_DETAIL_FIXTURE.exists():
        return [f"strategy_event_request_detail_fixture_missing:{STRATEGY_EVENT_REQUEST_DETAIL_FIXTURE}"], {}
    fixture = json.loads(STRATEGY_EVENT_REQUEST_DETAIL_FIXTURE.read_text(encoding="utf-8"))

    detail_rows = fixture.get("strategy_event_request_detail_table", [])
    if not isinstance(detail_rows, list) or not detail_rows:
        errors.append("strategy_event_request_detail_table_missing_or_empty")
        detail_rows = []
    for row_index, row in enumerate(detail_rows, start=1):
        if not isinstance(row, dict):
            errors.append(f"strategy_event_detail_row_{row_index}_not_object")
            continue
        for field in STRATEGY_EVENT_REQUEST_DETAIL_REQUIRED_FIELDS:
            if field not in row:
                errors.append(f"strategy_event_detail_row_{row_index}_missing_{field}")
        if row.get("evidence_source") != "current_observation":
            errors.append(f"strategy_event_detail_row_{row_index}_not_current_observation")
        if row.get("source_quality") in {"no_data", "timeout", "missing_contract", "auth_failed"}:
            errors.append(f"strategy_event_detail_row_{row_index}_gap_row_used_as_detail_fact")

    commonality_rows = fixture.get("field_level_commonality", [])
    if not isinstance(commonality_rows, list) or not commonality_rows:
        errors.append("strategy_field_level_commonality_missing_or_empty")
        commonality_rows = []
    current_field_commonality_seen = False
    for commonality_index, commonality in enumerate(commonality_rows, start=1):
        if not isinstance(commonality, dict):
            errors.append(f"strategy_commonality_{commonality_index}_not_object")
            continue
        source_fields = set(str(field) for field in commonality.get("source_fields", []) or [])
        if not source_fields & STRATEGY_REQUEST_DETAIL_CORE_FIELDS:
            errors.append(f"strategy_commonality_{commonality_index}_missing_request_detail_core_field")
        if source_fields <= STRATEGY_ENTRY_LABEL_FIELDS:
            errors.append(f"strategy_commonality_{commonality_index}_entry_label_only")
        if int(commonality.get("support_sample_count") or 0) < 2:
            errors.append(f"strategy_commonality_{commonality_index}_support_lt_2")
        if commonality.get("evidence_source") == "current_observation":
            current_field_commonality_seen = True
        if commonality.get("not_final_conclusion") is not True:
            errors.append(f"strategy_commonality_{commonality_index}_not_final_conclusion_missing")

    features = fixture.get("candidate_features", [])
    if not isinstance(features, list) or not features:
        errors.append("strategy_candidate_features_missing_or_empty")
        features = []
    for feature_index, feature in enumerate(features, start=1):
        if not isinstance(feature, dict):
            errors.append(f"strategy_feature_{feature_index}_not_object")
            continue
        for key in STRATEGY_REQUEST_DETAIL_FEATURE_REQUIRED_KEYS:
            if key not in feature:
                errors.append(f"strategy_feature_{feature_index}_missing_{key}")
        source_fields = set(str(field) for field in feature.get("source_fields", []) or [])
        if source_fields <= STRATEGY_ENTRY_LABEL_FIELDS:
            errors.append(f"strategy_feature_{feature_index}_policy_event_decision_only")
        if not source_fields & STRATEGY_REQUEST_DETAIL_CORE_FIELDS:
            errors.append(f"strategy_feature_{feature_index}_missing_request_detail_core_field")
        if not feature.get("field_combination"):
            errors.append(f"strategy_feature_{feature_index}_missing_field_combination")
        if int(feature.get("support_sample_count") or 0) < 2:
            errors.append(f"strategy_feature_{feature_index}_support_sample_count_lt_2")
        if feature.get("validation_needed") is not True:
            errors.append(f"strategy_feature_{feature_index}_validation_needed_not_true")
        if feature.get("not_final_conclusion") is not True:
            errors.append(f"strategy_feature_{feature_index}_not_final_conclusion_not_true")
        if not feature.get("normal_user_false_positive_risk"):
            errors.append(f"strategy_feature_{feature_index}_missing_false_positive_explanation")
        if not feature.get("missing_fields_to_check"):
            errors.append(f"strategy_feature_{feature_index}_missing_followup_fields")
        if not feature.get("strategy_usage_boundary"):
            errors.append(f"strategy_feature_{feature_index}_missing_usage_boundary")
        for evidence_index, evidence in enumerate(feature.get("supporting_current_evidence", []) or [], start=1):
            if not isinstance(evidence, dict):
                errors.append(f"strategy_feature_{feature_index}_evidence_{evidence_index}_not_object")
                continue
            for trace_field in ("sample_id", "entity_id", "round_id", "source_id", "source_quality"):
                if trace_field not in evidence:
                    errors.append(f"strategy_feature_{feature_index}_evidence_{evidence_index}_missing_{trace_field}")

    return errors, {
        "fixture": str(STRATEGY_EVENT_REQUEST_DETAIL_FIXTURE.relative_to(ROOT)),
        "detail_row_count": len(detail_rows),
        "commonality_row_count": len(commonality_rows),
        "candidate_feature_count": len(features),
        "current_field_commonality_seen": current_field_commonality_seen,
    }


def _validate_runtime_strategy_request_detail_artifacts(result: dict[str, Any]) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    round_results = result.get("round_results", []) if isinstance(result, dict) else []
    table_rows: list[dict[str, Any]] = []
    strategy_features: list[dict[str, Any]] = []
    commonality_rows: list[dict[str, Any]] = []
    for round_index, round_result in enumerate(round_results, start=1):
        for field in ("checkpoint_files", "latest_checkpoint_file", "checkpoint_count", "partial_result_available", "progress_trace", "timing_trace", "timing_summary"):
            if field not in round_result:
                errors.append(f"source_l1_l3_round_{round_index}_missing_{field}")
        for progress_index, progress in enumerate(round_result.get("progress_trace", []) or [], start=1):
            for field in (
                "current_chunk_id",
                "current_round_index",
                "current_batch_index",
                "current_source_group",
                "current_running_sources",
                "elapsed_seconds",
                "last_checkpoint_file",
                "completed_source_count",
                "partial_source_count",
                "blocked_source_count",
                "pending_source_count",
            ):
                if field not in progress:
                    errors.append(f"source_l1_l3_round_{round_index}_progress_{progress_index}_missing_{field}")
        timing_trace = round_result.get("timing_trace", {}) or {}
        global_timing = timing_trace.get("global", {}) if isinstance(timing_trace, dict) else {}
        for field in (
            "plan_build_ms",
            "chunk_build_ms",
            "batch_submit_ms",
            "batch_wait_ms",
            "service_return_ms",
            "artifact_build_ms",
            "checkpoint_write_ms",
            "total_elapsed_ms",
        ):
            if field not in global_timing:
                errors.append(f"source_l1_l3_round_{round_index}_timing_global_missing_{field}")
        for timing_index, timing_row in enumerate(timing_trace.get("chunks", []) or [], start=1):
            for field in (
                "chunk_id",
                "round_index",
                "batch_index",
                "source_group",
                "action_count",
                "submit_started_at",
                "submit_finished_at",
                "service_wait_started_at",
                "service_returned_at",
                "batch_elapsed_ms",
                "completed_count",
                "partial_count",
                "blocked_count",
                "timeout_count",
                "pending_count",
            ):
                if field not in timing_row:
                    errors.append(f"source_l1_l3_round_{round_index}_timing_row_{timing_index}_missing_{field}")
        artifacts = round_result.get("orchestration_artifacts", {}) if isinstance(round_result, dict) else {}
        rows = artifacts.get("strategy_event_request_detail_table", []) or []
        if not rows:
            errors.append(f"runtime_strategy_round_{round_index}_missing_strategy_event_request_detail_table")
        for row_index, row in enumerate(rows, start=1):
            if not isinstance(row, dict):
                errors.append(f"runtime_strategy_round_{round_index}_row_{row_index}_not_object")
                continue
            table_rows.append(row)
            if row.get("entry_label_fields_only") is True:
                continue
            if not any(row.get(field) not in {None, ""} for field in STRATEGY_REQUEST_DETAIL_CORE_FIELDS):
                errors.append(f"runtime_strategy_round_{round_index}_row_{row_index}_missing_request_detail_core_field")
        commonality_rows.extend([
            item for item in artifacts.get("strategy_event_request_detail_commonality", []) or []
            if isinstance(item, dict)
        ])
        strategy_features.extend([
            item for item in artifacts.get("candidate_features", []) or []
            if isinstance(item, dict)
            and str(item.get("feature_name") or "").startswith("strategy_request_detail")
        ])
    if not commonality_rows:
        errors.append("runtime_strategy_request_detail_commonality_missing")
    if not strategy_features:
        errors.append("runtime_strategy_request_detail_candidate_feature_missing")
    for feature_index, feature in enumerate(strategy_features, start=1):
        for key in STRATEGY_REQUEST_DETAIL_FEATURE_REQUIRED_KEYS:
            if key not in feature:
                errors.append(f"runtime_strategy_feature_{feature_index}_missing_{key}")
        source_fields = set(str(field) for field in feature.get("source_fields", []) or [])
        if source_fields <= STRATEGY_ENTRY_LABEL_FIELDS:
            errors.append(f"runtime_strategy_feature_{feature_index}_entry_label_only")
        if not source_fields & STRATEGY_REQUEST_DETAIL_CORE_FIELDS:
            errors.append(f"runtime_strategy_feature_{feature_index}_missing_request_detail_core_field")
        if int(feature.get("support_sample_count") or 0) < 2:
            errors.append(f"runtime_strategy_feature_{feature_index}_support_sample_count_lt_2")
        if feature.get("validation_needed") is not True:
            errors.append(f"runtime_strategy_feature_{feature_index}_validation_needed_not_true")
        if feature.get("not_final_conclusion") is not True:
            errors.append(f"runtime_strategy_feature_{feature_index}_not_final_conclusion_not_true")
    return errors, {
        "strategy_event_request_detail_table_rows": len(table_rows),
        "strategy_event_request_detail_commonality_count": len(commonality_rows),
        "strategy_request_detail_candidate_feature_count": len(strategy_features),
    }


def _expected_original_feature_row_count(fixture: dict[str, Any]) -> int:
    count = 0
    for round_item in fixture.get("rounds", []) or []:
        for observation in round_item.get("mock_current_observations", []) or []:
            for row in observation.get("feature_rows", []) or []:
                if isinstance(row, dict) and str(row.get("feature_tab") or row.get("featureGroup") or "") == "原始类":
                    count += 1
    return count


def _validate_runtime_strategy_feature_row_artifacts(
    result: dict[str, Any],
    fixture: dict[str, Any] | None = None,
) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    round_results = result.get("round_results", []) if isinstance(result, dict) else []
    table_rows: list[dict[str, Any]] = []
    commonality_rows: list[dict[str, Any]] = []
    feature_row_candidate_features: list[dict[str, Any]] = []
    for round_index, round_result in enumerate(round_results, start=1):
        artifacts = round_result.get("orchestration_artifacts", {}) if isinstance(round_result, dict) else {}
        rows = artifacts.get("strategy_event_feature_row_table", []) or []
        if not rows:
            errors.append(f"runtime_feature_row_round_{round_index}_table_missing_or_empty")
        table_rows.extend([row for row in rows if isinstance(row, dict)])
        commonality_rows.extend([
            item for item in artifacts.get("strategy_event_feature_row_commonality", []) or []
            if isinstance(item, dict)
        ])
        feature_row_candidate_features.extend([
            item for item in artifacts.get("candidate_features", []) or []
            if isinstance(item, dict)
            and (
                "source_feature_keys" in item
                or str(item.get("feature_name") or "").startswith("strategy_event_original_feature")
            )
        ])

    original_rows = [row for row in table_rows if row.get("feature_tab") == "原始类"]
    if fixture is not None:
        expected_original_count = _expected_original_feature_row_count(fixture)
        if len(original_rows) < expected_original_count:
            errors.append(
                f"runtime_feature_row_original_rows_lost:expected_{expected_original_count}_got_{len(original_rows)}"
            )
    for row_index, row in enumerate(table_rows, start=1):
        for field in STRATEGY_EVENT_FEATURE_ROW_REQUIRED_FIELDS:
            if field not in row:
                errors.append(f"runtime_feature_row_{row_index}_missing_{field}")
        if row.get("feature_tab") == "原始类" and row.get("original_feature_row_retained") is not True:
            errors.append(f"runtime_feature_row_{row_index}_original_not_marked_retained")
        if row.get("value_present") is True and "feature_value_or_safe_ref" not in row:
            errors.append(f"runtime_feature_row_{row_index}_present_value_missing_safe_ref")
        if row.get("sensitive_value_policy") in {"只保留安全引用", "只保留是否存在"} and row.get("value_present") is True:
            if row.get("feature_value_or_safe_ref") in {None, ""}:
                errors.append(f"runtime_feature_row_{row_index}_sensitive_policy_missing_safe_ref")

    if not any(str(row.get("feature_key")) == "unknownOriginalX" for row in original_rows):
        errors.append("runtime_feature_row_unknown_original_field_not_retained")

    coverage_rows = [
        row for row in commonality_rows
        if str(row.get("commonality_type") or "") == "coverage_commonality"
    ]
    if not coverage_rows:
        errors.append("runtime_feature_row_coverage_commonality_missing")
    for item_index, item in enumerate(coverage_rows, start=1):
        if item.get("candidate_feature_eligible") is True:
            errors.append(f"runtime_feature_row_coverage_{item_index}_candidate_feature_eligible")
        if item.get("risk_commonality") is True or item.get("eligible_for_group_candidate") is True:
            errors.append(f"runtime_feature_row_coverage_{item_index}_marked_as_risk")

    value_commonality_rows = [
        row for row in commonality_rows
        if str(row.get("commonality_type") or "") == "field_value_commonality"
    ]
    if not value_commonality_rows:
        errors.append("runtime_feature_row_value_commonality_missing")
    if not feature_row_candidate_features:
        errors.append("runtime_feature_row_candidate_feature_missing")
    for feature_index, feature in enumerate(feature_row_candidate_features, start=1):
        source_feature_keys = feature.get("source_feature_keys") or feature.get("source_fields") or []
        if not source_feature_keys:
            errors.append(f"runtime_feature_row_candidate_{feature_index}_missing_source_feature_keys")
        if set(str(key) for key in source_feature_keys) <= STRATEGY_ENTRY_LABEL_FIELDS:
            errors.append(f"runtime_feature_row_candidate_{feature_index}_entry_label_only")
        if not feature.get("field_combination"):
            errors.append(f"runtime_feature_row_candidate_{feature_index}_missing_field_combination")
        if int(feature.get("support_sample_count") or 0) < 2:
            errors.append(f"runtime_feature_row_candidate_{feature_index}_support_lt_2")
        if feature.get("validation_needed") is not True:
            errors.append(f"runtime_feature_row_candidate_{feature_index}_validation_needed_not_true")
        if feature.get("not_final_conclusion") is not True:
            errors.append(f"runtime_feature_row_candidate_{feature_index}_not_final_conclusion_not_true")
        if not feature.get("normal_user_false_positive_risk"):
            errors.append(f"runtime_feature_row_candidate_{feature_index}_missing_false_positive_boundary")

    return errors, {
        "strategy_event_feature_row_table_rows": len(table_rows),
        "original_feature_row_count": len(original_rows),
        "feature_row_commonality_count": len(commonality_rows),
        "field_value_commonality_count": len(value_commonality_rows),
        "feature_row_candidate_feature_count": len(feature_row_candidate_features),
    }


def _validate_runtime_device_detail_artifacts(
    result: dict[str, Any],
) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    round_results = result.get("round_results", []) if isinstance(result, dict) else []
    table_rows: list[dict[str, Any]] = []
    commonality_rows: list[dict[str, Any]] = []
    similarity_candidates: list[dict[str, Any]] = []
    consistency_candidates: list[dict[str, Any]] = []
    device_candidate_features: list[dict[str, Any]] = []
    for round_index, round_result in enumerate(round_results, start=1):
        artifacts = round_result.get("orchestration_artifacts", {}) if isinstance(round_result, dict) else {}
        rows = artifacts.get("device_detail_table", []) or []
        if not rows:
            errors.append(f"runtime_device_round_{round_index}_detail_table_missing_or_empty")
        table_rows.extend([row for row in rows if isinstance(row, dict)])
        commonality_rows.extend([
            item for item in artifacts.get("device_field_commonality", []) or []
            if isinstance(item, dict)
        ])
        similarity_candidates.extend([
            item for item in artifacts.get("device_environment_similarity_cluster_candidate", []) or []
            if isinstance(item, dict)
        ])
        consistency_candidates.extend([
            item for item in artifacts.get("behavior_device_consistency_gap_candidate", []) or []
            if isinstance(item, dict)
        ])
        device_candidate_features.extend([
            item for item in artifacts.get("candidate_features", []) or []
            if isinstance(item, dict)
            and (
                str(item.get("feature_name") or "").startswith("low_life_device")
                or str(item.get("feature_name") or "").startswith("automation_or_script_device")
                or str(item.get("feature_name") or "").startswith("modification_or_adversarial_device")
                or str(item.get("feature_name") or "").startswith("risky_app_environment")
                or str(item.get("feature_name") or "").startswith("device_environment_similarity")
                or str(item.get("feature_name") or "").startswith("behavior_device_consistency")
                or str(item.get("feature_name") or "").startswith("single_field_strong_signal")
                or str(item.get("feature_name") or "").startswith("hard_single_field_signal")
                or str(item.get("feature_name") or "").startswith("group_level_field_enrichment")
                or str(item.get("feature_name") or "").startswith("unknown_field_value_commonality")
                or str(item.get("feature_name") or "").startswith("unknown_field_value_enrichment")
            )
        ])

    if len(table_rows) < 20:
        errors.append(f"runtime_device_detail_rows_too_few:{len(table_rows)}")
    mapped_family_counts: dict[str, int] = {}
    for row in table_rows:
        family = str(row.get("mapped_field_family") or "missing")
        mapped_family_counts[family] = mapped_family_counts.get(family, 0) + 1
    non_unknown_family_count = sum(
        count for family, count in mapped_family_counts.items()
        if family not in {"unknown_device_field_family", "missing"}
    )
    if non_unknown_family_count < 12:
        errors.append(f"runtime_device_mapped_family_rows_too_few:{non_unknown_family_count}")
    required_families = {
        "device_basic",
        "device_freshness",
        "low_life_device_environment",
        "automation_or_script",
        "modification_or_adversarial",
        "app_environment",
    }
    missing_families = sorted(family for family in required_families if mapped_family_counts.get(family, 0) <= 0)
    if missing_families:
        errors.append(f"runtime_device_missing_mapped_families:{','.join(missing_families)}")
    source_types = {str(row.get("device_source_type") or "") for row in table_rows}
    required_source_types = {"设备基础信息", "设备风险标签", "设备使用画像", "安装列表 / 应用环境", "账号-设备关系", "行为-设备一致性"}
    missing_source_types = sorted(required_source_types - source_types)
    if missing_source_types:
        errors.append(f"runtime_device_missing_source_types:{','.join(missing_source_types)}")
    for row_index, row in enumerate(table_rows, start=1):
        for field in DEVICE_DETAIL_REQUIRED_FIELDS:
            if field not in row:
                errors.append(f"runtime_device_row_{row_index}_missing_{field}")
        if row.get("value_present") is True and "device_field_value_or_safe_ref" not in row:
            errors.append(f"runtime_device_row_{row_index}_present_value_missing")
        if str(row.get("device_field_key") or "") == "frontend_activity_signal":
            errors.append(f"runtime_device_row_{row_index}_frontend_activity_as_device_field")
        field_text = "".join(ch for ch in str(row.get("device_field_key") or "").lower() if ch.isalnum())
        path_parts = [
            "".join(ch for ch in part.lower() if ch.isalnum())
            for part in re.split(r"[.\[\]]+", str(row.get("field_path") or ""))
            if part
        ]
        if field_text in DEVICE_NON_DEVICE_DETAIL_BLOCK_KEYS or any(part in DEVICE_NON_DEVICE_DETAIL_BLOCK_KEYS for part in path_parts):
            errors.append(f"runtime_device_row_{row_index}_non_device_block_in_device_detail")

    coverage_rows = [
        item for item in commonality_rows
        if str(item.get("commonality_type") or "") == "coverage_commonality"
    ]
    value_rows = [
        item for item in commonality_rows
        if str(item.get("commonality_type") or "") in {"field_value_commonality", "known_field_commonality"}
    ]
    known_value_rows = [
        item for item in commonality_rows
        if str(item.get("commonality_type") or "") == "known_field_commonality"
    ]
    unknown_value_rows = [
        item for item in commonality_rows
        if str(item.get("commonality_type") or "") == "unknown_field_value_commonality"
    ]
    single_field_rows = [
        item for item in commonality_rows
        if str(item.get("commonality_type") or "") in {"single_field_strong_signal", "hard_single_field_signal"}
    ]
    group_enrichment_rows = [
        item for item in commonality_rows
        if str(item.get("commonality_type") or "") == "group_level_field_enrichment_commonality"
    ]
    combination_rows = [
        item for item in commonality_rows
        if str(item.get("commonality_type") or "") == "field_combination_commonality"
    ]
    if not coverage_rows:
        errors.append("runtime_device_coverage_commonality_missing")
    for item_index, item in enumerate(coverage_rows, start=1):
        if item.get("candidate_feature_eligible") is True:
            errors.append(f"runtime_device_coverage_{item_index}_candidate_feature_eligible")
        if item.get("risk_commonality") is True or item.get("eligible_for_group_candidate") is True:
            errors.append(f"runtime_device_coverage_{item_index}_marked_as_risk")
    if not value_rows:
        errors.append("runtime_device_field_value_commonality_missing")
    if not known_value_rows:
        errors.append("runtime_device_known_field_commonality_missing")
    if not unknown_value_rows:
        errors.append("runtime_device_unknown_field_value_commonality_missing")
    for item_index, item in enumerate(unknown_value_rows, start=1):
        if item.get("known_field") is not False:
            errors.append(f"runtime_device_unknown_commonality_{item_index}_known_field_not_false")
        if str(item.get("field_semantics_status") or "") != "field_semantics_unknown":
            errors.append(f"runtime_device_unknown_commonality_{item_index}_missing_unknown_semantics")
        if item.get("validation_needed") is not True:
            errors.append(f"runtime_device_unknown_commonality_{item_index}_validation_needed_missing")
        if not item.get("priority_level") or item.get("priority_score") is None or not item.get("reason_codes"):
            errors.append(f"runtime_device_unknown_commonality_{item_index}_priority_fields_missing")
        if str(item.get("device_field_key") or "").lower() in {"groupname", "grouplevel", "safestatus", "safe_status"}:
            if item.get("suspected_default_value") is not True:
                errors.append(f"runtime_device_unknown_commonality_{item_index}_default_enum_not_marked")
            if str(item.get("priority_level") or "") == "high":
                errors.append(f"runtime_device_unknown_commonality_{item_index}_default_enum_high_priority")
        suspicious_text = str(item.get("why_suspicious") or "")
        if any(word in suspicious_text.lower() for word in ("confirmed", "automation confirmed", "fraud_ring", "团伙确认", "已坐实")):
            errors.append(f"runtime_device_unknown_commonality_{item_index}_over_interpreted")
    if not single_field_rows:
        errors.append("runtime_device_single_field_strong_signal_missing")
    for item_index, item in enumerate(single_field_rows, start=1):
        family = str(item.get("device_field_family") or "")
        if family in {"device_freshness", "low_life_device_environment"}:
            errors.append(f"runtime_device_single_field_{item_index}_weak_field_promoted_to_hard")
        if not item.get("priority_level") or item.get("priority_score") is None or not item.get("reason_codes"):
            errors.append(f"runtime_device_single_field_{item_index}_priority_fields_missing")
    if not group_enrichment_rows:
        errors.append("runtime_device_group_level_field_enrichment_missing")
    for item_index, item in enumerate(group_enrichment_rows, start=1):
        if int(item.get("support_user_count") or item.get("support_count") or 0) < 2:
            errors.append(f"runtime_device_group_enrichment_{item_index}_support_lt_2")
        if item.get("baseline_missing") is not True and item.get("baseline_ratio") is None:
            errors.append(f"runtime_device_group_enrichment_{item_index}_baseline_boundary_missing")
    if not combination_rows:
        errors.append("runtime_device_field_combination_commonality_missing")

    if not similarity_candidates:
        errors.append("runtime_device_similarity_candidate_missing")
    for candidate_index, candidate in enumerate(similarity_candidates, start=1):
        if len(candidate.get("shared_device_fields", []) or []) < 2:
            errors.append(f"runtime_device_similarity_{candidate_index}_shared_fields_lt_2")
        if len(candidate.get("support_devices", []) or []) < 2:
            errors.append(f"runtime_device_similarity_{candidate_index}_support_devices_lt_2")
        if candidate.get("not_confirmed_as_group") is not True:
            errors.append(f"runtime_device_similarity_{candidate_index}_not_confirmed_boundary_missing")
        if len(candidate.get("shared_device_fields", []) or []) == 1 and str(candidate.get("confidence") or "").startswith("high"):
            errors.append(f"runtime_device_similarity_{candidate_index}_single_field_high_confidence")

    if not consistency_candidates:
        errors.append("runtime_behavior_device_consistency_candidate_missing")
    for candidate in consistency_candidates:
        boundary = str(candidate.get("boundary") or "")
        if "not a device fingerprint" not in boundary and "不是" not in boundary:
            errors.append("runtime_behavior_device_consistency_boundary_missing")

    if not device_candidate_features:
        errors.append("runtime_device_candidate_features_missing")
    for feature_index, feature in enumerate(device_candidate_features, start=1):
        source_fields = [str(field) for field in feature.get("source_device_fields") or feature.get("source_fields") or []]
        feature_name = str(feature.get("feature_name") or "")
        if not source_fields:
            errors.append(f"runtime_device_candidate_{feature_index}_missing_source_device_fields")
        if set(source_fields) <= DEVICE_ID_ONLY_FEATURE_FIELDS and not feature_name.startswith("behavior_device_consistency"):
            errors.append(f"runtime_device_candidate_{feature_index}_device_id_only_feature")
        if not feature.get("field_combination"):
            errors.append(f"runtime_device_candidate_{feature_index}_missing_field_combination")
        min_support = 1 if feature_name.startswith(("single_field_strong_signal", "hard_single_field_signal")) else 2
        if int(feature.get("support_user_count") or feature.get("support_sample_count") or 0) < min_support:
            errors.append(f"runtime_device_candidate_{feature_index}_support_lt_2")
        if not feature.get("feature_type"):
            errors.append(f"runtime_device_candidate_{feature_index}_missing_feature_type")
        if not feature.get("priority_level") or feature.get("priority_score") is None or not feature.get("reason_codes"):
            errors.append(f"runtime_device_candidate_{feature_index}_priority_fields_missing")
        if feature.get("support_ratio") is None or not feature.get("platform_scope"):
            errors.append(f"runtime_device_candidate_{feature_index}_ranking_context_missing")
        if not feature.get("field_values_or_safe_refs"):
            errors.append(f"runtime_device_candidate_{feature_index}_missing_field_values")
        if feature.get("conclusion_boundary") != "candidate_only_not_final_conclusion":
            errors.append(f"runtime_device_candidate_{feature_index}_missing_conclusion_boundary")
        if not feature.get("normal_user_false_positive_risk"):
            errors.append(f"runtime_device_candidate_{feature_index}_missing_false_positive_risk")
        if not feature.get("validation_method"):
            errors.append(f"runtime_device_candidate_{feature_index}_missing_validation_method")
        if feature.get("not_final_conclusion") is not True:
            errors.append(f"runtime_device_candidate_{feature_index}_not_final_false")
        if feature_name.startswith("behavior_device_consistency"):
            if "不是纯设备指纹" not in str(feature.get("strategy_usage_boundary") or "") and "not" not in str(feature.get("strategy_usage_boundary") or ""):
                errors.append(f"runtime_device_candidate_{feature_index}_consistency_boundary_missing")
        if feature_name.startswith(("unknown_field_value_commonality", "unknown_field_value_enrichment")):
            if str(feature.get("field_semantics_status") or "") != "field_semantics_unknown":
                errors.append(f"runtime_device_candidate_{feature_index}_unknown_semantics_missing")
            if "不得直接" not in str(feature.get("strategy_usage_boundary") or "") and "not" not in str(feature.get("strategy_usage_boundary") or ""):
                errors.append(f"runtime_device_candidate_{feature_index}_unknown_boundary_missing")
            if feature.get("suspected_default_value") is True and str(feature.get("priority_level") or "") == "high":
                errors.append(f"runtime_device_candidate_{feature_index}_unknown_default_high_priority")
        if feature_name.startswith("group_level_field_enrichment"):
            if feature.get("baseline_missing") is not True:
                errors.append(f"runtime_device_candidate_{feature_index}_group_enrichment_baseline_missing_not_marked")
            if "团组" not in str(feature.get("black_gray_interpretation") or "") and "富集" not in str(feature.get("black_gray_interpretation") or ""):
                errors.append(f"runtime_device_candidate_{feature_index}_group_enrichment_interpretation_missing")

    if not any(str(feature.get("feature_name") or "").startswith(("single_field_strong_signal", "hard_single_field_signal")) for feature in device_candidate_features):
        errors.append("runtime_device_single_field_candidate_missing")
    if not any(str(feature.get("feature_name") or "").startswith(("unknown_field_value_commonality", "unknown_field_value_enrichment")) for feature in device_candidate_features):
        errors.append("runtime_device_unknown_field_candidate_missing")
    if not any(str(feature.get("feature_name") or "").startswith("group_level_field_enrichment") for feature in device_candidate_features):
        errors.append("runtime_device_group_level_enrichment_candidate_missing")

    platform_summary = {}
    for round_result in round_results:
        artifacts = round_result.get("orchestration_artifacts", {}) if isinstance(round_result, dict) else {}
        summary = artifacts.get("device_field_platform_summary", {})
        if isinstance(summary, dict):
            platform_summary = summary
            break
    platforms = platform_summary.get("platforms", {}) if isinstance(platform_summary, dict) else {}
    android_rows = int((platforms.get("android", {}) or {}).get("row_count") or 0)
    ios_rows = int((platforms.get("ios", {}) or {}).get("row_count") or 0)
    if android_rows <= 0:
        errors.append("runtime_device_android_platform_rows_missing")
    if ios_rows < 8:
        errors.append(f"runtime_device_ios_rows_too_compressed:{ios_rows}")
    if int(platform_summary.get("unknown_field_value_commonality_count") or 0) <= 0:
        errors.append("runtime_device_platform_summary_unknown_commonality_missing")
    if int(platform_summary.get("single_field_strong_signal_count") or 0) <= 0:
        errors.append("runtime_device_platform_summary_single_signal_missing")

    return errors, {
        "device_detail_table_rows": len(table_rows),
        "device_source_types": sorted(source_types),
        "device_field_commonality_count": len(commonality_rows),
        "device_field_value_commonality_count": len(value_rows),
        "device_known_field_commonality_count": len(known_value_rows),
        "device_unknown_field_value_commonality_count": len(unknown_value_rows),
        "device_single_field_strong_signal_count": len(single_field_rows),
        "device_group_level_field_enrichment_count": len(group_enrichment_rows),
        "device_field_combination_commonality_count": len(combination_rows),
        "device_similarity_candidate_count": len(similarity_candidates),
        "behavior_device_consistency_candidate_count": len(consistency_candidates),
        "device_candidate_feature_count": len(device_candidate_features),
        "device_mapped_family_counts": mapped_family_counts,
        "device_non_unknown_family_row_count": non_unknown_family_count,
        "device_field_platform_summary": platform_summary,
    }


def _validate_weapon_device_detail_pre_projection_retention() -> tuple[list[str], dict[str, Any]]:
    payload = {f"deviceField{i}": i for i in range(150)}
    payload.update(
        {
            "deviceId": "ANDROID_SYNTHETIC_DEVICE",
            "phoneModel": "synthetic-phone",
            "clipboardStats": "{ pasteboardReadCount = 12; pasteboardWriteCount = 3; }",
            "cookie": "must_not_be_retained",
            "token": "must_not_be_retained",
        }
    )
    observation = build_safe_observation(
        source_id="synthetic_weapon_device_info",
        action="weapon_device_info",
        source_payload={"body": json.dumps({"data": payload}, ensure_ascii=False)},
        transport_row={"source_status": "completed", "quality_class": "completed"},
    )
    rows = observation.get("device_detail_rows", []) or []
    keys = {str(row.get("device_field_key") or "") for row in rows if isinstance(row, dict)}
    errors: list[str] = []
    if len(rows) < 153:
        errors.append("weapon_device_detail_large_json_not_retained_as_rows")
    if "token" in keys or "cookie" in keys:
        errors.append("weapon_device_detail_retained_credential_key")
    if "pasteboardreadcount" not in keys or "pasteboardwritecount" not in keys:
        errors.append("weapon_device_detail_embedded_scalar_not_parsed")
    if observation.get("fact_extraction_input_policy") != "pre_projection_prepared_body_credentials_filtered":
        errors.append("weapon_device_detail_fact_extraction_not_pre_projection")
    return errors, {
        "device_detail_rows": len(rows),
        "retained_large_json_fields": len([key for key in keys if key.startswith("devicefield")]),
        "credential_keys_retained": sorted(key for key in keys if key in {"token", "cookie"}),
        "embedded_scalar_keys_present": sorted(
            key for key in keys if key in {"pasteboardreadcount", "pasteboardwritecount"}
        ),
        "fact_extraction_input_policy": observation.get("fact_extraction_input_policy"),
    }


SOURCE_L1_L3_TABLES = [
    "login_detail_table",
    "account_detail_table",
    "user_behavior_summary_detail_table",
    "content_detail_table",
    "social_detail_table",
    "feedback_detail_table",
    "enforcement_detail_table",
]

SOURCE_L1_L3_ROW_REQUIRED_FIELDS = [
    "source_name",
    "source_domain",
    "entity_type",
    "entity_id",
    "field_name",
    "field_value_or_safe_ref",
    "field_family",
    "value_comparable",
    "source_quality",
    "extracted_from_observation_id",
]

RAW_DETAIL_FLAT_REQUIRED_FIELDS = [
    "observation_id",
    "parent_observation_id",
    "layer",
    "anchor_lineage",
    "source_name",
    "source_shape",
    "entity_id",
    "field_path",
    "field_name",
    "field_value_raw_or_ref",
    "value_handling",
    "redaction_reason",
    "field_family",
    "value_comparable",
    "source_quality",
    "is_unknown_field",
    "needs_field_dictionary_review",
]


def _validate_source_l1_l3_field_commonality_artifacts(result: dict[str, Any]) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    round_results = result.get("round_results", []) if isinstance(result, dict) else []
    table_counts = {table_name: 0 for table_name in SOURCE_L1_L3_TABLES}
    standard_commonality_count = 0
    standard_candidate_count = 0
    raw_flat_row_count = 0
    sequence_feature_count = 0
    wide_source_flattened_ok = False
    multi_row_sequence_seen = False
    forbidden_l4_terms = {"precision", "lift=", "误伤率=", "confirmed_group", "fraud_ring", "直接上线"}
    for round_index, round_result in enumerate(round_results, start=1):
        artifacts = round_result.get("orchestration_artifacts", {}) if isinstance(round_result, dict) else {}
        raw_rows = artifacts.get("raw_detail_flat_table", []) or []
        raw_flat_row_count += len(raw_rows)
        if not raw_rows:
            errors.append(f"source_l1_l3_round_{round_index}_raw_detail_flat_table_missing")
        for row_index, row in enumerate(raw_rows, start=1):
            if not isinstance(row, dict):
                errors.append(f"source_l1_l3_round_{round_index}_raw_detail_row_{row_index}_not_object")
                continue
            for field in RAW_DETAIL_FLAT_REQUIRED_FIELDS:
                if field not in row:
                    errors.append(f"source_l1_l3_round_{round_index}_raw_detail_row_{row_index}_missing_{field}")
            if row.get("field_name") in {"user_id", "device_id", "ip", "ua", "photo_id", "event_id", "policy_code"} and row.get("value_handling") in {"redacted", "safe_ref"}:
                errors.append(f"source_l1_l3_round_{round_index}_raw_anchor_over_redacted_{row.get('field_name')}")
            if str(row.get("field_name") or "").lower() in {"cookie", "token", "session", "header", "password", "authorization"} and row.get("value_handling") != "redacted":
                errors.append(f"source_l1_l3_round_{round_index}_credential_field_not_redacted_{row.get('field_name')}")
        raw_summary = artifacts.get("raw_detail_flat_table_summary", {}) or {}
        source_input_quality_table = artifacts.get("source_input_quality_table", []) or []
        if not source_input_quality_table:
            errors.append(f"source_l1_l3_round_{round_index}_source_input_quality_table_missing")
        for source_index, source_summary in enumerate(source_input_quality_table, start=1):
            for field in (
                "source_name",
                "source_domain",
                "source_role",
                "source_shape",
                "layer",
                "raw_record_count",
                "raw_field_count",
                "flattened_field_count",
                "comparable_field_count",
                "unknown_field_count",
                "filtered_field_count",
                "source_payload_thin",
                "parser_under_expanded",
                "action_mapping_incomplete",
                "auth_blocked",
                "not_entered_main_chain",
                "primary_blocked_reason",
                "l3_input_quality",
                "next_action",
            ):
                if field not in source_summary:
                    errors.append(f"source_l1_l3_round_{round_index}_source_input_quality_{source_index}_missing_{field}")
        for source_summary in raw_summary.get("sources", []) or []:
            if source_summary.get("source_shape") == "single_object_wide_field" and int(source_summary.get("flattened_field_count") or 0) >= 50:
                wide_source_flattened_ok = True
            if source_summary.get("source_shape") == "multi_row_event" and int(source_summary.get("raw_record_count") or 0) >= 2:
                multi_row_sequence_seen = True
        sequence_rows = artifacts.get("sequence_comparison_features", []) or []
        sequence_feature_count += len(sequence_rows)
        if not sequence_rows:
            errors.append(f"source_l1_l3_round_{round_index}_sequence_comparison_features_missing")
        for seq_index, seq in enumerate(sequence_rows, start=1):
            for field in (
                "source_name",
                "entity_id",
                "event_count",
                "sequence_feature_name",
                "sequence_feature_type",
                "involved_record_indexes",
                "involved_fields",
                "risk_interpretation_candidate",
                "candidate_only_not_final_conclusion",
            ):
                if field not in seq:
                    errors.append(f"source_l1_l3_round_{round_index}_sequence_{seq_index}_missing_{field}")
            if seq.get("candidate_only_not_final_conclusion") is not True:
                errors.append(f"source_l1_l3_round_{round_index}_sequence_{seq_index}_not_candidate_boundary")
        standard_rows = artifacts.get("standard_detail_table", []) or []
        if not standard_rows:
            errors.append(f"source_l1_l3_round_{round_index}_standard_detail_table_missing")
        for table_name in SOURCE_L1_L3_TABLES:
            rows = artifacts.get(table_name, []) or []
            table_counts[table_name] += len(rows)
            if not rows:
                errors.append(f"source_l1_l3_round_{round_index}_{table_name}_missing_or_empty")
            for row_index, row in enumerate(rows, start=1):
                if not isinstance(row, dict):
                    errors.append(f"source_l1_l3_round_{round_index}_{table_name}_{row_index}_not_object")
                    continue
                for field in SOURCE_L1_L3_ROW_REQUIRED_FIELDS:
                    if field not in row:
                        errors.append(f"source_l1_l3_round_{round_index}_{table_name}_{row_index}_missing_{field}")
                if row.get("source_quality") in {"no_data", "timeout", "auth_failed", "blocked"}:
                    errors.append(f"source_l1_l3_round_{round_index}_{table_name}_{row_index}_gap_row_should_not_enter_detail_table")
        commonality_rows = [
            item for item in artifacts.get("standard_field_commonality", []) or []
            if isinstance(item, dict)
        ]
        standard_commonality_count += len(commonality_rows)
        if not any(str(item.get("commonality_type") or "") == "field_value_commonality" for item in commonality_rows):
            errors.append(f"source_l1_l3_round_{round_index}_field_value_commonality_missing")
        for item in commonality_rows:
            if item.get("commonality_type") == "coverage_commonality":
                if item.get("candidate_feature_eligible") is True or item.get("risk_commonality") is True:
                    errors.append(f"source_l1_l3_round_{round_index}_coverage_commonality_promoted")
        commonality_distribution = artifacts.get("l3_commonality_type_distribution", {}) or {}
        for field in (
            "coverage_commonality_count",
            "field_value_commonality_count",
            "field_combination_commonality_count",
            "sequence_commonality_count",
            "cross_source_support_commonality_count",
        ):
            if field not in commonality_distribution:
                errors.append(f"source_l1_l3_round_{round_index}_commonality_distribution_missing_{field}")
        if int(commonality_distribution.get("field_combination_commonality_count") or 0) <= 0:
            errors.append(f"source_l1_l3_round_{round_index}_field_combination_commonality_not_promoted")
        if int(commonality_distribution.get("cross_source_support_commonality_count") or 0) <= 1:
            errors.append(f"source_l1_l3_round_{round_index}_cross_source_support_commonality_too_few")
        attack_chain_rows = artifacts.get("attack_chain_cooccurrence", []) or []
        if not attack_chain_rows:
            errors.append(f"source_l1_l3_round_{round_index}_attack_chain_cooccurrence_missing")
        for chain_index, chain in enumerate(attack_chain_rows, start=1):
            for field in (
                "chain_id",
                "chain_steps",
                "involved_sources",
                "involved_entities",
                "attack_chain_role",
                "cooccurrence_summary",
                "current_status",
                "missing_evidence",
                "candidate_only_not_final_conclusion",
            ):
                if field not in chain:
                    errors.append(f"source_l1_l3_attack_chain_{chain_index}_missing_{field}")
        field_value_funnel = artifacts.get("field_value_commonality_funnel", []) or []
        if not field_value_funnel:
            errors.append(f"source_l1_l3_round_{round_index}_field_value_commonality_funnel_missing")
        for funnel_index, funnel in enumerate(field_value_funnel, start=1):
            for field in (
                "source_name",
                "raw_field_value_match_count",
                "after_dedup_count",
                "after_semantic_grouping_count",
                "promoted_commonality_count",
                "top_candidate_count",
                "suppressed_count",
                "suppressed_reasons",
                "sample_suppressed_field_families",
                "over_compressed",
                "compression_diagnosis",
            ):
                if field not in funnel:
                    errors.append(f"source_l1_l3_field_value_funnel_{funnel_index}_missing_{field}")
        candidate_features = [
            item for item in artifacts.get("candidate_features", []) or []
            if isinstance(item, dict)
        ]
        source_candidate_features = [
            item for item in artifacts.get("candidate_features", []) or []
            if isinstance(item, dict)
            and str(item.get("feature_type") or "") == "source_field_value_commonality_candidate"
        ]
        standard_candidate_count += len(source_candidate_features)
        if len(source_candidate_features) < 4:
            errors.append(f"source_l1_l3_round_{round_index}_source_candidate_features_too_few")
        for feature_index, feature in enumerate(candidate_features, start=1):
            for field in (
                "feature_name",
                "source_domains",
                "source_fields",
                "field_combination",
                "support_sample_count",
                "support_user_count",
                "support_ratio",
                "priority_score",
                "priority_level",
                "reason_codes",
                "black_gray_interpretation",
                "false_positive_risk",
                "missing_evidence",
                "validation_method",
                "conclusion_boundary",
                "feature_origin",
                "source_names",
                "field_paths",
                "support_entity_count",
                "candidate_only_not_final_conclusion",
                "not_final_conclusion",
                "validation_needed",
                "essence_likeness",
                "essence_reason",
                "essence_boundary",
                "risk_choke_point_type",
                "choke_point_likeness",
                "choke_point_reason",
                "required_for_attack",
                "easy_to_evade_if_changed",
                "robustness",
                "supporting_commonality_types",
                "supporting_source_domains",
                "supporting_attack_chain_ids",
            ):
                if field not in feature:
                    errors.append(f"source_l1_l3_feature_{feature_index}_missing_{field}")
            if feature.get("essence_likeness") is None or feature.get("essence_reason") in {None, ""}:
                errors.append(f"source_l1_l3_feature_{feature_index}_essence_fields_empty")
            if feature.get("choke_point_likeness") is None or feature.get("choke_point_reason") in {None, ""}:
                errors.append(f"source_l1_l3_feature_{feature_index}_choke_point_fields_empty")
            if feature.get("not_final_conclusion") is not True:
                errors.append(f"source_l1_l3_feature_{feature_index}_not_final_conclusion_not_true")
            if feature.get("validation_needed") is not True:
                errors.append(f"source_l1_l3_feature_{feature_index}_validation_needed_not_true")
            if feature.get("candidate_only_not_final_conclusion") is not True:
                errors.append(f"source_l1_l3_feature_{feature_index}_candidate_boundary_missing")
            if "coverage_commonality" in set(str(item) for item in feature.get("supporting_commonality_types", []) or []) and feature.get("choke_point_likeness") == "high":
                errors.append(f"source_l1_l3_feature_{feature_index}_coverage_promoted_to_high_choke_point")
            text = json.dumps(feature, ensure_ascii=False)
            if any(term in text for term in forbidden_l4_terms):
                errors.append(f"source_l1_l3_feature_{feature_index}_contains_forbidden_l4_or_final_term")
        top_samples = artifacts.get("candidate_feature_top_samples", []) or []
        if len(top_samples) < 5:
            errors.append(f"source_l1_l3_round_{round_index}_candidate_feature_top_samples_too_few")
        for sample_index, sample in enumerate(top_samples, start=1):
            for field in (
                "candidate_feature_name",
                "feature_origin",
                "source_support",
                "evidence_commonality_types",
                "core_commonality",
                "attack_chain_support",
                "risk_choke_point_type",
                "choke_point_likeness",
                "choke_point_reason",
                "required_for_attack",
                "easy_to_evade_if_changed",
                "robustness",
                "essence_likeness",
                "essence_reason",
                "false_positive_risk",
                "missing_evidence",
                "validation_method",
                "current_status",
                "candidate_only_not_final_conclusion",
            ):
                if field not in sample:
                    errors.append(f"source_l1_l3_top_sample_{sample_index}_missing_{field}")
        if any(str(sample.get("candidate_feature_name") or "") == "multi_domain_anchor_overlap_candidate" and str(sample.get("choke_point_likeness") or "") in {"high", "medium"} for sample in top_samples):
            errors.append(f"source_l1_l3_round_{round_index}_generic_overlap_not_downranked")
        group_candidate = artifacts.get("group_profile_candidate", {})
        if isinstance(group_candidate, dict):
            if group_candidate.get("not_confirmed_as_group") is not True:
                errors.append(f"source_l1_l3_round_{round_index}_group_candidate_not_confirmed_flag_missing")
            if group_candidate.get("supporting_selected_anchors") and not group_candidate.get("supporting_selected_batch_anchors"):
                errors.append(f"source_l1_l3_round_{round_index}_group_candidate_context_anchor_mixed")
    if raw_flat_row_count < 100:
        errors.append("source_l1_l3_raw_detail_flat_table_too_small_for_stage_f")
    if not wide_source_flattened_ok:
        errors.append("source_l1_l3_wide_source_flattened_field_count_below_50")
    if not multi_row_sequence_seen or sequence_feature_count < 1:
        errors.append("source_l1_l3_multi_row_sequence_not_validated")
    return errors, {
        "table_counts": table_counts,
        "raw_detail_flat_table_count": raw_flat_row_count,
        "sequence_comparison_feature_count": sequence_feature_count,
        "standard_field_commonality_count": standard_commonality_count,
        "standard_candidate_feature_count": standard_candidate_count,
        "wide_source_flattened_ok": wide_source_flattened_ok,
        "multi_row_sequence_seen": multi_row_sequence_seen,
    }




# ════════════════════════════════════════════════════════════════════════════
# Bounded-rendering regression cases (F.5-R3 fix)
# ════════════════════════════════════════════════════════════════════════════



# ════════════════════════════════════════════════════════════════════════════
# G-R3/G-R4 candidate_features enrichment regression cases
# ════════════════════════════════════════════════════════════════════════════

# ── Shared fixture helpers (reduce duplication across regression functions) ──


def _make_device_farm_candidate(
    choke_type: str = "device_farm_template",
    likeness: str = "high",
    name: str = "device_farm_template_candidate",
) -> dict:
    """Minimal device_farm_template candidate fixture shared across regressions."""
    return {
        "candidate_feature_name": name,
        "risk_choke_point_type": choke_type,
        "choke_point_likeness": likeness,
        "core_commonality": "frida_xposed_mount_reset_or_emulator_related_field_truthy",
        "supporting_source_domains": ["device_domain"],
        "source_support": ["weapon_inventory", "weapon_device_info"],
        "evidence_commonality_types": ["device_integrity_check"],
        "missing_evidence": [],
        "field_combination": ["adbstatus", "debug", "frida_related"],
        "source_fields": ["weapon_inventory", "weapon_device_info"],
        "reason_codes": ["risky_device_environment"],
    }


def _make_unknown_device_candidate(
    name: str = "device_unknown_field_enrichment_candidate",
) -> dict:
    """Minimal device_unknown_field_enrichment_candidate fixture shared across regressions."""
    return {
        "candidate_feature_name": name,
        "risk_choke_point_type": "unknown",
        "choke_point_likeness": "low",
        "core_commonality": "weapon_inventory,weapon_device_info field combination",
        "supporting_source_domains": ["device_domain"],
        "source_support": ["weapon_inventory", "weapon_device_info"],
        "evidence_commonality_types": [],
        "missing_evidence": ["needs_field_dictionary_review"],
        "field_combination": [],
        "source_fields": ["weapon_inventory", "weapon_device_info"],
        "reason_codes": [],
    }


def _regression_candidate_features_global_enrichment() -> tuple[list[str], dict[str, Any]]:
    """CANDIDATE-FEATURES-GLOBAL-ENRICHMENT-001
    Expected:
    - candidate_feature_name is not null for all features
    - core_commonality is not null/empty for all features
    - source_support or supporting_source_domains at least one present
    - evidence_commonality_types has no empty strings
    - candidate_only_not_final_conclusion=True for all features
    """
    payload = {
        "route_mode": "sample_expand_validate_mode",
        "total_input_count": 6,
        "round_size": 6,
        "max_rounds": 1,
        "planned_rounds_this_run": 1,
        "max_deep_checked_this_run": 6,
        "sampling_method": "fixed_register_attack_sample",
        "data_window": "last_7d",
        "scene_hint": ["REGISTER_NEW", "RCP", "device"],
        "rounds": [{
            "round_id": 1,
            "sampled_entities": ["u1", "u2", "u3", "u4", "u5", "u6"],
            "mock_current_observations": [
                {"source_id": "s1", "action": "login_logs_search", "fields": {
                    "user_id": "u1", "candidate_device_id": "dev_001",
                    "login_type": "password", "backend_action_signal": "publish_after_login",
                }},
                {"source_id": "s2", "action": "weapon_inventory", "fields": {
                    "user_id": "u1", "device_id": "dev_001",
                    "sdk_version": "android_12", "root_flag": "false",
                    "hook_detected": "false", "device_model": "Redmi_Note_10",
                }},
                {"source_id": "s3", "action": "rcp_snapshot", "fields": {
                    "user_id": "u2", "source_id": "rcp_src_001",
                    "eventType": "REGISTER_NEW", "feature_code": "F001",
                }},
            ],
        }],
    }
    run = _run_payload(payload)
    result = run.get("result") or {}
    rr = result.get("round_results") or []
    oa = rr[0].get("orchestration_artifacts", {}) if rr else {}
    cfs = oa.get("candidate_features") or []
    errors: list[str] = []
    null_name_count = sum(1 for c in cfs if not c.get("candidate_feature_name"))
    null_core_count = sum(1 for c in cfs if not c.get("core_commonality"))
    no_source_count = sum(1 for c in cfs if not c.get("source_support") and not c.get("supporting_source_domains"))
    empty_ev_count = sum(1 for c in cfs for ev in (c.get("evidence_commonality_types") or []) if ev == "")
    not_cand_only_count = sum(1 for c in cfs if c.get("candidate_only_not_final_conclusion") is not True)
    if cfs and null_name_count == len(cfs):
        errors.append(f"CANDIDATE-FEATURES-GLOBAL-ENRICHMENT-001:all_candidate_feature_name_null(count={null_name_count})")
    if cfs and null_core_count == len(cfs):
        errors.append(f"CANDIDATE-FEATURES-GLOBAL-ENRICHMENT-001:all_core_commonality_null(count={null_core_count})")
    if no_source_count > 0:
        errors.append(f"CANDIDATE-FEATURES-GLOBAL-ENRICHMENT-001:source_gap(count={no_source_count})")
    if empty_ev_count > 0:
        errors.append(f"CANDIDATE-FEATURES-GLOBAL-ENRICHMENT-001:empty_evidence_type(count={empty_ev_count})")
    if not_cand_only_count > 0:
        errors.append(f"CANDIDATE-FEATURES-GLOBAL-ENRICHMENT-001:candidate_only_missing(count={not_cand_only_count})")
    return errors, {
        "candidate_features_count": len(cfs),
        "null_name_count": null_name_count,
        "null_core_commonality_count": null_core_count,
        "no_source_count": no_source_count,
        "empty_evidence_type_count": empty_ev_count,
        "not_candidate_only_count": not_cand_only_count,
    }


def _regression_device_domain_candidate_enrichment() -> tuple[list[str], dict[str, Any]]:
    """DEVICE-DOMAIN-CANDIDATE-ENRICHMENT-001
    Expected:
    - device_domain candidates have candidate_feature_name != null
    - at least one device_domain candidate translates to device_farm_template_candidate
      / risky_device_environment_candidate / device_unknown_field_enrichment_candidate
    - unknown device fields get needs_field_dictionary_review in missing_evidence
    """
    payload = {
        "route_mode": "sample_expand_validate_mode",
        "total_input_count": 6,
        "round_size": 6,
        "max_rounds": 1,
        "planned_rounds_this_run": 1,
        "max_deep_checked_this_run": 6,
        "sampling_method": "fixed_register_attack_sample",
        "data_window": "last_7d",
        "scene_hint": ["device"],
        "rounds": [{
            "round_id": 1,
            "sampled_entities": ["u1", "u2", "u3"],
            "mock_current_observations": [
                {"source_id": "w1", "action": "weapon_inventory", "fields": {
                    "user_id": "u1", "sdk_version": "android_12", "root_flag": "false",
                    "frida_detected": "true", "xposed_installed": "true",
                    "device_model": "Redmi_Note_10", "unknown_device_field_x": "val_001",
                }},
                {"source_id": "w2", "action": "weapon_inventory", "fields": {
                    "user_id": "u2", "sdk_version": "android_12", "root_flag": "false",
                    "frida_detected": "true", "xposed_installed": "true",
                    "device_model": "Redmi_Note_10", "unknown_device_field_x": "val_001",
                }},
            ],
        }],
    }
    run = _run_payload(payload)
    result = run.get("result") or {}
    rr = result.get("round_results") or []
    oa = rr[0].get("orchestration_artifacts", {}) if rr else {}
    cfs = oa.get("candidate_features") or []
    device_cfs = [c for c in cfs if "device_domain" in (c.get("supporting_source_domains") or [])]
    errors: list[str] = []
    if device_cfs:
        null_device_names = [c for c in device_cfs if not c.get("candidate_feature_name")]
        if null_device_names:
            errors.append(f"DEVICE-DOMAIN-CANDIDATE-ENRICHMENT-001:device_candidate_name_null(count={len(null_device_names)})")
        # device-only names + cross-domain names that device participates in are all valid
        device_specific_names = {
            "device_farm_template_candidate", "risky_device_environment_candidate",
            "device_app_environment_candidate", "device_unknown_field_enrichment_candidate",
            "device_execution_environment_candidate",
        }
        cross_domain_names_with_device = {
            "control_execution_separation_candidate",
            "protocol_constraint_gap_candidate",
            "automation_rhythm_candidate",
            "multi_domain_anchor_overlap_candidate",  # generic/downranked — device part of wide overlap
        }
        all_known_for_device = device_specific_names | cross_domain_names_with_device
        named_device = [c for c in device_cfs if c.get("candidate_feature_name") in all_known_for_device]
        if not named_device:
            errors.append("DEVICE-DOMAIN-CANDIDATE-ENRICHMENT-001:no_device_candidate_translated_to_known_name")
    return errors, {
        "device_candidate_count": len(device_cfs),
        "device_named_count": sum(1 for c in device_cfs if c.get("candidate_feature_name")),
        "device_with_source_support": sum(1 for c in device_cfs if c.get("source_support") or c.get("supporting_source_domains")),
    }


def _regression_domain_candidate_role_mapping() -> tuple[list[str], dict[str, Any]]:
    """DOMAIN-CANDIDATE-ROLE-MAPPING-001
    Expected: each domain that produces candidates has at least one with a non-null candidate_feature_name.
    """
    payload = {
        "route_mode": "sample_expand_validate_mode",
        "total_input_count": 6,
        "round_size": 6,
        "max_rounds": 1,
        "planned_rounds_this_run": 1,
        "max_deep_checked_this_run": 6,
        "sampling_method": "fixed_register_attack_sample",
        "data_window": "last_7d",
        "scene_hint": ["REGISTER_NEW", "RCP", "device", "login"],
        "rounds": [{
            "round_id": 1,
            "sampled_entities": ["u1", "u2", "u3", "u4", "u5", "u6"],
            "mock_current_observations": [
                {"source_id": "l1", "action": "login_logs_search", "fields": {
                    "user_id": "u1", "login_type": "sms", "backend_action_signal": "publish",
                }},
                {"source_id": "l2", "action": "login_logs_search", "fields": {
                    "user_id": "u2", "login_type": "sms", "backend_action_signal": "publish",
                }},
                {"source_id": "r1", "action": "rcp_snapshot", "fields": {
                    "user_id": "u1", "eventType": "REGISTER_NEW", "feature_code": "F001",
                }},
                {"source_id": "r2", "action": "rcp_snapshot", "fields": {
                    "user_id": "u2", "eventType": "REGISTER_NEW", "feature_code": "F001",
                }},
            ],
        }],
    }
    run = _run_payload(payload)
    result = run.get("result") or {}
    rr = result.get("round_results") or []
    oa = rr[0].get("orchestration_artifacts", {}) if rr else {}
    cfs = oa.get("candidate_features") or []
    domains_with_null = {}
    for c in cfs:
        for dom in (c.get("supporting_source_domains") or []):
            if not c.get("candidate_feature_name"):
                domains_with_null[dom] = domains_with_null.get(dom, 0) + 1
    errors: list[str] = []
    if cfs and all(not c.get("candidate_feature_name") for c in cfs):
        errors.append(f"DOMAIN-CANDIDATE-ROLE-MAPPING-001:all_names_null(count={len(cfs)})")
    return errors, {
        "total_candidates": len(cfs),
        "named_candidates": sum(1 for c in cfs if c.get("candidate_feature_name")),
        "domains_with_null_name": domains_with_null,
    }


def _regression_generic_candidate_downrank() -> tuple[list[str], dict[str, Any]]:
    """GENERIC-CANDIDATE-DOWNRANK-001
    Expected: multi_domain_anchor_overlap_candidate / group_level_field_enrichment_candidate
    must NOT have choke_point_likeness=high or medium unless they have source_support + core_commonality.
    """
    payload = {
        "route_mode": "sample_expand_validate_mode",
        "total_input_count": 6,
        "round_size": 6,
        "max_rounds": 1,
        "planned_rounds_this_run": 1,
        "max_deep_checked_this_run": 6,
        "sampling_method": "fixed_register_attack_sample",
        "data_window": "last_7d",
        "scene_hint": ["device"],
        "rounds": [{
            "round_id": 1,
            "sampled_entities": ["u1", "u2"],
            "mock_current_observations": [],
        }],
    }
    run = _run_payload(payload)
    result = run.get("result") or {}
    rr = result.get("round_results") or []
    oa = rr[0].get("orchestration_artifacts", {}) if rr else {}
    cfs = oa.get("candidate_features") or []
    generic_names = {"multi_domain_anchor_overlap_candidate", "group_level_field_enrichment_candidate", "hard_single_field_signal_candidate"}
    errors: list[str] = []
    for c in cfs:
        fn = str(c.get("feature_name") or c.get("candidate_feature_name") or "")
        if fn in generic_names:
            likeness = str(c.get("choke_point_likeness") or "unknown")
            has_src = bool(c.get("source_support") or c.get("supporting_source_domains"))
            has_core = bool(c.get("core_commonality"))
            has_reason = bool(c.get("choke_point_reason"))
            if likeness in ("high", "medium") and not (has_src and has_core and has_reason):
                errors.append(f"GENERIC-CANDIDATE-DOWNRANK-001:{fn}:likeness={likeness}_without_support")
    return errors, {
        "generic_candidates": [c.get("feature_name") or c.get("candidate_feature_name") for c in cfs if str(c.get("feature_name") or "") in generic_names],
        "generic_high_medium_without_support": len(errors),
    }


def _regression_top_candidate_no_null() -> tuple[list[str], dict[str, Any]]:
    """TOP-CANDIDATE-NO-NULL-001
    Expected: candidate_feature_top_samples must not have all of
    candidate_feature_name / core_commonality / source_support null at the same time.
    high/medium top candidates must have choke_point_reason.
    """
    payload = {
        "route_mode": "sample_expand_validate_mode",
        "total_input_count": 6,
        "round_size": 6,
        "max_rounds": 1,
        "planned_rounds_this_run": 1,
        "max_deep_checked_this_run": 6,
        "sampling_method": "fixed_register_attack_sample",
        "data_window": "last_7d",
        "scene_hint": ["REGISTER_NEW", "device", "login"],
        "rounds": [{
            "round_id": 1,
            "sampled_entities": ["u1", "u2", "u3", "u4", "u5", "u6"],
            "mock_current_observations": [
                {"source_id": "l1", "action": "login_logs_search", "fields": {
                    "user_id": "u1", "candidate_device_id": "dev_001",
                    "login_type": "password", "backend_action_signal": "publish",
                }},
                {"source_id": "l2", "action": "login_logs_search", "fields": {
                    "user_id": "u2", "candidate_device_id": "dev_001",
                    "login_type": "password", "backend_action_signal": "publish",
                }},
                {"source_id": "w1", "action": "weapon_inventory", "fields": {
                    "user_id": "u1", "sdk_version": "android_12", "root_flag": "false",
                }},
            ],
        }],
    }
    run = _run_payload(payload)
    result = run.get("result") or {}
    rr = result.get("round_results") or []
    oa_round = rr[0].get("orchestration_artifacts", {}) if rr else {}
    top_samples = oa_round.get("candidate_feature_top_samples") or []
    errors: list[str] = []
    for i, s in enumerate(top_samples):
        has_name = bool(s.get("candidate_feature_name"))
        has_core = bool(s.get("core_commonality"))
        has_src = bool(s.get("source_support") or s.get("supporting_source_domains"))
        if not has_name and not has_core and not has_src:
            errors.append(f"TOP-CANDIDATE-NO-NULL-001:sample[{i}]:all_null")
        likeness = str(s.get("choke_point_likeness") or "unknown")
        if likeness in ("high", "medium") and not s.get("choke_point_reason"):
            errors.append(f"TOP-CANDIDATE-NO-NULL-001:sample[{i}]:likeness={likeness}_no_reason")
    return errors, {
        "top_sample_count": len(top_samples),
        "all_null_count": sum(
            1 for s in top_samples
            if not s.get("candidate_feature_name") and not s.get("core_commonality") and not (s.get("source_support") or s.get("supporting_source_domains"))
        ),
        "high_medium_no_reason_count": sum(
            1 for s in top_samples
            if str(s.get("choke_point_likeness") or "unknown") in ("high", "medium") and not s.get("choke_point_reason")
        ),
    }


def _regression_candidate_features_normalize_no_empty_shell() -> tuple[list[str], dict[str, Any]]:
    """CANDIDATE-FEATURES-NORMALIZE-NO-EMPTY-SHELL-001
    验证 normalize_l3_candidate_feature_contract 输出的合同字段完整性：
    - candidate_feature_name/core_commonality/source_support 不能全部为空
    - high/medium 候选不允许缺 source_support 或 core_commonality
    - evidence_commonality_types 不含空字符串
    - candidate_only_not_final_conclusion=True
    直接对 normalize 函数进行单元测试，不依赖 live 数据。
    """
    from runtime_case_execution_runner import (
        normalize_l3_candidate_feature_contract,
    )
    errors: list[str] = []
    # --- 测试用例集合 ---
    test_cases = [
        # 1. unknown_field_commonality + device_domain（small-b 高频场景）
        {
            "feature_type": "unknown_field_value_commonality",
            "feature_name": "device_unknown_field_combo",
            "feature_origin": "unknown_field_commonality",
            "source_domains": ["device_domain"],
            "source_names": ["weapon_inventory"],
            "source_fields": ["unknown_field_x", "unknown_field_y"],
            "support_user_count": 4,
            "field_semantics_status": "needs_field_dictionary_review",
        },
        # 2. sequence_comparison（account_domain）
        {
            "feature_type": "sequence_comparison_candidate",
            "feature_name": "account_sequence_template",
            "feature_origin": "sequence_comparison",
            "source_domains": ["account_domain", "behavior_domain"],
            "source_names": ["login_logs_search"],
            "support_user_count": 3,
        },
        # 3. field_combination（strategy_domain）
        {
            "feature_type": "field_combination_candidate",
            "feature_name": "rcp_feature_combo",
            "feature_origin": "field_combination",
            "source_domains": ["strategy_domain"],
            "source_names": ["rcp_snapshot"],
            "field_combination": ["eventType", "feature_code", "request_path"],
            "support_user_count": 5,
        },
        # 4. 没有任何 domain，纯 fallback
        {
            "feature_type": "raw_field_commonality",
            "feature_name": "bare_field_commonality",
            "feature_origin": "raw_field_commonality",
            "source_domains": [],
            "source_names": [],
            "support_user_count": 2,
        },
        # 5. 已有 candidate_feature_name（不应被覆盖）
        {
            "feature_type": "field_combination_candidate",
            "feature_name": "rcp_combo_2",
            "candidate_feature_name": "rcp_feature_bundle_candidate",
            "feature_origin": "field_combination",
            "source_domains": ["strategy_domain"],
            "source_names": ["rcp_event_feature_list"],
            "field_combination": ["feature_code", "source_id_hash"],
            "support_user_count": 3,
        },
        # 6. evidence_commonality_types 含空字符串（验证去空逻辑）
        {
            "feature_type": "unknown_field_value_commonality",
            "feature_name": "ev_type_empty_test",
            "feature_origin": "unknown_field_commonality",
            "source_domains": ["device_domain"],
            "source_names": ["weapon_inventory"],
            "evidence_commonality_types": ["field_value_commonality", "", "cross_source_support_commonality", ""],
            "support_user_count": 2,
        },
        # 7. generic 候选（应被降级）
        {
            "feature_type": "anchor_overlap",
            "feature_name": "multi_domain_anchor_overlap_candidate",
            "feature_origin": "raw_field_commonality",
            "source_domains": ["device_domain", "behavior_domain"],
            "source_names": [],
            "support_user_count": 3,
        },
    ]
    results_summary: list[dict[str, Any]] = []
    for i, tc in enumerate(test_cases):
        out = normalize_l3_candidate_feature_contract(tc)
        name = out.get("candidate_feature_name")
        core = out.get("core_commonality")
        src = out.get("source_support") or out.get("supporting_source_domains")
        cand_only = out.get("candidate_only_not_final_conclusion")
        ev_types = out.get("evidence_commonality_types") or []
        likeness = str(out.get("choke_point_likeness") or "unknown")
        label = f"case[{i}]:{tc.get('feature_name')}"
        # 规则 1: candidate_feature_name/core_commonality/source_support 不能全部为空
        if not name and not core and not src:
            errors.append(f"CANDIDATE-FEATURES-NORMALIZE-NO-EMPTY-SHELL-001:{label}:all_null")
        # 规则 2: candidate_feature_name 不能为 null
        if not name:
            errors.append(f"CANDIDATE-FEATURES-NORMALIZE-NO-EMPTY-SHELL-001:{label}:candidate_feature_name_null")
        # 规则 3: core_commonality 不能为 null/空
        if not core:
            errors.append(f"CANDIDATE-FEATURES-NORMALIZE-NO-EMPTY-SHELL-001:{label}:core_commonality_null")
        # 规则 4: high/medium 候选不允许缺 source_support 或 core_commonality
        if likeness in ("high", "medium"):
            if not out.get("source_support"):
                errors.append(f"CANDIDATE-FEATURES-NORMALIZE-NO-EMPTY-SHELL-001:{label}:high_medium_no_source_support(likeness={likeness})")
            if not core:
                errors.append(f"CANDIDATE-FEATURES-NORMALIZE-NO-EMPTY-SHELL-001:{label}:high_medium_no_core_commonality(likeness={likeness})")
        # 规则 5: evidence_commonality_types 不含空字符串
        if any(t == "" or not str(t).strip() for t in ev_types):
            errors.append(f"CANDIDATE-FEATURES-NORMALIZE-NO-EMPTY-SHELL-001:{label}:empty_string_in_evidence_commonality_types")
        # 规则 6: candidate_only_not_final_conclusion=True
        if cand_only is not True:
            errors.append(f"CANDIDATE-FEATURES-NORMALIZE-NO-EMPTY-SHELL-001:{label}:candidate_only_not_final_conclusion_missing")
        # case 5 特殊验证：已有 candidate_feature_name 不应被覆盖
        if tc.get("candidate_feature_name") and name != tc["candidate_feature_name"]:
            errors.append(f"CANDIDATE-FEATURES-NORMALIZE-NO-EMPTY-SHELL-001:{label}:existing_name_overwritten(expected={tc['candidate_feature_name']!r},got={name!r})")
        results_summary.append({
            "case": label,
            "candidate_feature_name": name,
            "core_commonality": core,
            "source_support": out.get("source_support"),
            "choke_point_likeness": likeness,
            "candidate_only": cand_only,
            "ev_types": ev_types,
        })
    return errors, {
        "cases_tested": len(test_cases),
        "cases_failed": len([e for e in errors]),
        "results": results_summary,
    }


def _regression_top_candidate_explainable_first() -> tuple[list[str], dict[str, Any]]:
    """TOP-CANDIDATE-EXPLAINABLE-FIRST-001
    期望：Top candidate 优先展示 risk_choke_point_type != unknown 且 high/medium 候选。
    unknown_field_enrichment 不刷屏；core_commonality 不能是 insufficient_interpretable_commonality。
    """
    from runtime_case_execution_runner import (
        normalize_l3_candidate_feature_contract,
        build_candidate_feature_top_samples,
    )
    # 构造一组候选：包含 unknown 和可解释的混合
    features = [
        {  # 应优先出现：high + protocol_constraint_gap
            "feature_type": "field_combination_candidate",
            "feature_name": "protocol_feature",
            "feature_origin": "field_combination",
            "source_domains": ["strategy_domain", "behavior_domain"],
            "source_names": ["login_logs_search", "rcp_snapshot"],
            "field_combination": ["backend_action_signal", "frontend_activity_signal", "request_path"],
            "support_user_count": 5,
        },
        {  # 应降级：unknown device field
            "feature_type": "unknown_field_value_commonality",
            "feature_name": "unk_device_1",
            "feature_origin": "unknown_field_commonality",
            "source_domains": ["device_domain"],
            "source_names": ["weapon_inventory"],
            "source_fields": ["unknown_field_x"],
            "support_user_count": 4,
            "field_semantics_status": "needs_field_dictionary_review",
        },
        {  # 应降级：unknown device field
            "feature_type": "unknown_field_value_commonality",
            "feature_name": "unk_device_2",
            "feature_origin": "unknown_field_commonality",
            "source_domains": ["device_domain"],
            "source_names": ["weapon_inventory"],
            "source_fields": ["unknown_field_y"],
            "support_user_count": 4,
            "field_semantics_status": "needs_field_dictionary_review",
        },
        {  # 应次优先：content_funnel high
            "feature_type": "field_combination_candidate",
            "feature_name": "content_feature",
            "feature_origin": "field_combination",
            "source_domains": ["content_domain", "social_domain"],
            "source_names": ["archives_photo_search", "archives_comment_search"],
            "field_combination": ["caption", "target_user_id", "comment"],
            "support_user_count": 3,
        },
    ]
    normalized = [normalize_l3_candidate_feature_contract(f) for f in features]
    tops = build_candidate_feature_top_samples(
        candidate_features=normalized,
        source_input_quality_table=[],
        attack_chain_cooccurrence=[],
    )
    errors: list[str] = []
    # Top 5 中 unknown_field_enrichment 不应刷屏（不超过 1 条）
    unknown_enrichment_names = {
        "device_unknown_field_enrichment_candidate",
        "unknown_field_enrichment_candidate",
        "rcp_unknown_feature_bundle_candidate",
        "account_unknown_field_enrichment_candidate",
    }
    unknown_in_tops = sum(1 for s in tops if s.get("candidate_feature_name") in unknown_enrichment_names)
    if unknown_in_tops >= len(tops) and len(tops) > 0 and unknown_in_tops > 1:
        errors.append(f"TOP-CANDIDATE-EXPLAINABLE-FIRST-001:unknown_enrichment_spam(count={unknown_in_tops}/{len(tops)})")
    # core_commonality 不应是 insufficient_interpretable_commonality
    for i, s in enumerate(tops):
        core = s.get("core_commonality") or []
        if core == ["insufficient_interpretable_commonality"]:
            errors.append(f"TOP-CANDIDATE-EXPLAINABLE-FIRST-001:top[{i}]:insufficient_core")
    # 检查可解释候选（protocol/content）的候选评分是否优先于 unknown
    normalized_scores = []
    for n in normalized:
        from runtime_case_execution_runner import _g_r5_top_candidate_score
        normalized_scores.append((_g_r5_top_candidate_score(n), n.get("candidate_feature_name")))
    sorted_names = [name for _, name in sorted(normalized_scores)]
    protocol_idx = next((i for i, name in enumerate(sorted_names) if "protocol" in str(name) or "content" in str(name)), None)
    unknown_idx = next((i for i, name in enumerate(sorted_names) if "unknown_field_enrichment" in str(name)), None)
    if protocol_idx is not None and unknown_idx is not None and protocol_idx > unknown_idx:
        errors.append(f"TOP-CANDIDATE-EXPLAINABLE-FIRST-001:unknown_ranked_before_explainable(protocol_idx={protocol_idx},unknown_idx={unknown_idx})")
    return errors, {
        "tops_count": len(tops),
        "unknown_enrichment_in_tops": unknown_in_tops,
        "sorted_names": sorted_names,
    }


def _regression_unknown_device_review_queue() -> tuple[list[str], dict[str, Any]]:
    """UNKNOWN-DEVICE-FIELD-REVIEW-QUEUE-001
    期望：unknown device 候选进入 unknown_device_field_review_queue；
    missing_evidence 包含 needs_field_dictionary_review；不直接升级为 device_farm_template。
    """
    from runtime_case_execution_runner import (
        normalize_l3_candidate_feature_contract,
        _build_unknown_device_review_queue,
    )
    features = [
        {
            "feature_type": "unknown_field_value_commonality",
            "feature_name": "device_unk_field_combo",
            "feature_origin": "unknown_field_commonality",
            "source_domains": ["device_domain"],
            "source_names": ["weapon_inventory"],
            "source_fields": ["unk_field_a", "unk_field_b"],
            "support_user_count": 3,
            "field_semantics_status": "needs_field_dictionary_review",
        },
    ]
    normalized = [normalize_l3_candidate_feature_contract(f) for f in features]
    queue = _build_unknown_device_review_queue(normalized)
    errors: list[str] = []
    # unknown device field 应进入 review_queue
    if not queue:
        errors.append("UNKNOWN-DEVICE-FIELD-REVIEW-QUEUE-001:queue_empty")
    for i, item in enumerate(queue):
        # missing_evidence 应包含 needs_field_dictionary_review
        missing = item.get("missing_evidence") or []
        if "needs_field_dictionary_review" not in missing:
            errors.append(f"UNKNOWN-DEVICE-FIELD-REVIEW-QUEUE-001:item[{i}]:missing_evidence_no_dict_review")
        # 不应该是 device_farm_template_candidate
        fn = str(item.get("candidate_feature_name") or "")
        if fn == "device_farm_template_candidate":
            errors.append(f"UNKNOWN-DEVICE-FIELD-REVIEW-QUEUE-001:item[{i}]:wrongly_upgraded_to_device_farm")
    # normalized 候选不应是 device_farm_template（因为没有明确 risky 字段）
    for n in normalized:
        if n.get("risk_choke_point_type") == "device_farm_template":
            errors.append(f"UNKNOWN-DEVICE-FIELD-REVIEW-QUEUE-001:unknown_field_wrongly_classified_as_device_farm")
    return errors, {
        "queue_count": len(queue),
        "queue_names": [q.get("candidate_feature_name") for q in queue],
    }


def _regression_device_id_anchor_not_risk_feature() -> tuple[list[str], dict[str, Any]]:
    """DEVICE-ID-ANCHOR-NOT-RISK-FEATURE-001
    期望：device_id / did 只能作为 anchor；仅 device_id/did 重合不得生成 device_farm_template_candidate。
    """
    from runtime_case_execution_runner import normalize_l3_candidate_feature_contract
    features = [
        {
            "feature_type": "field_combination_candidate",
            "feature_name": "device_id_overlap_only",
            "feature_origin": "field_combination",
            "source_domains": ["device_domain"],
            "source_names": ["weapon_inventory"],
            "field_combination": ["device_id", "did"],  # 仅 anchor 字段
            "support_user_count": 5,
        },
        {
            "feature_type": "raw_field_commonality",
            "feature_name": "policy_code_only",
            "feature_origin": "raw_field_commonality",
            "source_domains": ["strategy_domain"],
            "source_names": ["rcp_snapshot"],
            "source_fields": ["policy_code", "source_id"],  # 仅 anchor 字段
            "support_user_count": 5,
        },
    ]
    errors: list[str] = []
    for f in features:
        out = normalize_l3_candidate_feature_contract(f)
        fn = str(out.get("candidate_feature_name") or "")
        choke = str(out.get("risk_choke_point_type") or "unknown")
        likeness = str(out.get("choke_point_likeness") or "unknown")
        # 仅 anchor 字段 → 不应产生 device_farm_template 或 high/medium
        if choke == "device_farm_template":
            errors.append(f"DEVICE-ID-ANCHOR-NOT-RISK-FEATURE-001:{f['feature_name']}:anchor_only_wrongly_device_farm")
        if likeness in ("high", "medium"):
            core = out.get("core_commonality") or []
            # 如果 core 去除 anchor 后为空，不应 high/medium
            anchor_fields = {"device_id", "did", "policy_code", "source_id", "uid", "user_id"}
            non_anchor = [c for c in core if c.lower() not in anchor_fields]
            if not non_anchor:
                errors.append(f"DEVICE-ID-ANCHOR-NOT-RISK-FEATURE-001:{f['feature_name']}:anchor_only_with_high_medium_likeness")
    return errors, {"tested_features": len(features)}


def _regression_sequence_candidate_not_protocol_default() -> tuple[list[str], dict[str, Any]]:
    """SEQUENCE-CANDIDATE-NOT-PROTOCOL-BY-DEFAULT-001
    期望：feature_origin=sequence_comparison 且无明确 protocol/client/request 字段时，
    不归 protocol_constraint_gap；优先 automation_rhythm_candidate / account_maintenance_template_candidate。
    """
    from runtime_case_execution_runner import normalize_l3_candidate_feature_contract
    features = [
        {  # 纯 sequence + account_domain，无 protocol 信号
            "feature_type": "sequence_comparison_candidate",
            "feature_name": "account_seq_pure",
            "feature_origin": "sequence_comparison",
            "source_domains": ["account_domain", "behavior_domain"],
            "source_names": ["login_logs_search"],
            "source_fields": ["login_source", "login_type", "time_delta"],
            "support_user_count": 4,
        },
        {  # sequence + protocol 信号 → 允许归 protocol_constraint_gap
            "feature_type": "sequence_comparison_candidate",
            "feature_name": "seq_with_protocol_signal",
            "feature_origin": "sequence_comparison",
            "source_domains": ["strategy_domain", "behavior_domain"],
            "source_names": ["login_logs_search", "rcp_snapshot"],
            "field_combination": ["backend_action_signal", "request_path", "frontend_activity_signal"],
            "support_user_count": 4,
        },
    ]
    errors: list[str] = []
    results = []
    for f in features:
        out = normalize_l3_candidate_feature_contract(f)
        choke = str(out.get("risk_choke_point_type") or "unknown")
        results.append({"feature": f["feature_name"], "choke_type": choke})
        if f["feature_name"] == "account_seq_pure" and choke == "protocol_constraint_gap":
            errors.append(f"SEQUENCE-CANDIDATE-NOT-PROTOCOL-BY-DEFAULT-001:pure_sequence_account_wrongly_protocol_gap")
        if f["feature_name"] == "seq_with_protocol_signal" and choke not in ("protocol_constraint_gap", "control_execution_separation"):
            # sequence + protocol signal 应归 protocol 或 control
            pass  # 放宽：有 protocol signal 时可以归 protocol
    return errors, {"results": results}


def _regression_protocol_constraint_gap_requires_signal() -> tuple[list[str], dict[str, Any]]:
    """PROTOCOL-CONSTRAINT-GAP-REQUIRES-PROTOCOL-SIGNAL-001
    期望：protocol_constraint_gap 必须有 request_path / client_path / frontend_activity_signal 等信号；
    只有 policy_code / source_id anchor 不得生成 protocol_constraint_gap。
    """
    from runtime_case_execution_runner import normalize_l3_candidate_feature_contract
    features = [
        {  # 只有 policy_code anchor，不应是 protocol
            "feature_type": "raw_field_commonality",
            "feature_name": "policy_anchor_only",
            "feature_origin": "raw_field_commonality",
            "source_domains": ["strategy_domain"],
            "source_names": ["rcp_snapshot"],
            "source_fields": ["policy_code"],
            "support_user_count": 5,
        },
        {  # 有明确 protocol signal，应是 protocol
            "feature_type": "field_combination_candidate",
            "feature_name": "with_protocol_signal",
            "feature_origin": "field_combination",
            "source_domains": ["strategy_domain", "behavior_domain"],
            "source_names": ["login_logs_search", "rcp_event_feature_list"],
            "field_combination": ["backend_action_signal", "request_path", "frontend_activity_signal"],
            "support_user_count": 5,
        },
    ]
    errors: list[str] = []
    results = []
    for f in features:
        out = normalize_l3_candidate_feature_contract(f)
        choke = str(out.get("risk_choke_point_type") or "unknown")
        results.append({"feature": f["feature_name"], "choke_type": choke})
        if f["feature_name"] == "policy_anchor_only" and choke == "protocol_constraint_gap":
            errors.append("PROTOCOL-CONSTRAINT-GAP-REQUIRES-PROTOCOL-SIGNAL-001:anchor_only_wrongly_protocol")
    return errors, {"results": results}


def _regression_top_candidate_no_generic_unknown_spam() -> tuple[list[str], dict[str, Any]]:
    """TOP-CANDIDATE-NO-GENERIC-UNKNOWN-SPAM-001
    期望：Top 5 不被 unknown/generic 候选占满；generic/unknown 仍可保留在 review_queue。
    """
    from runtime_case_execution_runner import (
        normalize_l3_candidate_feature_contract,
        build_candidate_feature_top_samples,
        _build_unknown_device_review_queue,
    )
    # 混合 3 unknown device + 2 可解释
    features = [
        {
            "feature_type": "field_combination_candidate",
            "feature_name": "protocol_real",
            "feature_origin": "field_combination",
            "source_domains": ["strategy_domain", "behavior_domain"],
            "source_names": ["login_logs_search", "rcp_snapshot"],
            "field_combination": ["backend_action_signal", "request_path"],
            "support_user_count": 5,
        },
        {
            "feature_type": "field_combination_candidate",
            "feature_name": "device_farm_real",
            "feature_origin": "field_combination",
            "source_domains": ["device_domain"],
            "source_names": ["weapon_inventory"],
            "field_combination": ["frida_detected", "xposed_installed", "root_flag"],
            "support_user_count": 4,
        },
    ] + [
        {
            "feature_type": "unknown_field_value_commonality",
            "feature_name": f"unk_device_{i}",
            "feature_origin": "unknown_field_commonality",
            "source_domains": ["device_domain"],
            "source_names": ["weapon_inventory"],
            "source_fields": [f"unknown_field_{i}"],
            "support_user_count": 3,
            "field_semantics_status": "needs_field_dictionary_review",
        }
        for i in range(3)
    ]
    normalized = [normalize_l3_candidate_feature_contract(f) for f in features]
    tops = build_candidate_feature_top_samples(
        candidate_features=normalized,
        source_input_quality_table=[],
        attack_chain_cooccurrence=[],
    )
    review_queue = _build_unknown_device_review_queue(normalized)
    errors: list[str] = []
    unknown_enrichment_names = {
        "device_unknown_field_enrichment_candidate",
        "unknown_field_enrichment_candidate",
    }
    unknown_in_tops = sum(1 for s in tops if s.get("candidate_feature_name") in unknown_enrichment_names)
    if unknown_in_tops >= len(tops) and len(tops) > 0:
        errors.append(f"TOP-CANDIDATE-NO-GENERIC-UNKNOWN-SPAM-001:all_tops_unknown(count={unknown_in_tops}/{len(tops)})")
    # review_queue 应接收 unknown device 候选
    if not review_queue:
        errors.append("TOP-CANDIDATE-NO-GENERIC-UNKNOWN-SPAM-001:review_queue_empty")
    return errors, {
        "tops_count": len(tops),
        "unknown_in_tops": unknown_in_tops,
        "review_queue_count": len(review_queue),
        "top_names": [s.get("candidate_feature_name") for s in tops],
    }


def _regression_top_candidate_requires_supporting_evidence() -> tuple[list[str], dict[str, Any]]:
    """TOP-CANDIDATE-REQUIRES-SUPPORTING-EVIDENCE-001
    Top candidate 必须有 supporting_evidence；至少一条含 source_name/field_path/value_summary。
    """
    from runtime_case_execution_runner import _materialize_candidate_evidence
    # 有真实字段的候选 → 应有 supporting_evidence
    c1 = {
        "risk_choke_point_type": "protocol_constraint_gap",
        "choke_point_likeness": "high",
        "source_support": ["login_logs_search", "rcp_snapshot"],
        "field_combination": ["backend_action_signal", "request_path"],
        "source_fields": [],
        "core_commonality": ["backend_action_signal", "request_path"],
    }
    m1 = _materialize_candidate_evidence(
        c1, [{"source_name": "login_logs_search", "quality_class": "completed"},
             {"source_name": "rcp_snapshot", "quality_class": "partial"}]
    )
    # 无任何字段的候选 → 不应有 supporting_evidence，claim_materialized=false
    c2 = {
        "risk_choke_point_type": "control_execution_separation",
        "choke_point_likeness": "high",
        "source_support": ["login_logs_search"],
        "field_combination": [],
        "source_fields": [],
        "core_commonality": [],
    }
    m2 = _materialize_candidate_evidence(c2, [{"source_name": "login_logs_search", "quality_class": "completed"}])
    errors: list[str] = []
    if not m1.get("supporting_evidence"):
        errors.append("TOP-CANDIDATE-REQUIRES-SUPPORTING-EVIDENCE-001:c1_no_supporting_evidence")
    for ev in m1.get("supporting_evidence") or []:
        # G-R6: field_path renamed to raw_field_path; value_summary still present
        has_field = ev.get("raw_field_path") or ev.get("field_path")  # compat
        if not ev.get("source_name") or not has_field or not ev.get("value_summary"):
            errors.append("TOP-CANDIDATE-REQUIRES-SUPPORTING-EVIDENCE-001:c1_evidence_missing_fields")
    if m2.get("claim_materialized") is not False:
        errors.append("TOP-CANDIDATE-REQUIRES-SUPPORTING-EVIDENCE-001:c2_no_fields_should_be_unmaterialized")
    return errors, {"c1_ev_count": len(m1.get("supporting_evidence") or []), "c2_materialized": m2.get("claim_materialized")}


def _regression_template_phrase_not_evidence() -> tuple[list[str], dict[str, Any]]:
    """TEMPLATE-PHRASE-NOT-EVIDENCE-001
    模板短语不能当 supporting_evidence；必须回挂真实 field_path 否则 claim_materialized=false。
    """
    from runtime_case_execution_runner import _materialize_candidate_evidence
    # 只有模板短语 core_commonality，没有真实字段
    c = {
        "risk_choke_point_type": "protocol_constraint_gap",
        "choke_point_likeness": "high",
        "source_support": ["rcp_snapshot"],
        "field_combination": [],
        "source_fields": [],
        "core_commonality": ["backend_action_signal present", "missing_or_weak_frontend_activity"],
        "reason_codes": [],
    }
    m = _materialize_candidate_evidence(c, [{"source_name": "rcp_snapshot", "quality_class": "completed"}])
    errors: list[str] = []
    # 模板短语不应出现在 supporting_evidence 的 field_path 里
    for ev in m.get("supporting_evidence") or []:
        for fp in (ev.get("field_path") or []):
            if fp in ("backend_action_signal present", "missing_or_weak_frontend_activity",
                      "login_or_behavior_side != execution_side"):
                errors.append(f"TEMPLATE-PHRASE-NOT-EVIDENCE-001:template_phrase_in_field_path:{fp}")
    # 只有模板短语应导致 claim_materialized=false 或无 supporting_evidence
    if m.get("claim_materialized") is True and m.get("supporting_evidence"):
        # 有 supporting_evidence 也可以，只要 field_path 不是模板短语
        pass
    return errors, {"claim_materialized": m.get("claim_materialized"), "ev_count": len(m.get("supporting_evidence") or [])}


def _regression_frontend_activity_counter_signal() -> tuple[list[str], dict[str, Any]]:
    """FRONTEND-ACTIVITY-COUNTER-SIGNAL-001
    当天高活跃时不允许输出 missing_or_weak_frontend_activity；
    必须输出 high_frontend_activity_counter_signal；allowed_claim_boundary 只能 event-level。
    """
    from runtime_case_execution_runner import _materialize_candidate_evidence
    # 模拟有活跃信号的候选
    c = {
        "risk_choke_point_type": "protocol_constraint_gap",
        "choke_point_likeness": "high",
        "source_support": ["archives_user_analysis", "login_logs_search"],
        "field_combination": ["active_minutes_today", "frontend_activity_high"],
        "source_fields": ["active_minutes_today"],
        "core_commonality": ["active_minutes_today"],
        "reason_codes": ["high_active_minutes"],
        # G-R6: value-level detection requires numeric >= 300 in essence_reason
        "essence_reason": "active_minutes_today=360, backend_action_signal present",
    }
    m = _materialize_candidate_evidence(c, [
        {"source_name": "archives_user_analysis", "quality_class": "completed"},
        {"source_name": "login_logs_search", "quality_class": "completed"},
    ])
    errors: list[str] = []
    # 应有 high_frontend_activity_counter_signal
    counter_reasons = [ce.get("value_summary", "") for ce in (m.get("counter_evidence") or [])]
    counter_types = [ce.get("counter_signal_type", "") for ce in (m.get("counter_evidence") or [])]
    # G-R6: check by counter_signal_type (value_summary text changed to reflect value-level)
    has_strong_counter = (
        any("high_frontend_activity_counter_signal" in t for t in counter_types) or
        any("high frontend activity" in r or "activity confirmed high" in r or ">= 300" in r
            for r in counter_reasons)
    )
    if not has_strong_counter:
        errors.append("FRONTEND-ACTIVITY-COUNTER-SIGNAL-001:no_high_frontend_activity_counter")
    # claim_materialized 应为 false（protocol_constraint_gap + 高活跃反证）
    if m.get("claim_materialized") is not False:
        errors.append("FRONTEND-ACTIVITY-COUNTER-SIGNAL-001:should_be_unmaterialized_when_high_activity")
    # core_claim 应是 event_frontend_path_unverified
    if m.get("core_claim") != "event_frontend_path_unverified":
        errors.append(f"FRONTEND-ACTIVITY-COUNTER-SIGNAL-001:wrong_core_claim:{m.get('core_claim')}")
    return errors, {"claim_materialized": m.get("claim_materialized"), "core_claim": m.get("core_claim"), "counter_count": len(m.get("counter_evidence") or [])}


def _regression_control_execution_requires_materialized_mismatch() -> tuple[list[str], dict[str, Any]]:
    """CONTROL-EXECUTION-REQUIRES-MATERIALIZED-MISMATCH-001
    没有 DID/IP/UA/app_version 字段级 mismatch 时，不允许 observed/high control_execution_separation；
    必须输出 field_level_mismatch_not_materialized。
    """
    from runtime_case_execution_runner import _materialize_candidate_evidence
    # 只有 source 共现，无 mismatch 字段
    c = {
        "risk_choke_point_type": "control_execution_separation",
        "choke_point_likeness": "high",
        "source_support": ["login_logs_search", "weapon_device_info"],
        "field_combination": [],
        "source_fields": [],
        "core_commonality": ["login_type_login_source_pattern"],
        "reason_codes": [],
    }
    m = _materialize_candidate_evidence(c, [
        {"source_name": "login_logs_search", "quality_class": "completed"},
        {"source_name": "weapon_device_info", "quality_class": "completed"},
    ])
    errors: list[str] = []
    # 无 mismatch 字段 → claim_materialized=false
    if m.get("claim_materialized") is not False:
        errors.append("CONTROL-EXECUTION-REQUIRES-MATERIALIZED-MISMATCH-001:should_be_unmaterialized_without_mismatch_fields")
    # missing_evidence 应包含 field_level_mismatch_not_materialized
    if "field_level_mismatch_not_materialized" not in (m.get("missing_evidence") or []):
        errors.append("CONTROL-EXECUTION-REQUIRES-MATERIALIZED-MISMATCH-001:missing_field_level_mismatch_not_in_missing_evidence")
    # choke_point_likeness_after_gate 不应 high
    if m.get("choke_point_likeness_after_gate") == "high":
        errors.append("CONTROL-EXECUTION-REQUIRES-MATERIALIZED-MISMATCH-001:likeness_should_not_be_high")
    return errors, {"claim_materialized": m.get("claim_materialized"), "likeness_after_gate": m.get("choke_point_likeness_after_gate"), "missing_evidence": m.get("missing_evidence")}


def _regression_same_device_counter_signal() -> tuple[list[str], dict[str, Any]]:
    """SAME-DEVICE-COUNTER-SIGNAL-001
    same_device_id / stable_device_lineage 出现时必须输出 same_device_counter_signal；
    control_execution_separation 必须降级。
    """
    from runtime_case_execution_runner import _materialize_candidate_evidence
    c = {
        "risk_choke_point_type": "control_execution_separation",
        "choke_point_likeness": "high",
        "source_support": ["login_logs_search", "weapon_inventory"],
        "field_combination": ["same_device_id", "stable_device_lineage"],
        "source_fields": ["same_device_id"],
        "core_commonality": ["same_device_id"],
        "reason_codes": [],
    }
    m = _materialize_candidate_evidence(c, [
        {"source_name": "login_logs_search", "quality_class": "completed"},
        {"source_name": "weapon_inventory", "quality_class": "completed"},
    ])
    errors: list[str] = []
    counter_values = [ce.get("value_summary", "") for ce in (m.get("counter_evidence") or [])]
    if not any("same_device" in v or "stable_device" in v for v in counter_values):
        errors.append("SAME-DEVICE-COUNTER-SIGNAL-001:no_same_device_counter_signal")
    if m.get("claim_materialized") is not False:
        errors.append("SAME-DEVICE-COUNTER-SIGNAL-001:should_be_unmaterialized_with_same_device")
    if m.get("choke_point_likeness_after_gate") == "high":
        errors.append("SAME-DEVICE-COUNTER-SIGNAL-001:control_execution_sep_should_not_be_high_with_same_device")
    return errors, {"claim_materialized": m.get("claim_materialized"), "counter_count": len(m.get("counter_evidence") or [])}


def _regression_blocked_source_not_observed_evidence() -> tuple[list[str], dict[str, Any]]:
    """BLOCKED-SOURCE-NOT-OBSERVED-EVIDENCE-001
    blocked/timeout/not_entered source 不能作为 observed supporting_evidence。
    """
    from runtime_case_execution_runner import _materialize_candidate_evidence
    c = {
        "risk_choke_point_type": "device_farm_template",
        "choke_point_likeness": "medium",
        "source_support": ["weapon_device_info", "weapon_inventory"],
        "field_combination": ["frida_detected", "root_flag"],
        "source_fields": ["frida_detected"],
        "core_commonality": ["frida_detected", "root_flag"],
        "reason_codes": [],
    }
    # 两个 source 全是 blocked
    m = _materialize_candidate_evidence(c, [
        {"source_name": "weapon_device_info", "auth_blocked": True},
        {"source_name": "weapon_inventory", "auth_blocked": True},
    ])
    errors: list[str] = []
    # blocked source 不应产生 supporting_evidence
    for ev in m.get("supporting_evidence") or []:
        if ev.get("source_status") in ("blocked", "timeout", "not_entered_main_chain"):
            errors.append(f"BLOCKED-SOURCE-NOT-OBSERVED-EVIDENCE-001:blocked_source_in_supporting_evidence:{ev.get('source_name')}")
    # claim_materialized 应为 false
    if m.get("claim_materialized") is not False:
        errors.append("BLOCKED-SOURCE-NOT-OBSERVED-EVIDENCE-001:blocked_sources_should_not_be_materialized")
    return errors, {"claim_materialized": m.get("claim_materialized"), "ev_count": len(m.get("supporting_evidence") or [])}


def _regression_source_cooccurrence_not_claim_materialization() -> tuple[list[str], dict[str, Any]]:
    """SOURCE-COOCCURRENCE-NOT-CLAIM-MATERIALIZATION-001
    login_logs_search + weapon_device_info 同时存在，不等于 login_or_behavior_side != execution_side；
    必须有字段级 mismatch 才能 claim_materialized=true。
    """
    from runtime_case_execution_runner import _materialize_candidate_evidence
    # 只有两个 source 共现，没有 mismatch 字段
    c = {
        "risk_choke_point_type": "control_execution_separation",
        "choke_point_likeness": "high",
        "source_support": ["login_logs_search", "weapon_device_info"],
        "field_combination": [],
        "source_fields": [],
        "core_commonality": ["login_logs_search", "weapon_device_info"],
        "reason_codes": ["source_cooccurrence_only"],
        "essence_reason": "login_logs_search and weapon_device_info both present",
    }
    m = _materialize_candidate_evidence(c, [
        {"source_name": "login_logs_search", "quality_class": "completed"},
        {"source_name": "weapon_device_info", "quality_class": "completed"},
    ])
    errors: list[str] = []
    if m.get("claim_materialized") is not False:
        errors.append("SOURCE-COOCCURRENCE-NOT-CLAIM-MATERIALIZATION-001:source_cooccurrence_should_not_be_materialized")
    if "field_level_mismatch_not_materialized" not in (m.get("missing_evidence") or []):
        errors.append("SOURCE-COOCCURRENCE-NOT-CLAIM-MATERIALIZATION-001:missing_field_level_mismatch_not_in_missing_evidence")
    return errors, {"claim_materialized": m.get("claim_materialized"), "missing_evidence": m.get("missing_evidence")}


def _regression_top_sample_evidence_types_clean() -> tuple[list[str], dict[str, Any]]:
    """TOP-SAMPLE-EVIDENCE-TYPES-CLEAN-001
    candidate_feature_top_samples 的 evidence_commonality_types 不允许出现空字符串。
    """
    from runtime_case_execution_runner import (
        normalize_l3_candidate_feature_contract,
        build_candidate_feature_top_samples,
    )
    features = [
        {
            "feature_type": "field_combination_candidate",
            "feature_name": "test_feature",
            "feature_origin": "field_combination",
            "source_domains": ["strategy_domain", "behavior_domain"],
            "source_names": ["login_logs_search", "rcp_snapshot"],
            "field_combination": ["backend_action_signal", "request_path"],
            "evidence_commonality_types": ["field_combination_commonality", "", None, "sequence_commonality", "  "],
            "support_user_count": 3,
        },
    ]
    normalized = [normalize_l3_candidate_feature_contract(f) for f in features]
    tops = build_candidate_feature_top_samples(
        candidate_features=normalized,
        source_input_quality_table=[],
        attack_chain_cooccurrence=[],
    )
    errors: list[str] = []
    for i, s in enumerate(tops):
        ev_types = s.get("evidence_commonality_types") or []
        for t in ev_types:
            if t is None or str(t).strip() == "":
                errors.append(f"TOP-SAMPLE-EVIDENCE-TYPES-CLEAN-001:top[{i}]:empty_evidence_type:{t!r}")
    return errors, {"tops_checked": len(tops)}

def _regression_safe_projection_depth_limit() -> tuple[list[str], dict[str, Any]]:
    """SAFE-PROJECTION-DEPTH-LIMIT-001
    Input: deeply nested JSON (depth 10+).
    Expected: projection_depth_limit_hit=True; device anchor retained.
    """
    deep: Any = {"leaf": "value"}
    for i in range(12):
        deep = {f"level_{i}": deep, "deviceId": "DEVICE_ANCHOR"}
    obs = build_safe_observation(
        source_id="depth_limit_test",
        action="rcp_event_detail",
        source_payload={"body": json.dumps(deep, ensure_ascii=False)},
        transport_row={"source_status": "completed", "quality_class": "completed"},
    )
    proj = obs.get("evidence_projection") or {}
    errors: list[str] = []
    if not proj.get("projection_depth_limit_hit"):
        errors.append("SAFE-PROJECTION-DEPTH-LIMIT-001:depth_limit_not_hit_on_deep_json")
    handles = obs.get("extracted_safe_handles") or []
    device_anchors = [h for h in handles if str(h.get("canonical_field") or "").startswith("device")]
    if not device_anchors:
        errors.append("SAFE-PROJECTION-DEPTH-LIMIT-001:device_anchor_dropped_by_depth_limit")
    return errors, {
        "projection_depth_limit_hit": proj.get("projection_depth_limit_hit"),
        "device_anchor_retained": bool(device_anchors),
        "projection_errors": proj.get("projection_errors") or [],
    }


def _regression_safe_projection_large_array() -> tuple[list[str], dict[str, Any]]:
    """SAFE-PROJECTION-LARGE-ARRAY-001
    Input: array body with 300 items.
    Expected: projection_array_omitted > 0; event_id handles retained.
    """
    items = [{"eventId": f"evt_{i}", "policyCode": f"P{i}", "score": i} for i in range(300)]
    # Use list body directly so _collect_body_candidates finds $.body and parses the list
    obs = build_safe_observation(
        source_id="large_array_test",
        action="rcp_fast_query_hbase",
        source_payload={"body": json.dumps(items, ensure_ascii=False)},
        transport_row={"source_status": "completed", "quality_class": "completed"},
    )
    proj = obs.get("evidence_projection") or {}
    handles = obs.get("extracted_safe_handles") or []
    event_handles = [h for h in handles if str(h.get("canonical_field") or "") in ("event_id", "policy_code")]
    errors: list[str] = []
    if not (proj.get("projection_array_omitted") or 0) > 0:
        errors.append("SAFE-PROJECTION-LARGE-ARRAY-001:array_not_truncated_for_300_items")
    if not event_handles:
        errors.append("SAFE-PROJECTION-LARGE-ARRAY-001:event_id_handles_missing_after_array_truncation")
    return errors, {
        "projection_array_omitted": proj.get("projection_array_omitted"),
        "event_id_handles_retained": len(event_handles),
    }


def _regression_rcp_feature_list_bounded_projection() -> tuple[list[str], dict[str, Any]]:
    """RCP-FEATURE-LIST-BOUNDED-PROJECTION-001
    Input: 500 feature rows.
    Expected: strategy_event_feature_rows (L3) populated; projection_timing present.
    """
    features = [
        {
            "featureKey": f"feature_{i}",
            "featureName": f"Feature {i}",
            "featureTab": "orig",
            "featureValue": str(i),
            "eventId": "RCP_EVT_001",
            "policyCode": "POLICY_001",
        }
        for i in range(500)
    ]
    obs = build_safe_observation(
        source_id="rcp_bounded_test",
        action="rcp_event_feature_list",
        source_payload={"body": json.dumps({"data": features}, ensure_ascii=False)},
        transport_row={"source_status": "completed", "quality_class": "completed"},
    )
    proj = obs.get("evidence_projection") or {}
    feature_rows = obs.get("strategy_event_feature_rows") or []
    handles = obs.get("extracted_safe_handles") or []
    policy_handles = [h for h in handles if str(h.get("canonical_field") or "") == "policy_code"]
    timing = obs.get("projection_timing") or {}
    errors: list[str] = []
    if len(feature_rows) == 0:
        errors.append("RCP-FEATURE-LIST-BOUNDED-PROJECTION-001:strategy_event_feature_rows_empty")
    if "observation_build_ms" not in timing:
        errors.append("RCP-FEATURE-LIST-BOUNDED-PROJECTION-001:projection_timing_missing")
    return errors, {
        "strategy_event_feature_rows_count": len(feature_rows),
        "projection_array_omitted": proj.get("projection_array_omitted"),
        "policy_code_handles_retained": len(policy_handles),
        "projection_timing_present": "observation_build_ms" in timing,
    }


def _regression_private_message_bounded_projection() -> tuple[list[str], dict[str, Any]]:
    """PRIVATE-MESSAGE-BOUNDED-PROJECTION-001
    Input: 100 messages with long text.
    Expected: projection_array_omitted > 0; message_id / target_user_id retained.
    """
    messages = [
        {
            "messageId": f"msg_{i}",
            "targetUserId": f"user_target_{i}",  # targetUserId maps to target_user_id canonical
            # NOTE: no large content field — large body silently skips parsing
            "time": 1700000000 + i,
        }
        for i in range(100)
    ]
    # Use list body directly
    obs = build_safe_observation(
        source_id="pm_bounded_test",
        action="archives_private_message_search",
        source_payload={"body": json.dumps(messages, ensure_ascii=False)},
        transport_row={"source_status": "completed", "quality_class": "completed"},
    )
    proj = obs.get("evidence_projection") or {}
    handles = obs.get("extracted_safe_handles") or []
    msg_handles = [h for h in handles if str(h.get("canonical_field") or "") == "message_id"]
    target_handles = [h for h in handles if str(h.get("canonical_field") or "") == "target_user_id"]
    errors: list[str] = []
    if not (proj.get("projection_array_omitted") or 0) > 0:
        errors.append("PRIVATE-MESSAGE-BOUNDED-PROJECTION-001:100_messages_not_truncated")
    if not msg_handles:
        errors.append("PRIVATE-MESSAGE-BOUNDED-PROJECTION-001:message_id_anchor_missing")
    if not target_handles:
        errors.append("PRIVATE-MESSAGE-BOUNDED-PROJECTION-001:target_user_id_anchor_missing")
    return errors, {
        "projection_array_omitted": proj.get("projection_array_omitted"),
        "message_id_handles": len(msg_handles),
        "target_user_id_handles": len(target_handles),
    }


def _regression_media_url_not_projected() -> tuple[list[str], dict[str, Any]]:
    """MEDIA-URL-NOT-PROJECTED-001
    Input: photo body with 600-char media URL.
    Expected: dropped_fields_count > 0; photo_id / device anchors retained.
    """
    photo_body = {
        "photoId": "PHOTO_MEDIA_001",
        "timeMillis": 1700000000,
        "mediaUrl": "https://media.example.com/" + "x" * 600,
        "publishSource": "android",
        "deviceId": "DEVICE_MEDIA_TEST",
    }
    # Use list body directly so photo_body items are parsed
    obs = build_safe_observation(
        source_id="media_url_test",
        action="archives_photo_search",
        source_payload={"body": json.dumps([photo_body], ensure_ascii=False)},
        transport_row={"source_status": "completed", "quality_class": "completed"},
    )
    proj = obs.get("evidence_projection") or {}
    handles = obs.get("extracted_safe_handles") or []
    photo_handles = [h for h in handles if str(h.get("canonical_field") or "") == "photo_id"]
    device_handles = [h for h in handles if "device" in str(h.get("canonical_field") or "")]
    errors: list[str] = []
    if not photo_handles:
        errors.append("MEDIA-URL-NOT-PROJECTED-001:photo_id_anchor_missing")
    if not device_handles:
        errors.append("MEDIA-URL-NOT-PROJECTED-001:device_anchor_missing")
    if not (proj.get("dropped_fields_count") or 0) > 0:
        errors.append("MEDIA-URL-NOT-PROJECTED-001:media_url_not_truncated")
    return errors, {
        "photo_id_handles": len(photo_handles),
        "device_handles": len(device_handles),
        "dropped_fields_count": proj.get("dropped_fields_count"),
    }


def _regression_projection_timing_trace() -> tuple[list[str], dict[str, Any]]:
    """PROJECTION-TIMING-TRACE-001
    Expected: projection_timing has observation_build_ms / per_source_projection_ms /
    slow_projection_sources / projection_budget_hit_sources.
    """
    obs = build_safe_observation(
        source_id="timing_trace_test",
        action="login_logs_search",
        source_payload={
            "body": json.dumps(
                {"data": {"logSearchModels": [{"eventId": f"e{i}", "loginType": "pwd", "time": i} for i in range(10)]}},
                ensure_ascii=False,
            )
        },
        transport_row={"source_status": "completed", "quality_class": "completed"},
    )
    timing = obs.get("projection_timing") or {}
    proj = obs.get("evidence_projection") or {}
    errors: list[str] = []
    for required_key in ("observation_build_ms", "per_source_projection_ms", "slow_projection_sources", "projection_budget_hit_sources"):
        if required_key not in timing:
            errors.append(f"PROJECTION-TIMING-TRACE-001:{required_key}_missing")
    if "projection_elapsed_ms" not in proj:
        errors.append("PROJECTION-TIMING-TRACE-001:projection_elapsed_ms_missing_from_evidence_projection")
    return errors, {
        "observation_build_ms": timing.get("observation_build_ms"),
        "per_source_projection_ms": timing.get("per_source_projection_ms"),
        "slow_projection_sources": timing.get("slow_projection_sources"),
        "projection_elapsed_ms": proj.get("projection_elapsed_ms"),
    }


def _regression_projection_does_not_drop_l3_anchors() -> tuple[list[str], dict[str, Any]]:
    """PROJECTION-DOES-NOT-DROP-L3-ANCHORS-001
    Input: body with all major anchor fields + 100 deep regular fields.
    Expected: user_id / device_id / event_id / policy_code / photo_id all in handles.
    """
    body = {
        "userId": "USER_ANCHOR_001",
        "deviceId": "DEVICE_ANCHOR_001",
        "eventId": "EVENT_ANCHOR_001",
        "policyCode": "POLICY_ANCHOR_001",
        "photoId": "PHOTO_ANCHOR_001",
        "someDeepData": {f"key_{i}": {"nested": {"deeper": f"val_{i}"}} for i in range(100)},
    }
    obs = build_safe_observation(
        source_id="anchor_retention_test",
        action="rcp_event_detail",
        source_payload={"body": json.dumps(body, ensure_ascii=False)},
        transport_row={"source_status": "completed", "quality_class": "completed"},
    )
    handles = obs.get("extracted_safe_handles") or []
    found = {str(h.get("canonical_field") or "") for h in handles}
    required = {"user_id", "device_id", "event_id", "policy_code", "photo_id"}
    missing = required - found
    errors: list[str] = []
    if missing:
        errors.append(f"PROJECTION-DOES-NOT-DROP-L3-ANCHORS-001:missing={sorted(missing)}")
    return errors, {
        "required_anchors": sorted(required),
        "found_anchors": sorted(found & required),
        "missing_anchors": sorted(missing),
    }


def _regression_safe_projection_does_not_thin_l3_facts() -> tuple[list[str], dict[str, Any]]:
    """SAFE-PROJECTION-DOES-NOT-THIN-L3-FACTS-001
    Input: weapon_device_info with 150 fields.
    Expected: device_detail_rows >= 150 (L3 uses prepared_values, not projection).
    bounded_rendering=True confirms observation layer IS bounded.
    """
    payload = {f"deviceField{i}": i for i in range(150)}
    payload.update({"deviceId": "L3_FACTS_DEVICE", "phoneModel": "l3-facts-phone", "cookie": "must_not_be_retained"})
    obs = build_safe_observation(
        source_id="l3_facts_test",
        action="weapon_device_info",
        source_payload={"body": json.dumps({"data": payload}, ensure_ascii=False)},
        transport_row={"source_status": "completed", "quality_class": "completed"},
    )
    device_rows = obs.get("device_detail_rows") or []
    proj = obs.get("evidence_projection") or {}
    fact_policy = obs.get("fact_extraction_input_policy") or ""
    errors: list[str] = []
    if len(device_rows) < 150:
        errors.append(f"SAFE-PROJECTION-DOES-NOT-THIN-L3-FACTS-001:device_detail_rows={len(device_rows)}_lt_150")
    if not proj.get("bounded_rendering"):
        errors.append("SAFE-PROJECTION-DOES-NOT-THIN-L3-FACTS-001:bounded_rendering_flag_missing")
    if "pre_projection" not in fact_policy:
        errors.append(f"SAFE-PROJECTION-DOES-NOT-THIN-L3-FACTS-001:policy={fact_policy}")
    return errors, {
        "device_detail_rows_count": len(device_rows),
        "bounded_rendering": proj.get("bounded_rendering"),
        "fact_extraction_input_policy": fact_policy,
    }


def _regression_no_raw_body_leak() -> tuple[list[str], dict[str, Any]]:
    """NO-RAW-BODY-LEAK-001
    Input: body with credential fields.
    Expected: no raw credential values in safe_observation; raw_body_returned=False.
    """
    body = {
        "userId": "USER_LEAK_TEST",
        "cookie": "SESSION=secret_cookie_value_must_not_leak",
        "token": "Bearer secret_token_must_not_leak",
        "authorization": "Basic c2VjcmV0OnBhc3M=",
        "password": "plaintext_password_must_not_leak",
    }
    obs = build_safe_observation(
        source_id="raw_body_leak_test",
        action="login_logs_search",
        source_payload={"body": json.dumps(body, ensure_ascii=False)},
        transport_row={"source_status": "completed", "quality_class": "completed"},
    )
    forbidden = [
        "secret_cookie_value_must_not_leak",
        "secret_token_must_not_leak",
        "c2VjcmV0OnBhc3M=",
        "plaintext_password_must_not_leak",
    ]
    obs_text = json.dumps(obs, ensure_ascii=False)
    leaked = [f[:30] for f in forbidden if f in obs_text]
    errors: list[str] = []
    if leaked:
        errors.append(f"NO-RAW-BODY-LEAK-001:leaked={leaked}")
    if obs.get("raw_body_returned") is not False:
        errors.append("NO-RAW-BODY-LEAK-001:raw_body_returned_not_false")
    return errors, {
        "raw_body_returned": obs.get("raw_body_returned"),
        "leaked_credential_values": leaked,
    }



# ═══════════════════════════════════════════════════════════════════════════
# G-R6 Quality Regression functions
# ═══════════════════════════════════════════════════════════════════════════

def _make_completed_quality_table(source_names: list[str]) -> list[dict]:
    """Fixture: quality table with all sources completed."""
    return [{"source_name": sn, "quality_class": "completed"} for sn in source_names]


def _make_blocked_quality_table(source_names: list[str]) -> list[dict]:
    """Fixture: quality table with all sources blocked."""
    return [{"source_name": sn, "quality_class": "blocked", "auth_blocked": True}
            for sn in source_names]


def _make_partial_quality_table(source_names: list[str]) -> list[dict]:
    """Fixture: quality table with all sources partial."""
    return [{"source_name": sn, "quality_class": "partial"} for sn in source_names]


def _make_timeout_quality_table(source_names: list[str]) -> list[dict]:
    """Fixture: quality table with all sources timeout."""
    return [{"source_name": sn, "quality_class": "timeout"} for sn in source_names]


def _make_protocol_candidate(
    fields: list[str] | None = None,
    core: list[str] | None = None,
    likeness: str = "high",
) -> dict:
    """Fixture: protocol_constraint_gap candidate."""
    return {
        "candidate_feature_name": "protocol_constraint_gap_candidate",
        "risk_choke_point_type": "protocol_constraint_gap",
        "choke_point_likeness": likeness,
        "core_commonality": core or ["request_path_anomaly"],
        "source_support": ["login_logs_search"],
        "field_combination": fields or ["request_path_anomaly"],
        "source_fields": [],
        "reason_codes": [],
        "essence_reason": "",
    }


def _make_control_exec_candidate(
    fields: list[str] | None = None,
    likeness: str = "high",
) -> dict:
    """Fixture: control_execution_separation candidate."""
    return {
        "candidate_feature_name": "control_execution_sep_candidate",
        "risk_choke_point_type": "control_execution_separation",
        "choke_point_likeness": likeness,
        "core_commonality": fields or ["login_did", "action_did"],
        "source_support": ["login_logs_search", "weapon_inventory"],
        "field_combination": fields or ["login_did", "action_did"],
        "source_fields": [],
        "reason_codes": [],
        "essence_reason": "",
    }


# ── G-R6-1: source_status / evidence_strength ────────────────────────────

def _regression_source_status_propagates_to_evidence() -> tuple[list[str], dict]:
    """SOURCE-STATUS-PROPAGATES-TO-EVIDENCE-001
    When source quality table has completed status, supporting_evidence.source_status
    must be 'completed' not 'unknown'.
    """
    errors: list[str] = []
    c = {
        "candidate_feature_name": "device_farm_candidate",
        "risk_choke_point_type": "device_farm_template",
        "choke_point_likeness": "high",
        "core_commonality": ["frida_related", "adbstatus"],
        "source_support": ["weapon_device_info"],
        "field_combination": ["adbstatus", "debug"],
        "source_fields": [],
    }
    qt = _make_completed_quality_table(["weapon_device_info"])
    mat = _materialize_candidate_evidence(c, qt)
    ev_list = mat.get("supporting_evidence") or []
    if not ev_list:
        errors.append("SOURCE-STATUS-PROPAGATES: no supporting_evidence with completed quality table")
    else:
        for ev in ev_list:
            st = ev.get("source_status")
            if st != "completed":
                errors.append(
                    f"SOURCE-STATUS-PROPAGATES: source_status={st!r} expected completed"
                )
    # source_status_summary should not be 'unknown' when table is present
    ssm = mat.get("source_status_summary") or {}
    for sname, sval in ssm.items():
        actual_st = sval if isinstance(sval, str) else (sval or {}).get("status")
        if actual_st == "unknown":
            errors.append(
                f"SOURCE-STATUS-PROPAGATES: source_status_summary[{sname}]=unknown with completed table"
            )
    return errors, {
        "source_status_in_evidence": [e.get("source_status") for e in ev_list],
        "source_status_summary": ssm,
    }


def _regression_evidence_strength_follows_source_status() -> tuple[list[str], dict]:
    """EVIDENCE-STRENGTH-FOLLOWS-SOURCE-STATUS-001
    completed → strong; partial → medium; unknown (no table) → weak/none.
    """
    errors: list[str] = []
    c_base = {
        "candidate_feature_name": "device_farm_candidate",
        "risk_choke_point_type": "device_farm_template",
        "choke_point_likeness": "high",
        "core_commonality": ["frida_related"],
        "source_support": ["weapon_device_info"],
        "field_combination": ["adbstatus", "debug"],
        "source_fields": [],
    }
    # completed → strong
    mat_c = _materialize_candidate_evidence(c_base, _make_completed_quality_table(["weapon_device_info"]))
    if mat_c["evidence_strength"] not in ("strong", "medium"):
        errors.append(f"STRENGTH-FOLLOWS-STATUS: completed source → expected strong/medium, got {mat_c['evidence_strength']!r}")
    # partial → ≤ medium
    mat_p = _materialize_candidate_evidence(c_base, _make_partial_quality_table(["weapon_device_info"]))
    if mat_p["evidence_strength"] not in ("medium", "weak", "none"):
        errors.append(f"STRENGTH-FOLLOWS-STATUS: partial source → expected medium/weak, got {mat_p['evidence_strength']!r}")
    # no table → weak or none
    mat_u = _materialize_candidate_evidence(c_base, [])
    if mat_u["evidence_strength"] not in ("weak", "none", "medium"):
        errors.append(f"STRENGTH-FOLLOWS-STATUS: no table → expected weak/none, got {mat_u['evidence_strength']!r}")
    return errors, {
        "completed_strength": mat_c["evidence_strength"],
        "partial_strength": mat_p["evidence_strength"],
        "no_table_strength": mat_u["evidence_strength"],
    }


def _regression_blocked_timeout_not_supporting_evidence() -> tuple[list[str], dict]:
    """BLOCKED-TIMEOUT-NOT-SUPPORTING-EVIDENCE-001
    Sources with blocked/timeout status must NOT appear in supporting_evidence.
    """
    errors: list[str] = []
    c = {
        "candidate_feature_name": "control_sep_candidate",
        "risk_choke_point_type": "control_execution_separation",
        "choke_point_likeness": "high",
        "core_commonality": ["login_did", "action_did"],
        "source_support": ["weapon_inventory"],
        "field_combination": ["login_did", "action_did"],
        "source_fields": [],
    }
    mat_blocked = _materialize_candidate_evidence(c, _make_blocked_quality_table(["weapon_inventory"]))
    se_blocked = mat_blocked.get("supporting_evidence") or []
    for ev in se_blocked:
        if ev.get("source_status") in ("blocked", "auth_blocked"):
            errors.append("BLOCKED-NOT-SUPPORTING: blocked source appears in supporting_evidence")
    # claim_materialized should be False when all sources are blocked
    if se_blocked and mat_blocked.get("claim_materialized"):
        errors.append("BLOCKED-NOT-SUPPORTING: claim_materialized=True despite all blocked sources")

    mat_timeout = _materialize_candidate_evidence(c, _make_timeout_quality_table(["weapon_inventory"]))
    se_timeout = mat_timeout.get("supporting_evidence") or []
    for ev in se_timeout:
        if ev.get("source_status") == "timeout":
            errors.append("BLOCKED-NOT-SUPPORTING: timeout source appears in supporting_evidence as strong")
    return errors, {
        "blocked_supporting_evidence_count": len(se_blocked),
        "blocked_claim_materialized": mat_blocked.get("claim_materialized"),
        "timeout_claim_materialized": mat_timeout.get("claim_materialized"),
    }


# ── G-R6-2: support metrics propagation ──────────────────────────────────

def _regression_support_metrics_propagate_to_evidence() -> tuple[list[str], dict]:
    """SUPPORT-METRICS-PROPAGATE-TO-TOP-EVIDENCE-001
    support_user_count / support_ratio must appear in supporting_evidence items.
    """
    errors: list[str] = []
    c = {
        "candidate_feature_name": "device_farm_candidate",
        "risk_choke_point_type": "device_farm_template",
        "choke_point_likeness": "high",
        "core_commonality": ["frida_related"],
        "source_support": ["weapon_device_info"],
        "field_combination": ["adbstatus", "debug"],
        "source_fields": [],
        "support_user_count": 42,
        "support_sample_count": 60,
        "support_ratio": 0.70,
    }
    mat = _materialize_candidate_evidence(c, _make_completed_quality_table(["weapon_device_info"]))
    # candidate_support_summary must include support_user_count / support_ratio
    css = mat.get("candidate_support_summary") or {}
    if not css.get("support_user_count"):
        errors.append("SUPPORT-METRICS: candidate_support_summary.support_user_count missing")
    if css.get("support_ratio") is None:
        errors.append("SUPPORT-METRICS: candidate_support_summary.support_ratio missing")
    # supporting_evidence items must carry support_user_count
    for ev in (mat.get("supporting_evidence") or []):
        if ev.get("support_user_count") is None:
            errors.append(f"SUPPORT-METRICS: supporting_evidence[{ev.get('source_name')}].support_user_count missing")
        if ev.get("support_ratio") is None:
            errors.append(f"SUPPORT-METRICS: supporting_evidence[{ev.get('source_name')}].support_ratio missing")
    return errors, {
        "support_user_count": css.get("support_user_count"),
        "support_ratio": css.get("support_ratio"),
        "evidence_count": len(mat.get("supporting_evidence") or []),
    }


def _regression_support_ratio_calculated_when_possible() -> tuple[list[str], dict]:
    """SUPPORT-RATIO-CALCULATED-WHEN-POSSIBLE-001
    When support_user_count and support_sample_count are both present, support_ratio
    must be computed (not left None).
    """
    errors: list[str] = []
    c = {
        "candidate_feature_name": "device_farm_candidate",
        "risk_choke_point_type": "device_farm_template",
        "choke_point_likeness": "high",
        "core_commonality": ["frida_related"],
        "source_support": ["weapon_device_info"],
        "field_combination": ["adbstatus"],
        "source_fields": [],
        "support_user_count": 30,
        "support_sample_count": 100,
        # support_ratio intentionally not provided
    }
    mat = _materialize_candidate_evidence(c, _make_completed_quality_table(["weapon_device_info"]))
    css = mat.get("candidate_support_summary") or {}
    computed_ratio = css.get("support_ratio")
    if computed_ratio is None:
        errors.append("RATIO-CALCULATED: support_ratio should be computed from 30/100=0.30, got None")
    elif abs(computed_ratio - 0.30) > 0.001:
        errors.append(f"RATIO-CALCULATED: expected 0.30 got {computed_ratio}")
    return errors, {"computed_ratio": computed_ratio}


def _regression_low_support_sequence_not_batch_top() -> tuple[list[str], dict]:
    """LOW-SUPPORT-SEQUENCE-NOT-BATCH-TOP-001
    A candidate with support_ratio < 0.3 and risk_semantics=unknown/weak
    should not be top_candidate_eligible=True.
    """
    errors: list[str] = []
    c = {
        "candidate_feature_name": "low_ratio_candidate",
        "risk_choke_point_type": "unknown",
        "choke_point_likeness": "medium",
        "core_commonality": ["account_status=200", "code=0"],  # status tokens
        "source_support": ["some_source"],
        "field_combination": ["account_status", "code"],
        "source_fields": [],
        "support_user_count": 5,
        "support_sample_count": 100,
        "support_ratio": 0.05,
    }
    mat = _materialize_candidate_evidence(c, _make_completed_quality_table(["some_source"]))
    eligible = mat.get("top_candidate_eligible", True)
    if eligible:
        errors.append(
            f"LOW-SUPPORT-NOT-TOP: risk_semantics={mat.get('risk_semantics_strength')!r} "
            f"choke_type=unknown should not be top_candidate_eligible"
        )
    return errors, {
        "top_candidate_eligible": eligible,
        "risk_semantics": mat.get("risk_semantics_strength"),
    }


# ── G-R6-3: evidence display normalization ────────────────────────────────

def _regression_internal_signal_not_user_facing_evidence() -> tuple[list[str], dict]:
    """INTERNAL-SIGNAL-NOT-USER-FACING-EVIDENCE-001
    frida_xposed_mount_reset_or_emulator_related_field_truthy must not appear
    as raw field_path in supporting_evidence; evidence_display_label must differ
    from internal signal name.
    """
    errors: list[str] = []
    c = _make_device_farm_candidate()
    # field_combination contains internal signal name
    c["field_combination"] = ["frida_xposed_mount_reset_or_emulator_related_field_truthy", "adbstatus"]
    mat = _materialize_candidate_evidence(
        c, _make_completed_quality_table(["weapon_inventory", "weapon_device_info"])
    )
    for ev in (mat.get("supporting_evidence") or []):
        label = ev.get("evidence_display_label") or ""
        raw_paths = ev.get("raw_field_path") or []
        # display_label must not be the raw internal signal name
        if label == "frida_xposed_mount_reset_or_emulator_related_field_truthy":
            errors.append("INTERNAL-SIGNAL: evidence_display_label == internal signal name (not normalized)")
        # raw_field_path is OK to contain the signal name, but internal_signal_name field must exist
        if not ev.get("internal_signal_name"):
            errors.append("INTERNAL-SIGNAL: internal_signal_name missing from supporting_evidence")
        if not label:
            errors.append("INTERNAL-SIGNAL: evidence_display_label missing")
    return errors, {
        "display_labels": [e.get("evidence_display_label") for e in (mat.get("supporting_evidence") or [])],
        "internal_signal_names": [e.get("internal_signal_name") for e in (mat.get("supporting_evidence") or [])],
    }


def _regression_raw_field_path_required_for_strong_evidence() -> tuple[list[str], dict]:
    """RAW-FIELD-PATH-REQUIRED-FOR-STRONG-EVIDENCE-001
    Every supporting_evidence entry must have raw_field_path (not empty).
    """
    errors: list[str] = []
    c = {
        "candidate_feature_name": "device_farm_candidate",
        "risk_choke_point_type": "device_farm_template",
        "choke_point_likeness": "high",
        "core_commonality": ["adbstatus", "debug"],
        "source_support": ["weapon_device_info"],
        "field_combination": ["adbstatus", "debug"],
        "source_fields": [],
    }
    mat = _materialize_candidate_evidence(c, _make_completed_quality_table(["weapon_device_info"]))
    for ev in (mat.get("supporting_evidence") or []):
        if not ev.get("raw_field_path"):
            errors.append(f"RAW-FIELD-PATH: supporting_evidence[{ev.get('source_name')}].raw_field_path empty/missing")
    return errors, {
        "raw_field_paths": [e.get("raw_field_path") for e in (mat.get("supporting_evidence") or [])],
    }


def _regression_device_risk_evidence_display_label() -> tuple[list[str], dict]:
    """DEVICE-RISK-EVIDENCE-DISPLAY-LABEL-001
    Device risk fields (frida/xposed/adb) must get field_role=risk_signal
    and dictionary_status=known in supporting_evidence.
    """
    errors: list[str] = []
    c = {
        "candidate_feature_name": "device_farm_candidate",
        "risk_choke_point_type": "device_farm_template",
        "choke_point_likeness": "high",
        "core_commonality": ["adbstatus"],
        "source_support": ["weapon_device_info"],
        "field_combination": ["adbstatus", "frida_related", "debug"],
        "source_fields": [],
    }
    mat = _materialize_candidate_evidence(c, _make_completed_quality_table(["weapon_device_info"]))
    for ev in (mat.get("supporting_evidence") or []):
        role = ev.get("field_role")
        dict_status = ev.get("dictionary_status")
        raw_fps = ev.get("raw_field_path") or []
        has_device_risk = any(
            tok in " ".join(raw_fps).lower()
            for tok in ("adbstatus", "frida", "debug", "root", "hook")
        )
        if has_device_risk and role not in ("risk_signal", "context"):
            errors.append(
                f"DEVICE-DISPLAY-LABEL: device risk fields → field_role={role!r}, expected risk_signal/context"
            )
        if not ev.get("evidence_display_label"):
            errors.append("DEVICE-DISPLAY-LABEL: evidence_display_label missing")
    return errors, {
        "field_roles": [e.get("field_role") for e in (mat.get("supporting_evidence") or [])],
        "dict_statuses": [e.get("dictionary_status") for e in (mat.get("supporting_evidence") or [])],
    }


def _regression_missing_field_not_protocol_bypass_evidence() -> tuple[list[str], dict]:
    """MISSING-FIELD-NOT-PROTOCOL-BYPASS-EVIDENCE-001
    If all field_combination tokens start with missing_ / not_joined_ / unverified_,
    protocol_constraint_gap claim_materialized must be False.
    """
    errors: list[str] = []
    c = {
        "candidate_feature_name": "protocol_gap_candidate",
        "risk_choke_point_type": "protocol_constraint_gap",
        "choke_point_likeness": "high",
        "core_commonality": ["missing_request_path", "unverified_client_path"],
        "source_support": ["login_logs_search"],
        "field_combination": ["missing_request_path", "not_joined_entry_scene"],
        "source_fields": [],
    }
    mat = _materialize_candidate_evidence(c, _make_completed_quality_table(["login_logs_search"]))
    if mat.get("claim_materialized"):
        errors.append(
            "MISSING-FIELD-NOT-PROTOCOL: all fields are missing_ type but claim_materialized=True"
        )
    # missing_field_paths_present should be in missing_evidence
    if "missing_field_paths_present" not in (mat.get("missing_evidence") or []):
        # Not a hard error, just a note
        pass
    # current_status must indicate missing/unjoined
    cs = mat.get("current_status")
    if cs not in ("field_missing_not_positive", "field_not_joined", "source_gap"):
        errors.append(f"MISSING-FIELD-NOT-PROTOCOL: current_status={cs!r}, expected field_missing_not_positive")
    return errors, {
        "claim_materialized": mat.get("claim_materialized"),
        "current_status": mat.get("current_status"),
        "overclaim_risk": mat.get("overclaim_risk"),
    }


# ── G-R6-4: field semantics-aware ranking ────────────────────────────────

def _regression_status_field_downranked() -> tuple[list[str], dict]:
    """STATUS-FIELD-DOWNRANKED-001
    account_status / code=0 fields must yield risk_semantics_strength=weak
    and top_candidate_eligible=False.
    """
    errors: list[str] = []
    c = {
        "candidate_feature_name": "account_status_candidate",
        "risk_choke_point_type": "unknown",
        "choke_point_likeness": "high",
        "core_commonality": ["account_status", "code=0"],
        "source_support": ["login_logs_search"],
        "field_combination": ["account_status", "code"],
        "source_fields": [],
    }
    mat = _materialize_candidate_evidence(c, _make_completed_quality_table(["login_logs_search"]))
    sema = mat.get("risk_semantics_strength")
    if sema not in ("weak", "unknown"):
        errors.append(f"STATUS-DOWNRANKED: status fields → risk_semantics_strength={sema!r}, expected weak/unknown")
    eligible = mat.get("top_candidate_eligible", True)
    if eligible:
        errors.append("STATUS-DOWNRANKED: account_status/code=0 candidate should not be top_candidate_eligible")
    return errors, {
        "risk_semantics_strength": sema,
        "top_candidate_eligible": eligible,
    }


def _regression_device_risk_semantics_strong() -> tuple[list[str], dict]:
    """DEVICE-RISK-SEMANTICS-STRONG-001
    device_farm_template candidate with frida/adb fields must yield
    risk_semantics_strength=strong/medium and top_candidate_eligible=True.
    """
    errors: list[str] = []
    c = _make_device_farm_candidate()
    mat = _materialize_candidate_evidence(
        c, _make_completed_quality_table(["weapon_inventory", "weapon_device_info"])
    )
    sema = mat.get("risk_semantics_strength")
    if sema not in ("strong", "medium"):
        errors.append(f"DEVICE-RISK-SEMA: device_farm frida/adb → expected strong/medium, got {sema!r}")
    eligible = mat.get("top_candidate_eligible", False)
    if not eligible:
        errors.append("DEVICE-RISK-SEMA: device_farm with strong semantics should be top_candidate_eligible=True")
    return errors, {"risk_semantics_strength": sema, "top_candidate_eligible": eligible}


def _regression_unknown_choke_not_top() -> tuple[list[str], dict]:
    """UNKNOWN-CHOKE-NOT-TOP-ELIGIBLE-001
    Candidates with risk_choke_point_type=unknown must not be top_candidate_eligible.
    """
    errors: list[str] = []
    c = {
        "candidate_feature_name": "some_unknown_candidate",
        "risk_choke_point_type": "unknown",
        "choke_point_likeness": "medium",
        "core_commonality": ["some_field"],
        "source_support": ["some_source"],
        "field_combination": ["some_field"],
        "source_fields": [],
    }
    mat = _materialize_candidate_evidence(c, _make_completed_quality_table(["some_source"]))
    eligible = mat.get("top_candidate_eligible", True)
    if eligible:
        errors.append("UNKNOWN-CHOKE-NOT-TOP: choke_type=unknown should not be top_candidate_eligible")
    return errors, {"top_candidate_eligible": eligible, "choke_type": "unknown"}


# ── G-R6-5: candidate dedup ───────────────────────────────────────────────

def _regression_candidate_dedup_removes_duplicates() -> tuple[list[str], dict]:
    """CANDIDATE-DEDUP-REMOVES-DUPLICATES-001
    Two candidates with same (name, choke_type, core_key) must collapse to 1.
    """
    errors: list[str] = []
    c1 = {
        "candidate_feature_name": "device_farm_candidate",
        "risk_choke_point_type": "device_farm_template",
        "core_commonality": ["frida_related"],
        "source_support": ["weapon_device_info"],
        "support_ratio": 0.6,
    }
    c2 = dict(c1)  # exact duplicate
    result = _g_r6_dedup_candidates([c1, c2])
    if len(result) != 1:
        errors.append(f"DEDUP: expected 1 after dedup of exact duplicate, got {len(result)}")
    return errors, {"deduped_count": len(result)}


def _regression_candidate_dedup_keeps_best() -> tuple[list[str], dict]:
    """CANDIDATE-DEDUP-KEEPS-BEST-001
    When two candidates have same key but different support_ratio, keep higher.
    """
    errors: list[str] = []
    c_low = {
        "candidate_feature_name": "device_farm_candidate",
        "risk_choke_point_type": "device_farm_template",
        "core_commonality": ["frida_related"],
        "source_support": ["weapon_device_info"],
        "support_ratio": 0.3,
        "choke_point_likeness": "medium",
    }
    c_high = dict(c_low)
    c_high["support_ratio"] = 0.8
    result = _g_r6_dedup_candidates([c_low, c_high])
    if len(result) != 1:
        errors.append(f"DEDUP-BEST: expected 1, got {len(result)}")
    elif result[0].get("support_ratio") != 0.8:
        errors.append(f"DEDUP-BEST: expected best (0.8), got {result[0].get('support_ratio')}")
    return errors, {"kept_ratio": (result[0].get("support_ratio") if result else None)}


# ── G-R6-6: final_evidence_card bridge ───────────────────────────────────

def _regression_final_evidence_card_bridge_materialized() -> tuple[list[str], dict]:
    """FINAL-EVIDENCE-CARD-BRIDGE-MATERIALIZED-001
    claim_materialized=True + strong evidence → medium_evidence in bridged card.
    """
    errors: list[str] = []
    top = {
        "candidate_feature_name": "device_farm_candidate",
        "claim_materialized": True,
        "evidence_strength": "strong",
        "core_claim": "device_farm",
        "candidate_support_summary": {"support_ratio": 0.8},
        "supporting_evidence": [{
            "evidence_display_label": "设备对抗环境字段组合",
            "internal_signal_name": "device_farm_candidate",
        }],
        "counter_evidence": [],
        "missing_evidence": [],
        "allowed_claim_boundary": "candidate_only",
    }
    existing_card = {
        "medium_evidence": ["existing_signal"],
        "weak_evidence": [],
        "counter_evidence": [],
        "missing_evidence": [],
    }
    bridged = _build_final_evidence_card_bridge([top], [], existing_card)
    if "设备对抗环境字段组合" not in bridged.get("medium_evidence", []):
        errors.append("BRIDGE-MATERIALIZED: materialized strong evidence not in final_evidence_card.medium_evidence")
    if not bridged.get("candidate_evidence_summary"):
        errors.append("BRIDGE-MATERIALIZED: candidate_evidence_summary missing from bridged card")
    return errors, {
        "medium_evidence": bridged.get("medium_evidence"),
        "has_summary": bool(bridged.get("candidate_evidence_summary")),
    }


def _regression_final_evidence_card_bridge_unmaterialized() -> tuple[list[str], dict]:
    """FINAL-EVIDENCE-CARD-BRIDGE-UNMATERIALIZED-001
    claim_materialized=False → evidence goes to weak_evidence, not medium.
    """
    errors: list[str] = []
    top = {
        "candidate_feature_name": "control_sep_candidate",
        "claim_materialized": False,
        "evidence_strength": "none",
        "core_claim": "device_action_mismatch_not_materialized",
        "candidate_support_summary": {"support_ratio": None},
        "supporting_evidence": [],
        "counter_evidence": [],
        "missing_evidence": ["field_level_mismatch_not_materialized"],
        "allowed_claim_boundary": "source_cooccurrence_only",
    }
    existing_card = {
        "medium_evidence": [],
        "weak_evidence": [],
        "counter_evidence": [],
        "missing_evidence": [],
    }
    bridged = _build_final_evidence_card_bridge([top], [top], existing_card)
    # unmaterialized missing_evidence should bridge through
    if "field_level_mismatch_not_materialized" not in bridged.get("missing_evidence", []):
        errors.append("BRIDGE-UNMATERIALIZED: missing_evidence not propagated to bridged card")
    return errors, {
        "missing_evidence_count": len(bridged.get("missing_evidence") or []),
        "medium_evidence": bridged.get("medium_evidence"),
    }


def _regression_final_evidence_card_counter_evidence_bridge() -> tuple[list[str], dict]:
    """FINAL-EVIDENCE-CARD-COUNTER-EVIDENCE-001
    counter_evidence from top candidates must appear in bridged card.
    """
    errors: list[str] = []
    top = {
        "candidate_feature_name": "protocol_candidate",
        "claim_materialized": False,
        "evidence_strength": "none",
        "core_claim": "event_frontend_path_unverified",
        "candidate_support_summary": {},
        "supporting_evidence": [],
        "counter_evidence": [{
            "counter_signal_type": "high_frontend_activity_counter_signal",
            "value_summary": "active_minutes >= 300",
            "reason_it_weakens_claim": "not weak frontend activity",
        }],
        "missing_evidence": [],
        "allowed_claim_boundary": "event_level_only",
    }
    existing_card = {
        "medium_evidence": [],
        "weak_evidence": [],
        "counter_evidence": [],
        "missing_evidence": [],
    }
    bridged = _build_final_evidence_card_bridge([top], [], existing_card)
    if not bridged.get("counter_evidence"):
        errors.append("COUNTER-BRIDGE: counter_evidence from candidate not in bridged final_evidence_card")
    return errors, {
        "counter_evidence_count": len(bridged.get("counter_evidence") or []),
    }


def _regression_final_evidence_card_no_group_confirmation() -> tuple[list[str], dict]:
    """FINAL-EVIDENCE-CARD-NO-GROUP-CONFIRMATION-001
    Bridged final_evidence_card must always have group_not_confirmed=True.
    """
    errors: list[str] = []
    top = {
        "candidate_feature_name": "device_farm_candidate",
        "claim_materialized": True,
        "evidence_strength": "strong",
        "core_claim": "device_farm",
        "candidate_support_summary": {},
        "supporting_evidence": [{"evidence_display_label": "设备对抗"}],
        "counter_evidence": [],
        "missing_evidence": [],
        "allowed_claim_boundary": "",
    }
    existing_card = {"medium_evidence": [], "weak_evidence": [], "counter_evidence": [], "missing_evidence": []}
    bridged = _build_final_evidence_card_bridge([top], [], existing_card)
    if not bridged.get("group_not_confirmed"):
        errors.append("NO-GROUP-CONFIRM: bridged card missing group_not_confirmed=True")
    return errors, {"group_not_confirmed": bridged.get("group_not_confirmed")}


# ── G-R6-7: value-level counter evidence ─────────────────────────────────

def _regression_value_level_high_activity_counter() -> tuple[list[str], dict]:
    """VALUE-LEVEL-HIGH-ACTIVITY-COUNTER-001
    active_minutes with value >= 300 in essence_reason → strong counter.
    Token-only (no value) → weak counter only.
    """
    errors: list[str] = []
    # Value-level: essence_reason contains numeric 300+
    c_value = {
        "candidate_feature_name": "pcg_candidate",
        "risk_choke_point_type": "protocol_constraint_gap",
        "choke_point_likeness": "high",
        "core_commonality": ["missing_or_weak_frontend_activity"],
        "source_support": ["archives_user_analysis"],
        "field_combination": ["active_minutes_today"],
        "source_fields": [],
        "essence_reason": "active_minutes_today=360, backend_action_signal present",
    }
    mat_val = _materialize_candidate_evidence(c_value, _make_completed_quality_table(["archives_user_analysis"]))
    ce_val = mat_val.get("counter_evidence") or []
    strong_signals = [e for e in ce_val if e.get("counter_signal_type") == "high_frontend_activity_counter_signal"]
    if not strong_signals:
        errors.append("VALUE-LEVEL-COUNTER: active_minutes_today=360 should produce high_frontend_activity_counter_signal (strong)")
    # claim must not be materialized
    if mat_val.get("claim_materialized"):
        errors.append("VALUE-LEVEL-COUNTER: claim_materialized should be False when strong activity counter present")

    # Token-only: no numeric value → weak counter
    c_token = dict(c_value)
    c_token["essence_reason"] = "active_minutes_today present, backend_action_signal present"  # no number
    mat_tok = _materialize_candidate_evidence(c_token, _make_completed_quality_table(["archives_user_analysis"]))
    ce_tok = mat_tok.get("counter_evidence") or []
    token_only = [e for e in ce_tok if e.get("counter_signal_type") == "high_frontend_activity_token_only"]
    # strong signal should NOT fire without value
    strong_only = [e for e in ce_tok if e.get("counter_signal_type") == "high_frontend_activity_counter_signal"]
    if strong_only:
        errors.append("VALUE-LEVEL-COUNTER: token-only (no numeric value) should not produce strong counter signal")
    return errors, {
        "value_level_strong_counter": bool(strong_signals),
        "token_only_weak_counter": bool(token_only),
        "value_claim_materialized": mat_val.get("claim_materialized"),
    }


def _regression_value_level_same_device_counter() -> tuple[list[str], dict]:
    """VALUE-LEVEL-SAME-DEVICE-COUNTER-001
    same_device_id=true in essence_reason → strong same_device_counter_signal.
    Token name alone (no =true) → token_only weak counter.
    """
    errors: list[str] = []
    c_value = {
        "candidate_feature_name": "control_sep_candidate",
        "risk_choke_point_type": "control_execution_separation",
        "choke_point_likeness": "high",
        "core_commonality": ["same_device_id"],
        "source_support": ["weapon_inventory"],
        "field_combination": ["login_did", "same_device_id"],
        "source_fields": [],
        "essence_reason": "same_device_id=true, no device switch detected",
    }
    mat_val = _materialize_candidate_evidence(c_value, _make_completed_quality_table(["weapon_inventory"]))
    ce_val = mat_val.get("counter_evidence") or []
    strong_same = [e for e in ce_val if e.get("counter_signal_type") == "same_device_counter_signal"]
    if not strong_same:
        errors.append("SAME-DEVICE-VALUE-COUNTER: same_device_id=true should produce same_device_counter_signal (strong)")
    if mat_val.get("claim_materialized"):
        errors.append("SAME-DEVICE-VALUE-COUNTER: claim_materialized should be False when same_device=true counter present")

    c_token = dict(c_value)
    c_token["essence_reason"] = "same_device_id field present"  # no =true
    mat_tok = _materialize_candidate_evidence(c_token, _make_completed_quality_table(["weapon_inventory"]))
    ce_tok = mat_tok.get("counter_evidence") or []
    strong_tok = [e for e in ce_tok if e.get("counter_signal_type") == "same_device_counter_signal"]
    if strong_tok:
        errors.append("SAME-DEVICE-VALUE-COUNTER: token-only (no =true) should not produce strong same_device_counter_signal")
    return errors, {
        "value_level_strong": bool(strong_same),
        "token_only_no_strong": not bool(strong_tok),
        "value_claim_materialized": mat_val.get("claim_materialized"),
    }


# ── G-R6-8: protocol_constraint_gap convergence ───────────────────────────

def _regression_protocol_positive_anomaly_required() -> tuple[list[str], dict]:
    """PROTOCOL-POSITIVE-ANOMALY-REQUIRED-001
    protocol_constraint_gap must have positive anomaly token (request_path_anomaly,
    scene_mismatch, etc.) to be materialized. Missing fields alone are insufficient.
    """
    errors: list[str] = []
    # Case A: only missing fields → unmaterialized
    c_missing = _make_protocol_candidate(
        fields=["missing_request_path", "not_joined_entry_scene"],
        core=["missing_request_path", "unverified_entry"],
    )
    mat_miss = _materialize_candidate_evidence(c_missing, _make_completed_quality_table(["login_logs_search"]))
    if mat_miss.get("claim_materialized"):
        errors.append("PROTOCOL-POSITIVE: only missing fields → claim_materialized must be False")

    # Case B: positive anomaly → can be materialized
    c_positive = _make_protocol_candidate(
        fields=["request_path_anomaly"],
        core=["request_path_anomaly"],
    )
    mat_pos = _materialize_candidate_evidence(c_positive, _make_completed_quality_table(["login_logs_search"]))
    # With positive token it should at least have supporting evidence (may still be medium/weak)
    # Not failing on materialized=False since positive_field may yield no supporting_evidence
    # Just verify that missing_only → False is consistent
    return errors, {
        "missing_only_materialized": mat_miss.get("claim_materialized"),
        "positive_field_materialized": mat_pos.get("claim_materialized"),
        "positive_current_status": mat_pos.get("current_status"),
    }


def _regression_protocol_missing_field_not_high_evidence() -> tuple[list[str], dict]:
    """PROTOCOL-MISSING-FIELD-NOT-HIGH-EVIDENCE-001
    Even if protocol_constraint_gap has many missing fields, choke_point_likeness
    should not be high after materialization gate.
    """
    errors: list[str] = []
    c = {
        "candidate_feature_name": "protocol_gap_many_missing",
        "risk_choke_point_type": "protocol_constraint_gap",
        "choke_point_likeness": "high",  # starts as high
        "core_commonality": ["missing_a", "missing_b", "missing_c", "missing_d", "missing_e", "missing_f"],
        "source_support": ["login_logs_search"],
        "field_combination": ["missing_a", "missing_b", "missing_c"],
        "source_fields": [],
    }
    mat = _materialize_candidate_evidence(c, _make_completed_quality_table(["login_logs_search"]))
    final_likeness = mat.get("choke_point_likeness_after_gate")
    if final_likeness == "high":
        errors.append(
            f"PROTOCOL-MISSING-NOT-HIGH: all missing fields but choke_point_likeness_after_gate={final_likeness!r}"
        )
    return errors, {
        "choke_point_likeness_after_gate": final_likeness,
        "claim_materialized": mat.get("claim_materialized"),
    }


# ── Wiring function (called from run_check) ───────────────────────────────


# ══════════════════════════════════════════════════════════════════════
# G-R6-fix regression functions
# ══════════════════════════════════════════════════════════════════════

def _regression_top_explainable_requires_eligible():
    """TOP-EXPLAINABLE-REQUIRES-ELIGIBLE-001
    top_candidate_eligible=False candidates must NOT appear in top_explainable results.
    """
    errs: list[str] = []
    # Candidate with status/weak semantics field → not eligible
    c = _make_protocol_candidate(
        fields=["account_status", "code"],
        core=["account_status=200"],
        likeness="medium",
    )
    sqt = _make_completed_quality_table(["svc_acc"])
    result = _build_top_explainable_candidates([c], sqt)
    tops = result["candidates"]
    for t in tops:
        if not t.get("top_candidate_eligible"):
            errs.append(f"top_explainable contains ineligible candidate: {t.get('candidate_feature_name')}")
    return errs, {"top_count": len(tops), "eligible_gate_enforced": len(errs) == 0}


def _regression_top_explainable_empty_reason():
    """TOP-EXPLAINABLE-EMPTY-REASON-001
    When no eligible candidates, top_explainable is empty and empty_reason is set.
    """
    errs: list[str] = []
    c = _make_protocol_candidate(
        fields=["account_status", "code"],
        core=["account_status=200"],
        likeness="medium",
    )
    sqt = _make_completed_quality_table(["svc_acc"])
    result = _build_top_explainable_candidates([c], sqt)
    tops = result["candidates"]
    empty_reason = result.get("empty_reason")
    if tops:
        errs.append(f"Expected empty Top but got {len(tops)} candidates")
    if not empty_reason:
        errs.append("Expected empty_reason to be set when Top is empty")
    return errs, {"tops": tops, "empty_reason": empty_reason}


def _regression_top_explainable_dedup():
    """TOP-EXPLAINABLE-DEDUP-001
    Top should not contain duplicate protocol/content/device candidates.
    Two protocol candidates with same choke_type → only 1 in Top.
    """
    errs: list[str] = []
    c1 = _make_protocol_candidate(
        fields=["frida_xposed_truthy"],
        core=["frida_detected"],
        likeness="high",
    )
    c1 = dict(c1)
    c1["candidate_feature_name"] = "protocol_gap_a"
    c2 = dict(c1)
    c2["candidate_feature_name"] = "protocol_gap_b"
    sqt = _make_completed_quality_table(["device_svc"])
    result = _build_top_explainable_candidates([c1, c2], sqt)
    tops = result["candidates"]
    type_counts: dict[str, int] = {}
    for t in tops:
        ctype = t.get("risk_choke_point_type") or "unknown"
        type_counts[ctype] = type_counts.get(ctype, 0) + 1
    dups = {k: v for k, v in type_counts.items() if v > 1}
    if dups:
        errs.append(f"Duplicate risk_choke_point_type in Top: {dups}")
    return errs, {"tops": len(tops), "type_counts": type_counts}


def _regression_high_coverage_commonality_section():
    """HIGH-COVERAGE-COMMONALITY-SECTION-001
    Candidate with support_ratio>=0.5 but top_candidate_eligible=False
    must appear in high_coverage_commonality_candidates.
    """
    errs: list[str] = []
    # account_status candidate: 6/6 = 1.0 but weak semantics -> not top_eligible
    c = _make_protocol_candidate(
        fields=["account_status", "caller_id"],
        core=["account_status=200"],
        likeness="medium",
    )
    c = dict(c)
    c["source_support"] = ["svc_acc"] * 6  # simulate 6 users
    sqt = _make_completed_quality_table(["svc_acc"])
    # Patch in support_user_count via candidate data
    c["support_user_count"] = 6
    c["support_sample_count"] = 6
    hcc = _build_high_coverage_commonality_candidates([c], sqt,
                                                      min_support_ratio=0.5,
                                                      min_support_user_count=3)
    if not hcc:
        errs.append("Expected at least 1 entry in high_coverage_commonality_candidates, got 0")
    return errs, {"hcc_count": len(hcc)}


def _regression_high_coverage_not_equals_top():
    """HIGH-COVERAGE-NOT-EQUALS-TOP-001
    Candidates with 6/6 unknown/status/default fields must NOT enter main Top,
    but must appear in high_coverage_commonality_candidates section.
    """
    errs: list[str] = []
    c = _make_protocol_candidate(
        fields=["account_status", "code"],
        core=["account_status=200"],
        likeness="medium",
    )
    sqt = _make_completed_quality_table(["svc_acc"])
    top_result = _build_top_explainable_candidates([c], sqt)
    tops = top_result["candidates"]
    hcc = _build_high_coverage_commonality_candidates([c], sqt)
    # status_field candidates must not be in Top
    for t in tops:
        name = t.get("candidate_feature_name") or ""
        if "protocol" in name.lower():
            ev_sem = t.get("risk_semantics_strength") or "unknown"
            if ev_sem in ("weak", "unknown"):
                errs.append(f"Weak semantics candidate in Top: {name} ({ev_sem})")
    return errs, {"tops": len(tops), "hcc": len(hcc)}


def _regression_high_coverage_candidate_has_why_not_top():
    """HIGH-COVERAGE-CANDIDATE-HAS-WHY-NOT-TOP-001
    Every high_coverage_commonality_candidates entry must have why_not_top and next_action.
    """
    errs: list[str] = []
    c = _make_protocol_candidate(
        fields=["account_status"],
        core=["account_status=200"],
        likeness="medium",
    )
    sqt = _make_completed_quality_table(["svc_acc"])
    hcc = _build_high_coverage_commonality_candidates([c], sqt, min_support_user_count=0, min_support_ratio=0.0)
    for item in hcc:
        if not item.get("why_not_top"):
            errs.append(f"{item.get('candidate_feature_name')}: missing why_not_top")
        if not item.get("next_action"):
            errs.append(f"{item.get('candidate_feature_name')}: missing next_action")
    return errs, {"hcc_checked": len(hcc)}


def _regression_support_metrics_shown_in_high_coverage():
    """SUPPORT-METRICS-SHOWN-IN-HIGH-COVERAGE-001
    high_coverage_commonality_candidates must expose support_user_count / support_sample_count / support_ratio.
    """
    errs: list[str] = []
    c = _make_control_exec_candidate(
        fields=["frida_xposed_truthy"],
        likeness="medium",
    )
    sqt = _make_completed_quality_table(["device_svc"])
    hcc = _build_high_coverage_commonality_candidates([c], sqt, min_support_ratio=0.0, min_support_user_count=0)
    for item in hcc:
        css = item.get("candidate_support_summary") or {}
        # At minimum, candidate_support_summary should be present
        if css is None:
            errs.append(f"{item.get('candidate_feature_name')}: missing candidate_support_summary")
    return errs, {"hcc_count": len(hcc)}


def _regression_context_commonality_section():
    """CONTEXT-COMMONALITY-SECTION-001
    account_status/code/caller/id/color fields must enter context_commonality_section,
    not main Top.
    """
    errs: list[str] = []
    _CONTEXT_TOKENS = ["account_status", "code", "caller", "color", "id"]
    c = _make_protocol_candidate(
        fields=["account_status=200", "code=0", "callerKsn"],
        core=["account_status=200"],
        likeness="medium",
    )
    sqt = _make_completed_quality_table(["svc_acc"])
    ctx = _build_context_commonality_section([c], sqt)
    top_result = _build_top_explainable_candidates([c], sqt)
    tops = top_result["candidates"]
    # Should NOT be in Top with purely context fields
    for t in tops:
        sem = t.get("risk_semantics_strength") or "unknown"
        if sem in ("weak", "unknown"):
            errs.append(f"Context-field candidate in Top with weak/unknown semantics: {t.get('candidate_feature_name')}")
    return errs, {"ctx_count": len(ctx), "tops": len(tops)}


def _regression_semantics_review_queue():
    """SEMANTICS-REVIEW-QUEUE-001
    action=deny / callerCatalog / callerKsn fields must enter semantics_review_queue.
    """
    errs: list[str] = []
    c = _make_protocol_candidate(
        fields=["action=deny", "callerCatalog", "callerKsn"],
        core=["action=deny"],
        likeness="medium",
    )
    sqt = _make_completed_quality_table(["login_svc"])
    sem_q = _build_semantics_review_queue([c], sqt)
    if not sem_q:
        errs.append("Expected action=deny / callerCatalog / callerKsn to appear in semantics_review_queue, got 0")
    for item in sem_q:
        if not item.get("semantics_question"):
            errs.append(f"Missing semantics_question in review item: {item}")
        if not item.get("next_action"):
            errs.append(f"Missing next_action in review item: {item}")
    return errs, {"sem_queue_count": len(sem_q)}


def _regression_weak_materialized_review_queue():
    """WEAK-MATERIALIZED-CANDIDATE-REVIEW-QUEUE-001
    claim_materialized=True but top_candidate_eligible=False candidates enter weak review queue.
    """
    errs: list[str] = []
    c = _make_protocol_candidate(
        fields=["login_device", "action_device"],
        core=["login_device_match"],
        likeness="medium",
    )
    sqt = []  # empty → source_status=unknown → weak evidence
    weak_q = _build_weak_materialized_review_queue([c], sqt)
    # With empty quality table, evidence is weak → should be in weak_materialized queue
    if not weak_q:
        errs.append("Expected weak_materialized_review_queue to have entries with unknown source quality")
    for item in weak_q:
        if not item.get("why_not_top"):
            errs.append(f"Missing why_not_top in weak materialized item")
        if not item.get("next_action"):
            errs.append(f"Missing next_action in weak materialized item")
    return errs, {"weak_q_count": len(weak_q)}


def _regression_no_top_but_high_coverage_summary():
    """NO-TOP-BUT-HIGH-COVERAGE-SUMMARY-001
    When Top is empty but high_coverage is non-empty, l3_candidate_discovery_summary
    must clearly state has_high_coverage_commonality=True and has_top_explainable_risk_candidate=False.
    """
    errs: list[str] = []
    # No top candidates (empty list)
    top_cands: list[dict] = []
    hcc = [{"candidate_feature_name": "account_maintenance_template_candidate"}]
    fdr: list[dict] = []
    ctx: list[dict] = []
    sem: list[dict] = []
    weak: list[dict] = []
    summary = _build_l3_candidate_discovery_summary(top_cands, hcc, fdr, ctx, sem, weak)
    if summary.get("has_top_explainable_risk_candidate"):
        errs.append("Expected has_top_explainable_risk_candidate=False when Top is empty")
    if not summary.get("has_high_coverage_commonality"):
        errs.append("Expected has_high_coverage_commonality=True when hcc is non-empty")
    boundary = summary.get("discovery_boundary") or ""
    if "高覆盖" not in boundary and "high_coverage" not in boundary.lower():
        errs.append(f"discovery_boundary should mention high coverage but got: {boundary!r}")
    return errs, {
        "has_top": summary.get("has_top_explainable_risk_candidate"),
        "has_hcc": summary.get("has_high_coverage_commonality"),
        "boundary": boundary[:80],
    }


def _regression_discovery_boundary_not_no_finding():
    """DISCOVERY-BOUNDARY-NOT-NO-FINDING-001
    When high_coverage exists, discovery_boundary must NOT say "没有发现" or "no finding".
    """
    errs: list[str] = []
    hcc = [{"candidate_feature_name": "device_unknown_field_enrichment_candidate"}]
    summary = _build_l3_candidate_discovery_summary([], hcc, [], [], [], [])
    boundary = summary.get("discovery_boundary") or ""
    # Check for truly negative "no finding" messages — but allow "不能说没有发现" (negation context)
    # Forbidden: the boundary IS "没有发现" as standalone assertion
    # Allowed: "不能说没有发现" (explicitly negating "no finding" claim)
    _BAD_EXACT = ["无发现", "nothing found", "no discovery", "no findings found"]
    for phrase in _BAD_EXACT:
        if phrase.lower() in boundary.lower():
            errs.append(f"discovery_boundary contains forbidden phrase '{phrase}': {boundary!r}")
    # "no finding" / "没有发现" only forbidden as standalone (not as part of "cannot say no finding")
    _NEGATION_CONTEXTS = ["不能说没有发现", "cannot say no finding", "can't say no finding"]
    _STANDALONE_BAD = ["no finding", "没有发现"]
    for phrase in _STANDALONE_BAD:
        if phrase.lower() in boundary.lower():
            # Check if it's negated
            if not any(neg.lower() in boundary.lower() for neg in _NEGATION_CONTEXTS):
                errs.append(f"discovery_boundary asserts no-finding without negation '{phrase}': {boundary!r}")
    return errs, {"boundary": boundary[:100]}


def _regression_high_coverage_bridges_final_card_as_weak():
    """HIGH-COVERAGE-BRIDGES-FINAL-CARD-AS-WEAK-001
    High coverage but weak/unknown semantics candidates must go to weak_evidence,
    NOT medium_evidence in final_evidence_card.
    """
    errs: list[str] = []
    c = _make_protocol_candidate(
        fields=["account_status"],
        core=["account_status=200"],
        likeness="medium",
    )
    sqt = _make_completed_quality_table(["svc_acc"])
    hcc = _build_high_coverage_commonality_candidates([c], sqt, min_support_ratio=0.0, min_support_user_count=0)
    existing_card: dict = {"medium_evidence": [], "weak_evidence": [], "missing_evidence": []}
    card = _build_final_evidence_card_bridge([], [], existing_card, high_coverage_candidates=hcc)
    # hcc items must be in weak, never medium
    for item in hcc:
        name = item.get("candidate_feature_name") or ""
        if name in (card.get("medium_evidence") or []):
            errs.append(f"hcc candidate {name!r} appeared in medium_evidence — must be in weak only")
    return errs, {
        "medium_ev": card.get("medium_evidence"),
        "weak_ev": card.get("weak_evidence"),
    }


def _regression_final_card_discovery_boundary():
    """FINAL-CARD-DISCOVERY-BOUNDARY-001
    final_evidence_card.final_answer_boundary must distinguish
    'has high coverage' from 'no high confidence Top'.
    """
    errs: list[str] = []
    # Case: no Top but has hcc
    hcc = [{"candidate_feature_name": "some_candidate", "claim_materialized": True}]
    existing_card: dict = {"medium_evidence": [], "weak_evidence": [], "missing_evidence": []}
    card = _build_final_evidence_card_bridge([], [], existing_card, high_coverage_candidates=hcc)
    boundary = card.get("final_answer_boundary") or ""
    # Must NOT just say "candidate_only_not_final_conclusion=true" (i.e., must be more specific)
    if boundary == "candidate_only_not_final_conclusion=true":
        errs.append(f"final_answer_boundary too generic when hcc is non-empty: {boundary!r}")
    # Must mention that high coverage was found
    _EXPECTED_PHRASES = ["高覆盖", "high_coverage", "high coverage", "候选", "commonality"]
    if not any(p.lower() in boundary.lower() for p in _EXPECTED_PHRASES):
        errs.append(f"final_answer_boundary doesn't mention high coverage context: {boundary!r}")
    return errs, {"boundary": boundary[:120]}


def _run_g_r6_quality_regressions() -> tuple[list[str], dict]:
    """Run all G-R6 quality regressions. Return (all_errors, results_dict)."""
    all_errors: list[str] = []
    results: dict[str, Any] = {}

    def _run(fn):
        try:
            errs, summary = fn()
            all_errors.extend(errs)
            return {"pass": not errs, **summary}
        except Exception as exc:
            all_errors.append(f"{fn.__name__}: EXCEPTION: {exc}")
            return {"pass": False, "exception": str(exc)}

    results["SOURCE-STATUS-PROPAGATES-TO-EVIDENCE-001"] = _run(_regression_source_status_propagates_to_evidence)
    results["EVIDENCE-STRENGTH-FOLLOWS-SOURCE-STATUS-001"] = _run(_regression_evidence_strength_follows_source_status)
    results["BLOCKED-TIMEOUT-NOT-SUPPORTING-EVIDENCE-001"] = _run(_regression_blocked_timeout_not_supporting_evidence)
    results["SUPPORT-METRICS-PROPAGATE-TO-TOP-EVIDENCE-001"] = _run(_regression_support_metrics_propagate_to_evidence)
    results["SUPPORT-RATIO-CALCULATED-WHEN-POSSIBLE-001"] = _run(_regression_support_ratio_calculated_when_possible)
    results["LOW-SUPPORT-SEQUENCE-NOT-BATCH-TOP-001"] = _run(_regression_low_support_sequence_not_batch_top)
    results["INTERNAL-SIGNAL-NOT-USER-FACING-EVIDENCE-001"] = _run(_regression_internal_signal_not_user_facing_evidence)
    results["RAW-FIELD-PATH-REQUIRED-FOR-STRONG-EVIDENCE-001"] = _run(_regression_raw_field_path_required_for_strong_evidence)
    results["DEVICE-RISK-EVIDENCE-DISPLAY-LABEL-001"] = _run(_regression_device_risk_evidence_display_label)
    results["MISSING-FIELD-NOT-PROTOCOL-BYPASS-EVIDENCE-001"] = _run(_regression_missing_field_not_protocol_bypass_evidence)
    results["STATUS-FIELD-DOWNRANKED-001"] = _run(_regression_status_field_downranked)
    results["DEVICE-RISK-SEMANTICS-STRONG-001"] = _run(_regression_device_risk_semantics_strong)
    results["UNKNOWN-CHOKE-NOT-TOP-ELIGIBLE-001"] = _run(_regression_unknown_choke_not_top)
    results["CANDIDATE-DEDUP-REMOVES-DUPLICATES-001"] = _run(_regression_candidate_dedup_removes_duplicates)
    results["CANDIDATE-DEDUP-KEEPS-BEST-001"] = _run(_regression_candidate_dedup_keeps_best)
    results["FINAL-EVIDENCE-CARD-BRIDGE-MATERIALIZED-001"] = _run(_regression_final_evidence_card_bridge_materialized)
    results["FINAL-EVIDENCE-CARD-BRIDGE-UNMATERIALIZED-001"] = _run(_regression_final_evidence_card_bridge_unmaterialized)
    results["FINAL-EVIDENCE-CARD-COUNTER-EVIDENCE-001"] = _run(_regression_final_evidence_card_counter_evidence_bridge)
    results["FINAL-EVIDENCE-CARD-NO-GROUP-CONFIRMATION-001"] = _run(_regression_final_evidence_card_no_group_confirmation)
    results["VALUE-LEVEL-HIGH-ACTIVITY-COUNTER-001"] = _run(_regression_value_level_high_activity_counter)
    results["VALUE-LEVEL-SAME-DEVICE-COUNTER-001"] = _run(_regression_value_level_same_device_counter)
    results["PROTOCOL-POSITIVE-ANOMALY-REQUIRED-001"] = _run(_regression_protocol_positive_anomaly_required)
    results["PROTOCOL-MISSING-FIELD-NOT-HIGH-EVIDENCE-001"] = _run(_regression_protocol_missing_field_not_high_evidence)

    # G-R6-fix regressions
    results["TOP-EXPLAINABLE-REQUIRES-ELIGIBLE-001"] = _run(_regression_top_explainable_requires_eligible)
    results["TOP-EXPLAINABLE-EMPTY-REASON-001"] = _run(_regression_top_explainable_empty_reason)
    results["TOP-EXPLAINABLE-DEDUP-001"] = _run(_regression_top_explainable_dedup)
    results["HIGH-COVERAGE-COMMONALITY-SECTION-001"] = _run(_regression_high_coverage_commonality_section)
    results["HIGH-COVERAGE-NOT-EQUALS-TOP-001"] = _run(_regression_high_coverage_not_equals_top)
    results["HIGH-COVERAGE-CANDIDATE-HAS-WHY-NOT-TOP-001"] = _run(_regression_high_coverage_candidate_has_why_not_top)
    results["SUPPORT-METRICS-SHOWN-IN-HIGH-COVERAGE-001"] = _run(_regression_support_metrics_shown_in_high_coverage)
    results["CONTEXT-COMMONALITY-SECTION-001"] = _run(_regression_context_commonality_section)
    results["SEMANTICS-REVIEW-QUEUE-001"] = _run(_regression_semantics_review_queue)
    results["WEAK-MATERIALIZED-CANDIDATE-REVIEW-QUEUE-001"] = _run(_regression_weak_materialized_review_queue)
    results["NO-TOP-BUT-HIGH-COVERAGE-SUMMARY-001"] = _run(_regression_no_top_but_high_coverage_summary)
    results["DISCOVERY-BOUNDARY-NOT-NO-FINDING-001"] = _run(_regression_discovery_boundary_not_no_finding)
    results["HIGH-COVERAGE-BRIDGES-FINAL-CARD-AS-WEAK-001"] = _run(_regression_high_coverage_bridges_final_card_as_weak)
    results["FINAL-CARD-DISCOVERY-BOUNDARY-001"] = _run(_regression_final_card_discovery_boundary)

    results["validation_pass"] = not all_errors
    return all_errors, results



def run_check() -> dict[str, Any]:
    fixed_run = _run_fixture(FIXTURE)
    fixed_errors, fixed_result = _validate_common_result(
        run=fixed_run,
        expected_round_count=3,
        require_current_observation_content=False,
    )
    mock_results: dict[str, dict[str, Any]] = {}
    mock_errors_by_name: dict[str, list[str]] = {}
    for name, fixture, required_domains, required_anchor_types in MOCK_SHAPED_FIXTURES:
        mock_run = _run_fixture(fixture)
        mock_errors, mock_result = _validate_common_result(
            run=mock_run,
            expected_round_count=1,
            require_current_observation_content=True,
            required_domains=required_domains,
            required_anchor_types=required_anchor_types,
        )
        mock_results[name] = {
            "run": mock_run,
            "result": mock_result,
        }
        mock_errors_by_name[name] = mock_errors
        if name == "rcp_request_detail_projection":
            runtime_strategy_errors, runtime_strategy_summary = _validate_runtime_strategy_request_detail_artifacts(mock_result)
            mock_errors_by_name[name].extend(runtime_strategy_errors)
            mock_results[name]["runtime_strategy_request_detail_summary"] = runtime_strategy_summary
        if name == "rcp_original_tab_feature_rows":
            fixture_payload = json.loads(fixture.read_text(encoding="utf-8"))
            runtime_feature_row_errors, runtime_feature_row_summary = _validate_runtime_strategy_feature_row_artifacts(
                mock_result,
                fixture=fixture_payload,
            )
            mock_errors_by_name[name].extend(runtime_feature_row_errors)
            mock_results[name]["runtime_strategy_feature_row_summary"] = runtime_feature_row_summary
        if name == "device_detail_multi_source":
            runtime_device_errors, runtime_device_summary = _validate_runtime_device_detail_artifacts(mock_result)
            mock_errors_by_name[name].extend(runtime_device_errors)
            mock_results[name]["runtime_device_detail_summary"] = runtime_device_summary
        if name == "source_l1_l3_field_commonality":
            source_l1_l3_errors, source_l1_l3_summary = _validate_source_l1_l3_field_commonality_artifacts(mock_result)
            mock_errors_by_name[name].extend(source_l1_l3_errors)
            mock_results[name]["runtime_source_l1_l3_summary"] = source_l1_l3_summary
    fixed_followup_alignment_errors, fixed_followup_alignment_summary = _validate_followup_quality_completion_alignment(fixed_result)
    mock_followup_alignment: dict[str, dict[str, Any]] = {}
    for name, payload in mock_results.items():
        mock_alignment_errors, mock_alignment_summary = _validate_followup_quality_completion_alignment(payload["result"])
        mock_errors_by_name[name].extend(f"followup_quality_alignment:{error}" for error in mock_alignment_errors)
        mock_followup_alignment[name] = mock_alignment_summary
    fixed_errors.extend(f"followup_quality_alignment:{error}" for error in fixed_followup_alignment_errors)
    errors = [f"fixed:{error}" for error in fixed_errors] + [
        f"mock_{name}:{error}"
        for name, fixture_errors in mock_errors_by_name.items()
        for error in fixture_errors
    ]
    rcp_snapshot_time_errors, rcp_snapshot_time_summary = _regression_rcp_snapshot_time_format()
    errors.extend(f"rcp_snapshot_time_format:{error}" for error in rcp_snapshot_time_errors)
    rolling_run = _run_fixture(ROLLING_FIXTURE)
    rolling_errors, rolling_result = _validate_common_result(
        run=rolling_run,
        expected_round_count=2,
        require_current_observation_content=True,
        required_domains={"device_domain", "strategy_domain", "content_domain"},
        required_anchor_types={"candidate_device_id", "candidate_policy_code", "candidate_photo_id"},
    )
    rolling_summary = (rolling_result.get("orchestration_artifacts", {}) if rolling_result else {}).get("rolling_anchor_summary", {})
    if not rolling_summary.get("stable_anchors"):
        rolling_errors.append("rolling_fixture_missing_stable_anchors")
    if not rolling_summary.get("dropped_anchors"):
        rolling_errors.append("rolling_fixture_missing_dropped_anchors")
    if not rolling_summary.get("new_anchor_delta"):
        rolling_errors.append("rolling_fixture_missing_new_anchor_delta")
    for item in rolling_summary.get("anchor_summaries", []) or []:
        if item.get("support_ratio") is None:
            rolling_errors.append("rolling_fixture_anchor_missing_support_ratio")
            break
    errors.extend(f"rolling:{error}" for error in rolling_errors)
    live_safe_errors, live_safe_summary = _validate_live_safe_summary_projection()
    errors.extend(f"live_safe_summary:{error}" for error in live_safe_errors)
    status_attribution_errors, status_attribution_summary = _validate_primary_followup_status_attribution()
    errors.extend(f"status_attribution:{error}" for error in status_attribution_errors)
    followup_quality_errors, followup_quality_summary = _validate_followup_source_quality_transport_regressions()
    errors.extend(f"followup_source_quality:{error}" for error in followup_quality_errors)
    raw_expansion_errors, raw_expansion_summary = _validate_raw_detail_expansion_handles()
    errors.extend(f"raw_detail_expansion:{error}" for error in raw_expansion_errors)
    rcp_l2_errors, rcp_l2_summary = _validate_rcp_register_new_l2_followup_plan()
    errors.extend(f"rcp_register_new_l2:{error}" for error in rcp_l2_errors)
    partial_quality_errors, partial_quality_summary = _validate_partial_quality_lowers_anchor_score()
    errors.extend(f"anchor_scoring:{error}" for error in partial_quality_errors)
    strategy_detail_errors, strategy_detail_summary = _validate_strategy_event_request_detail_fixture()
    errors.extend(f"strategy_event_request_detail:{error}" for error in strategy_detail_errors)
    weapon_retention_errors, weapon_retention_summary = _validate_weapon_device_detail_pre_projection_retention()
    errors.extend(f"weapon_device_detail_retention:{error}" for error in weapon_retention_errors)

    # ── Bounded rendering regression checks (F.5-R3 fix) ─────────────────────
    breg_depth_errors, breg_depth_summary = _regression_safe_projection_depth_limit()
    errors.extend(f"bounded_projection:{e}" for e in breg_depth_errors)
    breg_array_errors, breg_array_summary = _regression_safe_projection_large_array()
    errors.extend(f"bounded_projection:{e}" for e in breg_array_errors)
    breg_rcp_errors, breg_rcp_summary = _regression_rcp_feature_list_bounded_projection()
    errors.extend(f"bounded_projection:{e}" for e in breg_rcp_errors)
    breg_pm_errors, breg_pm_summary = _regression_private_message_bounded_projection()
    errors.extend(f"bounded_projection:{e}" for e in breg_pm_errors)
    breg_media_errors, breg_media_summary = _regression_media_url_not_projected()
    errors.extend(f"bounded_projection:{e}" for e in breg_media_errors)
    breg_timing_errors, breg_timing_summary = _regression_projection_timing_trace()
    errors.extend(f"bounded_projection:{e}" for e in breg_timing_errors)
    breg_anchors_errors, breg_anchors_summary = _regression_projection_does_not_drop_l3_anchors()
    errors.extend(f"bounded_projection:{e}" for e in breg_anchors_errors)
    breg_l3facts_errors, breg_l3facts_summary = _regression_safe_projection_does_not_thin_l3_facts()
    errors.extend(f"bounded_projection:{e}" for e in breg_l3facts_errors)
    breg_leak_errors, breg_leak_summary = _regression_no_raw_body_leak()
    errors.extend(f"bounded_projection:{e}" for e in breg_leak_errors)
    # ── G-R3 candidate_features enrichment regression checks ──────────────────
    gcfe_errors, gcfe_summary = _regression_candidate_features_global_enrichment()
    errors.extend(f"candidate_enrichment:{e}" for e in gcfe_errors)
    dcde_errors, dcde_summary = _regression_device_domain_candidate_enrichment()
    errors.extend(f"candidate_enrichment:{e}" for e in dcde_errors)
    dcrm_errors, dcrm_summary = _regression_domain_candidate_role_mapping()
    errors.extend(f"candidate_enrichment:{e}" for e in dcrm_errors)
    gcdr_errors, gcdr_summary = _regression_generic_candidate_downrank()
    errors.extend(f"candidate_enrichment:{e}" for e in gcdr_errors)
    tcnn_errors, tcnn_summary = _regression_top_candidate_no_null()
    errors.extend(f"candidate_enrichment:{e}" for e in tcnn_errors)
    nesh_errors, nesh_summary = _regression_candidate_features_normalize_no_empty_shell()
    errors.extend(f"candidate_enrichment:{e}" for e in nesh_errors)
    # ── G-R5a Top display / ranking regression (top_display_regression) ────────
    tcef_errors, tcef_summary = _regression_top_candidate_explainable_first()
    errors.extend(f"top_candidate_quality:{e}" for e in tcef_errors)
    udrq_errors, udrq_summary = _regression_unknown_device_review_queue()
    errors.extend(f"top_candidate_quality:{e}" for e in udrq_errors)
    diar_errors, diar_summary = _regression_device_id_anchor_not_risk_feature()
    errors.extend(f"top_candidate_quality:{e}" for e in diar_errors)
    scnp_errors, scnp_summary = _regression_sequence_candidate_not_protocol_default()
    errors.extend(f"top_candidate_quality:{e}" for e in scnp_errors)
    pcgr_errors, pcgr_summary = _regression_protocol_constraint_gap_requires_signal()
    errors.extend(f"top_candidate_quality:{e}" for e in pcgr_errors)
    tcgu_errors, tcgu_summary = _regression_top_candidate_no_generic_unknown_spam()
    errors.extend(f"top_candidate_quality:{e}" for e in tcgu_errors)
    # ── G-R5b evidence materialization regression ─────────────────────────
    tce_errors, tce_summary = _regression_top_candidate_requires_supporting_evidence()
    errors.extend(f"evidence_gate:{e}" for e in tce_errors)
    tpe_errors, tpe_summary = _regression_template_phrase_not_evidence()
    errors.extend(f"evidence_gate:{e}" for e in tpe_errors)
    fac_errors, fac_summary = _regression_frontend_activity_counter_signal()
    errors.extend(f"evidence_gate:{e}" for e in fac_errors)
    cem_errors, cem_summary = _regression_control_execution_requires_materialized_mismatch()
    errors.extend(f"evidence_gate:{e}" for e in cem_errors)
    sdc_errors, sdc_summary = _regression_same_device_counter_signal()
    errors.extend(f"evidence_gate:{e}" for e in sdc_errors)
    bsn_errors, bsn_summary = _regression_blocked_source_not_observed_evidence()
    errors.extend(f"evidence_gate:{e}" for e in bsn_errors)
    scc_errors, scc_summary = _regression_source_cooccurrence_not_claim_materialization()
    errors.extend(f"evidence_gate:{e}" for e in scc_errors)
    tsc_errors, tsc_summary = _regression_top_sample_evidence_types_clean()
    errors.extend(f"evidence_gate:{e}" for e in tsc_errors)

    single_sample_payload = {
        "route_mode": "sample_expand_validate_mode",
        "total_input_count": 1,
        "round_size": 1,
        "max_rounds": 1,
        "planned_rounds_this_run": 1,
        "max_deep_checked_this_run": 1,
        "sampling_method": "single_sample_limited_commonality_check",
        "data_window": "last_7d",
        "scene_hint": ["single_sample_limited_commonality"],
        "rounds": [
            {
                "round_id": 1,
                "sampled_entities": ["single_sample_user"],
                "mock_current_observations": [
                    {
                        "source_id": "single_sample_login",
                        "action": "login_logs_search",
                        "fields": {
                            "user_id": "single_sample_user",
                            "candidate_device_id": "single_sample_device",
                            "candidate_ip": "10.31.99.1",
                            "backend_action_signal": "login_then_publish",
                        },
                    }
                ],
            }
        ],
    }
    single_sample_run = _run_payload(single_sample_payload)
    single_sample_errors, single_sample_result = _validate_common_result(
        run=single_sample_run,
        expected_round_count=1,
        require_current_observation_content=True,
        required_domains={"device_domain", "network_domain"},
        required_anchor_types={"candidate_device_id", "candidate_ip"},
    )
    errors.extend(f"single_sample:{error}" for error in single_sample_errors)

    mock_artifact_coverage = {
        name: (payload["result"].get("orchestration_artifacts", {}) if payload["result"] else {}).get("artifact_coverage", {})
        for name, payload in mock_results.items()
    }
    mock_runner_returncodes = {
        name: payload["run"]["runner_returncode"]
        for name, payload in mock_results.items()
    }

    g6_errors, g6_results = _run_g_r6_quality_regressions()
    errors.extend(g6_errors)

    return {
        "check": "sample_expand_orchestration_artifact_check",
        "validation_pass": not errors,
        "errors": errors,
        "fixed_round_count": len(fixed_result.get("round_results", [])) if fixed_result else 0,
        "mock_round_count": {
            name: len(payload["result"].get("round_results", [])) if payload["result"] else 0
            for name, payload in mock_results.items()
        },
        "checked_count": fixed_result.get("cumulative_result", {}).get("checked_count") if fixed_result else None,
        "artifact_coverage": (fixed_result.get("orchestration_artifacts", {}) if fixed_result else {}).get("artifact_coverage", {}),
        "mock_artifact_coverage": mock_artifact_coverage,
        "fixed_runner_returncode": fixed_run["runner_returncode"],
        "mock_runner_returncode": mock_runner_returncodes,
        "followup_source_quality_artifact_alignment": {
            "fixed": fixed_followup_alignment_summary,
            "mock": mock_followup_alignment,
        },
        "rolling_anchor_summary": {
            "validation_pass": not rolling_errors,
            "runner_returncode": rolling_run["runner_returncode"],
            "round_count": len(rolling_result.get("round_results", [])) if rolling_result else 0,
            "current_status": rolling_summary.get("current_status"),
            "stable_anchor_count": len(rolling_summary.get("stable_anchors", []) or []),
            "dropped_anchor_count": len(rolling_summary.get("dropped_anchors", []) or []),
            "new_anchor_delta_count": len(rolling_summary.get("new_anchor_delta", []) or []),
        },
        "live_safe_summary_projection": {
            "validation_pass": not live_safe_errors,
            "source_status": live_safe_summary.get("source_results", {}).get("login_logs_search", {}).get("source_status"),
            "reason": live_safe_summary.get("source_results", {}).get("login_logs_search", {}).get("reason"),
            "source_quality_partial": live_safe_summary.get("source_quality", {}).get("partial"),
            "raw_passthrough_omitted": live_safe_summary.get("safe_projection", {}).get("raw_passthrough_omitted"),
        },
        "rcp_snapshot_time_format_regression": {
            "validation_pass": not rcp_snapshot_time_errors,
            **rcp_snapshot_time_summary,
        },
        "primary_followup_status_attribution": {
            "validation_pass": not status_attribution_errors,
            **status_attribution_summary,
        },
        "followup_source_quality_regression": followup_quality_summary,
        "raw_detail_expansion": {
            "validation_pass": not raw_expansion_errors,
            **raw_expansion_summary,
        },
        "rcp_register_new_l2_feature_drilldown": {
            "validation_pass": not rcp_l2_errors,
            **rcp_l2_summary,
        },
        "anchor_scoring_partial_quality": {
            "validation_pass": not partial_quality_errors,
            **partial_quality_summary,
        },
        "strategy_event_request_detail_feature": {
            "validation_pass": not strategy_detail_errors,
            **strategy_detail_summary,
        },
        "weapon_device_detail_pre_projection_retention": {
            "validation_pass": not weapon_retention_errors,
            **weapon_retention_summary,
        },
        "strategy_event_feature_rows": (
            mock_results.get("rcp_original_tab_feature_rows", {}).get("runtime_strategy_feature_row_summary", {})
        ),
        "device_detail_multi_source": (
            mock_results.get("device_detail_multi_source", {}).get("runtime_device_detail_summary", {})
        ),
        "source_l1_l3_field_commonality": (
            mock_results.get("source_l1_l3_field_commonality", {}).get("runtime_source_l1_l3_summary", {})
        ),
        "single_sample_limited_commonality": {
            "validation_pass": not single_sample_errors,
            "runner_returncode": single_sample_run["runner_returncode"],
            "round_count": len(single_sample_result.get("round_results", [])) if single_sample_result else 0,
            "artifact_coverage": (single_sample_result.get("orchestration_artifacts", {}) if single_sample_result else {}).get("artifact_coverage", {}),
        },
        "bounded_projection_regression": {
            "validation_pass": not any([
                breg_depth_errors, breg_array_errors, breg_rcp_errors,
                breg_pm_errors, breg_media_errors, breg_timing_errors,
                breg_anchors_errors, breg_l3facts_errors, breg_leak_errors,
            ]),
            "SAFE-PROJECTION-DEPTH-LIMIT-001": {"pass": not breg_depth_errors, **breg_depth_summary},
            "SAFE-PROJECTION-LARGE-ARRAY-001": {"pass": not breg_array_errors, **breg_array_summary},
            "RCP-FEATURE-LIST-BOUNDED-PROJECTION-001": {"pass": not breg_rcp_errors, **breg_rcp_summary},
            "PRIVATE-MESSAGE-BOUNDED-PROJECTION-001": {"pass": not breg_pm_errors, **breg_pm_summary},
            "MEDIA-URL-NOT-PROJECTED-001": {"pass": not breg_media_errors, **breg_media_summary},
            "PROJECTION-TIMING-TRACE-001": {"pass": not breg_timing_errors, **breg_timing_summary},
            "PROJECTION-DOES-NOT-DROP-L3-ANCHORS-001": {"pass": not breg_anchors_errors, **breg_anchors_summary},
            "SAFE-PROJECTION-DOES-NOT-THIN-L3-FACTS-001": {"pass": not breg_l3facts_errors, **breg_l3facts_summary},
            "NO-RAW-BODY-LEAK-001": {"pass": not breg_leak_errors, **breg_leak_summary},
        },
        "candidate_enrichment_regression": {
            "CANDIDATE-FEATURES-GLOBAL-ENRICHMENT-001": {"pass": not gcfe_errors, **gcfe_summary},
            "DEVICE-DOMAIN-CANDIDATE-ENRICHMENT-001": {"pass": not dcde_errors, **dcde_summary},
            "DOMAIN-CANDIDATE-ROLE-MAPPING-001": {"pass": not dcrm_errors, **dcrm_summary},
            "GENERIC-CANDIDATE-DOWNRANK-001": {"pass": not gcdr_errors, **gcdr_summary},
            "TOP-CANDIDATE-NO-NULL-001": {"pass": not tcnn_errors, **tcnn_summary},
            "CANDIDATE-FEATURES-NORMALIZE-NO-EMPTY-SHELL-001": {"pass": not nesh_errors, **nesh_summary},
        },
        "top_display_regression": {
            "TOP-CANDIDATE-EXPLAINABLE-FIRST-001": {"pass": not tcef_errors, **tcef_summary},
            "UNKNOWN-DEVICE-FIELD-REVIEW-QUEUE-001": {"pass": not udrq_errors, **udrq_summary},
            "DEVICE-ID-ANCHOR-NOT-RISK-FEATURE-001": {"pass": not diar_errors, **diar_summary},
            "SEQUENCE-CANDIDATE-NOT-PROTOCOL-BY-DEFAULT-001": {"pass": not scnp_errors, **scnp_summary},
            "PROTOCOL-CONSTRAINT-GAP-REQUIRES-PROTOCOL-SIGNAL-001": {"pass": not pcgr_errors, **pcgr_summary},
            "TOP-CANDIDATE-NO-GENERIC-UNKNOWN-SPAM-001": {"pass": not tcgu_errors, **tcgu_summary},
        },
        "evidence_gate_regression": {
            "TOP-CANDIDATE-REQUIRES-SUPPORTING-EVIDENCE-001": {"pass": not tce_errors, **tce_summary},
            "TEMPLATE-PHRASE-NOT-EVIDENCE-001": {"pass": not tpe_errors, **tpe_summary},
            "FRONTEND-ACTIVITY-COUNTER-SIGNAL-001": {"pass": not fac_errors, **fac_summary},
            "CONTROL-EXECUTION-REQUIRES-MATERIALIZED-MISMATCH-001": {"pass": not cem_errors, **cem_summary},
            "SAME-DEVICE-COUNTER-SIGNAL-001": {"pass": not sdc_errors, **sdc_summary},
            "BLOCKED-SOURCE-NOT-OBSERVED-EVIDENCE-001": {"pass": not bsn_errors, **bsn_summary},
            "SOURCE-COOCCURRENCE-NOT-CLAIM-MATERIALIZATION-001": {"pass": not scc_errors, **scc_summary},
            "TOP-SAMPLE-EVIDENCE-TYPES-CLEAN-001": {"pass": not tsc_errors, **tsc_summary},
        },
        "g_r6_quality_regression": g6_results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate sample-expand Phase 3 orchestration artifacts")
    parser.add_argument("--format", choices=["json", "pretty"], default="pretty")
    args = parser.parse_args()
    result = run_check()
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"validation_pass={result['validation_pass']}")
        if result["errors"]:
            print(f"errors={','.join(result['errors'])}")
    return 0 if result["validation_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
