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
import time
from functools import lru_cache
from typing import Any


CREDENTIAL_SECRET_KEYS = {
    "token", "accesstoken", "refreshtoken", "logintoken", "authtoken", "passtoken",
    "session", "sessionid", "cookie", "cookies", "authorization", "authheader",
    "rawauthheader", "password", "passwd", "secret", "credential", "ticket",
}

DEVICE_DETAIL_NON_DEVICE_SUBTREE_KEYS = {
    "userbehavior",
    "user_behavior",
    "userinfo",
    "user_info",
    "usercache",
    "user_cache",
    "userprofilechanged",
    "user_profile_changed",
    "userlastcomments",
    "user_last_comments",
    "usermessageusercnt",
    "user_message_user_cnt",
    "userchargeamountfen30d",
    "user_charge_amount_fen_30d",
    "userbanstatus",
    "user_ban_status",
    "query",
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

STRICT_PII_EXACT_KEYS = {
    "username",
    "rawusername",
    "nickname",
    "fromusername",
    "tousername",
    "reporterusername",
    "reporteruserprofile",
}

NONESSENTIAL_URL_KEYS = {
    "thumburl",
    "mediaurl",
    "relatedurl",
    "userhead",
    "rawuserhead",
    "fromuserhead",
    "touserhead",
    "reporterheadurl",
    "bgdupurl",
    "hddupurl",
    "frameurls",
    "image",
    "links",
    "url",
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
    "archives_comment_search": [
        "photo_id",
        "comment_id",
        "comment_text",
        "action_time",
        "target_user_id",
        "relation_type",
    ],
    "archives_private_message_search": [
        "message_id",
        "message_text",
        "sender",
        "receiver",
        "target_user_id",
        "action_time",
        "relation_type",
    ],
    "archives_related_users": [
        "related_user_id",
        "relation_type",
        "shared_device",
        "shared_login_or_register",
        "related_count",
    ],
    "archives_fans_list": [
        "target_user_id",
        "relation_type",
        "action_time",
    ],
    "archives_follow_list": [
        "target_user_id",
        "relation_type",
        "action_time",
    ],
    "archives_user_report_search": [
        "report_id",
        "report_time",
        "report_type",
        "feedback_object",
        "feedback_signal",
    ],
    "archives_negative_report": [
        "report_id",
        "report_time",
        "report_type",
        "feedback_object",
        "feedback_signal",
    ],
    "archives_review_logs": [
        "review_id",
        "review_result",
        "review_scene",
        "enforcement_action",
        "review_time",
        "enforcement_time",
        "policy_reason",
    ],
    "archives_punish_status": [
        "punish_id",
        "punish_type",
        "enforcement_action",
        "enforcement_time",
        "policy_reason",
        "photo_id",
        "user_id",
    ],
    "weapon_inventory": [
        "user_device_edge",
        "device_id",
        "risk_label",
        "graph_relation_count",
        "riskdata_status",
        "phone_model",
        "os_version",
        "app_version",
        "device_platform",
        "launch_count",
        "boot_duration",
        "lock_screen_enabled",
        "sim_present",
        "automation_service_detected",
        "script_risk",
        "device_reset_signal",
        "root_or_hook_signal",
        "frida_signal",
        "emulator_signal",
        "installed_app_list",
        "first_seen_time",
        "active_days",
    ],
    "weapon_device_info": [
        "device_id",
        "risk_label",
        "phone_model",
        "os_version",
        "app_version",
        "device_platform",
        "launch_count",
        "boot_duration",
        "lock_screen_enabled",
        "sim_present",
        "automation_service_detected",
        "script_risk",
        "device_reset_signal",
        "root_or_hook_signal",
        "frida_signal",
        "emulator_signal",
        "first_seen_time",
        "active_days",
    ],
    "weapon_device_app_list": [
        "device_id",
        "installed_app_list",
        "risk_app",
        "tool_app",
        "app_environment_signal",
    ],
    "weapon_device_location_info": [
        "device_id",
        "user_id",
        "ip_or_network",
        "location",
        "city",
        "province",
    ],
    "weapon_user_klink_status": [
        "user_id",
        "device_id",
        "klink_status",
        "session_status",
    ],
    "rcp_fast_query_hbase": [
        "event_id",
        "event_type",
        "event_time",
        "policy_code",
        "hit_policy",
        "risk_decision",
    ],
    "rcp_event_detail": [
        "event_id",
        "event_type",
        "event_time",
        "policy_code",
        "hit_policy",
        "risk_decision",
        "request_path",
        "request_scene",
        "entry",
        "action_type",
        "action_object",
        "task_type",
        "reward_type",
        "client_params",
        "app_version",
        "ua",
        "device_id",
        "ip_or_network",
        "frontend_activity_signal",
        "backend_action_signal",
        "time_delta_from_login_seconds",
        "time_delta_between_actions_seconds",
    ],
    "rcp_event_feature_list": [
        "event_id",
        "event_type",
        "event_time",
        "policy_code",
        "feature_group",
        "feature_key",
        "feature_name",
        "feature_value",
        "request_path",
        "request_scene",
        "action_type",
        "action_object",
        "task_type",
        "reward_type",
        "client_params",
        "frontend_activity_signal",
        "backend_action_signal",
    ],
}

BUSINESS_FIELD_ALIASES = {
    "user_id": {"user_id", "userId", "userID", "uid"},
    "device_id": {"device_id", "deviceId", "deviceid", "did", "loginDeviceId", "login_did"},
    "candidate_device_id": {"candidate_device_id", "candidateDeviceId", "device_id", "deviceId", "did"},
    "photo_id": {"photo_id", "photoId", "photoID", "content_id", "contentId"},
    "event_id": {"event_id", "eventId", "sourceId", "source_id"},
    "event_type": {"event_type", "eventType", "eventTypeCode", "eventTypeCodes"},
    "event_time": {"event_time", "eventTime", "queryTime", "hitTime", "createTime", "time"},
    "policy_code": {"policy_code", "policyCode", "hitFusePolicyCode", "policyTreeCode"},
    "hit_policy": {"hit_policy", "hitPolicy", "hitPolicies", "hitProductionPolicies", "policyName"},
    "risk_decision": {"risk_decision", "riskDecision", "decision", "riskResult", "result"},
    "request_path": {"request_path", "requestPath", "apiPath", "path", "urlPath", "uri", "interfacePath"},
    "request_scene": {"request_scene", "requestScene", "scene", "sceneType", "bizScene"},
    "entry": {"entry", "entryType", "entryScene", "entrance", "entranceType", "sourceEntry"},
    "action_type": {"action_type", "actionType", "operationType", "opType", "behaviorType"},
    "action_object": {"action_object", "actionObject", "objectId", "targetId", "resourceId", "itemId"},
    "task_type": {"task_type", "taskType", "missionType", "activityTaskType"},
    "reward_type": {"reward_type", "rewardType", "awardType", "incentiveType"},
    "client_params": {"client_params", "clientParams", "clientInfo", "deviceInfo", "requestParams", "params"},
    "app_version": {"app_version", "appVersion", "appVer", "clientVersion", "versionName"},
    "ua": {"ua", "UA", "userAgent", "user_agent", "browserUa"},
    "ip_or_network": {"ip_or_network", "ip", "clientIp", "requestIp", "network", "networkType"},
    "frontend_activity_signal": {"frontend_activity_signal", "frontendActivitySignal", "frontActivity", "frontendActivity"},
    "backend_action_signal": {"backend_action_signal", "backendActionSignal", "backendAction", "serverAction"},
    "time_delta_from_login_seconds": {"time_delta_from_login_seconds", "timeDeltaFromLogin", "loginActionDelta", "deltaFromLoginSeconds"},
    "time_delta_between_actions_seconds": {"time_delta_between_actions_seconds", "timeDeltaBetweenActions", "actionIntervalSeconds", "deltaBetweenActionsSeconds"},
    "feature_group": {"feature_group", "featureGroup", "featureGroupName"},
    "feature_key": {"feature_key", "featureKey"},
    "feature_name": {"feature_name", "featureName"},
    "feature_value": {"feature_value", "featureValue", "defaultFeatureValue", "value"},
    "token_event_id": {"tokenId", "token_id"},
    "login_time": {"login_time", "loginTime", "loginTimestamp", "timestamp", "event_time", "time"},
    "login_type": {"login_type", "loginType", "reset_login_type", "resetLoginType", "authType"},
    "login_source": {"login_source", "loginSource", "login_channel", "clientType", "platform", "loginPlatform", "logSource"},
    "login_device": {"login_device", "loginDevice", "loginDeviceId", "device_id", "deviceId", "did"},
    "ip_ua": {"ip", "loginIp", "clientIp", "requestIp", "ua", "UA", "userAgent", "user_agent", "browserUa"},
    "publish_time": {"publish_time", "publishTime", "createTime", "uploadTime", "upload_time", "create_time", "timeMillis"},
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
    "comment_id": {"comment_id", "commentId", "rootCommentId"},
    "comment_text": {"comment_text", "commentText", "commentContent"},
    "message_id": {"message_id", "messageId"},
    "message_text": {"message_text", "messageText", "contentNormalized", "title", "subTitle"},
    "sender": {"sender", "fromUserId", "fromUid"},
    "receiver": {"receiver", "toUserId", "toUid"},
    "target_user_id": {"target_user_id", "targetUserId", "authorId"},
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
    "report_id": {"report_id", "reportId", "feedbackId"},
    "report_time": {"report_time", "reportTime", "createTime", "time"},
    "report_type": {"report_type", "reportType"},
    "feedback_object": {"feedback_object", "feedbackObject", "detailInfo", "reportedObject"},
    "feedback_signal": {"feedback_signal", "reportSignal", "reportTimes", "reportedCount"},
    "review_id": {"review_id", "reviewId", "auditId"},
    "review_time": {"review_time", "reviewTime", "createTime"},
    "review_result": {"review_result", "reviewResult", "logType"},
    "punish_id": {"punish_id", "punishId"},
    "punish_type": {"punish_type", "punishType", "punishCode", "punishCodeNameB", "eventType"},
    "enforcement_action": {"enforcement_action", "enforcementAction", "requestSource", "desc"},
    "enforcement_time": {"enforcement_time", "enforcementTime", "createTime"},
    "policy_reason": {"policy_reason", "policyReason", "punishReason", "markCodeNameB", "bizAreaName", "subBizName"},
    "review_scene": {"review_scene", "reviewScene", "sourcePage"},
    "user_device_edge": {"user_device_edge", "edge", "pointInfoMap", "deviceId", "did"},
    "graph_relation_count": {"graph_relation_count", "relationCount", "edgeCount", "count"},
    "riskdata_status": {"riskdata_status", "riskData", "riskStatus"},
    "phone_model": {"phone_model", "phoneModel", "model", "deviceModel", "mobileModel", "machineModel", "hwModel"},
    "os_version": {"os_version", "osVersion", "systemVersion", "androidVersion", "iosVersion", "deviceOsVersion", "kernOsProductVersion", "kernelVersion"},
    "device_platform": {"device_platform", "devicePlatform", "appPlatform", "platform", "osName", "systemName", "productName"},
    "device_name": {"deviceName", "deviceName2", "kernHostname"},
    "device_hardware_model": {"hardwareType", "hwMachine", "hwProduct", "hwTarget", "deviceModel", "buildProduct", "buildBoard", "brand", "hardware", "cpuModel"},
    "cpu_core_count": {"hwNcpu", "hwLogicalcpu", "hwActivecpu", "hwAvailcpu", "hwPhysicalcpu", "hwPhysicalcpuMax", "cpuCoreCount", "cpuCores"},
    "memory_total": {"hwMemsize", "hwPhysmem", "hwUsermem", "systemMem", "totalMemory", "usedMemory"},
    "storage_total": {"diskSpace", "totalStorage", "sdTotalStorage"},
    "storage_free": {"diskFree", "systemMemFree", "sdUsedStorage", "usedStorage", "diskSpaceUsed"},
    "screen_resolution": {"resolution", "screenSize", "dpi"},
    "launch_count": {"launch_count", "launchCount", "startupCount", "startUpCount", "bootCount", "appLaunchCount", "launchTimes1d", "launchTimes7d", "launchTimes30d", "launchTimes90d", "launchTimes180d"},
    "boot_duration": {"boot_duration", "bootDuration", "bootDurationSeconds", "uptime", "upTime", "powerOnDuration", "kernWakeTime", "kernWakeTime", "bootTime", "kernBootTime", "startTime", "startTime2", "startupTime", "startupDurationms", "runningDurationms", "procesSystemUptime"},
    "lock_screen_enabled": {"lock_screen_enabled", "lockScreenEnabled", "hasLockScreen", "lockScreen", "screenLock", "lockScreenStatus", "deviceLocked"},
    "sim_present": {"sim_present", "simPresent", "hasSim", "hasSIM", "simCount", "simStatus", "isHasSimCard"},
    "charging_pattern": {"charging_pattern", "chargingPattern", "isCharging", "chargeStatus", "battery", "batteryTemperature"},
    "automation_service_detected": {"automation_service_detected", "automationServiceDetected", "accessibilityEnabled", "accessibilityService", "accessibilityServiceList", "installAccessibility", "autoService"},
    "script_risk": {"script_risk", "scriptRisk", "scriptDetected", "scriptSignal", "pluginVersion", "accessibilitySvc", "enabledAccessibilityServices"},
    "device_reset_signal": {"device_reset_signal", "deviceResetSignal", "resetSignal", "deviceReset", "resetTime", "resetTimeV2Ms", "bootId", "bootHashId"},
    "root_or_hook_signal": {"root_or_hook_signal", "rootOrHookSignal", "rootHookSignal", "xposed", "mountRiskCheck", "mountRiskPath", "inject", "jailbreakDetector", "jailbreak", "proxyDetector", "proxyV2"},
    "root_signal": {"root_signal", "rootSignal", "isRoot", "rooted", "rootCertificates"},
    "hook_signal": {"hook_signal", "hookSignal", "hookDetected"},
    "frida_signal": {"frida_signal", "fridaSignal", "fridaDetected", "frida"},
    "emulator_signal": {"emulator_signal", "emulatorSignal", "isEmulator", "simulator", "emulatorAndCloudphone"},
    "installed_app_list": {"installed_app_list", "installedApps", "appList", "installList", "installedAppList", "packageList", "appInfo", "packageName"},
    "installed_app_cluster": {"installed_app_cluster", "installedAppCluster", "appEnvironmentCluster"},
    "risk_app": {"risk_app", "riskApp", "riskApps", "riskyApp"},
    "tool_app": {"tool_app", "toolApp", "toolApps", "toolPackage"},
    "first_seen_time": {"first_seen_time", "firstSeenTime", "firstSeen", "firstAppearTime"},
    "active_days": {"active_days", "activeDays", "deviceActiveDays", "usageDays"},
    "device_age_days": {"device_age_days", "deviceAgeDays", "ageDays"},
    "account_device_count": {"account_device_count", "accountDeviceCount", "userDeviceCount"},
    "device_account_count": {"device_account_count", "deviceAccountCount", "linkedUserCount", "sameDeviceUserCount"},
    "endpoint_path": {"method", "path", "endpoint", "apiPath", "requestPath", "urlPath"},
    "network_context": {"clientIP", "clientIp", "sourceIp", "sourceIpv6", "ipv6", "dns", "interfaceData", "otherInterfaceData", "network", "networkType", "networkOperator", "mobileNetworkCode", "mobileCountryCode", "oneIpInfo", "bssid", "ssid", "ssidData", "mac", "routerMac", "networkLink"},
    "request_context": {"requestUri", "sourceType", "appKey", "ksAppId", "serverIp", "servertime", "timestamp", "sdkCollectTime", "sdkUploadTime"},
}

DEVICE_DETAIL_CANONICAL_FIELDS = {
    "phone_model",
    "os_version",
    "app_version",
    "device_platform",
    "device_name",
    "device_hardware_model",
    "cpu_core_count",
    "memory_total",
    "storage_total",
    "storage_free",
    "screen_resolution",
    "launch_count",
    "boot_duration",
    "lock_screen_enabled",
    "sim_present",
    "charging_pattern",
    "automation_service_detected",
    "script_risk",
    "device_reset_signal",
    "root_or_hook_signal",
    "root_signal",
    "hook_signal",
    "frida_signal",
    "emulator_signal",
    "installed_app_list",
    "installed_app_cluster",
    "risk_app",
    "tool_app",
    "first_seen_time",
    "active_days",
    "device_age_days",
    "account_device_count",
    "device_account_count",
    "network_context",
    "request_context",
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
    "event_type",
    "event_time",
    "hit_policy",
    "risk_decision",
    "token_event_id",
    "ip_ua",
    "publish_ip_ua",
    "operation_ip_ua",
    "endpoint_path",
    "request_path",
    "request_scene",
    "entry",
    "action_type",
    "action_object",
    "task_type",
    "reward_type",
    "client_params",
    "app_version",
    "ua",
    "ip_or_network",
    "frontend_activity_signal",
    "backend_action_signal",
    "time_delta_from_login_seconds",
    "time_delta_between_actions_seconds",
    "feature_group",
    *DEVICE_DETAIL_CANONICAL_FIELDS,
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

EMBEDDED_JSON_PARSE_MAX_CHARS = 200_000
EMBEDDED_JSON_SKIP_KEYS = {"logcontent", "html", "text", "description", "stacktrace"}

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
MAX_RCP_EVENT_FEATURE_ROWS = 2000
MAX_RETAINED_FIELD_PATHS = 120

# ── Observation/display-layer bounded rendering limits ─────────────────────
# These apply ONLY to _project_evidence_body (safe_observation display).
# They do NOT affect _extract_handles / _extract_device_detail_rows /
# _extract_rcp_strategy_event_feature_rows which feed the L3 fact tables.
PROJECTION_MAX_DEPTH = 5           # stop deep-recursing at this depth
PROJECTION_MAX_OBJ_KEYS = 80       # max dict keys kept per level (non-anchor keys truncated)
PROJECTION_OBS_ARRAY_ITEMS = 60    # default max array items in safe_observation display
# Per-source tighter caps for known large-body sources
PROJECTION_SLOW_THRESHOLD_MS = 5_000   # ms — mark source as slow if projection exceeds this
PROJECTION_VERY_SLOW_THRESHOLD_MS = 10_000  # ms — mark source as very_slow

PROJECTION_OBS_ARRAY_CAP_BY_SOURCE: dict[str, int] = {
    "rcp_event_feature_list":             80,
    "archives_private_message_search":    30,
    "archives_comment_search":            30,
    "archives_gallery_photo_list":        40,
    "archives_photo_search":              40,
    "archives_photo_profile":             40,
    "archives_photo_meta":                40,
    "weapon_device_info":                 60,
    "weapon_inventory":                   60,
    "weapon_device_app_list":             60,
    "login_logs_search":                  50,
}

RAW_DETAIL_UNKNOWN_RETENTION_ACTIONS = {
    "login_logs_search",
    "archives_user_analysis",
    "archives_user_profile",
    "archives_photo_search",
    "archives_photo_profile",
    "archives_photo_meta",
    "archives_gallery_photo_list",
    "archives_comment_search",
    "archives_private_message_search",
    "archives_related_users",
    "archives_fans_list",
    "archives_follow_list",
    "archives_user_report_search",
    "archives_negative_report",
    "archives_review_logs",
    "archives_punish_status",
    "weapon_device_app_list",
    "track_analysis_summary",
    "track_analysis_check_data_ready",
}

RCP_FEATURE_TAB_ALIASES = {
    "orig": "原始类",
    "original": "原始类",
    "raw": "原始类",
    "base": "原始类",
    "原始": "原始类",
    "原始类": "原始类",
    "derive": "衍生类",
    "deriv": "衍生类",
    "deriveclass": "衍生类",
    "derivedclass": "衍生类",
    "derived": "衍生类",
    "衍生": "衍生类",
    "衍生类": "衍生类",
    "counter": "聚合类",
    "count": "聚合类",
    "aggregate": "聚合类",
    "agg": "聚合类",
    "聚合": "聚合类",
    "聚合类": "聚合类",
    "dataserv": "服务类",
    "dataservice": "服务类",
    "data_service": "服务类",
    "service": "服务类",
    "服务": "服务类",
    "服务类": "服务类",
    "namelist": "名单类",
    "list": "名单类",
    "名单": "名单类",
    "名单类": "名单类",
    "sys": "系统类",
    "systemclass": "系统类",
    "system": "系统类",
    "系统": "系统类",
    "系统类": "系统类",
    "other": "未知",
    "uncreated": "未创建类",
    "未创建": "未创建类",
    "未创建类": "未创建类",
}

RCP_HIGH_VALUE_FEATURE_KEY_FRAGMENTS = {
    "device", "did", "android", "ios", "weapon", "wpn", "boot", "fingerprint",
    "root", "hook", "script", "groupcontrol", "virtual", "proxy", "vpn",
    "sim", "lock", "reset", "model", "osver", "ua", "client", "channel",
    "locale", "city", "ip", "network", "action", "task", "reward", "entry",
    "scene", "request", "startup", "start", "click", "register", "fakeaccount",
    "risk", "policy", "event",
}


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
    if normalized in STRICT_PII_EXACT_KEYS:
        return True
    return any(fragment in normalized for fragment in ("idcard", "identitynumber", "realname", "detailaddress", "detailedaddress"))


def _is_nonessential_url_key(key: str) -> bool:
    return _normalized_key(key) in NONESSENTIAL_URL_KEYS


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
    if len(text) > EMBEDDED_JSON_PARSE_MAX_CHARS:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def _expand_embedded_json_strings(value: Any, *, action: str, depth: int = 0) -> tuple[Any, dict[str, Any]]:
    """Expand visible JSON strings before safe handle extraction.

    Some passthrough sources expose business data as a JSON string inside an
    otherwise visible body, for example Archives PhotoMeta. Dennis owns this
    parsing step; the service remains a raw/capped passthrough and raw strings
    are not returned in the final answer.
    """

    meta = {
        "embedded_json_expanded": False,
        "embedded_json_expanded_count": 0,
        "embedded_json_parse_errors": [],
        "embedded_json_parse_policy": "dennis_side_safe_visible_body_parse",
    }
    if depth > 8:
        return value, meta

    def merge(child_meta: dict[str, Any]) -> None:
        if child_meta.get("embedded_json_expanded"):
            meta["embedded_json_expanded"] = True
        meta["embedded_json_expanded_count"] += int(child_meta.get("embedded_json_expanded_count") or 0)
        meta["embedded_json_parse_errors"].extend(child_meta.get("embedded_json_parse_errors", []))

    if isinstance(value, dict):
        expanded: dict[str, Any] = {}
        for key, child in value.items():
            normalized = _normalized_key(str(key))
            if _is_credential_secret_key(str(key)) or _is_strict_pii_key(str(key)):
                expanded[key] = child
                continue
            if isinstance(child, str) and normalized not in EMBEDDED_JSON_SKIP_KEYS:
                parsed = _parse_nested_json(child)
                if parsed is not None:
                    expanded_child, child_meta = _expand_embedded_json_strings(parsed, action=action, depth=depth + 1)
                    merge(child_meta)
                    meta["embedded_json_expanded"] = True
                    meta["embedded_json_expanded_count"] += 1
                    expanded[key] = expanded_child
                    continue
                if child.strip()[:1] in "[{":
                    meta["embedded_json_parse_errors"].append(str(key))
            if isinstance(child, (dict, list)):
                expanded_child, child_meta = _expand_embedded_json_strings(child, action=action, depth=depth + 1)
                merge(child_meta)
                expanded[key] = expanded_child
            else:
                expanded[key] = child
        return expanded, meta
    if isinstance(value, list):
        expanded_list: list[Any] = []
        max_items = MAX_RCP_EVENT_FEATURE_ROWS if action == "rcp_event_feature_list" else MAX_PROJECTED_ARRAY_ITEMS
        for child in value[:max_items]:
            expanded_child, child_meta = _expand_embedded_json_strings(child, action=action, depth=depth + 1)
            merge(child_meta)
            expanded_list.append(expanded_child)
        return expanded_list, meta
    return value, meta


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
        # bounded rendering stats (display layer only)
        "bounded_rendering": True,
        "projection_depth_limit_hit": False,
        "projection_key_limit_hit": False,
        "projection_array_omitted": 0,
        # timing (filled in by _project_evidence_body wrapper)
        "projection_elapsed_ms": 0.0,
        "projection_slow": False,
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


def _normalize_rcp_feature_tab(raw_tab: Any) -> str:
    text = str(raw_tab or "").strip()
    if not text:
        return "未知"
    normalized = _normalized_key(text)
    if text in RCP_FEATURE_TAB_ALIASES:
        return RCP_FEATURE_TAB_ALIASES[text]
    if normalized in RCP_FEATURE_TAB_ALIASES:
        return RCP_FEATURE_TAB_ALIASES[normalized]
    for alias, tab in RCP_FEATURE_TAB_ALIASES.items():
        alias_norm = _normalized_key(alias)
        if alias and (alias in text or alias_norm and alias_norm in normalized):
            return tab
    return text


def _rcp_feature_row_lists(value: Any, *, depth: int = 0) -> list[tuple[str, list[dict[str, Any]]]]:
    if depth > 6:
        return []
    if isinstance(value, list):
        if all(isinstance(item, dict) for item in value) and any(
            "featureKey" in item or "feature_key" in item or "featureName" in item
            for item in value
        ):
            return [("$", [item for item in value if isinstance(item, dict)])]
        results: list[tuple[str, list[dict[str, Any]]]] = []
        for index, item in enumerate(value[:MAX_RCP_EVENT_FEATURE_ROWS]):
            for path, rows in _rcp_feature_row_lists(item, depth=depth + 1):
                results.append((f"$[{index}]{path[1:]}", rows))
        return results
    if isinstance(value, dict):
        results: list[tuple[str, list[dict[str, Any]]]] = []
        for key, child in value.items():
            if isinstance(child, list) and all(isinstance(item, dict) for item in child) and any(
                "featureKey" in item or "feature_key" in item or "featureName" in item
                for item in child
            ):
                results.append((f"$.{key}", [item for item in child if isinstance(item, dict)]))
                continue
            if isinstance(child, (dict, list)):
                for path, rows in _rcp_feature_row_lists(child, depth=depth + 1):
                    suffix = path[1:] if path.startswith("$") else path
                    results.append((f"$.{key}{suffix}", rows))
        return results
    return []


def _rcp_feature_domain_and_family(feature_key: str, feature_name: str) -> tuple[str, str]:
    normalized = _normalized_key(f"{feature_key}_{feature_name}")
    if any(fragment in normalized for fragment in ("userid", "account", "registeruser", "usersex")):
        return "账号", "account_or_register_profile"
    if any(fragment in normalized for fragment in ("device", "did", "android", "ios", "weapon", "wpn", "boot", "fingerprint", "root", "hook", "sim", "lock", "reset", "model", "osver", "cloudphone", "virtualmachine")):
        return "设备", "device_fingerprint_or_environment"
    if any(fragment in normalized for fragment in ("ip", "city", "province", "locale", "network", "ua", "channel")):
        return "网络", "network_geo_or_client_channel"
    if any(fragment in normalized for fragment in ("item", "photo", "content", "live", "publish")):
        return "内容", "content_or_publish_object"
    if any(fragment in normalized for fragment in ("comment", "message", "follow", "fan", "like", "collect", "relation")):
        return "社交", "social_interaction"
    if any(fragment in normalized for fragment in ("action", "click", "task", "reward", "startup", "start", "clientevent", "lagtime", "register")):
        return "行为", "behavior_sequence_or_timing"
    if any(fragment in normalized for fragment in ("policy", "risk", "score", "decision", "event")):
        return "策略", "strategy_signal_or_risk_feature"
    if any(fragment in normalized for fragment in ("appeal", "report", "complaint", "review")):
        return "反馈", "feedback_signal"
    if any(fragment in normalized for fragment in ("punish", "ban", "block", "enforce", "unban")):
        return "处置", "enforcement_signal"
    return "未知", "unknown_feature_family"


def _rcp_feature_high_value_reason(feature_key: str, feature_name: str, feature_tab: str) -> str | None:
    if feature_tab == "原始类":
        return "original_tab_full_retention"
    normalized = _normalized_key(f"{feature_key}_{feature_name}")
    if any(fragment in normalized for fragment in RCP_HIGH_VALUE_FEATURE_KEY_FRAGMENTS):
        return "risk_relevant_feature_family"
    return None


def _rcp_feature_value_projection(feature_key: str, feature_name: str, value: Any, data_type: Any) -> dict[str, Any]:
    value_present = value not in (None, "", [], {})
    if not value_present:
        return {
            "feature_value_or_safe_ref": None,
            "value_present": False,
            "value_comparable": False,
            "comparable_type": "不可比较",
            "sensitive_value_policy": "只保留是否存在",
            "missing_reason": "empty_or_null_feature_value",
        }

    sensitive_key = _is_credential_secret_key(feature_key) or _is_credential_secret_key(feature_name)
    strict_pii_key = _is_strict_pii_key(feature_key) or _is_strict_pii_key(feature_name)
    sensitive_value = _looks_sensitive_scalar(value)
    if isinstance(value, dict) and (
        value.get("__strict_pii_redacted__")
        or value.get("__sensitive_control_chain_field_present__")
        or value.get("__large_string_projected__")
    ):
        return {
            "feature_value_or_safe_ref": value.get("value_hash") or _safe_value_hash(value),
            "value_present": True,
            "value_comparable": False,
            "comparable_type": "不可比较",
            "sensitive_value_policy": "只保留安全引用",
            "missing_reason": None,
        }
    if sensitive_key or strict_pii_key or sensitive_value:
        return {
            "feature_value_or_safe_ref": _safe_value_hash(value),
            "value_present": True,
            "value_comparable": False,
            "comparable_type": "不可比较",
            "sensitive_value_policy": "只保留安全引用",
            "missing_reason": None,
        }
    if isinstance(value, bool):
        comparable_type = "等值"
    elif isinstance(value, (int, float)):
        comparable_type = "数值分桶"
    elif isinstance(value, (list, dict)):
        return {
            "feature_value_or_safe_ref": _safe_value_hash(value),
            "value_present": True,
            "value_comparable": True,
            "comparable_type": "集合相似",
            "sensitive_value_policy": "只保留安全引用",
            "missing_reason": None,
        }
    else:
        comparable_type = "等值" if str(data_type or "").lower() in {"string", "str", "bool", "boolean"} else "文本相似"
    return {
        "feature_value_or_safe_ref": value,
        "value_present": True,
        "value_comparable": True,
        "comparable_type": comparable_type,
        "sensitive_value_policy": "原值可用",
        "missing_reason": None,
    }


def _extract_rcp_strategy_event_feature_rows(
    action: str,
    parsed_values: list[tuple[str, Any]],
    *,
    source_id: str,
) -> list[dict[str, Any]]:
    if action != "rcp_event_feature_list":
        return []
    rows: list[dict[str, Any]] = []
    seen_rows: set[tuple[str, str, str, str]] = set()
    for body_path, parsed in parsed_values:
        for list_path, feature_rows in _rcp_feature_row_lists(parsed):
            for index, feature in enumerate(feature_rows[:MAX_RCP_EVENT_FEATURE_ROWS], start=1):
                feature_key = str(feature.get("featureKey") or feature.get("feature_key") or "").strip()
                feature_name = str(feature.get("featureName") or feature.get("feature_name") or feature_key).strip()
                if not feature_key and not feature_name:
                    continue
                feature_tab = _normalize_rcp_feature_tab(
                    feature.get("featureTab")
                    or feature.get("feature_tab")
                    or feature.get("featureGroup")
                    or feature.get("feature_group")
                )
                high_value_reason = _rcp_feature_high_value_reason(feature_key, feature_name, feature_tab)
                if feature_tab != "原始类" and not high_value_reason:
                    continue
                raw_value = (
                    feature.get("defaultFeatureValue")
                    if "defaultFeatureValue" in feature
                    else feature.get("featureValue")
                    if "featureValue" in feature
                    else feature.get("featureOrigValue")
                    if "featureOrigValue" in feature
                    else feature.get("value")
                )
                row_identity = (
                    feature_tab,
                    feature_key or feature_name,
                    feature_name or feature_key,
                    _safe_value_hash(raw_value),
                )
                if row_identity in seen_rows:
                    continue
                seen_rows.add(row_identity)
                feature_type = feature.get("dataType") or feature.get("featureType")
                projection = _rcp_feature_value_projection(feature_key, feature_name, raw_value, feature_type)
                mapped_domain, mapped_family = _rcp_feature_domain_and_family(feature_key, feature_name)
                rows.append(
                    {
                        "source_id": source_id,
                        "source_name": "rcp_event_feature_list",
                        "feature_row_index": len(rows) + 1,
                        "source_field_path": f"{body_path}{list_path}[{index - 1}]",
                        "feature_tab": feature_tab,
                        "feature_key": feature_key or feature_name,
                        "feature_name": feature_name or feature_key,
                        "feature_type": feature_type or type(raw_value).__name__,
                        **projection,
                        "source_quality": None,
                        "evidence_source": "current_observation",
                        "candidate_feature_eligible": bool(projection.get("value_comparable") and high_value_reason),
                        "high_value_reason": high_value_reason,
                        "mapped_domain": mapped_domain,
                        "mapped_field_family": mapped_family,
                        "original_feature_row_retained": feature_tab == "原始类",
                    }
                )
    return rows


def _project_evidence_body(action: str, parsed: Any, *, body_path: str) -> tuple[Any, dict[str, Any]]:
    """Project large passthrough bodies before observation extraction.

    This is intentionally not a service normalizer and not a conclusion layer.
    It only removes obvious non-evidence bulk while retaining risk anchors and
    sensitive control-chain field presence as safe handles.
    """

    meta = _projection_meta()

    # Observation-layer array cap: use per-source cap if available, else default.
    # NOTE: this cap is for safe_observation display ONLY.
    # _extract_rcp_strategy_event_feature_rows and _extract_device_detail_rows
    # operate on prepared_values (pre-projection) and are NOT affected.
    _obs_array_cap = PROJECTION_OBS_ARRAY_CAP_BY_SOURCE.get(action, PROJECTION_OBS_ARRAY_ITEMS)

    def project(item: Any, path: str, depth: int = 0) -> Any:
        # ── Depth limit ──────────────────────────────────────────────────────
        # Stop deep-recursing past PROJECTION_MAX_DEPTH.
        # Anchors (credential / PII / canonical) are already handled before
        # the recursive call, so they are never truncated by depth.
        if depth > PROJECTION_MAX_DEPTH:
            meta["projection_depth_limit_hit"] = True
            meta["dropped_fields_count"] += 1
            if isinstance(item, dict):
                return {
                    "__depth_limit_truncated__": True,
                    "depth": depth,
                    "key_count": len(item),
                }
            if isinstance(item, list):
                return {
                    "__depth_limit_truncated__": True,
                    "depth": depth,
                    "item_count": len(item),
                }
            return item  # scalar at deep depth: keep as-is

        if isinstance(item, dict):
            projected: dict[str, Any] = {}
            omitted_keys: list[str] = []

            # Split keys into anchor-priority and regular buckets so that
            # anchor keys are never evicted by PROJECTION_MAX_OBJ_KEYS.
            anchor_items: list[tuple[str, Any]] = []
            regular_items: list[tuple[str, Any]] = []
            for key, child in item.items():
                canonical = _canonical_for_key(str(key))
                if (
                    _is_credential_secret_key(str(key))
                    or _is_strict_pii_key(str(key))
                    or (canonical and canonical in RISK_ENTITY_CANONICAL_FIELDS
                        and isinstance(child, (str, int, float, bool)))
                    or str(key) in PROJECTION_ALWAYS_KEEP_KEYS
                ):
                    anchor_items.append((key, child))
                else:
                    regular_items.append((key, child))

            # Always keep all anchor items; cap regular items.
            max_regular = max(0, PROJECTION_MAX_OBJ_KEYS - len(anchor_items))
            if len(regular_items) > max_regular:
                omitted = regular_items[max_regular:]
                regular_items = regular_items[:max_regular]
                omitted_keys = [k for k, _ in omitted]
                meta["projection_key_limit_hit"] = True
                meta["dropped_fields_count"] += len(omitted_keys)

            for key, child in anchor_items + regular_items:
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

            if omitted_keys:
                projected["__omitted_keys__"] = {
                    "omitted_key_count": len(omitted_keys),
                    "omitted_key_sample": omitted_keys[:10],
                    "projection_key_limit": PROJECTION_MAX_OBJ_KEYS,
                }
            return projected

        if isinstance(item, list):
            projected_list = []
            # Use observation-layer cap (NOT MAX_RCP_EVENT_FEATURE_ROWS).
            # L3 fact tables (_extract_rcp_strategy_event_feature_rows) run on
            # prepared_values before this projection, so they see the full list.
            obs_cap = _obs_array_cap
            total_items = len(item)
            capped_items = item[:obs_cap]
            omitted_count = max(0, total_items - obs_cap)
            for index, child in enumerate(capped_items):
                child_path = f"{path}[{index}]"
                projected_child = project(child, child_path, depth + 1)
                if projected_child in (None, "", [], {}):
                    meta["dropped_fields_count"] += 1
                    continue
                projected_list.append(projected_child)
            if omitted_count > 0:
                meta["projection_array_omitted"] += omitted_count
                projected_list.append({
                    "__array_truncated__": True,
                    "observed_count": total_items,
                    "projected_count": len(projected_list),
                    "omitted_count": omitted_count,
                    "projection_array_cap": obs_cap,
                })
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

    _t_start = time.monotonic()
    try:
        projected = project(parsed, body_path)
        if projected is not parsed:
            meta["projection_applied"] = True
        if meta["projected_records"] == 0 and isinstance(projected, dict):
            records = _value_at_path(projected, LOGIN_LOGS_ARRAY_CAP_PATH)
            if isinstance(records, list):
                meta["projected_records"] = len(records)
        elapsed_ms = (time.monotonic() - _t_start) * 1000
        meta["projection_elapsed_ms"] = round(elapsed_ms, 2)
        meta["projection_slow"] = elapsed_ms > PROJECTION_SLOW_THRESHOLD_MS
        return projected, meta
    except Exception as exc:  # defensive: projection must never block parsing
        elapsed_ms = (time.monotonic() - _t_start) * 1000
        meta["projection_elapsed_ms"] = round(elapsed_ms, 2)
        meta["projection_slow"] = elapsed_ms > PROJECTION_SLOW_THRESHOLD_MS
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
    # aggregate bounded rendering stats
    aggregate["projection_depth_limit_hit"] = any(bool(item.get("projection_depth_limit_hit")) for item in items)
    aggregate["projection_key_limit_hit"] = any(bool(item.get("projection_key_limit_hit")) for item in items)
    aggregate["projection_array_omitted"] = sum(int(item.get("projection_array_omitted") or 0) for item in items)
    aggregate["projection_elapsed_ms"] = round(sum(float(item.get("projection_elapsed_ms") or 0) for item in items), 2)
    aggregate["projection_slow"] = any(bool(item.get("projection_slow")) for item in items)
    return aggregate


def _prepare_body_for_action(action: str, parsed: Any) -> tuple[Any, dict[str, Any]]:
    expanded, embedded_meta = _expand_embedded_json_strings(parsed, action=action)
    if action != "login_logs_search" or not isinstance(expanded, dict):
        return expanded, embedded_meta
    candidate_paths = (LOGIN_LOGS_ARRAY_CAP_PATH, ("logSearchModels",))
    if not any(isinstance(_value_at_path(expanded, path), list) for path in candidate_paths):
        return expanded, embedded_meta
    cloned = _clone_json(expanded)
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
    return cloned, embedded_meta


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


@lru_cache(maxsize=2048)
def _canonical_for_key(key: str) -> str | None:
    """Hot-path alias scan, cached (LRU 2048).

    Called per field key at every projection depth; caching eliminates
    the O(n x m) alias re-scan for repeated keys such as device_id /
    event_id / policy_code across large RCP / device bodies.
    """
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
    action: str = "",
    retain_unknown_scalars: bool = False,
) -> tuple[list[dict[str, Any]], list[str]]:
    handles: list[dict[str, Any]] = []
    flags: list[str] = []

    def record_index_from_path(current_path: str) -> int | None:
        match = re.search(r"\[(\d+)\]", current_path)
        if not match:
            return None
        try:
            return int(match.group(1))
        except ValueError:
            return None

    def can_keep_unknown_scalar(key: str, child: Any) -> bool:
        if not retain_unknown_scalars:
            return False
        if _is_credential_secret_key(key) or _is_strict_pii_key(key):
            return False
        if isinstance(child, (dict, list)):
            if isinstance(child, list) and child and not any(isinstance(item, (dict, list)) for item in child[:20]):
                return True
            return False
        if child in (None, ""):
            return False
        if isinstance(child, str) and _looks_sensitive_scalar(child):
            return False
        return isinstance(child, (str, int, float, bool))

    def walk(item: Any, current_path: str) -> None:
        if len(handles) >= limit:
            return
        if isinstance(item, dict):
            for key, child in item.items():
                child_path = f"{current_path}.{key}"
                canonical = _canonical_for_key(key)
                if key.lower() in BODY_CANDIDATE_KEYS:
                    continue
                if _is_nonessential_url_key(key):
                    flags.append("nonessential_url_filtered")
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
                            "record_index": record_index_from_path(child_path),
                        }
                    )
                    if len(handles) >= limit:
                        return
                elif can_keep_unknown_scalar(str(key), child):
                    handles.append(
                        {
                            "field": key,
                            "field_path": child_path,
                            "source_id": source_id,
                            "value": child,
                            "record_index": record_index_from_path(child_path),
                            "unknown_field_retained": True,
                            "retention_reason": f"{action or 'source'}_raw_detail_unknown_scalar",
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
            if field == "targetid":
                clone = dict(handle)
                clone["canonical_field"] = "photo_id"
                clone["contextual_alias"] = "photo_targetid_as_photo_id"
                contextual.append(clone)
            if field in {"timemillis", "createtime"}:
                clone = dict(handle)
                clone["canonical_field"] = "publish_time"
                clone["contextual_alias"] = "photo_time_field_as_publish_time"
                contextual.append(clone)
            if field == "photoreviewstatus":
                clone = dict(handle)
                clone["canonical_field"] = "content_status"
                clone["contextual_alias"] = "photo_review_status_as_content_status"
                contextual.append(clone)
            if field == "reviewinfo":
                clone = dict(handle)
                clone["canonical_field"] = "audit_or_strategy_reason"
                clone["contextual_alias"] = "review_info_as_audit_reason"
                contextual.append(clone)
        elif action == "archives_user_analysis":
            if canonical in {"device_id", "candidate_device_id"} and field in {"deviceid", "did"}:
                clone = dict(handle)
                clone["canonical_field"] = "operation_device"
                clone["contextual_alias"] = "user_analysis_deviceid_as_operation_device"
                contextual.append(clone)
        elif action == "archives_comment_search":
            if field in {"commenttime", "createtime", "time"}:
                clone = dict(handle)
                clone["canonical_field"] = "action_time"
                clone["contextual_alias"] = "comment_time_as_action_time"
                contextual.append(clone)
        elif action == "archives_private_message_search":
            if field == "time":
                clone = dict(handle)
                clone["canonical_field"] = "action_time"
                clone["contextual_alias"] = "message_time_as_action_time"
                contextual.append(clone)
            if field in {"fromuserid", "touserid"}:
                clone = dict(handle)
                clone["canonical_field"] = "target_user_id"
                clone["contextual_alias"] = "message_peer_as_target_user_id"
                contextual.append(clone)
            if field == "content":
                clone = dict(handle)
                clone["canonical_field"] = "message_text"
                clone["contextual_alias"] = "message_content_as_message_text"
                contextual.append(clone)
        elif action in {"archives_user_report_search", "archives_negative_report"}:
            if field in {"createtime", "time"}:
                clone = dict(handle)
                clone["canonical_field"] = "report_time"
                clone["contextual_alias"] = "report_time_alias"
                contextual.append(clone)
            if field == "targetid":
                clone = dict(handle)
                clone["canonical_field"] = "feedback_object"
                clone["contextual_alias"] = "report_targetid_as_feedback_object"
                contextual.append(clone)
        elif action == "archives_review_logs":
            if field == "createtime":
                for canonical_field, alias in (
                    ("review_time", "review_log_create_time_as_review_time"),
                    ("enforcement_time", "review_log_create_time_as_enforcement_time"),
                ):
                    clone = dict(handle)
                    clone["canonical_field"] = canonical_field
                    clone["contextual_alias"] = alias
                    contextual.append(clone)
            if field == "desc":
                clone = dict(handle)
                clone["canonical_field"] = "policy_reason"
                clone["contextual_alias"] = "review_log_desc_as_policy_reason"
                contextual.append(clone)
        elif action == "archives_punish_status":
            if field in {"punishreason", "markcodenameb"}:
                clone = dict(handle)
                clone["canonical_field"] = "policy_reason"
                clone["contextual_alias"] = "punish_reason_alias"
                contextual.append(clone)
            if field == "punishid":
                clone = dict(handle)
                clone["canonical_field"] = "punish_id"
                clone["contextual_alias"] = "punish_id_alias"
                contextual.append(clone)
            if field in {"punishcode", "punishcodenameb", "eventtype"}:
                clone = dict(handle)
                clone["canonical_field"] = "punish_type"
                clone["contextual_alias"] = "punish_type_alias"
                contextual.append(clone)
    return handles + contextual


def _device_comparable_type(value: Any) -> str:
    if isinstance(value, bool):
        return "布尔"
    if isinstance(value, (int, float)):
        return "数值分桶"
    if isinstance(value, list):
        return "集合相似"
    if isinstance(value, dict):
        return "集合相似"
    return "等值"


def _device_source_type_for_key(field_key: str) -> str:
    if field_key in {"phone_model", "os_version", "app_version", "device_platform"}:
        return "设备基础信息"
    if field_key in {"launch_count", "boot_duration", "first_seen_time", "active_days", "device_age_days"}:
        return "设备使用画像"
    if field_key in {"lock_screen_enabled", "sim_present", "charging_pattern"}:
        return "设备使用画像"
    if field_key in {"automation_service_detected", "script_risk"}:
        return "设备风险标签"
    if field_key in {"device_reset_signal", "root_or_hook_signal", "root_signal", "hook_signal", "frida_signal", "emulator_signal"}:
        return "设备风险标签"
    if field_key in {"installed_app_list", "installed_app_cluster", "risk_app", "tool_app"}:
        return "安装列表 / 应用环境"
    if field_key in {"account_device_count", "device_account_count"}:
        return "账号-设备关系"
    return "未知"


def _safe_device_field_value(value: Any) -> tuple[Any, str, bool]:
    if isinstance(value, dict):
        safe_dict: dict[str, Any] = {}
        for key, child in value.items():
            if _is_credential_secret_key(str(key)):
                continue
            child_value, _policy, present = _safe_device_field_value(child)
            if present:
                safe_dict[str(key)] = child_value
            if len(safe_dict) >= 200:
                break
        return safe_dict, "原值可用", bool(safe_dict)
    if isinstance(value, list):
        safe_list: list[Any] = []
        for child in value[:200]:
            child_value, _policy, present = _safe_device_field_value(child)
            if present:
                safe_list.append(child_value)
        return safe_list, "原值可用", bool(safe_list)
    if value is None or value == "":
        return None, "原值可用", False
    if _looks_sensitive_scalar(value):
        return {"__strict_pii_redacted__": True, "value_hash": _safe_value_hash(value)}, "只保留安全引用", True
    return value, "原值可用", True


def _parse_device_embedded_scalar(value: Any) -> Any:
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text or len(text) > 5000:
        return None
    parsed_json = _parse_nested_json(text)
    if parsed_json is not None:
        return parsed_json
    if not (text.startswith("{") and text.endswith("}") and "=" in text):
        return None
    inner = text[1:-1].strip()
    if not inner:
        return None
    result: dict[str, Any] = {}
    for part in re.split(r"[;,]\s*", inner):
        if "=" not in part:
            continue
        key, raw_value = part.split("=", 1)
        key = key.strip().strip('"').strip("'")
        raw_value = raw_value.strip().strip('"').strip("'")
        if not key or _is_credential_secret_key(key):
            continue
        if re.fullmatch(r"-?\d+", raw_value):
            value_out: Any = int(raw_value)
        elif re.fullmatch(r"-?\d+\.\d+", raw_value):
            value_out = float(raw_value)
        else:
            value_out = raw_value
        result[key] = value_out
        if len(result) >= 100:
            break
    return result or None


WEAPON_DEVICE_DETAIL_ACTIONS = {
    "weapon_inventory",
    "weapon_device_info",
    "weapon_device_app_list",
    "weapon_device_location_info",
    "weapon_user_klink_status",
}


def _extract_device_detail_rows(
    action: str,
    parsed_values: list[tuple[str, Any]],
    *,
    source_id: str,
) -> list[dict[str, Any]]:
    if action not in WEAPON_DEVICE_DETAIL_ACTIONS:
        return []
    rows: list[dict[str, Any]] = []
    row_cap = 5000

    def nearest_device_id(item: dict[str, Any]) -> Any:
        for key, child in item.items():
            canonical = _canonical_for_key(str(key))
            if canonical in {"device_id", "candidate_device_id"} and isinstance(child, (str, int, float)):
                return child
        return None

    def device_field_key_for(raw_key: str) -> tuple[str, str | None]:
        canonical = _canonical_for_key(raw_key)
        if canonical:
            return canonical, canonical
        normalized = _normalized_key(raw_key)
        return (normalized or raw_key.strip() or "unknown_device_field"), None

    def should_emit_value(value: Any) -> bool:
        if value is None or value == "":
            return False
        if isinstance(value, dict):
            return False
        if isinstance(value, list):
            return not any(isinstance(child, dict) for child in value)
        return isinstance(value, (str, int, float, bool, list))

    def walk(item: Any, path: str, device_context: Any = None) -> None:
        if len(rows) >= row_cap:
            return
        if isinstance(item, dict):
            current_device = nearest_device_id(item) or device_context
            for key, child in item.items():
                if _is_credential_secret_key(str(key)):
                    continue
                if _normalized_key(str(key)) in DEVICE_DETAIL_NON_DEVICE_SUBTREE_KEYS:
                    continue
                child_path = f"{path}.{key}"
                field_key, canonical = device_field_key_for(str(key))
                if should_emit_value(child):
                    safe_value, sensitive_policy, value_present = _safe_device_field_value(child)
                    if value_present:
                        rows.append(
                            {
                                "source_id": source_id,
                                "source_name": action,
                                "action": action,
                                "device_id": str(current_device) if current_device else None,
                                "device_safe_ref": str(current_device) if current_device else None,
                                "device_source_type": _device_source_type_for_key(canonical or field_key),
                                "device_field_key": field_key,
                                "device_field_name": str(key),
                                "device_field_value_or_safe_ref": safe_value,
                                "device_field_type": type(child).__name__,
                                "value_present": value_present,
                                "value_comparable": value_present and sensitive_policy != "只保留安全引用",
                                "comparable_type": _device_comparable_type(safe_value),
                                "source_quality": None,
                                "evidence_source": "current_observation",
                                "sensitive_value_policy": sensitive_policy,
                                "field_path": child_path,
                                "candidate_feature_eligible": field_key not in {"device_id", "candidate_device_id"},
                                "known_device_field": canonical in DEVICE_DETAIL_CANONICAL_FIELDS,
                                "unknown_device_field_retained": canonical is None,
                                "raw_device_field_retention_policy": "retain_non_secret_weapon_leaf_fields",
                            }
                        )
                    embedded_device_value = _parse_device_embedded_scalar(child)
                    if embedded_device_value is not None:
                        walk(embedded_device_value, f"{child_path}.__parsed_scalar", current_device)
                if isinstance(child, (dict, list)):
                    walk(child, child_path, current_device)
        elif isinstance(item, list):
            for index, child in enumerate(item[:200]):
                walk(child, f"{path}[{index}]", device_context)
                if len(rows) >= row_cap:
                    return

    for body_path, parsed in parsed_values:
        walk(parsed, body_path)

    deduped: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, str]] = set()
    for row in rows:
        key = (
            str(row.get("device_id") or ""),
            str(row.get("device_field_key") or ""),
            str(row.get("field_path") or ""),
            _safe_value_hash(row.get("device_field_value_or_safe_ref")),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    return deduped


def _expected_fields_for_action(action: str, expected_business_fields: list[str] | None) -> list[str]:
    if expected_business_fields:
        return list(expected_business_fields)
    return list(SOURCE_EXPECTED_BUSINESS_FIELDS.get(action, []))


def _build_projection_timing(
    *,
    action: str,
    source_id: str,
    projection_metadata: list[dict[str, Any]],
    t_obs_start: float,
) -> dict[str, Any]:
    """Aggregate per-source projection timing for observation artifact."""
    observation_build_ms = round((time.monotonic() - t_obs_start) * 1000, 2)
    per_source_ms = [
        round(float(m.get("projection_elapsed_ms") or 0), 2)
        for m in projection_metadata
    ]
    total_projection_ms = round(sum(per_source_ms), 2)
    slow_sources: list[str] = []
    budget_hit_sources: list[str] = []
    for m in projection_metadata:
        elapsed = float(m.get("projection_elapsed_ms") or 0)
        if elapsed > PROJECTION_SLOW_THRESHOLD_MS:
            slow_sources.append(action)
        if elapsed > PROJECTION_VERY_SLOW_THRESHOLD_MS:
            budget_hit_sources.append(action)
    projection_slow = bool(slow_sources)
    return {
        "observation_build_ms": observation_build_ms,
        "total_projection_ms": total_projection_ms,
        "per_source_projection_ms": per_source_ms,
        "slow_projection_sources": _unique(slow_sources),
        "projection_budget_hit_sources": _unique(budget_hit_sources),
        "projection_slow": projection_slow,
        "source_id": source_id,
        "action": action,
    }


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
    prepared_values: list[tuple[str, Any]] = []
    projection_metadata: list[dict[str, Any]] = []
    embedded_json_metadata: list[dict[str, Any]] = []
    flags: list[str] = []
    row_cap_metadata = _row_cap_metadata(source_payload, transport_row)
    _t_obs_start = time.monotonic()

    for body_path, body_value in body_candidates:
        parsed, parse_status = _parse_body_value(body_value)
        body_parse_statuses.append(f"{body_path}:{parse_status}")
        if parsed is None:
            if parse_status.endswith("parse_error"):
                flags.append("passthrough_interpretation_gap")
            continue
        prepared, embedded_meta = _prepare_body_for_action(action, parsed)
        embedded_json_metadata.append(embedded_meta)
        prepared_values.append((body_path, prepared))
        projected, projection_meta = _project_evidence_body(action, prepared, body_path=body_path)
        projection_metadata.append(projection_meta)
        parsed_values.append((body_path, projected))

    direct_handles, direct_flags = _extract_handles(
        source_payload,
        source_id=source_id,
        path="$passthrough",
        action=action,
    )
    flags.extend(direct_flags)
    body_handles: list[dict[str, Any]] = []
    retain_unknown_scalars = action in RAW_DETAIL_UNKNOWN_RETENTION_ACTIONS
    body_handle_limit = 1200 if retain_unknown_scalars else 160
    for body_path, prepared in prepared_values:
        handles, body_flags = _extract_handles(
            prepared,
            source_id=source_id,
            path=body_path,
            limit=body_handle_limit,
            action=action,
            retain_unknown_scalars=retain_unknown_scalars,
        )
        body_handles.extend(handles)
        flags.extend(body_flags)

    parsed_body_handles = _dedupe_handles(_source_contextual_handles(action, body_handles))
    all_handles = _dedupe_handles(direct_handles + parsed_body_handles)
    strategy_event_feature_rows = _extract_rcp_strategy_event_feature_rows(
        action,
        prepared_values,
        source_id=source_id,
    )
    device_detail_rows = _extract_device_detail_rows(
        action,
        prepared_values if action in WEAPON_DEVICE_DETAIL_ACTIONS else parsed_values,
        source_id=source_id,
    )
    extracted_business_fields = _unique(
        [
            str(handle["canonical_field"])
            for handle in parsed_body_handles
            if str(handle.get("canonical_field")) in expected or not expected
        ]
        + [
            str(row.get("device_field_key"))
            for row in device_detail_rows
            if str(row.get("device_field_key") or "")
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
    if any(item.get("embedded_json_expanded") for item in embedded_json_metadata):
        flags.append("embedded_json_string_expanded")
    if strategy_event_feature_rows:
        flags.extend([
            "strategy_event_feature_rows_extracted",
            "rcp_event_feature_list_row_level_retention_applied",
        ])
    if device_detail_rows:
        flags.extend([
            "device_detail_rows_extracted",
            "weapon_device_detail_row_level_retention_applied",
            "device_raw_field_values_retained_except_credentials",
        ])
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
        "parser_input_available": bool(prepared_values),
        "fact_extraction_input_policy": "pre_projection_prepared_body_credentials_filtered",
        "display_projection_boundary": "projection_applies_to_user_visible_summary_not_fact_tables",
        "body_parse_statuses": body_parse_statuses,
        "direct_safe_handles": direct_handles,
        "parsed_body_safe_handles": parsed_body_handles,
        "extracted_safe_handles": all_handles,
        "strategy_event_feature_rows": strategy_event_feature_rows,
        "device_detail_rows": device_detail_rows,
        "extracted_business_fields": extracted_business_fields,
        "missing_business_fields": missing_business_fields,
        "candidate_device_ids": _dedupe_device_candidates(candidate_device_ids),
        "passthrough_row_cap": row_cap_metadata,
        "evidence_projection": _aggregate_projection_metadata(projection_metadata),
        "embedded_json_parse": {
            "embedded_json_expanded": any(bool(item.get("embedded_json_expanded")) for item in embedded_json_metadata),
            "embedded_json_expanded_count": sum(
                int(item.get("embedded_json_expanded_count") or 0) for item in embedded_json_metadata
            ),
            "embedded_json_parse_errors": _unique(
                [
                    str(error)
                    for item in embedded_json_metadata
                    for error in item.get("embedded_json_parse_errors", [])
                    if error
                ]
            ),
            "embedded_json_parse_policy": "dennis_side_safe_visible_body_parse",
        },
        "interpretation_flags": _unique(flags),
        "source_quality_hint": _source_quality_hint(flags, missing_business_fields),
        "evidence_chain_tags": _evidence_chain_tags(action, extracted_business_fields),
        "projection_timing": _build_projection_timing(
            action=action,
            source_id=source_id,
            projection_metadata=projection_metadata,
            t_obs_start=_t_obs_start,
        ),
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
