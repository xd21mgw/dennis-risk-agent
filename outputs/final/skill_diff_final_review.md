# Skill Diff Final Review

本文件对当前 modified 的 Skill 相关文件做最终 diff review。仅 review，不修改文件。

## 1. Review 范围

当前 `git diff --name-only` 中涉及 Skill / material 的 modified 文件：

- `skills/dennis_risk_agent_skills_v2_1_focused_deep/01_core_skills/material_delivery_skill.md`
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/02_domain_skills/account_security_expert_skill.md`
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/02_domain_skills/activity_anti_cheating_expert_skill.md`
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/02_domain_skills/anti_crawler_expert_skill.md`
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/02_domain_skills/traffic_anti_cheating_expert_skill.md`
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/02_domain_skills/traffic_diversion_interception_skill.md`
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/03_attack_skills/cracked_app_expert_skill.md`
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/03_attack_skills/group_control_expert_skill.md`
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/03_attack_skills/protocol_attack_expert_skill.md`
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/03_attack_skills/real_user_crowdsourcing_skill.md`
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/12_material_distillation/history_material_lessons_v2_1.md`

## 2. 总体结论

结论：建议纳入最终包，但入包前应按产品包范围区分“核心 Skill 包”和“材料沉淀附录”。

整体判断：

- 修改方向符合 v2.3 executable-deep 预期。
- 未发现 Data Agent adapter / query_intent / normalized_evidence 等内容误写入 modified Skill。
- 未发现真实表名、真实字段名、真实 API、真实 SQL。
- 未发现“前端无日志直接判协议”“设备聚集直接判群控”“低质直接判黑产”等强结论表达；多数文件明确写了禁止和降级。
- 未发现空模板或 TODO/TBD 型占位。
- 治理闭环中存在“冻结、扣除、封禁、强拦、强制升级”等高准治理动作表达，但均处于分层治理建议语境，并配有证据门槛、灰度、误伤控制或禁止证据不足强结论；不属于自动处罚表达。

## 3. 分文件 Review

### 3.1 material_delivery_skill.md

改动性质：

- 增补年度材料稳定写法和常用材料主线。
- 属于材料表达能力增强，不是风险判断逻辑改动。

检查结果：

- v2.3 executable-deep 预期：部分符合，偏材料交付增强。
- Data Agent 误改：未发现。
- 重复章节 / 空模板：未发现。
- 真实表名 / 字段 / API / SQL：未发现。
- 证据不足强结论：不涉及。
- 自动处罚表达：未发现。

建议：纳入最终包，属于表达交付增强。

### 3.2 account_security_expert_skill.md

改动性质：

- 从 v2.1 认知型升级为 v2.3 executable-deep 结构。
- 补齐 Skill 定位、触发条件、输入格式、专家认知、判断规则、证据体系、输出格式、治理闭环、禁止行为、质量校验、失败处理。
- 增加合法矩阵前置判断，避免把商家/达人/MCN/机构批量登录直接判为盗号、群控或协议。

检查结果：

- v2.3 executable-deep 预期：符合。
- Data Agent 误改：未发现 `query_intent`、`dataagent_request`、`normalized_evidence` 等内容。
- 重复章节 / 空模板：未发现。
- 真实表名 / 字段 / API / SQL：未发现。
- 证据不足强结论：未发现，明确写有 IP/设备/城市变化不得直接定性。
- 自动处罚表达：存在“风险 token 踢出、账号保护、敏感动作冻结”等治理动作，但属于高准分层治理；没有自动执行表达。

建议：纳入最终包。

### 3.3 activity_anti_cheating_expert_skill.md

改动性质：

- 升级为 executable-deep 结构。
- 强化活动黑产、真人低质、渠道抢量、规则漏洞、任务平台众包的区分。
- 补充 RTA / 曝光 / 点击 / 下载 / 激活 / 归因 / 结算链路表达。

检查结果：

- v2.3 executable-deep 预期：符合。
- Data Agent 误改：未发现。
- 重复章节 / 空模板：未发现。
- 真实表名 / 字段 / API / SQL：未发现。
- 证据不足强结论：未发现，明确写低质用户不得等同黑产。
- 自动处罚表达：存在结算扣除、冻结等治理动作，但语境是黑产高准或渠道治理建议；禁止“没有评估直接处罚渠道”。

建议：纳入最终包。

### 3.4 anti_crawler_expert_skill.md

改动性质：

- 升级为 executable-deep 结构。
- 强化反爬是领域、协议/群控/破解包/真人众包是手法的边界。
- 补充资产分级、非常 6+1 飞轮、外部泄漏与内部链路闭合、缓存/合作方/内部链路反证。

检查结果：

- v2.3 executable-deep 预期：符合。
- Data Agent 误改：未发现。
- 重复章节 / 空模板：未发现。
- 真实表名 / 字段 / API / SQL：未发现；`asset_id/content_id/url/hash/watermark_id` 是抽象取证键类型，不是真实字段名。
- 证据不足强结论：未发现，明确写外部报价/投诉不替代内部证据。
- 自动处罚表达：未发现自动处置表达。

建议：纳入最终包。

### 3.5 traffic_anti_cheating_expert_skill.md

改动性质：

- 升级为 executable-deep 结构。
- 强化指标可信、流量公平、DAU/DNU 口径保障、SLA、数据矫正和攻击证据边界。

检查结果：

- v2.3 executable-deep 预期：符合。
- Data Agent 误改：未发现。
- 重复章节 / 空模板：未发现。
- 真实表名 / 字段 / API / SQL：未发现。
- 证据不足强结论：未发现，明确写 DAU/DNU 缺攻击证据时先做口径校验和数据治理。
- 自动处罚表达：未发现自动执行表达。

建议：纳入最终包。

### 3.6 traffic_diversion_interception_skill.md

改动性质：

- 从较短 v2.1 文档升级为完整 v2.3 executable-deep 结构。
- 明确导流截流本质是“目标获取 -> 触达 -> 站外承接 -> 变现”。
- 强化直播间用户被站外添加不默认反爬或协议。
- 加入合法矩阵授权触达边界。

检查结果：

- v2.3 executable-deep 预期：符合。
- Data Agent 误改：未发现。
- 重复章节 / 空模板：未发现。
- 真实表名 / 字段 / API / SQL：未发现。
- 证据不足强结论：未发现，明确写无站外承接、无爬虫证据时不得强结论。
- 自动处罚表达：存在导流账号封禁/限权等高准治理动作，但有证据门槛和误伤控制，不是自动处置。

建议：纳入最终包。

### 3.7 cracked_app_expert_skill.md

改动性质：

- 升级为 v2.3 executable-deep。
- 明确破解包不是协议，但会制造“像协议”的端侧证据缺失。
- 补齐包签名、版本/渠道、Manifest、dex/so/assets、SDK 缺失、安全模块替换、runtime、方法级短链证据。

检查结果：

- v2.3 executable-deep 预期：符合。
- Data Agent 误改：未发现。
- 重复章节 / 空模板：未发现。
- 真实表名 / 字段 / API / SQL：未发现。
- 证据不足强结论：未发现，明确写无包工件证据不得强判破解包。
- 自动处罚表达：存在强制升级、风险版本限制、关键接口拒绝等治理动作，但属于治理闭环建议；未见自动执行表达。

建议：纳入最终包。

### 3.8 group_control_expert_skill.md

改动性质：

- 升级为 v2.3 executable-deep。
- 强化群控最小区分点是“统一调度”，不是设备多、账号多或访问高频。
- 加入合法矩阵前置判断。

检查结果：

- v2.3 executable-deep 预期：符合。
- Data Agent 误改：未发现。
- 重复章节 / 空模板：未发现。
- 真实表名 / 字段 / API / SQL：未发现。
- 证据不足强结论：未发现，明确写高频、聚集、设备多不得直接判群控。
- 自动处罚表达：存在账号封禁、设备处置、收益冻结、提现拦截等高准动作，但属于分层治理；同时有合法矩阵、热点、测试、NAT 等反证和误伤控制。

建议：纳入最终包。

### 3.9 protocol_attack_expert_skill.md

改动性质：

- 升级为 v2.3 executable-deep。
- 强化协议攻击本质是请求脱离正常端侧执行链。
- 明确前端无日志不能直接判协议。
- 加入破解包、群控、真人众包、合法自动化反证。

检查结果：

- v2.3 executable-deep 预期：符合。
- Data Agent 误改：未发现。
- 重复章节 / 空模板：未发现。
- 真实表名 / 字段 / API / SQL：未发现；文件中明确禁止编造真实表名、字段、SQL。
- 证据不足强结论：未发现，明确写高频、IP 聚集、前端无日志不得直接定性协议。
- 自动处罚表达：存在敏感接口强拦、token 失效、收益冻结等治理动作，但属于高准分层治理；有灰度和合法自动化审计。

建议：纳入最终包。

### 3.10 real_user_crowdsourcing_skill.md

改动性质：

- 升级为 v2.3 executable-deep。
- 强化“行为真实，但目标任务化”的本质。
- 明确设备离散不等于自然用户。
- 区分真人众包、群控、活动低质、正常自然用户。

检查结果：

- v2.3 executable-deep 预期：符合。
- Data Agent 误改：未发现。
- 重复章节 / 空模板：未发现。
- 真实表名 / 字段 / API / SQL：未发现。
- 证据不足强结论：未发现，明确写只有设备离散、任务相同、低质不得定义黑产。
- 自动处罚表达：存在奖励冻结、结算扣除等治理动作，但限定在高准和组织方/收益链闭合语境；有“低准只观察，不封禁真实用户”。

建议：纳入最终包。

### 3.11 history_material_lessons_v2_1.md

改动性质：

- 新增 2023-2025 跨年度主线沉淀。
- 属于材料经验沉淀，不是执行 Skill 主逻辑。

检查结果：

- v2.3 executable-deep 预期：间接相关，作为材料蒸馏附录。
- Data Agent 误改：未发现。
- 重复章节 / 空模板：未发现。
- 真实表名 / 字段 / API / SQL：未发现。
- 证据不足强结论：不涉及。
- 自动处罚表达：未发现自动执行表达。

建议：可纳入最终包的 `12_material_distillation/`，也可作为可选附录。

## 4. 专项检查结论

### 4.1 是否都是 v2.3 executable-deep 预期改动

是。核心 domain / attack Skill 均从 v2.1 认知型内容升级为：

- `0. Skill 定位`
- `1. 触发条件`
- `2. 输入格式`
- `3. 专家认知`
- `4. 判断规则`
- `5. 证据体系`
- `6. 输出格式`
- `7. 治理闭环`
- `8. 禁止行为`
- `9. 质量校验`
- `10. 失败处理`

`material_delivery_skill.md` 和 `history_material_lessons_v2_1.md` 不是典型 0-10 章改造，但改动符合材料表达和历史经验沉淀目标。

### 4.2 是否存在 Data Agent 阶段误改 Skill 的内容

未发现。检索 modified Skill 未发现：

- `Data Agent`
- `dataagent`
- `query_intent`
- `dataagent_request`
- `normalized_evidence`
- `adapter`

现有合法矩阵引用是前序 Skill 边界回写的一部分，符合预期。

### 4.3 是否存在重复章节、空模板、明显过度扩写

- 重复章节：未发现关键重复。
- 空模板：未发现 TODO/TBD 或未填占位。
- 过度扩写：整体偏完整，篇幅较长，但符合 executable-deep 目标。最终包可接受。

### 4.4 是否存在真实表名、真实字段名、真实 API、真实 SQL

未发现真实 SQL 或真实 API。

注意：

- 文件中出现 `API` 多为“工具 / API 不可用”的泛化表达。
- `asset_id/content_id/url/hash/watermark_id`、`token`、`device`、`ip`、`ua` 等是抽象取证字段类型或通用语义，不是内部真实字段名。
- `dex/so/assets`、Manifest、SDK、runtime activity 是客户端工件语义，不是数据表字段。

### 4.5 是否存在证据不足强结论

未发现。多个 Skill 明确写有：

- `证据不足时不得强结论`
- `只有前端无日志不得判协议`
- `只有设备聚集不得判群控`
- `只有低质/低钱效不得定义黑产`
- `外部报价/投诉不替代内部证据`
- `DAU/DNU 缺攻击证据时先做口径校验`

### 4.6 是否存在自动处罚、冻结、扣除、策略上线表达

未发现自动执行表达。

存在的高风险治理动作：

- 冻结。
- 扣除。
- 封禁。
- 强拦。
- 强制升级。
- 结算扣除。

这些均出现在 `治理闭环 / 分层处置 / 高准` 等语境，并配有灰度、误伤控制、禁止证据不足强结论或人工复核要求。建议最终 release notes 中继续强调“治理动作是建议，不是自动执行指令”。

## 5. 是否建议纳入最终包

建议纳入：

- 所有 modified core/domain/attack Skill。
- `history_material_lessons_v2_1.md` 可作为材料沉淀附录纳入。

入包前建议：

- 保留本 review 文件作为最终质量门禁。
- 打包时排除 `.swp`、`.DS_Store`、`__MACOSX/`、`.git/`。
- 若最终包聚焦 Data Agent integration，Skill 改动可作为 `v2.3 executable-deep core skills` 单独标注。

## 6. 风险结论

误改 Skill 风险：低。

主要理由：

- 未发现 Data Agent adapter 层内容混入 Skill。
- 未发现真实数据资产、字段、API 或 SQL。
- 未发现证据不足强结论。
- 高风险治理动作均处于分层治理语境，不是自动执行。

最终建议：可以纳入 `dennis-risk-agent v2.3 executable-deep + Data Agent integration design` 最终包。
