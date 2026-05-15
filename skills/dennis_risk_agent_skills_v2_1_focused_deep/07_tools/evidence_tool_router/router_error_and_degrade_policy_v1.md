# Router Error and Degrade Policy v1

## 0. 目标

本文件定义 Evidence Tool Router 层的失败和降级策略。原则是：provider 失败不能被解释为风险成立，也不能被解释为无风险。

## 1. provider_unavailable

- 是否可重试：可以
- 是否切换 provider：可以
- 是否生成 fallback query_intent：需要
- 是否降级结论：需要
- 是否人工确认：视风险和处置影响
- 是否停止自动补证：不一定，若有 fallback 可继续
- 是否可以输出治理建议：只能输出监控、补证、人工复核类建议
- 是否禁止强结论：是

## 2. provider_timeout

- 是否可重试：可以
- 是否切换 provider：可以
- 是否生成 fallback query_intent：需要
- 是否降级结论：需要
- 是否人工确认：必要时需要
- 是否停止自动补证：超过重试阈值后停止
- 是否可以输出治理建议：可以输出低风险治理或补证建议
- 是否禁止强结论：是

## 3. provider_no_permission

- 是否可重试：不建议无授权重试
- 是否切换 provider：可以，但不得绕过权限
- 是否生成 fallback query_intent：需要
- 是否降级结论：需要
- 是否人工确认：需要
- 是否停止自动补证：涉及敏感数据时停止
- 是否可以输出治理建议：只能输出权限申请、人工复核和非处置建议
- 是否禁止强结论：是

## 4. provider_partial

- 是否可重试：可以
- 是否切换 provider：可以
- 是否生成 fallback query_intent：需要
- 是否降级结论：需要
- 是否人工确认：强处置前需要
- 是否停止自动补证：不一定
- 是否可以输出治理建议：可以输出灰度、监控、补证建议
- 是否禁止强结论：是，除非关键证据已由其他 provider 闭合

## 5. provider_empty_result

- 是否可重试：可以
- 是否切换 provider：可以
- 是否生成 fallback query_intent：需要
- 是否降级结论：需要
- 是否人工确认：必要时需要
- 是否停止自动补证：不一定
- 是否可以输出治理建议：只能输出补证或暂不支持强结论
- 是否禁止强结论：是
- 重点规则：empty_result 不等于无风险

## 6. provider_ambiguous_result

- 是否可重试：可以，需缩小条件或补充输入
- 是否切换 provider：可以
- 是否生成 fallback query_intent：需要
- 是否降级结论：需要
- 是否人工确认：需要
- 是否停止自动补证：不一定
- 是否可以输出治理建议：可以输出多假设补证建议
- 是否禁止强结论：是

## 7. provider_data_quality_risk

- 是否可重试：视质量风险类型
- 是否切换 provider：可以
- 是否生成 fallback query_intent：需要
- 是否降级结论：需要
- 是否人工确认：关键证据受影响时需要
- 是否停止自动补证：不一定
- 是否可以输出治理建议：可以输出监控和质量校验建议
- 是否禁止强结论：当质量风险影响核心证据时禁止

## 8. provider_conflict

- 是否可重试：可以
- 是否切换 provider：需要引入第三方证据或人工复核
- 是否生成 fallback query_intent：需要
- 是否降级结论：需要
- 是否人工确认：需要
- 是否停止自动补证：冲突无法解释时停止
- 是否可以输出治理建议：只能输出多假设解释和补证建议
- 是否禁止强结论：是
- 重点规则：provider_conflict 必须进入多假设解释

## 9. provider_parse_failed

- 是否可重试：可以
- 是否切换 provider：可以
- 是否生成 fallback query_intent：需要
- 是否降级结论：需要
- 是否人工确认：需要
- 是否停止自动补证：parser 连续失败时停止
- 是否可以输出治理建议：仅补证或修复 parser
- 是否禁止强结论：是
- 重点规则：parse_failed 不得把原始文本硬解释成证据

## 10. provider_rate_limited

- 是否可重试：可以，需退避
- 是否切换 provider：可以
- 是否生成 fallback query_intent：可选
- 是否降级结论：需要
- 是否人工确认：视处置影响
- 是否停止自动补证：超过限流阈值后停止
- 是否可以输出治理建议：可以输出等待、缩小范围、人工复核建议
- 是否禁止强结论：是

## 11. 全局规则

- no_permission 不得强结论。
- empty_result 不等于无风险。
- provider_conflict 必须进入多假设解释。
- parse_failed 不得把原始文本硬解释成证据。
- 所有 provider 都失败时，输出证据不足和人工补证任务。
- 自动处罚、冻结、扣除、封禁、策略上线必须禁止。

