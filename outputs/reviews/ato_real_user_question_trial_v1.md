# ATO 真实问法试运行集 v1

## 1. 目标

验证内部盗号同学用自然语言使用 Dennis Risk Agent 时，Agent 是否能稳定：

- 理解问题。
- 选择 ATO workflow。
- 判断是否需要 Data Agent。
- 调用已有 Skill / 证据卡 / Data Agent 模板。
- 输出可执行结论和下一步动作。
- 保留证据边界，避免过拟合单批样本。

本轮不调用 Data Agent，不修改核心 Skill，不编造真实数据，不暴露完整 user_id。

## 2. 真实问法试运行

### Trial 01：单 case 研判

| 字段 | 内容 |
|---|---|
| 用户问题 | 用户说 5 月 4 日被陌生人扫码后账号异常，后面被封了，帮我判断是不是盗号。 |
| 识别 intent | single_case_judgement |
| 触发 workflow | `single_case_judgement` |
| 是否需要 Data Agent | 需要，若缺登录/授权/设备/token/下游行为证据 |
| 应调用的已有 Skill / 证据卡 / Data Agent 模板 | `account_security_expert_skill`；ATO evidence boundary；Web 扫码登录类 query template |
| 预期输出结构 | 单 case 输出：当前结论、为什么、支持证据、反证、缺失证据、下一步补证、是否需要 Data Agent、是否人工复核 |
| 必须包含的边界提醒 | 用户说扫码不是事实；封禁不等于盗号；需要异常登录/授权/账号接管链路 |
| Agent 应给出的下一步动作 | 生成只读取证问题，查 Web 扫码/异步登录、登录环境突变、账号安全风险策略、下游行为 |
| 是否符合 ATO response contract | 是 |
| 是否存在路由歧义 | 低 |
| 是否需要补充 ATO overlay / scenario contract | 否 |

### Trial 02：客诉可信度判断

| 字段 | 内容 |
|---|---|
| 用户问题 | 用户申诉说被盗，但只有人工备注，没有明显数据证据，这个能不能认？ |
| 识别 intent | single_case_judgement |
| 触发 workflow | `single_case_judgement` |
| 是否需要 Data Agent | 如果要判断可信度，需要；如果只讲原则，不需要 |
| 应调用的已有 Skill / 证据卡 / Data Agent 模板 | `account_security_expert_skill`；ATO response contract |
| 预期输出结构 | 当前结论、为什么、支持证据、反证、缺失证据、下一步补证 |
| 必须包含的边界提醒 | 人工备注只能作为线索，不能当事实；缺数据证据时应输出 insufficient_support |
| Agent 应给出的下一步动作 | 要求补 user_id/case_id、时间窗口、异常行为，再生成取证问题 |
| 是否符合 ATO response contract | 是 |
| 是否存在路由歧义 | 低 |
| 是否需要补充 ATO overlay / scenario contract | 否 |

### Trial 03：批量样本分层

| 字段 | 内容 |
|---|---|
| 用户问题 | 这批盗号客诉帮我分层，哪些是扫码，哪些是钓鱼，哪些是不确定。 |
| 识别 intent | batch_case_clustering |
| 触发 workflow | `batch_case_clustering` |
| 是否需要 Data Agent | 可选；先基于标签/备注分层，验证时再需要 |
| 应调用的已有 Skill / 证据卡 / Data Agent 模板 | ATO batch schema；ATO label taxonomy；`account_security_expert_skill` |
| 预期输出结构 | 批量输出：样本总览、ATO 发生方式分层、下游作恶方式分层、高置信正例、反例/不确定、待补证样本 |
| 必须包含的边界提醒 | 人工标签是线索；分层不是最终定性；空值不能自动补标签 |
| Agent 应给出的下一步动作 | 输出分层结果，并给需要 Data Agent 验证的分层清单 |
| 是否符合 ATO response contract | 是 |
| 是否存在路由歧义 | 低 |
| 是否需要补充 ATO overlay / scenario contract | 否 |

### Trial 04：无发布边界

| 字段 | 内容 |
|---|---|
| 用户问题 | 这批样本大部分没有发布行为，是不是不能算盗号？ |
| 识别 intent | dataagent_result_interpretation |
| 触发 workflow | `dataagent_result_interpretation`，辅以 `single_case_judgement` |
| 是否需要 Data Agent | 不需要，用户已给出数据发现；若要查其他下游行为再需要 |
| 应调用的已有 Skill / 证据卡 / Data Agent 模板 | ATO label refinement；ATO feature layering |
| 预期输出结构 | 当前结论、为什么、反证、缺失证据、下一步补证 |
| 必须包含的边界提醒 | 无发布不能反向排除 ATO；发布异常内容不是 ATO 成立必要条件 |
| Agent 应给出的下一步动作 | 建议按下游作恶方式分支轻量探查点赞/关注/私信/接口访问/活动/导流/养号 |
| 是否符合 ATO response contract | 是 |
| 是否存在路由歧义 | 中；也可归为边界型 single_case_judgement |
| 是否需要补充 ATO overlay / scenario contract | 否 |

### Trial 05：下游作恶分层

| 字段 | 内容 |
|---|---|
| 用户问题 | 盗号后除了发内容，还可能做点赞、爬虫、活动套利吗？这批样本怎么分？ |
| 识别 intent | batch_case_clustering |
| 触发 workflow | `batch_case_clustering`，辅以 `evidence_planning` |
| 是否需要 Data Agent | 分层原则不需要；验证每类下游行为需要 |
| 应调用的已有 Skill / 证据卡 / Data Agent 模板 | ATO label refinement；scenario workflow contract |
| 预期输出结构 | 下游作恶方式分层：发布、互动、接口访问/资产窃取、活动套利、导流、养号、未验证 |
| 必须包含的边界提醒 | 下游作恶是子标签，不是 ATO 成立必要条件 |
| Agent 应给出的下一步动作 | 先按下游分支定义取证目标，再选择低成本 Data Agent 问题 |
| 是否符合 ATO response contract | 是 |
| 是否存在路由歧义 | 中；包含概念解释和批量分层 |
| 是否需要补充 ATO overlay / scenario contract | 否 |

### Trial 06：Data Agent 问题生成

| 字段 | 内容 |
|---|---|
| 用户问题 | 帮我生成一个 Data Agent 问题，查这批扫码盗号有没有共性。 |
| 识别 intent | dataagent_question_generation |
| 触发 workflow | `dataagent_question_generation` |
| 是否需要 Data Agent | 需要，但当前只生成问题 |
| 应调用的已有 Skill / 证据卡 / Data Agent 模板 | ATO Data Agent query templates；scenario response contract |
| 预期输出结构 | Data Agent 问题输出：可复制问题、查询目标、样本范围、时间窗口、数据域、输出要求、降级规则 |
| 必须包含的边界提醒 | Data Agent 只读取证，不做最终判断；不写真表名/字段/SQL/API |
| Agent 应给出的下一步动作 | 生成 P0 Web 扫码登录共性验证问题 |
| 是否符合 ATO response contract | 是 |
| 是否存在路由歧义 | 低 |
| 是否需要补充 ATO overlay / scenario contract | 否 |

### Trial 07：Data Agent 返回解释

| 字段 | 内容 |
|---|---|
| 用户问题 | Data Agent 说 13/15 有异步 Web 登录，但只有 5/15 有发布，这说明什么？ |
| 识别 intent | dataagent_result_interpretation |
| 触发 workflow | `dataagent_result_interpretation` |
| 是否需要 Data Agent | 不需要，已有返回 |
| 应调用的已有 Skill / 证据卡 / Data Agent 模板 | ATO feature layering；Data Agent result interpretation |
| 预期输出结构 | 数据发现、provider_conclusion_hint、Dennis final judgement、强/中/弱证据、反证、缺失证据、下一步 |
| 必须包含的边界提醒 | 13/15、5/15 是本批统计；发布不是必要条件；无发布不是反证 |
| Agent 应给出的下一步动作 | 把本批沉淀为 Web 扫码登录类 ATO，发布作为下游子标签；建议分支轻量探查 |
| 是否符合 ATO response contract | 是 |
| 是否存在路由歧义 | 低 |
| 是否需要补充 ATO overlay / scenario contract | 否 |

### Trial 08：举一反三 / 回捞

| 字段 | 内容 |
|---|---|
| 用户问题 | 基于这些样本，怎么回捞同类盗号？哪些特征能用，哪些不能用？ |
| 识别 intent | generalization_and_recall |
| 触发 workflow | `generalization_and_recall` |
| 是否需要 Data Agent | 不一定；生成候选特征不需要，验证需要 |
| 应调用的已有 Skill / 证据卡 / Data Agent 模板 | ATO feature layering；anti-overfitting rules |
| 预期输出结构 | 原始观测、数据发现、候选特征、机制特征、不建议使用的表象特征、正反例验证方案、误伤风险 |
| 必须包含的边界提醒 | case 回扫生成假设，不直接生成线上策略；样本统计和具体策略名不写 Skill |
| Agent 应给出的下一步动作 | 优先验证 Web 扫码/异步登录、登录环境突变、无历史环境、账号安全风险策略命中 |
| 是否符合 ATO response contract | 是 |
| 是否存在路由歧义 | 低 |
| 是否需要补充 ATO overlay / scenario contract | 否 |

### Trial 09：治理方案

| 字段 | 内容 |
|---|---|
| 用户问题 | 这类扫码盗号应该怎么治理，是验证、踢 token、封禁，还是用户教育？ |
| 识别 intent | governance_design |
| 触发 workflow | `governance_design` |
| 是否需要 Data Agent | 框架治理不需要；评估命中量/效果需要 |
| 应调用的已有 Skill / 证据卡 / Data Agent 模板 | `account_security_expert_skill`；risk_governance_design_skill |
| 预期输出结构 | 短期止损、中期识别、长期治理、登录前/中/后、token/session、下游作恶、用户体验、业务协同 |
| 必须包含的边界提醒 | 不自动封号；高风险动作需人工确认；踢 token 要考虑误伤和恢复 |
| Agent 应给出的下一步动作 | 给分层治理：登录中验证、登录后提醒/二验、敏感动作限权、号主恢复、用户教育 |
| 是否符合 ATO response contract | 是 |
| 是否存在路由歧义 | 低 |
| 是否需要补充 ATO overlay / scenario contract | 否 |

### Trial 10：复盘沉淀

| 字段 | 内容 |
|---|---|
| 用户问题 | 这批 case 能沉淀什么？要不要回写 account_security_expert_skill？ |
| 识别 intent | review_and_skill_distillation |
| 触发 workflow | `review_and_skill_distillation` |
| 是否需要 Data Agent | 不需要，除非要求补充验证 |
| 应调用的已有 Skill / 证据卡 / Data Agent 模板 | ATO feature layering；scenario contracts；eval/regression assets |
| 预期输出结构 | 可回写 Skill、只进 eval/review、需更多数据验证、不应沉淀、下一步建议 |
| 必须包含的边界提醒 | 单批比例、具体策略名、时间窗、具体备注不回写 |
| Agent 应给出的下一步动作 | 建议暂不回写核心 Skill，先沉淀 eval/review 并补正反例验证 |
| 是否符合 ATO response contract | 是 |
| 是否存在路由歧义 | 低 |
| 是否需要补充 ATO overlay / scenario contract | 否 |

### Trial 11：反例 / 误报

| 字段 | 内容 |
|---|---|
| 用户问题 | 用户说被盗，但实际可能是账号租借或本人操作，Agent 应该怎么判断？ |
| 识别 intent | single_case_judgement |
| 触发 workflow | `single_case_judgement`，辅以 `evidence_planning` |
| 是否需要 Data Agent | 如果要验证具体 case，需要 |
| 应调用的已有 Skill / 证据卡 / Data Agent 模板 | `account_security_expert_skill`；ATO counter evidence rules |
| 预期输出结构 | 当前结论、支持证据、反证、缺失证据、下一步补证 |
| 必须包含的边界提醒 | 用户申诉不等于盗号事实；账号租借/本人操作是重要反证 |
| Agent 应给出的下一步动作 | 查历史设备、登录方式、本人常用环境、租借/交易线索、下游动作主体 |
| 是否符合 ATO response contract | 是 |
| 是否存在路由歧义 | 中；也可能是合法授权/账号交易边界 |
| 是否需要补充 ATO overlay / scenario contract | 否 |

### Trial 12：多意图

| 字段 | 内容 |
|---|---|
| 用户问题 | 帮我看这批是不是盗号，并生成 Data Agent 查询问题，再说下能不能回捞。 |
| 识别 intent | batch_case_clustering + dataagent_question_generation + generalization_and_recall |
| 触发 workflow | `batch_case_clustering` → `dataagent_question_generation` → `generalization_and_recall` |
| 是否需要 Data Agent | 需要生成问题，但本轮不调用 |
| 应调用的已有 Skill / 证据卡 / Data Agent 模板 | ATO batch clustering；Data Agent templates；feature layering |
| 预期输出结构 | 先分层，再给 Data Agent 问题，最后给候选回捞特征和验证边界 |
| 必须包含的边界提醒 | 先取证再回捞；回扫是生成假设，不直接上线策略 |
| Agent 应给出的下一步动作 | 输出分层、P0/P1 查询问题、候选机制特征、误伤风险 |
| 是否符合 ATO response contract | 是 |
| 是否存在路由歧义 | 中高；多意图较多但顺序清晰 |
| 是否需要补充 ATO overlay / scenario contract | 否 |

### Trial 13：token/session 问法

| 字段 | 内容 |
|---|---|
| 用户问题 | 用户没有明显重新登录，但账号后面异常了，会不会是 token 或 session 被复用？ |
| 识别 intent | single_case_judgement |
| 触发 workflow | `single_case_judgement`，辅以 `dataagent_question_generation` |
| 是否需要 Data Agent | 需要验证 token/session、设备/IP/UA、下游动作 |
| 应调用的已有 Skill / 证据卡 / Data Agent 模板 | token_reuse_or_session_hijack_check；`account_security_expert_skill` |
| 预期输出结构 | 当前结论、证据链、反证、缺失证据、Data Agent 问题 |
| 必须包含的边界提醒 | 无重新登录不等于 token 泄露成立；需 token/session 与环境冲突证据 |
| Agent 应给出的下一步动作 | 生成 token/session 只读取证问题，查登录态使用环境和下游动作 |
| 是否符合 ATO response contract | 是 |
| 是否存在路由歧义 | 低 |
| 是否需要补充 ATO overlay / scenario contract | 否 |

### Trial 14：钓鱼 / 验证码

| 字段 | 内容 |
|---|---|
| 用户问题 | 用户说点了会员领取链接，输过手机号和验证码，后面账号被封，这像不像钓鱼盗号？ |
| 识别 intent | single_case_judgement |
| 触发 workflow | `single_case_judgement` |
| 是否需要 Data Agent | 需要验证 web 短信验证码登录、设备/IP、发布/敏感动作 |
| 应调用的已有 Skill / 证据卡 / Data Agent 模板 | phishing_web_login_check；sms_code_leakage_login_check |
| 预期输出结构 | 当前结论、支持证据、反证、缺失证据、下一步补证 |
| 必须包含的边界提醒 | 用户说输入验证码只是线索；需要 web 登录和下游动作链路 |
| Agent 应给出的下一步动作 | 生成钓鱼/web短信验证码登录取证问题 |
| 是否符合 ATO response contract | 是 |
| 是否存在路由歧义 | 中；钓鱼和短信泄露双路径 |
| 是否需要补充 ATO overlay / scenario contract | 否 |

### Trial 15：内容作恶误判

| 字段 | 内容 |
|---|---|
| 用户问题 | 账号发了招嫖视频，是不是就能认定账号被盗？ |
| 识别 intent | single_case_judgement |
| 触发 workflow | `single_case_judgement` |
| 是否需要 Data Agent | 需要，如果要判断 ATO |
| 应调用的已有 Skill / 证据卡 / Data Agent 模板 | ATO feature layering；content/downstream abuse evidence |
| 预期输出结构 | 当前结论、为什么、支持证据、反证、缺失证据 |
| 必须包含的边界提醒 | 发布招嫖是下游作恶表象，不是 ATO 成立必要或充分条件 |
| Agent 应给出的下一步动作 | 查异常登录/授权/token/设备链路和发布主体一致性 |
| 是否符合 ATO response contract | 是 |
| 是否存在路由歧义 | 中；可能转导流/内容治理 |
| 是否需要补充 ATO overlay / scenario contract | 否 |

### Trial 16：缺输入

| 字段 | 内容 |
|---|---|
| 用户问题 | 帮我查一个盗号客诉，用户说上周被盗，但我还没整理 user_id。 |
| 识别 intent | dataagent_question_generation |
| 触发 workflow | `dataagent_question_generation` |
| 是否需要 Data Agent | 当前不能生成可执行问题，缺最小输入 |
| 应调用的已有 Skill / 证据卡 / Data Agent 模板 | minimum input validation；ATO Data Agent question template |
| 预期输出结构 | missing_input_request：需要 user_id/case_id、时间窗口、异常行为 |
| 必须包含的边界提醒 | 缺 user_id 或时间窗口时不进入 Data Agent 取数 |
| Agent 应给出的下一步动作 | 要求补 user_id/case_id、异常时间、业务场景、目标动作 |
| 是否符合 ATO response contract | 是 |
| 是否存在路由歧义 | 低 |
| 是否需要补充 ATO overlay / scenario contract | 可选：后续可在 response contract 中明确 missing_input 格式 |

### Trial 17：已有 Data Agent SQL-only

| 字段 | 内容 |
|---|---|
| 用户问题 | Data Agent 只生成了 SQL，没有执行结果，这个能不能作为证据？ |
| 识别 intent | dataagent_result_interpretation |
| 触发 workflow | `dataagent_result_interpretation` |
| 是否需要 Data Agent | 不需要；需要下一步执行 SQL 或获取结果 |
| 应调用的已有 Skill / 证据卡 / Data Agent 模板 | Data Agent markdown parser rules；SQL-only boundary |
| 预期输出结构 | 当前结论、为什么、缺失证据、下一步动作 |
| 必须包含的边界提醒 | SQL-only 是取证计划，不是证据；不得进入强/中证据链 |
| Agent 应给出的下一步动作 | 请求执行 SQL 或粘贴执行聚合结果 |
| 是否符合 ATO response contract | 是 |
| 是否存在路由歧义 | 低 |
| 是否需要补充 ATO overlay / scenario contract | 否 |

### Trial 18：迁移到其他场景

| 字段 | 内容 |
|---|---|
| 用户问题 | ATO 这个入口层如果跑通了，后面反爬和群控也能这么接吗？ |
| 识别 intent | review_and_skill_distillation |
| 触发 workflow | `review_and_skill_distillation` |
| 是否需要 Data Agent | 不需要 |
| 应调用的已有 Skill / 证据卡 / Data Agent 模板 | scenario_intent_router_contract；scenario_workflow_contract；scenario_response_contract |
| 预期输出结构 | 可复用部分、需要场景专属 overlay、下一步建议 |
| 必须包含的边界提醒 | ATO 是第一个 scenario overlay，不改变 Dennis Risk Agent 通用定位 |
| Agent 应给出的下一步动作 | 建议按同样模式设计 anti_crawler / group_control overlay |
| 是否符合 ATO response contract | 是，但更适合 scenario_response_contract |
| 是否存在路由歧义 | 低 |
| 是否需要补充 ATO overlay / scenario contract | 否 |

## 3. 汇总

### 3.1 真实问法覆盖是否充分

覆盖充分。

已覆盖：
- 单 case 研判。
- 客诉可信度。
- 批量分层。
- 无发布边界。
- 下游作恶分层。
- Data Agent 问题生成。
- Data Agent 返回解释。
- 举一反三 / 回捞。
- 治理方案。
- 复盘沉淀。
- 反例 / 误报。
- 多意图。
- token/session。
- 钓鱼 / 验证码。
- 内容作恶误判。
- 缺输入。
- SQL-only。
- 跨场景迁移。

### 3.2 哪些问法最容易误路由

- Trial 04：无发布边界，可能路由到 single_case_judgement 或 dataagent_result_interpretation。
- Trial 05：下游作恶分层，可能路由到 batch_case_clustering 或 evidence_planning。
- Trial 12：多意图，容易漏掉 generalization_and_recall。
- Trial 15：内容作恶误判，可能转到导流 / 内容治理，需要先判断是否有 ATO 链路。

### 3.3 哪些问法最容易过度依赖 Data Agent

- Trial 02：只有人工备注时，Agent 可能直接要求查数；实际可先输出“不能认”的原则，再给补证。
- Trial 06：生成问题时不应假装已经查数。
- Trial 08：回捞建议应先做特征分层，再决定是否需要 Data Agent 验证。
- Trial 16：缺 user_id 时不能生成可执行 Data Agent 问题。

### 3.4 哪些问法最容易过拟合样本

- Trial 04：把“无发布”误当非盗号反证。
- Trial 07：把 13/15、5/15 写成长期规则。
- Trial 08：把单批特征直接当回捞策略。
- Trial 15：把发布招嫖内容当 ATO 充分条件。

### 3.5 是否需要修改 ATO entrypoint / workflow / response contract

暂不需要。

可选后续增强：
- 在 response contract 增加 `missing_input_request` 格式。
- 在 intent router 中显式加入 `evidence_planning` 的 ATO 示例。
- 对“内容作恶但不一定 ATO”的跨 Skill 转交规则再细化。

### 3.6 是否需要现在做内部系统最小部署包

建议暂缓。

原因：
- 真实问法试运行覆盖较好，但还没有真实交互日志。
- 仍需验证缺输入、SQL-only、多意图、多场景转交的实际表现。
- 建议先做 1-2 轮真实同学试问，再固化最小部署包。

### 3.7 是否修改核心 Skill

未修改核心 Skill。

本轮只新增 `outputs/reviews/ato_real_user_question_trial_v1.md`。
