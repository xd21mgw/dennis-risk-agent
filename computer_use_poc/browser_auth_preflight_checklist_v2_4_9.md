# Browser Auth Preflight Checklist v2.4.9

## 1. 使用场景

适用于所有 browser computer use 平台手脚，包括：

- 档案中心
- 用户登录统一日志
- 设备 SDK / 设备基建平台
- 后续新增内部平台页面

本清单用于进入页面字段探索前的统一前置检查。它不是风险定性规则，也不是平台自动处置能力。

## 2. 执行前必须检查

### 2.1 source entry resolution

必须先确认：

- `source_name`
- `entry_url`
- `entry_url_source`：README / playbook / run log / runtime snapshot
- `validated_execution_path_found`
- `selector_or_playbook_found`

禁止：

- 凭记忆猜 URL。
- 从首页菜单随意探索作为正式路径。
- `entry missing` 时继续生成半成品报告。

标准输出：

```yaml
source_entry_resolution:
  source_name:
  entry_url:
  entry_url_source:
  validated_execution_path_found:
  selector_or_playbook_found:
  blocker:
  next_action:
```

### 2.2 browser auth preflight

标准输出：

```yaml
browser_auth_preflight:
  source_name:
  target_url:
  saved_state_name:
  saved_state_loaded:
  redirected_to_login:
  current_url:
  page_accessible:
  expected_domain:
  actual_domain:
  user_id_match_if_applicable:
  blocker:
  next_action:
```

解释规则：

- `saved_state_loaded=true` 不等于页面可访问，仍需确认 `redirected_to_login=false` 和 `current_url` 在 `expected_domain` 下。
- `page_accessible=true` 只代表页面可打开，不代表目标用户有数据。
- `user_id_match_if_applicable=true` 只用于确认查询对象一致，不代表风险判断成立。

### 2.3 saved state reuse check

必须判断：

- `saved_state` 是否存在。
- `saved_state` 是否成功加载。
- direct URL 是否打开成功。
- 是否跳转 login。
- 是否进入目标 source。
- 是否是目标 `userId`。

如果失败，只能输出：

- `auth_blocked`
- `saved_state_missing`
- `saved_state_expired`

不能输出：

- 页面无数据。
- 用户无记录。
- 用户无风险。
- 平台不可用。

### 2.4 single browser session / serial lock

要求：

- 默认 `single_browser_session=true`。
- 同一时间只允许一个 `agent-browser` 操作内部平台页面。
- 如发现其他 session 正在操作，应停止或等待。
- 多 session 并发导致的跳转异常不能解释为页面不可用。

标准输出：

```yaml
browser_session_check:
  single_browser_session:
  lock_acquired:
  existing_browser_task_detected:
  blocker:
  next_action:
```

### 2.5 redirect_to_login 判断

如果 `current_url` 跳到登录域：

- 标记 `redirected_to_login=true`。
- 标记 `auth_blocker`。
- 不继续点页面。
- 不做风险判断。

禁止解释为：

- 页面无数据。
- 用户无记录。
- 目标平台不可用。
- 目标 Tab 不存在。

### 2.5.2 sso_session.py cookie 到 agent-browser Chrome 桥接

当前半开放 runtime 中，`sso_session.py` / `sso_session_runner.py` 与 `agent-browser` Chrome session 是两个不同执行面。SSO API 能构造只读 URL 或验证 session，不代表 browser session 已经具备档案中心 / 天狮的可用登录态。

桥接前置检查：

```yaml
browser_session_bridge:
  api_sso_session_available:
  browser_chrome_profile_available:
  cookie_bridge_supported:
  target_domain:
  same_origin_fetch_possible:
  browser_page_logged_in:
  bridge_status: ready / cookie_bridge_missing / manual_login_required / unsupported
  forbidden_output:
    - cookie
    - token
    - session
    - header
```

规则：

- 不得在报告、run log、KIM 回复或调试日志中打印 cookie / token / session / header。
- 如果无法把 SSO cookie 安全注入 agent-browser Chrome，返回 `cookie_bridge_missing` 或 `permission_or_runtime_gap`。
- SSO state 存在不等于 API direct 可用；`sso_session.py` 认证注入成功不代表 browser session 或 API data fetch 一定成功。
- curl + cookie 返回 302 redirect 时，标记 `auth_session_issue`，不得把 redirect 当 no_data。
- browser fetch 必须 same-origin；未进入正确域名或跨源失败时标记 `same_origin_error`。
- agent-browser profile lock / SingletonLock 时标记 `profile_lock`，快速降级，不反复启动浏览器。
- `cookie_bridge_missing` 不等于平台无数据，不等于用户无风险。
- 不得反复重试 browser 登录导致 timeout；一次 preflight 失败后应快速降级为 partial evidence card。
- 如果同源页面已登录，可使用 same-origin fetch / DOM read；如返回 HTML auth page，应标记 `auth_session_issue`，不得当 JSON 解析。

#### 2.5.1 档案中心 independent login recoverable preflight

档案中心可能先跳转到 `account.p.adm-corp.kuaishou.com` 独立登录页。该状态是 auth preflight，不是页面无数据。
`account.p.adm-corp.kuaishou.com` 登录页也不应直接定性为 IP 白名单失败；只有明确的 AccessProxy / IP allowlist 错误页才可标 `permission_blocked`。

规则：

- 该恢复动作只允许在独立 `archives_center_auth_activation_fix` / `platform_auth_activation_task` / pre-case auth recovery 中执行；KNC / 单用户研判 / 批量研判等业务 case 中仍必须快速标 `archives_auth_session_issue`，不得现场修登录态。
- 如果页面只有账号 / 用户名输入框，且 username 已预填、已知或用户已在当前对话提供，可自动填入 username 并点击“下一步”尝试恢复会话；不得重复询问已知 username。
- 点击后进入档案中心 direct URL，标记 `recoverable_preflight_success=true`，并继续执行只读 health check。
- 点击后仍要求密码 / 扫码 / 短信 / MFA，标记 `manual_sso_required` 或 `archives_independent_login_required`，暂停等待用户手动完成。
- 如果账号 / 用户名未知且未预填，不得猜测或输入账号，应标记 `wait_for_manual_login` 或 `blocked_by_independent_login`。
- 用户完成 SSO 后必须保存 `archives_auth_state.json`，但报告和 run log 不得输出 cookie / token / session / header。
- `archives_auth_state.json` 过期或 state load 后仍跳登录页时，标记 `auth_state_expired` / `manual_sso_required`，不得泛化为 agent IP 不通内网或档案中心平台不可用。
- 禁止把登录页 / 认证页解释为页面无数据、用户无记录、档案无数据或用户无风险。
- 规则部分不得绑定具体账号名；具体预填账号只能在 run log 中作为本次运行样例记录。

保存 state 后的 health check：

1. 关闭 browser。
2. state load `archives_auth_state.json`。
3. 打开档案中心用户主页。
4. 确认未跳转登录页。
5. 在同源上下文 fetch `/archives/user/home/info?userId=...`。
6. 仅当 HTTP 200 且 `hasData=true` 时，标记 `archives_auth_health_check_passed=true`。

标准输出：

```yaml
archives_independent_login_preflight:
  redirected_to_independent_login: true
  login_domain: account.p.adm-corp.kuaishou.com
  allowed_context: archives_center_auth_activation_fix
  username_source: prefilled | user_provided | unknown
  username_prefilled:
  username_auto_filled:
  next_clicked:
  recoverable_preflight_success:
  still_requires_password_or_mfa:
  manual_sso_required:
  state_saved:
  auth_state_expired:
  health_check:
    browser_closed:
    state_loaded:
    user_home_opened:
    redirected_to_login:
    same_origin_home_info_http_status:
    hasData:
    archives_auth_health_check_passed:
  query_status_after_recovery:
  blocker:
  forbidden_interpretation:
    - 用户无记录
    - 档案无数据
    - 用户无风险
    - 平台查询成功但无风险
    - IP 白名单失败（无明确 IP / AccessProxy 证据时）
```

### 2.6 SPA route guardrail

Tab 点击前记录：

- `current_url`
- `target_tab_text`
- `target_tab_container_identified`
- `click_target_scope`

Tab 点击后校验：

- `current_url` 是否仍在目标 source。
- 是否仍为同一 `userId`。
- `target_tab` 是否 selected。
- 是否 `unexpected_route_redirect`。

标准输出：

```yaml
spa_tab_click_preflight:
  before_click:
    current_url:
    target_tab_text:
    target_tab_container_identified:
    click_target_scope:
  after_click:
    current_url:
    still_in_target_source:
    same_user_id:
    target_tab_selected:
    unexpected_route_redirect:
  blocker:
  next_action:
```

### 2.7 SPA operation loop guard

Browser / SPA sources such as 档案中心、track-analysis、天狮 / RCP must stop repeated UI operations.

Loop detection:

- Same action fails more than 3 times.
- Same dropdown / date picker / import button remains unavailable after 3 attempts.
- Repeated screenshots show the same failed UI state.
- No new structured field is extracted across repeated attempts.

Required output:

```yaml
spa_operation_loop_guard:
  operation_loop_detected:
  source_name:
  failed_action:
  failed_attempt_count:
  platform_access_partial:
  browser_overuse:
  stop_reason:
  next_action:
```

If `operation_loop_detected=true`:

- Stop browser operations for that source.
- Do not continue screenshots / clicks.
- Mark `platform_access_partial` or `partial_source`.
- Return partial evidence card.
- Suggest Hive / DataAgent query plan or manual source check if needed.

Forbidden:

- Infinite dropdown / date picker / import button retries.
- Naked timeout without partial evidence.
- Treating browser loop as no-risk or no-data evidence.

## 3. 允许进入页面字段探索的条件

只有满足以下条件，才能开始读取字段：

- `entry_found=true`
- `saved_state_loaded=true` 或无需登录
- `redirected_to_login=false`
- `page_accessible=true`
- `current_url` 在 `expected_domain` 下
- `single_browser_session=true`
- `click_target_scope` 可确认

任一条件不满足时，应停止当前 source 的页面字段探索，并返回 blocker。

## 4. 常见 blocker 及解释

| blocker | 含义 | next_action | forbidden interpretation |
| --- | --- | --- | --- |
| `source_entry_missing` | 未找到可信入口 | 回到 README / playbook / run log / runtime snapshot 补 entry | 不能说平台无数据 |
| `saved_state_missing` | 缺少可用 saved state | 先人工登录并保存 state，或换已有 state 环境 | 不能说用户无记录 |
| `saved_state_expired` | state 过期 | 重新登录并保存 state | 不能说平台不可用 |
| `redirected_to_login` | 打开目标 URL 后跳到登录页 | 停止并返回 auth blocker | 不能继续点页面，不能做风险判断 |
| `browser_context_polluted` | browser / SPA 状态被其他 session 污染 | 清理 session，串行重跑 | 不能解释为页面异常或无数据 |
| `unexpected_route_redirect` | 点击后跳出目标 source | 标记 tab_click_invalid，重新确认 click target | 不能解释为目标 Tab 不可访问 |
| `selector_scope_unknown` | 无法确认点击或选择器范围 | 停止点击，补 selector | 不能盲点全局按钮 |
| `permission_blocked` | 已登录但页面权限不足 | 返回权限阻断，提示换有权限环境或人工复核 | 不能解释为用户无数据 |
| `archives_independent_login_required` | 档案中心独立登录页无法自动恢复，仍需密码 / 扫码 / MFA | 等待人工登录或换已有认证态环境 | 不能解释为档案无数据 |
| `wait_for_manual_login` | 档案中心独立登录页账号 / 用户名未预填 | 等待人工登录 | 不能猜测账号，不能解释为用户无记录 |

## 5. 后续平台接入要求

任何新平台手脚，包括 Dennis Agent 5 设备 SDK 基建手脚，必须先完成：

```text
source_entry_resolution
→ browser_auth_preflight
→ saved_state_reuse_check
→ single_browser_session_check
→ 页面字段探索
```

接入原则：

- 先确认入口，再确认认证态，再读取字段。
- 不允许直接开始页面字段探索。
- 不允许把登录态阻断、route 污染、selector 范围不明解释成平台无数据。
- 不允许把单 source observation 包装成 multi-source success。

## 6. 边界

- 不修改核心 Skill。
- 不更新 final release package。
- 不改变 DataAgent / Hive 边界。
- DataAgent / Hive 仍只负责 Hive / 公司数仓取数分析，不替代 browser computer use。
- 不引入自动处置。
- 不引入自动风险定性。
