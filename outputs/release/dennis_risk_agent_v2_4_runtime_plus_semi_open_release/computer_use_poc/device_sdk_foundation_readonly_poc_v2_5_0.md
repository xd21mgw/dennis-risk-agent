# Device SDK Foundation Readonly POC v2.5.0

## 1. 阶段定位

v2.5.0 启动 Dennis Agent 5 — 设备 SDK 基建手脚。

本阶段只做 `source_entry_resolution` + `browser_auth_preflight` 设计，不做真实页面执行，不做字段验证，不做多平台联动，不做风险定性。

设备 SDK / 设备基建平台作为 Dennis Agent 的设备侧补证手脚，主要用于补充：

- `deviceId` / `did` 设备画像。
- SDK 采集状态。
- 设备风险标签。
- 设备一致性。
- root / hook / 多开 / 模拟器 / 改机 / 自动化环境等设备侧线索。
- 设备与账号 / IP / app / 登录行为之间的补证关系。

当前状态：

```yaml
source_name: device_sdk_foundation
validation_status: design_pending_validation
real_page_execution: false
release_status: not_in_release_package
```

## 2. 能力边界

### 2.1 能补什么

- 设备基础画像：设备类型、型号、系统版本、SDK 版本、App 版本。
- 设备风险画像：root / hook / 模拟器 / 多开 / 自动化 / 改机 / tamper 等风险线索。
- 设备一致性：同一设备在账号、IP、App、登录行为上的一致性或漂移。
- 设备关系摘要：相关账号、相关 IP、相关 App、相关登录事件的只读观察。

### 2.2 不替代什么

设备 SDK / 设备基建平台不替代：

- 用户登录统一日志。
- 档案中心。
- DataAgent / Hive。
- 埋点 / 行为细查。
- 设备攻防深度分析。
- 自动风险定性 / 自动处置。

解释规则：

- 设备风险标签是设备侧线索，不是账号风险最终结论。
- 设备字段缺失不等于设备无风险。
- 权限阻断不等于设备无数据。
- 登录态阻断不等于设备不存在。

## 3. source_entry_resolution 设计

必须按 v2.4.9 `browser_auth_preflight_checklist_v2_4_9.md` 执行。

标准输出：

```yaml
source_entry_resolution:
  source_name: device_sdk_foundation
  expected_entry_url:
  entry_url_source:
  validated_execution_path_found:
  selector_or_playbook_found:
  blocker:
  next_action:
```

当前规则：

- 如果入口未知，必须标记 `source_entry_missing`。
- 不允许凭记忆猜 URL。
- 不允许从首页菜单随意探索作为正式路径。
- `source_entry_missing` 不能解释为设备无数据、设备无风险或平台不可用。

当前状态：

```yaml
source_entry_resolution_status: pending_validation
expected_entry_url: unknown
entry_url_source: missing
validated_execution_path_found: false
selector_or_playbook_found: true
blocker: source_entry_missing_until_entry_confirmed
next_action: 补充可信入口 URL 和执行路径后再做 browser_auth_preflight
```

## 4. browser_auth_preflight 设计

新增标准 schema：

```yaml
browser_auth_preflight:
  source_name: device_sdk_foundation
  target_url:
  saved_state_name:
  saved_state_loaded:
  redirected_to_login:
  current_url:
  page_accessible:
  expected_domain:
  actual_domain:
  device_id_match_if_applicable:
  blocker:
  next_action:
```

解释规则：

- `saved_state_loaded=true` 不等于页面可访问。
- `page_accessible=true` 不等于设备有数据。
- `device_id_match_if_applicable=true` 只说明页面目标对象与查询设备一致，不代表设备风险成立。
- `redirected_to_login=true` 时必须停止，不继续字段探索。

## 5. 只读安全边界

允许：

- 打开已验证入口 URL。
- 输入单个 `deviceId` / `did`。
- 点击查询按钮。
- 切换只读 Tab。
- 读取字段名、字段值和派生特征。
- 记录设备风险标签和关系摘要。

禁止：

- 点击写操作。
- 修改设备状态。
- 导出敏感数据。
- 复制完整 JSON。
- 输出 token / session / ticket / authorization / cookie 等认证凭证明文。
- 自动处罚、封禁、冻结、解封或上线策略。

字段策略：

- `deviceId` / `did` / `sdkVersion` / `appVersion` / `riskTag` / `deviceModel` / `osVersion` / `ip` / `region` 等风控证据字段可以保留。
- token / session / ticket / authorization / cookie 等认证凭证明文只能记录 `present_redacted`。

## 6. observation schema 初稿

```yaml
device_sdk_foundation_observation:
  query:
    input_device_id:
    query_type:
    time_range:
  page_access:
    page_accessible:
    auth_required:
    permission_blocked:
    redirected_to_login:
  device_basic_info:
    device_id:
    did:
    device_type:
    device_model:
    os:
    os_version:
    app_version:
    sdk_version:
  device_risk_profile:
    risk_tags:
    risk_level:
    root_or_jailbreak:
    hook_detected:
    emulator_detected:
    multi_open_detected:
    automation_detected:
    tamper_detected:
  relation_summary:
    related_user_ids:
    related_ips:
    related_apps:
    related_login_events:
  field_visibility:
    visible_fields:
    missing_fields:
  limitations:
  readonly_safety_check:
```

字段解释：

- `device_basic_info`：设备基础信息，不代表风险。
- `device_risk_profile`：设备侧风险线索，需结合登录日志、档案中心、行为链路验证。
- `relation_summary`：只读关系摘要，不直接等同群控或账号接管。
- `field_visibility.missing_fields`：字段未出现时需区分 `field_not_visible` / `permission_blocked` / `query_no_result`。

## 7. guardrail

必须引用 v2.4.9：

```text
source_entry_resolution
→ browser_auth_preflight
→ saved_state_reuse_check
→ single_browser_session_check
→ 页面字段探索
```

关键解释：

- 登录态阻断不能解释为设备无数据。
- 权限阻断不能解释为设备无风险。
- 未看到字段不能解释为字段不存在。
- 需要区分：
  - `field_not_visible`
  - `permission_blocked`
  - `query_no_result`
  - `selector_scope_unknown`
- 设备标签不能单独作为最终风险定性。
- 设备关系聚集不能直接等同群控。

## 8. smoke tests

以下测试当前均为 pending validation：

| 测试项 | 预期 |
| --- | --- |
| source entry resolution | 不猜 URL；入口缺失时返回 `source_entry_missing` |
| browser auth preflight | 输出标准 `browser_auth_preflight` |
| saved state reuse | state 可用时进入目标 source；失败时返回 blocker |
| direct deviceId query | 单设备 ID 查询路径可用 |
| result table visibility | 可识别结果表或详情页模块 |
| device basic info visibility | 可见 deviceId / did / model / os / app / sdk 字段 |
| device risk tag visibility | 可见风险标签或明确无权限 / 无字段 |
| relation tab visibility | 可见账号 / IP / App / 登录关系摘要 |
| no result behavior | 无结果不解释为设备无风险 |
| permission blocked behavior | 权限阻断不解释为设备无数据 |
| pagination / tab behavior | 分页和 Tab 切换遵守 SPA guardrail |
| readonly safety | 不写、不导出、不复制完整 JSON、不输出凭证明文 |

## 9. 下一步

P0：

- 补充可信入口 URL。
- 定义设备平台 saved state 名称。
- 完成 `source_entry_resolution` 实跑。
- 完成 `browser_auth_preflight` 实跑。

P1：

- 验证单 `deviceId` / `did` 查询。
- 验证设备基础信息和风险标签字段可见性。
- 验证 no_result / permission_blocked 行为。

P2：

- 设计设备平台 relation observation。
- 再决定是否进入 multi-source e2e。

## 10. 边界

- 不修改核心 Skill。
- 不更新 final release package。
- 不改变 DataAgent / Hive 边界。
- 不引入自动处置。
- 不引入自动风险定性。
