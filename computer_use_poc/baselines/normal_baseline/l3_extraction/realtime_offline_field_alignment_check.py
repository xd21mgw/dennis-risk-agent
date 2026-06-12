#!/usr/bin/env python3
"""Reverse-check realtime L3 fields against offline normal baseline fields.

This checker is local/offline. It does not call realtime platforms,
DataAgent, Hive, or LLM. It answers whether baseline fields for selected
offline sources are present in the current structured L3 output.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


CHECK_SOURCES = {
    "infra_user_action_log": {
        "realtime_label": "login_logs / infra_user_action_log",
        "candidate_sources": {"infra_user_action_log", "login_logs", "login_logs_search"},
    },
    "passport_action_log": {
        "realtime_label": "archives_user_analysis -> passport_action_log",
        "candidate_sources": {"passport_action_log", "archives_user_analysis"},
    },
}


def _load_json(path: str | Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _as_list(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    if isinstance(data, dict):
        for key in (
            "candidates",
            "l3_candidates",
            "structured_l3_candidates",
            "enriched_candidates",
            "l4_cards",
            "cards",
        ):
            val = data.get(key)
            if isinstance(val, list):
                return [x for x in val if isinstance(x, dict)]
        for val in data.values():
            if isinstance(val, list):
                return [x for x in val if isinstance(x, dict)]
    return []


def _field_path(item: dict[str, Any]) -> str:
    return str(
        item.get("field_path")
        or item.get("canonical_field_path")
        or item.get("realtime_field_path")
        or ""
    )


def _source_name(item: dict[str, Any]) -> str:
    source = str(item.get("source_name") or item.get("canonical_source") or "")
    if source:
        return source
    field_path = _field_path(item)
    return field_path.split(".", 1)[0] if "." in field_path else ""


def _leaf(field_path: str) -> str:
    return str(field_path or "").split(".")[-1]


def _baseline_fields(baseline_dir: Path) -> dict[str, list[str]]:
    inventory = _as_list(_load_json(baseline_dir / "normal_field_inventory.json"))
    out: dict[str, list[str]] = defaultdict(list)
    for item in inventory:
        field_path = _field_path(item)
        source = str(item.get("source_name") or (field_path.split(".", 1)[0] if "." in field_path else ""))
        if source in CHECK_SOURCES and field_path:
            out[source].append(field_path)
    return {source: sorted(set(fields)) for source, fields in out.items()}


def _candidate_fields(candidates_path: Path) -> dict[str, set[str]]:
    candidates = _as_list(_load_json(candidates_path))
    out: dict[str, set[str]] = defaultdict(set)
    for item in candidates:
        field_path = _field_path(item)
        source = _source_name(item)
        if field_path:
            out[source].add(field_path)
    return out


def build_alignment_check(baseline_dir: str | Path, l3_candidates_path: str | Path) -> dict[str, Any]:
    baseline_dir = Path(baseline_dir)
    l3_candidates_path = Path(l3_candidates_path)
    baseline = _baseline_fields(baseline_dir)
    realtime = _candidate_fields(l3_candidates_path)

    source_reports = {}
    for source, config in CHECK_SOURCES.items():
        baseline_fields = baseline.get(source, [])
        realtime_fields = set()
        for candidate_source in config["candidate_sources"]:
            realtime_fields |= realtime.get(candidate_source, set())

        leaf_index: dict[str, list[str]] = defaultdict(list)
        for field_path in realtime_fields:
            leaf_index[_leaf(field_path)].append(field_path)

        mapped = []
        mapping_uncertain = []
        missing = []
        if not realtime_fields:
            source_missing = baseline_fields
        else:
            source_missing = []
            for field_path in baseline_fields:
                if field_path in realtime_fields:
                    mapped.append({
                        "offline_field_path": field_path,
                        "realtime_field_path": field_path,
                        "match_type": "exact_canonical_path",
                    })
                    continue
                leaf_matches = sorted(set(leaf_index.get(_leaf(field_path), [])))
                if leaf_matches:
                    mapping_uncertain.append({
                        "offline_field_path": field_path,
                        "candidate_realtime_field_paths": leaf_matches[:10],
                        "match_type": "same_leaf_needs_review",
                    })
                else:
                    missing.append(field_path)

        denominator = len(baseline_fields)
        source_reports[source] = {
            "realtime_label": config["realtime_label"],
            "baseline_field_count": denominator,
            "realtime_candidate_field_count": len(realtime_fields),
            "mapped_count": len(mapped),
            "mapping_uncertain_count": len(mapping_uncertain),
            "missing_count": len(missing),
            "source_missing_count": len(source_missing),
            "mapped_ratio": round(len(mapped) / denominator, 4) if denominator else 0.0,
            "mapped": mapped,
            "mapping_uncertain": mapping_uncertain,
            "missing": missing,
            "source_missing": source_missing,
        }

    return {
        "checker": "realtime_offline_field_alignment_check",
        "baseline_dir": str(baseline_dir),
        "l3_candidates_path": str(l3_candidates_path),
        "sources": source_reports,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Realtime Offline Field Alignment Check",
        "",
        f"- baseline_dir: `{report['baseline_dir']}`",
        f"- l3_candidates_path: `{report['l3_candidates_path']}`",
        "",
        "## Summary",
        "",
        "| offline_source | realtime_label | baseline_fields | realtime_fields | mapped | mapping_uncertain | missing | source_missing | mapped_ratio |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for source, item in report["sources"].items():
        lines.append(
            f"| {source} | {item['realtime_label']} | {item['baseline_field_count']} | "
            f"{item['realtime_candidate_field_count']} | {item['mapped_count']} | "
            f"{item['mapping_uncertain_count']} | {item['missing_count']} | "
            f"{item['source_missing_count']} | {item['mapped_ratio']:.4f} |"
        )

    for source, item in report["sources"].items():
        lines.extend([
            "",
            f"## {source}",
            "",
            "### Mapped Sample",
            "",
            "| offline_field_path | realtime_field_path | match_type |",
            "|---|---|---|",
        ])
        for row in item["mapped"][:40]:
            lines.append(
                f"| {row['offline_field_path']} | {row['realtime_field_path']} | {row['match_type']} |"
            )
        if not item["mapped"]:
            lines.append("| - | - | - |")

        lines.extend([
            "",
            "### Mapping Uncertain Sample",
            "",
            "| offline_field_path | candidate_realtime_field_paths | match_type |",
            "|---|---|---|",
        ])
        for row in item["mapping_uncertain"][:40]:
            candidates = "<br>".join(row["candidate_realtime_field_paths"])
            lines.append(f"| {row['offline_field_path']} | {candidates} | {row['match_type']} |")
        if not item["mapping_uncertain"]:
            lines.append("| - | - | - |")

        lines.extend([
            "",
            "### Missing Sample",
            "",
            "| offline_field_path |",
            "|---|",
        ])
        for field_path in item["missing"][:60]:
            lines.append(f"| {field_path} |")
        if not item["missing"]:
            lines.append("| - |")

    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Reverse-check L3 realtime fields against offline baseline fields")
    parser.add_argument("--baseline-dir", required=True)
    parser.add_argument("--l3-candidates", required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-md", required=True)
    args = parser.parse_args()

    report = build_alignment_check(args.baseline_dir, args.l3_candidates)
    out_json = Path(args.output_json)
    out_md = Path(args.output_md)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    out_md.write_text(render_markdown(report), encoding="utf-8")

    for source, item in report["sources"].items():
        print(
            f"{source}: baseline={item['baseline_field_count']} realtime={item['realtime_candidate_field_count']} "
            f"mapped={item['mapped_count']} uncertain={item['mapping_uncertain_count']} "
            f"missing={item['missing_count']} source_missing={item['source_missing_count']}"
        )
    print(f"wrote {out_json}")
    print(f"wrote {out_md}")


if __name__ == "__main__":
    main()
