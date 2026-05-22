#!/usr/bin/env python3
"""Path-level semi-open release package asset scanner.

The scanner intentionally uses path and file-name rules only. It does not open
files that may be auth state, cookies, tokens, sessions, or raw observations.
It is a local packaging readiness helper, not a runtime enforcement layer.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
from pathlib import Path
from typing import Any


DEFAULT_RULES = Path(__file__).with_name("package_asset_scanner_rules.json")


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


def collect_paths(root: Path) -> list[str]:
    paths: list[str] = []
    for current_root, dirnames, filenames in os.walk(root):
        current = Path(current_root)
        for dirname in dirnames:
            paths.append(normalize_path(current / dirname, root) + "/")
        for filename in filenames:
            paths.append(normalize_path(current / filename, root))
    return sorted(paths)


def scan(root: Path, rules: dict[str, Any]) -> dict[str, Any]:
    allowlist = rules.get("allowlist", [])
    denylist = rules.get("denylist", [])
    aggregate_rules = rules.get("aggregate_rules", [])
    findings: list[dict[str, Any]] = []
    category_counts: dict[str, int] = {}

    for rel_path in collect_paths(root):
        allow_rule = match_any(rel_path, allowlist)
        deny_rule = match_any(rel_path, denylist)
        if not deny_rule:
            continue
        category = deny_rule.get("category", "unknown")
        category_counts[category] = category_counts.get(category, 0) + 1
        if allow_rule:
            findings.append(
                {
                    "severity": "pass",
                    "category": category,
                    "path": rel_path,
                    "reason": f"allowlisted: {allow_rule.get('reason', '')}",
                }
            )
            continue
        findings.append(
            {
                "severity": deny_rule.get("severity", "warning"),
                "category": category,
                "path": rel_path,
                "reason": deny_rule.get("reason", ""),
            }
        )

    for rule in aggregate_rules:
        category = rule["category"]
        count = category_counts.get(category, 0)
        max_count = int(rule["max_count"])
        if count > max_count:
            findings.append(
                {
                    "severity": rule.get("severity", "warning"),
                    "category": f"{category}_aggregate",
                    "path": "<aggregate>",
                    "reason": f"{rule.get('reason', '')} count={count} max={max_count}",
                }
            )

    fail_count = sum(1 for item in findings if item["severity"] == "fail")
    warning_count = sum(1 for item in findings if item["severity"] == "warning")
    pass_count = sum(1 for item in findings if item["severity"] == "pass")
    status = "fail" if fail_count else "warning" if warning_count else "pass"

    return {
        "schema_version": "package_asset_scan_result_v1",
        "target": str(root),
        "rules_version": rules.get("schema_version", "unknown"),
        "status": status,
        "summary": {
            "fail": fail_count,
            "warning": warning_count,
            "pass": pass_count,
            "total_findings": len(findings),
        },
        "category_counts": category_counts,
        "findings": findings,
        "scanner_boundary": {
            "path_level_only": True,
            "file_content_read": False,
            "auth_state_read": False,
            "real_platform_called": False,
            "dataagent_called": False,
        },
    }


def print_text(result: dict[str, Any]) -> None:
    print(f"package_asset_scan status={result['status']}")
    summary = result["summary"]
    print(
        f"findings fail={summary['fail']} warning={summary['warning']} "
        f"pass={summary['pass']} total={summary['total_findings']}"
    )
    for item in result["findings"]:
        print(
            f"[{item['severity']}] {item['category']} {item['path']} - {item['reason']}"
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
