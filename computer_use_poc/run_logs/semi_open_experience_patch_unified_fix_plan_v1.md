# Semi-open Experience Patch Unified Fix Plan v1

## 1. 本轮目标

Dennis Risk Agent 半开放 Pilot 已上线，当前 P0=0。release 包、gateway config、live workspace overlay、Python runner、watchdog slim guard、安全注入测试、ATO 业务短问均已通过。

本轮不处理安全 P0，不重新做云端部署配置，只沉淀 semi-open experience patch v1 的路由规则、回答模板、测试样例和回归基线。

## 2. 输入材料

- Q1-Q20 半开放自动测试集。
- KIM 通道真实 session 质量评估。

## 3. 当前结论

整体状态：基本可用但需修。

已通过：

- prompt injection / API key / cookie / token / session / header 泄露测试正确拒绝。
- 无写操作，无越权处置。
- 登录日志 no_data / timeout / blocked 不作为无风险强反证。
- 设备关联不能直接定性作弊。
- 模型分不能单独作为 strong evidence。
- 用户反馈不能单独作为客观事实。

主要问题：

- 显式单用户查询偶发空研判。
- ATO 单案偶发绕路 DataAgent / 子 agent。
- 证据边界问题有时自动查平台，路由不稳定。
- 策略设计类问题被 `user_id` 拉偏到 execution。
- 3+ 用户批量逐个在线查导致不稳定。
- 举一返三 / 策略推荐 plan_mode 固化不足。
- 非 ATO 场景误进 browser。
- 档案中心 / 天狮 / browser / 2FA / HTML 返回降级不够快。
- timeout 有时裸返回。
- API / SSO / JSON 解析稳定性需要增强。
- sso_session.py cookie 到 agent-browser Chrome 的桥接方案需要沉淀。
- 专家问答和批量分析需要控长。
- 设备 SDK 类问题需要直接给三种解读。

## 4. 统一修复策略

### 4.1 显式查询不空研判

新增 `explicit_query_not_empty_analysis`：

- 触发词：帮我查、帮我看、看这个用户、看近期登录、看设备关联、看策略命中、看档案画像、判断具体 case、这个 user_id 是否疑似 ATO、这个 device_id 是否异常。
- 行为：进入 `single_entity_execution_mode` 或输出 partial evidence card。
- 禁止：只给方法论。

### 4.2 ATO 单案不绕 DataAgent

新增 / 强化 `single_entity_execution_mode`：

- 明确 `user_id` / `event_time` / `abnormal_action` 时，优先在线只读 observation。
- 不默认走 DataAgent，不默认只给方法论。
- timeout 默认 180s，复杂单用户 240s。
- 失败时输出 partial evidence card。

DataAgent 仅在超出在线窗口、3+ 批量、长窗口离线补查、复杂 SQL/Hive、发布链路 / token 长周期 / 跨表分析时，经确认后进入 query plan 或离线流程。

### 4.3 证据边界默认纯分析

新增 `evidence_boundary_mode`：

- 默认不查平台。
- 30s 内短答。
- no_data / timeout / blocked 不是反证。
- 设备关联、模型分、用户反馈不能单独支撑强结论。

### 4.4 策略设计带 user_id 仍 plan_mode

新增 `strategy_plan_mode_priority`：

- 灰度验证、误伤控制、策略推荐、举一返三、监控指标、治理方案、怎么做、如何设计，默认 `strategy_recommendation_plan_mode`。
- 即使带 `user_id` 也不自动查平台。

### 4.5 3+ 批量默认 plan_mode

新增 `batch_plan_mode`：

- 1-2 个实体可 execution。
- 3+ 用户 / 设备或批量语义默认 plan。
- 不逐个在线查。

### 4.6 非 ATO 不默认 browser

新增 `non_ato_browser_guard`：

- 反爬、协议、导流截流、活动作弊、渠道套利、群控泛化分析先专家分析。
- 不默认 browser / 档案中心。

### 4.7 browser / 2FA / HTML 快速降级

新增 / 强化：

- `browser_session_bridge`
- `auth_html_fast_fallback`
- `platform_permission_degradation_template`

标准状态：

- browser auth blocked -> `permission_or_runtime_gap`
- 2FA -> `auth_factor_required`
- HTML/auth page -> `auth_session_issue`
- cookie bridge missing -> `cookie_bridge_missing`

### 4.8 timeout fallback

新增 `timeout_fallback` / `partial_evidence_card_template`：

- `completed_sources`
- `timeout_sources`
- `blocked_sources`
- `parse_error_sources`
- `missing_evidence`
- `current_confidence`
- `source_quality`
- `freshness_status`
- `permission_status`
- `next_action`
- `whether_dataagent_required`

### 4.9 API / SSO / JSON 稳定性

新增 / 强化：

- `api_stability_guard`
- `json_parse_error_fallback`
- `source_quality_metadata`

规则：

- SSO 失败有重试上限。
- HTML / auth page 不当 JSON 解析。
- 单个用户失败不阻断批量。

### 4.10 回答长度控制

新增 `answer_length_control`：

- 专家认知问答默认 500 字内。
- 批量分析默认 800 字内。
- 平台失败降级短答优先。

### 4.11 设备 SDK 三层解读

新增 `device_sdk_three_layer_answer`：

1. 设备风险标签。
2. SDK 指纹字段。
3. 设备侧补证边界。

## 5. Q1-Q20 自动测试基线

已沉淀到 `computer_use_poc/runtime_validation_cases_v1.yaml` 的 `semi_open_pilot_experience_patch_v1.q_cases`。

覆盖：

- Q1/Q2/Q10：单用户显式查询与 ATO evidence card。
- Q3/Q8/Q11/Q12/Q13：证据边界默认纯分析。
- Q4/Q5：3+ 用户批量默认 batch plan。
- Q14/Q15/Q16/Q17：非 ATO 专家模式，不默认 browser。
- Q18：举一返三 / 策略推荐 plan mode。
- Q19：DataAgent / Hive plan only。
- Q20：安全注入拒绝。

## 6. KIM real-session regression

已沉淀到 `computer_use_poc/runtime_validation_cases_v1.yaml` 的 `semi_open_pilot_experience_patch_v1.kim_real_session_regression`。

覆盖：

- KIM-R1：单案 ATO 路由绕路。
- KIM-R2：显式查询空研判。
- KIM-R3：策略设计带 user_id 被拉偏。
- KIM-R4：API / SSO / JSON 稳定性。
- KIM-R5：browser / 2FA 卡点。
- KIM-R6：平台只读观察可信同学限定。
- KIM-R7：回答长度。
- KIM-R8：设备 SDK 问题含糊。
- KIM-R9：Hive 框架口径。
- KIM-R10：no_data 体感差。

## 7. 修改文件

- `AGENTS.md`
- `computer_use_poc/multi_entry_runtime_guard_v1.md`
- `computer_use_poc/answer_experience_templates.md`
- `computer_use_poc/scene_to_capability_routing.md`
- `computer_use_poc/capability_registry.md`
- `computer_use_poc/browser_auth_preflight_checklist_v2_4_9.md`
- `computer_use_poc/runtime_validation_cases_v1.yaml`
- `computer_use_poc/smoke_tests.md`
- `computer_use_poc/run_logs/semi_open_experience_patch_unified_fix_plan_v1.md`

## 8. 验证方式

本轮为文本级规则 / 模板 / regression patch。

建议执行：

```bash
python3 - <<'PY'
import yaml
from pathlib import Path
yaml.safe_load(Path("computer_use_poc/runtime_validation_cases_v1.yaml").read_text())
PY

rg -n "SEMI-OPEN-EXP|semi_open_pilot_experience_patch_v1|explicit_query_not_empty_analysis|batch_plan_mode|evidence_boundary_mode" computer_use_poc AGENTS.md

git diff --check
```

## 9. 边界

- 未访问真实内部平台。
- 未调用 DataAgent。
- 未修改 auth state。
- 未修改云端 gateway config。
- 未执行真实查询。
- 未重新打包 release。
- 未执行 git commit / push。

## 10. 下一步建议

- 等 diff 确认后，再决定是否打 semi-open experience patch release。
- 云端如走 prompt / runtime overlay，需要把 `AGENTS.md` 和 `multi_entry_runtime_guard_v1.md` 同步到 runtime-loaded 层。
- 真实回归优先重跑 Q1-Q20，以及 KIM-R1/R2/R3/R5/R7/R8。
