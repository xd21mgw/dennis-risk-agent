# BC-HARMONY-ATO-001 Bad Case Regression Run v1

## 1. Bad Case 背景

一批 14 个用户疑似 ATO。Agent 第一轮只看 totalCount、kick_out 次数、password fail / CAPTCHA 次数，把整波攻击定性为“撞库 ATO”。

用户补充线索后，Agent 二次逐条细查日志，发现真实链路更像“华为鸿蒙一键登录 ATO”：

- `HARMONY_` 设备一键授权登录。
- 同源 IP 集中。
- token issued / token 下发成功。
- token revoke / kick out。
- 后续小米 / Android 设备改密尝试或密码验证失败。

## 2. 问题本质

批量 ATO 分析不能只看统计汇总，不能从 `kick_out + password fail + CAPTCHA` 直接跳到撞库结论。

原因：

- kick_out 是账号安全后置状态，不是攻击入口。
- password fail / CAPTCHA 可能来自改密或密码验证环节。
- totalCount 只能说明事件量，不能说明事件顺序和攻击主线。
- HARMONY / oneKey / OAuth / token issued 可能代表另一条账号接管路径。

## 3. 新增攻击类型识别规则

### 鸿蒙一键登录 ATO pattern

触发信号：

- 出现 `HARMONY_` 设备 ID。
- token issued / token 下发成功。
- 多账号登录成功。
- 同一 IP 集中登录多个用户。
- token revoke / kick out。
- 后续小米 / Android 设备改密或密码验证失败。
- 用户原设备与新 HARMONY 设备明显不一致。

判断：

- 优先标记为“一键登录 / 三方授权接管 / 鸿蒙一键登录 ATO”候选。
- 不直接归为撞库。
- 大量 password fail / CAPTCHA 可能来自改密环节。

## 4. 逐条时序抽样规则

批量 ATO 中出现以下任一信号，必须抽取 3-5 个代表用户做 timeline：

- kick_out 密集。
- password fail / CAPTCHA 密集。
- 多设备切换。
- 同 IP 集中。
- 三方登录 / 一键登录 / OAuth / HARMONY 相关字段。

timeline 字段：

- 正常登录设备。
- 异常登录设备。
- 登录方式。
- token issued。
- token revoke / kick out。
- password verify / change password。
- IP。
- device model / did prefix。
- event order。

## 5. 撞库 ATO vs 鸿蒙一键登录 ATO

| 类型 | 主线 | 关键证据 | 易误判点 |
|---|---|---|---|
| 撞库 ATO | 密码尝试、失败爆发、CAPTCHA、成功登录 | 同 IP/代理多账号密码试探，失败后成功登录，成功后敏感动作 | 不能只凭 kick_out 或改密失败定性 |
| 一键登录 / 鸿蒙 ATO | 三方授权 / oneKey / OAuth / HARMONY token issued、设备切换、改密、token revoke | HARMONY_ 设备、token 下发成功、同源 IP 多账号登录、后续小米/Android 改密或密码验证失败 | 改密环节的 password fail / CAPTCHA 容易被误读成撞库 |

## 6. 修改沉淀

- 新增 `account_security_runtime_summary_v1.md`。
- 更新 `general_runtime_summary_manifest_v1.md`。
- 更新 `account_security_expert_skill.md`。
- 更新 `credential_stuffing_ato_skill.md`。
- 更新 `answer_experience_templates.md`。
- 更新 `scene_to_capability_routing.md`。
- 更新 `runtime_validation_cases_v1.yaml`。
- 更新 `smoke_tests.md`。

## 7. 回归期望

输入：

```text
一批用户都有 kick_out、密码失败、CAPTCHA，同时部分日志出现 HARMONY_ 设备、同一 IP token 下发、随后小米设备改密。请判断是否被盗以及攻击路径。
```

期望：

- 不直接定性撞库。
- 先提示存在“一键登录 / 鸿蒙授权接管”候选。
- 抽样逐条时序。
- 输出“撞库 vs 鸿蒙一键登录 ATO”的替代解释对比。
- 给出需要补查的字段：登录方式、OAuth/oneKey 授权、token issued、改密记录、设备型号、IP 聚集。

## 8. 本轮边界

- 未访问真实平台。
- 未调用 DataAgent。
- 未执行真实查询。
- 未修改 auth state。
- 未提交 git。
