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
    """Local hour == `evening_hour`, today's row exists, and no nudge sent yet."""
    local = now.astimezone(tz)
    if local.hour != evening_hour:
        return False, f"not evening: {local:%H:%M} local (want {evening_hour:02d}:xx)"
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
