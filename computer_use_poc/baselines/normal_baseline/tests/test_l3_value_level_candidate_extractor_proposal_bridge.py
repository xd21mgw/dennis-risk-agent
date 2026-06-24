import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
L3_DIR = BASE_DIR / "l3_extraction"
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(L3_DIR))

from l3_extraction.candidate_protocol import apply_candidate_protocol  # noqa: E402
from l3_extraction.l3_value_level_candidate_extractor import (  # noqa: E402
    candidates_from_llm_proposal_payload,
    validate_candidate_schema,
)
from l3_extraction.proposal_record_utils import safe_preview, value_shape  # noqa: E402


def _proposal_payload():
    return {
        "action_or_source": "archives_user_analysis.archives_user_analysis",
        "proposal_count": 1,
        "proposals": [{
            "proposal_id": "p_profile_mutation_chain",
            "proposal_type": "behavioral_chain",
            "derived_feature_name": "profile_mutation_chain_from_proposal",
            "commonality_claim": "Most samples share profile mutation payload fields.",
            "commonality_family": "behavior_pattern_commonality",
            "value_type": "sequence",
            "description": "Profile mutation submission fields form a candidate chain.",
            "source_fields": ["requestParam.operateType", "requestParam.data.nickname"],
            "required_fields": ["requestParam.operateType", "requestParam.data.nickname"],
            "recompute_rule": "required_fields_present",
            "calculation_logic": "required_fields_present",
            "estimated_risk_hit_count": 7,
            "estimated_risk_denominator": 8,
            "estimated_risk_hit_rate": 0.875,
            "commonality_evidence": "Proposal estimate only; not replayed in L3 bridge.",
            "logic_reason": "Candidate needs replay before support can be trusted.",
            "risk_semantic_type": "content_publish_chain_pattern",
            "risk_semantic_reason": "Profile payload mutation may be risk relevant.",
            "dennis_lens_tags": ["profile_mutation"],
            "suggested_bucket_or_value": "profile_mutation_required_fields_present",
        }],
    }


def test_proposal_bridge_does_not_import_validator_or_broader_modules():
    path = L3_DIR / "l3_value_level_candidate_extractor.py"
    text = path.read_text(encoding="utf-8")
    forbidden = (
        "commonality_" + "proposal_" + "validator",
        "dynamic_llm_semantic_discovery_runner",
        "code_assisted_commonality_runner",
        "llm_commonality_shadow_run",
        "l5_value_path_candidate_generator",
        "runtime_case_execution_runner",
    )
    for name in forbidden:
        assert name not in text


def test_llm_proposal_converts_to_protocol_compatible_discovery_candidate(tmp_path):
    candidates = candidates_from_llm_proposal_payload(
        _proposal_payload(),
        extraction_source="llm_proposal_bridge:fixture:/tmp/raw.json",
        proposer_mode="fixture",
        raw_observation_path=tmp_path / "raw.json",
    )

    assert len(candidates) == 1
    candidate = candidates[0]
    assert validate_candidate_schema(candidate) == []
    assert apply_candidate_protocol(candidate)["candidate_id"] == candidate["candidate_id"]

    assert candidate["source"] == "llm_proposal"
    assert candidate["candidate_source"] == "llm_proposal"
    assert candidate["proposal_source"] == "llm_proposal"
    assert candidate["feature_type"] == "derived_feature"
    assert candidate["baseline_mode"] == "discovery_only"
    assert candidate["discovery_status"] == "discovery_only"
    assert candidate["readiness"] == "needs_replay"
    assert candidate["next_step_suggestion"] == "baseline_and_replay_needed"
    assert candidate["replay_required"] is True
    assert candidate["requires_l6_replay"] is True

    assert candidate["risk_hit_count"] == 0
    assert candidate["risk_hit_rate"] == 0.0
    assert candidate["supporting_user_ids"] == []
    assert candidate["support_estimate"]["status"] == "proposal_claim_not_recomputed"
    assert candidate["support_estimate"]["claimed_hit_count"] == 7
    assert candidate["support_estimate"]["claimed_denominator"] == 8
    assert candidate["proposal_provenance"]["support_estimate_status"] == "proposal_claim_not_recomputed"
    assert candidate["proposal_provenance"]["proposer_mode"] == "fixture"

    for replay_field in ("support_user_count", "miss_user_count", "sample_hits", "sample_misses"):
        assert replay_field not in candidate
    for verified_field in ("verified", "strategy_ready"):
        assert verified_field not in candidate
    assert candidate["baseline_status"] == "not_applicable"
    assert candidate["normal_hit_rate"] is None
    assert candidate["lift"] is None


def test_proposal_record_utils_remain_lightweight():
    assert value_shape({"a": 1}) == "dict"
    assert safe_preview({"token": "secret"}, path="root")["token"] == "[REDACTED:sensitive]"
