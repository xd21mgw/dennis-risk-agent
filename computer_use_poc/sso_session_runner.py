#!/usr/bin/env python3
"""Controlled readonly SSO HTTP executor.

This runner is intentionally narrow:

- only whitelisted platform/action pairs are accepted;
- no arbitrary URL input is accepted;
- stdout is exactly one machine-parseable JSON observation;
- diagnostics go to stderr;
- authentication material and request headers are never printed.

The live runtime is expected to provide ``sso_session.SmartSSOSession``. In
live environments the preferred dependency is
``ks_aimate.sso_login_client.SmartSSOSession``. If that executor is unavailable
or cannot authenticate, the only fallback is reading `.ks_sso/sso-state.json`
and applying kuaishou.com cookies to the runner-built whitelist URL.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
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
    "weapon": "weapon",
}

ACTION_ALIASES = {
    "query_user_login_log": "query_user_login_log",
    "graph_data": "graph_data",
    "risk_data": "risk_data",
}

PLATFORM_ACTIONS = {
    ("user_login_unified_log", "query_user_login_log"): {
        "source_name": "user_login_unified_log",
        "method": "GET",
        "base_url": "https://user-center-workbench.corp.kuaishou.com/rest/unified/log/search",
    },
    ("weapon", "graph_data"): {
        "source_name": "weapon_user_to_device_graph",
        "method": "GET",
        "base_url": "https://weapon.corp.kuaishou.com/apiv2/graphData",
    },
    ("weapon", "risk_data"): {
        "source_name": "weapon_device_risk",
        "method": "GET",
        "base_url": "https://weapon.corp.kuaishou.com/apiv2/riskData",
    },
}

SENSITIVE_KEY_RE = re.compile(
    r"(cookie|token|session|header|authorization|password|passwd|api[_-]?key)",
    re.IGNORECASE,
)
AUTH_CODE_RE = re.compile(r"(login|sso|auth|unauthorized|forbidden|redirect)", re.IGNORECASE)


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
    if (
        "ks_aimate SmartSSOSession unavailable" in text
        or "SmartSSOSession unavailable" in text
        or "cookie state unavailable" in text
    ):
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


DEVICE_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,128}$")


def build_weapon_graph_url(user_id: str) -> tuple[str, dict[str, Any]]:
    params = {
        "product": "KUAISHOU",
        "productName": "KUAISHOU",
        "groupValue": user_id,
        "groupKey": "USER_ID",
        "dimKey": "DEVICE_ID",
        "searchLevel": "2",
    }
    url = f"{PLATFORM_ACTIONS[('weapon', 'graph_data')]['base_url']}?{urlencode(params)}"
    return url, {
        "request_safe_id": safe_id(url),
        "endpoint_contract": "/apiv2/graphData",
        "forbidden_endpoint": "/api/graphData",
        "query_shape": {
            "product": "KUAISHOU",
            "productName": "KUAISHOU",
            "groupKey": "USER_ID",
            "dimKey": "DEVICE_ID",
            "searchLevel": 2,
        },
    }


def build_weapon_risk_url(device_id: str) -> tuple[str, dict[str, Any]]:
    if not DEVICE_ID_RE.fullmatch(device_id):
        raise ValueError("device_id must be an opaque device identifier")
    params = {
        "product": "KUAISHOU",
        "deviceIds": device_id,
    }
    url = f"{PLATFORM_ACTIONS[('weapon', 'risk_data')]['base_url']}?{urlencode(params)}"
    return url, {
        "request_safe_id": safe_id(url),
        "device_id_safe_id": safe_id(f"device_id:{device_id}"),
        "device_id_masked": mask_device_id(device_id),
        "endpoint_contract": "/apiv2/riskData",
        "device_id_prefix_preserved": device_id.startswith(("ANDROID_", "IOS_")),
        "query_shape": {
            "product": "KUAISHOU",
            "deviceIds": "redacted_device_id",
        },
    }


def mask_device_id(device_id: str) -> str:
    if "_" in device_id:
        prefix, rest = device_id.split("_", 1)
        return f"{prefix}_***{rest[-4:]}" if rest else f"{prefix}_***"
    return f"device_***{device_id[-4:]}"


def extract_graph_device_ids(payload: Any) -> list[str]:
    """Extract raw device ids from Weapon graphData payload for internal chaining.

    Device ids are expected under payload.data.pointInfoMap in the verified
    graphData response shape. Numeric-only nodes are user ids and must not be
    treated as device ids.
    """
    if not isinstance(payload, dict):
        return []
    data = payload.get("data")
    if not isinstance(data, dict):
        return []
    point_info_map = data.get("pointInfoMap")
    if not isinstance(point_info_map, dict):
        return []

    candidates: list[str] = []
    for key, value in point_info_map.items():
        if isinstance(key, str):
            candidates.append(key)
        if isinstance(value, dict):
            for field in ("id", "nodeId", "vertexId", "value", "deviceId", "device_id"):
                field_value = value.get(field)
                if isinstance(field_value, str):
                    candidates.append(field_value)

    device_ids: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        candidate = candidate.strip()
        if not candidate or ID_RE.fullmatch(candidate):
            continue
        if not DEVICE_ID_RE.fullmatch(candidate):
            continue
        if candidate not in seen:
            seen.add(candidate)
            device_ids.append(candidate)
    return device_ids


LABEL_KEYWORDS = {
    "machine_account": ("机器", "机注", "machine", "robot", "bot", "账号农场", "小号"),
    "no_sim": ("无sim", "无 sim", "nosim", "no_sim", "无卡", "SIM缺失"),
    "no_lock_screen": ("无锁屏", "未设置锁屏", "no_lock", "nolock", "lock_screen"),
    "factory_reset": ("恢复出厂", "factory", "reset", "刷机", "wipe"),
    "low_launch_count": ("启动次数低", "低启动", "low_launch", "launch_count"),
    "uid_cluster": ("uid聚集", "uid_cluster", "账号聚集", "多账号", "群控"),
}

HIGH_RISK_WORDS = ("高危", "高风险", "严重", "黑", "high", "critical", "strong", "level_3", "level3")
MEDIUM_RISK_WORDS = ("中危", "中风险", "可疑", "medium", "middle", "level_2", "level2")
WEAK_RISK_WORDS = ("低危", "低风险", "弱", "low", "weak", "level_1", "level1")


def iter_label_items(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        items: list[Any] = []
        for item in value:
            items.extend(iter_label_items(item))
        return items
    if isinstance(value, dict):
        if any(
            key in value
            for key in (
                "labelName",
                "label_name",
                "label",
                "name",
                "riskGroupName",
                "risk_group_name",
                "groupName",
                "group_name",
                "groupLevel",
                "level",
            )
        ):
            return [value]
        items = []
        for nested in value.values():
            items.extend(iter_label_items(nested))
        return items
    if isinstance(value, str) and value.strip():
        return [value]
    return []


def find_label_info(payload: Any) -> Any:
    if isinstance(payload, dict):
        for key in ("labelInfo", "label_info", "labels", "riskLabels", "risk_labels"):
            if key in payload:
                return payload.get(key)
        for nested in payload.values():
            found = find_label_info(nested)
            if found is not None:
                return found
    elif isinstance(payload, list):
        merged: list[Any] = []
        for item in payload:
            found = find_label_info(item)
            if found is not None:
                merged.append(found)
        if merged:
            return merged
    return None


def normalize_label_text(item: Any) -> str:
    if isinstance(item, str):
        return sanitize_text(item)
    if not isinstance(item, dict):
        return sanitize_text(item)
    parts: list[str] = []
    for key in (
        "labelName",
        "label_name",
        "label",
        "name",
        "desc",
        "description",
        "riskGroupName",
        "risk_group_name",
        "groupName",
        "group_name",
        "groupLevel",
        "level",
    ):
        value = item.get(key)
        if value not in (None, ""):
            parts.append(sanitize_text(value))
    return " / ".join(parts)[:160] if parts else sanitize_text(item)


def classify_label_strength(item: Any, text: str) -> str:
    haystack = text.lower()
    if isinstance(item, dict):
        for key in ("groupLevel", "level", "riskLevel", "risk_level", "score", "weight"):
            value = item.get(key)
            if isinstance(value, (int, float)):
                if value >= 3 or value >= 50:
                    return "high"
                if value >= 2 or value >= 20:
                    return "medium"
                if value > 0:
                    return "weak"
            if isinstance(value, str):
                haystack += f" {value.lower()}"
    if any(word.lower() in haystack for word in HIGH_RISK_WORDS):
        return "high"
    if any(word.lower() in haystack for word in MEDIUM_RISK_WORDS):
        return "medium"
    if any(word.lower() in haystack for word in WEAK_RISK_WORDS):
        return "weak"
    return "weak"


def summarize_risk_labels(payload: Any) -> dict[str, Any]:
    label_info = find_label_info(payload)
    items = iter_label_items(label_info)
    readable_labels: list[str] = []
    risk_group_names: list[str] = []
    group_levels: list[str] = []
    keyword_hits = {key: False for key in LABEL_KEYWORDS}
    counts = {"high": 0, "medium": 0, "weak": 0}
    seen_labels: set[str] = set()

    for item in items:
        text = normalize_label_text(item)
        if not text:
            continue
        if text not in seen_labels:
            seen_labels.add(text)
            readable_labels.append(text[:160])
        strength = classify_label_strength(item, text)
        counts[strength] += 1
        lowered = text.lower()
        for key, keywords in LABEL_KEYWORDS.items():
            if any(keyword.lower() in lowered for keyword in keywords):
                keyword_hits[key] = True
        if isinstance(item, dict):
            for key in ("riskGroupName", "risk_group_name", "groupName", "group_name"):
                value = item.get(key)
                if value not in (None, ""):
                    safe_value = sanitize_text(value)
                    if safe_value not in risk_group_names:
                        risk_group_names.append(safe_value)
            for key in ("groupLevel", "level", "riskLevel", "risk_level"):
                value = item.get(key)
                if value not in (None, ""):
                    safe_value = sanitize_text(value)
                    if safe_value not in group_levels:
                        group_levels.append(safe_value)

    label_count = len(readable_labels)
    summary: dict[str, Any] = {
        "empty": label_count == 0,
        "label_count": label_count,
        "high_risk_count": counts["high"],
        "medium_risk_count": counts["medium"],
        "weak_risk_count": counts["weak"],
        "readable_labels": readable_labels[:20],
        "risk_group_name": risk_group_names[:10],
        "groupLevel": group_levels[:10],
        "machine_account": keyword_hits["machine_account"],
        "no_sim": keyword_hits["no_sim"],
        "no_lock_screen": keyword_hits["no_lock_screen"],
        "factory_reset": keyword_hits["factory_reset"],
        "low_launch_count": keyword_hits["low_launch_count"],
        "uid_cluster": keyword_hits["uid_cluster"],
        "raw_labelInfo_output": False,
    }
    if label_count == 0:
        summary["no_risk_label_not_no_risk_proof"] = True
    return summary


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = EnvelopeArgumentParser(description="Controlled readonly SSO API executor.")
    parser.add_argument("--platform", choices=sorted(PLATFORM_ALIASES), help="Recommended runtime platform key.")
    parser.add_argument("--action", choices=sorted(ACTION_ALIASES), help="Recommended runtime action key.")
    parser.add_argument("--user-id", dest="user_id_dash")
    parser.add_argument("--device-id", dest="device_id_dash")
    parser.add_argument("--timeout", default="30")
    parser.add_argument("--format", default="json", choices=["json"])

    # Backward-compatible parameters.
    parser.add_argument("--platform_key", choices=sorted(PLATFORM_ALIASES))
    parser.add_argument("--user_id")
    parser.add_argument("--device_id")
    parser.add_argument("--from_timestamp")
    parser.add_argument("--to_timestamp")
    return parser.parse_args(argv)


def normalize_args(args: argparse.Namespace) -> tuple[str, str, str | None, str | None, str | None, str | None, int]:
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
    device_id = args.device_id_dash or args.device_id
    if platform == "user_login_unified_log" and user_id is None:
        raise ValueError("user_id is required")
    if platform == "weapon" and action == "graph_data" and user_id is None:
        raise ValueError("user_id is required")
    if platform == "weapon" and action == "risk_data":
        if not device_id:
            raise ValueError("device_id is required")
        if not DEVICE_ID_RE.fullmatch(device_id):
            raise ValueError("device_id must be an opaque device identifier")
    from_ts = validate_digits(args.from_timestamp, "from_timestamp", TS_RE)
    to_ts = validate_digits(args.to_timestamp, "to_timestamp", TS_RE)
    timeout = parse_timeout(args.timeout)
    return platform, action, user_id, device_id, from_ts, to_ts, timeout


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
    executor_mode: str = "unavailable",
    auth_refresh_attempted: bool = False,
    auth_refresh_status: str = "skipped",
    retry_after_refresh: bool = False,
    source_status_before_refresh: str | None = None,
    source_name: str = "user_login_unified_log",
    response_type: str | None = None,
    source_card: dict[str, Any] | None = None,
    source_checkpoint_private: dict[str, Any] | None = None,
) -> dict[str, Any]:
    source_quality = dict(source_quality)
    source_quality.setdefault("redaction_applied", True)
    source_quality.setdefault("raw_reference_retained_for_followup", False)
    source_quality.setdefault("sensitive_output", False)
    source_quality.setdefault("provenance", "current_task_observation")
    observation: dict[str, Any] = {
        "schema_version": "sso_runner_observation_v2",
        "source_name": source_name,
        "source_status": source_status,
        "user_id": user_id,
        "records_count": records_count if records_count is not None else 0,
        "evidence_time_range": evidence_time_range or {},
        "evidence_summary": evidence_summary,
        "source_quality": source_quality,
        "raw_references": [],
        "redaction": {
            "redaction_applied": True,
            "raw_reference_retained_for_followup": bool(source_quality.get("raw_reference_retained_for_followup")),
            "sensitive_output": False,
        },
        "provenance": {
            "executor_agent": "dennis-risk-agent",
            "source_observation_id": raw_reference_safe_id,
            "current_task_only": True,
        },
        "raw_reference_safe_id": raw_reference_safe_id,
        "collected_at": now_iso(),
        "redaction_applied": True,
        "real_platform_request_executed": real_platform_request_executed,
        "executor_mode": executor_mode,
        "auth_refresh_attempted": auth_refresh_attempted,
        "auth_refresh_status": auth_refresh_status,
        "retry_after_refresh": retry_after_refresh,
        "source_status_before_refresh": source_status_before_refresh,
        "dataagent_called": False,
        "platform_write_action": False,
        "sensitive_output": False,
        "response_type": response_type,
        "source_card": source_card or {},
        "source_checkpoint_private": source_checkpoint_private or {},
        "logs": [],
    }
    if error_message:
        observation["error"] = {"message": sanitize_text(error_message)}
    else:
        observation["error"] = None
    if extra_metadata:
        observation["metadata"] = extra_metadata
    raw_refs: list[dict[str, Any]] = []
    if user_id:
        raw_refs.append(
            {
                "ref_type": "user_id",
                "raw_reference_safe_id": safe_id(f"user_id:{user_id}"),
                "alias": "user_ref_1",
                "masked_value": f"user_***{user_id[-4:]}",
                "allowed_downstream_sources": ["login_log", "archives", "weapon_graphData", "dataagent_query_plan"],
                "retention_scope": "current_task_only",
            }
        )
    if source_card and source_card.get("device_id_safe_id"):
        raw_refs.append(
            {
                "ref_type": "device_id",
                "raw_reference_safe_id": source_card["device_id_safe_id"],
                "alias": "device_ref_1",
                "masked_value": source_card.get("device_id_masked", "device_masked"),
                "allowed_downstream_sources": ["weapon_riskData", "track_analysis_device_query", "device_sdk_query_plan"],
                "retention_scope": "current_task_only",
            }
        )
    if source_checkpoint_private and source_checkpoint_private.get("raw_device_ids_for_chaining"):
        for index, raw_device_id in enumerate(source_checkpoint_private["raw_device_ids_for_chaining"], start=1):
            if not isinstance(raw_device_id, str):
                continue
            raw_refs.append(
                {
                    "ref_type": "device_id",
                    "raw_reference_safe_id": safe_id(f"device_id:{raw_device_id}"),
                    "alias": f"device_ref_{index}",
                    "masked_value": mask_device_id(raw_device_id),
                    "allowed_downstream_sources": ["weapon_riskData", "track_analysis_device_query", "device_sdk_query_plan"],
                    "retention_scope": "current_task_only",
                }
            )
    if raw_refs:
        observation["raw_references"] = raw_refs
        observation["redaction"]["raw_reference_retained_for_followup"] = True
        observation["source_quality"]["raw_reference_retained_for_followup"] = True
    return observation


def load_smart_sso_session() -> Any:
    try:
        from ks_aimate.sso_login_client import SmartSSOSession  # type: ignore
    except ImportError as exc:
        raise RuntimeError("ks_aimate SmartSSOSession unavailable") from exc
    return SmartSSOSession()


def call_smart_sso_get(url: str, timeout: int) -> Any:
    session = load_smart_sso_session()
    get = getattr(session, "get", None)
    if get is None:
        raise RuntimeError("SmartSSOSession.get unavailable")
    try:
        return get(url, timeout=timeout)
    except TypeError:
        return get(url)


def load_kuaishou_cookies_from_state() -> list[dict[str, Any]]:
    state_path = Path(".ks_sso") / "sso-state.json"
    if not state_path.exists():
        raise RuntimeError("cookie state unavailable")
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RuntimeError("cookie state unavailable") from exc

    cookies_raw = state.get("cookies") if isinstance(state, dict) else None
    if not isinstance(cookies_raw, list):
        raise RuntimeError("cookie state unavailable")

    cookies: list[dict[str, Any]] = []
    for cookie in cookies_raw:
        if not isinstance(cookie, dict):
            continue
        domain = str(cookie.get("domain") or "")
        name = str(cookie.get("name") or "")
        value = str(cookie.get("value") or "")
        if not name or not value:
            continue
        if "kuaishou.com" not in domain:
            continue
        cookies.append({"name": name, "value": value, "domain": domain})
    if not cookies:
        raise RuntimeError("cookie state unavailable")
    return cookies


def call_cookie_state_get(url: str, timeout: int) -> Any:
    try:
        import requests  # type: ignore
    except ImportError as exc:
        raise RuntimeError("cookie state fallback unavailable") from exc

    cookies = load_kuaishou_cookies_from_state()
    session = requests.Session()
    for cookie in cookies:
        session.cookies.set(cookie["name"], cookie["value"], domain=cookie["domain"])
    return session.get(url, timeout=timeout, allow_redirects=False)


def call_executor_get(url: str, timeout: int) -> tuple[Any, str]:
    smart_error: Exception | None = None
    try:
        return call_smart_sso_get(url, timeout), "smart_sso"
    except Exception as exc:
        smart_error = exc

    try:
        return call_cookie_state_get(url, timeout), "cookie_state_fallback"
    except Exception as cookie_exc:
        raise RuntimeError(f"{safe_error_message(smart_error)}; {safe_error_message(cookie_exc)}") from cookie_exc


def sso_refresh_script_path() -> Path:
    return Path(__file__).resolve().parents[1] / "skills" / "kuaishou-sso-login-client" / "scripts" / "sso_session.py"


def refresh_sso_for_whitelist_url(url: str, timeout: int) -> tuple[bool, str]:
    script = sso_refresh_script_path()
    if not script.exists():
        return False, "sso_refresh_script_missing"

    uv = shutil.which("uv")
    if uv:
        cmd = [uv, "run", str(script), "--target_url", url]
    else:
        cmd = [sys.executable, str(script), "--target_url", url]

    try:
        proc = subprocess.run(
            cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=max(1, min(timeout, MAX_TIMEOUT_SECONDS)),
            check=False,
        )
    except subprocess.TimeoutExpired:
        return False, "sso_refresh_timeout"
    except Exception:
        return False, "sso_refresh_failed"

    if proc.returncode == 0:
        return True, "succeeded"
    return False, "sso_refresh_failed"


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
    if isinstance(payload, dict) and "code" in payload and str(payload.get("code")) not in {"0", "0.0"}:
        code_text = sanitize_text(payload.get("code"))
        message_text = sanitize_text(payload.get("message") or payload.get("msg") or "")
        permission_status = "auth_failed" if AUTH_CODE_RE.search(f"{code_text} {message_text}") else "blocked"
        summary = "Unified login log returned JSON but did not return code=0."
        quality = {
            "permission_status": permission_status,
            "reliability_level": "api_json_error_summary",
            "failure_reason": "api_code_not_ok",
            "api_code_safe": code_text,
            "raw_response_redacted": True,
        }
        return permission_status, 0, summary, quality

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


def classify_weapon_payload(
    payload: Any,
    source_name: str,
    *,
    device_id_safe_id: str | None = None,
    device_id_masked: str | None = None,
) -> tuple[str, int, str, dict[str, Any], dict[str, Any], dict[str, Any]]:
    records = extract_records(payload)
    records_count = len(records)
    if records_count == 0 and isinstance(payload, dict):
        for key in ("pointInfoMap", "relationEdgeList", "labelInfo", "data"):
            value = payload.get(key)
            if isinstance(value, dict):
                records_count += len(value)
            elif isinstance(value, list):
                records_count += len(value)

    source_card = {
        "source_name": source_name,
        "response_shape": "json_summary",
        "raw_response_redacted": True,
    }
    source_checkpoint_private: dict[str, Any] = {}
    if source_name == "weapon_user_to_device_graph":
        graph_device_ids = extract_graph_device_ids(payload)
        source_card["endpoint"] = "/apiv2/graphData"
        source_card["forbidden_endpoint"] = "/api/graphData"
        source_card["graph_empty_not_no_device"] = records_count == 0
        source_card["masked_device_ids"] = [mask_device_id(device_id) for device_id in graph_device_ids]
        source_card["raw_device_ids_for_chaining_count"] = len(graph_device_ids)
        source_card["device_id_redaction_policy"] = "raw_in_chaining_field_masked_in_display"
        source_checkpoint_private["raw_device_ids_for_chaining"] = graph_device_ids
        source_checkpoint_private["filtered_numeric_user_nodes"] = True
    else:
        source_card["endpoint"] = "/apiv2/riskData"
        source_card["device_risk_not_user_risk"] = True
        if device_id_safe_id:
            source_card["device_id_safe_id"] = device_id_safe_id
            source_card["device_id_masked"] = device_id_masked
        risk_label_summary = summarize_risk_labels(payload)
        source_card["risk_label_summary"] = risk_label_summary
        source_card["labelInfo_redaction_policy"] = "raw_labelInfo_used_for_summary_not_final_output"
        source_checkpoint_private["raw_labelInfo_retained_for_summary"] = True

    status = "completed" if records_count > 0 else "no_data"
    summary = (
        f"{source_name} returned {records_count} summarized item(s)."
        if records_count > 0
        else f"{source_name} returned JSON with no summarized item in this source."
    )
    quality = {
        "permission_status": "ok",
        "reliability_level": "api_json_summary",
        "no_data_not_risk_exclusion": status == "no_data",
        "raw_response_redacted": True,
        "redaction_applied": True,
        "sensitive_output": False,
    }
    if source_name == "weapon_device_risk":
        quality["raw_labelInfo_retained_for_summary"] = True
        risk_label_summary = source_card.get("risk_label_summary", {})
        if isinstance(risk_label_summary, dict) and risk_label_summary.get("empty"):
            quality["no_risk_label_not_no_risk_proof"] = True
    return status, records_count, summary, quality, source_card, source_checkpoint_private


def classify_response_to_observation(
    *,
    response: Any,
    user_id: str,
    evidence_time_range: dict[str, Any],
    request_safe_id: str,
    metadata: dict[str, Any],
    executor_mode: str,
    auth_refresh_attempted: bool,
    auth_refresh_status: str,
    retry_after_refresh: bool,
    source_status_before_refresh: str | None,
) -> dict[str, Any]:
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
            executor_mode=executor_mode,
            auth_refresh_attempted=auth_refresh_attempted,
            auth_refresh_status=auth_refresh_status,
            retry_after_refresh=retry_after_refresh,
            source_status_before_refresh=source_status_before_refresh,
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
            executor_mode=executor_mode,
            auth_refresh_attempted=auth_refresh_attempted,
            auth_refresh_status=auth_refresh_status,
            retry_after_refresh=retry_after_refresh,
            source_status_before_refresh=source_status_before_refresh,
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
            executor_mode=executor_mode,
            auth_refresh_attempted=auth_refresh_attempted,
            auth_refresh_status=auth_refresh_status,
            retry_after_refresh=retry_after_refresh,
            source_status_before_refresh=source_status_before_refresh,
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
        executor_mode=executor_mode,
        auth_refresh_attempted=auth_refresh_attempted,
        auth_refresh_status=auth_refresh_status,
        retry_after_refresh=retry_after_refresh,
        source_status_before_refresh=source_status_before_refresh,
    )


def execute_login_log(user_id: str, from_ts: str | None, to_ts: str | None, timeout: int) -> dict[str, Any]:
    url, metadata = build_user_login_url(user_id, from_ts, to_ts)
    evidence_time_range = metadata.pop("evidence_time_range")
    request_safe_id = metadata.pop("request_safe_id")

    try:
        response, executor_mode = call_executor_get(url, timeout)
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
            executor_mode="unavailable",
        )
    except Exception as exc:
        raw_message = str(exc)
        return build_observation(
            source_status="blocked",
            user_id=user_id,
            evidence_time_range=evidence_time_range,
            evidence_summary="Unified login log request could not complete through controlled SSO executor.",
            source_quality={
                "permission_status": "blocked",
                "failure_reason": "sso_executor_unavailable",
                "no_data_not_risk_exclusion": True,
            },
            real_platform_request_executed=False,
            raw_reference_safe_id=request_safe_id,
            error_message=safe_error_message(exc),
            extra_metadata=metadata,
            executor_mode="unavailable",
        )

    first_observation = classify_response_to_observation(
        response=response,
        user_id=user_id,
        evidence_time_range=evidence_time_range,
        request_safe_id=request_safe_id,
        metadata=metadata,
        executor_mode=executor_mode,
        auth_refresh_attempted=False,
        auth_refresh_status="skipped",
        retry_after_refresh=False,
        source_status_before_refresh=None,
    )

    if first_observation["source_status"] != "auth_failed":
        return first_observation

    refresh_ok, refresh_reason = refresh_sso_for_whitelist_url(url, timeout)
    if not refresh_ok:
        first_observation["auth_refresh_attempted"] = True
        first_observation["auth_refresh_status"] = "failed"
        first_observation["retry_after_refresh"] = False
        first_observation["source_status_before_refresh"] = "auth_failed"
        first_observation["source_quality"]["failure_reason"] = refresh_reason
        return first_observation

    try:
        retry_response, retry_executor_mode = call_executor_get(url, timeout)
    except Exception as exc:
        return build_observation(
            source_status="auth_failed",
            user_id=user_id,
            evidence_time_range=evidence_time_range,
            evidence_summary="Unified login log auth refresh succeeded but retry could not complete.",
            source_quality={
                "permission_status": "auth_failed",
                "failure_reason": safe_error_message(exc),
                "no_data_not_risk_exclusion": True,
            },
            real_platform_request_executed=True,
            raw_reference_safe_id=request_safe_id,
            error_message=safe_error_message(exc),
            extra_metadata=metadata,
            executor_mode="unavailable",
            auth_refresh_attempted=True,
            auth_refresh_status="succeeded",
            retry_after_refresh=True,
            source_status_before_refresh="auth_failed",
        )

    return classify_response_to_observation(
        response=retry_response,
        user_id=user_id,
        evidence_time_range=evidence_time_range,
        request_safe_id=request_safe_id,
        metadata=metadata,
        executor_mode=retry_executor_mode,
        auth_refresh_attempted=True,
        auth_refresh_status="succeeded",
        retry_after_refresh=True,
        source_status_before_refresh="auth_failed",
    )


def execute_weapon(
    *,
    action: str,
    user_id: str | None,
    device_id: str | None,
    timeout: int,
) -> dict[str, Any]:
    source_name = PLATFORM_ACTIONS[("weapon", action)]["source_name"]
    if action == "graph_data":
        if user_id is None:
            raise ValueError("user_id is required")
        url, metadata = build_weapon_graph_url(user_id)
        observation_user_id = user_id
    elif action == "risk_data":
        if device_id is None:
            raise ValueError("device_id is required")
        url, metadata = build_weapon_risk_url(device_id)
        observation_user_id = None
    else:
        raise ValueError("unsupported weapon action")

    request_safe_id = metadata.pop("request_safe_id")
    device_id_safe_id = metadata.pop("device_id_safe_id", None)
    device_id_masked = metadata.pop("device_id_masked", None)
    try:
        response, executor_mode = call_executor_get(url, timeout)
    except TimeoutError as exc:
        return build_observation(
            source_name=source_name,
            source_status="timeout",
            user_id=observation_user_id,
            evidence_time_range={},
            evidence_summary=f"{source_name} request timed out.",
            source_quality={"permission_status": "unknown", "failure_reason": "timeout"},
            real_platform_request_executed=True,
            raw_reference_safe_id=request_safe_id,
            error_message=str(exc),
            extra_metadata=metadata,
            executor_mode="unavailable",
        )
    except Exception as exc:
        return build_observation(
            source_name=source_name,
            source_status="blocked",
            user_id=observation_user_id,
            evidence_time_range={},
            evidence_summary=f"{source_name} request could not complete through controlled SSO executor.",
            source_quality={
                "permission_status": "blocked",
                "failure_reason": "sso_executor_unavailable",
                "no_data_not_risk_exclusion": True,
            },
            real_platform_request_executed=False,
            raw_reference_safe_id=request_safe_id,
            error_message=safe_error_message(exc),
            extra_metadata=metadata,
            executor_mode="unavailable",
        )

    status_code = response_status(response)
    text = response_text(response)
    if status_code is not None and 300 <= int(status_code) < 400:
        return build_observation(
            source_name=source_name,
            source_status="auth_failed",
            user_id=observation_user_id,
            evidence_time_range={},
            evidence_summary=f"{source_name} request redirected, likely authentication or access proxy issue.",
            source_quality={"permission_status": "auth_failed", "failure_reason": "http_redirect"},
            real_platform_request_executed=True,
            raw_reference_safe_id=request_safe_id,
            extra_metadata=metadata,
            executor_mode=executor_mode,
            response_type="redirect",
        )
    if looks_like_auth_html(text):
        return build_observation(
            source_name=source_name,
            source_status="auth_failed",
            user_id=observation_user_id,
            evidence_time_range={},
            evidence_summary=f"{source_name} returned HTML/login-like content instead of JSON.",
            source_quality={"permission_status": "auth_failed", "failure_reason": "html_or_login_page"},
            real_platform_request_executed=True,
            raw_reference_safe_id=request_safe_id,
            extra_metadata=metadata,
            executor_mode=executor_mode,
            response_type="html",
        )
    try:
        payload = response_json(response)
    except Exception as exc:
        return build_observation(
            source_name=source_name,
            source_status="parse_error",
            user_id=observation_user_id,
            evidence_time_range={},
            evidence_summary=f"{source_name} response was not parseable as JSON.",
            source_quality={"permission_status": "unknown", "failure_reason": "json_parse_error"},
            real_platform_request_executed=True,
            raw_reference_safe_id=request_safe_id,
            error_message=str(exc),
            extra_metadata=metadata,
            executor_mode=executor_mode,
            response_type="parse_error",
        )

    source_status, records_count, summary, quality, source_card, source_checkpoint_private = classify_weapon_payload(
        payload,
        source_name,
        device_id_safe_id=device_id_safe_id,
        device_id_masked=device_id_masked,
    )
    return build_observation(
        source_name=source_name,
        source_status=source_status,
        user_id=observation_user_id,
        evidence_time_range={},
        evidence_summary=summary,
        source_quality=quality,
        real_platform_request_executed=True,
        records_count=records_count,
        raw_reference_safe_id=request_safe_id,
        extra_metadata=metadata,
        executor_mode=executor_mode,
        response_type="json",
        source_card=source_card,
        source_checkpoint_private=source_checkpoint_private,
    )


def main(argv: list[str] | None = None) -> int:
    try:
        args = parse_args(argv or sys.argv[1:])
        platform, action, user_id, device_id, from_ts, to_ts, timeout = normalize_args(args)
        if platform == "user_login_unified_log" and action == "query_user_login_log":
            if user_id is None:
                raise ValueError("user_id is required")
            observation = execute_login_log(user_id, from_ts, to_ts, timeout)
        elif platform == "weapon":
            observation = execute_weapon(action=action, user_id=user_id, device_id=device_id, timeout=timeout)
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
