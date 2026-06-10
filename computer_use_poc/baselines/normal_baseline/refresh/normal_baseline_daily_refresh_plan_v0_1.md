# normal_baseline Daily Refresh Plan v0.1

> **⚠️ v0.1 版本口径**：normal_baseline v0.1 是静态快照 baseline，不自动刷新。本文档仅为未来 refresh 设计的参考，当前不创建任何自动刷新、自动抽样、daily cron 或 DataAgent/Hive 自动执行逻辑。除非用户明确要求 `refresh / rerun profiler / replace samples`，否则后续一直使用用户指定的 `baseline_dir`。

## 定位

Daily refresh 设计文档（v0.1 仅保留设计，不创建自动化任务）。

目标是支持后续将 normal_baseline 定期刷新，使 baseline 统计保持时效性。

## 设计理念

normal_baseline 不是一次性资产。字段覆盖率、缺失率、TOP-N 分布和低熵 profile 会随时间变化：
- 新字段可能出现（平台新增字段）
- 字段覆盖率可能变化（SDK 升级、业务变更）
- TOP-N 分布可能变化（用户群体变化、设备市场变化）
- 低熵值可能变化（大众设备型号换代）

Daily refresh 的目标是保持 baseline 统计与当前数据一致。

## 刷新策略

### Batch 级刷新

每个 normal_batch 有自己的刷新策略：

```yaml
batch_refresh_config:
  batch_id: "normal_batch_20260609_login_aue_v0_1"
  refresh_frequency: daily
  refresh_time: "03:00 CST"  # 每日凌晨 3 点
  refresh_method: deterministic_hash_sample  # 使用与原 batch 相同的 hash 参数
  refresh_time_window:
    offset_from_current: -1  # 取前一天的数据
    window_duration: "4 hours"  # 取 4 小时窗口
  
  # 刷新后的 profiler 自动执行
  auto_profiler_after_refresh: true
  profiler_tool: local_profiler_v0_1
```

### 分层 baseline 刷新

各分层 baseline 的刷新策略与 batch 级类似，但按分层维度独立刷新：

```yaml
segmented_refresh_config:
  segment_key: "LOGIN_AUE_52_mature_user_medium_follower_success"
  refresh_frequency: daily
  refresh_time: "03:00 CST"
  refresh_method: deterministic_hash_sample
```

### 刷新结果比对

每次刷新后，自动与上一次 baseline 比对：

```yaml
refresh_comparison:
  compare_with: last_baseline
  comparison_fields:
    - coverage_ratio_change     # 覆盖率变化
    - missing_ratio_change      # 缺失率变化
    - top1_ratio_change         # TOP1 变化
    - top3_ratio_change         # TOP3 变化
    - new_fields_discovered     # 新发现字段
    - fields_disappeared        # 消失字段
    - normal_status_changes     # normal_status 变化
  
  comparison_thresholds:
    coverage_ratio_alert: 0.05    # 覆盖率变化超过 5% 告警
    top1_ratio_alert: 0.05        # TOP1 变化超过 5% 告警
    new_fields_alert: 3           # 新发现超过 3 个字段告警
```

## 刷新流程

```
[定时触发]
    ↓
[DataAgent：按 batch 条件抽取前一天的样本记录]
    ↓
[local profiler：对新样本做字段发现、profile、分布、缺失率、低熵]
    ↓
[baseline 比对：与上一次 baseline 比对变化]
    ↓
[baseline 更新：写入新 baseline 文件]
    ↓
[变更通知：通知消费方 baseline 已更新]
```

## 版本管理

每次刷新生成新版本 baseline：

- 版本号格式：`v{YYYYMMDD}`
- 文件路径：`sample_batches/normal_batch_{batch_id}_v{YYYYMMDD}.yaml`
- 保留最近 30 天的 baseline 版本
- 每月保留 1 个月度 baseline 作为长期参考

## 边界声明

1. daily refresh 只更新 normal 侧客观统计，不做风险判断
2. 刷新结果比对只记录客观变化，不做异常检测
3. 新发现字段只记录，不做候选特征推荐
4. 不自动扩展 batch
5. 不自动扩展分层维度
6. 不自动触发 DataAgent 新查询
7. 变化告警只通知，不自动处置

## v0.1 状态

- 只有设计文档，不创建自动化任务
- 不创建 cron job / scheduler
- 不创建 DataAgent 自动调用
- 不创建 baseline 版本管理脚本
- 等后续 profiler 实现后再考虑刷新自动化