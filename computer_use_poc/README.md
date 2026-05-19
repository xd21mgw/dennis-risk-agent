# Computer Use Readonly POC

## 1. POC 目标

验证 Dennis Risk Agent 是否可以通过内部 computer use / browser automation 环境，完成最小只读平台查询动作。

本 POC 只验证一个动作：

输入 `user_id`，打开档案中心，执行只读查询，返回结构化 observation。

## 2. 范围

- 平台：档案中心。
- 查询对象：单个 `user_id`。
- 操作类型：只读页面查询和页面信息观察。
- 输出：结构化 observation，不输出最终风险定性。

## 3. 非目标

- 不做多平台联动。
- 不做批量查询。
- 不做任何写操作、提交、处置、审批、封禁、解封、导出。
- 不绕过权限。
- 不自动形成处罚、冻结、解封、策略上线建议。
- 不替代 Dennis Risk Agent 的风险判断。

## 4. 与 v2.4.3 的关系

v2.4.3 internal platform routing patch 负责：

- 判断应该查哪个平台。
- 解释平台字段和边界。
- 给出跨平台取证路径。

computer use readonly POC 负责：

- 验证只读页面操作是否可行。
- 将页面可见信息整理为 observation。
- 把查询失败、权限不足、页面异常等情况结构化返回。

二者关系：

先由 `internal_risk_platforms/00_platform_routing_index.md` 判断是否应查档案中心，再由本 POC 执行档案中心只读查询。

## 5. 当前状态

当前状态：

```text
v2.4.4-computer-use-readonly-poc-validated
```

最新 P0 深读状态：

```text
v2.4.5 archives center user profile P0 tabs deep-read validated
```

已验证：

- 档案中心 `userId` direct URL 只读查询链路可用。
- 完整认证路径为 SSO KIM Code → 档案中心独立登录 → userId 直达详情页。
- saved state 复用已验证：加载已保存的档案中心认证 state 后，可直接打开 userId direct URL，无重定向，无需重新登录。
- 档案中心 SPA 可完整渲染。
- 页面可识别用户信息、审核日志、打标日志、用户分析、视频作品集、直播作品集、粉丝列表、关注列表、合集列表、收藏列表、动态列表等 Tab。
- 页面可识别基本信息、用户实时负向、最近登录、最近启动、注册信息、账户信息、同设备登录/注册入口等模块。
- target object / operator account 身份信息分层规则已补齐：`user_header` 可用于核验查询目标，`nav_menu` 当前登录操作者信息必须 redacted。
- 敏感字段策略已分层：认证票据类永远 `never_collect`；IP、设备 ID、手机号、open_id、版本、地理位置等字段可在执行态用于派生风控判断，但沉淀态只输出 redacted、计数、分布或一致性结论；字段名、操作类型、时间范围、表头和分布类结构信息可沉淀。
- userId 不存在 / 非法时的预期失败处理已验证：已登录、无重定向、SPA 完整渲染、页面返回“用户不存在”，识别为 `USER_NOT_FOUND`。
- v2.4.5 已验证用户信息、用户分析、审核日志、视频作品集四个 P0 Tab 的只读深读。
- v2.4.5.1 是性能优化设计，不是新能力扩展；目标是通过 quick / focused / deep mode、scoped extraction 和列表采样降低耗时与 token 成本。
- v2.4.5.1 quick mode 已验证，约 22 秒。
- v2.4.5.1 focused_login_risk 结构提取已验证，103 秒；full risk_event_scan 仍待验证。
- v2.4.5.1 focused_login_risk risk_event_scan 已部分验证，约 156 秒；已能输出派生风险摘要，但存在 selector 噪声，状态为 `partial_validated_with_selector_noise`。
- v2.4.5.1 focused_login_risk risk_event_scan selector noise 已修复，约 63 秒；row feature filter 已验证有效，状态可标记为 `validated`。
- quick mode、focused structure extraction、focused risk_event_scan 均已验证。
- v2.4.6 Dennis Agent single-source observation digestion 已验证：能消化档案中心 focused_login_risk observation，并输出证据总结、风险线索、证据缺口和下一步平台建议。
- 未点击任何写操作按钮，只读安全检查通过。

未验证：

- 多平台 computer use。
- 多入参查询。
- 批量查询。
- 自动研判。
- 二级链接、详情页、查重页。
- 处置、审批、导出、封禁、解封等任何写操作。
- 多平台 / 多入口风险联动。
- 多源联合 observation digest。

后续建议：

- 将 dedupe 逻辑内置到 eval 脚本中。
- 继续保持边界：本阶段只代表档案中心 `userId` direct URL 下的只读派生观察能力，不代表自动风险定性完成。
- 进入 v2.4.7 端到端联合测试：内部 Agent 只读 observation → Dennis Agent 消化 → 下一步平台补证建议。
