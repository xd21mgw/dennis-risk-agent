#!/usr/bin/env python3
"""Controlled readonly Tianshi/RCP runner scaffold.

The current implementation provides dry-run and contract-check modes only. It
does not access real platforms, does not read auth state, and does not build
arbitrary requests. Future live mode must be wired through a reviewed readonly
adapter before it can execute platform calls.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from typing import Any


ACTION_TO_SOURCE = {
    "strategy_hit_overview_lookup": "tianshi_strategy_hit",
    "rcp_event_list_readonly": "rcp_event_list",
}
SUPPORTED_ACTIONS = sorted(ACTION_TO_SOURCE)
SUPPORTED_ENTITY_TYPES = {
    "user_id_candidate",
    "source_id",
    "source_id_candidate",
    "event_id",
    "event_id_candidate",
    "device_id",
}
FAILURE_STATUSES = [
    "completed",
    "no_data",
    "auth_failed",
    "blocked",
    "timeout",
    "parse_error",
    "tool_gap",
    "dry_run_only",
]
OUTPUT_SCHEMA = [
    "source_status",
    "records_count",
    "hit_summary",
    "policy_code_summary",
    "risk_decision_summary",
    "time_range",
    "source_quality",
    "redaction_applied",
]

ID_RE = re.compile(r"^[A-Za-z0-9_.:-]{1,128}$")
NUMERIC_ID_RE = re.compile(r"^[0-9]{1,20}$")
TS_RE = re.compile(r"^[0-9]{1,20}$")
PRODUCT_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
EVENT_TYPE_RE = re.compile(r"^[A-Z0-9_]{1,128}$")
SENSITIVE_KEY_RE = re.compile(
    r"(cookie|token|session|header|authorization|password|passwd|api[_-]?key)",
    re.IGNORECASE,
)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_id(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def sanitize_text(value: Any) -> str:
    return SENSITIVE_KEY_RE.sub("redacted_sensitive_key", str(value))[:300]


def emit(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


def base_payload(*, source_name: str, source_status: str, action: str | None) -> dict[str, Any]:
    return {
        "schema_version": "tianshi_rcp_runner_observation_v1",
        "source_name": source_name,
        "action": action,
        "source_status": source_status,
        "records_count": 0,
        "hit_summary": {
            "dry_run_only": True,
            "has_strategy_hit": None,
            "production_policy_hit_count": None,
            "interpretation": "No platform query was executed in this local contract run.",
        },
        "policy_code_summary": {
            "policy_codes": [],
            "raw_policy_payload_output": False,
        },
        "risk_decision_summary": {
            "distribution": {},
            "dry_run_only": True,
        },
        "time_range": {},
        "source_quality": {
            "permission_status": "not_started",
            "auth_status": "not_checked",
            "response_type": "dry_run_contract",
            "reliability_level": "contract_ready_no_live_verification",
            "failure_reason": "dry_run_only_no_live_request",
            "no_data_not_risk_exclusion": True,
            "tool_gap": False,
            "runner_present": True,
        },
        "source_card": {
            "source_name": source_name,
            "source_status": source_status,
            "records_count": 0,
            "evidence_summary": "Dry-run contract is available; live readonly execution is not enabled in this runner.",
        },
        "source_checkpoint_private": {
            "raw_references": [],
            "downstream_source_chaining": [],
        },
        "redaction": {
            "redaction_applied": True,
            "sensitive_output": False,
            "raw_reference_retained_for_followup": False,
        },
        "redaction_applied": True,
        "sensitive_output": False,
        "real_platform_request_executed": False,
        "platform_write_action": False,
        "dataagent_called": False,
        "readonly": True,
        "collected_at": now_iso(),
    }


def blocked_payload(reason: str, *, action: str | None = None) -> dict[str, Any]:
    source_name = ACTION_TO_SOURCE.get(action or "", "tianshi_rcp_runner")
    payload = base_payload(source_name=source_name, source_status="blocked", action=action)
    safe_reason = sanitize_text(reason)
    payload["hit_summary"]["interpretation"] = f"Runner invocation blocked: {safe_reason}"
    payload["source_card"]["evidence_summary"] = f"Invocation blocked: {safe_reason}"
    payload["source_quality"]["permission_status"] = "not_started"
    payload["source_quality"]["failure_reason"] = "argument_validation_failed"
    payload["error"] = {"message": safe_reason}
    return payload


def contract_payload() -> dict[str, Any]:
    payload = base_payload(
        source_name="tianshi_rcp_runner",
        source_status="dry_run_only",
        action="contract_check",
    )
    payload["supported_actions"] = SUPPORTED_ACTIONS
    payload["required_inputs"] = [
        "entity_type",
        "entity_id",
        "bounded_time_range",
        "product_or_app",
    ]
    payload["inference_support"] = {
        "entity_type_user_id_candidate": True,
        "time_window_inferred": True,
        "inference_must_be_marked": True,
    }
    payload["output_schema"] = OUTPUT_SCHEMA
    payload["failure_statuses"] = FAILURE_STATUSES
    payload["live_mode"] = {
        "supported_in_contract": True,
        "enabled_by_default": False,
        "current_behavior": "fail_closed_as_dry_run_only",
    }
    payload["source_card"]["evidence_summary"] = "Tianshi/RCP runner contract is available in dry-run mode."
    return payload


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Controlled readonly Tianshi/RCP runner scaffold.")
    parser.add_argument("--mode", default="dry-run")
    parser.add_argument("--action")
    parser.add_argument("--entity-type")
    parser.add_argument("--entity-id")
    parser.add_argument("--from-timestamp")
    parser.add_argument("--to-timestamp")
    parser.add_argument("--product", default="KUAISHOU")
    parser.add_argument("--app-name", default="KUAISHOU")
    parser.add_argument("--event-type")
    parser.add_argument("--time-window-inferred", action="store_true")
    parser.add_argument("--entity-type-inferred", action="store_true")
    parser.add_argument("--format", default="json")
    return parser.parse_args(argv)


def validate_args(args: argparse.Namespace) -> list[str]:
    errors: list[str] = []
    if args.format != "json":
        errors.append("format must be json")
    if args.mode not in {"dry-run", "contract-check", "live"}:
        errors.append("mode must be dry-run, contract-check, or live")
    if args.mode == "contract-check":
        return errors
    if args.action not in ACTION_TO_SOURCE:
        errors.append("action must be strategy_hit_overview_lookup or rcp_event_list_readonly")
    if args.entity_type not in SUPPORTED_ENTITY_TYPES:
        errors.append("entity_type is required and must be a supported entity type")
    if not args.entity_id or not ID_RE.fullmatch(args.entity_id):
        errors.append("entity_id is required and must be an opaque bounded identifier")
    if args.entity_type == "user_id_candidate" and args.entity_id and not NUMERIC_ID_RE.fullmatch(args.entity_id):
        errors.append("user_id_candidate entity_id must be numeric")
    if not args.from_timestamp or not TS_RE.fullmatch(args.from_timestamp):
        errors.append("from_timestamp is required and must be epoch milliseconds")
    if not args.to_timestamp or not TS_RE.fullmatch(args.to_timestamp):
        errors.append("to_timestamp is required and must be epoch milliseconds")
    if args.from_timestamp and args.to_timestamp and TS_RE.fullmatch(args.from_timestamp) and TS_RE.fullmatch(args.to_timestamp):
        if int(args.from_timestamp) >= int(args.to_timestamp):
            errors.append("from_timestamp must be less than to_timestamp")
    if args.product and not PRODUCT_RE.fullmatch(args.product):
        errors.append("product contains unsupported characters")
    if args.app_name and not PRODUCT_RE.fullmatch(args.app_name):
        errors.append("app_name contains unsupported characters")
    if args.event_type and not EVENT_TYPE_RE.fullmatch(args.event_type):
        errors.append("event_type contains unsupported characters")
    return errors


def dry_run_payload(args: argparse.Namespace) -> dict[str, Any]:
    source_name = ACTION_TO_SOURCE[args.action]
    payload = base_payload(source_name=source_name, source_status="dry_run_only", action=args.action)
    from_ts = int(args.from_timestamp)
    to_ts = int(args.to_timestamp)
    entity_safe_id = safe_id(f"{args.entity_type}:{args.entity_id}")
    payload["entity"] = {
        "entity_type": args.entity_type,
        "entity_safe_id": entity_safe_id,
        "entity_type_inferred": bool(args.entity_type_inferred),
        "entity_value_output": "masked_or_safe_id_only",
    }
    payload["time_range"] = {
        "from_timestamp": from_ts,
        "to_timestamp": to_ts,
        "bounded_time_range": True,
        "time_window_inferred": bool(args.time_window_inferred),
        "full_history_claim": False,
    }
    payload["product_context"] = {
        "product": args.product,
        "app_name": args.app_name,
        "product_inferred": args.product == "KUAISHOU",
        "app_inferred": args.app_name == "KUAISHOU",
    }
    payload["source_quality"].update(
        {
            "failure_reason": "dry_run_only_no_live_request",
            "current_status": "dry_run_contract_ready",
            "live_readonly_verified": False,
            "explicit_source_not_silently_skipped": True,
        }
    )
    payload["source_card"]["evidence_summary"] = (
        "Runner contract is ready and this dry-run would route the request to "
        f"{source_name}; no platform evidence was collected."
    )
    payload["source_checkpoint_private"]["raw_references"] = [
        {
            "ref_type": args.entity_type,
            "raw_reference_safe_id": entity_safe_id,
            "alias": "target_entity",
            "retention_scope": "current_task_only",
        }
    ]
    payload["redaction"]["raw_reference_retained_for_followup"] = True
    payload["hit_summary"]["interpretation"] = (
        "Dry-run confirms runner invocation and output contract only. It cannot say whether strategy hits exist."
    )
    if args.action == "rcp_event_list_readonly":
        payload["event_query"] = {
            "event_type": args.event_type or "not_provided",
            "event_type_required_for_live_precision": args.event_type is None,
            "event_list_no_data_boundary": "dry_run_only_not_platform_no_data",
        }
    return payload


def live_disabled_payload(args: argparse.Namespace) -> dict[str, Any]:
    action = args.action if args.action in ACTION_TO_SOURCE else None
    source_name = ACTION_TO_SOURCE.get(action or "", "tianshi_rcp_runner")
    payload = base_payload(source_name=source_name, source_status="dry_run_only", action=action)
    payload["source_quality"]["failure_reason"] = "live_mode_not_enabled"
    payload["source_quality"]["current_status"] = "dry_run_contract_ready"
    payload["source_card"]["evidence_summary"] = (
        "Live readonly mode is declared for future wiring but disabled in this runner scaffold."
    )
    payload["hit_summary"]["interpretation"] = "No live platform call was attempted."
    return payload


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    if args.mode == "contract-check":
        emit(contract_payload())
        return 0

    errors = validate_args(args)
    if errors:
        emit(blocked_payload("; ".join(errors), action=args.action))
        return 2

    if args.mode == "live":
        emit(live_disabled_payload(args))
        return 1

    emit(dry_run_payload(args))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
