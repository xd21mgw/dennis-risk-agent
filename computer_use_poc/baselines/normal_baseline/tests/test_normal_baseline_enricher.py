"""Tests for normal_baseline_enricher.py

Covers: batch enrich, debug lookup, baseline miss, high cardinality,
normal_status semantics, metadata passthrough, forbidden keys.
"""

import json
import os
import tempfile

import pytest

# Add src to path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from normal_baseline_enricher import (
    batch_enrich,
    debug_lookup,
    enrich_one_candidate,
    build_low_entropy_index,
    build_discrete_distribution_index,
    build_high_cardinality_index,
    FORBIDDEN_OUTPUT_KEYS,
    _compute_baseline_caveat,
    _compute_recommended_l4_use,
)

# ---- Fixtures ----

BASELINE_DIR = "/tmp/normal_baseline_layered_v0_2"


@pytest.fixture
def baseline_dir():
    """Provide baseline output directory if it exists."""
    if not os.path.exists(BASELINE_DIR):
        pytest.skip("Baseline output not found at %s" % BASELINE_DIR)
    return BASELINE_DIR


@pytest.fixture
def sample_candidates():
    """Sample L3 candidates covering different normal_status scenarios."""
    return [
        {
            "candidate_id": "c001",
            "source_name": "infra_user_action_log",
            "field_path": "infra_user_action_log.action_type",
            "field_value": "LOGIN",
            "risk_sample_count": 100,
            "risk_covered_count": 95,
            "risk_value_count": 60,
            "risk_value_ratio": 0.6,
        },
        {
            "candidate_id": "c002",
            "source_name": "passport_action_log",
            "field_path": "passport_action_log.status",
            "field_value": "SUCCESS",
            "risk_sample_count": 50,
            "risk_covered_count": 50,
            "risk_value_count": 48,
            "risk_value_ratio": 0.96,
        },
        {
            "candidate_id": "c003",
            "source_name": "infra_user_action_log",
            "field_path": "infra_user_action_log.server_ip",
            "field_value": "10.106.242.219",
            "risk_sample_count": 10,
            "risk_covered_count": 10,
            "risk_value_count": 8,
            "risk_value_ratio": 0.8,
        },
        {
            "candidate_id": "c004",
            "source_name": "infra_user_action_log",
            "field_path": "infra_user_action_log.extra.serviceToken.basicToken.did",
            "field_value": "abc123",
            "risk_sample_count": 5,
            "risk_covered_count": 5,
            "risk_value_count": 1,
            "risk_value_ratio": 0.2,
        },
        {
            "candidate_id": "c005",
            "source_name": "nonexistent_source",
            "field_path": "nonexistent_source.nonexistent_field",
            "field_value": "x",
            "risk_sample_count": 1,
            "risk_covered_count": 1,
            "risk_value_count": 1,
            "risk_value_ratio": 1.0,
        },
    ]


@pytest.fixture
def synthetic_baseline(tmp_path):
    """Create synthetic baseline data for unit tests."""
    # low_entropy_profile
    le = [
        {
            "source_name": "src_a",
            "field_path": "src_a.field_x",
            "field_value_norm": "src_a.field_x=TOP1",
            "profile_grain": "field_value",
            "normal_status": "normal_low_entropy",
            "top1_ratio": 0.95,
            "top3_ratio": 0.99,
            "coverage_ratio": 1.0,
            "covered_count": 1000,
            "sample_entity_count": 1000,
            "rule_source": "sample_frequency_rule_v0_1",
        },
        {
            "source_name": "src_a",
            "field_path": "src_a.field_y",
            "field_value_norm": "src_a.field_y=TOP1",
            "profile_grain": "field_value",
            "normal_status": "normal_not_popular_in_sample",
            "top1_ratio": 0.3,
            "top3_ratio": 0.6,
            "coverage_ratio": 1.0,
            "covered_count": 1000,
            "sample_entity_count": 1000,
            "rule_source": "sample_frequency_rule_v0_1",
        },
        {
            "source_name": "src_a",
            "field_path": "src_a.field_z",
            "field_value_norm": "src_a.field_z=TOP1",
            "profile_grain": "field_value",
            "normal_status": "normal_referenceable",
            "top1_ratio": 0.5,
            "top3_ratio": 0.8,
            "coverage_ratio": 0.5,
            "covered_count": 400,
            "sample_entity_count": 1000,
            "rule_source": "sample_frequency_rule_v0_1",
        },
    ]

    # discrete_field_distribution
    dd = [
        {
            "source_name": "src_a",
            "field_path": "src_a.field_x",
            "total_entity_count": 1000,
            "covered_entity_count": 1000,
            "coverage_ratio": 1.0,
            "distinct_value_count": 3,
            "top_values": [
                {"value": "A", "count": 950, "ratio": 0.95, "rank": 1},
                {"value": "B", "count": 30, "ratio": 0.03, "rank": 2},
                {"value": "C", "count": 20, "ratio": 0.02, "rank": 3},
            ],
            "other_value_count": 0,
            "other_value_ratio": 0.0,
            "top1_ratio": 0.95,
            "top3_ratio": 0.99,
        },
        {
            "source_name": "src_a",
            "field_path": "src_a.field_y",
            "total_entity_count": 1000,
            "covered_entity_count": 1000,
            "coverage_ratio": 1.0,
            "distinct_value_count": 10,
            "top_values": [
                {"value": "X", "count": 300, "ratio": 0.3, "rank": 1},
                {"value": "Y", "count": 200, "ratio": 0.2, "rank": 2},
                {"value": "Z", "count": 100, "ratio": 0.1, "rank": 3},
            ],
            "other_value_count": 400,
            "other_value_ratio": 0.4,
            "top1_ratio": 0.3,
            "top3_ratio": 0.6,
        },
    ]

    # high_cardinality_summary
    hc = [
        {
            "source_name": "src_a",
            "field_path": "src_a.field_hc",
            "distinct_value_count": 800,
            "unique_value_ratio": 0.9,
            "reuse_ratio": 0.1,
            "max_entities_per_value": 3,
            "top_reused_values": [
                {"value": "v1", "entity_count": 3},
            ],
        },
    ]

    # metadata
    meta = {
        "baseline_scope": "population_baseline",
        "sample_size_level": "initial_population_baseline",
        "not_login_aue_specific": True,
        "rule_source": "sample_frequency_rule_v0_1",
    }

    # Write to tmp_path
    with open(os.path.join(tmp_path, "normal_low_entropy_profile.json"), "w") as f:
        json.dump(le, f)
    with open(os.path.join(tmp_path, "normal_discrete_field_distribution.json"), "w") as f:
        json.dump(dd, f)
    with open(os.path.join(tmp_path, "high_cardinality_summary.json"), "w") as f:
        json.dump(hc, f)
    with open(os.path.join(tmp_path, "profiler_metadata.json"), "w") as f:
        json.dump(meta, f)

    return str(tmp_path)


# ---- Unit tests (synthetic baseline) ----

class TestBatchEnrichSynthetic:
    def test_batch_enrich_preserves_original_fields(self, synthetic_baseline):
        candidates = [
            {
                "candidate_id": "t1",
                "source_name": "src_a",
                "field_path": "src_a.field_x",
                "field_value": "A",
                "risk_sample_count": 100,
                "risk_covered_count": 90,
                "risk_value_count": 80,
                "risk_value_ratio": 0.8,
            }
        ]
        result = batch_enrich(candidates, synthetic_baseline)
        e = result["enriched_candidates"][0]
        assert e["candidate_id"] == "t1"
        assert e["risk_sample_count"] == 100
        assert e["risk_covered_count"] == 90
        assert e["risk_value_count"] == 80
        assert e["risk_value_ratio"] == 0.8

    def test_batch_enrich_output_count_matches_input(self, synthetic_baseline):
        candidates = [
            {"candidate_id": "t1", "source_name": "src_a", "field_path": "src_a.field_x", "field_value": "A",
             "risk_sample_count": 1, "risk_covered_count": 1, "risk_value_count": 1, "risk_value_ratio": 1.0},
            {"candidate_id": "t2", "source_name": "src_a", "field_path": "src_a.field_y", "field_value": "X",
             "risk_sample_count": 2, "risk_covered_count": 2, "risk_value_count": 2, "risk_value_ratio": 1.0},
            {"candidate_id": "t3", "source_name": "src_a", "field_path": "src_a.field_missing", "field_value": "Z",
             "risk_sample_count": 1, "risk_covered_count": 1, "risk_value_count": 1, "risk_value_ratio": 1.0},
        ]
        result = batch_enrich(candidates, synthetic_baseline)
        assert len(result["enriched_candidates"]) == 3
        assert result["enrichment_metadata"]["input_candidate_count"] == 3
        assert result["enrichment_metadata"]["output_enriched_count"] == 3

    def test_batch_enrich_normal_status_populated(self, synthetic_baseline):
        candidates = [
            {"candidate_id": "t1", "source_name": "src_a", "field_path": "src_a.field_x",
             "field_value": "A", "risk_sample_count": 1, "risk_covered_count": 1,
             "risk_value_count": 1, "risk_value_ratio": 1.0},
        ]
        result = batch_enrich(candidates, synthetic_baseline)
        e = result["enriched_candidates"][0]
        assert e["baseline_hit"] is True
        assert e["normal_status"] == "normal_low_entropy"
        assert e["normal_covered_count"] == 1000

    def test_batch_enrich_value_rank_found(self, synthetic_baseline):
        candidates = [
            {"candidate_id": "t1", "source_name": "src_a", "field_path": "src_a.field_x",
             "field_value": "A", "risk_sample_count": 1, "risk_covered_count": 1,
             "risk_value_count": 1, "risk_value_ratio": 1.0},
        ]
        result = batch_enrich(candidates, synthetic_baseline)
        e = result["enriched_candidates"][0]
        assert e["normal_value_rank"] == 1
        assert e["normal_value_count"] == 950
        assert e["normal_value_ratio"] == 0.95

    def test_batch_enrich_value_rank_not_in_top(self, synthetic_baseline):
        candidates = [
            {"candidate_id": "t1", "source_name": "src_a", "field_path": "src_a.field_x",
             "field_value": "NONEXISTENT_VALUE", "risk_sample_count": 1,
             "risk_covered_count": 1, "risk_value_count": 1, "risk_value_ratio": 1.0},
        ]
        result = batch_enrich(candidates, synthetic_baseline)
        e = result["enriched_candidates"][0]
        assert e["normal_value_count"] == 0
        assert e["normal_value_ratio"] == 0.0

    def test_baseline_miss_returns_gap(self, synthetic_baseline):
        candidates = [
            {"candidate_id": "t1", "source_name": "src_missing", "field_path": "src_missing.field_missing",
             "field_value": "x", "risk_sample_count": 1, "risk_covered_count": 1,
             "risk_value_count": 1, "risk_value_ratio": 1.0},
        ]
        result = batch_enrich(candidates, synthetic_baseline)
        e = result["enriched_candidates"][0]
        assert e["baseline_hit"] is False
        assert e["normal_status"] is None
        assert "baseline_gap" in e["baseline_caveat"]
        assert e["recommended_l4_use"] == "baseline_gap_no_judgement"

    def test_high_cardinality_field(self, synthetic_baseline):
        candidates = [
            {"candidate_id": "t1", "source_name": "src_a", "field_path": "src_a.field_hc",
             "field_value": "some_id", "risk_sample_count": 1, "risk_covered_count": 1,
             "risk_value_count": 1, "risk_value_ratio": 1.0},
        ]
        result = batch_enrich(candidates, synthetic_baseline)
        e = result["enriched_candidates"][0]
        assert e["baseline_hit"] is True
        assert e["high_cardinality"] is True
        assert e["normal_status"] == "high_cardinality_field"
        assert "high_cardinality" in e["baseline_caveat"]
        assert e.get("hc_distinct_value_count") == 800

    def test_normal_low_entropy_caveat_is_not_safe(self, synthetic_baseline):
        candidates = [
            {"candidate_id": "t1", "source_name": "src_a", "field_path": "src_a.field_x",
             "field_value": "A", "risk_sample_count": 1, "risk_covered_count": 1,
             "risk_value_count": 1, "risk_value_ratio": 1.0},
        ]
        result = batch_enrich(candidates, synthetic_baseline)
        e = result["enriched_candidates"][0]
        # normal_low_entropy: caveat should say "不代表安全"
        assert "不代表安全" in e["baseline_caveat"]
        assert e["recommended_l4_use"] == "downgrade_or_explain"

    def test_normal_not_popular_caveat_not_risk(self, synthetic_baseline):
        candidates = [
            {"candidate_id": "t1", "source_name": "src_a", "field_path": "src_a.field_y",
             "field_value": "X", "risk_sample_count": 1, "risk_covered_count": 1,
             "risk_value_count": 1, "risk_value_ratio": 1.0},
        ]
        result = batch_enrich(candidates, synthetic_baseline)
        e = result["enriched_candidates"][0]
        assert e["normal_status"] == "normal_not_popular_in_sample"
        assert "不等于风险" in e["baseline_caveat"]
        assert e["recommended_l4_use"] == "candidate_for_validation"

    def test_metadata_passthrough(self, synthetic_baseline):
        candidates = [
            {"candidate_id": "t1", "source_name": "src_a", "field_path": "src_a.field_x",
             "field_value": "A", "risk_sample_count": 1, "risk_covered_count": 1,
             "risk_value_count": 1, "risk_value_ratio": 1.0},
        ]
        result = batch_enrich(candidates, synthetic_baseline)
        e = result["enriched_candidates"][0]
        assert e["baseline_scope"] == "population_baseline"
        assert e["sample_size_level"] == "initial_population_baseline"
        assert e["not_login_aue_specific"] is True

    def test_enrichment_metadata_summary(self, synthetic_baseline):
        candidates = [
            {"candidate_id": "t1", "source_name": "src_a", "field_path": "src_a.field_x",
             "field_value": "A", "risk_sample_count": 1, "risk_covered_count": 1,
             "risk_value_count": 1, "risk_value_ratio": 1.0},
            {"candidate_id": "t2", "source_name": "src_missing", "field_path": "src_missing.field",
             "field_value": "x", "risk_sample_count": 1, "risk_covered_count": 1,
             "risk_value_count": 1, "risk_value_ratio": 1.0},
        ]
        result = batch_enrich(candidates, synthetic_baseline)
        meta = result["enrichment_metadata"]
        assert meta["baseline_hit_count"] == 1
        assert meta["baseline_miss_count"] == 1
        assert meta["high_cardinality_count"] == 0


class TestDebugLookup:
    def test_debug_lookup_returns_enriched(self, synthetic_baseline):
        result = debug_lookup(synthetic_baseline, "src_a", "src_a.field_x", "A")
        assert result["baseline_hit"] is True
        assert result["normal_status"] == "normal_low_entropy"
        assert result["debug_mode"] is True

    def test_debug_lookup_missing_field(self, synthetic_baseline):
        result = debug_lookup(synthetic_baseline, "src_missing", "src_missing.field")
        assert result["baseline_hit"] is False
        assert "baseline_gap" in result["baseline_caveat"]


class TestForbiddenKeys:
    def test_no_forbidden_keys_in_enriched(self, synthetic_baseline):
        candidates = [
            {"candidate_id": "t1", "source_name": "src_a", "field_path": "src_a.field_x",
             "field_value": "A", "risk_sample_count": 1, "risk_covered_count": 1,
             "risk_value_count": 1, "risk_value_ratio": 1.0},
        ]
        result = batch_enrich(candidates, synthetic_baseline)
        for e in result["enriched_candidates"]:
            for k in FORBIDDEN_OUTPUT_KEYS:
                assert k not in e, "Forbidden key '%s' found in enriched candidate" % k

    def test_forbidden_keys_stripped_even_if_source_has_them(self, synthetic_baseline):
        candidates = [
            {"candidate_id": "t1", "source_name": "src_a", "field_path": "src_a.field_x",
             "field_value": "A", "risk_sample_count": 1, "risk_covered_count": 1,
             "risk_value_count": 1, "risk_value_ratio": 1.0,
             "risk_judgement": "should_be_removed",
             "feature_candidate": "should_be_removed",
             "candidate_feature_decision": "should_be_removed",
             },
        ]
        result = batch_enrich(candidates, synthetic_baseline)
        e = result["enriched_candidates"][0]
        assert "risk_judgement" not in e
        assert "feature_candidate" not in e
        assert "candidate_feature_decision" not in e


class TestCaveatSemantics:
    def test_low_entropy_caveat(self):
        caveat = _compute_baseline_caveat("normal_low_entropy", False)
        assert "不代表安全" in caveat

    def test_popular_caveat(self):
        caveat = _compute_baseline_caveat("normal_popular", False)
        assert "不代表安全" in caveat

    def test_not_popular_caveat(self):
        caveat = _compute_baseline_caveat("normal_not_popular_in_sample", False)
        assert "不等于风险" in caveat

    def test_referenceable_caveat(self):
        caveat = _compute_baseline_caveat("normal_referenceable", False)
        assert "不做强判断" in caveat

    def test_observable_caveat(self):
        caveat = _compute_baseline_caveat("normal_observable", False)
        assert "不做强判断" in caveat

    def test_sparse_caveat(self):
        caveat = _compute_baseline_caveat("normal_sparse_or_low_coverage", False)
        assert "样本不足" in caveat

    def test_high_cardinality_caveat(self):
        caveat = _compute_baseline_caveat("high_cardinality_field", True)
        assert "high_cardinality" in caveat


class TestRecommendedL4Use:
    def test_low_entropy_recommendation(self):
        assert _compute_recommended_l4_use("normal_low_entropy", False) == "downgrade_or_explain"

    def test_not_popular_recommendation(self):
        assert _compute_recommended_l4_use("normal_not_popular_in_sample", False) == "candidate_for_validation"

    def test_sparse_recommendation(self):
        assert _compute_recommended_l4_use("normal_sparse_or_low_coverage", False) == "baseline_gap_no_judgement"

    def test_high_cardinality_recommendation(self):
        assert _compute_recommended_l4_use("high_cardinality_field", True) == "high_cardinality_reference_only"


# ---- Integration tests (real baseline output) ----

@pytest.mark.skipif(
    not os.path.exists(BASELINE_DIR),
    reason="Baseline output not found at %s" % BASELINE_DIR
)
class TestIntegrationWithRealBaseline:
    def test_batch_enrich_with_real_data(self, baseline_dir, sample_candidates):
        result = batch_enrich(sample_candidates, baseline_dir)
        assert len(result["enriched_candidates"]) == 5
        meta = result["enrichment_metadata"]
        assert meta["input_candidate_count"] == 5
        assert meta["output_enriched_count"] == 5
        # At least some baseline hits
        assert meta["baseline_hit_count"] > 0

    def test_action_type_lookup(self, baseline_dir):
        result = debug_lookup(baseline_dir, "infra_user_action_log",
                              "infra_user_action_log.action_type", "LOGIN")
        assert result["baseline_hit"] is True
        assert result["normal_status"] in [
            "normal_popular", "normal_low_entropy", "normal_not_popular_in_sample",
            "normal_referenceable", "normal_observable",
        ]

    def test_high_cardinality_did(self, baseline_dir):
        result = debug_lookup(baseline_dir, "infra_user_action_log",
                              "infra_user_action_log.extra.serviceToken.basicToken.did")
        assert result["baseline_hit"] is True
        assert result["high_cardinality"] is True

    def test_nonexistent_field_returns_gap(self, baseline_dir):
        result = debug_lookup(baseline_dir, "no_source", "no_source.no_field", "x")
        assert result["baseline_hit"] is False
        assert "baseline_gap" in result["baseline_caveat"]

    def test_no_forbidden_keys_in_real_enrichment(self, baseline_dir, sample_candidates):
        result = batch_enrich(sample_candidates, baseline_dir)
        for e in result["enriched_candidates"]:
            for k in FORBIDDEN_OUTPUT_KEYS:
                assert k not in e, "Forbidden key '%s' in enriched" % k

    def test_metadata_scope_in_real_enrichment(self, baseline_dir, sample_candidates):
        result = batch_enrich(sample_candidates, baseline_dir)
        for e in result["enriched_candidates"]:
            assert e["baseline_scope"] == "population_baseline"
            assert e["sample_size_level"] == "initial_population_baseline"
            assert e["not_login_aue_specific"] is True
