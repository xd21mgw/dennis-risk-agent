import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "l3_extraction"))

from candidate_replay_provenance import build_context_from_records
from p0_7_autonomous_cold_start_rerun import (
    blind_match_against_cleaned,
    build_autonomous_provenance,
    discover_account_endpoint_families,
    discover_network_environment,
    discover_social_funnel_buckets,
    replay_proposal,
)


def _row(user_id, source_action, parsed_path, value, raw_path=None, wave="wave_4"):
    return {
        "wave_id": wave,
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


def test_account_endpoint_family_discovery_uses_facts_not_cleaned_candidates():
    parsed = []
    for user_id in ("u1", "u2", "u3"):
        parsed.extend([
            _row(user_id, "archives_user_analysis", "upstream.body.data.dataList.operateUri", "/rest/n/user/reset/select"),
            _row(user_id, "archives_user_analysis", "upstream.body.data.dataList.operateUri", "/rest/n/user/rebind/mobile"),
            _row(user_id, "login_logs_search", "upstream.body.data.logSearchModels.logContent.uri", "/rest/n/user/set"),
        ])
    ctx = build_context_from_records(wave_id="wave_4", parsed_records=parsed)

    proposals = discover_account_endpoint_families(ctx)
    names = {proposal.candidate_name for proposal in proposals}

    assert "autonomous_account_mutation_endpoint_family" in names
    assert "autonomous_reset_password_endpoint_family" in names
    assert "autonomous_mobile_rebind_endpoint_family" in names
    assert all(proposal.candidate_id.startswith("p0_7:wave_4:") for proposal in proposals)


def test_internal_server_ip_idc_noise_is_not_network_candidate():
    parsed = []
    for user_id in ("u1", "u2", "u3"):
        parsed.append(_row(
            user_id,
            "login_logs_search",
            "upstream.body.data.logSearchModels.logContent.serverIp",
            "public-bjy-c58-kce-node307.idchb1az2.hb1.kwaidc.com(10.51.137.145)",
            wave="wave_5",
        ))
    ctx = build_context_from_records(wave_id="wave_5", parsed_records=parsed)

    proposals = discover_network_environment(ctx)

    assert proposals == []


def test_social_funnel_bucket_replay_and_autonomous_provenance():
    parsed = []
    for user_id, visit in (("u1", 10), ("u2", 700), ("u3", 900)):
        parsed.extend([
            _row(user_id, "weapon_inventory", "x.originalLog.user_behavior.enterProfileCnt180D", visit, wave="wave_5"),
            _row(user_id, "weapon_inventory", "x.originalLog.user_behavior.photoUploadCnt180D", 0, wave="wave_5"),
            _row(user_id, "weapon_inventory", "x.originalLog.user_behavior.watchingCommentCnt180D", 0, wave="wave_5"),
            _row(user_id, "weapon_inventory", "x.originalLog.user_behavior.caiPhotoCnt180D", 0, wave="wave_5"),
        ])
    ctx = build_context_from_records(wave_id="wave_5", parsed_records=parsed)

    proposals = discover_social_funnel_buckets(ctx)
    replayed = [replay_proposal(ctx, proposal) for proposal in proposals]
    provenance = build_autonomous_provenance(replayed)

    assert any(item["candidate_name"] == "autonomous_profile_visit_low_content_present_bucket" for item in replayed)
    assert all(item["original_discovery_source"] == "cold_start_autonomous" for item in provenance)
    assert all(item["current_candidate_source"] == "cold_start_autonomous" for item in provenance)
    assert all(item["can_count_as_autonomous_discovery"] for item in provenance)


def test_blind_match_is_evaluation_only_and_matches_by_fact_signature():
    autonomous = [
        {
            "candidate_id": "p0_7:wave_5:auto_network",
            "candidate_name": "autonomous_network_provider_asn_cluster",
            "wave_id": "wave_5",
            "signal_type": "environment_cluster",
            "involved_sources": ["weapon_inventory", "weapon_user_klink_status"],
            "involved_events": ["device_environment_event"],
            "normalized_paths": ["originalLog.oneIpInfo.isp"],
            "proposed_replay_rule": "provider/ASN evidence repeats across users",
            "rule_params": {"category": "provider_asn"},
        }
    ]
    cleaned = [
        {
            "candidate_id": "wave_5:zenlayer_asn_cluster",
            "candidate_name": "zenlayer_asn_cluster",
            "wave_id": "wave_5",
            "signal_type": "environment_cluster",
            "involved_sources": ["weapon_inventory"],
            "involved_events": ["device_environment_event"],
            "normalized_paths": ["riskDataResults.body.data.originalLog.oneIpInfo.isp"],
            "replay_rule": "parsed environment fields contain Zenlayer provider/ASN evidence",
            "field_thresholds": {"category_support_required": 1},
        }
    ]

    result = blind_match_against_cleaned(autonomous, cleaned)

    assert result["matched_to_cleaned_candidate_count"] == 1
    assert result["new_candidate_count"] == 0
    assert result["missed_cleaned_candidate_count"] == 0
