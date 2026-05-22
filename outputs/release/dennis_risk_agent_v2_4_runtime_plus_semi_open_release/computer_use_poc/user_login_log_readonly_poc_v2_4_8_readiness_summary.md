# v2.4.8 用户登录统一日志 readonly POC Readiness Summary

## 1. 当前阶段结论

用户登录统一日志已经具备作为 Dennis Agent 最近实时登录链路补证手脚的基础能力，但尚不满足 fully validated / release ready。

当前能力更适合标记为：

```text
v2.4.8_user_login_log_hand_partially_ready
```

已完成 Run 001 ~ Run 005：

- Run 001：page_accessibility partially_validated。
- Run 002：detail_modal_partially_validated，switchUser 详情部分验证。
- Run 003：refresh_token_detail_modal_validated，仅限 refreshToken readonly JSON key extraction。
- Run 004：boundary_behavior_partially_validated，覆盖无结果和超窗防误判。
- Run 005：pagination_behavior_partially_validated，分页功能人工证据验证，自动化翻页不稳定。
- Run 006：multi_source_entry_resolution validated；multi_source_e2e blocked_by_archives_auth。
- Run 007：multi_source_e2e validated_with_partial_coverage。
- Run 008：archives_saved_state_reuse validated。
- Run 009：archives_user_analysis_pagination_behavior validated_with_correction。
- Run 010：archives_audit_label_log_access partially_validated。
- Run 011：unified_log_special_event_detail validated。

当前多源状态：

```yaml
multi_source_entry_resolution: validated
archives_saved_state_e2e: validated
archives_saved_state_reuse: validated
multi_source_e2e: validated_with_partial_coverage
archives_user_analysis_pagination: validated_with_correction
archives_audit_label_log_access: partially_validated
unified_log_special_event_detail: validated
release_status: release_candidate_not_final
```

Run 006 说明：

- 本轮目标是档案中心 + 用户登录统一日志同 `user_id=4700398885` 的 focused_login_risk e2e。
- Dennis 已先完成 `archives_center_entry_resolution`，读取了档案中心 README、playbook、lookup flow、integration notes、failure modes、历史 run logs、observation contract、smoke tests 和 scripts。
- 档案中心入口与 selector / playbook 已找到。
- e2e 未完成原因是 `agent-browser` 档案中心独立登录态阻断：`archives_browser_auth_blocked=true`、`archives_independent_login_required_for_agent_browser=true`。
- 档案中心 `userId` direct URL 已确认：`https://admin.p.adm-corp.kuaishou.com/frontend/archives/index.html#/archives/user/profile?userId={userId}`。
- 档案中心独立登录域已确认：`account.p.adm-corp.kuaishou.com`。
- 认证链路为：SSO → 档案中心独立登录 → userId direct URL。
- `sso_session.py` 可 HTTP 级访问，但 `agent-browser` GUI 进程未复用该 cookie，因此 direct URL 被重定向到独立登录页。
- 统一登录日志单源查询成功，`total_count=133`、`page_size=20`、`visible_row_count=20`、`partial_page_only=true`。
- 统一登录日志单源结果不能包装成 multi-source e2e 成功。

Run 007 说明：

- 本轮使用同一 `user_id=4700398885`。
- 档案中心 direct URL 成功访问，档案中心认证态已解决并保存 state：`archives_center_4700398885_20260519`。
- 档案中心 source：`accessible=true`、`query_success=true`、`result_present=true`，用户主页、用户分析 Tab、APP端核心操作日志可见。
- 档案中心时间范围约 6 个月：2025-11-20 ~ 2026-05-19，当前仅查看部分数据，`partial_coverage=true`。
- 统一登录日志 source：`accessible=true`、`query_success=true`、`result_present=true`、`total_count=133`、`page_size=20`、`visible_row_count=20`、`partial_page_only=true`。
- 跨源对齐：`same_user_id_used=true`、DID 一致，历史一键登录 / 退出登录行为可对齐。
- `multi_source_schema_ready=focused_login_risk_observation_only`。
- Run 007 不代表自动风险定性完成、全量历史数据已查看、设备攻防平台已验证、审核 / 打标日志已查看或最终风险结论已生成。

Run 008 ~ Run 011 说明：

- Run 008：`archives_center_4700398885_20260519` saved state 当前可复用，档案中心 direct URL 不再跳转独立登录页；该结论不泛化为所有账号 / 所有时间。
- Run 009：档案中心用户分析 / APP端核心操作日志存在分页，样例 `total_count=1181`、`page_size=10`；此前“无分页 / 无限滚动”结论作废，未遍历全页前必须 `partial_coverage=true`。
- Run 010：档案中心审核日志可访问且有结果，打标日志可访问且表头可见；审核 / 打标日志只作为补充 source，不替代登录链路证据。
- Run 011：统一登录日志高危接口和多账号登录详情 key extraction 已验证；高危接口偏服务端调用链视角，多账号登录偏客户端登录环境视角；token / loginToken / tokenId 等凭证明文只输出 `present_redacted`。

## 2. 已验证能力

- 页面可访问。
- 认证态复用。
- User ID 基础查询。
- 日志来源默认全勾选。
- 结果表字段读取。
- switchUser 详情弹窗部分读取。
- refreshToken 详情弹窗 key 级读取。
- sensitive field policy 已修正。
- 无结果行为 guardrail。
- 超窗行为 guardrail。
- 分页 partial_page_only guardrail。

## 3. 可稳定使用的 observation

当前可稳定使用的 observation 类型：

- query observation：记录查询对象、查询条件、日志来源 checkbox、时间范围来源。
- result_table observation：记录结果表字段、row count、total_count、page_size、pagination control。
- refreshToken detail observation：记录 refreshToken 详情弹窗 JSON key，不读取 value。
- no_result observation：记录“暂无数据”、查询条件是否保留、错误提示是否出现。
- time_window observation：记录前端可选范围、可靠窗口假设、超窗查询解释边界。
- pagination observation：记录 total_count、page_size、当前页、分页控件状态、partial_page_only。
- focused_login_risk multi_source observation：仅限同 userId 档案中心 + 用户登录统一日志的只读观察摘要；当前为 partial coverage，不是最终风险定性。
- special_event_detail observation：统一登录日志高危接口 / 多账号登录详情只读 key extraction，用于字段结构和视角识别，不输出 JSON value。

## 4. 字段保留 / 脱敏策略

统一登录日志不是“所有设备和用户字段都隐藏”。

应保留的风控证据字段：

- userId / accountId / principal 等用户标识字段。
- did / deviceId / deviceType / deviceModel 等设备字段。
- userIp / serverIp / userIpv6 / region 等网络字段。
- userAgent / appVer / appType / sysVer 等客户端字段。
- actionType / uri / method / result / reason 等行为字段。
- timestamp / dateTime / tokenCreateTime / tokenGenerateTime / tokenExpireTime / sessionCreateTime / sessionExpireTime 等时间字段。

只隐藏认证凭证明文：

- token。
- accessToken。
- refreshToken。
- session。
- sessionId。
- ticket。
- authorization。
- cookie。

重要规则：

- token 明文值必须隐藏。
- token 生成时间、过期时间、状态、类型、来源等 metadata 应保留。
- deviceId / did 是风控证据字段，不应默认隐藏。
- userId 是查询对象和证据字段，应保留。
- 如果字段名包含 token 但语义是时间、状态、类型、来源，不要 redacted。
- 如果字段语义是 accessToken / refreshToken / token value，只输出 `present_redacted`。

## 5. 核心 guardrail

- 无结果不等于用户无风险。
- 无结果不等于用户无登录记录。
- 超窗空结果不等于历史无记录。
- 前端可选超 7 天不等于长周期数据可靠。
- 只看第一页不等于已查看全量。
- 自动化翻页失败不等于没有下一页。
- 详情 JSON 可见不等于可以复制完整 JSON。
- 统一登录日志不等于替代 DataAgent / Hive / 设备平台 / 档案中心。

## 6. 仍未完成能力

- permission blocked behavior。
- full pagination traversal for unified log。
- full pagination traversal for archives user analysis。
- backend actual retention window。
- OAuth / QR 字段验证。
- request_id / trace_id 字段验证。
- risk decision 字段验证。
- nested JSON 完整性。
- device platform verification。
- audit / label logs verification。
- audit / label logs full validation。
- final release package update。
- 多源联合已完成 focused_login_risk partial coverage 验证，但未完成全分页、多平台、设备平台、审核/打标日志和最终发布验证。

## 7. 当前 release 判断

当前暂不更新 release package，但可标记为 release candidate not final。

建议状态：

```text
v2.4.8_user_login_log_hand_partially_ready
multi_source_e2e_validated_with_partial_coverage
release_candidate_not_final
```

RC plan:

```text
outputs/intermediate/dennis_risk_agent_v2_4_8_release_candidate_plan.md
```

原因：

- 单源基础能力可用。
- guardrail 已初步覆盖。
- 同 userId 多源 focused_login_risk e2e 已完成，但覆盖不完整。
- 自动化分页、权限阻断、设备平台、审核 / 打标日志仍未完成。
- 当前不应进入 final release package。

## 8. 下一步建议

P0：

- 继续补齐统一登录日志全分页遍历和档案中心用户分析全分页遍历。
- 多源 e2e 前必须先完成每个 source 的 `entry_resolution`，不得凭记忆或猜测 URL。
- 建立 agent-browser 串行锁或 session 隔离策略，避免 SPA route 污染。

P1：

- 权限阻断行为验证。
- 自动化分页 wait / scroll / selector 优化。
- 设备攻防平台验证。
- 审核 / 打标日志完整验证。

P2：

- OAuth / QR、request_id / trace_id、risk decision 字段专项验证。

## 9. 边界

- 不修改核心 Skill。
- 不更新 release package。
- 不改变 DataAgent / Hive 边界。
- 不引入自动处置或自动风险定性。
- 统一登录日志单源结果不等于多源 e2e 成功。
- 一个 source 失败时，不能把另一个 source 的 observation 包装成 multi_source observation。
- 多源 e2e 必须 `same_user_id_used=true`。
- `agent-browser` 缺少档案中心独立登录态时，应返回 `multi_source_e2e_blocked_by_archives_auth`，blocker 使用 `archives_browser_auth_blocked` / `archives_independent_login_required_for_agent_browser`；不得继续猜入口或输出半成品联合报告。
- 同一时间只允许一个 agent-browser session 操作内部平台页面；多 session 并发导致的跳转异常不得解释为页面不可用、Tab 不可访问、用户无数据或权限阻断。
- Tab 点击前必须确认 click target 属于当前页面内部 Tab 容器；若 click_target_scope=unknown，不允许点击。

## 10. Multi-source e2e entry resolution guardrail

```yaml
multi_source_e2e_entry_resolution_rule:
  required_before_execution: true
  docs_priority:
    - playbook
    - run_log
    - runtime_snapshot
    - README
  no_guess_url: true
  no_homepage_menu_exploration_as_formal_path: true
  on_missing_entry: source_entry_missing
  no_partial_single_source_wrapped_as_multi_source: true
  human_input_required_only_if_missing_docs_explained: true
  same_user_id_used_required: true
```

`source_entry_resolution` 输出格式：

```yaml
source_entry_resolution:
  source_name:
  docs_searched:
  entry_found:
  entry_url:
  validated_execution_path_found:
  selector_or_playbook_found:
  blocker:
  next_action:
```

解释规则：

- 档案中心入口缺失不等于档案中心无数据。
- 档案中心入口 404 不等于用户无档案记录。
- 用户登录统一日志 observation 只能作为单源补证，不能冒充多源联合。
