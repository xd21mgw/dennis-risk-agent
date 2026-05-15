# ATO Batch Case Import Rules v1

## 1. 目标

定义从申诉表、人工备注表、复核表或导出样本中批量导入 ATO case 的准入、清洗、去重和状态初始化规则。

本文件只定义导入规则，不调用 Data Agent，不写真实表名、字段名、SQL 或 API。

## 2. 支持来源

- 盗号申诉样本。
- 内容违规封禁后用户申诉“非本人操作”的样本。
- 人工复核标注样本。
- 风险类型为密码泄露、钓鱼、扫码、OAuth、短信泄露、token/session 异常的样本。
- Data Agent-only ATO pilot 已完成样本。

不支持：
- HRBI 或其他敏感人事数据。
- 无 user_id 且无可替代实体标识的样本。
- 无时间窗口且无法从申诉时间 / 异常时间推导窗口的样本。

## 3. 最小导入字段

必须具备：

- `user_id`
- `sample_date`
- `suspicious_event_time` 或可推导的异常日期
- `business_scene`
- `user_claim_summary` 或 `manual_note`

建议具备：

- `manual_label`
- `risk_category`
- `risk_subcategory`
- `target_api_or_action`
- `source_row_id`

缺 `user_id` 或可用时间窗口时，导入但标记：

```text
minimum_input_status = blocked_by_missing_input
execution_status = blocked_by_missing_input
conclusion_support = not_evaluated
```

## 4. case_id 生成规则

优先保留已有 case_id，例如：

```text
ATO_CASE_001_PASSWORD_KPN_RESWEEP
```

批量新增时建议格式：

```text
ATO_BATCH_<YYYYMM>_<SEQ>_<RISK_HINT>
```

示例：

```text
ATO_BATCH_202605_001_PASSWORD
ATO_BATCH_202605_002_QR_OAUTH
ATO_BATCH_202605_003_INSUFFICIENT
```

注意：`RISK_HINT` 只是线索，不代表结论。

## 5. 时间窗口推导

- `suspicious_event_time` 精确到小时：前后各 24 小时。
- 只精确到日期：前后各 1 天。
- 用户描述、人工备注和样本日期存在差异：覆盖可疑时间前后 2-3 天。
- 第一轮取证窗口原则上不超过 7 天。
- 如果 Data Agent 反馈窗口不足，再由 Dennis Agent 输出下一轮窗口扩展建议。

## 6. 人工备注处理

人工备注只能作为 golden hint：

- “已回扫”必须由数据或回扫记录验证。
- “KPN / 钓鱼域名 / 山东德州 / 地推”等来源信息必须由数据验证。
- 如果数据发现与人工备注不一致，以数据发现为准，同时记录情报偏差。
- 人工备注不得进入 strong_evidence。

## 7. 去重规则

优先用以下组合去重：

```text
user_id + suspicious_event_time + source_row_id
```

如果缺 source_row_id，则使用：

```text
user_id + sample_date + risk_category + risk_subcategory
```

同一用户多次申诉但异常时间不同，可以保留为多个 case。

## 8. 导入后初始化

成功导入后初始化：

```yaml
execution_status: imported
conclusion_support: not_evaluated
manual_review_required: true
long_term_regression: false
```

如果最小输入齐备：

```yaml
minimum_input_status: ready
execution_status: minimum_input_ready
```

## 9. 批量校验清单

导入后必须检查：

- 是否有 user_id。
- 是否有可执行 time_window。
- 是否存在明显重复 case。
- manual_label 是否被误写为结论字段。
- manual_note 是否保留为线索字段。
- target_api_or_action 是否覆盖登录、授权、token/session、发布、换绑、改密、找回、策略 / 画像。
- 是否存在需要脱敏或不应进入样本包的敏感明细。

## 10. 禁止行为

- 禁止导入后直接输出 ATO 结论。
- 禁止把申诉文本当事实。
- 禁止把人工备注当事实。
- 禁止因为风险类型是“盗号”就跳过数据取证。
- 禁止生成处罚、冻结、封禁、扣除或策略上线建议。
