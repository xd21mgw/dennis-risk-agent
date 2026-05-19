# ATO-S2-004 End-to-End Usage Walkthrough

## 1. 用户自然语言问题

“这个用户说 5 月 4 日在成都扫码后账号异常，后续被封，帮我判断是不是盗号，并告诉我还要不要继续查。”

## 2. Agent 识别结果

```yaml
intent: single_case_judgement
workflow: single_case_judgement -> dataagent_question_generation -> dataagent_result_interpretation
dataagent_needed: true
capabilities:
  - account_security_expert_skill
  - ATO evidence boundary
  - ATO query template
  - Data Agent result parser
  - governance_design
```

说明：
- 这是典型的单 case 研判问题，但已经带有“要不要继续查”的交互式下一步需求。
- 先走 ATO 单 case 判断，再生成 Data Agent 只读取证问题。
- Data Agent 返回后进入 result interpretation，再决定是否需要继续查询。

## 3. Data Agent 只读取证问题摘要

```text
请基于数据平台可查询的数据，对以下疑似 Web 扫码登录类 ATO case 做只读取证分析。

case_id:
ATO-S2-004

实体标识：
user_id = 615438489

时间窗口：
优先 2026-05-04，扩展至 2026-05-03 ~ 2026-05-05

数据域：
登录 / 授权链路、设备 / IP / 地区、账号安全事件、风控策略命中、下游风险事件。

输出要求：
只输出数据发现、覆盖范围、缺失证据、权限限制、口径风险和数据侧提示。
不要输出最终风控定性、处罚、冻结、封禁、扣除或策略上线建议。
```

边界说明：
- Data Agent 只做只读取证。
- 不要求 Data Agent 判断是否最终盗号。
- 不要求 Data Agent 输出最终结论等级。
- 不要求 Data Agent 决定下一步 provider。

## 4. Data Agent 阶段性返回摘要

```yaml
dataagent_stage_result:
  completed_sql:
    - 76439: 登录全景
    - 76442: 设备 IP 汇总
    - 76446: 安全事件
  running_sql:
    - 76451: 发布作品
  covered_data_domains:
    - 登录/授权链路
    - 设备/IP/地区
    - 风控策略命中
    - 账号安全事件
    - 社交封禁
  pending_evidence:
    - 发布作品
    - 作品内容是否违规
    - 精确发布时间
    - token/session 专用表
    - 二维码详情
    - 实时日志
```

阶段性返回的核心发现：
- 9 秒内完成完整扫码 / OAuth 链路。
- Web 新设备、无历史环境、新 IP、新 UA、新地区同时出现。
- 账号接管相关策略命中。
- 社交封禁 IP 与 Web 扫码 IP 完全一致。
- 发布作品 SQL 仍 running，不能假装已完成。

## 5. Parser / Evidence 结构化

```yaml
parser_evidence:
  data_findings:
    - 9 秒内完成 iOS 扫码 / OAuth -> Web 新设备 OAuth 成功链路。
    - Web 新设备首次出现，活跃天数为 0。
    - 新 IP、新 UA、新地区与无历史环境同时出现。
    - 多条账号接管 / Web 扫码 / 地区不匹配 / 无历史环境相关策略命中。
    - 社交封禁 IP 与 Web 扫码 IP 一致。
  provider_conclusion_hint: "数据强支持 Web 扫码登录异常 + 后续同 IP 社交封禁。"
  strong_evidence:
    - 完整扫码 / OAuth 链路闭合。
    - Web 新设备 / 新 IP / 新 UA / 新地区 / 无历史环境。
    - 账号接管风险策略命中。
    - 社交封禁 IP 与 Web 扫码 IP 一致。
  medium_evidence:
    - iOS 与 Web 设备同一秒多端登录成功。
    - 用户反馈成都扫码与 iOS 历史设备地区一致。
  counter_evidence:
    - iOS 历史设备同一时间也登录成功，可能是用户本人在线。
    - 无 token 被踢 / 复用 / 切换记录。
    - 无换绑 / 改密 / 找回记录。
    - 发布作品仍 pending，不能用来确认或排除 ATO。
  pending_evidence:
    - SQL 76451 发布作品仍 running。
  quality_risks:
    - IP 地区解析可能有偏差。
    - 仅 3 天窗口，长期行为不可见。
    - 离线表存在 T+1 延迟可能。
```

说明：
- Data Agent 的结论性文字只进入 `provider_conclusion_hint`。
- `76451` 仍 running，必须进入 `pending_evidence`。
- 具体策略名只作为 raw_observation，不沉淀为长期本质规则。

## 6. Dennis Interim Judgement

```yaml
dennis_interim_judgement:
  conclusion_level: 高度疑似 Web 扫码登录类 ATO，接近确认
  reason: >
    9 秒内扫码 / OAuth 链路闭合，Web 新设备、新 IP、新 UA、新地区和无历史环境同时出现，
    且账号接管风险策略命中、社交封禁 IP 与 Web 扫码 IP 一致。
  limitation:
    - 发布作品 SQL 76451 仍 running。
    - 发布异常内容子路径尚未验证。
    - token/session 细节和二维码来源缺失。
    - IP 地区解析存在口径风险。
  finality: interim
```

可直接给用户的阶段性判断：
- 当前已经可以把该 case 作为 Web 扫码登录类 ATO 高置信正例候选。
- 但仍要等待发布作品 SQL 76451 返回，补充下游作恶方式分层。
- 当前不是最终完整定性，但已经足够做阶段性研判和样本沉淀。

## 7. 给用户的下一步选项

A. 等待 SQL 76451 发布作品结果。
B. 先基于当前证据输出阶段性判断。
C. 停止新增查询，沉淀为 Web 扫码登录类 ATO 高置信正例候选。
D. 后续换查私信 / 点赞 / 关注 / 接口访问等非发布下游行为。

## 8. 推荐动作

推荐先做阶段性判断，不建议立即扩窗或新增大范围查询。

原因：
- 登录 / 授权 / 设备 / IP / 策略链路已经闭合，足以支持 ATO 发生方式的阶段性判断。
- 76451 发布作品仍 running，只影响下游作恶分层，不影响当前 ATO 发生方式主判断。
- 继续扩窗或大范围查询的边际收益较低，先把已有证据解释清楚更划算。

## 9. 防过拟合检查

- 具体策略名只作为 raw_observation。
- 单个 IP 只作为本 case 证据。
- 9 秒链路不是长期固定阈值。
- 发布行为不是 ATO 必要条件。
- 无发布不能反向排除 ATO。
- 社交封禁同 IP 是强 case 证据，但长期应抽象为“下游风险事件与异常登录环境一致”。

## 10. 输出总结

### 这个闭环证明了什么

1. 内部盗号同学可以通过自然语言提出 ATO 问题。
2. Agent 可以将问题路由到 `single_case_judgement` 和 `dataagent_question_generation`。
3. Data Agent 可以只读取证并返回阶段性数据发现。
4. parser 可以把阶段性返回映射成结构化 evidence。
5. Dennis 主 Agent 可以基于已完成结果给出 `interim` 级判断。
6. 用户可以在“等待 / 先判 / 停查 / 换查”之间做下一步选择。

### 还缺什么

1. SQL 76451 发布作品仍 running。
2. 发布内容、caption、精确发布时间未返回。
3. token/session 专用表和二维码详情缺失。
4. 需要最终确认发布行为子路径，但不影响当前 ATO 发生方式主判断。

### 是否需要修改 ATO entrypoint / workflow / response contract

不需要。

现有的 `scenario_workflow_contract_v1`、`scenario_response_contract_v1`、`ato_account_takeover_workflows_v1` 和 `ato_agent_response_contract_v1` 已经能承载这条闭环。

### 是否修改核心 Skill

未修改核心 Skill。

