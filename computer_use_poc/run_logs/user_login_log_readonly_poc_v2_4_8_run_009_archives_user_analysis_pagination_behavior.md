# User Login Log Readonly POC v2.4.8 Run 009

```yaml
test_stage: v2.4.8
test_type: archives_user_analysis_pagination_behavior
validation_status: archives_user_analysis_pagination_behavior_validated_with_correction

background:
  previous_automation_misread: 档案中心用户分析 Tab 被误判为无分页 / 无限滚动模式
  correction: 最新人工截图和测试证明该结论错误

archives_user_analysis_pagination_test:
  platform: archives_center
  tab: 用户分析
  sub_tab: APP端核心操作日志
  user_id: "2241990844"
  time_range: "2025-11-20 18:56 ~ 2026-05-19 18:56"
  pagination_present: true
  pagination_info:
    total_count_visible: true
    total_count: 1181
    page_size: 10
    current_page: 1
    next_button_present: true
    next_button_enabled: true
    page_jump_present: true
    page_range_visible: "1 2 3 4 5 6 ... 40"
  current_observation:
    current_page_only: true
    visible_rows_approx: 10
    partial_coverage: true

correction:
  incorrect_previous_conclusion: 无分页 / 无限滚动模式
  likely_root_cause:
    - 自动化滚动了 window / document.body
    - 未滚动表格内部 scroll container
    - 分页控件位于表格底部 / 表格容器底部，不一定随 body scroll 暴露
  required_future_behavior:
    - 区分 page body scroll 和 table container scroll
    - 先确认是否存在表格内部滚动容器
    - 未观察到分页控件不等于没有分页

guardrail:
  no_pagination_observed_does_not_mean_no_pagination: true
  table_container_scroll_required: true
  partial_coverage_required_when_total_gt_visible: true
  forbidden_interpretation:
    - 已查看6个月全量
    - 当前页就是全部历史
    - 没有更多登录记录
    - 用户分析无更多数据

status_update:
  archives_user_analysis_pagination: validated_with_correction
  archives_user_analysis_partial_coverage_guardrail: validated
  table_container_scroll_required: true
  release_status: release_candidate_not_final
```

## 边界

本轮只修正档案中心用户分析分页行为。未逐页遍历前，任何用户分析结论都必须保留 `partial_coverage=true`。
