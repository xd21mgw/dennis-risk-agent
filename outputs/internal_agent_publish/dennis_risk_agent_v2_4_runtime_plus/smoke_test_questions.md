# Dennis Risk Agent v2.4 Runtime Plus Smoke Test Questions

## 1. 账号被盗了，怎么判断是不是协议上号？

- 期望命中的加载路径：ATO 完全体
- 是否允许 DataAgent：允许，但仅在用户明确要求查数时
- 合格回答标准：
  - 先识别为 ATO / 账号安全。
  - 说明判断框架：登录 / 授权 / 设备 / IP / UA / 地区 / token / session / 下游行为。
  - 不假装已查到数据。
- 不合格表现：
  - 只给空泛建议。
  - 直接默认查数。
  - 把 ATO 退化成轻量 summary。

## 2. 外网一直能跟价我们商品，但内部没看到异常流量，怎么排查？

- 期望命中的加载路径：anti_crawler_runtime_summary_v1
- 是否允许 DataAgent：默认不允许，除非用户明确要求查数
- 合格回答标准：
  - 给出攻击路径、证据优先级、误判点、治理建议、下一步排查。
  - 不默认进入 DataAgent。
- 不合格表现：
  - 直接查数。
  - 回答表面化。

## 3. 怎么判断一个攻击是单纯协议攻击？

- 期望命中的加载路径：protocol_attack_runtime_summary_v1
- 是否允许 DataAgent：默认不允许
- 合格回答标准：
  - 能区分协议攻击、群控、真人众包。
  - 包含判断证据和反证。
  - 给出低成本取证方向。
- 不合格表现：
  - 与反爬、群控混为一谈。
  - 直接调用 DataAgent。

## 4. 群控和真人众包怎么区分？

- 期望命中的加载路径：group_control + real_user_crowdsourcing runtime summaries
- 是否允许 DataAgent：默认不允许
- 合格回答标准：
  - 说明设备、行为、账号、任务链、成本结构的差异。
  - 讲清组织化调度 vs 任务化真人执行。
- 不合格表现：
  - 只讲“很多设备/很多真人”。
  - 直接查数。

## 5. 裂变拉新怎么判断黑产假量？

- 期望命中的加载路径：activity_anti_cheating_runtime_summary_v1
- 是否允许 DataAgent：默认不允许
- 合格回答标准：
  - 包含活动链路拆解、黑产动机、证据优先级、误判点、治理动作。
  - 只有用户明确要求查数时才给 DataAgent / Hive 方向。
- 不合格表现：
  - 默认查数。
  - 只讲“加强监控”。

