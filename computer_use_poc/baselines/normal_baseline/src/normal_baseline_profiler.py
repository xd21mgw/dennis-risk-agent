#!/usr/bin/env python3
"""
normal_baseline_profiler.py v0.1

Local profiler for normal_baseline: field discovery, profile, distribution,
missingness, high-cardinality summary, and low-entropy profile.

This module only provides normal-side objective statistics.
It does NOT output risk_judgement, feature_candidate, or candidate_feature_decision.

Usage:
  python normal_baseline_profiler.py \
    --input-dir <path_to_excels> \
    --contract <path_to_contract_yaml> \
    --output-dir <output_path> \
    --topn-limit 20
"""

import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

# ==============================================================================
# Constants
# ==============================================================================

TOP_N_DEFAULT = 20
OTHER_BUCKET = "__OTHER__"
MAX_JSON_DEPTH = 5
SAMPLE_FREQUENCY_RULE = {
    "rule_source": "sample_frequency_rule_v0_1",
    "observable_min_covered_count": 200,
    "referenceable_min_covered_count": 300,
    "strong_low_entropy_min_covered_count": 1000,
    "min_coverage_ratio_for_strong": 0.8,
    "top1_ratio_threshold": 0.9,
    "top3_ratio_threshold": 0.97,
}

HIGH_CARDINALITY_FIELDS = {
    "user_id", "device_id", "did", "deviceId", "deviceid",
    "xm1", "xm3", "androidId", "oaid", "idfa", "idfv",
    "ip", "user_ip", "user_ip_v6", "user_ipv6",
    "photoId", "commentId", "requestId",
    "headerKsId", "vendorUniqueId", "sourceIp", "wifiIp",
    "clientIP", "clientIp", "account_identifier_md5", "ks_log_id",
    "imei", "egid", "did_gt",
}

CREDENTIAL_FIELDS = {
    "cookie", "cookies", "token", "tokenId", "session", "session_id",
    "header", "authorization", "password", "API_key",
    "secretKeyVersion", "signVersion", "headerKsId",
    "__NS_xfalcon", "__NStokensig", "__NS_sig3",
    "sig", "client_key", "ssecurity", "riskControlToken",
}

FIELD_LIFECYCLE_STATUS = [
    "discovered", "sample_profiled", "aggregation_scheduled",
    "aggregated", "deferred_due_to_cost", "parse_failed", "unknown_semantics",
]

NORMAL_STATUS_ENUM = [
    "normal_popular", "normal_low_entropy",
    "normal_not_popular_in_sample",
    "normal_referenceable",
    "normal_observable",
    "normal_sparse_or_low_coverage",
    "normal_unknown_sampling_bias",
    "normal_unknown_semantics",
]

MISSINGNESS_TYPE_ENUM = [
    "normal_present", "normal_sparse_field",
    "low_coverage_unreliable", "parse_failed",
    "source_not_checked", "unknown",
]

CARDINALITY_BUCKETS = {
    "low": 20,       # distinct <= 20
    "medium": 100,   # distinct <= 100
    "high": 1000,    # distinct <= 1000
    "very_high": None, # distinct > 1000
}

# Excel file mapping: source_id -> filename pattern
EXCEL_FILE_MAP = {
    "infra_user_action_log": "统一登陆日志",
    "passport_action_log": "档案中心用户分析",
    "weapon_android": "android weapon基线样例",
    "weapon_ios": "IOSweapon样例",
    "schema_reference": "四表常见action关联离线表schema",
}


# ==============================================================================
# Utility functions
# ==============================================================================

def classify_cardinality(distinct_count):
    """Classify distinct value count into a cardinality bucket."""
    if distinct_count <= 20:
        return "low"
    elif distinct_count <= 100:
        return "medium"
    elif distinct_count <= 1000:
        return "high"
    else:
        return "very_high"


def guess_type_from_values(values):
    """Guess field type from a sample of values."""
    if values is None or len(values) == 0:
        return "unknown"
    sample = list(values)[:20]
    types_seen = set()
    for v in sample:
        if v is None or (isinstance(v, float) and pd.isna(v)):
            continue
        if isinstance(v, bool):
            types_seen.add("boolean")
        elif isinstance(v, int):
            types_seen.add("int")
        elif isinstance(v, float):
            types_seen.add("float")
        elif isinstance(v, str):
            try:
                json.loads(v)
                types_seen.add("json_string")
            except (json.JSONDecodeError, TypeError):
                types_seen.add("string")
        else:
            types_seen.add("unknown")

    if len(types_seen) == 1:
        t = types_seen.pop()
        if t == "json_string":
            return "json_string"
        return t
    elif types_seen == {"int", "float"}:
        return "float"
    elif "json_string" in types_seen:
        return "json_string"
    elif len(types_seen) > 2:
        return "mixed"
    else:
        return "string"


def compute_top_n(counter, topn_limit):
    """Compute TOP-N distribution with __OTHER__ bucket."""
    total = sum(counter.values())
    if total == 0:
        return [], 0, 0.0

    sorted_items = counter.most_common(topn_limit)
    top_count = sum(c for _, c in sorted_items)
    other_count = total - top_count

    result = []
    for rank, (val, cnt) in enumerate(sorted_items, 1):
        result.append({
            "value": str(val),
            "count": cnt,
            "ratio": cnt / total,
            "rank": rank,
        })

    return result, other_count, other_count / total if total > 0 else 0.0


def compute_missingness(series, total_count):
    """Compute missingness profile for a field."""
    covered = series.notna().sum()
    missing = total_count - covered
    null_count = series.isna().sum()

    # Count empty strings
    empty_count = 0
    parse_error_count = 0
    for v in series:
        if v is None or (isinstance(v, float) and pd.isna(v)):
            continue
        s = str(v).strip()
        if s == "":
            empty_count += 1

    coverage = covered / total_count if total_count > 0 else 0.0
    missing_ratio = missing / total_count if total_count > 0 else 0.0
    null_ratio = null_count / total_count if total_count > 0 else 0.0
    empty_ratio = empty_count / total_count if total_count > 0 else 0.0
    parse_error_ratio = parse_error_count / total_count if total_count > 0 else 0.0

    # Classify missingness type
    if coverage >= 0.95:
        mt = "normal_present"
    elif coverage >= 0.5:
        mt = "normal_sparse_field"
    elif coverage >= 0.2:
        mt = "low_coverage_unreliable"
    elif coverage > 0:
        mt = "source_not_checked"
    else:
        mt = "unknown"

    return {
        "covered_entity_count": int(covered),
        "coverage_ratio": round(coverage, 4),
        "missing_count": int(missing),
        "missing_ratio": round(missing_ratio, 4),
        "null_ratio": round(null_ratio, 4),
        "empty_string_ratio": round(empty_ratio, 4),
        "parse_error_ratio": round(parse_error_ratio, 4),
        "missingness_type": mt,
    }


# ==============================================================================
# JSON recursive expansion
# ==============================================================================

def expand_json_field(raw_json_str, parent_path, source_name, depth=0, max_depth=MAX_JSON_DEPTH):
    """Recursively expand a JSON string into field_path -> value mappings."""
    if depth > max_depth:
        return {parent_path: {"parse_status": "parse_depth_exceeded", "value": None}}

    try:
        parsed = json.loads(raw_json_str)
    except (json.JSONDecodeError, TypeError):
        return {parent_path: {"parse_status": "parse_error", "value": raw_json_str}}

    result = {}
    if isinstance(parsed, dict):
        for key, val in parsed.items():
            child_path = f"{parent_path}.{key}"
            # Skip credential fields
            if key in CREDENTIAL_FIELDS:
                result[child_path] = {"parse_status": "credential_skipped", "value": str(val)[:50]}
                continue
            # High cardinality fields only record presence
            if key in HIGH_CARDINALITY_FIELDS:
                result[child_path] = {"parse_status": "high_cardinality_skipped", "value": str(val)[:50]}
                continue

            if isinstance(val, dict):
                sub = expand_json_field(json.dumps(val), child_path, source_name, depth + 1, max_depth)
                result.update(sub)
            elif isinstance(val, list):
                # Normalize array
                if len(val) == 0:
                    result[child_path] = {"parse_status": "parsed_ok", "value": []}
                elif len(val) == 1 and not isinstance(val[0], dict):
                    result[child_path] = {"parse_status": "parsed_ok", "value": val[0]}
                else:
                    # Multi-value array or dict array
                    if isinstance(val[0], dict):
                        for i, item in enumerate(val[:10]):
                            item_path = f"{child_path}[{i}]"
                            sub = expand_json_field(json.dumps(item), item_path, source_name, depth + 1, max_depth)
                            result.update(sub)
                    else:
                        result[child_path] = {"parse_status": "parsed_ok", "value": val}
            elif isinstance(val, str):
                # Try secondary JSON parse
                try:
                    inner = json.loads(val)
                    if isinstance(inner, (dict, list)):
                        sub = expand_json_field(val, child_path, source_name, depth + 1, max_depth)
                        result.update(sub)
                    else:
                        result[child_path] = {"parse_status": "parsed_ok", "value": inner}
                except (json.JSONDecodeError, TypeError):
                    result[child_path] = {"parse_status": "parsed_ok", "value": val}
            else:
                result[child_path] = {"parse_status": "parsed_ok", "value": val}
    elif isinstance(parsed, list):
        result[parent_path] = {"parse_status": "parsed_ok", "value": parsed}
    else:
        result[parent_path] = {"parse_status": "parsed_ok", "value": parsed}

    return result


def unwrap_array_value(val):
    """Unwrap passport params array-style values: ["2"] -> "2"."""
    if isinstance(val, list):
        if len(val) == 0:
            return None
        elif len(val) == 1:
            return val[0]
        else:
            # Multi-value: return as list for array_normalize
            return val
    return val


# ==============================================================================
# SourceProfiler - profiles one source
# ==============================================================================

class SourceProfiler:
    """Profile a single data source for normal_baseline."""

    def __init__(self, source_id, df, column_prefix, topn_limit=TOP_N_DEFAULT,
                 baseline_scope="population_baseline"):
        self.source_id = source_id
        self.df = df
        self.column_prefix = column_prefix
        self.topn_limit = topn_limit
        self.baseline_scope = baseline_scope
        self.total_entity_count = len(df)
        self.field_inventory = []
        self.field_profiles = []
        self.discrete_distributions = []
        self.missingness_profiles = []
        self.high_cardinality_summaries = []
        self.low_entropy_profiles = []

    def _get_col(self, raw_name):
        """Get column name, handling prefix stripping."""
        if self.column_prefix:
            prefixed = f"{self.column_prefix}.{raw_name}"
            if prefixed in self.df.columns:
                return prefixed
        if raw_name in self.df.columns:
            return raw_name
        return None

    def profile_ordinary_column(self, col_name, field_name):
        """Profile an ordinary (non-JSON, non-array) column."""
        col = self._get_col(col_name)
        if col is None:
            return None

        series = self.df[col]
        is_high_card = field_name in HIGH_CARDINALITY_FIELDS
        is_cred = field_name in CREDENTIAL_FIELDS

        coverage = series.notna().mean()
        distinct = series.dropna().nunique()
        cardinality_bucket = classify_cardinality(distinct)

        # Missingness
        miss = compute_missingness(series, self.total_entity_count)

        # Field inventory entry
        inventory_entry = {
            "source_name": self.source_id,
            "field_path": f"{self.source_id}.{field_name}",
            "field_name": field_name,
            "field_origin": "ordinary_column",
            "seen_count": int(series.notna().sum()),
            "coverage_ratio": round(coverage, 4),
            "example_values": [str(v)[:80] for v in series.dropna().unique()[:5]],
            "guessed_type": guess_type_from_values(series.dropna().values),
            "cardinality_bucket": cardinality_bucket,
            "parse_status": "parsed_ok",
        }
        self.field_inventory.append(inventory_entry)

        # Missingness profile
        miss_entry = {
            "field_path": f"{self.source_id}.{field_name}",
            "total_entity_count": self.total_entity_count,
            **miss,
        }
        self.missingness_profiles.append(miss_entry)

        # High cardinality: only summary
        if is_high_card:
            hc_entry = self._compute_high_cardinality_summary(field_name, series)
            self.high_cardinality_summaries.append(hc_entry)
            # Field profile with lifecycle
            profile_entry = {
                "field_path": f"{self.source_id}.{field_name}",
                "guessed_type": guess_type_from_values(series.dropna().values),
                "coverage_ratio": round(coverage, 4),
                "missing_ratio": round(1 - coverage, 4),
                "distinct_value_count": int(distinct),
                "top1_ratio": None,  # not computed for HC
                "top3_ratio": None,
                "cardinality_bucket": cardinality_bucket,
                "value_shape": "near_unique",
                "sample_examples": [str(v)[:50] for v in series.dropna().unique()[:3]],
                "field_lifecycle_status": "sample_profiled",
            }
            self.field_profiles.append(profile_entry)
            return inventory_entry

        # Credential: only coverage
        if is_cred:
            profile_entry = {
                "field_path": f"{self.source_id}.{field_name}",
                "guessed_type": "credential",
                "coverage_ratio": round(coverage, 4),
                "missing_ratio": round(1 - coverage, 4),
                "distinct_value_count": None,
                "top1_ratio": None,
                "top3_ratio": None,
                "cardinality_bucket": "unknown",
                "value_shape": "credential",
                "sample_examples": [],
                "field_lifecycle_status": "deferred_due_to_cost",
            }
            self.field_profiles.append(profile_entry)
            return inventory_entry

        # Normal discrete: compute TOP-N
        counter = Counter(series.dropna().astype(str))
        top_values, other_count, other_ratio = compute_top_n(counter, self.topn_limit)

        top1_ratio = top_values[0]["ratio"] if top_values else 0.0
        top3_sum = sum(v["ratio"] for v in top_values[:3]) if len(top_values) >= 1 else 0.0
        top3_ratio = min(top3_sum, 1.0)

        # Determine value_shape
        if distinct <= 5:
            value_shape = "enum"
        elif distinct <= 20:
            value_shape = "enum"
        else:
            value_shape = "scalar"

        # Discrete distribution entry
        dist_entry = {
            "source_name": self.source_id,
            "field_path": f"{self.source_id}.{field_name}",
            "total_entity_count": self.total_entity_count,
            "covered_entity_count": int(series.notna().sum()),
            "coverage_ratio": round(coverage, 4),
            "distinct_value_count": int(distinct),
            "top_values": top_values,
            "other_value_count": int(other_count),
            "other_value_ratio": round(other_ratio, 4),
            "top1_ratio": round(top1_ratio, 4),
            "top3_ratio": round(top3_ratio, 4),
            "full_value_distribution_stored": False,
        }
        self.discrete_distributions.append(dist_entry)

        # Field profile entry
        profile_entry = {
            "field_path": f"{self.source_id}.{field_name}",
            "guessed_type": guess_type_from_values(series.dropna().values),
            "coverage_ratio": round(coverage, 4),
            "missing_ratio": round(1 - coverage, 4),
            "distinct_value_count": int(distinct),
            "top1_ratio": round(top1_ratio, 4),
            "top3_ratio": round(top3_ratio, 4),
            "cardinality_bucket": cardinality_bucket,
            "value_shape": value_shape,
            "sample_examples": [str(v)[:50] for v in series.dropna().unique()[:5]],
            "field_lifecycle_status": "sample_profiled",
        }
        self.field_profiles.append(profile_entry)

        return inventory_entry

    def profile_json_field(self, col_name, field_name, unwrap_arrays=False):
        """Profile a JSON string field by expanding it."""
        col = self._get_col(col_name)
        if col is None:
            return []

        series = self.df[col]
        coverage = series.notna().mean()
        new_entries = []

        # Per-row JSON expansion
        expanded_data = {}  # field_path -> list of values
        for idx, raw_val in enumerate(series):
            if raw_val is None or (isinstance(raw_val, float) and pd.isna(raw_val)):
                continue
            raw_str = str(raw_val).strip()
            if raw_str in ("", "{}"):
                continue

            expanded = expand_json_field(raw_str, f"{self.source_id}.{field_name}",
                                         self.source_id, depth=0)
            for fp, info in expanded.items():
                if fp not in expanded_data:
                    expanded_data[fp] = []
                val = info.get("value", None)
                parse_status = info.get("parse_status", "parsed_ok")

                if unwrap_arrays and val is not None:
                    val = unwrap_array_value(val)

                if val is not None and parse_status == "parsed_ok":
                    expanded_data[fp].append(val)

        # Now profile each expanded field
        for fp, values in expanded_data.items():
            short_name = fp.split(".")[-1]
            is_hc = short_name in HIGH_CARDINALITY_FIELDS
            is_cred = short_name in CREDENTIAL_FIELDS

            val_count = len(values)
            distinct = len(set(str(v) for v in values if v is not None))
            coverage_ratio = val_count / self.total_entity_count if self.total_entity_count > 0 else 0

            inventory_entry = {
                "source_name": self.source_id,
                "field_path": fp,
                "field_name": short_name,
                "field_origin": "json_path",
                "seen_count": val_count,
                "coverage_ratio": round(coverage_ratio, 4),
                "example_values": [str(v)[:80] for v in list(set(str(x) for x in values[:20]))[:5]],
                "guessed_type": guess_type_from_values(values[:20]),
                "cardinality_bucket": classify_cardinality(distinct),
                "parse_status": "parsed_ok",
            }

            if is_hc:
                inventory_entry["parse_status"] = "high_cardinality_skipped"
                # HC summary
                hc_series_vals = [str(v) for v in values if v is not None]
                hc_counter = Counter(hc_series_vals)
                hc_entry = {
                    "source_name": self.source_id,
                    "field_path": fp,
                    "distinct_value_count": len(hc_counter),
                    "unique_value_ratio": round(
                        sum(1 for v, c in hc_counter.items() if c == 1) / len(hc_counter) if hc_counter else 0, 4),
                    "reuse_ratio": round(
                        sum(1 for v, c in hc_counter.items() if c > 1) / len(hc_counter) if hc_counter else 0, 4),
                    "max_entities_per_value": max(hc_counter.values()) if hc_counter else 0,
                    "top_reused_values": [
                        {"value": str(v)[:50], "entity_count": c, "reuse_rank": i + 1}
                        for i, (v, c) in enumerate(hc_counter.most_common(self.topn_limit))
                    ],
                }
                self.high_cardinality_summaries.append(hc_entry)
                self.field_inventory.append(inventory_entry)
                continue

            if is_cred:
                inventory_entry["parse_status"] = "credential_skipped"
                self.field_inventory.append(inventory_entry)
                continue

            self.field_inventory.append(inventory_entry)

            # TOP-N distribution
            str_counter = Counter(str(v) for v in values if v is not None)
            top_values, other_count, other_ratio = compute_top_n(str_counter, self.topn_limit)

            top1 = top_values[0]["ratio"] if top_values else 0.0
            top3_sum = sum(v["ratio"] for v in top_values[:3])
            top3 = min(top3_sum, 1.0)

            # Discrete distribution
            dist_entry = {
                "source_name": self.source_id,
                "field_path": fp,
                "total_entity_count": self.total_entity_count,
                "covered_entity_count": val_count,
                "coverage_ratio": round(coverage_ratio, 4),
                "distinct_value_count": distinct,
                "top_values": top_values,
                "other_value_count": int(other_count),
                "other_value_ratio": round(other_ratio, 4),
                "top1_ratio": round(top1, 4),
                "top3_ratio": round(top3, 4),
                "full_value_distribution_stored": False,
            }
            self.discrete_distributions.append(dist_entry)

            # Field profile
            profile_entry = {
                "field_path": fp,
                "guessed_type": guess_type_from_values(values[:20]),
                "coverage_ratio": round(coverage_ratio, 4),
                "missing_ratio": round(1 - coverage_ratio, 4),
                "distinct_value_count": distinct,
                "top1_ratio": round(top1, 4),
                "top3_ratio": round(top3, 4),
                "cardinality_bucket": classify_cardinality(distinct),
                "value_shape": "enum" if distinct <= 20 else "scalar",
                "sample_examples": [str(v)[:50] for v in list(set(str(x) for x in values[:20]))[:5]],
                "field_lifecycle_status": "sample_profiled",
            }
            self.field_profiles.append(profile_entry)

            # Missingness
            miss_entry = {
                "field_path": fp,
                "total_entity_count": self.total_entity_count,
                "covered_entity_count": val_count,
                "coverage_ratio": round(coverage_ratio, 4),
                "missing_count": self.total_entity_count - val_count,
                "missing_ratio": round(1 - coverage_ratio, 4),
                "null_ratio": round(1 - coverage_ratio, 4),  # JSON key absent = null
                "empty_string_ratio": 0.0,
                "parse_error_ratio": 0.0,
                "missingness_type": "normal_present" if coverage_ratio >= 0.95 else
                    "normal_sparse_field" if coverage_ratio >= 0.5 else "low_coverage_unreliable",
            }
            self.missingness_profiles.append(miss_entry)

        return new_entries

    def profile_array_field(self, col_name, field_name):
        """Profile an array field (like weapon_one_risk) using array_normalize."""
        col = self._get_col(col_name)
        if col is None:
            return None

        series = self.df[col]
        coverage = series.notna().mean()
        covered = int(series.notna().sum())

        # Parse each row as JSON array
        all_items = []
        empty_array_count = 0
        parse_error_count = 0
        for raw_val in series:
            if raw_val is None or (isinstance(raw_val, float) and pd.isna(raw_val)):
                continue
            raw_str = str(raw_val).strip()
            try:
                parsed = json.loads(raw_str)
                if isinstance(parsed, list):
                    if len(parsed) == 0:
                        empty_array_count += 1
                    for item in parsed:
                        all_items.append(str(item))
                else:
                    all_items.append(str(parsed))
            except (json.JSONDecodeError, TypeError):
                parse_error_count += 1

        total_with_data = covered - empty_array_count - parse_error_count
        empty_ratio = empty_array_count / covered if covered > 0 else 0.0

        # TOP-N of labels
        label_counter = Counter(all_items)
        top_labels, other_count, other_ratio = compute_top_n(label_counter, self.topn_limit)

        # Field inventory
        inventory_entry = {
            "source_name": self.source_id,
            "field_path": f"{self.source_id}.{field_name}",
            "field_name": field_name,
            "field_origin": "array",
            "seen_count": covered,
            "coverage_ratio": round(coverage, 4),
            "example_values": [str(v)[:80] for v in list(set(all_items))[:5]],
            "guessed_type": "json_array",
            "cardinality_bucket": classify_cardinality(len(label_counter)),
            "parse_status": "parsed_ok",
        }
        self.field_inventory.append(inventory_entry)

        # Discrete distribution for the array items
        dist_entry = {
            "source_name": self.source_id,
            "field_path": f"{self.source_id}.{field_name}",
            "total_entity_count": self.total_entity_count,
            "covered_entity_count": covered,
            "coverage_ratio": round(coverage, 4),
            "distinct_value_count": len(label_counter),
            "top_values": top_labels,
            "other_value_count": int(other_count),
            "other_value_ratio": round(other_ratio, 4),
            "top1_ratio": top_labels[0]["ratio"] if top_labels else 0.0,
            "top3_ratio": min(sum(v["ratio"] for v in top_labels[:3]), 1.0) if top_labels else 0.0,
            "full_value_distribution_stored": False,
            "empty_array_count": empty_array_count,
            "empty_array_ratio": round(empty_ratio, 4),
            "parse_error_count": parse_error_count,
        }
        self.discrete_distributions.append(dist_entry)

        # Field profile
        profile_entry = {
            "field_path": f"{self.source_id}.{field_name}",
            "guessed_type": "json_array",
            "coverage_ratio": round(coverage, 4),
            "missing_ratio": round(1 - coverage, 4),
            "distinct_value_count": len(label_counter),
            "top1_ratio": top_labels[0]["ratio"] if top_labels else 0.0,
            "top3_ratio": min(sum(v["ratio"] for v in top_labels[:3]), 1.0) if top_labels else 0.0,
            "cardinality_bucket": classify_cardinality(len(label_counter)),
            "value_shape": "array",
            "sample_examples": [str(v)[:50] for v in list(set(all_items))[:5]],
            "field_lifecycle_status": "sample_profiled",
        }
        self.field_profiles.append(profile_entry)

        # Missingness
        miss_entry = {
            "field_path": f"{self.source_id}.{field_name}",
            "total_entity_count": self.total_entity_count,
            **compute_missingness(series, self.total_entity_count),
        }
        self.missingness_profiles.append(miss_entry)

        return inventory_entry

    def _compute_high_cardinality_summary(self, field_name, series):
        """Compute high-cardinality summary for a field."""
        str_vals = series.dropna().astype(str)
        counter = Counter(str_vals)
        unique_count = sum(1 for v, c in counter.items() if c == 1)
        reuse_count = sum(1 for v, c in counter.items() if c > 1)
        total_distinct = len(counter)

        return {
            "source_name": self.source_id,
            "field_path": f"{self.source_id}.{field_name}",
            "distinct_value_count": total_distinct,
            "unique_value_ratio": round(unique_count / total_distinct if total_distinct > 0 else 0, 4),
            "reuse_ratio": round(reuse_count / total_distinct if total_distinct > 0 else 0, 4),
            "max_entities_per_value": max(counter.values()) if counter else 0,
            "top_reused_values": [
                {"value": str(v)[:50], "entity_count": c, "reuse_rank": i + 1}
                for i, (v, c) in enumerate(counter.most_common(self.topn_limit))
            ],
        }

    def compute_low_entropy_profiles(self):
        """Compute low-entropy profiles for all discrete fields.

        Uses layered thresholds from SAMPLE_FREQUENCY_RULE:
        - covered_count < 200: normal_sparse_or_low_coverage
        - 200 <= covered_count < 300: normal_observable
        - 300 <= covered_count < 1000: normal_referenceable
        - covered_count >= 1000: apply strong low-entropy check
        """
        rule = SAMPLE_FREQUENCY_RULE
        observable_min = rule["observable_min_covered_count"]
        referenceable_min = rule["referenceable_min_covered_count"]
        strong_min = rule["strong_low_entropy_min_covered_count"]
        min_coverage_for_strong = rule["min_coverage_ratio_for_strong"]
        top1_thresh = rule["top1_ratio_threshold"]
        top3_thresh = rule["top3_ratio_threshold"]

        for dist in self.discrete_distributions:
            fp = dist["field_path"]
            coverage = dist["coverage_ratio"]
            covered_count = dist.get("covered_entity_count",
                                       int(dist["total_entity_count"] * coverage))
            total = dist["total_entity_count"]
            top1 = dist["top1_ratio"]
            top3 = dist["top3_ratio"]

            # Layered sample-size classification
            if covered_count < observable_min:
                # Too few covered entities to observe
                normal_status = "normal_sparse_or_low_coverage"
            elif covered_count < referenceable_min:
                # Observable frequency but not enough for reference
                normal_status = "normal_observable"
            elif covered_count < strong_min:
                # Referenceable but not enough for strong low-entropy
                normal_status = "normal_referenceable"
            else:
                # covered_count >= strong_min: apply strong low-entropy rules
                if coverage < min_coverage_for_strong:
                    normal_status = "normal_sparse_or_low_coverage"
                elif top1 >= top1_thresh:
                    normal_status = "normal_low_entropy"
                elif top3 >= top3_thresh:
                    normal_status = "normal_low_entropy"
                elif top1 >= 0.5:
                    normal_status = "normal_popular"
                else:
                    normal_status = "normal_not_popular_in_sample"

            entry = {
                "source_name": dist.get("source_name", self.source_id),
                "field_path": fp,
                "field_value_norm": f"{fp}=TOP1",
                "profile_grain": "field_value",
                "normal_status": normal_status,
                "top1_ratio": round(top1, 4) if top1 is not None else 0.0,
                "top3_ratio": round(top3, 4) if top3 is not None else 0.0,
                "coverage_ratio": round(coverage, 4),
                "covered_count": covered_count,
                "sample_entity_count": total,
                "rule_source": rule["rule_source"],
            }
            self.low_entropy_profiles.append(entry)

    def run_full_profile(self, field_contract):
        """Run full profile on this source based on field contract."""
        for field in field_contract.get("ordinary_columns", []):
            self.profile_ordinary_column(field["name"], field["name"])

        for field in field_contract.get("json_string_fields", []):
            unwrap = field.get("unwrap_arrays", False)
            # passport params needs array unwrapping
            if field["name"] == "params":
                unwrap = True
            self.profile_json_field(field["name"], field["name"], unwrap_arrays=unwrap)

        for field in field_contract.get("array_fields", []):
            self.profile_array_field(field["name"], field["name"])

        # High cardinality IDs that are ordinary columns
        for field in field_contract.get("high_cardinality_id_fields", []):
            col = self._get_col(field["name"])
            if col and col in self.df.columns:
                # Already handled in profile_ordinary_column if it was listed there
                # Check if it's already in inventory
                fp = f"{self.source_id}.{field['name']}"
                if not any(e["field_path"] == fp for e in self.field_inventory):
                    self.profile_ordinary_column(field["name"], field["name"])

        self.compute_low_entropy_profiles()


# ==============================================================================
# Excel loading
# ==============================================================================

def find_excel_file(input_dir, source_id):
    """Find the Excel file for a given source_id in input_dir."""
    pattern = EXCEL_FILE_MAP.get(source_id, source_id)
    for f in os.listdir(input_dir):
        if f.endswith(".xlsx") and pattern in f:
            return os.path.join(input_dir, f)
    return None


def load_excel_source(input_dir, source_id):
    """Load an Excel file and return a DataFrame with cleaned column names."""
    path = find_excel_file(input_dir, source_id)
    if path is None:
        return None, None

    # Try different sheet name conventions
    xl = pd.ExcelFile(path)
    sheet_names = xl.sheet_names
    # Prefer lowercase "sheet1" or default Sheet1
    target_sheet = None
    for s in sheet_names:
        if s.lower() == "sheet1":
            target_sheet = s
            break
    if target_sheet is None and sheet_names:
        target_sheet = sheet_names[0]
    if target_sheet is None:
        return None, None

    df = pd.read_excel(path, sheet_name=target_sheet)

    # Determine column prefix
    columns = list(df.columns)
    if columns and "." in columns[0]:
        prefix = columns[0].split(".")[0]
        # Check if all columns share the same prefix
        if all(c.startswith(prefix + ".") for c in columns):
            # Strip prefix for easier access
            clean_cols = {c: c.split(".", 1)[1] for c in columns}
            df_clean = df.rename(columns=clean_cols)
            return df_clean, prefix
    return df, None


# ==============================================================================
# Contract loading
# ==============================================================================

def load_contract(contract_path):
    """Load profiler_input_contract from YAML file.

    This is the primary path for the CLI and production usage.
    The YAML file must exist and be valid; no silent fallback to hardcoded data.

    Raises:
        FileNotFoundError: If contract_path does not exist.
        ValueError: If YAML parsing fails or required structure is missing.
    """
    if not os.path.exists(contract_path):
        raise FileNotFoundError(
            f"profiler_input_contract YAML not found: {contract_path}\n"
            f"Please provide a valid --contract path pointing to the contract YAML file.\n"
            f"For testing without a YAML file, use load_builtin_test_contract() instead."
        )

    try:
        import yaml
    except ImportError:
        raise ImportError(
            "PyYAML is required to parse the contract YAML file.\n"
            "Install it with: pip install pyyaml"
        )

    with open(contract_path, "r") as f:
        raw = yaml.safe_load(f)

    if raw is None:
        raise ValueError(
            f"Contract YAML is empty or could not be parsed: {contract_path}"
        )

    # Extract the source_inputs section from the contract YAML
    contract = {}
    if "profiler_input_contract" in raw and "source_inputs" in raw["profiler_input_contract"]:
        for source_id, source_data in raw["profiler_input_contract"]["source_inputs"].items():
            fc_raw = source_data.get("field_contract", {})
            contract[source_id] = {
                "source_id": source_id,
                "field_contract": _normalize_field_contract(fc_raw),
            }
    else:
        raise ValueError(
            f"Contract YAML missing required structure: "
            f"profiler_input_contract.source_inputs\n"
            f"Found keys: {list(raw.keys())}\n"
            f"File: {contract_path}"
        )

    # Validate required sources exist
    required_sources = ["infra_user_action_log", "passport_action_log",
                        "weapon_android", "weapon_ios"]
    missing = [s for s in required_sources if s not in contract]
    if missing:
        raise ValueError(
            f"Contract YAML missing required sources: {missing}\n"
            f"Available sources: {list(contract.keys())}\n"
            f"File: {contract_path}"
        )

    return contract


def _normalize_field_contract(fc_raw):
    """Normalize field_contract YAML into the structure expected by SourceProfiler.

    YAML uses snake_case lists; this converts them to the expected format.
    """
    result = {
        "ordinary_columns": [],
        "json_string_fields": [],
        "high_cardinality_id_fields": [],
        "array_fields": [],
    }

    for field in fc_raw.get("ordinary_columns", []):
        result["ordinary_columns"].append({
            "name": field["name"],
            "action": field.get("action", "direct_profile"),
        })

    for field in fc_raw.get("json_string_fields", []):
        entry = {
            "name": field["name"],
            "action": field.get("action", "json_parse"),
        }
        if "unwrap_arrays" in field:
            entry["unwrap_arrays"] = field["unwrap_arrays"]
        # passport params needs array unwrapping by default
        if field["name"] == "params":
            entry["unwrap_arrays"] = True
        result["json_string_fields"].append(entry)

    for field in fc_raw.get("high_cardinality_id_fields", []):
        result["high_cardinality_id_fields"].append({
            "name": field["name"],
            "action": field.get("action", "high_cardinality_summary"),
        })

    for field in fc_raw.get("array_fields", []):
        result["array_fields"].append({
            "name": field["name"],
            "action": field.get("action", "array_normalize"),
        })

    return result


def load_builtin_test_contract():
    """Load a hardcoded contract for unit testing only.

    This is NOT the default path for CLI usage.
    The CLI always uses load_contract() with a YAML file path.
    This function is only for pytest fixtures that test without a YAML file.

    The contract structure mirrors profiler_input_contract_20260609_v0_1.yaml.
    """
    contract = {
        "infra_user_action_log": {
            "source_id": "infra_user_action_log",
            "field_contract": {
                "ordinary_columns": [
                    {"name": "server_ip", "action": "direct_profile"},
                    {"name": "action_type", "action": "direct_profile"},
                    {"name": "app_type", "action": "direct_profile"},
                    {"name": "result", "action": "direct_profile"},
                    {"name": "user_agent", "action": "direct_profile"},
                    {"name": "uri", "action": "direct_profile"},
                    {"name": "reason", "action": "direct_profile"},
                    {"name": "app_ver", "action": "direct_profile"},
                    {"name": "sid", "action": "direct_profile"},
                    {"name": "token_id", "action": "direct_profile"},
                    {"name": "exception_detail", "action": "direct_profile"},
                    {"name": "sys", "action": "direct_profile"},
                    {"name": "mod", "action": "direct_profile"},
                    {"name": "channel", "action": "direct_profile"},
                ],
                "json_string_fields": [
                    {"name": "extra", "action": "json_parse"},
                ],
                "high_cardinality_id_fields": [
                    {"name": "user_id", "action": "high_cardinality_summary"},
                    {"name": "user_ip", "action": "high_cardinality_summary"},
                    {"name": "did", "action": "high_cardinality_summary"},
                    {"name": "user_ip_v6", "action": "high_cardinality_summary"},
                    {"name": "account_identifier_md5", "action": "high_cardinality_summary"},
                ],
                "array_fields": [],
            },
        },
        "passport_action_log": {
            "source_id": "passport_action_log",
            "field_contract": {
                "ordinary_columns": [
                    {"name": "uri", "action": "direct_profile"},
                    {"name": "status", "action": "direct_profile"},
                    {"name": "sys_ver", "action": "direct_profile"},
                    {"name": "app_ver", "action": "direct_profile"},
                    {"name": "phone_mod", "action": "direct_profile"},
                    {"name": "server_ip", "action": "direct_profile"},
                ],
                "json_string_fields": [
                    {"name": "params", "action": "json_parse", "unwrap_arrays": True},
                    {"name": "extra", "action": "json_parse"},
                ],
                "high_cardinality_id_fields": [
                    {"name": "user_id", "action": "high_cardinality_summary"},
                    {"name": "device_id", "action": "high_cardinality_summary"},
                    {"name": "user_ip", "action": "high_cardinality_summary"},
                    {"name": "user_ipv6", "action": "high_cardinality_summary"},
                ],
                "array_fields": [],
            },
        },
        "weapon_android": {
            "source_id": "weapon_android",
            "field_contract": {
                "ordinary_columns": [
                    {"name": "product", "action": "direct_profile"},
                    {"name": "sdk_version", "action": "direct_profile"},
                    {"name": "app_version", "action": "direct_profile"},
                ],
                "json_string_fields": [
                    {"name": "raw_data", "action": "json_parse"},
                ],
                "high_cardinality_id_fields": [
                    {"name": "deviceid", "action": "high_cardinality_summary"},
                    {"name": "user_id", "action": "high_cardinality_summary"},
                ],
                "array_fields": [
                    {"name": "weapon_one_risk", "action": "array_normalize"},
                ],
            },
        },
        "weapon_ios": {
            "source_id": "weapon_ios",
            "field_contract": {
                "ordinary_columns": [
                    {"name": "product", "action": "direct_profile"},
                    {"name": "sdk_version", "action": "direct_profile"},
                    {"name": "app_version", "action": "direct_profile"},
                ],
                "json_string_fields": [
                    {"name": "raw_data", "action": "json_parse"},
                ],
                "high_cardinality_id_fields": [
                    {"name": "deviceid", "action": "high_cardinality_summary"},
                    {"name": "user_id", "action": "high_cardinality_summary"},
                ],
                "array_fields": [
                    {"name": "weapon_one_risk", "action": "array_normalize"},
                ],
            },
        },
    }
    return contract


# ==============================================================================
# Main profiler pipeline
# ==============================================================================

def run_profiler(input_dir, contract_path, output_dir, topn_limit):
    """Run the full profiler pipeline on all sources."""
    os.makedirs(output_dir, exist_ok=True)

    contract = load_contract(contract_path)

    all_inventory = []
    all_profiles = []
    all_discrete = []
    all_missingness = []
    all_hc_summary = []
    all_low_entropy = []
    source_results = {}

    source_ids = ["infra_user_action_log", "passport_action_log",
                  "weapon_android", "weapon_ios"]

    for sid in source_ids:
        df, prefix = load_excel_source(input_dir, sid)
        if df is None:
            print(f"  WARNING: No Excel found for {sid}, skipping")
            continue

        print(f"  Profiling {sid}: {len(df)} rows, {len(df.columns)} columns")
        profiler = SourceProfiler(sid, df, prefix, topn_limit=topn_limit,
                                  baseline_scope="population_baseline")
        fc = contract[sid]["field_contract"]
        profiler.run_full_profile(fc)

        all_inventory.extend(profiler.field_inventory)
        all_profiles.extend(profiler.field_profiles)
        all_discrete.extend(profiler.discrete_distributions)
        all_missingness.extend(profiler.missingness_profiles)
        all_hc_summary.extend(profiler.high_cardinality_summaries)
        all_low_entropy.extend(profiler.low_entropy_profiles)

        source_results[sid] = {
            "rows": len(df),
            "fields_discovered": len(profiler.field_inventory),
            "fields_profiled": len(profiler.field_profiles),
            "discrete_distributions": len(profiler.discrete_distributions),
            "missingness_profiles": len(profiler.missingness_profiles),
            "high_cardinality_summaries": len(profiler.high_cardinality_summaries),
            "low_entropy_profiles": len(profiler.low_entropy_profiles),
        }

    # Metadata
    metadata = {
        "version": "v0_1",
        "profiler_tool": "normal_baseline_profiler.py",
        "profiled_at": pd.Timestamp.now().isoformat(),
        "total_fields_discovered": len(all_inventory),
        "total_fields_profiled": len(all_profiles),
        "total_discrete_fields": len(all_discrete),
        "total_high_cardinality_fields": len(all_hc_summary),
        "total_low_entropy_fields": len(all_low_entropy),
        "total_not_popular_fields": sum(
            1 for e in all_low_entropy if e["normal_status"] == "normal_not_popular_in_sample"
        ),
        "total_sparse_or_low_coverage_fields": sum(
            1 for e in all_low_entropy if e["normal_status"] == "normal_sparse_or_low_coverage"
        ),
        "total_observable_fields": sum(
            1 for e in all_low_entropy if e["normal_status"] == "normal_observable"
        ),
        "total_referenceable_fields": sum(
            1 for e in all_low_entropy if e["normal_status"] == "normal_referenceable"
        ),
        "parse_errors": 0,
        "max_json_expand_depth": MAX_JSON_DEPTH,
        "top_n_default": topn_limit,
        "baseline_scope": "population_baseline",
        "baseline_scope_detail": "population_login_or_source_baseline_from_available_offline_samples",
        "not_login_aue_specific": True,
        "sample_size_level": "initial_population_baseline",
        "frequency_observation_min_covered_count": SAMPLE_FREQUENCY_RULE["observable_min_covered_count"],
        "frequency_reference_min_covered_count": SAMPLE_FREQUENCY_RULE["referenceable_min_covered_count"],
        "strong_low_entropy_min_covered_count": SAMPLE_FREQUENCY_RULE["strong_low_entropy_min_covered_count"],
        "rule_source": SAMPLE_FREQUENCY_RULE["rule_source"],
        "not_login_aue_specific": True,
        "login_aue_condition_status": "not_mapped_in_current_infra_sample",
        "login_aue_missing_conditions": [
            "loginType",
            "_errorCode",
            "userRegisterDays",
            "userFanCnt",
        ],
        "source_grain": {
            "infra_user_action_log": "population_login_behavior_sample",
            "passport_action_log": "app_related_passport_action_sample",
            "weapon_android": "population_weapon_android_sample",
            "weapon_ios": "population_weapon_ios_sample",
        },
        "contract_source": contract_path,
        "source_results": source_results,
        "low_entropy_rule": SAMPLE_FREQUENCY_RULE,
        "boundary_declaration": [
            "不做风险判断",
            "不输出 risk_judgement",
            "不输出 feature_candidate",
            "不输出 candidate_feature_decision",
            "weapon_one_risk 只做覆盖率/TOP-N 统计不做风险定性",
            "baseline_scope = population_baseline，不是 LOGIN_AUE 精准筛选",
            "当前 baseline 是大盘背景 baseline，不是 LOGIN_AUE 正常用户精准 baseline",
            "大盘作弊率较低时，population baseline 可先用于判断字段/取值是否大盘常见",
        ],
    }

    # Write outputs
    outputs = {
        "normal_field_inventory.json": all_inventory,
        "normal_field_profile_sample.json": all_profiles,
        "normal_discrete_field_distribution.json": all_discrete,
        "normal_field_missingness_profile.json": all_missingness,
        "normal_low_entropy_profile.json": all_low_entropy,
        "high_cardinality_summary.json": all_hc_summary,
        "profiler_metadata.json": metadata,
    }

    for fname, data in outputs.items():
        fpath = os.path.join(output_dir, fname)
        with open(fpath, "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        print(f"  Written {fpath}: {len(data)} entries")

    return metadata


# ==============================================================================
# CLI entry point
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(description="normal_baseline local profiler v0.1")
    parser.add_argument("--input-dir", required=True,
                        help="Path to directory containing input Excel files")
    parser.add_argument("--contract", required=True,
                        help="Path to profiler_input_contract YAML")
    parser.add_argument("--output-dir", required=True,
                        help="Path to output directory for profiler results")
    parser.add_argument("--topn-limit", type=int, default=TOP_N_DEFAULT,
                        help="TOP-N limit for discrete distributions (default: 20)")
    args = parser.parse_args()

    print(f"normal_baseline profiler v0.1")
    print(f"  input_dir: {args.input_dir}")
    print(f"  contract: {args.contract}")
    print(f"  output_dir: {args.output_dir}")
    print(f"  topn_limit: {args.topn_limit}")

    metadata = run_profiler(args.input_dir, args.contract, args.output_dir, args.topn_limit)

    print(f"\nProfiling complete!")
    print(f"  Total fields discovered: {metadata['total_fields_discovered']}")
    print(f"  Total fields profiled: {metadata['total_fields_profiled']}")
    print(f"  Total discrete distributions: {metadata['total_discrete_fields']}")
    print(f"  Total HC summaries: {metadata['total_high_cardinality_fields']}")
    print(f"  Total low entropy profiles: {metadata['total_low_entropy_fields']}")
    for sid, result in metadata["source_results"].items():
        print(f"  {sid}: {result['rows']} rows, {result['fields_discovered']} fields discovered")


if __name__ == "__main__":
    main()