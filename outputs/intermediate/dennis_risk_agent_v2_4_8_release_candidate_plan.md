# Dennis Risk Agent v2.4.8 Release Candidate Plan

## 1. 当前 RC 状态

```yaml
release_candidate_status: v2.4.8_user_login_log_hand_release_candidate_not_final
```

## 2. 可进入 RC 的能力

- 用户登录统一日志单源 hand。
- 档案中心 + 统一登录日志同 userId focused_login_risk observation。
- source entry resolution。
- saved state e2e。
- saved state reuse。
- no_result / time_window / pagination guardrail。
- sensitive field retain/redact policy。
- 档案中心用户分析分页 guardrail。
- 审核日志 / 打标日志补充 source 可访问性。
- 统一登录日志 special event detail key extraction。

## 3. 不能进入 final release 的原因

- full pagination traversal 未完成。
- permission blocked behavior 未完成。
- 设备攻防平台未验证。
- 审核 / 打标日志未完整验证。
- 当前仅支持 focused_login_risk_observation_only。
- 不支持自动风险定性 / 自动处置。

## 4. RC 使用边界

- 只读。
- 同 userId。
- 不跨源拼接不同 userId。
- 不输出处罚建议。
- 不复制完整 JSON。
- token / session / ticket / authorization / loginToken / tokenId 等凭证明文只输出 `present_redacted`。
- `partial_page_only` / `partial_coverage` 必须保留。
- table container scroll 与 page body scroll 必须区分。
- Tab 点击前必须确认 click target 属于当前页面内部 Tab 容器。
- 同一时间只允许一个 agent-browser session 操作内部平台页面，避免 SPA route 污染。

## 5. 下一步进入 final release 前的条件

- 至少完成统一登录日志全分页遍历策略。
- 至少完成档案中心用户分析分页遍历策略。
- 至少补一轮 permission blocked 行为。
- 明确是否接设备攻防平台。
- 明确审核 / 打标日志是否纳入 focused_login_risk。
- 明确 agent-browser 串行锁或 session 隔离策略。

## 6. 当前统一状态

```yaml
user_login_log_hand: partially_ready
multi_source_entry_resolution: validated
archives_saved_state_e2e: validated
archives_saved_state_reuse: validated
multi_source_e2e: validated_with_partial_coverage
archives_user_analysis_pagination: validated_with_correction
archives_audit_label_log_access: partially_validated
unified_log_special_event_detail: validated
release_status: release_candidate_not_final
```

仍未完成：

- unified_log_full_pagination_traversal。
- archives_user_analysis_full_pagination_traversal。
- permission_blocked_behavior。
- device_platform_verification。
- audit_label_log_full_validation。
- final_release_package_update。

## 7. 边界

- 不修改核心 Skill。
- 不改变 DataAgent / Hive 边界。
- 不引入自动处置或自动风险定性。
- 不更新 final release package。
