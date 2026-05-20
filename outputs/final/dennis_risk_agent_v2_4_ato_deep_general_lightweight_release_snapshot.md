# Dennis Risk Agent v2.4 Release Snapshot

## 1. 当前版本定位

Dennis Risk Agent 是**通用业务风控专家 Agent**，不是 ATO 专用 Agent。

当前版本的定位已经明确分层：

- **ATO** 是第一个深度 DataAgent 闭环样板场景。
- 其他场景默认轻量支持，不默认查数。
- 当前不是全自动多轮 DataAgent 编排系统，而是**同步 DataAgent skill 调用式闭环**。

这意味着：

- ATO 可以深度跑通。
- 其他场景先做场景识别、证据拆解、取证方向和治理建议。
- 不应把所有风险问题都默认推入深度取证。

## 2. 已验证能力

### 2.1 ATO 深度能力

已验证能力包括：

- 短问入口。
- 单 case 判断。
- DataAgent 自动同步调用。
- DataAgent 返回解释。
- `provider_conclusion_hint` / `dennis_final_judgement` 分离。
- `SQL-only / partial / no_permission / timeout` 降级。
- runtime slim。

### 2.2 通用轻量能力

已验证能力包括：

- 场景识别。
- 攻击路径判断。
- 强 / 中 / 弱证据拆解。
- 缺失证据识别。
- DataAgent 取证方向生成。
- 治理建议。
- 人工复核边界。

### 2.3 子 Agent 运行态

已验证能力包括：

- 子 Agent 承载风控上下文。
- 主 Agent 不被风控 MD 污染。
- DataAgent 作为 skill 被 Dennis 子 Agent 触发。
- 当前是 webchat run mode，不是 session / thread mode 的自动多轮编排。

### 2.4 User ↔ Device Entity Resolution v2.6.0

已吸收 release package 的新增能力：

- 在主 Agent intent routing 与具体 hand 之间新增 User ↔ Device Entity Resolution Layer。
- 只做 `userId ↔ deviceId / did / deviceceid` 的实体转译。
- 不直接查风险，不直接做风险定性。
- 不替代 Device SDK、用户登录统一日志、档案中心、前端活跃画像或 DataAgent。
- 只为后续 hand 补齐必要入参。

双向解析主入口统一为 Weapon `graphData`：

- `user_to_device`：`groupValue={userId}`，`groupKey=USER_ID`，`dimKey=DEVICE_ID`，解析 `pointInfoMap` 中 `DEVICE_ID` 节点和 `relationEdgeList` 中 `source=userId`、`target=DEVICE_ID` 的直连边。
- `device_to_user`：`groupValue={deviceId}`，`groupKey=DEVICE_ID`，`dimKey=USER_ID`，解析 `pointInfoMap` 中 `USER_ID` 节点和 `relationEdgeList` 中 `source=deviceId`、`target=USER_ID` 的直连边。

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
- 关联关系不是风险结论；候选过多不默认批量深查。

运行态错误语义已文档化：

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
- `no_data` / `auth_required` / `permission_denied` 等真实运行态还未做真实接口验证。

## 3. 当前不承诺能力

当前版本不承诺：

- DataAgent running / polling 的实时回调。
- 一次 run 中自动多阶段暂停确认。
- 自动扩窗。
- 自动大样本回捞。
- 自动 SQL 重跑。
- 自动处罚、封禁、冻结、踢 token、上线策略。
- 非 ATO 场景默认深度取证。
- User ↔ Device Entity Resolution 自动批量深查。
- graphData `no_data` / `auth_required` / `permission_denied` 真实运行态已验证。
- 关联关系可直接作为风险结论。

## 4. 关键文件清单

当前关键产物包括：

- ATO POC 结果 review。
- runtime slimming plan / manifest。
- short question adaptation。
- general lightweight support positioning。
- general lightweight short question regression。
- DataAgent platform calibration。
- timeout policy。
- ATO release / walkthrough 相关文件。

这些文件已经把当前版本的定位、边界和运行态压缩路径明确下来。

## 5. 使用原则

### 5.1 用户只是问“怎么看 / 是不是 / 怎么防”

默认轻量研判，不查数。

### 5.2 用户明确要求“查数 / 调 DataAgent / 生成查询”

进入 DataAgent 取证方向。

### 5.3 ATO 可以进入深度 DataAgent 闭环

ATO 是当前已经打通的深度样板，可直接沿用同步闭环模式。

### 5.4 非 ATO 场景默认只给取证计划

除非用户明确要求，否则不默认深度取证。

### 5.5 高成本查询必须用户确认

长周期扩窗、多表 join、大样本回捞、可能较慢的 Hive 查询，都应显式确认。

## 6. 当前主要风险

### 6.1 DataAgent 模型差异会影响执行形态

不同 DataAgent 实现可能在同步返回、结果摘要和提示风格上存在差异，影响体验的一致性。

### 6.2 DataAgent 只读 / evidence only 仍依赖 prompt / skill 边界

当前的只读约束主要还是通过 prompt、skill、workflow 和 boundary contract 实现，不是硬性技术隔离。

### 6.3 子 Agent run mode 每次仍会重新加载上下文

runtime slim 能降低成本，但每次 run 仍会有上下文重载开销。

### 6.4 runtime slim 不一定降低 DataAgent 内部成本

runtime slim 主要降低 Dennis 侧默认加载成本，不一定改变 DataAgent 内部查询成本。

### 6.5 还缺真实组内同学试用反馈

目前已通过 POC，但仍需要真实使用反馈来验证短问、交互、解释质量和成本感受。

### 6.6 非 ATO 场景目前只是轻量支持

轻量支持可用，但还不是深度闭环。

## 7. 下一阶段建议

### P0

1. 固化 release snapshot。
2. 用 ATO slim 子 Agent 继续保留最小 POC 能力。
3. 建立简单 run record / observability 记录方式。

### P1

1. 选择第二个深度场景，建议优先反爬 / 协议。
2. 复用 ATO 模式：
   - router
   - workflow
   - response contract
   - DataAgent 取证模板
   - short question regression
   - slim runtime

### P2

1. 再扩活动反作弊。
2. 建立统一 release gate。
3. 建立全局 runtime slimming 规范。

## 8. 结论

**一句话总结：**
ATO 深度样板已跑通，通用轻量支持已验证，下一步应从“继续堆能力”转向“固化版本、可观测、再扩第二场景”。
