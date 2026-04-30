from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

# GameClock, DownAndDistance, TeamScore, OCREvent.


class GameClock(BaseModel):
    model_config = ConfigDict(extra="forbid")
    quarter: int = Field(ge=1, le=5)
    time_remaining_seconds: int = Field(ge=0, le=900)


class DownAndDistance(BaseModel):
    model_config = ConfigDict(extra="forbid")
    down: int = Field(ge=1, le=4)
    distance: int = Field(ge=0, le=99)


class TeamScore(BaseModel):
    model_config = ConfigDict(extra="forbid")
    team_code: str = Field(min_length=2, max_length=3)
    score: int = Field(ge=0)


class OCREvent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_event_id: str = Field(min_length=1)
    game_id: str = Field(min_length=1)
    occurred_at: datetime | None = None
    clock: GameClock | None = None
    down_and_distance: DownAndDistance | None = None
    home: TeamScore | None = None
    away: TeamScore | None = None
    play_description: str | None = None
    raw_ocr_text: str = Field(min_length=1)


def time_string_to_seconds(time_str: str) -> int:
    """
    Converts MM:SS -> to game-clock string of time left in the game (01:30 -> 90)

    Raises:
    ValueError: if the input is malformed or out of valid ranges.
    """
    pieces = time_str.split(":")
    if len(pieces) != 2:
        raise ValueError(f"invalid time string {time_str!r}: expected format 'MM:SS'")

    minutes = int(pieces[0])
    seconds = int(pieces[1])

    if minutes < 0:
        raise ValueError(f"invalid time string {time_str!r}: minutes must be non-negative")
    if not (0 <= seconds < 60):
        raise ValueError(f"invalid time string {time_str!r}: seconds must be 0-59")

    return minutes * 60 + seconds
