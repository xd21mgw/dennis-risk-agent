#!/usr/bin/env python3
"""Minimal readonly SSO session runner wrapper.

This wrapper currently performs local argument validation and whitelisted URL
construction only. It does not read auth state, call internal platforms, call
DataAgent, or execute writes.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from urllib.parse import urlencode


RELIABLE_WINDOW_DAYS = 7
RELIABLE_WINDOW_MS = RELIABLE_WINDOW_DAYS * 24 * 60 * 60 * 1000
ID_RE = re.compile(r"^[0-9]{1,20}$")
TS_RE = re.compile(r"^[0-9]{1,20}$")

PLATFORM_BASE = {
    "user_login_unified_log": "https://user-center-workbench.corp.kuaishou.com/rest/unified/log/search",
    "archives_center_profile": "https://admin.p.adm-corp.kuaishou.com/archives/user/home/info",
}


def die(message: str) -> None:
    print(
        json.dumps(
            {
                "ok": False,
                "error": message,
                "tool_call_allowed": False,
            },
            ensure_ascii=False,
            indent=2,
        ),
        file=sys.stderr,
    )
    raise SystemExit(2)


def validate_digits(value: str | None, field_name: str, pattern: re.Pattern[str]) -> str | None:
    if value is None:
        return None
    if not pattern.fullmatch(value):
        die(f"{field_name} must match {pattern.pattern}")
    return value


def build_user_login_url(user_id: str, from_ts: str | None, to_ts: str | None) -> tuple[str, dict[str, object]]:
    now_ms = int(time.time() * 1000)
    default_window_used = False

    if (from_ts is None) ^ (to_ts is None):
        die("from_timestamp and to_timestamp must be provided together")

    if from_ts is None and to_ts is None:
        to_ts_int = now_ms
        from_ts_int = now_ms - RELIABLE_WINDOW_MS
        default_window_used = True
    else:
        from_ts_int = int(from_ts or "0")
        to_ts_int = int(to_ts or "0")

    if from_ts_int > to_ts_int:
        die("from_timestamp must be <= to_timestamp")

    window_ms = to_ts_int - from_ts_int
    over_reliable_window = window_ms > RELIABLE_WINDOW_MS

    params = {
        "userId": user_id,
        "did": "",
        "query": "",
        "from_timestamp": str(from_ts_int),
        "to_timestamp": str(to_ts_int),
    }
    url = f"{PLATFORM_BASE['user_login_unified_log']}?{urlencode(params)}"
    metadata = {
        "reliable_window_days": RELIABLE_WINDOW_DAYS,
        "default_window_used": default_window_used,
        "over_reliable_window": over_reliable_window,
        "login_log_window_incomplete": over_reliable_window,
        "offline_hive_required": over_reliable_window,
        "no_data_interpretation": "current_window_no_data_only",
        "over_window_no_data_is_counter_evidence": False,
        "over_window_no_data_is_log_cleanup_evidence": False,
    }
    return url, metadata


def build_archives_profile_url(user_id: str) -> tuple[str, dict[str, object]]:
    params = {"userId": user_id}
    url = f"{PLATFORM_BASE['archives_center_profile']}?{urlencode(params)}"
    return url, {"timestamp_parameters_ignored": True}


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate and construct whitelisted readonly SSO session URLs."
    )
    parser.add_argument("--platform_key", required=True, choices=sorted(PLATFORM_BASE))
    parser.add_argument("--user_id", required=True)
    parser.add_argument("--from_timestamp")
    parser.add_argument("--to_timestamp")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])

    user_id = validate_digits(args.user_id, "user_id", ID_RE)
    from_ts = validate_digits(args.from_timestamp, "from_timestamp", TS_RE)
    to_ts = validate_digits(args.to_timestamp, "to_timestamp", TS_RE)

    if args.platform_key == "user_login_unified_log":
        url, metadata = build_user_login_url(user_id or "", from_ts, to_ts)
    else:
        url, metadata = build_archives_profile_url(user_id or "")

    output = {
        "ok": True,
        "dry_run_only": True,
        "platform_key": args.platform_key,
        "constructed_url": url,
        "metadata": metadata,
        "sensitive_auth_output": False,
        "dataagent_called": False,
        "platform_write_action": False,
        "real_platform_request_executed": False,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
