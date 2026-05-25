#!/usr/bin/env python3
"""Semi-open release package asset scanner.

The scanner is a local packaging readiness helper. It applies path rules first
and then performs bounded content checks on ordinary text files. It does not
read files that are already path-blocked as auth state or credential material.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
from pathlib import Path
from typing import Any


DEFAULT_RULES = Path(__file__).with_name("package_asset_scanner_rules.json")
BLOCKING_SEVERITIES = {"critical", "high", "fail"}
TEXT_EXTENSIONS = {
    ".csv",
    ".json",
    ".jsonl",
    ".md",
    ".py",
    ".txt",
    ".yaml",
    ".yml",
}
PATH_BLOCK_CONTENT_SKIP_CATEGORIES = {"auth-state", "credential_material"}


def normalize_path(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def load_rules(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def match_any(rel_path: str, rules: list[dict[str, Any]]) -> dict[str, Any] | None:
    for rule in rules:
        pattern = rule["pattern"]
        if fnmatch.fnmatch(rel_path, pattern) or fnmatch.fnmatch("/" + rel_path, pattern):
            return rule
    return None


def collect_paths(root: Path) -> list[tuple[str, bool]]:
    paths: list[tuple[str, bool]] = []
    for current_root, dirnames, filenames in os.walk(root):
        current = Path(current_root)
        for dirname in dirnames:
            paths.append((normalize_path(current / dirname, root) + "/", True))
        for filename in filenames:
            paths.append((normalize_path(current / filename, root), False))
    return sorted(paths)


def is_blocking(severity: str) -> bool:
    return severity in BLOCKING_SEVERITIES


def normalized_status_severity(severity: str) -> str:
    if severity == "fail":
        return "critical"
    if severity == "warning":
        return "medium"
    return severity


def make_finding(
    *,
    rule: dict[str, Any],
    rel_path: str,
    match_type: str,
    matched_text: str | None = None,
    line_number: int | None = None,
) -> dict[str, Any]:
    severity = normalized_status_severity(rule.get("severity", "medium"))
    finding: dict[str, Any] = {
        "severity": severity,
        "rule_name": rule.get("name", rule.get("category", "unnamed_rule")),
        "category": rule.get("category", "unknown"),
        "path": rel_path,
        "match_type": match_type,
        "reason": rule.get("reason", ""),
        "recommendation": rule.get("recommendation", "Remove, redact, or replace this asset before packaging."),
        "package_should_block": is_blocking(severity),
    }
    if line_number is not None:
        finding["line_number"] = line_number
    if matched_text is not None:
        finding["matched_text"] = matched_text[:160]
    return finding


def should_scan_content(
    full_path: Path,
    rel_path: str,
    path_deny_rule: dict[str, Any] | None,
    rules: dict[str, Any],
) -> bool:
    if path_deny_rule and path_deny_rule.get("category") in PATH_BLOCK_CONTENT_SKIP_CATEGORIES:
        return False
    if any(fnmatch.fnmatch(rel_path, pattern) for pattern in rules.get("content_scan_exclude", [])):
        return False
    max_bytes = int(rules.get("content_scan_max_bytes", 2_000_000))
    try:
        if full_path.stat().st_size > max_bytes:
            return False
    except OSError:
        return False
    extensions = set(rules.get("content_scan_extensions", sorted(TEXT_EXTENSIONS)))
    if full_path.suffix.lower() in extensions:
        return True
    return any(fnmatch.fnmatch(rel_path, pattern) for pattern in rules.get("content_scan_path_allowlist", []))


def scan_file_content(full_path: Path, rel_path: str, rules: dict[str, Any]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    content_rules = rules.get("content_denylist", [])
    if not content_rules:
        return findings
    try:
        text = full_path.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        findings.append(
            {
                "severity": "low",
                "rule_name": "content_read_error",
                "category": "scanner_error",
                "path": rel_path,
                "match_type": "content_read",
                "reason": f"Could not read file for content scan: {exc}",
                "recommendation": "Review the file manually before packaging.",
                "package_should_block": False,
            }
        )
        return findings

    lines = text.splitlines()
    for rule in content_rules:
        pattern = re.compile(rule["pattern"], re.IGNORECASE)
        for idx, line in enumerate(lines, start=1):
            match = pattern.search(line)
            if not match:
                continue
            findings.append(
                make_finding(
                    rule=rule,
                    rel_path=rel_path,
                    match_type="content",
                    matched_text=match.group(0),
                    line_number=idx,
                )
            )
            break
    return findings


def scan(root: Path, rules: dict[str, Any]) -> dict[str, Any]:
    allowlist = rules.get("allowlist", [])
    denylist = rules.get("denylist", [])
    aggregate_rules = rules.get("aggregate_rules", [])
    findings: list[dict[str, Any]] = []
    category_counts: dict[str, int] = {}

    for rel_path, is_dir in collect_paths(root):
        allow_rule = match_any(rel_path, allowlist)
        deny_rule = match_any(rel_path, denylist)
        if deny_rule:
            category = deny_rule.get("category", "unknown")
            category_counts[category] = category_counts.get(category, 0) + 1
            if allow_rule:
                findings.append(
                    {
                        "severity": "pass",
                        "rule_name": allow_rule.get("name", "allowlist"),
                        "category": category,
                        "path": rel_path,
                        "match_type": "path",
                        "reason": f"allowlisted: {allow_rule.get('reason', '')}",
                        "recommendation": "No action required if the allowlist remains intentional.",
                        "package_should_block": False,
                    }
                )
            else:
                findings.append(make_finding(rule=deny_rule, rel_path=rel_path, match_type="path"))

        if not is_dir:
            full_path = root / rel_path
            if should_scan_content(full_path, rel_path, None if allow_rule else deny_rule, rules):
                findings.extend(scan_file_content(full_path, rel_path, rules))

    for rule in aggregate_rules:
        category = rule["category"]
        count = category_counts.get(category, 0)
        max_count = int(rule["max_count"])
        if count > max_count:
            findings.append(
                {
                    "severity": normalized_status_severity(rule.get("severity", "medium")),
                    "rule_name": rule.get("name", f"{category}_aggregate"),
                    "category": f"{category}_aggregate",
                    "path": "<aggregate>",
                    "match_type": "aggregate",
                    "reason": f"{rule.get('reason', '')} count={count} max={max_count}",
                    "recommendation": rule.get("recommendation", "Remove extra files or replace them with a release-safe summary."),
                    "package_should_block": is_blocking(normalized_status_severity(rule.get("severity", "medium"))),
                }
            )

    critical_count = sum(1 for item in findings if item["severity"] == "critical")
    high_count = sum(1 for item in findings if item["severity"] == "high")
    medium_count = sum(1 for item in findings if item["severity"] == "medium")
    low_count = sum(1 for item in findings if item["severity"] == "low")
    pass_count = sum(1 for item in findings if item["severity"] == "pass")
    package_should_block = any(item.get("package_should_block") for item in findings)
    status = "fail" if package_should_block else "warning" if (medium_count or low_count) else "pass"

    return {
        "schema_version": "package_asset_scan_result_v2",
        "target": str(root),
        "rules_version": rules.get("schema_version", "unknown"),
        "status": status,
        "package_should_block": package_should_block,
        "summary": {
            "critical": critical_count,
            "high": high_count,
            "medium": medium_count,
            "low": low_count,
            "pass": pass_count,
            "fail": critical_count + high_count,
            "warning": medium_count + low_count,
            "total_findings": len(findings),
        },
        "category_counts": category_counts,
        "findings": findings,
        "scanner_boundary": {
            "path_level_only": False,
            "bounded_content_scan": True,
            "file_content_read": True,
            "auth-state_read": False,
            "real_platform_called": False,
            "dataagent_called": False,
        },
    }


def print_text(result: dict[str, Any]) -> None:
    print(f"package_asset_scan status={result['status']} package_should_block={str(result['package_should_block']).lower()}")
    summary = result["summary"]
    print(
        f"findings critical={summary['critical']} high={summary['high']} "
        f"medium={summary['medium']} low={summary['low']} pass={summary['pass']} "
        f"total={summary['total_findings']}"
    )
    for item in result["findings"]:
        print(
            f"[{item['severity']}] {item.get('rule_name', item['category'])} "
            f"{item['path']} - {item['reason']} recommendation={item.get('recommendation', '')}"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scan a release directory for high-risk assets.")
    parser.add_argument("target", help="Release directory or staging directory to scan.")
    parser.add_argument("--rules", default=str(DEFAULT_RULES), help="Rules JSON path.")
    parser.add_argument("--json", action="store_true", help="Output JSON instead of text.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    target = Path(args.target).resolve()
    if not target.exists() or not target.is_dir():
        raise SystemExit(f"target must be an existing directory: {target}")
    rules = load_rules(Path(args.rules))
    result = scan(target, rules)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print_text(result)
    return 1 if result["status"] == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())
