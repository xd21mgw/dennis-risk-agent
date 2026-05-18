# Integration Quick Start

## 1. 默认加载

先加载：

1. `README.md`
2. `dennis_risk_agent_v2_4_runtime_plus_manifest_v1.md`

再按场景加载对应内容。

`dennis_risk_agent_v2_4_startup_loading_order_checklist_v1.md` 建议作为初始化 / 配置期文件使用，不建议每轮问答都常驻加载。

## 2. 用户问 ATO 怎么走

加载 ATO 完全体：

- `account_security_expert_skill.md`
- DataAgent parser / schema / join / interpretation / threshold
- DataAgent boundary / timeout
- ATO short question adaptation
- ATO runtime slim / POC 结果

然后按 ATO 路由、workflow、response contract 走。

## 3. 用户问非 ATO 怎么走

默认只加载对应 runtime summary，优先单一 summary；只有问题明确跨域时最多加载 2 个 summary：

- 反爬 → `anti_crawler_runtime_summary_v1.md`
- 协议 → `protocol_attack_runtime_summary_v1.md`
- 群控 → `group_control_runtime_summary_v1.md`
- 破解包 → `cracked_app_runtime_summary_v1.md`
- 真人众包 → `real_user_crowdsourcing_runtime_summary_v1.md`
- 活动反作弊 → `activity_anti_cheating_runtime_summary_v1.md`
- 导流截流 → `traffic_diversion_runtime_summary_v1.md`
- 流量反作弊 → `traffic_anti_cheating_runtime_summary_v1.md`

默认先给判断、证据拆解、取证方向和治理建议，不默认查数。

## 4. 用户明确要求查数时怎么走

如果用户明确说：

- 查数
- 拉样本
- 看日志
- 看画像
- 验证数据
- 生成查询问题

才进入 DataAgent 取证方向。

DataAgent 只定位为 Hive / 公司数仓取数分析能力。

## 5. 哪些情况不要调 DataAgent

- 只是问“怎么看 / 是不是 / 怎么防”。
- 只是问方法论。
- 只是要边界判断。
- 只是要治理建议。
- 当前 summary 已能覆盖的问题。

## 6. 高成本动作

以下情况必须用户确认：

- 长周期扩窗。
- 多表 join。
- 大样本回捞。
- 预计较慢的 Hive 查询。

正式接入前，可以先用 5 个 smoke test 问题验证路由是否按预期命中 ATO 完全体或对应 runtime summary。
