# 平台知识库质量验收报告

## 1. 已通过检查项

### 1.1 结构完整性

以下 10 个基础文件均已存在且非空：

- `00_platform_routing_index.md`
- `01_archives_center_platform_card.md`
- `02_risk_ops_center_platform_card.md`
- `03_device_defense_platform_card.md`
- `04_user_login_unified_log_platform_card.md`
- `05_tianshi_policy_engine_platform_card.md`
- `06_user_behavior_trace_platform_card.md`
- `90_cross_platform_investigation_paths.md`
- `91_platform_field_dictionary.md`
- `99_todo_unknown_fields.md`

本轮新增：

- `92_platform_routing_smoke_tests.md`
- `93_platform_knowledge_quality_report.md`

### 1.2 平台卡结构

6 个平台卡均包含以下 12 段：

- 平台一句话定位
- 平台能力边界
- 典型查询对象
- 页面 / 模块结构
- 核心字段字典
- 通用适用场景
- 风险场景覆盖矩阵
- 典型查询路径
- Agent 路由规则
- Agent 解释规则
- 截图与页面锚点
- 待确认项

### 1.3 ATO 泛化

未发现平台被写成 ATO 专用。ATO 被保留为账号安全典型用例之一，并已扩展到：

- 账号安全 / 异常登录
- 群控 / 号商
- 协议上号
- 反爬 / 资产抓取
- 内容风险
- 假量 / 裂变
- 社交骚扰
- 策略误伤 / 策略归因

### 1.4 DataAgent / Hive 边界

`00_platform_routing_index.md` 已明确：

- DataAgent 主要用于 Hive / 公司数仓取数分析、SQL 生成、批量样本聚合、趋势和归因。
- DataAgent 不是所有在线风控工具的替代品。
- DataAgent 不能覆盖所有实时日志、所有页面工具、所有权限受限字段。
- SQL-only / partial / no_permission / timeout 只能表示取证未完成或证据不足，不能作为反证。

### 1.5 不确定项处理

不确定字段、权限、截图缺失、页面入口和口径问题已集中写入 `99_todo_unknown_fields.md`，未在正文中强行解释为确定事实。

## 2. 发现的问题

1. 原始材料中 RAP 和天狮截图未包含在 `platform_cards_screenshots.tar.gz` 中，只保留了 Docs 路径。
2. 多个平台字段仍缺完整字典，例如 `safe_status`、`mark_code`、`punish_code`、`Method`、`policy_result`。
3. 用户行为细查平台的“手动导入行为记录”流程不够明确。
4. DataAgent / Hive 与在线平台的边界已写清，但后续接入 Agent 时仍需避免把 DataAgent 误当实时工具。

## 3. 已修复的问题

1. 在 `00_platform_routing_index.md` 中补充 Agent 默认读取顺序：
   - 涉及平台查询、证据补充、风险研判路径、平台手脚选择时，先读路由索引。
   - 需要字段和页面解释时，再读具体平台卡。
   - 涉及跨平台流程时，再读 `90_cross_platform_investigation_paths.md`。

2. 新增 `92_platform_routing_smoke_tests.md`，覆盖 22 个基础路由测试问题，并补充 RAP 关联用户图谱到设备平台用户扩散/设备扩散的联动测试。

3. 新增本质量报告，记录验收结论和剩余风险。

4. 根据用户补充的 RAP 关联用户截图，已将“关联用户 Tab / 关系图谱 / 字段明细”从粗粒度“关联账号”中拆出，补充为 RAP 的 P0 平台能力；同时在路由索引、跨平台链路、字段字典和待确认项中同步登记。

## 4. 未修复但已登记的问题

以下问题未在正文强行修复，已登记到 `99_todo_unknown_fields.md`：

- RAP 和天狮截图缺失；RAP 关联用户 Tab 已有用户补充截图，但尚未落为仓库内截图文件。
- RAP 关联用户关系图谱字段和口径：节点类型、关联用户数、用户标签聚合、设备标签、最后关联时间。
- 字段字典缺失：`safe_status`、`risk_level`、`punish_code`、`mark_code`、`Method`、`feature_value` 等。
- 高敏字段权限和合规审计边界。
- 行为埋点字典、session_id 口径、前端日志缺失解释。
- 天狮 v2pro/v2/v1 差异和策略结果字典。

## 5. 当前是否建议接入 Dennis Risk Agent

建议接入，定位为“平台路由和取证知识库 v1”。

接入方式建议：

1. 默认先加载 `00_platform_routing_index.md`。
2. 具体平台问题按需读取对应平台卡。
3. 跨平台研判读取 `90_cross_platform_investigation_paths.md`。
4. 字段解释读取 `91_platform_field_dictionary.md`。
5. 遇到不确定字段读取或追加 `99_todo_unknown_fields.md`。

不建议把本知识库表述成“平台字段已经全部确认”或“可替代平台权限和真实查询”。

## 6. 接入前还需要补哪些信息

P0：

- 明确接入 Agent 的加载顺序，避免一次性注入所有文件导致上下文过载。
- 告知 Agent：该知识库只提供平台路由和解释，不代表已经查到数据。

P1：

- 补 RAP 和天狮的本地截图包。
- 补充策略、设备风险、登录 method、审核/处罚编码字典。
- 用 3-5 个真实平台查询案例回填字段解释。

P2：

- 增加平台权限申请路径和联系人维护。
- 增加各平台字段示例值脱敏样例。
- 增加平台路由误判案例。

## 7. 总结

`internal_risk_platforms/` 已达到 Dennis Risk Agent 可读取和路由的最低质量要求：

- 能判断什么时候查哪个平台。
- 能解释每个平台查什么、不查什么、查不到去哪。
- 能支持跨平台研判链路。
- 能避免 ATO 绑死平台能力。
- 能明确 DataAgent / Hive 边界。

剩余问题主要是字段字典、截图缺失和权限口径，需要在后续真实使用中逐步补齐。
