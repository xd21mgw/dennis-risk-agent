# ATO Public Industry Question Set v1

## 1. 定位

本文件基于公开互联网内容平台中常见的 account takeover / ATO / 账号被盗问题，扩展 Dennis Risk Agent 的 ATO 真实问法库。

边界：
- 公开行业说法只作为问法覆盖和场景启发，不作为内部事实。
- 不调用 Data Agent。
- 不写真实表名、字段名、SQL 或 API。
- 不暴露完整 user_id。
- Data Agent 仍只是 evidence provider。
- Dennis 主 Agent 负责 `dennis_final_judgement`。
- 不自动输出处罚、冻结、封禁、扣除或策略上线。

## 2. 公开行业 ATO 问题类型归纳

| 类型 | 内容平台常见问题 | 典型 Agent 任务 |
|---|---|---|
| 单账号是否被盗 | 用户称非本人登录、非本人发布、资料变化、账号被封 | 单 case 研判 |
| 客诉可信度判断 | 只有申诉文本或人工备注，没有数据证据 | 证据强度和补证判断 |
| 凭证泄露 / 钓鱼 / 验证码泄露 | 用户点击链接、扫码、输入手机号/验证码、第三方领取会员 | 判断登录入口和账号接管链路 |
| token/session 泄露或复用 | 用户无重新登录感知，但账号被操作 | token/session 与设备/IP/UA/行为冲突补证 |
| 盗号后发布异常内容 | 色情、招嫖、广告、导流链接、诈骗内容 | 区分 ATO 发生方式和下游作恶 |
| 盗号后互动滥用 | 私信、评论、点赞、关注、拉群、骚扰 | 下游作恶分层 |
| 盗号后爬虫 / 接口访问 / 资产窃取 | 登录态访问内容、关系链、主页、粉丝、价格、库存等 | 与反爬/资产保护联动 |
| 创作者 / 达人 / 高粉账号被盗 | 高影响账号发链接、诈骗、导流、改资料 | 影响范围和治理优先级评估 |
| 账号租借 / 共享 / 交易 | 用户主动交出账号、共享设备、租借实名 | ATO 反证和边界判断 |
| 批量样本分层 | 一批客诉中混有扫码、钓鱼、token、不确定、非盗号 | batch clustering |
| Data Agent 取证问题生成 | 需要查登录、授权、token、设备、发布、策略、下游行为 | 生成只读取证问题 |
| Data Agent 返回解释 | 返回 SQL-only、partial、no_permission、聚合统计 | 解释证据强度和降级 |
| 回捞同类风险 | 从一批样本抽象候选特征 | 特征分层和回捞优先级 |
| 治理与止损 | 验证、踢 token、敏感动作限权、用户恢复 | 治理方案 |
| 复盘与 Skill 沉淀 | 哪些规则能回写，哪些只进 eval | review and distillation |

## 3. ATO 公开行业问法集

### Q01

| 字段 | 内容 |
|---|---|
| question_id | ATO_PUBLIC_Q01 |
| 用户自然语言问题 | 用户说账号被盗，但我只看到有违规发布，能不能确认是盗号？ |
| 适用场景 | 单账号被盗判断 / 内容作恶边界 |
| 预期 intent | single_case_judgement |
| 预期 workflow | `single_case_judgement` |
| 是否需要 Data Agent | 需要，若缺登录/授权/token/设备链路 |
| 应调用的核心 Skill / 证据卡 / Data Agent 模板 | `account_security_expert_skill`；ATO evidence boundary；content/downstream evidence |
| 期望输出结构 | 当前结论、为什么、支持证据、反证、缺失证据、下一步补证 |
| 必须包含的边界提醒 | 违规发布是下游作恶表象，不是 ATO 成立充分条件 |
| 是否存在多意图 | 否 |
| 是否存在过拟合风险 | 高，容易把内容作恶等同盗号 |
| 是否适合加入 ATO 入口层回归 | 是 |

### Q02

| 字段 | 内容 |
|---|---|
| question_id | ATO_PUBLIC_Q02 |
| 用户自然语言问题 | 用户说扫码后被盗，数据要查哪些链路？ |
| 适用场景 | 扫码 / 授权登录取证规划 |
| 预期 intent | evidence_planning |
| 预期 workflow | `dataagent_question_generation` 或 `single_case_judgement → dataagent_question_generation` |
| 是否需要 Data Agent | 需要生成问题，但不直接调用 |
| 应调用的核心 Skill / 证据卡 / Data Agent 模板 | Web 扫码 / 异步登录 query template；ATO evidence boundary |
| 期望输出结构 | 目标证据、数据域、join path、质量风险、可复制 Data Agent 问题 |
| 必须包含的边界提醒 | 用户说扫码只是线索，需要授权/登录/设备/token/下游链路验证 |
| 是否存在多意图 | 是 |
| 是否存在过拟合风险 | 中 |
| 是否适合加入 ATO 入口层回归 | 是 |

### Q03

| 字段 | 内容 |
|---|---|
| question_id | ATO_PUBLIC_Q03 |
| 用户自然语言问题 | 没有发布行为，能不能排除盗号？ |
| 适用场景 | 无发布边界 |
| 预期 intent | single_case_judgement |
| 预期 workflow | `single_case_judgement` 或 `dataagent_result_interpretation` |
| 是否需要 Data Agent | 不一定；若要查其他下游行为则需要 |
| 应调用的核心 Skill / 证据卡 / Data Agent 模板 | ATO label refinement；ATO feature layering |
| 期望输出结构 | 当前结论、为什么、反证、缺失证据、下一步 |
| 必须包含的边界提醒 | 无发布不能反向排除 ATO；可能存在其他下游作恶或仅登录控制 |
| 是否存在多意图 | 否 |
| 是否存在过拟合风险 | 高 |
| 是否适合加入 ATO 入口层回归 | 是 |

### Q04

| 字段 | 内容 |
|---|---|
| question_id | ATO_PUBLIC_Q04 |
| 用户自然语言问题 | 有发布色情/招嫖内容，是否一定是盗号？ |
| 适用场景 | 下游作恶与 ATO 发生方式解耦 |
| 预期 intent | single_case_judgement |
| 预期 workflow | `single_case_judgement` |
| 是否需要 Data Agent | 需要，若要确认异常登录链路 |
| 应调用的核心 Skill / 证据卡 / Data Agent 模板 | ATO feature layering；content risk evidence |
| 期望输出结构 | 当前结论、支持证据、反证、缺失证据 |
| 必须包含的边界提醒 | 色情/招嫖是下游子标签，不是 ATO 必要或充分条件 |
| 是否存在多意图 | 否 |
| 是否存在过拟合风险 | 高 |
| 是否适合加入 ATO 入口层回归 | 是 |

### Q05

| 字段 | 内容 |
|---|---|
| question_id | ATO_PUBLIC_Q05 |
| 用户自然语言问题 | 这批客诉怎么区分扫码、钓鱼、验证码、token？ |
| 适用场景 | 批量样本发生方式分层 |
| 预期 intent | batch_case_clustering |
| 预期 workflow | `batch_case_clustering` |
| 是否需要 Data Agent | 可选，先按标签/描述分层，验证再需要 |
| 应调用的核心 Skill / 证据卡 / Data Agent 模板 | ATO label taxonomy；batch case schema |
| 期望输出结构 | 样本总览、ATO 发生方式分层、待补证样本 |
| 必须包含的边界提醒 | 人工标签不是事实；空值不能自动补类 |
| 是否存在多意图 | 否 |
| 是否存在过拟合风险 | 中 |
| 是否适合加入 ATO 入口层回归 | 是 |

### Q06

| 字段 | 内容 |
|---|---|
| question_id | ATO_PUBLIC_Q06 |
| 用户自然语言问题 | 这批样本哪些适合做正例，哪些只能做线索？ |
| 适用场景 | 回归样本筛选 |
| 预期 intent | batch_case_clustering |
| 预期 workflow | `batch_case_clustering → review_and_skill_distillation` |
| 是否需要 Data Agent | 可选；如果判断数据支撑度则需要 |
| 应调用的核心 Skill / 证据卡 / Data Agent 模板 | ATO batch management；regression selection rules |
| 期望输出结构 | 高置信正例、线索样本、反例、不确定、入回归建议 |
| 必须包含的边界提醒 | 正例必须有数据链路支撑；人工备注只能作为线索 |
| 是否存在多意图 | 是 |
| 是否存在过拟合风险 | 中 |
| 是否适合加入 ATO 入口层回归 | 是 |

### Q07

| 字段 | 内容 |
|---|---|
| question_id | ATO_PUBLIC_Q07 |
| 用户自然语言问题 | 人工备注能不能直接作为盗号标签？ |
| 适用场景 | 标签边界 |
| 预期 intent | single_case_judgement |
| 预期 workflow | `single_case_judgement` |
| 是否需要 Data Agent | 原则判断不需要；验证具体 case 需要 |
| 应调用的核心 Skill / 证据卡 / Data Agent 模板 | ATO response contract；feature layering |
| 期望输出结构 | 当前结论、为什么、缺失证据、下一步补证 |
| 必须包含的边界提醒 | 人工备注只能作为线索，不能直接作为事实 |
| 是否存在多意图 | 否 |
| 是否存在过拟合风险 | 中 |
| 是否适合加入 ATO 入口层回归 | 是 |

### Q08

| 字段 | 内容 |
|---|---|
| question_id | ATO_PUBLIC_Q08 |
| 用户自然语言问题 | Data Agent 只返回 SQL，能不能下结论？ |
| 适用场景 | SQL-only 边界 |
| 预期 intent | dataagent_result_interpretation |
| 预期 workflow | `dataagent_result_interpretation` |
| 是否需要 Data Agent | 不需要；需要下一步执行 SQL 或返回结果 |
| 应调用的核心 Skill / 证据卡 / Data Agent 模板 | markdown parser rules；SQL execution follow-up |
| 期望输出结构 | 当前结论、为什么、缺失证据、下一步 |
| 必须包含的边界提醒 | SQL-only 是取证计划，不能进入强/中/弱证据链 |
| 是否存在多意图 | 否 |
| 是否存在过拟合风险 | 低 |
| 是否适合加入 ATO 入口层回归 | 是 |

### Q09

| 字段 | 内容 |
|---|---|
| question_id | ATO_PUBLIC_Q09 |
| 用户自然语言问题 | Data Agent 返回 partial / no_permission，怎么降级？ |
| 适用场景 | Data Agent 状态降级 |
| 预期 intent | dataagent_result_interpretation |
| 预期 workflow | `dataagent_result_interpretation` |
| 是否需要 Data Agent | 不需要，已有返回 |
| 应调用的核心 Skill / 证据卡 / Data Agent 模板 | error/degrade policy；response contract |
| 期望输出结构 | 数据发现、缺失证据、permission_notes、dennis_final_judgement、next action |
| 必须包含的边界提醒 | no_permission / partial 必须降级，不能强结论 |
| 是否存在多意图 | 否 |
| 是否存在过拟合风险 | 低 |
| 是否适合加入 ATO 入口层回归 | 是 |

### Q10

| 字段 | 内容 |
|---|---|
| question_id | ATO_PUBLIC_Q10 |
| 用户自然语言问题 | 异常登录后没有下游作恶，怎么判断？ |
| 适用场景 | 登录控制但下游未观测 |
| 预期 intent | single_case_judgement |
| 预期 workflow | `single_case_judgement` |
| 是否需要 Data Agent | 需要，若要查其他下游行为 |
| 应调用的核心 Skill / 证据卡 / Data Agent 模板 | ATO feature layering；downstream branch templates |
| 期望输出结构 | 当前结论、支持证据、反证、缺失证据、下一步 |
| 必须包含的边界提醒 | 仅登录控制可支持 ATO 嫌疑；无下游不能反向排除 |
| 是否存在多意图 | 否 |
| 是否存在过拟合风险 | 中 |
| 是否适合加入 ATO 入口层回归 | 是 |

### Q11

| 字段 | 内容 |
|---|---|
| question_id | ATO_PUBLIC_Q11 |
| 用户自然语言问题 | 被盗后只点赞/关注/私信，怎么识别？ |
| 适用场景 | 下游互动滥用 |
| 预期 intent | evidence_planning |
| 预期 workflow | `dataagent_question_generation` |
| 是否需要 Data Agent | 需要生成下游行为取证问题 |
| 应调用的核心 Skill / 证据卡 / Data Agent 模板 | downstream behavior branch；ATO query template |
| 期望输出结构 | 取证目标、数据域、输出要求、质量检查 |
| 必须包含的边界提醒 | 点赞/关注/私信是下游子标签，需要先证明账号接管链路 |
| 是否存在多意图 | 是 |
| 是否存在过拟合风险 | 中 |
| 是否适合加入 ATO 入口层回归 | 是 |

### Q12

| 字段 | 内容 |
|---|---|
| question_id | ATO_PUBLIC_Q12 |
| 用户自然语言问题 | 被盗后用于爬虫/接口访问，和反爬怎么联动？ |
| 适用场景 | ATO 与反爬交叉 |
| 预期 intent | governance_design |
| 预期 workflow | `single_case_judgement → governance_design` |
| 是否需要 Data Agent | 可能需要，查接口访问和资产访问链路 |
| 应调用的核心 Skill / 证据卡 / Data Agent 模板 | `account_security_expert_skill` + `anti_crawler_expert_skill`；asset access evidence |
| 期望输出结构 | ATO 链路判断、反爬证据、协同治理 |
| 必须包含的边界提醒 | ATO 是账号控制入口，反爬是资产访问下游；不要互相替代 |
| 是否存在多意图 | 是 |
| 是否存在过拟合风险 | 中 |
| 是否适合加入 ATO 入口层回归 | 是 |

### Q13

| 字段 | 内容 |
|---|---|
| question_id | ATO_PUBLIC_Q13 |
| 用户自然语言问题 | 创作者/达人账号被盗后发链接，怎么判断影响范围？ |
| 适用场景 | 高影响账号被盗 |
| 预期 intent | single_case_judgement |
| 预期 workflow | `single_case_judgement → governance_design` |
| 是否需要 Data Agent | 需要，若要查传播、触达、粉丝影响 |
| 应调用的核心 Skill / 证据卡 / Data Agent 模板 | `account_security_expert_skill`；traffic_diversion evidence；content/link risk evidence |
| 期望输出结构 | 当前结论、影响范围、下游风险、治理方案 |
| 必须包含的边界提醒 | 高粉账号影响更大，但不能降低证据标准；链接发布不等于 ATO 充分证据 |
| 是否存在多意图 | 是 |
| 是否存在过拟合风险 | 中 |
| 是否适合加入 ATO 入口层回归 | 是 |

### Q14

| 字段 | 内容 |
|---|---|
| question_id | ATO_PUBLIC_Q14 |
| 用户自然语言问题 | 高粉账号被盗和普通账号被盗，处置是否不同？ |
| 适用场景 | 分级治理 |
| 预期 intent | governance_design |
| 预期 workflow | `governance_design` |
| 是否需要 Data Agent | 框架不需要；评估影响范围需要 |
| 应调用的核心 Skill / 证据卡 / Data Agent 模板 | `account_security_expert_skill`；governance design |
| 期望输出结构 | 短期止损、中期识别、长期治理、用户恢复、业务协同 |
| 必须包含的边界提醒 | 影响等级影响处置优先级，不改变证据标准 |
| 是否存在多意图 | 否 |
| 是否存在过拟合风险 | 低 |
| 是否适合加入 ATO 入口层回归 | 是 |

### Q15

| 字段 | 内容 |
|---|---|
| question_id | ATO_PUBLIC_Q15 |
| 用户自然语言问题 | 账号租借/共享和 ATO 怎么区分？ |
| 适用场景 | 反证 / 边界 |
| 预期 intent | single_case_judgement |
| 预期 workflow | `single_case_judgement` |
| 是否需要 Data Agent | 需要，若验证具体 case |
| 应调用的核心 Skill / 证据卡 / Data Agent 模板 | account rental counter evidence；ATO evidence boundary |
| 期望输出结构 | 当前结论、支持证据、反证、缺失证据 |
| 必须包含的边界提醒 | 账号租借/共享可能是主动交付控制权，不等同被盗 |
| 是否存在多意图 | 否 |
| 是否存在过拟合风险 | 中 |
| 是否适合加入 ATO 入口层回归 | 是 |

### Q16

| 字段 | 内容 |
|---|---|
| question_id | ATO_PUBLIC_Q16 |
| 用户自然语言问题 | 用户泄露验证码和平台责任边界怎么判断？ |
| 适用场景 | 凭证泄露责任边界 / 治理 |
| 预期 intent | governance_design |
| 预期 workflow | `single_case_judgement → governance_design` |
| 是否需要 Data Agent | 需要，若验证验证码登录和风险提示链路 |
| 应调用的核心 Skill / 证据卡 / Data Agent 模板 | sms_code_leakage_login_check；account security governance |
| 期望输出结构 | 证据判断、平台防护链路、用户教育、风险提示、恢复方案 |
| 必须包含的边界提醒 | 用户泄露验证码是风险入口，但平台仍需看是否有异常环境、提示、验证、止损能力 |
| 是否存在多意图 | 是 |
| 是否存在过拟合风险 | 低 |
| 是否适合加入 ATO 入口层回归 | 可选 |

### Q17

| 字段 | 内容 |
|---|---|
| question_id | ATO_PUBLIC_Q17 |
| 用户自然语言问题 | 怎么基于一批 ATO 样本回捞同类？ |
| 适用场景 | 回捞 |
| 预期 intent | generalization_and_recall |
| 预期 workflow | `generalization_and_recall` |
| 是否需要 Data Agent | 后续验证需要；先做特征分层不需要 |
| 应调用的核心 Skill / 证据卡 / Data Agent 模板 | feature layering；anti-overfitting rules |
| 期望输出结构 | 原始观测、数据发现、候选特征、机制特征、反例验证、回捞优先级 |
| 必须包含的边界提醒 | case 回扫生成假设，不直接生成线上策略 |
| 是否存在多意图 | 否 |
| 是否存在过拟合风险 | 高 |
| 是否适合加入 ATO 入口层回归 | 是 |

### Q18

| 字段 | 内容 |
|---|---|
| question_id | ATO_PUBLIC_Q18 |
| 用户自然语言问题 | 哪些特征只能作为候选，不能直接上线？ |
| 适用场景 | 防过拟合 / 特征分层 |
| 预期 intent | generalization_and_recall |
| 预期 workflow | `generalization_and_recall → review_and_skill_distillation` |
| 是否需要 Data Agent | 不需要，除非要补验证 |
| 应调用的核心 Skill / 证据卡 / Data Agent 模板 | ATO feature layering and evidence boundary |
| 期望输出结构 | 原始观测、数据发现、候选特征、机制特征、本质规则、不能上线原因 |
| 必须包含的边界提醒 | 具体策略名、样本比例、时间窗、发布平台、表象特征不能直接上线 |
| 是否存在多意图 | 是 |
| 是否存在过拟合风险 | 高 |
| 是否适合加入 ATO 入口层回归 | 是 |

### Q19

| 字段 | 内容 |
|---|---|
| question_id | ATO_PUBLIC_Q19 |
| 用户自然语言问题 | ATO 治理是验证、踢 token、封禁还是用户教育？ |
| 适用场景 | 治理方案 |
| 预期 intent | governance_design |
| 预期 workflow | `governance_design` |
| 是否需要 Data Agent | 不需要，除非要评估规模和效果 |
| 应调用的核心 Skill / 证据卡 / Data Agent 模板 | risk_governance_design_skill；account_security_expert_skill |
| 期望输出结构 | 短期止损、中期识别、长期治理、用户体验、黑产成本、业务协同 |
| 必须包含的边界提醒 | 高风险治理动作不得自动执行，必须人工确认 |
| 是否存在多意图 | 否 |
| 是否存在过拟合风险 | 低 |
| 是否适合加入 ATO 入口层回归 | 是 |

### Q20

| 字段 | 内容 |
|---|---|
| question_id | ATO_PUBLIC_Q20 |
| 用户自然语言问题 | 这批 case 能沉淀哪些 Skill，哪些只留 eval？ |
| 适用场景 | 复盘沉淀 |
| 预期 intent | review_and_skill_distillation |
| 预期 workflow | `review_and_skill_distillation` |
| 是否需要 Data Agent | 不需要，除非要求补更多样本 |
| 应调用的核心 Skill / 证据卡 / Data Agent 模板 | scenario workflow contract；ATO feature layering |
| 期望输出结构 | 可回写 Skill、只进 eval/review、需更多数据验证、不应沉淀 |
| 必须包含的边界提醒 | principle_rule 才能回写；样本统计/具体策略名/具体时间窗只进 eval |
| 是否存在多意图 | 否 |
| 是否存在过拟合风险 | 高 |
| 是否适合加入 ATO 入口层回归 | 是 |

### Q21

| 字段 | 内容 |
|---|---|
| question_id | ATO_PUBLIC_Q21 |
| 用户自然语言问题 | 用户说账号被盗后头像昵称都变了，但没有看到发布，这种怎么判断？ |
| 适用场景 | 资料变更型下游行为 |
| 预期 intent | single_case_judgement |
| 预期 workflow | `single_case_judgement → dataagent_question_generation` |
| 是否需要 Data Agent | 需要验证资料变更、登录环境、token/session |
| 应调用的核心 Skill / 证据卡 / Data Agent 模板 | account profile change evidence；ATO query template |
| 期望输出结构 | 当前结论、支持证据、反证、缺失证据、Data Agent 问题 |
| 必须包含的边界提醒 | 无发布不是反证；资料变更也只是下游动作，需证明账号接管 |
| 是否存在多意图 | 是 |
| 是否存在过拟合风险 | 中 |
| 是否适合加入 ATO 入口层回归 | 是 |

### Q22

| 字段 | 内容 |
|---|---|
| question_id | ATO_PUBLIC_Q22 |
| 用户自然语言问题 | 账号被盗后粉丝收到诈骗私信，这应该走盗号还是导流/欺诈？ |
| 适用场景 | ATO 与导流/欺诈交叉 |
| 预期 intent | single_case_judgement |
| 预期 workflow | `single_case_judgement → governance_design` |
| 是否需要 Data Agent | 需要，若验证私信触达和账号接管链路 |
| 应调用的核心 Skill / 证据卡 / Data Agent 模板 | `account_security_expert_skill` + `traffic_diversion_interception_skill` |
| 期望输出结构 | ATO 入口判断、私信导流/欺诈链路、治理协同 |
| 必须包含的边界提醒 | 盗号是入口，私信诈骗是下游作恶；两者需分层治理 |
| 是否存在多意图 | 是 |
| 是否存在过拟合风险 | 中 |
| 是否适合加入 ATO 入口层回归 | 是 |

### Q23

| 字段 | 内容 |
|---|---|
| question_id | ATO_PUBLIC_Q23 |
| 用户自然语言问题 | 用户说异地登录，但数据里没有登录记录，是不是就能判不是被盗？ |
| 适用场景 | empty / no log 边界 |
| 预期 intent | dataagent_result_interpretation |
| 预期 workflow | `dataagent_result_interpretation` |
| 是否需要 Data Agent | 不需要；已有数据发现，下一步可能需补实时日志 |
| 应调用的核心 Skill / 证据卡 / Data Agent 模板 | data freshness and quality rules；ATO evidence boundary |
| 期望输出结构 | 数据发现、反证、缺失证据、质量风险、下一步 |
| 必须包含的边界提醒 | 无登录记录不能解释为无风险，也不能支持 ATO；可能是窗口、权限或日志覆盖问题 |
| 是否存在多意图 | 否 |
| 是否存在过拟合风险 | 中 |
| 是否适合加入 ATO 入口层回归 | 是 |

### Q24

| 字段 | 内容 |
|---|---|
| question_id | ATO_PUBLIC_Q24 |
| 用户自然语言问题 | ATO case 里哪些应该先进人工复核，哪些可以先监控？ |
| 适用场景 | 处置分层 |
| 预期 intent | governance_design |
| 预期 workflow | `governance_design` |
| 是否需要 Data Agent | 不需要，若已有证据等级；需要评估规模时再查 |
| 应调用的核心 Skill / 证据卡 / Data Agent 模板 | governance design；ATO conclusion thresholds |
| 期望输出结构 | 人工复核条件、监控条件、补证条件、用户体验控制 |
| 必须包含的边界提醒 | 高风险处置必须人工确认；监控不等于放过 |
| 是否存在多意图 | 否 |
| 是否存在过拟合风险 | 低 |
| 是否适合加入 ATO 入口层回归 | 可选 |

### Q25

| 字段 | 内容 |
|---|---|
| question_id | ATO_PUBLIC_Q25 |
| 用户自然语言问题 | 如果盗号后没有马上作恶，只是养号或等几天再用，怎么验证？ |
| 适用场景 | 延迟下游作恶 / 养号 |
| 预期 intent | evidence_planning |
| 预期 workflow | `dataagent_question_generation` |
| 是否需要 Data Agent | 需要生成分支取证问题 |
| 应调用的核心 Skill / 证据卡 / Data Agent 模板 | downstream behavior branch；account lifecycle evidence |
| 期望输出结构 | 取证计划、时间窗口建议、行为分支、降级规则 |
| 必须包含的边界提醒 | 长窗口无明显作恶也不能直接反向排除 ATO；需要看账号控制权和后续生命周期 |
| 是否存在多意图 | 是 |
| 是否存在过拟合风险 | 中 |
| 是否适合加入 ATO 入口层回归 | 是 |

## 4. 按 Workflow 归类

| workflow | question_id |
|---|---|
| single_case_judgement | Q01, Q03, Q04, Q07, Q10, Q15, Q21 |
| batch_case_clustering | Q05, Q06 |
| dataagent_question_generation | Q02, Q11, Q13, Q16, Q21, Q25 |
| dataagent_result_interpretation | Q08, Q09, Q23 |
| generalization_and_recall | Q17, Q18 |
| governance_design | Q12, Q14, Q16, Q19, Q22, Q24 |
| review_and_skill_distillation | Q06, Q18, Q20 |

多意图执行顺序：

- Q02：`single_case_judgement → dataagent_question_generation`
- Q06：`batch_case_clustering → review_and_skill_distillation`
- Q12：`single_case_judgement → governance_design`
- Q13：`single_case_judgement → governance_design`
- Q16：`single_case_judgement → governance_design`
- Q18：`generalization_and_recall → review_and_skill_distillation`
- Q21：`single_case_judgement → dataagent_question_generation`
- Q22：`single_case_judgement → governance_design`
- Q25：`evidence_planning → dataagent_question_generation`

## 5. 边界规则检查

| 边界规则 | 覆盖问题 |
|---|---|
| 用户申诉 / 人工备注只能作为线索，不能直接作为事实 | Q02, Q06, Q07, Q16 |
| Data Agent 是 evidence provider，不是 final decision maker | Q08, Q09, Q11, Q16 |
| Data Agent 的结论性文字只能进入 provider_conclusion_hint | Q08, Q09 |
| dennis_final_judgement 由 Dennis 主 Agent 生成 | Q08, Q09, Q20 |
| SQL-only 不能进入强/中/弱证据链 | Q08 |
| no_permission / partial 必须降级 | Q09 |
| ATO 发生方式与 ATO 后下游作恶方式必须分离 | Q01, Q03, Q04, Q10, Q11, Q12, Q21, Q22 |
| 发布异常内容不是 ATO 成立必要条件 | Q01, Q03, Q04 |
| 无发布不能反向排除 ATO | Q03, Q10, Q21, Q23, Q25 |
| 具体策略名 / 样本比例 / 时间窗不能作为长期本质特征 | Q17, Q18, Q20 |
| 高风险治理动作不得自动执行，必须人工确认 | Q14, Q19, Q24 |

覆盖结论：完整。

## 6. 和 ato_real_user_question_trial_v1.md 的关系

### 6.1 与现有 18 个真实问法重合

重合较高：
- Q01 与 Trial 01 / Trial 15。
- Q03 与 Trial 04。
- Q05 与 Trial 03。
- Q07 与 Trial 02 / Trial 10。
- Q08 与 Trial 17。
- Q12 与 Trial 18 的跨场景迁移方向相近，但更聚焦反爬联动。
- Q17 与 Trial 08。
- Q19 与 Trial 09。
- Q20 与 Trial 10。

### 6.2 新增公开行业启发问题

新增价值较高：
- Q11：盗号后点赞 / 关注 / 私信滥用。
- Q12：盗号后爬虫 / 接口访问，与反爬联动。
- Q13：创作者 / 达人 / 高粉账号被盗影响范围。
- Q14：高粉账号与普通账号处置差异。
- Q16：用户泄露验证码与平台责任边界。
- Q21：资料变更但无发布。
- Q22：盗号后粉丝收到诈骗私信，ATO 与导流/欺诈交叉。
- Q23：用户称异地登录但数据无登录记录。
- Q24：人工复核 vs 监控分层。
- Q25：盗号后延迟作恶 / 养号。

### 6.3 适合补充到下一轮 ATO entrypoint usability regression

建议加入：
- Q11
- Q12
- Q13
- Q15
- Q16
- Q21
- Q22
- Q23
- Q25

原因：
- 这些覆盖现有 Trial v1 较少涉及的公开行业问题。
- 能验证跨 Skill 路由、下游作恶分层、内容平台高影响账号和延迟作恶边界。

### 6.4 只适合作为扩展参考

暂不建议进入核心回归：
- Q14：偏治理分级，场景重要但不一定高频。
- Q24：偏内部处置流程，需要结合组织流程。

## 7. 总结

### 7.1 新增问法覆盖

本轮新增 25 个公开行业启发问法，重点补足：

- 内容平台高影响账号。
- 互动滥用。
- 接口访问 / 反爬联动。
- 账号租借 / 共享边界。
- 用户泄露验证码的责任边界。
- 下游延迟作恶 / 养号。
- 无登录记录 / empty-like 边界。
- 人工复核 vs 监控分层。

### 7.2 Workflow 覆盖不足

当前 workflow 覆盖基本充分。

轻微不足：
- `evidence_planning` 在 ATO overlay 中还不是显式 workflow，部分问题通过 `dataagent_question_generation` 承接。
- 跨 Skill 场景，例如反爬、导流、内容治理，需要后续在通用 scenario contract 中补更多 overlay 示例。

### 7.3 是否建议修改 ATO entrypoint / workflow / response contract

暂不建议立即修改。

建议：
- 将 Q11 / Q12 / Q13 / Q15 / Q16 / Q21 / Q22 / Q23 / Q25 加入下一轮 usability regression。
- 若真实试问中频繁出现，再补 ATO overlay 的 trigger examples。

### 7.4 是否建议修改通用 scenario contract

暂不建议修改。

现有通用 contract 能承接这些问法。

### 7.5 是否修改核心 Skill

未修改核心 Skill。

### 7.6 是否调用 Data Agent

未调用 Data Agent。

### 7.7 下一步建议

P0：
- 把新增高价值问法纳入下一轮 ATO entrypoint regression。
- 重点测试跨 Skill：ATO × 反爬、ATO × 导流、ATO × 内容治理。

P1：
- 根据真实盗号同学试问日志，统计最常见问法和误路由点。
- 决定是否在 ATO router 中补 trigger examples。

P2：
- 等 ATO entrypoint 试运行稳定后，再复用通用 scenario contract 做 anti_crawler / group_control overlay。
