# Real DataAgent Case 001 Missing Input Boundary Review

## 1. Data Agent 返回了什么

Data Agent 返回的是最小输入边界反馈，而不是查询失败，也不是 no_permission。

核心反馈：

- 没有具体 case 标识，无法跑 SQL。
- 没有时间窗口，无法定位分区和查询范围。
- 业务场景 / 接口范围不明确，无法找表和生成 SQL。
- 当前只能停留在框架层面，不能产出实际数据发现。

Data Agent 同时明确能力边界：

- 可查：离线 Hive / BI / 看板 / SQL / 表检索。
- 不可直接取证：实时前端日志、实时后端 service 日志、NG 网关明细、实时策略引擎、实时指纹、在线关系图。

## 2. 为什么这不是失败，而是最小输入边界命中

这不是 Data Agent 执行失败，因为尚未进入可执行查询阶段。

命中边界：

- 缺 entity_identifier。
- 缺 time_window。
- 缺 business_context。
- 缺 target_api_or_action。

因此应标记：

```yaml
status: blocked_by_missing_minimum_inputs
returned_type: missing_input_boundary_feedback
```

不应标记：

- `success`
- `failed`
- `no_permission`
- `empty_result`
- `partial`

## 3. question_encoder 需要如何调整

已在 `query_intent_to_question_encoder_v1.md` 中新增“调用前最小输入校验”。

规则：

- 缺 `entity_identifier` 或 `time_window` 时，不生成可执行 Data Agent question。
- 不调用 Data Agent。
- 不进入 parser / normalized evidence 阶段。
- 生成 `missing_input_request`。

最小输入：

- `entity_identifier`：user_id / device_id / session_id / trace_id / risk_event_id / request_id 至少一个。
- `time_window`：start_time / end_time 或具体日期区间。
- `business_context`：建议必填。
- `target_api_or_action`：建议必填。

## 4. real_pilot runbook 需要如何调整

已在 `protocol_attack_real_pilot_runbook_v1.md` 中新增“真实只读 case 启动前置条件”。

缺失时：

- case 状态标记为 `blocked_by_missing_minimum_inputs`。
- 不能调用 Data Agent。
- 不能生成风险结论。
- 只能输出待补信息清单。

## 5. 后续真实 case 应如何准备输入

下一次真实 case 应至少准备：

```yaml
real_case_input:
  case_id:
  entity_identifier:
    user_id:
    device_id:
    session_id:
    trace_id:
    risk_event_id:
    request_id:
  time_window:
    start_time:
    end_time:
  business_context:
    business_scene:
    target_api_or_action:
    target_api_pattern:
```

可选但建议补充：

- app 版本 / 渠道 / 包类型。
- 风险事件来源。
- 业务动作描述。
- 已知异常表现。
- 是否存在商家 / 达人 / MCN / 授权运营可能。

## 6. 是否修改核心 Skill

否。本轮只修改 Data Agent adapter / real_pilot 相关文档和 review 输出。

