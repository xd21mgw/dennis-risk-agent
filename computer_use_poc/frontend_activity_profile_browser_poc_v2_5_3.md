# Frontend Activity Profile Browser POC v2.5.3

## 1. 阶段定位

v2.5.3 基于内部 Agent 返回的直联 URL 预检结果，进入前端活跃画像 browser readonly POC 阶段。

本阶段目标是由内部 Agent 读取页面上方“用户属性及时长”区域，并形成第一份结构化 observation sample。

重要分工：

- Codex：开发与文档沉淀工具，负责 schema / playbook / run log / 开发说明。
- 内部 Agent：访问内部平台、截图、只读观察、返回结构化结果。
- Dennis Agent：未来运行在内部 Agent 系统中，理解用户问题，按 playbook 调用这些只读手脚，并消化 observation。

Codex 不登录、不访问、不截图内部平台。

## 2. 已完成预检

内部 Agent 已完成 direct-open preflight。

run log：

`computer_use_poc/run_logs/dennis_frontend_activity_profile_direct_open_preflight_run_001.md`

预检结论：

```yaml
platform: track_analysis
test_type: url_direct_open_preflight
url_opened: true
login_state_reused: true
redirected_to_login: false
permission_blocked: false
page_loaded: true
target_page_detected: true
target_area_visible: true
blocker_type: none
validation_status: direct_open_preflight_validated_by_internal_agent
```

已观察到：

- 页面标题为“埋点分析”。
- URL 无跳转，目标 URL 完全匹配。
- 成功进入“用户细查详情”页面。
- 用户属性区域完整可见。
- “用户属性及时长”标题区域可见。
- 使用时长时间序列图表可见。
- 行为记录区域存在“行为回放”、“行为序列”、“行为统计”标签，但本 POC 不读取这些区域。

## 2-A. 已完成单点 observation

内部 Agent 已完成 KUAISHOU + userId + 444946196 单点 browser readonly POC。

归档文件：

- `computer_use_poc/run_logs/dennis_frontend_activity_profile_readonly_run_002.md`
- `computer_use_poc/observations/frontend_activity_profile_observation_sample_v2_5_3.yaml`

结论：

```yaml
validation_status: frontend_activity_profile_single_observation_validated
app_name: KUAISHOU
query_subject_type: userId
query_subject_value: "444946196"
target_area_visible: true
screenshot_saved: true
observation_generated: true
activity_strength: strong
```

该 observation 只能证明存在较强前端活跃信号，不能单独证明真人、本人与具体业务动作。

## 2-B. 已完成四组合矩阵验证

内部 Agent 已完成 KUAISHOU / NEBULA × userId / deviceId 四组合矩阵验证。

归档文件：

- `computer_use_poc/run_logs/dennis_frontend_activity_profile_matrix_validation_run_001.md`
- `computer_use_poc/observations/frontend_activity_profile_matrix_validation_v2_5_4.yaml`

结论：

```yaml
validation_status: matrix_validation_passed_by_internal_agent
total_cases: 4
success_cases: 4
partial_success_cases: 0
failed_cases: 0
```

已验证：

- KUAISHOU / NEBULA × userId / deviceId 四组合均可直联查询。
- 四组合均可复用登录态，无登录跳转，无权限阻断。
- 四组合均能读取“用户属性及时长”区域。
- KUAISHOU 端活跃信号强。
- NEBULA 端使用时长几乎为零。
- deviceId 查询在样例中自动关联到同一用户，但不能单独证明稳定设备绑定关系。

## 2-C. DOM text read feasibility

v2.5.3 / v2.5.4 初始 observation 和 matrix validation 中，profile card 与使用时长字段最初来自 `screenshot_manual_read`，不是 DOM 文本读取。

原因：

- 原执行只使用 `snapshot -i` 和 `screenshot --full`。
- 未使用 `agent-browser get text @ref` 提取 DOM 文本。
- `snapshot -i` 返回的交互 ref 没有覆盖 profile card 的静态文本节点。

后续内部 Agent 已验证 DOM 文本读取可行：

```text
iframe[1].contentDocument → .user-card → innerText
```

DOM 提取结果与截图视觉识别一致，可读取：

- user_id: `444946196`
- register_time: `2017-02-17 19:30:21`
- fan_distribution: `100-1k`
- active_days_bucket: `16-30天`
- 年龄：`26`
- 地域：`浙江-嘉兴`
- 设备类型未知 / 归因渠道未知 / 渠道定向策略未知

执行建议：

- 首次需要 1-2 次 eval 探测 iframe / selector。
- 后续每次查询可用 1 次 eval 定向提取 profile card 文本。
- 相比截图，DOM text read token 成本更低，批量查询更稳定。

使用时长图表限制：

- 使用时长图表是 canvas 渲染。
- DOM 可确认 `chart_present=true` / `canvas_rendered`。
- DOM innerText 不能直接提取具体柱状数值、峰值和每日数据点。
- 如需精确使用时长数值，后续优先探索 tooltip / 图表数据接口 / network API，而不是长期依赖截图。

## 2-D. extraction mode cost guidance

| extraction_mode | 适用场景 | 成本判断 | 限制 |
| --- | --- | --- | --- |
| `screenshot_manual_read` | 首次探索、截图留证、图表视觉判断 | 成本较高，适合少量样例 | 不适合批量稳定抽取文本字段 |
| `dom_text_read` | 批量抽取 profile card 字段 | 成本低，稳定性更好 | 需先确认 iframe / selector |
| `visual_estimation` | 使用时长趋势、峰值粗估 | 可快速判断强弱 | 非精确数值 |
| `tooltip_or_api_probe` | 精确使用时长数值 | 后续推荐方向 | 尚未验证 |

## 3. v2.5.3 browser readonly POC 范围

只读取：

- 用户 ID / 设备 ID
- 注册时间
- 粉丝分布
- 月活跃天数
- 设备属性
- 使用时长趋势图
- 每日使用时长
- 是否存在前端活跃信号
- 活跃强度派生判断

不读取：

- 下方行为记录。
- 行为回放。
- 行为序列。
- 行为统计。
- 单条事件详情。
- 事件参数。
- 页面路径明细。

## 4. 内部 Agent 下一步任务

建议发送给内部 Agent 的任务：

```text
请基于 v2.5.3 frontend_activity_profile browser readonly POC 执行。

目标：
只读取埋点分析 / 用户洞查 / 用户细查详情页面上方“用户属性及时长”区域，输出 frontend_activity_profile_observation。

要求：
1. 使用已验证的直联 URL。
2. 只读取用户属性区域和使用时长图表区域。
3. 不读取下方行为记录、行为回放、行为序列、行为统计、单条事件详情或事件参数。
4. 输出字段：
   - platform
   - module
   - app_name
   - query_subject_type
   - query_subject_value
   - query_url
   - query_status
   - profile_card
   - usage_duration
   - activity_judgement
   - next_evidence_to_collect
   - raw_observation_reference
5. 活跃天数 / 使用时长只能解释为前端活跃信号，不得解释为真人、本人与具体业务动作。
6. 不做自动风险定性，不做自动处置。
```

## 5. 成功标准

```yaml
success_criteria:
  target_area_visible: true
  profile_card_extracted: true
  usage_duration_chart_detected: true
  activity_judgement_generated: true
  behavior_records_untouched: true
  readonly_safety_check: passed
```

## 6. 失败 / 降级

| 场景 | 返回 |
| --- | --- |
| 页面跳登录 | `auth_blocked` |
| 权限提示 | `permission_blocked` |
| 目标区域不可见 | `target_area_not_visible` |
| 图表不可见 | `usage_duration_chart_missing` |
| 只看到行为记录区域 | `wrong_area_detected` |
| 页面空白 / 报错 | `page_load_failed` |

降级解释：

- 页面不可访问不等于用户无活跃。
- 目标区域不可见不等于无前端行为。
- 图表缺失不等于无活跃。
- 空结果不能直接解释为无风险。

## 7. 边界

- 不修改核心 Skill。
- 不更新 final release package。
- 不改变 DataAgent / Hive 边界。
- 不引入自动处置。
- 不引入自动风险定性。
- 本阶段不解析完整行为序列。
- 当前能力适合提供“前端活跃存在性证据”。
- 不能单独证明真人操作。
- 不能单独证明本人操作。
- 不能单独证明具体业务动作发生。
- 不能单独证明设备稳定绑定关系。
- 后续如需具体动作链路，需要另起行为序列手脚，不要混在本手脚内。
