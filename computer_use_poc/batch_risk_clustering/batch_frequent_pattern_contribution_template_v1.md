# Batch Frequent Pattern Contribution Template v1

## Purpose

Frequent pattern and contribution analysis identifies combinations of L1 features that explain a large part of a batch.

The output is used as:

- cluster hint;
- candidate feature hint;
- representative sampling guide;
- abnormal A -> B relation candidate;
- strategy or monitoring candidate.

It is not a final risk conclusion.

## frequent_pattern Schema

| field | description |
|---|---|
| `pattern_id` | Stable local id for the pattern. |
| `feature_combination` | Ordered list of features and values. |
| `case_count` | Number of cases matching the pattern. |
| `coverage_ratio` | case_count / batch size. |
| `baseline_rate` | Rate in control population if available. |
| `baseline_status` | available / only_current_batch_available / baseline_missing. |
| `contribution_score` | 0-1 score combining coverage, lift, evidence quality and false-positive penalty. |
| `cluster_hint` | Which cluster this pattern suggests. |
| `candidate_feature_hint` | Feature candidate for monitoring or strategy research. |
| `evidence_basis` | raw evidence / derived evidence / model inference / user claim / missing evidence. |
| `risk_interpretation` | Why this combination may matter. |
| `business_explanation` | Possible non-risk explanation. |
| `false_positive_risk` | low / medium / high. |
| `required_validation` | Missing join key, denominator, source, or time-order checks. |
| `cannot_conclude_boundary` | What cannot be concluded yet. |

## contribution_score

Recommended scoring components:

```yaml
contribution_score:
  coverage_weight:
  enrichment_weight:
  evidence_quality_weight:
  time_alignment_weight:
  false_positive_penalty:
  final_score:
```

Rules:

- Strong contribution requires coverage plus baseline/control lift plus source reliability.
- If baseline is missing, cap contribution interpretation at `candidate_feature_hint`.
- High contribution does not mean high risk if a business explanation is plausible.
- Patterns from model inference, user claim or analyst note cannot become strong evidence without raw or derived evidence.

## Example Combination Patterns

| combination | possible risk meaning | false-positive / business explanation | required validation |
|---|---|---|---|
| old app version + frontend chain missing + abnormal publish | downgrade attack, fake client, protocol direct call | SDK logging bug, old-version release lag, creator campaign | app_version baseline, frontend instrumentation health, endpoint/action time order |
| same IP segment + same device model + many accounts | proxy pool, device farm, group control | campus/company NAT, popular device model, regional bias | IP denominator, device reuse join key, login/action sequence |
| login device change + token/kick out + user claim not本人 | ATO candidate, token/session takeover, credential stuffing/OAuth path | normal device migration, family/shared account, user misunderstanding | login method, token event status, downstream abnormal action, user history |
| fake account tag + downstream bad action + abnormal registration profile | fake account cluster and downstream abuse | stale high-recall tag, campaign cohort bias | tag precision, downstream action time alignment, registration baseline |
| channel A + reward claim + low retention + device reuse | activity arbitrage or channel fake traffic | new campaign targeting, cold-start traffic, retention measurement lag | channel denominator, same-period control, reward eligibility and device reuse join |

## Output Template

```yaml
frequent_patterns:
  - pattern_id:
    feature_combination:
    case_count:
    coverage_ratio:
    baseline_rate:
    baseline_status:
    contribution_score:
      coverage_weight:
      enrichment_weight:
      evidence_quality_weight:
      time_alignment_weight:
      false_positive_penalty:
      final_score:
    cluster_hint:
    candidate_feature_hint:
    evidence_basis:
    risk_interpretation:
    business_explanation:
    false_positive_risk:
    required_validation:
    cannot_conclude_boundary:
```

## Linkage

- Frequent patterns become candidate rows in abnormal correlation matrix.
- High contribution patterns guide representative sampling.
- Pattern-level evidence feeds cluster evidence card as derived evidence.
- Candidate feature hints can become monitoring or strategy recommendations only after validation.

