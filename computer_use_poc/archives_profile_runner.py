#!/usr/bin/env python3
"""Controlled Archives Center profile runner stub.

This is a minimal contract runner. It does not access real platforms and does
not perform auth repair. It validates input and returns a structured source gap
so Dennis can keep Archives Center as a P0 source without pretending that the
runner is connected.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Any


USER_ID_RE = re.compile(r"^[0-9]{1,20}$")
MAX_TIMEOUT_SECONDS = 60


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_id(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def emit(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Controlled Archives profile readonly runner stub.")
    parser.add_argument("--action", default="archives.profile_home_info")
    parser.add_argument("--user-id", required=True)
    parser.add_argument("--timeout", default="30")
    parser.add_argument("--format", default="json", choices=["json"])
    return parser.parse_args()


def parse_timeout(value: str) -> int:
    if not re.fullmatch(r"^[0-9]{1,2}$", value):
        raise ValueError("timeout must be an integer second value")
    timeout = int(value)
    if timeout <= 0 or timeout > MAX_TIMEOUT_SECONDS:
        raise ValueError(f"timeout must be between 1 and {MAX_TIMEOUT_SECONDS}")
    return timeout


def blocked_observation(reason: str, user_id: str | None = None) -> dict[str, Any]:
    return {
        "archives_profile_source_status": "blocked",
        "same_origin_fetch_ready": False,
        "available_fields": [],
        "account_status_summary": None,
        "ban_info_summary": None,
        "demote_info_summary": None,
        "login_device_summary": None,
        "register_device_summary": None,
        "missing_fields": [
            "user_profile_summary",
            "account_status",
            "ban_info",
            "demote_info",
            "login_device_summary",
            "register_device_summary",
        ],
        "source_card": {
            "source_name": "archives_profile_readonly",
            "source_status": "blocked",
            "evidence_summary": reason,
            "records_count": 0,
        },
        "source_quality": {
            "permission_status": "not_started",
            "auth_status": "not_checked",
            "response_type": "not_executed",
            "reliability_level": "none",
            "failure_reason": reason,
            "no_data_not_risk_exclusion": True,
            "not_executed_as_low_risk_evidence": True,
        },
        "source_checkpoint_private": {
            "raw_references": [
                {
                    "ref_type": "user_id",
                    "raw_reference_safe_id": safe_id(user_id or "missing_user_id"),
                    "alias": "target_user",
                    "allowed_downstream_sources": ["archives_profile_readonly"],
                    "retention_scope": "current_task_only",
                }
            ] if user_id else [],
            "downstream_source_chaining": [],
        },
        "redaction": {
            "redaction_applied": True,
            "sensitive_output": False,
            "raw_reference_retained_for_followup": bool(user_id),
        },
        "real_platform_request_executed": False,
        "runner_readiness_status": "planned_or_minimal_stub",
        "collected_at": now_iso(),
    }


def main() -> int:
    try:
        args = parse_args()
        timeout = parse_timeout(args.timeout)
        if args.action != "archives.profile_home_info":
            emit(blocked_observation("unsupported_action"))
            return 2
        if not USER_ID_RE.fullmatch(args.user_id):
            emit(blocked_observation("invalid_user_id"))
            return 2

        observation = blocked_observation(
            "archives_profile_runner_stub_not_connected; requires future same-origin/auth-ready implementation",
            user_id=args.user_id,
        )
        observation["timeout_seconds"] = timeout
        observation["source_quality"]["permission_status"] = "source_gap"
        observation["source_quality"]["auth_status"] = "not_connected"
        observation["source_quality"]["failure_reason"] = "archives_runner_not_connected"
        observation["remaining_gap"] = "connect archives_auth_state / same_origin_fetch implementation before live source execution"
        emit(observation)
        return 0
    except Exception as exc:  # fail closed with no sensitive data
        emit(blocked_observation(f"runner_error:{type(exc).__name__}"))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
