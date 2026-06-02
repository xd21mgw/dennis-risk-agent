#!/usr/bin/env python3
"""Local source orchestration validator for Dennis Risk Agent.

This script is intentionally offline-only. It reads the local source plan and
validates a provided source completion matrix. It does not access platforms,
call DataAgent, read auth state, or execute source wrappers.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = REPO_ROOT / "computer_use_poc" / "source_orchestration_plan_v1.yaml"
WEAPON_GRAPH_REQUIRED_PATH = "/apiv2/graphData"
WEAPON_RISK_REQUIRED_PATH = "/apiv2/riskData"
FORBIDDEN_WEAPON_GRAPH_PATH = "/api/graphData"
TRACK_ANALYSIS_BASE_PATH = "/dp/platform/app/analytics/v2/sequence/"
TRACK_ANALYSIS_REQUIRED_PATHS = {
    "track_analysis_getDeviceIds": TRACK_ANALYSIS_BASE_PATH + "getDeviceIds",
    "track_analysis_getUseDuration": TRACK_ANALYSIS_BASE_PATH + "getUseDuration",
    "track_analysis_profile": TRACK_ANALYSIS_BASE_PATH + "profile",
}
TRACK_ANALYSIS_FORBIDDEN_PATHS = {"/api/profile", "/rest/profile", "/api/user/profile"}
FIXED_BROWSER_BACKED_ACTIONS = {
    "track_analysis_check_data_ready",
    "rcp_snapshot",
    "weapon_inventory",
    "login_logs_search",
    "archives_user_profile",
    "archives_user_analysis",
    "archives_photo_search",
    "archives_related_users",
    "rcp_event_detail",
    "rcp_event_feature_list",
    "rcp_policy_tree_lookup",
}
LEGACY_BROWSER_BACKED_ACTIONS = {
    "track_analysis_summary",  # legacy client unit only; not current ATO case execution default
}
CONTROLLED_PARALLEL_EXECUTION_GROUPS = {
    "independent_parallel",
    "dependency_serial",
    "large_response_serial",
    "auth_sensitive_serial",
}
ATO_REALTIME_P0_REQUIRED_ACTIONS = {
    "login_logs_search",
    "archives_user_profile",
    "archives_user_analysis",
    "archives_photo_search",
    "track_analysis_check_data_ready",
}
ATO_DEVICE_IDENTITY_FIELDS = {
    "device_model",
    "os",
    "UA",
    "IP",
    "login_source",
    "login_type",
}
ATO_REALTIME_INCOMPLETE_REQUIRED_FLAGS = {
    "hive_required_hint",
    "login_log_window_incomplete",
    "admin_app_log_only_gap",
    "web_control_chain_missing",
    "offline_hive_required",
}
ATO_USER_DEVICE_ENTITY_SOURCES = {
    "login_logs_search",
    "archives_user_analysis",
    "archives_photo_search",
    "weapon_inventory",
    "track_analysis_check_data_ready",
}
ATO_EVIDENCE_CHAIN_SECTIONS = {
    "web_or_abnormal_publish_fact",
    "web_history_baseline",
    "device_identity_alignment",
    "control_entry",
    "account_state_and_post_actions",
    "content_publish_handoff",
    "frontend_backend_activity_alignment",
    "device_ip_spread",
    "strategy_risk_signal",
    "counter_evidence_and_gaps",
    "conclusion_boundary",
}
ATO_DYNAMIC_OFFLINE_MODULE_IDS = {
    "web_publish_fact",
    "web_login_history",
    "device_history_baseline",
}
BATCH_ATO_REQUIRED_PLAN_STEPS = {
    "existing_cluster_signal_collection",
    "ato_cluster_lens_overlay",
    "compromised_account_cluster_detection",
    "representative_case_selection",
    "representative_ato_single_case_deep_dive",
    "cluster_level_backfill",
    "batch_conclusion",
}
BATCH_ATO_REQUIRED_LABELS = {
    "ato_cluster_lens",
    "existing_cluster_plus_ato_lens",
    "web_untrusted_login_cluster",
    "login_to_action_cluster",
    "device_identity_inconsistency_cluster",
    "compromised_account_cluster",
    "mixed_cluster",
}
BATCH_ATO_REQUIRED_ANSWER_MARKERS = {
    "ato_cluster_lens",
    "existing_cluster_plus_ato_lens",
    "representative_ato_single_case_deep_dive",
    "cluster_level_backfill",
}
UNIVERSAL_WORKFLOW_REQUIRED_STEPS = {
    "risk_hypothesis_and_source_plan",
    "realtime_readonly_source_collection",
    "evidence_chain_closure_check",
    "partial_evidence_missing_evidence_when_not_closed",
    "offline_supplement_plan_by_risk_scene",
    "dataagent_hive_per_request_authorization",
    "cluster_expansion_when_batch_or_similar",
}
UNIVERSAL_OFFLINE_SCENES = {
    "account_takeover",
    "anti_cheating",
    "traffic_diversion",
    "strategy_governance",
}
ATO_CLUSTER_SIGNAL_DIMENSIONS = {
    "control_entry_commonality",
    "device_commonality",
    "ip_network_commonality",
    "temporal_sequence_commonality",
    "behavior_handoff_commonality",
    "frontend_activity_commonality",
    "strategy_signal_commonality",
    "user_claim_and_counter_evidence",
}
PASSTHROUGH_ENVELOPE_REQUIRED_FIELDS = {
    "action_name",
    "source_id",
    "platform",
    "http_status",
    "content_type",
    "body_present",
    "body_truncated",
    "observed_bytes",
    "elapsed_ms",
    "transport_error",
    "platform_error",
    "invalid_params",
    "timeout",
    "auth_redirect_detected",
    "raw_body_handling",
}
PASSTHROUGH_BATCH_REQUIRED_FIELDS = {
    "batch_status",
    "source_results",
    "transport_status_matrix",
    "classifications",
    "missing_or_failed_sources",
}
LEGACY_SERVICE_BUSINESS_FIELDS = {
    "normalized_observation",
    "source_quality",
    "source_quality_matrix",
    "evidence_card_inputs",
    "source_card",
    "compat_summary",
    "risk_event_scan",
    "feature_group_summary",
}
DENNIS_GENERATED_PASSTHROUGH_FIELDS = {
    "observation",
    "source_quality_matrix",
    "evidence_card",
    "missing_evidence",
    "final_answer_boundary",
}
USER_FACING_RUNTIME_YAML_MARKERS = {
    "routing_metadata:",
    "source_quality:",
    "boundary_flags:",
    "execution_mode:",
    "validator:",
    "validation_pass:",
    "debug_metadata:",
    "platform_debug:",
    "platform_call_summary:",
    "source_completion_matrix:",
}
USER_FACING_CONTEXTS = {
    "ato_single_case_business_answer",
    "batch_ato_cluster_answer",
    "partial_evidence_card",
    "local_patch_completion_report",
    "codex_final_summary",
    "generic_user_facing_answer",
}
FORBIDDEN_ACCESS_METHODS = {"curl_cookie", "manual_cookie", "main_agent_direct_exec", "arbitrary_url"}
NO_DATA_STATUSES = {"no_data", "blocked", "auth_failed", "timeout", "parse_error", "tool_gap", "auth_bridge_gap"}
NON_ENDPOINT_STATUSES = {"skipped", "missing_required_fields", "not_checked", "blocked", "auth_failed", "timeout", "tool_gap", "auth_bridge_gap"}
EXPLAINED_NOT_EXECUTED_STATUSES = {"blocked", "auth_failed", "not_checked", "missing_required_fields", "timeout", "parse_error", "tool_gap", "auth_bridge_gap", "no_data"}
ENVIRONMENT_GAP_MARKERS = {"sandbox_missing", "agent_browser_missing", "node_missing", "macos_capability_missing"}
AUTH_GAP_MARKERS = {"sso_ticket_expired", "auth_failed", "login_page", "access_proxy_redirect"}
TOOL_GAP_MARKERS = {"tool_unavailable", "safe_bin_missing", "browser_profile_lock"}
CREDENTIAL_REF_TYPES = {"token", "session", "cookie", "header", "password", "authorization", "api_key"}
MASKED_VALUE_MARKERS = {"*", "redacted", "masked", "<", ">", "xxx", "****"}
FORBIDDEN_CASE_EXECUTION_MARKERS = {
    ".ks_sso/sso-state.json": "NO-COOKIE-STATE-READ-DURING-CASE-001",
    "manual_cookie": "NO-MANUAL-COOKIE-CURL-001",
    "curl_cookie": "NO-MANUAL-COOKIE-CURL-001",
    "C" + "ookie:": "NO-MANUAL-COOKIE-CURL-001",
    "H" + "eader:": "NO-MANUAL-COOKIE-CURL-001",
    "urllib": "NO-MANUAL-COOKIE-CURL-001",
    "curl ": "NO-MANUAL-COOKIE-CURL-001",
    "requests_with_cookie": "NO-MANUAL-COOKIE-CURL-001",
    "SmartSSOSession": "NO-RUNNER-DEBUG-DURING-CASE-001",
    "sso_session_runner.py": "NO-RUNNER-DEBUG-DURING-CASE-001",
    "sso_session.py": "NO-RUNNER-DEBUG-DURING-CASE-001",
    "auth_bridge_implementation": "NO-RUNNER-DEBUG-DURING-CASE-001",
}
REFERENCE_TYPES_REQUIRING_RAW_SAFE_ID = {
    "user_id",
    "device_id",
    "event_id",
    "source_id",
    "policy_code",
    "ip",
}


def load_plan() -> dict[str, Any]:
    try:
        return json.loads(PLAN_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SystemExit("source orchestration plan missing")
    except json.JSONDecodeError as exc:
        raise SystemExit(f"source orchestration plan must be JSON-compatible YAML: {exc}")


def parse_matrix(raw: str | None) -> list[dict[str, Any]]:
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"source_completion_matrix must be JSON: {exc}")
    if not isinstance(data, list):
        raise SystemExit("source_completion_matrix must be a JSON list")
    for item in data:
        if not isinstance(item, dict):
            raise SystemExit("source_completion_matrix entries must be objects")
    return data


def parse_passthrough_envelope(raw: str | None) -> dict[str, Any] | None:
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"passthrough_envelope must be JSON: {exc}")
    if not isinstance(data, dict):
        raise SystemExit("passthrough_envelope must be a JSON object")
    return data


def classify_passthrough_source(envelope: dict[str, Any]) -> str:
    try:
        http_status = int(envelope.get("http_status")) if envelope.get("http_status") not in {None, ""} else None
    except (TypeError, ValueError):
        http_status = None
    if http_status is not None and 200 <= http_status < 300 and envelope.get("body_present") is True and envelope.get("body_truncated") is True:
        return "partial"
    if http_status is not None and 200 <= http_status < 300 and envelope.get("body_present") is True:
        return "completed"
    if envelope.get("timeout") is True:
        return "timeout"
    if (
        envelope.get("auth_redirect_detected") is True
        or str(envelope.get("api_code")) == "302"
        or http_status in {302, 401, 403}
    ):
        return "auth_failed"
    if envelope.get("invalid_params"):
        return "blocked"
    if envelope.get("transport_error") or envelope.get("platform_error"):
        return "blocked"
    if envelope.get("body_truncated") is True:
        return "partial"
    if str(envelope.get("raw_body_handling", "")) in {"suppressed", "capped", "metadata_only"}:
        return "completed"
    if envelope.get("body_present") is False:
        return "no_data"
    return "completed"


def validate_passthrough_envelope(envelope: dict[str, Any] | None) -> tuple[list[dict[str, str]], dict[str, Any]]:
    if envelope is None:
        return [], {}
    failures: list[dict[str, str]] = []
    missing_fields = sorted(field for field in PASSTHROUGH_ENVELOPE_REQUIRED_FIELDS if field not in envelope)
    if missing_fields:
        failures.append(
            {
                "rule": "passthrough_envelope_required_fields",
                "reason": f"passthrough envelope missing fields {missing_fields}",
            }
        )
    legacy_fields_present = sorted(field for field in LEGACY_SERVICE_BUSINESS_FIELDS if field in envelope)
    if legacy_fields_present:
        failures.append(
            {
                "rule": "service_must_not_emit_legacy_business_fields",
                "reason": f"pure passthrough envelope must not require or emit service business fields {legacy_fields_present}",
            }
        )
    if str(envelope.get("raw_body_handling", "")) not in {"suppressed", "capped", "metadata_only"}:
        failures.append(
            {
                "rule": "raw_body_handling_required",
                "reason": "raw_body_handling must be suppressed, capped, or metadata_only",
            }
        )
    status = classify_passthrough_source(envelope)
    generated = {
        "dennis_generated_status": status,
        "source_quality_bucket": status,
        "partial_observation_available": envelope.get("body_truncated") is True,
        "auth_flow_not_completed_in_bound_context": (
            envelope.get("auth_redirect_detected") is True
            or str(envelope.get("api_code")) == "302"
            or str(envelope.get("http_status")) == "302"
        ),
        "raw_body_limited_observation_only": str(envelope.get("raw_body_handling", "")) in {"suppressed", "capped", "metadata_only"},
        "missing_evidence_required": status in {"timeout", "auth_failed", "blocked", "parse_error", "no_data"},
    }
    return failures, generated


def select_plan(plan: dict[str, Any], task_type: str, entity_count: int) -> dict[str, Any] | None:
    for candidate in plan.get("plans", {}).values():
        applies_to = {str(item).lower() for item in candidate.get("applies_to", [])}
        entity_range = candidate.get("entity_count", {})
        if (
            task_type.lower() in applies_to
            and int(entity_range.get("min", 0)) <= entity_count <= int(entity_range.get("max", 0))
        ):
            return candidate
    return None


def validate_static_plan_contract(plan: dict[str, Any]) -> list[dict[str, str]]:
    failures: list[dict[str, str]] = []
    universal = plan.get("plans", {}).get("universal_realtime_first_risk_workflow_v1", {})
    fixed = plan.get("plans", {}).get("browser_backed_fixed_actions_v1", {})
    batch_ato = plan.get("plans", {}).get("batch_ato_cluster_lens_alignment_v1", {})
    batch_contract = fixed.get("controlled_parallel_batch_contract", {})
    required_fields = batch_contract.get("source_plan_item_required_fields", [])

    if not universal:
        failures.append(
            {
                "rule": "universal_realtime_first_workflow_required",
                "reason": "source plan must register the generic realtime-first/offline-supplement/clusterable risk workflow",
            }
        )
    else:
        if universal.get("default_runtime_routing") is not False:
            failures.append(
                {
                    "rule": "universal_workflow_default_runtime_routing_false_required",
                    "reason": "universal workflow is an orchestration contract and must keep default_runtime_routing=false",
                }
            )
        workflow = set(universal.get("workflow", []))
        missing_workflow_steps = sorted(UNIVERSAL_WORKFLOW_REQUIRED_STEPS - workflow)
        if missing_workflow_steps:
            failures.append(
                {
                    "rule": "universal_realtime_first_workflow_steps_required",
                    "reason": f"universal workflow missing steps {missing_workflow_steps}",
                }
            )
        required_outputs = set(universal.get("required_outputs", []))
        if not {"source_plan", "evidence_chain", "source_quality_matrix", "missing_evidence", "final_answer_boundary"}.issubset(required_outputs):
            failures.append(
                {
                    "rule": "universal_workflow_required_outputs",
                    "reason": "universal workflow must require source_plan/evidence_chain/source_quality_matrix/missing_evidence/final_answer_boundary",
                }
            )
        offline_scenes = set(universal.get("offline_supplement_by_risk_scene", {}).keys())
        missing_offline_scenes = sorted(UNIVERSAL_OFFLINE_SCENES - offline_scenes)
        if missing_offline_scenes:
            failures.append(
                {
                    "rule": "offline_supplement_by_risk_scene_required",
                    "reason": f"offline supplement plan must cover generic risk scenes {missing_offline_scenes}, not only ATO login Hive",
                }
            )
        auth_boundary = universal.get("authorization_boundary", {})
        if auth_boundary.get("dataagent_hive_requires_per_request_authorization") is not True or auth_boundary.get("previous_authorization_not_reusable") is not True:
            failures.append(
                {
                    "rule": "dataagent_hive_per_request_authorization_required",
                    "reason": "DataAgent/Hive execution must require explicit per-request authorization in the universal workflow",
                }
            )

    if fixed.get("default_runtime_routing") is not False:
        failures.append(
            {
                "rule": "default_runtime_routing_false_required",
                "reason": "browser_backed_fixed_actions_v1 must keep default_runtime_routing=false",
            }
        )
    for action_name, action in fixed.get("registered_actions", {}).items():
        if action.get("default_runtime_routing") is not False:
            failures.append(
                {
                    "rule": "default_runtime_routing_false_required",
                    "reason": f"registered action {action_name} must keep default_runtime_routing=false",
                }
            )

    for endpoint_key in ["service_batch_endpoint", "service_plan_endpoint"]:
        if not str(batch_contract.get(endpoint_key, "")).startswith("/actions/"):
            failures.append(
                {
                    "rule": "controlled_parallel_batch_contract_required",
                    "reason": f"controlled parallel contract missing {endpoint_key}",
                }
            )

    if batch_contract.get("service_output_mode") != "pure_passthrough_transport_envelope":
        failures.append(
            {
                "rule": "pure_passthrough_output_mode_required",
                "reason": "browser-backed service contract must be pure passthrough transport envelope, not service-side normalized observation",
            }
        )
    envelope_fields = set(batch_contract.get("service_single_source_envelope_fields", []))
    missing_envelope = sorted(PASSTHROUGH_ENVELOPE_REQUIRED_FIELDS - envelope_fields)
    if missing_envelope:
        failures.append(
            {
                "rule": "passthrough_envelope_fields_required",
                "reason": f"passthrough envelope missing required fields {missing_envelope}",
            }
        )
    batch_output_fields = set(batch_contract.get("service_batch_output_fields", []))
    missing_batch_fields = sorted(PASSTHROUGH_BATCH_REQUIRED_FIELDS - batch_output_fields)
    if missing_batch_fields:
        failures.append(
            {
                "rule": "passthrough_batch_fields_required",
                "reason": f"batch passthrough output missing required fields {missing_batch_fields}",
            }
        )
    legacy_not_required = set(batch_contract.get("service_legacy_business_fields_not_required", []))
    missing_legacy_markers = sorted(LEGACY_SERVICE_BUSINESS_FIELDS - legacy_not_required)
    if missing_legacy_markers:
        failures.append(
            {
                "rule": "legacy_service_business_fields_not_required",
                "reason": f"pure passthrough contract must explicitly remove service dependency on {missing_legacy_markers}",
            }
        )
    dennis_generated = set(batch_contract.get("dennis_generated_fields", []))
    missing_dennis_generated = sorted(DENNIS_GENERATED_PASSTHROUGH_FIELDS - dennis_generated)
    if missing_dennis_generated:
        failures.append(
            {
                "rule": "dennis_generated_passthrough_fields_required",
                "reason": f"Dennis must generate passthrough-derived fields {missing_dennis_generated}",
            }
        )

    supported_groups = set(batch_contract.get("execution_groups_supported", []))
    if not CONTROLLED_PARALLEL_EXECUTION_GROUPS.issubset(supported_groups):
        failures.append(
            {
                "rule": "controlled_parallel_execution_groups_missing",
                "reason": "controlled parallel contract must list all supported execution groups",
            }
        )
    if batch_contract.get("manual_local_actions_batch_curl_fallback_allowed") is not False:
        failures.append(
            {
                "rule": "manual_local_batch_curl_fallback_forbidden",
                "reason": "case execution must not fall back to manual curl /actions/batch after harness failure",
            }
        )
    if "harness_error" not in str(batch_contract.get("harness_error_policy", "")):
        failures.append(
            {
                "rule": "structured_harness_error_policy_required",
                "reason": "harness failure must return structured harness_error/source_gap",
            }
        )
    merge_contract = batch_contract.get("merge_contract", {})
    service_merge_fields = set(merge_contract.get("service_output_fields", []))
    if {"source_quality_matrix", "evidence_card_inputs", "evidence_card", "missing_evidence"} & service_merge_fields:
        failures.append(
            {
                "rule": "service_merge_must_not_require_dennis_business_fields",
                "reason": "service merge output must be transport_status_matrix/source_results only; Dennis generates quality, evidence card and missing evidence",
            }
        )
    dennis_merge_fields = set(merge_contract.get("dennis_generated_fields", []))
    if not {"source_quality_matrix", "evidence_card", "missing_evidence"}.issubset(dennis_merge_fields):
        failures.append(
            {
                "rule": "dennis_merge_fields_required",
                "reason": "Dennis merge contract must generate source_quality_matrix, evidence_card and missing_evidence from passthrough batch output",
            }
        )

    for scenario_name, scenario in fixed.get("scenario_source_plans", {}).items():
        source_plan = scenario.get("source_plan", [])
        if not isinstance(source_plan, list) or not source_plan:
            failures.append(
                {
                    "rule": "source_plan_items_required",
                    "reason": f"scenario {scenario_name} must define source_plan items",
                }
            )
            continue
        actions = set(scenario.get("actions", []))
        item_actions = {str(item.get("action")) for item in source_plan if isinstance(item, dict)}
        if actions and not actions.issubset(item_actions):
            failures.append(
                {
                    "rule": "source_plan_actions_mismatch",
                    "reason": f"scenario {scenario_name} source_plan missing actions {sorted(actions - item_actions)}",
                }
            )
        for idx, item in enumerate(source_plan):
            if not isinstance(item, dict):
                failures.append(
                    {
                        "rule": "source_plan_item_shape",
                        "reason": f"scenario {scenario_name} item {idx} must be an object",
                    }
                )
                continue
            for field in required_fields:
                if field not in item:
                    failures.append(
                        {
                            "rule": "source_plan_item_required_fields",
                            "reason": f"scenario {scenario_name} item {idx} missing {field}",
                        }
                    )
            execution_group = str(item.get("execution_group", ""))
            if execution_group and execution_group not in CONTROLLED_PARALLEL_EXECUTION_GROUPS:
                failures.append(
                    {
                        "rule": "source_plan_execution_group_unknown",
                        "reason": f"scenario {scenario_name} item {idx} uses unknown execution_group {execution_group}",
                    }
                )
            if not isinstance(item.get("depends_on", []), list):
                failures.append(
                    {
                        "rule": "source_plan_depends_on_list_required",
                        "reason": f"scenario {scenario_name} item {idx} depends_on must be a list",
                    }
                )

        if scenario_name == "ato_login_anomaly":
            item_actions = {str(item.get("action")) for item in source_plan if isinstance(item, dict)}
            missing_actions = sorted(ATO_REALTIME_P0_REQUIRED_ACTIONS - item_actions)
            if missing_actions:
                failures.append(
                    {
                        "rule": "ato_single_case_realtime_p0_plan_required",
                        "reason": f"ATO source_plan missing realtime P0 actions {missing_actions}",
                    }
                )
            missing_window_policy = [
                str(item.get("source_id") or item.get("action"))
                for item in source_plan
                if isinstance(item, dict)
                and str(item.get("action")) in ATO_REALTIME_P0_REQUIRED_ACTIONS
                and not item.get("window_policy")
            ]
            if missing_window_policy:
                failures.append(
                    {
                        "rule": "ato_source_specific_window_policy_required",
                        "reason": f"ATO realtime P0 source_plan items missing window_policy {missing_window_policy}",
                    }
                )
            track_items = [
                item
                for item in source_plan
                if isinstance(item, dict) and item.get("action") == "track_analysis_check_data_ready"
            ]
            if not track_items or "candidate_device" not in str(track_items[0].get("device_id_policy", "")):
                failures.append(
                    {
                        "rule": "ato_track_candidate_device_policy_required",
                        "reason": "Track checkDataReady must use provided or prior-source candidate device_id, and missing device_id must not fail the batch",
                    }
                )
            if (
                scenario.get("first_step") != "realtime_p0_source_collection"
                or scenario.get("anchor_discovery_mode") != "derive_suspicious_anchor_from_realtime_p0_sources"
                or scenario.get("standalone_suspicious_anchor_source_forbidden") is not True
            ):
                failures.append(
                    {
                        "rule": "ato_single_case_realtime_p0_anchor_derivation_required",
                        "reason": "ATO scenario must derive suspicious anchors from realtime P0 sources, not a standalone source action",
                    }
                )
            primary_chain = set(scenario.get("primary_brain_chain", []))
            if "user_device_entity_resolution" not in primary_chain:
                failures.append(
                    {
                        "rule": "ato_user_device_entity_resolution_required",
                        "reason": "ATO primary brain chain must include user_device_entity_resolution before device/Track/Weapon alignment",
                    }
                )
            entity_contract = scenario.get("user_device_entity_resolution_contract", {})
            entity_sources = set(entity_contract.get("candidate_device_sources", []))
            if (
                entity_contract.get("default_p0_entity_layer") is not True
                or entity_contract.get("not_final_risk_conclusion_source") is not True
                or not ATO_USER_DEVICE_ENTITY_SOURCES.issubset(entity_sources)
                or "candidate_device_id_missing" not in str(entity_contract.get("missing_candidate_device_rule", ""))
            ):
                failures.append(
                    {
                        "rule": "ato_user_device_entity_resolution_contract_required",
                        "reason": "ATO must resolve candidate devices from login/archives/photo/weapon/Track and treat missing candidate_device_id as missing_evidence, not batch failure",
                    }
                )
            identity_fields = set(
                scenario.get("device_identity_consistency_contract", {}).get("identity_fields", [])
            )
            expected_identity_markers = {
                "device_model_consistency",
                "os_consistency",
                "UA_consistency",
                "IP_province_city_ASN_consistency",
                "login_source_consistency",
                "login_type_consistency",
            }
            if not expected_identity_markers.issubset(identity_fields):
                failures.append(
                    {
                        "rule": "device_identity_consistency_fields_required",
                        "reason": "ATO device identity consistency must cover model/os/UA/IP/login_source/login_type",
                    }
                )
            interpretation = scenario.get("source_observation_interpretation_contract", {})
            interpretation_sources = interpretation.get("sources", {})
            required_interpretation_sources = {
                "login_logs_search",
                "archives_user_analysis",
                "archives_photo_search",
                "track_analysis_check_data_ready",
                "archives_related_users",
                "weapon_inventory",
                "rcp_event_feature_list",
                "rcp_policy_tree_lookup",
            }
            if (
                interpretation.get("completed_transport_not_business_chain_closure") is not True
                or not required_interpretation_sources.issubset(set(interpretation_sources.keys()))
                or "partial_observation_available" not in str(interpretation_sources.get("login_logs_search", {}))
                or "content_chain_business_fields_missing" not in str(interpretation_sources.get("archives_photo_search", {}))
                or "behavior_chain_business_fields_missing" not in str(interpretation_sources.get("archives_user_analysis", {}))
            ):
                failures.append(
                    {
                        "rule": "ato_source_observation_interpretation_contract_required",
                        "reason": "ATO passthrough interpretation must distinguish transport status from business closure and cover login/photo/analysis/Track/related/Weapon/RCP boundaries",
                    }
                )
            evidence_card_contract = scenario.get("evidence_card_chain_contract", {})
            evidence_sections = set(evidence_card_contract.get("required_sections", []))
            if (
                evidence_card_contract.get("organization") != "ato_risk_chain_not_flat_source_status"
                or not ATO_EVIDENCE_CHAIN_SECTIONS.issubset(evidence_sections)
                or "offline_backfill_recommendation" not in str(evidence_card_contract.get("insufficient_support_rule", ""))
            ):
                failures.append(
                    {
                        "rule": "ato_chain_evidence_card_contract_required",
                        "reason": "ATO evidence card must be organized by risk chain and include offline backfill recommendation when realtime evidence is incomplete",
                    }
                )
            login_patch = scenario.get("login_logs_search_contract_patch", {})
            if login_patch.get("response_too_large_status") != "source_contract_gap" or login_patch.get("response_too_large_not_login_evidence") is not True:
                failures.append(
                    {
                        "rule": "login_response_too_large_not_evidence",
                        "reason": "ATO login_logs_search must classify response_too_large as source_contract_gap, not login evidence",
                    }
                )
            hive_preflight = scenario.get("offline_hive_registry_preflight", {})
            if hive_preflight.get("required_before_dataagent_or_hive") is not True or "account_security_hive_source_registry_v1.md" not in str(hive_preflight.get("registry", "")):
                failures.append(
                    {
                        "rule": "ato_hive_registry_first_required",
                        "reason": "ATO Hive/DataAgent plan must reference account_security_hive_source_registry_v1.md before execution",
                    }
                )
            realtime_incomplete = scenario.get("realtime_source_incomplete_hive_required_contract", {})
            if realtime_incomplete.get("offline_hive_required_when_realtime_incomplete") is not True or realtime_incomplete.get("hive_required_hint") is not True:
                failures.append(
                    {
                        "rule": "ato_realtime_incomplete_hive_required_contract",
                        "reason": "ATO single-case plan must strongly require Hive hint when realtime sources are incomplete",
                    }
                )
            required_gap_flags = set(realtime_incomplete.get("required_gap_flags", []))
            if not ATO_REALTIME_INCOMPLETE_REQUIRED_FLAGS.issubset(required_gap_flags):
                failures.append(
                    {
                        "rule": "ato_realtime_incomplete_gap_flags_required",
                        "reason": "ATO realtime incomplete contract must require login window, admin APP-only, WEB control-chain and offline Hive flags",
                    }
                )
            offline_auth = scenario.get("offline_backfill_dynamic_authorization_contract", {})
            module_ids = {
                str(item.get("module_id"))
                for item in offline_auth.get("dynamic_module_catalog", [])
                if isinstance(item, dict) and item.get("module_id")
            }
            if (
                offline_auth.get("authorization_required") is not True
                or offline_auth.get("one_time_full_authorization_forbidden") is not True
                or offline_auth.get("previous_authorization_not_reusable") is not True
                or offline_auth.get("fixed_1_to_5_menu_forbidden") is not True
                or offline_auth.get("unselected_modules_enter_missing_evidence") is not True
                or offline_auth.get("dataagent_or_hive_call_without_module_authorization_allowed") is not False
                or not ATO_DYNAMIC_OFFLINE_MODULE_IDS.issubset(module_ids)
            ):
                failures.append(
                    {
                        "rule": "ato_offline_backfill_dynamic_authorization_required",
                        "reason": "ATO offline backfill must dynamically generate modules from current gaps and forbid DataAgent/Hive execution outside explicit module authorization",
                    }
                )

    if not batch_ato:
        failures.append(
            {
                "rule": "batch_ato_cluster_lens_plan_required",
                "reason": "source plan must include batch_ato_cluster_lens_alignment_v1",
            }
        )
    else:
        if batch_ato.get("default_runtime_routing") is not False:
            failures.append(
                {
                    "rule": "batch_ato_default_runtime_routing_false_required",
                    "reason": "batch ATO lens must keep default_runtime_routing=false",
                }
            )
        if batch_ato.get("real_platform_access") is not False or batch_ato.get("dataagent_hive_execution") is not False:
            failures.append(
                {
                    "rule": "batch_ato_plan_only_boundary_required",
                    "reason": "batch ATO lens is local planning/validation only and must not execute platforms or DataAgent/Hive",
                }
            )
        workflow = set(batch_ato.get("workflow", []))
        missing_steps = sorted(BATCH_ATO_REQUIRED_PLAN_STEPS - workflow)
        if missing_steps:
            failures.append(
                {
                    "rule": "batch_ato_workflow_steps_required",
                    "reason": f"batch ATO lens workflow missing {missing_steps}",
                }
            )
        labels = set(batch_ato.get("lens_output_labels", []))
        missing_labels = sorted(BATCH_ATO_REQUIRED_LABELS - labels)
        if missing_labels:
            failures.append(
                {
                    "rule": "batch_ato_lens_labels_required",
                    "reason": f"batch ATO lens output labels missing {missing_labels}",
                }
            )
        signal_registry = batch_ato.get("ato_account_takeover_cluster_signal_registry", {})
        missing_signal_dimensions = sorted(ATO_CLUSTER_SIGNAL_DIMENSIONS - set(signal_registry.keys()))
        if missing_signal_dimensions:
            failures.append(
                {
                    "rule": "ato_account_takeover_cluster_signal_registry_required",
                    "reason": f"batch ATO cluster lens must register signal dimensions {missing_signal_dimensions}",
                }
            )
        registry_output_fields = set(signal_registry.get("required_output_fields", []))
        if not {"cluster_key", "shared_features", "representative_users", "strong_evidence", "weak_evidence", "counter_evidence", "missing_evidence"}.issubset(registry_output_fields):
            failures.append(
                {
                    "rule": "ato_cluster_output_fields_required",
                    "reason": "ATO cluster signal registry must require cluster_key/shared_features/representative_users/evidence buckets/missing_evidence",
                }
            )
        hive_preflight = batch_ato.get("hive_registry_preflight", {})
        if hive_preflight.get("required_before_dataagent_or_hive") is not True or "account_security_hive_source_registry_v1.md" not in str(hive_preflight.get("registry", "")):
            failures.append(
                {
                    "rule": "batch_ato_hive_registry_first_required",
                    "reason": "batch ATO long-window login query plan must reference account-security Hive registry first",
                }
            )
        realtime_incomplete = batch_ato.get("realtime_source_incomplete_hive_required_contract", {})
        if realtime_incomplete.get("offline_hive_required_when_realtime_incomplete") is not True or realtime_incomplete.get("hive_required_hint") is not True:
            failures.append(
                {
                    "rule": "batch_ato_realtime_incomplete_hive_required_contract",
                    "reason": "batch ATO plan must strongly require Hive hint when realtime sources are incomplete",
                }
            )
        required_gap_flags = set(realtime_incomplete.get("required_gap_flags", []))
        if not ATO_REALTIME_INCOMPLETE_REQUIRED_FLAGS.issubset(required_gap_flags):
            failures.append(
                {
                    "rule": "batch_ato_realtime_incomplete_gap_flags_required",
                    "reason": "batch ATO realtime incomplete contract must require login window, admin APP-only, WEB control-chain and offline Hive flags",
                }
            )
        stop_conditions = batch_ato.get("stop_conditions", {})
        if stop_conditions.get("allow_per_user_online_loop_by_default") is not False or stop_conditions.get("allow_global_ato_conclusion_from_representative_only") is not False:
            failures.append(
                {
                    "rule": "batch_ato_no_for_loop_or_global_proof_required",
                    "reason": "batch ATO lens must forbid default per-user online loop and representative-as-global-proof drift",
                }
            )

    return failures


def source_names(matrix: list[dict[str, Any]]) -> set[str]:
    return {str(item.get("source_name", "")) for item in matrix}


def endpoint_for(matrix: list[dict[str, Any]], source_name: str) -> str:
    for item in matrix:
        if item.get("source_name") == source_name:
            passthrough = item.get("passthrough_envelope", {})
            passthrough_path = passthrough.get("path", "") if isinstance(passthrough, dict) else ""
            return str(item.get("endpoint", "") or item.get("path", "") or item.get("api_path", "") or passthrough_path)
    return ""


def as_bool(value: Any) -> bool:
    return value is True or str(value).lower() == "true"


def looks_masked(value: Any) -> bool:
    text = str(value or "").lower()
    return any(marker in text for marker in MASKED_VALUE_MARKERS)


def raw_references(item: dict[str, Any]) -> list[dict[str, Any]]:
    refs = item.get("raw_references", [])
    if isinstance(refs, list):
        return [ref for ref in refs if isinstance(ref, dict)]
    return []


def has_raw_reference(item: dict[str, Any], ref_type: str) -> bool:
    for ref in raw_references(item):
        if str(ref.get("ref_type")) == ref_type and ref.get("raw_reference_safe_id") and ref.get("retention_scope", "current_task_only") == "current_task_only":
            return True
    return False


def redaction_block(item: dict[str, Any]) -> dict[str, Any]:
    value = item.get("redaction", {})
    return value if isinstance(value, dict) else {}


def source_quality_block(item: dict[str, Any]) -> dict[str, Any]:
    value = item.get("dennis_generated_source_quality", {})
    return value if isinstance(value, dict) else {}


def is_browser_backed_item(item: dict[str, Any]) -> bool:
    action_name = str(item.get("action_name", ""))
    return (
        item.get("access_method") == "browser_backed_service"
        or item.get("source_provenance") == "browser_backed_service"
        or action_name in FIXED_BROWSER_BACKED_ACTIONS
        or action_name in LEGACY_BROWSER_BACKED_ACTIONS
    )


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def serialized_item(item: dict[str, Any]) -> str:
    return json.dumps(item, ensure_ascii=False, sort_keys=True)


def is_registered_endpoint(endpoint: str) -> bool:
    registered_fragments = {
        "/apiv2/graphData",
        "/apiv2/riskData",
        "/dp/platform/app/analytics/v2/sequence/getLastestDateTime",
        "/dp/platform/app/analytics/v2/sequence/getDeviceIds",
        "/dp/platform/app/analytics/v2/sequence/getUseDuration",
        "/dp/platform/app/analytics/v2/sequence/profile",
        "/actions/login_logs_search",
        "/actions/weapon_inventory",
        "/actions/track_analysis_summary",
        "/actions/rcp_snapshot",
        "/actions/track_analysis_check_data_ready",
        "/actions/archives_user_profile",
        "/actions/archives_user_analysis",
        "/actions/archives_photo_search",
        "/actions/archives_related_users",
        "/actions/rcp_event_detail",
        "/actions/rcp_event_feature_list",
        "/actions/rcp_policy_tree_lookup",
    }
    return any(fragment in endpoint for fragment in registered_fragments)


def validate_matrix(
    selected_plan: dict[str, Any],
    matrix: list[dict[str, Any]],
    *,
    no_cache: bool,
    final_conclusion: str | None,
) -> list[dict[str, str]]:
    failures: list[dict[str, str]] = []
    required_fields = selected_plan.get("source_completion_matrix_required_fields", [])
    names = source_names(matrix)

    if not matrix:
        failures.append(
            {
                "rule": "source_completion_matrix_required",
                "reason": "final evidence mode requires a source_completion_matrix",
            }
        )
        return failures

    for idx, item in enumerate(matrix):
        source_status = str(item.get("source_status", ""))
        for field in required_fields:
            if field not in item:
                failures.append(
                    {
                        "rule": "source_completion_matrix_required_fields",
                        "reason": f"entry {idx} missing required field {field}",
                    }
                )
        redaction = redaction_block(item)
        quality = source_quality_block(item)
        for key, expected in {
            "redaction_applied": True,
            "sensitive_output": False,
        }.items():
            top_level_value = item.get(key)
            browser_backed_redaction_ok = (
                key == "redaction_applied"
                and is_browser_backed_item(item)
                and item.get("sensitive_output") is False
                and (item.get("passthrough_envelope") is not None or item.get("dennis_generated_source_quality") is not None)
            )
            if redaction.get(key) is not expected and quality.get(key) is not expected and top_level_value is not expected and not browser_backed_redaction_ok:
                failures.append(
                    {
                        "rule": "raw_reference_redaction_layering",
                        "reason": f"entry {idx} missing {key}={str(expected).lower()} in redaction/source_quality",
                    }
                )
        if quality.get("provenance") != "current_task_observation" and item.get("source_provenance") not in {"current_task_observation", "realtime", "browser_backed_service"}:
            failures.append(
                {
                    "rule": "raw_reference_redaction_layering",
                    "reason": f"entry {idx} must mark provenance=current_task_observation or current realtime observation",
                }
            )
        retained_flag = redaction.get("raw_reference_retained_for_followup", quality.get("raw_reference_retained_for_followup"))
        if retained_flag not in {True, False} and not is_browser_backed_item(item):
            failures.append(
                {
                    "rule": "raw_reference_redaction_layering",
                    "reason": f"entry {idx} must declare raw_reference_retained_for_followup true/false",
                }
            )
        for ref_idx, ref in enumerate(raw_references(item)):
            ref_type = str(ref.get("ref_type", ""))
            if ref_type in CREDENTIAL_REF_TYPES:
                failures.append(
                    {
                        "rule": "credential_reference_forbidden",
                        "reason": f"entry {idx} raw_references[{ref_idx}] contains forbidden credential ref_type {ref_type}",
                    }
                )
            if ref_type in REFERENCE_TYPES_REQUIRING_RAW_SAFE_ID and not ref.get("raw_reference_safe_id"):
                failures.append(
                    {
                        "rule": "raw_reference_safe_id_required",
                        "reason": f"entry {idx} raw_references[{ref_idx}] missing raw_reference_safe_id for {ref_type}",
                    }
                )
            if ref.get("masked_value") and ref.get("raw_reference_safe_id") == ref.get("masked_value"):
                failures.append(
                    {
                        "rule": "masked_value_used_as_raw_reference",
                        "reason": f"entry {idx} raw_references[{ref_idx}] uses masked_value as raw_reference_safe_id",
                    }
                )
        access_method = str(item.get("access_method", ""))
        if access_method in FORBIDDEN_ACCESS_METHODS:
            failures.append(
                {
                    "rule": "forbidden_tool_boundary_drift",
                    "reason": f"entry {idx} uses forbidden access_method {access_method}",
                }
            )
        if item.get("write_edit_attempted") is True:
            failures.append(
                {
                    "rule": "write_edit_tool_boundary_drift",
                    "reason": f"entry {idx} attempted write/edit during readonly source execution",
                }
            )
        if no_cache and (item.get("stale_source") is True or str(item.get("source_provenance", "")).lower() in {"cache", "cached", "historical_observation"}):
            failures.append(
                {
                    "rule": "stale_data_drift",
                    "reason": f"entry {idx} uses stale/cached provenance during no-cache execution",
                }
            )
        if item.get("source_status") == "completed":
            if item.get("http_status") not in (None, 200):
                failures.append(
                    {
                        "rule": "completed_requires_http_200_if_http_status_present",
                        "reason": f"entry {idx} completed with non-200 http_status",
                    }
                )
            if not is_browser_backed_item(item) and item.get("response_type") not in (None, "json", "structured_json"):
                failures.append(
                    {
                        "rule": "completed_requires_structured_json_if_response_type_present",
                        "reason": f"entry {idx} completed with non-json response_type",
                    }
                )
        if item.get("source_status_before_refresh") in {"auth_failed", "http_redirect", "html_login"} and item.get("auth_refresh_attempted") is not True:
            failures.append(
                {
                    "rule": "auth_failed_requires_refresh_retry",
                    "reason": f"entry {idx} auth failed before refresh but did not attempt controlled refresh",
                }
            )
        item_text = serialized_item(item)
        for marker, case_id in FORBIDDEN_CASE_EXECUTION_MARKERS.items():
            if marker in item_text:
                failures.append(
                    {
                        "rule": "source_execution_guard_forbidden_case_debug",
                        "case_id": case_id,
                        "reason": f"entry {idx} contains forbidden case-execution marker {marker}",
                    }
                )
        for flag in [
            "read_cookie_state",
            "manual_cookie_constructed",
            "manual_header_constructed",
            "curl_cookie_attempted",
            "urllib_cookie_attempted",
            "requests_cookie_attempted",
            "smart_sso_debug_attempted",
            "runner_debug_attempted",
            "auth_bridge_inspected",
            "live_auth_repair_attempted",
        ]:
            if item.get(flag) is True:
                failures.append(
                    {
                        "rule": "source_execution_guard_forbidden_case_debug",
                        "reason": f"entry {idx} sets forbidden case-execution flag {flag}=true",
                    }
                )
        primary_attempts = as_list(item.get("primary_path_attempts", item.get("primary_paths_attempted")))
        fallback_attempts = as_list(item.get("fallback_path_attempts", item.get("fallback_paths_attempted")))
        all_attempts = as_list(item.get("source_path_attempts", item.get("attempted_paths")))
        if len(primary_attempts) > 1 or len(fallback_attempts) > 1 or (all_attempts and len(all_attempts) > 2):
            failures.append(
                {
                    "rule": "source_attempt_limit",
                    "case_id": "SOURCE-ATTEMPT-LIMIT-001",
                    "reason": f"entry {idx} exceeds one primary path and one fallback path per source",
                }
            )
        if source_status in {"tool_gap", "auth_bridge_gap"}:
            if not quality:
                failures.append(
                    {
                        "rule": "runner_unavailable_tool_gap",
                        "case_id": "RUNNER-UNAVAILABLE-TOOL-GAP-001",
                        "reason": f"entry {idx} source_status={source_status} must include source_quality",
                    }
                )
            if item.get("continued_next_source") is False:
                failures.append(
                    {
                        "rule": "partial_evidence_card_on_source_failure",
                        "case_id": "PARTIAL-EVIDENCE-CARD-ON-SOURCE-FAILURE-001",
                        "reason": f"entry {idx} source failure must continue to next source or partial evidence card",
                    }
                )

    if names == {"user_login_unified_log"}:
        failures.append(
            {
                "rule": "login_log_only_cannot_conclude",
                "reason": "login log only is not enough for single-user account security / ATO judgement",
            }
        )

    required_sources = selected_plan.get("required_p0_sources", [])
    for source in required_sources:
        name = source.get("source_name")
        if name not in names:
            failures.append(
                {
                    "rule": "source_plan_not_executed",
                    "reason": f"planned required P0 source {name} missing from executed source matrix",
                }
            )
            continue
        required_path = source.get("required_path_contains")
        endpoint = endpoint_for(matrix, name)
        entry = next((item for item in matrix if item.get("source_name") == name), {})
        status = str(entry.get("source_status", ""))
        if required_path and required_path not in endpoint and status not in NON_ENDPOINT_STATUSES and not is_browser_backed_item(entry):
            failures.append(
                {
                    "rule": "required_p0_source_path_missing",
                    "reason": f"{name} must use endpoint containing {required_path}",
                }
            )
        if name == "weapon_user_to_device_graph":
            if is_browser_backed_item(entry):
                if entry.get("action_name") != "weapon_inventory":
                    failures.append(
                        {
                            "rule": "browser_backed_action_name_required",
                            "reason": "weapon_user_to_device_graph must use browser-backed action_name=weapon_inventory",
                        }
                    )
            elif FORBIDDEN_WEAPON_GRAPH_PATH in endpoint:
                failures.append(
                    {
                        "rule": "weapon_forbidden_api_graphdata_path",
                        "reason": "weapon_user_to_device_graph must not use /api/graphData",
                    }
                )
            if not is_browser_backed_item(entry):
                for marker in ["product=KUAISHOU", "productName=KUAISHOU", "groupKey=USER_ID", "dimKey=DEVICE_ID"]:
                    if marker not in endpoint:
                        failures.append(
                            {
                                "rule": "weapon_graphdata_query_shape_drift",
                                "reason": f"weapon_user_to_device_graph missing {marker}",
                            }
                        )
        if name == "weapon_device_risk_if_device_id_available":
            for marker in ["product=KUAISHOU", "deviceIds="]:
                if marker not in endpoint and status not in NON_ENDPOINT_STATUSES:
                    failures.append(
                        {
                            "rule": "weapon_riskdata_query_shape_drift",
                            "reason": f"weapon_device_risk missing {marker}",
                        }
                    )

    graph_entry = next((item for item in matrix if item.get("source_name") == "weapon_user_to_device_graph"), {})
    graph_empty = (
        graph_entry.get("source_status") == "no_data"
        or graph_entry.get("records_count") == 0
        or graph_entry.get("edges_count") == 0
    )

    for idx, item in enumerate(matrix):
        endpoint = endpoint_for(matrix, str(item.get("source_name", "")))
        source_name = str(item.get("source_name", ""))
        source_status = str(item.get("source_status", ""))
        device_id = str(item.get("device_id", ""))
        original_device_id = str(item.get("device_id_original", ""))
        if source_name in {source.get("source_name") for source in required_sources}:
            if source_status not in EXPLAINED_NOT_EXECUTED_STATUSES and not endpoint and source_name not in {"user_login_unified_log", "time_window_inference"} and not is_browser_backed_item(item):
                failures.append(
                    {
                        "rule": "source_plan_not_executed",
                        "reason": f"{source_name} lacks endpoint and lacks explicit blocked/auth_failed/not_checked/missing_required_fields explanation",
                    }
                )
        if source_status == "completed":
            if is_browser_backed_item(item):
                if not item.get("action_name"):
                    failures.append(
                        {
                            "rule": "browser_backed_action_name_required",
                            "reason": f"entry {idx} browser-backed completed source missing action_name",
                        }
                    )
                if item.get("sensitive_output") is not False and redaction_block(item).get("sensitive_output") is not False and source_quality_block(item).get("sensitive_output") is not False:
                    failures.append(
                        {
                            "rule": "browser_backed_sensitive_output_false_required",
                            "reason": f"entry {idx} browser-backed completed source missing sensitive_output=false",
                        }
                    )
            elif item.get("real_platform_request_executed") is not True:
                failures.append(
                    {
                        "rule": "source_status_mismatch",
                        "reason": f"entry {idx} is completed without real_platform_request_executed=true",
                    }
                )
            if item.get("http_status") != 200:
                failures.append(
                    {
                        "rule": "source_status_mismatch",
                        "reason": f"entry {idx} is completed without http_status=200",
                    }
                )
            if not is_browser_backed_item(item) and item.get("response_type") not in {"json", "structured_json"}:
                failures.append(
                    {
                        "rule": "source_status_mismatch",
                        "reason": f"entry {idx} is completed without response_type=json",
                    }
                )
            if not is_browser_backed_item(item) and item.get("execution_observation_id") in (None, ""):
                failures.append(
                    {
                        "rule": "capability_registry_overtrust",
                        "reason": f"entry {idx} is completed without current execution observation id",
                    }
                )
        if source_status == "no_data":
            if is_browser_backed_item(item):
                has_passthrough_or_local_quality = (
                    isinstance(item.get("passthrough_envelope"), dict)
                    or isinstance(item.get("dennis_generated_source_quality"), dict)
                )
                if item.get("http_status") not in (None, 200) or not has_passthrough_or_local_quality:
                    failures.append(
                        {
                            "rule": "source_status_mismatch",
                            "reason": f"entry {idx} browser-backed no_data must have passthrough envelope or Dennis-generated source quality and http_status absent or 200",
                        }
                    )
            elif item.get("http_status") != 200 or item.get("response_type") not in {"json", "structured_json"} or item.get("records_count") != 0:
                failures.append(
                    {
                        "rule": "source_status_mismatch",
                        "reason": f"entry {idx} no_data must have http_status=200, response_type=json, and records_count=0",
                    }
                )
        if source_status == "auth_failed":
            auth_type = str(item.get("auth_failure_type", ""))
            if item.get("http_status") != 302 and item.get("response_type") not in {"html", "login_page", "access_proxy_redirect"} and auth_type not in {"login_page", "access_proxy_redirect", "http_redirect"}:
                failures.append(
                    {
                        "rule": "source_status_mismatch",
                        "reason": f"entry {idx} auth_failed lacks 302/login_page/access_proxy_redirect evidence",
                    }
                )
        if as_bool(item.get("not_checked")) and source_status in {"completed", "skipped"}:
            failures.append(
                {
                    "rule": "source_status_mismatch",
                    "reason": f"entry {idx} not_checked cannot be labelled {source_status}",
                }
            )
        gap_type = str(item.get("source_gap_type", ""))
        gap_reason = str(item.get("gap_reason", ""))
        if gap_type == "platform_gap" and (gap_reason in ENVIRONMENT_GAP_MARKERS or gap_reason in TOOL_GAP_MARKERS or gap_reason in AUTH_GAP_MARKERS):
            failures.append(
                {
                    "rule": "environment_issue_as_platform_gap",
                    "reason": f"entry {idx} mislabels {gap_reason} as platform_gap",
                }
            )
        if source_status in {"blocked", "auth_failed", "timeout", "not_checked", "tool_gap", "auth_bridge_gap"} and gap_type == "":
            failures.append(
                {
                    "rule": "source_gap_type_required",
                    "reason": f"entry {idx} must classify source gap as platform_gap/environment_gap/auth_gap/tool_gap/source_gap",
                }
            )
        if endpoint and not is_registered_endpoint(endpoint) and str(item.get("task_type", "")) != "endpoint_discovery":
            failures.append(
                {
                    "rule": "manual_exploration_creep",
                    "reason": f"entry {idx} attempted unregistered endpoint outside endpoint_discovery",
                }
            )
        if item.get("unapproved_endpoint_attempts"):
            failures.append(
                {
                    "rule": "manual_exploration_creep",
                    "reason": f"entry {idx} contains unapproved_endpoint_attempts",
                }
            )
        if item.get("prefix_removed") is True:
            failures.append(
                {
                    "rule": "device_id_prefix_removed",
                    "reason": f"{source_name} removed a device id prefix before source execution",
                }
            )
        if original_device_id.startswith(("ANDROID_", "IOS_")) and device_id and device_id != original_device_id:
            failures.append(
                {
                    "rule": "device_id_prefix_not_preserved",
                    "reason": f"{source_name} changed prefixed device id {original_device_id}",
                }
            )
        if source_name == "weapon_device_risk_if_device_id_available":
            if looks_masked(device_id):
                failures.append(
                    {
                        "rule": "masked_device_id_used_as_riskdata_input",
                        "reason": "Weapon riskData must use retained raw device_id reference, not masked/redacted display value",
                    }
                )
            if source_status not in {"skipped", "missing_required_fields", "not_checked", "blocked", "auth_failed", "timeout", "tool_gap", "auth_bridge_gap"} and not has_raw_reference(item, "device_id"):
                failures.append(
                    {
                        "rule": "raw_reference_safe_id_required",
                        "reason": "Weapon riskData execution requires current-task raw device_id reference safe id",
                    }
                )
            device_source = str(item.get("device_id_source", ""))
            if device_source and device_source not in {"weapon_user_to_device_graph", "Weapon graphData"}:
                if item.get("cross_source_device_id") is not True:
                    failures.append(
                        {
                            "rule": "cross_source_entity_misuse",
                            "reason": "Weapon riskData using non-Weapon device id must mark cross_source_device_id=true",
                        }
                    )
            if item.get("device_id_source") == "track_analysis_getDeviceIds" and item.get("cross_source_device_id") is not True:
                failures.append(
                    {
                        "rule": "cross_source_device_id_marker_required",
                        "reason": "Weapon riskData using track-analysis device id must mark cross_source_device_id=true",
                    }
                )
            if graph_empty and source_status not in {"skipped", "missing_required_fields", "not_checked", "blocked", "auth_failed", "timeout", "tool_gap", "auth_bridge_gap"} and item.get("weapon_graphData_empty") is not True:
                failures.append(
                    {
                        "rule": "cross_source_entity_misuse",
                        "reason": "Weapon graphData empty plus downstream riskData requires weapon_graphData_empty=true",
                    }
                )
        if source_name in TRACK_ANALYSIS_REQUIRED_PATHS:
            for forbidden_path in TRACK_ANALYSIS_FORBIDDEN_PATHS:
                if forbidden_path in endpoint:
                    failures.append(
                        {
                            "rule": "track_analysis_forbidden_guessed_endpoint",
                            "reason": f"{source_name} must not use guessed endpoint {forbidden_path}",
                        }
                    )
            required_track_path = TRACK_ANALYSIS_REQUIRED_PATHS[source_name]
            if item.get("source_status") == "completed" and required_track_path not in endpoint:
                failures.append(
                    {
                        "rule": "track_analysis_completed_endpoint_not_confirmed",
                        "reason": f"{source_name} completed endpoint must be {required_track_path}",
                    }
                )
        if source_name in {"tianshi_event_detail", "rcpEventDetail", "rcp_event_detail"}:
            event_id = str(item.get("event_id", ""))
            if looks_masked(event_id):
                failures.append(
                    {
                        "rule": "masked_event_id_used_as_rcp_input",
                        "reason": "event detail source must use retained raw event_id reference, not masked display value",
                    }
                )
        if source_name in {"ip_cluster_query", "hive_ip_cluster_query"}:
            ip_value = str(item.get("ip", ""))
            if looks_masked(ip_value):
                failures.append(
                    {
                        "rule": "redacted_ip_used_for_cluster_query",
                        "reason": "IP cluster query must use retained raw ip reference, not redacted display value",
                    }
                )
        if source_name == "track_analysis_profile":
            request_fields = set(item.get("request_fields", []))
            if item.get("source_status") == "completed" and not {"startTime", "endTime"}.issubset(request_fields):
                failures.append(
                    {
                        "rule": "track_analysis_profile_time_field_drift",
                        "reason": "track-analysis profile must use millisecond startTime/endTime",
                    }
                )
            if {"startDate", "endDate"} & request_fields:
                failures.append(
                    {
                        "rule": "track_analysis_profile_date_field_forbidden",
                        "reason": "track-analysis profile must not use startDate/endDate",
                    }
                )
        if source_name == "track_analysis_getUseDuration":
            if item.get("rows_shape") == "two_dimensional_array":
                failures.append(
                    {
                        "rule": "track_analysis_rows_shape_drift",
                        "reason": "getUseDuration.rows must be an object array with date/duration",
                    }
                )
        if item.get("source_name") in {"track_analysis_if_endpoint_verified", "track_analysis_getDeviceIds", "track_analysis_getUseDuration", "track_analysis_profile"}:
            endpoint_verified = bool(item.get("endpoint_verified"))
            if item.get("source_status") == "completed" and not endpoint_verified:
                failures.append(
                    {
                        "rule": "track_analysis_endpoint_not_confirmed_not_completed",
                        "reason": "track-analysis cannot be marked completed without executable endpoint verification",
                    }
                )

    if final_conclusion and final_conclusion in {"low_risk", "no_risk", "risk_excluded", "ato_excluded"}:
        if all(str(item.get("source_status")) in NO_DATA_STATUSES for item in matrix):
            failures.append(
                {
                    "rule": "nodata_timeout_blocked_not_counter_evidence",
                    "reason": "no_data / timeout / blocked / auth_failed cannot support low/no-risk conclusion",
                }
            )
    final_summary = final_conclusion or ""
    conclusion_state = str(next((item.get("conclusion_state") for item in matrix if item.get("conclusion_state")), ""))
    incomplete_matrix = any(str(item.get("source_status")) in {"blocked", "auth_failed", "timeout", "parse_error", "missing_required_fields", "not_checked", "tool_gap", "auth_bridge_gap"} for item in matrix)
    if final_summary in {"low_risk", "no_risk", "data_against_ato_suspicion"} and (incomplete_matrix or conclusion_state in {"needs_more_evidence", "insufficient_support", "partial"}):
        failures.append(
            {
                "rule": "summary_overclaim_drift",
                "reason": "final summary conclusion overclaims relative to incomplete evidence card",
            }
        )
    for idx, item in enumerate(matrix):
        manifest_path = item.get("manifest_path")
        actual_path = item.get("actual_path")
        if manifest_path and actual_path and manifest_path != actual_path:
            if item.get("fallback_path_used") is not True or not item.get("fallback_reason") or item.get("runtime_readable") is not True:
                failures.append(
                    {
                        "rule": "overlay_manifest_path_drift_warning",
                        "severity": "warning",
                        "reason": f"entry {idx} actual_path differs from manifest_path without fallback metadata",
                    }
                )

    return failures


def validate_user_facing_answer(answer_text: str, *, output_context: str = "generic_user_facing_answer") -> list[dict[str, str]]:
    failures: list[dict[str, str]] = []
    text = answer_text.lower()

    for marker in USER_FACING_RUNTIME_YAML_MARKERS:
        if marker in text:
            failures.append(
                {
                    "rule": "user_facing_no_runtime_yaml",
                    "case_id": "USER-FACING-NO-ROUTING-METADATA-001",
                    "output_context": output_context,
                    "reason": f"user-facing output contains runtime marker {marker}",
                }
            )

    return failures


def validate_ato_user_facing_answer(answer_text: str) -> list[dict[str, str]]:
    failures: list[dict[str, str]] = validate_user_facing_answer(
        answer_text,
        output_context="ato_single_case_business_answer",
    )
    text = answer_text.lower()
    raw_text = answer_text

    anchor_markers = ["可疑动作锚点", "可疑锚点", "多源锚点", "P0 多源", "realtime P0"]
    if not any(marker in raw_text for marker in anchor_markers):
        failures.append(
            {
                "rule": "ato_single_case_realtime_p0_anchor_required",
                "case_id": "ATO-SINGLE-NAKED-QUESTION-ANCHOR-FIRST-001",
                "reason": "ATO single-case answer must derive suspicious anchors from realtime P0 sources and state 可疑动作锚点",
            }
        )

    if "未完成可疑锚点发现" not in raw_text and "可疑动作锚点" not in raw_text and "多源锚点" not in raw_text:
        failures.append(
            {
                "rule": "ato_anchor_not_found_must_be_explicit",
                "reason": "when anchor is not established, answer must explicitly say 未完成可疑锚点发现",
            }
        )

    flat_markers = ["track", "rcp", "weapon", "登录日志", "档案中心"]
    if all(marker in text for marker in flat_markers) and not any(marker in raw_text for marker in ["可疑动作锚点", "可疑控制端", "设备身份一致性", "多源锚点"]):
        failures.append(
            {
                "rule": "source_plan_not_flat_source_summary",
                "case_id": "SOURCE-PLAN-NOT-FLAT-SOURCE-SUMMARY-001",
                "reason": "ATO answer cannot be a flat Track/RCP/Weapon/Login/Archives source summary",
            }
        )

    if "device_identity_consistency" not in text and "设备身份一致性" not in raw_text:
        failures.append(
            {
                "rule": "device_identity_consistency_required",
                "reason": "ATO answer must include device_identity_consistency / 设备身份一致性",
            }
        )
    else:
        missing_fields = [field for field in ATO_DEVICE_IDENTITY_FIELDS if field.lower() not in text and field not in raw_text]
        chinese_field_present = all(marker in raw_text for marker in ["机型", "系统", "UA", "IP", "登录端", "登录方式"])
        if missing_fields and not chinese_field_present:
            failures.append(
                {
                    "rule": "device_identity_consistency_fields_required",
                    "reason": "device identity consistency must cover model/os/UA/IP/login_source/login_type",
                }
            )

    owner_proof_phrases = ["track 证明本人", "track证明本人", "track 可以证明本人", "track可证明本人", "track 有活跃所以本人", "track有活跃所以本人"]
    if any(phrase in text for phrase in owner_proof_phrases):
        failures.append(
            {
                "rule": "track_not_proof_of_owner",
                "case_id": "TRACK-NOT-PROOF-OF-OWNER-001",
                "reason": "Track activity cannot prove owner operation",
            }
        )

    if "response_too_large" in text and any(phrase in raw_text for phrase in ["登录很多", "登录较多", "大量登录", "登录证据", "completed login"]):
        failures.append(
            {
                "rule": "login_response_too_large_not_evidence",
                "case_id": "LOGIN-RESPONSE-TOO-LARGE-NOT-EVIDENCE-001",
                "reason": "response_too_large is source_contract_gap, not login evidence or login volume evidence",
            }
        )

    if "常用" in raw_text and "device_id" in text and any(phrase in raw_text for phrase in ["风险较低", "排除 ATO", "排除被盗", "无风险"]):
        if "common_device_id_not_sufficient_to_exclude_ato" not in text and "伪装常用设备" not in raw_text:
            failures.append(
                {
                    "rule": "common_device_id_not_ato_exclusion",
                    "case_id": "ATO-COMMON-DEVICE-NOT-EXCLUSION-001",
                    "reason": "common device_id cannot be used as strong no-ATO counter evidence",
                }
            )

    if "wrapper_response_mismatch" in text and "login_log_evidence_unusable" not in text:
        failures.append(
            {
                "rule": "wrapper_response_mismatch_requires_unusable_login_evidence",
                "case_id": "LOGIN-UI-NODATA-WRAPPER-LARGE-MISMATCH-001",
                "reason": "UI no_data / wrapper response mismatch must mark login_log_evidence_unusable",
            }
        )

    realtime_incomplete_markers = [
        "7 天外",
        "7天外",
        "在线窗口",
        "窗口不足",
        "admin",
        "app 日志",
        "APP 日志",
        "WEB",
        "H5",
        "PC",
        "token",
        "OAuth",
        "扫码",
        "no_data",
        "response_too_large",
        "wrapper_response_mismatch",
        "source_contract_gap",
    ]
    risky_web_action_markers = ["发视频", "导流视频", "评论", "直播", "私信", "资料修改"]
    realtime_incomplete = any(marker in raw_text or marker.lower() in text for marker in realtime_incomplete_markers)
    web_action_gap = any(marker in raw_text for marker in risky_web_action_markers) and any(marker in raw_text for marker in ["WEB", "H5", "PC"])
    if realtime_incomplete or web_action_gap:
        missing_flags = [
            flag for flag in ATO_REALTIME_INCOMPLETE_REQUIRED_FLAGS
            if flag not in text and flag not in raw_text
        ]
        if missing_flags:
            failures.append(
                {
                    "rule": "ato_realtime_source_incomplete_hive_required",
                    "case_id": "ATO-REALTIME-SOURCE-INCOMPLETE-HIVE-REQUIRED-001",
                    "reason": f"ATO realtime incomplete answer must mark Hive-required gap flags {missing_flags}",
                }
            )
        if "account_security_hive_source_registry" not in text and "registry-first" not in text and "registry first" not in text:
            failures.append(
                {
                    "rule": "ato_hive_registry_first_required_in_answer",
                    "case_id": "ATO-LOGIN-HIVE-REGISTRY-FIRST-001",
                    "reason": "ATO Hive query plan must be registry-first and must not freely guess tables",
                }
            )

    realtime_no_anomaly_phrases = ["实时源无异常", "实时源没异常", "app 日志无异常", "APP 日志无异常", "在线登录无异常"]
    not_ato_phrases = ["倾向不是盗号", "不像盗号", "不是 ATO", "排除 ATO", "排除被盗", "低风险", "无风险"]
    if any(phrase in raw_text for phrase in realtime_no_anomaly_phrases) and any(phrase in raw_text for phrase in not_ato_phrases):
        closed_markers = [
            "login_control_chain_closed",
            "content_action_chain_closed",
            "device_identity_consistency_closed",
            "historical_baseline_closed",
        ]
        if not all(marker in text for marker in closed_markers):
            failures.append(
                {
                    "rule": "realtime_no_anomaly_not_ato_exclusion",
                    "case_id": "ATO-REALTIME-SOURCE-INCOMPLETE-HIVE-REQUIRED-001",
                    "reason": "realtime no anomaly cannot support non-ATO/low-risk conclusion unless all four chains are closed",
                }
            )

    return failures


def validate_batch_ato_user_facing_answer(answer_text: str) -> list[dict[str, str]]:
    failures: list[dict[str, str]] = validate_user_facing_answer(
        answer_text,
        output_context="batch_ato_cluster_answer",
    )
    text = answer_text.lower()
    raw_text = answer_text

    missing_markers = sorted(
        marker for marker in BATCH_ATO_REQUIRED_ANSWER_MARKERS
        if marker not in text and marker not in raw_text
    )
    if missing_markers:
        failures.append(
            {
                "rule": "batch_ato_cluster_lens_required",
                "case_id": "BATCH-ATO-CLUSTER-LENS-REQUIRED-001",
                "reason": f"batch ATO answer must include ATO lens overlay markers {missing_markers}",
            }
        )

    existing_cluster_markers = ["内容相似", "策略命中", "设备共性", "时间聚集", "账号画像", "行为模式", "existing_cluster"]
    if any(marker.lower() in text for marker in existing_cluster_markers) and "ato_cluster_lens" not in text and "ATO lens" not in raw_text:
        failures.append(
            {
                "rule": "existing_cluster_plus_ato_lens_required",
                "case_id": "BATCH-ATO-EXISTING-CLUSTER-PLUS-ATO-LENS-001",
                "reason": "existing content/strategy/device clusters must explicitly receive ATO lens overlay",
            }
        )

    web_login = any(marker in raw_text for marker in ["WEB", "H5", "PC"]) or any(marker in text for marker in ["web", "h5", "pc"])
    downstream_action = any(marker in raw_text for marker in ["导流", "发视频", "发布", "评论", "直播", "私信", "资料修改"])
    if web_login and downstream_action and not any(marker in text for marker in ["compromised_account_cluster", "high_suspected_ato_cluster", "web_untrusted_login_cluster"]):
        failures.append(
            {
                "rule": "batch_ato_web_untrusted_login_cluster_required",
                "case_id": "BATCH-ATO-WEB-UNTRUSTED-LOGIN-CLUSTER-001",
                "reason": "WEB non-trusted login plus downstream diversion action must identify compromised/high-suspected ATO cluster",
            }
        )

    if "login_to_action_delta" not in text and web_login and downstream_action:
        failures.append(
            {
                "rule": "batch_ato_login_to_action_delta_required",
                "case_id": "BATCH-ATO-LOGIN-TO-ACTION-DELTA-001",
                "reason": "batch ATO answer must extract login_to_action_delta for WEB/control-chain followed by downstream action",
            }
        )

    if "常用" in raw_text and "device_id" in text and any(phrase in raw_text for phrase in ["风险较低", "降低 ATO 置信度", "排除 ATO", "排除被盗", "无风险"]):
        if "common_device_id_not_sufficient_to_exclude_ato" not in text and "device_identity_inconsistency" not in text:
            failures.append(
                {
                    "rule": "batch_common_device_not_exclusion",
                    "case_id": "BATCH-ATO-COMMON-DEVICE-NOT-EXCLUSION-001",
                    "reason": "common device_id cannot reduce or exclude batch ATO confidence without full device identity consistency",
                }
            )

    login_gap_markers = ["no_data", "response_too_large", "wrapper mismatch", "wrapper_mismatch", "wrapper_response_mismatch", "无数据"]
    low_risk_markers = ["低风险", "无风险", "排除 ato", "排除ATO", "排除被盗", "risk_excluded"]
    low_risk_negated = any(
        phrase in raw_text
        for phrase in [
            "不得输出低风险",
            "不能输出低风险",
            "不得作为低风险",
            "不能作为低风险",
            "不是低风险",
            "不当低风险反证",
            "不得当低风险反证",
            "不能当低风险反证",
        ]
    )
    if any(marker in text for marker in login_gap_markers) and any(marker.lower() in text for marker in low_risk_markers) and not low_risk_negated:
        failures.append(
            {
                "rule": "batch_login_gap_not_low_risk",
                "case_id": "BATCH-ATO-LOGIN-NODATA-NOT-LOW-RISK-001",
                "reason": "login no_data / response_too_large / wrapper mismatch cannot be low-risk counter evidence",
            }
        )

    if any(phrase in raw_text for phrase in ["所有账号都被盗", "全批账号都被盗", "全量都是 ATO", "全部都是 ATO"]):
        if not any(marker in text for marker in ["coverage", "similarity", "counter", "反例", "代表样本不能"]):
            failures.append(
                {
                    "rule": "representative_not_global_proof",
                    "case_id": "BATCH-ATO-REPRESENTATIVE-NOT-GLOBAL-PROOF-001",
                    "reason": "representative sample or batch commonality cannot prove the full batch without coverage/similarity/counter-example analysis",
                }
            )

    if "track" in text and any(phrase in raw_text for phrase in ["证明本人", "本人操作", "低风险"]):
        failures.append(
            {
                "rule": "batch_track_not_owner_proof",
                "case_id": "BATCH-ATO-TRACK-NOT-OWNER-PROOF-001",
                "reason": "Track activity is auxiliary and cannot prove owner operation or batch low risk",
            }
        )

    realtime_incomplete_markers = [
        "实时登录源不完整",
        "实时源不完整",
        "在线登录源不完整",
        "在线窗口",
        "窗口不足",
        "admin",
        "app 日志",
        "APP 日志",
        "WEB",
        "H5",
        "PC",
        "token",
        "OAuth",
        "扫码",
        "no_data",
        "response_too_large",
        "wrapper_response_mismatch",
        "source_contract_gap",
    ]
    if any(marker in raw_text or marker.lower() in text for marker in realtime_incomplete_markers):
        missing_flags = [
            flag for flag in ATO_REALTIME_INCOMPLETE_REQUIRED_FLAGS
            if flag not in text and flag not in raw_text
        ]
        if missing_flags:
            failures.append(
                {
                    "rule": "batch_ato_realtime_incomplete_hive_required",
                    "case_id": "BATCH-ATO-HIVE-REQUIRED-WHEN-REALTIME-INCOMPLETE-001",
                    "reason": f"batch ATO realtime incomplete answer must mark Hive-required gap flags {missing_flags}",
                }
            )
        if "account_security_hive_source_registry" not in text and "registry-first" not in text and "registry first" not in text:
            failures.append(
                {
                    "rule": "batch_ato_hive_registry_first_required_in_answer",
                    "case_id": "BATCH-ATO-HIVE-REGISTRY-FIRST-001",
                    "reason": "batch ATO Hive query plan must be registry-first and must not freely guess tables",
                }
            )

    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Dennis source orchestration plan usage.")
    parser.add_argument("--task-type", default="single_user_account_security")
    parser.add_argument("--entity-count", type=int, default=1)
    parser.add_argument("--no-cache", action="store_true")
    parser.add_argument("--source-completion-matrix", default=None)
    parser.add_argument("--passthrough-envelope", default=None, help="Optional pure passthrough service envelope JSON for Dennis-side quality derivation validation.")
    parser.add_argument("--final-conclusion", default=None)
    parser.add_argument("--answer-text", default=None, help="Optional user-facing answer text for response-time contract validation.")
    parser.add_argument("--ato-single-case", action="store_true", help="Validate ATO single-case answer hard gates.")
    parser.add_argument("--batch-ato", action="store_true", help="Validate batch ATO cluster lens answer hard gates.")
    parser.add_argument(
        "--output-context",
        choices=sorted(USER_FACING_CONTEXTS),
        default="generic_user_facing_answer",
        help="User-facing answer context for runtime YAML visibility checks.",
    )
    parser.add_argument(
        "--allow-runtime-yaml",
        action="store_true",
        help="Allow runtime YAML markers for explicit debug/internal validation fixtures.",
    )
    parser.add_argument("--format", choices=["json"], default="json")
    args = parser.parse_args()

    plan = load_plan()
    selected = select_plan(plan, args.task_type, args.entity_count)
    matrix = parse_matrix(args.source_completion_matrix)
    passthrough_envelope = parse_passthrough_envelope(args.passthrough_envelope)
    static_failures = validate_static_plan_contract(plan)
    passthrough_failures, generated_passthrough = validate_passthrough_envelope(passthrough_envelope)
    failures = (
        validate_matrix(selected, matrix, no_cache=args.no_cache, final_conclusion=args.final_conclusion)
        if selected and matrix
        else []
    )
    failures = static_failures + passthrough_failures + failures
    answer_failures: list[dict[str, str]] = []
    if args.answer_text and not args.allow_runtime_yaml:
        if args.batch_ato:
            answer_failures = validate_batch_ato_user_facing_answer(args.answer_text)
        elif args.ato_single_case:
            answer_failures = validate_ato_user_facing_answer(args.answer_text)
        else:
            answer_failures = validate_user_facing_answer(args.answer_text, output_context=args.output_context)
    failures += answer_failures

    result = {
        "schema_version": "source_orchestration_check_v1",
        "task_type": args.task_type,
        "entity_count": args.entity_count,
        "no_cache": args.no_cache,
        "plan_selected": selected is not None,
        "static_plan_contract_valid": not static_failures,
        "controlled_parallel_groups_supported": sorted(CONTROLLED_PARALLEL_EXECUTION_GROUPS),
        "required_p0_sources": selected.get("required_p0_sources", []) if selected else [],
        "conditional_sources": selected.get("conditional_sources", []) if selected else [],
        "stop_conditions": selected.get("stop_conditions", {}) if selected else {},
        "source_completion_matrix_present": bool(matrix),
        "passthrough_envelope_validated": passthrough_envelope is not None,
        "dennis_generated_from_passthrough": generated_passthrough,
        "answer_text_validated": bool(args.answer_text),
        "ato_single_case_answer_validated": bool(args.ato_single_case and args.answer_text),
        "batch_ato_answer_validated": bool(args.batch_ato and args.answer_text),
        "output_context": args.output_context,
        "runtime_yaml_allowed": args.allow_runtime_yaml,
        "validation_pass": not failures,
        "failures": failures,
        "real_platform_called": False,
        "dataagent_called": False,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
