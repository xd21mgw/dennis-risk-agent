import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
L3_DIR = BASE_DIR / "l3_extraction"
sys.path.insert(0, str(BASE_DIR))

from l3_extraction.candidate_protocol import apply_candidate_protocol
from l3_extraction.l3_l4_candidate_pooling import build_l4_review_outputs


def test_candidate_protocol_sets_discovery_and_baseline_status_fields():
    registry = {
        "baseline_actions": [{
            "field_source": "login_logs",
            "action_name": "login_logs_search",
            "baseline_available": True,
            "supports_value_distribution": True,
            "field_path_prefixes": ["request"],
        }]
    }

    baseline_supported = apply_candidate_protocol({
        "candidate_id": "raw_login_type",
        "source_name": "login_logs",
        "source_action": "login_logs_search",
        "field_path": "request.loginType",
        "field_value_or_pattern": "token",
        "risk_hit_count": 4,
        "risk_observed_count": 4,
        "risk_hit_rate": 1.0,
    }, registry)
    discovery_only = apply_candidate_protocol({
        "candidate_id": "derived_profile_chain",
        "feature_type": "derived_feature",
        "value_type": "sequence",
        "signal_type": "event_chain",
        "proposal_source": "protocol_test_fixture",
        "proposal_type": "behavioral_chain",
        "feature_name": "profile_mutation_chain",
        "feature_definition": {"rule": "profile_set AND profile_modify"},
        "source_fields": ["requestParam.operateType"],
        "risk_hit_count": 4,
        "risk_observed_count": 6,
        "risk_hit_rate": 0.6667,
    }, registry)

    assert baseline_supported["baseline_mode"] == "baseline_supported"
    assert baseline_supported["baseline_status"] == "normal_baseline_available"
    assert baseline_supported["next_step_suggestion"] == "replay_needed"
    assert baseline_supported["readiness"] == "needs_replay"
    assert baseline_supported["requires_l6_replay"] is True

    assert discovery_only["baseline_mode"] == "discovery_only"
    assert discovery_only["baseline_status"] == "not_applicable"
    assert discovery_only["normal_hit_rate"] is None
    assert discovery_only["lift"] is None
    assert discovery_only["commonality_level"] == "high"
    assert discovery_only["candidate_source"] == "protocol_test_fixture"
    assert discovery_only["signal_type"] == "event_chain"
    assert discovery_only["readiness"] == "needs_baseline_and_replay"
    assert discovery_only["next_step_suggestion"] == "baseline_and_replay_needed"


def test_l3_l4_pooling_preserves_protocol_metadata_without_l5_or_baseline():
    candidate = apply_candidate_protocol({
        "candidate_id": "derived_profile_chain",
        "source_name": "archives_user_analysis",
        "source_action": "archives_user_analysis",
        "action_or_layer": "archives_user_analysis",
        "feature_type": "derived_feature",
        "value_type": "sequence",
        "signal_type": "event_chain",
        "proposal_source": "protocol_test_fixture",
        "proposal_type": "behavioral_chain",
        "feature_name": "profile_mutation_chain",
        "feature_definition": {"rule": "profile_set AND profile_modify"},
        "source_fields": ["requestParam.operateType"],
        "commonality_evidence": [{"evidence_type": "behavior_pattern_commonality"}],
        "risk_hit_count": 4,
        "risk_observed_count": 6,
        "risk_hit_rate": 0.6667,
        "supporting_user_ids": ["u1", "u2", "u3", "u4"],
    })
    card = {
        "candidate_id": "derived_profile_chain",
        "source_name": "archives_user_analysis",
        "field_name": "requestParam.operateType",
        "field_value_or_pattern": "profile mutation chain",
        "risk_hit_count": 4,
        "risk_observed_count": 6,
        "risk_hit_rate": 0.6667,
        "normal_value_lookup_status": "value_not_found_in_top",
        "l4_decision": "normal_unobserved_need_baseline",
        "leakage_risk": "none",
        "identifier_risk": "none",
    }

    output = build_l4_review_outputs([card], [candidate])
    pool_item = output["discovery_only_candidates"][0]

    assert pool_item["candidate_id"] == "derived_profile_chain"
    assert pool_item["source_name"] == "archives_user_analysis"
    assert pool_item["source_action"] == "archives_user_analysis"
    assert pool_item["candidate_source"] == "protocol_test_fixture"
    assert pool_item["proposal_source"] == "protocol_test_fixture"
    assert pool_item["proposal_type"] == "behavioral_chain"
    assert pool_item["signal_type"] == "event_chain"
    assert pool_item["readiness"] == "needs_baseline_and_replay"
    assert pool_item["baseline_mode"] == "discovery_only"
    assert pool_item["baseline_status"] == "not_applicable"
    assert pool_item["normal_hit_rate"] is None
    assert pool_item["lift"] is None
    assert pool_item["requires_l6_replay"] is True


def test_protocol_core_does_not_import_excluded_modules():
    forbidden = (
        "l3_value_level_candidate_extractor",
        "commonality_proposal_validator",
        "dynamic_llm_semantic_discovery_runner",
        "llm_commonality_shadow_run",
        "code_assisted_commonality_runner",
        "semantic_feature_schema",
        "l5_value_path_candidate_generator",
        "normal_baseline_enricher",
        "runtime_case_execution_runner",
    )
    for path in (L3_DIR / "candidate_protocol.py", L3_DIR / "l3_l4_candidate_pooling.py"):
        import_lines = [
            line for line in path.read_text(encoding="utf-8").splitlines()
            if line.startswith("import ") or line.startswith("from ")
        ]
        joined = "\n".join(import_lines)
        for name in forbidden:
            assert name not in joined
