# Dennis Risk Agent v2.4.1 Runtime Loading Optimization Regression Plan v1

## 1. 测试目标

验证 v2.4.1 的最小加载优化是否满足：

- ATO 仍进入完全体。
- 非 ATO 只加载单一 summary 或最多 2 个 summary。
- startup checklist 不再每轮常驻。
- 不误调 DataAgent。
- 回答质量不下降。

## 2. 测试问题

### 问题 1

**用户问题**：账号被盗了，怎么判断是不是协议上号？

- 预期命中的加载路径：ATO 完全体。
- 是否允许 DataAgent：允许，但仅在用户明确要求查数时。
- 合格标准：
  - 进入 ATO 完全体。
  - 说明判断框架、证据优先级、误判边界、治理建议。
  - 不假装已有数据。

### 问题 2

**用户问题**：群控和真人众包怎么区分？

- 预期命中的加载路径：group_control_runtime_summary_v1 + real_user_crowdsourcing_runtime_summary_v1。
- 是否允许 DataAgent：默认不允许。
- 合格标准：
  - 只加载必要的 2 个 summary。
  - 讲清设备、行为、账号、任务链、成本结构差异。
  - 不默认查数。

### 问题 3

**用户问题**：外网一直能跟价我们的商品，但内部没看到异常流量，怎么排查？

- 预期命中的加载路径：anti_crawler_runtime_summary_v1。
- 是否允许 DataAgent：默认不允许。
- 合格标准：
  - 不加载无关 deep skill。
  - 给出攻击路径、证据优先级、误判点、治理建议、下一步排查。
  - 只有用户明确要求查数时才给 DataAgent / Hive 方向。

## 3. 回归判定标准

### 3.1 路由

- 问题 1 必须命中 ATO 完全体。
- 问题 2 必须命中群控 + 真人众包 runtime summary。
- 问题 3 必须命中反爬 runtime summary。

### 3.2 加载控制

- startup checklist 不应每轮常驻。
- 不应默认加载所有 deep skill。
- 不应默认加载多个无关 summary。

### 3.3 DataAgent

- 不误调 DataAgent。
- 非 ATO 默认不查数。
- 高成本查询仍需用户确认。

### 3.4 回答质量

- 回答不能表面化。
- 必须保留判断框架、证据优先级、误判边界和治理建议。

## 4. 通过标准

三题全部满足以上要求即通过。

