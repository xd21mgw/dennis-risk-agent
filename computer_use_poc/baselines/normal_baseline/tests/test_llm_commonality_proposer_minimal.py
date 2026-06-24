import json
import sys
from pathlib import Path


L3_DIR = Path(__file__).resolve().parents[1] / "l3_extraction"
sys.path.insert(0, str(L3_DIR))

import dynamic_prompt_builder
import llm_commonality_proposer
import proposal_record_utils
from dynamic_prompt_builder import assemble_per_action_prompt, discovery_prompt_contains_oracle
from llm_commonality_proposer import CommonalityProposer, build_source_observation_groups, real_llm_preflight
from proposal_record_utils import (
    REDACTED,
    build_prompt_input_summary,
    coerce_observation_records,
    safe_preview,
    value_shape,
)


def test_record_utils_safe_preview_redacts_sensitive_values():
    payload = {
        "token": "token-secret",
        "cookie": "cookie-secret",
        "sessionId": "session-secret",
        "password": "password-secret",
        "headers": {"Authorization": "Bearer header-secret"},
        "nested": {"normal": "visible-value"},
    }

    preview = safe_preview(payload)
    encoded = json.dumps(preview, ensure_ascii=False)

    assert preview["token"] == REDACTED
    assert preview["cookie"] == REDACTED
    assert preview["sessionId"] == REDACTED
    assert preview["password"] == REDACTED
    assert preview["headers"] == REDACTED
    assert "visible-value" in encoded
    for secret in ("token-secret", "cookie-secret", "session-secret", "password-secret", "header-secret"):
        assert secret not in encoded


def test_record_utils_value_shape_and_contract_normalization():
    assert value_shape("x") == "string"
    assert value_shape(1) == "number"
    assert value_shape(1.5) == "number"
    assert value_shape(True) == "bool"
    assert value_shape([1]) == "list"
    assert value_shape({"a": 1}) == "dict"
    assert value_shape(None) == "null"

    contract = {
        "schema_version": "e2e_risk_observation_input_contract_v0_1",
        "users": [{
            "user_id": "u1",
            "sources": {
                "login_logs": {
                    "login_logs_search": {
                        "source_name": "login_logs",
                        "action": "login_logs_search",
                        "source_status": "completed",
                        "raw_body": {"event": {"loginType": "token"}},
                    }
                }
            },
        }],
    }
    records = coerce_observation_records(contract)

    assert records == [{
        "user_id": "u1",
        "source_name": "login_logs",
        "source_action": "login_logs_search",
        "action_or_layer": "login_logs_search",
        "payload": {"event": {"loginType": "token"}},
    }]


def test_proposer_builds_source_groups_without_validator_dependency(tmp_path: Path):
    raw_path = tmp_path / "raw.json"
    raw_path.write_text(json.dumps([
        {
            "source_name": "login_logs",
            "source_action": "login_logs_search",
            "user_id": "u1",
            "payload": {"params": {"loginType": "token", "count": 1}},
        },
        {
            "source_name": "login_logs",
            "source_action": "login_logs_search",
            "user_id": "u2",
            "payload": {"params": {"loginType": "token", "count": 2}},
        },
    ]), encoding="utf-8")

    groups = build_source_observation_groups(raw_path)
    group = groups["login_logs.login_logs_search"]
    records = coerce_observation_records(json.loads(raw_path.read_text(encoding="utf-8")))
    summary = build_prompt_input_summary(records)

    assert group["user_ids"] == ["u1", "u2"]
    assert group["field_path_stats"]["params.loginType"] == 2
    assert group["sample_values"]["params.count"] == [1, 2]
    assert summary["record_count"] == 2

    proposer_source = (L3_DIR / "llm_commonality_proposer.py").read_text(encoding="utf-8")
    assert "commonality_proposal_validator" not in proposer_source
    for forbidden_import in (
        "dynamic_llm_semantic_discovery_runner",
        "code_assisted_commonality_runner",
        "llm_commonality_shadow_run",
        "l3_l4_candidate_pooling",
        "l5_value_path_candidate_generator",
    ):
        assert f"import {forbidden_import}" not in proposer_source
        assert f"from {forbidden_import}" not in proposer_source


def test_commonality_proposer_outputs_proposals_not_replay_or_verified(tmp_path: Path):
    raw_path = tmp_path / "raw.json"
    fixture_path = tmp_path / "fixture.json"
    raw_path.write_text(json.dumps({
        "records": [{
            "source_name": "archives",
            "action": "archives_user_analysis",
            "user_id": "u1",
            "payload": {"requestParam": {"type": "profile_modify"}},
        }]
    }), encoding="utf-8")
    fixture_path.write_text(json.dumps({
        "action_or_source": "archives.archives_user_analysis",
        "proposal_count": 2,
        "proposals": [
            {
                "proposal_id": "p1",
                "proposal_type": "field_value_pattern",
                "commonality_claim": "Most samples share profile_modify requestParam.",
                "source_fields": ["requestParam.type"],
                "recompute_rule": "field_value_equals",
                "logic_reason": "Proposal-only fixture.",
            },
            {
                "proposal_id": "p2",
                "proposal_type": "field_presence_observation",
                "commonality_claim": "Most samples include requestParam.",
                "source_fields": ["requestParam"],
                "recompute_rule": "required_fields_present",
                "logic_reason": "Proposal-only fixture.",
            },
        ],
    }), encoding="utf-8")

    off_result = CommonalityProposer(mode="off").propose(raw_path)
    fixture_result = CommonalityProposer(
        mode="fixture",
        fixture_path=fixture_path,
        raw_proposals_per_action_source=1,
    ).propose(raw_path)
    encoded = json.dumps(fixture_result, ensure_ascii=False)

    assert off_result["proposal_payloads"] == []
    assert fixture_result["mode"] == "fixture"
    assert fixture_result["proposal_payloads"][0]["proposal_count"] == 1
    assert fixture_result["parse_warnings"][0]["warning_type"] == "raw_proposal_cap_applied"
    for replay_or_verified_field in (
        "support_user_count",
        "miss_user_count",
        "coverage_user_count",
        "replay_status",
        "normal_hit_rate",
        "verified_strategy",
    ):
        assert replay_or_verified_field not in encoded


def test_real_llm_preflight_defaults_to_no_call():
    preflight = real_llm_preflight(enable_real_llm=False)

    assert preflight["requested_llm_mode"] == "mock_or_fixture"
    assert preflight["effective_llm_mode"] == "mock_or_fixture"
    assert preflight["real_llm_called"] is False
    assert preflight["fallback_reason"] == "real_llm_not_requested"


def test_dynamic_prompt_builder_uses_canonical_lens():
    canonical_path = dynamic_prompt_builder.CANONICAL_LENS_PATH
    prompt = assemble_per_action_prompt("login_logs_search", {"covered_users": ["u1"]})
    first_non_empty_line = next(
        line for line in canonical_path.read_text(encoding="utf-8").splitlines() if line.strip()
    )

    assert canonical_path.name == "dennis_risk_semantic_lens.md"
    assert canonical_path.parent == L3_DIR
    assert first_non_empty_line in prompt
    assert "login_logs_search" in prompt
    assert not discovery_prompt_contains_oracle(prompt)
