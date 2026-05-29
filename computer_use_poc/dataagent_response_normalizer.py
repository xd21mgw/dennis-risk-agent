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


SOURCE_NAME = "dataagent_hive"
MODEL_ANSWER = "MODEL_ANSWER"
STEP_TYPES = {"MODEL_THINKING", "TOOL_CALL", "MODEL_ANSWER", "AGENT_END"}
SENSITIVE_FIELD_RE = re.compile(
    r"\b(phone|cookie|token|session|header|email|id_card)\b",
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
    for key in ("type", "step_type", "stepType", "name", "event"):
        value = step.get(key)
        if isinstance(value, str) and value.upper() in STEP_TYPES:
            return value.upper()
    role = step.get("role")
    if isinstance(role, str) and role.upper() == MODEL_ANSWER:
        return MODEL_ANSWER
    return None


def step_content(step: dict[str, Any]) -> str:
    for key in ("content", "text", "message", "answer", "output"):
        value = step.get(key)
        if isinstance(value, str):
            return value
        if isinstance(value, dict):
            nested = value.get("content") or value.get("text")
            if isinstance(nested, str):
                return nested
    return ""


def iter_steps(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []
    for key in ("steps", "data", "events", "messages"):
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    choices = payload.get("choices")
    if isinstance(choices, list):
        steps: list[dict[str, Any]] = []
        for choice in choices:
            if isinstance(choice, dict):
                message = choice.get("message")
                if isinstance(message, dict):
                    steps.append({"type": MODEL_ANSWER, "content": step_content(message)})
        return steps
    return []


def extract_model_answer(payload: Any) -> tuple[str, list[str]]:
    steps = iter_steps(payload)
    seen_types = [step_type(step) or "UNKNOWN" for step in steps]
    answers = [step_content(step) for step in steps if step_type(step) == MODEL_ANSWER and step_content(step)]
    if not answers and isinstance(payload, dict):
        direct = payload.get("model_answer") or payload.get("answer")
        if isinstance(direct, str):
            answers.append(direct)
    return "\n\n".join(answers), seen_types


def redact_sensitive_text(text: str) -> tuple[str, int]:
    count = len(SENSITIVE_FIELD_RE.findall(text))
    return SENSITIVE_FIELD_RE.sub("redacted_sensitive_field", text), count


def extract_sql(answer: str) -> tuple[str | None, int]:
    match = SQL_FENCE_RE.search(answer)
    if match:
        return redact_sensitive_text(match.group(1).strip())
    match = SQL_SELECT_RE.search(answer)
    if match:
        return redact_sensitive_text(match.group(1).strip())
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
        headers = split_table_row(line)
        safe_headers: list[str] = []
        keep_indexes: list[int] = []
        for header_index, header in enumerate(headers):
            if SENSITIVE_FIELD_RE.search(header):
                sensitive_blocked += 1
                continue
            safe_header, count = redact_sensitive_text(header)
            sensitive_blocked += count
            safe_headers.append(safe_header)
            keep_indexes.append(header_index)

        rows: list[dict[str, Any]] = []
        for row_line in lines[index + 2 :]:
            if "|" not in row_line or is_separator_row(row_line):
                break
            cells = split_table_row(row_line)
            if len(cells) < len(headers):
                break
            row: dict[str, Any] = {}
            for output_index, original_index in enumerate(keep_indexes):
                value = cells[original_index]
                safe_value, count = redact_sensitive_text(value)
                sensitive_blocked += count
                row[safe_headers[output_index]] = safe_value
            if row:
                rows.append(row)
        return safe_headers, rows, sensitive_blocked
    return [], [], 0


def extract_source_tables(text: str) -> list[str]:
    tables = sorted(set(TABLE_RE.findall(text)))
    return [table for table in tables if not table.startswith("http")]


def infer_status(answer: str, *, generated_sql: str | None, row_count: int) -> tuple[str, str | None]:
    if not answer.strip():
        return "failed", "missing_model_answer"
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
    return "failed", "unrecognized_model_answer"


def normalize_dataagent_response(payload: Any) -> dict[str, Any]:
    answer, raw_step_types = extract_model_answer(payload)
    safe_answer, answer_sensitive_count = redact_sensitive_text(answer)
    generated_sql, sql_sensitive_count = extract_sql(safe_answer)
    columns, result_rows, table_sensitive_count = parse_markdown_table(safe_answer)
    row_count = len(result_rows)
    status, status_reason = infer_status(safe_answer, generated_sql=generated_sql, row_count=row_count)
    source_tables = extract_source_tables(generated_sql or safe_answer)
    sensitive_blocked_count = answer_sensitive_count + sql_sensitive_count + table_sensitive_count

    permission_status = "permission_denied" if status == "permission_denied" else "ok"
    if status in {"failed", "timeout"}:
        permission_status = "unknown"
    if status == "sql_generated":
        permission_status = "not_started"

    warnings: list[str] = []
    if sensitive_blocked_count:
        warnings.append(f"sensitive_fields_blocked_count={sensitive_blocked_count}")
    if any(step_type != MODEL_ANSWER for step_type in raw_step_types):
        warnings.append("non_MODEL_ANSWER_steps_ignored_for_evidence")
    if status == "sql_generated":
        warnings.append("sql_generated_not_executed_evidence")
    if status in {"no_data", "permission_denied", "failed", "timeout"}:
        warnings.append(f"{status}_not_no_risk_evidence")

    request_id = None
    session_id = None
    query_id = None
    trace_id = None
    if isinstance(payload, dict):
        request_id = payload.get("request_id")
        session_id = payload.get("session_id")
        query_id = payload.get("query_id")
        trace_id = payload.get("trace_id")

    no_data_reason = status_reason if status == "no_data" else None
    error_message = status_reason if status in {"failed", "timeout", "permission_denied"} else None
    if error_message:
        error_message, blocked = redact_sensitive_text(error_message)
        sensitive_blocked_count += blocked

    dataagent_called = status != "sql_generated"
    dry_run = status == "sql_generated"
    source_quality = {
        "source_name": SOURCE_NAME,
        "permission_status": permission_status,
        "response_type": "step_based_json_model_answer",
        "reliability_level": "mock_normalized_contract",
        "failure_reason": status_reason,
        "no_data_not_risk_exclusion": True,
        "pending_execution_not_evidence": status in {"pending", "running", "sql_generated"},
        "dataagent_called": dataagent_called,
        "hive_called": dataagent_called,
        "dry_run": dry_run,
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
        "session_id": session_id,
        "query_id": query_id,
        "status": status,
        "generated_sql": generated_sql,
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
        "source_quality": source_quality,
        "source_card": source_card,
        "source_checkpoint_private": {
            "raw_references": [],
            "downstream_source_chaining": [],
        },
        "redaction": redaction,
        "redaction_applied": True,
        "sensitive_output": False,
        "raw_step_types_observed": raw_step_types,
        "model_answer_extracted": bool(answer.strip()),
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
