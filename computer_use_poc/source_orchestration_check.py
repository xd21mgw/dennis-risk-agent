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
FORBIDDEN_ACCESS_METHODS = {"curl_cookie", "manual_cookie", "main_agent_direct_exec", "arbitrary_url"}
NO_DATA_STATUSES = {"no_data", "blocked", "auth_failed", "timeout", "parse_error"}
NON_ENDPOINT_STATUSES = {"skipped", "missing_required_fields", "not_checked", "blocked", "auth_failed", "timeout"}
EXPLAINED_NOT_EXECUTED_STATUSES = {"blocked", "auth_failed", "not_checked", "missing_required_fields", "timeout", "parse_error"}
ENVIRONMENT_GAP_MARKERS = {"sandbox_missing", "agent_browser_missing", "node_missing", "macos_capability_missing"}
AUTH_GAP_MARKERS = {"sso_ticket_expired", "auth_failed", "login_page", "access_proxy_redirect"}
TOOL_GAP_MARKERS = {"tool_unavailable", "safe_bin_missing", "browser_profile_lock"}


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


def source_names(matrix: list[dict[str, Any]]) -> set[str]:
    return {str(item.get("source_name", "")) for item in matrix}


def endpoint_for(matrix: list[dict[str, Any]], source_name: str) -> str:
    for item in matrix:
        if item.get("source_name") == source_name:
            return str(item.get("endpoint", "") or item.get("path", "") or item.get("api_path", ""))
    return ""


def as_bool(value: Any) -> bool:
    return value is True or str(value).lower() == "true"


def is_registered_endpoint(endpoint: str) -> bool:
    registered_fragments = {
        "/apiv2/graphData",
        "/apiv2/riskData",
        "/dp/platform/app/analytics/v2/sequence/getLastestDateTime",
        "/dp/platform/app/analytics/v2/sequence/getDeviceIds",
        "/dp/platform/app/analytics/v2/sequence/getUseDuration",
        "/dp/platform/app/analytics/v2/sequence/profile",
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
        for field in required_fields:
            if field not in item:
                failures.append(
                    {
                        "rule": "source_completion_matrix_required_fields",
                        "reason": f"entry {idx} missing required field {field}",
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
            if item.get("response_type") not in (None, "json", "structured_json"):
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
        status = str(next((item.get("source_status") for item in matrix if item.get("source_name") == name), ""))
        if required_path and required_path not in endpoint and status not in NON_ENDPOINT_STATUSES:
            failures.append(
                {
                    "rule": "required_p0_source_path_missing",
                    "reason": f"{name} must use endpoint containing {required_path}",
                }
            )
        if name == "weapon_user_to_device_graph":
            if FORBIDDEN_WEAPON_GRAPH_PATH in endpoint:
                failures.append(
                    {
                        "rule": "weapon_forbidden_api_graphdata_path",
                        "reason": "weapon_user_to_device_graph must not use /api/graphData",
                    }
                )
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
            if source_status not in EXPLAINED_NOT_EXECUTED_STATUSES and not endpoint and source_name != "user_login_unified_log":
                failures.append(
                    {
                        "rule": "source_plan_not_executed",
                        "reason": f"{source_name} lacks endpoint and lacks explicit blocked/auth_failed/not_checked/missing_required_fields explanation",
                    }
                )
        if source_status == "completed":
            if item.get("real_platform_request_executed") is not True:
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
            if item.get("response_type") not in {"json", "structured_json"}:
                failures.append(
                    {
                        "rule": "source_status_mismatch",
                        "reason": f"entry {idx} is completed without response_type=json",
                    }
                )
            if item.get("execution_observation_id") in (None, ""):
                failures.append(
                    {
                        "rule": "capability_registry_overtrust",
                        "reason": f"entry {idx} is completed without current execution observation id",
                    }
                )
        if source_status == "no_data":
            if item.get("http_status") != 200 or item.get("response_type") not in {"json", "structured_json"} or item.get("records_count") != 0:
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
        if source_status in {"blocked", "auth_failed", "timeout", "not_checked"} and gap_type == "":
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
            if graph_empty and source_status not in {"skipped", "missing_required_fields", "not_checked"} and item.get("weapon_graphData_empty") is not True:
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
    incomplete_matrix = any(str(item.get("source_status")) in {"blocked", "auth_failed", "timeout", "parse_error", "missing_required_fields", "not_checked"} for item in matrix)
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Dennis source orchestration plan usage.")
    parser.add_argument("--task-type", default="single_user_account_security")
    parser.add_argument("--entity-count", type=int, default=1)
    parser.add_argument("--no-cache", action="store_true")
    parser.add_argument("--source-completion-matrix", default=None)
    parser.add_argument("--final-conclusion", default=None)
    parser.add_argument("--format", choices=["json"], default="json")
    args = parser.parse_args()

    plan = load_plan()
    selected = select_plan(plan, args.task_type, args.entity_count)
    matrix = parse_matrix(args.source_completion_matrix)
    failures = (
        validate_matrix(selected, matrix, no_cache=args.no_cache, final_conclusion=args.final_conclusion)
        if selected and matrix
        else []
    )

    result = {
        "schema_version": "source_orchestration_check_v1",
        "task_type": args.task_type,
        "entity_count": args.entity_count,
        "no_cache": args.no_cache,
        "plan_selected": selected is not None,
        "required_p0_sources": selected.get("required_p0_sources", []) if selected else [],
        "conditional_sources": selected.get("conditional_sources", []) if selected else [],
        "stop_conditions": selected.get("stop_conditions", {}) if selected else {},
        "source_completion_matrix_present": bool(matrix),
        "validation_pass": not failures,
        "failures": failures,
        "real_platform_called": False,
        "dataagent_called": False,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
