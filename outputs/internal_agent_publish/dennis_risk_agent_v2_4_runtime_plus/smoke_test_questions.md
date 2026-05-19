# Dennis Risk Agent v2.4 Runtime Plus Smoke Test Questions

## 1. 账号被盗了，怎么判断是不是协议上号？

- 期望命中的加载路径：ATO 完全体
- 是否允许 DataAgent：允许，但仅在用户明确要求查数时
- 合格回答标准：
  - 先识别为 ATO / 账号安全。
  - 说明判断框架，并按 6 段内部 checklist 覆盖：初步判断、风险本质、关键证据、误判边界、补证 / 查数建议、治理建议；最终用户短答不强制展示 6 个标题。
  - 覆盖登录 / 授权 / 设备 / IP / UA / 地区 / token / session / 下游行为。
  - 不假装已查到数据。
- 不合格表现：
  - 只给空泛建议。
  - 直接默认查数。
  - 把 ATO 退化成轻量 summary。

## 2. 外网一直能跟价我们商品，但内部没看到异常流量，怎么排查？

- 期望命中的加载路径：anti_crawler_runtime_summary_v1
- 是否允许 DataAgent：默认不允许，除非用户明确要求查数
- 合格回答标准：
  - 给出攻击路径、证据优先级、误判点、治理建议、下一步排查。
  - 不默认进入 DataAgent。
- 不合格表现：
  - 直接查数。
  - 回答表面化。

## 3. 怎么判断一个攻击是单纯协议攻击？

- 期望命中的加载路径：protocol_attack_runtime_summary_v1
- 是否允许 DataAgent：默认不允许
- 合格回答标准：
  - 能区分协议攻击、群控、真人众包。
  - 包含判断证据和反证。
  - 给出低成本取证方向。
  - 回答尽量保持短答骨架，不展开成长报告。
- 不合格表现：
  - 与反爬、群控混为一谈。
  - 直接调用 DataAgent。

## 4. 群控和真人众包怎么区分？

- 期望命中的加载路径：group_control + real_user_crowdsourcing runtime summaries
- 是否允许 DataAgent：默认不允许
- 合格回答标准：
  - 说明设备、行为、账号、任务链、成本结构的差异。
  - 讲清组织化调度 vs 任务化真人执行。
  - 回答尽量保持短答骨架。
- 不合格表现：
  - 只讲“很多设备/很多真人”。
  - 直接查数。

## 5. 裂变拉新怎么判断黑产假量？

- 期望命中的加载路径：activity_anti_cheating_runtime_summary_v1
- 是否允许 DataAgent：默认不允许
- 合格回答标准：
  - 包含活动链路拆解、黑产动机、证据优先级、误判点、治理动作。
  - 只有用户明确要求查数时才给 DataAgent / Hive 方向。
  - 回答尽量保持短答骨架，不默认查数。
- 不合格表现：
  - 默认查数。
  - 只讲“加强监控”。

## 6. 账号被盗了，怀疑协议上号，user_id 是 12345，时间窗口是昨晚 20:00 到今天 10:00，帮我看应该查什么。

- 期望命中的加载路径：ATO 完全体 + `dataagent_query_suggestion_contract_v1.md`
- 是否允许 DataAgent：允许生成查询建议，但不允许假装已查数
- 合格回答标准：
  - 先识别为 ATO / 账号安全。
  - 给出标准化查询建议结构：查询目标、必要入参（分最小必要入参 / 建议补充入参 / 可选上下文）、建议数据 / 字段、关键证据判断、强中弱证据、误判边界、预期输出结构、还需补充的信息。
  - 明确查询建议结构不等于可直接执行 SQL；执行前仍需 DataAgent / Hive 根据真实表名、权限、分区、join key 和数据口径转换。
  - 不把建议补充入参 / 可选上下文写成阻塞项。
  - 不输出虚构结果，不直接给强处置结论。
- 不合格表现：
  - 只给维度清单。
  - 把可选上下文写成“未提供就不能生成建议”。
  - 直接调用 DataAgent。
  - 把查询建议写成查询结果。

## 7. 外部站点一直能跟价我们商品，但内部没看到明显高频爬虫。帮我生成 DataAgent 查询建议，不要真的查。

- 期望命中的加载路径：anti_crawler_runtime_summary_v1 + `dataagent_query_suggestion_contract_v1.md`
- 是否允许 DataAgent：允许生成查询建议，但不允许实际查数
- 合格回答标准：
  - 先给出反爬 / 资产保护的判断框架和查询建议标准结构。
  - 明确 DataAgent 仅用于 Hive / 公司数仓取数分析，不直接执行。
  - 查询建议的入参要分层：最小必要入参 / 建议补充入参 / 可选上下文；可选上下文缺失不阻断建议输出。
  - 不虚构数据，不输出强处置结论。
- 不合格表现：
  - 直接查数。
  - 只给“看看日志、看看画像”这种维度列表。
  - 把可选上下文写成阻塞项。
  - 回答过于表面化。

## 8. v2.4.2 盗号短问骨架回归

### Case 1: 账号被盗了，怎么判断是不是协议上号？

- 期望命中的加载路径：ATO 完全体
- 是否允许 DataAgent：默认不允许；只有明确要求查数时才进入查询建议
- 合格回答标准：
  - 按 6 段内部 checklist 覆盖关键内容，最终用户短答不强制展示 6 个标题。
  - 不把用户自述 / 人工备注当 strong evidence。
  - 不默认进入查询建议。

### Case 2: 异地登录是不是盗号？

- 期望命中的加载路径：ATO 完全体
- 是否允许 DataAgent：默认不允许
- 合格回答标准：
  - 先纠偏误判边界。
  - 说明异地登录不等于盗号。
  - 按 6 段内部 checklist 覆盖关键内容，最终用户短答不强制展示 6 个标题。

### Case 3: token 被盗和协议上号怎么区分？

- 期望命中的加载路径：ATO 完全体
- 是否允许 DataAgent：默认不允许
- 合格回答标准：
  - 讲清协议上号、token 被盗、正常异地登录的差异。
  - 按 6 段内部 checklist 覆盖关键内容，最终用户短答不强制展示 6 个标题。

### Case 4: 用户说被盗了，我应该先看哪些证据？

- 期望命中的加载路径：ATO 完全体
- 是否允许 DataAgent：默认不允许
- 合格回答标准：
  - 先讲关键证据优先级。
  - 如用户没要求查数，不进入正式查询建议。
  - 按 6 段内部 checklist 覆盖关键内容，最终用户短答不强制展示 6 个标题。

### Case 5: 账号被盗了，user_id 是 12345，昨晚到今天异常，帮我看应该查什么。

- 期望命中的加载路径：ATO 完全体 + `dataagent_query_suggestion_contract_v1.md`
- 是否允许 DataAgent：允许生成查询建议，但不允许假装已查数
- 合格回答标准：
  - 触发查询建议 contract。
  - 首次回答必须输出标准查询建议结构。
  - 明确查询建议结构不等于可直接执行 SQL。
  - 仍不真实调用 DataAgent。

## 9. internal_risk_platforms 平台路由 smoke tests

### Case 1: 用户 5 月 4 日扫码后账号异常，先查哪里？

- 期望加载路径：`internal_risk_platforms/00_platform_routing_index.md` → `04_user_login_unified_log_platform_card.md`
- 合格回答标准：优先用户登录统一日志；补充档案中心、设备攻防、用户行为细查、天狮；不假装已有结果。

### Case 2: 一批账号同设备注册登录，像不像号商？

- 期望加载路径：`00_platform_routing_index.md` → `03_device_defense_platform_card.md`
- 合格回答标准：优先设备攻防；补充档案中心、风险运营中心；说明同设备只是聚集线索，不直接等于群控/号商。

### Case 3: 后端有高危操作，但前端没看到操作，怎么排查协议上号？

- 期望加载路径：`00_platform_routing_index.md` → `04_user_login_unified_log_platform_card.md` + `06_user_behavior_trace_platform_card.md`
- 合格回答标准：先查后端 method/action，再查前端行为反证；说明埋点缺失可能误判。

### Case 4: 怀疑设备是模拟器或刷机，先查哪个平台？

- 期望加载路径：`00_platform_routing_index.md` → `03_device_defense_platform_card.md`
- 合格回答标准：优先设备攻防；查 hardware_trusted、safe_status、appLaunchCount、apkPath；字段不确定时参考 todo。

### Case 5: 用户申诉策略误伤，想知道为什么命中。

- 期望加载路径：`00_platform_routing_index.md` → `05_tianshi_policy_engine_platform_card.md`
- 合格回答标准：优先天狮；补充档案中心和原始日志；说明策略命中不等于最终风险成立。

### Case 6: 1000 个样本要看留存和奖励提现趋势。

- 期望加载路径：`00_platform_routing_index.md`
- 合格回答标准：路由到 DataAgent/Hive 查询建议；说明 DataAgent 只负责 Hive/数仓聚合，不替代在线平台。

### Case 7: 设备平台查到 risk_label，但不知道含义。

- 期望加载路径：`00_platform_routing_index.md` → `03_device_defense_platform_card.md` → `99_todo_unknown_fields.md`
- 合格回答标准：不强解释未知标签；登记为待确认字段；不能进入 strong evidence。

### Case 8: 某视频被大量举报，想看内容风险和审核过程。

- 期望加载路径：`00_platform_routing_index.md` → `01_archives_center_platform_card.md`
- 合格回答标准：优先档案中心；补充风险运营中心和天狮；说明举报不等于事实。
