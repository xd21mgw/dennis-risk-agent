# Dennis E2E Multi Evidence Readonly Run 002 Cloud Success

```yaml
run_id: dennis_e2e_multi_evidence_readonly_run_002_cloud_success
version: v2.5.8.1
execution_env: cloud_internal_agent
test_type: e2e_multi_evidence_readonly_test
validation_status: e2e_three_source_success
test_question: "帮我看下 4231737183 今天是不是风险用户，为什么被阻止/验证？"
source_id: "4231737183"
completed_sources:
  - tianshi_strategy_hit_check
  - unified_login_log_check
  - archives_center_profile_check
failed_sources: []
```

## 1. recoverable_preflight_steps

```yaml
recoverable_preflight_steps:
  - archives_center initially redirected to account.p.adm-corp.kuaishou.com
  - account / username field was prefilled
  - clicking "下一步" entered archives center successfully
  - 本次运行中预填账号为 muguangwu，但这只是样例，不是固定规则

archives_preflight_result:
  status: archives_independent_login_preflight_required_but_recoverable
  recoverable_preflight_success: true
  query_status_after_recovery: success
```

说明：

- 不要把 `muguangwu` 写成固定判断条件。
- 后续执行时，只要档案中心独立登录页出现账号 / 用户名已预填状态，应先点击“下一步”尝试恢复会话。
- 如果点击后仍要求密码 / 扫码 / MFA，才标记为 `archives_independent_login_required`。

## 2. evidence_summary

```yaml
evidence_summary:
  conclusion_level: strong_suspicion
  conclusion: 三源证据均到位，存在较强风险线索；但不输出最终作弊定性。
  completed_sources:
    - tianshi_strategy_hit_check
    - unified_login_log_check
    - archives_center_profile_check
  failed_sources: []
```

## 3. strategy_evidence

```yaml
strategy_evidence:
  source: tianshi_strategy_hit_check
  query_status: success
  has_strategy_hit: true
  raw_record_count: 4
  production_policy_hit_count: 4
  risk_decision_distribution:
    阻止: 3
    验证: 1
  event_type_distribution:
    USER_REGISTER_NEW: 3
    LOGIN_AUDIT: 1
  risk_type_distribution:
    其他: 3
    账号: 1
  key_points:
    - 3 次 USER_REGISTER_NEW 注册阻止
    - 1 次 LOGIN_AUDIT 登录验证
    - 置信度均为强
    - 命中策略包括 BS_Register_nosense_captcha_all、BS_fake_account_register_thirdPlatformAll_bindphone、BS_fake_account_banuser_thirdLogin_nophone_need_sms
```

## 4. login_evidence

```yaml
login_evidence:
  source: unified_login_log_check
  query_status: success
  records_found: true
  login_event_count: 8
  verify_event_count: 0
  abnormal_login_signals:
    - 三方登录失败 6 次，其中今日 5 次
    - 全部操作来自同一设备 ANDROID_699157fc42e2a4b5
    - 失败集中在 11:38-12:08 约 30 分钟内
    - 今日仅 1 次三方登录成功，时间为 11:38:41
  token_or_session_risk_signals:
    - 11:38:41 token 下发成功
    - 11:48:26 refreshToken 成功
    - token 刷新与登录成功时间对齐
```

## 5. profile_evidence

```yaml
profile_evidence:
  source: archives_center_profile_check
  query_status: success
  extraction_mode: dom_snapshot_read
  profile_found: true
  account_status: 封禁
  username: 想念爱如潮水
  user_id: "4231737183"
  phone: 未设置
  kwai_id: 未设置
  fans: 58
  following: 371
  likes: 1151
  works: 0
  risk_tags:
    - 封禁（梯度计数 0）
  historical_risk_signals:
    - 用户实时负向：用户封禁
    - 业务领域：内容安全
    - 标签：色情诉求
    - 队列：恋童癖审核列表
    - 负向开始时间：2025-11-29 14:10:22
    - 预计结束时间：2026-11-29 14:10:23
    - 是否可申诉：不可申诉（处于频控限制中）
    - 审核来源：用户安全召回恋童癖审核
  platform_operations:
    - 限时封禁：封禁中，解除时间 2026-11-29 14:10:22
    - 直播权限：hidden（已关闭）
    - 永久封禁：正常
    - 高危封禁：正常
    - 梯度封禁：正常
    - 社交封禁：正常
    - 隔离：正常
  device_summary:
    - 最近登录设备：有
    - 最近启动 IP：183.197.228.61
    - 注册 IP：120.2.193.135
  realname_or_bind_summary:
    - 手机号：未设置
    - 快手号：未设置
    - 第三方注册原始信息入口可见
```

## 6. cross_evidence_summary

```yaml
cross_evidence_summary:
  - 三源证据全部到位
  - 档案中心显示账号当前处于限时封禁状态，封禁原因来自历史内容安全审核
  - 天狮显示今日 11:38-12:08 触发 4 次生产策略命中，包括注册阻止和登录验证
  - 登录日志显示同一 Android 设备在短时间内多次三方登录失败，并出现一次 token 下发和一次 token 刷新成功
  - 今日策略命中与登录日志时间窗口对齐
  - 历史封禁原因与今日注册/登录策略命中属于不同证据维度，不应混为同一个因果链
```

## 7. supporting_evidence

```yaml
supporting_evidence:
  - source: tianshi_strategy_hit_check
    finding: 今日有 4 条生产策略命中，包含注册阻止和登录验证
    interpretation: strong strategy evidence
  - source: unified_login_log_check
    finding: 短时间内同一 Android 设备出现多次三方登录失败，并有登录成功后的 token 下发和 refreshToken
    interpretation: login behavior evidence
  - source: archives_center_profile_check
    finding: 账号当前限时封禁，且存在历史内容安全审核负向
    interpretation: profile / historical risk evidence
```

## 8. counter_evidence

```yaml
counter_evidence:
  - source: unified_login_log_check
    finding: 今日存在一次三方登录成功并下发 token，且随后 refreshToken 成功
    interpretation: 这不是无风险证据，但说明仍有部分登录链路通过，需要进一步判断封禁对哪些业务能力生效
  - source: archives_center_profile_check
    finding: 历史封禁原因来自内容安全审核，和今日注册 / 登录策略命中不是同一个证据维度
    interpretation: 不能把历史封禁原因和今日策略命中强行合并成单一因果链
```

## 9. missing_evidence

```yaml
missing_evidence:
  - source: device_sdk_foundation_check
    reason: 本轮未跑设备 SDK / 设备画像
    impact: 无法确认同一 Android 设备是否存在 root / hook / 多开 / 模拟器 / 改机等设备侧异常
  - source: frontend_activity_profile_check
    reason: 本轮未跑前端活跃画像
    impact: 无法确认前端活跃信号和登录 / 策略命中窗口是否一致
  - source: DataAgent_Hive
    reason: 本轮不做离线聚合
    impact: 无法给出同类样本分布或历史基线
```

## 10. final_boundary_notes

```yaml
final_boundary_notes:
  - 单一证据不等于最终作弊定性
  - 策略命中阻止/验证是策略返回动作，不等于最终处置成功
  - 账号封禁原因来自历史审核结论，与今日策略命中是独立事件
  - 今日登录成功且 token 下发，说明仍存在部分登录链路通过，需要进一步判断封禁对哪些业务能力生效
  - 无数据不等于无风险
  - 本 run 不输出“用户一定作弊”等绝对结论
```
