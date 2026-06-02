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

LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1"}
SECRET_KEY_FRAGMENTS = (
    "cookie",
    "token",
    "session",
    "header",
    "authorization",
    "password",
)
BODY_KEYS_TO_SUPPRESS = {
    "body",
    "raw_body",
    "response_body",
    "upstream_body",
    "html",
    "raw_payload",
}


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
                "limit": 50,
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
        if item.execution_group in {"auth_sensitive_serial", "dependency_serial"}:
            group.setdefault("depends_on", ["independent_parallel"])
        group["sources"].append(item.to_batch_source())

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
    forbidden_key_parts = set(SECRET_KEY_FRAGMENTS) | {"url", "uri", "href", "path", "endpoint", "raw_body"}

    def scan_for_forbidden(value: Any, path: str) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                lowered = key.lower()
                if any(part in lowered for part in forbidden_key_parts):
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
            if any(fragment in lowered for fragment in SECRET_KEY_FRAGMENTS):
                clean[key] = "[suppressed]"
                continue
            if lowered in BODY_KEYS_TO_SUPPRESS and isinstance(item, (str, bytes, dict, list)):
                clean[key] = "[suppressed]"
                continue
            clean[key] = sanitize_for_output(item)
        return clean
    if isinstance(value, list):
        return [sanitize_for_output(item) for item in value]
    return value


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
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"content-type": "application/json"},
        method="POST",
    )
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(request, timeout=35) as response:
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


def merge_source_quality(source_plan: list[SourcePlanItem], batch_result: dict[str, Any]) -> dict[str, Any]:
    plan_by_id = {item.source_id: item for item in source_plan}
    rows = normalize_mapping_or_list(batch_result.get("transport_status_matrix"))
    if not rows:
        rows = rows_from_source_results(batch_result.get("source_results"))
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

    seen: set[str] = set()
    for row in rows:
        source_id = row.get("source_id") or "unknown_source"
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
        if classification == "no_data":
            notes.append("no_data_not_risk_exclusion")
        if classification in {"blocked", "timeout", "parse_error", "auth_failed"}:
            notes.append("missing_evidence_not_counter_evidence")
        if classification == "planned":
            notes.append("dry_run_not_platform_evidence")

        per_source.append(
            {
                "source_id": source_id,
                "action": row.get("action") or (item.action if item else None),
                "quality_class": classification,
                "source_status": row.get("source_status"),
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
        reason = row.get("error_type") or row.get("source_status") or quality
        missing.append(
            {
                "source_id": row["source_id"],
                "action": row.get("action"),
                "quality_class": quality,
                "reason": reason,
                "blocks_final_conclusion": quality != "planned",
                "is_low_risk_counter_evidence": False,
            }
        )
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
            "user_device_graph",
            "device_risk_label",
            "device_relation",
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
    "publish_time": {"publish_time", "publishTime", "createTime", "uploadTime"},
    "publish_device": {"publish_device", "publishDevice", "publishDeviceId", "device_id", "deviceId", "did"},
    "publish_source": {"publish_source", "publishSource", "source", "clientType", "publishPlatform"},
    "publish_ip": {"publish_ip", "publishIp", "ip", "clientIp"},
    "publish_ua": {"publish_ua", "publishUA", "publishUa", "ua", "userAgent"},
    "content_status": {"content_status", "photoStatus", "auditStatus", "status"},
    "audit_or_strategy_reason": {"audit_reason", "strategyReason", "hitReason", "reason"},
    "candidate_device_id": {"candidate_device_id", "device_id", "deviceId", "did"},
    "track_data_ready": {"track_data_ready", "dataReady", "ready"},
    "event_day_frontend_activity": {"event_day_frontend_activity", "frontendActivity", "activePv"},
    "frontend_backend_activity_alignment": {"frontend_backend_activity_alignment", "frontBackendAlignment"},
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
    serialized = json.dumps(row, ensure_ascii=False, sort_keys=True).lower()
    return row.get("body_truncated") is True or "response_too_large" in serialized or "too_large" in serialized


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
            if any(fragment in lowered for fragment in SECRET_KEY_FRAGMENTS):
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

    for item in source_plan:
        row = rows_by_id.get(item.source_id, {})
        action = str(row.get("action") or item.action)
        contract = SOURCE_OBSERVATION_CONTRACTS.get(action, {})
        quality = str(row.get("quality_class") or "blocked")
        flags: list[str] = []
        raw_source_payload = raw_rows_by_id.get(item.source_id, {})
        expected_business_fields = list(contract.get("expected_business_fields", []))
        safe_observation = build_safe_observation(
            source_id=item.source_id,
            action=action,
            source_payload=raw_source_payload,
            transport_row=row,
            expected_business_fields=expected_business_fields,
            chain_section=str(contract.get("chain_section", "source_quality")),
            role=str(contract.get("role", item.expected_observation)),
        )
        field_handles = list(safe_observation.get("extracted_safe_handles", []))
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
            if quality == "no_data":
                flags.append("login_no_data_or_window_gap_not_ato_exclusion")
        elif action == "archives_user_analysis":
            if quality == "partial" or row.get("body_truncated"):
                flags.append("partial_behavior_timeline")
            if quality in {"completed", "partial"} and "behavior_chain_business_fields_missing" not in flags and missing_business_fields:
                flags.append("behavior_chain_business_fields_missing")
        elif action == "archives_photo_search":
            if quality in {"completed", "partial"} and missing_business_fields:
                flags.append("content_chain_business_fields_missing")
            if quality == "no_data":
                flags.append("photo_search_no_data_not_abnormal_publish_exclusion")
            flags.append("publish_device_login_device_alignment_required")
        elif action == "track_analysis_check_data_ready":
            flags.append("track_check_data_ready_not_risk_conclusion")
            if "device_id" in row.get("missing_required_fields", []):
                flags.extend([
                    "user_device_entity_resolution_attempted",
                    "candidate_device_id_missing",
                ])
        elif action == "archives_related_users":
            flags.append("archives_related_users_spread_clue_not_gang")
        elif action == "weapon_inventory":
            flags.append("weapon_device_graph_not_ato_conclusion")
        elif action == "rcp_event_feature_list" and (quality == "partial" or row.get("body_truncated")):
            flags.append("feature_list_partial_only_feature_group_summary")
        elif action == "rcp_policy_tree_lookup":
            flags.append("policy_tree_asset_not_event_hit_path")

        if quality in {"completed", "partial"} and action in {"archives_user_analysis", "archives_photo_search"}:
            flags.append("completed_transport_not_business_chain_closure")

        observations.append(
            {
                "dennis_observation": safe_observation,
                "source_id": item.source_id,
                "action": action,
                "chain_section": contract.get("chain_section", "source_quality"),
                "quality_class": quality,
                "role": contract.get("role", item.expected_observation),
                "expected_business_fields": expected_business_fields,
                "extracted_business_fields": extracted_business_fields,
                "observed_field_handles": field_handles,
                "parsed_body_field_handles": safe_observation.get("parsed_body_safe_handles", []),
                "missing_business_fields": missing_business_fields,
                "candidate_device_ids": safe_observation.get("candidate_device_ids", []),
                "interpretation_flags": unique_strings(flags + list(safe_observation.get("interpretation_flags", []))),
                "breakpoint_type": infer_observation_breakpoint(
                    quality=quality,
                    row=row,
                    safe_observation=safe_observation,
                    missing_business_fields=missing_business_fields,
                ),
                "evidence_use": (
                    "business_evidence_candidate"
                    if extracted_business_fields and quality in {"completed", "partial"}
                    else "transport_only_boundary"
                    if quality in {"completed", "partial"}
                    else "missing_evidence_or_boundary_only"
                ),
                "is_low_risk_counter_evidence": False,
            }
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
    candidates: list[dict[str, str]] = []
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
                    "field_path": str(candidate.get("field_path") or "safe_observation.candidate_device_ids"),
                }
            )
    deduped: list[dict[str, str]] = []
    seen_ids: set[str] = set()
    for candidate in candidates:
        device_id = candidate["device_id"]
        if device_id in seen_ids:
            continue
        seen_ids.add(device_id)
        deduped.append(candidate)

    planned_actions = {item.action for item in source_plan}
    candidate_source_ids = {candidate["source_id"] for candidate in deduped}
    planned_source_ids_by_action = {item.action: item.source_id for item in source_plan}

    def source_has_candidate(action: str) -> bool:
        source_id = planned_source_ids_by_action.get(action)
        return bool(source_id and source_id in candidate_source_ids)

    device_entity_gap_breakdown = {
        "login_device_not_extracted": not source_has_candidate("login_logs_search"),
        "publish_device_not_extracted": not source_has_candidate("archives_photo_search"),
        "user_analysis_device_not_extracted": not source_has_candidate("archives_user_analysis"),
        "user_device_graph_not_checked_or_failed": (
            "weapon_inventory" not in planned_actions or not source_has_candidate("weapon_inventory")
        ),
        "track_candidate_device_missing": not deduped,
    }
    missing_device_reasons = [
        reason for reason, missing in device_entity_gap_breakdown.items() if missing
    ]
    return {
        "layer": "user_device_entity_resolution",
        "default_p0_entity_layer": True,
        "purpose": "bridge user-level evidence to device-level Track/Weapon/publish-device alignment",
        "candidate_device_ids": deduped,
        "candidate_device_id_missing": not deduped,
        "candidate_device_id_missing_semantics": "missing any device entity usable for login/publish/user-analysis/Track/Weapon alignment, not only missing risky device",
        "device_entity_gap_breakdown": device_entity_gap_breakdown,
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
                    "device_entity_gap_breakdown": device_entity_gap_breakdown,
                    "missing_device_reasons": missing_device_reasons,
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
        options.append(
            {
                "module_id": module_id,
                "label": module["label"],
                "purpose": module["purpose"],
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


def build_offline_backfill_recommendation() -> dict[str, Any]:
    """Compatibility wrapper for callers that have not passed current gaps."""
    return {
        "required_when": "realtime control/action/device/baseline chain is incomplete",
        "dataagent_hive_called": False,
        "authorization_required": True,
        "authorization_mode": "select_dynamic_modules_by_id",
        "fixed_1_to_5_menu": False,
        "module_generation": "dynamic_from_current_missing_evidence",
        "options": [],
        "user_prompt": "当前缺口未传入；需先基于 missing_evidence 动态生成 module_id。",
        "authorization_boundary": [
            "only selected dynamic modules may enter DataAgent/Hive query plan",
            "unselected modules remain missing_evidence",
            "previous authorization is not reusable for a new module, table, time range, or evidence direction",
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
        "missing_module": "device_history_baseline",
    },
}


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
        relevant = [obs for obs in source_observations if str(obs.get("source_id")) in source_ids]
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
            breakpoints.append("candidate_device_id_missing")
            missing_by_source.append(
                {
                    "source_id": "user_device_entity_resolution",
                    "action": "entity_resolution",
                    "missing_fields": ["candidate_device_id"],
                    "breakpoint_type": "candidate_device_id_missing",
                }
            )

        missing_fields_total = sorted(required_fields - extracted_fields)
        if not missing_fields_total and relevant and not non_closed_source_seen:
            chain_state = "closed"
        elif extracted_fields:
            chain_state = "partial"
        else:
            chain_state = "missing"
        status[chain_id] = {
            "label": definition["label"],
            "status": chain_state,
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
    for item in source_plan:
        payload = rows_by_id.get(item.source_id, {})
        row = payload.get("transport") if isinstance(payload.get("transport"), dict) else payload
        observation = observations_by_source.get(item.source_id, {})
        dennis_observation = observation.get("dennis_observation", {}) if isinstance(observation, dict) else {}
        rows.append(
            {
                "source_id": item.source_id,
                "action": item.action,
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
                "evidence_card_consumed": item.source_id in consumed_sources,
                "chain_coverage": observation.get("chain_section"),
                "breakpoint_type": observation.get("breakpoint_type"),
            }
        )
    return rows


def render_user_answer_draft(evidence_card: dict[str, Any]) -> str:
    chain_status = evidence_card.get("chain_status", {})
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

    return "\n".join(
        [
            "一句话判断：目前不能确认被盗，也不能排除被盗；结论状态是 insufficient_support。",
            "三条证据链状态：",
            line("web_publish_fact"),
            line("web_login_history"),
            line("device_identity_alignment"),
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

    if mode == "dry_run":
        conclusion_state = "not_judged_dry_run"
        final_status = "dry_run"
    elif completed or partial:
        conclusion_state = "insufficient_support"
        final_status = "partial"
    else:
        conclusion_state = "insufficient_support"
        final_status = "insufficient_support"

    observations_by_section: dict[str, list[dict[str, Any]]] = {}
    for observation in source_observations:
        section = str(observation.get("chain_section") or "source_quality")
        observations_by_section.setdefault(section, []).append(observation)

    chain_status = build_chain_status(source_observations, user_device_entity_resolution)

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


def build_result(args: argparse.Namespace) -> dict[str, Any]:
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
    primary_candidates = primary_user_device_entity_resolution.get("candidate_device_ids", [])
    candidate_device_id = (
        args.device_id
        or (primary_candidates[0]["device_id"] if primary_candidates else None)
        or extract_candidate_device_id(primary_result)
    )
    followup_batch_payloads: list[dict[str, Any]] = []
    followup_results: list[dict[str, Any]] = []
    track_device_resolution = {
        "device_id_provided": args.device_id is not None,
        "candidate_device_lookup_attempted": track_missing_device_id,
        "candidate_device_found": bool(candidate_device_id),
        "track_missing_device_id_blocks_batch": False,
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
    source_quality_matrix = merge_source_quality(source_plan, batch_result_raw)
    source_observations = build_source_observations(source_plan, source_quality_matrix, batch_result_raw)
    user_device_entity_resolution = build_user_device_entity_resolution(
        source_plan,
        batch_result_raw,
        provided_device_id=args.device_id,
        source_observations=source_observations,
    )
    batch_result = sanitize_for_output(batch_result_raw)
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
    parser.add_argument("--task", choices=["ato_single_case"], required=True)
    parser.add_argument("--user-id", required=True)
    parser.add_argument("--device-id")
    parser.add_argument("--mode", choices=["dry_run", "live"], default="dry_run")
    parser.add_argument("--browser-backed-base")
    parser.add_argument("--window-start-ms", type=int)
    parser.add_argument("--window-end-ms", type=int)
    parser.add_argument("--include-abnormal-publish", action="store_true")
    parser.add_argument("--include-same-device", action="store_true")
    parser.add_argument("--format", choices=["json", "pretty"], default="json")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    result = build_result(args)
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"task: {result['task']}")
        print(f"mode: {result['mode']}")
        print(f"final_status: {result['final_status']}")
        print("source_plan:")
        for item in result["source_plan"]:
            print(f"- {item['source_id']} -> {item['action']} [{item['execution_group']}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
