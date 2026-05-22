# Black Market Account Matrix Strategy Direction Template v1

## 1. 定位

本模板输出黑产账号矩阵 / 导流互动 / 互粉互动 / 养号账号池的候选策略方向。它不是自动上线方案，不执行处置。

必须包含：

- 简介签名聚类。
- 联系方式归一化。
- 账号矩阵识别。
- 行为链路补证。
- 查杀分离 / AB 评估。
- 误伤风险控制。

## 2. Candidate Strategy Directions

### Direction 1: 简介签名聚类

| 字段 | 内容 |
|---|---|
| candidate_direction | 对简介模板做归一化聚类，识别“一起互动 + 联系方式 redacted”等高相似文案 |
| required_evidence | intro_pattern、normalized_contact_hash、重复文案比例 |
| false_positive_risk | 正常活动模板、运营模板、普通社交表达 |
| boundary | 简介聚类只作查证入口，不直接处置 |

### Direction 2: 联系方式归一化

| 字段 | 内容 |
|---|---|
| candidate_direction | 对薇/微信/符号拆分/emoji 混淆联系方式做 redacted + hash 聚合 |
| required_evidence | contact_hash_cluster、账号数量、跨样本复用情况 |
| false_positive_risk | 正常用户展示联系方式、商家账号 |
| boundary | 不输出联系方式明文 |

### Direction 3: 账号矩阵识别

| 字段 | 内容 |
|---|---|
| candidate_direction | 结合简介、昵称、adminaction、注册天数、UID 号段识别账号矩阵候选 |
| required_evidence | 多维聚集共现，且有行为链路补证 |
| false_positive_risk | 正常活动批量注册、同主题用户群 |
| boundary | 账号矩阵候选不等于黑产结论 |

### Direction 4: 行为链路补证

| 字段 | 内容 |
|---|---|
| candidate_direction | 补充关注、互粉、评论、私信、导流点击等链路，验证矩阵是否真实协同 |
| required_evidence | account_edges、behavior_sequence、time_cohort |
| false_positive_risk | 自然社交互动、粉丝群正常互粉 |
| boundary | 行为链路用于补证，不直接替代人工评估 |

## 3. AB / 查杀分离评估

建议阶段：

1. offline_eval：评估聚类覆盖、样本纯度、误伤样本。
2. shadow_monitoring：记录候选命中，不处置。
3. manual_review_sampling：抽检正常活动模板、商家账号、真实社交用户。
4. check_kill_separation：查证条件和处置条件分离。

关键指标：

- cluster_precision_after_review
- contact_hash_reuse_rate
- behavior_edge_support_rate
- false_positive_template_rate
- normal_campaign_overlap_rate
- manual_review_pass_rate

## 4. 禁止输出

- “命中简介模板即可封禁。”
- “这些账号确认都是黑产。”
- “adminaction 一致即可处置。”
- “联系方式聚类就是导流作弊。”
- “直接上线查杀。”

## 5. 推荐话术

- “当前可形成账号矩阵候选方向，但需要行为链路和误伤样本验证。”
- “简介和昵称聚类适合作为召回入口，不能直接做处置依据。”
- “建议先做查杀分离：聚类查证、人工抽检、shadow 监控，再讨论策略化。”
