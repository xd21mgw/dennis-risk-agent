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
]

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
        "expected_boundary_flags": ["single_source_not_enough_for_ato", "no_data_not_risk_exclusion"],
        "should_not_do": ["do_not_only_query_login_logs", "do_not_make_final_judgement_without_source_quality"],
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
        "expected_boundary_flags": ["photo_search_no_data_not_abnormal_publish_exclusion"],
        "should_not_do": ["do_not_output_no_abnormal_publish_from_photo_no_data", "do_not_make_final_judgement"],
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
        "expected_boundary_flags": ["related_users_not_gang_conclusion"],
        "should_not_do": ["do_not_label_gang_from_same_device_only", "do_not_bulk_expand_without_plan"],
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


def route_query(plan: dict[str, Any], user_query: str) -> dict[str, Any]:
    text = normalize_text(user_query)
    actions: list[str] = []
    flags: list[str] = []
    orchestration = "explicit_source_plan_only"

    if has_any(text, ["cookie", "token", "session", "header", "password", "raw login records", "raw labelinfo", "raw body"]):
        return {
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
        }

    if has_any(text, ["未验证的新 action", "新 action", "接进主链"]):
        return {
            "actions": [],
            "orchestration": "reject default routing; require registry/readiness/live-smoke evidence first",
            "boundary_flags": ["disabled_or_unverified_action_not_default_route"],
            "answer_contract": ["source_plan", "final_answer_boundary"],
            "safety_flags": unique(GLOBAL_SAFETY_FLAGS + ANSWER_TEMPLATE_NEGATIVE_GUARDS + [
                "do_not_set_default_runtime_routing_true",
                "do_not_add_action",
                "do_not_guess_path",
            ]),
        }

    if has_any(text, ["302", "auth_failed", "登录态", "账号域"]):
        actions += ["archives_user_profile", "archives_user_analysis"]
        flags += ["auth_flow_not_completed_in_bound_context", "partial_evidence_required"]
        orchestration = "archives auth state is source quality; do not repair auth or infer permission denial"

    if has_any(text, ["policytree", "策略树", "资产路径", "树结构"]):
        if has_any(text, ["event", "事件", "两个都要", "不要混"]):
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

    if has_any(text, ["event", "eventid", "事件详情", "被拦", "feature", "特征"]):
        if "rcp_policy_tree_lookup" not in actions or has_any(text, ["命中归因", "详情", "feature", "特征"]):
            actions += scenario_actions(plan, "rcp_event_attribution")
            flags += scenario_flags(plan, "rcp_event_attribution")
            flags += ["attribution_not_cheating_judgement"]
            if "separate event attribution" not in orchestration:
                orchestration = "rcp_event_detail -> rcp_event_feature_list"
        if has_any(text, ["partial", "完整覆盖", "强证据"]):
            flags += ["partial_observation_available", "do_not_upgrade_partial_to_strong_evidence"]

    if has_any(text, ["同设备", "关联账号", "扩散"]):
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

    return {
        "actions": unique(actions),
        "orchestration": orchestration,
        "boundary_flags": unique(flags),
        "answer_contract": list(GLOBAL_ANSWER_CONTRACT),
        "safety_flags": unique(GLOBAL_SAFETY_FLAGS + ANSWER_TEMPLATE_NEGATIVE_GUARDS),
    }


def evaluate_case(plan: dict[str, Any], case: dict[str, Any]) -> dict[str, Any]:
    actual = route_query(plan, str(case.get("user_query", "")))
    expected_actions = list(case.get("expected_route_or_actions", []))
    expected_flags = list(case.get("expected_boundary_flags", []))
    expected_contract = list(case.get("expected_answer_contract", []))
    should_not_do = list(case.get("should_not_do", []))

    actual_actions = actual["actions"]
    if expected_actions:
        actions_ok = all(action in actual_actions for action in expected_actions)
    else:
        actions_ok = actual_actions == []

    flags_ok = all(flag in actual["boundary_flags"] for flag in expected_flags)
    contract_ok = all(field in actual["answer_contract"] for field in expected_contract)
    safety_ok = all(flag in actual["safety_flags"] for flag in should_not_do)
    default_routing_ok = default_runtime_routing_ok(plan)

    issues: list[str] = []
    if not actions_ok:
        issues.append(f"expected actions missing: {expected_actions}; actual={actual_actions}")
    if not flags_ok:
        missing = [flag for flag in expected_flags if flag not in actual["boundary_flags"]]
        issues.append(f"expected boundary flags missing: {missing}")
    if not contract_ok:
        missing = [field for field in expected_contract if field not in actual["answer_contract"]]
        issues.append(f"expected answer contract missing: {missing}")
    if not safety_ok:
        missing = [flag for flag in should_not_do if flag not in actual["safety_flags"]]
        issues.append(f"should_not_do not enforced: {missing}")
    if not default_routing_ok:
        issues.append("default_runtime_routing drifted from false")

    return {
        "id": case.get("id"),
        "user_query": case.get("user_query"),
        "expected_source_plan": {
            "actions": expected_actions,
            "orchestration": case.get("expected_orchestration"),
        },
        "actual_source_plan_or_template": {
            "actions": actual_actions,
            "orchestration": actual["orchestration"],
            "answer_contract": actual["answer_contract"],
        },
        "expected_boundary_flags": expected_flags,
        "actual_boundary_flags": actual["boundary_flags"],
        "pass": not issues,
        "issue_if_failed": "; ".join(issues) if issues else "",
        "fix_applied": "none" if not issues else "pending",
    }


def answer_draft_for(case: dict[str, Any], actual: dict[str, Any]) -> str:
    actions = actual["actions"]
    plan_label = " -> ".join(actions)
    focus = str(case.get("answer_focus", ""))
    drafts = {
        "ato": (
            f"我会先按显式 source_plan 做 ATO 研判，不自动执行平台查询：{plan_label}。"
            "登录日志用于看可见窗口内的登录时间、IP、设备和方式；档案账号画像用于确认账号当前状态和注册/状态基线；"
            "档案用户分析用于补最近操作和风险日志；Track checkDataReady 只验证设备维度数据是否可读。"
            "即使某个 source no_data，也只写入 source_quality，不能直接排除 ATO；最终只能在证据齐备后给倾向，不做单源定性。"
        ),
        "login_no_data": (
            f"不能。这里的 source_plan 是 {plan_label}，它只能回答在线窗口和查询条件下是否有可见登录记录。"
            "no_data 代表当前 source 没返回记录，不代表没有登录、没有异常设备，也不代表没有 ATO。"
            "如果投诉或异常时间超出在线窗口，需要把 window gap 写进 missing_evidence，并用档案操作、账号画像或后续离线授权来源补证。"
        ),
        "profile": (
            f"我会把这个问题收敛到账号基线 source_plan：{plan_label}。"
            "重点看账号状态、注册/资料状态、标签或风险信息摘要，用来判断当前账号画像是否有明显背景线索。"
            "但画像是静态/近实时基线，不等于行为链路；不能仅凭账号状态正常或异常就给最终风险结论。"
        ),
        "analysis": (
            f"我会把 source_plan 收敛为档案中心用户分析：{plan_label}。它负责看最近操作和风险日志摘要，重点关注登录、改密、保护账号、冻结、直播/发布相关操作和时间分布。"
            "如果响应过大，只能输出 partial_observation_available：说明可以看到部分结构、计数或时间范围，但不能声称完整明细覆盖。"
            "下一步应缩短时间窗、降低 pageSize 或分页复查；raw records 不输出。"
        ),
        "publish": (
            f"这个问题走发布/内容承接 source_plan：{plan_label}。"
            "photo_search 看作品/举报/发布线索，账号画像看当前账号状态，用户分析补发布前后的登录、改密、风控操作时间线。"
            "photo_search no_data 不能写成没有异常发布，只能说明该 source 在当前条件下未返回线索；最终需要结合操作链路和其他证据。"
        ),
        "same_device": (
            f"我会把同设备当扩散线索处理，source_plan 是 {plan_label}。"
            "archives_related_users 只说明同设备关系或候选关联账号，后续要用账号画像、登录日志和 Track readiness 验证设备/时间/行为是否一致。"
            "不能因为同设备就直接写团伙，也不能无计划批量扩散。"
        ),
        "event_attribution": (
            f"这个是 RCP 事件归因，不是策略树资产查询，source_plan 是 {plan_label}。"
            "先用 event detail 确认事件时间、策略命中、反馈和关键实体；再用 feature list 看特征分组/可用部分观察。"
            "策略命中只能说明这个事件触发了某些策略条件，不能单独推导用户最终风险。"
        ),
        "feature_partial": (
            f"不能说明完整特征。source_plan 是 {plan_label}，partial_observation_available 只能作为部分观察。"
            "可以引用 feature group、估算计数、关键实体和 source_quality.large_response_limited，但要明确 raw feature values 和完整明细不可见。"
            "如果需要完整覆盖，需要更窄查询或专门的有界提取，不应把 partial 升级成强证据。"
        ),
        "policy_tree": (
            f"这个走策略资产治理，不是单案事件归因，source_plan 是 {plan_label}。"
            "policyTree lookup 用来解释 policyCode 所在策略树、版本和节点上下文，帮助理解策略资产关系。"
            "它不能证明某个 user_id 或 eventId 实际命中过该策略；事件命中要回到 rcp_event_detail / feature list 或策略命中入口。"
        ),
        "strategy_hit_boundary": (
            f"不能直接定性。source_plan 是 {plan_label}，策略命中只是一类辅助证据。"
            "我会先看事件详情和 feature list 的可用观察，再把登录日志、账号画像、用户操作或发布链路作为交叉验证。"
            "如果只有策略命中，没有时间线、行为链和 source_quality 支撑，只能输出风险线索或待补证，不能给最终处置结论。"
        ),
    }
    return drafts.get(focus, f"按显式 source_plan 处理：{plan_label}。保留 source_quality、missing_evidence 和 final_answer_boundary，不自动执行平台查询。")


def evaluate_demo_case(plan: dict[str, Any], case: dict[str, Any]) -> dict[str, Any]:
    evaluated = evaluate_case(plan, case)
    actual = route_query(plan, str(case.get("user_query", "")))
    answer_draft = answer_draft_for(case, actual)
    answer_is_natural = (
        len(answer_draft) >= 80
        and "source_plan" in answer_draft
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
        f"- real_platform_called: `{str(result['real_platform_called']).lower()}`",
        f"- dataagent_called: `{str(result['dataagent_called']).lower()}`",
        f"- hive_called: `{str(result['hive_called']).lower()}`",
        "",
    ]
    for case in result["cases"]:
        expected_plan = " -> ".join(case["expected_source_plan"]["actions"]) or "(none)"
        actual_plan = " -> ".join(case["actual_source_plan_or_template"]["actions"]) or "(none)"
        lines.extend(
            [
                f"## {case['id']}",
                "",
                f"- user_query: {case['user_query']}",
                f"- expected_source_plan: `{expected_plan}`",
                f"- expected_orchestration: {case['expected_source_plan']['orchestration']}",
                f"- actual_source_plan_or_template: `{actual_plan}`",
                f"- expected_boundary_flags: `{', '.join(case['expected_boundary_flags'])}`",
                f"- actual_boundary_flags: `{', '.join(case['actual_boundary_flags'])}`",
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
        f"- real_platform_called: `{str(result['real_platform_called']).lower()}`",
        f"- dataagent_called: `{str(result['dataagent_called']).lower()}`",
        f"- hive_called: `{str(result['hive_called']).lower()}`",
        "",
        "| id | pass | expected_source_plan | actual_source_plan_or_template | expected_boundary_flags | actual_boundary_flags | issue_if_failed | fix_applied |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for case in result["cases"]:
        expected_plan = ",".join(case["expected_source_plan"]["actions"])
        actual_plan = ",".join(case["actual_source_plan_or_template"]["actions"])
        expected_flags = ",".join(case["expected_boundary_flags"])
        actual_flags = ",".join(case["actual_boundary_flags"])
        lines.append(
            "| {id} | {passed} | {expected} | {actual} | {expected_flags} | {actual_flags} | {issue} | {fix} |".format(
                id=case["id"],
                passed=str(case["pass"]).lower(),
                expected=expected_plan,
                actual=actual_plan,
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
