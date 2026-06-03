#!/usr/bin/env python3
"""Dennis-owned safe observation builder for pure passthrough envelopes.

The browser-backed service must stay a transport passthrough. This module is
runtime-local Dennis logic: it may inspect capped/raw body fields in memory,
extract only allowlisted risk handles, and return safe observations without
returning or persisting raw upstream bodies.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any


CREDENTIAL_SECRET_KEYS = {
    "token", "accesstoken", "refreshtoken", "logintoken", "authtoken", "passtoken",
    "session", "sessionid", "cookie", "cookies", "authorization", "authheader",
    "rawauthheader", "password", "passwd", "secret", "credential", "ticket",
}

RISK_ENTITY_TOKEN_KEYS = {
    "tokenid", "tokenstatus", "tokentype", "tokensource", "tokentime",
    "tokencreatetime", "tokengeneratetime", "tokenexpiretime",
}

STRICT_PII_KEYS = {
    "phone", "phonenumber", "mobile", "mobilenumber", "idcard", "identity",
    "identitynumber", "realname", "name", "address", "detailaddress",
    "detailedaddress",
}

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
    "archives_photo_profile": [
        "photo_id",
        "publish_time",
        "publish_source",
        "publish_device",
        "publish_ip_ua",
        "content_status",
        "audit_or_strategy_reason",
    ],
    "archives_photo_meta": [
        "photo_id",
        "publish_time",
        "publish_source",
        "publish_device",
        "publish_ip_ua",
        "content_status",
        "audit_or_strategy_reason",
    ],
    "archives_photo_report_aggregate": [
        "photo_id",
        "audit_or_strategy_reason",
        "content_status",
    ],
    "archives_photo_user_autonomy": [
        "photo_id",
        "operation_time",
        "operation_type",
        "content_status",
    ],
    "archives_gallery_photo_list": [
        "photo_id",
        "publish_time",
        "publish_source",
        "publish_device",
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
    "token_event_id": {"tokenId", "token_id"},
    "login_time": {"login_time", "loginTime", "loginTimestamp", "timestamp", "event_time", "time"},
    "login_type": {"login_type", "loginType", "reset_login_type", "resetLoginType", "authType"},
    "login_source": {"login_source", "loginSource", "login_channel", "clientType", "platform", "loginPlatform", "logSource"},
    "login_device": {"login_device", "loginDevice", "loginDeviceId", "device_id", "deviceId", "did"},
    "ip_ua": {"ip", "loginIp", "clientIp", "requestIp", "ua", "UA", "userAgent", "user_agent", "browserUa"},
    "publish_time": {"publish_time", "publishTime", "createTime", "uploadTime", "upload_time", "create_time"},
    "publish_source": {
        "publish_source",
        "publishSource",
        "publish_channel",
        "source",
        "clientType",
        "publishPlatform",
        "uploadSource",
        "photoMethod",
        "videoType",
        "operationSource",
        "client",
        "app",
        "platform",
    },
    "publish_device": {
        "publish_device",
        "publishDevice",
        "publishDeviceId",
        "publish_did",
        "uploadDevice",
        "uploadDeviceId",
        "device_id",
        "deviceId",
        "did",
    },
    "publish_ip_ua": {"publish_ip", "publishIp", "photoIp", "ip", "clientIp", "publishUA", "publishUa", "ua", "userAgent"},
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
    "endpoint_path": {"method", "path", "endpoint", "apiPath", "requestPath", "urlPath"},
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

RISK_ENTITY_CANONICAL_FIELDS = {
    "user_id",
    "device_id",
    "candidate_device_id",
    "login_device",
    "publish_device",
    "operation_device",
    "shared_device",
    "photo_id",
    "event_id",
    "policy_code",
    "token_event_id",
    "ip_ua",
    "publish_ip_ua",
    "operation_ip_ua",
    "endpoint_path",
}

SENSITIVE_VALUE_PATTERNS = (
    re.compile(r"1[3-9]\d{9}"),
    re.compile(r"\b\d{17}[\dXx]\b"),
)

LOGIN_LOGS_ARRAY_CAP_PATH = ("data", "logSearchModels")
ROW_CAP_METADATA_KEYS = (
    "capped_json_path",
    "observed_records",
    "returned_records",
    "missing_records",
    "missing_body_reason",
    "cap_reason",
)

PROJECTION_DROP_KEY_FRAGMENTS = {
    "uiconfig",
    "menulist",
    "theme",
    "stylesheet",
    "styleconfig",
    "debugblob",
    "debugmetadata",
    "stacktrace",
    "html",
    "dom",
    "rawhtml",
    "traceidlist",
    "frontendconfig",
}

PROJECTION_LARGE_LOW_VALUE_KEYS = {
    "extra",
    "ext",
    "context",
    "rawrequest",
    "rawresponse",
    "requestbody",
    "responsebody",
    "labelinfo",
    "debug",
}

PROJECTION_ALWAYS_KEEP_KEYS = {
    "id",
    "method",
    "path",
    "endpoint",
    "operation",
    "operationType",
    "status",
    "result",
    "reason",
    "errorReason",
    "logContent",
    "parsedLogContent",
    "parsedLogContentParams",
    "params",
    "code",
    "data",
    "logSearchModels",
    "items",
}

MAX_PROJECTED_STRING_VALUE_LENGTH = 512
MAX_PROJECTED_ARRAY_ITEMS = 200
MAX_RETAINED_FIELD_PATHS = 120


def _unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def _normalized_key(key: str) -> str:
    return re.sub(r"[^a-z0-9]", "", key.lower())


def _is_credential_secret_key(key: str) -> bool:
    normalized = _normalized_key(key)
    if normalized in RISK_ENTITY_TOKEN_KEYS:
        return False
    if normalized in CREDENTIAL_SECRET_KEYS:
        return True
    if any(fragment in normalized for fragment in ("cookie", "authorization", "password", "secret", "credential")):
        return True
    if "header" in normalized:
        return True
    if normalized.endswith("token") or "accesstoken" in normalized or "refreshtoken" in normalized:
        return True
    if normalized.startswith("session") or normalized.endswith("session"):
        return True
    return False


def _is_strict_pii_key(key: str) -> bool:
    normalized = _normalized_key(key)
    if normalized in STRICT_PII_KEYS:
        return True
    return any(fragment in normalized for fragment in ("idcard", "identitynumber", "realname", "detailaddress", "detailedaddress"))


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



def _safe_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value >= 0 else None
    if isinstance(value, float) and value.is_integer() and value >= 0:
        return int(value)
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return None


def _nested_dicts(value: dict[str, Any]) -> list[dict[str, Any]]:
    candidates = [value]
    upstream = value.get("upstream")
    if isinstance(upstream, dict):
        candidates.append(upstream)
    source_result = value.get("source_result")
    if isinstance(source_result, dict):
        candidates.append(source_result)
        nested_upstream = source_result.get("upstream")
        if isinstance(nested_upstream, dict):
            candidates.append(nested_upstream)
        transport = source_result.get("transport")
        if isinstance(transport, dict):
            candidates.append(transport)
    transport = value.get("transport")
    if isinstance(transport, dict):
        candidates.append(transport)
    return candidates


def _row_cap_metadata(source_payload: dict[str, Any], transport_row: dict[str, Any]) -> dict[str, Any]:
    for candidate in [transport_row, *_nested_dicts(source_payload)]:
        if not isinstance(candidate, dict):
            continue
        raw_handling = str(candidate.get("raw_body_handling") or "")
        path = candidate.get("capped_json_path")
        observed = _safe_int(candidate.get("observed_records"))
        returned = _safe_int(candidate.get("returned_records"))
        missing = _safe_int(candidate.get("missing_records"))
        if raw_handling != "json_array_capped" and not path:
            continue
        metadata = {
            "raw_body_handling": raw_handling or "json_array_capped",
            "capped_json_path": str(path or "data.logSearchModels"),
            "observed_records": observed,
            "returned_records": returned,
            "missing_records": missing,
            "missing_body_reason": candidate.get("missing_body_reason") or "response_too_large",
            "cap_reason": candidate.get("cap_reason"),
        }
        return {key: value for key, value in metadata.items() if value is not None}
    return {}


def _value_at_path(value: Any, path: tuple[str, ...]) -> Any:
    cursor = value
    for key in path:
        if not isinstance(cursor, dict) or key not in cursor:
            return None
        cursor = cursor[key]
    return cursor


def _clone_json(value: Any) -> Any:
    return json.loads(json.dumps(value, ensure_ascii=False))


def _parse_nested_json(value: Any) -> Any:
    if isinstance(value, (dict, list)):
        return value
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text or text[0] not in "[{":
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def _safe_value_hash(value: Any) -> str:
    text = json.dumps(value, ensure_ascii=False, sort_keys=True) if isinstance(value, (dict, list)) else str(value)
    return "sha256:" + hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()[:16]


def _projection_meta() -> dict[str, Any]:
    return {
        "projection_applied": False,
        "projection_not_business_normalizer": True,
        "raw_body_not_retained_in_answer": True,
        "cap_after_projection": True,
        "projection_policy": "drop_obvious_useless_duplicate_huge_only",
        "projected_records": 0,
        "dropped_fields_count": 0,
        "sensitive_fields_projected_as_handles": 0,
        "strict_pii_fields_redacted": 0,
        "retained_field_paths": [],
        "field_paths_retained": [],
        "projection_errors": [],
    }


def _record_retained_path(meta: dict[str, Any], path: str) -> None:
    paths = meta.setdefault("retained_field_paths", [])
    if len(paths) < MAX_RETAINED_FIELD_PATHS and path not in paths:
        paths.append(path)
    meta["field_paths_retained"] = paths


def _should_drop_projection_key(key: str, value: Any) -> bool:
    normalized = _normalized_key(key)
    if key in PROJECTION_ALWAYS_KEEP_KEYS or _canonical_for_key(key):
        return False
    if any(fragment in normalized for fragment in PROJECTION_DROP_KEY_FRAGMENTS):
        return True
    if value in (None, "", [], {}):
        return True
    if normalized in PROJECTION_LARGE_LOW_VALUE_KEYS and not _contains_allowlisted_field(value):
        return True
    if isinstance(value, str) and len(value) > MAX_PROJECTED_STRING_VALUE_LENGTH and not _contains_allowlisted_field({key: value}):
        return True
    return False


def _contains_allowlisted_field(value: Any, *, depth: int = 0) -> bool:
    if depth > 5:
        return False
    if isinstance(value, dict):
        for key, child in value.items():
            if key in PROJECTION_ALWAYS_KEEP_KEYS or _canonical_for_key(str(key)):
                return True
            if isinstance(child, (dict, list)) and _contains_allowlisted_field(child, depth=depth + 1):
                return True
    elif isinstance(value, list):
        return any(_contains_allowlisted_field(item, depth=depth + 1) for item in value[:20])
    return False


def _safe_sensitive_projection(key: str, value: Any) -> dict[str, Any]:
    value_type = type(value).__name__
    text = json.dumps(value, ensure_ascii=False, sort_keys=True) if isinstance(value, (dict, list)) else str(value)
    return {
        "__sensitive_control_chain_field_present__": True,
        "field": key,
        "value_type": value_type,
        "value_length": len(text),
        "value_hash": _safe_value_hash(value),
    }


def _project_evidence_body(action: str, parsed: Any, *, body_path: str) -> tuple[Any, dict[str, Any]]:
    """Project large passthrough bodies before observation extraction.

    This is intentionally not a service normalizer and not a conclusion layer.
    It only removes obvious non-evidence bulk while retaining risk anchors and
    sensitive control-chain field presence as safe handles.
    """

    meta = _projection_meta()

    def project(item: Any, path: str, depth: int = 0) -> Any:
        if isinstance(item, dict):
            projected: dict[str, Any] = {}
            for key, child in item.items():
                child_path = f"{path}.{key}"
                if _is_credential_secret_key(str(key)):
                    projected[key] = _safe_sensitive_projection(str(key), child)
                    meta["sensitive_fields_projected_as_handles"] += 1
                    _record_retained_path(meta, child_path)
                    continue
                if _is_strict_pii_key(str(key)):
                    projected[key] = {"__strict_pii_redacted__": True}
                    meta["strict_pii_fields_redacted"] += 1
                    _record_retained_path(meta, child_path)
                    continue
                canonical = _canonical_for_key(str(key))
                if canonical in RISK_ENTITY_CANONICAL_FIELDS and isinstance(child, (str, int, float, bool)):
                    projected[key] = child
                    _record_retained_path(meta, child_path)
                    continue
                if _should_drop_projection_key(str(key), child):
                    meta["dropped_fields_count"] += 1
                    continue
                if str(key) == "logContent" and isinstance(child, str) and "parsedLogContent" in item:
                    meta["dropped_fields_count"] += 1
                    continue
                projected_child = project(child, child_path, depth + 1)
                if projected_child in (None, "", [], {}):
                    meta["dropped_fields_count"] += 1
                    continue
                projected[key] = projected_child
                if _canonical_for_key(str(key)) or str(key) in PROJECTION_ALWAYS_KEEP_KEYS:
                    _record_retained_path(meta, child_path)
            return projected
        if isinstance(item, list):
            projected_list = []
            for index, child in enumerate(item[:MAX_PROJECTED_ARRAY_ITEMS]):
                child_path = f"{path}[{index}]"
                projected_child = project(child, child_path, depth + 1)
                if projected_child in (None, "", [], {}):
                    meta["dropped_fields_count"] += 1
                    continue
                projected_list.append(projected_child)
            if action == "login_logs_search" and path.endswith("logSearchModels"):
                meta["projected_records"] += len(projected_list)
            return projected_list
        if isinstance(item, str):
            if _looks_sensitive_scalar(item):
                meta["strict_pii_fields_redacted"] += 1
                return {"__strict_pii_redacted__": True}
            if len(item) > MAX_PROJECTED_STRING_VALUE_LENGTH:
                meta["dropped_fields_count"] += 1
                return {
                    "__large_string_projected__": True,
                    "value_length": len(item),
                    "value_hash": _safe_value_hash(item),
                }
        return item

    try:
        projected = project(parsed, body_path)
        if projected is not parsed:
            meta["projection_applied"] = True
        if meta["projected_records"] == 0 and isinstance(projected, dict):
            records = _value_at_path(projected, LOGIN_LOGS_ARRAY_CAP_PATH)
            if isinstance(records, list):
                meta["projected_records"] = len(records)
        return projected, meta
    except Exception as exc:  # defensive: projection must never block parsing
        meta["projection_errors"].append(type(exc).__name__)
        return parsed, meta


def _aggregate_projection_metadata(items: list[dict[str, Any]]) -> dict[str, Any]:
    aggregate = _projection_meta()
    if not items:
        return aggregate
    aggregate["projection_applied"] = any(bool(item.get("projection_applied")) for item in items)
    for key in (
        "projected_records",
        "dropped_fields_count",
        "sensitive_fields_projected_as_handles",
        "strict_pii_fields_redacted",
    ):
        aggregate[key] = sum(int(item.get(key) or 0) for item in items)
    retained_paths: list[str] = []
    errors: list[str] = []
    for item in items:
        retained_paths.extend(str(path) for path in item.get("retained_field_paths", []) if path)
        errors.extend(str(error) for error in item.get("projection_errors", []) if error)
    aggregate["retained_field_paths"] = _unique(retained_paths)[:MAX_RETAINED_FIELD_PATHS]
    aggregate["field_paths_retained"] = aggregate["retained_field_paths"]
    aggregate["projection_errors"] = _unique(errors)
    return aggregate


def _prepare_body_for_action(action: str, parsed: Any) -> Any:
    if action != "login_logs_search" or not isinstance(parsed, dict):
        return parsed
    candidate_paths = (LOGIN_LOGS_ARRAY_CAP_PATH, ("logSearchModels",))
    if not any(isinstance(_value_at_path(parsed, path), list) for path in candidate_paths):
        return parsed
    cloned = _clone_json(parsed)
    for path in candidate_paths:
        cloned_records = _value_at_path(cloned, path)
        if not isinstance(cloned_records, list):
            continue
        for record in cloned_records[:200]:
            if not isinstance(record, dict):
                continue
            parsed_log_content = _parse_nested_json(record.get("logContent"))
            if isinstance(parsed_log_content, dict):
                record["parsedLogContent"] = parsed_log_content
                params = parsed_log_content.get("params")
                if isinstance(params, dict):
                    record["parsedLogContentParams"] = params
            params = record.get("params")
            if isinstance(params, dict):
                record["loginParams"] = params
    return cloned


def _collect_body_candidates(value: Any, *, path: str = "$", limit: int = 12) -> list[tuple[str, Any]]:
    candidates: list[tuple[str, Any]] = []
    if len(candidates) >= limit:
        return candidates
    if isinstance(value, dict):
        for key, item in value.items():
            child_path = f"{path}.{key}"
            lowered = key.lower()
            if _is_credential_secret_key(key):
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
                if _is_credential_secret_key(key):
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
                if _is_strict_pii_key(key):
                    flags.append("pii_strict_redacted")
                    continue
                if canonical and isinstance(child, (str, int, float, bool)):
                    if canonical not in RISK_ENTITY_CANONICAL_FIELDS and _looks_sensitive_scalar(child):
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


def _source_contextual_handles(action: str, handles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Add source-specific aliases without changing the global field taxonomy."""

    contextual: list[dict[str, Any]] = []
    photo_actions = {
        "archives_photo_search",
        "archives_photo_profile",
        "archives_photo_meta",
        "archives_gallery_photo_list",
    }
    for handle in handles:
        canonical = str(handle.get("canonical_field") or "")
        field = _normalized_key(str(handle.get("field") or ""))
        field_path = str(handle.get("field_path") or "")
        normalized_path = _normalized_key(field_path)
        if action in photo_actions:
            if canonical in {"device_id", "candidate_device_id"} and (
                field in {"deviceid", "did"}
                or "commondeviceid" in normalized_path
                or "photometacommondeviceid" in normalized_path
            ):
                clone = dict(handle)
                clone["canonical_field"] = "publish_device"
                clone["contextual_alias"] = "photo_meta_common_deviceid_as_publish_device"
                contextual.append(clone)
            if canonical == "login_time" and field == "time":
                clone = dict(handle)
                clone["canonical_field"] = "publish_time"
                clone["contextual_alias"] = "photo_list_time_as_publish_time"
                contextual.append(clone)
        elif action == "archives_user_analysis":
            if canonical in {"device_id", "candidate_device_id"} and field in {"deviceid", "did"}:
                clone = dict(handle)
                clone["canonical_field"] = "operation_device"
                clone["contextual_alias"] = "user_analysis_deviceid_as_operation_device"
                contextual.append(clone)
    return handles + contextual


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
    projection_metadata: list[dict[str, Any]] = []
    flags: list[str] = []
    row_cap_metadata = _row_cap_metadata(source_payload, transport_row)

    for body_path, body_value in body_candidates:
        parsed, parse_status = _parse_body_value(body_value)
        body_parse_statuses.append(f"{body_path}:{parse_status}")
        if parsed is None:
            if parse_status.endswith("parse_error"):
                flags.append("passthrough_interpretation_gap")
            continue
        prepared = _prepare_body_for_action(action, parsed)
        projected, projection_meta = _project_evidence_body(action, prepared, body_path=body_path)
        projection_metadata.append(projection_meta)
        parsed_values.append((body_path, projected))

    direct_handles, direct_flags = _extract_handles(source_payload, source_id=source_id, path="$passthrough")
    flags.extend(direct_flags)
    body_handles: list[dict[str, Any]] = []
    for body_path, parsed in parsed_values:
        handles, body_flags = _extract_handles(parsed, source_id=source_id, path=body_path)
        body_handles.extend(handles)
        flags.extend(body_flags)

    parsed_body_handles = _dedupe_handles(_source_contextual_handles(action, body_handles))
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
    if any(item.get("projection_applied") for item in projection_metadata):
        flags.extend([
            "evidence_projection_applied",
            "projection_not_business_normalizer",
            "raw_body_not_retained_in_answer",
        ])
    if any(item.get("sensitive_fields_projected_as_handles") for item in projection_metadata):
        flags.append("credential_control_chain_projected_as_safe_handle")
    if any(item.get("strict_pii_fields_redacted") for item in projection_metadata):
        flags.append("pii_strict_redacted")
    if any(item.get("projection_errors") for item in projection_metadata):
        flags.append("projection_error")
    if not parsed_values and (transport_row.get("body_present") is True or int(transport_row.get("observed_bytes") or 0) > 0):
        flags.append("service_body_visibility_gap")
    if body_candidates and not parsed_values:
        flags.append("passthrough_interpretation_gap")
    if missing_business_fields and str(transport_row.get("quality_class") or "") in {"completed", "partial"}:
        flags.extend(["observation_compression_gap", "business_fields_not_extracted"])

    source_specific_flags = _source_specific_flags(action, missing_business_fields, extracted_business_fields, transport_row)
    flags.extend(source_specific_flags)
    if row_cap_metadata:
        flags.append("json_array_capped_body_available")
        if action == "login_logs_search":
            if parsed_values:
                flags.append("partial_login_log_parsed_from_json_array_capped")
            if int(row_cap_metadata.get("missing_records") or 0) > 0:
                flags.append("login_log_incomplete")

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
        "passthrough_row_cap": row_cap_metadata,
        "evidence_projection": _aggregate_projection_metadata(projection_metadata),
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
    elif action in {"archives_photo_search", "archives_photo_profile", "archives_photo_meta", "archives_gallery_photo_list"}:
        if {"photo_id", "publish_time", "publish_source", "publish_device"} & set(missing_business_fields):
            flags.append("content_chain_business_fields_missing")
        if "publish_device" in extracted_business_fields:
            flags.append("publish_device_candidate_device_source")
        if action in {"archives_photo_profile", "archives_photo_meta"} and "publish_device" in missing_business_fields:
            flags.append("publish_device_missing_after_photo_meta")
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
    if action in {"archives_photo_search", "archives_photo_profile", "archives_photo_meta", "archives_gallery_photo_list"} and {"publish_time", "publish_source", "publish_device", "photo_id"} & fields:
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
