import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "l3_extraction"))

from p0_foundation_quality_gate import build_quality_gate_summary, normalize_path


def _write_json(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def test_normalize_path_strips_wrappers_and_indexes():
    assert normalize_path("upstream.body.data.dataList[0].requestParam") == "data.dataList.requestParam"
    assert normalize_path("payload.body.data.foo[].bar") == "body.data.foo.bar"
    assert normalize_path("_local_payload.user_id") == "user_id"


def test_quality_gate_classifies_missing_and_board_platform(tmp_path: Path):
    smoke_dir = tmp_path / "wave_4_smoke"
    inventory_path = tmp_path / "full_action_field_inventory.json"
    _write_json(inventory_path, {
        "wave_4": {
            "archives_user_analysis": [
                {"field_path": "data.dataList.requestParam"},
                {"field_path": "data.dataList.parent"},
            ],
            "login_logs_search": [
                {"field_path": "data.logSearchModels.logContent"},
            ],
        }
    })
    raw_records = [
        {
            "wave_id": "wave_4",
            "user_id": "u1",
            "source_action": "archives_user_analysis",
            "raw_path": "upstream.body.data.dataList.requestParam",
            "inventory_seen": False,
            "missing_from_inventory": True,
            "parsed_children_expected": True,
            "parsed_children_seen_count": 3,
            "eligibility_status": "needs_parse",
            "visibility_status": "raw_seen",
            "value_shape": "json_string",
        },
        {
            "wave_id": "wave_4",
            "user_id": "u1",
            "source_action": "archives_user_analysis",
            "raw_path": "upstream.body.data.dataList.parent.child",
            "inventory_seen": False,
            "missing_from_inventory": True,
            "parsed_children_expected": False,
            "parsed_children_seen_count": 0,
            "eligibility_status": "eligible",
            "visibility_status": "raw_seen",
            "value_shape": "string",
        },
        {
            "wave_id": "wave_4",
            "user_id": "u1",
            "source_action": "archives_user_analysis",
            "raw_path": "upstream.body.data.rows.name",
            "inventory_seen": False,
            "missing_from_inventory": True,
            "parsed_children_expected": False,
            "parsed_children_seen_count": 0,
            "eligibility_status": "eligible",
            "visibility_status": "raw_seen",
            "value_shape": "string",
        },
        {
            "wave_id": "wave_4",
            "user_id": "u2",
            "source_action": "archives_user_analysis",
            "raw_path": "upstream.body.data.rows.name",
            "inventory_seen": False,
            "missing_from_inventory": True,
            "parsed_children_expected": False,
            "parsed_children_seen_count": 0,
            "eligibility_status": "eligible",
            "visibility_status": "raw_seen",
            "value_shape": "string",
        },
        {
            "wave_id": "wave_4",
            "user_id": "u1",
            "source_action": "archives_user_analysis",
            "raw_path": "http_status",
            "inventory_seen": False,
            "missing_from_inventory": True,
            "parsed_children_expected": False,
            "parsed_children_seen_count": 0,
            "eligibility_status": "noise",
            "visibility_status": "raw_seen",
            "value_shape": "number",
        },
        {
            "wave_id": "wave_4",
            "user_id": "u1",
            "source_action": "archives_user_analysis",
            "raw_path": "secretToken",
            "inventory_seen": False,
            "missing_from_inventory": True,
            "parsed_children_expected": False,
            "parsed_children_seen_count": 0,
            "eligibility_status": "sensitive_blocked",
            "visibility_status": "raw_seen",
            "value_shape": "string",
        },
    ]
    raw_records.extend([
        {
            "wave_id": "wave_4",
            "user_id": f"u{i}",
            "source_action": "archives_user_analysis",
            "raw_path": "upstream.body.data.rows.name",
            "inventory_seen": False,
            "missing_from_inventory": True,
            "parsed_children_expected": False,
            "parsed_children_seen_count": 0,
            "eligibility_status": "eligible",
            "visibility_status": "raw_seen",
            "value_shape": "string",
        }
        for i in range(3, 13)
    ])
    _write_json(smoke_dir / "full_action_inventory_raw_diff.json", {
        "schema_version": "p0_full_action_inventory_raw_diff_v1",
        "summary": {"wave_id": "wave_4", "raw_total_fields": len(raw_records), "inventory_seen_fields": 0, "missing_fields": len(raw_records)},
        "records": raw_records,
    })
    _write_json(smoke_dir / "parsed_field_inventory.json", {
        "summary": {"wave_id": "wave_4", "parsed_success_rate": 0.99},
        "records": [],
    })
    matrix = []
    for name in ["requestParam", "logContent", "data"]:
        matrix.append({
            "container_name": name,
            "source_action": "archives_user_analysis",
            "attempted": 1,
            "success": 1,
            "error": 0,
            "path_count": 3,
            "parsed_value_count": 3,
            "coverage_user_count": 1,
            "failed_examples": [],
            "parser_type": ["json_object"],
        })
    for name in ["extraParam", "params", "originalLog", "labelInfo", "accessibilitySvc", "enabledAccessibilityServices", "appList"]:
        matrix.append({
            "container_name": name,
            "source_action": "__all__",
            "attempted": 0,
            "success": 0,
            "error": 0,
            "path_count": 0,
            "parsed_value_count": 0,
            "coverage_user_count": 0,
            "failed_examples": [],
            "parser_type": [],
        })
    _write_json(smoke_dir / "container_parser_coverage_matrix.json", {
        "summary": {"wave_id": "wave_4", "container_success_rate": 1.0},
        "matrix": matrix,
    })
    _write_json(smoke_dir / "schema_noise_guard_report.json", {
        "summary": {"wave_id": "wave_4", "guarded_noise_count": 1, "report_only_count": 2},
        "guarded_fields": [
            {"path": "http_status", "guard_level": "noise", "guard_reason": "transport_or_response_wrapper_field", "high_value_allowed": False, "combo_allowed": False},
            {"path": "requestId", "guard_level": "noise", "guard_reason": "transport_or_response_wrapper_field", "high_value_allowed": False, "combo_allowed": False},
            {"path": "pageSize", "guard_level": "report_only", "guard_reason": "pagination_cap_or_query_parameter", "high_value_allowed": False, "combo_allowed": False},
            {"path": "logTags.color", "guard_level": "noise", "guard_reason": "fixed_logTags_color_schema", "high_value_allowed": False, "combo_allowed": False},
            {"path": "clientIp", "guard_level": "noise", "guard_reason": "platform_internal_clientIp", "high_value_allowed": False, "combo_allowed": False},
            {"path": "boardPlatform", "guard_level": "report_only", "guard_reason": "event_environment_context_only", "high_value_allowed": False, "combo_allowed": True},
            {"path": "body_present", "guard_level": "noise", "guard_reason": "transport_or_response_wrapper_field", "high_value_allowed": False, "combo_allowed": False},
            {"path": "response_mode", "guard_level": "noise", "guard_reason": "transport_or_response_wrapper_field", "high_value_allowed": False, "combo_allowed": False},
            {"path": "costTime", "guard_level": "noise", "guard_reason": "transport_or_response_wrapper_field", "high_value_allowed": False, "combo_allowed": False},
        ],
    })

    summary = build_quality_gate_summary(
        smoke_dir=smoke_dir,
        inventory_path=inventory_path,
        output_dir=tmp_path / "quality",
    )

    counts = summary["missing_field_attribution"]
    assert counts["path_alias_or_wrapper_mismatch"] == 1
    assert counts["container_parent_child_mismatch"] == 1
    assert counts["repeated_array_index_path_mismatch"] >= 10
    assert counts["schema_noise_missing"] == 1
    assert counts["sensitive_or_noneligible_missing"] == 1
    board = next(row for row in summary["schema_noise_guard_spot_check"] if row["guard_check"] == "boardPlatform 单字段")
    assert board["ok"] is True
    assert summary["full_autonomous_not_proven"] is True
    assert (tmp_path / "quality" / "p0_foundation_quality_gate_summary.json").exists()

