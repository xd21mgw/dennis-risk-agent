#!/usr/bin/env python3
"""normal_baseline_enricher.py — Batch enrich L3 candidate pool with normal baseline context.

Primary mode: batch enrich (L3 candidates → enriched candidates)
Debug mode: single-point lookup (one source_name + field_path + field_value)

Output never contains: risk_judgement, feature_candidate, candidate_feature_decision

v0.1.4: canonical field_path normalization moved BEFORE baseline lookup.
This lets the enricher use canonical profiler paths instead of G-R9 flat paths.
"""

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Optional

ALIGNMENT_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "realtime_offline_field_alignment")
)
if ALIGNMENT_DIR not in sys.path:
    sys.path.insert(0, ALIGNMENT_DIR)

from field_alignment_resolver import resolve_field, resolve_source  # noqa: E402

FORBIDDEN_OUTPUT_KEYS = {"risk_judgement", "feature_candidate", "candidate_feature_decision"}

# ---- Canonical field/source normalization (v0.1.4) ----
# Normalization now delegates to realtime_offline_field_alignment.
# Do not add local FIELD_ALIAS_MAP / SOURCE_ALIAS_MAP here.


def normalize_field_path(field_path: str, source_name: str = "") -> str:
    """Normalize field_path to canonical profiler path before baseline lookup."""
    return resolve_field(source_name, field_path).get("canonical_field_path", field_path)


def infer_source_name(field_path: str, provided_source: str = "") -> str:
    """Infer canonical source_name from canonical field_path or preserve provided source."""
    if provided_source:
        return resolve_source(provided_source).get("canonical_source", provided_source)
    return resolve_field("", field_path).get("canonical_source", "")

# ---- Index builders ----

def build_low_entropy_index(low_entropy: List[dict]) -> dict:
    """Index low_entropy_profile by (source_name, field_path)."""
    idx = {}
    for e in low_entropy:
        key = (e.get("source_name", ""), e.get("field_path", ""))
        idx[key] = e
    return idx


def build_discrete_distribution_index(discrete: List[dict]) -> dict:
    """Index discrete_field_distribution by (source_name, field_path).
    Each entry also gets a value_index for fast field_value lookup."""
    idx = {}
    for e in discrete:
        key = (e.get("source_name", ""), e.get("field_path", ""))
        # Build value index from top_values
        value_idx = {}
        normalized_value_idx = {}
        for tv in e.get("top_values", []):
            v = str(tv.get("value", ""))
            value_idx[v] = tv
            normalized = canonical_value_key(tv.get("value", ""))
            if normalized:
                existing = normalized_value_idx.get(normalized)
                if existing is None:
                    normalized_value_idx[normalized] = dict(tv)
                else:
                    # Multiple raw values can be equivalent after canonicalization
                    # (for example 0 and "0"). Aggregate conservatively.
                    merged = dict(existing)
                    merged["count"] = (merged.get("count") or 0) + (tv.get("count") or 0)
                    merged["ratio"] = (merged.get("ratio") or 0.0) + (tv.get("ratio") or 0.0)
                    ranks = [r for r in (merged.get("rank"), tv.get("rank")) if r is not None]
                    merged["rank"] = min(ranks) if ranks else None
                    merged.setdefault("raw_values", [])
                    if "raw_values" not in merged:
                        merged["raw_values"] = [existing.get("value")]
                    merged["raw_values"].append(tv.get("value"))
                    normalized_value_idx[normalized] = merged
        entry = dict(e)
        entry["_value_index"] = value_idx
        entry["_normalized_value_index"] = normalized_value_idx
        idx[key] = entry
    return idx


def build_high_cardinality_index(hc: List[dict]) -> dict:
    """Index high_cardinality_summary by (source_name, field_path)."""
    idx = {}
    for e in hc:
        key = (e.get("source_name", ""), e.get("field_path", ""))
        idx[key] = e
    return idx


# ---- Single candidate enrichment ----

def _compute_baseline_caveat(normal_status: str, high_cardinality: bool) -> str:
    """Compute caveat string based on normal_status."""
    if high_cardinality:
        return "high_cardinality: 不走普通 TOP-N 解释，只做 high_cardinality_summary 参考"
    caveats = {
        "normal_low_entropy": "大盘极高频，不代表安全；L4 建议降权或作为解释",
        "normal_popular": "大盘较高频，不代表安全；L4 建议降权或作为解释",
        "normal_not_popular_in_sample": "大盘不常见，可进入后续验证，不等于风险",
        "normal_referenceable": "参考级频率，样本不足强低熵判断，不做强判断",
        "normal_observable": "观察级频率，样本不足，不做强判断",
        "normal_sparse_or_low_coverage": "样本不足，不做频率判断",
    }
    return caveats.get(normal_status, "")


def _compute_recommended_l4_use(normal_status: str, high_cardinality: bool) -> str:
    """Compute recommended L4 action."""
    if high_cardinality:
        return "high_cardinality_reference_only"
    recs = {
        "normal_low_entropy": "downgrade_or_explain",
        "normal_popular": "downgrade_or_explain",
        "normal_not_popular_in_sample": "candidate_for_validation",
        "normal_referenceable": "weak_reference_only",
        "normal_observable": "weak_reference_only",
        "normal_sparse_or_low_coverage": "baseline_gap_no_judgement",
    }
    return recs.get(normal_status, "no_recommendation")


def canonical_value_key(value: Any) -> str:
    """Return a comparable key for normal/risk value lookup.

    This only normalizes representation differences such as 0 vs "0" and
    false vs "false". It does not encode detector semantics.
    """
    if value is None:
        return ""
    if isinstance(value, bool):
        return "1" if value else "0"
    raw = str(value).strip()
    lower = raw.lower()
    if lower in {"false", "f"}:
        return "0"
    if lower in {"true", "t"}:
        return "1"
    if lower in {"0", "0.0"}:
        return "0"
    if lower in {"1", "1.0"}:
        return "1"
    return raw


def _is_boolish_value(value: Any) -> bool:
    return canonical_value_key(value) in {"0", "1"} and str(value).strip().lower() in {
        "0", "1", "0.0", "1.0", "true", "false", "t", "f"
    }


def is_low_cardinality_value_candidate(candidate: dict, dd_entry: Optional[dict]) -> bool:
    """Return whether this candidate should be treated as low-cardinality.

    This is a distribution-shape check, not a business semantic judgement.
    """
    value = candidate.get("field_value")
    if value in (None, ""):
        value = candidate.get("field_value_or_pattern")

    distinct = None
    if dd_entry is not None:
        distinct = dd_entry.get("distinct_value_count")
        if distinct is None:
            distinct = len(dd_entry.get("top_values", []))
        try:
            distinct = int(distinct)
        except (TypeError, ValueError):
            distinct = None

    if _is_boolish_value(value):
        # Avoid treating every numeric "1" as binary if the normal field has
        # a broad numeric distribution.
        return distinct is None or distinct <= 5

    if distinct is not None and distinct <= 5:
        return True

    return False


def _mark_value_distribution_incomplete(result: dict, candidate: dict, dd_entry: dict, normalized_value_key: str) -> None:
    result["normal_value_rank"] = None
    result["normal_value_count"] = None
    result["normal_value_ratio"] = None
    result["normal_value_lookup_status"] = "normal_value_distribution_incomplete"
    result["normal_value_distribution_reliable"] = False
    result["normal_value_lookup_note"] = (
        "high_coverage_low_cardinality_field_value_missing_from_top_distribution; "
        "do_not_treat_missing_lookup_as_normal_hit_rate_zero"
    )
    result["normalized_value_key"] = normalized_value_key
    result["raw_value"] = candidate.get("field_value", candidate.get("field_value_or_pattern"))


def enrich_one_candidate(
    candidate: dict,
    le_index: dict,
    dd_index: dict,
    hc_index: dict,
    metadata: dict,
) -> dict:
    """Enrich a single L3 candidate with normal baseline context.

    Preserves all original candidate fields and appends baseline fields.

    v0.1.4: canonical field_path normalization happens HERE, before baseline lookup.
    """
    result = dict(candidate)  # copy original fields

    raw_source_name = candidate.get("source_name", "")
    raw_field_path = candidate.get("field_path", "")
    raw_candidate_value = candidate.get("field_value")
    if raw_candidate_value in (None, ""):
        raw_candidate_value = candidate.get("field_value_or_pattern", "")
    field_value = str(raw_candidate_value)
    normalized_value_key = canonical_value_key(raw_candidate_value)

    # v0.1.4: normalize BEFORE baseline lookup
    field_path = normalize_field_path(raw_field_path, raw_source_name)
    source_name = infer_source_name(field_path, raw_source_name)

    # Preserve original for audit/debug and expose canonical for downstream consumers.
    result["original_source_name"] = raw_source_name if raw_source_name != source_name else None
    result["original_field_path"] = raw_field_path if raw_field_path != field_path else None
    result["source_name"] = source_name or raw_source_name
    result["field_path"] = field_path
    result["canonical_lookup_applied"] = (raw_field_path != field_path) or (raw_source_name != (source_name or raw_source_name))

    key = (result["source_name"], result["field_path"])

    # Check high cardinality first
    hc_entry = hc_index.get(key)
    high_cardinality = hc_entry is not None

    # Look up low_entropy_profile
    le_entry = le_index.get(key)

    # Look up discrete_field_distribution
    dd_entry = dd_index.get(key)

    if le_entry is None and dd_entry is None and hc_entry is None:
        # Complete baseline miss
        result["baseline_hit"] = False
        result["normal_status"] = None
        result["normal_covered_count"] = None
        result["normal_coverage_ratio"] = None
        result["normal_value_rank"] = None
        result["normal_value_count"] = None
        result["normal_value_ratio"] = None
        result["normal_value_lookup_status"] = "field_unobserved"
        result["normal_value_distribution_reliable"] = False
        result["normal_value_lookup_note"] = "field not observed in normal baseline"
        result["raw_value"] = raw_candidate_value
        result["normalized_value_key"] = normalized_value_key
        result["normal_top1_ratio"] = None
        result["normal_top3_ratio"] = None
        result["high_cardinality"] = False
        result["baseline_scope"] = metadata.get("baseline_scope")
        result["sample_size_level"] = metadata.get("sample_size_level")
        result["not_login_aue_specific"] = metadata.get("not_login_aue_specific")
        result["baseline_caveat"] = "baseline_gap: baseline 中无此字段数据，不做负向结论"
        result["recommended_l4_use"] = "baseline_gap_no_judgement"
        return result

    # Baseline hit
    result["baseline_hit"] = True
    result["high_cardinality"] = high_cardinality
    result["baseline_scope"] = metadata.get("baseline_scope")
    result["sample_size_level"] = metadata.get("sample_size_level")
    result["not_login_aue_specific"] = metadata.get("not_login_aue_specific")

    if high_cardinality:
        # High cardinality: only return summary, no TOP-N
        result["normal_status"] = "high_cardinality_field"
        result["normal_covered_count"] = hc_entry.get("covered_entity_count",
                                                        hc_entry.get("distinct_value_count"))
        result["normal_coverage_ratio"] = None
        result["normal_value_rank"] = None
        result["normal_value_count"] = None
        result["normal_value_ratio"] = None
        result["normal_value_lookup_status"] = "high_cardinality_skipped"
        result["normal_value_distribution_reliable"] = False
        result["normal_value_lookup_note"] = "high cardinality field; value distribution skipped"
        result["raw_value"] = raw_candidate_value
        result["normalized_value_key"] = normalized_value_key
        result["normal_top1_ratio"] = None
        result["normal_top3_ratio"] = None
        # Add HC-specific fields
        result["hc_distinct_value_count"] = hc_entry.get("distinct_value_count")
        result["hc_unique_value_ratio"] = hc_entry.get("unique_value_ratio")
        result["hc_reuse_ratio"] = hc_entry.get("reuse_ratio")
        result["hc_max_entities_per_value"] = hc_entry.get("max_entities_per_value")
        result["baseline_caveat"] = _compute_baseline_caveat("high_cardinality_field", True)
        result["recommended_l4_use"] = _compute_recommended_l4_use("high_cardinality_field", True)
        return result

    # Normal field: get from low_entropy_profile
    if le_entry is not None:
        result["normal_status"] = le_entry.get("normal_status")
        result["normal_covered_count"] = le_entry.get("covered_count")
        result["normal_coverage_ratio"] = le_entry.get("coverage_ratio")
        result["normal_top1_ratio"] = le_entry.get("top1_ratio")
        result["normal_top3_ratio"] = le_entry.get("top3_ratio")
    else:
        result["normal_status"] = None
        result["normal_covered_count"] = None
        result["normal_coverage_ratio"] = None
        result["normal_top1_ratio"] = None
        result["normal_top3_ratio"] = None

    # Value-level lookup from discrete_field_distribution
    result["raw_value"] = raw_candidate_value
    result["normalized_value_key"] = normalized_value_key
    result["normal_value_distribution_reliable"] = False
    result["normal_value_lookup_note"] = ""

    if dd_entry is not None and field_value:
        value_idx = dd_entry.get("_value_index", {})
        normalized_value_idx = dd_entry.get("_normalized_value_index", {})
        value_hit = value_idx.get(field_value)
        if value_hit is None and normalized_value_key:
            value_hit = normalized_value_idx.get(normalized_value_key)
        if value_hit is not None:
            result["normal_value_rank"] = value_hit.get("rank")
            result["normal_value_count"] = value_hit.get("count")
            result["normal_value_ratio"] = value_hit.get("ratio")
            result["normal_value_lookup_status"] = "value_matched"
            result["normal_value_distribution_reliable"] = True
            result["normal_value_lookup_note"] = "matched by canonical value key" if value_idx.get(field_value) is None else "matched by raw value"
        else:
            # Value not in top_values
            coverage = dd_entry.get("coverage_ratio")
            try:
                coverage = float(coverage)
            except (TypeError, ValueError):
                coverage = None
            if (
                coverage is not None
                and coverage >= 0.8
                and is_low_cardinality_value_candidate(candidate, dd_entry)
            ):
                _mark_value_distribution_incomplete(result, candidate, dd_entry, normalized_value_key)
            else:
                result["normal_value_rank"] = None
                result["normal_value_count"] = 0
                result["normal_value_ratio"] = 0.0
                result["normal_value_lookup_status"] = "value_not_found_in_top"
                result["normal_value_distribution_reliable"] = False
                result["normal_value_lookup_note"] = "value not found in top distribution; top distribution may be incomplete"
        # Fill covered_count from dd if le didn't have it
        if result["normal_covered_count"] is None:
            result["normal_covered_count"] = dd_entry.get("covered_entity_count")
        if result["normal_coverage_ratio"] is None:
            result["normal_coverage_ratio"] = dd_entry.get("coverage_ratio")
        if result["normal_top1_ratio"] is None:
            result["normal_top1_ratio"] = dd_entry.get("top1_ratio")
        if result["normal_top3_ratio"] is None:
            result["normal_top3_ratio"] = dd_entry.get("top3_ratio")
    else:
        result["normal_value_rank"] = None
        result["normal_value_count"] = None
        result["normal_value_ratio"] = None
        result["normal_value_lookup_status"] = "field_matched_but_value_not_evaluated"
        result["normal_value_distribution_reliable"] = False
        result["normal_value_lookup_note"] = "field matched but candidate value was not evaluated"

    result["baseline_caveat"] = _compute_baseline_caveat(
        result.get("normal_status", ""), False)
    result["recommended_l4_use"] = _compute_recommended_l4_use(
        result.get("normal_status", ""), False)

    return result


# ---- Batch enrichment ----

def batch_enrich(
    candidates: List[dict],
    baseline_dir: str,
) -> dict:
    """Enrich a list of L3 candidates with normal baseline context.

    Returns: {"enriched_candidates": [...], "enrichment_metadata": {...}}
    """
    # Load baseline data
    le = _load_json(os.path.join(baseline_dir, "normal_low_entropy_profile.json"))
    dd = _load_json(os.path.join(baseline_dir, "normal_discrete_field_distribution.json"))
    hc = _load_json(os.path.join(baseline_dir, "high_cardinality_summary.json"))
    meta = _load_json(os.path.join(baseline_dir, "profiler_metadata.json"))
    if not isinstance(meta, dict):
        meta = {}

    # Build indices
    le_index = build_low_entropy_index(le)
    dd_index = build_discrete_distribution_index(dd)
    hc_index = build_high_cardinality_index(hc)

    # Enrich each candidate
    enriched = []
    for c in candidates:
        e = enrich_one_candidate(c, le_index, dd_index, hc_index, meta)
        # Strip forbidden keys
        for k in FORBIDDEN_OUTPUT_KEYS:
            e.pop(k, None)
        enriched.append(e)

    # Build enrichment metadata
    status_dist = {}
    hc_count = 0
    miss_count = 0
    for e in enriched:
        if not e.get("baseline_hit", False):
            miss_count += 1
        elif e.get("high_cardinality"):
            hc_count += 1
        else:
            s = e.get("normal_status", "unknown")
            status_dist[s] = status_dist.get(s, 0) + 1

    enrichment_meta = {
        "input_candidate_count": len(candidates),
        "output_enriched_count": len(enriched),
        "baseline_hit_count": len(enriched) - miss_count,
        "baseline_miss_count": miss_count,
        "high_cardinality_count": hc_count,
        "normal_status_distribution": status_dist,
        "baseline_scope": meta.get("baseline_scope"),
        "sample_size_level": meta.get("sample_size_level"),
        "not_login_aue_specific": meta.get("not_login_aue_specific"),
        "rule_source": meta.get("rule_source"),
        "canonical_lookup_enabled": True,
        "canonical_lookup_applied_count": sum(1 for e in enriched if e.get("canonical_lookup_applied")),
        "forbidden_keys_checked": sorted(list(FORBIDDEN_OUTPUT_KEYS)),
    }

    return {
        "enriched_candidates": enriched,
        "enrichment_metadata": enrichment_meta,
    }


# ---- Debug single-point lookup ----

def debug_lookup(
    baseline_dir: str,
    source_name: str,
    field_path: str,
    field_value: Optional[str] = None,
) -> dict:
    """Debug single-point lookup for one field/value combination."""
    candidate = {
        "candidate_id": "debug_lookup",
        "source_name": source_name,
        "field_path": field_path,
        "field_value": field_value or "",
        "risk_sample_count": 0,
        "risk_covered_count": 0,
        "risk_value_count": 0,
        "risk_value_ratio": 0.0,
    }

    result = batch_enrich([candidate], baseline_dir)
    enriched = result["enriched_candidates"][0]
    enriched["debug_mode"] = True
    return enriched


# ---- Helpers ----

def _load_json(path: str) -> Any:
    """Load JSON file with error handling."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print("WARNING: File not found: %s" % path, file=sys.stderr)
        return []
    except json.JSONDecodeError as e:
        print("WARNING: JSON parse error in %s: %s" % (path, e), file=sys.stderr)
        return []


def _validate_candidates(candidates: List[dict]) -> List[str]:
    """Validate candidate list structure. Returns list of issues."""
    issues = []
    required_keys = ["candidate_id", "source_name", "field_path"]
    for i, c in enumerate(candidates):
        for k in required_keys:
            if k not in c:
                issues.append("candidate[%d] missing required key: %s" % (i, k))
    return issues


# ---- CLI ----

def main():
    parser = argparse.ArgumentParser(
        description="normal_baseline_enricher: batch enrich L3 candidate pool with normal baseline context"
    )
    parser.add_argument("--baseline-dir", required=True,
                        help="Directory containing profiler output JSON files")
    parser.add_argument("--input-candidates",
                        help="L3 candidates JSON file (batch enrich mode)")
    parser.add_argument("--output",
                        help="Output file for enriched candidates JSON")
    # Debug mode args
    parser.add_argument("--source-name",
                        help="Source name for debug single-point lookup")
    parser.add_argument("--field-path",
                        help="Field path for debug single-point lookup")
    parser.add_argument("--field-value", default="",
                        help="Field value for debug single-point lookup (optional)")

    args = parser.parse_args()

    # Determine mode
    if args.input_candidates:
        # Batch enrich mode
        print("normal_baseline_enricher — batch enrich mode")
        print("  baseline_dir: %s" % args.baseline_dir)
        print("  input_candidates: %s" % args.input_candidates)
        print("  output: %s" % (args.output or "stdout"))

        candidates = _load_json(args.input_candidates)
        if not isinstance(candidates, list):
            print("ERROR: input_candidates must be a JSON array", file=sys.stderr)
            sys.exit(1)

        issues = _validate_candidates(candidates)
        if issues:
            for issue in issues:
                print("VALIDATION: %s" % issue, file=sys.stderr)

        result = batch_enrich(candidates, args.baseline_dir)

        # Output
        output_json = json.dumps(result, ensure_ascii=False, indent=2)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(output_json)
            print("Enriched %d candidates -> %s" % (
                result["enrichment_metadata"]["output_enriched_count"], args.output))
        else:
            print(output_json)

        # Print summary
        meta = result["enrichment_metadata"]
        print("\nEnrichment summary:")
        print("  Input: %d candidates" % meta["input_candidate_count"])
        print("  Output: %d enriched" % meta["output_enriched_count"])
        print("  Baseline hit: %d" % meta["baseline_hit_count"])
        print("  Baseline miss: %d" % meta["baseline_miss_count"])
        print("  High cardinality: %d" % meta["high_cardinality_count"])
        print("  Normal status distribution: %s" % meta["normal_status_distribution"])

    elif args.source_name and args.field_path:
        # Debug single-point lookup mode
        print("normal_baseline_enricher — debug lookup mode")
        print("  baseline_dir: %s" % args.baseline_dir)
        print("  source_name: %s" % args.source_name)
        print("  field_path: %s" % args.field_path)
        print("  field_value: %s" % (args.field_value or "(none)"))

        result = debug_lookup(
            args.baseline_dir, args.source_name, args.field_path, args.field_value)

        print("\nLookup result:")
        print(json.dumps(result, ensure_ascii=False, indent=2))

    else:
        parser.print_help()
        print("\nERROR: Provide --input-candidates for batch mode, "
              "or --source-name + --field-path for debug mode.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
