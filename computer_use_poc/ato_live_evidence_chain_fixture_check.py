#!/usr/bin/env python3
"""Validate ATO live-shaped evidence-chain rendering fixtures."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from runtime_case_execution_runner import (
    build_ato_single_case_source_plan,
    build_evidence_card,
    build_live_response_inspection,
    build_missing_evidence,
    build_source_observations,
    build_user_device_entity_resolution,
    merge_source_quality,
    render_user_answer_draft,
)


FIXTURE_PATH = (
    Path(__file__).resolve().parent
    / "test_fixtures"
    / "ato_live_evidence_chain_2892617234_shape_v1.json"
)


def _evaluate_case(case: dict[str, Any]) -> dict[str, Any]:
    source_plan = build_ato_single_case_source_plan(
        "2892617234",
        device_id=None,
        window_start_ms=1777784300000,
        window_end_ms=1780376300000,
        include_abnormal_publish=True,
        include_same_device=False,
    )
    batch_result = case["batch_result"]
    source_quality = merge_source_quality(source_plan, batch_result)
    observations = build_source_observations(source_plan, source_quality, batch_result)
    entity_resolution = build_user_device_entity_resolution(
        source_plan,
        batch_result,
        provided_device_id=None,
        source_observations=observations,
    )
    missing_evidence = build_missing_evidence(source_quality)
    missing_evidence.extend(entity_resolution.get("missing_evidence", []))
    evidence_card = build_evidence_card(
        "ato_single_case",
        "2892617234",
        "live",
        source_quality,
        observations,
        entity_resolution,
        missing_evidence,
    )
    inspection = build_live_response_inspection(source_plan, batch_result, observations, evidence_card)
    return {
        "case_id": case["id"],
        "source_quality": source_quality,
        "source_observations": observations,
        "user_device_entity_resolution": entity_resolution,
        "evidence_card": evidence_card,
        "live_response_inspection": inspection,
        "user_answer_draft": render_user_answer_draft(evidence_card),
    }


def _assert_suppressed_case(result: dict[str, Any]) -> None:
    by_source = {row["source_id"]: row for row in result["live_response_inspection"]}
    assert by_source["ato_archives_photo_search"]["breakpoint_type"] == "service_body_visibility_gap"
    assert by_source["ato_archives_user_analysis"]["breakpoint_type"] == "service_body_visibility_gap"
    assert not by_source["ato_archives_photo_search"]["parser_input_available"]
    chain_status = result["evidence_card"]["chain_status"]
    assert chain_status["web_publish_fact"]["status"] == "missing"
    assert "service_body_visibility_gap" in chain_status["web_publish_fact"]["breakpoint_types"]
    assert "web_publish_fact" in [
        item["module_id"]
        for item in result["evidence_card"]["offline_backfill_recommendation"]["options"]
    ]
    assert "completed_sources" not in result["user_answer_draft"].splitlines()[0]


def _assert_visible_case(result: dict[str, Any]) -> None:
    by_source = {row["source_id"]: row for row in result["live_response_inspection"]}
    assert by_source["ato_archives_photo_search"]["parser_input_available"]
    assert {"photo_id", "publish_time", "publish_source", "publish_device"} <= set(
        by_source["ato_archives_photo_search"]["extracted_business_fields"]
    )
    assert {"login_time", "login_type", "login_source", "device_id", "ip_ua"} <= set(
        by_source["ato_login_logs_search"]["extracted_business_fields"]
    )
    candidates = result["user_device_entity_resolution"]["candidate_device_ids"]
    candidate_ids = {item["device_id"] for item in candidates}
    assert {"did_publish_safe_1", "did_login_safe_1", "did_operation_safe_1"} <= candidate_ids
    chain_status = result["evidence_card"]["chain_status"]
    assert chain_status["web_publish_fact"]["status"] == "closed"
    assert chain_status["web_login_history"]["status"] == "partial"
    assert "response_too_large_needs_window_shrink" in chain_status["web_login_history"]["breakpoint_types"]
    assert chain_status["device_identity_alignment"]["status"] in {"closed", "partial"}


def main() -> int:
    fixture = json.loads(FIXTURE_PATH.read_text())
    results = [_evaluate_case(case) for case in fixture["cases"]]
    result_by_id = {item["case_id"]: item for item in results}
    _assert_suppressed_case(result_by_id["live_suppressed_body_visibility_gap"])
    _assert_visible_case(result_by_id["visible_capped_body_business_fields_available"])
    print(
        json.dumps(
            {
                "status": "ATO_LIVE_EVIDENCE_CHAIN_FIXTURE_OK",
                "cases": [
                    {
                        "case_id": item["case_id"],
                        "chain_status": item["evidence_card"]["chain_status"],
                        "dynamic_modules": [
                            option["module_id"]
                            for option in item["evidence_card"]["offline_backfill_recommendation"]["options"]
                        ],
                    }
                    for item in results
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
