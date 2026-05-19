# Evidence Source to Tool Map v1

## 0. 使用原则

本文件按证据类型定义推荐 provider。Data Agent 不再是默认取证工具，只有当证据适合 Hive / BI / 离线分析 / 看板 / AB / 画像标签时，才优先选择 `dataagent_provider`。

## 1. 前后端链路一致性

- 证据名称：前后端链路一致性
- 适用风险：协议攻击、破解包绕 SDK、埋点缺失排查、反爬资产访问异常
- 推荐 provider：`realtime_log_provider`
- 可选 provider：`dataagent_provider`、`structured_sql_or_feature_provider`
- 不推荐 provider：单独使用 `dataagent_provider` 做实时强结论
- 选择原因：前后端链路一致性通常需要更接近实时的前端、后端、SDK、NG 日志；Data Agent 适合作离线复核，不适合作低延迟补证。
- 数据时效要求：实时或准实时优先，离线 T+1 只能支持复盘
- 是否需要 join path：需要，前端事件、后端请求、设备、token、时间窗需对齐
- 是否需要人工确认：强处置前需要
- provider 失败时 fallback：降级到 Data Agent 离线复盘或人工补证，不输出实时强结论

## 2. SDK 日志覆盖 / 破解包绕采集

- 证据名称：SDK 日志覆盖 / 破解包绕采集
- 适用风险：破解包、协议误判排除、SDK 缺失、端侧采集绕过
- 推荐 provider：`device_fingerprint_provider`、`realtime_log_provider`
- 可选 provider：`dataagent_provider`
- 不推荐 provider：仅用 Data Agent markdown 返回下强结论
- 选择原因：SDK 和指纹需要设备侧或实时采集证据；Data Agent 更适合趋势和样本复盘。
- 数据时效要求：实时或准实时；版本趋势可离线
- 是否需要 join path：需要，设备、app 版本、SDK 状态、后端请求需关联
- 是否需要人工确认：涉及版本缺陷或破解包定性时需要
- provider 失败时 fallback：转人工确认官方版本、渠道、采集变更

## 3. token / device / ip / ua 一致性

- 证据名称：token / device / ip / ua 一致性
- 适用风险：协议攻击、token 泄露、登录态复用、ATO
- 推荐 provider：`realtime_log_provider`、`risk_engine_provider`、`device_fingerprint_provider`
- 可选 provider：`dataagent_provider`
- 不推荐 provider：只用离线聚合判断单次登录态冲突
- 选择原因：一致性冲突依赖请求级上下文、策略决策和设备指纹。
- 数据时效要求：实时或准实时优先
- 是否需要 join path：需要，token、设备、IP、UA、账号、请求时间窗
- 是否需要人工确认：处罚、冻结、扣除前需要
- provider 失败时 fallback：离线聚合补证 + 人工核验

## 4. 接口序列固化

- 证据名称：接口序列固化
- 适用风险：协议攻击、反爬、接口自动化、脚本化调用
- 推荐 provider：`realtime_log_provider`
- 可选 provider：`dataagent_provider`
- 不推荐 provider：只看策略命中
- 选择原因：接口序列固化需要请求级时序和相邻接口关系。
- 数据时效要求：实时、准实时或短周期明细
- 是否需要 join path：需要，请求序列、账号、设备、时间窗
- 是否需要人工确认：强处置前需要
- provider 失败时 fallback：离线序列聚合，结论降级

## 5. 设备团组 / 群控统一调度

- 证据名称：设备团组 / 群控统一调度
- 适用风险：群控、活动黑产、反爬真机群控、导流矩阵
- 推荐 provider：`device_fingerprint_provider`、`relation_graph_provider`、`realtime_log_provider`
- 可选 provider：`dataagent_provider`
- 不推荐 provider：仅用设备聚集下群控结论
- 选择原因：群控需要设备环境、关系网络和行为调度共同闭合。
- 数据时效要求：实时调度证据优先，团组可离线补证
- 是否需要 join path：需要，设备、账号、行为、团组、收益或目标
- 是否需要人工确认：需要，尤其涉及商家 / MCN / 机构运营
- provider 失败时 fallback：输出证据不足，转人工或离线复盘

## 6. 收益聚集 / 活动奖励 / 提现

- 证据名称：收益聚集 / 活动奖励 / 提现
- 适用风险：活动黑产、活动低质、真人众包、套利
- 推荐 provider：`dataagent_provider`、`structured_sql_or_feature_provider`
- 可选 provider：`risk_engine_provider`
- 不推荐 provider：只用实时日志判断收益链
- 选择原因：奖励、提现、后验质量更适合离线聚合或专题结构化查询。
- 数据时效要求：准实时或离线
- 是否需要 join path：需要，活动、账号、设备、奖励、提现、留存
- 是否需要人工确认：涉及扣除或处罚前需要
- provider 失败时 fallback：人工补证，不能定义黑产

## 7. 渠道 CTIT / 归因劫持

- 证据名称：渠道 CTIT / 归因劫持
- 适用风险：点击注入、点击洪泛、归因劫持、渠道抢量
- 推荐 provider：`dataagent_provider`
- 可选 provider：`structured_sql_or_feature_provider`
- 不推荐 provider：单独使用实时日志做整体归因结论
- 选择原因：渠道曝光、点击、激活、CTIT、自然量跷跷板更偏离线 / 准实时分析，Data Agent 适合。
- 数据时效要求：准实时或离线趋势
- 是否需要 join path：需要，曝光、点击、激活、渠道、设备、用户生命周期
- 是否需要人工确认：投放策略和扣量前需要
- provider 失败时 fallback：结构化专题查询或人工渠道复核

## 8. 外网跟价 / 反爬资产泄漏

- 证据名称：外网跟价 / 反爬资产泄漏
- 适用风险：反爬、价格 / 库存 / 内容资产泄漏、接口爬取
- 推荐 provider：`realtime_log_provider`、`dataagent_provider`、`relation_graph_provider`
- 可选 provider：`device_fingerprint_provider`
- 不推荐 provider：只因外网同步就判内部接口被爬
- 选择原因：实时日志查访问链路，Data Agent 做离线聚合、趋势、资产访问复盘，关系图查账号 / 设备团伙扩散。
- 数据时效要求：泄漏对齐需实时或准实时，复盘可离线
- 是否需要 join path：需要，资产访问、外部时间、账号、设备、IP、接口
- 是否需要人工确认：强治理前需要
- provider 失败时 fallback：排查缓存、前端、合作方、内部、真人访问路径

## 9. 导流截流 / 站外添加

- 证据名称：导流截流 / 站外添加
- 适用风险：直播间截流、私信导流、站外承接、黑产账号矩阵
- 推荐 provider：`realtime_log_provider`、`relation_graph_provider`、`dataagent_provider`
- 可选 provider：`manual_review_provider`
- 不推荐 provider：默认归为协议或反爬
- 选择原因：实时触达链路需要日志，矩阵扩散需要图关系，离线复盘可用 Data Agent。
- 数据时效要求：触达链路准实时，矩阵和投诉可离线
- 是否需要 join path：需要，信息暴露、搜索、关注、私信、站外承接、账号矩阵
- 是否需要人工确认：涉及正常社交和授权运营时需要
- provider 失败时 fallback：转人工复核，不能下导流黑产强结论

## 10. 合法矩阵 / 授权运营

- 证据名称：合法矩阵 / 授权运营
- 适用风险：商家、达人、MCN、客服、机构批量运营边界
- 推荐 provider：`dataagent_provider`、`structured_sql_or_feature_provider`、`manual_review_provider`
- 可选 provider：`risk_engine_provider`
- 不推荐 provider：直接按群控或协议处理
- 选择原因：授权主体、账号范围、工具来源、收益主体等可能分散在业务登记或专题数据里，需要人工确认边界。
- 数据时效要求：准实时或离线均可，授权口径必须准确
- 是否需要 join path：需要，授权主体、账号范围、工具来源、操作人、收益主体、历史违规
- 是否需要人工确认：需要
- provider 失败时 fallback：人工补授权证明和业务登记信息

## 11. 策略效果 / 误伤复盘

- 证据名称：策略效果 / 误伤复盘
- 适用风险：策略误伤、效果评估、灰度验证、回滚判断
- 推荐 provider：`risk_engine_provider`、`dataagent_provider`
- 可选 provider：`structured_sql_or_feature_provider`
- 不推荐 provider：只看策略命中下风险事实
- 选择原因：策略命中和处置链路走 risk_engine，后验效果和业务指标走 Data Agent。
- 数据时效要求：策略链路可实时，后验效果多为离线
- 是否需要 join path：需要，策略命中、处置、业务结果、申诉、后验风险
- 是否需要人工确认：策略变更前必须人工确认
- provider 失败时 fallback：暂停策略结论，输出补证任务

## 12. AB 实验分析

- 证据名称：AB 实验分析
- 适用风险：实验影响、策略效果、业务指标归因
- 推荐 provider：`dataagent_provider`
- 可选 provider：`manual_review_provider`
- 不推荐 provider：实时日志 provider 单独解释实验结论
- 选择原因：Data Agent 支持 AB 实验分析、CUPED、DiD、推全、实验报告。
- 数据时效要求：实验平台和离线指标口径
- 是否需要 join path：通常需要实验、指标、分组、时间窗
- 是否需要人工确认：推全或策略调整前需要
- provider 失败时 fallback：人工实验复核或补充实验链接 / 名称

