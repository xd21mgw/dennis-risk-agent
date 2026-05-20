# Dennis Risk Agent v2.6 Experience-First Manifest v1

## 1. 版本状态

```yaml
release_name: dennis_risk_agent_v2_6_experience_first_release
release_type: cloud_internal_agent_integration_package
status: ready_for_cloud_internal_agent_integration
platform_hands_frozen: true
new_platform_capability_added: false
real_platform_query_executed: false
core_skill_modified: false
release_package_archive_generated: false
```

## 2. 包含文件

| 文件 | 用途 |
|---|---|
| `README.md` | release 包说明和集成定位 |
| `dennis_risk_agent_v2_6_experience_first_manifest_v1.md` | 包清单、边界、风险、后续计划 |
| `integration_notes.md` | 云端内部 Agent 集成说明 |
| `smoke_test_summary.md` | 体验黄金 Case 干跑总结 |
| `computer_use_poc/README.md` | 当前 computer use POC 总说明 |
| `computer_use_poc/user_experience_golden_cases.md` | 6 个体验黄金 Case |
| `computer_use_poc/answer_experience_templates.md` | 3 类标准回答模板 |
| `computer_use_poc/scene_to_capability_routing.md` | 场景到能力路由 |
| `computer_use_poc/smoke_tests.md` | smoke tests 总索引 |
| `computer_use_poc/run_logs/user_experience_golden_cases_dry_run_001.md` | 6 个 Case 离线干跑记录 |

## 3. 版本边界

本版本只解决使用体验稳定性：

- 用户按业务问题提问。
- Dennis Agent 内部做 capability routing。
- 输出先给结论或解释，再给证据、边界和下一步。
- 不因为平台能力多而过度查数、过度调平台。

本版本不改变：

- 真实平台读取逻辑。
- 核心 Skill。
- DataAgent / Hive 边界。
- 认证态管理方式。
- 处置 / 审批 / 策略上线能力。

## 4. 不包含内容

- 不包含新平台手脚。
- 不包含真实平台访问。
- 不包含新的接口能力。
- 不包含 `outputs/packages/`。
- 不包含 cookie / token / storageState / session / KIM code。
- 不包含自动风险定性或自动处置。

## 5. 已知风险

- 当前仅完成离线 dry run，未在云端内部 Agent 中做真实只读回归。
- 如果云端 Agent 没有正确加载 `scene_to_capability_routing.md`，可能退化为平台清单式回答。
- 设备风险补证需要严格执行输入完整性规则：Device SDK 前置输入是 deviceId；userId 输入先走 user_to_device；无法解析时返回 `missing_device_id`。
- 策略命中、单次登录失败、单一设备关联都不能单独作为最终作弊或盗号定性。

## 6. 后续验证计划

P0：

- 在云端内部 Agent 集成后，先跑 ATO 用户研判真实只读验证。
- 再跑登录失败 / 被验证原因解释真实只读验证。

P1：

- 验证设备风险补证的 `missing_device_id` / `user_to_device` 输入完整性分支。
- 验证策略命中解释是否保留 riskDecision 边界。

P2：

- 将体验黄金 Case 扩展到更多业务问题前，必须先完成现有 6 个 Case 的云端回归。
