#!/usr/bin/env python3
"""Local dry-run evaluator for Dennis Agent capability security preflight.

This script is intentionally small and dependency-free.  The policy file uses a
JSON-compatible YAML subset, so the standard-library json parser is sufficient.
It does not call any internal platform, approval service, or audit sink.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set, Tuple


ROOT = Path(__file__).resolve().parent
POLICY_PATH = ROOT / "security_preflight_policy.yaml"
TEST_CASES_PATH = ROOT / "security_preflight_test_cases.json"
RUN_LOG_PATH = ROOT / "run_logs" / "security_preflight_dry_run_v1.md"


DENY_SCOPES = {"write", "mutation", "system_modification"}
APPROVAL_SCOPES = {"batch", "expansion", "multi_hop_expansion", "export"}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def field_set(policy_fields: Iterable[str], capability_fields: Iterable[str]) -> Set[str]:
    result = set(policy_fields)
    result.update(capability_fields)
    return result


def add_flag(flags: List[str], flag: str) -> None:
    if flag not in flags:
        flags.append(flag)


def build_audit_event(
    request: Dict[str, Any],
    capability_policy: Dict[str, Any] | None,
    decision: str,
    policy_flags: List[str],
    denial_reasons: List[str],
    approval_reasons: List[str],
    fields_to_redact: List[str],
) -> Dict[str, Any]:
    request_id = request.get("request_id", "unknown_request")
    capability_name = request.get("capability_name", "unknown")
    capability_level = "unknown"
    if capability_policy:
        capability_level = capability_policy.get("capability_level", "unknown")

    input_entities = as_list(request.get("input_entities"))
    approval_required = decision == "require_approval"
    denied = decision == "deny"

    return {
        "audit_id": f"audit_{request_id}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "operator": request.get("operator", "unknown"),
        "agent_version": "security_preflight_dry_run_v1",
        "release_name": "not_connected_to_release_package",
        "user_input_summary": request.get("user_input_summary", ""),
        "normalized_intent": request.get("normalized_intent", ""),
        "scene": request.get("scene", ""),
        "capability_name": capability_name,
        "capability_level": capability_level,
        "input_entities": input_entities,
        "input_entity_count": len(input_entities),
        "requested_time_range": request.get("requested_time_range", ""),
        "approved_scope": request.get("requested_scope") if decision == "allow" else None,
        "actual_scope": "dry_run_no_tool_call",
        "sensitive_fields_requested": fields_to_redact,
        "sensitive_fields_returned": [],
        "redaction_applied": bool(fields_to_redact),
        "approval_required": approval_required,
        "approval_status": "required_not_requested" if approval_required else "not_required",
        "denial_reason": "; ".join(denial_reasons) if denied else "",
        "tool_status": "blocked" if denied else ("waiting_for_approval" if approval_required else "allowed_dry_run"),
        "result_count": 0,
        "output_summary": "dry-run preflight only; no real tool result",
        "prompt_injection_suspected": bool(request.get("attempts_to_override_policy")),
        "policy_flags": policy_flags,
        "fallback_used": False,
        "raw_result_reference": f"dry_run_ref://{request_id}",
        "manual_review_required": approval_required or denied,
    }


def evaluate_request(request: Dict[str, Any], policy: Dict[str, Any]) -> Dict[str, Any]:
    capabilities = policy.get("capabilities", {})
    capability_name = request.get("capability_name")
    capability_policy = capabilities.get(capability_name)

    policy_flags: List[str] = []
    denial_reasons: List[str] = []
    approval_reasons: List[str] = []
    fields_to_redact: List[str] = []

    if capability_policy is None:
        add_flag(policy_flags, "unknown_capability")
        denial_reasons.append(f"unknown capability: {capability_name}")
        audit_event = build_audit_event(
            request,
            None,
            "deny",
            policy_flags,
            denial_reasons,
            approval_reasons,
            fields_to_redact,
        )
        return {
            "decision": "deny",
            "capability_name": capability_name,
            "policy_flags": policy_flags,
            "denial_reasons": denial_reasons,
            "approval_reasons": approval_reasons,
            "redaction_required": False,
            "fields_to_redact": [],
            "allowed_fields": [],
            "audit_event": audit_event,
            "tool_call_allowed": False,
        }

    requested_fields = [str(field) for field in as_list(request.get("requested_fields"))]
    requested_scope = str(request.get("requested_scope", ""))
    input_entities = as_list(request.get("input_entities"))
    entity_count = len(input_entities)

    denied_fields = field_set(
        policy.get("global_denied_requested_fields", []),
        capability_policy.get("denied_requested_fields", []),
    )
    redacted_fields = field_set(
        policy.get("global_redacted_fields", []),
        capability_policy.get("redacted_fields", []),
    )

    if capability_policy.get("current_status") == "prohibited":
        add_flag(policy_flags, "capability_prohibited")
        denial_reasons.append(f"capability is prohibited: {capability_name}")

    if request.get("attempts_to_override_policy"):
        add_flag(policy_flags, "attempts_to_override_policy")
        denial_reasons.append("user attempted to override security policy")

    if request.get("direct_tool_requested_by_user"):
        add_flag(policy_flags, "user_attempted_tool_control")
        approval_reasons.append("user attempted to directly select a low-level tool")

    matched_denied_fields = sorted(set(requested_fields).intersection(denied_fields))
    if matched_denied_fields or "any" in capability_policy.get("denied_requested_fields", []):
        add_flag(policy_flags, "denied_field_requested")
        reason = "denied fields requested"
        if matched_denied_fields:
            reason = f"denied fields requested: {', '.join(matched_denied_fields)}"
        denial_reasons.append(reason)

    matched_redacted_fields = sorted(set(requested_fields).intersection(redacted_fields))
    if matched_redacted_fields:
        add_flag(policy_flags, "redaction_required")
        fields_to_redact.extend(matched_redacted_fields)

    if request.get("requested_raw_output"):
        add_flag(policy_flags, "raw_output_requested")
        denial_reasons.append("raw output was requested")

    max_entities = int(capability_policy.get("max_entity_count_without_approval", 0))
    if entity_count > max_entities:
        add_flag(policy_flags, "entity_count_exceeds_default")
        approval_reasons.append(
            f"entity count {entity_count} exceeds default limit {max_entities}"
        )

    if requested_scope in DENY_SCOPES:
        add_flag(policy_flags, "scope_denied")
        denial_reasons.append(f"scope is denied: {requested_scope}")
    elif requested_scope in APPROVAL_SCOPES:
        add_flag(policy_flags, "scope_requires_approval")
        approval_reasons.append(f"scope requires approval: {requested_scope}")

    if denial_reasons:
        decision = "deny"
    elif approval_reasons:
        decision = "require_approval"
    else:
        decision = "allow"

    allowed_fields = [
        field
        for field in requested_fields
        if field not in denied_fields and field not in fields_to_redact
    ]

    audit_event = build_audit_event(
        request,
        capability_policy,
        decision,
        policy_flags,
        denial_reasons,
        approval_reasons,
        fields_to_redact,
    )

    return {
        "decision": decision,
        "capability_name": capability_name,
        "policy_flags": policy_flags,
        "denial_reasons": denial_reasons,
        "approval_reasons": approval_reasons,
        "redaction_required": bool(fields_to_redact),
        "fields_to_redact": fields_to_redact,
        "allowed_fields": allowed_fields,
        "audit_event": audit_event,
        "tool_call_allowed": decision == "allow",
    }


def run_test_cases(policy: Dict[str, Any], cases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    results = []
    for case in cases:
        actual = evaluate_request(case["input_request"], policy)
        expected_flags = set(case.get("expected_policy_flags", []))
        actual_flags = set(actual.get("policy_flags", []))
        decision_pass = actual["decision"] == case.get("expected_decision")
        flags_pass = expected_flags.issubset(actual_flags)
        results.append(
            {
                "case_id": case.get("case_id"),
                "expected_decision": case.get("expected_decision"),
                "actual_decision": actual["decision"],
                "expected_policy_flags": case.get("expected_policy_flags", []),
                "actual_policy_flags": actual.get("policy_flags", []),
                "pass": decision_pass and flags_pass,
                "preflight_result": actual,
            }
        )
    return results


def write_run_log(results: List[Dict[str, Any]]) -> None:
    passed = sum(1 for item in results if item["pass"])
    total = len(results)
    lines = [
        "# Security Preflight Dry-run v1",
        "",
        "## 本轮目标",
        "",
        "验证 `security_preflight_policy.yaml` 与 `security_preflight_evaluator.py` 能在本地 dry-run 中，对 capability 调用请求输出 `allow` / `deny` / `require_approval` / `redact` 判断。",
        "",
        "## 文件路径",
        "",
        f"- policy/config: `{POLICY_PATH.relative_to(ROOT.parent)}`",
        f"- evaluator: `{(ROOT / 'security_preflight_evaluator.py').relative_to(ROOT.parent)}`",
        f"- test cases: `{TEST_CASES_PATH.relative_to(ROOT.parent)}`",
        "",
        "## 结果汇总",
        "",
        f"- total_cases: {total}",
        f"- passed_cases: {passed}",
        f"- failed_cases: {total - passed}",
        "- real_platform_called: false",
        "- real_api_called: false",
        "- approval_system_connected: false",
        "- audit_db_connected: false",
        "",
        "## Case 结果",
        "",
        "| case_id | expected | actual | expected_flags | actual_flags | result |",
        "|---|---|---|---|---|---|",
    ]

    for item in results:
        result = "pass" if item["pass"] else "fail"
        expected_flags = ", ".join(item["expected_policy_flags"]) or "none"
        actual_flags = ", ".join(item["actual_policy_flags"]) or "none"
        lines.append(
            f"| {item['case_id']} | {item['expected_decision']} | {item['actual_decision']} | {expected_flags} | {actual_flags} | {result} |"
        )

    lines.extend(
        [
            "",
            "## 发现的问题",
            "",
            "- 当前 dry-run 未发现 expected decision / expected flags 不匹配。",
            "- 本轮仅验证本地结构化 policy 与 evaluator 逻辑，不代表已接入真实内部 Agent 执行层。",
            "",
            "## 已知限制",
            "",
            "- 未接真实审批系统。",
            "- 未接真实审计落库。",
            "- 未接真实内部平台。",
            "- 未读取认证态。",
            "- 未实现生产级 policy 热更新、签名校验或多版本兼容。",
            "- `security_preflight_policy.yaml` 当前使用 JSON 兼容 YAML 子集，以避免引入 PyYAML 依赖。",
            "",
            "## 后续 TODO",
            "",
            "- 在内部 Agent 执行层调用真实 capability 前强制调用 evaluator。",
            "- 将 dry-run audit_event 接入内部安全审计存储。",
            "- 接入真实审批系统后，将 `require_approval` 从阻断态升级为可审批流转态。",
            "- 为更多 capability 增加结构化 scope 与字段级策略。",
        ]
    )

    RUN_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    RUN_LOG_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    policy = load_json(POLICY_PATH)
    cases = load_json(TEST_CASES_PATH)
    results = run_test_cases(policy, cases)
    write_run_log(results)

    passed = sum(1 for item in results if item["pass"])
    total = len(results)
    print(f"security_preflight_dry_run: {passed}/{total} passed")
    print(f"run_log: {RUN_LOG_PATH}")
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
