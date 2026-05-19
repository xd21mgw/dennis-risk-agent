# Integration Notes

## 1. 与 internal_risk_platforms 的联动

推荐链路：

```text
用户问题
→ internal_risk_platforms/00_platform_routing_index.md 判断是否应查档案中心
→ computer_use_poc 执行档案中心 user_id 只读查询
→ 返回 observation
→ Dennis Risk Agent 结合多证据生成风险解释
```

## 2. 何时触发本 POC

仅当路由结果明确指向档案中心，且用户提供单个 `user_id` 时触发。

适用问题：

- 查询用户当前状态。
- 查询处罚 / 风控状态是否可见。
- 查询档案中心是否存在基础用户页。
- 查询档案中心可见模块。

不适用问题：

- 批量用户查询。
- token / OAuth / 扫码原始日志。
- 设备底层指纹和设备图谱。
- 策略配置和策略归因。
- Hive 离线大盘。

## 3. observation 的使用方式

computer use 返回结果只作为 observation。

Dennis Risk Agent 应继续判断：

- 该 observation 支持什么。
- 不能支持什么。
- 还缺哪些证据。
- 下一步应查哪个平台。

## 4. 与风险结论的边界

computer use 不输出最终结论。

风险结论必须由 Dennis Risk Agent 基于以下证据综合生成：

- 档案中心 observation。
- 登录日志。
- 设备平台。
- 策略归因。
- 行为链路。
- DataAgent / Hive 离线分析，如用户明确要求查数。

## 5. 后续扩展方向

当前只验证档案中心 user_id 查询。

后续如扩展，应逐个平台独立设计：

- 只读安全规则。
- 页面操作流程。
- observation schema。
- failure modes。
- smoke tests。

不得直接从档案中心 POC 推断其他平台已可自动操作。

## 6. Saved State 使用边界

后续可复用已保存的浏览器 state，减少重复认证成本。

安全要求：

- state 文件属于敏感认证态资产。
- state 文件不得提交到 Git。
- `archives_auth_state.json` 必须加入 `.gitignore` 或仅保存在本地安全路径。
- run log 不得包含 token、cookie、session、KIM code、认证 header。
- run log 不得包含用户名、手机号、设备 ID、IP、昵称、快手号等明文敏感字段。

推荐策略：

```text
state 文件仅本地保存
→ computer use 运行时读取
→ run log 只记录 state_saved=true/false 和 state_file_policy
→ 不记录 state 文件内容
```
