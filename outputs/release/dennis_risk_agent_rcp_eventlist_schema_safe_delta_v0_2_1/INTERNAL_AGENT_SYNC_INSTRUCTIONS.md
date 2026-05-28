# Internal Agent Sync Instructions

Apply this file:

- `computer_use_poc/platform_access/observation_schema_v0_1.yaml`

After overlay, validate:

1. YAML parse succeeds.
2. `source_status_enum` includes all v0.2.1 RCP eventList status values.
3. `failure_layer_enum` includes all v0.2.1 RCP eventList layer values.
4. Internal Agent can mark schema readiness before any RCP runtime smoke.

Do not run RCP runtime smoke from this package alone. It is a schema readiness delta.

