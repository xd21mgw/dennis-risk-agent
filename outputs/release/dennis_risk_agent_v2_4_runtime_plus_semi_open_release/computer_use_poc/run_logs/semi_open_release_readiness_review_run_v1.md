# Semi-open Release Readiness Review Run v1

## 1. Run Target

Prepare a packaging readiness review for the next Dennis Risk Agent full-scenario semi-open test release.

This run is not an ATO-only review. ATO is the deepest sample, but the release must cover the full Dennis Risk Agent semi-open capability set.

## 2. Actions Performed

Added local planning documents:

- `outputs/intermediate/dennis_risk_agent_semi_open_release_readiness_review_v1.md`
- `outputs/intermediate/dennis_risk_agent_semi_open_release_filelist_candidate_v1.md`
- `outputs/intermediate/dennis_risk_agent_semi_open_release_exclusion_list_v1.md`
- `outputs/intermediate/dennis_risk_agent_semi_open_release_manifest_patch_plan_v1.md`
- `outputs/intermediate/dennis_risk_agent_semi_open_test_prompt_matrix_v1.md`

Updated local entry/check docs:

- `computer_use_poc/README.md`
- `computer_use_poc/smoke_tests.md`
- `computer_use_poc/capability_registry.md`

## 3. Non-actions

- No real platform access.
- No DataAgent call.
- No auth state / cookie / token / session / header read.
- No actual package build.
- No `outputs/dist` update.
- No release directory update.

## 4. Full-scenario Capability Coverage

Covered in readiness review:

- ATO / 盗号
- 反爬
- 协议攻击
- 群控 / 设备风险
- 小号 / 账号农场
- 活动反作弊
- 流量反作弊
- 导流 / 截流
- 插件 / 破解包
- 通用证据卡 / 查证计划
- 策略推荐 / 举一返三
- DataAgent query plan
- 安全防护
- question_collection

## 5. question_collection Plan

Result: included as full-scenario capability.

Key points:

- Not ATO-only.
- Records user questions, quality risk signals, candidate learning value, and review state for every scene.
- Uses `agent_observed` / `agent_suggested` / `reviewer_final`.
- Defaults to `reviewer_decision=pending`.
- Does not automatically modify Skill, Prompt, runtime summary, release package, or regression.

## 6. ATO-only Bias Check

Result: no ATO-only packaging recommendation.

ATO is marked as deep closed-loop sample, while non-ATO runtime summaries are listed as formal semi-open capabilities.

Risk to watch: if actual package only includes ATO files and excludes non-ATO runtime summaries, the package would regress into ATO-only bias.

## 7. Non-ATO Capability Gap Check

Result: no blocking gap found for readiness review.

Non-ATO capabilities are currently stronger in expert cognition, response templates, evidence planning, and strategy recommendation than in tool execution. That is acceptable for semi-open test if the package states this clearly.

Need future test prompts for:

- anti-crawler
- traffic anti-cheating
- activity anti-cheating
- cracked app / plugin risk

## 8. DataAgent Boundary Check

Result: no DataAgent over-generalization found in the new readiness plan.

Required release wording:

- DataAgent is mainly Hive / company warehouse data analysis.
- Non-ATO defaults to no DataAgent or plan-only.
- ATO expansion uses query plan unless explicitly authorized.
- DataAgent is not the universal risk-control substrate.

## 9. Sensitive Asset Leakage Risk

Potential risk exists if actual package includes full run logs, raw observations, full Skill / Prompt source, auth states, or outputs/dist history.

Mitigation:

- Apply exclusion list.
- Run package scanner before building.
- Include selected redacted summaries only.
- Confirm audience field policy for UID / DID / IP.

## 10. Blocking Items

No P0 blocker for readiness documentation.

Before actual packaging:

- Review candidate filelist.
- Apply exclusion list.
- Decide whether full Skill source is allowed or should be replaced by runtime summaries.
- Run package scanner on assembled release directory.
- Confirm field output audience policy.

## 11. Recommendation

Recommendation: ready to proceed to actual packaging after explicit user approval and filelist review.

Do not build `outputs/dist` from this review alone.
