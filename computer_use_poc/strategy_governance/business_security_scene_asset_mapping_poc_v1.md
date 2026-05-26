# Business Security Scene Asset Mapping POC v1

## 1. POC 定位

本文档是天狮策略平台的业务安全场景资产地图 POC。

用途：

- 帮助 Dennis Agent 从“注册 / 登录已验证样板”扩展到更多业务安全场景。
- 沉淀 `eventType` / `policyTreeCode` / `policyTreeVersion` / `bizCat` / representative scene。
- 为后续选择少量高价值场景做深验证提供地图。

边界：

- 这不是 runtime 可直接调用的已上线能力。
- 这不是风险定性能力。
- 这不是策略归因能力。
- 不能把 `eventType` / `policyTree` 存在解释为策略正在命中。
- 不能把资产地图当成风险研判结论。
- 不能宣称这些场景已可上线使用。

## 2. 当前已发现的大类

### account_security

注册：

- `USER_REGISTER_NEW`
- `REGISTER`
- `REGISTER_NEW_DELAY`
- `WEB_USER_REGISTER`
- `REGISTER_FROM_QQ`

登录：

- `LOGIN_AUDIT`
- `ASYNC_LOGIN`
- `LOGIN`
- `CHECK_LOGIN`
- `LOGIN_AUDIT_FROM_WEB`

换绑：

- `REBIND`
- `VERIFY_BEFORE_REBIND`
- `ASYNC_REBIND_MOBILE`
- `REBIND_ID_CARD`
- `THIRD_PARTY_BIND`

改密：

- `RESET_PASSWORD`
- `RESET_PASSWORD_TEMP`
- `ASYNC_RESET_PASSWORD`
- `B_ACCOUNT_RESET_PWD`

找回：

- `KS_ACCOUNT_FIND_ONLINE`
- `ASYNC_ACCOUNT_FIND`

注销：

- `KS_ACCOUNT_CANCEL_ONLINE`
- `ASYNC_LOGOUT`

### traffic_security

- `SYNC_LIVE_ATTACH_REQUEST`
- `ASYNC_LIVE_ATTACH_REQUEST`
- `ATTACH_PUSH_BAD_USERS`
- `ANTIBRUSH_OFFLINE_PUNISH`
- `USER_FREE_PACKAGE`

### anti_crawler_antibrush

- `ANTICRAWL`
- `ANTICRAWL_LIVE`
- `ANTICRAWL_BASE`
- `ANTICRAWL_SEARCH`
- `ANTICRAWL_COMMON`
- `ANTICRAWL_RPC_SIGN`
- `ANTICRAWL_DEFAULT`
- `ANTICRAWL_WHITE`
- `ANTICRAWL_DOWNGRADE`
- `ANTICRAWL_NG_LOG`
- `ANTICRAWL_PLATFORM_SYNC`
- `FANPA_ACCOUNT_HI_PUNISH_TASK`
- `ANTICRAWL_MERCHANT_OFFLINE_PUNISH`
- `GAME_REGISTER`
- `GAME_LOGIN`
- `GAME_FOLLOW`

### interaction_anti_abuse

- `FOLLOW`
- `ZT_FOLLOW`
- `ASYNC_FOLLOW`
- `LIKE`
- `ZT_LIKE`
- `COMMENT`
- `ZT_COMMENT`
- `MESSAGE`
- `ZT_IM_CONTENT`
- `MESSAGE_ATTACHMENT`
- `LIVE_STREAM_LIKE`
- `COMMENT_LIKE`
- `MOMENT_LIKE`

### activity_anti_cheating

- `REDPACKET_RAIN`
- `CNY_PK_ACTIVITY`
- `BLIND_BOX_AWARD`
- `SF_MAIN_ACTIVITY`
- `XF_APP_REGISTER`
- `XF_APP_LOGIN`
- `EB_LOTTERY_SHOW`
- `ACFUN_COINS_AWARD`

## 3. 已验证 / 部分验证 / 未验证状态

### verified

#### USER_REGISTER_NEW

- `eventType` 已验证。
- `policyTree` 已验证。
- 节点结构已验证。
- 绑定策略已验证。
- eventList 已验证。
- fastQueryHbase 已验证。
- attribution 已验证。

### partial

#### LOGIN_AUDIT

- `eventType` 已发现。
- `policyTreeVersion` 有返回。
- eventList 有部分事件。
- 允许事件无 effective_policy。
- 归因未完成。

#### REBIND

- `eventType` / `policyTreeCode` 候选。
- `policyTreeVersion` 有返回。
- 节点结构未获取。
- 归因未验证。

#### RESET_PASSWORD

- `eventType` / `policyTreeCode` 候选。
- `policyTreeVersion` 有返回。
- 节点结构未获取。
- 归因未验证。

#### SYNC_LIVE_ATTACH_REQUEST

- fastQueryHbase 已看到真实阻止事件。
- eventList 已验证，返回 8 个事件：3 阻止 + 5 允许。
- 发现策略：
  - `BS_antibrush_attach_user_multi_loc_block_policy`
  - `BS_antibrush_attach_not_same_startup_block_policy`
- rcpEventDetail 对允许事件成功，对阻止事件 HTTP + browser 都 timeout。
- getPolicyVersionListByEvent 已验证。
- nodePolicyAttribution 已验证，2 条策略均完成条件级归因，5 条件全 true。
- queryProPolicyTree 仍 partial，只返回版本号，不返回节点结构；可用 nodePolicyAttribution 归因路径补足部分节点结构缺口。
- 当前状态更新为 `deep_validation_partial / runtime_candidate_beta_partial`，不是 full success。

#### FOLLOW / LIKE / COMMENT / MESSAGE

- `eventType` 已发现。
- `policyTreeVersion` 有返回。
- 节点结构未获取。
- 归因未验证。

### candidate_only

- `ANTICRAWL` 家族。
- 活动反作弊家族。
- 互动防刷子 eventType。
- 离线处置类 TASK 事件。

## 4. 高价值下一批验证场景

### P0

#### SYNC_LIVE_ATTACH_REQUEST / 直播长连接 attach

原因：

- fastQueryHbase 已看到真实命中，最接近可验证。

下一步：

- 验证 eventList。
- 验证 eventDetail 或 browser detail。
- 验证归因链路。

#### ANTICRAWL 家族

原因：

- 反爬是核心业务安全方向，eventType 家族很大。
- 当前仍保持 `candidate_only`，需要有反爬命中的 source_id 或 eventId 后再深验证。

下一步：

- 确认 `ANTICRAWL` / `ANTICRAWL_LIVE` / `ANTICRAWL_BASE` / `ANTICRAWL_PLATFORM_SYNC` 的 policyTreeCode 和节点结构。
- 当前已确认部分子树版本：`ANTICRAWL_LIVE`、`ANTICRAWL_BASE`、`ANTICRAWL_SEARCH`、`ANTICRAWL_COMMON`、`ANTICRAWL_RPC_SIGN`；`ANTICRAWL` 根节点 / `ANTICRAWL_PLATFORM_SYNC` / `LIVE_STREAM_ANTICRAWL` 无版本返回。

### P1

#### COMMENT / MESSAGE

原因：

- 策略树版本号很高，可能迭代最频繁。

下一步：

- 验证 eventList / fastQueryHbase / 策略树节点 / 绑定策略。

#### REBIND / RESET_PASSWORD

原因：

- 账号安全核心链路，补齐注册 / 登录之外的账号场景。

下一步：

- 验证 eventList / fastQueryHbase / policyTree node / attribution。

### P2

- FOLLOW / LIKE。
- 活动反作弊。
- 离线处置类 TASK 事件。

## 5. 参数缺口

- `policyTreeList` API 参数格式不明确：当前 `GET /v2/rest/pro/policyTree/policyTreeList` 返回 500 / MyBatis NullPointerException，需要 HAR 或页面网络请求确认正确参数。
- `queryProPolicyTree` 对非 `USER_REGISTER_NEW` 的树只返回版本号，不返回节点结构：需要对比 `USER_REGISTER_NEW` 的成功参数，或用 browser 页面点击策略树获取节点结构。
- `policySearch` 模糊搜索返回 0：可能只支持 policyCode 精确搜索，需确认参数格式。
- `ANTICRAWL` 家族结构不清：不确定是一个大策略树，还是多个子 eventType / policyTree。
- `SYNC_LIVE_ATTACH_REQUEST` eventDetail 超时：需要验证 browser same-origin detail 或其他详情接口。

## 6. Schema 草案

```yaml
business_security_scene_asset_mapping:
  domain:
  scene_name:
  scene_aliases:
  event_type:
  policy_tree_code:
  policy_tree_name:
  policy_tree_version:
  biz_category:
  representative_nodes:
  sample_policies:
  validation_status:
  event_type_seen:
  policy_tree_verified:
  node_structure_verified:
  binding_verified:
  eventList_verified:
  fastQueryHbase_seen:
  attribution_verified:
  confidence:
  notes:
  next_validation_step:
```

## 7. 回答模板草案

```text
结论摘要：
这是业务安全场景资产地图，不是已上线 runtime 能力，也不是风险定性或策略归因结论。

已覆盖大类：
- account_security:
- traffic_security:
- anti_crawler_antibrush:
- interaction_anti_abuse:
- activity_anti_cheating:

各大类候选 eventType：
- 按 domain 输出候选 eventType / policyTreeCode / policyTreeVersion / bizCat。

已验证场景：
- USER_REGISTER_NEW:

部分验证场景：
- LOGIN_AUDIT:
- REBIND:
- RESET_PASSWORD:
- SYNC_LIVE_ATTACH_REQUEST:
- FOLLOW / LIKE / COMMENT / MESSAGE:

仅候选场景：
- ANTICRAWL 家族:
- 活动反作弊家族:
- 互动防刷子 eventType:
- 离线处置类 TASK 事件:

高价值下一批验证场景：
- P0:
- P1:
- P2:

参数缺口：
- policyTreeList 参数格式:
- queryProPolicyTree 非注册树节点:
- policySearch 模糊搜索:
- ANTICRAWL 家族结构:
- SYNC_LIVE_ATTACH_REQUEST detail:

不能下的结论：
- 找到 eventType 不代表该场景已可研判。
- 找到 policyTreeCode 不代表策略树节点 / 绑定策略已验证。
- 找到策略树 / 策略组不等于策略正在命中。
- 策略存在不等于风险存在。
- policyTreeVersion 高不等于策略更多或风险更高。
- status=上线不等于每次事件都生效。
- owner / updateUser / operator 只做追溯字段，不做责任归因。

下一步建议：
- 选择少量高价值场景做深验证，不全量扩散。
- 优先验证 P0 的直播长连接 attach 和 ANTICRAWL 家族。

关键边界：
- 不输出敏感字段原值。
- 不自动处置、不写操作、不上线、不审批。
- 不注册成 runtime 已上线能力。
```

## 8. 关键边界

- 本文档是资产地图，不是已上线能力。
- 找到 `eventType` 不代表该场景已可研判。
- 找到 `policyTreeCode` 不代表策略树节点 / 绑定策略已验证。
- 找到策略树 / 策略组不等于策略正在命中。
- 策略存在不等于风险存在。
- `policyTreeVersion` 高不等于策略更多或风险更高。
- `status=上线` 不等于每次事件都生效。
- `owner` / `updateUser` / `operator` 只做追溯字段，不做责任归因。
- 不输出敏感字段原值。
- 不自动处置、不写操作、不上线、不审批。
- 不把 SubBiz / 策略组资产注册成 runtime 已上线能力。
