# Dennis Risk Agent v2.4 Runtime Plus Release

## 1. 版本定位

本 release 包对应 Dennis Risk Agent v2.4 Runtime Plus。

定位如下：

- Dennis Risk Agent 是通用业务风控专家 Agent。
- ATO 是第一个深度完全体样板。
- 非 ATO 通过 Runtime Plus 支持轻量但不表面的短问回答。
- DataAgent 只作为 Hive / 公司数仓取数分析能力，不是全能数据底座。

## 2. 默认启动加载方式

默认启动建议加载：

1. 总控 system prompt / working guide / routing rules。
2. `dennis_risk_agent_v2_4_runtime_plus_manifest_v1.md`
3. 通用 scenario contract 摘要。
4. DataAgent boundary 摘要。
5. timeout 摘要。
6. 当前场景 runtime summary。

`dennis_risk_agent_v2_4_startup_loading_order_checklist_v1.md` 建议作为初始化 / 配置期文件，不建议每轮问答常驻加载。

## 2.1 v2.6.0 User ↔ Device Entity Resolution Addendum

本 release 包已吸收 `computer_use_poc` 中的 v2.6.0 User ↔ Device Entity Resolution Layer。

定位：

- 位于主 Agent intent routing 和具体 hand 之间。
- 只做 `userId ↔ deviceId / did / deviceceid` 的实体转译。
- 不直接查风险。
- 不直接做风险定性。
- 不替代 Device SDK、用户登录统一日志、档案中心、前端活跃画像或 DataAgent。
- 只为后续 hand 补齐必要入参。

双向解析主入口统一为 Weapon `graphData`：

- `user_to_device`：`groupValue={userId}`，`groupKey=USER_ID`，`dimKey=DEVICE_ID`，解析 `pointInfoMap` 中 `DEVICE_ID` 节点，以及 `relationEdgeList` 中 `source=userId`、`target=DEVICE_ID` 的直连边。
- `device_to_user`：`groupValue={deviceId}`，`groupKey=DEVICE_ID`，`dimKey=USER_ID`，解析 `pointInfoMap` 中 `USER_ID` 节点，以及 `relationEdgeList` 中 `source=deviceId`、`target=USER_ID` 的直连边。

职责切分：

- Device SDK hand / `riskData` 不作为实体解析主入口，只在拿到 deviceId 后做 hook / frida / root / jailbreak / proxy / simulator / repack 等设备侧风险补证。
- 用户登录统一日志处理登录失败、登录流水、登录原因类问题，不应触发 graphData / Device SDK。
- 档案中心用户分析 API 只作为近期关联设备补充排序来源，不作为 `user_to_device` 主入口。
- DataAgent / Hive 只用于批量、长周期、历史聚合，不替代 graphData 在线实体解析。

路由边界：

- `userId + 设备风险`：先 `user_to_device` graphData，再 Device SDK 设备补证。
- `userId + 登录流水`：直接用户登录统一日志，不走 graphData / Device SDK。
- `deviceId + 设备风险`：直接 Device SDK，不做实体转译。
- `deviceId + 关联用户`：走 `device_to_user` graphData。
- 关联关系不是风险结论。
- 候选过多不默认批量深查。
- 缺失设备返回 `missing_device_id`。
- 缺失关联用户返回 `no_related_user / missing_user_id`。
- 候选过多返回 `too_many_candidates`。

已吸收的 runtime error semantics：

- `graphdata_error`
- `auth_required`
- `permission_denied`
- `no_related_entity`
- `no_direct_relation`
- `missing_device_id`
- `no_related_user / missing_user_id`
- `too_many_candidates`
- `parse_error`

验证状态：

- v2.6.0 文本回归 10/10 pass。
- graphData error semantics 已补充 8 个 error case。
- release package 更新前一致性检查已完成，未发现口径冲突。
- 仍未真实查询，未验证 graphData 在 `no_data` / `auth_required` / `permission_denied` 等运行态下的真实返回。

## 3. ATO 加载方式

ATO 命中后应进入完整体，不退化成轻量 summary。

ATO 完全体以 manifest 中列出的文件为准，包括：

- account_security_expert_skill。
- DataAgent parser / schema / join / interpretation / threshold。
- DataAgent boundary / timeout。
- ATO short question adaptation。
- ATO runtime slim / POC 结果。

## 4. 非 ATO 加载方式

非 ATO 场景默认加载对应 runtime summary：

- 反爬。
- 协议攻击。
- 群控。
- 破解包。
- 真人众包。
- 活动反作弊。
- 导流截流。
- 流量反作弊。

默认行为：

- 先判断场景。
- 先拆证据。
- 先给取证方向和治理建议。
- 不默认调 DataAgent。

## 5. DataAgent 边界

- 只有用户明确要求查数、拉样本、看日志、看画像、验证数据、生成查询问题时，才进入 DataAgent。
- DataAgent 只定位为 Hive / 公司数仓取数分析能力。
- 高成本查询必须用户确认。
- SQL-only / partial / timeout 不能强结论。

## 6. 推荐加载顺序

1. 总控规则。
2. Runtime Plus manifest。
3. 当前问题对应的 scenario summary。
4. 如果命中 ATO，再加载 ATO 完全体。
5. 如果用户明确要求查数，再进入 DataAgent 边界和取证模板。

## 7. 不建议一次性全量注入所有 deep skill

原因：

- token 成本高。
- 路由容易被历史材料污染。
- 非 ATO 场景只需要轻量但不表面的认知，不需要全量历史。

## 8. 集成前冒烟测试

本 release 包已通过集成前冒烟测试，确认：

- ATO 问题可进入完全体。
- 非 ATO 场景可默认走 runtime summary。
- 默认不误调 DataAgent。
- 不会把非 ATO 场景退化成表面化回答。

## 9. 回归说明

本 release 包中的 8 个非 ATO 扩展案例回归**不作为本次 release 阻塞项**，后续作为质量体检执行。
