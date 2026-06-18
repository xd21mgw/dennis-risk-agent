#!/usr/bin/env python3
"""Build the P0-7c network miner generalization refactor report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


BEFORE = {
    "wave1_holdout_candidate_count": 1,
    "false_or_noisy_candidate_count": 1,
    "overfit_risk_level": "high",
}

NETWORK_CANDIDATE_MAP = {
    "autonomous_network_provider_asn_cluster": "zenlayer_asn_cluster",
    "autonomous_hk_location_supporting_cluster": "hk_location_supporting",
    "autonomous_idc_network_supporting_cluster": "idc_network_supporting",
    "autonomous_network_environment_combo_cluster": "network_environment_cluster",
}


def _load_json(path: str | Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: str | Path, payload: Any) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _network_sanity(replay_payload: dict[str, Any]) -> tuple[bool, list[dict[str, Any]]]:
    network: list[dict[str, Any]] = []
    for candidate in replay_payload.get("candidates", []):
        name = str(candidate.get("candidate_name") or "")
        if candidate.get("wave_id") != "wave_5" or name not in NETWORK_CANDIDATE_MAP:
            continue
        roles = sorted({
            str(ev.get("field_role") or "")
            for ev in candidate.get("evidence_snippets", [])
            if ev.get("field_role")
        })
        network.append({
            "candidate_name": name,
            "mapped_cleaned_candidate": NETWORK_CANDIDATE_MAP[name],
            "support": candidate.get("support_user_count"),
            "miss": candidate.get("miss_user_count"),
            "coverage": candidate.get("coverage_user_count"),
            "replay_status": candidate.get("replay_status"),
            "sample_field_roles": roles,
        })
    mapped = {row["mapped_cleaned_candidate"] for row in network}
    required = set(NETWORK_CANDIDATE_MAP.values())
    ok = bool(required <= mapped and all(row["replay_status"] == "replay_pass" for row in network))
    return ok, network


def build_report(*, base_dir: str | Path, output_dir: str | Path) -> dict[str, Any]:
    base = Path(base_dir)
    holdout = _load_json(base / "p0_7b_holdout_wave_rerun" / "p0_7b_holdout_eval.json")
    p0_7_replay = _load_json(base / "p0_7_autonomous_cold_start" / "p0_7_autonomous_replay_provenance.json")
    p0_7_eval = _load_json(base / "p0_7_autonomous_cold_start" / "p0_7_autonomous_discovery_eval.json")
    after = holdout["summary"]
    network_ok, network = _network_sanity(p0_7_replay)
    final = {
        "p0_7c_network_miner_refactor_pass": bool(
            after["holdout_candidate_count"] == 0
            and after["false_or_noisy_candidate_count"] == 0
            and after["schema_noise_violation_count"] == 0
            and network_ok
        ),
        "wave1_false_network_candidate_removed": after["holdout_candidate_count"] == 0,
        "wave1_holdout_candidate_count_before": BEFORE["wave1_holdout_candidate_count"],
        "wave1_holdout_candidate_count_after": after["holdout_candidate_count"],
        "false_or_noisy_candidate_count_before": BEFORE["false_or_noisy_candidate_count"],
        "false_or_noisy_candidate_count_after": after["false_or_noisy_candidate_count"],
        "wave4_wave5_network_candidates_still_replay": network_ok,
        "schema_noise_violation_count": after["schema_noise_violation_count"],
        "overfit_risk_level_before": BEFORE["overfit_risk_level"],
        "overfit_risk_level_after": after["overfit_risk_level"],
        "can_claim_full_autonomous": False,
        "full_autonomous_not_proven": True,
        "next_recommended_step": "broader_new_wave_holdout",
    }
    report = {
        "schema_version": "p0_7c_miner_generalization_refactor_report_v1",
        "root_cause": {
            "false_candidate_name": "autonomous_idc_network_supporting_cluster",
            "trigger_source_action": "login_logs_search",
            "trigger_raw_path": "upstream.body.data",
            "trigger_parsed_path": "upstream.body.data.logSearchModels.logContent.sdkConfig.confContent.kconf.key",
            "trigger_values": [
                "infraService.passportSdkSidConfig.kuaishouVisionConfig",
                "infraService.passportSdkSidConfig.adminInstitution",
                "infraService.passportSdkSidConfig.kuaishouWeb",
                "sidInStaticCode",
            ],
            "why_current_miner_misjudged": (
                "The old network miner used broad string contains over whole row text. "
                "sdkConfig/kconf keys containing idc/sid/static were treated like IDC "
                "network evidence even though the path was a config key, not network telemetry."
            ),
            "correct_classification": [
                "schema/config/string_noise",
                "sdk_config_key",
                "report_only",
                "not_network_evidence",
            ],
        },
        "refactor_summary": {
            "field_role_inference_added": True,
            "network_roles_allowed": [
                "network_asn",
                "network_isp",
                "network_idc",
                "network_location",
                "network_ip",
            ],
            "guarded_roles": [
                "sdk_config_key",
                "internal_platform_ip",
                "schema_noise",
                "unknown",
            ],
            "trusted_source_semantics": [
                "Weapon oneIpInfo/ipInfo/IPP labelInfo",
                "Track province/city/location profile",
                "Archives lastLoginLocation/startUpLocation/userIpDesc",
                "login source/user IP fields with explicit IP semantics",
            ],
            "blocked_noise": [
                "sdkConfig/kconf/config key",
                "sidInStaticCode",
                "passportSdkSidConfig-like config keys",
                "internal serverIp/clientIp/serverInfo",
                "kwaidc.com internal platform host",
                "trace/request/schema metadata",
            ],
        },
        "before": BEFORE,
        "after": {
            "wave1_holdout_candidate_count": after["holdout_candidate_count"],
            "false_or_noisy_candidate_count": after["false_or_noisy_candidate_count"],
            "schema_noise_violation_count": after["schema_noise_violation_count"],
            "wave4_wave5_pattern_overfit_count": after["wave4_wave5_pattern_overfit_count"],
            "overfit_risk_level": after["overfit_risk_level"],
            "p0_7b_holdout_pass": after["p0_7b_holdout_pass"],
            "next_recommended_step": after["next_recommended_step"],
        },
        "wave4_wave5_network_sanity": {
            "wave4_wave5_network_candidates_still_replay": network_ok,
            "network_candidates": network,
            "p0_7_eval_summary": p0_7_eval["summary"],
        },
        "final_judgement": final,
        "output_paths": {
            "updated_p0_7b_holdout_eval_json": str(base / "p0_7b_holdout_wave_rerun" / "p0_7b_holdout_eval.json"),
            "updated_p0_7b_holdout_eval_md": str(base / "p0_7b_holdout_wave_rerun" / "p0_7b_holdout_eval.md"),
            "updated_p0_7_autonomous_discovery_eval_json": str(base / "p0_7_autonomous_cold_start" / "p0_7_autonomous_discovery_eval.json"),
            "updated_p0_7_autonomous_discovery_eval_md": str(base / "p0_7_autonomous_cold_start" / "p0_7_autonomous_discovery_eval.md"),
        },
    }
    out = Path(output_dir)
    _write_json(out / "p0_7c_miner_generalization_refactor_report.json", report)
    _write_markdown(out / "p0_7c_miner_generalization_refactor_report.md", report)
    return report


def _write_markdown(path: str | Path, report: dict[str, Any]) -> None:
    final = report["final_judgement"]
    root = report["root_cause"]
    before = report["before"]
    after = report["after"]
    lines = [
        "# P0-7c Miner Generalization Refactor Report",
        "",
        f"- p0_7c_network_miner_refactor_pass: `{str(final['p0_7c_network_miner_refactor_pass']).lower()}`",
        f"- wave1_false_network_candidate_removed: `{str(final['wave1_false_network_candidate_removed']).lower()}`",
        "- can_claim_full_autonomous: `false`",
        "- full_autonomous_not_proven: `true`",
        "",
        "## Root Cause",
        "",
        f"- false_candidate: `{root['false_candidate_name']}`",
        f"- trigger_source_action: `{root['trigger_source_action']}`",
        f"- trigger_parsed_path: `{root['trigger_parsed_path']}`",
        f"- trigger_values: {', '.join(root['trigger_values'])}",
        f"- cause: {root['why_current_miner_misjudged']}",
        f"- correct_classification: {', '.join(root['correct_classification'])}",
        "",
        "## Before / After",
        "",
        "|metric|before|after|",
        "|---|---:|---:|",
        f"|wave1_holdout_candidate_count|{before['wave1_holdout_candidate_count']}|{after['wave1_holdout_candidate_count']}|",
        f"|false_or_noisy_candidate_count|{before['false_or_noisy_candidate_count']}|{after['false_or_noisy_candidate_count']}|",
        f"|schema_noise_violation_count|-|{after['schema_noise_violation_count']}|",
        f"|overfit_risk_level|{before['overfit_risk_level']}|{after['overfit_risk_level']}|",
        "",
        "## Wave4/Wave5 Network Sanity",
        "",
        "|candidate|mapped_cleaned|support|status|roles|",
        "|---|---|---:|---|---|",
    ]
    for item in report["wave4_wave5_network_sanity"]["network_candidates"]:
        lines.append(
            f"|{item['candidate_name']}|{item['mapped_cleaned_candidate']}|"
            f"{item['support']}|{item['replay_status']}|{', '.join(item['sample_field_roles'])}|"
        )
    lines.extend([
        "",
        "## Remaining Boundary",
        "",
        "- This fixes one network miner generalization bug; it does not prove full autonomous discovery.",
        "- Holdout wave1-wave3 now has no false network candidate, but also no positive holdout candidate after refactor.",
        "- No baseline, L6/Hive replay, strict device_id join, or new-wave validation was run.",
        "- next_recommended_step: `broader_new_wave_holdout`",
    ])
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build P0-7c network miner refactor report.")
    parser.add_argument("--base-dir", default="/private/tmp/dennis_p1_1_p0_foundation_closure")
    parser.add_argument("--output-dir", default="/private/tmp/dennis_p1_1_p0_foundation_closure/p0_7c_miner_generalization_refactor")
    args = parser.parse_args(argv)
    report = build_report(base_dir=args.base_dir, output_dir=args.output_dir)
    print(json.dumps(report["final_judgement"], ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
