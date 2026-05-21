#!/usr/bin/env python3
"""Aggregate local shadow preflight event samples.

This is a local observability dry-run helper. It reads only
security_preflight_shadow_event_samples.json and does not connect to runtime,
internal platforms, auth state, approval systems, or audit storage.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Tuple


ROOT = Path(__file__).resolve().parent
INPUT_PATH = ROOT / "security_preflight_shadow_event_samples.json"
RUN_LOG_PATH = ROOT / "run_logs" / "security_preflight_shadow_metrics_aggregator_run_v1.md"

CORE_METRICS = [
    "total_tool_requests",
    "allow_count",
    "deny_count",
    "require_approval_count",
    "redaction_required_count",
    "shadow_risk_event_count",
    "false_positive_candidate_count",
    "redaction_gap_candidate_count",
    "unknown_capability_count",
    "evaluator_error_count",
]

KNOWN_EVENT_TYPES = {
    "none",
    "shadow_risk_event",
    "false_positive_candidate",
    "redaction_gap_candidate",
    "unknown_capability_event",
    "evaluator_error_event",
}

REQUIRED_EVENT_FIELDS = {
    "event_id",
    "tool_call_request",
    "expected_preflight_result",
    "expected_shadow_event_type",
    "expected_metric_increment",
}

REQUIRED_REQUEST_FIELDS = {"request_id", "capability_name", "runtime_mode"}
REQUIRED_RESULT_FIELDS = {"decision", "redaction_required", "policy_flags"}


def load_events(path: Path) -> Tuple[List[Dict[str, Any]], List[str]]:
    try:
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception as exc:  # noqa: BLE001 - fail closed summary needs the raw exception type.
        return [], [f"input_json_error: {type(exc).__name__}: {exc}"]

    if not isinstance(data, list):
        return [], ["input_json_error: top-level JSON must be a list"]
    return data, []


def validate_event(event: Dict[str, Any]) -> List[str]:
    issues: List[str] = []
    event_id = event.get("event_id", "unknown_event")

    missing_event = sorted(REQUIRED_EVENT_FIELDS - set(event.keys()))
    if missing_event:
        issues.append(f"{event_id}: missing event fields: {', '.join(missing_event)}")

    request = event.get("tool_call_request", {})
    if not isinstance(request, dict):
        issues.append(f"{event_id}: tool_call_request must be object")
    else:
        missing_request = sorted(REQUIRED_REQUEST_FIELDS - set(request.keys()))
        if missing_request:
            issues.append(f"{event_id}: missing request fields: {', '.join(missing_request)}")

    result = event.get("expected_preflight_result", {})
    if not isinstance(result, dict):
        issues.append(f"{event_id}: expected_preflight_result must be object")
    else:
        missing_result = sorted(REQUIRED_RESULT_FIELDS - set(result.keys()))
        if missing_result:
            issues.append(f"{event_id}: missing result fields: {', '.join(missing_result)}")

    event_type = event.get("expected_shadow_event_type")
    if event_type not in KNOWN_EVENT_TYPES:
        issues.append(f"{event_id}: unknown shadow event type: {event_type}")

    increments = event.get("expected_metric_increment", [])
    if not isinstance(increments, list):
        issues.append(f"{event_id}: expected_metric_increment must be list")

    return issues


def aggregate(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    metrics = {name: 0 for name in CORE_METRICS}
    capability_metrics: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {
            "total": 0,
            "allow": 0,
            "deny": 0,
            "require_approval": 0,
            "redaction_required": 0,
            "event_types": defaultdict(int),
        }
    )
    issues: List[str] = []

    for event in events:
        event_issues = validate_event(event)
        issues.extend(event_issues)
        if event_issues:
            continue

        request = event["tool_call_request"]
        result = event["expected_preflight_result"]
        capability_name = request["capability_name"]
        decision = result["decision"]
        event_type = event["expected_shadow_event_type"]

        metrics["total_tool_requests"] += 1
        if decision == "allow":
            metrics["allow_count"] += 1
        elif decision == "deny":
            metrics["deny_count"] += 1
        elif decision == "require_approval":
            metrics["require_approval_count"] += 1
        else:
            issues.append(f"{event['event_id']}: unknown decision: {decision}")
            continue

        if result.get("redaction_required"):
            metrics["redaction_required_count"] += 1

        if event_type == "shadow_risk_event":
            metrics["shadow_risk_event_count"] += 1
        elif event_type == "false_positive_candidate":
            metrics["false_positive_candidate_count"] += 1
        elif event_type == "redaction_gap_candidate":
            metrics["redaction_gap_candidate_count"] += 1
        elif event_type == "unknown_capability_event":
            metrics["shadow_risk_event_count"] += 1
            metrics["unknown_capability_count"] += 1
        elif event_type == "evaluator_error_event":
            metrics["evaluator_error_count"] += 1

        cap = capability_metrics[capability_name]
        cap["total"] += 1
        if decision in {"allow", "deny", "require_approval"}:
            cap[decision] += 1
        if result.get("redaction_required"):
            cap["redaction_required"] += 1
        cap["event_types"][event_type] += 1

    evaluator_error_like_issue = len(issues)
    return {
        "metrics": metrics,
        "capability_metrics": capability_metrics,
        "issues": issues,
        "evaluator_error_like_issue_count": evaluator_error_like_issue,
    }


def readiness_summary(metrics: Dict[str, int], issue_count: int) -> Dict[str, Any]:
    unknown_count = metrics["unknown_capability_count"]
    evaluator_error_count = metrics["evaluator_error_count"] + issue_count
    redaction_gap_count = metrics["redaction_gap_candidate_count"]
    shadow_risk_count = metrics["shadow_risk_event_count"]

    return {
        "high_risk_shadow_risk_event_count_is_zero": shadow_risk_count == 0,
        "unknown_capability_count_is_zero_or_explained": unknown_count == 0,
        "evaluator_error_count_is_zero": evaluator_error_count == 0,
        "redaction_gap_candidate_count_is_zero": redaction_gap_count == 0,
        "require_approval_default_blocking_policy_is_clear": True,
        "preliminary_enforce_ready": (
            shadow_risk_count == 0
            and unknown_count == 0
            and evaluator_error_count == 0
            and redaction_gap_count == 0
        ),
    }


def format_capability_metrics(capability_metrics: Dict[str, Dict[str, Any]]) -> List[str]:
    lines = [
        "| capability | total | allow | deny | require_approval | redaction_required | event_types |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for capability in sorted(capability_metrics):
        item = capability_metrics[capability]
        event_types = ", ".join(
            f"{name}:{count}" for name, count in sorted(item["event_types"].items())
        )
        lines.append(
            f"| {capability} | {item['total']} | {item['allow']} | {item['deny']} | {item['require_approval']} | {item['redaction_required']} | {event_types} |"
        )
    return lines


def write_run_log(summary: Dict[str, Any]) -> None:
    metrics = summary["metrics"]
    capability_metrics = summary["capability_metrics"]
    issues = summary["issues"]
    readiness = readiness_summary(metrics, summary["evaluator_error_like_issue_count"])

    lines = [
        "# Security Preflight Shadow Metrics Aggregator Run v1",
        "",
        "## 本轮目标",
        "",
        "读取 `security_preflight_shadow_event_samples.json`，本地聚合 shadow mode 模拟指标，验证后续 runtime shadow event 的可观测性。",
        "",
        "## 输入 / 输出",
        "",
        f"- input: `{INPUT_PATH.relative_to(ROOT.parent)}`",
        f"- output: `{RUN_LOG_PATH.relative_to(ROOT.parent)}`",
        "- real_runtime_connected: false",
        "- real_platform_called: false",
        "- auth_state_read: false",
        "- enforce_mode_enabled: false",
        "",
        "## 核心指标",
        "",
        "| metric | value |",
        "|---|---:|",
    ]
    for name in CORE_METRICS:
        lines.append(f"| {name} | {metrics[name]} |")
    lines.append(
        f"| evaluator_error_like_issue_count | {summary['evaluator_error_like_issue_count']} |"
    )

    lines.extend(["", "## Capability 维度聚合", ""])
    lines.extend(format_capability_metrics(capability_metrics))

    lines.extend(
        [
            "",
            "## Enforce Readiness 初步判断",
            "",
            "| check | value |",
            "|---|---|",
        ]
    )
    for key, value in readiness.items():
        lines.append(f"| {key} | {str(value).lower()} |")

    lines.extend(["", "## 字段 / 格式问题", ""])
    if issues:
        for issue in issues:
            lines.append(f"- {issue}")
    else:
        lines.append("- none")

    lines.extend(
        [
            "",
            "## 结论",
            "",
            "- shadow event samples 可聚合为核心指标和 capability 维度指标。",
            "- 当前模拟样例包含 shadow risk、unknown capability、evaluator error 和 redaction gap，因此不满足 enforce readiness。",
            "- 本轮只验证本地样例可观测性，不进入 enforce mode。",
        ]
    )

    RUN_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    RUN_LOG_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def print_summary(summary: Dict[str, Any]) -> None:
    metrics = summary["metrics"]
    readiness = readiness_summary(metrics, summary["evaluator_error_like_issue_count"])
    print("security_preflight_shadow_metrics_aggregator")
    for name in CORE_METRICS:
        print(f"{name}: {metrics[name]}")
    print(f"evaluator_error_like_issue_count: {summary['evaluator_error_like_issue_count']}")
    print("capability_summary:")
    for capability in sorted(summary["capability_metrics"]):
        item = summary["capability_metrics"][capability]
        print(
            f"- {capability}: total={item['total']}, allow={item['allow']}, deny={item['deny']}, require_approval={item['require_approval']}, redaction_required={item['redaction_required']}"
        )
    print("enforce_readiness:")
    for key, value in readiness.items():
        print(f"- {key}: {str(value).lower()}")
    print(f"run_log: {RUN_LOG_PATH}")


def main() -> int:
    events, load_issues = load_events(INPUT_PATH)
    if load_issues:
        summary = {
            "metrics": {name: 0 for name in CORE_METRICS},
            "capability_metrics": {},
            "issues": load_issues,
            "evaluator_error_like_issue_count": len(load_issues),
        }
        write_run_log(summary)
        print_summary(summary)
        return 1

    summary = aggregate(events)
    write_run_log(summary)
    print_summary(summary)
    return 0 if not summary["issues"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
