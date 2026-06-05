# Asset Extraction Guard Minimal Closure v1

## 本轮目标

在重新打包 / 上传前补齐 Dennis Risk Agent release 瘦身安全的最小闭环，防止 release 包带出不该共享的母体资产、完整 Skill 原文、历史 case、run logs、源码或敏感内部细节。

## 修改文件

- `computer_use_poc/asset_extraction_policy_v1.md`
- `computer_use_poc/package_asset_scanner_rules.json`
- `computer_use_poc/package_asset_scanner.py`
- `computer_use_poc/asset_extraction_regression_cases_v1.md`
- `computer_use_poc/release_security_checklist_v1.md`
- `computer_use_poc/answer_experience_templates.md`
- `computer_use_poc/README.md`
- `computer_use_poc/smoke_tests.md`
- `computer_use_poc/run_logs/asset_extraction_guard_minimal_closure_v1.md`
- `computer_use_poc/test_fixtures/package_asset_scanner_risky_mock/README.md`
- `computer_use_poc/test_fixtures/package_asset_scanner_risky_mock/skills/dennis_risk_agent_skills_v2_1_focused_deep/02_domain_skills/mock_skill.md`

## Scanner 规则摘要

- 路径级阻断：`02_domain_skills/`、全量 `run_logs/`、`runtime_logs/question_collection/`、`semi_open_pilot_logs/`、auth/session/cookie/token/secret/credential/key 命名文件、嵌套 `outputs/dist` / `outputs/release`。
- 内容级阻断：cookie、token、session、authorization、bearer、api_key、x-ks-*、header、password、secret、手机号、auth state、完整提示词、source observation / source response summary / platform response summary。
- 输出增强：severity 使用 `critical / high / medium / low`；critical / high 时 `package_should_block=true`；finding 包含命中文件、规则名、原因和建议处理方式。

## Regression 覆盖

新增 `asset_extraction_regression_cases_v1.md`，覆盖 26 条样例：

- 完整 Skill / prompt / run log / case / source observation 抽取。
- cookie / token / session / header / API key 抽取。
- 完整源码包、完整母体包、绕过 scanner、改名夹带。
- 手机号 / IP 输出边界。
- 完整策略库、bad case 库、question_collection 日志摘要。
- 合法的能力摘要、脱敏样例、schema、manifest 请求。

## 本地验证命令

```bash
python3 -m json.tool computer_use_poc/package_asset_scanner_rules.json >/tmp/package_asset_scanner_rules.ok
python3 -m py_compile computer_use_poc/package_asset_scanner.py
rg -n "asset_extraction|cookie|token|session|header|run_logs|domain_skills|package_should_block|safe_summary|release_security" computer_use_poc
git diff --check
python3 computer_use_poc/package_asset_scanner.py computer_use_poc/test_fixtures/package_asset_scanner_risky_mock
```

mock risky package 若启用，预期 critical / high 命中且 `package_should_block=true`。

## 未做事项

- 未访问真实平台。
- 未调用 DataAgent。
- 未修改 auth / gateway。
- 未重新打包 release。
- 未上传 release。
- 未提交 git。
