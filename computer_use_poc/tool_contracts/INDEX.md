# tool_contracts Index

Status: tool/source contract navigation. This directory is included by the
runtime manifest glob and is therefore high-risk for path moves.

## Files

| file | purpose | move risk |
|---|---|---|
| `user_login_log_reliable_window_contract_v1.md` | Unified login-log reliable-window boundary and no-data interpretation. | high |

## Migration Boundary

- Do not move files in this directory without updating
  `runtime_required_file_manifest_v1.yaml` and all source/playbook references.
- Tool contracts define source boundaries; they are not historical notes.
- This index follows `docs/architecture/runtime_directory_consolidation_plan_v1.md`.
