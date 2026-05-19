# DataAgent SSE Markdown Parser Rules v1

## 0. 目标

本文件定义真实 Data Agent SSE / markdown response 的 parser 规则。

Parser 负责映射 evidence，不负责最终风控判断。

## 1. Parser 可以做什么

Parser 可以：

- 合并 SSE chunks。
- 提取 markdown 中的数据发现。
- 识别 SQL-only。
- 识别 markdown 表格。
- 提取缺失证据。
- 提取权限限制。
- 提取口径风险。
- 提取反证和误判来源。
- 抽取 Data Agent 的结论性文字为 `provider_conclusion_hint`。
- 生成 `unified_normalized_evidence`。

## 2. Parser 不可以做什么

Parser 不可以：

- 把 Data Agent 结论性文字标记为 final judgement。
- 填充 `dennis_final_judgement`。
- 直接决定治理动作。
- 直接采用 Data Agent 的下一步建议作为 `recommended_next_provider`。
- 把 parser 期望识别写入真实 Data Agent 请求。

## 3. provider_conclusion_hint 规则

如果 markdown 中出现：

- “高度疑似”
- “证据不足”
- “无法判断”
- “可能是协议攻击”
- “建议判断为”
- “更像”

Parser 应：

```yaml
provider_conclusion_hint:
  text:
  source_section:
  confidence_words:
  conflicts_with_missing_evidence:
  conflicts_with_counter_evidence:
```

Parser 不得：

- 将其放入 `dennis_final_judgement`。
- 将其作为 strong evidence。
- 将其作为处罚依据。

## 4. parser 期望识别的归属

parser 期望识别只用于：

- mock response。
- 回归测试。
- parser 校准。
- 单元测试。

真实 Data Agent question 中不得包含：

- “parser 期望识别”
- “status 应识别为”
- “returned_type 应识别为”
- “strong_evidence 应为”
- “recommended_next_provider 应为”

## 5. 推荐 provider 归属

Parser 可以输出：

- missing evidence。
- provider limitations。
- permission notes。
- quality risks。

Router / Dennis Agent 根据这些字段生成 `recommended_next_provider`。

Data Agent markdown 中的“下一步建议”只作为参考文本，不直接转 provider。

## 6. 后端有请求、前端无日志示例规则

Data Agent markdown 如果写：

- “后端有请求”
- “前端无匹配”
- “可能是协议攻击”

Parser 应映射：

- 后端请求、前端无匹配 -> key_findings。
- “可能是协议攻击” -> provider_conclusion_hint。
- 破解包、官方埋点、join 口径、合法自动化、群控真机未排除 -> missing_evidence / counter_evidence。
- 缺 realtime log / device fingerprint / risk engine -> provider_limitations。

Dennis 主 Agent 再决定：

- 是否协议攻击。
- 结论等级。
- next provider。
- 是否人工复核。

