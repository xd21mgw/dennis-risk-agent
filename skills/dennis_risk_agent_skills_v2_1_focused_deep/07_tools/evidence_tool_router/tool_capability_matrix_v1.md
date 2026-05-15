# Tool Capability Matrix v1

## 0. 说明

本文件定义 Evidence Tool Router 可选择的 provider 能力矩阵。当前只描述抽象能力，不定义真实 API、表名、字段名或 SQL。

## 1. dataagent_provider

- provider 名称：`dataagent_provider`
- 定位：Hive / BI / 看板 / 数据集 / AB / 画像标签 / 离线分析 provider
- 主要能力：自然语言 question、SQL 生成、表检索、数据集分析、看板分析、AB 实验、画像标签、离线归因、趋势分析
- 适用证据：渠道 CTIT、收益聚集、活动奖励、策略后验、AB 实验、画像标签、离线趋势、指标归因
- 不适用证据：低延迟实时链路强判断、请求级实时 NG 明细、实时指纹、实时策略决策
- 输入形式：自然语言 question、链接、数据集编号、抽象取证问题
- 输出形式：SSE + markdown、SQL 文本、表格摘要、分析说明、错误信息、queryId / sessionId
- 时效特点：偏离线、准实时或看板口径
- 权限特点：依赖 Data Agent 内部权限判断
- 失败模式：无权限、返回 markdown partial、查询超时、问题歧义、只返回 SQL 未返回结果
- 是否支持结构化 request：不稳定，不能假设支持完整 query_intent constraints
- 是否支持自然语言 question：支持
- 是否支持 SQL：支持生成或解释，但返回 SQL 不等于已查到结果
- 是否支持实时查询：不作为默认实时 provider
- 是否支持批量查询：适合离线批量或聚合，真实能力待内部平台确认
- 是否支持返回 raw_result_reference：queryId 可作弱引用，但不等于完整回放能力
- 返回结果是否需要 parser：需要 markdown parser 和人工可读解释
- 是否适合作为一轮主证据：适合离线分析、趋势、AB、画像、收益、渠道归因；不适合实时链路强证据
- 是否适合作为二轮补证：适合
- 限制：不支持 structured query_intent、constraints 参数不确定、不返回结构化 evidence JSON、失败状态不细、queryId 只能弱引用

## 2. realtime_log_provider

- provider 名称：`realtime_log_provider`
- 定位：实时或准实时日志查询 provider
- 主要能力：前端日志、后端 service 日志、NG 网关日志、长链接日志、拉流日志、接口明细、请求序列
- 适用证据：前后端链路一致性、接口序列固化、NG 请求异常、实时触达链路、拉流行为
- 不适用证据：AB 实验分析、长期收益归因、画像标签检索、完整业务登记信息
- 输入形式：未来可能是结构化 query，包括用户、设备、接口、时间窗、事件类型
- 输出形式：结构化日志明细、聚合结果、无结果、超时、权限错误
- 时效特点：实时或准实时
- 权限特点：高敏，需要权限和审计
- 失败模式：超时、无权限、日志延迟、采样、join 口径不一致
- 是否支持结构化 request：未来待接入
- 是否支持自然语言 question：不作为默认方式
- 是否支持 SQL：不假设
- 是否支持实时查询：支持目标
- 是否支持批量查询：视内部平台能力
- 是否支持返回 raw_result_reference：未来应支持 trace / task 弱引用
- 返回结果是否需要 parser：需要结构化 parser
- 是否适合作为一轮主证据：适合实时链路类证据
- 是否适合作为二轮补证：适合
- 限制：真实 API 未定义，需要权限和审计

## 3. risk_engine_provider

- provider 名称：`risk_engine_provider`
- 定位：风控引擎决策和策略命中 provider
- 主要能力：策略命中、风险分、决策结果、处置动作、灰度分组、返回码、命中规则链路
- 适用证据：策略效果、误伤复盘、处置链路、风控决策解释
- 不适用证据：事实作恶直接证明、前端行为事实、设备环境事实
- 输入形式：未来可能是 risk_event_id、user_id、device_id、strategy_id、time_window
- 输出形式：策略命中、决策、分数、处置、灰度、规则链路
- 时效特点：实时或准实时
- 权限特点：高敏，需要审计
- 失败模式：无权限、日志延迟、命中链路缺失、灰度口径不一致
- 是否支持结构化 request：未来待接入
- 是否支持自然语言 question：不作为默认方式
- 是否支持 SQL：不假设
- 是否支持实时查询：支持目标
- 是否支持批量查询：视内部平台能力
- 是否支持返回 raw_result_reference：未来应支持
- 返回结果是否需要 parser：需要
- 是否适合作为一轮主证据：适合策略链路，不适合风险事实单点证明
- 是否适合作为二轮补证：适合
- 限制：策略命中不等于风险事实，需要后验验证

## 4. device_fingerprint_provider

- provider 名称：`device_fingerprint_provider`
- 定位：设备和指纹证据 provider
- 主要能力：实时指纹、异步 SDK、设备画像、模拟器 / 云手机 / 改机、app 签名 / 版本 / SDK 状态
- 适用证据：SDK 覆盖、破解包绕采集、设备环境、群控设备团组、token 环境一致性
- 不适用证据：完整收益链路、AB 实验、业务授权主体
- 输入形式：未来可能是 device_id、fingerprint_id、app version、channel、time_window
- 输出形式：指纹结果、SDK 状态、设备画像、环境异常、版本或签名线索
- 时效特点：实时与离线画像可能并存
- 权限特点：中高敏
- 失败模式：采集延迟、画像更新延迟、SDK 版本差异、设备重置影响
- 是否支持结构化 request：未来待接入
- 是否支持自然语言 question：不作为默认方式
- 是否支持 SQL：不假设
- 是否支持实时查询：支持目标
- 是否支持批量查询：视内部平台能力
- 是否支持返回 raw_result_reference：未来应支持
- 返回结果是否需要 parser：需要
- 是否适合作为一轮主证据：适合设备 / SDK 类证据
- 是否适合作为二轮补证：适合
- 限制：实时和离线画像可能不一致，SDK 缺失不能直接判破解包

## 5. relation_graph_provider

- provider 名称：`relation_graph_provider`
- 定位：关系网络和团组 provider
- 主要能力：强设备关联、用户团组、账号共设备、设备共账号、邀请关系、收益关系、导流矩阵
- 适用证据：群控团组、黑产团伙、小号、导流矩阵、活动套利网络、收益聚集辅助
- 不适用证据：单个请求链路、SDK 状态、AB 实验
- 输入形式：未来可能是 seed_user_ids、seed_device_ids、relation type、time_window
- 输出形式：团组、关系边、聚集指标、扩散路径
- 时效特点：通常准实时或离线，视图谱更新频率
- 权限特点：高敏，需要审批和审计
- 失败模式：离线延迟、关系边噪声、团组过大、权限不足
- 是否支持结构化 request：未来待接入
- 是否支持自然语言 question：不作为默认方式
- 是否支持 SQL：不假设
- 是否支持实时查询：视内部平台能力
- 是否支持批量查询：适合
- 是否支持返回 raw_result_reference：未来应支持
- 返回结果是否需要 parser：需要图结果 parser
- 是否适合作为一轮主证据：适合作为关系证据，但不能单独证明作恶
- 是否适合作为二轮补证：适合
- 限制：关联不等于作恶，图关系通常需要行为和收益补证

## 6. structured_sql_or_feature_provider

- provider 名称：`structured_sql_or_feature_provider`
- 定位：未来结构化 API / SQL / feature service provider
- 主要能力：结构化 request、结构化 response、专题特征、低延迟查询、批量查询
- 适用证据：已有专题宽表、feature service、结构化明细、低延迟补证
- 不适用证据：未建设专题的开放式分析、复杂业务解释、人工授权判断
- 输入形式：统一中间层 provider_request，未来映射为真实结构化请求
- 输出形式：结构化表格、JSON、SQL result 或 feature result
- 时效特点：可实时、准实时或离线，取决于服务
- 权限特点：取决于数据域，需审计
- 失败模式：接口不可用、schema 变化、特征过期、权限不足、限流
- 是否支持结构化 request：支持目标
- 是否支持自然语言 question：不作为默认方式
- 是否支持 SQL：可能支持，未来定义
- 是否支持实时查询：可能支持
- 是否支持批量查询：可能支持
- 是否支持返回 raw_result_reference：未来应支持
- 返回结果是否需要 parser：需要轻量映射
- 是否适合作为一轮主证据：适合标准化取证
- 是否适合作为二轮补证：适合
- 限制：未来待接入，需要定义 API

## 7. manual_review_provider

- provider 名称：`manual_review_provider`
- 定位：人工补证 / 审批 / 复核 provider
- 主要能力：人工判断、外部证据补充、权限审批、误伤复核、业务合理性确认
- 适用证据：合法矩阵、授权运营、证据冲突、权限受限、外部站外承接、误伤复核
- 不适用证据：高吞吐自动查询、实时自动闭环
- 输入形式：人工任务说明、待确认问题、证据摘要、缺口清单
- 输出形式：人工判断、业务确认、证据附件、回写建议
- 时效特点：人工时效
- 权限特点：由审批和复核流程控制
- 失败模式：等待超时、判断不一致、证据附件不足
- 是否支持结构化 request：支持任务模板
- 是否支持自然语言 question：支持
- 是否支持 SQL：不适用
- 是否支持实时查询：不适合
- 是否支持批量查询：不适合自动化闭环
- 是否支持返回 raw_result_reference：可记录审批 / 工单弱引用
- 返回结果是否需要 parser：需要人工反馈 parser
- 是否适合作为一轮主证据：只在业务合理性和人工确认场景适合
- 是否适合作为二轮补证：适合
- 限制：低效率，不适合自动化闭环

