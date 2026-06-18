import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "l3_extraction"))

from p0_foundation_inventory import build_p0_foundation_outputs


def _write_json(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def test_p0_foundation_builds_recursive_inventory_and_guards(tmp_path: Path):
    wave_dir = tmp_path / "wave_4"
    raw_dir = wave_dir / "raw"
    raw_dir.mkdir(parents=True)

    request_param = {
        "country_code": ["hk"],
        "boardPlatform": ["kona"],
        "data": json.dumps({"desc": "contact example.com", "token": "secret-token"}),
    }
    archives_payload = {
        "ok": True,
        "http_status": 200,
        "response_mode": "passthrough",
        "body_present": True,
        "content_type": "application/json",
        "requestId": "req-1",
        "upstream": {
            "body": {
                "clientIp": "10.0.0.1",
                "data": {
                    "pageSize": 1,
                    "total": 1,
                    "dataList": [
                        {
                            "aliasField": "alias-value",
                            "requestParam": json.dumps(request_param),
                            "extraParam": "clientPageCode=page_a&source=profile",
                            "enabledAccessibilityServices": "com.example/.Svc:org.demo/org.demo.AccessibilityService",
                            "logTags": [{"color": "#fff"}],
                        }
                    ],
                },
            }
        },
    }
    login_payload = {
        "ok": True,
        "action": "login_logs_search",
        "data": {
            "logSearchModels": [
                {
                    "logContent": json.dumps(
                        {
                            "uri": "/rest/n/user/rebind/verifyCheck",
                            "params": json.dumps(
                                {
                                    "boardPlatform": "lahaina",
                                    "data": json.dumps({"operateType": "rebind", "result": "ok"}),
                                }
                            ),
                        }
                    )
                }
            ]
        },
    }
    weapon_payload = {
        "ok": True,
        "action": "weapon_inventory",
        "upstream": {
            "body": {
                "data": {
                    "originalLog": {
                        "weaponDecodeHeader": {
                            "bootCount": "3",
                            "sim": "0",
                            "weaponStatus": "success",
                        },
                        "user_behavior": {
                            "enterProfileCnt180D": 123,
                            "photoLikeCnt1D": 0,
                        },
                        "model": "Pixel",
                    }
                }
            }
        },
    }
    _write_json(raw_dir / "archives_user_analysis_u1.json", archives_payload)
    _write_json(raw_dir / "login_logs_search_u1.json", login_payload)
    _write_json(raw_dir / "weapon_inventory_u1.json", weapon_payload)
    manifest = [
        {
            "wave_id": "wave_4",
            "action": "archives_user_analysis",
            "user_id": "u1",
            "raw_file_path": str(raw_dir / "archives_user_analysis_u1.json"),
            "raw_present": True,
        },
        {
            "wave_id": "wave_4",
            "action": "login_logs_search",
            "user_id": "u1",
            "raw_file_path": str(raw_dir / "login_logs_search_u1.json"),
            "raw_present": True,
        },
        {
            "wave_id": "wave_4",
            "action": "weapon_inventory",
            "user_id": "u1",
            "raw_file_path": str(raw_dir / "weapon_inventory_u1.json"),
            "raw_present": True,
        },
    ]
    _write_json(wave_dir / "wave_raw_bundle_manifest.json", manifest)
    inventory = {
        "wave_4": {
            "archives_user_analysis": [
                {"field_path": "ok"},
                {"field_path": "http_status"},
                {"field_path": "data.dataList.aliasField"},
                {"field_path": "data.dataList.logTags"},
                {"field_path": "upstream.body.data.dataList.requestParam"},
            ],
            "login_logs_search": [
                {"field_path": "ok"},
                {"field_path": "action"},
                {"field_path": "data.logSearchModels.logContent"},
            ],
            "weapon_inventory": [
                {"field_path": "ok"},
                {"field_path": "action"},
            ],
        }
    }
    inventory_path = tmp_path / "full_action_field_inventory.json"
    _write_json(inventory_path, inventory)

    out_dir = tmp_path / "out"
    summary = build_p0_foundation_outputs(
        wave_dir=wave_dir,
        inventory_path=inventory_path,
        output_dir=out_dir,
        max_parse_depth=4,
    )

    assert summary["full_autonomous_not_proven"] is True
    assert summary["raw_total_fields"] > 0
    assert summary["parsed_success_rate"] > 0
    assert summary["container_success_rate"] > 0

    raw_diff = json.loads((out_dir / "full_action_inventory_raw_diff.json").read_text(encoding="utf-8"))
    request_row = next(
        row for row in raw_diff["records"]
        if row["raw_path"] == "upstream.body.data.dataList.requestParam"
    )
    assert request_row["normalized_raw_path"] == "data.dataList.requestParam"
    assert request_row["normalized_inventory_path"]
    assert request_row["path_match_type"] == "exact"
    assert request_row["raw_container_seen"] is True
    assert request_row["parsed_children_expected"] is True
    assert request_row["parsed_children_seen_count"] > 0
    assert request_row["visibility_status"] in {"parsed_seen", "inventory_seen"}
    assert request_row["eligibility_status"] == "needs_parse"
    alias_row = next(
        row for row in raw_diff["records"]
        if row["raw_path"] == "upstream.body.data.dataList.aliasField"
    )
    assert alias_row["path_match_type"] == "normalized_alias"
    assert alias_row["missing_from_inventory"] is False
    child_row = next(
        row for row in raw_diff["records"]
        if row["raw_path"] == "upstream.body.data.dataList.logTags.color"
    )
    assert child_row["path_match_type"] == "container_parent_child"
    boot = next(
        row for row in raw_diff["records"]
        if row["raw_path"].endswith("originalLog.weaponDecodeHeader.bootCount")
    )
    assert boot["path_match_type"] == "weapon_deep_inventory_patch"
    assert boot["inventory_policy"] == "must_inventory"
    assert boot["is_weaponDecodeHeader"] is True
    assert boot["is_risk_candidate_key_field"] is True
    behavior = next(
        row for row in raw_diff["records"]
        if row["raw_path"].endswith("originalLog.user_behavior.enterProfileCnt180D")
    )
    assert behavior["path_match_type"] == "weapon_deep_inventory_patch"
    assert behavior["inventory_policy"] == "must_inventory"
    assert behavior["is_user_behavior"] is True
    model = next(
        row for row in raw_diff["records"]
        if row["raw_path"].endswith("originalLog.model")
    )
    assert model["path_match_type"] == "weapon_deep_inventory_patch"
    assert model["inventory_policy"] == "report_only_inventory"
    assert raw_diff["summary"]["must_inventory_missing_count"] == 0
    assert raw_diff["summary"]["weaponDecodeHeader_missing_count"] == 0
    assert raw_diff["summary"]["user_behavior_missing_count"] == 0

    parsed = json.loads((out_dir / "parsed_field_inventory.json").read_text(encoding="utf-8"))
    desc = next(
        row for row in parsed["records"]
        if row["raw_path"].endswith("requestParam") and row["parsed_path"].endswith("requestParam.data.desc")
    )
    assert desc["parse_success"] is True
    assert desc["parse_depth"] == 2
    assert desc["parent_parsed_path"].endswith("requestParam.data")
    assert desc["parser_chain"] == ["json_object", "json_object"]
    assert desc["max_parse_depth"] == 4
    token = next(
        row for row in parsed["records"]
        if row["parsed_path"].endswith("requestParam.data.token")
    )
    assert token["sensitive_level"] == "credential"
    assert token["redaction_status"] == "redacted"
    assert token["commonality_eligible"] is False

    coverage = json.loads((out_dir / "container_parser_coverage_matrix.json").read_text(encoding="utf-8"))
    containers = {row["container_name"] for row in coverage["matrix"]}
    for required in {
        "requestParam",
        "extraParam",
        "logContent",
        "params",
        "data",
        "originalLog",
        "labelInfo",
        "accessibilitySvc",
        "enabledAccessibilityServices",
        "appList",
    }:
        assert required in containers
    request_cov = next(
        row for row in coverage["matrix"]
        if row["container_name"] == "requestParam" and row["source_action"] == "archives_user_analysis"
    )
    assert request_cov["attempted"] >= 1
    assert request_cov["success"] >= 1
    assert request_cov["parse_attempted"] >= 1
    assert request_cov["parse_success"] >= 1
    assert request_cov["raw_present"] is True
    assert request_cov["path_count"] > 0
    enabled_cov = next(
        row for row in coverage["matrix"]
        if row["container_name"] == "enabledAccessibilityServices" and row["source_action"] == "archives_user_analysis"
    )
    assert enabled_cov["raw_present"] is True
    assert enabled_cov["parse_attempted"] >= 1
    assert enabled_cov["parse_success"] >= 1
    assert enabled_cov["scanner_gap_reason"] == ""
    app_cov = next(row for row in coverage["matrix"] if row["container_name"] == "appList")
    assert app_cov["raw_present"] is False
    assert app_cov["scanner_gap_reason"] == "raw_absent"
    assert "installedApps" in app_cov["alias_checked"]

    guard = json.loads((out_dir / "schema_noise_guard_report.json").read_text(encoding="utf-8"))
    board = next(row for row in guard["guarded_fields"] if row["path"].endswith("boardPlatform"))
    assert board["guard_level"] == "report_only"
    assert board["guard_reason"] == "event_environment_context_only"
    assert board["high_value_allowed"] is False
    assert board["combo_allowed"] is True
    assert any(row["guard_level"] == "noise" and row["path"].endswith("http_status") for row in guard["guarded_fields"])
    assert any(row["guard_reason"] == "pagination_cap_or_query_parameter" for row in guard["guarded_fields"])
    assert any(row["guard_reason"] == "fixed_logTags_color_schema" for row in guard["guarded_fields"])
    assert any(row["guard_reason"] == "platform_internal_clientIp" for row in guard["guarded_fields"])
