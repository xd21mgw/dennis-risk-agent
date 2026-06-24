# Profile Lure Expected Path Registry

This document is a registry only. It does not implement a parser, add tests, access platforms, call Hive/DataAgent, or prove full autonomous discovery.

## Scope

- Canonical family: `profile_lure_payload`
- Required text fields for any hit: `raw_text_preview`, `normalized_text`, `normalization_steps`, `matched_lure_tokens`
- Drift gate statuses: `profile_lure_detected`, `true_no_evidence`, `source_gap`, `parser_gap`, `path_drift`, `business_field_gap`, `needs_more_source`
- URL/OCR/QR stays `data_gap` in this phase.

## Expected Paths

| path_id | source_action | parsed_path | payload_role | default_signal_level | gap boundary |
|---|---|---|---|---|---|
| `login_logs_search.logContent.params.data` | `login_logs_search` | `logContent.params.data` | current submission payload | high-value | source/parser gap if login source incomplete or nested params parse fails |
| `archives_review_logs.desc.original_user_payload` | `archives_review_logs` | `data.desc` | historical audit payload containing original submitted text | high-value | split from enforcement-only text |
| `archives_review_logs.desc.enforcement_description` | `archives_review_logs` | `data.desc` | enforcement description | supporting | supports chain, does not replace original user payload |
| `archives_user_analysis.requestParam.data` | `archives_user_analysis` | `requestParam.data` | profile mutation payload | high-value | auth/timeout/raw_absent is source gap, not no evidence |
| `archives_private_message_search.content` | `archives_private_message_search` | `data.list.content` | private message contact script | supporting | low-specificity greeting downgrades to report-only |
| `archives_private_message_search.contentNormalized` | `archives_private_message_search` | `data.list.contentNormalized` | normalized private message text | supporting | keep raw preview alongside normalized field |
| `archives_user_profile.current_profile_text` | `archives_user_profile` | `profile.desc/signature/intro/nickname` | current profile payload | supporting | current empty is business_field_gap, not history no-evidence |
| `archives_negative_or_punish.desc` | `archives_negative_report` / `archives_punish_status` | `desc` / punish desc | enforcement support | supporting | not a substitute for submitted lure payload |
| `photo_or_content_ocr_text` | future OCR-capable source | OCR/image text | OCR lure payload | data_gap | no implementation claimed |
| `url_domain_qr_payload` | future URL/QR/domain source | URL/domain/QR payload | URL/domain/QR lure payload | data_gap | no implementation claimed |

## Review Logs Split

`archives_review_logs.desc` must be emitted as two semantic roles when applicable:

- `original_user_payload`: old intro, submitted intro, profile text, signature, nickname, or domain/contact text copied from user content.
- `enforcement_description`: clear intro, intro behavior ban, clear avatar, avatar behavior ban, negative operation, public/same-city no distribution, or other punishment wording.

The enforcement role is supporting evidence. It must not be used to claim a lure payload unless original submitted text is also present.

## Text Normalization Contract

Every normalized text observation must preserve:

- `raw_text_preview`: short raw payload excerpt for review.
- `normalized_text`: deterministic text used for matching.
- `normalization_steps`: ordered transformations applied.
- `matched_lure_tokens`: contact, domain, platform, carrier, or obfuscation tokens matched.

Recommended normalization steps:

1. `unicode_nfkc`
2. `strip_zero_width_and_invisible_joiners`
3. `preserve_raw_preview_before_symbol_cleanup`
4. `collapse_whitespace_and_newlines`
5. `lowercase_ascii`
6. `remove_decorative_emoji_for_matching_only`
7. `normalize_full_width_ascii`
8. `homophone_or_variant_token_map`
9. `contact_intent_tokenize`
10. `domain_or_url_extract_when_available`
11. `qr_or_ocr_placeholder_gap_when_not_available`

Token groups:

| group | examples |
|---|---|
| contact platform | 微信, 微, 薇, 徽, 信, wx, vx, v信, q, qq, 扣 |
| contact intent | 加我, 留下联系方式, 联系方式, 私信, 联系, 互动, 关注了我, 为您提供更好的服务 |
| diversion carrier | `.cc`, http, https, 浏览器, 搜索, 复制, 口令, 二维码, qr |
| obfuscation shape | zero-width split, emoji interleaving, homophone substitution, mixed case, linebreak split |

## Drift Gate

If a future wave does not find `profile_lure_payload`, it cannot directly conclude no commonality. It must first emit one fixed status:

| status | meaning |
|---|---|
| `profile_lure_detected` | Expected path is completed, parsed, and matched to lure/contact/diversion semantics. |
| `true_no_evidence` | Required sources completed, raw present, parser succeeded, expected paths checked, and no lure semantics found. |
| `source_gap` | Source auth_failed, timeout, blocked, not_called, or incomplete. |
| `parser_gap` | Raw exists but container parsing failed or parsed child path is absent due parser error. |
| `path_drift` | Parser succeeded but payload moved to a semantically equivalent new path. |
| `business_field_gap` | Transport/parser completed but business field is empty or not returned. |
| `needs_more_source` | URL/OCR/QR/domain enrichment or another source is required. |

## Current Anchors

- D2: `login_logs_search.logContent.params.data` closed as current profile submission payload, 15/15.
- new_holdout_C: `archives_review_logs.desc` closed as profile history lure payload, 8/8.
- Current profile empty does not negate review-history or login-params hits.
- URL/OCR/QR remains `data_gap`; no implementation is claimed.
