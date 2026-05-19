# Dennis Risk Agent v2.4.8 User Login Log Hand Runtime Snapshot

## 1. 当前状态

```yaml
user_login_log_hand_status: v2.4.8_user_login_log_hand_partially_ready
release_status: release_candidate_not_final
not_fully_validated: true
```

用户登录统一日志已经具备作为 Dennis Agent 最近实时登录链路补证手脚的基础能力。Run 007 已完成同 userId 多源 e2e partial coverage 验证，但尚不满足 fully validated / final release ready。

## 2. 已完成 run logs

- Run 001: page_accessibility partially_validated。
- Run 002: switchUser detail partially_validated。
- Run 003: refreshToken detail validated for readonly JSON key extraction。
- Run 004: no_result / time_window boundary partially_validated。
- Run 005: pagination behavior partially_validated。
- Run 006: multi_source_entry_resolution validated；multi_source_e2e blocked_by_archives_auth。
- Run 007: multi_source_e2e validated_with_partial_coverage。
- Run 008: archives_saved_state_reuse validated。
- Run 009: archives_user_analysis_pagination_behavior validated_with_correction。
- Run 010: archives_audit_label_log_access partially_validated。
- Run 011: unified_log_special_event_detail validated。

当前统一状态：

```yaml
user_login_log_hand: partially_ready
multi_source_entry_resolution: validated
archives_saved_state_e2e: validated
archives_saved_state_reuse: validated
multi_source_e2e: validated_with_partial_coverage
archives_user_analysis_pagination: validated_with_correction
archives_audit_label_log_access: partially_validated
unified_log_special_event_detail: validated
e2e_joint_observation_success: true
multi_source_schema_ready: focused_login_risk_observation_only
release_status: release_candidate_not_final
```

Run 006 关键事实：

- 目标：档案中心 + 用户登录统一日志同 `user_id=4700398885` focused_login_risk e2e。
- Dennis 已按规则完成 `archives_center_entry_resolution`，并确认档案中心入口、playbook、lookup flow、历史 run log、observation contract、smoke tests 和 scripts。
- 档案中心入口与 selector/playbook 已找到。
- e2e 阻断原因：`agent-browser` 档案中心独立登录态阻断，`archives_browser_auth_blocked=true`、`archives_independent_login_required_for_agent_browser=true`。
- 档案中心 `userId` direct URL 已确认：`https://admin.p.adm-corp.kuaishou.com/frontend/archives/index.html#/archives/user/profile?userId={userId}`。
- 档案中心独立登录域已确认：`account.p.adm-corp.kuaishou.com`。
- 认证链路为：SSO → 档案中心独立登录 → userId direct URL。
- `sso_session.py` 可 HTTP 级访问，但 `agent-browser` GUI 进程未复用该 cookie，因此 direct URL 被重定向到独立登录页。
- 统一登录日志单源查询成功：`total_count=133`、`page_size=20`、`visible_row_count=20`、`partial_page_only=true`。
- 统一登录日志单源结果不能包装成 multi-source e2e 成功。

Run 007 关键事实：

- 同一 `user_id=4700398885` 下，档案中心 + 用户登录统一日志 multi-source e2e 已跑通。
- 档案中心 direct URL 成功访问，认证态已解决并保存 state：`archives_center_4700398885_20260519`。
- 档案中心可见用户主页、用户分析 Tab、APP端核心操作日志；时间范围约 6 个月，当前仅部分覆盖。
- 统一登录日志可见 `total_count=133`、`page_size=20`、`visible_row_count=20`，当前仅第一页，`partial_page_only=true`。
- 跨源 DID 一致，历史一键登录 / 退出登录行为可对齐。
- 当前 `multi_source_schema_ready` 仅限 `focused_login_risk_observation_only`。
- 不代表自动风险定性完成、全量历史数据已查看、设备攻防平台已验证、审核 / 打标日志已查看或最终风险结论已生成。

Run 008 ~ Run 011 关键事实：

- Run 008：`archives_center_4700398885_20260519` saved state 复用已验证，档案中心独立登录 blocker 对该 state 当前已解决。
- Run 009：档案中心用户分析存在分页，样例 `total_count=1181`、`page_size=10`；此前“无分页 / 无限滚动”结论作废，未遍历全部分页前必须 `partial_coverage=true`。
- Run 010：档案中心审核日志 / 打标日志可访问性部分验证；审核 / 打标日志只作为补充 source。
- Run 011：统一登录日志高危接口 / 多账号登录详情 key extraction 已验证；凭证明文字段只输出 `present_redacted`。

## 3. 当前可用能力

- 可打开统一登录日志页面。
- 可按 User ID 查询。
- 可读取结果表。
- 可读取 refreshToken 详情 JSON key。
- 可读取部分 switchUser 详情。
- 可记录 total_count / page_size / partial_page_only。
- 可处理无结果、超窗、分页的防误判解释。
- 可在同 userId 下消费档案中心 + 用户登录统一日志 focused_login_risk multi-source observation，但当前覆盖仍为 partial。
- 可使用统一登录日志 special event detail key extraction 作为字段结构和视角补充；不输出 JSON value。

## 4. 关键 guardrail

- 无结果不等于无风险。
- 无结果不等于用户无登录记录。
- 超窗空结果不等于历史无记录。
- 前端可选超 7 天不等于长周期数据可靠。
- 只看第一页不等于已查看全量。
- 自动化翻页失败不等于没有下一页。
- 详情 JSON 可见不等于可以复制完整 JSON。
- 统一登录日志不替代 DataAgent / Hive / 设备平台 / 档案中心。

## 5. 字段保留与脱敏策略

### retain

- userId
- accountId
- principal
- did
- deviceId
- deviceType
- deviceModel
- userIp
- serverIp
- userIpv6
- region
- userAgent
- appVer
- appType
- sysVer
- actionType
- uri
- method
- result
- reason
- timestamp
- dateTime
- tokenCreateTime
- tokenGenerateTime
- tokenExpireTime
- sessionCreateTime
- sessionExpireTime
- tokenType
- tokenStatus
- tokenSource
- refreshReason

### redact_raw_value_only

- token
- accessToken
- refreshToken
- session
- sessionId
- ticket
- authorization
- cookie
- credential
- secret
- rawAuthHeader

## 6. 使用建议

- Dennis 在 focused_login_risk 场景中，可以把用户登录统一日志作为最近实时登录链路补证 source。
- 默认不主动改时间。
- 如果用户要求查超过最近 7 天，必须标记 `over_reliable_realtime_window=true`。
- 如果 `total_count > visible_row_count`，必须标记 `partial_page_only=true`。
- 即使 Run 007 多源 e2e 已跑通，也不要把用户登录统一日志或 multi-source observation 写成 fully validated；当前仅为 focused_login_risk partial coverage。

## 7. 下一步

P0:

- 固化 Run 007 的 focused_login_risk multi-source observation schema。
- 多源 e2e 前必须继续完成每个 source 的 `entry_resolution`，优先读取已有 playbook / run log / runtime snapshot / README，不允许猜 URL。
- 执行 v2.4.9 `browser_auth_preflight` 清单：`computer_use_poc/browser_auth_preflight_checklist_v2_4_9.md`。后续任何平台手脚必须按 `source_entry_resolution → browser_auth_preflight → saved_state_reuse_check → single_browser_session_check → 页面字段探索` 顺序执行。
- 补齐统一登录日志全分页遍历和档案中心用户分析全分页遍历。
- 建立 agent-browser 串行锁或 session 隔离策略。

P1:

- 权限阻断行为。
- 自动化分页 wait / scroll / selector 优化。
- 设备攻防平台验证。
- 审核 / 打标日志验证。

P2:

- OAuth / QR、request_id / trace_id、risk decision 字段专项验证。

## 8. 边界

- 不修改核心 Skill。
- 不更新 release package。
- 不改变 DataAgent / Hive 边界。
- 不引入自动处置或自动风险定性。
- 统一登录日志单源结果不等于多源 e2e 成功。
- 一个 source 失败时，不能把另一个 source 的 observation 包装成 multi_source observation。
- 多源 e2e 必须 `same_user_id_used=true`。
- `agent-browser` 缺少档案中心独立登录态时，应标记 `multi_source_e2e_blocked_by_archives_auth`，blocker 使用 `archives_browser_auth_blocked` / `archives_independent_login_required_for_agent_browser`；下一步是完成 agent-browser 档案中心独立登录并保存 state 后重跑，不是继续猜入口。
- Run 007 成功只代表 `validated_with_partial_coverage`；不能解释为 final release ready 或最终风险结论完成。
- 当前 RC plan：`outputs/intermediate/dennis_risk_agent_v2_4_8_release_candidate_plan.md`。
- 同一时间只允许一个 agent-browser session 操作内部平台页面；Tab 点击必须确认目标属于当前页面内部 Tab 容器。

## 9. Multi-source e2e entry resolution

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

每个 source 必须输出：

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

Guardrail:

- 档案中心入口缺失不等于档案中心无数据。
- 档案中心入口 404 不等于用户无档案记录。
- 统一登录日志单源结果不等于多源 e2e 成功。
- `browser_auth_preflight` 未通过时，只能返回 blocker；不得把登录态阻断、saved state 缺失、SPA route 污染或 selector 范围不明解释成页面无数据、用户无记录、用户无风险或平台不可用。
