#!/usr/bin/env python3
"""Local shadow pipeline dry-run for security preflight.

Pipeline:
tool_call_request samples -> contract validator -> preflight evaluator ->
shadow event generation -> local metric summary.

This script is local-only. It does not connect to runtime, internal platforms,
auth state, approval systems, audit storage, or enforce mode.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List

from security_preflight_evaluator import evaluate_request
from security_preflight_request_contract_validator import validate_request


ROOT = Path(__file__).resolve().parent
POLICY_PATH = ROOT / "security_preflight_policy.yaml"
TEST_CASES_PATH = ROOT / "security_preflight_request_contract_test_cases.json"
RUN_LOG_PATH = ROOT / "run_logs" / "security_preflight_shadow_pipeline_dryrun_v1.md"


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def event_type_for_preflight(preflight_result: Dict[str, Any]) -> str:
    flags = set(preflight_result.get("policy_flags", []))
    decision = preflight_result.get("decision")
    if "unknown_capability" in flags:
        return "unknown_capability_event"
    if preflight_result.get("redaction_required"):
        return "redaction_required"
    if decision in {"deny", "require_approval"}:
        return "shadow_risk_event"
    return "none"


def runtime_action_for_preflight(preflight_result: Dict[str, Any]) -> str:
    decision = preflight_result.get("decision")
    if decision == "allow":
        if preflight_result.get("redaction_required"):
            return "record_redaction_requirement_and_continue"
        return "observe_and_continue"
    if decision in {"deny", "require_approval"}:
        return "record_shadow_risk_event_and_continue"
    return "record_preflight_unknown_decision"


def metric_increment_for_event(event: Dict[str, Any]) -> List[str]:
    increments = ["total_requests"]
    contract = event["contract_validation_result"]
    if contract["valid"]:
        increments.append("contract_valid_count")
    else:
        increments.extend(["contract_invalid_count", "blocked_before_evaluator_count"])
        if contract.get("errors"):
            increments.append("evaluator_error_like_issue_count")

    if event.get("preflight_result"):
        increments.append("passed_to_evaluator_count")
        preflight = event["preflight_result"]
        decision = preflight.get("decision")
        if decision == "allow":
            increments.append("allow_count")
        elif decision == "deny":
            increments.append("deny_count")
        elif decision == "require_approval":
            increments.append("require_approval_count")
        if preflight.get("redaction_required"):
            increments.append("redaction_required_count")
        if "unknown_capability" in preflight.get("policy_flags", []):
            increments.append("unknown_capability_count")

    return increments


def build_shadow_event(
    index: int,
    case: Dict[str, Any],
    contract_result: Dict[str, Any],
    preflight_result: Dict[str, Any] | None,
) -> Dict[str, Any]:
    if preflight_result is None:
        expected_runtime_action = "block_before_evaluator"
        shadow_event_type = "contract_validation_blocked"
    else:
        expected_runtime_action = runtime_action_for_preflight(preflight_result)
        shadow_event_type = event_type_for_preflight(preflight_result)

    event = {
        "event_id": f"PIPE-{index:03d}",
        "source_case_id": case.get("case_id"),
        "contract_validation_result": {
            "valid": contract_result["valid"],
            "warnings": contract_result["warnings"],
            "errors": contract_result["errors"],
            "recommended_next_step": contract_result["recommended_next_step"],
        },
        "preflight_result": preflight_result,
        "expected_runtime_action": expected_runtime_action,
        "shadow_event_type": shadow_event_type,
        "metric_increment": [],
    }
    event["metric_increment"] = metric_increment_for_event(event)
    return event


def run_pipeline(policy: Dict[str, Any], cases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    events = []
    for index, case in enumerate(cases, start=1):
        request = case.get("input_request", {})
        contract_result = validate_request(request, policy)
        preflight_result = None
        if contract_result["recommended_next_step"] == "pass_to_evaluator":
            preflight_result = evaluate_request(contract_result["normalized_request"], policy)
        events.append(build_shadow_event(index, case, contract_result, preflight_result))
    return events


def aggregate_pipeline_events(events: List[Dict[str, Any]]) -> Dict[str, int]:
    metrics = Counter()
    for event in events:
        for metric in event.get("metric_increment", []):
            metrics[metric] += 1
    metric_names = [
        "total_requests",
        "contract_valid_count",
        "contract_invalid_count",
        "passed_to_evaluator_count",
        "blocked_before_evaluator_count",
        "allow_count",
        "deny_count",
        "require_approval_count",
        "redaction_required_count",
        "unknown_capability_count",
        "evaluator_error_like_issue_count",
    ]
    return {name: metrics.get(name, 0) for name in metric_names}


def write_run_log(events: List[Dict[str, Any]], metrics: Dict[str, int]) -> None:
    lines = [
        "# Security Preflight Shadow Pipeline Dry-run v1",
        "",
        "## 本轮目标",
        "",
        "将本地 `tool_call_request` 样例串联为 contract validator → preflight evaluator → shadow event → metrics summary 的 dry-run pipeline。",
        "",
        "## 输入",
        "",
        f"- request cases: `{TEST_CASES_PATH.relative_to(ROOT.parent)}`",
        f"- policy: `{POLICY_PATH.relative_to(ROOT.parent)}`",
        "",
        "## 运行边界",
        "",
        "- real_runtime_connected: false",
        "- real_platform_called: false",
        "- real_api_called: false",
        "- auth_state_read: false",
        "- enforce_mode_enabled: false",
        "",
        "## 指标汇总",
        "",
        "| metric | value |",
        "|---|---:|",
    ]
    for name, value in metrics.items():
        lines.append(f"| {name} | {value} |")

    lines.extend(
        [
            "",
            "## Event 结果",
            "",
            "| event_id | source_case_id | contract_valid | contract_next_step | preflight_decision | shadow_event_type | runtime_action |",
            "|---|---|---|---|---|---|---|",
        ]
    )
    for event in events:
        preflight = event.get("preflight_result") or {}
        decision = preflight.get("decision", "not_evaluated")
        contract = event["contract_validation_result"]
        lines.append(
            f"| {event['event_id']} | {event['source_case_id']} | {str(contract['valid']).lower()} | {contract['recommended_next_step']} | {decision} | {event['shadow_event_type']} | {event['expected_runtime_action']} |"
        )

    lines.extend(
        [
            "",
            "## 结论",
            "",
            "- 合法 request 可进入 preflight evaluator。",
            "- 非法 request 在 evaluator 前被阻断，并生成 `contract_validation_blocked` shadow event。",
            "- 本轮只验证本地 pipeline 串联，不接真实 runtime，不进入 enforce mode。",
            "",
            "## 后续 TODO",
            "",
            "- 将 pipeline 接入真实 runtime 生成的 request 样本做 shadow 验证。",
            "- 将 contract validation 错误纳入 shadow metrics 日报。",
            "- 在 enforce 评审前补足 false positive 和 redaction gap 的人工复核流程。",
        ]
    )
    RUN_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    RUN_LOG_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def print_summary(metrics: Dict[str, int], events: List[Dict[str, Any]]) -> None:
    print("security_preflight_shadow_pipeline_dryrun")
    for name, value in metrics.items():
        print(f"{name}: {value}")
    print("events:")
    for event in events:
        decision = "not_evaluated"
        if event.get("preflight_result"):
            decision = event["preflight_result"].get("decision", "unknown")
        print(
            f"- {event['event_id']} {event['source_case_id']}: contract={event['contract_validation_result']['recommended_next_step']}, preflight={decision}, shadow_event={event['shadow_event_type']}"
        )
    print(f"run_log: {RUN_LOG_PATH}")


def main() -> int:
    policy = load_json(POLICY_PATH)
    cases = load_json(TEST_CASES_PATH)
    events = run_pipeline(policy, cases)
    metrics = aggregate_pipeline_events(events)
    write_run_log(events, metrics)
    print_summary(metrics, events)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
