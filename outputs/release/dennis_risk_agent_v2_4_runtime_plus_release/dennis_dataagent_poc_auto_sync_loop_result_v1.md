# Dennis Risk Agent × DataAgent 自动同步闭环 POC 结果

## 1. POC 目标

验证 Dennis Risk Agent 子 Agent 是否能够在同一工作流中完成：

1. 识别需要取证；
2. 生成 DataAgent 只读取证问题；
3. 触发 DataAgent skill；
4. 接收 DataAgent 返回；
5. 区分 `provider_conclusion_hint` 与 `dennis_final_judgement`；
6. 对 `timeout / partial / no_permission / sql_only` 做降级处理；
7. 给出阶段性解释与下一步动作。

## 2. 测试链路

本次 POC 采用的链路为：

`用户问题 -> Dennis 子 Agent -> DataAgent skill -> DataAgent 返回 -> Dennis 子 Agent 解释 -> interim / final judgement`

核心验证点不在于是否“查到盗号定性”，而在于：

- 证据 provider 与最终裁判角色是否分离；
- 能否在返回后继续推理；
- 能否保持证据、提示、结论三层分离；
- 能否正确降级而不强判。

## 3. Test 1 结果：不调用 DataAgent 的 ATO 判断

### 结果

通过。

### 说明

当仅有用户自述、人工备注或粗粒度线索时，Dennis 子 Agent 能够：

- 明确指出证据不足；
- 识别还缺哪些关键链路；
- 输出下一步补证方向；
- 不把用户自述或人工备注当作事实。

### 结论

Test 1 说明：

- Dennis Agent 具备“先证据、后结论”的基本判断能力；
- 具备 ATO 场景下的边界控制；
- 可以在不调用 DataAgent 的情况下先做证据规划。

## 4. Test 2 结果：Dennis 子 Agent 成功触发 DataAgent

### 结果

通过。

### 说明

Dennis 子 Agent 能够把自然语言证据需求转成可执行的 DataAgent 问题，并成功触发 DataAgent skill。DataAgent 返回了真实登录链路、风控标签、拦截记录等信息。

### 结论

Test 2 说明：

- 子 Agent -> DataAgent 的同步触发链路成立；
- DataAgent 可以作为 evidence provider 工作；
- Dennis Agent 可以在返回后继续解释数据发现；
- 返回中存在的提示性结论没有覆盖 Dennis 主判断职责。

## 5. Test 3 结果：DataAgent 返回解释和 Dennis final judgement

### 结果

通过。

### 说明

DataAgent 返回后，Dennis 子 Agent 能够：

- 抽取 `data_findings`；
- 识别 `provider_conclusion_hint`；
- 保留缺失证据与反证；
- 生成自己的 `dennis_final_judgement`；
- 将阶段性结果保持在“高度疑似 Web 扫码类 ATO”，而不是直接升级为明确判断。

### 结论

Test 3 说明：

- `provider_conclusion_hint` 与 `dennis_final_judgement` 已分离；
- DataAgent 提示不会自动替代 Dennis 裁判；
- 当前 POC 可支持阶段性判断，但仍保留证据边界。

## 6. 当前已验证能力

1. Dennis 子 Agent 可以触发 DataAgent skill。
2. DataAgent 可以返回真实登录链路、风控标签、拦截记录。
3. Dennis 子 Agent 可以继续解释 DataAgent 返回。
4. `provider_conclusion_hint` 与 `dennis_final_judgement` 已分离。
5. 当前判断可以停留在“高度疑似 Web 扫码类 ATO”，不强行升级。
6. 对缺失证据、反证、权限限制能够保留降级空间。

## 7. 当前未验证或不支持能力

1. 不支持 DataAgent running / polling 的流式中间状态回调。
2. 不支持在一次 run 中自动暂停等待用户确认。
3. 不支持自动轮询剩余 SQL。
4. 不支持自动 SQL 修复重跑后的实时追踪。
5. 不支持结构化 audit trace。
6. DataAgent 的“只读 / evidence provider”主要仍是 prompt / policy 层约束，不是硬性技术隔离。

## 8. 关键边界是否成立

### 已成立

- DataAgent = evidence provider。
- Dennis = final judgement owner。
- timeout / partial / no_permission 需要降级。
- 不自动处罚 / 封禁 / 上线策略。

### 仍需注意

- DataAgent 只要返回的是执行计划、SQL-only 或不完整结果，就不能进入强证据链。
- 阶段性判断可以有，但必须清楚标注 interim。

## 9. 本次 POC 的 token / 耗时成本

- 运行时长约 7 分钟。
- token 成本约 139k。

### 成本感知

这说明当前链路可用，但运行态成本不低。成本主要来自：

- 过多运行态 MD 注入；
- 过长的历史 review / walkthrough；
- 过多重复证据边界文件；
- 多轮解释与回写上下文叠加。

## 10. 是否建议进入组内小范围试用

建议进入，但必须是**小范围、受控、只读**试用。

原因：

- 最小闭环已经验证；
- 证据 provider 与最终裁判已分离；
- 还未支持流式/多轮自动编排；
- 需要在真实使用中继续验证提示质量、路由稳定性和运行态成本。

