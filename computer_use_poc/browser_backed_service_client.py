#!/usr/bin/env python3
"""Executable client for the local browser-backed source service.

This module intentionally keeps Dennis out of browser ownership and auth
material handling. It only calls fixed local service actions with typed JSON
parameters and normalizes standard source responses for the source completion
matrix / partial evidence card path.
"""

from __future__ import annotations

import argparse
import json
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
}

ACTION_TO_SOURCE = {
    "track_analysis_summary": "track_analysis_summary",
    "rcp_snapshot": "rcp_snapshot",
    "weapon_inventory": "weapon_inventory",
    "login_logs_search": "login_logs_search",
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
    source_card = service_payload.get("source_card") or _synthetic_source_card(action_name, normalized_status, error_type)
    source_quality = service_payload.get("source_quality") or _synthetic_source_quality(normalized_status, error_type)
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
        "source_card": source_card,
        "source_quality": source_quality,
        "sensitive_output": False,
        "source_provenance": "browser_backed_service",
        "no_data_not_risk_exclusion": no_data_not_risk_exclusion,
    }

    response_summary = _safe_nested_get(service_payload, ("data", "response_summary"))
    if isinstance(response_summary, Mapping):
        normalized["response_shape_summary"] = dict(response_summary)

    return normalized


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
            "no_data_not_risk_exclusion": bool(result.get("no_data_not_risk_exclusion")),
        }
    return matrix


def build_partial_evidence_card(results: Iterable[Mapping[str, Any]]) -> Dict[str, Any]:
    """Build a display-safe partial evidence card from normalized source results."""

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
            }
        )

    return {
        "card_type": "partial_evidence_card",
        "sensitive_output": False,
        "source_completion_matrix": matrix,
        "completed_sources": matrix["completed_sources"],
        "no_data_sources": matrix["no_data_sources"],
        "blocked_sources": matrix["blocked_sources"],
        "source_quality": matrix["source_quality"],
        "no_data_not_risk_exclusion": any(
            bool(result.get("no_data_not_risk_exclusion")) for result in materialized_results
        ),
        "evidence_sections": evidence_sections,
    }


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


def _synthetic_source_card(action_name: str, source_status: str, error_type: Optional[str]) -> Dict[str, Any]:
    return {
        "source_name": ACTION_TO_SOURCE[action_name],
        "action_name": action_name,
        "source_status": source_status,
        "error_type": error_type,
        "source_provenance": "browser_backed_service",
        "body_policy": {
            "raw_response_full_body_returned": False,
            "sensitive_output": False,
        },
    }


def _synthetic_source_quality(source_status: str, error_type: Optional[str], detail: Optional[str] = None) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "source_status": source_status,
        "error_type": error_type,
        "quality_status": "source_unavailable" if source_status != "completed" else "usable",
        "no_data_not_risk_exclusion": source_status == "no_data",
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
        return _FakeResponse(200, self.payload or {})


def _fixture_payload(action_name: str, source_status: str, error_type: Optional[str] = None) -> Dict[str, Any]:
    return {
        "action": action_name,
        "status": source_status,
        "source_status": source_status,
        "error_type": error_type,
        "latency_ms": 123,
        "source_card": {
            "source_name": ACTION_TO_SOURCE[action_name],
            "action_name": action_name,
            "source_status": source_status,
            "body_policy": {"raw_response_full_body_returned": False},
        },
        "source_quality": {
            "source_status": source_status,
            "error_type": error_type,
            "no_data_not_risk_exclusion": source_status in NO_DATA_STATUSES,
        },
        "sensitive_output": False,
        "data": {
            "response_summary": {
                "shape_only": True,
                "raw_response_full_body_returned": False,
            }
        },
    }


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

    raw_payload = _fixture_payload("login_logs_search", "completed")
    raw_payload["data"]["login_records"] = [{"ip": "203.0.113.10", "deviceId": "ANDROID_raw"}]
    result = normalize_service_response("login_logs_search", raw_payload)
    serialized_result = json.dumps(result, ensure_ascii=True)
    assert "login_records" not in serialized_result
    assert "ANDROID_raw" not in serialized_result
    results.append(("raw_login_record_body_not_output", "passed"))

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
