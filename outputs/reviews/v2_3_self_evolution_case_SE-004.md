# v2.3 自我进化交叉 Case：SE-004

## 对抗点

只有高频访问、目标一致，但没有调度、路径、关系、收益证据。

## 交叉 Skill

- 主控候选：evidence_decomposition_skill
- 辅助候选：group_control_expert_skill、protocol_attack_expert_skill

## 修改结论

未修改 group_control_expert_skill。它已有明确规则：只有高频、设备聚集、账号聚集、IP 聚集、单接口异常，不得定性群控；协议 Skill 也有只有高频不得定性协议。

## 复核结论

当前最多下“高频/目标一致异常，进入监控和补证”。不得判群控，不得判协议。

## 需要补证

同批启动/停止、路径节奏、账号设备收益成团、接口序列、端侧链路、合法运营/热点/测试反证。

## 评分

修改后 89/100。未回写原因：现有 group_control 和 protocol 规则已覆盖，主要靠执行契约弱信号降级。
