import os
import sys

MODULE_DIR = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.abspath(MODULE_DIR))

from field_alignment_resolver import (  # noqa: E402
    align_realtime_to_offline,
    classify_field_role,
    resolve_field,
    resolve_source,
)


def test_login_source_alias_and_action_mapping():
    assert resolve_source("login_logs_search")["canonical_source"] == "infra_user_action_log"
    res = resolve_field("login_logs", "login_logs.action")
    assert res["canonical_source"] == "infra_user_action_log"
    assert res["canonical_field_path"] == "infra_user_action_log.action_type"
    assert res["field_role"] == "behavior_fact"
    assert res["match_type"] == "source_alias_field_match"


def test_passport_action_log_is_not_table_equivalent_or_excluded():
    res = resolve_source("passport_action_log")
    assert res["canonical_source"] == "passport_action_log"
    assert res["match_type"] == "exact_path_match"
    field = resolve_field("passport_action_log", "status")
    assert field["canonical_source"] == "passport_action_log"
    assert field["need_human_review"] is True


def test_weapon_seed_mapping_raw_data_android():
    for field, expected in {
        "arch": "weapon_android.raw_data.cpuInfo.arch",
        "asn": "weapon_android.raw_data.oneIpInfo.asn",
        "district": "weapon_android.raw_data.oneIpInfo.district",
        "hw": "weapon_android.raw_data.cpuInfo.hw",
        "qualcomm": "weapon_android.raw_data.sensorList.qualcomm",
        "scenes": "weapon_android.raw_data.oneIpInfo.scenes",
        "xiaomi": "weapon_android.raw_data.sensorList.xiaomi",
        "xiaomi_tz": "weapon_android.raw_data.vendorSecHw.xiaomi_tz",
        "xm4": "weapon_android.raw_data.vendorIds.xm4",
    }.items():
        res = align_realtime_to_offline("weapon_android", field)
        assert res["canonical_field_path"] == expected
        assert res["weapon_action"] == "raw_data"
        assert res["platform"] == "android"
        assert res["match_type"] == "seed_mapping_match"


def test_identifier_and_result_roles():
    assert classify_field_role("weapon_android", "weapon_android.raw_data.vendorIds.xm1")["field_role"] == "identifier_anchor"
    assert classify_field_role("weapon_android", "weapon_android.raw_data.vendorIds.xm3")["field_role"] == "identifier_anchor"
    did = classify_field_role("infra_user_action_log", "infra_user_action_log.extra.serviceToken.basicToken.did")
    device_id = classify_field_role("infra_user_action_log", "infra_user_action_log.extra.extra.deviceId")
    assert did["field_role"] == "identifier_anchor"
    assert did["cardinality_hint"] == "high"
    assert device_id["field_role"] == "identifier_anchor"
    assert device_id["cardinality_hint"] == "high"
    assert classify_field_role("weapon_android", "weapon_android.raw_data.weaponRisk.riskScore")["field_role"] == "result_signal"
    assert classify_field_role("weapon_android", "weapon_android.raw_data.weaponRisk.riskDecision")["field_role"] == "result_signal"
    assert classify_field_role("weapon_android", "weapon_android.raw_data.weaponRisk.modelDecision")["field_role"] == "result_signal"


def test_one_risk_factual_labels_not_result_signal():
    no_sim = classify_field_role("weapon_android", "weapon_android.raw_data.weaponRisk.oneRiskNoSim")
    launch = classify_field_role("weapon_android", "weapon_android.raw_data.weaponRisk.oneRiskLaunchLess10")
    assert no_sim["field_role"] == "factual_device_label"
    assert launch["field_role"] == "factual_device_label"
    assert no_sim["weapon_action"] == "oneRisk"
    assert launch["weapon_action"] == "oneRisk"


def test_service_kess_unresolved():
    res = resolve_field("login_logs_search", "serviceKess")
    assert res["canonical_field_path"] == "login_logs_search.serviceKess"
    assert res["match_type"] == "unresolved"
    assert res["unresolved_reason"] == "baseline_inventory_missing"
    assert res["need_human_review"] is True


def test_unresolved_gr9_fields_are_not_hard_mapped():
    for field in ("deviceRegisterCntCnt30d", "ams AG"):
        res = resolve_field("weapon_android", field)
        assert res["canonical_field_path"] == f"weapon_android.raw_data.{field}"
        assert res["field_role"] == "unknown_need_review"
        assert res["unresolved_reason"] == "baseline_inventory_missing"
        assert res["need_human_review"] is True
        assert res["can_use_for_l4_baseline"] is False
