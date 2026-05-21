# Black Market Account Matrix Case Schema v1

## 1. 定位

本 schema 用于黑产账号矩阵 / 导流互动 / 互粉互动 / 养号账号池的 batch case analysis。

它不是 ATO：

- ATO 主线是账号控制权异常，例如 token / OAuth / 登录态异常、改密、换绑、异设备登录。
- 本能力关注账号矩阵、资料模板化、导流互动、互粉互动、养号账号池和黑产账号集群归因。
- 如果只看到简介、昵称、adminaction、注册天数、UID 号段聚集等矩阵特征，不应写成 ATO。

边界：

- 不调用真实 DataAgent。
- 不访问真实内部平台。
- 不执行真实查询。
- 不自动上线策略。
- 不输出微信号、uid、device、IP 等敏感明文。

## 2. 标准 Case 字段

| 字段 | 类型 | 是否必填 | 含义 | 边界 |
|---|---|---:|---|---|
| `case_id` | string | 是 | 样本唯一 ID | 管理 ID，不代表风险结论 |
| `account_ref` | string | 是 | 脱敏账号引用 | 不写真实 UID 明文 |
| `uid_segment` | string | 否 | 脱敏 UID 号段 | 只保留聚集特征 |
| `nickname_pattern` | string | 否 | 昵称模板摘要 | 不写可识别原昵称 |
| `intro_pattern` | string | 否 | 简介模板摘要 | 联系方式必须 redacted |
| `adminaction_code` | string | 否 | adminaction 摘要 | 可保留 code，不代表最终风险 |
| `registration_age_days` | number/string | 否 | 注册天数或区间 | 用于 cohort 聚合 |
| `sample_date` | date/string | 否 | 样本日期 | 可按天保留 |
| `observed_behavior` | string/list | 否 | 已知行为摘要，如互动、互粉、导流 | 只写行为类型 |
| `available_evidence` | string/list | 否 | 当前已有证据摘要 | 不伪造查询结果 |
| `missing_evidence` | string/list | 否 | 仍缺的行为链路、设备/IP等 | 用于补证 |
| `initial_cluster_hint` | string | 否 | 初始聚类线索 | 只是 hint |
| `current_status` | string | 是 | standardized / missing_evidence / pending_review | 不代表处置状态 |
| `manual_label` | string | 否 | 人工标签 | 不替代证据 |
| `confidence` | string | 否 | low / medium / high / unknown | 样本级置信 |
| `notes` | string | 否 | 脱敏备注 | 不写敏感明文 |

## 3. YAML 示例

```yaml
black_market_account_matrix_case:
  case_id:
  account_ref:
  uid_segment:
  nickname_pattern:
  intro_pattern:
  adminaction_code:
  registration_age_days:
  sample_date:
  observed_behavior:
    - behavior_item
  available_evidence:
    - evidence_item
  missing_evidence:
    - missing_item
  initial_cluster_hint:
  current_status:
  manual_label:
  confidence:
  notes:
```

## 4. 证据口径

强证据倾向：

- 简介高度一致且联系方式归一化后同源。
- adminaction 一致且与黑产治理动作或策略命中有关。
- 昵称模板化、UID 号段、注册天数、日期窗口同时聚集。
- 多账号存在行为链路补证，如互粉、互评、私信、导流路径、共同设备/IP。

中证据倾向：

- 单一维度聚集，例如同简介或同昵称模板。
- 注册天数集中，但缺行为链路。
- UID 多号段聚集，但缺账号间关系。

弱证据倾向：

- 单个账号资料可疑。
- 只有人工备注或样本来源说明。
- 只有 adminaction code，缺上下文。

反证：

- 简介模板是正常活动模板或官方运营模板。
- 昵称相似但行为自然、设备/IP分散、无导流行为。
- adminaction 与导流互动无关。
- 注册天数集中来自正常活动拉新或平台批量导入。

## 5. 不适用场景

- ATO / 盗号控制权异常。
- 单用户登录失败原因。
- 纯设备 root / hook / frida 风险。
- 纯内容违规，无账号矩阵或导流互动特征。
- 需要真实全量 Hive 统计但未授权的批量分析。
