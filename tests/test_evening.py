from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pytest

from src.evening import evening_gate, run_evening
from src.log_store import read_log, write_log
from tests.conftest import make_row

TZ = ZoneInfo("America/New_York")


def cron_times(day: str) -> list[datetime]:
    """The evening.yml schedule: 22:03, 23:03 and 23:33 UTC."""
    y, m, d = map(int, day.split("-"))
    return [datetime(y, m, d, h, mi, tzinfo=timezone.utc) for h, mi in ((22, 3), (23, 3), (23, 33))]


def runs_that_nudge(day: str, times: list[datetime]) -> list[int]:
    rows = [make_row(1, day)]
    passed = []
    for i, now in enumerate(times):
        ok, _ = evening_gate(now, TZ, 18, rows)
        if ok:
            passed.append(i)
            rows[0].nudge_sent = True
    return passed


@pytest.mark.parametrize("day, nudging_cron", [("2026-07-15", 0), ("2026-01-15", 1)])  # EDT, EST
def test_exactly_one_cron_nudges(day: str, nudging_cron: int) -> None:
    assert runs_that_nudge(day, cron_times(day)) == [nudging_cron]


@pytest.mark.parametrize("day", ["2026-07-15", "2026-01-15"])
def test_dropped_run_is_retried(day: str) -> None:
    times = cron_times(day)
    assert runs_that_nudge(day, times[2:]) == [0]  # only the 23:33 UTC run happens


def test_gate_reasons() -> None:
    day = "2026-07-15"
    early = datetime(2026, 7, 15, 21, 30, tzinfo=timezone.utc)  # 17:30 EDT
    assert evening_gate(early, TZ, 18, [make_row(1, day)])[1].startswith("too early")
    late = datetime(2026, 7, 15, 22, 3, tzinfo=timezone.utc)
    assert "no row" in evening_gate(late, TZ, 18, [make_row(1, "2026-07-14")])[1]
    assert "already sent" in evening_gate(late, TZ, 18, [make_row(1, day, nudge_sent=True)])[1]
    after_reset = datetime(2026, 7, 16, 0, 30, tzinfo=timezone.utc)  # 20:30 EDT, new LeetCode day
    assert not evening_gate(after_reset, TZ, 18, [make_row(1, day)])[0]
    # Even if tomorrow's problem was already issued tonight, don't nudge about it yet.
    ok, why = evening_gate(after_reset, TZ, 18, [make_row(1, day), make_row(2, "2026-07-16")])
    assert not ok and "rolled over" in why


def test_run_evening_sends_nudge_once(cfg, fakes, make_runtime) -> None:
    lc, _, tg = fakes
    write_log(cfg.log_path, [make_row(1, "2026-07-15", title="Two & Sum")])
    rt = make_runtime(datetime(2026, 7, 15, 22, 3, tzinfo=timezone.utc))
    assert run_evening(rt) == 0
    [msg] = tg.sent
    assert msg["text"].startswith("⏰ <b>Still pending: #101</b>\nTwo &amp; Sum")
    assert "1 h 57 min left" in msg["text"] and "(8:00 PM)" in msg["text"]
    assert read_log(cfg.log_path)[0].nudge_sent
    assert rt.commits == ["chore: day 1 nudge"]

    run_evening(make_runtime(datetime(2026, 7, 15, 23, 3, tzinfo=timezone.utc)))
    assert len(tg.sent) == 1  # retry cron doesn't nudge twice


def test_run_evening_skips_solved(cfg, fakes, make_runtime) -> None:
    lc, _, tg = fakes
    write_log(cfg.log_path, [make_row(1, "2026-07-15", solved=True, solved_at="2026-07-15T13:00:00Z")])
    run_evening(make_runtime(datetime(2026, 7, 15, 22, 3, tzinfo=timezone.utc)))
    assert tg.sent == []
