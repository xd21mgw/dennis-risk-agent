import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "l3_extraction"))

from candidate_replay_provenance import build_context_from_records
from p0_7_autonomous_cold_start_rerun import (
    discover_network_environment,
    infer_network_field_role,
    replay_proposal,
)


def _row(user_id, source_action, parsed_path, value, wave="wave_5", raw_path=None):
    return {
        "wave_id": wave,
        "user_id": user_id,
        "source_action": source_action,
        "raw_path": raw_path or "upstream.body.data",
        "parsed_path": parsed_path,
        "normalized_parsed_path": parsed_path,
        "value_preview": str(value),
        "value_shape": "string",
        "commonality_eligible": True,
        "parse_success": True,
    }


def test_sdk_config_key_and_sid_static_code_do_not_trigger_network_candidate():
    parsed = []
    for user_id in ("u1", "u2", "u3"):
        parsed.extend([
            _row(
                user_id,
                "login_logs_search",
                "upstream.body.data.logSearchModels.logContent.sdkConfig.confContent.kconf.key",
                "infraService.passportSdkSidConfig.adminInstitution",
                wave="wave_1",
            ),
            _row(
                user_id,
                "login_logs_search",
                "upstream.body.data.logSearchModels.logContent.sdkConfig.sidInStaticCode",
                "true",
                wave="wave_1",
            ),
        ])
    ctx = build_context_from_records(wave_id="wave_1", parsed_records=parsed)

    assert infer_network_field_role(parsed[0]) == "sdk_config_key"
    assert infer_network_field_role(parsed[1]) == "sdk_config_key"
    assert discover_network_environment(ctx) == []


def test_idc_substring_in_sdk_config_role_does_not_trigger_network_candidate():
    row = _row(
        "u1",
        "login_logs_search",
        "upstream.body.data.logSearchModels.logContent.sdkConfig.confContent.kconf.key",
        "infraService.someIdcLikeConfig",
        wave="wave_1",
    )

    assert infer_network_field_role(row) == "sdk_config_key"


def test_internal_server_client_ip_and_kwaidc_host_do_not_trigger_network_candidate():
    parsed = []
    for user_id in ("u1", "u2", "u3"):
        parsed.extend([
            _row(
                user_id,
                "login_logs_search",
                "upstream.body.data.logSearchModels.logContent.serverIp",
                "public-bjy-c58-kce-node307.idchb1az2.hb1.kwaidc.com(10.51.137.145)",
                wave="wave_1",
            ),
            _row(
                user_id,
                "login_logs_search",
                "upstream.body.data.logSearchModels.logContent.clientIp",
                "10.51.137.145",
                wave="wave_1",
            ),
        ])
    ctx = build_context_from_records(wave_id="wave_1", parsed_records=parsed)

    assert infer_network_field_role(parsed[0]) == "internal_platform_ip"
    assert infer_network_field_role(parsed[1]) == "internal_platform_ip"
    assert discover_network_environment(ctx) == []


def test_one_ip_info_asn_and_isp_trigger_provider_asn_cluster():
    parsed = []
    for user_id in ("u1", "u2", "u3"):
        parsed.extend([
            _row(
                user_id,
                "weapon_inventory",
                "upstream.body.riskDataResults.body.data.originalLog.oneIpInfo.asn",
                "AS21859",
                raw_path="upstream.body.riskDataResults.body.data",
            ),
            _row(
                user_id,
                "weapon_inventory",
                "upstream.body.riskDataResults.body.data.originalLog.oneIpInfo.isp",
                "Zenlayer",
                raw_path="upstream.body.riskDataResults.body.data",
            ),
        ])
    ctx = build_context_from_records(wave_id="wave_5", parsed_records=parsed)

    proposals = discover_network_environment(ctx)
    by_name = {proposal.candidate_name: proposal for proposal in proposals}

    assert infer_network_field_role(parsed[0]) == "network_asn"
    assert infer_network_field_role(parsed[1]) == "network_isp"
    assert "autonomous_network_provider_asn_cluster" in by_name
    assert replay_proposal(ctx, by_name["autonomous_network_provider_asn_cluster"])["support_user_count"] == 3


def test_explicit_idc_label_triggers_network_idc_cluster():
    parsed = []
    for user_id in ("u1", "u2", "u3"):
        parsed.extend([
            _row(
                user_id,
                "weapon_inventory",
                "upstream.body.riskDataResults.body.data.labelInfo.IPP.labels.labelDesc",
                "IDC机房网络",
                raw_path="upstream.body.riskDataResults.body.data",
            ),
            _row(
                user_id,
                "weapon_inventory",
                "upstream.body.riskDataResults.body.data.originalLog.oneIpInfo.scenes",
                "IDC",
                raw_path="upstream.body.riskDataResults.body.data",
            ),
        ])
    ctx = build_context_from_records(wave_id="wave_5", parsed_records=parsed)

    proposals = discover_network_environment(ctx)

    assert infer_network_field_role(parsed[0]) == "network_idc"
    assert infer_network_field_role(parsed[1]) == "network_idc"
    assert "autonomous_idc_network_supporting_cluster" in {p.candidate_name for p in proposals}


def test_track_location_hk_is_supporting_not_high_value():
    parsed = []
    for user_id in ("u1", "u2", "u3"):
        parsed.append(_row(
            user_id,
            "track_sequence_profile",
            "upstream.body.data.profile.firstLevelProfile.province",
            "香港",
        ))
    ctx = build_context_from_records(wave_id="wave_5", parsed_records=parsed)

    proposals = discover_network_environment(ctx)
    hk = [p for p in proposals if p.candidate_name == "autonomous_hk_location_supporting_cluster"]

    assert hk
    assert hk[0].candidate_level == "supporting"
    assert hk[0].signal_type == "environment_cluster"


def test_network_environment_cluster_requires_core_network_plus_supporting_evidence():
    parsed = []
    for user_id in ("u1", "u2", "u3"):
        parsed.extend([
            _row(
                user_id,
                "weapon_inventory",
                "upstream.body.riskDataResults.body.data.originalLog.oneIpInfo.asn",
                "AS21859",
                raw_path="upstream.body.riskDataResults.body.data",
            ),
            _row(
                user_id,
                "track_sequence_profile",
                "upstream.body.data.profile.firstLevelProfile.city",
                "香港",
            ),
        ])
    ctx = build_context_from_records(wave_id="wave_5", parsed_records=parsed)

    proposals = discover_network_environment(ctx)
    by_name = {proposal.candidate_name: proposal for proposal in proposals}

    assert "autonomous_network_provider_asn_cluster" in by_name
    assert "autonomous_hk_location_supporting_cluster" in by_name
    assert "autonomous_network_environment_combo_cluster" in by_name
    combo = replay_proposal(ctx, by_name["autonomous_network_environment_combo_cluster"])
    assert combo["support_user_count"] == 3
