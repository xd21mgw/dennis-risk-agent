-- ==============================================================================
-- normal_population_sample_extraction_sql_v0_1.sql
--
-- Population baseline 抽样 SQL：deterministic hash sample
-- 口径：population_baseline / 大盘背景 baseline
-- 不是 LOGIN_AUE 精准 normal baseline
--
-- DataAgent 边界：只取数不分析
-- 不使用裸 LIMIT，使用 HASH(userId) % modulo 抽样
-- ==============================================================================

-- Source 1: infra_user_action_log
-- baseline_scope = population_login_behavior_sample
-- 当前不含 LOGIN_AUE 精准条件

SELECT
    *
FROM
    ks_raw_log_v3.infra_user_action_log
WHERE
    p_date = '20260609'
    AND HASH(userId) % 1000 BETWEEN 0 AND 9
;

-- ==============================================================================

-- Source 2: passport_action_log
-- baseline_scope = app_related_passport_action_sample
-- APP 过滤条件尚未完全确认，先保留全量口径

SELECT
    *
FROM
    ks_raw_log_v3.passport_action_log
WHERE
    p_date = '20260609'
    AND HASH(userId) % 1000 BETWEEN 0 AND 9
;

-- ==============================================================================

-- Source 3: weapon_android
-- baseline_scope = population_weapon_android_sample

SELECT
    *
FROM
    ks_rc_bs.weapon_data_report_device_log_kafka_2_hive_android_di_v2
WHERE
    p_date = '20260609'
    AND product IN ('KUAISHOU', 'NEBULA')
    AND HASH(userId) % 1000 BETWEEN 0 AND 9
;

-- ==============================================================================

-- Source 4: weapon_ios
-- baseline_scope = population_weapon_ios_sample

SELECT
    *
FROM
    ks_rc_bs.weapon_data_report_device_log_kafka_2_hive_IOS_di_v2
WHERE
    p_date = '20260609'
    AND product IN ('KUAISHOU', 'NEBULA')
    AND HASH(userId) % 1000 BETWEEN 0 AND 9
;

-- ==============================================================================
-- DataAgent 边界提醒（注释形式，不影响 SQL 执行）
-- 1. 只取数不分析：返回原始记录，不做聚合/统计
-- 2. 不使用裸 LIMIT
-- 3. 不输出风险判断
-- 4. 不计算 TOP-N
-- 5. 不计算低熵
-- 6. 不计算缺失率
-- 7. 不解释字段语义
-- 8. 保留所有原始字段，不做字段删减
-- 9. 不扩 source / 不 join 其他表
-- 10. 不改筛选条件
-- ==============================================================================