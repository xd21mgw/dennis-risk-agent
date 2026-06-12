#!/usr/bin/env python3
"""test_l4_candidate_validator.py — Unit tests for L4 candidate validator.

L4 = L3 单点候选 + normal baseline 的验证层。

Test categories:
1. normal_baseline_status classification
2. statistical_strength classification
3. semantic_clarity classification
4. leakage_risk classification
5. identifier_risk classification
6. l4_decision logic (all 7 decisions)
7. confidence calculation
8. missing_evidence and recommended_next_action
9. boundary rules enforcement
10. batch_validate integration
"""

import json
import os
import sys
import unittest

# Add parent to path
sys.path.insert(0, os.path.dirname(__file__))

from l4_candidate_validator import (
    L4_VERSION,
    batch_validate,
    classify_identifier_risk,
    classify_leakage_risk,
    classify_normal_baseline_status,
    classify_semantic_clarity,
    classify_statistical_strength,
    compute_confidence,
    compute_missing_evidence,
    compute_recommended_next_action,
    decide_l4_decision,
    normalize_field_path,
    infer_source_name,
    validate_one_candidate,
)


class TestNormalBaselineStatus(unittest.TestCase):
    """Test normal_baseline_status classification."""

    def test_unobserved_missing(self):
        self.assertEqual(
            classify_normal_baseline_status(0, 0, 0.5), "unobserved_missing")

    def test_insufficient_sample(self):
        self.assertEqual(
            classify_normal_baseline_status(100, 5, 0.5), "insufficient_sample")
        self.assertEqual(
            classify_normal_baseline_status(199, 10, 0.5), "insufficient_sample")

    def test_observed_negative_normal_high(self):
        # normal_hit_rate (0.5) >= risk_hit_rate (0.5) * 0.5 = 0.25 → observed_negative
        self.assertEqual(
            classify_normal_baseline_status(1000, 500, 0.5), "observed_negative")

    def test_observed_positive_normal_low(self):
        # normal_hit_rate (0.05) < risk_hit_rate (0.5) * 0.5 = 0.25 → observed_positive
        self.assertEqual(
            classify_normal_baseline_status(1000, 50, 0.5), "observed_positive")

    def test_observed_positive_boundary(self):
        # normal_hit_rate = 0.24, risk_hit_rate * 0.5 = 0.25 → 0.24 < 0.25 → observed_positive
        self.assertEqual(
            classify_normal_baseline_status(1000, 240, 0.5), "observed_positive")

    def test_observed_negative_boundary(self):
        # normal_hit_rate = 0.26, risk_hit_rate * 0.5 = 0.25 → 0.26 >= 0.25 → observed_negative
        self.assertEqual(
            classify_normal_baseline_status(1000, 260, 0.5), "observed_negative")


class TestStatisticalStrength(unittest.TestCase):
    """Test statistical_strength classification."""

    def test_high(self):
        self.assertEqual(
            classify_statistical_strength(0.8, "observed_positive", 0.2), "high")
        # delta=0.6 >= 0.3, risk >= 0.5

    def test_medium(self):
        self.assertEqual(
            classify_statistical_strength(0.4, "observed_positive", 0.2), "medium")
        # delta=0.2 >= 0.1, risk >= 0.3

    def test_low_negative(self):
        self.assertEqual(
            classify_statistical_strength(0.3, "observed_negative", 0.5), "low")

    def test_low_risk_below_threshold(self):
        self.assertEqual(
            classify_statistical_strength(0.1, "observed_positive", 0.05), "low")
        # risk_hit_rate < 0.3

    def test_unevaluable_unobserved(self):
        self.assertEqual(
            classify_statistical_strength(0.8, "unobserved_missing", None), "unevaluable")

    def test_unevaluable_insufficient(self):
        self.assertEqual(
            classify_statistical_strength(0.8, "insufficient_sample", 0.1), "unevaluable")

    def test_unevaluable_null_hit_rate(self):
        self.assertEqual(
            classify_statistical_strength(0.8, "observed_positive", None), "unevaluable")

    # v0.1.3: value-level not evaluated → cap at medium
    def test_value_not_evaluated_caps_at_medium(self):
        """v0.1.3: field_matched_but_value_not_evaluated → max medium."""
        # Would be high with full value-level, but capped at medium
        self.assertEqual(
            classify_statistical_strength(0.8, "observed_positive", 0.2,
                                         normal_value_lookup_status="field_matched_but_value_not_evaluated"),
            "medium")

    def test_value_matched_can_be_high(self):
        """v0.1.3: value_matched → full statistical strength allowed."""
        self.assertEqual(
            classify_statistical_strength(0.8, "observed_positive", 0.2,
                                         normal_value_lookup_status="value_matched"),
            "high")

    def test_value_not_found_in_top_caps_at_medium(self):
        """v0.1.3: value_not_found_in_top → max medium."""
        self.assertEqual(
            classify_statistical_strength(0.8, "observed_positive", 0.0,
                                         normal_value_lookup_status="value_not_found_in_top"),
            "medium")

    def test_high_cardinality_skipped_is_unevaluable(self):
        """v0.1.3: high_cardinality_skipped → unevaluable."""
        self.assertEqual(
            classify_statistical_strength(0.8, "observed_positive", 0.0,
                                         normal_value_lookup_status="high_cardinality_skipped"),
            "unevaluable")


class TestSemanticClarity(unittest.TestCase):
    """Test semantic_clarity classification."""

    def test_high_known_device(self):
        self.assertEqual(classify_semantic_clarity("weapon_android.raw_data.accessibilitySvc"), "high")
        self.assertEqual(classify_semantic_clarity("weapon_android.raw_data.phoneModel"), "high")

    def test_high_known_network(self):
        self.assertEqual(classify_semantic_clarity("login_log.ip"), "high")

    def test_medium_common_suffix(self):
        self.assertEqual(classify_semantic_clarity("some_source.someType"), "medium")

    def test_low_unrecognizable(self):
        self.assertEqual(classify_semantic_clarity("weapon_android.raw_data.f8a2b3c"), "low")

    def test_unknown_explicit(self):
        self.assertEqual(classify_semantic_clarity("any.field", is_unknown_field=True), "unknown")


class TestLeakageRisk(unittest.TestCase):
    """Test leakage_risk classification."""

    def test_confirmed_risk_decision(self):
        self.assertEqual(classify_leakage_risk("tianshi_rcp.risk_decision"), "confirmed")

    def test_confirmed_weapon_risk_container(self):
        """v0.1.1: weaponRisk as top-level field (container itself) still confirmed."""
        self.assertEqual(classify_leakage_risk("weapon_android.raw_data.weaponRisk"), "confirmed")

    def test_weaponrisk_subfield_conclusion(self):
        """v0.1.1: weaponRisk.riskScore (conclusion sub-label) → confirmed."""
        self.assertEqual(
            classify_leakage_risk("weapon_android.raw_data.weaponRisk.riskScore"), "confirmed")
        self.assertEqual(
            classify_leakage_risk("weapon_android.raw_data.weaponRisk.riskDecision"), "confirmed")
        # v0.1.1-hotfix: oneRiskMeetingTool is factual (detected app), not judgment
        self.assertEqual(
            classify_leakage_risk("weapon_android.raw_data.weaponRisk.oneRiskMeetingTool"), "none")

    def test_weaponrisk_subfield_factual(self):
        """v0.1.1: weaponRisk.noSim (factual sub-label) → none."""
        self.assertEqual(
            classify_leakage_risk("weapon_android.raw_data.weaponRisk.noSim"), "none")
        self.assertEqual(
            classify_leakage_risk("weapon_android.raw_data.weaponRisk.factoryReset"), "none")
        self.assertEqual(
            classify_leakage_risk("weapon_android.raw_data.weaponRisk.root"), "none")
        self.assertEqual(
            classify_leakage_risk("weapon_android.raw_data.weaponRisk.oneRiskNoSim"), "none")
        self.assertEqual(
            classify_leakage_risk("weapon_android.raw_data.weaponRisk.oneRiskBatteryZero"), "none")
        self.assertEqual(
            classify_leakage_risk("weapon_android.raw_data.weaponRisk.oneRiskLaunchLess10"), "none")
        # v0.1.1-hotfix: oneRisk* are factual descriptions, not risk judgments
        self.assertEqual(
            classify_leakage_risk("weapon_android.raw_data.weaponRisk.oneRiskAutoScript"), "none")
        self.assertEqual(
            classify_leakage_risk("weapon_android.raw_data.weaponRisk.oneRiskClickPlugin"), "none")
        self.assertEqual(
            classify_leakage_risk("weapon_android.raw_data.weaponRisk.oneRiskOnlineLoan"), "none")
        self.assertEqual(
            classify_leakage_risk("weapon_android.raw_data.weaponRisk.oneRiskIpIDC"), "none")
        self.assertEqual(
            classify_leakage_risk("weapon_android.raw_data.weaponRisk.oneRiskAccSvcAbilityCnt"), "none")

    def test_weaponrisk_subfield_unknown(self):
        """v0.1.1: weaponRisk.unknownLabel (not in either set) → possible."""
        self.assertEqual(
            classify_leakage_risk("weapon_android.raw_data.weaponRisk.someUnknownLabel"), "possible")

    def test_weapon_android_sibling_not_blocked(self):
        """v0.1.1: accessibilitySvc / cpuKernel in weapon_android NOT blocked by weaponRisk."""
        self.assertEqual(classify_leakage_risk("weapon_android.raw_data.accessibilitySvc"), "none")
        self.assertEqual(classify_leakage_risk("weapon_android.raw_data.cpuKernel"), "none")
        self.assertEqual(classify_leakage_risk("weapon_android.raw_data.deviceRegisterCntCnt30d"), "none")
        self.assertEqual(classify_leakage_risk("weapon_android.raw_data.rootCheck"), "none")
        self.assertEqual(classify_leakage_risk("weapon_android.raw_data.isEmulator"), "none")

    def test_labelinfo_container(self):
        """v0.1.1: labelInfo container also supported."""
        self.assertEqual(
            classify_leakage_risk("weapon_android.raw_data.labelInfo.noSim"), "none")
        self.assertEqual(
            classify_leakage_risk("weapon_android.raw_data.labelInfo.riskDecision"), "confirmed")

    def test_confirmed_policy_code(self):
        self.assertEqual(classify_leakage_risk("tianshi_rcp.policy_code"), "confirmed")

    def test_confirmed_event_type(self):
        self.assertEqual(classify_leakage_risk("tianshi_rcp.event_type"), "confirmed")

    def test_possible_risk_score(self):
        # risk_score is in RESULT_SIGNAL_FIELD_PATTERNS → confirmed, not possible
        self.assertEqual(classify_leakage_risk("weapon_android.raw_data.risk_score"), "confirmed")

    def test_none_behavioral(self):
        self.assertEqual(classify_leakage_risk("weapon_android.raw_data.accessibilitySvc"), "none")
        self.assertEqual(classify_leakage_risk("infra_user_action_log.action_type"), "none")
        self.assertEqual(classify_leakage_risk("weapon_android.raw_data.cpuKernel"), "none")

    # v0.1.2: source-aware action/result/decision tests
    def test_login_logs_action_not_blocked(self):
        """v0.1.2: login_logs.action is NOT a result signal (it's an operation type)."""
        self.assertEqual(
            classify_leakage_risk("login_logs.action", source_name="login_logs_search"), "none")
        self.assertEqual(
            classify_leakage_risk("login_logs_search.action", source_name="login_logs_search"), "none")

    def test_tianshi_action_is_blocked(self):
        """v0.1.2: tianshi_rcp.action IS a result signal (enforcement context)."""
        self.assertEqual(
            classify_leakage_risk("tianshi_rcp.action", source_name="tianshi_rcp"), "confirmed")

    def test_login_result_not_blocked(self):
        """v0.1.2: login_logs.result is NOT a result signal."""
        self.assertEqual(
            classify_leakage_risk("login_logs.result", source_name="login_logs_search"), "none")

    def test_tianshi_result_is_blocked(self):
        """v0.1.2: tianshi_rcp.result IS a result signal."""
        self.assertEqual(
            classify_leakage_risk("tianshi_rcp.result", source_name="tianshi_rcp"), "confirmed")

    def test_action_deny_value_in_enforcement(self):
        """v0.1.2: action=deny in enforcement path context → confirmed."""
        self.assertEqual(
            classify_leakage_risk("tianshi_rcp.action", field_value="deny",
                                 source_name="tianshi_rcp"), "confirmed")


class TestFieldAliasMapping(unittest.TestCase):
    """v0.1.2: Test field path normalization."""

    def test_short_name_expansion(self):
        self.assertEqual(normalize_field_path("arch"), "weapon_android.raw_data.cpuInfo.arch")
        self.assertEqual(normalize_field_path("xm1"), "weapon_android.raw_data.vendorIds.xm1")
        self.assertEqual(normalize_field_path("deviceRegisterCntCnt30d"),
                         "weapon_android.raw_data.deviceRegisterCntCnt30d")
        self.assertEqual(normalize_field_path("action"), "infra_user_action_log.action_type")
        # v0.1.3: nested container paths
        self.assertEqual(normalize_field_path("asn"), "weapon_android.raw_data.oneIpInfo.asn")
        self.assertEqual(normalize_field_path("district"), "weapon_android.raw_data.oneIpInfo.district")

    def test_canonical_path_passthrough(self):
        self.assertEqual(normalize_field_path("weapon_android.raw_data.arch"),
                         "weapon_android.raw_data.cpuInfo.arch")

    def test_source_prefix_infer(self):
        self.assertEqual(infer_source_name("weapon_android.raw_data.arch"), "weapon_android")
        self.assertEqual(infer_source_name("login_logs_search.action"), "infra_user_action_log")  # v0.1.3: confirmed source alias
        self.assertEqual(infer_source_name("infra_user_action_log.action_type"), "infra_user_action_log")

    def test_unknown_short_name(self):
        """Short name not in alias map → returned as-is."""
        self.assertEqual(normalize_field_path("unknownField"), "unknownField")


class TestIdentifierRisk(unittest.TestCase):
    """Test identifier_risk classification."""

    def test_confirmed_did(self):
        self.assertEqual(classify_identifier_risk("infra.extra.basicToken.did"), "confirmed")

    def test_confirmed_xm1(self):
        self.assertEqual(classify_identifier_risk("weapon_android.raw_data.xm1"), "confirmed")

    def test_confirmed_device_id(self):
        self.assertEqual(classify_identifier_risk("weapon_android.raw_data.device_id"), "confirmed")

    def test_confirmed_uuid(self):
        self.assertEqual(classify_identifier_risk("infra.extra.uuid"), "confirmed")

    def test_possible_id_suffix(self):
        self.assertEqual(classify_identifier_risk("infra.extra.some_id"), "possible")

    def test_none_regular_field(self):
        self.assertEqual(classify_identifier_risk("weapon_android.raw_data.accessibilitySvc"), "none")
        self.assertEqual(classify_identifier_risk("infra_user_action_log.action_type"), "none")

    # v0.1.1: bootId behavior/pattern boundary tests
    def test_bootId_behavior_pattern_gets_possible(self):
        """bootId with pattern/behavior keyword gets 'possible', not 'confirmed'."""
        self.assertEqual(
            classify_identifier_risk("weapon_android.raw_data.bootId",
                                     field_value_or_pattern="bootId_reset_frequency"),
            "possible")
        self.assertEqual(
            classify_identifier_risk("weapon_android.raw_data.bootId",
                                     field_value_or_pattern="high_stability"),
            "possible")

    def test_bootId_pure_value_gets_possible(self):
        """bootId is in IDENTIFIER_BEHAVIOR_EXEMPTIONS: even pure ID value gets 'possible'."""
        self.assertEqual(
            classify_identifier_risk("weapon_android.raw_data.bootId",
                                     field_value_or_pattern="b7c2e9f1"),
            "possible")

    def test_bootId_empty_value_gets_possible(self):
        """bootId in IDENTIFIER_BEHAVIOR_EXEMPTIONS: empty value → possible."""
        self.assertEqual(
            classify_identifier_risk("weapon_android.raw_data.bootId",
                                     field_value_or_pattern=""),
            "possible")

    def test_did_not_exempted(self):
        """did is NOT in IDENTIFIER_BEHAVIOR_EXEMPTIONS → still confirmed."""
        self.assertEqual(classify_identifier_risk("infra.extra.basicToken.did"), "confirmed")


class TestL4Decision(unittest.TestCase):
    """Test l4_decision logic — all 7 decision categories."""

    def test_strong_single_candidate(self):
        self.assertEqual(
            decide_l4_decision(
                statistical_strength="high", semantic_clarity="high",
                leakage_risk="none", identifier_risk="none",
                normal_baseline_status="observed_positive", risk_observed_count=10),
            "strong_single_candidate")

    def test_strong_with_medium_semantic(self):
        self.assertEqual(
            decide_l4_decision(
                statistical_strength="high", semantic_clarity="medium",
                leakage_risk="none", identifier_risk="none",
                normal_baseline_status="observed_positive", risk_observed_count=10),
            "strong_single_candidate")

    def test_weak_single_candidate(self):
        self.assertEqual(
            decide_l4_decision(
                statistical_strength="medium", semantic_clarity="high",
                leakage_risk="none", identifier_risk="none",
                normal_baseline_status="observed_positive", risk_observed_count=10),
            "weak_single_candidate")

    def test_semantic_unknown_but_strong_statistical(self):
        self.assertEqual(
            decide_l4_decision(
                statistical_strength="high", semantic_clarity="low",
                leakage_risk="none", identifier_risk="none",
                normal_baseline_status="observed_positive", risk_observed_count=10),
            "semantic_unknown_but_strong_statistical_candidate")

    def test_normal_unobserved(self):
        self.assertEqual(
            decide_l4_decision(
                statistical_strength="unevaluable", semantic_clarity="high",
                leakage_risk="none", identifier_risk="none",
                normal_baseline_status="unobserved_missing", risk_observed_count=10),
            "normal_unobserved_need_baseline")

    def test_normal_insufficient(self):
        self.assertEqual(
            decide_l4_decision(
                statistical_strength="unevaluable", semantic_clarity="high",
                leakage_risk="none", identifier_risk="none",
                normal_baseline_status="insufficient_sample", risk_observed_count=10),
            "normal_unobserved_need_baseline")

    def test_result_signal_confirmed(self):
        self.assertEqual(
            decide_l4_decision(
                statistical_strength="high", semantic_clarity="low",
                leakage_risk="confirmed", identifier_risk="none",
                normal_baseline_status="observed_positive", risk_observed_count=10),
            "result_signal_not_feature")

    def test_result_signal_possible(self):
        self.assertEqual(
            decide_l4_decision(
                statistical_strength="medium", semantic_clarity="medium",
                leakage_risk="possible", identifier_risk="none",
                normal_baseline_status="observed_positive", risk_observed_count=10),
            "result_signal_not_feature")

    def test_identifier_confirmed(self):
        self.assertEqual(
            decide_l4_decision(
                statistical_strength="high", semantic_clarity="low",
                leakage_risk="none", identifier_risk="confirmed",
                normal_baseline_status="observed_positive", risk_observed_count=10),
            "identifier_anchor_not_feature")

    def test_identifier_possible(self):
        self.assertEqual(
            decide_l4_decision(
                statistical_strength="medium", semantic_clarity="medium",
                leakage_risk="none", identifier_risk="possible",
                normal_baseline_status="observed_positive", risk_observed_count=10),
            "identifier_anchor_not_feature")

    def test_reject_or_hold_low_strength_negative(self):
        self.assertEqual(
            decide_l4_decision(
                statistical_strength="low", semantic_clarity="high",
                leakage_risk="none", identifier_risk="none",
                normal_baseline_status="observed_negative", risk_observed_count=100),
            "reject_or_hold")

    def test_reject_or_hold_tiny_sample(self):
        self.assertEqual(
            decide_l4_decision(
                statistical_strength="unevaluable", semantic_clarity="high",
                leakage_risk="none", identifier_risk="none",
                normal_baseline_status="unobserved_missing", risk_observed_count=2),
            "normal_unobserved_need_baseline")
        # risk_observed_count < 3 is handled after unobserved check

    def test_priority_leakage_over_identifier(self):
        """Leakage takes priority over identifier."""
        self.assertEqual(
            decide_l4_decision(
                statistical_strength="high", semantic_clarity="low",
                leakage_risk="confirmed", identifier_risk="confirmed",
                normal_baseline_status="observed_positive", risk_observed_count=10),
            "result_signal_not_feature")


class TestConfidence(unittest.TestCase):
    """Test confidence calculation."""

    def test_low_when_normal_zero(self):
        """normal_observed_count=0 MUST produce low confidence."""
        self.assertEqual(compute_confidence(0, "high", "strong_single_candidate"), "low")

    def test_low_for_result_signal(self):
        self.assertEqual(compute_confidence(1000, "high", "result_signal_not_feature"), "low")

    def test_low_for_identifier(self):
        self.assertEqual(compute_confidence(1000, "high", "identifier_anchor_not_feature"), "low")

    def test_high_for_strong_candidate(self):
        self.assertEqual(compute_confidence(1000, "high", "strong_single_candidate"), "high")

    def test_medium_for_weak(self):
        self.assertEqual(compute_confidence(1000, "medium", "weak_single_candidate"), "medium")

    def test_medium_for_semantic_unknown(self):
        self.assertEqual(
            compute_confidence(1000, "high", "semantic_unknown_but_strong_statistical_candidate"),
            "medium")

    def test_low_default(self):
        self.assertEqual(compute_confidence(1000, "low", "reject_or_hold"), "low")


class TestMissingEvidence(unittest.TestCase):
    """Test missing_evidence computation."""

    def test_unobserved_missing_baseline(self):
        missing = compute_missing_evidence(
            "normal_unobserved_need_baseline", "unobserved_missing", "high", "none", False)
        self.assertIn("normal_baseline_missing_for_this_field", missing)
        self.assertIn("build_normal_baseline_for_source", missing)

    def test_semantic_unknown_needs_mapping(self):
        missing = compute_missing_evidence(
            "semantic_unknown_but_strong_statistical_candidate", "observed_positive", "low", "none", False)
        self.assertIn("semantic_mapping_before_feature_naming", missing)
        self.assertIn("field_dictionary_or_semantic_mapping_needed", missing)

    def test_result_signal_needs_upstream(self):
        missing = compute_missing_evidence(
            "result_signal_not_feature", "observed_positive", "high", "none", False)
        self.assertIn("upstream_cause_feature_not_result_signal", missing)

    def test_identifier_needs_generation_evidence(self):
        missing = compute_missing_evidence(
            "identifier_anchor_not_feature", "observed_positive", "high", "confirmed", False)
        self.assertIn("generation_pattern_anomaly_evidence_if_used_as_feature", missing)

    def test_high_cardinality_adds_detail(self):
        missing = compute_missing_evidence(
            "identifier_anchor_not_feature", "unobserved_missing", "low", "confirmed", True)
        self.assertIn("high_cardinality_field_distribution_detail_needed", missing)


class TestRecommendedNextAction(unittest.TestCase):
    """Test recommended_next_action mapping."""

    def test_all_decisions_have_actions(self):
        decisions = [
            "strong_single_candidate", "weak_single_candidate",
            "semantic_unknown_but_strong_statistical_candidate",
            "normal_unobserved_need_baseline", "result_signal_not_feature",
            "identifier_anchor_not_feature", "reject_or_hold",
        ]
        for d in decisions:
            action = compute_recommended_next_action(d)
            self.assertTrue(len(action) > 0, "Missing action for %s" % d)
            # L4 actions must not reference L5+ directly as executable steps
            if d in ("normal_unobserved_need_baseline",):
                self.assertIn("baseline", action.lower())


class TestBoundaryRules(unittest.TestCase):
    """Test L4 boundary rule enforcement via validate_one_candidate."""

    def test_normal_zero_never_high_confidence(self):
        """Boundary: normal_observed_count=0 produces confidence=low."""
        card = validate_one_candidate({
            "candidate_id": "boundary_1",
            "source_name": "test",
            "field_path": "test.field",
            "field_value": "v",
            "risk_covered_count": 100,
            "risk_value_count": 80,
            "risk_value_ratio": 0.8,
            "normal_covered_count": 0,
            "normal_value_count": 0,
            "normal_value_ratio": None,
            "baseline_hit": False,
            "high_cardinality": False,
            "baseline_scope": "population_baseline",
            "baseline_caveat": "",
        })
        self.assertEqual(card["confidence"], "low")
        self.assertEqual(card["normal_baseline_status"], "unobserved_missing")

    def test_result_signal_not_feature(self):
        """Boundary: risk_decision field becomes result_signal_not_feature."""
        card = validate_one_candidate({
            "candidate_id": "boundary_2",
            "source_name": "tianshi_rcp",
            "field_path": "tianshi_rcp.risk_decision",
            "field_value": "deny",
            "risk_covered_count": 100,
            "risk_value_count": 100,
            "risk_value_ratio": 1.0,
            "normal_covered_count": 1000,
            "normal_value_count": 0,
            "normal_value_ratio": 0.0,
            "baseline_hit": True,
            "high_cardinality": False,
            "baseline_scope": "population_baseline",
            "baseline_caveat": "",
        })
        self.assertEqual(card["l4_decision"], "result_signal_not_feature")
        self.assertEqual(card["leakage_risk"], "confirmed")

    def test_identifier_anchor_not_feature(self):
        """Boundary: xm1 becomes identifier_anchor_not_feature."""
        card = validate_one_candidate({
            "candidate_id": "boundary_3",
            "source_name": "weapon_android",
            "field_path": "weapon_android.raw_data.xm1",
            "field_value": "abc123",
            "risk_covered_count": 100,
            "risk_value_count": 50,
            "risk_value_ratio": 0.5,
            "normal_covered_count": 0,
            "normal_value_count": 0,
            "normal_value_ratio": None,
            "baseline_hit": False,
            "high_cardinality": True,
            "baseline_scope": "population_baseline",
            "baseline_caveat": "",
        })
        self.assertEqual(card["l4_decision"], "identifier_anchor_not_feature")
        self.assertEqual(card["identifier_risk"], "confirmed")

    def test_not_final_conclusion_always_true(self):
        """Boundary: L4 cards always have not_final_conclusion=True."""
        card = validate_one_candidate({
            "candidate_id": "boundary_4",
            "source_name": "test",
            "field_path": "test.field",
            "field_value": "v",
            "risk_covered_count": 10,
            "risk_value_count": 8,
            "risk_value_ratio": 0.8,
            "normal_covered_count": 1000,
            "normal_value_count": 50,
            "normal_value_ratio": 0.05,
            "baseline_hit": True,
            "high_cardinality": False,
            "baseline_scope": "population_baseline",
            "baseline_caveat": "",
        })
        self.assertTrue(card["not_final_conclusion"])

    def test_candidate_type_hint_is_none(self):
        """Boundary: candidate_type_hint is reserved for L5, not filled by L4."""
        card = validate_one_candidate({
            "candidate_id": "boundary_5",
            "source_name": "test",
            "field_path": "test.field",
            "field_value": "v",
            "risk_covered_count": 10,
            "risk_value_count": 8,
            "risk_value_ratio": 0.8,
            "normal_covered_count": 1000,
            "normal_value_count": 50,
            "normal_value_ratio": 0.05,
            "baseline_hit": True,
            "high_cardinality": False,
            "baseline_scope": "population_baseline",
            "baseline_caveat": "",
        })
        self.assertIsNone(card["candidate_type_hint"])


class TestBatchValidate(unittest.TestCase):
    """Test batch_validate integration."""

    def test_batch_output_structure(self):
        result = batch_validate([
            {"candidate_id": "b1", "source_name": "test", "field_path": "test.field",
             "field_value": "v", "risk_covered_count": 10, "risk_value_count": 8,
             "risk_value_ratio": 0.8, "normal_covered_count": 1000, "normal_value_count": 50,
             "normal_value_ratio": 0.05, "baseline_hit": True, "high_cardinality": False,
             "baseline_scope": "population_baseline", "baseline_caveat": ""},
            {"candidate_id": "b2", "source_name": "test", "field_path": "test.risk_decision",
             "field_value": "deny", "risk_covered_count": 10, "risk_value_count": 10,
             "risk_value_ratio": 1.0, "normal_covered_count": 1000, "normal_value_count": 0,
             "normal_value_ratio": 0.0, "baseline_hit": True, "high_cardinality": False,
             "baseline_scope": "population_baseline", "baseline_caveat": ""},
        ])
        self.assertIn("l4_candidate_validation_cards", result)
        self.assertIn("l4_validation_summary", result)
        self.assertEqual(len(result["l4_candidate_validation_cards"]), 2)
        summary = result["l4_validation_summary"]
        self.assertEqual(summary["input_candidate_count"], 2)
        self.assertEqual(summary["output_card_count"], 2)
        self.assertIn("l4_decision_distribution", summary)
        self.assertIn("boundary_rules", summary)
        self.assertTrue(len(summary["boundary_rules"]) > 0)

    def test_l5_eligible_count(self):
        result = batch_validate([
            # strong candidate → L5 eligible
            {"candidate_id": "e1", "source_name": "weapon_android",
             "field_path": "weapon_android.raw_data.accessibilitySvc",
             "field_value": "auto.svc", "risk_covered_count": 10,
             "risk_value_count": 8, "risk_value_ratio": 0.8,
             "normal_covered_count": 1000, "normal_value_count": 30,
             "normal_value_ratio": 0.03, "baseline_hit": True,
             "high_cardinality": False, "baseline_scope": "population_baseline",
             "baseline_caveat": ""},
            # result signal → not L5 eligible
            {"candidate_id": "e2", "source_name": "tianshi_rcp",
             "field_path": "tianshi_rcp.risk_decision",
             "field_value": "deny", "risk_covered_count": 10,
             "risk_value_count": 10, "risk_value_ratio": 1.0,
             "normal_covered_count": 1000, "normal_value_count": 0,
             "normal_value_ratio": 0.0, "baseline_hit": True,
             "high_cardinality": False, "baseline_scope": "population_baseline",
             "baseline_caveat": ""},
            # identifier → not L5 eligible
            {"candidate_id": "e3", "source_name": "weapon_android",
             "field_path": "weapon_android.raw_data.xm1",
             "field_value": "abc", "risk_covered_count": 10,
             "risk_value_count": 5, "risk_value_ratio": 0.5,
             "normal_covered_count": 0, "normal_value_count": 0,
             "normal_value_ratio": None, "baseline_hit": False,
             "high_cardinality": True, "baseline_scope": "population_baseline",
             "baseline_caveat": ""},
        ])
        self.assertEqual(result["l4_validation_summary"]["l5_eligible_count"], 1)

    def test_sample_file_roundtrip(self):
        """Run batch_validate on the sample enriched candidates file."""
        sample_path = os.path.join(os.path.dirname(__file__),
                                   "l4_sample_enriched_candidates_v0_1.json")
        if not os.path.exists(sample_path):
            self.skipTest("Sample file not found: %s" % sample_path)
        with open(sample_path, "r", encoding="utf-8") as f:
            candidates = json.load(f)
        result = batch_validate(candidates)
        self.assertEqual(len(result["l4_candidate_validation_cards"]), 15)
        summary = result["l4_validation_summary"]
        self.assertEqual(summary["input_candidate_count"], 15)
        self.assertEqual(summary["output_card_count"], 15)
        # At least 1 L5 eligible
        self.assertGreaterEqual(summary["l5_eligible_count"], 1)
        # No high confidence when normal_observed_count=0
        for card in result["l4_candidate_validation_cards"]:
            if card["normal_observed_count"] == 0:
                self.assertEqual(card["confidence"], "low",
                    "candidate %s: normal_observed_count=0 but confidence=%s" % (
                        card["candidate_id"], card["confidence"]))


if __name__ == "__main__":
    unittest.main()
