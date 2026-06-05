#!/usr/bin/env python3
"""Local contract checks for the Dennis DataAgent connector.

This check uses in-memory mock DataAgent responses only. It does not call the
DataAgent Conversational API, Hive, or any internal platform.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
COMPUTER_USE_POC = REPO_ROOT / "computer_use_poc"

if str(COMPUTER_USE_POC) not in sys.path:
    sys.path.insert(0, str(COMPUTER_USE_POC))

from dataagent_response_normalizer import normalize_dataagent_response  # noqa: E402


REQUIRED_FILES = [
    "dataagent_cloud_skill_parity_contract_v1.md",
    "dataagent_connector_contract_v1.md",
    "dataagent_request_schema_v1.yaml",
    "dataagent_response_schema_v1.yaml",
    "dataagent_prompt_templates_v1.md",
    "dataagent_response_normalizer.py",
    "dataagent_sql_quality_gate.py",
]
PARITY_FIXTURE = COMPUTER_USE_POC / "test_fixtures" / "dataagent_cloud_skill_response_mock.json"

SENSITIVE_OUTPUT_RE = re.compile(
    r"\b(phone|cookie|token|session|header|authorization|password|email|id_card)\b",
    re.IGNORECASE,
)


def read_file(name: str) -> str:
    return (COMPUTER_USE_POC / name).read_text(encoding="utf-8")


def make_step_answer(answer: str, *, runtime_scope_id: str = "mock_runtime_scope") -> dict[str, Any]:
    return {
        "request_id": "mock_request",
        "session_id": runtime_scope_id,
        "query_id": "mock_query",
        "steps": [
            {"type": "MODEL_THINKING", "content": "planning is not evidence"},
            {"type": "TOOL_CALL", "content": "tool call raw output is not evidence"},
            {"type": "MODEL_ANSWER", "content": answer},
            {"type": "AGENT_END", "content": "done"},
        ],
    }


MOCKS: dict[str, dict[str, Any]] = {
    "completed": make_step_answer(
        """```sql
SELECT user_id, op_time, device_id
FROM ks_rc_bs.dwd_risk_usr_accnt_login_orign_info
WHERE p_date='20260528' AND p_action_type='login';
```

| user_id | op_time | device_id |
| --- | --- | --- |
| 544963630 | 2026-05-28 10:00:00 | device_ref_1 |
"""
    ),
    "no_data": make_step_answer(
        """```sql
SELECT user_id
FROM ks_rc_bs.dwd_risk_usr_accnt_login_orign_info
WHERE p_date='20260528' AND user_id=544963630;
```

No rows returned for this bounded query. This is no_data, not no risk.
"""
    ),
    "permission_denied": make_step_answer("Permission denied for requested table partition."),
    "sql_generated": make_step_answer(
        """```sql
SELECT user_id, count(*) AS cnt
FROM ks_rc_bs.dwd_risk_usr_accnt_login_orign_info
WHERE p_date='20260528'
GROUP BY user_id;
```"""
    ),
    "sensitive": make_step_answer(
        """```sql
SELECT user_id, phone, token_field
FROM ks_rc_bs.dwd_risk_usr_accnt_login_orign_info;
```

| user_id | phone | token_field | login_type |
| --- | --- | --- | --- |
| 544963630 | phone_safe_ref | redacted_token_ref | password_auth_type |
"""
    ),
}

ENVELOPE_MOCKS: dict[str, dict[str, Any]] = {
    "cloud_skill_steps": {
        "steps": [
            {"subType": "MODEL_THINKING", "content": "not evidence"},
            {
                "subType": "TOOL_CALL",
                "query_id": "mock_query_id",
                "trace_id": "mock_trace_id",
                "generated_sql": "SELECT user_id FROM ks_rc_bs.dwd_risk_usr_accnt_login_orign_info LIMIT 1",
            },
            {
                "subType": "MODEL_ANSWER",
                "content": "```sql\nSELECT user_id FROM ks_rc_bs.dwd_risk_usr_accnt_login_orign_info LIMIT 1;\n```",
            },
            {"subType": "AGENT_END", "content": "done"},
        ]
    },
    "choices_message_content": {
        "choices": [
            {
                "message": {
                    "content": "```sql\nSELECT user_id FROM ks_rc_bs.dwd_risk_usr_accnt_login_orign_info LIMIT 1;\n```"
                }
            }
        ]
    },
    "choices_delta_content": {
        "choices": [
            {
                "delta": {
                    "content": "```sql\nSELECT user_id FROM ks_rc_bs.dwd_risk_usr_accnt_login_orign_info LIMIT 1;\n```"
                }
            }
        ]
    },
    "data_steps": {
        "data": {
            "steps": [
                {"subType": "MODEL_THINKING", "content": "not evidence"},
                {
                    "subType": "TOOL_CALL",
                    "queryId": "mock_query_id",
                    "generated_sql": "SELECT user_id FROM ks_rc_bs.dwd_risk_usr_accnt_login_orign_info LIMIT 1",
                },
                {
                    "subType": "MODEL_ANSWER",
                    "content": "```sql\nSELECT user_id FROM ks_rc_bs.dwd_risk_usr_accnt_login_orign_info LIMIT 1;\n```",
                },
            ]
        }
    },
    "cloud_live_nested_stepdata": {
        "data": {
            "steps": [
                {
                    "data": {
                        "stepData": {
                            "subType": "MODEL_THINKING",
                            "componentInfo": {
                                "props": {
                                    "content": "planning text is not evidence",
                                }
                            },
                        }
                    }
                },
                {
                    "data": {
                        "stepData": {
                            "subType": "MODEL_ANSWER",
                            "componentInfo": {
                                "props": {
                                    "content": "```sql\nSELECT user_id FROM ks_rc_bs.dwd_risk_usr_accnt_login_orign_info LIMIT 1;\n```",
                                }
                            },
                        }
                    }
                },
                {
                    "data": {
                        "stepData": {
                            "subType": "TOOL_CALL",
                            "queryId": "mock_nested_query_id",
                            "generated_sql": "SELECT user_id FROM ks_rc_bs.dwd_risk_usr_accnt_login_orign_info LIMIT 1",
                        }
                    }
                },
            ]
        }
    },
    "answer_field": {
        "answer": "```sql\nSELECT user_id FROM ks_rc_bs.dwd_risk_usr_accnt_login_orign_info LIMIT 1;\n```"
    },
    "missing_model_answer": {
        "code": 0,
        "data": {
            "requestAccepted": True,
            "items": [],
        },
    },
    "query_id_only_unknown_steps": {
        "code": 0,
        "query_id": "mock_query_id_present_only",
        "data": {
            "steps": [
                {
                    "stage": "accepted",
                    "payload": {
                        "queryId": "mock_nested_query_id_present_only",
                    },
                }
            ]
        },
    },
}

SQL_QUALITY_GATE_MOCKS: dict[str, dict[str, Any]] = {
    "risk_entity_fields_pass": make_step_answer(
        """```sql
SELECT user_id, device_id, source_ip, event_id, source_id, op_time
FROM ks_rc_bs.dwd_risk_usr_accnt_login_orign_info
WHERE p_date='20260528' AND user_id=544963630
LIMIT 100;
```"""
    ),
    "metadata_catalog_caveat_blocks": make_step_answer(
        """```sql
SELECT user_id, device_id, source_ip, op_time
FROM ks_rc_bs.dwd_risk_usr_accnt_login_orign_info
WHERE p_date='20260528' AND user_id=544963630
LIMIT 100;
```

Table not found in metadata catalog; verify table name & partition column before execution.
"""
    ),
    "sensitive_fields_block": make_step_answer(
        """```sql
SELECT user_id, phone, cookie, device_id
FROM ks_rc_bs.dwd_risk_usr_accnt_login_orign_info
WHERE p_date='20260528' AND user_id=544963630
LIMIT 100;
```"""
    ),
    "unbounded_scan_blocks": make_step_answer(
        """```sql
SELECT user_id, device_id, source_ip
FROM ks_rc_bs.dwd_risk_usr_accnt_login_orign_info;
```"""
    ),
    "unknown_table_blocks": make_step_answer(
        """```sql
SELECT user_id, device_id
FROM ks_dw_fact.dw_fact_user_login_di
WHERE p_date='20260528' AND user_id=544963630
LIMIT 100;
```"""
    ),
}


def check_required_files() -> list[str]:
    errors: list[str] = []
    for name in REQUIRED_FILES:
        if not (COMPUTER_USE_POC / name).is_file():
            errors.append(f"missing_file:{name}")
    return errors


def check_contract_text() -> list[str]:
    errors: list[str] = []
    contract = read_file("dataagent_connector_contract_v1.md")
    request_schema = read_file("dataagent_request_schema_v1.yaml")
    response_schema = read_file("dataagent_response_schema_v1.yaml")
    templates = read_file("dataagent_prompt_templates_v1.md")

    required_contract_terms = [
        "cloud_skill_verified_contract",
        "Conversational API",
        "/v1/chat/completions/full",
        "structured-query API",
        "design direction only",
        "MODEL_ANSWER",
        "per-call user authorization",
    ]
    for term in required_contract_terms:
        if term not in contract:
            errors.append(f"contract_missing:{term}")

    if "dry_run" not in request_schema or "default: true" not in request_schema:
        errors.append("request_schema_missing_dry_run_default")
    if "structured_query_api: design_only_not_available" not in request_schema:
        errors.append("request_schema_structured_query_boundary_missing")
    if "MODEL_THINKING" not in response_schema or "MODEL_ANSWER" not in response_schema:
        errors.append("response_schema_step_types_missing")
    if "source_schema_drift" not in response_schema or "parse_error" not in response_schema:
        errors.append("response_schema_schema_drift_status_missing")
    if "response_shape_probe" not in response_schema:
        errors.append("response_schema_probe_contract_missing")
    for term in (
        "sql_quality_gate",
        "dry_run_false_eligible",
        "Table not found in metadata catalog",
        "IP / device_id / DID are risk_entity_identifier",
    ):
        if term not in response_schema:
            errors.append(f"response_schema_sql_quality_gate_missing:{term}")
    for template_id in (
        "single_user_ato_evidence",
        "batch_user_ato_clustering",
        "strategy_hit_login_timeline_alignment",
    ):
        if template_id not in templates:
            errors.append(f"prompt_template_missing:{template_id}")
    for table in (
        "ks_rc_bs.dwd_risk_usr_accnt_login_orign_info",
        "ks_rc_arch.antispam_feature_map_default_partitioned",
        "ks_rc_bs.account_security_basic_info",
        "kscdm.dim_ks_user_all",
        "ks_rc_bs.fake_account_tag_all_detail_snapshot",
    ):
        if table not in templates:
            errors.append(f"prompt_template_missing_table:{table}")
    return errors


def check_cloud_skill_parity() -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    if not PARITY_FIXTURE.is_file():
        return {"parity_mock_pass": False}, [f"missing_file:{PARITY_FIXTURE.relative_to(REPO_ROOT)}"]

    fixture_text = PARITY_FIXTURE.read_text(encoding="utf-8")
    if SENSITIVE_OUTPUT_RE.search(fixture_text):
        errors.append("parity_fixture_contains_sensitive_term")

    payload = json.loads(fixture_text)
    normalized = normalize_dataagent_response(payload)
    observed_types = set(normalized.get("raw_step_types_observed", []))
    required_types = {"MODEL_THINKING", "TOOL_CALL", "MODEL_ANSWER", "AGENT_END"}
    missing_types = sorted(required_types.difference(observed_types))
    if missing_types:
        errors.append(f"parity_fixture_missing_step_types:{','.join(missing_types)}")
    if normalized.get("status") != "completed":
        errors.append(f"parity_status_unexpected:{normalized.get('status')}")
    if not normalized.get("model_answer_extracted"):
        errors.append("parity_model_answer_not_extracted")
    tool_provenance = normalized.get("tool_call_provenance") or {}
    if not tool_provenance.get("query_id"):
        errors.append("parity_tool_call_query_id_missing")
    if not tool_provenance.get("generated_sql"):
        errors.append("parity_tool_call_generated_sql_missing")
    if not tool_provenance.get("provenance_only_not_business_conclusion"):
        errors.append("parity_tool_call_boundary_missing")
    if normalized.get("sensitive_output") is not False:
        errors.append("parity_sensitive_output_not_false")

    result = {
        "cloud_skill_contract_known": True,
        "local_live_verified": False,
        "parity_mock_pass": not errors,
        "status": normalized.get("status"),
        "row_count": normalized.get("row_count"),
        "model_answer_extracted": normalized.get("model_answer_extracted"),
        "tool_call_query_id_present": bool(tool_provenance.get("query_id")),
        "tool_call_generated_sql_present": bool(tool_provenance.get("generated_sql")),
        "tool_call_provenance_only": bool(tool_provenance.get("provenance_only_not_business_conclusion")),
    }
    return result, errors


def check_normalizer() -> tuple[list[dict[str, Any]], list[str]]:
    results: list[dict[str, Any]] = []
    errors: list[str] = []
    expected_status = {
        "completed": "completed",
        "no_data": "no_data",
        "permission_denied": "permission_denied",
        "sql_generated": "sql_generated",
        "sensitive": "completed",
    }
    for name, payload in MOCKS.items():
        normalized = normalize_dataagent_response(payload)
        result = {
            "mock": name,
            "status": normalized["status"],
            "row_count": normalized["row_count"],
            "source_status": normalized["source_card"]["source_status"],
            "sensitive_output": normalized["sensitive_output"],
            "redaction_applied": normalized["redaction_applied"],
        }
        results.append(result)
        if normalized["status"] != expected_status[name]:
            errors.append(f"mock_status_mismatch:{name}:{normalized['status']}")
        if normalized["source_card"]["source_status"] != normalized["status"]:
            errors.append(f"source_card_status_mismatch:{name}")
        if normalized["sensitive_output"] is not False:
            errors.append(f"sensitive_output_not_false:{name}")
        if normalized["redaction_applied"] is not True:
            errors.append(f"redaction_not_applied:{name}")
        if "sql_quality_gate" not in normalized:
            errors.append(f"sql_quality_gate_missing:{name}")
        if name == "sql_generated" and not normalized["source_quality"]["pending_execution_not_evidence"]:
            errors.append("sql_generated_missing_pending_boundary")
        if name == "no_data" and not normalized["source_quality"]["no_data_not_risk_exclusion"]:
            errors.append("no_data_boundary_missing")
        if name == "sensitive":
            sensitive_surface = json.dumps(
                {
                    "generated_sql": normalized.get("generated_sql"),
                    "columns": normalized.get("columns"),
                    "result_rows": normalized.get("result_rows"),
                    "error_message": normalized.get("error_message"),
                },
                ensure_ascii=False,
            )
            if SENSITIVE_OUTPUT_RE.search(sensitive_surface):
                errors.append("sensitive_terms_not_intercepted")
            if normalized["redaction"]["blocked_sensitive_fields_count"] <= 0:
                errors.append("sensitive_block_count_missing")
    return results, errors


def check_sql_quality_gate() -> tuple[list[dict[str, Any]], list[str]]:
    results: list[dict[str, Any]] = []
    errors: list[str] = []
    expected_status = {
        "risk_entity_fields_pass": "pass",
        "metadata_catalog_caveat_blocks": "block",
        "sensitive_fields_block": "block",
        "unbounded_scan_blocks": "block",
        "unknown_table_blocks": "block",
    }
    for name, payload in SQL_QUALITY_GATE_MOCKS.items():
        normalized = normalize_dataagent_response(payload)
        gate = normalized.get("sql_quality_gate") or {}
        field_policy = gate.get("field_policy") or {}
        result = {
            "mock": name,
            "normalizer_status": normalized.get("status"),
            "gate_status": gate.get("gate_status"),
            "dry_run_false_eligible": gate.get("dry_run_false_eligible"),
            "dry_run_false_execution_allowed": gate.get("dry_run_false_execution_allowed"),
            "failure_reasons": gate.get("failure_reasons", []),
            "risk_entity_identifier_fields_present": field_policy.get("risk_entity_identifier_fields_present", []),
            "credential_secret_fields_present": field_policy.get("credential_secret_fields_present", []),
            "pii_strict_fields_present": field_policy.get("pii_strict_fields_present", []),
        }
        results.append(result)
        if gate.get("gate_status") != expected_status[name]:
            errors.append(f"sql_quality_gate_status_mismatch:{name}:{gate.get('gate_status')}")
        if gate.get("sql_executed") is not False or gate.get("hive_called") is not False:
            errors.append(f"sql_quality_gate_execution_boundary_failed:{name}")
        if gate.get("dry_run_false_execution_allowed") is not False:
            errors.append(f"sql_quality_gate_dry_run_false_allowed:{name}")
        if name == "risk_entity_fields_pass":
            risk_fields = set(field_policy.get("risk_entity_identifier_fields_present", []))
            for field in ("source_ip", "device_id"):
                if field not in risk_fields:
                    errors.append(f"risk_entity_field_not_classified:{field}")
            if field_policy.get("credential_secret_fields_present") or field_policy.get("pii_strict_fields_present"):
                errors.append("risk_entity_fields_misclassified_sensitive")
            if gate.get("dry_run_false_eligible") is not True:
                errors.append("risk_entity_fields_pass_not_eligible_after_gate")
        if name == "metadata_catalog_caveat_blocks":
            reasons = set(gate.get("failure_reasons", []))
            if "dataagent_blocking_caveat" not in reasons:
                errors.append("metadata_catalog_caveat_not_blocking")
            if gate.get("dry_run_false_eligible") is not False:
                errors.append("metadata_catalog_caveat_marked_eligible")
        if name == "sensitive_fields_block":
            if not (field_policy.get("credential_secret_fields_present") or field_policy.get("pii_strict_fields_present")):
                errors.append("sensitive_fields_not_detected")
        if name == "unbounded_scan_blocks":
            reasons = set(gate.get("failure_reasons", []))
            for reason in ("missing_partition_filter", "missing_limit", "missing_bounded_entity_filter"):
                if reason not in reasons:
                    errors.append(f"unbounded_scan_missing_reason:{reason}")
        if name == "unknown_table_blocks":
            if not any(str(reason).startswith("unknown_table:") for reason in gate.get("failure_reasons", [])):
                errors.append("unknown_table_not_blocked")
    return results, errors


def check_envelope_compatibility() -> tuple[list[dict[str, Any]], list[str]]:
    results: list[dict[str, Any]] = []
    errors: list[str] = []
    expected = {
        "cloud_skill_steps": ("sql_generated", "model_answer_step", True),
        "choices_message_content": ("sql_generated", "content_fallback", True),
        "choices_delta_content": ("sql_generated", "content_fallback", True),
        "data_steps": ("sql_generated", "model_answer_step", True),
        "cloud_live_nested_stepdata": ("sql_generated", "model_answer_step", True),
        "answer_field": ("sql_generated", "answer_field", True),
        "missing_model_answer": ("source_schema_drift", "missing", False),
        "query_id_only_unknown_steps": ("source_schema_drift", "missing", False),
    }
    for name, payload in ENVELOPE_MOCKS.items():
        normalized = normalize_dataagent_response(payload)
        expected_status, expected_source, expected_extracted = expected[name]
        result = {
            "mock": name,
            "status": normalized["status"],
            "source_status": normalized["source_card"]["source_status"],
            "model_answer_source": normalized.get("model_answer_source"),
            "model_answer_extracted": normalized.get("model_answer_extracted"),
            "generated_sql_present": bool(normalized.get("generated_sql")),
            "query_id_present": bool(normalized.get("query_id")),
            "tool_call_provenance_only": bool(
                (normalized.get("tool_call_provenance") or {}).get("provenance_only_not_business_conclusion")
            ),
        }
        results.append(result)
        if normalized["status"] != expected_status:
            errors.append(f"envelope_status_mismatch:{name}:{normalized['status']}")
        if normalized["source_card"]["source_status"] != expected_status:
            errors.append(f"envelope_source_status_mismatch:{name}")
        if normalized.get("model_answer_source") != expected_source:
            errors.append(f"envelope_model_answer_source_mismatch:{name}:{normalized.get('model_answer_source')}")
        if normalized.get("model_answer_extracted") is not expected_extracted:
            errors.append(f"envelope_model_answer_extracted_mismatch:{name}")
        if name == "missing_model_answer":
            if normalized["status"] == "completed":
                errors.append("missing_model_answer_marked_completed")
            if normalized.get("error_message") != "missing_model_answer":
                errors.append("missing_model_answer_reason_missing")
        if name == "query_id_only_unknown_steps":
            if normalized["status"] == "completed":
                errors.append("query_id_only_unknown_steps_marked_completed")
            if not normalized.get("query_id"):
                errors.append("query_id_only_unknown_steps_query_id_not_provenance")
            if normalized.get("generated_sql"):
                errors.append("query_id_only_unknown_steps_generated_sql_should_be_absent")
        if name in {"cloud_skill_steps", "data_steps", "cloud_live_nested_stepdata"}:
            provenance = normalized.get("tool_call_provenance") or {}
            if not provenance.get("query_id"):
                errors.append(f"{name}_query_id_not_extracted_as_provenance")
            if not provenance.get("generated_sql"):
                errors.append(f"{name}_generated_sql_not_extracted_as_provenance")
    return results, errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check local DataAgent connector contract.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    args = parser.parse_args(argv)

    errors = []
    errors.extend(check_required_files())
    if not errors:
        errors.extend(check_contract_text())
    normalizer_results, normalizer_errors = check_normalizer()
    errors.extend(normalizer_errors)
    envelope_results, envelope_errors = check_envelope_compatibility()
    errors.extend(envelope_errors)
    sql_quality_gate_results, sql_quality_gate_errors = check_sql_quality_gate()
    errors.extend(sql_quality_gate_errors)
    cloud_skill_parity, parity_errors = check_cloud_skill_parity()
    errors.extend(parity_errors)

    payload = {
        "status": "PASS_DATAAGENT_CONNECTOR_CONTRACT_CHECK" if not errors else "FAILED_DATAAGENT_CONNECTOR_CONTRACT_CHECK",
        "cloud_skill_contract_known": True,
        "local_live_verified": False,
        "parity_mock_pass": cloud_skill_parity.get("parity_mock_pass") is True,
        "real_dataagent_api_called": False,
        "hive_called": False,
        "sql_submitted": False,
        "default_mode": "dry_run_sql_generation",
        "per_call_authorization_required": True,
        "structured_query_api_currently_available": False,
        "cloud_skill_parity": cloud_skill_parity,
        "normalizer_results": normalizer_results,
        "envelope_compatibility_results": envelope_results,
        "sql_quality_gate_results": sql_quality_gate_results,
        "errors": errors,
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(payload["status"])
        for item in normalizer_results:
            print(f"- {item['mock']}: {item['status']}")
        if errors:
            print("errors:")
            for error in errors:
                print(f"- {error}")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
