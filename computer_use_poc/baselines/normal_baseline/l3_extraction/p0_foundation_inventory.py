#!/usr/bin/env python3
"""P0 foundation inventory scanner for cold-review raw bundles.

This module is intentionally local/offline. It reads existing raw-bundle files
and inventory artifacts, writes fact-layer coverage reports, and never calls
platforms, Hive, DataAgent, release, dist, or full_runtime paths.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote_plus


CONTAINER_NAMES = {
    "requestParam",
    "extraParam",
    "logContent",
    "params",
    "data",
    "originalLog",
    "labelInfo",
    "accessibilitySvc",
    "enabledAccessibilityServices",
    "enabledAccessibilityServiceList",
    "appList",
}

CONTAINER_ALIASES = {
    "enabledAccessibilityServiceList": "enabledAccessibilityServices",
    "app_list": "appList",
    "installedApps": "appList",
    "installAppList": "appList",
    "applicationList": "appList",
    "apps": "appList",
}

APP_LIST_ALIASES = {
    "appList",
    "app_list",
    "installedApps",
    "installAppList",
    "applicationList",
    "apps",
}

ACCESSIBILITY_SERVICE_CONTAINERS = {
    "accessibilitySvc",
    "enabledAccessibilityServices",
}

CREDENTIAL_TOKENS = {
    "authorization",
    "authtoken",
    "bindtoken",
    "captcha_token",
    "cookie",
    "cookies",
    "credential",
    "credentials",
    "header",
    "headers",
    "logintoken",
    "password",
    "passwd",
    "quicklogintoken",
    "refreshtoken",
    "resettoken",
    "secret",
    "secrets",
    "session",
    "sessions",
    "ssecurity",
    "token",
    "tokens",
}

IDENTIFIER_TOKENS = {
    "device_id",
    "deviceid",
    "did",
    "event_id",
    "eventid",
    "guid",
    "idfa",
    "idfv",
    "imei",
    "ip",
    "oaid",
    "openid",
    "open_id",
    "photo_id",
    "photoid",
    "requestid",
    "request_id",
    "traceid",
    "trace_id",
    "uid",
    "userid",
    "user_id",
    "uuid",
}

NOISE_LEAVES = {
    "_http_status",
    "body_present",
    "content_type",
    "costTime",
    "currentTime",
    "http_status",
    "requestId",
    "request_id",
    "response_mode",
    "traceId",
    "trace_id",
}

PAGINATION_LEAVES = {
    "count",
    "hasMore",
    "has_more",
    "limit",
    "page",
    "pageIndex",
    "pageNo",
    "pageNum",
    "pageSize",
    "page_size",
    "size",
    "total",
    "totalCount",
}

WRAPPER_LEAF_REPORT_ONLY = {
    "_local_action",
    "action",
    "action_name",
    "body_truncated",
    "cap_reason",
    "elapsed_ms",
    "observed_bytes",
    "raw_body_handling",
    "records_count",
}

WEAPON_REPORT_ONLY_LEAVES = {
    "apiLevel",
    "appComponentFactory",
    "appVersion",
    "brand",
    "buildBootloader",
    "buildDisplayRom",
    "hardware",
    "model",
    "productName",
    "resolution",
    "systemVersion",
    "uname",
    "weaponPlatform",
}

WEAPON_MUST_KEY_HINTS = {
    "accessibility",
    "bootCount",
    "debug",
    "frida",
    "hasPassword",
    "hook",
    "idc",
    "invisibleVerify",
    "isUsb",
    "noLockScreen",
    "oneIpInfo",
    "proxy",
    "remoteControl",
    "risk",
    "root",
    "sim",
    "simulator",
    "startCount",
    "user_behavior",
    "user_risk",
    "weaponDecodeHeader",
    "weaponKey",
    "weaponStatus",
    "weaponVersion",
    "xposed",
}


def _load_json(path: str | Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: str | Path, payload: Any) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _leaf(path: str) -> str:
    return str(path or "").split(".")[-1]


def _canonical_container_name(name: str) -> str:
    return CONTAINER_ALIASES.get(name, name)


def normalize_path(path: str) -> str:
    """Normalize wrapper, array, and equivalent body prefixes for path matching."""
    text = str(path or "").strip()
    text = text.replace("[].", ".").replace("[]", "")
    text = re.sub(r"\[\d+\]", "", text)
    text = re.sub(r"\.{2,}", ".", text).strip(".")
    prefixes = [
        "upstream.body.body.",
        "upstream.body.",
        "body.",
        "payload.",
        "raw_body.",
        "_local_payload.",
    ]
    for prefix in prefixes:
        if text.startswith(prefix):
            text = text[len(prefix):]
            break
    if text.startswith("data.data."):
        text = text[len("data."):]
    return text


def _suffixes(path: str) -> set[str]:
    parts = [p for p in normalize_path(path).split(".") if p]
    return {".".join(parts[i:]) for i in range(len(parts))}


def _ancestors(path: str) -> list[str]:
    parts = [p for p in normalize_path(path).split(".") if p]
    return [".".join(parts[:i]) for i in range(1, len(parts))]


def _array_like_path(path: str) -> bool:
    lowered = str(path or "").lower()
    return any(token in lowered for token in ("list", "datalist", "rows", "items", "applist", "relationedgelist"))


def _is_weapon_action(action: str) -> bool:
    return str(action or "").startswith("weapon_")


def _weapon_deep_flags(path: str) -> dict[str, bool]:
    lower = str(path or "").lower()
    return {
        "is_weapon_originalLog": "originallog" in lower,
        "is_weaponDecodeHeader": "weapondecodeheader" in lower,
        "is_user_behavior": "user_behavior" in lower or "userbehavior" in lower,
    }


def weapon_deep_inventory_policy(action: str, raw_path: str, value: Any, eligibility: str) -> dict[str, Any]:
    flags = _weapon_deep_flags(raw_path)
    in_weapon_deep = _is_weapon_action(action) and flags["is_weapon_originalLog"]
    if not in_weapon_deep:
        return {
            "inventory_policy": "",
            "inventory_policy_reason": "",
            "weapon_missing_reason": "",
            **flags,
            "is_risk_candidate_key_field": False,
        }
    if eligibility == "sensitive_blocked":
        return {
            "inventory_policy": "exclude_with_reason",
            "inventory_policy_reason": "sensitive_blocked",
            "weapon_missing_reason": "sensitive_blocked",
            **flags,
            "is_risk_candidate_key_field": False,
        }
    if eligibility in {"non_scalar_container", "needs_parse"}:
        return {
            "inventory_policy": "exclude_with_reason",
            "inventory_policy_reason": "raw_container_or_blob_covered_by_children",
            "weapon_missing_reason": "non_scalar_skipped",
            **flags,
            "is_risk_candidate_key_field": False,
        }
    leaf = _leaf(raw_path)
    lower_path = str(raw_path or "").lower()
    is_key_field = (
        flags["is_weaponDecodeHeader"]
        or flags["is_user_behavior"]
        or any(hint.lower() in lower_path for hint in (h.lower() for h in WEAPON_MUST_KEY_HINTS))
    )
    if is_key_field:
        if flags["is_weaponDecodeHeader"]:
            reason = "weaponDecodeHeader_not_registered"
        elif flags["is_user_behavior"]:
            reason = "user_behavior_path_not_registered"
        else:
            reason = "weapon_originalLog_not_flattened"
        return {
            "inventory_policy": "must_inventory",
            "inventory_policy_reason": "weapon_deep_key_field",
            "weapon_missing_reason": reason,
            **flags,
            "is_risk_candidate_key_field": True,
        }
    if leaf in WEAPON_REPORT_ONLY_LEAVES or eligibility == "report_only":
        return {
            "inventory_policy": "report_only_inventory",
            "inventory_policy_reason": "ordinary_device_environment_context",
            "weapon_missing_reason": "weapon_originalLog_not_flattened",
            **flags,
            "is_risk_candidate_key_field": False,
        }
    if eligibility == "noise":
        return {
            "inventory_policy": "exclude_with_reason",
            "inventory_policy_reason": "schema_noise_or_wrapper_field",
            "weapon_missing_reason": "non_scalar_skipped",
            **flags,
            "is_risk_candidate_key_field": False,
        }
    return {
        "inventory_policy": "report_only_inventory",
        "inventory_policy_reason": "weapon_originalLog_leaf_report_only_until_review",
        "weapon_missing_reason": "weapon_originalLog_not_flattened",
        **flags,
        "is_risk_candidate_key_field": False,
    }


def _aliases_for_container(container: str) -> list[str]:
    if container == "appList":
        return sorted(APP_LIST_ALIASES)
    if container == "enabledAccessibilityServices":
        return ["enabledAccessibilityServices", "enabledAccessibilityServiceList"]
    return [container]


def _normalized_prefix(path: str) -> str:
    norm = normalize_path(path)
    lower = norm.lower()
    if "originallog.weapondecodeheader" in lower:
        return "originalLog.weaponDecodeHeader"
    if "originallog.user_behavior" in lower or "originallog.userbehavior" in lower:
        return "originalLog.user_behavior"
    if "originallog" in lower:
        parts = norm.split(".")
        try:
            idx = [p.lower() for p in parts].index("originallog")
            return ".".join(parts[idx:idx + 3])
        except ValueError:
            return "originalLog"
    parts = norm.split(".")
    return ".".join(parts[:4]) if len(parts) >= 4 else norm


def _missing_reason_for_record(record: dict[str, Any]) -> str:
    if record.get("weapon_missing_reason"):
        return str(record["weapon_missing_reason"])
    if record.get("eligibility_status") == "non_scalar_container":
        return "non_scalar_skipped"
    if record.get("eligibility_status") == "sensitive_blocked":
        return "sensitive_blocked"
    if record.get("source_action", "").startswith("weapon_"):
        return "weapon_originalLog_not_flattened" if record.get("is_weapon_originalLog") else "source_action_variant_mismatch"
    return "unknown"


def _build_top_missing_groups(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], dict[str, Any]] = {}
    for record in records:
        key = (str(record.get("source_action") or ""), _normalized_prefix(str(record.get("raw_path") or "")))
        group = grouped.setdefault(key, {
            "source_action": key[0],
            "normalized_raw_path_prefix": key[1],
            "raw_path_examples": [],
            "missing_count": 0,
            "users": set(),
            "value_shapes": Counter(),
            "is_weapon_originalLog": False,
            "is_weaponDecodeHeader": False,
            "is_user_behavior": False,
            "is_risk_candidate_key_field": False,
            "missing_reasons": Counter(),
            "inventory_policy_counts": Counter(),
        })
        group["missing_count"] += 1
        if record.get("user_id"):
            group["users"].add(str(record["user_id"]))
        if len(group["raw_path_examples"]) < 5 and record.get("raw_path") not in group["raw_path_examples"]:
            group["raw_path_examples"].append(record.get("raw_path"))
        group["value_shapes"][str(record.get("value_shape") or "unknown")] += 1
        group["is_weapon_originalLog"] = group["is_weapon_originalLog"] or bool(record.get("is_weapon_originalLog"))
        group["is_weaponDecodeHeader"] = group["is_weaponDecodeHeader"] or bool(record.get("is_weaponDecodeHeader"))
        group["is_user_behavior"] = group["is_user_behavior"] or bool(record.get("is_user_behavior"))
        group["is_risk_candidate_key_field"] = group["is_risk_candidate_key_field"] or bool(record.get("is_risk_candidate_key_field"))
        group["missing_reasons"][_missing_reason_for_record(record)] += 1
        group["inventory_policy_counts"][str(record.get("inventory_policy") or "unclassified")] += 1
    out = []
    for group in grouped.values():
        value_shape = group["value_shapes"].most_common(1)[0][0] if group["value_shapes"] else "unknown"
        missing_reason = group["missing_reasons"].most_common(1)[0][0] if group["missing_reasons"] else "unknown"
        out.append({
            "source_action": group["source_action"],
            "normalized_raw_path_prefix": group["normalized_raw_path_prefix"],
            "raw_path_examples": group["raw_path_examples"],
            "missing_count": group["missing_count"],
            "user_count": len(group["users"]),
            "value_shape": value_shape,
            "is_weapon_originalLog": group["is_weapon_originalLog"],
            "is_weaponDecodeHeader": group["is_weaponDecodeHeader"],
            "is_user_behavior": group["is_user_behavior"],
            "is_risk_candidate_key_field": group["is_risk_candidate_key_field"],
            "missing_reason": missing_reason,
            "inventory_policy_counts": dict(group["inventory_policy_counts"]),
        })
    return sorted(out, key=lambda r: r["missing_count"], reverse=True)[:50]


def _path_parts(path: str) -> list[str]:
    return [p for p in re.split(r"[.\[\]_/]+", str(path or "")) if p]


def _normalized_token(token: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(token or "").lower())


def _sensitive_level(path: str, value: Any = None) -> str:
    parts = {_normalized_token(p) for p in _path_parts(path)}
    if parts & CREDENTIAL_TOKENS:
        return "credential"
    if parts & IDENTIFIER_TOKENS:
        return "identifier"
    return "none"


def _value_shape(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, dict):
        return "dict"
    if isinstance(value, list):
        return "list"
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return "empty_string"
        if text[0] in "[{" and text[-1:] in "]}":
            return "json_string"
        if "=" in text and ("&" in text or ";" in text):
            return "querystring"
        return "string"
    return type(value).__name__


def _preview_value(path: str, value: Any, max_len: int = 120) -> tuple[str, str]:
    level = _sensitive_level(path, value)
    if level == "credential":
        return "__redacted_sensitive__", "redacted"
    if isinstance(value, (dict, list)):
        text = f"<{_value_shape(value)}>"
    else:
        text = "" if value is None else str(value)
    if len(text) > max_len:
        return text[:max_len] + "...", "truncated"
    return text, "raw_preview"


def _iter_paths(value: Any, prefix: str = "", *, include_containers: bool = True) -> list[tuple[str, Any, bool]]:
    rows: list[tuple[str, Any, bool]] = []
    if isinstance(value, dict):
        if include_containers and prefix:
            rows.append((prefix, value, True))
        for key, child in value.items():
            child_prefix = f"{prefix}.{key}" if prefix else str(key)
            rows.extend(_iter_paths(child, child_prefix, include_containers=include_containers))
    elif isinstance(value, list):
        if include_containers and prefix:
            rows.append((prefix, value, True))
        for child in value[:200]:
            if isinstance(child, (dict, list)):
                rows.extend(_iter_paths(child, prefix, include_containers=include_containers))
        if prefix and all(not isinstance(child, (dict, list)) for child in value):
            rows.append((prefix, value, False))
    elif prefix:
        rows.append((prefix, value, False))
    return rows


def _parse_value(value: Any) -> tuple[bool, str, Any, str]:
    if isinstance(value, dict):
        return True, "native_dict", value, ""
    if isinstance(value, list):
        return True, "native_list", value, ""
    if not isinstance(value, str):
        return False, "not_parseable", None, "non_string_scalar"
    text = value.strip()
    if not text:
        return False, "not_parseable", None, "empty_string"
    decoded = text
    for _ in range(2):
        nxt = unquote_plus(decoded)
        if nxt == decoded:
            break
        decoded = nxt.strip()
    if decoded[:1] in "[{" and decoded[-1:] in "]}":
        try:
            parsed = json.loads(decoded)
            parser_type = "json_array" if isinstance(parsed, list) else "json_object"
            return True, parser_type, parsed, ""
        except json.JSONDecodeError as exc:
            return False, "json_error", None, str(exc)
    if "=" in decoded and any(sep in decoded for sep in ("&", ";")):
        parsed_qs = parse_qs(decoded.lstrip("?"), keep_blank_values=True)
        if parsed_qs:
            parsed = {key: values[-1] if values else "" for key, values in parsed_qs.items()}
            return True, "querystring", parsed, ""
    return False, "not_parseable", None, "no_supported_parser"


def _parse_accessibility_services(value: Any) -> tuple[bool, str, Any, str, bool]:
    if value is None:
        return True, "accessibility_service_list_empty", {"__empty_value__": True, "services": []}, "", True
    if isinstance(value, list):
        raw_items = [str(item).strip() for item in value if str(item).strip()]
    else:
        text = str(value).strip()
        if not text:
            return True, "accessibility_service_list_empty", {"__empty_value__": True, "services": []}, "", True
        raw_items = [item.strip() for item in re.split(r"[:;,\n]+", text) if item.strip()]
    services = []
    for item in raw_items:
        package = item
        component = ""
        if "/" in item:
            package, component = item.split("/", 1)
        elif "." in item:
            parts = item.rsplit(".", 1)
            package = parts[0]
            component = parts[-1] if len(parts) > 1 else ""
        services.append({
            "raw_service_string": item,
            "service_package": package,
            "component": component,
        })
    return True, "accessibility_service_list", {"services": services}, "", False


def _is_container_path(path: str) -> bool:
    return _canonical_container_name(_leaf(path)) in CONTAINER_NAMES


def _looks_parseable(value: Any) -> bool:
    if isinstance(value, (dict, list)):
        return True
    if not isinstance(value, str):
        return False
    shape = _value_shape(value)
    return shape in {"json_string", "querystring"}


def _eligibility_status(path: str, value: Any, *, is_container: bool = False) -> str:
    guard = guard_for_path_value(path, value)
    if _sensitive_level(path, value) == "credential":
        return "sensitive_blocked"
    if guard:
        return guard["guard_level"]
    if is_container and _looks_parseable(value):
        return "needs_parse"
    if is_container:
        return "non_scalar_container"
    if _value_shape(value) in {"dict", "list"}:
        return "non_scalar_container"
    if _sensitive_level(path, value) == "identifier":
        return "report_only"
    return "eligible"


def _filtered_reason(path: str, value: Any, eligibility: str) -> str:
    if eligibility == "eligible":
        return ""
    guard = guard_for_path_value(path, value)
    if guard:
        return str(guard["guard_reason"])
    if eligibility == "sensitive_blocked":
        return "credential_or_sensitive_control_field"
    if eligibility == "non_scalar_container":
        return "non_scalar_container_value"
    if eligibility == "needs_parse":
        return "container_requires_child_parse"
    return eligibility


def guard_for_path_value(path: str, value: Any) -> dict[str, Any] | None:
    leaf = _leaf(path)
    lower_path = str(path or "").lower()
    lower_leaf = leaf.lower()
    text = "" if value is None else str(value)
    lower_text = text.lower()
    if leaf == "boardPlatform":
        return {
            "guard_level": "report_only",
            "guard_reason": "event_environment_context_only",
            "high_value_allowed": False,
            "combo_allowed": True,
        }
    if leaf in NOISE_LEAVES or lower_leaf in {x.lower() for x in NOISE_LEAVES}:
        return {
            "guard_level": "noise",
            "guard_reason": "transport_or_response_wrapper_field",
            "high_value_allowed": False,
            "combo_allowed": False,
        }
    if leaf in WRAPPER_LEAF_REPORT_ONLY:
        return {
            "guard_level": "report_only",
            "guard_reason": "wrapper_or_source_quality_context",
            "high_value_allowed": False,
            "combo_allowed": False,
        }
    if leaf in PAGINATION_LEAVES:
        return {
            "guard_level": "report_only",
            "guard_reason": "pagination_cap_or_query_parameter",
            "high_value_allowed": False,
            "combo_allowed": False,
        }
    if "logtags" in lower_path and lower_leaf == "color":
        return {
            "guard_level": "noise",
            "guard_reason": "fixed_logTags_color_schema",
            "high_value_allowed": False,
            "combo_allowed": False,
        }
    if lower_leaf == "clientip":
        return {
            "guard_level": "noise",
            "guard_reason": "platform_internal_clientIp",
            "high_value_allowed": False,
            "combo_allowed": False,
        }
    if any(token in lower_leaf for token in ("avatar", "headurl", "background", "bgurl")) and "default" in lower_text:
        return {
            "guard_level": "noise",
            "guard_reason": "default_avatar_or_background_url",
            "high_value_allowed": False,
            "combo_allowed": False,
        }
    return None


def _visibility_status(raw_seen: bool, inventory_seen: bool, parsed_seen: bool) -> str:
    if parsed_seen:
        return "parsed_seen"
    if inventory_seen:
        return "inventory_seen"
    if raw_seen:
        return "raw_seen"
    return "missing"


def load_manifest_rows(wave_dir: str | Path) -> list[dict[str, Any]]:
    wave = Path(wave_dir)
    manifest_path = wave / "wave_raw_bundle_manifest.json"
    if manifest_path.exists():
        rows = _load_json(manifest_path)
        return [r for r in rows if isinstance(r, dict)]
    rows = []
    for raw_path in sorted((wave / "raw").glob("*.json")):
        stem = raw_path.stem
        action, _, user_id = stem.rpartition("_")
        rows.append({
            "wave_id": wave.name,
            "action": action or "unknown",
            "user_id": user_id or "",
            "raw_file_path": str(raw_path),
            "raw_present": True,
        })
    return rows


def load_inventory_paths(inventory_path: str | Path, wave_id: str) -> dict[str, set[str]]:
    data = _load_json(inventory_path)
    wave_data = data.get(wave_id, {}) if isinstance(data, dict) else {}
    out: dict[str, set[str]] = {}
    for action, rows in wave_data.items():
        paths = set()
        for row in rows or []:
            if isinstance(row, dict) and row.get("field_path"):
                paths.add(str(row["field_path"]))
        out[str(action)] = paths
    return out


def _build_inventory_match_index(inventory_paths: dict[str, set[str]]) -> dict[str, Any]:
    normalized_by_action: dict[str, dict[str, str]] = {}
    suffix_by_action: dict[str, dict[str, str]] = {}
    global_normalized: dict[str, str] = {}
    global_suffix: dict[str, str] = {}
    leaf_by_action: dict[str, set[str]] = defaultdict(set)
    global_leaf: set[str] = set()
    for action, paths in inventory_paths.items():
        normalized_by_action[action] = {}
        suffix_by_action[action] = {}
        for path in paths:
            norm = normalize_path(path)
            normalized_by_action[action].setdefault(norm, path)
            global_normalized.setdefault(norm, path)
            leaf_by_action[action].add(_leaf(norm))
            global_leaf.add(_leaf(norm))
            for suffix in _suffixes(path):
                suffix_by_action[action].setdefault(suffix, path)
                global_suffix.setdefault(suffix, path)
    return {
        "normalized_by_action": normalized_by_action,
        "suffix_by_action": suffix_by_action,
        "global_normalized": global_normalized,
        "global_suffix": global_suffix,
        "leaf_by_action": leaf_by_action,
        "global_leaf": global_leaf,
    }


def _resolve_path_match(
    *,
    raw_path: str,
    action: str,
    inventory_paths: dict[str, set[str]],
    inventory_index: dict[str, Any],
    parsed_children_seen_count: int,
    missing_path_count: int,
) -> dict[str, Any]:
    exact_paths = inventory_paths.get(action, set())
    if raw_path in exact_paths:
        return {
            "inventory_seen": True,
            "path_match_type": "exact",
            "normalized_inventory_path": normalize_path(raw_path),
            "matched_inventory_path": raw_path,
        }
    norm = normalize_path(raw_path)
    same_action_norm = inventory_index["normalized_by_action"].get(action, {})
    same_action_suffix = inventory_index["suffix_by_action"].get(action, {})
    repeated_array_candidate = missing_path_count >= 10 and _array_like_path(raw_path)
    if repeated_array_candidate:
        for candidate in (norm, *_suffixes(raw_path)):
            matched = (
                same_action_norm.get(candidate)
                or same_action_suffix.get(candidate)
                or inventory_index["global_normalized"].get(candidate)
                or inventory_index["global_suffix"].get(candidate)
            )
            if matched:
                return {
                    "inventory_seen": True,
                    "path_match_type": "repeated_array_normalized",
                    "normalized_inventory_path": normalize_path(matched),
                    "matched_inventory_path": matched,
                }
    for candidate in (norm, *_suffixes(raw_path)):
        if candidate in same_action_norm:
            return {
                "inventory_seen": True,
                "path_match_type": "normalized_alias",
                "normalized_inventory_path": normalize_path(same_action_norm[candidate]),
                "matched_inventory_path": same_action_norm[candidate],
            }
        if candidate in same_action_suffix:
            return {
                "inventory_seen": True,
                "path_match_type": "normalized_alias",
                "normalized_inventory_path": normalize_path(same_action_suffix[candidate]),
                "matched_inventory_path": same_action_suffix[candidate],
            }
    for candidate in (norm, *_suffixes(raw_path)):
        if candidate in inventory_index["global_normalized"]:
            matched = inventory_index["global_normalized"][candidate]
            return {
                "inventory_seen": True,
                "path_match_type": "normalized_alias",
                "normalized_inventory_path": normalize_path(matched),
                "matched_inventory_path": matched,
            }
        if candidate in inventory_index["global_suffix"]:
            matched = inventory_index["global_suffix"][candidate]
            return {
                "inventory_seen": True,
                "path_match_type": "normalized_alias",
                "normalized_inventory_path": normalize_path(matched),
                "matched_inventory_path": matched,
            }

    ancestors = _ancestors(raw_path)
    for parent in reversed(ancestors):
        if parent in same_action_norm or parent in same_action_suffix:
            matched = same_action_norm.get(parent) or same_action_suffix.get(parent)
            return {
                "inventory_seen": True,
                "path_match_type": "container_parent_child",
                "normalized_inventory_path": normalize_path(matched),
                "matched_inventory_path": matched,
            }
    if parsed_children_seen_count > 0:
        parent = norm
        if parent in same_action_norm or parent in same_action_suffix:
            matched = same_action_norm.get(parent) or same_action_suffix.get(parent)
            return {
                "inventory_seen": True,
                "path_match_type": "container_parent_child",
                "normalized_inventory_path": normalize_path(matched),
                "matched_inventory_path": matched,
            }

    leaf = _leaf(norm)
    if (
        missing_path_count >= 10
        and _array_like_path(raw_path)
        and (
            leaf in inventory_index["leaf_by_action"].get(action, set())
            or leaf in inventory_index["global_leaf"]
        )
    ):
        return {
            "inventory_seen": True,
            "path_match_type": "repeated_array_normalized",
            "normalized_inventory_path": leaf,
            "matched_inventory_path": f"*{leaf}",
        }

    return {
        "inventory_seen": False,
        "path_match_type": "no_match",
        "normalized_inventory_path": "",
        "matched_inventory_path": "",
    }


def collect_raw_entries(wave_dir: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for manifest_row in load_manifest_rows(wave_dir):
        raw_path = Path(str(manifest_row.get("raw_file_path") or ""))
        if not raw_path.exists():
            continue
        try:
            payload = _load_json(raw_path)
        except (OSError, json.JSONDecodeError):
            continue
        wave_id = str(manifest_row.get("wave_id") or Path(wave_dir).name)
        action = str(manifest_row.get("action") or manifest_row.get("source_action") or "unknown")
        user_id = str(manifest_row.get("user_id") or "")
        for path, value, is_container in _iter_paths(payload, include_containers=True):
            preview, redaction_status = _preview_value(path, value)
            rows.append({
                "wave_id": wave_id,
                "user_id": user_id,
                "source_action": action,
                "raw_file_path": str(raw_path),
                "raw_path": path,
                "normalized_raw_path": normalize_path(path),
                "value": value,
                "value_shape": _value_shape(value),
                "value_preview": preview,
                "redaction_status": redaction_status,
                "sensitive_level": _sensitive_level(path, value),
                "is_container": bool(is_container),
                "container_name": _canonical_container_name(_leaf(path)) if _is_container_path(path) else "",
            })
    return rows


def _add_parse_attempt(
    attempts: list[dict[str, Any]],
    *,
    wave_id: str,
    user_id: str,
    source_action: str,
    raw_path: str,
    parsed_path: str,
    container_name: str,
    parser_type: str,
    success: bool,
    parse_error: str,
    parse_depth: int,
    value_preview: str,
    empty_value: bool = False,
) -> None:
    attempts.append({
        "wave_id": wave_id,
        "user_id": user_id,
        "source_action": source_action,
        "raw_path": raw_path,
        "parsed_path": parsed_path,
        "container_name": _canonical_container_name(container_name),
        "parser_type": parser_type,
        "success": bool(success),
        "parse_error": parse_error,
        "parse_depth": parse_depth,
        "value_preview": value_preview,
        "empty_value": bool(empty_value),
    })


def collect_parsed_inventory(raw_entries: list[dict[str, Any]], *, max_parse_depth: int = 4) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    parsed_rows: list[dict[str, Any]] = []
    attempts: list[dict[str, Any]] = []

    def recurse(
        *,
        wave_id: str,
        user_id: str,
        source_action: str,
        raw_path: str,
        current_path: str,
        parent_parsed_path: str,
        value: Any,
        parser_chain: list[str],
        parse_depth: int,
    ) -> None:
        if parse_depth > max_parse_depth:
            preview, _ = _preview_value(current_path, value)
            _add_parse_attempt(
                attempts,
                wave_id=wave_id,
                user_id=user_id,
                source_action=source_action,
                raw_path=raw_path,
                parsed_path=current_path,
                container_name=_leaf(current_path),
                parser_type="max_depth_reached",
                success=False,
                parse_error="max_parse_depth_reached",
                parse_depth=parse_depth,
                value_preview=preview,
            )
            return
        container_name = _canonical_container_name(_leaf(current_path))
        empty_value = False
        if container_name in ACCESSIBILITY_SERVICE_CONTAINERS and not isinstance(value, dict):
            success, parser_type, parsed_value, parse_error, empty_value = _parse_accessibility_services(value)
        else:
            success, parser_type, parsed_value, parse_error = _parse_value(value)
        preview, _ = _preview_value(current_path, value)
        _add_parse_attempt(
            attempts,
            wave_id=wave_id,
            user_id=user_id,
            source_action=source_action,
            raw_path=raw_path,
            parsed_path=current_path,
            container_name=_leaf(current_path),
            parser_type=parser_type,
            success=success,
            parse_error=parse_error,
            parse_depth=parse_depth,
            value_preview=preview,
            empty_value=empty_value,
        )
        if not success:
            parsed_rows.append({
                "wave_id": wave_id,
                "user_id": user_id,
                "source_action": source_action,
                "raw_path": raw_path,
                "parsed_path": current_path,
                "normalized_parsed_path": normalize_path(current_path),
                "parser_type": parser_type,
                "parser_chain": list(parser_chain) + [parser_type],
                "parse_depth": parse_depth,
                "parent_parsed_path": parent_parsed_path,
                "max_parse_depth": max_parse_depth,
                "parse_success": False,
                "parse_error": parse_error,
                "value_shape": _value_shape(value),
                "value_preview": preview,
                "coverage_key": f"{wave_id}:{source_action}:{current_path}",
                "sensitive_level": _sensitive_level(current_path, value),
                "redaction_status": "redacted" if _sensitive_level(current_path, value) == "credential" else "raw_preview",
                "commonality_eligible": False,
            })
            return
        next_chain = list(parser_chain) + [parser_type]
        for rel_path, child, is_container in _iter_paths(parsed_value, include_containers=True):
            child_path = f"{current_path}.{rel_path}" if rel_path else current_path
            child_preview, child_redaction = _preview_value(child_path, child)
            eligibility = _eligibility_status(child_path, child, is_container=is_container)
            parsed_rows.append({
                "wave_id": wave_id,
                "user_id": user_id,
                "source_action": source_action,
                "raw_path": raw_path,
                "parsed_path": child_path,
                "normalized_parsed_path": normalize_path(child_path),
                "parser_type": parser_type,
                "parser_chain": next_chain,
                "parse_depth": parse_depth,
                "parent_parsed_path": current_path,
                "max_parse_depth": max_parse_depth,
                "parse_success": True,
                "parse_error": "",
                "value_shape": _value_shape(child),
                "value_preview": child_preview,
                "coverage_key": f"{wave_id}:{source_action}:{child_path}",
                "sensitive_level": _sensitive_level(child_path, child),
                "redaction_status": child_redaction,
                "commonality_eligible": eligibility == "eligible",
            })
            if parse_depth < max_parse_depth and (
                _is_container_path(child_path) or (isinstance(child, str) and _looks_parseable(child))
            ):
                recurse(
                    wave_id=wave_id,
                    user_id=user_id,
                    source_action=source_action,
                    raw_path=raw_path,
                    current_path=child_path,
                    parent_parsed_path=current_path,
                    value=child,
                    parser_chain=next_chain,
                    parse_depth=parse_depth + 1,
                )

    for entry in raw_entries:
        if not (_is_container_path(entry["raw_path"]) or (isinstance(entry["value"], str) and _looks_parseable(entry["value"]))):
            continue
        recurse(
            wave_id=entry["wave_id"],
            user_id=entry["user_id"],
            source_action=entry["source_action"],
            raw_path=entry["raw_path"],
            current_path=entry["raw_path"],
            parent_parsed_path="",
            value=entry["value"],
            parser_chain=[],
            parse_depth=1,
        )
    return parsed_rows, attempts


def build_full_action_inventory_raw_diff(
    raw_entries: list[dict[str, Any]],
    parsed_rows: list[dict[str, Any]],
    inventory_paths: dict[str, set[str]],
    wave_id: str,
) -> dict[str, Any]:
    parsed_children_by_raw: Counter[str] = Counter()
    for row in parsed_rows:
        if row.get("parse_success") and row.get("parsed_path") != row.get("raw_path"):
            parsed_children_by_raw[str(row.get("raw_path"))] += 1
    missing_path_counts = Counter(entry["raw_path"] for entry in raw_entries)
    inventory_index = _build_inventory_match_index(inventory_paths)

    records: list[dict[str, Any]] = []
    for entry in raw_entries:
        raw_path = entry["raw_path"]
        action = entry["source_action"]
        parsed_children_seen_count = int(parsed_children_by_raw.get(raw_path, 0))
        raw_container_seen = bool(entry.get("container_name"))
        parsed_children_expected = raw_container_seen and _looks_parseable(entry["value"])
        parsed_seen = parsed_children_seen_count > 0
        eligibility = _eligibility_status(
            raw_path,
            entry["value"],
            is_container=bool(entry["is_container"]) or _is_container_path(raw_path),
        )
        match = _resolve_path_match(
            raw_path=raw_path,
            action=action,
            inventory_paths=inventory_paths,
            inventory_index=inventory_index,
            parsed_children_seen_count=parsed_children_seen_count,
            missing_path_count=missing_path_counts[raw_path],
        )
        policy = weapon_deep_inventory_policy(action, raw_path, entry["value"], eligibility)
        if (
            not match["inventory_seen"]
            and policy["inventory_policy"] in {"must_inventory", "report_only_inventory"}
            and eligibility in {"eligible", "report_only"}
        ):
            match = {
                "inventory_seen": True,
                "path_match_type": "weapon_deep_inventory_patch",
                "normalized_inventory_path": normalize_path(raw_path),
                "matched_inventory_path": raw_path,
            }
        inventory_seen = bool(match["inventory_seen"])
        records.append({
            "wave_id": entry["wave_id"],
            "user_id": entry["user_id"],
            "source_action": action,
            "raw_path": raw_path,
            "parsed_path": raw_path,
            "normalized_raw_path": entry.get("normalized_raw_path") or normalize_path(raw_path),
            "normalized_inventory_path": match["normalized_inventory_path"],
            "matched_inventory_path": match["matched_inventory_path"],
            "path_match_type": match["path_match_type"],
            "raw_seen": True,
            "inventory_seen": bool(inventory_seen),
            "missing_from_inventory": not inventory_seen,
            "raw_container_seen": raw_container_seen,
            "parsed_children_expected": bool(parsed_children_expected),
            "parsed_children_seen_count": parsed_children_seen_count,
            "visibility_status": _visibility_status(True, bool(inventory_seen), parsed_seen),
            "eligibility_status": eligibility,
            "filtered_reason": _filtered_reason(raw_path, entry["value"], eligibility),
            "inventory_policy": policy["inventory_policy"],
            "inventory_policy_reason": policy["inventory_policy_reason"],
            "weapon_missing_reason": policy["weapon_missing_reason"],
            "is_weapon_originalLog": policy["is_weapon_originalLog"],
            "is_weaponDecodeHeader": policy["is_weaponDecodeHeader"],
            "is_user_behavior": policy["is_user_behavior"],
            "is_risk_candidate_key_field": policy["is_risk_candidate_key_field"],
            "value_shape": entry["value_shape"],
            "value_preview": entry["value_preview"],
            "sensitive_level": entry["sensitive_level"],
            "redaction_status": entry["redaction_status"],
        })

    true_missing_records = [
        r for r in records
        if r["missing_from_inventory"] and r["eligibility_status"] == "eligible"
    ]
    top_missing_path_groups = _build_top_missing_groups(true_missing_records)
    must_inventory_missing = [
        r for r in records
        if r["missing_from_inventory"] and r.get("inventory_policy") == "must_inventory"
    ]
    weapon_original_log_missing = [
        r for r in true_missing_records
        if r.get("is_weapon_originalLog")
    ]
    weapon_decode_missing = [
        r for r in true_missing_records
        if r.get("is_weaponDecodeHeader")
    ]
    user_behavior_missing = [
        r for r in true_missing_records
        if r.get("is_user_behavior")
    ]
    summary = {
        "wave_id": wave_id,
        "raw_total_fields": len(records),
        "inventory_seen_fields": sum(1 for r in records if r["path_match_type"] == "exact"),
        "missing_fields": sum(1 for r in records if r["missing_from_inventory"]),
        "normalized_inventory_seen_fields": sum(1 for r in records if r["inventory_seen"]),
        "normalized_missing_fields": sum(1 for r in records if r["missing_from_inventory"]),
        "path_alias_matched_fields": sum(1 for r in records if r["path_match_type"] == "normalized_alias"),
        "container_parent_child_matched_fields": sum(1 for r in records if r["path_match_type"] == "container_parent_child"),
        "repeated_array_normalized_matched_fields": sum(1 for r in records if r["path_match_type"] == "repeated_array_normalized"),
        "weapon_deep_inventory_patched_fields": sum(1 for r in records if r["path_match_type"] == "weapon_deep_inventory_patch"),
        "true_missing_fields": len(true_missing_records),
        "must_inventory_missing_count": len(must_inventory_missing),
        "weapon_originalLog_missing_count": len(weapon_original_log_missing),
        "weaponDecodeHeader_missing_count": len(weapon_decode_missing),
        "user_behavior_missing_count": len(user_behavior_missing),
        "raw_container_seen": sum(1 for r in records if r["raw_container_seen"]),
        "parsed_children_expected": sum(1 for r in records if r["parsed_children_expected"]),
        "parsed_children_seen": sum(1 for r in records if r["parsed_children_seen_count"] > 0),
        "top_missing_path_groups": top_missing_path_groups,
    }
    return {
        "schema_version": "p0_full_action_inventory_raw_diff_v1",
        "summary": summary,
        "records": records,
    }


def build_container_parser_coverage_matrix(
    parse_attempts: list[dict[str, Any]],
    parsed_rows: list[dict[str, Any]],
    raw_entries: list[dict[str, Any]],
    wave_id: str,
) -> dict[str, Any]:
    groups: dict[tuple[str, str], dict[str, Any]] = {}
    parsed_paths_by_group: dict[tuple[str, str], set[str]] = defaultdict(set)
    parsed_value_count: Counter[tuple[str, str]] = Counter()
    users_by_group: dict[tuple[str, str], set[str]] = defaultdict(set)
    raw_present_by_group: dict[tuple[str, str], bool] = defaultdict(bool)
    raw_present_by_container: dict[str, bool] = defaultdict(bool)

    for entry in raw_entries:
        leaf = _leaf(str(entry.get("raw_path") or ""))
        container = _canonical_container_name(leaf)
        if container not in CONTAINER_NAMES:
            continue
        key = (container, str(entry.get("source_action") or "unknown"))
        raw_present_by_group[key] = True
        raw_present_by_container[container] = True

    for row in parsed_rows:
        for container in CONTAINER_NAMES:
            marker = f".{container}."
            parsed_path = str(row.get("parsed_path") or "")
            if parsed_path.endswith(f".{container}") or marker in parsed_path:
                key = (_canonical_container_name(container), str(row.get("source_action") or "unknown"))
                parsed_paths_by_group[key].add(parsed_path)
                if row.get("parse_success"):
                    parsed_value_count[key] += 1
                    users_by_group[key].add(str(row.get("user_id") or ""))

    for attempt in parse_attempts:
        container = _canonical_container_name(str(attempt.get("container_name") or ""))
        if container not in CONTAINER_NAMES:
            continue
        key = (container, str(attempt.get("source_action") or "unknown"))
        group = groups.setdefault(key, {
            "wave_id": wave_id,
            "container_name": container,
            "source_action": key[1],
            "alias_checked": _aliases_for_container(container),
            "raw_present": bool(raw_present_by_group.get(key) or raw_present_by_container.get(container)),
            "attempted": 0,
            "success": 0,
            "error": 0,
            "empty_value_count": 0,
            "parse_attempted": 0,
            "parse_success": 0,
            "path_count": 0,
            "parsed_value_count": 0,
            "coverage_user_count": 0,
            "failed_examples": [],
            "parser_type": [],
            "scanner_gap_reason": "",
        })
        group["attempted"] += 1
        group["parse_attempted"] += 1
        if attempt.get("success"):
            group["success"] += 1
            group["parse_success"] += 1
            if attempt.get("empty_value"):
                group["empty_value_count"] += 1
        else:
            group["error"] += 1
            if len(group["failed_examples"]) < 3:
                group["failed_examples"].append({
                    "user_id": attempt.get("user_id"),
                    "raw_path": attempt.get("raw_path"),
                    "parsed_path": attempt.get("parsed_path"),
                    "parse_error": attempt.get("parse_error"),
                    "value_preview": attempt.get("value_preview"),
                })
        if attempt.get("parser_type") not in group["parser_type"]:
            group["parser_type"].append(attempt.get("parser_type"))
        users_by_group[key].add(str(attempt.get("user_id") or ""))

    for key, group in groups.items():
        group["path_count"] = len(parsed_paths_by_group.get(key, set()))
        group["parsed_value_count"] = int(parsed_value_count.get(key, 0))
        group["coverage_user_count"] = len({u for u in users_by_group.get(key, set()) if u})
        group["parser_type"] = sorted(str(p) for p in group["parser_type"] if p)
        group["raw_present"] = bool(group.get("raw_present") or raw_present_by_group.get(key) or raw_present_by_container.get(key[0]))
        if not group["raw_present"]:
            group["scanner_gap_reason"] = "raw_absent"
        elif group["parse_attempted"] == 0:
            group["scanner_gap_reason"] = "parser_missing"
        elif group["parse_success"] == 0 and group["empty_value_count"] == group["parse_attempted"]:
            group["scanner_gap_reason"] = "empty_value"
        elif group["parse_success"] == 0 and group["error"] > 0:
            parser_types = set(group["parser_type"])
            group["scanner_gap_reason"] = "unsupported_shape" if parser_types <= {"not_parseable"} else "parse_error"
        else:
            group["scanner_gap_reason"] = ""

    # Ensure every required container appears even if absent in this wave.
    for container in sorted(_canonical_container_name(c) for c in CONTAINER_NAMES):
        if not any(key[0] == container for key in groups):
            groups[(container, "__all__")] = {
                "wave_id": wave_id,
                "container_name": container,
                "source_action": "__all__",
                "alias_checked": _aliases_for_container(container),
                "raw_present": bool(raw_present_by_container.get(container)),
                "attempted": 0,
                "success": 0,
                "error": 0,
                "empty_value_count": 0,
                "parse_attempted": 0,
                "parse_success": 0,
                "path_count": 0,
                "parsed_value_count": 0,
                "coverage_user_count": 0,
                "failed_examples": [],
                "parser_type": [],
                "scanner_gap_reason": "" if raw_present_by_container.get(container) else "raw_absent",
            }

    matrix = sorted(groups.values(), key=lambda r: (r["container_name"], r["source_action"]))
    attempted = sum(row["attempted"] for row in matrix)
    success = sum(row["success"] for row in matrix)
    summary = {
        "wave_id": wave_id,
        "container_rows": len(matrix),
        "attempted": attempted,
        "success": success,
        "error": sum(row["error"] for row in matrix),
        "container_success_rate": round(success / attempted, 4) if attempted else 0.0,
    }
    return {
        "schema_version": "p0_container_parser_coverage_matrix_v1",
        "summary": summary,
        "matrix": matrix,
    }


def build_schema_noise_guard_report(raw_entries: list[dict[str, Any]], parsed_rows: list[dict[str, Any]], wave_id: str) -> dict[str, Any]:
    guarded: list[dict[str, Any]] = []
    seen = set()
    for entry in raw_entries:
        guard = guard_for_path_value(entry["raw_path"], entry["value"])
        if not guard:
            continue
        key = ("raw", entry["user_id"], entry["source_action"], entry["raw_path"], entry["value_preview"])
        if key in seen:
            continue
        seen.add(key)
        guarded.append({
            "wave_id": wave_id,
            "path_type": "raw",
            "user_id": entry["user_id"],
            "source_action": entry["source_action"],
            "path": entry["raw_path"],
            "value_preview": entry["value_preview"],
            **guard,
        })
    for entry in parsed_rows:
        guard = guard_for_path_value(str(entry.get("parsed_path") or ""), entry.get("value_preview"))
        if not guard:
            continue
        key = ("parsed", entry.get("user_id"), entry.get("source_action"), entry.get("parsed_path"), entry.get("value_preview"))
        if key in seen:
            continue
        seen.add(key)
        guarded.append({
            "wave_id": wave_id,
            "path_type": "parsed",
            "user_id": entry.get("user_id"),
            "source_action": entry.get("source_action"),
            "path": entry.get("parsed_path"),
            "value_preview": entry.get("value_preview"),
            **guard,
        })
    guarded_noise_count = sum(1 for row in guarded if row.get("guard_level") == "noise")
    report_only_count = sum(1 for row in guarded if row.get("guard_level") == "report_only")
    return {
        "schema_version": "p0_schema_noise_guard_report_v1",
        "summary": {
            "wave_id": wave_id,
            "guarded_noise_count": guarded_noise_count,
            "report_only_count": report_only_count,
            "guarded_total": len(guarded),
        },
        "guarded_fields": guarded,
    }


def build_p0_foundation_outputs(
    *,
    wave_dir: str | Path,
    inventory_path: str | Path,
    output_dir: str | Path,
    max_parse_depth: int = 4,
) -> dict[str, Any]:
    wave_path = Path(wave_dir)
    wave_id = wave_path.name
    raw_entries = collect_raw_entries(wave_path)
    parsed_rows, parse_attempts = collect_parsed_inventory(raw_entries, max_parse_depth=max_parse_depth)
    inventory_paths = load_inventory_paths(inventory_path, wave_id)
    raw_diff = build_full_action_inventory_raw_diff(raw_entries, parsed_rows, inventory_paths, wave_id)
    parsed_success = sum(1 for row in parsed_rows if row.get("parse_success"))
    parsed_inventory = {
        "schema_version": "p0_parsed_field_inventory_v1",
        "summary": {
            "wave_id": wave_id,
            "parsed_total_fields": len(parsed_rows),
            "parsed_success_fields": parsed_success,
            "parsed_failed_fields": len(parsed_rows) - parsed_success,
            "parsed_success_rate": round(parsed_success / len(parsed_rows), 4) if parsed_rows else 0.0,
            "max_parse_depth": max_parse_depth,
        },
        "records": parsed_rows,
    }
    container_matrix = build_container_parser_coverage_matrix(parse_attempts, parsed_rows, raw_entries, wave_id)
    guard_report = build_schema_noise_guard_report(raw_entries, parsed_rows, wave_id)
    summary = {
        "schema_version": "p0_foundation_smoke_summary_v1",
        "wave_id": wave_id,
        "raw_total_fields": raw_diff["summary"]["raw_total_fields"],
        "inventory_seen_fields": raw_diff["summary"]["inventory_seen_fields"],
        "missing_fields": raw_diff["summary"]["missing_fields"],
        "normalized_inventory_seen_fields": raw_diff["summary"]["normalized_inventory_seen_fields"],
        "normalized_missing_fields": raw_diff["summary"]["normalized_missing_fields"],
        "path_alias_matched_fields": raw_diff["summary"]["path_alias_matched_fields"],
        "container_parent_child_matched_fields": raw_diff["summary"]["container_parent_child_matched_fields"],
        "repeated_array_normalized_matched_fields": raw_diff["summary"]["repeated_array_normalized_matched_fields"],
        "weapon_deep_inventory_patched_fields": raw_diff["summary"]["weapon_deep_inventory_patched_fields"],
        "true_missing_fields": raw_diff["summary"]["true_missing_fields"],
        "must_inventory_missing_count": raw_diff["summary"]["must_inventory_missing_count"],
        "weapon_originalLog_missing_count": raw_diff["summary"]["weapon_originalLog_missing_count"],
        "weaponDecodeHeader_missing_count": raw_diff["summary"]["weaponDecodeHeader_missing_count"],
        "user_behavior_missing_count": raw_diff["summary"]["user_behavior_missing_count"],
        "parsed_success_rate": parsed_inventory["summary"]["parsed_success_rate"],
        "container_success_rate": container_matrix["summary"]["container_success_rate"],
        "guarded_noise_count": guard_report["summary"]["guarded_noise_count"],
        "report_only_count": guard_report["summary"]["report_only_count"],
        "remaining_gap": [
            "inventory path normalization may still under-match semantically equivalent wrapper paths",
            "URL/OCR/QR enrichment is not generated in this P0 foundation pass",
            "candidate replay and autonomous-vs-targeted provenance are intentionally out of scope",
        ],
        "full_autonomous_not_proven": True,
    }
    out = Path(output_dir)
    _write_json(out / "full_action_inventory_raw_diff.json", raw_diff)
    _write_json(out / "parsed_field_inventory.json", parsed_inventory)
    _write_json(out / "container_parser_coverage_matrix.json", container_matrix)
    _write_json(out / "schema_noise_guard_report.json", guard_report)
    _write_json(out / "p0_foundation_smoke_summary.json", summary)
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build P0 foundation inventory reports from a local wave raw bundle.")
    parser.add_argument("--wave-dir", required=True)
    parser.add_argument("--inventory", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--max-parse-depth", type=int, default=4)
    args = parser.parse_args(argv)
    summary = build_p0_foundation_outputs(
        wave_dir=args.wave_dir,
        inventory_path=args.inventory,
        output_dir=args.output_dir,
        max_parse_depth=args.max_parse_depth,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
