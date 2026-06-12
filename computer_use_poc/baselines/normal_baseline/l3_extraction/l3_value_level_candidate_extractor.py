#!/usr/bin/env python3
"""Build structured L3 value-level candidates from raw risk observations.

The extractor is intentionally local/offline. It never calls realtime
platforms or DataAgent/Hive. Its full mode consumes the
e2e_risk_observation_input_contract_v0_1 shape. When raw observations are
unavailable it can run partial mode over already-reviewed G-R9 oneRisk label
summary and field-level fallback candidates from existing L4 cards, with
need_raw_confirm marked explicitly.
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[4]
L3_DIR = Path(__file__).resolve().parent
if str(L3_DIR) not in sys.path:
    sys.path.insert(0, str(L3_DIR))
ALIGNMENT_DIR = ROOT / "computer_use_poc" / "baselines" / "normal_baseline" / "realtime_offline_field_alignment"
if str(ALIGNMENT_DIR) not in sys.path:
    sys.path.insert(0, str(ALIGNMENT_DIR))

from field_alignment_resolver import classify_field_role, resolve_field, resolve_source  # noqa: E402
from candidate_protocol import (  # noqa: E402
    apply_candidate_protocol,
    bucket_for_value,
    infer_value_type,
    is_numeric_bucketable,
)


HIGH_CARDINALITY_LEAVES = {
    "xm1", "xm3", "did", "device_id", "deviceId", "androidId", "android_id",
    "oaid", "imei", "idfa", "idfv", "uuid", "guid",
}

SENSITIVE_LEAVES = {
    "cookie", "cookies", "token", "tokens", "session", "sessions",
    "authorization", "password", "passwd", "credential", "credentials",
    "secret", "secrets", "sign", "sig", "sig3", "ssecurity",
    "riskControlToken", "risk_control_token", "authToken", "auth_token",
    "accessToken", "access_token", "refreshToken", "refresh_token",
    "loginToken", "login_token", "quickloginToken", "quickLoginToken",
    "accountToken", "identityToken", "captcha_token", "qrLoginToken",
    "bindToken", "resetToken", "openId", "open_id",
}

RESULT_SIGNAL_LEAVES = {
    "riskScore", "risk_score", "riskDecision", "risk_decision",
    "modelDecision", "model_decision", "policyHit", "policy_hit",
    "hitStrategy", "hit_strategy", "weaponRiskScore", "weapon_risk_score",
}

ACCESSIBILITY_FIELDS = {
    "accessibilitySvc",
    "accessibilityServiceList",
    "enabledAccessibilityServiceList",
}

CANDIDATE_GRAINS = {
    "field_presence",
    "scalar_value",
    "enum_value",
    "array_element",
    "label_value",
    "object_child_value",
    "value_pattern",
    "high_cardinality_anchor",
    "unsupported_complex_value",
}

REQUIRED_CANDIDATE_FIELDS = {
    "candidate_id",
    "source_name",
    "platform",
    "action_or_layer",
    "field_path",
    "field_value_or_pattern",
    "candidate_grain",
    "field_role_hint",
    "risk_observed_count",
    "risk_hit_count",
    "risk_hit_rate",
    "supporting_user_ids",
    "supporting_device_ids",
    "sample_values",
    "extraction_source",
    "extraction_confidence",
    "need_raw_confirm",
    "notes",
    "feature_type",
    "value_type",
    "feature_name",
    "source_fields",
    "source_events",
    "feature_definition",
    "bucket_label",
    "bucket_range",
    "candidate_value",
    "risk_denominator",
    "baseline_mode",
    "normal_hit_rate",
    "lift",
    "evidence_examples",
    "eval_required_fields",
    "commonality_family",
    "feature_definition_status",
    "commonality_evidence",
}

REGISTERED_ACTIONS = {
    "track_analysis_check_data_ready",
    "rcp_snapshot",
    "weapon_inventory",
    "login_logs_search",
    "archives_user_analysis",
    "archives_photo_search",
    "archives_user_profile",
    "archives_related_users",
    "archives_private_message_search",
    "archives_past_four_items",
    "rcp_event_detail",
    "rcp_event_feature_list",
    "rcp_policy_version_lookup",
    "rcp_policy_detail_lookup",
    "rcp_policy_release_record_lookup",
    "rcp_policy_tree_lookup",
    "rcp_node_policy_attribution",
    "rcp_node_bind_policy_attribution",
}

ACTION_SOURCE_DEFAULTS = {
    "login_logs_search": "infra_user_action_log",
    "weapon_inventory": "weapon_android",
}

# From the user-provided G-R9 oneRisk/device-label summary screenshot in this
# thread. These are not raw rows; keep extraction_source and confidence explicit.
GR9_REVIEWED_LABEL_SUMMARY = [
    {
        "value": "oneRiskLaunchLess10",
        "risk_sample_count": 7,
        "risk_hit_count": 7,
        "supporting_device_ids": [
            "ANDROID_f08a309f76a1a1e5",
            "ANDROID_1c553795346a2c5e",
            "ANDROID_a66515efe1e62168",
            "ANDROID_7317ac7f3f4380d4",
            "ANDROID_c61346749fdae1a8",
            "ANDROID_c5623fdd37be3214",
            "ANDROID_2dfabe453d466dde",
        ],
        "notes": "user-provided G-R9 label summary: launch count less than 10",
    },
    {
        "value": "oneRiskOneDayReset",
        "risk_sample_count": 7,
        "risk_hit_count": 4,
        "supporting_device_ids": [
            "ANDROID_f08a309f76a1a1e5",
            "ANDROID_1c553795346a2c5e",
            "ANDROID_a66515efe1e62168",
            "ANDROID_7317ac7f3f4380d4",
        ],
        "notes": "user-provided G-R9 label summary: factory reset within one day",
    },
    {
        "value": "developer",
        "risk_sample_count": 7,
        "risk_hit_count": 4,
        "supporting_device_ids": [
            "ANDROID_f08a309f76a1a1e5",
            "ANDROID_c61346749fdae1a8",
            "ANDROID_c5623fdd37be3214",
            "ANDROID_2dfabe453d466dde",
        ],
        "notes": "user-provided G-R9 label summary: developer mode",
    },
    {
        "value": "noLockScreen",
        "risk_sample_count": 7,
        "risk_hit_count": 4,
        "supporting_device_ids": [
            "ANDROID_f08a309f76a1a1e5",
            "ANDROID_c5623fdd37be3214",
            "ANDROID_2dfabe453d466dde",
            "ANDROID_7317ac7f3f4380d4",
        ],
        "notes": "user-provided G-R9 label summary: no lock screen configured",
    },
    {
        "value": "startShort",
        "risk_sample_count": 7,
        "risk_hit_count": 4,
        "supporting_device_ids": [
            "ANDROID_f08a309f76a1a1e5",
            "ANDROID_c61346749fdae1a8",
            "ANDROID_c5623fdd37be3214",
            "ANDROID_2dfabe453d466dde",
        ],
        "notes": "user-provided G-R9 label summary: short uptime/start duration",
    },
    {
        "value": "acCharger",
        "risk_sample_count": 7,
        "risk_hit_count": 3,
        "supporting_device_ids": [
            "ANDROID_f08a309f76a1a1e5",
            "ANDROID_c61346749fdae1a8",
            "ANDROID_2dfabe453d466dde",
        ],
        "notes": "user-provided G-R9 label summary: AC charging state",
    },
    {
        "value": "lockScreenLong",
        "risk_sample_count": 7,
        "risk_hit_count": 3,
        "supporting_device_ids": [
            "ANDROID_f08a309f76a1a1e5",
            "ANDROID_c61346749fdae1a8",
            "ANDROID_7317ac7f3f4380d4",
        ],
        "notes": "user-provided G-R9 label summary: abnormal long screen-off interval",
    },
    {
        "value": "changeMachine_rule",
        "risk_sample_count": 7,
        "risk_hit_count": 2,
        "supporting_device_ids": [
            "ANDROID_c5623fdd37be3214",
            "ANDROID_2dfabe453d466dde",
        ],
        "notes": "user-provided G-R9 label summary: device-change rule label",
    },
]


def _leaf(path: str) -> str:
    return str(path or "").split(".")[-1]


def _is_sensitive_path(path: str) -> bool:
    parts = re.split(r"[.\[\]_/]+", str(path or ""))
    return any(part in SENSITIVE_LEAVES for part in parts if part)


def _platform(source_name: str, field_path: str) -> str:
    text = f"{source_name}.{field_path}".lower()
    if "weapon_android" in text:
        return "android"
    if "weapon_ios" in text:
        return "ios"
    return "unknown"


def _source_action(source_name: str, field_path: str, value: str = "") -> str:
    lower = f"{source_name}.{field_path}.{value}".lower()
    if "infra_user_action_log" in lower or "login_logs" in lower:
        return "login"
    if "passport_action_log" in lower:
        return "passport"
    if "archives_user_analysis" in lower:
        return "passport"
    if "weapon_one_risk" in lower or "weaponrisk" in lower or "onerisk" in lower:
        return "oneRisk"
    if "raw_data" in lower:
        return "raw_data"
    return "unknown"


def _source_name_for_record(record: dict[str, Any]) -> str:
    action = str(record.get("source_action") or record.get("action") or record.get("action_name") or "")
    source_name = str(record.get("source_name") or record.get("source") or ACTION_SOURCE_DEFAULTS.get(action) or action)
    if not source_name:
        source_name = "unknown_source"
    return resolve_source(source_name).get("canonical_source", source_name)


def _action_for_record(record: dict[str, Any], source_name: str) -> str:
    action = str(record.get("source_action") or record.get("action") or record.get("action_name") or "")
    if source_name.startswith("weapon_") and action == "weapon_inventory":
        return str(record.get("layer") or "raw_data")
    if action:
        return action
    if source_name == "infra_user_action_log":
        return "login_logs_search"
    if source_name.startswith("weapon_"):
        return "weapon_inventory"
    return source_name


def _candidate_grain(field_path: str, value: str, raw_value: Any = None) -> str:
    leaf = _leaf(field_path)
    if leaf in HIGH_CARDINALITY_LEAVES:
        return "high_cardinality_anchor"
    if "labelinfo" in field_path.lower() and leaf in {"labelName", "label_name"}:
        return "label_value"
    if "weapon_one_risk" in field_path or "oneRisk" in value:
        return "label_value"
    if leaf in ACCESSIBILITY_FIELDS:
        return "array_element" if value else "field_presence"
    if leaf in {"action", "action_type", "login_type", "status", "type"} and value:
        return "enum_value"
    if "." in field_path and value:
        return "object_child_value"
    if value:
        return "scalar_value"
    return "field_presence"


def _role_hint(source_name: str, field_path: str, value: str = "") -> dict[str, Any]:
    resolved = resolve_field(source_name, field_path)
    role = classify_field_role(resolved.get("canonical_source", source_name), resolved.get("canonical_field_path", field_path))
    leaf = _leaf(field_path)
    if value in RESULT_SIGNAL_LEAVES or leaf in RESULT_SIGNAL_LEAVES:
        role["field_role"] = "result_signal"
    if leaf in HIGH_CARDINALITY_LEAVES:
        role["field_role"] = "identifier_anchor"
        role["cardinality_hint"] = "high"
    if value.startswith("oneRisk") or value in {"developer", "noLockScreen", "startShort", "acCharger", "lockScreenLong"}:
        if role.get("field_role") in {"unknown_need_review", None}:
            role["field_role"] = "factual_device_label"
    return {
        "canonical_source": resolved.get("canonical_source", source_name),
        "canonical_field_path": resolved.get("canonical_field_path", field_path),
        "field_role_hint": role.get("field_role", "unknown_need_review"),
        "platform": role.get("platform") or _platform(source_name, field_path),
        "source_action": role.get("weapon_action") if role.get("weapon_action") != "unknown" else _source_action(source_name, field_path, value),
        "alignment_match_type": resolved.get("match_type"),
        "alignment_confidence": resolved.get("confidence"),
        "unresolved_reason": resolved.get("unresolved_reason"),
    }


def _safe_json_loads(value: Any) -> Any:
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


def _single_or_original(value: Any) -> Any:
    if isinstance(value, list) and len(value) == 1:
        return value[0]
    return value


def _iter_scalar_leaves(value: Any, prefix: str = "") -> Iterable[tuple[str, Any]]:
    """Yield scalar leaves while skipping credential/control fields."""
    if isinstance(value, dict):
        for key, child in value.items():
            child_prefix = f"{prefix}.{key}" if prefix else str(key)
            if _is_sensitive_path(child_prefix):
                continue
            yield from _iter_scalar_leaves(child, child_prefix)
    elif isinstance(value, list):
        if all(not isinstance(item, (dict, list)) for item in value):
            yield prefix, _single_or_original(value)
        else:
            for child in value:
                yield from _iter_scalar_leaves(child, prefix)
    else:
        if prefix and not _is_sensitive_path(prefix):
            yield prefix, value


def _derived_login_log_fields(payload: Any) -> Iterable[tuple[str, Any]]:
    """Unwrap realtime login log rows to offline infra_user_action_log paths."""
    if not isinstance(payload, dict):
        return
    rows = (((payload.get("data") or {}).get("logSearchModels")) or [])
    if not isinstance(rows, list):
        return
    direct_map = {
        "uri": "infra_user_action_log.uri",
        "sid": "infra_user_action_log.sid",
        "did": "infra_user_action_log.did",
        "userId": "infra_user_action_log.user_id",
        "userIp": "infra_user_action_log.user_ip",
        "user_ip": "infra_user_action_log.user_ip",
        "appVer": "infra_user_action_log.app_ver",
        "appver": "infra_user_action_log.app_ver",
        "userAgent": "infra_user_action_log.user_agent",
        "user_agent": "infra_user_action_log.user_agent",
        "method": "infra_user_action_log.action_type",
    }
    params_alias = {
        "appver": "appver",
        "appVer": "appver",
        "sysver": "sysver",
        "sys": "sysver",
        "mod": "mod",
        "net": "net",
        "channel": "channel",
        "kpn": "productName",
        "kpf": "platform",
        "product": "product",
        "productName": "productName",
        "subBiz": "subBiz",
        "androidApiLevel": "androidApiLevel",
        "android_os": "androidOs",
        "androidOs": "androidOs",
        "apiLevel": "apiLevel",
        "boardPlatform": "boardPlatform",
        "abi": "abi",
        "deviceBit": "deviceBit",
        "device_abi": "deviceAbi",
        "deviceAbi": "deviceAbi",
        "earphoneMode": "earphoneMode",
        "supportIpv6": "supportIpv6",
        "did_tag": "didTag",
        "didTag": "didTag",
        "cdid_tag": "cdidTag",
        "cdidTag": "cdidTag",
        "originalKpn": "originalKpn",
        "originalKpf": "originalKpf",
        "originalOs": "originalOs",
        "originalSys": "originalSys",
        "videoModelCrowdTag": "videoModelCrowdTag",
        "newOc": "newOc",
        "displayType": "displayType",
        "grantBrowseType": "grantBrowseType",
        "locale": "locale",
        "location": "location",
        "serverInfo": "serverInfo",
    }
    for row in rows:
        if not isinstance(row, dict):
            continue
        log_content = _safe_json_loads(row.get("logContent"))
        if not isinstance(log_content, dict):
            continue
        for key, field_path in direct_map.items():
            if key in log_content and not _is_sensitive_path(field_path):
                yield field_path, log_content.get(key)
        params = _safe_json_loads(log_content.get("params"))
        if isinstance(params, dict):
            for key, raw_value in params.items():
                target_key = params_alias.get(key)
                if not target_key:
                    continue
                field_path = f"infra_user_action_log.extra.extra.clientRequestInfo.{target_key}"
                if not _is_sensitive_path(field_path):
                    yield field_path, _single_or_original(raw_value)


def _derived_passport_fields_from_archives_user_analysis(payload: Any) -> Iterable[tuple[str, Any]]:
    """Map archives user-analysis rows to offline passport_action_log paths."""
    if not isinstance(payload, dict):
        return
    rows = (((payload.get("data") or {}).get("dataList")) or [])
    if not isinstance(rows, list):
        return
    direct_map = {
        "operateUri": "passport_action_log.uri",
        "appVersion": "passport_action_log.app_ver",
        "deviceId": "passport_action_log.device_id",
        "userIpDesc": "passport_action_log.user_ip",
    }
    for row in rows:
        if not isinstance(row, dict):
            continue
        for key, field_path in direct_map.items():
            if key in row and not _is_sensitive_path(field_path):
                yield field_path, row.get(key)
        # Do not map Chinese operateResult to passport status without an
        # explicit value-domain confirmation.
        request_param = _safe_json_loads(row.get("requestParam"))
        if isinstance(request_param, dict):
            for rel_path, raw_value in _iter_scalar_leaves(request_param):
                field_path = f"passport_action_log.params.{rel_path}"
                if not _is_sensitive_path(field_path):
                    yield field_path, raw_value
        extra_param = _safe_json_loads(row.get("extraParam"))
        if isinstance(extra_param, dict):
            for rel_path, raw_value in _iter_scalar_leaves(extra_param):
                field_path = f"passport_action_log.extra.{rel_path}"
                if not _is_sensitive_path(field_path):
                    yield field_path, raw_value
        photo_info = str(row.get("photoInfo") or "")
        for key, field_path in (("MOD:", "passport_action_log.phone_mod"), ("SYS:", "passport_action_log.sys_ver")):
            if key in photo_info:
                part = photo_info.split(key, 1)[1].split("\t", 1)[0].strip()
                if part:
                    yield field_path, part


def _derived_canonical_fields(source_name: str, payload: Any) -> Iterable[tuple[str, Any]]:
    if source_name == "infra_user_action_log":
        yield from _derived_login_log_fields(payload)
    elif source_name == "archives_user_analysis":
        yield from _derived_passport_fields_from_archives_user_analysis(payload)


def _skip_original_realtime_field(source_name: str, rel_path: str) -> bool:
    """Skip realtime wrapper/envelope fields replaced by canonical derived fields."""
    if source_name == "infra_user_action_log":
        return rel_path.startswith("code") or rel_path.startswith("data.")
    if source_name == "archives_user_analysis":
        return True
    return False


def _candidate_id(source_name: str, field_path: str, value: str, grain: str, prefix: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9]+", "_", f"{source_name}_{field_path}_{value or grain}").strip("_")
    return f"{prefix}_{safe[:96]}"


def make_candidate(
    *,
    source_name: str,
    field_path: str,
    field_value: str,
    risk_sample_count: int,
    risk_hit_count: int,
    supporting_user_ids: Iterable[str] | None = None,
    supporting_device_ids: Iterable[str] | None = None,
    sample_values: Iterable[str] | None = None,
    extraction_source: str,
    extraction_confidence: str,
    need_raw_confirm: bool,
    notes: str = "",
    prefix: str = "l3v",
) -> dict[str, Any]:
    role = _role_hint(source_name, field_path, field_value)
    grain = _candidate_grain(field_path, field_value)
    risk_hit_rate = round(risk_hit_count / risk_sample_count, 4) if risk_sample_count else 0.0
    source_action = role["source_action"] or _source_action(source_name, field_path, field_value)
    candidate = {
        "candidate_id": _candidate_id(source_name, field_path, field_value, grain, prefix),
        "source_name": role["canonical_source"] or source_name,
        "platform": role["platform"] or _platform(source_name, field_path),
        "action_or_layer": source_action,
        "source_action": source_action,
        "layer": source_action,
        "field_path": role["canonical_field_path"] or field_path,
        "field_value_or_pattern": field_value,
        "field_value": field_value,
        "candidate_grain": grain,
        "field_role_hint": role["field_role_hint"],
        "risk_observed_count": risk_sample_count,
        "risk_sample_count": risk_sample_count,
        "risk_covered_count": risk_sample_count if field_value else risk_hit_count,
        "risk_hit_count": risk_hit_count,
        "risk_value_count": risk_hit_count,
        "risk_hit_rate": risk_hit_rate,
        "risk_value_ratio": risk_hit_rate,
        "supporting_user_ids": sorted(set(str(x) for x in (supporting_user_ids or []) if x)),
        "supporting_device_ids": sorted(set(str(x) for x in (supporting_device_ids or []) if x)),
        "sample_values": list(sample_values or ([field_value] if field_value else [])),
        "extraction_source": extraction_source,
        "extraction_confidence": extraction_confidence,
        "need_raw_confirm": need_raw_confirm,
        "alignment_match_type": role["alignment_match_type"],
        "alignment_confidence": role["alignment_confidence"],
        "unresolved_reason": role["unresolved_reason"],
        "notes": notes,
    }
    return apply_candidate_protocol(candidate)


def _load_json(path: str | Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_l4_cards(path: str | Path) -> list[dict[str, Any]]:
    data = _load_json(path)
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("l4_candidate_validation_cards", "cards", "candidates"):
            val = data.get(key)
            if isinstance(val, list):
                return val
    raise ValueError(f"cannot find L4 cards list in {path}")


def candidates_from_l4_cards(path: str | Path) -> list[dict[str, Any]]:
    candidates = []
    for card in _load_l4_cards(path):
        field_path = str(card.get("field_name") or "")
        source_name = str(card.get("source_name") or "")
        role = _role_hint(source_name, field_path, "")
        leaf = _leaf(field_path)
        grain = "high_cardinality_anchor" if leaf in HIGH_CARDINALITY_LEAVES else "field_presence"
        source_action = role["source_action"] or _source_action(source_name, field_path)
        risk_observed_count = int(card.get("risk_observed_count") or 0)
        candidates.append(apply_candidate_protocol({
            "candidate_id": f"fp_{card.get('candidate_id', _candidate_id(source_name, field_path, '', grain, 'fp'))}",
            "source_name": role["canonical_source"] or source_name,
            "platform": role["platform"] or _platform(source_name, field_path),
            "action_or_layer": source_action,
            "source_action": source_action,
            "layer": source_action,
            "field_path": role["canonical_field_path"] or field_path,
            "field_value_or_pattern": "",
            "field_value": "",
            "candidate_grain": grain,
            "field_role_hint": role["field_role_hint"],
            "risk_observed_count": risk_observed_count,
            "risk_sample_count": risk_observed_count,
            "risk_covered_count": risk_observed_count,
            "risk_hit_count": int(card.get("risk_hit_count") or 0),
            "risk_value_count": int(card.get("risk_hit_count") or 0),
            "risk_hit_rate": float(card.get("risk_hit_rate") or 0.0),
            "risk_value_ratio": float(card.get("risk_hit_rate") or 0.0),
            "supporting_user_ids": [],
            "supporting_device_ids": [],
            "sample_values": [],
            "extraction_source": "report_reconstructed:existing_l4_cards_field_presence_fallback",
            "extraction_confidence": "partial",
            "need_raw_confirm": True,
            "alignment_match_type": role["alignment_match_type"],
            "alignment_confidence": role["alignment_confidence"],
            "unresolved_reason": role["unresolved_reason"],
            "notes": "field-level fallback from existing G-R9 L4 card; no raw value available",
        }))
    return candidates


def candidates_from_reviewed_gr9_label_summary() -> list[dict[str, Any]]:
    candidates = []
    for item in GR9_REVIEWED_LABEL_SUMMARY:
        candidates.append(make_candidate(
            source_name="weapon_android",
            field_path="weapon_android.weapon_one_risk",
            field_value=item["value"],
            risk_sample_count=int(item["risk_sample_count"]),
            risk_hit_count=int(item["risk_hit_count"]),
            supporting_device_ids=item["supporting_device_ids"],
            sample_values=[item["value"]],
            extraction_source="manual_summary:user_provided_gr9_label_summary_image_not_raw",
            extraction_confidence="partial",
            need_raw_confirm=True,
            notes=item["notes"],
            prefix="gr9_label",
        ))
    return candidates


def _coerce_records(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    if isinstance(data, dict):
        if data.get("schema_version") == "e2e_risk_observation_input_contract_v0_1" and isinstance(data.get("users"), list):
            return _records_from_e2e_contract(data)
        for key in ("records", "observations", "snapshots", "items"):
            if isinstance(data.get(key), list):
                return [x for x in data[key] if isinstance(x, dict)]
        return [data]
    return []


def _records_from_e2e_contract(data: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for user in data.get("users", []):
        if not isinstance(user, dict):
            continue
        user_id = str(user.get("user_id") or "")
        sources = user.get("sources") or {}
        if not isinstance(sources, dict):
            continue
        for source_name, source_payload in sources.items():
            if not isinstance(source_payload, dict):
                continue
            for action_or_layer, action_payload in source_payload.items():
                if not isinstance(action_payload, dict):
                    continue
                raw_body = action_payload.get("raw_body")
                source_status = str(action_payload.get("source_status") or "")
                if raw_body is None or source_status in {"not_exported", "to_be_exported", "no_data", "blocked", "timeout"}:
                    continue
                records.append({
                    "source_name": action_payload.get("source_name") or source_name,
                    "source_action": action_payload.get("action") or action_or_layer,
                    "layer": action_payload.get("layer") or action_or_layer,
                    "platform": action_payload.get("platform") or user.get("platform") or "unknown",
                    "user_id": user_id,
                    "device_id": _extract_device_id(raw_body),
                    "payload": raw_body,
                    "source_status": source_status,
                    "raw_body_format": action_payload.get("raw_body_format"),
                })
    return records


def _extract_device_id(raw_body: Any) -> str:
    if isinstance(raw_body, dict):
        for key in ("device_id", "deviceId", "did"):
            if raw_body.get(key):
                return str(raw_body[key])
    return ""


def _payload_for_record(record: dict[str, Any]) -> Any:
    for key in ("payload", "raw_data", "data", "snapshot", "observation", "source_observation"):
        if key in record:
            return record[key]
    return record


def _field_path_for_record(source_name: str, source_action: str, rel_path: str) -> str:
    if rel_path.startswith((
        "infra_user_action_log.",
        "passport_action_log.",
        "weapon_android.",
        "weapon_ios.",
    )):
        return rel_path
    if source_name.startswith("weapon_"):
        if rel_path.startswith("riskDataResults.body.data.labelInfo.") and rel_path.endswith(".labels.labelName"):
            return f"{source_name}.weapon_one_risk"
        if rel_path.startswith("riskDataResults.body.data.originalLog.weaponRisk"):
            return f"{source_name}.weapon_one_risk"
        if rel_path.startswith("riskDataResults.body.data.originalLog."):
            rel_path = rel_path[len("riskDataResults.body.data.originalLog."):]
    if rel_path.startswith(source_name + "."):
        return rel_path
    if source_name.startswith("weapon_") and source_action in {"raw_data", "oneRisk", "weapon_one_risk"}:
        if rel_path.startswith(("raw_data.", "weapon_one_risk", "oneRisk", "weaponRisk", "labelInfo")):
            return f"{source_name}.{rel_path}"
        return f"{source_name}.{source_action}.{rel_path}"
    return f"{source_name}.{rel_path}"


def _flatten(value: Any, prefix: str = "") -> Iterable[tuple[str, Any]]:
    if isinstance(value, dict):
        for key, child in value.items():
            child_prefix = f"{prefix}.{key}" if prefix else str(key)
            yield from _flatten(child, child_prefix)
    elif isinstance(value, list) and _leaf(prefix) in ACCESSIBILITY_FIELDS and any(isinstance(item, dict) for item in value):
        yield prefix, value
    elif isinstance(value, list) and any(isinstance(item, dict) for item in value):
        for child in value:
            if isinstance(child, dict):
                yield from _flatten(child, prefix)
            else:
                yield prefix, child
    else:
        yield prefix, value


def _parse_list_like(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value if str(v)]
    if isinstance(value, tuple):
        return [str(v) for v in value if str(v)]
    text = str(value).strip()
    if not text or text in {"[]", "null", "None"}:
        return []
    if text.startswith("[") and text.endswith("]"):
        try:
            parsed = ast.literal_eval(text)
            if isinstance(parsed, list):
                return [str(v) for v in parsed if str(v)]
        except (SyntaxError, ValueError):
            pass
    if "," in text:
        return [part.strip() for part in text.split(",") if part.strip()]
    return [text]


def _is_complex_unsupported(value: Any) -> bool:
    if isinstance(value, (dict, list, tuple)):
        return False
    text = str(value or "").strip()
    if not text:
        return False
    return len(text) > 2048


def _accessibility_elements(value: Any) -> list[str]:
    elements = []
    for item in _parse_list_like(value):
        elements.append(item)
        if "/" in item:
            elements.append(item.split("/", 1)[0])
    return sorted(set(elements))


def _label_names_from_object_list(value: Any) -> list[str]:
    labels: list[str] = []
    if not isinstance(value, list):
        return labels
    for item in value:
        if not isinstance(item, dict):
            continue
        for key in ("labelName", "label_name", "name", "label"):
            raw = item.get(key)
            if raw:
                labels.append(str(raw))
                break
    return sorted(set(labels))


def validate_candidate_schema(candidate: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    missing = sorted(field for field in REQUIRED_CANDIDATE_FIELDS if field not in candidate)
    if missing:
        errors.append(f"missing required fields: {', '.join(missing)}")
    grain = candidate.get("candidate_grain")
    if grain not in CANDIDATE_GRAINS:
        errors.append(f"invalid candidate_grain: {grain}")
    if candidate.get("extraction_confidence") not in {"high", "partial", "low"}:
        errors.append(f"invalid extraction_confidence: {candidate.get('extraction_confidence')}")
    if not isinstance(candidate.get("supporting_user_ids", []), list):
        errors.append("supporting_user_ids must be list")
    if not isinstance(candidate.get("supporting_device_ids", []), list):
        errors.append("supporting_device_ids must be list")
    if "need_raw_confirm" in candidate and not isinstance(candidate.get("need_raw_confirm"), bool):
        errors.append("need_raw_confirm must be boolean")
    return errors


def candidates_from_raw_observations(path: str | Path) -> list[dict[str, Any]]:
    records = _coerce_records(_load_json(path))
    grouped: dict[tuple[str, str, str], dict[str, Any]] = {}
    sample_count_by_source: dict[str, set[str]] = defaultdict(set)

    for i, record in enumerate(records):
        source_name = _source_name_for_record(record)
        source_action = _action_for_record(record, source_name)
        user_id = str(record.get("user_id") or record.get("uid") or "")
        device_id = str(record.get("device_id") or record.get("did") or "")
        entity_id = user_id or device_id or f"record_{i}"
        sample_count_by_source[source_name].add(entity_id)
        payload = _payload_for_record(record)

        flattened = [
            (rel_path, raw_value)
            for rel_path, raw_value in _flatten(payload)
            if not _skip_original_realtime_field(source_name, rel_path)
        ]
        flattened.extend(_derived_canonical_fields(source_name, payload))

        for rel_path, raw_value in flattened:
            if not rel_path:
                continue
            field_path = _field_path_for_record(source_name, source_action, rel_path)
            candidate_source_name = field_path.split(".", 1)[0] if "." in field_path else source_name
            sample_count_by_source[candidate_source_name].add(entity_id)
            leaf = _leaf(field_path)
            values: list[str]
            if "weapon_one_risk" in field_path or leaf == "weaponRisk":
                values = _parse_list_like(raw_value)
            elif isinstance(raw_value, list) and any(isinstance(item, dict) for item in raw_value):
                label_values = _label_names_from_object_list(raw_value)
                if label_values and ("labelinfo" in field_path.lower() or leaf.lower() in {"labels", "labelinfo"}):
                    field_path = f"{source_name}.weapon_one_risk" if source_name.startswith("weapon_") else field_path
                    values = label_values
                else:
                    values = ["need_pattern_extractor:list_of_objects"]
            elif leaf in ACCESSIBILITY_FIELDS:
                values = _accessibility_elements(raw_value)
            elif isinstance(raw_value, list):
                values = _parse_list_like(raw_value)
            elif isinstance(raw_value, dict):
                continue
            elif _is_complex_unsupported(raw_value):
                values = ["need_pattern_extractor:oversized_value"]
            else:
                values = [str(raw_value)] if str(raw_value) else []

            for value in values:
                if leaf in HIGH_CARDINALITY_LEAVES:
                    value = "__anchor_value_redacted__"
                key = (candidate_source_name, field_path, value)
                if key not in grouped:
                    grouped[key] = {
                        "users": set(),
                        "devices": set(),
                        "values": set(),
                    }
                if user_id:
                    grouped[key]["users"].add(user_id)
                if device_id:
                    grouped[key]["devices"].add(device_id)
                grouped[key]["values"].add(value)
                grouped[key]["actions"] = grouped[key].get("actions", set())
                grouped[key]["actions"].add(source_action)

    candidates = []
    for (source_name, field_path, value), support in sorted(grouped.items()):
        risk_sample_count = len(sample_count_by_source[source_name]) or len(support["users"]) or len(support["devices"]) or 1
        risk_hit_count = max(len(support["users"]), len(support["devices"]), 1)
        candidate_value = value
        feature_type = "raw_field"
        bucket = None
        if is_numeric_bucketable(value, field_path):
            bucket = bucket_for_value(value)
            if bucket:
                candidate_value = bucket["bucket_label"]
                feature_type = "numeric_bucket"
        candidate = make_candidate(
            source_name=source_name,
            field_path=field_path,
            field_value=candidate_value,
            risk_sample_count=risk_sample_count,
            risk_hit_count=risk_hit_count,
            supporting_user_ids=support["users"],
            supporting_device_ids=support["devices"],
            sample_values=sorted(support["values"]),
            extraction_source=f"raw_observation:{path}",
            extraction_confidence="high",
            need_raw_confirm=False,
            notes="extracted from local raw observation file",
            prefix="raw",
        )
        if feature_type == "numeric_bucket" and bucket:
            candidate["feature_type"] = "numeric_bucket"
            candidate["value_type"] = infer_value_type(value, field_path)
            candidate["feature_name"] = f"{field_path}#{bucket['bucket_label']}"
            candidate["feature_definition"] = {
                "source_field": field_path,
                "bucket_method": bucket["bucket_method"],
                "bucket_label": bucket["bucket_label"],
                "bucket_range": bucket["bucket_range"],
            }
            candidate["bucket_label"] = bucket["bucket_label"]
            candidate["bucket_range"] = bucket["bucket_range"]
            candidate["candidate_value"] = bucket["bucket_label"]
            candidate["field_value"] = bucket["bucket_label"]
            candidate["field_value_or_pattern"] = bucket["bucket_label"]
        if candidate["field_value"].startswith("need_pattern_extractor:"):
            candidate["candidate_grain"] = "unsupported_complex_value"
            candidate["field_role_hint"] = "unknown_need_review"
            candidate["extraction_confidence"] = "low"
            candidate["need_raw_confirm"] = False
            candidate["parser_needed"] = True
            candidate["feature_type"] = "derived_feature"
            candidate["value_type"] = "unknown"
            candidate["feature_definition"] = {}
            candidate["feature_definition_status"] = "missing"
            candidate["commonality_family"] = "expanded_feature_commonality"
            candidate["commonality_evidence"] = []
            candidate["baseline_mode"] = "discovery_only"
            candidate["normal_hit_rate"] = None
            candidate["lift"] = None
            candidate["notes"] = "unsupported complex value; parser or downstream pattern extractor required"
        candidates.append(candidate)
        actions = support.get("actions") or set()
        if actions:
            action_or_layer = sorted(actions)[0]
            candidates[-1]["action_or_layer"] = action_or_layer
            candidates[-1]["source_action"] = action_or_layer
            candidates[-1]["layer"] = action_or_layer
            candidates[-1] = apply_candidate_protocol(candidates[-1])
    return candidates


def dedupe_candidates(candidates: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for c in candidates:
        key = (
            str(c.get("source_name") or ""),
            str(c.get("field_path") or ""),
            str(c.get("field_value") or c.get("field_value_or_pattern") or ""),
            str(c.get("candidate_grain") or ""),
        )
        if key not in deduped:
            deduped[key] = c
            continue
        old = deduped[key]
        old["risk_hit_count"] = max(int(old.get("risk_hit_count") or 0), int(c.get("risk_hit_count") or 0))
        old["risk_value_count"] = old["risk_hit_count"]
        old["risk_sample_count"] = max(int(old.get("risk_sample_count") or 0), int(c.get("risk_sample_count") or 0))
        old["risk_observed_count"] = old["risk_sample_count"]
        old["risk_covered_count"] = max(int(old.get("risk_covered_count") or 0), int(c.get("risk_covered_count") or 0))
        old["risk_hit_rate"] = round(old["risk_hit_count"] / old["risk_sample_count"], 4) if old["risk_sample_count"] else 0.0
        old["risk_value_ratio"] = old["risk_hit_rate"]
        old["supporting_user_ids"] = sorted(set(old.get("supporting_user_ids", [])) | set(c.get("supporting_user_ids", [])))
        old["supporting_device_ids"] = sorted(set(old.get("supporting_device_ids", [])) | set(c.get("supporting_device_ids", [])))
        old["sample_values"] = sorted(set(old.get("sample_values", [])) | set(c.get("sample_values", [])))
        old["need_raw_confirm"] = bool(old.get("need_raw_confirm")) or bool(c.get("need_raw_confirm"))
        old["notes"] = f"{old.get('notes', '')}; merged duplicate from {c.get('extraction_source', '')}".strip("; ")
    return sorted(deduped.values(), key=lambda x: (x.get("candidate_grain", ""), x.get("source_name", ""), x.get("field_path", ""), x.get("field_value", "")))


def build_summary(candidates: list[dict[str, Any]], input_notes: list[str]) -> str:
    by_grain: dict[str, int] = defaultdict(int)
    by_source: dict[str, int] = defaultdict(int)
    non_empty = 0
    for c in candidates:
        by_grain[str(c.get("candidate_grain"))] += 1
        by_source[str(c.get("source_name"))] += 1
        if c.get("field_value_or_pattern"):
            non_empty += 1

    lines = [
        "# Structured L3 Candidates Summary v0.1",
        "",
        "## Input Boundary",
        "",
    ]
    for note in input_notes:
        lines.append(f"- {note}")
    lines.extend([
        "",
        "## Counts",
        "",
        f"- total_l3_candidates: {len(candidates)}",
        f"- field_value_or_pattern_non_empty: {non_empty}",
        f"- field_value_or_pattern_empty: {len(candidates) - non_empty}",
        f"- need_raw_confirm: {sum(1 for c in candidates if c.get('need_raw_confirm'))}",
        "",
        "## By Grain",
        "",
        "| candidate_grain | count |",
        "|---|---:|",
    ])
    for grain, count in sorted(by_grain.items()):
        lines.append(f"| {grain} | {count} |")
    lines.extend(["", "## By Source", "", "| source | count |", "|---|---:|"])
    for source, count in sorted(by_source.items()):
        lines.append(f"| {source} | {count} |")
    lines.extend([
        "",
        "## Registered Action Coverage",
        "",
        "The extractor is action-generic: every local observation with `action`, `action_name`, `source_action`, or `source_name` is routed through the same field-type extraction rules.",
        "",
        "| registered_action | extraction_entry |",
        "|---|---|",
    ])
    for action in sorted(REGISTERED_ACTIONS):
        lines.append(f"| {action} | supported_by_generic_observation_extractor |")
    lines.extend([
        "",
        "## Extraction Confidence",
        "",
        "| extraction_confidence | count |",
        "|---|---:|",
    ])
    by_confidence: dict[str, int] = defaultdict(int)
    for c in candidates:
        by_confidence[str(c.get("extraction_confidence"))] += 1
    for confidence, count in sorted(by_confidence.items()):
        lines.append(f"| {confidence} | {count} |")
    lines.extend([
        "",
        "## Value-Level Candidates",
        "",
        "| candidate_id | source | field_path | value | grain | risk_hit_rate | role | extraction_source |",
        "|---|---|---|---|---|---:|---|---|",
    ])
    for c in candidates:
        if not c.get("field_value_or_pattern"):
            continue
        lines.append(
            f"| {c['candidate_id']} | {c['source_name']} | {c['field_path']} | "
            f"{c['field_value_or_pattern']} | {c['candidate_grain']} | "
            f"{c['risk_hit_rate']:.4f} | {c['field_role_hint']} | {c['extraction_source']} |"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Build structured L3 value-level candidates")
    parser.add_argument("--input-raw-json", action="append", default=[], help="Local raw/snapshot JSON file")
    parser.add_argument("--input-l4-cards", help="Existing L4 cards used for field-level fallback")
    parser.add_argument("--include-gr9-label-summary", action="store_true",
                        help="Materialize reviewed G-R9 oneRisk label summary from this task context")
    parser.add_argument("--output", required=True, help="Output structured L3 candidate JSON")
    parser.add_argument("--summary-md", required=True, help="Output Markdown summary")
    args = parser.parse_args()

    candidates: list[dict[str, Any]] = []
    notes: list[str] = []

    if args.input_l4_cards:
        candidates.extend(candidates_from_l4_cards(args.input_l4_cards))
        notes.append(f"field-level fallback loaded from {args.input_l4_cards}")
    else:
        notes.append("no existing L4 cards provided for field-level fallback")

    if args.include_gr9_label_summary:
        candidates.extend(candidates_from_reviewed_gr9_label_summary())
        notes.append("value-level oneRisk labels loaded from user-provided G-R9 summary image/text, not raw rows")
    else:
        notes.append("G-R9 reviewed label summary not requested")

    if args.input_raw_json:
        for path in args.input_raw_json:
            candidates.extend(candidates_from_raw_observations(path))
            notes.append(f"raw/snapshot candidates extracted from {path}")
    else:
        notes.append("no local raw/snapshot JSON found or provided; no fabricated raw-only values")

    candidates = dedupe_candidates(candidates)
    schema_errors = []
    for candidate in candidates:
        for error in validate_candidate_schema(candidate):
            schema_errors.append(f"{candidate.get('candidate_id')}: {error}")
    if schema_errors:
        raise ValueError("candidate schema validation failed:\n" + "\n".join(schema_errors))

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(candidates, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    summary = Path(args.summary_md)
    summary.parent.mkdir(parents=True, exist_ok=True)
    summary.write_text(build_summary(candidates, notes), encoding="utf-8")

    print(f"wrote {len(candidates)} candidates -> {output}")
    print(f"wrote summary -> {summary}")


if __name__ == "__main__":
    main()
