import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from l3_extraction.l3_value_level_candidate_extractor import (
    candidates_from_raw_observations,
    candidates_from_reviewed_gr9_label_summary,
    validate_candidate_schema,
)


def test_raw_observation_value_level_extraction(tmp_path: Path):
    raw = [
        {
            "action": "weapon_inventory",
            "source_name": "weapon_android",
            "user_id": "u1",
            "device_id": "d1",
            "payload": {
                "weapon_one_risk": ["oneRiskLaunchLess10", "oneRiskBatteryZero"],
                "raw_data": {
                    "cpuInfo": {"arch": "arm64-v8a"},
                    "enabledAccessibilityServiceList": "com.example.accessibility",
                    "vendorIds": {"xm1": "id-1"},
                },
            },
        },
        {
            "action": "login_logs_search",
            "user_id": "u2",
            "payload": {
                "action_type": "REFRESH_TOKEN",
            },
        },
    ]
    path = tmp_path / "raw.json"
    path.write_text(json.dumps(raw), encoding="utf-8")

    candidates = candidates_from_raw_observations(path)
    keys = {
        (c["source_name"], c["field_path"], c["field_value_or_pattern"], c["candidate_grain"])
        for c in candidates
    }

    assert ("weapon_android", "weapon_android.weapon_one_risk", "oneRiskLaunchLess10", "label_value") in keys
    assert ("weapon_android", "weapon_android.raw_data.cpuInfo.arch", "arm64-v8a", "object_child_value") in keys
    assert (
        "weapon_android",
        "weapon_android.raw_data.enabledAccessibilityServiceList",
        "com.example.accessibility",
        "array_element",
    ) in keys
    assert (
        "weapon_android",
        "weapon_android.raw_data.vendorIds.xm1",
        "__anchor_value_redacted__",
        "high_cardinality_anchor",
    ) in keys
    assert (
        "infra_user_action_log",
        "infra_user_action_log.action_type",
        "REFRESH_TOKEN",
        "enum_value",
    ) in keys
    assert all(c["need_raw_confirm"] is False for c in candidates)
    assert all(c["extraction_confidence"] == "high" for c in candidates)
    assert all(validate_candidate_schema(c) == [] for c in candidates)
    arch = next(c for c in candidates if c["field_path"] == "weapon_android.raw_data.cpuInfo.arch")
    assert arch["feature_type"] == "raw_field"
    assert arch["value_type"] == "category"
    assert arch["baseline_mode"] == "baseline_supported"
    assert arch["commonality_family"] == "field_value_commonality"
    assert arch["commonality_evidence"]


def test_reviewed_gr9_label_summary_is_value_level():
    candidates = candidates_from_reviewed_gr9_label_summary()
    launch = next(c for c in candidates if c["field_value_or_pattern"] == "oneRiskLaunchLess10")

    assert launch["source_name"] == "weapon_android"
    assert launch["field_path"] == "weapon_android.weapon_one_risk"
    assert launch["candidate_grain"] == "label_value"
    assert launch["field_value"] == "oneRiskLaunchLess10"
    assert launch["risk_hit_count"] == 7
    assert launch["risk_sample_count"] == 7
    assert launch["extraction_source"].startswith("manual_summary:")
    assert launch["extraction_confidence"] == "partial"
    assert launch["need_raw_confirm"] is True
    assert validate_candidate_schema(launch) == []


def test_e2e_contract_input_shape_is_supported(tmp_path: Path):
    raw = {
        "schema_version": "e2e_risk_observation_input_contract_v0_1",
        "case_id": "unit",
        "users": [
            {
                "user_id": "u1",
                "sample_role": "risk",
                "sources": {
                    "weapon_android": {
                        "raw_data": {
                            "source_name": "weapon_android",
                            "platform": "android",
                            "action": "raw_data",
                            "layer": "raw_data",
                            "source_status": "completed",
                            "raw_body_format": "json_object",
                            "raw_body": {
                                "device_id": "d1",
                                "cpuInfo": {"hw": "qcom"},
                                "accessibilitySvc": ["com.example/.Svc"],
                            },
                        },
                        "oneRisk": {
                            "source_name": "weapon_android",
                            "platform": "android",
                            "action": "oneRisk",
                            "layer": "oneRisk",
                            "source_status": "completed",
                            "raw_body_format": "json_object",
                            "raw_body": {
                                "device_id": "d1",
                                "weapon_one_risk": ["oneRiskNoSim"],
                                "resultSignals": {"modelDecision": "reject"},
                            },
                        },
                    }
                },
            }
        ],
    }
    path = tmp_path / "e2e_raw.json"
    path.write_text(json.dumps(raw), encoding="utf-8")

    candidates = candidates_from_raw_observations(path)
    keys = {
        (c["field_path"], c["field_value_or_pattern"], c["candidate_grain"], c["field_role_hint"])
        for c in candidates
    }

    assert ("weapon_android.raw_data.cpuInfo.hw", "qcom", "object_child_value", "factual_environment_label") in keys
    assert (
        "weapon_android.raw_data.accessibilitySvc",
        "com.example/.Svc",
        "array_element",
        "factual_device_label",
    ) in keys
    assert (
        "weapon_android.weapon_one_risk",
        "oneRiskNoSim",
        "label_value",
        "factual_device_label",
    ) in keys
    assert (
        "weapon_android.oneRisk.resultSignals.modelDecision",
        "reject",
        "object_child_value",
        "result_signal",
    ) in keys


def test_login_logcontent_json_unwraps_to_infra_fields(tmp_path: Path):
    raw = {
        "schema_version": "e2e_risk_observation_input_contract_v0_1",
        "users": [
            {
                "user_id": "u1",
                "sources": {
                    "infra_user_action_log": {
                        "login": {
                            "source_name": "infra_user_action_log",
                            "action": "login_logs_search",
                            "source_status": "completed",
                            "raw_body": {
                                "code": 0,
                                "data": {
                                    "logSearchModels": [
                                        {
                                            "index": 1,
                                            "logContent": json.dumps({
                                                "uri": "/rest/n/user/register/mobileV2",
                                                "did": "ANDROID_d1",
                                                "sid": "kuaishou.api",
                                                "params": json.dumps({
                                                    "appver": "14.5.10.1",
                                                    "net": "WIFI",
                                                    "androidApiLevel": "35",
                                                    "tokenId": "secret-token",
                                                }),
                                                "cookies": "secret-cookie",
                                            }),
                                        }
                                    ]
                                },
                            },
                        }
                    }
                },
            }
        ],
    }
    path = tmp_path / "login_raw.json"
    path.write_text(json.dumps(raw), encoding="utf-8")

    candidates = candidates_from_raw_observations(path)
    keys = {(c["source_name"], c["field_path"], c["field_value_or_pattern"]) for c in candidates}

    assert ("infra_user_action_log", "infra_user_action_log.uri", "/rest/n/user/register/mobileV2") in keys
    assert ("infra_user_action_log", "infra_user_action_log.did", "__anchor_value_redacted__") in keys
    assert (
        "infra_user_action_log",
        "infra_user_action_log.extra.extra.clientRequestInfo.appver",
        "14.5.10.1",
    ) in keys
    assert (
        "infra_user_action_log",
        "infra_user_action_log.extra.extra.clientRequestInfo.net",
        "WIFI",
    ) in keys
    api_level = next(
        c
        for c in candidates
        if c["field_path"] == "infra_user_action_log.extra.extra.clientRequestInfo.androidApiLevel"
    )
    assert api_level["feature_type"] == "numeric_bucket"
    assert api_level["field_value_or_pattern"] == ">=30"
    assert api_level["bucket_label"] == ">=30"
    assert api_level["baseline_mode"] == "baseline_supported"
    assert api_level["commonality_family"] == "numeric_bucket_commonality"
    assert not any("tokenId" in c["field_path"] for c in candidates)
    assert not any("cookies" in c["field_path"] for c in candidates)


def test_archives_user_analysis_maps_request_param_to_passport(tmp_path: Path):
    raw = {
        "schema_version": "e2e_risk_observation_input_contract_v0_1",
        "users": [
            {
                "user_id": "u1",
                "sources": {
                    "archives_user_analysis": {
                        "user_analysis": {
                            "source_name": "archives_user_analysis",
                            "action": "archives_user_analysis",
                            "source_status": "completed",
                            "raw_body": {
                                "data": {
                                    "dataList": [
                                        {
                                            "operateUri": "/rest/n/user/requestMobileCode",
                                            "appVersion": "14.0.40.46379",
                                            "deviceId": "ANDROID_d1",
                                            "photoInfo": "MOD:Xiaomi(22041216UC)\tSYS:11.0",
                                            "requestParam": json.dumps({
                                                "type": ["27"],
                                                "net": ["WIFI"],
                                                "androidApiLevel": ["35"],
                                                "accessToken": ["secret"],
                                            }),
                                            "extraParam": json.dumps({"clientPageCode": "page_a"}),
                                        }
                                    ]
                                }
                            },
                        }
                    }
                },
            }
        ],
    }
    path = tmp_path / "archives_raw.json"
    path.write_text(json.dumps(raw), encoding="utf-8")

    candidates = candidates_from_raw_observations(path)
    keys = {(c["source_name"], c["field_path"], c["field_value_or_pattern"]) for c in candidates}

    assert ("passport_action_log", "passport_action_log.uri", "/rest/n/user/requestMobileCode") in keys
    assert ("passport_action_log", "passport_action_log.app_ver", "14.0.40.46379") in keys
    assert ("passport_action_log", "passport_action_log.phone_mod", "Xiaomi(22041216UC)") in keys
    assert ("passport_action_log", "passport_action_log.sys_ver", ">=10") in keys
    assert ("passport_action_log", "passport_action_log.params.type", "27") in keys
    assert ("passport_action_log", "passport_action_log.params.net", "WIFI") in keys
    assert ("passport_action_log", "passport_action_log.params.androidApiLevel", ">=30") in keys
    assert ("passport_action_log", "passport_action_log.extra.clientPageCode", "page_a") in keys
    assert not any("accessToken" in c["field_path"] for c in candidates)


def test_unsupported_complex_value_marks_parser_needed(tmp_path: Path):
    raw = [
        {
            "source_name": "weapon_android",
            "action": "weapon_inventory",
            "user_id": "u1",
            "payload": {
                "raw_data": {
                    "accessibilitySvc": [{"pkg": "com.example", "svc": "Svc"}],
                }
            },
        }
    ]
    path = tmp_path / "complex.json"
    path.write_text(json.dumps(raw), encoding="utf-8")

    candidates = candidates_from_raw_observations(path)
    unsupported = next(c for c in candidates if c["field_value_or_pattern"] == "need_pattern_extractor:list_of_objects")

    assert unsupported["candidate_grain"] == "unsupported_complex_value"
    assert unsupported["feature_type"] == "derived_feature"
    assert unsupported["value_type"] == "unknown"
    assert unsupported["baseline_mode"] == "discovery_only"
    assert unsupported["commonality_family"] == "expanded_feature_commonality"
    assert unsupported["feature_definition_status"] == "missing"
    assert unsupported["commonality_evidence"] == []
    assert unsupported["parser_needed"] is True
    assert unsupported["extraction_confidence"] == "low"


def test_unknown_action_candidate_is_discovery_only_and_does_not_fake_normal(tmp_path: Path):
    raw = [
        {
            "source_name": "new_source",
            "action": "new_action",
            "user_id": "u1",
            "payload": {"durationMs": 12},
        }
    ]
    path = tmp_path / "new_source.json"
    path.write_text(json.dumps(raw), encoding="utf-8")

    candidates = candidates_from_raw_observations(path)
    candidate = next(c for c in candidates if c["field_path"] == "new_source.durationMs")

    assert candidate["feature_type"] == "numeric_bucket"
    assert candidate["field_value_or_pattern"] == ">=10"
    assert candidate["baseline_mode"] == "discovery_only"
    assert candidate["normal_hit_rate"] is None
    assert candidate["lift"] is None


def test_candidate_schema_validation_reports_missing_fields():
    errors = validate_candidate_schema({"candidate_id": "bad", "candidate_grain": "not_a_grain"})

    assert errors
    assert any("missing required fields" in e for e in errors)
    assert any("invalid candidate_grain" in e for e in errors)
