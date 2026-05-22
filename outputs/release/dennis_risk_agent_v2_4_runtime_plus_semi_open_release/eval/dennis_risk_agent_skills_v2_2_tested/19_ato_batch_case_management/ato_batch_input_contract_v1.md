# ATO Batch Input Contract v1

## 1. 定位

本文件定义 ATO / 盗号批量 case analysis 的输入契约。目标是让用户提交的 5-20 个 case 可以被 Dennis Agent 标准化成 case_registry，再进入 evidence card、pattern summary 和候选策略方向流程。

边界：

- 不调用真实 DataAgent。
- 不访问真实内部平台。
- 不自动处置。
- 不自动上线策略。
- 输入契约只定义字段和缺字段处理，不生成真实 observation。

## 2. 推荐输入规模

- v1 推荐范围：5-20 cases。
- 少于 5 个：可走 single/few case analysis 或 ATO case expansion planning。
- 多于 20 个：先进入 Plan / scope control，必要时要求分批或转离线 DataAgent / Hive 取数。

## 3. 必填字段

| field | type | required | purpose | missing_status |
|---|---|---:|---|---|
| case_id | string | yes | case 唯一标识 | missing_case_id |
| user_id | string | yes | 账号实体 | missing_user_id |
| event_time | datetime/string | yes | 异常发生时间 | missing_event_time |
| abnormal_action | string | yes | 异常动作，如发布、私信、改密、换绑、关注、支付 | missing_abnormal_action |

缺任一必填字段时：

- 不进入事实结论。
- 标记 `needs_fields`。
- 只输出需要补充的信息。

## 4. 强建议字段

| field | type | purpose | missing_handling |
|---|---|---|---|
| device_id | string | 设备侧补证、实体解析 | missing_device_id，进入 missing evidence，不阻断 case intake |
| user_claim | string | 用户申诉或客服记录摘要 | 缺失时不影响导入，但减少人工语义上下文 |
| source_channel | string | 样本来源，如申诉、客服、人工抽样 | 缺失时标记 source_channel_unknown |
| available_evidence | list/object | 已有证据和 source metadata | 缺失时标记 no_initial_evidence |

## 5. 可选字段

| field | type | purpose |
|---|---|---|
| manual_label | string | 人工标签 / golden hint，只能作为参考 |
| initial_risk_hint | string | 初始风险线索 |
| notes | string | 附加说明，不放敏感原文 |

## 6. available_evidence 契约

每条 available_evidence 建议包含 source metadata：

```yaml
available_evidence:
  - evidence_id:
    evidence_item:
    evidence_value:
    evidence_source:
      source_name:
      source_type:
      source_tool_or_hand:
      source_platform:
      collected_at:
      evidence_time_range:
      raw_reference:
    source_quality:
      freshness_status:
      freshness_risk:
      permission_status:
      reliability_level:
```

source_type 枚举：

- internal_platform_api
- browser_dom_read
- screenshot_manual_read
- dataagent_hive
- manual_input
- model_inference
- historical_doc

边界：

- `manual_input` 不能单独作为 strong conclusion。
- `model_inference` 不能作为 raw evidence。
- 登录日志超窗 no_data 必须标记 freshness/window risk。

## 7. 缺字段处理

| condition | status | handling |
|---|---|---|
| 缺 user_id | missing_user_id | 不生成查询计划，不输出 ATO 结论 |
| 缺 event_time | missing_event_time | 不判断登录窗口，不输出 ATO 结论 |
| 缺 abnormal_action | missing_abnormal_action | 不进入 case evidence card |
| 缺 device_id | missing_device_id | 进入 missing evidence，不阻断导入 |
| 候选实体过多 | too_many_candidates | 要求缩小范围，不默认批量深查 |
| 非 ATO case | unsupported_case_type | 路由到其他 batch / scene，或返回不支持 |

## 8. 输入示例

```yaml
ato_batch_input:
  batch_id: ato_batch_example_001
  cases:
    - case_id: ato_case_001
      user_id: user_ref_001
      device_id: device_ref_001
      event_time: "2026-05-20 12:30:00"
      abnormal_action: "非本人发布"
      user_claim: "用户称未操作"
      source_channel: "appeal"
      available_evidence:
        - evidence_id: ev_001
          evidence_item: "异设备登录后发布"
          evidence_source:
            source_name: unified_login_log
            source_type: internal_platform_api
            source_tool_or_hand: login_log_read
            source_platform: user_login_unified_log
            collected_at: "simulated"
            evidence_time_range: "event_window"
            raw_reference: "safe_ref://ato_case_001/login"
          source_quality:
            freshness_status: fresh
            freshness_risk: low
            permission_status: success
            reliability_level: high
      manual_label:
      initial_risk_hint: "疑似 ATO"
      notes:
```

## 9. 不接受的输入

- 要求自动封禁 / 解封 / 限流。
- 要求直接上线策略。
- 要求输出 cookie / token / session / header。
- 要求不经审批批量扩散所有关联账号。
- 把非 ATO 的账号矩阵 / 导流样本强行当 ATO。
