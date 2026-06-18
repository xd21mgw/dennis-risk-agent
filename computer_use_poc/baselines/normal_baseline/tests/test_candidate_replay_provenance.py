import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "l3_extraction"))

from candidate_replay_provenance import (
    app_list_gap_status,
    apply_schema_guard_policy,
    build_context_from_records,
    replay_account_mutation_chain,
    replay_candidates_for_context,
    replay_extreme_profile_visit_low_content_behavior,
    replay_hk_location_supporting,
    replay_idc_network_supporting,
    replay_high_profile_visit_low_content_behavior,
    replay_low_bootcount_with_track_high_duration,
    replay_network_environment_cluster,
    replay_profile_visit_low_content_behavior,
    replay_reset_and_rebind_chain,
    replay_zenlayer_asn_cluster,
    replay_weapon_decode_header_runtime_template,
)


def _row(user_id, source_action, parsed_path, value, raw_path=None):
    return {
        "wave_id": "wave_5",
        "user_id": user_id,
        "source_action": source_action,
        "raw_path": raw_path or parsed_path,
        "parsed_path": parsed_path,
        "normalized_parsed_path": parsed_path,
        "value_preview": str(value),
        "value_shape": "number" if isinstance(value, (int, float)) else "string",
        "commonality_eligible": True,
        "parse_success": True,
    }


def test_account_mutation_broader_rule_differs_from_reset_and_rebind_all_of():
    parsed = [
        _row("u1", "archives_user_analysis", "upstream.body.data.dataList.operateUri", "/rest/n/user/rebind/mobile"),
        _row("u1", "login_logs_search", "upstream.body.data.logSearchModels.logContent.uri", "/rest/n/user/reset/select"),
        _row("u2", "archives_user_analysis", "upstream.body.data.dataList.operateUri", "/rest/n/user/set"),
        _row("u2", "login_logs_search", "upstream.body.data.logSearchModels.logContent.uri", "/rest/n/user/login/token"),
    ]
    ctx = build_context_from_records(
        wave_id="wave_4",
        parsed_records=parsed,
        raw_records=[
            {"user_id": "u1", "source_action": "archives_user_analysis"},
            {"user_id": "u1", "source_action": "login_logs_search"},
            {"user_id": "u2", "source_action": "archives_user_analysis"},
        ],
    )

    broader = replay_account_mutation_chain(ctx)
    strict = replay_reset_and_rebind_chain(ctx)

    assert broader["candidate_name"] == "account_mutation_chain"
    assert broader["support_user_count"] == 2
    assert strict["candidate_name"] == "reset_and_rebind_chain"
    assert strict["rule_logic_type"] == "all_of"
    assert strict["support_user_count"] == 1
    assert strict["missing_reason_by_user"]["u2"] == "threshold_not_met"
    assert broader["support_user_count"] != strict["support_user_count"]


def test_template_candidate_requires_multiple_weapon_header_fields():
    parsed = [
        _row("u1", "weapon_inventory", "x.originalLog.weaponDecodeHeader.bootCount", 3),
        _row("u1", "weapon_inventory", "x.originalLog.weaponDecodeHeader.version", "1.0"),
        _row("u1", "weapon_inventory", "x.originalLog.weaponDecodeHeader.totalStorage", 128),
        _row("u1", "weapon_inventory", "x.originalLog.weaponDecodeHeader.brightness", 0),
        _row("u1", "weapon_inventory", "x.originalLog.weaponDecodeHeader.simulator", 0),
        _row("u1", "weapon_inventory", "x.originalLog.weaponDecodeHeader.root", 0),
        _row("u2", "weapon_inventory", "x.originalLog.weaponDecodeHeader.bootCount", 2),
        _row("u2", "weapon_inventory", "x.originalLog.weaponDecodeHeader.version", "1.0"),
    ]
    ctx = build_context_from_records(wave_id="wave_5", parsed_records=parsed)

    result = replay_weapon_decode_header_runtime_template(ctx)

    assert result["support_user_count"] == 1
    assert result["missing_reason_by_user"]["u2"] == "threshold_not_met"
    assert result["candidate_level"] == "high_value"
    assert result["replay_status"] == "replay_pass"


def test_profile_visit_buckets_keep_high_threshold_separate_from_present_threshold():
    parsed = [
        _row("u1", "weapon_inventory", "x.originalLog.user_behavior.enterProfileCnt180D", 5),
        _row("u1", "weapon_inventory", "x.originalLog.user_behavior.photoUploadCnt180D", 0),
        _row("u1", "weapon_inventory", "x.originalLog.user_behavior.watchingCommentCnt180D", 0),
        _row("u1", "weapon_inventory", "x.originalLog.user_behavior.caiPhotoCnt180D", 0),
        _row("u2", "weapon_inventory", "x.originalLog.user_behavior.enterProfileCnt180D", 600),
        _row("u2", "weapon_inventory", "x.originalLog.user_behavior.photoUploadCnt180D", 0),
        _row("u2", "weapon_inventory", "x.originalLog.user_behavior.watchingCommentCnt180D", 0),
        _row("u2", "weapon_inventory", "x.originalLog.user_behavior.caiPhotoCnt180D", 0),
        _row("u3", "weapon_inventory", "x.originalLog.user_behavior.enterProfileCnt180D", 900),
        _row("u3", "weapon_inventory", "x.originalLog.user_behavior.photoUploadCnt180D", 0),
        _row("u3", "weapon_inventory", "x.originalLog.user_behavior.watchingCommentCnt180D", 0),
        _row("u3", "weapon_inventory", "x.originalLog.user_behavior.caiPhotoCnt180D", 0),
        _row("u4", "weapon_inventory", "x.originalLog.user_behavior.enterProfileCnt180D", 1000),
        _row("u4", "weapon_inventory", "x.originalLog.user_behavior.photoUploadCnt180D", 8),
        _row("u4", "weapon_inventory", "x.originalLog.user_behavior.watchingCommentCnt180D", 0),
    ]
    ctx = build_context_from_records(wave_id="wave_5", parsed_records=parsed)

    present = replay_profile_visit_low_content_behavior(ctx)
    high = replay_high_profile_visit_low_content_behavior(ctx)
    extreme = replay_extreme_profile_visit_low_content_behavior(ctx)

    assert present["candidate_name"] == "profile_visit_low_content_behavior"
    assert present["field_thresholds"]["enterProfile_or_profileVisit_min"] == 1
    assert present["support_user_count"] == 3
    assert high["candidate_name"] == "high_profile_visit_low_content_behavior"
    assert high["field_thresholds"]["enterProfile_or_profileVisit_min"] == 500
    assert high["support_user_count"] == 2
    assert extreme["candidate_name"] == "extreme_profile_visit_low_content_behavior"
    assert extreme["field_thresholds"]["enterProfile_or_profileVisit_min"] == 800
    assert extreme["support_user_count"] == 1
    assert high["whether_candidate_name_matches_rule"] is True


def test_schema_guarded_field_cannot_standalone_high_value():
    evidence = [
        {
            "source_action": "login_logs_search",
            "raw_path": "boardPlatform",
            "parsed_path": "boardPlatform",
            "normalized_path": "boardPlatform",
            "value_summary": "kona",
        }
    ]
    guard = [
        {
            "path": "boardPlatform",
            "guard_level": "report_only",
            "guard_reason": "event_environment_context_only",
            "high_value_allowed": False,
            "combo_allowed": True,
        }
    ]

    level, high_value_allowed, guard_applied, report_only = apply_schema_guard_policy(
        candidate_level="high_value",
        evidence=evidence,
        matching_guards=guard,
    )

    assert level == "high_value"
    assert high_value_allowed is True
    assert guard_applied is True
    assert report_only == ["boardPlatform"]

    blocking_guard = [{**guard[0], "combo_allowed": False}]
    level, high_value_allowed, _, _ = apply_schema_guard_policy(
        candidate_level="high_value",
        evidence=evidence,
        matching_guards=blocking_guard,
    )
    assert level == "report_only"
    assert high_value_allowed is False


def test_low_bootcount_track_duration_marks_partial_lineage():
    parsed = [
        _row("u1", "weapon_inventory", "x.originalLog.weaponDecodeHeader.bootCount", 3),
        _row("u1", "track_sequence_get_use_duration", "upstream.body.data.rows.duration", 1440),
        _row("u2", "weapon_inventory", "x.originalLog.weaponDecodeHeader.bootCount", 3),
        _row("u2", "track_sequence_get_use_duration", "upstream.body.data.rows.duration", 300),
    ]
    ctx = build_context_from_records(wave_id="wave_5", parsed_records=parsed)

    result = replay_low_bootcount_with_track_high_duration(ctx)

    assert result["support_user_count"] == 1
    assert result["lineage_status"] == "partial_lineage"
    assert result["replay_status"] == "replay_partial"
    assert result["missing_reason_by_user"]["u2"] == "threshold_not_met"


def test_network_cluster_split_outputs_distinct_zenlayer_hk_idc_support():
    parsed = [
        _row("u1", "weapon_inventory", "x.originalLog.oneIpInfo.isp", "Zenlayer"),
        _row("u1", "weapon_inventory", "x.labelInfo.IPP.labels.labelName", "oneRiskIpIDC"),
        _row("u2", "weapon_inventory", "x.originalLog.oneIpInfo.isp", "Zenlayer"),
        _row("u3", "weapon_inventory", "x.originalLog.oneIpInfo.isp", "Zenlayer"),
    ]
    raw = [
        {"user_id": "u1", "source_action": "weapon_user_klink_status", "raw_path": "upstream.body.data.country_code", "value_preview": "HK"},
        {"user_id": "u2", "source_action": "weapon_user_klink_status", "raw_path": "upstream.body.data.country_code", "value_preview": "HK"},
        {"user_id": "u3", "source_action": "weapon_user_klink_status", "raw_path": "upstream.body.data.country_code", "value_preview": "SG"},
    ]
    ctx = build_context_from_records(wave_id="wave_5", parsed_records=parsed, raw_records=raw)

    zenlayer = replay_zenlayer_asn_cluster(ctx)
    hk = replay_hk_location_supporting(ctx)
    idc = replay_idc_network_supporting(ctx)
    combo = replay_network_environment_cluster(ctx)

    assert zenlayer["support_user_count"] == 3
    assert hk["support_user_count"] == 2
    assert hk["candidate_level"] == "supporting"
    assert idc["support_user_count"] == 1
    assert combo["support_user_count"] == 2
    assert combo["candidate_name"] == "network_environment_cluster"
    assert combo["rule_logic_type"] == "weighted"


def test_candidate_names_match_rules_after_taxonomy_cleanup():
    wave4 = build_context_from_records(
        wave_id="wave_4",
        parsed_records=[
            _row("u1", "archives_user_analysis", "x.operateUri", "/rest/n/user/rebind/mobile"),
            _row("u1", "login_logs_search", "x.logContent.uri", "/rest/n/user/reset/select"),
            _row("u2", "archives_user_analysis", "x.operateUri", "/rest/n/user/set"),
            _row("u2", "login_logs_search", "x.logContent.uri", "/rest/n/user/login/token"),
        ],
    )
    wave5 = build_context_from_records(
        wave_id="wave_5",
        parsed_records=[
            _row("u1", "weapon_inventory", "x.originalLog.weaponDecodeHeader.bootCount", 3),
            _row("u1", "weapon_inventory", "x.originalLog.weaponDecodeHeader.version", "1.0"),
            _row("u1", "weapon_inventory", "x.originalLog.weaponDecodeHeader.totalStorage", 128),
            _row("u1", "weapon_inventory", "x.originalLog.weaponDecodeHeader.brightness", 0),
            _row("u1", "weapon_inventory", "x.originalLog.weaponDecodeHeader.simulator", 0),
            _row("u1", "weapon_inventory", "x.originalLog.weaponDecodeHeader.root", 0),
        ],
    )

    candidates = replay_candidates_for_context(wave4) + replay_candidates_for_context(wave5)
    names = {candidate["candidate_name"] for candidate in candidates}

    assert "account_reset_rebind_chain" not in names
    assert "idc_hk_zenlayer_environment_cluster" not in names
    assert all(candidate["whether_candidate_name_matches_rule"] is True for candidate in candidates)
    assert all(candidate["rule_semantics_status"] == "pass" for candidate in candidates)


def test_app_list_raw_absent_is_data_gap_not_scanner_gap():
    ctx = build_context_from_records(
        wave_id="wave_5",
        parsed_records=[],
        container_rows=[
            {
                "container_name": "appList",
                "raw_present": False,
                "attempted": 0,
                "parse_attempted": 0,
                "parse_success": 0,
                "scanner_gap_reason": "raw_absent",
            }
        ],
    )

    assert app_list_gap_status(ctx) == "DATA_GAP"

    ctx = build_context_from_records(
        wave_id="wave_5",
        parsed_records=[],
        container_rows=[
            {
                "container_name": "appList",
                "raw_present": True,
                "attempted": 0,
                "parse_attempted": 0,
                "parse_success": 0,
                "scanner_gap_reason": "parser_missing",
            }
        ],
    )
    assert app_list_gap_status(ctx) == "SCANNER_GAP"
