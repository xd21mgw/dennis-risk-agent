#!/usr/bin/env python3
"""Dennis-owned safe observation builder for pure passthrough envelopes.

The browser-backed service must stay a transport passthrough. This module is
runtime-local Dennis logic: it may inspect capped/raw body fields in memory,
extract only allowlisted risk handles, and return safe observations without
returning or persisting raw upstream bodies.
"""

from __future__ import annotations

import json
import re
from typing import Any


SECRET_KEY_FRAGMENTS = (
    "cookie",
    "token",
    "session",
    "header",
    "authorization",
    "password",
    "secret",
    "credential",
)

STRICT_PII_KEY_FRAGMENTS = (
    "phone",
    "mobile",
    "idcard",
    "identity",
    "realname",
    "name",
    "address",
)

BODY_CANDIDATE_KEYS = {
    "body",
    "raw_body",
    "response_body",
    "upstream_body",
    "raw_payload",
    "capped_body",
    "body_excerpt",
    "body_snippet",
    "body_preview",
    "capped_body_snippet",
    "response_text",
    "payload",
    "data",
}

SOURCE_EXPECTED_BUSINESS_FIELDS = {
    "login_logs_search": [
        "login_time",
        "login_type",
        "login_source",
        "device_id",
        "ip_ua",
        "success_failure",
        "kickout",
        "token_oauth_scan",
        "window_coverage",
    ],
    "archives_photo_search": [
        "photo_id",
        "publish_time",
        "publish_source",
        "publish_device",
        "publish_ip_ua",
        "content_status",
        "audit_or_strategy_reason",
    ],
    "archives_user_analysis": [
        "operation_time",
        "operation_type",
        "security_action_type",
        "profile_change_type",
        "publish_related_action",
        "operation_device",
        "operation_ip_ua",
    ],
    "archives_user_profile": [
        "account_status",
        "profile_status",
        "punish_or_tag_summary",
        "risk_label",
        "baseline_summary",
        "candidate_device_id",
    ],
    "archives_related_users": [
        "related_user_id",
        "relation_type",
        "shared_device",
        "shared_login_or_register",
        "related_count",
    ],
    "weapon_inventory": [
        "user_device_edge",
        "device_id",
        "risk_label",
        "graph_relation_count",
        "riskdata_status",
    ],
}

BUSINESS_FIELD_ALIASES = {
    "user_id": {"user_id", "userId", "userID", "uid"},
    "device_id": {"device_id", "deviceId", "deviceid", "did", "loginDeviceId", "login_did"},
    "candidate_device_id": {"candidate_device_id", "candidateDeviceId", "device_id", "deviceId", "did"},
    "photo_id": {"photo_id", "photoId", "photoID", "content_id", "contentId"},
    "event_id": {"event_id", "eventId", "sourceId", "source_id"},
    "policy_code": {"policy_code", "policyCode", "hitFusePolicyCode", "policyTreeCode"},
    "login_time": {"login_time", "loginTime", "loginTimestamp", "timestamp", "event_time", "time"},
    "login_type": {"login_type", "loginType", "reset_login_type", "resetLoginType", "authType"},
    "login_source": {"login_source", "loginSource", "login_channel", "clientType", "platform", "loginPlatform", "logSource"},
    "login_device": {"login_device", "loginDevice", "loginDeviceId", "device_id", "deviceId", "did"},
    "ip_ua": {"ip", "loginIp", "clientIp", "requestIp", "ua", "UA", "userAgent", "user_agent", "browserUa"},
    "publish_time": {"publish_time", "publishTime", "createTime", "uploadTime"},
    "publish_source": {"publish_source", "publishSource", "publish_channel", "source", "clientType", "publishPlatform"},
    "publish_device": {"publish_device", "publishDevice", "publishDeviceId", "publish_did", "device_id", "deviceId", "did"},
    "publish_ip_ua": {"publish_ip", "publishIp", "ip", "clientIp", "publishUA", "publishUa", "ua", "userAgent"},
    "operation_time": {"operation_time", "operationTime", "time", "createTime", "eventTime"},
    "operation_type": {"operation_type", "operationType", "actionType", "opType", "eventType"},
    "operation_device": {"operation_device", "operationDevice", "operationDeviceId", "device_id", "deviceId", "did"},
    "operation_ip_ua": {"operation_ip", "operationIp", "ip", "clientIp", "ua", "userAgent"},
    "security_action_type": {
        "security_action_type",
        "resetPwd",
        "password_reset",
        "bind_change",
        "protect_account",
        "kickout",
        "freeze",
    },
    "profile_change_type": {"profile_change_type", "profileChange", "modifyProfile"},
    "publish_related_action": {"publish_related_action", "publish", "photoPublish", "postVideo"},
    "account_status": {"account_status", "accountStatus", "status", "accountState"},
    "profile_status": {"profile_status", "profileStatus", "profile"},
    "punish_or_tag_summary": {"punishment", "punish", "label", "riskLabel", "tag", "penalty"},
    "risk_label": {"risk_label", "riskLabel", "label", "tag"},
    "baseline_summary": {"baseline", "profileBaseline", "profile_baseline"},
    "related_user_id": {"related_user_id", "relatedUserId", "user_id", "userId"},
    "relation_type": {"relation_type", "relationType", "relation"},
    "shared_device": {"shared_device", "sharedDevice", "device_id", "deviceId", "did"},
    "shared_login_or_register": {"shared_login", "sharedRegister", "registerDevice", "loginDevice"},
    "related_count": {"related_count", "relatedCount", "totalCount", "count"},
    "success_failure": {"success", "failure", "loginResult", "finalloginresult", "status"},
    "kickout": {"kickout", "kick_out", "kickedOut", "protectKickout"},
    "token_oauth_scan": {"oauth", "OAuth", "scan", "scanLogin", "refreshToken", "byToken", "logined", "passToken"},
    "window_coverage": {"request_window_start", "request_window_end", "from_timestamp", "to_timestamp"},
    "content_status": {"content_status", "photoStatus", "auditStatus", "status"},
    "audit_or_strategy_reason": {"audit_reason", "strategyReason", "hitReason", "reason"},
    "user_device_edge": {"user_device_edge", "edge", "pointInfoMap", "deviceId", "did"},
    "graph_relation_count": {"graph_relation_count", "relationCount", "edgeCount", "count"},
    "riskdata_status": {"riskdata_status", "riskData", "riskStatus"},
}

DEVICE_CANONICAL_FIELDS = {
    "device_id",
    "candidate_device_id",
    "login_device",
    "publish_device",
    "operation_device",
    "shared_device",
    "user_device_edge",
}

SENSITIVE_VALUE_PATTERNS = (
    re.compile(r"1[3-9]\d{9}"),
    re.compile(r"\b\d{17}[\dXx]\b"),
)


def _unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def _key_has_fragment(key: str, fragments: tuple[str, ...]) -> bool:
    lowered = key.lower()
    return any(fragment in lowered for fragment in fragments)


def _looks_sensitive_scalar(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    return any(pattern.search(value) for pattern in SENSITIVE_VALUE_PATTERNS)


def _parse_body_value(value: Any) -> tuple[Any, str]:
    if isinstance(value, (dict, list)):
        return value, "structured"
    if not isinstance(value, str):
        return None, "unsupported"
    text = value.strip()
    if not text:
        return None, "empty"
    if len(text) > 200_000:
        text = text[:200_000]
    if text[0] in "[{":
        try:
            return json.loads(text), "json"
        except json.JSONDecodeError:
            return None, "json_parse_error"
    return None, "non_json_text"


def _collect_body_candidates(value: Any, *, path: str = "$", limit: int = 12) -> list[tuple[str, Any]]:
    candidates: list[tuple[str, Any]] = []
    if len(candidates) >= limit:
        return candidates
    if isinstance(value, dict):
        for key, item in value.items():
            child_path = f"{path}.{key}"
            lowered = key.lower()
            if _key_has_fragment(key, SECRET_KEY_FRAGMENTS):
                continue
            if lowered in BODY_CANDIDATE_KEYS:
                candidates.append((child_path, item))
                if len(candidates) >= limit:
                    return candidates
            if isinstance(item, (dict, list)):
                candidates.extend(_collect_body_candidates(item, path=child_path, limit=limit - len(candidates)))
                if len(candidates) >= limit:
                    return candidates
    elif isinstance(value, list):
        for index, item in enumerate(value):
            candidates.extend(_collect_body_candidates(item, path=f"{path}[{index}]", limit=limit - len(candidates)))
            if len(candidates) >= limit:
                return candidates
    return candidates[:limit]


def _canonical_for_key(key: str) -> str | None:
    normalized = re.sub(r"[^a-z0-9]", "", key.lower())
    for canonical, aliases in BUSINESS_FIELD_ALIASES.items():
        if any(re.sub(r"[^a-z0-9]", "", alias.lower()) == normalized for alias in aliases):
            return canonical
    return None


def _extract_handles(
    value: Any,
    *,
    source_id: str,
    path: str = "$",
    limit: int = 160,
) -> tuple[list[dict[str, Any]], list[str]]:
    handles: list[dict[str, Any]] = []
    flags: list[str] = []

    def walk(item: Any, current_path: str) -> None:
        if len(handles) >= limit:
            return
        if isinstance(item, dict):
            for key, child in item.items():
                child_path = f"{current_path}.{key}"
                canonical = _canonical_for_key(key)
                if key.lower() in BODY_CANDIDATE_KEYS:
                    continue
                if _key_has_fragment(key, SECRET_KEY_FRAGMENTS):
                    flags.append("blocked_sensitive_material_detected")
                    if canonical == "token_oauth_scan":
                        handles.append(
                            {
                                "field": key,
                                "canonical_field": canonical,
                                "field_path": child_path,
                                "source_id": source_id,
                                "value": "present_redacted",
                            }
                        )
                    continue
                if _key_has_fragment(key, STRICT_PII_KEY_FRAGMENTS):
                    flags.append("pii_strict_redacted")
                    continue
                if canonical and isinstance(child, (str, int, float, bool)):
                    if _looks_sensitive_scalar(child):
                        flags.append("pii_strict_redacted")
                        continue
                    handles.append(
                        {
                            "field": key,
                            "canonical_field": canonical,
                            "field_path": child_path,
                            "source_id": source_id,
                            "value": child,
                        }
                    )
                    if len(handles) >= limit:
                        return
                if isinstance(child, (dict, list)):
                    walk(child, child_path)
        elif isinstance(item, list):
            for index, child in enumerate(item[:200]):
                walk(child, f"{current_path}[{index}]")
                if len(handles) >= limit:
                    return

    walk(value, path)
    return handles, _unique(flags)


def _expected_fields_for_action(action: str, expected_business_fields: list[str] | None) -> list[str]:
    if expected_business_fields:
        return list(expected_business_fields)
    return list(SOURCE_EXPECTED_BUSINESS_FIELDS.get(action, []))


def build_safe_observation(
    *,
    source_id: str,
    action: str,
    source_payload: dict[str, Any],
    transport_row: dict[str, Any],
    expected_business_fields: list[str] | None = None,
    chain_section: str = "source_quality",
    role: str = "",
) -> dict[str, Any]:
    expected = _expected_fields_for_action(action, expected_business_fields)
    body_candidates = _collect_body_candidates(source_payload)
    body_parse_statuses: list[str] = []
    parsed_values: list[tuple[str, Any]] = []
    flags: list[str] = []

    for body_path, body_value in body_candidates:
        parsed, parse_status = _parse_body_value(body_value)
        body_parse_statuses.append(f"{body_path}:{parse_status}")
        if parsed is None:
            if parse_status.endswith("parse_error"):
                flags.append("passthrough_interpretation_gap")
            continue
        parsed_values.append((body_path, parsed))

    direct_handles, direct_flags = _extract_handles(source_payload, source_id=source_id, path="$passthrough")
    flags.extend(direct_flags)
    body_handles: list[dict[str, Any]] = []
    for body_path, parsed in parsed_values:
        handles, body_flags = _extract_handles(parsed, source_id=source_id, path=body_path)
        body_handles.extend(handles)
        flags.extend(body_flags)

    parsed_body_handles = _dedupe_handles(body_handles)
    all_handles = _dedupe_handles(direct_handles + parsed_body_handles)
    extracted_business_fields = _unique(
        [
            str(handle["canonical_field"])
            for handle in parsed_body_handles
            if str(handle.get("canonical_field")) in expected or not expected
        ]
    )
    missing_business_fields = [field for field in expected if field not in extracted_business_fields]

    if body_candidates:
        flags.append("safe_raw_or_capped_body_parser_attempted")
    if parsed_values:
        flags.append("safe_body_parsed")
    elif (transport_row.get("body_present") is True or int(transport_row.get("observed_bytes") or 0) > 0):
        flags.append("service_body_visibility_gap")
    if body_candidates and not parsed_values:
        flags.append("passthrough_interpretation_gap")
    if missing_business_fields and str(transport_row.get("quality_class") or "") in {"completed", "partial"}:
        flags.extend(["observation_compression_gap", "business_fields_not_extracted"])

    source_specific_flags = _source_specific_flags(action, missing_business_fields, extracted_business_fields, transport_row)
    flags.extend(source_specific_flags)

    candidate_device_ids = [
        {
            "device_id": str(handle["value"]),
            "source_id": source_id,
            "field_path": str(handle["field_path"]),
            "canonical_field": str(handle["canonical_field"]),
        }
        for handle in all_handles
        if str(handle.get("canonical_field")) in DEVICE_CANONICAL_FIELDS and str(handle.get("value") or "").strip()
    ]

    return {
        "dennis_observation_version": "safe_passthrough_observation_v1",
        "source_id": source_id,
        "action": action,
        "chain_section": chain_section,
        "role": role,
        "safe_parse_body": True,
        "raw_body_returned": False,
        "visible_body_keys": [path for path, _value in body_candidates],
        "parser_input_available": bool(parsed_values),
        "body_parse_statuses": body_parse_statuses,
        "direct_safe_handles": direct_handles,
        "parsed_body_safe_handles": parsed_body_handles,
        "extracted_safe_handles": all_handles,
        "extracted_business_fields": extracted_business_fields,
        "missing_business_fields": missing_business_fields,
        "candidate_device_ids": _dedupe_device_candidates(candidate_device_ids),
        "interpretation_flags": _unique(flags),
        "source_quality_hint": _source_quality_hint(flags, missing_business_fields),
        "evidence_chain_tags": _evidence_chain_tags(action, extracted_business_fields),
    }


def _source_specific_flags(
    action: str,
    missing_business_fields: list[str],
    extracted_business_fields: list[str],
    transport_row: dict[str, Any],
) -> list[str]:
    flags: list[str] = []
    if action == "login_logs_search":
        if transport_row.get("body_truncated") is True:
            flags.extend(["partial_observation_available", "response_too_large_window_shrink_recommended"])
        if {"login_time", "login_type", "login_source", "device_id", "ip_ua"} & set(missing_business_fields):
            flags.append("login_chain_business_fields_missing")
    elif action == "archives_photo_search":
        if {"photo_id", "publish_time", "publish_source", "publish_device"} & set(missing_business_fields):
            flags.append("content_chain_business_fields_missing")
        if "publish_device" in extracted_business_fields:
            flags.append("publish_device_candidate_device_source")
    elif action == "archives_user_analysis":
        if {"operation_time", "operation_type", "security_action_type", "operation_device"} & set(missing_business_fields):
            flags.append("behavior_chain_business_fields_missing")
        if "operation_device" in extracted_business_fields:
            flags.append("operation_device_candidate_device_source")
    elif action == "archives_related_users":
        flags.append("archives_related_users_spread_clue_not_gang")
    elif action == "weapon_inventory":
        flags.append("weapon_device_graph_not_ato_conclusion")
    return flags


def _source_quality_hint(flags: list[str], missing_business_fields: list[str]) -> str:
    if "blocked_sensitive_material_detected" in flags:
        return "blocked_sensitive_material_detected"
    if "passthrough_interpretation_gap" in flags:
        return "passthrough_interpretation_gap"
    if missing_business_fields:
        return "business_fields_not_extracted"
    return "business_fields_extracted"


def _evidence_chain_tags(action: str, extracted_business_fields: list[str]) -> list[str]:
    fields = set(extracted_business_fields)
    tags: list[str] = []
    if action == "archives_photo_search" and {"publish_time", "publish_source", "publish_device", "photo_id"} & fields:
        tags.append("web_or_abnormal_publish_fact")
    if action == "login_logs_search" and {"login_time", "login_source", "login_type", "device_id"} & fields:
        tags.append("web_history_baseline")
        tags.append("control_entry")
    if fields & {"device_id", "login_device", "publish_device", "operation_device", "shared_device"}:
        tags.append("device_identity_alignment")
    if action == "archives_user_analysis" and {"security_action_type", "operation_type", "publish_related_action"} & fields:
        tags.append("post_action_or_security_timeline")
    return _unique(tags)


def _dedupe_handles(handles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for handle in handles:
        key = (
            str(handle.get("canonical_field")),
            str(handle.get("field_path")),
            str(handle.get("value")),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(handle)
    return deduped[:160]


def _dedupe_device_candidates(candidates: list[dict[str, str]]) -> list[dict[str, str]]:
    deduped: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for candidate in candidates:
        key = (candidate["device_id"], candidate["field_path"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(candidate)
    return deduped[:30]
