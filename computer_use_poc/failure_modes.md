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

## 14. saved state domain mismatch

- 表现：state 存在但无法应用到当前域名，或跨域 cookie 不生效。
- 返回：`failure_reason=saved_state_domain_mismatch`
- 动作：停止，重新确认 state 生成域名和目标域名。

## 15. SPA rendered but sensitive fields must be redacted

- 表现：SPA 渲染成功，同时页面展示用户名、手机号、设备 ID、IP、昵称、快手号等敏感字段。
- 返回：`page_status=user_home_visible`，并在 `sensitive_fields_visible` 中标记字段可见但值已 redacted。
- 动作：继续只读观察，但不得输出明文敏感值。
