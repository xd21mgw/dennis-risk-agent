# ATO Batch Regression Selection Rules v1

## 1. 目标

定义从批量 ATO case 中选择长期回归样例的规则，确保回归集覆盖正例、反例、边界、权限状态和人工备注冲突。

## 2. 入选标准

满足任一条件可入选长期回归：

- 覆盖一种稳定 ATO 手法链路。
- 暴露新的证据边界或误判风险。
- Data Agent 状态具有代表性，例如 SQL-only、no_permission、empty_result、partial。
- 人工备注与数据发现存在冲突。
- 反例价值高，能防止强判。
- 证据链完整，适合验证 parser 和 account_security 专节规则。
- 权限缺口明显，适合验证 permission_notes / quality_risks。

## 3. 不建议入选

- 与既有回归重复，且没有新增边界。
- 只有用户申诉，没有可执行取证输入。
- 只有人工备注，没有数据返回。
- 结论依赖无法复现的人工口头信息。
- 无法脱敏或无法保留 evidence snapshot。

## 4. 回归类别

| regression_type | 说明 |
|---|---|
| `positive_password_takeover` | 密码登录 / 密码泄露型账号接管 |
| `positive_qr_oauth_takeover` | 扫码 / OAuth 授权型账号接管 |
| `negative_or_insufficient_support` | 反例或证据不足 |
| `phishing_no_resweep` | 钓鱼疑似但未回扫 / 证据不闭合 |
| `sms_oauth_token` | 短信泄露 / OAuth token 异常 |
| `member_phishing_sms_code` | 会员钓鱼 / 短信验证码泄露 |
| `token_session_takeover` | token/session 复用或接管 |
| `sql_only_boundary` | SQL-only / pending_execution 边界 |
| `no_permission_boundary` | 核心数据无权限边界 |
| `data_conflict_boundary` | 人工备注与数据发现冲突 |

## 5. 固定回归样例

| case_id | regression_type | expected_conclusion | must_have | must_not |
|---|---|---|---|---|
| ATO_CASE_001_PASSWORD_KPN_RESWEEP | `positive_password_takeover` | `data_supports_ato_suspicion` | 密码登录；新设备 / 非历史设备；风控命中；发布链路 | 不得把 KPN / 已回扫人工备注当事实；不得输出最终人工盗号定性 |
| ATO_CASE_003_QR_SCAN_GROUND_PROMO_RESWEEP | `positive_qr_oauth_takeover` | `data_supports_ato_suspicion` | OAuth / 扫码；Web 新设备；token 生成；stealAccount 策略；发布链路 | 不得把山东德州 / 已回扫当事实；不得忽略权限缺口 |
| ATO_CASE_006_UNCERTAIN_NO_CLEAR_EVIDENCE | `negative_or_insufficient_support` | `insufficient_support` | 无异常登录证据；无 OAuth / 扫码；无 token/session 接管；疑点可正常解释 | 不得因申诉、发布行为、地区不一致强判；不得把无登录记录解释为无风险 |

## 6. 回归记录要求

每个入选 case 必须记录：

```yaml
regression_case:
  case_id:
  regression_type:
  expected_conclusion:
  evidence_snapshot_path:
  must_have:
  must_not:
  counter_evidence_to_preserve:
  permission_notes_to_preserve:
  quality_risks_to_preserve:
  provider_limitations_to_preserve:
```

## 7. 轮换和退役

保留：
- 固定种子样例 001 / 003 / 006。
- 每类手法至少 1 个正例。
- 每轮至少 1 个反例。
- 每轮至少 1 个状态边界样本。

退役：
- 连续 3 轮无新增价值且被更清晰样本替代。
- evidence snapshot 不完整。
- 无法满足脱敏和复现要求。

## 8. 禁止行为

- 禁止让回归集只包含正例。
- 禁止让人工备注成为 expected_conclusion 的来源。
- 禁止把 Data Agent provider_conclusion_hint 当作最终人工判断。
- 禁止将长期回归输出用于自动处罚或自动策略上线。
