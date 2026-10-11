"""Streak, week progress, snapshots, deltas, durations and milestones."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

from src.log_store import LogRow

SOLVED_MARK = "▰"
OPEN_MARK = "▱"


# ---- time helpers ------------------------------------------------------------


def to_iso(dt: datetime) -> str:
    """ISO8601 UTC with a `Z` suffix, second precision."""
    return dt.astimezone(timezone.utc).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_iso(value: str) -> datetime:
    """Parse an ISO8601 timestamp (with `Z` or offset) into an aware UTC datetime."""
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def from_epoch(seconds: int) -> datetime:
    """Epoch seconds -> aware UTC datetime."""
    return datetime.fromtimestamp(int(seconds), tz=timezone.utc)


def next_utc_midnight(now: datetime) -> datetime:
    """The next 00:00 UTC strictly after `now` (LeetCode's daily reset)."""
    today = now.astimezone(timezone.utc).date()
    return datetime.combine(today + timedelta(days=1), time(0), tzinfo=timezone.utc)


def is_late(utc_date: str, solved_at: datetime) -> bool:
    """True if `solved_at` is after the end of the row's UTC issue date."""
    end = datetime.combine(date.fromisoformat(utc_date) + timedelta(days=1), time(0), tzinfo=timezone.utc)
    return solved_at >= end


def format_duration(delta: timedelta) -> str:
    """`38 min`, `3 h 12 min`, `3 h` or `2 days`."""
    minutes = max(int(delta.total_seconds() // 60), 0)
    if minutes < 60:
        return f"{max(minutes, 1)} min"
    if minutes < 24 * 60:
        hours, mins = divmod(minutes, 60)
        return f"{hours} h {mins} min" if mins else f"{hours} h"
    days = minutes // (24 * 60)
    return "1 day" if days == 1 else f"{days} days"


# ---- streak ------------------------------------------------------------------


def calendar_by_date(calendar: dict[int, int]) -> dict[date, int]:
    """Epoch-keyed calendar -> UTC-date-keyed calendar."""
    out: dict[date, int] = {}
    for epoch, count in calendar.items():
        d = from_epoch(epoch).date()
        out[d] = out.get(d, 0) + count
    return out


def compute_streak(
    calendar: dict[int, int],
    today: date,
    load_year: Callable[[int], dict[int, int]] | None = None,
) -> int:
    """Consecutive UTC days with submissions, ending today (or yesterday if
    today has none yet). Loads the previous year's calendar when the streak
    reaches Jan 1.
    """
    days = calendar_by_date(calendar)
    loaded: set[int] = set()

    def active(d: date) -> bool:
        return days.get(d, 0) > 0

    cursor = today if active(today) else today - timedelta(days=1)
    streak = 0
    while active(cursor):
        streak += 1
        if cursor.month == 1 and cursor.day == 1 and load_year and cursor.year - 1 not in loaded:
            loaded.add(cursor.year - 1)
            for d, c in calendar_by_date(load_year(cursor.year - 1)).items():
                days[d] = max(days.get(d, 0), c)
        cursor -= timedelta(days=1)
    return streak


# ---- snapshots ---------------------------------------------------------------


@dataclass(frozen=True)
class Snapshot:
    date: str
    total: int
    easy: int
    medium: int
    hard: int
    ranking: int | None
    streak: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Snapshot":
        return cls(
            date=str(d["date"]),
            total=int(d["total"]),
            easy=int(d["easy"]),
            medium=int(d["medium"]),
            hard=int(d["hard"]),
            ranking=int(d["ranking"]) if d.get("ranking") else None,
            streak=int(d.get("streak") or 0),
        )


def load_history(path: Path) -> list[Snapshot]:
    """Read data/stats_history.json (empty list if missing)."""
    if not path.exists():
        return []
    return [Snapshot.from_dict(d) for d in json.loads(path.read_text(encoding="utf-8") or "[]")]


def save_history(path: Path, history: list[Snapshot]) -> None:
    """Write data/stats_history.json, one snapshot per line."""
    body = "[\n" + ",\n".join(json.dumps(s.to_dict()) for s in history) + ("\n" if history else "") + "]\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def upsert_snapshot(history: list[Snapshot], snap: Snapshot) -> list[Snapshot]:
    """Append `snap`, replacing an existing snapshot for the same date."""
    kept = [s for s in history if s.date != snap.date]
    return sorted(kept + [snap], key=lambda s: s.date)


def previous_snapshot(history: list[Snapshot], today: str) -> Snapshot | None:
    """Latest snapshot strictly before `today`."""
    earlier = [s for s in history if s.date < today]
    return earlier[-1] if earlier else None


def baseline_snapshot(history: list[Snapshot], today: date, days: int = 7) -> Snapshot | None:
    """Snapshot from `days` days earlier (or the latest before it), else the oldest available."""
    cutoff = (today - timedelta(days=days)).isoformat()
    at_or_before = [s for s in history if s.date <= cutoff]
    if at_or_before:
        return at_or_before[-1]
    return history[0] if history else None


# ---- week progress / recap -----------------------------------------------------


def iso_week_dates(d: date) -> list[date]:
    """Monday..Sunday of the ISO week containing `d`."""
    monday = d - timedelta(days=d.weekday())
    return [monday + timedelta(days=i) for i in range(7)]


def week_progress(rows: list[LogRow], today: date) -> tuple[int, str]:
    """(solved rows this ISO week, 7-char bar with one mark per weekday)."""
    week = iso_week_dates(today)
    in_week = [r for r in rows if r.solved and date.fromisoformat(r.date) in week]
    solved_dates = {date.fromisoformat(r.date) for r in in_week}
    bar = "".join(SOLVED_MARK if d in solved_dates else OPEN_MARK for d in week)
    return len(in_week), bar


def week_recap(rows: list[LogRow], today: date, current: Snapshot, history: list[Snapshot]) -> dict[str, Any]:
    """Sunday recap over the 7 UTC days before `today`, with deltas vs the
    snapshot from 7 days earlier (or the oldest available)."""
    start, end = today - timedelta(days=7), today - timedelta(days=1)
    window = [r for r in rows if start <= date.fromisoformat(r.date) <= end]
    solved = [r for r in window if r.solved]
    base = baseline_snapshot([s for s in history if s.date < today.isoformat()], today) or current
    rank_delta = None
    if current.ranking is not None and base.ranking is not None:
        rank_delta = current.ranking - base.ranking

    fastest = None
    timed = [r for r in solved if r.sent_at and r.solved_at]
    if timed:
        best = min(timed, key=lambda r: parse_iso(r.solved_at) - parse_iso(r.sent_at))
        fastest = {
            "frontend_id": best.frontend_id,
            "duration": format_duration(parse_iso(best.solved_at) - parse_iso(best.sent_at)),
        }
    return {
        "solved": len(solved),
        "easy": sum(1 for r in solved if r.difficulty == "Easy"),
        "medium": sum(1 for r in solved if r.difficulty == "Medium"),
        "hard": sum(1 for r in solved if r.difficulty == "Hard"),
        "total": current.total,
        "total_delta": current.total - base.total,
        "rank_delta": rank_delta,
        "fastest": fastest,
    }


# ---- milestones ----------------------------------------------------------------


def milestones(
    previous: Snapshot | None, current: Snapshot, solved_every: int, streak_days: list[int]
) -> list[str]:
    """Milestones reached since the previous snapshot (none without one)."""
    if previous is None:
        return []
    out = []
    if solved_every > 0 and current.total // solved_every > previous.total // solved_every:
        out.append(f"{current.total // solved_every * solved_every} problems solved on LeetCode!")
    if current.streak in streak_days and current.streak != previous.streak:
        out.append(f"{current.streak}-day streak!")
    return out
