import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from runtime_case_execution_runner import (  # noqa: E402
    SourcePlanItem,
    _new_scheduler_state,
    _split_by_scheduler_circuit,
    _update_scheduler_state_from_chunk,
    build_missing_evidence,
    build_short_circuit_batch_result,
    merge_source_quality,
)


def _item(action: str, source_id: str, user_id: str = "100") -> SourcePlanItem:
    return SourcePlanItem(
        source_id=source_id,
        action=action,
        execution_group="independent_parallel",
        depends_on=[],
        timeout_class="standard",
        failure_policy="non_blocking_partial",
        source_priority="P1",
        expected_observation="fixture",
        params={"user_id": user_id},
        timeout_ms=1000,
        required_fields=["user_id"],
        window_policy="event_centered",
        window_start_ms=1,
        window_end_ms=2,
    )


def _batch_result_for_row(row: dict) -> dict:
    source_id = row["source_id"]
    return {
        "ok": True,
        "batch_status": "completed",
        "transport_status_matrix": {source_id: row},
        "source_results": {
            source_id: {
                "source_id": source_id,
                "action": row.get("action"),
                "transport": row,
            }
        },
        "missing_or_failed_sources": [],
    }


def _quality_for(action: str, rows: list[dict]) -> dict:
    items = [_item(action, row["source_id"], str(index)) for index, row in enumerate(rows, start=1)]
    result = {
        "ok": True,
        "batch_status": "completed",
        "transport_status_matrix": {row["source_id"]: row for row in rows},
        "source_results": {
            row["source_id"]: {
                "source_id": row["source_id"],
                "action": row.get("action") or action,
                "transport": row,
            }
            for row in rows
        },
        "missing_or_failed_sources": [],
    }
    return merge_source_quality(items, result)


def test_track_need_data_sync_marks_business_gap_without_no_risk():
    item = _item("track_analysis_check_data_ready", "track_1")
    row = {
        "source_id": item.source_id,
        "action": item.action,
        "category": "completed",
        "source_status": "completed",
        "http_status": 200,
        "body_present": True,
        "platform_error": "NEED_DATA_SYNC",
    }

    quality = merge_source_quality([item], _batch_result_for_row(row))
    source = quality["per_source"][0]
    missing = build_missing_evidence(quality)[0]

    assert source["quality_class"] == "blocked"
    assert source["gap_state"] == "track_business_field_gap"
    assert source["gap_reason"] == "NEED_DATA_SYNC_or_HIVE_UNFINISHED"
    assert source["is_low_risk_counter_evidence"] is False
    assert missing["is_low_risk_counter_evidence"] is False


def test_track_hive_unfinished_marks_business_gap_without_deep_behavior_evidence():
    item = _item("track_analysis_check_data_ready", "track_2")
    row = {
        "source_id": item.source_id,
        "action": item.action,
        "category": "completed",
        "source_status": "completed",
        "http_status": 200,
        "body_present": True,
        "platform_error": "HIVE_UNFINISHED",
    }

    quality = merge_source_quality([item], _batch_result_for_row(row))
    source = quality["per_source"][0]

    assert source["gap_state"] == "track_business_field_gap"
    assert source["gap_reason"] == "NEED_DATA_SYNC_or_HIVE_UNFINISHED"
    assert "duration" not in source
    assert "active_days" not in source
    assert "lineage" not in source


def test_weapon_missing_raw_device_id_marks_riskdata_gap():
    item = _item("weapon_inventory", "weapon_1")
    row = {
        "source_id": item.source_id,
        "action": item.action,
        "category": "completed",
        "source_status": "completed",
        "http_status": 200,
        "body_present": True,
        "source_result": {"riskData_status": "not_executed_missing_device_id"},
    }

    quality = merge_source_quality([item], _batch_result_for_row(row))
    source = quality["per_source"][0]
    missing = build_missing_evidence(quality)

    assert source["gap_state"] == "not_executed_missing_device_id"
    assert source["gap_reason"] == "missing_raw_device_id"
    assert source["is_low_risk_counter_evidence"] is False
    assert missing[0]["gap_state"] == "not_executed_missing_device_id"
    assert missing[0]["gap_reason"] == "missing_raw_device_id"
    assert missing[0]["is_low_risk_counter_evidence"] is False


def test_rcp_event_detail_consecutive_timeout_opens_circuit_and_skips_only_that_action():
    state = _new_scheduler_state()
    row_1 = {"source_id": "rcp_1", "action": "rcp_event_detail", "source_status": "timeout", "error_type": "timeout"}
    row_1_ok = {"source_id": "rcp_1_ok", "action": "rcp_event_detail", "source_status": "completed", "http_status": 200, "body_present": True}
    row_2 = {"source_id": "rcp_2", "action": "rcp_event_detail", "source_status": "timeout", "error_type": "timeout"}

    assert _update_scheduler_state_from_chunk(state, chunk_quality=_quality_for("rcp_event_detail", [row_1, row_1_ok])) == []
    opened = _update_scheduler_state_from_chunk(state, chunk_quality=_quality_for("rcp_event_detail", [row_2]))

    assert opened[0]["source_action"] == "rcp_event_detail"
    assert opened[0]["gap_reason"] == "circuit_open_timeout"

    active, skipped, by_reason = _split_by_scheduler_circuit(
        state,
        [_item("rcp_event_detail", "rcp_3"), _item("login_logs_search", "login_1")],
    )
    assert [item.action for item in active] == ["login_logs_search"]
    assert [item.action for item in skipped] == ["rcp_event_detail"]
    assert list(by_reason) == ["circuit_open_timeout"]


def test_rcp_feature_list_timeout_ratio_over_half_opens_circuit():
    state = _new_scheduler_state()
    rows = [
        {"source_id": "feature_1", "action": "rcp_event_feature_list", "source_status": "timeout", "error_type": "timeout"},
        {"source_id": "feature_2", "action": "rcp_event_feature_list", "source_status": "completed", "http_status": 200, "body_present": True},
        {"source_id": "feature_3", "action": "rcp_event_feature_list", "source_status": "timeout", "error_type": "timeout"},
    ]

    opened = _update_scheduler_state_from_chunk(state, chunk_quality=_quality_for("rcp_event_feature_list", rows))

    assert opened[0]["source_action"] == "rcp_event_feature_list"
    assert state["open_circuits"]["rcp_event_feature_list"]["gap_reason"] == "circuit_open_timeout"


def test_repeated_auth_failed_opens_auth_short_circuit():
    state = _new_scheduler_state()
    rows = [
        {"source_id": "archives_1", "action": "archives_user_analysis", "source_status": "auth_failed", "error_type": "auth_failed"},
        {"source_id": "archives_2", "action": "archives_user_analysis", "source_status": "auth_failed", "error_type": "auth_failed"},
    ]

    opened = _update_scheduler_state_from_chunk(state, chunk_quality=_quality_for("archives_user_analysis", rows))

    assert opened[0]["source_action"] == "archives_user_analysis"
    assert opened[0]["gap_reason"] == "auth_session_issue"
    active, skipped, by_reason = _split_by_scheduler_circuit(
        state,
        [_item("archives_user_analysis", "archives_3"), _item("archives_review_logs", "review_1")],
    )
    assert [item.action for item in active] == ["archives_review_logs"]
    assert [item.action for item in skipped] == ["archives_user_analysis"]
    assert list(by_reason) == ["auth_session_issue"]


def test_short_circuit_result_is_source_gap_not_no_risk():
    items = [_item("rcp_event_detail", "rcp_4", "200"), _item("rcp_event_detail", "rcp_5", "201")]
    result = build_short_circuit_batch_result(
        items,
        gap_state="source_gap",
        gap_reason="circuit_open_timeout",
        short_circuit_type="timeout_circuit_breaker",
        circuit_open=True,
    )

    quality = merge_source_quality(items, result)
    missing = build_missing_evidence(quality)

    assert result["short_circuit_summary"]["affected_user_count"] == 2
    assert all(row["is_low_risk_counter_evidence"] is False for row in quality["per_source"])
    assert all(row["is_low_risk_counter_evidence"] is False for row in missing)
    assert {row["gap_reason"] for row in missing} == {"circuit_open_timeout"}
