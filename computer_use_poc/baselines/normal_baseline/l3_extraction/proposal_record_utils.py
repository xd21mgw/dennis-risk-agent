"""Lightweight raw observation helpers for proposal preparation.

This module is intentionally limited to source-record shaping, safe previews,
and simple value/path helpers. It must not contain replay, support/miss
recomputation, baseline, ranking, or verified-strategy logic.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable


SENSITIVE_KEY_PATTERN = re.compile(
    r"(authorization|cookie|credential|header|password|secret|session|storageState|token)",
    re.IGNORECASE,
)
REDACTED = "[REDACTED:sensitive]"


def load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def records_from_e2e_contract(data: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for user in data.get("users", []):
        if not isinstance(user, dict):
            continue
        user_id = str(user.get("user_id") or "")
        sources = user.get("sources") or {}
        if not isinstance(sources, dict):
            continue
        for source_name, source_payload in sources.items():
            if not isinstance(source_payload, dict):
                continue
            for action_or_layer, action_payload in source_payload.items():
                if not isinstance(action_payload, dict):
                    continue
                raw_body = action_payload.get("raw_body")
                status = str(action_payload.get("source_status") or "")
                if raw_body is None or status in {"not_exported", "to_be_exported", "no_data", "blocked", "timeout"}:
                    continue
                records.append({
                    "user_id": user_id,
                    "source_name": action_payload.get("source_name") or source_name,
                    "source_action": action_payload.get("action") or action_or_layer,
                    "action_or_layer": action_or_layer,
                    "payload": raw_body,
                })
    return records


def coerce_observation_records(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if not isinstance(data, dict):
        return []
    if data.get("schema_version") == "e2e_risk_observation_input_contract_v0_1":
        return records_from_e2e_contract(data)
    for key in ("records", "observations", "snapshots", "items"):
        if isinstance(data.get(key), list):
            return [item for item in data[key] if isinstance(item, dict)]
    return [data]


def payload_for_record(record: dict[str, Any]) -> Any:
    for key in ("payload", "raw_data", "data", "snapshot", "observation", "source_observation"):
        if key in record:
            return record[key]
    return record


def flatten_payload(value: Any, prefix: str = "") -> Iterable[tuple[str, Any]]:
    if isinstance(value, dict):
        for key, child in value.items():
            child_prefix = f"{prefix}.{key}" if prefix else str(key)
            yield from flatten_payload(child, child_prefix)
    elif isinstance(value, list):
        if all(not isinstance(item, (dict, list)) for item in value):
            yield prefix, value
        else:
            for child in value:
                yield from flatten_payload(child, prefix)
    elif prefix:
        yield prefix, value


def source_key(record: dict[str, Any]) -> str:
    source = str(record.get("source_name") or record.get("source") or "unknown_source")
    action = str(record.get("source_action") or record.get("action") or record.get("action_or_layer") or source)
    return f"{source}.{action}"


def value_shape(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "list"
    if isinstance(value, dict):
        return "dict"
    return type(value).__name__


def is_sensitive_path(path: str | None) -> bool:
    return bool(path and SENSITIVE_KEY_PATTERN.search(path))


def _safe_preview_value(value: Any, *, path: str = "", max_len: int = 160) -> Any:
    if is_sensitive_path(path):
        return REDACTED
    if isinstance(value, dict):
        preview: dict[str, Any] = {}
        for idx, (key, child) in enumerate(value.items()):
            if idx >= 20:
                preview["__truncated__"] = True
                break
            child_path = f"{path}.{key}" if path else str(key)
            preview[str(key)] = _safe_preview_value(child, path=child_path, max_len=max_len)
        return preview
    if isinstance(value, list):
        return [_safe_preview_value(item, path=path, max_len=max_len) for item in value[:5]]
    if isinstance(value, str):
        if len(value) > max_len:
            return value[:max_len] + "...[truncated]"
        return value
    return value


def safe_preview(value: Any, *, path: str | None = None, max_len: int = 160) -> Any:
    """Return a bounded preview that redacts credential-like paths."""
    return _safe_preview_value(value, path=path or "", max_len=max_len)


def extract_observation_text(record: dict[str, Any], *, max_len: int = 2000) -> str:
    preview = safe_preview(payload_for_record(record), max_len=240)
    text = json.dumps(preview, ensure_ascii=False, sort_keys=True)
    if len(text) > max_len:
        return text[:max_len] + "...[truncated]"
    return text


def build_prompt_input_summary(records: list[dict[str, Any]], *, sample_limit: int = 3) -> dict[str, Any]:
    summaries = []
    for record in records[:sample_limit]:
        summaries.append({
            "source_key": source_key(record),
            "user_id": str(record.get("user_id") or record.get("uid") or ""),
            "payload_shape": value_shape(payload_for_record(record)),
            "safe_payload_preview": safe_preview(payload_for_record(record), max_len=160),
        })
    return {
        "record_count": len(records),
        "sample_limit": sample_limit,
        "sample_records": summaries,
    }
