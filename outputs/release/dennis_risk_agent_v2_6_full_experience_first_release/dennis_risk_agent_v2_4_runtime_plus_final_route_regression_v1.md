# Dennis Risk Agent v2.4 Runtime Plus 最终路由回归报告 v1

## 1. 回归说明

本轮基于当前 `Runtime Plus` 与 `startup_loading_order_checklist_v1` 做文档级路由回归，验证默认加载、场景识别、summary / deep skill 切换、DataAgent 边界和回答质量是否符合预期。

结论先行：

- ATO 短问应进入 ATO 完全体，不应退化成轻量 summary。
- 反爬、协议、群控、活动反作弊等非 ATO 短问应优先走对应 runtime summary。
- 非 ATO 场景默认不调用 DataAgent。
- 四个问题均不需要默认查数，除非用户明确要求。

## 2. 回归结果总览

| 问题 | 应命中加载路径 | 是否符合 checklist | 是否误加载完整 deep skill | 是否误调 DataAgent | 回答是否表面化 | 结论 |
|---|---|---|---|---|---|---|
| 1. ATO 短问 | ATO 完全体 + 协议边界按需读取 | 是 | 否 | 否 | 否 | 通过 |
| 2. 反爬短问 | anti_crawler_runtime_summary_v1 | 是 | 否 | 否 | 否 | 通过 |
| 3. 协议攻击短问 | protocol_attack_runtime_summary_v1 + 群控 / 真人众包边界摘要 | 是 | 否 | 否 | 否 | 通过 |
| 4. 活动反作弊短问 | activity_anti_cheating_runtime_summary_v1 | 是 | 否 | 否 | 否 | 通过 |

## 3. 逐题回归

### 问题 1：ATO 短问

用户问题：账号被盗了，怎么判断是不是被协议上号？

#### 实际命中的加载路径

- 先命中 ATO router。
- 进入 ATO 完全体。
- 因问题涉及“协议上号”边界，按需读取协议攻击边界能力。

#### 是否符合 startup checklist

符合。

#### 是否误加载完整 deep skill

否。命中的 ATO 完全体本身就是应该加载的内容，不属于误加载；协议边界只是在问题需要时按需读取。

#### 是否误调 DataAgent

否。当前问题没有明确要求查数、看日志或生成查询问题，只应给出判断框架和最小补证方向。

#### 回答质量

不应表面化。应输出：

- 账号被盗属于 ATO。
- 需要区分协议上号和其他接管方式。
- 先看登录 / 授权链路、设备 / IP / UA、一致性、token / session、风控命中。
- 如果用户要查证据，再生成最小 DataAgent 方向。

#### 结论

通过。
该问题必须进入 ATO 完全体，而不是只走轻量 summary。

---

### 问题 2：反爬短问

用户问题：发现外网一直能跟价我们的商品，但内部没看到明显异常爬虫流量，可能怎么排查？

#### 实际命中的加载路径

- 命中 anti_crawler_runtime_summary_v1。

#### 是否符合 startup checklist

符合。

#### 是否误加载完整 deep skill

否。不应直接加载反爬完整 deep skill。

#### 是否误调 DataAgent

否。用户没有明确要求查数。

#### 回答质量

应包含：

- 外网跟价不等于一定是内部接口被爬。
- 优先排前端暴露、缓存、合作方同步、搜索结果、接口访问、资产搬运。
- 证据优先级应围绕链路、接口序列、设备 / IP / UA 聚集、未登录态访问。
- 治理上先收敛暴露面，再做限频、鉴权、延迟展示、授权登记。

#### 结论

通过。
该问题应只加载反爬 summary，不默认进入 DataAgent。

---

### 问题 3：协议攻击短问

用户问题：怎么判断一个攻击是单纯协议攻击，而不是群控或真人众包？

#### 实际命中的加载路径

- 命中 protocol_attack_runtime_summary_v1。
- 因问题要求区分群控 / 真人众包，按需读取 group_control_runtime_summary_v1 与 real_user_crowdsourcing_runtime_summary_v1 作为边界参考。

#### 是否符合 startup checklist

符合。

#### 是否误加载完整 deep skill

否。不应直接加载协议、群控、真人众包三个完整 deep skill。

#### 是否误调 DataAgent

否。当前问题是方法论短问，不是查数请求。

#### 回答质量

应包含：

- 协议：后端有请求但前端真实行为对不上，token / device / UA / IP 一致性差。
- 群控：看统一调度、设备团组、行为同步、收益聚集。
- 真人众包：看任务化真人执行、组织关系、派单 / 奖励 / 结算链路。
- 反证：合法自动化、测试流量、埋点缺失、正常高频。
- 治理：先做边界拆解，再决定是否要查数。

#### 结论

通过。
该问题应优先加载协议 summary，并按需加载群控 / 真人众包边界，而不是直接走 DataAgent。

---

### 问题 4：活动反作弊短问

用户问题：裂变拉新活动里，怎么判断黑产假量和正常用户增长？

#### 实际命中的加载路径

- 命中 activity_anti_cheating_runtime_summary_v1。

#### 是否符合 startup checklist

符合。

#### 是否误加载完整 deep skill

否。不应默认加载活动反作弊完整 deep skill。

#### 是否误调 DataAgent

否。用户没有明确要求查数。

#### 回答质量

应包含：

- 先拆活动链路、奖励链路、邀请关系、后验质量。
- 假量 / 裂变套利 / 渠道套利 / 真人众包是不同路径。
- 低留存、低付费、单一转化差不能直接等同作弊。
- 要做查杀分离和业务损伤控制。
- 如果要验证数据，再生成低成本查询方向。

#### 结论

通过。
该问题应落到活动反作弊 summary，不默认走 DataAgent。

## 4. 是否达标

### 4.1 哪些文件达标

- `outputs/final/dennis_risk_agent_v2_4_runtime_plus_manifest_v1.md`
- `outputs/final/dennis_risk_agent_v2_4_startup_loading_order_checklist_v1.md`
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/11_runtime_summaries/*.md`

### 4.2 哪些文件只是表面摘要

初版 summary 中，确实存在“只有场景定位 / 本质 / 路径 / 证据 / 治理”的风险。
本轮已补齐：

- 核心判断问题。
- 默认输出结构。
- 升级完整 Skill 条件。
- 允许查数 / 调 DataAgent 条件。
- 当前不应直接下结论的边界。

因此当前版本已经不是表面摘要，而是可运行的轻量认知底座。

### 4.3 哪些文件缺少关键判断框架

修正前缺少，修正后已补齐。

当前未发现还需要结构性补的关键框架。

## 5. 是否存在 DataAgent 泛化 / 滥用

未发现。

原因：

- 非 ATO summary 明确默认不调 DataAgent。
- 只有用户明确要求查数 / 拉样本 / 看日志 / 验证数据时，才进入 DataAgent。
- DataAgent 被限定为 Hive / 公司数仓取数分析能力，不是全能数据底座。

## 6. 是否存在 ATO 被削弱

未发现。

原因：

- ATO 在 manifest 中仍保留完整体。
- ATO 仍优先进入深度 skill。
- ATO 仍保留 DataAgent 闭环、短问入口、降级规则和 runtime slim 能力。
- 当前 checklist 已明确 ATO 查询、申诉、批量 case、DataAgent 取证链路不能被弱化。

## 7. 最小修改建议

无需大改架构，仅建议维持当前状态：

1. 继续按当前 manifest 运行，不扩大默认注入范围。
2. 非 ATO summary 保持当前结构，不再扩成长文。
3. 后续若出现新的非 ATO 深度场景，再按 ATO 模式单独补 overlay，而不是把全量 deep skill 默认塞进运行态。

## 8. 结论

本轮 4 个真实路由回归通过。

总结为：

- ATO 进入完全体；
- 非 ATO 走轻量 summary；
- 默认不调 DataAgent；
- 短问仍能稳定回答；
- 当前 Runtime Plus 的路由、边界和 token 控制都符合预期。

