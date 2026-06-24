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
MAX_ONE_DEGREE_USERS_PER_SEED = 2
MAX_ONE_DEGREE_ASSOCIATED_USERS_TOTAL = 6
DEFAULT_BROWSER_BACKED_BASE = "http://127.0.0.1:8787"
SOURCE_ACTION_CHUNK_LIMITS = {
    "login_logs_search": 2,
    "rcp_fast_query_hbase": 5,
    "archives_gallery_photo_list": 10,
    "archives_photo_profile": 10,
    "archives_photo_meta": 10,
}
TIMEOUT_CIRCUIT_BREAKER_ACTIONS = {"rcp_event_detail", "rcp_event_feature_list"}
TIMEOUT_CIRCUIT_CONSECUTIVE_CHUNKS = 2
TIMEOUT_CIRCUIT_RATIO_THRESHOLD = 0.5
AUTH_FAILED_SHORT_CIRCUIT_THRESHOLD = 2
TRACK_BUSINESS_GAP_MARKERS = {"NEED_DATA_SYNC", "HIVE_UNFINISHED"}
TRACK_READINESS_ACTION = "track_analysis_check_data_ready"
WEAPON_INVENTORY_ACTION = "weapon_inventory"

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
RAW_CONTRACT_BODY_KEYS = (
    "raw_body",
    "body",
    "response_body",
    "upstream_body",
    "capped_body",
    "payload",
)
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


def sanitize_for_raw_observation_contract(value: Any) -> Any:
    """Retain non-secret nested bodies for local L1 contract artifacts."""
    if isinstance(value, dict):
        clean: dict[str, Any] = {}
        for key, item in value.items():
            if _is_credential_secret_key(str(key)):
                continue
            clean[str(key)] = sanitize_for_raw_observation_contract(item)
        return clean
    if isinstance(value, list):
        return [sanitize_for_raw_observation_contract(item) for item in value]
    if isinstance(value, bytes):
        try:
            return value.decode("utf-8")
        except UnicodeDecodeError:
            return "<binary_body_omitted>"
    if isinstance(value, str):
        credential_field = r"(?i:cookie|cookies|token|accessToken|refreshToken|session|authorization|password)"
        value = re.sub(
            rf'("{credential_field}"\s*:\s*")[^"]*(")',
            r"\1<credential_secret_removed>\2",
            value,
        )
        value = re.sub(
            rf'(\\\"{credential_field}\\\"\s*:\s*\\\")[^\\"]*(\\\")',
            r"\1<credential_secret_removed>\2",
            value,
        )
        return value
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


def build_short_circuit_batch_result(
    source_plan: list[SourcePlanItem],
    *,
    gap_state: str,
    gap_reason: str,
    short_circuit_type: str,
    circuit_open: bool = False,
) -> dict[str, Any]:
    """Build a synthetic source-gap result for sources intentionally not called.

    This preserves source coverage accounting without treating skipped tail work
    as no-risk evidence. It is used only after local scheduler decisions such as
    timeout circuit-open, repeated auth failure, or missing required anchors.
    """
    transport_rows: dict[str, dict[str, Any]] = {}
    source_results: dict[str, dict[str, Any]] = {}
    missing_or_failed_sources: list[dict[str, Any]] = []
    for item in source_plan:
        row = {
            "source_id": item.source_id,
            "action": item.action,
            "category": "blocked",
            "source_status": gap_state,
            "error_type": gap_reason,
            "gap_state": gap_state,
            "gap_reason": gap_reason,
            "short_circuit": True,
            "short_circuit_type": short_circuit_type,
            "circuit_open": circuit_open,
            "http_status": None,
            "content_type": None,
            "body_present": False,
            "body_truncated": False,
            "observed_bytes": 0,
            "elapsed_ms": 0,
            "timeout_ms": item.timeout_ms,
            "transport_error": None,
            "platform_error": None,
            "invalid_params": False,
            "timed_out": gap_reason == "circuit_open_timeout",
            "raw_body_handling": "not_requested_short_circuit",
            "is_low_risk_counter_evidence": False,
            "no_data_not_risk_exclusion": True,
        }
        transport_rows[item.source_id] = row
        source_results[item.source_id] = {
            "source_id": item.source_id,
            "action": item.action,
            "category": "blocked",
            "source_status": gap_state,
            "transport": row,
        }
        missing_or_failed_sources.append(row)
    return {
        "ok": True,
        "response_mode": "controlled_batch_passthrough",
        "batch_status": "short_circuit_source_gap",
        "scheduler": "controlled_parallel",
        "source_results": source_results,
        "transport_status_matrix": transport_rows,
        "classifications": build_classifications(transport_rows),
        "missing_or_failed_sources": missing_or_failed_sources,
        "short_circuit_summary": {
            "short_circuit_type": short_circuit_type,
            "gap_state": gap_state,
            "gap_reason": gap_reason,
            "source_count": len(source_plan),
            "source_actions": unique_strings([item.action for item in source_plan]),
            "affected_user_count": _source_plan_user_count(source_plan),
            "circuit_open": circuit_open,
            "no_risk_counter_evidence": False,
        },
        "safety": {
            "raw_body_returned": False,
            "legacy_runner_fallback_attempted": False,
            "single_action_freeform_attempted": False,
        },
    }


def _source_plan_user_count(items: list[SourcePlanItem]) -> int:
    users = {
        str(item.params.get("user_id") or item.params.get("source_id") or item.params.get("device_id") or item.source_id)
        for item in items
    }
    return len({value for value in users if value})


def _gap_reason_counts_from_quality(chunk_quality: dict[str, Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in chunk_quality.get("per_source", []) or []:
        if not isinstance(row, dict):
            continue
        reason = str(row.get("gap_reason") or row.get("error_type") or "")
        if not reason:
            continue
        counts[reason] = counts.get(reason, 0) + 1
    return counts


def _track_business_gap_reason(row: dict[str, Any]) -> str | None:
    action = str(row.get("action") or "")
    if action != TRACK_READINESS_ACTION:
        return None
    text = json.dumps(row, ensure_ascii=False, sort_keys=True)
    if any(marker in text for marker in TRACK_BUSINESS_GAP_MARKERS):
        return "NEED_DATA_SYNC_or_HIVE_UNFINISHED"
    status = str(row.get("source_status") or row.get("category") or "").lower()
    if "completed" not in status:
        return None
    business_field_keys = {
        "track_data_ready",
        "dataReady",
        "ready",
        "event_day_frontend_activity",
        "frontend_backend_activity_alignment",
        "duration",
        "active_days",
        "lineage",
    }
    if not any(key in row for key in business_field_keys):
        return "track_business_fields_missing"
    return None


def _weapon_riskdata_gap_reason(row: dict[str, Any]) -> str | None:
    if str(row.get("action") or "") != WEAPON_INVENTORY_ACTION:
        return None
    text = json.dumps(row, ensure_ascii=False, sort_keys=True)
    if "not_executed_missing_device_id" in text:
        return "missing_raw_device_id"
    return None


def _quality_counts_by_action(chunk_quality: dict[str, Any]) -> dict[str, dict[str, int]]:
    counts: dict[str, dict[str, int]] = {}
    for row in chunk_quality.get("per_source", []) or []:
        if not isinstance(row, dict):
            continue
        action = str(row.get("action") or "unknown_action")
        action_counts = counts.setdefault(
            action,
            {"total": 0, "completed": 0, "timeout": 0, "auth_failed": 0, "blocked": 0, "partial": 0, "parse_error": 0},
        )
        action_counts["total"] += 1
        quality = str(row.get("quality_class") or "")
        if quality in action_counts:
            action_counts[quality] += 1
        elif quality == "no_data":
            action_counts["completed"] += 1
    return counts


def _new_scheduler_state() -> dict[str, Any]:
    return {
        "action_stats": {},
        "open_circuits": {},
        "events": [],
    }


def _open_scheduler_circuit(
    scheduler_state: dict[str, Any],
    *,
    source_action: str,
    gap_reason: str,
    short_circuit_type: str,
) -> None:
    if source_action in scheduler_state["open_circuits"]:
        return
    event = {
        "source_action": source_action,
        "gap_reason": gap_reason,
        "short_circuit_type": short_circuit_type,
        "circuit_open": True,
        "opened_at": _iso_now(),
    }
    scheduler_state["open_circuits"][source_action] = event
    scheduler_state["events"].append(event)


def _update_scheduler_state_from_chunk(
    scheduler_state: dict[str, Any],
    *,
    chunk_quality: dict[str, Any],
) -> list[dict[str, Any]]:
    opened_before = set(scheduler_state["open_circuits"])
    for action, counts in _quality_counts_by_action(chunk_quality).items():
        stats = scheduler_state["action_stats"].setdefault(
            action,
            {
                "chunks_seen": 0,
                "sources_seen": 0,
                "timeout_count": 0,
                "auth_failed_count": 0,
                "consecutive_timeout_chunks": 0,
                "consecutive_auth_failed_chunks": 0,
            },
        )
        stats["chunks_seen"] += 1
        stats["sources_seen"] += counts["total"]
        stats["timeout_count"] += counts["timeout"]
        stats["auth_failed_count"] += counts["auth_failed"]
        stats["consecutive_timeout_chunks"] = (
            stats["consecutive_timeout_chunks"] + 1
            if counts["timeout"] > 0
            else 0
        )
        stats["consecutive_auth_failed_chunks"] = (
            stats["consecutive_auth_failed_chunks"] + 1
            if counts["auth_failed"] > 0
            else 0
        )
        timeout_ratio = stats["timeout_count"] / stats["sources_seen"] if stats["sources_seen"] else 0.0
        if action in TIMEOUT_CIRCUIT_BREAKER_ACTIONS and (
            stats["consecutive_timeout_chunks"] >= TIMEOUT_CIRCUIT_CONSECUTIVE_CHUNKS
            or timeout_ratio > TIMEOUT_CIRCUIT_RATIO_THRESHOLD
        ):
            _open_scheduler_circuit(
                scheduler_state,
                source_action=action,
                gap_reason="circuit_open_timeout",
                short_circuit_type="timeout_circuit_breaker",
            )
        if stats["auth_failed_count"] >= AUTH_FAILED_SHORT_CIRCUIT_THRESHOLD or stats["consecutive_auth_failed_chunks"] >= 2:
            _open_scheduler_circuit(
                scheduler_state,
                source_action=action,
                gap_reason="auth_session_issue",
                short_circuit_type="auth_failed_short_circuit",
            )
    return [
        event
        for action, event in scheduler_state["open_circuits"].items()
        if action not in opened_before
    ]


def _split_by_scheduler_circuit(
    scheduler_state: dict[str, Any],
    items: list[SourcePlanItem],
) -> tuple[list[SourcePlanItem], list[SourcePlanItem], dict[str, list[SourcePlanItem]]]:
    active: list[SourcePlanItem] = []
    skipped: list[SourcePlanItem] = []
    by_reason: dict[str, list[SourcePlanItem]] = {}
    for item in items:
        circuit = scheduler_state["open_circuits"].get(item.action)
        if not circuit:
            active.append(item)
            continue
        skipped.append(item)
        by_reason.setdefault(str(circuit.get("gap_reason") or "source_gap"), []).append(item)
    return active, skipped, by_reason


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
        reason = getattr(exc, "reason", None)
        reason_type = type(reason).__name__ if reason is not None else type(exc).__name__
        reason_text = sanitize_for_output(str(reason) if reason is not None else str(exc))
        return build_harness_error_result(
            source_status="service_unavailable",
            error_type=f"{type(exc).__name__}:{reason_type}",
            detail={"reason": reason_text, "reason_type": reason_type},
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


DEFAULT_SAMPLE_BATCH_CHECKPOINT_DIR = Path("/private/tmp/dennis_f5_r3_checkpoints")


def _iso_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())


def _elapsed_ms(start_monotonic: float) -> int:
    return int((time.monotonic() - start_monotonic) * 1000)


def _chunk_actions_from_payload(payload: dict[str, Any]) -> list[str]:
    actions: list[str] = []
    for group in payload.get("execution_groups", []):
        if not isinstance(group, dict):
            continue
        for source in group.get("sources", []):
            if not isinstance(source, dict):
                continue
            action = str(source.get("action") or "").strip()
            if action:
                actions.append(action)
    return actions


def _chunk_source_ids_from_payload(payload: dict[str, Any]) -> list[str]:
    source_ids: list[str] = []
    for group in payload.get("execution_groups", []):
        if not isinstance(group, dict):
            continue
        for source in group.get("sources", []):
            if not isinstance(source, dict):
                continue
            source_id = str(source.get("source_id") or "").strip()
            if source_id:
                source_ids.append(source_id)
    return source_ids


def _chunk_source_group_from_payload(payload: dict[str, Any]) -> str:
    actions = unique_strings(_chunk_actions_from_payload(payload))
    if not actions:
        return "unknown_source_group"
    return "+".join(actions)


def _checkpoint_dir_for_args(args: argparse.Namespace, case_id: str) -> Path:
    base = Path(args.checkpoint_dir) if getattr(args, "checkpoint_dir", None) else DEFAULT_SAMPLE_BATCH_CHECKPOINT_DIR
    return base / case_id


def _pending_sources_from_quality(
    source_plan: list[SourcePlanItem],
    source_quality_matrix: dict[str, Any],
) -> list[str]:
    seen: set[str] = set()
    buckets = source_quality_matrix.get("buckets", {}) if isinstance(source_quality_matrix, dict) else {}
    for key in ("completed", "partial", "blocked", "timeout", "no_data", "auth_failed", "parse_error", "planned"):
        for source_id in buckets.get(key, []) or []:
            seen.add(str(source_id))
    pending = [item.source_id for item in source_plan if item.source_id not in seen]
    return pending


def _checkpoint_source_quality_summary(source_quality_matrix: dict[str, Any]) -> dict[str, Any]:
    summary = _source_quality_summary_for_output(source_quality_matrix)
    summary["completed_count"] = len(summary.get("completed", []))
    summary["partial_count"] = len(summary.get("partial", []))
    summary["blocked_count"] = len(summary.get("blocked", []))
    summary["timeout_count"] = len(summary.get("timeout", []))
    summary["auth_failed_count"] = len(summary.get("auth_failed", []))
    summary["pending_count"] = len(_pending_sources_from_quality([], {}))
    return summary


def _emit_sample_batch_progress(progress_row: dict[str, Any]) -> None:
    print(
        json.dumps(
            {
                "progress": {
                    "current_chunk_id": progress_row.get("current_chunk_id"),
                    "current_round_index": progress_row.get("current_round_index"),
                    "current_batch_index": progress_row.get("current_batch_index"),
                    "current_source_group": progress_row.get("current_source_group"),
                    "current_running_sources": progress_row.get("current_running_sources"),
                    "elapsed_seconds": progress_row.get("elapsed_seconds"),
                    "completed_source_count": progress_row.get("completed_source_count"),
                    "partial_source_count": progress_row.get("partial_source_count"),
                    "blocked_source_count": progress_row.get("blocked_source_count"),
                    "pending_source_count": progress_row.get("pending_source_count"),
                    "last_checkpoint_file": progress_row.get("last_checkpoint_file"),
                }
            },
            ensure_ascii=False,
        ),
        flush=True,
    )


def _write_sample_batch_checkpoint(
    *,
    checkpoint_dir: Path,
    case_id: str,
    round_index: int,
    batch_index: int,
    chunk_id: str,
    current_source_group: str,
    current_running_sources: list[str],
    current_source_plan: list[SourcePlanItem],
    current_results: list[dict[str, Any]],
    sampled_entities: list[str],
    mode: str,
    disabled_actions: set[str],
    waiting_reason: str,
    timing_trace: dict[str, Any],
    checkpoint_phase: str,
) -> tuple[str, dict[str, Any]]:
    checkpoint_started = time.monotonic()
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    batch_result_raw = merge_batch_results(current_results)
    source_quality_matrix = merge_source_quality(current_source_plan, batch_result_raw)
    source_observations = build_source_observations(current_source_plan, source_quality_matrix, batch_result_raw)
    source_commonality_cards = build_batch_source_commonality_cards(
        source_quality_matrix,
        len(sampled_entities),
        source_observations,
        disabled_actions,
    )
    orchestration_artifacts = build_round_orchestration_artifacts(
        round_id=round_index,
        sampled_entities=sampled_entities,
        source_plan=current_source_plan,
        source_quality_matrix=source_quality_matrix,
        source_observations=source_observations,
        source_commonality_cards=source_commonality_cards,
        mode=mode,
        disabled_actions=disabled_actions,
    )
    pending_sources = _pending_sources_from_quality(current_source_plan, source_quality_matrix)
    quality_summary = _source_quality_summary_for_output(source_quality_matrix)
    quality_summary["completed_count"] = len(quality_summary.get("completed", []))
    quality_summary["partial_count"] = len(quality_summary.get("partial", []))
    quality_summary["blocked_count"] = len(quality_summary.get("blocked", []))
    quality_summary["timeout_count"] = len(quality_summary.get("timeout", []))
    quality_summary["auth_failed_count"] = len(quality_summary.get("auth_failed", []))
    quality_summary["pending_count"] = len(pending_sources)
    checkpoint_payload = {
        "case_id": case_id,
        "chunk_id": chunk_id,
        "round_index": round_index,
        "batch_index": batch_index,
        "current_running_source": current_running_sources[0] if current_running_sources else None,
        "current_running_sources": current_running_sources,
        "completed_sources": quality_summary.get("completed", []),
        "partial_sources": quality_summary.get("partial", []),
        "blocked_sources": quality_summary.get("blocked", []),
        "timeout_sources": quality_summary.get("timeout", []),
        "auth_failed_sources": quality_summary.get("auth_failed", []),
        "pending_sources": pending_sources,
        "source_quality_summary": quality_summary,
        "raw_detail_flat_table_summary": orchestration_artifacts.get("raw_detail_flat_table_summary"),
        "field_value_commonality_funnel_summary": orchestration_artifacts.get("field_value_commonality_funnel"),
        "candidate_features_count": len(orchestration_artifacts.get("candidate_features", []) or []),
        "attack_chain_cooccurrence_count": len(orchestration_artifacts.get("attack_chain_cooccurrence", []) or []),
        "risk_choke_point_candidate_count": sum(
            1
            for item in orchestration_artifacts.get("candidate_features", []) or []
            if isinstance(item, dict) and str(item.get("risk_choke_point_type") or "").strip()
        ),
        "last_successful_source": (
            quality_summary.get("partial", [])[-1]
            if quality_summary.get("partial") else
            quality_summary.get("completed", [])[-1]
            if quality_summary.get("completed") else
            None
        ),
        "failure_or_waiting_reason": waiting_reason,
        "checkpoint_written_at": _iso_now(),
        "timing_trace": timing_trace,
        "partial_result_available": bool(
            quality_summary.get("completed") or quality_summary.get("partial") or quality_summary.get("blocked")
            or quality_summary.get("timeout") or quality_summary.get("auth_failed")
        ),
    }
    checkpoint_path = checkpoint_dir / f"round_{round_index:02d}_batch_{batch_index:02d}_{chunk_id}_{checkpoint_phase}.json"
    checkpoint_path.write_text(
        json.dumps(project_safe_stdout_value(checkpoint_payload), ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    timing_trace.setdefault("global", {})["checkpoint_write_ms"] = int(
        timing_trace.get("global", {}).get("checkpoint_write_ms") or 0
    ) + _elapsed_ms(checkpoint_started)
    progress_row = {
        "current_chunk_id": chunk_id,
        "current_round_index": round_index,
        "current_batch_index": batch_index,
        "current_source_group": current_source_group,
        "current_running_sources": current_running_sources,
        "elapsed_seconds": round((timing_trace.get("global", {}).get("total_elapsed_ms") or 0) / 1000, 2),
        "last_checkpoint_file": str(checkpoint_path),
        "completed_source_count": quality_summary["completed_count"],
        "partial_source_count": quality_summary["partial_count"],
        "blocked_source_count": quality_summary["blocked_count"],
        "pending_source_count": quality_summary["pending_count"],
    }
    return str(checkpoint_path), progress_row


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
    if _explicit_auth_failure(row):
        return "auth_failed"
    if row.get("invalid_params") or "missing_required" in status or "invalid" in status or "invalid" in error_type:
        return "invalid_params"
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
        row.setdefault("action", item.action if item else row.get("action"))
        track_gap_reason = _track_business_gap_reason(row)
        weapon_gap_reason = _weapon_riskdata_gap_reason(row)
        if track_gap_reason:
            row["gap_state"] = "track_business_field_gap"
            row["gap_reason"] = track_gap_reason
            row["source_status"] = "track_business_field_gap"
            row["error_type"] = track_gap_reason
        elif weapon_gap_reason:
            row["gap_state"] = "not_executed_missing_device_id"
            row["gap_reason"] = weapon_gap_reason
            row["source_status"] = "partial"
            row["error_type"] = weapon_gap_reason
        transport_interpretation = derive_transport_interpretation(row)
        classification = classify_source(row)
        if track_gap_reason:
            classification = "blocked"
        elif weapon_gap_reason:
            classification = "partial"
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
        if track_gap_reason:
            notes.extend(["track_business_field_gap", "missing_evidence_not_counter_evidence"])
        if weapon_gap_reason:
            notes.extend(["not_executed_missing_device_id", "missing_evidence_not_counter_evidence"])
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
                "gap_state": row.get("gap_state"),
                "gap_reason": row.get("gap_reason"),
                "is_low_risk_counter_evidence": False if row.get("gap_state") else None,
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
        if row.get("gap_state") or row.get("gap_reason"):
            item["gap_state"] = row.get("gap_state")
            item["gap_reason"] = row.get("gap_reason")
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
    "archives_comment_search": {
        "chain_section": "content_social_handoff",
        "expected_business_fields": [
            "photo_id",
            "comment_id",
            "comment_text",
            "action_time",
            "target_user_id",
            "relation_type",
        ],
        "role": "评论承接线索，只作为内容/社交候选，不单独定性。",
    },
    "archives_private_message_search": {
        "chain_section": "content_social_handoff",
        "expected_business_fields": [
            "message_id",
            "message_text",
            "sender",
            "receiver",
            "target_user_id",
            "action_time",
            "relation_type",
        ],
        "role": "私信承接线索，只作为单用户/小批候选，不直接升级为团伙或最终风险结论。",
    },
    "archives_fans_list": {
        "chain_section": "content_social_handoff",
        "expected_business_fields": [
            "target_user_id",
            "relation_type",
            "action_time",
        ],
        "role": "粉丝关系上下文，只作社交关系候选输入。",
    },
    "archives_follow_list": {
        "chain_section": "content_social_handoff",
        "expected_business_fields": [
            "target_user_id",
            "relation_type",
            "action_time",
        ],
        "role": "关注关系上下文，只作社交关系候选输入。",
    },
    "archives_user_report_search": {
        "chain_section": "feedback_signal",
        "expected_business_fields": [
            "report_id",
            "report_time",
            "report_type",
            "feedback_object",
            "feedback_signal",
        ],
        "role": "举报明细线索，是反馈不是风险事实。",
    },
    "archives_negative_report": {
        "chain_section": "feedback_signal",
        "expected_business_fields": [
            "report_id",
            "report_time",
            "report_type",
            "feedback_object",
            "feedback_signal",
        ],
        "role": "负向反馈汇总线索，是反馈不是风险事实。",
    },
    "archives_review_logs": {
        "chain_section": "enforcement_review",
        "expected_business_fields": [
            "review_id",
            "review_result",
            "review_scene",
            "enforcement_action",
            "review_time",
            "enforcement_time",
            "policy_reason",
        ],
        "role": "审核日志/治理动作线索，是处置过程不是黑灰产本质。",
    },
    "archives_punish_status": {
        "chain_section": "enforcement_review",
        "expected_business_fields": [
            "punish_id",
            "punish_type",
            "enforcement_action",
            "enforcement_time",
            "policy_reason",
            "photo_id",
            "user_id",
        ],
        "role": "处罚状态/处罚原因线索，是治理状态不是黑灰产本质。",
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
    "weapon_device_info": {
        "chain_section": "device_detail",
        "expected_business_fields": [
            "device_id",
            "phone_model",
            "os_version",
            "app_version",
            "device_platform",
            "risk_label",
            "launch_count",
            "boot_duration",
        ],
        "role": "Weapon 设备详情主 source，字段进入 device_detail_table，不替代风险结论",
    },
    "weapon_device_app_list": {
        "chain_section": "device_app_environment",
        "expected_business_fields": [
            "device_id",
            "installed_app_list",
            "risk_app",
            "tool_app",
            "app_environment_signal",
        ],
        "role": "Weapon 安装列表 / 应用环境 source，字段进入 device_detail_table",
    },
    "weapon_device_location_info": {
        "chain_section": "device_network_location",
        "expected_business_fields": [
            "device_id",
            "user_id",
            "ip_or_network",
            "location",
        ],
        "role": "Weapon 设备位置 / 网络上下文 source，需要 device_id + user_id",
    },
    "weapon_user_klink_status": {
        "chain_section": "account_device_session_status",
        "expected_business_fields": [
            "user_id",
            "device_id",
            "klink_status",
            "session_status",
        ],
        "role": "Weapon 账号会话 / Klink 状态 source，偏账号-设备链路上下文",
    },
    "rcp_event_detail": {
        "chain_section": "strategy_risk_signal",
        "expected_business_fields": [
            "event_id",
            "event_type",
            "hit_policy",
            "event_time",
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
        "role": "事件归因上下文，不单独定性风险",
    },
    "rcp_event_feature_list": {
        "chain_section": "strategy_risk_signal",
        "expected_business_fields": [
            "event_id",
            "event_type",
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
            "feature_presence",
            "feature_list_boundary",
        ],
        "role": "策略事件特征行安全投影；原始类 TAB 行级保留，不把策略命中当核心特征",
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
    "operation_device": {"operation_device", "operationDevice", "actionDeviceId", "operateDeviceId"},
    "security_action_type": {"security_action_type", "securityActionType", "actionType", "operationType", "credential_secret_event_id"},
    "related_count": {"related_count", "relatedCount", "count", "total", "recordCount"},
    "feature_value": {"feature_value", "featureValue", "value", "fieldValue"},
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
    "request_path": {"request_path", "requestPath", "apiPath", "path", "urlPath", "uri", "interfacePath"},
    "request_scene": {"request_scene", "requestScene", "scene", "sceneType", "bizScene"},
    "entry": {"entry", "entryType", "entryScene", "entrance", "entranceType", "sourceEntry"},
    "action_type": {"action_type", "actionType", "operationType", "opType", "behaviorType"},
    "action_object": {"action_object", "actionObject", "objectId", "targetId", "resourceId", "itemId"},
    "task_type": {"task_type", "taskType", "missionType", "activityTaskType"},
    "reward_type": {"reward_type", "rewardType", "awardType", "incentiveType"},
    "client_params": {"client_params", "clientParams", "clientInfo", "deviceInfo", "requestParams", "params"},
    "app_version": {"app_version", "appVersion", "appVer", "clientVersion"},
    "ip_or_network": {"ip_or_network", "ip", "clientIp", "requestIp", "network", "networkType"},
    "frontend_activity_signal": {"frontend_activity_signal", "frontendActivitySignal", "frontActivity", "frontendActivity"},
    "backend_action_signal": {"backend_action_signal", "backendActionSignal", "backendAction", "serverAction"},
    "time_delta_from_login_seconds": {"time_delta_from_login_seconds", "timeDeltaFromLogin", "loginActionDelta", "deltaFromLoginSeconds"},
    "time_delta_between_actions_seconds": {"time_delta_between_actions_seconds", "timeDeltaBetweenActions", "actionIntervalSeconds", "deltaBetweenActionsSeconds"},
    "feature_group": {"feature_group", "featureGroup", "featureGroupName"},
    "feature_key": {"feature_key", "featureKey"},
    "feature_name": {"feature_name", "featureName"},
    "feature_value": {"feature_value", "featureValue", "defaultFeatureValue", "value"},
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
    "request_path",
    "requestPath",
    "request_scene",
    "requestScene",
    "entry",
    "entryType",
    "entryScene",
    "action_type",
    "actionType",
    "action_object",
    "actionObject",
    "task_type",
    "taskType",
    "reward_type",
    "rewardType",
    "client_params",
    "clientParams",
    "clientInfo",
    "app_version",
    "appVersion",
    "ip_or_network",
    "requestIp",
    "networkType",
    "frontend_activity_signal",
    "frontendActivitySignal",
    "backend_action_signal",
    "backendActionSignal",
    "time_delta_from_login_seconds",
    "timeDeltaFromLogin",
    "time_delta_between_actions_seconds",
    "timeDeltaBetweenActions",
    "feature_group",
    "featureGroup",
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


def _source_contract_identity(item: SourcePlanItem) -> tuple[str, str, str]:
    action = str(item.action or "")
    if action == "weapon_inventory":
        return "weapon_android", "raw_data", "android"
    if action == "login_logs_search":
        return "infra_user_action_log", "login", "unknown"
    if action == "archives_user_analysis":
        return "archives_user_analysis", "user_analysis", "unknown"
    if action == "archives_user_profile":
        return "archives_user_profile", "profile", "unknown"
    if action == "rcp_event_feature_list":
        return "rcp_event_feature_list", "feature_list", "unknown"
    if action == "rcp_event_detail":
        return "rcp_event_detail", "event_detail", "unknown"
    if action == "rcp_fast_query_hbase":
        return "rcp_fast_query_hbase", "strategy", "unknown"
    return action or "unknown_source", action or "unknown", "unknown"


def _contract_body_candidate(value: Any) -> Any:
    if not isinstance(value, dict):
        return None
    for key in RAW_CONTRACT_BODY_KEYS:
        if key in value and value.get(key) not in (None, ""):
            return value.get(key)
    upstream = value.get("upstream")
    if isinstance(upstream, dict):
        body = _contract_body_candidate(upstream)
        if body is not None:
            return body
    source_result = value.get("source_result")
    if isinstance(source_result, dict):
        body = _contract_body_candidate(source_result)
        if body is not None:
            return body
    result = value.get("result")
    if isinstance(result, (dict, list)):
        return result
    data = value.get("data")
    if isinstance(data, (dict, list)):
        return data
    return None


def _raw_body_status(row: dict[str, Any], raw_body: Any) -> str:
    status = str(row.get("source_status") or row.get("category") or "").lower()
    if status in {"timeout"} or row.get("timed_out") is True or row.get("timeout") is True:
        return "timeout"
    if status in {"blocked", "auth_failed", "parse_error", "missing_required_fields", "failed"}:
        return "blocked"
    if raw_body is None:
        return "projected_only"
    if row.get("body_truncated") is True or str(row.get("raw_body_handling") or "").lower() in {"capped", "json_array_capped"}:
        return "partial_nested_raw"
    if isinstance(raw_body, (dict, list)):
        return "full_nested_raw"
    return "partial_nested_raw"


def _raw_body_format(raw_body: Any) -> str:
    if isinstance(raw_body, dict):
        return "json_object"
    if isinstance(raw_body, list):
        return "json_array"
    if raw_body is None:
        return "not_available"
    return "scalar_or_text"


def _field_count(value: Any) -> int:
    if isinstance(value, dict):
        return sum(_field_count(child) for child in value.values()) or len(value)
    if isinstance(value, list):
        return sum(_field_count(child) for child in value)
    return 1 if value not in (None, "") else 0


def build_l1_raw_observation_contract(
    *,
    case_id: str,
    source_plan: list[SourcePlanItem],
    batch_result: dict[str, Any],
    sampled_entities: list[str],
) -> dict[str, Any]:
    plan_by_id = {item.source_id: item for item in source_plan}
    rows_by_id = _rows_by_source_id_from_batch(batch_result)
    users: dict[str, dict[str, Any]] = {
        str(user_id): {
            "user_id": str(user_id),
            "sample_role": "risk",
            "sources": {},
        }
        for user_id in sampled_entities
    }
    gap_rows: list[dict[str, Any]] = []

    for source_id, row in sorted(rows_by_id.items()):
        item = plan_by_id.get(source_id)
        params = item.params if item else {}
        user_id = str(params.get("user_id") or row.get("user_id") or "")
        if not user_id:
            match = re.search(r"entity_(\d+)", source_id)
            if match:
                index = int(match.group(1)) - 1
                if 0 <= index < len(sampled_entities):
                    user_id = str(sampled_entities[index])
        if not user_id:
            user_id = "unknown_user"
            users.setdefault(user_id, {"user_id": user_id, "sample_role": "unknown", "sources": {}})

        source_name, layer, platform = _source_contract_identity(item) if item else (str(row.get("action") or "unknown_source"), str(row.get("action") or "unknown"), "unknown")
        raw_body = _contract_body_candidate(row)
        sanitized_body = sanitize_for_raw_observation_contract(raw_body) if raw_body is not None else None
        raw_status = _raw_body_status(row, sanitized_body)
        action_payload = {
            "source_name": source_name,
            "canonical_source_hint": source_name,
            "platform": platform,
            "action": item.action if item else row.get("action"),
            "layer": layer,
            "source_status": row.get("source_status") or row.get("category") or raw_status,
            "raw_body_status": raw_status,
            "observed_at": _iso_now(),
            "raw_body_format": _raw_body_format(sanitized_body),
            "raw_body": sanitized_body,
            "redaction": {
                "credential_secrets_removed": True,
                "risk_entity_identifiers_retained_for_internal_review": True,
            },
            "field_count_hint": {
                "raw_input_field_count": _field_count(sanitized_body),
                "commonality_eligible_field_count": None,
            },
            "source_quality": {
                "body_present": bool(row.get("body_present")),
                "body_truncated": bool(row.get("body_truncated")),
                "raw_body_handling": row.get("raw_body_handling"),
                "http_status": row.get("http_status"),
                "limitations": [] if raw_status == "full_nested_raw" else [raw_status],
            },
        }
        users.setdefault(user_id, {"user_id": user_id, "sample_role": "risk", "sources": {}})
        source_bucket = users[user_id]["sources"].setdefault(source_name, {})
        unique_layer = layer
        suffix = 2
        while unique_layer in source_bucket:
            unique_layer = f"{layer}_{suffix}"
            suffix += 1
        source_bucket[unique_layer] = action_payload
        if raw_status != "full_nested_raw":
            gap_rows.append({
                "user_id": user_id,
                "source_id": source_id,
                "source": source_name,
                "layer": unique_layer,
                "raw_body_status": raw_status,
                "source_status": action_payload["source_status"],
                "reason": "raw body unavailable or partial in browser-backed passthrough envelope",
            })

    return {
        "schema_version": "e2e_risk_observation_input_contract_v0_1",
        "case_id": case_id,
        "generated_at": _iso_now(),
        "export_mode": "source_observation_snapshot",
        "credential_secret_policy": {
            "cookie": "removed",
            "token": "removed",
            "session": "removed",
            "authorization": "removed",
            "password": "removed",
            "headers": "credential_headers_removed",
        },
        "source_registry_version": "registered_actions_current",
        "field_alignment_registry_version": "realtime_offline_field_alignment_v0_1",
        "users": [users[key] for key in sorted(users)],
        "raw_body_gap_report": gap_rows,
    }


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
                "strategy_event_feature_rows": safe_observation.get("strategy_event_feature_rows", []),
                "device_detail_rows": safe_observation.get("device_detail_rows", []),
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
        for item in normalize_mapping_or_list(result.get("source_results")):
            if not isinstance(item, dict):
                continue
            transport = item.get("transport") if isinstance(item.get("transport"), dict) else {}
            row = dict(transport or item)
            source_id = str(item.get("source_id") or row.get("source_id") or f"unknown_{len(merged_source_results) + 1}")
            row.setdefault("source_id", source_id)
            merged_source_results[source_id] = {
                "source_id": source_id,
                "action": item.get("action") or row.get("action"),
                "transport": row,
                "source_result": item,
            }
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


def validate_register_new_snapshot_rounds_payload(payload: dict[str, Any]) -> dict[str, Any]:
    scene_hints = [
        str(item)
        for item in payload.get("scene_hint", []) or []
        if str(item).strip()
    ]
    register_new_required = any("REGISTER_NEW" in item or "注册攻击" in item for item in scene_hints)
    if not register_new_required:
        return {"required": False, "valid": True, "errors": []}
    errors: list[str] = []
    for round_item in payload.get("rounds", []) or []:
        round_id = round_item.get("round_id")
        source_overrides = round_item.get("source_overrides")
        snapshot_override = (
            source_overrides.get("rcp_snapshot", {})
            if isinstance(source_overrides, dict) and isinstance(source_overrides.get("rcp_snapshot"), dict)
            else {}
        )
        if snapshot_override.get("enabled") is not True:
            errors.append(f"round_{round_id}_rcp_snapshot_enabled_required_for_register_new")
    return {"required": True, "valid": not errors, "errors": errors}


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


WEAPON_DEVICE_DETAIL_ACTIONS = {
    "weapon_device_info",
    "weapon_device_app_list",
    "weapon_device_location_info",
    "weapon_user_klink_status",
}


def _weapon_device_detail_source_items(
    *,
    round_id: int,
    index: int,
    entity: str,
    seed_entity_type: str,
    window_start_ms: int,
    window_end_ms: int,
) -> list[SourcePlanItem]:
    if seed_entity_type != "device_id":
        return []
    return [
        SourcePlanItem(
            source_id=_batch_source_id(round_id, index, "weapon_device_info"),
            action="weapon_device_info",
            execution_group="independent_parallel",
            depends_on=[],
            timeout_class="standard_readonly",
            failure_policy="non_blocking_partial",
            source_priority="P0",
            expected_observation="direct Weapon device detail fields for device_detail_table; inventory remains graph/relation context",
            params={"device_id": entity, "mode": "device_detail_primary"},
            timeout_ms=30_000,
            required_fields=["device_id"],
            window_policy="current_device_detail_window",
            window_start_ms=window_start_ms,
            window_end_ms=window_end_ms,
        ),
        SourcePlanItem(
            source_id=_batch_source_id(round_id, index, "weapon_device_app_list"),
            action="weapon_device_app_list",
            execution_group="independent_parallel",
            depends_on=[_batch_source_id(round_id, index, "weapon_device_info")],
            timeout_class="standard_readonly",
            failure_policy="non_blocking_partial",
            source_priority="P1",
            expected_observation="Weapon installed app / app environment fields for device_detail_table",
            params={"device_id": entity, "mode": "device_app_environment"},
            timeout_ms=30_000,
            required_fields=["device_id"],
            window_policy="current_device_app_environment_window",
            window_start_ms=window_start_ms,
            window_end_ms=window_end_ms,
        ),
    ]


def build_sample_round_source_plan(
    round_id: int,
    sampled_entities: list[str],
    *,
    window_start_ms: int,
    window_end_ms: int,
    disabled_actions: set[str] | None = None,
    source_overrides: dict[str, Any] | None = None,
) -> list[SourcePlanItem]:
    disabled_actions = disabled_actions or set()
    source_overrides = source_overrides or {}
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
        seed_entity_type = _infer_seed_entity_type(entity)
        common_user_params = {"user_id": entity}
        weapon_params = {"device_id": entity} if seed_entity_type == "device_id" else {"user_id": entity}
        weapon_required_fields = ["device_id"] if seed_entity_type == "device_id" else ["user_id"]
        weapon_expected_observation = (
            "device graphData/user relation summary; direct detail comes from weapon_device_info"
            if seed_entity_type == "device_id"
            else "user-device graphData/riskData summary for entity_resolution_first"
        )
        items.extend(
            _weapon_device_detail_source_items(
                round_id=round_id,
                index=index,
                entity=entity,
                seed_entity_type=seed_entity_type,
                window_start_ms=window_start_ms,
                window_end_ms=window_end_ms,
            )
        )
        if seed_entity_type == "device_id":
            items.append(
                SourcePlanItem(
                    source_id=_batch_source_id(round_id, index, "weapon"),
                    action="weapon_inventory",
                    execution_group="independent_parallel",
                    depends_on=[],
                    timeout_class="standard_readonly",
                    failure_policy="non_blocking_partial",
                    source_priority="P0",
                    expected_observation=weapon_expected_observation,
                    params={
                        **weapon_params,
                        "mode": "batch_user_device_graph_summary",
                        "include_risk_data": True,
                        "max_device_ids": 10,
                    },
                    timeout_ms=30_000,
                    required_fields=weapon_required_fields,
                    window_policy="current_user_device_graph_window",
                    window_start_ms=window_start_ms,
                    window_end_ms=window_end_ms,
                )
            )
            continue
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
                    expected_observation=weapon_expected_observation,
                    params={
                        **weapon_params,
                        "mode": "batch_user_device_graph_summary",
                        "include_risk_data": True,
                        "max_device_ids": 10,
                    },
                    timeout_ms=30_000,
                    required_fields=weapon_required_fields,
                    window_policy="current_user_device_graph_window",
                    window_start_ms=window_start_ms,
                    window_end_ms=window_end_ms,
                ),
                SourcePlanItem(
                    source_id=_batch_source_id(round_id, index, "user_analysis"),
                    action="archives_user_analysis",
                    execution_group="auth_sensitive_serial",
                    depends_on=[_batch_source_id(round_id, index, "archives_profile")],
                    timeout_class="large_response",
                    failure_policy="non_blocking_partial",
                    source_priority="P0",
                    expected_observation=(
                        "bounded user behavior/action summary fields for user_behavior_summary_detail_table; "
                        "profile/login/content gaps remain missing evidence, not counter evidence"
                    ),
                    params={
                        **common_user_params,
                        "beginTime": window_start_ms,
                        "endTime": window_end_ms,
                        "pageIndex": 1,
                        "pageSize": 30,
                    },
                    timeout_ms=45_000,
                    required_fields=["user_id", "beginTime", "endTime"],
                    window_policy="archives_scene_window_not_constrained_by_login_logs_7d",
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
                        "eventTypeCodes": str(source_overrides.get("rcp_fast_query_hbase", {}).get("eventTypeCodes", "")) if isinstance(source_overrides.get("rcp_fast_query_hbase"), dict) else "",
                        "limit": 100,
                        **(
                            source_overrides.get("rcp_fast_query_hbase", {})
                            if isinstance(source_overrides.get("rcp_fast_query_hbase"), dict)
                            else {}
                        ),
                    },
                    timeout_ms=30_000,
                    required_fields=["source_id", "startTime", "endTime"],
                    window_policy="strategy_hit_discovery_by_user_source_id_recent_window",
                    window_start_ms=window_start_ms,
                    window_end_ms=window_end_ms,
                ),
            ]
        )
        rcp_snapshot_override = (
            source_overrides.get("rcp_snapshot", {})
            if isinstance(source_overrides.get("rcp_snapshot"), dict)
            else {}
        )
        if rcp_snapshot_override.get("enabled") is True:
            snapshot_params = {
                "source_id": entity,
                "startTime": window_start_ms,
                "endTime": window_end_ms,
                "eventType": str(rcp_snapshot_override.get("eventType") or "REGISTER_NEW"),
                "eventTypeCodes": str(rcp_snapshot_override.get("eventTypeCodes") or rcp_snapshot_override.get("eventType") or "REGISTER_NEW"),
                "pageIndex": int(rcp_snapshot_override.get("pageIndex") or 1),
                "pageSize": int(rcp_snapshot_override.get("pageSize") or 20),
                **{key: value for key, value in rcp_snapshot_override.items() if key != "enabled"},
            }
            items.append(
                SourcePlanItem(
                    source_id=_batch_source_id(round_id, index, "rcp_snapshot"),
                    action="rcp_snapshot",
                    execution_group="independent_parallel",
                    depends_on=[],
                    timeout_class="standard_readonly",
                    failure_policy="non_blocking_partial",
                    source_priority="P1-controlled-event-discovery",
                    expected_observation="RCP eventList discovery for explicit REGISTER_NEW event anchors before feature-list L2",
                    params=snapshot_params,
                    timeout_ms=30_000,
                    required_fields=["eventType", "startTime", "endTime"],
                    window_policy="strategy_event_discovery_by_event_type_recent_window",
                    window_start_ms=window_start_ms,
                    window_end_ms=window_end_ms,
                )
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
        ({"archives_comment_search", "archives_private_message_search", "archives_related_users", "archives_fans_list", "archives_follow_list"}, "social_action_anchor"),
        ({"rcp_fast_query_hbase"}, "strategy_hit"),
        ({"rcp_snapshot"}, "strategy_hit_detail"),
        ({"rcp_event_detail", "rcp_event_feature_list"}, "strategy_event_request_detail"),
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
        "archives_comment_search": {"photo_id", "comment_id", "comment_text", "action_time", "target_user_id", "relation_type"},
        "archives_private_message_search": {"message_id", "message_text", "sender", "receiver", "target_user_id", "action_time", "relation_type"},
        "archives_related_users": {"related_user_id", "relation_type", "shared_device", "related_count"},
        "archives_fans_list": {"target_user_id", "relation_type", "action_time"},
        "archives_follow_list": {"target_user_id", "relation_type", "action_time"},
        "rcp_fast_query_hbase": {"event_type", "event_time", "policy_code", "hit_policy", "risk_decision"},
        "rcp_snapshot": {"event_type", "event_time", "policy_code", "hit_policy", "risk_decision"},
        "rcp_event_detail": {"request_path", "request_scene", "entry", "action_type", "action_object", "task_type", "reward_type", "client_params", "app_version", "ua", "device_id", "ip_or_network", "frontend_activity_signal", "backend_action_signal", "time_delta_from_login_seconds", "time_delta_between_actions_seconds"},
        "rcp_event_feature_list": {"request_path", "request_scene", "action_type", "action_object", "task_type", "reward_type", "client_params", "frontend_activity_signal", "backend_action_signal", "feature_group"},
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


def build_batch_candidate_action_groups(coverage_status: str) -> list[dict[str, Any]]:
    return [
        {
            "priority": "P0",
            "candidate_action_group": "prioritize_validation",
            "candidate_signal": "multi_source_device_login_content_behavior_combination",
            "target_cluster": "main_cluster_when_coverage_validated",
            "reason": "Only valid as a candidate after realtime field commonality shows multi-source consistency.",
            "coverage_estimate": coverage_status,
            "validation_status": "pending_l4_l5_validation",
            "false_positive_risk": "medium_until_counter_samples_checked",
            "next_validation_step": "collect_missing_fields_and_prepare_authorized_validation_plan",
            "usage_boundary": "candidate_action_only_not_strategy_recommendation_not_auto_disposition",
            "required_validation_data": ["full_batch_coverage", "normal_counter_samples", "source_quality"],
            "not_recommended_usage": "Do not use strategy hit or same-device alone.",
        },
        {
            "priority": "P1",
            "candidate_action_group": "combine_before_validation",
            "candidate_signal": "same_device_or_same_login_window_signal",
            "target_cluster": "candidate_secondary_clusters",
            "reason": "Useful as a weighted or review feature, not standalone disposition.",
            "coverage_estimate": coverage_status,
            "validation_status": "pending_l4_l5_validation",
            "false_positive_risk": "medium_high_if_standalone",
            "next_validation_step": "combine_with_cross_source_fields_before_any_validation",
            "usage_boundary": "candidate_action_only_not_strategy_recommendation_not_auto_disposition",
            "required_validation_data": ["cross_source_confirmation"],
            "not_recommended_usage": "Do not block from this signal alone.",
        },
        {
            "priority": "P2",
            "candidate_action_group": "observe_or_expand_only",
            "candidate_signal": "single_strategy_hit_or_single_frontend_similarity",
            "target_cluster": "weak_signal_pool",
            "reason": "Weak lead for monitoring and further discovery.",
            "coverage_estimate": "not_evaluable_from_current_rounds",
            "validation_status": "not_evaluable_at_l3",
            "false_positive_risk": "high_if_used_for_control",
            "next_validation_step": "expand_source_fields_or_keep_as_observation",
            "usage_boundary": "candidate_action_only_not_strategy_recommendation_not_auto_disposition",
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
    "weapon_device_info": ["device_domain"],
    "weapon_device_app_list": ["device_domain"],
    "weapon_device_location_info": ["device_domain", "network_domain"],
    "weapon_user_klink_status": ["account_domain", "device_domain", "behavior_domain"],
    "login_logs_search": ["account_domain", "network_domain", "behavior_domain"],
    "archives_photo_search": ["content_domain", "behavior_domain"],
    "archives_gallery_photo_list": ["content_domain", "behavior_domain"],
    "archives_photo_profile": ["content_domain", "network_domain", "behavior_domain"],
    "archives_photo_meta": ["content_domain", "device_domain", "network_domain"],
    "archives_comment_search": ["content_domain", "social_domain"],
    "archives_private_message_search": ["social_domain"],
    "archives_related_users": ["social_domain", "device_domain"],
    "archives_fans_list": ["social_domain"],
    "archives_follow_list": ["social_domain"],
    "archives_negative_report": ["feedback_domain"],
    "archives_user_report_search": ["feedback_domain", "content_domain"],
    "archives_punish_status": ["enforcement_domain", "content_domain"],
    "rcp_fast_query_hbase": ["strategy_domain"],
    "rcp_snapshot": ["strategy_domain"],
    "rcp_event_detail": ["strategy_domain", "behavior_domain"],
    "rcp_event_feature_list": ["strategy_domain", "behavior_domain"],
    "rcp_event_tree_or_decision": ["strategy_domain"],
    "track_analysis_check_data_ready": ["behavior_domain", "device_domain"],
}


FIRST_HOP_ACTIONS = {
    "archives_user_profile",
    "archives_review_logs",
    "weapon_inventory",
    "weapon_user_klink_status",
    "login_logs_search",
    "archives_photo_search",
    "rcp_fast_query_hbase",
}


ANCHOR_TRIGGERED_ACTIONS = {
    "archives_gallery_photo_list",
    "archives_photo_profile",
    "archives_photo_meta",
    "track_analysis_check_data_ready",
    "weapon_device_info",
    "weapon_device_app_list",
    "weapon_device_location_info",
    "rcp_event_tree_or_decision",
    "rcp_event_detail",
    "rcp_event_feature_list",
}


def _infer_seed_entity_type(entity: str) -> str:
    text = str(entity).strip()
    lowered = text.lower()
    if lowered.startswith(("web_", "did_", "device_", "android_", "ios_")):
        return "device_id"
    if re.fullmatch(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}", text):
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
        "rcp_event_detail": ["event_id", "request_path", "action_object", "client_params", "time_delta_from_login_seconds"],
        "rcp_event_feature_list": ["event_id", "feature_group", "request_path", "action_object"],
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
STRATEGY_EVENT_REQUEST_DETAIL_ACTIONS = {"rcp_event_detail", "rcp_event_feature_list", "rcp_fast_query_hbase"}
STRATEGY_EVENT_ENTRY_LABEL_FIELDS = {"policy_code", "event_type", "risk_decision"}
STRATEGY_EVENT_FEATURE_ROW_ACTIONS = {"rcp_event_feature_list"}
STRATEGY_EVENT_ORIGINAL_FEATURE_TAB = "原始类"
STRATEGY_EVENT_FEATURE_ROW_REQUIRED_FIELDS = [
    "sample_id",
    "entity_id",
    "event_id",
    "event_type",
    "source_id",
    "source_name",
    "feature_tab",
    "feature_key",
    "feature_name",
    "feature_type",
    "feature_value_or_safe_ref",
    "value_present",
    "value_comparable",
    "source_quality",
    "evidence_source",
]
STRATEGY_EVENT_REQUEST_DETAIL_FIELDS = [
    "user_id",
    "event_id",
    "event_type",
    "policy_code",
    "risk_decision",
    "event_time",
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
]
STRATEGY_EVENT_REQUEST_DETAIL_CORE_FIELDS = {
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
}

DEVICE_DETAIL_SOURCE_TYPES = {
    "设备基础信息",
    "设备风险标签",
    "设备使用画像",
    "安装列表 / 应用环境",
    "账号-设备关系",
    "行为-设备一致性",
    "未知",
}

DEVICE_DETAIL_TABLE_REQUIRED_FIELDS = [
    "sample_id",
    "entity_id",
    "user_id",
    "device_id",
    "device_safe_ref",
    "source_id",
    "source_name",
    "device_source_type",
    "device_field_key",
    "device_field_name",
    "device_field_value_or_safe_ref",
    "device_field_type",
    "value_present",
    "value_comparable",
    "comparable_type",
    "source_quality",
    "evidence_source",
    "event_time",
    "query_time",
    "device_role",
    "sensitive_value_policy",
]

STANDARD_DETAIL_TABLE_REQUIRED_FIELDS = [
    "sample_id",
    "entity_id",
    "entity_type",
    "round_id",
    "source_id",
    "source_name",
    "source_domain",
    "action",
    "detail_table",
    "field_name",
    "field_value_or_safe_ref",
    "field_family",
    "value_present",
    "value_comparable",
    "comparable_type",
    "source_quality",
    "evidence_source",
    "extracted_from_observation_id",
]

RAW_DETAIL_FLAT_TABLE_REQUIRED_FIELDS = [
    "observation_id",
    "parent_observation_id",
    "layer",
    "anchor_lineage",
    "source_name",
    "source_domain",
    "source_shape",
    "entity_type",
    "entity_id",
    "record_index",
    "record_time",
    "field_path",
    "field_name",
    "field_value_raw_or_ref",
    "field_value_type",
    "value_handling",
    "redaction_reason",
    "field_family",
    "field_family_confidence",
    "value_comparable",
    "comparable_reason",
    "source_quality",
    "missing_or_partial_reason",
    "extraction_quality",
    "is_unknown_field",
    "needs_field_dictionary_review",
]

SOURCE_ACTION_DETAIL_TABLES = {
    "login_logs_search": "login_detail_table",
    "archives_user_profile": "account_detail_table",
    "archives_user_analysis": "user_behavior_summary_detail_table",
    "archives_gallery_photo_list": "content_detail_table",
    "archives_photo_search": "content_detail_table",
    "archives_photo_profile": "content_detail_table",
    "archives_photo_meta": "content_detail_table",
    "archives_photo_report_aggregate": "content_detail_table",
    "archives_comment_search": "social_detail_table",
    "archives_livestream_comment_detail": "social_detail_table",
    "archives_private_message_search": "social_detail_table",
    "archives_related_users": "social_detail_table",
    "archives_fans_list": "social_detail_table",
    "archives_follow_list": "social_detail_table",
    "archives_user_report_search": "feedback_detail_table",
    "archives_negative_report": "feedback_detail_table",
    "archives_review_logs": "enforcement_detail_table",
    "archives_punish_status": "enforcement_detail_table",
}

MULTI_ROW_EVENT_ACTIONS = {
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
}

SINGLE_OBJECT_WIDE_FIELD_ACTIONS = {
    "weapon_inventory",
    "weapon_device_info",
    "weapon_device_app_list",
    "weapon_device_location_info",
    "weapon_user_klink_status",
    "rcp_event_feature_list",
}

DETAIL_TABLE_SOURCE_DOMAINS = {
    "login_detail_table": "behavior_domain",
    "account_detail_table": "account_domain",
    "user_behavior_summary_detail_table": "behavior_domain",
    "content_detail_table": "content_domain",
    "social_detail_table": "social_domain",
    "feedback_detail_table": "feedback_domain",
    "enforcement_detail_table": "enforcement_domain",
}

SOURCE_ROLE_BY_ACTION = {
    "rcp_snapshot": "anchor_discovery_source",
    "rcp_fast_query_hbase": "anchor_discovery_source",
    "rcp_event_detail": "auxiliary_detail_source",
    "rcp_event_feature_list": "dynamic_event_table",
    "weapon_inventory": "summary_or_inventory_source",
    "weapon_device_info": "primary_detail_source",
    "weapon_device_app_list": "auxiliary_detail_source",
    "weapon_device_location_info": "auxiliary_detail_source",
    "weapon_user_klink_status": "auxiliary_detail_source",
    "login_logs_search": "primary_detail_source",
    "archives_user_profile": "primary_detail_source",
    "archives_user_analysis": "primary_detail_source",
    "archives_photo_search": "primary_detail_source",
    "archives_gallery_photo_list": "auxiliary_detail_source",
    "archives_photo_profile": "auxiliary_detail_source",
    "archives_photo_meta": "auxiliary_detail_source",
    "archives_comment_search": "primary_detail_source",
    "archives_private_message_search": "primary_detail_source",
    "archives_related_users": "anchor_discovery_source",
    "archives_fans_list": "auxiliary_detail_source",
    "archives_follow_list": "auxiliary_detail_source",
    "archives_user_report_search": "primary_detail_source",
    "archives_negative_report": "auxiliary_detail_source",
    "archives_review_logs": "primary_detail_source",
    "archives_punish_status": "primary_detail_source",
    "track_analysis_check_data_ready": "summary_or_inventory_source",
}

FIELD_FAMILY_BY_CANONICAL_FIELD = {
    "login_time": "login_time_family",
    "login_type": "login_method_family",
    "login_source": "login_method_family",
    "login_result": "login_result_family",
    "success_failure": "login_result_family",
    "success_failure_sequence": "login_result_family",
    "token_oauth_scan": "login_result_family",
    "kickout": "login_result_family",
    "device_id": "login_device_family",
    "login_device": "login_device_family",
    "candidate_device_id": "login_device_family",
    "device_model": "login_device_family",
    "os": "login_client_family",
    "app_version": "login_client_family",
    "ua": "login_client_family",
    "ip": "login_network_family",
    "ip_ua": "login_network_family",
    "ip_or_network": "login_network_family",
    "province": "login_network_family",
    "city": "login_network_family",
    "region": "login_network_family",
    "asn": "login_network_family",
    "browser_fingerprint": "login_client_family",
    "time_delta_between_login": "login_sequence_family",
    "time_delta_to_action": "login_action_alignment_family",
    "event_time": "login_action_alignment_family",
    "operation_time": "login_action_alignment_family",
    "action_time": "login_action_alignment_family",
    "operation_device": "login_action_alignment_family",
    "security_action_type": "login_action_alignment_family",
    "frontend_activity_signal": "login_action_alignment_family",
    "backend_action_signal": "login_action_alignment_family",
    "frontend_backend_consistency": "login_action_alignment_family",
    "account_age": "account_age_family",
    "register_time": "account_age_family",
    "account_status": "account_status_family",
    "protection_status": "protection_punish_family",
    "protection_state": "protection_punish_family",
    "punish_status": "protection_punish_family",
    "punish_or_tag_summary": "protection_punish_family",
    "profile_change_time": "profile_change_family",
    "profile_change": "profile_change_family",
    "nickname_change": "profile_change_family",
    "avatar_change": "profile_change_family",
    "bio_change": "profile_change_family",
    "follow_count": "social_asset_family",
    "fan_count": "social_asset_family",
    "content_publish_count": "behavior_count_family",
    "active_days": "behavior_count_family",
    "recent_behavior_counts": "behavior_count_family",
    "blacklist": "protection_punish_family",
    "report": "protection_punish_family",
    "ban": "protection_punish_family",
    "limit": "protection_punish_family",
    "profile_completeness": "account_maintenance_family",
    "related_count": "behavior_count_family",
    "feature_value": "account_status_family",
    "photo_id": "content_publish_family",
    "content_id": "content_publish_family",
    "item_id": "content_publish_family",
    "publish_time": "content_publish_family",
    "publish_device": "content_publish_family",
    "publish_ip": "content_publish_family",
    "publish_ip_ua": "content_publish_family",
    "publish_source": "content_publish_family",
    "content_type": "content_media_family",
    "caption": "content_template_family",
    "title": "content_template_family",
    "text": "content_template_family",
    "ocr": "content_media_family",
    "asr": "content_media_family",
    "image_tags": "content_media_family",
    "audit_reason": "content_audit_family",
    "audit_or_strategy_reason": "content_audit_family",
    "strategy_reason": "content_audit_family",
    "like_count": "content_engagement_family",
    "comment_count": "content_engagement_family",
    "share_count": "content_engagement_family",
    "play_count": "content_engagement_family",
    "delete_status": "content_audit_family",
    "downrank_status": "content_audit_family",
    "content_status": "content_audit_family",
    "comment_id": "social_text_family",
    "message_id": "social_text_family",
    "message_anchor": "social_text_family",
    "target_user_id": "social_target_family",
    "relation_type": "social_relation_family",
    "message_text": "social_text_family",
    "comment_text": "social_text_family",
    "action_time": "social_action_sequence_family",
    "operation_time": "social_action_sequence_family",
    "sender": "social_relation_family",
    "receiver": "social_relation_family",
    "follow": "social_action_sequence_family",
    "unfollow": "social_action_sequence_family",
    "same_target": "social_target_family",
    "same_wording": "social_text_family",
    "same_path": "social_path_family",
    "reply_chain": "social_path_family",
    "report_id": "feedback_object_family",
    "report_time": "feedback_type_family",
    "report_type": "feedback_type_family",
    "feedback_object": "feedback_object_family",
    "feedback_signal": "feedback_type_family",
    "appeal_time": "appeal_family",
    "appeal_result": "appeal_family",
    "review_id": "review_result_family",
    "review_result": "review_result_family",
    "punish_id": "enforcement_type_family",
    "punish_type": "enforcement_type_family",
    "enforcement_action": "enforcement_type_family",
    "enforcement_time": "enforcement_timing_family",
    "policy_reason": "policy_reason_family",
    "review_scene": "review_result_family",
    "post_enforcement_action": "post_enforcement_migration_family",
}

FIELD_FAMILIES_BY_DETAIL_TABLE = {
    "login_detail_table": {
        "login_time_family",
        "login_method_family",
        "login_result_family",
        "login_device_family",
        "login_network_family",
        "login_client_family",
        "login_sequence_family",
        "login_action_alignment_family",
    },
    "account_detail_table": {
        "account_age_family",
        "account_status_family",
        "profile_change_family",
        "social_asset_family",
        "protection_punish_family",
        "account_maintenance_family",
    },
    "user_behavior_summary_detail_table": {
        "behavior_count_family",
        "account_maintenance_family",
        "profile_change_family",
        "protection_punish_family",
    },
    "content_detail_table": {
        "content_publish_family",
        "content_template_family",
        "content_media_family",
        "content_audit_family",
        "content_engagement_family",
    },
    "social_detail_table": {
        "social_relation_family",
        "social_text_family",
        "social_target_family",
        "social_path_family",
        "social_action_sequence_family",
    },
    "feedback_detail_table": {
        "feedback_type_family",
        "feedback_object_family",
        "appeal_family",
    },
    "enforcement_detail_table": {
        "review_result_family",
        "enforcement_type_family",
        "enforcement_timing_family",
        "policy_reason_family",
        "post_enforcement_migration_family",
    },
}

DETAIL_TABLE_FEATURE_NAMES = {
    "login_detail_table": "login_field_commonality_candidate",
    "account_detail_table": "account_profile_field_commonality_candidate",
    "user_behavior_summary_detail_table": "user_behavior_summary_field_commonality_candidate",
    "content_detail_table": "content_field_commonality_candidate",
    "social_detail_table": "social_field_commonality_candidate",
    "feedback_detail_table": "feedback_field_commonality_candidate",
    "enforcement_detail_table": "enforcement_field_commonality_candidate",
}

DEVICE_ID_ONLY_FIELDS = {"device_id", "candidate_device_id", "login_device_id", "backend_action_device_id", "frontend_active_device_id"}
DEVICE_CONTEXT_ONLY_FIELDS = {
    "user_id", "userid", "clientip", "client_ip", "sourceip", "sourceipv6", "ipv6",
    "serverip", "appkey", "ksappid", "requesturi", "sourcetype", "timestamp",
    "sdkcollecttime", "sdkuploadtime", "servertime", "request_context", "requestcontext",
    "network_context", "networkcontext", "userlevel",
}
DEVICE_NON_DEVICE_SUBTREE_KEYS = {
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
    "cookies",
}
DEVICE_BASIC_FIELDS = {
    "phone_model", "phonemodel", "hwmodel", "model", "os_version", "osversion", "system_version",
    "systemversion", "app_version", "appversion", "versionname", "device_platform", "platform",
    "productname", "kernosproductversion", "kernelversion", "resolution", "sdkversion",
    "devicename", "devicename2", "kernhostname", "hardwaretype", "hwmachine", "hwproduct",
    "hwtarget", "devicemodel", "buildproduct", "buildboard", "brand", "hardware", "cpumodel",
    "hwncpu", "hwlogicalcpu", "hwactivecpu", "hwavailcpu", "hwphysicalcpu",
    "hwphysicalcpumax", "cpucorecount", "cpucores", "hwmemsize", "hwphysmem",
    "hwusermem", "systemmem", "totalmemory", "usedmemory", "diskspace",
    "totalstorage", "sdtotalstorage", "diskfree", "systemmemfree", "sdusedstorage",
    "usedstorage", "diskspaceused", "screensize", "dpi", "hwcpufamily", "hwcputype",
    "hwcpusubtype", "hwcpu64bitcapable", "hwpagesize", "hwl1dcachesize",
    "hwl1icachesize", "hwl2cachesize", "hwl2settings", "hwtbfrequency",
    "hwbyteorder", "hwcachelinesize", "hwvectorunit", "kernosrelease", "kernosversion",
    "kernostype", "kernelversion", "securitypatch", "buildfingerprint", "buildtags",
    "builddisplayrom", "apiLevel", "apilevel", "cpuabi", "cpuinfo",
    "device_hardware_model", "cpu_core_count", "memory_total", "storage_total",
    "storage_free", "screen_resolution", "device_name",
}
DEVICE_FRESHNESS_FIELDS = {
    "launch_count", "launchcount", "applaunchcount", "launchtimes1d", "launchtimes7d",
    "launchtimes30d", "launchtimes90d", "launchtimes180d", "boot_duration",
    "bootduration", "boot_duration_seconds", "kernwaketime", "kernboottime", "boottime",
    "first_seen_delta", "first_seen_time", "firstinstallationtimestamp", "appinstalltime",
    "appinstalltime2", "active_days", "device_age_days", "starttime", "starttime2",
    "startuptime", "startupdurationms", "runningdurationms", "processystemuptime",
    "procesSystemUptime", "bootcount", "backgroundcount",
}
DEVICE_LOW_LIFE_FIELDS = {
    "lock_screen_enabled", "lockscreenenabled", "lockscreenstatus", "lockscreentime",
    "devicelocked", "sim_present", "simpresent", "simstatus", "ishassimcard",
    "charging_pattern", "chargingpattern", "battery", "batterytemperature", "low_life_signal",
}
DEVICE_AUTOMATION_FIELDS = {
    "automation_service_detected", "automationservicedetected", "accessibilityservicelist",
    "installaccessibility", "accessibilitysvc", "script_risk", "scriptrisk", "automation_signal",
    "abnormal_client_signal", "pluginversion", "enabledaccessibilityservices", "inputdevice",
    "touchEvent", "touchevent", "autoflip", "creatorreplaced", "appcomponentfactory",
}
DEVICE_MODIFICATION_FIELDS = {
    "device_reset_signal", "deviceresetsignal", "resettime", "resettimev2ms", "bootid",
    "boothashid", "root_or_hook_signal", "rootorhooksignal", "root_signal", "rootsignal",
    "hook_signal", "hooksignal", "frida_signal", "fridasignal", "frida", "xposed",
    "mountriskcheck", "mountriskpath", "emulator_signal", "emulatorsignal",
    "emulatorandcloudphone", "modification_signal", "rootcertificates", "inject",
    "jailbreakdetector", "jailbreak", "proxydetector", "proxyv2", "debug",
    "adbstatus", "doubleopen", "sandbox", "unidbg", "inodeseccomp", "systemfilehash",
    "apksignature", "apkpath", "apkprofile", "randompackgename", "drmid",
}
DEVICE_APP_ENV_FIELDS = {
    "installed_app_cluster", "installedappcluster", "risk_app", "riskapp", "tool_app",
    "toolapp", "app_environment_signal", "appenvironmentsignal", "installed_app_list",
    "installedapps", "applist", "appinfo", "packagename", "package_name", "versioncode",
    "system", "running", "uploadapplistcnt1d", "uploadapplistcnt7d", "uploadapplistcnt30d",
    "uploadapplistcnt90d", "uploadapplistcnt180d", "userappcnt", "kuaiShouCnt",
    "kuaishoucnt", "packageName", "randomPackgeName",
}
DEVICE_NETWORK_CONTEXT_FIELDS = {
    "clientip", "sourceip", "sourceipv6", "ipv6", "dns", "interfacedata",
    "otherinterfacedata", "network", "networktype", "networkoperator",
    "mobilenetworkcode", "mobilecountrycode", "oneipinfo", "bssid", "ssid",
    "ssiddata", "mac", "routermac", "networklink", "wgroupmac", "gateway",
    "broadcastaddress", "wifiip", "trafficinfo", "network_context", "networkcontext",
    "ip_or_network", "ipornetwork", "country", "province", "city", "district",
    "isp", "asn", "latitude", "longitude",
}
DEVICE_REQUEST_CONTEXT_FIELDS = {
    "requesturi", "sourcetype", "appkey", "ksappid", "serverip", "servertime",
    "timestamp", "sdkcollecttime", "sdkuploadtime", "asyncstatus", "product",
    "oneDataVersion", "onedataversion", "secretkeyversion", "weaponstatus",
    "weaponsignheader", "weapondecodeheader", "request_context", "requestcontext",
}
DEVICE_RISK_LABEL_FIELDS = {"risk_label", "risklabel", "labeldesc", "labelname", "risklevel", "risktime", "risk_label_group", "device_risk_label", "device_low_quality_label", "userrisk", "weaponrisk"}
DEVICE_RELATION_FIELDS = {"account_device_count", "device_account_count", "same_device_user_count", "device_pool_signal"}
DEVICE_BEHAVIOR_CONSISTENCY_FIELDS = {
    "login_device_id",
    "backend_action_device_id",
    "frontend_active_device_id",
    "behavior_device_consistency_signal",
}

DEVICE_FEATURE_CANDIDATE_EXCLUDED_FIELDS = DEVICE_ID_ONLY_FIELDS | DEVICE_CONTEXT_ONLY_FIELDS | {"frontend_activity_signal", "backend_action_signal"}
DEVICE_SECRET_FIELD_FRAGMENTS = (
    "cookie",
    "token",
    "session",
    "header",
    "authorization",
    "password",
    "credential",
)

DEVICE_HARD_SINGLE_FIELD_FRAGMENTS = (
    "frida",
    "xposed",
    "root",
    "hook",
    "mountrisk",
    "emulator",
    "rootcertificate",
)
DEVICE_HARD_RISK_LABEL_FRAGMENTS = (
    "frida",
    "xposed",
    "root",
    "hook",
    "mountrisk",
    "emulator",
    "cloudphone",
    "jailbreak",
    "改机",
    "模拟器",
    "云手机",
    "强风险",
    "高危",
)
DEVICE_WEAK_RISK_LABEL_FRAGMENTS = (
    "nosim",
    "launchless",
    "launchless10",
    "refresh",
    "lockscreen",
    "lowlife",
    "低启动",
    "无sim",
    "无锁屏",
)

DEVICE_WEAK_FIELD_FAMILIES = {"device_freshness", "low_life_device_environment"}
DEVICE_DEFAULT_LIKE_UNKNOWN_KEYS = {
    "code",
    "msg",
    "groupname",
    "grouplevel",
    "labeltype",
    "safestatus",
    "safe_status",
    "system",
    "running",
}
DEVICE_DEFAULT_LIKE_VALUES = {"0", "1", "success", "true", "false", "kuaishou", "较弱风险"}
DEVICE_UNKNOWN_CANDIDATE_LIMIT = 20


def _normalized_device_field_key(key: Any) -> str:
    return str(key or "").strip()


def _compact_device_field_key(key: Any) -> str:
    return "".join(ch for ch in str(key or "").lower() if ch.isalnum())


def _is_device_secret_field(row: dict[str, Any]) -> bool:
    text = " ".join(
        str(row.get(key) or "")
        for key in ("device_field_key", "device_field_name", "field_path")
    ).lower()
    normalized = "".join(ch for ch in text if ch.isalnum())
    return any(fragment in normalized for fragment in DEVICE_SECRET_FIELD_FRAGMENTS)


def _truthy_device_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    return text in {"true", "1", "yes", "y", "detected", "present", "enabled", "low", "short", "risk", "risky", "abnormal"}


def _device_value_safe_ref(value: Any) -> str | None:
    if value is None or value == "":
        return None
    if isinstance(value, (dict, list, tuple)):
        try:
            return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
        except (TypeError, ValueError):
            return str(value)
    return str(value)


def _device_value_tokens(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value if item not in {None, ""}]
    if isinstance(value, dict):
        return [str(key) for key in value.keys()] + [str(item) for item in value.values() if item not in {None, ""}]
    text = str(value)
    if not text:
        return []
    try:
        parsed = json.loads(text)
    except (TypeError, ValueError):
        parsed = None
    if isinstance(parsed, (list, tuple, set)):
        return [str(item) for item in parsed if item not in {None, ""}]
    if isinstance(parsed, dict):
        return [str(key) for key in parsed.keys()] + [str(item) for item in parsed.values() if item not in {None, ""}]
    return [text]


def _low_life_device_row_matches(key: str, value: Any) -> bool:
    compact_key = _compact_device_field_key(key)
    text = str(value).strip().lower()
    if compact_key in {"launchcount", "applaunchcount", "launchtimes1d"} and text.isdigit():
        return int(text) <= 3
    if compact_key in {"bootduration", "kernwaketime", "kernboottime"} and text.isdigit():
        return int(text) <= 600
    if compact_key in {"lockscreenenabled", "lockscreenstatus", "devicelocked", "simstatus", "simpresent", "ishassimcard"}:
        return text in {"false", "0", "no", "disabled", "-1"}
    if compact_key in {"weaponrisk", "userrisk", "risklabel", "devicerisklabel"}:
        compact_values = [
            "".join(ch for ch in token.lower() if ch.isalnum())
            for token in _device_value_tokens(value)
        ]
        return any(
            any(fragment in token for fragment in DEVICE_WEAK_RISK_LABEL_FRAGMENTS)
            for token in compact_values
        )
    return False


def _device_key_in_family(key: str, family_fields: set[str]) -> bool:
    compact_key = _compact_device_field_key(key)
    return key in family_fields or compact_key in family_fields


def _device_field_family(field_key: str) -> str:
    key = _normalized_device_field_key(field_key)
    compact_key = _compact_device_field_key(key)
    if compact_key in DEVICE_CONTEXT_ONLY_FIELDS:
        return "device_context_only"
    if key in DEVICE_BASIC_FIELDS or compact_key in DEVICE_BASIC_FIELDS:
        return "device_basic"
    if key in DEVICE_FRESHNESS_FIELDS or compact_key in DEVICE_FRESHNESS_FIELDS:
        return "device_freshness"
    if key in DEVICE_LOW_LIFE_FIELDS or compact_key in DEVICE_LOW_LIFE_FIELDS:
        return "low_life_device_environment"
    if key in DEVICE_AUTOMATION_FIELDS or compact_key in DEVICE_AUTOMATION_FIELDS:
        return "automation_or_script"
    if key in DEVICE_MODIFICATION_FIELDS or compact_key in DEVICE_MODIFICATION_FIELDS:
        return "modification_or_adversarial"
    if key in DEVICE_APP_ENV_FIELDS or compact_key in DEVICE_APP_ENV_FIELDS:
        return "app_environment"
    if key in DEVICE_NETWORK_CONTEXT_FIELDS or compact_key in DEVICE_NETWORK_CONTEXT_FIELDS:
        return "device_network_context"
    if key in DEVICE_REQUEST_CONTEXT_FIELDS or compact_key in DEVICE_REQUEST_CONTEXT_FIELDS:
        return "device_request_context"
    if key in DEVICE_RISK_LABEL_FIELDS or compact_key in DEVICE_RISK_LABEL_FIELDS:
        return "device_risk_label"
    if key in DEVICE_RELATION_FIELDS or compact_key in DEVICE_RELATION_FIELDS:
        return "account_device_relation"
    if key in DEVICE_BEHAVIOR_CONSISTENCY_FIELDS or compact_key in DEVICE_BEHAVIOR_CONSISTENCY_FIELDS:
        return "behavior_device_consistency"
    if key in DEVICE_ID_ONLY_FIELDS or compact_key in DEVICE_ID_ONLY_FIELDS:
        return "device_identifier_anchor"
    return "unknown_device_field_family"


def _device_source_type_for_field(field_key: str, explicit: Any = None) -> str:
    explicit_text = str(explicit or "").strip()
    if explicit_text in DEVICE_DETAIL_SOURCE_TYPES:
        return explicit_text
    family = _device_field_family(field_key)
    if family == "device_basic":
        return "设备基础信息"
    if family in {"device_freshness", "low_life_device_environment"}:
        return "设备使用画像"
    if family in {"automation_or_script", "modification_or_adversarial", "device_risk_label"}:
        return "设备风险标签"
    if family == "app_environment":
        return "安装列表 / 应用环境"
    if family in {"device_network_context", "device_request_context"}:
        return "未知"
    if family in {"account_device_relation", "device_identifier_anchor"}:
        return "账号-设备关系"
    if family == "behavior_device_consistency":
        return "行为-设备一致性"
    return "未知"


def _device_comparable_type(field_key: str, value: Any, explicit: Any = None) -> str:
    explicit_text = str(explicit or "").strip()
    if explicit_text:
        return explicit_text
    key = _normalized_device_field_key(field_key)
    compact_key = _compact_device_field_key(key)
    if value in {None, ""}:
        return "不可比较"
    if key in DEVICE_FRESHNESS_FIELDS or compact_key in DEVICE_FRESHNESS_FIELDS or key in {"account_device_count", "device_account_count", "same_device_user_count"}:
        return "数值分桶"
    if key in DEVICE_LOW_LIFE_FIELDS or compact_key in DEVICE_LOW_LIFE_FIELDS or key in DEVICE_AUTOMATION_FIELDS or compact_key in DEVICE_AUTOMATION_FIELDS or key in DEVICE_MODIFICATION_FIELDS or compact_key in DEVICE_MODIFICATION_FIELDS:
        return "布尔"
    if key in DEVICE_APP_ENV_FIELDS or compact_key in DEVICE_APP_ENV_FIELDS:
        return "集合相似"
    if key in DEVICE_NETWORK_CONTEXT_FIELDS or compact_key in DEVICE_NETWORK_CONTEXT_FIELDS or key in DEVICE_REQUEST_CONTEXT_FIELDS or compact_key in DEVICE_REQUEST_CONTEXT_FIELDS:
        return "等值"
    if key in DEVICE_BASIC_FIELDS or compact_key in DEVICE_BASIC_FIELDS or key in DEVICE_RISK_LABEL_FIELDS or compact_key in DEVICE_RISK_LABEL_FIELDS:
        return "等值"
    if key in DEVICE_BEHAVIOR_CONSISTENCY_FIELDS or key in DEVICE_ID_ONLY_FIELDS:
        return "等值"
    return "文本相似"


def _device_candidate_eligible(field_key: str, row: dict[str, Any]) -> bool:
    key = _normalized_device_field_key(field_key)
    if key in DEVICE_FEATURE_CANDIDATE_EXCLUDED_FIELDS:
        return False
    if row.get("value_present") is not True or row.get("value_comparable") is not True:
        return False
    return _device_field_family(key) not in {"unknown_device_field_family", "device_context_only", "device_network_context", "device_request_context"}


def _device_evidence_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "sample_id": row.get("sample_id"),
        "entity_id": row.get("entity_id"),
        "user_id": row.get("user_id"),
        "device_id": row.get("device_id") or row.get("device_safe_ref"),
        "round_id": row.get("round_id"),
        "source_id": row.get("source_id"),
        "source_quality": row.get("source_quality"),
        "device_field_key": row.get("device_field_key"),
        "device_field_value_or_safe_ref": row.get("device_field_value_or_safe_ref"),
    }


def _device_platform_bucket_from_row(row: dict[str, Any]) -> str:
    explicit = str(row.get("device_platform") or "").strip().lower()
    if explicit in {"android", "ios"}:
        return explicit
    text = " ".join(
        str(row.get(key) or "")
        for key in (
            "device_id",
            "device_safe_ref",
            "device_field_key",
            "device_field_value_or_safe_ref",
            "phone_model",
            "os_version",
        )
    ).lower()
    compact = "".join(ch for ch in text if ch.isalnum())
    if "android" in text or "android" in compact:
        return "android"
    ios_markers = ("iphone", "ipad", "ios", "idfa", "idfv", "kernos", "kernwake", "userposix", "hwmodel")
    if any(marker in compact for marker in ios_markers):
        return "ios"
    device_ref = str(row.get("device_id") or row.get("device_safe_ref") or "")
    if "-" in device_ref and len(device_ref) >= 32:
        return "ios"
    return "unknown"


def _device_single_field_strong_signal_reason(key: str, value: Any) -> str | None:
    family = _device_field_family(key)
    if key in DEVICE_FEATURE_CANDIDATE_EXCLUDED_FIELDS:
        return None
    compact_key = _compact_device_field_key(key)
    if (
        family == "modification_or_adversarial"
        and any(fragment in compact_key for fragment in DEVICE_HARD_SINGLE_FIELD_FRAGMENTS)
        and _truthy_device_value(value)
    ):
        return "hard adversarial device field is truthy; keep as high-priority candidate evidence, not final conclusion"
    if family == "device_risk_label":
        compact_values = [
            "".join(ch for ch in token.lower() if ch.isalnum())
            for token in _device_value_tokens(value)
        ]
        if any(
            any(fragment in token for fragment in DEVICE_HARD_RISK_LABEL_FRAGMENTS)
            for token in compact_values
        ):
            return "explicit high-risk device label is present; keep as candidate evidence, not final conclusion"
    return None


def _device_weak_field_observation_reason(key: str, value: Any) -> str | None:
    family = _device_field_family(key)
    if family in DEVICE_WEAK_FIELD_FAMILIES and _low_life_device_row_matches(key, value):
        return "weak low-life/freshness observation; single device cannot become hard signal, but batch enrichment can be useful"
    return None


def _unknown_field_noise_category(key: str, value: Any, platform_scope: str) -> str:
    compact_key = _compact_device_field_key(key)
    text = str(value).strip().lower()
    if key.lower() in DEVICE_DEFAULT_LIKE_UNKNOWN_KEYS or compact_key in DEVICE_DEFAULT_LIKE_UNKNOWN_KEYS:
        if text in DEVICE_DEFAULT_LIKE_VALUES or key.lower() in {"groupname", "grouplevel", "labeltype"}:
            return "unknown_possible_default_enum"
    if any(fragment in compact_key for fragment in ("hw", "kern", "userposix", "userstream", "userline", "disk", "memsize", "cpu")):
        return "unknown_possible_system_constant"
    if any(fragment in compact_key for fragment in ("group", "label", "risk", "safe")):
        return "unknown_possible_platform_label"
    if platform_scope in {"android", "ios"} and text in DEVICE_DEFAULT_LIKE_VALUES:
        return "unknown_possible_system_constant"
    return "unknown_needs_dictionary"


def _support_stats_for_rows(rows: list[dict[str, Any]], sampled_entities: list[str]) -> dict[str, Any]:
    support_entities = unique_strings([str(row.get("entity_id")) for row in rows if row.get("entity_id")])
    support_devices = unique_strings([
        str(row.get("device_id") or row.get("device_safe_ref"))
        for row in rows
        if row.get("device_id") or row.get("device_safe_ref")
    ])
    platforms = unique_strings([
        _device_platform_bucket_from_row(row)
        for row in rows
        if _device_platform_bucket_from_row(row) != "unknown"
    ])
    platform_scope = platforms[0] if len(platforms) == 1 else "mixed" if len(platforms) > 1 else "unknown"
    denominator = max(len(sampled_entities), 1)
    support_ratio = round(len(support_entities) / denominator, 4)
    return {
        "support_entities": support_entities,
        "support_devices": support_devices,
        "support_device_count": len(support_devices),
        "group_device_count": len(unique_strings([
            str(row.get("device_id") or row.get("device_safe_ref") or row.get("entity_id"))
            for row in rows
            if row.get("device_id") or row.get("device_safe_ref") or row.get("entity_id")
        ])),
        "support_user_count": len(support_entities),
        "support_sample_count": len(support_entities),
        "support_ratio": support_ratio,
        "platform_scope": platform_scope,
    }


def _device_priority_for_signal(
    *,
    signal_type: str,
    known_field: bool,
    field_family: str,
    support_ratio: float | None,
    suspected_default_value: bool | str,
    baseline_ratio: float | None = None,
) -> dict[str, Any]:
    ratio = float(support_ratio or 0.0)
    score = ratio * 40
    reason_codes: list[str] = [f"support_ratio={ratio:.4f}", "baseline_missing"]
    if known_field:
        score += 15
        reason_codes.append("known_field")
    else:
        score -= 8
        reason_codes.append("field_semantics_unknown")
    if field_family in {"modification_or_adversarial", "automation_or_script", "device_risk_label"}:
        score += 25
        reason_codes.append("high_value_device_family")
    elif field_family in {"low_life_device_environment", "device_freshness", "app_environment"}:
        score += 10
        reason_codes.append("enrichment_field_family")
    if signal_type == "hard_single_field_signal":
        score += 25
        reason_codes.append("hard_single_field_signal")
    if signal_type == "group_level_field_enrichment":
        score += 12
        reason_codes.append("weak_field_batch_enrichment")
    if signal_type == "field_combination_commonality":
        score += 18
        reason_codes.append("field_combination")
    if suspected_default_value is True:
        score -= 25
        reason_codes.append("suspected_default_value_downranked")
    elif suspected_default_value == "unknown":
        reason_codes.append("default_value_unknown")
    if baseline_ratio is not None:
        lift = round((ratio / baseline_ratio), 4) if baseline_ratio else None
        reason_codes = [code for code in reason_codes if code != "baseline_missing"]
        reason_codes.append("baseline_available")
        if lift and lift >= 3:
            score += 20
            reason_codes.append(f"lift={lift}")
    else:
        lift = None
    if score >= 70:
        level = "high"
    elif score >= 40:
        level = "medium"
    else:
        level = "low"
    return {
        "priority_score": round(max(score, 0), 2),
        "priority_level": level,
        "reason_codes": reason_codes,
        "baseline_ratio": baseline_ratio,
        "baseline_missing": baseline_ratio is None,
        "lift": lift,
        "lift_unavailable": lift is None,
    }


def _normalize_device_detail_row(
    *,
    source_row: dict[str, Any],
    observation: dict[str, Any],
    entity_id: str,
    round_id: int,
    row_index: int,
) -> dict[str, Any] | None:
    field_key = _normalized_device_field_key(
        source_row.get("device_field_key")
        or source_row.get("field_key")
        or source_row.get("feature_key")
        or source_row.get("field")
    )
    field_name = str(source_row.get("device_field_name") or source_row.get("field_name") or field_key).strip()
    if not field_key and not field_name:
        return None
    field_path_text = str(source_row.get("field_path") or "").lower()
    compact_field_key = _compact_device_field_key(field_key)
    compact_field_name = _compact_device_field_key(field_name)
    if compact_field_key in DEVICE_NON_DEVICE_SUBTREE_KEYS or compact_field_name in DEVICE_NON_DEVICE_SUBTREE_KEYS:
        return None
    path_parts = [
        _compact_device_field_key(part)
        for part in re.split(r"[.\[\]]+", field_path_text)
        if part
    ]
    if any(part in DEVICE_NON_DEVICE_SUBTREE_KEYS for part in path_parts):
        return None
    if _is_credential_secret_key(field_key) or _is_credential_secret_key(field_name):
        return None
    raw_value = (
        source_row.get("device_field_value_or_safe_ref")
        if "device_field_value_or_safe_ref" in source_row
        else source_row.get("field_value_or_safe_ref")
        if "field_value_or_safe_ref" in source_row
        else source_row.get("value")
    )
    redacted = _is_credential_secret_key(field_key) or _is_credential_secret_key(field_name)
    value_present = raw_value is not None and raw_value != ""
    safe_value = "redacted_safe_ref" if redacted and value_present else raw_value
    source_quality = str(source_row.get("source_quality") or observation.get("quality_class") or "completed")
    device_id = source_row.get("device_id") or source_row.get("device_safe_ref") or source_row.get("candidate_device_id")
    device_source_type = _device_source_type_for_field(field_key, source_row.get("device_source_type"))
    comparable_type = _device_comparable_type(field_key, safe_value, source_row.get("comparable_type"))
    value_comparable = bool(source_row.get("value_comparable", value_present and not redacted and comparable_type != "不可比较"))
    row = {
        "sample_id": source_row.get("sample_id") or f"round_{round_id}_{entity_id}",
        "entity_id": source_row.get("entity_id") or entity_id,
        "user_id": source_row.get("user_id") or entity_id,
        "round_id": round_id,
        "device_id": device_id if field_key in DEVICE_ID_ONLY_FIELDS else source_row.get("device_id"),
        "device_safe_ref": source_row.get("device_safe_ref") or device_id or f"device_context_{entity_id}",
        "source_id": source_row.get("source_id") or observation.get("source_id"),
        "source_name": source_row.get("source_name") or observation.get("action") or "weapon_inventory",
        "action": source_row.get("action") or observation.get("action"),
        "device_source_type": device_source_type,
        "device_field_key": field_key or field_name,
        "device_field_name": field_name or field_key,
        "device_field_value_or_safe_ref": safe_value,
        "device_field_type": str(source_row.get("device_field_type") or type(raw_value).__name__),
        "value_present": bool(value_present),
        "value_comparable": value_comparable,
        "comparable_type": comparable_type,
        "source_quality": source_quality,
        "evidence_source": source_row.get("evidence_source") or "current_observation",
        "event_time": source_row.get("event_time"),
        "query_time": source_row.get("query_time"),
        "device_role": source_row.get("device_role") or "未知",
        "sensitive_value_policy": source_row.get("sensitive_value_policy") or ("只保留安全引用" if redacted else "原值可用"),
        "device_platform": source_row.get("device_platform"),
        "app_version": source_row.get("app_version"),
        "os_version": source_row.get("os_version"),
        "phone_model": source_row.get("phone_model"),
        "risk_label": source_row.get("risk_label"),
        "risk_label_group": source_row.get("risk_label_group"),
        "usage_signal": source_row.get("usage_signal"),
        "environment_signal": source_row.get("environment_signal"),
        "automation_signal": source_row.get("automation_signal"),
        "modification_signal": source_row.get("modification_signal"),
        "low_life_signal": source_row.get("low_life_signal"),
        "app_environment_signal": source_row.get("app_environment_signal"),
        "relation_signal": source_row.get("relation_signal"),
        "behavior_device_consistency_signal": source_row.get("behavior_device_consistency_signal"),
        "mapped_field_family": source_row.get("mapped_field_family") or _device_field_family(field_key),
        "candidate_feature_eligible": bool(source_row.get("candidate_feature_eligible", False)),
    }
    row["device_platform"] = row.get("device_platform") or _device_platform_bucket_from_row(row)
    row["known_device_field"] = row["mapped_field_family"] != "unknown_device_field_family"
    row["unknown_device_field_retained"] = row["mapped_field_family"] == "unknown_device_field_family"
    row["raw_device_field_retention_policy"] = "retain_non_secret_weapon_leaf_fields"
    row["candidate_feature_eligible"] = bool(source_row.get("candidate_feature_eligible", _device_candidate_eligible(field_key, row)))
    row["source_priority_boundary"] = (
        "weapon_device_detail_primary" if str(row.get("source_name")) in {"weapon_device_info", "weapon_device_app_list", "weapon_device_location_info"}
        else "weapon_inventory_graph_relation_context" if str(row.get("source_name")) == "weapon_inventory"
        else "weapon_user_klink_context" if str(row.get("source_name")) == "weapon_user_klink_status"
        else "rcp_event_feature_context_only" if str(row.get("source_name")) == "rcp_event_feature_list"
        else "device_context_supplement"
    )
    row["device_stage_boundary"] = (
        "frontend_activity_is_behavior_domain_not_device_fingerprint"
        if field_key == "frontend_activity_signal"
        else "device_detail_field_candidate_not_final_conclusion"
    )
    return row


def build_device_detail_table(
    *,
    round_id: int,
    sampled_entities: list[str],
    source_observations: list[dict[str, Any]],
    strategy_event_feature_row_table: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for observation in source_observations:
        quality = str(observation.get("quality_class") or "unknown")
        if quality not in {"completed", "partial"}:
            continue
        entity_id = _observation_entity_for_round(observation, sampled_entities)
        for row_index, source_row in enumerate(observation.get("device_detail_rows", []) or [], start=1):
            if not isinstance(source_row, dict):
                continue
            normalized = _normalize_device_detail_row(
                source_row=source_row,
                observation=observation,
                entity_id=entity_id,
                round_id=round_id,
                row_index=row_index,
            )
            if normalized is not None:
                rows.append(normalized)
        for candidate in observation.get("candidate_device_ids", []) or []:
            if not isinstance(candidate, dict):
                continue
            normalized = _normalize_device_detail_row(
                source_row={
                    "device_field_key": "device_id",
                    "device_field_name": "设备号",
                    "device_field_value_or_safe_ref": candidate.get("device_id"),
                    "device_id": candidate.get("device_id"),
                    "source_id": candidate.get("source_id") or observation.get("source_id"),
                    "source_name": observation.get("action") or "unknown_source",
                    "device_source_type": "账号-设备关系",
                    "device_role": "未知",
                    "source_quality": quality,
                    "candidate_feature_eligible": False,
                },
                observation=observation,
                entity_id=entity_id,
                round_id=round_id,
                row_index=0,
            )
            if normalized is not None:
                rows.append(normalized)
    for feature_row in strategy_event_feature_row_table:
        if str(feature_row.get("mapped_domain") or "") != "设备":
            continue
        field_key = str(feature_row.get("feature_key") or "")
        normalized = _normalize_device_detail_row(
            source_row={
                "sample_id": feature_row.get("sample_id"),
                "entity_id": feature_row.get("entity_id"),
                "user_id": feature_row.get("user_id"),
                "device_field_key": field_key,
                "device_field_name": feature_row.get("feature_name") or field_key,
                "device_field_value_or_safe_ref": feature_row.get("feature_value_or_safe_ref"),
                "device_field_type": feature_row.get("feature_type"),
                "value_present": feature_row.get("value_present"),
                "value_comparable": feature_row.get("value_comparable"),
                "comparable_type": feature_row.get("comparable_type"),
                "source_id": feature_row.get("source_id"),
                "source_name": "rcp_event_feature_list",
                "device_source_type": _device_source_type_for_field(field_key),
                "device_role": "策略事件上下文设备字段",
                "source_quality": feature_row.get("source_quality"),
                "evidence_source": feature_row.get("evidence_source"),
                "event_time": feature_row.get("event_time"),
                "sensitive_value_policy": feature_row.get("sensitive_value_policy"),
                "mapped_field_family": _device_field_family(field_key),
            },
            observation={
                "source_id": feature_row.get("source_id"),
                "action": "rcp_event_feature_list",
                "quality_class": feature_row.get("source_quality") or "completed",
            },
            entity_id=str(feature_row.get("entity_id") or ""),
            round_id=round_id,
            row_index=int(feature_row.get("feature_row_index") or 0),
        )
        if normalized is not None:
            rows.append(normalized)
    deduped: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, str, str]] = set()
    for row in rows:
        if _is_device_secret_field(row):
            continue
        identity = (
            str(row.get("sample_id") or ""),
            str(row.get("device_safe_ref") or row.get("device_id") or ""),
            str(row.get("source_id") or ""),
            str(row.get("device_field_key") or ""),
            str(row.get("device_field_value_or_safe_ref") or ""),
        )
        if identity in seen:
            continue
        seen.add(identity)
        deduped.append(row)
    return deduped


def build_device_detail_source_field_summary(device_detail_table: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_source: dict[str, list[dict[str, Any]]] = {}
    for row in device_detail_table:
        source_name = str(row.get("source_name") or row.get("action") or "unknown_source")
        if source_name not in {"weapon_inventory", *WEAPON_DEVICE_DETAIL_ACTIONS}:
            continue
        by_source.setdefault(source_name, []).append(row)
    summary: list[dict[str, Any]] = []
    for source_name in sorted(by_source):
        rows = by_source[source_name]
        field_keys = unique_strings([str(row.get("device_field_key") or "") for row in rows if row.get("device_field_key")])
        comparable_field_keys = unique_strings([
            str(row.get("device_field_key") or "")
            for row in rows
            if row.get("device_field_key") and row.get("value_comparable") is True
        ])
        commonality_eligible_field_keys = unique_strings([
            str(row.get("device_field_key") or "")
            for row in rows
            if row.get("device_field_key")
            and row.get("value_comparable") is True
            and row.get("candidate_feature_eligible") is True
        ])
        summary.append(
            {
                "source_name": source_name,
                "device_detail_row_count": len(rows),
                "distinct_output_field_count": len(field_keys),
                "comparable_field_count": len(comparable_field_keys),
                "commonality_eligible_field_count": len(commonality_eligible_field_keys),
                "commonality_eligible_sample_keys": commonality_eligible_field_keys[:20],
                "field_retention_boundary": "non_credential_leaf_fields_retained; credential_auth_control_fields_excluded",
            }
        )
    return summary


def build_device_commonality_and_features(
    device_detail_table: list[dict[str, Any]],
    sampled_entities: list[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    rows_by_key: dict[str, list[dict[str, Any]]] = {}
    comparable_groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in device_detail_table:
        key = str(row.get("device_field_key") or "")
        if not key:
            continue
        rows_by_key.setdefault(key, []).append(row)
        if row.get("value_present") and row.get("value_comparable"):
            comparable_groups.setdefault((key, str(row.get("device_field_value_or_safe_ref"))), []).append(row)

    commonality_rows: list[dict[str, Any]] = []
    for key, rows in rows_by_key.items():
        entities = unique_strings([str(row.get("entity_id")) for row in rows if row.get("entity_id")])
        if len(entities) < 2:
            continue
        commonality_rows.append({
            "signal_name": f"device_field_coverage:{key}",
            "commonality_type": "coverage_commonality",
            "device_field_key": key,
            "device_field_family": _device_field_family(key),
            "source_fields": [key],
            "supporting_current_evidence": entities,
            "support_count": len(entities),
            "batch_support_count": len(entities),
            "commonality_anchor": False,
            "risk_commonality": False,
            "eligible_for_group_candidate": False,
            "candidate_feature_eligible": False,
            "evidence_source": "current_observation",
            "source_name": "device_detail_table",
            "not_final_conclusion": True,
        })

    known_value_commonality_rows: list[dict[str, Any]] = []
    unknown_value_commonality_rows: list[dict[str, Any]] = []
    for (key, value_ref), rows in comparable_groups.items():
        entities = unique_strings([str(row.get("entity_id")) for row in rows if row.get("entity_id")])
        if len(entities) < 2 or key in DEVICE_FEATURE_CANDIDATE_EXCLUDED_FIELDS:
            continue
        field_family = _device_field_family(key)
        known_field = field_family != "unknown_device_field_family"
        if known_field and not any(row.get("candidate_feature_eligible") for row in rows):
            continue
        commonality_type = "known_field_commonality" if known_field else "unknown_field_value_commonality"
        stats = _support_stats_for_rows(rows, sampled_entities)
        unknown_category = None if known_field else _unknown_field_noise_category(key, value_ref, stats["platform_scope"])
        suspected_default_value: bool | str = (
            False if known_field else unknown_category in {
                "unknown_possible_default_enum",
                "unknown_possible_system_constant",
                "unknown_possible_platform_label",
            }
        )
        priority = _device_priority_for_signal(
            signal_type=commonality_type,
            known_field=known_field,
            field_family=field_family,
            support_ratio=stats["support_ratio"],
            suspected_default_value=suspected_default_value,
        )
        commonality = {
            "signal_name": f"device_field_value_commonality:{key}",
            "commonality_type": commonality_type,
            "commonality_subtype": "field_value_commonality",
            "device_field_key": key,
            "device_field_family": field_family,
            "device_field_value_or_safe_ref": value_ref,
            "field_value_or_safe_ref": value_ref,
            "source_fields": [key],
            "supporting_current_evidence": entities,
            "support_count": len(entities),
            "batch_support_count": len(entities),
            "support_device_count": stats["support_device_count"],
            "group_device_count": stats["group_device_count"],
            "support_user_count": stats["support_user_count"],
            "support_ratio": stats["support_ratio"],
            "platform_scope": stats["platform_scope"],
            "commonality_anchor": False,
            "risk_commonality": False,
            "eligible_for_group_candidate": False,
            "candidate_feature_eligible": True,
            "known_field": known_field,
            "field_semantics_status": "known_field_family" if known_field else "field_semantics_unknown",
            "unknown_field_category": unknown_category,
            "suspected_default_value": suspected_default_value,
            "why_suspicious": (
                "多个设备/用户共享同一已知设备字段值，可作为候选设备字段共性。"
                if known_field else
                "多个设备/用户共享同一未知字段值，说明存在可疑字段值共性；字段语义未知，需字段字典或正常对照验证。"
            ),
            "false_positive_risk": (
                "同机型、同版本、同渠道或正常配置也可能共享字段值，需要正常样本背景率。"
                if known_field else
                "字段含义未知，可能是正常系统参数或平台默认值，不能强解释为黑产。"
            ),
            "validation_needed": True,
            "evidence_source": "current_observation",
            "source_name": "device_detail_table",
            "not_final_conclusion": True,
            **priority,
        }
        commonality_rows.append(commonality)
        if known_field:
            known_value_commonality_rows.append(commonality)
        else:
            unknown_value_commonality_rows.append(commonality)

    rows_by_entity: dict[str, list[dict[str, Any]]] = {}
    for row in device_detail_table:
        rows_by_entity.setdefault(str(row.get("entity_id") or ""), []).append(row)

    candidate_features: list[dict[str, Any]] = []
    low_life_support: list[dict[str, Any]] = []
    automation_support: list[dict[str, Any]] = []
    modification_support: list[dict[str, Any]] = []
    app_environment_support: list[dict[str, Any]] = []
    consistency_support: list[dict[str, Any]] = []
    single_field_strong_support: list[dict[str, Any]] = []
    single_field_groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    weak_field_groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for entity, rows in rows_by_entity.items():
        keyed = {str(row.get("device_field_key")): row for row in rows}
        low_life_fields = [
            row for key, row in keyed.items()
            if _device_key_in_family(key, DEVICE_FRESHNESS_FIELDS | DEVICE_LOW_LIFE_FIELDS)
            and _low_life_device_row_matches(key, row.get("device_field_value_or_safe_ref"))
        ]
        if len(low_life_fields) >= 2:
            low_life_support.extend(low_life_fields)
        automation_fields = [
            row for key, row in keyed.items()
            if _device_key_in_family(key, DEVICE_AUTOMATION_FIELDS) and _truthy_device_value(row.get("device_field_value_or_safe_ref"))
        ]
        if automation_fields:
            automation_support.extend(automation_fields)
        modification_fields = [
            row for key, row in keyed.items()
            if _device_key_in_family(key, DEVICE_MODIFICATION_FIELDS) and _truthy_device_value(row.get("device_field_value_or_safe_ref"))
        ]
        if modification_fields:
            modification_support.extend(modification_fields)
        app_environment_fields = [
            row for key, row in keyed.items()
            if _device_key_in_family(key, DEVICE_APP_ENV_FIELDS) and row.get("value_present") is True
        ]
        if len(app_environment_fields) >= 2:
            app_environment_support.extend(app_environment_fields)
        login_device = keyed.get("login_device_id", {}).get("device_field_value_or_safe_ref")
        backend_device = keyed.get("backend_action_device_id", {}).get("device_field_value_or_safe_ref")
        frontend_device = keyed.get("frontend_active_device_id", {}).get("device_field_value_or_safe_ref")
        if login_device and backend_device and login_device != backend_device:
            consistency_support.extend([keyed["login_device_id"], keyed["backend_action_device_id"]])
        if login_device and frontend_device and login_device != frontend_device:
            consistency_support.extend([keyed["login_device_id"], keyed["frontend_active_device_id"]])
        for row in rows:
            key = str(row.get("device_field_key") or "")
            reason = _device_single_field_strong_signal_reason(key, row.get("device_field_value_or_safe_ref"))
            value_ref = str(row.get("device_field_value_or_safe_ref"))
            if reason:
                single_field_strong_support.append(row)
                single_field_groups.setdefault((key, value_ref), []).append(row)
                continue
            weak_reason = _device_weak_field_observation_reason(key, row.get("device_field_value_or_safe_ref"))
            if weak_reason:
                weak_field_groups.setdefault((key, value_ref), []).append(row)

    for (key, value_ref), rows in single_field_groups.items():
        stats = _support_stats_for_rows(rows, sampled_entities)
        if not stats["support_entities"]:
            continue
        priority = _device_priority_for_signal(
            signal_type="hard_single_field_signal",
            known_field=True,
            field_family=_device_field_family(key),
            support_ratio=stats["support_ratio"],
            suspected_default_value=False,
        )
        signal = {
            "signal_name": f"single_field_strong_signal:{key}",
            "commonality_type": "hard_single_field_signal",
            "device_field_key": key,
            "device_field_family": _device_field_family(key),
            "device_field_value_or_safe_ref": value_ref,
            "source_fields": [key],
            "supporting_current_evidence": stats["support_entities"],
            "support_count": stats["support_user_count"],
            "batch_support_count": stats["support_user_count"],
            "support_device_count": stats["support_device_count"],
            "group_device_count": stats["group_device_count"],
            "support_user_count": stats["support_user_count"],
            "support_ratio": stats["support_ratio"],
            "platform_scope": stats["platform_scope"],
            "risk_commonality": False,
            "eligible_for_group_candidate": False,
            "candidate_feature_eligible": True,
            "risk_interpretation": _device_single_field_strong_signal_reason(key, value_ref),
            "false_positive_risk": "单字段可能来自测试机、企业设备、误报或正常系统参数，需要结合更多字段和正常对照。",
            "known_field": True,
            "field_semantics_status": "known_field_family",
            "suspected_default_value": False,
            "validation_needed": True,
            "evidence_source": "current_observation",
            "source_name": "device_detail_table",
            "not_final_conclusion": True,
            **priority,
        }
        commonality_rows.append(signal)

    group_level_enrichment_rows: list[dict[str, Any]] = []
    for (key, value_ref), rows in weak_field_groups.items():
        stats = _support_stats_for_rows(rows, sampled_entities)
        if stats["support_user_count"] < 2:
            continue
        priority = _device_priority_for_signal(
            signal_type="group_level_field_enrichment",
            known_field=True,
            field_family=_device_field_family(key),
            support_ratio=stats["support_ratio"],
            suspected_default_value=False,
        )
        signal = {
            "signal_name": f"group_level_field_enrichment:{key}",
            "commonality_type": "group_level_field_enrichment_commonality",
            "device_field_key": key,
            "device_field_family": _device_field_family(key),
            "device_field_value_or_safe_ref": value_ref,
            "source_fields": [key],
            "supporting_current_evidence": stats["support_entities"],
            "support_count": stats["support_user_count"],
            "batch_support_count": stats["support_user_count"],
            "support_device_count": stats["support_device_count"],
            "group_device_count": stats["group_device_count"],
            "support_user_count": stats["support_user_count"],
            "support_ratio": stats["support_ratio"],
            "platform_scope": stats["platform_scope"],
            "known_field": True,
            "field_semantics_status": "known_field_family",
            "suspected_default_value": False,
            "baseline_ratio": None,
            "baseline_missing": True,
            "lift": None,
            "lift_unavailable": True,
            "risk_commonality": False,
            "eligible_for_group_candidate": False,
            "candidate_feature_eligible": True,
            "risk_interpretation": "弱设备字段在批量样本中富集，可作为团组层面候选共性；没有 baseline 前不能作为最终风险结论。",
            "false_positive_risk": "新机、备用机、企业设备、系统配置或正常低活跃设备可能出现同类弱字段，需要正常背景率。",
            "validation_needed": True,
            "evidence_source": "current_observation",
            "source_name": "device_detail_table",
            "not_final_conclusion": True,
            **priority,
        }
        group_level_enrichment_rows.append(signal)
        commonality_rows.append(signal)

    def add_device_candidate(
        *,
        feature_name: str,
        feature_type: str,
        support_rows: list[dict[str, Any]],
        source_fields: list[str],
        field_combination: list[str],
        interpretation: str,
        false_positive: str,
        missing_fields: list[str],
        validation_method: str,
        usage_boundary: str,
        confidence: str = "medium_partial",
        support_min_users: int = 2,
        field_values_or_safe_refs: list[Any] | None = None,
        field_semantics_status: str | None = None,
        priority: dict[str, Any] | None = None,
        suspected_default_value: bool | str = False,
    ) -> None:
        stats = _support_stats_for_rows(support_rows, sampled_entities)
        if stats["support_user_count"] < support_min_users:
            return
        evidence = [_device_evidence_row(row) for row in support_rows]
        if field_values_or_safe_refs:
            value_refs = unique_strings([
                safe_ref
                for value in field_values_or_safe_refs
                for safe_ref in [_device_value_safe_ref(value)]
                if safe_ref
            ])[:20]
        else:
            value_refs = unique_strings([
                safe_ref
                for row in support_rows
                for safe_ref in [_device_value_safe_ref(row.get("device_field_value_or_safe_ref"))]
                if safe_ref
            ])[:20]
        priority_payload = priority or _device_priority_for_signal(
            signal_type=feature_type,
            known_field=field_semantics_status != "field_semantics_unknown",
            field_family=_device_field_family(source_fields[0] if source_fields else ""),
            support_ratio=stats["support_ratio"],
            suspected_default_value=suspected_default_value,
        )
        candidate_features.append({
            "feature_name": feature_name,
            "feature_type": feature_type,
            "source_domains": ["device_domain"],
            "source_fields": source_fields,
            "source_device_fields": source_fields,
            "field_values_or_safe_refs": value_refs,
            "field_combination": field_combination,
            "support_device_count": stats["support_device_count"],
            "group_device_count": stats["group_device_count"],
            "support_user_count": stats["support_user_count"],
            "support_sample_count": stats["support_sample_count"],
            "support_ratio": stats["support_ratio"],
            "platform_scope": stats["platform_scope"],
            "known_field": field_semantics_status != "field_semantics_unknown",
            "suspected_default_value": suspected_default_value,
            "supporting_current_evidence": evidence,
            "supporting_selected_anchors": [],
            "unselected_signal_hypothesis": True,
            "signal_inputs": [{"evidence_source": "current_observation", "device_fields": source_fields}],
            "hypothesis_inputs": [{"evidence_source": "expert_hypothesis", "signal": feature_name, "usage_boundary": "device_candidate_requires_validation"}],
            "black_gray_interpretation": interpretation,
            "normal_user_false_positive_risk": false_positive,
            "false_positive_risk": false_positive,
            "missing_fields_to_check": missing_fields,
            "missing_evidence": missing_fields,
            "validation_method": validation_method,
            "strategy_usage_boundary": usage_boundary,
            "confidence": confidence,
            "validation_needed": True,
            "not_final_conclusion": True,
            "conclusion_boundary": "candidate_only_not_final_conclusion",
            **priority_payload,
        })
        if field_semantics_status:
            candidate_features[-1]["field_semantics_status"] = field_semantics_status

    add_device_candidate(
        feature_name="low_life_device_environment_candidate",
        feature_type="field_combination_commonality",
        support_rows=low_life_support,
        source_fields=["launch_count", "boot_duration", "lock_screen_enabled", "sim_present"],
        field_combination=["launch_count_low", "boot_duration_short", "lock_screen_or_sim_missing"],
        interpretation="设备缺少正常生活化沉淀，可能是批量设备池或短期任务设备环境。",
        false_positive="新机、备用机、测试机也可能启动少或无 SIM，需要正常设备对照。",
        missing_fields=["device_first_seen_time", "active_days", "normal_device_control_group", "weapon_device_usage_profile"],
        validation_method="按设备使用画像字段回放目标样本和正常对照，计算覆盖率、背景率、lift 和误伤率。",
        usage_boundary="候选设备特征，只能用于观察、人审辅助或灰度验证，不能直接处置。",
    )
    add_device_candidate(
        feature_name="group_level_field_enrichment_candidate",
        feature_type="group_level_field_enrichment",
        support_rows=[
            row
            for signal in group_level_enrichment_rows
            for row in comparable_groups.get((str(signal.get("device_field_key") or ""), str(signal.get("device_field_value_or_safe_ref") or "")), [])
        ],
        source_fields=unique_strings([str(signal.get("device_field_key") or "") for signal in group_level_enrichment_rows]),
        field_combination=["weak_device_field_batch_enrichment"],
        interpretation="弱设备字段在多个设备/用户中高占比出现，可作为团组层面的设备生活化/新鲜度富集共性。",
        false_positive="弱字段常见于新机、备用机、企业设备或正常低活跃设备；没有正常背景率时不能直接定性。",
        missing_fields=["baseline_ratio", "normal_device_control_group", "support_ratio_by_platform", "device_usage_history"],
        validation_method="按字段值计算目标样本 support_ratio；补正常设备 baseline_ratio 后计算 lift，验证误伤。",
        usage_boundary="团组富集候选共性，不是 hard 单字段信号，不直接上线策略。",
        confidence="low_partial",
        priority=_device_priority_for_signal(
            signal_type="group_level_field_enrichment",
            known_field=True,
            field_family="low_life_device_environment",
            support_ratio=max([float(signal.get("support_ratio") or 0) for signal in group_level_enrichment_rows] or [0]),
            suspected_default_value=False,
        ),
    )
    add_device_candidate(
        feature_name="automation_or_script_device_candidate",
        feature_type="field_combination_commonality",
        support_rows=automation_support,
        source_fields=unique_strings([str(row.get("device_field_key") or "") for row in automation_support]) or ["automation_service_detected", "script_risk"],
        field_combination=["automation_or_script_related_field_truthy"],
        interpretation="设备环境出现自动化或脚本迹象，可能承载批量任务执行。",
        false_positive="辅助功能、企业测试环境或无障碍工具可能误触，需要结合行为节奏和对照组。",
        missing_fields=["backend_action_sequence", "frontend_behavior_sequence", "automation_detail_label", "normal_control_group"],
        validation_method="按自动化/脚本字段组合联动行为序列验证覆盖、误伤和跨轮稳定性。",
        usage_boundary="候选自动化设备特征，不等于确认脚本或群控。",
    )
    add_device_candidate(
        feature_name="modification_or_adversarial_device_candidate",
        feature_type="field_combination_commonality",
        support_rows=modification_support,
        source_fields=unique_strings([str(row.get("device_field_key") or "") for row in modification_support]) or ["frida_signal", "root_or_hook_signal", "device_reset_signal"],
        field_combination=["frida_xposed_mount_reset_or_emulator_related_field_truthy"],
        interpretation="设备环境出现改机、hook、frida、xposed、reset 或模拟器相关字段，可能存在对抗或环境伪造。",
        false_positive="安全测试机、研发机、越狱/刷机爱好者或误报标签可能命中，需要和行为链路、正常对照一起验证。",
        missing_fields=["weapon_device_risk_label_detail", "root_hook_frida_detail", "emulator_detail", "normal_device_control_group"],
        validation_method="按对抗字段组合计算目标样本覆盖率、正常设备背景率、lift 和人工复核误伤。",
        usage_boundary="候选对抗设备特征，不等于确认改机、脚本或团伙。",
        confidence="medium_partial",
    )
    add_device_candidate(
        feature_name="risky_app_environment_candidate",
        feature_type="field_combination_commonality",
        support_rows=app_environment_support,
        source_fields=unique_strings([str(row.get("device_field_key") or "") for row in app_environment_support]) or ["installed_app_list", "installed_app_cluster"],
        field_combination=["installed_app_or_upload_app_list_environment_similarity"],
        interpretation="安装列表、应用环境或应用上报统计存在相似字段，可能是同一工具链、脚本环境或设备模板。",
        false_positive="同版本客户端、系统应用、热门应用和同渠道包会天然相似，需要排除常见应用背景率。",
        missing_fields=["installed_app_detail", "risk_app_label", "normal_app_environment_baseline"],
        validation_method="按安装环境字段做目标样本和正常对照的字段值共性、背景率与误伤复核。",
        usage_boundary="应用环境候选特征，只能进入观察/人审辅助/灰度验证。",
        confidence="low_partial",
    )
    add_device_candidate(
        feature_name="behavior_device_consistency_gap_candidate",
        feature_type="field_combination_commonality",
        support_rows=consistency_support,
        source_fields=["login_device_id", "backend_action_device_id", "frontend_active_device_id"],
        field_combination=["login_device_backend_or_frontend_device_mismatch"],
        interpretation="登录设备、后端动作设备、前端活跃设备不一致，可能存在后端动作与真实前端使用脱节。",
        false_positive="多端登录、换机、前端埋点缺失也会导致不一致，需要行为链路补证。",
        missing_fields=["frontend_action_sequence", "backend_action_sequence", "device_role_timestamps", "track_readiness"],
        validation_method="按登录/后端/前端设备角色和时间序列验证链路一致性。",
        usage_boundary="行为-设备一致性候选线索，不是纯设备指纹特征。",
        confidence="low_partial",
    )
    add_device_candidate(
        feature_name="hard_single_field_signal_candidate",
        feature_type="hard_single_field_signal",
        support_rows=single_field_strong_support,
        source_fields=unique_strings([str(row.get("device_field_key") or "") for row in single_field_strong_support]),
        field_combination=["single_high_value_device_field"],
        interpretation="明确对抗类设备字段命中可作为高价值设备风险候选入口；职业黑产可能只露出少量高价值字段，但不能直接定性。",
        false_positive="研发机、测试机、企业设备、辅助功能或系统默认值可能误触，需要样本覆盖和正常对照。",
        missing_fields=["normal_device_control_group", "field_dictionary", "device_behavior_sequence"],
        validation_method="按 hard 单字段信号计算目标样本覆盖、正常背景率、lift 和人工复核误伤。",
        usage_boundary="hard 单字段信号只进入候选特征或人审辅助，不直接上线拦截。",
        support_min_users=1,
        confidence="low_partial",
        priority=_device_priority_for_signal(
            signal_type="hard_single_field_signal",
            known_field=True,
            field_family="modification_or_adversarial",
            support_ratio=(_support_stats_for_rows(single_field_strong_support, sampled_entities).get("support_ratio") or 0),
            suspected_default_value=False,
        ),
    )
    sorted_unknown_commonality = sorted(
        unknown_value_commonality_rows,
        key=lambda item: (
            1 if item.get("suspected_default_value") is True else 0,
            -float(item.get("priority_score") or 0),
            -float(item.get("support_ratio") or 0),
            str(item.get("device_field_key") or ""),
        ),
    )
    for commonality in sorted_unknown_commonality[:DEVICE_UNKNOWN_CANDIDATE_LIMIT]:
        key = str(commonality.get("device_field_key") or "")
        rows = [
            row for row in comparable_groups.get((key, str(commonality.get("device_field_value_or_safe_ref"))), [])
            if isinstance(row, dict)
        ]
        unknown_category = str(commonality.get("unknown_field_category") or "unknown_needs_dictionary")
        add_device_candidate(
            feature_name="unknown_field_value_enrichment_candidate",
            feature_type="unknown_field_value_commonality",
            support_rows=rows,
            source_fields=[key],
            field_combination=[f"{key}=shared_unknown_value"],
            interpretation="多个设备/用户共享同一未知字段值，可疑但字段语义未知；只能作为候选异常等待字段字典或正常对照验证。",
            false_positive="未知字段可能是系统默认值、SDK 常量、正常配置或平台枚举，误伤风险高。",
            missing_fields=["field_dictionary", "normal_device_control_group", "platform_specific_meaning", "more_samples"],
            validation_method="先补字段字典，再看目标样本覆盖、正常样本背景率、平台分布和跨轮稳定性。",
            usage_boundary="unknown 字段候选异常，不得直接解释成自动化、改机或团伙。",
            confidence="low_hypothesis",
            field_semantics_status="field_semantics_unknown",
            suspected_default_value=commonality.get("suspected_default_value", "unknown"),
            priority={
                key_: value
                for key_, value in commonality.items()
                if key_ in {"priority_score", "priority_level", "reason_codes", "baseline_ratio", "baseline_missing", "lift", "lift_unavailable"}
            },
        )
        if candidate_features:
            candidate_features[-1]["unknown_field_category"] = unknown_category

    def add_combination_signal(name: str, rows: list[dict[str, Any]], fields: list[str]) -> None:
        entities = unique_strings([str(row.get("entity_id")) for row in rows if row.get("entity_id")])
        if len(entities) < 2:
            return
        stats = _support_stats_for_rows(rows, sampled_entities)
        priority = _device_priority_for_signal(
            signal_type="field_combination_commonality",
            known_field=True,
            field_family=_device_field_family(fields[0] if fields else ""),
            support_ratio=stats["support_ratio"],
            suspected_default_value=False,
        )
        commonality_rows.append({
            "signal_name": f"field_combination_commonality:{name}",
            "commonality_type": "field_combination_commonality",
            "device_field_key": name,
            "source_fields": fields,
            "field_combination": fields,
            "supporting_current_evidence": entities,
            "support_count": len(entities),
            "batch_support_count": len(entities),
            "support_device_count": stats["support_device_count"],
            "group_device_count": stats["group_device_count"],
            "support_user_count": stats["support_user_count"],
            "support_ratio": stats["support_ratio"],
            "platform_scope": stats["platform_scope"],
            "known_field": True,
            "suspected_default_value": False,
            "commonality_anchor": False,
            "risk_commonality": False,
            "eligible_for_group_candidate": False,
            "candidate_feature_eligible": True,
            "validation_needed": True,
            "evidence_source": "current_observation",
            "source_name": "device_detail_table",
            "not_final_conclusion": True,
            **priority,
        })

    add_combination_signal("low_life_device_environment", low_life_support, ["launch_count", "boot_duration", "lock_screen_enabled", "sim_present"])
    add_combination_signal("automation_or_script_device_environment", automation_support, unique_strings([str(row.get("device_field_key") or "") for row in automation_support]))
    add_combination_signal("modification_or_adversarial_device_environment", modification_support, unique_strings([str(row.get("device_field_key") or "") for row in modification_support]))
    add_combination_signal("risky_app_environment", app_environment_support, unique_strings([str(row.get("device_field_key") or "") for row in app_environment_support]))
    add_combination_signal("behavior_device_consistency_gap", consistency_support, ["login_device_id", "backend_action_device_id", "frontend_active_device_id"])

    similarity_candidates: list[dict[str, Any]] = []
    similarity_fields = ["phone_model", "os_version", "app_version", "risk_label", "installed_app_cluster"]
    grouped_by_signature: dict[tuple[str, ...], list[dict[str, Any]]] = {}
    for entity, rows in rows_by_entity.items():
        keyed = {str(row.get("device_field_key")): row for row in rows}
        signature = tuple(str(keyed.get(field, {}).get("device_field_value_or_safe_ref") or "") for field in similarity_fields)
        shared_count = len([value for value in signature if value])
        if shared_count >= 2:
            grouped_by_signature.setdefault(signature, []).extend([keyed[field] for field in similarity_fields if field in keyed])
    for index, (signature, rows) in enumerate(grouped_by_signature.items(), start=1):
        support_users = unique_strings([str(row.get("entity_id")) for row in rows if row.get("entity_id")])
        support_devices = unique_strings([str(row.get("device_id") or row.get("device_safe_ref")) for row in rows if row.get("device_id") or row.get("device_safe_ref")])
        shared_fields = [field for field, value in zip(similarity_fields, signature) if value]
        if len(support_users) < 2 or len(shared_fields) < 2 or len(support_devices) < 2:
            continue
        candidate = {
            "cluster_id": f"device_environment_similarity_cluster_candidate_{index}",
            "support_users": support_users,
            "support_devices": support_devices,
            "shared_device_fields": shared_fields,
            "similarity_basis": [f"{field}={value}" for field, value in zip(similarity_fields, signature) if value],
            "confidence": "medium_partial" if len(shared_fields) >= 3 else "low_partial",
            "missing_fields": ["weapon_device_fingerprint_detail", "installed_app_detail", "normal_device_control_group"],
            "false_positive_risk": "同机型、同版本或同活动渠道正常用户也可能相似，不能只凭单字段或少量字段定性。",
            "not_confirmed_as_group": True,
        }
        similarity_candidates.append(candidate)
        add_device_candidate(
            feature_name="device_environment_similarity_cluster_candidate",
            feature_type="field_combination_commonality",
            support_rows=rows,
            source_fields=shared_fields,
            field_combination=candidate["similarity_basis"],
            interpretation="不同 device_id 在多个设备环境字段上高度相似，可能是设备池模板或批量环境。",
            false_positive=candidate["false_positive_risk"],
            missing_fields=candidate["missing_fields"],
            validation_method="基于更多设备指纹字段、安装环境和正常对照计算相似簇覆盖率、背景率和误伤。",
            usage_boundary="设备环境相似候选簇，不等于同设备或确认团伙。",
            confidence=candidate["confidence"],
        )
        add_combination_signal("device_environment_similarity_cluster", rows, shared_fields)

    consistency_candidates = [
        {
            "candidate_id": "behavior_device_consistency_gap_candidate",
            "support_users": unique_strings([str(row.get("entity_id")) for row in consistency_support if row.get("entity_id")]),
            "source_fields": ["login_device_id", "backend_action_device_id", "frontend_active_device_id"],
            "boundary": "frontend_activity_is_behavior_domain; this is a behavior-device consistency lead, not a device fingerprint",
            "not_final_conclusion": True,
        }
    ] if consistency_support else []

    platform_by_device_ref: dict[str, str] = {}
    for row in device_detail_table:
        device_ref = str(row.get("device_id") or row.get("device_safe_ref") or "")
        platform = _device_platform_bucket_from_row(row)
        if device_ref and platform != "unknown":
            platform_by_device_ref.setdefault(device_ref, platform)
    platform_rows: dict[str, list[dict[str, Any]]] = {"android": [], "ios": [], "unknown": []}
    for row in device_detail_table:
        device_ref = str(row.get("device_id") or row.get("device_safe_ref") or "")
        platform = platform_by_device_ref.get(device_ref) or _device_platform_bucket_from_row(row)
        platform_rows.setdefault(platform, []).append(row)
    platform_summary: dict[str, Any] = {}
    for platform, rows in sorted(platform_rows.items()):
        field_keys = unique_strings([str(row.get("device_field_key") or "") for row in rows if row.get("device_field_key")])
        unknown_keys = [
            str(row.get("device_field_key") or "")
            for row in rows
            if row.get("device_field_key") and str(row.get("mapped_field_family") or "") == "unknown_device_field_family"
        ]
        top_unknown: list[dict[str, Any]] = []
        for key in unique_strings(unknown_keys)[:20]:
            key_rows = [row for row in rows if str(row.get("device_field_key") or "") == key]
            top_unknown.append({
                "field_name": key,
                "row_count": len(key_rows),
                "support_user_count": len(unique_strings([str(row.get("entity_id")) for row in key_rows if row.get("entity_id")])),
            })
        platform_summary[platform] = {
            "row_count": len(rows),
            "distinct_field_count": len(field_keys),
            "known_field_row_count": len([row for row in rows if row.get("known_device_field") is True]),
            "unknown_field_row_count": len([row for row in rows if row.get("unknown_device_field_retained") is True]),
            "top_unknown_fields": top_unknown,
        }
    device_field_platform_summary = {
        "platforms": platform_summary,
        "known_field_commonality_count": len(known_value_commonality_rows),
        "unknown_field_value_commonality_count": len(unknown_value_commonality_rows),
        "single_field_strong_signal_count": len([
            row for row in commonality_rows
            if str(row.get("commonality_type") or "") in {"single_field_strong_signal", "hard_single_field_signal"}
        ]),
        "hard_single_field_signal_count": len([
            row for row in commonality_rows
            if str(row.get("commonality_type") or "") == "hard_single_field_signal"
        ]),
        "group_level_field_enrichment_commonality_count": len([
            row for row in commonality_rows
            if str(row.get("commonality_type") or "") == "group_level_field_enrichment_commonality"
        ]),
        "field_combination_commonality_count": len([
            row for row in commonality_rows
            if str(row.get("commonality_type") or "") == "field_combination_commonality"
        ]),
        "candidate_feature_count": len(candidate_features),
        "candidate_feature_top_limit_boundary": {
            "unknown_candidate_limit": DEVICE_UNKNOWN_CANDIDATE_LIMIT,
            "all_unknown_commonality_rows_retained": True,
            "user_visible_answer_should_show_top_3_to_5_candidates": True,
        },
    }
    return commonality_rows, similarity_candidates, consistency_candidates, candidate_features, device_field_platform_summary


def _anchor_ref(anchor: dict[str, Any]) -> str:
    return str(anchor.get("value") or anchor.get("safe_ref") or anchor.get("anchor_type") or "")


def _first_handle_value(handles: list[dict[str, Any]], canonical_field: str) -> Any:
    for handle in handles:
        if str(handle.get("canonical_field") or handle.get("field") or "") == canonical_field:
            return handle.get("value")
    return None


def _observation_entity_for_round(
    observation: dict[str, Any],
    sampled_entities: list[str],
) -> str:
    source_id = str(observation.get("source_id") or "")
    index = _entity_index_from_batch_source_id(source_id)
    if index is not None and 1 <= index <= len(sampled_entities):
        return str(sampled_entities[index - 1])
    user_id = _first_handle_value(observation.get("parsed_body_field_handles", []) or [], "user_id")
    if user_id:
        return str(user_id)
    return source_id or "unknown_entity"


def build_strategy_event_request_detail_table(
    *,
    round_id: int,
    sampled_entities: list[str],
    source_observations: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for observation in source_observations:
        action = str(observation.get("action") or "")
        if action not in STRATEGY_EVENT_REQUEST_DETAIL_ACTIONS:
            continue
        quality = str(observation.get("quality_class") or "unknown")
        if quality not in {"completed", "partial"}:
            continue
        handles = observation.get("parsed_body_field_handles", []) or []
        values = {
            field: _first_handle_value(handles, field)
            for field in STRATEGY_EVENT_REQUEST_DETAIL_FIELDS
        }
        if not any(values.values()):
            continue
        entity_id = _observation_entity_for_round(observation, sampled_entities)
        row: dict[str, Any] = {
            "sample_id": f"round_{round_id}_{entity_id}",
            "entity_id": entity_id,
            "user_id": values.get("user_id") or entity_id,
            "round_id": round_id,
            "source_id": observation.get("source_id"),
            "action": action,
            "observation_domain": "strategy_domain",
            "source_quality": quality,
            "evidence_source": "current_observation",
            "missing_request_detail_fields": sorted([
                field for field in STRATEGY_EVENT_REQUEST_DETAIL_CORE_FIELDS
                if values.get(field) in {None, ""}
            ]),
            "entry_label_fields_only": False,
        }
        for field in STRATEGY_EVENT_REQUEST_DETAIL_FIELDS:
            row[field] = values.get(field)
        if values.get("user_id"):
            row["user_id"] = values.get("user_id")
        row["entry_label_fields_only"] = not any(
            row.get(field) not in {None, ""}
            for field in STRATEGY_EVENT_REQUEST_DETAIL_CORE_FIELDS
        )
        rows.append(row)
    return rows


def build_strategy_event_feature_row_table(
    *,
    round_id: int,
    sampled_entities: list[str],
    source_observations: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for observation in source_observations:
        action = str(observation.get("action") or "")
        if action not in STRATEGY_EVENT_FEATURE_ROW_ACTIONS:
            continue
        quality = str(observation.get("quality_class") or "unknown")
        if quality not in {"completed", "partial"}:
            continue
        entity_id = _observation_entity_for_round(observation, sampled_entities)
        handles = observation.get("parsed_body_field_handles", []) or []
        user_id = _first_handle_value(handles, "user_id") or entity_id
        event_id = _first_handle_value(handles, "event_id")
        event_type = _first_handle_value(handles, "event_type")
        policy_code = _first_handle_value(handles, "policy_code")
        event_time = _first_handle_value(handles, "event_time")
        source_rows = observation.get("strategy_event_feature_rows", []) or []
        for row_index, source_row in enumerate(source_rows, start=1):
            if not isinstance(source_row, dict):
                continue
            row = {
                "sample_id": source_row.get("sample_id") or f"round_{round_id}_{entity_id}",
                "entity_id": source_row.get("entity_id") or entity_id,
                "user_id": source_row.get("user_id") or user_id,
                "round_id": round_id,
                "event_id": source_row.get("event_id") or event_id,
                "event_type": source_row.get("event_type") or event_type,
                "policy_code": source_row.get("policy_code") or policy_code,
                "event_time": source_row.get("event_time") or event_time,
                "source_id": source_row.get("source_id") or observation.get("source_id"),
                "source_name": source_row.get("source_name") or "rcp_event_feature_list",
                "action": action,
                "feature_row_index": source_row.get("feature_row_index") or row_index,
                "source_field_path": source_row.get("source_field_path"),
                "feature_tab": source_row.get("feature_tab") or "未知",
                "feature_key": source_row.get("feature_key"),
                "feature_name": source_row.get("feature_name") or source_row.get("feature_key"),
                "feature_type": source_row.get("feature_type"),
                "feature_value_or_safe_ref": source_row.get("feature_value_or_safe_ref"),
                "value_present": bool(source_row.get("value_present")),
                "value_comparable": bool(source_row.get("value_comparable")),
                "comparable_type": source_row.get("comparable_type") or "不可比较",
                "sensitive_value_policy": source_row.get("sensitive_value_policy") or "原值可用",
                "candidate_feature_eligible": bool(source_row.get("candidate_feature_eligible")),
                "high_value_reason": source_row.get("high_value_reason"),
                "missing_reason": source_row.get("missing_reason"),
                "mapped_domain": source_row.get("mapped_domain") or "未知",
                "mapped_field_family": source_row.get("mapped_field_family") or "unknown_feature_family",
                "original_feature_row_retained": bool(source_row.get("original_feature_row_retained")),
                "source_quality": source_row.get("source_quality") or quality,
                "evidence_source": source_row.get("evidence_source") or "current_observation",
            }
            rows.append(row)
    return rows


def build_strategy_feature_row_commonality_and_features(
    strategy_event_feature_row_table: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows_by_key: dict[str, list[dict[str, Any]]] = {}
    comparable_value_groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in strategy_event_feature_row_table:
        feature_key = str(row.get("feature_key") or "")
        if not feature_key:
            continue
        rows_by_key.setdefault(feature_key, []).append(row)
        if row.get("value_present") and row.get("value_comparable"):
            value_ref = str(row.get("feature_value_or_safe_ref"))
            comparable_value_groups.setdefault((feature_key, value_ref), []).append(row)

    commonality_rows: list[dict[str, Any]] = []
    for feature_key, rows in rows_by_key.items():
        entities = unique_strings([str(row.get("entity_id")) for row in rows if row.get("entity_id")])
        if len(entities) < 2:
            continue
        example = rows[0]
        commonality_rows.append(
            {
                "signal_name": f"feature_coverage:{feature_key}",
                "commonality_type": "coverage_commonality",
                "feature_key": feature_key,
                "feature_tab": example.get("feature_tab"),
                "source_fields": [feature_key],
                "supporting_current_evidence": entities,
                "support_count": len(entities),
                "batch_support_count": len(entities),
                "commonality_anchor": False,
                "risk_commonality": False,
                "eligible_for_group_candidate": False,
                "candidate_feature_eligible": False,
                "evidence_source": "current_observation",
                "source_name": "strategy_event_feature_row_table",
                "not_final_conclusion": True,
            }
        )

    value_commonality_rows: list[dict[str, Any]] = []
    for (feature_key, value_ref), rows in comparable_value_groups.items():
        entities = unique_strings([str(row.get("entity_id")) for row in rows if row.get("entity_id")])
        if len(entities) < 2:
            continue
        example = rows[0]
        if example.get("candidate_feature_eligible") is not True:
            continue
        commonality = {
            "signal_name": f"feature_value_commonality:{feature_key}",
            "commonality_type": "field_value_commonality",
            "feature_key": feature_key,
            "feature_tab": example.get("feature_tab"),
            "feature_value_or_safe_ref": value_ref,
            "source_fields": [feature_key],
            "supporting_current_evidence": entities,
            "support_count": len(entities),
            "batch_support_count": len(entities),
            "support_ratio": None,
            "commonality_anchor": False,
            "risk_commonality": False,
            "eligible_for_group_candidate": False,
            "candidate_feature_eligible": True,
            "mapped_domain": example.get("mapped_domain"),
            "mapped_field_family": example.get("mapped_field_family"),
            "evidence_source": "current_observation",
            "source_name": "strategy_event_feature_row_table",
            "not_final_conclusion": True,
        }
        commonality_rows.append(commonality)
        value_commonality_rows.append(commonality)

    value_commonality_rows = sorted(
        value_commonality_rows,
        key=lambda item: (
            0 if item.get("feature_tab") == STRATEGY_EVENT_ORIGINAL_FEATURE_TAB else 1,
            -int(item.get("support_count") or 0),
            str(item.get("feature_key") or ""),
        ),
    )
    selected = value_commonality_rows[:6]
    candidate_features: list[dict[str, Any]] = []
    if len(selected) >= 2:
        selected_keys = unique_strings([str(item.get("feature_key")) for item in selected if item.get("feature_key")])
        support_sets = [
            set(str(entity) for entity in item.get("supporting_current_evidence", []) or [] if str(entity))
            for item in selected
        ]
        support_intersection = set.intersection(*support_sets) if support_sets else set()
        support_entities = sorted(support_intersection) if len(support_intersection) >= 2 else unique_strings([
            entity for item in selected for entity in item.get("supporting_current_evidence", []) or []
        ])
        supporting_rows = [
            {
                "sample_id": row.get("sample_id"),
                "entity_id": row.get("entity_id"),
                "round_id": row.get("round_id"),
                "source_id": row.get("source_id"),
                "source_quality": row.get("source_quality"),
                "feature_key": row.get("feature_key"),
                "feature_tab": row.get("feature_tab"),
            }
            for row in strategy_event_feature_row_table
            if str(row.get("feature_key")) in selected_keys and str(row.get("entity_id")) in set(support_entities)
        ]
        if len(support_entities) >= 2:
            candidate_features.append(
                {
                    "feature_name": "strategy_event_original_feature_value_combination_candidate",
                    "source_domains": unique_strings([
                        str(row.get("mapped_domain"))
                        for row in strategy_event_feature_row_table
                        if str(row.get("feature_key")) in selected_keys and row.get("mapped_domain")
                    ]) or ["策略", "行为"],
                    "source_fields": selected_keys,
                    "source_feature_keys": selected_keys,
                    "field_combination": [
                        f"{item.get('feature_key')}={item.get('feature_value_or_safe_ref')}"
                        for item in selected
                    ],
                    "support_sample_count": len(support_entities),
                    "supporting_sample_refs": support_entities,
                    "supporting_current_evidence": supporting_rows,
                    "supporting_feature_rows": supporting_rows,
                    "supporting_selected_anchors": [],
                    "unselected_signal_hypothesis": True,
                    "signal_inputs": [{"evidence_source": "current_observation", "feature_keys": selected_keys}],
                    "hypothesis_inputs": [
                        {
                            "evidence_source": "expert_hypothesis",
                            "signal": "original_tab_field_value_combination_may_indicate_shared_register_or_action_context",
                            "usage_boundary": "hypothesis_only_requires_validation",
                        }
                    ],
                    "black_gray_interpretation": "多个样本在原始类或高价值特征行上出现相同/相近字段值组合，可作为注册入口、客户端环境、网络/地域、设备环境或行为节奏的候选共性输入。",
                    "normal_user_false_positive_risk": "正常 Android/iOS 用户、同地域网络、同版本客户端、活动入口集中也可能形成相同字段组合，需要正常对照和背景率。",
                    "missing_fields_to_check": [
                        "normal_register_or_action_control_group",
                        "field_value_distribution",
                        "device_fingerprint_detail_if_device_related",
                        "frontend_backend_sequence_if_behavior_related",
                    ],
                    "validation_method": "按 feature_key/value 组合在目标批次和正常对照中回放，计算支持样本数、背景率、lift、误伤率和跨轮稳定性。",
                    "strategy_usage_boundary": "候选特征 only: 观察、人审辅助或受控灰度验证；不能直接上线或处置。",
                    "confidence": "medium_partial",
                    "validation_needed": True,
                    "false_positive_risk": "medium",
                    "not_final_conclusion": True,
                }
            )
    return commonality_rows, candidate_features


def _strategy_delta_bucket(value: Any) -> str | None:
    try:
        seconds = int(float(value))
    except (TypeError, ValueError):
        return None
    if seconds <= 60:
        return "login_to_action_delta_le_60s"
    if seconds <= 300:
        return "login_to_action_delta_le_5m"
    return "login_to_action_delta_gt_5m"


def build_strategy_request_detail_features(
    strategy_event_request_detail_table: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    grouped: dict[tuple[str, ...], list[dict[str, Any]]] = {}
    for row in strategy_event_request_detail_table:
        if row.get("entry_label_fields_only") is True:
            continue
        if not any(row.get(field) not in {None, ""} for field in STRATEGY_EVENT_REQUEST_DETAIL_CORE_FIELDS):
            continue
        key = (
            str(row.get("request_path") or "missing_request_path"),
            str(row.get("request_scene") or "missing_request_scene"),
            str(row.get("entry") or "missing_entry"),
            str(row.get("action_type") or "missing_action_type"),
            str(row.get("action_object") or "missing_action_object"),
            str(row.get("task_type") or "missing_task_type"),
            str(row.get("reward_type") or "missing_reward_type"),
            str(row.get("frontend_activity_signal") or "missing_frontend_activity_signal"),
            str(row.get("backend_action_signal") or "missing_backend_action_signal"),
            _strategy_delta_bucket(row.get("time_delta_from_login_seconds")) or "missing_login_delta",
        )
        grouped.setdefault(key, []).append(row)

    shared_signals: list[dict[str, Any]] = []
    candidate_features: list[dict[str, Any]] = []
    for key, rows in grouped.items():
        entities = unique_strings([str(row.get("entity_id")) for row in rows if row.get("entity_id")])
        if len(entities) < 2:
            continue
        source_fields = [
            "request_path",
            "request_scene",
            "entry",
            "action_type",
            "action_object",
            "task_type",
            "reward_type",
            "frontend_activity_signal",
            "backend_action_signal",
            "time_delta_from_login_seconds",
            "app_version",
            "ua",
            "device_id",
            "ip_or_network",
        ]
        field_combination = [
            f"request_path={key[0]}",
            f"request_scene={key[1]}",
            f"entry={key[2]}",
            f"action_type={key[3]}",
            f"action_object={key[4]}",
            f"task_type={key[5]}",
            f"reward_type={key[6]}",
            f"frontend_activity_signal={key[7]}",
            f"backend_action_signal={key[8]}",
            f"time_delta_from_login={key[9]}",
        ]
        evidence = [
            {
                "sample_id": row.get("sample_id"),
                "entity_id": row.get("entity_id"),
                "round_id": row.get("round_id"),
                "source_id": row.get("source_id"),
                "source_quality": row.get("source_quality"),
            }
            for row in rows
        ]
        feature_name = "strategy_request_detail_shared_behavior_candidate"
        shared_signals.append(
            {
                "signal_name": feature_name,
                "commonality_type": "field_level_request_detail_commonality",
                "source_fields": source_fields,
                "field_combination": field_combination,
                "supporting_current_evidence": entities,
                "support_count": len(entities),
                "batch_support_count": len(entities),
                "support_ratio": None,
                "commonality_anchor": False,
                "risk_commonality": False,
                "eligible_for_group_candidate": False,
                "evidence_source": "current_observation",
                "source_name": "strategy_event_request_detail_table",
                "not_final_conclusion": True,
            }
        )
        candidate_features.append(
            {
                "feature_name": feature_name,
                "source_domains": ["strategy_domain", "behavior_domain"],
                "source_fields": source_fields,
                "field_combination": field_combination,
                "support_sample_count": len(entities),
                "supporting_current_evidence": evidence,
                "supporting_selected_anchors": unique_strings([
                    str(row.get("event_id") or row.get("policy_code") or row.get("source_id"))
                    for row in rows
                    if row.get("event_id") or row.get("policy_code") or row.get("source_id")
                ]),
                "signal_inputs": [{"evidence_source": "current_observation", "signals": [feature_name]}],
                "hypothesis_inputs": [
                    {
                        "evidence_source": "expert_hypothesis",
                        "signal": "strategy_request_detail_field_combination_may_indicate_automation_or_low_human_interaction",
                        "usage_boundary": "hypothesis_only_requires_validation",
                    }
                ],
                "black_gray_interpretation": "Similar request path, action object, client context, and login-to-action timing can indicate scripted task execution, reward abuse, or low-human-interaction behavior.",
                "normal_user_false_positive_risk": "Campaign users may legitimately perform similar actions shortly after login; request detail must be compared against a normal control group.",
                "missing_fields_to_check": unique_strings([
                    missing
                    for row in rows
                    for missing in row.get("missing_request_detail_fields", []) or []
                    if missing
                ] + [
                    "normal_control_group_background_rate",
                    "device_fingerprint_environment",
                    "full_request_param_distribution",
                    "frontend_action_sequence",
                    "reward_or_business_outcome",
                ]),
                "validation_method": "Replay this request-detail field combination on the target batch and a normal control group; measure support ratio, background rate, lift, false-positive review rate, and cross-round stability.",
                "strategy_usage_boundary": "Candidate only: observation, manual-review assist, or controlled gray validation. Do not auto-launch or auto-dispose.",
                "confidence": "medium_partial",
                "validation_needed": True,
                "false_positive_risk": "medium",
                "not_final_conclusion": True,
            }
        )
    return shared_signals, candidate_features


def _detail_table_for_action(action: str, canonical_field: str) -> str | None:
    if action in SOURCE_ACTION_DETAIL_TABLES:
        return SOURCE_ACTION_DETAIL_TABLES[action]
    family = FIELD_FAMILY_BY_CANONICAL_FIELD.get(canonical_field)
    if not family:
        return None
    for table_name, families in FIELD_FAMILIES_BY_DETAIL_TABLE.items():
        if family in families:
            return table_name
    return None


def _field_family_for_detail(field_name: str, detail_table: str) -> str:
    canonical = str(field_name or "")
    family = FIELD_FAMILY_BY_CANONICAL_FIELD.get(canonical)
    if family:
        return family
    normalized = re.sub(r"[^a-z0-9]", "", canonical.lower())
    for key, value in FIELD_FAMILY_BY_CANONICAL_FIELD.items():
        if re.sub(r"[^a-z0-9]", "", key.lower()) == normalized:
            return value
    if detail_table == "login_detail_table":
        return "login_unknown_field_family"
    if detail_table in {"account_detail_table", "user_behavior_summary_detail_table"}:
        return "account_unknown_field_family"
    if detail_table == "content_detail_table":
        return "content_unknown_field_family"
    if detail_table == "social_detail_table":
        return "social_unknown_field_family"
    if detail_table == "feedback_detail_table":
        return "feedback_unknown_field_family"
    if detail_table == "enforcement_detail_table":
        return "enforcement_unknown_field_family"
    return "unknown_field_family"


def _standard_comparable_type(value: Any) -> str:
    if isinstance(value, bool):
        return "布尔"
    if isinstance(value, (int, float)):
        return "数值分桶"
    text = str(value or "")
    if not text:
        return "不可比较"
    if re.search(r"\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{10,13}", text):
        return "时间差"
    if len(text) > 128:
        return "文本相似"
    return "等值"


def _source_shape_for_action(action: str, observation: dict[str, Any] | None = None) -> str:
    explicit = str((observation or {}).get("source_shape") or "").strip()
    if explicit:
        return explicit
    if action in MULTI_ROW_EVENT_ACTIONS:
        return "multi_row_event"
    if action in SINGLE_OBJECT_WIDE_FIELD_ACTIONS:
        return "single_object_wide_field"
    return "unknown"


def _source_domain_for_detail_table_or_action(detail_table: str | None, action: str) -> str:
    if detail_table:
        return DETAIL_TABLE_SOURCE_DOMAINS.get(detail_table, "unknown_domain")
    domains = INTERFACE_OBSERVATION_DOMAINS.get(action) or []
    return domains[0] if domains else "unknown_domain"


def _value_handling_for_field(field_name: str, value: Any) -> tuple[str, str, Any]:
    if _is_credential_secret_key(field_name):
        return "redacted", "credential", "redacted_safe_ref"
    text = str(value or "")
    if len(text) > 2048:
        return "summarized", "oversized_body", f"long_value_len_{len(text)}"
    return "raw_retained", "none", value


def _raw_value_type(value: Any) -> str:
    if value is None:
        return "missing"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return "string"


def _raw_flat_row(
    *,
    observation_id: str,
    source_name: str,
    source_domain: str,
    source_shape: str,
    layer: str,
    parent_observation_id: str | None,
    anchor_lineage: list[dict[str, Any]] | None,
    entity_id: str,
    entity_type: str,
    record_index: int | None,
    record_time: Any,
    field_path: str,
    field_name: str,
    field_value: Any,
    field_family: str,
    source_quality: str,
    missing_or_partial_reason: str | None,
    extraction_quality: str,
) -> dict[str, Any] | None:
    if not field_name:
        return None
    value_handling, redaction_reason, stored_value = _value_handling_for_field(field_name, field_value)
    if value_handling == "redacted" and redaction_reason == "credential":
        value_comparable = False
        comparable_reason = "credential_filtered"
    else:
        comparable_type = _standard_comparable_type(stored_value)
        value_comparable = comparable_type != "不可比较"
        comparable_reason = comparable_type
    unknown = field_family.endswith("_unknown_field_family") or field_family in {
        "unknown_field_family",
        "unknown_device_field_family",
        "unknown_feature_family",
    }
    return {
        "observation_id": observation_id,
        "parent_observation_id": parent_observation_id,
        "layer": layer,
        "anchor_lineage": anchor_lineage or [],
        "source_name": source_name,
        "source_domain": source_domain,
        "source_shape": source_shape,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "record_index": record_index,
        "record_time": record_time,
        "field_path": _safe_field_path(field_path),
        "field_name": field_name,
        "field_value_raw_or_ref": stored_value,
        "field_value_type": _raw_value_type(field_value),
        "value_handling": value_handling,
        "redaction_reason": redaction_reason,
        "field_family": field_family,
        "field_family_confidence": "mapped" if not unknown else "unknown",
        "value_comparable": value_comparable,
        "comparable_reason": comparable_reason,
        "source_quality": source_quality,
        "missing_or_partial_reason": missing_or_partial_reason,
        "extraction_quality": extraction_quality,
        "is_unknown_field": unknown,
        "needs_field_dictionary_review": unknown,
    }


def build_raw_detail_flat_table(
    *,
    round_id: int,
    sampled_entities: list[str],
    source_observations: list[dict[str, Any]],
    strategy_event_feature_row_table: list[dict[str, Any]],
    device_detail_table: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for observation in source_observations:
        action = str(observation.get("action") or "")
        quality = str(observation.get("quality_class") or "unknown")
        if quality not in {"completed", "partial"}:
            continue
        source_id = str(observation.get("source_id") or action or "unknown_source")
        entity_id = _source_detail_entity_id(observation, sampled_entities)
        entity_type = _infer_seed_entity_type(entity_id)
        source_shape = _source_shape_for_action(action, observation)
        detail_table_hint = SOURCE_ACTION_DETAIL_TABLES.get(action)
        source_domain = _source_domain_for_detail_table_or_action(detail_table_hint, action)
        missing_reason = None if quality == "completed" else quality
        for handle in observation.get("parsed_body_field_handles", []) or []:
            if not isinstance(handle, dict):
                continue
            field_name = str(handle.get("canonical_field") or handle.get("field") or "").strip()
            raw_field_name = str(handle.get("field") or field_name).strip()
            if not field_name or _is_credential_secret_key(field_name) or _is_credential_secret_key(raw_field_name):
                continue
            detail_table = _detail_table_for_action(action, field_name) or detail_table_hint
            field_family = _field_family_for_detail(field_name, detail_table or "")
            row = _raw_flat_row(
                observation_id=source_id,
                parent_observation_id=str(observation.get("parent_observation_id") or observation.get("parent_source_id") or ""),
                layer=str(observation.get("layer") or observation.get("source_layer") or "L1_source_observation"),
                anchor_lineage=observation.get("anchor_lineage") if isinstance(observation.get("anchor_lineage"), list) else [],
                source_name=action,
                source_domain=_source_domain_for_detail_table_or_action(detail_table, action),
                source_shape=source_shape,
                entity_id=entity_id,
                entity_type=entity_type,
                record_index=handle.get("record_index"),
                record_time=handle.get("record_time") or handle.get("event_time"),
                field_path=str(handle.get("field_path") or ""),
                field_name=field_name,
                field_value=handle.get("value"),
                field_family=field_family,
                source_quality=quality,
                missing_or_partial_reason=missing_reason,
                extraction_quality="parsed_body_field_handle",
            )
            if row is not None:
                rows.append(row)
    for feature_row in strategy_event_feature_row_table:
        feature_key = str(feature_row.get("feature_key") or "").strip()
        if not feature_key or _is_credential_secret_key(feature_key):
            continue
        row = _raw_flat_row(
            observation_id=str(feature_row.get("source_id") or "rcp_event_feature_list"),
            parent_observation_id=str(feature_row.get("parent_observation_id") or feature_row.get("parent_source_id") or ""),
            layer=str(feature_row.get("layer") or "L2_anchor_drilldown_observation"),
            anchor_lineage=feature_row.get("anchor_lineage") if isinstance(feature_row.get("anchor_lineage"), list) else [],
            source_name="rcp_event_feature_list",
            source_domain="strategy_domain",
            source_shape="single_object_wide_field",
            entity_id=str(feature_row.get("entity_id") or feature_row.get("user_id") or ""),
            entity_type="user_id",
            record_index=feature_row.get("feature_row_index"),
            record_time=feature_row.get("event_time"),
            field_path=str(feature_row.get("source_field_path") or feature_row.get("field_path") or ""),
            field_name=feature_key,
            field_value=feature_row.get("feature_value_or_safe_ref"),
            field_family=str(feature_row.get("mapped_field_family") or "unknown_feature_family"),
            source_quality=str(feature_row.get("source_quality") or "completed"),
            missing_or_partial_reason=None,
            extraction_quality="strategy_event_feature_row",
        )
        if row is not None:
            rows.append(row)
    for device_row in device_detail_table:
        field_key = str(device_row.get("device_field_key") or "").strip()
        if not field_key or _is_credential_secret_key(field_key):
            continue
        row = _raw_flat_row(
            observation_id=str(device_row.get("source_id") or "device_detail"),
            parent_observation_id=str(device_row.get("parent_observation_id") or device_row.get("parent_source_id") or ""),
            layer=str(device_row.get("layer") or "L2_anchor_drilldown_observation"),
            anchor_lineage=device_row.get("anchor_lineage") if isinstance(device_row.get("anchor_lineage"), list) else [],
            source_name=str(device_row.get("source_name") or device_row.get("action") or "device_detail"),
            source_domain="device_domain",
            source_shape="single_object_wide_field",
            entity_id=str(device_row.get("entity_id") or device_row.get("user_id") or ""),
            entity_type="device_id" if device_row.get("device_id") else "user_id",
            record_index=None,
            record_time=device_row.get("event_time") or device_row.get("query_time"),
            field_path=str(device_row.get("field_path") or device_row.get("source_field_path") or ""),
            field_name=field_key,
            field_value=device_row.get("device_field_value_or_safe_ref"),
            field_family=str(device_row.get("mapped_field_family") or "unknown_device_field_family"),
            source_quality=str(device_row.get("source_quality") or "completed"),
            missing_or_partial_reason=None,
            extraction_quality="device_detail_row",
        )
        if row is not None:
            rows.append(row)
    deduped: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, str, str]] = set()
    for row in rows:
        identity = (
            str(row.get("observation_id") or ""),
            str(row.get("record_index") or ""),
            str(row.get("field_path") or ""),
            str(row.get("field_name") or ""),
            str(row.get("field_value_raw_or_ref") or ""),
        )
        if identity in seen:
            continue
        seen.add(identity)
        deduped.append(row)
    return deduped


def _source_detail_entity_id(observation: dict[str, Any], sampled_entities: list[str]) -> str:
    for handle in observation.get("parsed_body_field_handles", []) or []:
        if not isinstance(handle, dict):
            continue
        canonical = str(handle.get("canonical_field") or handle.get("field") or "")
        value = str(handle.get("value") or "").strip()
        if canonical == "user_id" and value:
            return value
    return _observation_entity_for_round(observation, sampled_entities)


def build_standard_detail_table(
    *,
    round_id: int,
    sampled_entities: list[str],
    source_observations: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for observation in source_observations:
        action = str(observation.get("action") or "")
        quality = str(observation.get("quality_class") or "unknown")
        if quality not in {"completed", "partial"}:
            continue
        source_id = str(observation.get("source_id") or action or "unknown_source")
        entity_id = _source_detail_entity_id(observation, sampled_entities)
        for handle in observation.get("parsed_body_field_handles", []) or []:
            if not isinstance(handle, dict):
                continue
            field_name = str(handle.get("canonical_field") or handle.get("field") or "").strip()
            raw_field_name = str(handle.get("field") or field_name).strip()
            if not field_name or _is_credential_secret_key(field_name) or _is_credential_secret_key(raw_field_name):
                continue
            detail_table = _detail_table_for_action(action, field_name)
            if detail_table is None:
                continue
            value = handle.get("value")
            if value is None or value == "":
                continue
            comparable_type = _standard_comparable_type(value)
            field_family = _field_family_for_detail(field_name, detail_table)
            source_domain = DETAIL_TABLE_SOURCE_DOMAINS.get(detail_table, "unknown_domain")
            rows.append(
                {
                    "sample_id": f"round_{round_id}_{entity_id}",
                    "entity_id": entity_id,
                    "entity_type": _infer_seed_entity_type(entity_id),
                    "round_id": round_id,
                    "source_id": source_id,
                    "source_name": action,
                    "source_domain": source_domain,
                    "action": action,
                    "detail_table": detail_table,
                    "field_name": field_name,
                    "raw_field_name": raw_field_name,
                    "field_value_or_safe_ref": str(value),
                    "field_family": field_family,
                    "value_present": True,
                    "value_comparable": comparable_type != "不可比较",
                    "comparable_type": comparable_type,
                    "source_quality": quality,
                    "evidence_source": "current_observation",
                    "extracted_from_observation_id": source_id,
                    "field_path": _safe_field_path(str(handle.get("field_path") or "")),
                    "missing_or_partial_reason": None if quality == "completed" else quality,
                    "unknown_field_family": field_family.endswith("_unknown_field_family") or field_family == "unknown_field_family",
                }
            )
    deduped: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, str, str]] = set()
    for row in rows:
        identity = (
            str(row.get("sample_id") or ""),
            str(row.get("source_id") or ""),
            str(row.get("detail_table") or ""),
            str(row.get("field_name") or ""),
            str(row.get("field_value_or_safe_ref") or ""),
        )
        if identity in seen:
            continue
        seen.add(identity)
        deduped.append(row)
    return deduped


def _detail_rows_by_table(standard_detail_table: list[dict[str, Any]], table_name: str) -> list[dict[str, Any]]:
    return [row for row in standard_detail_table if row.get("detail_table") == table_name]


def build_source_field_volume_summary(
    *,
    source_observations: list[dict[str, Any]],
    standard_detail_table: list[dict[str, Any]],
    strategy_event_feature_row_table: list[dict[str, Any]],
    device_detail_table: list[dict[str, Any]],
) -> dict[str, Any]:
    summary: dict[str, dict[str, Any]] = {}

    def bucket(source_id: str, action: str) -> dict[str, Any]:
        key = source_id or action or "unknown_source"
        return summary.setdefault(
            key,
            {
                "source_id": source_id,
                "action": action,
                "raw_input_field_count": 0,
                "parsed_detail_field_count": 0,
                "standard_detail_field_count": 0,
                "commonality_eligible_field_count": 0,
                "detail_row_count": 0,
                "_raw_fields": set(),
                "_parsed_fields": set(),
                "_standard_fields": set(),
                "_eligible_fields": set(),
            },
        )

    for observation in source_observations:
        source_id = str(observation.get("source_id") or "")
        action = str(observation.get("action") or "")
        row = bucket(source_id, action)
        for handle in observation.get("parsed_body_field_handles", []) or []:
            if not isinstance(handle, dict):
                continue
            field_name = str(handle.get("canonical_field") or handle.get("field") or "").strip()
            raw_field = str(handle.get("field") or field_name).strip()
            if raw_field and not _is_credential_secret_key(raw_field):
                row["_raw_fields"].add(raw_field)
            if field_name and not _is_credential_secret_key(field_name):
                row["_parsed_fields"].add(field_name)
        for feature_row in observation.get("strategy_event_feature_rows", []) or []:
            if not isinstance(feature_row, dict):
                continue
            feature_key = str(feature_row.get("feature_key") or "").strip()
            if feature_key and not _is_credential_secret_key(feature_key):
                row["_raw_fields"].add(feature_key)
                row["_parsed_fields"].add(feature_key)
        for device_row in observation.get("device_detail_rows", []) or []:
            if not isinstance(device_row, dict):
                continue
            field_key = str(device_row.get("device_field_key") or "").strip()
            if field_key and not _is_credential_secret_key(field_key):
                row["_raw_fields"].add(field_key)
                row["_parsed_fields"].add(field_key)

    for detail_row in standard_detail_table:
        source_id = str(detail_row.get("source_id") or "")
        action = str(detail_row.get("action") or detail_row.get("source_name") or "")
        row = bucket(source_id, action)
        field_name = str(detail_row.get("field_name") or "").strip()
        if field_name:
            row["_standard_fields"].add(field_name)
            row["detail_row_count"] += 1
            if detail_row.get("value_comparable") is True:
                row["_eligible_fields"].add(field_name)

    for feature_row in strategy_event_feature_row_table:
        source_id = str(feature_row.get("source_id") or "")
        action = str(feature_row.get("action") or feature_row.get("source_name") or "rcp_event_feature_list")
        row = bucket(source_id, action)
        feature_key = str(feature_row.get("feature_key") or "").strip()
        if feature_key:
            row["_standard_fields"].add(feature_key)
            row["detail_row_count"] += 1
            if feature_row.get("value_comparable") is True:
                row["_eligible_fields"].add(feature_key)

    for device_row in device_detail_table:
        source_id = str(device_row.get("source_id") or "")
        action = str(device_row.get("action") or device_row.get("source_name") or "")
        row = bucket(source_id, action)
        field_key = str(device_row.get("device_field_key") or device_row.get("field_name") or "").strip()
        if field_key:
            row["_standard_fields"].add(field_key)
            row["detail_row_count"] += 1
            if device_row.get("value_comparable") is True:
                row["_eligible_fields"].add(field_key)

    public_rows: list[dict[str, Any]] = []
    for row in summary.values():
        raw_count = len(row.pop("_raw_fields"))
        parsed_count = len(row.pop("_parsed_fields"))
        standard_count = len(row.pop("_standard_fields"))
        eligible_count = len(row.pop("_eligible_fields"))
        row["raw_input_field_count"] = raw_count
        row["parsed_detail_field_count"] = parsed_count
        row["standard_detail_field_count"] = standard_count
        row["commonality_eligible_field_count"] = eligible_count
        row["source_payload_thin"] = False
        if eligible_count < 20 and str(row.get("action") or "") not in {"rcp_fast_query_hbase"}:
            if raw_count >= 20 and standard_count < 20:
                status = "parser_under_extraction_gap"
            elif raw_count == 0:
                status = "source_detail_not_returned_or_body_visibility_gap"
            elif raw_count < 20:
                status = "source_payload_thin"
                row["source_payload_thin"] = True
            else:
                status = "below_commonality_feature_floor"
        elif str(row.get("action") or "") == "rcp_fast_query_hbase":
            status = "entry_anchor_source_not_core_feature_source"
        else:
            status = "commonality_field_volume_ok"
        row["field_volume_status"] = status
        public_rows.append(row)
    return {
        "minimum_expected_commonality_eligible_fields": 50,
        "low_field_count_gap_threshold": 20,
        "detail_row_count_is_not_feature_count": True,
        "sources": sorted(public_rows, key=lambda item: str(item.get("source_id") or "")),
    }


def build_raw_detail_flat_table_summary(raw_detail_flat_table: list[dict[str, Any]]) -> dict[str, Any]:
    by_source: dict[str, dict[str, Any]] = {}
    for row in raw_detail_flat_table:
        source_name = str(row.get("source_name") or "unknown_source")
        bucket = by_source.setdefault(
            source_name,
            {
                "source_name": source_name,
                "source_shape": row.get("source_shape"),
                "raw_record_count": 0,
                "raw_field_count": 0,
                "flattened_field_count": 0,
                "comparable_field_count": 0,
                "unknown_field_count": 0,
                "filtered_field_count": 0,
                "filtered_reasons": {},
                "retained_raw_anchor_count": 0,
                "_records": set(),
                "_fields": set(),
                "_comparable": set(),
                "_unknown": set(),
                "_anchors": set(),
            },
        )
        record_key = (row.get("observation_id"), row.get("record_index"))
        bucket["_records"].add(record_key)
        field_name = str(row.get("field_name") or "")
        if field_name:
            bucket["_fields"].add(field_name)
            if row.get("value_comparable") is True:
                bucket["_comparable"].add(field_name)
            if row.get("is_unknown_field") is True:
                bucket["_unknown"].add(field_name)
            if field_name in {"user_id", "device_id", "did", "ip", "ua", "photo_id", "item_id", "event_id", "policy_code", "source_id"}:
                bucket["_anchors"].add(field_name)
        if row.get("value_handling") == "redacted":
            reason = str(row.get("redaction_reason") or "unknown")
            bucket["filtered_reasons"][reason] = int(bucket["filtered_reasons"].get(reason, 0)) + 1
    public_rows: list[dict[str, Any]] = []
    for bucket in by_source.values():
        bucket["raw_record_count"] = len(bucket.pop("_records"))
        field_count = len(bucket.pop("_fields"))
        bucket["raw_field_count"] = field_count
        bucket["flattened_field_count"] = field_count
        bucket["comparable_field_count"] = len(bucket.pop("_comparable"))
        bucket["unknown_field_count"] = len(bucket.pop("_unknown"))
        bucket["retained_raw_anchor_count"] = len(bucket.pop("_anchors"))
        source_shape = str(bucket.get("source_shape") or "")
        if source_shape == "single_object_wide_field" and bucket["flattened_field_count"] < 50:
            status = "P1_wide_source_under_flattened"
        elif source_shape == "multi_row_event" and bucket["flattened_field_count"] < 20:
            status = "P1_multi_row_source_under_flattened"
        else:
            status = "ok"
        bucket["field_volume_status"] = status
        public_rows.append(bucket)
    return {
        "row_count": len(raw_detail_flat_table),
        "source_count": len(public_rows),
        "sources": sorted(public_rows, key=lambda item: str(item.get("source_name") or "")),
    }


def _source_quality_bucket_from_observation(observation: dict[str, Any]) -> str:
    quality = str(observation.get("quality_class") or "unknown")
    if quality in {"completed", "partial", "no_data", "timeout", "auth_failed", "blocked", "parse_error", "planned"}:
        return quality
    return "unknown"


def _source_layer_from_observation(observation: dict[str, Any]) -> str:
    layer = str(observation.get("layer") or observation.get("source_layer") or "")
    if layer.startswith("L2"):
        return "L2"
    if layer.startswith("L1"):
        return "L1"
    if "anchor" in layer.lower():
        return "L2"
    return "L1"


def _source_quality_threshold(action: str, source_shape: str) -> int:
    if action == "weapon_device_info":
        return 100
    if action == "rcp_event_feature_list":
        return 100
    if action == "weapon_device_app_list":
        return 8
    if source_shape == "single_object_wide_field":
        return 50
    if source_shape == "multi_row_event":
        return 20
    return 20


def _source_next_action_from_quality(
    *,
    auth_blocked: bool,
    parser_under_expanded: bool,
    action_mapping_incomplete: bool,
    source_payload_thin: bool,
    repeated_item_list_schema_narrow: bool,
    dynamic_event_table_capped: bool,
    not_entered_main_chain: bool,
) -> str:
    if auth_blocked:
        return "fix_auth_or_page_state_before_l3"
    if action_mapping_incomplete:
        return "repair_action_mapping_or_required_params"
    if parser_under_expanded:
        return "expand_raw_fields_into_standard_detail_table"
    if dynamic_event_table_capped:
        return "increase_event_feature_row_retention_or_pagination"
    if repeated_item_list_schema_narrow:
        return "compare_item_rows_not_only_flat_field_count"
    if source_payload_thin:
        return "accept_thin_source_as_auxiliary_or_enrich_with_adjacent_source"
    if not_entered_main_chain:
        return "wire_source_into_default_l1_l2_chain"
    return "ready_for_l3_field_value_combination_sequence_compare"


def build_l3_source_input_quality_table(
    *,
    source_plan: list[SourcePlanItem],
    source_observations: list[dict[str, Any]],
    raw_detail_flat_table_summary: dict[str, Any],
    source_field_volume_summary: dict[str, Any],
) -> list[dict[str, Any]]:
    raw_by_source = {
        str(item.get("source_name") or ""): item
        for item in raw_detail_flat_table_summary.get("sources", []) or []
        if isinstance(item, dict)
    }
    volume_by_action = {
        str(item.get("action") or ""): item
        for item in source_field_volume_summary.get("sources", []) or []
        if isinstance(item, dict)
    }
    observations_by_action: dict[str, list[dict[str, Any]]] = {}
    for observation in source_observations:
        action = str(observation.get("action") or "")
        if not action:
            continue
        observations_by_action.setdefault(action, []).append(observation)

    planned_actions = [item.action for item in source_plan]
    relevant_actions = unique_strings(planned_actions + list(observations_by_action.keys()) + list(raw_by_source.keys()) + list(volume_by_action.keys()))
    rows: list[dict[str, Any]] = []
    for action in relevant_actions:
        observations = observations_by_action.get(action, [])
        raw_summary = raw_by_source.get(action, {})
        volume_summary = volume_by_action.get(action, {})
        role = SOURCE_ROLE_BY_ACTION.get(action, "primary_detail_source")
        source_domain = str(_source_domain_for_detail_table_or_action(SOURCE_ACTION_DETAIL_TABLES.get(action), action))
        source_shape = str(raw_summary.get("source_shape") or _source_shape_for_action(action))
        layer = "L2" if any(_source_layer_from_observation(observation) == "L2" for observation in observations) else "L1"
        quality_buckets = [_source_quality_bucket_from_observation(observation) for observation in observations]
        source_status = "not_entered" if not observations else (
            "completed" if "completed" in quality_buckets else
            "partial" if "partial" in quality_buckets else
            "auth_failed" if "auth_failed" in quality_buckets else
            "blocked" if "blocked" in quality_buckets else
            quality_buckets[0]
        )
        interpretation_flags = {
            str(flag)
            for observation in observations
            for flag in observation.get("interpretation_flags", []) or []
            if flag
        }
        breakpoint_types = [
            str(observation.get("breakpoint_type") or "")
            for observation in observations
            if observation.get("breakpoint_type")
        ]
        raw_record_count = int(raw_summary.get("raw_record_count") or 0)
        raw_field_count = int(raw_summary.get("raw_field_count") or volume_summary.get("raw_input_field_count") or 0)
        flattened_field_count = int(raw_summary.get("flattened_field_count") or volume_summary.get("parsed_detail_field_count") or 0)
        comparable_field_count = int(raw_summary.get("comparable_field_count") or volume_summary.get("commonality_eligible_field_count") or 0)
        unknown_field_count = int(raw_summary.get("unknown_field_count") or 0)
        filtered_field_count = int(raw_summary.get("filtered_field_count") or 0)
        threshold = _source_quality_threshold(action, source_shape)
        source_payload_thin = bool(volume_summary.get("source_payload_thin") is True)
        parser_under_expanded = (
            raw_field_count >= threshold
            and max(flattened_field_count, comparable_field_count) < threshold
            and action not in {"weapon_device_app_list"}
        ) or any(flag in interpretation_flags for flag in {"observation_compression_gap", "service_body_visibility_gap"})
        repeated_item_list_schema_narrow = (
            action == "weapon_device_app_list"
            and raw_record_count >= 20
            and comparable_field_count <= threshold
        )
        dynamic_event_table_capped = (
            action == "rcp_event_feature_list"
            and (
                "feature_list_partial_only_feature_group_summary" in interpretation_flags
                or comparable_field_count < threshold
            )
        )
        auth_blocked = (
            source_status == "auth_failed"
            or any("auth" in value or "session" in value for value in breakpoint_types)
        )
        action_mapping_incomplete = (
            any(value in {"invalid_parameter", "missing_required_fields", "missing_contract"} for value in breakpoint_types)
            or "tool_gap" in interpretation_flags
        )
        not_entered_main_chain = source_status == "not_entered"
        primary_blocked_reason = (
            breakpoint_types[0]
            if breakpoint_types else
            "auth_blocked" if auth_blocked else
            "source_not_executed_in_current_chain" if not_entered_main_chain else
            "none"
        )
        if not_entered_main_chain:
            l3_input_quality = "not_entered"
        elif auth_blocked:
            l3_input_quality = "blocked"
        elif parser_under_expanded or action_mapping_incomplete:
            l3_input_quality = "weak"
        elif source_payload_thin and role != "primary_detail_source":
            l3_input_quality = "weak"
        elif comparable_field_count >= threshold:
            l3_input_quality = "strong"
        elif comparable_field_count >= max(8, threshold // 2):
            l3_input_quality = "medium"
        else:
            l3_input_quality = "weak"
        rows.append(
            {
                "source_name": action,
                "source_domain": source_domain,
                "source_role": role,
                "source_shape": source_shape,
                "layer": layer,
                "source_status": source_status,
                "raw_record_count": raw_record_count,
                "raw_field_count": raw_field_count,
                "flattened_field_count": flattened_field_count,
                "comparable_field_count": comparable_field_count,
                "unknown_field_count": unknown_field_count,
                "filtered_field_count": filtered_field_count,
                "source_payload_thin": source_payload_thin,
                "parser_under_expanded": parser_under_expanded,
                "action_mapping_incomplete": action_mapping_incomplete,
                "auth_blocked": auth_blocked,
                "not_entered_main_chain": not_entered_main_chain,
                "repeated_item_list_schema_narrow": repeated_item_list_schema_narrow,
                "source_role_is_auxiliary": role != "primary_detail_source",
                "dynamic_event_table_capped": dynamic_event_table_capped,
                "primary_blocked_reason": primary_blocked_reason,
                "l3_input_quality": l3_input_quality,
                "next_action": _source_next_action_from_quality(
                    auth_blocked=auth_blocked,
                    parser_under_expanded=parser_under_expanded,
                    action_mapping_incomplete=action_mapping_incomplete,
                    source_payload_thin=source_payload_thin,
                    repeated_item_list_schema_narrow=repeated_item_list_schema_narrow,
                    dynamic_event_table_capped=dynamic_event_table_capped,
                    not_entered_main_chain=not_entered_main_chain,
                ),
            }
        )
    priority_rank = {
        "strategy_domain": 0,
        "device_domain": 1,
        "behavior_domain": 2,
        "account_domain": 3,
        "content_domain": 4,
        "social_domain": 5,
        "feedback_domain": 6,
        "enforcement_domain": 7,
    }
    return sorted(rows, key=lambda item: (priority_rank.get(str(item.get("source_domain") or ""), 99), str(item.get("source_name") or "")))


def _detail_candidate_priority(table_name: str, support_ratio: float, source_domains: list[str]) -> dict[str, Any]:
    score = 20 + support_ratio * 40
    reason_codes = [f"support_ratio={support_ratio:.4f}", "L3_candidate_only", "baseline_not_evaluated_in_L3"]
    if len(source_domains) >= 2:
        score += 10
        reason_codes.append("cross_domain_support")
    if table_name in {"login_detail_table", "content_detail_table", "social_detail_table"}:
        score += 8
        reason_codes.append("high_value_source_family")
    if score >= 65:
        level = "high"
    elif score >= 40:
        level = "medium"
    else:
        level = "low"
    return {
        "priority_score": round(score, 2),
        "priority_level": level,
        "reason_codes": reason_codes,
    }


def build_sequence_comparison_features(
    *,
    raw_detail_flat_table: list[dict[str, Any]],
    sampled_entities: list[str],
) -> list[dict[str, Any]]:
    rows_by_source_entity: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in raw_detail_flat_table:
        if row.get("source_shape") != "multi_row_event":
            continue
        if row.get("value_comparable") is not True:
            continue
        key = (str(row.get("source_name") or ""), str(row.get("entity_id") or ""))
        rows_by_source_entity.setdefault(key, []).append(row)

    sequence_rows: list[dict[str, Any]] = []
    sampled_denominator = max(len(sampled_entities), 1)
    for (source_name, entity_id), rows in sorted(rows_by_source_entity.items()):
        record_indexes = sorted({
            int(row.get("record_index"))
            for row in rows
            if isinstance(row.get("record_index"), int)
        })
        if len(record_indexes) < 2:
            continue
        fields = unique_strings([str(row.get("field_name") or "") for row in rows if row.get("field_name")])
        values_by_field: dict[str, set[str]] = {}
        for row in rows:
            values_by_field.setdefault(str(row.get("field_name") or ""), set()).add(str(row.get("field_value_raw_or_ref") or ""))
        repeated_fields = sorted([
            field for field, values in values_by_field.items()
            if field and len(values) == 1 and next(iter(values), "") != ""
        ])
        changing_fields = sorted([
            field for field, values in values_by_field.items()
            if field and len(values) > 1
        ])
        if source_name == "login_logs_search":
            feature_type = "login_sequence_comparison_candidate"
            feature_name = "login_multi_record_device_network_client_sequence_candidate"
            interpretation = "同一实体多条登录记录里，登录端、设备、网络、客户端或结果序列出现可比较变化/重复，可作为控制链候选输入。"
        elif source_name == "archives_user_analysis":
            feature_type = "user_behavior_sequence_comparison_candidate"
            feature_name = "user_behavior_action_rhythm_sequence_candidate"
            interpretation = "用户分析多条行为记录形成动作节奏或资料维护序列，可作为账号态/行为节奏候选输入。"
        elif source_name in {"archives_photo_search", "archives_gallery_photo_list", "archives_photo_profile", "archives_photo_meta"}:
            feature_type = "content_sequence_comparison_candidate"
            feature_name = "content_publish_sequence_candidate"
            interpretation = "内容多条记录在发布时间、发布端、模板或审核字段上形成序列共性，可作为内容承接候选输入。"
        elif source_name in {"archives_comment_search", "archives_private_message_search", "archives_livestream_comment_detail"}:
            feature_type = "social_sequence_comparison_candidate"
            feature_name = "social_target_wording_path_sequence_candidate"
            interpretation = "社交多条记录在对象、话术或路径上形成重复/变化，可作为社交承接候选输入。"
        elif source_name in {"archives_user_report_search", "archives_negative_report", "archives_review_logs", "archives_punish_status"}:
            feature_type = "feedback_enforcement_sequence_comparison_candidate"
            feature_name = "feedback_enforcement_timeline_sequence_candidate"
            interpretation = "反馈/处置多条记录形成时间线或类型重复，只能作为治理状态候选输入，不代表风险事实。"
        else:
            feature_type = "multi_row_sequence_comparison_candidate"
            feature_name = f"{source_name}_multi_row_sequence_candidate"
            interpretation = "多行事件记录形成字段重复或变化，可作为 L3 候选输入。"
        sequence_rows.append(
            {
                "source_name": source_name,
                "entity_type": _infer_seed_entity_type(entity_id),
                "entity_id": entity_id,
                "event_count": len(record_indexes),
                "time_window_start": min([str(row.get("record_time")) for row in rows if row.get("record_time")] or ["unknown"]),
                "time_window_end": max([str(row.get("record_time")) for row in rows if row.get("record_time")] or ["unknown"]),
                "sequence_feature_name": feature_name,
                "sequence_feature_type": feature_type,
                "involved_record_indexes": record_indexes,
                "involved_fields": fields,
                "observed_pattern": {
                    "repeated_fields": repeated_fields[:20],
                    "changing_fields": changing_fields[:20],
                },
                "comparable_values": {
                    field: sorted(values)[:5]
                    for field, values in values_by_field.items()
                    if field in set(repeated_fields[:10] + changing_fields[:10])
                },
                "support_record_count": len(record_indexes),
                "support_entity_count": 1,
                "support_ratio": round(1 / sampled_denominator, 4),
                "time_delta_summary": "not_computed_without_ordered_timestamp_parser",
                "risk_interpretation_candidate": interpretation,
                "false_positive_risk": "正常用户也可能在短时间内产生多条同类记录；L3 只能作为候选，需后续补时间窗、对照和行为上下文。",
                "missing_evidence": ["cross_entity_sequence_support", "normal_control_group_not_checked", "L4_validation_required"],
                "candidate_only_not_final_conclusion": True,
            }
        )
    return sequence_rows


def build_sequence_candidate_features(
    *,
    sequence_comparison_features: list[dict[str, Any]],
    sampled_entities: list[str],
) -> list[dict[str, Any]]:
    features: list[dict[str, Any]] = []
    for row in sequence_comparison_features:
        source_name = str(row.get("source_name") or "")
        involved_fields = [str(field) for field in row.get("involved_fields", []) or [] if field]
        support_entity_count = int(row.get("support_entity_count") or 1)
        support_ratio = round(support_entity_count / max(len(sampled_entities), 1), 4)
        priority = _detail_candidate_priority("login_detail_table" if source_name == "login_logs_search" else "user_behavior_summary_detail_table", support_ratio, [])
        features.append(
            {
                "feature_name": row.get("sequence_feature_name"),
                "feature_type": row.get("sequence_feature_type"),
                "feature_origin": "sequence_comparison",
                "source_domains": [str(INTERFACE_OBSERVATION_DOMAINS.get(source_name, ["unknown_domain"])[0])],
                "source_names": [source_name],
                "source_fields": involved_fields,
                "field_paths": [],
                "field_values_or_safe_refs": row.get("comparable_values"),
                "field_combination": [
                    f"{field}:sequence_compare" for field in involved_fields[:8]
                ],
                "support_sample_count": support_entity_count,
                "support_user_count": support_entity_count,
                "support_device_count": 0,
                "support_entity_count": support_entity_count,
                "support_record_count": row.get("support_record_count"),
                "support_ratio": support_ratio,
                **priority,
                "black_gray_interpretation": row.get("risk_interpretation_candidate"),
                "false_positive_risk": row.get("false_positive_risk"),
                "missing_evidence": row.get("missing_evidence"),
                "validation_method": "L3 only: compare multi-row event sequence on more samples; no baseline/lift/precision in this stage.",
                "conclusion_boundary": "candidate_only_not_final_conclusion",
                "candidate_only_not_final_conclusion": True,
                "not_final_conclusion": True,
                "validation_needed": True,
            }
        )
    return features


def _feature_text_blob(feature: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in (
        "feature_name",
        "feature_type",
        "black_gray_interpretation",
        "essence_reason",
    ):
        value = feature.get(key)
        if value:
            parts.append(str(value))
    for key in ("source_fields", "field_combination", "field_paths", "source_names", "source_domains"):
        for value in feature.get(key, []) or []:
            if value:
                parts.append(str(value))
    return " ".join(parts).lower()


def _feature_domains(feature: dict[str, Any]) -> list[str]:
    return unique_strings([str(value) for value in feature.get("source_domains", []) or [] if value])


def _feature_support_count(feature: dict[str, Any], key: str) -> int:
    try:
        return int(feature.get(key) or 0)
    except (TypeError, ValueError):
        return 0


def _candidate_essence_reason(feature: dict[str, Any], likeness: str) -> str:
    domains = set(_feature_domains(feature))
    field_semantics_status = str(feature.get("field_semantics_status") or "")
    if likeness == "unknown" or field_semantics_status == "field_semantics_unknown":
        return "字段族未解释或缺少行为链路验证，当前仅保留为候选共性。"
    reasons: list[str] = []
    if "behavior_domain" in domains and "content_domain" not in domains and "social_domain" not in domains:
        reasons.append("像登录控制链或账号动作节奏模板")
    if "device_domain" in domains:
        reasons.append("像设备环境模板或对抗环境")
    if "strategy_domain" in domains:
        reasons.append("像策略事件请求模板或特征组合模板")
    if "content_domain" in domains:
        reasons.append("像内容发布模板或导流内容模板")
    if "social_domain" in domains:
        reasons.append("像社交承接路径、对象或话术模板")
    if "feedback_domain" in domains or "enforcement_domain" in domains:
        reasons.append("像治理后迁移、反馈集中或处置轨迹模板")
    if not reasons:
        reasons.append("像字段值或字段组合层面的潜在风险模板")
    if likeness in {"high", "medium"}:
        reasons.append("但当前仍缺正常对照、统计验证和跨轮稳定性，不能直接定性。")
    elif likeness == "low":
        reasons.append("当前支撑偏弱或偏单域，容易受正常场景影响，不能直接定性。")
    return "；".join(unique_strings(reasons))


def infer_candidate_essence_fields(feature: dict[str, Any]) -> tuple[str, str, str]:
    feature_type = str(feature.get("feature_type") or "")
    feature_origin = str(feature.get("feature_origin") or "")
    source_domains = _feature_domains(feature)
    source_names = unique_strings([str(value) for value in feature.get("source_names", []) or [] if value])
    support_users = _feature_support_count(feature, "support_user_count")
    support_records = _feature_support_count(feature, "support_record_count")
    unknown_semantics = str(feature.get("field_semantics_status") or "") == "field_semantics_unknown" or "unknown_field" in feature_type
    cross_source_support = len(source_domains) >= 2 or len(source_names) >= 2
    has_field_combination = bool(feature.get("field_combination"))
    if feature_origin == "sequence_comparison" or "sequence" in feature_type:
        has_sequence = True
    else:
        has_sequence = False
    if unknown_semantics:
        likeness = "unknown"
    elif cross_source_support and (has_field_combination or has_sequence) and support_users >= 2:
        likeness = "high"
    elif (has_field_combination or has_sequence or feature_origin in {"field_combination", "raw_field_commonality"}) and support_users >= 2:
        likeness = "medium"
    elif feature_type in {"hard_single_field_signal", "source_field_value_commonality_candidate"} or support_records > 1:
        likeness = "low"
    else:
        likeness = "unknown"
    reason = _candidate_essence_reason(feature, likeness)
    boundary = "L3 only: 当前只回答像不像本质候选；未做正常对照、统计验证或跨轮稳定性验证。"
    return likeness, reason, boundary


def infer_risk_choke_point_fields(feature: dict[str, Any]) -> dict[str, Any]:
    text_blob = _feature_text_blob(feature)
    domains = set(_feature_domains(feature))
    feature_origin = str(feature.get("feature_origin") or "")
    support_users = _feature_support_count(feature, "support_user_count")
    cross_source = len(domains) >= 2
    has_field_combination = bool(feature.get("field_combination"))
    has_sequence = feature_origin == "sequence_comparison" or "sequence" in str(feature.get("feature_type") or "")
    unknown_semantics = str(feature.get("field_semantics_status") or "") in {"field_semantics_unknown", "needs_field_dictionary_review"}
    tokens = {
        "protocol": ["backend_action_signal", "missing_frontend_activity", "client path", "request_path", "frontend_activity_signal", "protocol", "request_scene"],
        "control_execution": ["mismatch", "consistency", "alignment", "device_execution", "execution", "behavior_device", "backend_action_device_id", "frontend_active_device_id"],
        "device_farm": ["root", "hook", "frida", "xposed", "simulator", "debug", "mountrisk", "risky app", "accessibility", "device environment", "package", "applist"],
        "account_transfer": ["login_type", "login_source", "refresh", "reset", "protection", "sensitive action", "profile", "publish_after_login", "private_message", "comment", "follow"],
        "content_funnel": ["caption", "template", "target_user_id", "comment", "message", "funnel", "social", "content_type", "audit_reason", "path"],
        "post_enforcement": ["punish", "review", "appeal", "report", "migration", "post_enforcement", "downrank", "remove"],
        "automation_rhythm": ["time_delta", "rhythm", "sequence_compare", "action_time", "short time", "burst", "window"],
    }
    # G-R5: protocol 信号 token（必须出现这些才允许归 protocol_constraint_gap）
    _PROTOCOL_STRONG_TOKENS = {
        "backend_action_signal", "frontend_activity_signal", "request_path",
        "client path", "missing_frontend_activity", "frontend_backend_alignment",
        "client_device_mismatch", "rcp_event_feature_list", "rcp_snapshot",
        "request_scene", "frontend_active_device_id", "backend_action_device_id",
    }
    _has_protocol_signal = any(tok in text_blob for tok in _PROTOCOL_STRONG_TOKENS)
    # G-R5: sequence/account 专用 token（automation_rhythm 优先识别）
    _SEQUENCE_RHYTHM_TOKENS = {
        "sequence_compare", "time_delta", "action_time", "rhythm", "ordered_event",
        "login_source", "login_type", "profile_change", "account_change",
    }
    _has_sequence_rhythm = has_sequence or any(tok in text_blob for tok in _SEQUENCE_RHYTHM_TOKENS)
    # G-R5: device risky environment token（区分 risky env vs device farm）
    _DEVICE_RISKY_ENV_TOKENS = {
        "root", "hook", "frida", "xposed", "simulator", "emulator", "debug",
        "accessibility", "factory_reset", "no_sim", "mountrisk", "risky app",
    }
    _DEVICE_FARM_TOKENS = {
        "device environment", "package", "applist", "sdk_version", "device_model",
        "device profile", "app list", "device bundle",
    }
    # anchor-only guard：仅有 device_id/did/policy_code/source_id 不得产生 device_farm
    _anchor_only_fields = {"device_id", "did", "policy_code", "source_id", "uid", "user_id"}
    _g_r5_field_combo = [str(f) for f in (feature.get("field_combination") or []) if f]
    _g_r5_src_fields = [str(f) for f in (feature.get("source_fields") or []) if f]
    _all_feature_fields = set(_g_r5_field_combo + _g_r5_src_fields)
    _anchor_only = bool(_all_feature_fields) and _all_feature_fields <= _anchor_only_fields

    type_name = "unknown"
    if unknown_semantics:
        type_name = "unknown"
    elif _anchor_only:
        # 仅有 anchor 字段（device_id/did/policy_code），不归任何有意义 choke type
        type_name = "unknown"
    elif has_sequence and not _has_protocol_signal:
        # G-R5: sequence_comparison 且无明确协议信号 → 优先 automation_rhythm，不归 protocol
        if _SEQUENCE_RHYTHM_TOKENS & set(text_blob.split()) or has_sequence:
            type_name = "automation_rhythm"
    elif _has_protocol_signal and (
        "strategy_domain" in domains or "behavior_domain" in domains
    ):
        # G-R5: protocol_constraint_gap 需要明确协议信号 + strategy/behavior domain
        type_name = "protocol_constraint_gap"
    elif any(token in text_blob for token in tokens["control_execution"]) or ({"behavior_domain", "device_domain"} <= domains and has_sequence):
        type_name = "control_execution_separation"
    elif "device_domain" in domains and any(tok in text_blob for tok in _DEVICE_RISKY_ENV_TOKENS):
        # 明确 risky 环境字段 → device_farm_template（已有最强语义）
        type_name = "device_farm_template"
    elif "device_domain" in domains and any(tok in text_blob for tok in _DEVICE_FARM_TOKENS):
        type_name = "device_farm_template"
    elif "behavior_domain" in domains and any(token in text_blob for token in tokens["account_transfer"]):
        type_name = "account_control_transfer"
    elif ({"content_domain", "social_domain"} & domains) and any(token in text_blob for token in tokens["content_funnel"]):
        type_name = "content_funnel_dependency"
    elif ({"feedback_domain", "enforcement_domain"} & domains) and any(token in text_blob for token in tokens["post_enforcement"]):
        type_name = "post_enforcement_migration"
    elif _has_sequence_rhythm or any(token in text_blob for token in tokens["automation_rhythm"]):
        type_name = "automation_rhythm"
    elif any(token in text_blob for token in tokens["protocol"]) and _has_protocol_signal:
        # fallback: 有 protocol tokens 但前面没匹配到 strategy/behavior domain 条件
        type_name = "protocol_constraint_gap"

    if type_name == "unknown":
        likeness = "unknown"
    elif cross_source and (has_field_combination or has_sequence) and support_users >= 2:
        likeness = "high"
    elif (has_field_combination or has_sequence or support_users >= 2):
        likeness = "medium"
    else:
        likeness = "low"
    if str(feature.get("feature_name") or "") == "multi_domain_anchor_overlap_candidate":
        likeness = "low"
        type_name = "unknown"

    reason_map = {
        "protocol_constraint_gap": "更像前后端约束脱节或协议约束缺失，攻击成立依赖客户端约束未闭合。",
        "control_execution_separation": "更像控制面与执行面分离，登录、设备或行为执行不在同一自然实体链路上。",
        "device_farm_template": "更像设备环境批量模板化，攻击执行依赖同类设备环境或对抗环境。",
        "account_control_transfer": "更像账号控制权转移或登录态滥用，后续敏感动作依赖控制链成立。",
        "content_funnel_dependency": "更像内容导流承接路径依赖，攻击要成立必须有内容到社交/私域的承接链。",
        "post_enforcement_migration": "更像治理后迁移能力，攻击者通过切换账号、设备或路径继续执行。",
        "automation_rhythm": "更像自动化执行节奏，动作序列和时间差体现模板化执行。",
        "unknown": "当前只能看见候选链路或未知字段重合，还不能解释成稳定关键卡口。",
    }
    if type_name in {"protocol_constraint_gap", "control_execution_separation", "device_farm_template", "account_control_transfer"}:
        required_for_attack = True if likeness in {"high", "medium"} else "unknown"
    elif type_name in {"content_funnel_dependency", "post_enforcement_migration", "automation_rhythm"}:
        required_for_attack = "unknown" if likeness == "low" else False
    else:
        required_for_attack = "unknown"

    if type_name in {"protocol_constraint_gap", "control_execution_separation", "device_farm_template"}:
        evade = "low" if likeness == "high" else "medium"
        robustness = "high" if likeness == "high" else "medium"
    elif type_name in {"content_funnel_dependency", "post_enforcement_migration", "automation_rhythm"}:
        evade = "medium"
        robustness = "medium" if likeness in {"high", "medium"} else "low"
    elif type_name == "account_control_transfer":
        evade = "medium"
        robustness = "medium"
    else:
        evade = "unknown"
        robustness = "unknown" if unknown_semantics else "low"

    supporting_types = unique_strings([
        "field_combination_commonality" if has_field_combination else "",
        "sequence_commonality" if has_sequence else "",
        "cross_source_support_commonality" if cross_source else "",
        "field_value_commonality" if feature_origin in {"raw_field_commonality", "unknown_field_commonality"} or "field_value" in str(feature.get("feature_type") or "") else "",
    ])
    if not supporting_types:
        supporting_types = ["coverage_commonality"] if not has_field_combination and not has_sequence else []
    return {
        "risk_choke_point_type": type_name,
        "choke_point_likeness": likeness,
        "choke_point_reason": reason_map.get(type_name, reason_map["unknown"]),
        "required_for_attack": required_for_attack,
        "easy_to_evade_if_changed": evade,
        "robustness": robustness,
        "supporting_commonality_types": supporting_types,
        "supporting_source_domains": sorted(domains),
    }


def _sanitize_l3_candidate_text(text: str) -> str:
    return (
        str(text or "")
        .replace("baseline/lift/precision", "statistical validation")
        .replace("baseline、lift、误伤率", "正常对照、统计验证")
        .replace("lift 和误伤率", "统计验证")
        .replace("lift，false-positive review rate", "statistical validation")
        .replace("lift、误伤率", "统计验证")
        .replace("lift", "statistical_validation")
        .replace("precision", "statistical_validation")
    )


def normalize_l3_candidate_feature_contract(feature: dict[str, Any]) -> dict[str, Any]:
    item = dict(feature)
    feature_type = str(item.get("feature_type") or item.get("feature_name") or "")
    if not item.get("feature_origin"):
        if "sequence" in feature_type:
            origin = "sequence_comparison"
        elif "unknown_field" in feature_type:
            origin = "unknown_field_commonality"
        elif feature_type == "source_field_value_commonality_candidate":
            origin = "raw_field_commonality"
        elif "combination" in feature_type or item.get("field_combination"):
            origin = "field_combination"
        else:
            origin = "raw_field_commonality"
        item["feature_origin"] = origin
    item.setdefault("source_names", unique_strings([str(item.get("source_name") or "")] + [str(x) for x in item.get("source_names", []) or [] if x]))
    item.setdefault("source_fields", item.get("source_fields") or [])
    item.setdefault("field_paths", item.get("field_paths") or [])
    item.setdefault("field_values_or_safe_refs", item.get("field_values_or_safe_refs") or item.get("field_value_or_safe_ref") or [])
    item.setdefault("field_combination", item.get("field_combination") or [])
    support_sample_count = item.get("support_sample_count") or item.get("support_user_count") or item.get("support_entity_count") or item.get("support_count") or 0
    item.setdefault("support_sample_count", support_sample_count)
    item.setdefault("support_user_count", item.get("support_user_count") or item.get("support_entity_count") or support_sample_count)
    item.setdefault("support_device_count", item.get("support_device_count") or 0)
    item.setdefault("support_entity_count", item.get("support_entity_count") or item.get("support_user_count") or support_sample_count)
    item.setdefault("support_record_count", item.get("support_record_count") or 0)
    item.setdefault("support_ratio", item.get("support_ratio"))
    item.setdefault("priority_score", item.get("priority_score") or 0)
    item.setdefault("priority_level", item.get("priority_level") or "low")
    sanitized_reason_codes = [
        str(code)
        for code in (item.get("reason_codes") or ["L3_candidate_only"])
        if code and not str(code).startswith("lift=") and str(code) != "baseline_available"
    ]
    item["reason_codes"] = sanitized_reason_codes or ["L3_candidate_only"]
    item.setdefault("black_gray_interpretation", item.get("black_gray_interpretation") or "字段共性候选，只能作为 L3 输入，不能直接定性。")
    item.setdefault("false_positive_risk", item.get("false_positive_risk") or item.get("normal_user_false_positive_risk") or "需要正常对照和场景验证。")
    item.setdefault("missing_evidence", item.get("missing_evidence") or ["L4_validation_required"])
    if not item.get("validation_method"):
        item["validation_method"] = "L3 only; compare more current observations and defer statistical validation to L4."
    item["validation_method"] = _sanitize_l3_candidate_text(str(item.get("validation_method") or ""))
    item.setdefault("conclusion_boundary", "candidate_only_not_final_conclusion")
    supporting_evidence = unique_strings(
        [str(x) for x in item.get("supporting_current_evidence", []) or [] if x]
        + [str(x) for x in item.get("support_entities", []) or [] if x]
        + [str(x) for x in item.get("supporting_entities", []) or [] if x]
        + [str(x) for x in item.get("supporting_samples", []) or [] if x]
    )
    if not supporting_evidence:
        supporting_evidence = unique_strings(
            [str(x) for x in item.get("field_values_or_safe_refs", []) or [] if x]
            + [str(x) for x in item.get("source_fields", []) or [] if x]
        )
    item.setdefault("supporting_current_evidence", supporting_evidence)
    item.setdefault("supporting_selected_anchors", item.get("supporting_selected_anchors") or [])
    item.setdefault("unselected_signal_hypothesis", not bool(item.get("supporting_selected_anchors")))
    item.setdefault(
        "signal_inputs",
        [
            {
                "evidence_source": "current_observation",
                "source_names": item.get("source_names") or [],
                "source_fields": item.get("source_fields") or [],
                "field_paths": item.get("field_paths") or [],
                "feature_origin": item.get("feature_origin"),
            }
        ],
    )
    item.setdefault(
        "hypothesis_inputs",
        [
            {
                "evidence_source": "candidate_hypothesis",
                "feature_type": feature_type,
                "usage_boundary": "L3_candidate_only_requires_validation",
            }
        ],
    )
    item.setdefault("confidence", item.get("confidence") or "candidate_partial")
    essence_likeness, essence_reason, essence_boundary = infer_candidate_essence_fields(item)
    item.setdefault("essence_likeness", essence_likeness)
    item.setdefault("essence_reason", _sanitize_l3_candidate_text(essence_reason))
    item.setdefault("essence_boundary", _sanitize_l3_candidate_text(essence_boundary))
    choke_fields = infer_risk_choke_point_fields(item)
    for key, value in choke_fields.items():
        item.setdefault(key, value)
    item.setdefault("supporting_attack_chain_ids", [])
    for transient_key in ("baseline_ratio", "lift", "lift_unavailable"):
        item.pop(transient_key, None)
    # ── G-R3: candidate_features enrichment ──────────────────────────────────
    # 将内部 feature dict 的字段映射为对外输出合同字段，确保无 empty_shell 候选。
    # 优先级：item 已有值 > 内部字段推断 > domain/origin fallback > 安全缺省
    _g_r3_choke_type = str(item.get("risk_choke_point_type") or "unknown")
    _g_r3_domains = set(_feature_domains(item))
    _g_r3_origin = str(item.get("feature_origin") or "")
    _g_r3_field_semantics = str(item.get("field_semantics_status") or "")
    # 1. candidate_feature_name
    #    优先 item.candidate_feature_name → item.feature_name → choke_type → domain/origin fallback
    _DOMAIN_NAME_MAP: dict[str, str] = {
        "device_farm_template": "device_farm_template_candidate",
        "control_execution_separation": "control_execution_separation_candidate",
        "protocol_constraint_gap": "protocol_constraint_gap_candidate",
        "account_control_transfer": "account_maintenance_template_candidate",
        "content_funnel_dependency": "content_funnel_dependency_candidate",
        "post_enforcement_migration": "post_enforcement_migration_candidate",
        "automation_rhythm": "automation_rhythm_candidate",
    }
    if not item.get("candidate_feature_name"):
        # 先看 feature_name（已有语义名）
        _g_r3_existing_fn = str(item.get("feature_name") or "")
        if _g_r3_choke_type != "unknown":
            _g_r3_feature_name = _DOMAIN_NAME_MAP.get(_g_r3_choke_type, f"{_g_r3_choke_type}_candidate")
        elif _g_r3_origin == "unknown_field_commonality" or _g_r3_field_semantics in ("field_semantics_unknown", "needs_field_dictionary_review"):
            if "device_domain" in _g_r3_domains:
                _g_r3_feature_name = "device_unknown_field_enrichment_candidate"
            elif "strategy_domain" in _g_r3_domains:
                _g_r3_feature_name = "rcp_unknown_feature_bundle_candidate"
            elif "account_domain" in _g_r3_domains:
                _g_r3_feature_name = "account_unknown_field_enrichment_candidate"
            else:
                _g_r3_feature_name = "unknown_field_enrichment_candidate"
        elif "device_domain" in _g_r3_domains:
            _g_r3_feature_name = "device_execution_environment_candidate"
        elif "strategy_domain" in _g_r3_domains and "behavior_domain" in _g_r3_domains:
            _g_r3_feature_name = "rcp_feature_bundle_candidate"
        elif "strategy_domain" in _g_r3_domains:
            _g_r3_feature_name = "register_strategy_feature_template_candidate"
        elif "behavior_domain" in _g_r3_domains:
            _g_r3_feature_name = "login_control_chain_candidate"
        elif "account_domain" in _g_r3_domains:
            _g_r3_feature_name = "account_maintenance_template_candidate"
        elif "content_domain" in _g_r3_domains or "social_domain" in _g_r3_domains:
            _g_r3_feature_name = "content_template_candidate"
        elif "feedback_domain" in _g_r3_domains or "enforcement_domain" in _g_r3_domains:
            _g_r3_feature_name = "enforcement_context_candidate"
        elif _g_r3_existing_fn:
            _g_r3_feature_name = _g_r3_existing_fn
        else:
            _g_r3_feature_name = "field_commonality_candidate"
        item["candidate_feature_name"] = _g_r3_feature_name
    # 2. source_support
    #    优先 item.source_support → item.source_names → domain fallback
    _DOMAIN_SOURCE_MAP: dict[str, list[str]] = {
        "device_domain": ["weapon_inventory", "weapon_device_info"],
        "strategy_domain": ["rcp_snapshot", "rcp_event_feature_list"],
        "behavior_domain": ["login_logs_search"],
        "account_domain": ["archives_user_analysis", "archives_user_profile"],
        "content_domain": ["archives_photo_search"],
        "social_domain": ["archives_private_message_search"],
        "feedback_domain": ["archives_negative_report", "archives_user_report_search"],
        "enforcement_domain": ["archives_review_logs"],
    }
    if not item.get("source_support"):
        _g_r3_src_names = unique_strings([str(x) for x in item.get("source_names", []) or [] if x])
        if not _g_r3_src_names:
            for _dom in sorted(_g_r3_domains):
                _g_r3_src_names.extend(_DOMAIN_SOURCE_MAP.get(_dom, []))
            _g_r3_src_names = unique_strings(_g_r3_src_names)
        item["source_support"] = _g_r3_src_names
    # 3. core_commonality
    #    优先 item.core_commonality → field_combination → source_fields → reason_codes → domain/origin fallback
    if not item.get("core_commonality"):
        _ANCHOR_ONLY_FIELDS = {"device_id", "did", "policy_code", "source_id", "uid", "user_id"}
        _g_r3_field_combo = [
            f for f in (item.get("field_combination") or []) or []
            if str(f).lower() not in _ANCHOR_ONLY_FIELDS
        ]
        _g_r3_src_fields = [
            f for f in (item.get("source_fields") or []) or []
            if str(f).lower() not in _ANCHOR_ONLY_FIELDS
        ]
        _g_r3_reason_codes = [
            str(c) for c in (item.get("reason_codes") or [])
            if c and str(c) not in {"L3_candidate_only"}
        ]
        _g_r3_core_com: list[str] = (
            _g_r3_field_combo
            or _g_r3_src_fields
            or _g_r3_reason_codes
        )
        if not _g_r3_core_com:
            if _g_r3_origin == "unknown_field_commonality" or _g_r3_field_semantics in ("field_semantics_unknown", "needs_field_dictionary_review"):
                _g_r3_core_com = ["unknown_device_field_bundle"] if "device_domain" in _g_r3_domains else ["unknown_field_bundle"]
            elif "device_domain" in _g_r3_domains:
                _g_r3_core_com = ["device_environment_fields_overlap"]
            elif "strategy_domain" in _g_r3_domains:
                _g_r3_core_com = ["register_event_feature_bundle"]
            elif "behavior_domain" in _g_r3_domains:
                _g_r3_core_com = ["login_type_login_source_pattern"]
            elif "account_domain" in _g_r3_domains:
                _g_r3_core_com = ["account_status_and_behavior_pattern"]
            elif "content_domain" in _g_r3_domains or "social_domain" in _g_r3_domains:
                _g_r3_core_com = ["content_template_social_funnel_path"]
            elif "feedback_domain" in _g_r3_domains or "enforcement_domain" in _g_r3_domains:
                _g_r3_core_com = ["enforcement_context_migration_pattern"]
            else:
                _g_r3_core_com = ["insufficient_interpretable_commonality"]
        item["core_commonality"] = _g_r3_core_com
    # 4. supporting_source_domains
    #    优先 item.supporting_source_domains → item.source_domains → 空列表
    item.setdefault("supporting_source_domains", sorted(_g_r3_domains))
    # 5. evidence_commonality_types：去掉空字符串
    _g_r3_ev_types = [
        str(t) for t in (item.get("evidence_commonality_types") or []) or []
        if t and str(t).strip()
    ]
    item["evidence_commonality_types"] = _g_r3_ev_types
    # 6. unknown device field → inject missing_evidence hint
    if (_g_r3_origin == "unknown_field_commonality" or _g_r3_field_semantics == "needs_field_dictionary_review") and "device_domain" in _g_r3_domains:
        existing_missing = list(item.get("missing_evidence") or [])
        if "needs_field_dictionary_review" not in existing_missing:
            existing_missing.insert(0, "needs_field_dictionary_review")
        item["missing_evidence"] = existing_missing
    # 7. generic candidates (multi_domain_anchor_overlap): 降级为 low/unknown
    if str(item.get("feature_name") or "") in {
        "multi_domain_anchor_overlap_candidate",
        "group_level_field_enrichment_candidate",
        "hard_single_field_signal_candidate",
    }:
        item["choke_point_likeness"] = "low"
        item["risk_choke_point_type"] = "unknown"
        item["candidate_feature_name"] = str(item.get("feature_name") or "generic_overlap_candidate")
    # ── end G-R3 enrichment ───────────────────────────────────────────────────
    item["candidate_only_not_final_conclusion"] = True
    item["not_final_conclusion"] = True
    item["validation_needed"] = True
    return item


def build_standard_field_commonality_and_features(
    *,
    standard_detail_table: list[dict[str, Any]],
    sampled_entities: list[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows_by_table_field: dict[tuple[str, str], list[dict[str, Any]]] = {}
    rows_by_table_field_value: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for row in standard_detail_table:
        table_name = str(row.get("detail_table") or "")
        field_name = str(row.get("field_name") or "")
        if not table_name or not field_name:
            continue
        rows_by_table_field.setdefault((table_name, field_name), []).append(row)
        if row.get("value_present") is True and row.get("value_comparable") is True:
            rows_by_table_field_value.setdefault((table_name, field_name, str(row.get("field_value_or_safe_ref"))), []).append(row)

    commonality_rows: list[dict[str, Any]] = []
    value_commonality_by_table: dict[str, list[dict[str, Any]]] = {}
    sampled_denominator = max(len(sampled_entities), 1)
    for (table_name, field_name), rows in rows_by_table_field.items():
        entities = unique_strings([str(row.get("entity_id")) for row in rows if row.get("entity_id")])
        if len(entities) < 2:
            continue
        example = rows[0]
        commonality_rows.append(
            {
                "signal_name": f"{table_name}:field_coverage:{field_name}",
                "commonality_type": "coverage_commonality",
                "detail_table": table_name,
                "source_fields": [field_name],
                "field_family": example.get("field_family"),
                "supporting_current_evidence": entities,
                "support_count": len(entities),
                "batch_support_count": len(entities),
                "support_ratio": round(len(entities) / sampled_denominator, 4),
                "commonality_anchor": False,
                "risk_commonality": False,
                "eligible_for_group_candidate": False,
                "candidate_feature_eligible": False,
                "evidence_source": "current_observation",
                "source_name": table_name,
                "not_final_conclusion": True,
            }
        )

    for (table_name, field_name, value_ref), rows in rows_by_table_field_value.items():
        entities = unique_strings([str(row.get("entity_id")) for row in rows if row.get("entity_id")])
        if len(entities) < 2:
            continue
        example = rows[0]
        unknown = bool(example.get("unknown_field_family"))
        commonality_type = "unknown_field_value_commonality" if unknown else "field_value_commonality"
        item = {
            "signal_name": f"{table_name}:{commonality_type}:{field_name}",
            "commonality_type": commonality_type,
            "detail_table": table_name,
            "source_fields": [field_name],
            "field_family": example.get("field_family"),
            "field_value_or_safe_ref": value_ref,
            "supporting_current_evidence": entities,
            "support_count": len(entities),
            "batch_support_count": len(entities),
            "support_ratio": round(len(entities) / sampled_denominator, 4),
            "commonality_anchor": False,
            "risk_commonality": False,
            "eligible_for_group_candidate": False,
            "candidate_feature_eligible": True,
            "field_semantics_status": "needs_field_dictionary_review" if unknown else "known_field_family",
            "evidence_source": "current_observation",
            "source_name": table_name,
            "not_final_conclusion": True,
        }
        commonality_rows.append(item)
        value_commonality_by_table.setdefault(table_name, []).append(item)

    candidate_features: list[dict[str, Any]] = []
    for table_name, items in value_commonality_by_table.items():
        selected = sorted(
            items,
            key=lambda item: (-float(item.get("support_ratio") or 0), str(item.get("source_fields") or "")),
        )[:5]
        if not selected:
            continue
        source_fields = unique_strings([
            field for item in selected for field in item.get("source_fields", []) or []
        ])
        support_entities = unique_strings([
            entity for item in selected for entity in item.get("supporting_current_evidence", []) or []
        ])
        if len(support_entities) < 2:
            continue
        supporting_rows = [
            {
                "sample_id": row.get("sample_id"),
                "entity_id": row.get("entity_id"),
                "round_id": row.get("round_id"),
                "source_id": row.get("source_id"),
                "source_quality": row.get("source_quality"),
                "field_name": row.get("field_name"),
                "field_family": row.get("field_family"),
            }
            for row in standard_detail_table
            if row.get("detail_table") == table_name
            and row.get("field_name") in set(source_fields)
            and str(row.get("entity_id")) in set(support_entities)
        ]
        source_domains = unique_strings([
            str(row.get("source_domain"))
            for row in standard_detail_table
            if row.get("detail_table") == table_name and row.get("source_domain")
        ])
        support_ratio = round(len(support_entities) / sampled_denominator, 4)
        priority = _detail_candidate_priority(table_name, support_ratio, source_domains)
        unknown_fields = [
            field for item in selected
            if item.get("field_semantics_status") == "needs_field_dictionary_review"
            for field in item.get("source_fields", []) or []
        ]
        candidate_features.append(
            {
                "feature_name": DETAIL_TABLE_FEATURE_NAMES.get(table_name, f"{table_name}_field_commonality_candidate"),
                "feature_type": "source_field_value_commonality_candidate",
                "source_domains": source_domains,
                "source_fields": source_fields,
                "field_values_or_safe_refs": [
                    item.get("field_value_or_safe_ref") for item in selected if item.get("field_value_or_safe_ref") is not None
                ],
                "field_combination": [
                    f"{item.get('source_fields', ['unknown'])[0]}={item.get('field_value_or_safe_ref')}"
                    for item in selected
                ],
                "support_sample_count": len(support_entities),
                "support_user_count": len(support_entities),
                "support_entity_count": len(support_entities),
                "support_ratio": support_ratio,
                **priority,
                "supporting_current_evidence": supporting_rows,
                "supporting_selected_anchors": [],
                "unselected_signal_hypothesis": True,
                "signal_inputs": [{"evidence_source": "current_observation", "detail_table": table_name, "source_fields": source_fields}],
                "hypothesis_inputs": [],
                "black_gray_interpretation": _detail_candidate_interpretation(table_name),
                "false_positive_risk": _detail_candidate_false_positive(table_name),
                "normal_user_false_positive_risk": _detail_candidate_false_positive(table_name),
                "missing_evidence": _detail_candidate_missing_evidence(table_name, unknown_fields),
                "missing_fields_to_check": _detail_candidate_missing_evidence(table_name, unknown_fields),
                "validation_method": "L3 only: replay field-value combinations on more current observations; deeper control validation is not executed in this stage.",
                "strategy_usage_boundary": "候选特征 only；只进入观察、人审辅助或后续验证计划，不能直接用于处置或策略动作。",
                "conclusion_boundary": "candidate_only_not_final_conclusion",
                "confidence": "medium_partial" if not unknown_fields else "low_hypothesis",
                "validation_needed": True,
                "not_final_conclusion": True,
            }
        )
        if len(selected) >= 2:
            commonality_rows.append(
                {
                    "signal_name": f"{table_name}:field_combination_commonality",
                    "commonality_type": "field_combination_commonality",
                    "detail_table": table_name,
                    "source_fields": source_fields,
                    "field_family": unique_strings([str(item.get("field_family") or "") for item in selected if item.get("field_family")]),
                    "field_combination": [
                        f"{item.get('source_fields', ['unknown'])[0]}={item.get('field_value_or_safe_ref')}"
                        for item in selected
                    ],
                    "supporting_current_evidence": support_entities,
                    "support_count": len(support_entities),
                    "batch_support_count": len(support_entities),
                    "support_ratio": support_ratio,
                    "commonality_anchor": False,
                    "risk_commonality": False,
                    "eligible_for_group_candidate": False,
                    "candidate_feature_eligible": True,
                    "evidence_source": "current_observation",
                    "source_name": table_name,
                    "not_final_conclusion": True,
                }
            )
    return commonality_rows, candidate_features


def _detail_candidate_interpretation(table_name: str) -> str:
    return {
        "login_detail_table": "多个样本在登录端、设备、网络、UA 或登录结果上出现字段值共性，可作为登录控制链或 ATO 候选线索。",
        "account_detail_table": "多个样本在账号状态、资料维护、粉关资产或处罚保护状态上出现字段值共性，可作为账号态维护或小号候选线索。",
        "user_behavior_summary_detail_table": "多个样本在用户分析行为计数或账号维护动作上出现字段值共性，可作为行为节奏候选线索。",
        "content_detail_table": "多个样本在发布、内容模板、审核原因或互动计数上出现字段值共性，可作为内容承接或导流候选线索。",
        "social_detail_table": "多个样本在社交对象、话术、关系路径或互动动作上出现字段值共性，可作为社交承接候选线索。",
        "feedback_detail_table": "多个样本在举报、反馈对象或申诉字段上出现共性，只能作为反馈线索，不能直接代表风险事实。",
        "enforcement_detail_table": "多个样本在审核、处罚、限流、下架或处置后动作上出现共性，只能作为治理状态线索，不能直接代表黑灰产本质。",
    }.get(table_name, "多个样本存在字段值共性，可作为候选线索，需后续验证。")


def _detail_candidate_false_positive(table_name: str) -> str:
    return {
        "login_detail_table": "同地区、同客户端、正常多端登录、网络出口集中都可能造成相似登录字段。",
        "account_detail_table": "新用户、活动用户、正常资料维护或低活跃账号也可能有相似画像字段。",
        "user_behavior_summary_detail_table": "正常活跃周期、活动引导、内容消费高峰可能造成行为计数相似。",
        "content_detail_table": "热点模板、同活动话题、同版本发布入口可能造成内容字段相似。",
        "social_detail_table": "正常社交互动、热门对象、活动评论模板可能造成社交字段相似。",
        "feedback_detail_table": "集中举报可能来自同一受害群体、活动争议或误报，不等于风险确认。",
        "enforcement_detail_table": "相似处置可能来自相同治理规则或审核批次，不等于黑灰产本质相同。",
    }.get(table_name, "正常业务场景可能出现相似字段，需要更多样本和对照验证。")


def _detail_candidate_missing_evidence(table_name: str, unknown_fields: list[str]) -> list[str]:
    base = ["baseline_not_evaluated_in_L3", "normal_control_group_not_checked", "L4_validation_required"]
    if unknown_fields:
        base.append("needs_field_dictionary_review")
    if table_name == "login_detail_table":
        base.extend(["behavior_action_alignment", "longer_login_window"])
    elif table_name in {"account_detail_table", "user_behavior_summary_detail_table"}:
        base.extend(["historical_account_baseline", "behavior_sequence_detail"])
    elif table_name == "content_detail_table":
        base.extend(["content_template_detail", "publish_device_alignment"])
    elif table_name == "social_detail_table":
        base.extend(["shared_target_or_wording_validation", "social_path_detail"])
    elif table_name in {"feedback_detail_table", "enforcement_detail_table"}:
        base.extend(["feedback_enforcement_timeline", "policy_reason_detail"])
    return unique_strings(base)


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
        return ["weapon_device_info", "weapon_device_app_list", "track_analysis_check_data_ready", "weapon_inventory"]
    if anchor_type in {"candidate_policy_code", "candidate_event_id", "candidate_source_id"}:
        return ["rcp_event_detail", "rcp_event_feature_list"]
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
                    next_allowed_interfaces=_anchor_next_interfaces("candidate_device_id"),
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
                    next_allowed_interfaces=["rcp_event_detail", "rcp_event_feature_list"],
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
                next_allowed_interfaces=_anchor_next_interfaces("candidate_device_id"),
                cap_key="device_anchor_top_k",
                reason="candidate_device_extracted_from_safe_observation",
                source_quality=quality,
                evidence_source="current_observation",
                field_path=str(candidate.get("field_path") or ""),
            )
    if not anchors and mode == "dry_run":
        for anchor_type, produced_by, domain, next_interfaces, cap_key in [
            ("candidate_photo_id", "archives_photo_search", "content_domain", ["archives_gallery_photo_list", "archives_photo_profile", "archives_photo_meta"], "photo_anchor_top_k"),
            ("candidate_device_id", "weapon_device_info", "device_domain", _anchor_next_interfaces("candidate_device_id"), "device_anchor_top_k"),
            ("candidate_policy_code", "rcp_fast_query_hbase", "strategy_domain", ["rcp_event_detail", "rcp_event_feature_list"], "strategy_anchor_top_k"),
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
    "login_time": "login_time",
    "login_type": "login_type",
    "login_source": "login_source",
    "login_result": "login_result",
    "network_signal": "ip_or_network",
    "account_age": "account_age",
    "register_time": "register_time",
    "account_status": "account_status",
    "protection_status": "protection_status",
    "punish_status": "punish_status",
    "profile_change_time": "profile_change_time",
    "nickname_change": "nickname_change",
    "avatar_change": "avatar_change",
    "bio_change": "bio_change",
    "follow_count": "follow_count",
    "fan_count": "fan_count",
    "content_publish_count": "content_publish_count",
    "active_days": "active_days",
    "recent_behavior_counts": "recent_behavior_counts",
    "photo_id": "photo_id",
    "item_id": "item_id",
    "publish_time": "publish_time",
    "publish_device": "publish_device",
    "publish_ip": "publish_ip",
    "content_type": "content_type",
    "caption": "caption",
    "title": "title",
    "audit_reason": "audit_reason",
    "strategy_reason": "strategy_reason",
    "like_count": "like_count",
    "comment_count": "comment_count",
    "share_count": "share_count",
    "play_count": "play_count",
    "comment_id": "comment_id",
    "message_id": "message_id",
    "target_user_id": "target_user_id",
    "relation_type": "relation_type",
    "message_text": "message_text",
    "comment_text": "comment_text",
    "action_time": "action_time",
    "sender": "sender",
    "receiver": "receiver",
    "same_target": "same_target",
    "same_wording": "same_wording",
    "same_path": "same_path",
    "report_time": "report_time",
    "report_type": "report_type",
    "feedback_object": "feedback_object",
    "appeal_time": "appeal_time",
    "appeal_result": "appeal_result",
    "review_result": "review_result",
    "punish_type": "punish_type",
    "enforcement_action": "enforcement_action",
    "enforcement_time": "enforcement_time",
    "policy_reason": "policy_reason",
    "request_path": "request_path",
    "request_scene": "request_scene",
    "entry": "entry",
    "action_type": "action_type",
    "action_object": "action_object",
    "task_type": "task_type",
    "reward_type": "reward_type",
    "client_params": "client_params",
    "app_version": "app_version",
    "ua": "ua",
    "ip_or_network": "ip_or_network",
    "frontend_activity_signal": "frontend_activity_signal",
    "backend_action_signal": "backend_action_signal",
    "time_delta_from_login_seconds": "time_delta_from_login_seconds",
    "time_delta_between_actions_seconds": "time_delta_between_actions_seconds",
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
        records = item.get("records") if isinstance(item.get("records"), list) else []
        feature_rows_input = item.get("feature_rows") if isinstance(item.get("feature_rows"), list) else []
        device_detail_rows_input = item.get("device_detail_rows") if isinstance(item.get("device_detail_rows"), list) else []
        generated_feature_count = int(item.get("generated_feature_row_count") or 0)
        if generated_feature_count > 0:
            feature_rows_input = list(feature_rows_input) + [
                {
                    "feature_key": f"mockRcpRawFeature{i:03d}",
                    "feature_name": f"mock RCP raw feature {i:03d}",
                    "feature_type": "string",
                    "defaultFeatureValue": "shared_rcp_template" if i % 7 == 0 else f"value_{i:03d}",
                    "feature_tab": STRATEGY_EVENT_ORIGINAL_FEATURE_TAB,
                    "mapped_domain": "未知",
                    "mapped_field_family": "unknown_feature_family",
                    "candidate_feature_eligible": True,
                }
                for i in range(1, generated_feature_count + 1)
            ]
        generated_device_count = int(item.get("generated_device_detail_field_count") or 0)
        if generated_device_count > 0:
            device_detail_rows_input = list(device_detail_rows_input) + [
                {
                    "device_field_key": f"mockDeviceWideField{i:03d}",
                    "device_field_name": f"mock device wide field {i:03d}",
                    "device_field_value_or_safe_ref": "shared_device_template" if i % 9 == 0 else f"device_value_{i:03d}",
                    "device_field_type": "string",
                    "value_comparable": True,
                    "comparable_type": "等值",
                    "device_source_type": "设备基础信息",
                    "mapped_field_family": "unknown_device_field_family",
                    "candidate_feature_eligible": True,
                }
                for i in range(1, generated_device_count + 1)
            ]
        strategy_event_feature_rows: list[dict[str, Any]] = []
        for row_index, row in enumerate(feature_rows_input, start=1):
            if not isinstance(row, dict):
                continue
            feature_key = str(row.get("feature_key") or row.get("featureKey") or "").strip()
            feature_name = str(row.get("feature_name") or row.get("featureName") or feature_key).strip()
            if not feature_key and not feature_name:
                continue
            raw_value = (
                row.get("feature_value_or_safe_ref")
                if "feature_value_or_safe_ref" in row
                else row.get("defaultFeatureValue")
                if "defaultFeatureValue" in row
                else row.get("feature_value")
                if "feature_value" in row
                else row.get("value")
            )
            redacted = _is_credential_secret_key(feature_key) or _is_credential_secret_key(feature_name)
            value_present = raw_value is not None and raw_value != ""
            strategy_event_feature_rows.append(
                {
                    "source_id": source_id,
                    "source_name": "rcp_event_feature_list",
                    "feature_row_index": row_index,
                    "source_field_path": str(row.get("source_field_path") or f"$.mock_current_observation.feature_rows[{row_index - 1}]"),
                    "feature_tab": str(row.get("feature_tab") or row.get("featureGroup") or STRATEGY_EVENT_ORIGINAL_FEATURE_TAB),
                    "feature_key": feature_key or feature_name,
                    "feature_name": feature_name or feature_key,
                    "feature_type": str(row.get("feature_type") or row.get("dataType") or type(raw_value).__name__),
                    "feature_value_or_safe_ref": "redacted_safe_ref" if redacted and value_present else raw_value,
                    "value_present": bool(value_present),
                    "value_comparable": bool(row.get("value_comparable", value_present and not redacted)),
                    "comparable_type": str(row.get("comparable_type") or ("不可比较" if redacted or not value_present else "等值")),
                    "sensitive_value_policy": str(row.get("sensitive_value_policy") or ("只保留安全引用" if redacted else "原值可用")),
                    "candidate_feature_eligible": bool(row.get("candidate_feature_eligible", value_present and not redacted)),
                    "high_value_reason": row.get("high_value_reason") or ("original_tab_full_retention" if str(row.get("feature_tab") or row.get("featureGroup") or STRATEGY_EVENT_ORIGINAL_FEATURE_TAB) == STRATEGY_EVENT_ORIGINAL_FEATURE_TAB else None),
                    "missing_reason": row.get("missing_reason"),
                    "mapped_domain": str(row.get("mapped_domain") or "未知"),
                    "mapped_field_family": str(row.get("mapped_field_family") or "unknown_feature_family"),
                    "original_feature_row_retained": bool(row.get("original_feature_row_retained", str(row.get("feature_tab") or row.get("featureGroup") or STRATEGY_EVENT_ORIGINAL_FEATURE_TAB) == STRATEGY_EVENT_ORIGINAL_FEATURE_TAB)),
                    "source_quality": "completed",
                    "evidence_source": "current_observation",
                    "event_id": row.get("event_id") or fields.get("candidate_event_id") or fields.get("event_id"),
                    "event_type": row.get("event_type") or fields.get("event_type"),
                    "policy_code": row.get("policy_code") or fields.get("candidate_policy_code") or fields.get("policy_code"),
                    "event_time": row.get("event_time") or fields.get("event_time"),
                }
            )
        handles: list[dict[str, Any]] = []
        extracted_fields: list[str] = []
        candidate_device_ids: list[dict[str, Any]] = []
        field_items: list[tuple[str, Any, int | None, Any, str]] = [
            (str(field), value, None, None, f"$.mock_current_observation.{field}")
            for field, value in fields.items()
        ]
        for record_index, record in enumerate(records, start=1):
            if not isinstance(record, dict):
                continue
            record_time = record.get("record_time") or record.get("login_time") or record.get("operation_time") or record.get("publish_time") or record.get("action_time") or record.get("report_time") or record.get("enforcement_time")
            for field, value in record.items():
                if field == "record_time":
                    continue
                field_items.append(
                    (
                        str(field),
                        value,
                        record_index,
                        record_time,
                        f"$.mock_current_observation.records[{record_index - 1}].{field}",
                    )
                )
        for field, value, record_index, record_time, field_path in field_items:
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
                    "field_path": field_path,
                    "value": value_text,
                    "source_id": source_id,
                    "evidence_source": "current_observation",
                    "record_index": record_index,
                    "record_time": record_time,
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
                "strategy_event_feature_rows": strategy_event_feature_rows,
                "device_detail_rows": device_detail_rows_input,
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


def build_l3_commonality_type_distribution(
    *,
    shared_signal_items: list[dict[str, Any]],
    sequence_comparison_features: list[dict[str, Any]],
    candidate_features: list[dict[str, Any]],
) -> dict[str, Any]:
    coverage_count = len([
        item for item in shared_signal_items
        if str(item.get("commonality_type") or "") == "coverage_commonality"
    ])
    field_value_count = len([
        item for item in shared_signal_items
        if str(item.get("commonality_type") or "") in {"field_value_commonality", "known_field_commonality", "unknown_field_value_commonality"}
    ])
    field_combination_count = len([
        item for item in shared_signal_items
        if str(item.get("commonality_type") or "") == "field_combination_commonality"
    ]) + len([
        item for item in candidate_features
        if str(item.get("feature_origin") or "") == "field_combination"
    ])
    cross_source_rows: list[dict[str, Any]] = []
    for feature in candidate_features:
        domains = _feature_domains(feature)
        if len(domains) < 2:
            continue
        cross_source_rows.append(
            {
                "signal_name": f"cross_source_support_commonality:{feature.get('feature_name')}",
                "commonality_type": "cross_source_support_commonality",
                "source_domains": domains,
                "source_names": feature.get("source_names") or [],
                "support_user_count": feature.get("support_user_count"),
                "support_record_count": feature.get("support_record_count"),
                "not_final_conclusion": True,
            }
        )
    return {
        "coverage_commonality_count": coverage_count,
        "field_value_commonality_count": field_value_count,
        "field_combination_commonality_count": field_combination_count,
        "sequence_commonality_count": len(sequence_comparison_features),
        "cross_source_support_commonality_count": len(cross_source_rows),
        "coverage_commonality_boundary": "coverage_commonality only proves field visibility; it cannot support high essence or final risk judgement.",
        "cross_source_support_commonality": cross_source_rows,
    }


def build_field_value_commonality_funnel(
    *,
    strategy_event_feature_row_table: list[dict[str, Any]],
    device_detail_table: list[dict[str, Any]],
    standard_detail_table: list[dict[str, Any]],
    shared_signal_items: list[dict[str, Any]],
    candidate_features: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    raw_groups: dict[str, dict[tuple[str, str], dict[str, Any]]] = {}
    promoted_groups: dict[str, list[dict[str, Any]]] = {}

    def add_raw(source_name: str, family: str, field_name: str, value_ref: str, entity_id: str) -> None:
        if not source_name or not field_name or not value_ref or not entity_id:
            return
        group = raw_groups.setdefault(source_name, {})
        key = (field_name, value_ref)
        row = group.setdefault(
            key,
            {
                "field_family": family or field_name,
                "field_name": field_name,
                "field_value_or_safe_ref": value_ref,
                "entities": set(),
            },
        )
        row["entities"].add(entity_id)

    for row in strategy_event_feature_row_table:
        if row.get("value_present") is True and row.get("value_comparable") is True:
            add_raw(
                str(row.get("source_name") or "rcp_event_feature_list"),
                str(row.get("mapped_field_family") or row.get("feature_tab") or "unknown_field_family"),
                str(row.get("feature_key") or ""),
                str(row.get("feature_value_or_safe_ref") or ""),
                str(row.get("entity_id") or ""),
            )
    for row in device_detail_table:
        if row.get("value_present") is True and row.get("value_comparable") is True:
            add_raw(
                str(row.get("source_name") or "weapon_device_info"),
                str(row.get("mapped_field_family") or row.get("device_source_type") or "unknown_field_family"),
                str(row.get("device_field_key") or ""),
                str(row.get("device_field_value_or_safe_ref") or ""),
                str(row.get("entity_id") or ""),
            )
    for row in standard_detail_table:
        if row.get("value_present") is True and row.get("value_comparable") is True:
            add_raw(
                str(row.get("source_name") or row.get("detail_table") or "standard_detail_source"),
                str(row.get("field_family") or ("unknown_field_family" if row.get("unknown_field_family") else row.get("field_name") or "")),
                str(row.get("field_name") or ""),
                str(row.get("field_value_or_safe_ref") or ""),
                str(row.get("entity_id") or ""),
            )

    for signal in shared_signal_items:
        signal_type = str(signal.get("commonality_type") or "")
        if signal_type not in {"field_value_commonality", "known_field_commonality", "unknown_field_value_commonality"}:
            continue
        promoted_groups.setdefault(str(signal.get("source_name") or ""), []).append(signal)

    results: list[dict[str, Any]] = []
    candidate_count_by_source: dict[str, int] = {}
    for feature in candidate_features:
        for source_name in feature.get("source_names", []) or []:
            candidate_count_by_source[str(source_name)] = candidate_count_by_source.get(str(source_name), 0) + 1

    source_names = sorted(set(raw_groups.keys()) | set(promoted_groups.keys()) | set(candidate_count_by_source.keys()))
    for source_name in source_names:
        raw_rows = [
            row for row in raw_groups.get(source_name, {}).values()
            if len(row.get("entities", set())) >= 2
        ]
        raw_field_value_match_count = len(raw_rows)
        dedup_families: dict[str, list[dict[str, Any]]] = {}
        for row in raw_rows:
            dedup_families.setdefault(str(row.get("field_name") or ""), []).append(row)
        after_dedup_count = len(dedup_families)
        semantic_families: dict[str, list[dict[str, Any]]] = {}
        for row in raw_rows:
            semantic_families.setdefault(str(row.get("field_family") or "unknown_field_family"), []).append(row)
        after_semantic_grouping_count = len(semantic_families)
        promoted = promoted_groups.get(source_name, [])
        promoted_commonality_count = len(promoted)
        top_candidate_count = candidate_count_by_source.get(source_name, 0)
        suppressed_count = max(after_semantic_grouping_count - promoted_commonality_count, 0)
        suppressed_reasons: list[str] = []
        if raw_field_value_match_count and promoted_commonality_count <= max(3, raw_field_value_match_count // 5):
            suppressed_reasons.append("weak_semantics")
        if any("unknown" in str(row.get("field_family") or "") for row in raw_rows):
            suppressed_reasons.append("unknown_field")
        if source_name in {"weapon_device_app_list"}:
            suppressed_reasons.append("auxiliary_source")
            suppressed_reasons.append("high_cardinality")
        if source_name == "rcp_event_feature_list" and raw_field_value_match_count >= 50 and promoted_commonality_count < 10:
            suppressed_reasons.append("duplicate")
        if not raw_field_value_match_count:
            suppressed_reasons.append("source_quality_gap")
        sample_suppressed_field_families = sorted(
            family for family in semantic_families.keys()
            if family and all(str(item.get("field_family") or "") != family for item in promoted)
        )[:6]
        over_compressed = raw_field_value_match_count >= 20 and promoted_commonality_count <= max(5, raw_field_value_match_count // 6)
        if not raw_field_value_match_count:
            diagnosis = "no raw field value matches survived comparable filtering"
        elif over_compressed:
            diagnosis = "raw match inventory is much larger than promoted commonality; review grouping and suppression boundaries"
        else:
            diagnosis = "promoted commonality count is within expected L3 compression range"
        results.append(
            {
                "source_name": source_name,
                "raw_field_value_match_count": raw_field_value_match_count,
                "after_dedup_count": after_dedup_count,
                "after_semantic_grouping_count": after_semantic_grouping_count,
                "promoted_commonality_count": promoted_commonality_count,
                "top_candidate_count": top_candidate_count,
                "suppressed_count": suppressed_count,
                "suppressed_reasons": unique_strings(suppressed_reasons) or ["low_support"] if raw_field_value_match_count else ["source_quality_gap"],
                "sample_suppressed_field_families": sample_suppressed_field_families,
                "over_compressed": over_compressed,
                "compression_diagnosis": diagnosis,
            }
        )
    return results


def build_attack_chain_cooccurrence(
    *,
    candidate_features: list[dict[str, Any]],
    source_input_quality_table: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    quality_by_source = {str(row.get("source_name") or ""): row for row in source_input_quality_table}
    chains: list[dict[str, Any]] = []

    def chain_status(source_names: list[str]) -> str:
        relevant = [quality_by_source.get(name, {}) for name in source_names]
        if not relevant:
            return "template_only"
        if any(bool(row.get("auth_blocked")) for row in relevant):
            return "blocked"
        if any(bool(row.get("not_entered_main_chain")) for row in relevant):
            return "not_entered_main_chain"
        if any(str(row.get("source_status") or "") == "partial" for row in relevant):
            return "partial"
        return "observed"

    chain_specs = [
        ("chain_login_entry", "login_entry", {"behavior_domain"}, ["login_logs_search"]),
        ("chain_device_execution", "device_execution", {"device_domain"}, ["weapon_device_info", "weapon_device_app_list"]),
        ("chain_content_publish", "content_publish", {"content_domain"}, ["archives_photo_search", "archives_photo_profile", "archives_photo_meta"]),
        ("chain_social_funnel", "social_funnel", {"social_domain"}, ["archives_comment_search", "archives_private_message_search"]),
        ("chain_enforcement_migration", "enforcement_migration", {"feedback_domain", "enforcement_domain"}, ["archives_user_report_search", "archives_negative_report", "archives_review_logs", "archives_punish_status"]),
    ]
    for chain_id, chain_role, domains, default_sources in chain_specs:
        supporting = [
            feature for feature in candidate_features
            if domains & set(_feature_domains(feature))
        ]
        source_names = unique_strings([
            source
            for feature in supporting
            for source in feature.get("source_names", []) or []
        ]) or default_sources
        steps = unique_strings([
            step
            for feature in supporting
            for step in [
                "login_entry" if "behavior_domain" in _feature_domains(feature) and "login" in str(feature.get("feature_name") or "") else "",
                "device_execution" if "device_domain" in _feature_domains(feature) else "",
                "content_publish" if "content_domain" in _feature_domains(feature) else "",
                "social_funnel" if "social_domain" in _feature_domains(feature) else "",
                "enforcement_migration" if {"feedback_domain", "enforcement_domain"} & set(_feature_domains(feature)) else "",
            ]
            if step
        ])
        if not supporting:
            status = chain_status(source_names)
            chains.append(
                {
                    "chain_id": chain_id,
                    "chain_steps": [],
                    "involved_sources": source_names,
                    "involved_entities": [],
                    "attack_chain_role": chain_role,
                    "cooccurrence_summary": "当前没有足够候选特征支撑完整链路，只保留链路模板。",
                    "current_status": status,
                    "missing_evidence": ["candidate_unavailable_due_to_source_gap"],
                    "candidate_only_not_final_conclusion": True,
                }
            )
            continue
        chains.append(
            {
                "chain_id": chain_id,
                "chain_steps": steps or [chain_role],
                "involved_sources": source_names,
                "involved_entities": unique_strings([
                    str(item)
                    for feature in supporting
                    for item in feature.get("supporting_current_evidence", []) or []
                    if str(item)
                ])[:20],
                "attack_chain_role": chain_role,
                "cooccurrence_summary": f"当前样本内可见 {chain_role} 相关证据共现，用于还原作恶链路，不自动升级为关键卡口。",
                "current_status": chain_status(source_names),
                "missing_evidence": unique_strings([
                    item
                    for feature in supporting
                    for item in feature.get("missing_evidence", []) or []
                ])[:8],
                "candidate_only_not_final_conclusion": True,
            }
        )
    return chains


def attach_attack_chain_links_to_candidates(
    *,
    candidate_features: list[dict[str, Any]],
    attack_chain_cooccurrence: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    updated: list[dict[str, Any]] = []
    for feature in candidate_features:
        item = dict(feature)
        domains = set(_feature_domains(item))
        chain_ids = []
        for chain in attack_chain_cooccurrence:
            role = str(chain.get("attack_chain_role") or "")
            if role == "login_entry" and "behavior_domain" in domains:
                chain_ids.append(str(chain.get("chain_id")))
            elif role == "device_execution" and "device_domain" in domains:
                chain_ids.append(str(chain.get("chain_id")))
            elif role == "content_publish" and "content_domain" in domains:
                chain_ids.append(str(chain.get("chain_id")))
            elif role == "social_funnel" and "social_domain" in domains:
                chain_ids.append(str(chain.get("chain_id")))
            elif role == "enforcement_migration" and ({"feedback_domain", "enforcement_domain"} & domains):
                chain_ids.append(str(chain.get("chain_id")))
        item["supporting_attack_chain_ids"] = unique_strings(chain_ids)
        updated.append(item)
    return updated



def _g_r5_top_candidate_score(item: dict[str, Any]) -> tuple:
    """G-R5: 业务解释力优先排序分 — 越小越优先展示"""
    choke = str(item.get("risk_choke_point_type") or "unknown")
    likeness = str(item.get("choke_point_likeness") or "unknown")
    essence = str(item.get("essence_likeness") or "unknown")
    fn = str(item.get("candidate_feature_name") or item.get("feature_name") or "")
    core = item.get("core_commonality") or []
    src = item.get("source_support") or item.get("source_names") or []
    missing = item.get("missing_evidence") or []
    # 1. unknown choke type 降级
    unknown_penalty = 0 if choke != "unknown" else 2
    # 2. unknown/device_unknown field 候选额外降级（不进主 Top）
    _REVIEW_QUEUE_NAMES = {
        "device_unknown_field_enrichment_candidate",
        "unknown_field_enrichment_candidate",
        "rcp_unknown_feature_bundle_candidate",
        "account_unknown_field_enrichment_candidate",
    }
    if fn in _REVIEW_QUEUE_NAMES:
        unknown_penalty = 4
    # 3. core 仅 fallback 降级
    fallback_core = (
        core == ["insufficient_interpretable_commonality"]
        or core in (["unknown_device_field_bundle"], ["unknown_field_bundle"])
    )
    core_penalty = 1 if fallback_core else 0
    # 4. missing_evidence 只有 needs_field_dictionary_review 且 choke=unknown → 送入 review_queue
    dict_review_only = missing == ["needs_field_dictionary_review"] or (
        missing and all(
            m in {"needs_field_dictionary_review", "L4_validation_required"}
            for m in missing
        )
    )
    review_queue_penalty = 1 if (choke == "unknown" and dict_review_only) else 0
    # 5. likeness 优先
    likeness_rank = {"high": 0, "medium": 1, "low": 2, "unknown": 3}.get(likeness, 9)
    essence_rank = {"high": 0, "medium": 1, "low": 2, "unknown": 3}.get(essence, 9)
    # 6. source 有真实 source_names 优先
    src_bonus = 0 if src else 1
    # 7. cross domain 优先
    doms = item.get("supporting_source_domains") or []
    cross_domain_bonus = 0 if len(doms) >= 2 else 1
    return (
        unknown_penalty + review_queue_penalty,
        core_penalty,
        likeness_rank,
        essence_rank,
        src_bonus,
        cross_domain_bonus,
        -float(item.get("priority_score") or 0),
        -float(item.get("support_ratio") or 0),
        str(item.get("feature_name") or ""),
    )

def build_candidate_feature_top_samples(
    *,
    candidate_features: list[dict[str, Any]],
    source_input_quality_table: list[dict[str, Any]],
    attack_chain_cooccurrence: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    quality_by_source = {str(row.get("source_name") or ""): row for row in source_input_quality_table}

    def top_feature(predicate) -> dict[str, Any] | None:
        matches = [feature for feature in candidate_features if predicate(feature)]
        if not matches:
            return None
        # G-R5: 业务解释力优先排序
        matches.sort(key=_g_r5_top_candidate_score)
        return matches[0]

    def sample_from_feature(feature: dict[str, Any], *, default_status: str = "observed") -> dict[str, Any]:
        choke_type = str(feature.get("risk_choke_point_type") or "unknown")
        display_name = (
            f"{choke_type}_candidate"
            if choke_type != "unknown"
            else feature.get("feature_name")
        )
        return {
            "candidate_feature_name": display_name,
            "feature_origin": feature.get("feature_origin"),
            "source_support": feature.get("source_names") or [],
            "evidence_commonality_types": [t for t in (feature.get("supporting_commonality_types") or []) if t and str(t).strip()],
            "core_commonality": feature.get("field_combination") or feature.get("source_fields") or [],
            "attack_chain_support": feature.get("supporting_attack_chain_ids") or [],
            "risk_choke_point_type": choke_type,
            "choke_point_likeness": feature.get("choke_point_likeness"),
            "choke_point_reason": feature.get("choke_point_reason"),
            "required_for_attack": feature.get("required_for_attack"),
            "easy_to_evade_if_changed": feature.get("easy_to_evade_if_changed"),
            "robustness": feature.get("robustness"),
            "essence_likeness": feature.get("essence_likeness"),
            "essence_reason": feature.get("essence_reason"),
            "false_positive_risk": feature.get("false_positive_risk"),
            "missing_evidence": feature.get("missing_evidence"),
            "validation_method": feature.get("validation_method"),
            "current_status": default_status,
            "candidate_only_not_final_conclusion": True,
        }

    def blocked_or_template(source_names: list[str], message: str) -> dict[str, Any]:
        relevant = [quality_by_source[name] for name in source_names if name in quality_by_source]
        if any(bool(row.get("auth_blocked")) for row in relevant):
            status = "blocked"
        elif any(bool(row.get("not_entered_main_chain")) for row in relevant):
            status = "not_entered_main_chain"
        else:
            status = "template_only"
        return {
            "candidate_feature_name": message,
            "feature_origin": "template_only",
            "source_support": source_names,
            "evidence_commonality_types": [],
            "core_commonality": [],
            "attack_chain_support": [],
            "risk_choke_point_type": "unknown",
            "choke_point_likeness": "unknown",
            "choke_point_reason": "当前没有足够 source 字段支撑关键卡口判断。",
            "required_for_attack": "unknown",
            "easy_to_evade_if_changed": "unknown",
            "robustness": "unknown",
            "essence_likeness": "unknown",
            "essence_reason": "字段族未解释或缺少行为链路验证，当前仅保留为候选共性。",
            "false_positive_risk": "当前没有足够 source 字段支撑，不能根据 gap 推断低风险或高风险。",
            "missing_evidence": ["candidate_unavailable_due_to_source_gap"],
            "validation_method": "先修 source gap，再进入字段值/字段组合/序列比较。",
            "current_status": status,
            "candidate_only_not_final_conclusion": True,
        }

    samples: list[dict[str, Any]] = []
    rcp_feature = top_feature(lambda item: "strategy_domain" in _feature_domains(item))
    samples.append(sample_from_feature(rcp_feature) if rcp_feature else blocked_or_template(["rcp_event_feature_list"], "rcp_candidate_unavailable_due_to_source_gap"))
    device_feature = top_feature(lambda item: str(item.get("risk_choke_point_type") or "") == "device_farm_template" or "device_domain" in _feature_domains(item))
    samples.append(sample_from_feature(device_feature) if device_feature else blocked_or_template(["weapon_device_info", "weapon_device_app_list"], "device_candidate_unavailable_due_to_source_gap"))
    login_feature = top_feature(lambda item: str(item.get("risk_choke_point_type") or "") in {"protocol_constraint_gap", "control_execution_separation", "account_control_transfer", "automation_rhythm"} and ("behavior_domain" in _feature_domains(item) or "login" in str(item.get("feature_name") or "")))
    samples.append(sample_from_feature(login_feature) if login_feature else blocked_or_template(["login_logs_search"], "login_candidate_unavailable_due_to_source_gap"))
    account_feature = top_feature(lambda item: "account_domain" in _feature_domains(item) or "user_behavior_summary_detail_table" in " ".join([str(x) for x in item.get("source_names", []) or []]))
    samples.append(sample_from_feature(account_feature) if account_feature else blocked_or_template(["archives_user_analysis", "archives_user_profile"], "account_candidate_unavailable_due_to_source_gap"))
    content_social_feature = top_feature(lambda item: str(item.get("risk_choke_point_type") or "") == "content_funnel_dependency" or ("content_domain" in _feature_domains(item) or "social_domain" in _feature_domains(item)))
    samples.append(sample_from_feature(content_social_feature) if content_social_feature else blocked_or_template(["archives_photo_search", "archives_comment_search", "archives_private_message_search"], "content_social_candidate_unavailable_due_to_source_gap"))
    return samples



def _build_l3_candidate_quality_summary(candidate_features: list[dict[str, Any]]) -> dict[str, Any]:
    """G-R5: 生成 l3_candidate_quality_summary 摘要"""
    total = len(candidate_features)
    _REVIEW_QUEUE_NAMES = {
        "device_unknown_field_enrichment_candidate",
        "unknown_field_enrichment_candidate",
        "rcp_unknown_feature_bundle_candidate",
        "account_unknown_field_enrichment_candidate",
    }
    _GENERIC_NAMES = {
        "multi_domain_anchor_overlap_candidate",
        "group_level_field_enrichment_candidate",
        "hard_single_field_signal_candidate",
    }
    unknown_count = sum(1 for c in candidate_features if str(c.get("risk_choke_point_type") or "unknown") == "unknown")
    unknown_device_review = sum(
        1 for c in candidate_features
        if str(c.get("candidate_feature_name") or "") in _REVIEW_QUEUE_NAMES
    )
    high_medium_explainable = sum(
        1 for c in candidate_features
        if str(c.get("choke_point_likeness") or "unknown") in ("high", "medium")
        and str(c.get("risk_choke_point_type") or "unknown") != "unknown"
        and c.get("core_commonality")
    )
    generic_downranked = sum(
        1 for c in candidate_features
        if str(c.get("feature_name") or "") in _GENERIC_NAMES
    )
    candidate_only_count = sum(1 for c in candidate_features if c.get("candidate_only_not_final_conclusion") is True)
    return {
        "candidate_features_total": total,
        "top_candidate_count": min(total, 5),
        "unknown_candidate_count": unknown_count,
        "unknown_device_review_count": unknown_device_review,
        "high_medium_explainable_count": high_medium_explainable,
        "generic_downranked_count": generic_downranked,
        "candidate_only_not_final_conclusion_count": candidate_only_count,
        "group_not_confirmed": True,
    }


def _materialize_candidate_evidence(
    candidate: dict,
    source_input_quality_table: list[dict] | None = None,
) -> dict:
    """G-R6 enhanced evidence materialization.
    Changes vs G-R5b:
    - source_status now follows completed/partial/blocked/timeout mapping (not just unknown)
    - evidence_display_label / internal_signal_name / raw_field_path / field_role / dictionary_status
    - candidate_support_summary with support_ratio
    - value-level counter signals (active_minutes >= 300, same_device=true token)
    - protocol: missing fields are NOT positive evidence (field_missing vs event_path_unverified)
    - risk_semantics_strength: strong/medium/weak/unknown
    - field_dictionary_review_queue eligibility
    - final_evidence_card bridge fields
    """
    # ── source quality lookup ──────────────────────────────────────────────
    quality_by_source: dict[str, dict] = {}
    if source_input_quality_table:
        for row in source_input_quality_table:
            sn = str(row.get("source_name") or row.get("source_id") or "")
            if sn:
                quality_by_source[sn] = row

    source_names: list[str] = [
        str(s) for s in (candidate.get("source_support") or candidate.get("source_names") or []) if s
    ]
    field_combo: list[str] = [str(f) for f in (candidate.get("field_combination") or []) if f]
    src_fields: list[str] = [str(f) for f in (candidate.get("source_fields") or []) if f]
    core_comm_raw = candidate.get("core_commonality") or []
    core_comm: list[str] = [str(c) for c in core_comm_raw if c] if isinstance(core_comm_raw, list) else [str(core_comm_raw)] if core_comm_raw else []
    missing_ev: list[str] = list(candidate.get("missing_evidence") or [])
    choke_type: str = str(candidate.get("risk_choke_point_type") or "unknown")
    likeness: str = str(candidate.get("choke_point_likeness") or "unknown")
    feature_name: str = str(candidate.get("feature_name") or "")
    candidate_name: str = str(candidate.get("candidate_feature_name") or "")
    reason_codes: list[str] = [str(r) for r in (candidate.get("reason_codes") or []) if r]
    essence_reason: str = str(candidate.get("essence_reason") or "")
    domains: list[str] = list(candidate.get("supporting_source_domains") or [])
    # support metrics
    support_user_count = candidate.get("support_user_count") or candidate.get("support_entity_count") or 0
    support_sample_count = candidate.get("support_sample_count") or candidate.get("support_count") or support_user_count
    support_record_count = candidate.get("support_record_count") or 0
    support_ratio = candidate.get("support_ratio")

    # ── G-R6: compute support_ratio if missing ────────────────────────────
    if support_ratio is None and support_user_count and support_sample_count and support_sample_count > 0:
        support_ratio = round(float(support_user_count) / float(support_sample_count), 4)
    elif support_ratio is None and support_user_count:
        support_ratio = None  # sample_count unknown

    # ── token sets ──────────────────────────────────────────────────────────
    _TEMPLATE_PHRASES = {
        "backend_action_signal present",
        "missing_or_weak_frontend_activity",
        "login_or_behavior_side != execution_side",
        "strategy request detail template",
        "content template",
        "same funnel path",
        "weak_frontend_activity",
        "backend_action_signal + weak_frontend_activity",
    }
    # G-R6: missing field prefix tokens — these are NOT positive evidence
    _MISSING_FIELD_PREFIXES = (
        "missing_", "not_joined_", "unverified_", "not_materialized_",
    )
    # mismatch tokens (must exist for control_execution_separation)
    _MISMATCH_TOKENS = {
        "login_did", "action_did", "weapon_did",
        "login_device_id", "action_device_id", "weapon_device_id",
        "login_ip", "action_ip", "ip_region",
        "login_ua", "action_ua", "app_version",
        "mismatch", "inconsistent", "device_switch",
        "left_scene", "right_scene",
    }
    _SAME_DEVICE_TOKENS = {
        "same_device_id", "same_did", "stable_device_lineage",
        "no_device_switch", "consistent_device",
    }
    _HIGH_ACTIVITY_TOKENS = {
        "active_minutes_today", "frontend_activity_high",
        "high_active_minutes", "active_duration",
    }
    # G-R6: risk-bearing device field tokens
    _DEVICE_RISK_TOKENS = {
        "frida", "xposed", "emulator", "hook", "debug", "adbstatus",
        "root", "magisk", "fake_device", "device_farm", "abnormal_device",
        "risky_device", "mock_device", "simulator",
    }
    # G-R6: status/context field tokens (weak risk semantics)
    _STATUS_CONTEXT_TOKENS = {
        "account_status", "code", "color", "caller", "caller_catalog",
        "callerkn", "callerksn", "webservice", "http_status", "status_code",
        "default_enum", "id_field",
    }
    # G-R6: protocol evidence tokens (positive anomalies, not missing)
    _PROTOCOL_POSITIVE_TOKENS = {
        "request_path_anomaly", "scene_mismatch", "entry_mismatch",
        "client_path_bypass", "frontend_backend_inconsistency",
        "request_forgery", "path_hijack",
    }
    _ANCHOR_ONLY = {"device_id", "did", "policy_code", "source_id", "uid", "user_id"}

    # ── G-R6: source_status mapping ───────────────────────────────────────
    def _source_status(sname: str) -> str:
        row = quality_by_source.get(sname)
        if not row:
            return "unknown"
        if row.get("auth_blocked"):
            return "blocked"
        if row.get("not_entered_main_chain"):
            return "not_entered_main_chain"
        cls = str(row.get("quality_class") or row.get("source_status") or "")
        _BLOCKED = ("blocked", "auth_blocked", "auth_failed", "no_data", "planned")
        _PARTIAL = ("partial", "response_limited", "capped")
        if cls in _BLOCKED or row.get("is_blocked"):
            return "blocked"
        if cls == "timeout" or row.get("is_timeout"):
            return "timeout"
        if cls == "not_entered_main_chain":
            return "not_entered_main_chain"
        if cls == "completed":
            return "completed"
        if cls in _PARTIAL:
            return "partial"
        return "unknown"

    def _source_status_reason(sname: str) -> str | None:
        st = _source_status(sname)
        if st == "unknown":
            return "source_not_in_quality_table_or_status_unresolved"
        return None

    def _is_observable_source(sname: str) -> bool:
        st = _source_status(sname)
        return st in ("completed", "partial", "response_limited", "unknown")

    def _evidence_strength_from_status(st: str) -> str:
        if st == "completed":
            return "strong"
        if st in ("partial", "response_limited", "capped"):
            return "medium"
        return "weak"

    # ── G-R6: field semantics classification ──────────────────────────────
    def _classify_field(fname: str) -> tuple[str, str]:
        """Return (field_role, dictionary_status)."""
        fl = fname.lower()
        if any(tok in fl for tok in _DEVICE_RISK_TOKENS):
            return "risk_signal", "known"
        if any(fl.startswith(pfx) for pfx in _MISSING_FIELD_PREFIXES):
            return "context", "needs_field_dictionary_review"
        if any(tok in fl for tok in _STATUS_CONTEXT_TOKENS):
            return "status_field", "known"
        if fl in _ANCHOR_ONLY:
            return "anchor", "known"
        if any(tok in fl for tok in {
            "template", "funnel", "request_path", "request_scene", "entry",
            "frontend_activity", "backend_action", "rcp_event", "login_event",
        }):
            return "context", "needs_field_dictionary_review"
        return "unknown", "needs_field_dictionary_review"

    def _is_missing_field_token(fname: str) -> bool:
        fl = fname.lower()
        return any(fl.startswith(pfx) for pfx in _MISSING_FIELD_PREFIXES) or "missing" in fl

    # G-R6: display label normalization
    _INTERNAL_SIGNAL_DISPLAY = {
        "frida_xposed_mount_reset_or_emulator_related_field_truthy": (
            "设备对抗环境字段组合",
            "疑似 Hook / 模拟器 / 调试 / 改机相关设备环境信号",
            "只能说设备环境模板化候选，不能直接断言具体 Frida/Xposed/模拟器工具",
        ),
        "backend_action_signal present": (
            "事件级后端行为信号",
            "后端存在行为类事件记录（具体字段路径需进一步 join）",
            "需要字段值级 join 才能确认，不能直接作为强证据",
        ),
        "missing_or_weak_frontend_activity": (
            "事件级客户端路径字段未 materialize",
            "当前输出中 request_path / request_scene / entry 等事件路径字段缺失或未 join",
            "只能说 event-level client/request path unverified，不能说 confirmed protocol bypass",
        ),
        "login_or_behavior_side != execution_side": (
            "登录侧与执行侧设备/行为待核查",
            "尚未完成字段级 device_id / IP / UA join；仅为 source 共现推断",
            "需要字段值级 mismatch 才能 materialize",
        ),
    }

    def _get_display_info(fname: str) -> tuple[str, str, str]:
        """Return (display_label, description, boundary). Falls back gracefully."""
        if fname in _INTERNAL_SIGNAL_DISPLAY:
            return _INTERNAL_SIGNAL_DISPLAY[fname]
        fl = fname.lower()
        if any(tok in fl for tok in _DEVICE_RISK_TOKENS):
            return (
                "设备对抗环境字段组合",
                f"设备风险相关字段信号: {fname}",
                "只能说设备环境候选；需字段语义字典确认具体风险含义",
            )
        if any(fl.startswith(pfx) for pfx in _MISSING_FIELD_PREFIXES) or "missing" in fl:
            return (
                "事件级路径字段缺失/未 join",
                f"字段 {fname} 缺失或未 materialize，不是正向异常证据",
                "event path unverified; field join required",
            )
        # default: use field name as label (unrecognized)
        return (fname, f"字段: {fname}", "needs_field_dictionary_review")

    # ── G-R6: risk_semantics_strength ─────────────────────────────────────
    def _infer_risk_semantics_strength(fields: list[str], choke: str) -> str:
        all_fields = " ".join(f.lower() for f in fields)
        if any(tok in all_fields for tok in _DEVICE_RISK_TOKENS):
            return "strong" if choke in ("device_farm_template", "risky_device_environment") else "medium"
        if choke in ("protocol_constraint_gap", "control_execution_separation",
                     "account_control_transfer", "post_enforcement_migration"):
            if any(tok in all_fields for tok in _MISMATCH_TOKENS | _PROTOCOL_POSITIVE_TOKENS):
                return "medium"
            return "weak"
        if choke == "automation_rhythm":
            return "medium"
        if any(tok in all_fields for tok in _STATUS_CONTEXT_TOKENS):
            return "weak"
        return "unknown"

    # ── effective fields (non-anchor, non-missing) ────────────────────────
    all_raw_fields = field_combo + src_fields
    effective_fields_raw = [f for f in all_raw_fields if f.lower() not in _ANCHOR_ONLY]
    # split into positive vs missing
    positive_fields = [f for f in effective_fields_raw if not _is_missing_field_token(f)]
    missing_only_fields = [f for f in effective_fields_raw if _is_missing_field_token(f)]

    # ── text blob for token detection ─────────────────────────────────────
    text_blob = " ".join([essence_reason] + reason_codes + core_comm + field_combo + src_fields).lower()

    # ── G-R6: value-level counter detection ──────────────────────────────
    # High activity: check for numeric values >= 300 in text_blob
    has_high_activity_token = any(tok in text_blob for tok in _HIGH_ACTIVITY_TOKENS)
    has_high_activity_value = False
    if has_high_activity_token:
        import re as _re
        nums = [int(m.group()) for m in _re.finditer(r'[0-9]+', text_blob)]
        has_high_activity_value = any(n >= 300 for n in nums)
    has_high_activity_counter = has_high_activity_value  # value-level

    # Same device: check for truthy value tokens
    has_same_device_token = any(tok in text_blob for tok in _SAME_DEVICE_TOKENS)
    has_same_device_value = has_same_device_token and any(
        v in text_blob for v in ("=true", "=1", ": true", ":true", "same_did_match")
    )
    # If no value found but token present, treat as token-only (not strong)
    has_same_device_counter = has_same_device_value  # value-level only

    # Field-level mismatch (control_execution_separation)
    has_field_mismatch = any(tok in text_blob for tok in _MISMATCH_TOKENS)
    # G-R6: missing field tokens are NOT positive mismatch evidence
    has_positive_mismatch = has_field_mismatch and not all(
        _is_missing_field_token(f) for f in effective_fields_raw if any(
            tok in f.lower() for tok in _MISMATCH_TOKENS
        )
    )

    # Protocol positive evidence (G-R6: missing≠positive)
    has_protocol_positive = any(tok in text_blob for tok in _PROTOCOL_POSITIVE_TOKENS)
    all_fields_are_missing = bool(effective_fields_raw) and all(
        _is_missing_field_token(f) for f in effective_fields_raw
    )

    # ── build supporting_evidence ─────────────────────────────────────────
    supporting_evidence: list[dict] = []
    for src in source_names:
        if not _is_observable_source(src):
            continue
        st = _source_status(src)
        ev_strength = _evidence_strength_from_status(st)
        # only positive fields (not missing)
        related = [f for f in positive_fields if f not in _TEMPLATE_PHRASES]
        if not related:
            continue
        raw_fps = related[:3]
        int_sig = candidate_name or choke_type
        display_label, description, boundary = _get_display_info(raw_fps[0] if raw_fps else int_sig)
        role, dict_status = _classify_field(raw_fps[0] if raw_fps else "")
        # G-R6: internal_signal → max weak unless raw_field_path present
        if all(f in _INTERNAL_SIGNAL_DISPLAY or any(f.lower() == k for k in _INTERNAL_SIGNAL_DISPLAY) for f in raw_fps):
            ev_strength = "weak"
            dict_status = "needs_field_dictionary_review"
        supporting_evidence.append({
            "source_name": src,
            "source_status": st,
            "source_status_reason": _source_status_reason(src),
            # G-R6 new fields
            "raw_field_path": raw_fps,
            "internal_signal_name": candidate_name or choke_type,
            "evidence_display_label": display_label,
            "evidence_description": description,
            "field_role": role,
            "dictionary_status": dict_status,
            # existing
            "value_summary": f"field_commonality_observed: {', '.join(raw_fps)}",
            "evidence_role": "support",
            "evidence_strength": ev_strength,
            "allowed_claim_boundary": boundary,
            # G-R6: support metrics per-evidence
            "support_user_count": support_user_count,
            "sample_user_count": support_sample_count,
            "support_ratio": support_ratio,
            "support_record_count": support_record_count,
            "support_ratio_unknown_reason": None if support_ratio is not None else "sample_count_unknown",
        })

    # fallback: clean core_comm with positive fields only
    clean_core = [c for c in core_comm
                  if c not in _TEMPLATE_PHRASES
                  and c not in {"insufficient_interpretable_commonality", "unknown_device_field_bundle", "unknown_field_bundle"}
                  and not _is_missing_field_token(c)]
    if clean_core and not supporting_evidence:
        observable_srcs = [s for s in source_names if _is_observable_source(s)]
        if observable_srcs:
            st = _source_status(observable_srcs[0])
            ev_strength = _evidence_strength_from_status(st)
            disp, desc, bnd = _get_display_info(clean_core[0])
            role, dict_status = _classify_field(clean_core[0])
            supporting_evidence.append({
                "source_name": observable_srcs[0],
                "source_status": st,
                "source_status_reason": _source_status_reason(observable_srcs[0]),
                "raw_field_path": clean_core[:3],
                "internal_signal_name": candidate_name or choke_type,
                "evidence_display_label": disp,
                "evidence_description": desc,
                "field_role": role,
                "dictionary_status": dict_status,
                "value_summary": f"field_combination_commonality: {', '.join(clean_core[:3])}",
                "evidence_role": "support",
                "evidence_strength": "medium",
                "allowed_claim_boundary": bnd,
                "support_user_count": support_user_count,
                "sample_user_count": support_sample_count,
                "support_ratio": support_ratio,
                "support_record_count": support_record_count,
                "support_ratio_unknown_reason": None if support_ratio is not None else "sample_count_unknown",
            })

    # ── counter_evidence ──────────────────────────────────────────────────
    counter_evidence: list[dict] = []
    if has_high_activity_counter:
        counter_evidence.append({
            "source_name": "archives_user_analysis",
            "field_path": "active_minutes_today",
            "value_summary": "active_minutes_today >= 300 observed; day-level activity confirmed high",
            "reason_it_weakens_claim": "missing_or_weak_frontend_activity cannot be claimed; only event-level path join is unverified",
            "evidence_strength": "strong",
            "counter_signal_type": "high_frontend_activity_counter_signal",
            "value_threshold_used": "active_minutes >= 300",
        })
    elif has_high_activity_token and not has_high_activity_value:
        counter_evidence.append({
            "source_name": "archives_user_analysis",
            "field_path": "active_minutes_today",
            "value_summary": "active_minutes_today field present but value not resolved (token-only detection)",
            "reason_it_weakens_claim": "token-only; value-level threshold not confirmed; counter not strong",
            "evidence_strength": "weak",
            "counter_signal_type": "high_frontend_activity_token_only",
            "value_threshold_used": "field_name_token_only_no_value",
        })
    if has_same_device_counter:
        counter_evidence.append({
            "source_name": "weapon_inventory",
            "field_path": "device_id / did",
            "value_summary": "same_device=true or device_id equality confirmed; no device switch detected",
            "reason_it_weakens_claim": "login_or_behavior_side != execution_side cannot be claimed without field mismatch",
            "evidence_strength": "strong",
            "counter_signal_type": "same_device_counter_signal",
            "value_threshold_used": "same_device_value_token_present",
        })
    elif has_same_device_token and not has_same_device_value:
        counter_evidence.append({
            "source_name": "weapon_inventory",
            "field_path": "device_id / did",
            "value_summary": "same_device token found but value not confirmed (token-only)",
            "reason_it_weakens_claim": "token-only detection; value join not materialized; counter not strong",
            "evidence_strength": "weak",
            "counter_signal_type": "same_device_token_only",
            "value_threshold_used": "field_name_token_only_no_value",
        })

    # ── risk_semantics_strength ───────────────────────────────────────────
    risk_semantics = _infer_risk_semantics_strength(all_raw_fields, choke_type)

    # ── candidate_support_summary ─────────────────────────────────────────
    candidate_support_summary = {
        "support_user_count": support_user_count,
        "support_sample_count": support_sample_count,
        "support_entity_count": candidate.get("support_entity_count") or support_user_count,
        "support_record_count": support_record_count,
        "support_ratio": support_ratio,
        "support_ratio_unknown_reason": None if support_ratio is not None else "sample_count_unknown",
        "source_count": len(source_names),
        "supporting_source_domains": domains,
    }

    # ── claim_materialization rules ───────────────────────────────────────
    claim_materialized = True
    materialization_reason = ""
    overclaim_risk = "low"
    allowed_claim_boundary = ""
    core_claim = candidate_name or feature_name or choke_type

    # Rule 1: protocol_constraint_gap + high activity (value-level)
    if has_high_activity_counter and choke_type == "protocol_constraint_gap":
        claim_materialized = False
        materialization_reason = "high_frontend_activity_counter_signal (value-level: >=300 min); missing_or_weak_frontend_activity is overclaim"
        overclaim_risk = "high"
        core_claim = "event_frontend_path_unverified"
        allowed_claim_boundary = "can only claim event-level client path not validated, not weak frontend activity"
        if "event_level_frontend_path_join" not in missing_ev:
            missing_ev.append("event_level_frontend_path_join")

    # Rule 1b: protocol_constraint_gap + all fields are missing-type
    elif choke_type == "protocol_constraint_gap" and all_fields_are_missing and not has_protocol_positive:
        claim_materialized = False
        materialization_reason = "all supporting fields are missing/unverified type; no positive protocol anomaly evidence"
        overclaim_risk = "high"
        core_claim = "event_frontend_path_unverified"
        allowed_claim_boundary = "event path unverified; field missing != protocol bypass; positive anomaly required"
        if "field_missing_not_positive_protocol_evidence" not in missing_ev:
            missing_ev.append("field_missing_not_positive_protocol_evidence")
        if "protocol_positive_anomaly_required" not in missing_ev:
            missing_ev.append("protocol_positive_anomaly_required")

    # Rule 2: control_execution_separation + no positive mismatch
    elif choke_type == "control_execution_separation" and not has_positive_mismatch:
        claim_materialized = False
        materialization_reason = "no field-level device/IP/UA mismatch materialized; only source co-occurrence or missing fields"
        overclaim_risk = "high"
        allowed_claim_boundary = "source co-occurrence only; field join missing; login_action_device_join required"
        core_claim = "device_action_mismatch_not_materialized"
        if "field_level_mismatch_not_materialized" not in missing_ev:
            missing_ev.append("field_level_mismatch_not_materialized")
        if "login_action_device_join_required" not in missing_ev:
            missing_ev.append("login_action_device_join_required")

    # Rule 3: control_execution_separation + same_device (value-level)
    elif choke_type == "control_execution_separation" and has_same_device_counter:
        claim_materialized = False
        materialization_reason = "same_device_counter_signal (value-level); device matches login-side"
        overclaim_risk = "high"
        core_claim = "device_action_mismatch_not_materialized"
        allowed_claim_boundary = "device/action mismatch not materialized; same device observed"

    # Rule 4: no supporting_evidence
    elif not supporting_evidence:
        claim_materialized = False
        materialization_reason = "no field-level supporting evidence; only template phrases or blocked sources"
        overclaim_risk = "medium"
        allowed_claim_boundary = "no materialized field evidence; candidate in review queue"

    # Rule 5: all sources blocked/timeout
    elif source_names and all(not _is_observable_source(s) for s in source_names):
        claim_materialized = False
        materialization_reason = "all sources blocked or not entered main chain"
        overclaim_risk = "medium"
        allowed_claim_boundary = "source gap; cannot claim observed"

    else:
        src_list = [e["source_name"] for e in supporting_evidence[:2]]
        materialization_reason = f"field-level evidence from {src_list}"
        overclaim_risk = "low" if likeness in ("high", "medium") else "medium"
        allowed_claim_boundary = (
            f"evidence limited to: {', '.join(src_list)}; candidate_only_not_final_conclusion=true"
        )

    # Downgrade likeness if not materialized
    final_likeness = likeness
    if not claim_materialized and likeness in ("high", "medium"):
        final_likeness = "low"

    # G-R6: risk_semantics + status/context field downgrade
    # status/context/default_enum fields should not be high/medium
    if risk_semantics == "weak" and final_likeness in ("high", "medium"):
        final_likeness = "low"
        if "status_or_context_field_downranked" not in missing_ev:
            missing_ev.append("status_or_context_field_downranked")

    # current_status
    if not claim_materialized:
        if source_names and all(not _is_observable_source(s) for s in source_names):
            current_status = "source_gap"
        elif all_fields_are_missing:
            current_status = "field_missing_not_positive"
        else:
            current_status = "field_not_joined"
    elif supporting_evidence:
        current_status = "partial" if any(e["evidence_strength"] != "strong" for e in supporting_evidence) else "observed"
    else:
        current_status = "template_only"

    # evidence_strength summary
    if not supporting_evidence:
        evidence_strength = "none"
    elif all(e["evidence_strength"] == "strong" for e in supporting_evidence):
        evidence_strength = "strong"
    elif any(e["evidence_strength"] == "strong" for e in supporting_evidence):
        evidence_strength = "medium"
    else:
        evidence_strength = "weak"

    # source_status_summary
    source_status_summary = {}
    for s in source_names:
        st = _source_status(s)
        reason = _source_status_reason(s)
        source_status_summary[s] = {"status": st, "unknown_reason": reason} if reason else st

    # missing_evidence: add missing field paths if they exist and aren't already noted
    if missing_only_fields and "missing_field_paths_present" not in missing_ev:
        missing_ev.append("missing_field_paths_present")

    # top_candidate_eligible: G-R6 semantics-aware
    top_candidate_eligible = (
        claim_materialized and
        bool(supporting_evidence) and
        risk_semantics in ("strong", "medium") and
        choke_type not in ("unknown",)
    )

    # field_dictionary_review_eligible
    field_dictionary_review_eligible = (
        not top_candidate_eligible or
        any(e.get("dictionary_status") == "needs_field_dictionary_review" for e in supporting_evidence)
    )

    return {
        "core_claim": core_claim,
        "risk_semantics_strength": risk_semantics,
        "candidate_support_summary": candidate_support_summary,
        "supporting_evidence": supporting_evidence,
        "counter_evidence": counter_evidence,
        "missing_evidence": missing_ev,
        "claim_materialized": claim_materialized,
        "claim_materialization_reason": materialization_reason,
        "allowed_claim_boundary": allowed_claim_boundary,
        "overclaim_risk": overclaim_risk,
        "evidence_status": "materialized" if claim_materialized else "unmaterialized",
        "evidence_strength": evidence_strength,
        "source_status_summary": source_status_summary,
        "choke_point_likeness_after_gate": final_likeness,
        "current_status": current_status,
        "top_candidate_eligible": top_candidate_eligible,
        "field_dictionary_review_eligible": field_dictionary_review_eligible,
    }


def _build_top_explainable_candidates(
    candidate_features: list[dict[str, Any]],
    source_input_quality_table: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """G-R6-fix: Top 层严格 gate。
    只有同时满足以下全部条件的候选才进入 top_explainable_risk_choke_point_candidates:
      - top_candidate_eligible=True
      - claim_materialized=True
      - evidence_strength not in (weak, none)  OR  risk_semantics_strength in (strong, medium)
      - risk_choke_point_type in _EXPLAINABLE_TYPES (non-unknown)
    不满足的候选根据情况分流到 high_coverage / weak_materialized / review_queue。
    返回 dict 包含: candidates, empty_reason (if empty)
    """
    _EXPLAINABLE_TYPES = [
        "protocol_constraint_gap",
        "control_execution_separation",
        "device_farm_template",
        "account_control_transfer",
        "content_funnel_dependency",
        "post_enforcement_migration",
        "automation_rhythm",
    ]
    result: list[dict[str, Any]] = []
    seen_types: set[str] = set()
    # Sort: best first (risk_semantics strong > medium > evidence_strength > support_ratio)
    sorted_cfs = sorted(candidate_features, key=_g_r5_top_candidate_score)
    for c in sorted_cfs:
        ctype = str(c.get("risk_choke_point_type") or "unknown")
        if ctype not in _EXPLAINABLE_TYPES:
            continue
        if ctype in seen_types:
            continue
        mat = _materialize_candidate_evidence(c, source_input_quality_table or [])
        seen_types.add(ctype)
        # G-R6-fix: strict gate — only top_candidate_eligible=True passes
        if not mat.get("top_candidate_eligible"):
            continue
        # Additional gate: must not be both evidence_strength=weak AND semantics=weak/unknown
        ev_strength = mat.get("evidence_strength") or "none"
        semantics = mat.get("risk_semantics_strength") or "unknown"
        if ev_strength in ("weak", "none") and semantics in ("weak", "unknown"):
            continue
        result.append({
            "candidate_feature_name": c.get("candidate_feature_name"),
            "risk_choke_point_type": ctype,
            "choke_point_likeness": mat["choke_point_likeness_after_gate"],
            "choke_point_reason": c.get("choke_point_reason"),
            "core_claim": mat["core_claim"],
            "risk_semantics_strength": mat.get("risk_semantics_strength"),
            "candidate_support_summary": mat.get("candidate_support_summary"),
            "supporting_evidence": mat["supporting_evidence"],
            "counter_evidence": mat["counter_evidence"],
            "claim_materialized": mat["claim_materialized"],
            "claim_materialization_reason": mat["claim_materialization_reason"],
            "allowed_claim_boundary": mat["allowed_claim_boundary"],
            "overclaim_risk": mat["overclaim_risk"],
            "evidence_status": mat["evidence_status"],
            "evidence_strength": mat["evidence_strength"],
            "source_status_summary": mat["source_status_summary"],
            "current_status": mat["current_status"],
            "top_candidate_eligible": mat.get("top_candidate_eligible"),
            "field_dictionary_review_eligible": mat.get("field_dictionary_review_eligible"),
            "core_commonality": c.get("core_commonality"),
            "source_support": c.get("source_support") or c.get("source_names") or [],
            "supporting_source_domains": c.get("supporting_source_domains") or [],
            "missing_evidence": mat["missing_evidence"],
            "validation_method": c.get("validation_method"),
            "candidate_only_not_final_conclusion": True,
        })

    empty_reason: str | None = None
    if not result:
        # Determine why: any eligible types in input at all?
        any_explainable = any(
            str(c.get("risk_choke_point_type") or "unknown") in _EXPLAINABLE_TYPES
            for c in candidate_features
        )
        if not any_explainable:
            empty_reason = "no_explainable_type_candidate_in_input"
        else:
            empty_reason = "no_candidate_passed_evidence_strength_and_semantics_gate"

    return {"candidates": result, "empty_reason": empty_reason}



def _why_not_top(mat: dict) -> str:
    """G-R6-fix: human-readable reason why candidate didn't make Top."""
    if not mat.get("claim_materialized"):
        return "claim_not_materialized: all fields are missing/template tokens"
    ev = mat.get("evidence_strength") or "none"
    sem = mat.get("risk_semantics_strength") or "unknown"
    if not mat.get("top_candidate_eligible"):
        if sem in ("unknown",):
            return "risk_semantics_strength=unknown: field semantics not confirmed, needs field dictionary"
        if sem in ("weak",):
            return "risk_semantics_strength=weak: status/context/default fields, weak risk explanation"
        if ev in ("weak", "none"):
            return f"evidence_strength={ev}: source_status unknown or source not entered main chain"
        return "top_candidate_eligible=False: combined gate not passed"
    if ev in ("weak", "none") and sem in ("weak", "unknown"):
        return f"evidence_strength={ev} AND risk_semantics_strength={sem}: both gates failed"
    return "gated_out"


def _next_action(mat: dict, candidate: dict) -> str:
    """G-R6-fix: next action for non-Top candidates."""
    sem = mat.get("risk_semantics_strength") or "unknown"
    if sem == "unknown":
        name = candidate.get("candidate_feature_name") or ""
        if "device" in name.lower() or "weapon" in name.lower():
            return "补 Weapon/device 字段字典，确认字段含义和正常背景率"
        return "补字段语义字典，确认字段含义和正常背景率"
    if sem == "weak":
        role = ""
        for ev in (mat.get("supporting_evidence") or []):
            role = ev.get("field_role") or role
        if role == "status_field":
            return "作为 context_commonality 保留，不进入风险 Top；确认是否有背景率异常"
        return "补字段语义字典，确认 deny/caller/code 等字段的真实含义和正常背景率"
    return "补 raw_field_path、risk label detail、正常背景率后重新评估"


def _build_high_coverage_commonality_candidates(
    candidate_features: list[dict[str, Any]],
    source_input_quality_table: list[dict[str, Any]] | None = None,
    min_support_ratio: float = 0.5,
    min_support_user_count: int = 3,
) -> list[dict[str, Any]]:
    """G-R6-fix: 高覆盖但暂不能进主 Top 的共性展示区.
    条件: support_ratio >= 0.5 OR support_user_count >= 3, 且 top_candidate_eligible=False.
    """
    result: list[dict[str, Any]] = []
    for c in candidate_features:
        mat = _materialize_candidate_evidence(c, source_input_quality_table or [])
        css = mat.get("candidate_support_summary") or {}
        sup_ratio = css.get("support_ratio") or 0.0
        sup_users = css.get("support_user_count") or 0
        # Must NOT be top_candidate_eligible (those go to Top section)
        if mat.get("top_candidate_eligible"):
            continue
        # Coverage gate
        if sup_ratio < min_support_ratio and sup_users < min_support_user_count:
            continue
        sem = mat.get("risk_semantics_strength") or "unknown"
        ev = mat.get("evidence_strength") or "none"
        result.append({
            "candidate_feature_name": c.get("candidate_feature_name"),
            "commonality_display_label": (
                c.get("candidate_feature_name") or
                str(c.get("risk_choke_point_type") or "unknown")
            ),
            "source_support": c.get("source_support") or c.get("source_names") or [],
            "supporting_source_domains": c.get("supporting_source_domains") or [],
            "core_commonality": c.get("core_commonality"),
            "support_user_count": css.get("support_user_count"),
            "support_sample_count": css.get("support_sample_count"),
            "support_ratio": css.get("support_ratio"),
            "support_record_count": css.get("support_record_count"),
            "risk_choke_point_type": c.get("risk_choke_point_type"),
            "risk_semantics_strength": sem,
            "evidence_strength": ev,
            "dictionary_status": next(
                (ev_item.get("dictionary_status") for ev_item in (mat.get("supporting_evidence") or [])
                 if ev_item.get("dictionary_status")),
                "unknown"
            ),
            "field_role": next(
                (ev_item.get("field_role") for ev_item in (mat.get("supporting_evidence") or [])
                 if ev_item.get("field_role")),
                "unknown"
            ),
            "top_candidate_eligible": False,
            "why_not_top": _why_not_top(mat),
            "next_action": _next_action(mat, c),
            "claim_materialized": mat.get("claim_materialized"),
            "candidate_support_summary": css,
            "candidate_only_not_final_conclusion": True,
        })
    # Sort: support_ratio desc, support_user_count desc, semantics (strong > medium > weak > unknown)
    _sem_order = {"strong": 0, "medium": 1, "weak": 2, "unknown": 3}
    result.sort(key=lambda x: (
        -float(x.get("support_ratio") or 0.0),
        -int(x.get("support_user_count") or 0),
        _sem_order.get(x.get("risk_semantics_strength") or "unknown", 3),
    ))
    return result


def _build_semantics_review_queue(
    candidate_features: list[dict[str, Any]],
    source_input_quality_table: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """G-R6-fix: 语义未确认字段进入 semantics_review_queue.
    包括: action=deny / callerCatalog / callerKsn / 登录链路语义不清字段.
    """
    _SEMANTICS_REVIEW_TOKENS = {
        "action=deny", "action = deny", "caller", "callerCatalog", "callerKsn",
        "code=0", "code = 0", "callerappid", "callersource",
    }
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for c in candidate_features:
        mat = _materialize_candidate_evidence(c, source_input_quality_table or [])
        for ev in (mat.get("supporting_evidence") or []):
            raw_fps = ev.get("raw_field_path") or []
            val_summary = str(ev.get("value_summary") or "")
            # Check if any field/value matches semantics review tokens
            combined_text = " ".join(raw_fps) + " " + val_summary
            combined_lower = combined_text.lower()
            for tok in _SEMANTICS_REVIEW_TOKENS:
                if tok.lower() in combined_lower:
                    key = f"{c.get('candidate_feature_name')}:{tok}"
                    if key not in seen:
                        seen.add(key)
                        css = mat.get("candidate_support_summary") or {}
                        result.append({
                            "candidate_feature_name": c.get("candidate_feature_name"),
                            "field_path": raw_fps,
                            "matched_token": tok,
                            "value_summary": val_summary,
                            "source_support": ev.get("source_name"),
                            "support_ratio": css.get("support_ratio"),
                            "support_user_count": css.get("support_user_count"),
                            "semantics_question": (
                                f"字段 '{tok}' 语义未确认: "
                                "是正常登录服务链路字段还是异常信号? 正常背景率未知"
                            ),
                            "next_action": (
                                "补登录/服务链路字段语义字典，确认正常用户背景率，"
                                "确认 deny/caller/code 的真实含义"
                            ),
                            "candidate_only_not_final_conclusion": True,
                        })
    return result


def _build_weak_materialized_review_queue(
    candidate_features: list[dict[str, Any]],
    source_input_quality_table: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """G-R6-fix: claim_materialized=True 但 top_candidate_eligible=False 的弱候选.
    这类候选有字段级证据，但语义强度或 source_status 不够进主 Top.
    """
    result: list[dict[str, Any]] = []
    for c in candidate_features:
        mat = _materialize_candidate_evidence(c, source_input_quality_table or [])
        if not mat.get("claim_materialized"):
            continue
        if mat.get("top_candidate_eligible"):
            continue  # 这些进 Top，不在此队列
        css = mat.get("candidate_support_summary") or {}
        result.append({
            "candidate_feature_name": c.get("candidate_feature_name"),
            "risk_choke_point_type": c.get("risk_choke_point_type"),
            "candidate_support_summary": css,
            "supporting_evidence": mat.get("supporting_evidence"),
            "evidence_strength": mat.get("evidence_strength"),
            "risk_semantics_strength": mat.get("risk_semantics_strength"),
            "allowed_claim_boundary": mat.get("allowed_claim_boundary"),
            "why_not_top": _why_not_top(mat),
            "next_action": _next_action(mat, c),
            "candidate_only_not_final_conclusion": True,
        })
    return result


def _build_l3_candidate_discovery_summary(
    top_candidates: list[dict],
    high_coverage_candidates: list[dict],
    field_dictionary_review: list[dict],
    context_commonality: list[dict],
    semantics_review: list[dict],
    weak_materialized: list[dict],
) -> dict[str, Any]:
    """G-R6-fix: 报告层 summary，避免误以为没有共性发现."""
    top_count = len(top_candidates)
    hcc_count = len(high_coverage_candidates)
    fdr_count = len(field_dictionary_review)
    ctx_count = len(context_commonality)
    sem_count = len(semantics_review)
    weak_count = len(weak_materialized)

    has_top = top_count > 0
    has_hcc = hcc_count > 0

    if has_top:
        discovery_boundary = (
            "产出高置信风险核心候选特征；候选均通过 evidence_strength 与 "
            "risk_semantics_strength 门禁；结论仍需进一步数据验证，"
            "candidate_only_not_final_conclusion=true"
        )
    elif has_hcc:
        discovery_boundary = (
            "本批发现多类高覆盖共性，但没有候选同时通过 evidence_strength 与 "
            "risk_semantics_strength 门禁进入主 Top；"
            "当前不能说没有发现，只能说未产出高置信风险核心特征。"
            "高覆盖共性已列入 high_coverage_commonality_candidates，"
            "需补字段字典和语义确认后再评估。"
        )
    else:
        discovery_boundary = (
            "本批无高覆盖共性，无高置信风险核心候选特征；"
            "候选字段均为模板短语或 unknown 语义，"
            "candidate_only_not_final_conclusion=true"
        )

    return {
        "top_explainable_count": top_count,
        "high_coverage_commonality_count": hcc_count,
        "field_dictionary_review_count": fdr_count,
        "context_commonality_count": ctx_count,
        "semantics_review_count": sem_count,
        "weak_materialized_review_count": weak_count,
        "has_top_explainable_risk_candidate": has_top,
        "has_high_coverage_commonality": has_hcc,
        "discovery_boundary": discovery_boundary,
        "candidate_only_not_final_conclusion": True,
    }


def _build_unknown_device_review_queue(candidate_features: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """G-R5: unknown device field 候选进入 review_queue，不刷屏主 Top"""
    _REVIEW_QUEUE_NAMES = {
        "device_unknown_field_enrichment_candidate",
        "unknown_field_enrichment_candidate",
        "rcp_unknown_feature_bundle_candidate",
        "account_unknown_field_enrichment_candidate",
    }
    queue: list[dict[str, Any]] = []
    for c in candidate_features:
        fn = str(c.get("candidate_feature_name") or "")
        if fn not in _REVIEW_QUEUE_NAMES:
            continue
        if len(queue) >= 10:
            break
        src_fields = [str(f) for f in (c.get("source_fields") or []) if f]
        field_combo = [str(f) for f in (c.get("field_combination") or []) if f]
        queue.append({
            "candidate_feature_name": fn,
            "source_support": c.get("source_support") or c.get("source_names") or [],
            "supporting_source_domains": c.get("supporting_source_domains") or [],
            "core_commonality": c.get("core_commonality") or [],
            "unknown_field_paths_sample": (field_combo or src_fields)[:5],
            "support_user_count": c.get("support_user_count") or c.get("support_sample_count") or 0,
            "support_record_count": c.get("support_record_count") or 0,
            "missing_evidence": c.get("missing_evidence") or [],
            "suggested_field_dictionary_action": "needs_field_dictionary_review: 请在 Weapon 字段字典中补录该字段的语义、正常值域和风险阈值，完成后重新评估候选 choke_type。",
            "candidate_only_not_final_conclusion": True,
        })
    return queue


def _unmaterialized_candidate_review_queue(
    candidate_features: list[dict[str, Any]],
    source_input_quality_table: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """G-R5b: 收集无字段级证据的候选，进入 review_queue。
    包含：只有模板短语、只有 source 共现、有反证但缺解释、blocked/timeout source。
    """
    _REVIEW_QUEUE_NAMES = {
        "device_unknown_field_enrichment_candidate",
        "unknown_field_enrichment_candidate",
        "rcp_unknown_feature_bundle_candidate",
        "account_unknown_field_enrichment_candidate",
    }
    queue: list[dict[str, Any]] = []
    for c in candidate_features:
        fn = str(c.get("candidate_feature_name") or "")
        mat = _materialize_candidate_evidence(c, source_input_quality_table or [])
        # 进 queue 的条件：unknown device field 或 unmaterialized
        if fn in _REVIEW_QUEUE_NAMES or not mat["claim_materialized"]:
            if len(queue) >= 10:
                continue
            queue.append({
                "candidate_feature_name": fn,
                "risk_choke_point_type": c.get("risk_choke_point_type"),
                "choke_point_likeness": mat["choke_point_likeness_after_gate"],
                "core_claim": mat["core_claim"],
                "claim_materialized": mat["claim_materialized"],
                "claim_materialization_reason": mat["claim_materialization_reason"],
                "overclaim_risk": mat["overclaim_risk"],
                "allowed_claim_boundary": mat["allowed_claim_boundary"],
                "evidence_status": mat["evidence_status"],
                "evidence_strength": mat["evidence_strength"],
                "counter_evidence": mat["counter_evidence"],
                "missing_evidence": mat["missing_evidence"],
                "source_status_summary": mat["source_status_summary"],
                "suggested_action": "需补充字段级证据或反证核查后才能进入 Top",
                "candidate_only_not_final_conclusion": True,
            })
    return queue

def _build_field_dictionary_review_queue(
    candidate_features: list[dict],
    source_input_quality_table: list[dict] | None = None,
) -> list[dict]:
    """G-R6: 6/6 unknown/status/default fields that need semantic dictionary review."""
    queue = []
    for c in candidate_features:
        mat = _materialize_candidate_evidence(c, source_input_quality_table or [])
        if not mat.get("field_dictionary_review_eligible"):
            continue
        if len(queue) >= 10:
            break
        queue.append({
            "candidate_feature_name": c.get("candidate_feature_name"),
            "risk_choke_point_type": c.get("risk_choke_point_type"),
            "internal_signal_name": c.get("candidate_feature_name") or c.get("risk_choke_point_type"),
            "raw_field_path": (c.get("field_combination") or [])[:5],
            "support_ratio": mat["candidate_support_summary"].get("support_ratio"),
            "support_user_count": mat["candidate_support_summary"].get("support_user_count"),
            "dictionary_status": "needs_field_dictionary_review",
            "why_not_top_candidate": (
                "risk_semantics_strength=unknown/weak or claim_not_materialized or status_field"
            ),
            "suggested_dictionary_action": (
                "请在 Weapon 字段字典中补录该字段的语义、正常值域和风险阈值，完成后重新评估。"
            ),
            "candidate_only_not_final_conclusion": True,
        })
    return queue


def _build_context_commonality_section(
    candidate_features: list[dict],
    source_input_quality_table: list[dict] | None = None,
) -> list[dict]:
    """G-R6: account_status/code/color/id/caller context fields go here, not risk Top."""
    _STATUS_CONTEXT_NAMES = {
        "account_maintenance_template_candidate",
        "login_control_chain_candidate",
        "account_status_commonality_candidate",
        "default_enum_commonality_candidate",
    }
    _STATUS_CONTEXT_CHOKES = {"unknown"}
    _STATUS_CONTEXT_CORE_TOKENS = {
        "account_status", "code=0", "code=200", "color=", "callerCatalog",
        "callerKsn", "webservice", "http_status", "caller_service",
    }
    section = []
    for c in candidate_features:
        fn = str(c.get("candidate_feature_name") or "")
        choke = str(c.get("risk_choke_point_type") or "unknown")
        core = " ".join(str(x) for x in (c.get("core_commonality") or [])).lower()
        is_context = (
            fn in _STATUS_CONTEXT_NAMES or
            any(tok in core for tok in _STATUS_CONTEXT_CORE_TOKENS)
        )
        if not is_context:
            continue
        if len(section) >= 8:
            break
        mat = _materialize_candidate_evidence(c, source_input_quality_table or [])
        section.append({
            "candidate_feature_name": fn,
            "risk_choke_point_type": choke,
            "field_role": "status_field_or_context",
            "risk_semantics_strength": mat.get("risk_semantics_strength", "weak"),
            "support_ratio": mat["candidate_support_summary"].get("support_ratio"),
            "core_commonality": c.get("core_commonality"),
            "interpretation": "普通状态/上下文字段，不进入风险 Top。需进行字段语义审查后才能提升。",
            "why_not_top": "status_or_context_field; support_ratio high ≠ risk_semantics high",
            "needs_semantics_review": True,
            "candidate_only_not_final_conclusion": True,
        })
    return section


def _g_r6_dedup_candidates(
    candidate_features: list[dict],
) -> list[dict]:
    """G-R6: deduplicate candidate list for report layer.
    Keep highest support_ratio / risk_semantics / claim_materialized per dedup key.
    """
    _SEMA_RANK = {"strong": 0, "medium": 1, "weak": 2, "unknown": 3}
    seen: dict[tuple, dict] = {}
    for c in candidate_features:
        name = str(c.get("candidate_feature_name") or "")
        choke = str(c.get("risk_choke_point_type") or "unknown")
        # normalize core
        core_raw = c.get("core_commonality") or []
        core_key = tuple(sorted(str(x) for x in (core_raw if isinstance(core_raw, list) else [core_raw])))
        src_key = tuple(sorted(str(s) for s in (c.get("source_support") or c.get("source_names") or [])))
        key = (name, choke, core_key[:2], src_key[:2])
        if key not in seen:
            seen[key] = c
        else:
            # Keep better one
            existing = seen[key]
            new_ratio = float(c.get("support_ratio") or 0)
            old_ratio = float(existing.get("support_ratio") or 0)
            new_sema = _SEMA_RANK.get(str(c.get("risk_semantics_strength") or "unknown"), 3)
            old_sema = _SEMA_RANK.get(str(existing.get("risk_semantics_strength") or "unknown"), 3)
            if new_sema < old_sema or (new_sema == old_sema and new_ratio > old_ratio):
                seen[key] = c
    return list(seen.values())


def _build_final_evidence_card_bridge(
    top_candidates: list[dict],
    unmaterialized_queue: list[dict],
    existing_card: dict,
    high_coverage_candidates: list[dict] | None = None,
    discovery_summary: dict | None = None,
) -> dict:
    """G-R6-fix: bridge candidate evidence into final_evidence_card with proper layering.
    - Top candidates with strong/medium evidence -> medium_evidence
    - High coverage but weak/unknown semantics -> weak_evidence ONLY (never medium)
    - Counter evidence bridged from all Top candidates
    - discovery_summary reflected in final_answer_boundary
    """
    medium_evidence = list(existing_card.get("medium_evidence") or [])
    weak_evidence = list(existing_card.get("weak_evidence") or [])
    counter_evidence_all: list[dict] = []
    missing_evidence_all: list[str] = list(existing_card.get("missing_evidence") or [])
    allowed_boundaries: list[str] = []

    # Layer 1: Top candidates (eligible, strong/medium evidence -> medium_evidence)
    for top in top_candidates:
        ev_label = top.get("candidate_feature_name") or top.get("risk_choke_point_type") or "unknown"
        mat = top.get("claim_materialized", False)
        ev_strength = top.get("evidence_strength") or "none"
        for ev in (top.get("supporting_evidence") or []):
            label = ev.get("evidence_display_label") or ev.get("internal_signal_name") or ev_label
            if mat and ev_strength in ("strong", "medium"):
                if label not in medium_evidence:
                    medium_evidence.append(label)
            else:
                if label not in weak_evidence:
                    weak_evidence.append(label)
        for ce in (top.get("counter_evidence") or []):
            counter_evidence_all.append({
                "candidate": ev_label,
                "counter_signal_type": ce.get("counter_signal_type"),
                "value_summary": ce.get("value_summary"),
                "reason": ce.get("reason_it_weakens_claim"),
            })
        for me in (top.get("missing_evidence") or []):
            if me and me not in missing_evidence_all:
                missing_evidence_all.append(me)
        bnd = top.get("allowed_claim_boundary")
        if bnd and bnd not in allowed_boundaries:
            allowed_boundaries.append(bnd)

    # Layer 2: High coverage candidates (unknown/weak semantics -> weak_evidence ONLY)
    for hcc in (high_coverage_candidates or []):
        ev_label = hcc.get("candidate_feature_name") or "high_coverage_commonality"
        # These NEVER go to medium_evidence regardless of support_ratio
        if ev_label not in weak_evidence:
            weak_evidence.append(ev_label)

    # Unmaterialized: propagate missing_evidence
    for q in unmaterialized_queue:
        for me in (q.get("missing_evidence") or []):
            if me and me not in missing_evidence_all:
                missing_evidence_all.append(me)

    # Build final_answer_boundary
    has_top = len(top_candidates) > 0
    has_hcc = len(high_coverage_candidates or []) > 0
    if has_top and allowed_boundaries:
        final_answer_boundary = "; ".join(allowed_boundaries[:3])
    elif not has_top and has_hcc:
        final_answer_boundary = (
            "发现高覆盖共性，但未形成可主张的高置信风险核心特征；"
            "高覆盖共性已列入 high_coverage_commonality_candidates；"
            "candidate_only_not_final_conclusion=true"
        )
    else:
        final_answer_boundary = "candidate_only_not_final_conclusion=true"

    # Build candidate_evidence_summary
    ces: list[dict] = []
    for t in top_candidates:
        ces.append({
            "candidate": t.get("candidate_feature_name"),
            "section": "top_explainable",
            "claim_materialized": t.get("claim_materialized"),
            "evidence_strength": t.get("evidence_strength"),
            "risk_semantics_strength": t.get("risk_semantics_strength"),
            "core_claim": t.get("core_claim"),
            "support_ratio": (t.get("candidate_support_summary") or {}).get("support_ratio"),
        })
    for hcc in (high_coverage_candidates or []):
        ces.append({
            "candidate": hcc.get("candidate_feature_name"),
            "section": "high_coverage_commonality",
            "claim_materialized": hcc.get("claim_materialized"),
            "evidence_strength": hcc.get("evidence_strength"),
            "risk_semantics_strength": hcc.get("risk_semantics_strength"),
            "support_ratio": hcc.get("support_ratio"),
            "why_not_top": hcc.get("why_not_top"),
        })

    card = dict(existing_card)
    card.update({
        "medium_evidence": medium_evidence,
        "weak_evidence": weak_evidence,
        "counter_evidence": counter_evidence_all,
        "missing_evidence": missing_evidence_all,
        "candidate_evidence_summary": ces,
        "candidate_evidence_summary_counts": {
            "top_explainable_count": len(top_candidates),
            "high_coverage_commonality_count": len(high_coverage_candidates or []),
            "review_queue_count": len(unmaterialized_queue),
        },
        "unmaterialized_candidate_review_summary": [
            {"candidate": q.get("candidate_feature_name"), "reason": q.get("claim_materialization_reason")}
            for q in unmaterialized_queue[:5]
        ],
        "allowed_claim_boundaries": allowed_boundaries,
        "final_answer_boundary": final_answer_boundary,
        "evidence_card_source": "candidate_evidence_bridge",
        "group_not_confirmed": True,
    })
    if discovery_summary:
        card["discovery_summary"] = discovery_summary
    return card



def build_commonality_artifacts(
    *,
    sampled_entities: list[str],
    source_commonality_cards: list[dict[str, Any]],
    candidate_anchor_pool: list[dict[str, Any]],
    batch_anchor_pool: list[dict[str, Any]],
    selected_drilldown_anchors: list[dict[str, Any]],
    strategy_event_request_detail_table: list[dict[str, Any]],
    strategy_event_feature_row_table: list[dict[str, Any]],
    device_detail_table: list[dict[str, Any]],
    standard_detail_table: list[dict[str, Any]],
    raw_detail_flat_table: list[dict[str, Any]],
    sequence_comparison_features: list[dict[str, Any]],
    source_quality: dict[str, Any],
    source_input_quality_table: list[dict[str, Any]],
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
        "social_action_anchor": ["social_domain", "behavior_domain"],
        "strategy_hit": ["strategy_domain"],
        "strategy_hit_detail": ["strategy_domain"],
        "strategy_event_request_detail": ["strategy_domain", "behavior_domain"],
        "track_frontend_behavior": ["behavior_domain", "device_domain"],
        "feedback_signal": ["feedback_domain"],
        "enforcement_review": ["enforcement_domain", "behavior_domain"],
    }
    shared_signal_items: list[dict[str, Any]] = []
    card_domains: list[str] = []
    strategy_detail_shared_signals, strategy_detail_candidate_features = build_strategy_request_detail_features(
        strategy_event_request_detail_table
    )
    strategy_feature_row_shared_signals, strategy_feature_row_candidate_features = build_strategy_feature_row_commonality_and_features(
        strategy_event_feature_row_table
    )
    (
        device_field_shared_signals,
        device_similarity_candidates,
        behavior_device_consistency_candidates,
        device_candidate_features,
        device_field_platform_summary,
    ) = (
        build_device_commonality_and_features(device_detail_table, sampled_entities)
    )
    standard_detail_shared_signals, standard_detail_candidate_features = build_standard_field_commonality_and_features(
        standard_detail_table=standard_detail_table,
        sampled_entities=sampled_entities,
    )
    sequence_candidate_features = build_sequence_candidate_features(
        sequence_comparison_features=sequence_comparison_features,
        sampled_entities=sampled_entities,
    )
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
    for signal in strategy_detail_shared_signals:
        signal = dict(signal)
        signal["limited_commonality"] = limited_commonality
        shared_signal_items.append(signal)
    for signal in strategy_feature_row_shared_signals:
        signal = dict(signal)
        signal["limited_commonality"] = limited_commonality
        shared_signal_items.append(signal)
    for signal in device_field_shared_signals:
        signal = dict(signal)
        signal["limited_commonality"] = limited_commonality
        shared_signal_items.append(signal)
    for signal in standard_detail_shared_signals:
        signal = dict(signal)
        signal["limited_commonality"] = limited_commonality
        shared_signal_items.append(signal)
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
    ] + card_domains + [
        str(row.get("mapped_domain"))
        for row in strategy_event_feature_row_table
        if row.get("mapped_domain") and str(row.get("mapped_domain")) != "未知"
    ] + [
        "device_domain"
        for row in device_detail_table
        if row.get("device_field_key")
    ] + [
        str(row.get("source_domain"))
        for row in standard_detail_table
        if row.get("source_domain")
    ])
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
    generic_candidate_features = [
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
    if {"behavior_domain", "device_domain"} <= set(domains):
        generic_candidate_features.append(
            {
                "feature_name": "control_execution_separation_candidate",
                "feature_type": "field_combination_commonality",
                "feature_origin": "field_combination",
                "source_domains": ["behavior_domain", "device_domain"],
                "source_names": ["login_logs_search", "weapon_device_info"],
                "source_fields": ["login_device", "action_device", "frontend_activity_signal", "backend_action_signal"],
                "field_combination": ["login_or_behavior_side != execution_side", "backend_action_signal + weak_frontend_activity"],
                "support_user_count": max(len(sampled_entities), 2),
                "support_entity_count": max(len(sampled_entities), 2),
                "support_sample_count": max(len(sampled_entities), 2),
                "support_record_count": len(sequence_comparison_features) or 2,
                "support_ratio": min(1.0, round(max(len(sampled_entities), 2) / max(len(sampled_entities), 1), 4)),
                "priority_score": 92,
                "priority_level": "high",
                "reason_codes": ["multi_domain_control_execution_gap"],
                "black_gray_interpretation": "登录/行为端与执行端字段组合不一致，更像控制面与执行面分离的候选卡口。",
                "false_positive_risk": "同一用户多设备、弱前台采集或字段不完整也可能造成不一致，需要补充更多上下文。",
                "missing_evidence": ["frontend_backend_alignment_validation", "normal_control_path_counter_sample"],
                "validation_method": "回放登录、设备、行为三域字段组合，确认是否稳定出现控制端与执行端脱节。",
                "not_final_conclusion": True,
            }
        )
    if {"behavior_domain", "strategy_domain"} <= set(domains):
        generic_candidate_features.append(
            {
                "feature_name": "protocol_constraint_gap_candidate",
                "feature_type": "field_combination_commonality",
                "feature_origin": "field_combination",
                "source_domains": ["behavior_domain", "strategy_domain"],
                "source_names": ["login_logs_search", "rcp_event_feature_list"],
                "source_fields": ["backend_action_signal", "frontend_activity_signal", "request_path", "request_scene"],
                "field_combination": ["backend_action_signal present", "missing_or_weak_frontend_activity", "strategy request detail template"],
                "support_user_count": max(len(sampled_entities), 2),
                "support_entity_count": max(len(sampled_entities), 2),
                "support_sample_count": max(len(sampled_entities), 2),
                "support_record_count": len(strategy_event_feature_row_table) or 2,
                "support_ratio": min(1.0, round(max(len(sampled_entities), 2) / max(len(sampled_entities), 1), 4)),
                "priority_score": 90,
                "priority_level": "high",
                "reason_codes": ["protocol_constraint_gap_candidate"],
                "black_gray_interpretation": "后端动作和策略请求细节存在，但前台约束或客户端路径支撑偏弱，像协议约束缺口候选。",
                "false_positive_risk": "部分正常后台任务、弱前台埋点或采样缺失也会表现为前后端不完全对齐。",
                "missing_evidence": ["client_path_validation", "frontend_activity_counter_sample"],
                "validation_method": "补查请求路径、前台活跃和设备执行一致性，确认是否属于真实客户端约束缺失。",
                "not_final_conclusion": True,
            }
        )
    if {"content_domain", "social_domain"} & set(domains) and {"content_domain", "social_domain"} <= set(domains):
        generic_candidate_features.append(
            {
                "feature_name": "content_funnel_dependency_candidate",
                "feature_type": "field_combination_commonality",
                "feature_origin": "field_combination",
                "source_domains": ["content_domain", "social_domain"],
                "source_names": ["archives_photo_search", "archives_comment_search", "archives_private_message_search"],
                "source_fields": ["caption", "content_type", "comment_target", "message_target", "path"],
                "field_combination": ["content template", "comment or message target overlap", "same funnel path"],
                "support_user_count": max(len(sampled_entities), 2),
                "support_entity_count": max(len(sampled_entities), 2),
                "support_sample_count": max(len(sampled_entities), 2),
                "support_record_count": len(sequence_comparison_features) or 2,
                "support_ratio": min(1.0, round(max(len(sampled_entities), 2) / max(len(sampled_entities), 1), 4)),
                "priority_score": 88,
                "priority_level": "high",
                "reason_codes": ["content_social_funnel_dependency"],
                "black_gray_interpretation": "内容模板、评论/私信对象和承接路径共同出现，更像导流或私域承接依赖的候选卡口。",
                "false_positive_risk": "热点内容和正常社交互动也可能形成相似路径，需要对象和后续承接补证。",
                "missing_evidence": ["target_object_overlap_validation", "off_platform_or_private_domain_followup"],
                "validation_method": "回放内容、评论、私信对象和时间窗，确认是否存在稳定承接路径。",
                "not_final_conclusion": True,
            }
        )
    candidate_features = (
        strategy_detail_candidate_features
        + strategy_feature_row_candidate_features
        + device_candidate_features
        + standard_detail_candidate_features
        + sequence_candidate_features
        + generic_candidate_features
    )
    candidate_features = [normalize_l3_candidate_feature_contract(feature) for feature in candidate_features]
    attack_chain_cooccurrence = build_attack_chain_cooccurrence(
        candidate_features=candidate_features,
        source_input_quality_table=source_input_quality_table,
    )
    candidate_features = attach_attack_chain_links_to_candidates(
        candidate_features=candidate_features,
        attack_chain_cooccurrence=attack_chain_cooccurrence,
    )
    commonality_type_distribution = build_l3_commonality_type_distribution(
        shared_signal_items=shared_signal_items,
        sequence_comparison_features=sequence_comparison_features,
        candidate_features=candidate_features,
    )
    field_value_commonality_funnel = build_field_value_commonality_funnel(
        strategy_event_feature_row_table=strategy_event_feature_row_table,
        device_detail_table=device_detail_table,
        standard_detail_table=standard_detail_table,
        shared_signal_items=shared_signal_items,
        candidate_features=candidate_features,
    )
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
    # G-R6-fix: pre-compute all output sections
    _top_exp_result = _build_top_explainable_candidates(
        candidate_features, source_input_quality_table=source_input_quality_table
    )
    _top_exp = _top_exp_result["candidates"]
    _top_exp_empty_reason = _top_exp_result["empty_reason"]
    _unmat_queue = _unmaterialized_candidate_review_queue(
        candidate_features, source_input_quality_table=source_input_quality_table
    )
    _high_cov = _build_high_coverage_commonality_candidates(
        candidate_features, source_input_quality_table=source_input_quality_table
    )
    _sem_review = _build_semantics_review_queue(
        candidate_features, source_input_quality_table=source_input_quality_table
    )
    _weak_mat = _build_weak_materialized_review_queue(
        candidate_features, source_input_quality_table=source_input_quality_table
    )
    _fdr = _build_field_dictionary_review_queue(
        candidate_features, source_input_quality_table=source_input_quality_table
    )
    _ctx = _build_context_commonality_section(
        candidate_features, source_input_quality_table=source_input_quality_table
    )
    _deduped = _g_r6_dedup_candidates(candidate_features)
    _discovery_summary = _build_l3_candidate_discovery_summary(
        _top_exp, _high_cov, _fdr, _ctx, _sem_review, _weak_mat
    )
    _bridged_card = _build_final_evidence_card_bridge(
        _top_exp, _unmat_queue, final_evidence_card,
        high_coverage_candidates=_high_cov,
        discovery_summary=_discovery_summary,
    )

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
        "strategy_event_request_detail_commonality": strategy_detail_shared_signals,
        "strategy_event_feature_row_commonality": strategy_feature_row_shared_signals,
        "device_field_commonality": device_field_shared_signals,
        "standard_field_commonality": standard_detail_shared_signals,
        "sequence_comparison_features": sequence_comparison_features,
        "commonality_type_distribution": commonality_type_distribution,
        "field_value_commonality_funnel": field_value_commonality_funnel,
        "attack_chain_cooccurrence": attack_chain_cooccurrence,
        "raw_detail_flat_table_summary": build_raw_detail_flat_table_summary(raw_detail_flat_table),
        "device_field_platform_summary": device_field_platform_summary,
        "device_environment_similarity_cluster_candidate": device_similarity_candidates,
        "behavior_device_consistency_gap_candidate": behavior_device_consistency_candidates,
        "group_profile_candidate": group_profile_candidate,
        "candidate_features": candidate_features,
        "l3_candidate_quality_summary": _build_l3_candidate_quality_summary(candidate_features),
        # TODO-G-R6-SOURCE-QUALITY-PROPAGATION: pass source_input_quality_table so
        # _materialize_candidate_evidence can resolve source_status/evidence_strength.
        # Currently source_input_quality_table is available in this scope; wiring it
        # into _build_top_explainable_candidates / _unmaterialized_candidate_review_queue
        # will fix source_status_summary=unknown and evidence_strength=weak (P1).
        "top_explainable_risk_choke_point_candidates": _top_exp,
        "top_explainable_empty_reason": _top_exp_empty_reason,
        "high_coverage_commonality_candidates": _high_cov,
        "unknown_device_field_review_queue": _build_unknown_device_review_queue(candidate_features),
        "unmaterialized_candidate_review_queue": _unmat_queue,
        "field_dictionary_review_queue": _fdr,
        "context_commonality_section": _ctx,
        "semantics_review_queue": _sem_review,
        "weak_materialized_candidate_review_queue": _weak_mat,
        "candidate_features_deduped": _deduped,
        "l3_candidate_discovery_summary": _discovery_summary,
        "validation_plan": validation_plan,
        "final_evidence_card": _bridged_card,
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
    strategy_event_request_detail_table = build_strategy_event_request_detail_table(
        round_id=round_id,
        sampled_entities=sampled_entities,
        source_observations=source_observations,
    )
    strategy_event_feature_row_table = build_strategy_event_feature_row_table(
        round_id=round_id,
        sampled_entities=sampled_entities,
        source_observations=source_observations,
    )
    standard_detail_table = build_standard_detail_table(
        round_id=round_id,
        sampled_entities=sampled_entities,
        source_observations=source_observations,
    )
    device_detail_table = build_device_detail_table(
        round_id=round_id,
        sampled_entities=sampled_entities,
        source_observations=source_observations,
        strategy_event_feature_row_table=strategy_event_feature_row_table,
    )
    raw_detail_flat_table = build_raw_detail_flat_table(
        round_id=round_id,
        sampled_entities=sampled_entities,
        source_observations=source_observations,
        strategy_event_feature_row_table=strategy_event_feature_row_table,
        device_detail_table=device_detail_table,
    )
    sequence_comparison_features = build_sequence_comparison_features(
        raw_detail_flat_table=raw_detail_flat_table,
        sampled_entities=sampled_entities,
    )
    raw_detail_flat_table_summary = build_raw_detail_flat_table_summary(raw_detail_flat_table)
    source_field_volume_summary = build_source_field_volume_summary(
        source_observations=source_observations,
        standard_detail_table=standard_detail_table,
        strategy_event_feature_row_table=strategy_event_feature_row_table,
        device_detail_table=device_detail_table,
    )
    source_input_quality_table = build_l3_source_input_quality_table(
        source_plan=source_plan,
        source_observations=source_observations,
        raw_detail_flat_table_summary=raw_detail_flat_table_summary,
        source_field_volume_summary=source_field_volume_summary,
    )
    commonality = build_commonality_artifacts(
        sampled_entities=sampled_entities,
        source_commonality_cards=source_commonality_cards,
        candidate_anchor_pool=candidate_anchor_pool,
        batch_anchor_pool=anchor_selection["batch_anchor_pool"],
        selected_drilldown_anchors=anchor_selection["selected_drilldown_anchors"],
        strategy_event_request_detail_table=strategy_event_request_detail_table,
        strategy_event_feature_row_table=strategy_event_feature_row_table,
        device_detail_table=device_detail_table,
        standard_detail_table=standard_detail_table,
        raw_detail_flat_table=raw_detail_flat_table,
        sequence_comparison_features=sequence_comparison_features,
        source_quality=normalized_source_quality,
        source_input_quality_table=source_input_quality_table,
        mode=mode,
    )
    candidate_feature_top_samples = build_candidate_feature_top_samples(
        candidate_features=commonality["candidate_features"],
        source_input_quality_table=source_input_quality_table,
        attack_chain_cooccurrence=commonality["attack_chain_cooccurrence"],
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
        "strategy_event_request_detail_table": strategy_event_request_detail_table,
        "strategy_event_request_detail_commonality": commonality["strategy_event_request_detail_commonality"],
        "strategy_event_feature_row_table": strategy_event_feature_row_table,
        "strategy_event_feature_row_commonality": commonality["strategy_event_feature_row_commonality"],
        "raw_detail_flat_table": raw_detail_flat_table,
        "raw_detail_flat_table_summary": raw_detail_flat_table_summary,
        "sequence_comparison_features": sequence_comparison_features,
        "device_detail_table": device_detail_table,
        "device_detail_source_field_summary": build_device_detail_source_field_summary(device_detail_table),
        "source_field_volume_summary": source_field_volume_summary,
        "source_input_quality_table": source_input_quality_table,
        "device_field_commonality": commonality["device_field_commonality"],
        "device_field_platform_summary": commonality["device_field_platform_summary"],
        "device_environment_similarity_cluster_candidate": commonality["device_environment_similarity_cluster_candidate"],
        "behavior_device_consistency_gap_candidate": commonality["behavior_device_consistency_gap_candidate"],
        "standard_detail_table": standard_detail_table,
        "login_detail_table": _detail_rows_by_table(standard_detail_table, "login_detail_table"),
        "account_detail_table": _detail_rows_by_table(standard_detail_table, "account_detail_table"),
        "user_behavior_summary_detail_table": _detail_rows_by_table(standard_detail_table, "user_behavior_summary_detail_table"),
        "content_detail_table": _detail_rows_by_table(standard_detail_table, "content_detail_table"),
        "social_detail_table": _detail_rows_by_table(standard_detail_table, "social_detail_table"),
        "feedback_detail_table": _detail_rows_by_table(standard_detail_table, "feedback_detail_table"),
        "enforcement_detail_table": _detail_rows_by_table(standard_detail_table, "enforcement_detail_table"),
        "standard_field_commonality": commonality["standard_field_commonality"],
        "l3_commonality_type_distribution": commonality["commonality_type_distribution"],
        "field_value_commonality_funnel": commonality["field_value_commonality_funnel"],
        "attack_chain_cooccurrence": commonality["attack_chain_cooccurrence"],
        "group_profile_candidate": commonality["group_profile_candidate"],
        "candidate_features": commonality["candidate_features"],
        "candidate_feature_top_samples": candidate_feature_top_samples,
        "l3_candidate_quality_summary": commonality["l3_candidate_quality_summary"],
        "top_explainable_risk_choke_point_candidates": commonality["top_explainable_risk_choke_point_candidates"],
        "top_explainable_empty_reason": commonality.get("top_explainable_empty_reason"),
        "high_coverage_commonality_candidates": commonality.get("high_coverage_commonality_candidates", []),
        "unknown_device_field_review_queue": commonality["unknown_device_field_review_queue"],
        "unmaterialized_candidate_review_queue": commonality["unmaterialized_candidate_review_queue"],
        "field_dictionary_review_queue": commonality["field_dictionary_review_queue"],
        "context_commonality_section": commonality["context_commonality_section"],
        "semantics_review_queue": commonality.get("semantics_review_queue", []),
        "weak_materialized_candidate_review_queue": commonality.get("weak_materialized_candidate_review_queue", []),
        "candidate_features_deduped": commonality["candidate_features_deduped"],
        "l3_candidate_discovery_summary": commonality.get("l3_candidate_discovery_summary", {}),
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


def _quality_bucket_count(source_quality_matrix: dict[str, Any], *bucket_names: str) -> int:
    buckets = source_quality_matrix.get("buckets", {}) if isinstance(source_quality_matrix, dict) else {}
    return sum(len(buckets.get(name, []) or []) for name in bucket_names)


def _quality_status_from_counts(source_quality_matrix: dict[str, Any]) -> str:
    completed = _quality_bucket_count(source_quality_matrix, "completed")
    partial = _quality_bucket_count(source_quality_matrix, "partial")
    blocked_like = _quality_bucket_count(source_quality_matrix, "blocked", "auth_failed", "timeout", "parse_error")
    no_data = _quality_bucket_count(source_quality_matrix, "no_data")
    planned = _quality_bucket_count(source_quality_matrix, "planned")
    total = completed + partial + blocked_like + no_data + planned
    if total == 0:
        return "not_executed"
    if completed and not partial and not blocked_like:
        return "completed"
    if completed or partial:
        return "partial" if not blocked_like else "partial_with_blocked_sources"
    if no_data and not blocked_like:
        return "no_data"
    if planned and not blocked_like:
        return "planned"
    return "blocked"


def _quality_blocked_reasons(source_quality_matrix: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    for row in source_quality_matrix.get("per_source", []) or []:
        if not isinstance(row, dict):
            continue
        if row.get("quality_class") not in {"blocked", "auth_failed", "timeout", "parse_error"}:
            continue
        reason = str(row.get("reason") or row.get("error_type") or row.get("source_status") or row.get("quality_class") or "")
        action = str(row.get("action") or "")
        if action and reason:
            reasons.append(f"{action}:{reason}")
        elif reason:
            reasons.append(reason)
    return unique_strings(reasons)


def build_status_attribution(
    *,
    primary_source_plan: list[SourcePlanItem],
    primary_batch_result: dict[str, Any],
    followup_source_plan: list[SourcePlanItem],
    followup_batch_result: dict[str, Any],
) -> dict[str, Any]:
    primary_quality = merge_source_quality(primary_source_plan, primary_batch_result)
    followup_quality = merge_source_quality(followup_source_plan, followup_batch_result) if followup_source_plan else {
        "buckets": {"completed": [], "partial": [], "blocked": [], "auth_failed": [], "timeout": [], "parse_error": [], "no_data": [], "planned": []},
        "per_source": [],
    }
    primary_status = _quality_status_from_counts(primary_quality)
    followup_status = _quality_status_from_counts(followup_quality)
    primary_blocked_count = _quality_bucket_count(primary_quality, "blocked", "auth_failed", "timeout", "parse_error")
    followup_blocked_count = _quality_bucket_count(followup_quality, "blocked", "auth_failed", "timeout", "parse_error")
    primary_partial_count = _quality_bucket_count(primary_quality, "partial")
    primary_completed_count = _quality_bucket_count(primary_quality, "completed")
    primary_source_impact = primary_blocked_count > 0 and primary_completed_count == 0 and primary_partial_count == 0
    status_contamination = bool(followup_blocked_count and not primary_source_impact)
    if status_contamination:
        top_status = "partial_with_followup_blocked" if primary_partial_count else "completed_primary_with_followup_blocked"
    elif primary_source_impact:
        top_status = "primary_source_blocked"
    else:
        top_status = primary_status
    return {
        "primary_source_status": primary_status,
        "primary_source_completed_count": primary_completed_count,
        "primary_source_partial_count": primary_partial_count,
        "primary_source_blocked_count": primary_blocked_count,
        "followup_source_status": followup_status,
        "followup_blocked_count": followup_blocked_count,
        "followup_blocked_reasons": _quality_blocked_reasons(followup_quality),
        "top_level_final_status": top_status,
        "status_contamination": status_contamination,
        "primary_source_impact": primary_source_impact,
        "followup_source_quality": followup_quality,
        "status_boundary": (
            "source_level_and_round_level_status_take_priority_over_top_level_final_status; "
            "followup blocked sources do not make completed primary source extraction failed"
        ),
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


def _one_degree_associated_users_by_round_entity(
    round_id: int,
    sampled_entities: list[str],
    source_observations: list[dict[str, Any]],
) -> dict[int, list[dict[str, Any]]]:
    by_index: dict[int, list[dict[str, Any]]] = {index: [] for index in range(1, len(sampled_entities) + 1)}
    input_entities = set(sampled_entities)
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
        if str(observation.get("action") or "") not in WEAPON_DEVICE_DETAIL_ACTIONS | {"weapon_inventory"}:
            continue
        for handle in observation.get("parsed_body_field_handles", []) or []:
            canonical = str(handle.get("canonical_field") or handle.get("field") or "")
            if canonical not in {"user_id", "related_user_id"}:
                continue
            user_id = str(handle.get("value") or "").strip()
            if not user_id or user_id in input_entities or not user_id.isdigit():
                continue
            key = (entity_index, user_id)
            if key in seen:
                continue
            seen.add(key)
            by_index[entity_index].append(
                {
                    "user_id": user_id,
                    "source_id": source_id,
                    "action": observation.get("action"),
                    "field_path": handle.get("field_path"),
                    "association_depth": 1,
                    "association_type": "device_to_user",
                    "seed_entity_type": _infer_seed_entity_type(sampled_entities[entity_index - 1]),
                    "recursive_expansion_allowed": False,
                    "stop_reason": "one_degree_depth_reached",
                }
            )
            if len(by_index[entity_index]) >= MAX_ONE_DEGREE_USERS_PER_SEED:
                break
    return by_index


def build_one_degree_user_detail_source_plan(
    round_id: int,
    sampled_entities: list[str],
    source_observations: list[dict[str, Any]],
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
    by_entity = _one_degree_associated_users_by_round_entity(round_id, sampled_entities, source_observations)
    selected: list[tuple[int, dict[str, Any]]] = []
    for index, users in by_entity.items():
        for user in users[:MAX_ONE_DEGREE_USERS_PER_SEED]:
            selected.append((index, user))
            if len(selected) >= MAX_ONE_DEGREE_ASSOCIATED_USERS_TOTAL:
                break
        if len(selected) >= MAX_ONE_DEGREE_ASSOCIATED_USERS_TOTAL:
            break
    items: list[SourcePlanItem] = []
    for seed_index, user in selected:
        user_id = str(user.get("user_id") or "")
        if not user_id:
            continue
        prefix = _batch_source_id(round_id, seed_index, f"one_degree_user_{user_id}")
        common = {
            "association_depth": 1,
            "seed_entity": sampled_entities[seed_index - 1],
            "seed_entity_type": _infer_seed_entity_type(sampled_entities[seed_index - 1]),
            "associated_user_id": user_id,
            "recursive_expansion_allowed": False,
            "stop_reason": "one_degree_depth_reached",
        }
        source_specs = [
            (
                "profile",
                "archives_user_profile",
                {"user_id": user_id, "mode": "one_degree_associated_user_profile", **common},
                [],
                "auth_sensitive",
                "P1-one-degree-detail",
                "one-degree associated user profile/status; no recursive expansion",
                ["user_id"],
                30_000,
                window_start_ms,
                window_end_ms,
                "one_degree_associated_user_profile",
            ),
            (
                "analysis",
                "archives_user_analysis",
                {"user_id": user_id, "mode": "one_degree_associated_user_analysis", **common},
                [],
                "auth_sensitive",
                "P1-one-degree-detail",
                "one-degree associated user behavior summary; newly found anchors are context only",
                ["user_id"],
                30_000,
                window_start_ms,
                window_end_ms,
                "one_degree_associated_user_behavior",
            ),
            (
                "gallery",
                "archives_gallery_photo_list",
                {"user_id": user_id, "pageIndex": 1, "pageSize": 10, "mode": "one_degree_associated_user_recent_video_list", **common},
                [],
                "auth_sensitive",
                "P1-one-degree-detail",
                "one-degree associated user recent video list for publish-device positioning only",
                ["user_id"],
                30_000,
                window_start_ms,
                window_end_ms,
                "one_degree_associated_user_content_positioning_no_recursive_photo_expansion",
            ),
            (
                "login",
                "login_logs_search",
                {
                    "user_id": user_id,
                    "from_timestamp": login_start_ms,
                    "to_timestamp": login_end_ms,
                    "recallSource": DEFAULT_RECALL_SOURCE,
                    "max_records": 30,
                    "mode": "one_degree_associated_user_login_summary",
                    **common,
                },
                [],
                "standard_readonly",
                "P1-one-degree-detail",
                "one-degree associated user login summary for seed-device consistency only",
                ["user_id"],
                45_000,
                login_start_ms,
                login_end_ms,
                "one_degree_associated_user_login_window",
            ),
            (
                "strategy",
                "rcp_fast_query_hbase",
                {
                    "source_id": user_id,
                    "startTime": window_start_ms,
                    "endTime": window_end_ms,
                    "eventTypeCodes": "",
                    "limit": 50,
                    "mode": "one_degree_associated_user_strategy_summary",
                    **common,
                },
                [],
                "standard_readonly",
                "P1-one-degree-detail",
                "one-degree associated user strategy hit summary; strategy hit is not final judgement",
                ["source_id", "startTime", "endTime"],
                30_000,
                window_start_ms,
                window_end_ms,
                "one_degree_associated_user_strategy_window",
            ),
        ]
        for suffix, action, params, depends_on, timeout_class, priority, expected, required, timeout_ms, start_ms, end_ms, window_policy in source_specs:
            if action in disabled_actions:
                continue
            items.append(
                SourcePlanItem(
                    source_id=f"{prefix}_{suffix}",
                    action=action,
                    execution_group="one_degree_associated_user_detail",
                    depends_on=depends_on,
                    timeout_class=timeout_class,
                    failure_policy="non_blocking_partial",
                    source_priority=priority,
                    expected_observation=expected,
                    params=params,
                    timeout_ms=timeout_ms,
                    required_fields=required,
                    window_policy=window_policy,
                    window_start_ms=start_ms,
                    window_end_ms=end_ms,
                )
            )
    return items


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


def _event_anchors_by_round_entity(
    round_id: int,
    sampled_entities: list[str],
    source_observations: list[dict[str, Any]],
) -> dict[int, list[dict[str, Any]]]:
    by_index: dict[int, list[dict[str, Any]]] = {index: [] for index in range(1, len(sampled_entities) + 1)}
    seen: set[tuple[int, str, str]] = set()
    for observation in source_observations:
        source_id = str(observation.get("source_id") or "")
        entity_index = None
        for index in by_index:
            if source_id.startswith(_round_entity_prefix(round_id, index)):
                entity_index = index
                break
        if entity_index is None:
            continue
        action = str(observation.get("action") or "")
        if action not in {"rcp_snapshot", "rcp_fast_query_hbase", "rcp_event_detail", "rcp_event_feature_list"}:
            continue
        handles = observation.get("parsed_body_field_handles", []) or []
        event_ids: list[str] = []
        event_types: list[str] = []
        event_times: list[Any] = []
        policy_codes: list[str] = []
        source_ids: list[str] = []
        for handle in handles:
            if not isinstance(handle, dict):
                continue
            raw_field = str(handle.get("field") or "")
            raw_normalized = re.sub(r"[^a-z0-9]", "", raw_field.lower())
            canonical = str(handle.get("canonical_field") or handle.get("field") or "")
            value = handle.get("value")
            value_text = str(value or "").strip()
            if not value_text:
                continue
            if canonical == "event_id":
                if raw_normalized in {"sourceid", "source"} or "sourceid" in raw_normalized:
                    source_ids.append(value_text)
                else:
                    event_ids.append(value_text)
            elif canonical == "event_type":
                event_types.append(value_text)
            elif canonical == "event_time":
                event_times.append(value)
            elif canonical == "policy_code":
                policy_codes.append(value_text)
        if not event_ids:
            continue
        default_event_type = event_types[0] if event_types else "REGISTER_NEW"
        default_query_time = event_times[0] if event_times else None
        default_policy_code = policy_codes[0] if policy_codes else None
        for event_id in event_ids[:5]:
            key = (entity_index, event_id, default_event_type)
            if key in seen:
                continue
            seen.add(key)
            by_index[entity_index].append(
                {
                    "event_id": event_id,
                    "source_id_value": source_ids[0] if source_ids else event_id,
                    "event_type": default_event_type,
                    "query_time": default_query_time,
                    "policy_code": default_policy_code,
                    "source_id": source_id,
                    "action": action,
                }
            )
    return by_index


def _coerce_event_query_time(value: Any, fallback_ms: int) -> int:
    if value is None or value == "":
        return fallback_ms
    if isinstance(value, (int, float)):
        text = str(int(value))
    else:
        text = str(value).strip()
    digits = "".join(ch for ch in text if ch.isdigit())
    if not digits:
        return fallback_ms
    number = int(digits[:13])
    if number < 10_000_000_000:
        number *= 1000
    return number


def build_rcp_event_followup_source_plan(
    round_id: int,
    sampled_entities: list[str],
    source_observations: list[dict[str, Any]],
    *,
    window_start_ms: int,
    window_end_ms: int,
    disabled_actions: set[str] | None = None,
) -> list[SourcePlanItem]:
    disabled_actions = disabled_actions or set()
    if {"rcp_event_detail", "rcp_event_feature_list"} <= disabled_actions:
        return []
    event_anchors_by_entity = _event_anchors_by_round_entity(round_id, sampled_entities, source_observations)
    items: list[SourcePlanItem] = []
    for index, candidates in event_anchors_by_entity.items():
        for candidate_index, candidate in enumerate(candidates[:2], start=1):
            event_id = str(candidate.get("event_id") or "").strip()
            event_type = str(candidate.get("event_type") or "REGISTER_NEW").strip() or "REGISTER_NEW"
            query_time = _coerce_event_query_time(candidate.get("query_time"), window_end_ms)
            depends_on = [str(candidate.get("source_id") or _batch_source_id(round_id, index, "strategy"))]
            base_params = {
                "eventType": event_type,
                "event_type": event_type,
                "eventId": event_id,
                "event_id": event_id,
                "source_id": str(candidate.get("source_id_value") or event_id),
                "queryTime": query_time,
                "query_time": query_time,
            }
            if candidate.get("policy_code"):
                base_params["policyCode"] = candidate.get("policy_code")
                base_params["policy_code"] = candidate.get("policy_code")
            if "rcp_event_detail" not in disabled_actions:
                items.append(
                    SourcePlanItem(
                        source_id=_batch_source_id(round_id, index, f"rcp_event_detail_{candidate_index}"),
                        action="rcp_event_detail",
                        execution_group="dependency_serial",
                        depends_on=depends_on,
                        timeout_class="standard_readonly",
                        failure_policy="non_blocking_partial",
                        source_priority="P1-auto-next-hop",
                        expected_observation="RCP event request detail fields; policy/event labels are entry context only",
                        params=dict(base_params),
                        timeout_ms=30_000,
                        required_fields=["eventId", "eventType", "queryTime"],
                        window_policy="rcp_event_detail_from_selected_strategy_anchor",
                        window_start_ms=window_start_ms,
                        window_end_ms=window_end_ms,
                    )
                )
            if "rcp_event_feature_list" not in disabled_actions:
                feature_params = {**base_params, "featureGroup": "", "feature_group": ""}
                items.append(
                    SourcePlanItem(
                        source_id=_batch_source_id(round_id, index, f"rcp_event_feature_list_{candidate_index}"),
                        action="rcp_event_feature_list",
                        execution_group="dependency_serial",
                        depends_on=depends_on,
                        timeout_class="large_response",
                        failure_policy="non_blocking_partial",
                        source_priority="P1-auto-next-hop",
                        expected_observation="RCP featureKey/defaultFeatureValue rows for strategy_event_feature_row_table",
                        params=feature_params,
                        timeout_ms=45_000,
                        required_fields=["eventId", "eventType", "queryTime"],
                        window_policy="rcp_event_feature_rows_from_selected_strategy_anchor",
                        window_start_ms=window_start_ms,
                        window_end_ms=window_end_ms,
                    )
                )
    return items


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
        if _infer_seed_entity_type(entity) != "user_id":
            continue
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


def build_content_social_followup_source_plan(
    round_id: int,
    sampled_entities: list[str],
    source_observations: list[dict[str, Any]],
    *,
    window_start_ms: int,
    window_end_ms: int,
    disabled_actions: set[str] | None = None,
) -> list[SourcePlanItem]:
    disabled_actions = disabled_actions or set()
    photo_ids_by_entity = _photo_ids_by_round_entity(round_id, sampled_entities, source_observations)
    items: list[SourcePlanItem] = []
    for index, entity in enumerate(sampled_entities, start=1):
        if _infer_seed_entity_type(entity) == "user_id" and "archives_private_message_search" not in disabled_actions:
            items.append(
                SourcePlanItem(
                    source_id=_batch_source_id(round_id, index, "private_message"),
                    action="archives_private_message_search",
                    execution_group="dependency_serial",
                    depends_on=[_batch_source_id(round_id, index, "archives_profile")],
                    timeout_class="auth_sensitive",
                    failure_policy="non_blocking_partial",
                    source_priority="P1-auto-next-hop",
                    expected_observation="bounded received private-message rows for social_detail_table; single-entity signal only",
                    params={
                        "user_id": entity,
                        "direction": "received",
                        "page": 1,
                        "count": 20,
                    },
                    timeout_ms=30_000,
                    required_fields=["user_id", "direction"],
                    window_policy="social_private_message_received_recent_window",
                    window_start_ms=window_start_ms,
                    window_end_ms=window_end_ms,
                )
            )
        photo_candidates = photo_ids_by_entity.get(index, [])
        if not photo_candidates or "archives_comment_search" in disabled_actions:
            continue
        photo_candidate = photo_candidates[0]
        photo_id = str(photo_candidate.get("photo_id") or "").strip()
        if not photo_id:
            continue
        items.append(
            SourcePlanItem(
                source_id=_batch_source_id(round_id, index, f"comment_{photo_id}"),
                action="archives_comment_search",
                execution_group="dependency_serial",
                depends_on=[str(photo_candidate.get("source_id") or _batch_source_id(round_id, index, "photo"))],
                timeout_class="auth_sensitive",
                failure_policy="non_blocking_partial",
                source_priority="P1-auto-next-hop",
                expected_observation="bounded comment rows for content/social handoff; single-entity signal unless cross-entity support emerges later",
                params={
                    "photo_id": photo_id,
                    "page": 1,
                    "count": 20,
                    "containsPhotoInfo": True,
                },
                timeout_ms=30_000,
                required_fields=["photo_id"],
                window_policy="content_social_comment_followup_from_photo_anchor",
                window_start_ms=window_start_ms,
                window_end_ms=window_end_ms,
            )
        )
    return items


def build_feedback_enforcement_followup_source_plan(
    round_id: int,
    sampled_entities: list[str],
    source_observations: list[dict[str, Any]],
    *,
    window_start_ms: int,
    window_end_ms: int,
    disabled_actions: set[str] | None = None,
) -> list[SourcePlanItem]:
    disabled_actions = disabled_actions or set()
    photo_ids_by_entity = _photo_ids_by_round_entity(round_id, sampled_entities, source_observations)
    items: list[SourcePlanItem] = []
    for index, entity in enumerate(sampled_entities, start=1):
        if _infer_seed_entity_type(entity) != "user_id":
            continue
        depends_on = [_batch_source_id(round_id, index, "archives_profile")]
        if "archives_user_report_search" not in disabled_actions:
            items.append(
                SourcePlanItem(
                    source_id=_batch_source_id(round_id, index, "user_report"),
                    action="archives_user_report_search",
                    execution_group="dependency_serial",
                    depends_on=depends_on,
                    timeout_class="auth_sensitive",
                    failure_policy="non_blocking_partial",
                    source_priority="P1-auto-next-hop",
                    expected_observation="bounded report rows for feedback_detail_table; feedback is not risk fact",
                    params={
                        "user_id": entity,
                        "begin": window_start_ms,
                        "end": window_end_ms,
                        "page": 1,
                        "count": 20,
                    },
                    timeout_ms=30_000,
                    required_fields=["user_id"],
                    window_policy="feedback_report_recent_window",
                    window_start_ms=window_start_ms,
                    window_end_ms=window_end_ms,
                )
            )
        if "archives_negative_report" not in disabled_actions:
            items.append(
                SourcePlanItem(
                    source_id=_batch_source_id(round_id, index, "negative_report"),
                    action="archives_negative_report",
                    execution_group="dependency_serial",
                    depends_on=depends_on,
                    timeout_class="auth_sensitive",
                    failure_policy="non_blocking_partial",
                    source_priority="P1-auto-next-hop",
                    expected_observation="bounded negative-report summary/detail rows for feedback_detail_table; feedback is not risk fact",
                    params={"user_id": entity},
                    timeout_ms=30_000,
                    required_fields=["user_id"],
                    window_policy="negative_report_recent_window",
                    window_start_ms=window_start_ms,
                    window_end_ms=window_end_ms,
                )
            )
        if "archives_review_logs" not in disabled_actions:
            items.append(
                SourcePlanItem(
                    source_id=_batch_source_id(round_id, index, "review_logs"),
                    action="archives_review_logs",
                    execution_group="dependency_serial",
                    depends_on=depends_on,
                    timeout_class="auth_sensitive",
                    failure_policy="non_blocking_partial",
                    source_priority="P1-auto-next-hop",
                    expected_observation="bounded review log rows for enforcement_detail_table; enforcement is governance state not risk fact",
                    params={
                        "user_id": entity,
                        "beginTime": window_start_ms,
                        "endTime": window_end_ms,
                        "pageIndex": 1,
                        "pageSize": 30,
                    },
                    timeout_ms=30_000,
                    required_fields=["user_id", "beginTime", "endTime"],
                    window_policy="review_logs_recent_window",
                    window_start_ms=window_start_ms,
                    window_end_ms=window_end_ms,
                )
            )
        if "archives_punish_status" in disabled_actions:
            continue
        photo_candidates = photo_ids_by_entity.get(index, [])
        if not photo_candidates:
            continue
        photo_candidate = photo_candidates[0]
        photo_id = str(photo_candidate.get("photo_id") or "").strip()
        if not photo_id:
            continue
        items.append(
            SourcePlanItem(
                source_id=_batch_source_id(round_id, index, f"punish_{photo_id}"),
                action="archives_punish_status",
                execution_group="dependency_serial",
                depends_on=[str(photo_candidate.get("source_id") or _batch_source_id(round_id, index, "photo"))],
                timeout_class="auth_sensitive",
                failure_policy="non_blocking_partial",
                source_priority="P1-auto-next-hop",
                expected_observation="bounded punish status rows for enforcement_detail_table; governance state only, not black-gray essence",
                params={"photo_id": photo_id},
                timeout_ms=30_000,
                required_fields=["photo_id"],
                window_policy="punish_status_followup_from_photo_anchor",
                window_start_ms=window_start_ms,
                window_end_ms=window_end_ms,
            )
        )
    return items


def build_single_case_content_social_followup_items(
    user_id: str,
    source_observations: list[dict[str, Any]],
    *,
    window_start_ms: int,
    window_end_ms: int,
    disabled_actions: set[str] | None = None,
) -> list[SourcePlanItem]:
    disabled_actions = disabled_actions or set()
    photo_ids = _photo_ids_from_observations(source_observations)
    items: list[SourcePlanItem] = []
    existing_actions = {str(observation.get("action") or "") for observation in source_observations}
    if "archives_private_message_search" not in disabled_actions and "archives_private_message_search" not in existing_actions:
        items.append(
            SourcePlanItem(
                source_id=f"ato_archives_private_message_search_{user_id}",
                action="archives_private_message_search",
                execution_group="dependency_serial",
                depends_on=["ato_archives_user_profile"],
                timeout_class="auth_sensitive",
                failure_policy="non_blocking_partial",
                source_priority="P1-auto-next-hop",
                expected_observation="bounded received private-message rows for social_detail_table; single-entity signal only",
                params={
                    "user_id": user_id,
                    "direction": "received",
                    "page": 1,
                    "count": 20,
                },
                timeout_ms=30_000,
                required_fields=["user_id", "direction"],
                window_policy="social_private_message_received_recent_window",
                window_start_ms=window_start_ms,
                window_end_ms=window_end_ms,
            )
        )
    existing_comment_photo_ids = {
        str(handle.get("value"))
        for observation in source_observations
        if str(observation.get("action") or "") == "archives_comment_search"
        for handle in observation.get("parsed_body_field_handles", [])
        if str(handle.get("canonical_field") or handle.get("field")) == "photo_id"
    }
    if "archives_comment_search" in disabled_actions:
        return items
    for photo_id in photo_ids:
        if photo_id in existing_comment_photo_ids:
            continue
        items.append(
            SourcePlanItem(
                source_id=f"ato_archives_comment_search_{photo_id}",
                action="archives_comment_search",
                execution_group="dependency_serial",
                depends_on=["ato_archives_photo_search"],
                timeout_class="auth_sensitive",
                failure_policy="non_blocking_partial",
                source_priority="P1-auto-next-hop",
                expected_observation="bounded comment rows for content/social handoff; single-entity signal unless cross-entity support emerges later",
                params={
                    "photo_id": photo_id,
                    "page": 1,
                    "count": 20,
                    "containsPhotoInfo": True,
                },
                timeout_ms=30_000,
                required_fields=["photo_id"],
                window_policy="content_social_comment_followup_from_photo_anchor",
                window_start_ms=window_start_ms,
                window_end_ms=window_end_ms,
            )
        )
    return items


def build_single_case_feedback_enforcement_followup_items(
    user_id: str,
    source_observations: list[dict[str, Any]],
    *,
    window_start_ms: int,
    window_end_ms: int,
    disabled_actions: set[str] | None = None,
) -> list[SourcePlanItem]:
    disabled_actions = disabled_actions or set()
    photo_ids = _photo_ids_from_observations(source_observations)
    items: list[SourcePlanItem] = []
    existing_actions = {str(observation.get("action") or "") for observation in source_observations}
    if "archives_user_report_search" not in disabled_actions and "archives_user_report_search" not in existing_actions:
        items.append(
            SourcePlanItem(
                source_id=f"ato_archives_user_report_search_{user_id}",
                action="archives_user_report_search",
                execution_group="dependency_serial",
                depends_on=["ato_archives_user_profile"],
                timeout_class="auth_sensitive",
                failure_policy="non_blocking_partial",
                source_priority="P1-auto-next-hop",
                expected_observation="bounded report rows for feedback_detail_table; feedback is not risk fact",
                params={
                    "user_id": user_id,
                    "begin": window_start_ms,
                    "end": window_end_ms,
                    "page": 1,
                    "count": 20,
                },
                timeout_ms=30_000,
                required_fields=["user_id"],
                window_policy="feedback_report_recent_window",
                window_start_ms=window_start_ms,
                window_end_ms=window_end_ms,
            )
        )
    if "archives_negative_report" not in disabled_actions and "archives_negative_report" not in existing_actions:
        items.append(
            SourcePlanItem(
                source_id=f"ato_archives_negative_report_{user_id}",
                action="archives_negative_report",
                execution_group="dependency_serial",
                depends_on=["ato_archives_user_profile"],
                timeout_class="auth_sensitive",
                failure_policy="non_blocking_partial",
                source_priority="P1-auto-next-hop",
                expected_observation="bounded negative-report summary/detail rows for feedback_detail_table; feedback is not risk fact",
                params={"user_id": user_id},
                timeout_ms=30_000,
                required_fields=["user_id"],
                window_policy="negative_report_recent_window",
                window_start_ms=window_start_ms,
                window_end_ms=window_end_ms,
            )
        )
    if "archives_review_logs" not in disabled_actions and "archives_review_logs" not in existing_actions:
        items.append(
            SourcePlanItem(
                source_id=f"ato_archives_review_logs_{user_id}",
                action="archives_review_logs",
                execution_group="dependency_serial",
                depends_on=["ato_archives_user_profile"],
                timeout_class="auth_sensitive",
                failure_policy="non_blocking_partial",
                source_priority="P1-auto-next-hop",
                expected_observation="bounded review log rows for enforcement_detail_table; enforcement is governance state not risk fact",
                params={
                    "user_id": user_id,
                    "beginTime": window_start_ms,
                    "endTime": window_end_ms,
                    "pageIndex": 1,
                    "pageSize": 30,
                },
                timeout_ms=30_000,
                required_fields=["user_id", "beginTime", "endTime"],
                window_policy="review_logs_recent_window",
                window_start_ms=window_start_ms,
                window_end_ms=window_end_ms,
            )
        )
    if "archives_punish_status" in disabled_actions:
        return items
    existing_punish_photo_ids = {
        str(handle.get("value"))
        for observation in source_observations
        if str(observation.get("action") or "") == "archives_punish_status"
        for handle in observation.get("parsed_body_field_handles", [])
        if str(handle.get("canonical_field") or handle.get("field")) == "photo_id"
    }
    for photo_id in photo_ids:
        if photo_id in existing_punish_photo_ids:
            continue
        items.append(
            SourcePlanItem(
                source_id=f"ato_archives_punish_status_{photo_id}",
                action="archives_punish_status",
                execution_group="dependency_serial",
                depends_on=["ato_archives_photo_search"],
                timeout_class="auth_sensitive",
                failure_policy="non_blocking_partial",
                source_priority="P1-auto-next-hop",
                expected_observation="bounded punish status rows for enforcement_detail_table; governance state only, not black-gray essence",
                params={"photo_id": photo_id},
                timeout_ms=30_000,
                required_fields=["photo_id"],
                window_policy="punish_status_followup_from_photo_anchor",
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
    round_started = time.monotonic()
    round_id = int(round_item.get("round_id"))
    sampled_entities = [str(entity) for entity in round_item.get("sampled_entities", [])]
    checkpoint_dir = _checkpoint_dir_for_args(args, case_id)
    checkpoint_enabled = args.mode == "live" or bool(getattr(args, "checkpoint_dir", None))
    checkpoint_files: list[str] = []
    progress_trace: list[dict[str, Any]] = []
    timing_trace: dict[str, Any] = {
        "global": {
            "plan_build_ms": 0,
            "chunk_build_ms": 0,
            "batch_submit_ms": 0,
            "batch_wait_ms": 0,
            "service_return_ms": 0,
            "artifact_build_ms": 0,
            "checkpoint_write_ms": 0,
            "total_elapsed_ms": 0,
        },
        "chunks": [],
    }
    batch_index_counter = 0
    checkpoint_results_so_far: list[dict[str, Any]] = []
    checkpoint_source_plan_so_far: list[SourcePlanItem] = []
    plan_started = time.monotonic()
    source_plan = build_sample_round_source_plan(
        round_id,
        sampled_entities,
        window_start_ms=window_start_ms,
        window_end_ms=window_end_ms,
        disabled_actions=disabled_actions,
        source_overrides=round_item.get("source_overrides") if isinstance(round_item.get("source_overrides"), dict) else None,
    )
    timing_trace["global"]["plan_build_ms"] = _elapsed_ms(plan_started)
    chunked_payloads, executable, skipped = _chunked_batch_payloads_for_executable_sources(
        f"{case_id}:round_{round_id}",
        source_plan,
        dry_run=args.mode == "dry_run",
    )
    timing_trace["global"]["chunk_build_ms"] = _elapsed_ms(plan_started) - int(timing_trace["global"]["plan_build_ms"])
    payloads = [payload for payload, _items in chunked_payloads]
    batch_payload = _summarize_chunked_batch_payloads(payloads)
    contract_validation = _validate_chunked_batch_payloads(payloads)
    batch_started = time.monotonic()
    scheduler_state = _new_scheduler_state()

    def execute_chunk_group(
        *,
        stage_name: str,
        chunk_group: list[tuple[dict[str, Any], list[SourcePlanItem]]],
    ) -> list[dict[str, Any]]:
        nonlocal batch_index_counter
        results: list[dict[str, Any]] = []

        def append_short_circuit_chunk(
            *,
            chunk_offset: int,
            reason: str,
            reason_items: list[SourcePlanItem],
        ) -> None:
            nonlocal batch_index_counter
            if not reason_items:
                return
            batch_index_counter += 1
            short_circuit_type = "auth_failed_short_circuit" if reason == "auth_session_issue" else "timeout_circuit_breaker"
            gap_state = "auth_failed" if reason == "auth_session_issue" else "source_gap"
            circuit_open = reason == "circuit_open_timeout"
            chunk_id = f"round_{round_id}_{stage_name}_{chunk_offset}_short_circuit_{reason}"
            current_running_sources = [item.source_id for item in reason_items]
            source_actions = unique_strings([item.action for item in reason_items])
            current_source_group = "+".join(source_actions) if source_actions else "short_circuit_source_gap"
            checkpoint_source_plan_so_far.extend(reason_items)
            short_circuit_result = build_short_circuit_batch_result(
                reason_items,
                gap_state=gap_state,
                gap_reason=reason,
                short_circuit_type=short_circuit_type,
                circuit_open=circuit_open,
            )
            checkpoint_results_so_far.append(short_circuit_result)
            results.append(short_circuit_result)
            chunk_quality = merge_source_quality(reason_items, short_circuit_result)
            buckets = chunk_quality.get("buckets", {})
            timing_row = {
                "chunk_id": chunk_id,
                "round_index": round_id,
                "batch_index": batch_index_counter,
                "source_group": current_source_group,
                "actions": source_actions,
                "action_count": len(reason_items),
                "submit_started_at": _iso_now(),
                "submit_finished_at": _iso_now(),
                "service_wait_started_at": None,
                "service_returned_at": _iso_now(),
                "submit_ms": 0,
                "wait_ms": 0,
                "artifact_ms": 0,
                "checkpoint_ms": 0,
                "batch_elapsed_ms": 0,
                "per_source_elapsed_ms": None,
                "completed_count": len(buckets.get("completed", [])),
                "partial_count": len(buckets.get("partial", [])),
                "blocked_count": len(buckets.get("blocked", [])) + len(buckets.get("auth_failed", [])) + len(buckets.get("parse_error", [])),
                "timeout_count": len(buckets.get("timeout", [])),
                "auth_failed_count": len(buckets.get("auth_failed", [])),
                "source_gap_count": len(reason_items),
                "pending_count": 0,
                "short_circuit_count": len(reason_items),
                "circuit_open_count": 1 if circuit_open else 0,
                "affected_user_count": _source_plan_user_count(reason_items),
                "gap_reason_counts": {reason: len(reason_items)},
                "short_circuit_events": [
                    {
                        "source_action": action,
                        "gap_reason": reason,
                        "short_circuit_type": short_circuit_type,
                        "affected_user_count": _source_plan_user_count([item for item in reason_items if item.action == action]),
                    }
                    for action in source_actions
                ],
                "circuit_open_events": [
                    {
                        "source_action": action,
                        "gap_reason": reason,
                        "affected_user_count": _source_plan_user_count([item for item in reason_items if item.action == action]),
                    }
                    for action in source_actions
                ] if circuit_open else [],
            }
            timing_trace["chunks"].append(timing_row)
            timing_trace["global"]["total_elapsed_ms"] = _elapsed_ms(round_started)
            checkpoint_started = time.monotonic()
            if checkpoint_enabled:
                checkpoint_path, progress_row = _write_sample_batch_checkpoint(
                    checkpoint_dir=checkpoint_dir,
                    case_id=case_id,
                    round_index=round_id,
                    batch_index=batch_index_counter,
                    chunk_id=chunk_id,
                    current_source_group=current_source_group,
                    current_running_sources=current_running_sources,
                    current_source_plan=checkpoint_source_plan_so_far,
                    current_results=[*checkpoint_results_so_far, *([build_dry_run_batch_result(skipped)] if skipped else [])],
                    sampled_entities=sampled_entities,
                    mode=args.mode,
                    disabled_actions=disabled_actions,
                    waiting_reason=reason,
                    timing_trace=timing_trace,
                    checkpoint_phase="done",
                )
                timing_row["checkpoint_ms"] = _elapsed_ms(checkpoint_started)
                checkpoint_files.append(checkpoint_path)
                progress_trace.append(progress_row)
                if args.mode == "live":
                    _emit_sample_batch_progress(progress_row)
            else:
                progress_trace.append(
                    {
                        "current_chunk_id": chunk_id,
                        "current_round_index": round_id,
                        "current_batch_index": batch_index_counter,
                        "current_source_group": current_source_group,
                        "current_running_sources": current_running_sources,
                        "elapsed_seconds": round((timing_trace.get("global", {}).get("total_elapsed_ms") or 0) / 1000, 2),
                        "last_checkpoint_file": None,
                        "completed_source_count": timing_row["completed_count"],
                        "partial_source_count": timing_row["partial_count"],
                        "blocked_source_count": timing_row["blocked_count"],
                        "pending_source_count": 0,
                    }
                )

        for chunk_offset, (payload, chunk_items) in enumerate(chunk_group, start=1):
            active_chunk_items, _circuit_skipped_items, circuit_items_by_reason = _split_by_scheduler_circuit(
                scheduler_state,
                chunk_items,
            )
            for reason, reason_items in sorted(circuit_items_by_reason.items()):
                append_short_circuit_chunk(chunk_offset=chunk_offset, reason=reason, reason_items=reason_items)
            if not active_chunk_items:
                continue
            if len(active_chunk_items) != len(chunk_items):
                payload = build_batch_payload(
                    str(payload.get("request_id") or f"{case_id}:round_{round_id}:{stage_name}:{chunk_offset}"),
                    active_chunk_items,
                    dry_run=args.mode == "dry_run",
                )
                chunk_items = active_chunk_items
            batch_index_counter += 1
            chunk_id = f"round_{round_id}_{stage_name}_{chunk_offset}"
            current_running_sources = [item.source_id for item in chunk_items]
            current_source_group = _chunk_source_group_from_payload(payload)
            checkpoint_source_plan_so_far.extend(chunk_items)
            timing_row = {
                "chunk_id": chunk_id,
                "round_index": round_id,
                "batch_index": batch_index_counter,
                "source_group": current_source_group,
                "actions": _chunk_actions_from_payload(payload),
                "action_count": len(chunk_items),
                "submit_started_at": _iso_now(),
                "submit_finished_at": None,
                "service_wait_started_at": None,
                "service_returned_at": None,
                "submit_ms": 0,
                "wait_ms": None,
                "artifact_ms": 0,
                "checkpoint_ms": 0,
                "batch_elapsed_ms": None,
                "per_source_elapsed_ms": None,
                "completed_count": 0,
                "partial_count": 0,
                "blocked_count": 0,
                "timeout_count": 0,
                "auth_failed_count": 0,
                "source_gap_count": 0,
                "pending_count": len(chunk_items),
                "short_circuit_count": 0,
                "circuit_open_count": 0,
                "affected_user_count": _source_plan_user_count(chunk_items),
                "gap_reason_counts": {},
                "short_circuit_events": [],
                "circuit_open_events": [],
            }
            timing_trace["chunks"].append(timing_row)
            timing_trace["global"]["total_elapsed_ms"] = _elapsed_ms(round_started)
            if checkpoint_enabled:
                checkpoint_path, progress_row = _write_sample_batch_checkpoint(
                    checkpoint_dir=checkpoint_dir,
                    case_id=case_id,
                    round_index=round_id,
                    batch_index=batch_index_counter,
                    chunk_id=chunk_id,
                    current_source_group=current_source_group,
                    current_running_sources=current_running_sources,
                    current_source_plan=checkpoint_source_plan_so_far,
                    current_results=[*checkpoint_results_so_far, *([build_dry_run_batch_result(skipped)] if skipped else [])],
                    sampled_entities=sampled_entities,
                    mode=args.mode,
                    disabled_actions=disabled_actions,
                    waiting_reason="waiting_on_batch_return",
                    timing_trace=timing_trace,
                    checkpoint_phase="start",
                )
                checkpoint_files.append(checkpoint_path)
                progress_trace.append(progress_row)
                if args.mode == "live":
                    _emit_sample_batch_progress(progress_row)
            call_started = time.monotonic()
            if args.mode == "dry_run":
                chunk_result = build_dry_run_batch_result(chunk_items)
            elif args.browser_backed_base:
                timing_row["service_wait_started_at"] = _iso_now()
                chunk_result = call_browser_backed_batch(args.browser_backed_base, payload)
            else:
                chunk_result = build_harness_error_result(
                    source_status="service_unavailable",
                    error_type="browser_backed_base_required",
                    detail={"reason": "--browser-backed-base is required in live mode"},
                )
            call_elapsed = _elapsed_ms(call_started)
            timing_row["submit_finished_at"] = timing_row["submit_started_at"]
            timing_row["service_wait_started_at"] = timing_row["service_wait_started_at"] or timing_row["submit_started_at"]
            timing_row["service_returned_at"] = _iso_now()
            timing_row["wait_ms"] = call_elapsed
            timing_row["batch_elapsed_ms"] = call_elapsed
            timing_row["pending_count"] = 0
            timing_trace["global"]["batch_wait_ms"] = int(timing_trace["global"]["batch_wait_ms"]) + call_elapsed
            timing_trace["global"]["service_return_ms"] = int(timing_trace["global"]["service_return_ms"]) + call_elapsed
            checkpoint_results_so_far.append(chunk_result)
            results.append(chunk_result)
            chunk_quality = merge_source_quality(chunk_items, chunk_result)
            buckets = chunk_quality.get("buckets", {})
            timing_row["completed_count"] = len(buckets.get("completed", []))
            timing_row["partial_count"] = len(buckets.get("partial", []))
            timing_row["blocked_count"] = len(buckets.get("blocked", [])) + len(buckets.get("auth_failed", [])) + len(buckets.get("parse_error", []))
            timing_row["timeout_count"] = len(buckets.get("timeout", []))
            timing_row["auth_failed_count"] = len(buckets.get("auth_failed", []))
            timing_row["source_gap_count"] = (
                timing_row["timeout_count"]
                + len(buckets.get("blocked", []))
                + len(buckets.get("auth_failed", []))
                + len(buckets.get("parse_error", []))
                + len(buckets.get("partial", []))
            )
            timing_row["gap_reason_counts"] = _gap_reason_counts_from_quality(chunk_quality)
            opened_events = _update_scheduler_state_from_chunk(scheduler_state, chunk_quality=chunk_quality)
            timing_row["circuit_open_count"] = len(opened_events)
            timing_row["circuit_open_events"] = opened_events
            timing_trace["global"]["total_elapsed_ms"] = _elapsed_ms(round_started)
            checkpoint_started = time.monotonic()
            if checkpoint_enabled:
                checkpoint_path, progress_row = _write_sample_batch_checkpoint(
                    checkpoint_dir=checkpoint_dir,
                    case_id=case_id,
                    round_index=round_id,
                    batch_index=batch_index_counter,
                    chunk_id=chunk_id,
                    current_source_group=current_source_group,
                    current_running_sources=current_running_sources,
                    current_source_plan=checkpoint_source_plan_so_far,
                    current_results=[*checkpoint_results_so_far, *([build_dry_run_batch_result(skipped)] if skipped else [])],
                    sampled_entities=sampled_entities,
                    mode=args.mode,
                    disabled_actions=disabled_actions,
                    waiting_reason=str(chunk_result.get("batch_status") or "chunk_completed"),
                    timing_trace=timing_trace,
                    checkpoint_phase="done",
                )
                timing_row["checkpoint_ms"] = _elapsed_ms(checkpoint_started)
                checkpoint_files.append(checkpoint_path)
                progress_trace.append(progress_row)
                if args.mode == "live":
                    _emit_sample_batch_progress(progress_row)
            else:
                progress_trace.append(
                    {
                        "current_chunk_id": chunk_id,
                        "current_round_index": round_id,
                        "current_batch_index": batch_index_counter,
                        "current_source_group": current_source_group,
                        "current_running_sources": current_running_sources,
                        "elapsed_seconds": round((timing_trace.get("global", {}).get("total_elapsed_ms") or 0) / 1000, 2),
                        "last_checkpoint_file": None,
                        "completed_source_count": timing_row["completed_count"],
                        "partial_source_count": timing_row["partial_count"],
                        "blocked_source_count": timing_row["blocked_count"],
                        "pending_source_count": timing_row["pending_count"],
                    }
                )
        return results

    if args.mode == "dry_run":
        primary_results = execute_chunk_group(stage_name="primary", chunk_group=chunked_payloads)
    else:
        if not args.browser_backed_base:
            primary_results = [build_harness_error_result(
                source_status="service_unavailable",
                error_type="browser_backed_base_required",
                detail={"reason": "--browser-backed-base is required in live mode"},
            )]
        else:
            primary_results = execute_chunk_group(stage_name="primary", chunk_group=chunked_payloads)
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
        gallery_results = execute_chunk_group(stage_name="gallery_followup", chunk_group=gallery_chunks)

    after_gallery_plan = [*source_plan, *gallery_source_plan]
    after_gallery_result = merge_batch_results([*primary_results, *gallery_results, skipped_result])
    after_gallery_quality = merge_source_quality(after_gallery_plan, after_gallery_result)
    after_gallery_observations = build_source_observations(after_gallery_plan, after_gallery_quality, after_gallery_result)

    rcp_event_source_plan: list[SourcePlanItem] = []
    rcp_event_results: list[dict[str, Any]] = []
    rcp_event_payloads: list[dict[str, Any]] = []
    if next_hop_allowed:
        rcp_event_source_plan = build_rcp_event_followup_source_plan(
            round_id,
            sampled_entities,
            after_gallery_observations,
            window_start_ms=window_start_ms,
            window_end_ms=window_end_ms,
            disabled_actions=disabled_actions,
        )
    if rcp_event_source_plan:
        rcp_event_chunks, _rcp_event_executable, _rcp_event_skipped = _chunked_batch_payloads_for_executable_sources(
            f"{case_id}:round_{round_id}:rcp_event_followup",
            rcp_event_source_plan,
            dry_run=args.mode == "dry_run",
        )
        rcp_event_payloads = [payload for payload, _items in rcp_event_chunks]
        rcp_event_results = execute_chunk_group(stage_name="rcp_event_followup", chunk_group=rcp_event_chunks)

    after_rcp_plan = [*source_plan, *gallery_source_plan, *rcp_event_source_plan]
    after_rcp_result = merge_batch_results([*primary_results, *gallery_results, *rcp_event_results, skipped_result])
    after_rcp_quality = merge_source_quality(after_rcp_plan, after_rcp_result)
    after_rcp_observations = build_source_observations(after_rcp_plan, after_rcp_quality, after_rcp_result)

    photo_detail_source_plan: list[SourcePlanItem] = []
    photo_detail_results: list[dict[str, Any]] = []
    photo_detail_payloads: list[dict[str, Any]] = []
    if next_hop_allowed:
        photo_detail_source_plan = build_photo_detail_followup_source_plan(
            round_id,
            sampled_entities,
            after_rcp_observations,
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
        photo_detail_results = execute_chunk_group(stage_name="photo_detail_followup", chunk_group=photo_detail_chunks)

    before_social_plan = [*source_plan, *gallery_source_plan, *rcp_event_source_plan, *photo_detail_source_plan]
    before_social_result = merge_batch_results([*primary_results, *gallery_results, *rcp_event_results, *photo_detail_results, skipped_result])
    before_social_quality = merge_source_quality(before_social_plan, before_social_result)
    before_social_observations = build_source_observations(before_social_plan, before_social_quality, before_social_result)

    content_social_source_plan: list[SourcePlanItem] = []
    content_social_results: list[dict[str, Any]] = []
    content_social_payloads: list[dict[str, Any]] = []
    if next_hop_allowed:
        content_social_source_plan = build_content_social_followup_source_plan(
            round_id,
            sampled_entities,
            before_social_observations,
            window_start_ms=window_start_ms,
            window_end_ms=window_end_ms,
            disabled_actions=disabled_actions,
        )
    if content_social_source_plan:
        content_social_chunks, _content_social_executable, _content_social_skipped = _chunked_batch_payloads_for_executable_sources(
            f"{case_id}:round_{round_id}:content_social_followup",
            content_social_source_plan,
            dry_run=args.mode == "dry_run",
        )
        content_social_payloads = [payload for payload, _items in content_social_chunks]
        content_social_results = execute_chunk_group(stage_name="content_social_followup", chunk_group=content_social_chunks)

    before_feedback_plan = [*source_plan, *gallery_source_plan, *rcp_event_source_plan, *photo_detail_source_plan, *content_social_source_plan]
    before_feedback_result = merge_batch_results([*primary_results, *gallery_results, *rcp_event_results, *photo_detail_results, *content_social_results, skipped_result])
    before_feedback_quality = merge_source_quality(before_feedback_plan, before_feedback_result)
    before_feedback_observations = build_source_observations(before_feedback_plan, before_feedback_quality, before_feedback_result)

    feedback_enforcement_source_plan: list[SourcePlanItem] = []
    feedback_enforcement_results: list[dict[str, Any]] = []
    feedback_enforcement_payloads: list[dict[str, Any]] = []
    if next_hop_allowed:
        feedback_enforcement_source_plan = build_feedback_enforcement_followup_source_plan(
            round_id,
            sampled_entities,
            before_feedback_observations,
            window_start_ms=window_start_ms,
            window_end_ms=window_end_ms,
            disabled_actions=disabled_actions,
        )
    if feedback_enforcement_source_plan:
        feedback_enforcement_chunks, _feedback_executable, _feedback_skipped = _chunked_batch_payloads_for_executable_sources(
            f"{case_id}:round_{round_id}:feedback_enforcement_followup",
            feedback_enforcement_source_plan,
            dry_run=args.mode == "dry_run",
        )
        feedback_enforcement_payloads = [payload for payload, _items in feedback_enforcement_chunks]
        feedback_enforcement_results = execute_chunk_group(stage_name="feedback_enforcement_followup", chunk_group=feedback_enforcement_chunks)

    before_track_plan = [
        *source_plan,
        *gallery_source_plan,
        *rcp_event_source_plan,
        *photo_detail_source_plan,
        *content_social_source_plan,
        *feedback_enforcement_source_plan,
    ]
    before_track_result = merge_batch_results([
        *primary_results,
        *gallery_results,
        *rcp_event_results,
        *photo_detail_results,
        *content_social_results,
        *feedback_enforcement_results,
        skipped_result,
    ])
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
        followup_results = execute_chunk_group(stage_name="track_followup", chunk_group=followup_chunks)

    before_one_degree_plan = [*source_plan, *gallery_source_plan, *rcp_event_source_plan, *photo_detail_source_plan, *content_social_source_plan, *feedback_enforcement_source_plan, *followup_source_plan]
    before_one_degree_result = merge_batch_results([*primary_results, *gallery_results, *rcp_event_results, *photo_detail_results, *content_social_results, *feedback_enforcement_results, *followup_results, skipped_result])
    before_one_degree_quality = merge_source_quality(before_one_degree_plan, before_one_degree_result)
    before_one_degree_observations = build_source_observations(before_one_degree_plan, before_one_degree_quality, before_one_degree_result)

    one_degree_user_source_plan: list[SourcePlanItem] = []
    one_degree_user_results: list[dict[str, Any]] = []
    one_degree_user_payloads: list[dict[str, Any]] = []
    if next_hop_allowed:
        one_degree_user_source_plan = build_one_degree_user_detail_source_plan(
            round_id,
            sampled_entities,
            before_one_degree_observations,
            window_start_ms=window_start_ms,
            window_end_ms=window_end_ms,
            disabled_actions=disabled_actions,
        )
    if one_degree_user_source_plan:
        one_degree_chunks, _one_degree_executable, _one_degree_skipped = _chunked_batch_payloads_for_executable_sources(
            f"{case_id}:round_{round_id}:one_degree_user_detail",
            one_degree_user_source_plan,
            dry_run=args.mode == "dry_run",
        )
        one_degree_user_payloads = [payload for payload, _items in one_degree_chunks]
        one_degree_user_results = execute_chunk_group(stage_name="one_degree_user_detail", chunk_group=one_degree_chunks)

    combined_source_plan = [
        *source_plan,
        *gallery_source_plan,
        *rcp_event_source_plan,
        *photo_detail_source_plan,
        *content_social_source_plan,
        *feedback_enforcement_source_plan,
        *followup_source_plan,
        *one_degree_user_source_plan,
    ]
    batch_result_raw = merge_batch_results([
        *primary_results,
        *gallery_results,
        *rcp_event_results,
        *photo_detail_results,
        *content_social_results,
        *feedback_enforcement_results,
        *followup_results,
        *one_degree_user_results,
        skipped_result,
    ])
    followup_source_plan_all = [
        *gallery_source_plan,
        *rcp_event_source_plan,
        *photo_detail_source_plan,
        *content_social_source_plan,
        *feedback_enforcement_source_plan,
        *followup_source_plan,
        *one_degree_user_source_plan,
    ]
    status_attribution = build_status_attribution(
        primary_source_plan=source_plan,
        primary_batch_result=merge_batch_results([*primary_results, skipped_result]),
        followup_source_plan=followup_source_plan_all,
        followup_batch_result=merge_batch_results([
            *gallery_results,
            *rcp_event_results,
            *photo_detail_results,
            *followup_results,
            *one_degree_user_results,
        ]),
    )
    batch_result_for_round = dict(batch_result_raw)
    if status_attribution.get("status_contamination") and not status_attribution.get("primary_source_impact"):
        batch_result_for_round["raw_batch_status"] = batch_result_raw.get("batch_status")
        batch_result_for_round["batch_status"] = status_attribution.get("top_level_final_status")
        batch_result_for_round["ok"] = True
    round_result = build_round_result(
        round_id=round_id,
        sampled_entities=sampled_entities,
        source_plan=combined_source_plan,
        batch_payload=batch_payload,
        batch_result_raw=batch_result_for_round,
        mode=args.mode,
        disabled_actions=disabled_actions,
        mock_current_observations=round_item.get("mock_current_observations")
        if isinstance(round_item.get("mock_current_observations"), list)
        else None,
    )
    round_result["l1_raw_observation_contract"] = build_l1_raw_observation_contract(
        case_id=case_id,
        source_plan=combined_source_plan,
        batch_result=batch_result_raw,
        sampled_entities=sampled_entities,
    )
    round_result["batch_contract_validation"] = contract_validation
    round_result["executable_source_count"] = len(executable)
    round_result["skipped_source_count"] = len(skipped)
    round_result["auto_next_hop"] = {
        "gallery_followup_source_count": len(gallery_source_plan),
        "gallery_followup_executed": bool(gallery_results),
        "gallery_followup_batch_payload": _summarize_chunked_batch_payloads(gallery_payloads) if gallery_payloads else None,
        "rcp_event_followup_source_count": len(rcp_event_source_plan),
        "rcp_event_followup_executed": bool(rcp_event_results),
        "rcp_event_followup_batch_payload": _summarize_chunked_batch_payloads(rcp_event_payloads) if rcp_event_payloads else None,
        "photo_detail_followup_source_count": len(photo_detail_source_plan),
        "photo_detail_followup_executed": bool(photo_detail_results),
        "photo_detail_followup_batch_payload": _summarize_chunked_batch_payloads(photo_detail_payloads) if photo_detail_payloads else None,
        "content_social_followup_source_count": len(content_social_source_plan),
        "content_social_followup_executed": bool(content_social_results),
        "content_social_followup_batch_payload": _summarize_chunked_batch_payloads(content_social_payloads) if content_social_payloads else None,
        "feedback_enforcement_followup_source_count": len(feedback_enforcement_source_plan),
        "feedback_enforcement_followup_executed": bool(feedback_enforcement_results),
        "feedback_enforcement_followup_batch_payload": _summarize_chunked_batch_payloads(feedback_enforcement_payloads) if feedback_enforcement_payloads else None,
        "track_followup_source_count": len(followup_source_plan),
        "track_followup_executed": bool(followup_results),
        "track_followup_batch_payload": _summarize_chunked_batch_payloads(followup_payloads) if followup_payloads else None,
        "one_degree_user_detail_source_count": len(one_degree_user_source_plan),
        "one_degree_user_detail_executed": bool(one_degree_user_results),
        "one_degree_user_detail_batch_payload": _summarize_chunked_batch_payloads(one_degree_user_payloads) if one_degree_user_payloads else None,
        "one_degree_depth_boundary": "associated user details reuse registered user/content/login/strategy sources; newly discovered anchors are context only and do not trigger recursive expansion",
    }
    if disabled_actions:
        round_result["disabled_actions"] = sorted(disabled_actions)
    round_result["raw_batch_status"] = batch_result_raw.get("batch_status")
    round_result["status_attribution"] = status_attribution
    for key in (
        "primary_source_status",
        "primary_source_completed_count",
        "primary_source_partial_count",
        "followup_source_status",
        "followup_blocked_count",
        "followup_blocked_reasons",
        "top_level_final_status",
        "status_contamination",
        "primary_source_impact",
    ):
        round_result[key] = status_attribution.get(key)
    round_result["followup_source_quality"] = status_attribution.get("followup_source_quality")
    round_result["batch_status"] = status_attribution.get("top_level_final_status") or batch_result_raw.get("batch_status")
    if status_attribution.get("status_contamination") and not status_attribution.get("primary_source_impact"):
        round_result["decision"] = {
            "action": "continue",
            "reason": "primary_sources_completed_or_partial_followup_blocked_recorded_separately",
            "required_authorization": False,
        }
    round_result["batch_result"] = build_safe_batch_summary(batch_result_raw, round_result.get("source_quality"))
    timing_trace["global"]["artifact_build_ms"] = _elapsed_ms(batch_started) - int(
        timing_trace["global"]["batch_wait_ms"] or 0
    )
    timing_trace["global"]["total_elapsed_ms"] = _elapsed_ms(round_started)
    round_result["checkpoint_files"] = checkpoint_files
    round_result["latest_checkpoint_file"] = checkpoint_files[-1] if checkpoint_files else None
    round_result["checkpoint_count"] = len(checkpoint_files)
    round_result["partial_result_available"] = bool(checkpoint_files)
    round_result["progress_trace"] = progress_trace
    round_result["timing_trace"] = timing_trace
    round_result["timing_summary"] = [
        {
            "chunk": item.get("chunk_id"),
            "source_group": item.get("source_group"),
            "actions": item.get("actions"),
            "submit_ms": item.get("submit_ms"),
            "wait_ms": item.get("wait_ms"),
            "artifact_ms": item.get("artifact_ms"),
            "checkpoint_ms": item.get("checkpoint_ms"),
            "completed": item.get("completed_count"),
            "blocked": item.get("blocked_count"),
            "timeout": item.get("timeout_count"),
            "auth_failed": item.get("auth_failed_count"),
            "source_gap": item.get("source_gap_count"),
            "short_circuit": item.get("short_circuit_count"),
            "circuit_open": item.get("circuit_open_count"),
            "gap_reason_counts": item.get("gap_reason_counts"),
            "affected_user_count": item.get("affected_user_count"),
            "pending": item.get("pending_count"),
        }
        for item in timing_trace.get("chunks", [])
    ]
    round_result["scheduler_short_circuit_summary"] = {
        "event_count": len(scheduler_state.get("events", []) or []),
        "open_circuit_actions": sorted((scheduler_state.get("open_circuits") or {}).keys()),
        "events": scheduler_state.get("events", []),
        "no_risk_counter_evidence": False,
    }
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
        "candidate_action_groups": build_batch_candidate_action_groups(
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
    primary_source_completed_count = sum(int(item.get("primary_source_completed_count") or 0) for item in round_results)
    primary_source_partial_count = sum(int(item.get("primary_source_partial_count") or 0) for item in round_results)
    followup_blocked_count = sum(int(item.get("followup_blocked_count") or 0) for item in round_results)
    followup_blocked_reasons = unique_strings([
        str(reason)
        for item in round_results
        for reason in item.get("followup_blocked_reasons", []) or []
        if str(reason)
    ])
    top_level_statuses = unique_strings([
        str(item.get("top_level_final_status") or item.get("batch_status") or "")
        for item in round_results
        if str(item.get("top_level_final_status") or item.get("batch_status") or "")
    ])
    status_contamination = any(bool(item.get("status_contamination")) for item in round_results)
    primary_source_impact = any(bool(item.get("primary_source_impact")) for item in round_results)
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
        "source_status_attribution": {
            "primary_source_status": "partial" if primary_source_partial_count else "completed" if primary_source_completed_count else "not_executed",
            "primary_source_completed_count": primary_source_completed_count,
            "primary_source_partial_count": primary_source_partial_count,
            "followup_source_status": "blocked" if followup_blocked_count else "completed_or_not_executed",
            "followup_blocked_count": followup_blocked_count,
            "followup_blocked_reasons": followup_blocked_reasons,
            "top_level_final_status": top_level_statuses[0] if len(top_level_statuses) == 1 else "mixed_round_status",
            "round_top_level_final_statuses": top_level_statuses,
            "status_contamination": status_contamination,
            "primary_source_impact": primary_source_impact,
            "boundary": "primary source completion is reported separately from blocked follow-up source quality",
        },
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
        "l3_candidate_quality_summary": _build_l3_candidate_quality_summary(candidate_features[:10]),
        # TODO-G-R6-SOURCE-QUALITY-PROPAGATION: source_input_quality_table is not
        # aggregated to cumulative layer yet. Pass cumulative_source_quality_table
        # (built from round-level quality rows) to fix evidence_strength=weak.
        # TODO-G-R6-SOURCE-QUALITY-PROPAGATION: pass cumulative_source_quality_table
        "top_explainable_risk_choke_point_candidates": _build_top_explainable_candidates(
            candidate_features[:10]
        )["candidates"],
        "top_explainable_empty_reason": _build_top_explainable_candidates(
            candidate_features[:10]
        )["empty_reason"],
        "unknown_device_field_review_queue": _build_unknown_device_review_queue(candidate_features[:10]),
        "unmaterialized_candidate_review_queue": _unmaterialized_candidate_review_queue(
            candidate_features[:10]
            # TODO-G-R6: add source_input_quality_table=cumulative_source_quality_table
        ),
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
            "七、候选动作分组",
            "包含 P0/P1/P2 + candidate_action_group；P0 仅表示优先补证 / 准备后续验证，不是灰度发布、策略建议或自动处置。",
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
    register_new_validation = validate_register_new_snapshot_rounds_payload(rounds_payload)
    if register_new_validation["required"] and not register_new_validation["valid"]:
        validation = {
            **validation,
            "valid": False,
            "errors": [*validation.get("errors", []), *register_new_validation.get("errors", [])],
            "register_new_snapshot_validation": register_new_validation,
        }
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
    checkpoint_files = [
        path
        for item in round_results
        for path in item.get("checkpoint_files", []) or []
    ]
    partial_result_available = any(bool(item.get("partial_result_available")) for item in round_results) or bool(checkpoint_files)
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
        "register_new_snapshot_validation": register_new_validation,
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
        "checkpoint_files": checkpoint_files,
        "latest_checkpoint_file": checkpoint_files[-1] if checkpoint_files else None,
        "checkpoint_count": len(checkpoint_files),
        "partial_result_available": partial_result_available,
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
    disabled_actions = {str(action) for action in (args.disable_action or []) if str(action)}
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

    content_social_followup_items: list[SourcePlanItem] = []
    feedback_enforcement_followup_items: list[SourcePlanItem] = []
    content_social_followup_results: list[dict[str, Any]] = []
    feedback_enforcement_followup_results: list[dict[str, Any]] = []
    pre_social_result = merge_batch_results([primary_result, *followup_results])
    pre_social_source_quality_matrix = merge_source_quality(executed_source_plan, pre_social_result)
    pre_social_source_observations = build_source_observations(
        executed_source_plan,
        pre_social_source_quality_matrix,
        pre_social_result,
    )
    content_social_followup_items = build_single_case_content_social_followup_items(
        args.user_id,
        pre_social_source_observations,
        window_start_ms=window_start_ms,
        window_end_ms=window_end_ms,
        disabled_actions=disabled_actions,
    )
    if content_social_followup_items:
        executed_source_plan.extend(content_social_followup_items)
        followup_payload = build_batch_payload(
            f"{case_id}:content_social_followup",
            content_social_followup_items,
            dry_run=args.mode == "dry_run",
        )
        followup_batch_payloads.append(followup_payload)
        if args.mode == "dry_run":
            content_social_followup_results.append(build_dry_run_batch_result(content_social_followup_items))
        else:
            content_social_followup_results.append(call_browser_backed_batch(args.browser_backed_base, followup_payload))

    pre_feedback_result = merge_batch_results([primary_result, *followup_results, *content_social_followup_results])
    pre_feedback_source_quality_matrix = merge_source_quality(executed_source_plan, pre_feedback_result)
    pre_feedback_source_observations = build_source_observations(
        executed_source_plan,
        pre_feedback_source_quality_matrix,
        pre_feedback_result,
    )
    feedback_enforcement_followup_items = build_single_case_feedback_enforcement_followup_items(
        args.user_id,
        pre_feedback_source_observations,
        window_start_ms=window_start_ms,
        window_end_ms=window_end_ms,
        disabled_actions=disabled_actions,
    )
    if feedback_enforcement_followup_items:
        executed_source_plan.extend(feedback_enforcement_followup_items)
        followup_payload = build_batch_payload(
            f"{case_id}:feedback_enforcement_followup",
            feedback_enforcement_followup_items,
            dry_run=args.mode == "dry_run",
        )
        followup_batch_payloads.append(followup_payload)
        if args.mode == "dry_run":
            feedback_enforcement_followup_results.append(build_dry_run_batch_result(feedback_enforcement_followup_items))
        else:
            feedback_enforcement_followup_results.append(call_browser_backed_batch(args.browser_backed_base, followup_payload))

    pre_track_result = merge_batch_results([primary_result, *followup_results, *content_social_followup_results, *feedback_enforcement_followup_results])
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

    batch_result_raw = merge_batch_results([
        primary_result,
        *followup_results,
        *content_social_followup_results,
        *feedback_enforcement_followup_results,
    ])
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
    source_commonality_cards = build_batch_source_commonality_cards(
        source_quality_matrix,
        1,
        source_observations,
        disabled_actions,
    )
    orchestration_artifacts = build_round_orchestration_artifacts(
        round_id=1,
        sampled_entities=[args.user_id],
        source_plan=executed_source_plan,
        source_quality_matrix=source_quality_matrix,
        source_observations=source_observations,
        source_commonality_cards=source_commonality_cards,
        mode=args.mode,
        disabled_actions=disabled_actions,
    )
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
        "auto_next_hop": {
            "content_social_followup_source_count": len(content_social_followup_items),
            "content_social_followup_executed": bool(content_social_followup_results),
            "feedback_enforcement_followup_source_count": len(feedback_enforcement_followup_items),
            "feedback_enforcement_followup_executed": bool(feedback_enforcement_followup_results),
            "track_followup_source_count": 1 if track_item and track_missing_device_id and candidate_device_id else 0,
            "track_followup_executed": bool(track_item and track_missing_device_id and candidate_device_id),
        },
        "track_device_resolution": track_device_resolution,
        "user_device_entity_resolution": user_device_entity_resolution,
        "batch_result": batch_result,
        "live_response_inspection": live_response_inspection,
        "transport_status_matrix": batch_result.get("transport_status_matrix", []),
        "source_observations": source_observations,
        "source_commonality_cards": source_commonality_cards,
        "orchestration_artifacts": orchestration_artifacts,
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
    parser.add_argument("--browser-backed-base", default=DEFAULT_BROWSER_BACKED_BASE)
    parser.add_argument("--window-start-ms", type=int)
    parser.add_argument("--window-end-ms", type=int)
    parser.add_argument("--scene-hint", action="append")
    parser.add_argument("--data-window")
    parser.add_argument("--disable-action", action="append", default=[])
    parser.add_argument("--skip-login-logs", action="store_true")
    parser.add_argument("--max-rounds", type=int)
    parser.add_argument("--max-deep-checked", type=int)
    parser.add_argument("--output-json")
    parser.add_argument("--raw-observation-contract-json")
    parser.add_argument("--checkpoint-dir")
    parser.add_argument("--include-abnormal-publish", action="store_true")
    parser.add_argument("--include-same-device", action="store_true")
    parser.add_argument("--format", choices=["json", "pretty"], default="json")
    return parser.parse_args(argv)


def collect_l1_raw_observation_contract(result: dict[str, Any]) -> dict[str, Any]:
    contracts = [
        item.get("l1_raw_observation_contract")
        for item in result.get("round_results", [])
        if isinstance(item, dict) and isinstance(item.get("l1_raw_observation_contract"), dict)
    ]
    if not contracts:
        return {
            "schema_version": "e2e_risk_observation_input_contract_v0_1",
            "case_id": str(result.get("task") or "unknown_case"),
            "generated_at": _iso_now(),
            "export_mode": "source_observation_snapshot",
            "users": [],
            "raw_body_gap_report": [
                {
                    "raw_body_status": "projected_only",
                    "reason": "no l1_raw_observation_contract present in result",
                }
            ],
        }
    users_by_id: dict[str, dict[str, Any]] = {}
    gaps: list[dict[str, Any]] = []
    for contract in contracts:
        gaps.extend(contract.get("raw_body_gap_report") or [])
        for user in contract.get("users", []):
            if not isinstance(user, dict):
                continue
            user_id = str(user.get("user_id") or "unknown_user")
            target = users_by_id.setdefault(user_id, {
                "user_id": user_id,
                "sample_role": user.get("sample_role") or "risk",
                "sources": {},
            })
            for source_name, source_payload in (user.get("sources") or {}).items():
                if not isinstance(source_payload, dict):
                    continue
                target_source = target["sources"].setdefault(source_name, {})
                for layer, layer_payload in source_payload.items():
                    unique_layer = layer
                    suffix = 2
                    while unique_layer in target_source:
                        unique_layer = f"{layer}_{suffix}"
                        suffix += 1
                    target_source[unique_layer] = layer_payload
    first = contracts[0]
    return {
        "schema_version": "e2e_risk_observation_input_contract_v0_1",
        "case_id": first.get("case_id") or str(result.get("task") or "unknown_case"),
        "generated_at": _iso_now(),
        "export_mode": "source_observation_snapshot",
        "credential_secret_policy": first.get("credential_secret_policy", {}),
        "source_registry_version": first.get("source_registry_version"),
        "field_alignment_registry_version": first.get("field_alignment_registry_version"),
        "users": [users_by_id[key] for key in sorted(users_by_id)],
        "raw_body_gap_report": gaps,
    }


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    result = build_result(args)
    if args.raw_observation_contract_json:
        raw_contract_path = Path(args.raw_observation_contract_json)
        raw_contract_path.parent.mkdir(parents=True, exist_ok=True)
        raw_contract = collect_l1_raw_observation_contract(result)
        raw_contract_path.write_text(json.dumps(raw_contract, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    output_result = build_safe_stdout_result(result)
    if args.output_json:
        output_path = Path(args.output_json)
        output_path.parent.mkdir(parents=True, exist_ok=True)
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
