# Validation TODO

Local package validation:

- YAML parse for the two included YAML files.
- Package asset scan must pass with no blocking findings.
- Confirm the package does not include transient runtime files, network-capture payloads, or full runtime release files.
- Confirm no runtime transient identifier appears in the package.

Internal Agent follow-up after overlay:

- Re-run contract-level validation for RCP eventList.
- Do not classify wrong body shape as auth or permission failure.
- Do not classify guessed direct request failure as direct mode unavailable.
- Keep `fastQueryHbase` as fallback or comparison source, not the primary blocking source.
- Wait for separate approval before RCP runtime smoke.
