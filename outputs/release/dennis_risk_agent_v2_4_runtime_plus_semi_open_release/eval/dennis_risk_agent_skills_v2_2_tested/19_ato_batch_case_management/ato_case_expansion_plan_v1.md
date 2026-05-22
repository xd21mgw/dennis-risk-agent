# ATO Case Expansion Plan v1

## 1. 定位

ATO / 盗号 case 举一返三，是针对单个或少量 ATO case，在不直接真实查询的前提下，设计如何扩展发现同类受害账号、同类攻击链路和同类黑产基础设施。

边界：

- 不调用真实 DataAgent。
- 不访问真实平台。
- 不自动处置。
- 不自动上线策略。
- 不修改 release/dist。
- 只输出扩展方案、查询问题、证据卡结构和人工审核边界。

核心口径：

- ATO 的本质是账号控制权异常。
- ATO 举一返三不是找相同昵称、相同简介、相同导流文案。
- 昵称、简介、导流、关注、发布等后置行为只能作为 ATO 后置动作或变现路径补证；若缺少凭证、登录态、控制权变化证据，不应把这些后置行为归入 ATO 主因。

## 2. 扩展锚点分类

### A. 攻击链路锚点

用于扩展同类账号控制权异常链路：

- 异常登录方式。
- token refresh / switchUser / OAuth 授权。
- 新设备登录 / 异设备接管。
- 改绑 / 改密 / 安全操作。
- 异常发布 / 私信 / 关注 / 支付等后置动作。

优先级说明：

- 凭证 / token / OAuth / 登录态异常是 ATO 主线核心。
- 改密、换绑、安全设置变化是控制权变化强证据。
- 发布、私信、关注、支付等后置动作需要回连到前置控制权异常，不能单独定义 ATO。

### B. 基础设施锚点

用于扩展攻击者资源、代理链路和设备环境：

- IP / 网段 / 代理。
- deviceId / did / deviceceid。
- UA / appVersion / sdkVersion。
- OAuth app / token source。
- 地理位置跳变。
- 设备环境异常。

优先级说明：

- 同 IP / 同设备 / 同 UA 多账号异常登录是强扩展入口。
- appVersion / sdkVersion / UA 需要结合时间窗口和行为链路，避免正常版本聚集误伤。
- 地理位置跳变必须结合历史稳定性、登录成功链路和后续敏感动作。

### C. 后置动作锚点

用于扩展被接管后的行为目的和变现路径：

- 异常发布内容。
- 私信 / 关注 / 点赞对象。
- 导流文案 / 外部联系方式。
- 支付 / 提现 / 交易动作。
- 批量相似行为时间窗口。

边界：

- 后置动作是 ATO 后的异常行为，不是 ATO 主因。
- 如果只有后置动作聚集，而没有控制权异常证据，应进入导流作弊、互动作弊、内容风险或交易风险路径。

## 3. 扩展流程

### Step 1. Single Case Evidence Card

先把单 case 证据卡做清楚：

- 已知事实：用户、事件时间、异常动作、用户申诉、平台已读 observation。
- 强证据：凭证异常、异设备登录、改密/换绑、安全设置变化、token 使用异常。
- 中证据：IP / UA / 设备环境异常、登录失败后成功、后置敏感行为。
- 弱证据：单次异地、单条低置信关联、孤立后置行为。
- 反证：历史设备连续、行为自然、无控制权变化、窗口完整且无异常登录。
- 缺口：离线登录、发布审计、OAuth 授权、token 使用链路、行为对象聚集。

### Step 2. Expansion Anchor Extraction

从单 case 提取扩展锚点：

| anchor_type | examples | expansion_value | boundary |
|---|---|---|---|
| 攻击链路 | token refresh、OAuth、switchUser、改密、换绑 | 找同类控制权异常链路 | 必须有时间窗口 |
| 基础设施 | IP、did、UA、appVersion、OAuth app | 找同源攻击资源 | 不能单靠高频聚集定性 |
| 后置动作 | 发布、私信、关注、支付、导流 | 找同类被接管后行为 | 不能直接当 ATO 主因 |

### Step 3. Query Scope Control

先窄后宽：

1. 同一天 / 同小时级异常窗口。
2. 同攻击链路核心字段。
3. 同基础设施锚点。
4. 同后置动作对象或内容。
5. 再放宽到前后多日或相邻变体。

保护规则：

- 候选过多时返回 `too_many_candidates`。
- 不默认批量深查。
- 不直接导出明细。
- 需要长周期聚合时转 DataAgent / Hive，并明确字段、时间和审批边界。

### Step 4. Candidate Account Discovery

候选账号发现只生成候选，不生成处置名单：

- 同 token / OAuth / switchUser 行为聚集的账号。
- 同 IP / 设备 / UA / appVersion 的多账号异常登录。
- 同异常登录后短时间内发生改密、改绑、发布、私信、关注、支付的账号。
- 同后置动作对象、内容、外部联系方式或时间窗口的账号。

### Step 5. Evidence Card Backfill

对候选账号回填证据卡：

- 是否存在登录态 / 凭证异常。
- 是否存在账号控制权变化。
- 是否存在后置敏感动作。
- 是否共享基础设施。
- 是否存在正常反证。
- 是否存在数据窗口或权限缺口。

### Step 6. Pattern Summary

聚合输出：

- common attack chain。
- common IP / device / UA / OAuth app。
- common control-change operation。
- common post-action path。
- shared missing evidence。
- suspected attack path。
- confidence level。

### Step 7. Manual Review Boundary

人工复核必须覆盖：

- 是否存在正常登录 / 正常改密反证。
- 是否存在同设备家庭共用、测试账号、运营账号或授权自动化。
- 后置动作是否可能是正常用户行为。
- 是否存在日志窗口不完整、埋点缺失、平台权限阻断。

### Step 8. Strategy Direction Draft

只能输出候选策略方向：

- 候选规则逻辑。
- 证据强弱。
- 误伤风险。
- 需要补证。
- AB / 灰度建议。
- 查杀分离建议。

不能输出：

- 自动封禁结论。
- 自动上线结论。
- 未经验证的批量处置名单。

## 4. 内部 Agent / DataAgent / Codex 分工

| role | responsibility | boundary |
|---|---|---|
| 内部 Agent | 单个或小批账号在线只读补证，读取登录、档案、设备、策略等 observation | 不作为最终研判大脑，不做写操作 |
| DataAgent | Hive / 数仓批量取数分析，适合长周期登录、token、行为日志、发布审计和批量聚合 | 不是万能数据底座，不自动处置 |
| Codex | 文档、schema、run log、测试、扩展方案和方法论沉淀 | 不调用真实平台，不生成真实 observation |

## 5. 统一登录日志窗口边界

- 在线统一登录日志只按近 7 天可靠窗口处理。
- 超窗不调用在线日志做历史验证。
- 超窗时标记 `login_log_window_incomplete` / `offline_hive_required`。
- no_data 不能作为无盗号反证。
- no_data 不能解释为历史无登录或日志被清理。
- 长周期登录、token、发布审计、行为序列需要 DataAgent / Hive 或人工离线日志补查。

## 6. DataAgent / Hive 取数问题模板

以下是可转 DataAgent / Hive 的问题模板，不代表本轮已调用：

1. 在异常时间窗口内，是否存在同类 token refresh / OAuth / switchUser 行为聚集？
2. 是否存在同 IP / 设备 / UA / appVersion 的多账号异常登录？
3. 是否存在异常登录后短时间内发布 / 私信 / 关注 / 改绑等后置动作？
4. 是否存在同一基础设施关联多个被盗账号？
5. 是否存在同 OAuth app / token source 关联多个异常账号？
6. 是否存在改密 / 换绑 / 安全设置变化前后设备、IP、UA 突变？
7. 是否存在同一后置动作对象或导流文案关联多个账号？
8. 是否存在同一时间窗口批量 token revoke / stolen mark / 风控踢登录态？
9. 是否存在正常用户反证样本，如历史设备连续、常用 IP、无控制权变化、无后置敏感动作？

## 7. 输出模板

```text
扩展目标：
单 case 核心证据：
扩展锚点：
- 攻击链路锚点：
- 基础设施锚点：
- 后置动作锚点：
查询范围控制：
候选账号发现规则：
证据卡回填字段：
pattern summary：
缺失证据：
DataAgent / Hive 问题：
人工复核边界：
候选策略方向：
不能下的结论：
```

## 8. 边界总结

- ATO 举一返三围绕账号控制权异常和攻击链路扩展，不围绕相同昵称 / 简介扩展。
- 后置行为不能直接等同 ATO 主因。
- 在线日志超窗 no_data 不能作为无盗号反证。
- 不自动处罚。
- 不自动上线策略。
- 不调用真实 DataAgent。
- 不访问真实平台。
- 不修改 release/dist。
