# v2.4.9 Browser Auth State Stabilization Plan

## 1. 背景

v2.4.8 用户登录统一日志 + 档案中心 e2e 实验中，多次暴露出 browser computer use 的认证态、saved state、SPA route 状态和 agent-browser session 并发问题。

这些问题不是单个平台字段解析问题，而是所有后续平台手脚复用时都必须先解决的运行态稳定性问题。

v2.4.9 的目标是沉淀 browser auth state stabilization 规范，作为后续档案中心、用户登录统一日志、设备 SDK 基建平台等只读平台查询的共同前置规则。

## 2. 当前问题

### 2.1 认证态隔离

- `sso_session.py` 的 HTTP cookie 与 `agent-browser` GUI cookie 不共享。
- HTTP 级访问成功不代表 browser computer use 进程已具备同一登录态。
- 档案中心存在独立登录域，SSO 成功后仍可能需要在 `agent-browser` 中完成平台独立登录。

### 2.2 agent-browser session 隔离不足

- 当前 `agent-browser` 是单 daemon / 单 Chrome 进程架构。
- `--session` 不能提供真正并行隔离。
- `--profile` 在 daemon 已启动后不能可靠切换。
- 多个 Dennis / browser session 同时访问内部平台页面，可能共享 cookie、localStorage、sessionStorage 和 SPA route state。

### 2.3 SPA route 污染

- 多 session 并发或错误点击可能污染后台 SPA 路由。
- Tab 点击、分页、弹窗、saved state 保存等操作如果不在单 session 下执行，容易出现跳转到其他 source、Tab 误点、页面状态错读。
- route redirect 不能解释为页面无数据、用户无记录、权限无数据或目标 Tab 不可访问。

### 2.4 saved state 生命周期不明确

- saved state 可复用，但复用成功依赖：
  - state 文件存在；
  - state 未过期；
  - state 对应目标域；
  - 当前 browser profile / workspace 能加载该 state；
  - 平台独立登录态仍有效。
- state 失效时应进入 auth blocked / relogin required，而不是继续探索页面或输出半成品 observation。

## 3. 短期策略

v2.4.9 短期采用保守稳定策略：

- 默认单 browser session。
- browser computer use 操作串行执行。
- 使用 lock / flag 避免多个 Dennis 同时操作内部平台页面。
- 每次平台操作前先做 `saved_state_reuse_check`。
- 每次页面打开后检查 `current_url` 是否跳到登录域。
- `current_url` 跳到 login 时标记 `auth_blocked`，停止本轮平台查询。
- 不绕过权限，不尝试自动规避登录流程。
- 认证态阻断只说明当前 browser 执行环境不可用，不说明目标用户无数据或平台无结果。

推荐短期状态：

```yaml
browser_execution_policy:
  default_session_mode: single_browser_session
  parallel_browser_sessions_allowed: false
  lock_required: true
  saved_state_reuse_check_required: true
  redirect_to_login_check_required: true
  on_auth_blocked: stop_and_return_blocker
```

## 4. 标准前置检查

所有 browser computer use 平台手脚在正式读取页面字段前，必须先输出 `browser_auth_preflight`。

```yaml
browser_auth_preflight:
  source_name:
  target_url:
  saved_state_name:
  saved_state_loaded:
  redirected_to_login:
  current_url:
  page_accessible:
  user_id_match_if_applicable:
  blocker:
  next_action:
```

字段解释：

| 字段 | 含义 | 解释规则 |
| --- | --- | --- |
| source_name | 平台 source 名称 | 例如 archives_center / user_login_unified_log / device_sdk_platform |
| target_url | 本轮目标 URL | 必须来自已验证 playbook / run log / routing index，不允许猜测 |
| saved_state_name | 本轮尝试加载的 state 名称 | 若无 state，应明确为空 |
| saved_state_loaded | state 是否加载成功 | 成功不代表页面已可访问，仍需检查 URL 和页面 |
| redirected_to_login | 是否跳转登录页 | true 时必须停止 |
| current_url | 当前页面 URL | 用于判断是否仍在目标 source 下 |
| page_accessible | 页面是否可访问 | 只表示页面打开成功，不等于有数据 |
| user_id_match_if_applicable | 页面目标对象是否与 query user_id 匹配 | 仅适用于 userId direct URL 或用户详情页 |
| blocker | 阻断原因 | 如 auth_blocked / permission_blocked / source_entry_missing |
| next_action | 下一步动作 | 如重新登录保存 state、换环境重跑、停止 observation |

## 5. 对后续 Dennis Agent 5 的要求

设备 SDK 基建手脚正式接入前，必须先完成 `browser_auth_preflight`。

要求：

- 不能直接开始页面字段探索。
- 不能凭记忆或猜测平台入口。
- 不能从首页菜单随意探索作为正式执行路径。
- 不能把登录态阻断解释成页面无数据。
- 不能把登录态阻断解释成权限无数据。
- 不能把 HTTP 脚本态认证成功当作 browser GUI 态认证成功。
- 如果 `browser_auth_preflight.blocker` 不为空，应停止该 source 的 observation。
- 如果多源 e2e 中某个 source auth blocked，不能把其他 source 的 observation 包装成 multi-source success。

设备 SDK 基建手脚接入前置状态建议：

```yaml
device_sdk_platform_onboarding_precondition:
  source_entry_resolution_required: true
  browser_auth_preflight_required: true
  saved_state_profile_defined: true
  single_browser_session_required: true
  no_field_exploration_before_auth_ready: true
```

## 6. 下一步

### P0：统一 source entry + auth preflight

- 为档案中心、统一登录日志、设备 SDK 平台分别定义：
  - source_name；
  - canonical entry URL；
  - auth path；
  - saved state 名称；
  - redirect_to_login 判断规则；
  - permission_blocked 判断规则。
- 将 `source_entry_resolution` 与 `browser_auth_preflight` 串起来：
  1. 先确认 entry 来自文档；
  2. 再确认 browser 认证态；
  3. 再开始页面只读 observation。

### P1：统一 browser lock 规则

- 建立任务级互斥规则。
- 同一时间只允许一个 agent-browser session 操作内部平台。
- 记录 `single_browser_session=true / false`。
- 若已有任务运行，后续任务应等待或返回 `browser_session_busy`。

### P1：统一 redirect_to_login 判断

- 档案中心：
  - 登录域：`account.p.adm-corp.kuaishou.com`
  - direct URL 跳转登录域时标记 `archives_browser_auth_blocked`。
- 用户登录统一日志：
  - 若跳转登录页或 SSO 页面，标记 `user_login_log_auth_blocked`。
- 设备 SDK 平台：
  - 待接入前补充。

### P2：长期并发隔离方案

如后续确实需要并发，再考虑改造 agent-browser CLI / daemon：

- 每个 session 独立 Chrome process。
- 每个 session 独立 user-data-dir。
- 每个 daemon 独立 CDP port。
- 避免共享 cookie / localStorage / sessionStorage / SPA route state。

## 7. 统一边界

- 不修改核心 Skill。
- 不更新 final release package。
- 不改变 DataAgent / Hive 边界。
- DataAgent / Hive 仍只负责 Hive / 公司数仓取数分析，不替代 browser computer use。
- 不引入自动处置。
- 不引入自动风险定性。
- browser computer use observation 只作为只读平台观察结果，风险结论仍由 Dennis 基于多证据综合输出。
