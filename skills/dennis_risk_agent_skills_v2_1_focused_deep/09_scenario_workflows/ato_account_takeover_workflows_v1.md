# ATO Account Takeover Workflows v1

## 0. 定位

本文件定义 ATO / 账号接管场景的 Agent 调度工作流，供 Dennis Risk Agent 自动选择流程使用。

边界：
- ATO 是 v2.4 第一优先落地场景，不改变 Dennis Risk Agent 的通用业务风控专家定位。
- Dennis Risk Agent 仍覆盖账号安全、反爬、活动反作弊、流量反作弊、协议、群控、破解包、导流等多个方向。
- 本文件沉淀的是“场景落地样板”：风险专家大脑 + 证据卡 / 查数卡 + Data Agent 手脚 + 结果解释 + 举一反三 + 回捞建议 + 治理建议 + 回归沉淀。
- 不调用真实 Data Agent。
- 不包含真实表名、字段名、SQL 或 API。

通用链路：

```text
用户自然语言问题
→ ATO intent router
→ scenario workflow
→ account_security_expert_skill + evidence boundary
→ Data Agent question / result parser，如需要
→ Dennis final judgement
→ next action / governance / regression
```

## 1. single_case_judgement

### 适用

用户问：
- 这个用户是不是被盗？
- 这个客诉是否可信？
- 这个账号异常行为是否是 ATO？
- 用户说扫码 / 钓鱼 / 验证码泄露后被封，怎么看？

### 输入

```yaml
input:
  user_id_or_case_id:
  user_claim_summary:
  suspicious_event_time:
  abnormal_behavior:
  manual_note:
  existing_dataagent_response: optional
  existing_manual_review: optional
```

### 调度步骤

1. 识别 ATO 发生方式候选：
   - Web 扫码 / 异步登录 / 授权登录。
   - 钓鱼 / 验证码泄露。
   - token/session 泄露。
   - 账号租借 / 交易。
   - 非盗号 / 历史 / 不确定。
2. 识别 ATO 后下游作恶方式候选：
   - 发布内容。
   - 点赞 / 关注 / 评论 / 私信。
   - 接口访问 / 资产窃取。
   - 活动套利。
   - 导流截流。
   - 养号 / 转生。
   - 仅登录控制，尚未观测到明显作恶。
3. 拆分证据：
   - 用户自述。
   - 人工备注。
   - 数据发现。
   - provider_conclusion_hint。
4. 判断是否需要 Data Agent：
   - 缺登录 / 授权 / token / 设备 / 发布 / 策略证据时，需要。
   - 已有 Data Agent 返回时，进入 result interpretation。
5. 输出 Dennis final judgement。

### 输出

```yaml
output:
  dennis_final_judgement:
  reason:
  support_evidence:
  counter_evidence:
  missing_evidence:
  next_evidence_to_collect:
  dataagent_needed:
  manual_review_required:
```

### 关键边界

- 用户申诉不是事实。
- 人工备注不是事实。
- Data Agent 返回不是最终判断。
- 无发布不能反向排除 ATO。
- 发布异常内容不是 ATO 成立必要条件。

## 2. batch_case_clustering

### 适用

用户问：
- 这批盗号样本帮我分层。
- 哪些是扫码，哪些是钓鱼，哪些是 token，哪些是不确定？
- Sheet2 这批样本怎么拆？

### 输入

```yaml
input:
  case_list:
  source_sheet_or_batch_id:
  user_claim_summary_list:
  manual_labels:
  manual_notes:
  optional_data_findings:
```

### 调度步骤

1. 先按 ATO 发生方式分层。
2. 再按 ATO 后下游作恶方式分层。
3. 区分：
   - 高置信正例。
   - 反例。
   - 不确定样本。
   - 历史 case。
   - 标签缺失样本。
   - 待补证样本。
4. 把单批统计保留在 review / eval，不直接写入 Skill。

### 输出

```yaml
output:
  ato_method_layers:
  downstream_abuse_layers:
  high_confidence_positive_cases:
  counterexample_cases:
  uncertain_cases:
  historical_cases:
  missing_label_cases:
  evidence_pending_cases:
  sample_statistics_not_for_skill:
```

### 关键边界

- 样本比例不是长期规则。
- 具体策略名不是本质特征。
- 单批正例不能替代反例验证。

## 3. dataagent_question_generation

### 适用

用户问：
- 帮我生成 Data Agent 查询问题。
- 帮我查这批样本有没有共性。
- 这批样本要怎么取证？
- 单 case 该怎么问 Data Agent？

### 输入

```yaml
input:
  risk_question:
  case_scope:
  minimum_inputs:
    - case_id
    - user_id_or_entity_id
    - time_window
    - business_scene
    - target_action
  evidence_goal:
  known_boundaries:
```

### 调度步骤

1. 校验最小输入。
2. 选择 query template：
   - Web 扫码 / 异步登录。
   - 钓鱼 / web 短信验证码。
   - token/session。
   - 非盗号 / 误报复盘。
3. 编码只读取证问题。
4. 明确 Data Agent provider boundary。
5. 明确 Data Agent 不做最终定性。

### 输出

```yaml
output:
  dataagent_question:
  required_data_domains:
  field_types_needed:
  join_paths_needed:
  expected_outputs:
  quality_checks:
  provider_boundary:
  degrade_rules:
```

### 关键边界

- 不生成真实 SQL。
- 不写真表名 / 真字段。
- Data Agent 不输出处罚、冻结、封禁、扣除或策略上线建议。

## 4. dataagent_result_interpretation

### 适用

用户问：
- 这是 Data Agent 返回，帮我解释。
- 这些数据够不够判断盗号？
- 哪些是数据发现，哪些只是 provider hint？

### 输入

```yaml
input:
  dataagent_response:
  query_intent_or_question:
  case_scope:
  expected_evidence:
```

### 调度步骤

1. 识别状态：
   - success。
   - sql_only / pending_execution。
   - partial。
   - no_permission。
   - empty_result。
   - failed / timeout。
2. 抽取：
   - data_findings。
   - provider_conclusion_hint。
   - evidence。
   - counter_evidence。
   - missing_evidence。
   - quality_risks。
3. 生成 Dennis final judgement。
4. 生成 next action。

### 输出

```yaml
output:
  data_findings:
  provider_conclusion_hint:
  strong_evidence:
  medium_evidence:
  weak_evidence:
  counter_evidence:
  missing_evidence:
  quality_risks:
  provider_limitations:
  dennis_final_judgement:
  recommended_next_provider:
  next_action:
```

### 关键边界

- SQL-only 不是证据。
- no_permission 必须降级。
- empty_result 不等于无风险。
- provider_conclusion_hint 不等于 Dennis final judgement。

## 5. generalization_and_recall

### 适用

用户问：
- 怎么举一反三？
- 怎么回捞同类盗号？
- 哪些特征能用？
- 哪些特征不要用？

### 输入

```yaml
input:
  case_findings:
  batch_findings:
  existing_labels:
  known_counterexamples:
```

### 调度步骤

1. 做特征分层：
   - raw_observation。
   - data_finding。
   - candidate_feature。
   - mechanism_feature。
   - principle_rule。
2. 标注哪些可回捞、哪些只进 eval。
3. 设计正反例验证。
4. 评估误伤风险和业务边界。

### 输出

```yaml
output:
  raw_observations:
  data_findings:
  candidate_features:
  mechanism_features:
  principle_rules:
  positive_negative_validation_plan:
  false_positive_risks:
  recall_priority:
```

### 关键边界

- 具体策略名只在 raw_observation。
- 单批样本统计只留 review / eval。
- 下游作恶表象不能作为 ATO 成立必要条件。

## 6. governance_design

### 适用

用户问：
- 这类盗号怎么治理？
- 该验证、踢 token、封禁，还是用户教育？
- 怎么降低误伤？

### 输入

```yaml
input:
  ato_method:
  downstream_abuse_type:
  evidence_strength:
  user_impact:
  business_constraints:
```

### 调度步骤

1. 拆治理阶段：
   - 登录前预防。
   - 登录中验证。
   - 登录后止损。
   - token/session 处置。
   - 下游作恶拦截。
   - 号主恢复。
   - 用户教育。
2. 分轻重处置：
   - 监控。
   - 二次验证。
   - 风险提醒。
   - token 柔性踢出。
   - 敏感动作限权。
   - 人工复核。
3. 输出误伤和体验控制。

### 输出

```yaml
output:
  pre_login_prevention:
  in_login_verification:
  post_login_loss_control:
  token_session_action:
  downstream_abuse_interception:
  owner_recovery:
  user_education:
  black_industry_cost_increase:
  false_positive_and_experience_control:
  business_collaboration:
```

### 关键边界

- 治理建议不等于自动上线。
- 高风险处置必须人工确认。
- 不因用户申诉直接解封或处罚。

## 7. review_and_skill_distillation

### 适用

用户问：
- 这批 case 能沉淀什么？
- 要不要回写 Skill？
- 哪些只留在 eval？
- 下一轮回归怎么做？

### 输入

```yaml
input:
  case_reviews:
  batch_reviews:
  dataagent_findings:
  regression_results:
```

### 调度步骤

1. 按特征层级归档。
2. 判断是否满足回写条件。
3. 区分：
   - 可沉淀本质规则。
   - 机制特征。
   - 候选特征。
   - 表象特征。
   - 样本统计。
4. 生成 eval / regression 更新建议。

### 输出

```yaml
output:
  principle_rules_for_skill_candidate:
  mechanism_features:
  candidate_features:
  surface_features:
  sample_statistics_for_eval_only:
  writeback_recommendation:
  new_regression_cases:
  more_dataagent_validation_needed:
```

### 关键边界

- ATO workflow 是场景落地样板，不是把 Agent 改造成盗号专用 Agent。
- 可复用到反爬、活动、流量、导流、协议、群控等其他场景。
