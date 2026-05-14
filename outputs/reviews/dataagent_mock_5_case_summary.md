# Data Agent Mock 5 Case 回归汇总

说明：本轮基于 `07_tools/dataagent/` 抽象层做离线 mock 回归，不调用真实 Data Agent，不修改 Skill 文件，不编造真实表名、字段名、API 或真实结果。

## Case 清单

| Case | 主题 | 输出文件 | mock status | 结论等级 | 是否强结论 |
|---|---|---|---|---|---|
| AC-003 | 单纯协议判定 | `outputs/reviews/dataagent_mock_case_AC-003.md` | success | 高度疑似 | 否 |
| AC-004 | 群控真机爬取 | `outputs/reviews/dataagent_mock_case_AC-004.md` | success | 明确判断 | 是 |
| AS-001 | token 泄露 | `outputs/reviews/dataagent_mock_case_AS-001.md` | partial | 高度疑似 | 否 |
| ACT-003 | 渠道抢量 | `outputs/reviews/dataagent_mock_case_ACT-003.md` | success | 证据不足 | 否 |
| MIX-001 | 直播间截流 / 站外添加 | `outputs/reviews/dataagent_mock_case_MIX-001.md` | success | 高度疑似 | 否 |

## 关键发现

1. Data Agent 抽象层能把风控问题转成可执行的证据型查询意图。
2. 结论阈值能有效防止“有数据返回就强结论”：
   - AC-003 有多项协议证据，但缺方法级短链和完整包工件排除，只给高度疑似。
   - ACT-003 有 CTIT 和自然量异常，但存在预算/归因变更反证，降级为证据不足。
3. partial 返回能被正确降级：
   - AS-001 缺可信设备、用户确认和正常网络反证，不打明确 token 泄露。
4. 能下明确判断的 case 需要强证据链和关键反证排除：
   - AC-004 同时具备真机团组、同批调度、路径模板、资产访问集中和合法矩阵排除。
5. 混合场景能保持主控边界：
   - MIX-001 归导流截流主控，不默认转反爬或协议。

## 需要人工确认的点

所有 5 个 case 都建议人工确认，原因不同：

- AC-003：协议强处置前需补方法级短链和签名细节。
- AC-004：明确判断后仍需确认业务白名单和误伤影响。
- AS-001：账号安全处置高误伤，且 mock 为 partial。
- ACT-003：渠道结算影响高，且存在业务变更反证。
- MIX-001：涉及社交互动和私信处置，需要抽样确认承接内容。

## 是否符合 dataagent_conclusion_thresholds_v1.md

整体符合。

- 明确判断只出现在 AC-004，原因是强证据链闭合且关键反证已排除。
- 高度疑似用于 AC-003、AS-001、MIX-001，原因是中强证据成组但仍缺关键闭环。
- 证据不足用于 ACT-003，原因是存在明确业务变更反证且缺点击/设备异常。
- 没有把单点异常直接解释为协议、群控、token 泄露、渠道作弊或导流黑产。

## 后续建议

- 把 `query_intent` 增加 `case_id`、`risk_domain`、`risk_type`、`manual_review_required` 字段，便于未来平台审计。
- 为高风险处置类 case 增加“结果不可直接处罚”的结构化字段。
- 后续可继续补 5 个低质/DAU/破解包/合法矩阵/AB 实验 case，验证更多反证分支。
