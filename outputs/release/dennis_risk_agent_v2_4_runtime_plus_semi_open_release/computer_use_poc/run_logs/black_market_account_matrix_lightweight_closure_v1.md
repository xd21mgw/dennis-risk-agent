# Black Market Account Matrix Lightweight Closure v1

## 1. 当前状态

- sample_family: `black_market_account_matrix`
- closure_type: `lightweight_status_archive`
- current_priority: `pause_deep_dive_for_runtime_semi_open_test`
- completed_validation_scope: `15_case_pattern_validation`
- readonly_only: true
- dataagent_called: false
- platform_write_action: false
- release_package_updated: false

当前 black_market_account_matrix 支线已完成 15 case pattern validation，整体支持 `black_market_account_matrix` 假设。

形态判断：

- primary_shape: `单设备单账号分布式养号矩阵`
- secondary_shape: `导流小号矩阵`
- not_ato: true
- not_traditional_same_device_multi_account_group_control: true

该支线仍有较多本质链路待补，包括重置前资料、导流行为、注册生产链、行为对象聚集等。为避免拖慢内部半开放测试，本轮只做状态归档和 future work 标记。

## 2. 证据分层

### 2.1 前置证据

这些证据更接近账号生产、设备环境和批次化养号过程：

- 注册 IP cohort。
- 注册时间窗口集中。
- 设备环境异常。
- 单设备单账号形态。
- `BB4` / `WIFI157` 等 WiFi 命名规则。
- Weapon 机器小号 / 无 SIM / 启动次数低等设备侧线索。

证据解释：

- 单设备单账号不是低风险反证，也不是单独强风险证据。
- 在分布式养号矩阵中，1:1 设备配置可能是规避同设备聚集特征的形态。
- 前置证据需要和资料模板、行为链路、策略/处罚标签叠加解释。

### 2.2 后置结果

这些证据更接近平台治理后的结果或账号当前状态：

- 默认昵称。
- 空简介。
- 三层封禁。
- 昵称 / 头像 / 简介重置。
- actionBan。
- 社交封禁。

证据解释：

- 默认昵称和空简介本身不是强风险证据。
- 当前默认资料可能是治理后的 cleanup aftermath。
- 三层封禁 / 昵称重置 / actionBan 支持资料治理发生，但不能替代原始资料倒查。
- 需要 profile change history、adminaction reason、audit log、before/after diff 才能形成更强闭环。

## 3. 当前边界

- 不作为 ATO。
- 不作为当前半开放测试阻塞项。
- 不直接输出策略处置结论。
- 不自动封禁。
- 不自动上线策略。
- 不调用真实平台。
- 不调用 DataAgent。
- 不输出敏感明文。

与 ATO 的边界：

- ATO 是账号控制权异常，核心是凭证 / token / OAuth / 登录态异常、改密、换绑、异设备登录。
- black_market_account_matrix 是账号池 / 导流互动 / 养号矩阵归因，核心是账号生产、资料模板、设备/注册 cohort、行为对象聚集和导流链路。
- 不要把导流小号矩阵误写成盗号。

## 4. Future Work

| future_work | purpose | why_deferred |
|---|---|---|
| 重置前资料倒查 | 复原用户名 / 昵称 / 简介三层同构的原始状态 | 需要 profile history / audit log / before-after diff |
| 行为 / 导流链路补证 | 确认关注、点赞、评论、私信、导流对象是否聚集 | 行为链未触达，当前不能闭环 |
| 注册生产链 Hive 扩量 | 扩展注册 IP cohort、注册时间窗口、UID 号段、设备环境 | 需要 DataAgent / Hive，当前不调用 |
| 设备物理环境扩量 | 验证 BB4 / WIFI157 / 无 SIM / 低启动等设备环境模式规模 | 需要更大样本和设备侧批量聚合 |
| 策略候选规则卡 | 将资料模板、设备环境、注册 cohort、行为链路转成候选规则 | 需要误伤评估、灰度验证、查杀分离 |

## 5. 推荐状态

- pause_deep_dive: true
- keep_as_batch_analysis_followup: true
- not_blocking_runtime_semi_open_test: true
- recommended_next_focus: `internal_runtime_semi_open_test`

## 6. 关联材料

- `computer_use_poc/run_logs/black_market_account_matrix_5_case_observation_run_001.md`
- `computer_use_poc/run_logs/black_market_account_matrix_v2_targeted_rerun.md`
- `computer_use_poc/observation_templates/black_market_account_matrix_observation_template.yaml`
- `eval/dennis_risk_agent_skills_v2_2_tested/20_black_market_account_matrix_batch/`

本 closure 不合并历史 run log，不删除历史文件，不移动目录。
