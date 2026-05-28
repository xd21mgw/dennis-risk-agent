# Safe Delta Summary

This safe delta fixes the v0.2 packaging gap: the RCP eventList contract and failure taxonomy were overlaid, but the live workspace also needs the observation schema enum update.

`observation_schema_supports_new_status=true`

Required `source_status_enum` values covered:

- `guessed_body_failed`
- `wrong_request_body_shape`
- `wrong_time_field_format`
- `needs_har_request_body_confirmation`
- `completed_no_hit_for_small_window`
- `extraction_timeout_after_response`
- `query_window_too_large`
- `realtime_query_timeout`

Required `failure_layer_enum` values covered:

- `parameter_contract`
- `timeout`
- `no_failure`
- `extraction_timeout`
- `query_window`

This package only contains the schema file and safe overlay notes.

