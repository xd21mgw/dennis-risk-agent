# ATO 盗号样本台账: Huawei QuickLogin / Xiaomi Reset 2026-05-20

## 1. Sample Set

- sample_set_id: `ato_huawei_quicklogin_xiaomi_reset_20260520`
- sample_set_type: `ato`
- case_table_status: `pending_observation`
- readonly_only: true
- dataagent_called: false
- platform_query_executed: false
- release_package_updated: false

## 2. Known Hypothesis

当前样本集的待验证假设链路：

HUAWEI / Harmony quickLogin 或 token 登录  
→ `login_type=16`  
→ Xiaomi(MI 8 Lite)  
→ `/rest/n/user/reset/byToken/logined`  
→ `reset_login_type=99`

ATO 主线口径：

- 核心不是“机型切换”本身，而是登录态 / token / quickLogin 链路是否存在异常复用或账号控制权变化。
- `HUAWEI / Harmony` 到 `Xiaomi(MI 8 Lite)` 的链路只是一条候选异常路径，需要真实只读 observation 验证。
- `/rest/n/user/reset/byToken/logined` 与 `reset_login_type=99` 只能作为重置链路候选证据，不代表已确认盗号。
- 当前样本台账不包含真实 observation，不输出 ATO 结论。

## 3. Batch Input Consistency Check

batch_input_consistency_check:

- total_cases: 20
- unique_user_count: 20
- all_p_date: 20260520
- initial_login_type_all: 16
- reset_login_type_all: 99
- reset_phone_model_all: Xiaomi(MI 8 Lite)
- reset_path_all: `/rest/n/user/reset/byToken/logined`
- quickLogin_count: 11
- login_token_count: 9
- pending_user_id_count: 0

一致性结论：

- 20 条 case 均已写入真实样本 user_id。
- 初始登录类型均为 `16`。
- 重置登录类型均为 `99`。
- 重置机型均为 `Xiaomi(MI 8 Lite)`。
- 重置路径均为 `/rest/n/user/reset/byToken/logined`。
- 初始登录路径分布为 quickLogin 11 条、token 9 条。

## 4. 原始 20 个 user_id 列表

| index | user_id |
|---:|---:|
| 1 | 4910098437 |
| 2 | 5376326876 |
| 3 | 3635896641 |
| 4 | 4382576023 |
| 5 | 1705514992 |
| 6 | 4540329365 |
| 7 | 2384142803 |
| 8 | 237419164 |
| 9 | 5501335684 |
| 10 | 3469247246 |
| 11 | 5121621748 |
| 12 | 5439409930 |
| 13 | 628988198 |
| 14 | 2188497621 |
| 15 | 2678499885 |
| 16 | 2109589440 |
| 17 | 2810169785 |
| 18 | 2816963455 |
| 19 | 547061183 |
| 20 | 3101900624 |

## 5. Case Table / 样本台账

| case_id | p_date | user_id | initial_phone_model | initial_path | initial_login_type | reset_phone_model | reset_path | reset_login_type | case_status | evidence_quality | ato_chain_support_level |
|---|---:|---:|---|---|---:|---|---|---:|---|---|---|
| ato_001 | 20260520 | 4910098437 | HUAWEI(BLK-AL00) | `/rest/n/user/login/huawei/quickLogin` | 16 | Xiaomi(MI 8 Lite) | `/rest/n/user/reset/byToken/logined` | 99 | pending_observation | pending | pending |
| ato_002 | 20260520 | 5376326876 | HUAWEI(BLK-AL80) | `/rest/n/user/login/token` | 16 | Xiaomi(MI 8 Lite) | `/rest/n/user/reset/byToken/logined` | 99 | pending_observation | pending | pending |
| ato_003 | 20260520 | 3635896641 | HUAWEI(BLK-AL80) | `/rest/n/user/login/token` | 16 | Xiaomi(MI 8 Lite) | `/rest/n/user/reset/byToken/logined` | 99 | pending_observation | pending | pending |
| ato_004 | 20260520 | 4382576023 | HUAWEI(ADA-AL00U) | `/rest/n/user/login/huawei/quickLogin` | 16 | Xiaomi(MI 8 Lite) | `/rest/n/user/reset/byToken/logined` | 99 | pending_observation | pending | pending |
| ato_005 | 20260520 | 1705514992 | HUAWEI(BLK-AL80) | `/rest/n/user/login/token` | 16 | Xiaomi(MI 8 Lite) | `/rest/n/user/reset/byToken/logined` | 99 | pending_observation | pending | pending |
| ato_006 | 20260520 | 4540329365 | HUAWEI(BLK-AL80) | `/rest/n/user/login/huawei/quickLogin` | 16 | Xiaomi(MI 8 Lite) | `/rest/n/user/reset/byToken/logined` | 99 | pending_observation | pending | pending |
| ato_007 | 20260520 | 2384142803 | HUAWEI(BLK-AL80) | `/rest/n/user/login/token` | 16 | Xiaomi(MI 8 Lite) | `/rest/n/user/reset/byToken/logined` | 99 | pending_observation | pending | pending |
| ato_008 | 20260520 | 237419164 | HUAWEI(ADA-AL00U) | `/rest/n/user/login/token` | 16 | Xiaomi(MI 8 Lite) | `/rest/n/user/reset/byToken/logined` | 99 | pending_observation | pending | pending |
| ato_009 | 20260520 | 5501335684 | HUAWEI(BLK-AL80) | `/rest/n/user/login/huawei/quickLogin` | 16 | Xiaomi(MI 8 Lite) | `/rest/n/user/reset/byToken/logined` | 99 | pending_observation | pending | pending |
| ato_010 | 20260520 | 3469247246 | HUAWEI(BLK-AL80) | `/rest/n/user/login/huawei/quickLogin` | 16 | Xiaomi(MI 8 Lite) | `/rest/n/user/reset/byToken/logined` | 99 | pending_observation | pending | pending |
| ato_011 | 20260520 | 5121621748 | HUAWEI(ADA-AL00) | `/rest/n/user/login/huawei/quickLogin` | 16 | Xiaomi(MI 8 Lite) | `/rest/n/user/reset/byToken/logined` | 99 | pending_observation | pending | pending |
| ato_012 | 20260520 | 5439409930 | HUAWEI(BLK-AL80) | `/rest/n/user/login/token` | 16 | Xiaomi(MI 8 Lite) | `/rest/n/user/reset/byToken/logined` | 99 | pending_observation | pending | pending |
| ato_013 | 20260520 | 628988198 | HUAWEI(BLK-AL80) | `/rest/n/user/login/huawei/quickLogin` | 16 | Xiaomi(MI 8 Lite) | `/rest/n/user/reset/byToken/logined` | 99 | pending_observation | pending | pending |
| ato_014 | 20260520 | 2188497621 | HUAWEI(BLK-AL80) | `/rest/n/user/login/huawei/quickLogin` | 16 | Xiaomi(MI 8 Lite) | `/rest/n/user/reset/byToken/logined` | 99 | pending_observation | pending | pending |
| ato_015 | 20260520 | 2678499885 | HUAWEI(BLK-AL80) | `/rest/n/user/login/huawei/quickLogin` | 16 | Xiaomi(MI 8 Lite) | `/rest/n/user/reset/byToken/logined` | 99 | pending_observation | pending | pending |
| ato_016 | 20260520 | 2109589440 | HUAWEI(BLK-AL80) | `/rest/n/user/login/huawei/quickLogin` | 16 | Xiaomi(MI 8 Lite) | `/rest/n/user/reset/byToken/logined` | 99 | pending_observation | pending | pending |
| ato_017 | 20260520 | 2810169785 | HUAWEI(BLK-AL80) | `/rest/n/user/login/token` | 16 | Xiaomi(MI 8 Lite) | `/rest/n/user/reset/byToken/logined` | 99 | pending_observation | pending | pending |
| ato_018 | 20260520 | 2816963455 | HUAWEI(BLK-AL00) | `/rest/n/user/login/token` | 16 | Xiaomi(MI 8 Lite) | `/rest/n/user/reset/byToken/logined` | 99 | pending_observation | pending | pending |
| ato_019 | 20260520 | 547061183 | HUAWEI(BLK-AL80) | `/rest/n/user/login/token` | 16 | Xiaomi(MI 8 Lite) | `/rest/n/user/reset/byToken/logined` | 99 | pending_observation | pending | pending |
| ato_020 | 20260520 | 3101900624 | HUAWEI(BLK-AL80) | `/rest/n/user/login/huawei/quickLogin` | 16 | Xiaomi(MI 8 Lite) | `/rest/n/user/reset/byToken/logined` | 99 | pending_observation | pending | pending |

## 6. Evidence Boundary

当前所有 case 均为 `pending_observation`：

- 不代表已观察到 initial login。
- 不代表已观察到 reset event。
- 不代表 quickLogin / token login 与 reset event 已形成同一条 ATO 链路。
- 不代表 Xiaomi(MI 8 Lite) 是攻击设备。
- 不代表 `reset_login_type=99` 必然异常。

必须通过只读 observation 验证：

1. initial login 是否真实存在。
2. initial login 的 device / model / path / login_type 是否匹配。
3. reset event 是否真实存在。
4. reset event 的 device / model / path / reset_login_type 是否匹配。
5. 两个事件是否在时间、用户、token / session / device 关系上可连接。
6. 是否存在本人常用设备、正常找回流程、误报或平台字段解释差异等反证。
