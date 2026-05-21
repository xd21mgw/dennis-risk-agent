#!/usr/bin/env python3
"""Dry-run normal business tool_call_request samples through preflight pipeline.

This script validates that common readonly business requests are not broadly
misblocked while batch, expansion, cross-platform, and sensitive field requests
still receive approval or redaction decisions.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List

from security_preflight_evaluator import evaluate_request
from security_preflight_request_contract_validator import validate_request


ROOT = Path(__file__).resolve().parent
POLICY_PATH = ROOT / "security_preflight_policy.yaml"
SAMPLES_PATH = ROOT / "security_preflight_normal_business_request_samples.json"
RUN_LOG_PATH = ROOT / "run_logs" / "security_preflight_normal_business_pipeline_dryrun_v1.md"


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def runtime_action(preflight_result: Dict[str, Any] | None) -> str:
    if preflight_result is None:
        return "block_before_evaluator"
    decision = preflight_result.get("decision")
    if decision == "allow":
        if preflight_result.get("redaction_required"):
            return "record_redaction_requirement"
        return "observe_and_continue"
    if decision in {"deny", "require_approval"}:
        return "record_shadow_risk_event_and_continue"
    return "unknown_runtime_action"


def run_pipeline(policy: Dict[str, Any], samples: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    results = []
    for sample in samples:
        request = sample["tool_call_request"]
        contract = validate_request(request, policy)
        preflight = None
        if contract["recommended_next_step"] == "pass_to_evaluator":
            preflight = evaluate_request(contract["normalized_request"], policy)

        actual_decision = preflight.get("decision") if preflight else "not_evaluated"
        actual_action = runtime_action(preflight)
        expected_decision = sample.get("expected_preflight_decision")
        expected_action = sample.get("expected_runtime_action")

        false_positive = expected_decision == "allow" and actual_decision != "allow"
        false_negative = expected_decision in {"deny", "require_approval"} and actual_decision == "allow"
        redaction_gap = expected_action == "record_redaction_requirement" and (
            not preflight or not preflight.get("redaction_required")
        )

        results.append(
            {
                "case_id": sample["case_id"],
                "capability_name": request.get("capability_name"),
                "expected_contract_result": sample.get("expected_contract_result"),
                "actual_contract_result": contract["recommended_next_step"],
                "contract_valid": contract["valid"],
                "expected_decision": expected_decision,
                "actual_decision": actual_decision,
                "expected_runtime_action": expected_action,
                "actual_runtime_action": actual_action,
                "false_positive_candidate": false_positive,
                "false_negative_candidate": false_negative,
                "redaction_gap_candidate": redaction_gap,
                "contract_result": contract,
                "preflight_result": preflight,
                "notes": sample.get("notes", ""),
            }
        )
    return results


def aggregate(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    metrics = Counter()
    capability = defaultdict(Counter)

    for item in results:
        metrics["total_samples"] += 1
        if item["contract_valid"]:
            metrics["contract_valid_count"] += 1
        else:
            metrics["contract_invalid_count"] += 1
        if item["actual_contract_result"] == "pass_to_evaluator":
            metrics["passed_to_evaluator_count"] += 1
        else:
            metrics["blocked_before_evaluator_count"] += 1

        decision = item["actual_decision"]
        if decision == "allow":
            metrics["allow_count"] += 1
        elif decision == "deny":
            metrics["deny_count"] += 1
        elif decision == "require_approval":
            metrics["require_approval_count"] += 1

        preflight = item.get("preflight_result") or {}
        if preflight.get("redaction_required"):
            metrics["redaction_required_count"] += 1
        if item["false_positive_candidate"]:
            metrics["false_positive_candidate_count"] += 1
        if item["false_negative_candidate"]:
            metrics["false_negative_candidate_count"] += 1
        if item["redaction_gap_candidate"]:
            metrics["redaction_gap_candidate_count"] += 1

        cap = capability[item["capability_name"]]
        cap["total"] += 1
        cap[decision] += 1
        if preflight.get("redaction_required"):
            cap["redaction_required"] += 1

    return {"metrics": metrics, "capability_metrics": capability}


def write_run_log(results: List[Dict[str, Any]], summary: Dict[str, Any]) -> None:
    metrics = summary["metrics"]
    capability_metrics = summary["capability_metrics"]
    normal_single_point_misblocked = [
        item for item in results if item["expected_decision"] == "allow" and item["actual_decision"] != "allow"
    ]
    batch_or_expansion_leak = [
        item
        for item in results
        if item["expected_decision"] == "require_approval" and item["actual_decision"] == "allow"
    ]
    redaction_gaps = [item for item in results if item["redaction_gap_candidate"]]

    lines = [
        "# Security Preflight Normal Business Pipeline Dry-run v1",
        "",
        "## 本轮目标",
        "",
        "验证 Dennis Agent 常见只读研判请求不会被安全框架大量误拦，同时批量、扩散、多平台串联和敏感字段请求仍进入审批或脱敏。",
        "",
        "## 输入",
        "",
        f"- samples: `{SAMPLES_PATH.relative_to(ROOT.parent)}`",
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
    for name in [
        "total_samples",
        "contract_valid_count",
        "contract_invalid_count",
        "passed_to_evaluator_count",
        "blocked_before_evaluator_count",
        "allow_count",
        "require_approval_count",
        "deny_count",
        "redaction_required_count",
        "false_positive_candidate_count",
        "false_negative_candidate_count",
        "redaction_gap_candidate_count",
    ]:
        lines.append(f"| {name} | {metrics.get(name, 0)} |")

    lines.extend(["", "## Capability 维度摘要", ""])
    lines.extend(
        [
            "| capability | total | allow | require_approval | deny | redaction_required |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for cap_name in sorted(capability_metrics):
        item = capability_metrics[cap_name]
        lines.append(
            f"| {cap_name} | {item.get('total', 0)} | {item.get('allow', 0)} | {item.get('require_approval', 0)} | {item.get('deny', 0)} | {item.get('redaction_required', 0)} |"
        )

    lines.extend(
        [
            "",
            "## Case 结果",
            "",
            "| case_id | capability | contract | expected_decision | actual_decision | runtime_action | false_positive | false_negative | redaction_gap |",
            "|---|---|---|---|---|---|---|---|---|",
        ]
    )
    for item in results:
        lines.append(
            f"| {item['case_id']} | {item['capability_name']} | {item['actual_contract_result']} | {item['expected_decision']} | {item['actual_decision']} | {item['actual_runtime_action']} | {str(item['false_positive_candidate']).lower()} | {str(item['false_negative_candidate']).lower()} | {str(item['redaction_gap_candidate']).lower()} |"
        )

    lines.extend(
        [
            "",
            "## 结论",
            "",
            f"- normal_single_point_misblocked_count: {len(normal_single_point_misblocked)}",
            f"- batch_or_expansion_unapproved_leak_count: {len(batch_or_expansion_leak)}",
            f"- redaction_gap_count: {len(redaction_gaps)}",
            "- 本轮只验证本地正常业务样例，不接真实 runtime，不进入 enforce mode。",
            "",
            "## 后续 TODO",
            "",
            "- 用真实 Agent 生成的正常业务 request 样本继续跑 pipeline。",
            "- 若 false positive 出现，优先修 request mapping 或 policy scope，而不是放宽安全边界。",
            "- 若 false negative 出现，优先补 policy / evaluator approval scopes。",
        ]
    )
    RUN_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    RUN_LOG_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def print_summary(results: List[Dict[str, Any]], summary: Dict[str, Any]) -> None:
    metrics = summary["metrics"]
    print("security_preflight_normal_business_pipeline_dryrun")
    for name in [
        "total_samples",
        "contract_valid_count",
        "contract_invalid_count",
        "passed_to_evaluator_count",
        "blocked_before_evaluator_count",
        "allow_count",
        "require_approval_count",
        "deny_count",
        "redaction_required_count",
        "false_positive_candidate_count",
        "false_negative_candidate_count",
        "redaction_gap_candidate_count",
    ]:
        print(f"{name}: {metrics.get(name, 0)}")
    print("cases:")
    for item in results:
        print(
            f"- {item['case_id']} {item['capability_name']}: contract={item['actual_contract_result']}, preflight={item['actual_decision']}, action={item['actual_runtime_action']}"
        )
    print(f"run_log: {RUN_LOG_PATH}")


def main() -> int:
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    samples = load_json(SAMPLES_PATH)
    results = run_pipeline(policy, samples)
    summary = aggregate(results)
    write_run_log(results, summary)
    print_summary(results, summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
