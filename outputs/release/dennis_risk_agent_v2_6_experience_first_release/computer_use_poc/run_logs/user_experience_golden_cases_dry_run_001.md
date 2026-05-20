# User Experience Golden Cases Dry Run 001

```yaml
run_id: user_experience_golden_cases_dry_run_001
test_type: user_experience_golden_cases_dry_run
source_docs:
  - computer_use_poc/user_experience_golden_cases.md
  - computer_use_poc/answer_experience_templates.md
  - computer_use_poc/scene_to_capability_routing.md
  - computer_use_poc/smoke_tests.md
real_platform_called: false
new_platform_hand_added: false
platform_read_logic_modified: false
release_package_updated: false
total_cases: 6
passed_cases: 6
failed_cases: 0
overall_result: passed
```

## 验收口径

本轮只做离线体验干跑，不调用真实平台。重点检查：

- 是否像风控专家在判断，而不是平台导航。
- 是否先给结论，再给证据和不确定性。
- 是否避免过度查数、过度调用平台。
- 是否明确下一步动作。
- 是否存在“看起来正确但用户体感一般”的回答。

## Case 1: ATO 用户研判

```yaml
user_query: 帮我看这个用户是不是被盗号
recognized_scene:
  domain: 账号安全
  scenario: ATO / 异常登录 / 账号接管风险研判
selected_capabilities:
  - unified_login_log_check
  - archives_center_profile_check
  - device_sdk_check_if_device_id_available
  - tianshi_strategy_hit_check_if_strategy_hit_question_relevant
forbidden_capabilities_checked:
  - 不默认批量 DataAgent / Hive
  - 不默认全量翻页抓取
  - 不自动处罚 / 冻结 / 踢 token
  - 不把单一登录失败直接定性为盗号
answer_template_used: 风险研判类回答模板
result: pass
failure_reason: null
experience_issue: 无明显体验问题
```

simulated_final_answer:

```text
一句话判断：
当前更适合先看作 ATO 风险研判，而不是直接判断“已被盗号”。我会优先看登录链路、账号画像和可用的设备证据，判断是否存在异地、异设备、失败集中、token/登录态异常和后续行为突变。

关键证据：
1. 支持风险的证据：优先看统一登录日志里是否存在短时间集中失败、异地/异设备登录、异常登录成功后的 token 下发或刷新；再看档案中心是否有账号状态、处罚、历史风险背景；如果能拿到 deviceId，再补 Device SDK 看 hook/frida/root/代理/重打包等设备环境证据。
2. 反证 / 降级因素：同地区、同设备、稳定登录方式、用户近期前端活跃正常，都只能降低风险，不等于直接排除盗号。
3. 缺失证据：如果只有一次登录失败或单源策略命中，还缺设备画像和登录成功后的行为链路。

本质判断：
正常用户换机、输错密码、三方登录授权也会出现失败或设备变化；黑灰产更典型的是失败集中、环境异常、登录态变化和后续行为突变同时出现。最小区分点是：异常登录设备是否具备高风险环境证据，以及登录成功后是否出现非本人行为。

下一步建议：
先查统一登录日志；如出现异常成功登录或异设备，再补 Device SDK；如出现策略命中，再解释策略动作和请求级细节。
```

验收说明：

- 先给风险判断边界，再组织证据。
- 没有平台导航式回答。
- 没有过度触发 DataAgent / Hive。

## Case 2: 登录失败 / 被验证原因

```yaml
user_query: 这个用户为什么登录失败 / 被验证
recognized_scene:
  domain: 账号安全
  scenario: 登录链路原因解释
selected_capabilities:
  - unified_login_log_check
  - tianshi_strategy_hit_check_if_question_mentions_strategy_or_block_verify
  - tianshi_eventlist_api_read_if_specific_event_time_and_event_type_available
  - archives_center_profile_check_as_context
forbidden_capabilities_checked:
  - 不优先 Device SDK
  - 不默认 frontend activity
  - 不把 riskDecision 当最终执行结果
  - 不把 no_data 解释为无风险
answer_template_used: 原因解释类回答模板
result: pass
failure_reason: null
experience_issue: 无明显体验问题
```

simulated_final_answer:

```text
直接原因：
这是登录链路原因解释问题，优先看统一登录日志里的失败原因、登录方式、验证动作和时间窗口。如果问题里提到“被验证/被阻止”，再补天狮策略命中看是否有生产策略返回验证或阻止。

证据链：
1. 时间：先定位失败/验证发生在哪个时间段。
2. 触发动作：看是密码错误、三方登录失败、token 下发异常、刷新 token、退出登录，还是高危接口验证。
3. 策略 / 日志返回：如果天狮返回“阻止/验证”，它表示策略返回动作，不代表最终处置一定成功。
4. 账号 / 设备背景：档案中心只作为上下文，说明账号是否已有封禁、历史风险或异常状态。

它说明什么：
可以说明当前登录请求在哪个环节被失败或被策略要求验证。

它不说明什么：
不能单靠“登录失败”或“被验证”判断用户一定作弊，也不能把无结果解释成无风险。

下一步：
如果要解释到具体请求字段，围绕对应时间点查 eventList；如果怀疑设备环境触发，再补 Device SDK。
```

验收说明：

- 回答围绕“原因”，不是平台清单。
- 明确 riskDecision 边界。
- 没有默认拉设备或前端活跃。

## Case 3: 设备风险补证

```yaml
user_query: 这个设备是不是群控 / root / hook / frida
recognized_scene:
  domain: 设备基建 / 账号安全补证
  scenario: 设备环境风险补证
selected_capabilities:
  - device_sdk_api_direct_readonly
forbidden_capabilities_checked:
  - 不默认统一登录日志
  - 不默认档案中心
  - 不调用 location
  - 不把设备风险单独作为最终风险定性
answer_template_used: 风险研判类回答模板
result: pass
failure_reason: null
experience_issue: 轻微：若用户没有提供 deviceId，应先提示缺少必要实体或进入 user_to_device，而不是直接查设备。
```

simulated_final_answer:

```text
一句话判断：
这是设备侧风险补证问题。即使查到 root/hook/frida，也只能说明设备环境存在风险线索，不能单独定性用户作弊。

关键证据：
1. 支持风险的证据：Device SDK 中明确的 root/jailbreak、hook、frida、模拟器、双开、proxy、repack、强风险标签，是设备侧强证据。
2. 中弱证据：SDK 采集异常、低启动、appList 异常、klink 或 graph 关系异常，可以作为补充线索。
3. 缺失证据：还需要登录链路、账号画像或策略命中判断该设备环境是否参与了具体风险行为。

本质判断：
正常设备也可能有少量环境异常或字段缺失；群控/改机更关键的是自动化环境、hook/frida/代理/重打包和多账号行为链同时出现。最小区分点是设备环境异常是否能和登录、账号、策略命中形成同一链路。

下一步建议：
先查 Device SDK 的风险字段；如有异常，再补该设备关联用户和登录链路。
```

验收说明：

- 不调用 location。
- 没有把设备异常直接升级为最终定性。
- 体验问题可接受：模板需在实际回答中根据是否有 deviceId 加一句实体缺失处理。

## Case 4: 用户关联设备查询

```yaml
user_query: 这个用户最近关联了哪些设备
recognized_scene:
  domain: 实体解析 / 设备关联
  scenario: userId -> deviceId 实体解析
selected_capabilities:
  - user_to_device_entity_resolution
  - weapon_graphData
  - archives_user_analysis_recent_devices_as_supplemental_ranking
forbidden_capabilities_checked:
  - 不直接拿 userId 调 Device SDK riskData
  - 不默认批量深查所有设备风险
  - 不把关联设备数直接解释为群控
answer_template_used: 实体关系查询类回答模板
result: pass
failure_reason: null
experience_issue: 无明显体验问题
```

simulated_final_answer:

```text
查询意图：
这是用户转设备的实体关系查询，目标是先确认这个 userId 关联了哪些候选 deviceId，再决定是否需要进入设备风险补证。

关系摘要：
我会优先用 Weapon graphData 做 user_to_device，方向是 groupKey=USER_ID、dimKey=DEVICE_ID；返回后只整理候选设备、直连关系、relationDetail、weight 和排序理由。

怎么理解：
关联设备只是候选实体关系，不是风险结论。多设备可能来自换机、登录历史、共享设备或测试设备，不能直接解释为群控。

下一步：
如果候选设备较少，优先选最近登录、近期活跃或 relationDetail 风险提示更强的设备进入 Device SDK；如果候选过多，只返回 top candidates，并要求缩小时间范围或指定设备。
```

验收说明：

- 清楚体现 entity resolution 在 Device SDK 前。
- 没有默认批量深查。

## Case 5: 设备关联用户查询

```yaml
user_query: 这个设备关联了哪些用户
recognized_scene:
  domain: 实体解析 / 设备关联账号
  scenario: deviceId -> userId 实体解析
selected_capabilities:
  - device_to_user_entity_resolution
  - weapon_graphData
forbidden_capabilities_checked:
  - 不直接定性团伙作弊
  - 不默认拉所有关联用户的深度画像
  - 不默认 DataAgent / Hive
answer_template_used: 实体关系查询类回答模板
result: pass
failure_reason: null
experience_issue: 无明显体验问题
```

simulated_final_answer:

```text
查询意图：
这是设备转用户的实体关系查询，目标是确认这个 deviceId 直接关联了哪些用户，以及是否存在封禁或状态异常摘要。

关系摘要：
我会走 Weapon graphData 的 device_to_user，方向是 groupKey=DEVICE_ID、dimKey=USER_ID。输出会重点看 related_user_ids 数量、直连边、封禁用户数、状态异常数和 relationDetail 摘要。

怎么理解：
设备关联多个用户只能说明存在关系线索，不等于团伙作弊。正常共享设备、换机、家庭设备或测试设备也可能形成多账号关联。

下一步：
如果出现关联封禁或状态异常用户，再选 top 用户补档案中心、统一登录日志和策略命中；不默认把所有关联用户都深查一遍。
```

验收说明：

- 像风控专家在解释关系证据，而不是只说接口。
- 没有把多账号关系直接定性。

## Case 6: 策略命中解释

```yaml
user_query: 这个策略命中到底说明什么
recognized_scene:
  domain: 策略证据解释 / 风控命中
  scenario: 策略命中证据解释
selected_capabilities:
  - tianshi_strategy_hit_check
  - tianshi_eventlist_api_read_if_specific_request_detail_needed
  - unified_login_log_check_if_login_or_verify_chain_needed
  - archives_center_profile_check_if_account_context_needed
forbidden_capabilities_checked:
  - 不把 riskDecision=阻止/验证解释为最终处罚成功
  - 不把命中策略等同用户一定作弊
  - 不把无命中解释为无风险
answer_template_used: 原因解释类回答模板
result: pass
failure_reason: null
experience_issue: 无明显体验问题
```

simulated_final_answer:

```text
直接解释：
策略命中说明生产风控策略在该时间窗口内对某类请求给出了风险动作或风险判断，它是策略证据，不是最终作弊定性。

它说明什么：
如果 riskDecision 是“阻止/验证”，说明策略返回的动作倾向是阻止或要求验证；如果命中次数、eventType、riskType 和时间窗口与登录/注册请求对齐，证据强度会提升。

它不说明什么：
它不等于最终处置一定执行成功，也不等于用户一定作弊。无命中也不能说明无风险，只能说明当前查询窗口和策略范围内未见命中。

下一步：
如果要解释某次请求为什么被打到，补 eventList 看 eventType、error_code、实时反馈和字段摘要；如果要看是否影响登录链路，补统一登录日志；如果要看账号背景，补档案中心。
```

验收说明：

- 先解释证据含义，再讲边界。
- 没有把策略动作写成最终处置。

## 汇总

```yaml
case_results:
  - case: ATO 用户研判
    result: pass
  - case: 登录失败 / 被验证原因
    result: pass
  - case: 设备风险补证
    result: pass
  - case: 用户关联设备查询
    result: pass
  - case: 设备关联用户查询
    result: pass
  - case: 策略命中解释
    result: pass
main_experience_findings:
  - 6 个回答都能先给判断或解释，再组织证据和边界。
  - 没有出现平台导航式回答。
  - 没有过度查数或默认批量调用。
  - 下一步动作均明确。
  - 设备风险补证 case 需要在真实回答中根据输入实体是否存在 deviceId，补一句 missing_device_id / user_to_device 处理。
recommended_fix:
  - 在实际主 Agent 输出中，如果设备风险问题未携带 deviceId，应优先提示缺少 deviceId 或进入 user_to_device entity resolution。
```
