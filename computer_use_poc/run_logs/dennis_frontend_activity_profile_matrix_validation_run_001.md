# Dennis Frontend Activity Profile Matrix Validation Run 001

## 1. 测试目标

归档 v2.5.4 前端活跃画像只读手脚四组合矩阵验证结果。

矩阵范围：

- KUAISHOU + userId
- NEBULA + userId
- KUAISHOU + deviceId
- NEBULA + deviceId

## 2. 结果来源

本 run log 沉淀的是内部 Agent 返回的真实平台访问结果。

说明：

- Codex 没有登录或访问埋点分析平台。
- Codex 没有截图或抓取真实页面。
- Codex 只负责文档沉淀、run log 归档和 observation / matrix sample 落盘。
- 内部 Agent 负责访问内部平台、截图、只读观察和结构化结果返回。

## 3. 验证摘要

```yaml
frontend_activity_profile_matrix_validation:
  platform: track_analysis
  test_stage: v2.5.4
  total_cases: 4
  success_cases: 4
  partial_success_cases: 0
  failed_cases: 0
  validation_status: matrix_validation_passed_by_internal_agent
  extraction_mode: screenshot_manual_read
  dom_text_read_available: true
  dom_text_read_verified_afterward: true
  dom_extraction_path: iframe[1].contentDocument → .user-card → innerText
  usage_duration_chart_mode: canvas_rendered
```

## 4. 成功点

- 四组合矩阵全部验证通过。
- 所有组合均可直联打开。
- 登录态均可复用。
- 均无登录跳转。
- 均无权限阻断。
- 均能读取“用户属性及时长”区域。
- 均能看到 profile card 和使用时长图表。
- 均已保存截图。

## 5. 关键发现

1. KUAISHOU 端该用户前端活跃信号强，使用时长图表有明显波动。
2. NEBULA 端该用户 / 设备使用时长几乎为零，可能极少使用极速版。
3. deviceId 查询在本次样例中自动关联到同一用户 444946196，但不能单独证明稳定设备绑定关系。
4. 设备维度查询的使用时长峰值低于用户维度，可能该设备非主要使用设备。

## 5-A. extraction_mode 修正

v2.5.4 四组合矩阵最初执行时只使用 `snapshot -i` 和 `screenshot --full`，没有使用 `agent-browser get text @ref` 提取 DOM 文本。

因此：

- profile card 字段最初来源是 `screenshot_manual_read`。
- 使用时长峰值、每日点位和趋势强弱最初来源是 `screenshot_manual_read` / `visual_estimation`。
- 这些字段不能写成 DOM 精确读取。

内部 Agent 后续补充验证：

- 页面为 wujie 微前端。
- profile card 位于 `iframe[1].contentDocument`。
- 可通过 `iframe[1].contentDocument → .user-card → innerText` 提取 profile card 文本。
- DOM 提取结果与截图视觉识别一致。

DOM 已验证可读取：

- `user_id`
- `register_time`
- `fan_distribution`
- `active_days_bucket`
- 年龄
- 地域
- 设备类型 / 归因渠道 / 渠道定向策略的 unknown 状态

使用时长图表：

- 为 canvas 渲染。
- DOM 可确认图表存在。
- 不能通过 DOM innerText 直接提取具体柱状数值、峰值和每日数据点。
- 精确数值后续应优先探索 tooltip / 图表数据接口 / network API，而不是长期依赖截图。

## 6. matrix 文件

```text
computer_use_poc/observations/frontend_activity_profile_matrix_validation_v2_5_4.yaml
```

## 7. 证据边界

该手脚当前适合提供“前端活跃存在性证据”。

不能单独证明：

- 真人操作。
- 本人操作。
- 具体业务动作发生。
- 设备稳定绑定关系。
- 无自动化、脚本、群控。

仍未读取：

- 下方行为记录。
- 行为回放。
- 行为序列。
- 行为统计。
- 单条事件详情。
- 事件参数。

如果需要具体动作链路，需要另起行为序列手脚，不要混在本手脚内。

## 8. 下一步

- 如需判断具体业务动作，需要进一步查看行为序列或后端业务日志。
- 如需验证设备真实性，需要结合设备 SDK / 设备画像。
- 如需验证登录环境，需要结合用户登录统一日志。
- 如需批量统计，需要交给 DataAgent / Hive 做群体分析。

## 9. 边界

- 不修改核心 Skill。
- 不更新 final release package。
- 不改变 DataAgent / Hive 边界。
- 不引入自动处置。
- 不引入自动风险定性。
