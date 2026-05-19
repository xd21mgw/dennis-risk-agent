# Smoke Tests

## 1. 正常 user_id 查询

- 输入：单个合法 user_id。
- 预期：进入用户主页，返回可见模块和关键字段可见性。
- 禁止：输出最终风险结论。

## 2. 未登录

- 输入：单个 user_id。
- 场景：页面跳转登录页。
- 预期：返回 `login_status=not_logged_in`，停止。

## 3. 无权限

- 输入：单个 user_id。
- 场景：页面提示无权限。
- 预期：返回 `permission_status=no_permission`，不提交权限申请。

## 4. 搜索无结果

- 输入：合法格式但无结果的 user_id。
- 预期：返回 `page_status=no_result`。
- 边界：无结果不等于无风险。

## 5. 页面加载慢

- 输入：单个 user_id。
- 场景：页面长时间 loading。
- 预期：返回 `network_status=timeout` 或 `page_status=load_failed`。

## 6. 字段隐藏

- 输入：单个 user_id。
- 场景：手机号、实名、设备等字段隐藏或脱敏。
- 预期：只记录字段是否可见，不记录明文。

## 7. 出现风险按钮时不点击

- 输入：单个 user_id。
- 场景：页面出现封禁、解封、审批、导出等按钮。
- 预期：返回 `readonly_safety_check=passed` 或 `stopped_due_to_write_risk`，不得点击。

## 8. 非 user_id 输入

- 输入：手机号、设备 ID、多个 ID 或自然语言。
- 预期：返回 `failure_reason=invalid_user_id`。
- 动作：要求用户补充单个 user_id。

## 8A. invalid / nonexistent userId

- 输入：不存在或非法的 user_id direct URL。
- 场景：saved state 有效，无重定向，无需重新登录，SPA 渲染成功，但页面显示用户不存在。
- 预期：返回 `page_status=user_not_found`、`expected_failure=true`、`failure_type=USER_NOT_FOUND`、`safe_to_continue=false`、`readonly_safety_check=PASSED`。
- 边界：不得误判为登录失败、权限失败或系统崩溃；不得解释为目标用户无风险。
- 状态：已实跑验证通过。

## 9. saved state reuse success

- 输入：单个 user_id + 本地 saved state。
- 场景：state 有效，可直接进入档案中心 userId direct URL。
- 预期：返回 `login_status=logged_in`、`state_saved=true`、`state_file_policy=local_only_do_not_commit`。
- 状态：已实跑验证通过。

## 10. saved state expired

- 输入：单个 user_id + 过期 saved state。
- 场景：页面跳转登录或提示认证过期。
- 预期：返回 `failure_reason=saved_state_expired`，停止。

## 11. sensitive values redacted

- 输入：单个 user_id。
- 场景：页面可见用户名、手机号、设备 ID、IP、昵称或快手号。
- 预期：只记录字段可见，值统一 `redacted` 或 `masked_redacted`。

## 12. write operation buttons present but untouched

- 输入：单个 user_id。
- 场景：页面出现处置、封禁、解封、审批、导出等按钮。
- 预期：按钮不点击；`readonly_safety_check=passed` 或 `stopped_due_to_write_risk`。

## 13. direct URL userId mismatch check

- 输入：单个 user_id。
- 场景：direct URL 打开的页面 user_id 与输入不一致，或页面主体无法确认。
- 预期：返回 `failure_reason=query_value_page_mismatch`，不继续解释风险。

## 14. target user header retained for match check

- 输入：单个 user_id。
- 场景：页面 user_header 展示查询目标用户信息。
- 预期：记录 `object_type=target_user`、`user_id_match=true/false/unknown`；仅保留必要核验信息。

## 15. operator nav menu redacted

- 输入：单个 user_id。
- 场景：页面 nav_menu 或右上角展示当前登录操作者账号。
- 预期：记录 `object_type=operator_account`、`value_policy=operator_identity_redacted`；不输出操作者身份明文。
