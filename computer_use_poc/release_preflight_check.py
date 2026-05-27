#!/usr/bin/env python3
"""Release preflight gate for Dennis Risk Agent packages.

This wrapper makes package asset scanning a required preflight step before a
release directory can be packed or uploaded. It calls package_asset_scanner.py
and prints only a safe summary; scanner raw matches and file content are never
forwarded to stdout.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCANNER = ROOT / "computer_use_poc" / "package_asset_scanner.py"
DEFAULT_REQUIRED_FILES = [
    "README.md",
    "computer_use_poc/runtime_semi_open_user_guide_v1.md",
    "computer_use_poc/multi_entry_runtime_guard_v1.md",
    "computer_use_poc/answer_experience_templates.md",
]
FOCUSED_SAFE_SUMMARY_PATCH_REQUIRED_FILES = [
    "README.md",
    "PATCH_MANIFEST.md",
    "CAPABILITY_DELTA_SUMMARY.md",
    "ROUTING_DELTA_SUMMARY.md",
    "ANSWER_TEMPLATE_DELTA_SUMMARY.md",
    "ROUTING_METADATA_CONTRACT_SUMMARY.md",
    "VALIDATION_SUMMARY.md",
    "OVERLAY_INSTRUCTIONS.md",
    "SAFETY_BOUNDARIES.md",
    "PATCH_CHECKLIST.md",
]
RELEASE_TYPES = {
    "full_runtime_release": DEFAULT_REQUIRED_FILES,
    "focused_safe_summary_patch": FOCUSED_SAFE_SUMMARY_PATCH_REQUIRED_FILES,
}
MANIFEST_PATTERNS = ["*manifest*.md", "*manifest*.json", "*manifest*.yaml", "*manifest*.yml"]
EXPLICITLY_ALLOWED_HIGH_RULES: set[str] = set()


def load_scanner_result(target: Path) -> tuple[dict[str, Any] | None, str | None]:
    command = ["python3", str(SCANNER), str(target), "--json"]
    try:
        proc = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return None, f"scanner_execution_error:{type(exc).__name__}"

    if not proc.stdout.strip():
        return None, f"scanner_no_json_output:returncode={proc.returncode}"

    try:
        result = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return None, f"scanner_json_parse_error:returncode={proc.returncode}"

    result["_scanner_returncode"] = proc.returncode
    return result, None


def manifest_present(target: Path) -> bool:
    return any(target.glob(pattern) for pattern in MANIFEST_PATTERNS)


def check_required_files(target: Path, release_type: str) -> dict[str, Any]:
    required_files = RELEASE_TYPES[release_type]
    missing = [rel for rel in required_files if not (target / rel).is_file()]
    if release_type == "full_runtime_release":
        manifest_ok = manifest_present(target)
        if not manifest_ok:
            missing.append("<release_manifest: *manifest*.md|json|yaml|yml>")
    return {
        "release_type": release_type,
        "required_files_pass": not missing,
        "missing_required_files": missing,
    }


def summarize_findings(findings: list[dict[str, Any]]) -> dict[str, Any]:
    blocking = [item for item in findings if item.get("package_should_block")]
    high_unallowed = [
        item
        for item in findings
        if item.get("severity") == "high"
        and item.get("rule_name") not in EXPLICITLY_ALLOWED_HIGH_RULES
    ]
    rule_counts = Counter(str(item.get("rule_name", "unknown")) for item in blocking)
    category_counts = Counter(str(item.get("category", "unknown")) for item in blocking)
    return {
        "blocking_finding_count": len(blocking),
        "unallowed_high_count": len(high_unallowed),
        "blocking_rule_counts": dict(sorted(rule_counts.items())),
        "blocking_category_counts": dict(sorted(category_counts.items())),
    }


def build_safe_summary(
    target: Path,
    scanner_result: dict[str, Any],
    required: dict[str, Any],
) -> dict[str, Any]:
    summary = scanner_result.get("summary", {})
    finding_summary = summarize_findings(scanner_result.get("findings", []))
    package_should_block = bool(scanner_result.get("package_should_block"))
    scanner_returncode = int(scanner_result.get("_scanner_returncode", 0))
    critical = int(summary.get("critical", 0))
    high = int(summary.get("high", 0))
    unallowed_high = int(finding_summary["unallowed_high_count"])

    preflight_pass = (
        scanner_returncode == 0
        and not package_should_block
        and critical == 0
        and unallowed_high == 0
        and required["required_files_pass"]
    )

    return {
        "schema_version": "release_preflight_safe_summary_v1",
        "target": str(target),
        "release_type": required["release_type"],
        "preflight_pass": preflight_pass,
        "scanner_pass": scanner_returncode == 0 and not package_should_block and critical == 0 and unallowed_high == 0,
        "package_should_block": package_should_block,
        "scanner_status": scanner_result.get("status", "unknown"),
        "scanner_returncode": scanner_returncode,
        "scanner_summary": {
            "critical": critical,
            "high": high,
            "medium": int(summary.get("medium", 0)),
            "low": int(summary.get("low", 0)),
            "pass": int(summary.get("pass", 0)),
            "total_findings": int(summary.get("total_findings", 0)),
        },
        "required_files_pass": required["required_files_pass"],
        "missing_required_files": required["missing_required_files"],
        "explicitly_allowed_high_rules": sorted(EXPLICITLY_ALLOWED_HIGH_RULES),
        "finding_safe_summary": finding_summary,
        "output_policy": "safe_summary_only_no_raw_file_content",
    }


def print_summary(summary: dict[str, Any]) -> None:
    print(f"release_type={summary['release_type']}")
    print(f"release_preflight preflight_pass={str(summary['preflight_pass']).lower()}")
    print(f"scanner_pass={str(summary['scanner_pass']).lower()}")
    print(f"package_should_block={str(summary['package_should_block']).lower()}")
    scanner = summary["scanner_summary"]
    print(
        "scanner_summary "
        f"critical={scanner['critical']} high={scanner['high']} "
        f"medium={scanner['medium']} low={scanner['low']} total={scanner['total_findings']}"
    )
    print(f"required_files_pass={str(summary['required_files_pass']).lower()}")
    if summary["missing_required_files"]:
        print("missing_required_files=" + ",".join(summary["missing_required_files"]))
    finding_summary = summary["finding_safe_summary"]
    print(f"blocking_finding_count={finding_summary['blocking_finding_count']}")
    if finding_summary["blocking_rule_counts"]:
        print("blocking_rule_counts=" + json.dumps(finding_summary["blocking_rule_counts"], ensure_ascii=False, sort_keys=True))
    print(f"output_policy={summary['output_policy']}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run release package preflight checks.")
    parser.add_argument("target", help="Release directory to validate before packaging/upload.")
    parser.add_argument(
        "--release-type",
        "--package-type",
        choices=sorted(RELEASE_TYPES),
        default="full_runtime_release",
        help="Package type to validate. full_runtime_release checks runtime files; focused_safe_summary_patch checks summary patch files only.",
    )
    parser.add_argument("--json", action="store_true", help="Output safe summary JSON.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    target = Path(args.target).resolve()
    if not target.exists() or not target.is_dir():
        error_summary = {
            "schema_version": "release_preflight_safe_summary_v1",
            "target": str(target),
            "release_type": args.release_type,
            "preflight_pass": False,
            "scanner_pass": False,
            "package_should_block": True,
            "failure_reason": "target_directory_missing",
            "output_policy": "safe_summary_only_no_raw_file_content",
        }
        if args.json:
            print(json.dumps(error_summary, ensure_ascii=False, indent=2))
        else:
            print("release_preflight preflight_pass=false")
            print("package_should_block=true")
            print("failure_reason=target_directory_missing")
            print("output_policy=safe_summary_only_no_raw_file_content")
        return 1

    scanner_result, scanner_error = load_scanner_result(target)
    if scanner_error or scanner_result is None:
        error_summary = {
            "schema_version": "release_preflight_safe_summary_v1",
            "target": str(target),
            "release_type": args.release_type,
            "preflight_pass": False,
            "scanner_pass": False,
            "package_should_block": True,
            "failure_reason": scanner_error or "scanner_unknown_error",
            "output_policy": "safe_summary_only_no_raw_file_content",
        }
        if args.json:
            print(json.dumps(error_summary, ensure_ascii=False, indent=2))
        else:
            print("release_preflight preflight_pass=false")
            print("package_should_block=true")
            print(f"failure_reason={error_summary['failure_reason']}")
            print("output_policy=safe_summary_only_no_raw_file_content")
        return 1

    required = check_required_files(target, args.release_type)
    summary = build_safe_summary(target, scanner_result, required)
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print_summary(summary)
    return 0 if summary["preflight_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
