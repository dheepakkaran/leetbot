"""Entry point: `python -m src.evening`. Nudges if today's problem is unsolved."""

from __future__ import annotations

import sys
from datetime import datetime
from typing import Any

from src.log_store import LogRow, latest_row_for_date, read_log, write_log
from src.messages import render_nudge
from src.runtime import Runtime, build_runtime, parse_args
from src.stats import compute_streak
from src.sync import run_sync


def evening_gate(now: datetime, tz: Any, evening_hour: int, rows: list[LogRow]) -> tuple[bool, str]:
    """At/after `evening_hour` local, today's UTC row exists, and no nudge sent yet.

    "At or after" (not "during") so a delayed or retried cron still nudges. The
    UTC-date row lookup ends the window at LeetCode's 00:00 UTC reset.
    """
    local = now.astimezone(tz)
    if local.hour < evening_hour:
        return False, f"too early: {local:%H:%M} local < {evening_hour:02d}:00"
    if local.date() != now.date():
        return False, f"LeetCode's day already rolled over ({local:%H:%M} local)"
    row = latest_row_for_date(rows, now.date().isoformat())
    if row is None:
        return False, f"no row for {now.date().isoformat()}"
    if row.nudge_sent:
        return False, "nudge already sent"
    return True, "ok"


def run_evening(rt: Runtime) -> int:
    """Sync, then send the nudge if today's problem is still open."""
    cfg = rt.cfg
    now = rt.now()
    today_iso = now.date().isoformat()
    rows = read_log(cfg.log_path)
    if not rt.force:
        ok, why = evening_gate(now, cfg.timezone, cfg.evening_local_hour, rows)
        if not ok:
            rt.log(f"[evening] skip: {why}")
            return 0

    rows = run_sync(rt)
    row = latest_row_for_date(rows, today_iso)
    if row is None:
        rt.log(f"[evening] skip: no row for {today_iso}")
        return 0
    if row.solved:
        rt.log(f"[evening] day {row.day} already solved")
        return 0

    username = cfg.leetcode_username
    user = rt.leetcode.get_user_stats(username)
    streak = compute_streak(user.calendar, now.date(), load_year=lambda y: rt.leetcode.get_calendar(username, y))
    rendered = render_nudge(
        frontend_id=row.frontend_id, title=row.title, slug=row.slug, streak=streak, now=now, tz=cfg.timezone
    )
    rt.telegram.send_message(rendered.text, rendered.buttons)
    row.nudge_sent = True
    if not rt.dry_run:
        write_log(cfg.log_path, rows)
    rt.commit_and_push(f"chore: day {row.day} nudge")
    return 0


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    args = parse_args("Evening nudge for an unsolved problem.", argv)
    return run_evening(build_runtime(args))


if __name__ == "__main__":
    sys.exit(main())
