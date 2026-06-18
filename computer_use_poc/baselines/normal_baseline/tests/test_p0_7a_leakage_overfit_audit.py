import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "l3_extraction"))

from p0_7a_leakage_overfit_audit import (
    audit_candidate_process,
    audit_forbidden_inputs,
    audit_hardcoding,
    build_p0_7a_audit_outputs,
)


def test_forbidden_input_audit_distinguishes_eval_only_cleaned_read(tmp_path):
    source = tmp_path / "runner.py"
    source.write_text(
        "\n".join([
            "def discover():",
            "    return []",
            "# many lines omitted",
            "",
            "cleaned_candidate_file = 'candidate_replay_provenance.json'",
            "payload = Path(cleaned_candidate_file).read_text(encoding='utf-8')",
        ]),
        encoding="utf-8",
    )

    result = audit_forbidden_inputs(source_file=source, base_dir=tmp_path)

    assert result["forbidden_input_used"] is False
    assert result["eval_only_reference_paths"]


def test_hardcoding_audit_reports_semantic_overlap_and_generic_miners(tmp_path):
    source = tmp_path / "runner.py"
    source.write_text(
        "\n".join([
            "name='autonomous_hk_location_supporting_cluster'",
            "operator='endpoint_family_miner'",
            "operator2='network_environment_miner'",
            "rule={'visit_min': 500, 'track_duration_min': 1440}",
        ]),
        encoding="utf-8",
    )

    result = audit_hardcoding(source)

    assert result["hardcoded_candidate_name_count"] >= 1
    assert result["generic_miner_count"] == 2
    assert result["hardcoded_answer_risk"] in {"medium", "high"}


def test_candidate_process_marks_generic_miner_clean_but_rule_template_hardcoded(tmp_path):
    candidates = {
        "candidates": [
            {
                "candidate_id": "p0_7:wave_5:auto",
                "candidate_name": "autonomous_network_provider_asn_cluster",
                "discovery_operator": "network_environment_miner",
                "rule_type": "network_combo",
                "rule_params": {"core": "provider_asn"},
            }
        ]
    }
    replay = {"candidates": [{"candidate_id": "p0_7:wave_5:auto", "replay_status": "replay_pass"}]}
    candidate_file = tmp_path / "candidates.json"
    replay_file = tmp_path / "replay.json"
    candidate_file.write_text(json.dumps(candidates), encoding="utf-8")
    replay_file.write_text(json.dumps(replay), encoding="utf-8")

    rows = audit_candidate_process(candidate_file=candidate_file, replay_file=replay_file)

    assert rows[0]["generated_by_miner"] == "network_environment_miner"
    assert rows[0]["uses_cleaned_candidate_name"] is False
    assert rows[0]["uses_challenge_hint"] is False
    assert rows[0]["uses_gap_focused_hint"] is False
    assert rows[0]["rule_hardcoded"] is True
    assert rows[0]["leakage_status"] == "clean"


def test_full_audit_outputs_files_and_final_judgement(tmp_path):
    source = tmp_path / "runner.py"
    source.write_text(
        "\n".join([
            "operator='endpoint_family_miner'",
            "def build():",
            "    pass",
            "cleaned_candidate_file='candidate_replay_provenance.json'",
            "Path(cleaned_candidate_file).read_text(encoding='utf-8')",
        ]),
        encoding="utf-8",
    )
    p0_7_dir = tmp_path / "p0_7"
    p0_7_dir.mkdir()
    (p0_7_dir / "p0_7_autonomous_cold_start_candidates.json").write_text(
        json.dumps({"candidates": []}),
        encoding="utf-8",
    )
    (p0_7_dir / "p0_7_autonomous_replay_provenance.json").write_text(
        json.dumps({"candidates": []}),
        encoding="utf-8",
    )

    payload = build_p0_7a_audit_outputs(
        source_file=source,
        base_dir=tmp_path,
        p0_7_dir=p0_7_dir,
        output_dir=tmp_path / "out",
    )

    assert payload["final_judgement"]["p0_7a_leakage_audit_pass"] is True
    assert payload["final_judgement"]["can_claim_full_autonomous"] is False
    assert (tmp_path / "out" / "p0_7a_leakage_overfit_audit.json").exists()
    assert (tmp_path / "out" / "p0_7a_leakage_overfit_audit.md").exists()
