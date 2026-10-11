"""All Telegram message rendering (HTML parse mode).

Morning messages and their "solved" edits are rendered from the same saved
context (`data/messages/{date}.json`) by the same function.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from html import escape as _html_escape
from typing import Any
from zoneinfo import ZoneInfo

from src.stats import format_duration, next_utc_midnight, parse_iso

MAX_LEN = 4096
HINT_LIMITS = (400, 200, 80)
MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")

CLOSING_NORMAL = "Do it asap."
CLOSING_MISSED = "Yesterday slipped. Today gets you back on track."
CLOSING_SUNDAY = "New week. Do it asap."
CLOSING_SOLVED = "Done. See you tomorrow."
NO_SOLUTION_LINE = "📘 Solution unavailable today. Rerun from Actions."

Buttons = list[list[dict[str, str]]]


def escape(text: str) -> str:
    """html.escape for text nodes (quotes stay readable; Telegram needs only <, >, &)."""
    return _html_escape(text, quote=False)


def escape_attr(text: str) -> str:
    """html.escape for attribute values such as href."""
    return _html_escape(text, quote=True)


@dataclass(frozen=True)
class Rendered:
    text: str
    buttons: Buttons


@dataclass(frozen=True)
class SolvedInfo:
    solved_at: str       # ISO8601 UTC
    late: bool
    submission_id: str
    sent_at: str         # ISO8601 UTC


# ---- small formatters ----------------------------------------------------------


def format_clock(dt: datetime) -> str:
    """`8:00 PM` (locale-independent)."""
    hour = dt.hour % 12 or 12
    return f"{hour}:{dt.minute:02d} {'AM' if dt.hour < 12 else 'PM'}"


def format_month_day(dt: datetime) -> str:
    """`Oct 11` (locale-independent)."""
    return f"{MONTHS[dt.month - 1]} {dt.day}"


def plural_days(n: int) -> str:
    return "1 day" if n == 1 else f"{n} days"


def _truncate(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def submission_url(submission_id: str) -> str:
    return f"https://leetcode.com/submissions/detail/{submission_id}/"


def choose_variant(*, has_solution: bool, missed: bool, sunday: bool) -> str:
    """Primary variant label for logs/context: no_solution > sunday > missed > normal."""
    if not has_solution:
        return "no_solution"
    if sunday:
        return "sunday"
    if missed:
        return "missed"
    return "normal"


# ---- morning message -----------------------------------------------------------


def _yesterday_line(yesterday: dict[str, Any] | None) -> str | None:
    if not yesterday:
        return None
    pid = escape(str(yesterday["frontend_id"]))
    status = yesterday["status"]
    if status == "solved":
        return f"✅ Yesterday: #{pid} solved"
    if status == "late":
        return f"✅ Yesterday: #{pid} solved late"
    return f"❌ Yesterday: #{pid} not solved · streak reset"


def _ranking(value: int | None) -> str:
    return f"{value:,}" if value else "—"


def _stats_block(stats: dict[str, Any]) -> str:
    return (
        "<blockquote expandable>📊 <b>Your LeetCode</b>\n"
        f"Solved {stats['total']} · Easy {stats['easy']} · Medium {stats['medium']} · Hard {stats['hard']}\n"
        f"Ranking {_ranking(stats.get('ranking'))} · Active days {stats['active_days']}</blockquote>"
    )


def _recap_block(recap: dict[str, Any]) -> str:
    rank_delta = recap.get("rank_delta")
    if rank_delta is None:
        ranking = "Ranking —"
    else:
        arrow = "↑" if rank_delta < 0 else ("↓" if rank_delta > 0 else "→")
        ranking = f"Ranking {arrow} {abs(rank_delta):,}"
    lines = [
        "<blockquote expandable>📊 <b>Week recap</b>",
        f"Solved {recap['solved']}/7 · Easy {recap['easy']} · Medium {recap['medium']} · Hard {recap['hard']}",
        f"Total {recap['total']} ({recap['total_delta']:+d}) · {ranking}",
    ]
    fastest = recap.get("fastest")
    if recap["solved"] and fastest:
        lines.append(f"Fastest: #{escape(str(fastest['frontend_id']))} in {escape(fastest['duration'])} after alert")
    return "\n".join(lines) + "</blockquote>"


def _status_line(solved: SolvedInfo, tz: ZoneInfo) -> str:
    solved_at = parse_iso(solved.solved_at)
    if solved.late:
        return f"✅ <b>Solved late · {format_month_day(solved_at.astimezone(tz))}</b>"
    duration = format_duration(solved_at - parse_iso(solved.sent_at))
    return f"✅ <b>Solved at {format_clock(solved_at.astimezone(tz))} · {duration} after alert</b>"


def _closing(ctx: dict[str, Any], solved: SolvedInfo | None) -> str:
    if solved:
        return CLOSING_SOLVED
    if ctx.get("missed"):
        return CLOSING_MISSED
    if ctx.get("sunday"):
        return CLOSING_SUNDAY
    return CLOSING_NORMAL


def _morning_text(ctx: dict[str, Any], tz: ZoneInfo, solved: SolvedInfo | None, hint_limit: int) -> str:
    p, lang, stats = ctx["problem"], ctx["language"], ctx["stats"]
    tags = ", ".join(p.get("tags", [])[:3])
    meta = [escape(p["difficulty"])] + ([escape(tags)] if tags else [])
    meta.append(f"Solve in {escape(lang['display'])} ({lang['k']}/{lang['block_size']})")

    lines = [
        f"☀️ <b>{escape(ctx['greeting'])} · Day {ctx['day']}</b>",
        f"Today: #{escape(str(p['frontend_id']))} {escape(_truncate(p['title'], 200))}",
        " · ".join(meta),
    ]
    if solved:
        lines.append(_status_line(solved, tz))
    lines.append("")
    yesterday = _yesterday_line(ctx.get("yesterday"))
    if yesterday:
        lines.append(yesterday)
    week = ctx["week"]
    lines.append(f"🔥 Streak {plural_days(stats['streak'])} · Week {week['solved']}/7 {week['bar']}")
    for milestone in ctx.get("milestones") or []:
        lines.append(f"🎉 {escape(milestone)}")
    if ctx.get("sunday") and ctx.get("recap"):
        lines.append(_recap_block(ctx["recap"]))
    else:
        lines.append(_stats_block(stats))

    url = ctx.get("solution_url")
    if url:
        def reveal(inner: str) -> str:
            return inner if solved else f"<tg-spoiler>{inner}</tg-spoiler>"

        hint = (ctx.get("hint") or "").strip()
        if hint:
            lines.append(f"💡 Hint: {reveal(escape(_truncate(hint, hint_limit)))}")
        link = f'<a href="{escape_attr(url)}">{escape(ctx.get("solution_path") or url)}</a>'
        lines.append(f"📘 Solution: {reveal(link)}")
    else:
        lines.append(NO_SOLUTION_LINE)
    lines += ["", _closing(ctx, solved)]
    return "\n".join(lines)


def render_morning(ctx: dict[str, Any], tz: ZoneInfo, solved: SolvedInfo | None = None) -> Rendered:
    """Render the morning message, or its solved edit when `solved` is given."""
    text = ""
    for limit in HINT_LIMITS:
        text = _morning_text(ctx, tz, solved, limit)
        if len(text) <= MAX_LEN:
            break
    if len(text) > MAX_LEN:
        raise ValueError(f"morning message too long ({len(text)} chars)")

    problem_url = ctx["problem"]["url"]
    url = ctx.get("solution_url")
    if solved:
        row = [{"text": "Your submission", "url": submission_url(solved.submission_id)}]
    else:
        row = [{"text": "Open problem", "url": problem_url}]
    if url:
        row.append({"text": "View solution", "url": url})
    return Rendered(text=text, buttons=[row])


def render_solved_reply(ctx: dict[str, Any], tz: ZoneInfo, solved: SolvedInfo) -> Rendered:
    """Short reply used when the original morning message can't be edited."""
    p = ctx["problem"]
    status = _status_line(solved, tz).replace("✅ ", "", 1)
    text = f"✅ #{escape(str(p['frontend_id']))} {escape(p['title'])}\n{status}"
    row = [{"text": "Your submission", "url": submission_url(solved.submission_id)}]
    if ctx.get("solution_url"):
        row.append({"text": "View solution", "url": ctx["solution_url"]})
    return Rendered(text=text, buttons=[row])


# ---- evening nudge ---------------------------------------------------------------


def render_nudge(
    *, frontend_id: str, title: str, slug: str, streak: int, now: datetime, tz: ZoneInfo
) -> Rendered:
    """Evening reminder before LeetCode's 00:00 UTC reset."""
    reset = next_utc_midnight(now)
    left: timedelta = reset - now
    last = f"🔥 Your {streak}-day streak is on the line." if streak > 0 else "Start a new streak today."
    text = "\n".join([
        f"⏰ <b>Still pending: #{escape(str(frontend_id))}</b>",
        escape(title),
        "",
        f"{format_duration(left)} left before LeetCode's day resets ({format_clock(reset.astimezone(tz))}).",
        last,
    ])
    return Rendered(text=text, buttons=[[{"text": "Open problem", "url": f"https://leetcode.com/problems/{slug}/"}]])


def render_failure_alert(workflow: str, run_url: str) -> str:
    """Plain-text failure alert (the workflows send the same text with curl)."""
    return f"⚠️ Bot error: {workflow} failed. {run_url}"
