# ATO Entrypoint Usability Regression v1

## 1. 测试目标

验证内部盗号同学用自然语言提问时，Dennis Risk Agent 能否稳定：

- 识别 ATO 场景意图。
- 路由到正确 workflow。
- 判断是否需要 Data Agent。
- 调用正确核心 Skill / 证据卡 / 模板。
- 按 scenario_response_contract / ato_agent_response_contract 输出。
- 保留关键边界：Data Agent 不是最终判断、人工备注不是事实、无发布不能反向排除 ATO、具体策略名不能单独强结论。

本轮不调用 Data Agent，不修改核心 Skill，不编造真实数据，不暴露完整 user_id。

## 2. Case Regression

### Case 01：单 case 研判

| 字段 | 内容 |
|---|---|
| 用户问题 | 这个用户说自己被盗了，5 月 4 日扫码后账号异常，帮我判断可信不可信。 |
| 识别到的 intent | single_case_judgement |
| 触发 workflow | `single_case_judgement` |
| 是否需要 Data Agent | 需要，如果缺登录 / 授权 / token / 设备 / 下游行为证据 |
| 应调用的核心 Skill / 证据卡 / 模板 | `account_security_expert_skill`；ATO evidence boundary；必要时 `dataagent_question_generation` |
| 预期输出结构 | 单 case 输出格式：当前结论、为什么、支持证据、反证、缺失证据、下一步补证、是否需要 Data Agent、是否需要人工复核 |
| 必须包含的边界提醒 | 用户自述扫码不是事实；扫码后异常需要登录/授权/设备/token链路验证 |
| 是否符合 scenario_response_contract | 是 |
| 是否存在路由歧义 | 低 |
| 修正建议 | 无 |

### Case 02：批量 case 分层

| 字段 | 内容 |
|---|---|
| 用户问题 | 这批盗号客诉帮我分下类，哪些是扫码，哪些是钓鱼，哪些可能不是盗号。 |
| 识别到的 intent | batch_case_clustering |
| 触发 workflow | `batch_case_clustering` |
| 是否需要 Data Agent | 可选；如果只有人工表格，先分层；需要验证时再生成 Data Agent 问题 |
| 应调用的核心 Skill / 证据卡 / 模板 | `account_security_expert_skill`；ATO 标签体系；batch case schema |
| 预期输出结构 | 批量 case 输出格式：样本总览、ATO 发生方式分层、下游作恶方式分层、高置信正例、反例/不确定/历史 case、可回捞候选、风险与局限 |
| 必须包含的边界提醒 | 人工标签只是线索；样本比例不能直接写入 Skill |
| 是否符合 scenario_response_contract | 是 |
| 是否存在路由歧义 | 低 |
| 修正建议 | 无 |

### Case 03：生成 Data Agent 问题

| 字段 | 内容 |
|---|---|
| 用户问题 | 帮我生成 Data Agent 问题，查这批扫码盗号样本有没有共性。 |
| 识别到的 intent | dataagent_question_generation |
| 触发 workflow | `dataagent_question_generation` |
| 是否需要 Data Agent | 需要，但本轮只生成问题，不调用 |
| 应调用的核心 Skill / 证据卡 / 模板 | ATO Data Agent query templates；scenario response contract |
| 预期输出结构 | Data Agent 问题输出格式：可复制问题、查询目标、样本范围、时间窗口、数据域、输出要求、降级规则、Data Agent 边界 |
| 必须包含的边界提醒 | Data Agent 只做 evidence provider，不做最终风控判断；不写真表名/字段/SQL/API |
| 是否符合 scenario_response_contract | 是 |
| 是否存在路由歧义 | 低 |
| 修正建议 | 无 |

### Case 04：解释 Data Agent 返回

| 字段 | 内容 |
|---|---|
| 用户问题 | Data Agent 返回说 13/15 有 ASYNC_WEB_LOGIN，但只有 5/15 有发布，这能说明什么？ |
| 识别到的 intent | dataagent_result_interpretation |
| 触发 workflow | `dataagent_result_interpretation` |
| 是否需要 Data Agent | 不需要；已有返回，进入解释 |
| 应调用的核心 Skill / 证据卡 / 模板 | Data Agent result interpretation；ATO feature layering；`account_security_expert_skill` |
| 预期输出结构 | Data Agent 返回解释格式：数据发现、provider_conclusion_hint、Dennis final judgement、强/中/弱证据、反证、缺失证据、下一步 |
| 必须包含的边界提醒 | 13/15 和 5/15 是本批样本统计，只留 review/eval；无发布不能反向排除 ATO；发布不是必要条件 |
| 是否符合 scenario_response_contract | 是 |
| 是否存在路由歧义 | 低 |
| 修正建议 | 无 |

### Case 05：举一反三 / 回捞

| 字段 | 内容 |
|---|---|
| 用户问题 | 基于这批样本，怎么回捞同类盗号？ |
| 识别到的 intent | generalization_and_recall |
| 触发 workflow | `generalization_and_recall` |
| 是否需要 Data Agent | 可选；先给候选机制特征，再建议验证问题 |
| 应调用的核心 Skill / 证据卡 / 模板 | ATO feature layering；anti-overfitting rules；Data Agent query templates |
| 预期输出结构 | 举一反三输出格式：原始观测、数据发现、候选特征、机制特征、不建议使用的表象特征、正反例验证方案、误伤风险、回捞优先级 |
| 必须包含的边界提醒 | case 回扫生成假设，不直接生成线上策略；具体策略名不能作为长期本质特征 |
| 是否符合 scenario_response_contract | 是 |
| 是否存在路由歧义 | 中；用户可能同时想要治理 |
| 修正建议 | 如果用户提“怎么处理”，追加 `governance_design` |

### Case 06：治理方案

| 字段 | 内容 |
|---|---|
| 用户问题 | 这类 Web 扫码盗号怎么治理？应该验证、踢 token，还是封号？ |
| 识别到的 intent | governance_design |
| 触发 workflow | `governance_design` |
| 是否需要 Data Agent | 不一定；如果问治理框架不需要，若问命中量/效果需要 |
| 应调用的核心 Skill / 证据卡 / 模板 | `account_security_expert_skill`；risk_governance_design_skill；ATO governance workflow |
| 预期输出结构 | 治理方案输出格式：短期止损、中期识别、长期治理、登录前/中/后、token/session、下游作恶拦截、用户体验、业务协同 |
| 必须包含的边界提醒 | 不自动封号；高风险处置需人工确认；token 踢出要考虑误伤和恢复 |
| 是否符合 scenario_response_contract | 是 |
| 是否存在路由歧义 | 低 |
| 修正建议 | 无 |

### Case 07：复盘沉淀

| 字段 | 内容 |
|---|---|
| 用户问题 | 这批盗号 case 能沉淀什么？要不要回写 Skill？ |
| 识别到的 intent | review_and_skill_distillation |
| 触发 workflow | `review_and_skill_distillation` |
| 是否需要 Data Agent | 不需要，除非要补更多样本验证 |
| 应调用的核心 Skill / 证据卡 / 模板 | ATO feature layering；scenario workflow contract；eval/regression assets |
| 预期输出结构 | 复盘沉淀输出格式：可回写 Skill、只进 eval/review、需更多数据验证、不应沉淀、下一步建议 |
| 必须包含的边界提醒 | 样本统计、具体策略名、时间窗不写入 Skill；当前可先沉淀 review/eval |
| 是否符合 scenario_response_contract | 是 |
| 是否存在路由歧义 | 低 |
| 修正建议 | 无 |

### Case 08：多意图问题

| 字段 | 内容 |
|---|---|
| 用户问题 | 帮我看这批是不是盗号，并生成 Data Agent 查询问题。 |
| 识别到的 intent | batch_case_clustering + dataagent_question_generation |
| 触发 workflow | `batch_case_clustering` → `dataagent_question_generation` |
| 是否需要 Data Agent | 需要生成问题，但不调用 |
| 应调用的核心 Skill / 证据卡 / 模板 | ATO batch clustering；Data Agent question templates |
| 预期输出结构 | 先输出批量分层，再输出可复制给 Data Agent 的只读取证问题 |
| 必须包含的边界提醒 | 先分层再取证；人工标签不是事实；Data Agent 不做最终判断 |
| 是否符合 scenario_response_contract | 是 |
| 是否存在路由歧义 | 中；多意图明确但需排序 |
| 修正建议 | router 中继续保留先分层、后生成问题的顺序 |

### Case 09：边界问题：无发布

| 字段 | 内容 |
|---|---|
| 用户问题 | 这批样本大部分没发布内容，是不是就不能算盗号？ |
| 识别到的 intent | dataagent_result_interpretation |
| 触发 workflow | `dataagent_result_interpretation`，可辅以 `single_case_judgement` |
| 是否需要 Data Agent | 不需要，用户已给出数据发现 |
| 应调用的核心 Skill / 证据卡 / 模板 | ATO label refinement；feature layering |
| 预期输出结构 | 当前结论、为什么、反证/缺口、下一步补证 |
| 必须包含的边界提醒 | 无发布不能反向排除 ATO；发布异常内容不是 ATO 成立必要条件；可能存在其他下游作恶 |
| 是否符合 scenario_response_contract | 是 |
| 是否存在路由歧义 | 中；可解释为单 case 或批量结果解释 |
| 修正建议 | router 可优先 dataagent_result_interpretation，因为用户引用了批量数据发现 |

### Case 10：边界问题：人工备注

| 字段 | 内容 |
|---|---|
| 用户问题 | 人工备注说是扫码盗号，这能不能直接作为事实？ |
| 识别到的 intent | single_case_judgement |
| 触发 workflow | `single_case_judgement` |
| 是否需要 Data Agent | 视是否要验证；概念边界不需要 |
| 应调用的核心 Skill / 证据卡 / 模板 | `account_security_expert_skill`；ATO response contract |
| 预期输出结构 | 当前结论、为什么、支持证据、反证、缺失证据、下一步补证 |
| 必须包含的边界提醒 | 人工备注只能作为线索，不能直接当事实；需登录/授权/设备/token/下游行为验证 |
| 是否符合 scenario_response_contract | 是 |
| 是否存在路由歧义 | 低 |
| 修正建议 | 无 |

### Case 11：边界问题：具体策略名

| 字段 | 内容 |
|---|---|
| 用户问题 | 命中了某个盗号策略，是不是就能直接确认 ATO？ |
| 识别到的 intent | single_case_judgement |
| 触发 workflow | `single_case_judgement`，可辅以 `evidence_planning` |
| 是否需要 Data Agent | 不需要，除非要补查链路 |
| 应调用的核心 Skill / 证据卡 / 模板 | ATO feature layering；account security evidence boundary |
| 预期输出结构 | 当前结论、为什么、证据强度、反证、缺失证据 |
| 必须包含的边界提醒 | 具体策略名不能作为本质特征，也不能单独强结论；应抽象为账号安全风险策略命中，只是独立风险信号之一 |
| 是否符合 scenario_response_contract | 是 |
| 是否存在路由歧义 | 低 |
| 修正建议 | 无 |

### Case 12：迁移问题

| 字段 | 内容 |
|---|---|
| 用户问题 | 这个入口层以后反爬能不能复用？ |
| 识别到的 intent | review_and_skill_distillation |
| 触发 workflow | `review_and_skill_distillation` |
| 是否需要 Data Agent | 不需要 |
| 应调用的核心 Skill / 证据卡 / 模板 | scenario_intent_router_contract；scenario_workflow_contract；scenario_response_contract |
| 预期输出结构 | 复盘沉淀输出格式：可回写/可复用、只进 eval/review、需更多验证、下一步建议 |
| 必须包含的边界提醒 | ATO 是第一个 scenario overlay；反爬可复用通用 contract 扩展，不应把 Agent 改成盗号专用 |
| 是否符合 scenario_response_contract | 是 |
| 是否存在路由歧义 | 低 |
| 修正建议 | 无 |

## 3. 汇总

### 3.1 路由准确率

| 指标 | 结果 |
|---|---:|
| 测试问题数 | 12 |
| workflow 命中正确 | 12 |
| 路由准确率 | 100% |

### 3.2 多意图问题

存在多意图：

- Case 05：回捞问题可能附带治理意图。
- Case 08：批量判断 + Data Agent 问题生成。
- Case 09：可解释为批量结果解释，也可解释为单 case 边界判断。

当前 router 能处理，但建议继续保留 workflow 顺序规则。

### 3.3 哪些输出需要更稳定

建议后续进一步稳定：

- 多意图输出的排序规则。
- 单 case 短答模式和完整模式切换。
- evidence_planning 是否作为显式 workflow 暴露给 ATO overlay。
- Data Agent question 中 minimum_inputs 缺失时的统一提示。

### 3.4 是否需要修改 ATO overlay

当前不需要修改。

原因：
- 12 个问题均能路由。
- 边界提醒完整。
- response contract 可覆盖主要输出。

可选后续增强：
- 在 ATO router 中显式加入 `evidence_planning` intent，当前由 `dataagent_question_generation` 和 `single_case_judgement` 间接覆盖。

### 3.5 是否需要修改通用 scenario contract

当前不需要修改。

原因：
- 通用 contract 已覆盖 8 类 intent。
- ATO overlay 可按 contract 实现。
- 未来反爬、群控、活动反作弊也可复用。

### 3.6 是否修改核心 Skill

未修改核心 Skill。

本轮只新增 `outputs/reviews/ato_entrypoint_usability_regression_v1.md`。
