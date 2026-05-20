# Dennis Risk Agent v2.6 Experience-First Release Snapshot

## 1. 版本定位

v2.6 experience-first 是面向云端内部 Agent 集成的最小可用体验版本。

目标不是新增平台手脚，而是让用户用自然业务问题提问时，Dennis Agent 能稳定完成：

- 场景识别。
- capability routing。
- 证据组织。
- 结论边界。
- 下一步建议。

## 2. 本次吸收内容

release package 路径：

```text
outputs/release/dennis_risk_agent_v2_6_experience_first_release/
```

核心文件：

- `computer_use_poc/user_experience_golden_cases.md`
- `computer_use_poc/answer_experience_templates.md`
- `computer_use_poc/scene_to_capability_routing.md`
- `computer_use_poc/smoke_tests.md`
- `computer_use_poc/run_logs/user_experience_golden_cases_dry_run_001.md`
- `computer_use_poc/README.md`

## 3. 已验证状态

```yaml
experience_golden_cases_dry_run:
  total_cases: 6
  passed_cases: 6
  failed_cases: 0
  real_platform_called: false
  new_platform_hand_added: false
  platform_read_logic_modified: false
```

已覆盖：

- ATO 用户研判。
- 登录失败 / 被验证原因。
- 设备风险补证。
- 用户关联设备查询。
- 设备关联用户查询。
- 策略命中解释。

## 4. 关键体验修正

设备风险补证输入完整性已固化：

- Device SDK 前置输入是 deviceId / did / deviceceid。
- 输入是 userId 时，先走 user_to_device entity resolution。
- 缺少 deviceId 且无法解析时，返回 `missing_device_id`。
- 设备风险补证只能说明设备侧异常证据，不直接定性作弊或盗号。

## 5. 不包含内容

- 不新增平台手脚。
- 不修改核心 Skill。
- 不修改真实读取逻辑。
- 不执行真实平台访问。
- 不包含 `outputs/packages/`。
- 不包含认证态、cookie、token、storageState。
- 不引入自动处置或自动风险定性。

## 6. 后续云端集成建议

P0：

1. 加载 experience-first release 包。
2. 优先真实只读验证 ATO 用户研判。
3. 再验证登录失败 / 被验证原因解释。

P1：

- 验证设备风险补证 missing_device_id 分支。
- 验证策略命中解释不越界。

P2：

- 基于真实用户反馈调整 answer templates，不先扩平台。
