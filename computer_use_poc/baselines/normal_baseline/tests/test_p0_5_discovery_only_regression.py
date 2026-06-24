import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from l3_extraction.l3_l4_candidate_pooling import build_l4_review_outputs  # noqa: E402
from l5_candidate_generation.l5_value_path_candidate_generator import (  # noqa: E402
    load_knowledge_base,
    load_l4_review_candidates,
    run_l5,
)


FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "p0_5_discovery_only_candidates.json"


def _load_fixture_candidates():
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    return payload["l3_candidates"]


def _card(candidate):
    return {
        "candidate_id": candidate["candidate_id"],
        "source_name": candidate["source_name"],
        "field_name": candidate["field_path"],
        "field_value_or_pattern": candidate["field_value_or_pattern"],
        "risk_observed_count": candidate["risk_observed_count"],
        "risk_hit_count": candidate["risk_hit_count"],
        "risk_hit_rate": candidate["risk_hit_rate"],
        "normal_field_coverage_ratio": 0.0,
        "normal_value_lookup_status": "field_unobserved",
        "normal_value_distribution_reliable": None,
        "normal_hit_rate": 0.0,
        "statistical_strength": "medium",
        "semantic_clarity": "unknown",
        "leakage_risk": "none",
        "identifier_risk": "none",
        "l4_decision": "weak_single_candidate",
        "recommended_next_action": "review",
    }


def _l4_output_from_fixture():
    candidates = _load_fixture_candidates()
    return build_l4_review_outputs([_card(c) for c in candidates], candidates)


def test_l4_routes_new_paths_to_discovery_only_with_null_normal_metrics():
    output = _l4_output_from_fixture()
    discovery = {item["candidate_id"]: item for item in output["discovery_only_candidates"]}

    assert set(discovery) == {"no_base_numeric", "valid_derived", "missing_derived", "unsupported_complex"}
    assert output["baseline_supported_candidates"] == []
    assert {item["candidate_id"] for item in output["l5_input_candidates"]} == {
        "no_base_numeric",
        "valid_derived",
    }
    for item in discovery.values():
        assert item["baseline_mode"] == "discovery_only"
        assert item["normal_hit_rate"] is None
        assert item["lift"] is None
        assert item["requires_l6_replay"] is True
    assert discovery["no_base_numeric"]["feature_type"] == "numeric_bucket"
    assert discovery["no_base_numeric"]["commonality_family"] == "numeric_bucket_commonality"


def test_l4_marks_missing_definition_derived_features_audit_only():
    output = _l4_output_from_fixture()
    discovery = {item["candidate_id"]: item for item in output["discovery_only_candidates"]}

    assert discovery["valid_derived"]["l5_usage"] == "experimental_strategy_draft"
    assert discovery["valid_derived"]["feature_definition_status"] == "present"
    assert discovery["valid_derived"]["commonality_evidence"]
    for candidate_id in ("missing_derived", "unsupported_complex"):
        assert discovery[candidate_id]["l5_usage"] == "audit_only"
        assert discovery[candidate_id]["l5_exclusion_reason"] == "derived_feature_missing_feature_definition"
        assert discovery[candidate_id]["feature_definition_status"] == "missing"


def test_l3_to_l4_preserves_new_commonality_feature_fields():
    output = _l4_output_from_fixture()
    discovery = {item["candidate_id"]: item for item in output["discovery_only_candidates"]}

    numeric = discovery["no_base_numeric"]
    assert numeric["feature_name"] == "new_behavior_source.durationMs#>=10"
    assert numeric["commonality_family"] == "numeric_bucket_commonality"
    assert numeric["bucket_label"] == ">=10"
    assert numeric["risk_hit_rate"] == 0.6667
    assert numeric["baseline_mode"] == "discovery_only"
    assert numeric["requires_l6_replay"] is True

    derived = discovery["valid_derived"]
    assert derived["feature_name"] == "short_window_profile_change"
    assert derived["commonality_family"] == "behavior_pattern_commonality"
    assert derived["commonality_level"] == "high"
    assert derived["feature_definition_status"] == "present"
    assert derived["feature_definition"]["rule"]
    assert derived["commonality_evidence"]
    assert derived["baseline_mode"] == "discovery_only"
    assert derived["requires_l6_replay"] is True


def test_l5_generates_experimental_strategy_only_for_valid_discovery_candidates():
    output = _l4_output_from_fixture()
    result = run_l5(output["l5_input_candidates"], load_knowledge_base())

    assert result["summary"]["value_node_count"] == 2
    assert {node["source_candidate_id"] for node in result["value_nodes"]} == {
        "no_base_numeric",
        "valid_derived",
    }
    assert result["l6_tasks"]
    for task in result["l6_tasks"]:
        assert task["baseline_mode"] == "discovery_only"
        assert task["strategy_draft_type"] == "experimental_strategy_draft"
        assert task["requires_l6_replay"] is True
        assert task["candidate_signal_level"] == "candidate_signal"
        assert "new_behavior_source.durationMs#>=10" in task["feature_names"]
        assert "short_window_profile_change" in task["feature_names"]
        assert "numeric_bucket" in task["feature_types"]
        assert "derived_feature" in task["feature_types"]
        assert "numeric_bucket_commonality" in task["commonality_families"]
        assert "behavior_pattern_commonality" in task["commonality_families"]
        assert ">=10" in task["bucket_labels"]
        assert any(defn and defn.get("rule") for defn in task["feature_definitions"])
        assert 0.6667 in task["risk_hit_rates"]
        assert 0.6667 in task["risk_hit_rates"]
        assert all(evidence is not None for evidence in task["commonality_evidence"])
    filter_reasons = output["l5_input_summary"]["filtered_reason_distribution"]
    assert filter_reasons["derived_feature_missing_feature_definition"] == 2


def test_formal_strategy_draft_is_not_emitted_for_discovery_only_fixture():
    output = _l4_output_from_fixture()
    result = run_l5(output["l5_input_candidates"], load_knowledge_base())

    assert all(task["strategy_draft_type"] != "formal_strategy_draft" for task in result["l6_tasks"])
    assert all(task["eval_request"]["eval_status"] == "not_run" for task in result["l6_tasks"])


def test_l5_loader_prefers_l5_input_candidates_over_review_candidates(tmp_path: Path):
    output = _l4_output_from_fixture()
    path = tmp_path / "l4_output.json"
    path.write_text(json.dumps(output), encoding="utf-8")

    loaded = load_l4_review_candidates(path)

    assert {item["candidate_id"] for item in loaded} == {"no_base_numeric", "valid_derived"}
