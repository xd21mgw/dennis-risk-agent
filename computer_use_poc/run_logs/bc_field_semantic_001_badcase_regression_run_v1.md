# BC-FIELD-SEMANTIC-001 Bad Case Regression Run v1

## 1. Background

This bad case records a field-semantics correction for a client-version downgrade / suspected protocol-login case.

Observed issue:

- The Agent saw `mods=['POST', ...]` in logs.
- It misread `POST` as `HTTP method=POST`.
- It then inferred that the attacker directly called backend APIs with HTTP POST.

Correction:

- `mod` / `mods` / `model` / `device_model` are device model or device-reported fields.
- `POST` in those fields is not HTTP method evidence.
- It can only indicate device model anomaly, placeholder anomaly, or spoofed-value anomaly.

## 2. Correct Field Semantics

| field | meaning | can prove HTTP method |
|---|---|---|
| `mod` | device model / device-reported model field | no |
| `mods` | device model list / device-reported model field | no |
| `model` | device model | no |
| `device_model` | device model | no |
| `method` | request method | yes |
| `request_method` | request method | yes |
| `http_method` | request method | yes |
| `requestMethod` | request method | yes |

## 3. Required Judgment Rule

Do not write:

- "Because `mod='POST'`, the attacker used HTTP POST to directly call backend APIs."

Use this corrected wording:

- "`POST` appears in a device model field, so it is a device-reporting anomaly or spoofed-value anomaly. It does not prove HTTP POST direct API calls."

## 4. Protocol Login Evidence Requirement

Protocol-login judgment must rely on combined evidence:

- abnormal `mod` / non-real device model / encrypted-looking string;
- mixed app versions;
- high-frequency old-version usage;
- inconsistent `did`;
- differences between normal device and downgraded device;
- missing frontend behavior or abnormal request chain.

`POST` alone cannot support a protocol-login conclusion.

## 5. Regression Case

Input:

```text
客户端版本降级疑似协议上号，日志里 mods=['POST', 'v1_like_string']，同时有旧版本高频、did 不一致和前端行为缺失。请判断是不是攻击者用 HTTP POST 直调后端 API。
```

Expected:

- Do not interpret `mods=['POST']` as HTTP method.
- Explain `POST` as a device model field anomaly / placeholder anomaly / spoofed value.
- State that only `method` / `request_method` / `http_method` / `requestMethod` can prove request method.
- State that protocol-login requires combined evidence.
- Ask for version mix, old-version frequency, `did` mismatch, device difference, frontend behavior, and request-chain evidence.

## 6. Files Updated

- `skills/dennis_risk_agent_skills_v2_1_focused_deep/03_attack_skills/protocol_attack_expert_skill.md`
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/11_runtime_summaries/protocol_attack_runtime_summary_v1.md`
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/02_domain_skills/account_security_expert_skill.md`
- `computer_use_poc/answer_experience_templates.md`
- `computer_use_poc/runtime_validation_cases_v1.yaml`
- `computer_use_poc/smoke_tests.md`

## 7. Boundaries

- real_platform_called: false
- DataAgent_called: false
- auth-state category_read: false
- release_updated: false
- outputs_dist_updated: false
- git_committed: false
