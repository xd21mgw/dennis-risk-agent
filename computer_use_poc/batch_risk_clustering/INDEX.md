# batch_risk_clustering Index

Status: batch risk capability navigation. This directory mixes active batch
runtime contracts, ATO cluster lens rules, offline/Hive planning, validation,
and historical golden materials.

## Runtime / Capability Mainline

| file | purpose | move risk |
|---|---|---|
| `README.md` | Batch risk clustering entry and boundaries. | high |
| `batch_risk_clustering_methodology_v1.md` | Batch clustering method and workflow. | high |
| `batch_ato_cluster_lens_v1.md` | ATO / compromised-account cluster lens overlay. | high |
| `batch_risk_case_schema_v1.md` | Batch case schema. | high |
| `batch_risk_threshold_policy_v1.md` | Threshold and confidence policy. | high |
| `batch_risk_response_template_v1.md` | Batch answer template. | high |
| `batch_risk_evidence_card_template_v1.md` | Batch evidence card template. | high |
| `batch_risk_pattern_summary_template_v1.md` | Pattern summary template. | high |
| `batch_risk_representative_sampling_v1.md` | Representative sample selection. | high |
| `batch_top_dimension_drilldown_template_v1.md` | Top-dimension drilldown template. | high |
| `batch_frequent_pattern_contribution_template_v1.md` | Frequent-pattern contribution template. | high |
| `abnormal_correlation_matrix_v1.md` | Abnormal correlation matrix. | high |
| `account_risk_data_source_registry_v1.md` | Account-risk data source registry. | high |

## Offline / Hive Planning

| file | purpose | boundary |
|---|---|---|
| `account_security_hive_source_registry_v1.md` | Registry-first Hive source guidance for account security. | planning only; DataAgent/Hive execution still requires explicit authorization |
| `account_security_hive_query_plan_templates_v1.md` | Hive query plan templates. | planning only |
| `batch_l1_feature_query_contract_v1.md` | L1 feature query contract. | planning / offline evidence contract |

## Validation / Regression / Historical

| file | purpose | role |
|---|---|---|
| `batch_risk_runtime_validation_cases_v1.yaml` | Batch runtime validation cases. | validation |
| `batch_risk_runtime_prompt_examples_v1.md` | Prompt examples. | validation aid |
| `batch_risk_text_dry_run_v1.md` | Text dry-run record. | historical / validation |
| `batch_risk_quality_rubric_v1.md` | Quality rubric. | validation |
| `batch_risk_golden_answers_v1.md` | Golden answers. | regression_source / historical |
| `batch_risk_golden_samples_v1.md` | Golden samples. | regression_source / historical |

## Migration Boundary

- Do not move runtime mainline files without checking
  `runtime_required_file_manifest_v1.yaml`, `smoke_tests.md`, and batch routing
  references.
- Golden and text dry-run files are historical/regression assets, not runtime
  source truth.
- This index follows `docs/architecture/runtime_directory_consolidation_plan_v1.md`.
