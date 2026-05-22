# Security Preflight Coverage Matrix

## 1. 当前定位

当前 Agent Safety / Security Preflight 定位为半开放测试前的安全基线。

目标：

- 防止裸奔式工具调用。
- 防 prompt injection。
- 防越权工具调用。
- 防敏感字段输出。
- 防批量扩散失控。
- 防运行时对话修改 Agent 逻辑、skill、routing、release 或配置。

当前状态：

- 已完成本地 dry-run、shadow mode 设计、shadow hook 设计、request contract、validator、evaluator、pipeline 和 normal business coverage。
- 尚未接入真实 runtime。
- 尚未进入真实 enforce mode。
- 尚未接真实审批系统。
- 尚未接真实审计落库。

## 2. 已完成能力矩阵

| module | purpose | current_status | validation_result | limitation |
|---|---|---|---|---|
| 安全制度文档 | 固化安全原则和禁止事项 | completed | documented | 仅文档约束，不是运行时闸门 |
| capability security policy | 定义 capability 分级和调用边界 | completed | documented | 需 runtime 强制读取 |
| approval policy | 定义自动允许、确认、审批、禁止边界 | completed | documented | 未接真实审批状态机 |
| sensitive field redaction policy | 定义敏感字段脱敏策略 | completed | documented | 未接真实输出层脱敏器 |
| tool call audit schema | 定义审计字段 | completed | documented | 未接审计落库 |
| prompt injection defense cases | 沉淀提示词攻击样例 | completed | 19/19 pass | 文本回归，不是 runtime 防护 |
| capability registry 安全字段 | 给 capability 增加安全字段 | completed | documented | 仍需与 runtime registry 对齐 |
| scene_to_capability_routing 安全边界 | 说明场景路由和拒绝/审批边界 | completed | documented | 不替代 evaluator |
| security_preflight_policy.yaml | 结构化安全策略 | completed | dry-run used | JSON 兼容 YAML 子集 |
| security_preflight_evaluator.py | 本地 preflight evaluator | completed | 12/12 pass | 未接真实 tool-call 链路 |
| request contract | 定义 tool_call_request 字段契约 | completed | documented | 未接 runtime request builder |
| request contract validator | 校验 request 字段完整性和安全质量 | completed | 14/14 pass | 本地样例验证 |
| shadow mode design | 定义 dry_run / shadow / enforce 三阶段 | completed | documented | 未接 runtime |
| shadow hook plan | 定义 tool-call 前旁路 hook 接入点 | completed | documented | 未实现 hook |
| shadow event samples | 提供 15 条模拟 shadow event | completed | JSON valid | 模拟样例，不是真实流量 |
| shadow metrics aggregator | 聚合 shadow event 指标 | completed | local run passed | 未接真实指标系统 |
| shadow pipeline dry-run | 串联 validator → evaluator → event → metrics | completed | local run passed | 使用本地异常/边界样例 |
| normal business request samples | 提供 18 条正常业务 request 样例 | completed | JSON valid | 模拟正常请求 |
| normal business pipeline dry-run | 验证正常业务样例不会大量误拦 | completed | 18 valid, 13 allow, 5 require_approval, 0 deny | 未接真实 Agent request |
| smoke tests | 登记 safety / preflight / shadow / pipeline 测试口径 | completed | documented | 非自动化完整测试套件 |

## 3. 核心验证结论

- prompt injection 文本回归已覆盖并通过。
- preflight evaluator dry-run 已通过。
- request validator 可识别字段缺失、unknown capability、prohibited field、敏感实体未标记等问题。
- shadow pipeline 可证明非法 request 不进入 evaluator。
- normal business pipeline 证明正常单点只读请求未明显误拦。
- 批量 / 扩散 / 多平台串联进入 `require_approval`。
- 敏感字段进入 `redaction_required`。
- 当前不适合直接进入 enforce mode。

## 4. 当前不继续深挖的原因

继续推进会进入生产安全工程专项，包括：

- 真实 runtime hook。
- 审批系统。
- 审计落库。
- enforce mode。
- 权限平台集成。
- 输出层真实脱敏器。
- 平台 runtime readonly config apply。

当前阶段优先目标仍是 Dennis Agent 业务能力、半开放体验和 case 研判质量。现有安全框架已经足够支撑“非裸奔”的半开放前基线，但不等价于生产安全执行框架。

## 5. 暂缓 TODO

| todo | why_deferred | trigger_to_resume | owner_suggestion | risk_if_skipped |
|---|---|---|---|---|
| runtime shadow hook 接入 | 会进入真实 runtime 改造 | 接入真实 tool-call 链路前 | Agent runtime owner | 无法观察真实请求风险 |
| enforce mode 灰度 | 需要生产评审和灰度策略 | shadow 指标稳定后 | Safety + runtime owner | 继续只停留在旁路观察 |
| 审批状态机 | 需要真实组织审批流 | 批量/扩散工具开放前 | Safety owner | require_approval 无法流转 |
| 审计落库 | 需要审计存储和权限设计 | 半开放真实试运行前 | Infra / security owner | 难以复盘和问责 |
| 真实 runtime request 样本回归 | 需要 runtime 产出样本 | runtime request builder 完成后 | Agent runtime owner | contract 偏差无法发现 |
| readonly runtime config apply | 涉及工具隔离配置 | 半开放环境准备前 | Platform owner | 漏判时缺少平台侧兜底 |
| sso_session_runner wrapper preapply review | 涉及真实认证链路包装 | runner 接真实能力前 | Runtime + security owner | 认证态和请求边界风险 |
| release 包安全配置模板固化 | 需要 release 集成窗口 | 下一次正式 release 前 | Release owner | 集成方缺少安全配置 |
| shadow metrics 日报/周报化 | 需要真实 shadow 数据源 | shadow hook 接入后 | Ops / security owner | 无法跟踪趋势 |
| redaction runtime output check | 需要输出层接入 | 输出层进入半开放前 | Agent runtime owner | 敏感字段泄露风险 |

## 6. 下一阶段恢复条件

在以下任一条件出现时恢复安全专项：

- 准备真实半开放测试前。
- 内部 Agent readonly config 准备 apply 前。
- 接入真实 tool-call 链路前。
- 出现 prompt injection / 越权工具调用 / 敏感字段输出 bad case 后。
- batch case analysis 或策略推荐要接更多工具前。

## 7. 当前推荐转向

当前建议转回：

- 真实半开放体验样板。
- 单 case 研判质量提升。
- batch case analysis。
- evidence card / case registry。
- release 集成与用户体验。
