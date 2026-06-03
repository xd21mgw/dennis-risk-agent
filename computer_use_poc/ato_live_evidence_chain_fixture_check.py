#!/usr/bin/env python3
"""Validate ATO live-shaped evidence-chain rendering fixtures."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from runtime_case_execution_runner import (
    build_batch_payload,
    build_photo_detail_followup_items,
    build_ato_single_case_source_plan,
    build_evidence_card,
    build_live_response_inspection,
    build_missing_evidence,
    build_source_observations,
    build_user_device_entity_resolution,
    merge_source_quality,
    render_user_answer_draft,
    validate_batch_payload_contract,
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
    assert by_source["ato_login_logs_search"]["breakpoint_type"] == "service_body_visibility_gap_for_truncated_login_log"
    assert by_source["ato_archives_photo_search"]["breakpoint_type"] == "service_body_visibility_gap"
    assert by_source["ato_archives_user_analysis"]["breakpoint_type"] == "service_body_visibility_gap"
    assert not by_source["ato_archives_photo_search"]["parser_input_available"]
    chain_status = result["evidence_card"]["chain_status"]
    assert chain_status["web_publish_fact"]["status"] == "partial_transport"
    assert chain_status["web_publish_fact"]["partial_subtype"] == "partial_transport"
    assert "service_body_visibility_gap" in chain_status["web_publish_fact"]["breakpoint_types"]
    assert chain_status["web_login_history"]["status"] == "partial_transport"
    assert "service_body_visibility_gap_for_truncated_login_log" in chain_status["web_login_history"]["breakpoint_types"]
    assert result["user_device_entity_resolution"]["resolution_status"] == "candidate_device_id_missing_after_resolution"
    active_groups = {
        item["group_id"]: item["status"]
        for item in result["evidence_card"]["active_backfill_plan"]["groups"]
    }
    assert active_groups["candidate_device_id"] == "candidate_device_id_missing_after_resolution"
    assert active_groups["login_fields"] == "service_body_visibility_gap_for_truncated_login_log"
    candidate_group = next(
        item
        for item in result["evidence_card"]["active_backfill_plan"]["groups"]
        if item["group_id"] == "candidate_device_id"
    )
    assert candidate_group["next_hop_type"] == "auto_realtime_next_hop"
    assert result["evidence_card"]["active_backfill_plan"]["login_window_shrink_plan"]["status"] == "login_log_window_shrink_anchor_missing"
    assert "web_publish_fact" in [
        item["module_id"]
        for item in result["evidence_card"]["offline_backfill_recommendation"]["options"]
    ]
    assert "completed_sources" not in result["user_answer_draft"].splitlines()[0]


def _assert_visible_case(result: dict[str, Any]) -> None:
    by_source = {row["source_id"]: row for row in result["live_response_inspection"]}
    assert by_source["ato_archives_photo_search"]["parser_input_available"]
    assert {"photo_id", "publish_time"} <= set(
        by_source["ato_archives_photo_search"]["extracted_business_fields"]
    )
    detail_fields = set(
        by_source["ato_archives_photo_meta_197323059879"]["extracted_business_fields"]
    ) | set(by_source["ato_archives_photo_profile_197323443136"]["extracted_business_fields"])
    assert {"photo_id", "publish_source", "publish_device", "publish_ip_ua"} <= detail_fields
    assert {"login_time", "login_type", "login_source", "device_id", "ip_ua"} <= set(
        by_source["ato_login_logs_search"]["extracted_business_fields"]
    )
    login_flags = next(
        item["interpretation_flags"]
        for item in result["source_observations"]
        if item["source_id"] == "ato_login_logs_search"
    )
    assert "partial_login_log_parsed_from_capped_body" in login_flags
    assert "partial_login_log_parsed_from_json_array_capped" in login_flags
    assert "login_log_incomplete" in login_flags
    login_observation = next(
        item
        for item in result["source_observations"]
        if item["source_id"] == "ato_login_logs_search"
    )
    assert login_observation["passthrough_row_cap"]["observed_records"] == 61
    assert login_observation["passthrough_row_cap"]["returned_records"] == 17
    assert login_observation["passthrough_row_cap"]["missing_records"] == 44
    assert login_observation["passthrough_row_cap"]["cap_reason"] == "byte_limit"
    login_quality = next(
        item
        for item in result["source_quality"]["per_source"]
        if item["source_id"] == "ato_login_logs_search"
    )
    assert login_quality["observed_records"] == 61
    assert login_quality["returned_records"] == 17
    assert login_quality["missing_records"] == 44
    assert login_quality["cap_reason"] == "byte_limit"
    login_observation_detail = login_observation["dennis_observation"]
    projection = login_observation_detail["evidence_projection"]
    assert projection["projection_applied"] is True
    assert projection["projection_not_business_normalizer"] is True
    assert projection["raw_body_not_retained_in_answer"] is True
    assert projection["projected_records"] >= 3
    assert projection["sensitive_fields_projected_as_handles"] >= 1
    assert projection["strict_pii_fields_redacted"] >= 1
    assert "evidence_projection_applied" in login_observation["interpretation_flags"]
    assert "credential_control_chain_projected_as_safe_handle" in login_observation["interpretation_flags"]
    login_observation_values = {
        (str(handle.get("canonical_field")), str(handle.get("value")))
        for handle in login_observation_detail["extracted_safe_handles"]
    }
    login_values = {value for _field, value in login_observation_values}
    assert ("device_id", "web_c5a2b6bbe230e1ad1c596577d00615c2") in login_observation_values
    assert ("ip_ua", "223.221.196.192") in login_observation_values
    assert ("ip_ua", "Chrome/140") in login_observation_values
    assert ("token_event_id", "token_event_safe_1") in login_observation_values
    assert "refresh_secret_should_not_survive" not in login_values
    assert "cookie_secret_should_not_survive" not in login_values
    assert projection["dropped_fields_count"] >= 1
    assert "13812345678" not in login_values
    assert "strict_name_should_not_survive" not in login_values
    assert "blocked_sensitive_material_detected" in login_observation["interpretation_flags"]
    assert "pii_strict_redacted" in login_observation["interpretation_flags"]
    photo_meta_observation = next(
        item
        for item in result["source_observations"]
        if item["source_id"] == "ato_archives_photo_meta_197323059879"
    )
    assert photo_meta_observation["dennis_observation"]["embedded_json_parse"]["embedded_json_expanded"] is True
    assert "embedded_json_string_expanded" in photo_meta_observation["interpretation_flags"]
    candidates = result["user_device_entity_resolution"]["candidate_device_ids"]
    candidate_ids = {item["device_id"] for item in candidates}
    assert {"web_c5a2b6bbe230e1ad1c596577d00615c2", "did_operation_safe_1"} <= candidate_ids
    assert result["user_device_entity_resolution"]["resolution_status"] == "multiple_candidate_devices_need_ranking"
    chain_status = result["evidence_card"]["chain_status"]
    assert chain_status["web_publish_fact"]["status"] == "closed"
    publish_fields = {
        (item["field"], str(item["value"]))
        for item in chain_status["web_publish_fact"]["field_paths"]
    }
    publish_field_paths = {
        (item["field"], str(item["field_path"]))
        for item in chain_status["web_publish_fact"]["field_paths"]
    }
    assert ("photo_id", "197323059879") in publish_fields
    assert ("photo_id", "197323443136") in publish_fields
    assert ("publish_device", "web_c5a2b6bbe230e1ad1c596577d00615c2") in publish_fields
    assert any(
        field == "publish_device" and path.endswith(".common.deviceId")
        for field, path in publish_field_paths
    )
    assert any(
        field == "publish_source" and path.endswith(".common.uploadSource")
        for field, path in publish_field_paths
    )
    assert any(
        field == "publish_source" and path.endswith(".videoType")
        for field, path in publish_field_paths
    )
    assert chain_status["web_login_history"]["status"] == "partial_transport"
    assert chain_status["web_login_history"]["partial_subtype"] == "partial_transport"
    assert "response_too_large_needs_window_shrink" in chain_status["web_login_history"]["breakpoint_types"]
    assert chain_status["device_identity_alignment"]["status"] in {"closed", "partial_baseline", "partial_consistency"}
    assert result["evidence_card"]["active_backfill_plan"]["login_window_shrink_plan"]["status"] == "login_log_truncated_needs_window_shrink"
    assert result["evidence_card"]["active_backfill_plan"]["login_window_shrink_plan"]["next_hop_type"] == "auto_realtime_next_hop"
    assert result["evidence_card"]["active_backfill_plan"]["photo_detail_next_hop_plan"]["status"] == "photo_detail_backfill_consumed"
    assert result["evidence_card"]["evidence_projection_summary"]


def _assert_source_plan_contract() -> None:
    source_plan = build_ato_single_case_source_plan(
        "2892617234",
        device_id=None,
        window_start_ms=1777784300000,
        window_end_ms=1780376300000,
        include_abnormal_publish=True,
        include_same_device=False,
    )
    login_item = next(item for item in source_plan if item.action == "login_logs_search")
    assert login_item.params["max_records"] == 300
    assert "limit" not in login_item.params


def _assert_backfill_source_constraints(case: dict[str, Any]) -> None:
    constrained = json.loads(json.dumps(case))
    source_results = constrained["batch_result"]["source_results"]
    transport_matrix = constrained["batch_result"]["transport_status_matrix"]
    for source_id in list(source_results):
        if "photo_profile" in source_id or "photo_meta" in source_id:
            del source_results[source_id]
    for source_id in list(transport_matrix):
        if "photo_profile" in source_id or "photo_meta" in source_id:
            del transport_matrix[source_id]
    source_results["ato_login_logs_search"].pop("upstream", None)
    source_results["ato_login_logs_search"].pop("capped_body", None)
    result = _evaluate_case(constrained)
    groups = {
        item["group_id"]: item
        for item in result["evidence_card"]["active_backfill_plan"]["groups"]
    }
    assert groups["publish_device"]["status"] != "publish_device_found"
    assert not any(
        item.get("field") == "operation_device"
        for item in groups["publish_device"].get("found_values", [])
    )
    assert groups["login_fields"]["status"] != "login_fields_found"
    assert groups["login_fields"].get("found_values") == []


def _assert_login_unexpected_html_response_case(case: dict[str, Any]) -> None:
    html_case = json.loads(json.dumps(case))
    login_row = {
        "source_id": "ato_login_logs_search",
        "action": "login_logs_search",
        "http_status": 200,
        "source_status": "failed",
        "error_type": "unexpected_html_response",
        "content_type": "text/html; charset=utf-8",
        "body_present": True,
        "body_truncated": True,
        "observed_bytes": 108115,
        "raw_body_handling": "omitted",
        "transport_error": None,
        "platform_error": None,
        "invalid_params": False,
        "timeout": False,
    }
    html_case["batch_result"]["transport_status_matrix"]["ato_login_logs_search"] = dict(login_row)
    html_case["batch_result"]["source_results"]["ato_login_logs_search"] = {
        "source_id": "ato_login_logs_search",
        "transport": dict(login_row),
    }
    result = _evaluate_case(html_case)
    login_quality = next(
        item
        for item in result["source_quality"]["per_source"]
        if item["source_id"] == "ato_login_logs_search"
    )
    assert login_quality["quality_class"] == "auth_failed"
    assert login_quality["transport_interpretation"] == "auth_flow_not_completed_in_bound_context"
    assert "auth_flow_not_completed_in_bound_context" in login_quality["boundary_notes"]
    login_observation = next(
        item
        for item in result["source_observations"]
        if item["source_id"] == "ato_login_logs_search"
    )
    assert login_observation["breakpoint_type"] == "auth_flow_not_completed_in_bound_context"
    assert "service_body_visibility_gap_for_truncated_login_log" not in login_observation["interpretation_flags"]
    login_chain = result["evidence_card"]["chain_status"]["web_login_history"]
    assert "auth_flow_not_completed_in_bound_context" in login_chain["breakpoint_types"]
    assert "service_body_visibility_gap_for_truncated_login_log" not in login_chain["breakpoint_types"]


def _assert_photo_detail_followup_from_primary_only(case: dict[str, Any]) -> None:
    source_plan = build_ato_single_case_source_plan(
        "2892617234",
        device_id=None,
        window_start_ms=1777784300000,
        window_end_ms=1780376300000,
        include_abnormal_publish=True,
        include_same_device=False,
    )
    primary_only = json.loads(json.dumps(case["batch_result"]))
    primary_only["source_results"] = {
        key: value
        for key, value in primary_only.get("source_results", {}).items()
        if "photo_profile" not in key and "photo_meta" not in key
    }
    primary_only["transport_status_matrix"] = {
        key: value
        for key, value in primary_only.get("transport_status_matrix", {}).items()
        if "photo_profile" not in key and "photo_meta" not in key
    }
    source_quality = merge_source_quality(source_plan, primary_only)
    observations = build_source_observations(source_plan, source_quality, primary_only)
    followup_items = build_photo_detail_followup_items(
        observations,
        window_start_ms=1777784300000,
        window_end_ms=1780376300000,
    )
    source_ids = {item.source_id for item in followup_items}
    actions = {item.action for item in followup_items}
    assert actions == {"archives_photo_profile", "archives_photo_meta"}
    assert "ato_archives_photo_profile_197323059879" in source_ids
    assert "ato_archives_photo_meta_197323059879" in source_ids
    assert "ato_archives_photo_profile_197323443136" in source_ids
    assert "ato_archives_photo_meta_197323443136" in source_ids
    assert all(item.execution_group == "auth_sensitive_serial" for item in followup_items)
    assert all(item.failure_policy == "non_blocking_partial" for item in followup_items)
    assert all(item.required_fields == ["photo_id"] for item in followup_items)
    followup_payload = build_batch_payload(
        "dennis_ato_single_case_2892617234:photo_detail_followup",
        followup_items,
        dry_run=False,
    )
    assert validate_batch_payload_contract(followup_payload)["valid"]
    assert [group["group_id"] for group in followup_payload["execution_groups"]] == ["auth_sensitive_serial"]
    assert "depends_on" not in followup_payload["execution_groups"][0]


def main() -> int:
    fixture = json.loads(FIXTURE_PATH.read_text())
    _assert_source_plan_contract()
    results = [_evaluate_case(case) for case in fixture["cases"]]
    result_by_id = {item["case_id"]: item for item in results}
    _assert_suppressed_case(result_by_id["live_suppressed_body_visibility_gap"])
    _assert_visible_case(result_by_id["visible_capped_body_business_fields_available"])
    _assert_photo_detail_followup_from_primary_only(
        next(case for case in fixture["cases"] if case["id"] == "visible_capped_body_business_fields_available")
    )
    _assert_backfill_source_constraints(
        next(case for case in fixture["cases"] if case["id"] == "visible_capped_body_business_fields_available")
    )
    _assert_login_unexpected_html_response_case(
        next(case for case in fixture["cases"] if case["id"] == "visible_capped_body_business_fields_available")
    )
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
