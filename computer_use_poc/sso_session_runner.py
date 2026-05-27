#!/usr/bin/env python3
"""Controlled readonly SSO HTTP executor.

This runner is intentionally narrow:

- only whitelisted platform/action pairs are accepted;
- no arbitrary URL input is accepted;
- stdout is exactly one machine-parseable JSON observation;
- diagnostics go to stderr;
- authentication material and request headers are never printed.

The live runtime is expected to provide ``sso_session.SmartSSOSession``. In
local environments where that module is unavailable, the runner fails closed
with a structured ``blocked`` observation instead of falling back to curl or
manual credential handling.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import re
import sys
import time
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlencode


RELIABLE_WINDOW_DAYS = 7
RELIABLE_WINDOW_MS = RELIABLE_WINDOW_DAYS * 24 * 60 * 60 * 1000
ID_RE = re.compile(r"^[0-9]{1,20}$")
TS_RE = re.compile(r"^[0-9]{1,20}$")
RECALL_SOURCE = "2,0,1,3"
MAX_TIMEOUT_SECONDS = 120

PLATFORM_ALIASES = {
    "login_log": "user_login_unified_log",
    "user_login_unified_log": "user_login_unified_log",
}

ACTION_ALIASES = {
    "query_user_login_log": "query_user_login_log",
}

PLATFORM_ACTIONS = {
    ("user_login_unified_log", "query_user_login_log"): {
        "source_name": "user_login_unified_log",
        "method": "GET",
        "base_url": "https://user-center-workbench.corp.kuaishou.com/rest/unified/log/search",
    }
}

SENSITIVE_KEY_RE = re.compile(
    r"(cookie|token|session|header|authorization|password|passwd|api[_-]?key)",
    re.IGNORECASE,
)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def emit_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


def safe_id(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def sanitize_text(value: Any) -> str:
    text = str(value)
    text = SENSITIVE_KEY_RE.sub("redacted_sensitive_key", text)
    return text[:300]


def safe_error_message(value: Any) -> str:
    text = str(value)
    if "sso_session module unavailable" in text or "SmartSSOSession unavailable" in text:
        return "SSO executor module unavailable"
    return sanitize_text(text)


def validate_digits(value: str | None, field_name: str, pattern: re.Pattern[str]) -> str | None:
    if value is None:
        return None
    if not pattern.fullmatch(value):
        raise ValueError(f"{field_name} must match {pattern.pattern}")
    return value


def parse_timeout(value: str | None) -> int:
    if value is None:
        return 30
    if not re.fullmatch(r"^[0-9]{1,3}$", value):
        raise ValueError("timeout must be an integer second value")
    timeout = int(value)
    if timeout <= 0 or timeout > MAX_TIMEOUT_SECONDS:
        raise ValueError(f"timeout must be between 1 and {MAX_TIMEOUT_SECONDS}")
    return timeout


class EnvelopeArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        observation = build_observation(
            source_status="blocked",
            user_id=None,
            evidence_time_range=None,
            evidence_summary=f"Argument validation failed: {sanitize_text(message)}",
            source_quality={
                "permission_status": "not_started",
                "reliability_level": "none",
                "failure_reason": "argument_validation_failed",
            },
            real_platform_request_executed=False,
            error_message=message,
        )
        print(f"sso runner argument error: {message}", file=sys.stderr)
        emit_json(observation)
        raise SystemExit(2)


def build_time_range(from_ts: str | None, to_ts: str | None) -> tuple[int, int, dict[str, Any]]:
    now_ms = int(time.time() * 1000)
    default_window_used = False

    if (from_ts is None) ^ (to_ts is None):
        raise ValueError("from_timestamp and to_timestamp must be provided together")

    if from_ts is None and to_ts is None:
        to_ts_int = now_ms
        from_ts_int = now_ms - RELIABLE_WINDOW_MS
        default_window_used = True
    else:
        from_ts_int = int(from_ts or "0")
        to_ts_int = int(to_ts or "0")

    if from_ts_int >= to_ts_int:
        raise ValueError("from_timestamp must be < to_timestamp")

    window_ms = to_ts_int - from_ts_int
    over_reliable_window = window_ms > RELIABLE_WINDOW_MS
    metadata = {
        "reliable_window_days": RELIABLE_WINDOW_DAYS,
        "recall_source": RECALL_SOURCE,
        "default_window_used": default_window_used,
        "over_reliable_window": over_reliable_window,
        "login_log_window_incomplete": over_reliable_window,
        "offline_hive_required": over_reliable_window,
        "no_data_interpretation": "current_window_no_data_only",
        "over_window_no_data_is_counter_evidence": False,
        "over_window_no_data_is_log_cleanup_evidence": False,
    }
    return from_ts_int, to_ts_int, metadata


def build_user_login_url(user_id: str, from_ts: str | None, to_ts: str | None) -> tuple[str, dict[str, Any]]:
    from_ts_int, to_ts_int, metadata = build_time_range(from_ts, to_ts)
    params = {
        "userId": user_id,
        "did": "",
        "query": "",
        "recallSource": RECALL_SOURCE,
        "from_timestamp": str(from_ts_int),
        "to_timestamp": str(to_ts_int),
    }
    url = f"{PLATFORM_ACTIONS[('user_login_unified_log', 'query_user_login_log')]['base_url']}?{urlencode(params, safe=',')}"
    metadata["evidence_time_range"] = {
        "from_timestamp": from_ts_int,
        "to_timestamp": to_ts_int,
    }
    metadata["request_safe_id"] = safe_id(url)
    return url, metadata


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = EnvelopeArgumentParser(description="Controlled readonly SSO API executor.")
    parser.add_argument("--platform", choices=sorted(PLATFORM_ALIASES), help="Recommended runtime platform key.")
    parser.add_argument("--action", choices=sorted(ACTION_ALIASES), help="Recommended runtime action key.")
    parser.add_argument("--user-id", dest="user_id_dash")
    parser.add_argument("--timeout", default="30")
    parser.add_argument("--format", default="json", choices=["json"])

    # Backward-compatible parameters.
    parser.add_argument("--platform_key", choices=sorted(PLATFORM_ALIASES))
    parser.add_argument("--user_id")
    parser.add_argument("--from_timestamp")
    parser.add_argument("--to_timestamp")
    return parser.parse_args(argv)


def normalize_args(args: argparse.Namespace) -> tuple[str, str, str, str | None, str | None, int]:
    platform_raw = args.platform or args.platform_key
    if not platform_raw:
        raise ValueError("platform is required")
    platform = PLATFORM_ALIASES.get(platform_raw)
    if not platform:
        raise ValueError("unknown platform")

    if args.action:
        action = ACTION_ALIASES[args.action]
    else:
        action = "query_user_login_log"

    if (platform, action) not in PLATFORM_ACTIONS:
        raise ValueError("unsupported platform/action")

    user_id = validate_digits(args.user_id_dash or args.user_id, "user_id", ID_RE)
    if user_id is None:
        raise ValueError("user_id is required")
    from_ts = validate_digits(args.from_timestamp, "from_timestamp", TS_RE)
    to_ts = validate_digits(args.to_timestamp, "to_timestamp", TS_RE)
    timeout = parse_timeout(args.timeout)
    return platform, action, user_id, from_ts, to_ts, timeout


def build_observation(
    *,
    source_status: str,
    user_id: str | None,
    evidence_time_range: dict[str, Any] | None,
    evidence_summary: str,
    source_quality: dict[str, Any],
    real_platform_request_executed: bool,
    records_count: int | None = None,
    raw_reference_safe_id: str | None = None,
    error_message: str | None = None,
    extra_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    observation: dict[str, Any] = {
        "schema_version": "sso_runner_observation_v2",
        "source_name": "user_login_unified_log",
        "source_status": source_status,
        "user_id": user_id,
        "records_count": records_count if records_count is not None else 0,
        "evidence_time_range": evidence_time_range or {},
        "evidence_summary": evidence_summary,
        "source_quality": source_quality,
        "raw_reference_safe_id": raw_reference_safe_id,
        "collected_at": now_iso(),
        "redaction_applied": True,
        "real_platform_request_executed": real_platform_request_executed,
        "dataagent_called": False,
        "platform_write_action": False,
        "sensitive_output": False,
        "logs": [],
    }
    if error_message:
        observation["error"] = {"message": sanitize_text(error_message)}
    else:
        observation["error"] = None
    if extra_metadata:
        observation["metadata"] = extra_metadata
    return observation


def load_sso_session() -> Any:
    try:
        module = importlib.import_module("sso_session")
    except ImportError as exc:
        raise RuntimeError("sso_session module unavailable") from exc
    session_cls = getattr(module, "SmartSSOSession", None)
    if session_cls is None:
        raise RuntimeError("SmartSSOSession unavailable")
    return session_cls()


def call_sso_get(url: str, timeout: int) -> Any:
    session = load_sso_session()
    get = getattr(session, "get", None)
    if get is None:
        raise RuntimeError("SmartSSOSession.get unavailable")
    try:
        return get(url, timeout=timeout)
    except TypeError:
        return get(url)


def response_status(response: Any) -> int | None:
    return getattr(response, "status_code", None) if not isinstance(response, dict) else None


def response_text(response: Any) -> str:
    if isinstance(response, dict):
        return json.dumps(response, ensure_ascii=False)
    text = getattr(response, "text", None)
    if text is not None:
        return str(text)
    content = getattr(response, "content", None)
    if isinstance(content, bytes):
        return content.decode("utf-8", errors="ignore")
    return str(response)


def response_json(response: Any) -> Any:
    if isinstance(response, dict):
        return response
    json_func = getattr(response, "json", None)
    if callable(json_func):
        return json_func()
    return json.loads(response_text(response))


def looks_like_auth_html(text: str) -> bool:
    stripped = text.lstrip()[:3000]
    lower = stripped.lower()
    return (
        lower.startswith("<!doctype html")
        or lower.startswith("<html")
        or "<body" in lower
        or "window.location" in lower
        or "sso login" in lower
    )


def extract_records(payload: Any) -> list[Any]:
    candidates: list[Any] = []
    if isinstance(payload, list):
        return payload
    if not isinstance(payload, dict):
        return []
    for key in ("data", "result", "rows", "records", "list", "dataList"):
        value = payload.get(key)
        if isinstance(value, list):
            return value
        if isinstance(value, dict):
            candidates.append(value)
    for item in candidates:
        records = extract_records(item)
        if records:
            return records
    return []


def classify_json_payload(payload: Any) -> tuple[str, int, str, dict[str, Any]]:
    records = extract_records(payload)
    records_count = len(records)
    if records_count > 0:
        summary = f"Unified login log returned {records_count} record(s) in the requested window."
        status = "completed"
    else:
        summary = "Unified login log returned no visible records in the requested window."
        status = "no_data"
    quality = {
        "permission_status": "ok",
        "reliability_level": "api_json_summary",
        "no_data_not_risk_exclusion": status == "no_data",
        "raw_response_redacted": True,
    }
    return status, records_count, summary, quality


def execute_login_log(user_id: str, from_ts: str | None, to_ts: str | None, timeout: int) -> dict[str, Any]:
    url, metadata = build_user_login_url(user_id, from_ts, to_ts)
    evidence_time_range = metadata.pop("evidence_time_range")
    request_safe_id = metadata.pop("request_safe_id")

    try:
        response = call_sso_get(url, timeout)
    except TimeoutError as exc:
        return build_observation(
            source_status="timeout",
            user_id=user_id,
            evidence_time_range=evidence_time_range,
            evidence_summary="Unified login log request timed out.",
            source_quality={"permission_status": "unknown", "failure_reason": "timeout"},
            real_platform_request_executed=True,
            raw_reference_safe_id=request_safe_id,
            error_message=str(exc),
            extra_metadata=metadata,
        )
    except Exception as exc:
        raw_message = str(exc)
        unavailable = "sso_session module unavailable" in raw_message or "SmartSSOSession unavailable" in raw_message
        status = "blocked" if unavailable else "auth_failed"
        return build_observation(
            source_status=status,
            user_id=user_id,
            evidence_time_range=evidence_time_range,
            evidence_summary="Unified login log request could not complete through controlled SSO executor.",
            source_quality={
                "permission_status": "blocked" if unavailable else "auth_failed",
                "failure_reason": "sso_executor_unavailable" if unavailable else "sso_request_failed",
                "no_data_not_risk_exclusion": True,
            },
            real_platform_request_executed=not unavailable,
            raw_reference_safe_id=request_safe_id,
            error_message=safe_error_message(exc),
            extra_metadata=metadata,
        )

    status_code = response_status(response)
    text = response_text(response)
    if status_code is not None and 300 <= int(status_code) < 400:
        return build_observation(
            source_status="auth_failed",
            user_id=user_id,
            evidence_time_range=evidence_time_range,
            evidence_summary="Unified login log request redirected, likely authentication or access proxy issue.",
            source_quality={"permission_status": "auth_failed", "failure_reason": "http_redirect"},
            real_platform_request_executed=True,
            raw_reference_safe_id=request_safe_id,
            extra_metadata=metadata,
        )
    if looks_like_auth_html(text):
        return build_observation(
            source_status="auth_failed",
            user_id=user_id,
            evidence_time_range=evidence_time_range,
            evidence_summary="Unified login log returned HTML/login-like content instead of JSON.",
            source_quality={"permission_status": "auth_failed", "failure_reason": "html_or_login_page"},
            real_platform_request_executed=True,
            raw_reference_safe_id=request_safe_id,
            extra_metadata=metadata,
        )

    try:
        payload = response_json(response)
    except Exception as exc:
        return build_observation(
            source_status="parse_error",
            user_id=user_id,
            evidence_time_range=evidence_time_range,
            evidence_summary="Unified login log response was not parseable as JSON.",
            source_quality={"permission_status": "unknown", "failure_reason": "json_parse_error"},
            real_platform_request_executed=True,
            raw_reference_safe_id=request_safe_id,
            error_message=str(exc),
            extra_metadata=metadata,
        )

    source_status, records_count, summary, quality = classify_json_payload(payload)
    return build_observation(
        source_status=source_status,
        user_id=user_id,
        evidence_time_range=evidence_time_range,
        evidence_summary=summary,
        source_quality=quality,
        real_platform_request_executed=True,
        records_count=records_count,
        raw_reference_safe_id=request_safe_id,
        extra_metadata=metadata,
    )


def main(argv: list[str] | None = None) -> int:
    try:
        args = parse_args(argv or sys.argv[1:])
        platform, action, user_id, from_ts, to_ts, timeout = normalize_args(args)
        if platform == "user_login_unified_log" and action == "query_user_login_log":
            observation = execute_login_log(user_id, from_ts, to_ts, timeout)
        else:
            raise ValueError("unsupported platform/action")
        emit_json(observation)
        return 0 if observation["source_status"] in {"completed", "no_data"} else 1
    except ValueError as exc:
        print(f"sso runner validation failed: {exc}", file=sys.stderr)
        emit_json(
            build_observation(
                source_status="blocked",
                user_id=None,
                evidence_time_range=None,
                evidence_summary=f"Validation failed: {sanitize_text(exc)}",
                source_quality={"permission_status": "not_started", "failure_reason": "validation_failed"},
                real_platform_request_executed=False,
                error_message=str(exc),
            )
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
