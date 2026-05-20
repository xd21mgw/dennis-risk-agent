# Smoke Test Summary

## 1. Dry Run 结果

来源：

- `computer_use_poc/run_logs/user_experience_golden_cases_dry_run_001.md`

结果：

```yaml
total_cases: 6
passed_cases: 6
failed_cases: 0
overall_result: passed
real_platform_called: false
new_platform_hand_added: false
platform_read_logic_modified: false
```

## 2. 6 个 Golden Case

| Case | 结果 | 说明 |
|---|---|---|
| ATO 用户研判 | pass | 能先给风险线索判断，再拆支持证据、反证、缺口和下一步 |
| 登录失败 / 被验证原因 | pass | 能按原因解释组织，不把 riskDecision 写成最终处置 |
| 设备风险补证 | pass | 能输出设备侧证据边界 |
| 用户关联设备查询 | pass | 能先做 user_to_device，不直接拿 userId 调 Device SDK |
| 设备关联用户查询 | pass | 能输出关系摘要，不直接定性团伙 |
| 策略命中解释 | pass | 能说明策略命中是证据，不是最终定性 |

## 3. 设备风险补证 input completeness 修正

dry run 发现的轻微体验问题：

- 如果用户问“这个设备是不是群控/root/hook/frida”，但没有提供 deviceId，不能直接进入 Device SDK。

已修正规则：

- Device SDK 前置输入是 deviceId / did / deviceceid。
- 输入是 userId 时，先走 user_to_device entity resolution。
- 缺少 deviceId 且无法解析时，返回 `missing_device_id`。
- 设备风险补证只能说明设备侧异常证据，不直接定性作弊或盗号。

## 4. 是否适合进入云端内部 Agent 集成

结论：适合进入云端内部 Agent 集成。

理由：

- 6 个体验黄金 Case 已完成离线 dry run。
- 回答模板覆盖风险研判、原因解释、实体关系查询三类常见体验。
- capability routing 已明确应调用和不应调用能力。
- 主要体验问题已修正为输入完整性规则。

## 5. 集成后优先真实只读验证

建议优先验证：

1. ATO 用户研判。
2. 登录失败 / 被验证原因解释。

验证要求：

- 只读。
- 不新增平台手脚。
- 不修改真实读取逻辑。
- 不输出敏感认证信息。
- 不把单一证据写成最终风险定性。
