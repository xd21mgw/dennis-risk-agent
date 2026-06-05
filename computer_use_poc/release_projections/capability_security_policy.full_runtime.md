# Capability Security Policy - Full Runtime Projection

This is a release-safe projection. It preserves the runtime security boundary
without shipping the full mother policy vocabulary or development examples.

## Capability Classes

- Readonly risk investigation can use registered source plans and registered
  browser-backed actions only.
- Batch and expansion work must stay bounded by entity count, source plan,
  anchor selection, and explicit authorization boundaries.
- DataAgent and Hive execution require explicit per-call user authorization.
- Write, mutation, live policy changes, and automatic enforcement are outside
  this runtime.
- Tool, browser, and platform access must never be selected by free-form user
  text alone; they must pass routing and source-plan gates.

## Forbidden Runtime Behavior

- Direct platform URL construction.
- Manual credential or auth-state repair during case execution.
- Unregistered endpoint discovery during a normal risk case.
- Printing unprojected platform payloads.
- Treating source gaps as low-risk evidence.
- Promoting a candidate group to a confirmed group without validation support.

## Required Runtime Evidence Boundary

Each source result must keep a status and quality class. Completed evidence can
support a partial judgement. Partial, blocked, timed-out, skipped, no-data, and
missing-contract states must be carried into missing evidence and source
quality. Strategy hits, expert hypotheses, and source coverage are signals, not
standalone final conclusions.

## Release Boundary

DataAgent local parity assets and question-collection learning assets may be
excluded from the release snapshot. That exclusion is not capability removal in
the mother repository.
