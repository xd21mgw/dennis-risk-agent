import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "l3_extraction"))

from batch_action_timing_exporter import build_timing_summary, render_markdown, write_timing_summary


def _write_checkpoint(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "timing_trace": {
            "global": {
                "total_elapsed_ms": 10000,
                "batch_wait_ms": 6800,
                "plan_build_ms": 10,
                "batch_submit_ms": 20,
                "artifact_build_ms": 30,
                "checkpoint_write_ms": 40,
            },
            "chunks": [
                {
                    "chunk_id": "round_1_primary_1",
                    "source_group": "login_logs_search",
                    "actions": ["login_logs_search", "login_logs_search"],
                    "action_count": 2,
                    "completed_count": 2,
                    "timeout_count": 0,
                    "blocked_count": 0,
                    "partial_count": 0,
                    "pending_count": 0,
                    "wait_ms": 1200,
                    "batch_elapsed_ms": 1250,
                    "service_wait_started_at": "2026-06-24T01:00:00",
                    "service_returned_at": "2026-06-24T01:00:01",
                    "per_source_elapsed_ms": None,
                },
                {
                    "chunk_id": "round_1_primary_2",
                    "source_group": "archives_user_profile+weapon_inventory+archives_user_analysis+archives_photo_search",
                    "actions": [
                        "archives_user_profile",
                        "weapon_inventory",
                        "archives_user_analysis",
                        "archives_photo_search",
                    ],
                    "action_count": 4,
                    "completed_count": 3,
                    "timeout_count": 1,
                    "blocked_count": 0,
                    "partial_count": 0,
                    "pending_count": 0,
                    "wait_ms": 5600,
                    "batch_elapsed_ms": 5650,
                    "service_wait_started_at": "2026-06-24T01:00:02",
                    "service_returned_at": "2026-06-24T01:00:08",
                    "per_source_elapsed_ms": None,
                },
                {
                    "chunk_id": "round_1_cookie_token_session_header_password_probe",
                    "source_group": "cookie_token_session_header_password_source",
                    "actions": [],
                    "action_count": 1,
                    "completed_count": 0,
                    "timeout_count": 0,
                    "wait_ms": None,
                    "per_source_elapsed_ms": None,
                },
            ],
        }
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_single_action_chunk_exports_action_level_timing(tmp_path: Path):
    checkpoint = tmp_path / "checkpoints" / "dennis_sample_expand_validate_batch" / "round_01_batch_01_done.json"
    _write_checkpoint(checkpoint)

    summary = build_timing_summary([checkpoint], batch_run_id="fixture_batch")

    login = next(row for row in summary["action_timing_summary"] if row["source_action"] == "login_logs_search")
    assert login["timing_precision"] == "action_level"
    assert login["instrumentation_gap"] is False
    assert login["wait_ms"] == 1200
    assert login["user_count"] == 2
    assert login["provenance"]["wait_ms_source"] == "timing_trace.chunks[].wait_ms"


def test_mixed_chunk_is_group_only_and_does_not_allocate_wait(tmp_path: Path):
    checkpoint = tmp_path / "checkpoints" / "dennis_sample_expand_validate_batch" / "round_01_batch_01_done.json"
    _write_checkpoint(checkpoint)

    summary = build_timing_summary([checkpoint], batch_run_id="fixture_batch")

    mixed = next(row for row in summary["action_timing_summary"] if row["source_action"] == "mixed_actions")
    assert mixed["timing_precision"] == "group_only"
    assert mixed["instrumentation_gap"] is True
    assert mixed["wait_ms"] == 5600
    assert "per_action_wait_ms" in mixed["missing_fields"]
    assert "per_source_elapsed_ms" in mixed["missing_fields"]
    assert not any(row["source_action"] == "archives_user_profile" and row["wait_ms"] == 5600 for row in summary["action_timing_summary"])


def test_primary_summary_marks_partial_breakdown(tmp_path: Path):
    checkpoint = tmp_path / "checkpoints" / "dennis_sample_expand_validate_batch" / "round_01_batch_01_done.json"
    _write_checkpoint(checkpoint)

    summary = build_timing_summary([checkpoint], batch_run_id="fixture_batch")

    assert summary["primary_action_breakdown_possible"] == "partial"
    assert summary["primary_action_breakdown_blocker"] == "per_action_wait_ms_missing"
    primary_mixed = next(row for row in summary["primary_action_timing_summary"] if row["source_action"] == "mixed_actions")
    assert primary_mixed["source_group"] == "primary"
    assert primary_mixed["instrumentation_gap"] is True


def test_missing_fields_do_not_crash_and_sensitive_words_are_redacted(tmp_path: Path):
    checkpoint = tmp_path / "checkpoints" / "dennis_sample_expand_validate_batch" / "round_01_batch_01_done.json"
    _write_checkpoint(checkpoint)

    summary = build_timing_summary([checkpoint], batch_run_id="fixture_batch")
    out_json, out_md = write_timing_summary(summary, tmp_path / "out")
    rendered = render_markdown(summary)
    serialized = json.dumps(summary, ensure_ascii=False).lower() + rendered.lower() + out_json.read_text().lower() + out_md.read_text().lower()

    unknown = next(row for row in summary["action_timing_summary"] if row["source_action"] == "unknown_action")
    assert unknown["instrumentation_gap"] is True
    assert "actions" in unknown["missing_fields"]
    assert "wait_ms" in unknown["missing_fields"]
    for sensitive in ["cookie", "token", "session", "header", "password"]:
        assert sensitive not in serialized


def test_source_group_summary_and_gap_summary_are_present(tmp_path: Path):
    checkpoint = tmp_path / "checkpoints" / "dennis_sample_expand_validate_batch" / "round_01_batch_01_done.json"
    _write_checkpoint(checkpoint)

    summary = build_timing_summary([checkpoint], batch_run_id="fixture_batch")

    assert summary["total_elapsed_ms"] == 10000
    assert summary["browser_wait_ms"] == 6800
    assert summary["timeout_summary"]["total_timeout_count"] == 1
    assert summary["source_gap_summary"]["total_source_gap_count"] == 1
    assert summary["instrumentation_gap_summary"]["instrumentation_gap"] is True
    assert summary["instrumentation_gap_summary"]["mixed_primary_chunk_gap_count"] == 1
