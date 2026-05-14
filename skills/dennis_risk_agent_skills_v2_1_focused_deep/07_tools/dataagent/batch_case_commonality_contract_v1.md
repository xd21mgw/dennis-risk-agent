# Batch Case Commonality Contract v1

## 0. 目标

本文件定义 Dennis 风控 Agent 对“一批 case 找共性”的输入、输出和 Data Agent 查询意图契约。

适用目标：

- 判断一批 case 是否同源、同团伙、同链路、同机制或只是表象相似。
- 将个案证据升级为批量共性证据。
- 避免因高频、聚集、低质、缺日志等表象把不同问题过拟合成同一类攻击。
- 为后续 Data Agent 接入提供批量查询意图。

当前 Codex 阶段不调用真实 Data Agent，只生成批量 `query_intent`、共性分析框架、解释规则和治理建议。

## 1. 适用场景

适用于以下批量问题：

- 多个协议疑似 case 是否来自同一脚本或接口模板。
- 多个群控/真机异常是否属于同一设备团组。
- 多个账号安全 case 是否复用同一 token、IP、设备或撞库资源。
- 多个活动作弊 case 是否复用奖励、提现、任务平台或教程话术。
- 多个渠道异常是否来自同一归因劫持链路。
- 多个导流截流 case 是否复用同一目标获取入口、触达账号矩阵或站外承接。
- 多个低质/DAU/DNU 异常是否由同一口径、实验、活动或版本导致。

## 2. 批量 case 标准输入

```yaml
batch_case_input:
  batch_id: "<批次ID>"
  business_scene: "<业务场景>"
  suspected_risks:
    - "<协议 | 群控 | token泄露 | 活动黑产 | 导流截流 | 渠道抢量 | 低质 | 混合攻击>"
  decision_needed:
    - "<是否同源>"
    - "<是否同链路>"
    - "<是否需要统一治理>"
  time_window:
    baseline: "<历史对照窗口；未知写待补充>"
    observation: "<异常观测窗口；未知写待补充>"
  cases:
    - case_id: "<case id>"
      business_context: "<单 case 业务背景>"
      known_objects:
        users: []
        accounts: []
        devices: []
        ips: []
        tokens: []
        packages: []
        channels: []
        campaigns: []
        live_rooms: []
        benefit_subjects: []
      observed_signals:
        - "<已知异常信号>"
      current_evidence:
        - "<已有证据>"
      current_action: "<已采取动作；未知写无>"
      business_impact: "<业务影响；未知写待补充>"
  exclusions_to_check:
    - "<合法矩阵>"
    - "<业务活动>"
    - "<版本发布>"
    - "<实验流量>"
    - "<数据口径变化>"
```

## 3. 批量共性 query_intent 标准格式

```yaml
query_intent:
  intent_id: "<batch_id + commonality_type + 序号>"
  risk_question: "<这批 case 要回答的共性风险问题>"
  target_evidence: "<资源共性 | 行为共性 | 链路共性 | 收益共性 | 入口共性 | 后验共性 | 业务共性>"
  commonality_goal:
    classify_as: "<同源同链路 | 同源不同链路 | 不同源同机制 | 表象相似 | 证据不足>"
    compare_level: "<case级 | 对象级 | 团组级 | 链路级 | 收益主体级>"
  applicable_skill:
    primary: "evidence_decomposition_skill"
    auxiliary:
      - "risk_chain_reconstruction_skill"
      - "attack_type_classification_skill"
      - "<按场景补充领域或攻击 Skill>"
  minimum_inputs:
    required:
      - "case_id 列表"
      - "观测时间窗口"
      - "至少一种对象集合或异常信号"
    optional:
      - "历史处置结果"
      - "后验质量"
      - "业务活动/实验/版本变更"
    missing:
      - "<缺失信息>"
  query_dimensions:
    entities:
      - "case"
      - "账号"
      - "设备"
      - "IP"
      - "UA"
      - "token"
      - "客户端包"
      - "渠道"
      - "活动"
      - "直播间"
      - "收益主体"
    group_by:
      - "资源复用"
      - "路径相似"
      - "时间同步"
      - "收益聚集"
      - "入口来源"
      - "后验质量"
      - "授权主体"
    joins:
      - "case样本"
      - "行为日志"
      - "设备环境"
      - "登录态"
      - "奖励/提现/结算"
      - "前后端链路"
      - "授权矩阵"
  time_window:
    baseline: "<历史对照窗口>"
    observation: "<异常窗口>"
    granularity: "<分钟 | 小时 | 天>"
  expected_outputs:
    - "case 聚类摘要"
    - "共性维度贡献"
    - "同源/同链路置信提示"
    - "反证分布"
    - "治理合并建议"
  interpretation_notes:
    strong_evidence_if:
      - "多个 case 复用同一关键资源、链路或收益主体，且业务反证已排除"
    weak_signal_if:
      - "只有同一时间、同一活动或同一高频表象"
    counter_evidence_if:
      - "同一业务活动、版本、实验、合法矩阵或口径变化可解释"
  conclusion_threshold:
    sufficient_for: "<明确判断 | 高度疑似 | 证据不足 | 反向排除>"
    must_combine_with:
      - "<必须组合的共性证据>"
  safety_boundary:
    false_positive_risks:
      - "业务机制导致相似"
      - "合法运营矩阵"
      - "自然热点"
      - "实验/版本/口径变化"
    prohibited_actions:
      - "不得仅凭表象相似做统一处罚"
```

## 4. 标准输出

```text
一句话判断：
批次结论类型：同源同链路 / 同源不同链路 / 不同源同机制 / 表象相似 / 证据不足
主控 Skill：
辅助 Skill：
最大共性：
强共性证据：
中共性证据：
弱共性证据：
反证与误判：
分群结果：
统一治理建议：
不应统一治理的部分：
下一步 query_intent：
是否需要人工确认：
可沉淀资产：
```

## 5. 禁止行为

- 禁止只因为多个 case 高频、聚集、低质、缺日志就判断同源。
- 禁止把业务机制导致的相似误判为攻击团伙。
- 禁止跳过合法矩阵、活动排期、实验流量、版本发布、口径变化等反证。
- 禁止在当前 Codex 阶段声称已真实查数或调用 Data Agent。
- 禁止编造真实表名、字段名、API、接口路径或真实结果。
- 禁止把批量聚类结果直接转成处罚、冻结、扣款、全量封禁。
