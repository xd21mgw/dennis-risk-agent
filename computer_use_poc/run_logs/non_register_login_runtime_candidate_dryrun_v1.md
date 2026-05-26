# Non-register / Login Runtime Candidate Dry-run v1

## Goal

验证非注册 / 登录相关天狮能力的轻量 runtime / plan 级接入是否符合边界。

本轮只做文本级 dry-run：

- 不访问真实平台。
- 不调用 DataAgent。
- 不更新 release package。
- 不修改核心 Skill。
- 不提交 git。

## Capability Scope

```yaml
registered_or_indexed_capabilities:
  tianshi_live_attach_attribution_candidate:
    status: runtime_candidate_beta_partial
    executable_scope: live_attach only
  business_security_scene_asset_mapping:
    status: asset_index_only / query_plan_only
    executable_scope: none
  tianshi_anticrawl_family_candidate:
    status: candidate_only / query_plan_only
    executable_scope: none
not_registered_as_runtime:
  - ANTICRAWL executable attribution
  - COMMENT
  - MESSAGE
  - REBIND
  - RESET_PASSWORD
```

## Case 1: live attach user-level block reason

```yaml
user_question: 帮我看下用户 218368298 的直播长连接为什么被拦。
expected_route: tianshi_live_attach_attribution_candidate
expected_behavior:
  - 首选 fastQueryHbase。
  - eventList 补事件分布。
  - nodePolicyAttribution 作为归因路径。
  - 标记 event_detail_partial。
  - 不做最终风险定性。
result: pass
```

## Case 2: explicit SYNC_LIVE_ATTACH_REQUEST event

```yaml
user_question: SYNC_LIVE_ATTACH_REQUEST 这个事件为什么阻止？
expected_route: tianshi_live_attach_attribution_candidate
expected_behavior:
  - 不是 USER_REGISTER_NEW 单事件归因模板。
  - 输出 attach 专属归因模板。
  - 包含直播人气防刷 / 用户位置频繁跳变 / 启动参数不一致等归因路径占位。
result: pass
```

## Case 3: business security scene asset map

```yaml
user_question: 业务安全除了注册登录还有哪些场景？
expected_route: business_security_scene_asset_mapping
expected_behavior:
  - 输出账号、流量、反爬、互动、活动 5 类资产地图。
  - 明确资产地图不是上线能力。
  - 明确 verified / partial / candidate_only 分层。
  - 不触发平台查询。
result: pass
```

## Case 4: ANTICRAWL query plan

```yaml
user_question: 这个接口是不是被爬了？能查 ANTICRAWL 吗？
expected_route: tianshi_anticrawl_family_candidate / anti_crawler_expert_mode
expected_behavior:
  - 输出反爬查询计划。
  - 要求 source_id / eventId / time_window 等输入。
  - 不执行完整归因。
  - 不声称 ANTICRAWL 已上线可执行。
result: pass
```

## Case 5: user risk question

```yaml
user_question: 帮我看下用户 218368298 有没有风险。
expected_route: multi_evidence_orchestration
expected_behavior:
  - 不默认触发 attach。
  - 不默认触发 ANTICRAWL。
  - 不默认触发完整策略治理。
  - 天狮策略命中仅作为候选证据源。
result: pass
```

## Case 6: COMMENT / MESSAGE strategy question

```yaml
user_question: 评论和私信的策略能不能也查？
expected_route: business_security_scene_asset_mapping / query_plan_only
expected_behavior:
  - 不注册 COMMENT / MESSAGE runtime。
  - 输出当前是 asset map 中的 partial 场景，需单独深验证。
  - 不假装已可执行。
result: pass
```

## Summary

```yaml
dryrun_result: pass
case_count: 6
real_platform_access: false
dataagent_called: false
release_package_updated: false
core_skill_modified: false
wrong_runtime_registration:
  anticrawl: false
  comment: false
  message: false
  rebinding_or_reset_password: false
```
