# Overlay Scene to Capability Routing

This file is the validation overlay routing subset. It exists to verify cloud natural-language routing for the currently closed Tianshi and real-name partial-contract capabilities.

## Routing Table

| user intent | route | expected behavior | boundary |
|---|---|---|---|
| “这次 eventId 为什么被阻止 / 为什么命中某策略” | `single_event_policy_attribution` | Use the single-event policy attribution template when event context is present | Attribution explains policy conditions, not final cheating judgement |
| “这条策略是什么 / 条件是什么 / 当前版本是什么” | `policy_detail_lookup` | Explain policy definition, expression, and version context | Expression is not complete business causality |
| “这条策略挂在哪个节点 / 哪棵策略树” | `policy_tree_asset_lookup` | Explain node path, tree asset, and bound policies | Tree asset is not a specific event hit path |
| “这条策略什么时候上线 / 最近是否改过” | `policy_release_record_lookup` | Explain workflow records and version tracing | Release record is not risk judgement |
| “这个用户最近命中过哪些策略 / 被哪些策略拦过” | `tianshi_strategy_hit_inventory` / `strategy_hit_overview_lookup` | Prefer fastQueryHbase for overview; use eventList only as supplement | Strategy hits are evidence candidates, not final risk judgement |
| “这个用户一天内哪些策略反复命中 / TOP 策略 / 策略共现” | `tianshi_strategy_hit_inventory` | Output policy_topn, node_topn, condition_topn, cooccurrence, representative events | Cooccurrence is signal, not group or attack-path conclusion |
| “直播长连接为什么被拦 / SYNC_LIVE_ATTACH_REQUEST 为什么阻止” | `tianshi_live_attach_attribution_candidate` | Use attach beta template and representative attribution | Must mark beta partial and `event_detail_partial` when detail is unavailable |
| “业务安全除了注册登录还有哪些场景” | `business_security_scene_asset_mapping` | Output asset map by verified / partial / candidate-only layers | Asset map is not executable judgement |
| “这个接口是不是被爬了 / 能查 ANTICRAWL 吗” | `tianshi_anticrawl_family_candidate` or anti-crawler expert mode | Output candidate-only query plan and required inputs | Do not claim full ANTICRAWL attribution |
| “实名信息能查吗 / 能输出哪些字段 / EB_USER_REAL_NAME_VERILY__1 怎么传参” | `real_name_feature_service_partial_contract` | Output partial contract, parameter mapping, and redacted schema | No real query and no identity judgement |
| “身份证前6位 / 身份证号 / 姓名 / 完整生日” | safe refusal under real-name boundary | Refuse raw identity output; offer derived summary alternatives | No raw identity fields |
| “实名省份和发布 IP 一致，是不是就不是盗号” | account-security / multi-evidence orchestration | Treat real-name summary as candidate evidence only | Cannot independently exclude or prove ATO |
| “帮我看下这个用户有没有风险” | multi-evidence orchestration | Do not default to full governance, attach, ANTICRAWL, or real-name partial contract | Specialized capabilities are candidate evidence sources only |

## Missing Field Handling

- Missing eventId / eventType / query time / policy code: return a query plan or ask for fields; do not guess.
- Missing source_id or time window for strategy inventory: return input requirements.
- Missing ANTICRAWL hit sample: keep candidate-only query plan.
- Missing real-name execution approval: keep contract/schema explanation only.
