# ATO 客诉标签体系梳理

## 1. 是否盗号分布

基于有效 user_id 行统计：

| 标签 | 工作表1 | 工作表2 | 合计观察 |
|---|---:|---:|---|
| 是 | 515 | 77 | 主体正例来源 |
| 否 | 37 | 0 | 主要来自工作表1，是反例回归核心 |
| 不确定 | 4 | 0 | 适合做证据不足边界 |
| 历史case | 1 | 0 | 结构化标签较少，更多写在备注 |
| 空值 | 105 | 0 | 待清洗，不能自动定性 |

问题：
- “历史case”既作为 `是否盗号` 标签出现，也大量写在 `盗号具体原因` 中。
- 空值样本中可能包含非被盗、历史 case、token 漏洞等，需要人工或数据补证，不能直接归类。

建议标准化：

```text
is_ato_label:
- positive
- negative
- uncertain
- historical
- missing
```

## 2. 盗号大类分布

| 盗号大类 | 工作表1 | 工作表2 | 备注 |
|---|---:|---:|---|
| 欺诈 | 230 | 65 | 最大类，覆盖地推、钓鱼、扫码等 |
| 登录信息泄露 | 201 | 5 | 主要是短信泄露、密码泄露 |
| 盗号兜底 | 60 | 0 | 口径偏兜底，需进一步拆分 |
| token泄露 | 23 | 4 | 与 token / session 取证模板强相关 |
| 租借实名 | 1 | 0 | 更像账号交易 / 实名租借边界 |
| 用户历史被封禁，近期发现后客诉 | 1 | 0 | 不应作为标准大类 |
| 空值 | 146 | 3 | 待清洗 |

建议标准化：

```text
attack_category:
- fraud
- credential_leakage
- token_or_session_leakage
- ato_fallback
- account_rental_or_realname_rental
- historical_or_late_complaint
- non_ato
- unknown
```

## 3. 盗号小类分布

| 盗号小类 | 工作表1 | 工作表2 | 备注 |
|---|---:|---:|---|
| 短信泄露 | 168 | 5 | 需要区分 app / web / 小程序登录 |
| 钓鱼欺诈 | 117 | 37 | 工作表2中占比最高 |
| 地推欺诈 | 77 | 27 | 典型线下扫码 / 拿手机 / 助力链路 |
| 盗号兜底 | 49 | 0 | 需要被更细分替代 |
| 密码泄露 | 31 | 0 | 适合 ATO password takeover |
| 扫码欺诈 | 25 | 1 | 与地推欺诈有交叉 |
| token泄露 | 22 | 3 | 需要 token/session 取证 |
| 租借账号 | 13 | 1 | 账号交易 / 主体授权边界 |
| 其他欺诈 | 8 | 0 | 需要补子类 |
| 三方账号泄露 | 2 | 0 | 可归 credential_leakage |
| 空值 | 150 | 3 | 待清洗 |

建议标准化：

```text
attack_subcategory:
- ground_promotion_scan
- phishing_web_login
- qr_oauth_scan
- sms_code_leakage
- password_leakage
- token_reuse_or_session_hijack
- account_rental
- third_party_account_leakage
- fallback_unknown
- non_ato
- historical
```

## 4. 作恶类型分布

| 作恶类型 | 工作表1 | 工作表2 | 备注 |
|---|---:|---:|---|
| 色情视频-网址 | 38 | 38 | 最主要作恶类型 |
| 招嫖视频-微信 | 15 | 15 | 站外承接线索 |
| 招嫖视频-钱 | 5 | 5 | 收益 / 招嫖链路 |
| 色情视频-网址单人 | 3 | 3 | 与“色情视频-网址”可标准化归并 |
| 视频标题 | 1 | 1 | 标题导流 / 内容承接 |
| 视频招嫖-金额 | 1 | 1 | 与招嫖视频-钱相近 |
| 低俗视频 | 1 | 1 | 内容违规但类型弱 |
| 空值 | 595 | 10 | 作恶类型缺失严重 |

建议标准化：

```text
abuse_type:
- porn_video_url
- prostitution_wechat
- prostitution_money
- porn_video_single_url
- title_diversion
- vulgar_video
- unknown
```

## 5. 标签不一致问题

| 问题 | 示例 | 建议 |
|---|---|---|
| 大类/小类层级混用 | `token泄露` 同时是大类和小类 | 标准化为 `token_or_session_leakage / token_reuse_or_session_hijack` |
| 历史 case 写法不一 | `历史case`、`24年盗号`、`25年5月...` | 增加 `case_temporal_status=historical` |
| 回捞信息写入原因 | `已回捞`、`未回扫`、`需二次回捞` | 拆成 `resweep_status` 和 `resweep_note` |
| 非盗号原因写入原因字段 | `非被盗`、`反诈封禁`、`导流封禁` | 标准化为 negative reason |
| 作恶类型粒度不一 | `色情视频-网址` vs `色情视频-网址单人` | 保留原值，同时映射标准枚举 |
| 盗号兜底过宽 | `盗号兜底` | 后续用 Data Agent 补证后重分类 |

## 6. 应进入 account_security_expert_skill 的标签

适合进入 Skill 的通用标签和判断边界：

- 地推扫码欺诈
- 钓鱼网站 / web 登录盗号
- 短信验证码泄露
- 密码泄露
- token 泄露 / 登录态复用
- 扫码 / OAuth 授权异常
- 租借账号 / 实名租借作为反证或边界
- 非盗号 / 历史 case / 证据不足样本

不应直接进入 Skill 的细碎标签：

- 具体人名、核查人。
- 单个来源域名或工具名。
- 具体回捞量级。
- 未验证的地名、活动点位、第三方平台线索。

## 7. 应进入 evidence / Data Agent 取证模板的标签

适合进入 Data Agent 取证模板：

- 登录方式：密码、短信验证码、OAuth、扫码、web、小程序、app。
- 设备：新设备、历史设备、Web 新设备、设备活跃天数。
- token/session：生成、置换、踢出、复用、多端冲突。
- 发布链路：异常登录后发布、发布设备、发布 IP/地区、删除/隐藏状态。
- 敏感动作：换绑、改密、找回、注销、账号资料变更。
- 策略 / 风险画像：stealAccount、异常登录、风险设备、高异常记录。
- 回捞：是否存在回扫记录、是否可批量扩展。

## 8. 结论

标签体系已经足够支撑 ATO 回归和 Data Agent query_intent 设计，但不能直接作为最终事实使用。应采用：

```text
人工标签 / 用户自述 / 备注线索
→ Data Agent 离线取证
→ parser evidence
→ Dennis Agent 解释
→ 人工复核
```
