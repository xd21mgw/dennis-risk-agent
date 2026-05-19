# v2.4.8 Multi-source E2E Lessons Learned

本文沉淀档案中心 + 用户登录统一日志同 userId focused_login_risk e2e 的执行教训。它是执行 guardrail，不是风险定性规则。

## 1. 核心教训

- 不要猜 URL，先做 `entry_resolution`。
- 404 / 登录跳转不等于无数据。
- 浏览器态和脚本态认证分离：HTTP 级认证可用不代表 `agent-browser` GUI 进程已复用 cookie。
- AJAX / 分页 / 弹窗需要等待策略，不能把自动化点击失败解释成页面无结果。
- `partial_page_only` 是默认保守规则：只要未覆盖全部分页，就不能说已查看全量。
- multi-source observation 必须同 `userId`，否则不得合并。
- page body scroll 和 table container scroll 必须区分；档案中心用户分析此前“无分页 / 无限滚动”判断已被 Run 009 修正。
- 后台 SPA 多 session 并发可能污染路由状态；当前 agent-browser 必须串行执行。
- Tab 点击成功不等于进入正确 Tab，必须校验 current_url、同 userId、Tab selected 和内容区。

## 2. 成功经验

- 同 userId multi-source observation 可行。
- 档案中心和统一登录日志分工清晰：
  - 档案中心提供长期画像：账号状态、风控等级、设备型号、地域、用户分析日志。
  - 统一登录日志提供实时链路：token 生命周期、登录方式、高危接口、多账号登录、精确时间戳。
- DID / 登录方式 / 退出登录 / token 生命周期是稳定对齐锚点。
- saved state 是档案中心 e2e 成功前置；没有 `agent-browser` 档案中心独立登录态时，应先解决认证态再重跑。
- `archives_center_4700398885_20260519` saved state 复用已验证，可提升同 userId e2e 重跑稳定性。
- 审核日志 / 打标日志可作为补充 source，但不替代登录链路证据。
- 统一登录日志 special event detail key extraction 可区分服务端调用链视角和客户端登录环境视角。

## 3. 固化 guardrail

- 无结果不等于无风险。
- 404 不等于无数据。
- 登录阻断不等于用户无档案。
- 单源 observation 不等于 multi-source success。
- 只看第一页不等于全量。
- 自动化翻页失败不等于没有下一页。
- HTTP 认证成功不等于浏览器认证成功。
- e2e observation 成功不等于风险定性完成。
- multi-source e2e 必须 `same_user_id_used=true`。
- 只看第一页不等于全量；档案中心用户分析和统一登录日志均需要分页 guardrail。
- Tab redirect 不能解释为目标 Tab 不可访问、无权限、无数据或无结果。
- 多 session 并发导致的跳转异常不得解释为平台能力失败。
- 凭证明文字段如 token / loginToken / tokenId / session / ticket / authorization 只能输出 `present_redacted`。

## 4. 后续执行要求

v2.4.9 已将这些执行教训沉淀为统一前置检查清单：

`computer_use_poc/browser_auth_preflight_checklist_v2_4_9.md`

任何平台手脚必须按以下顺序执行：

```text
source_entry_resolution
→ browser_auth_preflight
→ saved_state_reuse_check
→ single_browser_session_check
→ 页面字段探索
```

任何 multi-source e2e 前，执行器必须先输出：

```yaml
source_entry_resolution:
  source_name:
  docs_searched:
  entry_found:
  entry_url:
  auth_path:
  saved_state_required:
  saved_state_available:
  selector_or_playbook_found:
  blocker:
  next_action:
```

只有所有必要 source 的 `entry_resolution` 成功，且认证态可用，才允许进入 e2e observation。

如果任何必要 source entry 或认证态失败：

- 返回对应 blocker。
- 不输出半成品 multi-source 报告。
- 不把成功 source 的 observation 包装成 multi-source success。
- 不要求用户手动执行平台查询，除非明确标记 `human_input_required=true` 且说明缺失文档项。
- 不把登录态阻断、saved state 缺失、SPA route 污染或 selector 范围不明解释成页面无数据、用户无记录、用户无风险或平台不可用。

## 5. 状态口径

当前 Run 007 的状态是：

```yaml
multi_source_e2e: validated_with_partial_coverage
multi_source_schema_ready: focused_login_risk_observation_only
release_status: release_candidate_not_final
```

Run 008 ~ Run 011 后的补充状态：

```yaml
archives_saved_state_reuse: validated
archives_user_analysis_pagination: validated_with_correction
archives_audit_label_log_access: partially_validated
unified_log_special_event_detail: validated
release_status: release_candidate_not_final
```

不代表：

- 自动风险定性完成。
- 全量历史数据已查看。
- 设备攻防平台已验证。
- 审核 / 打标日志已查看。
- 最终风险结论已生成。
