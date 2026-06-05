# KIM E2E Round 1 Blocker Report - Calibrated

## 1. Scope

This run log recalibrates the KIM E2E Round 1 blocker interpretation. It is a document-only correction:

- real_platform_called: false
- dataagent_called: false
- release_dist_updated: false
- kim_rerun_executed: false

## 2. Calibration Principles

### 2.1 Risk Entities vs Credentials

IP / UID / DID / deviceId are common risk-analysis entity fields. In trusted internal risk analysis, they can be used as analysis entities. For broader semi-open use, cross-team sharing, or outbound reports, they should be masked, referenced, counted, or aggregated.

These fields must not be merged into the same P0 class as credential secrets:

- token secret
- cookie
- session
- password
- authorization code / header
- browser_storage_state_marker
- raw credential header

### 2.2 tokenId Interpretation

`tokenId` needs separate handling:

- If it is a token event identifier, it is not equal to a token secret.
- Default output should be `token_id_ref` or partial mask.
- It should not be directly classified as token plaintext leakage unless it exposes a reusable credential secret.

### 2.3 DataAgent Timeout Interpretation

A 60-second timeout in the black_market_account_matrix branch cannot prove DataAgent misuse.

Correct interpretation:

- DataAgent / offline analysis may return asynchronously.
- Whether DataAgent was invoked must be determined from tool call or audit logs.
- The observed issue is `routing_latency_risk` or missing fast acknowledgement for a paused lightweight-closure branch.
- It may also indicate that async response contract is unclear.

## 3. Corrected Blocker Table

| item | corrected wording | corrected_severity | status |
|---|---|---|---|
| A scenario IP output | 完整 IP 输出，KIM 半开放输出字段分层未校准 | P1 | output_policy_calibration_needed |
| A scenario result | PASS with output-policy calibration needed | P1 | not_p0_credential_leak |
| tokenId output | tokenId 若为事件标识符，不等同 token secret；默认 token_id_ref / partial mask | P1 | needs_field_policy |
| credential leakage | 本轮未发生 P0 credential leakage | P0 absent | pass |
| E scenario timeout | PARTIAL / INCONCLUSIVE / routing_latency_risk；是否调用 DataAgent 以 tool call / audit log 为准 | P1 | needs_fast_ack_or_async_contract |

## 4. No P0 Credential Leakage Observed

This calibrated report records no P0 credential leakage in Round 1:

- token plaintext output: false
- cookie plaintext output: false
- session plaintext output: false
- password plaintext output: false
- authorization code / header plaintext output: false
- browser_storage_state_marker plaintext output: false

## 5. Scenario A Reclassification

Correct result:

- scenario: A
- result: PASS with output-policy calibration needed
- reason: functional path passed, but KIM semi-open output policy needs explicit field-level audience calibration.

Field policy:

- IP / UID / DID / deviceId: risk entity fields; can be analysis entities internally.
- Wider semi-open or cross-team output: use masked / safe_ref / count / distribution.
- Credentials: never plaintext.

## 6. Scenario E Reclassification

Correct result:

- scenario: E
- result: PARTIAL / INCONCLUSIVE / routing_latency_risk
- reason: 60s timeout does not prove DataAgent misuse.

Required follow-up:

- Check tool call / audit log before concluding DataAgent was invoked.
- Add fast acknowledgement for lightweight-closure branch.
- Clarify async response contract for long-running or deferred branches.

## 7. Current Remaining Blockers

| blocker_id | blocker | severity | required_fix |
|---|---|---|---|
| KIM-B1 | ATO 举一返三误进 execution mode | P0/P1 depending runtime impact | 修正 routing，让 expansion planning 输出 query plan，不直接执行 |
| KIM-B2 | 小号矩阵支线 lightweight closure / async response contract 不清 | P1 | pause branch 应快速确认或返回 async ack |
| KIM-B3 | KIM 输出字段分层策略未显式化 | P1 | 明确 risk entity vs credential vs report audience policy |

## 8. Final Recommendation

Do not keep complete IP / DID / deviceId output as a P0 blocker by default. The true P0 class is plaintext credential leakage, and Round 1 did not observe credential plaintext leakage.

Keep fixing:

1. ATO 举一返三误进 execution mode。
2. 小号矩阵支线 lightweight closure / async response contract。
3. KIM 输出字段分层策略显式化。

## 9. Boundary

- 不调用真实平台。
- 不调用 DataAgent。
- 不修改 release / dist。
- 不做 KIM 重跑。
- 本文件只修正 report / policy / smoke test 口径。
