# Validation TODO

Local validation:

- Parse the included YAML file.
- Run package asset scan.
- Confirm `observation_schema_supports_new_status=true`.
- Confirm the package contains only the schema file and safe notes.
- Confirm no runtime transient identifiers or credential material are included.

Internal Agent follow-up:

- Overlay the schema file.
- Re-check readiness gate for RCP eventList runtime smoke.
- Keep runtime smoke separate from this package validation.

