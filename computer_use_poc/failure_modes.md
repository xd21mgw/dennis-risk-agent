# Failure Modes

## 1. 未登录

- 表现：进入登录页、登录态过期、需要扫码登录。
- 返回：`login_status=not_logged_in`
- 动作：停止，不尝试登录或绕过验证。

## 2. 无权限

- 表现：403、无权限提示、权限申请页。
- 返回：`permission_status=no_permission`
- 动作：停止，不提交权限申请。

## 3. VPN / 办公网不可用

- 表现：页面无法访问、网络超时、域名不可达。
- 返回：`network_status=vpn_required` 或 `network_status=failed`
- 动作：停止，提示需确认网络环境。

## 4. 页面加载失败

- 表现：白屏、长时间 loading、资源加载失败。
- 返回：`page_status=load_failed`
- 动作：可提示重试，但不连续刷新和不批量尝试。

## 5. 搜索无结果

- 表现：页面提示无用户、无记录或空列表。
- 返回：`page_status=no_result`
- 动作：不要解释为无风险；提示核对 user_id 和平台覆盖范围。

## 5.1 USER_NOT_FOUND

- 触发条件：URL direct userId 不存在、非法或超出有效范围。
- 识别信号：
  - saved state 有效或已登录。
  - 无重定向。
  - 无需重新登录。
  - SPA 渲染成功。
  - 页面显示用户不存在。
  - 用户详情核心 Tab 缺失。
  - `user_header_match=false`。
- 返回：
  - `page_status=user_not_found`
  - `expected_failure=true`
  - `failure_type=USER_NOT_FOUND`
  - `safe_to_continue=false`
  - `readonly_safety_check=PASSED`
- 动作：停止本次用户详情研判，返回 failure_reason，提示用户更换或核对 `user_id`。
- 边界：不得误判为登录失败、权限失败或系统异常；也不得解释为目标用户无风险。

## 6. user_id 格式错误

- 表现：输入为空、多个 ID、非用户 ID。
- 返回：`failure_reason=invalid_user_id`
- 动作：停止，要求补充单个 user_id。

## 7. 字段不可见

- 表现：页面模块存在但字段为空、隐藏、脱敏或无权限。
- 返回：写入 `hidden_or_missing_modules` 或 `sensitive_fields_visible`
- 动作：不得编造字段值。

## 8. 页面结构变化

- 表现：入口、Tab、字段名与流程不一致。
- 返回：`failure_reason=page_structure_changed`
- 动作：停止或只记录已确认可见模块。

## 9. 出现写操作风险按钮

- 表现：页面出现处置、封禁、解封、保存、审批、导出等按钮。
- 返回：`readonly_safety_check=stopped_due_to_write_risk`
- 动作：不点击，继续观察安全区域或停止。

## 10. 页面弹窗阻塞

- 表现：公告、权限提示、二次确认、合规提示遮挡页面。
- 返回：`failure_reason=popup_blocked`
- 动作：不点击确认类按钮；如弹窗可安全关闭且不涉及写操作，可关闭后继续。

## 11. SSO 已认证但档案中心仍需独立登录

- 表现：SSO KIM Code 已通过，但进入 `account.p.adm-corp.kuaishou.com` 后仍要求档案中心独立登录。
- 返回：`login_status=archives_independent_login_required`
- 动作：停止或等待人工完成独立登录；不绕过认证。

## 12. 档案中心独立登录 required

- 表现：页面明确提示需要档案中心账号登录或重新认证。
- 返回：`failure_reason=archives_independent_login_required`
- 动作：停止，不自动输入账号密码。

## 13. saved state expired

- 表现：复用 state 后被重定向到登录页或提示登录态过期。
- 返回：`failure_reason=saved_state_expired`
- 动作：停止，要求重新人工认证。

## 13.1 STATE_EXPIRED_RELOGIN_REQUIRED

- 表现：saved state 过期后回到档案中心独立登录页。
- 返回：
  - `state_reuse_status=EXPIRED_RELOGIN_REQUIRED`
  - `failure_type=STATE_EXPIRED_RELOGIN_REQUIRED`
- 动作：不误判为权限失败；可通过人工重新登录并保存新 state 恢复。
- 边界：重新登录过程仍不得记录密码、token、cookie、session、KIM code 或认证 header。

## 14. saved state domain mismatch

- 表现：state 存在但无法应用到当前域名，或跨域 cookie 不生效。
- 返回：`failure_reason=saved_state_domain_mismatch`
- 动作：停止，重新确认 state 生成域名和目标域名。

## 15. SPA rendered but sensitive fields must be redacted

- 表现：SPA 渲染成功，同时页面展示用户名、手机号、设备 ID、IP、昵称、快手号等敏感字段。
- 返回：`page_status=user_home_visible`，并在 `sensitive_fields_visible` 中标记字段可见但值已 redacted。
- 动作：继续只读观察，但不得输出明文敏感值。

## 16. operator identity visible in nav menu

- 表现：页面导航栏、右上角头像、账号菜单、登录信息中展示当前登录操作者身份。
- 返回：在 `identity_context.nav_menu` 中记录 `object_type=operator_account`、`value_policy=operator_identity_redacted`。
- 动作：不得输出操作者账号名、头像、邮箱、工号或任何可识别身份信息。

## 17. target object header visible

- 表现：页面头部展示查询目标用户信息，可用于核验页面对象。
- 返回：在 `identity_context.user_header` 中记录 `object_type=target_user`、`user_id_match=true/false/unknown`。
- 动作：仅保留必要核验信息；如果 user_id 不匹配，返回 `failure_reason=query_value_page_mismatch`。

## 18. LOADED_EMPTY_OR_NO_ROWS

- 表现：Tab 加载成功，但当前筛选条件下没有数据行。
- 返回：
  - `tab_status=loaded_empty_or_no_rows`
  - 记录当前筛选条件和时间范围。
- 动作：不得解释为没有风险、没有行为或没有审核记录。
- 适用：审核日志、用户分析、视频作品集等列表型 Tab。
