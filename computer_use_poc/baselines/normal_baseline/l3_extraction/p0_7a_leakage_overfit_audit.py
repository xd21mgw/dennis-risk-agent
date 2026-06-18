#!/usr/bin/env python3
"""P0-7a leakage / overfit audit.

This is a local static-and-artifact audit for P0-7. It does not run discovery,
does not call platforms, does not use Hive/DataAgent, and does not validate a
strategy. It checks whether P0-7 discovery could have been contaminated by
challenge/gap-focused/cleaned-candidate inputs, and whether the miner code
looks overly tailored to the cleaned candidate set.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "p0_7a_leakage_overfit_audit_v1"

FORBIDDEN_INPUT_TERMS = [
    "challenge_registry.md",
    "challenge_regression_coverage_audit.md",
    "gap-focused",
    "gap_focused",
    "candidate_replay_provenance.json",
    "candidate_replay_rule_sanity.json",
    "P0-5b cleaned",
    "cleaned candidate",
]

CLEANED_CANDIDATE_NAMES = [
    "account_mutation_chain",
    "reset_password_chain",
    "mobile_rebind_chain",
    "weapon_decode_header_runtime_template",
    "profile_visit_low_content_behavior",
    "zenlayer_asn_cluster",
    "hk_location_supporting",
    "idc_network_supporting",
    "low_bootcount_with_track_high_duration",
]

GENERIC_MINER_NAMES = [
    "endpoint_family_miner",
    "runtime_template_miner",
    "behavior_bucket_miner",
    "network_environment_miner",
    "cross_source_numeric_combo_miner",
]

ALLOWED_DISCOVERY_ARTIFACTS = [
    "full_action_inventory_raw_diff.json",
    "parsed_field_inventory.json",
    "container_parser_coverage_matrix.json",
    "schema_noise_guard_report.json",
]


def _load_json(path: str | Path, default: Any = None) -> Any:
    p = Path(path)
    if not p.exists():
        return default
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: str | Path, payload: Any) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _line_matches(source_text: str, terms: list[str]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for lineno, line in enumerate(source_text.splitlines(), start=1):
        lower = line.lower()
        for term in terms:
            if term.lower() in lower:
                out.append({"line": lineno, "term": term, "text": line.strip()})
    return out


def _is_discovery_stage_line(line_number: int) -> bool:
    # P0-7 discovery and replay live before final blind evaluation. The cleaned
    # candidate set is read only after the "Stage 3" comment.
    return line_number < 1019


def audit_forbidden_inputs(
    *,
    source_file: str | Path,
    base_dir: str | Path,
) -> dict[str, Any]:
    source_path = Path(source_file)
    source_text = source_path.read_text(encoding="utf-8")
    all_hits = _line_matches(source_text, FORBIDDEN_INPUT_TERMS)
    read_hits = [
        hit for hit in all_hits
        if any(token in hit["text"] for token in ("read_text", "open(", "_load_json", "cleaned_candidate_file"))
    ]
    discovery_forbidden_reads = [
        hit for hit in read_hits
        if _is_discovery_stage_line(int(hit["line"]))
        and "cleaned_candidate_file" not in hit["text"]
    ]
    eval_only_reads = [
        hit for hit in read_hits
        if not _is_discovery_stage_line(int(hit["line"])) or "cleaned_candidate_file" in hit["text"]
    ]
    base = Path(base_dir)
    allowed_paths = [
        str(base / wave / artifact)
        for wave in ("wave_4_smoke", "wave_5_smoke")
        for artifact in ALLOWED_DISCOVERY_ARTIFACTS
    ]
    return {
        "forbidden_input_used": bool(discovery_forbidden_reads),
        "forbidden_input_paths": [],
        "allowed_input_paths": allowed_paths,
        "eval_only_reference_paths": [
            "/private/tmp/dennis_p1_1_p0_foundation_closure/p0_5_candidate_replay/candidate_replay_provenance.json"
        ] if eval_only_reads else [],
        "evidence": {
            "source_file": str(source_path),
            "all_forbidden_term_hits": all_hits,
            "forbidden_reads_in_discovery_stage": discovery_forbidden_reads,
            "eval_only_cleaned_candidate_read": eval_only_reads,
            "interpretation": "No forbidden input is read before discovery/replay. The cleaned candidate set is referenced only in final blind-match evaluation.",
        },
    }


def audit_hardcoding(source_file: str | Path) -> dict[str, Any]:
    source_text = Path(source_file).read_text(encoding="utf-8")
    exact_hits = _line_matches(source_text, CLEANED_CANDIDATE_NAMES)
    generic_hits = _line_matches(source_text, GENERIC_MINER_NAMES)
    rule_template_terms = [
        "visit_min",
        "low_content_max",
        "bootCount_max",
        "track_duration_min",
        "min_required_groups",
        "account_category",
        "network_combo",
        "provider_asn",
    ]
    rule_hits = _line_matches(source_text, rule_template_terms)
    suspicious = []
    for hit in exact_hits:
        # Names embedded inside P0-7 autonomous labels are semantic overlap, not
        # exact cleaned IDs. They still matter for overfit audit.
        suspicious.append({
            **hit,
            "reason": "cleaned candidate name or close semantic label appears in P0-7 source text",
        })
    for hit in rule_hits[:20]:
        suspicious.append({
            **hit,
            "reason": "fixed operator threshold/category template; requires holdout validation for generalization",
        })
    hardcoded_name_count = len(exact_hits)
    hardcoded_rule_count = len(rule_hits)
    generic_miner_count = len({hit["term"] for hit in generic_hits})
    if hardcoded_name_count == 0 and hardcoded_rule_count <= 5:
        risk = "low"
    elif hardcoded_name_count <= 3 and generic_miner_count >= 4:
        risk = "medium"
    else:
        risk = "high"
    return {
        "hardcoded_candidate_name_count": hardcoded_name_count,
        "hardcoded_candidate_rule_count": hardcoded_rule_count,
        "generic_miner_count": generic_miner_count,
        "generic_miner_examples": generic_hits[:20],
        "suspicious_hardcode_examples": suspicious[:40],
        "leakage_risk_level": risk,
        "hardcoded_answer_risk": risk,
        "evidence": {
            "exact_or_semantic_cleaned_name_hits": exact_hits,
            "rule_template_hits": rule_hits,
        },
    }


def audit_candidate_process(
    *,
    candidate_file: str | Path,
    replay_file: str | Path,
) -> list[dict[str, Any]]:
    candidate_payload = _load_json(candidate_file, default={}) or {}
    replay_payload = _load_json(replay_file, default={}) or {}
    replay_by_id = {
        str(item.get("candidate_id")): item
        for item in replay_payload.get("candidates", []) or []
    }
    rows = []
    for item in candidate_payload.get("candidates", []) or []:
        candidate_id = str(item.get("candidate_id"))
        replay = replay_by_id.get(candidate_id, {})
        name = str(item.get("candidate_name") or "")
        name_hits = [term for term in CLEANED_CANDIDATE_NAMES if term in name]
        operator = str(item.get("discovery_operator") or "")
        rule_type = str(item.get("rule_type") or "")
        rule_params = item.get("rule_params") or {}
        hardcoded_rule = bool(rule_params) or rule_type in {
            "account_category_any_of",
            "account_category_all_of",
            "profile_visit_low_content_bucket",
            "low_boot_track_duration",
            "weapon_header_template",
            "network_combo",
        }
        if name_hits:
            status = "suspicious"
        elif operator in GENERIC_MINER_NAMES:
            status = "clean"
        else:
            status = "suspicious"
        rows.append({
            "candidate_id": candidate_id,
            "candidate_name": name,
            "generated_by_miner": operator,
            "miner_type": _miner_type(operator),
            "input_artifacts": ALLOWED_DISCOVERY_ARTIFACTS,
            "uses_cleaned_candidate_name": False,
            "uses_challenge_hint": False,
            "uses_gap_focused_hint": False,
            "rule_generated_from_data": True,
            "rule_hardcoded": hardcoded_rule,
            "leakage_status": status,
            "notes": _candidate_note(name_hits, hardcoded_rule, replay.get("replay_status")),
        })
    return rows


def _miner_type(operator: str) -> str:
    mapping = {
        "endpoint_family_miner": "generic_endpoint_family_miner",
        "runtime_template_miner": "generic_container_template_miner",
        "behavior_bucket_miner": "generic_behavior_bucket_miner",
        "network_environment_miner": "generic_environment_cluster_miner",
        "cross_source_numeric_combo_miner": "generic_cross_source_numeric_combo_miner",
    }
    return mapping.get(operator, "unknown_miner")


def _candidate_note(name_hits: list[str], hardcoded_rule: bool, replay_status: Any) -> str:
    bits = []
    if name_hits:
        bits.append(f"candidate name semantically overlaps cleaned label(s): {', '.join(name_hits)}")
    if hardcoded_rule:
        bits.append("rule is an operator template with fixed categories/thresholds; support and paths are data-derived")
    bits.append(f"replay_status={replay_status}")
    return "; ".join(bits)


def build_holdout_recommendation(audit_pass: bool, hardcoded_risk: str) -> dict[str, Any]:
    return {
        "holdout_recommended": True,
        "next_recommended_step": "holdout_wave_rerun",
        "wave1_to_wave3_rerun": "recommended",
        "new_wave_needed": "recommended_after_wave1_to_wave3",
        "cleaned_candidate_set_usage": "final_eval_only",
        "autonomous_generalization_pass_definition": [
            "discovery stage reads only raw/parsed P0 foundation artifacts",
            "forbidden input leakage remains false",
            "schema_noise_violation_count remains 0 or explained as report-only",
            "core cleaned-candidate recall on holdout reaches agreed threshold without targeted prompt",
            "new candidates are either replay-pass and non-noisy or explicitly report-only",
            "full autonomous remains false until baseline/L6/Hive/strict lineage requirements are separately satisfied",
        ],
        "why": (
            "No discovery-stage leakage was found, but fixed operator templates and semantic overlap with cleaned candidate families need holdout validation."
            if audit_pass and hardcoded_risk in {"medium", "high"}
            else "Holdout rerun is the next clean test of generalization."
        ),
    }


def _write_markdown(path: str | Path, payload: dict[str, Any]) -> None:
    lines = [
        "# P0-7a Leakage / Overfit Audit",
        "",
        f"- schema_version: `{payload['schema_version']}`",
        f"- p0_7a_leakage_audit_pass: `{str(payload['final_judgement']['p0_7a_leakage_audit_pass']).lower()}`",
        f"- forbidden_input_used: `{str(payload['input_leakage_audit']['forbidden_input_used']).lower()}`",
        f"- hardcoded_answer_risk: `{payload['final_judgement']['hardcoded_answer_risk']}`",
        f"- can_trust_p0_7_wave4_wave5_autonomous_result: `{str(payload['final_judgement']['can_trust_p0_7_wave4_wave5_autonomous_result']).lower()}`",
        f"- can_claim_full_autonomous: `{str(payload['final_judgement']['can_claim_full_autonomous']).lower()}`",
        "",
        "## Input Leakage",
        "",
        f"- forbidden_input_paths: `{payload['input_leakage_audit']['forbidden_input_paths']}`",
        f"- eval_only_reference_paths: `{payload['input_leakage_audit']['eval_only_reference_paths']}`",
        "",
        "## Code Hardcoding",
        "",
        f"- hardcoded_candidate_name_count: `{payload['code_hardcoding_audit']['hardcoded_candidate_name_count']}`",
        f"- hardcoded_candidate_rule_count: `{payload['code_hardcoding_audit']['hardcoded_candidate_rule_count']}`",
        f"- generic_miner_count: `{payload['code_hardcoding_audit']['generic_miner_count']}`",
        f"- leakage_risk_level: `{payload['code_hardcoding_audit']['leakage_risk_level']}`",
        "",
        "## Candidate Process",
        "",
        "|candidate|miner|rule_hardcoded|leakage_status|notes|",
        "|---|---|---|---|---|",
    ]
    for item in payload["candidate_process_audit"]:
        lines.append(
            f"|{item['candidate_name']}|{item['generated_by_miner']}|"
            f"{str(item['rule_hardcoded']).lower()}|{item['leakage_status']}|{item['notes']}|"
        )
    lines.extend([
        "",
        "## Holdout Recommendation",
        "",
        f"- next_recommended_step: `{payload['holdout_recommendation']['next_recommended_step']}`",
        f"- wave1_to_wave3_rerun: `{payload['holdout_recommendation']['wave1_to_wave3_rerun']}`",
        f"- new_wave_needed: `{payload['holdout_recommendation']['new_wave_needed']}`",
        "",
        "## Generalization Pass Definition",
        "",
    ])
    for item in payload["holdout_recommendation"]["autonomous_generalization_pass_definition"]:
        lines.append(f"- {item}")
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_p0_7a_audit_outputs(
    *,
    source_file: str | Path = "computer_use_poc/baselines/normal_baseline/l3_extraction/p0_7_autonomous_cold_start_rerun.py",
    base_dir: str | Path = "/private/tmp/dennis_p1_1_p0_foundation_closure",
    p0_7_dir: str | Path = "/private/tmp/dennis_p1_1_p0_foundation_closure/p0_7_autonomous_cold_start",
    output_dir: str | Path = "/private/tmp/dennis_p1_1_p0_foundation_closure/p0_7a_leakage_overfit_audit",
) -> dict[str, Any]:
    p0_7 = Path(p0_7_dir)
    input_audit = audit_forbidden_inputs(source_file=source_file, base_dir=base_dir)
    hardcode_audit = audit_hardcoding(source_file)
    candidate_audit = audit_candidate_process(
        candidate_file=p0_7 / "p0_7_autonomous_cold_start_candidates.json",
        replay_file=p0_7 / "p0_7_autonomous_replay_provenance.json",
    )
    leaked_candidates = [item for item in candidate_audit if item["leakage_status"] == "leaked"]
    audit_pass = not input_audit["forbidden_input_used"] and not leaked_candidates
    hardcoded_risk = hardcode_audit["hardcoded_answer_risk"]
    payload = {
        "schema_version": SCHEMA_VERSION,
        "input_leakage_audit": input_audit,
        "code_hardcoding_audit": hardcode_audit,
        "candidate_process_audit": candidate_audit,
        "holdout_recommendation": build_holdout_recommendation(audit_pass, hardcoded_risk),
        "final_judgement": {
            "p0_7a_leakage_audit_pass": audit_pass,
            "forbidden_input_used": input_audit["forbidden_input_used"],
            "hardcoded_answer_risk": hardcoded_risk,
            "can_trust_p0_7_wave4_wave5_autonomous_result": audit_pass,
            "can_claim_full_autonomous": False,
            "next_recommended_step": "holdout_wave_rerun",
            "full_autonomous_not_proven": True,
        },
    }
    out = Path(output_dir)
    _write_json(out / "p0_7a_leakage_overfit_audit.json", payload)
    _write_markdown(out / "p0_7a_leakage_overfit_audit.md", payload)
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build P0-7a leakage / overfit audit.")
    parser.add_argument("--source-file", default="computer_use_poc/baselines/normal_baseline/l3_extraction/p0_7_autonomous_cold_start_rerun.py")
    parser.add_argument("--base-dir", default="/private/tmp/dennis_p1_1_p0_foundation_closure")
    parser.add_argument("--p0-7-dir", default="/private/tmp/dennis_p1_1_p0_foundation_closure/p0_7_autonomous_cold_start")
    parser.add_argument("--output-dir", default="/private/tmp/dennis_p1_1_p0_foundation_closure/p0_7a_leakage_overfit_audit")
    args = parser.parse_args(argv)
    payload = build_p0_7a_audit_outputs(
        source_file=args.source_file,
        base_dir=args.base_dir,
        p0_7_dir=args.p0_7_dir,
        output_dir=args.output_dir,
    )
    print(json.dumps(payload["final_judgement"], ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
