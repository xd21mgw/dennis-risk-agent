#!/usr/bin/env python3
"""Local no-platform health checks for existing full_runtime source runners.

This script is a validator, not a source runner. It only checks invocation
contracts and structured output for runners that already exist in full_runtime.
It never supplies enough valid input to sso_session_runner to reach live SSO or
cookie fallback code paths.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
FULL_RUNTIME_ROOT = REPO_ROOT / "outputs" / "full_runtime"
MANIFEST_PATH = FULL_RUNTIME_ROOT / "RUNTIME_MANIFEST.md"

SENSITIVE_OUTPUT_RE = re.compile(
    r"("
    r"authorization\s*[:=]|"
    r"bearer\s+[a-z0-9._=-]+|"
    r"cookie\s*[:=]|"
    r"header\s*[:=]|"
    r"token\s*[:=]|"
    r"session\s*[:=]|"
    r"password\s*[:=]"
    r")",
    re.IGNORECASE,
)

COMMON_REQUIRED_OUTPUT_KEYS = {
    "source_quality",
    "redaction",
    "real_platform_request_executed",
}

CHECKS: list[dict[str, Any]] = [
    {
        "source_name": "user_login_log",
        "runner_file": "bin/sso_session_runner",
        "command": [
            "bin/sso_session_runner",
            "--platform",
            "login_log",
            "--action",
            "query_user_login_log",
            "--format",
            "json",
        ],
        "expected_exit_codes": {2},
        "expected_source_status": {"blocked"},
        "expected_failure_reason": "validation_failed",
        "no_platform_expected": True,
        "contract_mode": "missing_required_args_no_platform",
    },
    {
        "source_name": "weapon_graphData",
        "runner_file": "bin/sso_session_runner",
        "command": [
            "bin/sso_session_runner",
            "--platform",
            "weapon",
            "--action",
            "graph_data",
            "--format",
            "json",
        ],
        "expected_exit_codes": {2},
        "expected_source_status": {"blocked"},
        "expected_failure_reason": "validation_failed",
        "no_platform_expected": True,
        "contract_mode": "missing_required_args_no_platform",
    },
    {
        "source_name": "weapon_riskData",
        "runner_file": "bin/sso_session_runner",
        "command": [
            "bin/sso_session_runner",
            "--platform",
            "weapon",
            "--action",
            "risk_data",
            "--format",
            "json",
        ],
        "expected_exit_codes": {2},
        "expected_source_status": {"blocked"},
        "expected_failure_reason": "validation_failed",
        "no_platform_expected": True,
        "contract_mode": "missing_required_args_no_platform",
    },
    {
        "source_name": "archives_center_profile",
        "runner_file": "bin/archives_profile_runner",
        "command": [
            "bin/archives_profile_runner",
            "--action",
            "archives.profile_home_info",
            "--user-id",
            "544963630",
            "--timeout",
            "1",
            "--format",
            "json",
        ],
        "expected_exit_codes": {0},
        "expected_source_status": {"blocked"},
        "expected_failure_reason": "archives_runner_not_connected",
        "no_platform_expected": True,
        "contract_mode": "safe_local_stub",
    },
]


def extract_json_object(stdout: str) -> dict[str, Any]:
    start = stdout.find("{")
    if start < 0:
        raise ValueError("stdout did not contain a JSON object")
    return json.loads(stdout[start:])


def manifest_contains(rel_path: str) -> bool:
    if not MANIFEST_PATH.is_file():
        return False
    text = MANIFEST_PATH.read_text(encoding="utf-8")
    return f"`{rel_path}`" in text or f'"{rel_path}"' in text


def has_sensitive_output(text: str) -> bool:
    return bool(SENSITIVE_OUTPUT_RE.search(text))


def resolve_source_status(payload: dict[str, Any]) -> Any:
    if payload.get("source_status"):
        return payload.get("source_status")
    if payload.get("archives_profile_source_status"):
        return payload.get("archives_profile_source_status")
    source_card = payload.get("source_card")
    if isinstance(source_card, dict):
        return source_card.get("source_status")
    return None


def resolve_sensitive_output(payload: dict[str, Any]) -> Any:
    if "sensitive_output" in payload:
        return payload.get("sensitive_output")
    redaction = payload.get("redaction")
    if isinstance(redaction, dict):
        return redaction.get("sensitive_output")
    return None


def run_check(check: dict[str, Any]) -> dict[str, Any]:
    runner_path = REPO_ROOT / check["runner_file"]
    result: dict[str, Any] = {
        "source_name": check["source_name"],
        "runner_file": check["runner_file"],
        "contract_mode": check["contract_mode"],
        "runner_present": runner_path.is_file(),
        "runner_in_full_runtime_manifest": manifest_contains(check["runner_file"]),
        "command": check["command"],
        "status": "FAILED",
        "errors": [],
    }

    if not result["runner_present"]:
        result["errors"].append("runner_file_missing")
        return result

    proc = subprocess.run(
        check["command"],
        cwd=REPO_ROOT,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=10,
        check=False,
    )
    result["exit_code"] = proc.returncode
    result["stderr_summary"] = proc.stderr.strip()[:300]

    combined_output = f"{proc.stdout}\n{proc.stderr}"
    if has_sensitive_output(combined_output):
        result["errors"].append("sensitive_output_pattern_detected")

    if proc.returncode not in check["expected_exit_codes"]:
        result["errors"].append(f"unexpected_exit_code:{proc.returncode}")

    try:
        payload = extract_json_object(proc.stdout)
    except Exception as exc:
        result["errors"].append(f"json_parse_failed:{type(exc).__name__}")
        return result

    result["observed_source_status"] = resolve_source_status(payload)
    result["real_platform_request_executed"] = payload.get("real_platform_request_executed")
    result["sensitive_output"] = resolve_sensitive_output(payload)
    result["output_keys_present"] = sorted(COMMON_REQUIRED_OUTPUT_KEYS.intersection(payload))
    result["source_quality_failure_reason"] = (
        payload.get("source_quality", {}).get("failure_reason")
        if isinstance(payload.get("source_quality"), dict)
        else None
    )

    missing_keys = sorted(COMMON_REQUIRED_OUTPUT_KEYS.difference(payload))
    if missing_keys:
        result["errors"].append(f"missing_common_output_keys:{','.join(missing_keys)}")

    if result["observed_source_status"] not in check["expected_source_status"]:
        result["errors"].append(f"unexpected_source_status:{result['observed_source_status']}")

    if check["no_platform_expected"] and payload.get("real_platform_request_executed") is not False:
        result["errors"].append("real_platform_request_executed_not_false")

    if resolve_sensitive_output(payload) is not False:
        result["errors"].append("sensitive_output_not_false")

    expected_failure = check.get("expected_failure_reason")
    if expected_failure and result["source_quality_failure_reason"] != expected_failure:
        result["errors"].append(
            f"unexpected_failure_reason:{result['source_quality_failure_reason']}"
        )

    if result["errors"]:
        return result
    result["status"] = "PASS"
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run local no-platform source runner health checks.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    args = parser.parse_args(argv)

    results = [run_check(check) for check in CHECKS]
    passed = all(item["status"] == "PASS" for item in results)
    payload = {
        "status": "PASS_LOCAL_RUNNER_CONTRACT_CHECK" if passed else "FAILED_LOCAL_RUNNER_CONTRACT_CHECK",
        "scope": "existing_full_runtime_runners_no_platform",
        "real_platform_access": False,
        "dataagent_hive_called": False,
        "checks": results,
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(payload["status"])
        for item in results:
            print(f"- {item['source_name']}: {item['status']} ({item['contract_mode']})")
            if item["errors"]:
                print(f"  errors: {', '.join(item['errors'])}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
