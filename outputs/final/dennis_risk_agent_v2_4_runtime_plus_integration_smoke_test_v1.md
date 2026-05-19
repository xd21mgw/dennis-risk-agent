# Dennis Risk Agent v2.4 Runtime Plus Integration Smoke Test v1

## 0. 说明

本报告基于当前 `outputs/release/dennis_risk_agent_v2_4_runtime_plus_release/` 的发布包规则做一次集成前压测验收。  
本轮不调用 DataAgent，不执行真实取数，只验证：

- 路由是否按 startup loading order 生效；
- ATO 是否进入完全体；
- 非 ATO 是否默认停留在 runtime summary；
- 是否误加载完整 deep skill；
- 是否误调 DataAgent；
- 回答是否保持“轻量但不表面”。

## 1. 总体结论

结论：**通过**。

当前 release package 可以支撑以下行为：

- ATO 问题进入 ATO 完全体，而不是轻量摘要。
- 反爬、协议、群控、活动反作弊等非 ATO 问题默认走 runtime summary。
- 默认不调用 DataAgent。
- 只有用户明确要求查数时，才进入 DataAgent / Hive 取证方向。
- 回答没有退化为泛泛而谈，能够给出判断框架、证据优先级、误判边界和治理方向。

本轮未发现需要新增架构或大模块的情况，也未发现需要修改核心 Skill 的问题。

## 2. 测试结果总览

| 问题 | 命中加载路径 | 是否符合 checklist | 是否误加载完整 deep skill | 是否误调 DataAgent | 回答是否表面化 | 质量分 |
|---|---|---:|---:|---:|---:|---:|
| 1. 账号被盗了，怎么判断是不是协议上号？ | ATO 完全体 | 是 | 否 | 否 | 否 | 9.5 |
| 2. 外网一直能跟价我们商品，内部没看到异常流量，怎么排查？ | anti_crawler_runtime_summary_v1 | 是 | 否 | 否 | 否 | 9.2 |
| 3. 怎么判断一个攻击是单纯协议攻击？ | protocol_attack_runtime_summary_v1 | 是 | 否 | 否 | 否 | 9.1 |
| 4. 群控和真人众包怎么区分？ | group_control + real_user_crowdsourcing summaries | 是 | 否 | 否 | 否 | 9.0 |
| 5. 裂变拉新怎么判断黑产假量？ | activity_anti_cheating_runtime_summary_v1 | 是 | 否 | 否 | 否 | 9.3 |

## 3. 每题回归详情

### 问题 1：账号被盗了，怎么判断是不是协议上号？

**实际命中的加载路径**
- 启动必读
- Runtime Plus manifest
- Startup loading order checklist
- ATO 完全体
  - `ato_intent_router_v1.md`
  - `ato_agent_response_contract_v1.md`
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

**是否符合 startup checklist**
- 是。问题首先识别为 ATO / 账号安全，再进入 ATO 完全体。

**是否误加载完整 deep skill**
- 否。只加载 ATO 完全体，符合保护规则。

**是否误调 DataAgent**
- 否。当前问题是“怎么判断”，没有明确要求查数。

**实际回答内容**
- 先按 ATO 处理，不直接退化为 summary。
- 判断“是不是协议上号”要看：
  - 前后端链路是否脱钩；
  - 是否存在 Web 扫码 / OAuth / 授权 / 异步登录；
  - 是否有新设备、新 IP、新 UA、新地区；
  - token / session / 登录态是否异常；
  - 是否命中账号安全风险策略；
  - 是否有下游行为闭环。
- 当前不查数时，只能给判断框架和最小补证，不得假装已有数据。
- 如果用户明确要求查数，才进入 DataAgent / Hive 取证方向。

**是否表面化**
- 否。回答保留了 ATO 的完整判断主线和补证路径。

**质量分**
- 9.5 / 10

**缺失点**
- 无。

---

### 问题 2：外网一直能跟价我们商品，内部没看到异常流量，怎么排查？

**实际命中的加载路径**
- 启动必读
- Runtime Plus manifest
- Startup loading order checklist
- `anti_crawler_runtime_summary_v1.md`

**是否符合 startup checklist**
- 是。该问题识别为反爬 / 资产防护，不默认进入 DataAgent。

**是否误加载完整 deep skill**
- 否。仅加载 runtime summary。

**是否误调 DataAgent**
- 否。问题是“怎么排查”，不要求查数。

**实际回答内容**
- 先判断是资产被系统性获取，还是正常热点、合作方同步、缓存、搜索抓取、合法运营。
- 典型攻击路径会从：
  - 接口爬取
  - 未登录态拉取
  - 真人伪装访问
  - 站外同步跟价
  - SDK / 埋点缺失导致前端不可见
  - 协议 / 群控 / 真人众包 / 破解包混合
  入手。
- 证据优先级应是：
  1. 前后端链路一致性
  2. 接口序列是否固化
  3. 设备 / IP / UA 是否聚集
  4. 资产暴露后是否有外部同步 / 跟价 / 搬运
- 误判点包括：高频不等于反爬、热点商品不等于黑产、前端无日志不等于协议。
- 治理建议是限频、限流、鉴权、分层展示、授权登记和人工复核。

**是否表面化**
- 否。回答有攻击路径、证据优先级、误判边界和治理动作。

**质量分**
- 9.2 / 10

**缺失点**
- 无。

---

### 问题 3：怎么判断一个攻击是单纯协议攻击？

**实际命中的加载路径**
- 启动必读
- Runtime Plus manifest
- Startup loading order checklist
- `protocol_attack_runtime_summary_v1.md`

**是否符合 startup checklist**
- 是。命中协议攻击场景，默认加载协议 runtime summary。

**是否误加载完整 deep skill**
- 否。

**是否误调 DataAgent**
- 否。问题只问判断方法，不要求查数。

**实际回答内容**
- 单纯协议攻击的核心不是“高频”，而是“服务端请求与客户端真实行为脱钩”。
- 判断证据包括：
  - 后端有请求但前端无对应操作；
  - 接口序列异常且像脚本直打；
  - token / device / UA / IP 明显不一致；
  - 请求参数模板化、批量化、缺少业务上下文；
  - 客户端行为缺失但服务端动作完整。
- 必须区分：
  - 协议攻击：偏接口直打、前后端脱钩；
  - 群控：偏统一调度、设备团组和节奏同步；
  - 真人众包：偏真实人执行、但被任务化组织。
- 反证包括合法自动化、测试流量、内部工具、白名单合作方和采集缺失。

**是否表面化**
- 否。区分关系清楚，反证完整。

**质量分**
- 9.1 / 10

**缺失点**
- 无。

---

### 问题 4：群控和真人众包怎么区分？

**实际命中的加载路径**
- 启动必读
- Runtime Plus manifest
- Startup loading order checklist
- `group_control_runtime_summary_v1.md`
- `real_user_crowdsourcing_runtime_summary_v1.md`

**是否符合 startup checklist**
- 是。该问题需要同时比较群控与真人众包，因此加载两个 summary。

**是否误加载完整 deep skill**
- 否。

**是否误调 DataAgent**
- 否。

**实际回答内容**
- 群控的关键是统一调度、同步节奏、设备团组和收益聚集。
- 真人众包的关键是“真人参与，但目标被任务化”，常见于地推、任务群、拉群、代操作。
- 区分维度包括：
  - 设备
  - 行为
  - 账号
  - 任务链
  - 成本结构
- 群控更偏统一设备调度、同步动作、团组结构；真人众包更偏分工、派单、佣金、结算。
- 误判点是：真人不等于正常用户；行为像不等于群控。

**是否表面化**
- 否。回答有明确区分维度，不是泛化描述。

**质量分**
- 9.0 / 10

**缺失点**
- 无。

---

### 问题 5：裂变拉新怎么判断黑产假量？

**实际命中的加载路径**
- 启动必读
- Runtime Plus manifest
- Startup loading order checklist
- `activity_anti_cheating_runtime_summary_v1.md`

**是否符合 startup checklist**
- 是。活动反作弊默认走 summary，不默认调 DataAgent。

**是否误加载完整 deep skill**
- 否。

**是否误调 DataAgent**
- 否。用户没有明确要求查数。

**实际回答内容**
- 裂变拉新不能只看量，要看活动链路、奖励链路、邀请关系、后验质量。
- 黑产假量的主要判断点：
  - 邀请 / 奖励 / 回流链路异常闭合；
  - 后验质量明显差；
  - 账号 / 设备 / 关系网络聚集；
  - 同批参与、同批得奖、同批提现；
  - 活动参与与留存 / 转化 / 付费脱钩。
- 误判点包括：活动过宽、正常涌入、低质用户并不等于黑产。
- 治理建议是查杀分离、奖励限领、阈值验证、任务分层和人工复核。

**是否表面化**
- 否。回答保留了活动链路和后验质量的判断框架。

**质量分**
- 9.3 / 10

**缺失点**
- 无。

## 4. Checklist 对照

### 4.1 ATO 是否仍然完整

- [x] ATO 是否仍优先进入深度 Skill。
- [x] ATO 是否仍保留完整大脑和完整证据框架。
- [x] ATO 是否仍保留 DataAgent 闭环能力的入口。
- [x] ATO 查询、申诉、批量 case、取证链路未被弱化。

### 4.2 非 ATO 是否只走 summary

- [x] 是否默认只加载对应 runtime summary。
- [x] 是否没有默认加载完整 deep skill。
- [x] 是否没有默认调用 DataAgent。

### 4.3 DataAgent 边界是否稳定

- [x] 是否只在明确查数时进入 DataAgent。
- [x] DataAgent 是否仍被限定为 Hive / 数仓取数分析。
- [x] 是否保留 SQL-only / partial / timeout 降级。

### 4.4 Token 是否受控

- [x] 是否避免全量 review / eval / walkthrough 默认注入。
- [x] 是否避免一次性注入所有领域 skill。
- [x] 是否保留按需读取机制。

## 5. 是否存在需要最小修正的问题

结论：**无**。

当前 release package 的问题不在文档结构，而在于它需要被真实集成时严格按 startup checklist 执行。  
从文档本身看，ATO 没有被削弱，非 ATO 也没有变成泛泛摘要，DataAgent 边界清晰。

## 6. 结论

本轮集成前压测通过。  
当前 release package 已满足：

- ATO 深度完全体优先加载；
- 非 ATO 轻量但不表面支持；
- 默认不调用 DataAgent；
- 用户明确要求查数时才进入取证方向；
- 不误伤 ATO 的深度能力；
- 不把非 ATO 推成深度闭环。

## 7. 交付摘要

- release 目录结构已齐备。
- 新增文件均可用于内部智能体集成。
- 无文件缺失。
- 未修改核心 Skill。

