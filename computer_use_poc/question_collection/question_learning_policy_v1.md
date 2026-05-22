# Question Learning Policy v1

## 1. Purpose

This policy decides whether a user question should enter the learning candidate queue.

Question collection is not automatic learning. It only creates candidate records for human review.

Agent can self-correct within the current answer, but self-correction is not learning deposition. If a correction happened, the question record should still keep the observed quality risk signal, such as `user_correction_detected=true` or `answer_uncertainty_high=true`.

The Agent must not judge its own answer as final quality and must not decide final deposition. It records runtime signals and candidate suggestions; `reviewer_final` makes the final assessment and action decision.

## 2. High-value Candidate Conditions

Enter candidate queue when the question is:

- A real business risk question.
- A high-frequency short question.
- Answered shallowly by the agent.
- Answered incorrectly or corrected by the user.
- A new scene.
- Ambiguous in routing.
- Missing evidence card fields.
- Requiring a new hand/tool in the future.
- Requiring DataAgent / Hive query planning.
- Triggering asset extraction or sensitive information risk.
- A multi-turn interaction that becomes reusable as a case.

## 3. Low-value Questions

Do not enter the formal candidate queue by default when:

- Pure small talk.
- Already fully covered by FAQ.
- Too little information and no follow-up.
- One-off wording rewrite.
- Obviously unauthorized request with no new safety value.
- Unrelated to Dennis Agent risk-control capabilities.

## 4. learning_value

### high

- Affects core capability.
- Can become golden case or bad case.
- Exposes obvious capability gap.
- Safety bypass or asset extraction class.
- Likely reusable by multiple users.

### medium

- Can enter FAQ.
- Useful semi-open experience sample.
- Slightly improves wording or template quality.

### low

- Already covered.
- One-off.
- Not worth formal asset update.

## 5. recommended_action Landing

| recommended_action | landing |
|---|---|
| `add_to_faq` | FAQ |
| `add_golden_case` | golden case |
| `add_bad_case` | bad case |
| `update_skill_summary` | runtime summary / domain skill |
| `update_routing` | `scene_to_capability_routing` |
| `update_evidence_template` | evidence card template |
| `add_regression_case` | regression cases |
| `generate_dataagent_query_plan` | DataAgent / Hive query plan |
| `add_asset_extraction_guard_case` | asset extraction guard regression |
| `create_case_learning_note` | case learning note |
| `need_human_review` | human review |

## 6. Human Review Gate

- `reviewer_decision=pending`: do not modify core Skill, Prompt, runtime summary, routing, release package, or regression suites.
- `reviewer_decision=accepted`: Codex may use `codex_followup_prompt` to create follow-up changes in FAQ, golden case, bad case, routing, evidence template, or regression.
- `reviewer_decision=rejected`: archive or ignore.
- `reviewer_decision=need_more_info`: ask for missing context.
- `reviewer_decision=deferred`: keep in queue but do not act.

Safety attack questions can be stored as bad case/regression candidates, but sensitive original content must be sanitized.

## 7. Hard Boundaries

- Question collection does not access real platforms.
- Question collection does not call DataAgent.
- Question collection does not modify Prompt / Skill / routing / release automatically.
- Question collection does not store cookie / token / session / header / phone plaintext.
- Model inference is not raw evidence.
- Agent self-correction does not erase the quality risk signal that triggered correction.
- `agent_suggested` is candidate metadata only and must not be presented as final judgment.
- `reviewer_final` is the only layer that can approve formal deposition.
