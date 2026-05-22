# Device SDK Foundation Internal Agent Playbook v2.5.0

## 1. 当前能力范围

本 playbook 面向 Dennis 子 Agent / browser computer use 执行。

当前阶段只支持设计：

- `source_entry_resolution`
- `browser_auth_preflight`
- saved state 复用检查
- 单 browser session 串行检查

当前不支持：

- 真实页面执行。
- 多平台联合。
- 多入参批量查询。
- 二级入口验证。
- 自动风险定性。
- 自动处置。

## 2. 平台定位

设备 SDK / 设备基建平台是 Dennis Agent 的设备侧补证手脚。

主要用于补充：

- deviceId / did 设备画像。
- SDK 采集状态。
- 设备风险标签。
- 设备一致性。
- root / hook / 多开 / 模拟器 / 改机 / 自动化环境等设备侧线索。
- 设备与账号 / IP / app / 登录行为之间的补证关系。

## 3. 执行前置顺序

必须按 v2.4.9 前置检查顺序执行：

```text
source_entry_resolution
→ browser_auth_preflight
→ saved_state_reuse_check
→ single_browser_session_check
→ 页面字段探索
```

在本阶段，若 `source_entry_resolution` 未通过，不进入 `browser_auth_preflight` 之后的页面探索。

## 4. source_entry_resolution

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

- `expected_entry_url` 未知时，必须返回 `source_entry_missing`。
- 不凭记忆猜 URL。
- 不从首页菜单随意探索作为正式路径。
- 不把入口缺失解释为设备无数据、平台不可用或权限无数据。

## 5. browser_auth_preflight

标准输出：

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

执行规则：

- `current_url` 跳转登录域时，返回 `redirected_to_login=true` 和 `auth_blocked`。
- `page_accessible=true` 只说明页面可打开，不说明设备有数据。
- `device_id_match_if_applicable=true` 只说明目标对象匹配，不说明风险成立。

## 6. saved state reuse check

必须检查：

- saved state 是否存在。
- saved state 是否成功加载。
- direct URL 是否打开成功。
- 是否跳转 login。
- 是否进入目标 source。
- 是否匹配目标 deviceId / did。

失败时只能输出：

- `auth_blocked`
- `saved_state_missing`
- `saved_state_expired`

禁止输出：

- 设备无数据。
- 设备无风险。
- 平台不可用。

## 7. single browser session check

要求：

- 默认 `single_browser_session=true`。
- 同一时间只允许一个 `agent-browser` 操作内部平台页面。
- 如果已有任务运行，应等待或停止。
- 多 session 并发导致的跳转异常不得解释为页面不可用、Tab 不可访问、设备无数据或权限阻断。

## 8. 只读安全规则

允许：

- 打开已验证入口。
- 输入单个 deviceId / did。
- 点击查询。
- 切换只读 Tab。
- 读取字段名、字段值和派生特征。

禁止：

- 点击写操作。
- 修改设备状态。
- 导出敏感数据。
- 复制完整 JSON。
- 输出 token / session / ticket / authorization / cookie 等认证凭证明文。
- 自动处罚、封禁、冻结、解封或策略上线。

字段保留：

- deviceId / did
- sdkVersion
- appVersion
- riskTag
- deviceModel
- osVersion
- ip
- region
- root / hook / emulator / multi-open / automation / tamper 等风险字段

凭证明文字段：

- token / session / ticket / authorization / cookie 等如出现，只能输出 `present_redacted`。

## 9. observation schema 初稿

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

## 10. 解释边界

- 设备风险标签是风险线索，不是最终风险定性。
- 设备字段不可见不等于字段不存在。
- 设备无结果不等于设备无风险。
- 权限阻断不等于设备无数据。
- 设备聚集不直接等同群控。
- 设备异常不直接等同协议上号。
- 需要结合用户登录统一日志、档案中心、行为细查或 DataAgent / Hive 补证。

## 11. 标准执行 Prompt 模板

```text
请按 v2.4.9 browser auth preflight 规范，为 device_sdk_foundation 做只读前置检查。

目标：
只完成 source_entry_resolution 和 browser_auth_preflight，不做真实字段读取，不做风险定性。

要求：
1. 先读取 device_sdk_foundation playbook。
2. 输出 source_entry_resolution。
3. 如果入口未知，返回 source_entry_missing，不要猜 URL。
4. 如入口已确认，再输出 browser_auth_preflight。
5. 如果跳转登录或 saved state 不可用，返回 auth_blocked / saved_state_missing / saved_state_expired。
6. 不把认证阻断、权限阻断、入口缺失解释为设备无数据或设备无风险。
7. 不点击写操作，不导出，不复制完整 JSON，不输出凭证明文。
```

## 12. 边界

- 不修改核心 Skill。
- 不更新 final release package。
- 不改变 DataAgent / Hive 边界。
- 不引入自动处置。
- 不引入自动风险定性。
