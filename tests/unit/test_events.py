"""Unit tests for OCR event domain models and parsing helpers.

These tests exercise pure logic: no IO, no database. They run in
milliseconds and form the fast feedback loop during development.
"""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from sim_league_platform.domain.events import (
    DownAndDistance,
    GameClock,
    OCREvent,
    TeamScore,
    time_string_to_seconds,
)


def test_gameclock_valid() -> None:
    """A valid GameClock can be constructed."""
    clock = GameClock(quarter=1, time_remaining_seconds=100)
    assert clock.quarter == 1
    assert clock.time_remaining_seconds == 100


def test_gameclock_quarter_below_range_raises() -> None:
    with pytest.raises(ValidationError):
        GameClock(quarter=0, time_remaining_seconds=600)


def test_gameclock_quarter_above_range_raises() -> None:
    with pytest.raises(ValidationError):
        GameClock(quarter=10, time_remaining_seconds=600)


def test_gameclock_negative_seconds_raises() -> None:
    with pytest.raises(ValidationError):
        GameClock(quarter=1, time_remaining_seconds=-1)


def test_gameclock_extra_field_forbidden() -> None:
    with pytest.raises(ValidationError):
        GameClock(quarter=1, time_remaining_seconds=400, kickoff_time="1:00")  # type: ignore[call-arg]


def test_down_and_distance_valid() -> None:
    """A valid DownAndDistance can be constructed."""
    down_and_distance = DownAndDistance(down=1, distance=10)
    assert down_and_distance.down == 1
    assert down_and_distance.distance == 10


def test_down_below_range_raises() -> None:
    with pytest.raises(ValidationError):
        DownAndDistance(down=0, distance=10)


def test_down_above_range_raises() -> None:
    with pytest.raises(ValidationError):
        DownAndDistance(down=5, distance=10)


def test_distance_above_range_raises() -> None:
    with pytest.raises(ValidationError):
        DownAndDistance(down=1, distance=100)


def test_distance_below_range_raises() -> None:
    with pytest.raises(ValidationError):
        DownAndDistance(down=1, distance=-1)


def test_down_and_distance_extra_field_forbidden() -> None:
    with pytest.raises(ValidationError):
        DownAndDistance(down=1, distance=10, formation="I")  # type: ignore[call-arg]


def test_team_score_valid() -> None:
    """A valid TeamScore can be constructed."""
    team_score = TeamScore(team_code="IND", score=10)
    assert team_score.team_code == "IND"
    assert team_score.score == 10


def test_team_score_team_code_below_range_raises() -> None:
    with pytest.raises(ValidationError):
        TeamScore(team_code="I", score=10)


def test_team_score_team_code_above_range_raises() -> None:
    with pytest.raises(ValidationError):
        TeamScore(team_code="INDY", score=10)


def test_team_score_score_below_range_raises() -> None:
    with pytest.raises(ValidationError):
        TeamScore(team_code="IND", score=-1)


def test_team_score_extra_field_forbidden() -> None:
    with pytest.raises(ValidationError):
        TeamScore(team_code="IND", score=10, margin=10)  # type: ignore[call-arg]


def test_ocrevent_full_population() -> None:
    """An OCREvent with every field populated round-trips cleanly."""
    event = OCREvent(
        source_event_id="frame-001",
        game_id="game-42",
        occurred_at=datetime(2026, 4, 28, 14, 30, tzinfo=UTC),
        clock=GameClock(quarter=2, time_remaining_seconds=600),
        down_and_distance=DownAndDistance(down=3, distance=7),
        home=TeamScore(team_code="KC", score=14),
        away=TeamScore(team_code="SF", score=10),
        play_description="QB sneak for 2 yards",
        raw_ocr_text="2nd & 7 KC 14 SF 10 12:34 Q2",
    )
    assert event.source_event_id == "frame-001"
    assert event.game_id == "game-42"

    # Nested fields require None-narrowing for mypy strict
    assert event.clock is not None
    assert event.clock.quarter == 2

    assert event.down_and_distance is not None
    assert event.down_and_distance.down == 3

    assert event.home is not None
    assert event.home.team_code == "KC"
    assert event.home.score == 14

    assert event.away is not None
    assert event.away.team_code == "SF"


def test_ocrevent_minimal_population() -> None:
    """An OCREvent with only required fields defaults optional fields to None."""
    event = OCREvent(
        source_event_id="frame-001",
        game_id="game-42",
        raw_ocr_text="some OCR text",
    )
    assert event.occurred_at is None
    assert event.clock is None
    assert event.down_and_distance is None
    assert event.home is None
    assert event.away is None
    assert event.play_description is None


def test_ocrevent_empty_source_event_id_raises() -> None:
    with pytest.raises(ValidationError):
        OCREvent(
            source_event_id="",
            game_id="game-42",
            raw_ocr_text="some text",
        )


def test_ocrevent_empty_raw_ocr_text_raises() -> None:
    with pytest.raises(ValidationError):
        OCREvent(
            source_event_id="frame-001",
            game_id="game-42",
            raw_ocr_text="",
        )


def test_ocrevent_extra_field_forbidden() -> None:
    with pytest.raises(ValidationError):
        OCREvent(
            source_event_id="frame-001",
            game_id="game-42",
            raw_ocr_text="some text",
            weather="sunny",  # type: ignore[call-arg]
        )


def test_ocrevent_roundtrip() -> None:
    """Dumping and re-validating an OCREvent produces an equivalent object."""
    original = OCREvent(
        source_event_id="frame-001",
        game_id="game-42",
        occurred_at=datetime(2026, 4, 28, 14, 30, tzinfo=UTC),
        clock=GameClock(quarter=2, time_remaining_seconds=600),
        home=TeamScore(team_code="KC", score=14),
        away=TeamScore(team_code="SF", score=10),
        raw_ocr_text="some text",
    )

    dumped = original.model_dump()
    reconstructed = OCREvent.model_validate(dumped)

    assert reconstructed == original
    # Spot-check a nested field survived the round trip
    assert reconstructed.home is not None
    assert reconstructed.home.team_code == "KC"


@pytest.mark.parametrize(
    "time_str,expected",
    [
        ("0:00", 0),
        ("0:01", 1),
        ("1:00", 60),
        ("12:34", 754),
        ("15:00", 900),
    ],
)
def test_time_string_to_seconds_valid(time_str: str, expected: int) -> None:
    assert time_string_to_seconds(time_str) == expected


@pytest.mark.parametrize(
    "bad_input",
    [
        "",
        "12",
        "12:34:56",
        "12:60",
        "-5:00",
        "abc:def",
    ],
)
def test_time_string_to_seconds_invalid_raises(bad_input: str) -> None:
    with pytest.raises(ValueError):
        time_string_to_seconds(bad_input)
