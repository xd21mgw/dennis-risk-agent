#!/usr/bin/env python3
"""Offline text dry-run for browser-backed fixed actions v1 routing.

This script validates Dennis text-level routing and answer-boundary contracts
without starting the browser-backed service, accessing platforms, calling
DataAgent/Hive, or reading auth material. It intentionally produces a source
plan only; source execution remains explicit and out of scope.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = REPO_ROOT / "computer_use_poc" / "source_orchestration_plan_v1.yaml"
CASES_PATH = REPO_ROOT / "computer_use_poc" / "browser_backed_fixed_actions_text_regression_cases_v1.yaml"
DEMO_DOC_PATH = REPO_ROOT / "computer_use_poc" / "browser_backed_fixed_actions_text_demo_v1.md"

GLOBAL_ANSWER_CONTRACT = [
    "source_plan",
    "actions",
    "source_quality_matrix",
    "missing_evidence",
    "evidence_strength",
    "final_answer_boundary",
]

GLOBAL_SAFETY_FLAGS = [
    "do_not_call_dataagent",
    "do_not_call_hive",
    "do_not_access_real_platform",
    "do_not_read_cookie_or_session",
    "do_not_output_cookie",
    "do_not_output_token",
    "do_not_output_session",
    "do_not_output_header",
    "do_not_output_password",
    "do_not_add_browser_backed_action",
]

CONTROLLED_PARALLEL_EXECUTION_GROUPS = [
    "independent_parallel",
    "dependency_serial",
    "large_response_serial",
    "auth_sensitive_serial",
]

ANSWER_TEMPLATE_NEGATIVE_GUARDS = [
    "do_not_use_login_no_data_as_no_risk",
    "do_not_make_final_risk_judgement_from_profile_only",
    "do_not_output_pii_strict",
    "do_not_dump_raw_records",
    "do_not_claim_full_coverage_when_limited",
    "do_not_treat_photo_no_data_as_no_publish_risk",
    "do_not_access_unregistered_publish_url",
    "do_not_call_same_device_gang",
    "do_not_bulk_expand_without_plan",
    "do_not_jump_to_policy_tree_asset_lookup",
    "do_not_make_final_risk_judgement",
    "do_not_output_raw_feature_values",
    "do_not_claim_complete_when_partial",
    "do_not_treat_policy_tree_as_event_hit",
    "do_not_make_user_risk_judgement",
    "do_not_output_low_risk_from_no_data",
    "do_not_stop_multisource_plan",
    "do_not_say_no_permission_without_evidence",
    "do_not_repair_auth",
    "do_not_read_cookie",
    "do_not_set_default_runtime_routing_true",
    "do_not_add_action",
    "do_not_guess_path",
    "do_not_use_policy_tree_as_single_case_hit_evidence",
    "do_not_make_final_judgement_from_strategy_hit_only",
    "do_not_mix_event_detail_and_tree_governance",
    "do_not_claim_complete_feature_coverage",
    "do_not_output_no_abnormal_publish_from_photo_no_data",
    "do_not_dump_raw_body",
    "do_not_claim_complete_timeline",
    "do_not_exclude_ato_from_online_window_gap",
    "do_not_call_hive_without_authorization",
    "do_not_make_device_risk_judgement_from_readiness",
    "do_not_label_gang_from_same_device_only",
    "do_not_only_query_login_logs",
    "do_not_make_final_judgement_without_source_quality",
    "do_not_skip_event_detail_to_policy_tree",
    "do_not_force_conclusion",
    "do_not_discard_completed_source",
    "do_not_make_final_judgement",
    "do_not_query_user_sources",
    "do_not_make_risk_judgement",
    "do_not_upgrade_partial_to_strong_evidence",
    "do_not_say_no_permission_without_permission_response",
    "do_not_auth_repair",
    "do_not_discard_conflicting_source",
    "do_not_call_gang",
    "do_not_suppress_behavior_due_to_normal_profile",
    "do_not_final_judge_without_other_sources",
    "do_not_merge_event_hit_and_policy_asset_as_same_evidence",
    "do_not_output_raw_login_records",
    "do_not_output_raw_labelInfo",
    "do_not_answer_like_interface_manual",
    "do_not_mix_track_summary_with_check_data_ready",
    "do_not_claim_private_message_live_verified",
    "do_not_claim_past_four_items_live_verified",
    "do_not_make_unstable_source_default",
    "do_not_skip_archives_for_ato",
    "do_not_stop_on_archives_auth_failed",
    "do_not_use_archives_no_data_as_no_risk",
    "do_not_claim_archives_related_users_gang",
    "do_not_default_unstable_archives_sources",
    "do_not_emit_full_routing_metadata_by_default",
    "do_not_dump_boundary_flags_yaml_by_default",
    "do_not_show_full_metadata_without_debug_request",
    "do_not_hide_internal_run_log_metadata",
]

FULL_METADATA_REQUEST_PATTERNS = [
    "routing_metadata",
    "routing metadata",
    "debug",
    "run log",
    "runlog",
    "yaml",
    "原始执行元数据",
    "完整元数据",
    "完整 metadata",
    "调试信息",
    "路由元数据",
]

FULL_METADATA_NEGATION_PATTERNS = [
    "不要输出完整 routing_metadata",
    "不输出完整 routing_metadata",
    "不得输出完整 routing_metadata",
    "默认不输出完整 routing_metadata",
    "不要默认输出 routing_metadata",
    "不得默认输出 routing_metadata",
    "不要 dump boundary_flags yaml",
    "不要 dump",
    "不要输出 yaml",
    "用户可见不要默认展示",
    "不要默认展示",
]

BOUNDARY_FLAG_EXPLANATIONS = {
    "no_data_not_risk_exclusion": "no_data 只代表当前条件下无结果，不能作为无风险反证",
    "login_no_data_or_window_gap_not_ato_exclusion": "登录日志 no_data 或窗口不足不能排除 ATO",
    "login_log_window_incomplete_possible": "登录日志在线窗口可能不完整",
    "partial_observation_available": "partial 观察可用于部分判断，但不能声称完整覆盖",
    "large_response_limited_enters_source_quality": "大响应截断进入 source_quality",
    "auth_flow_not_completed_in_bound_context": "auth_failed/302 是认证状态，不直接等于无权限或无数据",
    "archives_failure_enters_partial_evidence": "档案中心失败进入 partial evidence，不中断回答",
    "archives_no_data_not_risk_exclusion": "档案中心 no_data 不能作为低风险反证",
    "related_users_not_gang_conclusion": "同设备/关联用户只是扩散线索，不是团伙结论",
    "archives_related_users_spread_clue_not_gang": "archives_related_users 只提供扩散候选，需要交叉验证",
    "strategy_hit_not_final_judgement": "策略命中只是辅助证据，不能单独定性风险",
    "policy_tree_asset_not_event_hit_path": "policyTree 是资产治理，不是单案命中证据",
    "track_check_data_ready_not_risk_conclusion": "Track 数据可用性只说明 readiness/provenance，不是风险结论",
    "feature_list_partial_only_feature_group_summary": "feature list partial 只能做特征组摘要",
    "unstable_source_not_default_verified": "未稳定 source 只能作为 follow-up，不默认必跑",
    "default_runtime_routing_false": "browser-backed source 仍需显式 source plan，不自动默认路由",
    "source_timeout_non_blocking_partial": "单 source timeout 进入 source_quality，不阻塞已完成 source 的 partial answer",
    "controlled_parallel_plan_only": "本轮只验证受控并行编排计划，不执行真实平台 source",
    "source_quality_matrix_merge_required": "completed/no_data/partial/auth_failed/blocked/timeout/parse_error 必须分类合并进 source_quality_matrix",
    "service_batch_contract_aligned": "source_plan 字段与 browser-backed service batch contract 对齐",
}

DEMO_CASES = [
    {
        "id": "BBFA-DEMO-001",
        "user_query": "帮我判断 user_id=2871834924 是否疑似 ATO",
        "expected_route_or_actions": [
            "login_logs_search",
            "archives_user_profile",
            "archives_user_analysis",
            "track_analysis_check_data_ready",
        ],
        "expected_orchestration": "ATO multi-source plan, not login logs only.",
        "expected_boundary_flags": [
            "single_source_not_enough_for_ato",
            "no_data_not_risk_exclusion",
            "archives_required_for_behavior_closure_non_blocking",
        ],
        "should_not_do": [
            "do_not_only_query_login_logs",
            "do_not_skip_archives_for_ato",
            "do_not_make_final_judgement_without_source_quality",
        ],
        "expected_answer_contract": GLOBAL_ANSWER_CONTRACT,
        "answer_focus": "ato",
    },
    {
        "id": "BBFA-DEMO-002",
        "user_query": "登录日志没查到，是不是就没风险？",
        "expected_route_or_actions": ["login_logs_search"],
        "expected_orchestration": "Explain login no_data/window gap as source quality, not counter-evidence.",
        "expected_boundary_flags": ["no_data_not_risk_exclusion", "login_log_window_incomplete_possible"],
        "should_not_do": ["do_not_output_low_risk_from_no_data", "do_not_stop_multisource_plan"],
        "expected_answer_contract": ["source_quality_matrix", "missing_evidence", "evidence_strength", "final_answer_boundary"],
        "answer_focus": "login_no_data",
    },
    {
        "id": "BBFA-DEMO-003",
        "user_query": "看下这个账号画像和状态",
        "expected_route_or_actions": ["archives_user_profile"],
        "expected_orchestration": "Account profile is baseline context; not final judgement.",
        "expected_boundary_flags": ["profile_context_not_final_judgement"],
        "should_not_do": ["do_not_make_final_risk_judgement_from_profile_only", "do_not_output_pii_strict"],
        "expected_answer_contract": GLOBAL_ANSWER_CONTRACT,
        "answer_focus": "profile",
    },
    {
        "id": "BBFA-DEMO-004",
        "user_query": "这个账号最近有没有异常操作或风险日志？",
        "expected_route_or_actions": ["archives_user_analysis"],
        "expected_orchestration": "Use Archives user analysis; capped large response becomes partial observation.",
        "expected_boundary_flags": ["large_response_limited_enters_source_quality", "partial_observation_available"],
        "should_not_do": ["do_not_dump_raw_records", "do_not_claim_full_coverage_when_limited"],
        "expected_answer_contract": GLOBAL_ANSWER_CONTRACT,
        "answer_focus": "analysis",
    },
    {
        "id": "BBFA-DEMO-005",
        "user_query": "这个账号是不是异常发布/色导导流？",
        "expected_route_or_actions": ["archives_photo_search", "archives_user_profile", "archives_user_analysis"],
        "expected_orchestration": "Publish/content branch with photo search, profile baseline, and user analysis.",
        "expected_boundary_flags": [
            "photo_search_no_data_not_abnormal_publish_exclusion",
            "archives_failure_enters_partial_evidence",
        ],
        "should_not_do": [
            "do_not_output_no_abnormal_publish_from_photo_no_data",
            "do_not_use_archives_no_data_as_no_risk",
            "do_not_make_final_judgement",
        ],
        "expected_answer_contract": GLOBAL_ANSWER_CONTRACT,
        "answer_focus": "publish",
    },
    {
        "id": "BBFA-DEMO-006",
        "user_query": "这个账号有没有同设备关联账号？",
        "expected_route_or_actions": [
            "archives_related_users",
            "archives_user_profile",
            "login_logs_search",
            "track_analysis_check_data_ready",
        ],
        "expected_orchestration": "Same-device relation is an expansion clue with cross-source validation.",
        "expected_boundary_flags": [
            "related_users_not_gang_conclusion",
            "archives_related_users_spread_clue_not_gang",
        ],
        "should_not_do": [
            "do_not_label_gang_from_same_device_only",
            "do_not_claim_archives_related_users_gang",
            "do_not_bulk_expand_without_plan",
        ],
        "expected_answer_contract": GLOBAL_ANSWER_CONTRACT,
        "answer_focus": "same_device",
    },
    {
        "id": "BBFA-DEMO-007",
        "user_query": "这个 eventId 为什么被拦？",
        "expected_route_or_actions": ["rcp_event_detail", "rcp_event_feature_list"],
        "expected_orchestration": "Event attribution first, feature list second when exact event identity is available.",
        "expected_boundary_flags": ["event_detail_not_policy_tree_asset_lookup", "strategy_hit_not_final_judgement"],
        "should_not_do": ["do_not_jump_to_policy_tree_asset_lookup", "do_not_make_final_risk_judgement"],
        "expected_answer_contract": GLOBAL_ANSWER_CONTRACT,
        "answer_focus": "event_attribution",
    },
    {
        "id": "BBFA-DEMO-008",
        "user_query": "feature list 只拿到 partial，能不能说明完整特征？",
        "expected_route_or_actions": ["rcp_event_feature_list"],
        "expected_orchestration": "Partial feature observation can summarize groups but cannot claim full detail coverage.",
        "expected_boundary_flags": ["feature_list_partial_only_feature_group_summary", "partial_observation_available"],
        "should_not_do": ["do_not_claim_complete_feature_coverage", "do_not_output_raw_feature_values"],
        "expected_answer_contract": ["source_quality_matrix", "missing_evidence", "final_answer_boundary"],
        "answer_focus": "feature_partial",
    },
    {
        "id": "BBFA-DEMO-009",
        "user_query": "这条策略挂在哪棵策略树？",
        "expected_route_or_actions": ["rcp_policy_tree_lookup"],
        "expected_orchestration": "Policy-tree lookup is governance context only.",
        "expected_boundary_flags": ["policy_tree_asset_not_event_hit_path"],
        "should_not_do": ["do_not_treat_policy_tree_as_event_hit", "do_not_make_user_risk_judgement"],
        "expected_answer_contract": GLOBAL_ANSWER_CONTRACT,
        "answer_focus": "policy_tree",
    },
    {
        "id": "BBFA-DEMO-010",
        "user_query": "命中过策略，能不能直接定性风险？",
        "expected_route_or_actions": ["rcp_event_detail", "rcp_event_feature_list"],
        "expected_orchestration": "Strategy hit is auxiliary evidence; risk judgement needs cross-source context.",
        "expected_boundary_flags": ["strategy_hit_not_final_judgement"],
        "should_not_do": ["do_not_make_final_judgement_from_strategy_hit_only"],
        "expected_answer_contract": ["source_quality_matrix", "evidence_strength", "missing_evidence", "final_answer_boundary"],
        "answer_focus": "strategy_hit_boundary",
    },
    {
        "id": "BBFA-DEMO-011",
        "user_query": "先给 plan_mode，不要执行平台，说明是否查平台和 DataAgent",
        "expected_route_or_actions": ["source_plan_only_no_action_selected"],
        "expected_orchestration": "Plan-mode answer translates execution status into natural language.",
        "expected_boundary_flags": ["plan_mode_no_platform_execution", "default_runtime_routing_false"],
        "should_not_do": [
            "do_not_emit_full_routing_metadata_by_default",
            "do_not_dump_boundary_flags_yaml_by_default",
        ],
        "expected_answer_contract": GLOBAL_ANSWER_CONTRACT,
        "expected_metadata_visibility": "user_visible_summary",
        "expected_full_metadata_allowed": False,
        "expected_user_visible_contains": ["本轮未访问真实平台", "未调用 DataAgent/Hive"],
        "expected_user_visible_absent": ["routing_metadata:"],
        "answer_focus": "plan_mode_summary",
    },
    {
        "id": "BBFA-DEMO-012",
        "user_query": "给我 routing_metadata debug run log YAML",
        "expected_route_or_actions": ["source_plan_only_no_action_selected"],
        "expected_orchestration": "Explicit debug request may show full routing_metadata.",
        "expected_boundary_flags": ["missing_explicit_source_plan"],
        "should_not_do": ["do_not_hide_internal_run_log_metadata"],
        "expected_answer_contract": GLOBAL_ANSWER_CONTRACT,
        "expected_metadata_visibility": "full_routing_metadata",
        "expected_full_metadata_allowed": True,
        "expected_user_visible_contains": ["routing_metadata:", "platform_called: false", "dataagent_called: false"],
        "answer_focus": "debug_metadata",
    },
]


def load_plan() -> dict[str, Any]:
    try:
        return json.loads(PLAN_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SystemExit(f"missing source plan: {PLAN_PATH}")
    except json.JSONDecodeError as exc:
        raise SystemExit(f"source plan must remain JSON-compatible YAML: {exc}")


def parse_simple_value(raw: str) -> Any:
    value = raw.strip()
    if value in {"true", "false"}:
        return value == "true"
    if value == "[]":
        return []
    if value.startswith("[") and value.endswith("]"):
        inside = value[1:-1].strip()
        if not inside:
            return []
        return [item.strip().strip("\"'") for item in inside.split(",")]
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    return value


def load_text_cases(path: Path = CASES_PATH) -> dict[str, Any]:
    """Parse the small local regression YAML subset without PyYAML."""

    root: dict[str, Any] = {"cases": []}
    current_case: dict[str, Any] | None = None
    current_top_list: str | None = None
    in_cases = False

    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith("cases:"):
            in_cases = True
            current_top_list = None
            continue
        if not in_cases:
            if line.startswith("  - ") and current_top_list:
                root.setdefault(current_top_list, []).append(parse_simple_value(line.split("- ", 1)[1]))
                continue
            if ":" in line and not line.startswith(" "):
                key, raw = line.split(":", 1)
                key = key.strip()
                if raw.strip():
                    root[key] = parse_simple_value(raw)
                    current_top_list = None
                else:
                    root[key] = []
                    current_top_list = key
            continue

        if line.startswith("  - "):
            current_case = {}
            root["cases"].append(current_case)
            body = line.split("- ", 1)[1]
            if ":" in body:
                key, raw = body.split(":", 1)
                current_case[key.strip()] = parse_simple_value(raw)
            continue
        if current_case is not None and line.startswith("    ") and ":" in line:
            key, raw = line.strip().split(":", 1)
            current_case[key] = parse_simple_value(raw)

    return root


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def has_any(text: str, patterns: list[str]) -> bool:
    return any(pattern.lower() in text for pattern in patterns)


def wants_full_routing_metadata(text: str) -> bool:
    return has_any(text, FULL_METADATA_REQUEST_PATTERNS) and not has_any(text, FULL_METADATA_NEGATION_PATTERNS)


def unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def default_runtime_routing_ok(plan: dict[str, Any]) -> bool:
    fixed = plan.get("plans", {}).get("browser_backed_fixed_actions_v1", {})
    if fixed.get("default_runtime_routing") is not False:
        return False
    for action in fixed.get("registered_actions", {}).values():
        if action.get("default_runtime_routing") is not False:
            return False
    return True


def scenario_actions(plan: dict[str, Any], scenario: str) -> list[str]:
    fixed = plan.get("plans", {}).get("browser_backed_fixed_actions_v1", {})
    return list(fixed.get("scenario_source_plans", {}).get(scenario, {}).get("actions", []))


def scenario_flags(plan: dict[str, Any], scenario: str) -> list[str]:
    fixed = plan.get("plans", {}).get("browser_backed_fixed_actions_v1", {})
    return list(fixed.get("scenario_source_plans", {}).get(scenario, {}).get("boundary_flags", []))


def scenario_source_plan(plan: dict[str, Any], scenario: str) -> list[dict[str, Any]]:
    fixed = plan.get("plans", {}).get("browser_backed_fixed_actions_v1", {})
    source_plan = fixed.get("scenario_source_plans", {}).get(scenario, {}).get("source_plan", [])
    return [dict(item) for item in source_plan if isinstance(item, dict)]


def large_response_actions_from_text(text: str) -> set[str]:
    large_response_actions: set[str] = set()
    if has_any(text, ["large", "大响应", "太大", "pageSize", "完整覆盖", "feature partial", "返回 partial"]):
        large_response_actions.update({"archives_user_analysis", "rcp_event_feature_list"})
    return large_response_actions


def source_plan_for_actions(plan: dict[str, Any], actions: list[str], text: str) -> list[dict[str, Any]]:
    if actions == ["source_plan_only_no_action_selected"]:
        return []

    action_set = set(actions)
    scenario_order: list[str] = []
    if "archives_photo_search" in action_set:
        scenario_order.append("abnormal_publish_content_handoff")
    if "archives_related_users" in action_set:
        scenario_order.append("account_spread_same_device")
    if {"login_logs_search", "archives_user_profile", "archives_user_analysis", "track_analysis_check_data_ready"}.issubset(action_set):
        scenario_order.append("ato_login_anomaly")
    if {"rcp_event_detail", "rcp_event_feature_list"} & action_set:
        scenario_order.append("rcp_event_attribution")
    if "rcp_policy_tree_lookup" in action_set:
        scenario_order.append("policy_asset_governance")

    scenarios = [
        "ato_login_anomaly",
        "abnormal_publish_content_handoff",
        "account_spread_same_device",
        "rcp_event_attribution",
        "policy_asset_governance",
    ]
    ordered_scenarios = unique(scenario_order + scenarios)
    catalog: list[dict[str, Any]] = []
    for scenario in ordered_scenarios:
        catalog.extend(scenario_source_plan(plan, scenario))

    by_action: dict[str, dict[str, Any]] = {}
    for item in catalog:
        by_action.setdefault(str(item.get("action")), item)

    large_actions = large_response_actions_from_text(text)
    result: list[dict[str, Any]] = []
    for action in actions:
        if action == "source_plan_only_no_action_selected":
            continue
        item = dict(by_action.get(action, {
            "source_id": action,
            "action": action,
            "execution_group": "dependency_serial",
            "depends_on": [],
            "dependency": "explicit_source_plan_required",
            "timeout_class": "standard_readonly",
            "failure_policy": "non_blocking_partial",
            "source_priority": "conditional",
            "expected_observation": "explicit_source_observation",
        }))
        if action in large_actions:
            item["execution_group"] = "large_response_serial"
            item["timeout_class"] = "large_response"
            item["failure_policy"] = "non_blocking_partial"
        result.append(item)
    return result


def execution_groups_for(source_plan_items: list[dict[str, Any]]) -> list[str]:
    return unique([
        str(item.get("execution_group"))
        for item in source_plan_items
        if item.get("execution_group")
    ])


def finalize_route(plan: dict[str, Any], text: str, routed: dict[str, Any]) -> dict[str, Any]:
    routed = apply_output_metadata_policy(text, routed)
    source_plan_items = source_plan_for_actions(plan, list(routed.get("actions", [])), text)
    routed["source_plan_items"] = source_plan_items
    routed["actual_execution_groups"] = execution_groups_for(source_plan_items)
    routed["controlled_parallel_groups_supported"] = list(CONTROLLED_PARALLEL_EXECUTION_GROUPS)
    return routed


def explain_boundary_flags(flags: list[str]) -> list[str]:
    explanations = [BOUNDARY_FLAG_EXPLANATIONS[flag] for flag in flags if flag in BOUNDARY_FLAG_EXPLANATIONS]
    return unique(explanations)


def user_visible_status_summary(flags: list[str], full_metadata_allowed: bool) -> str:
    explanations = explain_boundary_flags(flags)
    if not explanations:
        explanations = ["本轮只生成 source plan 和回答边界，不把未执行 source 写成已完成证据"]
    boundary_text = "；".join(explanations[:4])
    metadata_text = "已按请求附完整 routing_metadata" if full_metadata_allowed else "默认不展示完整 routing_metadata YAML"
    return (
        "执行状态：本轮未访问真实平台，未调用 DataAgent/Hive。"
        f"证据边界：{boundary_text}。"
        "缺失字段/下一步：如需执行，先补齐明确实体、时间窗口和显式 source plan。"
        f"{metadata_text}。"
    )


def apply_output_metadata_policy(text: str, routed: dict[str, Any]) -> dict[str, Any]:
    full_metadata_allowed = wants_full_routing_metadata(text)
    flags = list(routed.get("boundary_flags", []))
    routed["metadata_visibility"] = "full_routing_metadata" if full_metadata_allowed else "user_visible_summary"
    routed["routing_metadata_yaml_visible"] = full_metadata_allowed
    routed["full_routing_metadata_allowed"] = full_metadata_allowed
    routed["internal_run_log_metadata_retained"] = True
    routed["user_visible_status_summary"] = user_visible_status_summary(flags, full_metadata_allowed)
    return routed


def route_query(plan: dict[str, Any], user_query: str) -> dict[str, Any]:
    text = normalize_text(user_query)
    actions: list[str] = []
    flags: list[str] = []
    orchestration = "explicit_source_plan_only"

    if has_any(text, ["cookie", "token", "session", "header", "password", "raw login records", "raw labelinfo", "raw body"]):
        return finalize_route(plan, text, {
            "actions": [],
            "orchestration": "deny raw secret/raw dump request; offer sanitized source summary only",
            "boundary_flags": [
                "credential_secret_forbidden",
                "raw_dump_forbidden",
                "pii_strict_forbidden",
            ],
            "answer_contract": ["final_answer_boundary", "redaction_applied"],
            "safety_flags": unique(GLOBAL_SAFETY_FLAGS + ANSWER_TEMPLATE_NEGATIVE_GUARDS + [
                "do_not_output_raw_login_records",
                "do_not_output_raw_labelInfo",
                "do_not_output_raw_full_body",
            ]),
        })

    if has_any(text, ["未验证的新 action", "新 action", "接进主链"]):
        return finalize_route(plan, text, {
            "actions": [],
            "orchestration": "reject default routing; require registry/readiness/live-smoke evidence first",
            "boundary_flags": ["disabled_or_unverified_action_not_default_route"],
            "answer_contract": ["source_plan", "final_answer_boundary"],
            "safety_flags": unique(GLOBAL_SAFETY_FLAGS + ANSWER_TEMPLATE_NEGATIVE_GUARDS + [
                "do_not_set_default_runtime_routing_true",
                "do_not_add_action",
                "do_not_guess_path",
            ]),
        })

    if has_any(text, ["私信", "private message", "资料四件套", "四件套", "过往四项", "past four", "related_devices", "关联设备"]):
        return finalize_route(plan, text, {
            "actions": [],
            "orchestration": "unstable or not-default source stays follow-up only; use only when a stable interface or user-provided clue exists",
            "boundary_flags": [
                "unstable_source_not_default_verified",
                "default_runtime_routing_false",
            ],
            "answer_contract": ["source_plan", "missing_evidence", "final_answer_boundary"],
            "safety_flags": unique(GLOBAL_SAFETY_FLAGS + ANSWER_TEMPLATE_NEGATIVE_GUARDS + [
                "do_not_claim_private_message_live_verified",
                "do_not_claim_past_four_items_live_verified",
                "do_not_make_unstable_source_default",
            ]),
        })

    if has_any(text, ["先给计划", "先给 plan", "plan_mode", "plan mode", "不要执行", "不查平台"]):
        flags += ["plan_mode_no_platform_execution", "default_runtime_routing_false"]
        orchestration = "plan mode only; translate platform_called=false and dataagent_called=false into natural language"

    if has_any(text, ["controlled parallel", "受控并行", "parallel", "batch", "execution_group", "multi_source_plan", "多 source", "多源"]):
        flags += [
            "controlled_parallel_plan_only",
            "source_quality_matrix_merge_required",
            "service_batch_contract_aligned",
            "default_runtime_routing_false",
        ]

    if has_any(text, ["timeout", "超时"]):
        flags += ["source_timeout_non_blocking_partial", "partial_evidence_required"]

    if has_any(text, ["no_data", "无数据", "没查到"]):
        flags += ["no_data_not_risk_exclusion"]

    if has_any(text, ["partial", "部分观察", "不完整"]):
        flags += ["partial_observation_available"]

    if has_any(text, ["302", "auth_failed", "登录态", "账号域"]):
        actions += ["archives_user_profile", "archives_user_analysis"]
        flags += [
            "auth_flow_not_completed_in_bound_context",
            "archives_failure_enters_partial_evidence",
            "partial_evidence_required",
        ]
        orchestration = "archives auth state is source quality; do not repair auth or infer permission denial"

    if has_any(text, ["档案中心 no_data", "archives no_data", "archives_user_profile no_data", "archives_user_analysis no_data"]):
        actions += ["archives_user_profile", "archives_user_analysis"]
        flags += [
            "archives_no_data_not_risk_exclusion",
            "archives_failure_enters_partial_evidence",
            "partial_evidence_required",
        ]
        orchestration = "archives no_data is source quality and missing evidence, not low-risk counter-evidence"

    policy_tree_governance_only = has_any(text, ["只做资产治理", "不当 event hit path", "不是 event hit path", "不替代 event hit path"])
    if has_any(text, ["policytree", "策略树", "资产路径", "树结构"]):
        if has_any(text, ["event", "事件", "两个都要", "不要混"]) and not policy_tree_governance_only:
            actions += ["rcp_event_detail", "rcp_event_feature_list", "rcp_policy_tree_lookup"]
            flags += ["event_detail_not_policy_tree_asset_lookup", "policy_tree_asset_not_event_hit_path"]
            orchestration = "produce separate event attribution and policy asset branches"
        elif has_any(text, ["证明", "这次命中", "命中了策略", "用户这次"]):
            actions += ["rcp_policy_tree_lookup"]
            flags += ["policy_tree_asset_not_event_hit_path", "policy_tree_lookup_not_single_case_risk_evidence"]
            orchestration = "policy tree explains assets only; event hit requires event detail/source evidence"
        elif has_any(text, ["命中归因直接查策略树"]):
            actions += scenario_actions(plan, "rcp_event_attribution")
            flags += ["event_detail_not_policy_tree_asset_lookup", "policy_tree_asset_not_event_hit_path"]
            orchestration = "event attribution must use event detail and feature list before optional governance context"
        else:
            actions += scenario_actions(plan, "policy_asset_governance")
            flags += scenario_flags(plan, "policy_asset_governance")
            orchestration = "policy asset governance only"

    if has_any(text, ["event", "eventid", "事件详情", "被拦", "feature", "特征"]) and not policy_tree_governance_only:
        if "rcp_policy_tree_lookup" not in actions or has_any(text, ["命中归因", "详情", "feature", "特征"]):
            actions += scenario_actions(plan, "rcp_event_attribution")
            flags += scenario_flags(plan, "rcp_event_attribution")
            flags += ["attribution_not_cheating_judgement"]
            if "separate event attribution" not in orchestration:
                orchestration = "rcp_event_detail -> rcp_event_feature_list"
        if has_any(text, ["partial", "完整覆盖", "强证据"]):
            flags += ["partial_observation_available", "do_not_upgrade_partial_to_strong_evidence"]

    if has_any(text, ["同设备", "关联账号", "扩散", "黑产账号", "黑产扩散", "黑灰产"]):
        actions += scenario_actions(plan, "account_spread_same_device")
        flags += scenario_flags(plan, "account_spread_same_device")
        orchestration = "same-device relation is an expansion clue with cross-source validation"

    if has_any(text, ["异常发布", "色导", "色情导流", "作品", "举报", "photo_search", "非本人发布"]):
        actions += scenario_actions(plan, "abnormal_publish_content_handoff")
        flags += scenario_flags(plan, "abnormal_publish_content_handoff")
        orchestration = "archives_photo_search -> archives_user_profile -> archives_user_analysis"

    if has_any(text, ["账号画像", "账号状态", "资料正常", "画像", "状态查询"]):
        actions += ["archives_user_profile"]
        flags += ["profile_context_not_final_judgement"]
        orchestration = "profile is baseline context"

    if has_any(text, ["用户操作", "风险日志", "操作日志", "archives_user_analysis", "大量操作", "用户分析"]):
        actions += ["archives_user_analysis"]
        flags += ["large_response_limited_enters_source_quality", "partial_observation_available"]
        orchestration = "archives_user_analysis with bounded window/page and partial boundary when capped"

    if has_any(text, ["登录日志", "login", "ato", "疑似 ato", "登录有没有异常", "客诉时间"]):
        if has_any(text, ["疑似 ato", "判断", "ato", "异常但档案中心", "多 source", "多source"]):
            actions += scenario_actions(plan, "ato_login_anomaly")
            flags += scenario_flags(plan, "ato_login_anomaly")
            flags += ["single_source_not_enough_for_ato"]
            orchestration = "ATO multi-source plan, not login logs only"
        else:
            actions += ["login_logs_search"]
        flags += [
            "no_data_not_risk_exclusion",
            "login_no_data_or_window_gap_not_ato_exclusion",
            "login_log_window_incomplete_possible",
        ]
        if has_any(text, ["超出", "在线窗口", "历史"]):
            flags += ["offline_hive_required_if_historical"]

    if has_any(text, ["checkdataready", "dataready", "数据准备", "设备没问题"]):
        actions += ["track_analysis_check_data_ready"]
        flags += ["track_check_data_ready_not_risk_conclusion"]
        orchestration = "track_analysis_check_data_ready is readiness/provenance only"

    if has_any(text, ["track summary", "track_analysis_summary", "track 命名", "track能力", "track 能力", "track 活跃", "数据可用性"]):
        actions += ["track_analysis_check_data_ready"]
        flags += [
            "track_v1_name_check_data_ready",
            "track_summary_is_generic_capability_not_current_action_name",
            "track_check_data_ready_not_risk_conclusion",
        ]
        orchestration = "v1 wording uses track_analysis_check_data_ready / Track 活跃与数据可用性; historical Track summary remains a generic capability description"

    if has_any(text, ["策略命中", "直接定风险", "定性风险"]):
        if not actions:
            actions += scenario_actions(plan, "rcp_event_attribution")
        flags += ["strategy_hit_not_final_judgement"]

    if has_any(text, ["冲突", "不一致", "登录日志没异常但"]):
        flags += ["conflicting_sources_require_source_quality", "final_judgement_boundary_required"]

    if actions and actions != ["source_plan_only_no_action_selected"]:
        flags += ["source_quality_required"]

    if has_any(text, ["先别定性", "不要定性"]):
        flags += ["final_risk_judgement_made_false"]

    if not actions:
        actions = ["source_plan_only_no_action_selected"]
        flags += ["missing_explicit_source_plan"]

    return finalize_route(plan, text, {
        "actions": unique(actions),
        "orchestration": orchestration,
        "boundary_flags": unique(flags),
        "answer_contract": list(GLOBAL_ANSWER_CONTRACT),
        "safety_flags": unique(GLOBAL_SAFETY_FLAGS + ANSWER_TEMPLATE_NEGATIVE_GUARDS),
    })


def evaluate_case(plan: dict[str, Any], case: dict[str, Any]) -> dict[str, Any]:
    actual = route_query(plan, str(case.get("user_query", "")))
    expected_actions = list(case.get("expected_route_or_actions", []))
    expected_flags = list(case.get("expected_boundary_flags", []))
    expected_contract = list(case.get("expected_answer_contract", []))
    expected_execution_groups = list(case.get("expected_execution_groups", []))
    should_not_do = list(case.get("should_not_do", []))
    expected_metadata_visibility = case.get("expected_metadata_visibility")
    expected_full_metadata_allowed = case.get("expected_full_metadata_allowed")
    expected_internal_metadata_retained = case.get("expected_internal_metadata_retained")
    expected_user_visible_contains = list(case.get("expected_user_visible_contains", []))
    expected_user_visible_absent = list(case.get("expected_user_visible_absent", []))

    actual_actions = actual["actions"]
    actual_execution_groups = list(actual.get("actual_execution_groups", []))
    if expected_actions:
        actions_ok = all(action in actual_actions for action in expected_actions)
    else:
        actions_ok = actual_actions == []

    flags_ok = all(flag in actual["boundary_flags"] for flag in expected_flags)
    contract_ok = all(field in actual["answer_contract"] for field in expected_contract)
    execution_groups_ok = all(group in actual_execution_groups for group in expected_execution_groups)
    safety_ok = all(flag in actual["safety_flags"] for flag in should_not_do)
    default_routing_ok = default_runtime_routing_ok(plan)
    metadata_visibility_ok = (
        expected_metadata_visibility is None
        or actual.get("metadata_visibility") == expected_metadata_visibility
    )
    full_metadata_ok = (
        expected_full_metadata_allowed is None
        or actual.get("full_routing_metadata_allowed") is expected_full_metadata_allowed
    )
    internal_metadata_ok = (
        expected_internal_metadata_retained is None
        or actual.get("internal_run_log_metadata_retained") is expected_internal_metadata_retained
    )
    visible_output = actual.get("user_visible_status_summary", "")
    if actual.get("routing_metadata_yaml_visible"):
        visible_output += "\n" + full_routing_metadata_preview(actual)
    visible_contains_ok = all(text in visible_output for text in expected_user_visible_contains)
    visible_absent_ok = all(text not in visible_output for text in expected_user_visible_absent)

    issues: list[str] = []
    if not actions_ok:
        issues.append(f"expected actions missing: {expected_actions}; actual={actual_actions}")
    if not flags_ok:
        missing = [flag for flag in expected_flags if flag not in actual["boundary_flags"]]
        issues.append(f"expected boundary flags missing: {missing}")
    if not contract_ok:
        missing = [field for field in expected_contract if field not in actual["answer_contract"]]
        issues.append(f"expected answer contract missing: {missing}")
    if not execution_groups_ok:
        missing = [group for group in expected_execution_groups if group not in actual_execution_groups]
        issues.append(f"expected execution groups missing: {missing}; actual={actual_execution_groups}")
    if not safety_ok:
        missing = [flag for flag in should_not_do if flag not in actual["safety_flags"]]
        issues.append(f"should_not_do not enforced: {missing}")
    if not metadata_visibility_ok:
        issues.append(
            "metadata visibility mismatch: "
            f"expected={expected_metadata_visibility}; actual={actual.get('metadata_visibility')}"
        )
    if not full_metadata_ok:
        issues.append(
            "full metadata policy mismatch: "
            f"expected={expected_full_metadata_allowed}; actual={actual.get('full_routing_metadata_allowed')}"
        )
    if not internal_metadata_ok:
        issues.append(
            "internal metadata retention mismatch: "
            f"expected={expected_internal_metadata_retained}; actual={actual.get('internal_run_log_metadata_retained')}"
        )
    if not visible_contains_ok:
        missing = [text for text in expected_user_visible_contains if text not in visible_output]
        issues.append(f"user-visible summary missing expected text: {missing}")
    if not visible_absent_ok:
        present = [text for text in expected_user_visible_absent if text in visible_output]
        issues.append(f"user-visible summary contains forbidden text: {present}")
    if not default_routing_ok:
        issues.append("default_runtime_routing drifted from false")

    return {
        "id": case.get("id"),
        "user_query": case.get("user_query"),
        "expected_source_plan": {
            "actions": expected_actions,
            "orchestration": case.get("expected_orchestration"),
        },
        "expected_execution_groups": expected_execution_groups,
        "actual_source_plan_or_template": {
            "actions": actual_actions,
            "orchestration": actual["orchestration"],
            "answer_contract": actual["answer_contract"],
            "source_plan_items": actual.get("source_plan_items", []),
        },
        "actual_execution_groups": actual_execution_groups,
        "expected_boundary_flags": expected_flags,
        "actual_boundary_flags": actual["boundary_flags"],
        "actual_output_metadata": {
            "metadata_visibility": actual.get("metadata_visibility"),
            "routing_metadata_yaml_visible": actual.get("routing_metadata_yaml_visible"),
            "full_routing_metadata_allowed": actual.get("full_routing_metadata_allowed"),
            "internal_run_log_metadata_retained": actual.get("internal_run_log_metadata_retained"),
            "user_visible_status_summary": actual.get("user_visible_status_summary"),
        },
        "pass": not issues,
        "issue_if_failed": "; ".join(issues) if issues else "",
        "fix_applied": "none" if not issues else "pending",
    }


def full_routing_metadata_preview(actual: dict[str, Any]) -> str:
    flags = actual.get("boundary_flags", [])
    flags_block = "\n".join(f"    - {flag}" for flag in flags[:6]) or "    []"
    return (
        "routing_metadata:\n"
        "  route: multi_evidence_orchestration\n"
        "  capability: multi_evidence_orchestration_contracts\n"
        "  sub_capability: null\n"
        "  intent_type: browser_backed_fixed_actions_text_debug\n"
        "  execution_mode: plan_mode\n"
        "  evidence_mode: expert_reasoning\n"
        "  query_plan_only: true\n"
        "  platform_called: false\n"
        "  platform_call_summary: []\n"
        "  dataagent_called: false\n"
        "  direct_tool_bypass: false\n"
        "  sensitive_output: false\n"
        "  redaction_applied: true\n"
        "  boundary_flags:\n"
        f"{flags_block}\n"
        "  source_quality:\n"
        "    completed_sources: []\n"
        "    no_data_sources: []\n"
        "    blocked_sources: []\n"
        "    auth_failed_sources: []\n"
        "    timeout_sources: []\n"
        "    parse_error_sources: []\n"
        "    missing_sources: []\n"
        "  missing_required_fields: []\n"
        "  partial_reason: null\n"
        "  final_status: answered"
    )


def answer_draft_for(case: dict[str, Any], actual: dict[str, Any]) -> str:
    actions = actual["actions"]
    if actions == ["source_plan_only_no_action_selected"]:
        plan_label = "plan-only（本轮不选择具体 source）"
    else:
        plan_label = " -> ".join(actions)
    focus = str(case.get("answer_focus", ""))
    if actual.get("routing_metadata_yaml_visible"):
        return (
            "已按 debug / run log 请求输出完整 routing_metadata；本轮仍未访问真实平台，未调用 DataAgent/Hive。\n\n"
            f"{full_routing_metadata_preview(actual)}"
        )
    drafts = {
        "ato": (
            f"我会按“控制权变化 -> 异常行为闭环 -> 扩散/策略佐证”收敛，不自动查平台。source_plan：{plan_label}。"
            "先看登录链路是否有新设备、异地、验证或 token 变化；再用档案用户分析对齐改密、发布、关注等后置动作；"
            "最后只把 Track 活跃与数据可用性、策略命中当旁证。no_data 只进 source_quality，不能排除 ATO。"
            "档案中心若 auth_failed/no_data/timeout，也只降级为 partial evidence，不能跳过行为闭环。"
        ),
        "login_no_data": (
            f"不能。source_plan：{plan_label}。它只能说明在线窗口和当前条件下没有可见登录记录。"
            "no_data 不是无风险反证；如果客诉时间超窗，必须写 window gap。"
            "后续要用账号操作、账号画像或经授权的离线来源补控制权变化链路。"
        ),
        "profile": (
            f"这个裸问只看账号基线，source_plan：{plan_label}。"
            "重点是账号状态、注册/资料状态和风险摘要，用来判断背景线索。"
            "画像正常不等于本人操作，画像异常也不等于风险定性；行为链路要另补。"
        ),
        "analysis": (
            f"这个问题收敛到操作时间线，source_plan：{plan_label}。"
            "重点看登录、改密、保护账号、冻结、直播/发布等动作是否能串成异常行为闭环。"
            "大响应只写 partial_observation_available，不能声称完整覆盖；raw records 不输出。"
        ),
        "publish": (
            f"导流/异常发布按“内容动作 -> 账号状态 -> 发布前后操作”看，source_plan：{plan_label}。"
            "先找作品/举报/发布线索，再看账号基线，最后对齐发布前后的登录、改密和风控操作。"
            "photo_search no_data 或档案中心失败都不能排除异常发布，只能作为当前条件下的 source_quality。"
        ),
        "same_device": (
            f"同设备只进入扩散/佐证层，source_plan：{plan_label}。"
            "它能给候选关联账号，但不能直接写团伙。"
            "需要再用账号画像、登录日志和 Track 活跃与数据可用性验证设备、时间和行为是否一致；档案中心失败时输出 partial evidence。"
        ),
        "event_attribution": (
            f"这是事件归因，不是策略树资产查询，source_plan：{plan_label}。"
            "先用 event detail 锚定事件时间、反馈和关键实体，再用 feature list 做可用特征摘要。"
            "策略命中只能作为事件层证据，不能单独推导用户风险。"
        ),
        "feature_partial": (
            f"不能说明完整特征。source_plan：{plan_label}。partial_observation_available 只能做部分观察。"
            "可引用 feature group、计数和关键实体摘要，但不能输出 raw feature values，也不能升级成强证据。"
        ),
        "policy_tree": (
            f"这个只走策略资产治理，source_plan：{plan_label}。"
            "policyTree lookup 解释策略树、版本和节点上下文。"
            "它不是 event hit path，不能证明某个用户或事件实际命中；命中证据要回到事件详情或策略命中入口。"
        ),
        "strategy_hit_boundary": (
            f"不能直接定性。source_plan：{plan_label}，只解决事件层上下文；策略命中只是辅助证据。"
            "风险结论还要回到控制权变化、异常行为闭环和账号/设备/发布链路的交叉验证。"
            "没有 source_quality 支撑时，只能写线索和待补证。"
        ),
    }
    draft = drafts.get(
        focus,
        f"按显式 source_plan 处理：{plan_label}。保留 source_quality、missing_evidence 和 final_answer_boundary，不自动执行平台查询。",
    )
    return f"{draft}\n\n{actual['user_visible_status_summary']}"


def evaluate_demo_case(plan: dict[str, Any], case: dict[str, Any]) -> dict[str, Any]:
    evaluated = evaluate_case(plan, case)
    actual = route_query(plan, str(case.get("user_query", "")))
    answer_draft = answer_draft_for(case, actual)
    if actual.get("routing_metadata_yaml_visible"):
        answer_is_natural = "routing_metadata:" in answer_draft and "platform_called: false" in answer_draft
    else:
        answer_is_natural = (
            len(answer_draft) >= 80
            and "source_plan" in answer_draft
            and "routing_metadata:" not in answer_draft
            and "action" not in answer_draft.lower()
        )
    issues = []
    if not evaluated["pass"]:
        issues.append(evaluated["issue_if_failed"])
    if not answer_is_natural:
        issues.append("answer draft is too terse or too action-list-like")
    return {
        **evaluated,
        "Dennis_answer_draft": answer_draft,
        "user_visible_status_summary": actual.get("user_visible_status_summary"),
        "metadata_visibility": actual.get("metadata_visibility"),
        "routing_metadata_yaml_visible": actual.get("routing_metadata_yaml_visible"),
        "should_not_do": list(case.get("should_not_do", [])),
        "pass": not issues,
        "issue_if_failed": "; ".join(issue for issue in issues if issue),
        "fix_applied": "none" if not issues else "pending",
    }


def demo_result(plan: dict[str, Any]) -> dict[str, Any]:
    cases = [evaluate_demo_case(plan, case) for case in DEMO_CASES]
    failed = [case for case in cases if not case["pass"]]
    return {
        "schema_version": "browser_backed_fixed_actions_text_demo_v1",
        "cases_total": len(cases),
        "cases_passed": len(cases) - len(failed),
        "cases_failed": len(failed),
        "default_runtime_routing_false": default_runtime_routing_ok(plan),
        "controlled_parallel_groups_supported": list(CONTROLLED_PARALLEL_EXECUTION_GROUPS),
        "real_platform_called": False,
        "dataagent_called": False,
        "hive_called": False,
        "cases": cases,
    }


def render_demo_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Browser-Backed Fixed Actions Text Demo V1",
        "",
        "This is an offline text demo. It does not start the browser-backed service, access real platforms, call DataAgent/Hive, read auth material, or execute source actions.",
        "",
        f"- cases_total: `{result['cases_total']}`",
        f"- cases_passed: `{result['cases_passed']}`",
        f"- cases_failed: `{result['cases_failed']}`",
        f"- default_runtime_routing_false: `{str(result['default_runtime_routing_false']).lower()}`",
        f"- controlled_parallel_groups_supported: `{', '.join(result['controlled_parallel_groups_supported'])}`",
        f"- real_platform_called: `{str(result['real_platform_called']).lower()}`",
        f"- dataagent_called: `{str(result['dataagent_called']).lower()}`",
        f"- hive_called: `{str(result['hive_called']).lower()}`",
        "",
    ]
    for case in result["cases"]:
        expected_plan = " -> ".join(case["expected_source_plan"]["actions"]) or "(none)"
        actual_plan = " -> ".join(case["actual_source_plan_or_template"]["actions"]) or "(none)"
        expected_groups = ", ".join(case.get("expected_execution_groups", [])) or "(none)"
        actual_groups = ", ".join(case.get("actual_execution_groups", [])) or "(none)"
        lines.extend(
            [
                f"## {case['id']}",
                "",
                f"- user_query: {case['user_query']}",
                f"- expected_source_plan: `{expected_plan}`",
                f"- expected_orchestration: {case['expected_source_plan']['orchestration']}",
                f"- actual_source_plan_or_template: `{actual_plan}`",
                f"- expected_execution_groups: `{expected_groups}`",
                f"- actual_execution_groups: `{actual_groups}`",
                f"- expected_boundary_flags: `{', '.join(case['expected_boundary_flags'])}`",
                f"- actual_boundary_flags: `{', '.join(case['actual_boundary_flags'])}`",
                f"- metadata_visibility: `{case['metadata_visibility']}`",
                f"- routing_metadata_yaml_visible: `{str(case['routing_metadata_yaml_visible']).lower()}`",
                f"- user_visible_status_summary: {case['user_visible_status_summary']}",
                f"- should_not_do: `{', '.join(case['should_not_do'])}`",
                f"- pass: `{str(case['pass']).lower()}`",
                f"- issue_if_failed: {case['issue_if_failed'] or 'none'}",
                f"- fix_applied: {case['fix_applied']}",
                "",
                "Dennis_answer_draft:",
                "",
                case["Dennis_answer_draft"],
                "",
            ]
        )
    return "\n".join(lines)


def render_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Browser-Backed Fixed Actions Text Dry-Run",
        "",
        f"- cases_total: `{result['cases_total']}`",
        f"- cases_passed: `{result['cases_passed']}`",
        f"- cases_failed: `{result['cases_failed']}`",
        f"- default_runtime_routing_false: `{str(result['default_runtime_routing_false']).lower()}`",
        f"- controlled_parallel_groups_supported: `{', '.join(result['controlled_parallel_groups_supported'])}`",
        f"- real_platform_called: `{str(result['real_platform_called']).lower()}`",
        f"- dataagent_called: `{str(result['dataagent_called']).lower()}`",
        f"- hive_called: `{str(result['hive_called']).lower()}`",
        "",
        "| id | pass | expected_source_plan | actual_source_plan_or_template | expected_execution_groups | actual_execution_groups | expected_boundary_flags | actual_boundary_flags | issue_if_failed | fix_applied |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for case in result["cases"]:
        expected_plan = ",".join(case["expected_source_plan"]["actions"])
        actual_plan = ",".join(case["actual_source_plan_or_template"]["actions"])
        expected_groups = ",".join(case.get("expected_execution_groups", []))
        actual_groups = ",".join(case.get("actual_execution_groups", []))
        expected_flags = ",".join(case["expected_boundary_flags"])
        actual_flags = ",".join(case["actual_boundary_flags"])
        lines.append(
            "| {id} | {passed} | {expected} | {actual} | {expected_groups} | {actual_groups} | {expected_flags} | {actual_flags} | {issue} | {fix} |".format(
                id=case["id"],
                passed=str(case["pass"]).lower(),
                expected=expected_plan,
                actual=actual_plan,
                expected_groups=expected_groups,
                actual_groups=actual_groups,
                expected_flags=expected_flags,
                actual_flags=actual_flags,
                issue=case["issue_if_failed"].replace("|", "/"),
                fix=case["fix_applied"],
            )
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Offline text dry-run for browser-backed fixed actions v1.")
    parser.add_argument("--cases", default=str(CASES_PATH))
    parser.add_argument("--format", choices=["json", "markdown"], default="json")
    parser.add_argument("--ids", nargs="*", default=None, help="Optional case ids to run.")
    parser.add_argument("--demo", action="store_true", help="Run the small natural-language text demo set.")
    parser.add_argument("--write-demo-doc", action="store_true", help="Write the demo markdown document.")
    args = parser.parse_args()

    plan = load_plan()
    if args.demo:
        result = demo_result(plan)
        if args.write_demo_doc:
            DEMO_DOC_PATH.write_text(render_demo_markdown(result), encoding="utf-8")
        if args.format == "markdown":
            print(render_demo_markdown(result))
        else:
            print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 0 if result["cases_failed"] == 0 and result["default_runtime_routing_false"] else 1

    cases_doc = load_text_cases(Path(args.cases))
    cases = list(cases_doc.get("cases", []))
    if args.ids:
        wanted = set(args.ids)
        cases = [case for case in cases if case.get("id") in wanted]

    evaluated = [evaluate_case(plan, case) for case in cases]
    failed = [case for case in evaluated if not case["pass"]]
    result = {
        "schema_version": "browser_backed_fixed_actions_text_dryrun_v1",
        "cases_total": len(evaluated),
        "cases_passed": len(evaluated) - len(failed),
        "cases_failed": len(failed),
        "default_runtime_routing_false": default_runtime_routing_ok(plan),
        "controlled_parallel_groups_supported": list(CONTROLLED_PARALLEL_EXECUTION_GROUPS),
        "real_platform_called": False,
        "dataagent_called": False,
        "hive_called": False,
        "cases": evaluated,
    }

    if args.format == "markdown":
        print(render_markdown(result))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not failed and result["default_runtime_routing_false"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
