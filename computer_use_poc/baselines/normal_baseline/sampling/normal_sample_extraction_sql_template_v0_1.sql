-- normal_baseline sample extraction SQL template v0.1
-- ⚠️ DataAgent 边界：只取数，不分析（do not analyze）
-- 不输出"可疑/正常/异常/风险/共性/特征"等判断
-- 不自行扩展查询 source
-- 不自行 join 其他表
-- 不改筛选条件
-- 不聚合字段分布
-- 不计算 TOP-N
-- 不计算低熵
-- 不计算缺失率
-- 不解释字段语义
-- 如果 SQL 有问题，只指出执行错误和最小修正建议

-- ============================================================
-- 替换说明：
-- {table_name}       -> 目标表名
-- {start_time}       -> 时间窗口起始，格式 'yyyy-MM-dd HH:mm:ss'
-- {end_time}         -> 时间窗口终止，格式 'yyyy-MM-dd HH:mm:ss'
-- {hash_modulo}      -> hash 取模数，默认 1000
-- {hash_range_start} -> hash 范围起始
-- {hash_range_end}   -> hash 范围终止
-- {sampling_conditions} -> WHERE 条件列表，从 normal_batch yaml 照搬
-- ============================================================

-- Deterministic hash sample：不使用裸 LIMIT
-- hash(userId) % {hash_modulo} BETWEEN {hash_range_start} AND {hash_range_end}
-- 确保同条件多次取样结果一致

SELECT
  -- 普通列：保留原始字段名和值
  userId            AS entity_id,
  dt                AS dt,
  event_time        AS event_time,
  loginType         AS loginType,
  _errorCode        AS _errorCode,
  userRegisterDays  AS userRegisterDays,
  userFanCnt        AS userFanCnt,

  -- JSON 字段：保留原始字符串，本地 profiler 展开
  deviceInfo        AS deviceInfo_raw_json,
  networkInfo       AS networkInfo_raw_json,
  appVersionInfo    AS appVersionInfo_raw_json,

  -- map/struct 字段：保留原始结构，本地 profiler 展开
  extParams         AS extParams_raw_map,
  loginContext      AS loginContext_raw_struct,

  -- array 字段：保留原始结构，本地 profiler 展开
  tagList           AS tagList_raw_array,

  -- 其他可能字段（按实际表结构调整）
  deviceId,
  xm1,
  xm3,
  androidId,
  oaid,
  ip,
  appVersion,
  platform,
  province,
  city,
  networkType,
  deviceModel,
  osVersion,
  screenResolution,
  isRoot,
  isEmulator,
  isDebugMode,
  accessibilitySvc

FROM {table_name}

WHERE
  -- 时间窗口
  event_time >= '{start_time}'
  AND event_time <= '{end_time}'

  -- 筛选条件（从 normal_batch yaml 照搬，不得修改）
  AND userRegisterDays > 200
  AND loginType = 52
  AND _errorCode = 1
  AND userFanCnt > 200

  -- Deterministic hash sample
  AND HASH(userId) % {hash_modulo} BETWEEN {hash_range_start} AND {hash_range_end}

-- 不使用 ORDER BY + LIMIT
-- 不使用 RAND()
-- 不使用 TABLESAMPLE
-- hash sample 保证可重复、确定性