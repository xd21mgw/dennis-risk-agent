# Abnormal Correlation Matrix v1

## 1. Definition

“不可预测矩阵”在本项目里的准确含义是：异常相关性矩阵。

It is not:

- a generic uncertainty matrix.
- a prediction error matrix.
- a model confidence table.

It is:

- a risk explanation matrix that checks whether dimension A strongly binds to, enriches, or skews dimension B in a risk batch.
- a method to discover infrastructure, attack path, toolchain, channel arbitrage, strategy gap, false-positive source, or business abuse path.

The unit is not just `field A -> field B`; it is:

```text
relation_family + relation_direction + evidence_basis + baseline policy + denominator + reverse/confounder checks + relationship_strength + cannot_conclude_boundary
```

## 2. Core Question

In normal business, two dimensions should not show unexplained strong binding, one-way enrichment, or sudden conditional distribution shift.

For each relation `A -> B`, the matrix asks:

- A 条件下 B 是否异常集中.
- 是否高于正常业务基线.
- 是否有总体分母，不能只看分子不看分母.
- 是否覆盖批次中足够比例的 case.
- 是否能解释攻击路径、黑产基础设施、工具链、渠道套利或策略噪声.
- 反向 `B -> A` 是否也成立.
- A 是否发生在 B 之前.
- 是否可能由活动、节假日、版本发布、策略上线、渠道投放等混杂因素解释.
- 是否存在 selection bias, especially strategy recall batch.

## 3. Relation Families

### 3.1 infrastructure correlation

Relations:

- IP -> device_model / os_version / app_version / user_id.
- device_id -> user_id / abnormal_action.
- proxy / VPN / ASN -> request_pattern / account_cluster.

Risk explanation:

- 群控.
- 设备农场.
- 代理池.
- 批量注册.
- 批量上号.

Required cautions:

- IP clustering can be office, campus, carrier NAT, CDN, or regional campaign traffic.
- Device sharing can be family / work device unless behavior and timing align.

### 3.2 toolchain correlation

Relations:

- app_version -> abnormal_action.
- mod / device_model -> request_pattern.
- frontend_activity_gap -> backend_request.
- old_version -> high_risk_behavior.

Risk explanation:

- 协议直调.
- 伪造客户端.
- 降版本攻击.
- 自动化工具.

Required cautions:

- `mod=POST` is a field value / abnormal mod marker unless a field dictionary proves it means HTTP method.
- Old version alone is not risk; combine with request pattern, frontend gap, DID mismatch, UA, endpoint, and timing.

### 3.3 entry-path correlation

Relations:

- login_method -> abnormal_action.
- OAuth / Harmony / one-click-login -> kick_out / token_revoke / publish / password_change.
- H5 / Web / App entry -> downstream behavior.

Risk explanation:

- 扫码接管.
- OAuth / 一键登录接管.
- 入口链路异常.

Required cautions:

- Harmony / OAuth relation is not credential stuffing by default.
- Strong judgement requires authorization chain, token lifecycle, and downstream behavior evidence.

### 3.4 behavior-chain correlation

Relations:

- login_success -> publish / withdraw / bind_change / private_message.
- no_frontend_action -> backend_action.
- strategy_hit -> downstream risky behavior.

Risk explanation:

- ATO 后行为链路.
- 爬虫.
- 自动化.
- 策略绕过.

Required cautions:

- Event order matters. A must happen before B for attack-path explanation.
- Strategy hit is evidence of control response, not final risk conclusion.

### 3.4A ATO cluster lens correlation

Relations:

- existing content / strategy / device cluster -> ATO lens hit.
- WEB / H5 / PC non-trusted login -> downstream diversion action.
- suspicious login/control-chain event -> `login_to_action_delta`.
- common `device_id` -> UA / model / IP / login_source drift.
- representative single-case ATO proof -> cluster-level coverage and confidence backfill.

Risk explanation:

- 盗号后投放导流内容.
- WEB/session/API 控制端接管.
- 常用 `device_id` 下设备身份变量伪装.
- 内容导流簇叠加 ATO 盗号投放嫌疑.

Required cautions:

- Existing cluster signals and `ato_cluster_lens` are additive, not mutually exclusive.
- Content similarity, strategy hit or shared device cannot independently prove ATO.
- Common `device_id` cannot lower ATO confidence unless device identity consistency is complete.
- Representative single-case deep dive supports the represented cluster only after `cluster_level_backfill` checks coverage, similarity, source quality and counter examples.

### 3.5 business-arbitrage correlation

Relations:

- channel / campaign -> reward_claim / low_retention / low_real_behavior.
- activity_entry -> device_reuse / account_reuse.
- incentive_event -> abnormal_conversion.

Risk explanation:

- 活动套利.
- 渠道假量.
- 真人众包任务.

Required cautions:

- Low retention alone is not black production evidence.
- Reward claim must be compared with channel denominator and campaign design.

### 3.6 strategy-feedback correlation

Relations:

- strategy_id -> false_positive_feedback.
- hit_reason -> manual_review_result.
- control_action -> complaint / appeal / churn.

Risk explanation:

- 误伤.
- 策略噪声.
- 策略可扩散性.

Required cautions:

- Strategy recall batches have selection_bias_risk by construction.
- Do not repeat hit reason as final attribution.

## 4. Baseline Policy

### Baseline states

| baseline_status | meaning | allowed enrichment judgement |
|---|---|---|
| `historical_normal_baseline_available` | Historical normal traffic / user / channel distribution exists. | strong allowed if other checks pass. |
| `same_period_control_group_available` | Same-period non-hit or holdout group exists. | strong allowed if other checks pass. |
| `strategy_population_baseline_available` | Baseline within all strategy candidates or recall population exists. | strong allowed with selection-bias caution. |
| `only_current_batch_available` | Only the current batch is available. | batch_internal_concentration only; no strong enrichment. |
| `baseline_missing` | No baseline or denominator. | hypothesis_only or weak unless very strong raw join key exists. |

### Rules

- 有历史正常基线或同周期对照组时，才允许判断 `enrichment_signal=strong`.
- 只有当前批次时，只能写 `batch_internal_concentration`，不能写 strong enrichment.
- `baseline_missing` 时，只能输出 `hypothesis_only` 或 `weak`，除非存在非常强的 raw evidence join key.
- 不能只看分子不看分母，必须提示 `denominator_required`.
- 如果是策略召回集合，必须标记 `selection_bias_risk`.
- Baseline should match the relation family: channel baseline for channel relations, endpoint baseline for interface relations, login-method baseline for entry-path relations.

## 5. Relationship Strength Grading

| relationship_strength | conditions |
|---|---|
| `strong_abnormal_correlation` | raw evidence support; historical or control baseline; clear enrichment; material batch coverage; explains attack path; pseudo-correlation checks pass. |
| `medium_abnormal_correlation` | current batch concentration is clear; partial raw evidence exists; baseline or key follow-up is missing; good priority validation hypothesis. |
| `weak_signal` | small number of similar cases; missing baseline; missing join key; candidate clue only. |
| `hypothesis_only` | mainly from model inference, analyst note, user claim, or historical similar pattern; insufficient raw evidence. |
| `not_enough_evidence` | sample too small; key fields missing; source blocked / timeout; directionality cannot be judged. |

### Upgrade / downgrade rules

- Upgrade only when evidence basis improves, not because wording is stronger.
- Downgrade if denominator is missing.
- Downgrade if time alignment is unknown.
- Downgrade if plausible business explanation exists.
- Downgrade if selection bias is present and no control population exists.

## 6. Required Checks Per Matrix Row

Each matrix row must evaluate:

| check | question | failure handling |
|---|---|---|
| `direction_check` | Does A -> B hold? | If unclear, relationship_strength <= weak_signal. |
| `reverse_check` | Does B -> A also hold? | If only one-way, explain whether A is entry/toolchain/infra. |
| `time_alignment_check` | Did A happen before B? | If unknown, cannot claim attack path. |
| `denominator_check` | Is population denominator available? | If missing, mark `denominator_required`. |
| `confounder_check` | Could activity, holiday, version launch, strategy launch, channel campaign explain it? | If yes, downgrade and add follow-up. |
| `selection_bias_check` | Is the sample from one strategy recall or curated alert set? | If yes, mark `selection_bias_risk`. |
| `business_explanation_check` | Is there a normal-business explanation? | If yes, add false-positive risk. |
| `source_quality_check` | Are sources fresh, reliable, partial, blocked, or timeout? | If partial/blocked, mark source_gap. |

## 7. Standard Output Table Template

| relation_family | relation_direction | observed_pattern | evidence_basis | baseline_status | denominator_status | coverage_ratio | enrichment_signal | directionality | reverse_check_result | confounder_risk | false_positive_risk | relationship_strength | attack_path_hypothesis | required_followup | cannot_conclude_boundary |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| infrastructure / toolchain / entry-path / behavior-chain / business-arbitrage / strategy-feedback | A -> B | what was observed | raw / derived / model / claim / missing / blocked | historical_normal_baseline_available / same_period_control_group_available / strategy_population_baseline_available / only_current_batch_available / baseline_missing | denominator_available / denominator_required / denominator_partial | x/y or % | strong / medium / weak / batch_internal_concentration / none / unknown | one_way / two_way / unknown | reverse_holds / reverse_not_holds / reverse_not_checked | low / medium / high | low / medium / high | strong_abnormal_correlation / medium_abnormal_correlation / weak_signal / hypothesis_only / not_enough_evidence | candidate explanation | fields and source needed | what cannot be concluded now |

## 7A. Batch ATO Lens Matrix Rows

| relation_family | relation_direction | observed_pattern | relationship_strength | required_followup | cannot_conclude_boundary |
|---|---|---|---|---|---|
| `existing_cluster_plus_ato_lens` | content_diversion_cluster -> `web_untrusted_login_cluster` | content-similar accounts also show recent WEB/H5/PC non-trusted login | medium_to_high if baseline and coverage are available | login/control-chain evidence and `representative_ato_single_case_deep_dive` | content similarity alone is not ATO proof |
| `login_to_action_cluster` | suspicious_login -> publish/comment/live/private_message | WEB/control-chain event followed by action within 0-30 minutes | high when repeated and source quality is good | publish audit, content IDs and candidate-session alignment | short delta is a clue until login identity and action source align |
| `device_identity_inconsistency_cluster` | common_device_id -> abnormal UA/model/IP/login_source drift | `device_id` looks common but identity variables drift across cases | medium_to_high | device identity coverage and counter-example review | common `device_id` cannot reduce ATO confidence by itself |
| `cluster_level_backfill` | representative_case_deep_dive -> cluster confidence | representative sample proves ATO mechanism and backfills coverage/similarity | depends_on_coverage | coverage, similarity, source gap and counter examples | representative sample cannot prove the full batch by itself |

## 8. Concrete Examples

### Example 1: ATO Harmony / OAuth

| relation_family | relation_direction | observed_pattern | evidence_basis | baseline_status | denominator_status | coverage_ratio | enrichment_signal | directionality | reverse_check_result | confounder_risk | false_positive_risk | relationship_strength | attack_path_hypothesis | required_followup | cannot_conclude_boundary |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| entry-path correlation | login_method=HARMONY_ONE_CLICK -> kick_out / token_revoke / publish_after_login | Several batch cases show one-click login followed by kick-out or publish | derived from current batch; raw auth chain missing | baseline_missing | denominator_required | current batch subset only | batch_internal_concentration | one_way | reverse_not_checked | medium: normal one-click login exists | medium: device migration / normal login can resemble this | medium_abnormal_correlation | Harmony / OAuth login takeover candidate | OAuth grant record, token issued/revoke raw evidence, event order, device trust | Cannot call strong ATO or credential stuffing without authorization chain and token raw evidence |

Required interpretation:

- Output medium, not strong.
- Do not call it credential stuffing by default.
- Strong requires authorization chain, token lifecycle raw evidence, and downstream abnormal action order.

### Example 2: Protocol Downgrade

| relation_family | relation_direction | observed_pattern | evidence_basis | baseline_status | denominator_status | coverage_ratio | enrichment_signal | directionality | reverse_check_result | confounder_risk | false_positive_risk | relationship_strength | attack_path_hypothesis | required_followup | cannot_conclude_boundary |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| toolchain correlation | old_app_version + abnormal_mod -> high_frequency_backend_action | Old versions and abnormal mod values concentrate in high-frequency backend actions | current batch raw fields + derived concentration | only_current_batch_available | denominator_required | current batch subset | batch_internal_concentration | one_way | reverse_not_checked | high: old client compatibility / version release | medium: legitimate old clients | medium_abnormal_correlation or weak_signal if frontend baseline missing | protocol direct call / forged client / downgrade candidate | field dictionary for mod, frontend action baseline, UA, endpoint, DID consistency | `mod=POST` cannot be interpreted as HTTP method; cannot strong-judge without frontend baseline and field semantics |

Required interpretation:

- `mod=POST` only means abnormal mod / model field unless schema proves HTTP method.
- If frontend behavior baseline is missing, strength should be medium or weak, not strong.

### Example 3: Activity Arbitrage

| relation_family | relation_direction | observed_pattern | evidence_basis | baseline_status | denominator_status | coverage_ratio | enrichment_signal | directionality | reverse_check_result | confounder_risk | false_positive_risk | relationship_strength | attack_path_hypothesis | required_followup | cannot_conclude_boundary |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| business-arbitrage correlation | channel=A -> reward_claim + low_retention + device_reuse | Channel A cases show early reward claim, low retention, and device reuse | current batch derived evidence | only_current_batch_available | denominator_required | current batch channel subset | batch_internal_concentration | one_way | reverse_not_checked | high: channel campaign mix / incentive design | high: new channel quality can be low without fraud | medium_abnormal_correlation | activity arbitrage / channel fake volume candidate | full channel denominator, same-period control group, reward eligibility, device graph confidence | Without channel denominator, cannot call strong enrichment or block all channel A users |

Required interpretation:

- If channel denominator is missing, write `batch_internal_concentration`, not strong enrichment.
- Low retention alone is not arbitrage proof.

## 9. Interpretation Rules

- Abnormal correlation can generate candidate risk patterns only.
- It cannot replace raw evidence.
- Similar cases do not equal same gang.
- Shared join key, shared device, shared IP, shared version, shared entry, shared behavior chain or shared infrastructure is required before same-source judgement.
- Historical case can only be similar pattern / hypothesis.
- If baseline is missing, write `baseline_missing`, not strong enrichment.
- If only current batch is available, write `batch_internal_concentration`.
- One-way relation may indicate entry, toolchain or local infrastructure, but must be validated.

## 10. Output Boundary

- Do not output cookie / token / session / header / phone / API key.
- Use safe_ref or aggregate features for sensitive fields.
- Current batch evidence must come from current input or current task observation.
