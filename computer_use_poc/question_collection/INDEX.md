# question_collection Index

Status: question learning and runtime logging contract navigation. This
directory mixes runtime logging stubs, learning policy docs, templates,
samples, and historical validation records.

## Runtime-support Files

| file | purpose | move risk |
|---|---|---|
| `README.md` | Module entry and current boundaries. | high |
| `pilot_observation_writer.py` | Pilot observation writer. | high |
| `runtime_question_record_collector_stub_v1.py` | Local append-only collector stub. | high |
| `runtime_append_only_logging_contract_v1.md` | Runtime append-only logging contract. | high |
| `question_record_schema_v1.md` | Question record schema. | high |
| `user_feedback_capture_v1.md` | User feedback capture contract. | high |
| `question_learning_policy_v1.md` | Learning candidate policy. | high |
| `case_learning_note_template_v1.md` | Case learning note template. | high |

## Validation / Samples / Historical

| file | purpose | role |
|---|---|---|
| `question_collection_text_regression_cases_v1.yaml` | Text regression cases. | validation |
| `question_collection_text_regression_run_v1.md` | Regression run record. | historical |
| `runtime_logging_smoke_test_v1.md` | Runtime logging smoke record. | historical / validation |
| `runtime_question_record_sample_v1.jsonl` | Sample record. | sample only |
| `question_learning_candidate_queue_v1.csv` | Template/candidate queue sample. | template / historical; do not overwrite as runtime output |

## Migration Boundary

- Do not move runtime-support files without checking the manifest and smoke
  tests.
- Do not treat sample CSV/JSONL files as live runtime output.
- Live runtime writes belong under configured runtime log locations, not by
  overwriting templates in this directory.
- This index follows `docs/architecture/runtime_directory_consolidation_plan_v1.md`.
