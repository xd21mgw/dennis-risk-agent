# DataAgent Query Suggestion Contract v1

## 1. 触发条件

当用户明确出现以下表达时，触发查询建议输出：

- 帮我看应该查什么
- 生成查数建议
- 生成 DataAgent 查询建议
- 给我 DataAgent query intent
- 看日志 / 拉样本 / 看画像 / 验证数据
- 帮我设计 Hive 取证路径

## 2. 非触发条件

以下情况不触发正式查询建议，只给取证方向或判断框架：

- 用户只是问“怎么判断”
- 用户只是问“怎么区分”
- 用户只是问“有哪些证据”
- 用户没有要求查数或生成查询建议

## 3. 标准输出结构

每次生成 DataAgent 查询建议时，必须包含以下 10 段结构：

1. 查询目标
2. 必要入参
3. 建议查询数据 / 字段
4. 关键证据判断
5. strong evidence
6. medium evidence
7. weak evidence
8. counter evidence / 误判边界
9. 预期输出结构
10. 还需要用户补充的信息

其中第 2 段“必要入参”必须分为三类表达：

- 最小必要入参：缺失后会影响查询建议是否能成立，或者无法明确查询目标。
- 建议补充入参：有助于缩小范围、提升查询质量；缺失不阻塞初步查询建议。
- 可选上下文：仅用于解释和人工复核；不能作为 strong evidence。

说明：
- 只要最小必要入参已具备，即使建议补充入参或可选上下文缺失，也应先输出通用查询建议。
- 只有最小必要入参缺失时，才需要在第 10 段中明确说明哪些内容会帮助把查询建议收敛得更好。

## 4. 硬性约束

- 不真实调用 DataAgent。
- 不假装已经查到结果。
- 不输出虚构数据。
- 具体阈值只能作为示例阈值，且必须注明“需按业务历史分布和风控口径校准”。
- 查询建议阶段不得直接输出强处置结论，例如 `block` / `ignore`。
- 如需处置建议，只能写 `recommended_action_candidate`、`manual_review_required`、`need_more_evidence`。
- JSON key 尽量使用英文或拼音，不混用中文字段名。
- DataAgent 仅定位为 Hive / 公司数仓取数分析能力，不是全能数据底座。

## 5. 场景模板

下面 4 个模板只给字段和证据结构，不写具体业务结论。

### 5.1 ATO / 协议上号查询建议模板

```text
query_goal:
- 验证是否存在 ATO / 协议上号 / Web 扫码 / OAuth / 异步登录 / 登录态接管的证据。

required_inputs:
- 最小必要入参: user_id, time_window
- 建议补充入参: suspicious_event_time, business_line, sensitive_action_scope
- 可选上下文: user_claim_summary, manual_note

suggested_data_and_fields:
- 登录 / 授权链路
- 设备 / IP / UA / 地区
- token / session / 登录态变化
- 账号安全风险策略命中
- 下游行为（发布 / 资料变更 / 互动 / 找回 / 改密 / 换绑）

key_evidence_judgment:
- 是否形成“异常登录/授权 → 新设备/新环境 → 登录态变化 → 下游行为”的闭环。

strong_evidence:
- Web 扫码 / OAuth / 异步登录链路闭合
- 新设备 / 新 IP / 新 UA / 新地区
- 账号接管风险策略命中
- token / session 异常变化

medium_evidence:
- 登录环境突变但缺历史基线
- 多设备多 IP 短时间切换
- 风险画像存在但缺完整策略明细

weak_evidence:
- 用户自述
- 人工备注
- 单一异常登录信号

counter_evidence_false_positive_boundary:
- 登录环境与历史一致
- 无异常授权 / 无 token 变化
- 可被本人设备、跨省移动、正常找回解释

expected_output_structure:
- 数据发现
- 证据分层
- 反证与边界
- query_plan
- need_more_evidence

suggested_additional_info:
- 更明确的异常时间
- 账号标识
- 已知的异常行为描述
```

### 5.2 群控 vs 真人众包查询建议模板

```text
query_goal:
- 区分群控、真人众包、正常矩阵运营、合法代运营。

required_inputs:
- 最小必要入参: sample_list / account_list, time_window
- 建议补充入参: current_label_or_source, investigation_goal
- 可选上下文: 样本来源备注, 人工标签说明

suggested_data_and_fields:
- 设备团组
- IP / UA / 地区
- 行为序列
- 任务链 / 结算链
- 内容模板相似度
- 账号生命周期

key_evidence_judgment:
- 是否存在统一调度、任务化执行、收益聚集或组织化协同。

strong_evidence:
- 设备团组 + 行为同步 + 任务链闭合
- 收益聚集 / 统一结算
- 高度一致的行为模板

medium_evidence:
- 设备或 IP 有聚集
- 行为相似但缺任务链
- 账号生命周期短且集中

weak_evidence:
- 账号数量多
- 看起来很像
- 人工主观判断

counter_evidence_false_positive_boundary:
- 授权矩阵 / 代运营 / MCN / 内部测试可解释相似性
- 群体行为不等于群控

expected_output_structure:
- 分层结果
- 证据优先级
- 误判边界
- query_plan
- manual_review_required

suggested_additional_info:
- 是否有授权矩阵
- 是否有业务合作关系
- 是否有已知任务群线索
```

### 5.3 外部跟价 / 反爬资产泄露查询建议模板

```text
query_goal:
- 验证高价值资产是否被异常获取、同步或外泄。

required_inputs:
- 最小必要入参: asset_scope, time_window
- 建议补充入参: suspected_channel, business_owner, external_site
- 可选上下文: 业务备注, 站外线索描述

suggested_data_and_fields:
- 访问链路
- 前后端一致性
- 设备 / IP / UA / 地区
- 资产页 / 接口暴露面
- 站外同步 / 跟价时序

key_evidence_judgment:
- 是否存在“资产被拿走 → 站外快速同步”的路径。

strong_evidence:
- 高价值资产被系统性访问
- 前后端链路异常
- 站外同步时间差稳定

medium_evidence:
- 访问模式异常但无法直接闭环
- 资产暴露面存在但来源不明

weak_evidence:
- 外部跟价现象
- 内部主观怀疑

counter_evidence_false_positive_boundary:
- 合法比价 / 搜索抓取 / 合作方同步 / 用户分享 / 媒体转载

expected_output_structure:
- 资产暴露面
- 路径拆解
- 证据优先级
- 误判边界
- query_plan

suggested_additional_info:
- 资产类型
- 暴露范围
- 期望查的时间窗
```

### 5.4 裂变拉新假量查询建议模板

```text
query_goal:
- 验证活动增长是否存在假量、套利或后验质量失真。

required_inputs:
- 最小必要入参: campaign_id / activity_id, time_window
- 建议补充入参: sample_scope, analysis_goal, business_line
- 可选上下文: 活动备注, 运营说明, 争议样本线索

suggested_data_and_fields:
- 邀请链路
- 奖励链路
- 留存 / 转化 / 付费
- 设备 / IP / 账号聚集
- 结算 / 提现 / 回流

key_evidence_judgment:
- 是否存在异常增长 + 后验质量显著偏低 + 套利闭环。

strong_evidence:
- 邀请 / 奖励 / 回流链路异常闭合
- 后验质量显著偏低
- 账号 / 设备 / IP 聚集

medium_evidence:
- 前段指标好看但后验质量差
- 个别环节异常但缺完整闭环

weak_evidence:
- 增长快
- 留存差
- 主观怀疑假量

counter_evidence_false_positive_boundary:
- 正常活动波峰
- 真实用户画像差异
- 渠道结构变化

expected_output_structure:
- 活动链路拆解
- 强中弱证据
- 查杀分离
- query_plan

suggested_additional_info:
- 活动目标
- 结算方式
- 是否已有争议样本
```
