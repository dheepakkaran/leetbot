from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest

from src.leetcode_client import DailyChallenge, Problem, QuestionSummary, Tag
from src.picker import (
    PickerError,
    cache_is_stale,
    least_covered_pattern,
    load_problems_cache,
    pick_from_list,
    pick_problem,
    save_problems_cache,
    slugify,
)
from tests.conftest import make_row

WEEKDAYS = {0: "Easy", 1: "Medium", 2: "Medium", 3: "Easy", 4: "Medium", 5: "Hard", 6: "Medium"}
CORE = ["array", "hash-table", "two-pointers", "stack", "binary-search", "dynamic-programming"]
RANGES = {"Easy": (45.0, 100.0), "Medium": (35.0, 75.0), "Hard": (0.0, 100.0)}
TODAY = date(2026, 10, 12)  # a Monday


def daily(slug: str = "daily-one", paid: bool = False) -> DailyChallenge:
    return DailyChallenge("2026-10-12", f"/problems/{slug}/", QuestionSummary("9", "Daily", slug, "Medium", paid, [Tag("Array", "array")]))


def problems() -> list[Problem]:
    return [
        Problem("1", "A", "a", "Easy", 60.0, False, ["array"]),
        Problem("2", "B", "b", "Easy", 50.0, False, ["hash-table"]),
        Problem("3", "C", "c", "Easy", 70.0, True, ["stack"]),          # premium
        Problem("4", "D", "d", "Easy", 20.0, False, ["stack"]),         # low acRate
        Problem("5", "E", "e", "Medium", 50.0, False, ["two-pointers"]),
        Problem("6", "F", "f", "Hard", 30.0, False, ["dynamic-programming"]),
        Problem("7", "G", "g", "Easy", 80.0, False, ["math"]),          # no core tag
        Problem("8", "H", "h", "Easy", 65.0, False, ["array", "stack"]),
    ]


def pick(**kw):
    args = dict(
        daily=daily(),
        load_problems=problems,
        rows=[],
        recent_ac=set(),
        difficulty_by_weekday=WEEKDAYS,
        core_patterns=CORE,
        acrate_ranges=RANGES,
        utc_date=TODAY,
        local_weekday=0,
    )
    args.update(kw)
    return pick_problem(**args)


def test_uses_daily_when_fresh() -> None:
    called = []
    result = pick(load_problems=lambda: called.append(1) or problems())
    assert (result.slug, result.source) == ("daily-one", "daily")
    assert called == []  # list not needed


@pytest.mark.parametrize(
    "kw",
    [
        {"daily": daily(paid=True)},
        {"rows": [make_row(1, "2026-10-01", slug="daily-one")]},
        {"recent_ac": {"daily-one"}},
        {"daily": None},
    ],
)
def test_daily_rejected_falls_back_to_picker(kw) -> None:
    result = pick(**kw)
    assert result.source == "picker"
    assert result.slug != "daily-one"


def test_picker_respects_premium_log_and_recent_ac() -> None:
    rows = [make_row(1, "2026-10-01", slug="a")]
    for seed_day in range(30):
        result = pick(daily=None, rows=rows, recent_ac={"b"}, utc_date=TODAY + timedelta(days=7 * seed_day))
        assert result.slug not in {"a", "b", "c"}


def test_weekday_difficulty() -> None:
    assert pick(daily=None, local_weekday=1).slug == "e"   # Tuesday -> Medium
    assert pick(daily=None, local_weekday=5).slug == "f"   # Saturday -> Hard
    easy = {p.slug for p in problems() if p.difficulty == "Easy"}
    assert pick(daily=None, local_weekday=0).slug in easy


def test_least_covered_pattern_ties_by_config_order() -> None:
    assert least_covered_pattern([], CORE) == "array"
    rows = [make_row(1, "2026-10-01", tags="Array; Hash Table"), make_row(2, "2026-10-02", tags="Two Pointers")]
    assert least_covered_pattern(rows, CORE) == "stack"
    assert slugify("Heap (Priority Queue)") == "heap-priority-queue"


def test_picker_filters_by_least_covered_pattern() -> None:
    rows = [make_row(1, "2026-10-01", slug="zz", tags="Array")]
    # array covered once -> hash-table is next -> only "b" is Easy+hash-table
    assert pick(daily=None, rows=rows).slug == "b"


def test_deterministic_per_date() -> None:
    a = pick(daily=None)
    b = pick(daily=None)
    assert a == b
    seen = {pick(daily=None, utc_date=TODAY + timedelta(days=7 * i)).slug for i in range(20)}
    assert len(seen) > 1  # different dates can give different picks


def test_fallback_cascade_any_core_then_any_then_relaxed() -> None:
    probs = [
        Problem("1", "A", "a", "Easy", 10.0, False, ["math"]),       # no core tag, low acRate
    ]
    problem, used, reason = pick_from_list(
        probs, difficulty="Easy", rows=[], recent_ac=set(), core_patterns=CORE,
        acrate_range=(45, 100), utc_date=TODAY,
    )
    assert problem.slug == "a" and used == "any" and "relaxed" in reason

    probs.append(Problem("2", "B", "b", "Easy", 10.0, False, ["stack"]))
    problem, used, _ = pick_from_list(
        probs, difficulty="Easy", rows=[], recent_ac=set(), core_patterns=CORE,
        acrate_range=(45, 100), utc_date=TODAY,
    )
    assert problem.slug == "b" and used == "any-core"   # least-covered "array" has none


def test_acrate_preferred_over_out_of_range() -> None:
    probs = [
        Problem("1", "A", "a", "Easy", 10.0, False, ["array"]),
        Problem("2", "B", "b", "Easy", 60.0, False, ["array"]),
    ]
    for i in range(10):
        problem, _, _ = pick_from_list(
            probs, difficulty="Easy", rows=[], recent_ac=set(), core_patterns=CORE,
            acrate_range=(45, 100), utc_date=TODAY + timedelta(days=i),
        )
        assert problem.slug == "b"


def test_no_candidates_at_difficulty_uses_any_difficulty() -> None:
    probs = [Problem("5", "E", "e", "Medium", 50.0, False, ["array"])]
    problem, _, reason = pick_from_list(
        probs, difficulty="Hard", rows=[], recent_ac=set(), core_patterns=CORE, acrate_range=None, utc_date=TODAY,
    )
    assert problem.slug == "e" and "any difficulty" in reason


def test_nothing_left_raises() -> None:
    with pytest.raises(PickerError):
        pick_from_list([], difficulty="Easy", rows=[], recent_ac=set(), core_patterns=CORE, acrate_range=None, utc_date=TODAY)


def test_problems_cache_roundtrip_and_staleness(tmp_path: Path) -> None:
    path = tmp_path / "problems.json"
    assert load_problems_cache(path) == ([], None)
    now = datetime(2026, 10, 12, 12, tzinfo=timezone.utc)
    save_problems_cache(path, problems(), "questionList", now)
    loaded, fetched = load_problems_cache(path)
    assert loaded == problems()
    assert fetched == now
    assert not cache_is_stale(fetched, now + timedelta(days=6), 7)
    assert cache_is_stale(fetched, now + timedelta(days=8), 7)
    assert cache_is_stale(None, now, 7)
