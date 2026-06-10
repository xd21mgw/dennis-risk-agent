# Source Field Recon Report - 2026-06-09 v0.1

## 定位

本报告是 normal_baseline v0.1 Stage A：离线字段侦察的产出。

5 个 Excel 是字段侦察输入，不是正式 normal baseline 结果。
本报告只读取 Excel、分析字段结构、产出 recon 资产；
不访问真实平台，不调用 DataAgent/Hive，不刷新 outputs，不提交 git，
不接入 Dennis runtime，不修改原始 Excel，不把 Excel 明细内容复制进报告。

## 输入 Excel 清单

| # | 文件名 | Sheet 数 | 主 sheet 行数 | 主 sheet 列数 | Source ID |
|---|---|---|---|---|---|
| 1 | 四表常见action关联离线表schema_副本.xlsx | 1 | 83 | 7 | schema_reference |
| 2 | android weapon基线样例～1000_副本.xlsx | 2 | ~1000 | 12 | weapon_android |
| 3 | IOSweapon样例～1000条_副本.xlsx | 2 | ~1000 | 12 | weapon_ios |
| 4 | 档案中心用户分析基线样例～1000 _副本.xlsx | 2 | ~1000 | 17 | passport_action_log |
| 5 | 统一登陆日志样例～1000条_副本.xlsx | 2 | ~1000 | 34 | infra_user_action_log |

每个 Excel 的 info sheet 为空，只有 sheet1 有数据。

---

## Source 1: infra_user_action_log（统一登陆日志）

**Hive 表**：`ks_raw_log_v3.infra_user_action_log`

### 概述

- 34 个普通列字段（不含分区字段）
- 2 个分区字段：`p_date` (STRING)、`p_hourmin` (STRING)
- 约 1000 条样本，时间窗口 p_date=20260609，p_hourmin=1200

### 字段形态摘要

| 字段 | 覆盖率 | 唯一值数 | 字段分类 | profiler_action | 说明 |
|---|---|---|---|---|---|
| p_date | 100% | 1 | partition | keep_as_condition_field | 时间分区，全量 20260609 |
| p_hourmin | 100% | 1 | partition | keep_as_condition_field | 小时分钟分区，全量 1200 |
| server_ip | 100% | 109 | ordinary_column | direct_profile | 服务端 IP |
| action_type | 100% | 11 | ordinary_column | direct_profile | 用户行为类型：REFRESH_TOKEN / CREATE_SERVICE_TOKEN / VISITOR_LOGIN / PASSTOKEN_LOGIN / GET_SAFE_PASSWORD / GET_PROFILE / GET_SMS_CODE / SNS_LOGIN / SMS_LOGIN / PWD_LOGIN / QUICK_LOGIN |
| app_type | 96.9% | 8 | ordinary_column | direct_profile | 业务类型：KUAISHOU_APP / UNRECOGNIZED / KUAISHOU_KY / KUAISHOU_SHOP_CS 等 |
| user_id | 83.8% | 838 | high_cardinality_id | high_cardinality_summary | 用户 ID，高基数，~3.1% null（VISITOR_LOGIN 无 user_id） |
| result | 100% | 2 | ordinary_column | direct_profile | 登录结果 True/False |
| user_ip | 44.2% | 440 | high_cardinality_id | high_cardinality_summary | 用户 IP，高基数，55.8% null |
| user_agent | 100% | 126 | ordinary_column | direct_profile | 用户代理字符串 |
| did | 99.6% | 994 | high_cardinality_id | high_cardinality_summary | 设备 ID，高基数 |
| date_time | 100% | 868 | timestamp | keep_as_condition_field | 日期时间字符串 |
| uri | 100% | 23 | ordinary_column | direct_profile | 请求 path |
| reason | 67.6% | 16 | ordinary_column | direct_profile | 失败/场景原因：HOT_START / COLD_START / UNKNOWN 等 |
| app_ver | 80.8% | 139 | ordinary_column | direct_profile | App 版本号 |
| extra | 100% | 721 | json_string | json_parse | JSON 格式，含 serviceToken / extra 等嵌套；22.5% 为空 {} |
| timestamp | 100% | 1000 | timestamp | keep_as_condition_field | 时间戳（毫秒） |
| sid | 96.4% | 37 | ordinary_column | direct_profile | 业务 SID |
| soft_did | 0.3% | 1 | ordinary_column | skip_for_v0_1 | 几乎全 null |
| token_id | 81.2% | 39 | ordinary_column | direct_profile | 登录态 Token ID，风控使用 |
| antispam_result | 1.3% | 13 | json_string | skip_for_v0_1 | 风控结果 JSON，98.7% null |
| exception_detail | 20.8% | 12 | ordinary_column | direct_profile | 异常详情 |
| user_ip_v6 | 37.0% | 370 | high_cardinality_id | high_cardinality_summary | IPv6 地址，63% null |
| sys | 15.2% | 27 | ordinary_column | direct_profile | 系统版本：ANDROID_12 等 |
| operation | 0.4% | 2 | ordinary_column | skip_for_v0_1 | 登录/注册类型，99.6% null |
| mod | 70.8% | 403 | ordinary_column | direct_profile | 机型 |
| operation_type | 0.2% | 1 | ordinary_column | skip_for_v0_1 | 操作类型，99.8% null |
| gps_location | 0% | 0 | unknown | skip_for_v0_1 | 全 null |
| ip_location | 0% | 0 | unknown | skip_for_v0_1 | 全 null |
| country_code | 0% | 0 | unknown | skip_for_v0_1 | 全 null |
| gps_raw_data | 0% | 0 | unknown | skip_for_v0_1 | 全 null |
| channel | 14.7% | 39 | ordinary_column | direct_profile | 渠道 |
| original_sid | 0.8% | 1 | ordinary_column | skip_for_v0_1 | 初始化 SID，99.2% null |
| ks_request_source | 0.7% | 1 | ordinary_column | skip_for_v0_1 | 网页端来源，99.3% null |
| account_identifier_md5 | 0.7% | 7 | high_cardinality_id | high_cardinality_summary | MD5 哈希，99.3% null |

### extra 字段解析

infra_user_action_log 的 `extra` 字段结构：
- 22.5% 为空 JSON `{}`
- 77.5% 含 JSON 内容
- 顶层 key 只有 2 种：`extra`、`serviceToken`
- `serviceToken` 内含嵌套 JSON：`basicToken`（含 userId / did / createTime / nonce / sid / verifiedFlag 等）
- `extra` 内含双重转义 JSON（`\\"`），包含完整的 clientRequestInfo（约 50+ key）

### 关键发现

1. **infra_user_action_log 不包含 userRegisterDays / userFanCnt / loginType / _errorCode 作为普通列或 extra 内字段**。这四个字段在当前 1000 条样本中未出现。
2. LOGIN_AUE 场景的筛选条件（loginType=52 / _errorCode=1 / userRegisterDays>200 / userFanCnt>200）在 infra_user_action_log 中不直接存在。
3. `action_type` 可间接表达登录方式：PASSTOKEN_LOGIN / SMS_LOGIN / PWD_LOGIN / QUICK_LOGIN / SNS_LOGIN / VISITOR_LOGIN 等，但没有 loginType=52（运营商一键登录）的编码。
4. `result` 字段表达登录成功/失败，但不是 _errorCode=1 的精确编码。
5. **infra_user_action_log 适合作为第一批 normal baseline 主 source，但需要补充 LOGIN_AUE 场景的筛选条件映射**。

### LOGIN_AUE 筛选条件映射分析

| 筛选条件 | infra 中是否存在 | 可能替代 | 说明 |
|---|---|---|---|
| loginType = 52 | ❌ 不存在 | action_type ≈ PASSTOKEN_LOGIN 或 QUICK_LOGIN | 需确认运营商一键登录的 action_type |
| _errorCode = 1 | ❌ 不存在 | result = True | result=True 大致等价于登录成功，但不是精确 _errorCode |
| userRegisterDays > 200 | ❌ 不存在 | 需从 passport_action_log 或档案中心关联 | infra 本身不含注册天数 |
| userFanCnt > 200 | ❌ 不存在 | 需从档案中心用户画像关联 | infra 本身不含粉丝数 |

---

## Source 2: passport_action_log（档案中心用户分析）

**Hive 表**：`ks_raw_log_v3.passport_action_log`

### 概述

- 17 个字段（含 2 个分区字段）
- 约 1000 条样本
- 注意：档案中心只有 APP 相关数据，小时分区 p_hourmin 全是 0000

### 字段形态摘要

| 字段 | 覆盖率 | 唯一值数 | 字段分类 | profiler_action | 说明 |
|---|---|---|---|---|---|
| p_date | 100% | 1 | partition | keep_as_condition_field | 全量 20260609 |
| p_hourmin | 100% | 1 | partition | keep_as_condition_field | 全量 0（小时分区不精确） |
| user_id | 100% | 1000 | high_cardinality_id | high_cardinality_summary | 用户 ID，每行不同 |
| timestamp | 100% | 1000 | timestamp | keep_as_condition_field | 时间戳（毫秒） |
| device_id | 100% | 1000 | high_cardinality_id | high_cardinality_summary | 设备 ID |
| user_ip | 100% | 568 | high_cardinality_id | high_cardinality_summary | 用户 IP（含 0.0.0.0） |
| server_ip | 100% | 104 | ordinary_column | direct_profile | 服务端 IP（含域名和内网 IP） |
| sys_ver | 100% | 88 | ordinary_column | direct_profile | 系统版本（浮点数） |
| app_ver | 100% | 135 | ordinary_column | direct_profile | App 版本号 |
| uri | 100% | 82 | ordinary_column | direct_profile | 请求 URI |
| status | 100% | 28 | ordinary_column | direct_profile | 状态码（20107 成功 / 1 / 110 / 705 等） |
| phone_mod | 99.7% | 412 | ordinary_column | direct_profile | 手机机型（品牌+型号） |
| params | 100% | 968 | json_string | json_parse | 60~66 key 的 JSON，含大量设备/请求/客户端信息 |
| extra | 100% | 979 | json_string | json_parse | JSON，含 tokenId / clientPageCode 等 |
| ks_log_id | 100% | 1000 | high_cardinality_id | high_cardinality_summary | 日志 ID |
| remote_port | 96.5% | 962 | ordinary_column | skip_for_v0_1 | 远端端口 |
| user_ipv6 | 43.4% | 434 | high_cardinality_id | high_cardinality_summary | IPv6，含二进制乱码 |

### params 字段解析

passport_action_log 的 `params` 字段：
- 每行含 47~66 个 key 的 JSON 对象
- 所有 key 的 value 都是 array 形式（如 `["2"]`、`["CUCC"]`）
- 100 行中发现 110 个唯一 key
- 主要 key 分类：
  - **设备信息**：oDid / boardPlatform / android_os / androidApiLevel / deviceBit / device_abi / abi / socName / ddpi / sw / sh / max_memory / totalMemory
  - **网络信息**：isp / net / language / country_code
  - **客户端信息**：app / kpf / kpn / bottom_navigation / browseType / grant_browse_type / is_background / darkMode / earphoneMode
  - **安全/反爬信息**：egid / __NS_xfalcon / __NStokensig / __NS_sig3 / sig / client_key / keyconfig_state / cdid_tag / did_tag / did_gt
  - **用户信息**：user_name / mobile / mobileCountryCode / passport_account_image
  - **渠道信息**：oc / c / newOc / channel
  - **登录/验证信息**：type / needCheck / requestSource / forceLogout / forceUnique / captcha_token / bindNewMobileType / code / confirm
  - **热修复/版本**：hotfix_ver / bundleVersionCode / ftt
  - **视频/社交**：videoModelCrowdTag / icaver / isAIHead / useVoice
  - **时间**：cold_launch_time_ms

### 关键发现

1. **passport_action_log 的 params 包含远比 infra_user_action_log 更丰富的客户端设备信息**，是 LOGIN_AUE 场景的核心字段来源。
2. params 中不含 userRegisterDays / userFanCnt / loginType / _errorCode 作为显式 key。
3. params 中有 `type` 字段（如 `["27"]`），可能对应 loginType 编码，需要进一步确认。
4. params 中有 `needCheck`（如 `["false"]`），可能与登录验证成功相关。
5. passport_action_log 需要进一步限定 APP 相关过滤条件：uri / status / params.type 等字段可用于筛选 LOGIN_AUE 场景的子集。

---

## Source 3: weapon_android（Weapon Android 设备指纹）

**Hive 表**：`ks_rc_bs.weapon_data_report_device_log_kafka_2_hive_android_di_v2`

### 概述

- 12 个普通列（含 1 个分区字段）
- 约 1000 条样本，p_date=20260609
- 核心字段：deviceid + raw_data（159~160 key JSON）+ weapon_one_risk

### 字段形态摘要

| 字段 | 覆盖率 | 唯一值数 | 字段分类 | profiler_action | 说明 |
|---|---|---|---|---|---|
| p_date | 100% | 1 | partition | keep_as_condition_field | 时间分区 |
| deviceid | 100% | 1000 | high_cardinality_id | high_cardinality_summary | ANDROID_ 前缀设备 ID |
| product | 100% | 2 | ordinary_column | direct_profile | APP 产品：NEBULA / KUAISHOU |
| async_status | 100% | 1 | ordinary_column | skip_for_v0_1 | 指纹状态，全量 SUCCESS |
| server_time | 100% | 991 | timestamp | keep_as_condition_field | 服务端时间 |
| client_time | 100% | 1000 | timestamp | keep_as_condition_field | 客户端时间 |
| sdk_version | 100% | 28 | ordinary_column | direct_profile | SDK 版本 |
| user_id | 100% | 888 | high_cardinality_id | high_cardinality_summary | 用户 ID |
| app_version | 100% | 134 | ordinary_column | direct_profile | App 版本号 |
| raw_data | 100% | 1000 | json_string | json_parse | **核心字段**：159~160 key 的设备指纹 JSON |
| one_data_version | 100% | 1 | ordinary_column | skip_for_v0_1 | 服务端版本，全量 2 |
| weapon_one_risk | 100% | 45 | array | array_normalize | 设备风险标签数组 |

### raw_data 字段解析

Android raw_data 是 normal_baseline profiler 最重要的 JSON 字段来源：
- 每条含 159~160 个 key
- key 覆盖率：前 30 个 key 在 100 行中 100% 出现（appVersion / ps / signVersion / deviceId / buildBootloader / sdkVersion 等）
- 关键子结构：
  - **设备标识**：deviceId / androidId / xm1 / xm3 / oaid / imei / ifaaId / soterId / vendorUniqueId / localId
  - **设备环境**：model / brand / resolution / apiLevel / hardware / buildFingerprint / buildDisplayRom / buildBoard / cpuKernel / cpuCore / battery / batteryTemperature
  - **网络信息**：wifiIp / networkLink / networkCardType / sourceIpv6 / sourceIp
  - **安全信息**：accessibilitySvc / installAccessibility / enabledAccessibilityServiceList / proxyV2 / rootCheck / isRoot / isEmulator
  - **应用信息**：appLaunchCount / appVersion / apkPath / apkSignature / apkProfile / apkExistCode / appInfo
  - **加密/签名**：signVersion / secretKeyVersion / headerKsId / weaponDecodeHeader
  - **嵌套 JSON**：vendorSecHw / vendorIds / trafficInfo / cookies / oneIpInfo / query / weaponRisk
  - **高基数 ID**：xm1 / xm3 / androidId / oaid / imei / headerKsId / vendorUniqueId 等

### weapon_one_risk 字段解析

weapon_one_risk 是 JSON 数组（可为空 `[]`）：
- 627/1000 条为空数组 `[]`
- 373/1000 条含风险标签
- 标签分布 TOP：
  - oneRiskMeetingTool: 138
  - oneRiskNoSim: 103
  - oneRiskUserAppCntLess10: 55
  - oneRiskOnlineLoan: 51
  - oneRiskLaunchLess10: 41
  - oneRiskBatteryZero: 14
  - oneRiskAutoScript: 12
  - oneRiskClickPlugin: 7
  - oneRiskIpIDC: 6
  - oneRiskAccSvcAbilityCnt: 5
  - 共 22 种不同标签

**⚠️ weapon_one_risk 是风险标签，不是 normal baseline 的统计对象。**
normal_baseline 只记录它的覆盖率、缺失率、TOP-N 分布等客观统计，
不解释标签含义、不做风险定性、不做候选特征推荐。

### 高基数字段

Android raw_data 中以下字段需做高基数摘要，不做全量展开：
- deviceId / xm1 / xm3 / androidId / oaid / imei / headerKsId / vendorUniqueId
- sourceIp / wifiIp
- user_id（普通列）

---

## Source 4: weapon_ios（Weapon iOS 设备指纹）

**Hive 表**：`ks_rc_bs.weapon_data_report_device_log_kafka_2_hive_ios_di_v2`

### 概述

- 12 个普通列（含 1 个分区字段）
- 约 1000 条样本
- 核心字段：deviceid + raw_data（164~165 key JSON）+ weapon_one_risk

### 字段形态摘要

iOS 普通列与 Android 相同结构：deviceid / product / async_status / server_time / client_time / sdk_version / user_id / app_version / raw_data / one_data_version / weapon_one_risk / p_date

差异点：
- iOS deviceid 格式为 UUID（如 `107C1107-9E7A-4614-AC99-A2588E0EA983`），不带 ANDROID_ 前缀
- iOS sdk_version 只有 16 种（Android 有 28 种）
- iOS app_version 只有 69 种（Android 有 134 种）
- iOS user_id 有 982 distinct（Android 有 888）

### raw_data 字段解析

iOS raw_data 与 Android raw_data 存在显著差异：
- **总 key 数**：iOS 165 vs Android 160
- **重叠 key**：40 个（约 24%）
- **Android-only key**：120 个
- **iOS-only key**：125 个

重叠 key（Android 和 iOS 都有）：
appInitTime / appKey / appLaunchCount / appVersion / asyncStatus / cookies / deviceId / dpi / kas / kaw / localId / mac / model / networkOperator / networkType / oneDataVersion / oneIpInfo / osVersion / platform / product / query / requestUri / resolution / sdkVersion / secretKeyVersion / serverIp / servertime / signVersion / sourceIp / sourceIpv6 / timestamp / weaponDecodeHeader / weaponPlatform / weaponRisk / xm1 等

Android-only key 代表：
accessibilityServiceList / accessibilitySvc / activityReferrer / adbStatus / alarminfo / androidId / anonyMemory / apiLevel / apkPath / apkProfile / apkSignature / appComponentFactory / battery / batteryTemperature / bootCount / bootId / brand / buildBoard / buildBootloader / buildDisplayRom / buildFingerprint / cpuKernel 等（120 个）

iOS-only key 代表：
activeMem / appInstallTime / appInstallTime2 / backgroundCount / biometric / bootHashId / broadcastAddress / bssid / caidTime / clientIP / cpuCoreCount / developerId / deviceModel / deviceName / deviceName2 / diskFree / diskSpace / dns / gateWay / hardwareType / hwActivecpu / hwAvailcpu / hwCpusubtype / idfv / idfv / kernOsproductversion / kernSecureKernel / kernSavedIds 等（125 个）

### iOS 特有高基数字段

iOS raw_data 中以下字段需做高基数摘要：
- deviceId / xm1 / xm3 / idfv / idfa（iOS 特有）
- sourceIp / clientIP / clientIp
- user_id（普通列）

### weapon_one_risk iOS

- 906/1000 条为空数组 `[]`
- 94/1000 条含风险标签
- 标签分布 TOP：
  - oneRiskNoPasswordIos: 41
  - oneRiskNoSimCardIos: 25
  - oneRiskLaunchLess10Ios: 16
  - oneRiskFirstLaunchIos: 10
  - oneRiskRefresh_12Day: 8
  - oneRiskApkInstall_5M: 5
  - oneRiskIpIDC: 4
  - 共 8 种不同标签（iOS 标签少于 Android）

---

## Source 5: 四表 Schema Reference（schema_reference）

**内容**：4 个 Hive 表的 schema 定义

### 4 个表的 schema

#### 表 1: weapon_android（12 字段）
p_date / deviceid / product / async_status / server_time / client_time / sdk_version / user_id / app_version / raw_data / one_data_version / weapon_one_risk

#### 表 2: weapon_ios（12 字段）
p_date / deviceid / product / async_status / server_time / client_time / sdk_version / user_id / app_version / raw_data / one_data_version / weapon_one_risk

#### 表 3: passport_action_log（17 字段）
p_date / p_hourmin / user_id / timestamp / device_id / user_ip / server_ip / sys_ver / app_ver / uri / status / phone_mod / params / extra / ks_log_id / remote_port / user_ipv6

#### 表 4: infra_user_action_log（34 字段）
p_date / p_hourmin / server_ip / action_type / app_type / user_id / result / user_ip / user_agent / did / date_time / uri / reason / app_ver / extra / timestamp / sid / soft_did / token_id / antispam_result / exception_detail / user_ip_v6 / sys / operation / mod / operation_type / gps_location / ip_location / country_code / gps_raw_data / channel / original_sid / ks_request_source / account_identifier_md5

---

## raw_data 解析建议

### Weapon raw_data

raw_data 是设备指纹核心 JSON，profiler 需要：

1. **json_parse**：递归展开所有 key，生成 `field_path = weapon_android.raw_data.{key}` 或 `weapon_ios.raw_data.{key}`
2. **嵌套 JSON 处理**：raw_data 内含嵌套 JSON 字段（vendorSecHw / vendorIds / trafficInfo / cookies / oneIpInfo / query / weaponRisk / weaponDecodeHeader），需二级展开
3. **高基数字段摘要**：xm1 / xm3 / androidId / oaid / imei / idfv / idfa / headerKsId / deviceId / sourceIp / wifiIp / vendorUniqueId 等不做全量 TOP-N，只做 distinct/unique/reuse 摘要
4. **凭证字段跳过**：headerKsId / signVersion / secretKeyVersion / __NS_xfalcon / __NStokensig / __NS_sig3 / sig / client_key 等签名/加密字段，v0.1 建议标记为 `skip_for_v0_1` 或只做覆盖率统计
5. **Android/iOS 分开处理**：两个平台的 raw_data key 差异巨大（只有 40 个重叠 key），必须分开 profile

### weapon_one_risk

weapon_one_risk 是风险标签数组：
- profiler 只做 `array_normalize`：统计覆盖率、标签 TOP-N 分布、空数组比例
- **不做风险定性**
- **不做候选特征推荐**
- 标签名称只是客观统计对象

---

## infra_user_action_log 是否适合作为第一批 normal baseline 主 source

**结论：适合作为第一批 normal baseline 主 source，但需补充 LOGIN_AUE 筛选条件映射。**

理由：
1. infra_user_action_log 是统一登陆日志，覆盖所有登录/刷新/验证行为，是 LOGIN_AUE 场景的天然数据源。
2. 34 个字段中，大部分是普通列（不需要 JSON 解析），profiler 处理成本最低。
3. `extra` 字段虽然含嵌套 JSON，但结构相对稳定（只有 serviceToken / extra 两种顶层 key）。
4. 核心筛选字段（action_type / result / app_type）已是普通列，可直接 SQL 过滤。
5. **缺失**：loginType / _errorCode / userRegisterDays / userFanCnt 在 infra 中不直接存在，需从 passport_action_log params 或档案中心关联补充。

**第一批 normal baseline 建议用 infra_user_action_log + passport_action_log 联合取样**，而非只用 infra 单表。

---

## passport_action_log 是否需要进一步限定 APP 过滤字段

**结论：需要进一步限定 APP 过滤字段。**

理由：
1. passport_action_log 的 `uri` 字段有 82 种不同值，包含大量非 LOGIN_AUE 场景的 URI（如 modifyProfileBG / changeOption / set 等）。
2. `status` 字段有 28 种不同值，包含非登录成功的状态码。
3. `params.type` 可能对应 loginType 编码，需要确认 type=27 是否等价于 loginType=52。
4. passport_action_log 的 `params` 包含最丰富的设备/客户端信息（60~66 key），是 normal baseline 字段发现的核心来源。
5. **APP 过滤建议**：
   - uri 过滤：只取 `/rest/n/user/login/` 或 `/rest/nebula/user/login/` 开头的 URI
   - status 过滤：只取 status=1 或 status=20107（登录成功）
   - params.type 过滤：只取 type=27 或其他对应运营商一键登录的编码
   - 注意：档案中心只有 APP 相关数据，已天然过滤掉非 APP 数据

---

## profiler_input_contract 草案摘要

profiler_input_contract 定义了 4 个 source 的输入格式、字段分类和 profiler 处理策略：

1. **infra_user_action_log**：34 字段，27 个普通列 + 1 个 JSON（extra）+ 2 个分区 + 4 个高基数 ID + 1 个 timestamp
2. **passport_action_log**：17 字段，12 个普通列 + 2 个 JSON（params/extra）+ 2 个分区 + 4 个高基数 ID + 1 个 timestamp
3. **weapon_android**：12 字段，8 个普通列 + 1 个 JSON（raw_data，159~160 key）+ 1 个 array（weapon_one_risk）+ 1 个分区 + 2 个 timestamp + 2 个高基数 ID
4. **weapon_ios**：12 字段，8 个普通列 + 1 个 JSON（raw_data，164~165 key）+ 1 个 array（weapon_one_risk）+ 1 个分区 + 2 个 timestamp + 2 个高基数 ID

profiler_action 分布：
- direct_profile：约 30 个字段（普通列的离散/枚举字段）
- json_parse：3 个字段（infra.extra / passport.params / passport.extra / weapon.raw_data）
- array_normalize：2 个字段（weapon.weapon_one_risk Android/iOS）
- high_cardinality_summary：约 10 个字段（user_id / device_id / did / user_ip / xm1 / xm3 等）
- keep_as_condition_field：约 6 个字段（p_date / p_hourmin / timestamp / date_time 等）
- skip_for_v0_1：约 10 个字段（覆盖率 <5% 的字段、凭证字段、全量常量字段）
- deferred_due_to_cost：0（v0.1 不标记）

---

## 不做的事

- 不做风险判断
- 不输出 risk_judgement
- 不输出 feature_candidate
- 不输出 candidate_feature_decision
- 不做人审结论
- 不新增 compare / cognition / risk_candidate / feature_candidate / automatic entity expansion 目录
- 不修改原始 Excel
- 不把 Excel 明细内容复制进报告