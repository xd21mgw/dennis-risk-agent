# v2.3 自我进化交叉 Case：SE-005

## 对抗点

外网价格同步，但内部没有明显接口异常。

## 交叉 Skill

- 主控候选：anti_crawler_expert_skill
- 辅助候选：protocol_attack_expert_skill、group_control_expert_skill、risk_chain_reconstruction_skill

## 修改结论

未修改 anti_crawler_expert_skill。它已有资产分级、资产级溯源、缓存/前端/弱端、合作方/内部链路泄漏分支，并禁止把外部报价/投诉当内部证据。

## 复核结论

当前最多下“价格资产外泄待溯源”。不能直接判协议。

## 需要补证

SKU/price_id/url/hash、水印/蜜罐、外部同步时延、CDN/缓存、弱端、合作方、后台导出、协议/群控/真人证据。

## 评分

修改后 90/100。未回写原因：现有反爬规则覆盖较完整。
