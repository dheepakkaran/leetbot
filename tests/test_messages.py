import copy
import re
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pytest

from src.messages import (
    MAX_LEN,
    SolvedInfo,
    choose_variant,
    format_clock,
    render_failure_alert,
    render_morning,
    render_nudge,
    render_solved_reply,
)
from src.preview import sample_context, variants

TZ = ZoneInfo("America/New_York")
REPO = "dheepakkaran/leetcode-daily"


def ctx(**kw):
    c = sample_context(REPO)
    c.update(kw)
    return c


def solved(late: bool = False) -> SolvedInfo:
    return SolvedInfo(
        solved_at="2026-10-14T03:00:00Z" if late else "2026-10-13T13:52:00Z",
        late=late,
        submission_id="987654321",
        sent_at="2026-10-13T12:20:00Z",
    )


@pytest.mark.parametrize("label, context", variants(REPO, "Dheepak"))
def test_every_variant_renders(label, context) -> None:
    r = render_morning(context, TZ)
    assert r.text and r.buttons
    assert len(r.text) <= MAX_LEN
    first, second = r.text.split("\n")[:2]
    assert "Dheepak" in first and f"Day {context['day']}" in first
    assert second.startswith("Today: #")


def test_normal_layout() -> None:
    r = render_morning(ctx(), TZ)
    lines = r.text.split("\n")
    assert lines[0] == "☀️ <b>Good morning, Dheepak · Day 12</b>"
    assert lines[1] == "Today: #11 Container With Most Water"
    assert lines[2] == "Medium · Array, Two Pointers, Greedy · Solve in Python (2/10)"
    assert "✅ Yesterday: #167 solved" in r.text
    assert "🔥 Streak 4 days · Week 1/7 ▰▱▱▱▱▱▱" in r.text
    assert "<blockquote expandable>📊 <b>Your LeetCode</b>\nSolved 67 · Easy 37 · Medium 30 · Hard 0\nRanking 2,266,342 · Active days 41</blockquote>" in r.text
    assert "💡 Hint: <tg-spoiler>" in r.text
    assert "📘 Solution: <tg-spoiler><a href=" in r.text
    assert lines[-1] == "Do it asap."
    assert [b["text"] for b in r.buttons[0]] == ["Open problem", "View solution"]
    assert r.buttons[0][0]["url"] == "https://leetcode.com/problems/container-with-most-water/"


def test_tags_capped_at_three() -> None:
    c = ctx()
    c["problem"]["tags"] = ["Array", "Two Pointers", "Greedy", "Sorting", "Math"]
    assert "Array, Two Pointers, Greedy · Solve" in render_morning(c, TZ).text


def test_day_one_has_no_yesterday_line() -> None:
    r = render_morning(ctx(day=1, yesterday=None), TZ)
    assert "Yesterday" not in r.text


def test_yesterday_late_and_missed() -> None:
    late = render_morning(ctx(yesterday={"frontend_id": "5", "status": "late"}), TZ).text
    assert "✅ Yesterday: #5 solved late" in late
    missed = render_morning(ctx(missed=True, yesterday={"frontend_id": "5", "status": "unsolved"}), TZ).text
    assert "❌ Yesterday: #5 not solved · streak reset" in missed
    assert missed.endswith("Yesterday slipped. Today gets you back on track.")


def test_sunday_recap() -> None:
    sunday = dict(variants(REPO, "Dheepak"))["sunday"]
    text = render_morning(sunday, TZ).text
    assert "<blockquote expandable>📊 <b>Week recap</b>" in text
    assert "Solved 5/7 · Easy 2 · Medium 3 · Hard 0" in text
    assert "Total 74 (+7) · Ranking ↑ 18,234" in text
    assert "Fastest: #125 in 38 min after alert</blockquote>" in text
    assert "Your LeetCode" not in text
    assert text.endswith("New week. Do it asap.")

    worse = copy.deepcopy(sunday)
    worse["recap"].update(rank_delta=500, solved=0, total_delta=0, fastest=None)
    text = render_morning(worse, TZ).text
    assert "Ranking ↓ 500" in text and "(+0)" in text and "Fastest" not in text


def test_sunday_and_missed_uses_sunday_layout_with_missed_closing() -> None:
    sunday = dict(variants(REPO, "Dheepak"))["sunday"]
    sunday.update(missed=True, yesterday={"frontend_id": "5", "status": "unsolved"})
    text = render_morning(sunday, TZ).text
    assert "Week recap" in text and "❌ Yesterday: #5 not solved" in text
    assert text.endswith("Yesterday slipped. Today gets you back on track.")


def test_no_solution_variant() -> None:
    r = render_morning(dict(variants(REPO, "Dheepak"))["no_solution"], TZ)
    assert "📘 Solution unavailable today. Rerun from Actions." in r.text
    assert "Hint" not in r.text
    assert [b["text"] for b in r.buttons[0]] == ["Open problem"]


def test_milestone_line_above_stats() -> None:
    text = render_morning(dict(variants(REPO, "Dheepak"))["milestone"], TZ).text
    assert text.index("🎉 7-day streak!") < text.index("<blockquote")


def test_html_is_escaped() -> None:
    c = ctx(hint="use a < b && c > d")
    c["problem"]["title"] = "Pairs & <Things> > Stuff"
    c["problem"]["tags"] = ["A&B"]
    text = render_morning(c, TZ).text
    assert "Pairs &amp; &lt;Things&gt; &gt; Stuff" in text
    assert "A&amp;B" in text
    assert "use a &lt; b &amp;&amp; c &gt; d" in text
    assert "<Things>" not in text
    stripped = re.sub(r"</?(b|blockquote( expandable)?|tg-spoiler|a( href=\"[^\"]*\")?)>", "", text)
    assert "<" not in stripped and ">" not in stripped


def test_length_limit_with_huge_hint() -> None:
    r = render_morning(ctx(hint="x" * 10_000), TZ)
    assert len(r.text) <= MAX_LEN


def test_solved_edit_has_no_spoilers_and_new_buttons() -> None:
    r = render_morning(ctx(), TZ, solved())
    assert "<tg-spoiler>" not in r.text
    lines = r.text.split("\n")
    assert lines[3] == "✅ <b>Solved at 9:52 AM · 1 h 32 min after alert</b>"
    assert lines[-1] == "Done. See you tomorrow."
    assert "💡 Hint: Start wide." in r.text
    assert r.buttons[0][0] == {"text": "Your submission", "url": "https://leetcode.com/submissions/detail/987654321/"}
    assert r.buttons[0][1]["text"] == "View solution"
    # stats block unchanged
    assert render_morning(ctx(), TZ).text.split("<blockquote")[1] .split("</blockquote>")[0] in r.text


def test_solved_late_line() -> None:
    r = render_morning(ctx(), TZ, solved(late=True))
    assert "✅ <b>Solved late · Oct 13</b>" in r.text  # 03:00Z Oct 14 = 11 PM EDT Oct 13


def test_solved_reply() -> None:
    r = render_solved_reply(ctx(), TZ, solved())
    assert r.text.startswith("✅ #11 Container With Most Water")
    assert r.buttons[0][0]["text"] == "Your submission"


@pytest.mark.parametrize(
    "now, reset, left",
    [
        (datetime(2026, 7, 1, 22, 3, tzinfo=timezone.utc), "8:00 PM", "1 h 57 min"),   # EDT 18:03
        (datetime(2026, 12, 1, 23, 3, tzinfo=timezone.utc), "7:00 PM", "57 min"),      # EST 18:03
    ],
)
def test_evening_nudge_reset_time(now, reset, left) -> None:
    r = render_nudge(frontend_id="11", title="A & B", slug="a-b", streak=4, now=now, tz=TZ)
    lines = r.text.split("\n")
    assert lines[0] == "⏰ <b>Still pending: #11</b>"
    assert lines[1] == "A &amp; B"
    assert lines[3] == f"{left} left before LeetCode's day resets ({reset})."
    assert lines[4] == "🔥 Your 4-day streak is on the line."
    assert r.buttons == [[{"text": "Open problem", "url": "https://leetcode.com/problems/a-b/"}]]


def test_evening_nudge_zero_streak() -> None:
    now = datetime(2026, 7, 1, 22, 3, tzinfo=timezone.utc)
    r = render_nudge(frontend_id="1", title="T", slug="t", streak=0, now=now, tz=TZ)
    assert r.text.endswith("Start a new streak today.")


def test_variant_choice_and_misc() -> None:
    assert choose_variant(has_solution=True, missed=False, sunday=False) == "normal"
    assert choose_variant(has_solution=True, missed=True, sunday=False) == "missed"
    assert choose_variant(has_solution=True, missed=True, sunday=True) == "sunday"
    assert choose_variant(has_solution=False, missed=True, sunday=True) == "no_solution"
    assert format_clock(datetime(2026, 1, 1, 0, 5)) == "12:05 AM"
    assert format_clock(datetime(2026, 1, 1, 12, 0)) == "12:00 PM"
    assert render_failure_alert("morning", "https://x/runs/1") == "⚠️ Bot error: morning failed. https://x/runs/1"
