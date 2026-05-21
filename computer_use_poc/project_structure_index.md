# Project Structure Index

本文是 Dennis Risk Agent 当前仓库的轻量目录索引，用于区分主入口、能力文档、历史过程文件和 release 产物。

## 1. 推荐主入口

| 路径 | 定位 | 使用方式 |
|---|---|---|
| `README.md` | 仓库总入口 | 了解项目背景、核心能力和顶层说明 |
| `computer_use_poc/README.md` | computer_use_poc 阶段主入口 | 当前 POC、只读手脚、安全框架、体验优先和阶段状态 |
| `computer_use_poc/capability_registry.md` | 能力注册表 | 按 capability 理解当前正式能力，不按平台硬记 |
| `computer_use_poc/scene_to_capability_routing.md` | 场景到能力路由 | 看账号安全、ATO、设备风险、策略命中、批量分析如何拆能力 |
| `computer_use_poc/smoke_tests.md` | 回归测试清单 | 查能力、路由、安全、Plan、体验等文档级测试覆盖 |
| `computer_use_poc/project_structure_index.md` | 目录说明 | 新接手项目时先看，用于定位文件角色 |

## 2. 核心目录定位

| 目录 / 文件 | 定位 | 主入口或历史过程 | 备注 |
|---|---|---|---|
| `README.md` | 仓库级说明 | 主入口 | 项目总说明 |
| `skills/` | Dennis 风控专家认知 Skill | 主能力资产 | v2.1 大脑提示词、边界矩阵、rubric 和业务 Skill |
| `computer_use_poc/` | 内部平台只读手脚、路由、安全和体验沉淀 | 当前主要工作区 | 新增能力文档优先放这里 |
| `computer_use_poc/run_logs/` | 实验、回归、dry-run 过程记录 | 历史过程文件 + 证据记录 | 不移动、不删除；按文件名查版本和 run |
| `computer_use_poc/observations/` | observation 样例 | 过程/样例数据 | 用于 schema 和回答样例，不等于实时数据 |
| `outputs/release/` | release package | 集成产物 | 不轻易重构；每个版本包保持历史结构 |
| `outputs/dist/` | 打包上传产物 | 发布产物 | 本轮目录治理不更新 |
| `outputs/intermediate/` | 中间状态、runtime snapshot、计划草案 | 过程文件 | 用于追溯阶段状态，不作为唯一入口 |
| `outputs/final/` | final manifest / release snapshot | 发布说明 | 不覆盖旧版本 |
| `eval/` | 测试集与黄金期望 | 评测资产 | v2.2 50 case 和 golden rules |

## 3. computer_use_poc 内部常用文件

| 文件 | 定位 |
|---|---|
| `capability_registry.md` | 按 capability 列出正式能力、brain capability、安全字段 |
| `scene_to_capability_routing.md` | 体验优先、Plan / execution、安全路由和半开放状态 |
| `answer_experience_templates.md` | 风险研判、原因解释、实体关系查询等回答模板 |
| `user_experience_golden_cases.md` | 体验黄金 Case |
| `plan_mode_capability_v1.md` | Plan 模式能力定义 |
| `security_preflight_coverage_matrix.md` | Agent Safety / Security Preflight 当前覆盖矩阵 |
| `security_preflight_policy.yaml` | 结构化 preflight policy |
| `security_preflight_evaluator.py` | 本地 preflight evaluator dry-run |
| `security_preflight_tool_call_request_contract.md` | tool_call_request 字段契约 |

## 4. 历史过程文件处理原则

- 不移动历史 `run_logs`。
- 不删除历史 POC 文件。
- 不把旧版本 release 目录重构成新格式。
- 新能力优先新增索引、registry、routing 和 smoke tests，减少对历史过程文件的破坏。
- 若历史文件口径与当前入口冲突，以 `README.md`、`computer_use_poc/README.md`、`capability_registry.md`、`scene_to_capability_routing.md` 和最新 run log 为准。

## 5. 新人阅读顺序

1. `README.md`
2. `computer_use_poc/README.md`
3. `computer_use_poc/project_structure_index.md`
4. `computer_use_poc/capability_registry.md`
5. `computer_use_poc/scene_to_capability_routing.md`
6. `computer_use_poc/smoke_tests.md`
7. 需要追溯时再看 `computer_use_poc/run_logs/`、`outputs/release/`、`outputs/intermediate/`。
