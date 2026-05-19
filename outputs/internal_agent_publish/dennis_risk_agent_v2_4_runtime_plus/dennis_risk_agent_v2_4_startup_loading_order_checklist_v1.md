# Dennis Risk Agent v2.4 启动加载顺序清单 v1

## 一页总览

本清单用于约束 Dennis Risk Agent 在 v2.4 Runtime Plus 下的实际启动加载顺序。

核心原则：

1. 先加载总控和运行态边界，不默认加载所有 deep skill。
2. 先识别是不是 ATO / 账号被盗 / 申诉 / 批量 case / 登录异常，再决定是否加载 ATO 完全体。
3. 非 ATO 场景默认只加载对应 runtime summary，不默认调用 DataAgent。
4. 用户明确要求查数、拉样本、看日志、看画像、验证数据时，才进入 DataAgent / Hive 取证请求。
5. 查数结果只补必要 interpretation rules，不把全量历史 review / eval / walkthrough 塞进运行态。

## 加载顺序表

| 顺序 | 加载层级 | 目的 | 是否默认加载 |
|---|---|---|---|
| 1 | 总控 system prompt / working guide / routing rules | 统一角色、边界、输出风格 | 是 |
| 2 | Runtime Plus manifest | 约束默认加载 / 按需读取 / 不建议注入 | 是 |
| 3 | 通用 scenario contract 摘要 | 通用路由、workflow、response 规则 | 是 |
| 4 | DataAgent 边界说明 / timeout 摘要 | 约束查数、降级、成本 | 是 |
| 5 | 场景识别 | 判断是 ATO 还是其他风险场景 | 是 |
| 6 | 场景 summary 或 ATO 完全体 | 根据场景加载对应能力 | 条件式 |
| 7 | 取证 / 解释 / 阈值规则 | 只在需要查数或解释 DataAgent 时读取 | 条件式 |
| 8 | review / eval / walkthrough | 仅离线复盘参考 | 否 |

## 场景到文件映射表

### 1. 启动必备

默认启动只保留以下文件类别：

- 总控 system prompt / working guide / routing rules。
- Runtime Plus manifest。
- 通用 scenario contract 摘要。
- DataAgent 边界说明。
- timeout policy 摘要。

### 2. ATO 场景加载顺序

#### 2.1 先识别是否为 ATO

用户问题只要涉及以下语义，应先判断是否进入 ATO：

- ATO / 账号被盗 / 账号接管。
- 申诉 / 解封 / 客诉可信度。
- 扫码 / OAuth / 授权登录 / 异步登录。
- 登录异常 / token / session / 账号控制权变化。
- 批量 case / 批量盗号 / 批量申诉。

#### 2.2 命中 ATO 后加载 ATO 完全体

命中 ATO 后，按需加载以下完整文件集合：

- `account_security_expert_skill.md`
- `dataagent_markdown_response_parser_v1.md`
- `query_intent_schema_v2.md`
- `data_join_paths_v1.md`
- `dataagent_result_interpretation_rules_v1.md`
- `dataagent_conclusion_thresholds_v1.md`
- `dataagent_provider_boundary_overlay_v1.md`
- `dataagent_timeout_policy_review_v1.md`
- `ato_short_question_entrypoint_adaptation_v1.md`
- `ato_runtime_slimming_plan_v1.md`
- `ato_runtime_slim_manifest_v1.md`
- `dennis_dataagent_poc_auto_sync_loop_result_v1.md`

#### 2.3 ATO 完全体加载顺序建议

1. `ato_intent_router_v1.md`
2. `ato_agent_response_contract_v1.md`
3. `account_security_expert_skill.md`
4. DataAgent parser / schema / join / interpretation / threshold
5. DataAgent boundary / timeout
6. ATO short question adaptation
7. ATO runtime slim / POC 结果

#### 2.4 ATO 特殊保护规则

- ATO 不应被 runtime summary 替代。
- ATO 的短问入口、单 case 判断、DataAgent 闭环、`provider_conclusion_hint` / `dennis_final_judgement` 分离必须保留。
- ATO 场景下，默认优先完整 ATO 能力，不降级成只读 summary。
- ATO 查询、申诉、批量 case、DataAgent 取证链路不能被弱化。

### 3. 非 ATO 场景加载顺序

#### 3.1 默认只加载对应 runtime summary

非 ATO 场景默认加载对应 runtime summary，而不是完整 deep skill：

- 反爬 → `anti_crawler_runtime_summary_v1.md`
- 协议 → `protocol_attack_runtime_summary_v1.md`
- 群控 → `group_control_runtime_summary_v1.md`
- 破解包 → `cracked_app_runtime_summary_v1.md`
- 真人众包 → `real_user_crowdsourcing_runtime_summary_v1.md`
- 活动反作弊 → `activity_anti_cheating_runtime_summary_v1.md`
- 导流截流 → `traffic_diversion_runtime_summary_v1.md`
- 流量反作弊 → `traffic_anti_cheating_runtime_summary_v1.md`

#### 3.2 runtime summary 对应的用户问题类型

| 场景 | 典型用户问题 |
|---|---|
| 反爬 | 这个接口是不是被爬？外网一直能跟价我们商品，可能怎么来的？ |
| 协议 | 后端有请求但前端没操作，可能是什么？这个是不是单纯协议攻击？ |
| 群控 | 这些设备行为很像，是不是群控？很多账号同一批设备操作，怎么判断？ |
| 破解包 | 这个是不是破解包？SDK 没日志是不是包被改了？ |
| 真人众包 | 这是正常用户还是真人众包？地推扫码算不算真人众包？ |
| 活动反作弊 | 这批活动用户是不是假量？渠道拉新质量很差，是不是在套利？ |
| 导流截流 | 直播间用户被陌生人加好友，是不是导流？评论区这些账号是不是在引流？ |
| 流量反作弊 | 这批流量是不是刷的？渠道质量很差是不是作弊？ |

#### 3.3 非 ATO 默认行为

- 默认只做场景判断、证据拆解、取证方向、治理建议。
- 默认不调用 DataAgent。
- 默认不进入深度 Skill 全文。

#### 3.4 只有明确要求时才进入 DataAgent

只有当用户明确要求以下内容时，才进入 DataAgent 取证请求：

- 查数。
- 拉样本。
- 看日志。
- 看画像。
- 验证数据。
- 生成查询问题。

DataAgent 只能定位为：

- Hive / 公司数仓取数分析能力。
- 不应写成全能数据底座。

## 升级完整 Skill 条件

满足以下任一条件，可从 runtime summary 升级到完整 Skill：

1. 用户要求深入方案。
2. 短问回答不足。
3. 涉及复杂攻击链。
4. 需要输出治理方案 / 复盘 / 报告。
5. runtime summary 明确无法覆盖。
6. 多轮追问进入深水区。

升级后应按需读取对应 deep skill，不要一次性全量展开。

## 降级和 token 控制规则

### 1. 短问优先 runtime summary

非 ATO 短问先用 runtime summary 回答，不直接展开成深度文档。

### 2. 非关键场景不加载完整 deep skill

只有真正需要更深判断、治理、边界时，再读取完整 skill。

### 3. 查数结果只加载必要 interpretation rules

如果进入 DataAgent，只加载必要的解释规则，不把全量 review / history 带入运行态。

### 4. 不要一次性注入所有领域 skill

按场景按需加载，避免 token 爆炸。

### 5. 回答优先结构

默认按以下顺序输出：

1. 判断框架。
2. 证据优先级。
3. 治理建议。
4. 下一步。

## 非 ATO DataAgent 边界

- 默认不调用 DataAgent。
- 明确要求查数 / 拉样本 / 看日志 / 看画像 / 验证数据时，才进入 DataAgent。
- DataAgent 只承担 Hive / 公司数仓取数分析方向。
- 高成本查询必须用户确认。
- SQL-only / partial / timeout 不能强结论。

## 回归检查清单

### 1. ATO 是否仍然完整

- [ ] ATO 是否仍优先进入深度 Skill。
- [ ] ATO 是否仍保留完整大脑和完整证据框架。
- [ ] ATO 是否仍保留 DataAgent 闭环能力。
- [ ] ATO 查询、申诉、批量 case、取证链路是否未被弱化。

### 2. 非 ATO 是否只走 summary

- [ ] 是否默认只加载对应 runtime summary。
- [ ] 是否没有默认加载完整 deep skill。
- [ ] 是否没有默认调用 DataAgent。

### 3. DataAgent 边界是否稳定

- [ ] 是否只在明确查数时进入 DataAgent。
- [ ] DataAgent 是否仍被限定为 Hive / 数仓取数分析。
- [ ] 是否保留 SQL-only / partial / timeout 降级。

### 4. Token 是否受控

- [ ] 是否避免全量 review / eval / walkthrough 默认注入。
- [ ] 是否避免一次性注入所有领域 skill。
- [ ] 是否保留按需读取机制。

### 5. 是否需要升级

- [ ] 当前问题是否已超出 summary 能力。
- [ ] 是否需要读取完整 deep skill。
- [ ] 是否需要进入 DataAgent。

