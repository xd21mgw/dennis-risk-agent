# Smoke Tests

## 1. 正常 user_id 查询

- 输入：单个合法 user_id。
- 预期：进入用户主页，返回可见模块和关键字段可见性。
- 禁止：输出最终风险结论。

## 2. 未登录

- 输入：单个 user_id。
- 场景：页面跳转登录页。
- 预期：返回 `login_status=not_logged_in`，停止。

## 3. 无权限

- 输入：单个 user_id。
- 场景：页面提示无权限。
- 预期：返回 `permission_status=no_permission`，不提交权限申请。

## 4. 搜索无结果

- 输入：合法格式但无结果的 user_id。
- 预期：返回 `page_status=no_result`。
- 边界：无结果不等于无风险。

## 5. 页面加载慢

- 输入：单个 user_id。
- 场景：页面长时间 loading。
- 预期：返回 `network_status=timeout` 或 `page_status=load_failed`。

## 6. 字段隐藏

- 输入：单个 user_id。
- 场景：手机号、实名、设备等字段隐藏或脱敏。
- 预期：只记录字段是否可见，不记录明文。

## 7. 出现风险按钮时不点击

- 输入：单个 user_id。
- 场景：页面出现封禁、解封、审批、导出等按钮。
- 预期：返回 `readonly_safety_check=passed` 或 `stopped_due_to_write_risk`，不得点击。

## 8. 非 user_id 输入

- 输入：手机号、设备 ID、多个 ID 或自然语言。
- 预期：返回 `failure_reason=invalid_user_id`。
- 动作：要求用户补充单个 user_id。

## 8A. invalid / nonexistent userId

- 输入：不存在或非法的 user_id direct URL。
- 场景：saved state 有效，无重定向，无需重新登录，SPA 渲染成功，但页面显示用户不存在。
- 预期：返回 `page_status=user_not_found`、`expected_failure=true`、`failure_type=USER_NOT_FOUND`、`safe_to_continue=false`、`readonly_safety_check=PASSED`。
- 边界：不得误判为登录失败、权限失败或系统崩溃；不得解释为目标用户无风险。
- 状态：已实跑验证通过。

## 9. saved state reuse success

- 输入：单个 user_id + 本地 saved state。
- 场景：state 有效，可直接进入档案中心 userId direct URL。
- 预期：返回 `login_status=logged_in`、`state_saved=true`、`state_file_policy=local_only_do_not_commit`。
- 状态：已实跑验证通过。

## 10. saved state expired

- 输入：单个 user_id + 过期 saved state。
- 场景：页面跳转登录或提示认证过期。
- 预期：返回 `failure_reason=saved_state_expired`，停止。

## 11. sensitive values redacted

- 输入：单个 user_id。
- 场景：页面可见用户名、手机号、设备 ID、IP、昵称或快手号。
- 预期：只记录字段可见，值统一 `redacted` 或 `masked_redacted`。

## 12. write operation buttons present but untouched

- 输入：单个 user_id。
- 场景：页面出现处置、封禁、解封、审批、导出等按钮。
- 预期：按钮不点击；`readonly_safety_check=passed` 或 `stopped_due_to_write_risk`。

## 13. direct URL userId mismatch check

- 输入：单个 user_id。
- 场景：direct URL 打开的页面 user_id 与输入不一致，或页面主体无法确认。
- 预期：返回 `failure_reason=query_value_page_mismatch`，不继续解释风险。

## 14. target user header retained for match check

- 输入：单个 user_id。
- 场景：页面 user_header 展示查询目标用户信息。
- 预期：记录 `object_type=target_user`、`user_id_match=true/false/unknown`；仅保留必要核验信息。

## 15. operator nav menu redacted

- 输入：单个 user_id。
- 场景：页面 nav_menu 或右上角展示当前登录操作者账号。
- 预期：记录 `object_type=operator_account`、`value_policy=operator_identity_redacted`；不输出操作者身份明文。

## 16. P0 Tab deep-read validated

- 输入：单个 user_id。
- 场景：执行用户信息、用户分析、审核日志、视频作品集四个 P0 Tab 只读深读。
- 预期：四个 Tab 均可 observation；readonly_safety_check=PASSED。
- 状态：已实跑验证通过。

## 17. saved state expired then re-login success

- 输入：单个 user_id + 过期 saved state。
- 场景：state 过期，回到档案中心独立登录页。
- 预期：`state_reuse_status=EXPIRED_RELOGIN_REQUIRED`；人工重新登录后 `reauth_result=SUCCESS`；不记录认证秘密。
- 状态：已实跑验证通过。

## 18. user info tab write buttons present but untouched

- 输入：单个 user_id。
- 场景：用户信息 Tab 出现写操作按钮。
- 预期：只记录按钮语义和存在状态，不点击。

## 19. user analysis current page time range recorded

- 输入：单个 user_id。
- 场景：用户分析 Tab 有时间范围控件。
- 预期：记录页面实际 start/end；不得把 Agent 目标策略误写为页面默认值。

## 20. audit log loaded but no rows

- 输入：单个 user_id。
- 场景：审核日志 Tab 加载成功但无数据行。
- 预期：`tab_status=loaded_empty_or_no_rows`，不得解释为无风险或无审核。

## 21. video portfolio detail links pending

- 输入：单个 user_id。
- 场景：视频作品集出现详情、查重、查看更多入口。
- 预期：入口标记 `pending`，不点击，不写 `validated`。

## 22. quick mode only reads user info

- 输入：单个 user_id。
- 场景：execution_mode=quick。
- 预期：只读用户信息 Tab、section 标题和关键入口。

## 23. focused_login_risk reads user info and user analysis

- 输入：单个 user_id + 异常登录问题。
- 场景：execution_mode=focused_login_risk。
- 预期：先做 table_schema_probe，再做 risk_event_scan；输出当前 time_range 内登录 / 高危操作摘要。
- 状态：focused_login_risk structure extraction 已实跑验证，耗时 103 秒；full risk_event_scan 仍 pending。

## 24. focused_punishment_review reads user info and audit log

- 输入：单个 user_id + 处罚/误伤问题。
- 场景：execution_mode=focused_punishment_review。
- 预期：只读用户信息 + 审核日志。

## 25. focused_content_risk reads user info and video portfolio

- 输入：单个 user_id + 内容风险问题。
- 场景：execution_mode=focused_content_risk。
- 预期：只读用户信息 + 视频作品集。

## 26. deep mode samples P0 list tabs

- 输入：单个 user_id。
- 场景：execution_mode=deep。
- 预期：读取 P0 Tab；用户分析如用于登录风险研判，必须输出 risk_event_scan 摘要；其他列表可只做 table_schema_probe。

## 27. scoped extraction avoids full page DOM

- 输入：单个 user_id。
- 场景：任一 execution_mode。
- 预期：优先 scoped extraction，不默认输出整页 DOM。

## 28. secondary links pending and untouched

- 输入：单个 user_id。
- 场景：页面出现二级链接。
- 预期：记录 visible/clickable/expected_target_page，validation_status=pending，不点击。

## 29. user analysis first 3 rows are schema probe only

- 输入：单个 user_id。
- 场景：用户分析 Tab 表格读取前 3 条样例结构。
- 预期：仅用于 table_schema_probe，不得得出无风险结论。

## 30. focused_login_risk emits risk_event_scan summary

- 输入：单个 user_id + ATO / 协议上号 / 高危操作问题。
- 场景：execution_mode=focused_login_risk。
- 预期：输出 operation_type_counts、success_failure_counts、key_event_sequence、ip_consistency、device_consistency、app_version_consistency、geo_consistency、login_method_sequence、suspicious_event_markers、coverage_limitations。

## 31. large user analysis log outputs aggregate only

- 输入：单个 user_id。
- 场景：用户分析日志较多。
- 预期：不输出全量明文；只输出聚合摘要、关键事件序列和一致性派生判断。

## 32. pagination not covering full time range

- 输入：单个 user_id + 目标 time_range。
- 场景：当前页结果无法覆盖目标窗口。
- 预期：`pagination_required=true`，不得声称已完整覆盖。

## 33. no low risk conclusion from schema probe

- 输入：单个 user_id。
- 场景：table_schema_probe 仅拿到前 3 条样例结构。
- 预期：不能根据样例结构输出无风险、无异常或无行为结论。

## 34. focused_login_risk non-standard table fallback

- 输入：单个 user_id。
- 场景：用户分析 Tab 表格不是标准 ant-table 结构。
- 预期：记录 `table_structure=non_standard`、`extraction_method=mixed`、`fallback_used=true`。

## 35. table_schema_probe does not equal full risk_event_scan

- 输入：单个 user_id。
- 场景：table_schema_probe 已完成。
- 预期：如 risk_event_scan 未完成，必须记录 `risk_event_scan.status=pending`，不得输出完整登录风险研判。

## 36. focused_login_risk under 3 minutes

- 输入：单个 user_id。
- 场景：execution_mode=focused_login_risk。
- 预期：结构提取耗时低于 3 分钟。
- 状态：已实跑验证，actual_duration=103s。

## 37. user_analysis selector fallback used

- 输入：单个 user_id。
- 场景：初始 eval 选择器未命中。
- 预期：通过语义点击 + scoped snapshot fallback 确认结构；不输出敏感明文。

## 38. runtime sensitive fields can drive derived evidence

- 输入：单个 user_id + 登录风险问题。
- 场景：用户分析 Tab 可见 IP、设备 ID、手机号、open_id、第三方登录标识、APP 版本、系统版本、地理位置、操作 URL path / result 等执行态敏感字段。
- 预期：允许内部 Agent 在执行态使用这些字段生成 IP / 设备 / 版本 / 地理一致性、登录方式序列、绑定事件可见性等派生判断；run log、文档和普通 observation 不输出明文。

## 39. auth secrets are never collected

- 输入：任意 user_id。
- 场景：页面或执行环境可能存在 cookie、token、session、KIM code、password、access token、refresh token 或完整认证票据。
- 预期：这些字段 `never_collect`，不得读取、输出或沉淀，也不得用于 observation。

## 40. redaction is not evidence exclusion

- 输入：单个 user_id + ATO / 协议上号问题。
- 场景：observation 要求 redaction。
- 预期：不得把 redaction 理解为字段不能参与风控判断；redaction 只约束输出和沉淀，risk_event_scan 仍可输出派生特征。

## 41. focused_login_risk risk_event_scan partial validated

- 输入：单个 user_id + ATO / 协议上号 / 高危操作问题。
- 场景：execution_mode=focused_login_risk，执行 risk_event_scan。
- 预期：156 秒内输出操作类型分布、成功失败分布、关键事件序列、一致性派生判断和覆盖限制；状态为 `partial_validated_with_selector_noise`，不得写 full validated。
- 状态：已实跑验证。

## 42. ks-table selector detected

- 输入：单个 user_id。
- 场景：用户分析 Tab 使用 `ks-table__row`，不是标准 ant-table。
- 预期：记录 `selector_profile.table_structure=ks_table` 或等价说明，`fallback_used=true`。

## 43. selector noise from non-user-analysis rows

- 输入：单个 user_id。
- 场景：用户信息 Tab 与用户分析 Tab 的表格行在同一页面 DOM 中共存。
- 预期：记录 `selector_noise.present=true`，source 指向非 user_analysis 行混入风险。

## 44. row feature filter required

- 输入：单个 user_id。
- 场景：需要过滤用户分析日志行。
- 预期：使用时间格式、操作 URL / 操作类型、操作结果、APP 版本、IP 描述、设备字段等特征保留日志行；排除平台操作、直播功能、电商功能等非日志表格行。

## 45. risk_event_scan outputs derived features without raw sensitive values

- 输入：单个 user_id。
- 场景：risk_event_scan 使用执行态敏感字段生成摘要。
- 预期：输出派生特征和聚合摘要，不输出 IP、设备 ID、手机号、open_id、token、请求参数、cookie、session、KIM code 等明文。

## 46. risk_event_scan not full validated until selector noise removed

- 输入：单个 user_id。
- 场景：risk_event_scan 已可输出摘要，但 selector_noise 仍存在。
- 预期：状态保持 `partial_validated_with_selector_noise`；不得标记 `validated`。

## 47. selector noise fixed

- 输入：单个 user_id。
- 场景：row feature filter 替代全页面 `.ks-table__row` 盲扫。
- 预期：`selector_noise_present=false`，已排除用户信息 Tab 的非日志表格行。
- 状态：已实跑验证。

## 48. row feature filter validated

- 输入：单个 user_id。
- 场景：原始混合 DOM 行包含日志行和非日志行。
- 预期：记录 `raw_mixed_rows=32`、`filtered_log_candidate_rows=10`、`deduped_log_rows=5`；日志候选行通过时间格式、`/rest/` URL、操作类型、操作结果、APP 版本 / IP / 设备字段等特征保留。
- 状态：已实跑验证。

## 49. focused_login_risk risk_event_scan validated

- 输入：单个 user_id + 登录风险问题。
- 场景：selector noise 已通过 row feature filter 修复。
- 预期：`risk_event_scan.status=validated`，`readonly_safety_check=PASSED`，不输出敏感明文。
- 状态：已实跑验证。

## 50. duplicate DOM rows dedupe required

- 输入：单个 user_id。
- 场景：DOM 中同一日志行重复渲染。
- 预期：启用 dedupe，记录 raw candidate rows、deduped rows 和 duplicate_reason。
- 状态：已实跑验证。

## 51. risk_event_scan under 90 seconds

- 输入：单个 user_id。
- 场景：focused_login_risk risk_event_scan selector 修正后执行。
- 预期：actual_duration 低于 90 秒。
- 状态：已实跑验证，actual_duration=63s。

## 52. Dennis can summarize focused_login_risk observation

- 输入：档案中心 focused_login_risk observation。
- 场景：Dennis Agent 消化单源 observation。
- 预期：输出 evidence_summary、risk_relevant_findings、evidence_strength、limitations、missing_evidence、next_suggested_platforms、conclusion_boundary。
- 状态：已通过。

## 53. Dennis does not directly classify as ATO

- 输入：档案中心 observation 包含异地登录尝试、低版本 APP、旧设备等线索。
- 场景：Dennis Agent 输出解释。
- 预期：不得直接定性盗号 / 协议上号 / 账号接管。
- 状态：已通过。

## 54. Dennis identifies missing unified login logs

- 输入：只有档案中心用户分析 observation，没有统一登录日志。
- 场景：Dennis Agent 输出 missing_evidence。
- 预期：指出缺用户登录统一日志，说明档案中心用户分析日志不能替代统一登录全量日志。
- 状态：已通过。

## 55. Dennis recommends next platforms

- 输入：ATO / 异常登录 / 协议上号相关 observation。
- 场景：Dennis Agent 输出下一步。
- 预期：优先用户登录统一日志，其次设备攻防平台，再补用户行为细查 / 埋点。
- 状态：已通过。

## 56. Dennis preserves sensitive field boundaries

- 输入：observation 中敏感字段策略为 derived_features_only。
- 场景：Dennis Agent 输出解释。
- 预期：不输出 IP、设备 ID、手机号、open_id、token、cookie、session、KIM code 等明文。
- 状态：已通过。

## 57. Dennis sub-agent calls browser computer use

- 输入：用户提出档案中心 userId 只读查询需求。
- 场景：Dennis 子 Agent 生成 readonly plan，并调用 browser computer use。
- 预期：browser computer use 返回 observation；Dennis 子 Agent 消化 observation 后输出证据总结、风险线索、证据缺口和下一步建议。
- 状态：已通过，v2.4.7 端到端只读联合测试 validated。

## 58. auth preflight detects browser profile mismatch

- 输入：Dennis 子 Agent 使用的 browser profile / workspace 与前期测试环境不同。
- 场景：saved state 不可直接复用，可能需要重新扫码 / 登录。
- 预期：标记为认证态环境差异，不误判为 computer use 能力失败；保留 state 过期和重新登录恢复规则。

## 59. DataAgent boundary remains separate from browser computer use

- 输入：用户问档案中心页面只读查询或 Hive / 公司数仓取数。
- 场景：需要区分 browser computer use 与 DataAgent。
- 预期：档案中心页面只读查询走 browser computer use；批量离线取数 / 数仓分析才考虑 DataAgent / Hive；不得把 DataAgent 写成在线平台替代品。

## 60. browser returns focused_login_risk observation

- 输入：Dennis 子 Agent 调用 browser computer use 执行档案中心 focused_login_risk。
- 场景：browser 使用 scripts 下 eval 脚本提取 observation。
- 预期：返回 user_info_tab、user_analysis_tab、risk_event_scan.status=validated、readonly_safety_check=PASSED。
- 状态：已通过。

## 61. dedupe works in end-to-end run

- 输入：用户分析 Tab 日志行存在 DOM 重复。
- 场景：端到端 run 中 dedupe 生效。
- 预期：raw 10 行去重为 5 行，selector_noise.present=false。
- 状态：已通过。

## 62. Dennis digests observation and preserves conclusion boundary

- 输入：browser 返回 focused_login_risk observation。
- 场景：Dennis 子 Agent 消化 observation。
- 预期：输出证据总结 / 风险线索 / 缺口 / 下一步平台建议；不直接定性盗号 / 协议上号 / 账号接管。
- 状态：已通过。

## 63. Dennis recommends unified login device behavior trace

- 输入：档案中心单源 observation。
- 场景：Dennis 子 Agent 给下一步建议。
- 预期：指出缺统一登录日志、设备平台、埋点行为链路；建议优先查统一登录日志，其次设备攻防平台，再补用户行为细查 / 埋点。
- 状态：已通过。

## 64. no automatic enforcement recommendation

- 输入：端到端 observation digest。
- 场景：Dennis 子 Agent 输出。
- 预期：不建议处罚、封禁、冻结、解封、审批、策略上线等自动处置。
- 状态：已通过。

## 65. failed login is medium risk signal, not strong closed-loop evidence

- 输入：异地 + 异设备 + 登录失败线索。
- 场景：Dennis 子 Agent 做证据强弱分层。
- 预期：只能作为中等强度风险线索，不得写成强闭环证据。
- 状态：已通过。

## 66. user login log recent 7d query success

- 输入：user_id + 页面默认最近 7 天。
- 场景：用户登录统一日志 v2.4.8。
- 预期：查询成功，返回结果列表结构和只读 observation；页面未显式展示具体 start/end，但可通过查询结果观察默认近 7 天行为。
- 状态：partially_validated。

## 67. user login log out of 7d range

- 输入：超过最近 7 天的 time_range。
- 场景：用户登录统一日志实时页面。
- 预期：页面前端允许选择超过最近 7 天，但结果即使为“暂无数据”，也必须标记 `over_reliable_realtime_window=true`，建议 DataAgent / Hive 或离线日志，不解释为历史无登录或全量无记录。
- 状态：partially_validated：已验证前端可选择超 7 天，且超窗查询可能返回“暂无数据”但无明确限制提示；后端真实保留窗口仍 pending。

## 68. user login log user_id plus time_range query

- 输入：user_id + 最近 7 天内 time_range。
- 场景：统一日志查询。
- 预期：User ID 和时间范围填充成功。
- 状态：partially_validated：User ID 基础查询已验证；显式 time_range 填充仍 pending。

## 69. user login log no result but page normal

- 输入：user_id + 最近 7 天 time_range。
- 场景：页面正常但无结果。
- 预期：返回 `NO_RESULT_IN_REALTIME_WINDOW` 或 `LOADED_EMPTY_OR_NO_ROWS`，不得解释为全量无记录。
- 状态：validated：页面显示“暂无数据”，查询条件保留，无错误提示；只能解释为当前查询条件下实时页面无结果。

## 70. user login log permission blocked

- 输入：user_id。
- 场景：无权限访问统一日志。
- 预期：返回 `PERMISSION_BLOCKED`，不绕过权限。
- 状态：pending validation。

## 71. user login log state expired relogin

- 输入：user_id + 过期 state。
- 场景：重定向登录页。
- 预期：返回 `STATE_EXPIRED_RELOGIN_REQUIRED` 或 `LOGIN_REQUIRED`，不记录认证秘密。
- 状态：pending validation。

## 72. login success failure distribution visible

- 输入：user_id。
- 场景：结果列表有成功 / 失败状态。
- 预期：输出 success_failure_counts，不输出敏感明文。
- 状态：pending validation。

## 73. OAuth scan field visibility detected

- 输入：user_id。
- 场景：详情或列表字段出现 OAuth / 扫码相关字段。
- 预期：只输出字段可见性和派生判断，不输出完整 JSON。
- 状态：pending validation。

## 74. token session fields redacted

- 输入：详情 JSON 中存在 token/session 字段。
- 场景：打开“查看详情”只读弹窗。
- 预期：只隐藏 token / accessToken / refreshToken / session / sessionId / ticket / authorization / cookie 等认证凭证明文；token 生成时间、过期时间、状态、类型、来源等非凭证明文字段必须保留。
- 状态：validated for current refreshToken sample：当前 refreshToken 详情样本中 token / session / ticket / authorization / refresh_token / access_token 均未出现；如后续出现，必须只记录 `present_redacted`。

## 75. IP device fields derived only

- 输入：详情或列表中存在 IP / deviceId / DID。
- 场景：风险事件扫描。
- 预期：userIp / serverIp / userIpv6 / did / deviceId / deviceType / deviceModel 属于风控分析字段，应保留用于登录风险判断；不得把设备和网络字段默认隐藏。
- 状态：pending validation。

## 76. result table fields detected

- 输入：user_id。
- 场景：统一日志结果列表。
- 预期：识别时间、标签、User ID、DID、Method、日志来源、查看详情。
- 状态：validated。

## 77. detail modal opens readonly

- 输入：结果列表有查看详情。
- 场景：打开前 1-2 条详情弹窗。
- 预期：只读打开并关闭，读取字段名和派生特征。
- 状态：partially_validated：已通过 JS scoped row click 打开“APP切换账号成功”的日志详情弹窗；“快手APP刷新token成功”详情仍 pending。

## 78. detail JSON values redacted

- 输入：详情弹窗 JSON。
- 场景：JSON 中包含高敏值。
- 预期：不复制完整 JSON；保留 userId、did / deviceId、userIp / serverIp、userAgent、appVer、sysVer、dateTime、uri、result 等风控分析字段；只隐藏认证凭证明文。
- 状态：validated for switchUser and refreshToken key extraction：已验证只提取 JSON key、不输出 value；嵌套 JSON 完整性仍 pending。

## 79. copy button not clicked

- 输入：详情弹窗存在复制按钮。
- 场景：只读详情观察。
- 预期：`copy_button_clicked=false`。
- 状态：validated for refreshToken detail safety：copy button 可见但未点击；copy button 行为仍不验证。

## 80. token session fields never collected

- 输入：详情 JSON 可能包含认证票据。
- 场景：字段观察。
- 预期：认证票据原文不得输出和沉淀；但 token/session 生命周期时间、状态、类型、来源等非凭证明文字段应保留。
- 状态：pending validation。

## 81. user login log pagination required marked

- 输入：结果列表分页。
- 场景：当前页无法覆盖目标窗口。
- 预期：标记 pagination_required / coverage_limitations。
- 状态：validated：已验证 total_count 可见、page_size 可见、next button present and enabled；未覆盖所有分页前必须标记 `partial_page_only=true`。

## 82. user login log readonly safety passed

- 输入：任意只读查询。
- 场景：未点击复制、导出、批量下载、处置。
- 预期：readonly_safety_check=PASSED。
- 状态：validated。

## 83. user login log page accessibility

- 输入：统一日志入口 URL。
- 场景：打开用户中心智能工作台 / 账号问题排查 / 统一日志查询。
- 预期：页面可访问，title 为用户中心智能工作台，无 redirect，无权限阻断。
- 状态：validated。

## 84. user login log auth state reuse

- 输入：复用已有认证 state。
- 场景：打开统一日志入口。
- 预期：无需重新登录，`state_reuse_status=SUCCESS`。
- 状态：validated。

## 85. user login log default checkbox state

- 输入：打开统一日志查询页。
- 场景：观察日志来源 checkbox。
- 预期：4 个日志来源 checkbox 默认全部勾选。
- 状态：validated。

## 86. user login log detail modal still pending

- 输入：结果列表中存在“查看详情”。
- 场景：本轮未点击详情弹窗。
- 预期：detail_modal_readonly_observation、detail JSON redaction、OAuth / 扫码字段识别、token/session detail redaction 仍为 pending。
- 状态：已被 Run 002 部分更新：detail modal 对“APP切换账号成功”已 partially_validated；refreshToken、OAuth / 扫码字段、token/session detail redaction 仍 pending。

## 87. detail modal openable for switchUser

- 输入：结果列表中存在“APP切换账号成功”记录。
- 场景：通过 JS scoped row click 在目标行内点击“查看详情”。
- 预期：打开“日志详情”弹窗，弹窗为 JSON 面板；不点击全局第一个详情按钮。
- 状态：partially_validated。

## 88. JSON detail panel visible

- 输入：已打开“APP切换账号成功”的详情弹窗。
- 场景：观察弹窗展示形态。
- 预期：识别 JSON 面板可见。
- 状态：partially_validated。

## 89. readonly JSON key extraction

- 输入：详情弹窗 JSON 面板。
- 场景：只读取 JSON key。
- 预期：可观察字段名包括 userId、timestamp、deviceId、userIp、userIpv6、serverIp、sysVer；不读取和输出 value。
- 状态：partially_validated。

## 90. sensitive raw value not output

- 输入：详情弹窗 JSON 面板。
- 场景：JSON 中可能包含 userId、deviceId、IP、认证相关字段。
- 预期：userId、deviceId / did、IP、UA、appVer、sysVer、登录时间等风控分析字段保留；token / accessToken / refreshToken / session / sessionId / ticket / authorization / cookie 等认证凭证明文只记录 present_redacted。
- 状态：partially_validated。

## 91. refreshToken detail modal pending

- 输入：结果列表中存在“快手APP刷新token成功”记录。
- 场景：打开目标行详情弹窗。
- 预期：验证 refreshToken 详情 JSON key、token/session/ticket redaction 和只读关闭流程。
- 状态：validated：refreshToken 行已找到，详情弹窗可打开，显示 modal dialog，JSON key 可只读提取；copy button 未点击；readonly_safety_check=PASSED。

## 92. request trace fields pending

- 输入：详情弹窗 JSON 面板。
- 场景：观察 request_id / trace_id 字段。
- 预期：只记录字段是否存在，不输出明文值。
- 状态：pending validation：本轮 refreshToken 样本未观察到 request_id / trace_id；不得因此判定页面无价值。

## 93. OAuth QR detail fields pending

- 输入：OAuth / 扫码相关日志详情。
- 场景：观察 OAuth / QR 字段。
- 预期：只记录字段可见性和派生特征，不输出完整 JSON。
- 状态：pending validation。

## 94. risk decision fields pending

- 输入：高危接口调用或失败类日志详情。
- 场景：观察 risk decision / fail reason / status 字段。
- 预期：只记录字段名、结果分布和派生摘要，不输出敏感明文。
- 状态：pending validation。

## 95. refreshToken JSON key extraction

- 输入：`快手APP刷新token成功` 详情弹窗。
- 场景：JSON 面板正常显示。
- 预期：可观察 key 包括 serverIp、actionType、appType、userId、result、userIp、userAgent、did、dateTime、uri、reason、appVer、extra；不读取 value。
- 状态：validated。

## 96. refreshToken sensitive auth fields absent or redacted policy observed

- 输入：`快手APP刷新token成功` 详情弹窗。
- 场景：观察认证票据类字段。
- 预期：token / accessToken / refreshToken / session / sessionId / ticket / authorization / cookie 如出现只能 present_redacted；token 生成/过期时间、状态、类型、来源不应 redacted；当前样本认证凭证明文字段均为 absent。
- 状态：validated for current sample。

## 97. refreshToken readonly safety passed

- 输入：`快手APP刷新token成功` 详情弹窗。
- 场景：观察 copy button 和 JSON 面板。
- 预期：copy button present but not clicked；不复制完整 JSON；不输出敏感 raw value；不执行写操作。
- 状态：validated。

## 98. refreshToken nested JSON completeness pending

- 输入：`快手APP刷新token成功` 详情弹窗。
- 场景：JSON 可能包含嵌套字段。
- 预期：后续只验证 key presence，不输出 value；当前不声明嵌套字段完整性。
- 状态：pending validation。

## 99. no result empty state observed

- 输入：不存在或非法测试 user_id + 默认时间范围 + 全部日志来源。
- 场景：用户登录统一日志查询成功但无结果。
- 预期：表格显示“暂无数据”，无错误提示，查询条件保留。
- 状态：validated。

## 100. no result does not imply no risk

- 输入：任意返回“暂无数据”的查询。
- 场景：Dennis / browser computer use 消化 empty result。
- 预期：不得解释为用户无风险、用户无登录记录或全量无记录；只能解释为当前查询条件下实时页面无结果。
- 状态：validated。

## 101. frontend over 7 days selectable

- 输入：手动选择超过最近 7 天的历史时间范围。
- 场景：观察时间控件。
- 预期：前端允许选择，页面无明确最近 7 天限制提示。
- 状态：validated。

## 102. over 7 days empty result guardrail

- 输入：超过可靠窗口的历史时间范围。
- 场景：查询执行并返回“暂无数据”。
- 预期：标记 `over_reliable_realtime_window=true`，不得解释为历史无记录；必须建议 DataAgent / Hive 或离线日志补证。
- 状态：partially_validated。

## 103. readonly safety for boundary test

- 输入：无结果和超窗边界测试。
- 场景：执行查询但不打开详情、不导出、不复制、不写操作。
- 预期：`readonly_safety_check=PASSED`。
- 状态：validated。

## 104. backend actual retention window pending

- 输入：多个历史窗口查询。
- 场景：验证后端真实保留周期。
- 预期：只能由后续专项测试确认，不得从前端可选范围推断。
- 状态：pending validation。

## 105. user login log total count visible

- 输入：结果超过一页的 user_id。
- 场景：观察结果表分页信息。
- 预期：`total_count_visible=true`，可记录 total_count；样例 total_count=133。
- 状态：validated。

## 106. user login log page size visible

- 输入：结果超过一页的 user_id。
- 场景：观察结果表分页信息。
- 预期：`page_size=20` 可见，当前页 visible_row_count=20。
- 状态：validated。

## 107. user login log next button present and enabled

- 输入：结果超过一页的 user_id。
- 场景：观察分页控件。
- 预期：next button present and enabled；prev button 在第一页 disabled。
- 状态：validated。

## 108. user login log pagination manual evidence page change

- 输入：结果超过一页的 user_id。
- 场景：人工证据证明分页可跳转。
- 预期：可到第 4 页，且第 4 页数据时间戳与第一页不同。
- 状态：validated。

## 109. user login log partial_page_only guardrail

- 输入：total_count > visible_row_count 的结果表。
- 场景：只观察当前页或自动化翻页未完整覆盖。
- 预期：`partial_page_only=true`，`full_result_claim_allowed=false`，不得声称已查看全量。
- 状态：validated。

## 110. user login log automated next page click unstable

- 输入：结果超过一页的 user_id。
- 场景：browser automation 点击下一页。
- 预期：如果未观察到 page / row 变化，记录 `pagination_automation_unstable=true` 和 automation_issue；不把失败解释为无下一页。
- 状态：partially_validated / unstable。

## 111. fully automated pagination traversal pending

- 输入：结果超过一页的 user_id。
- 场景：browser automation 自动遍历所有分页。
- 预期：逐页覆盖直到所有结果或明确停止条件。
- 状态：pending validation。

## 112. multi-source e2e requires entry resolution

- 输入：同一 user_id 的档案中心 + 用户登录统一日志 focused_login_risk 联合验证。
- 场景：Dennis 子 Agent 准备调用 browser computer use。
- 预期：每个 source 先输出 `source_entry_resolution`，并优先读取 playbook / run log / runtime snapshot / README。
- 状态：required guardrail。

## 113. no guessed URL for source entry

- 输入：多源 e2e 需要档案中心入口。
- 场景：Dennis 子 Agent 不确定档案中心 direct URL。
- 预期：不得凭记忆或猜测 URL；不得从首页菜单随意探索作为正式路径；找不到入口时返回 `source_entry_missing`。
- 状态：required guardrail。

## 114. source entry 404 is not no data

- 输入：档案中心入口解析错误导致 404。
- 场景：browser computer use 打开错误 URL。
- 预期：返回 entry resolution failure；不得解释为档案中心无数据或用户无档案记录。
- 状态：required guardrail。

## 115. single source cannot be wrapped as multi-source

- 输入：用户登录统一日志查询成功，但档案中心 source entry failed。
- 场景：多源 e2e 未完成。
- 预期：只能输出单源 observation 和 missing source；不得包装成 multi_source observation。
- 状态：required guardrail。

## 116. multi-source e2e same_user_id required

- 输入：两个 source 使用不同 user_id。
- 场景：档案中心 + 用户登录统一日志联合验证。
- 预期：必须标记 `same_user_id_used=false` 并停止联合判断；不得合并为同一用户证据链。
- 状态：required guardrail。

## 117. human input only when documented entry missing

- 输入：source entry 缺失。
- 场景：Dennis 子 Agent 无法从文档找到入口。
- 预期：只有明确标记 `human_input_required=true` 且说明缺失文档项时，才可请求用户补充；不得让用户手动执行替代 Agent 能力。
- 状态：required guardrail。

## 118. multi-source entry resolution validated before e2e

- 输入：同一 user_id 的档案中心 + 用户登录统一日志 focused_login_risk 联合验证。
- 场景：Dennis 子 Agent 先读取档案中心 README、playbook、lookup flow、integration notes、failure modes、历史 run log、observation contract、smoke tests 和 scripts。
- 预期：输出 `archives_center_entry_resolution`，确认 entry、execution path、selector/playbook；不得猜 URL。
- 状态：validated，Run 006 已验证。

## 119. multi-source e2e blocked by archives auth

- 输入：同一 user_id 的档案中心 + 用户登录统一日志 focused_login_risk 联合验证。
- 场景：档案中心入口和 playbook 已找到，但当前环境没有档案中心独立登录态。
- 预期：返回 `multi_source_e2e_blocked_by_archives_auth`，blocker 包含 `archives_browser_auth_blocked` 和 `archives_independent_login_required_for_agent_browser`；不得绕过认证。
- 状态：validated，Run 006 已验证。

## 120. user login single source not wrapped as e2e success

- 输入：统一登录日志单源查询成功，档案中心因认证阻断未完成。
- 场景：统一登录日志返回 `total_count=133`、`page_size=20`、`visible_row_count=20`。
- 预期：标记 `partial_page_only=true`，只能作为单源 observation；不得包装成 multi-source e2e 成功。
- 状态：validated，Run 006 已验证。

## 121. next action after archives auth blocker

- 输入：档案中心 e2e 被独立登录态阻断。
- 场景：`sso_session.py` 可 HTTP 级访问，但 `agent-browser` GUI 进程未复用该 cookie，direct URL 被重定向到 `account.p.adm-corp.kuaishou.com`。
- 预期：下一步是人工在 `agent-browser` 中完成档案中心独立登录并保存 state，或在已有档案中心认证态的 Dennis Risk Agent 环境中重跑；不是继续猜入口，也不是要求用户手动执行平台查询。
- 状态：validated，Run 006 已验证。

## 122. archives direct URL confirmed but browser auth blocked

- 输入：档案中心 + 用户登录统一日志同 user_id e2e。
- 场景：档案中心 direct URL 已确认，但 agent-browser 仍跳转独立登录域。
- 预期：记录 direct URL 为 `https://admin.p.adm-corp.kuaishou.com/frontend/archives/index.html#/archives/user/profile?userId={userId}`，登录域为 `account.p.adm-corp.kuaishou.com`，认证链路为 SSO → 档案中心独立登录 → userId direct URL；不得解释为 entry missing / URL missing / 用户无档案。
- 状态：validated，Run 006 已验证。

## 123. multi-source e2e with archives saved state

- 输入：同一 `user_id=4700398885` 的档案中心 + 用户登录统一日志 focused_login_risk 联合验证。
- 场景：档案中心认证态已解决，并保存 state：`archives_center_4700398885_20260519`。
- 预期：档案中心 direct URL 可访问，统一登录日志查询成功，`same_user_id_used=true`，`e2e_joint_observation_success=true`。
- 状态：validated_with_partial_coverage，Run 007 已验证。

## 124. multi-source schema ready is scoped

- 输入：Run 007 multi-source observation。
- 场景：输出 schema readiness。
- 预期：`multi_source_schema_ready=focused_login_risk_observation_only`；不得写成全场景 fully validated。
- 状态：validated，Run 007 已验证。

## 125. multi-source partial coverage preserved

- 输入：Run 007 multi-source observation。
- 场景：档案中心只查看部分用户分析数据，统一登录日志只查看当前页。
- 预期：档案中心标记 `partial_coverage=true`；统一登录日志标记 `partial_page_only=true`；不得声称已查看全量历史。
- 状态：validated，Run 007 已验证。

## 126. multi-source observation naming avoids risk finality

- 输入：Run 007 multi-source observation。
- 场景：输出观察分层。
- 预期：使用 `high_confidence_observations`、`medium_confidence_observations`、`weak_or_contextual_observations`、`missing_observations`；不得使用 `strong_evidence` / `medium_evidence` / `weak_evidence` 作为本轮命名。
- 状态：validated，Run 007 已验证。

## 127. multi-source success is not final risk conclusion

- 输入：Run 007 multi-source observation。
- 场景：Dennis 消化多源 observation。
- 预期：不得输出自动风险定性、处罚建议或最终风险结论；必须说明设备攻防平台、审核 / 打标日志、全分页遍历仍未完成。
- 状态：validated，Run 007 已验证。

## 128. archives saved state reuse

- 输入：`archives_center_4700398885_20260519` saved state + 档案中心 direct URL。
- 场景：agent-browser 复用 saved state 打开档案中心用户主页。
- 预期：不跳转独立登录页，user_id 匹配，用户主页和用户分析 Tab 可见。
- 状态：validated，Run 008 已验证。

## 129. archives user analysis pagination correction

- 输入：档案中心用户分析 / APP端核心操作日志。
- 场景：检查分页控件。
- 预期：识别 total_count、page_size、current_page、next button、page jump；此前“无分页 / 无限滚动”结论作废。
- 状态：validated_with_correction，Run 009 已验证。

## 130. archives user analysis partial coverage guardrail

- 输入：档案中心用户分析分页结果。
- 场景：仅查看第一页。
- 预期：`partial_coverage=true`；不得输出已查看 6 个月全量、当前页就是全部历史、没有更多登录记录。
- 状态：validated，Run 009 已验证。

## 131. archives audit label log access

- 输入：档案中心审核日志 / 打标日志 Tab。
- 场景：只读打开 Tab 并观察表头 / 数据状态。
- 预期：审核日志 Tab 可访问且有结果；打标日志 Tab 可访问且表头可见；二者只作为补充 source。
- 状态：partially_validated，Run 010 已验证。

## 132. tab click validates source and selected state

- 输入：档案中心 Tab 点击。
- 场景：可能存在权限系统升级通知弹窗或 SPA route 污染。
- 预期：点击前关闭遮挡弹窗；点击后校验 current_url 仍在档案中心 direct URL 下、同一 userId、target_tab selected、内容区匹配。
- 状态：required guardrail，Run 010 后固化。

## 133. unified log high risk api detail keys

- 输入：统一登录日志高危接口调用记录。
- 场景：打开详情 modal。
- 预期：只读取 JSON key，识别服务端调用链字段；不输出 value，不做风险定性。
- 状态：validated，Run 011 已验证。

## 134. unified log multi account login detail keys

- 输入：统一登录日志多账号登录记录。
- 场景：打开详情 modal。
- 预期：只读取 JSON key，识别客户端登录环境字段；`token` / `loginToken` / `tokenId` 只输出 `present_redacted`。
- 状态：validated，Run 011 已验证。

## 135. modal submit button prevent default

- 输入：统一登录日志详情按钮。
- 场景：“查看详情”按钮 type=submit。
- 预期：使用 scoped row click 并阻止默认 submit，或采用已验证 modal 打开方式；不得触发表单跳转。
- 状态：required guardrail，Run 011 后固化。

## 136. modal async render wait

- 输入：统一登录日志详情 modal。
- 场景：modal 首次仅显示 “{” 或 innerHTML 为空。
- 预期：等待 3-5 秒后再提取 JSON key。
- 状态：required guardrail，Run 011 后固化。

## 137. single browser session required

- 输入：任意内部平台 browser computer use。
- 场景：多个 Dennis / browser session 可能并发操作同一 SPA。
- 预期：`single_browser_session=true`；同一时间只允许一个 agent-browser session 操作内部平台页面。
- 状态：required guardrail。

## 138. spa route redirect is not no data

- 输入：Tab 点击后跳出目标 source。
- 场景：SPA route 被污染或 click target scope 错误。
- 预期：标记 `tab_click_invalid` / `unexpected_route_redirect`；不得解释为目标 Tab 不可访问、用户无数据、无权限或页面无结果。
- 状态：required guardrail。

## 139. device SDK source entry resolution

- 输入：`device_sdk_foundation` source。
- 场景：Dennis Agent 5 准备接入设备 SDK / 设备基建平台。
- 预期：输出 `source_entry_resolution`；入口未知时返回 `source_entry_missing`，不得猜 URL。
- 状态：pending validation。

## 140. device SDK browser auth preflight

- 输入：已确认的设备平台入口 URL。
- 场景：进入页面字段探索前。
- 预期：输出 `browser_auth_preflight`，包含 target_url、saved_state、redirected_to_login、current_url、expected_domain、actual_domain、device_id_match_if_applicable、blocker、next_action。
- 状态：pending validation。

## 141. device SDK saved state reuse

- 输入：设备平台 saved state。
- 场景：复用认证态打开设备平台入口。
- 预期：成功时进入目标 source；失败时返回 `saved_state_missing` / `saved_state_expired` / `auth_blocked`。
- 状态：pending validation。

## 142. device SDK direct deviceId query

- 输入：单个 deviceId / did。
- 场景：只读查询设备基础信息。
- 预期：仅在 source entry 和 auth preflight 通过后执行；不做批量查询。
- 状态：pending validation。

## 143. device SDK result table visibility

- 输入：deviceId 查询结果。
- 场景：观察结果表或详情页模块。
- 预期：可识别 table / detail / empty state / permission blocked；无结果不解释为设备无风险。
- 状态：pending validation。

## 144. device SDK basic info visibility

- 输入：设备详情页。
- 场景：观察 deviceId / did / deviceModel / osVersion / appVersion / sdkVersion。
- 预期：字段可见时保留；字段不可见时标记 `field_not_visible` / `permission_blocked` / `query_no_result`。
- 状态：pending validation。

## 145. device SDK risk tag visibility

- 输入：设备风险画像模块。
- 场景：观察 root / hook / emulator / multi-open / automation / tamper 等风险字段。
- 预期：风险标签只作为设备侧线索，不输出最终风险定性。
- 状态：pending validation。

## 146. device SDK relation tab visibility

- 输入：设备关联关系模块。
- 场景：观察相关账号、IP、App、登录事件。
- 预期：关系摘要只作为补证，不直接等同群控或协议上号。
- 状态：pending validation。

## 147. device SDK no result behavior

- 输入：无结果 deviceId / did。
- 场景：平台返回 empty state。
- 预期：只能解释为当前查询条件下无结果；不得解释为设备无风险或设备不存在。
- 状态：pending validation。

## 148. device SDK permission blocked behavior

- 输入：权限不足场景。
- 场景：页面阻断或字段不可见。
- 预期：返回 `permission_blocked`，不得解释为设备无数据。
- 状态：pending validation。

## 149. device SDK pagination / tab behavior

- 输入：设备平台 Tab / 分页。
- 场景：切换只读 Tab 或分页。
- 预期：遵守 v2.4.9 SPA route guardrail，确认 current_url、source、target tab、click scope。
- 状态：pending validation。

## 150. device SDK readonly safety

- 输入：任意设备平台只读查询。
- 场景：执行页面观察。
- 预期：不点击写操作，不修改设备状态，不导出，不复制完整 JSON，不输出 token / session / ticket / authorization / cookie 明文。
- 状态：pending validation。

## 151. frontend activity profile KUAISHOU userId active

- 输入：`appName=KUAISHOU`、`filtersType=userId`。
- 场景：用户属性及时长区域显示明显使用时长。
- 预期：判断存在前端活跃信号；不得解释为真人 / 本人 / 具体业务动作。
- 状态：validated by internal Agent，v2.5.3 单点 observation 和 v2.5.4 matrix 均已验证。

## 152. frontend activity profile NEBULA userId weak

- 输入：`appName=NEBULA`、`filtersType=userId`。
- 场景：使用时长为空或活跃天数弱。
- 预期：判断前端活跃信号弱或无；不得解释为用户无行为或无风险。
- 状态：validated by internal Agent，v2.5.4 matrix 已验证。

## 153. frontend activity profile deviceId active trend

- 输入：`filtersType=deviceId`。
- 场景：设备维度存在使用时长趋势。
- 预期：说明设备存在前端活跃信号；不得直接归因到具体用户操作。
- 状态：validated by internal Agent，v2.5.4 matrix 已验证 KUAISHOU / NEBULA + deviceId 可查询。

## 154. frontend activity profile empty but backend action exists

- 输入：后端有业务动作，前端活跃画像为空。
- 场景：前后端信号不一致。
- 预期：需要查行为序列、后端日志、登录日志、设备 SDK；不得直接说用户无前端行为。
- 状态：pending browser validation。

## 155. frontend activity strong but device login abnormal

- 输入：前端活跃强，登录日志 / 设备 SDK 异常。
- 场景：活跃信号与风险信号冲突。
- 预期：不能直接判定正常真人；需继续补登录链路和设备风险。
- 状态：pending browser validation。

## 156. frontend activity profile user appeal boundary

- 输入：用户申诉未操作，但前端活跃画像存在。
- 场景：客服 / 风控解释。
- 预期：只能作为中弱证据；仍需查具体行为序列、登录日志、设备一致性和后端动作。
- 状态：pending browser validation。

## 157. frontend activity profile direct open preflight

- 输入：已知直联 URL。
- 场景：内部 Agent 打开埋点分析 / 用户洞查 / 用户细查详情页面。
- 预期：URL 无跳转、登录态复用成功、无权限阻断、页面标题为“埋点分析”、目标页面和“用户属性及时长”区域可见。
- 状态：validated by internal Agent，Run 001 已记录。

## 158. frontend activity profile target area extraction

- 输入：v2.5.3 已通过 preflight 的页面。
- 场景：内部 Agent 读取“用户属性及时长”区域。
- 预期：输出 `frontend_activity_profile_observation`，包含 profile_card、usage_duration、activity_judgement。
- 状态：validated by internal Agent，v2.5.3 单点 observation 已生成。

## 159. frontend activity profile behavior records untouched

- 输入：同一页面下方行为记录区域。
- 场景：页面显示“行为回放”、“行为序列”、“行为统计”标签。
- 预期：只记录这些标签存在，不点击、不读取、不解析下方行为记录。
- 状态：validated by internal Agent as boundary：v2.5.3 / v2.5.4 均未读取下方行为记录。

## 160. frontend activity profile four-combination matrix

- 输入：KUAISHOU / NEBULA × userId / deviceId。
- 场景：四组合矩阵验证。
- 预期：四组均可直联打开，复用登录态，无权限阻断，目标区域可见。
- 状态：validated by internal Agent，v2.5.4 matrix 已验证，4/4 success。

## 161. frontend activity profile evidence boundary

- 输入：任意前端活跃画像 observation。
- 场景：Dennis 消化前端活跃证据。
- 预期：只能作为前端活跃存在性证据；不得单独证明真人、本人、具体业务动作或设备稳定绑定关系。
- 状态：validated by documentation guardrail。

## 162. frontend activity profile extraction mode correction

- 输入：v2.5.3 / v2.5.4 已归档 observation。
- 场景：校准字段来源。
- 预期：profile card 初始来源标记为 `screenshot_manual_read`；后续标记 `dom_text_read_verified=true`；DOM 路径为 `iframe[1].contentDocument → .user-card → innerText`。
- 状态：validated by internal Agent follow-up confirmation。

## 163. frontend activity profile DOM text read for profile card

- 输入：用户细查详情页面。
- 场景：读取 profile card 静态文本。
- 预期：可通过 iframe 内 `.user-card → innerText` 提取 user_id、register_time、fan_distribution、active_days_bucket、年龄、地域等字段。
- 状态：validated by internal Agent follow-up confirmation。

## 164. frontend activity profile canvas usage duration limitation

- 输入：使用时长图表。
- 场景：尝试从 DOM 获取使用时长数值。
- 预期：DOM 可确认 `chart_present=true` / `canvas_rendered`，但不能直接提取柱状图具体数值、峰值和每日点位。
- 状态：validated as limitation。

## 165. frontend activity profile usage duration precise value pending

- 输入：使用时长图表。
- 场景：需要精确峰值和每日使用时长。
- 预期：后续探索 tooltip / 图表数据接口 / network API；不得长期把截图视觉估算写成 DOM 精确读取。
- 状态：pending validation。

## 166. tianshi strategy hit query success

- 输入：`sourceId` + 时间窗口。
- 场景：天狮策略平台 / rcp `fastQueryHbase` 只读查询。
- 预期：`status=200` 且 `message=成功` 时输出 `query_status=success`。
- 状态：validated by internal Agent，v2.5.5 Run 001 已验证。

## 167. tianshi strategy production policy hit

- 输入：天狮 `data` 数组。
- 场景：判断生产策略命中。
- 预期：任一 `data[*].hitProductionPolicy=true` 时输出 `has_strategy_hit=true`；`production_policy_hit_count` 统计命中生产策略的记录数。
- 状态：validated by internal Agent，v2.5.5 Run 001 已验证，样例为 4/4 命中。

## 168. tianshi strategy distribution summary

- 输入：天狮命中记录。
- 场景：汇总策略返回动作和风险类型。
- 预期：对 `riskDecision`、`eventType`、`riskType` 做分布统计；`sample_hits` 最多保留 3 条。
- 状态：validated by internal Agent，v2.5.5 Run 001 已验证。

## 169. tianshi trace value not persisted

- 输入：天狮响应中的 host / port / traceId。
- 场景：标准 observation 沉淀。
- 预期：不记录 host、port、traceId 原值；如需表达链路可用性，仅记录 `has_trace=true/false`。
- 状态：validated by documentation guardrail。

## 170. tianshi strategy hit is not final risk classification

- 输入：天狮策略命中 observation。
- 场景：Dennis 消化策略证据。
- 预期：明确天狮命中是策略证据，不等于最终作弊定性；`riskDecision=阻止/验证` 代表策略返回动作，不代表最终执行成功；无命中不代表无风险。
- 状态：validated by documentation guardrail。

## 171. tianshi strategy hit routing plan

- 输入：“帮我看下 4231737183 今天有没有被风控策略命中过”。
- 场景：用户明确询问单个 sourceId 是否命中风控 / 反作弊策略。
- 预期：
  - Dennis 识别 `intent=strategy_hit_check`。
  - 生成 `tianshi_strategy_hit_check` 查询计划。
  - 查询计划包含 `source_id=4231737183`、`time_window`、固定 `eventTypeCodes=BS/ANTICRAWL/ACTIVITY_ANTISPAM/ACCOUNT/FLOW_ANTISPAM`。
  - 输出不得直接判定用户作弊。
  - 输出必须包含“策略命中是证据，不等于最终风险定性；无命中不代表无风险”的边界说明。
- 状态：routing smoke test added，pending live regression。

## 172. multi evidence orchestration risk assessment

- 输入：“帮我看下 4231737183 今天是不是风险用户”。
- 场景：用户要求综合风险判断，而不是只问是否命中策略。
- 预期：
  - Dennis 不只调用天狮后直接定性。
  - 生成 `multi_evidence_query_plan`。
  - 查询计划包含五类 evidence：`strategy_evidence`、`login_evidence`、`profile_evidence`、`behavior_evidence`、`device_evidence`。
  - 天狮用于 strategy evidence；统一登录日志用于 login evidence；档案中心用于 profile evidence；前端活跃画像用于 behavior evidence；设备 SDK 用于 device evidence。
  - 明确 DataAgent / Hive 只在需要离线聚合统计、历史基线或批量样本时触发。
  - 最终输出包含 `supporting_evidence`、`counter_evidence`、`missing_evidence`。
  - 不输出“用户一定作弊”等绝对定性。
- 状态：orchestration smoke test added，pending live regression。

## 173. e2e multi evidence readonly minimum loop

- 输入：“帮我看下 4231737183 今天是不是风险用户，为什么被阻止/验证？”
- 场景：真实 E2E 多手脚只读验证模板。
- 期望：
  - 生成 `multi_evidence_query_plan`。
  - 包含 `tianshi_strategy_hit_check`。
  - 包含 `unified_login_log_check`。
  - 包含 `archives_center_profile_check`。
  - 不强制包含 `frontend_activity_profile_check` / `device_sdk_foundation_check`。
  - 不默认触发 DataAgent / Hive。
  - 输出不能只根据天狮命中直接判定用户作弊。
  - 输出必须包含 `supporting_evidence` / `counter_evidence` / `missing_evidence` / `boundary_notes`。
  - `failed / permission_blocked / no_data` 必须进入 `missing_evidence` 或 `blockers`。
- 状态：E2E template smoke test added，pending real run。

## 174. archives independent login recoverable preflight

- 输入：档案中心 direct URL 跳转到 `account.p.adm-corp.kuaishou.com` 独立登录页。
- 场景：账号 / 用户名输入框已预填。
- 预期：
  - 不要立即判定 `archives_center_profile_check failed`。
  - 应点击“下一步”尝试恢复会话。
  - 若进入档案中心，则 `query_status=success`。
  - 记录 `recoverable_preflight_success=true`。
  - 不得把预填账号样例写成固定判断条件。
- 状态：validated by cloud internal Agent，v2.5.8.1 Run 002 已验证。

## 175. archives independent login still requires MFA

- 输入：档案中心独立登录页点击“下一步”后仍要求密码 / 扫码 / MFA。
- 场景：preflight 不可恢复。
- 预期：
  - `query_status=blocked_by_independent_login`。
  - `blocker_type=archives_independent_login_required`。
  - 进入 `blockers` / `missing_evidence`。
  - 不得解释为用户无记录、档案无数据、用户无风险。
- 状态：guardrail added，pending regression。

## 176. archives independent login username not prefilled

- 输入：档案中心独立登录页账号 / 用户名未预填。
- 场景：无法确认操作者身份或恢复会话。
- 预期：
  - 不猜测账号。
  - 不输入固定用户名。
  - `query_status=blocked_by_independent_login` 或 `wait_for_manual_login`。
  - 禁止解释为平台查询成功但无风险。
- 状态：guardrail added，pending regression。

## 177. e2e cloud three source success digest

- 输入：“帮我看下 4231737183 今天是不是风险用户，为什么被阻止/验证？”
- 场景：云端内部 Agent 三源 E2E 成功运行。
- 预期：
  - completed_sources 包含 `tianshi_strategy_hit_check`、`unified_login_log_check`、`archives_center_profile_check`。
  - failed_sources 为空。
  - 档案中心 recoverable preflight 成功时，profile evidence `query_status=success`。
  - 历史封禁原因与今日登录 / 注册策略命中不得强行合并成同一因果链。
  - 登录成功 + token 下发只能作为 counter / nuance evidence，不解释为无风险。
  - 不输出“用户一定作弊”等绝对结论。
- 状态：validated by cloud internal Agent，v2.5.8.1 Run 002 已验证。

## 178. user login log API GET-only accessible

- 输入：`GET /rest/unified/log/search`。
- 场景：内部 Agent 直接访问统一登录日志核心查询接口。
- 预期：`status_code=200`，body `code=0`，无登录跳转，无 auth blocked。
- 状态：validated，v2.4.10 Run 001 已验证。

## 179. user login log API standard userId exact query mode

- 输入：用户维度查询 `4700398885`。
- 场景：构造 API query。
- 预期：标准查询必须使用 `userId=4700398885&did=&query=`；不得使用 `query=4700398885&userId=` 作为 Dennis 标准用户链路查询方式。
- 状态：validated by documentation guardrail，v2.4.10 已固化。

## 180. user login log API keyword fallback mode

- 输入：keyword 查询。
- 场景：用户明确要求通用关键词搜索，或无法归入 userId / did 精确查询。
- 预期：可使用 `query={keyword}&userId=&did=`；该模式是 fallback，不替代 userId exact query。
- 状态：validated by documentation guardrail。

## 181. user login log API full result loaded

- 输入：API response。
- 场景：`totalCount=141` 且 `logSearchModels.length=141`。
- 预期：标记 `api_full_result_loaded=true`，记录 `length_equals_totalCount=true` 和 index continuity。
- 状态：validated，v2.4.10 Run 001 已验证。

## 182. user login log UI frontend pagination discovery

- 输入：UI 翻页行为与 API 请求观察。
- 场景：UI 翻页没有触发新的 search 请求。
- 预期：标记 `pagination_mode=frontend_pagination`、`ui_frontend_pagination=true`；API hand 可作为结构化读取优先方式。
- 状态：validated，v2.4.10 Run 001 已验证。

## 183. user login log API credential raw value not output

- 输入：API response / logContent。
- 场景：parse `logContent`。
- 预期：不输出完整 response，不输出完整 `logContent`；token / loginToken / tokenId / accessToken / refreshToken / session / ticket / authorization / cookie / rawAuthHeader 只输出 `present_redacted`。
- 状态：validated by documentation guardrail。

## 184. user login log API no result behavior

- 输入：API 返回空结果。
- 场景：目标查询条件下无 logSearchModels。
- 预期：不得解释为无风险或用户无登录记录；只能说明当前查询条件和可靠窗口内 API 未返回记录。
- 状态：pending validation。

## 185. user login log API unauthorized / expired auth behavior

- 输入：API 401 / 403 / redirect。
- 场景：认证态失效或权限不足。
- 预期：返回 auth / permission blocker；不得解释为无数据。
- 状态：pending validation。

## 186. user login log API over reliable window behavior

- 输入：超过 reliable window 的 API 查询。
- 场景：长周期查询。
- 预期：不得解释为历史无记录；需要进入 limitations，并建议 DataAgent / Hive 或离线日志。
- 状态：pending validation。

## 187. user login log API logContent parse normalization

- 输入：API `logContent` JSON string。
- 场景：parse key 和允许保留的非凭证明文 value。
- 预期：保留 userId / deviceId / did / IP / UA / appVer / sysVer / uri / method / result / reason / timestamp / loginType 等风控字段；凭证明文 present_redacted。
- 状态：pending validation。

## 188. tianshi eventList USER_REGISTER_NEW API-read

- 输入：“用天狮 eventList API-read 查 2740906395 今天 13:06-14:06 的 USER_REGISTER_NEW 事件”。
- 场景：用户明确要求细查某个 sourceId、小时间窗口、单个注册 eventType 明细。
- 预期：
  - 生成 `eventlist_api_read` 查询计划。
  - 使用 `POST /v2/rest/event/eventList`。
  - `sourceIds` 必须填入 `2740906395`，不得为空。
  - `eventType=USER_REGISTER_NEW`。
  - `startTime/endTime` 为同一天 Asia/Shanghai 字符串。
  - 不记录 cookie / token / 完整 header 敏感值。
  - 返回 eventList / pagination / tableHeaderList 后结构化解析。
  - 若接口返回 401 / 403 / 跳登录，标记 auth blocker，不得输出 no_data。
- 状态：validated by internal Agent，v2.5.9 Run 001 已验证。

## 189. tianshi eventList app login sync async query plan

- 输入：“查 2740906395 今天 app 登录同步和异步事件”。
- 场景：账号 app 登录事件级细查。
- 预期：
  - 识别为 app_login 细查。
  - eventType 组合为 `LOGIN_AUDIT` + `ASYNC_LOGIN`。
  - 生成两个 eventList 查询计划或分步查询计划。
  - 查询窗口不跨天。
  - 输出中区分 sync / async。
  - no_data 只能解释为该查询条件下未见记录，不代表用户未登录或无风险。
- 状态：routing smoke test added，pending live regression。

## 190. tianshi eventList long window guardrail

- 输入：“查 2740906395 最近一周 eventList 明细”。
- 场景：用户要求大窗口 eventList 细查。
- 预期：
  - 不直接生成跨天 eventList 查询。
  - 要求缩小时间窗口，或基于已有证据定位小窗口。
  - 如必须查多天，应拆分为按天 / 小窗口分段。
  - 输出说明 eventList 不适合大窗口全量统计；大范围统计、趋势、历史聚合应转 DataAgent / Hive 或离线能力。
- 状态：guardrail added，pending regression。

## 191. tianshi eventList no_data is not no login

- 输入：“eventList 没查到记录，说明用户没登录吧？”
- 场景：用户把 eventList no_data 误解为行为未发生。
- 预期：
  - 明确否定。
  - 说明命中策略事件 100% 记录，但非命中策略事件存在抽样。
  - `eventList no_data` 不代表行为未发生，不代表用户无风险。
  - 如需确认登录链路，应补用户登录统一日志或围绕实际活跃时间缩小窗口再查。
- 状态：guardrail added，pending regression。

## 192. archives user_analysis API direct POST succeeds

- 输入：档案中心用户分析 / APP端核心操作日志。
- 场景：在已登录档案中心 browser session 内通过 same-origin fetch 调用 `/v3/user/log/coreLogs/fetch`。
- 预期：POST 成功，response JSON 返回，`data.totalCount` 和 `data.dataList` 可见。
- 状态：validated by internal Agent，v2.4.7.1 Run 001 已验证。

## 193. archives user_analysis same-origin browser session fetch works

- 输入：已登录档案中心 browser session。
- 场景：API direct POST 认证上下文。
- 预期：`browser_session_used=true`，`same_origin_fetch=true`，不导出 cookie / token / session，不需要额外 CSRF header。
- 状态：validated by internal Agent，v2.4.7.1 Run 001 已验证。

## 194. archives user_analysis pagination pageIndex pageSize validated

- 输入：`pageIndex=1/2`、`pageSize=30`。
- 场景：验证 API 分页机制。
- 预期：pageIndex=1 返回 5 条，pageIndex=2 返回 0 条，totalCount 仍为 5，`has_more=false`。
- 状态：validated by internal Agent，v2.4.7.1 Run 001 已验证。

## 195. archives user_analysis response shape detected

- 输入：API response。
- 场景：字段结构识别。
- 预期：top-level fields、`data.totalCount`、`data.dataList`、record fields 可识别；record fields 与 DOM 表格列一致。
- 状态：validated by internal Agent，v2.4.7.1 Run 001 已验证。

## 196. archives user_analysis risk_event_scan from API response

- 输入：`data.dataList`。
- 场景：focused_login_risk。
- 预期：可直接从 API response 生成 `risk_event_scan`，不依赖 DOM row feature filter。
- 状态：validated by internal Agent，v2.4.7.1 Run 001 已验证。

## 197. archives user_analysis sensitive requestParam extraParam not output

- 输入：record 中的 `requestParam` / `extraParam`。
- 场景：敏感字段输出边界。
- 预期：不输出完整 `requestParam` / `extraParam`；不输出 token / tokenId / refresh_token / sig / open_id 明文；只沉淀字段名、字段存在性、计数、分布和派生特征。
- 状态：validated by documentation guardrail，v2.4.7.1 已固化。

## 198. archives user_analysis DOM extraction fallback remains available

- 输入：API direct POST 失败或 response shape 变化。
- 场景：fallback。
- 预期：回退 DOM scoped JS eval / row feature filter；不得因 API 失败直接解释为用户无数据或无风险。
- 状态：guardrail added，pending regression。
