#!/usr/bin/env python3
"""Local semi-open pilot observation / feedback writer.

This script is a local-only bridge for semi-open pilot logs. It appends
observation records and user feedback records to markdown pilot logs, and
optionally appends high-value feedback to a runtime candidate queue CSV.

It does not access networks, internal platforms, DataAgent, auth state, or
release packages.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any


DEFAULT_LOG_DIR = Path("semi_open_pilot_logs")
DEFAULT_CANDIDATE_QUEUE_RELATIVE = Path("runtime_logs/question_collection/question_learning_candidate_queue_v1.csv")

CANDIDATE_QUEUE_HEADER = [
    "candidate_id",
    "timestamp",
    "source_channel",
    "linked_log_id",
    "user_prompt",
    "agent_answer_summary",
    "feedback_type",
    "feedback_text",
    "issue_tags",
    "suggested_fix_area",
    "priority",
    "review_status",
    "notes",
]

HIGH_VALUE_FEEDBACK = {
    "too_generic",
    "off_target",
    "wrong_intent",
    "needs_data",
    "timeout_bad_experience",
    "worth_learning",
    "unsafe_or_overexposed",
}

FOLLOWUP_QUERY_TERMS = {"查一下吧", "继续", "看下", "可以", "试一下"}

SENSITIVE_PATTERNS = [
    (re.compile(r"(?i)(cookie|session|token|header|authorization|auth_state|storageState)\s*[:=]\s*[^,\s]+"), "[CREDENTIAL_REDACTED]"),
    (re.compile(r"(?i)(access_token|refresh_token|session_id|auth_token)\s*[:=]\s*[^,\s]+"), "[CREDENTIAL_REDACTED]"),
    (re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"), "[PHONE_REDACTED]"),
]


def now_iso() -> str:
    return dt.datetime.now(dt.timezone(dt.timedelta(hours=8))).isoformat(timespec="seconds")


def load_json(input_path: str | None) -> dict[str, Any]:
    raw = Path(input_path).read_text(encoding="utf-8") if input_path else sys.stdin.read()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid_json: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("input_must_be_json_object")
    return data


def sanitize_text(value: Any) -> str:
    text = "" if value is None else str(value)
    for pattern, replacement in SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def sanitize_record(record: dict[str, Any]) -> dict[str, Any]:
    sanitized: dict[str, Any] = {}
    for key, value in record.items():
        key_lower = key.lower()
        if any(marker in key_lower for marker in ("cookie", "token", "session", "header", "auth_state", "storagestate")):
            sanitized[key] = "[REDACTED]"
        elif isinstance(value, dict):
            sanitized[key] = sanitize_record(value)
        elif isinstance(value, list):
            sanitized[key] = [sanitize_record(item) if isinstance(item, dict) else sanitize_text(item) for item in value]
        elif isinstance(value, str):
            sanitized[key] = sanitize_text(value)
        else:
            sanitized[key] = value
    return sanitized


def find_repo_root_from_script() -> Path | None:
    """Locate the repository root from this script path without using CWD."""
    script_path = Path(__file__).resolve()
    for parent in script_path.parents:
        if (parent / "computer_use_poc" / "question_collection").is_dir():
            return parent
    return None


def resolve_candidate_queue_path(candidate_queue_arg: str | None) -> tuple[Path, str]:
    if candidate_queue_arg:
        return Path(candidate_queue_arg).expanduser().resolve(), "explicit_arg"

    env_home = os.environ.get("DENNIS_AGENT_HOME")
    if env_home:
        return (Path(env_home).expanduser().resolve() / DEFAULT_CANDIDATE_QUEUE_RELATIVE), "dennis_agent_home"

    repo_root = find_repo_root_from_script()
    if repo_root:
        return (repo_root / DEFAULT_CANDIDATE_QUEUE_RELATIVE), "script_repo_root"

    return (Path.cwd() / DEFAULT_CANDIDATE_QUEUE_RELATIVE), "fallback_cwd"


def infer_feedback_type(message: str, linked_previous_record_id: str | None = None) -> tuple[str, float, list[str]]:
    normalized = message.strip().lower()
    tags: list[str] = []

    if re.search(r"api\s*key|cookie|token|session|header|太敏感|不该输出|泄露", normalized, re.I):
        return "unsafe_or_overexposed", 0.9, ["safety_boundary"]
    if "值得沉淀" in message or "记录下" in message or "后面修" in message:
        return "worth_learning", 0.9, ["learning_candidate"]
    if "等太久" in message or "卡住了" in message or "怎么还没结果" in message or "timeout" in normalized:
        return "timeout_bad_experience", 0.9, ["timeout", "bad_experience"]
    if "不是这个意思" in message or "你理解错了" in message or "意图不对" in message:
        return "wrong_intent", 0.9, ["routing_gap", "intent_mismatch"]
    if "答偏" in message:
        return "off_target", 0.85, ["routing_gap"]
    if "没查数据" in message or "实际查一下" in message or "查一下吧" in message or "能不能实际查" in message:
        return "needs_data", 0.9, ["needs_data"]
    if linked_previous_record_id and message.strip() in FOLLOWUP_QUERY_TERMS:
        return "needs_data", 0.75, ["followup_query"]
    if "太泛" in message or "都是方法论" in message or "没啥信息" in message:
        return "too_generic", 0.9, ["template_gap"]
    if "有用" in message or "可以" in message or "这个对" in message or "这个结论准" in message:
        return "useful", 0.8, ["positive_feedback"]
    return "unknown", 0.4, tags


def priority_for_feedback(feedback_type: str) -> str:
    if feedback_type == "unsafe_or_overexposed":
        return "P0"
    if feedback_type in {"wrong_intent", "off_target", "needs_data", "timeout_bad_experience"}:
        return "P1"
    if feedback_type in {"too_generic", "worth_learning"}:
        return "P2"
    return "P3"


def suggested_fix_area(feedback_type: str) -> str:
    mapping = {
        "too_generic": "answer_template",
        "off_target": "routing",
        "wrong_intent": "routing",
        "needs_data": "execution_or_evidence_plan",
        "timeout_bad_experience": "timeout_fallback",
        "worth_learning": "case_learning_note",
        "unsafe_or_overexposed": "safety_redaction",
        "useful": "none",
    }
    return mapping.get(feedback_type, "human_review")


def log_path(log_dir: Path, timestamp: str) -> Path:
    date = timestamp[:10] if timestamp else dt.date.today().isoformat()
    return log_dir / f"{date}.md"


def markdown_block(record_type: str, record: dict[str, Any]) -> str:
    title = "Observation Record" if record_type == "observation_record" else "Feedback Record"
    record_id = record.get("record_id") or record.get("feedback_id") or record.get("linked_previous_record_id") or "unknown"
    return (
        f"\n## {title}: {record_id}\n\n"
        "```json\n"
        f"{json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True)}\n"
        "```\n"
    )


def append_markdown_log(record_type: str, record: dict[str, Any], log_dir: Path) -> Path:
    timestamp = str(record.get("timestamp") or record.get("asked_at") or now_iso())
    path = log_path(log_dir, timestamp)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(markdown_block(record_type, record))
    return path


def ensure_candidate_queue_header(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists() or path.stat().st_size == 0:
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(CANDIDATE_QUEUE_HEADER)
        return

    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        existing_header = next(reader, [])
    if existing_header != CANDIDATE_QUEUE_HEADER:
        timestamp = dt.datetime.now().strftime("%Y%m%d%H%M%S")
        backup = path.with_name(f"{path.stem}.schema_mismatch_backup_{timestamp}{path.suffix}")
        path.replace(backup)
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(CANDIDATE_QUEUE_HEADER)


def append_candidate_queue(record: dict[str, Any], candidate_queue: Path) -> None:
    ensure_candidate_queue_header(candidate_queue)
    timestamp = str(record.get("timestamp") or now_iso())
    feedback_type = str(record.get("inferred_feedback_type") or "unknown")
    row = {
        "candidate_id": f"cand_{timestamp[:10].replace('-', '')}_{record.get('linked_previous_record_id', 'unlinked')}_{feedback_type}",
        "timestamp": timestamp,
        "source_channel": record.get("source_channel", "unknown"),
        "linked_log_id": record.get("linked_previous_record_id", ""),
        "user_prompt": sanitize_text(record.get("user_prompt", "")),
        "agent_answer_summary": sanitize_text(record.get("agent_answer_summary", "")),
        "feedback_type": feedback_type,
        "feedback_text": sanitize_text(record.get("sanitized_feedback_text", record.get("feedback_message", ""))),
        "issue_tags": ",".join(record.get("issue_tags", [])) if isinstance(record.get("issue_tags"), list) else record.get("issue_tags", ""),
        "suggested_fix_area": suggested_fix_area(feedback_type),
        "priority": priority_for_feedback(feedback_type),
        "review_status": "pending",
        "notes": "runtime feedback candidate; reviewer_final required before deposition",
    }
    with candidate_queue.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CANDIDATE_QUEUE_HEADER)
        writer.writerow(row)


def normalize_observation_record(data: dict[str, Any]) -> dict[str, Any]:
    record = sanitize_record(data)
    record.setdefault("timestamp", now_iso())
    record.setdefault("record_id", f"obs_{record['timestamp'].replace(':', '').replace('-', '')}")
    record.setdefault("user_feedback", {
        "feedback_type": "none",
        "feedback_text": "",
        "inferred_from_message": False,
        "confidence": 0.0,
        "linked_previous_record_id": "",
        "should_enter_candidate_queue": False,
    })
    return record


def normalize_feedback_record(data: dict[str, Any]) -> dict[str, Any]:
    sanitized = sanitize_record(data)
    timestamp = str(sanitized.get("timestamp") or now_iso())
    message = sanitize_text(sanitized.get("feedback_message") or sanitized.get("message") or "")
    linked = sanitized.get("linked_previous_record_id")
    inferred, confidence, tags = infer_feedback_type(message, str(linked) if linked else None)
    should_enter = inferred in HIGH_VALUE_FEEDBACK
    record = {
        "record_type": "feedback_record",
        "timestamp": timestamp,
        "source_channel": sanitized.get("source_channel", "unknown"),
        "feedback_message": message,
        "linked_previous_record_id": linked or "",
        "inferred_feedback_type": sanitized.get("inferred_feedback_type") or inferred,
        "confidence": sanitized.get("confidence", confidence),
        "should_enter_candidate_queue": sanitized.get("should_enter_candidate_queue", should_enter),
        "sanitized_feedback_text": sanitize_text(sanitized.get("sanitized_feedback_text") or message),
        "issue_tags": sanitized.get("issue_tags") or tags,
        "user_prompt": sanitized.get("user_prompt", ""),
        "agent_answer_summary": sanitized.get("agent_answer_summary", ""),
    }
    return record


def process_record(
    data: dict[str, Any],
    log_dir: Path,
    candidate_queue: Path,
    path_resolution: str,
    dry_run: bool = False,
) -> dict[str, Any]:
    record_type = data.get("record_type")
    if not record_type:
        record_type = "feedback_record" if ("feedback_message" in data or "message" in data) else "observation_record"
    if record_type not in {"observation_record", "feedback_record"}:
        raise ValueError("record_type_must_be_observation_record_or_feedback_record")

    if record_type == "observation_record":
        record = normalize_observation_record(data)
    else:
        record = normalize_feedback_record(data)

    if dry_run:
        return {
            "status": "dry_run",
            "record_type": record_type,
            "record": record,
            "candidate_queue_path": str(candidate_queue),
            "path_resolution": path_resolution,
        }

    path = append_markdown_log(record_type, record, log_dir)
    candidate_appended = False
    if record_type == "feedback_record" and record.get("should_enter_candidate_queue"):
        append_candidate_queue(record, candidate_queue)
        candidate_appended = True
    return {
        "status": "appended",
        "record_type": record_type,
        "log_path": str(path),
        "candidate_queue_path": str(candidate_queue),
        "path_resolution": path_resolution,
        "candidate_appended": candidate_appended,
    }


def run_self_test(candidate_queue: Path, path_resolution: str) -> dict[str, Any]:
    cases = [
        ("too_generic", {"record_type": "feedback_record", "source_channel": "KIM", "feedback_message": "太泛了", "linked_previous_record_id": "obs_001"}),
        ("wrong_intent", {"record_type": "feedback_record", "source_channel": "KIM", "feedback_message": "不是这个意思", "linked_previous_record_id": "obs_002"}),
        ("needs_data_followup", {"record_type": "feedback_record", "source_channel": "KIM", "feedback_message": "查一下吧", "linked_previous_record_id": "obs_003"}),
        ("worth_learning", {"record_type": "feedback_record", "source_channel": "KIM", "feedback_message": "这个值得沉淀", "linked_previous_record_id": "obs_004"}),
        ("useful", {"record_type": "feedback_record", "source_channel": "KIM", "feedback_message": "这个有用", "linked_previous_record_id": "obs_005"}),
        ("sensitive", {"record_type": "feedback_record", "source_channel": "KIM", "feedback_message": "这个不该输出 cookie=abc token=secret session=raw header=Bearer 13800138000", "linked_previous_record_id": "obs_006"}),
    ]
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        log_dir = base / "semi_open_pilot_logs"
        results = []
        for name, payload in cases:
            result = process_record(payload, log_dir, candidate_queue, path_resolution, dry_run=False)
            results.append({"case": name, **result})
        with candidate_queue.open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self_test_rows = {
            row.get("linked_log_id"): row
            for row in rows
            if row.get("linked_log_id") in {"obs_001", "obs_002", "obs_003", "obs_004", "obs_005", "obs_006"}
        }
        queue_text = "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in self_test_rows.values())
        log_text = "\n".join(path.read_text(encoding="utf-8") for path in log_dir.glob("*.md"))
        assertions = {
            "too_generic_candidate": self_test_rows.get("obs_001", {}).get("feedback_type") == "too_generic",
            "wrong_intent_candidate": self_test_rows.get("obs_002", {}).get("feedback_type") == "wrong_intent",
            "needs_data_candidate": self_test_rows.get("obs_003", {}).get("feedback_type") == "needs_data",
            "worth_learning_candidate": self_test_rows.get("obs_004", {}).get("feedback_type") == "worth_learning",
            "useful_not_candidate": "obs_005" not in self_test_rows,
            "sensitive_redacted": "abc" not in log_text and "secret" not in log_text and "13800138000" not in log_text and "Bearer" not in queue_text,
            "candidate_queue_path_present": all(result.get("candidate_queue_path") for result in results),
            "path_resolution_present": all(result.get("path_resolution") for result in results),
            "runtime_header_13_columns": list(rows[0].keys()) == CANDIDATE_QUEUE_HEADER if rows else False,
        }
        return {
            "status": "pass" if all(assertions.values()) else "fail",
            "candidate_queue_path": str(candidate_queue),
            "path_resolution": path_resolution,
            "assertions": assertions,
            "results": results,
        }


def main() -> int:
    parser = argparse.ArgumentParser(description="Append semi-open pilot observation or feedback records.")
    parser.add_argument("--input", help="Path to JSON input. Reads stdin when omitted.")
    parser.add_argument("--log-dir", default=str(DEFAULT_LOG_DIR), help="Append-only markdown pilot log directory.")
    parser.add_argument("--candidate-queue", help="Explicit runtime candidate queue CSV path.")
    parser.add_argument("--dry-run", action="store_true", help="Print normalized record without writing.")
    parser.add_argument("--self-test", action="store_true", help="Run local smoke tests in a temporary directory.")
    args = parser.parse_args()

    try:
        candidate_queue, path_resolution = resolve_candidate_queue_path(args.candidate_queue)
        if args.self_test:
            print(json.dumps(run_self_test(candidate_queue, path_resolution), ensure_ascii=False, indent=2, sort_keys=True))
            return 0
        data = load_json(args.input)
        result = process_record(data, Path(args.log_dir), candidate_queue, path_resolution, dry_run=args.dry_run)
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    except Exception as exc:  # noqa: BLE001 - CLI should fail closed with structured error.
        print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False, sort_keys=True), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
