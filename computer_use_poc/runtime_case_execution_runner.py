#!/usr/bin/env python3
"""Controlled case execution harness for Dennis runtime.

The harness is the shared entry for mother-repo and full-runtime execution
tests. It never calls legacy runners or platform URLs directly. Dry-run mode
builds the source plan and controlled batch payload locally. Live mode is
restricted to a local browser-backed service batch endpoint.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from passthrough_observation_builder import build_safe_observation


REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ORCHESTRATION_CHECK = REPO_ROOT / "computer_use_poc" / "source_orchestration_check.py"
DEFAULT_RECALL_SOURCE = "2,0,1,3"
MILLIS_PER_DAY = 24 * 60 * 60 * 1000
DEFAULT_SCENE_WINDOW_DAYS = 30
LOGIN_LOG_RELIABLE_WINDOW_DAYS = 7
TRACK_READINESS_WINDOW_DAYS = 7
MAX_BROWSER_BACKED_BATCH_SOURCES = 30
SOURCE_ACTION_CHUNK_LIMITS = {
    "login_logs_search": 2,
    "rcp_fast_query_hbase": 5,
    "archives_gallery_photo_list": 10,
    "archives_photo_profile": 10,
    "archives_photo_meta": 10,
}

LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1"}
CREDENTIAL_SECRET_KEYS = {
    "token", "accesstoken", "refreshtoken", "logintoken", "authtoken", "passtoken",
    "session", "sessionid", "cookie", "cookies", "authorization", "authheader",
    "rawauthheader", "password", "passwd", "secret", "credential", "ticket",
}
RISK_ENTITY_TOKEN_KEYS = {
    "tokenid", "tokenstatus", "tokentype", "tokensource", "tokentime",
    "tokencreatetime", "tokengeneratetime", "tokenexpiretime",
}
BODY_KEYS_TO_SUPPRESS = {
    "body",
    "raw_body",
    "response_body",
    "upstream_body",
    "upstream",
    "capped_body",
    "body_snippet",
    "body_excerpt",
    "body_preview",
    "logContent",
    "logcontent",
    "html",
    "raw_payload",
}
STDOUT_SECRET_KEY_FRAGMENTS = (
    "cookie",
    "token",
    "session",
    "header",
    "authorization",
    "password",
)
STDOUT_KEY_ALIASES = {
    "authorization_required": "user_approval_required",
    "requires_user_authorization": "requires_user_approval",
    "next_action_required_authorization": "next_action_requires_user_approval",
}
STDOUT_SECRET_STRING_REPLACEMENTS = {
    "cookie": "credential_secret",
    "token": "credential_secret",
    "session": "credential_state",
    "header": "credential_metadata",
    "authorization": "user_approval",
    "password": "credential_secret",
}
SAFE_BATCH_METADATA_KEYS = (
    "source_id",
    "action",
    "category",
    "source_status",
    "error_type",
    "http_status",
    "content_type",
    "body_present",
    "body_truncated",
    "observed_bytes",
    "elapsed_ms",
    "timeout_ms",
    "timed_out",
    "timeout",
    "raw_body_handling",
    "capped_json_path",
    "observed_records",
    "returned_records",
    "missing_records",
    "missing_body_reason",
    "cap_reason",
    "missing_required_fields",
)


def _normalized_key(key: str) -> str:
    return "".join(ch for ch in key.lower() if ch.isalnum())


RAW_OUTPUT_KEY_NORMALIZED = {
    _normalized_key(key)
    for key in BODY_KEYS_TO_SUPPRESS
}


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


def _is_raw_output_key(key: str) -> bool:
    return _normalized_key(key) in RAW_OUTPUT_KEY_NORMALIZED


def _safe_field_path(path: str | None) -> str | None:
    if not path:
        return None
    normalized = _normalized_key(path)
    if any(raw_key in normalized for raw_key in RAW_OUTPUT_KEY_NORMALIZED):
        return "projected_safe_field_path"
    if any(secret_key in normalized for secret_key in CREDENTIAL_SECRET_KEYS):
        return "projected_safe_field_path"
    return path


@dataclass(frozen=True)
class SourcePlanItem:
    source_id: str
    action: str
    execution_group: str
    depends_on: list[str]
    timeout_class: str
    failure_policy: str
    source_priority: str
    expected_observation: str
    params: dict[str, Any]
    timeout_ms: int
    required_fields: list[str]
    window_policy: str
    window_start_ms: int
    window_end_ms: int

    def to_plan_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "action": self.action,
            "execution_group": self.execution_group,
            "depends_on": self.depends_on,
            "timeout_class": self.timeout_class,
            "failure_policy": self.failure_policy,
            "source_priority": self.source_priority,
            "expected_observation": self.expected_observation,
            "required_fields": self.required_fields,
            "window_policy": self.window_policy,
            "time_window_ms": {
                "start": self.window_start_ms,
                "end": self.window_end_ms,
            },
        }

    def to_batch_source(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "action": self.action,
            "params": self.params,
            "timeout_ms": self.timeout_ms,
        }


def _now_ms() -> int:
    return int(time.time() * 1000)


def _default_scene_window() -> tuple[int, int]:
    end_ms = _now_ms()
    start_ms = end_ms - DEFAULT_SCENE_WINDOW_DAYS * MILLIS_PER_DAY
    return start_ms, end_ms


def _bounded_source_window(scene_start_ms: int, scene_end_ms: int, days: int) -> tuple[int, int]:
    return max(scene_start_ms, scene_end_ms - days * MILLIS_PER_DAY), scene_end_ms


def _compact_case_id(task: str, user_id: str) -> str:
    safe_user = "".join(ch for ch in user_id if ch.isalnum() or ch in {"_", "-"})
    return f"dennis_{task}_{safe_user}"


def _validate_local_base(base_url: str) -> str:
    parsed = urllib.parse.urlparse(base_url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("browser-backed base must use http/https")
    host = parsed.hostname or ""
    if host not in LOCAL_HOSTS:
        raise ValueError("live mode only accepts localhost browser-backed base URL")
    if parsed.query or parsed.fragment:
        raise ValueError("browser-backed base URL must not include query or fragment")
    return base_url.rstrip("/")


def _is_missing(value: Any) -> bool:
    return value is None or value == "" or value == []


def _missing_fields(item: SourcePlanItem) -> list[str]:
    return [field for field in item.required_fields if _is_missing(item.params.get(field))]


def build_ato_single_case_source_plan(
    user_id: str,
    *,
    device_id: str | None,
    window_start_ms: int,
    window_end_ms: int,
    include_abnormal_publish: bool,
    include_same_device: bool,
) -> list[SourcePlanItem]:
    login_start_ms, login_end_ms = _bounded_source_window(
        window_start_ms,
        window_end_ms,
        LOGIN_LOG_RELIABLE_WINDOW_DAYS,
    )
    track_start_ms, track_end_ms = _bounded_source_window(
        window_start_ms,
        window_end_ms,
        TRACK_READINESS_WINDOW_DAYS,
    )
    items = [
        SourcePlanItem(
            source_id="ato_login_logs_search",
            action="login_logs_search",
            execution_group="independent_parallel",
            depends_on=[],
            timeout_class="standard_readonly",
            failure_policy="non_blocking_partial",
            source_priority="P0",
            expected_observation=(
                "recent login/control-chain events, login source/type, device, IP, UA, "
                "and online-window boundary"
            ),
            params={
                "user_id": user_id,
                "from_timestamp": login_start_ms,
                "to_timestamp": login_end_ms,
                "recallSource": DEFAULT_RECALL_SOURCE,
                "max_records": 300,
            },
            timeout_ms=30_000,
            required_fields=["user_id"],
            window_policy="login_logs_reliable_online_window_7d_or_playbook_override",
            window_start_ms=login_start_ms,
            window_end_ms=login_end_ms,
        ),
        SourcePlanItem(
            source_id="ato_archives_user_profile",
            action="archives_user_profile",
            execution_group="independent_parallel",
            depends_on=[],
            timeout_class="auth_sensitive",
            failure_policy="non_blocking_partial",
            source_priority="P0",
            expected_observation="account status, profile baseline, protection state, and archive availability",
            params={
                "user_id": user_id,
                "mode": "archives_user_home_profile",
            },
            timeout_ms=30_000,
            required_fields=["user_id"],
            window_policy="profile_current_state_no_7d_login_window_constraint",
            window_start_ms=window_start_ms,
            window_end_ms=window_end_ms,
        ),
        SourcePlanItem(
            source_id="ato_track_analysis_check_data_ready",
            action="track_analysis_check_data_ready",
            execution_group="independent_parallel",
            depends_on=[],
            timeout_class="short_readiness",
            failure_policy="non_blocking_partial",
            source_priority="P0",
            expected_observation=(
                "front-end activity readiness/provenance; not owner proof and not a risk conclusion"
            ),
            params={
                "device_id": device_id,
                "startTime": track_start_ms,
                "endTime": track_end_ms,
                "appName": "KUAISHOU",
                "product": "KUAISHOU",
                "mode": "track_analysis_data_readiness_precheck",
                "include": 1,
                "pageSize": 100,
                "category": ["active"],
                "event": [],
                "appPlatform": [],
                "metric": "pv",
                "type": "deviceId",
            },
            timeout_ms=15_000,
            required_fields=["device_id", "startTime", "endTime"],
            window_policy="track_readiness_source_window_7d_default_or_explicit_track_window",
            window_start_ms=track_start_ms,
            window_end_ms=track_end_ms,
        ),
        SourcePlanItem(
            source_id="ato_archives_photo_search",
            action="archives_photo_search",
            execution_group="auth_sensitive_serial",
            depends_on=["ato_archives_user_profile"],
            timeout_class="auth_sensitive",
            failure_policy="non_blocking_partial",
            source_priority="P0",
            expected_observation=(
                "recent publish/content handoff, photo_id, publish time, source end, device/IP/UA, "
                "and no_data boundary; photo no_data is not ATO or publish-risk exclusion"
            ),
            params={
                "user_id": user_id,
                "begin": window_start_ms,
                "end": window_end_ms,
                "page": 1,
                "count": 20,
            },
            timeout_ms=30_000,
            required_fields=["user_id"],
            window_policy="archives_scene_window_not_constrained_by_login_logs_7d",
            window_start_ms=window_start_ms,
            window_end_ms=window_end_ms,
        ),
        SourcePlanItem(
            source_id="ato_archives_user_analysis",
            action="archives_user_analysis",
            execution_group="auth_sensitive_serial",
            depends_on=["ato_archives_user_profile"],
            timeout_class="large_response",
            failure_policy="non_blocking_partial",
            source_priority="P0",
            expected_observation=(
                "post-login/account-state/action chain, protection events, and behavior baseline hints"
            ),
            params={
                "user_id": user_id,
                "mode": "focused_login_risk_core_logs",
                "beginTime": window_start_ms,
                "endTime": window_end_ms,
                "pageIndex": 1,
                "pageSize": 50,
                "haveParamAuth": 1,
            },
            timeout_ms=45_000,
            required_fields=["user_id"],
            window_policy="archives_scene_window_not_constrained_by_login_logs_7d",
            window_start_ms=window_start_ms,
            window_end_ms=window_end_ms,
        ),
    ]

    if include_same_device:
        items.append(
            SourcePlanItem(
                source_id="ato_archives_related_users",
                action="archives_related_users",
                execution_group="dependency_serial",
                depends_on=["ato_archives_user_profile"],
                timeout_class="standard_readonly",
                failure_policy="non_blocking_partial",
                source_priority="P0-conditional",
                expected_observation=(
                    "candidate related users for spread analysis; same device is a lead, not a gang conclusion"
                ),
                params={
                    "user_id": user_id,
                    "pageIndex": 1,
                    "pageSize": 50,
                },
                timeout_ms=30_000,
                required_fields=["user_id"],
                window_policy="archives_related_users_current_relation_window_or_explicit_scene_window",
                window_start_ms=window_start_ms,
                window_end_ms=window_end_ms,
            )
        )

    return items


def build_batch_payload(
    case_id: str,
    source_plan: list[SourcePlanItem],
    dry_run: bool,
    *,
    excluded_source_ids: set[str] | None = None,
) -> dict[str, Any]:
    excluded_source_ids = excluded_source_ids or set()
    groups: dict[str, dict[str, Any]] = {}
    for item in source_plan:
        if item.source_id in excluded_source_ids:
            continue
        group = groups.setdefault(
            item.execution_group,
            {
                "group_id": item.execution_group,
                "execution": item.execution_group,
                "sources": [],
            },
        )
        group["sources"].append(item.to_batch_source())

    if "independent_parallel" in groups:
        for group_id in ("auth_sensitive_serial", "dependency_serial"):
            if group_id in groups:
                groups[group_id].setdefault("depends_on", ["independent_parallel"])

    ordered_group_ids = ["independent_parallel", "auth_sensitive_serial", "dependency_serial", "large_response_serial"]
    execution_groups = [groups[group_id] for group_id in ordered_group_ids if group_id in groups]

    return {
        "request_id": case_id,
        "dry_run": dry_run,
        "response_mode": "controlled_batch_passthrough",
        "default_timeout_ms": 30_000,
        "execution_groups": execution_groups,
    }


def validate_batch_payload_contract(payload: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    groups = payload.get("execution_groups")
    if not isinstance(groups, list) or not groups:
        errors.append("execution_groups_required")

    source_ids: set[str] = set()
    supported_groups = {
        "independent_parallel",
        "dependency_serial",
        "large_response_serial",
        "auth_sensitive_serial",
    }
    forbidden_key_parts = {"url", "uri", "href", "path", "endpoint", "raw_body"}

    def scan_for_forbidden(value: Any, path: str) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                lowered = key.lower()
                if _is_credential_secret_key(key) or any(part in lowered for part in forbidden_key_parts):
                    errors.append(f"forbidden_key:{path}.{key}")
                scan_for_forbidden(child, f"{path}.{key}")
        elif isinstance(value, list):
            for index, child in enumerate(value):
                scan_for_forbidden(child, f"{path}[{index}]")

    for group in groups if isinstance(groups, list) else []:
        if not isinstance(group, dict):
            errors.append("execution_group_must_be_object")
            continue
        execution = group.get("execution")
        if execution not in supported_groups:
            errors.append(f"unsupported_execution_group:{execution}")
        sources = group.get("sources")
        if not isinstance(sources, list) or not sources:
            errors.append(f"group_sources_required:{group.get('group_id')}")
            continue
        for source in sources:
            if not isinstance(source, dict):
                errors.append("source_must_be_object")
                continue
            source_id = source.get("source_id")
            action = source.get("action")
            if not source_id or not action:
                errors.append("source_id_and_action_required")
            if source_id in source_ids:
                errors.append(f"duplicate_source_id:{source_id}")
            source_ids.add(str(source_id))
            params = source.get("params")
            if not isinstance(params, dict):
                errors.append(f"params_required:{source_id}")
            scan_for_forbidden(source, f"source:{source_id}")

    return {
        "valid": not errors,
        "errors": errors,
        "contract": "browser_backed_actions_batch_v1",
        "endpoint": "/actions/batch",
        "manual_curl_fallback_allowed": False,
    }


def run_orchestration_check(task: str, entity_count: int) -> dict[str, Any]:
    if not SOURCE_ORCHESTRATION_CHECK.exists():
        return {"status": "skipped", "reason": "source_orchestration_check_missing"}

    check_task_type = "ATO" if task == "ato_single_case" else task
    cmd = [
        sys.executable,
        str(SOURCE_ORCHESTRATION_CHECK),
        "--task-type",
        check_task_type,
        "--entity-count",
        str(entity_count),
        "--output-context",
        "partial_evidence_card",
        "--format",
        "json",
    ]
    if task == "ato_single_case":
        cmd.append("--ato-single-case")
    try:
        completed = subprocess.run(cmd, check=False, capture_output=True, text=True, timeout=15)
    except subprocess.TimeoutExpired:
        return {"status": "timeout", "command": "source_orchestration_check.py"}

    try:
        payload = json.loads(completed.stdout) if completed.stdout.strip() else {}
    except json.JSONDecodeError:
        payload = {"raw_stdout_present": bool(completed.stdout.strip())}

    return {
        "status": "completed" if completed.returncode == 0 else "failed",
        "returncode": completed.returncode,
        "command": "source_orchestration_check.py",
        "task_type_used": check_task_type,
        "result": payload,
    }


def sanitize_for_output(value: Any) -> Any:
    if isinstance(value, dict):
        clean: dict[str, Any] = {}
        for key, item in value.items():
            lowered = key.lower()
            if _is_credential_secret_key(key) or _is_raw_output_key(key):
                continue
            if lowered in BODY_KEYS_TO_SUPPRESS and isinstance(item, (str, bytes, dict, list)):
                continue
            clean[key] = sanitize_for_output(item)
        return clean
    if isinstance(value, list):
        return [sanitize_for_output(item) for item in value]
    return value


def _safe_stdout_key(key: str) -> str | None:
    alias = STDOUT_KEY_ALIASES.get(key)
    if alias:
        return alias
    normalized = _normalized_key(key)
    if normalized in RAW_OUTPUT_KEY_NORMALIZED or _is_raw_output_key(key):
        return None
    if any(fragment in normalized for fragment in STDOUT_SECRET_KEY_FRAGMENTS):
        return None
    return key


def _safe_stdout_string(value: str) -> str:
    normalized = _normalized_key(value)
    if any(raw_key in normalized for raw_key in RAW_OUTPUT_KEY_NORMALIZED):
        return "projected_safe_reference"
    safe = value
    for fragment, replacement in STDOUT_SECRET_STRING_REPLACEMENTS.items():
        safe = re.sub(re.escape(fragment), replacement, safe, flags=re.IGNORECASE)
    return safe


def project_safe_stdout_value(value: Any) -> Any:
    if isinstance(value, dict):
        clean: dict[str, Any] = {}
        for key, item in value.items():
            safe_key = _safe_stdout_key(str(key))
            if safe_key is None:
                continue
            clean[safe_key] = project_safe_stdout_value(item)
        return clean
    if isinstance(value, list):
        return [project_safe_stdout_value(item) for item in value]
    if isinstance(value, str):
        return _safe_stdout_string(value)
    return value


def build_safe_stdout_result(result: dict[str, Any]) -> dict[str, Any]:
    safe_result = project_safe_stdout_value(result)
    if not isinstance(safe_result, dict):
        return {
            "schema_version": "runtime_case_execution_result_v1",
            "stdout_projection": {
                "applied": True,
                "raw_passthrough_omitted": True,
                "projection_error": "non_mapping_result",
            },
        }
    projection = {
        "applied": True,
        "scope": "final_stdout_and_output_json",
        "raw_passthrough_omitted": True,
        "body_sections_omitted": True,
        "credential_like_values_omitted": True,
        "preserves": [
            "source_status",
            "quality_class",
            "response_limited",
            "record_counts",
            "source_quality",
            "missing_evidence",
            "orchestration_artifacts_summary",
        ],
    }
    existing_projection = safe_result.get("stdout_projection")
    if isinstance(existing_projection, dict):
        existing_projection.update(projection)
    else:
        safe_result["stdout_projection"] = projection
    return safe_result


def _normalized_source_status(row: dict[str, Any], quality_class: str) -> str:
    if quality_class == "partial" and _row_has_large_response(row):
        return "partial"
    return str(row.get("source_status") or row.get("category") or quality_class)


def _source_status_reason(row: dict[str, Any], quality_class: str) -> str:
    if quality_class == "partial" and _row_has_large_response(row):
        return "response_limited"
    return str(row.get("error_type") or row.get("source_status") or row.get("category") or quality_class)


def build_safe_source_row_summary(row: dict[str, Any], source_payload: dict[str, Any] | None = None) -> dict[str, Any]:
    merged = _merge_row_cap_metadata(row, source_payload or {})
    quality_class = classify_source(merged)
    response_limited = quality_class == "partial" and _row_has_large_response(merged)
    cap_metadata_keys = ("capped_json_path", "observed_records", "returned_records", "missing_records")
    cap_metadata_available = any(merged.get(key) is not None for key in cap_metadata_keys)
    summary: dict[str, Any] = {
        "source_id": merged.get("source_id"),
        "action": merged.get("action"),
        "quality_class": quality_class,
        "source_status": _normalized_source_status(merged, quality_class),
        "reason": _source_status_reason(merged, quality_class),
        "response_limited": response_limited,
        "safe_summary_only": True,
        "raw_passthrough_omitted": True,
    }
    for key in SAFE_BATCH_METADATA_KEYS:
        if key in {"source_status", "category", "error_type"}:
            continue
        if key in merged and not _is_credential_secret_key(key) and not _is_raw_output_key(key):
            summary[key] = sanitize_for_output(merged.get(key))
    if response_limited:
        summary["partial_subtype"] = "response_limited"
        summary["remaining_records_not_parsed"] = int(merged.get("missing_records") or 0)
        summary["cap_metadata_status"] = (
            "available_from_safe_projection" if cap_metadata_available else "unavailable_from_current_projection"
        )
        if not cap_metadata_available:
            summary["cap_metadata_reason"] = "not_exposed_by_safe_summary"
    return summary


def _source_quality_summary_for_output(source_quality_matrix: dict[str, Any] | None) -> dict[str, Any]:
    if not source_quality_matrix:
        return {}
    buckets = source_quality_matrix.get("buckets", {})
    return {
        "completed": list(buckets.get("completed", [])),
        "partial": list(buckets.get("partial", [])),
        "blocked": list(buckets.get("blocked", [])),
        "timeout": list(buckets.get("timeout", [])),
        "no_data": list(buckets.get("no_data", [])),
        "auth_failed": list(buckets.get("auth_failed", [])),
        "parse_error": list(buckets.get("parse_error", [])),
        "planned": list(buckets.get("planned", [])),
        "partial_reasons": [
            {
                "source_id": row.get("source_id"),
                "action": row.get("action"),
                "reason": row.get("reason") or row.get("source_status"),
                "remaining_records_not_parsed": row.get("remaining_records_not_parsed"),
            }
            for row in source_quality_matrix.get("per_source", [])
            if row.get("quality_class") == "partial"
        ],
    }


def build_safe_batch_summary(
    batch_result: dict[str, Any],
    source_quality_matrix: dict[str, Any] | None = None,
) -> dict[str, Any]:
    raw_rows_by_id = _rows_by_source_id_from_batch(batch_result)
    transport_rows = normalize_mapping_or_list(batch_result.get("transport_status_matrix"))
    source_rows = rows_from_source_results(batch_result.get("source_results"))
    if not transport_rows:
        transport_rows = source_rows
    seen: set[str] = set()
    safe_rows: list[dict[str, Any]] = []
    for row in transport_rows:
        if not isinstance(row, dict):
            continue
        source_id = str(row.get("source_id") or "unknown_source")
        seen.add(source_id)
        safe_rows.append(build_safe_source_row_summary(row, raw_rows_by_id.get(source_id, {})))
    for row in source_rows:
        if not isinstance(row, dict):
            continue
        source_id = str(row.get("source_id") or "unknown_source")
        if source_id in seen:
            continue
        safe_rows.append(build_safe_source_row_summary(row, raw_rows_by_id.get(source_id, {})))
    safe_by_id = {
        str(row.get("source_id") or f"source_{index}"): row
        for index, row in enumerate(safe_rows, start=1)
    }
    classifications = build_classifications(safe_rows)
    return {
        "ok": batch_result.get("ok"),
        "response_mode": batch_result.get("response_mode"),
        "batch_status": batch_result.get("batch_status"),
        "scheduler": batch_result.get("scheduler"),
        "source_results": safe_by_id,
        "transport_status_matrix": safe_rows,
        "classifications": classifications,
        "source_quality": _source_quality_summary_for_output(source_quality_matrix),
        "safe_projection": {
            "applied": True,
            "raw_passthrough_omitted": True,
            "raw_body_not_retained_in_stdout": True,
            "secret_values_omitted": True,
            "body_sections_omitted": True,
            "cleanup_required_for_raw_debug_files": True,
        },
        "safety": {
            "raw_body_returned": False,
            "legacy_runner_fallback_attempted": False,
            "single_action_freeform_attempted": False,
            "manual_batch_curl_fallback_allowed": False,
        },
    }


def build_dry_run_batch_result(source_plan: list[SourcePlanItem]) -> dict[str, Any]:
    transport_rows: dict[str, dict[str, Any]] = {}
    source_results: dict[str, dict[str, Any]] = {}
    missing_or_failed_sources: list[dict[str, Any]] = []

    for item in source_plan:
        missing = _missing_fields(item)
        if missing:
            category = "blocked"
            source_status = "missing_required_fields"
            error_type = "missing_required_fields"
            missing_or_failed_sources.append(
                {
                    "source_id": item.source_id,
                    "action": item.action,
                    "category": category,
                    "source_status": source_status,
                    "error_type": error_type,
                    "missing_required_fields": missing,
                }
            )
        else:
            category = "planned"
            source_status = "planned_not_executed"
            error_type = None

        row = {
            "source_id": item.source_id,
            "action": item.action,
            "category": category,
            "source_status": source_status,
            "error_type": error_type,
            "http_status": None,
            "content_type": None,
            "body_present": False,
            "body_truncated": False,
            "observed_bytes": 0,
            "elapsed_ms": 0,
            "timeout_ms": item.timeout_ms,
            "transport_error": None,
            "platform_error": None,
            "invalid_params": bool(missing),
            "timed_out": False,
            "raw_body_handling": "not_requested_in_dry_run",
            "missing_required_fields": missing,
        }
        transport_rows[item.source_id] = row
        source_results[item.source_id] = {
            "source_id": item.source_id,
            "action": item.action,
            "category": category,
            "source_status": source_status,
            "transport": row,
        }

    return {
        "ok": True,
        "response_mode": "controlled_batch_passthrough",
        "batch_status": "dry_run_planned",
        "scheduler": "controlled_parallel",
        "source_results": source_results,
        "transport_status_matrix": transport_rows,
        "classifications": build_classifications(transport_rows),
        "missing_or_failed_sources": missing_or_failed_sources,
        "safety": {
            "raw_body_returned": False,
            "legacy_runner_fallback_attempted": False,
            "single_action_freeform_attempted": False,
        },
    }


def build_classifications(transport_rows: dict[str, dict[str, Any]] | list[dict[str, Any]]) -> dict[str, list[str]]:
    rows = list(transport_rows.values()) if isinstance(transport_rows, dict) else transport_rows
    classifications: dict[str, list[str]] = {
        "completed": [],
        "no_data": [],
        "partial": [],
        "auth_failed": [],
        "blocked": [],
        "timeout": [],
        "parse_error": [],
        "planned": [],
    }
    for row in rows:
        if not isinstance(row, dict):
            continue
        source_id = str(row.get("source_id") or "unknown_source")
        classification = classify_source(row)
        classifications.setdefault(classification, []).append(source_id)
    return classifications


def call_browser_backed_batch(base_url: str, payload: dict[str, Any]) -> dict[str, Any]:
    base = _validate_local_base(base_url)
    endpoint = f"{base}/actions/batch"
    request_options = {"headers": {"content-type": "application/json"}}
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        **request_options,
    )
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    source_timeouts = [
        int(source.get("timeout_ms") or 0)
        for group in payload.get("execution_groups", [])
        if isinstance(group, dict)
        for source in group.get("sources", [])
        if isinstance(source, dict)
    ]
    request_timeout = min(120, max(35, (max(source_timeouts or [30_000]) // 1000) + 20))
    try:
        with opener.open(request, timeout=request_timeout) as response:
            data = response.read()
    except urllib.error.HTTPError as exc:
        body = exc.read() if hasattr(exc, "read") else b""
        error_payload: dict[str, Any] = {}
        if body:
            try:
                error_payload = sanitize_for_output(json.loads(body.decode("utf-8")))
            except (UnicodeDecodeError, json.JSONDecodeError):
                error_payload = {"body_present": True, "body_parse_error": "non_json_error_body"}
        return build_harness_error_result(
            source_status="batch_contract_rejected",
            error_type=getattr(exc, "code", None) or "http_error",
            detail=error_payload,
            http_status=getattr(exc, "code", None),
        )
    except urllib.error.URLError as exc:
        return build_harness_error_result(
            source_status="service_unavailable",
            error_type=type(exc).__name__,
            detail={"reason": sanitize_for_output(str(exc.reason) if hasattr(exc, "reason") else str(exc))},
        )

    try:
        return json.loads(data.decode("utf-8"))
    except json.JSONDecodeError:
        return build_harness_error_result(
            source_status="parse_error",
            error_type="non_json_batch_response",
            detail={"body_present": bool(data)},
            category="parse_error",
        )


def build_harness_error_result(
    *,
    source_status: str,
    error_type: Any,
    detail: dict[str, Any],
    category: str = "blocked",
    http_status: int | None = None,
) -> dict[str, Any]:
    error_text = str(error_type)
    row = {
        "source_id": "browser_backed_batch",
        "action": "controlled_batch",
        "category": category,
        "source_status": source_status,
        "error_type": error_text,
        "http_status": http_status,
        "body_present": False,
        "body_truncated": False,
        "observed_bytes": 0,
        "elapsed_ms": None,
        "transport_error": error_text,
        "platform_error": None,
        "invalid_params": source_status == "batch_contract_rejected",
        "timeout": "timeout" in error_text.lower(),
        "raw_body_handling": "suppressed",
    }
    return {
        "ok": False,
        "response_mode": "controlled_batch_passthrough",
        "batch_status": "harness_error",
        "harness_error": {
            "source_status": source_status,
            "error_type": error_text,
            "detail": detail,
            "manual_batch_curl_fallback_allowed": False,
            "next_action": "return_structured_source_gap_or_retry_harness; do_not_manual_curl_actions_batch",
        },
        "source_results": {"browser_backed_batch": {"source_id": "browser_backed_batch", "transport": row}},
        "transport_status_matrix": {"browser_backed_batch": row},
        "classifications": build_classifications({"browser_backed_batch": row}),
        "missing_or_failed_sources": [row],
        "safety": {
            "legacy_runner_fallback_attempted": False,
            "manual_batch_curl_fallback_allowed": False,
            "single_action_freeform_attempted": False,
        },
    }


def _http_status_int(row: dict[str, Any]) -> int | None:
    try:
        value = row.get("http_status")
        if value is None or value == "":
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def _success_http_with_body(row: dict[str, Any]) -> bool:
    http_status = _http_status_int(row)
    return http_status is not None and 200 <= http_status < 300 and row.get("body_present") is True


def _explicit_auth_failure(row: dict[str, Any]) -> bool:
    http_status = _http_status_int(row)
    status = str(row.get("source_status") or "").lower()
    error_type = str(row.get("error_type") or "").lower()
    platform_error = str(row.get("platform_error") or "").lower()
    return (
        http_status in {401, 403}
        or row.get("auth_redirect_detected") is True
        or str(row.get("api_code")) == "302"
        or http_status == 302
        or "auth_failed" in status
        or "auth_failed" in error_type
        or "permission_denied" in status
        or "permission_denied" in error_type
        or "permission_denied" in platform_error
    )


def _auth_flow_not_completed_gap(row: dict[str, Any]) -> bool:
    status = str(row.get("source_status") or "").lower()
    error_type = str(row.get("error_type") or "").lower()
    platform_error = str(row.get("platform_error") or "").lower()
    content_type = str(row.get("content_type") or "").lower()
    raw_body_handling = str(row.get("raw_body_handling") or "").lower()
    return (
        "unexpected_html_response" in error_type
        or "unexpected_html_response" in status
        or "html_response" in error_type
        or "html_response" in status
        or "auth_flow_not_completed" in error_type
        or "auth_flow_not_completed" in status
        or "auth_session_issue" in error_type
        or "auth_session_issue" in status
        or "sso" in platform_error
        or (
            row.get("body_present") is True
            and ("html" in content_type or raw_body_handling == "html_omitted")
        )
    )


def _row_has_empty_hint(row: dict[str, Any]) -> bool:
    empty_keys = (
        "empty_result",
        "no_data_hint",
        "result_empty",
        "is_empty_result",
        "has_records",
    )
    for key in empty_keys:
        if key in row:
            value = row.get(key)
            if key == "has_records":
                return value is False
            return bool(value)
    for key in ("totalCount", "total_count", "result_count", "resultArrayLength", "result_array_length", "count"):
        if key in row:
            try:
                return int(row.get(key) or 0) == 0
            except (TypeError, ValueError):
                continue
    return False


def derive_transport_interpretation(row: dict[str, Any]) -> str:
    """Classify transport before business interpretation.

    The browser-backed service is pure passthrough: capped/suppressed bodies
    are expected transport behavior and are not auth or body-missing evidence.
    """
    status = str(row.get("source_status") or row.get("category") or "").lower()
    error_type = str(row.get("error_type") or "").lower()
    transport_error = str(row.get("transport_error") or "").lower()
    platform_error = str(row.get("platform_error") or "").lower()

    if _auth_flow_not_completed_gap(row):
        return "auth_flow_not_completed_in_bound_context"
    if _success_http_with_body(row) and _row_has_large_response(row):
        return "transport_success_partial_observation_response_too_large"
    if _success_http_with_body(row) and _row_has_empty_hint(row):
        return "transport_success_likely_no_data"
    if _success_http_with_body(row):
        if str(row.get("raw_body_handling") or "").lower() in {"suppressed", "capped", "metadata_only"}:
            return "transport_success_body_suppressed"
        return "transport_success"
    if row.get("timed_out") or row.get("timeout") or "timeout" in status or "timeout" in error_type or "timeout" in transport_error:
        return "timeout"
    if _explicit_auth_failure(row):
        return "auth_failed"
    if row.get("invalid_params") or "missing_required" in status or "invalid" in status or "invalid" in error_type:
        return "invalid_params"
    if "parse" in status or "parse" in error_type:
        return "parse_error"
    if "no_data" in status or "empty" in status:
        return "likely_no_data"
    if row.get("body_truncated") or "response_too_large" in status or "too_large" in error_type or "too_large" in platform_error:
        return "partial_observation_available_response_too_large"
    if "planned" in status or "planned" in str(row.get("category") or "").lower():
        return "planned_not_executed"
    if transport_error or "network_error" in status or "network_error" in error_type:
        return "network_error"
    if platform_error:
        return "platform_error"
    if row.get("body_present") is False:
        return "body_not_present"
    if "completed" in status or "completed" in str(row.get("category") or "").lower():
        return "completed_transport"
    return "blocked_or_unknown"


def classify_source(row: dict[str, Any]) -> str:
    interpretation = derive_transport_interpretation(row)
    if interpretation == "transport_success_partial_observation_response_too_large":
        return "partial"
    if interpretation == "transport_success_likely_no_data":
        return "no_data"
    if interpretation in {"transport_success_body_suppressed", "transport_success"}:
        return "completed"
    status = str(row.get("source_status") or row.get("category") or "").lower()
    category = str(row.get("category") or "").lower()
    error_type = str(row.get("error_type") or "").lower()
    platform_error = str(row.get("platform_error") or "").lower()
    transport_error = str(row.get("transport_error") or "").lower()

    if _auth_flow_not_completed_gap(row):
        return "auth_failed"
    if row.get("timed_out") or row.get("timeout") or "timeout" in status or "timeout" in error_type or "timeout" in transport_error:
        return "timeout"
    if _explicit_auth_failure(row):
        return "auth_failed"
    if row.get("invalid_params") or "missing_required" in status or "invalid" in status:
        return "blocked"
    if "parse" in status or "parse" in error_type:
        return "parse_error"
    if "no_data" in status or "empty" in status:
        return "no_data"
    if row.get("body_truncated") or "response_too_large" in status or "too_large" in error_type or "too_large" in platform_error:
        return "partial"
    if "partial" in status or "partial" in category:
        return "partial"
    if "completed" in status or "completed" in category:
        return "completed"
    if "planned" in status or "planned" in category:
        return "planned"
    if "blocked" in status or "blocked" in category or "unavailable" in status or platform_error:
        return "blocked"
    return "blocked"


def normalize_mapping_or_list(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, dict):
        rows = []
        for key, item in value.items():
            if isinstance(item, dict):
                row = dict(item)
                row.setdefault("source_id", key)
                rows.append(row)
        return rows
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    return []


def rows_from_source_results(value: Any) -> list[dict[str, Any]]:
    rows = []
    for item in normalize_mapping_or_list(value):
        transport = item.get("transport")
        if isinstance(transport, dict):
            row = dict(transport)
            row.setdefault("source_id", item.get("source_id"))
            row.setdefault("action", item.get("action"))
            rows.append(row)
            continue
        rows.append(item)
    return rows


ROW_CAP_METADATA_KEYS = {
    "capped_json_path",
    "observed_records",
    "returned_records",
    "missing_records",
    "missing_body_reason",
    "cap_reason",
}


def _row_cap_metadata_sources(source_payload: dict[str, Any]) -> list[dict[str, Any]]:
    sources = [source_payload]
    upstream = source_payload.get("upstream")
    if isinstance(upstream, dict):
        sources.append(upstream)
    source_result = source_payload.get("source_result")
    if isinstance(source_result, dict):
        sources.append(source_result)
        nested_upstream = source_result.get("upstream")
        if isinstance(nested_upstream, dict):
            sources.append(nested_upstream)
        transport = source_result.get("transport")
        if isinstance(transport, dict):
            sources.append(transport)
    transport = source_payload.get("transport")
    if isinstance(transport, dict):
        sources.append(transport)
    return sources


def _merge_row_cap_metadata(row: dict[str, Any], source_payload: dict[str, Any]) -> dict[str, Any]:
    merged = dict(row)
    for candidate in _row_cap_metadata_sources(source_payload):
        if not isinstance(candidate, dict):
            continue
        if not (candidate.get("raw_body_handling") == "json_array_capped" or candidate.get("capped_json_path")):
            continue
        merged.setdefault("raw_body_handling", candidate.get("raw_body_handling"))
        merged.setdefault("response_too_large", candidate.get("response_too_large"))
        for key in ROW_CAP_METADATA_KEYS:
            if key in candidate and key not in merged:
                merged[key] = candidate[key]
    return merged


def merge_source_quality(source_plan: list[SourcePlanItem], batch_result: dict[str, Any]) -> dict[str, Any]:
    plan_by_id = {item.source_id: item for item in source_plan}
    rows = normalize_mapping_or_list(batch_result.get("transport_status_matrix"))
    source_result_rows = rows_from_source_results(batch_result.get("source_results"))
    if not rows:
        rows = source_result_rows
    else:
        seen_row_ids = {str(row.get("source_id") or "") for row in rows if isinstance(row, dict)}
        rows.extend(
            row
            for row in source_result_rows
            if isinstance(row, dict) and str(row.get("source_id") or "") not in seen_row_ids
        )
    if not rows:
        rows = normalize_mapping_or_list(batch_result.get("missing_or_failed_sources"))
    if not rows:
        classifications = batch_result.get("classifications")
        if isinstance(classifications, dict):
            for category, source_ids in classifications.items():
                if not isinstance(source_ids, list):
                    continue
                for source_id in source_ids:
                    item = plan_by_id.get(str(source_id))
                    rows.append(
                        {
                            "source_id": str(source_id),
                            "action": item.action if item else None,
                            "category": category,
                            "source_status": category,
                        }
                    )

    buckets: dict[str, list[str]] = {
        "completed": [],
        "no_data": [],
        "partial": [],
        "auth_failed": [],
        "blocked": [],
        "timeout": [],
        "parse_error": [],
        "planned": [],
    }
    per_source: list[dict[str, Any]] = []

    raw_rows_by_id = _rows_by_source_id_from_batch(batch_result)
    seen: set[str] = set()
    for row in rows:
        source_id = str(row.get("source_id") or "unknown_source")
        row = _merge_row_cap_metadata(row, raw_rows_by_id.get(source_id, {}))
        seen.add(source_id)
        item = plan_by_id.get(source_id)
        transport_interpretation = derive_transport_interpretation(row)
        classification = classify_source(row)
        buckets.setdefault(classification, []).append(source_id)

        notes: list[str] = []
        if "transport_success" in transport_interpretation:
            notes.append("transport_success")
        if transport_interpretation == "transport_success_body_suppressed":
            notes.append("raw_body_suppressed_not_body_missing")
        if transport_interpretation == "transport_success_likely_no_data":
            notes.append("likely_no_data_not_risk_exclusion")
        if row.get("body_truncated"):
            notes.append("partial_observation_available")
        if _row_has_large_response(row):
            notes.extend(["partial_observation_available", "response_too_large_not_login_evidence"])
        if str(row.get("raw_body_handling") or "") == "json_array_capped":
            notes.append("partial_login_log_parsed_from_json_array_capped")
        if int(row.get("missing_records") or 0) > 0:
            notes.append("login_log_incomplete")
        if str(row.get("cap_reason") or "") == "byte_limit":
            notes.append("byte_limit_partial_source")
        if transport_interpretation == "auth_flow_not_completed_in_bound_context":
            notes.extend(
                [
                    "auth_flow_not_completed_in_bound_context",
                    "html_response_not_business_json",
                    "missing_evidence_not_counter_evidence",
                ]
            )
        if classification == "no_data":
            notes.append("no_data_not_risk_exclusion")
        if classification in {"blocked", "timeout", "parse_error", "auth_failed"}:
            notes.append("missing_evidence_not_counter_evidence")
        if classification == "planned":
            notes.append("dry_run_not_platform_evidence")
        normalized_status = _normalized_source_status(row, classification)
        status_reason = _source_status_reason(row, classification)
        response_limited = classification == "partial" and _row_has_large_response(row)
        remaining_records_not_parsed = int(row.get("missing_records") or 0) if response_limited else 0

        per_source.append(
            {
                "source_id": source_id,
                "action": row.get("action") or (item.action if item else None),
                "quality_class": classification,
                "source_status": normalized_status,
                "raw_source_status": row.get("source_status"),
                "reason": status_reason,
                "error_type": row.get("error_type"),
                "http_status": row.get("http_status"),
                "body_present": row.get("body_present"),
                "body_truncated": row.get("body_truncated"),
                "observed_bytes": row.get("observed_bytes"),
                "timeout_ms": row.get("timeout_ms"),
                "transport_error": row.get("transport_error"),
                "platform_error": row.get("platform_error"),
                "invalid_params": row.get("invalid_params"),
                "raw_body_handling": row.get("raw_body_handling"),
                "capped_json_path": row.get("capped_json_path"),
                "observed_records": row.get("observed_records"),
                "returned_records": row.get("returned_records"),
                "missing_records": row.get("missing_records"),
                "remaining_records_not_parsed": remaining_records_not_parsed,
                "missing_body_reason": row.get("missing_body_reason"),
                "cap_reason": row.get("cap_reason"),
                "cap_metadata_status": (
                    "available_from_safe_projection"
                    if response_limited
                    and any(row.get(key) is not None for key in ("capped_json_path", "observed_records", "returned_records", "missing_records"))
                    else "unavailable_from_current_projection" if response_limited else None
                ),
                "cap_metadata_reason": (
                    "not_exposed_by_safe_summary"
                    if response_limited
                    and not any(row.get(key) is not None for key in ("capped_json_path", "observed_records", "returned_records", "missing_records"))
                    else None
                ),
                "response_limited": response_limited,
                "partial_subtype": "response_limited" if response_limited else None,
                "missing_required_fields": row.get("missing_required_fields", []),
                "transport_interpretation": transport_interpretation,
                "failure_policy": item.failure_policy if item else "non_blocking_partial",
                "boundary_notes": unique_strings(notes),
                "legacy_runner_fallback_attempted": False,
                "manual_batch_curl_fallback_attempted": False,
            }
        )

    for item in source_plan:
        if item.source_id in seen:
            continue
        buckets["blocked"].append(item.source_id)
        per_source.append(
            {
                "source_id": item.source_id,
                "action": item.action,
                "quality_class": "blocked",
                "source_status": "not_returned_by_batch",
                "error_type": "missing_transport_status",
                "failure_policy": item.failure_policy,
                "boundary_notes": ["missing_evidence_not_counter_evidence"],
                "legacy_runner_fallback_attempted": False,
                "manual_batch_curl_fallback_attempted": False,
            }
        )

    return {
        "generated_by": "dennis_runtime_case_execution_runner",
        "service_source_quality_dependency": False,
        "buckets": buckets,
        "per_source": per_source,
    }


def build_missing_evidence(source_quality_matrix: dict[str, Any]) -> list[dict[str, Any]]:
    missing: list[dict[str, Any]] = []
    for row in source_quality_matrix["per_source"]:
        quality = row["quality_class"]
        if quality == "completed":
            continue
        reason = row.get("reason") or row.get("error_type") or row.get("source_status") or quality
        item = {
            "source_id": row["source_id"],
            "action": row.get("action"),
            "quality_class": quality,
            "reason": reason,
            "blocks_final_conclusion": quality != "planned",
            "is_low_risk_counter_evidence": False,
        }
        if row.get("response_limited"):
            item.update(
                {
                    "partial_subtype": "response_limited",
                    "remaining_records_not_parsed": row.get("remaining_records_not_parsed"),
                    "cap_metadata_status": row.get("cap_metadata_status"),
                    "cap_metadata_reason": row.get("cap_metadata_reason"),
                    "missing_evidence_type": "remaining_records_not_parsed",
                }
            )
        missing.append(item)
    return missing


DEVICE_ID_KEYS = {
    "device_id",
    "deviceid",
    "deviceId",
    "did",
    "candidate_device_id",
    "candidateDeviceId",
}


OFFLINE_BACKFILL_MODULE_CATALOG = {
    "web_publish_fact": {
        "label": "WEB/发布事实",
        "purpose": "补发布时间、发布端、发布设备、发布 IP/UA、photo_id",
        "trigger_flags": {"content_chain_business_fields_missing", "photo_search_no_data_not_abnormal_publish_exclusion"},
        "trigger_missing_fields": {"photo_id", "publish_time", "publish_device", "publish_source", "publish_ip", "publish_ua"},
    },
    "web_login_history": {
        "label": "WEB/登录历史",
        "purpose": "补发布前后 WEB/H5/PC/token/OAuth/扫码登录，判断历史 WEB 是否常用",
        "trigger_flags": {
            "login_no_data_or_window_gap_not_ato_exclusion",
            "response_too_large_not_login_evidence",
            "login_network_error_subtyped",
        },
        "trigger_missing_fields": {"login_time", "login_source", "login_type", "device_id", "ip_ua"},
    },
    "device_history_baseline": {
        "label": "设备历史基线",
        "purpose": "对齐登录设备、发布设备、用户历史设备是否同一类，补首次出现和历史出现天数",
        "trigger_flags": {"candidate_device_id_missing", "publish_device_login_device_alignment_required"},
        "trigger_missing_fields": {"device_id", "candidate_device_id", "publish_device"},
    },
    "token_oauth_scan_chain": {
        "label": "token/OAuth/扫码链路",
        "purpose": "仅在实时观察出现 token/OAuth/扫码/refreshToken 锚点或对应缺口时补非密码型接管链",
        "trigger_flags": {"token_oauth_scan_anchor_detected", "missing_token_oauth_scan_chain"},
        "trigger_missing_fields": {"token_oauth_scan"},
    },
    "security_action_chain": {
        "label": "改密/换绑/保护账号链",
        "purpose": "仅在实时观察出现安全动作锚点或用户分析缺安全动作字段时补控制权变化后的安全操作",
        "trigger_flags": {"behavior_chain_business_fields_missing"},
        "trigger_missing_fields": {"security_action_type", "operation_time", "operation_type", "operation_device"},
    },
    "post_action_chain": {
        "label": "私信/资料修改/后置行为链",
        "purpose": "仅在实时观察出现私信、资料修改、关注或后置行为锚点/缺口时补非本人动作承接",
        "trigger_flags": {"behavior_chain_business_fields_missing"},
        "trigger_missing_fields": {"profile_change_type", "publish_related_action", "operation_type"},
    },
}


OFFLINE_BACKFILL_MODULE_DECISIONS = {
    "web_publish_fact": {
        "chain_id": "web_publish_fact",
        "next_hop_type": "user_authorized_next_hop",
        "candidate_actions": ["DataAgent/Hive web_publish_fact"],
        "required_inputs": ["user_id", "photo_id_or_publish_time_window"],
        "input_resolution_strategy": "use parsed photo_id/publish_time first; otherwise plan photo anchor discovery",
        "expected_fields": ["publish_time", "publish_source", "publish_device", "publish_ip_ua", "photo_id"],
        "can_auto_execute": False,
        "requires_user_authorization": True,
        "stop_condition": "publish_fact_fields_available",
        "fallback_if_failed": "web_publish_fact_remains_missing_evidence",
        "source_quality_boundary": "offline_required_not_no_risk",
        "answer_boundary": "only generate query plan for explicitly authorized module_id",
    },
    "web_login_history": {
        "chain_id": "web_login_history",
        "next_hop_type": "user_authorized_next_hop",
        "candidate_actions": ["DataAgent/Hive web_login_history"],
        "required_inputs": ["user_id", "anchor_time_or_time_window"],
        "input_resolution_strategy": "use publish/event/user-claim anchor; if absent, ask for anchor or keep plan-only",
        "expected_fields": ["login_time", "login_type", "login_source", "device_id", "ip_ua", "historical_web_baseline"],
        "can_auto_execute": False,
        "requires_user_authorization": True,
        "stop_condition": "login_history_baseline_available",
        "fallback_if_failed": "login_window_incomplete_not_no_risk",
        "source_quality_boundary": "offline_required_not_no_risk",
        "answer_boundary": "offline login history requires per-module authorization",
    },
    "device_history_baseline": {
        "chain_id": "device_identity_alignment",
        "next_hop_type": "user_authorized_next_hop",
        "candidate_actions": ["DataAgent/Hive device_history_baseline"],
        "required_inputs": ["user_id", "device_id_or_did", "anchor_time"],
        "input_resolution_strategy": "use candidate device ranking from login/photo/user-analysis/Track/Weapon",
        "expected_fields": ["historical_device_frequency", "first_seen_time", "recent_activity", "device_seen_days"],
        "can_auto_execute": False,
        "requires_user_authorization": True,
        "stop_condition": "historical_baseline_available",
        "fallback_if_failed": "baseline_authorization_required",
        "source_quality_boundary": "offline_required_not_no_risk",
        "answer_boundary": "baseline query plan only after explicit user authorization",
    },
}


SOURCE_OBSERVATION_CONTRACTS = {
    "login_logs_search": {
        "chain_section": "control_entry",
        "expected_business_fields": [
            "login_time",
            "login_type",
            "login_source",
            "device_id",
            "ip_ua",
            "token_oauth_scan",
            "kickout",
            "success_failure",
            "window_coverage",
        ],
        "role": "登录/控制链入口，不单独完成 ATO 定性",
    },
    "archives_user_profile": {
        "chain_section": "account_state_and_post_actions",
        "expected_business_fields": [
            "account_status",
            "profile_status",
            "punish_or_tag_summary",
            "risk_label",
            "baseline_summary",
            "candidate_device_id",
        ],
        "role": "账号状态和画像基线，不是最终风险判断",
    },
    "archives_user_analysis": {
        "chain_section": "account_state_and_post_actions",
        "expected_business_fields": [
            "operation_time",
            "operation_type",
            "security_action_type",
            "profile_change_type",
            "publish_related_action",
            "operation_device",
            "operation_ip_ua",
        ],
        "role": "改密、换绑、保护账号、资料修改和后置行为时间线",
    },
    "archives_photo_search": {
        "chain_section": "content_publish_handoff",
        "expected_business_fields": [
            "photo_id",
            "publish_time",
            "publish_device",
            "publish_source",
            "publish_ip_ua",
            "content_status",
            "audit_or_strategy_reason",
        ],
        "role": "作品/发布/内容承接链路，no_data 不排除异常发布或 ATO",
    },
    "archives_photo_profile": {
        "chain_section": "content_publish_handoff",
        "expected_business_fields": [
            "photo_id",
            "publish_time",
            "publish_device",
            "publish_source",
            "publish_ip_ua",
            "content_status",
            "audit_or_strategy_reason",
        ],
        "role": "作品 profile 详情，用于回填发布事实链和设备一致性链",
    },
    "archives_photo_meta": {
        "chain_section": "content_publish_handoff",
        "expected_business_fields": [
            "photo_id",
            "publish_time",
            "publish_device",
            "publish_source",
            "publish_ip_ua",
            "content_status",
            "audit_or_strategy_reason",
        ],
        "role": "作品 meta 详情，用于回填 uploadSource/photoMethod/photoIp/publishDevice 等发布证据字段",
    },
    "archives_photo_report_aggregate": {
        "chain_section": "strategy_risk_signal",
        "expected_business_fields": [
            "photo_id",
            "audit_or_strategy_reason",
            "content_status",
        ],
        "role": "作品举报/审核聚合辅助线索，不单独定性 ATO",
    },
    "archives_photo_user_autonomy": {
        "chain_section": "account_state_and_post_actions",
        "expected_business_fields": [
            "photo_id",
            "operation_time",
            "operation_type",
            "content_status",
        ],
        "role": "作品相关用户自治/处置动作辅助线索",
    },
    "archives_gallery_photo_list": {
        "chain_section": "content_publish_handoff",
        "expected_business_fields": [
            "photo_id",
            "publish_time",
            "publish_device",
            "publish_source",
        ],
        "role": "缺 photo_id 时的作品列表锚点发现 source",
    },
    "track_analysis_check_data_ready": {
        "chain_section": "frontend_backend_activity_alignment",
        "expected_business_fields": [
            "candidate_device_id",
            "track_data_ready",
            "event_day_frontend_activity",
            "frontend_backend_activity_alignment",
        ],
        "role": "前后端活跃对齐和真实客户端线索，不是风险结论",
    },
    "archives_related_users": {
        "chain_section": "device_ip_spread",
        "expected_business_fields": [
            "related_user_ids",
            "relation_type",
            "shared_device_or_relation",
        ],
        "role": "扩散线索，不是团伙结论",
    },
    "weapon_inventory": {
        "chain_section": "device_ip_spread",
        "expected_business_fields": [
            "user_device_edge",
            "device_id",
            "risk_label",
            "graph_relation_count",
            "riskdata_status",
        ],
        "role": "设备图谱和设备风险辅助证据，不替代登录/发布链路",
    },
    "rcp_event_detail": {
        "chain_section": "strategy_risk_signal",
        "expected_business_fields": [
            "event_id",
            "event_type",
            "hit_policy",
            "event_time",
        ],
        "role": "事件归因上下文，不单独定性风险",
    },
    "rcp_event_feature_list": {
        "chain_section": "strategy_risk_signal",
        "expected_business_fields": [
            "feature_group",
            "feature_presence",
            "feature_list_boundary",
        ],
        "role": "策略特征分组/有限观察，不声称完整明细",
    },
    "rcp_fast_query_hbase": {
        "chain_section": "strategy_risk_signal",
        "expected_business_fields": [
            "event_id",
            "event_type",
            "event_time",
            "policy_code",
            "risk_decision",
            "hit_policy",
        ],
        "role": "用户/source_id 维度近期策略命中 discovery；策略命中是辅助线索，不是最终定性",
    },
    "rcp_policy_tree_lookup": {
        "chain_section": "strategy_risk_signal",
        "expected_business_fields": [
            "policy_tree_code",
            "policy_tree_version",
            "policy_asset_path",
        ],
        "role": "策略资产治理，不是单案命中证据",
    },
}


BUSINESS_FIELD_ALIASES = {
    "login_time": {"login_time", "loginTime", "loginTimestamp", "timestamp", "event_time", "time"},
    "login_type": {"login_type", "loginType", "reset_login_type", "resetLoginType", "authType"},
    "login_source": {"login_source", "loginSource", "source", "clientType", "platform", "loginPlatform"},
    "device_id": {"device_id", "deviceId", "deviceid", "did", "loginDeviceId"},
    "ip": {"ip", "loginIp", "clientIp", "requestIp"},
    "ua": {"ua", "UA", "userAgent", "user_agent", "browserUa"},
    "token_oauth_scan": {"token", "oauth", "OAuth", "scan", "scanLogin", "refreshToken", "byToken", "logined"},
    "kickout": {"kickout", "kick_out", "kickedOut", "protectKickout"},
    "success_failure_sequence": {"login_result", "loginResult", "success", "failure", "status"},
    "window_coverage": {"request_window_start", "request_window_end", "from_timestamp", "to_timestamp"},
    "account_status": {"account_status", "accountStatus", "status", "accountState"},
    "profile_baseline": {"profile_baseline", "profileBaseline", "profile", "userProfile"},
    "punishment_or_label": {"punishment", "label", "riskLabel", "tag", "penalty"},
    "protection_state": {"protection_state", "accountProtection", "protectState"},
    "password_change": {"password_change", "resetPwd", "changePassword", "pwdChange"},
    "binding_change": {"binding_change", "bindPhone", "unbind", "changeBinding"},
    "account_protection": {"account_protection", "protectAccount", "accountProtect"},
    "profile_change": {"profile_change", "profileChange", "modifyProfile"},
    "follow_action": {"follow_action", "follow", "followAction"},
    "publish_related_operation": {"publish_related_operation", "publish", "photoPublish", "postVideo"},
    "security_operation_timeline": {"security_operation_timeline", "securityTimeline", "operationTime"},
    "photo_id": {"photo_id", "photoId", "photoID", "content_id", "contentId"},
    "publish_time": {"publish_time", "publishTime", "createTime", "uploadTime", "upload_time", "create_time"},
    "publish_device": {"publish_device", "publishDevice", "publishDeviceId", "uploadDevice", "uploadDeviceId", "device_id", "deviceId", "did"},
    "publish_source": {"publish_source", "publishSource", "source", "clientType", "publishPlatform", "uploadSource", "photoMethod", "operationSource", "client", "app", "platform"},
    "publish_ip": {"publish_ip", "publishIp", "photoIp", "ip", "clientIp"},
    "publish_ua": {"publish_ua", "publishUA", "publishUa", "ua", "userAgent"},
    "content_status": {"content_status", "photoStatus", "auditStatus", "status"},
    "audit_or_strategy_reason": {"audit_reason", "strategyReason", "hitReason", "reason"},
    "candidate_device_id": {"candidate_device_id", "device_id", "deviceId", "did"},
    "track_data_ready": {"track_data_ready", "dataReady", "ready"},
    "event_day_frontend_activity": {"event_day_frontend_activity", "frontendActivity", "activePv"},
    "frontend_backend_activity_alignment": {"frontend_backend_activity_alignment", "frontBackendAlignment"},
    "event_id": {"event_id", "eventId", "sourceId", "source_id"},
    "event_type": {"event_type", "eventType", "eventTypeCode", "eventTypeCodes"},
    "event_time": {"event_time", "eventTime", "queryTime", "time", "hitTime", "createTime"},
    "policy_code": {"policy_code", "policyCode", "hitPolicyCode", "hitFusePolicyCode"},
    "hit_policy": {"hit_policy", "hitPolicy", "hitPolicies", "hitProductionPolicies"},
    "risk_decision": {"risk_decision", "riskDecision", "decision", "riskResult", "result"},
}


OBSERVATION_SAFE_ANCHOR_KEYS = {
    "user_id",
    "userId",
    "photo_id",
    "photoId",
    "event_id",
    "eventId",
    "source_id",
    "sourceId",
    "policy_code",
    "policyCode",
    "policyTreeCode",
    "device_id",
    "deviceId",
    "did",
    "candidate_device_id",
    "login_time",
    "loginTime",
    "publish_time",
    "publishTime",
    "createTime",
    "operationTime",
    "login_source",
    "loginSource",
    "login_type",
    "loginType",
    "publish_source",
    "publishSource",
    "publish_device",
    "publishDevice",
    "uploadSource",
    "photoMethod",
    "photoIp",
    "uploadDevice",
    "uploadDeviceId",
    "ip",
    "clientIp",
    "loginIp",
    "publishIp",
    "province",
    "city",
    "asn",
    "isProxy",
    "isIDC",
    "ua",
    "UA",
    "userAgent",
    "device_model",
    "deviceModel",
    "os",
    "osVersion",
    "appVersion",
    "eventType",
    "eventTypeCode",
    "policy_code",
    "hitPolicy",
    "hitPolicies",
    "riskDecision",
    "queryTime",
    "first_seen_device",
    "firstSeenDevice",
    "device_seen_days",
    "deviceSeenDays",
    "field_path",
    "result_array_path",
    "request_window_start",
    "request_window_end",
}


def _source_quality_by_id(source_quality_matrix: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(row.get("source_id")): row for row in source_quality_matrix.get("per_source", [])}


def _transport_issue_subtype(row: dict[str, Any]) -> str | None:
    interpretation = derive_transport_interpretation(row)
    if interpretation in {
        "transport_success",
        "transport_success_body_suppressed",
        "transport_success_likely_no_data",
        "transport_success_partial_observation_response_too_large",
    }:
        return None
    if interpretation == "auth_flow_not_completed_in_bound_context":
        return "auth_flow_not_completed_in_bound_context"
    status = str(row.get("source_status") or "").lower()
    error_type = str(row.get("error_type") or "").lower()
    transport_error = str(row.get("transport_error") or "").lower()
    platform_error = str(row.get("platform_error") or "").lower()
    if row.get("invalid_params") or "invalid" in status or "missing_required" in status:
        return "invalid_params"
    if "batch_contract" in status or "batch_contract" in error_type:
        return "batch_contract_error"
    if "service_unavailable" in status or "connection" in transport_error or "urlerror" in error_type:
        return "service_gap"
    if transport_error:
        return "transport_error"
    if platform_error:
        return "platform_error"
    return None


def _row_has_large_response(row: dict[str, Any]) -> bool:
    if row.get("body_truncated") is True or row.get("response_too_large") is True:
        return True
    if str(row.get("raw_body_handling") or "").lower() == "json_array_capped":
        return True
    if int(row.get("missing_records") or 0) > 0:
        return True
    for key in ("source_status", "error_type", "platform_error", "transport_error", "missing_body_reason", "cap_reason"):
        text = str(row.get(key) or "").lower()
        if "response_too_large" in text or "too_large" in text or "byte_limit" in text:
            return True
    return False


def _small_visible_body_without_business_fields(row: dict[str, Any]) -> bool:
    try:
        observed_bytes = int(row.get("observed_bytes") or row.get("transport.observed_bytes") or 0)
    except (TypeError, ValueError):
        observed_bytes = 0
    raw_body_handling = str(row.get("raw_body_handling") or row.get("transport.raw_body_handling") or "").lower()
    return (
        (row.get("body_present") is True or row.get("transport.body_present") is True)
        and row.get("body_truncated") is not True
        and row.get("transport.body_truncated") is not True
        and 0 < observed_bytes <= 512
        and raw_body_handling in {"visible", "body_visible"}
    )


def _rows_by_source_id_from_batch(batch_result: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for row in normalize_mapping_or_list(batch_result.get("transport_status_matrix")):
        source_id = str(row.get("source_id") or "")
        if source_id:
            rows[source_id] = row
    for item in normalize_mapping_or_list(batch_result.get("source_results")):
        source_id = str(item.get("source_id") or "")
        if not source_id:
            continue
        merged = dict(rows.get(source_id, {}))
        merged["source_result"] = item
        if isinstance(item.get("transport"), dict):
            merged.update({f"transport.{key}": value for key, value in item["transport"].items()})
        rows[source_id] = merged
    return rows


def _key_matches_business_field(key: str, business_field: str) -> bool:
    aliases = BUSINESS_FIELD_ALIASES.get(business_field, {business_field})
    lowered = key.lower()
    return any(alias.lower() == lowered or alias.lower() in lowered for alias in aliases)


def extract_observation_field_handles(
    value: Any,
    *,
    source_id: str,
    path: str = "$",
    limit: int = 80,
) -> list[dict[str, Any]]:
    handles: list[dict[str, Any]] = []
    if len(handles) >= limit:
        return handles
    if isinstance(value, dict):
        for key, item in value.items():
            lowered = key.lower()
            child_path = f"{path}.{key}"
            if _is_credential_secret_key(key):
                continue
            if lowered in BODY_KEYS_TO_SUPPRESS:
                continue
            if key in OBSERVATION_SAFE_ANCHOR_KEYS and isinstance(item, (str, int, float, bool)):
                handles.append(
                    {
                        "field": key,
                        "field_path": child_path,
                        "source_id": source_id,
                        "value": item,
                    }
                )
                if len(handles) >= limit:
                    return handles
            handles.extend(
                extract_observation_field_handles(item, source_id=source_id, path=child_path, limit=limit - len(handles))
            )
            if len(handles) >= limit:
                return handles[:limit]
    elif isinstance(value, list):
        for index, item in enumerate(value):
            handles.extend(
                extract_observation_field_handles(item, source_id=source_id, path=f"{path}[{index}]", limit=limit - len(handles))
            )
            if len(handles) >= limit:
                return handles[:limit]
    return handles[:limit]


def match_business_fields(
    field_handles: list[dict[str, Any]],
    expected_business_fields: list[str],
) -> tuple[list[str], list[str]]:
    present: list[str] = []
    for business_field in expected_business_fields:
        for handle in field_handles:
            field_name = str(handle.get("field") or "")
            field_path = str(handle.get("field_path") or "")
            if _key_matches_business_field(field_name, business_field) or _key_matches_business_field(field_path, business_field):
                present.append(business_field)
                break
    present = unique_strings(present)
    missing = [field for field in expected_business_fields if field not in present]
    return present, missing


def build_source_observations(
    source_plan: list[SourcePlanItem],
    source_quality_matrix: dict[str, Any],
    batch_result: dict[str, Any],
) -> list[dict[str, Any]]:
    rows_by_id = _source_quality_by_id(source_quality_matrix)
    raw_rows_by_id = _rows_by_source_id_from_batch(batch_result)
    observations: list[dict[str, Any]] = []
    processed_source_ids: set[str] = set()

    def append_observation(source_id: str, fallback_action: str, fallback_role: str) -> None:
        row = rows_by_id.get(source_id, {})
        action = str(row.get("action") or fallback_action)
        contract = SOURCE_OBSERVATION_CONTRACTS.get(action, {})
        quality = str(row.get("quality_class") or "blocked")
        flags: list[str] = []
        raw_source_payload = raw_rows_by_id.get(source_id, {})
        expected_business_fields = list(contract.get("expected_business_fields", []))
        safe_observation = build_safe_observation(
            source_id=source_id,
            action=action,
            source_payload=raw_source_payload,
            transport_row=row,
            expected_business_fields=expected_business_fields,
            chain_section=str(contract.get("chain_section", "source_quality")),
            role=str(contract.get("role", fallback_role)),
        )
        field_handles = list(safe_observation.get("extracted_safe_handles", []))
        row_cap_metadata = safe_observation.get("passthrough_row_cap") or {}
        extracted_business_fields = list(safe_observation.get("extracted_business_fields", []))
        missing_business_fields = list(safe_observation.get("missing_business_fields", []))

        if row.get("body_truncated") or quality == "partial":
            flags.append("partial_observation_available")
        if str(row.get("raw_body_handling") or "").lower() in {"suppressed", "capped", "metadata_only"}:
            flags.append("raw_body_suppressed_not_body_missing")
        if quality == "no_data":
            flags.append("no_data_not_risk_exclusion")
        if quality in {"blocked", "timeout", "parse_error", "auth_failed"}:
            flags.append("missing_evidence_not_counter_evidence")
        if quality == "planned":
            flags.append("dry_run_not_platform_evidence")
        if quality in {"completed", "partial"} and missing_business_fields:
            flags.extend(["observation_compression_gap", "business_fields_not_extracted"])
        if "service_body_visibility_gap" in safe_observation.get("interpretation_flags", []):
            flags.append("service_body_visibility_gap")

        if action == "login_logs_search":
            if str(row.get("transport_interpretation") or "") == "auth_flow_not_completed_in_bound_context":
                flags.extend(["auth_flow_not_completed_in_bound_context", "html_response_not_business_json"])
            if row_cap_metadata:
                flags.append("partial_login_log_parsed_from_json_array_capped")
                if int(row_cap_metadata.get("missing_records") or 0) > 0:
                    flags.append("login_log_incomplete")
                if str(row_cap_metadata.get("cap_reason") or "") == "byte_limit":
                    flags.append("byte_limit_partial_source")
            subtype = _transport_issue_subtype(row)
            if subtype:
                flags.append(f"login_logs_{subtype}")
            transport_interpretation = str(row.get("transport_interpretation") or "")
            if "transport_success" in transport_interpretation:
                flags.append(transport_interpretation)
            if _row_has_large_response(row):
                flags.extend([
                    "response_too_large_not_login_evidence",
                    "response_too_large_window_shrink_recommended",
                ])
                if safe_observation.get("parser_input_available") and set(extracted_business_fields) & {
                    "login_time",
                    "login_type",
                    "login_source",
                    "device_id",
                    "ip_ua",
                }:
                    flags.append("partial_login_log_parsed_from_capped_body")
                elif row.get("body_present") is True and not _auth_flow_not_completed_gap(row):
                    flags.append("service_body_visibility_gap_for_truncated_login_log")
            if quality == "no_data":
                flags.append("login_no_data_or_window_gap_not_ato_exclusion")
        elif action == "archives_user_analysis":
            if quality == "partial" or row.get("body_truncated"):
                flags.append("partial_behavior_timeline")
            if quality in {"completed", "partial"} and "behavior_chain_business_fields_missing" not in flags and missing_business_fields:
                flags.append("behavior_chain_business_fields_missing")
        elif action in {"archives_photo_search", "archives_photo_profile", "archives_photo_meta", "archives_gallery_photo_list"}:
            if quality in {"completed", "partial"} and missing_business_fields:
                flags.append("content_chain_business_fields_missing")
                if _small_visible_body_without_business_fields(row):
                    flags.append("content_anchor_no_rows_or_empty_payload")
            if quality == "no_data":
                flags.append("photo_search_no_data_not_abnormal_publish_exclusion")
            flags.append("publish_device_login_device_alignment_required")
        elif action == "track_analysis_check_data_ready":
            flags.append("track_check_data_ready_not_risk_conclusion")
            if "device_id" in row.get("missing_required_fields", []):
                flags.extend([
                    "user_device_entity_resolution_attempted",
                    "candidate_device_id_missing",
                    "candidate_device_id_missing_after_resolution",
                ])
        elif action == "archives_related_users":
            flags.append("archives_related_users_spread_clue_not_gang")
        elif action == "weapon_inventory":
            flags.append("weapon_device_graph_not_ato_conclusion")
        elif action == "rcp_event_feature_list" and (quality == "partial" or row.get("body_truncated")):
            flags.append("feature_list_partial_only_feature_group_summary")
        elif action == "rcp_policy_tree_lookup":
            flags.append("policy_tree_asset_not_event_hit_path")

        if quality in {"completed", "partial"} and action in {
            "archives_user_analysis",
            "archives_photo_search",
            "archives_photo_profile",
            "archives_photo_meta",
            "archives_gallery_photo_list",
        }:
            flags.append("completed_transport_not_business_chain_closure")

        breakpoint_type = infer_observation_breakpoint(
            quality=quality,
            row=row,
            safe_observation=safe_observation,
            missing_business_fields=missing_business_fields,
        )
        if (
            action in {"archives_photo_search", "archives_photo_profile", "archives_photo_meta", "archives_gallery_photo_list"}
            and missing_business_fields
            and _small_visible_body_without_business_fields(row)
        ):
            breakpoint_type = "source_has_no_content_anchor_rows"

        observations.append(
            {
                "dennis_observation": safe_observation,
                "source_id": source_id,
                "action": action,
                "chain_section": contract.get("chain_section", "source_quality"),
                "quality_class": quality,
                "role": contract.get("role", fallback_role),
                "expected_business_fields": expected_business_fields,
                "extracted_business_fields": extracted_business_fields,
                "observed_field_handles": field_handles,
                "parsed_body_field_handles": safe_observation.get("parsed_body_safe_handles", []),
                "missing_business_fields": missing_business_fields,
                "candidate_device_ids": safe_observation.get("candidate_device_ids", []),
                "passthrough_row_cap": row_cap_metadata,
                "interpretation_flags": unique_strings(flags + list(safe_observation.get("interpretation_flags", []))),
                "breakpoint_type": breakpoint_type,
                "evidence_use": (
                    "business_evidence_candidate"
                    if (extracted_business_fields or safe_observation.get("candidate_device_ids")) and quality in {"completed", "partial"}
                    else "transport_only_boundary"
                    if quality in {"completed", "partial"}
                    else "missing_evidence_or_boundary_only"
                ),
                "is_low_risk_counter_evidence": False,
            }
        )
        processed_source_ids.add(source_id)

    for item in source_plan:
        append_observation(item.source_id, item.action, item.expected_observation)

    for row in source_quality_matrix.get("per_source", []):
        source_id = str(row.get("source_id") or "")
        if not source_id or source_id in processed_source_ids:
            continue
        append_observation(
            source_id,
            str(row.get("action") or "unknown_action"),
            "additional controlled batch source returned outside initial source_plan",
        )

    return observations


def infer_observation_breakpoint(
    *,
    quality: str,
    row: dict[str, Any],
    safe_observation: dict[str, Any],
    missing_business_fields: list[str],
) -> str | None:
    flags = set(str(flag) for flag in safe_observation.get("interpretation_flags", []))
    if _auth_flow_not_completed_gap(row):
        return "auth_flow_not_completed_in_bound_context"
    if (
        row.get("body_truncated") is True
        and row.get("body_present") is True
        and not safe_observation.get("parser_input_available")
    ):
        return "service_body_visibility_gap_for_truncated_login_log"
    if row.get("body_truncated") is True or _row_has_large_response(row):
        return "response_too_large_needs_window_shrink"
    if "service_body_visibility_gap" in flags:
        return "service_body_visibility_gap"
    if safe_observation.get("parser_input_available") and missing_business_fields:
        return "parser_mapping_gap"
    if quality in {"completed", "partial"} and missing_business_fields:
        return "source_has_no_field"
    if quality in {"blocked", "timeout", "parse_error", "auth_failed"}:
        return str(row.get("error_type") or row.get("transport_interpretation") or quality)
    return None


def unique_strings(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def _count_by_key(items: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        value = str(item.get(key) or "unknown")
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def extract_candidate_device_ids(value: Any, *, source_id: str | None = None, path: str = "$") -> list[dict[str, str]]:
    candidates: list[dict[str, str]] = []
    if isinstance(value, dict):
        current_source_id = str(value.get("source_id") or source_id or "unknown_source")
        for key, item in value.items():
            child_path = f"{path}.{key}"
            if key in DEVICE_ID_KEYS and isinstance(item, (str, int)) and str(item).strip():
                candidates.append(
                    {
                        "device_id": str(item).strip(),
                        "source_id": current_source_id,
                        "field_path": child_path,
                    }
                )
            candidates.extend(extract_candidate_device_ids(item, source_id=current_source_id, path=child_path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            candidates.extend(extract_candidate_device_ids(item, source_id=source_id, path=f"{path}[{index}]"))
    deduped: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for candidate in candidates:
        key = (candidate["device_id"], candidate["source_id"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(candidate)
    return deduped[:20]


def extract_candidate_device_id(value: Any) -> str | None:
    candidates = extract_candidate_device_ids(value)
    return candidates[0]["device_id"] if candidates else None


def build_user_device_entity_resolution(
    source_plan: list[SourcePlanItem],
    batch_result: dict[str, Any],
    *,
    provided_device_id: str | None,
    source_observations: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    extracted = extract_candidate_device_ids(batch_result)
    candidates: list[dict[str, Any]] = []
    if provided_device_id:
        candidates.append(
            {
                "device_id": provided_device_id,
                "source_id": "user_input",
                "field_path": "args.device_id",
            }
        )
    candidates.extend(extracted)
    for observation in source_observations or []:
        for candidate in observation.get("candidate_device_ids", []):
            if not isinstance(candidate, dict):
                continue
            device_id = str(candidate.get("device_id") or "").strip()
            if not device_id:
                continue
            candidates.append(
                {
                    "device_id": device_id,
                    "source_id": str(candidate.get("source_id") or observation.get("source_id") or "safe_observation"),
                    "action": str(observation.get("action") or ""),
                    "field_path": str(candidate.get("field_path") or "safe_observation.candidate_device_ids"),
                }
            )
    source_rank = {
        "user_input": 100,
        "ato_archives_photo_search": 90,
        "ato_login_logs_search": 85,
        "ato_archives_user_analysis": 80,
        "ato_archives_user_profile": 70,
        "ato_weapon_inventory": 70,
        "ato_track_analysis_check_data_ready": 60,
    }
    action_rank = {
        "archives_photo_meta": 95,
        "archives_photo_profile": 92,
        "archives_photo_search": 90,
        "login_logs_search": 85,
        "archives_user_analysis": 80,
    }
    deduped: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for candidate in candidates:
        device_id = candidate["device_id"]
        if device_id in seen_ids:
            continue
        seen_ids.add(device_id)
        candidate = dict(candidate)
        source_id_text = str(candidate.get("source_id") or "")
        candidate["rank_score"] = (
            source_rank.get(source_id_text)
            or action_rank.get(str(candidate.get("action") or ""))
            or (95 if "photo_meta" in source_id_text else 92 if "photo_profile" in source_id_text else 50)
        )
        candidate["rank_reason"] = (
            "user_provided"
            if candidate.get("source_id") == "user_input"
            else "source_business_field_device_handle"
        )
        deduped.append(candidate)
    deduped.sort(key=lambda item: int(item.get("rank_score") or 0), reverse=True)

    planned_actions = {item.action for item in source_plan}
    candidate_source_ids = {candidate["source_id"] for candidate in deduped}
    planned_source_ids_by_action = {item.action: item.source_id for item in source_plan}

    def source_has_candidate(action: str) -> bool:
        source_id = planned_source_ids_by_action.get(action)
        return bool(source_id and source_id in candidate_source_ids) or any(
            str(candidate.get("action")) == action for candidate in deduped
        )

    device_entity_gap_breakdown = {
        "login_device_not_extracted": not source_has_candidate("login_logs_search"),
        "publish_device_not_extracted": not (
            source_has_candidate("archives_photo_search")
            or source_has_candidate("archives_photo_profile")
            or source_has_candidate("archives_photo_meta")
        ),
        "user_analysis_device_not_extracted": not source_has_candidate("archives_user_analysis"),
        "user_device_graph_not_checked_or_failed": (
            "weapon_inventory" not in planned_actions or not source_has_candidate("weapon_inventory")
        ),
        "track_candidate_device_missing": not deduped,
    }
    missing_device_reasons = [
        reason for reason, missing in device_entity_gap_breakdown.items() if missing
    ]
    observations_by_action = {str(obs.get("action")): obs for obs in source_observations or []}

    def candidate_attempt(action: str, label: str) -> dict[str, Any]:
        source_id = planned_source_ids_by_action.get(action)
        observation = observations_by_action.get(action, {})
        if source_has_candidate(action):
            status = "candidate_device_found"
        elif not source_id:
            status = "candidate_device_source_not_planned"
        elif observation.get("breakpoint_type") in {
            "service_body_visibility_gap",
            "service_body_visibility_gap_for_truncated_login_log",
        }:
            status = "candidate_device_source_unavailable"
        elif observation.get("quality_class") in {"blocked", "timeout", "parse_error", "auth_failed"}:
            status = "candidate_device_source_unavailable"
        elif observation.get("missing_business_fields"):
            status = "device_missing_after_backfill"
        else:
            status = "candidate_device_source_checked_no_candidate"
        return {
            "source": label,
            "action": action,
            "source_id": source_id,
            "status": status,
            "breakpoint_type": observation.get("breakpoint_type"),
            "missing_business_fields": observation.get("missing_business_fields", []),
        }

    next_hop_attempts = [
        candidate_attempt("login_logs_search", "login_device"),
        candidate_attempt("archives_photo_search", "publish_device"),
        candidate_attempt("archives_user_analysis", "operation_device"),
        candidate_attempt("archives_user_profile", "historical_or_profile_device"),
        candidate_attempt("weapon_inventory", "user_device_graph"),
        candidate_attempt("track_analysis_check_data_ready", "track_get_device_or_readiness"),
    ]
    resolution_status = (
        "multiple_candidate_devices_need_ranking"
        if len(deduped) > 1
        else "candidate_device_found"
        if deduped
        else "candidate_device_id_missing_after_resolution"
    )
    return {
        "layer": "user_device_entity_resolution",
        "default_p0_entity_layer": True,
        "resolution_attempted": True,
        "resolution_status": resolution_status,
        "purpose": "bridge user-level evidence to device-level Track/Weapon/publish-device alignment",
        "candidate_device_ids": deduped,
        "ranked_candidate_device_ids": deduped,
        "multiple_candidate_devices_need_ranking": len(deduped) > 1,
        "candidate_device_id_missing": not deduped,
        "candidate_device_id_missing_after_resolution": not deduped,
        "candidate_device_id_missing_semantics": "missing any device entity usable for login/publish/user-analysis/Track/Weapon alignment, not only missing risky device",
        "device_entity_gap_breakdown": device_entity_gap_breakdown,
        "next_hop_attempts": next_hop_attempts,
        "candidate_sources_checked": [
            "login_logs_search",
            "archives_user_analysis",
            "archives_photo_search",
            "weapon_inventory",
            "track_analysis_check_data_ready",
        ],
        "drives_followup": [
            source
            for source in [
                "track_analysis_check_data_ready",
                "weapon_inventory",
                "publish_device_login_device_alignment",
                "historical_device_baseline",
            ]
            if source in planned_actions or source.endswith("_alignment") or source.endswith("_baseline")
        ],
        "track_missing_device_id_blocks_batch": False,
        "missing_evidence": (
            [
                {
                    "reason": "candidate_device_id_missing",
                    "post_resolution_reason": "candidate_device_id_missing_after_resolution",
                    "device_entity_gap_breakdown": device_entity_gap_breakdown,
                    "missing_device_reasons": missing_device_reasons,
                    "next_hop_attempts": next_hop_attempts,
                    "needed_for": [
                        "track_analysis_check_data_ready",
                        "weapon riskData/graphData follow-up",
                        "publish device vs login device alignment",
                        "historical device baseline comparison",
                    ],
                    "is_low_risk_counter_evidence": False,
                }
            ]
            if not deduped
            else []
        ),
    }


def build_dynamic_offline_backfill_recommendation(
    source_observations: list[dict[str, Any]],
    user_device_entity_resolution: dict[str, Any],
    missing_evidence: list[dict[str, Any]],
    chain_status: dict[str, Any] | None = None,
) -> dict[str, Any]:
    observed_flags: set[str] = set()
    missing_fields: set[str] = set()
    triggering_sources: dict[str, list[str]] = {}

    for observation in source_observations:
        source_id = str(observation.get("source_id") or "unknown_source")
        for flag in observation.get("interpretation_flags", []):
            observed_flags.add(str(flag))
            triggering_sources.setdefault(str(flag), []).append(source_id)
        for field in observation.get("missing_business_fields", []):
            missing_fields.add(str(field))
            triggering_sources.setdefault(str(field), []).append(source_id)

    if user_device_entity_resolution.get("candidate_device_id_missing"):
        observed_flags.add("candidate_device_id_missing")
        triggering_sources.setdefault("candidate_device_id_missing", []).append("user_device_entity_resolution")
    for item in missing_evidence:
        reason = str(item.get("reason") or "")
        if reason:
            observed_flags.add(reason)
            triggering_sources.setdefault(reason, []).append(str(item.get("source_id") or "missing_evidence"))
        for field in item.get("missing_business_fields", []) if isinstance(item.get("missing_business_fields"), list) else []:
            missing_fields.add(str(field))

    options: list[dict[str, Any]] = []
    for module_id, module in OFFLINE_BACKFILL_MODULE_CATALOG.items():
        if chain_status and any(
            isinstance(chain_status.get(chain_id), dict)
            and chain_status[chain_id].get("status") == "closed"
            and definition.get("missing_module") == module_id
            for chain_id, definition in CHAIN_DEFINITIONS.items()
        ):
            continue
        trigger_flags = set(module.get("trigger_flags", set()))
        trigger_missing_fields = set(module.get("trigger_missing_fields", set()))
        matched_flags = sorted(trigger_flags & observed_flags)
        matched_fields = sorted(trigger_missing_fields & missing_fields)
        if not matched_flags and not matched_fields:
            continue
        matched_reasons = matched_flags + matched_fields
        decision = OFFLINE_BACKFILL_MODULE_DECISIONS.get(module_id, {})
        options.append(
            {
                "module_id": module_id,
                "label": module["label"],
                "purpose": module["purpose"],
                "chain_id": decision.get("chain_id"),
                "trigger_condition": matched_reasons,
                "next_hop_type": decision.get("next_hop_type", "user_authorized_next_hop"),
                "candidate_actions": decision.get("candidate_actions", []),
                "required_inputs": decision.get("required_inputs", []),
                "input_resolution_strategy": decision.get("input_resolution_strategy"),
                "expected_fields": decision.get("expected_fields", []),
                "can_auto_execute": bool(decision.get("can_auto_execute", False)),
                "requires_user_authorization": bool(decision.get("requires_user_authorization", True)),
                "stop_condition": decision.get("stop_condition"),
                "fallback_if_failed": decision.get("fallback_if_failed"),
                "source_quality_boundary": decision.get("source_quality_boundary"),
                "answer_boundary": decision.get("answer_boundary"),
                "generated_from_current_gap": True,
                "triggered_by": matched_reasons,
                "triggering_sources": unique_strings(
                    [
                        source
                        for reason in matched_reasons
                        for source in triggering_sources.get(reason, [])
                    ]
                ),
            }
        )

    return {
        "required_when": "realtime control/action/device/baseline chain is incomplete",
        "dataagent_hive_called": False,
        "authorization_required": True,
        "authorization_mode": "select_dynamic_modules_by_id",
        "fixed_1_to_5_menu": False,
        "module_generation": "dynamic_from_current_missing_evidence",
        "options": options,
        "user_prompt": (
            "请回复要授权的 module_id，例如 web_publish_fact,device_history_baseline；"
            "只会生成你授权模块的 DataAgent/Hive 查询计划，未授权模块继续保留为 missing_evidence。"
        ),
        "authorization_boundary": [
            "only selected dynamic modules may enter DataAgent/Hive query plan",
            "unselected modules remain missing_evidence",
            "previous authorization is not reusable for a new module, table, time range, or evidence direction",
            "DataAgent/Hive is not called by this harness without explicit per-module authorization",
        ],
    }


def with_track_device(source_plan: list[SourcePlanItem], device_id: str) -> SourcePlanItem:
    for item in source_plan:
        if item.source_id == "ato_track_analysis_check_data_ready":
            params = dict(item.params)
            params["device_id"] = device_id
            return SourcePlanItem(
                source_id=item.source_id,
                action=item.action,
                execution_group="independent_parallel",
                depends_on=[],
                timeout_class=item.timeout_class,
                failure_policy=item.failure_policy,
                source_priority=item.source_priority,
                expected_observation=item.expected_observation,
                params=params,
                timeout_ms=item.timeout_ms,
                required_fields=item.required_fields,
                window_policy=item.window_policy,
                window_start_ms=item.window_start_ms,
                window_end_ms=item.window_end_ms,
            )
    raise ValueError("track source plan missing")


def _photo_ids_from_observations(source_observations: list[dict[str, Any]]) -> list[str]:
    values = _field_values_from_observations(source_observations, {"photo_id"})
    return unique_strings([str(item.get("value")) for item in values if item.get("value")])[:5]


def build_photo_detail_followup_items(
    source_observations: list[dict[str, Any]],
    *,
    window_start_ms: int,
    window_end_ms: int,
) -> list[SourcePlanItem]:
    """Build registered photo detail next-hop sources from already parsed photo ids.

    This uses the existing controlled batch path. It does not discover new
    actions, guess URLs, or call platform sources outside the harness.
    """

    photo_ids = _photo_ids_from_observations(source_observations)
    if not photo_ids:
        return []

    existing = {
        (str(observation.get("action")), str(handle.get("value")))
        for observation in source_observations
        if str(observation.get("action")) in {"archives_photo_profile", "archives_photo_meta"}
        for handle in observation.get("parsed_body_field_handles", [])
        if str(handle.get("canonical_field") or handle.get("field")) == "photo_id"
    }
    items: list[SourcePlanItem] = []
    for photo_id in photo_ids:
        for action, suffix, expected in [
            (
                "archives_photo_profile",
                "profile",
                "photo profile publish source/device/IP/status fields",
            ),
            (
                "archives_photo_meta",
                "meta",
                "photo meta uploadSource/photoMethod/photoIp/publishDevice fields",
            ),
        ]:
            if (action, photo_id) in existing:
                continue
            items.append(
                SourcePlanItem(
                    source_id=f"ato_archives_photo_{suffix}_{photo_id}",
                    action=action,
                    execution_group="auth_sensitive_serial",
                    depends_on=["ato_archives_photo_search"],
                    timeout_class="auth_sensitive",
                    failure_policy="non_blocking_partial",
                    source_priority="P0-next-hop",
                    expected_observation=expected,
                    params={"photo_id": photo_id},
                    timeout_ms=30_000,
                    required_fields=["photo_id"],
                    window_policy="photo_detail_no_7d_login_window_constraint",
                    window_start_ms=window_start_ms,
                    window_end_ms=window_end_ms,
                )
            )
    return items


def synthetic_track_missing_result(track_item: SourcePlanItem) -> dict[str, Any]:
    row = {
        "source_id": track_item.source_id,
        "action": track_item.action,
        "category": "blocked",
        "source_status": "missing_required_fields",
        "error_type": "missing_required_fields",
        "http_status": None,
        "content_type": None,
        "body_present": False,
        "body_truncated": False,
        "observed_bytes": 0,
        "elapsed_ms": 0,
        "timeout_ms": track_item.timeout_ms,
        "transport_error": None,
        "platform_error": None,
        "invalid_params": True,
        "timeout": False,
        "raw_body_handling": "not_requested_until_candidate_device_id",
        "missing_required_fields": ["device_id"],
        "candidate_device_lookup_attempted": True,
        "candidate_device_resolution_status": "candidate_device_id_missing_after_resolution",
    }
    return {
        "ok": True,
        "response_mode": "controlled_batch_passthrough",
        "batch_status": "partial",
        "source_results": {track_item.source_id: {"source_id": track_item.source_id, "transport": row}},
        "transport_status_matrix": {track_item.source_id: row},
        "classifications": build_classifications({track_item.source_id: row}),
        "missing_or_failed_sources": [row],
        "safety": {
            "legacy_runner_fallback_attempted": False,
            "manual_batch_curl_fallback_allowed": False,
            "single_action_freeform_attempted": False,
        },
    }


def merge_batch_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    merged_transport: dict[str, dict[str, Any]] = {}
    merged_source_results: dict[str, Any] = {}
    merged_missing: list[dict[str, Any]] = []
    harness_errors: list[dict[str, Any]] = []

    for result in results:
        for row in normalize_mapping_or_list(result.get("transport_status_matrix")):
            source_id = str(row.get("source_id") or f"unknown_{len(merged_transport) + 1}")
            merged_transport[source_id] = row
        for row in rows_from_source_results(result.get("source_results")):
            source_id = str(row.get("source_id") or f"unknown_{len(merged_source_results) + 1}")
            merged_source_results[source_id] = {"source_id": source_id, "transport": row}
        merged_missing.extend(normalize_mapping_or_list(result.get("missing_or_failed_sources")))
        if isinstance(result.get("harness_error"), dict):
            harness_errors.append(result["harness_error"])

    classifications = build_classifications(merged_transport)
    non_planned = sum(len(values) for key, values in classifications.items() if key not in {"planned"})
    if harness_errors:
        batch_status = "harness_error"
    elif non_planned and (classifications.get("blocked") or classifications.get("timeout") or classifications.get("parse_error") or classifications.get("auth_failed")):
        batch_status = "partial"
    elif classifications.get("planned") and not non_planned:
        batch_status = "planned"
    elif classifications.get("completed") and len(classifications["completed"]) == len(merged_transport):
        batch_status = "completed"
    else:
        batch_status = "partial" if merged_transport else "empty"

    return {
        "ok": not harness_errors,
        "response_mode": "controlled_batch_passthrough",
        "batch_status": batch_status,
        "source_results": merged_source_results,
        "transport_status_matrix": merged_transport,
        "classifications": classifications,
        "missing_or_failed_sources": merged_missing,
        "harness_errors": harness_errors,
        "safety": {
            "legacy_runner_fallback_attempted": False,
            "manual_batch_curl_fallback_allowed": False,
            "single_action_freeform_attempted": False,
        },
    }


CHAIN_DEFINITIONS: dict[str, dict[str, Any]] = {
    "web_publish_fact": {
        "label": "WEB/发布事实链",
        "required_fields": {"photo_id", "publish_time", "publish_source", "publish_device"},
        "source_ids": {"ato_archives_photo_search"},
        "source_actions": {
            "archives_photo_search",
            "archives_photo_profile",
            "archives_photo_meta",
            "archives_gallery_photo_list",
        },
        "missing_module": "web_publish_fact",
    },
    "web_login_history": {
        "label": "WEB 登录历史链",
        "required_fields": {"login_time", "login_type", "login_source", "device_id", "ip_ua"},
        "source_ids": {"ato_login_logs_search"},
        "missing_module": "web_login_history",
    },
    "device_identity_alignment": {
        "label": "设备一致性链",
        "required_fields": {"device_id", "publish_device", "operation_device"},
        "source_ids": {
            "ato_login_logs_search",
            "ato_archives_photo_search",
            "ato_archives_user_analysis",
            "ato_track_analysis_check_data_ready",
        },
        "source_actions": {
            "login_logs_search",
            "archives_photo_search",
            "archives_photo_profile",
            "archives_photo_meta",
            "archives_user_analysis",
            "track_analysis_check_data_ready",
        },
        "missing_module": "device_history_baseline",
    },
}


PARTIAL_STATE_ORDER = [
    "missing",
    "partial_transport",
    "partial_fields",
    "partial_baseline",
    "partial_consistency",
    "partial_authorization_required",
    "closed",
]


def _chain_has_transport_breakpoint(breakpoints: list[str]) -> bool:
    transport_markers = {
        "response_too_large_needs_window_shrink",
        "service_body_visibility_gap",
        "service_body_visibility_gap_for_truncated_login_log",
        "timeout",
        "auth_failed",
        "parse_error",
        "blocked",
    }
    return any(
        breakpoint in transport_markers
        or "response_too_large" in breakpoint
        or "byte_limit" in breakpoint
        or "visibility_gap" in breakpoint
        for breakpoint in breakpoints
    )


def _partial_subtype_for_chain(
    *,
    chain_id: str,
    extracted_fields: set[str],
    missing_fields_total: list[str],
    breakpoints: list[str],
    relevant: list[dict[str, Any]],
    non_closed_source_seen: bool,
    user_device_entity_resolution: dict[str, Any],
) -> str:
    if not relevant and not extracted_fields:
        return "missing"
    if not missing_fields_total and not non_closed_source_seen and not _chain_has_transport_breakpoint(breakpoints):
        return "closed"
    if _chain_has_transport_breakpoint(breakpoints) and (
        chain_id == "web_login_history" or not extracted_fields
    ):
        return "partial_transport"
    if chain_id == "device_identity_alignment":
        if user_device_entity_resolution.get("multiple_candidate_devices_need_ranking"):
            return "partial_consistency"
        if extracted_fields and ("device_id" in extracted_fields or "publish_device" in extracted_fields):
            return "partial_baseline"
        if user_device_entity_resolution.get("candidate_device_id_missing_after_resolution"):
            return "missing"
    if chain_id == "web_login_history" and extracted_fields and "device_id" in extracted_fields:
        return "partial_baseline"
    if chain_id == "web_publish_fact" and extracted_fields and {"publish_device", "publish_source"} & extracted_fields:
        return "partial_consistency" if not missing_fields_total else "partial_fields"
    if missing_fields_total and extracted_fields:
        return "partial_fields"
    if _chain_has_transport_breakpoint(breakpoints):
        return "partial_transport"
    return "missing"


def _handles_for_fields(observations: list[dict[str, Any]], fields: set[str]) -> list[dict[str, Any]]:
    handles: list[dict[str, Any]] = []
    for observation in observations:
        extracted_fields = set(str(field) for field in observation.get("extracted_business_fields", []))
        for handle in observation.get("parsed_body_field_handles", []):
            canonical = str(handle.get("canonical_field") or handle.get("field") or "")
            if canonical in fields and canonical in extracted_fields:
                handles.append(
                    {
                        "source_id": observation.get("source_id"),
                        "action": observation.get("action"),
                        "field": canonical,
                        "field_path": handle.get("field_path"),
                        "value": handle.get("value"),
                    }
                )
    return handles


def build_chain_status(
    source_observations: list[dict[str, Any]],
    user_device_entity_resolution: dict[str, Any],
) -> dict[str, Any]:
    status: dict[str, Any] = {}
    for chain_id, definition in CHAIN_DEFINITIONS.items():
        required_fields = set(definition["required_fields"])
        source_ids = set(definition["source_ids"])
        source_actions = set(definition.get("source_actions", set()))
        relevant = [
            obs
            for obs in source_observations
            if str(obs.get("source_id")) in source_ids or str(obs.get("action")) in source_actions
        ]
        extracted_fields: set[str] = set()
        missing_by_source: list[dict[str, Any]] = []
        breakpoints: list[str] = []
        non_closed_source_seen = False
        for observation in relevant:
            fields = set(str(field) for field in observation.get("extracted_business_fields", []))
            extracted_fields |= (fields & required_fields)
            missing_fields = sorted(required_fields & set(str(field) for field in observation.get("missing_business_fields", [])))
            quality_class = str(observation.get("quality_class") or "")
            if missing_fields:
                missing_by_source.append(
                    {
                        "source_id": observation.get("source_id"),
                        "action": observation.get("action"),
                        "missing_fields": missing_fields,
                        "breakpoint_type": observation.get("breakpoint_type") or "source_has_no_field",
                    }
                )
                if observation.get("breakpoint_type"):
                    breakpoints.append(str(observation.get("breakpoint_type")))
            if quality_class != "completed":
                non_closed_source_seen = True
                if observation.get("breakpoint_type"):
                    breakpoints.append(str(observation.get("breakpoint_type")))
            elif any(
                flag in set(str(item) for item in observation.get("interpretation_flags", []))
                for flag in {
                    "partial_observation_available",
                    "response_too_large_not_login_evidence",
                    "response_too_large_window_shrink_recommended",
                }
            ):
                non_closed_source_seen = True
                if observation.get("breakpoint_type"):
                    breakpoints.append(str(observation.get("breakpoint_type")))

        if chain_id == "device_identity_alignment" and user_device_entity_resolution.get("candidate_device_id_missing"):
            breakpoints.append("candidate_device_id_missing_after_resolution")
            missing_by_source.append(
                {
                    "source_id": "user_device_entity_resolution",
                    "action": "entity_resolution",
                    "missing_fields": ["candidate_device_id"],
                    "breakpoint_type": "candidate_device_id_missing_after_resolution",
                }
            )

        missing_fields_total = sorted(required_fields - extracted_fields)
        chain_state = _partial_subtype_for_chain(
            chain_id=chain_id,
            extracted_fields=extracted_fields,
            missing_fields_total=missing_fields_total,
            breakpoints=unique_strings(breakpoints),
            relevant=relevant,
            non_closed_source_seen=non_closed_source_seen,
            user_device_entity_resolution=user_device_entity_resolution,
        )
        status[chain_id] = {
            "label": definition["label"],
            "status": chain_state,
            "partial_subtype": None if chain_state in {"closed", "missing"} else chain_state,
            "state_machine": PARTIAL_STATE_ORDER,
            "required_fields": sorted(required_fields),
            "extracted_fields": sorted(extracted_fields),
            "missing_fields": missing_fields_total,
            "field_paths": _handles_for_fields(relevant, required_fields),
            "breakpoint_types": unique_strings(breakpoints)
            or ([] if chain_state == "closed" else ["source_has_no_field"]),
            "missing_by_source": missing_by_source,
            "dynamic_backfill_module": definition["missing_module"] if chain_state != "closed" else None,
        }
    return status


NEXT_HOP_FIELD_GROUPS: dict[str, dict[str, Any]] = {
    "photo_id": {
        "fields": {"photo_id"},
        "sources": [
            ("archives_gallery_photo_list", "用户近期作品列表 / gallery"),
            ("archives_photo_search", "用户近期发布作品列表 / photo_search"),
            ("archives_user_analysis", "用户分析发布相关操作"),
            ("rcp_event_detail", "策略命中或内容事件详情"),
        ],
        "found_status": "photo_id_found",
        "unavailable_status": "photo_source_unavailable",
        "missing_status": "photo_id_missing_after_backfill",
    },
    "publish_time": {
        "fields": {"publish_time"},
        "sources": [
            ("archives_photo_search", "作品列表发布时间"),
            ("archives_user_analysis", "用户分析发布时间"),
            ("rcp_event_detail", "策略命中时间 / 内容事件时间"),
        ],
        "found_status": "publish_time_found",
        "unavailable_status": "publish_time_source_unavailable",
        "missing_status": "publish_time_missing_after_backfill",
    },
    "publish_device": {
        "fields": {"publish_device"},
        "found_actions": {"archives_photo_search", "archives_photo_profile", "archives_photo_meta", "archives_gallery_photo_list"},
        "sources": [
            ("archives_photo_search", "作品发布设备 / 发布端"),
            ("archives_photo_profile", "作品 profile 详情中的发布来源/设备/IP"),
            ("archives_photo_meta", "作品 meta 详情中的 uploadSource/photoMethod/photoIp/publishDevice"),
            ("archives_user_analysis", "操作设备候选，只能进入设备一致性链，不能当作发布设备已补齐"),
            ("weapon_inventory", "Weapon user-device graph"),
            ("track_analysis_check_data_ready", "Track device readiness"),
        ],
        "found_status": "publish_device_found",
        "unavailable_status": "device_source_unavailable",
        "missing_status": "device_missing_after_backfill",
    },
    "login_fields": {
        "fields": {"login_time", "login_type", "login_source", "device_id", "ip_ua"},
        "found_actions": {"login_logs_search"},
        "sources": [
            ("login_logs_search", "统一登录日志 capped 前段 / 缩窗重试"),
            ("archives_user_analysis", "安全操作日志候选时间"),
            ("archives_photo_search", "发布时间反推登录窗口"),
            ("rcp_event_detail", "策略命中时间反推窗口"),
        ],
        "found_status": "login_fields_found",
        "unavailable_status": "service_body_visibility_gap_for_truncated_login_log",
        "missing_status": "login_fields_missing_after_backfill",
    },
    "candidate_device_id": {
        "fields": {"device_id", "publish_device", "operation_device", "candidate_device_id"},
        "sources": [
            ("login_logs_search", "登录设备"),
            ("archives_photo_search", "发布设备"),
            ("archives_photo_profile", "作品 profile 发布设备"),
            ("archives_photo_meta", "作品 meta 发布设备"),
            ("archives_user_analysis", "操作设备"),
            ("archives_user_profile", "历史 / 画像设备"),
            ("weapon_inventory", "user-device graph"),
            ("track_analysis_check_data_ready", "Track getDeviceIds / readiness"),
        ],
        "found_status": "candidate_device_found",
        "unavailable_status": "candidate_device_source_unavailable",
        "missing_status": "candidate_device_id_missing_after_resolution",
    },
}


NEXT_HOP_DECISION_TABLE: dict[str, dict[str, Any]] = {
    "photo_id": {
        "chain_id": "web_publish_fact",
        "current_state": "missing",
        "next_hop_type": "auto_plan_only_next_hop",
        "candidate_actions": ["archives_gallery_photo_list", "archives_photo_search"],
        "required_inputs": ["user_id", "time_window_or_content_anchor"],
        "can_auto_execute": False,
        "requires_user_authorization": False,
        "expected_fields": ["photo_id", "publish_time"],
        "stop_condition": "photo_id_found_or_photo_source_unavailable",
        "fallback_if_failed": "photo_id_missing_after_backfill",
        "source_quality_boundary": "photo_source_no_data_not_ato_exclusion",
    },
    "publish_time": {
        "chain_id": "web_publish_fact",
        "current_state": "partial_fields",
        "next_hop_type": "auto_realtime_next_hop",
        "candidate_actions": ["archives_photo_profile", "archives_photo_meta", "archives_user_analysis"],
        "required_inputs": ["photo_id"],
        "can_auto_execute": True,
        "requires_user_authorization": False,
        "expected_fields": ["publish_time", "publish_source", "publish_device"],
        "stop_condition": "publish_time_or_publish_source_found",
        "fallback_if_failed": "publish_time_missing_after_backfill",
        "source_quality_boundary": "completed_transport_not_business_evidence",
    },
    "publish_device": {
        "chain_id": "web_publish_fact",
        "current_state": "partial_fields",
        "next_hop_type": "auto_realtime_next_hop",
        "candidate_actions": ["archives_photo_profile", "archives_photo_meta"],
        "required_inputs": ["photo_id"],
        "can_auto_execute": True,
        "requires_user_authorization": False,
        "expected_fields": ["publish_device", "publish_source", "publish_ip_ua", "uploadSource", "photoMethod"],
        "stop_condition": "publish_device_or_publish_source_found",
        "fallback_if_failed": "mark_publish_device_missing_after_photo_meta",
        "source_quality_boundary": "completed_transport_not_business_evidence",
    },
    "login_fields": {
        "chain_id": "web_login_history",
        "current_state": "partial_transport",
        "next_hop_type": "auto_realtime_next_hop",
        "candidate_actions": ["login_logs_search"],
        "required_inputs": ["user_id", "anchor_time"],
        "can_auto_execute": True,
        "requires_user_authorization": False,
        "expected_fields": ["login_time", "login_type", "login_source", "device_id", "ip_ua"],
        "stop_condition": "returned_records_not_truncated_or_key_window_covered",
        "fallback_if_failed": "dynamic_offline_module_web_login_history",
        "source_quality_boundary": "byte_limit_partial_source_not_no_data",
    },
    "candidate_device_id": {
        "chain_id": "device_identity_alignment",
        "current_state": "missing",
        "next_hop_type": "auto_realtime_next_hop",
        "candidate_actions": [
            "login_logs_search",
            "archives_photo_profile",
            "archives_photo_meta",
            "archives_user_analysis",
            "track_analysis_check_data_ready",
            "weapon_inventory",
        ],
        "required_inputs": ["user_id", "photo_id_or_login_or_operation_anchor"],
        "can_auto_execute": True,
        "requires_user_authorization": False,
        "expected_fields": ["device_id", "publish_device", "operation_device", "shared_device"],
        "stop_condition": "candidate_device_found_or_resolution_exhausted",
        "fallback_if_failed": "candidate_device_id_missing_after_resolution",
        "source_quality_boundary": "candidate_device_missing_not_low_risk",
    },
}


def _field_values_from_observations(
    source_observations: list[dict[str, Any]],
    fields: set[str],
    *,
    allowed_actions: set[str] | None = None,
) -> list[dict[str, Any]]:
    values: list[dict[str, Any]] = []
    for observation in source_observations:
        if allowed_actions and str(observation.get("action") or "") not in allowed_actions:
            continue
        for handle in observation.get("parsed_body_field_handles", []):
            canonical = str(handle.get("canonical_field") or handle.get("field") or "")
            if canonical not in fields:
                continue
            values.append(
                {
                    "field": canonical,
                    "value": handle.get("value"),
                    "field_path": handle.get("field_path"),
                    "source_id": observation.get("source_id"),
                    "action": observation.get("action"),
                }
            )
    return values


def _source_next_hop_status(action: str, observations_by_action: dict[str, dict[str, Any]]) -> tuple[str, str | None]:
    observation = observations_by_action.get(action, {})
    if not observation:
        return "source_not_in_current_plan_or_not_returned", None
    breakpoint = observation.get("breakpoint_type")
    if breakpoint in {"service_body_visibility_gap", "service_body_visibility_gap_for_truncated_login_log"}:
        return "service_body_visibility_gap", str(breakpoint)
    if observation.get("quality_class") in {"blocked", "timeout", "parse_error", "auth_failed"}:
        return "source_unavailable", str(breakpoint or observation.get("quality_class"))
    if observation.get("extracted_business_fields"):
        return "business_fields_available", str(breakpoint) if breakpoint else None
    if observation.get("dennis_observation", {}).get("parser_input_available"):
        return "parser_mapping_gap", str(breakpoint or "parser_mapping_gap")
    return "business_fields_missing", str(breakpoint or "source_has_no_field")


def _login_window_shrink_plan(source_observations: list[dict[str, Any]], chain_status: dict[str, Any]) -> dict[str, Any]:
    decision = NEXT_HOP_DECISION_TABLE["login_fields"]
    anchors = _field_values_from_observations(
        source_observations,
        {"publish_time", "operation_time", "event_time", "login_time"},
    )
    if anchors:
        return {
            "status": "login_log_truncated_needs_window_shrink",
            "next_hop_type": "auto_realtime_next_hop",
            "can_auto_execute": True,
            "requires_user_authorization": False,
            "candidate_actions": decision["candidate_actions"],
            "required_inputs": decision["required_inputs"],
            "expected_fields": decision["expected_fields"],
            "stop_condition": decision["stop_condition"],
            "fallback_if_failed": decision["fallback_if_failed"],
            "source_quality_boundary": decision["source_quality_boundary"],
            "anchor_status": "window_shrink_anchor_found",
            "anchor_priority": [
                "publish_time",
                "user_claim_time",
                "abnormal_event_time",
                "strategy_hit_time",
                "recent_publish_time",
            ],
            "available_anchors": anchors[:10],
            "recommended_window": "anchor_time +/- 2-6h",
        }
    login_chain = chain_status.get("web_login_history", {})
    if "response_too_large_needs_window_shrink" in set(login_chain.get("breakpoint_types", [])) or (
        "service_body_visibility_gap_for_truncated_login_log" in set(login_chain.get("breakpoint_types", []))
    ):
        return {
            "status": "login_log_window_shrink_anchor_missing",
            "next_hop_type": "auto_plan_only_next_hop",
            "can_auto_execute": False,
            "requires_user_authorization": False,
            "candidate_actions": ["archives_photo_search", "archives_user_analysis", "rcp_event_detail_if_event_id_exists"],
            "required_inputs": ["publish_time_or_event_time_or_user_claim_time"],
            "expected_fields": ["anchor_time"],
            "stop_condition": "anchor_time_found",
            "fallback_if_failed": "dynamic_offline_module_web_login_history",
            "source_quality_boundary": "byte_limit_partial_source_not_no_data",
            "anchor_status": "need_publish_or_event_anchor_before_retry",
            "anchor_priority": [
                "publish_time",
                "user_claim_time",
                "abnormal_event_time",
                "strategy_hit_time",
                "recent_publish_time",
            ],
            "recommended_next_sources": [
                "archives_photo_search",
                "archives_user_analysis",
                "rcp_event_detail_if_event_id_exists",
            ],
        }
    return {
        "status": "not_needed",
        "next_hop_type": "blocked_next_hop",
        "can_auto_execute": False,
        "requires_user_authorization": False,
        "anchor_status": "login_log_not_large_response",
    }


def _photo_detail_next_hop_plan(source_observations: list[dict[str, Any]], chain_status: dict[str, Any]) -> dict[str, Any]:
    decision = NEXT_HOP_DECISION_TABLE["publish_device"]
    photo_values = _field_values_from_observations(source_observations, {"photo_id"})
    photo_ids = unique_strings([str(item.get("value")) for item in photo_values if item.get("value")])
    detail_actions_present = {
        str(obs.get("action"))
        for obs in source_observations
        if str(obs.get("action")) in {"archives_photo_profile", "archives_photo_meta"}
    }
    publish_chain = chain_status.get("web_publish_fact", {})
    if photo_ids and {"archives_photo_profile", "archives_photo_meta"} <= detail_actions_present:
        status = "photo_detail_backfill_consumed"
    elif photo_ids:
        status = "photo_detail_next_hop_required"
    elif publish_chain.get("status") != "closed":
        status = "photo_id_discovery_required"
    else:
        status = "not_needed"
    planned_sources = []
    for photo_id in photo_ids[:5]:
        planned_sources.extend(
            [
                {
                    "source_id": f"photo_profile_{photo_id}",
                    "action": "archives_photo_profile",
                    "params": {"photo_id": photo_id},
                    "execution_group": "auth_sensitive_serial",
                    "failure_policy": "non_blocking_partial",
                    "expected_observation": "photo profile publish source/device/IP/status fields",
                },
                {
                    "source_id": f"photo_meta_{photo_id}",
                    "action": "archives_photo_meta",
                    "params": {"photo_id": photo_id},
                    "execution_group": "auth_sensitive_serial",
                    "failure_policy": "non_blocking_partial",
                    "expected_observation": "photo meta uploadSource/photoMethod/photoIp/publishDevice fields",
                },
            ]
        )
    if not photo_ids and status == "photo_id_discovery_required":
        planned_sources.extend(
            [
                {
                    "source_id": "gallery_photo_list",
                    "action": "archives_gallery_photo_list",
                    "params": {"source": "user_id_or_content_anchor"},
                    "execution_group": "auth_sensitive_serial",
                    "failure_policy": "non_blocking_partial",
                    "expected_observation": "recent gallery photo_id and publish_time candidates",
                },
                {
                    "source_id": "archives_photo_search",
                    "action": "archives_photo_search",
                    "params": {"source": "user_id_time_window"},
                    "execution_group": "auth_sensitive_serial",
                    "failure_policy": "non_blocking_partial",
                    "expected_observation": "photo_id discovery before photo detail follow-up",
                },
            ]
        )
    return {
        "status": status,
        "next_hop_type": (
            "completed_auto_realtime_next_hop"
            if status == "photo_detail_backfill_consumed"
            else "auto_realtime_next_hop"
            if status == "photo_detail_next_hop_required"
            else "auto_plan_only_next_hop"
            if status == "photo_id_discovery_required"
            else "blocked_next_hop"
        ),
        "can_auto_execute": status == "photo_detail_next_hop_required",
        "requires_user_authorization": False,
        "candidate_actions": decision["candidate_actions"] if photo_ids else NEXT_HOP_DECISION_TABLE["photo_id"]["candidate_actions"],
        "required_inputs": decision["required_inputs"] if photo_ids else NEXT_HOP_DECISION_TABLE["photo_id"]["required_inputs"],
        "expected_fields": decision["expected_fields"] if photo_ids else NEXT_HOP_DECISION_TABLE["photo_id"]["expected_fields"],
        "stop_condition": decision["stop_condition"] if photo_ids else NEXT_HOP_DECISION_TABLE["photo_id"]["stop_condition"],
        "fallback_if_failed": decision["fallback_if_failed"] if photo_ids else NEXT_HOP_DECISION_TABLE["photo_id"]["fallback_if_failed"],
        "source_quality_boundary": decision["source_quality_boundary"] if photo_ids else NEXT_HOP_DECISION_TABLE["photo_id"]["source_quality_boundary"],
        "photo_ids": photo_ids[:5],
        "planned_sources": planned_sources,
        "default_runtime_routing": False,
        "manual_curl_or_single_action_fallback_allowed": False,
    }


def build_missing_evidence_next_hops(
    source_observations: list[dict[str, Any]],
    user_device_entity_resolution: dict[str, Any],
    chain_status: dict[str, Any],
) -> dict[str, Any]:
    observations_by_action = {str(obs.get("action")): obs for obs in source_observations}
    chain_missing_fields = {
        field
        for chain in chain_status.values()
        if isinstance(chain, dict)
        for field in chain.get("missing_fields", [])
    }
    groups: list[dict[str, Any]] = []
    for group_id, definition in NEXT_HOP_FIELD_GROUPS.items():
        group_fields = set(definition["fields"])
        if not (chain_missing_fields & group_fields):
            continue
        found_actions = definition.get("found_actions")
        found_values = _field_values_from_observations(
            source_observations,
            group_fields,
            allowed_actions=set(found_actions) if found_actions else None,
        )
        attempts: list[dict[str, Any]] = []
        source_visibility_gap = False
        for action, purpose in definition["sources"]:
            status, breakpoint = _source_next_hop_status(action, observations_by_action)
            if status == "service_body_visibility_gap":
                source_visibility_gap = True
            attempts.append(
                {
                    "action": action,
                    "purpose": purpose,
                    "status": status,
                    "breakpoint_type": breakpoint,
                }
            )
        if found_values:
            status = definition["found_status"]
        elif group_id == "candidate_device_id" and user_device_entity_resolution.get(
            "candidate_device_id_missing_after_resolution"
        ):
            status = definition["missing_status"]
        elif source_visibility_gap:
            status = definition["unavailable_status"]
        else:
            status = definition["missing_status"]
        decision = dict(NEXT_HOP_DECISION_TABLE.get(group_id, {}))
        if status == definition.get("found_status"):
            next_hop_type = "completed_auto_realtime_next_hop"
            can_auto_execute = False
        elif group_id == "photo_id" and not found_values:
            next_hop_type = "auto_plan_only_next_hop"
            can_auto_execute = False
        else:
            next_hop_type = str(decision.get("next_hop_type") or "auto_plan_only_next_hop")
            can_auto_execute = bool(decision.get("can_auto_execute")) and next_hop_type == "auto_realtime_next_hop"
        groups.append(
            {
                "group_id": group_id,
                "missing_fields": sorted(chain_missing_fields & group_fields),
                "status": status,
                "chain_id": decision.get("chain_id"),
                "current_state": decision.get("current_state"),
                "next_hop_type": next_hop_type,
                "candidate_actions": decision.get("candidate_actions", []),
                "required_inputs": decision.get("required_inputs", []),
                "can_auto_execute": can_auto_execute,
                "requires_user_authorization": bool(decision.get("requires_user_authorization", False)),
                "expected_fields": decision.get("expected_fields", []),
                "stop_condition": decision.get("stop_condition"),
                "fallback_if_failed": decision.get("fallback_if_failed"),
                "source_quality_boundary": decision.get("source_quality_boundary"),
                "found_values": found_values[:10],
                "next_hop_attempts": attempts,
                "no_new_platform_action_added": True,
            }
        )

    if user_device_entity_resolution.get("candidate_device_id_missing_after_resolution") and not any(
        group.get("group_id") == "candidate_device_id" for group in groups
    ):
        groups.append(
            {
                "group_id": "candidate_device_id",
                "missing_fields": ["candidate_device_id"],
                "status": "candidate_device_id_missing_after_resolution",
                "chain_id": "device_identity_alignment",
                "current_state": "missing",
                "next_hop_type": "auto_realtime_next_hop",
                "candidate_actions": NEXT_HOP_DECISION_TABLE["candidate_device_id"]["candidate_actions"],
                "required_inputs": NEXT_HOP_DECISION_TABLE["candidate_device_id"]["required_inputs"],
                "can_auto_execute": True,
                "requires_user_authorization": False,
                "expected_fields": NEXT_HOP_DECISION_TABLE["candidate_device_id"]["expected_fields"],
                "stop_condition": NEXT_HOP_DECISION_TABLE["candidate_device_id"]["stop_condition"],
                "fallback_if_failed": NEXT_HOP_DECISION_TABLE["candidate_device_id"]["fallback_if_failed"],
                "source_quality_boundary": NEXT_HOP_DECISION_TABLE["candidate_device_id"]["source_quality_boundary"],
                "found_values": [],
                "next_hop_attempts": user_device_entity_resolution.get("next_hop_attempts", []),
                "no_new_platform_action_added": True,
            }
        )

    return {
        "planner_version": "missing_evidence_next_hop_v1",
        "active_backfill_attempted": True,
        "generic_pattern": [
            "missing_entity_to_entity_resolution",
            "missing_time_anchor_to_behavior_event_strategy_anchor",
            "large_response_to_capped_parse_then_window_shrink",
            "completed_transport_to_body_visibility_or_parser_mapping_gap",
            "new_evidence_to_chain_recompute",
        ],
        "groups": groups,
        "photo_detail_next_hop_plan": _photo_detail_next_hop_plan(source_observations, chain_status),
        "login_window_shrink_plan": _login_window_shrink_plan(source_observations, chain_status),
        "dataagent_hive_called": False,
        "service_normalizer_restored": False,
    }


def recompute_conclusion_state(
    *,
    mode: str,
    chain_status: dict[str, Any],
    source_observations: list[dict[str, Any]],
) -> dict[str, Any]:
    if mode == "dry_run":
        return {
            "conclusion_state": "not_judged_dry_run",
            "final_status": "dry_run",
            "reason": "dry_run_source_plan_only",
            "recomputed_after_backfill": True,
        }
    chain_states = {chain_id: str(chain.get("status")) for chain_id, chain in chain_status.items()}
    extracted_field_count = sum(len(obs.get("extracted_business_fields", [])) for obs in source_observations)
    closed_count = sum(1 for state in chain_states.values() if state == "closed")
    partial_count = sum(1 for state in chain_states.values() if state.startswith("partial_"))
    if closed_count == len(chain_status) and extracted_field_count:
        conclusion_state = "likely_risk"
        reason = "core_chains_closed_but_business_abnormality_still_requires_value_interpretation"
    elif closed_count + partial_count >= 2 and extracted_field_count:
        conclusion_state = "insufficient_support"
        reason = "some_business_fields_available_but_core_chain_not_closed"
    else:
        conclusion_state = "insufficient_support"
        reason = "core_chains_missing_or_body_visibility_gap"
    return {
        "conclusion_state": conclusion_state,
        "final_status": "partial" if conclusion_state != "no_risk_supported" else "answered",
        "reason": reason,
        "chain_states": chain_states,
        "extracted_business_field_count": extracted_field_count,
        "recomputed_after_backfill": True,
        "allowed_states": [
            "confirmed_risk",
            "likely_risk",
            "insufficient_support",
            "likely_false_positive",
            "no_risk_supported",
        ],
        "caveats_preserved": [
            "no_data_not_risk_exclusion",
            "completed_transport_not_business_evidence",
            "partial_not_final",
            "body_visibility_gap_not_business_no_data",
            "strategy_hit_not_final_judgement",
        ],
    }


def build_live_response_inspection(
    source_plan: list[SourcePlanItem],
    batch_result_raw: dict[str, Any],
    source_observations: list[dict[str, Any]],
    evidence_card: dict[str, Any],
) -> list[dict[str, Any]]:
    observations_by_source = {str(obs.get("source_id")): obs for obs in source_observations}
    rows_by_id = _rows_by_source_id_from_batch(batch_result_raw)
    consumed_sources: set[str] = set()
    for chain in evidence_card.get("evidence_chain", {}).values():
        if not isinstance(chain, dict):
            continue
        for observation in chain.get("observations", []) or []:
            if isinstance(observation, dict) and observation.get("source_id"):
                consumed_sources.add(str(observation.get("source_id")))

    rows: list[dict[str, Any]] = []
    inspection_items = [
        {"source_id": item.source_id, "action": item.action}
        for item in source_plan
    ]
    seen_inspection_ids = {item["source_id"] for item in inspection_items}
    for observation in source_observations:
        source_id = str(observation.get("source_id") or "")
        if not source_id or source_id in seen_inspection_ids:
            continue
        inspection_items.append({"source_id": source_id, "action": str(observation.get("action") or "")})
        seen_inspection_ids.add(source_id)

    for item in inspection_items:
        source_id = str(item["source_id"])
        action = str(item["action"])
        payload = rows_by_id.get(source_id, {})
        row = payload.get("transport") if isinstance(payload.get("transport"), dict) else payload
        observation = observations_by_source.get(source_id, {})
        dennis_observation = observation.get("dennis_observation", {}) if isinstance(observation, dict) else {}
        rows.append(
            {
                "source_id": source_id,
                "action": action,
                "status": row.get("source_status") or row.get("category"),
                "body_present": row.get("body_present"),
                "body_truncated": row.get("body_truncated"),
                "observed_bytes": row.get("observed_bytes"),
                "raw_body_handling": row.get("raw_body_handling"),
                "visible_body_keys": dennis_observation.get("visible_body_keys", []),
                "parser_input_available": bool(dennis_observation.get("parser_input_available")),
                "extracted_business_fields": observation.get("extracted_business_fields", []),
                "field_paths": [
                    {
                        "field": handle.get("canonical_field") or handle.get("field"),
                        "field_path": handle.get("field_path"),
                    }
                    for handle in observation.get("parsed_body_field_handles", [])
                    if (handle.get("canonical_field") or handle.get("field"))
                    in {
                        "photo_id",
                        "publish_time",
                        "publish_source",
                        "publish_device",
                        "publish_ip_ua",
                        "login_time",
                        "login_type",
                        "login_source",
                        "device_id",
                        "ip_ua",
                        "operation_time",
                        "operation_type",
                        "security_action_type",
                        "operation_device",
                    }
                ],
                "evidence_card_consumed": source_id in consumed_sources,
                "chain_coverage": observation.get("chain_section"),
                "breakpoint_type": observation.get("breakpoint_type"),
            }
        )
    return rows


def render_user_answer_draft(evidence_card: dict[str, Any]) -> str:
    chain_status = evidence_card.get("chain_status", {})
    active_plan = evidence_card.get("active_backfill_plan", {})
    modules = [
        option.get("module_id")
        for option in evidence_card.get("offline_backfill_recommendation", {}).get("options", [])
        if option.get("module_id")
    ]

    def line(chain_id: str) -> str:
        chain = chain_status.get(chain_id, {})
        label = chain.get("label", chain_id)
        status = chain.get("status", "missing")
        missing = ", ".join(chain.get("missing_fields", [])) or "none"
        reasons = ", ".join(chain.get("breakpoint_types", [])) or "unknown_gap"
        return f"- {label}: {status}; missing={missing}; breakpoint={reasons}"

    active_groups = [
        f"{group.get('group_id')}={group.get('status')}({group.get('next_hop_type', 'next_hop')})"
        for group in active_plan.get("groups", [])
        if group.get("group_id")
    ]
    auto_next_hops = [
        group.get("group_id")
        for group in active_plan.get("groups", [])
        if group.get("can_auto_execute")
    ]
    authorized_modules = [
        option.get("module_id")
        for option in evidence_card.get("offline_backfill_recommendation", {}).get("options", [])
        if option.get("requires_user_authorization")
    ]
    shrink_plan = active_plan.get("login_window_shrink_plan", {})
    shrink_line = (
        f"登录日志缩窗：{shrink_plan.get('status')}"
        if shrink_plan.get("status") and shrink_plan.get("status") != "not_needed"
        else "登录日志缩窗：当前无可执行缩窗锚点或暂不需要"
    )
    conclusion_state = evidence_card.get("conclusion_state", "insufficient_support")
    conclusion_text = (
        "目前不能确认被盗，也不能排除被盗"
        if conclusion_state == "insufficient_support"
        else f"当前结论状态为 {conclusion_state}"
    )

    return "\n".join(
        [
            f"一句话判断：{conclusion_text}；结论状态是 {conclusion_state}。",
            "三条证据链状态：",
            line("web_publish_fact"),
            line("web_login_history"),
            line("device_identity_alignment"),
            "Dennis 已主动补证/回填：" + (", ".join(active_groups) if active_groups else "当前没有可用下一跳"),
            "可自动 next-hop：" + (", ".join(auto_next_hops) if auto_next_hops else "无；缺输入或需授权"),
            "需用户授权：" + (", ".join(authorized_modules) if authorized_modules else "无离线授权项"),
            shrink_line,
            "关键边界：transport completed 不等于业务链闭合；no_data/partial/auth gap 不是低风险反证。",
            "下一步补证模块：" + (", ".join(modules) if modules else "当前缺口未生成离线模块"),
            "处置建议：不建议强处置，可进入人工复核或轻保护策略；DataAgent/Hive 需用户按 module_id 单独授权。",
        ]
    )


def build_evidence_card(
    task: str,
    user_id: str,
    mode: str,
    source_quality_matrix: dict[str, Any],
    source_observations: list[dict[str, Any]],
    user_device_entity_resolution: dict[str, Any],
    missing_evidence: list[dict[str, Any]],
) -> dict[str, Any]:
    buckets = source_quality_matrix["buckets"]
    completed = buckets.get("completed", [])
    partial = buckets.get("partial", [])
    blockers = (
        buckets.get("blocked", [])
        + buckets.get("timeout", [])
        + buckets.get("parse_error", [])
        + buckets.get("auth_failed", [])
    )

    observations_by_section: dict[str, list[dict[str, Any]]] = {}
    for observation in source_observations:
        section = str(observation.get("chain_section") or "source_quality")
        observations_by_section.setdefault(section, []).append(observation)

    chain_status = build_chain_status(source_observations, user_device_entity_resolution)
    active_backfill_plan = build_missing_evidence_next_hops(
        source_observations,
        user_device_entity_resolution,
        chain_status,
    )
    conclusion_recompute = recompute_conclusion_state(
        mode=mode,
        chain_status=chain_status,
        source_observations=source_observations,
    )
    conclusion_state = str(conclusion_recompute["conclusion_state"])
    final_status = str(conclusion_recompute["final_status"])

    offline_backfill = build_dynamic_offline_backfill_recommendation(
        source_observations,
        user_device_entity_resolution,
        missing_evidence,
        chain_status,
    )
    business_evidence_candidates = [
        {
            "source_id": observation.get("source_id"),
            "action": observation.get("action"),
            "chain_section": observation.get("chain_section"),
            "extracted_business_fields": observation.get("extracted_business_fields", []),
            "observed_field_handles": observation.get("observed_field_handles", []),
        }
        for observation in source_observations
        if observation.get("evidence_use") == "business_evidence_candidate"
    ]
    transport_only_boundaries = [
        {
            "source_id": observation.get("source_id"),
            "action": observation.get("action"),
            "chain_section": observation.get("chain_section"),
            "missing_business_fields": observation.get("missing_business_fields", []),
            "interpretation_flags": observation.get("interpretation_flags", []),
        }
        for observation in source_observations
        if observation.get("evidence_use") == "transport_only_boundary"
    ]
    evidence_projection_summary = []
    for observation in source_observations:
        projection = observation.get("dennis_observation", {}).get("evidence_projection")
        if not isinstance(projection, dict) or not projection.get("projection_applied"):
            continue
        evidence_projection_summary.append(
            {
                "source_id": observation.get("source_id"),
                "action": observation.get("action"),
                "projection_applied": True,
                "projection_not_business_normalizer": True,
                "raw_body_not_retained_in_answer": True,
                "projected_records": projection.get("projected_records"),
                "dropped_fields_count": projection.get("dropped_fields_count"),
                "sensitive_fields_projected_as_handles": projection.get("sensitive_fields_projected_as_handles"),
                "strict_pii_fields_redacted": projection.get("strict_pii_fields_redacted"),
                "retained_field_paths": projection.get("retained_field_paths", [])[:30],
            }
        )
    chain_missing = [
        {
            "chain": "web_or_abnormal_publish_fact",
            "missing": "WEB/异常端发布事实未闭合：publish_time/publish_source/publish_device/publish_ip_ua/photo_id",
            "source_ids": ["ato_archives_photo_search", "ato_archives_user_analysis"],
        },
        {
            "chain": "web_history_baseline",
            "missing": "WEB/H5/PC/token/OAuth/扫码登录是否历史常用未闭合",
            "source_ids": ["ato_login_logs_search"],
        },
        {
            "chain": "device_identity_alignment",
            "missing": "发布设备、登录设备、用户设备反查和历史设备基线一致性未闭合",
            "source_ids": ["ato_login_logs_search", "ato_archives_photo_search", "ato_track_analysis_check_data_ready", "user_device_entity_resolution"],
        },
        {
            "chain": "control_entry",
            "missing": "closed login/control-chain evidence with login_type/device/IP/UA/window coverage",
            "source_ids": ["ato_login_logs_search"],
        },
        {
            "chain": "post_action_or_security_timeline",
            "missing": "改密、换绑、保护账号、资料修改、私信/关注/发布后置行为时间线未闭合",
            "source_ids": ["ato_archives_user_analysis"],
        },
    ]
    if user_device_entity_resolution.get("candidate_device_id_missing"):
        chain_missing.append(
            {
                "chain": "device_ip_spread",
                "missing": "candidate_device_id for Track/Weapon/publish-device alignment",
                "source_ids": ["user_device_entity_resolution"],
            }
        )
    return {
        "case_id": _compact_case_id(task, user_id),
        "task": task,
        "user_id": user_id,
        "final_status": final_status,
        "conclusion_state": conclusion_state,
        "organization": "ato_risk_chain_not_flat_source_status",
        "core_chain_order": [
            "web_or_abnormal_publish_fact",
            "web_history_baseline",
            "device_identity_alignment",
            "control_entry",
            "account_state_and_post_actions",
            "frontend_backend_activity_alignment",
            "strategy_risk_signal",
            "counter_evidence_and_gaps",
            "conclusion_boundary",
        ],
        "chain_status": chain_status,
        "active_backfill_plan": active_backfill_plan,
        "conclusion_recompute": conclusion_recompute,
        "evidence_projection_summary": evidence_projection_summary,
        "evidence_chain": {
            "web_or_abnormal_publish_fact": {
                "question": "是否存在 WEB/异常端发布或导流内容承接",
                "observations": observations_by_section.get("content_publish_handoff", []),
                "boundary": "只有提取到 publish_time/publish_source/publish_device/photo_id 等业务字段才进入证据；transport completed 不等于发布链闭合",
            },
            "web_history_baseline": {
                "question": "WEB/H5/PC/token/OAuth/扫码登录是否历史常用",
                "observations": observations_by_section.get("control_entry", []),
                "boundary": "登录日志 no_data/response_too_large/window gap 只说明当前实时窗口或解析受限，不能排除 ATO",
            },
            "device_identity_alignment": {
                "question": "发布设备、登录设备、用户设备反查是否一致",
                "user_device_entity_resolution": user_device_entity_resolution,
                "observations": observations_by_section.get("device_ip_spread", [])
                + observations_by_section.get("frontend_backend_activity_alignment", []),
                "boundary": "candidate_device_id_missing 是缺可用于对齐的设备实体，不是只缺风险设备",
            },
            "control_entry": {
                "question": "是否存在异常登录/控制权入口",
                "observations": observations_by_section.get("control_entry", []),
                "boundary": "login no_data/response_too_large/window gap cannot exclude ATO",
            },
            "account_state_and_post_actions": {
                "question": "控制权变化后是否出现改密、换绑、保护账号、资料修改或后置行为",
                "observations": observations_by_section.get("account_state_and_post_actions", []),
                "boundary": "profile is baseline context; completed transport is not business closure",
            },
            "content_publish_handoff": {
                "question": "是否有作品/发布/导流内容承接",
                "observations": observations_by_section.get("content_publish_handoff", []),
                "boundary": "photo_search no_data cannot exclude abnormal publish or diversion",
            },
            "frontend_backend_activity_alignment": {
                "question": "前端活跃是否能与后端登录/发布对齐",
                "observations": observations_by_section.get("frontend_backend_activity_alignment", []),
                "boundary": "Track readiness is auxiliary provenance, not owner proof",
            },
            "device_ip_spread": {
                "question": "候选设备/IP/扩散线索是否支持控制端异常",
                "user_device_entity_resolution": user_device_entity_resolution,
                "observations": observations_by_section.get("device_ip_spread", []),
                "boundary": "same device or device risk is not a gang/ATO conclusion by itself",
            },
            "strategy_risk_signal": {
                "question": "策略/风控信号是否提供旁证",
                "observations": observations_by_section.get("strategy_risk_signal", []),
                "boundary": "strategy hit is auxiliary evidence and cannot alone decide ATO",
            },
            "counter_evidence_and_gaps": {
                "counter_evidence": [],
                "missing_chain_evidence": chain_missing,
                "transport_only_boundaries": transport_only_boundaries,
                "source_quality_boundary": (
                    "no_data, partial, auth_failed, blocked, timeout and parse_error are not low-risk counter evidence"
                ),
            },
            "conclusion_boundary": {
                "final_status": final_status,
                "conclusion_state": conclusion_state,
                "evidence_based_final_conclusion_allowed": False,
                "reason": "control entry, post-action/content handoff, device identity, and baseline chain are not fully closed",
            },
        },
        "completed_sources": completed,
        "partial_sources": partial,
        "blocked_or_failed_sources": blockers,
        "no_data_sources": buckets.get("no_data", []),
        "planned_sources": buckets.get("planned", []),
        "strong_evidence": [],
        "medium_evidence": business_evidence_candidates,
        "weak_evidence": [],
        "counter_evidence": [],
        "missing_evidence": missing_evidence,
        "caveats": [
            "no_data, timeout, auth_failed, blocked, parse_error, and partial observations are not low-risk counter evidence",
            "Track activity, if available, is auxiliary provenance only and cannot prove owner operation",
            "DataAgent/Hive was not called; offline evidence requires per-request authorization",
        ],
        "offline_backfill_recommendation": offline_backfill,
    }


def load_rounds_payload(rounds_json: str | None) -> dict[str, Any]:
    if not rounds_json:
        raise ValueError("--rounds-json is required for sample_expand_validate_batch")
    stripped = rounds_json.strip()
    if stripped.startswith("{") or stripped.startswith("["):
        return json.loads(stripped)
    candidate_path = Path(rounds_json)
    if candidate_path.exists():
        return json.loads(candidate_path.read_text(encoding="utf-8"))
    return json.loads(stripped)


def _looks_like_forbidden_entity(value: str) -> bool:
    lowered = value.lower()
    forbidden_fragments = [
        "http://",
        "https://",
        "cookie",
        "token",
        "session",
        "header",
        "authorization",
        "password",
    ]
    return any(fragment in lowered for fragment in forbidden_fragments)


def validate_sample_expand_rounds_payload(
    payload: dict[str, Any],
    *,
    max_rounds_arg: int | None,
    max_deep_checked_arg: int | None,
) -> dict[str, Any]:
    errors: list[str] = []
    route_mode = payload.get("route_mode")
    if route_mode != "sample_expand_validate_mode":
        errors.append("route_mode_must_be_sample_expand_validate_mode")

    round_size = int(payload.get("round_size") or 10)
    max_rounds = int(max_rounds_arg or payload.get("max_rounds") or 5)
    planned_rounds = int(payload.get("planned_rounds_this_run") or 0)
    max_deep_checked = int(max_deep_checked_arg or payload.get("max_deep_checked_this_run") or 50)
    rounds = payload.get("rounds")
    if not isinstance(rounds, list) or not rounds:
        errors.append("rounds_required")
        rounds = []
    if planned_rounds and planned_rounds > max_rounds:
        errors.append("planned_rounds_this_run_exceeds_max_rounds")
    if len(rounds) > max_rounds:
        errors.append("round_count_exceeds_max_rounds")

    total_entities = 0
    for round_item in rounds:
        if not isinstance(round_item, dict):
            errors.append("round_item_must_be_object")
            continue
        sampled_entities = round_item.get("sampled_entities")
        if not isinstance(sampled_entities, list) or not sampled_entities:
            errors.append(f"sampled_entities_required_round_{round_item.get('round_id')}")
            continue
        if len(sampled_entities) > round_size:
            errors.append(f"round_{round_item.get('round_id')}_entity_count_exceeds_round_size")
        total_entities += len(sampled_entities)
        for entity in sampled_entities:
            if not isinstance(entity, str) or not entity.strip():
                errors.append(f"round_{round_item.get('round_id')}_entity_must_be_non_empty_string")
                continue
            if _looks_like_forbidden_entity(entity):
                errors.append(f"round_{round_item.get('round_id')}_forbidden_entity_material")
    if total_entities > max_deep_checked:
        errors.append("total_deep_checked_exceeds_max_deep_checked_this_run")

    return {
        "valid": not errors,
        "errors": errors,
        "route_mode": route_mode,
        "round_size": round_size,
        "max_rounds": max_rounds,
        "planned_rounds_this_run": planned_rounds or len(rounds),
        "max_deep_checked_this_run": max_deep_checked,
        "total_deep_checked_requested": total_entities,
    }


def disabled_actions_for_sample_batch(args: argparse.Namespace, rounds_payload: dict[str, Any]) -> set[str]:
    disabled = {
        str(action).strip()
        for action in rounds_payload.get("disabled_actions", [])
        if str(action).strip()
    } if isinstance(rounds_payload.get("disabled_actions"), list) else set()
    for action in getattr(args, "disable_action", []) or []:
        action_text = str(action).strip()
        if action_text:
            disabled.add(action_text)
    if getattr(args, "skip_login_logs", False):
        disabled.add("login_logs_search")
    return disabled


def _batch_source_id(round_id: int, index: int, source: str) -> str:
    return f"round_{round_id}_entity_{index}_{source}"


def build_sample_round_source_plan(
    round_id: int,
    sampled_entities: list[str],
    *,
    window_start_ms: int,
    window_end_ms: int,
    disabled_actions: set[str] | None = None,
) -> list[SourcePlanItem]:
    disabled_actions = disabled_actions or set()
    login_start_ms, login_end_ms = _bounded_source_window(
        window_start_ms,
        window_end_ms,
        LOGIN_LOG_RELIABLE_WINDOW_DAYS,
    )
    track_start_ms, track_end_ms = _bounded_source_window(
        window_start_ms,
        window_end_ms,
        TRACK_READINESS_WINDOW_DAYS,
    )
    items: list[SourcePlanItem] = []
    for index, entity in enumerate(sampled_entities, start=1):
        common_user_params = {"user_id": entity}
        items.extend(
            [
                SourcePlanItem(
                    source_id=_batch_source_id(round_id, index, "archives_profile"),
                    action="archives_user_profile",
                    execution_group="independent_parallel",
                    depends_on=[],
                    timeout_class="auth_sensitive",
                    failure_policy="non_blocking_partial",
                    source_priority="P0",
                    expected_observation="archive/admin profile baseline for entity graph and account status",
                    params={**common_user_params, "mode": "archives_user_home_profile"},
                    timeout_ms=30_000,
                    required_fields=["user_id"],
                    window_policy="profile_current_state_no_7d_login_window_constraint",
                    window_start_ms=window_start_ms,
                    window_end_ms=window_end_ms,
                ),
                SourcePlanItem(
                    source_id=_batch_source_id(round_id, index, "weapon"),
                    action="weapon_inventory",
                    execution_group="independent_parallel",
                    depends_on=[],
                    timeout_class="standard_readonly",
                    failure_policy="non_blocking_partial",
                    source_priority="P0",
                    expected_observation="user-device graphData/riskData summary for entity_resolution_first",
                    params={
                        **common_user_params,
                        "mode": "batch_user_device_graph_summary",
                        "include_risk_data": True,
                        "max_device_ids": 10,
                    },
                    timeout_ms=30_000,
                    required_fields=["user_id"],
                    window_policy="current_user_device_graph_window",
                    window_start_ms=window_start_ms,
                    window_end_ms=window_end_ms,
                ),
                SourcePlanItem(
                    source_id=_batch_source_id(round_id, index, "photo"),
                    action="archives_photo_search",
                    execution_group="auth_sensitive_serial",
                    depends_on=[_batch_source_id(round_id, index, "archives_profile")],
                    timeout_class="auth_sensitive",
                    failure_policy="non_blocking_partial",
                    source_priority="P0",
                    expected_observation="content/diversion photo anchors, publish time/source/device, and no_data boundary",
                    params={**common_user_params, "begin": window_start_ms, "end": window_end_ms, "page": 1, "count": 20},
                    timeout_ms=30_000,
                    required_fields=["user_id"],
                    window_policy="archives_scene_window_not_constrained_by_login_logs_7d",
                    window_start_ms=window_start_ms,
                    window_end_ms=window_end_ms,
                ),
                SourcePlanItem(
                    source_id=_batch_source_id(round_id, index, "login"),
                    action="login_logs_search",
                    execution_group="independent_parallel",
                    depends_on=[],
                    timeout_class="standard_readonly",
                    failure_policy="non_blocking_partial",
                    source_priority="P0-conditional",
                    expected_observation="login/protocol/ATO-like control-chain summary for batch commonality",
                    params={
                        **common_user_params,
                        "from_timestamp": login_start_ms,
                        "to_timestamp": login_end_ms,
                        "recallSource": DEFAULT_RECALL_SOURCE,
                        "max_records": 50,
                    },
                    timeout_ms=45_000,
                    required_fields=["user_id"],
                    window_policy="login_logs_reliable_online_window_7d_or_playbook_override",
                    window_start_ms=login_start_ms,
                    window_end_ms=login_end_ms,
                ),
                SourcePlanItem(
                    source_id=_batch_source_id(round_id, index, "strategy"),
                    action="rcp_fast_query_hbase",
                    execution_group="independent_parallel",
                    depends_on=[],
                    timeout_class="standard_readonly",
                    failure_policy="non_blocking_partial",
                    source_priority="P1",
                    expected_observation="user/source_id recent strategy hit discovery; strategy hit is not final judgement",
                    params={
                        "source_id": entity,
                        "startTime": window_start_ms,
                        "endTime": window_end_ms,
                        "eventTypeCodes": "",
                        "limit": 100,
                    },
                    timeout_ms=30_000,
                    required_fields=["source_id", "startTime", "endTime"],
                    window_policy="strategy_hit_discovery_by_user_source_id_recent_window",
                    window_start_ms=window_start_ms,
                    window_end_ms=window_end_ms,
                ),
            ]
        )
    return [item for item in items if item.action not in disabled_actions]


def split_executable_and_skipped(source_plan: list[SourcePlanItem]) -> tuple[list[SourcePlanItem], list[SourcePlanItem]]:
    executable: list[SourcePlanItem] = []
    skipped: list[SourcePlanItem] = []
    for item in source_plan:
        if _missing_fields(item):
            skipped.append(item)
        else:
            executable.append(item)
    return executable, skipped


def build_round_entity_graph(
    round_id: int,
    sampled_entities: list[str],
    source_quality_matrix: dict[str, Any],
    source_observations: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    completed_weapon = [
        row["source_id"]
        for row in source_quality_matrix.get("per_source", [])
        if row.get("action") == "weapon_inventory" and row.get("quality_class") == "completed"
    ]
    blocked_weapon = [
        row["source_id"]
        for row in source_quality_matrix.get("per_source", [])
        if row.get("action") == "weapon_inventory" and row.get("quality_class") != "completed"
    ]
    device_candidates = _candidate_devices_by_round_entity(round_id, sampled_entities, source_observations or [])
    user_device_edges: list[dict[str, Any]] = []
    expanded_devices: list[str] = []
    for index, entity in enumerate(sampled_entities, start=1):
        for candidate in device_candidates.get(index, []):
            device_id = str(candidate.get("device_id") or "")
            if not device_id:
                continue
            expanded_devices.append(device_id)
            user_device_edges.append(
                {
                    "user_id": entity,
                    "device_id": device_id,
                    "source_id": candidate.get("source_id"),
                    "field_path": candidate.get("field_path"),
                }
            )
    expanded_devices = unique_strings(expanded_devices)
    unresolved = [
        entity
        for index, entity in enumerate(sampled_entities, start=1)
        if not device_candidates.get(index)
    ]
    return {
        "round_id": round_id,
        "input_users": sampled_entities,
        "input_devices": [],
        "expanded_users": sampled_entities,
        "expanded_devices": expanded_devices,
        "user_device_edges": user_device_edges,
        "high_degree_devices": [],
        "high_degree_users": [],
        "unresolved_entities": unresolved,
        "entity_resolution_source": ["weapon_inventory"],
        "entity_resolution_quality": (
            "business_edges_extracted"
            if user_device_edges else
            "planned_or_partial"
            if blocked_weapon or completed_weapon else
            "not_evaluated_in_dry_run"
        ),
        "missing_or_blocked_reason": None if user_device_edges else "no parsed user-device graph edge in current round",
    }


def build_source_completion(source_quality_matrix: dict[str, Any]) -> dict[str, Any]:
    buckets = source_quality_matrix.get("buckets", {})
    return {
        "completed_sources": buckets.get("completed", []),
        "skipped_sources": [
            row.get("source_id")
            for row in source_quality_matrix.get("per_source", [])
            if row.get("quality_class") == "blocked" and row.get("error_type") == "missing_required_fields"
        ],
        "blocked_sources": buckets.get("blocked", []),
        "timeout_sources": buckets.get("timeout", []),
        "no_data_sources": buckets.get("no_data", []),
        "auth_failed_sources": buckets.get("auth_failed", []),
        "parse_error_sources": buckets.get("parse_error", []),
        "partial_sources": buckets.get("partial", []),
        "planned_sources": buckets.get("planned", []),
        "source_window_boundary": "recent_7d_scene_with_source_specific_windows",
        "fallback_used": False,
    }


def build_batch_source_commonality_cards(
    source_quality_matrix: dict[str, Any],
    sampled_count: int,
    source_observations: list[dict[str, Any]] | None = None,
    disabled_actions: set[str] | None = None,
) -> list[dict[str, Any]]:
    disabled_actions = disabled_actions or set()
    actions = [
        ({"login_logs_search"}, "login_log"),
        ({"archives_user_profile"}, "archive_admin_profile"),
        ({"weapon_inventory"}, "weapon_graph_risk"),
        ({"archives_photo_search", "archives_gallery_photo_list", "archives_photo_profile", "archives_photo_meta"}, "content_action_anchor"),
        ({"rcp_fast_query_hbase"}, "strategy_hit"),
        ({"rcp_snapshot"}, "strategy_hit_detail"),
        ({"track_analysis_check_data_ready"}, "track_frontend_behavior"),
        ({"archives_negative_report", "archives_user_report_search"}, "feedback_signal"),
        ({"archives_punish_status", "archives_review_logs"}, "enforcement_review"),
    ]
    source_summary_fields = {
        "login_logs_search": {"login_type", "login_source", "device_id", "ip_ua", "operation_type"},
        "archives_user_profile": {"account_status", "profile_status", "risk_label"},
        "weapon_inventory": {"device_id", "candidate_device_id", "risk_label", "linked_user_count"},
        "archives_photo_search": {"photo_id", "publish_time", "publish_source", "publish_device"},
        "archives_gallery_photo_list": {"photo_id", "publish_time", "publish_source", "publish_device"},
        "archives_photo_profile": {"photo_id", "publish_time", "publish_source", "publish_device", "publish_ip", "publish_ua"},
        "archives_photo_meta": {"photo_id", "publish_time", "publish_source", "publish_device", "publish_ip", "publish_ua"},
        "rcp_fast_query_hbase": {"event_type", "event_time", "policy_code", "hit_policy", "risk_decision"},
        "rcp_snapshot": {"event_type", "event_time", "policy_code", "hit_policy", "risk_decision"},
        "track_analysis_check_data_ready": {"device_id", "track_data_ready", "active_status", "event_type"},
        "archives_negative_report": {"report_id", "report_type", "report_time", "feedback_signal"},
        "archives_user_report_search": {"report_id", "report_type", "report_time", "feedback_signal"},
        "archives_punish_status": {"punish_id", "punish_type", "punish_time", "enforcement_action"},
        "archives_review_logs": {"review_id", "review_time", "review_result", "enforcement_action"},
    }
    per_source = source_quality_matrix.get("per_source", [])
    observations = source_observations or []
    cards: list[dict[str, Any]] = []
    for action_names, source_name in actions:
        if action_names <= disabled_actions:
            continue
        rows = [row for row in per_source if str(row.get("action") or "") in action_names]
        completed = [row for row in rows if row.get("quality_class") == "completed"]
        blocked = [row for row in rows if row.get("quality_class") in {"blocked", "timeout", "auth_failed", "parse_error"}]
        partial = [row for row in rows if row.get("quality_class") == "partial"]
        relevant_observations = [obs for obs in observations if str(obs.get("action") or "") in action_names]
        business_observations = [
            obs for obs in relevant_observations
            if obs.get("evidence_use") == "business_evidence_candidate"
        ]
        breakpoint_types = set(str(obs.get("breakpoint_type") or "") for obs in relevant_observations)
        extracted_fields = unique_strings([
            str(field)
            for obs in business_observations
            for field in obs.get("extracted_business_fields", [])
        ])
        summary_fields: set[str] = set()
        for action_name in action_names:
            summary_fields |= source_summary_fields.get(action_name, set())
        field_value_summary = _top_field_value_summary(relevant_observations, summary_fields)
        device_candidates = [
            candidate
            for obs in relevant_observations
            for candidate in obs.get("candidate_device_ids", [])
            if isinstance(candidate, dict)
        ]
        device_support_entities = unique_strings([
            str(candidate.get("source_id") or "") for candidate in device_candidates
        ])
        shared_signals: list[dict[str, Any]] = []
        if business_observations:
            shared_signals.append(
                {
                    "signal_name": f"{source_name}_business_fields_extracted",
                    "support_entities": [
                        str(obs.get("source_id")) for obs in business_observations
                    ],
                    "support_count": len(business_observations),
                    "support_ratio": round(len(business_observations) / sampled_count, 4) if sampled_count else 0,
                    "strength": "high" if len(business_observations) / max(sampled_count, 1) >= 0.7 else "medium",
                    "reason": f"extracted_fields={','.join(extracted_fields[:8])}",
                    "field_value_summary": field_value_summary,
                    "commonality_type": "coverage_commonality",
                    "risk_commonality": False,
                    "commonality_anchor": False,
                    "eligible_for_group_candidate": False,
                    "risk_interpretation": "source/field coverage only; this proves evidence availability, not shared risk anchor or same-origin commonality",
                    "evidence_type": "raw",
                    "can_be_used_for_strategy": "no",
                }
            )
        if device_candidates and source_name in {"weapon_graph_risk", "content_action_anchor", "login_log", "track_frontend_behavior"}:
            shared_device_value_seen = _has_shared_field_value(
                _top_field_value_summary(
                    relevant_observations,
                    {"device_id", "candidate_device_id", "publish_device", "operation_device", "shared_device"},
                )
            )
            shared_signals.append(
                {
                    "signal_name": f"{source_name}_candidate_device_extracted",
                    "support_entities": device_support_entities,
                    "support_count": len(device_support_entities),
                    "support_ratio": round(len(device_support_entities) / sampled_count, 4) if sampled_count else 0,
                    "strength": "medium",
                    "reason": "candidate device anchors available for Track/device consistency next-hop",
                    "field_value_summary": _top_field_value_summary(
                        relevant_observations,
                        {"device_id", "candidate_device_id", "publish_device", "operation_device", "shared_device"},
                    ),
                    "commonality_type": "anchor_commonality" if shared_device_value_seen else "anchor_lead_commonality",
                    "risk_commonality": shared_device_value_seen,
                    "eligible_for_group_candidate": shared_device_value_seen,
                    "risk_interpretation": (
                        "shared device anchor candidate across samples; still requires source-quality and validation checks"
                        if shared_device_value_seen else
                        "device anchors are linkage leads; extraction alone is not same-device commonality or gang conclusion"
                    ),
                    "evidence_type": "raw",
                    "can_be_used_for_strategy": "with_combination_only",
                }
            )
        transport_only_completed = completed and not business_observations and not shared_signals
        if source_name == "content_action_anchor" and "source_has_no_content_anchor_rows" in breakpoint_types:
            missing_data = ["content_anchor_no_rows_in_current_source_window", "not_low_risk_counter_evidence"]
        elif not completed and not partial:
            missing_data = ["business_commonality_not_available_without_completed_observation"]
        elif transport_only_completed:
            missing_data = ["completed_transport_not_business_commonality", "business_fields_not_extracted_for_commonality"]
        elif not business_observations and not shared_signals:
            missing_data = ["business_fields_not_extracted_for_commonality"]
        else:
            missing_data = []
        cards.append(
            {
                "source_name": source_name,
                "entity_coverage": {
                    "sampled_count": sampled_count,
                    "completed_or_partial": len(completed) + len(partial),
                    "blocked_or_skipped": len(blocked),
                },
                "records_coverage": (
                    "business_fields_extracted"
                    if business_observations else
                    "transport_completed_without_business_fields"
                    if transport_only_completed else
                    "not_evaluated_in_dry_run_or_transport_only"
                ),
                "shared_signals": shared_signals,
                "differentiating_signals": [],
                "counter_evidence": [],
                "missing_data": missing_data,
                "source_quality": {
                    "completed": len(completed),
                    "partial": len(partial),
                    "blocked_or_skipped": len(blocked),
                },
                "boundary_notes": [
                    "no_data_not_risk_exclusion",
                    "strategy_hit_not_final_judgement" if source_name in {"strategy_hit", "strategy_hit_detail"} else "source_quality_required",
                ],
            }
        )
    return cards


def build_batch_strategy_recommendations(coverage_status: str) -> list[dict[str, Any]]:
    return [
        {
            "priority": "P0",
            "action_group": "ready_for_controlled_gray_validation",
            "feature_or_strategy": "multi_source_device_login_content_behavior_combination",
            "target_cluster": "main_cluster_when_coverage_validated",
            "reason": "Only valid after realtime/wide-table validation shows multi-source consistency.",
            "coverage_estimate": coverage_status,
            "precision_estimate": "pending_full_validation",
            "false_positive_risk": "medium_until_counter_samples_checked",
            "rollout_suggestion": "controlled_gray_validation_only; no automatic disposition",
            "required_validation_data": ["full_batch_coverage", "normal_counter_samples", "source_quality"],
            "not_recommended_usage": "Do not use strategy hit or same-device alone.",
        },
        {
            "priority": "P1",
            "action_group": "combine_before_use",
            "feature_or_strategy": "same_device_or_same_login_window_signal",
            "target_cluster": "candidate_secondary_clusters",
            "reason": "Useful as a weighted or review feature, not standalone disposition.",
            "coverage_estimate": coverage_status,
            "precision_estimate": "pending_full_validation",
            "false_positive_risk": "medium_high_if_standalone",
            "rollout_suggestion": "risk score / second verification / manual review",
            "required_validation_data": ["cross_source_confirmation"],
            "not_recommended_usage": "Do not block from this signal alone.",
        },
        {
            "priority": "P2",
            "action_group": "monitor_or_expand_only",
            "feature_or_strategy": "single_strategy_hit_or_single_frontend_similarity",
            "target_cluster": "weak_signal_pool",
            "reason": "Weak lead for monitoring and further discovery.",
            "coverage_estimate": "not_evaluable_from_current_rounds",
            "precision_estimate": "not_evaluable",
            "false_positive_risk": "high_if_used_for_control",
            "rollout_suggestion": "monitoring / offline exploration only",
            "required_validation_data": ["additional_source_commonality"],
            "not_recommended_usage": "Not for direct control or P0 policy.",
        },
    ]


def _entity_index_from_batch_source_id(source_id: str) -> int | None:
    parts = source_id.split("_")
    if len(parts) >= 5 and parts[0] == "round" and parts[2] == "entity":
        try:
            return int(parts[3])
        except ValueError:
            return None
    return None


def _candidate_coverage_from_commonality_cards(cards: list[dict[str, Any]]) -> dict[str, Any]:
    support_by_index: dict[int, set[str]] = {}
    signal_names: list[str] = []
    for card in cards:
        source_name = str(card.get("source_name") or "")
        if source_name == "strategy_hit_detail":
            continue
        for signal in card.get("shared_signals", []) or []:
            if not isinstance(signal, dict):
                continue
            if not _is_risk_commonality_signal(signal):
                continue
            signal_names.append(str(signal.get("signal_name") or source_name))
            for source_id in signal.get("support_entities", []) or []:
                index = _entity_index_from_batch_source_id(str(source_id))
                if index is None:
                    continue
                support_by_index.setdefault(index, set()).add(source_name)
    multi_source_indices = sorted(
        index for index, sources in support_by_index.items()
        if len(sources) >= 2
    )
    single_source_indices = sorted(
        index for index, sources in support_by_index.items()
        if len(sources) == 1
    )
    return {
        "multi_source_candidate_indices": multi_source_indices,
        "single_source_signal_indices": single_source_indices,
        "support_by_index": {str(index): sorted(sources) for index, sources in support_by_index.items()},
        "signal_names": unique_strings(signal_names),
    }


def _signal_name(signal: dict[str, Any] | str) -> str:
    if isinstance(signal, dict):
        return str(signal.get("signal_name") or "")
    return str(signal or "")


def _is_coverage_commonality_signal(signal: dict[str, Any] | str) -> bool:
    if isinstance(signal, dict) and str(signal.get("commonality_type") or "") == "coverage_commonality":
        return True
    return _signal_name(signal).endswith(COVERAGE_COMMONALITY_SUFFIX)


def _is_risk_commonality_signal(signal: dict[str, Any] | str) -> bool:
    if not isinstance(signal, dict):
        return False
    if _is_coverage_commonality_signal(signal):
        return False
    if signal.get("eligible_for_group_candidate") is True:
        return True
    return str(signal.get("commonality_type") or "") in RISK_COMMONALITY_TYPES


def _has_shared_field_value(field_value_summary: dict[str, Any]) -> bool:
    for values in field_value_summary.values():
        if not isinstance(values, list):
            continue
        for item in values:
            if not isinstance(item, dict):
                continue
            if int(item.get("support_count") or 0) >= COMMONALITY_ANCHOR_MIN_SUPPORT:
                return True
    return False


def _top_field_value_summary(
    observations: list[dict[str, Any]],
    fields: set[str],
    *,
    max_values_per_field: int = 5,
) -> dict[str, list[dict[str, Any]]]:
    counts: dict[str, dict[str, int]] = {}
    for observation in observations:
        for handle in observation.get("parsed_body_field_handles", []) or []:
            canonical = str(handle.get("canonical_field") or handle.get("field") or "")
            if canonical not in fields:
                continue
            value = handle.get("value")
            if value is None:
                continue
            value_text = str(value).strip()
            if not value_text:
                continue
            if len(value_text) > 128:
                value_text = f"{value_text[:125]}..."
            counts.setdefault(canonical, {})
            counts[canonical][value_text] = counts[canonical].get(value_text, 0) + 1
    summary: dict[str, list[dict[str, Any]]] = {}
    for field, values in counts.items():
        ranked = sorted(values.items(), key=lambda item: (-item[1], item[0]))[:max_values_per_field]
        summary[field] = [
            {
                "value": value,
                "support_count": count,
            }
            for value, count in ranked
        ]
    return summary


INTERFACE_OBSERVATION_DOMAINS: dict[str, list[str]] = {
    "archives_user_profile": ["account_domain", "enforcement_domain"],
    "archives_user_analysis": ["account_domain", "behavior_domain"],
    "archives_review_logs": ["behavior_domain", "enforcement_domain"],
    "weapon_inventory": ["device_domain", "group_domain"],
    "login_logs_search": ["account_domain", "network_domain", "behavior_domain"],
    "archives_photo_search": ["content_domain", "behavior_domain"],
    "archives_gallery_photo_list": ["content_domain", "behavior_domain"],
    "archives_photo_profile": ["content_domain", "network_domain", "behavior_domain"],
    "archives_photo_meta": ["content_domain", "device_domain", "network_domain"],
    "archives_negative_report": ["feedback_domain"],
    "archives_user_report_search": ["feedback_domain", "content_domain"],
    "archives_punish_status": ["enforcement_domain", "content_domain"],
    "rcp_fast_query_hbase": ["strategy_domain"],
    "rcp_snapshot": ["strategy_domain"],
    "rcp_event_tree_or_decision": ["strategy_domain"],
    "track_analysis_check_data_ready": ["behavior_domain", "device_domain"],
}


FIRST_HOP_ACTIONS = {
    "archives_user_profile",
    "archives_review_logs",
    "weapon_inventory",
    "login_logs_search",
    "archives_photo_search",
    "rcp_fast_query_hbase",
}


ANCHOR_TRIGGERED_ACTIONS = {
    "archives_gallery_photo_list",
    "archives_photo_profile",
    "archives_photo_meta",
    "track_analysis_check_data_ready",
    "rcp_event_tree_or_decision",
}


def _infer_seed_entity_type(entity: str) -> str:
    text = str(entity).strip()
    lowered = text.lower()
    if lowered.startswith(("web_", "did_", "device_", "android_", "ios_")):
        return "device_id"
    if lowered.startswith(("photo_", "kwai_photo_")):
        return "photo_id"
    if lowered.startswith(("event_", "evt_")):
        return "event_id"
    if lowered.startswith(("policy_", "pol_")):
        return "policy_code"
    if "." in text and all(part.isdigit() for part in text.split(".") if part):
        return "ip"
    if text.isdigit():
        return "user_id"
    return "mixed"


def _round_seed_entity(sampled_entities: list[str]) -> dict[str, Any]:
    types = [_infer_seed_entity_type(entity) for entity in sampled_entities]
    unique_types = unique_strings(types)
    return {
        "input_type": unique_types[0] if len(unique_types) == 1 else "mixed",
        "seed_count": len(sampled_entities),
        "seed_entity_refs": [
            {"entity_type": entity_type, "safe_ref": f"seed_entity_{index}"}
            for index, entity_type in enumerate(types, start=1)
        ],
        "raw_seed_entities_retained_for_internal_risk_review": True,
    }


def _interface_role(action: str) -> str:
    if action in FIRST_HOP_ACTIONS:
        return "first_hop_candidate"
    if action in ANCHOR_TRIGGERED_ACTIONS:
        return "anchor_triggered_drilldown"
    return "validation_only" if action.startswith("dataagent_") else "unavailable_or_missing_contract"


def _expected_anchor_types_for_action(action: str) -> list[str]:
    mapping = {
        "archives_user_profile": ["account_status_anchor", "punishment_anchor", "profile_anchor"],
        "archives_review_logs": ["review_id", "review_result", "enforcement_action"],
        "weapon_inventory": ["candidate_device_id", "same_device_anchor"],
        "login_logs_search": ["candidate_login_time", "candidate_device_id", "candidate_ip_ua"],
        "archives_photo_search": ["candidate_photo_id", "candidate_publish_time", "candidate_publish_device"],
        "archives_gallery_photo_list": ["candidate_photo_id", "candidate_publish_time"],
        "archives_photo_profile": ["publish_source", "publish_device", "publish_ip_ua"],
        "archives_photo_meta": ["publish_device", "publish_source", "photo_meta_anchor"],
        "archives_negative_report": ["report_id", "feedback_signal"],
        "archives_user_report_search": ["report_id", "feedback_signal"],
        "archives_punish_status": ["punish_id", "enforcement_action"],
        "rcp_fast_query_hbase": ["candidate_policy_code", "candidate_event_id", "strategy_hit_time"],
        "track_analysis_check_data_ready": ["frontend_activity_anchor", "frontend_backend_consistency_anchor"],
    }
    return mapping.get(action, [])


def _required_anchor_for_action(action: str, params: dict[str, Any]) -> list[str]:
    if action in FIRST_HOP_ACTIONS:
        return [field for field in ("user_id", "device_id", "photo_id", "source_id") if field in params]
    if action in {"archives_photo_profile", "archives_photo_meta"}:
        return ["photo_id"]
    if action == "track_analysis_check_data_ready":
        return ["device_id"]
    if action.startswith("rcp_"):
        return ["event_id_or_policy_code_or_source_id"]
    return []


def build_base_interface_plan_artifact(
    source_plan: list[SourcePlanItem],
    *,
    disabled_actions: set[str] | None,
) -> dict[str, Any]:
    planned_interfaces = []
    for item in source_plan:
        role = _interface_role(item.action)
        if role != "first_hop_candidate":
            continue
        planned_interfaces.append(
            {
                "source_id": item.source_id,
                "interface": item.action,
                "role": role,
                "observation_domains": INTERFACE_OBSERVATION_DOMAINS.get(item.action, []),
                "required_anchor": _required_anchor_for_action(item.action, item.params),
                "expected_anchor_types": _expected_anchor_types_for_action(item.action),
                "cap": {
                    "max_sources_per_batch": MAX_BROWSER_BACKED_BATCH_SOURCES,
                    "per_action_chunk_limit": SOURCE_ACTION_CHUNK_LIMITS.get(item.action),
                },
            }
        )
    return {
        "plan_type": "base_interface_plan",
        "planned_interfaces": planned_interfaces,
        "skipped_interfaces": [
            {"interface": action, "reason": "disabled_by_request_or_fixture", "source_quality": "not_executed"}
            for action in sorted(disabled_actions or set())
        ],
        "cap": {
            "max_browser_backed_batch_sources": MAX_BROWSER_BACKED_BATCH_SOURCES,
            "no_70_action_cartesian_product": True,
            "source_count_planned": len(source_plan),
        },
        "expected_anchor_types": unique_strings([
            anchor
            for item in planned_interfaces
            for anchor in item.get("expected_anchor_types", [])
        ]),
        "forbidden_behavior": [
            "user_id_input_must_not_expand_all_photo_ip_event_policy",
            "do_not_run_70_actions_per_sample",
            "do_not_call_dataagent_hive_without_user_authorization",
        ],
    }


def _normalized_interface_source_quality(source_quality_matrix: dict[str, Any]) -> dict[str, Any]:
    buckets = source_quality_matrix.get("buckets", {})
    per_source = source_quality_matrix.get("per_source", [])
    return {
        "completed": buckets.get("completed", []),
        "no_data": buckets.get("no_data", []),
        "skipped_missing_anchor": [
            row.get("source_id")
            for row in per_source
            if row.get("quality_class") == "blocked" and row.get("error_type") == "missing_required_fields"
        ],
        "skipped_by_cap": [
            row.get("source_id")
            for row in per_source
            if row.get("error_type") == "skipped_by_cap"
        ],
        "skipped_low_score": [],
        "low_value_anchor": [],
        "missing_contract": [
            row.get("source_id")
            for row in per_source
            if row.get("error_type") == "missing_contract"
        ],
        "timeout": buckets.get("timeout", []),
        "parse_error": buckets.get("parse_error", []),
        "authorization_required": [
            row.get("source_id")
            for row in per_source
            if row.get("quality_class") == "auth_failed"
        ],
        "not_executed": buckets.get("planned", []),
        "partial": buckets.get("partial", []),
        "response_limited": [
            row.get("source_id")
            for row in per_source
            if row.get("response_limited") is True
        ],
        "partial_reasons": [
            {
                "source_id": row.get("source_id"),
                "action": row.get("action"),
                "reason": row.get("reason") or row.get("source_status"),
                "remaining_records_not_parsed": row.get("remaining_records_not_parsed"),
            }
            for row in per_source
            if row.get("quality_class") == "partial"
        ],
        "blocked": buckets.get("blocked", []),
        "auth_failed": buckets.get("auth_failed", []),
        "boundary": [
            "no_data_skipped_timeout_missing_contract_not_low_risk_counter_evidence",
            "completed_transport_not_business_evidence",
            "response_limited_partial_not_failed_final",
        ],
    }


def build_base_summary_card_artifact(
    *,
    round_id: int,
    sampled_entities: list[str],
    source_plan: list[SourcePlanItem],
    source_quality_matrix: dict[str, Any],
    source_observations: list[dict[str, Any]],
) -> dict[str, Any]:
    planned_by_domain: dict[str, list[str]] = {}
    for item in source_plan:
        if _interface_role(item.action) != "first_hop_candidate":
            continue
        for domain in INTERFACE_OBSERVATION_DOMAINS.get(item.action, []):
            planned_by_domain.setdefault(domain, [])
            if item.action not in planned_by_domain[domain]:
                planned_by_domain[domain].append(item.action)
    extracted_by_domain: dict[str, list[str]] = {}
    for observation in source_observations:
        action = str(observation.get("action") or "")
        for domain in INTERFACE_OBSERVATION_DOMAINS.get(action, []):
            extracted_by_domain.setdefault(domain, [])
            extracted_by_domain[domain].extend(str(field) for field in observation.get("extracted_business_fields", []))
    return {
        "round_id": round_id,
        "entities": [
            {"entity": entity, "entity_type": _infer_seed_entity_type(entity), "safe_ref": f"round_{round_id}_seed_{index}"}
            for index, entity in enumerate(sampled_entities, start=1)
        ],
        "observation_domains": sorted(planned_by_domain),
        "base_facts": {
            "planned_interfaces_by_domain": planned_by_domain,
            "extracted_business_fields_by_domain": {
                domain: unique_strings(fields)
                for domain, fields in extracted_by_domain.items()
            },
            "dry_run_structure_only": not bool(extracted_by_domain),
        },
        "candidate_anchors": [],
        "source_quality": _normalized_interface_source_quality(source_quality_matrix),
        "no_data_boundary": "no_data_skipped_timeout_missing_contract_not_low_risk_counter_evidence",
    }


def _append_anchor(
    anchors: list[dict[str, Any]],
    *,
    anchor_type: str,
    value: str | None = None,
    safe_ref: str | None = None,
    produced_by: str,
    observation_domain: str,
    confidence: str,
    next_allowed_interfaces: list[str],
    cap_key: str,
    reason: str,
    source_quality: str,
    evidence_source: str,
    field_path: str | None = None,
) -> None:
    identity = (anchor_type, value or safe_ref or produced_by)
    existing = {
        (
            str(anchor.get("anchor_type")),
            str(anchor.get("value") or anchor.get("safe_ref") or anchor.get("produced_by")),
        )
        for anchor in anchors
    }
    if identity in existing:
        return
    anchor: dict[str, Any] = {
        "anchor_type": anchor_type,
        "produced_by": produced_by,
        "observation_domain": observation_domain,
        "confidence": confidence,
        "next_allowed_interfaces": next_allowed_interfaces,
        "cap_key": cap_key,
        "reason": reason,
        "source_quality": source_quality,
        "evidence_source": evidence_source,
    }
    if value is not None:
        anchor["value"] = value
    if safe_ref is not None:
        anchor["safe_ref"] = safe_ref
    if field_path:
        anchor["field_path"] = _safe_field_path(field_path)
    anchors.append(anchor)


MAX_CANDIDATE_ANCHORS_PER_ROUND = 30
MAX_SELECTED_DRILLDOWN_ANCHORS = 5
MAX_SELECTED_ANCHORS_PER_DOMAIN = 2
MAX_SELECTED_ANCHORS_PER_TYPE = 2
MAX_L2_INTERFACES_PER_ANCHOR = 3
COMMONALITY_ANCHOR_MIN_SUPPORT = 2
COVERAGE_COMMONALITY_SUFFIX = "_business_fields_extracted"
RISK_COMMONALITY_TYPES = {"anchor_commonality", "chain_commonality", "group_candidate_commonality"}


def _anchor_ref(anchor: dict[str, Any]) -> str:
    return str(anchor.get("value") or anchor.get("safe_ref") or anchor.get("anchor_type") or "")


def _canonical_anchor_type(canonical: str) -> str | None:
    if canonical == "photo_id":
        return "candidate_photo_id"
    if canonical in {"device_id", "publish_device", "operation_device", "login_device"}:
        return "candidate_device_id"
    if canonical in {"policy_code", "event_id", "source_id"}:
        return f"candidate_{canonical}"
    if canonical == "ip":
        return "candidate_ip"
    if canonical in {"relation_anchor", "comment_id", "message_anchor", "live_id"}:
        return f"candidate_{canonical}"
    if canonical in {"report_id", "review_id", "punish_id"}:
        return f"candidate_{canonical}"
    return None


def _quality_value(source_quality: str) -> float:
    quality = str(source_quality or "").lower()
    if quality in {"completed", "current_observation"}:
        return 1.0
    if quality in {"partial", "response_limited", "completed_or_partial"}:
        return 0.55
    if quality in {"not_executed", "planned_only_dry_run", "dry_run_anchor_hint"}:
        return 0.35
    if quality in {"no_data", "timeout", "missing_contract", "skipped_missing_anchor", "skipped_by_cap", "parse_error"}:
        return 0.2
    if quality in {"blocked", "auth_failed"}:
        return 0.15
    return 0.4


def _risk_label_penalty(label: str) -> float:
    return {
        "low": 0.0,
        "medium": 0.5,
        "high": 1.0,
    }.get(label, 0.5)


def _anchor_cost_level(anchor_type: str) -> str:
    if anchor_type in {"candidate_photo_id", "candidate_policy_code", "candidate_event_id"}:
        return "low"
    if anchor_type in {"candidate_device_id", "candidate_report_id", "candidate_review_id", "candidate_punish_id"}:
        return "medium"
    if anchor_type in {"candidate_ip", "candidate_relation_anchor", "candidate_comment_id", "candidate_message_anchor"}:
        return "high"
    return "medium"


def _anchor_expansion_risk(anchor_type: str) -> str:
    if anchor_type in {"candidate_ip", "candidate_device_id", "candidate_relation_anchor", "candidate_comment_id", "candidate_message_anchor"}:
        return "high"
    if anchor_type in {"candidate_policy_code", "candidate_event_id"}:
        return "medium"
    return "low"


def _anchor_false_positive_risk(anchor_type: str) -> str:
    if anchor_type in {"candidate_ip", "candidate_relation_anchor", "candidate_comment_id", "candidate_message_anchor"}:
        return "high"
    if anchor_type in {"candidate_device_id", "candidate_policy_code", "candidate_event_id"}:
        return "medium"
    return "low"


def _anchor_class(anchor_type: str, batch_support_count: int, anomaly_strength: float, chain_value: float) -> str:
    if batch_support_count >= COMMONALITY_ANCHOR_MIN_SUPPORT:
        return "commonality_anchor"
    if chain_value >= 3:
        return "chain_anchor"
    if anomaly_strength >= 2:
        return "anomaly_anchor"
    return "presence_anchor"


def _anchor_domain(anchor_type: str) -> str:
    if anchor_type in {"candidate_photo_id", "candidate_live_id"}:
        return "content_domain"
    if anchor_type == "candidate_device_id":
        return "device_domain"
    if anchor_type == "candidate_ip":
        return "network_domain"
    if anchor_type in {"candidate_policy_code", "candidate_event_id", "candidate_source_id"}:
        return "strategy_domain"
    if anchor_type in {"candidate_relation_anchor", "candidate_comment_id", "candidate_message_anchor"}:
        return "social_domain"
    if anchor_type == "candidate_report_id":
        return "feedback_domain"
    if anchor_type in {"candidate_review_id", "candidate_punish_id"}:
        return "enforcement_domain"
    return "unknown_domain"


def _anchor_next_interfaces(anchor_type: str) -> list[str]:
    if anchor_type == "candidate_photo_id":
        return ["archives_photo_profile", "archives_photo_meta"]
    if anchor_type == "candidate_device_id":
        return ["track_analysis_check_data_ready", "weapon_inventory"]
    if anchor_type in {"candidate_policy_code", "candidate_event_id", "candidate_source_id"}:
        return ["rcp_event_tree_or_decision", "rcp_feature_info_by_keys"]
    if anchor_type == "candidate_ip":
        return ["login_logs_search"]
    if anchor_type == "candidate_comment_id":
        return ["archives_comment_search", "archives_livestream_comment_detail"]
    if anchor_type == "candidate_message_anchor":
        return ["archives_private_message_search"]
    if anchor_type == "candidate_live_id":
        return ["archives_livestream_home_info", "archives_livestream_home_meta"]
    if anchor_type == "candidate_relation_anchor":
        return ["archives_related_users", "archives_fans_list", "archives_follow_list"]
    if anchor_type == "candidate_report_id":
        return ["archives_user_report_search", "archives_negative_report"]
    if anchor_type in {"candidate_review_id", "candidate_punish_id"}:
        return ["archives_review_logs", "archives_punish_status"]
    return []


def _anchor_cap_key(anchor_type: str) -> str:
    if anchor_type == "candidate_photo_id":
        return "photo_anchor_top_k"
    if anchor_type == "candidate_device_id":
        return "device_anchor_top_k"
    if anchor_type in {"candidate_policy_code", "candidate_event_id", "candidate_source_id"}:
        return "strategy_anchor_top_k"
    if anchor_type == "candidate_ip":
        return "network_anchor_top_k"
    return f"{anchor_type}_top_k"


def _batch_signal_name(anchor_type: str, scope: str) -> str:
    prefix = "batch" if scope == "batch_anchor" else "single_entity"
    if anchor_type == "candidate_message_anchor":
        return f"{prefix}_private_message_signal"
    if anchor_type in {"candidate_relation_anchor", "candidate_comment_id"}:
        return f"{prefix}_social_anchor"
    if anchor_type == "candidate_device_id":
        return f"{prefix}_device_anchor"
    if anchor_type == "candidate_ip":
        return f"{prefix}_network_anchor"
    if anchor_type == "candidate_photo_id":
        return f"{prefix}_content_anchor"
    if anchor_type in {"candidate_policy_code", "candidate_event_id", "candidate_source_id"}:
        return f"{prefix}_strategy_anchor"
    return f"{prefix}_{anchor_type}"


def _is_candidate_extraction_signal(signal: dict[str, Any] | str) -> bool:
    name = str(signal.get("signal_name") if isinstance(signal, dict) else signal)
    return "_candidate_" in name and name.endswith("_extracted")


def _observation_support_entities(observation: dict[str, Any], sampled_entities: list[str]) -> set[str]:
    support_entities: set[str] = set()
    sampled_set = set(str(entity) for entity in sampled_entities)
    for key in ("user_id", "entity", "seed_entity"):
        value = str(observation.get(key) or "").strip()
        if value:
            support_entities.add(value)
    for handle in observation.get("parsed_body_field_handles", []) or []:
        if not isinstance(handle, dict):
            continue
        canonical = str(handle.get("canonical_field") or handle.get("field") or "")
        value = str(handle.get("value") or "").strip()
        if canonical == "user_id" and value:
            support_entities.add(value)
    source_id = str(observation.get("source_id") or "")
    index = _entity_index_from_batch_source_id(source_id)
    if index is not None and 1 <= index <= len(sampled_entities):
        support_entities.add(str(sampled_entities[index - 1]))
    if not support_entities and len(sampled_entities) == 1:
        support_entities.add(str(sampled_entities[0]))
    if sampled_set:
        matched = {entity for entity in support_entities if entity in sampled_set}
        if matched:
            return matched
    return support_entities


def _anchor_occurrence_stats(
    source_observations: list[dict[str, Any]],
    sampled_entities: list[str],
) -> dict[tuple[str, str], dict[str, Any]]:
    stats: dict[tuple[str, str], dict[str, Any]] = {}

    def add_occurrence(anchor_type: str | None, value: Any, observation: dict[str, Any]) -> None:
        if not anchor_type:
            return
        value_text = str(value or "").strip()
        if not value_text:
            return
        action = str(observation.get("action") or "")
        source_id = str(observation.get("source_id") or action or "unknown_source")
        key = (anchor_type, value_text)
        row = stats.setdefault(
            key,
            {
                "support_sources": set(),
                "support_entities": set(),
                "actions": set(),
                "domains": set(),
                "qualities": [],
            },
        )
        row["support_sources"].add(source_id)
        row["support_entities"].update(_observation_support_entities(observation, sampled_entities))
        row["actions"].add(action)
        for domain in INTERFACE_OBSERVATION_DOMAINS.get(action, []):
            row["domains"].add(domain)
        if observation.get("quality_class"):
            row["qualities"].append(str(observation.get("quality_class")))

    for observation in source_observations:
        for handle in observation.get("parsed_body_field_handles", []) or []:
            if not isinstance(handle, dict):
                continue
            canonical = str(handle.get("canonical_field") or handle.get("field") or "")
            add_occurrence(_canonical_anchor_type(canonical), handle.get("value"), observation)
        for candidate in observation.get("candidate_device_ids", []) or []:
            if isinstance(candidate, dict):
                add_occurrence("candidate_device_id", candidate.get("device_id"), observation)
    return stats


def build_batch_anchor_pool(
    *,
    candidate_anchor_pool: list[dict[str, Any]],
    source_observations: list[dict[str, Any]],
    sampled_entities: list[str],
) -> list[dict[str, Any]]:
    occurrence_stats = _anchor_occurrence_stats(source_observations, sampled_entities)
    prototypes: dict[tuple[str, str], dict[str, Any]] = {}
    ordered_keys: list[tuple[str, str]] = []
    for anchor in candidate_anchor_pool:
        anchor_type = str(anchor.get("anchor_type") or "")
        value = str(anchor.get("value") or anchor.get("safe_ref") or "").strip()
        if not anchor_type or not value:
            continue
        key = (anchor_type, value)
        if key not in prototypes:
            prototypes[key] = dict(anchor)
            ordered_keys.append(key)
    for key in occurrence_stats:
        if key not in prototypes:
            ordered_keys.append(key)

    sampled_count = len(sampled_entities)
    batch_pool: list[dict[str, Any]] = []
    for index, key in enumerate(ordered_keys):
        anchor_type, value = key
        stats = occurrence_stats.get(key, {})
        prototype = prototypes.get(key, {})
        support_entities = sorted(str(item) for item in stats.get("support_entities", set()))
        if not support_entities:
            produced_index = _entity_index_from_batch_source_id(str(prototype.get("produced_by") or ""))
            if produced_index is not None and 1 <= produced_index <= len(sampled_entities):
                support_entities = [str(sampled_entities[produced_index - 1])]
            elif len(sampled_entities) == 1:
                support_entities = [str(sampled_entities[0])]
        support_sources = sorted(str(item) for item in stats.get("support_sources", set()))
        if not support_sources and prototype.get("produced_by"):
            support_sources = [str(prototype.get("produced_by"))]
        support_actions = sorted(str(item) for item in stats.get("actions", set()))
        support_domains = sorted(str(item) for item in stats.get("domains", set()))
        domain = str(prototype.get("observation_domain") or _anchor_domain(anchor_type))
        if domain and domain not in support_domains:
            support_domains.append(domain)
        support_count = len(set(support_entities))
        if sampled_count <= 1 and support_count > 1:
            support_count = 1
            support_entities = support_entities[:1]
        scope = "batch_anchor" if sampled_count > 1 and support_count >= COMMONALITY_ANCHOR_MIN_SUPPORT else "single_entity_anchor"
        anchor = {
            **prototype,
            "anchor_type": anchor_type,
            "value": value,
            "produced_by": str(prototype.get("produced_by") or (support_sources[0] if support_sources else "batch_anchor_pool")),
            "observation_domain": domain,
            "confidence": str(prototype.get("confidence") or "current_observation"),
            "next_allowed_interfaces": list(prototype.get("next_allowed_interfaces") or _anchor_next_interfaces(anchor_type)),
            "cap_key": str(prototype.get("cap_key") or _anchor_cap_key(anchor_type)),
            "reason": str(prototype.get("reason") or f"{anchor_type}_aggregated_in_batch_anchor_pool"),
            "source_quality": str(prototype.get("source_quality") or "unknown"),
            "evidence_source": str(prototype.get("evidence_source") or "current_observation"),
            "field_path": _safe_field_path(str(prototype.get("field_path") or "projected_safe_field_path")),
            "batch_anchor_key": f"{anchor_type}:{value}",
            "batch_anchor_scope": scope,
            "is_batch_anchor": scope == "batch_anchor",
            "eligible_for_batch_commonality": scope == "batch_anchor",
            "supporting_entities": support_entities,
            "supporting_sources": support_sources,
            "supporting_actions": support_actions,
            "supporting_domains": unique_strings(support_domains),
            "support_entity_count": support_count,
            "batch_signal_name": _batch_signal_name(anchor_type, scope),
            "anchor_group_boundary": (
                "batch_anchor_can_support_risk_commonality_but_not_final_conclusion"
                if scope == "batch_anchor"
                else "single_entity_anchor_cannot_support_group_profile_candidate"
            ),
            "_original_index": index,
        }
        batch_pool.append(anchor)
    return batch_pool[:MAX_CANDIDATE_ANCHORS_PER_ROUND]


def score_candidate_anchors(
    *,
    candidate_anchor_pool: list[dict[str, Any]],
    sampled_entities: list[str],
    source_observations: list[dict[str, Any]],
    max_selected: int = MAX_SELECTED_DRILLDOWN_ANCHORS,
) -> dict[str, Any]:
    occurrence_stats = _anchor_occurrence_stats(source_observations, sampled_entities)
    batch_anchor_pool = build_batch_anchor_pool(
        candidate_anchor_pool=candidate_anchor_pool,
        source_observations=source_observations,
        sampled_entities=sampled_entities,
    )
    scored: list[dict[str, Any]] = []
    skipped_anchors: list[dict[str, Any]] = []
    sampled_count = len(sampled_entities)

    for index, anchor in enumerate(batch_anchor_pool):
        anchor_type = str(anchor.get("anchor_type") or "")
        ref = _anchor_ref(anchor)
        stats = occurrence_stats.get((anchor_type, str(anchor.get("value") or "")), {})
        support_sources = sorted(str(item) for item in stats.get("support_sources", set())) or list(anchor.get("supporting_sources") or [])
        support_entities = sorted(str(item) for item in stats.get("support_entities", set())) or list(anchor.get("supporting_entities") or [])
        if not support_entities:
            produced_index = _entity_index_from_batch_source_id(str(anchor.get("produced_by") or ""))
            if produced_index is not None and 1 <= produced_index <= len(sampled_entities):
                support_entities = [str(sampled_entities[produced_index - 1])]
            elif len(sampled_entities) == 1:
                support_entities = [str(sampled_entities[0])]
        support_domains = sorted(str(item) for item in stats.get("domains", set())) or list(anchor.get("supporting_domains") or [])
        if anchor.get("observation_domain") and str(anchor.get("observation_domain")) not in support_domains:
            support_domains.append(str(anchor.get("observation_domain")))
        qualities = [str(item) for item in stats.get("qualities", [])] or [str(anchor.get("source_quality") or "unknown")]
        quality_scores = [_quality_value(item) for item in qualities]
        evidence_quality = round(sum(quality_scores) / len(quality_scores), 2) if quality_scores else 0.4
        batch_support_count = len(support_entities) if support_entities else (1 if anchor.get("value") else 0)
        if sampled_count <= 1 and batch_support_count > 1:
            batch_support_count = 1
        cross_domain_support = len(support_domains)
        anchor_presence = 1 if ref else 0
        anomaly_strength = 0.0
        if anchor_type in {"candidate_policy_code", "candidate_event_id", "candidate_ip"}:
            anomaly_strength += 1.5
        if anchor_type in {"candidate_device_id", "candidate_report_id", "candidate_review_id", "candidate_punish_id"}:
            anomaly_strength += 1.0
        reason_text = str(anchor.get("reason") or "").lower()
        if any(token in reason_text for token in ("abnormal", "risk", "front", "backend", "proxy", "policy")):
            anomaly_strength += 0.5
        chain_value = 1.0 if anchor.get("next_allowed_interfaces") else 0.0
        if anchor_type in {"candidate_device_id", "candidate_policy_code", "candidate_event_id", "candidate_photo_id"}:
            chain_value += 1.0
        if cross_domain_support >= 2:
            chain_value += 1.0
        if batch_support_count >= COMMONALITY_ANCHOR_MIN_SUPPORT and sampled_count > 1:
            chain_value += 1.0
        current_support = 1.0 if anchor.get("evidence_source") == "current_observation" else 0.0
        cost_level = _anchor_cost_level(anchor_type)
        expansion_risk = _anchor_expansion_risk(anchor_type)
        false_positive_risk = _anchor_false_positive_risk(anchor_type)
        total_score = (
            anchor_presence
            + anomaly_strength
            + min(batch_support_count, 5) * 0.8
            + min(cross_domain_support, 4) * 0.5
            + chain_value
            + evidence_quality
            + current_support
            - _risk_label_penalty(cost_level)
            - _risk_label_penalty(expansion_risk)
            - _risk_label_penalty(false_positive_risk)
        )
        anchor_class = _anchor_class(anchor_type, batch_support_count if sampled_count > 1 else 1, anomaly_strength, chain_value)
        batch_anchor_scope = "batch_anchor" if sampled_count > 1 and batch_support_count >= COMMONALITY_ANCHOR_MIN_SUPPORT else "single_entity_anchor"
        if batch_anchor_scope != "batch_anchor" and anchor_class == "commonality_anchor":
            anchor_class = "chain_anchor" if chain_value >= 3 else "anomaly_anchor" if anomaly_strength >= 2 else "presence_anchor"
        priority_reasons = []
        if anchor.get("evidence_source") == "current_observation":
            priority_reasons.append("current_observation_supported")
        if sampled_count > 1 and batch_support_count >= COMMONALITY_ANCHOR_MIN_SUPPORT:
            priority_reasons.append(f"batch_support_count={batch_support_count}")
            priority_reasons.append("batch_anchor")
        else:
            priority_reasons.append("single_entity_anchor")
        if cross_domain_support >= 2:
            priority_reasons.append(f"cross_domain_support={cross_domain_support}")
        if chain_value >= 3:
            priority_reasons.append("high_chain_value")
        if evidence_quality < 0.6:
            priority_reasons.append("evidence_quality_lowered_by_partial_or_gap_status")
        if not priority_reasons:
            priority_reasons.append("presence_only_anchor")

        enriched = {
            **anchor,
            "anchor_class": anchor_class,
            "batch_anchor_scope": batch_anchor_scope,
            "is_batch_anchor": batch_anchor_scope == "batch_anchor",
            "eligible_for_batch_commonality": batch_anchor_scope == "batch_anchor",
            "supporting_entities": support_entities[:10],
            "supporting_sources": support_sources[:10],
            "support_entity_count": batch_support_count,
            "batch_signal_name": _batch_signal_name(anchor_type, batch_anchor_scope),
            "anchor_group_boundary": (
                "batch_anchor_can_support_risk_commonality_but_not_final_conclusion"
                if batch_anchor_scope == "batch_anchor"
                else "single_entity_anchor_cannot_support_group_profile_candidate"
            ),
            "anchor_score": {
                "anchor_presence": anchor_presence,
                "anomaly_strength": round(anomaly_strength, 2),
                "batch_support_count": batch_support_count if sampled_count > 1 else 1,
                "cross_domain_support": cross_domain_support,
                "chain_value": round(chain_value, 2),
                "cost_level": cost_level,
                "expansion_risk": expansion_risk,
                "false_positive_risk": false_positive_risk,
                "evidence_quality": evidence_quality,
                "current_observation_support": current_support,
                "total_score": round(total_score, 2),
                "supporting_entities": support_entities[:10],
                "supporting_sources": support_sources[:10],
            },
            "anchor_priority_reason": unique_strings(priority_reasons),
            "_original_index": index,
        }
        scored.append(enriched)

    ranked = sorted(
        scored,
        key=lambda item: (
            float(item.get("anchor_score", {}).get("total_score") or 0),
            int(item.get("anchor_score", {}).get("batch_support_count") or 0),
            int(item.get("anchor_score", {}).get("cross_domain_support") or 0),
            -int(item.get("_original_index") or 0),
        ),
        reverse=True,
    )
    selected_keys: set[tuple[str, str]] = set()
    selected_drilldown_anchors: list[dict[str, Any]] = []
    selected_domain_counts: dict[str, int] = {}
    selected_type_counts: dict[str, int] = {}

    def can_select(item: dict[str, Any]) -> tuple[bool, str]:
        ref = _anchor_ref(item)
        anchor_type = str(item.get("anchor_type") or "")
        domain = str(item.get("observation_domain") or "unknown_domain")
        key = (anchor_type, ref)
        score = float(item.get("anchor_score", {}).get("total_score") or 0)
        if not item.get("value") and item.get("evidence_source") == "dry_run_structure_only":
            if len(selected_drilldown_anchors) >= max_selected:
                return False, "skipped_by_cap"
            return True, "plan_only"
        if key in selected_keys:
            return False, "duplicate_anchor"
        if score < 2.0:
            return False, "skipped_low_score"
        if len(selected_drilldown_anchors) >= max_selected:
            return False, "skipped_by_cap"
        if selected_domain_counts.get(domain, 0) >= MAX_SELECTED_ANCHORS_PER_DOMAIN:
            return False, "skipped_by_domain_cap"
        if selected_type_counts.get(anchor_type, 0) >= MAX_SELECTED_ANCHORS_PER_TYPE:
            return False, "skipped_by_type_cap"
        return True, "selected"

    def select_item(item: dict[str, Any], *, reason: str) -> None:
        ref = _anchor_ref(item)
        anchor_type = str(item.get("anchor_type") or "")
        domain = str(item.get("observation_domain") or "unknown_domain")
        status = "plan_only" if reason == "plan_only" else "selected"
        item["selection_status"] = status
        priority = list(item.get("anchor_priority_reason", []) or [])
        if reason == "domain_diversity":
            priority.append("selected_for_domain_diversity")
        elif reason == "score_fill":
            priority.append("selected_by_score_after_diversity")
        elif reason == "plan_only":
            priority.append("plan_only_selected_within_cap")
        if str(item.get("anchor_type")) == "candidate_policy_code":
            priority.append("strategy_anchor_selected_for_attribution_or_validation_not_final_judgement")
        if str(item.get("anchor_score", {}).get("false_positive_risk")) == "high":
            priority.append("selected_despite_high_false_positive_risk_due_to_score_and_cap")
        item["anchor_priority_reason"] = unique_strings(priority)
        selected_keys.add((anchor_type, ref))
        selected_domain_counts[domain] = selected_domain_counts.get(domain, 0) + 1
        selected_type_counts[anchor_type] = selected_type_counts.get(anchor_type, 0) + 1
        selected_drilldown_anchors.append(item)

    def skip_item(item: dict[str, Any], reason: str) -> None:
        item["selection_status"] = reason
        priority = list(item.get("anchor_priority_reason", []) or [])
        if reason == "skipped_by_domain_cap":
            priority.append(f"domain_cap_reached:{item.get('observation_domain')}")
        elif reason == "skipped_by_type_cap":
            priority.append(f"anchor_type_cap_reached:{item.get('anchor_type')}")
        elif reason == "skipped_by_cap":
            priority.append("global_top_k_cap_reached")
        elif reason == "skipped_low_score":
            priority.append("score_below_selection_threshold")
        elif reason == "duplicate_anchor":
            priority.append("duplicate_anchor_ref_already_selected")
        elif reason == "skipped_by_entity_diversity":
            priority.append("entity_diversity_selected_another_sample_anchor")
        if str(item.get("anchor_score", {}).get("false_positive_risk")) == "high":
            priority.append("high_false_positive_risk_lowered_priority")
        item["anchor_priority_reason"] = unique_strings(priority)
        skipped_anchors.append(
            {
                "anchor": item,
                "skip_reason": reason,
                "anchor_priority_reason": item.get("anchor_priority_reason", []),
            }
        )

    def primary_entity(item: dict[str, Any]) -> str:
        entities = item.get("anchor_score", {}).get("supporting_entities", []) or []
        return str(entities[0]) if entities else "unknown_entity"

    def entity_distribution(anchors: list[dict[str, Any]]) -> dict[str, int]:
        counts: dict[str, int] = {}
        for anchor in anchors:
            entity = primary_entity(anchor)
            counts[entity] = counts.get(entity, 0) + 1
        return dict(sorted(counts.items()))

    def replace_for_entity_diversity() -> str | None:
        if sampled_count <= 1 or len(selected_drilldown_anchors) < 2:
            return None
        eligible_entities = sorted({
            primary_entity(item)
            for item in ranked
            if primary_entity(item) != "unknown_entity"
            and float(item.get("anchor_score", {}).get("total_score") or 0) >= 2.0
        })
        selected_entities = sorted({
            primary_entity(item)
            for item in selected_drilldown_anchors
            if primary_entity(item) != "unknown_entity"
        })
        target_entity_count = min(max_selected, len(eligible_entities), sampled_count, 3)
        if len(eligible_entities) < 2:
            return "only_one_entity_has_valid_anchor"
        if len(selected_entities) >= target_entity_count:
            return "entity_diversity_satisfied"
        replacements_made = 0
        while len(selected_entities) < target_entity_count:
            selected_counts = entity_distribution(selected_drilldown_anchors)
            replacement_options = [
                (skip_index, item.get("anchor", {}))
                for skip_index, item in enumerate(skipped_anchors)
                if isinstance(item, dict)
                and isinstance(item.get("anchor"), dict)
                and primary_entity(item.get("anchor", {})) not in selected_entities
                and primary_entity(item.get("anchor", {})) != "unknown_entity"
                and float(item.get("anchor", {}).get("anchor_score", {}).get("total_score") or 0) >= 2.0
            ]
            replacement_options.sort(
                key=lambda pair: float(pair[1].get("anchor_score", {}).get("total_score") or 0),
                reverse=True,
            )
            replacement_applied = False
            for skip_index, replacement in replacement_options:
                replacement_domain = str(replacement.get("observation_domain") or "unknown_domain")
                replacement_type = str(replacement.get("anchor_type") or "")
                victims = sorted(
                    [
                        item for item in selected_drilldown_anchors
                        if selected_counts.get(primary_entity(item), 0) > 1
                    ],
                    key=lambda item: float(item.get("anchor_score", {}).get("total_score") or 0),
                )
                for victim in victims:
                    remaining = [item for item in selected_drilldown_anchors if item is not victim]
                    domain_counts = _count_by_key(remaining, "observation_domain")
                    type_counts = _count_by_key(remaining, "anchor_type")
                    if domain_counts.get(replacement_domain, 0) + 1 > MAX_SELECTED_ANCHORS_PER_DOMAIN:
                        continue
                    if type_counts.get(replacement_type, 0) + 1 > MAX_SELECTED_ANCHORS_PER_TYPE:
                        continue
                    selected_drilldown_anchors.remove(victim)
                    victim["selection_status"] = "skipped_by_entity_diversity"
                    victim_reasons = list(victim.get("anchor_priority_reason", []) or [])
                    victim_reasons.append("replaced_to_cover_another_sample_entity")
                    victim["anchor_priority_reason"] = unique_strings(victim_reasons)
                    skipped_anchors.append(
                        {
                            "anchor": victim,
                            "skip_reason": "skipped_by_entity_diversity",
                            "anchor_priority_reason": victim.get("anchor_priority_reason", []),
                        }
                    )
                    skipped_anchors.pop(skip_index)
                    replacement["selection_status"] = "selected"
                    replacement_reasons = list(replacement.get("anchor_priority_reason", []) or [])
                    replacement_reasons.append("selected_for_entity_diversity")
                    replacement["anchor_priority_reason"] = unique_strings(replacement_reasons)
                    selected_drilldown_anchors.append(replacement)
                    selected_entities = sorted({
                        primary_entity(item)
                        for item in selected_drilldown_anchors
                        if primary_entity(item) != "unknown_entity"
                    })
                    replacements_made += 1
                    replacement_applied = True
                    break
                if replacement_applied:
                    break
            if not replacement_applied:
                break
        if len(selected_entities) >= target_entity_count:
            return "replaced_overrepresented_entity_anchor" if replacements_made else "entity_diversity_satisfied"
        return "eligible_cross_entity_anchor_available_but_blocked_by_score_or_caps"

    represented_domains: set[str] = set()
    for item in ranked:
        if len(selected_drilldown_anchors) >= max_selected:
            break
        domain = str(item.get("observation_domain") or "unknown_domain")
        if domain in represented_domains:
            continue
        ok, reason = can_select(item)
        if ok:
            select_item(item, reason="plan_only" if reason == "plan_only" else "domain_diversity")
            represented_domains.add(domain)

    for item in ranked:
        if item.get("selection_status") in {"selected", "plan_only"}:
            continue
        ok, reason = can_select(item)
        if ok:
            select_item(item, reason="plan_only" if reason == "plan_only" else "score_fill")
        else:
            skip_item(item, reason)

    entity_diversity_adjustment = replace_for_entity_diversity()
    selected_keys = {
        (str(item.get("anchor_type") or ""), _anchor_ref(item))
        for item in selected_drilldown_anchors
    }
    eligible_entities = sorted({
        primary_entity(item)
        for item in scored
        if primary_entity(item) != "unknown_entity"
        and float(item.get("anchor_score", {}).get("total_score") or 0) >= 2.0
    })
    selected_entity_distribution = entity_distribution(selected_drilldown_anchors)
    selected_entity_count = len([
        entity for entity in selected_entity_distribution
        if entity != "unknown_entity"
    ])
    target_entity_count = min(max_selected, len(eligible_entities), sampled_count, 3)
    if sampled_count <= 1:
        entity_diversity_reason = "single_sample_no_cross_entity_requirement"
    elif len(eligible_entities) <= 1:
        entity_diversity_reason = "only_one_entity_has_valid_anchor"
    elif selected_entity_count >= target_entity_count:
        entity_diversity_reason = "selected_anchors_cover_required_entities"
    else:
        entity_diversity_reason = entity_diversity_adjustment or "entity_diversity_blocked_by_score_or_caps"

    enriched_pool = sorted(scored, key=lambda item: int(item.get("_original_index") or 0))
    for item in enriched_pool:
        item.pop("_original_index", None)
    for item in selected_drilldown_anchors:
        item.pop("_original_index", None)
    for item in skipped_anchors:
        if isinstance(item.get("anchor"), dict):
            item["anchor"].pop("_original_index", None)

    if not skipped_anchors and scored:
        low_value = min(scored, key=lambda item: float(item.get("anchor_score", {}).get("total_score") or 0))
        low_key = (str(low_value.get("anchor_type") or ""), _anchor_ref(low_value))
        if low_key not in selected_keys:
            skipped_anchors.append(
                {
                    "anchor": low_value,
                    "skip_reason": "low_value_anchor",
                    "anchor_priority_reason": low_value.get("anchor_priority_reason", []),
                }
            )

    summary = {
        "scoring_version": "anchor_scoring_v2_distinct_entity_diversity",
        "candidate_anchor_count": len(enriched_pool),
        "selected_anchor_count": len(selected_drilldown_anchors),
        "skipped_anchor_count": len(skipped_anchors),
        "max_selected_drilldown_anchors": max_selected,
        "max_selected_per_domain": MAX_SELECTED_ANCHORS_PER_DOMAIN,
        "max_selected_per_anchor_type": MAX_SELECTED_ANCHORS_PER_TYPE,
        "batch_support_enabled": sampled_count > 1,
        "limited_commonality": sampled_count <= 1,
        "domain_distribution": _count_by_key(enriched_pool, "observation_domain"),
        "selected_domain_distribution": _count_by_key(selected_drilldown_anchors, "observation_domain"),
        "skipped_domain_distribution": _count_by_key([
            item.get("anchor", {}) for item in skipped_anchors if isinstance(item.get("anchor"), dict)
        ], "observation_domain"),
        "entity_distribution": entity_distribution(enriched_pool),
        "selected_entity_distribution": selected_entity_distribution,
        "skipped_entity_distribution": entity_distribution([
            item.get("anchor", {}) for item in skipped_anchors if isinstance(item.get("anchor"), dict)
        ]),
        "eligible_entity_count": len(eligible_entities),
        "eligible_entities": eligible_entities,
        "selected_entity_count": selected_entity_count,
        "target_selected_entity_count": target_entity_count,
        "entity_diversity_reason": entity_diversity_reason,
        "entity_diversity_adjustment": entity_diversity_adjustment or "not_needed",
        "anchor_type_distribution": _count_by_key(enriched_pool, "anchor_type"),
        "selected_anchor_type_distribution": _count_by_key(selected_drilldown_anchors, "anchor_type"),
        "skipped_anchor_type_distribution": _count_by_key([
            item.get("anchor", {}) for item in skipped_anchors if isinstance(item.get("anchor"), dict)
        ], "anchor_type"),
        "selection_policy": "domain_diversity_then_score_with_domain_type_and_entity_diversity_caps",
        "batch_support_count_semantics": "distinct_sampled_entity_count",
        "raw_candidate_anchor_count": len(candidate_anchor_pool),
        "batch_anchor_pool_count": len(enriched_pool),
        "batch_anchor_count": len([item for item in enriched_pool if item.get("batch_anchor_scope") == "batch_anchor"]),
        "single_entity_anchor_count": len([item for item in enriched_pool if item.get("batch_anchor_scope") == "single_entity_anchor"]),
        "score_dimensions": [
            "anchor_presence",
            "anomaly_strength",
            "batch_support_count",
            "cross_domain_support",
            "chain_value",
            "cost_level",
            "expansion_risk",
            "false_positive_risk",
            "evidence_quality",
            "current_observation_support",
        ],
    }
    return {
        "candidate_anchor_pool": enriched_pool,
        "batch_anchor_pool": enriched_pool,
        "selected_drilldown_anchors": selected_drilldown_anchors,
        "skipped_anchors": skipped_anchors,
        "anchor_scoring_summary": summary,
    }


def build_candidate_anchor_pool_artifact(
    *,
    round_id: int,
    source_observations: list[dict[str, Any]],
    mode: str,
) -> list[dict[str, Any]]:
    anchors: list[dict[str, Any]] = []
    for observation in source_observations:
        action = str(observation.get("action") or "")
        source_id = str(observation.get("source_id") or "")
        quality = str(observation.get("quality_class") or "unknown")
        for handle in observation.get("parsed_body_field_handles", []) or []:
            canonical = str(handle.get("canonical_field") or handle.get("field") or "")
            value = str(handle.get("value") or "").strip()
            if not value:
                continue
            if canonical == "photo_id":
                _append_anchor(
                    anchors,
                    anchor_type="candidate_photo_id",
                    value=value,
                    produced_by=source_id or action,
                    observation_domain="content_domain",
                    confidence="current_observation",
                    next_allowed_interfaces=["archives_photo_profile", "archives_photo_meta"],
                    cap_key="photo_anchor_top_k",
                    reason="photo_id_extracted_from_current_observation",
                    source_quality=quality,
                    evidence_source="current_observation",
                    field_path=str(handle.get("field_path") or ""),
                )
            elif canonical in {"device_id", "publish_device", "operation_device", "login_device"}:
                _append_anchor(
                    anchors,
                    anchor_type="candidate_device_id",
                    value=value,
                    produced_by=source_id or action,
                    observation_domain="device_domain",
                    confidence="current_observation",
                    next_allowed_interfaces=["track_analysis_check_data_ready", "weapon_inventory"],
                    cap_key="device_anchor_top_k",
                    reason=f"{canonical}_extracted_from_current_observation",
                    source_quality=quality,
                    evidence_source="current_observation",
                    field_path=str(handle.get("field_path") or ""),
                )
            elif canonical in {"policy_code", "event_id", "source_id"}:
                _append_anchor(
                    anchors,
                    anchor_type=f"candidate_{canonical}",
                    value=value,
                    produced_by=source_id or action,
                    observation_domain="strategy_domain",
                    confidence="current_observation",
                    next_allowed_interfaces=["rcp_event_tree_or_decision", "rcp_feature_info_by_keys"],
                    cap_key="strategy_anchor_top_k",
                    reason=f"{canonical}_extracted_from_current_observation",
                    source_quality=quality,
                    evidence_source="current_observation",
                    field_path=str(handle.get("field_path") or ""),
                )
            elif canonical == "ip":
                _append_anchor(
                    anchors,
                    anchor_type="candidate_ip",
                    value=value,
                    produced_by=source_id or action,
                    observation_domain="network_domain",
                    confidence="current_observation",
                    next_allowed_interfaces=["login_logs_search"],
                    cap_key="network_anchor_top_k",
                    reason="ip_extracted_from_current_observation",
                    source_quality=quality,
                    evidence_source="current_observation",
                    field_path=str(handle.get("field_path") or ""),
                )
            elif canonical in {"relation_anchor", "comment_id", "message_anchor", "live_id"}:
                next_interfaces = (
                    ["archives_comment_search", "archives_livestream_comment_detail"]
                    if canonical == "comment_id"
                    else ["archives_private_message_search"]
                    if canonical == "message_anchor"
                    else ["archives_livestream_home_info", "archives_livestream_home_meta"]
                    if canonical == "live_id"
                    else ["archives_related_users", "archives_fans_list", "archives_follow_list"]
                )
                domain = "content_domain" if canonical == "live_id" else "social_domain"
                _append_anchor(
                    anchors,
                    anchor_type=f"candidate_{canonical}",
                    value=value,
                    produced_by=source_id or action,
                    observation_domain=domain,
                    confidence="current_observation",
                    next_allowed_interfaces=next_interfaces,
                    cap_key=f"{canonical}_anchor_top_k",
                    reason=f"{canonical}_extracted_from_current_observation",
                    source_quality=quality,
                    evidence_source="current_observation",
                    field_path=str(handle.get("field_path") or ""),
                )
            elif canonical in {"report_id", "review_id", "punish_id"}:
                domain = "feedback_domain" if canonical == "report_id" else "enforcement_domain"
                next_interfaces = (
                    ["archives_user_report_search", "archives_negative_report"]
                    if canonical == "report_id"
                    else ["archives_review_logs", "archives_punish_status"]
                )
                _append_anchor(
                    anchors,
                    anchor_type=f"candidate_{canonical}",
                    value=value,
                    produced_by=source_id or action,
                    observation_domain=domain,
                    confidence="current_observation",
                    next_allowed_interfaces=next_interfaces,
                    cap_key=f"{canonical}_anchor_top_k",
                    reason=f"{canonical}_extracted_from_current_observation",
                    source_quality=quality,
                    evidence_source="current_observation",
                    field_path=str(handle.get("field_path") or ""),
                )
        for candidate in observation.get("candidate_device_ids", []) or []:
            if not isinstance(candidate, dict):
                continue
            device_id = str(candidate.get("device_id") or "").strip()
            if not device_id:
                continue
            _append_anchor(
                anchors,
                anchor_type="candidate_device_id",
                value=device_id,
                produced_by=str(candidate.get("source_id") or source_id or action),
                observation_domain="device_domain",
                confidence="current_observation",
                next_allowed_interfaces=["track_analysis_check_data_ready", "weapon_inventory"],
                cap_key="device_anchor_top_k",
                reason="candidate_device_extracted_from_safe_observation",
                source_quality=quality,
                evidence_source="current_observation",
                field_path=str(candidate.get("field_path") or ""),
            )
    if not anchors and mode == "dry_run":
        for anchor_type, produced_by, domain, next_interfaces, cap_key in [
            ("candidate_photo_id", "archives_photo_search", "content_domain", ["archives_gallery_photo_list", "archives_photo_profile", "archives_photo_meta"], "photo_anchor_top_k"),
            ("candidate_device_id", "weapon_inventory", "device_domain", ["track_analysis_check_data_ready", "weapon_inventory"], "device_anchor_top_k"),
            ("candidate_policy_code", "rcp_fast_query_hbase", "strategy_domain", ["rcp_event_tree_or_decision", "rcp_feature_info_by_keys"], "strategy_anchor_top_k"),
        ]:
            _append_anchor(
                anchors,
                anchor_type=anchor_type,
                safe_ref=f"round_{round_id}_{anchor_type}_dry_run_hint",
                produced_by=produced_by,
                observation_domain=domain,
                confidence="dry_run_anchor_hint",
                next_allowed_interfaces=next_interfaces,
                cap_key=cap_key,
                reason="dry_run_structure_hint_not_current_platform_evidence",
                source_quality="not_executed",
                evidence_source="dry_run_structure_only",
            )
    return anchors[:MAX_CANDIDATE_ANCHORS_PER_ROUND]


MOCK_OBSERVATION_CANONICAL_FIELDS: dict[str, str] = {
    "candidate_photo_id": "photo_id",
    "candidate_device_id": "device_id",
    "candidate_ip": "ip",
    "candidate_policy_code": "policy_code",
    "candidate_event_id": "event_id",
    "candidate_relation_anchor": "relation_anchor",
    "candidate_comment_id": "comment_id",
    "candidate_message_anchor": "message_anchor",
    "candidate_live_id": "live_id",
    "candidate_report_id": "report_id",
    "candidate_review_id": "review_id",
    "candidate_punish_id": "punish_id",
    "login_ip": "ip_ua",
    "login_ua": "ip_ua",
}


def build_mock_current_source_observations(
    mock_current_observations: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    observations: list[dict[str, Any]] = []
    for index, item in enumerate(mock_current_observations or [], start=1):
        if not isinstance(item, dict):
            continue
        action = str(item.get("action") or "mock_current_observation")
        source_id = str(item.get("source_id") or f"mock_current_observation_{index}")
        fields = item.get("fields") if isinstance(item.get("fields"), dict) else {}
        handles: list[dict[str, Any]] = []
        extracted_fields: list[str] = []
        candidate_device_ids: list[dict[str, Any]] = []
        for field, value in fields.items():
            field_text = str(field)
            if _is_credential_secret_key(field_text) or value is None:
                continue
            canonical = MOCK_OBSERVATION_CANONICAL_FIELDS.get(field_text, field_text)
            value_text = str(value).strip()
            if not value_text:
                continue
            handles.append(
                {
                    "field": field_text,
                    "canonical_field": canonical,
                    "field_path": f"$.mock_current_observation.{field_text}",
                    "value": value_text,
                    "source_id": source_id,
                    "evidence_source": "current_observation",
                }
            )
            extracted_fields.append(canonical)
            if canonical in {"device_id", "publish_device", "operation_device", "login_device"}:
                candidate_device_ids.append(
                    {
                        "device_id": value_text,
                        "source_id": source_id,
                        "action": action,
                        "field_path": f"$.mock_current_observation.{field_text}",
                    }
                )
        observations.append(
            {
                "source_id": source_id,
                "action": action,
                "chain_section": "mock_current_observation",
                "quality_class": "completed",
                "role": "mock-shaped current observation fixture",
                "expected_business_fields": sorted(set(extracted_fields)),
                "extracted_business_fields": unique_strings(extracted_fields),
                "observed_field_handles": handles,
                "parsed_body_field_handles": handles,
                "missing_business_fields": [],
                "candidate_device_ids": candidate_device_ids,
                "passthrough_row_cap": {},
                "interpretation_flags": [
                    "mock_current_observation_fixture",
                    "current_observation_support_for_artifact_regression",
                    "not_live_platform_evidence",
                ],
                "breakpoint_type": None,
                "evidence_use": "business_evidence_candidate" if handles else "transport_only_boundary",
                "is_low_risk_counter_evidence": False,
            }
        )
    return observations


def build_drilldown_artifacts(
    *,
    candidate_anchor_pool: list[dict[str, Any]],
    batch_anchor_pool: list[dict[str, Any]],
    selected_drilldown_anchors: list[dict[str, Any]],
    source_observations: list[dict[str, Any]],
    sampled_entities: list[str],
    mode: str,
) -> dict[str, Any]:
    cards: list[dict[str, Any]] = []
    stop_reasons: list[str] = []
    observations_by_action: dict[str, list[dict[str, Any]]] = {}
    for observation in source_observations:
        observations_by_action.setdefault(str(observation.get("action") or ""), []).append(observation)
    selected_refs = {_anchor_ref(anchor) for anchor in selected_drilldown_anchors}
    for anchor in selected_drilldown_anchors:
        next_interfaces = list(anchor.get("next_allowed_interfaces") or [])[:MAX_L2_INTERFACES_PER_ANCHOR]
        supporting_entities = unique_strings([str(item) for item in anchor.get("supporting_entities", []) or []])
        if not supporting_entities and anchor.get("anchor_score"):
            supporting_entities = unique_strings([str(item) for item in anchor.get("anchor_score", {}).get("supporting_entities", []) or []])
        missing_anchor_entities = [
            str(entity) for entity in sampled_entities
            if supporting_entities and str(entity) not in set(supporting_entities)
        ]
        if not next_interfaces:
            stop_reason = "missing_contract"
            stop_reasons.append(stop_reason)
            cards.append(
                {
                    "anchor": anchor,
                    "applicable_entities": supporting_entities,
                    "skipped_entities_missing_anchor": missing_anchor_entities,
                    "interface": None,
                    "extracted_facts": [],
                    "new_anchors": [],
                    "missing_fields": ["next_allowed_interfaces"],
                    "source_quality": "missing_contract",
                    "stop_reason": stop_reason,
                }
            )
            continue
        for interface in next_interfaces:
            observations = observations_by_action.get(interface, [])
            extracted_fields = unique_strings([
                str(field)
                for observation in observations
                for field in observation.get("extracted_business_fields", [])
            ])
            if not anchor.get("value"):
                stop_reason = "skipped_missing_anchor"
                source_quality = "skipped_missing_anchor"
            elif mode == "dry_run":
                stop_reason = "planned_only_dry_run"
                source_quality = "not_executed"
            elif not observations:
                stop_reason = "missing_contract"
                source_quality = "missing_contract"
            elif extracted_fields:
                stop_reason = "bounded_drilldown_completed"
                source_quality = "completed_or_partial"
            else:
                stop_reason = "business_fields_not_extracted"
                source_quality = "partial"
            stop_reasons.append(stop_reason)
            cards.append(
                {
                    "anchor": anchor,
                    "applicable_entities": supporting_entities,
                    "skipped_entities_missing_anchor": missing_anchor_entities,
                    "interface": interface,
                    "extracted_facts": extracted_fields,
                    "new_anchors": [],
                    "missing_fields": [] if extracted_fields else _expected_anchor_types_for_action(interface),
                    "source_quality": source_quality,
                    "stop_reason": stop_reason,
                }
            )
    return {
        "drilldown_evidence_card": cards,
        "new_anchor_pool": [],
        "tracking_commonality": [
            {
                "signal_name": "bounded_drilldown_not_complete",
                "supporting_anchors": [
                    str(anchor.get("safe_ref") or anchor.get("value") or anchor.get("anchor_type"))
                    for anchor in selected_drilldown_anchors
                ],
                "selected_anchor_count": len(selected_drilldown_anchors),
                "candidate_anchor_count": len(candidate_anchor_pool),
                "batch_anchor_count": len(batch_anchor_pool),
                "drilldown_selection_policy": "batch_anchor_pool_then_selected_drilldown_anchors_top_k_only",
                "evidence_source": "current_observation" if mode != "dry_run" else "dry_run_structure_only",
                "confidence": "not_evaluated_in_dry_run" if mode == "dry_run" else "partial",
                "not_final_conclusion": True,
            }
        ],
        "selected_anchor_refs": sorted(ref for ref in selected_refs if ref),
        "stop_reason": unique_strings(stop_reasons) or ["no_candidate_anchor_available"],
    }


def enrich_source_quality_with_artifacts(
    source_quality: dict[str, Any],
    *,
    drilldown: dict[str, Any],
    skipped_anchors: list[dict[str, Any]],
    source_observations: list[dict[str, Any]],
) -> dict[str, Any]:
    enriched = {
        key: list(value) if isinstance(value, list) else value
        for key, value in source_quality.items()
    }

    def add(bucket: str, value: str) -> None:
        if not value:
            return
        current = enriched.setdefault(bucket, [])
        if isinstance(current, list) and value not in current:
            current.append(value)

    for observation in source_observations:
        source_id = str(observation.get("source_id") or "")
        flags = set(str(flag) for flag in observation.get("interpretation_flags", []) or [])
        if "mock_current_observation_fixture" in flags and observation.get("quality_class") == "completed":
            add("completed", source_id)

    for card in drilldown.get("drilldown_evidence_card", []) or []:
        if not isinstance(card, dict):
            continue
        status = str(card.get("source_quality") or "")
        interface = str(card.get("interface") or "")
        anchor = card.get("anchor") if isinstance(card.get("anchor"), dict) else {}
        ref = interface or str(anchor.get("safe_ref") or anchor.get("value") or anchor.get("anchor_type") or "")
        for entity in card.get("skipped_entities_missing_anchor", []) or []:
            add("skipped_missing_anchor", f"{entity}:{interface or anchor.get('anchor_type')}")
        if status in {
            "skipped_missing_anchor",
            "skipped_by_cap",
            "missing_contract",
            "timeout",
            "no_data",
            "parse_error",
            "authorization_required",
            "not_executed",
        }:
            add(status, ref)
        elif status == "planned_only_dry_run":
            add("not_executed", ref)
        elif status == "completed_or_partial":
            add("partial", ref)
    for item in skipped_anchors:
        if not isinstance(item, dict):
            continue
        reason = str(item.get("skip_reason") or "")
        anchor = item.get("anchor") if isinstance(item.get("anchor"), dict) else {}
        ref = _anchor_ref(anchor)
        if reason in {
            "skipped_by_cap",
            "skipped_by_domain_cap",
            "skipped_by_type_cap",
            "skipped_by_entity_diversity",
            "skipped_low_score",
            "low_value_anchor",
            "duplicate_anchor",
        }:
            add(reason, ref)
    return enriched


def _distinct_signal_support_entities(support_entities: list[Any], sampled_entities: list[str]) -> list[str]:
    sampled = [str(entity) for entity in sampled_entities]
    normalized: list[str] = []
    for raw in support_entities:
        value = str(raw or "").strip()
        if not value:
            continue
        index = _entity_index_from_batch_source_id(value)
        if index is not None and 1 <= index <= len(sampled):
            normalized.append(sampled[index - 1])
        else:
            normalized.append(value)
    return unique_strings(normalized)


def build_commonality_artifacts(
    *,
    sampled_entities: list[str],
    source_commonality_cards: list[dict[str, Any]],
    candidate_anchor_pool: list[dict[str, Any]],
    batch_anchor_pool: list[dict[str, Any]],
    selected_drilldown_anchors: list[dict[str, Any]],
    source_quality: dict[str, Any],
    mode: str,
) -> dict[str, Any]:
    # Each live round is only a bounded sample of the requested batch.
    # Stable commonality is reserved for the cumulative rolling summary.
    limited_commonality = True
    source_commonality_domains = {
        "login_log": ["behavior_domain", "network_domain"],
        "archive_admin_profile": ["account_domain"],
        "weapon_graph_risk": ["device_domain", "group_domain"],
        "content_action_anchor": ["content_domain", "behavior_domain"],
        "strategy_hit": ["strategy_domain"],
        "strategy_hit_detail": ["strategy_domain"],
        "track_frontend_behavior": ["behavior_domain", "device_domain"],
        "feedback_signal": ["feedback_domain"],
        "enforcement_review": ["enforcement_domain", "behavior_domain"],
    }
    shared_signal_items: list[dict[str, Any]] = []
    card_domains: list[str] = []
    for card in source_commonality_cards:
        card_domains.extend(source_commonality_domains.get(str(card.get("source_name") or ""), []))
        for signal in card.get("shared_signals", []) or []:
            if not isinstance(signal, dict) or not signal.get("signal_name"):
                continue
            support_count = signal.get("support_count")
            supporting_entities = _distinct_signal_support_entities(
                list(signal.get("support_entities") or []),
                sampled_entities,
            )
            distinct_support_count = len(supporting_entities) or int(support_count or 0)
            coverage_commonality = _is_coverage_commonality_signal(signal)
            declared_type = str(signal.get("commonality_type") or "")
            candidate_extraction_signal = _is_candidate_extraction_signal(signal)
            group_eligible = bool(signal.get("eligible_for_group_candidate") is True) and not candidate_extraction_signal
            commonality_anchor = bool(
                not limited_commonality
                and distinct_support_count >= COMMONALITY_ANCHOR_MIN_SUPPORT
                and group_eligible
                and not coverage_commonality
            )
            commonality_type = (
                "coverage_commonality" if coverage_commonality else
                "anchor_lead_commonality" if candidate_extraction_signal else
                declared_type if declared_type else
                "anchor_commonality" if commonality_anchor else
                "anchor_lead_commonality"
            )
            risk_commonality = commonality_type in RISK_COMMONALITY_TYPES and not coverage_commonality
            shared_signal_items.append(
                {
                    "signal_name": str(signal.get("signal_name")),
                    "supporting_current_evidence": supporting_entities,
                    "support_count": distinct_support_count,
                    "batch_support_count": distinct_support_count,
                    "support_ratio": signal.get("support_ratio"),
                    "commonality_anchor": commonality_anchor,
                    "commonality_type": commonality_type,
                    "risk_commonality": risk_commonality,
                    "eligible_for_group_candidate": bool(risk_commonality and group_eligible),
                    "limited_commonality": limited_commonality,
                    "evidence_source": "current_observation",
                    "source_name": card.get("source_name"),
                    "not_final_conclusion": True,
                }
            )
    for anchor in batch_anchor_pool:
        if not isinstance(anchor, dict) or anchor.get("batch_anchor_scope") != "batch_anchor":
            continue
        support_entities = unique_strings([str(item) for item in anchor.get("supporting_entities", []) or []])
        if limited_commonality or len(support_entities) < COMMONALITY_ANCHOR_MIN_SUPPORT:
            continue
        shared_signal_items.append(
            {
                "signal_name": _batch_signal_name(str(anchor.get("anchor_type") or ""), "batch_anchor"),
                "anchor_type": anchor.get("anchor_type"),
                "anchor_value_or_safe_ref": anchor.get("value") or anchor.get("safe_ref"),
                "supporting_current_evidence": support_entities,
                "support_count": len(support_entities),
                "batch_support_count": len(support_entities),
                "support_ratio": round(len(support_entities) / len(sampled_entities), 4) if sampled_entities else None,
                "commonality_anchor": True,
                "commonality_type": "anchor_commonality",
                "risk_commonality": True,
                "eligible_for_group_candidate": True,
                "batch_anchor_scope": "batch_anchor",
                "limited_commonality": False,
                "evidence_source": "current_observation",
                "source_name": "batch_anchor_pool",
                "not_final_conclusion": True,
            }
        )
    if not shared_signal_items and any(anchor.get("evidence_source") == "current_observation" for anchor in candidate_anchor_pool):
        support_count = len([
            anchor for anchor in candidate_anchor_pool
            if anchor.get("evidence_source") == "current_observation"
        ])
        shared_signal_items.append(
            {
                "signal_name": "current_observation_anchor_available",
                "supporting_current_evidence": [
                    str(anchor.get("produced_by"))
                    for anchor in candidate_anchor_pool
                    if anchor.get("evidence_source") == "current_observation"
                ],
                "support_count": support_count,
                "batch_support_count": support_count if not limited_commonality else 1,
                "support_ratio": None,
                "commonality_anchor": False,
                "commonality_type": "anchor_lead_commonality",
                "risk_commonality": False,
                "eligible_for_group_candidate": False,
                "limited_commonality": limited_commonality,
                "evidence_source": "current_observation",
                "source_name": "candidate_anchor_pool",
                "not_final_conclusion": True,
            }
        )
    shared_signal_names = unique_strings([
        str(signal.get("signal_name")) for signal in shared_signal_items
    ])
    risk_shared_signal_items = [
        signal for signal in shared_signal_items
        if _is_risk_commonality_signal(signal)
    ]
    risk_shared_signal_names = unique_strings([
        str(signal.get("signal_name")) for signal in risk_shared_signal_items
    ])
    coverage_signal_names = unique_strings([
        str(signal.get("signal_name")) for signal in shared_signal_items
        if _is_coverage_commonality_signal(signal)
    ])
    domains = unique_strings([
        str(anchor.get("observation_domain"))
        for anchor in candidate_anchor_pool
        if anchor.get("observation_domain")
    ] + card_domains)
    commonality_matrix = [
        {
            "shared_signals": shared_signal_items,
            "coverage_commonality": coverage_signal_names,
            "risk_commonality": risk_shared_signal_names,
            "differentiating_signals": [],
            "counter_evidence": [],
            "source_domains": domains,
            "evidence_source": "current_observation" if shared_signal_names else "dry_run_structure_only",
            "confidence": "partial" if shared_signal_names else "not_evaluated_in_dry_run",
            "limited_commonality": limited_commonality,
            "not_final_conclusion": True,
        }
    ]
    abnormal_correlation = [
        {
            "relation_family": "content_device_strategy_correlation_candidate",
            "source_domain": "content_domain",
            "target_domain": "device_domain|strategy_domain",
            "evidence_basis": shared_signal_names or ["candidate_anchor_pool"],
            "expected_normal_pattern": "stable device/content/behavior continuity with explainable strategy context",
            "abnormal_pattern": "historical risk patterns may share device, content, strategy, or behavior anchors across small-account matrices",
            "strength": "hypothesis_only" if mode == "dry_run" else "partial",
            "caveat": "expert_risk_signal_input_cannot_replace_current_evidence",
            "not_final_conclusion": True,
        }
    ]
    relation_seed_candidates = [
        anchor for anchor in selected_drilldown_anchors
        if anchor.get("value")
        and anchor.get("observation_domain") in {"device_domain", "network_domain", "social_domain"}
        and anchor.get("selection_status") == "selected"
    ]
    seed_anchor = relation_seed_candidates[0] if relation_seed_candidates else {"anchor_type": "none", "safe_ref": "no_selected_relation_anchor_available"}
    seed_has_value = bool(seed_anchor.get("value"))
    seed_domain = str(seed_anchor.get("observation_domain") or "")
    relation_expansion_result = [
        {
            "seed_anchor": seed_anchor,
            "edge_type": {
                "device_domain": "same_device_anchor",
                "network_domain": "same_network_anchor",
                "social_domain": "same_social_relation_anchor",
            }.get(seed_domain, "no_selected_relation_anchor"),
            "expansion_depth": 1 if seed_has_value else 0,
            "entity_cap": 10,
            "returned_entities": [],
            "edge_strength": "not_evaluated_in_dry_run" if mode == "dry_run" and seed_has_value else "partial" if seed_has_value else "not_started",
            "stop_reason": "bounded_depth_cap_reached" if seed_has_value else "planned_only_missing_selected_relation_anchor",
            "cannot_conclude_boundary": "same_device_ip_social_strategy_edges_are_expansion_leads_not_confirmed_group",
        }
    ]
    selected_anchor_refs = unique_strings([
        str(anchor.get("value") or anchor.get("safe_ref") or anchor.get("anchor_type"))
        for anchor in selected_drilldown_anchors
        if anchor.get("selection_status") in {"selected", "plan_only"}
    ])
    selected_high_value_anchor_refs = unique_strings([
        str(anchor.get("value") or anchor.get("safe_ref") or anchor.get("anchor_type"))
        for anchor in selected_drilldown_anchors
        if anchor.get("selection_status") == "selected"
        and anchor.get("evidence_source") == "current_observation"
    ])
    selected_batch_anchor_refs = unique_strings([
        str(anchor.get("value") or anchor.get("safe_ref") or anchor.get("anchor_type"))
        for anchor in selected_drilldown_anchors
        if anchor.get("selection_status") == "selected"
        and anchor.get("evidence_source") == "current_observation"
        and anchor.get("batch_anchor_scope") == "batch_anchor"
    ])
    context_selected_anchor_refs = unique_strings([
        str(anchor.get("value") or anchor.get("safe_ref") or anchor.get("anchor_type"))
        for anchor in selected_drilldown_anchors
        if anchor.get("selection_status") in {"selected", "plan_only"}
        and anchor.get("batch_anchor_scope") != "batch_anchor"
    ])
    supporting_selected_anchors = selected_high_value_anchor_refs or selected_anchor_refs
    supporting_current_evidence = risk_shared_signal_names or supporting_selected_anchors
    signal_inputs = [
        {
            "evidence_source": "current_observation",
            "signals": risk_shared_signal_names,
            "coverage_signals_not_risk_commonality": coverage_signal_names,
            "supporting_selected_anchors": supporting_selected_anchors,
            "usage_boundary": "supports_candidate_feature_only_not_final_conclusion",
        }
    ]
    hypothesis_inputs = [
        {
            "evidence_source": "historical_risk_pattern",
            "signal": "black_market_small_account_matrices_often_share_device_content_strategy_or_behavior_anchors",
            "usage_boundary": "expert_hypothesis_only_not_current_evidence",
        }
    ]
    candidate_features = [
        {
            "feature_name": "multi_domain_anchor_overlap_candidate",
            "source_domains": domains or ["device_domain", "content_domain", "strategy_domain"],
            "supporting_current_evidence": supporting_current_evidence,
            "supporting_selected_anchors": supporting_selected_anchors,
            "unselected_signal_hypothesis": not bool(supporting_selected_anchors or risk_shared_signal_names),
            "signal_inputs": signal_inputs,
            "hypothesis_inputs": hypothesis_inputs,
            "expert_risk_signal_input": {
                "evidence_source": "historical_risk_pattern",
                "signal": "black_market_small_account_matrices_often_share_device_content_strategy_or_behavior_anchors",
                "usage_boundary": "compatibility_alias_for_hypothesis_inputs_only_not_evidence",
            },
            "confidence": "medium_partial" if risk_shared_signal_names else "anchor_lead_partial" if supporting_selected_anchors else "hypothesis_only",
            "validation_needed": True,
            "false_positive_risk": "medium_high_until_counter_samples_and_wide_table_validation",
            "not_final_conclusion": True,
        }
    ]
    group_profile_candidate = {
        "cluster_id": "group_profile_candidate_round",
        "representative_entities": sampled_entities[:3],
            "shared_domains": domains if risk_shared_signal_items else [],
            "shared_signals": risk_shared_signal_items,
            "coverage_signals_not_group_support": coverage_signal_names,
            "supporting_selected_anchors": selected_batch_anchor_refs if risk_shared_signal_items else [],
            "supporting_selected_batch_anchors": selected_batch_anchor_refs if risk_shared_signal_items else [],
            "context_selected_anchors": context_selected_anchor_refs,
            "supporting_anchor_boundary": (
                "supporting_selected_batch_anchors_can_support_group_candidate; "
                "context_selected_anchors_are_single_entity_or_explanatory_only"
            ),
            "missing_evidence": unique_strings([
                item for item in [
                    "insufficient_risk_commonality" if not risk_shared_signal_items else "validation_layer_required",
                "coverage_commonality_not_group_support" if coverage_signal_names else "",
            "relation_expansion_not_full_graph",
            ] if item
        ]),
        "confidence": "low_limited_single_sample" if limited_commonality and risk_shared_signal_names else "medium_partial" if risk_shared_signal_names else "insufficient_risk_commonality",
        "not_confirmed_as_group": True,
        "required_validation": ["coverage_replay_or_wide_table", "normal_counter_sample_check", "source_quality_completion"],
        "limited_commonality": limited_commonality,
    }
    validation_plan = {
        "validation_goal": "validate candidate group/commonality coverage and false-positive risk before strategy use",
        "required_data": ["full_100_batch_coverage", "control_group_or_counter_samples", "source_quality_by_domain"],
        "dataagent_or_hive_required": True,
        "authorization_required": True,
        "expected_output": "wide_table_aggregate_report_or_batch_validate_report",
        "validation_status": "planned" if mode == "dry_run" else "pending",
    }
    final_evidence_card = {
        "conclusion_state": "dry_run_structure_only" if mode == "dry_run" else "insufficient_support_or_partial",
        "strong_evidence": [],
        "medium_evidence": risk_shared_signal_names,
        "weak_evidence": [],
        "signal_inputs": signal_inputs,
        "hypothesis_inputs": hypothesis_inputs,
        "counter_evidence": [],
        "missing_evidence": [
            "validation_layer_not_executed",
            "candidate_features_not_final_conclusion",
            "relation_expansion_bounded_or_not_executed",
        ],
        "source_quality": source_quality,
        "boundary": [
            "not_final_conclusion",
            "not_confirmed_as_group",
            "no_data_skipped_timeout_missing_contract_not_low_risk_counter_evidence",
            "DataAgent_Hive_not_called",
        ],
    }
    return {
        "base_commonality": {
            "shared_signals": shared_signal_names,
            "coverage_commonality": coverage_signal_names,
            "risk_commonality": risk_shared_signal_names,
            "source_commonality_cards_used": len(source_commonality_cards),
            "not_final_conclusion": True,
        },
        "commonality_matrix": commonality_matrix,
        "abnormal_correlation": abnormal_correlation,
        "relation_expansion_result": relation_expansion_result,
        "group_profile_candidate": group_profile_candidate,
        "candidate_features": candidate_features,
        "validation_plan": validation_plan,
        "final_evidence_card": final_evidence_card,
        "missing_evidence": final_evidence_card["missing_evidence"],
    }


def build_round_orchestration_artifacts(
    *,
    round_id: int,
    sampled_entities: list[str],
    source_plan: list[SourcePlanItem],
    source_quality_matrix: dict[str, Any],
    source_observations: list[dict[str, Any]],
    source_commonality_cards: list[dict[str, Any]],
    mode: str,
    disabled_actions: set[str] | None,
) -> dict[str, Any]:
    seed_entity = _round_seed_entity(sampled_entities)
    task_route = {
        "route_mode": "batch_interface_orchestration",
        "runtime_mode": "sample_expand_validate_mode",
        "input_type": seed_entity["input_type"],
        "allowed_layers": [
            "input_route_layer",
            "base_summary_layer",
            "anchor_drilldown_layer",
            "cross_domain_commonality_layer",
            "validation_layer",
            "judgement_output_layer",
        ],
        "forbidden_expansion": [
            "no_70_action_cartesian_product",
            "no_full_graph_relation_expansion",
            "no_full_photo_comment_message_fan_follow_expand_without_anchor_and_cap",
        ],
        "authorization_boundary": [
            "DataAgent_Hive_requires_user_authorization",
            "dry_run_is_not_platform_evidence",
        ],
    }
    base_interface_plan = build_base_interface_plan_artifact(source_plan, disabled_actions=disabled_actions)
    base_summary_card = build_base_summary_card_artifact(
        round_id=round_id,
        sampled_entities=sampled_entities,
        source_plan=source_plan,
        source_quality_matrix=source_quality_matrix,
        source_observations=source_observations,
    )
    candidate_anchor_pool = build_candidate_anchor_pool_artifact(
        round_id=round_id,
        source_observations=source_observations,
        mode=mode,
    )
    anchor_selection = score_candidate_anchors(
        candidate_anchor_pool=candidate_anchor_pool,
        sampled_entities=sampled_entities,
        source_observations=source_observations,
    )
    candidate_anchor_pool = anchor_selection["candidate_anchor_pool"]
    base_summary_card["candidate_anchors"] = candidate_anchor_pool
    drilldown = build_drilldown_artifacts(
        candidate_anchor_pool=candidate_anchor_pool,
        batch_anchor_pool=anchor_selection["batch_anchor_pool"],
        selected_drilldown_anchors=anchor_selection["selected_drilldown_anchors"],
        source_observations=source_observations,
        sampled_entities=sampled_entities,
        mode=mode,
    )
    normalized_source_quality = enrich_source_quality_with_artifacts(
        _normalized_interface_source_quality(source_quality_matrix),
        drilldown=drilldown,
        skipped_anchors=anchor_selection["skipped_anchors"],
        source_observations=source_observations,
    )
    commonality = build_commonality_artifacts(
        sampled_entities=sampled_entities,
        source_commonality_cards=source_commonality_cards,
        candidate_anchor_pool=candidate_anchor_pool,
        batch_anchor_pool=anchor_selection["batch_anchor_pool"],
        selected_drilldown_anchors=anchor_selection["selected_drilldown_anchors"],
        source_quality=normalized_source_quality,
        mode=mode,
    )
    return {
        "task_route": task_route,
        "seed_entity": seed_entity,
        "base_interface_plan": base_interface_plan,
        "base_summary_card": base_summary_card,
        "base_commonality": commonality["base_commonality"],
        "candidate_anchor_pool": candidate_anchor_pool,
        "batch_anchor_pool": anchor_selection["batch_anchor_pool"],
        "anchor_scoring_summary": anchor_selection["anchor_scoring_summary"],
        "selected_drilldown_anchors": anchor_selection["selected_drilldown_anchors"],
        "skipped_anchors": anchor_selection["skipped_anchors"],
        "drilldown_evidence_card": drilldown["drilldown_evidence_card"],
        "new_anchor_pool": drilldown["new_anchor_pool"],
        "tracking_commonality": drilldown["tracking_commonality"],
        "stop_reason": drilldown["stop_reason"],
        "commonality_matrix": commonality["commonality_matrix"],
        "abnormal_correlation": commonality["abnormal_correlation"],
        "relation_expansion_result": commonality["relation_expansion_result"],
        "group_profile_candidate": commonality["group_profile_candidate"],
        "candidate_features": commonality["candidate_features"],
        "validation_plan": commonality["validation_plan"],
        "final_evidence_card": commonality["final_evidence_card"],
        "missing_evidence": commonality["missing_evidence"],
        "source_quality": normalized_source_quality,
    }


def build_round_result(
    *,
    round_id: int,
    sampled_entities: list[str],
    source_plan: list[SourcePlanItem],
    batch_payload: dict[str, Any],
    batch_result_raw: dict[str, Any],
    mode: str,
    disabled_actions: set[str] | None = None,
    mock_current_observations: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    source_quality_matrix = merge_source_quality(source_plan, batch_result_raw)
    source_completion = build_source_completion(source_quality_matrix)
    source_observations = build_source_observations(source_plan, source_quality_matrix, batch_result_raw)
    source_observations.extend(build_mock_current_source_observations(mock_current_observations))
    source_commonality_cards = build_batch_source_commonality_cards(
        source_quality_matrix,
        len(sampled_entities),
        source_observations,
        disabled_actions,
    )
    orchestration_artifacts = build_round_orchestration_artifacts(
        round_id=round_id,
        sampled_entities=sampled_entities,
        source_plan=source_plan,
        source_quality_matrix=source_quality_matrix,
        source_observations=source_observations,
        source_commonality_cards=source_commonality_cards,
        mode=mode,
        disabled_actions=disabled_actions,
    )
    candidate_coverage = _candidate_coverage_from_commonality_cards(source_commonality_cards)
    risk_like_count = len(candidate_coverage["multi_source_candidate_indices"])
    risk_coverage_ratio = round(risk_like_count / len(sampled_entities), 4) if sampled_entities else 0.0
    service_blocked = batch_result_raw.get("batch_status") == "harness_error"
    dry_run_only = mode == "dry_run"
    if service_blocked:
        decision = {
            "action": "blocked",
            "reason": "browser_backed_service_not_running_or_batch_harness_error",
            "required_authorization": False,
        }
    elif dry_run_only:
        decision = {
            "action": "continue",
            "reason": "dry_run_structure_only_no_platform_evidence",
            "required_authorization": False,
        }
    else:
        decision = {
            "action": "continue",
            "reason": "business_commonality_not_yet_closed_from_current_source_quality",
            "required_authorization": False,
        }

    return {
        "round_id": round_id,
        "sampled_count": len(sampled_entities),
        "sampled_entities": sampled_entities,
        "source_plan": [item.to_plan_dict() for item in source_plan],
        "batch_payload": batch_payload,
        "source_completion": source_completion,
        "source_quality": source_quality_matrix,
        "source_observation_summary": [
            {
                "source_id": observation.get("source_id"),
                "action": observation.get("action"),
                "quality_class": observation.get("quality_class"),
                "evidence_use": observation.get("evidence_use"),
                "extracted_business_fields": observation.get("extracted_business_fields", []),
                "candidate_device_count": len(observation.get("candidate_device_ids", [])),
                "breakpoint_type": observation.get("breakpoint_type"),
            }
            for observation in source_observations
        ],
        "entity_graph": build_round_entity_graph(round_id, sampled_entities, source_quality_matrix, source_observations),
        "orchestration_artifacts": orchestration_artifacts,
        "source_commonality_cards": source_commonality_cards,
        "discovered_clusters": [] if dry_run_only or service_blocked or risk_like_count == 0 else [
            {
                "cluster_id": "candidate_multi_source_signal_cluster",
                "sample_count": risk_like_count,
                "sample_ratio": risk_coverage_ratio,
                "risk_type": "content_diversion_or_black_market_small_account_candidate",
                "attack_chain_status": "hypothesis_chain",
                "confidence": "medium_partial_until_login_content_baseline_closes",
                "shared_signals": candidate_coverage["signal_names"],
            }
        ],
        "main_shared_signals": [] if dry_run_only or service_blocked else candidate_coverage["signal_names"],
        "coverage_in_round": {
            "risk_like_count": risk_like_count,
            "sampled_count": len(sampled_entities),
            "risk_coverage_ratio": risk_coverage_ratio,
            "coverage_basis": "multi_source_candidate_signal_not_disposition",
            "evaluation_status": (
                "not_evaluated_in_dry_run"
                if dry_run_only else
                "multi_source_candidate_partial"
                if risk_like_count else
                "blocked_or_partial"
            ),
            "support_by_entity_index": candidate_coverage["support_by_index"],
        },
        "possible_normal_mixed_entities": [],
        "missing_evidence": [
            {
                "reason": "business_commonality_not_available_in_dry_run" if dry_run_only else "source_blocked_or_partial",
                "is_low_risk_counter_evidence": False,
            }
        ],
        "decision": decision,
    }


def _batch_payload_for_executable_sources(case_id: str, source_plan: list[SourcePlanItem], dry_run: bool) -> tuple[dict[str, Any], list[SourcePlanItem], list[SourcePlanItem]]:
    executable, skipped = split_executable_and_skipped(source_plan)
    payload = build_batch_payload(case_id, executable, dry_run=dry_run)
    return payload, executable, skipped


def _chunked_batch_payloads_for_executable_sources(
    case_id: str,
    source_plan: list[SourcePlanItem],
    dry_run: bool,
    *,
    max_sources_per_batch: int = MAX_BROWSER_BACKED_BATCH_SOURCES,
) -> tuple[list[tuple[dict[str, Any], list[SourcePlanItem]]], list[SourcePlanItem], list[SourcePlanItem]]:
    executable, skipped = split_executable_and_skipped(source_plan)
    chunks: list[tuple[dict[str, Any], list[SourcePlanItem]]] = []
    ordered_batches: list[tuple[str, list[SourcePlanItem], int]] = []
    general_items = [
        item for item in executable
        if item.action not in SOURCE_ACTION_CHUNK_LIMITS
    ]
    if general_items:
        ordered_batches.append(("general", general_items, max_sources_per_batch))
    for action, action_limit in SOURCE_ACTION_CHUNK_LIMITS.items():
        action_items = [item for item in executable if item.action == action]
        if action_items:
            ordered_batches.append((action, action_items, action_limit))

    chunk_id = 1
    for action, items, chunk_limit in ordered_batches:
        for index in range(0, len(items), chunk_limit):
            chunk_items = items[index:index + chunk_limit]
            payload = build_batch_payload(
                f"{case_id}:chunk_{chunk_id}:{action}",
                chunk_items,
                dry_run=dry_run,
            )
            chunks.append((payload, chunk_items))
            chunk_id += 1
    return chunks, executable, skipped


def _summarize_chunked_batch_payloads(payloads: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "endpoint": "/actions/batch",
        "chunk_count": len(payloads),
        "max_sources_per_chunk": MAX_BROWSER_BACKED_BATCH_SOURCES,
        "manual_curl_fallback_allowed": False,
        "chunks": [
            {
                "request_id": payload.get("request_id"),
                "dry_run": payload.get("dry_run"),
                "source_count": sum(
                    len(group.get("sources", []))
                    for group in payload.get("execution_groups", [])
                    if isinstance(group, dict)
                ),
                "execution_groups": [
                    {
                        "group_id": group.get("group_id"),
                        "execution": group.get("execution"),
                        "source_count": len(group.get("sources", [])),
                    }
                    for group in payload.get("execution_groups", [])
                    if isinstance(group, dict)
                ],
            }
            for payload in payloads
        ],
    }


def _validate_chunked_batch_payloads(payloads: list[dict[str, Any]]) -> dict[str, Any]:
    validations = []
    errors: list[str] = []
    for index, payload in enumerate(payloads, start=1):
        validation = validate_batch_payload_contract(payload)
        source_count = sum(
            len(group.get("sources", []))
            for group in payload.get("execution_groups", [])
            if isinstance(group, dict)
        )
        chunk_errors = list(validation.get("errors") or [])
        if source_count > MAX_BROWSER_BACKED_BATCH_SOURCES:
            chunk_errors.append(f"chunk_{index}_exceeds_service_source_limit:{source_count}")
        validations.append({
            "chunk_id": index,
            "source_count": source_count,
            "valid": validation.get("valid") and not chunk_errors,
            "errors": chunk_errors,
        })
        errors.extend(chunk_errors)
    return {
        "valid": not errors,
        "errors": errors,
        "contract": "browser_backed_actions_batch_v1",
        "endpoint": "/actions/batch",
        "chunk_count": len(payloads),
        "max_sources_per_chunk": MAX_BROWSER_BACKED_BATCH_SOURCES,
        "manual_curl_fallback_allowed": False,
        "chunks": validations,
    }


def _round_entity_prefix(round_id: int, index: int) -> str:
    return f"round_{round_id}_entity_{index}_"


def _candidate_devices_by_round_entity(
    round_id: int,
    sampled_entities: list[str],
    source_observations: list[dict[str, Any]],
) -> dict[int, list[dict[str, Any]]]:
    input_entities = set(sampled_entities)
    by_index: dict[int, list[dict[str, Any]]] = {index: [] for index in range(1, len(sampled_entities) + 1)}
    seen: set[tuple[int, str]] = set()
    for observation in source_observations:
        source_id = str(observation.get("source_id") or "")
        entity_index = None
        for index in by_index:
            if source_id.startswith(_round_entity_prefix(round_id, index)):
                entity_index = index
                break
        if entity_index is None:
            continue
        for candidate in observation.get("candidate_device_ids", []):
            if not isinstance(candidate, dict):
                continue
            device_id = str(candidate.get("device_id") or "").strip()
            if not device_id or device_id in input_entities:
                continue
            key = (entity_index, device_id)
            if key in seen:
                continue
            seen.add(key)
            candidate_copy = dict(candidate)
            candidate_copy.setdefault("source_id", source_id)
            candidate_copy.setdefault("action", observation.get("action"))
            by_index[entity_index].append(candidate_copy)
    return by_index


def build_track_followup_source_plan(
    round_id: int,
    sampled_entities: list[str],
    source_observations: list[dict[str, Any]],
    *,
    window_start_ms: int,
    window_end_ms: int,
) -> list[SourcePlanItem]:
    track_start_ms, track_end_ms = _bounded_source_window(
        window_start_ms,
        window_end_ms,
        TRACK_READINESS_WINDOW_DAYS,
    )
    by_entity = _candidate_devices_by_round_entity(round_id, sampled_entities, source_observations)
    items: list[SourcePlanItem] = []
    for index, candidates in by_entity.items():
        if not candidates:
            continue
        candidate = sorted(candidates, key=lambda item: str(item.get("source_id") or ""))[0]
        device_id = str(candidate.get("device_id") or "").strip()
        if not device_id:
            continue
        items.append(
            SourcePlanItem(
                source_id=_batch_source_id(round_id, index, "track_followup"),
                action="track_analysis_check_data_ready",
                execution_group="dependency_serial",
                depends_on=[str(candidate.get("source_id") or _batch_source_id(round_id, index, "weapon"))],
                timeout_class="short_readiness",
                failure_policy="non_blocking_partial",
                source_priority="P1-auto-next-hop",
                expected_observation="frontend behavior readiness after Dennis-side candidate device resolution",
                params={
                    "device_id": device_id,
                    "startTime": track_start_ms,
                    "endTime": track_end_ms,
                    "appName": "KUAISHOU",
                    "product": "KUAISHOU",
                    "mode": "track_analysis_data_readiness_precheck",
                    "include": 1,
                    "pageSize": 100,
                    "category": ["active"],
                    "event": [],
                    "appPlatform": [],
                    "metric": "pv",
                    "type": "deviceId",
                },
                timeout_ms=15_000,
                required_fields=["device_id", "startTime", "endTime"],
                window_policy="auto_next_hop_after_candidate_device_resolution",
                window_start_ms=track_start_ms,
                window_end_ms=track_end_ms,
            )
        )
    return items


def _photo_ids_by_round_entity(
    round_id: int,
    sampled_entities: list[str],
    source_observations: list[dict[str, Any]],
) -> dict[int, list[dict[str, Any]]]:
    by_index: dict[int, list[dict[str, Any]]] = {index: [] for index in range(1, len(sampled_entities) + 1)}
    seen: set[tuple[int, str]] = set()
    for observation in source_observations:
        source_id = str(observation.get("source_id") or "")
        entity_index = None
        for index in by_index:
            if source_id.startswith(_round_entity_prefix(round_id, index)):
                entity_index = index
                break
        if entity_index is None:
            continue
        if str(observation.get("action") or "") not in {
            "archives_photo_search",
            "archives_gallery_photo_list",
            "archives_photo_profile",
            "archives_photo_meta",
        }:
            continue
        for handle in observation.get("parsed_body_field_handles", []) or []:
            canonical = str(handle.get("canonical_field") or handle.get("field") or "")
            if canonical != "photo_id":
                continue
            photo_id = str(handle.get("value") or "").strip()
            if not photo_id:
                continue
            key = (entity_index, photo_id)
            if key in seen:
                continue
            seen.add(key)
            by_index[entity_index].append(
                {
                    "photo_id": photo_id,
                    "source_id": source_id,
                    "field_path": handle.get("field_path"),
                    "action": observation.get("action"),
                }
            )
    return by_index


def build_gallery_followup_source_plan(
    round_id: int,
    sampled_entities: list[str],
    source_observations: list[dict[str, Any]],
    *,
    window_start_ms: int,
    window_end_ms: int,
    disabled_actions: set[str] | None = None,
) -> list[SourcePlanItem]:
    if "archives_gallery_photo_list" in (disabled_actions or set()):
        return []
    photo_ids_by_entity = _photo_ids_by_round_entity(round_id, sampled_entities, source_observations)
    items: list[SourcePlanItem] = []
    for index, entity in enumerate(sampled_entities, start=1):
        if photo_ids_by_entity.get(index):
            continue
        items.append(
            SourcePlanItem(
                source_id=_batch_source_id(round_id, index, "gallery"),
                action="archives_gallery_photo_list",
                execution_group="dependency_serial",
                depends_on=[_batch_source_id(round_id, index, "photo")],
                timeout_class="auth_sensitive",
                failure_policy="non_blocking_partial",
                source_priority="P1-auto-next-hop",
                expected_observation="recent gallery photo_id and publish_time candidates when photo_search did not expose anchors",
                params={
                    "user_id": entity,
                    "pageIndex": 1,
                    "pageSize": 10,
                },
                timeout_ms=30_000,
                required_fields=["user_id"],
                window_policy="content_anchor_discovery_not_constrained_by_login_logs",
                window_start_ms=window_start_ms,
                window_end_ms=window_end_ms,
            )
        )
    return items


def build_photo_detail_followup_source_plan(
    round_id: int,
    sampled_entities: list[str],
    source_observations: list[dict[str, Any]],
    *,
    window_start_ms: int,
    window_end_ms: int,
    disabled_actions: set[str] | None = None,
) -> list[SourcePlanItem]:
    disabled_actions = disabled_actions or set()
    if {"archives_photo_profile", "archives_photo_meta"} <= disabled_actions:
        return []
    photo_ids_by_entity = _photo_ids_by_round_entity(round_id, sampled_entities, source_observations)
    items: list[SourcePlanItem] = []
    for index, candidates in photo_ids_by_entity.items():
        if not candidates:
            continue
        candidate = candidates[0]
        photo_id = str(candidate.get("photo_id") or "").strip()
        if not photo_id:
            continue
        depends_on = [str(candidate.get("source_id") or _batch_source_id(round_id, index, "photo"))]
        if "archives_photo_profile" not in disabled_actions:
            items.append(
                SourcePlanItem(
                    source_id=_batch_source_id(round_id, index, f"photo_profile_{photo_id}"),
                    action="archives_photo_profile",
                    execution_group="dependency_serial",
                    depends_on=depends_on,
                    timeout_class="auth_sensitive",
                    failure_policy="non_blocking_partial",
                    source_priority="P1-auto-next-hop",
                    expected_observation="photo profile publish source/device/IP/status fields for content chain backfill",
                    params={"photo_id": photo_id},
                    timeout_ms=30_000,
                    required_fields=["photo_id"],
                    window_policy="photo_detail_for_content_chain_backfill",
                    window_start_ms=window_start_ms,
                    window_end_ms=window_end_ms,
                )
            )
        if "archives_photo_meta" not in disabled_actions:
            items.append(
                SourcePlanItem(
                    source_id=_batch_source_id(round_id, index, f"photo_meta_{photo_id}"),
                    action="archives_photo_meta",
                    execution_group="dependency_serial",
                    depends_on=depends_on,
                    timeout_class="auth_sensitive",
                    failure_policy="non_blocking_partial",
                    source_priority="P1-auto-next-hop",
                    expected_observation="photo meta uploadSource/photoMethod/photoIp/publishDevice fields for device consistency",
                    params={"photo_id": photo_id},
                    timeout_ms=30_000,
                    required_fields=["photo_id"],
                    window_policy="photo_meta_for_publish_device_backfill",
                    window_start_ms=window_start_ms,
                    window_end_ms=window_end_ms,
                )
            )
    return items


def execute_sample_round(
    *,
    case_id: str,
    round_item: dict[str, Any],
    args: argparse.Namespace,
    window_start_ms: int,
    window_end_ms: int,
    disabled_actions: set[str],
) -> dict[str, Any]:
    round_id = int(round_item.get("round_id"))
    sampled_entities = [str(entity) for entity in round_item.get("sampled_entities", [])]
    source_plan = build_sample_round_source_plan(
        round_id,
        sampled_entities,
        window_start_ms=window_start_ms,
        window_end_ms=window_end_ms,
        disabled_actions=disabled_actions,
    )
    chunked_payloads, executable, skipped = _chunked_batch_payloads_for_executable_sources(
        f"{case_id}:round_{round_id}",
        source_plan,
        dry_run=args.mode == "dry_run",
    )
    payloads = [payload for payload, _items in chunked_payloads]
    batch_payload = _summarize_chunked_batch_payloads(payloads)
    contract_validation = _validate_chunked_batch_payloads(payloads)
    if args.mode == "dry_run":
        primary_results = [
            build_dry_run_batch_result(chunk_items)
            for _payload, chunk_items in chunked_payloads
        ]
    else:
        if not args.browser_backed_base:
            primary_results = [build_harness_error_result(
                source_status="service_unavailable",
                error_type="browser_backed_base_required",
                detail={"reason": "--browser-backed-base is required in live mode"},
            )]
        else:
            primary_results = [
                call_browser_backed_batch(args.browser_backed_base, payload)
                for payload in payloads
            ]
    preliminary_result = merge_batch_results(primary_results)
    preliminary_quality = merge_source_quality(source_plan, preliminary_result)
    preliminary_observations = build_source_observations(source_plan, preliminary_quality, preliminary_result)
    skipped_result = build_dry_run_batch_result(skipped) if skipped else {
        "ok": True,
        "batch_status": "empty",
        "transport_status_matrix": {},
        "source_results": {},
        "missing_or_failed_sources": [],
    }
    next_hop_allowed = preliminary_result.get("batch_status") != "harness_error"

    gallery_source_plan: list[SourcePlanItem] = []
    gallery_results: list[dict[str, Any]] = []
    gallery_payloads: list[dict[str, Any]] = []
    if next_hop_allowed:
        gallery_source_plan = build_gallery_followup_source_plan(
            round_id,
            sampled_entities,
            preliminary_observations,
            window_start_ms=window_start_ms,
            window_end_ms=window_end_ms,
            disabled_actions=disabled_actions,
        )
    if gallery_source_plan:
        gallery_chunks, _gallery_executable, _gallery_skipped = _chunked_batch_payloads_for_executable_sources(
            f"{case_id}:round_{round_id}:gallery_followup",
            gallery_source_plan,
            dry_run=args.mode == "dry_run",
        )
        gallery_payloads = [payload for payload, _items in gallery_chunks]
        if args.mode == "dry_run":
            gallery_results = [
                build_dry_run_batch_result(chunk_items)
                for _payload, chunk_items in gallery_chunks
            ]
        elif args.browser_backed_base:
            gallery_results = [
                call_browser_backed_batch(args.browser_backed_base, payload)
                for payload in gallery_payloads
            ]

    after_gallery_plan = [*source_plan, *gallery_source_plan]
    after_gallery_result = merge_batch_results([*primary_results, *gallery_results, skipped_result])
    after_gallery_quality = merge_source_quality(after_gallery_plan, after_gallery_result)
    after_gallery_observations = build_source_observations(after_gallery_plan, after_gallery_quality, after_gallery_result)

    photo_detail_source_plan: list[SourcePlanItem] = []
    photo_detail_results: list[dict[str, Any]] = []
    photo_detail_payloads: list[dict[str, Any]] = []
    if next_hop_allowed:
        photo_detail_source_plan = build_photo_detail_followup_source_plan(
            round_id,
            sampled_entities,
            after_gallery_observations,
            window_start_ms=window_start_ms,
            window_end_ms=window_end_ms,
            disabled_actions=disabled_actions,
        )
    if photo_detail_source_plan:
        photo_detail_chunks, _photo_detail_executable, _photo_detail_skipped = _chunked_batch_payloads_for_executable_sources(
            f"{case_id}:round_{round_id}:photo_detail_followup",
            photo_detail_source_plan,
            dry_run=args.mode == "dry_run",
        )
        photo_detail_payloads = [payload for payload, _items in photo_detail_chunks]
        if args.mode == "dry_run":
            photo_detail_results = [
                build_dry_run_batch_result(chunk_items)
                for _payload, chunk_items in photo_detail_chunks
            ]
        elif args.browser_backed_base:
            photo_detail_results = [
                call_browser_backed_batch(args.browser_backed_base, payload)
                for payload in photo_detail_payloads
            ]

    before_track_plan = [*source_plan, *gallery_source_plan, *photo_detail_source_plan]
    before_track_result = merge_batch_results([*primary_results, *gallery_results, *photo_detail_results, skipped_result])
    before_track_quality = merge_source_quality(before_track_plan, before_track_result)
    before_track_observations = build_source_observations(before_track_plan, before_track_quality, before_track_result)
    followup_source_plan: list[SourcePlanItem] = []
    followup_results: list[dict[str, Any]] = []
    followup_payloads: list[dict[str, Any]] = []
    if next_hop_allowed and "track_analysis_check_data_ready" not in disabled_actions:
        followup_source_plan = build_track_followup_source_plan(
            round_id,
            sampled_entities,
            before_track_observations,
            window_start_ms=window_start_ms,
            window_end_ms=window_end_ms,
        )
    if followup_source_plan:
        followup_chunks, _followup_executable, _followup_skipped = _chunked_batch_payloads_for_executable_sources(
            f"{case_id}:round_{round_id}:track_followup",
            followup_source_plan,
            dry_run=args.mode == "dry_run",
        )
        followup_payloads = [payload for payload, _items in followup_chunks]
        if args.mode == "dry_run":
            followup_results = [
                build_dry_run_batch_result(chunk_items)
                for _payload, chunk_items in followup_chunks
            ]
        elif args.browser_backed_base:
            followup_results = [
                call_browser_backed_batch(args.browser_backed_base, payload)
                for payload in followup_payloads
            ]

    combined_source_plan = [*source_plan, *gallery_source_plan, *photo_detail_source_plan, *followup_source_plan]
    batch_result_raw = merge_batch_results([*primary_results, *gallery_results, *photo_detail_results, *followup_results, skipped_result])
    round_result = build_round_result(
        round_id=round_id,
        sampled_entities=sampled_entities,
        source_plan=combined_source_plan,
        batch_payload=batch_payload,
        batch_result_raw=batch_result_raw,
        mode=args.mode,
        disabled_actions=disabled_actions,
        mock_current_observations=round_item.get("mock_current_observations")
        if isinstance(round_item.get("mock_current_observations"), list)
        else None,
    )
    round_result["batch_contract_validation"] = contract_validation
    round_result["executable_source_count"] = len(executable)
    round_result["skipped_source_count"] = len(skipped)
    round_result["auto_next_hop"] = {
        "gallery_followup_source_count": len(gallery_source_plan),
        "gallery_followup_executed": bool(gallery_results),
        "gallery_followup_batch_payload": _summarize_chunked_batch_payloads(gallery_payloads) if gallery_payloads else None,
        "photo_detail_followup_source_count": len(photo_detail_source_plan),
        "photo_detail_followup_executed": bool(photo_detail_results),
        "photo_detail_followup_batch_payload": _summarize_chunked_batch_payloads(photo_detail_payloads) if photo_detail_payloads else None,
        "track_followup_source_count": len(followup_source_plan),
        "track_followup_executed": bool(followup_results),
        "track_followup_batch_payload": _summarize_chunked_batch_payloads(followup_payloads) if followup_payloads else None,
    }
    if disabled_actions:
        round_result["disabled_actions"] = sorted(disabled_actions)
    round_result["batch_status"] = batch_result_raw.get("batch_status")
    round_result["batch_result"] = build_safe_batch_summary(batch_result_raw, round_result.get("source_quality"))
    return round_result


def build_cumulative_sample_result(
    *,
    rounds_payload: dict[str, Any],
    validation: dict[str, Any],
    round_results: list[dict[str, Any]],
    args: argparse.Namespace,
) -> dict[str, Any]:
    checked_count = sum(int(item.get("sampled_count") or 0) for item in round_results)
    total_input_count = int(rounds_payload.get("total_input_count") or checked_count)
    blocked_rounds = [item for item in round_results if item.get("decision", {}).get("action") == "blocked"]
    dry_run_only = args.mode == "dry_run"
    risk_like_count = sum(
        int((item.get("coverage_in_round") or {}).get("risk_like_count") or 0)
        for item in round_results
    )
    stable_high_rounds = sum(
        1 for item in round_results
        if float((item.get("coverage_in_round") or {}).get("risk_coverage_ratio") or 0.0) >= 0.7
    )
    main_cluster_ratio = round(risk_like_count / checked_count, 4) if checked_count else 0.0
    risk_cluster_ratio = main_cluster_ratio
    if blocked_rounds:
        next_action = "start_browser_backed_service_then_rerun_harness"
        next_auth = False
        decision_reason = "source execution blocked before business commonality could be evaluated"
    elif dry_run_only:
        next_action = "run_live_readonly_when_browser_backed_service_ready"
        next_auth = False
        decision_reason = "dry_run verified harness shape only"
    elif risk_cluster_ratio >= 0.7 and stable_high_rounds >= 2:
        next_action = "offline_validate"
        next_auth = True
        decision_reason = "multi-source candidate coverage reached validation threshold; not an auto-disposition threshold"
    elif 0.4 <= risk_cluster_ratio < 0.7:
        next_action = "continue_round_4_or_5"
        next_auth = False
        decision_reason = "coverage in 40-70 range"
    else:
        next_action = "continue_or_refine_source_plan"
        next_auth = False
        decision_reason = "risk coverage below threshold or source evidence incomplete"

    return {
        "route_mode": "sample_expand_validate_mode",
        "checked_count": checked_count,
        "total_input_count": total_input_count,
        "planned_rounds_this_run": validation["planned_rounds_this_run"],
        "max_rounds": validation["max_rounds"],
        "cluster_coverage": {
            "main_risk_cluster_ratio": main_cluster_ratio,
            "secondary_risk_cluster_ratio": 0.0,
            "combined_risk_cluster_ratio": risk_cluster_ratio,
            "normal_or_counter_ratio": 0.0,
            "insufficient_or_blocked_ratio": 1.0 if dry_run_only or blocked_rounds else 0.0,
            "coverage_status": "not_evaluated_in_dry_run" if dry_run_only else (
                "multi_source_candidate_high_coverage_requires_offline_validation"
                if risk_cluster_ratio >= 0.7 and stable_high_rounds >= 2 else
                "blocked_or_partial"
            ),
            "coverage_basis": "multi_source_candidate_signal_not_disposition",
            "stable_high_rounds": stable_high_rounds,
        },
        "main_cluster": (
            {
                "cluster_id": "candidate_multi_source_signal_cluster",
                "sample_count": risk_like_count,
                "sample_ratio": main_cluster_ratio,
                "risk_type": "content_diversion_or_black_market_small_account_candidate",
                "confidence": "medium_partial_until_login_content_baseline_closes",
            }
            if risk_like_count else None
        ),
        "secondary_clusters": [],
        "normal_or_counter": [],
        "cumulative_coverage": {
            "checked_count": checked_count,
            "coverage_basis": "multi_source_candidate_signal_not_disposition",
            "threshold_70_percent_is_validation_not_disposition": True,
        },
        "multi_source_fusion": {
            "strong_shared_signals": [],
            "medium_shared_signals": [
                "strategy_hit_discovery_and_device_graph_candidate_overlap"
            ] if risk_like_count else [],
            "weak_signals": [],
            "conflicting_signals": [],
            "counter_evidence": [],
            "possible_normal_mixed_entities": [],
            "risk_clusters": [
                {
                    "cluster_id": "candidate_multi_source_signal_cluster",
                    "sample_count": risk_like_count,
                    "sample_ratio": main_cluster_ratio,
                    "evidence_boundary": "sampled multi-source candidate only; full 100 coverage requires authorized offline/wide-table validation",
                }
            ] if risk_like_count else [],
            "conclusion_boundary": [
                "sample_candidate_coverage_is_not_auto_disposition",
                "strategy_hit_not_final_judgement",
                "no_data_not_risk_exclusion",
                "login_log_and_content_baseline_still_required_for_final_chain",
            ],
        },
        "attack_chain": {
            "chain_status": "no_chain" if dry_run_only or blocked_rounds else "hypothesis_chain",
            "entry_point": None,
            "infrastructure": None,
            "account_control": None,
            "behavior_execution": None,
            "monetization_or_goal": "content_diversion_or_black_market_small_account_hypothesis",
            "platform_response": None,
            "missing_links": [
                "entity_graph_business_edges",
                "content_anchor_commonality",
                "strategy_hit_commonality",
                "frontend_behavior_commonality",
            ],
            "confidence": "not_evaluated_in_dry_run" if dry_run_only else "medium_partial" if risk_like_count else "low_until_sources_complete",
            "evidence_support": [
                "strategy_hit_discovery",
                "weapon_user_device_graph",
                "track_followup_when_candidate_device_available",
            ] if risk_like_count else [],
        },
        "strategy_recommendations": build_batch_strategy_recommendations(
            "not_evaluated_in_dry_run" if dry_run_only else "pending_full_validation"
        ),
        "next_action": next_action,
        "next_action_required_authorization": next_auth,
        "decision_reason": decision_reason,
        "conclusion_boundary": [
            "not_auto_disposition",
            "not_auto_strategy_launch",
            "DataAgent_Hive_not_called",
            "offline_validate_requires_user_authorization",
            "representative_samples_do_not_prove_full_100_coverage",
        ],
    }


def _rolling_anchor_key(anchor: dict[str, Any]) -> str:
    anchor_type = str(anchor.get("anchor_type") or "unknown_anchor")
    ref = str(anchor.get("value") or anchor.get("safe_ref") or "").strip()
    if not ref:
        ref = str(anchor.get("batch_anchor_key") or anchor_type)
    return f"{anchor_type}:{ref}"


def _rolling_anchor_public_summary(
    key: str,
    entry: dict[str, Any],
    *,
    current_status: str,
) -> dict[str, Any]:
    round_support = entry.get("round_support", {})
    support_ratios = [
        item.get("support_ratio")
        for item in round_support.values()
        if isinstance(item, dict) and item.get("support_ratio") is not None
    ]
    support_ratio = round(max(support_ratios), 4) if support_ratios else None
    return {
        "anchor_key": key,
        "anchor_type": entry.get("anchor_type"),
        "anchor_value_or_safe_ref": entry.get("anchor_value_or_safe_ref"),
        "observation_domain": entry.get("observation_domain"),
        "batch_anchor_scope": entry.get("batch_anchor_scope"),
        "cumulative_support_count": entry.get("cumulative_support_count", 0),
        "support_rounds": sorted(entry.get("support_rounds", [])),
        "support_ratio": support_ratio,
        "current_status": current_status,
    }


def build_rolling_anchor_summary(
    *,
    round_results: list[dict[str, Any]],
    round_artifacts: list[dict[str, Any]],
) -> dict[str, Any]:
    round_count = len(round_artifacts)
    anchor_entries: dict[str, dict[str, Any]] = {}
    keys_by_round: dict[int, set[str]] = {}
    for round_index, artifact in enumerate(round_artifacts, start=1):
        sampled_count = len(round_results[round_index - 1].get("sampled_entities", []) or []) if round_index <= len(round_results) else 0
        keys_by_round[round_index] = set()
        for anchor in artifact.get("batch_anchor_pool", []) or []:
            if not isinstance(anchor, dict):
                continue
            key = _rolling_anchor_key(anchor)
            supporting_entities = unique_strings([
                str(entity)
                for entity in anchor.get("supporting_entities", []) or []
                if str(entity)
            ])
            support_count = len(supporting_entities)
            support_ratio = round(support_count / sampled_count, 4) if sampled_count else None
            entry = anchor_entries.setdefault(
                key,
                {
                    "anchor_type": anchor.get("anchor_type"),
                    "anchor_value_or_safe_ref": anchor.get("value") or anchor.get("safe_ref"),
                    "observation_domain": anchor.get("observation_domain"),
                    "batch_anchor_scope": anchor.get("batch_anchor_scope"),
                    "cumulative_support_count": 0,
                    "support_rounds": [],
                    "round_support": {},
                },
            )
            entry["cumulative_support_count"] = int(entry.get("cumulative_support_count") or 0) + support_count
            if round_index not in entry["support_rounds"]:
                entry["support_rounds"].append(round_index)
            entry["round_support"][round_index] = {
                "support_entities": supporting_entities,
                "support_count": support_count,
                "support_ratio": support_ratio,
            }
            keys_by_round[round_index].add(key)

    if round_count <= 1:
        anchor_summaries = [
            _rolling_anchor_public_summary(key, entry, current_status="insufficient_rounds")
            for key, entry in sorted(anchor_entries.items())
        ]
        return {
            "round_count": round_count,
            "current_status": "insufficient_rounds",
            "stable_anchors": [],
            "dropped_anchors": [],
            "new_anchor_delta": anchor_summaries,
            "support_ratio": {item["anchor_key"]: item.get("support_ratio") for item in anchor_summaries},
            "support_rounds": {item["anchor_key"]: item.get("support_rounds", []) for item in anchor_summaries},
            "anchor_summaries": anchor_summaries,
            "boundary": "single_round_mode_1_or_single_round_sample_cannot_claim_cross_round_stability",
        }

    last_round = round_count
    previous_round = round_count - 1
    last_keys = keys_by_round.get(last_round, set())
    previous_keys = keys_by_round.get(previous_round, set())
    stable_keys = {
        key for key, entry in anchor_entries.items()
        if len(set(entry.get("support_rounds", []))) >= 2 and key in last_keys
    }
    dropped_keys = previous_keys - last_keys
    new_keys = last_keys - previous_keys
    stable_anchors = [
        _rolling_anchor_public_summary(key, anchor_entries[key], current_status="stable")
        for key in sorted(stable_keys)
    ]
    dropped_anchors = [
        _rolling_anchor_public_summary(key, anchor_entries[key], current_status="dropped")
        for key in sorted(dropped_keys)
        if key in anchor_entries
    ]
    new_anchor_delta = [
        _rolling_anchor_public_summary(key, anchor_entries[key], current_status="emerging")
        for key in sorted(new_keys)
        if key in anchor_entries
    ]
    anchor_summaries: list[dict[str, Any]] = []
    for key, entry in sorted(anchor_entries.items()):
        if key in stable_keys:
            status = "stable"
        elif key in dropped_keys:
            status = "dropped"
        elif key in new_keys:
            status = "emerging"
        else:
            status = "weakening" if key not in last_keys else "stable"
        anchor_summaries.append(_rolling_anchor_public_summary(key, entry, current_status=status))
    if stable_anchors:
        current_status = "stable"
    elif new_anchor_delta and not dropped_anchors:
        current_status = "emerging"
    elif dropped_anchors and not new_anchor_delta:
        current_status = "weakening"
    else:
        current_status = "weakening" if dropped_anchors else "emerging"
    return {
        "round_count": round_count,
        "current_status": current_status,
        "stable_anchors": stable_anchors,
        "dropped_anchors": dropped_anchors,
        "new_anchor_delta": new_anchor_delta,
        "support_ratio": {item["anchor_key"]: item.get("support_ratio") for item in anchor_summaries},
        "support_rounds": {item["anchor_key"]: item.get("support_rounds", []) for item in anchor_summaries},
        "anchor_summaries": anchor_summaries,
        "boundary": "rolling_anchor_summary_is_evidence_for_batch_stability_only_not_disposition",
    }


def build_cumulative_orchestration_artifacts(
    *,
    round_results: list[dict[str, Any]],
    cumulative_result: dict[str, Any],
) -> dict[str, Any]:
    round_artifacts = [
        item.get("orchestration_artifacts", {})
        for item in round_results
        if isinstance(item.get("orchestration_artifacts"), dict)
    ]
    candidate_anchor_counts = [
        len(artifact.get("candidate_anchor_pool", []) or [])
        for artifact in round_artifacts
    ]
    batch_anchor_counts = [
        len(artifact.get("batch_anchor_pool", []) or [])
        for artifact in round_artifacts
    ]
    selected_anchor_counts = [
        len(artifact.get("selected_drilldown_anchors", []) or [])
        for artifact in round_artifacts
    ]
    skipped_anchor_counts = [
        len(artifact.get("skipped_anchors", []) or [])
        for artifact in round_artifacts
    ]
    stop_reasons = unique_strings([
        str(reason)
        for artifact in round_artifacts
        for reason in artifact.get("stop_reason", []) or []
    ])
    candidate_features = [
        feature
        for artifact in round_artifacts
        for feature in artifact.get("candidate_features", []) or []
        if isinstance(feature, dict)
    ]
    group_candidates = [
        artifact.get("group_profile_candidate")
        for artifact in round_artifacts
        if isinstance(artifact.get("group_profile_candidate"), dict)
    ]
    validation_plans = [
        artifact.get("validation_plan")
        for artifact in round_artifacts
        if isinstance(artifact.get("validation_plan"), dict)
    ]
    round_level_source_quality: dict[str, Any] = {
        "completed": [],
        "partial": [],
        "response_limited": [],
        "blocked": [],
        "timeout": [],
        "no_data": [],
        "auth_failed": [],
        "parse_error": [],
        "planned": [],
        "partial_reasons": [],
    }
    for round_result in round_results:
        quality_matrix = round_result.get("source_quality", {})
        if not isinstance(quality_matrix, dict):
            continue
        buckets = quality_matrix.get("buckets", {})
        if isinstance(buckets, dict):
            for key in ("completed", "partial", "blocked", "timeout", "no_data", "auth_failed", "parse_error", "planned"):
                for value in buckets.get(key, []) or []:
                    value_text = str(value)
                    if value_text and value_text not in round_level_source_quality[key]:
                        round_level_source_quality[key].append(value_text)
        for row in quality_matrix.get("per_source", []) or []:
            if not isinstance(row, dict):
                continue
            source_id = str(row.get("source_id") or "")
            if row.get("response_limited") is True and source_id and source_id not in round_level_source_quality["response_limited"]:
                round_level_source_quality["response_limited"].append(source_id)
            if row.get("quality_class") == "partial":
                reason = {
                    "source_id": source_id,
                    "action": row.get("action"),
                    "reason": row.get("reason") or row.get("source_status"),
                    "remaining_records_not_parsed": row.get("remaining_records_not_parsed"),
                    "cap_metadata_status": row.get("cap_metadata_status"),
                    "cap_metadata_reason": row.get("cap_metadata_reason"),
                }
                if reason not in round_level_source_quality["partial_reasons"]:
                    round_level_source_quality["partial_reasons"].append(reason)
    artifact_quality_summary: dict[str, Any] = {
        "skipped_missing_anchor": [],
        "skipped_by_cap": [],
        "skipped_by_domain_cap": [],
        "skipped_by_type_cap": [],
        "skipped_by_entity_diversity": [],
        "skipped_low_score": [],
        "low_value_anchor": [],
        "duplicate_anchor": [],
        "missing_contract": [],
        "not_executed": [],
        "candidate_features_not_final_conclusion": [],
        "validation_pending": [],
        "boundary": [
            "artifact_quality_is_not_source_completion",
            "skipped_or_missing_contract_is_missing_evidence_not_counter_evidence",
        ],
    }
    for artifact in round_artifacts:
        quality = artifact.get("source_quality", {})
        if not isinstance(quality, dict):
            continue
        for key in (
            "skipped_missing_anchor",
            "skipped_by_cap",
            "skipped_by_domain_cap",
            "skipped_by_type_cap",
            "skipped_by_entity_diversity",
            "skipped_low_score",
            "low_value_anchor",
            "duplicate_anchor",
            "missing_contract",
            "not_executed",
        ):
            for value in quality.get(key, []) or []:
                value_text = str(value)
                if value_text and value_text not in artifact_quality_summary[key]:
                    artifact_quality_summary[key].append(value_text)
    for feature in candidate_features:
        if feature.get("not_final_conclusion") is True:
            feature_name = str(feature.get("feature_name") or "candidate_feature")
            if feature_name not in artifact_quality_summary["candidate_features_not_final_conclusion"]:
                artifact_quality_summary["candidate_features_not_final_conclusion"].append(feature_name)
    for plan in validation_plans:
        status = str(plan.get("validation_status") or "")
        if status in {"planned", "pending", "not_executed"} and status not in artifact_quality_summary["validation_pending"]:
            artifact_quality_summary["validation_pending"].append(status)
    source_quality_summary = round_level_source_quality
    missing_evidence_summary: list[str] = []
    for artifact in round_artifacts:
        for item in artifact.get("missing_evidence", []) or []:
            if isinstance(item, dict):
                missing_evidence_summary.append(
                    str(item.get("source_id") or item.get("missing_evidence_type") or item.get("reason") or "missing_evidence")
                )
            elif isinstance(item, str):
                missing_evidence_summary.append(item)
    missing_evidence_summary = unique_strings(missing_evidence_summary)
    all_anchor_types = unique_strings([
        str(anchor.get("anchor_type"))
        for artifact in round_artifacts
        for anchor in artifact.get("batch_anchor_pool", []) or artifact.get("candidate_anchor_pool", []) or []
        if isinstance(anchor, dict) and anchor.get("anchor_type")
    ])
    all_anchor_domains = unique_strings([
        str(anchor.get("observation_domain"))
        for artifact in round_artifacts
        for anchor in artifact.get("batch_anchor_pool", []) or artifact.get("candidate_anchor_pool", []) or []
        if isinstance(anchor, dict) and anchor.get("observation_domain")
    ])
    batch_anchor_scope_counts: dict[str, int] = {}
    for artifact in round_artifacts:
        for anchor in artifact.get("batch_anchor_pool", []) or []:
            if not isinstance(anchor, dict):
                continue
            scope = str(anchor.get("batch_anchor_scope") or "unknown")
            batch_anchor_scope_counts[scope] = batch_anchor_scope_counts.get(scope, 0) + 1
    selected_anchor_types = unique_strings([
        str(anchor.get("anchor_type"))
        for artifact in round_artifacts
        for anchor in artifact.get("selected_drilldown_anchors", []) or []
        if isinstance(anchor, dict) and anchor.get("anchor_type")
    ])
    skipped_anchor_reasons = unique_strings([
        str(item.get("skip_reason"))
        for artifact in round_artifacts
        for item in artifact.get("skipped_anchors", []) or []
        if isinstance(item, dict) and item.get("skip_reason")
    ])
    base_domains = unique_strings([
        str(domain)
        for artifact in round_artifacts
        for domain in artifact.get("base_summary_card", {}).get("observation_domains", []) or []
    ])
    rolling_anchor_summary = build_rolling_anchor_summary(
        round_results=round_results,
        round_artifacts=round_artifacts,
    )
    cumulative_supporting_selected_batch_anchors = unique_strings([
        str(anchor)
        for candidate in group_candidates
        for anchor in candidate.get("supporting_selected_batch_anchors", []) or candidate.get("supporting_selected_anchors", []) or []
        if str(anchor)
    ])
    cumulative_context_selected_anchors = unique_strings([
        str(anchor)
        for candidate in group_candidates
        for anchor in candidate.get("context_selected_anchors", []) or []
        if str(anchor)
    ])
    return {
        "task_route": {
            "route_mode": "batch_interface_orchestration",
            "runtime_mode": "sample_expand_validate_mode",
            "round_count": len(round_results),
            "checked_count": cumulative_result.get("checked_count"),
            "no_70_action_cartesian_product": True,
        },
        "base_summary_card": {
            "round_count": len(round_results),
            "observation_domains": base_domains,
            "safe_summary_only": True,
        },
        "candidate_anchor_pool_count": sum(candidate_anchor_counts),
        "batch_anchor_pool_count": sum(batch_anchor_counts),
        "candidate_anchor_pool_summary": {
            "counts_by_round": candidate_anchor_counts,
            "batch_anchor_counts_by_round": batch_anchor_counts,
            "batch_anchor_scope_counts": batch_anchor_scope_counts,
            "commonality_mode_boundary": "batch_realtime_review_single_round_and_rolling_rounds_share_batch_anchor_pool_before_drilldown",
            "selected_counts_by_round": selected_anchor_counts,
            "skipped_counts_by_round": skipped_anchor_counts,
            "anchor_types": all_anchor_types,
            "selected_anchor_types": selected_anchor_types,
            "skipped_anchor_reasons": skipped_anchor_reasons,
            "observation_domains": all_anchor_domains,
            "safe_refs_only": True,
            "raw_values_not_expanded_at_top_level": True,
        },
        "anchor_scoring_summary": {
            "round_count": len(round_artifacts),
            "candidate_anchor_counts": candidate_anchor_counts,
            "batch_anchor_counts": batch_anchor_counts,
            "selected_anchor_counts": selected_anchor_counts,
            "skipped_anchor_counts": skipped_anchor_counts,
            "selection_policy": "batch_anchor_pool_first_then_top_k_selected_drilldown_anchors_with_domain_type_and_entity_diversity",
            "skipped_anchor_reasons": skipped_anchor_reasons,
            "selected_entity_distribution_by_round": [
                artifact.get("anchor_scoring_summary", {}).get("selected_entity_distribution", {})
                for artifact in round_artifacts
            ],
            "eligible_entity_count_by_round": [
                artifact.get("anchor_scoring_summary", {}).get("eligible_entity_count")
                for artifact in round_artifacts
            ],
            "selected_entity_count_by_round": [
                artifact.get("anchor_scoring_summary", {}).get("selected_entity_count")
                for artifact in round_artifacts
            ],
            "target_selected_entity_count_by_round": [
                artifact.get("anchor_scoring_summary", {}).get("target_selected_entity_count")
                for artifact in round_artifacts
            ],
            "entity_diversity_reason_by_round": [
                artifact.get("anchor_scoring_summary", {}).get("entity_diversity_reason")
                for artifact in round_artifacts
            ],
        },
        "rolling_anchor_summary": rolling_anchor_summary,
        "artifact_coverage": {
            "round_artifacts_count": len(round_artifacts),
            "candidate_anchor_pool_counts": candidate_anchor_counts,
            "selected_drilldown_anchor_counts": selected_anchor_counts,
            "skipped_anchor_counts": skipped_anchor_counts,
            "drilldown_stop_reasons": stop_reasons,
            "group_profile_candidate_count": len(group_candidates),
            "candidate_features_count": len(candidate_features),
            "validation_plan_count": len(validation_plans),
        },
        "source_quality": source_quality_summary,
        "round_level_source_quality": round_level_source_quality,
        "artifact_quality_summary": artifact_quality_summary,
        "missing_evidence": missing_evidence_summary,
        "group_profile_candidate": {
            "cluster_id": "cumulative_group_profile_candidate",
            "representative_entities": unique_strings([
                entity
                for item in round_results
                for entity in item.get("sampled_entities", [])[:2]
            ])[:10],
            "shared_domains": unique_strings([
                domain
                for candidate in group_candidates
                for domain in candidate.get("shared_domains", []) or []
            ]),
            "shared_signals": unique_strings([
                str(signal.get("signal_name") if isinstance(signal, dict) else signal)
                for candidate in group_candidates
                for signal in candidate.get("shared_signals", []) or []
            ]),
            "supporting_selected_anchors": cumulative_supporting_selected_batch_anchors,
            "supporting_selected_batch_anchors": cumulative_supporting_selected_batch_anchors,
            "context_selected_anchors": cumulative_context_selected_anchors,
            "supporting_anchor_boundary": (
                "supporting_selected_batch_anchors_can_support_cumulative_group_candidate; "
                "context_selected_anchors_are_not_group_support"
            ),
            "missing_evidence": [
                "cumulative_validation_not_executed",
                "representative_samples_do_not_prove_full_batch_coverage",
            ],
            "confidence": cumulative_result.get("cluster_coverage", {}).get("coverage_status", "not_evaluated"),
            "not_confirmed_as_group": True,
            "required_validation": [
                "offline_validate_or_wide_table_aggregate_report",
                "counter_sample_review",
            ],
        },
        "candidate_features": candidate_features[:10],
        "validation_plan": {
            "validation_goal": "validate sampled candidate coverage against full batch and counter samples",
            "required_data": ["full_input_batch", "control_group_or_counter_samples", "source_quality_by_round"],
            "dataagent_or_hive_required": True,
            "authorization_required": True,
            "expected_output": "wide_table_aggregate_report",
            "validation_status": "planned",
        },
        "final_evidence_card": {
            "conclusion_state": cumulative_result.get("conclusion_state", "sampled_partial"),
            "strong_evidence_count": 0,
            "medium_evidence_count": len([
                signal
                for candidate in group_candidates
                for signal in candidate.get("shared_signals", []) or []
            ]),
            "weak_evidence_count": 0,
            "counter_evidence_count": 0,
            "missing_evidence_count": len(missing_evidence_summary),
            "source_quality": source_quality_summary,
            "artifact_quality_summary": artifact_quality_summary,
            "boundary": [
                "top_level_artifacts_are_safe_summary_only",
                "round_level_artifacts_hold_detailed_safe_anchors",
                "top_level_source_quality_counts_real_source_completion_only",
                "artifact_quality_summary_holds_l2_and_validation_status",
                "not_final_conclusion",
            ],
        },
        "source_quality_boundary": [
            "not_final_conclusion",
            "not_confirmed_as_group",
            "no_data_skipped_timeout_missing_contract_not_low_risk_counter_evidence",
            "response_limited_partial_not_failed_final",
        ],
    }


def render_sample_expand_user_summary(cumulative_result: dict[str, Any], round_results: list[dict[str, Any]]) -> str:
    round_lines = []
    commonality_lines = []
    disabled_actions = sorted({
        action
        for item in round_results
        for action in item.get("disabled_actions", []) or []
    })
    for item in round_results:
        source_completion = item.get("source_completion", {})
        auto_next_hop = item.get("auto_next_hop", {}) or {}
        round_lines.append(
            "Round "
            f"{item['round_id']}: sampled={item['sampled_count']}, "
            f"decision={item['decision']['action']}, source_status={item.get('batch_status')}, "
            f"completed={len(source_completion.get('completed_sources', []))}, "
            f"partial={len(source_completion.get('partial_sources', []))}, "
            f"blocked={len(source_completion.get('blocked_sources', []))}, "
            f"timeout={len(source_completion.get('timeout_sources', []))}, "
            f"auth_failed={len(source_completion.get('auth_failed_sources', []))}, "
            f"gallery_next_hop={auto_next_hop.get('gallery_followup_source_count', 0)}, "
            f"photo_detail_next_hop={auto_next_hop.get('photo_detail_followup_source_count', 0)}, "
            f"track_next_hop={auto_next_hop.get('track_followup_source_count', 0)}"
        )
        signal_sources = [
            card.get("source_name")
            for card in item.get("source_commonality_cards", [])
            if card.get("shared_signals")
        ]
        if signal_sources:
            commonality_lines.append(
                f"Round {item['round_id']}: shared_signal_sources={','.join(signal_sources)}"
            )
        else:
            commonality_lines.append(
                f"Round {item['round_id']}: 未形成可用 shared_signals，仍是 source_quality / 字段缺口"
            )
    return "\n".join(
        [
            "一、当前模式与三轮抽样计划",
            f"sample_expand_validate_mode；checked_count={cumulative_result['checked_count']} / total_input_count={cumulative_result['total_input_count']}。",
            f"本轮显式禁用 source={','.join(disabled_actions) if disabled_actions else 'none'}；禁用 source 不计入失败或低风险反证。",
            "二、每轮 source 完成情况",
            *round_lines,
            "三、每轮共性与风险簇",
            *commonality_lines,
            "四、累计覆盖率与稳定性判断",
            json.dumps(cumulative_result["cluster_coverage"], ensure_ascii=False),
            "五、多源融合结论",
            "已基于可解析业务锚点计算多源候选覆盖；高覆盖只代表进入全量/离线验证的依据，不是自动处置结论。",
            "六、攻击链路还原",
            f"chain_status={cumulative_result['attack_chain']['chain_status']}；missing_links={','.join(cumulative_result['attack_chain']['missing_links'])}",
            "七、策略建议优先级",
            "包含 P0/P1/P2 + action_group；P0 仅表示可进入受控灰度验证，不是自动处置。",
            "八、是否进入全量 100 个离线/宽表验证",
            f"next_action={cumulative_result['next_action']}；required_authorization={cumulative_result['next_action_required_authorization']}",
            "九、缺失证据与 source_quality",
            "no_data / blocked / timeout / auth_failed / response_limited 均进入 source_quality，不作为无风险反证；response_limited 是 partial，不是 failed final。",
            "十、结论边界",
            "本 harness 不调用 DataAgent/Hive、不自动处置、不自动上线策略；代表样本不等于全量覆盖。live 输出默认只展示 envelope/counts/cap metadata/safe anchor summary，不展开 raw upstream body。",
        ]
    )


def build_sample_expand_validate_batch_result(args: argparse.Namespace) -> dict[str, Any]:
    if args.window_start_ms is None or args.window_end_ms is None:
        window_start_ms, window_end_ms = _default_scene_window()
    else:
        window_start_ms, window_end_ms = args.window_start_ms, args.window_end_ms
    if window_start_ms >= window_end_ms:
        raise ValueError("window_start_ms must be earlier than window_end_ms")

    rounds_payload = load_rounds_payload(args.rounds_json)
    validation = validate_sample_expand_rounds_payload(
        rounds_payload,
        max_rounds_arg=args.max_rounds,
        max_deep_checked_arg=args.max_deep_checked,
    )
    if not validation["valid"]:
        return {
            "schema_version": "runtime_case_execution_result_v1",
            "task": args.task,
            "mode": args.mode,
            "route_mode": rounds_payload.get("route_mode"),
            "validation_status": "validation_failed",
            "validation": validation,
            "real_platform_called": False,
            "dataagent_called": False,
            "fallback_used": False,
            "final_status": "validation_failed",
        }

    case_id = "dennis_sample_expand_validate_batch"
    disabled_actions = disabled_actions_for_sample_batch(args, rounds_payload)
    round_results = [
        execute_sample_round(
            case_id=case_id,
            round_item=round_item,
            args=args,
            window_start_ms=window_start_ms,
            window_end_ms=window_end_ms,
            disabled_actions=disabled_actions,
        )
        for round_item in rounds_payload.get("rounds", [])
    ]
    cumulative_result = build_cumulative_sample_result(
        rounds_payload=rounds_payload,
        validation=validation,
        round_results=round_results,
        args=args,
    )
    orchestration_artifacts = build_cumulative_orchestration_artifacts(
        round_results=round_results,
        cumulative_result=cumulative_result,
    )
    service_unavailable = any(
        item.get("batch_status") == "harness_error" for item in round_results
    )
    return {
        "schema_version": "runtime_case_execution_result_v1",
        "task": args.task,
        "route_mode": "sample_expand_validate_mode",
        "mode": args.mode,
        "input_summary": {
            "total_input_count": rounds_payload.get("total_input_count"),
            "round_size": validation["round_size"],
            "max_rounds": validation["max_rounds"],
            "planned_rounds_this_run": validation["planned_rounds_this_run"],
            "max_deep_checked_this_run": validation["max_deep_checked_this_run"],
            "sampling_method": rounds_payload.get("sampling_method"),
            "data_window": args.data_window or rounds_payload.get("data_window"),
            "scene_hint": args.scene_hint or rounds_payload.get("scene_hint", []),
            "disabled_actions": sorted(disabled_actions),
            "login_logs_skipped_for_this_run": "login_logs_search" in disabled_actions,
        },
        "validation": validation,
        "execution_gate": {
            "entry": "runtime_case_execution_runner.py",
            "task": "sample_expand_validate_batch",
            "batch_endpoint": "/actions/batch",
            "manual_local_batch_curl_fallback_allowed": False,
            "legacy_runner_fallback_allowed": False,
            "per_user_ato_single_case_loop_allowed": False,
            "direct_platform_curl_allowed": False,
            "dataagent_hive_execution_allowed": False,
            "default_runtime_routing": False,
        },
        "source_orchestration_check": run_orchestration_check("sample_expand_validate_mode", validation["total_deep_checked_requested"]),
        "round_results": round_results,
        "cumulative_result": cumulative_result,
        "orchestration_artifacts": orchestration_artifacts,
        "user_visible_summary": render_sample_expand_user_summary(cumulative_result, round_results),
        "final_answer_boundary": {
            "ordinary_user_answer_must_not_dump_routing_metadata": True,
            "manual_curl_actions_batch_fallback_allowed": False,
            "dataagent_hive_called": False,
            "offline_validate_requires_user_authorization": True,
            "threshold_70_percent_is_validation_not_disposition": True,
            "final_risk_judgement_made": False,
        },
        "safety": {
            "platform_called": args.mode == "live" and not service_unavailable,
            "real_platform_called": args.mode == "live" and not service_unavailable,
            "platform_call_scope": "local_browser_backed_batch_only" if args.mode == "live" and not service_unavailable else "none",
            "dataagent_called": False,
            "hive_called": False,
            "legacy_runner_called": False,
            "manual_actions_batch_curl_called": False,
            "direct_platform_url_called": False,
            "per_user_ato_single_case_loop_called": False,
            "fallback_used": False,
            "secrets_output": False,
        },
        "final_status": "blocked" if service_unavailable else "dry_run_planned" if args.mode == "dry_run" else "partial",
    }


def build_result(args: argparse.Namespace) -> dict[str, Any]:
    if args.task == "sample_expand_validate_batch":
        return build_sample_expand_validate_batch_result(args)

    if not args.user_id:
        raise ValueError("--user-id is required for ato_single_case")
    if args.window_start_ms is None or args.window_end_ms is None:
        window_start_ms, window_end_ms = _default_scene_window()
    else:
        window_start_ms, window_end_ms = args.window_start_ms, args.window_end_ms

    if window_start_ms >= window_end_ms:
        raise ValueError("window_start_ms must be earlier than window_end_ms")

    case_id = _compact_case_id(args.task, args.user_id)
    source_plan = build_ato_single_case_source_plan(
        args.user_id,
        device_id=args.device_id,
        window_start_ms=window_start_ms,
        window_end_ms=window_end_ms,
        include_abnormal_publish=args.include_abnormal_publish,
        include_same_device=args.include_same_device,
    )
    track_missing_device_id = args.device_id is None
    deferred_source_ids = {"ato_track_analysis_check_data_ready"} if track_missing_device_id else set()
    primary_source_plan = [item for item in source_plan if item.source_id not in deferred_source_ids]
    track_item = next((item for item in source_plan if item.source_id == "ato_track_analysis_check_data_ready"), None)
    batch_payload = build_batch_payload(case_id, primary_source_plan, dry_run=args.mode == "dry_run")
    batch_contract_validation = validate_batch_payload_contract(batch_payload)

    if args.mode == "dry_run":
        primary_result = build_dry_run_batch_result(primary_source_plan)
    else:
        if not args.browser_backed_base:
            raise ValueError("--browser-backed-base is required in live mode")
        primary_result = call_browser_backed_batch(args.browser_backed_base, batch_payload)

    executed_source_plan = list(source_plan)
    primary_source_quality_matrix = merge_source_quality(primary_source_plan, primary_result)
    primary_source_observations = build_source_observations(
        primary_source_plan,
        primary_source_quality_matrix,
        primary_result,
    )
    primary_user_device_entity_resolution = build_user_device_entity_resolution(
        source_plan,
        primary_result,
        provided_device_id=args.device_id,
        source_observations=primary_source_observations,
    )
    followup_batch_payloads: list[dict[str, Any]] = []
    followup_results: list[dict[str, Any]] = []
    photo_detail_followup_items = build_photo_detail_followup_items(
        primary_source_observations,
        window_start_ms=window_start_ms,
        window_end_ms=window_end_ms,
    )
    if photo_detail_followup_items:
        executed_source_plan.extend(photo_detail_followup_items)
        followup_payload = build_batch_payload(
            f"{case_id}:photo_detail_followup",
            photo_detail_followup_items,
            dry_run=args.mode == "dry_run",
        )
        followup_batch_payloads.append(followup_payload)
        if args.mode == "dry_run":
            followup_results.append(build_dry_run_batch_result(photo_detail_followup_items))
        else:
            followup_results.append(call_browser_backed_batch(args.browser_backed_base, followup_payload))

    pre_track_result = merge_batch_results([primary_result, *followup_results])
    pre_track_source_quality_matrix = merge_source_quality(executed_source_plan, pre_track_result)
    pre_track_source_observations = build_source_observations(
        executed_source_plan,
        pre_track_source_quality_matrix,
        pre_track_result,
    )
    pre_track_user_device_entity_resolution = build_user_device_entity_resolution(
        executed_source_plan,
        pre_track_result,
        provided_device_id=args.device_id,
        source_observations=pre_track_source_observations,
    )
    primary_candidates = pre_track_user_device_entity_resolution.get("candidate_device_ids", [])
    candidate_device_id = (
        args.device_id
        or (primary_candidates[0]["device_id"] if primary_candidates else None)
        or extract_candidate_device_id(pre_track_result)
    )
    track_device_resolution = {
        "device_id_provided": args.device_id is not None,
        "candidate_device_lookup_attempted": track_missing_device_id,
        "candidate_device_found": bool(candidate_device_id),
        "track_missing_device_id_blocks_batch": False,
        "photo_detail_next_hop_attempted_before_track": bool(photo_detail_followup_items),
        "photo_detail_next_hop_source_ids": [item.source_id for item in photo_detail_followup_items],
    }

    if track_item and track_missing_device_id:
        if candidate_device_id:
            followup_track = with_track_device(source_plan, candidate_device_id)
            followup_payload = build_batch_payload(
                f"{case_id}:track_followup",
                [followup_track],
                dry_run=args.mode == "dry_run",
            )
            followup_batch_payloads.append(followup_payload)
            if args.mode == "dry_run":
                followup_results.append(build_dry_run_batch_result([followup_track]))
            else:
                followup_results.append(call_browser_backed_batch(args.browser_backed_base, followup_payload))
        else:
            followup_results.append(synthetic_track_missing_result(track_item))

    batch_result_raw = merge_batch_results([primary_result, *followup_results])
    source_quality_matrix = merge_source_quality(executed_source_plan, batch_result_raw)
    source_observations = build_source_observations(executed_source_plan, source_quality_matrix, batch_result_raw)
    user_device_entity_resolution = build_user_device_entity_resolution(
        executed_source_plan,
        batch_result_raw,
        provided_device_id=args.device_id,
        source_observations=source_observations,
    )
    batch_result = build_safe_batch_summary(batch_result_raw, source_quality_matrix)
    missing_evidence = build_missing_evidence(source_quality_matrix)
    missing_evidence.extend(user_device_entity_resolution.get("missing_evidence", []))
    evidence_card = build_evidence_card(
        args.task,
        args.user_id,
        args.mode,
        source_quality_matrix,
        source_observations,
        user_device_entity_resolution,
        missing_evidence,
    )
    live_response_inspection = build_live_response_inspection(
        source_plan,
        batch_result_raw,
        source_observations,
        evidence_card,
    )
    user_answer_draft = render_user_answer_draft(evidence_card)

    return {
        "schema_version": "runtime_case_execution_result_v1",
        "task": args.task,
        "mode": args.mode,
        "user_id": args.user_id,
        "time_window_ms": {
            "start": window_start_ms,
            "end": window_end_ms,
            "inferred": args.window_start_ms is None or args.window_end_ms is None,
            "policy": "scene_window_default_30d; source-specific windows may be narrower",
        },
        "source_time_windows": {
            item.source_id: {
                "start": item.window_start_ms,
                "end": item.window_end_ms,
                "window_policy": item.window_policy,
            }
            for item in source_plan
        },
        "execution_gate": {
            "entry": "runtime_case_execution_runner.py",
            "source_plan_required": True,
            "batch_endpoint": "/actions/batch",
            "manual_local_batch_curl_fallback_allowed": False,
            "legacy_runner_fallback_allowed": False,
            "browser_backed_single_action_freeform_allowed": False,
            "direct_platform_curl_allowed": False,
            "default_runtime_routing": False,
        },
        "source_orchestration_check": run_orchestration_check(args.task, 1),
        "source_plan": [item.to_plan_dict() for item in source_plan],
        "auto_realtime_next_hop_source_plan": [
            item.to_plan_dict() for item in executed_source_plan if item.source_id not in {source.source_id for source in source_plan}
        ],
        "execution_groups": [
            {
                "group_id": group["group_id"],
                "execution": group["execution"],
                "depends_on": group.get("depends_on", []),
                "source_ids": [source["source_id"] for source in group["sources"]],
            }
            for group in batch_payload["execution_groups"]
        ],
        "batch_endpoint": "/actions/batch",
        "batch_payload": batch_payload,
        "batch_contract_validation": batch_contract_validation,
        "followup_batch_payloads": followup_batch_payloads,
        "photo_detail_next_hop": {
            "attempted": bool(photo_detail_followup_items),
            "source_ids": [item.source_id for item in photo_detail_followup_items],
            "actions": [item.action for item in photo_detail_followup_items],
            "execution_path": "controlled_batch_followup_only",
            "manual_curl_or_single_action_fallback_allowed": False,
        },
        "track_device_resolution": track_device_resolution,
        "user_device_entity_resolution": user_device_entity_resolution,
        "batch_result": batch_result,
        "live_response_inspection": live_response_inspection,
        "transport_status_matrix": batch_result.get("transport_status_matrix", []),
        "source_observations": source_observations,
        "source_quality_matrix": source_quality_matrix,
        "evidence_card": evidence_card,
        "user_answer_draft": user_answer_draft,
        "missing_evidence": missing_evidence,
        "offline_backfill_recommendation": evidence_card.get("offline_backfill_recommendation"),
        "final_answer_boundary": {
            "ordinary_user_answer_must_not_dump_routing_metadata": True,
            "raw_upstream_body_returned": False,
            "service_normalized_observation_dependency": False,
            "service_source_quality_dependency": False,
            "service_evidence_card_inputs_dependency": False,
            "manual_curl_actions_batch_fallback_allowed": False,
            "dataagent_hive_called": False,
            "dynamic_offline_authorization_options_visible_when_realtime_incomplete": True,
            "fixed_1_to_5_offline_menu_used": False,
            "offline_hive_requires_per_request_authorization": True,
            "final_risk_judgement_made": False,
        },
        "final_status": evidence_card["final_status"],
        "safety": {
            "platform_called": args.mode == "live",
            "platform_call_scope": "local_browser_backed_batch_only" if args.mode == "live" else "none",
            "dataagent_called": False,
            "legacy_runner_called": False,
            "manual_actions_batch_curl_called": False,
            "direct_platform_url_called": False,
            "secrets_output": False,
        },
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Dennis controlled case execution harness")
    parser.add_argument("--task", choices=["ato_single_case", "sample_expand_validate_batch"], required=True)
    parser.add_argument("--user-id")
    parser.add_argument("--device-id")
    parser.add_argument("--rounds-json")
    parser.add_argument("--mode", choices=["dry_run", "live"], default="dry_run")
    parser.add_argument("--browser-backed-base")
    parser.add_argument("--window-start-ms", type=int)
    parser.add_argument("--window-end-ms", type=int)
    parser.add_argument("--scene-hint", action="append")
    parser.add_argument("--data-window")
    parser.add_argument("--disable-action", action="append", default=[])
    parser.add_argument("--skip-login-logs", action="store_true")
    parser.add_argument("--max-rounds", type=int)
    parser.add_argument("--max-deep-checked", type=int)
    parser.add_argument("--output-json")
    parser.add_argument("--include-abnormal-publish", action="store_true")
    parser.add_argument("--include-same-device", action="store_true")
    parser.add_argument("--format", choices=["json", "pretty"], default="json")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    result = build_result(args)
    output_result = build_safe_stdout_result(result)
    if args.output_json:
        output_path = Path(args.output_json)
        output_path.write_text(json.dumps(output_result, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    if args.format == "json":
        print(json.dumps(output_result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"task: {output_result['task']}")
        print(f"mode: {output_result['mode']}")
        print(f"final_status: {output_result['final_status']}")
        if output_result.get("source_plan"):
            print("source_plan:")
            for item in output_result["source_plan"]:
                print(f"- {item['source_id']} -> {item['action']} [{item['execution_group']}]")
        elif output_result.get("round_results"):
            print("round_results:")
            for item in output_result["round_results"]:
                print(f"- round {item['round_id']}: {item['sampled_count']} entities -> {item['decision']['action']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
