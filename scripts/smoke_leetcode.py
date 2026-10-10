"""Live check of every LeetCode query used by the bot.

Usage: python scripts/smoke_leetcode.py [username]
The username defaults to $LEETCODE_USERNAME (or .env). Exits 1 if any check fails.
Prints trimmed results only: never the statement text.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import load_config  # noqa: E402
from src.leetcode_client import LeetCodeClient, html_to_text  # noqa: E402
from src.stats import compute_streak, from_epoch  # noqa: E402


def main() -> int:
    cfg = load_config()
    username = sys.argv[1] if len(sys.argv) > 1 else cfg.leetcode_username
    if not username:
        print("Set LEETCODE_USERNAME (or pass the username as an argument).")
        return 2
    lc = LeetCodeClient()
    failures: list[str] = []

    def check(name: str, fn) -> None:  # type: ignore[no-untyped-def]
        try:
            summary = fn()
        except Exception as exc:  # noqa: BLE001 - report every failure
            failures.append(name)
            print(f"FAIL  {name}: {exc}")
        else:
            print(f"ok    {name}: {summary}")

    def daily() -> str:
        d = lc.get_daily()
        q = d.question
        return f"{d.date} #{q.frontend_id} {q.title} [{q.difficulty}] paid={q.paid_only} tags={[t.slug for t in q.tags]}"

    def detail() -> str:
        q = lc.get_question("two-sum")
        assert q.content_html and q.code_snippets, "missing content/snippets"
        for slug in ("cpp", "python3", "java"):
            assert slug in q.code_snippets, f"missing {slug} snippet"
        text = html_to_text(q.content_html)
        return (
            f"#{q.frontend_id} {q.title} [{q.difficulty}] snippets={sorted(q.code_snippets)[:6]}... "
            f"statement={len(text)} chars (not shown) examples={q.example_testcases.count(chr(10)) + 1} lines"
        )

    def problem_list(method_name: str):  # type: ignore[no-untyped-def]
        def run() -> str:
            problems = getattr(lc, method_name)()
            assert problems, "empty list"
            free = sum(1 for p in problems if not p.paid_only)
            tagged = sum(1 for p in problems if p.tags)
            p = problems[0]
            return (
                f"{len(problems)} problems ({free} free, {tagged} tagged); first=#{p.frontend_id} {p.slug} "
                f"{p.difficulty} ac={p.ac_rate:.1f}% tags={p.tags[:3]}"
            )
        return run

    def user_stats() -> str:
        s = lc.get_user_stats(username)
        today = datetime.now(timezone.utc).date()
        streak = compute_streak(s.calendar, today, load_year=lambda y: lc.get_calendar(username, y))
        last = max(s.calendar) if s.calendar else None
        last_day = from_epoch(last).date() if last else "never"
        return (
            f"total={s.total} easy={s.easy} medium={s.medium} hard={s.hard} ranking={s.ranking:,} "
            f"active_days={s.active_days} calendar_days={len(s.calendar)} last_active={last_day} streak={streak}"
        )

    def calendar_year() -> str:
        year = datetime.now(timezone.utc).year - 1
        cal = lc.get_calendar(username, year)
        return f"{year}: {len(cal)} active days"

    def recent_ac() -> str:
        acs = lc.get_recent_ac(username)
        assert acs, "no accepted submissions returned"
        a = acs[0]
        return f"{len(acs)} ACs; latest=#{a.id} {a.slug} at {from_epoch(a.timestamp):%Y-%m-%d %H:%M}Z"

    def recent_subs() -> str:
        subs = lc.get_recent_submissions(username)
        assert subs, "no submissions returned"
        langs = sorted({s.lang for s in subs})
        return f"{len(subs)} submissions; lang exposed={bool(subs[0].lang)} langs={langs}"

    print(f"LeetCode smoke test for {username!r}\n")
    check("1. daily problem", daily)
    check("2. question detail", detail)
    check("3a. problem list (questionList)", problem_list("_problem_list_v1"))
    check("3b. problem list (problemsetQuestionListV2)", problem_list("_problem_list_v2"))
    check("3c. problem list (REST)", problem_list("_problem_list_rest"))
    check("4. user stats", user_stats)
    check("4b. user calendar (previous year)", calendar_year)
    check("5. recent accepted submissions", recent_ac)
    check("6. recent submissions (lang)", recent_subs)

    print()
    if failures:
        print(f"{len(failures)} check(s) failed: {', '.join(failures)}")
        return 1
    print("All LeetCode queries OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
