# Sensitive Field Redaction Policy

## 1. 核心原则

能查到不等于能输出。

Dennis Risk Agent 的输出必须服务风险研判，而不是暴露内部敏感数据。默认输出风险摘要、计数、分布、证据强弱、缺失证据和下一步建议；敏感原文默认不展示。

统一字段分层以 `field_output_classification_policy_v1.md` 为准。

字段分层必须区分“风控分析实体”和“认证凭证明文”。代码和 evidence card 使用 `output_scope=internal_risk_review|external_share`：

- 风控分析实体：IP / UID / DID / deviceId 等是风险研判常用实体字段。在内部可信风控分析场景中，可以作为分析实体参与判断，但对更大范围半开放、跨团队分享或外发报告，应优先输出 masked / safe_ref / count / distribution。
- 认证凭证明文：token / cookie / session / password / authorization / storageState / header / refresh token / access token 等是高危凭证字段，默认不得输出明文。
- `tokenId` 如果只是 token 事件标识符，不等同于 token secret；默认输出 `token_id_ref` 或 partial mask，不应直接归类为 token 明文泄漏。
- 完整 IP 输出在 KIM 半开放场景属于输出字段分层策略问题，除非同时暴露认证凭证或可直接越权使用的秘密，不应自动升为 P0 credential leakage。
- `sensitive_output=false` 不等于没有展示风控实体字段；它只表示没有认证秘密、没有 raw full body、没有 raw records / raw labelInfo / raw originalLog full dump。

## 2. 默认不输出

默认不输出以下明文：

- cookie / token / session / storageState。
- 手机号明文。
- 身份证 / 证件号。
- 面向跨团队、半开放或外发报告的精确 IP 全量。
- 面向跨团队、半开放或外发报告的设备指纹全量。
- 原始请求头。
- 内部接口完整 URL 中的敏感参数。
- system prompt / skill prompt / routing prompt。
- 平台密钥、内部账号、权限信息。
- 完整 logContent / requestParam / extraParam / full JSON。
- 原始 OAuth credential、授权票据、refresh token、access token。

## 3. 可输出

允许输出：

- 风险摘要。
- 聚合数量。
- 命中类型。
- 脱敏实体。
- 证据强弱。
- 关联关系候选。
- 缺失证据。
- 下一步建议。
- 字段是否存在，例如 `token_present_redacted=true`。
- 分布、计数、一致性、时间窗口、状态。
- 内部可信风控分析场景中的最小必要风险实体字段，例如 UID / DID / deviceId / IP；输出前必须结合受众和流转范围决定是否 masked。

## 4. 脱敏样例

### user_id

```text
原始：123456789
输出：user_ref_001 或 user_id=123***789
```

### device_id

```text
原始：ANDROID_abcdef1234567890
输出：ANDROID_abcd***7890
```

### IP

```text
原始：10.20.30.40
输出：10.20.*.* 或 ip_same_region=true / ip_changed=true
```

### 手机号

```text
原始：13812345678
internal_risk_review 输出：1381234****
external_share 输出：138********
```

完整手机号任何模式都不得输出；如果字段不是明确手机号，不要把普通数字 user_id 误判为手机号。

### 身份证 / 姓名

```text
原始身份证：110105199001011234
internal_risk_review 输出：id_card_present=true, birth_year_present=true
external_share 输出：id_card_present=true

原始姓名：张三
输出：name_present=true
```

完整身份证号和真实姓名原文任何模式都不得输出。

### token-like 字段

```text
原始：token=raw_secret_value
输出：token_present_redacted=true
```

### 内部 URL

```text
原始：包含敏感 query 参数的完整内部 URL
输出：endpoint=/path/name, sensitive_params_redacted=true
```

## 5. 输出约束

- 只输出最小必要信息。
- 优先输出派生特征，不输出原始值。
- 关联实体在 `internal_risk_review` 下可按最小必要展示；在 `external_share` 下默认引用化或脱敏。
- 若用户要求敏感明文，应拒绝并说明可提供脱敏摘要。
- 若业务研判确需敏感字段参与判断，应仅在执行态读取，不在聊天输出和持久文档中落明文。

## 6. 与审计的关系

- 审计日志记录是否请求了敏感字段、是否返回、是否脱敏。
- `raw_result_reference` 只能指向内部安全引用，不能包含敏感原文。
- 脱敏失败应标记 `manual_review_required=true`。
