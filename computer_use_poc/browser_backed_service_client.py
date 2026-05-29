#!/usr/bin/env python3
"""Executable client for the local browser-backed source service.

This module intentionally keeps Dennis out of browser ownership and auth
material handling. It only calls fixed local service actions with typed JSON
parameters and normalizes standard source responses for the source completion
matrix / partial evidence card path.
"""

from __future__ import annotations

import argparse
import errno
import json
import re
import socket
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, Iterable, Mapping, Optional


DEFAULT_BASE_URL = "http://127.0.0.1:8787"
DEFAULT_TIMEOUT_SECONDS = 10

ACTION_ENDPOINTS = {
    "track_analysis_summary": "/actions/track_analysis_summary",
    "rcp_snapshot": "/actions/rcp_snapshot",
    "weapon_inventory": "/actions/weapon_inventory",
    "login_logs_search": "/actions/login_logs_search",
    "archives_user_analysis": "/actions/archives_user_analysis",
}

ACTION_TO_SOURCE = {
    "track_analysis_summary": "track_analysis_summary",
    "rcp_snapshot": "rcp_snapshot",
    "weapon_inventory": "weapon_inventory",
    "login_logs_search": "login_logs_search",
    "archives_user_analysis": "archives_user_analysis",
}

ACCOUNT_SECURITY_TRACK_SUB_INTERFACES = ("profile", "getUseDuration", "getDeviceIds", "getLastestDateTime")
ACCOUNT_SECURITY_RISKDATA_DEVICE_PREFIXES = ("ANDROID_", "IOS_")
TRACK_ANALYSIS_BUNDLE_SOURCE_NAME = "track_analysis_account_security_bundle"
TRACK_ANALYSIS_BUNDLE_MODE = "account_security_bundle"
ARCHIVES_USER_ANALYSIS_FIXED_PATH = "/v3/user/log/coreLogs/fetch"
ARCHIVES_USER_ANALYSIS_FILTER_FIELDS = (
    "loginStart",
    "registerBind",
    "resetPass",
    "protectAccount",
    "liveStream",
    "scanCode",
    "logout",
    "frozen",
)
DEFAULT_OUTPUT_SCOPE = "internal_risk_review"
OUTPUT_SCOPES = {"internal_risk_review", "external_share"}
FIELD_CLASSIFICATION = {
    "credential_secret": [
        "cookie",
        "token",
        "session",
        "header",
        "authorization",
        "password",
        "raw_response_full_body",
        "raw_login_records_full_dump",
        "raw_labelInfo_full_dump",
        "raw_originalLog_full_dump",
    ],
    "pii_strict": ["phone_number", "id_card", "real_name"],
    "risk_entity_identifier": [
        "user_id",
        "uid",
        "device_id",
        "deviceId",
        "did",
        "DID",
        "ip",
        "userIpDesc",
        "eventId",
        "sourceId",
        "photo_id",
        "photoId",
        "live_id",
        "liveId",
        "strategy_id",
        "hitFusePolicyCode",
        "strategy_code",
        "logSource",
        "method",
        "timestamp",
        "_occurTime",
    ],
    "source_summary_metric": ["records_count", "event_count", "duration", "field_presence", "latency_ms"],
}

FORBIDDEN_INPUT_KEYS = {
    "url",
    "uri",
    "href",
    "origin",
    "host",
    "hostname",
    "path",
    "pathname",
    "endpoint",
    "route",
    "header",
    "headers",
    "cookie",
    "cookies",
    "authorization",
    "auth",
    "token",
    "access_token",
    "refresh_token",
    "session",
    "session_id",
    "secret",
    "raw_query",
    "raw_body",
}

COMPLETED_STATUSES = {"ok", "completed"}
NO_DATA_STATUSES = {"no_data", "completed_no_data", "completed_no_hit_for_small_window"}
AUTH_FAILED_STATUSES = {"auth_failed"}
BLOCKED_STATUSES = {"blocked", "network_error", "platform_error"}
TIMEOUT_STATUSES = {"timeout"}
PARSE_ERROR_STATUSES = {"parse_error"}
INVALID_PARAMETER_STATUSES = {"parameter_error", "invalid_parameter", "wrong_request_body_shape"}
DISPLAY_FORBIDDEN_FIELD_MARKERS = {
    "raw_profile",
    "raw_body",
    "raw_response",
    "raw_login_records",
    "raw_labelinfo",
    "raw_originalLog",
    "requestParam",
    "extraParam",
    "logContent",
    "full_json",
    "password",
    "authorization",
    "cookie",
    "session",
    "credential",
}


class BrowserBackedServiceInputError(ValueError):
    """Raised when the caller tries to bypass the fixed action contract."""


class BrowserBackedServiceClient:
    """Fixed-action HTTP client for browser-backed source results."""

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
        opener: Optional[Any] = None,
    ) -> None:
        self.base_url = _validate_local_base_url(base_url)
        self.timeout_seconds = timeout_seconds
        self.opener = opener or urllib.request.build_opener()

    def call_action(self, action_name: str, typed_params: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
        """Call one fixed browser-backed action and normalize the response.

        Transport failures are returned as source results instead of escaping as
        Dennis runtime failures.
        """

        _validate_action_name(action_name)
        params = dict(typed_params or {})
        _validate_typed_params(params)

        endpoint = ACTION_ENDPOINTS[action_name]
        service_url = f"{self.base_url}{endpoint}"
        started_at = time.monotonic()
        body = json.dumps(params, ensure_ascii=True, separators=(",", ":")).encode("utf-8")
        request = urllib.request.Request(service_url, data=body, method="POST")
        request.add_header("Content-Type", "application/json")
        request.add_header("Accept", "application/json")

        try:
            with self.opener.open(request, timeout=self.timeout_seconds) as response:
                http_status = int(response.getcode())
                response_text = response.read().decode("utf-8", errors="replace")
        except (TimeoutError, socket.timeout) as exc:
            return _transport_result(
                action_name,
                source_status="timeout",
                error_type="service_timeout",
                failure_layer="service_transport",
                started_at=started_at,
                detail=str(exc),
            )
        except urllib.error.HTTPError as exc:
            return _transport_result(
                action_name,
                source_status="blocked",
                error_type="service_http_error",
                failure_layer="service_transport",
                started_at=started_at,
                http_status=exc.code,
            )
        except urllib.error.URLError as exc:
            return _transport_result(
                action_name,
                source_status="blocked",
                error_type=_classify_url_error(exc),
                failure_layer="service_transport",
                started_at=started_at,
                detail=str(exc.reason),
            )

        try:
            service_payload = json.loads(response_text)
        except json.JSONDecodeError:
            return _transport_result(
                action_name,
                source_status="parse_error",
                error_type="service_non_json_response",
                failure_layer="service_transport",
                started_at=started_at,
                http_status=http_status,
            )

        return normalize_service_response(action_name, service_payload, http_status=http_status)

    def call_account_security_sources(
        self,
        user_id: str,
        app_name: str = "KUAISHOU",
        include_rcp_snapshot: bool = True,
    ) -> list[Dict[str, Any]]:
        """Call the default single-user account-security browser-backed sources.

        Track Analysis remains one evidence source, but its account-security
        bundle is collected through four explicit sub-interface calls before
        being merged into one display-safe source result.
        """

        results: list[Dict[str, Any]] = []
        track_results: list[Dict[str, Any]] = []
        for request_plan in build_account_security_browser_backed_requests(
            user_id,
            app_name=app_name,
            include_rcp_snapshot=include_rcp_snapshot,
            expand_track_analysis_bundle=True,
        ):
            action_name = str(request_plan["action_name"])
            result = self.call_action(action_name, request_plan.get("typed_params", {}))
            result["planned_source_name"] = request_plan.get("source_name")
            result["typed_params_summary"] = _typed_params_summary(request_plan.get("typed_params", {}))
            if request_plan.get("bundle_source_name") == TRACK_ANALYSIS_BUNDLE_SOURCE_NAME:
                result["requested_track_sub_interface"] = request_plan.get("track_sub_interface")
                track_results.append(result)
                continue

            results.append(result)
            fallback = request_plan.get("fallback_on")
            if result.get("source_status") == "parse_error" and isinstance(fallback, Mapping):
                fallback_plan = fallback.get("parse_error")
                if isinstance(fallback_plan, Mapping):
                    fallback_result = self.call_action(
                        str(fallback_plan["action_name"]),
                        fallback_plan.get("typed_params", {}),
                    )
                    fallback_result["planned_source_name"] = fallback_plan.get("source_name")
                    fallback_result["typed_params_summary"] = _typed_params_summary(fallback_plan.get("typed_params", {}))
                    fallback_result["fallback_for"] = request_plan.get("source_name")
                    results.append(fallback_result)

        if track_results:
            results.insert(0, merge_track_analysis_account_security_bundle(track_results))
        return results


def build_account_security_browser_backed_requests(
    user_id: str,
    app_name: str = "KUAISHOU",
    include_rcp_snapshot: bool = True,
    expand_track_analysis_bundle: bool = True,
) -> list[Dict[str, Any]]:
    """Return the clean full_runtime request plan for one account-security user.

    This constructs fixed browser-backed actions only. It does not call the
    local service, start a browser, inspect auth state, or use legacy runners.
    """

    if not isinstance(user_id, str) or not user_id.isdigit():
        raise BrowserBackedServiceInputError("user_id must be a decimal string")
    if app_name not in {"KUAISHOU", "NEBULA"}:
        raise BrowserBackedServiceInputError("app_name must be KUAISHOU or NEBULA")

    requests: list[Dict[str, Any]] = []
    if expand_track_analysis_bundle:
        for sub_interface in ACCOUNT_SECURITY_TRACK_SUB_INTERFACES:
            requests.append(
                {
                    "source_name": TRACK_ANALYSIS_BUNDLE_SOURCE_NAME,
                    "bundle_source_name": TRACK_ANALYSIS_BUNDLE_SOURCE_NAME,
                    "track_sub_interface": sub_interface,
                    "action_name": "track_analysis_summary",
                    "typed_params": {
                        "user_id": user_id,
                        "appName": app_name,
                        "mode": TRACK_ANALYSIS_BUNDLE_MODE,
                        "sub_interface": sub_interface,
                        "sub_interfaces": [sub_interface],
                    },
                }
            )
    else:
        requests.append(
            {
                "source_name": TRACK_ANALYSIS_BUNDLE_SOURCE_NAME,
                "action_name": "track_analysis_summary",
                "typed_params": {
                    "user_id": user_id,
                    "appName": app_name,
                    "mode": TRACK_ANALYSIS_BUNDLE_MODE,
                    "sub_interfaces": list(ACCOUNT_SECURITY_TRACK_SUB_INTERFACES),
                },
            }
        )
    if include_rcp_snapshot:
        requests.append(
            {
                "source_name": "rcp_strategy_hit_entry",
                "action_name": "rcp_snapshot",
                "typed_params": {
                    "entity_type": "user_id",
                    "entity_id": user_id,
                    "mode": "account_security_strategy_event_entry",
                },
            }
        )
    requests.extend(
        [
            {
                "source_name": "weapon_user_to_device_graph",
                "action_name": "weapon_inventory",
                "typed_params": {
                    "user_id": user_id,
                    "mode": "account_security_user_device_graph_with_conditional_riskData",
                    "riskData_trigger_device_prefix": list(ACCOUNT_SECURITY_RISKDATA_DEVICE_PREFIXES),
                },
            },
            {
                "source_name": "user_login_unified_log",
                "action_name": "login_logs_search",
                "typed_params": {
                    "user_id": user_id,
                    "window": "last_7d",
                    "recallSource": "2,0,1,3",
                },
                "fallback_on": {
                    "parse_error": {
                        "source_name": "user_login_unified_log_24h_fallback",
                        "action_name": "login_logs_search",
                        "typed_params": {
                            "user_id": user_id,
                            "window": "last_24h",
                            "recallSource": "2,0,1,3",
                        },
                        "preserve_primary_source_quality": True,
                    }
                },
            },
        ]
    )

    for request in requests:
        _validate_action_name(str(request["action_name"]))
        _validate_typed_params(request.get("typed_params", {}))
        fallback = request.get("fallback_on")
        if isinstance(fallback, Mapping):
            for fallback_plan in fallback.values():
                if isinstance(fallback_plan, Mapping):
                    _validate_action_name(str(fallback_plan["action_name"]))
                    _validate_typed_params(fallback_plan.get("typed_params", {}))
    return requests


def build_archives_user_analysis_browser_backed_request(
    user_id: str,
    begin_time_ms: int,
    end_time_ms: int,
    page_index: int = 1,
    page_size: int = 30,
) -> Dict[str, Any]:
    """Return the fixed Archives Center user-analysis action plan.

    The local browser-backed service owns same-origin fetch and maps these typed
    params to `/v3/user/log/coreLogs/fetch`; Dennis never passes URL/path/header
    or auth material.
    """

    if not isinstance(user_id, str) or not user_id.isdigit():
        raise BrowserBackedServiceInputError("user_id must be a decimal string")
    if not isinstance(begin_time_ms, int) or not isinstance(end_time_ms, int) or begin_time_ms <= 0 or end_time_ms <= 0:
        raise BrowserBackedServiceInputError("begin_time_ms and end_time_ms must be positive millisecond timestamps")
    if begin_time_ms >= end_time_ms:
        raise BrowserBackedServiceInputError("begin_time_ms must be before end_time_ms")
    if not isinstance(page_index, int) or page_index < 1:
        raise BrowserBackedServiceInputError("page_index must be a positive integer")
    if not isinstance(page_size, int) or page_size < 1 or page_size > 100:
        raise BrowserBackedServiceInputError("page_size must be between 1 and 100")

    typed_params: Dict[str, Any] = {
        "user_id": user_id,
        "mode": "focused_login_risk_core_logs",
        "beginTime": begin_time_ms,
        "endTime": end_time_ms,
        "pageIndex": page_index,
        "pageSize": page_size,
        "haveParamAuth": 1,
        "operation_filters": {field: 1 for field in ARCHIVES_USER_ANALYSIS_FILTER_FIELDS},
    }
    request = {
        "source_name": "archives_user_analysis",
        "action_name": "archives_user_analysis",
        "priority": "P0",
        "fixed_path": ARCHIVES_USER_ANALYSIS_FIXED_PATH,
        "typed_params": typed_params,
        "body_builder_summary": {
            "service_side_body_builder": True,
            "body_fields": [
                "userId",
                "beginTime",
                "endTime",
                "pageIndex",
                "pageSize",
                "haveParamAuth",
                *ARCHIVES_USER_ANALYSIS_FILTER_FIELDS,
            ],
            "all_operation_filters_default_on": True,
            "raw_requestParam_extraParam_output": False,
        },
    }
    _validate_action_name(str(request["action_name"]))
    _validate_typed_params(request["typed_params"])
    return request


def _typed_params_summary(typed_params: Any) -> Dict[str, Any]:
    if not isinstance(typed_params, Mapping):
        return {}
    return {
        str(key): value
        for key, value in typed_params.items()
        if str(key) not in {"user_id", "entity_id"}
    }


def merge_track_analysis_account_security_bundle(results: Iterable[Mapping[str, Any]]) -> Dict[str, Any]:
    """Merge four track-analysis sub-interface action results into one source.

    The merge is intentionally conservative: a sub-interface is considered
    completed only when the observed sub-interface matches the requested one.
    This prevents a service-side fallback to `getLastestDateTime` from being
    presented as a complete account-security bundle.
    """

    materialized = [dict(result) for result in results]
    sub_interface_statuses: Dict[str, Dict[str, Any]] = {}
    profile_summary: Dict[str, Any] = {}
    latest_timestamp_summary: Dict[str, Any] = {}
    use_duration_summary: Dict[str, Any] = {}
    device_ids_summary: Dict[str, Any] = {}
    total_latency = 0

    for result in materialized:
        requested = str(result.get("requested_track_sub_interface") or "")
        observed = _observed_track_sub_interface(result) or requested
        status = str(result.get("source_status") or "blocked")
        total_latency += int(result.get("latency_ms") or 0)
        matched = bool(requested and observed == requested)
        summary = build_business_evidence_summary(result)
        if requested:
            sub_interface_statuses[requested] = {
                "source_status": status if matched else "wrong_sub_interface_result",
                "observed_sub_interface": observed or None,
                "error_type": result.get("error_type"),
                "latency_ms": result.get("latency_ms"),
            }
        if not matched:
            continue
        profile_summary.update(summary.get("profile_summary") or {})
        latest_timestamp_summary.update(summary.get("latest_timestamp_summary") or {})
        use_duration_summary.update(summary.get("use_duration_summary") or {})
        device_ids_summary.update(summary.get("device_ids_summary") or {})

    completed = [
        sub_interface
        for sub_interface, info in sub_interface_statuses.items()
        if info.get("source_status") == "completed"
    ]
    missing = [
        sub_interface
        for sub_interface in ACCOUNT_SECURITY_TRACK_SUB_INTERFACES
        if sub_interface not in completed
    ]
    source_status = _merged_bundle_status(
        [str(result.get("source_status") or "blocked") for result in materialized],
        completed_count=len(completed),
    )
    source_quality = {
        "source_status": source_status,
        "output_scope": DEFAULT_OUTPUT_SCOPE,
        "field_classification": _field_classification_summary(),
        "sub_interface_statuses": sub_interface_statuses,
        "sub_interfaces_completed": completed,
        "sub_interfaces_missing": missing,
        "partial_source": bool(missing),
        "no_data_not_risk_exclusion": True,
        "activity_signal_not_final_judgement": True,
        "redaction_applied": True,
        "raw_reference_retained_for_followup": False,
        "sensitive_output": False,
    }
    return {
        "source_name": "track_analysis_summary",
        "planned_source_name": TRACK_ANALYSIS_BUNDLE_SOURCE_NAME,
        "action_name": "track_analysis_summary",
        "source_status": source_status,
        "failure_layer": "no_failure" if source_status == "completed" else "source_observation",
        "error_type": None,
        "latency_ms": total_latency,
        "source_card": {
            "source_name": TRACK_ANALYSIS_BUNDLE_SOURCE_NAME,
            "action_name": "track_analysis_summary",
            "source_status": source_status,
            "bundle_summary": {
                "mode": TRACK_ANALYSIS_BUNDLE_MODE,
                "sub_interfaces": list(ACCOUNT_SECURITY_TRACK_SUB_INTERFACES),
                "sub_interfaces_completed": completed,
                "sub_interfaces_missing": missing,
                "account_security_bundle": True,
            },
            "profile_summary": profile_summary,
            "latest_timestamp_summary": latest_timestamp_summary,
            "getUseDuration": use_duration_summary,
            "getDeviceIds": device_ids_summary,
            "sub_interface_statuses": sub_interface_statuses,
            "output_scope": DEFAULT_OUTPUT_SCOPE,
            "field_classification": _field_classification_summary(),
            "body_policy": {
                "raw_response_full_body_returned": False,
                "credential_secret_plaintext_returned": False,
                "raw_records_full_dump_returned": False,
                "raw_labelInfo_full_dump_returned": False,
                "raw_originalLog_full_dump_returned": False,
                "sensitive_output": False,
            },
        },
        "source_quality": source_quality,
        "source_checkpoint_private": {"raw_references": [], "downstream_source_chaining": []},
        "redaction": {
            "redaction_applied": True,
            "raw_reference_retained_for_followup": False,
            "sensitive_output": False,
        },
        "sensitive_output": False,
        "source_provenance": "browser_backed_service",
        "no_data_not_risk_exclusion": True,
    }


def _observed_track_sub_interface(result: Mapping[str, Any]) -> str | None:
    for container in (
        result.get("response_shape_summary"),
        result.get("source_card"),
        result.get("source_quality"),
    ):
        found = _find_first(container, ("sub_interface", "observed_sub_interface"))
        if isinstance(found, str) and found:
            return found
    return None


def _merged_bundle_status(statuses: list[str], completed_count: int) -> str:
    if completed_count:
        return "completed"
    if not statuses:
        return "blocked"
    if all(status == "no_data" for status in statuses):
        return "no_data"
    if all(status == "parse_error" for status in statuses):
        return "parse_error"
    if all(status == "timeout" for status in statuses):
        return "timeout"
    if all(status == "auth_failed" for status in statuses):
        return "auth_failed"
    return "blocked"


def normalize_service_response(
    action_name: str,
    service_payload: Mapping[str, Any],
    http_status: Optional[int] = None,
) -> Dict[str, Any]:
    """Normalize a standard browser-backed service result for Dennis."""

    _validate_action_name(action_name)
    source_name = ACTION_TO_SOURCE[action_name]

    if service_payload.get("sensitive_output") is not False:
        return {
            "source_name": source_name,
            "action_name": action_name,
            "source_status": "blocked",
            "failure_layer": "sensitive_output_policy",
            "error_type": "sensitive_output_violation",
            "http_status": http_status,
            "latency_ms": service_payload.get("latency_ms"),
            "source_card": _synthetic_source_card(action_name, "blocked", "sensitive_output_violation"),
            "source_quality": _synthetic_source_quality("blocked", "sensitive_output_violation"),
            "sensitive_output": False,
            "source_provenance": "browser_backed_service",
        }

    raw_status = _coerce_status(service_payload)
    error_type = service_payload.get("error_type")
    normalized_status, failure_layer = _normalize_status(raw_status, error_type)
    output_scope = _coerce_output_scope(service_payload.get("output_scope"))
    source_card = _sanitize_display_material(
        service_payload.get("source_card") or _synthetic_source_card(action_name, normalized_status, error_type),
        output_scope,
    )
    source_quality = _sanitize_display_material(
        service_payload.get("source_quality") or _synthetic_source_quality(normalized_status, error_type),
        output_scope,
    )
    source_checkpoint_private = _sanitize_source_checkpoint_private(service_payload)
    raw_reference_retained = bool(source_checkpoint_private.get("raw_references"))
    if isinstance(source_quality, Mapping):
        source_quality = dict(source_quality)
        source_quality.setdefault("raw_reference_retained_for_followup", raw_reference_retained)
        source_quality.setdefault("redaction_applied", True)
        source_quality.setdefault("sensitive_output", False)
        source_quality.setdefault("output_scope", output_scope)
        source_quality.setdefault("field_classification", _field_classification_summary())
        source_quality.setdefault(
            "source_status_not_risk_exclusion",
            normalized_status in {"no_data", "blocked", "auth_failed", "timeout", "parse_error", "invalid_parameter"},
        )
    no_data_not_risk_exclusion = _extract_no_data_marker(source_quality, normalized_status)

    normalized: Dict[str, Any] = {
        "source_name": source_name,
        "action_name": action_name,
        "service_action_status": service_payload.get("status"),
        "source_status": normalized_status,
        "failure_layer": failure_layer,
        "error_type": error_type,
        "http_status": http_status,
        "latency_ms": service_payload.get("latency_ms"),
        "output_scope": output_scope,
        "field_classification": _field_classification_summary(),
        "source_card": source_card,
        "source_quality": source_quality,
        "source_checkpoint_private": source_checkpoint_private,
        "redaction": {
            "redaction_applied": True,
            "raw_reference_retained_for_followup": raw_reference_retained,
            "sensitive_output": False,
        },
        "sensitive_output": False,
        "source_provenance": "browser_backed_service",
        "no_data_not_risk_exclusion": no_data_not_risk_exclusion,
    }

    response_summary = _safe_nested_get(service_payload, ("data", "response_summary"))
    if isinstance(response_summary, Mapping):
        normalized["response_shape_summary"] = dict(response_summary)

    if action_name == "archives_user_analysis":
        _attach_archives_user_analysis_contract_fields(normalized, service_payload, source_card, source_quality, output_scope)

    return normalized


def _attach_archives_user_analysis_contract_fields(
    normalized: Dict[str, Any],
    service_payload: Mapping[str, Any],
    source_card: Any,
    source_quality: Any,
    output_scope: str,
) -> None:
    material = {
        "service_payload": service_payload,
        "source_card": source_card if isinstance(source_card, Mapping) else {},
        "source_quality": source_quality if isinstance(source_quality, Mapping) else {},
    }
    key_entities = service_payload.get("key_entities")
    if not isinstance(key_entities, Mapping):
        key_entities = _pick_fields(
            material,
            ("user_id", "userId", "deviceId", "device_id_sample", "ip", "userIpDesc", "photo_id", "photoId"),
            output_scope,
        )
    missing_fields = service_payload.get("missing_fields")
    if not isinstance(missing_fields, list):
        missing_fields = _find_first(material, ("missing_fields", "fields_missing", "required_fields_missing"), output_scope)
    if not isinstance(missing_fields, list):
        missing_fields = []
    next_action = service_payload.get("next_action")
    if not isinstance(next_action, str) or not next_action:
        next_action = _find_first(material, ("next_action",), output_scope)
    if not isinstance(next_action, str) or not next_action:
        next_action = "Cross-check Archives user analysis with login logs, Weapon, and RCP before any risk judgement."

    normalized["key_entities"] = _sanitize_display_material(key_entities, output_scope)
    normalized["missing_fields"] = _sanitize_display_material(missing_fields, output_scope)
    normalized["next_action"] = _safe_display_value("next_action", next_action, output_scope)
    normalized["no_data_not_risk_exclusion"] = True
    if isinstance(normalized.get("source_quality"), Mapping):
        quality = dict(normalized["source_quality"])
        quality.setdefault("archives_action_contract", "archives_user_analysis")
        quality["no_data_not_risk_exclusion"] = True
        quality.setdefault("raw_response_full_body_returned", False)
        quality.setdefault("requestParam_extraParam_suppressed", True)
        normalized["source_quality"] = quality
    if isinstance(normalized.get("source_card"), Mapping):
        card = dict(normalized["source_card"])
        card.setdefault("key_entities", normalized["key_entities"])
        card.setdefault("missing_fields", normalized["missing_fields"])
        card.setdefault("next_action", normalized["next_action"])
        normalized["source_card"] = card


def build_source_completion_matrix(results: Iterable[Mapping[str, Any]]) -> Dict[str, Any]:
    """Bucket normalized source results for Dennis evidence rendering."""

    matrix: Dict[str, Any] = {
        "completed_sources": [],
        "no_data_sources": [],
        "auth_failed_sources": [],
        "blocked_sources": [],
        "timeout_sources": [],
        "parse_error_sources": [],
        "invalid_parameter_sources": [],
        "source_quality": {},
    }
    for result in results:
        source_name = str(result.get("source_name"))
        status = result.get("source_status")
        if status == "completed":
            matrix["completed_sources"].append(source_name)
        elif status == "no_data":
            matrix["no_data_sources"].append(source_name)
        elif status == "auth_failed":
            matrix["auth_failed_sources"].append(source_name)
        elif status == "timeout":
            matrix["timeout_sources"].append(source_name)
        elif status == "parse_error":
            matrix["parse_error_sources"].append(source_name)
        elif status == "invalid_parameter":
            matrix["invalid_parameter_sources"].append(source_name)
        else:
            matrix["blocked_sources"].append(source_name)

        matrix["source_quality"][source_name] = {
            "source_status": status,
            "failure_layer": result.get("failure_layer"),
            "error_type": result.get("error_type"),
            "latency_ms": result.get("latency_ms"),
            "output_scope": _coerce_output_scope(result.get("output_scope")),
            "source_card_present": result.get("source_card") is not None,
            "source_quality_present": result.get("source_quality") is not None,
            "no_data_not_risk_exclusion": bool(result.get("no_data_not_risk_exclusion")),
            "source_status_not_risk_exclusion": status in {"no_data", "blocked", "auth_failed", "timeout", "parse_error", "invalid_parameter"},
            "sensitive_output": False,
        }
    return matrix


def build_partial_evidence_card(
    results: Iterable[Mapping[str, Any]],
    output_scope: str = DEFAULT_OUTPUT_SCOPE,
) -> Dict[str, Any]:
    """Build a display-safe partial evidence card from normalized source results."""

    scope = _coerce_output_scope(output_scope)
    materialized_results = [dict(result) for result in results]
    matrix = build_source_completion_matrix(materialized_results)
    evidence_sections = []
    for result in materialized_results:
        evidence_sections.append(
            {
                "source_name": result.get("source_name"),
                "source_status": result.get("source_status"),
                "error_type": result.get("error_type"),
                "source_card_present": result.get("source_card") is not None,
                "source_quality_present": result.get("source_quality") is not None,
                "no_data_not_risk_exclusion": bool(result.get("no_data_not_risk_exclusion")),
                "business_summary": build_business_evidence_summary(result, output_scope=scope),
            }
        )

    evidence_summary_by_source = {
        str(result.get("source_name")): build_business_evidence_summary(result, output_scope=scope)
        for result in materialized_results
    }
    missing_evidence = build_missing_evidence(materialized_results)
    return {
        "card_type": "partial_evidence_card",
        "sensitive_output": False,
        "output_scope": scope,
        "field_classification": _field_classification_summary(),
        "source_completion_matrix": matrix,
        "completed_sources": matrix["completed_sources"],
        "no_data_sources": matrix["no_data_sources"],
        "blocked_sources": matrix["blocked_sources"],
        "source_quality": matrix["source_quality"],
        "no_data_not_risk_exclusion": any(
            bool(result.get("no_data_not_risk_exclusion")) for result in materialized_results
        ),
        "evidence_summary_by_source": evidence_summary_by_source,
        "evidence_boundary": {
            "no_data_not_no_risk": True,
            "strategy_hit_device_risk_activity_profile_are_evidence_not_final_judgement": True,
            "final_risk_judgement_made": False,
            "sensitive_output_false_meaning": (
                "no credential_secret, raw full body, raw records, raw labelInfo, or raw originalLog full dump; "
                "risk_entity_identifier may appear in internal_risk_review"
            ),
        },
        "missing_evidence": missing_evidence,
        "next_action": build_next_action(missing_evidence),
        "final_risk_judgement_made": False,
        "evidence_sections": evidence_sections,
    }


def build_small_batch_evidence_output(
    user_results: Iterable[Mapping[str, Any]],
    output_scope: str = DEFAULT_OUTPUT_SCOPE,
) -> Dict[str, Any]:
    """Build display-safe small-batch evidence output.

    Each item in `user_results` must contain `user_id` and `results` (or
    `source_results`). Internal review output keeps the raw risk entity user id
    in the user title so reviewers can copy it for follow-up; external sharing
    gets a stable local alias and masked user id.
    """

    scope = _coerce_output_scope(output_scope)
    per_user_evidence = []
    for index, item in enumerate(user_results, start=1):
        user_id = str(item.get("user_id") or "")
        source_results = item.get("results") or item.get("source_results") or []
        evidence_card = build_partial_evidence_card(source_results, output_scope=scope)
        entry: Dict[str, Any] = {
            "user_title": _small_batch_user_title(user_id, index, scope),
            "source_completion_matrix": evidence_card["source_completion_matrix"],
            "completed_sources": evidence_card["completed_sources"],
            "no_data_sources": evidence_card["no_data_sources"],
            "blocked_sources": evidence_card["blocked_sources"],
            "evidence_summary_by_source": evidence_card["evidence_summary_by_source"],
            "missing_evidence": evidence_card["missing_evidence"],
            "sensitive_output": False,
            "final_risk_judgement_made": False,
        }
        if scope == "internal_risk_review":
            entry["user_id"] = user_id
        else:
            entry["user_ref"] = f"U{index}"
            entry["user_id"] = _external_user_id_label(user_id)
        per_user_evidence.append(entry)

    return {
        "card_type": "small_batch_evidence_summary",
        "execution_mode": "small_batch_execution_with_checkpoint",
        "output_scope": scope,
        "user_count": len(per_user_evidence),
        "per_user_evidence": per_user_evidence,
        "sensitive_output": False,
        "final_risk_judgement_made": False,
        "display_policy": {
            "internal_risk_review_user_title": "用户 {raw_user_id}",
            "external_share_user_title": "用户 U{index}（user_***last4）",
            "risk_entity_identifier_internal_raw_allowed": True,
            "risk_entity_identifier_external_masked": True,
        },
    }


def build_business_evidence_summary(
    result: Mapping[str, Any],
    output_scope: str = DEFAULT_OUTPUT_SCOPE,
) -> Dict[str, Any]:
    """Extract display-safe business evidence from source_card/source_quality."""

    if output_scope == DEFAULT_OUTPUT_SCOPE and result.get("output_scope"):
        scope = _coerce_output_scope(result.get("output_scope"))
    else:
        scope = _coerce_output_scope(output_scope)
    source_name = str(result.get("source_name") or "")
    action_name = str(result.get("action_name") or "")
    action = action_name or _source_to_action(source_name)
    if action == "track_analysis_summary":
        return _track_analysis_summary(result, scope)
    if action == "rcp_snapshot":
        return _rcp_summary(result, scope)
    if action == "weapon_inventory":
        return _weapon_summary(result, scope)
    if action == "login_logs_search":
        return _login_logs_summary(result, scope)
    if action == "archives_user_analysis":
        return _archives_user_analysis_summary(result, scope)
    return _generic_summary(result, scope)


def build_missing_evidence(results: Iterable[Mapping[str, Any]]) -> list[Dict[str, Any]]:
    missing: list[Dict[str, Any]] = []
    for result in results:
        source_name = str(result.get("source_name"))
        status = result.get("source_status")
        source_quality = result.get("source_quality") if isinstance(result.get("source_quality"), Mapping) else {}
        source_card = result.get("source_card") if isinstance(result.get("source_card"), Mapping) else {}
        for sub_interface in source_quality.get("sub_interfaces_missing", []) if isinstance(source_quality.get("sub_interfaces_missing"), list) else []:
            missing.append(
                {
                    "source_name": source_name,
                    "reason": f"track_analysis_sub_interface_missing:{sub_interface}",
                    "caveat": "account-security track bundle is partial until this sub-interface is collected",
                }
            )
        if source_name == "weapon_inventory" and _find_first(source_card, ("riskData_status",)) == "not_executed_missing_device_id":
            missing.append(
                {
                    "source_name": source_name,
                    "reason": "weapon_riskData_missing_device_safe_handle",
                    "caveat": "riskData must use a retained current-task raw device safe handle, not a masked display id",
                }
            )
        if status == "no_data":
            missing.append(
                {
                    "source_name": source_name,
                    "reason": "visible_window_no_data",
                    "caveat": "no_data is not no-risk evidence",
                }
            )
        elif status in {"blocked", "auth_failed", "timeout", "parse_error", "invalid_parameter"}:
            missing.append(
                {
                    "source_name": source_name,
                    "reason": f"source_status_{status}",
                    "error_type": result.get("error_type"),
                }
            )
    return missing


def build_next_action(missing_evidence: list[Mapping[str, Any]]) -> Dict[str, Any]:
    actions = ["confirm case complaint/event time window"]
    if missing_evidence:
        actions.append("retry or supplement missing sources only after source_quality is understood")
    actions.append("use DataAgent/Hive only as a recommendation for long-window or cross-table follow-up")
    return {
        "recommended_follow_up": actions,
        "dataagent_hive_called": False,
        "dataagent_hive_boundary": "recommendation_only_not_called",
    }


def _source_to_action(source_name: str) -> str:
    for action, source in ACTION_TO_SOURCE.items():
        if source == source_name:
            return action
    return source_name


def _summary_material(result: Mapping[str, Any], output_scope: str = DEFAULT_OUTPUT_SCOPE) -> Dict[str, Any]:
    merged: Dict[str, Any] = {}
    for key in ("source_card", "source_quality", "response_shape_summary"):
        value = result.get(key)
        if isinstance(value, Mapping):
            merged[key] = _sanitize_display_material(value, output_scope)
    return merged


def _has_private_raw_reference(result: Mapping[str, Any], ref_type: str) -> bool:
    checkpoint = result.get("source_checkpoint_private")
    if not isinstance(checkpoint, Mapping):
        return False
    refs = checkpoint.get("raw_references")
    if not isinstance(refs, list):
        return False
    for ref in refs:
        if isinstance(ref, Mapping) and ref.get("ref_type") == ref_type and ref.get("raw_reference_safe_id"):
            return True
    return False


def _find_first(value: Any, candidate_keys: Iterable[str], output_scope: str = DEFAULT_OUTPUT_SCOPE) -> Any:
    candidates = set(candidate_keys)
    if isinstance(value, Mapping):
        for key, nested in value.items():
            if key in candidates and _is_safe_display_value(key, nested, output_scope):
                return nested
        for key, nested in value.items():
            if not _is_safe_display_key(str(key)):
                continue
            found = _find_first(nested, candidates, output_scope)
            if found is not None:
                return found
    elif isinstance(value, list):
        for item in value:
            found = _find_first(item, candidates, output_scope)
            if found is not None:
                return found
    return None


def _pick_fields(
    material: Mapping[str, Any],
    field_names: Iterable[str],
    output_scope: str = DEFAULT_OUTPUT_SCOPE,
) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for field_name in field_names:
        value = _find_first(material, (field_name,), output_scope)
        if value is not None:
            result[field_name] = _safe_display_value(field_name, value, output_scope)
    return result


def _safe_display_value(key: str, value: Any, output_scope: str = DEFAULT_OUTPUT_SCOPE) -> Any:
    if not _is_safe_display_key(key):
        return "<redacted>"
    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, str) and _is_masked_placeholder(value):
        return value
    if _is_phone_key(key) and (_looks_like_phone(str(value)) or _looks_like_internal_phone_mask(str(value))):
        return _mask_phone(str(value), output_scope)
    if _is_id_card_key(key) and _looks_like_id_card(str(value)):
        return _id_card_summary(str(value), output_scope)
    if _is_real_name_key(key):
        return {"name_present": True}
    if _is_risk_entity_key(key) and isinstance(value, (str, int, float)):
        text = str(value)
        return text[:160] if output_scope == "internal_risk_review" else _mask_risk_entity(key, text)
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        return _display_string_value(key, value, output_scope)
    if isinstance(value, list):
        safe_values = []
        for item in value[:8]:
            if isinstance(item, (str, int, float, bool)) or item is None:
                safe_values.append(_safe_display_value(key, item, output_scope))
            elif isinstance(item, Mapping):
                safe_values.append(_safe_shape_keys(item))
            else:
                safe_values.append(type(item).__name__)
        return safe_values
    if isinstance(value, Mapping):
        return {
            str(nested_key): _safe_display_value(str(nested_key), nested_value, output_scope)
            for nested_key, nested_value in list(value.items())[:16]
            if _is_safe_display_key(str(nested_key))
        }
    return str(type(value).__name__)


def _is_safe_display_value(key: str, value: Any, output_scope: str = DEFAULT_OUTPUT_SCOPE) -> bool:
    if not _is_safe_display_key(key):
        return False
    if isinstance(value, Mapping):
        return True
    if isinstance(value, list):
        return True
    if isinstance(value, (str, int, float, bool)) or value is None:
        return _is_safe_display_string(key, str(value), output_scope)
    return False


def _is_safe_display_key(key: str) -> bool:
    lowered = key.lower()
    if lowered in {"labelinfo", "originallog"}:
        return False
    return not any(marker.lower() in lowered for marker in DISPLAY_FORBIDDEN_FIELD_MARKERS)


def _is_safe_display_string(key: str, value: str, output_scope: str = DEFAULT_OUTPUT_SCOPE) -> bool:
    lowered_key = key.lower()
    lowered_value = value.lower()
    if not _is_safe_display_key(key):
        return False
    if "labelinfo" in lowered_value or "originallog" in lowered_value:
        return False
    if _is_credential_secret_key(key) or _looks_like_credential_secret(value):
        return False
    if _is_real_name_key(key):
        return False
    if _is_id_card_key(key) and _looks_like_id_card(value):
        return False
    if _is_phone_key(key) and _looks_like_phone(value):
        return True
    if lowered_key.endswith("_count") or lowered_key.endswith("_present"):
        return True
    if output_scope == "external_share" and _is_risk_entity_key(key):
        return True
    if _is_risk_entity_key(key):
        return True
    if _looks_like_phone(value) or _looks_like_id_card(value):
        return False
    return True


def _display_string_value(key: str, value: str, output_scope: str = DEFAULT_OUTPUT_SCOPE) -> Any:
    if not _is_safe_display_string(key, value, output_scope):
        if _is_real_name_key(key):
            return {"name_present": True}
        if _is_id_card_key(key) and _looks_like_id_card(value):
            return _id_card_summary(value, output_scope)
        return "<redacted>"
    if _is_phone_key(key) and _looks_like_phone(value):
        return _mask_phone(value, output_scope)
    if _is_id_card_key(key) and _looks_like_id_card(value):
        return _id_card_summary(value, output_scope)
    if _is_real_name_key(key):
        return {"name_present": True}
    if _is_risk_entity_key(key):
        return value[:160] if output_scope == "internal_risk_review" else _mask_risk_entity(key, value)
    if _looks_like_phone(value) or _looks_like_id_card(value) or _looks_like_credential_secret(value):
        return "<redacted>"
    return value[:160]


def _sanitize_display_material(value: Any, output_scope: str = DEFAULT_OUTPUT_SCOPE, key: str = "") -> Any:
    if isinstance(value, Mapping):
        result: Dict[str, Any] = {}
        for nested_key, nested_value in value.items():
            nested_key_text = str(nested_key)
            if not _is_safe_display_key(nested_key_text):
                continue
            result[nested_key_text] = _sanitize_display_material(nested_value, output_scope, nested_key_text)
        return result
    if isinstance(value, list):
        return [_sanitize_display_material(item, output_scope, key) for item in value[:50]]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return _safe_display_value(key or "value", value, output_scope)
    return str(type(value).__name__)


def _safe_shape_keys(value: Mapping[str, Any]) -> list[str]:
    return [str(key) for key in value.keys() if _is_safe_display_key(str(key))][:16]


def _coerce_output_scope(scope: Any) -> str:
    return str(scope) if isinstance(scope, str) and scope in OUTPUT_SCOPES else DEFAULT_OUTPUT_SCOPE


def _field_classification_summary() -> Dict[str, list[str]]:
    return {key: list(values) for key, values in FIELD_CLASSIFICATION.items()}


def _is_credential_secret_key(key: str) -> bool:
    lowered = key.lower()
    if "tokenid" in lowered or "token_id" in lowered:
        return False
    return any(
        marker in lowered
        for marker in (
            "cookie",
            "authorization",
            "password",
            "credential",
            "secret",
            "session",
            "header",
            "accesstoken",
            "access_token",
            "refreshtoken",
            "refresh_token",
            "jwt",
            "csrf",
        )
    ) or lowered == "token"


def _looks_like_credential_secret(value: str) -> bool:
    text = str(value)
    return bool(re.search(r"(authorization|cookie|token|session|password|credential|secret)\s*[:=]\s*\S+", text, re.I))


def _is_risk_entity_key(key: str) -> bool:
    lowered = key.lower()
    if _is_credential_secret_key(key):
        return False
    if lowered.endswith("_count") or lowered.endswith("_present") or lowered in {"count", "records_count", "event_count"}:
        return False
    return bool(
        re.search(
            r"(user_?ids?|^uid$|device_?ids?|deviceid|device_did|^did$|(^|_)ip($|_)|ipaddr|ipdesc|clientip|remoteip|loginip|event_?id|source_?id|photo_?id|live_?id|livestreamid|hitfusepolicycode|strategy|logsource|method|timestamp|occur_?time|_occurtime)",
            lowered,
            re.I,
        )
    )


def _is_phone_key(key: str) -> bool:
    return bool(re.search(r"(phone|mobile|手机号|手机|电话号码|phone_number)", str(key), re.I))


def _looks_like_phone(value: str) -> bool:
    return bool(re.fullmatch(r"1\d{10}", re.sub(r"\D", "", str(value))))


def _looks_like_internal_phone_mask(value: str) -> bool:
    return bool(re.fullmatch(r"1\d{6}\*{4}", str(value)))


def _mask_phone(value: str, output_scope: str) -> str:
    digits = re.sub(r"\D", "", str(value))
    return f"{digits[:3]}********" if output_scope == "external_share" else f"{digits[:7]}****"


def _is_id_card_key(key: str) -> bool:
    return bool(re.search(r"(id.?card|identity|身份证|证件号|idno)", str(key), re.I))


def _looks_like_id_card(value: str) -> bool:
    return bool(re.fullmatch(r"\d{17}[\dXx]", str(value)))


def _id_card_summary(value: str, output_scope: str) -> Dict[str, Any]:
    result: Dict[str, Any] = {"id_card_present": True}
    if output_scope == "internal_risk_review":
        result["birth_year_present"] = bool(re.fullmatch(r"\d{6}\d{4}\d{7}[\dXx]", str(value)))
    return result


def _is_real_name_key(key: str) -> bool:
    return bool(re.search(r"(^name$|real.?name|姓名|真实姓名)", str(key), re.I))


def _mask_risk_entity(key: str, value: str) -> str:
    text = str(value)
    lowered = str(key).lower()
    if "ip" in lowered or re.fullmatch(r"\d{1,3}(?:\.\d{1,3}){3}", text):
        parts = text.split(".")
        return f"{parts[0]}.{parts[1]}.*.*" if len(parts) == 4 else "[masked_ip]"
    if "device" in lowered or "did" in lowered or text.startswith(("ANDROID_", "IOS_")):
        return f"[masked_device_id:length={len(text)}]"
    if "user" in lowered or lowered == "uid":
        return f"[masked_user_id:length={len(text)}]"
    return f"[masked_identifier:length={len(text)}]"


def _external_user_id_label(user_id: str) -> str:
    text = str(user_id)
    return f"user_***{text[-4:]}" if len(text) >= 4 else "user_***"


def _small_batch_user_title(user_id: str, index: int, output_scope: str) -> str:
    if output_scope == "internal_risk_review":
        return f"用户 {user_id}"
    return f"用户 U{index}（{_external_user_id_label(user_id)}）"


def _is_masked_placeholder(value: str) -> bool:
    return bool(re.fullmatch(r"\[masked_[a-z_]+:length=\d+\]", str(value)))


def _base_source_summary(result: Mapping[str, Any], evidence_type: str, output_scope: str) -> Dict[str, Any]:
    return {
        "evidence_type": evidence_type,
        "source_name": result.get("source_name"),
        "action_name": result.get("action_name"),
        "source_status": result.get("source_status"),
        "error_type": result.get("error_type"),
        "latency_ms": result.get("latency_ms"),
        "output_scope": output_scope,
        "field_classification": _field_classification_summary(),
        "source_card_exists": result.get("source_card") is not None,
        "source_quality_exists": result.get("source_quality") is not None,
        "sensitive_output": False,
        "raw_body_suppressed": True,
        "raw_records_full_dump_suppressed": True,
        "credential_secret_plaintext_suppressed": True,
        "no_data_not_risk_exclusion": bool(result.get("no_data_not_risk_exclusion")),
    }


def _track_analysis_summary(result: Mapping[str, Any], output_scope: str) -> Dict[str, Any]:
    material = _summary_material(result, output_scope)
    summary = _base_source_summary(result, "track_analysis", output_scope)
    summary["bundle_summary"] = _pick_fields(
        material,
        (
            "mode",
            "sub_interface",
            "sub_interfaces",
            "sub_interfaces_completed",
            "sub_interfaces_missing",
            "account_security_bundle",
        ),
        output_scope,
    )
    summary["profile_summary"] = _pick_fields(
        material,
        (
            "register_time_present",
            "fan_distribution_present",
            "active_days_bucket_present",
            "device_ids_count",
        ),
        output_scope,
    )
    summary["latest_timestamp_summary"] = _pick_fields(
        material,
        (
            "latest_datetime_present",
            "uid_did_relation_latest_datetime_present",
        ),
        output_scope,
    )
    summary["use_duration_summary"] = _pick_fields(
        material,
        ("rows_count", "nonzero_days_count", "total_duration", "peak_date"),
        output_scope,
    )
    summary["device_ids_summary"] = _pick_fields(
        material,
        ("device_ids_count", "device_id_sample", "device_id_sample_masked", "device_model_fields_present", "last_active_fields_present"),
        output_scope,
    )
    return summary


def _rcp_summary(result: Mapping[str, Any], output_scope: str) -> Dict[str, Any]:
    material = _summary_material(result, output_scope)
    summary = _base_source_summary(result, "rcp_snapshot", output_scope)
    summary["event_summary"] = _pick_fields(
        material,
        (
            "event_count",
            "table_header_columns",
            "returned_columns_observed",
            "first_event_shape_keys",
            "dynamic_columns_observed",
        ),
        output_scope,
    )
    summary["first_event_entity_samples"] = _pick_fields(material, ("first_event_entity_samples",), output_scope).get(
        "first_event_entity_samples",
        {},
    )
    summary["chaining_keys_present"] = {
        "hitFusePolicyCode": _find_first(material, ("hitFusePolicyCode_present", "hitFusePolicyCode"), output_scope) is not None,
        "eventId": _find_first(material, ("eventId_present", "eventId"), output_scope) is not None,
        "_occurTime": _find_first(material, ("_occurTime_present", "_occurTime"), output_scope) is not None,
    }
    summary["boundary"] = "RCP is a strategy event entry source, not a final risk judgement."
    return summary


def _weapon_summary(result: Mapping[str, Any], output_scope: str) -> Dict[str, Any]:
    material = _summary_material(result, output_scope)
    summary = _base_source_summary(result, "weapon_inventory", output_scope)
    summary["graph_summary"] = _pick_fields(
        material,
        ("graph_status", "related_device_count", "related_user_count", "related_device_id_sample", "related_user_id_sample"),
        output_scope,
    )
    summary["risk_summary"] = _pick_fields(
        material,
        (
            "riskData_status",
            "risk_label_count",
            "risk_group_names_observed",
            "readable_label_sample",
            "userLevel_observed",
        ),
        output_scope,
    )
    summary["original_log_summary"] = _pick_fields(
        material,
        ("originalLog_key_summary", "originalLog_eventId_sample"),
        output_scope,
    )
    summary["raw_weapon_fields_suppressed"] = ["raw labelInfo full dump", "raw originalLog full dump"]
    summary["chaining_summary"] = {
        "raw_device_safe_handle_retained": _has_private_raw_reference(result, "device_id"),
        "riskData_chaining_uses_safe_handle_only": True,
        "raw_device_id_suppressed_from_display": True,
    }
    return summary


def _login_logs_summary(result: Mapping[str, Any], output_scope: str) -> Dict[str, Any]:
    material = _summary_material(result, output_scope)
    summary = _base_source_summary(result, "login_logs", output_scope)
    summary["login_window_summary"] = _pick_fields(
        material,
        (
            "records_count",
            "time_window_observed",
            "first_login_time_observed",
            "last_login_time_observed",
            "ip_sample",
            "device_id_sample",
            "user_id_sample",
            "method_sample",
            "logSource_sample",
            "phone_number_sample",
        ),
        output_scope,
    )
    summary["login_window_summary"]["source_status"] = result.get("source_status")
    summary["login_window_summary"]["error_type"] = result.get("error_type")
    summary["login_window_summary"]["standard_browser_backed_source_result"] = (
        result.get("source_card") is not None
        and result.get("source_quality") is not None
        and result.get("latency_ms") is not None
        and result.get("sensitive_output") is False
    )
    summary["pii_strict_summary"] = _pick_fields(
        material,
        ("phone_number_sample", "id_card", "id_card_present", "birth_year_present", "real_name", "name_present"),
        output_scope,
    )
    if "records_count" not in summary["login_window_summary"] and result.get("source_status") == "no_data":
        summary["login_window_summary"]["records_count"] = 0
    summary["no_data_not_risk_exclusion"] = True
    summary["blocked_parse_or_no_data_not_counter_evidence"] = result.get("source_status") in {"blocked", "parse_error", "no_data"}
    summary["caveat"] = "no_data / blocked / parse_error are source-quality states; they are not no-risk evidence."
    return summary


def _archives_user_analysis_summary(result: Mapping[str, Any], output_scope: str) -> Dict[str, Any]:
    material = _summary_material(result, output_scope)
    summary = _base_source_summary(result, "archives_user_analysis", output_scope)
    summary["action_contract"] = {
        "fixed_path": ARCHIVES_USER_ANALYSIS_FIXED_PATH,
        "same_origin_service_owned": True,
        "raw_full_body_suppressed": True,
        "requestParam_extraParam_suppressed": True,
    }
    summary["risk_event_scan"] = _pick_fields(
        material,
        (
            "total_records_visible",
            "records_count",
            "dataList_length",
            "operation_type_counts",
            "success_failure_counts",
            "earliest_event_time",
            "latest_event_time",
            "login_method_sequence",
            "ip_consistency",
            "device_consistency",
            "app_version_consistency",
            "geo_consistency",
            "suspicious_event_markers",
            "pagination_required",
            "coverage_limitations",
        ),
        output_scope,
    )
    summary["key_entities"] = _pick_fields(
        material,
        ("user_id", "userId", "deviceId", "device_id_sample", "ip", "userIpDesc", "photo_id", "photoId"),
        output_scope,
    )
    summary["missing_fields"] = _pick_fields(
        material,
        ("missing_fields", "fields_missing", "required_fields_missing"),
        output_scope,
    ).get("missing_fields", [])
    summary["next_action"] = _find_first(material, ("next_action",), output_scope) or (
        "Use Archives Center user analysis as account-side observation; cross-check login logs/Weapon/RCP before judgement."
    )
    summary["boundary"] = (
        "Archives user analysis is a P0 account-side observation source; no_data/empty_result is not no-risk evidence "
        "and raw requestParam/extraParam/full response are never displayed."
    )
    return summary


def _generic_summary(result: Mapping[str, Any], output_scope: str) -> Dict[str, Any]:
    summary = _base_source_summary(result, "generic_browser_backed_source", output_scope)
    summary["summary"] = "source result normalized; raw body suppressed"
    return summary


def _validate_local_base_url(base_url: str) -> str:
    parsed = urllib.parse.urlparse(base_url)
    if parsed.scheme != "http":
        raise BrowserBackedServiceInputError("browser-backed service base_url must use local http")
    if parsed.hostname not in {"127.0.0.1", "localhost"}:
        raise BrowserBackedServiceInputError("browser-backed service base_url must be local only")
    if parsed.port != 8787:
        raise BrowserBackedServiceInputError("browser-backed service base_url must use port 8787")
    if parsed.path not in {"", "/"} or parsed.params or parsed.query or parsed.fragment:
        raise BrowserBackedServiceInputError("browser-backed service base_url must not include a path or query")
    return f"{parsed.scheme}://{parsed.netloc}".rstrip("/")


def _validate_action_name(action_name: str) -> None:
    if action_name not in ACTION_ENDPOINTS:
        raise BrowserBackedServiceInputError(f"browser-backed action is not allowlisted: {action_name}")


def _validate_typed_params(value: Any, path: str = "$") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            normalized_key = str(key).strip().lower()
            if normalized_key in FORBIDDEN_INPUT_KEYS:
                raise BrowserBackedServiceInputError(f"forbidden browser-backed input key at {path}.{key}")
            _validate_typed_params(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _validate_typed_params(child, f"{path}[{index}]")
    elif isinstance(value, str) and ("http://" in value.lower() or "https://" in value.lower()):
        raise BrowserBackedServiceInputError(f"forbidden browser-backed URL-like input at {path}")


def _classify_url_error(exc: urllib.error.URLError) -> str:
    reason = exc.reason
    if isinstance(reason, ConnectionRefusedError):
        return "connection_refused"
    if isinstance(reason, OSError) and reason.errno == errno.ECONNREFUSED:
        return "connection_refused"
    if "connection refused" in str(reason).lower():
        return "connection_refused"
    if isinstance(reason, socket.timeout):
        return "service_timeout"
    return "service_unavailable"


def _transport_result(
    action_name: str,
    source_status: str,
    error_type: str,
    failure_layer: str,
    started_at: float,
    http_status: Optional[int] = None,
    detail: Optional[str] = None,
) -> Dict[str, Any]:
    normalized_status, normalized_failure_layer = _normalize_status(source_status, error_type)
    return {
        "source_name": ACTION_TO_SOURCE[action_name],
        "action_name": action_name,
        "source_status": normalized_status,
        "failure_layer": failure_layer or normalized_failure_layer,
        "error_type": error_type,
        "http_status": http_status,
        "latency_ms": int((time.monotonic() - started_at) * 1000),
        "output_scope": DEFAULT_OUTPUT_SCOPE,
        "field_classification": _field_classification_summary(),
        "source_card": _synthetic_source_card(action_name, normalized_status, error_type),
        "source_quality": _synthetic_source_quality(normalized_status, error_type, detail=detail),
        "sensitive_output": False,
        "source_provenance": "browser_backed_service",
        "no_data_not_risk_exclusion": False,
    }


def _coerce_status(payload: Mapping[str, Any]) -> str:
    for key in ("source_status", "status"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    return "blocked"


def _normalize_status(raw_status: str, error_type: Optional[Any]) -> tuple[str, str]:
    status = str(raw_status or "").strip().lower()
    error = str(error_type or "").strip().lower()

    if status in COMPLETED_STATUSES:
        return "completed", "no_failure"
    if status in NO_DATA_STATUSES:
        return "no_data", "source_observation"
    if status in AUTH_FAILED_STATUSES or error == "auth_redirect":
        return "auth_failed", "auth_session"
    if status in TIMEOUT_STATUSES or error in {"timeout", "service_timeout"}:
        return "timeout", "service_transport"
    if status in PARSE_ERROR_STATUSES:
        return "parse_error", "parser"
    if status in INVALID_PARAMETER_STATUSES or error in {"invalid_parameter", "wrong_request_body_shape"}:
        return "invalid_parameter", "parameter_contract"
    if status in BLOCKED_STATUSES or error in {"network_error", "platform_error", "connection_refused"}:
        return "blocked", "source_or_service"
    return "blocked", "source_or_service"


def _extract_no_data_marker(source_quality: Any, normalized_status: str) -> bool:
    if normalized_status == "no_data":
        return True
    if isinstance(source_quality, Mapping):
        return bool(source_quality.get("no_data_not_risk_exclusion"))
    return False


def _safe_nested_get(payload: Mapping[str, Any], keys: Iterable[str]) -> Any:
    current: Any = payload
    for key in keys:
        if not isinstance(current, Mapping):
            return None
        current = current.get(key)
    return current


def _sanitize_source_checkpoint_private(payload: Mapping[str, Any]) -> Dict[str, Any]:
    """Keep only safe private chaining handles from a service payload.

    Raw reference values are not copied into the normalized result. The service
    may provide `raw_reference_safe_id` handles that are valid for current-task
    source chaining; those handles are preserved in the private checkpoint.
    """

    checkpoint = payload.get("source_checkpoint_private") or _safe_nested_get(payload, ("data", "source_checkpoint_private"))
    if not isinstance(checkpoint, Mapping):
        return {"raw_references": [], "downstream_source_chaining": []}

    raw_references = []
    for ref in checkpoint.get("raw_references", []) if isinstance(checkpoint.get("raw_references"), list) else []:
        if not isinstance(ref, Mapping):
            continue
        ref_type = str(ref.get("ref_type") or "")
        safe_id = ref.get("raw_reference_safe_id")
        if not ref_type or not safe_id:
            continue
        raw_references.append(
            {
                "ref_type": ref_type,
                "raw_reference_safe_id": safe_id,
                "alias": ref.get("alias"),
                "masked_value": ref.get("masked_value"),
                "allowed_downstream_sources": list(ref.get("allowed_downstream_sources") or []),
                "retention_scope": ref.get("retention_scope", "current_task_only"),
            }
        )

    raw_device_handles = checkpoint.get("raw_device_ids_for_chaining")
    if isinstance(raw_device_handles, list):
        for index, handle in enumerate(raw_device_handles):
            if not isinstance(handle, Mapping):
                continue
            safe_id = handle.get("raw_reference_safe_id")
            if not safe_id:
                continue
            raw_references.append(
                {
                    "ref_type": "device_id",
                    "raw_reference_safe_id": safe_id,
                    "alias": handle.get("alias") or f"device_ref_{index + 1}",
                    "masked_value": handle.get("masked_value"),
                    "allowed_downstream_sources": list(handle.get("allowed_downstream_sources") or ["weapon_device_risk_if_device_id_available"]),
                    "retention_scope": handle.get("retention_scope", "current_task_only"),
                }
            )

    downstream = checkpoint.get("downstream_source_chaining")
    return {
        "raw_references": raw_references,
        "downstream_source_chaining": downstream if isinstance(downstream, list) else [],
    }


def _synthetic_source_card(action_name: str, source_status: str, error_type: Optional[str]) -> Dict[str, Any]:
    return {
        "source_name": ACTION_TO_SOURCE[action_name],
        "action_name": action_name,
        "source_status": source_status,
        "error_type": error_type,
        "source_provenance": "browser_backed_service",
        "body_policy": {
            "raw_response_full_body_returned": False,
            "credential_secret_plaintext_returned": False,
            "raw_records_full_dump_returned": False,
            "raw_labelInfo_full_dump_returned": False,
            "raw_originalLog_full_dump_returned": False,
            "sensitive_output": False,
        },
        "output_scope": DEFAULT_OUTPUT_SCOPE,
        "field_classification": _field_classification_summary(),
    }


def _synthetic_source_quality(source_status: str, error_type: Optional[str], detail: Optional[str] = None) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "source_status": source_status,
        "error_type": error_type,
        "quality_status": "source_unavailable" if source_status != "completed" else "usable",
        "no_data_not_risk_exclusion": source_status == "no_data",
        "source_status_not_risk_exclusion": source_status != "completed",
        "redaction_applied": True,
        "raw_reference_retained_for_followup": False,
        "sensitive_output": False,
        "output_scope": DEFAULT_OUTPUT_SCOPE,
        "field_classification": _field_classification_summary(),
    }
    if detail:
        result["sanitized_detail"] = detail[:160]
    return result


class _FakeResponse:
    def __init__(self, http_status: int, payload: Mapping[str, Any]) -> None:
        self.http_status = http_status
        self.payload = payload

    def getcode(self) -> int:
        return self.http_status

    def read(self) -> bytes:
        return json.dumps(self.payload, ensure_ascii=True).encode("utf-8")

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        return None


class _FakeOpener:
    def __init__(self, payload: Optional[Mapping[str, Any]] = None, exc: Optional[BaseException] = None) -> None:
        self.payload = payload
        self.exc = exc
        self.calls = []

    def open(self, request: urllib.request.Request, timeout: int) -> _FakeResponse:
        self.calls.append({"url": request.full_url, "timeout": timeout, "body": request.data})
        if self.exc:
            raise self.exc
        payload = self.payload(request) if callable(self.payload) else self.payload
        return _FakeResponse(200, payload or {})


def _fixture_payload(
    action_name: str,
    source_status: str,
    error_type: Optional[str] = None,
    *,
    track_sub_interface: Optional[str] = None,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "action": action_name,
        "status": source_status,
        "source_status": source_status,
        "error_type": error_type,
        "latency_ms": 123,
        "output_scope": DEFAULT_OUTPUT_SCOPE,
        "field_classification": _field_classification_summary(),
        "source_card": {
            "source_name": ACTION_TO_SOURCE[action_name],
            "action_name": action_name,
            "source_status": source_status,
            "output_scope": DEFAULT_OUTPUT_SCOPE,
            "field_classification": _field_classification_summary(),
            "body_policy": {
                "raw_response_full_body_returned": False,
                "credential_secret_plaintext_returned": False,
                "raw_records_full_dump_returned": False,
                "raw_labelInfo_full_dump_returned": False,
                "raw_originalLog_full_dump_returned": False,
                "sensitive_output": False,
            },
        },
        "source_quality": {
            "source_status": source_status,
            "error_type": error_type,
            "output_scope": DEFAULT_OUTPUT_SCOPE,
            "field_classification": _field_classification_summary(),
            "no_data_not_risk_exclusion": source_status in NO_DATA_STATUSES,
            "sensitive_output_false_meaning": "no credential_secret/raw dumps; risk entities allowed in internal review",
        },
        "sensitive_output": False,
        "data": {
            "response_summary": {
                "shape_only": True,
                "raw_response_full_body_returned": False,
            }
        },
    }
    source_card = payload["source_card"]
    if action_name == "track_analysis_summary":
        source_card["bundle_summary"] = {
            "mode": TRACK_ANALYSIS_BUNDLE_MODE,
            "sub_interfaces": list(ACCOUNT_SECURITY_TRACK_SUB_INTERFACES),
            "sub_interfaces_completed": [track_sub_interface] if track_sub_interface else list(ACCOUNT_SECURITY_TRACK_SUB_INTERFACES),
            "sub_interfaces_missing": [
                item for item in ACCOUNT_SECURITY_TRACK_SUB_INTERFACES if track_sub_interface and item != track_sub_interface
            ],
            "account_security_bundle": True,
        }
        payload["data"]["response_summary"]["track_analysis"] = {
            "sub_interface": track_sub_interface or "account_security_bundle",
            "appName": "KUAISHOU",
            "no_data_not_risk_exclusion": True,
        }
        if track_sub_interface in {None, "profile"}:
            source_card["profile_summary"] = {
                "register_time_present": True,
                "fan_distribution_present": True,
                "active_days_bucket_present": True,
                "device_ids_count": 2,
                "user_id_sample": "2871834924",
            }
        if track_sub_interface in {None, "getLastestDateTime"}:
            source_card["latest_timestamp_summary"] = {
                "latest_datetime_present": True,
                "uid_did_relation_latest_datetime_present": True,
            }
        if track_sub_interface in {None, "getUseDuration"}:
            source_card["getUseDuration"] = {
                "rows_count": 7,
                "nonzero_days_count": 5,
                "total_duration": 32400,
                "peak_date": "2026-05-28",
            }
        if track_sub_interface in {None, "getDeviceIds"}:
            source_card["getDeviceIds"] = {
                "device_ids_count": 2,
                "device_id_sample": "ANDROID_track_device_001",
                "deviceIds": ["ANDROID_track_device_001", "IOS_track_device_002"],
                "device_model_fields_present": True,
                "last_active_fields_present": True,
            }
    elif action_name == "rcp_snapshot":
        source_card["event_summary"] = {
            "event_count": 3,
            "table_header_columns": ["eventId", "_occurTime", "hitFusePolicyCode"],
            "returned_columns_observed": ["eventId", "_occurTime", "hitFusePolicyCode"],
            "first_event_shape_keys": ["eventId", "_occurTime", "hitFusePolicyCode"],
            "dynamic_columns_observed": ["hitFusePolicyCode"],
            "first_event_entity_samples": {
                "eventId": "evt_rcp_001",
                "sourceId": "src_rcp_001",
                "deviceId": "ANDROID_rcp_device_001",
                "hitFusePolicyCode": "BS_fake_account_register",
                "_occurTime": "2026-05-29 10:00:00",
            },
            "hitFusePolicyCode_present": True,
            "eventId_present": True,
            "_occurTime_present": True,
        }
    elif action_name == "weapon_inventory":
        source_card["weapon_summary"] = {
            "graph_status": "completed",
            "related_device_count": 2,
            "related_user_count": 4,
            "related_device_id_sample": "ANDROID_weapon_device_001",
            "related_user_id_sample": "2871834924",
            "riskData_status": "completed",
            "risk_label_count": 2,
            "risk_group_names_observed": ["account_risk", "device_risk"],
            "readable_label_sample": ["risk_label_sample"],
            "userLevel_observed": True,
            "originalLog_eventId_sample": "evt_weapon_001",
            "raw_labelInfo": {"deviceId": "raw_device_should_not_render", "originalLog": "raw_log_should_not_render"},
        }
        payload["source_checkpoint_private"] = {
            "raw_references": [
                {
                    "ref_type": "device_id",
                    "raw_reference_safe_id": "device_safe_handle_001",
                    "alias": "device_ref_1",
                    "masked_value": "ANDROID_***9999",
                    "allowed_downstream_sources": ["weapon_device_risk_if_device_id_available"],
                    "retention_scope": "current_task_only",
                    "raw_value": "ANDROID_raw_device_should_not_render",
                }
            ],
            "raw_device_ids_for_chaining": [
                {
                    "raw_reference_safe_id": "device_safe_handle_001",
                    "alias": "device_ref_1",
                    "masked_value": "ANDROID_***9999",
                    "allowed_downstream_sources": ["weapon_device_risk_if_device_id_available"],
                    "raw_value": "ANDROID_raw_device_should_not_render",
                }
            ],
            "downstream_source_chaining": ["weapon_device_risk_if_device_id_available"],
        }
    elif action_name == "login_logs_search":
        source_card["login_logs_summary"] = {
            "records_count": 0 if source_status in NO_DATA_STATUSES else 2,
            "time_window_observed": "visible_window",
            "first_login_time_observed": None,
            "last_login_time_observed": None,
            "ip_sample": "10.20.30.40",
            "device_id_sample": "ANDROID_login_device_001",
            "user_id_sample": "2871834924",
            "method_sample": "PASSWORD",
            "logSource_sample": "account_login",
            "phone_number_sample": "13812345678",
            "id_card": "110105199001011234",
            "real_name": "Fixture User",
        }
    elif action_name == "archives_user_analysis":
        source_card["archives_user_analysis_summary"] = {
            "fixed_path": ARCHIVES_USER_ANALYSIS_FIXED_PATH,
            "records_count": 3,
            "total_records_visible": 3,
            "dataList_length": 3,
            "operation_type_counts": {"loginStart": 2, "scanCode": 1},
            "success_failure_counts": {"success": 2, "failed": 1},
            "earliest_event_time": "2026-05-28 09:00:00",
            "latest_event_time": "2026-05-28 11:00:00",
            "login_method_sequence": ["loginStart", "scanCode"],
            "ip_consistency": "mixed",
            "device_consistency": "single_device",
            "app_version_consistency": "stable",
            "geo_consistency": "mixed_city",
            "suspicious_event_markers": ["scanCode_after_loginStart"],
            "pagination_required": False,
            "coverage_limitations": ["archives_user_analysis_is_not_unified_login_log"],
            "userId": "2871834924",
            "deviceId": "ANDROID_archives_device_001",
            "userIpDesc": "10.20.30.40",
            "requestParam": "token=raw_token_should_not_render&open_id=raw_open_id_should_not_render",
            "extraParam": "refresh_token=raw_refresh_token_should_not_render",
        }
        source_card["key_entities"] = {
            "user_id": "2871834924",
            "deviceId": "ANDROID_archives_device_001",
            "ip": "10.20.30.40",
            "photo_id": "photo_123456",
        }
        source_card["missing_fields"] = ["unified_login_full_window"]
        source_card["next_action"] = "Cross-check with login logs and Weapon before judgement."
        payload["key_entities"] = dict(source_card["key_entities"])
        payload["missing_fields"] = list(source_card["missing_fields"])
        payload["next_action"] = source_card["next_action"]
        payload["source_quality"].update(
            {
                "no_data_not_risk_exclusion": True,
                "archives_action_contract": "archives_user_analysis",
                "fixed_path": ARCHIVES_USER_ANALYSIS_FIXED_PATH,
                "requestParam_extraParam_suppressed": True,
                "raw_response_full_body_returned": False,
            }
        )
    return payload


def run_fixture_tests() -> Dict[str, Any]:
    results = []

    for action_name in ("track_analysis_summary", "rcp_snapshot", "weapon_inventory"):
        client = BrowserBackedServiceClient(opener=_FakeOpener(_fixture_payload(action_name, "completed")))
        result = client.call_action(action_name, {"user_id": "fixture"})
        assert result["source_status"] == "completed"
        assert result["source_card"] and result["source_quality"]
        results.append((f"{action_name}_completed", "passed"))

    client = BrowserBackedServiceClient(opener=_FakeOpener(_fixture_payload("login_logs_search", "no_data")))
    result = client.call_action("login_logs_search", {"user_id": "fixture"})
    assert result["source_status"] == "no_data"
    assert result["no_data_not_risk_exclusion"] is True
    results.append(("login_logs_search_no_data", "passed"))

    archives_plan = build_archives_user_analysis_browser_backed_request(
        "2871834924",
        begin_time_ms=1764201600000,
        end_time_ms=1764288000000,
    )
    assert archives_plan["action_name"] == "archives_user_analysis"
    assert archives_plan["fixed_path"] == ARCHIVES_USER_ANALYSIS_FIXED_PATH
    assert archives_plan["typed_params"]["user_id"] == "2871834924"
    assert archives_plan["typed_params"]["pageIndex"] == 1
    assert archives_plan["typed_params"]["pageSize"] == 30
    assert archives_plan["typed_params"]["operation_filters"] == {
        field: 1 for field in ARCHIVES_USER_ANALYSIS_FILTER_FIELDS
    }
    serialized_archives_plan = json.dumps(archives_plan, ensure_ascii=True)
    assert "cookie" not in serialized_archives_plan.lower()
    assert "token" not in serialized_archives_plan.lower()
    assert "session" not in serialized_archives_plan.lower()
    assert "/v3/user/log/coreLogs/fetch" in serialized_archives_plan
    assert "http://" not in serialized_archives_plan.lower()
    assert "https://" not in serialized_archives_plan.lower()
    results.append(("archives_user_analysis_typed_request_plan", "passed"))

    archives_opener = _FakeOpener(_fixture_payload("archives_user_analysis", "completed"))
    client = BrowserBackedServiceClient(opener=archives_opener)
    archives_result = client.call_action("archives_user_analysis", archives_plan["typed_params"])
    assert archives_opener.calls[0]["url"].endswith(ACTION_ENDPOINTS["archives_user_analysis"])
    assert archives_result["source_status"] == "completed"
    assert archives_result["source_card"] and archives_result["source_quality"]
    assert archives_result["key_entities"]["user_id"] == "2871834924"
    assert archives_result["missing_fields"] == ["unified_login_full_window"]
    assert archives_result["next_action"] == "Cross-check with login logs and Weapon before judgement."
    assert archives_result["sensitive_output"] is False
    assert archives_result["no_data_not_risk_exclusion"] is True
    archives_card = build_partial_evidence_card([archives_result])
    archives_summary = archives_card["evidence_summary_by_source"]["archives_user_analysis"]
    assert archives_summary["action_contract"]["fixed_path"] == ARCHIVES_USER_ANALYSIS_FIXED_PATH
    assert archives_summary["risk_event_scan"]["total_records_visible"] == 3
    assert archives_summary["key_entities"]["deviceId"] == "ANDROID_archives_device_001"
    archives_text = json.dumps(archives_card, ensure_ascii=True)
    assert "raw_token_should_not_render" not in archives_text
    assert "raw_open_id_should_not_render" not in archives_text
    assert "raw_refresh_token_should_not_render" not in archives_text
    assert '"requestParam":' not in archives_text
    assert '"extraParam":' not in archives_text
    assert archives_card["sensitive_output"] is False
    results.append(("archives_user_analysis_standard_source_result", "passed"))

    blocked_payload = _fixture_payload("rcp_snapshot", "blocked", "platform_error")
    client = BrowserBackedServiceClient(opener=_FakeOpener(blocked_payload))
    result = client.call_action("rcp_snapshot", {"eventType": "USER_REGISTER_NEW"})
    assert result["source_status"] == "blocked"
    assert result["source_card"] and result["source_quality"]
    results.append(("blocked_platform_error_standardized", "passed"))

    refused = urllib.error.URLError(ConnectionRefusedError("connection refused"))
    client = BrowserBackedServiceClient(opener=_FakeOpener(exc=refused))
    result = client.call_action("weapon_inventory", {"user_id": "fixture"})
    assert result["source_status"] == "blocked"
    assert result["error_type"] == "connection_refused"
    results.append(("service_connection_refused", "passed"))

    client = BrowserBackedServiceClient(opener=_FakeOpener(exc=socket.timeout("timed out")))
    result = client.call_action("track_analysis_summary", {"user_id": "fixture"})
    assert result["source_status"] == "timeout"
    results.append(("service_timeout", "passed"))

    sensitive_payload = _fixture_payload("weapon_inventory", "completed")
    sensitive_payload["sensitive_output"] = True
    client = BrowserBackedServiceClient(opener=_FakeOpener(sensitive_payload))
    result = client.call_action("weapon_inventory", {"user_id": "fixture"})
    assert result["source_status"] == "blocked"
    assert result["error_type"] == "sensitive_output_violation"
    assert result["sensitive_output"] is False
    results.append(("sensitive_output_true_rejected", "passed"))

    try:
        BrowserBackedServiceClient().call_action("arbitrary_action", {})
        raise AssertionError("arbitrary action was not rejected")
    except BrowserBackedServiceInputError:
        results.append(("arbitrary_action_rejected", "passed"))

    for forbidden_key in ("header", "cookie", "token", "session", "secret"):
        try:
            BrowserBackedServiceClient(opener=_FakeOpener(_fixture_payload("rcp_snapshot", "completed"))).call_action(
                "rcp_snapshot", {forbidden_key: "fixture"}
            )
            raise AssertionError(f"forbidden key was not rejected: {forbidden_key}")
        except BrowserBackedServiceInputError:
            continue
    results.append(("forbidden_auth_material_keys_rejected", "passed"))

    try:
        BrowserBackedServiceClient(base_url="https://example.invalid:8787")
        raise AssertionError("non-local base_url was not rejected")
    except BrowserBackedServiceInputError:
        results.append(("arbitrary_base_url_rejected", "passed"))

    try:
        BrowserBackedServiceClient(opener=_FakeOpener(_fixture_payload("rcp_snapshot", "completed"))).call_action(
            "rcp_snapshot", {"typed_hint": "https://example.invalid/path"}
        )
        raise AssertionError("URL-like typed param was not rejected")
    except BrowserBackedServiceInputError:
        results.append(("url_like_typed_param_rejected", "passed"))

    account_security_source_plan = build_account_security_browser_backed_requests(
        "2871834924",
        expand_track_analysis_bundle=False,
    )
    assert [item["action_name"] for item in account_security_source_plan] == [
        "track_analysis_summary",
        "rcp_snapshot",
        "weapon_inventory",
        "login_logs_search",
    ]
    track_plan = account_security_source_plan[0]
    assert track_plan["typed_params"]["mode"] == "account_security_bundle"
    assert track_plan["typed_params"]["sub_interfaces"] == [
        "profile",
        "getUseDuration",
        "getDeviceIds",
        "getLastestDateTime",
    ]
    rcp_plan = account_security_source_plan[1]
    assert rcp_plan["typed_params"]["mode"] == "account_security_strategy_event_entry"
    weapon_plan = account_security_source_plan[2]
    assert weapon_plan["typed_params"]["riskData_trigger_device_prefix"] == ["ANDROID_", "IOS_"]
    login_plan = account_security_source_plan[3]
    assert login_plan["fallback_on"]["parse_error"]["typed_params"]["window"] == "last_24h"
    expanded_account_security_plan = build_account_security_browser_backed_requests("2871834924")
    assert [item.get("track_sub_interface") for item in expanded_account_security_plan[:4]] == [
        "profile",
        "getUseDuration",
        "getDeviceIds",
        "getLastestDateTime",
    ]
    assert [item["action_name"] for item in expanded_account_security_plan[:4]] == ["track_analysis_summary"] * 4
    serialized_plan = json.dumps(expanded_account_security_plan, ensure_ascii=True)
    assert "sso_session_runner" not in serialized_plan
    assert "track_analysis_runner" not in serialized_plan
    assert "cookie" not in serialized_plan.lower()
    assert "token" not in serialized_plan.lower()
    results.append(("account_security_browser_backed_request_plan", "passed"))

    def account_security_payload(request: urllib.request.Request) -> Dict[str, Any]:
        body = json.loads((request.data or b"{}").decode("utf-8"))
        if request.full_url.endswith(ACTION_ENDPOINTS["track_analysis_summary"]):
            return _fixture_payload("track_analysis_summary", "completed", track_sub_interface=body.get("sub_interface"))
        if request.full_url.endswith(ACTION_ENDPOINTS["rcp_snapshot"]):
            return _fixture_payload("rcp_snapshot", "completed")
        if request.full_url.endswith(ACTION_ENDPOINTS["weapon_inventory"]):
            return _fixture_payload("weapon_inventory", "completed")
        if request.full_url.endswith(ACTION_ENDPOINTS["login_logs_search"]):
            return _fixture_payload("login_logs_search", "no_data")
        return {}

    account_security_opener = _FakeOpener(account_security_payload)
    account_security_results = BrowserBackedServiceClient(opener=account_security_opener).call_account_security_sources("2871834924")
    assert len(account_security_opener.calls) == 7
    assert [result["source_name"] for result in account_security_results] == [
        "track_analysis_summary",
        "rcp_snapshot",
        "weapon_inventory",
        "login_logs_search",
    ]
    account_security_card = build_partial_evidence_card(account_security_results)
    track_summary = account_security_card["evidence_summary_by_source"]["track_analysis_summary"]
    assert track_summary["bundle_summary"]["sub_interfaces_completed"] == [
        "profile",
        "getUseDuration",
        "getDeviceIds",
        "getLastestDateTime",
    ]
    assert track_summary["profile_summary"]["register_time_present"] is True
    assert track_summary["use_duration_summary"]["rows_count"] == 7
    assert track_summary["device_ids_summary"]["device_ids_count"] == 2
    assert track_summary["latest_timestamp_summary"]["latest_datetime_present"] is True
    results.append(("ACCOUNT-SECURITY-TRACK-ANALYSIS-BUNDLE-EXPANDS-FOUR-SUBINTERFACES", "passed"))

    raw_payload = _fixture_payload("login_logs_search", "completed")
    raw_payload["data"]["login_records"] = [{"ip": "203.0.113.10", "deviceId": "ANDROID_raw"}]
    result = normalize_service_response("login_logs_search", raw_payload)
    serialized_result = json.dumps(result, ensure_ascii=True)
    assert "203.0.113.10" not in serialized_result
    assert "ANDROID_raw" not in serialized_result
    results.append(("raw_login_record_body_not_output", "passed"))

    internal_results = [
        normalize_service_response("track_analysis_summary", _fixture_payload("track_analysis_summary", "completed")),
        normalize_service_response("rcp_snapshot", _fixture_payload("rcp_snapshot", "completed")),
        normalize_service_response("weapon_inventory", _fixture_payload("weapon_inventory", "completed")),
        normalize_service_response("login_logs_search", _fixture_payload("login_logs_search", "completed")),
    ]
    internal_card = build_partial_evidence_card(internal_results)
    internal_text = json.dumps(internal_card, ensure_ascii=True)
    assert internal_card["output_scope"] == "internal_risk_review"
    assert "10.20.30.40" in internal_text
    assert "ANDROID_login_device_001" in internal_text
    assert "ANDROID_weapon_device_001" in internal_text
    assert "2871834924" in internal_text
    assert "evt_rcp_001" in internal_text
    assert "evt_weapon_001" in internal_text
    assert "src_rcp_001" in internal_text
    assert internal_card["evidence_boundary"]["sensitive_output_false_meaning"].startswith("no credential_secret")
    assert internal_card["sensitive_output"] is False
    assert "13812345678" not in internal_text
    assert "1381234****" in internal_text
    assert "110105199001011234" not in internal_text
    assert "Fixture User" not in internal_text
    assert "raw_device_should_not_render" not in internal_text
    assert "raw_log_should_not_render" not in internal_text
    results.append(("internal_risk_review_entity_fields_allowed", "passed"))

    external_card = build_partial_evidence_card(internal_results, output_scope="external_share")
    external_text = json.dumps(external_card, ensure_ascii=True)
    assert external_card["output_scope"] == "external_share"
    assert "10.20.30.40" not in external_text
    assert "10.20.*.*" in external_text
    assert "ANDROID_login_device_001" not in external_text
    assert "ANDROID_weapon_device_001" not in external_text
    assert "[masked_device_id:length=24]" in external_text
    assert "evt_rcp_001" not in external_text
    assert "evt_weapon_001" not in external_text
    assert "src_rcp_001" not in external_text
    assert "[masked_identifier:length=11]" in external_text
    assert "2871834924" not in external_text
    assert "[masked_user_id:length=10]" in external_text
    assert "13812345678" not in external_text
    assert "138********" in external_text
    assert "110105199001011234" not in external_text
    assert "Fixture User" not in external_text
    results.append(("external_share_risk_entities_masked", "passed"))

    def fixture_results_for_user(user_id: str) -> list[Dict[str, Any]]:
        track_payload = _fixture_payload("track_analysis_summary", "completed")
        track_payload["source_card"]["profile_summary"]["user_id_sample"] = user_id
        rcp_payload = _fixture_payload("rcp_snapshot", "completed")
        weapon_payload = _fixture_payload("weapon_inventory", "completed")
        weapon_payload["source_card"]["weapon_summary"]["related_user_id_sample"] = user_id
        login_payload = _fixture_payload("login_logs_search", "completed")
        login_payload["source_card"]["login_logs_summary"]["user_id_sample"] = user_id
        return [
            normalize_service_response("track_analysis_summary", track_payload),
            normalize_service_response("rcp_snapshot", rcp_payload),
            normalize_service_response("weapon_inventory", weapon_payload),
            normalize_service_response("login_logs_search", login_payload),
        ]

    small_batch_input = [
        {"user_id": "772671837", "results": fixture_results_for_user("772671837")},
        {"user_id": "3481089791", "results": fixture_results_for_user("3481089791")},
    ]
    internal_batch = build_small_batch_evidence_output(small_batch_input, output_scope="internal_risk_review")
    internal_batch_text = json.dumps(internal_batch, ensure_ascii=False)
    assert internal_batch["output_scope"] == "internal_risk_review"
    assert "用户 772671837" in internal_batch_text
    assert "用户 3481089791" in internal_batch_text
    assert "U1" not in internal_batch_text
    assert "U2" not in internal_batch_text
    assert "尾号" not in internal_batch_text
    assert "user_***1837" not in internal_batch_text
    assert "user_***9791" not in internal_batch_text
    assert "ANDROID_login_device_001" in internal_batch_text
    assert "ANDROID_weapon_device_001" in internal_batch_text
    assert "evt_rcp_001" in internal_batch_text
    assert "src_rcp_001" in internal_batch_text
    assert "10.20.30.40" in internal_batch_text
    results.append(("small_batch_internal_titles_show_raw_user_ids", "passed"))

    external_batch = build_small_batch_evidence_output(small_batch_input, output_scope="external_share")
    external_batch_text = json.dumps(external_batch, ensure_ascii=False)
    assert external_batch["output_scope"] == "external_share"
    assert "用户 U1（user_***1837）" in external_batch_text
    assert "用户 U2（user_***9791）" in external_batch_text
    assert "772671837" not in external_batch_text
    assert "3481089791" not in external_batch_text
    assert "ANDROID_login_device_001" not in external_batch_text
    assert "ANDROID_weapon_device_001" not in external_batch_text
    assert "evt_rcp_001" not in external_batch_text
    assert "src_rcp_001" not in external_batch_text
    assert "10.20.30.40" not in external_batch_text
    assert "10.20.*.*" in external_batch_text
    assert "13812345678" not in external_batch_text
    assert "138********" in external_batch_text
    assert "raw_device_should_not_render" not in external_batch_text
    assert "raw_log_should_not_render" not in external_batch_text
    results.append(("small_batch_external_titles_mask_user_ids", "passed"))

    numeric_user_payload = _fixture_payload("login_logs_search", "completed")
    numeric_user_payload["source_card"]["login_logs_summary"]["user_id_sample"] = "12345678901"
    numeric_user_result = normalize_service_response("login_logs_search", numeric_user_payload)
    numeric_user_card = build_partial_evidence_card([numeric_user_result])
    numeric_user_summary = numeric_user_card["evidence_summary_by_source"]["login_logs_search"]
    assert numeric_user_summary["login_window_summary"]["user_id_sample"] == "12345678901"
    assert numeric_user_summary["login_window_summary"]["phone_number_sample"] == "1381234****"
    numeric_user_text = json.dumps(numeric_user_card, ensure_ascii=True)
    assert "13812345678" not in numeric_user_text
    results.append(("phone_masking_does_not_reclassify_numeric_user_id", "passed"))

    credential_payload = _fixture_payload("login_logs_search", "completed")
    credential_payload["source_card"]["login_logs_summary"]["authorization"] = "Bearer raw_secret_value"
    credential_payload["source_card"]["login_logs_summary"]["cookie"] = "ks_session=raw_cookie_value"
    credential_payload["source_card"]["login_logs_summary"]["token"] = "raw_token_value"
    credential_result = normalize_service_response("login_logs_search", credential_payload)
    credential_card = build_partial_evidence_card([credential_result])
    credential_text = json.dumps(credential_card, ensure_ascii=True)
    assert "raw_secret_value" not in credential_text
    assert "raw_cookie_value" not in credential_text
    assert "raw_token_value" not in credential_text
    assert credential_card["sensitive_output"] is False
    results.append(("credential_secret_never_output", "passed"))

    raw_dump_payload = _fixture_payload("weapon_inventory", "completed")
    raw_dump_payload["source_card"]["raw_body"] = {"full": "raw_full_body_should_not_render"}
    raw_dump_payload["source_card"]["raw_login_records"] = [{"ip": "198.51.100.10"}]
    raw_dump_payload["source_card"]["raw_labelInfo"] = {"label": "raw_label_should_not_render"}
    raw_dump_payload["source_card"]["raw_originalLog"] = {"eventId": "raw_original_event_should_not_render"}
    raw_dump_result = normalize_service_response("weapon_inventory", raw_dump_payload)
    raw_dump_card = build_partial_evidence_card([raw_dump_result])
    raw_dump_text = json.dumps(raw_dump_card, ensure_ascii=True)
    assert "raw_full_body_should_not_render" not in raw_dump_text
    assert "198.51.100.10" not in raw_dump_text
    assert "raw_label_should_not_render" not in raw_dump_text
    assert "raw_original_event_should_not_render" not in raw_dump_text
    results.append(("raw_body_records_labelinfo_originallog_not_output", "passed"))

    completed = normalize_service_response("track_analysis_summary", _fixture_payload("track_analysis_summary", "completed"))
    no_data = normalize_service_response("login_logs_search", _fixture_payload("login_logs_search", "no_data"))
    blocked = normalize_service_response("rcp_snapshot", _fixture_payload("rcp_snapshot", "blocked", "platform_error"))
    card = build_partial_evidence_card([completed, no_data, blocked])
    assert card["completed_sources"] == ["track_analysis_summary"]
    assert card["no_data_sources"] == ["login_logs_search"]
    assert card["blocked_sources"] == ["rcp_snapshot"]
    assert card["sensitive_output"] is False
    assert card["no_data_not_risk_exclusion"] is True
    results.append(("partial_evidence_card_mixed_sources", "passed"))

    parse_error = normalize_service_response("login_logs_search", _fixture_payload("login_logs_search", "parse_error", "parse_error"))
    parse_error_card = build_partial_evidence_card([parse_error])
    assert parse_error["source_status"] == "parse_error"
    assert parse_error["source_card"] and parse_error["source_quality"]
    assert parse_error["sensitive_output"] is False
    assert parse_error_card["source_completion_matrix"]["parse_error_sources"] == ["login_logs_search"]
    results.append(("login_logs_parse_error_standard_source_result", "passed"))

    network_error = normalize_service_response(
        "login_logs_search",
        _fixture_payload("login_logs_search", "network_error", "network_error"),
    )
    network_error_card = build_partial_evidence_card([network_error])
    network_login_summary = network_error_card["evidence_summary_by_source"]["login_logs_search"]
    assert network_error["source_status"] == "blocked"
    assert network_error["source_card"] and network_error["source_quality"]
    assert network_error["latency_ms"] == 123
    assert network_error["sensitive_output"] is False
    assert network_error_card["source_completion_matrix"]["blocked_sources"] == ["login_logs_search"]
    assert network_login_summary["login_window_summary"]["standard_browser_backed_source_result"] is True
    assert network_login_summary["blocked_parse_or_no_data_not_counter_evidence"] is True
    results.append(("LOGIN-LOGS-STANDARD-SOURCE-RESULT-IN-EVIDENCE-CARD", "passed"))

    weapon_result = normalize_service_response("weapon_inventory", _fixture_payload("weapon_inventory", "completed"))
    weapon_card = build_partial_evidence_card([weapon_result])
    weapon_summary = weapon_card["evidence_summary_by_source"]["weapon_inventory"]
    assert _has_private_raw_reference(weapon_result, "device_id") is True
    assert weapon_summary["chaining_summary"]["raw_device_safe_handle_retained"] is True
    serialized_weapon_result = json.dumps(weapon_result, ensure_ascii=True)
    serialized_weapon_card = json.dumps(weapon_card, ensure_ascii=True)
    assert "ANDROID_raw_device_should_not_render" not in serialized_weapon_result
    assert "ANDROID_raw_device_should_not_render" not in serialized_weapon_card
    assert "raw_value" not in serialized_weapon_result
    results.append(("WEAPON-RISKDATA-CHAINING-SAFE-HANDLE-PRESERVED", "passed"))

    four_source_results = [
        normalize_service_response("track_analysis_summary", _fixture_payload("track_analysis_summary", "completed")),
        normalize_service_response("rcp_snapshot", _fixture_payload("rcp_snapshot", "completed")),
        normalize_service_response("weapon_inventory", _fixture_payload("weapon_inventory", "completed")),
        normalize_service_response("login_logs_search", _fixture_payload("login_logs_search", "no_data")),
    ]
    four_source_card = build_partial_evidence_card(four_source_results)
    summaries = four_source_card["evidence_summary_by_source"]
    assert summaries["track_analysis_summary"]["bundle_summary"]["mode"] == "account_security_bundle"
    assert summaries["track_analysis_summary"]["bundle_summary"]["sub_interfaces"] == [
        "profile",
        "getUseDuration",
        "getDeviceIds",
        "getLastestDateTime",
    ]
    assert summaries["track_analysis_summary"]["profile_summary"]["register_time_present"] is True
    assert summaries["track_analysis_summary"]["latest_timestamp_summary"]["latest_datetime_present"] is True
    assert summaries["track_analysis_summary"]["use_duration_summary"]["rows_count"] == 7
    assert summaries["track_analysis_summary"]["device_ids_summary"]["device_ids_count"] == 2
    assert summaries["rcp_snapshot"]["event_summary"]["event_count"] == 3
    assert summaries["rcp_snapshot"]["chaining_keys_present"]["hitFusePolicyCode"] is True
    assert "final risk judgement" in summaries["rcp_snapshot"]["boundary"].lower()
    assert summaries["weapon_inventory"]["graph_summary"]["related_device_count"] == 2
    assert summaries["weapon_inventory"]["risk_summary"]["risk_label_count"] == 2
    assert summaries["login_logs_search"]["login_window_summary"]["records_count"] == 0
    assert four_source_card["missing_evidence"][0]["source_name"] == "login_logs_search"
    assert four_source_card["evidence_boundary"]["final_risk_judgement_made"] is False
    serialized_card = json.dumps(four_source_card, ensure_ascii=True)
    assert '"raw_labelInfo":' not in serialized_card
    assert "raw_device_should_not_render" not in serialized_card
    assert "raw_log_should_not_render" not in serialized_card
    results.append(("four_source_business_evidence_summary", "passed"))

    return {
        "fixture_tests": len(results),
        "passed": [name for name, status in results if status == "passed"],
    }


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Browser-backed service client utilities")
    parser.add_argument("--self-test", action="store_true", help="run fixture tests without live service")
    args = parser.parse_args(argv)

    if args.self_test:
        print(json.dumps(run_fixture_tests(), indent=2, sort_keys=True))
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
