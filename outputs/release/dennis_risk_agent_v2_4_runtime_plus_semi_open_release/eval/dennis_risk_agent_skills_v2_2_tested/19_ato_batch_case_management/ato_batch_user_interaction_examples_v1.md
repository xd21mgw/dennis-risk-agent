# ATO Batch User Interaction Examples v1

## 1. 定位

本文件给出 ATO batch input/output contract 的用户交互样例，用于说明 Dennis Agent 在收到不同质量的批量 case 输入时，应如何降级、补字段、输出计划或生成批量分析结果。

本文件只做交互样例，不调用真实平台，不调用 DataAgent，不生成真实 observation。

## 2. 示例一：用户粘贴 10 个字段基本完整的 case

### 用户输入

用户粘贴 10 行 ATO 样本，每行包含：
- `case_id`
- `user_id`
- `event_time`
- `abnormal_action`
- `device_id`
- `user_claim`
- `available_evidence`

用户问题：
“帮我把这 10 个疑似盗号 case 做批量归因，看是否像同一类攻击链路，并给出策略方向。”

### Agent 应识别

- scene: ATO batch case analysis
- expected_capability: batch_case_analysis
- input_contract_status: schema_checked
- batch_size: within_v1_range
- route: evidence_card_generation → pattern_summary → source_coverage_summary → candidate_strategy_direction

### 应输出

- `batch_summary`
- `case_registry_quality`
- `per_case_evidence_cards`
- `batch_pattern_summary`
- `source_coverage_summary`
- `missing_evidence_summary`
- `candidate_strategy_direction`
- `manual_review_boundary`
- `next_actions`

### 关键边界

- 不直接调用 DataAgent / Hive。
- 不自动扩量。
- 不自动上线策略。
- 不自动处置用户。
- 每个核心结论必须带 evidence_source / source_quality。

### 理想回应摘要

“这 10 个 case 字段足够进入 v1 批量分析。我会先按单 case 证据卡归一化，再做跨 case 模式聚合。输出会包含候选策略方向和误伤风险，但不会自动处置或上线策略。”

## 3. 示例二：用户只给投诉描述，缺 user_id / event_time

### 用户输入

用户粘贴多段投诉描述：
“用户说账号突然发了违规作品，后来被封，怀疑被盗。还有几个类似用户反馈，但没有给 user_id 和具体时间。”

### Agent 应识别

- scene: ATO batch intake with missing required fields
- input_contract_status: needs_fields
- missing_fields:
  - `missing_user_id`
  - `missing_event_time`
  - `missing_abnormal_action` may be partial
- route: clarification / generic plan

### 不应输出

- 不输出 strong ATO conclusion。
- 不生成 batch pattern summary 作为事实结论。
- 不把投诉描述单独当作强证据。

### 应输出

- 需要补齐的字段清单。
- 可接受的 case table 格式。
- 如果用户暂时无法补齐，可输出通用 ATO 排查计划。

### 理想回应摘要

“这些投诉可以作为线索，但还不能进入 ATO batch evidence card。至少需要每个 case 的 user_id、异常时间和异常动作。当前只能标记为 clue / needs_fields，不能输出强结论。”

## 4. 示例三：用户给一批 case，但登录日志已超窗

### 用户输入

用户给 8 个 case：
- 字段包含 user_id、event_time、abnormal_action。
- 异常时间均在 30 天前。
- 用户要求判断是否盗号，并让 Agent 查登录日志。

### Agent 应识别

- scene: ATO batch case analysis with login log window risk
- input_contract_status: schema_checked
- reliable_window_status:
  - `login_log_window_incomplete`
  - `offline_hive_required`
- route: evidence_card_generation with freshness risk + DataAgent/Hive query plan only

### 应输出

- case_registry_quality：字段可用。
- per_case_evidence_cards：登录日志来源标记 freshness/window risk。
- source_coverage_summary：online login log 不覆盖异常时间。
- missing_evidence_summary：离线登录日志、token 使用、发布审计。
- next_actions：生成 DataAgent/Hive query plan，不直接调用 DataAgent。

### 不应输出

- 不把 online login log no_data 写为“无异常登录”。
- 不把 no_data 写为反证。
- 不推断日志被清理。
- 不直接调用 DataAgent / Hive。

### 理想回应摘要

“这些 case 可以进入批量分析，但登录行为需要标记为窗口不完整。在线统一登录日志超过可靠窗口后 no_data 只能表示数据缺口，不能作为无盗号反证。下一步应输出 Hive / 离线日志补查问题清单。”

