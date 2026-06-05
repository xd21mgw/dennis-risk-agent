#!/usr/bin/env python3
"""Static runtime readiness preflight for Dennis Risk Agent overlays.

The script intentionally performs local file checks only. It does not read auth
state, access platforms, call DataAgent, or validate live gateway config.
"""

from __future__ import annotations

import json
import re
import subprocess
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
    source_plan = read_text(REPO_ROOT / "computer_use_poc" / "source_orchestration_plan_v1.yaml")
    source_check = read_text(REPO_ROOT / "computer_use_poc" / "source_orchestration_check.py")
    interface_asset_table = read_text(REPO_ROOT / "computer_use_poc" / "browser_backed_interface_asset_table_v1.yaml")
    capability_registry = read_text(REPO_ROOT / "computer_use_poc" / "capability_registry.md")
    service_adapter = read_text(REPO_ROOT / "computer_use_poc" / "browser_backed_service_adapter_v1.md")
    runtime_runner = read_text(REPO_ROOT / "computer_use_poc" / "runtime_case_execution_runner.py")
    drift_audit = read_text(REPO_ROOT / "computer_use_poc" / "internal_agent_drift_audit_v1.md")
    tools = read_text(REPO_ROOT / "TOOLS.md")
    validation = read_text(REPO_ROOT / "computer_use_poc" / "runtime_validation_cases_v1.yaml")
    readiness = read_text(REPO_ROOT / "computer_use_poc" / "release_overlay_readiness_checklist.md")
    bin_runner = read_text(REPO_ROOT / "bin" / "sso_session_runner")
    raw_reference_contract = read_text(REPO_ROOT / "computer_use_poc" / "raw_reference_redaction_contract_v1.md")

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
            "--device-id",
            "--timeout",
            "--format",
            "query_user_login_log",
            "graph_data",
            "risk_data",
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
            "arbitrary_url",
        ],
    )
    if re.search(r"parser\.add_argument\([\"']--target[_-]url", runner):
        findings.append(
            {
                "check": "runner_no_target_url_cli_argument",
                "severity": "critical",
                "status": "fail",
                "reason": "runner must not accept target_url / arbitrary URL from CLI",
            }
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
    findings += check_contains(
        "runner_auth_refresh_retry_contract",
        runner,
        [
            "auth_refresh_attempted",
            "auth_refresh_status",
            "retry_after_refresh",
            "source_status_before_refresh",
            "sso_session.py",
            "--target_url",
            "refresh_sso_for_whitelist_url",
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
    findings += check_contains(
        "weapon_runner_action_contract",
        runner,
        [
            '"weapon"',
            '"graph_data"',
            '"risk_data"',
            "/apiv2/graphData",
            "/apiv2/riskData",
            "source_card",
            "response_type",
            "records_count",
            "raw_device_ids_for_chaining",
            "masked_device_ids",
            "device_id_redaction_policy",
            "pointInfoMap",
        ],
    )
    findings += check_contains(
        "raw_reference_redaction_contract",
        raw_reference_contract + "\n" + source_check + "\n" + validation,
        [
            "Raw Reference Retention",
            "tool_call_internal",
            "source_checkpoint_private",
            "source_chaining",
            "masked_device_id",
            "masked_event_id",
            "redacted_ip",
            "CREDENTIAL-NEVER-RETAIN-001",
        ],
    )
    findings += check_absent(
        "weapon_runner_no_forbidden_default_path",
        runner,
        [
            "weapon.corp.kuaishou.com/api/graphData",
            "/anti-device/",
        ],
    )
    if "/api/graphData" in runner and "forbidden_endpoint" not in runner:
        findings.append(
            {
                "check": "weapon_runner_api_graphdata_boundary",
                "severity": "critical",
                "status": "fail",
                "reason": "runner mentions /api/graphData without marking it forbidden",
            }
        )
    findings += check_contains(
        "safe_bin_runner_wrapper",
        bin_runner,
        [
            'cd "$(dirname "$0")/.."',
            "exec python3 computer_use_poc/sso_session_runner.py",
        ],
    )

    combined_guard = agents + "\n" + guard + "\n" + routing
    first_200_agents = "\n".join((read_text(REPO_ROOT / "AGENTS.md").splitlines())[:200])
    findings += check_contains(
        "agents_entry_guard_first_200",
        first_200_agents,
        [
            "source_orchestration_check.py",
            "没有 source plan，不允许调用",
            "业务 case 中禁止现场修认证态",
            "main agent 不得 fallback direct 查平台",
            "禁止自由猜 URL",
        ],
    )
    findings += check_contains(
        "tools_restore_marker",
        tools,
        [
            "TOOLS_MAIN_ENTRY_GUARD_FULL",
            "Focused overlays must not include or overwrite top-level `AGENTS.md` or `TOOLS.md`",
            "source_orchestration_check.py",
        ],
    )
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
            "TOOLS-RESTORE-MARKER-001",
            "FOCUSED-OVERLAY-NO-AGENTS-TOOLS-001",
            "AGENTS-ENTRY-GUARD-FIRST-200-001",
            "SAFEBIN-RUNNER-WRAPPER-001",
            "EXEC-ALLOWLIST-CONTRACT-001",
            "WEAPON-RUNNER-ACTION-001",
            "MAIN-FALLBACK-DIRECT-BYPASS-FORBIDDEN-001",
        ],
    )
    findings += check_contains(
        "release_overlay_readiness_live_fix_contract",
        readiness,
        [
            "TOOLS_MAIN_ENTRY_GUARD_FULL",
            "Focused overlays must not include top-level `AGENTS.md` or `TOOLS.md`",
            "bin/sso_session_runner",
            "exec.security=allowlist",
            "exec.security=full",
            "sso_session_runner",
        ],
    )
    # Live openclaw / exec-approvals files are not committed to this repo. If a
    # caller supplies snapshots under computer_use_poc/live_runtime_snapshots/,
    # validate them fail-closed; otherwise report a non-blocking warning.
    snapshot_dir = REPO_ROOT / "computer_use_poc" / "live_runtime_snapshots"
    openclaw_snapshot = snapshot_dir / "openclaw.json"
    approvals_snapshot = snapshot_dir / "exec-approvals.json"
    if openclaw_snapshot.exists():
        openclaw_text = read_text(openclaw_snapshot)
        if "dennis-risk-agent" not in openclaw_text or '"security": "full"' in openclaw_text or '"exec.security": "full"' in openclaw_text:
            findings.append(
                {
                    "check": "exec_security_allowlist_contract",
                    "severity": "critical",
                    "status": "fail",
                    "reason": "live openclaw snapshot must contain dennis-risk-agent and must not set exec.security=full",
                }
            )
    else:
        findings.append(
            {
                "check": "exec_security_allowlist_contract",
                "severity": "warning",
                "status": "not_checked",
                "reason": "live openclaw snapshot absent; validate dennis-risk-agent exec.security=allowlist during live apply",
            }
        )
    if approvals_snapshot.exists():
        approvals_text = read_text(approvals_snapshot)
        if "dennis-risk-agent" not in approvals_text or "sso_session_runner" not in approvals_text or "python3" not in approvals_text:
            findings.append(
                {
                    "check": "exec_approvals_allowlist_contract",
                    "severity": "critical",
                    "status": "fail",
                    "reason": "exec approvals snapshot must include dennis-risk-agent allowlist with sso_session_runner and python3",
                }
            )
    else:
        findings.append(
            {
                "check": "exec_approvals_allowlist_contract",
                "severity": "warning",
                "status": "not_checked",
                "reason": "exec-approvals snapshot absent; validate non-empty dennis-risk-agent allowlist during live apply",
            }
        )
    findings += check_contains(
        "source_orchestration_plan_required",
        source_plan,
        [
            "single_user_account_security",
            "allow_stop_after_login_log_only",
            "allow_final_conclusion_without_source_completion_matrix",
            "allow_low_risk_from_no_data_only",
        ],
    )
    current_interface_contract = "\n".join(
        [
            interface_asset_table,
            capability_registry,
            service_adapter,
            source_plan,
            runtime_runner,
        ]
    )
    findings += check_contains(
        "current_browser_backed_interface_contract",
        current_interface_contract,
        [
            "interface_count: 70",
            "action_count=70",
            "browser_backed_interface_asset_table_v1.yaml",
            "login_logs_search",
            "weapon_inventory",
            "/actions/batch",
            "browser_backed_actions_batch_v1",
        ],
    )
    findings += check_contains(
        "source_orchestration_validator_contract",
        source_check,
        [
            "--task-type",
            "--entity-count",
            "--no-cache",
            "source_completion_matrix",
            "login_log_only_cannot_conclude",
            "/apiv2/graphData",
            "/apiv2/riskData",
            "track_analysis_endpoint_not_confirmed_not_completed",
            "stale_data_drift",
            "forbidden_tool_boundary_drift",
            "weapon_forbidden_api_graphdata_path",
            "nodata_timeout_blocked_not_counter_evidence",
            "source_plan_not_executed",
            "source_status_mismatch",
            "cross_source_entity_misuse",
            "capability_registry_overtrust",
            "environment_issue_as_platform_gap",
            "manual_exploration_creep",
            "summary_overclaim_drift",
            "overlay_manifest_path_drift_warning",
        ],
    )
    findings += check_contains(
        "internal_agent_drift_audit_required",
        drift_audit,
        [
            "Routing Drift",
            "Source Orchestration Drift",
            "Platform Path Drift",
            "Auth / Session Drift",
            "Tool Boundary Drift",
            "Evidence Semantic Drift",
            "Stale Data Drift",
            "Capability Status Drift",
            "Source Plan Not Executed",
            "Source Status Mismatch",
            "Cross Source Entity Misuse",
            "Capability Registry Overtrust",
            "Environment Issue As Platform Gap",
            "Manual Exploration Creep",
            "Summary Overclaim Drift",
            "Overlay Manifest Path Drift",
        ],
    )
    source_check_path = REPO_ROOT / "computer_use_poc" / "source_orchestration_check.py"
    asset_check_path = REPO_ROOT / "computer_use_poc" / "interface_asset_table_check.py"
    if not interface_asset_table or not asset_check_path.exists():
        findings.append(
            {
                "check": "interface_asset_table_check_available",
                "severity": "critical",
                "status": "fail",
                "reason": "browser_backed_interface_asset_table_v1.yaml or interface_asset_table_check.py missing",
            }
        )
    else:
        try:
            asset_proc = subprocess.run(
                [
                    sys.executable,
                    str(asset_check_path),
                    "--format",
                    "json",
                ],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                timeout=10,
                check=False,
            )
            if asset_proc.returncode != 0:
                findings.append(
                    {
                        "check": "interface_asset_table_check_passes",
                        "severity": "critical",
                        "status": "fail",
                        "reason": f"interface_asset_table_check.py returned {asset_proc.returncode}: {asset_proc.stderr.strip()}",
                    }
                )
            else:
                asset_output = json.loads(asset_proc.stdout)
                if (
                    not asset_output.get("validation_pass")
                    or asset_output.get("service_allowlist_count") != 70
                    or asset_output.get("asset_table_count") != 70
                    or asset_output.get("missing_in_asset")
                    or asset_output.get("extra_in_asset")
                ):
                    findings.append(
                        {
                            "check": "interface_asset_table_check_passes",
                            "severity": "critical",
                            "status": "fail",
                            "reason": "interface asset table must match 70 service actions with no missing/extra entries",
                        }
                    )
        except Exception as exc:  # noqa: BLE001 - preflight should report fail-closed reason.
            findings.append(
                {
                    "check": "interface_asset_table_check_passes",
                    "severity": "critical",
                    "status": "fail",
                    "reason": f"interface_asset_table_check.py failed to run: {exc}",
                }
            )

    if not source_check_path.exists():
        findings.append(
            {
                "check": "source_orchestration_validator_runnable",
                "severity": "critical",
                "status": "fail",
                "reason": "computer_use_poc/source_orchestration_check.py missing",
            }
        )
    else:
        try:
            proc = subprocess.run(
                [
                    sys.executable,
                    str(source_check_path),
                    "--task-type",
                    "single_user_account_security",
                    "--entity-count",
                    "1",
                    "--no-cache",
                    "--format",
                    "json",
                ],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                timeout=10,
                check=False,
            )
            if proc.returncode != 0:
                findings.append(
                    {
                        "check": "source_orchestration_validator_runnable",
                        "severity": "critical",
                        "status": "fail",
                        "reason": f"source_orchestration_check.py returned {proc.returncode}: {proc.stderr.strip()}",
                    }
                )
            else:
                output = json.loads(proc.stdout)
                if not output.get("plan_selected"):
                    findings.append(
                        {
                            "check": "source_orchestration_validator_runnable",
                            "severity": "critical",
                            "status": "fail",
                            "reason": "source_orchestration_check.py did not select a plan",
                        }
                    )
            negative_proc = subprocess.run(
                [
                    sys.executable,
                    str(source_check_path),
                    "--task-type",
                    "single_user_account_security",
                    "--entity-count",
                    "1",
                    "--source-completion-matrix",
                    '[{"source_name":"login_logs_search","source_status":"no_data","source_quality":"no_data_not_risk_exclusion","evidence_time_range":"last_30_days","collected_at":"2026-05-27T00:00:00+08:00","source_provenance":"realtime"}]',
                    "--format",
                    "json",
                ],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                timeout=10,
                check=False,
            )
            if negative_proc.returncode == 0 or "login_log_only_cannot_conclude" not in negative_proc.stdout:
                findings.append(
                    {
                        "check": "source_orchestration_negative_case",
                        "severity": "critical",
                        "status": "fail",
                        "reason": "source_orchestration_check.py did not fail login-log-only matrix",
                    }
                )
        except Exception as exc:  # noqa: BLE001 - preflight should report fail-closed reason.
            findings.append(
                {
                    "check": "source_orchestration_validator_runnable",
                    "severity": "critical",
                    "status": "fail",
                    "reason": f"source_orchestration_check.py failed to run: {exc}",
                }
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
            "computer_use_poc/source_orchestration_plan_v1.yaml",
            "computer_use_poc/source_orchestration_check.py",
            "computer_use_poc/browser_backed_interface_asset_table_v1.yaml",
            "computer_use_poc/interface_asset_table_check.py",
            "computer_use_poc/capability_registry.md",
            "computer_use_poc/browser_backed_service_adapter_v1.md",
            "computer_use_poc/runtime_case_execution_runner.py",
            "computer_use_poc/internal_agent_drift_audit_v1.md",
            "computer_use_poc/runtime_validation_cases_v1.yaml",
            "TOOLS.md",
            "bin/sso_session_runner",
            "computer_use_poc/release_overlay_readiness_checklist.md",
            "computer_use_poc/raw_reference_redaction_contract_v1.md",
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
