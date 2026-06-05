#!/usr/bin/env python3
"""Static and fixture checks for Dennis interface orchestration contracts.

This checker is intentionally offline-only. It does not start the
browser-backed service, call platforms, call DataAgent/Hive, or execute live
sources.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

CONTRACT_FILE = ROOT / "computer_use_poc" / "interface_orchestration_contract_v1.md"
SOURCE_PLAN_FILE = ROOT / "computer_use_poc" / "source_orchestration_plan_v1.yaml"
ANSWER_TEMPLATE_FILE = ROOT / "computer_use_poc" / "answer_experience_templates.md"
VALIDATION_FILE = ROOT / "computer_use_poc" / "runtime_validation_cases_v1.yaml"
SMOKE_FILE = ROOT / "computer_use_poc" / "smoke_tests.md"
ANSWER_FIXTURE = ROOT / "computer_use_poc" / "test_fixtures" / "interface_orchestration_mock_answer_render_v1.json"

CHECK_FILES = [
    CONTRACT_FILE,
    SOURCE_PLAN_FILE,
    ANSWER_TEMPLATE_FILE,
    VALIDATION_FILE,
    SMOKE_FILE,
]

LAYERS = [
    "input_route_layer",
    "base_summary_layer",
    "anchor_drilldown_layer",
    "cross_domain_commonality_layer",
    "validation_layer",
    "judgement_output_layer",
]

LAYER_REQUIRED_FIELDS = [
    "purpose",
    "input",
    "allowed_interface_roles",
    "output_artifacts",
    "stop_condition",
    "forbidden_behavior",
]

REQUIRED_KEYWORDS = [
    *LAYERS,
    "candidate_anchor_pool",
    "new_anchor_pool",
    "relation_expansion_result",
    "commonality_matrix",
    "group_profile_candidate",
    "candidate_features",
    "signal_inputs",
    "hypothesis_inputs",
    "expert_risk_signal_input",
    "stop_reason",
    "skipped_missing_anchor",
    "skipped_by_cap",
    "missing_contract",
    "enforcement_domain",
    "feedback_domain",
    "behavior_domain",
    "frontend_backend_consistency",
    "not_final_conclusion",
    "not_confirmed_as_group",
]

CANDIDATE_FEATURE_REQUIRED_FIELDS = [
    "feature_name",
    "source_domains",
    "supporting_current_evidence",
    "supporting_selected_anchors",
    "confidence",
    "validation_needed",
    "false_positive_risk",
    "not_final_conclusion",
]

GROUP_PROFILE_REQUIRED_FIELDS = [
    "representative_entities",
    "shared_domains",
    "shared_signals",
    "supporting_selected_anchors",
    "supporting_selected_batch_anchors",
    "context_selected_anchors",
    "missing_evidence",
    "confidence",
    "not_confirmed_as_group",
    "required_validation",
]

VALIDATION_PLAN_REQUIRED_FIELDS = [
    "validation_goal",
    "required_data",
    "dataagent_or_hive_required",
    "authorization_required",
    "expected_output",
    "validation_status",
]

ANSWER_SECTIONS = [
    "input_recognition",
    "base_summary",
    "candidate_anchors",
    "drilldown",
    "cross_domain_commonality",
    "relation_expansion",
    "group_profile_candidate",
    "validation",
    "judgement_output",
]

ANSWER_ARTIFACTS = [
    "base_summary_card",
    "candidate_anchor_pool",
    "drilldown_evidence_card",
    "commonality_matrix",
    "relation_expansion_result",
    "group_profile_candidate",
    "validation_plan",
    "final_evidence_card",
]

GAP_COUNTER_EVIDENCE_FORBIDDEN = {
    "no_data",
    "skipped",
    "skipped_missing_anchor",
    "skipped_by_cap",
    "timeout",
    "missing_contract",
}


def _relative(path: Path) -> str:
    return str(path.relative_to(ROOT))


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _layer_segment(source_plan_text: str, layer_id: str) -> str:
    markers = [f'"layer_id": "{layer_id}"', f"layer_id: {layer_id}", f"`{layer_id}`"]
    start = min([pos for marker in markers if (pos := source_plan_text.find(marker)) >= 0], default=-1)
    if start < 0:
        return ""
    next_positions = [
        source_plan_text.find('"layer_id": "', start + 1),
        source_plan_text.find("layer_id: ", start + 1),
    ]
    next_positions = [pos for pos in next_positions if pos > start]
    end = min(next_positions) if next_positions else len(source_plan_text)
    return source_plan_text[start:end]


def _validate_layer_fields(source_plan_text: str) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    summary: dict[str, Any] = {}
    for layer_id in LAYERS:
        segment = _layer_segment(source_plan_text, layer_id)
        missing = [field for field in LAYER_REQUIRED_FIELDS if field not in segment]
        summary[layer_id] = {
            "present": bool(segment),
            "missing_fields": missing,
        }
        if not segment:
            errors.append(f"layer_missing:{layer_id}")
        for field in missing:
            errors.append(f"layer_field_missing:{layer_id}.{field}")
    return errors, summary


def _validate_schema_text(combined_text: str) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    missing_keywords = [keyword for keyword in REQUIRED_KEYWORDS if keyword not in combined_text]
    errors.extend(f"keyword_missing:{keyword}" for keyword in missing_keywords)

    candidate_feature_missing = [
        field for field in CANDIDATE_FEATURE_REQUIRED_FIELDS
        if field not in combined_text
    ]
    if "signal_inputs" not in combined_text and "hypothesis_inputs" not in combined_text:
        candidate_feature_missing.append("signal_inputs_or_hypothesis_inputs")
    errors.extend(f"candidate_features_field_missing:{field}" for field in candidate_feature_missing)

    group_missing = [field for field in GROUP_PROFILE_REQUIRED_FIELDS if field not in combined_text]
    errors.extend(f"group_profile_candidate_field_missing:{field}" for field in group_missing)

    validation_missing = [field for field in VALIDATION_PLAN_REQUIRED_FIELDS if field not in combined_text]
    errors.extend(f"validation_plan_field_missing:{field}" for field in validation_missing)

    return errors, {
        "missing_keywords": missing_keywords,
        "candidate_features_missing_fields": candidate_feature_missing,
        "group_profile_candidate_missing_fields": group_missing,
        "validation_plan_missing_fields": validation_missing,
        "candidate_feature_primary_fields": "signal_inputs_or_hypothesis_inputs",
        "expert_risk_signal_input_status": "compatibility_alias_only",
    }


def _list_contains_expert_signal(values: Any) -> bool:
    if isinstance(values, list):
        return any(_list_contains_expert_signal(value) for value in values)
    if isinstance(values, dict):
        return any(_list_contains_expert_signal(value) for value in values.values())
    return "expert_risk_signal_input" in str(values)


def _validate_candidate_features(features: list[Any], *, prefix: str) -> list[str]:
    errors: list[str] = []
    if not features:
        return [f"{prefix}:candidate_features_empty"]
    for index, feature in enumerate(features, start=1):
        if not isinstance(feature, dict):
            errors.append(f"{prefix}:candidate_feature_{index}_not_object")
            continue
        for field in CANDIDATE_FEATURE_REQUIRED_FIELDS:
            if field not in feature:
                errors.append(f"{prefix}:candidate_feature_{index}_missing_{field}")
        if not (feature.get("signal_inputs") or feature.get("hypothesis_inputs")):
            errors.append(f"{prefix}:candidate_feature_{index}_missing_signal_or_hypothesis_inputs")
        if feature.get("not_final_conclusion") is not True:
            errors.append(f"{prefix}:candidate_feature_{index}_not_final_conclusion_not_true")
        if feature.get("validation_needed") is not True:
            errors.append(f"{prefix}:candidate_feature_{index}_validation_needed_not_true")
        if not feature.get("supporting_current_evidence"):
            errors.append(f"{prefix}:candidate_feature_{index}_missing_supporting_current_evidence")
        alias = feature.get("expert_risk_signal_input")
        if alias and "compatibility_alias" not in str(alias):
            errors.append(f"{prefix}:candidate_feature_{index}_expert_alias_boundary_missing")
    return errors


def _validate_group_profile(group: Any, *, prefix: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(group, dict):
        return [f"{prefix}:group_profile_candidate_not_object"]
    for field in GROUP_PROFILE_REQUIRED_FIELDS:
        if field not in group:
            errors.append(f"{prefix}:group_profile_candidate_missing_{field}")
    if group.get("not_confirmed_as_group") is not True:
        errors.append(f"{prefix}:group_profile_candidate_not_confirmed_as_group_not_true")
    if not group.get("shared_signals"):
        errors.append(f"{prefix}:group_profile_candidate_shared_signals_empty")
    return errors


def _validate_validation_plan(plan: Any, *, prefix: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(plan, dict):
        return [f"{prefix}:validation_plan_not_object"]
    for field in VALIDATION_PLAN_REQUIRED_FIELDS:
        if field not in plan:
            errors.append(f"{prefix}:validation_plan_missing_{field}")
    if plan.get("validation_status") not in {"planned", "pending", "not_executed"}:
        errors.append(f"{prefix}:validation_plan_status_invalid")
    return errors


def _validate_final_evidence_card(card: Any, *, prefix: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(card, dict):
        return [f"{prefix}:final_evidence_card_not_object"]
    if _list_contains_expert_signal(card.get("weak_evidence", [])):
        errors.append(f"{prefix}:expert_signal_in_weak_evidence")
    counter_text = json.dumps(card.get("counter_evidence", []), ensure_ascii=False)
    if any(term in counter_text for term in GAP_COUNTER_EVIDENCE_FORBIDDEN):
        errors.append(f"{prefix}:gap_state_in_counter_evidence")
    missing_text = json.dumps(card.get("missing_evidence", []), ensure_ascii=False)
    if "validation" not in missing_text and "gap" not in missing_text and "not_executed" not in missing_text:
        errors.append(f"{prefix}:missing_evidence_does_not_carry_gap_or_validation_boundary")
    return errors


def _validate_answer_fixture() -> tuple[list[str], dict[str, Any]]:
    if not ANSWER_FIXTURE.exists():
        return ["answer_fixture_missing"], {"fixture": _relative(ANSWER_FIXTURE), "present": False}
    data = json.loads(_read(ANSWER_FIXTURE))
    errors: list[str] = []
    sections = data.get("rendered_answer_sections", {})
    for section in ANSWER_SECTIONS:
        if not sections.get(section):
            errors.append(f"answer_section_missing:{section}")
    artifact_consumption = data.get("artifact_consumption", {})
    for artifact in ANSWER_ARTIFACTS:
        if artifact_consumption.get(artifact) is not True:
            errors.append(f"answer_artifact_not_consumed:{artifact}")
    excerpt = data.get("orchestration_artifacts_excerpt", {})
    errors.extend(_validate_candidate_features(excerpt.get("candidate_features", []), prefix="answer_fixture"))
    errors.extend(_validate_group_profile(excerpt.get("group_profile_candidate", {}), prefix="answer_fixture"))
    errors.extend(_validate_validation_plan(excerpt.get("validation_plan", {}), prefix="answer_fixture"))
    errors.extend(_validate_final_evidence_card(excerpt.get("final_evidence_card", {}), prefix="answer_fixture"))
    rendered_text = json.dumps(sections, ensure_ascii=False)
    for required_phrase in [
        "基础摘要",
        "候选锚点",
        "追踪下钻",
        "交叉共性",
        "关联扩散",
        "团伙候选",
        "补证验证",
        "研判输出",
    ]:
        if required_phrase not in rendered_text:
            errors.append(f"answer_phrase_missing:{required_phrase}")
    for boundary_phrase in [
        "不是反证",
        "不等于 confirmed_group",
        "hypothesis",
        "未完成取数",
    ]:
        if boundary_phrase not in rendered_text:
            errors.append(f"answer_boundary_phrase_missing:{boundary_phrase}")
    return errors, {
        "fixture": _relative(ANSWER_FIXTURE),
        "present": True,
        "section_count": len(sections),
        "consumed_artifacts": [name for name, consumed in artifact_consumption.items() if consumed is True],
    }


def run_check() -> dict[str, Any]:
    missing_files = [str(path.relative_to(ROOT)) for path in CHECK_FILES if not path.exists()]
    combined = "\n".join(_read(path) for path in CHECK_FILES if path.exists())
    source_plan_text = _read(SOURCE_PLAN_FILE) if SOURCE_PLAN_FILE.exists() else ""

    errors: list[str] = []
    errors.extend(f"file_missing:{path}" for path in missing_files)
    layer_errors, layer_summary = _validate_layer_fields(source_plan_text)
    schema_errors, schema_summary = _validate_schema_text(combined)
    answer_errors, answer_summary = _validate_answer_fixture()
    errors.extend(layer_errors)
    errors.extend(schema_errors)
    errors.extend(answer_errors)

    return {
        "check": "interface_orchestration_contract_check",
        "validation_pass": not errors,
        "errors": errors,
        "checked_files": [str(path.relative_to(ROOT)) for path in CHECK_FILES],
        "missing_files": missing_files,
        "keyword_count": len(REQUIRED_KEYWORDS),
        "field_check_summary": {
            "layers": layer_summary,
            "schema_text": schema_summary,
            "answer_fixture": answer_summary,
        },
        "service_called": False,
        "platform_called": False,
        "dataagent_called": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate interface orchestration contract fields and answer fixture")
    parser.add_argument("--format", choices=["json", "pretty"], default="pretty")
    args = parser.parse_args()
    result = run_check()
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"validation_pass={result['validation_pass']}")
        if result["errors"]:
            print(f"errors={','.join(result['errors'])}")
    return 0 if result["validation_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
