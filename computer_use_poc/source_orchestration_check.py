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
FORBIDDEN_ACCESS_METHODS = {"curl_cookie", "manual_cookie", "main_agent_direct_exec", "arbitrary_url"}
NO_DATA_STATUSES = {"no_data", "blocked", "auth_failed", "timeout", "parse_error"}


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
                    "rule": "required_p0_source_missing",
                    "reason": f"missing required P0 source {name}",
                }
            )
            continue
        required_path = source.get("required_path_contains")
        endpoint = endpoint_for(matrix, name)
        if required_path and required_path not in endpoint:
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
        if name == "weapon_device_risk":
            for marker in ["product=KUAISHOU", "deviceIds="]:
                if marker not in endpoint:
                    failures.append(
                        {
                            "rule": "weapon_riskdata_query_shape_drift",
                            "reason": f"weapon_device_risk missing {marker}",
                        }
                    )

    for item in matrix:
        if item.get("source_name") == "track_analysis_if_endpoint_verified":
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
