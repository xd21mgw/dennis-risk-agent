#!/usr/bin/env python3
"""Offline checks for Dennis fact table contract and minimal fixture.

This checker does not start services, access platforms, call DataAgent/Hive,
or execute runtime sources.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_FILE = ROOT / "computer_use_poc" / "fact_table_contract_v1.md"
SOURCE_PLAN_FILE = ROOT / "computer_use_poc" / "source_orchestration_plan_v1.yaml"
VALIDATION_FILE = ROOT / "computer_use_poc" / "runtime_validation_cases_v1.yaml"
SMOKE_FILE = ROOT / "computer_use_poc" / "smoke_tests.md"
FIXTURE_FILE = ROOT / "computer_use_poc" / "test_fixtures" / "fact_table_minimal_batch_v1.json"

CHECK_FILES = [CONTRACT_FILE, SOURCE_PLAN_FILE, VALIDATION_FILE, SMOKE_FILE]

TABLE_REQUIRED_FIELDS = {
    "standard_detail_table": [
        "sample_id",
        "entity_id",
        "entity_type",
        "round_id",
        "source_id",
        "action",
        "observation_domain",
        "field_name",
        "field_value_or_safe_ref",
        "event_time",
        "source_quality",
        "evidence_source",
    ],
    "anchor_table": [
        "round_id",
        "sample_id",
        "entity_id",
        "anchor_type",
        "anchor_value_or_safe_ref",
        "source_id",
        "field_path",
        "source_quality",
        "anchor_class",
        "anchor_score",
        "selection_status",
        "anchor_priority_reason",
    ],
    "feature_table": [
        "feature_name",
        "source_domains",
        "supporting_current_evidence",
        "supporting_selected_anchors",
        "signal_inputs",
        "hypothesis_inputs",
        "validation_needed",
        "false_positive_risk",
        "not_final_conclusion",
    ],
    "relation_table": [
        "from_entity",
        "to_entity",
        "relation_type",
        "edge_type",
        "edge_strength",
        "source_id",
        "source_quality",
        "round_id",
        "expansion_depth",
        "stop_reason",
    ],
    "source_quality_table": [
        "round_id",
        "entity_id",
        "source_id",
        "action",
        "quality_class",
        "reason",
        "partial_subtype",
        "missing_fields",
        "response_limited",
    ],
    "round_support_table": [
        "signal_name",
        "round_id",
        "support_entities",
        "support_count",
        "support_ratio",
        "source_quality_summary",
    ],
    "rolling_anchor_summary": [
        "anchor_type",
        "anchor_value_or_safe_ref",
        "cumulative_support_count",
        "support_rounds",
        "stability_across_rounds",
        "new_anchor_delta",
        "dropped_anchor_reason",
        "current_status",
    ],
}

CONTRACT_KEYWORDS = [
    "raw_detail_retention_layer",
    "safe_projected_records",
    *TABLE_REQUIRED_FIELDS.keys(),
    "per_user_observation",
    "batch commonality",
    "full_observation_mode",
    "sample_expand_validate_mode",
    "round_support_count",
    "cumulative_support_count",
    "support_ratio",
    "stability_across_rounds",
    "new_anchor_delta",
    "stable_anchors",
    "dropped_anchors",
]

ROLLING_BATCH_FIELDS = [
    "round_support_count",
    "cumulative_support_count",
    "support_ratio",
    "stability_across_rounds",
    "new_anchor_delta",
    "stable_anchors",
    "dropped_anchors",
]

SAFE_PROJECTED_FORBIDDEN_FRAGMENTS = [
    "raw_body",
    "upstream.body",
    "upstream.capped_body",
    "capped_body",
    "logContent",
    "cookie",
    "token",
    "session",
    "header",
    "authorization",
    "password",
]

TRACE_FIELDS = ["sample_id", "entity_id", "round_id", "source_id", "source_quality"]


def _relative(path: Path) -> str:
    return str(path.relative_to(ROOT))


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _load_fixture() -> dict[str, Any]:
    return json.loads(FIXTURE_FILE.read_text(encoding="utf-8"))


def _validate_files_exist() -> list[str]:
    return [f"missing_file:{_relative(path)}" for path in [*CHECK_FILES, FIXTURE_FILE] if not path.exists()]


def _validate_contract_keywords() -> tuple[list[str], dict[str, Any]]:
    combined = "\n".join(_read(path) for path in CHECK_FILES if path.exists())
    missing = [keyword for keyword in CONTRACT_KEYWORDS if keyword not in combined]
    return [f"contract_keyword_missing:{keyword}" for keyword in missing], {
        "checked_files": [_relative(path) for path in CHECK_FILES],
        "missing_keywords": missing,
    }


def _validate_table_rows(fixture: dict[str, Any]) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    summary: dict[str, Any] = {}
    for table_name, required_fields in TABLE_REQUIRED_FIELDS.items():
        rows = fixture.get(table_name)
        if not isinstance(rows, list) or not rows:
            errors.append(f"table_missing_or_empty:{table_name}")
            summary[table_name] = {"row_count": 0, "missing_fields": required_fields}
            continue
        table_missing: list[str] = []
        for index, row in enumerate(rows, start=1):
            if not isinstance(row, dict):
                errors.append(f"{table_name}:{index}:row_not_object")
                continue
            missing = [field for field in required_fields if field not in row]
            table_missing.extend(missing)
            errors.extend(f"{table_name}:{index}:field_missing:{field}" for field in missing)
        summary[table_name] = {
            "row_count": len(rows),
            "missing_fields": sorted(set(table_missing)),
        }
    return errors, summary


def _value_contains_forbidden(value: Any) -> bool:
    if isinstance(value, dict):
        return any(
            any(fragment.lower() in str(key).lower() for fragment in SAFE_PROJECTED_FORBIDDEN_FRAGMENTS)
            or _value_contains_forbidden(child)
            for key, child in value.items()
        )
    if isinstance(value, list):
        return any(_value_contains_forbidden(child) for child in value)
    text = str(value)
    return any(fragment.lower() in text.lower() for fragment in SAFE_PROJECTED_FORBIDDEN_FRAGMENTS)


def _validate_safe_projected_records(fixture: dict[str, Any]) -> tuple[list[str], dict[str, Any]]:
    records = fixture.get("safe_projected_records", [])
    errors: list[str] = []
    if not isinstance(records, list) or not records:
        errors.append("safe_projected_records_missing_or_empty")
        return errors, {"record_count": 0, "forbidden_fragment_found": False}
    for index, record in enumerate(records, start=1):
        if _value_contains_forbidden(record):
            errors.append(f"safe_projected_records:{index}:forbidden_raw_or_credential_fragment")
    return errors, {
        "record_count": len(records),
        "forbidden_fragment_found": any("safe_projected_records:" in error for error in errors),
    }


def _validate_traceability(fixture: dict[str, Any]) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    summary: dict[str, Any] = {}

    direct_tables = [
        "standard_detail_table",
        "anchor_table",
        "relation_table",
        "source_quality_table",
    ]
    for table_name in direct_tables:
        missing_count = 0
        for index, row in enumerate(fixture.get(table_name, []) or [], start=1):
            missing = [field for field in TRACE_FIELDS if field not in row]
            if missing:
                missing_count += 1
                errors.append(f"{table_name}:{index}:trace_fields_missing:{','.join(missing)}")
        summary[table_name] = {"rows_missing_trace_fields": missing_count}

    feature_missing = 0
    for index, row in enumerate(fixture.get("feature_table", []) or [], start=1):
        evidence_rows = row.get("supporting_current_evidence", [])
        if not evidence_rows:
            feature_missing += 1
            errors.append(f"feature_table:{index}:supporting_current_evidence_missing")
            continue
        for evidence_index, evidence in enumerate(evidence_rows, start=1):
            missing = [field for field in TRACE_FIELDS if field not in evidence]
            if missing:
                feature_missing += 1
                errors.append(
                    f"feature_table:{index}:supporting_current_evidence:{evidence_index}:trace_fields_missing:{','.join(missing)}"
                )
    summary["feature_table"] = {"supporting_evidence_trace_errors": feature_missing}

    return errors, summary


def _validate_batch_commonality_inputs(fixture: dict[str, Any]) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    inputs = fixture.get("batch_commonality_inputs", {})
    primary_tables = set(inputs.get("primary_tables", []) or [])
    required_primary = {
        "anchor_table",
        "feature_table",
        "relation_table",
        "source_quality_table",
        "round_support_table",
        "rolling_anchor_summary",
    }
    missing_primary = sorted(required_primary - primary_tables)
    if missing_primary:
        errors.extend(f"batch_commonality_primary_table_missing:{table}" for table in missing_primary)
    if inputs.get("per_user_observation_role") != "explanation_only":
        errors.append("per_user_observation_role_not_explanation_only")
    if inputs.get("batch_commonality_not_based_only_on_per_user_observation") is not True:
        errors.append("batch_commonality_only_per_user_observation_guard_missing")

    mode_consumption = fixture.get("mode_consumption", {})
    mode2 = mode_consumption.get("sample_expand_validate_mode", {})
    if mode2.get("must_not_depend_only_on_per_user_observation") is not True:
        errors.append("mode2_per_user_only_guard_missing")
    required_mode2 = set(mode2.get("required_inputs", []) or [])
    missing_mode2 = sorted(required_primary - required_mode2)
    errors.extend(f"mode2_required_input_missing:{table}" for table in missing_mode2)

    rolling = fixture.get("rolling_batch_summary", {})
    missing_rolling = [field for field in ROLLING_BATCH_FIELDS if field not in rolling]
    errors.extend(f"rolling_batch_field_missing:{field}" for field in missing_rolling)

    return errors, {
        "primary_tables": sorted(primary_tables),
        "missing_primary_tables": missing_primary,
        "missing_mode2_inputs": missing_mode2,
        "missing_rolling_fields": missing_rolling,
    }


def run_checks() -> dict[str, Any]:
    errors: list[str] = []
    errors.extend(_validate_files_exist())
    keyword_errors, keyword_summary = _validate_contract_keywords()
    errors.extend(keyword_errors)

    fixture = _load_fixture() if FIXTURE_FILE.exists() else {}
    table_errors, table_summary = _validate_table_rows(fixture)
    safe_errors, safe_summary = _validate_safe_projected_records(fixture)
    trace_errors, trace_summary = _validate_traceability(fixture)
    commonality_errors, commonality_summary = _validate_batch_commonality_inputs(fixture)
    errors.extend(table_errors)
    errors.extend(safe_errors)
    errors.extend(trace_errors)
    errors.extend(commonality_errors)

    return {
        "validation_pass": not errors,
        "errors": errors,
        "contract_keyword_summary": keyword_summary,
        "table_summary": table_summary,
        "safe_projected_records_summary": safe_summary,
        "traceability_summary": trace_summary,
        "batch_commonality_input_summary": commonality_summary,
        "platform_called": False,
        "browser_backed_service_started": False,
        "dataagent_called": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--format", choices=["json", "text"], default="text")
    args = parser.parse_args()

    result = run_checks()
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"validation_pass={str(result['validation_pass']).lower()}")
        if result["errors"]:
            print("errors:")
            for error in result["errors"]:
                print(f"- {error}")
    return 0 if result["validation_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
