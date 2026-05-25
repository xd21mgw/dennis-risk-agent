# Batch TOP Dimension Drilldown Template v1

## Purpose

TOP dimension drilldown turns `batch_feature_table` into interpretable concentration summaries. It helps identify where a batch is concentrated, whether the concentration has a risk explanation, and where false-positive or business explanations may exist.

TOP dimensions are hints, not final risk conclusions.

## top_dimension_summary Schema

| field | description |
|---|---|
| `dimension_name` | Dimension being summarized, such as app_version, ip24, device_model. |
| `top_value` | TOP value or bucket. |
| `case_count` | Number of cases covered. |
| `coverage_ratio` | case_count / batch size. |
| `baseline_rate` | Rate in historical normal or same-period control group. |
| `baseline_status` | historical_normal_baseline_available / same_period_control_group_available / only_current_batch_available / baseline_missing. |
| `denominator_status` | denominator_available / denominator_required / denominator_partial. |
| `risk_interpretation` | Why this dimension may indicate infrastructure, toolchain, entry path, behavior chain, business arbitrage or strategy-feedback risk. |
| `business_explanation` | Possible benign explanation, such as campaign, release, monitoring change, product launch. |
| `false_positive_risk` | low / medium / high. |
| `next_drilldown` | Suggested next dimension or A -> B relation to test. |
| `evidence_level` | strong / medium / weak / hypothesis_only / not_enough_evidence. |

## Supported TOP Dimensions

| dimension | risk interpretation | false-positive / business explanation | next drilldown |
|---|---|---|---|
| `app_version` | Old or abnormal version may indicate downgrade attack, fake client, crawler SDK mismatch. | Product rollout, grey release, app-store lag, regional version distribution. | app_version -> abnormal_action; app_version -> frontend_missing_rate; app_version -> device_model. |
| `ip24` | Shared IP segment may indicate proxy pool, device farm, office/campus NAT, batch registration. | Carrier NAT, public Wi-Fi, company/campus network, campaign traffic. | ip24 -> device_model; ip24 -> user_id count; ip24 -> login_type. |
| `device_model` | Concentrated model may indicate emulator farm, device farm, toolchain fingerprint. | Popular low-end device, regional model bias, channel distribution. | device_model -> app_version; device_model -> frontend_missing_rate; device_model -> account_count. |
| `login_type` / `login_method` | OAuth/Harmony/one-click/password pattern can separate ATO paths. | Product login migration, entry experiment, normal platform login preference. | login_method -> kick_out/token_revoke; login_method -> abnormal_action. |
| `strategy_hit` / `strategy_id` | Strategy recall concentration can reveal rule noise or shared risk feature. | Selection bias from recall set; policy rollout. | strategy_id -> false_positive_feedback; strategy_id -> behavior_type. |
| `abnormal_action` | Downstream action concentration may show attack objective. | Normal campaign behavior, product feature push, influencer events. | abnormal_action -> login_method; abnormal_action -> app_version; abnormal_action -> channel. |
| `frontend_missing_rate` | Backend requests without frontend chain may indicate protocol direct call or crawler. | Instrumentation loss, SDK bug, frontend logging delay. | frontend_missing_rate -> endpoint; frontend_missing_rate -> app_version; frontend_missing_rate -> UA. |
| `channel` | Channel concentration may indicate fake traffic, incentive abuse, channel quality issue. | Campaign targeting, budget shift, seasonal traffic. | channel -> reward_claim; channel -> retention; channel -> device_reuse. |
| `fake_account_tag` | Tags can support fake-account clustering and downstream badness. | High-recall tag false positives; stale tags. | fake_account_tag -> downstream_bad_action; fake_account_tag -> register_profile. |

## Output Template

```yaml
top_dimension_summary:
  - dimension_name:
    top_value:
    case_count:
    coverage_ratio:
    baseline_rate:
    baseline_status:
    denominator_status:
    risk_interpretation:
    business_explanation:
    false_positive_risk:
    next_drilldown:
    evidence_level:
```

## Boundary

- High TOP coverage is not a strong conclusion without denominator and baseline.
- If the batch itself is strategy recall, mark `selection_bias_risk`.
- TOP dimensions feed abnormal correlation matrix and representative sampling; they do not replace raw evidence.

