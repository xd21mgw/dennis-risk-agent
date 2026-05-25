# Dennis Risk Agent Runtime Validation Overlay v1

## Package position

This is a runtime overlay package for internal Agent live workspace integration. It is not a formal major release and it is not an upload-ready `outputs/dist` package by itself.

Use this package to overlay the semi-open runtime validation patch, feedback loop contract, evidence quality patch, batch risk clustering analysis pack, and release preflight gate into a live workspace after internal review.

## Intended use

- Internal Agent runtime overlay.
- Staging or live workspace validation.
- Runtime routing, answer template, feedback writer, batch clustering, and safety preflight integration.

## Preconditions

- Do not access real platforms during overlay validation.
- Do not call DataAgent during overlay validation.
- Do not change auth or gateway components.
- Do not run real business queries.
- Do not upload this package to cloud storage.
- Do not place runtime credential material in this package.
- Keep template queue files separate from live runtime output.

## Overlay steps

1. Review `OVERLAY_MANIFEST.md`.
2. Copy each runtime file to its target live path.
3. Keep local-test-only files out of live runtime unless the release owner explicitly approves them.
4. Keep the template feedback queue as a template only.
5. Configure live feedback output to `runtime_logs/question_collection/question_learning_candidate_queue_v1.csv`.
6. Run the validation steps in `OVERLAY_CHECKLIST.md`.
7. Before creating any transfer archive or final package, run:

```bash
python3 computer_use_poc/release_preflight_check.py outputs/release/dennis_risk_agent_runtime_validation_overlay_v1
```

## Live validation

Validate:

- KIM/webchat risk routing spawns Dennis Risk Agent.
- Follow-up prompts inherit prior risk context unless a new batch fingerprint is present.
- Evidence cards separate facts, claims, inference, hypothesis, and missing evidence.
- Batch risk clustering emits clusters, representative cases, abnormal correlation matrix, and validation plan.
- Browser loop and blocked source handling downgrade to partial evidence card.
- Feedback writer appends high-value learning candidates to the runtime output path.
- Release preflight passes before any archive is created.

## Rollback

- Keep a pre-overlay snapshot of every live file.
- Restore only overlaid runtime files if rollback is needed.
- Do not mutate live auth state, browser state, or append-only logs during rollback.
- If feedback writing misbehaves, disable the live caller hook first and inspect only safe summaries.

## Forbidden package content

Do not add credential material, browser state, SSO state, complete prompt source, complete mother-body skill source, full historical logs, real raw case samples, raw internal platform payloads, high-sensitive personal data, unredacted screenshots, previous dist archives, or platform-specific private paths.

