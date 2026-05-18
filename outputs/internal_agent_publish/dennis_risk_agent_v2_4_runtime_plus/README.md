# Dennis Risk Agent v2.4 Runtime Plus Release

## 1. 版本定位

本 release 包对应 Dennis Risk Agent v2.4 Runtime Plus。

定位如下：

- Dennis Risk Agent 是通用业务风控专家 Agent。
- ATO 是第一个深度完全体样板。
- 非 ATO 通过 Runtime Plus 支持轻量但不表面的短问回答。
- DataAgent 只作为 Hive / 公司数仓取数分析能力，不是全能数据底座。

## 2. 默认启动加载方式

默认启动建议加载：

1. 总控 system prompt / working guide / routing rules。
2. `dennis_risk_agent_v2_4_runtime_plus_manifest_v1.md`
3. `dennis_risk_agent_v2_4_startup_loading_order_checklist_v1.md`
4. 通用 scenario contract 摘要。
5. DataAgent boundary 摘要。
6. timeout 摘要。
7. 当前场景 runtime summary。

## 3. ATO 加载方式

ATO 命中后应进入完整体，不退化成轻量 summary。

ATO 完全体以 manifest 中列出的文件为准，包括：

- account_security_expert_skill。
- DataAgent parser / schema / join / interpretation / threshold。
- DataAgent boundary / timeout。
- ATO short question adaptation。
- ATO runtime slim / POC 结果。

## 4. 非 ATO 加载方式

非 ATO 场景默认加载对应 runtime summary：

- 反爬。
- 协议攻击。
- 群控。
- 破解包。
- 真人众包。
- 活动反作弊。
- 导流截流。
- 流量反作弊。

默认行为：

- 先判断场景。
- 先拆证据。
- 先给取证方向和治理建议。
- 不默认调 DataAgent。

## 5. DataAgent 边界

- 只有用户明确要求查数、拉样本、看日志、看画像、验证数据、生成查询问题时，才进入 DataAgent。
- DataAgent 只定位为 Hive / 公司数仓取数分析能力。
- 高成本查询必须用户确认。
- SQL-only / partial / timeout 不能强结论。

## 6. 推荐加载顺序

1. 总控规则。
2. Runtime Plus manifest。
3. Startup loading order checklist。
4. 当前问题对应的 scenario summary。
5. 如果命中 ATO，再加载 ATO 完全体。
6. 如果用户明确要求查数，再进入 DataAgent 边界和取证模板。

## 7. 不建议一次性全量注入所有 deep skill

原因：

- token 成本高。
- 路由容易被历史材料污染。
- 非 ATO 场景只需要轻量但不表面的认知，不需要全量历史。

## 8. 回归说明

本 release 包中的 8 个非 ATO 扩展案例回归**不作为本次 release 阻塞项**，后续作为质量体检执行。

## 9. 集成前冒烟测试

本 release 包已通过集成前冒烟测试，确认：

- ATO 问题可进入完全体。
- 非 ATO 场景可默认走 runtime summary。
- 默认不误调 DataAgent。
- 不会把非 ATO 场景退化成表面化回答。
