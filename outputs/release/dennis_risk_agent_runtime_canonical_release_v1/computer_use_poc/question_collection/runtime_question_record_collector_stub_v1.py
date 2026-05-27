#!/usr/bin/env python3
"""Local append-only question_record collector stub.

This stub validates and appends sanitized question records to
runtime_logs/question_collection/question_records_YYYYMMDD.jsonl.

It does not access network, internal platforms, DataAgent, or release assets.
"""

from __future__ import annotations

import argparse
import copy
import datetime as _dt
import json
import sys
from pathlib import Path
from typing import Any


DEFAULT_OUTPUT_DIR = Path("runtime_logs/question_collection")
SENSITIVE_KEYWORDS = (
    "cookie",
    "token",
    "session",
    "header",
    "auth state",
    "authstate",
    "storage_state",
    "storage state",
    "phone",
    "mobile",
    "id_card",
    "idcard",
)


def load_record(input_path: str | None) -> dict[str, Any]:
    if input_path:
        raw = Path(input_path).read_text(encoding="utf-8")
    else:
        raw = sys.stdin.read()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid_json: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("record_must_be_json_object")
    return data


def is_sensitive_key(key: str) -> bool:
    lowered = key.lower()
    return any(marker in lowered for marker in SENSITIVE_KEYWORDS)


def sanitize(value: Any) -> Any:
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, child in value.items():
            if is_sensitive_key(key):
                result[key] = "[REDACTED]"
            else:
                result[key] = sanitize(child)
        return result
    if isinstance(value, list):
        return [sanitize(item) for item in value]
    return value


def validate_and_normalize(record: dict[str, Any]) -> dict[str, Any]:
    normalized = sanitize(copy.deepcopy(record))
    for required in ("agent_observed", "agent_suggested", "reviewer_final"):
        if required not in normalized or not isinstance(normalized[required], dict):
            raise ValueError(f"missing_or_invalid_required_layer: {required}")

    reviewer_final = normalized["reviewer_final"]
    decision = reviewer_final.get("reviewer_decision")
    if decision is None:
        reviewer_final["reviewer_decision"] = "pending"
    elif decision != "pending":
        raise ValueError("runtime_must_not_write_non_pending_reviewer_decision")

    return normalized


def output_path(output_dir: Path, now: _dt.datetime | None = None) -> Path:
    current = now or _dt.datetime.now()
    return output_dir / f"question_records_{current:%Y%m%d}.jsonl"


def append_record(record: dict[str, Any], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_path(output_dir)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True))
        handle.write("\n")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Append-only question_record collector stub")
    parser.add_argument("--input", help="Path to a question_record JSON file. Reads stdin when omitted.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Output directory for JSONL logs.")
    parser.add_argument("--dry-run", action="store_true", help="Print sanitized record without writing.")
    args = parser.parse_args()

    try:
        raw_record = load_record(args.input)
        normalized = validate_and_normalize(raw_record)
        if args.dry_run:
            print(json.dumps({"status": "dry_run", "record": normalized}, ensure_ascii=False, indent=2, sort_keys=True))
            return 0
        path = append_record(normalized, Path(args.output_dir))
        print(json.dumps({"status": "appended", "path": str(path)}, ensure_ascii=False, sort_keys=True))
        return 0
    except Exception as exc:  # noqa: BLE001 - local CLI should return structured failure.
        print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False, sort_keys=True), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
