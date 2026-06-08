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
    build_rcp_event_followup_source_plan,
    build_status_attribution,
    build_missing_evidence,
    build_safe_batch_summary,
    build_safe_stdout_result,
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
    errors = [f"fixed:{error}" for error in fixed_errors] + [
        f"mock_{name}:{error}"
        for name, fixture_errors in mock_errors_by_name.items()
        for error in fixture_errors
    ]
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
        "primary_followup_status_attribution": {
            "validation_pass": not status_attribution_errors,
            **status_attribution_summary,
        },
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
