# platform_access Index

Status: platform access contract navigation. This directory is not the runtime
brain itself; it documents platform hands, observation contracts, and access
boundaries.

Do not move or rewrite schemas in this indexing round.

## Files

| file | purpose | role | move risk |
|---|---|---|---|
| `observation_schema_v0_1.yaml` | Common source observation envelope and status vocabulary. | platform observation contract | `do_not_move_without_reference_check` |
| `failure_taxonomy_v0_1.yaml` | Standard source failure and degradation taxonomy. | platform access boundary | `do_not_move_without_reference_check` |
| `runner_invocation_contract_v0_1.md` | Runner invocation and parameter contract. | platform access support | medium |
| `browser_same_origin_adapter_contract_v0_1.md` | Browser same-origin adapter boundary. | platform access support | medium |
| `platform_access_inventory_v0_1.yaml` | Inventory of platform access assets. | index / support | medium |
| `source_orchestration_examples_v0_1.md` | Examples connecting platform sources to source plans. | example / validation aid | medium |
| `login_log_api_contract_v0_1.yaml` | Login log API contract. | platform source contract | `do_not_move_without_reference_check` |
| `archives_center_contract_v0_1.yaml` | Archives center API contract. | platform source contract | `do_not_move_without_reference_check` |
| `weapon_api_contract_v0_1.yaml` | Weapon API contract. | platform source contract | `do_not_move_without_reference_check` |
| `tianshi_rcp_api_contract_v0_1.yaml` | Tianshi/RCP API contract. | platform source contract | `do_not_move_without_reference_check` |
| `track_analysis_api_contract_v0_1.yaml` | Track-analysis API contract. | platform source contract | `do_not_move_without_reference_check` |

## Boundary

- Observation schema and failure taxonomy define how Dennis interprets platform
  source results.
- Browser-backed passthrough contracts and fixed actions remain primarily in
  `computer_use_poc/browser_backed_*` until a future path migration.
- API direct and HAR-derived inventories are currently split between this
  directory and root-level `computer_use_poc/*` playbooks.
- Raw reference and redaction rules are currently split between root-level
  contracts and field/output policy files.

## Future Migration Check

Before moving platform access files:

- Check `platform_call_playbook_index.md`.
- Check `runtime_required_file_manifest_v1.yaml`.
- Check `source_orchestration_plan_v1.yaml`.
- Check platform-specific playbooks and validation cases.
- Run relevant source orchestration and text dry-run checks.
