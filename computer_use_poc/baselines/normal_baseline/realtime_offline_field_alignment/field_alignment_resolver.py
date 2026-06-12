#!/usr/bin/env python3
"""Realtime/offline field alignment resolver.

This is the single deterministic entrypoint for source alias, field alias,
canonical path, field role, Weapon action, and platform resolution.
Model-assisted alignment is intentionally represented only as reviewable
candidates; this resolver never upgrades semantic-only matches to confirmed.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple

import yaml


_REGISTRY_CACHE: Optional[Dict[str, Any]] = None
_FIELD_INDEX_CACHE: Optional[Dict[Tuple[str, str], Dict[str, Any]]] = None


@dataclass(frozen=True)
class AlignmentResult:
    canonical_source: str
    canonical_field_path: str
    match_type: str
    field_role: str
    confidence: str
    unresolved_reason: Optional[str]
    need_human_review: bool
    notes: str
    cardinality_hint: Optional[str] = None
    can_use_for_l4_baseline: Optional[bool] = None
    field_family: Optional[str] = None
    weapon_action: str = "unknown"
    platform: str = "unknown"

    def as_dict(self) -> Dict[str, Any]:
        return {
            "canonical_source": self.canonical_source,
            "canonical_field_path": self.canonical_field_path,
            "match_type": self.match_type,
            "field_role": self.field_role,
            "confidence": self.confidence,
            "unresolved_reason": self.unresolved_reason,
            "need_human_review": self.need_human_review,
            "notes": self.notes,
            "cardinality_hint": self.cardinality_hint,
            "can_use_for_l4_baseline": self.can_use_for_l4_baseline,
            "field_family": self.field_family,
            "weapon_action": self.weapon_action,
            "platform": self.platform,
        }


def _registry_path() -> str:
    return os.path.join(os.path.dirname(__file__), "field_alignment_registry.yaml")


def load_registry() -> Dict[str, Any]:
    global _REGISTRY_CACHE
    if _REGISTRY_CACHE is None:
        with open(_registry_path(), "r", encoding="utf-8") as f:
            _REGISTRY_CACHE = yaml.safe_load(f) or {}
    return _REGISTRY_CACHE


def clear_registry_cache() -> None:
    global _REGISTRY_CACHE, _FIELD_INDEX_CACHE
    _REGISTRY_CACHE = None
    _FIELD_INDEX_CACHE = None


def _leaf(path: str) -> str:
    return str(path or "").split(".")[-1]


def _source_from_path(path: str) -> str:
    parts = str(path or "").split(".")
    return parts[0] if len(parts) > 1 else ""


def _field_index() -> Dict[Tuple[str, str], Dict[str, Any]]:
    global _FIELD_INDEX_CACHE
    if _FIELD_INDEX_CACHE is not None:
        return _FIELD_INDEX_CACHE
    registry = load_registry()
    idx: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for rec in registry.get("alignment_records", []):
        sources = {rec.get("realtime_source"), rec.get("canonical_source"), rec.get("offline_source")}
        fields = {
            rec.get("realtime_field_path"),
            rec.get("offline_field_path"),
            rec.get("canonical_field_path"),
            rec.get("realtime_leaf_key"),
            rec.get("offline_leaf_key"),
        }
        for source in filter(None, sources):
            for field in filter(None, fields):
                idx[(str(source), str(field))] = rec
    for source, aliases in (registry.get("additional_field_aliases") or {}).items():
        for alias, canonical in aliases.items():
            meta = dict((registry.get("path_metadata") or {}).get(canonical, {}))
            key = (str(source), str(alias))
            if key in idx:
                continue
            idx[key] = {
                "realtime_source": source,
                "realtime_field_path": alias,
                "realtime_leaf_key": _leaf(alias),
                "offline_source": _source_from_path(canonical),
                "offline_field_path": canonical,
                "offline_leaf_key": _leaf(canonical),
                "canonical_source": _source_from_path(canonical) or source,
                "canonical_field_path": canonical,
                "field_family": meta.get("field_family", "unknown"),
                "field_role": meta.get("field_role", "unknown_need_review"),
                "cardinality_hint": meta.get("cardinality_hint"),
                "can_use_for_l4_baseline": meta.get("can_use_for_l4_baseline"),
                "match_type": "source_alias_field_match" if source.startswith("login_logs") else "seed_mapping_match",
                "confidence": "high",
                "unresolved_reason": meta.get("unresolved_reason"),
                "need_human_review": bool(meta.get("unresolved_reason")),
                "weapon_action": meta.get("weapon_action", _infer_weapon_action(canonical)),
                "platform": meta.get("platform", _infer_platform(source, canonical)),
                "notes": meta.get("notes", "additional registry alias"),
            }
    _FIELD_INDEX_CACHE = idx
    return idx


def resolve_source(source_name: str) -> Dict[str, Any]:
    registry = load_registry()
    source_name = str(source_name or "")
    entry = (registry.get("source_aliases") or {}).get(source_name)
    if entry:
        return {
            "canonical_source": entry.get("canonical_source", source_name),
            "match_type": entry.get("match_type", "exact_path_match"),
            "confidence": entry.get("confidence", "high"),
            "unresolved_reason": None,
            "need_human_review": False,
            "notes": entry.get("notes", ""),
        }
    return {
        "canonical_source": source_name,
        "match_type": "unresolved" if source_name else "no_match",
        "confidence": "low",
        "unresolved_reason": "unknown_source" if source_name else "missing_source",
        "need_human_review": True,
        "notes": "source not found in registry; passthrough only",
    }


def _lookup_metadata(canonical_field_path: str) -> Dict[str, Any]:
    return dict((load_registry().get("path_metadata") or {}).get(canonical_field_path, {}))


def _infer_platform(source: str, path: str = "") -> str:
    text = f"{source}.{path}".lower()
    if "weapon_android" in text:
        return "android"
    if "weapon_ios" in text:
        return "ios"
    return "unknown"


def _infer_weapon_action(path: str) -> str:
    lower = str(path or "").lower()
    if ".raw_data.weaponrisk." in lower or lower.endswith(".raw_data.weaponrisk"):
        return "oneRisk"
    if ".onerisk." in lower or "onerisk" in _leaf(path):
        return "oneRisk"
    if ".raw_data." in lower:
        return "raw_data"
    return "unknown"


def _role_from_rules(canonical_source: str, canonical_field_path: str) -> Dict[str, Any]:
    registry = load_registry()
    rules = registry.get("role_rules", {})
    last = _leaf(canonical_field_path)
    lower_path = canonical_field_path.lower()

    result_rules = rules.get("result_signal", {})
    if last in set(result_rules.get("exact_last_parts", [])):
        return {"field_role": "result_signal", "confidence": "high", "notes": "registry result_signal last-part"}
    for ambiguous, cfg in (result_rules.get("source_aware_last_parts") or {}).items():
        if last == ambiguous and any(p.lower() in lower_path for p in cfg.get("allowed_prefixes", [])):
            return {"field_role": "result_signal", "confidence": "high", "notes": "registry source-aware result signal"}

    one_risk_labels = set(rules.get("one_risk_factual_labels", []))
    if ".weaponrisk." in lower_path or "onerisk" in last:
        if last in one_risk_labels:
            return {"field_role": "factual_device_label", "confidence": "high", "notes": "registry oneRisk factual label"}
        return {"field_role": "unknown_need_review", "confidence": "low", "notes": "unknown oneRisk/weaponRisk label requires review"}

    id_rules = rules.get("identifier_anchor", {})
    if last in set(id_rules.get("exact_last_parts", [])):
        cardinality = "high" if last in {"did", "device_id", "deviceId", "xm1", "xm3", "uuid", "guid"} else None
        return {
            "field_role": "identifier_anchor",
            "confidence": "high",
            "notes": "registry identifier last-part",
            "cardinality_hint": cardinality,
        }
    if any(sub in last for sub in id_rules.get("substrings", [])):
        return {"field_role": "identifier_anchor", "confidence": "medium", "notes": "registry identifier substring"}

    if canonical_source == "infra_user_action_log" and last in {"action_type", "login_type", "reason", "uri"}:
        return {"field_role": "behavior_fact", "confidence": "high", "notes": "login log behavior field"}
    if any(tok in lower_path for tok in ["cpu", "sensor", "asn", "district", "scene", "xiaomi", "qualcomm", "arch", "model", "kernel", "utc", "time", "rom"]):
        return {"field_role": "factual_environment_label", "confidence": "medium", "notes": "device/environment path heuristic"}
    if any(tok in lower_path for tok in ["nosim", "root", "emulator", "factoryreset", "accessibility", "charging"]):
        return {"field_role": "factual_device_label", "confidence": "medium", "notes": "device state path heuristic"}
    return {"field_role": "unknown_need_review", "confidence": "low", "notes": "no registry role rule matched"}


def classify_field_role(canonical_source: str, canonical_field_path: str) -> Dict[str, Any]:
    meta = _lookup_metadata(canonical_field_path)
    if meta.get("field_role"):
        return {
            "field_role": meta.get("field_role"),
            "confidence": "high",
            "need_human_review": bool(meta.get("unresolved_reason")),
            "notes": meta.get("notes", "registry explicit path metadata"),
            "weapon_action": meta.get("weapon_action", _infer_weapon_action(canonical_field_path)),
            "platform": meta.get("platform", _infer_platform(canonical_source, canonical_field_path)),
            "field_family": meta.get("field_family"),
            "cardinality_hint": meta.get("cardinality_hint"),
            "can_use_for_l4_baseline": meta.get("can_use_for_l4_baseline"),
            "unresolved_reason": meta.get("unresolved_reason"),
        }
    role = _role_from_rules(canonical_source, canonical_field_path)
    role.update({
        "need_human_review": role["field_role"] == "unknown_need_review",
        "weapon_action": _infer_weapon_action(canonical_field_path),
        "platform": _infer_platform(canonical_source, canonical_field_path),
        "field_family": None,
        "cardinality_hint": role.get("cardinality_hint"),
        "can_use_for_l4_baseline": None,
    })
    return role


def _result_from_record(source: str, field: str, rec: Dict[str, Any]) -> AlignmentResult:
    role_info = classify_field_role(str(rec.get("canonical_source") or ""), str(rec.get("canonical_field_path") or ""))
    unresolved = rec.get("unresolved_reason")
    return AlignmentResult(
        canonical_source=str(rec.get("canonical_source") or rec.get("offline_source") or source),
        canonical_field_path=str(rec.get("canonical_field_path") or rec.get("offline_field_path") or field),
        match_type=str(rec.get("match_type") or "seed_mapping_match"),
        field_role=str(rec.get("field_role") or role_info["field_role"]),
        confidence=str(rec.get("confidence") or role_info.get("confidence") or "medium"),
        unresolved_reason=str(unresolved) if unresolved else None,
        need_human_review=bool(rec.get("need_human_review") or unresolved),
        notes=str(rec.get("notes") or role_info.get("notes") or ""),
        cardinality_hint=rec.get("cardinality_hint") or role_info.get("cardinality_hint"),
        can_use_for_l4_baseline=rec.get("can_use_for_l4_baseline")
        if rec.get("can_use_for_l4_baseline") is not None else role_info.get("can_use_for_l4_baseline"),
        field_family=rec.get("field_family") or role_info.get("field_family"),
        weapon_action=str(rec.get("weapon_action") or role_info.get("weapon_action") or "unknown"),
        platform=str(rec.get("platform") or role_info.get("platform") or "unknown"),
    )


def resolve_field(source_name: str, field_name_or_path: str) -> Dict[str, Any]:
    source_res = resolve_source(source_name)
    source = str(source_name or "")
    canonical_source = str(source_res["canonical_source"] or source)
    field = str(field_name_or_path or "")

    for key in ((source, field), (canonical_source, field), (_source_from_path(field), field)):
        rec = _field_index().get(key)
        if rec:
            return _result_from_record(source, field, rec).as_dict()

    if not source and "." not in field:
        leaf_matches = [rec for (src, alias), rec in _field_index().items() if alias == field]
        canonical_paths = {rec.get("canonical_field_path") for rec in leaf_matches}
        if len(canonical_paths) == 1 and leaf_matches:
            return _result_from_record(str(leaf_matches[0].get("realtime_source") or ""), field, leaf_matches[0]).as_dict()

    if "." in field:
        path_source = _source_from_path(field)
        source_for_role = resolve_source(path_source)["canonical_source"] if path_source else canonical_source
        role = classify_field_role(str(source_for_role), field)
        return AlignmentResult(
            canonical_source=str(source_for_role),
            canonical_field_path=field,
            match_type="exact_path_match" if path_source == canonical_source else "parent_container_match",
            field_role=str(role["field_role"]),
            confidence=str(role["confidence"]),
            unresolved_reason=role.get("unresolved_reason")
            or (None if role["field_role"] != "unknown_need_review" else "field_role_unknown"),
            need_human_review=bool(role.get("need_human_review")),
            notes=str(role["notes"]),
            cardinality_hint=role.get("cardinality_hint"),
            can_use_for_l4_baseline=role.get("can_use_for_l4_baseline"),
            field_family=role.get("field_family"),
            weapon_action=str(role.get("weapon_action") or "unknown"),
            platform=str(role.get("platform") or "unknown"),
        ).as_dict()

    composed = f"{canonical_source}.{field}" if canonical_source and field else field
    role = classify_field_role(canonical_source, composed)
    return AlignmentResult(
        canonical_source=canonical_source,
        canonical_field_path=composed,
        match_type="unresolved",
        field_role=str(role["field_role"]),
        confidence="low",
        unresolved_reason="unknown_field_alias",
        need_human_review=True,
        notes="field alias not found in registry; composed path only",
        cardinality_hint=role.get("cardinality_hint"),
        can_use_for_l4_baseline=role.get("can_use_for_l4_baseline"),
        field_family=role.get("field_family"),
        weapon_action=str(role.get("weapon_action") or "unknown"),
        platform=str(role.get("platform") or "unknown"),
    ).as_dict()


def explain_resolution(source_name: str, field_name_or_path: str) -> Dict[str, Any]:
    source_res = resolve_source(source_name)
    field_res = resolve_field(source_name, field_name_or_path)
    notes = "; ".join(filter(None, [source_res.get("notes"), field_res.get("notes")]))
    return {
        "input_source": source_name,
        "input_field": field_name_or_path,
        **field_res,
        "source_match_type": source_res.get("match_type"),
        "notes": notes,
    }


def align_realtime_to_offline(realtime_source: str, realtime_field_path: str) -> Dict[str, Any]:
    return resolve_field(realtime_source, realtime_field_path)


def load_field_inventory(path: str) -> List[Dict[str, Any]]:
    if not path or not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, list) else data.get("fields", [])


def deterministic_candidate_matches(
    realtime_fields: Iterable[Dict[str, Any]],
    offline_fields: Iterable[Dict[str, Any]],
) -> Dict[str, List[Dict[str, Any]]]:
    """Produce deterministic alignment buckets without model promotion."""
    offline_by_path = {f.get("field_path"): f for f in offline_fields}
    offline_by_leaf: Dict[str, List[Dict[str, Any]]] = {}
    for item in offline_fields:
        offline_by_leaf.setdefault(_leaf(str(item.get("field_path") or item.get("field_name") or "")), []).append(item)

    out = {
        "confirmed_match": [],
        "likely_match_need_review": [],
        "conflict_same_leaf_key": [],
        "unresolved": [],
        "no_match": [],
    }
    for rt in realtime_fields:
        source = str(rt.get("source_name") or rt.get("realtime_source") or "")
        field = str(rt.get("field_path") or rt.get("field_name") or "")
        res = align_realtime_to_offline(source, field)
        offline_hit = offline_by_path.get(res["canonical_field_path"])
        row = {"realtime": rt, "resolution": res, "offline_inventory": offline_hit}
        if offline_hit and res["match_type"] in {"seed_mapping_match", "source_alias_field_match", "exact_path_match"} and not res["need_human_review"]:
            out["confirmed_match"].append(row)
        elif res["unresolved_reason"]:
            out["unresolved"].append(row)
        else:
            leaf_matches = offline_by_leaf.get(_leaf(field), [])
            if len(leaf_matches) > 1:
                out["conflict_same_leaf_key"].append(row)
            elif len(leaf_matches) == 1:
                row["resolution"] = {**res, "match_type": "leaf_key_unique_match", "need_human_review": True}
                out["likely_match_need_review"].append(row)
            else:
                out["no_match"].append(row)
    return out
