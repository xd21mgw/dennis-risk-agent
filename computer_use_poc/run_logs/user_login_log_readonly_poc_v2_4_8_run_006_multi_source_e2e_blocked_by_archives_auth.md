# User Login Log Readonly POC v2.4.8 Run 006

## v2.5.8.1 clarification

本 run 记录的是当时执行环境下的认证阻断事实，不应被泛化为“档案中心独立登录页一定失败”。

v2.5.8.1 云端内部 Agent 后续验证：

- 档案中心 direct URL 可能先跳转 `account.p.adm-corp.kuaishou.com` 独立登录页。
- 如果账号 / 用户名输入框已预填，可以先点击“下一步”尝试恢复会话。
- 点击后成功进入档案中心时，应标记 `recoverable_preflight_success=true`，且 `archives_center_profile_check.query_status=success`。
- 如果点击后仍要求密码 / 扫码 / MFA，才标记 `archives_independent_login_required`。
- 如果账号 / 用户名未预填，不得猜测账号，应等待人工登录或标记 `wait_for_manual_login`。

因此，Run 006 的 blocker 仍是历史事实，但新的通用规则应使用 `archives_independent_login_preflight_required_but_recoverable` 分支优先判断是否可恢复。

```yaml
test_stage: v2.4.8
test_type: multi_source_focused_login_risk_e2e
validation_status: multi_source_e2e_blocked_by_archives_auth

target:
  goal: 档案中心 + 用户登录统一日志同 userId focused_login_risk e2e
  user_id: "4700398885"
  same_user_id_used: true

source_entry_resolution:
  archives_center:
    completed: true
    docs_searched:
      - computer_use_poc/README.md
      - computer_use_poc/archives_center_internal_agent_playbook.md
      - computer_use_poc/archives_center_user_lookup_flow.md
      - computer_use_poc/integration_notes.md
      - computer_use_poc/failure_modes.md
      - computer_use_poc/run_logs/archives_center_userid_direct_url_run_001_validated.md
      - computer_use_poc/run_logs/archives_center_saved_state_reuse_run_001_validated.md
      - computer_use_poc/observation_contract_v2_4_6.md
      - computer_use_poc/smoke_tests.md
      - computer_use_poc/scripts/archives_user_info_quick_extract.js
    entry_found: true
    entry_url: https://admin.p.adm-corp.kuaishou.com/frontend/archives/index.html#/archives/user/profile?userId={userId}
    independent_login_domain: account.p.adm-corp.kuaishou.com
    auth_path: SSO → 档案中心独立登录 → userId direct URL
    validated_execution_path_found: true
    selector_or_playbook_found: true
    selector_or_playbook_sources:
      - computer_use_poc/archives_center_internal_agent_playbook.md
      - computer_use_poc/archives_center_user_lookup_flow.md
      - computer_use_poc/scripts/archives_user_info_quick_extract.js
      - computer_use_poc/scripts/archives_user_analysis_extract.js
      - row feature filter 规则
    blocker:
      - archives_browser_auth_blocked
      - archives_independent_login_required_for_agent_browser
    next_action: 在 agent-browser 中完成档案中心独立登录并保存 state，或在已有档案中心认证态的 Dennis Risk Agent 环境中重跑
  user_login_unified_log:
    completed: true
    entry_found: true
    query_success: true

archives_center_auth_blocker:
  archives_browser_auth_blocked: true
  archives_independent_login_required_for_agent_browser: true
  sso_session_py_http_access: true
  agent_browser_reused_sso_cookie: false
  redirect_target: account.p.adm-corp.kuaishou.com
  interpretation: sso_session.py 可 HTTP 级访问，但 agent-browser GUI 进程未复用该 cookie，因此 direct URL 被重定向到档案中心独立登录页
  required_behavior: 按 failure_modes.md 停止，不绕过认证

user_login_unified_log_observation:
  query_success: true
  user_id: "4700398885"
  total_count: 133
  page_size: 20
  visible_row_count: 20
  partial_page_only: true
  event_types_observed:
    - token 吊销
    - token 下发
    - 退出登录
    - 历史一键登录
    - 多账号登录
    - 高危接口调用
  interpretation_boundary:
    - 仅代表统一登录日志单源观察
    - 当前页不是全量结果
    - 不能包装成 multi_source observation

guardrail_check:
  no_cross_user_merge: true
  no_auto_risk_conclusion: true
  no_punishment_recommendation: true
  no_full_json_copied: true
  credential_raw_value_output: false
  partial_page_only_marked_if_needed: true
  readonly_safety_check: PASSED

e2e_result:
  e2e_joint_observation_success: false
  blocker:
    - archives_browser_auth_blocked
    - archives_independent_login_required_for_agent_browser
  correct_next_step: 人工在 agent-browser 中完成档案中心独立登录并保存 state，或在已有档案中心认证态的 Dennis Risk Agent 环境中重跑；随后再执行 Run 007：multi_source_e2e_with_archives_saved_state
```

## Clarification Note

本轮补充 Dennis 最新返回后的精确口径：

- 档案中心 `userId` direct URL 已确认：
  `https://admin.p.adm-corp.kuaishou.com/frontend/archives/index.html#/archives/user/profile?userId={userId}`
- 档案中心独立登录域已确认：
  `account.p.adm-corp.kuaishou.com`
- 认证链路为：
  SSO → 档案中心独立登录 → userId direct URL
- 本轮 userId 为：`4700398885`
- `sso_session.py` 可 HTTP 级访问，但 `agent-browser` GUI 进程未复用该 cookie。
- 因此 `agent-browser` 打开 direct URL 后仍被重定向到 `account.p.adm-corp.kuaishou.com` 独立登录页。
- 当前 blocker 更准确写法是：
  `archives_browser_auth_blocked` / `archives_independent_login_required_for_agent_browser`。

当前不是：

- entry missing。
- URL missing。
- 档案中心无结果。
- 用户无档案。
- multi-source e2e 成功。

下一步：

- 人工在 `agent-browser` 中完成档案中心独立登录并保存 state；或
- 在已有档案中心认证态的 Dennis Risk Agent 环境中重跑；然后
- 执行 Run 007：`multi_source_e2e_with_archives_saved_state`。

## 结论

本轮 multi-source e2e 没有完成。阻断原因是 `agent-browser` 没有档案中心独立登录态，不是入口文档缺失、URL 缺失、页面 404、用户无档案记录或统一登录日志失败。

本轮已验证新规则有效：Dennis 先完成 `archives_center_entry_resolution`，没有继续猜 URL；统一登录日志单源查询成功，但没有被包装为多源联合成功。

## 边界

- 不修改核心 Skill。
- 不更新 release package。
- 不改变 DataAgent / Hive 边界。
- 不引入自动处置或自动风险定性。
- 不输出认证 state、cookie、token、KIM code 或操作者身份明文。
