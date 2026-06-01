# General Runtime Summary Manifest v1

## 1. 定位

本 manifest 固化 Dennis 的通用风险研判工作模式。账号安全 / ATO 是已沉淀较深的场景之一，但不能把通用 workflow 收窄成只围绕 ATO、登录日志或 Hive 登录表。

通用主线：

```text
实时 readonly source 优先
-> 实时证据能闭合则给 evidence-based 结论
-> 实时证据不闭合则输出 partial evidence / missing_evidence
-> 需要时给分场景离线补证计划
-> DataAgent/Hive 执行前逐次确认
-> 单案可扩展为分簇 / 共性分析
```

以下 runtime summaries 是运行态专家认知底座：

- `account_security_runtime_summary_v1.md`
- `anti_crawler_runtime_summary_v1.md`
- `protocol_attack_runtime_summary_v1.md`
- `group_control_runtime_summary_v1.md`
- `cracked_app_runtime_summary_v1.md`
- `real_user_crowdsourcing_runtime_summary_v1.md`
- `activity_anti_cheating_runtime_summary_v1.md`
- `traffic_diversion_runtime_summary_v1.md`
- `traffic_anti_cheating_runtime_summary_v1.md`

它们用于：

- 默认轻量加载。
- 让所有风险场景默认按证据链工作，而不是堆 source。
- 给出场景判断、实时 source 计划、证据拆解、缺口、分场景离线补证方向、治理建议。
- 支持从单案抽象到批量分簇 / 共性分析。

它们**不替代**深度 Skill 原文。

## 2. 使用原则

### 2.1 实时优先

用户问风险研判时，先规划低成本、只读、实时 source。实时 source 可以来自 Login Logs、Archives、Track、RCP、Weapon、browser-backed fixed actions 或已登记 readonly API。实时证据能闭合时，直接给 evidence-based 结论；实时不闭合时，不强行定性。

实时研判输出必须包含：

- source_plan。
- evidence_chain。
- source_quality_matrix。
- strong / weak / counter evidence。
- missing_evidence。
- final_answer_boundary。

### 2.2 离线补证

实时证据不闭合时，输出离线补证计划。离线补证不是只补 Hive 登录表，不同风险场景对应不同数据源：

- 账号安全 / ATO：登录、注册、改密、换绑、扫码 / OAuth / token、发布、私信、资料修改和内容操作链路。
- 反作弊 / 群控：设备、请求、行为、策略命中、特征宽表、群体聚集和对照分母。
- 内容 / 导流：作品、评论、私信、主页、举报、处罚、策略命中、落地页和联系方式。
- 策略治理：策略版本、发布记录、命中样本、误伤样本、灰度指标和线上回流。

DataAgent/Hive 只能作为离线补证计划或用户逐次授权后的执行能力。上一次授权、同一会话或 P0/P1 数据不足都不构成默认授权。

### 2.3 多源单链路分析

Dennis 不是堆 source，而是围绕风险假设构建证据链。实时和离线只是取数方式不同，分析逻辑一致：

- 先定义风险假设和最小区分点。
- 再选择能验证该假设的 source。
- 每个 source 都必须给 source_quality 和时间窗口边界。
- 多 source 冲突时输出冲突原因、可信度和 missing_evidence，不强行定论。
- no_data、blocked、auth_failed、timeout、parse_error、partial 都不能作为低风险反证。

### 2.4 共性分簇

用户问“一批 / 举一反三 / 同类攻击 / 黑产模式”时，进入共性分簇或计划模式，而不是逐个在线 for-loop。通用维度包括：

- 时间窗。
- 设备 / IP / 网络。
- 行为序列。
- 内容 / 发布 / 互动。
- 策略命中。
- 前端活跃。
- 账号画像。
- 关联账号。

实时数据能支撑就输出 cluster evidence；实时不够时输出离线补证计划。代表样本只证明代表簇机制，不能直接泛化到全批。

### 2.5 深度能力按需读取

任何场景后续要做深度接入，应补齐：

- router。
- workflow。
- response contract。
- 实时 source contract。
- 分场景离线补证模板。
- short question regression。
- runtime slim / manifest。

## 3. 不替代的内容

runtime summaries 不替代：

- 深度 Skill 原文。
- review / eval 历史材料。
- 真实 case walkthrough。
- DataAgent parser / boundary / timeout 细则。

这些仍按需读取。

## 4. 为什么要有 runtime summaries

问题在于：

- 只保留“轻量定位”会让非 ATO 回答偏表面。
- 直接把全量 review / history 塞进 runtime 又会导致 token 成本过高。

runtime summaries 的作用就是把已有完整认知压缩成“运行态可读版本”。

## 5. 默认加载 / 按需读取 / 不建议注入

### 5.1 默认加载

- 通用 scenario contract 的摘要。
- 当前场景 router 的摘要。
- 当前场景 response contract 的摘要。
- 对应场景的 runtime summary。
- DataAgent boundary 摘要。
- timeout 摘要。

### 5.2 按需读取

- 深度 Skill 原文。
- query schema。
- parser 细则。
- join path。
- 结论阈值。

### 5.3 不建议默认注入

- 全量 review。
- 全量 eval。
- walkthrough 全文。
- 历史 case 大集合。
- 旧版本交叉说明全文。

## 6. 场景扩展方式

如果某个场景后续要变成深度样板，应复用通用路径：

1. 场景 router。
2. 实时 source workflow。
3. response contract。
4. 分场景离线补证 template。
5. source_quality / missing_evidence 边界。
6. runtime slim。
7. regression / smoke test。

## 7. 账号安全 / ATO 运行态补充

`account_security_runtime_summary_v1.md` 用于半开放 runtime 下的账号安全和 ATO 判断，尤其防止批量 ATO 只看统计汇总后误判攻击类型。

关键要求：

- 批量 ATO 不能只看 totalCount、kick_out 次数、password fail / CAPTCHA 次数。
- 发现 `HARMONY_` 设备、token issued、同 IP 多账号登录、token revoke / kick out、后续小米 / Android 改密或密码验证失败时，应优先考虑一键登录 / 三方授权接管 / 鸿蒙一键登录 ATO 候选。
- 必须抽取 3-5 个代表用户做逐条时序，比较撞库 ATO 与一键登录 ATO 的替代解释。
- 在线登录日志窗口不足时必须标记 `login_log_window_incomplete`，不能把 online no_data / 超窗 no_data 当作“无登录异常”或“无 ATO 风险”反证。
- 账号安全 Hive 取数计划必须按目标选表：成功登录查 `ks_rc_bs.ks_account_login_basic_info`；登录失败 / 撞库 / 暴力破解 / 改密查 `ks_rc_bs.dwd_risk_usr_accnt_login_orign_info`；Web RCP 查 `ks_rc_arch.antispam_feature_map_default_partitioned`；App RCP 查 `ks_raw_log_v2.antispam_feature_map_partitioned`。
- App / Web RCP plan 必须限制 `p_date + p_hourmin + p_action_type`；DataAgent 只作为 Hive / 数仓取数分析能力。
- browser-backed service 是 pure passthrough 职责：service 只输出固定 action envelope、transport metadata、capped body 和 batch transport matrix；Dennis 生成 observation、source quality、evidence card、missing evidence 和 final answer boundary，不依赖 service-side `normalized_observation` / `source_card` / `compat_summary`。
- browser-backed controlled parallel 只用于显式 source plan：ATO 可将 `login_logs_search`、`archives_user_profile`、`track_analysis_check_data_ready` 放入 `independent_parallel`，再让 `archives_photo_search` 和 `archives_user_analysis` 走 `auth_sensitive_serial`；RCP 归因保持 `rcp_event_detail -> rcp_event_feature_list` 依赖；大响应 source 走 `large_response_serial`；任何 `no_data` / `partial` / `timeout` 不作为低风险反证。
- ATO 单案裸问必须先收集实时 P0 source（登录、档案画像、档案用户分析、作品发布、Track readiness），再由 Dennis 从多源观察推导可疑锚点、候选控制端、`device_identity_consistency` 和历史基线输出业务 evidence card；`suspicious_anchor_discovery` 不是独立 source，Weapon / RCP 只是补证 source。

## 8. 数据调用边界

- 实时 readonly source 在字段齐备且已登记时可进入 source_plan。
- DataAgent/Hive 不默认执行；每一次实际执行都必须用户明确授权。
- 可以生成 query plan、推荐表、字段、窗口、聚合维度和 no-data 解释。
- 不得在 plan_mode 下伪装成已经查过离线数据。
- SQL-only、pending、partial、timeout、no_data 都不能强结论。

## 9. 结论

runtime summaries 的定位是：  
**在不加载全量历史材料的前提下，把通用证据链 workflow 和各场景专家认知带进运行态。**

这样既能提升回答质量，也能控制 token 成本。
