#!/usr/bin/env python3
"""Executable client for the local browser-backed source service.

This module intentionally keeps Dennis out of browser ownership and auth
material handling. It only calls fixed local service actions with typed JSON
parameters and interprets safe passthrough envelopes for Dennis-side source
completion matrix / partial evidence card generation.
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
RESPONSE_MODE_PASSTHROUGH = "passthrough"
RESPONSE_MODES = {RESPONSE_MODE_PASSTHROUGH}
ACCOUNT_SECURITY_DEFAULT_RESPONSE_MODE = RESPONSE_MODE_PASSTHROUGH
PASSTHROUGH_PARSER_REGISTRY: Dict[str, Any] = {}

ACTION_ENDPOINTS = {
    "track_analysis_summary": "/actions/track_analysis_summary",
    "track_analysis_check_data_ready": "/actions/track_analysis_check_data_ready",
    "rcp_snapshot": "/actions/rcp_snapshot",
    "weapon_inventory": "/actions/weapon_inventory",
    "weapon_device_info": "/actions/weapon_device_info",
    "weapon_device_app_list": "/actions/weapon_device_app_list",
    "weapon_device_location_info": "/actions/weapon_device_location_info",
    "weapon_user_klink_status": "/actions/weapon_user_klink_status",
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
    "weapon_device_info": "weapon_device_info",
    "weapon_device_app_list": "weapon_device_app_list",
    "weapon_device_location_info": "weapon_device_location_info",
    "weapon_user_klink_status": "weapon_user_klink_status",
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
ACCOUNT_SECURITY_RISKDATA_DEVICE_PREFIXES = ("ANDROID_", "HARMONY_")
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
    "full" + "_json",
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
        response_mode: str = RESPONSE_MODE_PASSTHROUGH,
    ) -> Dict[str, Any]:
        """Call one fixed browser-backed action and interpret passthrough output.

        Transport failures are returned as source results instead of escaping as
        Dennis runtime failures.
        """

        _validate_action_name(action_name)
        if response_mode not in RESPONSE_MODES:
            raise BrowserBackedServiceInputError(
                "unsupported browser-backed response_mode: pure passthrough is the only runtime mode"
            )
        params = dict(typed_params or {})
        _validate_typed_params(params)
        request_params = dict(params)
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

        return normalize_passthrough_service_response(
            action_name,
            service_payload,
            http_status=http_status,
            request_params=request_params,
        )

    def call_account_security_sources(
        self,
        user_id: str,
        app_name: str = "KUAISHOU",
        include_rcp_snapshot: bool = True,
        response_mode: str = ACCOUNT_SECURITY_DEFAULT_RESPONSE_MODE,
    ) -> list[Dict[str, Any]]:
        """Call the default single-user account-security browser-backed sources.

        Track Analysis remains one evidence source, but its account-security
        bundle is collected through four explicit sub-interface calls before
        being merged into one display-safe source result.
        """

        if response_mode not in RESPONSE_MODES:
            raise BrowserBackedServiceInputError(
                "unsupported browser-backed response_mode: pure passthrough is the only runtime mode"
            )
        results: list[Dict[str, Any]] = []
        track_results: list[Dict[str, Any]] = []
        for request_plan in build_account_security_browser_backed_requests(
            user_id,
            app_name=app_name,
            include_rcp_snapshot=include_rcp_snapshot,
            expand_track_analysis_bundle=True,
        ):
            action_name = str(request_plan["action_name"])
            result = self.call_action(
                action_name,
                request_plan.get("typed_params", {}),
                response_mode=response_mode,
            )
            result["planned_source_name"] = request_plan.get("source_name")
            result["typed_params_summary"] = _typed_params_summary(request_plan.get("typed_params", {}))
            result["account_security_response_mode"] = response_mode
            if request_plan.get("bundle_source_name") == TRACK_ANALYSIS_BUNDLE_SOURCE_NAME:
                result["requested_track_sub_interface"] = request_plan.get("track_sub_interface")
                track_results.append(result)
                continue

            results.append(result)

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
    dennis_fields_observed: list[Any] = []
    dennis_samples: list[Any] = []
    profile_fields_observed: list[Any] = []
    profile_sections_observed: list[Any] = []
    dennis_records_count = 0
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
        observation = _result_observation(result)
        for field in observation.get("fields_observed", []) if isinstance(observation.get("fields_observed"), list) else []:
            if field not in dennis_fields_observed:
                dennis_fields_observed.append(field)
        for sample in observation.get("samples", []) if isinstance(observation.get("samples"), list) else []:
            if sample not in dennis_samples:
                dennis_samples.append(sample)
        if requested == "profile":
            profile_fields_observed = list(observation.get("profile_fields_observed", [])) if isinstance(observation.get("profile_fields_observed"), list) else []
            profile_sections_observed = list(observation.get("profile_sections_observed", [])) if isinstance(observation.get("profile_sections_observed"), list) else []
        if isinstance(observation.get("records_count"), int):
            dennis_records_count += int(observation["records_count"])

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
    dennis_source_quality = {
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
        "response_mode": RESPONSE_MODE_PASSTHROUGH,
    }
    dennis_observation: Dict[str, Any] = {
        "source_name": "track_analysis_summary",
        "source_status": source_status,
        "sub_interface": TRACK_ANALYSIS_BUNDLE_MODE,
        "sub_interfaces_completed": completed,
        "sub_interfaces_missing": missing,
        "records_count": dennis_records_count,
        "fields_observed": dennis_fields_observed[:64],
        "samples": dennis_samples[:8],
        "raw_body_suppressed": True,
        "no_data_not_risk_exclusion": True,
        "activity_signal_not_final_judgement": True,
    }
    if profile_fields_observed:
        dennis_observation["profile_fields_observed"] = profile_fields_observed
    if profile_sections_observed:
        dennis_observation["profile_sections_observed"] = profile_sections_observed
    if isinstance(device_ids_summary.get("device_ids_count"), int):
        dennis_observation["device_ids_count"] = device_ids_summary["device_ids_count"]
    if isinstance(use_duration_summary.get("rows_count"), int):
        dennis_observation["rows_count"] = use_duration_summary["rows_count"]
    return {
        "source_name": "track_analysis_summary",
        "planned_source_name": TRACK_ANALYSIS_BUNDLE_SOURCE_NAME,
        "action_name": "track_analysis_summary",
        "response_mode": dennis_source_quality["response_mode"],
        "account_security_response_mode": dennis_source_quality["response_mode"],
        "source_status": source_status,
        "failure_layer": "no_failure" if source_status == "completed" else "source_observation",
        "error_type": None,
        "latency_ms": total_latency,
        "dennis_generated_source_quality": dennis_source_quality,
        "dennis_observation": dennis_observation,
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
        result.get("dennis_observation"),
        result.get("response_shape_summary"),
        result.get("dennis_generated_source_quality"),
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
    """Reject removed service-side normalization payloads.

    Dennis runtime now consumes only pure passthrough envelopes. The former
    service-normalized response path is intentionally removed so callers cannot
    silently depend on `source_card`, service `source_quality`, or compat
    summaries.
    """

    _validate_action_name(action_name)
    raise BrowserBackedServiceInputError(
        "service-side normalized response mode was removed; use pure passthrough envelopes"
    )


def normalize_passthrough_service_response(
    action_name: str,
    service_payload: Mapping[str, Any],
    http_status: Optional[int] = None,
    request_params: Optional[Mapping[str, Any]] = None,
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
        dennis_observation = {
            "source_name": source_name,
            "source_status": "blocked",
            "error_type": "credential_material_violation",
            "raw_body_suppressed": True,
        }
        base.update(
            {
                "source_status": "blocked",
                "failure_layer": "sensitive_output_policy",
                "error_type": "credential_material_violation",
                "credential_material_violation": True,
                "dennis_observation": dennis_observation,
                "dennis_generated_source_quality": _passthrough_source_quality(
                    "blocked",
                    "credential_material_violation",
                    dennis_observation,
                ),
            }
        )
        return base

    base["safety"] = {"credential_material_output": False}
    service_error_type = service_payload.get("error_type")
    if service_error_type is None and isinstance(upstream, Mapping):
        service_error_type = upstream.get("error_type")
    if service_payload.get("ok") is False and service_error_type:
        source_status, failure_layer = _normalize_passthrough_service_failure(service_error_type)
        dennis_observation = {
            "source_name": source_name,
            "source_status": source_status,
            "error_type": service_error_type,
            "raw_body_suppressed": True,
        }
        base.update(
            {
                "source_status": source_status,
                "failure_layer": failure_layer,
                "error_type": service_error_type,
                "dennis_observation": dennis_observation,
                "dennis_generated_source_quality": _passthrough_source_quality(source_status, service_error_type, dennis_observation),
            }
        )
        return base

    if not isinstance(upstream, Mapping) or "body" not in upstream or upstream.get("body") is None:
        if service_payload.get("ok") is not True:
            source_status, failure_layer = _normalize_passthrough_service_failure(service_error_type or "passthrough_failed")
            dennis_observation = {
                "source_name": source_name,
                "source_status": source_status,
                "error_type": service_error_type or "passthrough_failed",
                "raw_body_suppressed": True,
            }
            base.update(
                {
                    "source_status": source_status,
                    "failure_layer": failure_layer,
                    "error_type": service_error_type or "passthrough_failed",
                    "dennis_observation": dennis_observation,
                    "dennis_generated_source_quality": _passthrough_source_quality(
                        source_status,
                        service_error_type or "passthrough_failed",
                        dennis_observation,
                    ),
                }
            )
            return base
        dennis_observation = {
            "source_name": source_name,
            "source_status": "parse_error",
            "error_type": "passthrough_body_missing",
            "raw_body_suppressed": True,
        }
        base.update(
            {
                "source_status": "parse_error",
                "failure_layer": "parser",
                "error_type": "passthrough_body_missing",
                "dennis_observation": dennis_observation,
                "dennis_generated_source_quality": _passthrough_source_quality(
                    "parse_error",
                    "passthrough_body_missing",
                    dennis_observation,
                ),
            }
        )
        return base

    dennis_observation = parse_passthrough_response(action_name, upstream.get("body"), request_params=request_params)
    normalized_status, failure_layer = _normalize_status(
        str(dennis_observation.get("source_status") or "completed"),
        dennis_observation.get("error_type"),
    )
    base.update(
        {
            "source_status": normalized_status,
            "failure_layer": failure_layer,
            "error_type": dennis_observation.get("error_type"),
            "dennis_observation": dennis_observation,
            "dennis_generated_source_quality": _passthrough_source_quality(
                normalized_status,
                dennis_observation.get("error_type"),
                dennis_observation,
            ),
            "no_data_not_risk_exclusion": bool(dennis_observation.get("no_data_not_risk_exclusion")),
        }
    )
    return base


def _passthrough_source_quality(
    source_status: str,
    error_type: Optional[Any],
    dennis_observation: Mapping[str, Any],
) -> Dict[str, Any]:
    return {
        "source_status": source_status,
        "error_type": error_type,
        "quality_status": "available" if source_status == "completed" else source_status,
        "response_mode": RESPONSE_MODE_PASSTHROUGH,
        "dennis_observation_present": bool(dennis_observation),
        "no_data_not_risk_exclusion": bool(dennis_observation.get("no_data_not_risk_exclusion")),
        "source_status_not_risk_exclusion": source_status in {
            "no_data",
            "blocked",
            "auth_failed",
            "timeout",
            "parse_error",
            "invalid_parameter",
        },
        "passthrough_default_path": True,
        "raw_body_suppressed": True,
        "raw_records_suppressed": bool(dennis_observation.get("raw_records_suppressed", True)),
        "raw_labelInfo_suppressed": bool(dennis_observation.get("raw_labelInfo_suppressed", True)),
        "raw_originalLog_suppressed": bool(dennis_observation.get("raw_originalLog_suppressed", True)),
        "redaction_applied": True,
        "raw_reference_retained_for_followup": False,
        "sensitive_output": False,
        "output_scope": DEFAULT_OUTPUT_SCOPE,
        "field_classification": _field_classification_summary(),
    }


def _normalize_passthrough_service_failure(error_type: Any) -> tuple[str, str]:
    error = str(error_type or "").strip().lower()
    if error in {"auth_failed", "auth_redirect", "auth_required", "login_page", "landing_flow_blocked"}:
        return "auth_failed", "auth_session"
    if error in {"timeout", "service_timeout", "navigation_timeout"}:
        return "timeout", "service_transport"
    if error in {"invalid_parameter", "parameter_error"}:
        return "invalid_parameter", "parameter_contract"
    return "blocked", "source_or_service"


def parse_passthrough_response(
    action_name: str,
    upstream_body: Any,
    request_params: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Parse passthrough upstream.body into a Dennis-owned observation."""

    _validate_action_name(action_name)
    parser = PASSTHROUGH_PARSER_REGISTRY.get(action_name)
    if parser is None:
        body = _coerce_json_body(upstream_body)
        fields_observed = _observed_field_names(body)
        rows = _extract_row_mappings(body)
        record_count = _infer_generic_record_count(body, rows)
        return {
            "source_name": ACTION_TO_SOURCE[action_name],
            "source_status": "completed" if record_count > 0 or fields_observed else "no_data",
            "records_count": record_count,
            "fields_observed": fields_observed,
            "samples": _generic_samples(body, rows),
            "raw_body_suppressed": True,
            "no_data_not_risk_exclusion": True,
        }
    return parser(upstream_body, request_params=request_params)


def _parse_track_analysis_passthrough(
    upstream_body: Any,
    request_params: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
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

    sub_interface = _detect_track_sub_interface(body, request_params=request_params)
    rows = _extract_row_mappings(body)
    device_ids = _extract_device_ids(body)
    fields_observed = _observed_field_names(body)
    samples = _track_analysis_samples(body, rows, device_ids, sub_interface)
    record_count = _infer_record_count(body, rows, device_ids, sub_interface)
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
        numeric_durations = [
            row.get("duration") or row.get("totalDuration") or row.get("activeDuration") or row.get("useDuration")
            for row in rows
        ]
        numeric_durations = [value for value in numeric_durations if isinstance(value, (int, float))]
        if numeric_durations:
            observation["total_duration"] = sum(numeric_durations)
    if device_ids:
        observation["device_ids_count"] = len(device_ids)
        observation["device_id_sample"] = _safe_display_value("device_id", device_ids[0], DEFAULT_OUTPUT_SCOPE)
    latest_datetime = _find_first(body, ("latestDateTime", "latest_datetime", "lastestDateTime"))
    if latest_datetime is not None:
        observation["latest_datetime_present"] = True
    uid_did_latest = _find_first(body, ("uidDidRelLatestDateTime", "uid_did_rel_latest_datetime"))
    if uid_did_latest is not None:
        observation["uid_did_relation_latest_datetime_present"] = True
    if sub_interface == "profile":
        profile = _track_profile_payload(body)
        observation["profile_fields_observed"] = _track_profile_fields_observed(body)
        observation["profile_sections_observed"] = _track_profile_sections_observed(body)
        if isinstance(profile, Mapping):
            observation["register_time_present"] = _find_first(
                profile,
                ("registerTime", "register_time", "registrationTime", "createTime"),
            ) is not None
            observation["fan_distribution_present"] = _find_first(
                profile,
                ("fanDistribution", "fan_distribution", "fansDistribution"),
            ) is not None
            observation["active_days_bucket_present"] = _find_first(
                profile,
                ("activeDaysBucket", "active_days_bucket", "activeDays", "active_days"),
            ) is not None
    return observation


def _parse_login_logs_passthrough(
    upstream_body: Any,
    request_params: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
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


def _parse_weapon_inventory_passthrough(
    upstream_body: Any,
    request_params: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    body = _coerce_json_body(upstream_body)
    source_name = "weapon_inventory"
    if not isinstance(body, (Mapping, list)):
        return {
            "source_name": source_name,
            "source_status": "parse_error",
            "error_type": "passthrough_body_not_structured_json",
            "fields_observed": [],
            "raw_body_suppressed": True,
            "raw_labelInfo_suppressed": True,
            "raw_originalLog_suppressed": True,
            "no_data_not_risk_exclusion": True,
        }

    graph = _extract_weapon_graph_container(body)
    point_info_map_present = isinstance(graph, Mapping) and isinstance(graph.get("pointInfoMap"), Mapping)
    relation_edge_list_present = isinstance(graph, Mapping) and isinstance(graph.get("relationEdgeList"), list)
    point_info_map = graph.get("pointInfoMap") if point_info_map_present else {}
    relation_edges = _extract_weapon_relation_edges(graph)
    device_ids, user_ids = _extract_weapon_graph_entities(point_info_map, relation_edges)
    risk = _extract_weapon_risk_container(body)
    risk_summary = _extract_weapon_risk_summary(risk if risk is not None else body)
    chain_status = _extract_weapon_chain_status(body)
    graph_present = isinstance(graph, Mapping) and ("pointInfoMap" in graph or "relationEdgeList" in graph)
    point_count = len(point_info_map) if isinstance(point_info_map, Mapping) else 0
    edge_count = len(relation_edges)
    risk_present = risk is not None
    has_graph_data = point_count > 0 or edge_count > 0
    has_risk_data = risk_summary["risk_item_count"] > 0 or risk_summary["risk_label_count"] > 0 or risk_summary["userLevel_observed"]
    source_status = "completed" if has_graph_data or has_risk_data else "no_data"
    risk_data_status = _weapon_risk_data_status(chain_status, risk_present, has_risk_data)

    return {
        "source_name": source_name,
        "source_status": source_status,
        "entity": _extract_passthrough_entity(body),
        "graph_status": "completed" if has_graph_data else ("no_data" if graph_present else "not_present"),
        "weapon_chain_graphData_status": chain_status.get("graphData_status"),
        "weapon_chain_riskData_status": chain_status.get("riskData_status"),
        "weapon_chain_selected_device_count": chain_status.get("selected_device_count"),
        "pointInfoMap_present": point_info_map_present,
        "pointInfoMap_count": point_count,
        "relationEdgeList_present": relation_edge_list_present,
        "relationEdgeList_count": edge_count,
        "related_device_count": len(device_ids),
        "related_user_count": len(user_ids),
        "device_id_samples": [_safe_display_value("device_id", value, DEFAULT_OUTPUT_SCOPE) for value in device_ids[:5]],
        "user_id_samples": [_safe_display_value("user_id", value, DEFAULT_OUTPUT_SCOPE) for value in user_ids[:5]],
        "riskData_status": risk_data_status,
        "risk_item_count": risk_summary["risk_item_count"],
        "risk_label_count": risk_summary["risk_label_count"],
        "risk_group_names_observed": risk_summary["risk_group_names_observed"],
        "readable_label_sample": risk_summary["readable_label_sample"],
        "userLevel_observed": risk_summary["userLevel_observed"],
        "raw_body_suppressed": True,
        "raw_labelInfo_suppressed": True,
        "raw_originalLog_suppressed": True,
        "no_data_not_risk_exclusion": True,
        "graphData_empty_not_risk_exclusion": True,
        "riskData_not_final_judgement": True,
    }


def _parse_rcp_snapshot_passthrough(
    upstream_body: Any,
    request_params: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    body = _coerce_json_body(upstream_body)
    source_name = "rcp_snapshot"
    if not isinstance(body, (Mapping, list)):
        return {
            "source_name": source_name,
            "source_status": "parse_error",
            "error_type": "passthrough_body_not_structured_json",
            "event_count": 0,
            "fields_observed": [],
            "raw_body_suppressed": True,
            "raw_eventList_full_dump_suppressed": True,
            "no_data_not_risk_exclusion": True,
        }

    event_list = _extract_rcp_event_list(body)
    table_headers = _extract_rcp_table_header_columns(body)
    returned_columns = _observed_event_columns(event_list)
    first_event_shape_keys = _safe_shape_keys(event_list[0]) if event_list else []
    source_status = "completed" if event_list else "no_data"
    return {
        "source_name": source_name,
        "source_status": source_status,
        "event_count": len(event_list),
        "pagination_summary": _extract_rcp_pagination_summary(body),
        "table_header_columns": table_headers,
        "returned_columns_observed": returned_columns,
        "first_event_shape_keys": first_event_shape_keys,
        "eventId_samples": _sample_event_values(event_list, ("eventId", "event_id")),
        "sourceId_samples": _sample_event_values(event_list, ("sourceId", "source_id")),
        "deviceId_samples": _sample_event_values(event_list, ("deviceId", "device_id", "did")),
        "hitFusePolicyCode_samples": _sample_event_values(event_list, ("hitFusePolicyCode", "policyCode", "policy_code")),
        "occurTime_samples": _sample_event_values(event_list, ("_occurTime", "occurTime", "occur_time", "hitTimestamp")),
        "raw_body_suppressed": True,
        "raw_eventList_full_dump_suppressed": True,
        "no_data_not_risk_exclusion": True,
        "eventList_not_final_judgement": True,
    }


PASSTHROUGH_PARSER_REGISTRY.update(
    {
        "track_analysis_summary": _parse_track_analysis_passthrough,
        "login_logs_search": _parse_login_logs_passthrough,
        "weapon_inventory": _parse_weapon_inventory_passthrough,
        "rcp_snapshot": _parse_rcp_snapshot_passthrough,
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


def _detect_track_sub_interface(body: Any, request_params: Optional[Mapping[str, Any]] = None) -> Optional[str]:
    request_hint = _track_sub_interface_hint(request_params)
    if request_hint and _track_body_supports_sub_interface(body, request_hint):
        return request_hint
    for key in ("sub_interface", "subInterface", "interface", "func", "function", "mode"):
        value = _find_first(body, (key,))
        if (
            isinstance(value, str)
            and value in ACCOUNT_SECURITY_TRACK_SUB_INTERFACES
            and _track_body_supports_sub_interface(body, value)
        ):
            return value
    if _track_profile_payload(body) is not None:
        return "profile"
    if _track_use_duration_rows(body):
        return "getUseDuration"
    if _track_device_payload(body):
        return "getDeviceIds"
    if _find_first(body, ("latestDateTime", "latest_datetime", "lastestDateTime", "getLastestDateTime")) is not None:
        return "getLastestDateTime"
    if _find_first(body, ("uidDidRelLatestDateTime", "uid_did_rel_latest_datetime")) is not None:
        return "getLastestDateTime"
    if _find_first(body, ("useDuration", "duration", "totalDuration", "activeDuration", "getUseDuration")) is not None:
        return "getUseDuration"
    if _find_first(body, ("registerTime", "activeDays", "fanDistribution", "userProfile", "profile")) is not None:
        return "profile"
    if request_hint:
        return request_hint
    return None


def _track_sub_interface_hint(request_params: Optional[Mapping[str, Any]]) -> Optional[str]:
    if not isinstance(request_params, Mapping):
        return None
    value = request_params.get("sub_interface") or request_params.get("subInterface")
    if isinstance(value, str) and value in ACCOUNT_SECURITY_TRACK_SUB_INTERFACES:
        return value
    return None


def _track_body_supports_sub_interface(body: Any, sub_interface: str) -> bool:
    if sub_interface == "profile":
        return _track_profile_payload(body) is not None
    if sub_interface == "getUseDuration":
        return bool(_track_use_duration_rows(body)) or _find_first(
            body,
            ("useDuration", "duration", "totalDuration", "activeDuration", "getUseDuration"),
        ) is not None
    if sub_interface == "getDeviceIds":
        return bool(_track_device_payload(body) or _extract_device_ids(body))
    if sub_interface == "getLastestDateTime":
        return _find_first(
            body,
            ("latestDateTime", "latest_datetime", "lastestDateTime", "getLastestDateTime", "uidDidRelLatestDateTime"),
        ) is not None
    return False


def _track_profile_payload(body: Any) -> Optional[Mapping[str, Any]]:
    if isinstance(body, Mapping):
        data = body.get("data")
        if isinstance(data, Mapping) and isinstance(data.get("profile"), Mapping):
            return data["profile"]
        if isinstance(body.get("profile"), Mapping):
            return body["profile"]
        user_profile = body.get("userProfile")
        if isinstance(user_profile, Mapping):
            return user_profile
    return None


def _track_use_duration_rows(body: Any) -> list[Mapping[str, Any]]:
    rows = _extract_row_mappings(body)
    result: list[Mapping[str, Any]] = []
    for row in rows:
        has_date = any(key in row for key in ("date", "dt", "day", "statDate"))
        has_duration = any(key in row for key in ("duration", "totalDuration", "activeDuration", "useDuration"))
        if has_date and has_duration:
            result.append(row)
    return result


def _track_device_payload(body: Any) -> list[Any]:
    if isinstance(body, list) and _is_track_device_array(body):
        return list(body)
    if isinstance(body, Mapping):
        data = body.get("data")
        if isinstance(data, list) and _is_track_device_array(data):
            return list(data)
        if _track_profile_payload(body) is None:
            device_ids = _find_first(body, ("deviceIds", "device_ids", "deviceIdList", "didList"))
            if isinstance(device_ids, list):
                return list(device_ids)
    return []


def _is_track_device_array(value: list[Any]) -> bool:
    if not value:
        return False
    for item in value[:5]:
        if isinstance(item, (str, int)):
            continue
        if isinstance(item, Mapping) and any(key in item for key in ("device_id", "deviceId", "did", "DID")):
            continue
        return False
    return True


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


def _infer_generic_record_count(body: Any, rows: list[Mapping[str, Any]]) -> int:
    if rows:
        return len(rows)
    count = _find_first(body, ("total", "totalCount", "count", "records_count", "event_count"))
    if isinstance(count, int):
        return max(count, 0)
    if isinstance(body, list):
        return len(body)
    if isinstance(body, Mapping) and body:
        return 1
    return 0


def _generic_samples(body: Any, rows: list[Mapping[str, Any]]) -> list[Any]:
    material = rows[:3] if rows else ([body] if isinstance(body, Mapping) else body[:3] if isinstance(body, list) else [])
    samples = []
    for item in material:
        if isinstance(item, Mapping):
            samples.append(_sanitize_display_material(item, DEFAULT_OUTPUT_SCOPE))
    return samples


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
    if sub_interface == "profile":
        profile_sample = _track_profile_sample(body)
        if profile_sample:
            samples.append(profile_sample)
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


def _track_profile_fields_observed(body: Any) -> list[str]:
    profile = _track_profile_payload(body)
    return _observed_field_names(profile) if isinstance(profile, Mapping) else []


def _track_profile_sections_observed(body: Any) -> list[str]:
    profile = _track_profile_payload(body)
    if not isinstance(profile, Mapping):
        return []
    return [str(key) for key, value in profile.items() if isinstance(value, (Mapping, list)) and _is_safe_display_key(str(key))]


def _track_profile_sample(body: Any) -> Dict[str, Any]:
    profile = _track_profile_payload(body)
    if not isinstance(profile, Mapping):
        return {}
    sample: Dict[str, Any] = {}
    sample_fields = {
        "register_time": ("registerTime", "register_time", "registrationTime", "createTime"),
        "fan_distribution": ("fanDistribution", "fan_distribution", "fansDistribution"),
        "active_days_bucket": ("activeDaysBucket", "active_days_bucket", "activeDays", "active_days"),
        "country": ("country",),
        "province": ("province",),
        "city": ("city",),
        "user_type_30d": ("userType30d", "user_type_30d"),
        "channel_type": ("channelType", "channel_type"),
    }
    for output_key, candidates in sample_fields.items():
        value = _find_first(profile, candidates)
        if value is not None:
            sample[output_key] = _safe_display_value(output_key, value, DEFAULT_OUTPUT_SCOPE)
    return sample


def _infer_record_count(
    body: Any,
    rows: list[Mapping[str, Any]],
    device_ids: list[Any],
    sub_interface: Optional[str] = None,
) -> int:
    if sub_interface == "profile" and _track_profile_payload(body) is not None:
        return 1
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


def _extract_weapon_graph_container(body: Any) -> Mapping[str, Any]:
    for candidate in _candidate_mappings(body):
        if "pointInfoMap" in candidate or "relationEdgeList" in candidate:
            return candidate
        graph_data = candidate.get("graphData")
        if isinstance(graph_data, Mapping) and ("pointInfoMap" in graph_data or "relationEdgeList" in graph_data):
            return graph_data
        if isinstance(graph_data, Mapping) and isinstance(graph_data.get("data"), Mapping):
            data = graph_data["data"]
            if "pointInfoMap" in data or "relationEdgeList" in data:
                return data
    return {}


def _extract_weapon_relation_edges(graph: Any) -> list[Mapping[str, Any]]:
    if not isinstance(graph, Mapping):
        return []
    edges = graph.get("relationEdgeList")
    if not isinstance(edges, list):
        return []
    return [edge for edge in edges if isinstance(edge, Mapping)]


def _extract_weapon_risk_container(body: Any) -> Optional[Any]:
    if isinstance(body, Mapping) and "riskDataResults" in body:
        return body.get("riskDataResults")
    for candidate in _candidate_mappings(body):
        if "riskDataResults" in candidate:
            return candidate.get("riskDataResults")
        risk_data = candidate.get("riskData")
        if risk_data is not None:
            return risk_data
        if any(key in candidate for key in ("labelInfo", "riskItems", "riskLabels", "userLevel", "riskGroupName")):
            return candidate
    return None


def _candidate_mappings(body: Any) -> list[Mapping[str, Any]]:
    candidates: list[Mapping[str, Any]] = []
    if isinstance(body, Mapping):
        candidates.append(body)
        for key in ("payload", "data", "result", "body", "graphData", "riskData", "weapon_chain"):
            child = body.get(key)
            if isinstance(child, Mapping):
                candidates.extend(_candidate_mappings(child))
    return candidates


def _extract_weapon_graph_entities(
    point_info_map: Mapping[str, Any],
    relation_edges: list[Mapping[str, Any]],
) -> tuple[list[Any], list[Any]]:
    device_ids: list[Any] = []
    user_ids: list[Any] = []

    def add_entity(key: str, value: Any) -> None:
        entity_type = _classify_weapon_entity(key, value)
        if entity_type == "device_id" and value not in device_ids:
            device_ids.append(value)
        elif entity_type == "user_id" and value not in user_ids:
            user_ids.append(value)

    for node_key, node_value in point_info_map.items():
        node_type = _weapon_node_type(node_value)
        add_entity(node_type or "pointInfoMap.key", node_key)
        if isinstance(node_value, Mapping):
            for nested_key, nested_value in node_value.items():
                if str(nested_key) in {"entityType", "nodeType", "type", "groupKey", "dimKey"}:
                    continue
                if not _is_weapon_identifier_field(str(nested_key)):
                    continue
                if isinstance(nested_value, (str, int)):
                    key_hint = node_type if node_type and str(nested_key).lower() in {"id", "value", "key"} else str(nested_key)
                    add_entity(key_hint, nested_value)
    for edge in relation_edges:
        for edge_key, edge_value in edge.items():
            if isinstance(edge_value, (str, int)):
                add_entity(str(edge_key), edge_value)

    return device_ids, user_ids


def _classify_weapon_entity(key: str, value: Any) -> Optional[str]:
    text = str(value)
    lowered_key = key.lower()
    if not text:
        return None
    if "device_id" in lowered_key or lowered_key in {"device", "deviceid", "did", "didlist"}:
        return "device_id"
    if lowered_key in {"device_id", "dim_device_id", "device_node", "type:device_id"}:
        return "device_id"
    if "user_id" in lowered_key or lowered_key in {"uid", "userid", "user"}:
        return "user_id" if text.isdigit() else None
    if lowered_key in {"type:user_id", "user_node"}:
        return "user_id" if text.isdigit() else None
    if "user" in lowered_key or lowered_key in {"uid", "userid"}:
        return "user_id" if text.isdigit() else None
    if "device" in lowered_key or lowered_key in {"did", "didlist"}:
        return "device_id"
    if text.isdigit():
        return "user_id"
    if _looks_like_weapon_device_id(text):
        return "device_id"
    return None


def _weapon_node_type(node_value: Any) -> Optional[str]:
    if not isinstance(node_value, Mapping):
        return None
    for key in ("entityType", "nodeType", "type", "groupKey", "dimKey"):
        value = node_value.get(key)
        if not isinstance(value, str):
            continue
        normalized = value.strip().upper()
        if normalized in {"DEVICE_ID", "DEVICE", "DID"}:
            return "type:device_id"
        if normalized in {"USER_ID", "USER", "UID"}:
            return "type:user_id"
    return None


def _is_weapon_identifier_field(key: str) -> bool:
    lowered = key.lower()
    return lowered in {
        "id",
        "value",
        "key",
        "entityid",
        "entity_id",
        "userid",
        "user_id",
        "uid",
        "deviceid",
        "device_id",
        "did",
        "didlist",
    }


def _looks_like_weapon_device_id(value: str) -> bool:
    text = str(value)
    if text.isdigit():
        return False
    if text.startswith(("ANDROID_", "HARMONY_")):
        return True
    # Legacy compatibility only. Current Weapon docs/tests use Android/Harmony,
    # raw UUID-like IDs, or long non-numeric IDs as the canonical device shapes.
    if text.startswith(("IOS_", "web_")):
        return True
    if re.fullmatch(r"[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}", text):
        return True
    if re.fullmatch(r"[0-9A-Fa-f]{16,64}", text):
        return True
    if len(text) >= 16 and re.fullmatch(r"[A-Za-z0-9._:-]+", text) and re.search(r"[A-Za-z]", text):
        return True
    return False


def _extract_weapon_chain_status(body: Any) -> Dict[str, Any]:
    chain = None
    if isinstance(body, Mapping):
        chain = body.get("weapon_chain")
    if not isinstance(chain, Mapping):
        return {}
    return {
        "graphData_status": _safe_display_value("status", chain.get("graphData_status"), DEFAULT_OUTPUT_SCOPE)
        if chain.get("graphData_status") is not None
        else None,
        "riskData_status": _safe_display_value("status", chain.get("riskData_status"), DEFAULT_OUTPUT_SCOPE)
        if chain.get("riskData_status") is not None
        else None,
        "selected_device_count": chain.get("selected_device_count") if isinstance(chain.get("selected_device_count"), int) else None,
    }


def _weapon_risk_data_status(chain_status: Mapping[str, Any], risk_present: bool, has_risk_data: bool) -> str:
    if has_risk_data:
        return "completed"
    chain_value = chain_status.get("riskData_status") if isinstance(chain_status, Mapping) else None
    if isinstance(chain_value, str) and chain_value:
        if chain_value in {"completed", "no_data", "not_executed", "not_executed_no_result", "missing_device_reference"}:
            return chain_value
        return str(chain_value)
    if risk_present:
        return "no_data"
    return "not_executed"


def _extract_weapon_risk_summary(risk_body: Any) -> Dict[str, Any]:
    risk_items = _extract_weapon_risk_items(risk_body)
    label_items = _extract_weapon_label_items(risk_body)
    risk_group_names = _unique_safe_values(_collect_values_for_keys(risk_body, ("riskGroupName", "groupName", "risk_group_name")))
    readable_labels = _unique_safe_values(
        _collect_values_for_keys(risk_body, ("readableLabel", "readable_label", "labelName", "label_name", "riskLabelName"))
    )
    if not readable_labels:
        readable_labels = _unique_safe_values(_label_item_names(label_items))
    return {
        "risk_item_count": len(risk_items),
        "risk_label_count": len(label_items),
        "risk_group_names_observed": risk_group_names[:8],
        "readable_label_sample": readable_labels[:8],
        "userLevel_observed": _contains_key_recursive(risk_body, ("userLevel", "user_level")),
    }


def _extract_weapon_risk_items(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if not isinstance(value, Mapping):
        return []
    for key in ("riskItems", "riskList", "riskData", "data", "result"):
        child = value.get(key)
        if isinstance(child, list):
            return child
        if isinstance(child, Mapping):
            nested = _extract_weapon_risk_items(child)
            if nested:
                return nested
    return [value] if any(key in value for key in ("labelInfo", "riskLabels", "userLevel", "riskGroupName")) else []


def _extract_weapon_label_items(value: Any) -> list[Any]:
    labels: list[Any] = []

    def visit(node: Any) -> None:
        if isinstance(node, Mapping):
            for key, child in node.items():
                if str(key) in {"labelInfo", "riskLabels", "labels", "riskLabelList"}:
                    if isinstance(child, list):
                        labels.extend(child)
                    elif isinstance(child, Mapping):
                        labels.extend(child.values())
                    elif child:
                        labels.append(child)
                    continue
                if str(key) in {"originalLog", "rawOriginalLog"}:
                    continue
                if isinstance(child, (Mapping, list)):
                    visit(child)
        elif isinstance(node, list):
            for item in node:
                visit(item)

    visit(value)
    return labels


def _label_item_names(items: list[Any]) -> list[Any]:
    names: list[Any] = []
    for item in items:
        if isinstance(item, Mapping):
            for key in ("readableLabel", "readable_label", "labelName", "label_name", "name", "label"):
                value = item.get(key)
                if isinstance(value, (str, int, float)):
                    names.append(value)
                    break
        elif isinstance(item, (str, int, float)):
            names.append(item)
    return names


def _collect_values_for_keys(value: Any, keys: Iterable[str]) -> list[Any]:
    wanted = set(keys)
    values: list[Any] = []

    def visit(node: Any) -> None:
        if isinstance(node, Mapping):
            for key, child in node.items():
                if str(key) in {"labelInfo", "originalLog", "rawOriginalLog"}:
                    if str(key) == "labelInfo":
                        visit(child)
                    continue
                if str(key) in wanted and isinstance(child, (str, int, float)):
                    values.append(child)
                elif isinstance(child, (Mapping, list)):
                    visit(child)
        elif isinstance(node, list):
            for item in node:
                visit(item)

    visit(value)
    return values


def _unique_safe_values(values: Iterable[Any]) -> list[Any]:
    result: list[Any] = []
    for value in values:
        if not isinstance(value, (str, int, float)):
            continue
        safe_value = _safe_display_value("risk_label", value, DEFAULT_OUTPUT_SCOPE)
        if safe_value not in result:
            result.append(safe_value)
    return result


def _contains_key_recursive(value: Any, keys: Iterable[str]) -> bool:
    wanted = set(keys)
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key) in wanted:
                return True
            if isinstance(child, (Mapping, list)) and _contains_key_recursive(child, wanted):
                return True
    elif isinstance(value, list):
        return any(_contains_key_recursive(item, wanted) for item in value)
    return False


def _extract_rcp_event_list(body: Any) -> list[Mapping[str, Any]]:
    if isinstance(body, list):
        return [item for item in body if isinstance(item, Mapping)]
    if not isinstance(body, Mapping):
        return []
    data = body.get("data")
    if isinstance(data, Mapping) and isinstance(data.get("eventList"), list):
        return [item for item in data["eventList"] if isinstance(item, Mapping)]
    if isinstance(body.get("eventList"), list):
        return [item for item in body["eventList"] if isinstance(item, Mapping)]
    return []


def _extract_rcp_pagination_summary(body: Any) -> Dict[str, Any]:
    pagination = None
    if isinstance(body, Mapping):
        data = body.get("data")
        if isinstance(data, Mapping):
            pagination = data.get("pagination") or data.get("pageInfo") or data.get("page")
        if pagination is None:
            pagination = body.get("pagination") or body.get("pageInfo") or body.get("page")
    if not isinstance(pagination, Mapping):
        return {}
    return _safe_passthrough_sample(
        pagination,
        ("page", "pageIndex", "pageSize", "size", "total", "totalCount", "hasMore"),
    )


def _extract_rcp_table_header_columns(body: Any) -> list[str]:
    table_columns = None
    if isinstance(body, Mapping):
        data = body.get("data")
        if isinstance(data, Mapping):
            table_columns = data.get("tableHeaderList") or data.get("tableHeaders")
        if table_columns is None:
            table_columns = body.get("tableHeaderList") or body.get("tableHeaders")
    if not isinstance(table_columns, list):
        return []
    columns: list[str] = []
    for header in table_columns:
        column = None
        if isinstance(header, str):
            column = header
        elif isinstance(header, Mapping):
            for key in ("dataIndex", "key", "prop", "field", "columnName", "name", "title"):
                value = header.get(key)
                if isinstance(value, str) and value:
                    column = value
                    break
        if column and _is_safe_display_key(column) and column not in columns:
            columns.append(column)
    return columns


def _observed_event_columns(event_list: list[Mapping[str, Any]]) -> list[str]:
    columns: list[str] = []
    for event in event_list[:5]:
        for key in event.keys():
            key_text = str(key)
            if _is_safe_display_key(key_text) and key_text not in columns:
                columns.append(key_text)
    return columns


def _sample_event_values(event_list: list[Mapping[str, Any]], keys: Iterable[str]) -> list[Any]:
    samples: list[Any] = []
    for event in event_list:
        value = _find_first(event, keys)
        if value is None:
            continue
        key_for_display = next(iter(keys), "value")
        safe_value = _safe_display_value(key_for_display, value, DEFAULT_OUTPUT_SCOPE)
        if safe_value not in samples:
            samples.append(safe_value)
        if len(samples) >= 5:
            break
    return samples


def _safe_passthrough_sample(value: Mapping[str, Any], candidate_keys: Iterable[str]) -> Dict[str, Any]:
    sample: Dict[str, Any] = {}
    for key in candidate_keys:
        found = _find_first(value, (key,))
        if found is not None:
            sample[key] = _safe_display_value(key, found, DEFAULT_OUTPUT_SCOPE)
    return sample


def build_source_completion_matrix(results: Iterable[Mapping[str, Any]]) -> Dict[str, Any]:
    """Bucket Dennis-interpreted source results for evidence rendering."""

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
            "dennis_observation_present": bool(_result_observation(result)),
            "dennis_generated_source_quality_present": bool(_result_quality(result)),
            "no_data_not_risk_exclusion": bool(result.get("no_data_not_risk_exclusion")),
            "source_status_not_risk_exclusion": status in {"no_data", "blocked", "auth_failed", "timeout", "parse_error", "invalid_parameter"},
            "sensitive_output": False,
        }
    return matrix


def build_partial_evidence_card(
    results: Iterable[Mapping[str, Any]],
    output_scope: str = DEFAULT_OUTPUT_SCOPE,
) -> Dict[str, Any]:
    """Build a display-safe partial evidence card from Dennis source results."""

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
                "dennis_observation_present": bool(_result_observation(result)),
                "dennis_generated_source_quality_present": bool(_result_quality(result)),
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
        "auth_failed_sources": matrix["auth_failed_sources"],
        "blocked_sources": matrix["blocked_sources"],
        "timeout_sources": matrix["timeout_sources"],
        "parse_error_sources": matrix["parse_error_sources"],
        "invalid_parameter_sources": matrix["invalid_parameter_sources"],
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
    """Extract display-safe business evidence from Dennis-owned observations."""

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
        source_quality = _result_quality(result)
        for sub_interface in source_quality.get("sub_interfaces_missing", []) if isinstance(source_quality.get("sub_interfaces_missing"), list) else []:
            missing.append(
                {
                    "source_name": source_name,
                    "reason": f"track_analysis_sub_interface_missing:{sub_interface}",
                    "caveat": "account-security track bundle is partial until this sub-interface is collected",
                }
            )
        observation = _result_observation(result)
        weapon_material = observation
        if source_name == "weapon_inventory" and _find_first(weapon_material, ("riskData_status",)) == "not_executed_missing_device_id":
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
    for key in (
        "dennis_generated_source_quality",
        "response_shape_summary",
        "dennis_observation",
    ):
        value = result.get(key)
        if isinstance(value, Mapping):
            merged[key] = _sanitize_display_material(value, output_scope)
    return merged


def _result_observation(result: Mapping[str, Any]) -> Dict[str, Any]:
    value = result.get("dennis_observation")
    return dict(value) if isinstance(value, Mapping) else {}


def _result_quality(result: Mapping[str, Any]) -> Dict[str, Any]:
    value = result.get("dennis_generated_source_quality")
    return dict(value) if isinstance(value, Mapping) else {}


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
            "cs" + "rf",
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
    if "device" in lowered or "did" in lowered or text.startswith(("ANDROID_", "HARMONY_", "IOS_")):
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
        "dennis_generated_source_quality_exists": bool(_result_quality(result)),
        "dennis_observation_exists": bool(_result_observation(result)),
        "response_mode": result.get("response_mode"),
        "sensitive_output": False,
        "raw_body_suppressed": True,
        "raw_records_full_dump_suppressed": True,
        "credential_secret_plaintext_suppressed": True,
        "no_data_not_risk_exclusion": bool(result.get("no_data_not_risk_exclusion")),
    }


def _track_analysis_summary(result: Mapping[str, Any], output_scope: str) -> Dict[str, Any]:
    material = _summary_material(result, output_scope)
    observation = material.get("dennis_observation") if isinstance(material.get("dennis_observation"), Mapping) else {}
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
    if observation:
        summary["dennis_observation_summary"] = _pick_fields(
            observation,
            (
                "sub_interface",
                "records_count",
                "rows_count",
                "device_ids_count",
                "profile_fields_observed",
                "profile_sections_observed",
                "fields_observed",
                "samples",
                "raw_body_suppressed",
            ),
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
    observation = material.get("dennis_observation") if isinstance(material.get("dennis_observation"), Mapping) else {}
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
        "hitFusePolicyCode": _find_first(material, ("hitFusePolicyCode_present", "hitFusePolicyCode", "hitFusePolicyCode_samples"), output_scope) is not None,
        "eventId": _find_first(material, ("eventId_present", "eventId", "eventId_samples"), output_scope) is not None,
        "sourceId": _find_first(material, ("sourceId_present", "sourceId", "sourceId_samples"), output_scope) is not None,
        "deviceId": _find_first(material, ("deviceId_present", "deviceId", "deviceId_samples"), output_scope) is not None,
        "_occurTime": _find_first(material, ("_occurTime_present", "_occurTime", "occurTime_samples"), output_scope) is not None,
    }
    if observation:
        summary["dennis_observation_summary"] = _pick_fields(
            observation,
            (
                "event_count",
                "pagination_summary",
                "returned_columns_observed",
                "eventId_samples",
                "sourceId_samples",
                "deviceId_samples",
                "hitFusePolicyCode_samples",
                "occurTime_samples",
                "raw_body_suppressed",
                "raw_eventList_full_dump_suppressed",
            ),
            output_scope,
        )
    summary["boundary"] = "RCP is a strategy event entry source, not a final risk judgement."
    return summary


def _weapon_summary(result: Mapping[str, Any], output_scope: str) -> Dict[str, Any]:
    material = _summary_material(result, output_scope)
    observation = material.get("dennis_observation") if isinstance(material.get("dennis_observation"), Mapping) else {}
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
    if observation:
        summary["dennis_observation_summary"] = _pick_fields(
            observation,
            (
                "graph_status",
                "pointInfoMap_count",
                "relationEdgeList_count",
                "related_device_count",
                "related_user_count",
                "device_id_samples",
                "user_id_samples",
                "riskData_status",
                "risk_item_count",
                "risk_label_count",
                "risk_group_names_observed",
                "readable_label_sample",
                "raw_body_suppressed",
                "raw_labelInfo_suppressed",
                "raw_originalLog_suppressed",
            ),
            output_scope,
        )
    return summary


def _login_logs_summary(result: Mapping[str, Any], output_scope: str) -> Dict[str, Any]:
    material = _summary_material(result, output_scope)
    observation = material.get("dennis_observation") if isinstance(material.get("dennis_observation"), Mapping) else {}
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
        bool(_result_observation(result))
        and bool(_result_quality(result))
        and result.get("latency_ms") is not None
        and result.get("sensitive_output") is False
    )
    if observation:
        summary["dennis_observation_summary"] = _pick_fields(
            observation,
            ("records_count", "fields_observed", "samples", "raw_records_suppressed"),
            output_scope,
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
    summary["dennis_action_observation"] = _pick_fields(
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
    dennis_observation = {
        "source_name": ACTION_TO_SOURCE[action_name],
        "source_status": normalized_status,
        "error_type": error_type,
        "raw_body_suppressed": True,
    }
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
        "dennis_observation": dennis_observation,
        "dennis_generated_source_quality": _synthetic_source_quality(normalized_status, error_type, detail=detail),
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


def _default_passthrough_body(action_name: str, typed_params: Mapping[str, Any]) -> Dict[str, Any]:
    user_id = str(typed_params.get("user_id") or typed_params.get("entity_id") or "2871834924")
    if action_name == "login_logs_search":
        return {
            "data": {
                "logSearchModels": [
                    {
                        "logSource": "APP_LOGIN",
                        "method": "PASSWORD",
                        "timestamp": 1764288000000,
                        "userId": user_id,
                        "deviceId": "ANDROID_login_device_001",
                        "userIpDesc": "10.20.30.40",
                    }
                ]
            }
        }
    if action_name == "track_analysis_summary":
        sub_interface = typed_params.get("sub_interface") or "profile"
        return {
            "data": {
                "profile": {
                    "firstLevelProfile": {
                        "userId": user_id,
                        "province": "Guangdong",
                        "city": "Shenzhen",
                        "registerTime": "2020-01-01",
                    }
                },
                "deviceIds": ["ANDROID_track_device_001"],
                "latestDateTime": "2026-05-28",
            },
            "sub_interface": sub_interface,
        }
    if action_name == "weapon_inventory":
        return {
            "data": {
                "graphData": {
                    "pointInfoMap": {
                        user_id: {"entityType": "USER_ID"},
                        "ANDROID_weapon_device_001": {"entityType": "DEVICE_ID"},
                    },
                    "relationEdgeList": [{"source": user_id, "target": "ANDROID_weapon_device_001"}],
                }
            }
        }
    if action_name == "rcp_snapshot":
        return {
            "data": {
                "eventList": [
                    {
                        "eventId": "evt_rcp_001",
                        "sourceId": user_id,
                        "deviceId": "ANDROID_rcp_device_001",
                        "hitFusePolicyCode": "BS_fake_account_register",
                        "_occurTime": "2026-05-29 10:00:00",
                    }
                ],
                "pagination": {"total": 1},
            }
        }
    return {
        "data": {
            "records": [
                {
                    "source_name": ACTION_TO_SOURCE[action_name],
                    "userId": user_id,
                    "eventId": "evt_fixture_001",
                }
            ],
            "total": 1,
        }
    }


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
    fixture_body = _default_passthrough_body(action_name, typed_params)
    client = BrowserBackedServiceClient() if live_service else BrowserBackedServiceClient(
        opener=_FakeOpener(_passthrough_fixture_payload(action_name, fixture_body))
    )
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
    )
    passthrough_request_body = json.loads((passthrough_opener.calls[0]["body"] or b"{}").decode("utf-8"))
    assert passthrough_request_body["response_mode"] == RESPONSE_MODE_PASSTHROUGH
    assert passthrough_result["response_mode"] == RESPONSE_MODE_PASSTHROUGH
    assert passthrough_result["source_status"] == "completed"
    assert passthrough_result["dennis_observation"]["records_count"] == 1
    assert passthrough_result["dennis_observation"]["raw_records_suppressed"] is True
    assert "source_card" not in passthrough_result
    assert "source_quality" not in passthrough_result
    assert passthrough_result["dennis_generated_source_quality"]["response_mode"] == RESPONSE_MODE_PASSTHROUGH
    assert passthrough_result["dennis_generated_source_quality"]["dennis_observation_present"] is True
    results.append(("passthrough_client_parses_upstream_body", "passed"))

    try:
        BrowserBackedServiceClient(opener=passthrough_opener).call_action(
            "login_logs_search",
            {"user_id": "fixture"},
            response_mode="compat_summary",
        )
    except BrowserBackedServiceInputError:
        results.append(("compat_summary_runtime_mode_removed", "passed"))
    else:
        raise AssertionError("compat_summary response mode must be rejected")

    summary_field_result = BrowserBackedServiceClient(
        opener=_FakeOpener(
            _passthrough_fixture_payload(
                "login_logs_search",
                passthrough_login_body,
                include_summary_fields=True,
            )
        )
    ).call_action("login_logs_search", {"user_id": "fixture"})
    assert summary_field_result["source_status"] == "completed"
    assert summary_field_result["unexpected_summary_fields"] == ["source_card", "source_quality"]
    assert "source_card" not in summary_field_result
    assert "source_quality" not in summary_field_result
    results.append(("service_summary_fields_not_consumed", "passed"))

    credential_violation = BrowserBackedServiceClient(
        opener=_FakeOpener(
            _passthrough_fixture_payload(
                "login_logs_search",
                passthrough_login_body,
                credential_material_output=True,
            )
        )
    ).call_action("login_logs_search", {"user_id": "fixture"})
    assert credential_violation["source_status"] == "blocked"
    assert credential_violation["error_type"] == "credential_material_violation"
    assert credential_violation["sensitive_output"] is False
    assert "source_card" not in credential_violation
    assert "source_quality" not in credential_violation
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
    ).call_action("login_logs_search", {"user_id": "fixture"})
    assert landing_flow_blocked["source_status"] == "auth_failed"
    assert landing_flow_blocked["failure_layer"] == "auth_session"
    assert landing_flow_blocked["error_type"] == "landing_flow_blocked"
    assert landing_flow_blocked["dennis_observation"]["error_type"] == "landing_flow_blocked"
    results.append(("passthrough_landing_flow_blocked_preserves_service_error", "passed"))

    missing_body_result = BrowserBackedServiceClient(
        opener=_FakeOpener(_passthrough_fixture_payload("login_logs_search", include_body=False))
    ).call_action("login_logs_search", {"user_id": "fixture"})
    assert missing_body_result["source_status"] == "parse_error"
    assert missing_body_result["error_type"] == "passthrough_body_missing"
    results.append(("passthrough_body_missing_marked", "passed"))

    track_profile_body = {
        "data": {
            "deviceIds": ["ANDROID_track_device_001", "IOS_track_device_002"],
            "profile": {
                "firstLevelProfile": {
                    "userId": "2871834924",
                    "province": "Guangdong",
                    "city": "Shenzhen",
                    "activeDaysBucket": "active_30d",
                    "registerTime": "2020-01-01",
                },
                "secondLevelProfile": [
                    {"label": "fanDistribution", "value": "bucketed"},
                ],
            },
            "latestDateTime": "2026-05-28",
        }
    }
    track_profile_result = BrowserBackedServiceClient(
        opener=_FakeOpener(_passthrough_fixture_payload("track_analysis_summary", track_profile_body))
    ).call_action(
        "track_analysis_summary",
        {"user_id": "2871834924", "appName": "KUAISHOU", "sub_interface": "profile"},
    )
    assert track_profile_result["dennis_observation"]["sub_interface"] == "profile"
    assert track_profile_result["dennis_observation"]["device_ids_count"] == 2
    results.append(("track_analysis_passthrough_observation", "passed"))

    weapon_graph_body = {
        "data": {
            "graphData": {
                "pointInfoMap": {
                    "2871834924": {"id": "2871834924", "entityType": "USER_ID"},
                    "ANDROID_c081c29a506f9db1": {"id": "ANDROID_c081c29a506f9db1", "entityType": "DEVICE_ID"},
                },
                "relationEdgeList": [
                    {"source": "2871834924", "target": "ANDROID_c081c29a506f9db1"},
                ],
            }
        }
    }
    weapon_result = BrowserBackedServiceClient(
        opener=_FakeOpener(_passthrough_fixture_payload("weapon_inventory", weapon_graph_body))
    ).call_action("weapon_inventory", {"user_id": "fixture"})
    assert weapon_result["source_status"] == "completed"
    assert weapon_result["dennis_observation"]["related_device_count"] == 1
    results.append(("weapon_passthrough_observation", "passed"))

    rcp_event_body = {
        "data": {
            "pagination": {"page": 1, "pageSize": 10, "total": 1},
            "eventList": [
                {
                    "eventId": "evt_rcp_001",
                    "sourceId": "src_rcp_001",
                    "deviceId": "ANDROID_rcp_device_001",
                    "hitFusePolicyCode": "BS_fake_account_register",
                    "_occurTime": "2026-05-29 10:00:00",
                }
            ],
        }
    }
    rcp_result = BrowserBackedServiceClient(
        opener=_FakeOpener(_passthrough_fixture_payload("rcp_snapshot", rcp_event_body))
    ).call_action("rcp_snapshot", {"entity_type": "user_id", "entity_id": "fixture"})
    assert rcp_result["source_status"] == "completed"
    assert rcp_result["dennis_observation"]["event_count"] == 1
    results.append(("rcp_passthrough_observation", "passed"))

    evidence_card = build_partial_evidence_card([passthrough_result, missing_body_result, landing_flow_blocked])
    assert evidence_card["completed_sources"] == ["login_logs_search"]
    assert "login_logs_search" in evidence_card["parse_error_sources"]
    assert "login_logs_search" in evidence_card["auth_failed_sources"]
    assert evidence_card["source_quality"]["login_logs_search"]["dennis_generated_source_quality_present"] is True
    serialized_card = json.dumps(evidence_card, ensure_ascii=True)
    assert "source_card" not in serialized_card
    assert "normalized_observation" not in serialized_card
    assert "compat_summary" not in serialized_card
    results.append(("partial_evidence_card_dennis_generated_only", "passed"))

    account_security_results = BrowserBackedServiceClient(
        opener=_FakeOpener(lambda request: _passthrough_fixture_payload(
            _action_name_from_url(request.full_url),
            _default_passthrough_body(_action_name_from_url(request.full_url), json.loads((request.data or b"{}").decode("utf-8"))),
        ))
    ).call_account_security_sources("2871834924")
    assert account_security_results[0]["dennis_observation"]["sub_interface"] == TRACK_ANALYSIS_BUNDLE_MODE
    assert all("source_card" not in result for result in account_security_results)
    assert all("source_quality" not in result for result in account_security_results)
    account_security_card = build_partial_evidence_card(account_security_results)
    assert account_security_card["source_completion_matrix"]["source_quality"]
    results.append(("account_security_passthrough_bundle", "passed"))

    small_batch = build_small_batch_evidence_output(
        [
            {"user_id": "772671837", "source_results": [passthrough_result]},
            {"user_id": "3481089791", "source_results": [missing_body_result]},
        ]
    )
    assert small_batch["execution_mode"] == "small_batch_execution_with_checkpoint"
    assert small_batch["user_count"] == 2
    results.append(("small_batch_passthrough_evidence", "passed"))

    return {
        "fixture_tests": len(results),
        "passed": [name for name, status in results if status == "passed"],
    }


def _action_name_from_url(url: str) -> str:
    path = urllib.parse.urlparse(url).path
    for action_name, endpoint in ACTION_ENDPOINTS.items():
        if path.endswith(endpoint):
            return action_name
    raise BrowserBackedServiceInputError(f"unknown action endpoint in fixture URL: {path}")

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
