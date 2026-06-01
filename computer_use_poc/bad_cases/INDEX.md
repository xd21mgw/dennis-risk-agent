# bad_cases Index

Status: `regression_source` and `historical_only`. Bad cases explain failures
that should be converted into active runtime, orchestration, answer-template, or
validation rules. They are not runtime mainline by themselves.

Do not move or delete existing bad case files in this indexing round.

## Current Files

| file | theme | intended use |
|---|---|---|
| `BC-ATO-SUSPICIOUS-ANCHOR-2892617234.md` | ATO single-case suspicious anchor discovery | regression_source for ATO anchor-first workflow, device identity consistency, and response-too-large boundary |
| `BC-BATCH-ATO-MISSING-CLUSTER-LENS.md` | Batch ATO missing cluster lens | regression_source for compromised-account cluster lens, representative case deep dive, and cluster-level backfill |

## Boundary

- Bad cases are quality evolution assets.
- If a bad case describes a rule that should affect runtime, register it in the
  active runtime files and validation cases.
- Do not infer current behavior only from bad case text.

## Future Migration Check

Before moving bad cases:

- Check references from `runtime_validation_cases_v1.yaml`.
- Check `smoke_tests.md` keyword gates.
- Check run logs and architecture docs that cite exact bad case filenames.
- Keep bad case migrations separate from runtime behavior changes.
