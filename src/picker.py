"""Problem selection: official daily first, deterministic picker as fallback."""

from __future__ import annotations

import json
import random
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Callable

from src.leetcode_client import DailyChallenge, Problem
from src.log_store import LogRow


class PickerError(RuntimeError):
    """Raised when no problem can be selected at all."""


@dataclass(frozen=True)
class Pick:
    slug: str
    source: str           # daily | picker
    reason: str           # human-readable explanation for logs
    pattern: str | None = None


def slugify(name: str) -> str:
    """Topic name -> tag slug, e.g. 'Heap (Priority Queue)' -> 'heap-priority-queue'."""
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def daily_rejection(daily: DailyChallenge, logged: set[str], recent_ac: set[str]) -> str | None:
    """Why the official daily can't be used, or None if it can."""
    q = daily.question
    if q.paid_only:
        return "daily is premium"
    if q.slug in logged:
        return "daily already in log"
    if q.slug in recent_ac:
        return "daily already solved recently"
    return None


def least_covered_pattern(rows: list[LogRow], core_patterns: list[str]) -> str:
    """Core pattern with the fewest log rows; ties go to config order."""
    counts = {p: 0 for p in core_patterns}
    for row in rows:
        for slug in {slugify(name) for name in row.tag_list}:
            if slug in counts:
                counts[slug] += 1
    return min(core_patterns, key=lambda p: (counts[p], core_patterns.index(p)))


def _sort_key(p: Problem) -> tuple[int, str]:
    return (int(p.frontend_id) if p.frontend_id.isdigit() else 10**9, p.slug)


def pick_from_list(
    problems: list[Problem],
    *,
    difficulty: str,
    rows: list[LogRow],
    recent_ac: set[str],
    core_patterns: list[str],
    acrate_range: tuple[float, float] | None,
    utc_date: date,
) -> tuple[Problem, str, str]:
    """Run the fallback picker. Returns (problem, pattern_used, reason)."""
    logged = {r.slug for r in rows}
    fresh = [p for p in problems if not p.paid_only and p.slug not in logged and p.slug not in recent_ac]
    candidates = [p for p in fresh if p.difficulty == difficulty]
    reason_parts = [f"difficulty={difficulty}"]
    if not candidates:
        candidates = fresh
        reason_parts.append("no candidates at that difficulty, using any difficulty")
    if not candidates:
        raise PickerError("no unlogged, non-premium problems left")

    pattern = least_covered_pattern(rows, core_patterns)
    by_pattern = [p for p in candidates if pattern in p.tags]
    if by_pattern:
        pool, used = by_pattern, pattern
    else:
        core = set(core_patterns)
        any_core = [p for p in candidates if core & set(p.tags)]
        pool, used = (any_core, "any-core") if any_core else (candidates, "any")
    reason_parts.append(f"pattern={pattern} (used {used})")

    if acrate_range is not None:
        lo, hi = acrate_range
        in_range = [p for p in pool if lo <= p.ac_rate <= hi]
        if in_range:
            pool = in_range
            reason_parts.append(f"acRate in [{lo:g}, {hi:g}]")
        else:
            reason_parts.append("acRate range relaxed")

    rng = random.Random(f"{utc_date}")
    choice = rng.choice(sorted(pool, key=_sort_key))
    return choice, used, ", ".join(reason_parts)


def pick_problem(
    *,
    daily: DailyChallenge | None,
    load_problems: Callable[[], list[Problem]],
    rows: list[LogRow],
    recent_ac: set[str],
    difficulty_by_weekday: dict[int, str],
    core_patterns: list[str],
    acrate_ranges: dict[str, tuple[float, float]],
    utc_date: date,
    local_weekday: int,
) -> Pick:
    """Hybrid rule (§8): use the official daily unless premium/logged/recently
    solved, otherwise pick deterministically from the cached problem list.

    `load_problems` is only called when the fallback is needed.
    """
    logged = {r.slug for r in rows}
    if daily is not None:
        rejection = daily_rejection(daily, logged, recent_ac)
        if rejection is None:
            return Pick(slug=daily.question.slug, source="daily", reason="official daily")
    else:
        rejection = "daily unavailable"

    difficulty = difficulty_by_weekday[local_weekday]
    problem, pattern, reason = pick_from_list(
        load_problems(),
        difficulty=difficulty,
        rows=rows,
        recent_ac=recent_ac,
        core_patterns=core_patterns,
        acrate_range=acrate_ranges.get(difficulty),
        utc_date=utc_date,
    )
    return Pick(slug=problem.slug, source="picker", reason=f"{rejection}; {reason}", pattern=pattern)


# ---- problems.json cache ---------------------------------------------------


def load_problems_cache(path: Path) -> tuple[list[Problem], datetime | None]:
    """Read data/problems.json. Returns ([], None) if missing or unreadable."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        fetched_at = datetime.fromisoformat(raw["fetched_at"])
        return [Problem.from_dict(p) for p in raw["problems"]], fetched_at
    except (OSError, ValueError, KeyError, TypeError):
        return [], None


def cache_is_stale(fetched_at: datetime | None, now: datetime, max_age_days: int) -> bool:
    """True when the cache is missing or older than `max_age_days`."""
    return fetched_at is None or now - fetched_at > timedelta(days=max_age_days)


def save_problems_cache(path: Path, problems: list[Problem], source: str, now: datetime) -> None:
    """Write data/problems.json, one problem per line so git diffs stay small."""
    fetched = now.astimezone(timezone.utc).replace(microsecond=0).isoformat()
    lines = [json.dumps(p.to_dict(), ensure_ascii=False) for p in problems]
    body = (
        "{\n"
        f'"fetched_at": {json.dumps(fetched)},\n'
        f'"source": {json.dumps(source)},\n'
        f'"count": {len(problems)},\n'
        '"problems": [\n' + ",\n".join(lines) + "\n]\n}\n"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(body, encoding="utf-8")
    tmp.replace(path)
