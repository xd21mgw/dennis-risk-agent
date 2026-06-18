# Challenge Regression Coverage Audit

Scope: audit of `challenge_registry.md` completeness and regression readiness for P1.1 dynamic LLM commonality discovery. This is documentation-only and does not claim implementation, platform execution, Hive/DataAgent execution, or code validation.

## Completeness Verdict

- registry_complete: true for the challenges visible from this repository, `/private/tmp` P1.1 run outputs, cold/gap-focused review outputs in this conversation, and user-pasted prompts/feedback.
- Not complete for unknown private discussion outside this thread or missing runlogs not readable under `/private/tmp`.
- can_start_mechanization: false.

The registry now contains 29 challenges. The previous 20 entries covered the main themes, but several were merged across different capability domains. This audit split them when the user challenge tested a different mechanism.

## Merged And Split Items

| current_challenge | merged_from / aliases | audit_decision |
|---|---|---|
| CH-001 | old CH-001; prior_discovery_contamination; cold_start_purity | Kept as autonomous proof challenge. |
| CH-002 | split from old CH-012; raw_field_coverage; full_inventory_claim | Split out because full raw inventory coverage is different from parsed inventory. |
| CH-003 | old CH-002; split from old CH-012; parsed_visibility_gap | Kept separate because parsed path coverage is an independent blocker. |
| CH-004 | split from old CH-003; requestParam_data; logContent_params; extraParam | Split out for archives/login containers. |
| CH-005 | split from old CH-003 and old CH-017; originalLog_parse; labelInfo_parse; appList_parse | Split out for Weapon/device containers. |
| CH-006 | old CH-004, old CH-005, old CH-016; profile_lure_history; four_items_payload | Merged because these all describe the same profile/history lure false-miss family. |
| CH-007 | split from old CH-004; URL_domain_OCR_QR | Split out because URL/OCR/QR closure is source enrichment, not just profile text parsing. |
| CH-008 | split from old CH-014; rebind_mobile_chain; reset_bind_verify | Split out because account mutation chain is event reconstruction, not generic replay failure. |
| CH-009 | new from latest user checklist; wave4_account_mutation | Added because old registry did not isolate wave4 dominant method family. |
| CH-010 | new from latest user checklist; country_code_hk; Zenlayer; IDC | Added because old registry did not isolate network/IDC/environment cluster. |
| CH-011 | new from latest user checklist; boardPlatform_context | Added because boardPlatform must be event environment, not a standalone signal. |
| CH-012 | old CH-007; weapon_header_runtime | Kept as field-level Weapon header template challenge. |
| CH-013 | old CH-017 split; accessibility; remoteControl; random_package_service | Split out from appList because toolchain taxonomy is a different mechanism. |
| CH-014 | old CH-005 split, old CH-017 split; appList_columns; device_fields | Split out for appList/device field coverage matrix. |
| CH-015 | old CH-006; low_bootcount_track_high_duration | Kept as cross-source chain challenge. |
| CH-016 | split from old CH-006; raw_device_id_join; lineage_strictness | Split out because strict device join is a prerequisite mechanism. |
| CH-017 | old CH-008; high_visit_low_content; social_funnel | Kept but now includes profile visit, content production, and relation counters. |
| CH-018 | new from latest user checklist; near_full_page; page_cap | Added because pagination cap false positive was missing. |
| CH-019 | old CH-009; top_value_fp; fixed_schema_fp | Kept as generic schema/noise gate. |
| CH-020 | split from old CH-012; source_gap_not_counter_evidence | Split out because source quality boundary differs from field inventory coverage. |
| CH-021 | old CH-010; wave_feature_contamination | Kept as wave isolation challenge. |
| CH-022 | old CH-011 split; autonomous_vs_targeted | Split out to force candidate provenance labels. |
| CH-023 | old CH-013; full_autonomous_boundary | Kept as readiness verdict, currently report-only. |
| CH-024 | old CH-014; replay_unsolved | Kept as self-repair failure import challenge. |
| CH-025 | old CH-015; output_inconsistency | Kept as parser drift contradiction. |
| CH-026 | old CH-016; wave1_lure_false_miss | Kept as fact-table recall failure. |
| CH-027 | old CH-018; baseline_needed | Kept as L4/L6 validation boundary. |
| CH-028 | old CH-019; reproducibility_gap | Kept as candidate provenance/replay gap. |
| CH-029 | old CH-020; challenge_learning_asset | Kept as registry maintenance challenge. |

## User Checklist Coverage

| required_check | registry_challenge | current_status | audit_note |
|---|---:|---|---|
| full_action_field_inventory 是否真实覆盖每个 action/raw field | CH-002 | PARTIAL_COVERED | File exists, but no raw-vs-inventory diff proof. |
| parsed_field_inventory 缺失 | CH-003 | DATA_GAP | Independent parsed inventory missing. |
| requestParam / logContent / extraParam container deep parse | CH-004 | TARGETED_ONLY | Some manual parsing; no general mechanism. |
| profile/history lure，当前 profile 为空但历史提交有导流 | CH-006 | SCANNER_GAP | User confirmed wave1-wave3 should hit but scanner missed. |
| URL/domain/OCR/QR 是否闭合 | CH-007 | DATA_GAP | Blind eval marks this as data gap. |
| rebind/mobile 是否按 account mutation chain 而非单 endpoint | CH-008 | PARTIAL_COVERED | URI evidence exists, chain builder missing. |
| wave4 account mutation 主手法族 | CH-009 | TARGETED_ONLY | Added as explicit challenge; not independently proven as automatic. |
| country_code=hk / IDC / Zenlayer 是否按环境簇处理 | CH-010 | PARTIAL_COVERED | Direction known, source/path closure missing. |
| boardPlatform 是否作为 event environment，而非单字段强推 | CH-011 | PARTIAL_COVERED | Needs environment-field role classifier. |
| weaponDecodeHeader 逐字段模板 | CH-012 | PARTIAL_COVERED | Wave5 field list exists; baseline and per-wave coverage missing. |
| accessibility / remoteControl / 随机包名服务组件 | CH-013 | SCANNER_GAP | Toolchain taxonomy missing. |
| appList / device fields 逐列与 coverage gap | CH-014 | DATA_GAP | Per-column coverage matrix missing. |
| bootCount + Track duration + user-device lineage / any-risk-device | CH-015 | PARTIAL_COVERED | Wave5 discovered, strict lineage incomplete. |
| strict device_id join 是否缺失 | CH-016 | DATA_GAP | No raw device-id join audit. |
| social funnel：高主页访问 + 低内容产出 | CH-017 | PARTIAL_COVERED | Profile/count part exists; visit event is gap. |
| follow_list_near_full_page 分页误判 | CH-018 | NOT_COVERED | Newly added; no current review coverage. |
| schema/top value 假共性 | CH-019 | PARTIAL_COVERED | Report-level guard exists; mechanism missing. |
| source gap vs no risk | CH-020 | PARTIAL_COVERED | Report-level boundary exists; candidate gate missing. |
| wave4 / wave5 不能互相套特征 | CH-021 | PARTIAL_COVERED | Report split exists; provenance guard missing. |
| 哪些是无提示主动发现，哪些是 TARGETED_ONLY | CH-022 | TARGETED_ONLY | Needs candidate provenance labels. |
| full autonomous 是否仍未证明 | CH-023 | REPORT_ONLY | Verdict exists; readiness gate missing. |

## Coverage Matrix

| challenge_type | challenge_ids | coverage_summary |
|---|---|---|
| field_visibility | CH-002, CH-012, CH-014 | Raw/Weapon field visibility is partially reviewed; appList/device column coverage remains a data gap. |
| parsed_visibility | CH-003 | Parsed inventory is missing. |
| container_parse | CH-004, CH-005, CH-006, CH-013 | Some targeted parsing exists; profile lure and device toolchain still show scanner/container gaps. |
| event_reconstruction | CH-008 | Account mutation chain evidence exists but chain assembly is incomplete. |
| cross_source_chain | CH-010, CH-015, CH-016, CH-017 | Cross-source hypotheses exist; strict joins, visit events, and network enrichment remain incomplete. |
| wave_family | CH-009, CH-021 | Per-wave separation is partially handled; wave4 dominant family needs explicit scoring. |
| schema_noise | CH-011, CH-018, CH-019 | Generic schema/noise concern is covered; pagination and environment-field role guards are not mechanized. |
| source_gap | CH-007, CH-020 | Source gap boundaries are named; URL/OCR/QR and source-quality-to-candidate gating remain unresolved. |
| validator_gap | CH-024, CH-025, CH-026, CH-027, CH-028 | Several replay/parser drift/provenance failures are documented but not automated. |
| autonomous_proof | CH-001, CH-022, CH-023, CH-029 | Cold-start purity and provenance are only partially controlled; full autonomous remains unproven. |

## Status Counts

| status | count | challenge_ids |
|---|---:|---|
| FULL_COVERED | 1 | CH-029 |
| PARTIAL_COVERED | 12 | CH-001, CH-002, CH-008, CH-010, CH-011, CH-012, CH-015, CH-017, CH-019, CH-020, CH-021, CH-027 |
| TARGETED_ONLY | 3 | CH-004, CH-009, CH-022 |
| DATA_GAP | 5 | CH-003, CH-005, CH-007, CH-014, CH-016 |
| SCANNER_GAP | 4 | CH-006, CH-013, CH-024, CH-026 |
| NOT_COVERED | 3 | CH-018, CH-025, CH-028 |
| REPORT_ONLY | 1 | CH-023 |

## Mechanization Blockers

The registry should not move directly into implementation until these P0 blockers are resolved or explicitly accepted as scoped gaps:

1. Build or specify independent `parsed_field_inventory` with parsed paths and coverage.
2. Add raw full-action inventory diff against raw bundles.
3. Create container parser coverage for `requestParam/logContent/extraParam` and Weapon `originalLog/labelInfo/accessibilitySvc/appList`.
4. Add profile/history lure replay using the user-stated four-item sample intent as expected recall.
5. Add strict raw `device_id` lineage audit before Track + Weapon chain claims.
6. Separate autonomous blind discoveries from user-targeted follow-up discoveries.
7. Add candidate provenance records: raw path, parsed path, support users, parser version, replay command.
8. Add parser drift detection for conflicting runner outputs.
9. Add schema/noise gates for pagination caps and environment-only fields.

## Final Summary

```yaml
registry_complete: true
total_challenges: 29
full_covered_count: 1
partial_covered_count: 12
targeted_only_count: 3
data_gap_count: 5
scanner_gap_count: 4
not_covered_count: 3
report_only_count: 1
can_start_mechanization: false
must_fix_before_mechanization:
  - parsed_field_inventory_missing
  - full_action_inventory_raw_diff_missing
  - container_parser_coverage_missing
  - profile_history_lure_expected_recall_not_closed
  - strict_device_id_join_missing
  - autonomous_vs_targeted_provenance_missing
  - candidate_replay_provenance_missing
  - parser_drift_detector_missing
  - schema_noise_pagination_environment_guards_missing
```
