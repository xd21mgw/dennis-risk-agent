# Batch Analysis Framework v1

## 1. 定位

本框架抽象当前两个 batch analysis 样板的共用方法：

1. `19_ato_batch_case_management/`
2. `20_black_market_account_matrix_batch/`

它不是新的平台手脚，不执行真实查询，不替代场景专家判断。它用于把 5-20 个同类 case 转成统一的 registry、evidence card、pattern summary、missing evidence 和 strategy direction draft。

边界：

- 不调用真实 DataAgent。
- 不访问真实内部平台。
- 不修改 release / dist。
- 不自动上线策略。
- 不自动处置。
- 不把后置行为直接当成风险本质。

## 2. 通用流程

| 阶段 | 通用目标 | 输出物 | 关键边界 |
|---|---|---|---|
| case intake | 接收 5-20 个同类 case，确认是否适合同一风险场景 | intake checklist | 不混入风险定义不同的 case |
| case registry | 统一字段、脱敏实体、记录现有材料和缺口 | registry CSV / table | 不放敏感明文，不伪造证据 |
| entity normalization | 归一化 user / account / device / uid segment / contact hash 等实体 | normalized entity summary | 实体只是引用，不是风险结论 |
| single-case evidence card | 每个 case 生成强/中/弱/反证/缺失证据 | evidence card | 用户申诉和人工备注不能当强证据 |
| cross-case pattern summary | 聚合共性实体、行为、时间、模板、链路 | pattern summary | 聚合模式只是候选路径 |
| missing evidence aggregation | 汇总共性缺口并排序 | missing evidence list | no_data / missing 不等于无风险 |
| strategy direction draft | 输出候选策略方向和补证建议 | strategy direction draft | 候选方向不是自动上线 |
| manual review boundary | 标注人工复核点、误伤风险、禁止动作 | review checklist | 人工确认前不进入处置 |

## 3. 场景替换点

不同风险场景复用同一框架，但必须替换以下内容：

| 替换项 | 含义 | 示例 |
|---|---|---|
| risk definition | 当前场景的风险本质 | ATO 是账号控制权异常；账号矩阵是账号池/导流互动 |
| scene-specific fields | 场景特有字段 | ATO 关注 event_time、abnormal_action；账号矩阵关注 intro_pattern、adminaction、uid_segment |
| evidence priority | 哪些证据优先级最高 | ATO 优先 token/OAuth/登录态/控制权；账号矩阵优先资料聚类+行为链路 |
| pattern dimensions | 批量聚合维度 | ATO 聚合凭证链路、控制权变化；账号矩阵聚合简介、昵称、注册 cohort、UID 号段 |
| strategy direction boundary | 策略方向的边界 | ATO 不因后置动作定性；账号矩阵不因简介聚类直接处置 |

## 4. ATO Batch vs 黑产账号矩阵 Batch

| 维度 | ATO batch | 黑产账号矩阵 batch |
|---|---|---|
| 风险本质 | 账号控制权异常 | 账号池 / 导流互动 / 互粉互动 / 养号矩阵 |
| 主线证据 | token / OAuth / 登录态异常，改密、换绑、异设备登录 | 简介签名聚类、联系方式归一化、adminaction、昵称模板、注册天数 cohort、UID 号段 |
| 后置行为 | 发布、私信、关注、支付、活动参与等，只是非本人动作结果 | 关注、点赞、互粉、私信、导流是行为链路本身 |
| 不能误判 | 不能把后置行为直接当 ATO | 不能把简介聚类直接当处置依据 |
| 缺失证据 | 发布审计、token 使用、OAuth 授权、登录日志窗口完整性 | 联系方式 hash、互动边、设备/IP/注册来源、行为时间序列 |
| 策略方向 | 凭证/登录态异常补证、账号控制权变化补证、后置动作补证 | 简介签名聚类、联系方式归一化、账号矩阵识别、行为链路补证 |

## 5. 后置行为不能等于风险本质

通用规则：

- 先定义风险本质，再看后置行为。
- 后置行为只能说明“发生了什么”，不能单独说明“为什么发生”。
- 如果风险本质不成立，应分流到对应场景。

示例：

- 发布违规内容不等于 ATO；需要凭证、登录态或控制权异常证据。
- 关注 / 点赞 / 私信导流不等于 ATO；若无控制权异常，应归入导流 / 互动作弊。
- 简介带联系方式不等于黑产；需要矩阵聚类、行为链路、误伤反证。
- adminaction 一致不等于自动处置；需要上下文和行为补证。

## 6. DataAgent 与内部 Agent 边界

DataAgent：

- 只作为 Hive / 数仓取数分析能力。
- 只在场景允许、范围明确、权限边界清楚时进入补证。
- 不是默认万能数据底座。
- 不替代 Dennis Agent 的风险定义、证据强弱判断和策略边界。

内部 Agent：

- 后续可作为真实只读 observation 执行层。
- 负责按 playbook 获取结构化 observation。
- 不作为最终研判大脑。
- 不应把平台返回直接包装成最终结论。

Dennis Agent：

- 负责定义风险本质。
- 负责组织 evidence card。
- 负责跨 case pattern summary。
- 负责缺口识别、反证、误伤风险和候选策略方向。

## 7. Strategy Direction 通用边界

任何 batch strategy direction 都必须包含：

- candidate_direction。
- supporting_patterns。
- strong_required_evidence。
- missing_before_eval。
- false_positive_risk。
- AB / shadow / 查杀分离建议。
- manual_review_required。

禁止：

- 直接上线。
- 自动封禁 / 解封 / 限流。
- 命中单一模式即处置。
- 用用户申诉、人工备注、简介聚类、adminaction 或单一后置行为直接定性。

## 8. 新场景扩展方法

新增 batch 场景时，建议复制最小结构：

1. `<scene>_case_schema_v1.md`
2. `<scene>_registry_template_v1.csv`
3. `<scene>_evidence_card_template_v1.md`
4. `<scene>_pattern_summary_template_v1.md`
5. `<scene>_strategy_direction_template_v1.md`
6. `<scene>_dry_run_sample_v1.md`

新增前必须先写清：

- risk definition。
- 与已有 batch 场景的边界。
- scene-specific fields。
- evidence priority。
- pattern dimensions。
- strategy direction boundary。
