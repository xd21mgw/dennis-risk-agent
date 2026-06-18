import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "l3_extraction"))

from p0_7b_holdout_wave_rerun import audit_holdout_candidate, _container_status


def test_sdk_config_idc_substring_is_false_noisy_holdout_candidate():
    item = {
        "candidate_id": "p0_7:wave_1:autonomous_idc_network_supporting_cluster",
        "candidate_name": "autonomous_idc_network_supporting_cluster",
        "rule_type": "network_category_any_of",
        "candidate_level": "supporting",
        "support_user_count": 8,
        "coverage_user_count": 9,
        "schema_guard_conflict": False,
        "report_only_fields_used": [],
        "evidence_snippets": [
            {
                "source_action": "login_logs_search",
                "raw_path": "upstream.body.data",
                "parsed_path": "upstream.body.data.logSearchModels.logContent.sdkConfig.confContent.kconf.key",
                "normalized_path": "data.logSearchModels.logContent.sdkConfig.confContent.kconf.key",
                "value_summary": "infraService.passportSdkSidConfig.adminInstitution",
            }
        ],
    }

    audit = audit_holdout_candidate(item)

    assert audit["false_or_noisy"] is True
    assert audit["wave4_wave5_pattern_overfit"] is True
    assert audit["leakage_status"] == "suspicious"
    assert "sdk_config_idc_substring_false_positive" in audit["audit_reasons"]


def test_real_network_semantic_field_is_not_marked_as_sdk_config_noise():
    item = {
        "candidate_id": "p0_7:wave_1:autonomous_idc_network_supporting_cluster",
        "candidate_name": "autonomous_idc_network_supporting_cluster",
        "rule_type": "network_category_any_of",
        "candidate_level": "supporting",
        "support_user_count": 8,
        "coverage_user_count": 9,
        "schema_guard_conflict": False,
        "report_only_fields_used": [],
        "evidence_snippets": [
            {
                "source_action": "weapon_inventory",
                "raw_path": "upstream.body.riskDataResults.body.data.originalLog.oneIpInfo",
                "parsed_path": "upstream.body.riskDataResults.body.data.originalLog.oneIpInfo.isp",
                "normalized_path": "riskDataResults.body.data.originalLog.oneIpInfo.isp",
                "value_summary": "IDC network label",
            }
        ],
    }

    audit = audit_holdout_candidate(item)

    assert audit["false_or_noisy"] is False
    assert audit["wave4_wave5_pattern_overfit"] is False
    assert audit["leakage_status"] == "clean"


def test_container_status_distinguishes_app_list_raw_absent_data_gap():
    matrix = {
        "matrix": [
            {
                "container_name": "appList",
                "attempted": 0,
                "success": 0,
                "error": 0,
                "raw_present": False,
                "parse_attempted": 0,
                "parse_success": 0,
                "scanner_gap_reason": "raw_absent",
            }
        ]
    }

    status = _container_status(matrix, "appList")

    assert status["status"] == "DATA_GAP"
    assert status["scanner_gap_reason"] == "raw_absent"
