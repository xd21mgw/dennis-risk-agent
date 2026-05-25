# Account Security Runtime Summary v1

## 1. 定位

本 summary 支撑半开放 runtime 下的账号安全 / ATO / 盗号判断。重点是避免把批量统计直接解释成攻击本质。

## 2. ATO 攻击类型识别

### 2.1 撞库 ATO

主线特征：

- 密码尝试、登录失败、CAPTCHA 或验证挑战密集。
- 同 IP / 代理 / 设备对多账号做凭证测试。
- 成功登录后出现敏感动作、资料修改、私信、发布、支付等后置行为。

判断边界：

- `password fail + CAPTCHA + kick_out` 只能提示账号安全异常，不能单独定性撞库。
- 必须看到密码尝试是攻击主线，而不是改密 / 密码验证环节的后置现象。

### 2.2 一键登录 / 三方授权 / 鸿蒙一键登录 ATO

候选触发信号：

- 出现 `HARMONY_` 设备 ID 或鸿蒙设备前缀。
- token issued / token 下发成功。
- 多账号登录成功。
- 同一 IP 集中登录多个用户。
- token revoke / kick out。
- 后续小米 / Android 设备改密或密码验证失败。
- 用户原设备与新 HARMONY 设备明显不一致。

判断：

- 这类 case 应优先识别为“一键登录 / 三方授权接管 / 鸿蒙一键登录 ATO”候选。
- 不应直接归为撞库。
- 大量 password fail / CAPTCHA 可能来自改密环节，不一定是撞库尝试。

## 3. 批量 ATO 逐条时序抽样

批量 ATO case 中出现以下任一信号时，不能只看 totalCount / kick_out 次数 / fail 次数：

- kick_out 密集。
- password fail / CAPTCHA 密集。
- 多设备切换。
- 同 IP 集中。
- 三方登录 / 一键登录 / OAuth / HARMONY 相关字段。

必须抽取 3-5 个代表用户做 timeline：

- 正常登录设备。
- 异常登录设备。
- 登录方式。
- token issued。
- token revoke / kick out。
- password verify / change password。
- IP。
- device model / did prefix。
- event order。

输出必须包含“撞库 ATO vs 一键登录 ATO”的替代解释对比。

## 4. 禁止结论跳跃

禁止：

- 只凭 `kick_out + password fail + CAPTCHA` 直接输出“撞库 ATO”。
- 只看 totalCount 汇总，不抽样逐条时序。
- 把改密阶段的 password fail / CAPTCHA 当作撞库主线证据。

推荐表述：

```text
当前批量统计显示账号安全异常，但不能直接定性撞库。日志中出现 HARMONY_ 设备、同 IP token 下发、token revoke / kick out，以及后续小米 / Android 改密尝试，更应优先验证一键登录 / 三方授权接管 / 鸿蒙一键登录 ATO 链路。
```

## 5. 单案 evidence card 证据类型分离

单个 user_id / case 的 ATO 研判必须区分：

- `raw_evidence`: 平台日志、发布审计、登录日志、设备画像、策略命中等事实。
- `behavior_event`: 违规内容发布、改密、换绑、私信、关注、支付等动作发生事实。
- `user_claim`: 用户声称被盗、非本人操作、客服备注。
- `inference`: 基于多源证据的解释。
- `hypothesis`: 需要补证的候选路径。
- `missing_evidence`: 未查到、未查询、blocked、timeout、超窗的关键证据。

边界：

- 用户反馈账号被盗只能作为 `user_claim` / weak signal。
- 违规内容发布只能证明违规发生，不能证明被盗。
- 钓鱼页访问、OAuth 授权、前端行为、token 链路、发布审计如果未实际查到，必须写入 `missing_evidence`，不得写“已确认”。
- 发布设备与日常设备不一致通常是 medium evidence，需要登录、设备、行为或发布审计补证；不能单独强判盗号。
- 每条 strong / medium / weak / counter evidence 都必须带 `evidence_type` 和 `strength`。

单案 evidence card 必须包含：

- `conclusion`
- `confidence`
- `strong_evidence`
- `medium_evidence`
- `weak_evidence`
- `counter_evidence`
- `missing_evidence`
- `completed_sources`
- `blocked_or_timeout_sources`
- `source_quality`
- `next_action`

平台 blocked、timeout、browser loop 时，输出 partial evidence card，不裸 timeout。
