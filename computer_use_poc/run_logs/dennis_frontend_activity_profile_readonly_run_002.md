# Dennis Frontend Activity Profile Readonly Run 002

## 1. 测试目标

归档 v2.5.3 前端活跃画像只读手脚的单点 observation 实测结果。

## 2. 结果来源

本 run log 沉淀的是内部 Agent 返回的真实平台访问结果。

说明：

- Codex 没有登录或访问埋点分析平台。
- Codex 只负责工程沉淀、文档更新、run log 归档和 observation sample 落盘。
- 内部 Agent 负责访问内部平台、截图、页面观察和结构化结果返回。

## 3. 测试对象

```yaml
platform: track_analysis
module: 用户洞查 / 用户细查详情 / 用户属性及时长
app_name: KUAISHOU
query_subject_type: userId
query_subject_value: "444946196"
test_stage: v2.5.3
```

## 4. 实测结论

```yaml
validation_status: frontend_activity_profile_single_observation_validated
url_direct_open: true
login_state_reused: true
page_loaded: true
target_area_visible: true
screenshot_saved: true
observation_generated: true
behavior_records_read: false
readonly_safety_check: PASSED
extraction_mode: screenshot_manual_read
dom_text_read_available: true
dom_text_read_verified_afterward: true
dom_extraction_path: iframe[1].contentDocument → .user-card → innerText
```

结论口径：

- KUAISHOU + userId + 444946196 单点 browser readonly POC 成功。
- URL 可直联。
- 登录态可复用。
- 页面可加载。
- “用户属性及时长”区域可见。
- 截图已保存。
- 已形成前端活跃画像 observation。

## 4-A. extraction_mode 修正

原 v2.5.3 执行时只使用了 `snapshot -i` 和 `screenshot --full`。

因此以下字段最初应标记为 `screenshot_manual_read`：

- `user_id`
- `register_time`
- `active_days_bucket`
- `fan_distribution`
- `device_attributes`
- 使用时长图表峰值和每日趋势视觉判断

内部 Agent 后续补充确认：

- 页面为 wujie 微前端。
- profile card 位于 `iframe[1].contentDocument`。
- 可通过 `iframe[1].contentDocument → .user-card → innerText` 提取 profile card 文本。
- DOM 提取结果与截图视觉识别一致。

DOM 已验证可读取：

- user_id: `444946196`
- register_time: `2017-02-17 19:30:21`
- fan_distribution: `100-1k`
- active_days_bucket: `16-30天`
- 年龄：`26`
- 地域：`浙江-嘉兴`
- 设备类型未知 / 归因渠道未知 / 渠道定向策略未知

使用时长图表为 canvas 渲染：

- DOM 可确认 `chart_present=true` / `canvas_rendered`。
- DOM innerText 不能直接提取柱状图具体数值、峰值和每日数据点。
- 如需精确使用时长数值，后续需要截图视觉识别、tooltip 探测或底层接口 / API 替代。

## 5. 证据边界

该 observation 只能证明存在较强前端活跃信号。

不能单独证明：

- 真人操作。
- 本人操作。
- 具体业务动作发生。
- 无自动化、脚本、群控。
- 设备稳定绑定关系。

如果需要判断具体动作链路，必须进一步查行为序列、后端业务日志、统一登录日志、设备 SDK / 设备画像或 DataAgent / Hive。

## 6. observation 文件

```text
computer_use_poc/observations/frontend_activity_profile_observation_sample_v2_5_3.yaml
```

## 7. 未完成项

- 未读取下方行为记录。
- 未打开行为回放。
- 未解析行为序列。
- 未读取行为统计。
- 未读取单条事件详情。
- 未读取事件参数。

## 8. 边界

- 不修改核心 Skill。
- 不更新 final release package。
- 不改变 DataAgent / Hive 边界。
- 不引入自动处置。
- 不引入自动风险定性。
