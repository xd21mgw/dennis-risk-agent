#!/usr/bin/env python3
"""P0-7b holdout rerun for autonomous cold-start miners.

This wrapper prepares P0 foundation artifacts for wave1-wave3, runs the
existing P0-7 autonomous miners against those holdout waves, then audits replay
results for schema noise and wave4/wave5 pattern overfit. It does not add new
candidate discovery logic and never calls platforms, Hive, DataAgent, release,
dist, or full_runtime paths.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from candidate_replay_provenance import build_context_from_smoke_dir
from p0_7_autonomous_cold_start_rerun import (
    AutonomousProposal,
    build_autonomous_provenance,
    discover_candidates_for_context,
    replay_proposal,
)
from p0_foundation_inventory import build_p0_foundation_outputs
from p0_foundation_quality_gate import build_quality_gate_summary


SCHEMA_VERSION = "p0_7b_holdout_wave_rerun_v1"
HOLDOUT_WAVES = ("wave_1", "wave_2", "wave_3")
ALLOWED_DISCOVERY_ARTIFACTS = [
    "full_action_inventory_raw_diff.json",
    "parsed_field_inventory.json",
    "container_parser_coverage_matrix.json",
    "schema_noise_guard_report.json",
]
FORBIDDEN_DISCOVERY_INPUTS = [
    "challenge_registry.md",
    "challenge_regression_coverage_audit.md",
    "gap-focused review output",
    "P0-5b cleaned candidate set as discovery input",
    "wave4/wave5 cleaned candidate names as discovery hints",
    "user challenge field checklist",
]

MINER_TYPE_BY_OPERATOR = {
    "endpoint_family_miner": "generic_endpoint_family_miner",
    "runtime_template_miner": "generic_runtime_template_miner",
    "behavior_bucket_miner": "generic_behavior_bucket_miner",
    "network_environment_miner": "generic_network_environment_miner",
    "cross_source_numeric_combo_miner": "generic_cross_source_numeric_combo_miner",
}

NETWORK_FIELD_TOKENS = {
    "oneipinfo",
    "asn",
    "isp",
    "country_code",
    "countrycode",
    "province",
    "city",
    "iprisklabel",
    "oneriskipidc",
    "labelinfo",
    "idcresult",
}
WAVE4_WAVE5_PATTERN_TERMS = {
    "account_mutation",
    "reset",
    "rebind",
    "weapon_runtime",
    "profile_visit",
    "low_bootcount",
    "track_high_duration",
    "network_provider",
    "hk_location",
    "idc_network",
}
INTERNAL_NOISE_TOKENS = {
    "clientip",
    "serverip",
    "serverinfo",
    "kwaidc.com",
    "traceid",
    "requestid",
}
SDK_CONFIG_NOISE_TOKENS = {
    "passportsdksidconfig",
    "kconf.key",
    "sidinstaticcode",
    "sdkconfig.confcontent",
}


def _load_json(path: str | Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: str | Path, payload: Any) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _container_status(matrix_payload: dict[str, Any], container_name: str) -> dict[str, Any]:
    rows = [
        row for row in matrix_payload.get("matrix", [])
        if row.get("container_name") == container_name
    ]
    if not rows:
        return {
            "container_name": container_name,
            "attempted": 0,
            "success": 0,
            "error": 0,
            "raw_present": False,
            "parse_attempted": 0,
            "parse_success": 0,
            "scanner_gap_reason": "raw_absent",
            "status": "DATA_GAP",
        }
    attempted = sum(int(row.get("attempted") or 0) for row in rows)
    success = sum(int(row.get("success") or 0) for row in rows)
    error = sum(int(row.get("error") or 0) for row in rows)
    parse_attempted = sum(int(row.get("parse_attempted") or 0) for row in rows)
    parse_success = sum(int(row.get("parse_success") or 0) for row in rows)
    raw_present = any(bool(row.get("raw_present")) for row in rows)
    reasons = sorted({str(row.get("scanner_gap_reason") or "") for row in rows if row.get("scanner_gap_reason")})
    if not raw_present:
        status = "DATA_GAP"
    elif parse_attempted > 0 and parse_success > 0 and error == 0:
        status = "PASS"
    elif parse_attempted == 0:
        status = "SCANNER_GAP"
    else:
        status = "PARTIAL"
    return {
        "container_name": container_name,
        "attempted": attempted,
        "success": success,
        "error": error,
        "raw_present": raw_present,
        "parse_attempted": parse_attempted,
        "parse_success": parse_success,
        "scanner_gap_reason": ",".join(reasons),
        "status": status,
    }


def prepare_holdout_foundation(
    *,
    raw_bundle_base: str | Path,
    foundation_base_dir: str | Path,
    inventory_path: str | Path,
    waves: tuple[str, ...] = HOLDOUT_WAVES,
    force_rebuild: bool = False,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    foundation_base = Path(foundation_base_dir)
    raw_base = Path(raw_bundle_base)
    required = [
        "full_action_inventory_raw_diff.json",
        "parsed_field_inventory.json",
        "container_parser_coverage_matrix.json",
        "schema_noise_guard_report.json",
    ]
    for wave_id in waves:
        smoke_dir = foundation_base / f"{wave_id}_smoke"
        if force_rebuild or not all((smoke_dir / name).exists() for name in required):
            build_p0_foundation_outputs(
                wave_dir=raw_base / wave_id,
                inventory_path=inventory_path,
                output_dir=smoke_dir,
            )
        gate = build_quality_gate_summary(
            smoke_dir=smoke_dir,
            inventory_path=inventory_path,
            output_dir=smoke_dir,
        )
        smoke_summary = _load_json(smoke_dir / "p0_foundation_smoke_summary.json")
        containers = _load_json(smoke_dir / "container_parser_coverage_matrix.json")
        decisions = gate["quality_gate_decision"]
        foundation_gap = not all(
            decisions[key]
            for key in (
                "p0_1_raw_diff_quality_pass",
                "p0_2_parsed_inventory_quality_pass",
                "p0_3_container_coverage_quality_pass",
                "p0_4_schema_guard_quality_pass",
            )
        )
        out.append({
            "wave_id": wave_id,
            "smoke_dir": str(smoke_dir),
            "raw_total": smoke_summary.get("raw_total_fields"),
            "normalized_seen": smoke_summary.get("normalized_inventory_seen_fields"),
            "normalized_missing": smoke_summary.get("normalized_missing_fields"),
            "true_missing": smoke_summary.get("true_missing_fields"),
            "parsed_rate": smoke_summary.get("parsed_success_rate"),
            "container_rate": smoke_summary.get("container_success_rate"),
            "schema_guard_count": smoke_summary.get("guarded_noise_count"),
            "report_only_count": smoke_summary.get("report_only_count"),
            "appList_status": _container_status(containers, "appList"),
            "enabledAccessibilityServices_status": _container_status(containers, "enabledAccessibilityServices"),
            "quality_gate_decision": decisions,
            "foundation_gap": foundation_gap,
            "foundation_gap_reasons": [
                key for key, value in decisions.items()
                if key.startswith("p0_") and not value
            ],
        })
    return out


def _text_for_evidence(item: dict[str, Any]) -> str:
    parts: list[str] = [
        str(item.get("candidate_name") or ""),
        str(item.get("proposed_replay_rule") or ""),
        json.dumps(item.get("rule_params") or {}, ensure_ascii=False),
    ]
    for ev in item.get("evidence_snippets") or []:
        parts.extend([
            str(ev.get("source_action") or ""),
            str(ev.get("raw_path") or ""),
            str(ev.get("parsed_path") or ""),
            str(ev.get("normalized_path") or ""),
            str(ev.get("value_summary") or ""),
        ])
    return " ".join(parts).lower()


def _has_network_semantic_field(item: dict[str, Any]) -> bool:
    for ev in item.get("evidence_snippets") or []:
        path = f"{ev.get('raw_path', '')} {ev.get('parsed_path', '')} {ev.get('normalized_path', '')}".lower()
        if any(token in path for token in NETWORK_FIELD_TOKENS):
            return True
    return False


def audit_holdout_candidate(item: dict[str, Any]) -> dict[str, Any]:
    text = _text_for_evidence(item)
    name = str(item.get("candidate_name") or "").lower()
    rule_type = str(item.get("rule_type") or "")
    support = int(item.get("support_user_count") or 0)
    coverage = int(item.get("coverage_user_count") or 0)
    level = str(item.get("candidate_level") or "")
    report_only_fields = list(item.get("report_only_fields_used") or [])
    reasons: list[str] = []

    schema_noise_violation = bool(item.get("schema_guard_conflict"))
    report_only_misused = level == "high_value" and bool(report_only_fields)
    if report_only_misused:
        reasons.append("high_value_candidate_uses_report_only_fields")
    if schema_noise_violation:
        reasons.append("schema_guard_conflict")

    internal_noise = any(token in text for token in INTERNAL_NOISE_TOKENS)
    if internal_noise:
        reasons.append("internal_platform_network_or_trace_noise")

    sdk_config_noise = (
        rule_type in {"network_category_any_of", "network_combo"}
        and any(token in text for token in SDK_CONFIG_NOISE_TOKENS)
        and not _has_network_semantic_field(item)
    )
    if sdk_config_noise:
        reasons.append("sdk_config_idc_substring_false_positive")

    pattern_overfit = any(term in name for term in WAVE4_WAVE5_PATTERN_TERMS)
    if pattern_overfit and (sdk_config_noise or internal_noise or schema_noise_violation):
        reasons.append("wave4_wave5_pattern_overfit_without_valid_holdout_semantics")

    hardcoded_rule_low_support = support < 3 or (coverage > 0 and support / max(coverage, 1) < 0.3)
    if hardcoded_rule_low_support:
        reasons.append("hardcoded_rule_low_support_or_sparse_coverage")

    false_or_noisy = bool(
        schema_noise_violation
        or report_only_misused
        or internal_noise
        or sdk_config_noise
        or (pattern_overfit and sdk_config_noise)
    )
    leakage_status = "suspicious" if false_or_noisy or hardcoded_rule_low_support else "clean"
    return {
        "candidate_id": item.get("candidate_id"),
        "candidate_name": item.get("candidate_name"),
        "false_or_noisy": false_or_noisy,
        "wave4_wave5_pattern_overfit": bool(pattern_overfit and false_or_noisy),
        "schema_noise_violation": schema_noise_violation,
        "report_only_misused": report_only_misused,
        "hardcoded_rule_low_support": hardcoded_rule_low_support,
        "leakage_status": leakage_status,
        "audit_reasons": reasons,
    }


def _candidate_record(proposal: AutonomousProposal, replay_item: dict[str, Any], audit: dict[str, Any]) -> dict[str, Any]:
    data = proposal.as_dict()
    return {
        **data,
        "generated_by_miner": proposal.discovery_operator,
        "miner_type": MINER_TYPE_BY_OPERATOR.get(proposal.discovery_operator, "generic_miner"),
        "schema_guard_applied": bool(replay_item.get("schema_guard_applied")),
        "report_only_fields_used": replay_item.get("report_only_fields_used") or [],
        "leakage_status": audit["leakage_status"],
    }


def _write_candidates_md(path: str | Path, payload: dict[str, Any]) -> None:
    lines = [
        "# P0-7b Holdout Wave Candidates",
        "",
        "- discovery_input_boundary: wave1-wave3 P0 foundation artifacts only.",
        "- forbidden_inputs_used: false",
        f"- holdout_candidate_count: {len(payload['candidates'])}",
        "",
        "|wave|candidate|miner|signal|level|confidence|pre_support|leakage_status|",
        "|---|---|---|---|---|---|---:|---|",
    ]
    for row in payload["candidates"]:
        lines.append(
            f"|{row['wave_id']}|{row['candidate_name']}|{row['generated_by_miner']}|"
            f"{row['signal_type']}|{row['candidate_level']}|{row['confidence']}|"
            f"{row['support_user_count_pre_replay']}|{row['leakage_status']}|"
        )
    lines.extend(["", "## Foundation Gaps", ""])
    for row in payload["foundation_preparation"]:
        if row["foundation_gap"]:
            lines.append(f"- {row['wave_id']}: {', '.join(row['foundation_gap_reasons'])}")
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_replay_md(path: str | Path, payload: dict[str, Any]) -> None:
    audit_by_id = {row["candidate_id"]: row for row in payload["overfit_candidate_audit"]}
    lines = [
        "# P0-7b Holdout Replay Provenance",
        "",
        "- replay_scope: support/miss/coverage recomputation for holdout autonomous proposals.",
        "- verified_strategy: false",
        "",
        "|wave|candidate|support|miss|coverage|status|level|audit|",
        "|---|---|---:|---:|---:|---|---|---|",
    ]
    for item in payload["candidates"]:
        audit = audit_by_id.get(item["candidate_id"], {})
        lines.append(
            f"|{item['wave_id']}|{item['candidate_name']}|{item['support_user_count']}|"
            f"{item['miss_user_count']}|{item['coverage_user_count']}|{item['replay_status']}|"
            f"{item['candidate_level']}|{audit.get('leakage_status', 'unknown')}|"
        )
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_eval_md(path: str | Path, payload: dict[str, Any]) -> None:
    s = payload["summary"]
    lines = [
        "# P0-7b Holdout Eval",
        "",
        f"- p0_7b_holdout_pass: `{str(s['p0_7b_holdout_pass']).lower()}`",
        f"- overfit_risk_level: `{s['overfit_risk_level']}`",
        f"- can_claim_full_autonomous: `{str(s['can_claim_full_autonomous']).lower()}`",
        f"- full_autonomous_not_proven: `{str(s['full_autonomous_not_proven']).lower()}`",
        "",
        "|metric|value|",
        "|---|---:|",
    ]
    for key in (
        "holdout_candidate_count",
        "replay_pass_count",
        "replay_partial_count",
        "replay_failed_count",
        "high_value_count",
        "supporting_count",
        "report_only_count",
        "data_gap_count",
        "false_or_noisy_candidate_count",
        "schema_noise_violation_count",
        "wave4_wave5_pattern_overfit_count",
        "report_only_misused_count",
        "hardcoded_rule_low_support_count",
    ):
        lines.append(f"|{key}|{s[key]}|")
    lines.extend(["", "## Foundation", ""])
    lines.extend(["|wave|raw_total|normalized_seen|true_missing|parsed_rate|container_rate|foundation_gap|", "|---|---:|---:|---:|---:|---:|---|"])
    for row in payload["foundation_preparation"]:
        lines.append(
            f"|{row['wave_id']}|{row['raw_total']}|{row['normalized_seen']}|{row['true_missing']}|"
            f"{row['parsed_rate']}|{row['container_rate']}|{str(row['foundation_gap']).lower()}|"
        )
    lines.extend(["", "## False / Noisy Candidates", ""])
    noisy = [row for row in payload["overfit_candidate_audit"] if row["false_or_noisy"]]
    if not noisy:
        lines.append("- None")
    else:
        for row in noisy:
            lines.append(f"- {row['candidate_name']}: {', '.join(row['audit_reasons'])}")
    lines.extend(["", "## Remaining Gap", ""])
    for gap in payload["remaining_gap"]:
        lines.append(f"- {gap}")
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_holdout_outputs(
    *,
    raw_bundle_base: str | Path = "/private/tmp/dennis_multiwave_live_raw_bundle",
    foundation_base_dir: str | Path = "/private/tmp/dennis_p1_1_p0_foundation_closure",
    inventory_path: str | Path = "/private/tmp/dennis_p1_1_cold_start_discovery/full_action_field_inventory.json",
    output_dir: str | Path = "/private/tmp/dennis_p1_1_p0_foundation_closure/p0_7b_holdout_wave_rerun",
    waves: tuple[str, ...] = HOLDOUT_WAVES,
    force_foundation_rebuild: bool = False,
) -> dict[str, Any]:
    foundation = prepare_holdout_foundation(
        raw_bundle_base=raw_bundle_base,
        foundation_base_dir=foundation_base_dir,
        inventory_path=inventory_path,
        waves=waves,
        force_rebuild=force_foundation_rebuild,
    )
    base = Path(foundation_base_dir)
    contexts = {
        wave_id: build_context_from_smoke_dir(base / f"{wave_id}_smoke", wave_id)
        for wave_id in waves
    }

    proposals: list[AutonomousProposal] = []
    for wave_id in waves:
        proposals.extend(discover_candidates_for_context(contexts[wave_id]))
    replay_items = [
        replay_proposal(contexts[proposal.wave_id], proposal)
        for proposal in proposals
    ]
    audits = [audit_holdout_candidate(item) for item in replay_items]
    candidates = [
        _candidate_record(proposal, replay_item, audit)
        for proposal, replay_item, audit in zip(proposals, replay_items, audits)
    ]
    provenance = build_autonomous_provenance(replay_items)
    status_counts = Counter(item["replay_status"] for item in replay_items)
    level_counts = Counter(item.get("candidate_level") for item in replay_items)
    false_or_noisy = sum(1 for row in audits if row["false_or_noisy"])
    schema_noise = sum(1 for row in audits if row["schema_noise_violation"])
    pattern_overfit = sum(1 for row in audits if row["wave4_wave5_pattern_overfit"])
    report_only_misused = sum(1 for row in audits if row["report_only_misused"])
    hardcoded_low_support = sum(1 for row in audits if row["hardcoded_rule_low_support"])
    foundation_gap_waves = [row["wave_id"] for row in foundation if row["foundation_gap"]]

    if false_or_noisy or pattern_overfit:
        overfit_risk_level = "high"
    elif hardcoded_low_support:
        overfit_risk_level = "medium"
    else:
        overfit_risk_level = "low"
    candidate_count = len(replay_items)
    p0_7b_pass = bool(
        candidate_count > 0
        and status_counts.get("replay_failed", 0) == 0
        and false_or_noisy == 0
        and schema_noise == 0
        and pattern_overfit == 0
        and overfit_risk_level == "low"
    )
    summary = {
        "p0_7b_holdout_pass": p0_7b_pass,
        "holdout_candidate_count": candidate_count,
        "replay_pass_count": status_counts.get("replay_pass", 0),
        "replay_partial_count": status_counts.get("replay_partial", 0),
        "replay_failed_count": status_counts.get("replay_failed", 0),
        "high_value_count": level_counts.get("high_value", 0),
        "supporting_count": level_counts.get("supporting", 0),
        "report_only_count": level_counts.get("report_only", 0),
        "data_gap_count": level_counts.get("data_gap", 0),
        "false_or_noisy_candidate_count": false_or_noisy,
        "schema_noise_violation_count": schema_noise,
        "wave4_wave5_pattern_overfit_count": pattern_overfit,
        "report_only_misused_count": report_only_misused,
        "hardcoded_rule_low_support_count": hardcoded_low_support,
        "overfit_risk_level": overfit_risk_level,
        "can_trust_holdout_result": True,
        "can_claim_full_autonomous": False,
        "full_autonomous_not_proven": True,
        "next_recommended_step": (
            "miner_generalization_refactor"
            if false_or_noisy or pattern_overfit
            else "broader_new_wave_holdout"
        ),
        "foundation_gap_waves": foundation_gap_waves,
    }

    candidate_payload = {
        "schema_version": SCHEMA_VERSION,
        "discovery_boundary": {
            "allowed_inputs": ALLOWED_DISCOVERY_ARTIFACTS,
            "forbidden_inputs_not_used": FORBIDDEN_DISCOVERY_INPUTS,
            "challenge_registry_used": False,
            "gap_focused_output_used": False,
            "cleaned_candidate_set_used_for_discovery": False,
            "wave4_wave5_cleaned_candidate_names_used_as_discovery_hints": False,
        },
        "foundation_preparation": foundation,
        "candidates": candidates,
    }
    replay_payload = {
        "schema_version": SCHEMA_VERSION,
        "replay_boundary": {
            "cleaned_candidate_set_used_for_replay": False,
            "verified_strategy": False,
            "baseline_used": False,
            "hive_or_dataagent_used": False,
            "strict_device_id_join_used": False,
        },
        "candidates": replay_items,
        "provenance": provenance,
        "overfit_candidate_audit": audits,
    }
    remaining_gap = [
        "Holdout replay still proves only support/miss/coverage recomputation, not verified strategy quality.",
        "No normal baseline, L6/Hive replay, population false-positive validation, or strict device_id join was run.",
        "Wave1 has a P0-3 container coverage foundation gap and must not be treated as full source closure.",
    ]
    if false_or_noisy:
        remaining_gap.append(
            "At least one holdout network candidate is spurious under replay evidence and requires miner generalization cleanup before claiming broader autonomy."
        )
    elif candidate_count == 0:
        remaining_gap.append(
            "No holdout candidate remains after network miner refactor; this removes the false positive but does not prove positive holdout recall."
        )
    eval_payload = {
        "schema_version": SCHEMA_VERSION,
        "evaluation_boundary": {
            "cleaned_candidate_set_used_for_discovery": False,
            "cleaned_candidate_set_used_for_replay": False,
            "cleaned_candidate_set_used_for_final_eval": False,
            "challenge_registry_used": False,
            "gap_focused_output_used": False,
            "verified_strategy": False,
        },
        "summary": summary,
        "foundation_preparation": foundation,
        "overfit_candidate_audit": audits,
        "remaining_gap": remaining_gap,
    }

    out = Path(output_dir)
    _write_json(out / "p0_7b_holdout_wave_candidates.json", candidate_payload)
    _write_candidates_md(out / "p0_7b_holdout_wave_candidates.md", candidate_payload)
    _write_json(out / "p0_7b_holdout_replay_provenance.json", replay_payload)
    _write_replay_md(out / "p0_7b_holdout_replay_provenance.md", replay_payload)
    _write_json(out / "p0_7b_holdout_eval.json", eval_payload)
    _write_eval_md(out / "p0_7b_holdout_eval.md", eval_payload)
    return {
        "candidates": candidate_payload,
        "replay": replay_payload,
        "eval": eval_payload,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run P0-7b holdout wave rerun from local P0 foundation artifacts.")
    parser.add_argument("--raw-bundle-base", default="/private/tmp/dennis_multiwave_live_raw_bundle")
    parser.add_argument("--foundation-base-dir", default="/private/tmp/dennis_p1_1_p0_foundation_closure")
    parser.add_argument("--inventory", default="/private/tmp/dennis_p1_1_cold_start_discovery/full_action_field_inventory.json")
    parser.add_argument("--output-dir", default="/private/tmp/dennis_p1_1_p0_foundation_closure/p0_7b_holdout_wave_rerun")
    parser.add_argument("--force-foundation-rebuild", action="store_true")
    args = parser.parse_args(argv)
    payload = build_holdout_outputs(
        raw_bundle_base=args.raw_bundle_base,
        foundation_base_dir=args.foundation_base_dir,
        inventory_path=args.inventory,
        output_dir=args.output_dir,
        force_foundation_rebuild=args.force_foundation_rebuild,
    )
    print(json.dumps(payload["eval"]["summary"], ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
