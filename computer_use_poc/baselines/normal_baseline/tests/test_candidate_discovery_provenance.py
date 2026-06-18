import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "l3_extraction"))

from candidate_discovery_provenance import (
    CandidateRule,
    TaxonomyInfo,
    build_candidate_discovery_provenance_payload,
    build_taxonomy_map_from_sanity,
    classify_candidate_provenance,
)


def _candidate(name, wave="wave_x", replay_status="replay_pass"):
    return {
        "candidate_id": f"{wave}:{name}",
        "candidate_name": name,
        "wave_id": wave,
        "replay_status": replay_status,
        "rule_semantics_status": "pass",
        "candidate_level": "high_value",
    }


def _cold_index(wave, feature_name):
    return {
        wave: {
            feature_name: [
                {
                    "_report_file": f"/tmp/{wave}_blind_discovery.json",
                    "_run_dir": "/tmp/cold",
                    "_section": "features",
                    "feature_name": feature_name,
                    "risk_semantic_type": "test_pattern",
                    "hit_count": 2,
                    "hit_rate": 1.0,
                    "evidence_path": ["source.field"],
                    "risk_reason": "cold-start test feature",
                }
            ]
        }
    }


def test_cold_start_original_candidate_can_count_as_autonomous():
    candidate = _candidate("auto_candidate")
    rule_map = {
        ("wave_x", "auto_candidate"): CandidateRule(cold_aliases=("auto_feature",)),
    }

    result = classify_candidate_provenance(
        candidate,
        cold_index=_cold_index("wave_x", "auto_feature"),
        rule_map=rule_map,
    )

    assert result["original_discovery_source"] == "cold_start_autonomous"
    assert result["current_candidate_source"] == "cold_start_autonomous"
    assert result["was_user_prompted"] is False
    assert result["can_count_as_autonomous_discovery"] is True


def test_user_prompted_candidate_is_targeted_not_autonomous():
    candidate = _candidate("targeted_candidate")
    rule_map = {
        ("wave_x", "targeted_candidate"): CandidateRule(
            current_candidate_source="user_challenge_regression",
            original_discovery_source="user_challenge_regression",
            related_user_challenge_id="CH-999",
        )
    }

    result = classify_candidate_provenance(
        candidate,
        cold_index={},
        registry_text="| CH-999 | user challenged field |",
        rule_map=rule_map,
    )

    assert result["original_discovery_source"] == "user_challenge_regression"
    assert result["current_candidate_source"] == "user_challenge_regression"
    assert result["was_user_prompted"] is True
    assert result["can_count_as_autonomous_discovery"] is False


def test_taxonomy_split_candidate_is_derived_and_keeps_parent():
    candidate = _candidate("reset_password_chain", wave="wave_4")
    taxonomy_map = {
        ("wave_4", "reset_password_chain"): TaxonomyInfo(
            parent_candidate_id="wave_4:account_reset_rebind_chain",
            parent_candidate_name="account_reset_rebind_chain",
            split_from="account_reset_rebind_chain",
            renamed_from="",
            reason="split broad account mutation candidate",
        )
    }
    rule_map = {
        ("wave_4", "reset_password_chain"): CandidateRule(cold_aliases=("reset_or_rebind_event_chain",)),
    }

    result = classify_candidate_provenance(
        candidate,
        cold_index=_cold_index("wave_4", "reset_or_rebind_event_chain"),
        taxonomy_map=taxonomy_map,
        rule_map=rule_map,
    )

    assert result["original_discovery_source"] == "cold_start_autonomous"
    assert result["current_candidate_source"] == "taxonomy_cleanup_derived"
    assert result["parent_candidate_id"] == "wave_4:account_reset_rebind_chain"
    assert result["split_from"] == "account_reset_rebind_chain"
    assert result["can_count_as_autonomous_discovery"] is False


def test_replay_pass_does_not_automatically_become_autonomous():
    candidate = _candidate("replay_only_unknown")

    result = classify_candidate_provenance(candidate, cold_index={})

    assert result["replay_status"] == "replay_pass"
    assert result["original_discovery_source"] == "unknown"
    assert result["current_candidate_source"] == "unknown"
    assert result["can_count_as_autonomous_discovery"] is False


def test_unknown_run_metadata_remains_unknown():
    candidate = _candidate("metadata_missing")

    payload = build_candidate_discovery_provenance_payload(
        replay_payload={"candidates": [candidate]},
        sanity_payload={"candidates": []},
        cold_index={},
        registry_text="",
        audit_text="",
        rule_map={},
        taxonomy_map={},
    )

    item = payload["candidates"][0]
    assert item["original_discovery_source"] == "unknown"
    assert item["current_candidate_source"] == "unknown"
    assert payload["summary"]["unknown_count"] == 1
    assert payload["summary"]["autonomous_count"] == 0


def test_can_count_as_autonomous_only_when_evidence_is_sufficient():
    auto = _candidate("auto_candidate")
    targeted = _candidate("targeted_candidate")
    rules = {
        ("wave_x", "auto_candidate"): CandidateRule(cold_aliases=("auto_feature",)),
        ("wave_x", "targeted_candidate"): CandidateRule(
            current_candidate_source="gap_focused_targeted",
            original_discovery_source="gap_focused_targeted",
            related_user_challenge_id="CH-100",
        ),
    }

    payload = build_candidate_discovery_provenance_payload(
        replay_payload={"candidates": [auto, targeted]},
        sanity_payload={"candidates": [auto, targeted]},
        cold_index=_cold_index("wave_x", "auto_feature"),
        registry_text="| CH-100 | targeted gap focused challenge |",
        audit_text="",
        rule_map=rules,
        taxonomy_map={},
    )

    assert payload["summary"]["autonomous_count"] == 1
    assert payload["summary"]["targeted_count"] == 1
    assert payload["summary"]["can_count_as_autonomous_discovery_candidates"] == ["auto_candidate"]


def test_build_taxonomy_map_from_sanity_handles_rename_and_split():
    candidates = [
        _candidate("account_mutation_chain", wave="wave_4"),
        _candidate("zenlayer_asn_cluster", wave="wave_5"),
    ]
    sanity = {
        "candidates_renamed": [
            {
                "old_candidate_name": "account_reset_rebind_chain",
                "new_candidate_names": ["account_mutation_chain"],
                "reason": "rename broad account rule",
            }
        ],
        "candidates_split": [
            {
                "old_candidate_name": "idc_hk_zenlayer_environment_cluster",
                "new_candidate_names": ["zenlayer_asn_cluster"],
                "reason": "split network rule",
            }
        ],
    }

    taxonomy = build_taxonomy_map_from_sanity(sanity, candidates)

    assert taxonomy[("wave_4", "account_mutation_chain")].renamed_from == "account_reset_rebind_chain"
    assert taxonomy[("wave_5", "zenlayer_asn_cluster")].split_from == "idc_hk_zenlayer_environment_cluster"
