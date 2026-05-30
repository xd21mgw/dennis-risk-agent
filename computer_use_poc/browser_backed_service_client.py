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
RESPONSE_MODE_COMPAT_SUMMARY = "compat_summary"
RESPONSE_MODE_PASSTHROUGH = "passthrough"
RESPONSE_MODES = {RESPONSE_MODE_COMPAT_SUMMARY, RESPONSE_MODE_PASSTHROUGH}
PASSTHROUGH_PARSER_REGISTRY: Dict[str, Any] = {}

ACTION_ENDPOINTS = {
    "track_analysis_summary": "/actions/track_analysis_summary",
    "track_analysis_check_data_ready": "/actions/track_analysis_check_data_ready",
    "rcp_snapshot": "/actions/rcp_snapshot",
    "weapon_inventory": "/actions/weapon_inventory",
    "login_logs_search": "/actions/login_logs_search",
    "archives_user_analysis": "/actions/archives_user_analysis",
    "archives_photo_search": "/actions/archives_photo_search",
    "archives_user_profile": "/actions/archives_user_profile",
    "archives_related_users": "/actions/archives_related_users",
    "archives_private_message_search": "/actions/archives_private_message_search",
    "archives_past_four_items": "/actions/archives_past_four_items",
    "rcp_event_detail": "/actions/rcp_event_detail",
    "rcp_event_feature_list": "/actions/rcp_event_feature_list",
    "rcp_policy_version_lookup": "/actions/rcp_policy_version_lookup",
    "rcp_policy_detail_lookup": "/actions/rcp_policy_detail_lookup",
    "rcp_policy_release_record_lookup": "/actions/rcp_policy_release_record_lookup",
    "rcp_policy_tree_lookup": "/actions/rcp_policy_tree_lookup",
    "rcp_node_policy_attribution": "/actions/rcp_node_policy_attribution",
    "rcp_node_bind_policy_attribution": "/actions/rcp_node_bind_policy_attribution",
}

ACTION_TO_SOURCE = {
    "track_analysis_summary": "track_analysis_summary",
    "track_analysis_check_data_ready": "track_analysis_check_data_ready",
    "rcp_snapshot": "rcp_snapshot",
    "weapon_inventory": "weapon_inventory",
    "login_logs_search": "login_logs_search",
    "archives_user_analysis": "archives_user_analysis",
    "archives_photo_search": "archives_photo_search",
    "archives_user_profile": "archives_user_profile",
    "archives_related_users": "archives_related_users",
    "archives_private_message_search": "archives_private_message_search",
    "archives_past_four_items": "archives_past_four_items",
    "rcp_event_detail": "rcp_event_detail",
    "rcp_event_feature_list": "rcp_event_feature_list",
    "rcp_policy_version_lookup": "rcp_policy_version_lookup",
    "rcp_policy_detail_lookup": "rcp_policy_detail_lookup",
    "rcp_policy_release_record_lookup": "rcp_policy_release_record_lookup",
    "rcp_policy_tree_lookup": "rcp_policy_tree_lookup",
    "rcp_node_policy_attribution": "rcp_node_policy_attribution",
    "rcp_node_bind_policy_attribution": "rcp_node_bind_policy_attribution",
}

ACCOUNT_SECURITY_TRACK_SUB_INTERFACES = ("profile", "getUseDuration", "getDeviceIds", "getLastestDateTime")
ACCOUNT_SECURITY_RISKDATA_DEVICE_PREFIXES = ("ANDROID_", "IOS_")
TRACK_ANALYSIS_BUNDLE_SOURCE_NAME = "track_analysis_account_security_bundle"
TRACK_ANALYSIS_BUNDLE_MODE = "account_security_bundle"
TRACK_ANALYSIS_CHECK_DATA_READY_FIXED_PATH = "/dp/platform/app/analytics/v2/sequence/checkDataReady"
TRACK_ANALYSIS_FUNC_TYPE = "USER_PROFILE_QUERY"
TRACK_ANALYSIS_APP_NAMES = {"KUAISHOU", "NEBULA"}
ARCHIVES_USER_ANALYSIS_FIXED_PATH = "/v3/user/log/coreLogs/fetch"
ARCHIVES_PHOTO_SEARCH_FIXED_PATH = "/v4/archives/report/photo/search"
ARCHIVES_USER_PROFILE_FIXED_PATH = "/archives/user/home/info"
ARCHIVES_RELATED_USERS_FIXED_PATH = "/archives/user/search/device"
ARCHIVES_PRIVATE_MESSAGE_SEARCH_FIXED_PATH = "/archives/user/message/search"
ARCHIVES_PAST_FOUR_ITEMS_FIXED_PATH = "/v4/audit/user/fourinfo/log/search"
RCP_EVENT_DETAIL_FIXED_PATH = "/v2/rest/event/rcpEventDetail"
RCP_EVENT_FEATURE_LIST_FIXED_PATH = "/v2/rest/event/rcpEventFeatureList"
RCP_POLICY_VERSION_LOOKUP_FIXED_PATH = "/v2/rest/pc/policy/getPolicyVersionListByEvent"
RCP_POLICY_DETAIL_LOOKUP_FIXED_PATH = "/v2/rest/pro/policy/getPolicyDetailByVersion"
RCP_POLICY_RELEASE_SELECT_INFO_FIXED_PATH = "/v2/rest/common/pipeline/selectInfo"
RCP_POLICY_RELEASE_LIST_FIXED_PATH = "/v2/rest/common/pipeline/list"
RCP_POLICY_TREE_LIST_FIXED_PATH = "/v2/rest/pro/policyTree/policyTreeList"
RCP_POLICY_TREE_LOOKUP_FIXED_PATH = "/v2/rest/pro/policyTree/queryProPolicyTree"
RCP_POLICY_TREE_BINDING_BY_NODE_FIXED_PATH = "/v2/rest/pro/policyTree/queryBindingByNodeCode"
RCP_POLICY_TREE_ALL_POLICY_CODE_FIXED_PATH = "/v2/rest/pro/policyTree/getAllPolicyCodeByPage"
RCP_NODE_POLICY_ATTRIBUTION_FIXED_PATH = "/v2/rest/pc/policy/nodePolicyAttribution"
RCP_NODE_BIND_POLICY_ATTRIBUTION_FIXED_PATH = "/v2/rest/pc/policy/nodeBindPolicyAttribution"
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
ARCHIVES_RELATED_USER_TYPES = {
    "same_device_registered": 0,
    "same_device_login": 1,
}
ARCHIVES_PRIVATE_MESSAGE_DIRECTIONS = {
    "sent": "fromUserId",
    "received": "toUserId",
}
ARCHIVES_FOUR_INFO_TYPES = {
    "all": 0,
    "username": 1,
    "avatar": 2,
    "profile_description": 3,
    "background": 4,
}
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
        "user_ids",
        "related_user_ids",
        "uid",
        "device_id",
        "device_ids",
        "deviceId",
        "did",
        "DID",
        "ip",
        "ip_address",
        "userIpDesc",
        "eventId",
        "event_id",
        "eventType",
        "sourceId",
        "source_id",
        "photo_id",
        "photo_ids",
        "photoId",
        "live_id",
        "live_ids",
        "liveId",
        "strategy_id",
        "policyCode",
        "policy_code",
        "policy_codes",
        "policyVersion",
        "policyTreeCode",
        "policyTreeNodeCode",
        "businessUnionKey",
        "business_union_key",
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
CONTROL_INPUT_KEYS = {"response_mode"}

COMPLETED_STATUSES = {"ok", "completed"}
NO_DATA_STATUSES = {"no_data", "completed_no_data", "completed_no_hit_for_small_window"}
AUTH_FAILED_STATUSES = {"auth_failed"}
BLOCKED_STATUSES = {"blocked", "network_error", "platform_error"}
TIMEOUT_STATUSES = {"timeout"}
PARSE_ERROR_STATUSES = {"parse_error"}
INVALID_PARAMETER_STATUSES = {"parameter_error", "invalid_parameter", "wrong_request_body_shape"}
DISPLAY_FORBIDDEN_FIELD_MARKERS = {
    "raw_profile",
    "rawProfile",
    "userProfileRaw",
    "raw_body",
    "raw_response",
    "raw_login_records",
    "raw_labelinfo",
    "raw_originalLog",
    "requestParam",
    "extraParam",
    "logContent",
    "full_json",
    "reportText",
    "reportContent",
    "messageContent",
    "commentContent",
    "privateMessage",
    "privateMessagePlaintext",
    "messageText",
    "counterpartNickname",
    "rawRelatedUserProfile",
    "rawFourInfo",
    "oldValue",
    "newValue",
    "avatarUrl",
    "backgroundUrl",
    "profileDescription",
    "operatorName",
    "rawDetailBody",
    "rawFeatureValue",
    "featureValue",
    "rawPolicyVersionBody",
    "rawPolicyTreeBody",
    "policyTreeRaw",
    "rawConditionDump",
    "conditionListRaw",
    "rawNodeBindingBody",
    "nodebindingPolicyListRaw",
    "rawReadinessBody",
    "traceId",
    "rawReleaseRecords",
    "releaseRecordsRaw",
    "rawPipelineRecords",
    "pipelineRecordsRaw",
    "createUser",
    "updateUser",
    "bindingUser",
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

    def call_action(
        self,
        action_name: str,
        typed_params: Optional[Mapping[str, Any]] = None,
        *,
        response_mode: str = RESPONSE_MODE_COMPAT_SUMMARY,
    ) -> Dict[str, Any]:
        """Call one fixed browser-backed action and normalize the response.

        Transport failures are returned as source results instead of escaping as
        Dennis runtime failures.
        """

        _validate_action_name(action_name)
        if response_mode not in RESPONSE_MODES:
            raise BrowserBackedServiceInputError(f"unsupported browser-backed response_mode: {response_mode}")
        params = dict(typed_params or {})
        _validate_typed_params(params)
        if response_mode == RESPONSE_MODE_PASSTHROUGH:
            params["response_mode"] = RESPONSE_MODE_PASSTHROUGH

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

        if response_mode == RESPONSE_MODE_PASSTHROUGH:
            return normalize_passthrough_service_response(action_name, service_payload, http_status=http_status)
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


def build_track_analysis_check_data_ready_browser_backed_request(
    device_id: str,
    start_time_ms: int,
    end_time_ms: int,
    app_name: str = "KUAISHOU",
    product: str = "KUAISHOU",
    categories: Optional[Iterable[str]] = None,
    metric: str = "pv",
    check_type: str = "deviceId",
    app_platforms: Optional[Iterable[str]] = None,
    events: Optional[Iterable[str]] = None,
    page_size: int = 100,
    include: int = 1,
) -> Dict[str, Any]:
    """Return the fixed Track Analysis data-readiness precheck plan."""

    _validate_track_analysis_device_id(device_id)
    _validate_track_analysis_app_name(app_name)
    if product not in TRACK_ANALYSIS_APP_NAMES:
        raise BrowserBackedServiceInputError("product must be KUAISHOU or NEBULA")
    if not isinstance(start_time_ms, int) or not isinstance(end_time_ms, int) or start_time_ms <= 0 or end_time_ms <= 0:
        raise BrowserBackedServiceInputError("start_time_ms and end_time_ms must be positive millisecond timestamps")
    if start_time_ms >= end_time_ms:
        raise BrowserBackedServiceInputError("start_time_ms must be before end_time_ms")
    if not isinstance(page_size, int) or page_size < 1 or page_size > 1000:
        raise BrowserBackedServiceInputError("page_size must be between 1 and 1000")
    if include not in {0, 1}:
        raise BrowserBackedServiceInputError("include must be 0 or 1")
    if not _is_safe_track_analysis_label(metric):
        raise BrowserBackedServiceInputError("metric must be a safe Track Analysis metric label")
    if check_type != "deviceId":
        raise BrowserBackedServiceInputError("check_type must remain deviceId for this HAR-confirmed contract")

    category_list = _coerce_track_analysis_label_list(categories, default=["active"])
    platform_list = _coerce_track_analysis_label_list(app_platforms, default=[])
    event_list = _coerce_track_analysis_label_list(events, default=[])
    typed_params: Dict[str, Any] = {
        "device_id": device_id,
        "appName": app_name,
        "product": product,
        "startTime": start_time_ms,
        "endTime": end_time_ms,
        "include": include,
        "pageSize": page_size,
        "category": category_list,
        "event": event_list,
        "appPlatform": platform_list,
        "metric": metric,
        "type": check_type,
        "mode": "track_analysis_data_readiness_precheck",
    }
    request = {
        "source_name": "track_analysis_check_data_ready",
        "action_name": "track_analysis_check_data_ready",
        "priority": "P2-helper",
        "fixed_path": TRACK_ANALYSIS_CHECK_DATA_READY_FIXED_PATH,
        "typed_params": typed_params,
        "body_builder_summary": {
            "service_side_body_builder": True,
            "method": "POST",
            "body_fields": [
                "appName",
                "startTime",
                "endTime",
                "include",
                "pageSize",
                "deviceId",
                "batchQueryId",
                "appPlatform",
                "category",
                "event",
                "metric",
                "product",
                "type",
                "funcType",
                "_t",
            ],
            "service_generated_fields": ["batchQueryId", "_t"],
            "fixed_fields": {"funcType": TRACK_ANALYSIS_FUNC_TYPE, "type": "deviceId"},
            "response_shape": "code/message/data.dateStatus/traceId",
            "trace_id_value_output": False,
            "raw_full_body_output": False,
        },
    }
    _validate_action_name(str(request["action_name"]))
    _validate_typed_params(request["typed_params"])
    return request


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


def build_archives_photo_search_browser_backed_request(
    user_id: str,
    begin_time_ms: int,
    end_time_ms: int,
    page: int = 1,
    count: int = 20,
    match_type: str = "0",
    sort: str = "0",
) -> Dict[str, Any]:
    """Return the fixed Archives Center photo report/search action plan."""

    if not isinstance(user_id, str) or not user_id.isdigit():
        raise BrowserBackedServiceInputError("user_id must be a decimal string")
    if not isinstance(begin_time_ms, int) or not isinstance(end_time_ms, int) or begin_time_ms <= 0 or end_time_ms <= 0:
        raise BrowserBackedServiceInputError("begin_time_ms and end_time_ms must be positive millisecond timestamps")
    if begin_time_ms >= end_time_ms:
        raise BrowserBackedServiceInputError("begin_time_ms must be before end_time_ms")
    if not isinstance(page, int) or page < 1:
        raise BrowserBackedServiceInputError("page must be a positive integer")
    if not isinstance(count, int) or count < 1 or count > 100:
        raise BrowserBackedServiceInputError("count must be between 1 and 100")
    if str(match_type) not in {"0", "1", "2"}:
        raise BrowserBackedServiceInputError("match_type must be a supported string enum")
    if str(sort) not in {"0", "1"}:
        raise BrowserBackedServiceInputError("sort must be a supported string enum")

    typed_params: Dict[str, Any] = {
        "user_id": user_id,
        "mode": "archives_photo_report_search",
        "begin": begin_time_ms,
        "end": end_time_ms,
        "page": page,
        "count": count,
        "matchType": str(match_type),
        "sort": str(sort),
    }
    request = {
        "source_name": "archives_photo_search",
        "action_name": "archives_photo_search",
        "priority": "P0-conditional",
        "fixed_path": ARCHIVES_PHOTO_SEARCH_FIXED_PATH,
        "typed_params": typed_params,
        "body_builder_summary": {
            "service_side_body_builder": True,
            "body_fields": ["reportedIds", "matchType", "sort", "begin", "end", "page", "count"],
            "reportedIds_source": "user_id",
            "raw_report_text_output": False,
            "raw_full_body_output": False,
        },
    }
    _validate_action_name(str(request["action_name"]))
    _validate_typed_params(request["typed_params"])
    return request


def build_archives_user_profile_browser_backed_request(user_id: str) -> Dict[str, Any]:
    """Return the fixed Archives Center user home/profile action plan."""

    if not isinstance(user_id, str) or not user_id.isdigit():
        raise BrowserBackedServiceInputError("user_id must be a decimal string")

    typed_params: Dict[str, Any] = {
        "user_id": user_id,
        "mode": "archives_user_home_profile",
    }
    request = {
        "source_name": "archives_user_profile",
        "action_name": "archives_user_profile",
        "priority": "P0",
        "fixed_path": ARCHIVES_USER_PROFILE_FIXED_PATH,
        "typed_params": typed_params,
        "body_builder_summary": {
            "service_side_body_builder": True,
            "method": "GET",
            "query_fields": ["userId"],
            "userId_source": "user_id",
            "optional_bundle_paths": [
                "/archives/user/home/getUserLabel",
                "/archives/user/home/getUserShopInfo",
                "/v3/user/risk/info",
            ],
            "raw_profile_body_output": False,
            "raw_full_body_output": False,
        },
    }
    _validate_action_name(str(request["action_name"]))
    _validate_typed_params(request["typed_params"])
    return request


def build_archives_related_users_browser_backed_request(
    user_id: str,
    relation_type: str = "same_device_registered",
) -> Dict[str, Any]:
    """Return the fixed Archives Center same-device related users action plan."""

    if not isinstance(user_id, str) or not user_id.isdigit():
        raise BrowserBackedServiceInputError("user_id must be a decimal string")
    if relation_type not in ARCHIVES_RELATED_USER_TYPES:
        raise BrowserBackedServiceInputError("relation_type must be same_device_registered or same_device_login")

    typed_params: Dict[str, Any] = {
        "user_id": user_id,
        "mode": "archives_same_device_related_users",
        "relation_type": relation_type,
        "inputType": 0,
        "type": ARCHIVES_RELATED_USER_TYPES[relation_type],
    }
    request = {
        "source_name": "archives_related_users",
        "action_name": "archives_related_users",
        "priority": "P1",
        "fixed_path": ARCHIVES_RELATED_USERS_FIXED_PATH,
        "typed_params": typed_params,
        "body_builder_summary": {
            "service_side_body_builder": True,
            "method": "POST",
            "body_fields": ["keyword", "inputType", "type"],
            "keyword_source": "user_id",
            "type_mapping": dict(ARCHIVES_RELATED_USER_TYPES),
            "raw_related_user_profile_output": False,
            "raw_full_body_output": False,
        },
    }
    _validate_action_name(str(request["action_name"]))
    _validate_typed_params(request["typed_params"])
    return request


def build_archives_private_message_search_browser_backed_request(
    user_id: str,
    direction: str,
    page: int = 1,
    count: int = 20,
    status: str = "",
    sort: str = "0",
) -> Dict[str, Any]:
    """Return the fixed Archives Center private-message summary action plan."""

    if not isinstance(user_id, str) or not user_id.isdigit():
        raise BrowserBackedServiceInputError("user_id must be a decimal string")
    if direction not in ARCHIVES_PRIVATE_MESSAGE_DIRECTIONS:
        raise BrowserBackedServiceInputError("direction must be sent or received")
    if not isinstance(page, int) or page < 1:
        raise BrowserBackedServiceInputError("page must be a positive integer")
    if not isinstance(count, int) or count < 1 or count > 100:
        raise BrowserBackedServiceInputError("count must be between 1 and 100")
    if not isinstance(status, str) or len(status) > 64:
        raise BrowserBackedServiceInputError("status must be a short string")
    if str(sort) not in {"0", "1"}:
        raise BrowserBackedServiceInputError("sort must be a supported string enum")

    typed_params: Dict[str, Any] = {
        "user_id": user_id,
        "mode": "archives_private_message_summary",
        "direction": direction,
        "page": page,
        "count": count,
        "status": status,
        "sort": str(sort),
    }
    request = {
        "source_name": "archives_private_message_search",
        "action_name": "archives_private_message_search",
        "priority": "P2-conditional",
        "fixed_path": ARCHIVES_PRIVATE_MESSAGE_SEARCH_FIXED_PATH,
        "typed_params": typed_params,
        "body_builder_summary": {
            "service_side_body_builder": True,
            "method": "POST",
            "body_fields": ["fromUserId|toUserId", "status", "sort", "page", "count"],
            "direction_mapping": dict(ARCHIVES_PRIVATE_MESSAGE_DIRECTIONS),
            "raw_message_plaintext_output": False,
            "raw_full_body_output": False,
        },
    }
    _validate_action_name(str(request["action_name"]))
    _validate_typed_params(request["typed_params"])
    return request


def build_archives_past_four_items_browser_backed_request(
    user_id: str,
    info_type: str = "all",
    page: int = 1,
    count: int = 20,
    mark_result: str = "",
    punish_result: str = "",
) -> Dict[str, Any]:
    """Return the fixed Archives Center four-info change-log action plan."""

    if not isinstance(user_id, str) or not user_id.isdigit():
        raise BrowserBackedServiceInputError("user_id must be a decimal string")
    if info_type not in ARCHIVES_FOUR_INFO_TYPES:
        raise BrowserBackedServiceInputError("info_type must be all, username, avatar, profile_description, or background")
    if not isinstance(page, int) or page < 1:
        raise BrowserBackedServiceInputError("page must be a positive integer")
    if not isinstance(count, int) or count < 1 or count > 100:
        raise BrowserBackedServiceInputError("count must be between 1 and 100")
    if not isinstance(mark_result, str) or len(mark_result) > 64:
        raise BrowserBackedServiceInputError("mark_result must be a short string")
    if not isinstance(punish_result, str) or len(punish_result) > 64:
        raise BrowserBackedServiceInputError("punish_result must be a short string")

    typed_params: Dict[str, Any] = {
        "user_id": user_id,
        "mode": "archives_four_info_change_log_summary",
        "info_type": info_type,
        "infoType": ARCHIVES_FOUR_INFO_TYPES[info_type],
        "page": page,
        "count": count,
        "markResult": mark_result,
        "punishResult": punish_result,
    }
    request = {
        "source_name": "archives_past_four_items",
        "action_name": "archives_past_four_items",
        "priority": "P2-conditional",
        "fixed_path": ARCHIVES_PAST_FOUR_ITEMS_FIXED_PATH,
        "typed_params": typed_params,
        "body_builder_summary": {
            "service_side_body_builder": True,
            "method": "POST",
            "body_fields": ["keyword", "infoType", "markResult", "punishResult", "page", "count"],
            "keyword_source": "user_id",
            "infoType_mapping": dict(ARCHIVES_FOUR_INFO_TYPES),
            "raw_old_new_profile_content_output": False,
            "raw_media_url_output": False,
            "raw_full_body_output": False,
        },
    }
    _validate_action_name(str(request["action_name"]))
    _validate_typed_params(request["typed_params"])
    return request


def build_rcp_event_detail_browser_backed_request(
    event_type: str,
    event_id: str,
    query_time_ms: int,
) -> Dict[str, Any]:
    """Return the fixed RCP event detail action plan."""

    _validate_rcp_event_identity(event_type, event_id, query_time_ms)
    typed_params: Dict[str, Any] = {
        "eventType": event_type,
        "eventId": event_id,
        "queryTime": query_time_ms,
        "mode": "rcp_event_detail_readonly",
    }
    request = {
        "source_name": "rcp_event_detail",
        "action_name": "rcp_event_detail",
        "priority": "P0-explicit",
        "fixed_path": RCP_EVENT_DETAIL_FIXED_PATH,
        "typed_params": typed_params,
        "body_builder_summary": {
            "service_side_body_builder": True,
            "method": "GET",
            "query_fields": ["eventType", "eventId", "queryTime"],
            "queryTime_rule": "use exact _occurTime from eventList/fastQueryHbase when available",
            "raw_detail_body_output": False,
            "raw_full_body_output": False,
        },
    }
    _validate_action_name(str(request["action_name"]))
    _validate_typed_params(request["typed_params"])
    return request


def build_rcp_event_feature_list_browser_backed_request(
    event_type: str,
    event_id: str,
    query_time_ms: int,
    feature_group: str = "",
) -> Dict[str, Any]:
    """Return the fixed RCP event feature snapshot action plan."""

    _validate_rcp_event_identity(event_type, event_id, query_time_ms)
    if feature_group != "":
        raise BrowserBackedServiceInputError("feature_group must be empty string until a later contract proves otherwise")
    typed_params: Dict[str, Any] = {
        "eventType": event_type,
        "eventId": event_id,
        "queryTime": query_time_ms,
        "featureGroup": feature_group,
        "mode": "rcp_event_feature_snapshot_readonly",
    }
    request = {
        "source_name": "rcp_event_feature_list",
        "action_name": "rcp_event_feature_list",
        "priority": "P1-explicit",
        "fixed_path": RCP_EVENT_FEATURE_LIST_FIXED_PATH,
        "typed_params": typed_params,
        "body_builder_summary": {
            "service_side_body_builder": True,
            "method": "GET",
            "query_fields": ["eventType", "eventId", "queryTime", "featureGroup"],
            "featureGroup_default": "",
            "queryTime_rule": "use exact _occurTime from event detail; do not use hitTimestamp when _occurTime is available",
            "raw_feature_values_output": False,
            "raw_full_body_output": False,
        },
    }
    _validate_action_name(str(request["action_name"]))
    _validate_typed_params(request["typed_params"])
    return request


def build_rcp_policy_version_lookup_browser_backed_request(
    event_type: str,
    event_id: str,
    policy_code: str,
    policy_version: int,
    query_time_ms: int,
) -> Dict[str, Any]:
    """Return the fixed RCP policy version context action plan."""

    _validate_rcp_event_identity(event_type, event_id, query_time_ms)
    _validate_rcp_policy_identity(policy_code, policy_version)
    typed_params: Dict[str, Any] = {
        "eventType": event_type,
        "eventId": event_id,
        "policyCode": policy_code,
        "policyVersion": policy_version,
        "queryTime": query_time_ms,
        "mode": "rcp_policy_version_lookup_readonly",
    }
    request = {
        "source_name": "rcp_policy_version_lookup",
        "action_name": "rcp_policy_version_lookup",
        "priority": "P1-explicit",
        "fixed_path": RCP_POLICY_VERSION_LOOKUP_FIXED_PATH,
        "typed_params": typed_params,
        "body_builder_summary": {
            "service_side_body_builder": True,
            "method": "GET",
            "query_fields": ["eventType", "eventId", "policyCode", "policyVersion", "queryTime"],
            "queryTime_rule": "use exact _occurTime from event detail when available",
            "raw_policy_version_body_output": False,
            "raw_full_body_output": False,
        },
    }
    _validate_action_name(str(request["action_name"]))
    _validate_typed_params(request["typed_params"])
    return request


def build_rcp_policy_detail_lookup_browser_backed_request(
    policy_code: str,
    policy_version: int,
) -> Dict[str, Any]:
    """Return the fixed RCP policy detail readonly action plan."""

    _validate_rcp_policy_identity(policy_code, policy_version)
    typed_params: Dict[str, Any] = {
        "policyCode": policy_code,
        "policyVersion": policy_version,
        "mode": "rcp_policy_detail_lookup_readonly",
    }
    request = {
        "source_name": "rcp_policy_detail_lookup",
        "action_name": "rcp_policy_detail_lookup",
        "priority": "strategy_governance",
        "fixed_path": RCP_POLICY_DETAIL_LOOKUP_FIXED_PATH,
        "typed_params": typed_params,
        "body_builder_summary": {
            "service_side_body_builder": True,
            "method": "GET",
            "query_fields": ["policyCode", "policyVersion"],
            "companion_readonly_paths": [
                "/v2/rest/pro/policy/getPolicyAllVersion",
                "/v2/rest/pc/policyReview/getRelationPolicyTree",
            ],
            "raw_policy_detail_body_output": False,
            "raw_condition_expression_output": False,
            "raw_full_body_output": False,
        },
    }
    _validate_action_name(str(request["action_name"]))
    _validate_typed_params(request["typed_params"])
    return request


def build_rcp_policy_release_record_lookup_browser_backed_request(
    policy_code: str,
    status_code: str = "",
    page: int = 1,
    size: int = 20,
) -> Dict[str, Any]:
    """Return the fixed RCP policy release-record readonly action plan."""

    if not _is_safe_policy_code(policy_code):
        raise BrowserBackedServiceInputError("policy_code must be a stable policy code")
    if status_code and not re.fullmatch(r"[A-Za-z0-9_:-]{1,32}", status_code):
        raise BrowserBackedServiceInputError("status_code must be a stable workflow status code")
    if not isinstance(page, int) or page < 1:
        raise BrowserBackedServiceInputError("page must be a positive integer")
    if not isinstance(size, int) or size < 1 or size > 100:
        raise BrowserBackedServiceInputError("size must be between 1 and 100")

    typed_params: Dict[str, Any] = {
        "policyCode": policy_code,
        "statusCode": status_code,
        "page": page,
        "size": size,
        "mode": "rcp_policy_release_record_lookup_readonly",
    }
    request = {
        "source_name": "rcp_policy_release_record_lookup",
        "action_name": "rcp_policy_release_record_lookup",
        "priority": "strategy_governance",
        "fixed_path": RCP_POLICY_RELEASE_LIST_FIXED_PATH,
        "typed_params": typed_params,
        "body_builder_summary": {
            "service_side_body_builder": True,
            "method": "POST",
            "body_fields": [
                "configCode",
                "createUser",
                "extrbA",
                "extrbB",
                "extrbC",
                "pageInfoRequest",
                "statusCode",
            ],
            "field_mapping": {
                "extrbB": "policyCode",
                "statusCode": "statusCode",
                "pageInfoRequest.page": "page",
                "pageInfoRequest.size": "size",
            },
            "service_owned_fields": ["configCode", "createUser", "extrbA", "extrbC"],
            "companion_readonly_paths": [RCP_POLICY_RELEASE_SELECT_INFO_FIXED_PATH],
            "selectInfo_query_fields": ["pipelineConfig"],
            "businessUnionKey_rule": "{policyCode}_{policyVersion}_{eventTypeCode}",
            "pipelineVersion_boundary": "pipelineVersion is process iteration version, not policy version",
            "raw_release_records_output": False,
            "operator_identity_output": False,
            "raw_full_body_output": False,
        },
    }
    _validate_action_name(str(request["action_name"]))
    _validate_typed_params(request["typed_params"])
    return request


def build_rcp_policy_tree_lookup_browser_backed_request(
    policy_tree_code: str,
    policy_tree_version: int,
    target_policy_code: Optional[str] = None,
) -> Dict[str, Any]:
    """Return the fixed RCP policy tree lookup action plan."""

    if not isinstance(policy_tree_code, str) or not re.fullmatch(r"[A-Za-z0-9_:-]{2,128}", policy_tree_code):
        raise BrowserBackedServiceInputError("policy_tree_code must be a stable policy tree code")
    if not isinstance(policy_tree_version, int) or policy_tree_version <= 0:
        raise BrowserBackedServiceInputError("policy_tree_version must be a positive integer")
    if target_policy_code is not None and not _is_safe_policy_code(target_policy_code):
        raise BrowserBackedServiceInputError("target_policy_code must be a stable policy code")
    typed_params: Dict[str, Any] = {
        "policyTreeCode": policy_tree_code,
        "policyTreeVersion": policy_tree_version,
        "mode": "rcp_policy_tree_lookup_readonly",
    }
    if target_policy_code:
        typed_params["targetPolicyCode"] = target_policy_code
    request = {
        "source_name": "rcp_policy_tree_lookup",
        "action_name": "rcp_policy_tree_lookup",
        "priority": "strategy_governance",
        "fixed_path": RCP_POLICY_TREE_LOOKUP_FIXED_PATH,
        "typed_params": typed_params,
        "body_builder_summary": {
            "service_side_body_builder": True,
            "method": "GET",
            "query_fields": ["policyTreeCode", "policyTreeVersion", "targetPolicyCode"],
            "companion_readonly_paths": [
                RCP_POLICY_TREE_LIST_FIXED_PATH,
                RCP_POLICY_TREE_BINDING_BY_NODE_FIXED_PATH,
                RCP_POLICY_TREE_ALL_POLICY_CODE_FIXED_PATH,
            ],
            "policyTreeList_role": "coarse filter/list only; not precise node lookup",
            "queryProPolicyTree_query_fields": ["policyTreeCode", "treeSnapshot", "_t"],
            "queryBindingByNodeCode_query_fields": [
                "policyCode",
                "searchOwn",
                "isOrder",
                "orderDesc",
                "orderField",
                "isNewest",
                "page",
                "size",
                "policyTreeCode",
                "policyTreeVersion",
                "policyTreeNodeCode",
                "treeSnapshot",
                "_t",
            ],
            "getAllPolicyCodeByPage_query_fields": [
                "page",
                "size",
                "policyTreeCode",
                "policyTreeVersion",
                "code",
                "_t",
            ],
            "node_resolution": "service recursively parses queryProPolicyTree result; caller must not provide guessed node code",
            "incorrect_path_forbidden": "/v2/rest/pc/policytree/getPolicyTreeByVersion",
            "raw_policy_tree_body_output": False,
            "raw_node_binding_list_output": False,
            "raw_all_policy_code_list_output": False,
            "raw_full_body_output": False,
        },
    }
    _validate_action_name(str(request["action_name"]))
    _validate_typed_params(request["typed_params"])
    return request


def build_rcp_node_policy_attribution_browser_backed_request(
    event_type: str,
    event_id: str,
    policy_code: str,
    policy_version: int,
    query_time_ms: int,
    region: str = "china",
) -> Dict[str, Any]:
    """Return the fixed RCP node policy attribution action plan."""

    _validate_rcp_event_identity(event_type, event_id, query_time_ms)
    _validate_rcp_policy_identity(policy_code, policy_version)
    if region not in {"china", "oversea", ""}:
        raise BrowserBackedServiceInputError("region must be china, oversea, or empty string")
    typed_params: Dict[str, Any] = {
        "eventType": event_type,
        "eventId": event_id,
        "policyCode": policy_code,
        "policyVersion": policy_version,
        "queryTime": query_time_ms,
        "region": region,
        "type": "",
        "mode": "rcp_node_policy_attribution_readonly",
    }
    request = {
        "source_name": "rcp_node_policy_attribution",
        "action_name": "rcp_node_policy_attribution",
        "priority": "P1-explicit",
        "fixed_path": RCP_NODE_POLICY_ATTRIBUTION_FIXED_PATH,
        "typed_params": typed_params,
        "body_builder_summary": {
            "service_side_body_builder": True,
            "method": "POST",
            "body_fields": ["eventType", "eventId", "policyCode", "policyVersion", "queryTime", "region", "type"],
            "fixed_fields": {"type": ""},
            "raw_condition_dump_output": False,
            "raw_feature_values_output": False,
            "raw_full_body_output": False,
        },
    }
    _validate_action_name(str(request["action_name"]))
    _validate_typed_params(request["typed_params"])
    return request


def build_rcp_node_bind_policy_attribution_browser_backed_request(
    event_type: str,
    event_id: str,
    query_time_ms: int,
    policy_tree_code: str,
    policy_tree_version: int,
    policy_tree_node_code: str,
) -> Dict[str, Any]:
    """Return the fixed RCP node-binding policy attribution action plan."""

    _validate_rcp_event_identity(event_type, event_id, query_time_ms)
    if not isinstance(policy_tree_code, str) or not re.fullmatch(r"[A-Za-z0-9_:-]{2,128}", policy_tree_code):
        raise BrowserBackedServiceInputError("policy_tree_code must be a stable policy tree code")
    if not isinstance(policy_tree_version, int) or policy_tree_version <= 0:
        raise BrowserBackedServiceInputError("policy_tree_version must be a positive integer")
    if not isinstance(policy_tree_node_code, str) or not re.fullmatch(r"[A-Za-z0-9_:-]{2,128}", policy_tree_node_code):
        raise BrowserBackedServiceInputError("policy_tree_node_code must be a stable resolved node code")
    typed_params: Dict[str, Any] = {
        "eventType": event_type,
        "eventId": event_id,
        "queryTime": query_time_ms,
        "policyTreeCode": policy_tree_code,
        "policyTreeVersion": policy_tree_version,
        "policyTreeNodeCode": policy_tree_node_code,
        "mode": "rcp_node_bind_policy_attribution_readonly",
    }
    request = {
        "source_name": "rcp_node_bind_policy_attribution",
        "action_name": "rcp_node_bind_policy_attribution",
        "priority": "strategy_governance",
        "fixed_path": RCP_NODE_BIND_POLICY_ATTRIBUTION_FIXED_PATH,
        "typed_params": typed_params,
        "body_builder_summary": {
            "service_side_body_builder": True,
            "method": "GET",
            "query_fields": [
                "eventType",
                "eventId",
                "queryTime",
                "policyTreeCode",
                "policyTreeVersion",
                "policyTreeNodeCode",
            ],
            "policyTreeNodeCode_rule": "must come from queryProPolicyTree parser; do not guess from serial/policyCode/name",
            "raw_node_binding_body_output": False,
            "raw_condition_dump_output": False,
            "raw_full_body_output": False,
        },
    }
    _validate_action_name(str(request["action_name"]))
    _validate_typed_params(request["typed_params"])
    return request


def _validate_rcp_event_identity(event_type: str, event_id: str, query_time_ms: int) -> None:
    if not isinstance(event_type, str) or not re.fullmatch(r"[A-Za-z0-9_:-]{2,128}", event_type):
        raise BrowserBackedServiceInputError("event_type must be a stable event type string")
    if not isinstance(event_id, str) or not re.fullmatch(r"[A-Za-z0-9_:-]{4,128}", event_id):
        raise BrowserBackedServiceInputError("event_id must be a stable event id string")
    if not isinstance(query_time_ms, int) or query_time_ms <= 0:
        raise BrowserBackedServiceInputError("query_time_ms must be a positive millisecond timestamp")


def _validate_rcp_policy_identity(policy_code: str, policy_version: int) -> None:
    if not _is_safe_policy_code(policy_code):
        raise BrowserBackedServiceInputError("policy_code must be a stable policy code")
    if not isinstance(policy_version, int) or policy_version <= 0:
        raise BrowserBackedServiceInputError("policy_version must be a positive integer")


def _is_safe_policy_code(policy_code: Any) -> bool:
    return isinstance(policy_code, str) and bool(re.fullmatch(r"[A-Za-z0-9_:#.-]{2,256}", policy_code))


def _validate_track_analysis_device_id(device_id: Any) -> None:
    if not isinstance(device_id, str) or not re.fullmatch(r"[A-Za-z0-9_:-]{4,256}", device_id):
        raise BrowserBackedServiceInputError("device_id must be a stable device risk entity identifier")


def _validate_track_analysis_app_name(app_name: Any) -> None:
    if app_name not in TRACK_ANALYSIS_APP_NAMES:
        raise BrowserBackedServiceInputError("appName must be KUAISHOU or NEBULA")


def _is_safe_track_analysis_label(value: Any) -> bool:
    return isinstance(value, str) and bool(re.fullmatch(r"[A-Za-z0-9_:-]{1,128}", value))


def _coerce_track_analysis_label_list(values: Optional[Iterable[str]], default: list[str]) -> list[str]:
    if values is None:
        return list(default)
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise BrowserBackedServiceInputError("Track Analysis label list must be a list of safe labels")
    result = list(values)
    if len(result) > 20:
        raise BrowserBackedServiceInputError("Track Analysis label list must not exceed 20 items")
    for value in result:
        if not _is_safe_track_analysis_label(value):
            raise BrowserBackedServiceInputError("Track Analysis label list contains an unsafe label")
    return result


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

    if action_name == "track_analysis_check_data_ready":
        _attach_track_analysis_check_data_ready_contract_fields(
            normalized,
            service_payload,
            source_card,
            source_quality,
            output_scope,
        )
    if action_name == "archives_user_analysis":
        _attach_archives_user_analysis_contract_fields(normalized, service_payload, source_card, source_quality, output_scope)
    if action_name == "archives_photo_search":
        _attach_archives_photo_search_contract_fields(normalized, service_payload, source_card, source_quality, output_scope)
    if action_name == "archives_user_profile":
        _attach_archives_user_profile_contract_fields(normalized, service_payload, source_card, source_quality, output_scope)
    if action_name == "archives_related_users":
        _attach_archives_related_users_contract_fields(normalized, service_payload, source_card, source_quality, output_scope)
    if action_name == "archives_private_message_search":
        _attach_archives_private_message_search_contract_fields(normalized, service_payload, source_card, source_quality, output_scope)
    if action_name == "archives_past_four_items":
        _attach_archives_past_four_items_contract_fields(normalized, service_payload, source_card, source_quality, output_scope)
    if action_name == "rcp_event_detail":
        _attach_rcp_event_detail_contract_fields(normalized, service_payload, source_card, source_quality, output_scope)
    if action_name == "rcp_event_feature_list":
        _attach_rcp_event_feature_list_contract_fields(normalized, service_payload, source_card, source_quality, output_scope)
    if action_name == "rcp_policy_version_lookup":
        _attach_rcp_policy_version_lookup_contract_fields(normalized, service_payload, source_card, source_quality, output_scope)
    if action_name == "rcp_policy_detail_lookup":
        _attach_rcp_policy_detail_lookup_contract_fields(normalized, service_payload, source_card, source_quality, output_scope)
    if action_name == "rcp_policy_release_record_lookup":
        _attach_rcp_policy_release_record_lookup_contract_fields(
            normalized,
            service_payload,
            source_card,
            source_quality,
            output_scope,
        )
    if action_name == "rcp_policy_tree_lookup":
        _attach_rcp_policy_tree_lookup_contract_fields(normalized, service_payload, source_card, source_quality, output_scope)
    if action_name == "rcp_node_policy_attribution":
        _attach_rcp_node_policy_attribution_contract_fields(normalized, service_payload, source_card, source_quality, output_scope)
    if action_name == "rcp_node_bind_policy_attribution":
        _attach_rcp_node_bind_policy_attribution_contract_fields(normalized, service_payload, source_card, source_quality, output_scope)

    return normalized


def normalize_passthrough_service_response(
    action_name: str,
    service_payload: Mapping[str, Any],
    http_status: Optional[int] = None,
) -> Dict[str, Any]:
    """Normalize an explicit passthrough-mode response without exposing raw body."""

    _validate_action_name(action_name)
    source_name = ACTION_TO_SOURCE[action_name]
    latency_ms = _extract_passthrough_latency_ms(service_payload)
    unexpected_summary_fields = [key for key in ("source_card", "source_quality") if key in service_payload]
    upstream = service_payload.get("upstream") if isinstance(service_payload.get("upstream"), Mapping) else {}
    upstream_summary = {
        "status": upstream.get("status") if isinstance(upstream, Mapping) else None,
        "content_type": upstream.get("content_type") if isinstance(upstream, Mapping) else None,
        "body_suppressed": True,
    }
    base: Dict[str, Any] = {
        "source_name": source_name,
        "action_name": action_name,
        "service_ok": service_payload.get("ok"),
        "response_mode": service_payload.get("response_mode") or RESPONSE_MODE_PASSTHROUGH,
        "http_status": http_status,
        "latency_ms": latency_ms,
        "output_scope": DEFAULT_OUTPUT_SCOPE,
        "field_classification": _field_classification_summary(),
        "upstream": upstream_summary,
        "raw_body_suppressed": True,
        "source_provenance": "browser_backed_service",
        "sensitive_output": False,
        "unexpected_summary_fields": unexpected_summary_fields,
    }

    safety = service_payload.get("safety") if isinstance(service_payload.get("safety"), Mapping) else {}
    credential_material_output = safety.get("credential_material_output") if isinstance(safety, Mapping) else None
    if credential_material_output is not False:
        base.update(
            {
                "source_status": "blocked",
                "failure_layer": "sensitive_output_policy",
                "error_type": "credential_material_violation",
                "credential_material_violation": True,
                "normalized_observation": {
                    "source_name": source_name,
                    "source_status": "blocked",
                    "error_type": "credential_material_violation",
                    "raw_body_suppressed": True,
                },
            }
        )
        return base

    base["safety"] = {"credential_material_output": False}
    service_error_type = service_payload.get("error_type")
    if service_error_type is None and isinstance(upstream, Mapping):
        service_error_type = upstream.get("error_type")
    if service_payload.get("ok") is False and service_error_type:
        source_status, failure_layer = _normalize_passthrough_service_failure(service_error_type)
        base.update(
            {
                "source_status": source_status,
                "failure_layer": failure_layer,
                "error_type": service_error_type,
                "normalized_observation": {
                    "source_name": source_name,
                    "source_status": source_status,
                    "error_type": service_error_type,
                    "raw_body_suppressed": True,
                },
            }
        )
        return base

    if not isinstance(upstream, Mapping) or "body" not in upstream or upstream.get("body") is None:
        if service_payload.get("ok") is not True:
            source_status, failure_layer = _normalize_passthrough_service_failure(service_error_type or "passthrough_failed")
            base.update(
                {
                    "source_status": source_status,
                    "failure_layer": failure_layer,
                    "error_type": service_error_type or "passthrough_failed",
                    "normalized_observation": {
                        "source_name": source_name,
                        "source_status": source_status,
                        "error_type": service_error_type or "passthrough_failed",
                        "raw_body_suppressed": True,
                    },
                }
            )
            return base
        base.update(
            {
                "source_status": "parse_error",
                "failure_layer": "parser",
                "error_type": "passthrough_body_missing",
                "normalized_observation": {
                    "source_name": source_name,
                    "source_status": "parse_error",
                    "error_type": "passthrough_body_missing",
                    "raw_body_suppressed": True,
                },
            }
        )
        return base

    normalized_observation = parse_passthrough_response(action_name, upstream.get("body"))
    normalized_status, failure_layer = _normalize_status(
        str(normalized_observation.get("source_status") or "completed"),
        normalized_observation.get("error_type"),
    )
    base.update(
        {
            "source_status": normalized_status,
            "failure_layer": failure_layer,
            "error_type": normalized_observation.get("error_type"),
            "normalized_observation": normalized_observation,
            "no_data_not_risk_exclusion": bool(normalized_observation.get("no_data_not_risk_exclusion")),
        }
    )
    return base


def _normalize_passthrough_service_failure(error_type: Any) -> tuple[str, str]:
    error = str(error_type or "").strip().lower()
    if error in {"auth_failed", "auth_redirect", "auth_required", "login_page", "landing_flow_blocked"}:
        return "auth_failed", "auth_session"
    if error in {"timeout", "service_timeout", "navigation_timeout"}:
        return "timeout", "service_transport"
    if error in {"invalid_parameter", "parameter_error"}:
        return "invalid_parameter", "parameter_contract"
    return "blocked", "source_or_service"


def parse_passthrough_response(action_name: str, upstream_body: Any) -> Dict[str, Any]:
    """Parse passthrough upstream.body into a Dennis normalized observation."""

    _validate_action_name(action_name)
    parser = PASSTHROUGH_PARSER_REGISTRY.get(action_name)
    if parser is None:
        return {
            "source_name": ACTION_TO_SOURCE[action_name],
            "source_status": "blocked",
            "error_type": "unsupported_passthrough_parser",
            "fields_observed": _observed_field_names(_coerce_json_body(upstream_body)),
            "raw_body_suppressed": True,
        }
    return parser(upstream_body)


def _parse_track_analysis_passthrough(upstream_body: Any) -> Dict[str, Any]:
    body = _coerce_json_body(upstream_body)
    source_name = "track_analysis_summary"
    if not isinstance(body, (Mapping, list)):
        return {
            "source_name": source_name,
            "source_status": "parse_error",
            "error_type": "passthrough_body_not_structured_json",
            "fields_observed": [],
            "samples": [],
            "raw_body_suppressed": True,
        }

    sub_interface = _detect_track_sub_interface(body)
    rows = _extract_row_mappings(body)
    device_ids = _extract_device_ids(body)
    fields_observed = _observed_field_names(body)
    samples = _track_analysis_samples(body, rows, device_ids, sub_interface)
    record_count = _infer_record_count(body, rows, device_ids)
    observation: Dict[str, Any] = {
        "source_name": source_name,
        "source_status": "completed" if record_count > 0 else "no_data",
        "entity": _extract_passthrough_entity(body),
        "sub_interface": sub_interface,
        "fields_observed": fields_observed,
        "records_count": record_count,
        "samples": samples,
        "raw_body_suppressed": True,
        "no_data_not_risk_exclusion": True,
    }
    if rows:
        observation["rows_count"] = len(rows)
    if device_ids:
        observation["device_ids_count"] = len(device_ids)
    return observation


def _parse_login_logs_passthrough(upstream_body: Any) -> Dict[str, Any]:
    body = _coerce_json_body(upstream_body)
    source_name = "login_logs_search"
    if not isinstance(body, (Mapping, list)):
        return {
            "source_name": source_name,
            "source_status": "parse_error",
            "error_type": "passthrough_body_not_structured_json",
            "records_count": 0,
            "fields_observed": [],
            "samples": [],
            "raw_records_suppressed": True,
            "no_data_not_risk_exclusion": True,
        }

    records = _extract_login_log_records(body)
    return {
        "source_name": source_name,
        "source_status": "completed" if records else "no_data",
        "records_count": len(records),
        "fields_observed": _observed_field_names(records if records else body),
        "samples": [_login_log_sample(record) for record in records[:3]],
        "raw_records_suppressed": True,
        "no_data_not_risk_exclusion": True,
    }


PASSTHROUGH_PARSER_REGISTRY.update(
    {
        "track_analysis_summary": _parse_track_analysis_passthrough,
        "login_logs_search": _parse_login_logs_passthrough,
    }
)


def _extract_passthrough_latency_ms(service_payload: Mapping[str, Any]) -> Optional[int]:
    meta = service_payload.get("meta") if isinstance(service_payload.get("meta"), Mapping) else {}
    value = meta.get("latency_ms") if isinstance(meta, Mapping) else None
    if value is None:
        value = service_payload.get("latency_ms")
    return int(value) if isinstance(value, (int, float)) else None


def _coerce_json_body(value: Any) -> Any:
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return ""
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            return value
    return value


def _observed_field_names(value: Any, max_fields: int = 64) -> list[str]:
    fields: list[str] = []

    def visit(node: Any, prefix: str = "") -> None:
        if len(fields) >= max_fields:
            return
        if isinstance(node, Mapping):
            for key, child in node.items():
                key_text = str(key)
                lowered = key_text.lower()
                if lowered in FORBIDDEN_INPUT_KEYS or _is_credential_secret_key(key_text) or not _is_safe_display_key(key_text):
                    continue
                path = f"{prefix}.{key_text}" if prefix else key_text
                if path not in fields:
                    fields.append(path)
                if isinstance(child, (Mapping, list)):
                    visit(child, path)
                if len(fields) >= max_fields:
                    return
        elif isinstance(node, list):
            for item in node[:3]:
                visit(item, prefix)
                if len(fields) >= max_fields:
                    return

    visit(value)
    return fields


def _extract_passthrough_entity(body: Any) -> Dict[str, Any]:
    entity: Dict[str, Any] = {}
    for key in ("user_id", "userId", "uid", "device_id", "deviceId", "did", "appName", "product"):
        value = _find_first(body, (key,))
        if value is not None:
            entity[key] = _safe_display_value(key, value, DEFAULT_OUTPUT_SCOPE)
    return entity


def _detect_track_sub_interface(body: Any) -> Optional[str]:
    for key in ("sub_interface", "subInterface", "interface", "func", "function", "mode"):
        value = _find_first(body, (key,))
        if isinstance(value, str) and value in ACCOUNT_SECURITY_TRACK_SUB_INTERFACES:
            return value
    if _extract_device_ids(body):
        return "getDeviceIds"
    if _find_first(body, ("latestDateTime", "latest_datetime", "lastestDateTime", "getLastestDateTime")) is not None:
        return "getLastestDateTime"
    if _find_first(body, ("useDuration", "duration", "totalDuration", "activeDuration", "getUseDuration")) is not None:
        return "getUseDuration"
    if _find_first(body, ("registerTime", "activeDays", "fanDistribution", "userProfile", "profile")) is not None:
        return "profile"
    return None


def _extract_row_mappings(value: Any) -> list[Mapping[str, Any]]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, Mapping)]
    if not isinstance(value, Mapping):
        return []
    for key in ("rows", "records", "dataList", "list", "items", "result"):
        child = value.get(key)
        if isinstance(child, list):
            return [item for item in child if isinstance(item, Mapping)]
    data = value.get("data")
    if isinstance(data, list):
        return [item for item in data if isinstance(item, Mapping)]
    if isinstance(data, Mapping):
        nested = _extract_row_mappings(data)
        if nested:
            return nested
    return []


def _extract_device_ids(value: Any) -> list[Any]:
    candidates: list[Any] = []
    found = _find_first(value, ("deviceIds", "device_ids", "deviceIdList", "didList"))
    if isinstance(found, list):
        candidates.extend(found)
    elif isinstance(found, (str, int)):
        candidates.append(found)
    for row in _extract_row_mappings(value):
        for key in ("device_id", "deviceId", "did", "DID"):
            if key in row and row.get(key) is not None:
                candidates.append(row.get(key))
    unique: list[Any] = []
    for item in candidates:
        if isinstance(item, (str, int)) and item not in unique:
            unique.append(item)
    return unique


def _track_analysis_samples(
    body: Any,
    rows: list[Mapping[str, Any]],
    device_ids: list[Any],
    sub_interface: Optional[str],
) -> list[Dict[str, Any]]:
    samples: list[Dict[str, Any]] = []
    if device_ids:
        samples.append({"device_id_sample": _safe_display_value("device_id", device_ids[0], DEFAULT_OUTPUT_SCOPE)})
    if rows:
        samples.extend(_safe_passthrough_sample(row, ("date", "duration", "totalDuration", "deviceId", "device_id")) for row in rows[:2])
    if sub_interface in {"profile", None} and isinstance(body, Mapping):
        profile_sample = _safe_passthrough_sample(
            body,
            ("user_id", "userId", "registerTime", "activeDays", "fanDistribution", "deviceIds"),
        )
        if profile_sample:
            samples.append(profile_sample)
    latest = _find_first(body, ("latestDateTime", "latest_datetime", "lastestDateTime"))
    if latest is not None:
        samples.append({"latest_datetime_sample": _safe_display_value("timestamp", latest, DEFAULT_OUTPUT_SCOPE)})
    return [sample for sample in samples if sample]


def _infer_record_count(body: Any, rows: list[Mapping[str, Any]], device_ids: list[Any]) -> int:
    if rows:
        return len(rows)
    if device_ids:
        return len(device_ids)
    if isinstance(body, list):
        return len(body)
    if isinstance(body, Mapping):
        data = body.get("data")
        if isinstance(data, Mapping) and data:
            return 1
        if isinstance(data, list):
            return len(data)
        return 1 if body else 0
    return 0


def _extract_login_log_records(body: Any) -> list[Mapping[str, Any]]:
    if isinstance(body, list):
        return [item for item in body if isinstance(item, Mapping)]
    if not isinstance(body, Mapping):
        return []
    data = body.get("data")
    if isinstance(data, Mapping) and isinstance(data.get("logSearchModels"), list):
        return [item for item in data["logSearchModels"] if isinstance(item, Mapping)]
    if isinstance(body.get("logSearchModels"), list):
        return [item for item in body["logSearchModels"] if isinstance(item, Mapping)]
    return []


def _login_log_sample(record: Mapping[str, Any]) -> Dict[str, Any]:
    sample_fields = {
        "logSource": ("logSource", "log_source"),
        "method": ("method", "loginMethod", "login_method"),
        "timestamp": ("timestamp", "time", "loginTime", "logTime", "createTime"),
        "user_id": ("user_id", "userId", "uid"),
        "device_id": ("device_id", "deviceId", "did", "DID"),
        "IP": ("IP", "ip", "userIp", "userIpDesc", "clientIp", "remoteIp"),
    }
    sample: Dict[str, Any] = {}
    for output_key, candidates in sample_fields.items():
        value = _find_first(record, candidates)
        if value is not None:
            sample[output_key] = _safe_display_value(output_key, value, DEFAULT_OUTPUT_SCOPE)
    return sample


def _safe_passthrough_sample(value: Mapping[str, Any], candidate_keys: Iterable[str]) -> Dict[str, Any]:
    sample: Dict[str, Any] = {}
    for key in candidate_keys:
        found = _find_first(value, (key,))
        if found is not None:
            sample[key] = _safe_display_value(key, found, DEFAULT_OUTPUT_SCOPE)
    return sample


def _attach_track_analysis_check_data_ready_contract_fields(
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
            ("device_id", "deviceId", "appName", "product", "startTime", "endTime"),
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
        next_action = "Use readiness only as source-quality context; run profile/use-duration/device/latest source actions for evidence."

    normalized["key_entities"] = _sanitize_display_material(key_entities, output_scope)
    normalized["missing_fields"] = _sanitize_display_material(missing_fields, output_scope)
    normalized["next_action"] = _safe_display_value("next_action", next_action, output_scope)
    normalized["no_data_not_risk_exclusion"] = True
    if isinstance(normalized.get("source_quality"), Mapping):
        quality = dict(normalized["source_quality"])
        quality.setdefault("track_analysis_action_contract", "track_analysis_check_data_ready")
        quality["no_data_not_risk_exclusion"] = True
        quality.setdefault("raw_response_full_body_returned", False)
        quality.setdefault("raw_readiness_body_suppressed", True)
        quality.setdefault("trace_id_value_suppressed", True)
        quality.setdefault("readiness_not_evidence", True)
        normalized["source_quality"] = quality
    if isinstance(normalized.get("source_card"), Mapping):
        card = dict(normalized["source_card"])
        card.setdefault("key_entities", normalized["key_entities"])
        card.setdefault("missing_fields", normalized["missing_fields"])
        card.setdefault("next_action", normalized["next_action"])
        normalized["source_card"] = card


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


def _attach_archives_photo_search_contract_fields(
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
            ("user_id", "userId", "reportedIds", "photo_ids", "photoIds", "photo_id", "photoId", "live_id", "liveId"),
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
        next_action = "Use photo search as a content/report signal; cross-check publish detail, audit logs, and account timeline."

    normalized["key_entities"] = _sanitize_display_material(key_entities, output_scope)
    normalized["missing_fields"] = _sanitize_display_material(missing_fields, output_scope)
    normalized["next_action"] = _safe_display_value("next_action", next_action, output_scope)
    normalized["no_data_not_risk_exclusion"] = True
    if isinstance(normalized.get("source_quality"), Mapping):
        quality = dict(normalized["source_quality"])
        quality.setdefault("archives_action_contract", "archives_photo_search")
        quality["no_data_not_risk_exclusion"] = True
        quality.setdefault("raw_response_full_body_returned", False)
        quality.setdefault("raw_report_text_suppressed", True)
        normalized["source_quality"] = quality
    if isinstance(normalized.get("source_card"), Mapping):
        card = dict(normalized["source_card"])
        card.setdefault("key_entities", normalized["key_entities"])
        card.setdefault("missing_fields", normalized["missing_fields"])
        card.setdefault("next_action", normalized["next_action"])
        normalized["source_card"] = card


def _attach_archives_user_profile_contract_fields(
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
            ("user_id", "userId", "uid", "device_id", "deviceId", "did", "ip", "userIpDesc"),
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
        next_action = "Use Archives user profile as account baseline; cross-check action logs and external evidence before judgement."

    normalized["key_entities"] = _sanitize_display_material(key_entities, output_scope)
    normalized["missing_fields"] = _sanitize_display_material(missing_fields, output_scope)
    normalized["next_action"] = _safe_display_value("next_action", next_action, output_scope)
    normalized["no_data_not_risk_exclusion"] = True
    if isinstance(normalized.get("source_quality"), Mapping):
        quality = dict(normalized["source_quality"])
        quality.setdefault("archives_action_contract", "archives_user_profile")
        quality["no_data_not_risk_exclusion"] = True
        quality.setdefault("raw_response_full_body_returned", False)
        quality.setdefault("raw_profile_body_suppressed", True)
        normalized["source_quality"] = quality
    if isinstance(normalized.get("source_card"), Mapping):
        card = dict(normalized["source_card"])
        card.setdefault("key_entities", normalized["key_entities"])
        card.setdefault("missing_fields", normalized["missing_fields"])
        card.setdefault("next_action", normalized["next_action"])
        normalized["source_card"] = card


def _attach_archives_related_users_contract_fields(
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
            ("user_id", "userId", "related_user_ids", "relatedUserIds", "device_id", "deviceId", "did"),
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
        next_action = "Use related users only as expansion candidates; validate each related account before judgement."

    normalized["key_entities"] = _sanitize_display_material(key_entities, output_scope)
    normalized["missing_fields"] = _sanitize_display_material(missing_fields, output_scope)
    normalized["next_action"] = _safe_display_value("next_action", next_action, output_scope)
    normalized["no_data_not_risk_exclusion"] = True
    if isinstance(normalized.get("source_quality"), Mapping):
        quality = dict(normalized["source_quality"])
        quality.setdefault("archives_action_contract", "archives_related_users")
        quality["no_data_not_risk_exclusion"] = True
        quality.setdefault("raw_response_full_body_returned", False)
        quality.setdefault("raw_related_user_profile_suppressed", True)
        normalized["source_quality"] = quality
    if isinstance(normalized.get("source_card"), Mapping):
        card = dict(normalized["source_card"])
        card.setdefault("key_entities", normalized["key_entities"])
        card.setdefault("missing_fields", normalized["missing_fields"])
        card.setdefault("next_action", normalized["next_action"])
        normalized["source_card"] = card


def _attach_archives_private_message_search_contract_fields(
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
            ("user_id", "userId", "fromUserId", "toUserId", "counterpart_user_ids", "counterpartUserIds"),
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
        next_action = "Use private-message summary only as social-interaction context; do not output plaintext."

    normalized["key_entities"] = _sanitize_display_material(key_entities, output_scope)
    normalized["missing_fields"] = _sanitize_display_material(missing_fields, output_scope)
    normalized["next_action"] = _safe_display_value("next_action", next_action, output_scope)
    normalized["no_data_not_risk_exclusion"] = True
    if isinstance(normalized.get("source_quality"), Mapping):
        quality = dict(normalized["source_quality"])
        quality.setdefault("archives_action_contract", "archives_private_message_search")
        quality["no_data_not_risk_exclusion"] = True
        quality.setdefault("raw_response_full_body_returned", False)
        quality.setdefault("raw_message_plaintext_suppressed", True)
        quality.setdefault("private_message_summary_not_final_judgement", True)
        normalized["source_quality"] = quality
    if isinstance(normalized.get("source_card"), Mapping):
        card = dict(normalized["source_card"])
        card.setdefault("key_entities", normalized["key_entities"])
        card.setdefault("missing_fields", normalized["missing_fields"])
        card.setdefault("next_action", normalized["next_action"])
        normalized["source_card"] = card


def _attach_archives_past_four_items_contract_fields(
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
        key_entities = _pick_fields(material, ("user_id", "userId", "keyword"), output_scope)
    missing_fields = service_payload.get("missing_fields")
    if not isinstance(missing_fields, list):
        missing_fields = _find_first(material, ("missing_fields", "fields_missing", "required_fields_missing"), output_scope)
    if not isinstance(missing_fields, list):
        missing_fields = []
    next_action = service_payload.get("next_action")
    if not isinstance(next_action, str) or not next_action:
        next_action = _find_first(material, ("next_action",), output_scope)
    if not isinstance(next_action, str) or not next_action:
        next_action = "Use four-info change logs as profile-change timeline only; cross-check with login/publish evidence."

    normalized["key_entities"] = _sanitize_display_material(key_entities, output_scope)
    normalized["missing_fields"] = _sanitize_display_material(missing_fields, output_scope)
    normalized["next_action"] = _safe_display_value("next_action", next_action, output_scope)
    normalized["no_data_not_risk_exclusion"] = True
    if isinstance(normalized.get("source_quality"), Mapping):
        quality = dict(normalized["source_quality"])
        quality.setdefault("archives_action_contract", "archives_past_four_items")
        quality["no_data_not_risk_exclusion"] = True
        quality.setdefault("raw_response_full_body_returned", False)
        quality.setdefault("raw_old_new_profile_content_suppressed", True)
        quality.setdefault("raw_media_url_suppressed", True)
        quality.setdefault("four_info_change_log_not_final_judgement", True)
        normalized["source_quality"] = quality
    if isinstance(normalized.get("source_card"), Mapping):
        card = dict(normalized["source_card"])
        card.setdefault("key_entities", normalized["key_entities"])
        card.setdefault("missing_fields", normalized["missing_fields"])
        card.setdefault("next_action", normalized["next_action"])
        normalized["source_card"] = card


def _attach_rcp_event_detail_contract_fields(
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
            (
                "eventId",
                "eventType",
                "sourceId",
                "deviceId",
                "ip",
                "userRegisterIp",
                "policyCode",
                "policy_codes",
                "hitFusePolicyCode",
            ),
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
        next_action = "Use event detail only as single-event strategy evidence; call feature/policy attribution only with required upstream ids."

    normalized["key_entities"] = _sanitize_display_material(key_entities, output_scope)
    normalized["missing_fields"] = _sanitize_display_material(missing_fields, output_scope)
    normalized["next_action"] = _safe_display_value("next_action", next_action, output_scope)
    normalized["no_data_not_risk_exclusion"] = True
    if isinstance(normalized.get("source_quality"), Mapping):
        quality = dict(normalized["source_quality"])
        quality.setdefault("rcp_action_contract", "rcp_event_detail")
        quality["no_data_not_risk_exclusion"] = True
        quality.setdefault("raw_response_full_body_returned", False)
        quality.setdefault("raw_detail_body_suppressed", True)
        quality.setdefault("strategy_event_not_final_judgement", True)
        normalized["source_quality"] = quality
    if isinstance(normalized.get("source_card"), Mapping):
        card = dict(normalized["source_card"])
        card.setdefault("key_entities", normalized["key_entities"])
        card.setdefault("missing_fields", normalized["missing_fields"])
        card.setdefault("next_action", normalized["next_action"])
        normalized["source_card"] = card


def _attach_rcp_event_feature_list_contract_fields(
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
            ("eventId", "eventType", "sourceId", "policyCode", "policy_codes", "hitFusePolicyCode"),
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
        next_action = "Use feature snapshot for attribution context only; do not output raw feature values."

    normalized["key_entities"] = _sanitize_display_material(key_entities, output_scope)
    normalized["missing_fields"] = _sanitize_display_material(missing_fields, output_scope)
    normalized["next_action"] = _safe_display_value("next_action", next_action, output_scope)
    normalized["no_data_not_risk_exclusion"] = True
    if isinstance(normalized.get("source_quality"), Mapping):
        quality = dict(normalized["source_quality"])
        quality.setdefault("rcp_action_contract", "rcp_event_feature_list")
        quality["no_data_not_risk_exclusion"] = True
        quality.setdefault("raw_response_full_body_returned", False)
        quality.setdefault("raw_feature_values_suppressed", True)
        quality.setdefault("strategy_feature_snapshot_not_final_judgement", True)
        normalized["source_quality"] = quality
    if isinstance(normalized.get("source_card"), Mapping):
        card = dict(normalized["source_card"])
        card.setdefault("key_entities", normalized["key_entities"])
        card.setdefault("missing_fields", normalized["missing_fields"])
        card.setdefault("next_action", normalized["next_action"])
        normalized["source_card"] = card


def _attach_rcp_policy_version_lookup_contract_fields(
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
            ("eventId", "eventType", "policyCode", "policyVersion", "policy_codes", "snapshotVersion"),
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
        next_action = "Use policy version context only for attribution prerequisites; do not treat version existence as risk judgement."

    normalized["key_entities"] = _sanitize_display_material(key_entities, output_scope)
    normalized["missing_fields"] = _sanitize_display_material(missing_fields, output_scope)
    normalized["next_action"] = _safe_display_value("next_action", next_action, output_scope)
    normalized["no_data_not_risk_exclusion"] = True
    if isinstance(normalized.get("source_quality"), Mapping):
        quality = dict(normalized["source_quality"])
        quality.setdefault("rcp_action_contract", "rcp_policy_version_lookup")
        quality["no_data_not_risk_exclusion"] = True
        quality.setdefault("raw_response_full_body_returned", False)
        quality.setdefault("raw_policy_version_body_suppressed", True)
        quality.setdefault("policy_version_not_final_judgement", True)
        normalized["source_quality"] = quality
    if isinstance(normalized.get("source_card"), Mapping):
        card = dict(normalized["source_card"])
        card.setdefault("key_entities", normalized["key_entities"])
        card.setdefault("missing_fields", normalized["missing_fields"])
        card.setdefault("next_action", normalized["next_action"])
        normalized["source_card"] = card


def _attach_rcp_policy_detail_lookup_contract_fields(
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
            (
                "policyCode",
                "policyVersion",
                "eventTypeCode",
                "policyTreeCode",
                "policyTreeVersion",
                "policy_codes",
            ),
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
        next_action = "Use policy detail for strategy-governance context only; do not output raw condition expressions."

    normalized["key_entities"] = _sanitize_display_material(key_entities, output_scope)
    normalized["missing_fields"] = _sanitize_display_material(missing_fields, output_scope)
    normalized["next_action"] = _safe_display_value("next_action", next_action, output_scope)
    normalized["no_data_not_risk_exclusion"] = True
    if isinstance(normalized.get("source_quality"), Mapping):
        quality = dict(normalized["source_quality"])
        quality.setdefault("rcp_action_contract", "rcp_policy_detail_lookup")
        quality["no_data_not_risk_exclusion"] = True
        quality.setdefault("raw_response_full_body_returned", False)
        quality.setdefault("raw_policy_detail_body_suppressed", True)
        quality.setdefault("raw_condition_expression_suppressed", True)
        quality.setdefault("policy_detail_not_final_judgement", True)
        normalized["source_quality"] = quality
    if isinstance(normalized.get("source_card"), Mapping):
        card = dict(normalized["source_card"])
        card.setdefault("key_entities", normalized["key_entities"])
        card.setdefault("missing_fields", normalized["missing_fields"])
        card.setdefault("next_action", normalized["next_action"])
        normalized["source_card"] = card


def _attach_rcp_policy_release_record_lookup_contract_fields(
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
            (
                "policyCode",
                "statusCode",
                "business_union_key_count",
                "parsed_policy_versions",
                "pipeline_versions",
            ),
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
        next_action = "Use release records for policy lifecycle provenance only; do not treat release status as risk judgement."

    normalized["key_entities"] = _sanitize_display_material(key_entities, output_scope)
    normalized["missing_fields"] = _sanitize_display_material(missing_fields, output_scope)
    normalized["next_action"] = _safe_display_value("next_action", next_action, output_scope)
    normalized["no_data_not_risk_exclusion"] = True
    if isinstance(normalized.get("source_quality"), Mapping):
        quality = dict(normalized["source_quality"])
        quality.setdefault("rcp_action_contract", "rcp_policy_release_record_lookup")
        quality["no_data_not_risk_exclusion"] = True
        quality.setdefault("raw_response_full_body_returned", False)
        quality.setdefault("raw_release_records_suppressed", True)
        quality.setdefault("operator_identity_suppressed", True)
        quality.setdefault("release_record_not_final_judgement", True)
        quality.setdefault("pipelineVersion_not_policy_version", True)
        normalized["source_quality"] = quality
    if isinstance(normalized.get("source_card"), Mapping):
        card = dict(normalized["source_card"])
        card.setdefault("key_entities", normalized["key_entities"])
        card.setdefault("missing_fields", normalized["missing_fields"])
        card.setdefault("next_action", normalized["next_action"])
        normalized["source_card"] = card


def _attach_rcp_policy_tree_lookup_contract_fields(
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
            (
                "policyTreeCode",
                "policyTreeVersion",
                "policyTreeNodeCode",
                "targetPolicyCode",
                "policyCode",
                "policy_codes",
            ),
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
        next_action = "Use queryProPolicyTree for node resolution; never guess policyTreeNodeCode from policyCode or node name."

    normalized["key_entities"] = _sanitize_display_material(key_entities, output_scope)
    normalized["missing_fields"] = _sanitize_display_material(missing_fields, output_scope)
    normalized["next_action"] = _safe_display_value("next_action", next_action, output_scope)
    normalized["no_data_not_risk_exclusion"] = True
    if isinstance(normalized.get("source_quality"), Mapping):
        quality = dict(normalized["source_quality"])
        quality.setdefault("rcp_action_contract", "rcp_policy_tree_lookup")
        quality["no_data_not_risk_exclusion"] = True
        quality.setdefault("raw_response_full_body_returned", False)
        quality.setdefault("raw_policy_tree_body_suppressed", True)
        quality.setdefault("raw_node_binding_list_suppressed", True)
        quality.setdefault("raw_all_policy_code_list_suppressed", True)
        quality.setdefault("policyTreeList_is_coarse_filter", True)
        quality.setdefault("policy_tree_not_final_judgement", True)
        normalized["source_quality"] = quality
    if isinstance(normalized.get("source_card"), Mapping):
        card = dict(normalized["source_card"])
        card.setdefault("key_entities", normalized["key_entities"])
        card.setdefault("missing_fields", normalized["missing_fields"])
        card.setdefault("next_action", normalized["next_action"])
        normalized["source_card"] = card


def _attach_rcp_node_policy_attribution_contract_fields(
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
            (
                "eventId",
                "eventType",
                "policyCode",
                "policyVersion",
                "policyTreeNodeCode",
                "sourceId",
                "deviceId",
            ),
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
        next_action = "Use condition-level attribution as policy explanation only; do not emit raw condition/feature dumps."

    normalized["key_entities"] = _sanitize_display_material(key_entities, output_scope)
    normalized["missing_fields"] = _sanitize_display_material(missing_fields, output_scope)
    normalized["next_action"] = _safe_display_value("next_action", next_action, output_scope)
    normalized["no_data_not_risk_exclusion"] = True
    if isinstance(normalized.get("source_quality"), Mapping):
        quality = dict(normalized["source_quality"])
        quality.setdefault("rcp_action_contract", "rcp_node_policy_attribution")
        quality["no_data_not_risk_exclusion"] = True
        quality.setdefault("raw_response_full_body_returned", False)
        quality.setdefault("raw_condition_dump_suppressed", True)
        quality.setdefault("raw_feature_values_suppressed", True)
        quality.setdefault("policy_attribution_not_final_judgement", True)
        normalized["source_quality"] = quality
    if isinstance(normalized.get("source_card"), Mapping):
        card = dict(normalized["source_card"])
        card.setdefault("key_entities", normalized["key_entities"])
        card.setdefault("missing_fields", normalized["missing_fields"])
        card.setdefault("next_action", normalized["next_action"])
        normalized["source_card"] = card


def _attach_rcp_node_bind_policy_attribution_contract_fields(
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
            (
                "eventId",
                "eventType",
                "policyTreeCode",
                "policyTreeVersion",
                "policyTreeNodeCode",
                "targetPolicyCode",
                "effectivePolicy",
                "policyCode",
            ),
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
        next_action = "Use node-binding attribution only as strategy-tree explanation; do not emit raw condition or binding dumps."

    normalized["key_entities"] = _sanitize_display_material(key_entities, output_scope)
    normalized["missing_fields"] = _sanitize_display_material(missing_fields, output_scope)
    normalized["next_action"] = _safe_display_value("next_action", next_action, output_scope)
    normalized["no_data_not_risk_exclusion"] = True
    if isinstance(normalized.get("source_quality"), Mapping):
        quality = dict(normalized["source_quality"])
        quality.setdefault("rcp_action_contract", "rcp_node_bind_policy_attribution")
        quality["no_data_not_risk_exclusion"] = True
        quality.setdefault("raw_response_full_body_returned", False)
        quality.setdefault("raw_node_binding_body_suppressed", True)
        quality.setdefault("raw_condition_dump_suppressed", True)
        quality.setdefault("node_binding_attribution_not_final_judgement", True)
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
    if action == "track_analysis_check_data_ready":
        return _track_analysis_check_data_ready_summary(result, scope)
    if action == "rcp_snapshot":
        return _rcp_summary(result, scope)
    if action == "weapon_inventory":
        return _weapon_summary(result, scope)
    if action == "login_logs_search":
        return _login_logs_summary(result, scope)
    if action == "archives_user_analysis":
        return _archives_user_analysis_summary(result, scope)
    if action == "archives_photo_search":
        return _archives_photo_search_summary(result, scope)
    if action == "archives_user_profile":
        return _archives_user_profile_summary(result, scope)
    if action == "archives_related_users":
        return _archives_related_users_summary(result, scope)
    if action == "archives_private_message_search":
        return _archives_private_message_search_summary(result, scope)
    if action == "archives_past_four_items":
        return _archives_past_four_items_summary(result, scope)
    if action == "rcp_event_detail":
        return _rcp_event_detail_summary(result, scope)
    if action == "rcp_event_feature_list":
        return _rcp_event_feature_list_summary(result, scope)
    if action == "rcp_policy_version_lookup":
        return _rcp_policy_version_lookup_summary(result, scope)
    if action == "rcp_policy_detail_lookup":
        return _rcp_policy_detail_lookup_summary(result, scope)
    if action == "rcp_policy_release_record_lookup":
        return _rcp_policy_release_record_lookup_summary(result, scope)
    if action == "rcp_policy_tree_lookup":
        return _rcp_policy_tree_lookup_summary(result, scope)
    if action == "rcp_node_policy_attribution":
        return _rcp_node_policy_attribution_summary(result, scope)
    if action == "rcp_node_bind_policy_attribution":
        return _rcp_node_bind_policy_attribution_summary(result, scope)
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
            r"(user_?ids?|^uid$|device_?ids?|deviceid|device_did|^did$|(^|_)ip($|_)|ipaddr|ipdesc|clientip|remoteip|loginip|registerip|event_?id|eventtype|source_?id|photo_?id|live_?id|livestreamid|policy_?codes?|policycode|policytree|policyversion|businessunionkey|hitfusepolicycode|strategy|logsource|method|timestamp|occur_?time|_occurtime)",
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


def _track_analysis_check_data_ready_summary(result: Mapping[str, Any], output_scope: str) -> Dict[str, Any]:
    material = _summary_material(result, output_scope)
    summary = _base_source_summary(result, "track_analysis_check_data_ready", output_scope)
    summary["action_contract"] = {
        "fixed_path": TRACK_ANALYSIS_CHECK_DATA_READY_FIXED_PATH,
        "same_origin_service_owned": True,
        "method": "POST",
        "funcType": TRACK_ANALYSIS_FUNC_TYPE,
        "service_generated_fields": ["batchQueryId", "_t"],
        "raw_full_body_suppressed": True,
        "trace_id_value_suppressed": True,
    }
    summary["readiness_summary"] = _pick_fields(
        material,
        (
            "readiness_status",
            "dateStatus",
            "date_status_present",
            "code",
            "message_summary",
            "trace_id_present",
            "coverage_limitations",
        ),
        output_scope,
    )
    summary["key_entities"] = _pick_fields(
        material,
        ("device_id", "deviceId", "appName", "product", "startTime", "endTime"),
        output_scope,
    )
    summary["missing_fields"] = _pick_fields(
        material,
        ("missing_fields", "fields_missing", "required_fields_missing"),
        output_scope,
    ).get("missing_fields", [])
    summary["next_action"] = _find_first(material, ("next_action",), output_scope) or (
        "Use readiness only as source-quality context; it is not account-security evidence by itself."
    )
    summary["boundary"] = "Track Analysis readiness is provenance/source-quality context, not final evidence or risk judgement."
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


def _archives_photo_search_summary(result: Mapping[str, Any], output_scope: str) -> Dict[str, Any]:
    material = _summary_material(result, output_scope)
    summary = _base_source_summary(result, "archives_photo_search", output_scope)
    summary["action_contract"] = {
        "fixed_path": ARCHIVES_PHOTO_SEARCH_FIXED_PATH,
        "same_origin_service_owned": True,
        "raw_full_body_suppressed": True,
        "raw_report_text_suppressed": True,
    }
    summary["photo_search_summary"] = _pick_fields(
        material,
        (
            "photo_count",
            "totalCount",
            "dataList_length",
            "publish_time_range",
            "status_summary",
            "risk_context_summary",
            "report_reason_summary",
            "pagination_required",
            "coverage_limitations",
        ),
        output_scope,
    )
    summary["key_entities"] = _pick_fields(
        material,
        ("user_id", "userId", "reportedIds", "photo_ids", "photoIds", "photo_id", "photoId", "live_id", "liveId"),
        output_scope,
    )
    summary["missing_fields"] = _pick_fields(
        material,
        ("missing_fields", "fields_missing", "required_fields_missing"),
        output_scope,
    ).get("missing_fields", [])
    summary["next_action"] = _find_first(material, ("next_action",), output_scope) or (
        "Cross-check photo report signal with publish detail, audit log, and account timeline before judgement."
    )
    summary["boundary"] = (
        "Archives photo search is a report/content signal source; reports and no_data are not final risk judgement."
    )
    return summary


def _archives_user_profile_summary(result: Mapping[str, Any], output_scope: str) -> Dict[str, Any]:
    material = _summary_material(result, output_scope)
    summary = _base_source_summary(result, "archives_user_profile", output_scope)
    summary["action_contract"] = {
        "fixed_path": ARCHIVES_USER_PROFILE_FIXED_PATH,
        "same_origin_service_owned": True,
        "raw_full_body_suppressed": True,
        "raw_profile_body_suppressed": True,
    }
    summary["profile_summary"] = _pick_fields(
        material,
        (
            "account_status_summary",
            "registration_summary",
            "profile_state_summary",
            "label_summary",
            "risk_info_summary",
            "shop_status_summary",
            "punish_status_summary",
            "coverage_limitations",
        ),
        output_scope,
    )
    summary["key_entities"] = _pick_fields(
        material,
        ("user_id", "userId", "uid", "device_id", "deviceId", "did", "ip", "userIpDesc"),
        output_scope,
    )
    summary["missing_fields"] = _pick_fields(
        material,
        ("missing_fields", "fields_missing", "required_fields_missing"),
        output_scope,
    ).get("missing_fields", [])
    summary["next_action"] = _find_first(material, ("next_action",), output_scope) or (
        "Cross-check profile baseline with user analysis, login logs, and content/report evidence before judgement."
    )
    summary["boundary"] = (
        "Archives user profile is account baseline evidence; profile labels/status are not final risk judgement by themselves."
    )
    return summary


def _archives_related_users_summary(result: Mapping[str, Any], output_scope: str) -> Dict[str, Any]:
    material = _summary_material(result, output_scope)
    summary = _base_source_summary(result, "archives_related_users", output_scope)
    summary["action_contract"] = {
        "fixed_path": ARCHIVES_RELATED_USERS_FIXED_PATH,
        "same_origin_service_owned": True,
        "raw_full_body_suppressed": True,
        "raw_related_user_profile_suppressed": True,
    }
    summary["related_users_summary"] = _pick_fields(
        material,
        (
            "related_user_count",
            "relation_type_summary",
            "same_device_registered_count",
            "same_device_login_count",
            "status_summary",
            "risk_context_summary",
            "pagination_required",
            "coverage_limitations",
        ),
        output_scope,
    )
    summary["key_entities"] = _pick_fields(
        material,
        ("user_id", "userId", "related_user_ids", "relatedUserIds", "device_id", "deviceId", "did"),
        output_scope,
    )
    summary["missing_fields"] = _pick_fields(
        material,
        ("missing_fields", "fields_missing", "required_fields_missing"),
        output_scope,
    ).get("missing_fields", [])
    summary["next_action"] = _find_first(material, ("next_action",), output_scope) or (
        "Treat same-device users as expansion candidates; validate account behavior before judgement."
    )
    summary["boundary"] = (
        "Same-device relation is a clustering clue, not standalone cheating or ATO judgement."
    )
    return summary


def _archives_private_message_search_summary(result: Mapping[str, Any], output_scope: str) -> Dict[str, Any]:
    material = _summary_material(result, output_scope)
    summary = _base_source_summary(result, "archives_private_message_search", output_scope)
    summary["action_contract"] = {
        "fixed_path": ARCHIVES_PRIVATE_MESSAGE_SEARCH_FIXED_PATH,
        "same_origin_service_owned": True,
        "direction_mapping": dict(ARCHIVES_PRIVATE_MESSAGE_DIRECTIONS),
        "raw_full_body_suppressed": True,
        "raw_message_plaintext_suppressed": True,
    }
    summary["private_message_summary"] = _pick_fields(
        material,
        (
            "private_message_count",
            "total",
            "direction_summary",
            "message_time_range",
            "status_summary",
            "counterpart_count",
            "risk_context_summary",
            "pagination_required",
            "coverage_limitations",
        ),
        output_scope,
    )
    summary["key_entities"] = _pick_fields(
        material,
        ("user_id", "userId", "fromUserId", "toUserId", "counterpart_user_ids", "counterpartUserIds"),
        output_scope,
    )
    summary["missing_fields"] = _pick_fields(
        material,
        ("missing_fields", "fields_missing", "required_fields_missing"),
        output_scope,
    ).get("missing_fields", [])
    summary["next_action"] = _find_first(material, ("next_action",), output_scope) or (
        "Use private-message counts/status only; never output plaintext message content."
    )
    summary["boundary"] = "Private-message summary is social-interaction context, not final risk judgement."
    return summary


def _archives_past_four_items_summary(result: Mapping[str, Any], output_scope: str) -> Dict[str, Any]:
    material = _summary_material(result, output_scope)
    summary = _base_source_summary(result, "archives_past_four_items", output_scope)
    summary["action_contract"] = {
        "fixed_path": ARCHIVES_PAST_FOUR_ITEMS_FIXED_PATH,
        "same_origin_service_owned": True,
        "keyword_source": "user_id",
        "infoType_mapping": dict(ARCHIVES_FOUR_INFO_TYPES),
        "raw_full_body_suppressed": True,
        "raw_old_new_profile_content_suppressed": True,
        "raw_media_url_suppressed": True,
    }
    summary["four_info_change_summary"] = _pick_fields(
        material,
        (
            "total_changes",
            "total",
            "change_time_range",
            "info_type_summary",
            "status_summary",
            "profile_change_risk_summary",
            "pagination_required",
            "coverage_limitations",
        ),
        output_scope,
    )
    summary["key_entities"] = _pick_fields(material, ("user_id", "userId", "keyword"), output_scope)
    summary["missing_fields"] = _pick_fields(
        material,
        ("missing_fields", "fields_missing", "required_fields_missing"),
        output_scope,
    ).get("missing_fields", [])
    summary["next_action"] = _find_first(material, ("next_action",), output_scope) or (
        "Align profile-change timeline with login, publish, and report evidence before judgement."
    )
    summary["boundary"] = "Four-info change logs are profile timeline evidence; raw profile text/media never displays."
    return summary


def _rcp_event_detail_summary(result: Mapping[str, Any], output_scope: str) -> Dict[str, Any]:
    material = _summary_material(result, output_scope)
    summary = _base_source_summary(result, "rcp_event_detail", output_scope)
    summary["action_contract"] = {
        "fixed_path": RCP_EVENT_DETAIL_FIXED_PATH,
        "same_origin_service_owned": True,
        "raw_full_body_suppressed": True,
        "raw_detail_body_suppressed": True,
    }
    summary["event_detail_summary"] = _pick_fields(
        material,
        (
            "event_detail_status",
            "occur_time",
            "_occurTime",
            "real_time_feedback",
            "error_code",
            "side_effect_ops_summary",
            "effective_policy_summary",
            "hit_policy_count",
            "hit_policy_codes",
            "policy_exception_summary",
            "coverage_limitations",
        ),
        output_scope,
    )
    summary["key_entities"] = _pick_fields(
        material,
        (
            "eventId",
            "eventType",
            "sourceId",
            "deviceId",
            "ip",
            "userRegisterIp",
            "policyCode",
            "policy_codes",
            "hitFusePolicyCode",
        ),
        output_scope,
    )
    summary["missing_fields"] = _pick_fields(
        material,
        ("missing_fields", "fields_missing", "required_fields_missing"),
        output_scope,
    ).get("missing_fields", [])
    summary["next_action"] = _find_first(material, ("next_action",), output_scope) or (
        "Use exact _occurTime as queryTime for feature snapshot or policy attribution if needed."
    )
    summary["boundary"] = "RCP event detail is single-event strategy evidence, not final risk judgement."
    return summary


def _rcp_event_feature_list_summary(result: Mapping[str, Any], output_scope: str) -> Dict[str, Any]:
    material = _summary_material(result, output_scope)
    summary = _base_source_summary(result, "rcp_event_feature_list", output_scope)
    summary["action_contract"] = {
        "fixed_path": RCP_EVENT_FEATURE_LIST_FIXED_PATH,
        "same_origin_service_owned": True,
        "featureGroup_default": "",
        "raw_full_body_suppressed": True,
        "raw_feature_values_suppressed": True,
    }
    summary["feature_snapshot_summary"] = _pick_fields(
        material,
        (
            "feature_count",
            "feature_group_distribution",
            "feature_key_samples",
            "feature_name_samples",
            "check_result_summary",
            "feature_snapshot_status",
            "coverage_limitations",
        ),
        output_scope,
    )
    summary["key_entities"] = _pick_fields(
        material,
        ("eventId", "eventType", "sourceId", "policyCode", "policy_codes", "hitFusePolicyCode"),
        output_scope,
    )
    summary["missing_fields"] = _pick_fields(
        material,
        ("missing_fields", "fields_missing", "required_fields_missing"),
        output_scope,
    ).get("missing_fields", [])
    summary["next_action"] = _find_first(material, ("next_action",), output_scope) or (
        "Summarize feature groups/keys only; use policy attribution for condition-level explanation."
    )
    summary["boundary"] = "Feature snapshots provide attribution context; raw feature values stay suppressed."
    return summary


def _rcp_policy_version_lookup_summary(result: Mapping[str, Any], output_scope: str) -> Dict[str, Any]:
    material = _summary_material(result, output_scope)
    summary = _base_source_summary(result, "rcp_policy_version_lookup", output_scope)
    summary["action_contract"] = {
        "fixed_path": RCP_POLICY_VERSION_LOOKUP_FIXED_PATH,
        "same_origin_service_owned": True,
        "raw_full_body_suppressed": True,
        "raw_policy_version_body_suppressed": True,
    }
    summary["policy_version_summary"] = _pick_fields(
        material,
        (
            "version_lookup_status",
            "version_found",
            "policyCode",
            "policyVersion",
            "policy_name_summary",
            "policy_type_summary",
            "snapshotVersion",
            "version_metadata_summary",
            "coverage_limitations",
        ),
        output_scope,
    )
    summary["key_entities"] = _pick_fields(
        material,
        ("eventId", "eventType", "policyCode", "policyVersion", "policy_codes", "snapshotVersion"),
        output_scope,
    )
    summary["missing_fields"] = _pick_fields(
        material,
        ("missing_fields", "fields_missing", "required_fields_missing"),
        output_scope,
    ).get("missing_fields", [])
    summary["next_action"] = _find_first(material, ("next_action",), output_scope) or (
        "Use policy version context only as prerequisite for policy attribution."
    )
    summary["boundary"] = "Policy version existence is attribution context, not risk judgement or governance recommendation."
    return summary


def _rcp_policy_detail_lookup_summary(result: Mapping[str, Any], output_scope: str) -> Dict[str, Any]:
    material = _summary_material(result, output_scope)
    summary = _base_source_summary(result, "rcp_policy_detail_lookup", output_scope)
    summary["action_contract"] = {
        "fixed_path": RCP_POLICY_DETAIL_LOOKUP_FIXED_PATH,
        "same_origin_service_owned": True,
        "companion_readonly_paths": [
            "/v2/rest/pro/policy/getPolicyAllVersion",
            "/v2/rest/pc/policyReview/getRelationPolicyTree",
        ],
        "raw_full_body_suppressed": True,
        "raw_policy_detail_body_suppressed": True,
        "raw_condition_expression_suppressed": True,
    }
    summary["policy_detail_summary"] = _pick_fields(
        material,
        (
            "policy_detail_status",
            "policyCode",
            "policyVersion",
            "eventTypeCode",
            "policy_name_summary",
            "policy_status_summary",
            "condition_count",
            "condition_expression_present",
            "punish_summary",
            "version_count",
            "latest_version",
            "relation_policy_tree_count",
            "coverage_limitations",
        ),
        output_scope,
    )
    summary["key_entities"] = _pick_fields(
        material,
        (
            "policyCode",
            "policyVersion",
            "eventTypeCode",
            "policyTreeCode",
            "policyTreeVersion",
            "policy_codes",
        ),
        output_scope,
    )
    summary["missing_fields"] = _pick_fields(
        material,
        ("missing_fields", "fields_missing", "required_fields_missing"),
        output_scope,
    ).get("missing_fields", [])
    summary["next_action"] = _find_first(material, ("next_action",), output_scope) or (
        "Use policy detail as strategy-governance context; use event attribution for a specific hit path."
    )
    summary["boundary"] = "Policy detail explains strategy definition and versions, not final cheating judgement."
    return summary


def _rcp_policy_release_record_lookup_summary(result: Mapping[str, Any], output_scope: str) -> Dict[str, Any]:
    material = _summary_material(result, output_scope)
    summary = _base_source_summary(result, "rcp_policy_release_record_lookup", output_scope)
    summary["action_contract"] = {
        "fixed_path": RCP_POLICY_RELEASE_LIST_FIXED_PATH,
        "same_origin_service_owned": True,
        "companion_readonly_paths": [RCP_POLICY_RELEASE_SELECT_INFO_FIXED_PATH],
        "extrbB_rule": "policyCode exact filter",
        "businessUnionKey_rule": "{policyCode}_{policyVersion}_{eventTypeCode}",
        "pipelineVersion_boundary": "process iteration version, not policy version",
        "raw_full_body_suppressed": True,
        "raw_release_records_suppressed": True,
        "operator_identity_suppressed": True,
    }
    summary["release_record_summary"] = _pick_fields(
        material,
        (
            "release_record_status",
            "policyCode",
            "statusCode",
            "record_count",
            "business_union_key_count",
            "business_union_keys_present",
            "parsed_policy_versions",
            "pipeline_versions",
            "status_distribution",
            "experiment_or_gray_summary",
            "terminal_records",
            "online_acceptance_records",
            "coverage_limitations",
        ),
        output_scope,
    )
    summary["key_entities"] = _pick_fields(
        material,
        ("policyCode", "statusCode", "parsed_policy_versions", "pipeline_versions"),
        output_scope,
    )
    summary["missing_fields"] = _pick_fields(
        material,
        ("missing_fields", "fields_missing", "required_fields_missing"),
        output_scope,
    ).get("missing_fields", [])
    summary["next_action"] = _find_first(material, ("next_action",), output_scope) or (
        "Use release records only as lifecycle provenance; pair with event attribution before explanation."
    )
    summary["boundary"] = "Policy release records explain lifecycle/version changes, not risk or cheating judgement."
    return summary


def _rcp_policy_tree_lookup_summary(result: Mapping[str, Any], output_scope: str) -> Dict[str, Any]:
    material = _summary_material(result, output_scope)
    summary = _base_source_summary(result, "rcp_policy_tree_lookup", output_scope)
    summary["action_contract"] = {
        "fixed_path": RCP_POLICY_TREE_LOOKUP_FIXED_PATH,
        "same_origin_service_owned": True,
        "companion_readonly_paths": [
            RCP_POLICY_TREE_LIST_FIXED_PATH,
            RCP_POLICY_TREE_BINDING_BY_NODE_FIXED_PATH,
            RCP_POLICY_TREE_ALL_POLICY_CODE_FIXED_PATH,
        ],
        "policyTreeList_role": "coarse_filter_only",
        "queryBindingByNodeCode_role": "node_level_binding_policy_list",
        "getAllPolicyCodeByPage_role": "full_tree_policy_code_list",
        "incorrect_path_forbidden": "/v2/rest/pc/policytree/getPolicyTreeByVersion",
        "raw_full_body_suppressed": True,
        "raw_policy_tree_body_suppressed": True,
        "raw_node_binding_list_suppressed": True,
        "raw_all_policy_code_list_suppressed": True,
    }
    summary["policy_tree_summary"] = _pick_fields(
        material,
        (
            "policy_tree_status",
            "policyTreeCode",
            "policyTreeVersion",
            "policyTreeNodeCode",
            "node_name_summary",
            "node_code_source",
            "target_policy_found",
            "policy_tree_depth_summary",
            "policy_tree_list_records_total",
            "node_binding_policy_count",
            "all_policy_code_count",
            "policy_code_sample_count",
            "target_policy_binding_status",
            "coverage_limitations",
        ),
        output_scope,
    )
    summary["key_entities"] = _pick_fields(
        material,
        (
            "policyTreeCode",
            "policyTreeVersion",
            "policyTreeNodeCode",
            "targetPolicyCode",
            "policyCode",
            "policy_codes",
        ),
        output_scope,
    )
    summary["missing_fields"] = _pick_fields(
        material,
        ("missing_fields", "fields_missing", "required_fields_missing"),
        output_scope,
    ).get("missing_fields", [])
    summary["next_action"] = _find_first(material, ("next_action",), output_scope) or (
        "Use resolved policyTreeNodeCode for node binding attribution only when required."
    )
    summary["boundary"] = "Policy tree lookup is strategy-governance context, not final cheating judgement."
    return summary


def _rcp_node_policy_attribution_summary(result: Mapping[str, Any], output_scope: str) -> Dict[str, Any]:
    material = _summary_material(result, output_scope)
    summary = _base_source_summary(result, "rcp_node_policy_attribution", output_scope)
    summary["action_contract"] = {
        "fixed_path": RCP_NODE_POLICY_ATTRIBUTION_FIXED_PATH,
        "same_origin_service_owned": True,
        "fixed_type": "",
        "raw_full_body_suppressed": True,
        "raw_condition_dump_suppressed": True,
        "raw_feature_values_suppressed": True,
    }
    summary["policy_attribution_summary"] = _pick_fields(
        material,
        (
            "attribution_status",
            "policyCode",
            "policyVersion",
            "condition_count",
            "true_condition_count",
            "false_condition_count",
            "condition_result_summary",
            "error_feature_count",
            "node_status_summary",
            "coverage_limitations",
        ),
        output_scope,
    )
    summary["key_entities"] = _pick_fields(
        material,
        (
            "eventId",
            "eventType",
            "policyCode",
            "policyVersion",
            "policyTreeNodeCode",
            "sourceId",
            "deviceId",
        ),
        output_scope,
    )
    summary["missing_fields"] = _pick_fields(
        material,
        ("missing_fields", "fields_missing", "required_fields_missing"),
        output_scope,
    ).get("missing_fields", [])
    summary["next_action"] = _find_first(material, ("next_action",), output_scope) or (
        "Use attribution summary for policy explanation; pair with event evidence before judgement."
    )
    summary["boundary"] = "Condition-level attribution explains a policy result; it is not final cheating judgement."
    return summary


def _rcp_node_bind_policy_attribution_summary(result: Mapping[str, Any], output_scope: str) -> Dict[str, Any]:
    material = _summary_material(result, output_scope)
    summary = _base_source_summary(result, "rcp_node_bind_policy_attribution", output_scope)
    summary["action_contract"] = {
        "fixed_path": RCP_NODE_BIND_POLICY_ATTRIBUTION_FIXED_PATH,
        "same_origin_service_owned": True,
        "policyTreeNodeCode_source_required": "queryProPolicyTree",
        "raw_full_body_suppressed": True,
        "raw_node_binding_body_suppressed": True,
        "raw_condition_dump_suppressed": True,
    }
    summary["node_binding_summary"] = _pick_fields(
        material,
        (
            "node_binding_status",
            "node_name_summary",
            "policyTreeNodeCode",
            "binding_policy_count",
            "effective_policy_summary",
            "target_policy_online",
            "target_policy_result",
            "condition_count",
            "nodebinding_policy_summary",
            "coverage_limitations",
        ),
        output_scope,
    )
    summary["key_entities"] = _pick_fields(
        material,
        (
            "eventId",
            "eventType",
            "policyTreeCode",
            "policyTreeVersion",
            "policyTreeNodeCode",
            "targetPolicyCode",
            "effectivePolicy",
            "policyCode",
        ),
        output_scope,
    )
    summary["missing_fields"] = _pick_fields(
        material,
        ("missing_fields", "fields_missing", "required_fields_missing"),
        output_scope,
    ).get("missing_fields", [])
    summary["next_action"] = _find_first(material, ("next_action",), output_scope) or (
        "Use node binding attribution as policy-tree explanation only; do not make final risk judgement."
    )
    summary["boundary"] = "Node-binding attribution completes policy-tree explanation, not cheating classification."
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
            if normalized_key in CONTROL_INPUT_KEYS:
                raise BrowserBackedServiceInputError(f"browser-backed control key must be passed as an explicit client option: {path}.{key}")
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


def _passthrough_fixture_payload(
    action_name: str,
    upstream_body: Any = None,
    *,
    ok: bool = True,
    error_type: Optional[str] = None,
    include_body: bool = True,
    credential_material_output: bool = False,
    include_summary_fields: bool = False,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "ok": ok,
        "action": action_name,
        "response_mode": RESPONSE_MODE_PASSTHROUGH,
        "upstream": {
            "status": 200,
            "content_type": "application/json",
        },
        "meta": {"latency_ms": 42},
        "safety": {"credential_material_output": credential_material_output},
    }
    if error_type:
        payload["error_type"] = error_type
    if include_body:
        payload["upstream"]["body"] = upstream_body if upstream_body is not None else {"data": {}}
    if include_summary_fields:
        payload["source_card"] = {"unexpected": True}
        payload["source_quality"] = {"unexpected": True}
    return payload


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
    elif action_name == "track_analysis_check_data_ready":
        source_card["track_analysis_check_data_ready_summary"] = {
            "fixed_path": TRACK_ANALYSIS_CHECK_DATA_READY_FIXED_PATH,
            "readiness_status": "completed",
            "dateStatus": "ready",
            "date_status_present": True,
            "code": 1,
            "message_summary": "readiness status returned",
            "trace_id_present": True,
            "coverage_limitations": ["readiness_not_evidence"],
            "rawReadinessBody": "raw_readiness_body_should_not_render",
            "traceId": "trace_id_value_should_not_render",
        }
        source_card["key_entities"] = {
            "device_id": "ANDROID_track_device_001",
            "deviceId": "ANDROID_track_device_001",
            "appName": "KUAISHOU",
            "product": "KUAISHOU",
            "startTime": 1764201600000,
            "endTime": 1764288000000,
        }
        source_card["missing_fields"] = ["track_analysis_profile", "track_analysis_getUseDuration", "track_analysis_getDeviceIds"]
        source_card["next_action"] = "Use readiness only as source-quality context; run Track Analysis evidence actions next."
        payload["key_entities"] = dict(source_card["key_entities"])
        payload["missing_fields"] = list(source_card["missing_fields"])
        payload["next_action"] = source_card["next_action"]
        payload["source_quality"].update(
            {
                "no_data_not_risk_exclusion": True,
                "track_analysis_action_contract": "track_analysis_check_data_ready",
                "fixed_path": TRACK_ANALYSIS_CHECK_DATA_READY_FIXED_PATH,
                "raw_readiness_body_suppressed": True,
                "trace_id_value_suppressed": True,
                "raw_response_full_body_returned": False,
                "readiness_not_evidence": True,
            }
        )
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
    elif action_name == "archives_photo_search":
        source_card["archives_photo_search_summary"] = {
            "fixed_path": ARCHIVES_PHOTO_SEARCH_FIXED_PATH,
            "photo_count": 2,
            "totalCount": 2,
            "dataList_length": 2,
            "publish_time_range": {
                "earliest_publish_time": "2026-05-27 08:00:00",
                "latest_publish_time": "2026-05-28 12:00:00",
            },
            "status_summary": {"visible": 1, "deleted": 1},
            "risk_context_summary": ["reported_photo_cluster", "publish_time_anchor_present"],
            "report_reason_summary": {"fraud": 1, "harassment": 1},
            "pagination_required": False,
            "coverage_limitations": ["report_signal_not_final_judgement"],
            "userId": "2871834924",
            "reportedIds": "2871834924",
            "photo_ids": ["photo_1001", "photo_1002"],
            "photoId": "photo_1001",
            "liveId": "live_2001",
            "reportText": "raw_report_text_should_not_render",
            "reportContent": "raw_report_content_should_not_render",
        }
        source_card["key_entities"] = {
            "user_id": "2871834924",
            "photo_ids": ["photo_1001", "photo_1002"],
            "live_id": "live_2001",
        }
        source_card["missing_fields"] = ["photo_detail_meta"]
        source_card["next_action"] = "Cross-check reported photo with photo detail, audit log, and account timeline."
        payload["key_entities"] = dict(source_card["key_entities"])
        payload["missing_fields"] = list(source_card["missing_fields"])
        payload["next_action"] = source_card["next_action"]
        payload["source_quality"].update(
            {
                "no_data_not_risk_exclusion": True,
                "archives_action_contract": "archives_photo_search",
                "fixed_path": ARCHIVES_PHOTO_SEARCH_FIXED_PATH,
                "raw_report_text_suppressed": True,
                "raw_response_full_body_returned": False,
            }
        )
    elif action_name == "archives_user_profile":
        source_card["archives_user_profile_summary"] = {
            "fixed_path": ARCHIVES_USER_PROFILE_FIXED_PATH,
            "account_status_summary": {"account_state": "normal", "profile_visible": True},
            "registration_summary": {"register_time_present": True, "register_channel_present": True},
            "profile_state_summary": {"avatar_present": True, "intro_present": True, "nickname_present": True},
            "label_summary": {"risk_label_count": 1, "label_groups_observed": ["account_baseline"]},
            "risk_info_summary": {"risk_info_present": True, "risk_info_count": 1},
            "shop_status_summary": {"shop_status_present": False},
            "punish_status_summary": {"user_level_punish_unsupported": True},
            "coverage_limitations": ["home_info_is_current_state_not_history"],
            "userId": "2871834924",
            "deviceId": "ANDROID_profile_device_001",
            "userIpDesc": "10.20.30.41",
            "phone_number": "13812345678",
            "id_card": "110105199001011234",
            "real_name": "Fixture User",
            "rawProfileBody": "raw_profile_body_should_not_render",
        }
        source_card["key_entities"] = {
            "user_id": "2871834924",
            "deviceId": "ANDROID_profile_device_001",
            "ip": "10.20.30.41",
        }
        source_card["missing_fields"] = ["profile_change_history"]
        source_card["next_action"] = "Cross-check profile baseline with user analysis and content/report evidence."
        payload["key_entities"] = dict(source_card["key_entities"])
        payload["missing_fields"] = list(source_card["missing_fields"])
        payload["next_action"] = source_card["next_action"]
        payload["source_quality"].update(
            {
                "no_data_not_risk_exclusion": True,
                "archives_action_contract": "archives_user_profile",
                "fixed_path": ARCHIVES_USER_PROFILE_FIXED_PATH,
                "raw_profile_body_suppressed": True,
                "raw_response_full_body_returned": False,
            }
        )
    elif action_name == "archives_related_users":
        source_card["archives_related_users_summary"] = {
            "fixed_path": ARCHIVES_RELATED_USERS_FIXED_PATH,
            "related_user_count": 3,
            "relation_type_summary": {
                "same_device_registered_count": 2,
                "same_device_login_count": 1,
            },
            "same_device_registered_count": 2,
            "same_device_login_count": 1,
            "status_summary": {"normal": 2, "restricted": 1},
            "risk_context_summary": ["same_device_cluster_candidate", "needs_per_account_validation"],
            "pagination_required": False,
            "coverage_limitations": ["same_device_relation_not_standalone_judgement"],
            "userId": "2871834924",
            "related_user_ids": ["772671837", "3481089791", "2871834924"],
            "deviceId": "ANDROID_relation_device_001",
            "rawRelatedUserProfile": "raw_related_user_profile_should_not_render",
        }
        source_card["key_entities"] = {
            "user_id": "2871834924",
            "related_user_ids": ["772671837", "3481089791", "2871834924"],
            "deviceId": "ANDROID_relation_device_001",
        }
        source_card["missing_fields"] = ["related_user_login_behavior"]
        source_card["next_action"] = "Validate related users individually before any cluster judgement."
        payload["key_entities"] = dict(source_card["key_entities"])
        payload["missing_fields"] = list(source_card["missing_fields"])
        payload["next_action"] = source_card["next_action"]
        payload["source_quality"].update(
            {
                "no_data_not_risk_exclusion": True,
                "archives_action_contract": "archives_related_users",
                "fixed_path": ARCHIVES_RELATED_USERS_FIXED_PATH,
                "raw_related_user_profile_suppressed": True,
                "raw_response_full_body_returned": False,
            }
        )
    elif action_name == "archives_private_message_search":
        source_card["archives_private_message_search_summary"] = {
            "fixed_path": ARCHIVES_PRIVATE_MESSAGE_SEARCH_FIXED_PATH,
            "private_message_count": 12,
            "total": 12,
            "direction_summary": {"sent": 7, "received": 5},
            "message_time_range": {
                "earliest_message_time": "2026-05-27 10:00:00",
                "latest_message_time": "2026-05-28 16:30:00",
            },
            "status_summary": {"normal": 10, "deleted": 2},
            "counterpart_count": 3,
            "risk_context_summary": ["message_activity_present", "plaintext_suppressed"],
            "pagination_required": False,
            "coverage_limitations": ["private_message_summary_not_final_judgement"],
            "userId": "2871834924",
            "fromUserId": "2871834924",
            "counterpart_user_ids": ["772671837", "3481089791"],
            "messageContent": "raw_private_message_text_should_not_render",
            "privateMessagePlaintext": "raw_private_message_plaintext_should_not_render",
            "messageText": "full_message_text_should_not_render",
            "counterpartNickname": "raw_counterpart_nickname_should_not_render",
        }
        source_card["key_entities"] = {
            "user_id": "2871834924",
            "counterpart_user_ids": ["772671837", "3481089791"],
        }
        source_card["missing_fields"] = ["message_risk_policy_attribution"]
        source_card["next_action"] = "Use message counts/status only; do not output private message plaintext."
        payload["key_entities"] = dict(source_card["key_entities"])
        payload["missing_fields"] = list(source_card["missing_fields"])
        payload["next_action"] = source_card["next_action"]
        payload["source_quality"].update(
            {
                "no_data_not_risk_exclusion": True,
                "archives_action_contract": "archives_private_message_search",
                "fixed_path": ARCHIVES_PRIVATE_MESSAGE_SEARCH_FIXED_PATH,
                "raw_message_plaintext_suppressed": True,
                "raw_response_full_body_returned": False,
                "private_message_summary_not_final_judgement": True,
            }
        )
    elif action_name == "archives_past_four_items":
        source_card["archives_past_four_items_summary"] = {
            "fixed_path": ARCHIVES_PAST_FOUR_ITEMS_FIXED_PATH,
            "total_changes": 6,
            "total": 6,
            "change_time_range": {
                "earliest_change_time": "2026-05-26 09:00:00",
                "latest_change_time": "2026-05-28 14:00:00",
            },
            "info_type_summary": {
                "username": 1,
                "avatar": 2,
                "profile_description": 2,
                "background": 1,
            },
            "status_summary": {"approved": 4, "rejected": 2},
            "profile_change_risk_summary": ["profile_changed_after_login_window", "raw_profile_content_suppressed"],
            "pagination_required": False,
            "coverage_limitations": ["four_info_change_log_not_final_judgement"],
            "userId": "2871834924",
            "keyword": "2871834924",
            "oldValue": "raw_old_profile_value_should_not_render",
            "newValue": "raw_new_profile_value_should_not_render",
            "avatarUrl": "https://example.invalid/raw_avatar_should_not_render",
            "backgroundUrl": "https://example.invalid/raw_background_should_not_render",
            "profileDescription": "raw_profile_description_should_not_render",
            "operatorName": "raw_operator_name_should_not_render",
            "rawFourInfo": "full_four_info_raw_should_not_render",
        }
        source_card["key_entities"] = {"user_id": "2871834924"}
        source_card["missing_fields"] = ["login_or_publish_alignment"]
        source_card["next_action"] = "Align profile-change timeline with login, publish, and report evidence before judgement."
        payload["key_entities"] = dict(source_card["key_entities"])
        payload["missing_fields"] = list(source_card["missing_fields"])
        payload["next_action"] = source_card["next_action"]
        payload["source_quality"].update(
            {
                "no_data_not_risk_exclusion": True,
                "archives_action_contract": "archives_past_four_items",
                "fixed_path": ARCHIVES_PAST_FOUR_ITEMS_FIXED_PATH,
                "raw_old_new_profile_content_suppressed": True,
                "raw_media_url_suppressed": True,
                "raw_response_full_body_returned": False,
                "four_info_change_log_not_final_judgement": True,
            }
        )
    elif action_name == "rcp_event_detail":
        source_card["rcp_event_detail_summary"] = {
            "fixed_path": RCP_EVENT_DETAIL_FIXED_PATH,
            "event_detail_status": "completed",
            "eventType": "USER_REGISTER_NEW",
            "eventId": "5370247893355116990",
            "_occurTime": 1779774526479,
            "occur_time": "2026-05-26 01:48:46",
            "sourceId": "2871834924",
            "deviceId": "ANDROID_rcp_detail_device_001",
            "userRegisterIp": "10.20.30.42",
            "real_time_feedback": "blocked",
            "error_code": "217009",
            "side_effect_ops_summary": ["REGISTER_BLOCK"],
            "effective_policy_summary": "BS_fake_account_register_thirdPlatformAll_bindphone#5",
            "hit_policy_count": 2,
            "hit_policy_codes": [
                "BS_Register_nosense_captcha_all#5",
                "BS_fake_account_register_thirdPlatformAll_bindphone#5",
            ],
            "policy_exception_summary": {"exception_present": False},
            "coverage_limitations": ["single_event_detail_not_final_judgement"],
            "rawDetailBody": "raw_rcp_detail_body_should_not_render",
        }
        source_card["key_entities"] = {
            "eventId": "5370247893355116990",
            "eventType": "USER_REGISTER_NEW",
            "sourceId": "2871834924",
            "deviceId": "ANDROID_rcp_detail_device_001",
            "userRegisterIp": "10.20.30.42",
            "policy_codes": ["BS_Register_nosense_captcha_all#5", "BS_fake_account_register_thirdPlatformAll_bindphone#5"],
        }
        source_card["missing_fields"] = ["policyTreeNodeCode"]
        source_card["next_action"] = "Use _occurTime as queryTime for rcp_event_feature_list or policy attribution if needed."
        payload["key_entities"] = dict(source_card["key_entities"])
        payload["missing_fields"] = list(source_card["missing_fields"])
        payload["next_action"] = source_card["next_action"]
        payload["source_quality"].update(
            {
                "no_data_not_risk_exclusion": True,
                "rcp_action_contract": "rcp_event_detail",
                "fixed_path": RCP_EVENT_DETAIL_FIXED_PATH,
                "raw_detail_body_suppressed": True,
                "raw_response_full_body_returned": False,
                "strategy_event_not_final_judgement": True,
            }
        )
    elif action_name == "rcp_event_feature_list":
        source_card["rcp_event_feature_list_summary"] = {
            "fixed_path": RCP_EVENT_FEATURE_LIST_FIXED_PATH,
            "feature_snapshot_status": "completed",
            "eventType": "USER_REGISTER_NEW",
            "eventId": "5370247893355116990",
            "queryTime": 1779774526479,
            "featureGroup": "",
            "feature_count": 519,
            "feature_group_distribution": {
                "DERIVE": 120,
                "ORIG": 90,
                "COUNTER": 160,
                "SYS": 50,
                "DATASERV": 60,
                "OTHER": 39,
            },
            "feature_key_samples": ["deviceIdWeaponLogCnt", "deviceClientEventLogCnt3h", "appealPhoneModel"],
            "feature_name_samples": ["device log count", "client event count", "phone model"],
            "check_result_summary": {"feature_values_present": True, "raw_values_suppressed": True},
            "coverage_limitations": ["feature_snapshot_context_only"],
            "rawFeatureValue": "raw_feature_value_should_not_render",
            "featureValue": "full_feature_value_should_not_render",
        }
        source_card["key_entities"] = {
            "eventId": "5370247893355116990",
            "eventType": "USER_REGISTER_NEW",
        }
        source_card["missing_fields"] = ["policy_condition_attribution"]
        source_card["next_action"] = "Use policy attribution for condition-level explanation; do not expose raw feature values."
        payload["key_entities"] = dict(source_card["key_entities"])
        payload["missing_fields"] = list(source_card["missing_fields"])
        payload["next_action"] = source_card["next_action"]
        payload["source_quality"].update(
            {
                "no_data_not_risk_exclusion": True,
                "rcp_action_contract": "rcp_event_feature_list",
                "fixed_path": RCP_EVENT_FEATURE_LIST_FIXED_PATH,
                "raw_feature_values_suppressed": True,
                "raw_response_full_body_returned": False,
                "strategy_feature_snapshot_not_final_judgement": True,
            }
        )
    elif action_name == "rcp_policy_version_lookup":
        source_card["rcp_policy_version_lookup_summary"] = {
            "fixed_path": RCP_POLICY_VERSION_LOOKUP_FIXED_PATH,
            "version_lookup_status": "completed",
            "eventType": "USER_REGISTER_NEW",
            "eventId": "5370247893355116990",
            "queryTime": 1779774526479,
            "policyCode": "BS_fake_account_register_thirdPlatformAll_bindphone",
            "policyVersion": 5,
            "version_found": True,
            "policy_name_summary": "third platform bind phone registration policy",
            "policy_type_summary": "risk_control_policy",
            "snapshotVersion": "887",
            "version_metadata_summary": {"versionStr_present": True, "online_status_present": True},
            "coverage_limitations": ["policy_version_context_not_final_judgement"],
            "rawPolicyVersionBody": "raw_policy_version_body_should_not_render",
        }
        source_card["key_entities"] = {
            "eventId": "5370247893355116990",
            "eventType": "USER_REGISTER_NEW",
            "policyCode": "BS_fake_account_register_thirdPlatformAll_bindphone",
            "policyVersion": 5,
            "snapshotVersion": "887",
        }
        source_card["missing_fields"] = ["policyTreeNodeCode"]
        source_card["next_action"] = "Resolve policyTreeNodeCode via queryProPolicyTree before node binding attribution."
        payload["key_entities"] = dict(source_card["key_entities"])
        payload["missing_fields"] = list(source_card["missing_fields"])
        payload["next_action"] = source_card["next_action"]
        payload["source_quality"].update(
            {
                "no_data_not_risk_exclusion": True,
                "rcp_action_contract": "rcp_policy_version_lookup",
                "fixed_path": RCP_POLICY_VERSION_LOOKUP_FIXED_PATH,
                "raw_policy_version_body_suppressed": True,
                "raw_response_full_body_returned": False,
                "policy_version_not_final_judgement": True,
            }
        )
    elif action_name == "rcp_policy_detail_lookup":
        source_card["rcp_policy_detail_lookup_summary"] = {
            "fixed_path": RCP_POLICY_DETAIL_LOOKUP_FIXED_PATH,
            "policy_detail_status": "completed",
            "policyCode": "BS_fake_account_register_thirdPlatformAll_bindphone",
            "policyVersion": 5,
            "eventTypeCode": "USER_REGISTER_NEW",
            "policy_name_summary": "third platform bind phone registration policy",
            "policy_status_summary": {"online_status_present": True, "status_code": 2},
            "condition_count": 4,
            "condition_expression_present": True,
            "punish_summary": {"punish_config_present": True, "raw_punish_body_suppressed": True},
            "version_count": 5,
            "latest_version": 5,
            "relation_policy_tree_count": 1,
            "coverage_limitations": ["policy_detail_not_final_judgement"],
            "rawPolicyDetailBody": "raw_policy_detail_body_should_not_render",
            "conditionExpressionRaw": "raw_condition_expression_should_not_render",
        }
        source_card["key_entities"] = {
            "policyCode": "BS_fake_account_register_thirdPlatformAll_bindphone",
            "policyVersion": 5,
            "eventTypeCode": "USER_REGISTER_NEW",
        }
        source_card["missing_fields"] = ["event_attribution_for_specific_hit_path"]
        source_card["next_action"] = "Use event attribution for a specific hit path; do not output raw condition expressions."
        payload["key_entities"] = dict(source_card["key_entities"])
        payload["missing_fields"] = list(source_card["missing_fields"])
        payload["next_action"] = source_card["next_action"]
        payload["source_quality"].update(
            {
                "no_data_not_risk_exclusion": True,
                "rcp_action_contract": "rcp_policy_detail_lookup",
                "fixed_path": RCP_POLICY_DETAIL_LOOKUP_FIXED_PATH,
                "raw_policy_detail_body_suppressed": True,
                "raw_condition_expression_suppressed": True,
                "raw_response_full_body_returned": False,
                "policy_detail_not_final_judgement": True,
            }
        )
    elif action_name == "rcp_policy_release_record_lookup":
        source_card["rcp_policy_release_record_lookup_summary"] = {
            "fixed_path": RCP_POLICY_RELEASE_LIST_FIXED_PATH,
            "companion_readonly_paths": [RCP_POLICY_RELEASE_SELECT_INFO_FIXED_PATH],
            "release_record_status": "completed",
            "policyCode": "BS_fake_account_register_thirdPlatformAll_bindphone",
            "statusCode": "",
            "record_count": 4,
            "business_union_key_count": 4,
            "business_union_keys_present": True,
            "parsed_policy_versions": [2, 3, 4, 5],
            "pipeline_versions": [11, 12, 13],
            "status_distribution": {"001": 1, "000": 2, "202": 1},
            "experiment_or_gray_summary": {"experiment_or_gray_record_present": True},
            "terminal_records": 2,
            "online_acceptance_records": 1,
            "coverage_limitations": ["release_record_not_final_judgement"],
            "rawReleaseRecords": "raw_release_records_should_not_render",
            "pipelineRecordsRaw": "raw_pipeline_records_should_not_render",
            "operatorName": "operator_identity_should_not_render",
            "createUser": "create_user_should_not_render",
        }
        source_card["key_entities"] = {
            "policyCode": "BS_fake_account_register_thirdPlatformAll_bindphone",
            "statusCode": "",
            "parsed_policy_versions": [2, 3, 4, 5],
            "pipeline_versions": [11, 12, 13],
        }
        source_card["missing_fields"] = ["event_attribution_for_specific_hit_path"]
        source_card["next_action"] = "Use release records as lifecycle provenance only; do not treat release status as risk judgement."
        payload["key_entities"] = dict(source_card["key_entities"])
        payload["missing_fields"] = list(source_card["missing_fields"])
        payload["next_action"] = source_card["next_action"]
        payload["source_quality"].update(
            {
                "no_data_not_risk_exclusion": True,
                "rcp_action_contract": "rcp_policy_release_record_lookup",
                "fixed_path": RCP_POLICY_RELEASE_LIST_FIXED_PATH,
                "selectInfo_fixed_path": RCP_POLICY_RELEASE_SELECT_INFO_FIXED_PATH,
                "extrbB_exact_policyCode_filter": True,
                "raw_release_records_suppressed": True,
                "operator_identity_suppressed": True,
                "raw_response_full_body_returned": False,
                "release_record_not_final_judgement": True,
                "pipelineVersion_not_policy_version": True,
            }
        )
    elif action_name == "rcp_policy_tree_lookup":
        source_card["rcp_policy_tree_lookup_summary"] = {
            "fixed_path": RCP_POLICY_TREE_LOOKUP_FIXED_PATH,
            "policy_tree_status": "completed",
            "policyTreeCode": "USER_REGISTER_NEW",
            "policyTreeVersion": 887,
            "targetPolicyCode": "BS_fake_account_register_thirdPlatformAll_bindphone",
            "policyTreeNodeCode": "53187346034508",
            "node_name_summary": "third platform bind phone registration node",
            "node_code_source": "recursive_queryProPolicyTree_parse",
            "target_policy_found": True,
            "policy_tree_depth_summary": {"nodes_scanned": 18, "max_depth_observed": 4},
            "policy_tree_list_records_total": 20,
            "node_binding_policy_count": 13,
            "all_policy_code_count": 20,
            "policy_code_sample_count": 3,
            "target_policy_binding_status": "bound_to_resolved_node",
            "coverage_limitations": ["policy_tree_context_not_final_judgement"],
            "incorrect_path_forbidden": "/v2/rest/pc/policytree/getPolicyTreeByVersion",
            "companion_readonly_paths": [
                RCP_POLICY_TREE_LIST_FIXED_PATH,
                RCP_POLICY_TREE_BINDING_BY_NODE_FIXED_PATH,
                RCP_POLICY_TREE_ALL_POLICY_CODE_FIXED_PATH,
            ],
            "rawPolicyTreeBody": "raw_policy_tree_body_should_not_render",
            "policyTreeRaw": "full_policy_tree_raw_should_not_render",
            "rawNodeBindingList": "raw_node_binding_list_should_not_render",
            "rawAllPolicyCodeList": "raw_all_policy_code_list_should_not_render",
        }
        source_card["key_entities"] = {
            "policyTreeCode": "USER_REGISTER_NEW",
            "policyTreeVersion": 887,
            "policyTreeNodeCode": "53187346034508",
            "targetPolicyCode": "BS_fake_account_register_thirdPlatformAll_bindphone",
        }
        source_card["missing_fields"] = []
        source_card["next_action"] = "Use resolved policyTreeNodeCode only for node binding attribution when required; never guess it."
        payload["key_entities"] = dict(source_card["key_entities"])
        payload["missing_fields"] = list(source_card["missing_fields"])
        payload["next_action"] = source_card["next_action"]
        payload["source_quality"].update(
            {
                "no_data_not_risk_exclusion": True,
                "rcp_action_contract": "rcp_policy_tree_lookup",
                "fixed_path": RCP_POLICY_TREE_LOOKUP_FIXED_PATH,
                "companion_readonly_paths": [
                    RCP_POLICY_TREE_LIST_FIXED_PATH,
                    RCP_POLICY_TREE_BINDING_BY_NODE_FIXED_PATH,
                    RCP_POLICY_TREE_ALL_POLICY_CODE_FIXED_PATH,
                ],
                "incorrect_path_forbidden": "/v2/rest/pc/policytree/getPolicyTreeByVersion",
                "raw_policy_tree_body_suppressed": True,
                "raw_node_binding_list_suppressed": True,
                "raw_all_policy_code_list_suppressed": True,
                "raw_response_full_body_returned": False,
                "policyTreeList_is_coarse_filter": True,
                "policy_tree_not_final_judgement": True,
            }
        )
    elif action_name == "rcp_node_policy_attribution":
        source_card["rcp_node_policy_attribution_summary"] = {
            "fixed_path": RCP_NODE_POLICY_ATTRIBUTION_FIXED_PATH,
            "attribution_status": "completed",
            "eventType": "USER_REGISTER_NEW",
            "eventId": "5370247893355116990",
            "queryTime": 1779774526479,
            "policyCode": "BS_fake_account_register_thirdPlatformAll_bindphone",
            "policyVersion": 5,
            "condition_count": 4,
            "true_condition_count": 4,
            "false_condition_count": 0,
            "condition_result_summary": {"all_conditions_true": True, "failed_condition_present": False},
            "error_feature_count": 0,
            "node_status_summary": {"nodeStatus_present": True, "node_result_true": True},
            "coverage_limitations": ["policy_attribution_not_final_judgement"],
            "rawConditionDump": "raw_condition_dump_should_not_render",
            "conditionListRaw": "full_condition_list_should_not_render",
            "rawFeatureValue": "raw_feature_value_should_not_render",
        }
        source_card["key_entities"] = {
            "eventId": "5370247893355116990",
            "eventType": "USER_REGISTER_NEW",
            "policyCode": "BS_fake_account_register_thirdPlatformAll_bindphone",
            "policyVersion": 5,
        }
        source_card["missing_fields"] = ["node_bind_policy_attribution"]
        source_card["next_action"] = "Use node binding attribution only if node-level strategy-tree context is required."
        payload["key_entities"] = dict(source_card["key_entities"])
        payload["missing_fields"] = list(source_card["missing_fields"])
        payload["next_action"] = source_card["next_action"]
        payload["source_quality"].update(
            {
                "no_data_not_risk_exclusion": True,
                "rcp_action_contract": "rcp_node_policy_attribution",
                "fixed_path": RCP_NODE_POLICY_ATTRIBUTION_FIXED_PATH,
                "raw_condition_dump_suppressed": True,
                "raw_feature_values_suppressed": True,
                "raw_response_full_body_returned": False,
                "policy_attribution_not_final_judgement": True,
            }
        )
    elif action_name == "rcp_node_bind_policy_attribution":
        source_card["rcp_node_bind_policy_attribution_summary"] = {
            "fixed_path": RCP_NODE_BIND_POLICY_ATTRIBUTION_FIXED_PATH,
            "node_binding_status": "completed",
            "eventType": "USER_REGISTER_NEW",
            "eventId": "5370247893355116990",
            "queryTime": 1779774526479,
            "policyTreeCode": "USER_REGISTER_NEW",
            "policyTreeVersion": 887,
            "policyTreeNodeCode": "53187346034508",
            "node_name_summary": "third platform bind phone registration node",
            "binding_policy_count": 2,
            "effective_policy_summary": "BS_fake_account_register_thirdPlatformAll_bindphone#5",
            "targetPolicyCode": "BS_fake_account_register_thirdPlatformAll_bindphone",
            "target_policy_online": True,
            "target_policy_result": True,
            "condition_count": 4,
            "nodebinding_policy_summary": {
                "target_policy_found": True,
                "node_binding_list_present": True,
            },
            "coverage_limitations": ["node_binding_attribution_not_final_judgement"],
            "rawNodeBindingBody": "raw_node_binding_body_should_not_render",
            "nodebindingPolicyListRaw": "full_nodebinding_policy_list_should_not_render",
            "rawConditionDump": "raw_condition_dump_should_not_render",
        }
        source_card["key_entities"] = {
            "eventId": "5370247893355116990",
            "eventType": "USER_REGISTER_NEW",
            "policyTreeCode": "USER_REGISTER_NEW",
            "policyTreeVersion": 887,
            "policyTreeNodeCode": "53187346034508",
            "targetPolicyCode": "BS_fake_account_register_thirdPlatformAll_bindphone",
            "effectivePolicy": "BS_fake_account_register_thirdPlatformAll_bindphone#5",
        }
        source_card["missing_fields"] = []
        source_card["next_action"] = "Use node binding attribution as strategy-tree explanation only; do not treat it as final risk judgement."
        payload["key_entities"] = dict(source_card["key_entities"])
        payload["missing_fields"] = list(source_card["missing_fields"])
        payload["next_action"] = source_card["next_action"]
        payload["source_quality"].update(
            {
                "no_data_not_risk_exclusion": True,
                "rcp_action_contract": "rcp_node_bind_policy_attribution",
                "fixed_path": RCP_NODE_BIND_POLICY_ATTRIBUTION_FIXED_PATH,
                "raw_node_binding_body_suppressed": True,
                "raw_condition_dump_suppressed": True,
                "raw_response_full_body_returned": False,
                "node_binding_attribution_not_final_judgement": True,
            }
        )
    return payload


def parse_typed_params_json(raw_json: str) -> Dict[str, Any]:
    """Parse CLI typed params while preserving the fixed-action boundary."""

    try:
        parsed = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        raise BrowserBackedServiceInputError(f"typed params must be a JSON object: {exc.msg}") from exc
    if not isinstance(parsed, Mapping):
        raise BrowserBackedServiceInputError("typed params must be a JSON object")
    typed_params = dict(parsed)
    _validate_typed_params(typed_params)
    return typed_params


def run_action_invocation(action_name: str, typed_params: Mapping[str, Any], *, live_service: bool = False) -> Dict[str, Any]:
    """Invoke a fixed action in mock mode or against the local service."""

    _validate_action_name(action_name)
    params = dict(typed_params)
    _validate_typed_params(params)
    client = BrowserBackedServiceClient() if live_service else BrowserBackedServiceClient(opener=_FakeOpener(_fixture_payload(action_name, "completed")))
    result = client.call_action(action_name, params)
    result["invocation_mode"] = "live_service" if live_service else "mock"
    result["live_service_called"] = bool(live_service)
    result["platform_called"] = False if not live_service else result.get("source_status") == "completed"
    result["dataagent_called"] = False
    result["default_runtime_routing"] = False
    result["live_verified"] = False
    result["typed_params_summary"] = _typed_params_summary(params)
    result["fixed_action_endpoint"] = ACTION_ENDPOINTS[action_name]
    result["safety_boundary"] = {
        "fixed_action_name_only": True,
        "typed_params_only": True,
        "caller_url_path_header_cookie_token_session_allowed": False,
        "default_runtime_routing": False,
        "live_verified": False,
        "live_service_explicitly_requested": bool(live_service),
    }
    return result


def run_mock_action_invocation(action_name: str, typed_params: Mapping[str, Any]) -> Dict[str, Any]:
    """Invoke a fixed action against local fixtures without service/platform access."""

    return run_action_invocation(action_name, typed_params, live_service=False)


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

    passthrough_login_body = {
        "data": {
            "logSearchModels": [
                {
                    "logSource": "APP_LOGIN",
                    "method": "PASSWORD",
                    "timestamp": 1764288000000,
                    "userId": "2871834924",
                    "deviceId": "ANDROID_login_device_001",
                    "userIpDesc": "10.20.30.40",
                }
            ]
        }
    }
    passthrough_opener = _FakeOpener(_passthrough_fixture_payload("login_logs_search", passthrough_login_body))
    passthrough_result = BrowserBackedServiceClient(opener=passthrough_opener).call_action(
        "login_logs_search",
        {"user_id": "fixture"},
        response_mode=RESPONSE_MODE_PASSTHROUGH,
    )
    passthrough_request_body = json.loads((passthrough_opener.calls[0]["body"] or b"{}").decode("utf-8"))
    assert passthrough_request_body["response_mode"] == RESPONSE_MODE_PASSTHROUGH
    assert passthrough_result["response_mode"] == RESPONSE_MODE_PASSTHROUGH
    assert passthrough_result["source_status"] == "completed"
    assert passthrough_result["normalized_observation"]["records_count"] == 1
    assert passthrough_result["normalized_observation"]["raw_records_suppressed"] is True
    assert "source_card" not in passthrough_result
    assert "source_quality" not in passthrough_result
    results.append(("passthrough_client_parses_upstream_body", "passed"))

    summary_field_result = BrowserBackedServiceClient(
        opener=_FakeOpener(
            _passthrough_fixture_payload(
                "login_logs_search",
                passthrough_login_body,
                include_summary_fields=True,
            )
        )
    ).call_action("login_logs_search", {"user_id": "fixture"}, response_mode=RESPONSE_MODE_PASSTHROUGH)
    assert summary_field_result["source_status"] == "completed"
    assert summary_field_result["unexpected_summary_fields"] == ["source_card", "source_quality"]
    results.append(("passthrough_unexpected_summary_fields_marked", "passed"))

    credential_violation = BrowserBackedServiceClient(
        opener=_FakeOpener(
            _passthrough_fixture_payload(
                "login_logs_search",
                passthrough_login_body,
                credential_material_output=True,
            )
        )
    ).call_action("login_logs_search", {"user_id": "fixture"}, response_mode=RESPONSE_MODE_PASSTHROUGH)
    assert credential_violation["source_status"] == "blocked"
    assert credential_violation["error_type"] == "credential_material_violation"
    assert credential_violation["sensitive_output"] is False
    results.append(("passthrough_credential_material_fail_closed", "passed"))

    landing_flow_blocked = BrowserBackedServiceClient(
        opener=_FakeOpener(
            _passthrough_fixture_payload(
                "login_logs_search",
                include_body=False,
                ok=False,
                error_type="landing_flow_blocked",
            )
        )
    ).call_action("login_logs_search", {"user_id": "fixture"}, response_mode=RESPONSE_MODE_PASSTHROUGH)
    assert landing_flow_blocked["source_status"] == "auth_failed"
    assert landing_flow_blocked["failure_layer"] == "auth_session"
    assert landing_flow_blocked["error_type"] == "landing_flow_blocked"
    assert landing_flow_blocked["normalized_observation"]["error_type"] == "landing_flow_blocked"
    results.append(("passthrough_landing_flow_blocked_preserves_service_error", "passed"))

    auth_failed = BrowserBackedServiceClient(
        opener=_FakeOpener(
            _passthrough_fixture_payload(
                "login_logs_search",
                include_body=False,
                ok=False,
                error_type="auth_failed",
            )
        )
    ).call_action("login_logs_search", {"user_id": "fixture"}, response_mode=RESPONSE_MODE_PASSTHROUGH)
    assert auth_failed["source_status"] == "auth_failed"
    assert auth_failed["failure_layer"] == "auth_session"
    assert auth_failed["error_type"] == "auth_failed"
    results.append(("passthrough_auth_failed_preserves_service_error", "passed"))

    missing_body_result = BrowserBackedServiceClient(
        opener=_FakeOpener(_passthrough_fixture_payload("login_logs_search", include_body=False))
    ).call_action("login_logs_search", {"user_id": "fixture"}, response_mode=RESPONSE_MODE_PASSTHROUGH)
    assert missing_body_result["source_status"] == "parse_error"
    assert missing_body_result["error_type"] == "passthrough_body_missing"
    results.append(("passthrough_body_missing_marked", "passed"))

    track_observation = parse_passthrough_response(
        "track_analysis_summary",
        {
            "sub_interface": "getDeviceIds",
            "userId": "2871834924",
            "data": {
                "deviceIds": ["ANDROID_track_device_001", "IOS_track_device_002"],
            },
        },
    )
    assert track_observation["source_status"] == "completed"
    assert track_observation["sub_interface"] == "getDeviceIds"
    assert track_observation["device_ids_count"] == 2
    assert track_observation["raw_body_suppressed"] is True
    results.append(("track_analysis_passthrough_parser_normalizes_observation", "passed"))

    login_observation = parse_passthrough_response("login_logs_search", passthrough_login_body)
    assert login_observation["source_status"] == "completed"
    assert login_observation["records_count"] == 1
    assert login_observation["samples"][0]["logSource"] == "APP_LOGIN"
    assert login_observation["raw_records_suppressed"] is True
    results.append(("login_logs_passthrough_parser_log_search_models", "passed"))

    compat_opener = _FakeOpener(_fixture_payload("login_logs_search", "completed"))
    compat_result = BrowserBackedServiceClient(opener=compat_opener).call_action("login_logs_search", {"user_id": "fixture"})
    compat_request_body = json.loads((compat_opener.calls[0]["body"] or b"{}").decode("utf-8"))
    assert "response_mode" not in compat_request_body
    assert compat_result["source_card"] and compat_result["source_quality"]
    assert compat_result["source_status"] == "completed"
    results.append(("compat_summary_fixture_not_regressed", "passed"))

    readiness_plan = build_track_analysis_check_data_ready_browser_backed_request(
        "ANDROID_track_device_001",
        start_time_ms=1764201600000,
        end_time_ms=1764288000000,
        categories=["active"],
    )
    assert readiness_plan["action_name"] == "track_analysis_check_data_ready"
    assert readiness_plan["fixed_path"] == TRACK_ANALYSIS_CHECK_DATA_READY_FIXED_PATH
    assert readiness_plan["typed_params"]["device_id"] == "ANDROID_track_device_001"
    assert readiness_plan["typed_params"]["type"] == "deviceId"
    serialized_readiness_plan = json.dumps(readiness_plan, ensure_ascii=True)
    assert "cookie" not in serialized_readiness_plan.lower()
    assert "token" not in serialized_readiness_plan.lower()
    assert "session" not in serialized_readiness_plan.lower()
    assert "/dp/platform/app/analytics/v2/sequence/checkDataReady" in serialized_readiness_plan
    assert "http://" not in serialized_readiness_plan.lower()
    assert "https://" not in serialized_readiness_plan.lower()
    results.append(("track_analysis_check_data_ready_typed_request_plan", "passed"))

    readiness_opener = _FakeOpener(_fixture_payload("track_analysis_check_data_ready", "completed"))
    client = BrowserBackedServiceClient(opener=readiness_opener)
    readiness_result = client.call_action("track_analysis_check_data_ready", readiness_plan["typed_params"])
    assert readiness_opener.calls[0]["url"].endswith(ACTION_ENDPOINTS["track_analysis_check_data_ready"])
    assert readiness_result["source_status"] == "completed"
    assert readiness_result["key_entities"]["device_id"] == "ANDROID_track_device_001"
    assert readiness_result["missing_fields"] == [
        "track_analysis_profile",
        "track_analysis_getUseDuration",
        "track_analysis_getDeviceIds",
    ]
    readiness_card = build_partial_evidence_card([readiness_result])
    readiness_summary = readiness_card["evidence_summary_by_source"]["track_analysis_check_data_ready"]
    assert readiness_summary["action_contract"]["fixed_path"] == TRACK_ANALYSIS_CHECK_DATA_READY_FIXED_PATH
    assert readiness_summary["readiness_summary"]["date_status_present"] is True
    readiness_text = json.dumps(readiness_card, ensure_ascii=True)
    assert "raw_readiness_body_should_not_render" not in readiness_text
    assert "trace_id_value_should_not_render" not in readiness_text
    assert '"rawReadinessBody":' not in readiness_text
    assert '"traceId":' not in readiness_text
    results.append(("track_analysis_check_data_ready_standard_source_result", "passed"))

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

    photo_plan = build_archives_photo_search_browser_backed_request(
        "2871834924",
        begin_time_ms=1764201600000,
        end_time_ms=1764288000000,
    )
    assert photo_plan["action_name"] == "archives_photo_search"
    assert photo_plan["fixed_path"] == ARCHIVES_PHOTO_SEARCH_FIXED_PATH
    assert photo_plan["typed_params"]["user_id"] == "2871834924"
    assert photo_plan["typed_params"]["matchType"] == "0"
    assert photo_plan["typed_params"]["sort"] == "0"
    assert photo_plan["body_builder_summary"]["reportedIds_source"] == "user_id"
    serialized_photo_plan = json.dumps(photo_plan, ensure_ascii=True)
    assert "cookie" not in serialized_photo_plan.lower()
    assert "token" not in serialized_photo_plan.lower()
    assert "session" not in serialized_photo_plan.lower()
    assert "/v4/archives/report/photo/search" in serialized_photo_plan
    assert "http://" not in serialized_photo_plan.lower()
    assert "https://" not in serialized_photo_plan.lower()
    results.append(("archives_photo_search_typed_request_plan", "passed"))

    photo_opener = _FakeOpener(_fixture_payload("archives_photo_search", "completed"))
    client = BrowserBackedServiceClient(opener=photo_opener)
    photo_result = client.call_action("archives_photo_search", photo_plan["typed_params"])
    assert photo_opener.calls[0]["url"].endswith(ACTION_ENDPOINTS["archives_photo_search"])
    assert photo_result["source_status"] == "completed"
    assert photo_result["source_card"] and photo_result["source_quality"]
    assert photo_result["key_entities"]["photo_ids"] == ["photo_1001", "photo_1002"]
    assert photo_result["missing_fields"] == ["photo_detail_meta"]
    assert photo_result["sensitive_output"] is False
    assert photo_result["no_data_not_risk_exclusion"] is True
    photo_card = build_partial_evidence_card([photo_result])
    photo_summary = photo_card["evidence_summary_by_source"]["archives_photo_search"]
    assert photo_summary["action_contract"]["fixed_path"] == ARCHIVES_PHOTO_SEARCH_FIXED_PATH
    assert photo_summary["photo_search_summary"]["photo_count"] == 2
    assert photo_summary["photo_search_summary"]["publish_time_range"]["latest_publish_time"] == "2026-05-28 12:00:00"
    assert photo_summary["key_entities"]["photo_ids"] == ["photo_1001", "photo_1002"]
    photo_text = json.dumps(photo_card, ensure_ascii=True)
    assert "raw_report_text_should_not_render" not in photo_text
    assert "raw_report_content_should_not_render" not in photo_text
    assert '"reportText":' not in photo_text
    assert '"reportContent":' not in photo_text
    results.append(("archives_photo_search_standard_source_result", "passed"))

    profile_plan = build_archives_user_profile_browser_backed_request("2871834924")
    assert profile_plan["action_name"] == "archives_user_profile"
    assert profile_plan["fixed_path"] == ARCHIVES_USER_PROFILE_FIXED_PATH
    assert profile_plan["typed_params"]["user_id"] == "2871834924"
    serialized_profile_plan = json.dumps(profile_plan, ensure_ascii=True)
    assert "cookie" not in serialized_profile_plan.lower()
    assert "token" not in serialized_profile_plan.lower()
    assert "session" not in serialized_profile_plan.lower()
    assert "/archives/user/home/info" in serialized_profile_plan
    assert "http://" not in serialized_profile_plan.lower()
    assert "https://" not in serialized_profile_plan.lower()
    results.append(("archives_user_profile_typed_request_plan", "passed"))

    profile_opener = _FakeOpener(_fixture_payload("archives_user_profile", "completed"))
    client = BrowserBackedServiceClient(opener=profile_opener)
    profile_result = client.call_action("archives_user_profile", profile_plan["typed_params"])
    assert profile_opener.calls[0]["url"].endswith(ACTION_ENDPOINTS["archives_user_profile"])
    assert profile_result["source_status"] == "completed"
    assert profile_result["key_entities"]["deviceId"] == "ANDROID_profile_device_001"
    profile_card = build_partial_evidence_card([profile_result])
    profile_summary = profile_card["evidence_summary_by_source"]["archives_user_profile"]
    assert profile_summary["action_contract"]["fixed_path"] == ARCHIVES_USER_PROFILE_FIXED_PATH
    assert profile_summary["profile_summary"]["account_status_summary"]["account_state"] == "normal"
    profile_text = json.dumps(profile_card, ensure_ascii=True)
    assert "13812345678" not in profile_text
    assert "110105199001011234" not in profile_text
    assert "Fixture User" not in profile_text
    assert "raw_profile_body_should_not_render" not in profile_text
    results.append(("archives_user_profile_standard_source_result", "passed"))

    related_plan = build_archives_related_users_browser_backed_request("2871834924", "same_device_login")
    assert related_plan["action_name"] == "archives_related_users"
    assert related_plan["fixed_path"] == ARCHIVES_RELATED_USERS_FIXED_PATH
    assert related_plan["typed_params"]["user_id"] == "2871834924"
    assert related_plan["typed_params"]["inputType"] == 0
    assert related_plan["typed_params"]["type"] == 1
    assert related_plan["body_builder_summary"]["keyword_source"] == "user_id"
    serialized_related_plan = json.dumps(related_plan, ensure_ascii=True)
    assert "cookie" not in serialized_related_plan.lower()
    assert "token" not in serialized_related_plan.lower()
    assert "session" not in serialized_related_plan.lower()
    assert "/archives/user/search/device" in serialized_related_plan
    assert "http://" not in serialized_related_plan.lower()
    assert "https://" not in serialized_related_plan.lower()
    results.append(("archives_related_users_typed_request_plan", "passed"))

    related_opener = _FakeOpener(_fixture_payload("archives_related_users", "completed"))
    client = BrowserBackedServiceClient(opener=related_opener)
    related_result = client.call_action("archives_related_users", related_plan["typed_params"])
    assert related_opener.calls[0]["url"].endswith(ACTION_ENDPOINTS["archives_related_users"])
    assert related_result["source_status"] == "completed"
    assert related_result["key_entities"]["related_user_ids"] == ["772671837", "3481089791", "2871834924"]
    related_card = build_partial_evidence_card([related_result])
    related_summary = related_card["evidence_summary_by_source"]["archives_related_users"]
    assert related_summary["action_contract"]["fixed_path"] == ARCHIVES_RELATED_USERS_FIXED_PATH
    assert related_summary["related_users_summary"]["related_user_count"] == 3
    assert related_summary["key_entities"]["related_user_ids"] == ["772671837", "3481089791", "2871834924"]
    related_text = json.dumps(related_card, ensure_ascii=True)
    assert "raw_related_user_profile_should_not_render" not in related_text
    results.append(("archives_related_users_standard_source_result", "passed"))

    private_message_plan = build_archives_private_message_search_browser_backed_request(
        "2871834924",
        direction="sent",
    )
    assert private_message_plan["action_name"] == "archives_private_message_search"
    assert private_message_plan["fixed_path"] == ARCHIVES_PRIVATE_MESSAGE_SEARCH_FIXED_PATH
    assert private_message_plan["typed_params"]["direction"] == "sent"
    assert private_message_plan["body_builder_summary"]["direction_mapping"]["sent"] == "fromUserId"
    serialized_private_message_plan = json.dumps(private_message_plan, ensure_ascii=True)
    assert "cookie" not in serialized_private_message_plan.lower()
    assert "token" not in serialized_private_message_plan.lower()
    assert "session" not in serialized_private_message_plan.lower()
    assert "/archives/user/message/search" in serialized_private_message_plan
    assert "http://" not in serialized_private_message_plan.lower()
    assert "https://" not in serialized_private_message_plan.lower()
    results.append(("archives_private_message_search_typed_request_plan", "passed"))

    private_message_opener = _FakeOpener(_fixture_payload("archives_private_message_search", "completed"))
    client = BrowserBackedServiceClient(opener=private_message_opener)
    private_message_result = client.call_action("archives_private_message_search", private_message_plan["typed_params"])
    assert private_message_opener.calls[0]["url"].endswith(ACTION_ENDPOINTS["archives_private_message_search"])
    assert private_message_result["source_status"] == "completed"
    assert private_message_result["key_entities"]["counterpart_user_ids"] == ["772671837", "3481089791"]
    assert private_message_result["missing_fields"] == ["message_risk_policy_attribution"]
    private_message_card = build_partial_evidence_card([private_message_result])
    private_message_summary = private_message_card["evidence_summary_by_source"]["archives_private_message_search"]
    assert private_message_summary["action_contract"]["fixed_path"] == ARCHIVES_PRIVATE_MESSAGE_SEARCH_FIXED_PATH
    assert private_message_summary["private_message_summary"]["private_message_count"] == 12
    private_message_text = json.dumps(private_message_card, ensure_ascii=True)
    assert "raw_private_message_text_should_not_render" not in private_message_text
    assert "raw_private_message_plaintext_should_not_render" not in private_message_text
    assert "full_message_text_should_not_render" not in private_message_text
    assert "raw_counterpart_nickname_should_not_render" not in private_message_text
    assert '"messageContent":' not in private_message_text
    assert '"privateMessagePlaintext":' not in private_message_text
    results.append(("archives_private_message_search_standard_source_result", "passed"))

    four_items_plan = build_archives_past_four_items_browser_backed_request(
        "2871834924",
        info_type="profile_description",
    )
    assert four_items_plan["action_name"] == "archives_past_four_items"
    assert four_items_plan["fixed_path"] == ARCHIVES_PAST_FOUR_ITEMS_FIXED_PATH
    assert four_items_plan["typed_params"]["infoType"] == 3
    assert four_items_plan["body_builder_summary"]["keyword_source"] == "user_id"
    serialized_four_items_plan = json.dumps(four_items_plan, ensure_ascii=True)
    assert "cookie" not in serialized_four_items_plan.lower()
    assert "token" not in serialized_four_items_plan.lower()
    assert "session" not in serialized_four_items_plan.lower()
    assert "/v4/audit/user/fourinfo/log/search" in serialized_four_items_plan
    assert "http://" not in serialized_four_items_plan.lower()
    assert "https://" not in serialized_four_items_plan.lower()
    results.append(("archives_past_four_items_typed_request_plan", "passed"))

    four_items_opener = _FakeOpener(_fixture_payload("archives_past_four_items", "completed"))
    client = BrowserBackedServiceClient(opener=four_items_opener)
    four_items_result = client.call_action("archives_past_four_items", four_items_plan["typed_params"])
    assert four_items_opener.calls[0]["url"].endswith(ACTION_ENDPOINTS["archives_past_four_items"])
    assert four_items_result["source_status"] == "completed"
    assert four_items_result["key_entities"]["user_id"] == "2871834924"
    assert four_items_result["missing_fields"] == ["login_or_publish_alignment"]
    four_items_card = build_partial_evidence_card([four_items_result])
    four_items_summary = four_items_card["evidence_summary_by_source"]["archives_past_four_items"]
    assert four_items_summary["action_contract"]["fixed_path"] == ARCHIVES_PAST_FOUR_ITEMS_FIXED_PATH
    assert four_items_summary["four_info_change_summary"]["total_changes"] == 6
    four_items_text = json.dumps(four_items_card, ensure_ascii=True)
    assert "raw_old_profile_value_should_not_render" not in four_items_text
    assert "raw_new_profile_value_should_not_render" not in four_items_text
    assert "raw_avatar_should_not_render" not in four_items_text
    assert "raw_background_should_not_render" not in four_items_text
    assert "raw_profile_description_should_not_render" not in four_items_text
    assert "raw_operator_name_should_not_render" not in four_items_text
    assert "full_four_info_raw_should_not_render" not in four_items_text
    assert '"oldValue":' not in four_items_text
    assert '"newValue":' not in four_items_text
    assert '"avatarUrl":' not in four_items_text
    results.append(("archives_past_four_items_standard_source_result", "passed"))

    rcp_detail_plan = build_rcp_event_detail_browser_backed_request(
        "USER_REGISTER_NEW",
        "5370247893355116990",
        1779774526479,
    )
    assert rcp_detail_plan["action_name"] == "rcp_event_detail"
    assert rcp_detail_plan["fixed_path"] == RCP_EVENT_DETAIL_FIXED_PATH
    assert rcp_detail_plan["typed_params"]["eventType"] == "USER_REGISTER_NEW"
    assert rcp_detail_plan["typed_params"]["eventId"] == "5370247893355116990"
    assert rcp_detail_plan["typed_params"]["queryTime"] == 1779774526479
    serialized_rcp_detail_plan = json.dumps(rcp_detail_plan, ensure_ascii=True)
    assert "cookie" not in serialized_rcp_detail_plan.lower()
    assert "token" not in serialized_rcp_detail_plan.lower()
    assert "session" not in serialized_rcp_detail_plan.lower()
    assert "/v2/rest/event/rcpEventDetail" in serialized_rcp_detail_plan
    assert "http://" not in serialized_rcp_detail_plan.lower()
    assert "https://" not in serialized_rcp_detail_plan.lower()
    results.append(("rcp_event_detail_typed_request_plan", "passed"))

    rcp_detail_opener = _FakeOpener(_fixture_payload("rcp_event_detail", "completed"))
    client = BrowserBackedServiceClient(opener=rcp_detail_opener)
    rcp_detail_result = client.call_action("rcp_event_detail", rcp_detail_plan["typed_params"])
    assert rcp_detail_opener.calls[0]["url"].endswith(ACTION_ENDPOINTS["rcp_event_detail"])
    assert rcp_detail_result["source_status"] == "completed"
    assert rcp_detail_result["key_entities"]["eventId"] == "5370247893355116990"
    assert rcp_detail_result["key_entities"]["deviceId"] == "ANDROID_rcp_detail_device_001"
    assert rcp_detail_result["missing_fields"] == ["policyTreeNodeCode"]
    assert rcp_detail_result["sensitive_output"] is False
    assert rcp_detail_result["no_data_not_risk_exclusion"] is True
    rcp_detail_card = build_partial_evidence_card([rcp_detail_result])
    rcp_detail_summary = rcp_detail_card["evidence_summary_by_source"]["rcp_event_detail"]
    assert rcp_detail_summary["action_contract"]["fixed_path"] == RCP_EVENT_DETAIL_FIXED_PATH
    assert rcp_detail_summary["event_detail_summary"]["hit_policy_count"] == 2
    rcp_detail_text = json.dumps(rcp_detail_card, ensure_ascii=True)
    assert "raw_rcp_detail_body_should_not_render" not in rcp_detail_text
    assert '"rawDetailBody":' not in rcp_detail_text
    results.append(("rcp_event_detail_standard_source_result", "passed"))

    rcp_feature_plan = build_rcp_event_feature_list_browser_backed_request(
        "USER_REGISTER_NEW",
        "5370247893355116990",
        1779774526479,
    )
    assert rcp_feature_plan["action_name"] == "rcp_event_feature_list"
    assert rcp_feature_plan["fixed_path"] == RCP_EVENT_FEATURE_LIST_FIXED_PATH
    assert rcp_feature_plan["typed_params"]["featureGroup"] == ""
    serialized_rcp_feature_plan = json.dumps(rcp_feature_plan, ensure_ascii=True)
    assert "cookie" not in serialized_rcp_feature_plan.lower()
    assert "token" not in serialized_rcp_feature_plan.lower()
    assert "session" not in serialized_rcp_feature_plan.lower()
    assert "/v2/rest/event/rcpEventFeatureList" in serialized_rcp_feature_plan
    assert "http://" not in serialized_rcp_feature_plan.lower()
    assert "https://" not in serialized_rcp_feature_plan.lower()
    results.append(("rcp_event_feature_list_typed_request_plan", "passed"))

    try:
        build_rcp_event_feature_list_browser_backed_request(
            "USER_REGISTER_NEW",
            "5370247893355116990",
            1779774526479,
            feature_group="ORIG",
        )
        raise AssertionError("feature_group override was not rejected")
    except BrowserBackedServiceInputError:
        results.append(("rcp_event_feature_list_feature_group_override_rejected", "passed"))

    rcp_feature_opener = _FakeOpener(_fixture_payload("rcp_event_feature_list", "completed"))
    client = BrowserBackedServiceClient(opener=rcp_feature_opener)
    rcp_feature_result = client.call_action("rcp_event_feature_list", rcp_feature_plan["typed_params"])
    assert rcp_feature_opener.calls[0]["url"].endswith(ACTION_ENDPOINTS["rcp_event_feature_list"])
    assert rcp_feature_result["source_status"] == "completed"
    assert rcp_feature_result["key_entities"]["eventId"] == "5370247893355116990"
    assert rcp_feature_result["missing_fields"] == ["policy_condition_attribution"]
    rcp_feature_card = build_partial_evidence_card([rcp_feature_result])
    rcp_feature_summary = rcp_feature_card["evidence_summary_by_source"]["rcp_event_feature_list"]
    assert rcp_feature_summary["action_contract"]["fixed_path"] == RCP_EVENT_FEATURE_LIST_FIXED_PATH
    assert rcp_feature_summary["feature_snapshot_summary"]["feature_count"] == 519
    rcp_feature_text = json.dumps(rcp_feature_card, ensure_ascii=True)
    assert "raw_feature_value_should_not_render" not in rcp_feature_text
    assert "full_feature_value_should_not_render" not in rcp_feature_text
    assert '"rawFeatureValue":' not in rcp_feature_text
    assert '"featureValue":' not in rcp_feature_text
    results.append(("rcp_event_feature_list_standard_source_result", "passed"))

    policy_version_plan = build_rcp_policy_version_lookup_browser_backed_request(
        "USER_REGISTER_NEW",
        "5370247893355116990",
        "BS_fake_account_register_thirdPlatformAll_bindphone",
        5,
        1779774526479,
    )
    assert policy_version_plan["action_name"] == "rcp_policy_version_lookup"
    assert policy_version_plan["fixed_path"] == RCP_POLICY_VERSION_LOOKUP_FIXED_PATH
    assert policy_version_plan["typed_params"]["policyCode"] == "BS_fake_account_register_thirdPlatformAll_bindphone"
    assert policy_version_plan["typed_params"]["policyVersion"] == 5
    serialized_policy_version_plan = json.dumps(policy_version_plan, ensure_ascii=True)
    assert "cookie" not in serialized_policy_version_plan.lower()
    assert "token" not in serialized_policy_version_plan.lower()
    assert "session" not in serialized_policy_version_plan.lower()
    assert "/v2/rest/pc/policy/getPolicyVersionListByEvent" in serialized_policy_version_plan
    assert "http://" not in serialized_policy_version_plan.lower()
    assert "https://" not in serialized_policy_version_plan.lower()
    results.append(("rcp_policy_version_lookup_typed_request_plan", "passed"))

    policy_version_opener = _FakeOpener(_fixture_payload("rcp_policy_version_lookup", "completed"))
    client = BrowserBackedServiceClient(opener=policy_version_opener)
    policy_version_result = client.call_action("rcp_policy_version_lookup", policy_version_plan["typed_params"])
    assert policy_version_opener.calls[0]["url"].endswith(ACTION_ENDPOINTS["rcp_policy_version_lookup"])
    assert policy_version_result["source_status"] == "completed"
    assert policy_version_result["key_entities"]["policyCode"] == "BS_fake_account_register_thirdPlatformAll_bindphone"
    assert policy_version_result["missing_fields"] == ["policyTreeNodeCode"]
    policy_version_card = build_partial_evidence_card([policy_version_result])
    policy_version_summary = policy_version_card["evidence_summary_by_source"]["rcp_policy_version_lookup"]
    assert policy_version_summary["action_contract"]["fixed_path"] == RCP_POLICY_VERSION_LOOKUP_FIXED_PATH
    assert policy_version_summary["policy_version_summary"]["version_found"] is True
    policy_version_text = json.dumps(policy_version_card, ensure_ascii=True)
    assert "raw_policy_version_body_should_not_render" not in policy_version_text
    assert '"rawPolicyVersionBody":' not in policy_version_text
    results.append(("rcp_policy_version_lookup_standard_source_result", "passed"))

    policy_detail_plan = build_rcp_policy_detail_lookup_browser_backed_request(
        "BS_fake_account_register_thirdPlatformAll_bindphone",
        5,
    )
    assert policy_detail_plan["action_name"] == "rcp_policy_detail_lookup"
    assert policy_detail_plan["fixed_path"] == RCP_POLICY_DETAIL_LOOKUP_FIXED_PATH
    assert policy_detail_plan["typed_params"]["policyCode"] == "BS_fake_account_register_thirdPlatformAll_bindphone"
    assert policy_detail_plan["typed_params"]["policyVersion"] == 5
    serialized_policy_detail_plan = json.dumps(policy_detail_plan, ensure_ascii=True)
    assert "cookie" not in serialized_policy_detail_plan.lower()
    assert "token" not in serialized_policy_detail_plan.lower()
    assert "session" not in serialized_policy_detail_plan.lower()
    assert "/v2/rest/pro/policy/getPolicyDetailByVersion" in serialized_policy_detail_plan
    assert "/v2/rest/pro/policy/getPolicyAllVersion" in serialized_policy_detail_plan
    assert "/v2/rest/pc/policyReview/getRelationPolicyTree" in serialized_policy_detail_plan
    assert "http://" not in serialized_policy_detail_plan.lower()
    assert "https://" not in serialized_policy_detail_plan.lower()
    results.append(("rcp_policy_detail_lookup_typed_request_plan", "passed"))

    policy_detail_opener = _FakeOpener(_fixture_payload("rcp_policy_detail_lookup", "completed"))
    client = BrowserBackedServiceClient(opener=policy_detail_opener)
    policy_detail_result = client.call_action("rcp_policy_detail_lookup", policy_detail_plan["typed_params"])
    assert policy_detail_opener.calls[0]["url"].endswith(ACTION_ENDPOINTS["rcp_policy_detail_lookup"])
    assert policy_detail_result["source_status"] == "completed"
    assert policy_detail_result["key_entities"]["policyCode"] == "BS_fake_account_register_thirdPlatformAll_bindphone"
    assert policy_detail_result["missing_fields"] == ["event_attribution_for_specific_hit_path"]
    policy_detail_card = build_partial_evidence_card([policy_detail_result])
    policy_detail_summary = policy_detail_card["evidence_summary_by_source"]["rcp_policy_detail_lookup"]
    assert policy_detail_summary["action_contract"]["fixed_path"] == RCP_POLICY_DETAIL_LOOKUP_FIXED_PATH
    assert policy_detail_summary["policy_detail_summary"]["condition_count"] == 4
    policy_detail_text = json.dumps(policy_detail_card, ensure_ascii=True)
    assert "raw_policy_detail_body_should_not_render" not in policy_detail_text
    assert "raw_condition_expression_should_not_render" not in policy_detail_text
    assert '"rawPolicyDetailBody":' not in policy_detail_text
    assert '"conditionExpressionRaw":' not in policy_detail_text
    results.append(("rcp_policy_detail_lookup_standard_source_result", "passed"))

    release_plan = build_rcp_policy_release_record_lookup_browser_backed_request(
        "BS_fake_account_register_thirdPlatformAll_bindphone",
    )
    assert release_plan["action_name"] == "rcp_policy_release_record_lookup"
    assert release_plan["fixed_path"] == RCP_POLICY_RELEASE_LIST_FIXED_PATH
    assert release_plan["typed_params"]["policyCode"] == "BS_fake_account_register_thirdPlatformAll_bindphone"
    assert release_plan["typed_params"]["statusCode"] == ""
    assert release_plan["typed_params"]["page"] == 1
    assert release_plan["typed_params"]["size"] == 20
    serialized_release_plan = json.dumps(release_plan, ensure_ascii=True)
    assert "cookie" not in serialized_release_plan.lower()
    assert "token" not in serialized_release_plan.lower()
    assert "session" not in serialized_release_plan.lower()
    assert "/v2/rest/common/pipeline/list" in serialized_release_plan
    assert "/v2/rest/common/pipeline/selectInfo" in serialized_release_plan
    assert "http://" not in serialized_release_plan.lower()
    assert "https://" not in serialized_release_plan.lower()
    results.append(("rcp_policy_release_record_lookup_typed_request_plan", "passed"))

    release_opener = _FakeOpener(_fixture_payload("rcp_policy_release_record_lookup", "completed"))
    client = BrowserBackedServiceClient(opener=release_opener)
    release_result = client.call_action("rcp_policy_release_record_lookup", release_plan["typed_params"])
    assert release_opener.calls[0]["url"].endswith(ACTION_ENDPOINTS["rcp_policy_release_record_lookup"])
    assert release_result["source_status"] == "completed"
    assert release_result["key_entities"]["policyCode"] == "BS_fake_account_register_thirdPlatformAll_bindphone"
    assert release_result["missing_fields"] == ["event_attribution_for_specific_hit_path"]
    release_card = build_partial_evidence_card([release_result])
    release_summary = release_card["evidence_summary_by_source"]["rcp_policy_release_record_lookup"]
    assert release_summary["action_contract"]["fixed_path"] == RCP_POLICY_RELEASE_LIST_FIXED_PATH
    assert release_summary["release_record_summary"]["record_count"] == 4
    assert release_summary["release_record_summary"]["parsed_policy_versions"] == [2, 3, 4, 5]
    release_text = json.dumps(release_card, ensure_ascii=True)
    assert "raw_release_records_should_not_render" not in release_text
    assert "raw_pipeline_records_should_not_render" not in release_text
    assert "operator_identity_should_not_render" not in release_text
    assert "create_user_should_not_render" not in release_text
    assert '"rawReleaseRecords":' not in release_text
    assert '"pipelineRecordsRaw":' not in release_text
    assert '"operatorName":' not in release_text
    assert '"createUser":' not in release_text
    results.append(("rcp_policy_release_record_lookup_standard_source_result", "passed"))

    policy_tree_plan = build_rcp_policy_tree_lookup_browser_backed_request(
        "USER_REGISTER_NEW",
        887,
        target_policy_code="BS_fake_account_register_thirdPlatformAll_bindphone",
    )
    assert policy_tree_plan["action_name"] == "rcp_policy_tree_lookup"
    assert policy_tree_plan["fixed_path"] == RCP_POLICY_TREE_LOOKUP_FIXED_PATH
    assert policy_tree_plan["typed_params"]["policyTreeCode"] == "USER_REGISTER_NEW"
    assert policy_tree_plan["typed_params"]["policyTreeVersion"] == 887
    assert policy_tree_plan["typed_params"]["targetPolicyCode"] == "BS_fake_account_register_thirdPlatformAll_bindphone"
    serialized_policy_tree_plan = json.dumps(policy_tree_plan, ensure_ascii=True)
    assert "cookie" not in serialized_policy_tree_plan.lower()
    assert "token" not in serialized_policy_tree_plan.lower()
    assert "session" not in serialized_policy_tree_plan.lower()
    assert "/v2/rest/pro/policyTree/queryProPolicyTree" in serialized_policy_tree_plan
    assert "/v2/rest/pro/policyTree/policyTreeList" in serialized_policy_tree_plan
    assert "/v2/rest/pro/policyTree/queryBindingByNodeCode" in serialized_policy_tree_plan
    assert "/v2/rest/pro/policyTree/getAllPolicyCodeByPage" in serialized_policy_tree_plan
    assert "/v2/rest/pc/policytree/getPolicyTreeByVersion" in serialized_policy_tree_plan
    assert "http://" not in serialized_policy_tree_plan.lower()
    assert "https://" not in serialized_policy_tree_plan.lower()
    results.append(("rcp_policy_tree_lookup_typed_request_plan", "passed"))

    policy_tree_opener = _FakeOpener(_fixture_payload("rcp_policy_tree_lookup", "completed"))
    client = BrowserBackedServiceClient(opener=policy_tree_opener)
    policy_tree_result = client.call_action("rcp_policy_tree_lookup", policy_tree_plan["typed_params"])
    assert policy_tree_opener.calls[0]["url"].endswith(ACTION_ENDPOINTS["rcp_policy_tree_lookup"])
    assert policy_tree_result["source_status"] == "completed"
    assert policy_tree_result["key_entities"]["policyTreeNodeCode"] == "53187346034508"
    policy_tree_card = build_partial_evidence_card([policy_tree_result])
    policy_tree_summary = policy_tree_card["evidence_summary_by_source"]["rcp_policy_tree_lookup"]
    assert policy_tree_summary["action_contract"]["fixed_path"] == RCP_POLICY_TREE_LOOKUP_FIXED_PATH
    assert RCP_POLICY_TREE_BINDING_BY_NODE_FIXED_PATH in policy_tree_summary["action_contract"]["companion_readonly_paths"]
    assert RCP_POLICY_TREE_ALL_POLICY_CODE_FIXED_PATH in policy_tree_summary["action_contract"]["companion_readonly_paths"]
    assert policy_tree_summary["policy_tree_summary"]["node_code_source"] == "recursive_queryProPolicyTree_parse"
    assert policy_tree_summary["policy_tree_summary"]["node_binding_policy_count"] == 13
    assert policy_tree_summary["policy_tree_summary"]["all_policy_code_count"] == 20
    policy_tree_text = json.dumps(policy_tree_card, ensure_ascii=True)
    assert "raw_policy_tree_body_should_not_render" not in policy_tree_text
    assert "full_policy_tree_raw_should_not_render" not in policy_tree_text
    assert "raw_node_binding_list_should_not_render" not in policy_tree_text
    assert "raw_all_policy_code_list_should_not_render" not in policy_tree_text
    assert '"rawPolicyTreeBody":' not in policy_tree_text
    assert '"policyTreeRaw":' not in policy_tree_text
    assert '"rawNodeBindingList":' not in policy_tree_text
    assert '"rawAllPolicyCodeList":' not in policy_tree_text
    results.append(("rcp_policy_tree_lookup_standard_source_result", "passed"))

    node_attr_plan = build_rcp_node_policy_attribution_browser_backed_request(
        "USER_REGISTER_NEW",
        "5370247893355116990",
        "BS_fake_account_register_thirdPlatformAll_bindphone",
        5,
        1779774526479,
    )
    assert node_attr_plan["action_name"] == "rcp_node_policy_attribution"
    assert node_attr_plan["fixed_path"] == RCP_NODE_POLICY_ATTRIBUTION_FIXED_PATH
    assert node_attr_plan["typed_params"]["type"] == ""
    assert node_attr_plan["typed_params"]["region"] == "china"
    serialized_node_attr_plan = json.dumps(node_attr_plan, ensure_ascii=True)
    assert "cookie" not in serialized_node_attr_plan.lower()
    assert "token" not in serialized_node_attr_plan.lower()
    assert "session" not in serialized_node_attr_plan.lower()
    assert "/v2/rest/pc/policy/nodePolicyAttribution" in serialized_node_attr_plan
    assert "http://" not in serialized_node_attr_plan.lower()
    assert "https://" not in serialized_node_attr_plan.lower()
    results.append(("rcp_node_policy_attribution_typed_request_plan", "passed"))

    node_attr_opener = _FakeOpener(_fixture_payload("rcp_node_policy_attribution", "completed"))
    client = BrowserBackedServiceClient(opener=node_attr_opener)
    node_attr_result = client.call_action("rcp_node_policy_attribution", node_attr_plan["typed_params"])
    assert node_attr_opener.calls[0]["url"].endswith(ACTION_ENDPOINTS["rcp_node_policy_attribution"])
    assert node_attr_result["source_status"] == "completed"
    assert node_attr_result["key_entities"]["policyCode"] == "BS_fake_account_register_thirdPlatformAll_bindphone"
    assert node_attr_result["missing_fields"] == ["node_bind_policy_attribution"]
    node_attr_card = build_partial_evidence_card([node_attr_result])
    node_attr_summary = node_attr_card["evidence_summary_by_source"]["rcp_node_policy_attribution"]
    assert node_attr_summary["action_contract"]["fixed_path"] == RCP_NODE_POLICY_ATTRIBUTION_FIXED_PATH
    assert node_attr_summary["policy_attribution_summary"]["true_condition_count"] == 4
    node_attr_text = json.dumps(node_attr_card, ensure_ascii=True)
    assert "raw_condition_dump_should_not_render" not in node_attr_text
    assert "full_condition_list_should_not_render" not in node_attr_text
    assert "raw_feature_value_should_not_render" not in node_attr_text
    assert '"rawConditionDump":' not in node_attr_text
    assert '"conditionListRaw":' not in node_attr_text
    results.append(("rcp_node_policy_attribution_standard_source_result", "passed"))

    node_bind_plan = build_rcp_node_bind_policy_attribution_browser_backed_request(
        "USER_REGISTER_NEW",
        "5370247893355116990",
        1779774526479,
        "USER_REGISTER_NEW",
        887,
        "53187346034508",
    )
    assert node_bind_plan["action_name"] == "rcp_node_bind_policy_attribution"
    assert node_bind_plan["fixed_path"] == RCP_NODE_BIND_POLICY_ATTRIBUTION_FIXED_PATH
    assert node_bind_plan["typed_params"]["policyTreeNodeCode"] == "53187346034508"
    serialized_node_bind_plan = json.dumps(node_bind_plan, ensure_ascii=True)
    assert "cookie" not in serialized_node_bind_plan.lower()
    assert "token" not in serialized_node_bind_plan.lower()
    assert "session" not in serialized_node_bind_plan.lower()
    assert "/v2/rest/pc/policy/nodeBindPolicyAttribution" in serialized_node_bind_plan
    assert "http://" not in serialized_node_bind_plan.lower()
    assert "https://" not in serialized_node_bind_plan.lower()
    results.append(("rcp_node_bind_policy_attribution_typed_request_plan", "passed"))

    node_bind_opener = _FakeOpener(_fixture_payload("rcp_node_bind_policy_attribution", "completed"))
    client = BrowserBackedServiceClient(opener=node_bind_opener)
    node_bind_result = client.call_action("rcp_node_bind_policy_attribution", node_bind_plan["typed_params"])
    assert node_bind_opener.calls[0]["url"].endswith(ACTION_ENDPOINTS["rcp_node_bind_policy_attribution"])
    assert node_bind_result["source_status"] == "completed"
    assert node_bind_result["key_entities"]["policyTreeNodeCode"] == "53187346034508"
    node_bind_card = build_partial_evidence_card([node_bind_result])
    node_bind_summary = node_bind_card["evidence_summary_by_source"]["rcp_node_bind_policy_attribution"]
    assert node_bind_summary["action_contract"]["fixed_path"] == RCP_NODE_BIND_POLICY_ATTRIBUTION_FIXED_PATH
    assert node_bind_summary["node_binding_summary"]["target_policy_result"] is True
    node_bind_text = json.dumps(node_bind_card, ensure_ascii=True)
    assert "raw_node_binding_body_should_not_render" not in node_bind_text
    assert "full_nodebinding_policy_list_should_not_render" not in node_bind_text
    assert "raw_condition_dump_should_not_render" not in node_bind_text
    assert '"rawNodeBindingBody":' not in node_bind_text
    assert '"nodebindingPolicyListRaw":' not in node_bind_text
    results.append(("rcp_node_bind_policy_attribution_standard_source_result", "passed"))

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

    mock_invocation = run_mock_action_invocation(
        "archives_user_analysis",
        {
            "user_id": "2871834924",
            "beginTime": 1764201600000,
            "endTime": 1764288000000,
            "pageIndex": 1,
            "pageSize": 20,
        },
    )
    assert mock_invocation["source_status"] == "completed"
    assert mock_invocation["invocation_mode"] == "mock"
    assert mock_invocation["live_service_called"] is False
    assert mock_invocation["platform_called"] is False
    assert mock_invocation["default_runtime_routing"] is False
    assert mock_invocation["live_verified"] is False
    assert mock_invocation["fixed_action_endpoint"] == ACTION_ENDPOINTS["archives_user_analysis"]
    results.append(("explicit_action_mock_invocation", "passed"))

    try:
        parse_typed_params_json('{"header": "forbidden"}')
        raise AssertionError("forbidden CLI typed param was not rejected")
    except BrowserBackedServiceInputError:
        results.append(("explicit_action_cli_forbidden_typed_param_rejected", "passed"))

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
    for call in account_security_opener.calls:
        account_security_call_body = json.loads((call["body"] or b"{}").decode("utf-8"))
        assert "response_mode" not in account_security_call_body
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
    results.append(("call_account_security_sources_default_compat_summary", "passed"))
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
    parser.add_argument(
        "--action",
        choices=sorted(ACTION_ENDPOINTS),
        help="invoke a fixed browser-backed action in local mock mode",
    )
    parser.add_argument(
        "--typed-params-json",
        default="{}",
        help="JSON object with typed params for --action; URL/path/header/cookie/token/session keys are rejected",
    )
    parser.add_argument(
        "--live-service",
        action="store_true",
        help="call the fixed action on the local browser-backed service instead of local mock fixtures",
    )
    args = parser.parse_args(argv)

    if args.self_test:
        print(json.dumps(run_fixture_tests(), indent=2, sort_keys=True))
        return 0

    if args.action:
        try:
            typed_params = parse_typed_params_json(args.typed_params_json)
            result = run_action_invocation(args.action, typed_params, live_service=args.live_service)
        except BrowserBackedServiceInputError as exc:
            parser.error(str(exc))
        print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
