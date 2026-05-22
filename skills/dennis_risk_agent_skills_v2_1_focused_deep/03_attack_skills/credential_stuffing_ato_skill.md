# Credential Stuffing / ATO Skill：撞库与账号接管 Skill v2.1

## 认知

撞库是泄漏凭证被批量测试，ATO 是账号被接管后的状态。ATO 可能来自撞库、钓鱼、token 泄露、欺诈验证或设备接管。

不要把所有 ATO 都归因成撞库。批量 case 中如果只看到 `kick_out`、密码失败、CAPTCHA 或 totalCount 汇总，不能直接判断为撞库；这些也可能是改密 / 密码验证环节的后置现象。

## 撞库 ATO vs 一键登录 / 鸿蒙授权接管

| 类型 | 主线 | 关键识别点 | 判断边界 |
|---|---|---|---|
| 撞库 ATO | 密码尝试、失败爆发、CAPTCHA、成功登录 | 同 IP/代理多账号密码试探，失败后成功，成功后行为突变 | 必须证明密码试探是主线 |
| 一键登录 / 鸿蒙 ATO | HARMONY / oneKey / OAuth token issued 后接管 | `HARMONY_` 设备、同 IP 多账号 token 下发、token revoke / kick_out、后续小米/Android 改密或密码验证失败 | password fail / CAPTCHA 可能来自改密环节，不等于撞库 |

批量 ATO 出现 `HARMONY_` 设备、同源 IP、多账号 token issued、token revoke / kick out、后续小米 / Android 设备改密或密码验证失败时，应优先标记为“一键登录 / 三方授权接管 / 鸿蒙一键登录 ATO”候选，并抽样做逐条 timeline。

## 证据

登录失败/成功序列、异地 IP、同 IP 多账号尝试、成功后行为突变、设备环境不一致、MFA/验证异常、下游私信/支付/导流扩散。

批量分析必须抽取 3-5 个代表用户做逐条时序，字段包括正常登录设备、异常登录设备、登录方式、token issued、token revoke / kick out、password verify / change password、IP、device model / did prefix、event order。

## 治理

速率限制、条件 MFA/Step-up、泄漏凭证库、异常登录提醒、风险 token 踢出、下游高风险动作二次验证、用户教育、快速找回。

## 指标

撞库尝试量、成功率、ATO 客诉、高风险登录、验证通过率、找回成功率、误伤率。
