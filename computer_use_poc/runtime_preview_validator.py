#!/usr/bin/env python3
"""Lightweight validator for runtime preview reports.

The validator checks local text only. It does not access platforms, DataAgent,
Hive, auth state, gateway config, or TOOLS.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


PASS = "PASS_EXPECTED_BEHAVIOR"
FAILED = "PREVIEW_FAILED_CONTRACT_VIOLATION"
BLOCKED_INSUFFICIENT = "PREVIEW_BLOCKED_INSUFFICIENT_CONTRACT"
BLOCKED_CONFLICT = "PREVIEW_BLOCKED_CONTRACT_CONFLICT"

REQUIRED_SECTIONS = [
    "route_decision",
    "execution_mode",
    "source_plan",
    "source_completion_matrix",
    "evidence_card",
    "source_quality",
    "routing_metadata",
    "expected_user_answer",
    "uncertainty_due_to_missing_runtime_info",
    "contract_compliance_check",
]

FORBIDDEN_PATTERNS = [
    {
        "name": "credential_plaintext_key",
        "pattern": r"(?i)\b(cookie|token|session|authorization|raw_header|raw_headers)\s*[:=]\s*[^,\s]+",
        "reason": "credential-like key/value output is forbidden",
    },
    {
        "name": "http_credential_header",
        "pattern": r"(?i)\b(Cookie|Authorization)\s*:\s*[^,\s]+",
        "reason": "raw HTTP credential header output is forbidden",
    },
    {
        "name": "no_data_as_no_risk",
        "pattern": r"(?i)no_data.{0,30}(?:therefore|=>|=|所以|因此).{0,30}(?:no risk|low risk|无风险|低风险|排除)",
        "reason": "no_data must not be used as no-risk evidence",
    },
    {
        "name": "platform_failure_as_no_risk",
        "pattern": r"(?i)(?:timeout|blocked|auth_failed|parse_error|tool_gap).{0,30}(?:therefore|=>|=|所以|因此).{0,30}(?:no risk|low risk|无风险|低风险|排除)",
        "reason": "source failure must not be used as no-risk evidence",
    },
    {
        "name": "strategy_hit_as_final_ato_judgement",
        "pattern": r"(?i)(?:strategy_hit|策略命中).{0,40}(?:final|最终|直接|即可|therefore|所以).{0,40}(?:ATO|盗号|作弊|风险)",
        "reason": "strategy hit alone is not a final ATO or cheating judgement",
    },
    {
        "name": "partial_as_final",
        "pattern": r"(?i)(?:final_status\s*:\s*final|最终结论).{0,80}(?:partial|timeout|blocked|auth_failed|tool_gap)",
        "reason": "partial evidence must not be wrapped as final",
    },
    {
        "name": "mock_as_real_query",
        "pattern": r"(?i)(?:mock|模拟|preview).{0,40}(?:real query|真实查询已完成|平台查询完成)",
        "reason": "mock or preview cannot be presented as a real platform query",
    },
    {
        "name": "main_agent_direct_platform_query",
        "pattern": r"(?i)(?:direct_tool_bypass\s*:\s*true|main agent direct platform query|main_agent.*直接查平台)",
        "reason": "main agent must not directly query platforms",
    },
    {
        "name": "batch_or_expansion_misrouted_to_execution",
        "pattern": r"(?i)(?:批量|举一返三|expansion|batch).{0,80}(?:single_entity_execution_mode|逐个在线查|per-user live execution)",
        "reason": "batch or expansion requests must not silently become per-entity execution",
    },
    {
        "name": "stale_data_as_realtime",
        "pattern": r"(?i)(?:stale|历史缓存|旧 observation).{0,40}(?:realtime|实时|no-cache)",
        "reason": "stale data must not be presented as realtime",
    },
    {
        "name": "forbidden_path_accessed",
        "pattern": r"(?i)(?:accessed|read|已读取|读取了|引用了|使用了).{0,30}(?:run_logs|\.ks_sso|TOOLS\.md|old outputs|历史 outputs)",
        "reason": "preview must not read forbidden local paths",
    },
    {
        "name": "auth_debug_or_manual_cookie",
        "pattern": r"(?i)(?:debugged auth|auth debug executed|执行.*auth.*debug|手拼.*cookie|manual_cookie\s*:\s*true|arbitrary_url\s*:\s*true)",
        "reason": "source failure must not trigger auth debug, manual cookie, or arbitrary URL probing",
    },
]


def section_present(text: str, section: str) -> bool:
    pattern = rf"(?im)^\s*(?:#{{1,6}}\s*)?{re.escape(section)}\b\s*:?"
    return re.search(pattern, text) is not None


def find_missing_sections(text: str) -> list[str]:
    return [section for section in REQUIRED_SECTIONS if not section_present(text, section)]


def find_forbidden_behaviors(text: str) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for item in FORBIDDEN_PATTERNS:
        match = re.search(item["pattern"], text)
        if match:
            findings.append(
                {
                    "check": item["name"],
                    "reason": item["reason"],
                    "matched_text": match.group(0)[:160],
                }
            )
    return findings


def validate_report(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {
            "status": BLOCKED_INSUFFICIENT,
            "findings": [
                {
                    "check": "report_exists",
                    "reason": f"report not found: {path}",
                }
            ],
        }

    text = path.read_text(encoding="utf-8", errors="replace")
    missing_sections = find_missing_sections(text)
    forbidden_findings = find_forbidden_behaviors(text)
    findings: list[dict[str, Any]] = []

    if missing_sections:
        findings.append(
            {
                "check": "required_sections",
                "reason": "missing required preview sections",
                "missing_sections": missing_sections,
            }
        )
    findings.extend(forbidden_findings)

    if BLOCKED_CONFLICT in text:
        status = BLOCKED_CONFLICT
    elif BLOCKED_INSUFFICIENT in text and not forbidden_findings:
        status = BLOCKED_INSUFFICIENT
    elif findings:
        status = FAILED
    else:
        status = PASS

    return {
        "status": status,
        "findings": findings,
        "required_sections_checked": REQUIRED_SECTIONS,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a runtime preview report.")
    parser.add_argument("--report", required=True, help="Path to outputs/local_preview/preview_report.md")
    args = parser.parse_args()

    result = validate_report(Path(args.report))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] in {PASS, BLOCKED_INSUFFICIENT, BLOCKED_CONFLICT} else 1


if __name__ == "__main__":
    raise SystemExit(main())
