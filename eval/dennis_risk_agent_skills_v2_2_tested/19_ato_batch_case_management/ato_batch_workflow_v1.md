# ATO Batch Workflow v1

## 1. 定位

本流程用于 5-20 个 ATO / 盗号申诉 case 的半自动批量归因。目标是把分散 case 标准化成证据卡、模式摘要、缺口清单和候选策略方向。

边界：

- 不调用真实 DataAgent。
- 不访问真实内部平台。
- 不执行真实 SQL / API / browser 查询。
- 不做自动策略上线。
- 不做自动处罚、封禁、解封或权益影响动作。
- DataAgent 仅在未来需要 Hive / 数仓取数分析且场景允许时作为补证来源，不是默认万能数据底座。

## 2. 流程总览

| 阶段 | 输入 | 输出 | 关键检查 |
|---|---|---|---|
| case intake | CSV / 人工整理 case | 标准 case registry | 不含真实敏感明文，字段满足最小闭环 |
| entity parse | user_id / device_id / event_time / abnormal_action | 实体和时间窗口摘要 | 缺实体时标记 missing evidence，不伪造 |
| single case evidence card generation | 单 case 标准字段 | 单 case 证据卡 | 区分强/中/弱/反证/缺口 |
| cross-case pattern aggregation | 5-20 个 evidence card | 批量模式摘要 | 聚合只输出候选模式，不直接定性团伙 |
| missing evidence summary | 所有 case 缺口 | 批量补证清单 | 标注在线窗口、权限、数据缺口 |
| strategy direction draft | 模式摘要 + 缺口 | 候选策略方向 | 必须包含误伤风险、AB 和查杀分离建议 |
| manual review boundary | 证据卡和策略方向 | 人工复核任务 | 人工确认前不得上线或处置 |

## 3. Case Intake

接入时只要求最小字段：

- case_id
- user_id
- device_id 可为空
- event_time
- abnormal_action
- user_claim / available_evidence / notes 至少一个
- current_status

导入检查：

- 不接受 cookie、token、手机号、完整 IP、完整 device fingerprint 等敏感明文。
- 不把用户申诉当事实。
- 不把 manual_label 当最终结论。
- 不把缺失字段自动补成默认值。

## 4. Entity Parse

解析目标：

- 提取 user_id、device_id、event_time、abnormal_action。
- 标记缺失实体，如 missing_device_id、missing_event_time。
- 根据 event_time 判断是否存在 login_log_window_incomplete 风险。

输出：

- entity_summary
- time_window_summary
- missing_required_entity
- freshness_risk

## 5. Single Case Evidence Card Generation

每个 case 生成一张证据卡，使用 `ato_batch_evidence_card_template_v1.md`。

证据卡必须包含：

- strong evidence
- medium evidence
- weak evidence
- counter evidence
- missing evidence
- freshness risk
- permission / data gap
- conclusion support level

结论支持等级只能是证据支持程度，不是最终事实定性。

## 6. Cross-case Pattern Aggregation

聚合维度：

- common entity pattern
- common device / IP / login pattern
- common behavior path
- shared missing evidence
- suspected attack path
- case clustering result
- confidence level

聚合边界：

- 关联设备 / 关联用户只代表候选实体关系。
- 多 case 同模式只能说明“值得进一步补证的模式”，不等于团伙已确认。
- 不能用少量样本直接推出全量策略。

## 7. Missing Evidence Summary

常见缺口：

- 发布审计日志缺失。
- token / refreshToken / passToken 使用链路缺失。
- OAuth / 第三方授权记录缺失。
- 统一登录日志在线窗口超出，需 offline Hive。
- 设备指纹 / 风险标签缺失。
- 审核 / 封禁工单缺失。
- 权限阻断或 API failed。

缺口输出应优先服务下一步补证，而不是用 no_data 反向定性。

## 8. Strategy Direction Draft

策略方向只输出候选建议：

- 候选风险路径。
- 候选识别特征。
- 候选补证字段。
- 误伤风险。
- AB / 查杀分离评估建议。
- 人工复核边界。

禁止：

- 直接给自动上线结论。
- 直接建议处罚或封禁。
- 将候选关联关系当作处罚依据。

## 9. Status Flow

建议状态：

- imported
- standardized
- missing_required_input
- evidence_card_ready
- pattern_summary_ready
- strategy_direction_draft
- manual_review_required
- archived

## 10. Manual Review Boundary

人工复核必须关注：

- 是否把申诉文本误当事实。
- 是否把在线日志 no_data 误当反证。
- 是否忽略反证或误伤风险。
- 是否把 batch 聚合误写成自动上线结论。
- 是否遗漏关键补证动作。
