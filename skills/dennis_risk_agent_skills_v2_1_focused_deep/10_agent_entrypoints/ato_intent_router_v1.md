# ATO Intent Router v1

## 0. 定位

本文件定义 ATO 场景下，Dennis Risk Agent 如何把用户自然语言问题路由到 ATO scenario workflows。

目标不是让盗号同学阅读 Markdown，而是让他们直接问 Agent，Agent 自动完成：

- 单 case 研判。
- 批量 case 分层。
- Data Agent 取证问题生成。
- Data Agent 返回解释。
- 举一反三 / 回捞建议。
- 治理方案。
- 复盘沉淀。

边界：
- ATO 是第一个优先落地场景，不改变 Dennis Risk Agent 的通用风险专家定位。
- 本 router 不替代 `account_security_expert_skill`，而是调用它。
- 本 router 不调用真实 Data Agent。

## 1. 触发关键词

命中以下任意关键词或语义时，可进入 ATO router：

```text
盗号
被盗
ATO
账号接管
登录异常
异地登录
扫码
Web 扫码
异步登录
OAuth
授权登录
钓鱼
验证码
短信泄露
密码泄露
token
session
登录态
异常发布
色情作品
招嫖内容
客诉
申诉
解封
回扫
回捞
批量样本
Data Agent 返回
```

## 2. 基础路由规则

| 用户意图 | 示例问题 | workflow |
|---|---|---|
| 单 case 判断 | “这个用户是不是被盗？”、“这个客诉可信吗？” | `single_case_judgement` |
| 批量样本分层 | “这批盗号样本帮我分层” | `batch_case_clustering` |
| 生成 Data Agent 问题 | “怎么查数？”、“帮我生成 Data Agent 问题” | `dataagent_question_generation` |
| 解释 Data Agent 返回 | “这是 Data Agent 返回，帮我解释” | `dataagent_result_interpretation` |
| 举一反三 / 回捞 | “怎么回捞同类盗号？”、“哪些特征能用？” | `generalization_and_recall` |
| 治理方案 | “这类盗号怎么治理？” | `governance_design` |
| 复盘沉淀 | “这批 case 能沉淀什么？”、“要不要回写 Skill？” | `review_and_skill_distillation` |

## 3. 多意图处理

### 3.1 批量判断 + Data Agent 问题

用户问题：

```text
帮我看这批样本是不是盗号，并给 Data Agent 问题。
```

路由：

```text
batch_case_clustering
→ dataagent_question_generation
```

输出：
- 先给样本分层。
- 再给按层级拆分的 Data Agent 只读取证问题。

### 3.2 Data Agent 返回 + 回捞

用户问题：

```text
Data Agent 返回了，帮我判断能不能回捞。
```

路由：

```text
dataagent_result_interpretation
→ generalization_and_recall
```

输出：
- 先解释数据发现、反证和缺口。
- 再做原始观测 / 数据发现 / 候选特征 / 机制特征 / 本质规则分层。
- 最后给回捞优先级和误伤风险。

### 3.3 单 case 判断 + 治理

用户问题：

```text
这个用户是不是被盗，如果是该怎么处理？
```

路由：

```text
single_case_judgement
→ governance_design
```

输出：
- 先给证据等级和是否需要补证。
- 再给登录前、中、后和恢复链路治理建议。

### 3.4 批量复盘 + 是否回写

用户问题：

```text
这批 case 能不能沉淀到 Skill？
```

路由：

```text
batch_case_clustering 或 dataagent_result_interpretation
→ review_and_skill_distillation
```

输出：
- 区分可回写规则、只进 eval、需更多验证、不应沉淀。

## 4. 边界规则

ATO router 必须始终遵守：

- 用户申诉只能作为线索。
- 人工备注只能作为线索。
- Data Agent 返回不是最终判断。
- `provider_conclusion_hint` 不等于 `dennis_final_judgement`。
- 无发布不能反向排除 ATO。
- 发布异常内容不是 ATO 必要条件。
- 具体策略名不能作为本质特征。
- 样本比例不能直接写入 Skill。
- SQL-only 不是证据。
- no_permission / partial / empty_result 必须降级。

## 5. 场景内分类提示

ATO router 应自动区分：

### 5.1 ATO 发生方式

- Web 扫码 / 异步登录 / 授权登录。
- 地推扫码 / 助力诱导。
- 钓鱼 / 验证码泄露。
- token/session 泄露。
- 账号租借 / 交易。
- 非盗号 / 历史 / 不确定。

### 5.2 ATO 后下游作恶方式

- 发布色情 / 招嫖 / 导流内容。
- 点赞 / 关注 / 评论 / 私信。
- 爬虫 / 接口访问 / 资产窃取。
- 活动套利 / 抢福利。
- 直播间截流 / 私域导流。
- 账号交易 / 养号 / 转生。
- 仅登录控制，尚未观测到明显作恶。
- 未验证 / 权限不足。

## 6. Data Agent 触发判断

需要 Data Agent 的情况：

- 用户要求查数 / 取证 / 共性分析。
- 缺登录、授权、token/session、设备、发布、策略、活动等证据。
- 用户贴出批量样本，需要分布和聚合。
- 用户贴出 Data Agent 返回，需要解释。

不需要 Data Agent 的情况：

- 用户只问概念边界。
- 用户只要求治理打法框架。
- 用户要求对已有 Data Agent 返回做解释。
- 用户要求做 Skill / eval / review 沉淀。

## 7. 短问入口适配

真实策略同学通常只会给 1-3 句话。router 必须先做短问意图识别，再判断是否需要追问。

### 7.1 短问类型

- 单 case 判断：这个用户是不是被盗 / 能不能认盗号。
- 批量样本分层：这批扫码 case 帮我看下 / 有没有共性。
- Data Agent 问题生成：帮我查下 / 怎么问 Data Agent。
- Data Agent 返回解释：这能不能认 / 这个结果够不够。
- 下游作恶边界：没发布是不是就不是盗号 / 有发布是不是就是盗号。
- 回捞 / 策略：这个能不能回捞 / 要不要打。
- 治理建议：这类怎么处理 / 要踢 token 还是封号。

### 7.2 处理顺序

1. 先识别 intent。
2. 判断信息是否足够。
3. 如果不足，优先追问关键字段。
4. 如果能给方向，先给阶段性判断。
5. 如果需要 Data Agent，生成低成本最小取证问题。
6. 不默认跑长周期、不默认大样本、不默认多表复杂 join。

### 7.3 缺信息追问规则

#### 单 case

最少需要：

- `user_id` / `case_id`
- 异常时间
- 用户自述或异常行为
- 是否已有 Data Agent 返回

如果缺 `user_id` 或时间窗：

- 不进入取证；
- 先返回 missing_input_request；
- 明确提示需要补什么字段。

#### 批量 case

最少需要：

- 样本列表
- 时间窗口
- 当前标签或来源
- 期望目标：分层 / 回捞 / 复盘 / 查共性

#### Data Agent 返回解释

最少需要：

- Data Agent 原始返回
- 查询状态：`success / SQL-only / partial / no_permission / timeout`
- 查询时间窗

### 7.4 默认最小取证策略

用户只说“帮我查是不是盗号”时，默认：

- 单 `user_id`
- 单日或 1 小时时间窗，优先用户给的异常时间
- 先查登录 / 授权 / 设备 / IP / UA / 地区 / 账号安全风险命中
- 暂不查长周期历史画像
- 暂不查大样本回捞
- 暂不查高成本下游全链路，除非用户确认

### 7.5 多意图处理

常见组合：

- “帮我看这批是不是盗号，并生成 Data Agent 查询问题”  
  → `batch_case_clustering` → `dataagent_question_generation`
- “Data Agent 返回了，帮我判断能不能回捞”  
  → `dataagent_result_interpretation` → `generalization_and_recall`
- “这批 case 能沉淀什么，要不要回写 Skill”  
  → `batch_case_clustering` / `dataagent_result_interpretation` → `review_and_skill_distillation`

### 7.6 短问边界

- 用户自述 / 人工备注只能作为线索。
- 无发布不能反向排除 ATO。
- 有发布不能直接确认 ATO。
- Data Agent 是 evidence provider。
- Dennis final judgement 由 Dennis Agent 生成。
- SQL-only / partial / timeout 不能强结论。
- 高风险处置动作需要人工确认。
- 具体策略名不能作为本质特征。

## 7. 路由输出字段

router 内部应输出：

```yaml
ato_route:
  triggered: true
  workflow:
  secondary_workflow:
  reason:
  minimum_inputs_needed:
  dataagent_needed:
  response_contract:
  boundary_warnings:
```

## 8. 非 ATO 转交

如果用户问题看似盗号但核心不是账号接管，应转交：

- 导流 / 私域触达：`traffic_diversion_interception_skill`
- 协议 / 无端请求：`protocol_attack_expert_skill`
- 群控 / 统一调度：`group_control_expert_skill`
- 破解包 / SDK 缺失：`cracked_app_expert_skill`
- 活动套利：`activity_anti_cheating_expert_skill`
- 反爬资产访问：`anti_crawler_expert_skill`

ATO router 是账号安全场景入口，不是所有风险问题的默认入口。
