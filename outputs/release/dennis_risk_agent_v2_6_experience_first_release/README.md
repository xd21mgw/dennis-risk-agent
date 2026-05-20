# Dennis Risk Agent v2.6 Experience-First Release

## 1. 当前版本定位

`dennis_risk_agent_v2_6_experience_first_release` 是体验优先的最小可用 Dennis Agent release package。

本版本目标不是继续新增平台手脚，而是让内部 Agent 云端升级后，在用户输入真实业务问题时，稳定完成：

- 识别风险场景。
- 选择合适能力。
- 组织证据和反证。
- 给出清晰结论边界。
- 给出下一步最小补证动作。

## 2. 当前阶段原则

- 手脚暂时冻结。
- 不新增真实平台能力。
- 不修改真实平台读取逻辑。
- 不执行真实平台查询。
- 不引入自动处置或自动风险定性。
- 用户仍按业务问题提问，系统内部按 capability routing 执行。

## 3. 包内核心文件

- `computer_use_poc/user_experience_golden_cases.md`
  - 6 个体验黄金 Case。
- `computer_use_poc/answer_experience_templates.md`
  - 风险研判、原因解释、实体关系查询 3 类回答模板。
- `computer_use_poc/scene_to_capability_routing.md`
  - 体验优先场景到能力路由。
- `computer_use_poc/smoke_tests.md`
  - 包含体验黄金 Case smoke tests 和 dry run 记录索引。
- `computer_use_poc/run_logs/user_experience_golden_cases_dry_run_001.md`
  - 6 个 golden case 离线干跑验收。
- `computer_use_poc/README.md`
  - 当前 computer use POC 总说明。

## 4. 集成后用户体验目标

用户不需要知道平台、接口或字段细节，只需要按业务问题提问，例如：

- “帮我看这个用户是不是被盗号。”
- “这个用户为什么登录失败 / 被验证。”
- “这个设备是不是群控 / root / hook / frida。”
- “这个用户最近关联了哪些设备。”
- “这个设备关联了哪些用户。”
- “这个策略命中到底说明什么。”

Dennis Agent 应输出业务可读回答，而不是平台导航说明。

## 5. 后续验证

后续真实只读验证需要等云端内部 Agent 升级后进行。

优先验证：

1. ATO 用户研判。
2. 登录失败 / 被验证原因解释。

## 6. 边界

本 release 不包含：

- 新平台手脚。
- 真实平台访问结果。
- 核心 Skill 修改。
- final package 压缩包。
- cookie、token、storageState 或任何认证态资产。
- 自动处罚、封禁、冻结、踢 token、策略上线能力。
