# Internal Agent Sync Instructions

Apply only the two YAML files in this safe delta:

1. `computer_use_poc/platform_access/tianshi_rcp_api_contract_v0_1.yaml`
2. `computer_use_poc/platform_access/failure_taxonomy_v0_1.yaml`

After overlay:

1. Parse both YAML files.
2. Confirm eventList uses `browser_same_origin` as primary invocation.
3. Confirm HTTP SSO direct is marked `needs_har_request_body_exact_replay`.
4. Confirm `tableHeaderList` is an object array with `column_name` and `column_comment`.
5. Confirm time fields use `YYYY-MM-DD HH:mm:ss`.
6. Confirm `eventV2.sourceIds` is a string field.
7. Confirm `conditionList` is a nested condition group.
8. Confirm wrong body and wrong time failures map to parameter-contract failures.

Do not run RCP runtime tests from this package. Runtime test readiness remains blocked until this mother sync and safe delta are applied.

