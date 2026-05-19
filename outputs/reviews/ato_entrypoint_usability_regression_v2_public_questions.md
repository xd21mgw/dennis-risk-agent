# ATO Entrypoint Usability Regression v2 - Public Questions

## 0. 回归定位

本轮基于 `outputs/reviews/ato_public_industry_question_set_v1.md`，选择 9 个公开行业启发问题做 ATO entrypoint usability regression v2。

目标不是新增能力，而是验证现有 ATO intent router、ATO workflows、ATO response contract 是否能稳定承载扩展问法。

边界：
- 不调用 Data Agent。
- 不修改核心 Skill。
- 不编造真实内部数据。
- 不暴露完整 user_id。
- 不写真实表名、字段名、SQL 或 API。
- 公开行业问法只作为场景覆盖和回归输入，不作为内部事实。
- Data Agent 仍是 evidence provider。
- `dennis_final_judgement` 由 Dennis 主 Agent 生成。

## 1. Case 清单

| case | question_id | 覆盖目标 | 预期 workflow |
|---|---|---|---|
| R2-01 | ATO_PUBLIC_Q11 | 下游非发布作恶：点赞 / 关注 / 评论 / 私信 | `dataagent_question_generation` |
| R2-02 | ATO_PUBLIC_Q12 | 下游非发布作恶：爬虫 / 接口访问 / 资产窃取 | `single_case_judgement -> governance_design` |
| R2-03 | ATO_PUBLIC_Q13 | 高粉 / 达人 / 创作者账号被盗影响范围 | `single_case_judgement -> governance_design` |
| R2-04 | ATO_PUBLIC_Q15 | 账号租借 / 共享 / 交易 vs ATO | `single_case_judgement` |
| R2-05 | ATO_PUBLIC_Q16 | 用户泄露验证码后的平台责任边界 | `single_case_judgement -> governance_design` |
| R2-06 | ATO_PUBLIC_Q08 | Data Agent SQL-only 降级 | `dataagent_result_interpretation` |
| R2-07 | ATO_PUBLIC_Q09 | Data Agent partial / no_permission 降级 | `dataagent_result_interpretation` |
| R2-08 | ATO_PUBLIC_Q04 | 有异常内容发布但不能直接确认 ATO | `single_case_judgement` |
| R2-09 | ATO_PUBLIC_Q03 | 无发布行为但不能反向排除 ATO | `single_case_judgement` |

## 2. 逐 Case 压测

### R2-01 - 下游互动滥用

| 字段 | 结果 |
|---|---|
| question_id | ATO_PUBLIC_Q11 |
| 用户问题 | 被盗后只点赞/关注/私信，怎么识别？ |
| 预期 intent | `evidence_planning` |
| 实际应触发 workflow | `dataagent_question_generation`，必要时接 `single_case_judgement` |
| 是否多意图 | 是。既问识别逻辑，也隐含取证规划。 |
| 是否需要 Data Agent | 需要生成只读取证问题；本轮不调用。 |
| 应调用的核心 Skill / 证据卡 / Data Agent 模板 | `account_security_expert_skill`；ATO evidence boundary；downstream behavior branch；互动行为取证模板。 |
| 预期输出结构 | 取证目标、ATO 发生方式证据、互动下游作恶证据、反证、缺失证据、Data Agent 问题、降级规则。 |
| 必须包含的边界提醒 | 点赞/关注/评论/私信是 ATO 后下游作恶方式，不是 ATO 发生方式；必须先证明登录/授权/token/设备等账号接管链路。 |
| 是否符合 ATO response contract | 符合，可落到 Data Agent 问题输出格式。 |
| 是否存在路由歧义 | 轻微。若用户给具体 case，应先 `single_case_judgement`；若只问怎么识别，应走 `dataagent_question_generation`。 |
| 是否存在过拟合风险 | 中。不能把“互动滥用”沉淀成 ATO 必要条件。 |
| 是否需要修改 ATO entrypoint / workflow / response contract | 不需要。 |
| 是否需要修改通用 scenario contract | 不需要。 |

### R2-02 - ATO 与反爬联动

| 字段 | 结果 |
|---|---|
| question_id | ATO_PUBLIC_Q12 |
| 用户问题 | 被盗后用于爬虫/接口访问，和反爬怎么联动？ |
| 预期 intent | `governance_design` |
| 实际应触发 workflow | `single_case_judgement -> governance_design` |
| 是否多意图 | 是。先判断是否 ATO，再判断是否进入反爬/资产访问治理。 |
| 是否需要 Data Agent | 可能需要，用于生成接口访问、资产访问、登录态链路的只读取证问题。 |
| 应调用的核心 Skill / 证据卡 / Data Agent 模板 | `account_security_expert_skill` + `anti_crawler_expert_skill`；ATO evidence boundary；asset access evidence；Evidence Tool Router 设计。 |
| 预期输出结构 | ATO 入口判断、接口/资产访问证据、反爬协同治理、反证、缺失证据、下一步 provider。 |
| 必须包含的边界提醒 | ATO 是账号控制入口，反爬是下游资产访问场景；不能把接口访问直接当 ATO，也不能把 ATO 直接当反爬证据。 |
| 是否符合 ATO response contract | 符合，可用单 case 输出 + 治理方案输出。 |
| 是否存在路由歧义 | 有。问题同时触发账号安全和反爬，应以 ATO 为入口、反爬为辅助。 |
| 是否存在过拟合风险 | 中。接口访问是下游作恶方式，不是 ATO 成立必要条件。 |
| 是否需要修改 ATO entrypoint / workflow / response contract | 不需要。 |
| 是否需要修改通用 scenario contract | 不需要。 |

### R2-03 - 高粉 / 达人 / 创作者账号被盗

| 字段 | 结果 |
|---|---|
| question_id | ATO_PUBLIC_Q13 |
| 用户问题 | 创作者/达人账号被盗后发链接，怎么判断影响范围？ |
| 预期 intent | `single_case_judgement` |
| 实际应触发 workflow | `single_case_judgement -> governance_design` |
| 是否多意图 | 是。既要判断 ATO，又要评估影响范围和治理优先级。 |
| 是否需要 Data Agent | 需要，若要评估触达、传播、粉丝影响、链接点击或下游承接范围。 |
| 应调用的核心 Skill / 证据卡 / Data Agent 模板 | `account_security_expert_skill`；`traffic_diversion_interception_skill` 作为辅助；内容/链接风险证据卡；Data Agent 影响范围问题模板。 |
| 预期输出结构 | 当前 ATO 证据等级、链接/导流下游风险、影响范围、缺失证据、短期止损、人工复核。 |
| 必须包含的边界提醒 | 高粉账号提高治理优先级和影响评估要求，但不降低 ATO 证据标准；发链接不是 ATO 的充分证据。 |
| 是否符合 ATO response contract | 符合，可组合单 case输出和治理方案输出。 |
| 是否存在路由歧义 | 中。可能进入导流截流场景，但入口仍是账号安全。 |
| 是否存在过拟合风险 | 中。不能把“高粉 + 发链接”写成 ATO 本质规则。 |
| 是否需要修改 ATO entrypoint / workflow / response contract | 不需要。 |
| 是否需要修改通用 scenario contract | 不需要。 |

### R2-04 - 账号租借 / 共享 / 交易 vs ATO

| 字段 | 结果 |
|---|---|
| question_id | ATO_PUBLIC_Q15 |
| 用户问题 | 账号租借/共享和 ATO 怎么区分？ |
| 预期 intent | `single_case_judgement` |
| 实际应触发 workflow | `single_case_judgement` |
| 是否多意图 | 否。核心是边界判断。 |
| 是否需要 Data Agent | 具体 case 需要；概念边界不需要。 |
| 应调用的核心 Skill / 证据卡 / Data Agent 模板 | `account_security_expert_skill`；ATO 反证规则；账号交易/租借边界证据卡。 |
| 预期输出结构 | 当前结论、ATO 支持证据、租借/共享反证、缺失证据、下一步补证。 |
| 必须包含的边界提醒 | 租借/共享/交易可能是号主主动交付控制权，不等同于被盗；也不能因为存在共享迹象就直接排除胁迫、欺诈或二次接管。 |
| 是否符合 ATO response contract | 符合。 |
| 是否存在路由歧义 | 低。 |
| 是否存在过拟合风险 | 中。不能把“多设备/异地/共享设备”直接判为 ATO。 |
| 是否需要修改 ATO entrypoint / workflow / response contract | 不需要。 |
| 是否需要修改通用 scenario contract | 不需要。 |

### R2-05 - 验证码泄露与平台责任边界

| 字段 | 结果 |
|---|---|
| question_id | ATO_PUBLIC_Q16 |
| 用户问题 | 用户泄露验证码和平台责任边界怎么判断？ |
| 预期 intent | `governance_design` |
| 实际应触发 workflow | `single_case_judgement -> governance_design` |
| 是否多意图 | 是。先判断账号接管链路，再判断平台防护与责任边界。 |
| 是否需要 Data Agent | 若验证具体 case，需要查询验证码登录、风险提示、二次验证、异常环境、止损链路。 |
| 应调用的核心 Skill / 证据卡 / Data Agent 模板 | `account_security_expert_skill`；sms_code_leakage_login_check；账号安全治理证据卡。 |
| 预期输出结构 | 证据判断、平台侧可验证证据、用户责任线索、平台防护链路、治理建议、人工复核。 |
| 必须包含的边界提醒 | 用户泄露验证码是风险入口线索，不等于平台无责任；需要看异常环境识别、风险提示、二次验证、敏感动作保护和事后止损是否充分。 |
| 是否符合 ATO response contract | 符合，使用单 case输出 + 治理方案输出。 |
| 是否存在路由歧义 | 中。可能被误路由为纯治理问题，实际应先做证据判断。 |
| 是否存在过拟合风险 | 低。 |
| 是否需要修改 ATO entrypoint / workflow / response contract | 不需要。 |
| 是否需要修改通用 scenario contract | 不需要。 |

### R2-06 - Data Agent SQL-only 降级

| 字段 | 结果 |
|---|---|
| question_id | ATO_PUBLIC_Q08 |
| 用户问题 | Data Agent 只返回 SQL，能不能下结论？ |
| 预期 intent | `dataagent_result_interpretation` |
| 实际应触发 workflow | `dataagent_result_interpretation` |
| 是否多意图 | 否。 |
| 是否需要 Data Agent | 不需要；已有返回，下一步是执行 SQL 或请求执行结果。 |
| 应调用的核心 Skill / 证据卡 / Data Agent 模板 | Data Agent markdown parser rules；SQL execution follow-up template；ATO response contract。 |
| 预期输出结构 | status=`sql_only/pending_execution`、数据发现为空、证据链不可用、缺失证据、next_action、人工复核。 |
| 必须包含的边界提醒 | SQL-only 是取证计划，不是查询结果；不得进入强/中/弱证据链；不能生成 ATO 强结论。 |
| 是否符合 ATO response contract | 符合 Data Agent 返回解释格式。 |
| 是否存在路由歧义 | 低。 |
| 是否存在过拟合风险 | 低。 |
| 是否需要修改 ATO entrypoint / workflow / response contract | 不需要。 |
| 是否需要修改通用 scenario contract | 不需要。 |

### R2-07 - Data Agent partial / no_permission 降级

| 字段 | 结果 |
|---|---|
| question_id | ATO_PUBLIC_Q09 |
| 用户问题 | Data Agent 返回 partial / no_permission，怎么降级？ |
| 预期 intent | `dataagent_result_interpretation` |
| 实际应触发 workflow | `dataagent_result_interpretation` |
| 是否多意图 | 否。 |
| 是否需要 Data Agent | 不需要；已有返回，下一步是补权限、补 provider 或人工复核。 |
| 应调用的核心 Skill / 证据卡 / Data Agent 模板 | Data Agent error/degrade policy；parser rules；ATO response contract。 |
| 预期输出结构 | data_findings、permission_notes、missing_evidence、quality_risks、provider_conclusion_hint、Dennis final judgement、next action。 |
| 必须包含的边界提醒 | partial / no_permission 必须降级；无权限域要进入 missing_evidence 和 permission_notes；Data Agent 的结论性文字只能进入 provider_conclusion_hint。 |
| 是否符合 ATO response contract | 符合。 |
| 是否存在路由歧义 | 低。 |
| 是否存在过拟合风险 | 低。 |
| 是否需要修改 ATO entrypoint / workflow / response contract | 不需要。 |
| 是否需要修改通用 scenario contract | 不需要。 |

### R2-08 - 有异常内容发布但不能直接确认 ATO

| 字段 | 结果 |
|---|---|
| question_id | ATO_PUBLIC_Q04 |
| 用户问题 | 有发布色情/招嫖内容，是否一定是盗号？ |
| 预期 intent | `single_case_judgement` |
| 实际应触发 workflow | `single_case_judgement` |
| 是否多意图 | 否。 |
| 是否需要 Data Agent | 若要验证具体 case，需要补登录/授权/token/设备/内容发布时间链路。 |
| 应调用的核心 Skill / 证据卡 / Data Agent 模板 | `account_security_expert_skill`；ATO feature layering；content risk evidence。 |
| 预期输出结构 | 当前结论、支持证据、反证、缺失证据、下一步补证。 |
| 必须包含的边界提醒 | 色情/招嫖发布是下游作恶表象，既不是 ATO 成立必要条件，也不是充分条件；还要排除本人作恶、账号租借、共享/交易、内容误判。 |
| 是否符合 ATO response contract | 符合。 |
| 是否存在路由歧义 | 中。可能被误路由到内容治理，但问题核心是账号安全边界。 |
| 是否存在过拟合风险 | 高。容易把公开行业常见表象写成 ATO 本质规则。 |
| 是否需要修改 ATO entrypoint / workflow / response contract | 不需要。 |
| 是否需要修改通用 scenario contract | 不需要。 |

### R2-09 - 无发布行为但不能反向排除 ATO

| 字段 | 结果 |
|---|---|
| question_id | ATO_PUBLIC_Q03 |
| 用户问题 | 没有发布行为，能不能排除盗号？ |
| 预期 intent | `single_case_judgement` |
| 实际应触发 workflow | `single_case_judgement`，若用户贴 Data Agent 结果也可走 `dataagent_result_interpretation` |
| 是否多意图 | 低。 |
| 是否需要 Data Agent | 不一定；如需查其他下游行为或登录链路则需要。 |
| 应调用的核心 Skill / 证据卡 / Data Agent 模板 | `account_security_expert_skill`；ATO label refinement；ATO feature layering。 |
| 预期输出结构 | 当前结论、为什么、反证、缺失证据、下一步。 |
| 必须包含的边界提醒 | 无发布不能反向排除 ATO；可能存在互动滥用、接口访问、活动套利、资料变更、延迟作恶或仅登录控制。 |
| 是否符合 ATO response contract | 符合。 |
| 是否存在路由歧义 | 低。 |
| 是否存在过拟合风险 | 高。容易把“发布内容”当成 ATO 的必要表象。 |
| 是否需要修改 ATO entrypoint / workflow / response contract | 不需要。 |
| 是否需要修改通用 scenario contract | 不需要。 |

## 3. 重点检查结论

| 检查项 | 结论 |
|---|---|
| 是否仍然坚持 Data Agent evidence provider 边界 | 通过。Q08/Q09 明确 Data Agent 返回只进入 evidence / provider_conclusion_hint，不替代 Dennis final judgement。 |
| 是否仍然由 Dennis 主 Agent 生成 dennis_final_judgement | 通过。所有 Data Agent 解释类 case 均要求 Dennis 单独生成结论。 |
| 是否没有把发布异常内容当成 ATO 必要条件 | 通过。Q03/Q04/Q11/Q12 明确下游作恶与 ATO 发生方式分离。 |
| 是否没有把无发布当成非盗号反证 | 通过。Q03 明确无发布不能反向排除 ATO。 |
| 是否没有把账号租借 / 共享 / 交易直接误判为 ATO | 通过。Q15 要求作为边界和反证处理。 |
| 是否能识别高粉 / 达人账号被盗后的影响范围和治理差异 | 通过。Q13 走单 case + 治理，不降低证据标准。 |
| 是否能区分用户责任线索和平台侧可验证证据 | 通过。Q16 明确验证码泄露是用户侧线索，但平台侧仍需验证防护链路。 |
| 是否能把下游作恶方式从 ATO 发生方式中拆开 | 通过。9 个 case 均遵循发生方式 / 下游作恶双层结构。 |
| 是否避免把公开行业问法写成内部事实 | 通过。所有 case 仅作为问法和路由压测，不作为内部数据发现。 |

## 4. 汇总

### 4.1 路由准确率

9/9 通过，路由准确率 100%。

判定口径：
- 每个问题都能落到现有 ATO workflow。
- 每个问题都能套用现有 ATO response contract。
- 没有发现必须修改 ATO overlay 或通用 scenario contract 才能承载的问题。

### 4.2 Workflow 覆盖

| workflow | 覆盖 case |
|---|---|
| `single_case_judgement` | R2-02, R2-03, R2-04, R2-05, R2-08, R2-09 |
| `dataagent_question_generation` | R2-01 |
| `dataagent_result_interpretation` | R2-06, R2-07 |
| `governance_design` | R2-02, R2-03, R2-05 |
| `batch_case_clustering` | 本轮未覆盖 |
| `generalization_and_recall` | 本轮未覆盖 |
| `review_and_skill_distillation` | 本轮未覆盖 |

说明：本轮目标聚焦扩展问法中的边界和降级，不要求覆盖所有 workflow。上一轮真实问法 trial 已覆盖批量分层、回捞和复盘沉淀。

### 4.3 最容易误路由的问题

| 问题 | 风险 | 推荐处理 |
|---|---|---|
| R2-02 被盗后爬虫/接口访问 | 容易直接路由反爬，忽略账号接管入口 | 先 `single_case_judgement`，再调用 `anti_crawler_expert_skill` 辅助治理。 |
| R2-03 创作者/达人被盗后发链接 | 容易直接路由导流/内容治理，忽略 ATO 证据标准 | 先判断账号接管，再评估导流/影响范围。 |
| R2-05 验证码泄露责任边界 | 容易只做治理讨论，忽略证据判断 | 先区分用户责任线索与平台可验证防护证据。 |
| R2-08 有异常内容发布 | 容易误判为 ATO，或被路由到纯内容治理 | 发布内容只是下游表象，必须补登录/授权/token/设备链路。 |

### 4.4 最容易过度依赖 Data Agent 的问题

| 问题 | 原因 | 降级原则 |
|---|---|---|
| R2-01 互动滥用识别 | 需要下游行为取证，但 Data Agent 可能只能给离线聚合 | 只把 Data Agent 输出作为 provider evidence，缺实时日志时保留 limitations。 |
| R2-02 接口访问 / 资产窃取 | 可能需要实时日志、NG、反爬策略、在线图谱 | Data Agent-only 下不能强结论，必要时建议 realtime_log / anti_crawler 侧补证。 |
| R2-03 高粉账号影响范围 | 影响范围常涉及传播、触达、站外承接 | Data Agent 可做离线范围估计，最终影响等级需人工复核。 |
| R2-06 / R2-07 Data Agent 状态降级 | 容易把 SQL / partial 误当结果 | SQL-only 不进证据链，partial/no_permission 必须降级。 |

### 4.5 最容易过拟合表象特征的问题

| 问题 | 表象特征 | 防过拟合规则 |
|---|---|---|
| R2-01 | 点赞 / 关注 / 私信 | 下游互动是子标签，不能作为 ATO 必要条件。 |
| R2-02 | 接口访问 / 资产访问 | 下游资产访问不等于 ATO，需先证明登录态接管。 |
| R2-03 | 高粉 / 发链接 | 影响等级不改变证据标准。 |
| R2-08 | 色情 / 招嫖发布 | 内容作恶不是 ATO 充分条件。 |
| R2-09 | 无发布 | 无发布不是非盗号反证。 |

### 4.6 是否建议修改 ATO overlay

暂不建议。

理由：
- 9 个扩展问题均能被现有 ATO router / workflows / response contract 承载。
- 误路由风险可以通过执行顺序和边界提醒解决，不需要改入口层。
- 若后续真实使用中 R2-02 / R2-03 / R2-05 高频出现，可再给 ATO router 增加跨 Skill 示例，不必现在改。

### 4.7 是否建议修改通用 scenario contract

暂不建议。

理由：
- 通用 scenario contract 已能支持单 case、Data Agent、治理、复盘等流程。
- 本轮暴露的是 ATO 场景内跨 Skill 组合问题，不是通用 contract 缺口。

### 4.8 是否修改核心 Skill

未修改核心 Skill。

### 4.9 下一步建议

P0：
- 将 R2-02、R2-03、R2-05、R2-08 作为下一轮真实使用日志重点观察项，关注是否发生误路由。
- 在真实问答中持续检查“先 ATO 入口，再下游场景辅助”的执行顺序。

P1：
- 若 R2-02 高频出现，可新增 ATO × anti_crawler 联动示例。
- 若 R2-03 高频出现，可新增 ATO × traffic_diversion / content risk 联动示例。
- 若 R2-05 高频出现，可新增验证码泄露责任边界的标准输出示例。

P2：
- 暂不进入内部系统最小部署包调整，先用 v2 regression 结果继续收集真实盗号同学问法。

