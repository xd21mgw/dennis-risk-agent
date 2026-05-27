# Release Manifest

Release name: `dennis_risk_agent_runtime_canonical_release_v1`

This manifest describes the clean canonical runtime release. The complete file list is in `OVERLAY_MANIFEST.txt`; file hashes are in `OVERLAY_FILE_HASHES.sha256`.

## Included Areas

- Root release docs.
- Runtime config apply checklist.
- Runtime canonical baseline.
- Multi-entry runtime guard.
- Scene routing.
- Capability registry.
- Answer templates.
- Runtime validation cases.
- Runtime integration checklist.
- Smoke tests.
- Login log and browser auth readonly playbooks.
- Question collection schemas, templates, writer, and collector stubs.
- Distilled runtime summaries only.
- Runtime-safe batch risk clustering contracts/templates/schemas.

## Explicitly Excluded

- Full deep Skill source outside `11_runtime_summaries`.
- Historical run logs full directory.
- Raw platform observations.
- Real sensitive samples.
- Risky fixtures.
- `outputs/dist`.
- `outputs/packages`.
- `.DS_Store`.
- Historical release directories.

## Release Boundary

This package does not prove live runtime config is applied. Internal Agent must validate live `openclaw.json` separately.
