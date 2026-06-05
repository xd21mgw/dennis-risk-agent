#!/usr/bin/env python3
"""Normalize mock DataAgent step-based JSON responses.

This module performs local parsing only. It does not call DataAgent, Hive, or
any internal platform.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from dataagent_sql_quality_gate import evaluate_dataagent_sql_quality


SOURCE_NAME = "dataagent_hive"
MODEL_ANSWER = "MODEL_ANSWER"
STEP_TYPES = {"MODEL_THINKING", "TOOL_CALL", "MODEL_ANSWER", "AGENT_END"}
STEP_CONTAINER_PATHS = (
    ("steps",),
    ("messages",),
    ("events",),
    ("data",),
    ("data", "steps"),
    ("data", "messages"),
    ("data", "events"),
    ("result", "steps"),
    ("result", "messages"),
    ("result", "events"),
)
ANSWER_FIELD_PATHS = (
    ("answer",),
    ("model_answer",),
    ("result", "answer"),
    ("data", "answer"),
)
CONTENT_FALLBACK_PATHS = (
    ("content",),
    ("message", "content"),
    ("data", "content"),
    ("result", "content"),
)
SENSITIVE_FIELD_RE = re.compile(
    r"\b(phone|cookie|token|session|header|authorization|password|email|id_card)\b",
    re.IGNORECASE,
)
PERMISSION_RE = re.compile(r"(permission\s*denied|not\s*authorized|unauthorized|权限|无权限|denied)", re.IGNORECASE)
TIMEOUT_RE = re.compile(r"(timeout|timed\s*out|超时)", re.IGNORECASE)
NO_DATA_RE = re.compile(r"(no\s*data|no\s*rows|0\s*rows|empty\s*result|无数据|没有数据|未查询到|未发现)", re.IGNORECASE)
ERROR_RE = re.compile(r"(error|failed|exception|失败|报错)", re.IGNORECASE)
SQL_FENCE_RE = re.compile(r"```sql\s*(.*?)```", re.IGNORECASE | re.DOTALL)
SQL_SELECT_RE = re.compile(r"((?:WITH|SELECT)\s+.*?)(?:\n\n|$)", re.IGNORECASE | re.DOTALL)
TABLE_RE = re.compile(r"\b[a-zA-Z_][\w]*\.[a-zA-Z_][\w]*(?:\.[a-zA-Z_][\w]*)?\b")


def load_json(path: Path | None) -> Any:
    text = sys.stdin.read() if path is None else path.read_text(encoding="utf-8")
    return json.loads(text)


def step_type(step: Any) -> str | None:
    if not isinstance(step, dict):
        return None
    for candidate in step_payload_candidates(step):
        for key in ("type", "step_type", "stepType", "subType", "subtype", "name", "event"):
            value = candidate.get(key)
            if isinstance(value, str) and value.upper() in STEP_TYPES:
                return value.upper()
        role = candidate.get("role")
        if isinstance(role, str) and role.upper() == MODEL_ANSWER:
            return MODEL_ANSWER
    return None


def step_payload_candidates(step: dict[str, Any]) -> list[dict[str, Any]]:
    candidates = [step]
    data = step.get("data")
    if isinstance(data, dict):
        step_data = data.get("stepData")
        if isinstance(step_data, dict):
            candidates.append(step_data)
            component_info = step_data.get("componentInfo")
            if isinstance(component_info, dict):
                candidates.append(component_info)
                props = component_info.get("props")
                if isinstance(props, dict):
                    candidates.append(props)
    return candidates


def step_content(step: dict[str, Any]) -> str:
    for candidate in step_payload_candidates(step):
        for key in ("content", "text", "message", "answer", "output"):
            value = candidate.get(key)
            if isinstance(value, str):
                return value
            if isinstance(value, dict):
                nested = value.get("content") or value.get("text")
                if isinstance(nested, str):
                    return nested
    return ""


def get_path(payload: Any, path: tuple[str, ...]) -> Any:
    value = payload
    for key in path:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def iter_choice_content(payload: Any) -> list[str]:
    if not isinstance(payload, dict):
        return []
    choices = payload.get("choices")
    if not isinstance(choices, list):
        return []
    contents: list[str] = []
    for choice in choices:
        if not isinstance(choice, dict):
            continue
        for container_key in ("message", "delta"):
            container = choice.get(container_key)
            if isinstance(container, dict):
                content = container.get("content")
                if isinstance(content, str) and content.strip():
                    contents.append(content)
    return contents


def iter_steps(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []
    for path in STEP_CONTAINER_PATHS:
        value = get_path(payload, path)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    return []


def extract_model_answer(payload: Any, steps: list[dict[str, Any]] | None = None) -> tuple[str, list[str], str]:
    steps = steps if steps is not None else iter_steps(payload)
    seen_types = [step_type(step) or "UNKNOWN" for step in steps]
    answers = [step_content(step) for step in steps if step_type(step) == MODEL_ANSWER and step_content(step)]
    if answers:
        return "\n\n".join(answers), seen_types, "model_answer_step"
    if isinstance(payload, dict):
        for path in ANSWER_FIELD_PATHS:
            direct = get_path(payload, path)
            if isinstance(direct, str) and direct.strip():
                return direct, seen_types, "answer_field"
        choice_contents = iter_choice_content(payload)
        if choice_contents:
            return "\n\n".join(choice_contents), seen_types, "content_fallback"
        for path in CONTENT_FALLBACK_PATHS:
            direct = get_path(payload, path)
            if isinstance(direct, str) and direct.strip():
                return direct, seen_types, "content_fallback"
    return "", seen_types, "missing"


def collect_first_value(value: Any, keys: set[str]) -> Any:
    if isinstance(value, dict):
        for key, nested in value.items():
            if key in keys and nested not in (None, ""):
                return nested
        for nested in value.values():
            found = collect_first_value(nested, keys)
            if found not in (None, ""):
                return found
    elif isinstance(value, list):
        for nested in value:
            found = collect_first_value(nested, keys)
            if found not in (None, ""):
                return found
    return None


def extract_tool_call_provenance(steps: list[dict[str, Any]], payload: Any | None = None) -> tuple[dict[str, Any], int]:
    provenance: dict[str, Any] = {}
    sensitive_count = 0
    sources = [step for step in steps if step_type(step) == "TOOL_CALL"]
    if payload is not None:
        sources.append(payload)
    for source in sources:
        query_id = collect_first_value(source, {"query_id", "queryId", "queryID", "sql_id", "sqlId"})
        trace_id = collect_first_value(source, {"trace_id", "traceId", "traceID"})
        generated_sql = collect_first_value(source, {"generated_sql", "generatedSql", "sql"})
        if query_id and "query_id" not in provenance:
            safe_query_id, count = redact_sensitive_text(str(query_id))
            provenance["query_id"] = safe_query_id
            sensitive_count += count
        if trace_id and "trace_id" not in provenance:
            safe_trace_id, count = redact_sensitive_text(str(trace_id))
            provenance["trace_id"] = safe_trace_id
            sensitive_count += count
        if generated_sql and "generated_sql" not in provenance:
            safe_sql, count = redact_sensitive_text(str(generated_sql).strip())
            provenance["generated_sql"] = safe_sql
            provenance["source_tables"] = extract_source_tables(safe_sql)
            sensitive_count += count
    if provenance:
        provenance["provenance_only_not_business_conclusion"] = True
    return provenance, sensitive_count


def redact_sensitive_text(text: str) -> tuple[str, int]:
    count = len(SENSITIVE_FIELD_RE.findall(text))
    return SENSITIVE_FIELD_RE.sub("redacted_sensitive_field", text), count


def find_sql_text(answer: str) -> str | None:
    match = SQL_FENCE_RE.search(answer)
    if match:
        return match.group(1).strip()
    match = SQL_SELECT_RE.search(answer)
    if match:
        return match.group(1).strip()
    return None


def extract_sql(answer: str) -> tuple[str | None, int]:
    raw_sql = find_sql_text(answer)
    if raw_sql:
        return redact_sensitive_text(raw_sql)
    return None, 0


def split_table_row(line: str) -> list[str]:
    stripped = line.strip().strip("|")
    return [cell.strip() for cell in stripped.split("|")]


def is_separator_row(line: str) -> bool:
    cells = split_table_row(line)
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell or "") for cell in cells)


def parse_markdown_table(answer: str) -> tuple[list[str], list[dict[str, Any]], int]:
    lines = [line.rstrip() for line in answer.splitlines()]
    sensitive_blocked = 0
    for index, line in enumerate(lines[:-1]):
        if "|" not in line or "|" not in lines[index + 1] or not is_separator_row(lines[index + 1]):
            continue
        columns = split_table_row(line)
        safe_columns: list[str] = []
        keep_indexes: list[int] = []
        for column_index, column in enumerate(columns):
            if SENSITIVE_FIELD_RE.search(column):
                sensitive_blocked += 1
                continue
            safe_column, count = redact_sensitive_text(column)
            sensitive_blocked += count
            safe_columns.append(safe_column)
            keep_indexes.append(column_index)

        rows: list[dict[str, Any]] = []
        for row_line in lines[index + 2 :]:
            if "|" not in row_line or is_separator_row(row_line):
                break
            cells = split_table_row(row_line)
            if len(cells) < len(columns):
                break
            row: dict[str, Any] = {}
            for output_index, original_index in enumerate(keep_indexes):
                value = cells[original_index]
                safe_value, count = redact_sensitive_text(value)
                sensitive_blocked += count
                row[safe_columns[output_index]] = safe_value
            if row:
                rows.append(row)
        return safe_columns, rows, sensitive_blocked
    return [], [], 0


def extract_source_tables(text: str) -> list[str]:
    tables = sorted(set(TABLE_RE.findall(text)))
    return [table for table in tables if not table.startswith("http")]


def infer_status(
    answer: str,
    *,
    generated_sql: str | None,
    row_count: int,
    tool_call_generated_sql: str | None = None,
) -> tuple[str, str | None]:
    if not answer.strip():
        if tool_call_generated_sql:
            return "sql_generated", "tool_call_sql_provenance_only"
        return "source_schema_drift", "missing_model_answer"
    if PERMISSION_RE.search(answer):
        return "permission_denied", "permission_denied"
    if TIMEOUT_RE.search(answer):
        return "timeout", "timeout"
    if ERROR_RE.search(answer):
        return "failed", "dataagent_error"
    if NO_DATA_RE.search(answer):
        return "no_data", "model_answer_reported_no_data"
    if row_count > 0:
        return "completed", None
    if generated_sql:
        return "sql_generated", None
    return "parse_error", "unrecognized_model_answer"


def normalize_dataagent_response(payload: Any) -> dict[str, Any]:
    steps = iter_steps(payload)
    answer, raw_step_types, model_answer_source = extract_model_answer(payload, steps)
    tool_call_provenance, tool_sensitive_count = extract_tool_call_provenance(steps, payload)
    safe_answer, answer_sensitive_count = redact_sensitive_text(answer)
    raw_model_answer_sql = find_sql_text(answer)
    generated_sql, sql_sensitive_count = (
        redact_sensitive_text(raw_model_answer_sql) if raw_model_answer_sql else (None, 0)
    )
    generated_sql_source = "MODEL_ANSWER" if generated_sql else None
    if not generated_sql and tool_call_provenance.get("generated_sql"):
        generated_sql = str(tool_call_provenance["generated_sql"])
        generated_sql_source = "TOOL_CALL_PROVENANCE_ONLY"
    columns, result_rows, table_sensitive_count = parse_markdown_table(safe_answer)
    row_count = len(result_rows)
    status, status_reason = infer_status(
        safe_answer,
        generated_sql=generated_sql,
        row_count=row_count,
        tool_call_generated_sql=tool_call_provenance.get("generated_sql"),
    )
    source_tables = extract_source_tables(generated_sql or safe_answer)
    if tool_call_provenance.get("source_tables"):
        source_tables = sorted(set(source_tables + list(tool_call_provenance["source_tables"])))
    sql_quality_gate = evaluate_dataagent_sql_quality(
        raw_model_answer_sql or generated_sql,
        model_answer_text=answer,
    )
    sensitive_blocked_count = answer_sensitive_count + sql_sensitive_count + table_sensitive_count + tool_sensitive_count

    permission_status = "permission_denied" if status == "permission_denied" else "ok"
    if status in {"failed", "timeout", "parse_error", "source_schema_drift"}:
        permission_status = "unknown"
    if status == "sql_generated":
        permission_status = "not_started"

    warnings: list[str] = []
    if sensitive_blocked_count:
        warnings.append(f"sensitive_fields_blocked_count={sensitive_blocked_count}")
    if any(step_type != MODEL_ANSWER for step_type in raw_step_types):
        warnings.append("non_MODEL_ANSWER_steps_ignored_for_evidence")
    if tool_call_provenance:
        warnings.append("TOOL_CALL_provenance_not_business_conclusion")
    if model_answer_source == "content_fallback":
        warnings.append("content_fallback_used_as_model_answer_source")
    if status == "sql_generated":
        warnings.append("sql_generated_not_executed_evidence")
    if sql_quality_gate.get("gate_status") == "block":
        warnings.append("sql_quality_gate_blocked_dry_run_false")
    elif sql_quality_gate.get("gate_status") == "pass":
        warnings.append("sql_quality_gate_passed_but_dry_run_false_still_requires_authorization")
    if status in {"no_data", "permission_denied", "failed", "timeout", "parse_error", "source_schema_drift"}:
        warnings.append(f"{status}_not_no_risk_evidence")

    request_id = None
    runtime_scope_id = None
    query_id = None
    trace_id = None
    if isinstance(payload, dict):
        request_id = payload.get("request_id")
        runtime_scope_id = payload.get("session_id")
        query_id = payload.get("query_id") or tool_call_provenance.get("query_id")
        trace_id = payload.get("trace_id") or tool_call_provenance.get("trace_id")

    no_data_reason = status_reason if status == "no_data" else None
    error_message = status_reason if status in {"failed", "timeout", "permission_denied", "parse_error", "source_schema_drift"} else None
    if error_message:
        error_message, blocked = redact_sensitive_text(error_message)
        sensitive_blocked_count += blocked

    dry_run = status == "sql_generated"
    step_response_received = bool(steps)
    model_answer_extracted = bool(answer.strip())
    source_quality = {
        "source_name": SOURCE_NAME,
        "permission_status": permission_status,
        "response_type": "step_based_json_model_answer",
        "reliability_level": "mock_normalized_contract",
        "failure_reason": status_reason,
        "no_data_not_risk_exclusion": True,
        "pending_execution_not_evidence": status in {"pending", "running", "sql_generated"},
        "dataagent_api_attempted": False,
        "http_request_sent": False,
        "step_response_received": step_response_received,
        "model_answer_extracted": model_answer_extracted,
        "model_answer_source": model_answer_source,
        "dataagent_called": False,
        "hive_called": False,
        "dry_run": dry_run,
        "sql_submitted": False,
        "sql_quality_gate_status": sql_quality_gate.get("gate_status"),
        "dry_run_false_eligible": sql_quality_gate.get("dry_run_false_eligible") is True,
        "dry_run_false_execution_allowed": False,
        "normalized_from_mock": True,
    }
    source_card = {
        "source_name": SOURCE_NAME,
        "source_status": status,
        "evidence_summary": build_evidence_summary(status, row_count, generated_sql),
        "records_count": row_count,
    }
    redaction = {
        "redaction_applied": True,
        "sensitive_output": False,
        "blocked_sensitive_fields_count": sensitive_blocked_count,
    }
    return {
        "schema_version": "dataagent_normalized_response_v1",
        "request_id": request_id,
        "session_id": runtime_scope_id,
        "query_id": query_id,
        "status": status,
        "model_answer_source": model_answer_source,
        "generated_sql": generated_sql,
        "generated_sql_source": generated_sql_source,
        "result_rows": result_rows,
        "columns": columns,
        "row_count": row_count,
        "error_message": error_message,
        "permission_status": permission_status,
        "data_freshness": None,
        "source_tables": source_tables,
        "query_time_range": {},
        "warnings": warnings,
        "no_data_reason": no_data_reason,
        "trace_id": trace_id,
        "sql_quality_gate": sql_quality_gate,
        "source_quality": source_quality,
        "tool_call_provenance": tool_call_provenance,
        "source_card": source_card,
        "source_checkpoint_private": {
            "raw_references": [],
            "downstream_source_chaining": [],
        },
        "redaction": redaction,
        "redaction_applied": True,
        "sensitive_output": False,
        "raw_step_types_observed": raw_step_types,
        "step_response_received": step_response_received,
        "model_answer_extracted": model_answer_extracted,
    }


def build_evidence_summary(status: str, row_count: int, generated_sql: str | None) -> str:
    if status == "completed":
        return f"DataAgent MODEL_ANSWER normalized with {row_count} row(s)."
    if status == "no_data":
        return "DataAgent MODEL_ANSWER reported no rows for the bounded query."
    if status == "permission_denied":
        return "DataAgent MODEL_ANSWER reported permission denial."
    if status == "timeout":
        return "DataAgent MODEL_ANSWER reported timeout."
    if status == "sql_generated" and generated_sql:
        return "DataAgent MODEL_ANSWER generated SQL only; no query result was executed."
    if status == "parse_error":
        return "DataAgent response content existed but could not be normalized as evidence."
    if status == "source_schema_drift":
        return "DataAgent response shape did not expose MODEL_ANSWER or supported content fallback."
    return "DataAgent MODEL_ANSWER could not be normalized as completed evidence."


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Normalize a mock DataAgent step-based JSON response.")
    parser.add_argument("--input", help="Path to mock step-based JSON. Reads stdin when omitted.")
    parser.add_argument("--json", action="store_true", help="Emit JSON. This is the default.")
    args = parser.parse_args(argv)

    payload = load_json(Path(args.input) if args.input else None)
    normalized = normalize_dataagent_response(payload)
    print(json.dumps(normalized, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
