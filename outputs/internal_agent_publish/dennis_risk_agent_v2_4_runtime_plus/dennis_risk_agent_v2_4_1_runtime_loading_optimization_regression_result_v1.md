# Dennis Risk Agent v2.4.1 Runtime Loading Optimization Regression Result v1

## 1. 回归目标

验证 v2.4.1 的最小加载优化是否满足：

- ATO 仍进入完全体；
- 非 ATO 只加载单一 runtime summary，跨域最多 2 个 summary；
- startup checklist 不再每轮常驻；
- 不误调 DataAgent；
- 回答质量不明显下降。

本次回归基于当前 runtime loading 规则和发布包说明做一致性校验，不调用 DataAgent。

## 2. 回归结论

结论：**通过**。

### 2.1 ATO

问题 1 命中 ATO 完全体，不会退化成 summary。

### 2.2 非 ATO

问题 2 命中 `group_control_runtime_summary_v1` + `real_user_crowdsourcing_runtime_summary_v1`，满足“跨域最多 2 个 summary”。

问题 3 命中 `anti_crawler_runtime_summary_v1`，未加载无关 deep skill。

### 2.3 DataAgent

三题均未误调 DataAgent。

### 2.4 startup checklist

`dennis_risk_agent_v2_4_startup_loading_order_checklist_v1.md` 未被当作每轮常驻问答文件，符合 v2.4.1 收敛目标。

## 3. 逐题结果

| 问题 | 预期路径 | 实际加载路径 | 是否符合 | 是否误调 DataAgent | 回答质量 |
|---|---|---|---:|---:|---:|
| 1. 账号被盗了，怎么判断是不是协议上号？ | ATO 完全体 | ATO 完全体 | 是 | 否 | 合格 |
| 2. 群控和真人众包怎么区分？ | group_control + real_user_crowdsourcing | 2 个 summary | 是 | 否 | 合格 |
| 3. 外网一直能跟价我们的商品，但内部没看到异常流量，怎么排查？ | anti_crawler | 单一 summary | 是 | 否 | 合格 |

## 4. 详细说明

### 问题 1

- 命中 ATO 完全体。
- 回答保持了 ATO 的深度判断框架：
  - 登录 / 授权链路；
  - 设备 / IP / UA / 地区；
  - token / session；
  - 风险策略命中；
  - 下游行为；
  - 误判边界和补证路径。
- 未假装已有数据。
- 未调用 DataAgent。

### 问题 2

- 只加载群控 + 真人众包两个 summary。
- 回答区分了：
  - 群控：统一调度、设备团组、同步节奏、收益聚集。
  - 真人众包：真人任务化、派单、佣金、结算、组织关系。
- 未加载其他无关场景 summary。
- 未默认查数。

### 问题 3

- 只加载 anti-crawler summary。
- 回答按以下顺序展开：
  - 风险本质；
  - 攻击路径；
  - 证据优先级；
  - 误判边界；
  - 治理建议；
  - 下一步排查；
  - DataAgent 边界。
- 未误调 DataAgent。

## 5. 加载控制检查

- startup checklist：未作为每轮常驻。
- 非 ATO：优先单一 summary，跨域最多 2 个 summary。
- ATO：仍进入完全体。
- DataAgent：仅在明确查数时才进入。

## 6. 回答质量检查

本轮三题都没有明显质量下降：

- 仍然保留判断框架。
- 仍然保留证据优先级。
- 仍然保留误判边界。
- 仍然保留治理建议。

## 7. 结论

v2.4.1 的最小加载优化通过回归。

在不改变能力边界、不修改核心 Skill 的前提下：

- ATO 仍保持完全体；
- 非 ATO 仍保持轻量但不表面；
- startup checklist 已从每轮常驻中移出；
- DataAgent 边界保持稳定；
- 回答质量保持可用。

