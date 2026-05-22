# Frontend Activity Profile Readonly POC v2.5.2

## 1. 定位

v2.5.2 新增 Dennis Agent 的“前端活跃画像只读手脚”。

该能力面向“埋点分析 → 分析工具 → 用户洞查 → 用户细查详情”，只读取页面上方“用户属性及时长”区域，用于判断用户 / 设备是否存在前端活跃痕迹，以及活跃强度的大致情况。

当前不是完整埋点行为序列手脚，不抓取下方行为记录，不解析单条事件，不做行为链路定性。

当前状态：

```yaml
source_name: frontend_activity_profile
platform: track_analysis
module: 用户洞查 / 用户细查详情 / 用户属性及时长
validation_status: design_pending_browser_validation
real_page_execution: false
release_status: not_in_release_package
```

## 2. 只读范围

本轮只关注页面上方“用户属性及时长”区域，包括但不限于：

- 用户 ID / 设备 ID
- 注册时间
- 月活跃天数
- 粉丝分布
- 设备属性
- 使用时长趋势图
- 每日使用时长
- 是否存在明显前端活跃
- 活跃强度判断

## 3. 暂不获取范围

本轮明确不获取：

- 下方行为记录
- 行为回放
- 行为序列
- 行为统计
- 单条事件详情
- 事件参数
- 页面路径明细

如果用户要判断具体行为链路，需要后续进入行为序列、后端日志、统一登录日志、设备 SDK 或 DataAgent / Hive 补证。

## 4. 平台与 URL 参数

平台路径：

```text
埋点分析 → 分析工具 → 用户洞查 → 用户细查详情
```

基础参数：

| 参数 | 含义 | 当前口径 |
| --- | --- | --- |
| `funcType` | 查询功能 | 固定 `USER_PROFILE_QUERY` |
| `appName` | App 名称 | 当前主要支持 `KUAISHOU` / `NEBULA` |
| `filtersType` | 查询对象类型 | `userId` / `deviceId` |
| `filtersValue` | 查询对象值 | 用户 ID 或设备 ID |
| `actionType` | 页面动作 | 固定 `detail` |

URL 模板详见：

`computer_use_poc/frontend_activity_profile_url_templates_v2_5_2.md`

## 5. 证据解释边界

必须明确：

- 有使用时长 / 活跃天数，只能说明存在前端活跃信号。
- 不能直接证明是真人操作。
- 不能直接证明是本人操作。
- 不能直接证明没有自动化、脚本、群控。
- 不能证明某个具体业务动作一定发生过。
- 如果要判断具体链路，后续需要行为序列、后端日志、登录日志、设备 SDK 共同补证。

证据定位：

| 观察项 | 可说明 | 不能说明 |
| --- | --- | --- |
| 活跃天数 | 目标对象在前端有活跃痕迹 | 真人 / 本人操作 |
| 使用时长趋势 | 活跃强度和时间分布 | 具体业务动作发生 |
| 设备属性 | 前端侧可见设备画像 | 设备无风险 |
| 粉丝分布 | 账号画像背景 | 行为真实性 |

## 6. 只读安全边界

允许：

- 打开已知直联 URL。
- 读取页面上方“用户属性及时长”区域。
- 记录字段是否可见。
- 记录活跃天数、使用时长趋势、活跃强度派生判断。
- 截图留存红框区域，前提是遵守敏感字段策略。

禁止：

- 抓取下方行为记录。
- 打开行为回放。
- 解析行为序列。
- 打开单条事件详情。
- 读取事件参数。
- 导出 / 下载数据。
- 复制完整页面数据。
- 自动风险定性或自动处置。

## 7. observation schema

标准 schema 见：

`computer_use_poc/frontend_activity_profile_observation_schema_v2_5_2.md`

## 8. 与其他平台关系

| 平台 | 关系 |
| --- | --- |
| 用户登录统一日志 | 用于补登录链路、token、登录方式、接口调用；前端活跃画像不能替代它 |
| 设备 SDK / 设备基建 | 用于补设备风险、SDK 采集、root / hook / 多开等设备侧线索 |
| 档案中心 | 用于账号状态、长期画像、审核 / 打标 / 用户分析补充 |
| DataAgent / Hive | 用于离线大范围取数分析，不替代在线埋点页面只读观察 |
| 后端业务日志 | 用于确认具体业务动作是否发生 |

## 9. 下一步

P0：

- 真实 browser 只读 POC：验证 URL 直联、页面加载、红框区域字段识别。
- 验证 `appName=KUAISHOU / NEBULA` 的 userId 查询。
- 验证 `filtersType=deviceId` 查询。
- 输出第一版真实 observation。

P1：

- 验证截图留存策略。
- 验证字段缺失 / 无结果 / 权限阻断行为。
- 验证 appName 扩展能力。

P2：

- 如后续需要，再单独设计行为序列手脚；不得混入本 POC。

## 10. 边界

- 不修改核心 Skill。
- 不更新 final release package。
- 不改变 DataAgent / Hive 边界。
- 不引入自动处置。
- 不引入自动风险定性。
