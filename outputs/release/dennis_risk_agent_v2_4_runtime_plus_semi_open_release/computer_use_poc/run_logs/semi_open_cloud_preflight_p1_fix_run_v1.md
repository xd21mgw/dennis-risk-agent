# Semi-open Cloud Preflight P1 Fix Run v1

## 1. 本轮目标

基于云端 Dennis Risk Agent 半开放启动自检报告，修复 release 包内 P1 内容一致性问题。

本轮只处理 release 包和本地母体中的 P1 文档 / contract / smoke test 问题，不处理云端 gateway config P0。

## 2. 云端自检发现的问题

### P0: gateway config 缺少 dennis-risk-agent 定义

- 状态：本轮不处理。
- owner：云端内部 Agent / gateway 配置侧。
- 原因：Codex 本轮不访问云端 gateway config，不接 runtime。

### P1-1: sso_session_runner 版本一致性

- 检查对象：
  - `computer_use_poc/sso_session_runner.py`
  - `outputs/release/dennis_risk_agent_v2_4_runtime_plus_semi_open_release/computer_use_poc/sso_session_runner.py`
- 结论：母体和 release 包均为 Python 版。
- 关键 contract：
  - stdout 只输出单个 `sso_session_runner_envelope_v1` JSON。
  - stderr 只输出人类可读诊断 / 调试日志。
  - 不打印 cookie / token / session / header。
  - 只接受固定 `platform_key`。
  - 不接受任意 `target_url`。
  - `user_id` / timestamp 使用纯数字校验。
  - 注入字符被拒绝。
  - 异常 fail closed。

### P1-2: watchdog readonly guard 过重

- 修复：在 runtime semi-open checklist 中明确 guard 口径。
- 新口径：
  - release 包目录不强制整体 `555`，避免阻断 framework bootstrap。
  - 目录本身和 `models.json` 不纳入 watchdog 只读保护。
  - guard 只保护关键 `.md` / `.py` runtime、policy、routing、preflight、wrapper 文件。
  - guard 不阻断 framework 正常启动、依赖加载、模型配置读取或 bootstrap 写入必要工作目录。
  - 半开放 runtime 禁止通过 Agent 对话修改 release、source、policy、evaluator、routing、Skill、Prompt 或 wrapper。

### P1-3: AGENTS.md 必读路径引用 release 中不存在的 00_agent_core

- 修复：母体和 release 包 `AGENTS.md` 的“必读文件”改为“Runtime 必读文件”。
- 新路径只引用 release 包实际存在的 runtime 文件：
  - `skills/dennis_risk_agent_skills_v2_1_focused_deep/11_runtime_summaries/`
  - `computer_use_poc/runtime_semi_open_user_guide_v1.md`
  - `computer_use_poc/multi_entry_runtime_guard_v1.md`
  - `computer_use_poc/capability_registry.md`
  - `computer_use_poc/scene_to_capability_routing.md`
  - `computer_use_poc/security_preflight_policy.yaml`
  - `computer_use_poc/answer_experience_templates.md`
  - `computer_use_poc/observation_contract_v2_4_6.md`
  - `computer_use_poc/smoke_tests.md`
- 明确半开放 release runtime 不依赖 `00_agent_core`。

## 3. 修改文件

- `AGENTS.md`
- `outputs/release/dennis_risk_agent_v2_4_runtime_plus_semi_open_release/AGENTS.md`
- `computer_use_poc/runtime_semi_open_test_checklist_v1.md`
- `outputs/release/dennis_risk_agent_v2_4_runtime_plus_semi_open_release/computer_use_poc/runtime_semi_open_test_checklist_v1.md`
- `computer_use_poc/smoke_tests.md`
- `outputs/release/dennis_risk_agent_v2_4_runtime_plus_semi_open_release/computer_use_poc/smoke_tests.md`
- `computer_use_poc/run_logs/semi_open_cloud_preflight_p1_fix_run_v1.md`

## 4. 验证命令

建议本地执行：

```bash
python3 computer_use_poc/sso_session_runner.py --platform_key user_login_unified_log --user_id 4910098437
python3 computer_use_poc/sso_session_runner.py --platform_key user_login_unified_log --user_id '4910098437; rm -rf /'
python3 computer_use_poc/sso_session_runner.py --platform_key invalid_platform --user_id 4910098437
python3 computer_use_poc/sso_session_runner.py --platform_key user_login_unified_log --user_id 4910098437 --target_url https://example.com
rg -n '00_agent_core' outputs/release/dennis_risk_agent_v2_4_runtime_plus_semi_open_release/AGENTS.md
git diff --check
```

## 5. 本轮边界

- 未访问真实内部平台。
- 未调用 DataAgent。
- 未修改 auth state。
- 未处理云端 gateway config。
- 未执行真实查询。
- 未重新打 release tar.gz。

## 6. 当前结论

- release 包内 P1 内容一致性问题已修复。
- P0 gateway config 缺少 dennis-risk-agent 定义仍需云端修复。
- 若云端使用 tar.gz 部署，需要重新打包并上传新 tarball；若云端直接同步 release 目录，则同步本轮修改文件即可。
