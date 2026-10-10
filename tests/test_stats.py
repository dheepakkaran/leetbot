from datetime import date, datetime, timedelta, timezone

import pytest

from src.stats import (
    Snapshot,
    baseline_snapshot,
    compute_streak,
    format_duration,
    is_late,
    milestones,
    next_utc_midnight,
    previous_snapshot,
    upsert_snapshot,
    week_progress,
    week_recap,
)
from tests.conftest import epoch, make_row

TODAY = date(2026, 10, 14)  # Wednesday


def cal(*days: date) -> dict[int, int]:
    return {epoch(d.year, d.month, d.day): 2 for d in days}


def test_streak_including_today() -> None:
    c = cal(TODAY, TODAY - timedelta(1), TODAY - timedelta(2), TODAY - timedelta(4))
    assert compute_streak(c, TODAY) == 3


def test_streak_when_today_has_no_submission_yet() -> None:
    c = cal(TODAY - timedelta(1), TODAY - timedelta(2))
    assert compute_streak(c, TODAY) == 2


def test_streak_zero() -> None:
    assert compute_streak(cal(TODAY - timedelta(2)), TODAY) == 0
    assert compute_streak({}, TODAY) == 0


def test_streak_fixture_matches_owner_state() -> None:
    # Live calendar shape: last activity 2026-06-20, so the current streak is 0.
    owner = {1781654400: 1, 1781740800: 1, 1781827200: 5, 1781913600: 1}
    assert compute_streak(owner, date(2026, 10, 10)) == 0
    assert compute_streak(owner, date(2026, 6, 21)) == 4


def test_streak_crosses_new_year_by_loading_previous_year() -> None:
    today = date(2026, 1, 2)
    current = cal(date(2026, 1, 1), date(2026, 1, 2))
    loaded = []

    def load_year(y: int) -> dict[int, int]:
        loaded.append(y)
        return cal(date(2025, 12, 31), date(2025, 12, 30))

    assert compute_streak(current, today, load_year) == 4
    assert loaded == [2025]


def test_format_duration() -> None:
    assert format_duration(timedelta(minutes=38)) == "38 min"
    assert format_duration(timedelta(hours=3, minutes=12)) == "3 h 12 min"
    assert format_duration(timedelta(hours=3)) == "3 h"
    assert format_duration(timedelta(days=2, hours=1)) == "2 days"
    assert format_duration(timedelta(days=1, hours=1)) == "1 day"
    assert format_duration(timedelta(seconds=20)) == "1 min"


def test_is_late_and_reset() -> None:
    assert not is_late("2026-10-12", datetime(2026, 10, 12, 23, 59, 59, tzinfo=timezone.utc))
    assert is_late("2026-10-12", datetime(2026, 10, 13, 0, 0, tzinfo=timezone.utc))
    assert next_utc_midnight(datetime(2026, 10, 12, 22, 3, tzinfo=timezone.utc)) == datetime(2026, 10, 13, tzinfo=timezone.utc)


def test_week_progress_bar() -> None:
    rows = [
        make_row(1, "2026-10-11", solved=True),   # previous ISO week (Sunday)
        make_row(2, "2026-10-12", solved=True),   # Monday
        make_row(3, "2026-10-13", solved=False),  # Tuesday
        make_row(4, "2026-10-14", solved=True),   # Wednesday
    ]
    assert week_progress(rows, TODAY) == (2, "▰▱▰▱▱▱▱")


def snap(d: str, total: int, streak: int = 0, ranking: int | None = 1000) -> Snapshot:
    return Snapshot(d, total, total // 2, total - total // 2, 0, ranking, streak)


@pytest.mark.parametrize(
    "prev, cur, expected",
    [
        (snap("2026-10-13", 99), snap("2026-10-14", 101), ["100 problems solved on LeetCode!"]),
        (snap("2026-10-13", 67), snap("2026-10-14", 68), []),
        (snap("2026-10-13", 67, streak=6), snap("2026-10-14", 68, streak=7), ["7-day streak!"]),
        (snap("2026-10-13", 67, streak=7), snap("2026-10-14", 67, streak=7), []),
        (None, snap("2026-10-14", 100, streak=7), []),
    ],
)
def test_milestones(prev, cur, expected) -> None:
    assert milestones(prev, cur, 50, [7, 30, 50, 100]) == expected


def test_snapshot_history_helpers() -> None:
    history = [snap("2026-10-01", 60), snap("2026-10-07", 64), snap("2026-10-10", 66)]
    history = upsert_snapshot(history, snap("2026-10-14", 70))
    history = upsert_snapshot(history, snap("2026-10-14", 71))  # same date replaced
    assert [s.date for s in history] == ["2026-10-01", "2026-10-07", "2026-10-10", "2026-10-14"]
    assert history[-1].total == 71
    assert previous_snapshot(history, "2026-10-14").date == "2026-10-10"
    assert baseline_snapshot(history, TODAY).date == "2026-10-07"
    assert baseline_snapshot(history[2:], TODAY).date == "2026-10-10"  # oldest available


def test_week_recap() -> None:
    sunday = date(2026, 10, 18)
    rows = [
        make_row(1, "2026-10-10", difficulty="Easy", solved=True,
                 sent_at="2026-10-10T12:20:00Z", solved_at="2026-10-10T12:30:00Z"),   # outside window
        make_row(2, "2026-10-12", difficulty="Easy", solved=True,
                 sent_at="2026-10-12T12:20:00Z", solved_at="2026-10-12T13:00:00Z"),
        make_row(3, "2026-10-13", difficulty="Medium", solved=True,
                 sent_at="2026-10-13T12:20:00Z", solved_at="2026-10-13T16:00:00Z"),
        make_row(4, "2026-10-14", difficulty="Hard", solved=False),
    ]
    history = [snap("2026-10-11", 67, ranking=2_266_342), snap("2026-10-18", 70, ranking=2_250_000)]
    recap = week_recap(rows, sunday, history[-1], history)
    assert recap["solved"] == 2 and (recap["easy"], recap["medium"], recap["hard"]) == (1, 1, 0)
    assert recap["total_delta"] == 3 and recap["rank_delta"] == -16_342
    assert recap["fastest"] == {"frontend_id": "102", "duration": "40 min"}
