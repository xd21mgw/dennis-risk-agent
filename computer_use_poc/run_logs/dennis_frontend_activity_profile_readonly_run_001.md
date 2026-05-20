# Dennis Frontend Activity Profile Readonly Run 001

## 1. 测试目标

沉淀 v2.5.2 前端活跃画像只读手脚的方法论、URL 模板、observation schema 和测试用例。

## 2. 输入来源

本轮依据用户提供的平台路径和 URL 示例完成文档设计。

平台路径：

```text
埋点分析 → 分析工具 → 用户洞查 → 用户细查详情
```

已知 URL 示例：

- KUAISHOU + userId
- NEBULA + userId
- KUAISHOU + deviceId

## 3. 当前执行状态

```yaml
validation_status: design_only_pending_browser_validation
actual_platform_login: false
real_data_captured: false
dom_selector_validated: false
behavior_records_parsed: false
readonly_safety_check: not_applicable_design_only
```

## 4. 已完成沉淀

- 定义“前端活跃画像只读手脚”定位。
- 明确只读取上方“用户属性及时长”区域。
- 抽象 URL 模板：
  - KUAISHOU + userId
  - NEBULA + userId
  - KUAISHOU / NEBULA + deviceId
- 定义 frontend_activity_profile_observation schema。
- 设计 6 个测试用例。
- 固化证据解释边界。

## 5. 本轮未做

- 未实际登录平台。
- 未抓取真实数据。
- 未验证 DOM selector。
- 未解析下方行为记录。
- 未打开行为回放。
- 未读取事件参数。
- 未输出真实用户 / 设备 observation。

## 6. 下一步

下一步需要做真实 browser 只读 POC，验证：

- URL 直联。
- 页面加载。
- 红框区域字段识别。
- 截图留存。
- observation 输出。

## 7. 边界

- 不修改核心 Skill。
- 不更新 final release package。
- 不改变 DataAgent / Hive 边界。
- 不引入自动处置。
- 不引入自动风险定性。
