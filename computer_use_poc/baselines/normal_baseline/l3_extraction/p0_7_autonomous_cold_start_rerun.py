#!/usr/bin/env python3
"""P0-7 autonomous cold-start rerun with P0 foundation instrumentation.

The discovery stage reads only P0 foundation fact artifacts:
full_action_inventory_raw_diff, parsed_field_inventory,
container_parser_coverage_matrix, and schema_noise_guard_report.

It intentionally does not read challenge registry, gap-focused outputs, or the
P0-5b cleaned candidate set before candidate proposals are produced. The
cleaned set is read only in the final blind-match evaluation stage.
"""

from __future__ import annotations

import argparse
import ipaddress
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from candidate_replay_provenance import (
    ReplayContext,
    build_context_from_smoke_dir,
    matching_guards_for_evidence,
    normalize_path,
)


SCHEMA_VERSION = "p0_7_autonomous_cold_start_rerun_v1"
RULE_VERSION = "p0_7_autonomous_fact_operators_v1"

ALLOWED_DISCOVERY_ARTIFACTS = [
    "full_action_inventory_raw_diff.json",
    "parsed_field_inventory.json",
    "container_parser_coverage_matrix.json",
    "schema_noise_guard_report.json",
]

FORBIDDEN_DISCOVERY_INPUTS = [
    "challenge_registry.md",
    "challenge_regression_coverage_audit.md",
    "gap-focused review prompt/output",
    "P0-5b cleaned candidate taxonomy as discovery input",
    "user-prompted field checklist",
]


@dataclass
class AutonomousProposal:
    candidate_id: str
    candidate_name: str
    wave_id: str
    signal_type: str
    involved_sources: list[str]
    involved_events: list[str]
    raw_paths: list[str]
    parsed_paths: list[str]
    normalized_paths: list[str]
    proposed_replay_rule: str
    rule_type: str
    rule_params: dict[str, Any]
    why_not_schema_commonality: str
    candidate_level: str
    confidence: str
    discovery_operator: str
    support_user_count_pre_replay: int
    coverage_user_count_pre_replay: int
    evidence_values: list[str]

    def as_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "candidate_name": self.candidate_name,
            "wave_id": self.wave_id,
            "signal_type": self.signal_type,
            "involved_sources": self.involved_sources,
            "involved_events": self.involved_events,
            "raw_paths": self.raw_paths,
            "parsed_paths": self.parsed_paths,
            "normalized_paths": self.normalized_paths,
            "proposed_replay_rule": self.proposed_replay_rule,
            "rule_type": self.rule_type,
            "rule_params": self.rule_params,
            "why_not_schema_commonality": self.why_not_schema_commonality,
            "candidate_level": self.candidate_level,
            "confidence": self.confidence,
            "discovery_operator": self.discovery_operator,
            "support_user_count_pre_replay": self.support_user_count_pre_replay,
            "coverage_user_count_pre_replay": self.coverage_user_count_pre_replay,
            "evidence_values": self.evidence_values,
        }


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def _as_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value or "").strip()
    if not text or text.startswith("<"):
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _row_path(row: dict[str, Any]) -> str:
    return str(row.get("parsed_path") or row.get("raw_path") or "")


def _row_value(row: dict[str, Any]) -> str:
    return str(row.get("value_preview") or "")


def _row_text(row: dict[str, Any]) -> str:
    return f"{row.get('source_action', '')} {_row_path(row)} {_row_value(row)}".lower()


def _evidence_from_row(row: dict[str, Any]) -> dict[str, Any]:
    raw_path = str(row.get("raw_path") or "")
    parsed_path = str(row.get("parsed_path") or "")
    evidence = {
        "source_action": row.get("source_action"),
        "raw_path": raw_path,
        "parsed_path": parsed_path,
        "normalized_path": str(row.get("normalized_parsed_path") or normalize_path(parsed_path or raw_path)),
        "value_summary": row.get("value_preview"),
    }
    if row.get("field_role"):
        evidence["field_role"] = row.get("field_role")
    return evidence


def _unique_evidence(rows: list[dict[str, Any]], limit: int = 16) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, str]] = set()
    for row in rows:
        ev = _evidence_from_row(row)
        key = (
            str(ev.get("source_action") or ""),
            str(ev.get("raw_path") or ""),
            str(ev.get("parsed_path") or ""),
            str(ev.get("value_summary") or ""),
        )
        if key in seen:
            continue
        seen.add(key)
        out.append(ev)
        if len(out) >= limit:
            break
    return out


def _proposal_from_hits(
    ctx: ReplayContext,
    *,
    name: str,
    signal_type: str,
    involved_sources: list[str],
    involved_events: list[str],
    hit_evidence: dict[str, list[dict[str, Any]]],
    proposed_replay_rule: str,
    rule_type: str,
    rule_params: dict[str, Any],
    why_not_schema_commonality: str,
    candidate_level: str,
    confidence: str,
    discovery_operator: str,
) -> AutonomousProposal:
    evidence_rows = [row for rows in hit_evidence.values() for row in rows]
    snippets = _unique_evidence(evidence_rows)
    parsed_paths = sorted({str(x.get("parsed_path") or "") for x in snippets if x.get("parsed_path")})
    raw_paths = sorted({str(x.get("raw_path") or "") for x in snippets if x.get("raw_path")})
    normalized_paths = sorted({str(x.get("normalized_path") or "") for x in snippets if x.get("normalized_path")})
    values: list[str] = []
    for ev in snippets:
        value = str(ev.get("value_summary") or "")
        if value and value not in values:
            values.append(value)
    coverage = sum(
        1 for user_id in ctx.users
        if any(row.get("source_action") in involved_sources for row in ctx.records_by_user.get(user_id, []))
    )
    return AutonomousProposal(
        candidate_id=f"p0_7:{ctx.wave_id}:{_slug(name)}",
        candidate_name=name,
        wave_id=ctx.wave_id,
        signal_type=signal_type,
        involved_sources=involved_sources,
        involved_events=involved_events,
        raw_paths=raw_paths,
        parsed_paths=parsed_paths,
        normalized_paths=normalized_paths,
        proposed_replay_rule=proposed_replay_rule,
        rule_type=rule_type,
        rule_params=rule_params,
        why_not_schema_commonality=why_not_schema_commonality,
        candidate_level=candidate_level,
        confidence=confidence,
        discovery_operator=discovery_operator,
        support_user_count_pre_replay=len(hit_evidence),
        coverage_user_count_pre_replay=coverage,
        evidence_values=values[:12],
    )


ACCOUNT_SOURCES = ["archives_user_analysis", "login_logs_search"]
ACCOUNT_CATEGORY_PATTERNS = {
    "reset_password": ["/reset/select", "/reset/bytoken/logined"],
    "reset_family": ["/reset/"],
    "mobile_rebind": ["rebind/mobile", "/rebind/verify", "checkverification", "startverification"],
    "bind_new_mobile": ["bind/newmobile", "bindnewmobile", "newmobile"],
    "verify_check": ["verifycheck", "checkverification", "startverification", "antispamcheck"],
    "login_token": ["login/token", "token/infra", "refreshtoken"],
    "profile_mutation": ["/user/set", "/user/modify", "changeoption"],
}


def _account_rows(ctx: ReplayContext, user_id: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in ctx.records_by_user.get(user_id, []):
        if row.get("source_action") not in ACCOUNT_SOURCES:
            continue
        path = _row_path(row).lower()
        if any(key in path for key in ("operateuri", "logcontent.uri", ".uri", "method", "requestparam")):
            rows.append(row)
    return rows


def _account_categories(ctx: ReplayContext, user_id: str) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in _account_rows(ctx, user_id):
        text = _row_text(row)
        for category, patterns in ACCOUNT_CATEGORY_PATTERNS.items():
            if any(pattern in text for pattern in patterns):
                out[category].append(row)
    return out


def discover_account_endpoint_families(ctx: ReplayContext) -> list[AutonomousProposal]:
    if ctx.wave_id != "wave_4":
        return []
    proposals: list[AutonomousProposal] = []
    by_user = {user_id: _account_categories(ctx, user_id) for user_id in ctx.users}
    mutation_categories = {"reset_family", "mobile_rebind", "bind_new_mobile", "verify_check", "login_token", "profile_mutation"}

    broad_hits: dict[str, list[dict[str, Any]]] = {}
    for user_id, categories in by_user.items():
        matched = sorted(set(categories) & mutation_categories)
        if len(matched) >= 2:
            rows: list[dict[str, Any]] = []
            for category in matched:
                rows.extend(categories[category][:2])
            broad_hits[user_id] = rows
    if broad_hits:
        proposals.append(_proposal_from_hits(
            ctx,
            name="autonomous_account_mutation_endpoint_family",
            signal_type="event_chain",
            involved_sources=ACCOUNT_SOURCES,
            involved_events=["account_mutation_event", "login_event", "profile_mutation_event"],
            hit_evidence=broad_hits,
            proposed_replay_rule="URI/operation fields hit when >=2 account/profile mutation endpoint families are visible among reset, rebind, bindNewMobile, verify/check, login token, and profile set/modify",
            rule_type="account_endpoint_family",
            rule_params={"min_categories": 2, "categories": sorted(mutation_categories)},
            why_not_schema_commonality="The proposal depends on repeated business endpoint values in parsed URI/operation fields, not response status, wrapper schema, or fixed field presence.",
            candidate_level="high_value",
            confidence="high",
            discovery_operator="endpoint_family_miner",
        ))

    endpoint_specs = [
        ("autonomous_reset_password_endpoint_family", "reset_password", "URI fields contain reset password endpoints such as reset/select or reset/byToken/logined", "high_value"),
        ("autonomous_mobile_rebind_endpoint_family", "mobile_rebind", "URI fields contain mobile rebind or rebind verification endpoint family", "high_value"),
        ("autonomous_profile_set_modify_endpoint_family", "profile_mutation", "URI/operation fields contain profile set, modify, or changeOption endpoint family", "high_value"),
    ]
    for name, category, rule, level in endpoint_specs:
        hits = {
            user_id: categories[category][:8]
            for user_id, categories in by_user.items()
            if categories.get(category)
        }
        if len(hits) >= max(3, int(len(ctx.users) * 0.5)):
            proposals.append(_proposal_from_hits(
                ctx,
                name=name,
                signal_type="event_chain",
                involved_sources=ACCOUNT_SOURCES,
                involved_events=["account_mutation_event", "login_event"],
                hit_evidence=hits,
                proposed_replay_rule=rule,
                rule_type="account_category_any_of",
                rule_params={"category": category},
                why_not_schema_commonality="The proposal uses non-fixed endpoint values and mutation verbs; it is not triggered by the mere presence of URI fields.",
                candidate_level=level,
                confidence="high",
                discovery_operator="endpoint_family_miner",
            ))

    strict_hits: dict[str, list[dict[str, Any]]] = {}
    for user_id, categories in by_user.items():
        if categories.get("reset_family") and categories.get("mobile_rebind"):
            strict_hits[user_id] = categories["reset_family"][:4] + categories["mobile_rebind"][:4]
    if len(strict_hits) >= max(3, int(len(ctx.users) * 0.5)):
        proposals.append(_proposal_from_hits(
            ctx,
            name="autonomous_reset_and_mobile_rebind_endpoint_combo",
            signal_type="event_chain",
            involved_sources=ACCOUNT_SOURCES,
            involved_events=["account_mutation_event", "login_event"],
            hit_evidence=strict_hits,
            proposed_replay_rule="strict all-of: reset-family endpoint evidence and mobile rebind endpoint evidence both present for the user",
            rule_type="account_category_all_of",
            rule_params={"categories": ["reset_family", "mobile_rebind"]},
            why_not_schema_commonality="The combo requires two distinct business endpoint families and cannot be satisfied by fixed schema fields.",
            candidate_level="high_value",
            confidence="high",
            discovery_operator="endpoint_family_miner",
        ))
    return proposals


HEADER_GROUPS = {
    "boot_count": ("bootcount",),
    "version": ("version", "weaponversion", "ver"),
    "storage": ("storage", "disk"),
    "brightness": ("brightness",),
    "sim_or_simulator": ("sim", "simcount", "simulator"),
    "lock_state": ("haspassword", "nolockscreen", "lock"),
    "root_or_jailbreak": ("root", "jailbreak"),
    "hook_or_inject": ("hook", "xposed", "frida", "inject"),
    "proxy": ("proxy",),
    "invisible_verify": ("invisibleverify",),
}


def _weapon_header_group(row: dict[str, Any]) -> str | None:
    path = _row_path(row).lower()
    if "weapondecodeheader" not in path:
        return None
    leaf = path.split(".")[-1]
    for group, needles in HEADER_GROUPS.items():
        if any(needle in leaf for needle in needles):
            return group
    return None


def discover_weapon_runtime_template(ctx: ReplayContext) -> list[AutonomousProposal]:
    hits: dict[str, list[dict[str, Any]]] = {}
    for user_id in ctx.users:
        groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in ctx.records_by_user.get(user_id, []):
            if row.get("source_action") != "weapon_inventory":
                continue
            group = _weapon_header_group(row)
            if group:
                groups[group].append(row)
        if len(set(groups) & set(HEADER_GROUPS)) >= 5:
            rows: list[dict[str, Any]] = []
            for group in sorted(set(groups) & set(HEADER_GROUPS)):
                rows.extend(groups[group][:1])
            hits[user_id] = rows
    if len(hits) < max(3, int(len(ctx.users) * 0.6)):
        return []
    return [_proposal_from_hits(
        ctx,
        name="autonomous_weapon_runtime_header_template",
        signal_type="device_toolchain",
        involved_sources=["weapon_inventory"],
        involved_events=["device_environment_event"],
        hit_evidence=hits,
        proposed_replay_rule="weaponDecodeHeader hits when >=5 runtime/capability groups are present across boot count, version, storage, brightness, SIM/simulator, lock, root, hook, proxy, or invisibleVerify",
        rule_type="weapon_header_template",
        rule_params={"min_required_groups": 5, "groups": sorted(HEADER_GROUPS)},
        why_not_schema_commonality="The proposal requires a multi-field runtime/capability template under weaponDecodeHeader, not a single ordinary device model/platform field.",
        candidate_level="high_value",
        confidence="high",
        discovery_operator="runtime_template_miner",
    )]


def _behavior_numbers(ctx: ReplayContext, user_id: str) -> dict[str, tuple[float, list[dict[str, Any]]]]:
    groups = {
        "profile_visit": ("enterprofilecnt180d", "profilevisit"),
        "photo_upload": ("photouploadcnt180d",),
        "comment": ("watchingcommentcnt180d", "commentcnt180d"),
        "collect": ("collectcount", "caiphotocnt180d"),
    }
    values: dict[str, list[tuple[float, dict[str, Any]]]] = defaultdict(list)
    for row in ctx.records_by_user.get(user_id, []):
        path = _row_path(row).lower()
        num = _as_number(row.get("value_preview"))
        if num is None:
            continue
        for group, needles in groups.items():
            if any(needle in path for needle in needles):
                values[group].append((num, row))
    out: dict[str, tuple[float, list[dict[str, Any]]]] = {}
    for group, rows in values.items():
        best = max(rows, key=lambda x: x[0])
        out[group] = (best[0], [best[1]])
    return out


def discover_social_funnel_buckets(ctx: ReplayContext) -> list[AutonomousProposal]:
    user_numbers = {user_id: _behavior_numbers(ctx, user_id) for user_id in ctx.users}
    thresholds = [
        ("autonomous_profile_visit_low_content_present_bucket", 1, "supporting"),
        ("autonomous_profile_visit_low_content_high_bucket", 500, "high_value"),
        ("autonomous_profile_visit_low_content_extreme_bucket", 800, "supporting"),
    ]
    proposals: list[AutonomousProposal] = []
    for name, visit_min, level in thresholds:
        hits: dict[str, list[dict[str, Any]]] = {}
        for user_id, nums in user_numbers.items():
            visit = nums.get("profile_visit")
            if not visit:
                continue
            content_values = [
                nums[group][0]
                for group in ("photo_upload", "comment", "collect")
                if group in nums
            ]
            if not content_values:
                continue
            if visit[0] >= visit_min and max(content_values) <= 1:
                rows = list(visit[1])
                for group in ("photo_upload", "comment", "collect"):
                    if group in nums:
                        rows.extend(nums[group][1])
                hits[user_id] = rows
        min_support = max(3, int(len(ctx.users) * (0.5 if visit_min >= 500 else 0.6)))
        if len(hits) >= min_support:
            proposals.append(_proposal_from_hits(
                ctx,
                name=name,
                signal_type="behavior_bucket",
                involved_sources=["weapon_inventory", "archives_user_profile"],
                involved_events=["social_funnel_behavior_event"],
                hit_evidence=hits,
                proposed_replay_rule=f"profile/social behavior hits when max profile visit counter >= {visit_min} and visible content/interaction production counters stay <= 1",
                rule_type="profile_visit_low_content_bucket",
                rule_params={"visit_min": visit_min, "low_content_max": 1},
                why_not_schema_commonality="The proposal requires a numeric behavior ratio/bucket across visit and production counters; pagination and fixed response fields are not used.",
                candidate_level=level,
                confidence="high" if visit_min >= 500 else "medium",
                discovery_operator="behavior_bucket_miner",
            ))
    return proposals


INTERNAL_PLATFORM_NETWORK_PATH_TOKENS = {
    "clientip",
    "serverip",
    "serverinfo",
}
SDK_CONFIG_PATH_TOKENS = {
    "sdkconfig",
    "kconf",
    "confcontent",
    "sidinstaticcode",
    "featureflag",
    "configkey",
}
SCHEMA_NOISE_PATH_TOKENS = {
    "traceid",
    "requestid",
    "logtags.color",
    "response_mode",
    "body_present",
    "http_status",
}
NETWORK_TRUSTED_ACTIONS = {
    "archives_user_analysis",
    "archives_user_profile",
    "login_logs_search",
    "track_sequence_profile",
    "weapon_device_info",
    "weapon_device_location_info",
    "weapon_inventory",
    "weapon_user_klink_status",
}
NETWORK_LOCATION_PATH_TOKENS = {
    "country_code",
    "countrycode",
    "country",
    "region",
    "province",
    "city",
    "location",
    "lastloginlocation",
    "laststartuplocation",
    "useripdesc",
}
NETWORK_IP_PATH_TOKENS = {
    "sourceip",
    "userip",
    "loginip",
    "ipaddr",
    "ipaddress",
    "useripdesc",
}


def _has_ip_address(text: str) -> bool:
    for candidate in re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", str(text or "")):
        try:
            ipaddress.ip_address(candidate)
            return True
        except ValueError:
            continue
    return False


def _is_internal_network_noise(path_text: str, value_text: str) -> bool:
    lowered = f"{path_text} {value_text}".lower()
    if any(token in path_text for token in INTERNAL_PLATFORM_NETWORK_PATH_TOKENS):
        return True
    return "kwaidc.com" in lowered


def infer_network_field_role(row: dict[str, Any]) -> str:
    """Infer a lightweight semantic role for network miners.

    The role is intentionally conservative: network candidates may consume only
    network_* roles. Config keys, platform internals, fixed response schema, and
    unknown strings are blocked even if their value contains substrings such as
    "idc" or "sid".
    """
    raw_path = str(row.get("raw_path") or "")
    parsed_path = str(row.get("parsed_path") or "")
    normalized = str(row.get("normalized_parsed_path") or normalize_path(parsed_path or raw_path))
    source_action = str(row.get("source_action") or "")
    value = str(row.get("value_preview") or "").strip()
    path_text = f"{raw_path} {parsed_path} {normalized}".lower()
    value_text = value.lower()

    if any(token in path_text for token in SDK_CONFIG_PATH_TOKENS):
        return "sdk_config_key"
    if _is_internal_network_noise(path_text, value_text):
        return "internal_platform_ip"
    if any(token in path_text for token in SCHEMA_NOISE_PATH_TOKENS):
        return "schema_noise"
    if source_action not in NETWORK_TRUSTED_ACTIONS:
        return "unknown"

    if "oneipinfo" in path_text or "ipinfo" in path_text:
        if re.fullmatch(r"as\d{2,}", value_text):
            return "network_asn"
        if path_text.endswith(".asn") or ".asn" in path_text:
            return "network_asn" if re.fullmatch(r"(as)?\d{2,}", value_text) else "unknown"
        if path_text.endswith(".isp") or ".isp" in path_text or "provider" in path_text:
            if value and not any(token in value_text for token in SDK_CONFIG_PATH_TOKENS):
                return "network_isp"
        if "scenes" in path_text and value_text == "idc":
            return "network_idc"

    label_path = "labelinfo" in path_text and ("ipp" in path_text or "ip" in path_text)
    if label_path and ("idc" in value_text or "机房" in value):
        return "network_idc"
    if "oneriskipidc" in path_text or "oneriskipidc" in value_text:
        return "network_idc"

    if any(token in path_text for token in NETWORK_LOCATION_PATH_TOKENS):
        if value and not value.startswith("{") and not any(token in value_text for token in SDK_CONFIG_PATH_TOKENS):
            return "network_location"

    if any(token in path_text for token in NETWORK_IP_PATH_TOKENS):
        if _has_ip_address(value):
            return "network_ip"

    return "unknown"


def _network_row_with_role(row: dict[str, Any]) -> dict[str, Any] | None:
    role = infer_network_field_role(row)
    if not role.startswith("network_"):
        return None
    out = dict(row)
    out["field_role"] = role
    return out


def _network_categories(ctx: ReplayContext, user_id: str) -> dict[str, list[dict[str, Any]]]:
    rows = list(ctx.records_by_user.get(user_id, [])) + list(ctx.raw_records_by_user.get(user_id, []))
    out: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        role_row = _network_row_with_role(row)
        if not role_row:
            continue
        role = str(role_row.get("field_role") or "")
        value = _row_value(role_row).lower()
        raw_value = _row_value(role_row)
        if role == "network_asn" and re.search(r"\bas\d{2,}\b", value):
            out["provider_asn"].append(role_row)
        elif role == "network_isp" and value:
            out["provider_asn"].append(role_row)
        elif role == "network_location" and (value in {"hk", "hong kong"} or "香港" in raw_value):
            out["hk_location"].append(role_row)
        elif role == "network_ip" and ("香港" in raw_value or value.startswith("hk:")):
            out["hk_location"].append(role_row)
        elif role == "network_idc":
            out["idc_network"].append(role_row)
    return out


def discover_network_environment(ctx: ReplayContext) -> list[AutonomousProposal]:
    by_user = {user_id: _network_categories(ctx, user_id) for user_id in ctx.users}
    specs = [
        ("autonomous_network_provider_asn_cluster", "provider_asn", "environment_cluster", "high_value", "provider/ASN evidence repeats across users"),
        ("autonomous_hk_location_supporting_cluster", "hk_location", "environment_cluster", "supporting", "HK country/city/location evidence repeats across users"),
        ("autonomous_idc_network_supporting_cluster", "idc_network", "environment_cluster", "supporting", "IDC risk label or IDC network evidence repeats across users"),
    ]
    proposals: list[AutonomousProposal] = []
    for name, category, signal_type, level, rule in specs:
        hits = {
            user_id: categories[category][:8]
            for user_id, categories in by_user.items()
            if categories.get(category)
        }
        if len(hits) >= max(3, int(len(ctx.users) * 0.6)):
            proposals.append(_proposal_from_hits(
                ctx,
                name=name,
                signal_type=signal_type,
                involved_sources=["weapon_inventory", "weapon_user_klink_status", "track_sequence_profile", "archives_user_profile"],
                involved_events=["device_environment_event", "login_event", "track_device_behavior_event"],
                hit_evidence=hits,
                proposed_replay_rule=rule,
                rule_type="network_category_any_of",
                rule_params={"category": category},
                why_not_schema_commonality="The proposal uses network/location/provider values and excludes platform-internal clientIp, boardPlatform, requestId, traceId, and response wrapper fields.",
                candidate_level=level,
                confidence="high" if category == "provider_asn" else "medium",
                discovery_operator="network_environment_miner",
            ))

    combo_hits: dict[str, list[dict[str, Any]]] = {}
    for user_id, categories in by_user.items():
        if categories.get("provider_asn") and (categories.get("hk_location") or categories.get("idc_network")):
            combo_hits[user_id] = categories["provider_asn"][:4] + categories.get("hk_location", [])[:2] + categories.get("idc_network", [])[:2]
    if len(combo_hits) >= max(3, int(len(ctx.users) * 0.6)):
        proposals.append(_proposal_from_hits(
            ctx,
            name="autonomous_network_environment_combo_cluster",
            signal_type="environment_cluster",
            involved_sources=["weapon_inventory", "weapon_user_klink_status", "track_sequence_profile", "archives_user_profile"],
            involved_events=["device_environment_event", "login_event", "track_device_behavior_event"],
            hit_evidence=combo_hits,
            proposed_replay_rule="provider/ASN evidence plus at least one supporting HK location or IDC network evidence",
            rule_type="network_combo",
            rule_params={"core": "provider_asn", "supporting_any_of": ["hk_location", "idc_network"]},
            why_not_schema_commonality="The combo requires cross-field network evidence, not a single environment field or fixed response schema.",
            candidate_level="high_value",
            confidence="medium",
            discovery_operator="network_environment_miner",
        ))
    return proposals


def discover_low_boot_track_duration(ctx: ReplayContext) -> list[AutonomousProposal]:
    hits: dict[str, list[dict[str, Any]]] = {}
    for user_id in ctx.users:
        boot_rows: list[tuple[float, dict[str, Any]]] = []
        duration_rows: list[tuple[float, dict[str, Any]]] = []
        for row in ctx.records_by_user.get(user_id, []):
            path = _row_path(row).lower()
            num = _as_number(row.get("value_preview"))
            if num is None:
                continue
            if "bootcount" in path:
                boot_rows.append((num, row))
            if row.get("source_action") == "track_sequence_get_use_duration" and path.endswith("rows.duration"):
                duration_rows.append((num, row))
        if not boot_rows or not duration_rows:
            continue
        low_boot = min(boot_rows, key=lambda x: x[0])
        high_duration = max(duration_rows, key=lambda x: x[0])
        if low_boot[0] <= 10 and high_duration[0] >= 1440:
            hits[user_id] = [low_boot[1], high_duration[1]]
    if len(hits) < max(3, int(len(ctx.users) * 0.6)):
        return []
    return [_proposal_from_hits(
        ctx,
        name="autonomous_low_bootcount_track_high_duration_combo",
        signal_type="combo",
        involved_sources=["weapon_inventory", "track_sequence_get_use_duration"],
        involved_events=["device_environment_event", "track_device_behavior_event"],
        hit_evidence=hits,
        proposed_replay_rule="user-level combo hits when any visible Weapon bootCount <= 10 and Track daily duration has a row >= 1440; strict device_id join is not asserted",
        rule_type="low_boot_track_duration",
        rule_params={"bootCount_max": 10, "track_duration_min": 1440, "lineage_status": "partial_lineage"},
        why_not_schema_commonality="The proposal requires a numeric cross-source combo across Weapon and Track; it is not based on field presence or user-level averages alone.",
        candidate_level="supporting",
        confidence="medium",
        discovery_operator="cross_source_numeric_combo_miner",
    )]


def discover_candidates_for_context(ctx: ReplayContext) -> list[AutonomousProposal]:
    proposals: list[AutonomousProposal] = []
    proposals.extend(discover_account_endpoint_families(ctx))
    proposals.extend(discover_weapon_runtime_template(ctx))
    proposals.extend(discover_social_funnel_buckets(ctx))
    proposals.extend(discover_low_boot_track_duration(ctx))
    proposals.extend(discover_network_environment(ctx))
    return proposals


def replay_proposal(ctx: ReplayContext, proposal: AutonomousProposal) -> dict[str, Any]:
    rule_type = proposal.rule_type
    params = proposal.rule_params
    hit_evidence: dict[str, list[dict[str, Any]]] = {}
    miss_reason: dict[str, str] = {}

    if rule_type in {"account_endpoint_family", "account_category_any_of", "account_category_all_of"}:
        for user_id in ctx.users:
            categories = _account_categories(ctx, user_id)
            if rule_type == "account_endpoint_family":
                matched = sorted(set(categories) & set(params["categories"]))
                if len(matched) >= int(params["min_categories"]):
                    rows: list[dict[str, Any]] = []
                    for category in matched:
                        rows.extend(categories[category][:2])
                    hit_evidence[user_id] = rows
                else:
                    miss_reason[user_id] = "threshold_not_met"
            elif rule_type == "account_category_any_of":
                category = str(params["category"])
                if categories.get(category):
                    hit_evidence[user_id] = categories[category][:8]
                else:
                    miss_reason[user_id] = "threshold_not_met"
            else:
                required = [str(x) for x in params["categories"]]
                if all(categories.get(category) for category in required):
                    rows = []
                    for category in required:
                        rows.extend(categories[category][:4])
                    hit_evidence[user_id] = rows
                else:
                    miss_reason[user_id] = "threshold_not_met"

    elif rule_type == "weapon_header_template":
        required_groups = set(params.get("groups") or HEADER_GROUPS)
        min_groups = int(params.get("min_required_groups", 5))
        for user_id in ctx.users:
            groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
            for row in ctx.records_by_user.get(user_id, []):
                group = _weapon_header_group(row)
                if group:
                    groups[group].append(row)
            matched = sorted(set(groups) & required_groups)
            if len(matched) >= min_groups:
                rows = []
                for group in matched:
                    rows.extend(groups[group][:1])
                hit_evidence[user_id] = rows
            else:
                miss_reason[user_id] = "threshold_not_met"

    elif rule_type == "profile_visit_low_content_bucket":
        visit_min = float(params["visit_min"])
        low_content_max = float(params["low_content_max"])
        for user_id in ctx.users:
            nums = _behavior_numbers(ctx, user_id)
            visit = nums.get("profile_visit")
            content_values = [nums[group][0] for group in ("photo_upload", "comment", "collect") if group in nums]
            if visit and content_values and visit[0] >= visit_min and max(content_values) <= low_content_max:
                rows = list(visit[1])
                for group in ("photo_upload", "comment", "collect"):
                    if group in nums:
                        rows.extend(nums[group][1])
                hit_evidence[user_id] = rows
            else:
                miss_reason[user_id] = "threshold_not_met"

    elif rule_type in {"network_category_any_of", "network_combo"}:
        for user_id in ctx.users:
            categories = _network_categories(ctx, user_id)
            if rule_type == "network_category_any_of":
                category = str(params["category"])
                if categories.get(category):
                    hit_evidence[user_id] = categories[category][:8]
                else:
                    miss_reason[user_id] = "field_absent"
            else:
                core = str(params["core"])
                supporting = [str(x) for x in params["supporting_any_of"]]
                support_rows: list[dict[str, Any]] = []
                for category in supporting:
                    support_rows.extend(categories.get(category, [])[:3])
                if categories.get(core) and support_rows:
                    hit_evidence[user_id] = categories[core][:4] + support_rows
                else:
                    miss_reason[user_id] = "field_absent"

    elif rule_type == "low_boot_track_duration":
        for user_id in ctx.users:
            boot_rows: list[tuple[float, dict[str, Any]]] = []
            duration_rows: list[tuple[float, dict[str, Any]]] = []
            for row in ctx.records_by_user.get(user_id, []):
                path = _row_path(row).lower()
                num = _as_number(row.get("value_preview"))
                if num is None:
                    continue
                if "bootcount" in path:
                    boot_rows.append((num, row))
                if row.get("source_action") == "track_sequence_get_use_duration" and path.endswith("rows.duration"):
                    duration_rows.append((num, row))
            if boot_rows and duration_rows:
                low_boot = min(boot_rows, key=lambda x: x[0])
                high_duration = max(duration_rows, key=lambda x: x[0])
                if low_boot[0] <= float(params["bootCount_max"]) and high_duration[0] >= float(params["track_duration_min"]):
                    hit_evidence[user_id] = [low_boot[1], high_duration[1]]
                else:
                    miss_reason[user_id] = "threshold_not_met"
            else:
                miss_reason[user_id] = "field_absent"

    snippets = _unique_evidence([row for rows in hit_evidence.values() for row in rows], limit=20)
    guard_matches = matching_guards_for_evidence(ctx, snippets)
    blocking_guards = [
        guard for guard in guard_matches
        if not bool(guard.get("high_value_allowed")) and not bool(guard.get("combo_allowed"))
    ]
    schema_guard_conflict = bool(blocking_guards)
    report_only_fields = sorted({
        str(guard.get("path") or "")
        for guard in guard_matches
        if str(guard.get("guard_level") or "") == "report_only"
    })
    support = len(hit_evidence)
    coverage = sum(
        1 for user_id in ctx.users
        if any(row.get("source_action") in proposal.involved_sources for row in ctx.records_by_user.get(user_id, []))
        or any(row.get("source_action") in proposal.involved_sources for row in ctx.raw_records_by_user.get(user_id, []))
    )
    lineage_status = "partial_lineage" if rule_type == "low_boot_track_duration" else "user_level"
    if support <= 0 or schema_guard_conflict:
        replay_status = "replay_failed"
    elif lineage_status == "partial_lineage":
        replay_status = "replay_partial"
    else:
        replay_status = "replay_pass"
    return {
        **proposal.as_dict(),
        "rule_version": RULE_VERSION,
        "support_user_count": support,
        "miss_user_count": len(ctx.users) - support,
        "coverage_user_count": coverage,
        "sample_hits": [
            {
                "user_id": user_id,
                "evidence_count": len(rows),
                "value_summary": [str(row.get("value_preview") or "") for row in rows[:6]],
            }
            for user_id, rows in sorted(hit_evidence.items())
        ],
        "sample_misses": [
            {"user_id": user_id, "missing_reason": miss_reason.get(user_id, "field_absent")}
            for user_id in ctx.users
            if user_id not in hit_evidence
        ],
        "missing_reason_by_user": {
            user_id: miss_reason.get(user_id, "field_absent")
            for user_id in ctx.users
            if user_id not in hit_evidence
        },
        "evidence_snippets": snippets,
        "schema_guard_applied": bool(guard_matches),
        "schema_guard_conflict": schema_guard_conflict,
        "report_only_fields_used": report_only_fields,
        "replay_status": replay_status,
        "readiness": "needs_more_source" if lineage_status == "partial_lineage" else "discovery_only",
        "lineage_status": lineage_status,
        "verified_strategy": False,
    }


def build_autonomous_provenance(replay_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for item in replay_items:
        can_count = (
            item.get("replay_status") in {"replay_pass", "replay_partial"}
            and not item.get("schema_guard_conflict")
        )
        out.append({
            "candidate_id": item["candidate_id"],
            "candidate_name": item["candidate_name"],
            "wave_id": item["wave_id"],
            "parent_candidate_id": "",
            "parent_candidate_name": "",
            "split_from": "",
            "renamed_from": "",
            "original_discovery_source": "cold_start_autonomous",
            "current_candidate_source": "cold_start_autonomous",
            "provenance_confidence": item.get("confidence", "medium"),
            "evidence_of_source": {
                "run_dir": "",
                "report_file": "p0_7_autonomous_cold_start_candidates.json",
                "prompt_tag": "p0_7_no_prompt_foundation_fact_discovery",
                "review_file": "",
            },
            "was_user_prompted": False,
            "related_user_challenge_id": "",
            "related_gap_focused_blocker": "",
            "replay_status": item.get("replay_status"),
            "rule_semantics_status": "pass" if item.get("replay_status") != "replay_failed" else "replay_failed",
            "candidate_level": item.get("candidate_level"),
            "can_count_as_autonomous_discovery": can_count,
            "why_or_why_not_autonomous": (
                "Counts as autonomous discovery because the proposal was generated from P0 foundation raw/parsed facts before any cleaned-candidate blind match."
                if can_count
                else "Does not count as autonomous because replay failed or schema guard conflict was detected."
            ),
            "notes": "Discovery-only candidate; not a verified strategy.",
        })
    return out


def _tokenize_match_text(value: Any) -> set[str]:
    text = json.dumps(value, ensure_ascii=False).lower() if not isinstance(value, str) else value.lower()
    tokens = set(re.findall(r"[a-z0-9_]{3,}", text))
    aliases = {
        "provider": {"zenlayer", "asn", "isp"},
        "asn": {"as21859", "zenlayer"},
        "profile": {"enterprofilecnt180d", "profilevisit", "set", "modify"},
        "rebind": {"mobile", "verifycheck", "checkverification"},
        "reset": {"reset_password", "reset_family"},
        "weapon": {"weapondecodeheader", "runtime", "header"},
        "network": {"oneipinfo", "idc", "hk", "zenlayer"},
    }
    expanded = set(tokens)
    for token in list(tokens):
        expanded |= aliases.get(token, set())
    return expanded


def blind_match_against_cleaned(
    replay_items: list[dict[str, Any]],
    cleaned_candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    matches: list[dict[str, Any]] = []
    matched_cleaned: set[str] = set()
    matched_autonomous: set[str] = set()
    for cleaned in cleaned_candidates:
        best: tuple[float, dict[str, Any] | None, dict[str, Any]] = (0.0, None, {})
        cleaned_tokens = _tokenize_match_text({
            "name": cleaned.get("candidate_name"),
            "signal_type": cleaned.get("signal_type"),
            "sources": cleaned.get("involved_sources"),
            "events": cleaned.get("involved_events"),
            "paths": cleaned.get("normalized_paths") or cleaned.get("parsed_paths") or cleaned.get("raw_paths"),
            "rule": cleaned.get("replay_rule"),
            "fields": cleaned.get("fields_used"),
            "thresholds": cleaned.get("field_thresholds"),
        })
        for item in replay_items:
            if item.get("wave_id") != cleaned.get("wave_id"):
                continue
            item_tokens = _tokenize_match_text({
                "name": item.get("candidate_name"),
                "signal_type": item.get("signal_type"),
                "sources": item.get("involved_sources"),
                "events": item.get("involved_events"),
                "paths": item.get("normalized_paths") or item.get("parsed_paths") or item.get("raw_paths"),
                "rule": item.get("proposed_replay_rule"),
                "params": item.get("rule_params"),
            })
            intersection = cleaned_tokens & item_tokens
            union = cleaned_tokens | item_tokens
            jaccard = len(intersection) / max(1, len(union))
            source_overlap = len(set(cleaned.get("involved_sources", [])) & set(item.get("involved_sources", [])))
            signal_bonus = 0.12 if cleaned.get("signal_type") == item.get("signal_type") else 0.0
            source_bonus = min(0.18, source_overlap * 0.06)
            score = jaccard + signal_bonus + source_bonus
            if score > best[0]:
                best = (score, item, {"token_overlap": sorted(intersection)[:20], "jaccard": round(jaccard, 4), "source_overlap": source_overlap})
        if best[1] and best[0] >= 0.18:
            item = best[1]
            cleaned_id = str(cleaned.get("candidate_id") or f"{cleaned.get('wave_id')}:{cleaned.get('candidate_name')}")
            matched_cleaned.add(cleaned_id)
            matched_autonomous.add(str(item["candidate_id"]))
            matches.append({
                "cleaned_candidate_id": cleaned_id,
                "cleaned_candidate_name": cleaned.get("candidate_name"),
                "autonomous_candidate_id": item["candidate_id"],
                "autonomous_candidate_name": item["candidate_name"],
                "match_score": round(best[0], 4),
                "match_reason": best[2],
            })
    cleaned_ids = {
        str(c.get("candidate_id") or f"{c.get('wave_id')}:{c.get('candidate_name')}")
        for c in cleaned_candidates
    }
    all_autonomous_ids = {str(item["candidate_id"]) for item in replay_items}
    missed = sorted(cleaned_ids - matched_cleaned)
    new = sorted(all_autonomous_ids - matched_autonomous)
    return {
        "matches": matches,
        "matched_cleaned_ids": sorted(matched_cleaned),
        "matched_autonomous_ids": sorted(matched_autonomous),
        "missed_cleaned_candidate_ids": missed,
        "new_autonomous_candidate_ids": new,
        "matched_to_cleaned_candidate_count": len(matched_cleaned),
        "missed_cleaned_candidate_count": len(missed),
        "new_candidate_count": len(new),
        "autonomous_recall_against_cleaned_candidates": round(len(matched_cleaned) / max(1, len(cleaned_ids)), 4),
    }


def _write_json(path: str | Path, payload: Any) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_candidates_md(path: str | Path, payload: dict[str, Any]) -> None:
    lines = [
        "# P0-7 Autonomous Cold-Start Candidates",
        "",
        "- discovery_input_boundary: P0 foundation fact artifacts only.",
        "- forbidden_inputs_used: false",
        f"- candidate_count: {len(payload['candidates'])}",
        "",
        "|wave|candidate|signal|level|confidence|pre_support|operator|",
        "|---|---|---|---|---|---:|---|",
    ]
    for c in payload["candidates"]:
        lines.append(f"|{c['wave_id']}|{c['candidate_name']}|{c['signal_type']}|{c['candidate_level']}|{c['confidence']}|{c['support_user_count_pre_replay']}|{c['discovery_operator']}|")
    lines.extend(["", "## Boundary", ""])
    for item in payload["discovery_boundary"]["forbidden_inputs_not_used"]:
        lines.append(f"- not used: {item}")
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_replay_md(path: str | Path, payload: dict[str, Any]) -> None:
    lines = [
        "# P0-7 Autonomous Replay Provenance",
        "",
        "- replay_scope: support/miss/coverage recomputation for P0-7 autonomous proposals.",
        "- verified_strategy: false",
        "",
        "|wave|candidate|support|miss|coverage|status|lineage|can_auto|",
        "|---|---|---:|---:|---:|---|---|---|",
    ]
    provenance_by_id = {p["candidate_id"]: p for p in payload["provenance"]}
    for item in payload["candidates"]:
        prov = provenance_by_id[item["candidate_id"]]
        lines.append(
            f"|{item['wave_id']}|{item['candidate_name']}|{item['support_user_count']}|"
            f"{item['miss_user_count']}|{item['coverage_user_count']}|{item['replay_status']}|"
            f"{item['lineage_status']}|{str(prov['can_count_as_autonomous_discovery']).lower()}|"
        )
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_eval_md(path: str | Path, payload: dict[str, Any]) -> None:
    s = payload["summary"]
    lines = [
        "# P0-7 Autonomous Discovery Eval",
        "",
        f"- targeted_leakage_detected: `{str(s['targeted_leakage_detected']).lower()}`",
        f"- can_claim_full_autonomous: `{str(s['can_claim_full_autonomous']).lower()}`",
        f"- full_autonomous_not_proven: `{str(s['full_autonomous_not_proven']).lower()}`",
        "",
        "|metric|value|",
        "|---|---:|",
    ]
    for key in (
        "autonomous_candidate_count",
        "replay_pass_count",
        "replay_partial_count",
        "replay_failed_count",
        "matched_to_cleaned_candidate_count",
        "new_candidate_count",
        "false_or_noisy_candidate_count",
        "missed_cleaned_candidate_count",
        "autonomous_recall_against_cleaned_candidates",
        "schema_noise_violation_count",
    ):
        lines.append(f"|{key}|{s[key]}|")
    lines.extend(["", "## Blind Matches", ""])
    lines.extend(["|cleaned|autonomous|score|", "|---|---|---:|"])
    for row in payload["blind_match"]["matches"]:
        lines.append(f"|{row['cleaned_candidate_name']}|{row['autonomous_candidate_name']}|{row['match_score']}|")
    lines.extend(["", "## Missed Cleaned Candidates", ""])
    if payload["blind_match"]["missed_cleaned_candidate_ids"]:
        for item in payload["blind_match"]["missed_cleaned_candidate_ids"]:
            lines.append(f"- {item}")
    else:
        lines.append("- None")
    lines.extend(["", "## Remaining Gap", ""])
    for gap in s["remaining_gap"]:
        lines.append(f"- {gap}")
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_p0_7_outputs(
    *,
    base_dir: str | Path = "/private/tmp/dennis_p1_1_p0_foundation_closure",
    cleaned_candidate_file: str | Path = "/private/tmp/dennis_p1_1_p0_foundation_closure/p0_5_candidate_replay/candidate_replay_provenance.json",
    output_dir: str | Path = "/private/tmp/dennis_p1_1_p0_foundation_closure/p0_7_autonomous_cold_start",
    waves: tuple[str, ...] = ("wave_4", "wave_5"),
) -> dict[str, Any]:
    base = Path(base_dir)
    contexts = {
        wave_id: build_context_from_smoke_dir(base / f"{wave_id}_smoke", wave_id)
        for wave_id in waves
    }

    # Stage 1: autonomous discovery. Do not read cleaned candidates here.
    proposals: list[AutonomousProposal] = []
    for wave_id in waves:
        proposals.extend(discover_candidates_for_context(contexts[wave_id]))
    candidate_payload = {
        "schema_version": SCHEMA_VERSION,
        "rule_version": RULE_VERSION,
        "discovery_boundary": {
            "allowed_inputs": ALLOWED_DISCOVERY_ARTIFACTS,
            "forbidden_inputs_not_used": FORBIDDEN_DISCOVERY_INPUTS,
            "challenge_registry_used": False,
            "gap_focused_output_used": False,
            "cleaned_candidate_set_used_for_discovery": False,
        },
        "candidates": [proposal.as_dict() for proposal in proposals],
    }

    # Stage 2: replay autonomous proposals from the same P0 fact tables.
    replay_items = [
        replay_proposal(contexts[proposal.wave_id], proposal)
        for proposal in proposals
    ]
    provenance = build_autonomous_provenance(replay_items)
    replay_payload = {
        "schema_version": SCHEMA_VERSION,
        "rule_version": RULE_VERSION,
        "replay_boundary": {
            "cleaned_candidate_set_used_for_replay": False,
            "verified_strategy": False,
            "baseline_used": False,
            "hive_or_dataagent_used": False,
        },
        "candidates": replay_items,
        "provenance": provenance,
    }

    # Stage 3: blind recall evaluation. Cleaned candidates are read only here.
    cleaned_payload = json.loads(Path(cleaned_candidate_file).read_text(encoding="utf-8"))
    cleaned_candidates = list(cleaned_payload.get("candidates") or [])
    blind_match = blind_match_against_cleaned(replay_items, cleaned_candidates)
    status_counts = Counter(item["replay_status"] for item in replay_items)
    schema_noise_violation_count = sum(1 for item in replay_items if item.get("schema_guard_conflict"))
    false_or_noisy = status_counts.get("replay_failed", 0) + schema_noise_violation_count
    autonomous_count = sum(1 for item in provenance if item["can_count_as_autonomous_discovery"])
    eval_summary = {
        "autonomous_candidate_count": autonomous_count,
        "replay_pass_count": status_counts.get("replay_pass", 0),
        "replay_partial_count": status_counts.get("replay_partial", 0),
        "replay_failed_count": status_counts.get("replay_failed", 0),
        "matched_to_cleaned_candidate_count": blind_match["matched_to_cleaned_candidate_count"],
        "new_candidate_count": blind_match["new_candidate_count"],
        "false_or_noisy_candidate_count": false_or_noisy,
        "missed_cleaned_candidate_count": blind_match["missed_cleaned_candidate_count"],
        "autonomous_recall_against_cleaned_candidates": blind_match["autonomous_recall_against_cleaned_candidates"],
        "schema_noise_violation_count": schema_noise_violation_count,
        "targeted_leakage_detected": False,
        "can_claim_full_autonomous": False,
        "full_autonomous_not_proven": True,
        "remaining_gap": [
            "Replay pass proves candidate support/miss can be recomputed, not verified strategy quality.",
            "No normal baseline, L6/Hive replay, population false-positive validation, or strict device_id join was run.",
            "The blind match is evaluation-only and was not available to the discovery stage.",
            "This run supports autonomous discovery capability on wave4/wave5 facts, but not full autonomous proof.",
        ],
    }
    eval_payload = {
        "schema_version": SCHEMA_VERSION,
        "evaluation_boundary": {
            "cleaned_candidate_set_used_only_after_discovery": True,
            "challenge_registry_used": False,
            "gap_focused_output_used": False,
            "verified_strategy": False,
        },
        "summary": eval_summary,
        "blind_match": blind_match,
    }

    out = Path(output_dir)
    _write_json(out / "p0_7_autonomous_cold_start_candidates.json", candidate_payload)
    _write_candidates_md(out / "p0_7_autonomous_cold_start_candidates.md", candidate_payload)
    _write_json(out / "p0_7_autonomous_replay_provenance.json", replay_payload)
    _write_replay_md(out / "p0_7_autonomous_replay_provenance.md", replay_payload)
    _write_json(out / "p0_7_autonomous_discovery_eval.json", eval_payload)
    _write_eval_md(out / "p0_7_autonomous_discovery_eval.md", eval_payload)
    return {
        "candidates": candidate_payload,
        "replay": replay_payload,
        "eval": eval_payload,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run P0-7 autonomous cold-start rerun from local P0 foundation artifacts.")
    parser.add_argument("--base-dir", default="/private/tmp/dennis_p1_1_p0_foundation_closure")
    parser.add_argument("--cleaned-candidate-file", default="/private/tmp/dennis_p1_1_p0_foundation_closure/p0_5_candidate_replay/candidate_replay_provenance.json")
    parser.add_argument("--output-dir", default="/private/tmp/dennis_p1_1_p0_foundation_closure/p0_7_autonomous_cold_start")
    args = parser.parse_args(argv)
    payload = build_p0_7_outputs(
        base_dir=args.base_dir,
        cleaned_candidate_file=args.cleaned_candidate_file,
        output_dir=args.output_dir,
    )
    print(json.dumps(payload["eval"]["summary"], ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
