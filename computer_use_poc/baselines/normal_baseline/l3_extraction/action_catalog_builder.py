"""Action catalog and family mapping for dynamic semantic discovery."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any


FAMILY_PROMPTS: dict[str, str] = {
    "profile_user_profile": "Profile/account fields: social counts, content counts, profile completeness; labels are supporting context only.",
    "social_relation": "Follow/fans/relation fields: list size, source concentration, reciprocal weakness, followed-account traits.",
    "content_collect": "Collect/content fields: collect/photo/private-message/comment content and possible diversion clues.",
    "login_client": "Login/client fields: sdkVersion, appVersion, clientVersion, loginType, trusted-device and client consistency.",
    "device_environment": "Device environment: app list, accessibility, proxy/VPN/hook/frida/emulator/root/toolchain packages.",
    "graph_relation": "Graph/relation fields: same-device, related-user structures, relation edges and group matrices.",
    "strategy_event": "Strategy/event fields: explanatory context only; label/post-action leakage is not primary feature.",
    "behavior_event": "Behavior/timing fields: duration, sequence, rhythm and cross-action behavior.",
}


ACTION_CARDS: dict[str, dict[str, Any]] = {
    "archives_user_profile": {
        "primary_family": "profile_user_profile",
        "physical_meaning": "查询用户画像、资料、关注/粉丝/作品/收藏等账号画像字段。",
        "key_questions": ["是否高关注低粉丝", "是否低作品高关注", "是否收藏/关注/作品结构异常"],
        "important_fields": ["followCount", "fansCount", "photoCount", "collectCount"],
        "schema_only_fields": ["result", "currentTime", "costTime", "host", "message"],
    },
    "archives_follow_list": {
        "primary_family": "social_relation",
        "physical_meaning": "查询用户关注了哪些账号，用于判断大量关注、关注来源和关注对象共性。",
        "key_questions": ["关注列表是否接近满页", "关注来源是否集中", "关注对象是否有共同特征"],
        "important_fields": ["data.dataList.source", "data.dataList.fansCount", "data.dataList.photoCount"],
    },
    "archives_fans_list": {
        "primary_family": "social_relation",
        "physical_meaning": "查询用户粉丝列表，用于判断粉丝少、回关弱、关注粉丝比异常。",
        "key_questions": ["粉丝列表是否很少", "粉丝来源是否集中"],
    },
    "archives_collect_photo_list": {
        "primary_family": "content_collect",
        "physical_meaning": "查询用户收藏作品，用于判断收藏内容是否有导流、二维码、URL 或内容钩子。",
    },
    "archives_collection_list": {
        "primary_family": "content_collect",
        "physical_meaning": "查询用户收藏夹结构，用于判断收藏夹是否作为导流入口。",
    },
    "archives_related_users": {
        "primary_family": "graph_relation",
        "physical_meaning": "查询同设备/关联用户，用于判断团伙、同设备族和关联矩阵。",
    },
    "archives_photo_search": {
        "primary_family": "content_collect",
        "physical_meaning": "查询用户作品/内容，用于判断低作品、发布内容和导流线索。",
    },
    "archives_private_message_search": {
        "primary_family": "content_collect",
        "physical_meaning": "查询私信记录，用于判断私信导流、联系链路和异常互动。",
    },
    "login_logs_search": {
        "primary_family": "login_client",
        "physical_meaning": "查询登录日志，用于判断 sdkVersion、appVersion、loginType、IP/UA/设备切换。",
    },
    "infra_user_action_log": {
        "primary_family": "login_client",
        "physical_meaning": "登录/行为日志离线同源字段，用于解析 requestParam、uri、客户端协议参数。",
    },
    "track_sequence_get_device_ids": {
        "primary_family": "device_environment",
        "physical_meaning": "查询用户近期 Track 设备 ID，用于驱动设备环境补证。",
    },
    "track_sequence_get_use_duration": {
        "primary_family": "behavior_event",
        "physical_meaning": "查询使用时长，用于判断活跃度和行为节奏。",
    },
    "track_sequence_profile": {
        "primary_family": "behavior_event",
        "physical_meaning": "查询 Track 用户画像摘要，用于补充活跃和行为上下文。",
    },
    "weapon_inventory": {
        "primary_family": "device_environment",
        "physical_meaning": "Weapon 设备风险画像，用于判断设备环境和风险标签。",
    },
    "weapon_device_info": {
        "primary_family": "device_environment",
        "physical_meaning": "查询设备基础信息。",
    },
    "weapon_device_app_list": {
        "primary_family": "device_environment",
        "physical_meaning": "查询设备安装 APP 列表，用于判断异常工具、辅助、多开、代理或自动化工具链。",
    },
    "weapon_device_location_info": {
        "primary_family": "device_environment",
        "physical_meaning": "查询设备位置上下文。",
    },
    "weapon_user_klink_status": {
        "primary_family": "device_environment",
        "physical_meaning": "查询用户 KLink 状态，作为设备/环境解释上下文。",
    },
    "rcp_snapshot": {
        "primary_family": "strategy_event",
        "physical_meaning": "查询 RCP/策略事件入口上下文，注意只作解释，不能作为强特征。",
    },
    "rcp_fast_query_hbase": {
        "primary_family": "strategy_event",
        "physical_meaning": "查询策略事件快照入口，注意 label leakage。",
    },
}


def card_for_action(action_name: str) -> dict[str, Any]:
    if action_name in ACTION_CARDS:
        return dict(ACTION_CARDS[action_name])
    if action_name.startswith("archives_"):
        family = "content_collect"
    elif action_name.startswith("track_"):
        family = "behavior_event"
    elif action_name.startswith("weapon_"):
        family = "device_environment"
    elif action_name.startswith("rcp_"):
        family = "strategy_event"
    elif "login" in action_name:
        family = "login_client"
    else:
        family = "behavior_event"
    return {
        "primary_family": family,
        "physical_meaning": f"{action_name} 的本地 raw action；按 {family} 家族做动态发现。",
        "key_questions": [],
        "important_fields": [],
        "schema_only_fields": [],
    }


def build_action_catalog(manifest_rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_action: dict[str, dict[str, Any]] = {}
    for row in manifest_rows:
        action = row.get("action") or "unknown"
        entry = by_action.setdefault(action, {"action_name": action, "rows": [], **card_for_action(action)})
        entry["rows"].append(row)
    family_counts = Counter(entry["primary_family"] for entry in by_action.values())
    actions = []
    for action, entry in sorted(by_action.items()):
        users = sorted({str(row.get("user_id")) for row in entry["rows"] if row.get("user_id")})
        actions.append({
            "action_name": action,
            "source_name": action.split("_", 1)[0],
            "family": entry["primary_family"],
            "action_physical_meaning": entry["physical_meaning"],
            "important_fields": entry.get("important_fields", []),
            "schema_only_fields": entry.get("schema_only_fields", []),
            "covered_users": users,
            "row_count": len(entry["rows"]),
        })
    return {
        "action_count": len(actions),
        "family_count": len(family_counts),
        "family_distribution": dict(family_counts),
        "actions": actions,
    }


def write_action_catalog_markdown(catalog: dict[str, Any], output: str | Path) -> None:
    lines = ["# Action Catalog With Family", "", "|action|family|covered_users|physical meaning|", "|---|---|---:|---|"]
    for item in catalog.get("actions", []):
        lines.append(
            f"|{item['action_name']}|{item['family']}|{len(item.get('covered_users') or [])}|{item['action_physical_meaning']}|"
        )
    Path(output).write_text("\n".join(lines) + "\n", encoding="utf-8")

