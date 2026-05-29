#!/usr/bin/env python3
"""Check local network readiness for the DataAgent Conversational API.

This script never sends a business payload, never submits SQL, never calls
Hive, never reads .ks_sso, and never constructs authentication headers.
"""

from __future__ import annotations

import argparse
import json
import os
import socket
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


DEFAULT_ENDPOINT_PATH = "/v1/chat/completions/full"
DEFAULT_TIMEOUT_SECONDS = 5.0
ALLOWED_NETWORK_STATUS = {
    "env_missing",
    "dns_failed",
    "tcp_failed",
    "tls_failed",
    "http_reachable",
    "auth_required",
    "permission_denied",
    "read_timeout",
    "unknown",
}


def parse_timeout(env: dict[str, str]) -> tuple[float, str | None]:
    raw = env.get("DATAAGENT_HTTP_TIMEOUT_SECONDS")
    if raw is None or raw.strip() == "":
        return DEFAULT_TIMEOUT_SECONDS, None
    try:
        timeout = float(raw)
    except ValueError:
        return DEFAULT_TIMEOUT_SECONDS, "invalid_DATAAGENT_HTTP_TIMEOUT_SECONDS"
    if timeout <= 0:
        return DEFAULT_TIMEOUT_SECONDS, "invalid_DATAAGENT_HTTP_TIMEOUT_SECONDS"
    return timeout, None


def build_urls(env: dict[str, str]) -> tuple[str | None, str | None, str | None]:
    endpoint_url = env.get("DATAAGENT_ENDPOINT_URL")
    base_url = env.get("DATAAGENT_BASE_URL")
    endpoint_path = env.get("DATAAGENT_ENDPOINT_PATH") or DEFAULT_ENDPOINT_PATH

    if endpoint_url:
        parsed_endpoint = urllib.parse.urlparse(endpoint_url)
        if not parsed_endpoint.scheme or not parsed_endpoint.netloc:
            return None, None, "invalid_DATAAGENT_ENDPOINT_URL"
        base = f"{parsed_endpoint.scheme}://{parsed_endpoint.netloc}"
        return base, sanitize_url(endpoint_url), None

    if not base_url:
        return None, None, "missing_DATAAGENT_BASE_URL_or_DATAAGENT_ENDPOINT_URL"

    parsed_base = urllib.parse.urlparse(base_url)
    if not parsed_base.scheme or not parsed_base.netloc:
        return None, None, "invalid_DATAAGENT_BASE_URL"

    path = endpoint_path if endpoint_path.startswith("/") else f"/{endpoint_path}"
    endpoint = urllib.parse.urljoin(f"{parsed_base.scheme}://{parsed_base.netloc}", path)
    return f"{parsed_base.scheme}://{parsed_base.netloc}", sanitize_url(endpoint), None


def sanitize_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    netloc = parsed.hostname or ""
    if parsed.port:
        netloc = f"{netloc}:{parsed.port}"
    return urllib.parse.urlunparse((parsed.scheme, netloc, parsed.path or "/", "", "", ""))


def endpoint_parts(endpoint_url: str) -> tuple[str, str, int]:
    parsed = urllib.parse.urlparse(endpoint_url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("unsupported_url_scheme")
    if not parsed.hostname:
        raise ValueError("missing_hostname")
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    return parsed.scheme, parsed.hostname, port


def status_result(
    *,
    network_status: str,
    endpoint_url: str | None,
    base_url: str | None,
    timeout_seconds: float,
    reason: str | None = None,
    checks: dict[str, Any] | None = None,
    http_status: int | None = None,
) -> dict[str, Any]:
    if network_status not in ALLOWED_NETWORK_STATUS:
        network_status = "unknown"
    return {
        "schema_version": "dataagent_network_readiness_check_v1",
        "network_status": network_status,
        "reason": reason,
        "base_url_configured": base_url is not None,
        "endpoint_configured": endpoint_url is not None,
        "endpoint_url": endpoint_url,
        "timeout_seconds": timeout_seconds,
        "http_status": http_status,
        "checks": checks or {},
        "safety": {
            "business_payload_sent": False,
            "hive_called": False,
            "sql_submitted": False,
            "sso_state_read": False,
            "auth_header_sent": False,
            "cookie_token_session_header_printed": False,
        },
    }


def classify_http_error(code: int) -> str:
    if code == 401:
        return "auth_required"
    if code == 403:
        return "permission_denied"
    if code in {200, 204, 301, 302, 307, 308, 405}:
        return "http_reachable"
    return "unknown"


def classify_timeout_error(error: BaseException) -> bool:
    text = str(getattr(error, "reason", error)).lower()
    return "timed out" in text or "timeout" in text


def run_check(env: dict[str, str]) -> dict[str, Any]:
    timeout_seconds, timeout_warning = parse_timeout(env)
    base_url, endpoint_url, env_error = build_urls(env)
    checks: dict[str, Any] = {
        "env_configured": env_error is None,
        "dns_resolved": False,
        "tcp_connected": False,
        "tls_connected": False,
        "http_endpoint_checked": False,
        "read_timeout_classifiable": True,
    }
    if timeout_warning:
        checks["timeout_warning"] = timeout_warning
    if env_error:
        return status_result(
            network_status="env_missing" if env_error.startswith("missing_") else "unknown",
            endpoint_url=endpoint_url,
            base_url=base_url,
            timeout_seconds=timeout_seconds,
            reason=env_error,
            checks=checks,
        )

    assert endpoint_url is not None
    try:
        scheme, host, port = endpoint_parts(endpoint_url)
    except ValueError as exc:
        return status_result(
            network_status="unknown",
            endpoint_url=endpoint_url,
            base_url=base_url,
            timeout_seconds=timeout_seconds,
            reason=str(exc),
            checks=checks,
        )

    try:
        socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
        checks["dns_resolved"] = True
    except socket.gaierror as exc:
        return status_result(
            network_status="dns_failed",
            endpoint_url=endpoint_url,
            base_url=base_url,
            timeout_seconds=timeout_seconds,
            reason=f"dns_failed:{exc.errno}",
            checks=checks,
        )

    try:
        with socket.create_connection((host, port), timeout=timeout_seconds) as sock:
            checks["tcp_connected"] = True
            if scheme == "https":
                context = ssl.create_default_context()
                with context.wrap_socket(sock, server_hostname=host):
                    checks["tls_connected"] = True
            else:
                checks["tls_connected"] = None
    except socket.timeout:
        return status_result(
            network_status="tcp_failed",
            endpoint_url=endpoint_url,
            base_url=base_url,
            timeout_seconds=timeout_seconds,
            reason="tcp_timeout",
            checks=checks,
        )
    except ssl.SSLError as exc:
        return status_result(
            network_status="tls_failed",
            endpoint_url=endpoint_url,
            base_url=base_url,
            timeout_seconds=timeout_seconds,
            reason=f"tls_failed:{exc.__class__.__name__}",
            checks=checks,
        )
    except OSError as exc:
        return status_result(
            network_status="tcp_failed",
            endpoint_url=endpoint_url,
            base_url=base_url,
            timeout_seconds=timeout_seconds,
            reason=f"tcp_failed:{exc.__class__.__name__}",
            checks=checks,
        )

    request = urllib.request.Request(endpoint_url, method="HEAD")
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            checks["http_endpoint_checked"] = True
            return status_result(
                network_status="http_reachable",
                endpoint_url=endpoint_url,
                base_url=base_url,
                timeout_seconds=timeout_seconds,
                checks=checks,
                http_status=int(response.getcode()),
            )
    except urllib.error.HTTPError as exc:
        checks["http_endpoint_checked"] = True
        status = classify_http_error(exc.code)
        reason = None
        if status in {"auth_required", "permission_denied"}:
            reason = "permission_boundary"
        else:
            reason = f"http_status_{exc.code}"
        return status_result(
            network_status=status,
            endpoint_url=endpoint_url,
            base_url=base_url,
            timeout_seconds=timeout_seconds,
            reason=reason,
            checks=checks,
            http_status=exc.code,
        )
    except (urllib.error.URLError, socket.timeout, TimeoutError) as exc:
        checks["http_endpoint_checked"] = True
        if classify_timeout_error(exc):
            return status_result(
                network_status="read_timeout",
                endpoint_url=endpoint_url,
                base_url=base_url,
                timeout_seconds=timeout_seconds,
                reason="read_timeout",
                checks=checks,
            )
        return status_result(
            network_status="unknown",
            endpoint_url=endpoint_url,
            base_url=base_url,
            timeout_seconds=timeout_seconds,
            reason=exc.__class__.__name__,
            checks=checks,
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="DataAgent local network readiness check.")
    parser.add_argument("--json", action="store_true", help="Emit JSON.")
    args = parser.parse_args(argv)

    result = run_check(dict(os.environ))
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(result["network_status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
