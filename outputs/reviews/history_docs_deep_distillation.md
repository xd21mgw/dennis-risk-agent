# 历史 PDF 材料深度沉淀

## 输入材料

- `2023年反作弊组年度述职.pdf`
- `2024年反作弊组年度述职.pdf`
- `2025年反作弊年度述职.pdf`
- `职级晋升评审沐广武-2024年3月.pdf`
- `职级晋升评审沐广武-2025年3月-V2.pdf`

同时读取了桌面上对应的 2024、2025 晋升 PPTX，以获得更完整的 slide 文本。

## 抽取方式

- 用 `pypdf` 抽取 PDF 文本；
- 用 PPTX XML 结构抽取 slide 文本；
- 重点检索：渠道、投放、抢量、归因、RTA、CPA、反爬、版权、账号、token、弱端、群控、协议、本质、BP、沙盒等关键词。

## 总体沉淀

### 1. 输出风格

历史材料的强点不是字段完整，而是有清晰主线：

```text
业务情况 → 核心思考 → 策略打法 → 核心进展 + 一句话总结 → 做得好的 / 可提升的 → 下一步方向
```

其中“一句话总结”非常关键，要把项目从流水账压缩成判断。

### 2. 增长反作弊

主线：

```text
站内黑产对抗守基本盘
→ 真人低质做厚价值
→ 站外投放反作弊拓展防线
```

关键沉淀：

- 黑产假量：通能策略体系提升攻防效率；
- 真人低质：不是黑产，重点是钱效监控和业务优化；
- 站外投放：从 0 到 1 建渠道抢量识别能力，落地内外双策略评估；
- 落地应用：不能只识别，要进入归因沙盒、CPA 调价、CPA 结算和渠道质量分。

### 3. 渠道抢量 / RTA

材料对齐后的核心本质：

```text
渠道抢量不是带来用户，而是抢到归因。
RTA、曝光、点击、商店下载、激活、端内归因是否连续，是判断真实贡献和抢量占坑的关键。
```

必须沉淀的识别与应用：

- 媒体下发 RTA 信息；
- 广告曝光；
- 代理上传真实点击；
- 端内归因统计；
- CPA 调价；
- CPA 结算；
- 结算后诉讼。

评估上要同时看抢量设备召回/准确率、点击召回、自然量准确率、付费量增量误伤和归因沙盒关联止损。

### 4. 反爬 / 版权

主线：

```text
接口式被动防控
→ 核心资产分级
→ 视野外漏洞主动发现
→ 非常6+1体系
→ 版权诉讼和资产保护价值
```

关键沉淀：

- 反爬目标是资产安全；
- 爬虫敌人模式包括竞对、黑灰产、三方公司、内部/开放平台；
- 攻击常找漏洞：未接反爬、未开签名、接口复用、过度数据、越权、路径穿越；
- 版权保护要前链路产品改造、中链路策略对抗、后链路取证诉讼；
- 外部泄漏素材不仅用于证明损害，也用于溯源爬取路径。

### 5. 账号安全

主线：

```text
历史负债清偿
→ 可信体系减少打扰
→ 盗号分型治理
→ token / 弱端 / 验证体系补债
→ 账号生命周期治理
```

关键沉淀：

- 历史负债包括漏洞、不支持验证、token 永久有效、无法踢出登录态、未接风控、弱端入口、核心指纹缺失；
- 治理分降负债、降发生、降影响；
- 高价值账号重安全，非高价值重体验；
- token 泄露要看能否踢出、是否跨环境、是否和敏感动作绑定；
- 小号不能只看注册，要扩到活跃、回扫、交易和下游作恶。

### 6. 方法论

稳定表达：

- 风控不是防控，更是治理；
- 防控是降影响，治理是降发生；
- 大问题小解，小问题根解；
- 从单一指标评估到立体监控发现；
- 从止损化到通用化再到本质化；
- 用望远镜看行业和外部情报，用显微镜看内部链路和证据。

## 回写文件

已回写：

- `skills/dennis_risk_agent_skills_v2_1_focused_deep/02_domain_skills/activity_anti_cheating_expert_skill.md`
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/02_domain_skills/anti_crawler_expert_skill.md`
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/02_domain_skills/account_security_expert_skill.md`
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/01_core_skills/material_delivery_skill.md`
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/12_material_distillation/history_material_lessons_v2_1.md`

## 后续可选回写

- 单独新增 `channel_ads_anti_cheating_skill.md`，把站外投放/RTA/归因沙盒/CPA 结算做成独立 Skill；
- 单独新增 `copyright_protection_skill.md`，把版权保护从反爬 Skill 中拆出，强化诉讼、取证、溯源和内容清理；
- 更新 50 case 中 ACT-003、AC-014、AC-015、AS-001、AS-004、BI-003 的 golden expectation。
