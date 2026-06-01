# General Runtime Summary Manifest v1

## 1. 定位

ATO 是当前已经打通的深度 DataAgent 闭环样板。

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
- 提升非 ATO 场景回答质量。
- 给出场景判断、证据拆解、低成本取证方向、治理建议。

它们**不替代**深度 Skill 原文。

## 2. 使用原则

### 2.1 轻量支持

非 ATO 场景默认只做：

- 场景判断。
- 攻击路径判断。
- 强 / 中 / 弱证据拆解。
- 缺失证据识别。
- 低成本取证方向。
- 治理建议。
- 人工复核边界。

### 2.2 不默认查数

- 非 ATO 场景默认不自动调用 DataAgent。
- 只有用户明确要求“查数 / 调 DataAgent / 生成查询问题”时，才进入 DataAgent。
- 高成本查询必须用户确认。

### 2.3 深度能力按需读取

非 ATO 场景如果后续要做深度接入，仍应按 ATO 模式补齐：

- router。
- workflow。
- response contract。
- DataAgent 取证模板。
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

如果某个非 ATO 场景后续要变成深度样板，应复用 ATO 的路径：

1. 场景 router。
2. workflow。
3. response contract。
4. DataAgent template。
5. 真实 POC。
6. runtime slim。

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
- browser-backed controlled parallel 只用于显式 source plan：ATO 可将 `login_logs_search`、`archives_user_profile`、`track_analysis_check_data_ready` 放入 `independent_parallel`，再让 `archives_user_analysis` 走 `auth_sensitive_serial`；RCP 归因保持 `rcp_event_detail -> rcp_event_feature_list` 依赖；大响应 source 走 `large_response_serial`；任何 `no_data` / `partial` / `timeout` 不作为低风险反证。
- ATO 单案裸问必须先做 `suspicious_anchor_discovery`，再围绕登录 / 控制链路、内容 / 行为链路、候选控制端、`device_identity_consistency` 和历史基线输出业务 evidence card；Track / Weapon / RCP 只是补证 source，不能替代可疑锚点发现。

## 8. 数据调用边界

- 非 ATO 场景默认不调 DataAgent。
- 用户明确要求查数才生成 query plan。
- 高成本查询必须确认。
- SQL-only / partial / timeout 不能强结论。

## 9. 结论

runtime summaries 的定位是：  
**在不加载全量历史材料的前提下，把非 ATO 场景的完整风控认知带进运行态。**

这样既能提升回答质量，也能控制 token 成本。
