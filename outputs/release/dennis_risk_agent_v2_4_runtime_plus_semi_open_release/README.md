# Dennis Risk Agent v2.4 Runtime Plus Semi-open Release

## 1. Package定位

这是 Dennis Risk Agent 的**全场景半开放测试 release 包**，不是 ATO-only 包。

定位如下：

- ATO / 盗号是当前最完整的深度样板能力。
- 非 ATO 场景是正式半开放能力，覆盖反爬、协议攻击、群控 / 设备风险、小号 / 账号农场、活动反作弊、流量反作弊、导流 / 截流、插件 / 破解包、通用证据卡 / 查证计划、策略推荐和安全防护。
- `question_collection` 是全场景用户问题观测与学习候选队列，不只服务 ATO。
- `DataAgent` 只定位为 Hive / 公司数仓取数分析能力，不是全能风控底座。

## 2. 目录说明

release 目录内的主要模块：

- `computer_use_poc/README.md`：半开放入口总说明。
- `computer_use_poc/multi_entry_runtime_guard_v1.md`：KIM / APP / Web 统一 runtime guard。
- `computer_use_poc/scene_to_capability_routing.md`：场景到 capability 路由。
- `computer_use_poc/answer_experience_templates.md`：回答模板。
- `computer_use_poc/field_output_classification_policy_v1.md`：字段输出分层。
- `computer_use_poc/sensitive_field_redaction_policy.md`：敏感字段脱敏。
- `computer_use_poc/approval_policy.md`：审批与拒绝边界。
- `computer_use_poc/runtime_semi_open_user_guide_v1.md`：用户使用说明。
- `computer_use_poc/runtime_validation_cases_v1.yaml`：半开放 validation cases。
- `computer_use_poc/smoke_tests.md`：文档级 smoke tests。
- `computer_use_poc/security_preflight_*`：本地 preflight / validator / contract / test cases。
- `computer_use_poc/asset_extraction_guard_*`：资产抽取防护与瘦身规则。
- `computer_use_poc/question_collection/`：全场景问题收集与 append-only logging contract。
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/11_runtime_summaries/`：非 ATO runtime summaries。
- `eval/dennis_risk_agent_skills_v2_2_tested/19_ato_batch_case_management/`：ATO batch contracts / templates。
- `eval/dennis_risk_agent_skills_v2_2_tested/20_black_market_account_matrix_batch/`：black market matrix batch templates。

## 3. 用户如何使用

推荐先读：

1. `AGENTS.md`
2. 本 README
3. `computer_use_poc/runtime_semi_open_user_guide_v1.md`
4. `computer_use_poc/multi_entry_runtime_guard_v1.md`
5. `computer_use_poc/scene_to_capability_routing.md`
6. `computer_use_poc/answer_experience_templates.md`
7. `computer_use_poc/smoke_tests.md`

用户提问时：

- ATO 单 case：可进入只读 execution，输出 concise evidence card。
- ATO 举一返三：必须 plan mode only，只输出 DataAgent / Hive query plan。
- black_market_account_matrix paused branch：必须 fast_ack / lightweight closure，不进入深挖。
- 其他非 ATO 场景：默认先给专家认知、证据规划和策略建议，不默认调用 DataAgent。

## 4. question_collection

`question_collection` 在本 release 中正式作为全场景能力纳入。

核心口径：

- `question_learning_candidate_queue_v1.csv` 是只读模板，不承接真实用户问题。
- 真实用户问题必须 append-only 写入：

```text
runtime_logs/question_collection/question_records_YYYYMMDD.jsonl
```

- `question_record` 必须包含：
  - `agent_observed`
  - `agent_suggested`
  - `reviewer_final`
- `reviewer_final.reviewer_decision` 默认 `pending`。
- runtime 不自动写 `accepted`。
- runtime 不自动改 Skill / Prompt / runtime summary / release 包。

## 5. 安全与资产边界

本 release 明确禁止输出或纳入：

- 完整源码。
- 完整 Prompt / Skill 原文。
- cookie / token / session / header / auth state 明文。
- 未脱敏平台截图。
- 真实 observation 原始数据。
- 历史 POC 全量 run logs。
- outputs/dist 旧包。

允许输出或纳入：

- 高层设计和模块职责。
- 证据卡与查证计划。
- 风险实体字段的 safe_ref / partial mask / count / distribution。
- 正常的 runtime summaries 和模板文件。

## 6. Package Scanner

打包前必须运行 package scanner。

scanner 结果的解释方式：

- `pass`：无高风险路径。
- `warning`：存在 selected summary / prompt / POC / run log 路径，需要人工确认是否属于受控摘要。
- `fail`：存在 `.git`、auth state、cookie / token / session、outputs/dist 旧包、nested release 等禁止路径，必须回收。

本 release 只允许保留被审核过的 selected summary / template / sample / smoke test / run log。

## 7. 不支持事项

本 release 不支持：

- 自动处置。
- 自动上线策略。
- 自动改脑。
- 默认自动调用 DataAgent。
- 把 DataAgent 当成万能风控底座。
- 把 question_collection 当成已自动接入真实 runtime 的自动学习系统。

## 8. Release 目录与 tarball

- release 目录：`outputs/release/dennis_risk_agent_v2_4_runtime_plus_semi_open_release/`
- release manifest：`outputs/release/dennis_risk_agent_v2_4_runtime_plus_semi_open_release/dennis_risk_agent_v2_4_runtime_plus_semi_open_manifest_v1.md`
- tarball：`outputs/dist/dennis_risk_agent_v2_4_runtime_plus_semi_open_release.tar.gz`
