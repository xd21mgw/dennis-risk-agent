import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from l3_extraction.l3_l4_candidate_pooling import (  # noqa: E402
    DISCOVERY_L5_PER_SOURCE_FIELD_FAMILY_TOPK,
    build_l4_review_outputs,
    pool_l3_candidates,
)


def _candidate(candidate_id, hit_count, hit_rate, grain="object_child_value", field="weapon_android.raw_data.x", value="v"):
    return {
        "candidate_id": candidate_id,
        "source_name": "weapon_android",
        "action_or_layer": "raw_data",
        "field_path": field,
        "field_value_or_pattern": value,
        "candidate_grain": grain,
        "field_role_hint": "unknown_need_review",
        "risk_hit_count": hit_count,
        "risk_observed_count": 6,
        "risk_hit_rate": hit_rate,
    }


def _card(candidate, decision, risk_hit_count=None, risk_hit_rate=None):
    return {
        "candidate_id": candidate["candidate_id"],
        "source_name": candidate["source_name"],
        "field_name": candidate["field_path"],
        "field_value_or_pattern": candidate["field_value_or_pattern"],
        "risk_observed_count": candidate["risk_observed_count"],
        "risk_hit_count": risk_hit_count if risk_hit_count is not None else candidate["risk_hit_count"],
        "risk_hit_rate": risk_hit_rate if risk_hit_rate is not None else candidate["risk_hit_rate"],
        "normal_field_coverage_ratio": 1.0,
        "normal_value_lookup_status": "value_not_found_in_top",
        "normal_value_distribution_reliable": False,
        "normal_hit_rate": 0.0,
        "statistical_strength": "medium",
        "semantic_clarity": "unknown",
        "leakage_risk": "none",
        "identifier_risk": "none",
        "l4_decision": decision,
        "recommended_next_action": "review",
    }


def test_l3_pooling_retains_commonality_and_anchors_but_not_singletons():
    candidates = [
        _candidate("single普通", 1, 0.1667),
        _candidate("common", 2, 0.3333),
        _candidate("anchor", 1, 0.1667, grain="high_cardinality_anchor"),
        _candidate("focus", 1, 0.1667, field="weapon_android.weapon_one_risk", value="oneRiskLaunchLess10"),
        _candidate("parser", 1, 0.1667, grain="unsupported_complex_value", value="need_pattern_extractor:list_of_objects"),
    ]

    pooled = pool_l3_candidates(candidates)

    retained_ids = {c["original_candidate_id"] for c in pooled["retained"]}
    watchlist_ids = {c["original_candidate_id"] for c in pooled["watchlist"]}

    assert "common" in retained_ids
    assert "anchor" in retained_ids
    assert "single普通" not in retained_ids
    assert "focus" in watchlist_ids
    assert "parser" in watchlist_ids
    assert pooled["dropped_count"] == 1


def test_l3_pooling_makes_candidate_ids_unique():
    candidates = [_candidate("dup", 2, 0.3333, value="a"), _candidate("dup", 2, 0.3333, value="b")]

    pooled = pool_l3_candidates(candidates)

    ids = [c["candidate_id"] for c in pooled["retained"]]
    assert len(ids) == len(set(ids))
    assert all(c["original_candidate_id"] == "dup" for c in pooled["retained"])


def test_l4_review_output_excludes_result_identifier_reject_and_keeps_reviewable():
    strong = _candidate("strong", 3, 0.5)
    weak = _candidate("weak", 3, 0.5)
    unobserved = _candidate("focus_unobserved", 1, 0.1667, field="weapon_android.weapon_one_risk", value="oneRiskLaunchLess10")
    reject = _candidate("reject", 6, 1.0)
    result = _candidate("result", 6, 1.0)
    retained = [strong, weak, unobserved, reject, result]
    cards = [
        _card(strong, "strong_single_candidate"),
        _card(weak, "weak_single_candidate"),
        _card(unobserved, "normal_unobserved_need_baseline"),
        _card(reject, "reject_or_hold"),
        _card(result, "result_signal_not_feature"),
    ]

    output = build_l4_review_outputs(cards, retained)
    review_ids = {c["candidate_id"] for c in output["l4_review_candidates"]}

    assert {"strong", "weak", "focus_unobserved"} <= review_ids
    assert "reject" not in review_ids
    assert "result" not in review_ids


def test_l4_review_filters_low_cardinality_incomplete_normal_distribution():
    candidate = _candidate("binary_miss", 6, 1.0, field="weapon_android.raw_data.frida", value="0")
    card = _card(candidate, "weak_single_candidate")
    card["normal_field_coverage_ratio"] = 0.98
    card["normal_value_lookup_status"] = "normal_value_distribution_incomplete"
    card["normal_value_distribution_reliable"] = False
    card["normal_hit_rate"] = None

    output = build_l4_review_outputs([card], [candidate])

    assert output["l4_review_candidates"] == []
    assert output["l4_review_summary"]["normal_value_distribution_incomplete_summary"]["count"] == 1


def test_l4_review_keeps_reliable_value_match_when_distribution_separates():
    candidate = _candidate("reliable_match", 6, 1.0, field="weapon_android.raw_data.some_flag", value="1")
    card = _card(candidate, "weak_single_candidate")
    card["normal_value_lookup_status"] = "value_matched"
    card["normal_value_distribution_reliable"] = True
    card["normal_hit_rate"] = 0.01

    output = build_l4_review_outputs([card], [candidate])

    assert [c["candidate_id"] for c in output["l4_review_candidates"]] == ["reliable_match"]


def test_l4_splits_baseline_supported_and_discovery_only_pools():
    baseline_candidate = _candidate("baseline", 3, 0.5, field="weapon_android.raw_data.cpuInfo.arch", value="arm64")
    discovery_candidate = _candidate("discovery", 3, 0.5, field="new_source.durationMs", value=">=10")
    discovery_candidate["source_name"] = "new_source"
    discovery_candidate["action_or_layer"] = "new_action"
    discovery_candidate["feature_type"] = "numeric_bucket"
    discovery_candidate["bucket_label"] = ">=10"
    cards = [
        _card(baseline_candidate, "weak_single_candidate"),
        _card(discovery_candidate, "weak_single_candidate"),
    ]
    cards[0]["normal_hit_rate"] = 0.05
    cards[0]["normal_value_lookup_status"] = "value_matched"
    cards[1]["normal_hit_rate"] = 0.0
    cards[1]["normal_value_lookup_status"] = "field_unobserved"

    output = build_l4_review_outputs(cards, [baseline_candidate, discovery_candidate])

    assert [c["candidate_id"] for c in output["baseline_supported_candidates"]] == ["baseline"]
    assert [c["candidate_id"] for c in output["discovery_only_candidates"]] == ["discovery"]
    discovery = output["discovery_only_candidates"][0]
    assert discovery["baseline_mode"] == "discovery_only"
    assert discovery["normal_hit_rate"] is None
    assert discovery["lift"] is None
    assert discovery["l5_usage"] == "experimental_strategy_draft"
    assert [c["candidate_id"] for c in output["l5_input_candidates"]] == ["baseline", "discovery"]
    assert output["l5_input_summary"]["formal_strategy_draft_count"] == 1
    assert output["l5_input_summary"]["experimental_strategy_draft_count"] == 1
    assert output["l4_review_summary"]["baseline_mode_distribution"] == {
        "baseline_supported": 1,
        "discovery_only": 1,
    }


def test_l4_marks_derived_feature_without_definition_audit_only():
    candidate = _candidate("derived_missing", 3, 0.5, field="new_source.derived.flag", value="pattern")
    candidate.update({
        "source_name": "new_source",
        "action_or_layer": "new_action",
        "feature_type": "derived_feature",
        "value_type": "unknown",
        "feature_definition": {},
        "feature_definition_status": "missing",
        "commonality_family": "expanded_feature_commonality",
        "commonality_evidence": [],
    })
    card = _card(candidate, "weak_single_candidate")
    card["normal_value_lookup_status"] = "field_unobserved"

    output = build_l4_review_outputs([card], [candidate])
    item = output["discovery_only_candidates"][0]

    assert item["baseline_mode"] == "discovery_only"
    assert item["l5_usage"] == "audit_only"
    assert item["l5_exclusion_reason"] == "derived_feature_missing_feature_definition"
    assert item["normal_hit_rate"] is None
    assert item["lift"] is None
    assert output["l5_input_candidates"] == []
    assert output["l5_input_summary"]["filtered_reason_distribution"]["derived_feature_missing_feature_definition"] == 1


def test_l4_bounds_discovery_only_before_l5_input():
    candidates = []
    cards = []
    for idx in range(DISCOVERY_L5_PER_SOURCE_FIELD_FAMILY_TOPK + 5):
        candidate = _candidate(
            f"disc_{idx}",
            3 + (idx % 3),
            0.5 + (idx % 3) * 0.1,
            field=f"new_source.same_family.leaf.child_{idx}",
            value=f"value_{idx}",
        )
        candidate.update({
            "source_name": "new_source",
            "action_or_layer": "new_action",
            "feature_type": "raw_field",
            "commonality_family": "field_value_commonality",
        })
        card = _card(candidate, "weak_single_candidate")
        card["normal_value_lookup_status"] = "field_unobserved"
        candidates.append(candidate)
        cards.append(card)

    output = build_l4_review_outputs(cards, candidates)

    l5_ids = {item["candidate_id"] for item in output["l5_input_candidates"]}
    assert len(l5_ids) == DISCOVERY_L5_PER_SOURCE_FIELD_FAMILY_TOPK
    assert output["l5_input_summary"]["discovery_only_l5_eligible_before_bound_count"] == DISCOVERY_L5_PER_SOURCE_FIELD_FAMILY_TOPK + 5
    assert output["l5_input_summary"]["discovery_only_l5_input_count"] == DISCOVERY_L5_PER_SOURCE_FIELD_FAMILY_TOPK
    assert output["l5_input_summary"]["filtered_reason_distribution"]["discovery_filtered_duplicate_same_source_field_family"] == 5
