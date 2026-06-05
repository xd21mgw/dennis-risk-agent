#!/usr/bin/env python3
"""Run the fixed sample-expand dry-run fixture and validate Phase 3 artifacts."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from runtime_case_execution_runner import (
    build_missing_evidence,
    build_safe_batch_summary,
    build_safe_stdout_result,
    score_candidate_anchors,
)


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "computer_use_poc" / "runtime_case_execution_runner.py"
FIXTURE = ROOT / "computer_use_poc" / "test_fixtures" / "sample_expand_validate_batch_fixed_rounds_v1.json"
ROLLING_FIXTURE = ROOT / "computer_use_poc" / "test_fixtures" / "sample_expand_mock_rolling_anchor_summary_v1.json"
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
            "next_allowed_interfaces": ["track_analysis_check_data_ready", "weapon_inventory"],
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
    partial_quality_errors, partial_quality_summary = _validate_partial_quality_lowers_anchor_score()
    errors.extend(f"anchor_scoring:{error}" for error in partial_quality_errors)

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
        "anchor_scoring_partial_quality": {
            "validation_pass": not partial_quality_errors,
            **partial_quality_summary,
        },
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
