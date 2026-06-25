import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from runtime_case_execution_runner import (  # noqa: E402
    _batch_source_id,
    build_archives_broad_followup_source_plans,
)


def _photo_observation(round_id: int = 1, entity_index: int = 1, photo_id: str = "photo_1") -> dict:
    return {
        "source_id": _batch_source_id(round_id, entity_index, "photo"),
        "action": "archives_photo_search",
        "parsed_body_field_handles": [
            {
                "field": "photo_id",
                "canonical_field": "photo_id",
                "field_path": "body.data.list[0].photoId",
                "value": photo_id,
            }
        ],
    }


def test_archives_broad_followup_builds_independent_groups_from_same_anchor_snapshot():
    photo_plan, social_plan, feedback_plan = build_archives_broad_followup_source_plans(
        1,
        ["10001"],
        [_photo_observation()],
        window_start_ms=1000,
        window_end_ms=2000,
    )

    actions = {item.action for item in [*photo_plan, *social_plan, *feedback_plan]}

    assert {
        "archives_photo_profile",
        "archives_photo_meta",
        "archives_private_message_search",
        "archives_comment_search",
        "archives_user_report_search",
        "archives_negative_report",
        "archives_review_logs",
        "archives_punish_status",
    } <= actions

    user_level_actions = {
        "archives_private_message_search",
        "archives_user_report_search",
        "archives_negative_report",
        "archives_review_logs",
    }
    photo_level_actions = {
        "archives_photo_profile",
        "archives_photo_meta",
        "archives_comment_search",
        "archives_punish_status",
    }
    by_action = {item.action: item for item in [*photo_plan, *social_plan, *feedback_plan]}

    for action in user_level_actions:
        assert by_action[action].required_fields[0] == "user_id"
        assert by_action[action].depends_on == [_batch_source_id(1, 1, "archives_profile")]

    photo_anchor = _batch_source_id(1, 1, "photo")
    for action in photo_level_actions:
        assert by_action[action].depends_on == [photo_anchor]


def test_archives_broad_followup_respects_disabled_actions_without_source_coverage_side_effects():
    photo_plan, social_plan, feedback_plan = build_archives_broad_followup_source_plans(
        1,
        ["10001"],
        [_photo_observation()],
        window_start_ms=1000,
        window_end_ms=2000,
        disabled_actions={"archives_private_message_search", "archives_review_logs"},
    )

    actions = {item.action for item in [*photo_plan, *social_plan, *feedback_plan]}

    assert "archives_private_message_search" not in actions
    assert "archives_review_logs" not in actions
    assert "archives_photo_profile" in actions
    assert "archives_user_report_search" in actions
