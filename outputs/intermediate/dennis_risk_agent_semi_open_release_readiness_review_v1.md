# Dennis Risk Agent Semi-open Release Readiness Review v1

## 1. Review Target

This readiness review prepares the next Dennis Risk Agent semi-open test release package.

Scope correction:

- This is a full-scenario semi-open release readiness review.
- It is not an ATO-only package review.
- ATO is the deepest completed sample capability, but the semi-open package must also cover anti-crawler, protocol attack, group control, device risk, account farm, activity anti-cheating, traffic anti-cheating, traffic diversion, cracked app / plugin risk, general evidence planning, strategy recommendation, safety guardrails, and question collection.

This round only produces local documentation, manifest guidance, checklist, and packing plan.

Not performed:

- No real internal platform access.
- No DataAgent call.
- No auth state / cookie / token / session read.
- No `outputs/dist` update.
- No actual package build.

## 2. Candidate Capability List

| capability area | release role | current readiness | package principle |
|---|---|---|---|
| ATO / 盗号 | Deep sample capability | deep sample ready | Include as full-depth sample and runtime route. |
| Anti-crawler | Expert cognition + response template | runtime summary exists | Include as formal semi-open capability, not appendix. |
| Protocol attack | Expert cognition + evidence planning | runtime summary exists | Include as formal semi-open capability. |
| Group control / device risk | Device risk and automation reasoning | runtime summary + device hand docs exist | Include routing, evidence cards, and boundary rules. |
| Account farm / 小号 | Account matrix and account farm reasoning | batch sample exists for black-market matrix | Include as formal capability with paused deep-dive boundary where relevant. |
| Activity anti-cheating | Promo abuse / incentive abuse reasoning | runtime summary exists | Include formal short-answer and planning coverage. |
| Traffic anti-cheating | Exposure/click/conversion fraud reasoning | runtime summary exists | Include formal short-answer and strategy planning coverage. |
| Traffic diversion / interception | Live / DM / search / homepage diversion reasoning | runtime summary exists | Include formal short-answer and evidence planning coverage. |
| Cracked app / plugin risk | Repack, plugin, dynamic loading, automation risk | cracked app runtime summary + plugin skill exist | Include formal expert cognition and evidence planning. |
| General risk judgment | Evidence card, investigation plan, strategy suggestion | answer templates + plan mode exist | Include cross-scenario contracts. |
| DataAgent query plan | Hive / warehouse question generation | boundary docs exist | Include as plan-only by default; do not represent as universal data substrate. |
| Safety guardrails | prompt injection / asset extraction / preflight | documented + dry-run validated | Include runtime-facing policy summaries and smoke tests. |
| question_collection | user question radar and learning candidate queue | schema/templates/regression ready | Include as full-scenario observation module, pending-review only. |

## 3. Full-scenario Coverage Matrix

| scene / capability | user-facing value | supported mode | DataAgent boundary | readiness | gap |
|---|---|---|---|---|---|
| ATO / 盗号 | Single case judgment, evidence card, batch pattern, expansion plan | execution / plan / batch template | Offline Hive only by explicit query plan or confirmation | fully supported deep sample | Fresh-case runtime validation still useful. |
| 反爬 | Interface / asset / request anomaly and 6+1 control flywheel reasoning | expert cognition / evidence planning | plan_only unless user requests Hive plan | ready as formal cognition capability | Need more semi-open prompts. |
| 协议攻击 | Backend request without frontend action, signing, replay, bypassing client | expert cognition / evidence planning | plan_only | ready as formal cognition capability | Need concise examples in test prompts. |
| 群控 / 设备风险 | Device aggregation, automation, hook/root/frida/proxy relations | expert cognition / readonly evidence planning | no default DataAgent | ready with device boundary | Must keep relation as candidate, not conclusion. |
| 小号 / 账号农场 | Registration, farming, association, batch behavior, resource abuse | expert cognition / batch sample | plan_only for large expansion | ready as formal capability | Black-market deep dive paused, not blocking. |
| 活动反作弊 | Promo abuse, incentive abuse, channel quality | expert cognition / strategy planning | plan_only | ready as formal cognition capability | Needs more semi-open cases. |
| 流量反作弊 | Fake exposure/click/conversion, RTA/RTB abuse | expert cognition / strategy planning | plan_only | ready as formal cognition capability | Needs runtime prompt examples. |
| 导流 / 截流 | Live room, DM, search, profile, nickname, external path | expert cognition / evidence planning | plan_only | ready as formal cognition capability | Should avoid ATO contamination. |
| 插件 / 破解包 | Repack, plugin, dynamic loading, automation behavior | expert cognition / evidence planning | plan_only | ready as formal cognition capability | Need non-ATO smoke prompts. |
| 通用证据卡 / 查证计划 | Evidence card, source quality, missing evidence, manual review boundary | response template / plan mode | plan_only unless authorized | ready | Keep source metadata for single and batch cases. |
| 策略推荐 / 举一返三 | Candidate strategy direction, expansion anchors, query plan | plan_mode_only | query plan only | ready | Must not enter execution for ATO expansion. |
| DataAgent query plan | Hive question generation | plan_only | not default runtime call | ready | Must not become universal data substrate. |
| 安全防护 | Prompt / Skill / source / credential extraction protection | deny / degrade / summarize | no DataAgent | ready | Need package minimization scanner before build. |
| question_collection | Full-scenario user question capture, quality signals, candidate queue | post-answer accounting | no DataAgent | ready | Needs release placement under `question_collection/`. |

## 4. Suggested Include Set

High-level include groups:

- Runtime entry and README.
- Multi-entry runtime guard and user guide.
- Capability registry and scene routing.
- Answer experience templates and observation/evidence contracts.
- Full-scenario runtime summaries from `skills/.../11_runtime_summaries/`.
- ATO deep sample templates and selected redacted run summaries.
- Safety policies, field output classification, asset extraction guard summary, package scanner.
- Security preflight runtime-facing config / evaluator where needed.
- `question_collection/` as full-scenario learning candidate queue.
- Runtime validation cases, semi-open prompt matrix, minimal smoke tests.

## 5. Suggested Exclude Set

Exclude by default:

- Auth state, cookie, token, session, storageState, headers, credentials.
- `.git`, local temp files, `.DS_Store`.
- `outputs/dist` historical tarballs.
- Full historical `run_logs/`.
- Raw observations and unredacted platform screenshots.
- Full internal test corpus and prompt injection / asset extraction full cases unless explicitly approved.
- Full Skill / Prompt source that is not intended for semi-open distribution.
- POC process files not needed for runtime.
- Unreviewed pilot materials.

## 6. question_collection Inclusion

`question_collection` should be included as:

```text
outputs/release/<release_name>/question_collection/
```

Required semantics in manifest:

- Full-scenario user question observation.
- Learning candidate queue.
- `agent_observed` / `agent_suggested` / `reviewer_final`.
- `reviewer_decision=pending` by default.
- No automatic brain update.
- No automatic release update.
- No automatic DataAgent call.
- Not ATO-only.

Runtime logging contract:

- Current repository had no real runtime write integration at review time.
- Runtime must append real user question records to `runtime_logs/question_collection/question_records_YYYYMMDD.jsonl`.
- `question_learning_candidate_queue_v1.csv` remains a read-only template.
- This is a non-blocking TODO for documentation readiness, but should be wired before real semi-open runtime use.

## 7. Safety / Asset Extraction Guard Inclusion

Include runtime-facing summaries and policies:

- `field_output_classification_policy_v1.md`
- `sensitive_field_redaction_policy.md`
- `asset_extraction_guard_policy.md`
- `release_package_asset_minimization_policy.md`
- `readonly_semi_open_release_manifest_guidance.md`
- package scanner and rules, if the release process needs local validation.

Do not ship full sensitive regression corpus unless the target audience is explicitly authorized.

## 8. Runtime Validation Cases

Include:

- `runtime_validation_cases_v1.yaml`
- semi-open prompt matrix from this readiness review.
- smoke test summary.

Runtime validation must cover:

- All full-scenario expert cognition categories.
- ATO deep sample.
- DataAgent plan-only boundary.
- Safety / asset extraction.
- question_collection three-layer record model.
- Multi-entry runtime guard and mixed-request decomposition.

## 9. DataAgent Boundary

DataAgent is currently positioned as a Hive / company warehouse data analysis capability.

It must not be generalized as an all-purpose risk-control substrate.

Release wording:

- Non-ATO scenarios do not call DataAgent by default.
- ATO also defaults to readonly online observation or query planning unless user explicitly asks for offline query planning or execution is authorized.
- When data is needed, generate a query plan first or wait for user confirmation.
- DataAgent output must still pass evidence source, source quality, and manual review boundary.

## 10. ATO and Non-ATO Inclusion Principle

ATO:

- Deep closed-loop sample.
- More complete evidence chain, tool boundary, DataAgent/Hive expansion questions, batch sample, browser smoke test.

Non-ATO:

- Formal semi-open capabilities.
- Include expert cognition, response templates, evidence framework, investigation plan, and strategy recommendation.
- Do not treat as lightweight appendix.

## 11. Package Minimization

Principles:

- Ship runtime minimum, not repository backup.
- Prefer summaries over full raw development assets.
- Ship selected redacted run summaries, not all run logs.
- Keep test prompts compact.
- Exclude full case libraries unless explicitly approved.
- Run package scanner before `outputs/dist` packaging.

## 12. Sensitive Asset Exclusion

Before build, scan for:

- `cookie`, `token`, `session`, `storageState`, `authorization`, `header`.
- `.ks_sso`, auth state, browser storage.
- raw IP/UID/DID if the audience is broad; use safe_ref or partial mask when needed.
- real personal information, phone number, ID card, raw platform screenshots.
- internal URLs or fields that expose unauthorized platform access detail.

UID / DID / IP can be used as internal risk entities, but semi-open packages should follow audience-scope field output policy.

## 13. Blockers Before Actual Packaging

Current blocking items:

- Need final package filelist decision from this review.
- Need package scanner run on the candidate release directory after it is assembled.
- Need confirmation whether full Skill prompt source should be included or replaced with runtime summaries.
- Need final audience scope for UID / DID / IP masking policy.

No P0 blocker was found in this document review, but the package must not be built until exclusion list and scanner are applied.

## 14. Non-blocking TODO

- Add more non-ATO semi-open test prompts after first user trial.
- Add APP / Web entry validation beyond KIM.
- Add reviewer workflow for question_collection.
- Wire question_collection runtime append-only logging to `runtime_logs/question_collection/question_records_YYYYMMDD.jsonl`.
- Add release package manifest automation later.

## 15. Recommendation

Recommendation: proceed to actual packaging only after the user explicitly requests it and after the candidate filelist is reviewed.

Do not update `outputs/dist` in this readiness review round.
