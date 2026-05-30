#!/usr/bin/env python3
"""Prepare local DataAgent live parity dry-run checks.

Default behavior never calls DataAgent, never submits SQL, and never calls
Hive. HTTP dry-run requires both --live-dry-run and --allow-live-dry-run.
Live dry-run sends only the Conversational API payload and records source
failures without auth repair.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import socket
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
COMPUTER_USE_POC = REPO_ROOT / "computer_use_poc"
MOCK_PATH = COMPUTER_USE_POC / "test_fixtures" / "dataagent_cloud_skill_response_mock.json"
ENDPOINT = "https://video-data.corp.kuaishou.com/v1/chat/completions/full"
DEFAULT_HTTP_TIMEOUT_SECONDS = 30
MAX_RESPONSE_BYTES = 2_000_000
MAX_PROBE_DEPTH = 7
MAX_PROBE_ITEMS = 40
SENSITIVE_KEY_RE = re.compile(r"(cookie|token|session|header|authorization|password)", re.IGNORECASE)
SQL_KEY_RE = re.compile(r"(^sql$|generated_sql|generatedSql|sql_text|sqlText|query_sql|querySql)", re.IGNORECASE)
QUERY_ID_KEY_RE = re.compile(r"(query[_-]?id|queryId|sqlId|sql_id)", re.IGNORECASE)
TRACE_ID_KEY_RE = re.compile(r"(trace[_-]?id|traceId)", re.IGNORECASE)
TEXT_KEY_RE = re.compile(r"^(content|text|answer|message|output)$", re.IGNORECASE)

if str(COMPUTER_USE_POC) not in sys.path:
    sys.path.insert(0, str(COMPUTER_USE_POC))

from dataagent_response_normalizer import normalize_dataagent_response, redact_sensitive_text, step_type  # noqa: E402


SYSTEM_PROMPT = (
    "Dennis DataAgent readonly contract. Return step-based JSON. MODEL_ANSWER is the only "
    "evidence explanation. TOOL_CALL/query_id/generated_sql/trace are provenance only. "
    "Do not output sensitive plaintext. dry_run=true means SQL generation only."
)


CASE_DEFINITIONS: dict[str, dict[str, Any]] = {
    "single_user_ato": {
        "task_type": "SINGLE_USER_QUERY",
        "user_id": "544963630",
        "time_window": "last 7 days, Asia/Shanghai, bounded",
        "dry_run": True,
        "max_rows": 1000,
        "goal": "Generate login log / device / IP / account-security evidence SQL.",
        "recommended_tables": [
            "ks_rc_bs.dwd_risk_usr_accnt_login_orign_info",
            "ks_rc_bs.ks_account_login_basic_info",
            "ks_rc_bs.account_security_basic_info",
            "kscdm.dim_ks_user_all",
        ],
        "fields": [
            "user_id",
            "op_time",
            "device_id",
            "source_ip",
            "login_type",
            "finalloginresult",
            "p_action_type",
            "code",
            "punish",
            "hit_policies",
        ],
        "no_data_boundary": "No rows under this bounded query is not no ATO and not no risk.",
    },
    "strategy_hit_login_timeline": {
        "task_type": "STRATEGY_HIT_QUERY",
        "user_id": "544963630",
        "time_window": "last 7 days, Asia/Shanghai, bounded",
        "dry_run": True,
        "max_rows": 1000,
        "goal": "Generate strategy hit / RCP / login behavior timeline SQL.",
        "recommended_tables": [
            "ks_rc_bs.dwd_risk_usr_accnt_login_orign_info",
            "ks_rc_arch.antispam_feature_map_default_partitioned",
            "ks_raw_log_v2.antispam_feature_map_partitioned",
        ],
        "fields": [
            "user_id",
            "source_id",
            "action_type",
            "p_action_type",
            "time",
            "op_time",
            "device_id",
            "source_ip",
            "code",
            "punish",
            "hit_policies",
        ],
        "no_data_boundary": "No RCP rows or no login rows under this bounded query is not no risk.",
    },
}


def build_structured_prompt(case: dict[str, Any]) -> str:
    lines = [
        f"Task type: {case['task_type']}",
        "Business context: DataAgent local live parity dry-run",
        f"Goal: {case['goal']}",
        f"Entity: user_id={case['user_id']}",
        f"Time window: {case['time_window']}",
        f"dry_run: {str(case['dry_run']).lower()}",
        f"max_rows: {case['max_rows']}",
        "",
        "Recommended source tables:",
    ]
    lines.extend(f"- {table}" for table in case["recommended_tables"])
    lines.extend(["", "Recommended fields:"])
    lines.extend(f"- {field}" for field in case["fields"])
    lines.extend(
        [
            "",
            "Generate SQL only. Do not execute Hive. Do not submit SQL.",
            "Return final SQL or dry-run result only in MODEL_ANSWER.",
            f"No-data boundary: {case['no_data_boundary']}",
            "Sensitive output boundary: do not output phone, cookie, token, session, header, email, id_card or credential plaintext.",
        ]
    )
    return "\n".join(lines)


def build_payload(case_id: str) -> dict[str, Any]:
    case = CASE_DEFINITIONS[case_id]
    return {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_structured_prompt(case)},
        ],
        "stream": False,
        "session_id": f"local_dryrun_parity_{case_id}",
        "user_id": "dennis_full_runtime_local",
    }


def http_timeout_seconds() -> float:
    raw = os.environ.get("DATAAGENT_HTTP_TIMEOUT_SECONDS")
    if raw is None or raw.strip() == "":
        return float(DEFAULT_HTTP_TIMEOUT_SECONDS)
    try:
        timeout = float(raw)
    except ValueError:
        return float(DEFAULT_HTTP_TIMEOUT_SECONDS)
    return timeout if timeout > 0 else float(DEFAULT_HTTP_TIMEOUT_SECONDS)


def run_mock() -> dict[str, Any]:
    payload = json.loads(MOCK_PATH.read_text(encoding="utf-8"))
    normalized = normalize_dataagent_response(payload)
    tool_provenance = normalized.get("tool_call_provenance") or {}
    dry_run_status = normalized.get("status")
    dry_run_completed_like_response_downgraded = False
    if dry_run_status == "completed":
        dry_run_status = "sql_generated" if normalized.get("generated_sql") else "parse_error"
        dry_run_completed_like_response_downgraded = True
    source_quality = dict(normalized.get("source_quality") or {})
    step_response_received = bool(normalized.get("step_response_received"))
    model_answer_extracted = bool(normalized.get("model_answer_extracted"))
    source_quality.update(
        {
            "dataagent_api_attempted": False,
            "http_request_sent": False,
            "step_response_received": step_response_received,
            "model_answer_extracted": model_answer_extracted,
            "dataagent_called": False,
            "hive_called": False,
            "dry_run": True,
            "pending_execution_not_evidence": True,
            "mock_only": True,
            "real_dataagent_api_called": False,
            "sql_submitted": False,
            "completed_evidence": False,
            "sql_quality_gate_status": (normalized.get("sql_quality_gate") or {}).get("gate_status"),
            "dry_run_false_eligible": (normalized.get("sql_quality_gate") or {}).get("dry_run_false_eligible") is True,
            "dry_run_false_execution_allowed": False,
            "dry_run_completed_like_response_downgraded": dry_run_completed_like_response_downgraded,
        }
    )
    return {
        "mode": "mock",
        "mock_path": str(MOCK_PATH.relative_to(REPO_ROOT)),
        "status": "PASS" if normalized.get("model_answer_extracted") else "FAILED",
        "real_dataagent_api_called": False,
        "dataagent_api_attempted": False,
        "http_request_sent": False,
        "step_response_received": step_response_received,
        "model_answer_extracted": model_answer_extracted,
        "hive_called": False,
        "sql_submitted": False,
        "normalized_status": dry_run_status,
        "completed_evidence": False,
        "dry_run_completed_like_response_downgraded": dry_run_completed_like_response_downgraded,
        "tool_call_provenance_only": bool(tool_provenance.get("provenance_only_not_business_conclusion")),
        "sql_quality_gate": normalized.get("sql_quality_gate"),
        "source_quality": source_quality,
    }


def print_payload(case_id: str) -> dict[str, Any]:
    payload = build_payload(case_id)
    return {
        "mode": "print_payload",
        "case": case_id,
        "endpoint": ENDPOINT,
        "method": "POST",
        "payload": payload,
        "real_dataagent_api_called": False,
        "dataagent_api_attempted": False,
        "http_request_sent": False,
        "step_response_received": False,
        "model_answer_extracted": False,
        "hive_called": False,
        "sql_submitted": False,
        "dry_run": True,
        "expected_response_status": "sql_generated",
        "normalization_expectation": {
            "MODEL_ANSWER_only_for_evidence": True,
            "TOOL_CALL_generated_sql_query_id_trace_as_provenance_only": True,
            "sql_generated_not_completed_evidence": True,
        },
        "source_quality_mapping": {
            "pending_failed_timeout_no_data_permission_denied_enter_source_quality": True,
            "no_data_not_risk_exclusion": True,
        },
    }


def safe_path(path: str) -> str:
    parts = []
    for part in path.split("."):
        if SENSITIVE_KEY_RE.search(part):
            parts.append("redacted_sensitive_key")
        else:
            parts.append(part)
    return ".".join(parts)


def value_type(value: Any) -> str:
    if isinstance(value, dict):
        return "object"
    if isinstance(value, list):
        return "array"
    if isinstance(value, str):
        return "string"
    if isinstance(value, bool):
        return "boolean"
    if value is None:
        return "null"
    if isinstance(value, (int, float)):
        return "number"
    return type(value).__name__


def shape_walk(value: Any, path: str, summary: dict[str, Any], depth: int = 0) -> None:
    if depth > MAX_PROBE_DEPTH:
        return
    if isinstance(value, dict):
        if any(key in value for key in ("steps", "messages", "data", "result", "choices", "answer", "content")):
            summary["candidate_paths"].append(safe_path(path or "$"))
        for key, nested in list(value.items())[:MAX_PROBE_ITEMS]:
            child_path = f"{path}.{key}" if path else key
            lowered_key = key.lower()
            if key in {"type", "step_type", "stepType"}:
                summary["observed_type_fields"].append({"path": safe_path(child_path), "value": str(nested)[:80]})
            if key in {"subType", "subtype"}:
                summary["observed_subtype_fields"].append({"path": safe_path(child_path), "value": str(nested)[:80]})
            if isinstance(nested, str):
                if TEXT_KEY_RE.search(key):
                    summary["text_field_paths_with_lengths_only"].append(
                        {"path": safe_path(child_path), "length": len(nested)}
                    )
                    if "answer" in lowered_key or "content" in lowered_key or "message" in lowered_key:
                        summary["possible_model_answer_paths"].append(safe_path(child_path))
                if SQL_KEY_RE.search(key):
                    summary["sql_field_paths_present_only"].append({"path": safe_path(child_path), "present": True})
                if QUERY_ID_KEY_RE.search(key):
                    summary["query_id_paths_present_only"].append({"path": safe_path(child_path), "present": True})
                if TRACE_ID_KEY_RE.search(key):
                    summary["trace_id_paths_present_only"].append({"path": safe_path(child_path), "present": True})
            if step_type(value) == "MODEL_ANSWER":
                summary["possible_model_answer_paths"].append(safe_path(path or "$"))
            if step_type(value) == "TOOL_CALL":
                summary["possible_tool_call_paths"].append(
                    {
                        "path": safe_path(path or "$"),
                        "generated_sql_present": bool(collect_probe_value(value, SQL_KEY_RE)),
                        "query_id_present": bool(collect_probe_value(value, QUERY_ID_KEY_RE)),
                        "trace_id_present": bool(collect_probe_value(value, TRACE_ID_KEY_RE)),
                    }
                )
            shape_walk(nested, child_path, summary, depth + 1)
    elif isinstance(value, list):
        if value and all(isinstance(item, dict) for item in value[: min(len(value), MAX_PROBE_ITEMS)]):
            if any(step_type(item) for item in value if isinstance(item, dict)):
                summary["step_like_array_paths"].append(safe_path(path or "$"))
        for index, item in enumerate(value[:MAX_PROBE_ITEMS]):
            shape_walk(item, f"{path}[{index}]", summary, depth + 1)


def collect_probe_value(value: Any, key_re: re.Pattern[str]) -> Any:
    if isinstance(value, dict):
        for key, nested in value.items():
            if key_re.search(key) and nested not in (None, ""):
                return nested
        for nested in value.values():
            found = collect_probe_value(nested, key_re)
            if found not in (None, ""):
                return found
    elif isinstance(value, list):
        for nested in value:
            found = collect_probe_value(nested, key_re)
            if found not in (None, ""):
                return found
    return None


def unique_list(items: list[Any]) -> list[Any]:
    seen: set[str] = set()
    output: list[Any] = []
    for item in items:
        marker = json.dumps(item, ensure_ascii=False, sort_keys=True)
        if marker in seen:
            continue
        seen.add(marker)
        output.append(item)
    return output


def response_shape_summary(
    payload: Any,
    *,
    http_status: int,
    content_type: str | None,
    response_size_bytes: int,
) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "http_status": http_status,
        "content_type": content_type,
        "top_level_type": value_type(payload),
        "top_level_keys": [],
        "candidate_paths": [],
        "step_like_array_paths": [],
        "observed_type_fields": [],
        "observed_subtype_fields": [],
        "possible_model_answer_paths": [],
        "possible_tool_call_paths": [],
        "text_field_paths_with_lengths_only": [],
        "sql_field_paths_present_only": [],
        "query_id_paths_present_only": [],
        "trace_id_paths_present_only": [],
        "response_size_bytes": response_size_bytes,
        "raw_response_body_printed": False,
        "sensitive_output": False,
    }
    if isinstance(payload, dict):
        summary["top_level_keys"] = [safe_path(str(key)) for key in list(payload.keys())[:MAX_PROBE_ITEMS]]
    shape_walk(payload, "", summary)
    for key in (
        "candidate_paths",
        "step_like_array_paths",
        "observed_type_fields",
        "observed_subtype_fields",
        "possible_model_answer_paths",
        "possible_tool_call_paths",
        "text_field_paths_with_lengths_only",
        "sql_field_paths_present_only",
        "query_id_paths_present_only",
        "trace_id_paths_present_only",
    ):
        summary[key] = unique_list(summary[key])
    return summary


def source_failure_observation(
    *,
    source_status: str,
    failure_reason: str,
    http_status: int | None = None,
    response_type: str,
    dataagent_api_attempted: bool,
    http_request_sent: bool,
    step_response_received: bool = False,
    model_answer_extracted: bool = False,
) -> dict[str, Any]:
    safe_reason, blocked_count = redact_sensitive_text(failure_reason)
    permission_status = "permission_denied" if source_status == "permission_denied" else "unknown"
    real_dataagent_api_called = http_request_sent
    return {
        "schema_version": "dataagent_normalized_response_v1",
        "request_id": None,
        "session_id": None,
        "query_id": None,
        "status": source_status,
        "model_answer_source": "missing",
        "generated_sql": None,
        "generated_sql_source": None,
        "result_rows": [],
        "columns": [],
        "row_count": 0,
        "error_message": safe_reason,
        "permission_status": permission_status,
        "data_freshness": None,
        "source_tables": [],
        "query_time_range": {},
        "warnings": [
            f"{source_status}_not_no_risk_evidence",
            "dry_run_no_hive_sql_submitted",
        ],
        "no_data_reason": None,
        "trace_id": None,
        "source_quality": {
            "source_name": "dataagent_hive",
            "permission_status": permission_status,
            "response_type": response_type,
            "reliability_level": "live_dryrun_source_failure_recorded",
            "failure_reason": safe_reason,
            "http_status": http_status,
            "no_data_not_risk_exclusion": True,
            "pending_execution_not_evidence": True,
            "dataagent_api_attempted": dataagent_api_attempted,
            "http_request_sent": http_request_sent,
            "step_response_received": step_response_received,
            "model_answer_extracted": model_answer_extracted,
            "model_answer_source": "missing",
            "real_dataagent_api_called": real_dataagent_api_called,
            "dataagent_called": real_dataagent_api_called,
            "hive_called": False,
            "dry_run": True,
            "sql_submitted": False,
            "auth_debug_attempted": False,
        },
        "tool_call_provenance": {},
        "source_card": {
            "source_name": "dataagent_hive",
            "source_status": source_status,
            "evidence_summary": "DataAgent live dry-run did not produce completed evidence; failure recorded in source_quality.",
            "records_count": 0,
        },
        "source_checkpoint_private": {
            "raw_references": [],
            "downstream_source_chaining": [],
        },
        "redaction": {
            "redaction_applied": True,
            "sensitive_output": False,
            "blocked_sensitive_fields_count": blocked_count,
        },
        "redaction_applied": True,
        "sensitive_output": False,
        "raw_step_types_observed": [],
        "step_response_received": step_response_received,
        "model_answer_extracted": model_answer_extracted,
    }


def apply_live_dry_run_boundary(normalized: dict[str, Any], *, http_status: int) -> dict[str, Any]:
    observation = json.loads(json.dumps(normalized, ensure_ascii=False))
    warnings = list(observation.get("warnings") or [])
    status = observation.get("status")

    if status == "completed":
        warnings.append("dry_run_completed_like_response_downgraded_to_sql_generated_not_evidence")
        observation["status"] = "sql_generated" if observation.get("generated_sql") else "failed"
        observation["result_rows"] = []
        observation["columns"] = []
        observation["row_count"] = 0
    if observation.get("status") == "sql_generated":
        warnings.append("dry_run_sql_generated_not_completed_evidence")
    sql_quality_gate = observation.get("sql_quality_gate") or {}
    if sql_quality_gate.get("gate_status") == "block":
        warnings.append("sql_quality_gate_blocked_dry_run_false")
    elif sql_quality_gate.get("gate_status") == "pass":
        warnings.append("sql_quality_gate_passed_but_dry_run_false_still_requires_authorization")
    warnings.append("dry_run_no_hive_sql_submitted")
    observation["warnings"] = sorted(set(warnings))

    source_quality = dict(observation.get("source_quality") or {})
    source_quality.update(
        {
            "response_type": "live_dryrun_step_based_json_model_answer",
            "reliability_level": "local_live_dryrun_parity",
            "http_status": http_status,
            "no_data_not_risk_exclusion": True,
            "pending_execution_not_evidence": True,
            "dataagent_api_attempted": True,
            "http_request_sent": True,
            "step_response_received": True,
            "model_answer_extracted": bool(observation.get("model_answer_extracted")),
            "real_dataagent_api_called": True,
            "dataagent_called": True,
            "hive_called": False,
            "dry_run": True,
            "sql_submitted": False,
            "auth_debug_attempted": False,
            "sql_quality_gate_status": sql_quality_gate.get("gate_status"),
            "dry_run_false_eligible": sql_quality_gate.get("dry_run_false_eligible") is True,
            "dry_run_false_execution_allowed": False,
            "normalized_from_mock": False,
            "local_live_verified": False,
            "local_live_dryrun_verified": observation.get("status") == "sql_generated",
        }
    )
    observation["source_quality"] = source_quality

    source_card = dict(observation.get("source_card") or {})
    if observation.get("status") == "sql_generated":
        evidence_summary = "DataAgent live dry-run generated SQL/provenance only; no Hive SQL was submitted."
    else:
        evidence_summary = "DataAgent live dry-run response was recorded but not completed evidence; no Hive SQL was submitted."
    source_card.update(
        {
            "source_name": "dataagent_hive",
            "source_status": observation.get("status"),
            "records_count": observation.get("row_count", 0),
            "evidence_summary": evidence_summary,
        }
    )
    observation["source_card"] = source_card
    observation["redaction_applied"] = True
    observation["sensitive_output"] = False
    redaction = dict(observation.get("redaction") or {})
    redaction.update({"redaction_applied": True, "sensitive_output": False})
    observation["redaction"] = redaction
    observation["step_response_received"] = True
    return observation


def read_response_body(response: Any) -> bytes:
    body = response.read(MAX_RESPONSE_BYTES + 1)
    if len(body) > MAX_RESPONSE_BYTES:
        raise ValueError("response_too_large")
    return body


def classify_network_failure(reason_text: str) -> tuple[str, str, bool]:
    normalized = reason_text.lower()
    if "read operation timed out" in normalized or "read timed out" in normalized:
        return "timeout", "read_timeout", True
    if "timed out" in normalized or "timeout" in normalized:
        return "timeout", "timeout", False
    if "nodename nor servname" in normalized or "name or service not known" in normalized:
        return "failed", "dns_resolution_failed", False
    return "failed", reason_text, False


def result_envelope(
    *,
    case: str,
    status: str,
    dry_run: bool,
    dataagent_api_attempted: bool,
    http_request_sent: bool,
    step_response_received: bool,
    model_answer_extracted: bool,
    normalized_observation: dict[str, Any],
) -> dict[str, Any]:
    return {
        "mode": "live_dry_run",
        "case": case,
        "status": status,
        "endpoint": ENDPOINT,
        "method": "POST",
        "dry_run": dry_run,
        "dataagent_api_attempted": dataagent_api_attempted,
        "http_request_sent": http_request_sent,
        "step_response_received": step_response_received,
        "model_answer_extracted": model_answer_extracted,
        "real_dataagent_api_called": http_request_sent,
        "hive_called": False,
        "sql_submitted": False,
        "normalized_observation": normalized_observation,
    }


def run_status_semantics_self_test() -> dict[str, Any]:
    source_status, failure_reason, http_request_sent = classify_network_failure("The read operation timed out")
    observation = source_failure_observation(
        source_status=source_status,
        failure_reason=failure_reason,
        response_type="network_error",
        dataagent_api_attempted=True,
        http_request_sent=http_request_sent,
    )
    source_quality = observation["source_quality"]
    checks = {
        "dataagent_api_attempted_true": source_quality.get("dataagent_api_attempted") is True,
        "http_request_sent_true": source_quality.get("http_request_sent") is True,
        "step_response_received_false": source_quality.get("step_response_received") is False,
        "model_answer_extracted_false": source_quality.get("model_answer_extracted") is False,
        "read_timeout_reason": source_quality.get("failure_reason") == "read_timeout",
        "source_status_timeout": observation.get("status") == "timeout",
        "hive_called_false": source_quality.get("hive_called") is False,
        "sql_submitted_false": source_quality.get("sql_submitted") is False,
        "real_dataagent_api_called_aliases_http_request_sent": (
            source_quality.get("real_dataagent_api_called") is source_quality.get("http_request_sent")
        ),
    }
    return {
        "mode": "self_test_status_semantics",
        "status": "PASS" if all(checks.values()) else "FAILED",
        "checks": checks,
        "observation": observation,
    }


def live_dry_run(args: argparse.Namespace) -> dict[str, Any]:
    if not args.allow_live_dry_run:
        return {
            "mode": "live_dry_run",
            "status": "BLOCKED",
            "reason": "live dry-run requires explicit --allow-live-dry-run",
            "real_dataagent_api_called": False,
            "dataagent_api_attempted": False,
            "http_request_sent": False,
            "step_response_received": False,
            "model_answer_extracted": False,
            "hive_called": False,
            "sql_submitted": False,
        }
    payload = build_payload(args.case)
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(ENDPOINT, data=body, method="POST")
    request.add_header("Content-Type", "application/json")
    request.add_header("Accept", "application/json")
    try:
        with urllib.request.urlopen(request, timeout=http_timeout_seconds()) as response:
            http_status = int(response.getcode())
            content_type = response.headers.get("Content-Type")
            response_body = read_response_body(response)
    except urllib.error.HTTPError as exc:
        source_status = "permission_denied" if exc.code in {401, 403} else "failed"
        observation = source_failure_observation(
            source_status=source_status,
            failure_reason=f"http_error_{exc.code}",
            http_status=exc.code,
            response_type="http_error",
            dataagent_api_attempted=True,
            http_request_sent=True,
        )
        return result_envelope(
            case=args.case,
            status="SOURCE_FAILURE_RECORDED",
            dry_run=True,
            dataagent_api_attempted=True,
            http_request_sent=True,
            step_response_received=False,
            model_answer_extracted=False,
            normalized_observation=observation,
        )
    except (urllib.error.URLError, socket.timeout, TimeoutError) as exc:
        reason = getattr(exc, "reason", exc)
        reason_text = str(reason)
        source_status, failure_reason, http_request_sent = classify_network_failure(reason_text)
        observation = source_failure_observation(
            source_status=source_status,
            failure_reason=failure_reason,
            response_type="network_error",
            dataagent_api_attempted=True,
            http_request_sent=http_request_sent,
        )
        return result_envelope(
            case=args.case,
            status="SOURCE_FAILURE_RECORDED",
            dry_run=True,
            dataagent_api_attempted=True,
            http_request_sent=http_request_sent,
            step_response_received=False,
            model_answer_extracted=False,
            normalized_observation=observation,
        )
    except ValueError as exc:
        observation = source_failure_observation(
            source_status="failed",
            failure_reason=str(exc),
            response_type="response_limit_error",
            dataagent_api_attempted=True,
            http_request_sent=True,
        )
        return result_envelope(
            case=args.case,
            status="SOURCE_FAILURE_RECORDED",
            dry_run=True,
            dataagent_api_attempted=True,
            http_request_sent=True,
            step_response_received=False,
            model_answer_extracted=False,
            normalized_observation=observation,
        )

    try:
        raw_payload = json.loads(response_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        observation = source_failure_observation(
            source_status="parse_error",
            failure_reason=f"parse_error:{type(exc).__name__}",
            http_status=http_status,
            response_type="parse_error",
            dataagent_api_attempted=True,
            http_request_sent=True,
        )
        observation["warnings"].append("parse_error_not_no_risk_evidence")
        return result_envelope(
            case=args.case,
            status="SOURCE_FAILURE_RECORDED",
            dry_run=True,
            dataagent_api_attempted=True,
            http_request_sent=True,
            step_response_received=False,
            model_answer_extracted=False,
            normalized_observation=observation,
        )

    if args.probe_response_shape:
        return {
            "mode": "response_shape_probe",
            "case": args.case,
            "status": "SHAPE_PROBE_RECORDED",
            "endpoint": ENDPOINT,
            "method": "POST",
            "dry_run": True,
            "dataagent_api_attempted": True,
            "http_request_sent": True,
            "step_response_received": True,
            "model_answer_extracted": False,
            "real_dataagent_api_called": True,
            "hive_called": False,
            "sql_submitted": False,
            "response_shape_probe": response_shape_summary(
                raw_payload,
                http_status=http_status,
                content_type=content_type,
                response_size_bytes=len(response_body),
            ),
        }

    normalized = normalize_dataagent_response(raw_payload)
    observation = apply_live_dry_run_boundary(normalized, http_status=http_status)
    return result_envelope(
        case=args.case,
        status="PASS" if observation.get("status") == "sql_generated" else "SOURCE_RESULT_RECORDED",
        dry_run=True,
        dataagent_api_attempted=True,
        http_request_sent=True,
        step_response_received=True,
        model_answer_extracted=bool(observation.get("model_answer_extracted")),
        normalized_observation=observation,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="DataAgent local live parity dry-run scaffold.")
    parser.add_argument("--mock", action="store_true", help="Normalize the cloud Skill mock response.")
    parser.add_argument("--print-payload", action="store_true", help="Print local dry-run Conversational API payload.")
    parser.add_argument("--live-dry-run", action="store_true", help="Future live HTTP dry-run mode; disabled by default.")
    parser.add_argument("--allow-live-dry-run", action="store_true", help="Required with --live-dry-run.")
    parser.add_argument("--probe-response-shape", action="store_true", help="Probe sanitized live response envelope shape.")
    parser.add_argument("--self-test-status-semantics", action="store_true", help="Run local status field semantics self-test.")
    parser.add_argument("--case", choices=sorted(CASE_DEFINITIONS), default="single_user_ato")
    parser.add_argument("--json", action="store_true", help="Emit JSON.")
    args = parser.parse_args(argv)

    if args.probe_response_shape and not (args.live_dry_run and args.allow_live_dry_run):
        result = {
            "status": "BLOCKED",
            "reason": "--probe-response-shape requires --live-dry-run --allow-live-dry-run",
            "real_dataagent_api_called": False,
            "dataagent_api_attempted": False,
            "http_request_sent": False,
            "step_response_received": False,
            "model_answer_extracted": False,
            "hive_called": False,
            "sql_submitted": False,
        }
        exit_code = 2
    elif args.live_dry_run:
        result = live_dry_run(args)
        exit_code = 0 if result.get("status") != "BLOCKED" else 2
    elif args.self_test_status_semantics:
        result = run_status_semantics_self_test()
        exit_code = 0 if result["status"] == "PASS" else 1
    elif args.print_payload:
        result = print_payload(args.case)
        exit_code = 0
    elif args.mock:
        result = run_mock()
        exit_code = 0 if result["status"] == "PASS" else 1
    else:
        result = {
            "status": "BLOCKED",
            "reason": "choose --mock, --print-payload, or --live-dry-run",
            "real_dataagent_api_called": False,
            "dataagent_api_attempted": False,
            "http_request_sent": False,
            "step_response_received": False,
            "model_answer_extracted": False,
            "hive_called": False,
            "sql_submitted": False,
        }
        exit_code = 2

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(result.get("status", result.get("mode", "UNKNOWN")))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
