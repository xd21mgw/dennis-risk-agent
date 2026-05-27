# Dennis Risk Agent Live Overlay Checklist

- [ ] Copy overlay files into live workspace using repository-relative paths.
- [ ] Run `python3 computer_use_poc/runtime_preflight_check.py`.
- [ ] Run `python3 computer_use_poc/sso_session_runner.py --platform login_log --action query_user_login_log --user-id 62950989 --timeout 30 --format json`.
- [ ] Confirm runner returns structured JSON observation, not constructed_url-only / dry_run_only success.
- [ ] KIM/Web retest: “不走缓存，用户是不是有问题？user_id=62950989”.
- [ ] Confirm realtime readonly API auto-trigger does not require user confirmation.
- [ ] Confirm DataAgent/Hive requires confirmation for every query / SQL / table / time window / evidence direction.
- [ ] Confirm track-analysis `track_analysis_activity_profile_api_direct` is registered.
- [ ] Confirm event-day activity alignment marks `front_backend_activity_mismatch` when applicable.
- [ ] Confirm `evidence_card`, `source_quality`, and YAML `routing_metadata` are present in evidence mode.
- [ ] Confirm no cookie/token/session/header/auth state is printed or persisted.
