# Data Agent 工具契约 v1

## 0. 定位

本文件定义 Dennis 风控 Agent 与未来 Data Agent 的工具抽象层契约。目标不是在当前 Codex 环境真实调用 Data Agent，而是标准化三件事：

1. 风控证据应该怎么问 Data Agent。
2. Data Agent 返回后 Dennis 风控 Agent 怎么解释。
3. 数据结果够不够支持风险结论。

## 1. 当前 Codex 阶段不真实调用

当前 Codex 阶段：

- 不调用 Data Agent。
- 不编造 Data Agent API、认证、接口路径、请求参数或返回结构。
- 不编造真实表名、字段名、分区、看板内容、AB 结果或画像标签。
- 只输出 `query_intent`、查询模板、解释规则、结论阈值和补证建议。
- 所有数据能力输出都必须标注为“待 Data Agent / 人工平台执行”。

## 2. 未来内部平台阶段如何调用

未来内部平台阶段可按以下抽象流程接入：

1. Dennis 风控 Agent 识别风险问题、主控 Skill、辅助 Skill 和证据缺口。
2. Dennis 风控 Agent 生成标准 `query_intent`。
3. 人工平台或编排层将 `query_intent` 转换为真实 Data Agent 调用。
4. Data Agent 执行找表、SQL、看板、AB、画像或圈选任务。
5. Data Agent 返回结构化结果。
6. Dennis 风控 Agent 解释结果，输出结论等级、证据强度、反证、补证和治理建议。
7. 若证据不足，Dennis 风控 Agent 继续生成下一轮 `query_intent`。

## 3. 职责边界

| 角色 | 负责 | 不负责 |
|---|---|---|
| Dennis 风控 Agent | 风险理解、Skill 路由、证据需求、query_intent 生成、结果解释、结论等级、治理建议 | 真实取数、真实 SQL 执行、内部权限申请 |
| Data Agent | 找表、SQL、看板分析、AB 实验分析、画像标签、人群圈选、数据结果返回 | 风控最终定性、处罚、冻结、扣除、策略上线 |
| 人工平台 / 编排层 | 权限控制、真实调用、审计、结果传递、失败重试 | 替代 Dennis 风控 Agent 做风险判断 |

原则：

- Data Agent 只回答“怎么查、查到了什么、数据怎么看”。
- Dennis 风控 Agent 才回答“这说明什么风险、证据强弱如何、能不能治理”。
- 数据结果必须经过反证、误伤、业务边界校验，不能直接转成处罚动作。

## 4. 标准 query_intent 格式

```yaml
query_intent:
  intent_id: "<稳定唯一标识；例如 risk_case_id + evidence_type + 序号>"
  risk_question: "<用户真实要回答的风险问题>"
  target_evidence: "<要补齐的证据类型，例如前后端链路一致性、token/device/ip/ua 一致性>"
  applicable_skill:
    primary: "<主控 Skill>"
    auxiliary:
      - "<辅助 Skill>"
  minimum_inputs:
    required:
      - "<执行查询所需的最小输入，例如时间范围、对象ID、场景、事件口径>"
    optional:
      - "<有助于提升解释质量的输入>"
    missing:
      - "<当前缺失但必须由用户或平台补齐的信息>"
  query_dimensions:
    entities:
      - "<用户 / 账号 / 设备 / IP / token / 包 / 直播间 / 商品 / 实验组等实体类型>"
    group_by:
      - "<需要聚合或下钻的维度；只写语义，不写真实字段名>"
    joins:
      - "<需要关联的日志或资产类型；不写真实表名>"
  time_window:
    baseline: "<历史基线窗口；未知写待补充>"
    observation: "<观测窗口；未知写待补充>"
    granularity: "<分钟 / 小时 / 天 / 周等>"
  expected_outputs:
    - "<期望返回的指标、分布、样本、趋势、分群、SQL 模板或看板解释>"
  interpretation_notes:
    strong_evidence_if:
      - "<什么结果可解释为强证据>"
    weak_signal_if:
      - "<什么结果只能解释为弱信号>"
    counter_evidence_if:
      - "<什么结果构成反证>"
  conclusion_threshold:
    sufficient_for: "<明确判断 / 高度疑似 / 证据不足 / 反向排除>"
    must_combine_with:
      - "<必须组合的其他证据>"
  safety_boundary:
    false_positive_risks:
      - "<误伤来源，例如合法运营、埋点缺失、自然热点、实验流量>"
    prohibited_actions:
      - "<当前结果不得直接触发的动作>"
```

## 5. query_intent 生成规则

1. 先写风险问题，再写数据问题，避免把取数目标反客为主。
2. 证据类型必须明确，例如“前后端链路一致性”，不能只写“查异常”。
3. 最小输入必须显式列出，缺失项不得假设。
4. 查询维度只写语义粒度，不写真实表名和字段名。
5. 期望输出必须服务于结论阈值，例如强证据、反证、灰度指标或治理评估。
6. 每个 `query_intent` 必须包含安全边界，防止单指标强结论。

## 6. 禁止行为

1. 禁止在当前 Codex 阶段声称已经调用 Data Agent。
2. 禁止编造 Data Agent API、认证、接口路径、请求参数、返回字段。
3. 禁止编造真实表名、字段名、分区、血缘、看板、实验结果、画像标签。
4. 禁止把 Data Agent 返回直接作为风控最终定性。
5. 禁止让 Data Agent 直接执行处罚、冻结、扣除、封禁、策略上线。
6. 禁止用单一指标异常直接下协议、群控、黑产、盗号、作弊强结论。
7. 禁止跳过反证：合法矩阵、埋点缺失、口径差异、权限缺失、样本偏差、业务活动、实验流量。
