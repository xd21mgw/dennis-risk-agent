# Semi-open Release Package Run v1

## 1. 本轮目标

实际组装 Dennis Risk Agent 全场景半开放测试 release 包：

- release name: `dennis_risk_agent_v2_4_runtime_plus_semi_open_release`
- release dir: `outputs/release/dennis_risk_agent_v2_4_runtime_plus_semi_open_release/`
- tarball: `outputs/dist/dennis_risk_agent_v2_4_runtime_plus_semi_open_release.tar.gz`

本轮只做本地打包，不访问真实平台，不调用 DataAgent，不读取认证态，不更新正式 release/dist 之外的任何历史包。

## 2. 依据文件

实际打包前已依据：

- `outputs/intermediate/dennis_risk_agent_semi_open_release_readiness_review_v1.md`
- `outputs/intermediate/dennis_risk_agent_semi_open_release_filelist_candidate_v1.md`
- `outputs/intermediate/dennis_risk_agent_semi_open_release_exclusion_list_v1.md`
- `outputs/intermediate/dennis_risk_agent_semi_open_release_manifest_patch_plan_v1.md`
- `computer_use_poc/question_collection/runtime_append_only_logging_contract_v1.md`
- `computer_use_poc/question_collection/runtime_question_record_sample_v1.jsonl`
- `computer_use_poc/question_collection/runtime_logging_smoke_test_v1.md`
- `computer_use_poc/question_collection/runtime_question_record_collector_stub_v1.py`

## 3. 实际纳入能力

### 3.1 ATO / 盗号

- ATO 是当前最完整的深度样板能力。
- 包含 batch contracts、evidence card、pattern summary、status transition、manual review boundary、expansion plan、pilot checklist、real case dry run / final summary / closure summary。

### 3.2 非 ATO 正式能力

- 反爬 runtime summary。
- 协议攻击 runtime summary。
- 群控 / 设备风险 runtime summary。
- 小号 / 账号农场 / 黑产账号矩阵样板。
- 活动反作弊 runtime summary。
- 流量反作弊 runtime summary。
- 导流 / 截流 runtime summary。
- 插件 / 破解包 runtime summary。

### 3.3 通用证据卡 / 查证计划

- `strong / medium / weak / counter / missing evidence`。
- `evidence_source / source_quality / freshness / permission / reliability`。
- model inference 不是 raw evidence。
- manual input 不能单独作为 strong conclusion。
- 登录日志超窗 no_data 不能作为 counter evidence。

### 3.4 安全与资产防抽取

- credential plaintext 永不输出。
- prompt / skill / source code / API key 抽取拒绝。
- broad-share 使用 `safe_ref` / partial mask / count / distribution。

### 3.5 question_collection

- 全场景用户问题观测与候选学习队列。
- `agent_observed` / `agent_suggested` / `reviewer_final` 三层结构。
- append-only runtime logging contract。
- template CSV 只读。
- runtime 写入位置为 `runtime_logs/question_collection/question_records_YYYYMMDD.jsonl`。
- runtime 不自动写 `accepted`。
- runtime 不自动改 Skill / Prompt / runtime summary / release 包。

## 4. 实际 release 目录

实际生成的 release 目录为：

```text
outputs/release/dennis_risk_agent_v2_4_runtime_plus_semi_open_release/
```

目录内包含：

- root `README.md`
- root `dennis_risk_agent_v2_4_runtime_plus_semi_open_manifest_v1.md`
- `AGENTS.md`
- `computer_use_poc/` 选定 runtime / routing / safety / question_collection / validation / user guide / prompt matrix / selected run logs
- `skills/.../11_runtime_summaries/` 选定非 ATO runtime summaries
- `eval/.../19_ato_batch_case_management/` 选定 ATO batch templates
- `eval/.../20_black_market_account_matrix_batch/` 选定 black market matrix templates

## 5. question_collection 映射结果

已纳入：

- `computer_use_poc/question_collection/README.md`
- `computer_use_poc/question_collection/question_record_schema_v1.md`
- `computer_use_poc/question_collection/question_learning_policy_v1.md`
- `computer_use_poc/question_collection/question_learning_candidate_queue_v1.csv`
- `computer_use_poc/question_collection/user_feedback_capture_v1.md`
- `computer_use_poc/question_collection/case_learning_note_template_v1.md`
- `computer_use_poc/question_collection/runtime_append_only_logging_contract_v1.md`
- `computer_use_poc/question_collection/runtime_question_record_sample_v1.jsonl`
- `computer_use_poc/question_collection/runtime_logging_smoke_test_v1.md`
- `computer_use_poc/question_collection/runtime_question_record_collector_stub_v1.py`

release README 与 manifest 已明确：

- `question_learning_candidate_queue_v1.csv` 是模板，不承接真实用户问题。
- 真实问题写 `runtime_logs/question_collection/question_records_YYYYMMDD.jsonl`。
- runtime 只记账，不自动改脑。

## 6. exclusion list 应用结果

已明确不纳入：

- `auth-state categorys/`、`.ks_sso/`。
- cookie / token / session / header / auth state 明文。
- outputs/dist 旧包。
- 真实 observation 原始数据。
- 未脱敏平台截图。
- 历史 POC 全量 run logs。
- 未审核 eval pilot 文件。
- 完整源码 / 完整 Prompt / 完整 Skill / 完整 case 全量资产。

本次构建未发现 hard-fail 路径。

## 7. package scanner 结果

扫描命令：

```bash
python3 computer_use_poc/package_asset_scanner.py outputs/release/dennis_risk_agent_v2_4_runtime_plus_semi_open_release
python3 computer_use_poc/package_asset_scanner.py outputs/release/dennis_risk_agent_v2_4_runtime_plus_semi_open_release --json
```

结果摘要：

- status: `warning`
- fail: `0`
- warning: `63`
- pass: `6`
- total findings: `69`

结论：

- 没有 hard exclusion 违规。
- warning 主要来自选定的 POC / run log / prompt matrix / runtime summary 文件名。
- 这些 warning 已在 release README / manifest 中解释为选定摘要、模板、样例和受控运行态资产，不是全量历史资产。

## 8. tarball

已生成：

```text
outputs/dist/dennis_risk_agent_v2_4_runtime_plus_semi_open_release.tar.gz
```

## 9. git diff --check

- 本轮 `git diff --check` 已通过。

## 10. 阻塞项

无 P0 阻塞。

非阻塞 TODO：

- 半开放 runtime 的真实 append-only logging 联调后续补齐。
- APP / Web 实际部署验证后续补齐。
- 若后续反馈需要，可再增补非 ATO runtime summaries。

## 11. 是否建议人工抽检

建议。

抽检重点：

- release README 是否明确不是 ATO-only。
- `question_collection` 是否明确 template CSV 只读、runtime append-only。
- 安全边界是否没有带入 cookie / token / session / header / auth state。
- selected run logs 是否都是 redacted summary，而非 raw 原始过程。

