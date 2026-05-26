# Real Name Feature Service Partial Contract v1

## 1. POC 定位

本文档沉淀 `EB_USER_REAL_NAME_VERILY__1` 最小复测结果。

定位：

- 这是 `EB_USER_REAL_NAME_VERILY__1` 数据服务 partial contract。
- 不是完整实名画像能力。
- 不是本人 / 盗号判断能力。
- 不注册 runtime 可执行能力。

## 2. 接口调用方式

入口：

```text
POST /v2/rest/testCase/run
```

body 模板：

```json
{
  "foreignKey": "EB_USER_REAL_NAME_VERILY__1",
  "caseType": "FEATURE",
  "eventType": "TEST_TOOL_EVENT_TYPE",
  "input": {
    "sourceId": "<user_id>",
    "activityName": "MERCHANT_NEWSHOP_OPEN_AWARD"
  }
}
```

关键参数：

- `foreignKey=EB_USER_REAL_NAME_VERILY__1`
- `caseType=FEATURE`
- `eventType=TEST_TOOL_EVENT_TYPE`
- `input.sourceId`
- `input.activityName`

## 3. 参数映射

| 参数 | 语义 | 说明 |
|---|---|---|
| `sourceId` | `userId` | sourceId 映射为用户 ID |
| `activityName` | call_condition | 调用条件字段，不是 sid |
| `sid` | feature config auto-filled constant | `sid=kuaishou.api` 由特征配置自动填充 |
| `required_activityName_value` | `MERCHANT_NEWSHOP_OPEN_AWARD` | 当前最小复测可用值 |

复测结论：

- `activityName=kuaishou.api` 会返回 null / timeout。
- `sourceId=218368298 + activityName=MERCHANT_NEWSHOP_OPEN_AWARD` 返回空 dict。
- `sourceId=62950989 + activityName=MERCHANT_NEWSHOP_OPEN_AWARD` 返回 `idNo`。
- 空 dict 不能证明用户未实名。

## 4. 字段返回状态

| 字段 | 状态 | 说明 |
|---|---|---|
| `idNo` | actually_returned | 当前实际返回字段 |
| `age` | schema_only_not_output | schema 存在但未实际输出 |
| `birthday` | schema_only_not_output | schema 存在但未实际输出 |
| `gender` | schema_only_not_output | schema 存在但未实际输出 |
| `name` | schema_only_not_output | schema 存在但未实际输出 |

当前实际只输出 `idNo`。如需全部 5 字段，需改 feature 出参配置。

## 5. 脱敏输出 schema

```yaml
identity_summary_observation:
  query_status:
  source_id:
  real_name_verified:
  id_no_present:
  name_present:
  id_region:
    province:
    city_level_available:
    raw_id_no_output: false
    raw_id_prefix_output: false
  age_bucket:
  gender:
  sensitive_fields_redacted: true
  field_limitations:
    age_raw_output: false
    birthday_raw_output: false
    gender_raw_output: false
    name_raw_output: false
```

输出策略：

- 不输出姓名。
- 不输出身份证号。
- 不输出身份证前 6 位。
- 不输出完整生日。
- 不输出手机号。
- 不输出完整 IP。
- 年龄只输出年龄段。
- 性别只输出摘要。
- 可从 `idNo` 内部解析省份、城市级可用性、年龄段、性别摘要，但只能输出派生摘要，不输出原值或前缀。

## 6. 红线规则

- 不输出姓名。
- 不输出身份证号。
- 不输出身份证前 6 位。
- 不输出完整生日。
- 不输出手机号。
- 不输出完整 IP。
- 年龄只输出年龄段。
- 性别只输出摘要。
- 身份信息不能单独定性本人 / 盗号 / 黑产。

## 7. 当前限制

- `sourceId=218368298` 返回空 dict，不能证明用户未实名。
- 该服务可能只覆盖电商实名认证。
- 当前只有 `idNo` 实际返回。
- `age` / `birthday` / `gender` / `name` 仅 schema 存在但未输出。
- 如需全部 5 字段，需改 feature 出参配置。
- 该服务所属子域临时待下线，生产可用性需确认。
- 不注册 identity runtime 能力；后续如要使用，必须先完成权限、稳定性、脱敏输出和业务适用范围评审。
