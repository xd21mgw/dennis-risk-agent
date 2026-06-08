#!/usr/bin/env python3
"""Replay HAR/JSON action responses into Dennis raw-detail flattening stats.

This is a local diagnostic helper, not a case runner. It does not call
platforms. It converts saved HAR/JSON response bodies into the existing
`parsed_body_field_handles` shape, then reuses runtime_case_execution_runner's
raw_detail_flat_table builder to check whether each source exposes enough
field-level facts for L3 commonality.
"""

from __future__ import annotations

import argparse
import base64
import json
from collections import defaultdict
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from runtime_case_execution_runner import (
    build_raw_detail_flat_table,
    build_raw_detail_flat_table_summary,
)


ACTION_PATH_HINTS = [
    ("weapon_device_info", ["/apiv2/riskData"]),
    ("weapon_device_app_list", ["/api/dataReport/getDeviceAppList"]),
    ("weapon_device_location_info", ["/api/dataReport/getLocationInfo"]),
    ("weapon_user_klink_status", ["/api/dataReport/getKlinkStatusByUsers"]),
    ("weapon_inventory", ["/apiv2/graphData"]),
    ("rcp_event_feature_list", ["/v2/rest/event/fastQueryHbase"]),
    ("rcp_event_detail", ["/v2/rest/event/eventList"]),
    ("rcp_event_feature_key_lookup", ["/v2/rest/basicInfo/getFeatureListByKeyWord"]),
    ("login_logs_search", ["login_logs_search", "logSearchModels"]),
    ("archives_user_analysis", ["/v3/user/log/coreLogs/fetch", "/v3/user/analyze/fetch"]),
    ("archives_user_profile", ["/archives/user/home/info", "/archives/user/home/getUserLabel", "/archives/user/home/getUserShopInfo", "/archives/user/risk/info", "/v3/user/risk/info"]),
    ("archives_photo_search", ["archives_photo_search", "/photo/"]),
    ("archives_comment_search", ["archives_comment_search", "/comment/"]),
    ("archives_private_message_search", ["archives_private_message_search", "/message/"]),
    ("archives_user_report_search", ["/v3/user/negative/report", "/v3/user/negative/unInterested"]),
    ("archives_review_logs", ["archives_review_logs", "/review/"]),
    ("archives_punish_status", ["/archives/draco/getPunishStatus"]),
    ("track_analysis_check_data_ready", ["/dp/platform/app/analytics/v2/sequence/checkDataReady"]),
    ("track_analysis_summary", ["/dp/platform/app/analytics/v2/sequence/getDeviceIds", "/dp/platform/app/analytics/v2/sequence/getUseDuration", "/dp/platform/app/analytics/v2/sequence/profile"]),
    ("track_analysis_config_lookup", ["/dp/platform/app/analytics/v2/sequence/config", "/dp/platform/app/analytics/v2/sequence/getLastestDateTime"]),
]

IGNORED_HAR_PATH_PREFIXES = (
    "/rest/wd/common/log/collect/",
    "/kos/",
)

ANCHOR_NAMES = {
    "user_id",
    "userId",
    "device_id",
    "deviceId",
    "did",
    "ip",
    "clientIP",
    "sourceIp",
    "ua",
    "userAgent",
    "appVersion",
    "event_id",
    "eventId",
    "policy_code",
    "policyCode",
    "photo_id",
    "photoId",
    "item_id",
    "itemId",
}

MIN_FIELD_THRESHOLDS = {
    "single_object_wide_field": 50,
    "multi_row_event": 20,
}


def _safe_load_json_text(text: str) -> Any | None:
    text = text.strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def _iter_input_paths(paths: list[str]) -> list[Path]:
    out: list[Path] = []
    for raw in paths:
        path = Path(raw)
        if path.is_dir():
            out.extend(sorted(p for p in path.rglob("*") if p.suffix.lower() in {".har", ".json"}))
        elif path.exists():
            out.append(path)
    return out


def _guess_action(name: str, url: str, body: Any) -> str:
    path = urlparse(url).path if url else ""
    if any(path.startswith(prefix) for prefix in IGNORED_HAR_PATH_PREFIXES):
        return "ignored_telemetry_or_static_asset"
    haystack = f"{name} {path} {json.dumps(body, ensure_ascii=False)[:2000] if body is not None else ''}"
    for action, hints in ACTION_PATH_HINTS:
        if any(hint in haystack for hint in hints):
            return action
    return "unknown_action"


def _extract_har_entries(path: Path, data: dict[str, Any]) -> list[dict[str, Any]]:
    entries = data.get("log", {}).get("entries", [])
    out: list[dict[str, Any]] = []
    for index, entry in enumerate(entries):
        request = entry.get("request", {}) if isinstance(entry, dict) else {}
        response = entry.get("response", {}) if isinstance(entry, dict) else {}
        content = response.get("content", {}) if isinstance(response, dict) else {}
        text = content.get("text")
        if text is None:
            continue
        if content.get("encoding") == "base64":
            try:
                text = base64.b64decode(text).decode("utf-8", errors="replace")
            except Exception:
                continue
        body = _safe_load_json_text(str(text))
        if body is None:
            continue
        url = str(request.get("url") or "")
        action = _guess_action(path.name, url, body)
        if action == "ignored_telemetry_or_static_asset":
            continue
        out.append(
            {
                "source_id": f"{path.stem}_{index}",
                "action": action,
                "url": url,
                "body": body,
            }
        )
    return out


def _extract_json_entries(path: Path, data: Any) -> list[dict[str, Any]]:
    if isinstance(data, dict) and isinstance(data.get("log", {}), dict) and data.get("log", {}).get("entries"):
        return _extract_har_entries(path, data)
    if isinstance(data, dict) and isinstance(data.get("rounds"), list):
        out: list[dict[str, Any]] = []
        for round_index, round_item in enumerate(data.get("rounds", []) or []):
            if not isinstance(round_item, dict):
                continue
            for obs_index, observation in enumerate(round_item.get("mock_current_observations", []) or []):
                if not isinstance(observation, dict):
                    continue
                action = str(observation.get("action") or "unknown_action")
                body: dict[str, Any] = {}
                if isinstance(observation.get("fields"), dict):
                    body.update(observation.get("fields") or {})
                if isinstance(observation.get("records"), list):
                    body["records"] = observation.get("records")
                if isinstance(observation.get("feature_rows"), list):
                    body["feature_rows"] = observation.get("feature_rows")
                if isinstance(observation.get("device_detail_rows"), list):
                    body["device_detail_rows"] = observation.get("device_detail_rows")
                if observation.get("generated_feature_row_count"):
                    body["generated_feature_rows"] = [
                        {"featureKey": f"generated_feature_{i}", "defaultFeatureValue": f"value_{i}"}
                        for i in range(int(observation.get("generated_feature_row_count") or 0))
                    ]
                if observation.get("generated_device_detail_field_count"):
                    body["generated_device_fields"] = {
                        f"generated_device_field_{i}": f"device_value_{i}"
                        for i in range(int(observation.get("generated_device_detail_field_count") or 0))
                    }
                out.append(
                    {
                        "source_id": str(observation.get("source_id") or f"{path.stem}_{round_index}_{obs_index}"),
                        "action": action,
                        "url": "",
                        "body": body,
                    }
                )
        return out
    action = "unknown_action"
    if isinstance(data, dict):
        action = str(data.get("action") or data.get("source_name") or data.get("source") or "")
        body = data.get("body", data.get("response", data.get("data", data)))
    else:
        body = data
    if not action:
        action = _guess_action(path.name, "", body)
    return [{"source_id": path.stem, "action": action, "url": "", "body": body}]


def _flatten_json(value: Any, *, prefix: str = "", record_index: int | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            rows.extend(_flatten_json(child, prefix=path, record_index=record_index))
    elif isinstance(value, list):
        if not value:
            rows.append(
                {
                    "field": prefix or "empty_array",
                    "canonical_field": (prefix or "empty_array").split(".")[-1],
                    "field_path": prefix,
                    "value": [],
                    "record_index": record_index,
                }
            )
        for index, child in enumerate(value):
            child_record_index = index if record_index is None and isinstance(child, dict) else record_index
            rows.extend(_flatten_json(child, prefix=f"{prefix}[{index}]", record_index=child_record_index))
    else:
        field_name = (prefix or "value").replace("]", "").split(".")[-1].split("[")[0]
        rows.append(
            {
                "field": field_name,
                "canonical_field": field_name,
                "field_path": prefix or field_name,
                "value": value,
                "record_index": record_index,
            }
        )
    return rows


def _observation_from_entry(entry: dict[str, Any]) -> dict[str, Any]:
    handles = _flatten_json(entry.get("body"))
    return {
        "source_id": entry.get("source_id"),
        "action": entry.get("action") or "unknown_action",
        "quality_class": "completed",
        "parsed_body_field_handles": handles,
        "observed_records": len({h.get("record_index") for h in handles if h.get("record_index") is not None}) or None,
    }


def _status_for_source(source: dict[str, Any]) -> str:
    shape = str(source.get("source_shape") or "unknown")
    threshold = MIN_FIELD_THRESHOLDS.get(shape)
    if threshold is None:
        return "check_manually"
    if int(source.get("flattened_field_count") or 0) >= threshold:
        return "ok"
    return "P1_under_expanded"


def _direct_action_field_stats(observations: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    stats: dict[str, dict[str, Any]] = {}
    for observation in observations:
        action = str(observation.get("action") or "unknown_action")
        item = stats.setdefault(
            action,
            {
                "entry_count": 0,
                "leaf_row_count": 0,
                "distinct_field_path_count": 0,
                "distinct_field_name_count": 0,
                "record_index_count": 0,
                "_field_paths": set(),
                "_field_names": set(),
                "_record_indexes": set(),
            },
        )
        item["entry_count"] += 1
        for handle in observation.get("parsed_body_field_handles", []) or []:
            item["leaf_row_count"] += 1
            if handle.get("field_path"):
                item["_field_paths"].add(str(handle.get("field_path")))
            if handle.get("canonical_field") or handle.get("field"):
                item["_field_names"].add(str(handle.get("canonical_field") or handle.get("field")))
            if handle.get("record_index") is not None:
                item["_record_indexes"].add(str(handle.get("record_index")))
    clean: dict[str, dict[str, Any]] = {}
    for action, item in stats.items():
        field_path_count = len(item.pop("_field_paths"))
        field_name_count = len(item.pop("_field_names"))
        record_index_count = len(item.pop("_record_indexes"))
        item["distinct_field_path_count"] = field_path_count
        item["distinct_field_name_count"] = field_name_count
        item["record_index_count"] = record_index_count
        source_shape = "unknown"
        if action in {
            "weapon_inventory",
            "weapon_device_info",
            "weapon_device_app_list",
            "weapon_device_location_info",
            "weapon_user_klink_status",
            "rcp_event_feature_list",
            "track_analysis_check_data_ready",
            "track_analysis_summary",
        }:
            source_shape = "single_object_wide_field"
        elif action in {
            "login_logs_search",
            "archives_user_analysis",
            "archives_gallery_photo_list",
            "archives_photo_search",
            "archives_photo_profile",
            "archives_photo_meta",
            "archives_comment_search",
            "archives_livestream_comment_detail",
            "archives_private_message_search",
            "archives_related_users",
            "archives_fans_list",
            "archives_follow_list",
            "archives_user_report_search",
            "archives_negative_report",
            "archives_review_logs",
            "archives_punish_status",
        }:
            source_shape = "multi_row_event"
        threshold = MIN_FIELD_THRESHOLDS.get(source_shape)
        item["source_shape"] = source_shape
        item["feature_count_for_commonality"] = field_path_count
        item["feature_count_status"] = (
            "ok"
            if threshold is not None and field_path_count >= threshold
            else "P1_under_expanded"
            if threshold is not None
            else "check_manually"
        )
        clean[action] = item
    return clean


def run(paths: list[str]) -> dict[str, Any]:
    input_paths = _iter_input_paths(paths)
    entries: list[dict[str, Any]] = []
    parse_errors: list[str] = []
    for path in input_paths:
        try:
            data = json.loads(path.read_text())
        except Exception as exc:
            parse_errors.append(f"{path}:{exc}")
            continue
        entries.extend(_extract_json_entries(path, data))

    observations = [_observation_from_entry(entry) for entry in entries]
    rows = build_raw_detail_flat_table(
        round_id=1,
        sampled_entities=[],
        source_observations=observations,
        strategy_event_feature_row_table=[],
        device_detail_table=[],
    )
    summary = build_raw_detail_flat_table_summary(rows)
    sources = summary.get("sources", []) if isinstance(summary, dict) else []
    by_action: dict[str, dict[str, Any]] = {}
    for source in sources:
        action = str(source.get("source_name") or "unknown_action")
        item = dict(source)
        item["status"] = _status_for_source(item)
        by_action[action] = item

    direct_action_stats = _direct_action_field_stats(observations)

    return {
        "check": "har_action_field_replay_check",
        "input_file_count": len(input_paths),
        "entry_count": len(entries),
        "parse_errors": parse_errors,
        "raw_detail_flat_table_count": len(rows),
        "summary": summary,
        "action_summary": by_action,
        "direct_action_field_stats": direct_action_stats,
        "thresholds": {
            "single_object_wide_field_min": MIN_FIELD_THRESHOLDS["single_object_wide_field"],
            "multi_row_event_min": MIN_FIELD_THRESHOLDS["multi_row_event"],
        },
        "validation_pass": not parse_errors and bool(entries),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Replay saved HAR/JSON responses into raw detail field stats.")
    parser.add_argument("paths", nargs="+", help="HAR/JSON files or directories")
    parser.add_argument("--format", choices=["json"], default="json")
    args = parser.parse_args()
    print(json.dumps(run(args.paths), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
