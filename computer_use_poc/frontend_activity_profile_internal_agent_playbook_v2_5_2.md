# Frontend Activity Profile Internal Agent Playbook v2.5.2

## 1. 当前能力范围

本 playbook 面向 Dennis 子 Agent / browser computer use 执行。

当前只支持设计“前端活跃画像只读观察”，聚焦页面上方统计层信息和“用户属性及时长”区域。

支持的查询对象：

- `userId`
- `deviceId`

支持的 App：

- `KUAISHOU`
- `NEBULA`

当前不支持：

- 下方行为记录。
- 行为回放。
- 行为序列。
- 行为统计。
- 单条事件详情。
- 事件参数。
- 页面路径明细。
- 自动风险定性。
- 自动处置。

## 2. 执行前置顺序

必须按 v2.4.9 前置检查顺序执行：

```text
source_entry_resolution
→ browser_auth_preflight
→ saved_state_reuse_check
→ single_browser_session_check
→ 页面字段探索
```

直联 URL 模板来自：

`computer_use_poc/frontend_activity_profile_url_templates_v2_5_2.md`

## 3. URL 构造规则

必填：

- `appName`: `KUAISHOU` / `NEBULA`
- `filtersType`: `userId` / `deviceId`
- `filtersValue`: 用户 ID 或设备 ID
- `funcType`: `USER_PROFILE_QUERY`
- `actionType`: `detail`

禁止：

- 猜测其他 appName。
- 手动拼接未确认参数作为能力声明。
- 在未完成页面加载验证前声称查询成功。

## 4. 页面读取范围

优先读取统计层 evidence，不把明细行为序列作为必需前置。

首选：

- 使用 `sequence_list` URL 直达 `USER_PROFILE_QUERY`。
- 先读取页面可见统计层字段。

统计层字段包括：

- 用户 ID / 设备 ID
- 注册时间
- 月活跃天数
- 粉丝分布
- 设备属性
- 设备类型
- 地区
- 用户画像 / 设备画像
- 使用时长趋势图
- 每日使用时长
- 活跃天数与使用时长派生判断

不得读取：

- 下方行为记录。
- 单条事件详情。
- 事件参数。
- 行为回放。
- 行为序列。

明细行为序列只是可选补证。如果明细数据未同步、日期选择器复杂、设备下拉框不可用、导入数据耗时或 SPA 控件反复失败，应快速降级为 `partial_source`，不得无限尝试。

## 5. 输出 interpretation

允许输出：

- 是否存在前端活跃信号。
- 活跃强度：none / weak / medium / strong / unknown。
- 判断依据：活跃天数、使用时长趋势、日使用时长点位。
- 统计层字段如何支撑或削弱当前风险假设。
- 与登录日志 / 后端请求 / 设备画像的交叉验证建议。
- 证据边界：不能证明真人 / 本人 / 具体动作。

禁止输出：

- 该用户一定是真人。
- 该用户一定本人操作。
- 该设备没有自动化风险。
- 某个业务动作已经发生。
- 正常 / 黑产最终定性。

## 6. 标准 observation 输出

按以下文件输出：

`computer_use_poc/frontend_activity_profile_observation_schema_v2_5_2.md`

## 7. 标准执行 Prompt 模板

```text
请按 v2.5.2 frontend_activity_profile 只读 playbook 执行。

目标：
只观察埋点分析 / 用户洞查 / 用户细查详情页面上方“用户属性及时长”区域，判断是否存在前端活跃信号。

输入：
- appName:
- filtersType:
- filtersValue:

要求：
1. 先按 v2.4.9 做 source_entry_resolution 和 browser_auth_preflight。
2. 使用 URL template 构造直联 URL。
3. 只读取用户属性及时长区域。
4. 不读取下方行为记录、行为回放、行为序列、事件详情或事件参数。
5. 输出 frontend_activity_profile_observation。
6. 活跃信号只能作为前端活跃痕迹，不得解释为真人、本人与具体业务动作。
```

## 8. 边界

- 不修改核心 Skill。
- 不更新 final release package。
- 不改变 DataAgent / Hive 边界。
- 不引入自动处置。
- 不引入自动风险定性。

## 9. SPA Loop Guard

track-analysis / browser SPA 操作必须设置最大尝试边界。

停止条件：

- 同一动作连续失败超过 3 次。
- 同一下拉框 / 日期选择器 / 导入数据按钮连续不可用。
- 连续截图显示同一失败 UI，没有新增字段产出。
- 页面进入 auth HTML / 2FA / 权限阻断 / session issue。

停止后输出：

```yaml
browser_spa_loop_guard:
  operation_loop_detected: true
  failed_action:
  failed_attempt_count:
  platform_access_partial: true
  browser_overuse_prevented: true
  query_status: partial_source
  completed_sources:
  blocked_or_timeout_sources:
  next_action:
    - use_stats_layer_if_available
    - offline_hive_or_dataagent_query_plan
    - manual_platform_check
```

禁止：

- 无限操作设备下拉框、日期选择器、导入数据按钮。
- 把明细行为序列不可用解释为没有前端行为。
- 因 track-analysis partial source 阻断整体证据卡。
