#!/usr/bin/env python3
"""Static runtime readiness preflight for Dennis Risk Agent overlays.

The script intentionally performs local file checks only. It does not read auth
state, access platforms, call DataAgent, or validate live gateway config.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def check_contains(name: str, text: str, patterns: list[str], severity: str = "critical") -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for pattern in patterns:
        if pattern not in text:
            findings.append(
                {
                    "check": name,
                    "severity": severity,
                    "status": "fail",
                    "reason": f"missing required marker: {pattern}",
                }
            )
    return findings


def check_absent(name: str, text: str, patterns: list[str], severity: str = "critical") -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for pattern in patterns:
        if pattern in text:
            findings.append(
                {
                    "check": name,
                    "severity": severity,
                    "status": "fail",
                    "reason": f"forbidden marker present: {pattern}",
                }
            )
    return findings


def check_regex(name: str, text: str, patterns: list[str], severity: str = "critical") -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for pattern in patterns:
        if not re.search(pattern, text, flags=re.MULTILINE):
            findings.append(
                {
                    "check": name,
                    "severity": severity,
                    "status": "fail",
                    "reason": f"missing required regex: {pattern}",
                }
            )
    return findings


def main() -> int:
    runner = read_text(REPO_ROOT / "computer_use_poc" / "sso_session_runner.py")
    agents = read_text(REPO_ROOT / "AGENTS.md") + "\n" + read_text(REPO_ROOT / "computer_use_poc" / "AGENTS.md")
    guard = read_text(REPO_ROOT / "computer_use_poc" / "multi_entry_runtime_guard_v1.md")
    routing = read_text(REPO_ROOT / "computer_use_poc" / "scene_to_capability_routing.md")
    playbook_index = read_text(REPO_ROOT / "computer_use_poc" / "platform_call_playbook_index.md")
    tools = read_text(REPO_ROOT / "TOOLS.md")
    validation = read_text(REPO_ROOT / "computer_use_poc" / "runtime_validation_cases_v1.yaml")

    findings: list[dict[str, Any]] = []

    findings += check_absent(
        "runner_no_dry_run_success",
        runner,
        [
            '"dry_run_only": True',
            "'dry_run_only': True",
            '"constructed_url"',
            "'constructed_url'",
        ],
    )
    findings += check_contains(
        "runner_required_cli",
        runner,
        [
            "--platform",
            "--action",
            "--user-id",
            "--timeout",
            "--format",
            "query_user_login_log",
        ],
    )
    findings += check_contains(
        "runner_observation_contract",
        runner,
        [
            "real_platform_request_executed",
            "executor_mode",
            "source_status",
            "source_quality",
            "redaction_applied",
            "SmartSSOSession",
        ],
    )
    findings += check_absent(
        "runner_no_arbitrary_url_input",
        runner,
        [
            "--target_url",
            "--target-url",
            "arbitrary_url",
        ],
    )
    findings += check_contains(
        "runner_live_dependency_contract",
        runner,
        [
            "ks_aimate.sso_login_client",
            "cookie_state_fallback",
            ".ks_sso",
            "sso-state.json",
            "kuaishou.com",
        ],
    )
    findings += check_absent(
        "runner_no_legacy_sso_session_import_dependency",
        runner,
        [
            'importlib.import_module("sso_session")',
            "importlib.import_module('sso_session')",
        ],
    )

    combined_guard = agents + "\n" + guard + "\n" + routing
    findings += check_contains(
        "routing_guard_markers",
        combined_guard + "\n" + tools,
        [
            "DENNIS_ROUTING_GUARD_V1",
            "small_batch_execution_with_checkpoint",
            "single_entity_execution_mode",
            "batch_clustering_mode",
        ],
    )
    findings += check_contains(
        "realtime_api_confirmation_boundary",
        combined_guard,
        [
            "实时只读 API 查询不需要用户确认",
            "DataAgent / Hive / 大批量 / 写操作 / 高风险操作需要确认",
        ],
    )
    findings += check_contains(
        "platform_playbook_preflight_required",
        combined_guard + "\n" + playbook_index,
        [
            "platform_call_playbook_index",
            "执行任何平台 source 前，必须先读取",
            "platform_call_preflight",
        ],
    )
    findings += check_contains(
        "source_quality_boundaries",
        combined_guard + "\n" + playbook_index,
        [
            "no_data",
            "blocked",
            "timeout",
            "auth_failed",
            "source_quality",
        ],
    )
    findings += check_contains(
        "validation_gate_cases",
        validation,
        [
            "SSO-RUNNER-REAL-EXECUTOR-001",
            "PLATFORM-PLAYBOOK-PREFLIGHT-001",
            "REALTIME-API-NO-USER-CONFIRM-001",
            "SINGLE-USER-P0-MULTISOURCE-62950989-001",
        ],
    )

    tools_status = "present" if tools else "optional_absent_using_platform_call_playbook_index"
    blocking = [item for item in findings if item["severity"] in {"critical", "high"}]
    summary = {
        "schema_version": "dennis_runtime_preflight_v1",
        "preflight_pass": not blocking,
        "release_overlay_ready": not blocking,
        "critical_count": sum(1 for item in findings if item["severity"] == "critical"),
        "high_count": sum(1 for item in findings if item["severity"] == "high"),
        "findings": findings,
        "checked_files": [
            "AGENTS.md",
            "computer_use_poc/sso_session_runner.py",
            "computer_use_poc/multi_entry_runtime_guard_v1.md",
            "computer_use_poc/scene_to_capability_routing.md",
            "computer_use_poc/platform_call_playbook_index.md",
            "computer_use_poc/runtime_validation_cases_v1.yaml",
        ],
        "tools_md_status": tools_status,
        "real_platform_called": False,
        "dataagent_called": False,
        "warnings": [
            "static_preflight_pass_does_not_prove_live_auth_success",
            "live SmartSSOSession / cookie-state validation must be tested in live runtime",
        ],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not blocking else 1


if __name__ == "__main__":
    raise SystemExit(main())
