# Abnormal Correlation Matrix v1

## 1. Definition

“不可预测矩阵”在本项目里的准确含义是：异常相关性矩阵。

It is not:

- a generic uncertainty matrix.
- a prediction error matrix.
- a model confidence table.

It is:

- a matrix that checks whether dimension A strongly binds to, enriches, or skews dimension B in a risk batch.
- a way to discover infrastructure, attack path, toolchain, channel arbitrage, strategy gap or business abuse path.

## 2. Core Question

In normal business, two dimensions should not show strong binding, one-way enrichment or sudden conditional distribution shift.

In a risk batch, if `A -> B` shows abnormal concentration or enrichment, the matrix asks:

- A 条件下 B 是否异常集中.
- 该组合是否高于正常业务基线.
- 该组合是否在正常业务中少见.
- 是否覆盖批次中足够比例的 case.
- 是否能解释攻击路径或黑产基础设施.
- 反向 `B -> A` 是否也成立.
- 如果只单向成立，是否说明它是入口、工具链或局部基础设施.

## 3. Example Relations

- IP -> device model / system version / app_version / mod.
- device_id -> user_id.
- app_version -> high_risk_behavior.
- login_method -> abnormal_action.
- channel -> retention / reward / conversion.
- strategy_id -> behavior_type / false_positive_feedback.
- interface -> request_pattern / frontend_activity_gap.
- event_time -> burst_cluster / periodic_pattern.
- entry_source -> downstream abnormal action.
- campaign_id -> reward_claim / low_retention / device_reuse.

## 4. Matrix Cell Schema

Each matrix cell should include:

| field | meaning |
|---|---|
| `relation_direction` | Example: IP -> model. |
| `observed_pattern` | Observed abnormal combination. |
| `baseline_comparison` | above_baseline / normal_range / below_baseline / baseline_missing. |
| `enrichment_signal` | strong / medium / weak / none / unknown. |
| `coverage_ratio` | Batch coverage ratio. |
| `rarity_signal` | common / uncommon / rare / unknown. |
| `directionality` | one_way / two_way / unknown. |
| `attack_path_hypothesis` | Candidate attack path. |
| `evidence_level` | strong / medium / weak / hypothesis_only. |
| `required_followup` | Evidence needed to validate. |
| `risk_of_false_positive` | Normal-business explanation or FP risk. |

## 5. Interpretation Rules

- Abnormal correlation can generate candidate risk patterns only.
- It cannot replace raw evidence.
- Similar cases do not equal same gang.
- Shared join key, shared device, shared IP, shared version, shared entry, shared behavior chain or shared infrastructure is required before same-source judgement.
- Historical case can only be similar pattern / hypothesis.
- If baseline is missing, write `baseline_missing`, not strong enrichment.
- One-way relation may indicate entry, toolchain or local infrastructure, but must be validated.

## 6. Evidence Upgrade Ladder

| evidence_level | condition |
|---|---|
| hypothesis_only | Pattern exists but baseline / coverage / source quality missing. |
| weak | Pattern covers a small subset or has plausible normal explanation. |
| medium | Pattern has meaningful coverage and some source support, but missing join key or baseline. |
| strong | Pattern is above baseline, covers material subset, has join key or shared infrastructure, and explains behavior chain. |

## 7. Output Boundary

- Do not output cookie / token / session / header / phone / API key.
- Use safe_ref or aggregate features for sensitive fields.
- Current batch evidence must come from current input or current task observation.
