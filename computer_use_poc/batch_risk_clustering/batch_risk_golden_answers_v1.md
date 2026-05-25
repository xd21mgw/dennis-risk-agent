# Batch Risk Golden Answers v1

These are text-level golden answers for user-facing Batch Risk Clustering Analysis. They contain simulated inputs only and no real platform data.

## Golden Answer 1: ATO Mixed Batch

### user_prompt

```text
这 12 个用户像不像一批 ATO？里面有几个人被踢登录态，有几个 Harmony/一键登录后改密，还有几个只是用户说被盗。
```

### input_summary

- 12 个 case。
- 4 个像密码失败 / 异设备登录 / kick_out。
- 3 个像 Harmony/OAuth/一键登录后 token revoke / 改密 / 发布。
- 3 个只有 user claim。
- 2 个像正常换机或误报。

### expected_routing_mode

`batch_clustering_mode`

### ideal_answer

```text
一句话：这批不能直接写成“同一批 ATO”，更像是 3-4 个风险簇混在一起；当前只能中等置信支持“存在批量账号接管候选”，不能强判同团伙。

处理模式：12 个实体，进入 batch_clustering_mode。本轮不逐个在线查平台，先做分簇、抽代表样本、列异常相关性矩阵和补证计划。

分簇看：
1. 撞库候选簇：密码失败密集 + 新设备登录 + kick_out，证据强度 medium。需要登录事件顺序、IP/设备一致性、改密/换绑审计补齐。
2. Harmony/OAuth/一键登录接管候选簇：login_method=HARMONY/OAuth/one-click-login -> token_revoke / password_change / publish_after_login，证据强度 medium。它不能被粗暴归成撞库，必须补授权链路和 token 生命周期。
3. user_claim/source_gap 簇：只有用户反馈被盗，最多 weak user_claim，不能当 strong evidence。
4. 正常换机/误报边界簇：稳定地理、可信设备迁移、无后置异常动作，应作为 false-positive 样本。

异常相关性矩阵重点看三组：password_failure_burst -> new_device_login；login_method=Harmony/OAuth -> abnormal_action；stable_device_migration -> no_downstream_abnormal_action。当前多处 baseline_missing / denominator_required，只能写 batch_internal_concentration 或 medium hypothesis，不能 strong enrichment。

代表样本建议抽 4 个：撞库候选 1 个、Harmony/OAuth 候选 1 个、user_claim-only 1 个、正常换机 1 个。每个样本输出 strong/medium/weak/counter/missing evidence。

补证优先级：先补登录 timeline、设备可信历史、OAuth 授权 / token issued / revoke、改密换绑、异常发布审计；超窗或批量扩展再生成 DataAgent/Hive 取数计划。

不能强判：不能说 12 个都是 ATO；不能说同团伙；不能把 Harmony/OAuth 当撞库；不能把用户反馈当强证据。
```

### why_this_answer_is_good

- 先给结论，明确不是单一风险簇。
- 选择 `batch_clustering_mode`，不逐个查平台。
- 将撞库、Harmony/OAuth、user claim、正常换机拆开。
- 输出有方向的异常相关性。
- 明确 baseline / denominator 缺口，避免 strong enrichment。
- 给出代表样本和补证优先级。

### common_bad_answer

```text
这批用户大概率都是 ATO，建议重点查 IP、设备、登录日志和用户反馈。如果有相似设备或相似时间，就可以判断是同一批黑产。建议直接扩大查关联账号并拦截。
```

### scoring_notes

- routing：必须是 `batch_clustering_mode`。
- 分簇：至少拆撞库、Harmony/OAuth、source_gap / false-positive。
- 证据：user_claim 只能 weak；Harmony/OAuth 不能误判撞库。
- 矩阵：必须出现 relation_direction、baseline/denominator、relationship_strength。
- 边界：不能强判同团伙。
- 补证：登录链路、授权链路、token 生命周期、后置动作审计。
- 可读性：结论先行，避免长表堆砌。

### should_call_platform

false

### should_call_DataAgent

false; DataAgent/Hive only as follow-up query plan if over-window or expansion is needed.

### cannot_conclude_boundary

- 不能判定全部 12 个都是 ATO。
- 不能判定同团伙。
- 不能用 user_claim 支撑 strong conclusion。
- 不能把 Harmony/OAuth 接管路径归成撞库。

## Golden Answer 2: Interface Request Spike

### user_prompt

```text
这个接口请求量突然升高，是不是被爬？
```

### input_summary

- 某接口请求量短时间升高。
- 未提供 UA、IP/ASN、前端行为、版本分布、活动窗口、监控口径变化。
- 需要区分爬虫、协议直调、业务波动、监控口径变化、策略/版本发布影响。

### expected_routing_mode

`interface/request batch clustering`

### ideal_answer

```text
一句话：现在不能直接判“被爬”。这更像一个接口请求激增批次，需要先把爬虫/协议直调、业务活动波动、监控口径变化、策略或版本发布影响拆开验证。

处理模式：进入 interface/request batch clustering。本轮不逐请求在线查，也不直接调用 DataAgent；先做批次级分布、异常相关性矩阵和补证计划。

我会先分 4 类假设：
1. 爬虫/协议直调候选：interface -> request_pattern 异常，例如固定间隔、高频、UA 单一、IP/ASN 聚集、前端行为缺失。
2. 业务活动波动：interface -> campaign_window / activity_entry，如果请求上涨与活动曝光、入口改版或投放同步，可能是正常业务增量。
3. 监控口径变化：sampling_policy / log_collect_version -> observed_volume，如果采样率、埋点口径、去重逻辑变了，看到的上涨可能是观测口径变化。
4. 策略/版本发布影响：app_version -> request_spike 或 strategy_release -> retry/429，如果新版本重试、策略拦截或错误码变化，也会造成突增。

异常相关性矩阵至少看：interface -> request_pattern；interface -> frontend_activity_gap；app_version -> request_spike；user/device cluster -> request_pattern。当前缺前端行为、UA、版本、用户/设备分布和时间基线，应标 baseline_missing / denominator_required，不能写 strong crawler enrichment。

补证优先级：先补 1 小时粒度趋势、活动/版本/策略上线时间轴；再按 endpoint、UA、IP/ASN、device_id、app_version、frontend_activity_presence、response_code 做聚合；最后抽 3-5 个代表请求样本看间隔、参数模式和前后端链路。

策略建议只能是候选：先监控和灰度限速，不自动封禁；指标看前端缺失率、UA/IP 聚集、429/失败率、正常业务转化是否下降。
```

### why_this_answer_is_good

- 不强判爬虫。
- 主动列出四类替代解释。
- 异常相关性矩阵有方向。
- 缺基线时明确 `baseline_missing / denominator_required`。
- 给出可执行补证字段和优先级。
- 策略建议是灰度和监控，不自动处置。

### common_bad_answer

```text
请求量突然升高基本就是被爬了，建议封 IP、加验证码、限制接口频率。可以查一下日志确认。
```

### scoring_notes

- routing：应进入 interface/request batch clustering。
- 分歧：必须同时考虑爬虫、协议直调、业务活动、监控口径、版本/策略影响。
- 矩阵：必须包含 interface -> request_pattern / frontend_activity_gap。
- baseline：缺分母不能 strong。
- 补证：UA、IP/ASN、前端行为、版本、时间基线、response code。
- 策略：candidate only，先灰度。

### should_call_platform

false

### should_call_DataAgent

false; only produce DataAgent/Hive aggregation plan if user confirms offline analysis.

### cannot_conclude_boundary

- 不能直接判爬虫。
- 不能只凭请求量上涨判断协议直调。
- 不能忽略活动、版本、策略、监控口径变化。
- no_data / partial source 不能当无风险反证。

## Golden Answer 3: Activity Channel Fake Volume / Arbitrage

### user_prompt

```text
这批活动渠道用户是不是假量/套利？
```

### input_summary

- 活动渠道批次。
- 怀疑 reward claim 异常、留存低、设备复用、真实行为弱、转化异常。
- 未提供渠道全量分母和对照组。

### expected_routing_mode

`business-arbitrage clustering` / `large_batch_aggregation_mode` if batch size is 50+

### ideal_answer

```text
一句话：目前只能判断“存在渠道套利/假量候选簇”，不能直接强判渠道作假。关键要看 channel -> reward_claim / low_retention / device_reuse / low_real_behavior 是否同时成立，并且是否高于渠道全量基线。

处理模式：这是活动/渠道批量归因，默认走 business-arbitrage clustering；如果样本 50+，进入 large_batch_aggregation_mode。本轮不逐个查用户，不调用 DataAgent，只输出聚合取数计划和代表样本方案。

分簇建议：
1. 高疑似套利簇：channel=A -> early reward_claim + device_reuse + low_real_behavior，若同时低留存，证据可到 medium。
2. 渠道质量差但未必套利簇：channel -> low_retention，但 reward_claim 不高、设备不复用，只能是业务质量问题候选。
3. 正常高激励渠道簇：reward_claim 高但留存正常、设备分散、后续行为真实，用作误伤对照。

异常相关性矩阵要有方向：channel -> reward_claim；channel -> low_retention；channel -> device_reuse；channel -> low_real_behavior；campaign -> abnormal_conversion。若没有渠道全量分母或同周期对照组，baseline_status 应写 baseline_missing / only_current_batch_available，denominator_status 写 denominator_required，只能说 batch_internal_concentration，不能写 strong enrichment。

代表样本抽 4 个：高奖励+复用设备样本、低留存但无奖励样本、高奖励但正常留存样本、高影响/高金额样本。证据卡要区分 raw evidence、derived evidence 和 missing evidence。

补证计划：按 channel、campaign、reward_claim、D1/D7 retention、device_family、account_reuse、real_behavior_count、conversion_path 聚合；再对比同周期非命中渠道。策略只给 candidate only / do_not_auto_launch：先灰度限制高风险组合，保留 holdout，监控奖励成本、留存、人工复核通过率和投诉。
```

### why_this_answer_is_good

- 不直接强判渠道作假。
- 用 channel -> reward / retention / device reuse / real behavior 的有方向矩阵解释风险。
- 缺分母时明确不能 strong enrichment。
- 给出对照簇和误伤控制。
- 策略建议明确 candidate only / do_not_auto_launch。

### common_bad_answer

```text
这批渠道用户留存低，基本就是假量。建议把这个渠道拉黑，后续所有奖励都拦截，同时扩大排查相同设备用户。
```

### scoring_notes

- routing：business-arbitrage clustering；大批量时 large_batch_aggregation_mode。
- 矩阵：必须有 channel -> reward_claim / low_retention / device_reuse / low_real_behavior。
- baseline：无渠道全量分母不能 strong。
- 样本：需要高疑似、边界、误伤、高影响样本。
- 证据：低留存是 derived evidence / 业务质量线索，不是黑产强证据。
- 策略：candidate only / do_not_auto_launch，包含灰度和人工复核。

### should_call_platform

false

### should_call_DataAgent

false; DataAgent/Hive only as follow-up aggregation query plan.

### cannot_conclude_boundary

- 不能直接判渠道作假。
- 不能只凭低留存或高奖励判断套利。
- 没有渠道全量分母和对照组时不能 strong enrichment。
- 不能自动上线拦截或全量拉黑。
