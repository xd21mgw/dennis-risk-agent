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


def validate_matrix(selected_plan: dict[str, Any], matrix: list[dict[str, Any]]) -> list[dict[str, str]]:
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
        if required_path and required_path not in endpoint_for(matrix, name):
            failures.append(
                {
                    "rule": "required_p0_source_path_missing",
                    "reason": f"{name} must use endpoint containing {required_path}",
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

    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Dennis source orchestration plan usage.")
    parser.add_argument("--task-type", default="single_user_account_security")
    parser.add_argument("--entity-count", type=int, default=1)
    parser.add_argument("--no-cache", action="store_true")
    parser.add_argument("--source-completion-matrix", default=None)
    parser.add_argument("--format", choices=["json"], default="json")
    args = parser.parse_args()

    plan = load_plan()
    selected = select_plan(plan, args.task_type, args.entity_count)
    matrix = parse_matrix(args.source_completion_matrix)
    failures = validate_matrix(selected, matrix) if selected and matrix else []

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
