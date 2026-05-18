# ATO-S2-004 Real Case Interim Parse

## 一、Case 摘要

| 字段 | 内容 |
|---|---|
| case_id | ATO-S2-004 |
| user_id | 615438489 |
| 时间窗口 | 优先 2026-05-04，扩展至 2026-05-03 ~ 2026-05-05 |
| 当前 Data Agent 查询状态 | 登录全景、设备 IP 汇总、安全事件已完成；发布作品仍 running |
| 当前是否 final | 否，`interim` |

查询状态：

| SQL ID | 目的 | 状态 | 行数 | 是否进入当前 evidence |
|---|---|---|---:|---|
| 76439 | 登录全景 | success | 6 | 是 |
| 76442 | 设备 IP 汇总 | success | 3 | 是 |
| 76446 | 安全事件 | success | 7 | 是 |
| 76451 | 发布作品 | running | - | 否，进入 `pending_evidence` |

覆盖范围：
- 已覆盖：登录 / 授权链路、设备 / IP / 地区、账号安全风险策略命中、账号安全事件、社交封禁。
- 未完成：发布作品。
- 不支持或无权限：token/session 专用表、二维码详情、实时日志、caption、upload_timestamp、高敏 params。

## 二、Parser 结构化结果

```yaml
parser_result:
  provider_status: partial_completed
  batch_status: polling
  query_execution_summary:
    total_queries_count: 4
    completed_queries_count: 3
    running_queries_count: 1
    failed_queries_count: 0
    repaired_queries_count: 0
    available_partial_results:
      - 登录全景
      - 设备 IP 汇总
      - 账号安全事件
    unavailable_results:
      - 发布作品
    current_progress_summary: "3 组 SQL 已完成，1 组发布作品 SQL 仍 running。"
  available_data_findings:
    - 9 秒内形成 iOS 扫码 / OAuth 授权到 Web 新设备授权成功的链路。
    - Web 新设备、同一新 IP、新 UA、新地区、无历史环境同时出现。
    - iOS 历史设备地区为四川成都，Web 扫码 / 新设备地区为湖北武汉。
    - 出现多条账号接管 / Web 扫码 / 地区不匹配 / 无历史环境 / 二维码环境异常相关策略命中。
    - Web 新设备获得登录态，OAuth 授权成功。
    - iOS 与 Web 设备在 14:27:09 同时登录成功，多端共存。
    - 社交封禁 IP 与 Web 扫码 IP 一致。
  pending_evidence:
    - SQL 76451 发布作品详情仍 running。
    - 发布作品数量、发布时间、设备/IP/地区、内容风险均未完成。
  missing_evidence:
    - 作品内容是否违规不可见。
    - 精确发布时间不可见。
    - 二维码来源、授权应用、权限范围不支持。
    - token/session 生命周期无专用表权限。
    - 被盗前更长历史数据不在当前窗口。
  quality_risks:
    - IP 地区解析可能存在偏差。
    - 扫码地区不匹配策略依赖 IP 解析。
    - 仅覆盖 3 天窗口，长期行为不可见。
    - 离线表可能存在 T+1 延迟。
    - 高敏 params 已移除，策略决策细节不可见。
  provider_conclusion_hint: "Data Agent 阶段性提示：数据强支持 Web 扫码登录异常 + 后续同 IP 社交封禁；发布作品详情待补。"
  interim_judgement_allowed:
    allowed: true
    reason: "登录 / 授权链路、设备/IP、安全事件已完成，足以对 ATO 发生方式做阶段性判断；发布行为仍 pending，只影响下游作恶分层。"
```

## 三、证据分层

### strong_evidence

- 9 秒内形成完整扫码 / OAuth 链路：
  - iOS 历史设备发起 OAuth 授权。
  - Web 端完成扫码。
  - Web 新设备 OAuth 授权成功。
- Web 新设备首次出现，活跃天数为 0，且与新 IP、新 UA、新地区同时出现。
- Web 扫码 / 新设备地区为湖北武汉，而用户反馈和 iOS 历史设备均指向四川成都，形成登录环境突变和地区不匹配。
- 多条账号接管、Web 扫码、异常授权、无历史环境、地区不匹配相关策略命中。
  - 注意：具体策略名只作为 `raw_observation`，长期规则应抽象为“账号接管风险策略命中 / 异常授权风险命中 / Web 扫码风险命中”。
- Web 新设备获得登录态，OAuth 授权成功。
- 社交封禁 IP 与 Web 扫码 IP 完全一致，支持同一异常 Web/IP 环境后续触发下游社交风险。

### medium_evidence

- iOS 与 Web 设备在同一秒多端登录成功，支持多端共存和登录态接管可能性。
- 用户反馈“成都线下扫码”与 iOS 历史设备地区一致，与 Web 端武汉不一致，符合“用户线下授权、远程 Web 接收”的路径解释。
- 凌晨出现社交封禁，时间和行为形态更偏风险场景，但仍需要结合具体封禁原因和上下文解释。

### weak_evidence

- 用户反馈账号异常、疑似扫码后被盗。
- “远程 Web 接管”是基于地区差异、扫码链路和同 IP 下游风险形成的解释，不是单独数据字段。
- “典型深夜作案”属于经验解释，只能作为辅助说明，不能作为强证据。

### counter_evidence

- iOS 历史设备也在 14:27:09 登录成功，可能是用户本人同时在线或正常使用。
- 无 token 被踢 / 复用 / 切换记录。
- 无换绑、改密、找回记录。
- 成都扫码 vs 武汉 Web 登录可能存在 IP 解析偏差或网络代理解释。
- 发布作品仍 pending，不能用发布行为确认 ATO，也不能用未返回发布结果排除 ATO。

### pending_evidence

- SQL 76451 发布作品仍 running。
- 发布行为是否发生、是否异常、是否与 Web 扫码环境一致均待返回。
- 发布作品内容、caption、精确发布时间不可见或无权限。

### unsupported_or_unavailable_evidence

- 二维码来源 / 授权应用 / 权限范围：数据平台不支持。
- token/session 生命周期：无专用表权限。
- 实时扫码流程和实时设备指纹：当前 Data Agent-only 能力不可充分覆盖。
- 高敏 params：已移除。

## 四、Dennis Final Judgement

```yaml
dennis_final_judgement:
  conclusion_level: 高度疑似 Web 扫码登录类 ATO，接近确认
  finality: interim
  reason: >
    9 秒内扫码 / OAuth 链路闭合，Web 新设备、新 IP、新 UA、新地区和无历史环境同时出现，
    多条账号接管 / Web 扫码 / 异常授权相关风险命中，并且后续社交封禁 IP 与 Web 扫码 IP 一致。
    这些证据共同支持 Web 扫码登录类账号接管嫌疑。
  limitation:
    - 发布作品 SQL 76451 仍 running，发布异常内容子路径尚未验证。
    - token/session 细节和二维码来源缺失。
    - IP 地区解析和策略高敏参数存在口径限制。
```

当前可以把该 case 作为 Web 扫码登录类 ATO 高置信正例候选。

但要明确：
- 发布异常内容子路径仍 pending。
- 发布 SQL 返回前，不得把“发布异常内容”作为已验证事实。
- Data Agent 的“数据强支持”只进入 `provider_conclusion_hint`；上面的阶段性判断由 Dennis 主 Agent 基于证据链单独生成。

## 五、是否进入回归 Case

建议进入 ATO 高置信正例回归。

适合标签：

```yaml
regression_candidate:
  include: true
  ato_occurrence_method:
    - Web 扫码
    - 异步登录
    - OAuth 授权类 ATO
  downstream_abuse_method:
    - 社交风险行为已验证
    - 发布行为 pending
  expected_conclusion: 高度疑似 Web 扫码登录类 ATO，接近确认
  finality: interim_until_publish_sql_returns
```

不应沉淀为长期规则：
- 具体策略名。
- 单个 IP。
- 单个时间点。
- 9 秒固定阈值。
- 单 case 的地域组合。

可沉淀为候选机制特征：
- 异常扫码 / OAuth 授权链路闭合。
- Web 新设备 / 无历史环境 / 新 IP / 新 UA / 新地区。
- 账号接管风险策略命中。
- 下游风险事件与异常登录环境一致。

## 六、下一步动作

| 问题 | 判断 |
|---|---|
| 是否必须等待 SQL 76451 | 否。ATO 发生方式主判断已可阶段性成立。 |
| SQL 76451 返回后如何补充 | 补充下游发布行为分层：是否发布、是否与 Web 环境一致、是否内容风险；不改变当前 ATO 发生方式主判断。 |
| 是否需要继续 Data Agent | 仅等待 running SQL 76451；不建议新增扩窗或大范围查询。 |
| 是否需要回写 Skill | 暂不回写，先作为 real case review / eval。 |

建议用户可选动作：

- A. 等待 SQL 76451 完成，补下游发布行为分层。
- B. 先基于已完成结果输出阶段性 case 判断。
- C. 不新增扩窗，不新增大范围查询，避免成本扩大。

推荐动作：B + A。先记录阶段性高置信 ATO 正例候选，同时等待发布 SQL 完成后补全下游作恶标签。

## 七、防过拟合检查

- 具体策略名只作为 `raw_observation`，不得写入长期本质规则。
- `58.48.205.38` 只作为本 case 证据，不作为长期规则。
- 9 秒链路是本 case 事实，不作为固定阈值规则。
- 社交封禁同 IP 是强 case 证据，长期应抽象为“下游风险事件与异常登录环境一致”。
- 发布行为不是 ATO 必要条件。
- 无发布不能反向排除 ATO。
- 用户反馈是线索，不是事实；本 case 结论主要来自登录 / 授权 / 设备 / IP / 策略 / 社交封禁链路。
- Data Agent provider_conclusion_hint 不等于 Dennis final judgement。

## 八、输出总结

1. 新增文件路径：`outputs/reviews/ato_real_case_ATO-S2-004_interim_parse.md`
2. 是否修改核心 Skill：否。
3. 是否调用 Data Agent：否。
4. 当前是否允许阶段性判断：允许。原因是登录链路、设备/IP、安全事件已完成，且支持 ATO 发生方式判断。
5. 当前是否需要继续等待 SQL 76451：建议继续等待，但不是当前阶段性 ATO 发生方式判断的必要前提；它主要用于补充发布行为下游分层。

