#!/usr/bin/env python3
"""
dataagent_population_client.py v0.2

Minimal DataAgent Conversational API client for population baseline sampling.

Changes from v0.1:
  - Content extraction: step.data.stepData.componentInfo.props.content (primary path)
  - Fallback: step.data.stepData.content
  - Aggregation of multiple MODEL_ANSWER content fragments
  - ConnectionResetError: max 1 retry
  - timeout default 300s
  - Table visibility check subcommand (--action check-table)
  - dataagent_date_context_mismatch detection
  - table_not_found / permission_denied / metadata_not_indexed classification

Boundary:
  DataAgent 只取数不分析
  不输出 risk_judgement / feature_candidate / candidate_feature_decision
  不改 runtime / outputs / git
  不改 SSO/auth
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

# ── Config ──────────────────────────────────────────────────────────

DEFAULT_TIMEOUT = 300
MAX_RETRIES = 1
RETRY_DELAY = 3

ENV_FILE = Path.home() / ".dennis-agent" / "dataagent.env"
REQUIRED_ENV_KEYS = [
    "DATAAGENT_BASE_URL",
    "DATAAGENT_ENDPOINT_PATH",
    "DATAAGENT_USER_ID",
    "DATAAGENT_X_FORWARDED_USER",
]

POPULATION_TABLES = [
    "ks_raw_log_v3.infra_user_action_log",
    "ks_raw_log_v3.passport_action_log",
    "ks_rc_bs.weapon_data_report_device_log_kafka_2_hive_android_di_v2",
    "ks_rc_bs.weapon_data_report_device_log_kafka_2_hive_IOS_di_v2",
]

FORBIDDEN_OUTPUT_KEYS = [
    "risk_judgement", "feature_candidate", "candidate_feature_decision",
]

# ── Env Loading ─────────────────────────────────────────────────────

def load_env() -> dict[str, str]:
    """Load non-sensitive DataAgent env from ~/.dennis-agent/dataagent.env."""
    env = {}
    if ENV_FILE.exists():
        with open(ENV_FILE) as f:
            for line in f:
                line = line.strip()
                if line.startswith("export ") and "=" in line:
                    key, val = line[7:].split("=", 1)
                    val = val.strip('"').strip("'")
                    env[key] = val
    missing = [k for k in REQUIRED_ENV_KEYS if k not in env]
    if missing:
        raise RuntimeError(
            "Missing DataAgent env keys: %s. Run: source %s"
            % (missing, ENV_FILE)
        )
    return env


# ── DataAgent POST ──────────────────────────────────────────────────

def dataagent_post(
    payload: dict[str, Any],
    timeout: int = DEFAULT_TIMEOUT,
    max_retries: int = MAX_RETRIES,
) -> dict[str, Any]:
    """POST to DataAgent Conversational API with retry on ConnectionResetError."""
    env = load_env()
    base_url = env["DATAAGENT_BASE_URL"]
    endpoint_path = env["DATAAGENT_ENDPOINT_PATH"]
    url = base_url + endpoint_path
    user_id = env.get("DATAAGENT_X_FORWARDED_USER", env.get("DATAAGENT_USER_ID", ""))

    data = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "X-Forwarded-User": user_id,
    }
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")

    attempts = 0
    while attempts <= max_retries:
        attempts += 1
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = resp.read().decode("utf-8")
                parsed = json.loads(body)
                return parsed
        except ConnectionResetError:
            if attempts <= max_retries:
                print("  ConnectionResetError on attempt %d, retrying after %ds..." % (attempts, RETRY_DELAY))
                time.sleep(RETRY_DELAY)
                continue
            else:
                raise RuntimeError(
                    "DataAgent POST failed after %d attempts: ConnectionResetError" % attempts
                )
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")[:500]
            if e.code == 401:
                raise RuntimeError("DataAgent auth failure: HTTP %d" % e.code)
            elif e.code == 403:
                raise RuntimeError("DataAgent permission failure: HTTP %d %s" % (e.code, error_body[:200]))
            else:
                raise RuntimeError("DataAgent HTTP error: %d %s" % (e.code, e.reason))
        except TimeoutError:
            raise RuntimeError(
                "DataAgent POST timeout after %ds (payload may need simpler query)" % timeout
            )
    raise RuntimeError("DataAgent POST exhausted retries")


# ── Step Parsing ────────────────────────────────────────────────────

def _extract_step_content(inner_sd: dict) -> str:
    """Extract text content from a step's stepData.

    Primary path: stepData.componentInfo.props.content
    Fallback: stepData.content
    """
    # Primary path
    ci = inner_sd.get("componentInfo", {})
    if isinstance(ci, dict):
        props = ci.get("props", {})
        if isinstance(props, dict):
            content = props.get("content", "")
            if content:
                return content

    # Fallback path
    content = inner_sd.get("content", "")
    return content


def parse_steps(response: dict[str, Any]) -> dict[str, Any]:
    """Parse DataAgent step-based response structure.

    Returns a summary dict with:
      - result, step_count, step_types
      - model_answer: concatenated MODEL_ANSWER content fragments
      - model_answer_length, tool_calls, query_ids
      - has_data_result, has_agent_end
    """
    top_result = response.get("result")
    data_section = response.get("data", {})
    steps = data_section.get("steps", [])

    step_types = []
    model_answer_parts = []
    tool_calls = []
    query_ids = []
    has_data_result = False
    has_agent_end = False

    for step in steps:
        step_data = step.get("data", {})
        inner_sd = step_data.get("stepData", {})
        sub_type = inner_sd.get("subType", "")

        step_types.append(sub_type)
        content = _extract_step_content(inner_sd)

        if sub_type == "MODEL_ANSWER":
            if content:
                model_answer_parts.append(content)

        elif sub_type == "TOOL_CALL":
            ci = inner_sd.get("componentInfo", {})
            tc = inner_sd.get("toolCall", {})
            if not tc and isinstance(ci, dict):
                tc = ci.get("toolCall", {})
            qid = inner_sd.get("queryId") or step_data.get("queryId")
            tc_info = {
                "function": tc.get("function", "") if isinstance(tc, dict) else "",
                "has_arguments": bool(tc.get("arguments", "")) if isinstance(tc, dict) else False,
            }
            if qid:
                tc_info["queryId"] = qid
                query_ids.append(qid)
            # Also extract TOOL_CALL content (may contain SQL)
            if content:
                tc_info["content_preview"] = content[:100]
            tool_calls.append(tc_info)

        elif sub_type == "DATA_RESULT":
            has_data_result = True

        elif sub_type == "AGENT_END":
            has_agent_end = True

    return {
        "result": top_result,
        "step_count": len(steps),
        "step_types": step_types,
        "model_answer": "\n\n".join(model_answer_parts) if model_answer_parts else "",
        "model_answer_length": sum(len(p) for p in model_answer_parts),
        "tool_calls": tool_calls,
        "query_ids": query_ids,
        "has_data_result": has_data_result,
        "has_agent_end": has_agent_end,
    }


# ── Table Visibility Classification ────────────────────────────────

TABLE_NOT_FOUND_PATTERNS = [
    re.compile(r"不存在|not\s*exist|not\s*found|no\s*such|未找到|找不到", re.IGNORECASE),
]

PERMISSION_DENIED_PATTERNS = [
    re.compile(r"权限|permission|denied|authorized|unauthorized|无权限|没有权限|access\s*denied", re.IGNORECASE),
]

METADATA_NOT_INDEXED_PATTERNS = [
    re.compile(r"元数据|metadata|未索引|not\s*indexed|搜索未命中|搜索也没有", re.IGNORECASE),
]

PARTITION_NOT_FOUND_PATTERNS = [
    re.compile(r"分区.*不存在|partition.*not\s*exist|分区.*没有|partition.*not\s*found", re.IGNORECASE),
]

FUTURE_DATE_PATTERNS = [
    re.compile(r"未来日期|future\s*date|尚未产出|not\s*yet|还没.*产生|data\s*not\s*produced", re.IGNORECASE),
]


def classify_table_visibility(model_answer: str) -> dict[str, Any]:
    """Classify the table visibility status from MODEL_ANSWER content.

    Returns:
      visibility_status: table_not_found / permission_denied / metadata_not_indexed /
                         partition_not_found / visible / unknown
      date_context_mismatch: true if DataAgent claims date is future when it shouldn't be
      evidence: relevant text snippets
    """
    if not model_answer:
        return {
            "visibility_status": "unknown",
            "date_context_mismatch": None,
            "evidence": "no_model_answer_content",
        }

    # Check patterns in order of specificity
    for pattern in PERMISSION_DENIED_PATTERNS:
        if pattern.search(model_answer):
            return {
                "visibility_status": "permission_denied",
                "date_context_mismatch": False,
                "evidence": _extract_evidence(model_answer, pattern),
            }

    for pattern in TABLE_NOT_FOUND_PATTERNS:
        if pattern.search(model_answer):
            # Check if it's actually partition_not_found
            for ptn in PARTITION_NOT_FOUND_PATTERNS:
                if ptn.search(model_answer):
                    # Check if DataAgent incorrectly claims date is future
                    is_future_date = any(p.search(model_answer) for p in FUTURE_DATE_PATTERNS)
                    return {
                        "visibility_status": "partition_not_found",
                        "date_context_mismatch": is_future_date,
                        "evidence": _extract_evidence(model_answer, ptn),
                    }
            return {
                "visibility_status": "table_not_found",
                "date_context_mismatch": False,
                "evidence": _extract_evidence(model_answer, pattern),
            }

    for pattern in METADATA_NOT_INDEXED_PATTERNS:
        if pattern.search(model_answer):
            return {
                "visibility_status": "metadata_not_indexed",
                "date_context_mismatch": False,
                "evidence": _extract_evidence(model_answer, pattern),
            }

    # If no error patterns found, assume table is visible
    # (but check for data result indicators)
    data_keywords = ["查询结果", "数据", "rows", "records", "返回了"]
    has_data_keyword = any(k in model_answer for k in data_keywords)
    if has_data_keyword:
        return {
            "visibility_status": "visible",
            "date_context_mismatch": False,
            "evidence": "model_answer_contains_data_keywords",
        }

    return {
        "visibility_status": "unknown",
        "date_context_mismatch": None,
        "evidence": "no_specific_pattern_matched",
    }


def _extract_evidence(text: str, pattern: re.Pattern) -> str:
    """Extract the line(s) containing the matching pattern."""
    lines = text.split("\n")
    evidence_lines = [l.strip() for l in lines if pattern.search(l)]
    return evidence_lines[0][:100] if evidence_lines else "pattern_found_but_no_line_match"


# ── Query Builders ──────────────────────────────────────────────────

def build_limit1_query(table: str, p_date: str) -> dict[str, Any]:
    """Build LIMIT 1 verification payload."""
    env = load_env()
    user_id = env.get("DATAAGENT_X_FORWARDED_USER", env.get("DATAAGENT_USER_ID", ""))
    return {
        "messages": [
            {
                "role": "system",
                "content": "DataAgent readonly. 只取数不分析。不计算TOP-N。不计算低熵。不解释字段语义。不输出风险判断。不输出feature_candidate。这是population baseline抽样验证，LIMIT 1。"
            },
            {
                "role": "user",
                "content": "请执行: SELECT * FROM %s WHERE p_date = '%s' LIMIT 1" % (table, p_date)
            }
        ],
        "stream": False,
        "session_id": "nb_limit1_%s_%d" % (table.replace(".", "_")[-30:], int(time.time())),
        "user_id": user_id,
    }


def build_table_check_query(table: str) -> dict[str, Any]:
    """Build table visibility check payload (no data query, just metadata)."""
    env = load_env()
    user_id = env.get("DATAAGENT_X_FORWARDED_USER", env.get("DATAAGENT_USER_ID", ""))
    db, tbl = table.split(".", 1) if "." in table else ("unknown", table)
    return {
        "messages": [
            {
                "role": "system",
                "content": "DataAgent readonly. 只检查元数据可见性。不查询数据。不输出风险判断。不输出feature_candidate。"
            },
            {
                "role": "user",
                "content": "请确认以下表在 Hive 元数据中是否可见: %s.%s 。只返回表是否存在、库名是否正确。如果表不可见，请说明是权限问题、表名不存在、还是元数据未索引。不要执行 SELECT 查询。" % (db, tbl)
            }
        ],
        "stream": False,
        "session_id": "nb_tblchk_%s_%d" % (tbl[:20], int(time.time())),
        "user_id": user_id,
    }


# ── CLI ─────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="DataAgent population baseline client v0.2")
    parser.add_argument("--action", choices=["limit1", "check-table", "check-all-tables"],
                        default="limit1",
                        help="Action: limit1 (LIMIT 1 query), check-table (metadata visibility), check-all-tables (4 target tables)")
    parser.add_argument("--table", default="ks_raw_log_v3.infra_user_action_log",
                        help="Hive table to query")
    parser.add_argument("--p-date", default="20260609",
                        help="Partition date")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT,
                        help="HTTP timeout in seconds (default: 300)")
    parser.add_argument("--output", default="/tmp/dataagent_result.json",
                        help="Output JSON path")
    args = parser.parse_args()

    print("DataAgent population baseline client v0.2")
    print("  action: %s" % args.action)
    print("  table: %s" % args.table)
    print("  p_date: %s" % args.p_date)
    print("  timeout: %ds" % args.timeout)

    if args.action == "check-all-tables":
        # Check all 4 target tables sequentially
        results = {}
        for table in POPULATION_TABLES:
            print("\n--- Checking table: %s ---" % table)
            payload = build_table_check_query(table)
            try:
                response = dataagent_post(payload, timeout=args.timeout)
                parsed = parse_steps(response)
                visibility = classify_table_visibility(parsed.get("model_answer", ""))
                parsed["table_visibility"] = visibility
                parsed["post_success"] = True
                parsed["table"] = table
                print("  POST: OK, steps=%d, visibility=%s, date_mismatch=%s" % (
                    parsed["step_count"],
                    visibility["visibility_status"],
                    visibility.get("date_context_mismatch"),
                ))
                if parsed.get("model_answer"):
                    print("  Answer preview: %s" % parsed["model_answer"][:200])
                results[table] = parsed
            except RuntimeError as e:
                results[table] = {
                    "post_success": False,
                    "error": str(e)[:200],
                    "table": table,
                    "table_visibility": {"visibility_status": "dataagent_post_failed", "date_context_mismatch": None},
                }
                print("  POST failed: %s" % str(e)[:100])

            # Small delay between requests to avoid ConnectionResetError
            time.sleep(2)

        # Summary
        print("\n\n=== Table Visibility Summary ===")
        for table in POPULATION_TABLES:
            r = results[table]
            vis = r.get("table_visibility", {})
            print("  %s: visibility=%s, date_mismatch=%s" % (
                table, vis.get("visibility_status"), vis.get("date_context_mismatch")
            ))

        # Save
        with open(args.output, "w") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print("\nSaved to: %s" % args.output)

    elif args.action == "check-table":
        payload = build_table_check_query(args.table)
        print("\n  Sending table visibility check...")
        try:
            response = dataagent_post(payload, timeout=args.timeout)
            parsed = parse_steps(response)
            visibility = classify_table_visibility(parsed.get("model_answer", ""))
            parsed["table_visibility"] = visibility
            parsed["post_success"] = True
            parsed["table"] = args.table

            print("  POST succeeded: HTTP 200")
            print("  Steps: %d" % parsed["step_count"])
            print("  Step types: %s" % parsed["step_types"])
            print("  MODEL_ANSWER length: %d" % parsed["model_answer_length"])
            print("  Visibility: %s" % visibility["visibility_status"])
            print("  Date context mismatch: %s" % visibility.get("date_context_mismatch"))
            if parsed.get("model_answer"):
                print("  Answer preview: %s" % parsed["model_answer"][:300])
            print("  Tool calls: %d" % len(parsed["tool_calls"]))
            print("  Query IDs: %s" % parsed["query_ids"])
            print("  AGENT_END: %s" % parsed["has_agent_end"])

        except RuntimeError as e:
            parsed = {
                "post_success": False,
                "error": str(e)[:200],
                "table": args.table,
                "table_visibility": {"visibility_status": "dataagent_post_failed", "date_context_mismatch": None},
            }
            print("  POST failed: %s" % str(e)[:100])

        with open(args.output, "w") as f:
            json.dump(parsed, f, ensure_ascii=False, indent=2)
        print("\nSaved to: %s" % args.output)

    elif args.action == "limit1":
        payload = build_limit1_query(args.table, args.p_date)
        print("\n  Sending LIMIT 1 query...")
        try:
            response = dataagent_post(payload, timeout=args.timeout)
            parsed = parse_steps(response)
            visibility = classify_table_visibility(parsed.get("model_answer", ""))
            parsed["table_visibility"] = visibility
            parsed["post_success"] = True
            parsed["table"] = args.table
            parsed["p_date"] = args.p_date
            parsed["timeout_used"] = args.timeout

            print("  POST succeeded: HTTP 200")
            print("  Steps: %d" % parsed["step_count"])
            print("  Step types: %s" % parsed["step_types"])
            print("  MODEL_ANSWER length: %d" % parsed["model_answer_length"])
            print("  Tool calls: %d" % len(parsed["tool_calls"]))
            print("  Query IDs: %s" % parsed["query_ids"])
            print("  DATA_RESULT: %s" % parsed["has_data_result"])
            print("  AGENT_END: %s" % parsed["has_agent_end"])
            print("  Visibility: %s" % visibility["visibility_status"])
            print("  Date context mismatch: %s" % visibility.get("date_context_mismatch"))
            if parsed.get("model_answer"):
                print("\n  === MODEL_ANSWER Preview (first 300 chars) ===")
                print(parsed["model_answer"][:300])

        except RuntimeError as e:
            parsed = {
                "post_success": False,
                "error": str(e)[:200],
                "table": args.table,
                "p_date": args.p_date,
            }
            print("  POST failed: %s" % str(e)[:100])

        with open(args.output, "w") as f:
            json.dump(parsed, f, ensure_ascii=False, indent=2)
        print("\nSaved to: %s" % args.output)


if __name__ == "__main__":
    main()