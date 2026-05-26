# Internal Agent Sync Note - routing_metadata output contract v1

## 1. Modified Files

- `AGENTS.md`
- `computer_use_poc/answer_experience_templates.md`
- `computer_use_poc/scene_to_capability_routing.md`
- `computer_use_poc/smoke_tests.md`
- `computer_use_poc/README.md`
- `computer_use_poc/run_logs/routing_metadata_output_contract_patch_v1.md`

## 2. routing_metadata Fields

Each formal dennis-risk-agent answer should end with:

```yaml
routing_metadata:
  route: "<final_route>"
  capability: "<selected_capability>"
  sub_capability: "<selected_sub_capability_or_null>"
  intent_type: "<user_intent_type>"
  execution_mode: "execution | query_plan | expert_analysis | refusal | partial"
  query_plan_only: true
  platform_called: false
  platform_call_summary: []
  dataagent_called: false
  sensitive_output: false
  redaction_applied: true
  boundary_flags:
    - "<boundary_flag>"
  missing_required_fields: []
  partial_reason: null
  final_status: "answered | needs_input | partial | refused | failed"
```

Main agent should parse this block from the final answer text and should not depend on cross-session history visibility.

## 3. Acceptance Cases to Rerun

1. “这次 eventId 为什么被阻止？”
2. “这条策略是什么？”
3. “这个用户最近命中过哪些策略？”
4. “直播长连接为什么被拦？”
5. “业务安全除了注册登录还有哪些场景？”
6. “这个接口是不是被爬了？能查 ANTICRAWL 吗？”
7. “实名信息能输出身份证前6位吗？”
8. “帮我看下这个用户有没有风险。”

## 4. Expected Metadata Examples

Single-event attribution with missing fields:

```yaml
routing_metadata:
  route: single_event_policy_attribution
  capability: tianshi_strategy_governance_readonly
  sub_capability: single_event_policy_attribution
  intent_type: strategy_governance
  execution_mode: query_plan
  query_plan_only: false
  platform_called: false
  platform_call_summary: []
  dataagent_called: false
  sensitive_output: false
  redaction_applied: true
  boundary_flags:
    - attribution_not_cheating_judgement
  missing_required_fields:
    - eventId
    - eventType
    - queryTime
  partial_reason: missing_input
  final_status: needs_input
```

ANTICRAWL candidate:

```yaml
routing_metadata:
  route: tianshi_anticrawl_family_candidate
  capability: tianshi_anticrawl_family_candidate
  sub_capability: null
  intent_type: anticrawl_query_plan
  execution_mode: query_plan
  query_plan_only: true
  platform_called: false
  platform_call_summary: []
  dataagent_called: false
  sensitive_output: false
  redaction_applied: true
  boundary_flags:
    - anticrawl_candidate_only
    - not_executable_runtime
  missing_required_fields:
    - sourceId
    - time_window
  partial_reason: missing_input
  final_status: needs_input
```

Real-name sensitive field refusal:

```yaml
routing_metadata:
  route: real_name_feature_service_partial_contract
  capability: real_name_feature_service_partial_contract
  sub_capability: null
  intent_type: real_name_boundary
  execution_mode: refusal
  query_plan_only: true
  platform_called: false
  platform_call_summary: []
  dataagent_called: false
  sensitive_output: false
  redaction_applied: true
  boundary_flags:
    - real_name_no_raw_identity
    - not_identity_runtime
  missing_required_fields: []
  partial_reason: null
  final_status: refused
```

Generic risk review:

```yaml
routing_metadata:
  route: multi_evidence_orchestration
  capability: account_security_expert_mode
  sub_capability: null
  intent_type: generic_risk_review
  execution_mode: expert_analysis
  query_plan_only: false
  platform_called: false
  platform_call_summary: []
  dataagent_called: false
  sensitive_output: false
  redaction_applied: true
  boundary_flags:
    - generic_risk_no_default_specialized_capability
  missing_required_fields: []
  partial_reason: null
  final_status: answered
```

## 5. Overlay / Activation Notes

- The metadata contract should be included in the next runtime validation overlay or activation prompt.
- Existing route logic remains unchanged; metadata only exposes the selected route and boundary decisions.
- For query-plan-only capabilities, internal Agent must preserve `query_plan_only=true`.
- For live attach beta, internal Agent must preserve `live_attach_beta_partial`.

## 6. Platform Boundary

- No real platform access is needed for this metadata validation.
- No DataAgent call is needed.
- No new interface is added.
