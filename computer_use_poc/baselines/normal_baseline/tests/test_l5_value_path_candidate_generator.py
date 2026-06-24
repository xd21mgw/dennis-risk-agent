import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from l5_candidate_generation.l5_value_path_candidate_generator import (  # noqa: E402
    EVIDENCE_BOUNDARY,
    PATTERN_EVIDENCE_BOUNDARY,
    attach_prior_overlay,
    experimental_combo_filter_reason,
    load_knowledge_base,
    run_l5,
    strategy_fields_for_nodes,
)


def _candidate(candidate_id, field_path, value, sample_ids, decision="weak_single_candidate"):
    return {
        "candidate_id": candidate_id,
        "field_path": field_path,
        "field_value_or_pattern": value,
        "risk_hit_sample_ids": sample_ids,
        "support_count": len(sample_ids) if sample_ids is not None else 0,
        "risk_hit_count": len(sample_ids) if sample_ids is not None else 0,
        "risk_hit_rate": (len(sample_ids) / 6) if sample_ids else 0.0,
        "l4_decision": decision,
        "normal_value_distribution_reliable": True,
    }


def _kb():
    return load_knowledge_base()


def _normal(fields):
    return {
        "normal_baseline_status": "available",
        "field_count": len(fields),
        "fields": fields,
    }


def test_experimental_strategy_combo_bounds_block_four_feature_and_pure_discovery_three_feature():
    discovery_nodes = [{"baseline_mode": "discovery_only"} for _ in range(3)]
    mixed_nodes = [{"baseline_mode": "baseline_supported"}] + [{"baseline_mode": "discovery_only"} for _ in range(3)]
    bounded_mixed_nodes = [{"baseline_mode": "baseline_supported"}] + [{"baseline_mode": "discovery_only"} for _ in range(2)]

    pure = {"strategy_draft_type": "experimental_strategy_draft", **strategy_fields_for_nodes(discovery_nodes)}
    mixed_too_long = {"strategy_draft_type": "experimental_strategy_draft", **strategy_fields_for_nodes(mixed_nodes)}
    mixed_ok = {"strategy_draft_type": "experimental_strategy_draft", **strategy_fields_for_nodes(bounded_mixed_nodes)}

    assert experimental_combo_filter_reason(pure) == "pure_discovery_only_feature_count>2"
    assert experimental_combo_filter_reason(mixed_too_long) == "experimental_strategy_total_feature_count>3"
    assert experimental_combo_filter_reason(mixed_ok) == ""


def _field(distinct=100, entropy=0.8, value="v", rate=0.01, count=10):
    return {
        "normal_field_non_null_count": 1000,
        "normal_field_distinct_count": distinct,
        "normal_field_entropy": entropy * 8,
        "normal_field_entropy_normalized": entropy,
        "coverage_ratio": 1.0,
        "value_rates": {str(value).lower(): {"value": value, "ratio": rate, "count": count}},
    }


def test_normal_pair_generates_l6_task_with_threshold_override():
    candidates = [
        _candidate("ip", "risk.ip24", "123.45.67.*", ["u1", "u2", "u3", "u4"]),
        _candidate("model", "device.device_model", "Redmi_X", ["u1", "u2", "u3"]),
    ]

    result = run_l5(candidates, _kb())

    assert result["summary"]["l6_task_count"] >= 1
    pair = next(p for p in result["pair_candidates"] if p["anchor_field"] == "ip24" and p["target_field"] == "device_model")
    assert pair["pair_decision"] == "pass_to_path_expansion"
    assert pair["threshold_source"] == "anchor_override"
    assert pair["threshold_values"]["min_pair_conversion_rate"] == 0.65
    assert result["l6_tasks"][0]["candidate_signal_level"] == "candidate_signal"
    assert result["l6_tasks"][0]["evidence_boundary"] == EVIDENCE_BOUNDARY


def test_natural_relation_device_model_to_brand_skips_as_trivial():
    candidates = [
        _candidate("model", "device.device_model", "Redmi_X", ["u1", "u2", "u3", "u4"]),
        _candidate("brand", "device.brand", "Xiaomi", ["u1", "u2", "u3", "u4"]),
    ]

    result = run_l5(candidates, _kb())

    assert any(p["pair_decision"] == "skip_as_trivial" for p in result["pair_candidates"])
    assert result["summary"]["l6_task_count"] == 0


def test_too_coarse_ip24_is_contract_violation_and_no_l6_task():
    candidates = [
        _candidate("ip", "risk.ip24", "*", ["u1", "u2", "u3", "u4"]),
        _candidate("model", "device.device_model", "Redmi_X", ["u1", "u2", "u3", "u4"]),
    ]

    result = run_l5(candidates, _kb())

    assert any(p["pair_decision"] == "reject_bad_granularity" for p in result["pair_candidates"])
    assert any(v["violation_type"] == "bad_granularity_too_coarse" for v in result["contract_violations"])
    assert result["summary"]["l6_task_count"] == 0


def test_missing_risk_hit_sample_ids_goes_to_contract_violations():
    candidates = [_candidate("bad", "risk.ip24", "123.45.67.*", None)]

    result = run_l5(candidates, _kb())

    assert result["summary"]["value_node_count"] == 0
    assert result["contract_violations"]
    assert result["contract_violations"][0]["violation_type"] == "missing_risk_hit_sample_ids"
    assert result["summary"]["l6_task_count"] == 0


def test_unreliable_l4_normal_distribution_is_contract_violation():
    candidate = _candidate("bad_lookup", "weapon.raw_data.frida", "0", ["u1", "u2", "u3"])
    candidate["normal_value_distribution_reliable"] = False
    candidate["normal_value_lookup_status"] = "normal_value_distribution_incomplete"

    result = run_l5([candidate], _kb())

    assert any(v["violation_type"] == "normal_value_distribution_unreliable" for v in result["contract_violations"])
    assert result["summary"]["value_node_count"] == 0
    assert result["summary"]["l6_task_count"] == 0


def test_low_support_pair_is_held():
    candidates = [
        _candidate("ip", "risk.ip24", "123.45.67.*", ["u1", "u2"]),
        _candidate("model", "device.device_model", "Redmi_X", ["u1", "u2"]),
    ]

    result = run_l5(candidates, _kb())

    assert any(p["pair_decision"] == "hold_low_support" for p in result["pair_candidates"])
    assert result["summary"]["l6_task_count"] == 0


def test_path_expansion_prunes_low_conversion_and_does_not_revive():
    from l5_candidate_generation.l5_value_path_candidate_generator import build_path_record  # noqa: E402

    node_by_id = {
        "a": {"field_path": "src.a", "value_or_pattern": "A", "field_key": "a"},
        "b": {"field_path": "src.b", "value_or_pattern": "B", "field_key": "b"},
        "c": {"field_path": "src.c", "value_or_pattern": "C", "field_key": "c"},
    }
    record = build_path_record(
        ["a", "b", "c"],
        node_by_id,
        {"u1"},
        [1.0, 0.2],
        "pruned",
        "hold_low_conversion",
        previous_support_count=5,
        threshold_values={"min_support_samples": 3, "min_path_conversion_rate": 0.6},
        threshold_source="global",
    )

    assert record["path_decision"] == "pruned"
    assert record["prune_reason"] == "hold_low_conversion"


def test_every_l6_task_has_candidate_signal_boundary_not_verified_claim():
    candidates = [
        _candidate("ip", "risk.ip24", "123.45.67.*", ["u1", "u2", "u3", "u4"]),
        _candidate("model", "device.device_model", "Redmi_X", ["u1", "u2", "u3"]),
    ]

    result = run_l5(candidates, _kb())

    assert result["l6_tasks"]
    for task in result["l6_tasks"]:
        assert task["candidate_signal_level"] == "candidate_signal"
        assert task["evidence_boundary"] == EVIDENCE_BOUNDARY
        blob = str(task)
        assert "validated_feature" not in blob
        assert "confirmed_strategy" not in blob
        assert "production_rule" not in blob


def test_top_k_limits_l6_tasks_but_keeps_full_execution_candidates():
    kb = _kb()
    kb["top_k_selection"]["max_l6_tasks"] = 5
    kb["top_k_selection"]["include_uncertain_prior_limit"] = 50
    kb["top_k_selection"]["near_duplicate_jaccard_threshold"] = 1.1
    candidates = [
        _candidate(f"c{i}", f"src.field{i}", f"value{i}", [f"u{i}", "u_common1", "u_common2", "u_common3"])
        for i in range(12)
    ]

    result = run_l5(candidates, kb)

    assert result["summary"]["pair_candidate_count"] > result["summary"]["l6_task_count"]
    assert result["summary"]["l6_task_count"] == 5
    assert len(result["pair_candidates"]) == result["summary"]["pair_candidate_count"]
    assert result["summary"]["candidate_eval_queue_count"] >= result["summary"]["l6_task_count"]
    assert result["candidate_eval_queue"]


def test_value_ranking_prefers_high_support_specific_value_over_generic_brand():
    candidates = [
        _candidate("specific", "weapon.raw_data.accessibilitySvc", "com.app.service", ["u1", "u2", "u3", "u4", "u5"]),
        _candidate("brand", "weapon.raw_data.brand", "Xiaomi", ["u1", "u2", "u3"]),
    ]

    result = run_l5(candidates, _kb())
    nodes = {n["source_candidate_id"]: n for n in result["value_nodes"]}

    assert nodes["specific"]["value_score"] > nodes["brand"]["value_score"]
    assert nodes["brand"]["ranking_reason"]["over_generalization_penalty"] > 0


def test_unique_id_and_label_like_nodes_are_rejected_or_heavily_penalized():
    candidates = [
        _candidate("id", "profile.deviceId", "abc-123", ["u1", "u2", "u3"]),
        _candidate("policy", "rcp.hitPolicies", "BAN_POLICY", ["u1", "u2", "u3"]),
        _candidate("env", "weapon.raw_data.sensorList.xiaomi", "sensor-x", ["u1", "u2", "u3"]),
    ]

    result = run_l5(candidates, _kb())
    nodes = {n["source_candidate_id"]: n for n in result["value_nodes"]}

    assert nodes["id"]["role_suggestion"] == "reject_node"
    assert nodes["policy"]["role_suggestion"] == "reject_node"
    assert nodes["id"]["ranking_reason"]["uniqueness_penalty"] > 0
    assert nodes["policy"]["ranking_reason"]["label_leakage_penalty"] > 0


def test_uncertain_prior_anchor_quota_field_pair_quota_and_duplicates_limit_selection():
    kb = _kb()
    kb["top_k_selection"].update({
        "max_l6_tasks": 10,
        "per_anchor_max_tasks": 2,
        "per_field_pair_max_tasks": 2,
        "include_uncertain_prior_limit": 3,
        "near_duplicate_jaccard_threshold": 0.85,
        "min_pair_score": 0.0,
    })
    candidates = [
        _candidate("anchor", "src.anchor", "A", ["u1", "u2", "u3", "u4", "u5"]),
        _candidate("t1", "src.t1", "B1", ["u1", "u2", "u3", "u4"]),
        _candidate("t2", "src.t2", "B2", ["u1", "u2", "u3", "u5"]),
        _candidate("t3", "src.t3", "B3", ["u1", "u2", "u4", "u5"]),
        _candidate("dup1", "src.dup", "D1", ["u1", "u2", "u3", "u4"]),
        _candidate("dup2", "src.dup2", "D2", ["u1", "u2", "u3", "u4"]),
    ]

    result = run_l5(candidates, kb)
    decisions = [p["selection_decision"] for p in result["pair_candidates"]]

    assert "filtered_anchor_quota" in decisions
    assert "hold_uncertain_prior" in decisions
    assert "filtered_near_duplicate" in decisions


def test_field_pair_quota_limits_same_pair_family():
    kb = _kb()
    kb["top_k_selection"].update({
        "max_l6_tasks": 20,
        "per_anchor_max_tasks": 20,
        "per_field_pair_max_tasks": 1,
        "include_uncertain_prior_limit": 20,
        "near_duplicate_jaccard_threshold": 1.1,
        "min_pair_score": 0.0,
    })
    kb["field_pair_prior_config"].append({"anchor_field": "ip24", "target_field": "device_model", "prior": "normally_weak_related", "reason": "test"})
    candidates = [
        _candidate("ip1", "risk.ip24", "1.1.1.*", ["u1", "u2", "u3", "u4"]),
        _candidate("ip2", "risk.ip24", "2.2.2.*", ["u5", "u6", "u7", "u8"]),
        _candidate("m1", "device.device_model", "M1", ["u1", "u2", "u3"]),
        _candidate("m2", "device.device_model", "M2", ["u5", "u6", "u7"]),
    ]

    result = run_l5(candidates, kb)

    assert any(p["selection_decision"] == "filtered_field_pair_quota" for p in result["pair_candidates"])


def test_eval_request_fields_are_null_and_required_for_selected_tasks():
    candidates = [
        _candidate("ip", "risk.ip24", "123.45.67.*", ["u1", "u2", "u3", "u4"]),
        _candidate("model", "device.device_model", "Redmi_X", ["u1", "u2", "u3"]),
    ]

    result = run_l5(candidates, _kb())
    task = result["l6_tasks"][0]

    assert task["eval_request"]["need_candidate_eval"] is True
    assert task["eval_request"]["eval_status"] == "not_run"
    assert "global_base_rate" in task["eval_request"]["eval_required_fields"]
    assert task["in_sample_only_metrics"]["global_value_rate"] is None
    assert "Hive" in task["evidence_boundary"]
    assert "偏白" in task["evidence_boundary"]


def test_l5_strategy_draft_type_follows_baseline_mode_and_requires_l6_replay():
    formal_candidates = [
        {**_candidate("a", "weapon_android.raw_data.cpuInfo.arch", "arm64", ["u1", "u2", "u3", "u4"]), "baseline_mode": "baseline_supported"},
        {**_candidate("b", "weapon_android.raw_data.sensorList.xiaomi", "1", ["u1", "u2", "u3"]), "baseline_mode": "baseline_supported"},
    ]
    discovery_candidates = [
        {**_candidate("a", "new_source.durationMs", ">=10", ["u1", "u2", "u3", "u4"]), "baseline_mode": "discovery_only", "feature_type": "numeric_bucket", "value_type": "duration"},
        {**_candidate("b", "new_source.seq", "abc", ["u1", "u2", "u3"]), "baseline_mode": "discovery_only"},
    ]

    formal = run_l5(formal_candidates, _kb())
    discovery = run_l5(discovery_candidates, _kb())

    assert formal["l6_tasks"][0]["strategy_draft_type"] == "formal_strategy_draft"
    assert formal["l6_tasks"][0]["requires_l6_replay"] is True
    assert discovery["l6_tasks"][0]["strategy_draft_type"] == "experimental_strategy_draft"
    assert discovery["l6_tasks"][0]["baseline_mode"] == "discovery_only"
    assert discovery["l6_tasks"][0]["requires_l6_replay"] is True


def test_l5_rejects_explicit_raw_continuous_value_without_numeric_bucket():
    candidates = [
        {
            **_candidate("duration", "new_source.durationMs", "12", ["u1", "u2", "u3"]),
            "feature_type": "raw_field",
            "value_type": "duration",
        }
    ]

    result = run_l5(candidates, _kb())

    assert result["summary"]["value_node_count"] == 0
    assert any(v["violation_type"] == "continuous_value_requires_numeric_bucket" for v in result["contract_violations"])


def test_l5_rejects_derived_feature_without_feature_definition():
    candidates = [
        {
            **_candidate("derived", "new_source.derived.flag", "pattern", ["u1", "u2", "u3"]),
            "feature_type": "derived_feature",
            "value_type": "unknown",
            "baseline_mode": "discovery_only",
            "feature_definition": {},
            "feature_definition_status": "missing",
            "commonality_family": "expanded_feature_commonality",
            "commonality_evidence": [],
            "l5_usage": "audit_only",
        }
    ]

    result = run_l5(candidates, _kb())

    assert result["summary"]["value_node_count"] == 0
    assert any(v["violation_type"] == "derived_feature_missing_feature_definition" for v in result["contract_violations"])
    assert any(v["violation_type"] == "derived_feature_audit_only_not_l5_input" for v in result["contract_violations"])


def test_l5_allows_defined_derived_feature_as_experimental_strategy_draft():
    derived = {
        **_candidate("derived", "new_source.derived.behavior_pattern", "short_window_profile_change", ["u1", "u2", "u3", "u4"]),
        "feature_type": "derived_feature",
        "value_type": "sequence",
        "baseline_mode": "discovery_only",
        "feature_definition": {
            "rule": "count profile change events inside short window",
            "window": "risk_sample_window",
        },
        "feature_definition_status": "present",
        "source_fields": ["new_source.event_type", "new_source.event_ts"],
        "commonality_family": "behavior_pattern_commonality",
        "commonality_level": "high",
        "commonality_evidence": [
            {
                "evidence_type": "behavior_pattern_commonality",
                "risk_hit_count": 4,
                "risk_denominator": 6,
                "description": "4 risk samples share short-window profile change events",
            }
        ],
    }
    raw = {
        **_candidate("raw", "new_source.context.net", "WIFI", ["u1", "u2", "u3"]),
        "baseline_mode": "discovery_only",
    }

    result = run_l5([derived, raw], _kb())

    assert result["summary"]["value_node_count"] == 2
    assert result["l6_tasks"]
    assert result["l6_tasks"][0]["strategy_draft_type"] == "experimental_strategy_draft"
    assert result["l6_tasks"][0]["baseline_mode"] == "discovery_only"
    assert result["l6_tasks"][0]["requires_l6_replay"] is True


def test_pattern_abstraction_network_anchor_device_concentration():
    candidates = [
        _candidate("ip", "risk.ip24", "123.45.67.*", ["u1", "u2", "u3", "u4"]),
        _candidate("model", "device.device_model", "Redmi_X", ["u1", "u2", "u3"]),
    ]

    result = run_l5(candidates, _kb())
    patterns = result["pattern_candidates"]

    assert any(p["pattern_type"] == "network_anchor_device_concentration" for p in patterns)
    pattern = next(p for p in patterns if p["pattern_type"] == "network_anchor_device_concentration")
    assert pattern["evidence_boundary"] == PATTERN_EVIDENCE_BOUNDARY
    assert pattern["eval_request"]["eval_target_type"] == "pattern_level"
    assert "global_base_rate" in pattern["eval_request"]["eval_required_fields"]
    assert set(pattern["source_value_candidate_ids"]) == {"ip", "model"}
    assert any(pattern["pattern_candidate_id"] in task["related_pattern_candidate_ids"] for task in result["l6_tasks"])


def test_pattern_abstraction_environment_anchor_low_activity_device():
    candidates = [
        _candidate("sensor", "weapon.raw_data.sensorList.xiaomi", "1", ["u1", "u2", "u3", "u4"]),
        _candidate("launch", "weapon_android.weapon_one_risk", "oneRiskLaunchLess10", ["u1", "u2", "u3"]),
    ]

    result = run_l5(candidates, _kb())

    assert any(p["pattern_type"] == "environment_anchor_low_activity_device" for p in result["pattern_candidates"])


def test_pattern_abstraction_account_packaging_after_registration():
    kb = _kb()
    kb["top_k_selection"].update({"include_uncertain_prior_limit": 20, "min_pair_score": 0.0})
    candidates = [
        _candidate("nick", "profile.after_registration.nickname_modify", "1", ["u1", "u2", "u3", "u4"]),
        _candidate("avatar", "profile.after_registration.avatar_modify", "1", ["u1", "u2", "u3"]),
    ]

    result = run_l5(candidates, kb)

    assert any(p["pattern_type"] == "account_packaging_after_registration" for p in result["pattern_candidates"])


def test_pattern_candidate_is_candidate_signal_not_verified_claim():
    candidates = [
        _candidate("ip", "risk.ip24", "123.45.67.*", ["u1", "u2", "u3", "u4"]),
        _candidate("model", "device.device_model", "Redmi_X", ["u1", "u2", "u3"]),
    ]

    result = run_l5(candidates, _kb())
    assert result["pattern_candidates"]
    for pattern in result["pattern_candidates"]:
        assert pattern["candidate_signal_level"] == "candidate_signal"
        blob = str(pattern)
        assert "validated_feature" not in blob
        assert "confirmed_strategy" not in blob
        assert "production_rule" not in blob


def test_value_relation_candidate_outputs_relation_expression_metrics_and_thresholds():
    candidates = [
        _candidate("ip", "risk.ip24", "123.45.67.*", ["u1", "u2", "u3", "u4"]),
        _candidate("model", "device.device_model", "Redmi_X", ["u1", "u2", "u3"]),
    ]

    result = run_l5(candidates, _kb())
    task = result["l6_tasks"][0]

    assert task["candidate_kind"] == "value_relation_candidate"
    assert task["relation_level"] == "value_level"
    assert task["relation_expression"]["relation_type"] == "value_relation"
    assert task["relation_expression"]["path_length"] == 2
    assert "CNT(A_AND_B)" in task["relation_expression"]["logic"][0]
    assert task["observed_metrics"]["cnt_a"] == 4
    assert task["observed_metrics"]["cnt_b"] == 3
    assert task["observed_metrics"]["cnt_ab"] == 3
    assert task["observed_metrics"]["conversion_ab_over_a"] == 0.75
    assert task["observed_metrics"]["reverse_conversion_ab_over_b"] == 1.0
    assert task["thresholds"]["min_pair_conversion_rate"] == 0.65


def test_value_relation_does_not_duplicate_and_or_arrow_candidate_family():
    candidates = [
        _candidate("ip", "risk.ip24", "123.45.67.*", ["u1", "u2", "u3", "u4"]),
        _candidate("model", "device.device_model", "Redmi_X", ["u1", "u2", "u3"]),
    ]

    result = run_l5(candidates, _kb())

    assert len(result["pair_candidates"]) == 1
    pair = result["pair_candidates"][0]
    assert pair["candidate_kind"] == "value_relation_candidate"
    assert pair["observed_metrics"]["conversion_ab_over_a"] == 0.75
    assert pair["observed_metrics"]["reverse_conversion_ab_over_b"] == 1.0


def test_pattern_relation_candidate_outputs_relation_expression_metrics_and_thresholds():
    candidates = [
        _candidate("sensor", "weapon.raw_data.sensorList.xiaomi", "1", ["u1", "u2", "u3", "u4"]),
        _candidate("launch", "weapon_android.weapon_one_risk", "oneRiskLaunchLess10", ["u1", "u2", "u3"]),
    ]

    result = run_l5(candidates, _kb())
    pattern = result["pattern_candidates"][0]

    assert pattern["candidate_kind"] == "pattern_relation_candidate"
    assert pattern["relation_level"] == "pattern_level"
    assert pattern["relation_expression"]["relation_type"] == "pattern_relation"
    assert pattern["relation_expression"]["path_length"] == 2
    assert "CNT(A_AND_B)" in pattern["relation_expression"]["logic"][0]
    assert pattern["observed_metrics"]["cnt_ab"] == 3
    assert "min_pair_conversion_rate" in pattern["thresholds"]


def test_three_hop_relation_expression_uses_incremental_next_hop_logic():
    node_by_id = {
        "a": {"field_path": "src.a", "value_or_pattern": "A", "field_key": "a"},
        "b": {"field_path": "src.b", "value_or_pattern": "B", "field_key": "b"},
        "c": {"field_path": "src.c", "value_or_pattern": "C", "field_key": "c"},
    }
    from l5_candidate_generation.l5_value_path_candidate_generator import build_path_record  # noqa: E402

    record = build_path_record(
        ["a", "b", "c"],
        node_by_id,
        {"u1", "u2", "u3"},
        [1.0, 0.75],
        "pass_to_l6",
        None,
        previous_support_count=4,
        threshold_values={"min_support_samples": 3, "min_path_conversion_rate": 0.6},
        threshold_source="global",
    )

    assert record["relation_expression"]["path_length"] == 3
    assert record["relation_expression"]["logic"] == [
        "CNT(A_AND_B_AND_C) >= min_path_support",
        "CNT(A_AND_B_AND_C) / CNT(A_AND_B) >= min_next_hop_conversion_rate",
    ]
    assert record["observed_metrics"]["cnt_previous_path"] == 4
    assert record["observed_metrics"]["cnt_full_path"] == 3
    assert record["thresholds"]["min_next_hop_conversion_rate"] == 0.6


def test_one_risk_high_support_has_lower_anchor_score_than_next_node_score():
    candidates = [_candidate("launch", "weapon_android.weapon_one_risk", "oneRiskLaunchLess10", ["u1", "u2", "u3", "u4", "u5", "u6"])]
    baseline = _normal({"weapon_android.weapon_one_risk": _field(distinct=20, entropy=0.5, value="oneRiskLaunchLess10", rate=0.12, count=120)})

    result = run_l5(candidates, _kb(), baseline)
    node = result["value_nodes"][0]

    assert node["anchor_score"] < node["next_node_score"]
    assert node["not_recommended_as_anchor_reason"] == "oneRisk_label_is_confirming_signal_not_primary_anchor"


def test_one_risk_one_day_reset_can_be_confirming_but_not_primary_anchor():
    candidates = [_candidate("reset", "weapon_android.weapon_one_risk", "oneRiskOneDayReset", ["u1", "u2", "u3", "u4"])]
    result = run_l5(candidates, _kb(), _normal({"weapon_android.weapon_one_risk": _field(distinct=20, entropy=0.5, value="oneRiskOneDayReset", rate=0.05, count=50)}))
    node = result["value_nodes"][0]

    assert node["role_suggestion"] in {"confirming_node", "next_node_candidate", "context_node"}
    assert node["role_suggestion"] != "preferred_anchor"


def test_common_resolution_battery_camera_anchor_score_is_downgraded():
    candidates = [
        _candidate("resolution", "weapon_android.raw_data.resolution", "1080*2340", ["u1", "u2", "u3", "u4", "u5"]),
        _candidate("camera", "weapon_android.raw_data.camera.o", "0", ["u1", "u2", "u3", "u4", "u5", "u6"]),
    ]
    baseline = _normal({
        "weapon_android.raw_data.resolution": _field(distinct=100, entropy=0.7, value="1080*2340", rate=0.2, count=200),
        "weapon_android.raw_data.camera.o": _field(distinct=2, entropy=0.2, value="0", rate=0.6, count=600),
    })

    result = run_l5(candidates, _kb(), baseline)
    nodes = {n["source_candidate_id"]: n for n in result["value_nodes"]}

    assert nodes["resolution"]["not_recommended_as_anchor_reason"] == "common_profile_context_requires_low_normal_rate_before_anchor"
    assert nodes["camera"]["not_recommended_as_anchor_reason"] == "common_profile_context_requires_low_normal_rate_before_anchor"
    assert nodes["camera"]["anchor_score"] < nodes["camera"]["next_node_score"]


def test_anchor_quality_gate_downgrades_high_normal_rate_microphone_and_lock_status():
    candidates = [
        _candidate("mic", "weapon_android.raw_data.microPhone.m", "-1", ["u1", "u2", "u3", "u4", "u5", "u6"]),
        _candidate("lock", "weapon_android.raw_data.lockScreenStatus", "0", ["u1", "u2", "u3", "u4", "u5"]),
    ]
    baseline = _normal({
        "weapon_android.raw_data.microPhone.m": _field(distinct=2, entropy=0.2, value="-1", rate=0.389, count=389),
        "weapon_android.raw_data.lockScreenStatus": _field(distinct=2, entropy=0.2, value="0", rate=0.219, count=219),
    })

    result = run_l5(candidates, _kb(), baseline)
    nodes = {n["source_candidate_id"]: n for n in result["value_nodes"]}

    assert nodes["mic"]["anchor_quality_gate"] == "weak_anchor"
    assert nodes["mic"]["role_suggestion"] == "weak_anchor"
    assert nodes["mic"]["anchor_score"] <= 45.0
    assert nodes["lock"]["anchor_quality_gate"] == "weak_anchor"
    assert nodes["lock"]["role_suggestion"] == "weak_anchor"
    assert nodes["lock"]["anchor_score"] <= 45.0


def test_high_normal_weak_anchor_does_not_enter_candidate_eval_as_selected_anchor():
    kb = _kb()
    kb["top_k_selection"].update({
        "max_l6_tasks": 1,
        "include_uncertain_prior_limit": 10,
        "near_duplicate_jaccard_threshold": 1.1,
        "min_pair_score": 0.0,
        "candidate_eval_queue": {
            "max_candidate_eval_tasks": 10,
            "min_candidate_eval_score": 0.0,
            "tier_3_max_tasks": 10,
        },
    })
    candidates = [
        _candidate("mic", "weapon_android.raw_data.microPhone.m", "-1", ["u1", "u2", "u3", "u4", "u5", "u6"]),
        _candidate("lock", "weapon_android.raw_data.lockScreenStatus", "0", ["u1", "u2", "u3", "u4", "u5"]),
        _candidate("sensor", "weapon_android.raw_data.sensorList.akm", "1", ["u1", "u2", "u3", "u4", "u5"]),
    ]
    baseline = _normal({
        "weapon_android.raw_data.microPhone.m": _field(distinct=2, entropy=0.2, value="-1", rate=0.389, count=389),
        "weapon_android.raw_data.lockScreenStatus": _field(distinct=2, entropy=0.2, value="0", rate=0.219, count=219),
        "weapon_android.raw_data.sensorList.akm": _field(distinct=50, entropy=0.8, value="1", rate=0.01, count=10),
    })

    result = run_l5(candidates, kb, baseline)

    assert result["candidate_eval_queue"]
    assert all("microPhone.m" not in item["field_path_sequence"][0] for item in result["candidate_eval_queue"])
    assert all("lockScreenStatus" not in item["field_path_sequence"][0] for item in result["candidate_eval_queue"])
    assert result["summary"]["anchor_funnel_audit_summary"]["high_quality_anchor_node_count"] >= 1


def test_candidate_reduction_summary_reports_main_filters():
    kb = _kb()
    kb["top_k_selection"].update({
        "max_l6_tasks": 2,
        "include_uncertain_prior_limit": 1,
        "near_duplicate_jaccard_threshold": 0.85,
        "min_pair_score": 35.0,
    })
    candidates = [
        _candidate("anchor", "src.anchor", "A", ["u1", "u2", "u3", "u4", "u5"]),
        _candidate("t1", "src.t1", "B1", ["u1", "u2", "u3", "u4"]),
        _candidate("t2", "src.t2", "B2", ["u1", "u2", "u3", "u5"]),
        _candidate("t3", "src.t3", "B3", ["u1", "u2", "u4", "u5"]),
    ]

    result = run_l5(candidates, kb, _normal({}))
    reduction = result["summary"]["candidate_reduction_summary"]

    assert "duplicate_suppression_filtered_count" in reduction
    assert "uncertain_limit_filtered_count" in reduction
    assert "min_pair_score_filtered_count" in reduction
    assert "anchor_quality_gate_distribution" in reduction


def test_high_entropy_low_normal_rate_value_gets_high_anchor_score():
    candidates = [_candidate("ip", "risk.ip24", "123.45.67.*", ["u1", "u2", "u3", "u4", "u5"])]
    baseline = _normal({"risk.ip24": _field(distinct=900, entropy=0.95, value="123.45.67.*", rate=0.001, count=1)})

    result = run_l5(candidates, _kb(), baseline)
    node = result["value_nodes"][0]

    assert node["anchor_score"] >= node["next_node_score"]
    assert node["role_suggestion"] == "preferred_anchor"
    assert node["risk_normal_lift"] > 100


def test_user_device_token_uuid_are_not_preferred_anchors():
    candidates = [
        _candidate("uid", "profile.user_id", "123", ["u1", "u2", "u3"]),
        _candidate("token", "profile.token", "tok", ["u1", "u2", "u3"]),
    ]
    result = run_l5(candidates, _kb(), _normal({}))
    nodes = {n["source_candidate_id"]: n for n in result["value_nodes"]}

    assert nodes["uid"]["role_suggestion"] == "reject_node"
    assert nodes["token"]["role_suggestion"] == "reject_node"


def test_label_post_action_field_cannot_be_preferred_anchor():
    candidates = [_candidate("ban", "audit.ban_result", "1", ["u1", "u2", "u3", "u4"])]
    result = run_l5(candidates, _kb(), _normal({}))
    node = result["value_nodes"][0]

    assert node["role_suggestion"] == "reject_node"
    assert "label_or_post_action" in node["not_recommended_as_anchor_reason"]


def test_next_node_score_keeps_confirming_signal():
    candidates = [_candidate("adb", "weapon_android.raw_data.adbStatus", "1", ["u1", "u2", "u3", "u4"])]
    result = run_l5(candidates, _kb(), _normal({"weapon_android.raw_data.adbStatus": _field(distinct=2, entropy=0.2, value="1", rate=0.03, count=30)}))
    node = result["value_nodes"][0]

    assert node["next_node_score"] > 0
    assert node["role_suggestion"] in {"refinement_component", "confirming_node", "next_node_candidate", "preferred_anchor"}


def test_top_k_prefers_better_anchor_over_low_anchor_one_risk():
    kb = _kb()
    kb["top_k_selection"].update({"max_l6_tasks": 5, "near_duplicate_jaccard_threshold": 1.1, "include_uncertain_prior_limit": 10, "min_pair_score": 0.0})
    candidates = [
        _candidate("launch", "weapon_android.weapon_one_risk", "oneRiskLaunchLess10", ["u1", "u2", "u3", "u4", "u5", "u6"]),
        _candidate("ip", "risk.ip24", "123.45.67.*", ["u1", "u2", "u3", "u4", "u5"]),
        _candidate("env", "weapon.raw_data.accessibilitySvc", "com.app/.Svc", ["u1", "u2", "u3", "u4"]),
    ]
    baseline = _normal({
        "weapon_android.weapon_one_risk": _field(distinct=20, entropy=0.5, value="oneRiskLaunchLess10", rate=0.2, count=200),
        "risk.ip24": _field(distinct=900, entropy=0.95, value="123.45.67.*", rate=0.001, count=1),
        "weapon.raw_data.accessibilitySvc": _field(distinct=800, entropy=0.9, value="com.app/.Svc", rate=0.002, count=2),
    })

    result = run_l5(candidates, kb, baseline)

    assert result["l6_tasks"]
    assert all("weapon_one_risk" not in task["relation_expression"]["nodes"][0]["field_path"] for task in result["l6_tasks"])


def test_high_confidence_overlay_prior_is_loaded_without_runtime_llm_call():
    kb = attach_prior_overlay(_kb(), {
        "field_family_map": [],
        "field_pair_prior_seed_library": [
            {
                "anchor_field": "risk.foo_anchor",
                "target_field": "risk.bar_signal",
                "prior": "normally_unrelated",
                "confidence": "high",
                "judgement_source": "llm_seed",
                "reason": "test overlay",
                "need_human_review": False,
            }
        ],
        "natural_relation_seed_library": [],
        "leakage_field_map": [],
        "over_general_field_map": [],
        "unique_id_field_map": [],
        "field_role_map": [],
    })
    candidates = [
        _candidate("foo", "risk.foo_anchor", "foo", ["u1", "u2", "u3", "u4"]),
        _candidate("bar", "risk.bar_signal", "bar", ["u1", "u2", "u3"]),
    ]

    result = run_l5(candidates, kb, _normal({"risk.foo_anchor": _field(value="foo", rate=0.001), "risk.bar_signal": _field(value="bar", rate=0.01)}))
    pair = result["pair_candidates"][0]

    assert pair["field_pair_prior"]["prior"] == "normally_unrelated"
    assert pair["field_pair_prior"]["judgement_source"] == "llm_seed"
    assert result["summary"]["prior_overlay_status"] == "loaded"


def test_low_confidence_overlay_prior_remains_uncertain_and_reviewable():
    kb = attach_prior_overlay(_kb(), {
        "field_pair_prior_seed_library": [
            {
                "anchor_field": "risk.foo",
                "target_field": "risk.bar",
                "prior": "normally_unrelated",
                "confidence": "low",
                "judgement_source": "llm_seed",
                "reason": "test low confidence",
                "need_human_review": True,
            }
        ]
    })
    candidates = [
        _candidate("foo", "risk.foo", "A", ["u1", "u2", "u3"]),
        _candidate("bar", "risk.bar", "B", ["u1", "u2", "u3"]),
    ]

    result = run_l5(candidates, kb, _normal({}))
    pair = result["pair_candidates"][0]

    assert pair["field_pair_prior"]["prior"] == "uncertain"
    assert pair["field_pair_prior"]["need_human_review"] is True


def test_missing_normal_baseline_does_not_fail_and_marks_summary_missing():
    result = run_l5([_candidate("ip", "risk.ip24", "123.45.67.*", ["u1", "u2", "u3"])], _kb())

    assert result["summary"]["normal_baseline_status"] == "missing"
    assert result["value_nodes"][0]["normal_baseline_status"] == "missing"


def test_field_level_kb_unique_leakage_and_over_general_maps_downgrade_fields():
    kb = attach_prior_overlay(_kb(), None, {
        "unique_id_field_map": [{"field_path": "risk.exact_device", "judgement": "unique_id"}],
        "leakage_field_map": [{"field_path": "risk.audit_result", "judgement": "leakage_field"}],
        "over_general_field_map": [{"field_path": "risk.context_field", "judgement": "over_general_field"}],
        "field_family_map": [],
        "field_role_map": [],
        "field_pair_prior": [],
        "natural_relation_map": [],
    })
    candidates = [
        _candidate("id", "risk.exact_device", "d1", ["u1", "u2", "u3"]),
        _candidate("leak", "risk.audit_result", "hit", ["u1", "u2", "u3"]),
        _candidate("ctx", "risk.context_field", "common", ["u1", "u2", "u3"]),
    ]

    result = run_l5(candidates, kb, _normal({"risk.context_field": _field(value="common", rate=0.3)}))
    nodes = {n["source_candidate_id"]: n for n in result["value_nodes"]}

    assert nodes["id"]["role_suggestion"] == "reject_node"
    assert nodes["leak"]["role_suggestion"] == "reject_node"
    assert nodes["ctx"]["anchor_quality_gate"] in {"weak_anchor", "reject_as_anchor"}


def test_value_relation_overlay_exact_match_has_priority_over_field_level_prior():
    kb = attach_prior_overlay(
        _kb(),
        None,
        {
            "field_pair_prior": [
                {"anchor_field": "risk.a", "target_field": "risk.b", "prior": "normally_strong_related", "confidence": "high"}
            ],
            "field_family_map": [],
            "field_role_map": [],
            "natural_relation_map": [],
            "leakage_field_map": [],
            "over_general_field_map": [],
            "unique_id_field_map": [],
        },
        {
            "value_relation_prior_overlay": [
                {
                    "anchor_field": "risk.a",
                    "anchor_value": "A",
                    "target_field": "risk.b",
                    "target_value": "B",
                    "prior": "value_conditioned_unusual_relation",
                    "recommended_usage": "allow_as_anchor",
                    "confidence": "high",
                    "judgement_source": "human_seed",
                    "reason": "specific value relation override",
                    "need_human_review": True,
                    "run_id": "test_run",
                    "source_task_ids": ["t1"],
                }
            ]
        },
    )
    candidates = [
        _candidate("a", "risk.a", "A", ["u1", "u2", "u3"]),
        _candidate("b", "risk.b", "B", ["u1", "u2", "u3"]),
    ]

    result = run_l5(candidates, kb, _normal({"risk.a": _field(value="A", rate=0.01), "risk.b": _field(value="B", rate=0.02)}))
    pair = result["pair_candidates"][0]

    assert pair["field_pair_prior"]["scope"] == "value_relation"
    assert pair["field_pair_prior"]["prior"] == "normally_unrelated"
    assert pair["field_pair_prior"]["judgement_source"] == "human_seed"
    assert result["summary"]["value_relation_overlay_hit_count"] >= 1


def test_medium_confidence_value_overlay_participates_with_uncertainty_penalty():
    kb = attach_prior_overlay(_kb(), None, None, {
        "value_relation_prior_overlay": [
            {
                "anchor_field": "risk.a",
                "anchor_value": "A",
                "target_field": "risk.b",
                "target_value": "B",
                "prior": "value_conditioned_unusual_relation",
                "recommended_usage": "allow_as_refinement_component",
                "confidence": "medium",
                "judgement_source": "llm_seed",
                "reason": "medium seed",
                "need_human_review": True,
            }
        ]
    })
    result = run_l5([
        _candidate("a", "risk.a", "A", ["u1", "u2", "u3"]),
        _candidate("b", "risk.b", "B", ["u1", "u2", "u3"]),
    ], kb, _normal({"risk.a": _field(value="A", rate=0.01), "risk.b": _field(value="B", rate=0.01)}))
    pair = result["pair_candidates"][0]

    assert pair["field_pair_prior"]["confidence"] == "medium"
    assert pair["uncertainty_penalty"] > 0
    assert pair["field_pair_prior"]["need_human_review"] is True


def test_value_overlay_is_not_promoted_automatically_to_long_term_kb():
    kb = attach_prior_overlay(_kb(), None, None, {
        "value_relation_prior_overlay": [
            {
                "anchor_field": "risk.a",
                "anchor_value": "A",
                "target_field": "risk.b",
                "target_value": "B",
                "prior": "value_conditioned_common_relation",
                "recommended_usage": "context_only",
                "confidence": "high",
                "judgement_source": "human_seed",
                "reason": "run only",
                "need_human_review": True,
            }
        ]
    })
    result = run_l5([
        _candidate("a", "risk.a", "A", ["u1", "u2", "u3"]),
        _candidate("b", "risk.b", "B", ["u1", "u2", "u3"]),
    ], kb, _normal({"risk.a": _field(value="A", rate=0.01), "risk.b": _field(value="B", rate=0.01)}))

    assert result["promotion_candidates"]
    assert all(p["promotion_decision"] == "pending" for p in result["promotion_candidates"])
    assert not any("value_relation_prior_overlay" in str(p.get("candidate", {})) for p in result["promotion_candidates"])


def test_missing_all_prior_falls_back_to_uncertain():
    kb = attach_prior_overlay(_kb(), None, {
        "field_pair_prior": [],
        "field_family_map": [],
        "field_role_map": [],
        "natural_relation_map": [],
        "leakage_field_map": [],
        "over_general_field_map": [],
        "unique_id_field_map": [],
    }, {"value_relation_prior_overlay": []})
    result = run_l5([
        _candidate("foo", "risk.foo_unseen", "A", ["u1", "u2", "u3"]),
        _candidate("bar", "risk.bar_unseen", "B", ["u1", "u2", "u3"]),
    ], kb, _normal({}))

    assert result["pair_candidates"][0]["field_pair_prior"]["prior"] == "uncertain"


def test_candidate_eval_queue_dedupes_same_anchor_same_target_family_high_jaccard():
    kb = _kb()
    kb["top_k_selection"].update({
        "max_l6_tasks": 10,
        "near_duplicate_jaccard_threshold": 0.85,
        "candidate_eval_queue": {
            "max_candidate_eval_tasks": 10,
            "min_candidate_eval_score": 0.0,
            "per_anchor_max_tasks": 10,
            "tier_1_max_tasks": 10,
            "tier_3_max_tasks": 10,
        },
    })
    candidates = [
        _candidate("ip", "risk.ip24", "123.45.67.*", ["u1", "u2", "u3", "u4"]),
        _candidate("svc1", "weapon.raw_data.accessibilitySvc", "svc.a", ["u1", "u2", "u3", "u4"]),
        _candidate("svc2", "weapon.raw_data.enabledAccessibilityServiceList", "svc.b", ["u1", "u2", "u3", "u4"]),
    ]
    baseline = _normal({
        "risk.ip24": _field(distinct=900, entropy=0.95, value="123.45.67.*", rate=0.001, count=1),
        "weapon.raw_data.accessibilitySvc": _field(distinct=800, entropy=0.9, value="svc.a", rate=0.001, count=1),
        "weapon.raw_data.enabledAccessibilityServiceList": _field(distinct=800, entropy=0.9, value="svc.b", rate=0.001, count=1),
    })

    result = run_l5(candidates, kb, baseline)
    ip_accessibility_pairs = [
        p for p in result["pair_candidates"]
        if p.get("anchor_field") == "ip24" and p.get("target_field") == "accessibility_service"
    ]

    assert any(p.get("candidate_eval_queue_decision") == "selected_candidate_eval_queue" for p in ip_accessibility_pairs)
    assert any(p.get("candidate_eval_queue_decision") == "filtered_eval_near_duplicate" for p in ip_accessibility_pairs)
    assert result["summary"]["eval_duplicate_suppression_count"] >= 1


def test_candidate_eval_queue_retains_cross_family_high_jaccard_overlap():
    kb = _kb()
    kb["top_k_selection"].update({
        "max_l6_tasks": 10,
        "near_duplicate_jaccard_threshold": 0.85,
        "candidate_eval_queue": {
            "max_candidate_eval_tasks": 10,
            "min_candidate_eval_score": 0.0,
            "per_anchor_max_tasks": 10,
            "tier_1_max_tasks": 10,
            "tier_3_max_tasks": 10,
        },
    })
    candidates = [
        _candidate("ip", "risk.ip24", "123.45.67.*", ["u1", "u2", "u3", "u4"]),
        _candidate("svc", "weapon.raw_data.accessibilitySvc", "svc.a", ["u1", "u2", "u3", "u4"]),
        _candidate("risk", "weapon_android.weapon_one_risk", "oneRiskLaunchLess10", ["u1", "u2", "u3", "u4"]),
    ]
    baseline = _normal({
        "risk.ip24": _field(distinct=900, entropy=0.95, value="123.45.67.*", rate=0.001, count=1),
        "weapon.raw_data.accessibilitySvc": _field(distinct=800, entropy=0.9, value="svc.a", rate=0.001, count=1),
        "weapon_android.weapon_one_risk": _field(distinct=20, entropy=0.5, value="oneRiskLaunchLess10", rate=0.08, count=80),
    })

    result = run_l5(candidates, kb, baseline)
    selected = result["candidate_eval_queue"]
    ip_pairs = [
        p for p in result["pair_candidates"]
        if p.get("anchor_field") == "ip24" and p.get("candidate_eval_queue_decision") == "selected_candidate_eval_queue"
    ]

    assert len(ip_pairs) >= 2
    assert any(p.get("candidate_eval_queue_reason") == "cross_family_overlap_retained_for_eval" for p in ip_pairs)
    assert any(p.get("duplicate_related") for p in ip_pairs)
    assert result["summary"]["cross_family_overlap_retained_count"] >= 1
    assert all(task["candidate_signal_level"] == "candidate_signal" for task in selected)


def test_pair_outputs_bidirectional_direction_views():
    result = run_l5([
        _candidate("a", "risk.a", "A", ["u1", "u2", "u3", "u4"]),
        _candidate("b", "risk.b", "B", ["u1", "u2", "u3"]),
    ], _kb(), _normal({"risk.a": _field(value="A", rate=0.01), "risk.b": _field(value="B", rate=0.01)}))
    pair = result["pair_candidates"][0]

    assert set(pair["directional_metrics"]) == {"A_to_B", "B_to_A"}
    assert pair["directional_metrics"]["A_to_B"]["directional_conversion"] == 0.75
    assert pair["directional_metrics"]["B_to_A"]["directional_conversion"] == 1.0
    assert pair["relation_strength"] == "bidirectional"


def test_reverse_direction_enters_candidate_eval_when_forward_conversion_fails():
    candidates = [
        _candidate("launch", "weapon_android.weapon_one_risk", "oneRiskLaunchLess10", ["u1", "u2", "u3", "u4", "u5", "u6"]),
        _candidate("brand", "weapon_android.raw_data.brand", "Xiaomi", ["u1", "u2", "u3", "u4"]),
    ]
    baseline = _normal({
        "weapon_android.weapon_one_risk": _field(distinct=20, entropy=0.5, value="oneRiskLaunchLess10", rate=0.08, count=80),
        "weapon_android.raw_data.brand": _field(distinct=50, entropy=0.6, value="Xiaomi", rate=0.02, count=20),
    })

    result = run_l5(candidates, _kb(), baseline)
    pair = result["pair_candidates"][0]
    brand_tasks = [task for task in result["candidate_eval_queue"] if task.get("field_path_sequence") == ["weapon_android.raw_data.brand", "weapon_android.weapon_one_risk"]]

    assert pair["pair_decision"] == "pass_to_path_expansion"
    assert any(view["direction_decision"] == "pass_directional_relation" for view in pair["directional_metrics"].values())
    assert brand_tasks
    assert brand_tasks[0]["observed_metrics"]["directional_conversion"] == 1.0
    assert brand_tasks[0]["anchor_unit_type"] == "atomic_anchor"
    assert all("weapon_one_risk" not in task["field_path_sequence"][0] for task in result["candidate_eval_queue"])


def test_refinement_component_direction_rescues_eval_only_not_strict_l6():
    kb = _kb()
    kb["top_k_selection"].update({"max_l6_tasks": 1, "candidate_eval_queue": {"max_candidate_eval_tasks": 10, "min_candidate_eval_score": 0.0}})
    candidates = [
        _candidate("a", "risk.big_anchor", "A", ["u1", "u2", "u3", "u4", "u5", "u6"]),
        _candidate("b", "risk.secondary_env", "B", ["u1", "u2", "u3"]),
    ]
    baseline = _normal({
        "risk.big_anchor": _field(distinct=900, entropy=0.95, value="A", rate=0.001, count=1),
        "risk.secondary_env": _field(distinct=200, entropy=0.65, value="B", rate=0.05, count=50),
    })

    result = run_l5(candidates, kb, baseline)
    pair = result["pair_candidates"][0]

    assert pair["pair_decision"] == "hold_low_conversion"
    assert pair["directional_metrics"]["A_to_B"]["direction_decision"] == "pass_refinement_component_direction"
    assert result["candidate_eval_queue"]
    assert result["summary"]["refinement_component_direction_count"] >= 1
    assert result["summary"]["hold_low_conversion_rescued_count"] >= 1
    assert result["summary"]["l6_task_count"] == 0


def test_conditional_gain_audit_for_three_hop_path():
    from l5_candidate_generation.l5_value_path_candidate_generator import build_path_record  # noqa: E402

    node_by_id = {
        "a": {"field_path": "src.a", "value_or_pattern": "A", "field_key": "a", "risk_hit_sample_ids": ["u1", "u2", "u3", "u4"]},
        "b": {"field_path": "src.b", "value_or_pattern": "B", "field_key": "b", "risk_hit_sample_ids": ["u1", "u2", "u3", "u5"]},
        "c": {"field_path": "src.c", "value_or_pattern": "C", "field_key": "c", "risk_hit_sample_ids": ["u1", "u2", "u3"]},
    }
    record = build_path_record(
        ["a", "b", "c"],
        node_by_id,
        {"u1", "u2", "u3"},
        [0.75, 1.0],
        "pass_to_l6",
        None,
        previous_support_count=3,
        threshold_values={"min_support_samples": 3, "min_path_conversion_rate": 0.6},
        threshold_source="global",
    )

    audit = record["conditional_gain_audit"]
    assert audit["target_node"] == "c"
    assert audit["conditional_gain_status"] in {"incremental_gain_candidate", "no_incremental_gain"}
    assert "A_B" in audit["subpath_predictability"]


def test_broad_brand_anchor_goes_to_held_drilldown_not_main_eval():
    candidates = [
        _candidate("launch", "weapon_android.weapon_one_risk", "oneRiskLaunchLess10", ["u1", "u2", "u3", "u4", "u5", "u6"]),
        _candidate("brand", "weapon_android.raw_data.brand", "Xiaomi", ["u1", "u2", "u3", "u4"]),
    ]
    baseline = _normal({
        "weapon_android.weapon_one_risk": _field(distinct=20, entropy=0.5, value="oneRiskLaunchLess10", rate=0.08, count=80),
        "weapon_android.raw_data.brand": _field(distinct=10, entropy=0.3, value="Xiaomi", rate=0.35, count=350),
    })

    result = run_l5(candidates, _kb(), baseline)

    assert not [task for task in result["candidate_eval_queue"] if task.get("field_path_sequence") == ["weapon_android.raw_data.brand", "weapon_android.weapon_one_risk"]]
    held = [task for task in result["held_or_drilldown_queue"] if task.get("field_path_sequence") == ["weapon_android.raw_data.brand", "weapon_android.weapon_one_risk"]]
    assert held
    assert held[0]["eval_anchor_eligibility"] == "broad_anchor_hold"


def test_strict_l6_filters_ineligible_anchor_without_backfill_requirement():
    kb = _kb()
    kb["top_k_selection"].update({"max_l6_tasks": 10, "min_pair_score": 0.0})
    candidates = [
        _candidate("launch", "weapon_android.weapon_one_risk", "oneRiskLaunchLess10", ["u1", "u2", "u3", "u4", "u5", "u6"]),
        _candidate("brand", "weapon_android.raw_data.brand", "Xiaomi", ["u1", "u2", "u3", "u4", "u5"]),
    ]
    baseline = _normal({
        "weapon_android.weapon_one_risk": _field(distinct=20, entropy=0.5, value="oneRiskLaunchLess10", rate=0.08, count=80),
        "weapon_android.raw_data.brand": _field(distinct=10, entropy=0.3, value="Xiaomi", rate=0.35, count=350),
    })

    result = run_l5(candidates, kb, baseline)

    assert result["summary"]["l6_task_count"] == 0
    assert result["summary"]["candidate_reduction_summary"]["strict_ineligible_anchor_filtered_count"] >= 1
    assert all(task.get("eval_anchor_eligibility") == "eligible" for task in result["l6_tasks"])


def test_strict_l6_keeps_eligible_anchor_candidate_signal():
    candidates = [
        _candidate("ip", "risk.ip24", "123.45.67.*", ["u1", "u2", "u3", "u4"]),
        _candidate("model", "device.device_model", "Redmi_X", ["u1", "u2", "u3"]),
    ]

    result = run_l5(candidates, _kb())

    assert result["l6_tasks"]
    assert all(task.get("eval_anchor_eligibility") == "eligible" for task in result["l6_tasks"])
    assert all(task.get("candidate_signal_level") == "candidate_signal" for task in result["l6_tasks"])


def test_broad_brand_plus_old_os_can_form_composite_anchor_to_evidence():
    candidates = [
        _candidate("launch", "weapon_android.weapon_one_risk", "oneRiskLaunchLess10", ["u1", "u2", "u3", "u4"]),
        _candidate("brand", "weapon_android.raw_data.brand", "Xiaomi", ["u1", "u2", "u3", "u4", "u5"]),
        _candidate("os", "weapon_android.raw_data.osVersion", "old_9", ["u1", "u2", "u3", "u4"]),
    ]
    baseline = _normal({
        "weapon_android.weapon_one_risk": _field(distinct=20, entropy=0.5, value="oneRiskLaunchLess10", rate=0.08, count=80),
        "weapon_android.raw_data.brand": _field(distinct=10, entropy=0.3, value="Xiaomi", rate=0.35, count=350),
        "weapon_android.raw_data.osVersion": _field(distinct=80, entropy=0.8, value="old_9", rate=0.02, count=20),
    })

    result = run_l5(candidates, _kb(), baseline)
    composite = [
        task for task in result["candidate_eval_queue"]
        if task.get("anchor_unit_type") == "composite_anchor"
        and "weapon_android.weapon_one_risk" in task.get("field_path_sequence", [])
    ]

    assert composite
    assert composite[0]["normal_joint_rate_status"] == "need_hive_eval"
    assert composite[0]["relation_form"] == "composite_anchor_to_evidence"
