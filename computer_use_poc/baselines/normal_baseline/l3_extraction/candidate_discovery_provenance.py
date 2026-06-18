#!/usr/bin/env python3
"""P0-6 candidate discovery provenance builder.

This module is intentionally offline and provenance-only. It reads existing
P0-5b replay outputs, cold-start reports, and challenge registry documents to
label whether each replayable candidate was originally found autonomously,
introduced by targeted follow-up, or derived by taxonomy cleanup. It does not
discover new candidates and does not call platforms, Hive, DataAgent, baseline,
L6 replay, release, dist, or full_runtime paths.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "p0_6_candidate_discovery_provenance_v1"
SOURCE_ENUM = {
    "cold_start_autonomous",
    "gap_focused_targeted",
    "user_challenge_regression",
    "manual_review",
    "taxonomy_cleanup_derived",
    "replay_only",
    "unknown",
}


@dataclass(frozen=True)
class CandidateRule:
    cold_aliases: tuple[str, ...] = ()
    related_user_challenge_id: str = ""
    related_gap_focused_blocker: str = ""
    current_candidate_source: str | None = None
    original_discovery_source: str | None = None
    cold_confidence: str = "high"
    notes: str = ""


@dataclass(frozen=True)
class TaxonomyInfo:
    parent_candidate_id: str
    parent_candidate_name: str
    split_from: str
    renamed_from: str
    reason: str


CANDIDATE_RULES: dict[tuple[str, str], CandidateRule] = {
    ("wave_4", "account_mutation_chain"): CandidateRule(
        cold_aliases=("account_mutation_event_chain",),
        related_user_challenge_id="CH-008",
        related_gap_focused_blocker="account_mutation_chain_builder",
        notes="Cold start found the broad account mutation event family; current name came from P0-5b taxonomy cleanup.",
    ),
    ("wave_4", "reset_password_chain"): CandidateRule(
        cold_aliases=("reset_or_rebind_event_chain",),
        related_user_challenge_id="CH-008",
        related_gap_focused_blocker="account_mutation_chain_builder",
        notes="Narrow reset-password semantics were split from the broader cold-start reset/rebind family.",
    ),
    ("wave_4", "mobile_rebind_chain"): CandidateRule(
        cold_aliases=("reset_or_rebind_event_chain",),
        related_user_challenge_id="CH-008",
        related_gap_focused_blocker="account_mutation_chain_builder",
        notes="Mobile rebind semantics were split from the broader cold-start reset/rebind family.",
    ),
    ("wave_4", "reset_and_rebind_chain"): CandidateRule(
        cold_aliases=("reset_or_rebind_event_chain",),
        related_user_challenge_id="CH-008",
        related_gap_focused_blocker="account_mutation_chain_builder",
        notes="Strict reset+rebind all-of semantics were created by taxonomy cleanup from the broader family.",
    ),
    ("wave_4", "profile_set_modify_mutation_chain"): CandidateRule(
        related_user_challenge_id="CH-008",
        related_gap_focused_blocker="account_mutation_chain_builder",
        current_candidate_source="gap_focused_targeted",
        original_discovery_source="gap_focused_targeted",
        notes="Profile set/modify replay was selected during targeted account/profile mutation follow-up, not proven cold-start autonomous.",
    ),
    ("wave_5", "weapon_decode_header_runtime_template"): CandidateRule(
        cold_aliases=("weapon_runtime_value_template",),
        related_user_challenge_id="CH-012",
        related_gap_focused_blocker="weapon_decode_header_template_extractor",
        current_candidate_source="user_challenge_regression",
        notes="Cold start found a Weapon runtime/header template; the current field-level header template was tightened after user challenge CH-012.",
    ),
    ("wave_5", "profile_visit_low_content_behavior"): CandidateRule(
        cold_aliases=("high_profile_visit_low_content",),
        related_user_challenge_id="CH-017",
        related_gap_focused_blocker="social_funnel_chain_builder",
        notes="The >=1 visit bucket is a taxonomy-cleanup split from the cold-start social funnel candidate.",
    ),
    ("wave_5", "high_profile_visit_low_content_behavior"): CandidateRule(
        cold_aliases=("high_profile_visit_low_content",),
        related_user_challenge_id="CH-017",
        related_gap_focused_blocker="social_funnel_chain_builder",
        notes="The high-threshold bucket inherits the cold-start social funnel parent but is a cleaned-up threshold candidate.",
    ),
    ("wave_5", "extreme_profile_visit_low_content_behavior"): CandidateRule(
        cold_aliases=("high_profile_visit_low_content",),
        related_user_challenge_id="CH-017",
        related_gap_focused_blocker="social_funnel_chain_builder",
        notes="The extreme-threshold bucket is a taxonomy-cleanup derivative of the cold-start social funnel candidate.",
    ),
    ("wave_5", "low_bootcount_with_track_high_duration"): CandidateRule(
        related_user_challenge_id="CH-015",
        related_gap_focused_blocker="low_boot_track_lineage_chain",
        current_candidate_source="user_challenge_regression",
        original_discovery_source="user_challenge_regression",
        notes="Cold start saw near-24h Track duration, but the low bootCount + Track duration + partial lineage combo was user-challenged and targeted.",
    ),
    ("wave_5", "zenlayer_asn_cluster"): CandidateRule(
        cold_aliases=("network_location_pattern",),
        related_user_challenge_id="CH-010",
        related_gap_focused_blocker="network_idc_cluster_builder",
        cold_confidence="medium",
        notes="Cold start found network location/provider commonality; Zenlayer/ASN was split as the core condition by taxonomy cleanup.",
    ),
    ("wave_5", "hk_location_supporting"): CandidateRule(
        cold_aliases=("network_location_pattern",),
        related_user_challenge_id="CH-010",
        related_gap_focused_blocker="network_idc_cluster_builder",
        cold_confidence="medium",
        notes="HK location support inherits a broader cold-start network-location finding but current support semantics are cleanup-derived.",
    ),
    ("wave_5", "idc_network_supporting"): CandidateRule(
        cold_aliases=("weapon_risk_label_commonality", "network_location_pattern"),
        related_user_challenge_id="CH-010",
        related_gap_focused_blocker="network_idc_cluster_builder",
        cold_confidence="medium",
        notes="IDC support inherits broader cold-start risk-label/network findings; exact supporting role was cleanup-derived.",
    ),
    ("wave_5", "network_environment_cluster"): CandidateRule(
        cold_aliases=("network_location_pattern",),
        related_user_challenge_id="CH-010",
        related_gap_focused_blocker="network_idc_cluster_builder",
        cold_confidence="medium",
        notes="The combined network environment cluster is a taxonomy-cleanup candidate over cold-start network-location evidence.",
    ),
}


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


def _read_text(path: str | Path) -> str:
    p = Path(path)
    if not p.exists():
        return ""
    return p.read_text(encoding="utf-8")


def _iter_feature_rows(report: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for section in (
        "features",
        "supporting_signals",
        "report_only",
        "data_gap_scanner_gap",
        "candidate_features",
    ):
        value = report.get(section)
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    row = dict(item)
                    row["_section"] = section
                    rows.append(row)
    return rows


def load_cold_start_index(cold_start_dir: str | Path, waves: tuple[str, ...] = ("wave_4", "wave_5")) -> dict[str, dict[str, list[dict[str, Any]]]]:
    root = Path(cold_start_dir)
    index: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for wave_id in waves:
        report_path = root / f"{wave_id}_blind_discovery.json"
        report = _load_json(report_path, default={}) or {}
        feature_index: dict[str, list[dict[str, Any]]] = {}
        for row in _iter_feature_rows(report):
            name = str(row.get("feature_name") or "").strip()
            if not name:
                continue
            enriched = dict(row)
            enriched["_report_file"] = str(report_path)
            enriched["_run_dir"] = str(root)
            feature_index.setdefault(name, []).append(enriched)
        index[wave_id] = feature_index
    return index


def find_cold_evidence(
    *,
    wave_id: str,
    candidate_name: str,
    cold_index: dict[str, dict[str, list[dict[str, Any]]]],
    rule_map: dict[tuple[str, str], CandidateRule] | None = None,
) -> dict[str, Any] | None:
    rule = (rule_map or CANDIDATE_RULES).get((wave_id, candidate_name), CandidateRule())
    feature_index = cold_index.get(wave_id, {})
    for alias in rule.cold_aliases:
        rows = feature_index.get(alias)
        if rows:
            row = rows[0]
            return {
                "feature_name": alias,
                "risk_semantic_type": row.get("risk_semantic_type"),
                "hit_count": row.get("hit_count"),
                "hit_rate": row.get("hit_rate"),
                "section": row.get("_section"),
                "evidence_path": row.get("evidence_path", []),
                "risk_reason": row.get("risk_reason"),
                "report_file": row.get("_report_file"),
                "run_dir": row.get("_run_dir"),
            }
    return None


def build_taxonomy_map_from_sanity(
    sanity_payload: dict[str, Any],
    candidates: list[dict[str, Any]],
) -> dict[tuple[str, str], TaxonomyInfo]:
    rows: list[tuple[str, list[str], str, str]] = []
    for row in sanity_payload.get("candidates_renamed", []) or []:
        rows.append((
            str(row.get("old_candidate_name") or ""),
            [str(x) for x in row.get("new_candidate_names", [])],
            "renamed",
            str(row.get("reason") or ""),
        ))
    for row in sanity_payload.get("candidates_split", []) or []:
        rows.append((
            str(row.get("old_candidate_name") or ""),
            [str(x) for x in row.get("new_candidate_names", [])],
            "split",
            str(row.get("reason") or ""),
        ))

    out: dict[tuple[str, str], TaxonomyInfo] = {}
    wave_by_name: dict[str, set[str]] = {}
    for candidate in candidates:
        wave_by_name.setdefault(str(candidate.get("candidate_name")), set()).add(str(candidate.get("wave_id")))

    for old_name, new_names, action, reason in rows:
        for new_name in new_names:
            for wave_id in wave_by_name.get(new_name, set()):
                parent_id = f"{wave_id}:{old_name}"
                if old_name == new_name:
                    parent_id = f"{wave_id}:{old_name}:pre_cleanup"
                out[(wave_id, new_name)] = TaxonomyInfo(
                    parent_candidate_id=parent_id,
                    parent_candidate_name=old_name,
                    split_from=old_name if action == "split" else "",
                    renamed_from=old_name if action == "renamed" else "",
                    reason=reason,
                )
    return out


def _sanity_by_candidate(sanity_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(item.get("candidate_id")): item
        for item in sanity_payload.get("candidates", []) or []
        if item.get("candidate_id")
    }


def _challenge_present(challenge_id: str, registry_text: str, audit_text: str) -> bool:
    if not challenge_id:
        return False
    needle = f"| {challenge_id} |"
    return needle in registry_text or needle in audit_text or challenge_id in registry_text or challenge_id in audit_text


def _candidate_id(wave_id: str, candidate_name: str) -> str:
    return f"{wave_id}:{candidate_name}"


def _valid_source(source: str | None) -> str:
    if source in SOURCE_ENUM:
        return str(source)
    return "unknown"


def classify_candidate_provenance(
    candidate: dict[str, Any],
    *,
    cold_index: dict[str, dict[str, list[dict[str, Any]]]],
    sanity_by_candidate: dict[str, dict[str, Any]] | None = None,
    taxonomy_map: dict[tuple[str, str], TaxonomyInfo] | None = None,
    registry_text: str = "",
    audit_text: str = "",
    rule_map: dict[tuple[str, str], CandidateRule] | None = None,
    replay_file: str = "",
    sanity_file: str = "",
    challenge_registry_file: str = "",
    challenge_audit_file: str = "",
) -> dict[str, Any]:
    wave_id = str(candidate.get("wave_id") or "")
    candidate_name = str(candidate.get("candidate_name") or "")
    candidate_id = str(candidate.get("candidate_id") or _candidate_id(wave_id, candidate_name))
    rules = rule_map or CANDIDATE_RULES
    rule = rules.get((wave_id, candidate_name), CandidateRule())
    taxonomy_info = (taxonomy_map or {}).get((wave_id, candidate_name))
    cold_evidence = find_cold_evidence(
        wave_id=wave_id,
        candidate_name=candidate_name,
        cold_index=cold_index,
        rule_map=rules,
    )
    challenge_seen = _challenge_present(rule.related_user_challenge_id, registry_text, audit_text)

    if rule.original_discovery_source:
        original_source = rule.original_discovery_source
    elif cold_evidence:
        original_source = "cold_start_autonomous"
    elif rule.current_candidate_source:
        original_source = rule.current_candidate_source
    else:
        original_source = "unknown"

    if taxonomy_info:
        current_source = "taxonomy_cleanup_derived"
    elif rule.current_candidate_source:
        current_source = rule.current_candidate_source
    elif cold_evidence:
        current_source = "cold_start_autonomous"
    else:
        current_source = "unknown"

    original_source = _valid_source(original_source)
    current_source = _valid_source(current_source)

    if current_source in {"gap_focused_targeted", "user_challenge_regression", "taxonomy_cleanup_derived", "manual_review"}:
        was_user_prompted: bool | str = True
    elif current_source == "cold_start_autonomous":
        was_user_prompted = False
    else:
        was_user_prompted = "unknown"

    confidence = "low"
    if cold_evidence or challenge_seen or taxonomy_info or rule.current_candidate_source:
        confidence = rule.cold_confidence if cold_evidence and rule.cold_confidence in {"high", "medium", "low"} else "high"
    if current_source == "unknown" or original_source == "unknown":
        confidence = "low"

    can_count_as_autonomous = (
        original_source == "cold_start_autonomous"
        and current_source == "cold_start_autonomous"
        and was_user_prompted is False
        and bool(cold_evidence)
        and confidence == "high"
    )

    evidence_of_source: dict[str, Any] = {
        "replay_file": replay_file,
        "rule_sanity_file": sanity_file,
    }
    if cold_evidence:
        evidence_of_source.update({
            "run_dir": cold_evidence.get("run_dir"),
            "report_file": cold_evidence.get("report_file"),
            "prompt_tag": "cold_start_blind_discovery",
            "cold_feature_name": cold_evidence.get("feature_name"),
            "cold_feature_section": cold_evidence.get("section"),
            "cold_hit_count": cold_evidence.get("hit_count"),
            "cold_evidence_path": cold_evidence.get("evidence_path"),
        })
    if rule.related_user_challenge_id:
        evidence_of_source.update({
            "challenge_id": rule.related_user_challenge_id,
            "review_file": challenge_registry_file,
            "coverage_audit_file": challenge_audit_file,
        })
    if taxonomy_info:
        evidence_of_source["taxonomy_cleanup_file"] = sanity_file
        evidence_of_source["taxonomy_cleanup_reason"] = taxonomy_info.reason
        evidence_of_source["prompt_tag"] = evidence_of_source.get("prompt_tag") or "p0_5b_taxonomy_cleanup"

    sanity = (sanity_by_candidate or {}).get(candidate_id, {})
    why_or_why_not = "Counts as autonomous because the current candidate exactly comes from cold-start discovery evidence with no targeted or taxonomy-cleanup derivation."
    if not can_count_as_autonomous:
        if current_source == "taxonomy_cleanup_derived":
            why_or_why_not = "Does not count as autonomous discovery because the current candidate was split or renamed during P0-5b taxonomy cleanup; only the parent/original signal can inherit cold-start evidence."
        elif current_source in {"gap_focused_targeted", "user_challenge_regression", "manual_review"}:
            why_or_why_not = "Does not count as autonomous discovery because the current candidate was introduced or tightened by targeted review/user challenge."
        elif current_source == "unknown":
            why_or_why_not = "Does not count as autonomous discovery because no cold-start or targeted provenance evidence was found."
        else:
            why_or_why_not = "Does not count as autonomous discovery because replayability alone is not discovery provenance."

    return {
        "candidate_id": candidate_id,
        "candidate_name": candidate_name,
        "wave_id": wave_id,
        "parent_candidate_id": taxonomy_info.parent_candidate_id if taxonomy_info else "",
        "parent_candidate_name": taxonomy_info.parent_candidate_name if taxonomy_info else "",
        "split_from": taxonomy_info.split_from if taxonomy_info else "",
        "renamed_from": taxonomy_info.renamed_from if taxonomy_info else "",
        "original_discovery_source": original_source,
        "current_candidate_source": current_source,
        "provenance_confidence": confidence,
        "evidence_of_source": evidence_of_source,
        "was_user_prompted": was_user_prompted,
        "related_user_challenge_id": rule.related_user_challenge_id,
        "related_gap_focused_blocker": rule.related_gap_focused_blocker,
        "replay_status": candidate.get("replay_status"),
        "rule_semantics_status": sanity.get("rule_semantics_status", candidate.get("rule_semantics_status", "unknown")),
        "candidate_level": candidate.get("candidate_level"),
        "can_count_as_autonomous_discovery": can_count_as_autonomous,
        "why_or_why_not_autonomous": why_or_why_not,
        "notes": rule.notes,
    }


def build_candidate_discovery_provenance_payload(
    *,
    replay_payload: dict[str, Any],
    sanity_payload: dict[str, Any],
    cold_index: dict[str, dict[str, list[dict[str, Any]]]],
    registry_text: str,
    audit_text: str,
    replay_file: str = "",
    sanity_file: str = "",
    challenge_registry_file: str = "",
    challenge_audit_file: str = "",
    rule_map: dict[tuple[str, str], CandidateRule] | None = None,
    taxonomy_map: dict[tuple[str, str], TaxonomyInfo] | None = None,
) -> dict[str, Any]:
    candidates = list(replay_payload.get("candidates") or [])
    taxonomy = taxonomy_map or build_taxonomy_map_from_sanity(sanity_payload, candidates)
    sanity_by_id = _sanity_by_candidate(sanity_payload)
    provenance = [
        classify_candidate_provenance(
            candidate,
            cold_index=cold_index,
            sanity_by_candidate=sanity_by_id,
            taxonomy_map=taxonomy,
            registry_text=registry_text,
            audit_text=audit_text,
            rule_map=rule_map,
            replay_file=replay_file,
            sanity_file=sanity_file,
            challenge_registry_file=challenge_registry_file,
            challenge_audit_file=challenge_audit_file,
        )
        for candidate in candidates
    ]
    current_counts = Counter(item["current_candidate_source"] for item in provenance)
    original_counts = Counter(item["original_discovery_source"] for item in provenance)
    autonomy_true = [item["candidate_name"] for item in provenance if item["can_count_as_autonomous_discovery"]]
    summary = {
        "schema_version": SCHEMA_VERSION,
        "candidate_count": len(provenance),
        "current_candidate_source_counts": dict(sorted(current_counts.items())),
        "original_discovery_source_counts": dict(sorted(original_counts.items())),
        "autonomous_count": len(autonomy_true),
        "targeted_count": current_counts.get("gap_focused_targeted", 0) + current_counts.get("user_challenge_regression", 0),
        "taxonomy_cleanup_derived_count": current_counts.get("taxonomy_cleanup_derived", 0),
        "unknown_count": current_counts.get("unknown", 0),
        "can_count_as_autonomous_discovery_candidates": autonomy_true,
        "p0_6_discovery_provenance_pass": current_counts.get("unknown", 0) == 0 and all(item["rule_semantics_status"] == "pass" for item in provenance),
        "can_claim_full_autonomous": False,
        "full_autonomous_not_proven": True,
        "remaining_gap": [
            "Taxonomy-cleanup-derived candidates are not counted as autonomous even when their parent signal has cold-start evidence.",
            "Replay pass proves support/miss recomputation, not discovery origin or strategy validation.",
            "No baseline, L6/Hive replay, or population false-positive validation is run.",
            "Strict device_id join is still out of scope; low_bootcount_with_track_high_duration remains partial_lineage from P0-5b.",
            "P0-6 labels provenance only; it does not prove full autonomous discovery.",
        ],
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "input_materials": {
            "candidate_replay_provenance": replay_file,
            "candidate_replay_rule_sanity": sanity_file,
            "challenge_registry": challenge_registry_file,
            "challenge_regression_coverage_audit": challenge_audit_file,
            "cold_start_index": sorted({
                evidence.get("evidence_of_source", {}).get("report_file")
                for evidence in provenance
                if evidence.get("evidence_of_source", {}).get("report_file")
            }),
            "not_used_as_support": [
                "platform",
                "Hive/DataAgent",
                "baseline",
                "L6 replay",
                "new candidate discovery",
                "strict device_id join",
            ],
        },
        "full_autonomous_not_proven": True,
        "candidates": provenance,
        "summary": summary,
    }


def _write_markdown(path: str | Path, payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# P0-6 Candidate Discovery Provenance",
        "",
        f"- schema_version: `{payload['schema_version']}`",
        "- execution_boundary: local provenance labeling only; no platform, Hive/DataAgent, baseline, L6 replay, strict device_id join, or new discovery.",
        f"- full_autonomous_not_proven: `{str(payload['full_autonomous_not_proven']).lower()}`",
        "",
        "## Summary",
        "",
        "|metric|value|",
        "|---|---:|",
        f"|candidate_count|{summary['candidate_count']}|",
        f"|autonomous_count|{summary['autonomous_count']}|",
        f"|targeted_count|{summary['targeted_count']}|",
        f"|taxonomy_cleanup_derived_count|{summary['taxonomy_cleanup_derived_count']}|",
        f"|unknown_count|{summary['unknown_count']}|",
        f"|p0_6_discovery_provenance_pass|{str(summary['p0_6_discovery_provenance_pass']).lower()}|",
        f"|can_claim_full_autonomous|{str(summary['can_claim_full_autonomous']).lower()}|",
        "",
        "## Candidates",
        "",
        "|wave|candidate|original_source|current_source|parent|prompted|can_count_autonomous|confidence|replay|rule|",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for item in payload["candidates"]:
        parent = item.get("parent_candidate_name") or ""
        lines.append(
            f"|{item['wave_id']}|{item['candidate_name']}|{item['original_discovery_source']}|"
            f"{item['current_candidate_source']}|{parent}|{item['was_user_prompted']}|"
            f"{str(item['can_count_as_autonomous_discovery']).lower()}|"
            f"{item['provenance_confidence']}|{item['replay_status']}|{item['rule_semantics_status']}|"
        )
    lines.extend(["", "## Autonomous Count Candidates", ""])
    if summary["can_count_as_autonomous_discovery_candidates"]:
        for name in summary["can_count_as_autonomous_discovery_candidates"]:
            lines.append(f"- {name}")
    else:
        lines.append("- None. Current P0-5b candidates are targeted, taxonomy-cleanup-derived, or otherwise not independently countable as autonomous current candidates.")
    lines.extend(["", "## Per-Candidate Notes", ""])
    for item in payload["candidates"]:
        evidence = item.get("evidence_of_source", {})
        source_bits = []
        for key in ("cold_feature_name", "challenge_id", "taxonomy_cleanup_file"):
            if evidence.get(key):
                source_bits.append(f"{key}={evidence[key]}")
        lines.extend([
            f"### {item['candidate_name']}",
            "",
            f"- why_or_why_not_autonomous: {item['why_or_why_not_autonomous']}",
            f"- related_user_challenge_id: `{item['related_user_challenge_id']}`",
            f"- related_gap_focused_blocker: `{item['related_gap_focused_blocker']}`",
            f"- evidence_of_source: {', '.join(source_bits) if source_bits else 'unknown'}",
            f"- notes: {item['notes']}",
            "",
        ])
    lines.extend(["## Remaining Gap", ""])
    for gap in summary["remaining_gap"]:
        lines.append(f"- {gap}")
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_candidate_discovery_provenance_outputs(
    *,
    replay_file: str | Path = "/private/tmp/dennis_p1_1_p0_foundation_closure/p0_5_candidate_replay/candidate_replay_provenance.json",
    sanity_file: str | Path = "/private/tmp/dennis_p1_1_p0_foundation_closure/p0_5_candidate_replay/candidate_replay_rule_sanity.json",
    cold_start_dir: str | Path = "/private/tmp/dennis_p1_1_cold_start_discovery",
    challenge_registry_file: str | Path = "challenge_registry.md",
    challenge_audit_file: str | Path = "challenge_regression_coverage_audit.md",
    output_dir: str | Path = "/private/tmp/dennis_p1_1_p0_foundation_closure/p0_6_discovery_provenance",
) -> dict[str, Any]:
    replay_path = Path(replay_file)
    sanity_path = Path(sanity_file)
    registry_path = Path(challenge_registry_file)
    audit_path = Path(challenge_audit_file)
    replay_payload = _load_json(replay_path, default={}) or {}
    sanity_payload = _load_json(sanity_path, default={}) or {}
    cold_index = load_cold_start_index(cold_start_dir)
    payload = build_candidate_discovery_provenance_payload(
        replay_payload=replay_payload,
        sanity_payload=sanity_payload,
        cold_index=cold_index,
        registry_text=_read_text(registry_path),
        audit_text=_read_text(audit_path),
        replay_file=str(replay_path),
        sanity_file=str(sanity_path),
        challenge_registry_file=str(registry_path),
        challenge_audit_file=str(audit_path),
    )
    out = Path(output_dir)
    _write_json(out / "candidate_discovery_provenance.json", payload)
    _write_json(out / "p0_6_discovery_provenance_summary.json", payload["summary"])
    _write_markdown(out / "candidate_discovery_provenance.md", payload)
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build P0-6 candidate discovery provenance labels.")
    parser.add_argument("--replay-file", default="/private/tmp/dennis_p1_1_p0_foundation_closure/p0_5_candidate_replay/candidate_replay_provenance.json")
    parser.add_argument("--sanity-file", default="/private/tmp/dennis_p1_1_p0_foundation_closure/p0_5_candidate_replay/candidate_replay_rule_sanity.json")
    parser.add_argument("--cold-start-dir", default="/private/tmp/dennis_p1_1_cold_start_discovery")
    parser.add_argument("--challenge-registry-file", default="challenge_registry.md")
    parser.add_argument("--challenge-audit-file", default="challenge_regression_coverage_audit.md")
    parser.add_argument("--output-dir", default="/private/tmp/dennis_p1_1_p0_foundation_closure/p0_6_discovery_provenance")
    args = parser.parse_args(argv)
    payload = build_candidate_discovery_provenance_outputs(
        replay_file=args.replay_file,
        sanity_file=args.sanity_file,
        cold_start_dir=args.cold_start_dir,
        challenge_registry_file=args.challenge_registry_file,
        challenge_audit_file=args.challenge_audit_file,
        output_dir=args.output_dir,
    )
    print(json.dumps(payload["summary"], ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
