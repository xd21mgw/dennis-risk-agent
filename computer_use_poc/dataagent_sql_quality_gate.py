#!/usr/bin/env python3
"""Local SQL quality gate for DataAgent dry-run output.

This module never executes SQL and never calls Hive or DataAgent. It only
checks a generated SQL string against the Dennis dry-run execution boundary.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from typing import Any


MAX_DEFAULT_ROWS = 1000

ALLOWED_TABLES = {
    "ks_rc_bs.dwd_risk_usr_accnt_login_orign_info",
    "ks_rc_bs.ks_account_login_basic_info",
    "ks_rc_bs.account_security_basic_info",
    "kscdm.dim_ks_user_all",
    "ks_rc_bs.fake_account_tag_all_detail_snapshot",
    "ks_rc_bs.fake_account_tag_all_summary_snapshot",
    "ks_rc_bs.fake_account_tag_di",
    "ks_rc_bs.fake_account_tag_online_detail",
    "ks_rc_bs.fake_account_tag_offline_detail",
    "ks_rc_bs.fake_account_high_recall_snapshot",
    "ks_rc_arch.antispam_feature_map_default_partitioned",
    "ks_raw_log_v2.antispam_feature_map_partitioned",
}

TABLE_REQUIRED_PARTITION_FIELDS = {table: {"p_date"} for table in ALLOWED_TABLES}

PARTITION_FIELDS = {"p_date", "p_hourmin", "dt", "date"}

RISK_ENTITY_IDENTIFIER_FIELDS = {
    "uid",
    "user_id",
    "userid",
    "did",
    "device_id",
    "deviceid",
    "deviceceid",
    "source_ip",
    "sourceip",
    "user_ip",
    "userip",
    "server_ip",
    "serverip",
    "ip",
    "event_id",
    "eventid",
    "source_id",
    "sourceid",
    "strategy_id",
    "strategyid",
    "policy_code",
    "policycode",
    "hit_policies",
    "hitfusepolicycode",
    "logsource",
    "log_source",
    "method",
    "timestamp",
    "op_time",
    "time",
    "occur_time",
    "_occurtime",
    "login_type",
    "action_type",
    "p_action_type",
    "code",
    "punish",
    "finalloginresult",
    "product",
    "client",
    "app_version",
    "appversion",
    "ua",
    "user_agent",
    "device_model",
    "device_type",
    "token_id",
    "tokenid",
}

SAFE_ANALYSIS_FIELDS = {
    "fake_account_tag",
    "cnt",
    "count",
    "total",
    "success_count",
    "failure_count",
    "risk_tag",
    "risk_label",
    "risk_score",
    "status",
    "reason",
    "result",
    "register_time",
    "create_time",
    "update_time",
    "carrier",
    "asn",
    "city",
    "province",
    "country",
    "geo",
}

PII_STRICT_FIELDS = {
    "phone",
    "phone_number",
    "mobile",
    "email",
    "id_card",
    "idcard",
    "identity_card",
    "real_name",
    "realname",
    "name",
    "nickname",
}

CREDENTIAL_SECRET_FIELDS = {
    "cookie",
    "cookies",
    "session",
    "session_id",
    "sessionid",
    "header",
    "headers",
    "authorization",
    "auth",
    "auth_token",
    "authtoken",
    "access_token",
    "accesstoken",
    "refresh_token",
    "refreshtoken",
    "token",
    "password",
    "passwd",
    "pwd",
    "secret",
    "salt",
    "ticket",
    "storage_state",
    "storagestate",
}

SQL_KEYWORDS = {
    "all",
    "and",
    "as",
    "asc",
    "between",
    "by",
    "case",
    "cast",
    "desc",
    "distinct",
    "else",
    "end",
    "false",
    "from",
    "full",
    "group",
    "having",
    "in",
    "inner",
    "is",
    "join",
    "left",
    "like",
    "limit",
    "not",
    "null",
    "on",
    "or",
    "order",
    "outer",
    "right",
    "select",
    "then",
    "true",
    "union",
    "when",
    "where",
    "with",
}

SQL_FUNCTIONS = {
    "avg",
    "coalesce",
    "concat",
    "count",
    "date_format",
    "from_unixtime",
    "if",
    "max",
    "min",
    "nvl",
    "sum",
    "substr",
    "substring",
}

WRITE_OPERATION_RE = re.compile(
    r"\b(insert|update|delete|drop|create|alter|truncate|merge|overwrite|load\s+data)\b",
    re.IGNORECASE,
)
TABLE_RE = re.compile(r"\b[a-zA-Z_][\w]*\.[a-zA-Z_][\w]*(?:\.[a-zA-Z_][\w]*)?\b")
IDENTIFIER_RE = re.compile(r"\b[a-zA-Z_][\w]*\b")
LIMIT_RE = re.compile(r"\blimit\s+(\d+)\b", re.IGNORECASE)
STRING_LITERAL_RE = re.compile(r"'(?:''|[^'])*'|\"(?:\"\"|[^\"])*\"")
ALIAS_RE = re.compile(r"\bas\s+([a-zA-Z_][\w]*)\b", re.IGNORECASE)
TABLE_ALIAS_RE = re.compile(
    r"\b(?:from|join)\s+[a-zA-Z_][\w]*\.[a-zA-Z_][\w]*(?:\.[a-zA-Z_][\w]*)?\s+([a-zA-Z_][\w]*)\b",
    re.IGNORECASE,
)
CAVEAT_LINE_RE = re.compile(
    r"(caveat|table\s+not\s+found|metadata\s+catalog|verify\s+table|partition\s+column|"
    r"unknown\s+table|cannot\s+verify|could\s+not\s+verify|表不存在|元数据|分区字段|确认表)",
    re.IGNORECASE,
)
BLOCKING_CAVEAT_RE = re.compile(
    r"(table\s+not\s+found|metadata\s+catalog|verify\s+table|partition\s+column|"
    r"unknown\s+table|cannot\s+verify|could\s+not\s+verify|表不存在|元数据|分区字段)",
    re.IGNORECASE,
)


def normalize_identifier(value: str) -> str:
    return value.strip("`").lower()


def strip_sql_strings(sql: str) -> str:
    return STRING_LITERAL_RE.sub("''", sql)


def extract_source_tables(sql: str) -> list[str]:
    return sorted({normalize_identifier(table) for table in TABLE_RE.findall(sql or "")})


def extract_limit(sql: str) -> int | None:
    match = LIMIT_RE.search(sql or "")
    if not match:
        return None
    try:
        return int(match.group(1))
    except ValueError:
        return None


def extract_aliases(sql: str) -> set[str]:
    lowered = strip_sql_strings(sql or "")
    aliases = {normalize_identifier(item) for item in ALIAS_RE.findall(lowered)}
    aliases.update(normalize_identifier(item) for item in TABLE_ALIAS_RE.findall(lowered))
    return aliases


def extract_identifiers(sql: str, tables: list[str]) -> list[str]:
    clean = strip_sql_strings((sql or "").replace("`", " "))
    for table in tables:
        clean = re.sub(rf"\b{re.escape(table)}\b", " ", clean, flags=re.IGNORECASE)
    aliases = extract_aliases(sql)
    table_parts = {part for table in tables for part in table.split(".")}
    ignored = SQL_KEYWORDS | SQL_FUNCTIONS | aliases | table_parts
    identifiers = []
    for raw in IDENTIFIER_RE.findall(clean):
        identifier = normalize_identifier(raw)
        if identifier in ignored:
            continue
        if identifier.isdigit():
            continue
        identifiers.append(identifier)
    return sorted(set(identifiers))


def looks_like_risk_entity_field(field: str) -> bool:
    normalized = normalize_identifier(field)
    if normalized in RISK_ENTITY_IDENTIFIER_FIELDS:
        return True
    return any(fragment in normalized for fragment in ("device", "did", "ip", "eventid", "sourceid"))


def field_class(field: str) -> str:
    normalized = normalize_identifier(field)
    if looks_like_risk_entity_field(normalized):
        return "risk_entity_identifier"
    if normalized in CREDENTIAL_SECRET_FIELDS:
        return "credential_secret"
    if normalized in PII_STRICT_FIELDS:
        return "pii_strict"
    if normalized in PARTITION_FIELDS or normalized in SAFE_ANALYSIS_FIELDS:
        return "source_summary_metric"
    if "token" in normalized and normalized not in {"token_id", "tokenid"}:
        return "credential_secret"
    if any(fragment in normalized for fragment in ("cookie", "session", "password", "passwd", "authorization")):
        return "credential_secret"
    if any(fragment in normalized for fragment in ("phone", "mobile", "idcard", "id_card", "email", "realname")):
        return "pii_strict"
    return "unknown"


def extract_caveats(answer_text: str | None) -> tuple[list[str], list[str]]:
    if not answer_text:
        return [], []
    caveats: list[str] = []
    blocking: list[str] = []
    for raw_line in answer_text.splitlines():
        line = raw_line.strip()
        if not line or not CAVEAT_LINE_RE.search(line):
            continue
        safe_line = line[:220]
        caveats.append(safe_line)
        if BLOCKING_CAVEAT_RE.search(line):
            blocking.append(safe_line)
    return sorted(set(caveats)), sorted(set(blocking))


def partition_filter_present(sql: str, partition_fields: set[str]) -> bool:
    clean = strip_sql_strings(sql or "")
    for field in partition_fields:
        if re.search(rf"\b{re.escape(field)}\b\s*(=|in\b|between\b|>=|<=|>|<)", clean, re.IGNORECASE):
            return True
    return False


def bounded_entity_filter_present(sql: str) -> bool:
    clean = strip_sql_strings(sql or "")
    entity_fields = (
        "user_id",
        "userid",
        "uid",
        "device_id",
        "deviceid",
        "did",
        "source_id",
        "sourceid",
        "event_id",
        "eventid",
        "source_ip",
        "user_ip",
        "ip",
    )
    for field in entity_fields:
        if re.search(rf"\b{re.escape(field)}\b\s*(=|in\b|between\b|>=|<=|>|<|like\b)", clean, re.IGNORECASE):
            return True
    return False


def evaluate_dataagent_sql_quality(
    generated_sql: str | None,
    *,
    model_answer_text: str | None = None,
    max_rows: int = MAX_DEFAULT_ROWS,
) -> dict[str, Any]:
    """Return a no-raw-SQL quality gate result for a DataAgent dry-run SQL."""

    if not generated_sql or not generated_sql.strip():
        return {
            "schema_version": "dataagent_sql_quality_gate_v1",
            "checked": False,
            "gate_status": "not_applicable",
            "dry_run_false_eligible": False,
            "dry_run_false_execution_allowed": False,
            "requires_per_call_authorization": True,
            "sql_executed": False,
            "hive_called": False,
            "failure_reasons": ["missing_generated_sql"],
        }

    sql = generated_sql.strip()
    tables = extract_source_tables(sql)
    unknown_tables = [table for table in tables if table not in ALLOWED_TABLES]
    allowed_tables = [table for table in tables if table in ALLOWED_TABLES]
    required_partition_fields = set().union(
        *(TABLE_REQUIRED_PARTITION_FIELDS.get(table, set()) for table in allowed_tables)
    )
    partition_fields_present = {
        field for field in PARTITION_FIELDS if re.search(rf"\b{re.escape(field)}\b", sql, re.IGNORECASE)
    }
    missing_partition_by_table = {
        table: sorted(TABLE_REQUIRED_PARTITION_FIELDS[table].difference(partition_fields_present))
        for table in allowed_tables
        if TABLE_REQUIRED_PARTITION_FIELDS[table].difference(partition_fields_present)
    }

    fields = extract_identifiers(sql, tables)
    classified_fields: dict[str, list[str]] = {
        "risk_entity_identifier": [],
        "source_summary_metric": [],
        "credential_secret": [],
        "pii_strict": [],
        "unknown": [],
    }
    for field in fields:
        classified_fields[field_class(field)].append(field)
    for class_name in classified_fields:
        classified_fields[class_name] = sorted(set(classified_fields[class_name]))

    disallowed_fields = classified_fields["unknown"]
    sensitive_fields = classified_fields["credential_secret"] + classified_fields["pii_strict"]
    limit_value = extract_limit(sql)
    dataagent_caveats, blocking_caveats = extract_caveats(model_answer_text)
    write_operation_present = bool(WRITE_OPERATION_RE.search(sql))
    partition_ok = not required_partition_fields or (
        partition_filter_present(sql, required_partition_fields) and not missing_partition_by_table
    )
    limit_ok = limit_value is not None and limit_value <= max_rows
    bounded_ok = bounded_entity_filter_present(sql)

    failure_reasons: list[str] = []
    if write_operation_present:
        failure_reasons.append("write_operation_present")
    if not tables:
        failure_reasons.append("no_source_table_detected")
    failure_reasons.extend(f"unknown_table:{table}" for table in unknown_tables)
    for table, fields_missing in sorted(missing_partition_by_table.items()):
        failure_reasons.append(f"missing_partition_field:{table}:{','.join(fields_missing)}")
    if required_partition_fields and not partition_filter_present(sql, required_partition_fields):
        failure_reasons.append("missing_partition_filter")
    failure_reasons.extend(f"field_not_whitelisted:{field}" for field in disallowed_fields)
    failure_reasons.extend(f"sensitive_field_requested:{field}" for field in sensitive_fields)
    if limit_value is None:
        failure_reasons.append("missing_limit")
    elif limit_value > max_rows:
        failure_reasons.append(f"limit_exceeds_max_rows:{limit_value}")
    if not bounded_ok:
        failure_reasons.append("missing_bounded_entity_filter")
    failure_reasons.extend("dataagent_blocking_caveat" for _ in blocking_caveats)

    gate_status = "pass" if not failure_reasons else "block"
    return {
        "schema_version": "dataagent_sql_quality_gate_v1",
        "checked": True,
        "gate_status": gate_status,
        "dry_run_false_eligible": gate_status == "pass",
        "dry_run_false_execution_allowed": False,
        "requires_per_call_authorization": True,
        "sql_executed": False,
        "hive_called": False,
        "quality_checks": {
            "readonly_select_only": not write_operation_present,
            "table_whitelist_pass": bool(tables) and not unknown_tables,
            "partition_filter_pass": partition_ok,
            "field_whitelist_pass": not disallowed_fields,
            "sensitive_field_pass": not sensitive_fields,
            "scan_scope_pass": limit_ok and bounded_ok,
            "dataagent_caveat_pass": not blocking_caveats,
        },
        "table_policy": {
            "allowed_tables": allowed_tables,
            "unknown_tables": unknown_tables,
        },
        "partition_policy": {
            "required_partition_fields": sorted(required_partition_fields),
            "present_partition_fields": sorted(partition_fields_present),
            "missing_partition_by_table": missing_partition_by_table,
        },
        "field_policy": {
            "risk_entity_identifier_fields_present": classified_fields["risk_entity_identifier"],
            "source_summary_metric_fields_present": classified_fields["source_summary_metric"],
            "credential_secret_fields_present": classified_fields["credential_secret"],
            "pii_strict_fields_present": classified_fields["pii_strict"],
            "unknown_fields_present": classified_fields["unknown"],
            "ip_and_device_are_risk_entity_identifiers": True,
        },
        "scan_scope_policy": {
            "limit_present": limit_value is not None,
            "limit_value": limit_value,
            "max_rows": max_rows,
            "bounded_entity_filter_present": bounded_ok,
            "partition_filter_present": partition_filter_present(sql, required_partition_fields),
        },
        "dataagent_caveat_policy": {
            "caveats_present": bool(dataagent_caveats),
            "caveats": dataagent_caveats,
            "blocking_caveats": blocking_caveats,
        },
        "failure_reasons": sorted(set(failure_reasons)),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate DataAgent dry-run SQL quality without execution.")
    parser.add_argument("--sql", help="SQL string to check. Reads stdin when omitted.")
    parser.add_argument("--answer-text", help="Optional MODEL_ANSWER text for caveat extraction.")
    parser.add_argument("--max-rows", type=int, default=MAX_DEFAULT_ROWS)
    parser.add_argument("--json", action="store_true", help="Emit JSON. This is the default.")
    args = parser.parse_args(argv)

    sql = args.sql if args.sql is not None else sys.stdin.read()
    result = evaluate_dataagent_sql_quality(sql, model_answer_text=args.answer_text, max_rows=args.max_rows)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result.get("gate_status") in {"pass", "not_applicable"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
