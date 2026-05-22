#!/usr/bin/env python3
"""Validate local tool_call_request contract samples.

This validator checks request shape and safety-field quality only. It does not
call the preflight evaluator, runtime, internal platforms, auth state, approval
systems, or audit storage.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple


ROOT = Path(__file__).resolve().parent
POLICY_PATH = ROOT / "security_preflight_policy.yaml"
TEST_CASES_PATH = ROOT / "security_preflight_request_contract_test_cases.json"
RUN_LOG_PATH = ROOT / "run_logs" / "security_preflight_request_contract_validator_run_v1.md"

REQUIRED_FIELDS = [
    "request_id",
    "operator",
    "user_input_summary",
    "normalized_intent",
    "scene",
    "capability_name",
    "input_entities",
    "input_entity_count",
    "requested_fields",
    "requested_scope",
    "requested_time_range",
    "direct_tool_requested_by_user",
    "attempts_to_override_policy",
    "requested_raw_output",
    "source_agent",
    "runtime_mode",
]

BOOL_FIELDS = [
    "direct_tool_requested_by_user",
    "attempts_to_override_policy",
    "requested_raw_output",
]

ENTITY_REQUIRED_FIELDS = {
    "entity_type",
    "entity_value",
    "is_sensitive",
    "source",
    "confidence",
}

SCOPE_ENUM = {
    "single_entity",
    "small_scope",
    "multi_entity",
    "batch",
    "expansion",
    "cross_platform",
    "system_modification",
    "unknown",
}

SENSITIVE_ENTITY_TYPES = {"user_id", "device_id", "phone", "ip"}
SAFE_SUMMARY_FIELDS = ["risk_summary"]
RAW_PLATFORM_CAPABILITY_PATTERNS = (
    "weapon_",
    "archives_any",
    "tianshi_free",
    "browser_execute",
    "api_any",
)


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def load_policy() -> Dict[str, Any]:
    return load_json(POLICY_PATH)


def prohibited_fields(policy: Dict[str, Any]) -> Set[str]:
    fields = set(policy.get("global_denied_requested_fields", []))
    for capability in policy.get("capabilities", {}).values():
        fields.update(capability.get("denied_requested_fields", []))
    fields.discard("any")
    return fields


def normalize_request(request: Dict[str, Any]) -> Dict[str, Any]:
    normalized = dict(request)
    if "request_id" not in normalized:
        normalized["request_id"] = "tmp_request_id_generated_by_contract_validator"
    if "requested_scope" not in normalized:
        normalized["requested_scope"] = "unknown"
    if "requested_fields" not in normalized:
        normalized["requested_fields"] = SAFE_SUMMARY_FIELDS[:]
    if "input_entities" in normalized and "input_entity_count" not in normalized:
        entities = normalized.get("input_entities")
        normalized["input_entity_count"] = len(entities) if isinstance(entities, list) else 0
    return normalized


def choose_next_step(errors: List[str], warnings: List[str]) -> str:
    if any(error in {"capability_name_missing", "unknown_capability", "prohibited_field_requested"} for error in errors):
        return "deny"
    if "input_entities_missing" in errors:
        return "require_clarification"
    if errors:
        return "fix_request_mapping"
    return "pass_to_evaluator"


def validate_request(request: Dict[str, Any], policy: Dict[str, Any]) -> Dict[str, Any]:
    errors: List[str] = []
    warnings: List[str] = []
    normalized = normalize_request(request)

    missing_fields = [field for field in REQUIRED_FIELDS if field not in request]
    for field in missing_fields:
        if field == "request_id":
            warnings.append("request_id_missing_generated_temp_id")
        elif field == "requested_fields":
            warnings.append("requested_fields_missing_safe_summary_only")
        elif field == "requested_scope":
            errors.append("requested_scope_missing")
        elif field == "input_entities":
            errors.append("input_entities_missing")
        elif field == "capability_name":
            errors.append("capability_name_missing")
        else:
            warnings.append(f"{field}_missing")

    capability_name = normalized.get("capability_name")
    capabilities = policy.get("capabilities", {})
    if capability_name:
        if capability_name not in capabilities:
            errors.append("unknown_capability")
        if isinstance(capability_name, str) and capability_name.startswith(RAW_PLATFORM_CAPABILITY_PATTERNS):
            errors.append("raw_platform_name_used_as_capability")

    requested_scope = normalized.get("requested_scope")
    if requested_scope not in SCOPE_ENUM:
        errors.append("requested_scope_invalid")

    requested_fields = normalized.get("requested_fields")
    if not isinstance(requested_fields, list):
        errors.append("requested_fields_type_error")
        requested_fields_list: List[str] = []
    else:
        requested_fields_list = [str(field) for field in requested_fields]

    matched_prohibited = sorted(set(requested_fields_list).intersection(prohibited_fields(policy)))
    if matched_prohibited:
        errors.append("prohibited_field_requested")

    entities = normalized.get("input_entities")
    if not isinstance(entities, list):
        errors.append("input_entities_type_error")
        entities_list: List[Dict[str, Any]] = []
    else:
        entities_list = entities

    input_entity_count = normalized.get("input_entity_count")
    if not isinstance(input_entity_count, int):
        errors.append("input_entity_count_type_error")
    elif input_entity_count != len(entities_list):
        errors.append("entity_count_mismatch")

    for field in BOOL_FIELDS:
        if field in normalized and not isinstance(normalized[field], bool):
            errors.append(f"{field}_type_error")

    for index, entity in enumerate(entities_list):
        if not isinstance(entity, dict):
            errors.append(f"entity_{index}_type_error")
            continue
        missing_entity_fields = sorted(ENTITY_REQUIRED_FIELDS - set(entity.keys()))
        if missing_entity_fields:
            errors.append(f"entity_{index}_missing_fields:{','.join(missing_entity_fields)}")
            continue
        if not isinstance(entity.get("is_sensitive"), bool):
            errors.append(f"entity_{index}_is_sensitive_type_error")
        entity_type = entity.get("entity_type")
        if entity_type in SENSITIVE_ENTITY_TYPES and entity.get("is_sensitive") is not True:
            errors.append("sensitive_entity_not_marked")

    recommended_next_step = choose_next_step(errors, warnings)
    valid = not errors

    return {
        "valid": valid,
        "warnings": warnings,
        "errors": errors,
        "normalized_request": normalized,
        "recommended_next_step": recommended_next_step,
    }


def run_cases(policy: Dict[str, Any], cases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    results = []
    for case in cases:
        result = validate_request(case.get("input_request", {}), policy)
        expected_valid = case.get("expected_valid")
        expected_next_step = case.get("expected_recommended_next_step")
        passed = result["valid"] == expected_valid and result["recommended_next_step"] == expected_next_step
        results.append(
            {
                "case_id": case.get("case_id"),
                "description": case.get("description"),
                "expected_valid": expected_valid,
                "actual_valid": result["valid"],
                "expected_next_step": expected_next_step,
                "actual_next_step": result["recommended_next_step"],
                "warnings": result["warnings"],
                "errors": result["errors"],
                "pass": passed,
                "validation_result": result,
            }
        )
    return results


def write_run_log(results: List[Dict[str, Any]]) -> None:
    total = len(results)
    passed = sum(1 for item in results if item["pass"])
    next_steps = Counter(item["actual_next_step"] for item in results)
    warning_types = Counter(warning for item in results for warning in item["warnings"])
    error_types = Counter(error for item in results for error in item["errors"])

    lines = [
        "# Security Preflight Request Contract Validator Run v1",
        "",
        "## 本轮目标",
        "",
        "校验本地 `tool_call_request` 样例的字段完整性和安全字段质量，用于后续接 runtime 前降低 `evaluator_error_like_issue`。",
        "",
        "## 新增文件",
        "",
        "- `computer_use_poc/security_preflight_request_contract_validator.py`",
        "- `computer_use_poc/security_preflight_request_contract_test_cases.json`",
        "- `computer_use_poc/run_logs/security_preflight_request_contract_validator_run_v1.md`",
        "",
        "## Case 覆盖范围",
        "",
        "- 完整合法 user_profile_read",
        "- 完整合法 login_log_read",
        "- 缺 capability_name",
        "- unknown capability",
        "- requested_scope 缺失 / 非法",
        "- requested_fields 缺失",
        "- input_entities 缺失",
        "- input_entity_count 不一致",
        "- bool 字段类型错误",
        "- prohibited field 请求",
        "- 敏感实体未标记 is_sensitive",
        "- 底层平台名被当 capability_name",
        "",
        "## Validator 结果摘要",
        "",
        f"- total_cases: {total}",
        f"- passed_cases: {passed}",
        f"- failed_cases: {total - passed}",
        "",
        "| case_id | valid | next_step | warnings | errors | result |",
        "|---|---|---|---|---|---|",
    ]

    for item in results:
        warnings = ", ".join(item["warnings"]) or "none"
        errors = ", ".join(item["errors"]) or "none"
        result = "pass" if item["pass"] else "fail"
        lines.append(
            f"| {item['case_id']} | {str(item['actual_valid']).lower()} | {item['actual_next_step']} | {warnings} | {errors} | {result} |"
        )

    lines.extend(["", "## recommended_next_step 分布", ""])
    for name, count in sorted(next_steps.items()):
        lines.append(f"- {name}: {count}")

    lines.extend(["", "## 主要 warning 类型", ""])
    if warning_types:
        for name, count in sorted(warning_types.items()):
            lines.append(f"- {name}: {count}")
    else:
        lines.append("- none")

    lines.extend(["", "## 主要 error 类型", ""])
    if error_types:
        for name, count in sorted(error_types.items()):
            lines.append(f"- {name}: {count}")
    else:
        lines.append("- none")

    lines.extend(
        [
            "",
            "## 已知限制",
            "",
            "- 本轮只校验本地样例，不接真实 runtime。",
            "- 本轮不调用 preflight evaluator。",
            "- 本轮不读取认证态、不调用真实 API、不接真实平台。",
            "- validator 只做输入质量检查，不代替 security preflight evaluator。",
            "",
            "## 后续 TODO",
            "",
            "- 接 runtime 前，用真实 Agent 生成的 request 样本跑 validator。",
            "- 将 validator 与 evaluator 串联，形成 shadow hook 接入前输入质量闸门。",
            "- 将字段缺失和类型错误纳入 shadow metrics。",
        ]
    )

    RUN_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    RUN_LOG_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def print_summary(results: List[Dict[str, Any]]) -> None:
    total = len(results)
    passed = sum(1 for item in results if item["pass"])
    next_steps = Counter(item["actual_next_step"] for item in results)
    warning_types = Counter(warning for item in results for warning in item["warnings"])
    error_types = Counter(error for item in results for error in item["errors"])

    print("security_preflight_request_contract_validator")
    print(f"total_cases: {total}")
    print(f"passed_cases: {passed}")
    print(f"failed_cases: {total - passed}")
    print("recommended_next_step:")
    for name, count in sorted(next_steps.items()):
        print(f"- {name}: {count}")
    print("warning_types:")
    if warning_types:
        for name, count in sorted(warning_types.items()):
            print(f"- {name}: {count}")
    else:
        print("- none")
    print("error_types:")
    if error_types:
        for name, count in sorted(error_types.items()):
            print(f"- {name}: {count}")
    else:
        print("- none")
    print(f"run_log: {RUN_LOG_PATH}")


def main() -> int:
    policy = load_json(POLICY_PATH)
    cases = load_json(TEST_CASES_PATH)
    results = run_cases(policy, cases)
    write_run_log(results)
    print_summary(results)
    return 0 if all(item["pass"] for item in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
