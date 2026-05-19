# 设备攻防基建平台（风控攻防基建中心）

## 1. 平台一句话定位

设备攻防基建平台用于查询设备 SDK 指纹、设备真实性、风险标签、安装 APP、关联图谱和设备底层信息。

## 2. 平台能力边界

### 2.1 能查什么

- 设备基础信息：device_id、平台、用户、网络 IP、地理位置、APP 版本、SDK 版本、安装时间。
- 设备可信：硬件可信、真机验证、设备上报状态。
- 风险详情：设备风险类别、风险标签、描述、风险等级、APK 风险。
- 应用列表：全部/非系统/系统 APP、包名、安装时间。
- 关联图谱：用户扩散、设备扩散、网络扩散、关联用户和封禁用户数。
- 账号信息：账号状态、封禁、黑名单、粉丝、资料变更、风险标签。
- 设备信息：appLaunchCount、apkPath、safe_status、buildDisplayRom 等底层 SDK 指纹。

### 2.2 不能查什么

- 不适合查登录日志、OAuth、token、扫码、高危接口明细。
- 不适合查用户处罚和审核全量记录。
- 不适合查策略配置和特征命中明细。
- 不适合做离线大盘聚合。

### 2.3 应转向哪些平台

| 需求 | 应转向平台 |
|---|---|
| 登录方式 / token / OAuth / 扫码 | 用户登录统一日志 |
| 用户状态 / 审核 / 内容 / 举报 | 档案中心 |
| 策略命中和配置 | 天狮策略引擎 |
| 批量设备趋势 | DataAgent / Hive |
| 前端行为链路 | 用户行为细查平台 |

## 3. 典型查询对象

| 查询对象 | 输入方式 | 适用问题 | 注意事项 |
|---|---|---|---|
| deviceId | 搜索框，queryType=deviceId | 设备可信、风险标签、关联图谱 | 高敏查询，需工作必要 |
| product | URL 参数 | 产品线过滤 | 原文示例固定 KUAISHOU |
| user_id | 关联账号 Tab 跳转 | 查看该设备关联账号 | 用户粒度事实转档案中心 |
| network_ip | 基础信息区 / 图谱 | IP 聚集和网络扩散 | IP 噪声高 |

## 4. 页面 / 模块结构

| 页面模块 | 核心功能 | 关键字段 | 常用场景 | 优先级 |
|---|---|---|---|---|
| 搜索页 | 输入 deviceId 查询 | device_id, product | 设备风险入口 | P0 |
| 风险详情 | 风险标签、APK 风险、活跃信息 | risk_category, risk_label, apk_risk | 模拟器、刷机、破解包、设备风险 | P0 |
| 应用列表 | 设备安装 APP | app_name, app_package, app_install_time | 灰产工具、群控工具、多开器、VPN | P0 |
| 位置信息 | GPS 位置历史 | longitude_latitude | 地理漂移核查 | P2 |
| 关联图谱 | 用户/设备/网络扩散 | related_user_count, banned_user_count | 群控/号商/设备扩量 | P0 |
| 账号信息 | 关联账号画像和资料变更 | account_status, profile_changed, risk_label | 账号安全、社交风险、设备关联 | P1 |
| 设备信息 | SDK 底层指纹 | appLaunchCount, safe_status, apkPath | 模拟器、刷机、破解包、协议上号 | P0 |

## 5. 核心字段字典

| 字段名 | 页面展示名 | 含义 | 风控解释 | 适用场景 | 可信度/注意事项 |
|---|---|---|---|---|---|
| device_id | 设备ID | 设备唯一标识 | 核心锚点 | 设备风险、群控、账号安全 | 高可信 |
| network_ip | 网络信息 | 设备上报 IP | IP 聚集、代理、地理漂移 | 群控、协议上号、反爬 | IP 地理有误差 |
| ip_location | IP位置 | IP 地理位置 | 异地、境外、地区冲突 | 账号安全、设备风险 | 需交叉验证 |
| app_version | app版本 | 快手 APP 版本 | 低版本/异常版本线索 | 破解包、协议上号 | 不能单独定性 |
| risk_sdk_version | 风控SDK版本 | SDK 版本 | 旧版 SDK 可能信号缺失 | 设备风险 | 需确认版本口径 |
| app_install_time | app安装时间 | APP 安装时间 | 新安装、事件临近安装 | 账号安全、设备扩量 | 时间需对齐事件 |
| hardware_trusted | 硬件可信 | 设备硬件可信状态 | 不具备提示模拟器/刷机/硬件伪造 | 群控、破解包、设备风险 | 强线索，仍需结合 |
| real_device_verify | 真机验证 | 是否通过真机验证 | 未验证提示可疑 | 群控、设备风险 | 不是最终结论 |
| device_report_status | 设备上报 | SDK 上报状态 | 异常提示数据缺失或伪造 | 协议上号、破解包 | 需排除 SDK 问题 |
| risk_category | 类别 | 风险大类 | 快速定位设备风险类型 | 全设备风险 | 需读描述 |
| risk_label | 标签 | 具体设备风险标签 | 精细风险 tag | 设备风险、群控 | 具体标签不沉淀为本质规则 |
| risk_description | 描述 | 标签说明 | 理解标签本质和误伤 | 设备风险 | 高价值解释字段 |
| risk_level | 风险等级 | 客观事实/中/高风险 | 客观事实不等于风险 | 全场景 | 注意不要误判 |
| apk_risk | APK风险 | APK 风险状态 | 重打包/破解线索 | 破解包、协议上号 | 需工件证据 |
| app_package | 包名 | APP 包名 | 防止 APP 改名混淆 | 灰产工具、群控 | 高可信 |
| related_user_count | 关联用户数 | 设备关联用户量 | 大量关联提示群控/号商 | 群控、假量 | 关联不等于同伙 |
| banned_user_count | 封禁用户数 | 关联用户中封禁数 | 封禁比例高提示设备风险 | 群控、设备风险 | 需看样本量 |
| appLaunchCount | app启动计数器值 | APP 启动次数 | 极低可提示新设备/刷机/首次使用 | 账号安全、设备风险 | 具体阈值需业务校准 |
| apkPath | APK 安装路径 | 安装路径可信度 | 非标准路径提示重打包/破解 | 破解包 | 需端侧专家确认 |
| safe_status | 硬件可信状态值 | 硬件可信数值 | -1 等异常值提示风险 | 设备风险 | 取值字典需确认 |

## 6. 通用适用场景

- ATO / 账号安全：适用。查新设备、历史设备、设备可信、资料变更，ATO 是典型用例之一。
- 群控 / 号商：适用。查模拟器、设备图谱、关联用户、封禁比例。
- 协议上号：适用。查 SDK 上报异常、APK 风险、设备可信、重打包线索。
- 反爬 / 资产抓取：部分适用。查设备风险和批量设备，资产访问链路需其他平台。
- 内容风险：部分适用。查发布设备和账号状态，不覆盖内容审核本身。
- 假量 / 裂变：适用。查设备扩量、设备重置、同设备新账号。
- 社交骚扰：部分适用。查设备关联和账号封禁，具体私信评论需其他平台。
- 策略误伤 / 策略归因：部分适用。提供设备反证，策略归因转天狮。

## 7. 风险场景覆盖矩阵

| 风险场景 | 是否适用 | 适用方式 | 关键字段 / 模块 |
|---|---|---|---|
| ATO / 账号安全 | 适用 | 新设备、设备可信、资料变更 | appLaunchCount, app_install_time, profile_changed |
| 群控 / 号商 | 适用 | 设备图谱、模拟器、封禁比例 | 关联图谱, hardware_trusted, banned_user_count |
| 协议上号 | 适用 | APK 风险、SDK 异常、设备上报异常 | apk_risk, device_report_status, apkPath |
| 反爬 / 资产抓取 | 部分适用 | 批量设备和设备环境线索 | risk_label, app_package |
| 内容风险 | 部分适用 | 发布设备侧反证 | 账号信息, device_id |
| 假量 / 裂变 | 适用 | 设备重置、新设备、关联账号 | risk_category, recent_register_count |
| 社交骚扰 | 部分适用 | 社交封禁账号和设备聚集 | social_ban, account_status |
| 策略误伤 / 策略归因 | 部分适用 | 设备可信反证 | hardware_trusted, risk_description |

## 8. 典型查询路径

### 8.1 设备风险 / 异常登录设备核查

- 输入：device_id
- 查询模块：风险详情 → 设备信息 → 账号信息 → 应用列表
- 关键字段：hardware_trusted, real_device_verify, risk_label, appLaunchCount, app_install_time, safe_status
- 输出结论：设备是否新、是否可信、是否有模拟器/刷机/重打包/灰产 APP 线索
- 下一步平台：用户登录统一日志验证该设备是否参与登录/高危操作

### 8.2 群控 / 号商扩量

- 输入：device_id
- 查询模块：关联图谱 → 用户扩散 / 设备扩散 / 网络扩散
- 关键字段：related_user_count, banned_user_count, abnormal_status_count, expand_type
- 输出结论：设备团组规模、封禁比例、扩量方向
- 下一步平台：档案中心核验账号事实；风险运营中心做滚雪球和举报分析

### 8.3 破解包 / 协议上号设备侧排查

- 输入：device_id
- 查询模块：风险详情 → 应用列表 → 设备信息
- 关键字段：apk_risk, apkPath, signVersion, buildDisplayRom, device_report_status, risk_sdk_version
- 输出结论：是否存在端侧改造、SDK 异常、APK 风险线索
- 下一步平台：用户行为细查验证前端行为；用户登录统一日志验证后端登录

## 9. Agent 路由规则

- 问题包含“设备是否可信 / 模拟器 / 刷机 / 重打包 / 破解包 / 群控工具 / 关联图谱 / 设备扩量”时，优先查设备攻防。
- 问题从 user_id 开始但核心是设备风险时，先从档案中心拿 device_id，再转设备攻防。
- 问题涉及登录链路时，不要只看设备风险，应转用户登录统一日志。

## 10. Agent 解释规则

- `hardware_trusted=不具备`、`safe_status` 异常是强设备风险线索，但不能单独判断用户作恶。
- `appLaunchCount` 极低提示新设备/刷机/首次使用，但阈值需按业务分布校准。
- 应用列表中的灰产 APP 是风险线索，需结合安装时间、操作链路和账号行为。
- 关联图谱封禁比例高可支持团组风险，但关联关系本身不是同伙证明。
- risk_label 具体名称只作为 raw observation，不沉淀为长期本质规则。

## 11. 截图与页面锚点

| 截图路径 | 对应页面 | 关键模块 | 关键字段位置 |
|---|---|---|---|
| `platform_cards_screenshots/device_platform/01_overview.png` | 设备详情总览 | 基础信息、风险详情 | device_id, hardware_trusted, risk_label |
| `platform_cards_screenshots/device_platform/02_app_list.png` | 应用列表 | 全部/非系统 APP | app_name, app_package, app_install_time |
| `platform_cards_screenshots/device_platform/03_relation_graph.png` | 关联图谱 | 设备扩散、用户扩散 | related_user_count, banned_user_count |
| `platform_cards_screenshots/device_platform/04_account_info.png` | 账号信息 | 账号状态、资料变更 | account_status, profile_changed, risk_label |
| `platform_cards_screenshots/device_platform/05_device_info.png` | 设备信息 | SDK 底层指纹 | appLaunchCount, safe_status, apkPath |

## 12. 待确认项

- `safe_status` 完整取值字典和含义需确认。
- `risk_level=客观事实` 与风险等级的解释边界需确认。
- 应用列表、设备信息为高敏数据，权限和审计要求需确认。
- APK 风险字段的检测口径需补充。

