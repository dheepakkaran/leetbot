"""Entry point: `python -m src.morning`. Issues today's problem."""

from __future__ import annotations

import sys
from datetime import datetime
from typing import Any

from src.languages import Language, language_by_key, language_for_day
from src.leetcode_client import LeetCodeError, Problem, QuestionDetail, UserStats, html_to_text
from src.llm import build_messages
from src.log_store import LogRow, join_tags, latest_row_for_date, read_log, write_log
from src.messages import SolvedInfo, choose_variant, render_morning, render_solved_reply
from src.picker import cache_is_stale, load_problems_cache, pick_problem, save_problems_cache
from src.readme_progress import update_readme
from src.runtime import (
    Runtime,
    build_runtime,
    greeting_for_day,
    load_greetings,
    load_message_context,
    message_context_path,
    parse_args,
    save_message_context,
)
from src.solution_writer import problem_url, render_solution, solution_path, solution_url, write_solution
from src.stats import (
    Snapshot,
    compute_streak,
    load_history,
    milestones,
    previous_snapshot,
    save_history,
    to_iso,
    upsert_snapshot,
    week_progress,
    week_recap,
)
from src.sync import run_sync

DRY_RUN_DIR = ".dry-run"


def morning_gate(now: datetime, tz: Any, morning_hour: int, rows: list[LogRow]) -> tuple[bool, str]:
    """Send only at/after `morning_hour` local, while the local and UTC dates still
    agree, and only if today's UTC date has no row.

    The date check stops a night-time run (after LeetCode's 00:00 UTC reset,
    8 PM EDT / 7 PM EST) from issuing the next day's problem early.
    """
    local = now.astimezone(tz)
    if local.hour < morning_hour:
        return False, f"too early: {local:%H:%M} local < {morning_hour:02d}:00"
    if local.date() != now.date():
        return False, f"LeetCode's day already rolled over ({local:%H:%M} local); tomorrow's problem waits for the morning"
    if latest_row_for_date(rows, now.date().isoformat()) is not None:
        return False, f"already issued for {now.date().isoformat()}"
    return True, "ok"


def needs_repair(row: LogRow) -> bool:
    """Today's row was never sent, or has no solution (LLM failed)."""
    return not row.message_id or not row.has_solution


def read_hint(markdown: str) -> str:
    """Pull the hint line back out of a solution file (used when resuming)."""
    lines = markdown.splitlines()
    try:
        start = lines.index("## Hint") + 1
    except ValueError:
        return ""
    out = []
    for line in lines[start:]:
        if line.startswith("## "):
            break
        out.append(line)
    return "\n".join(out).strip()


# ---- steps ---------------------------------------------------------------------


def _ensure_problems(rt: Runtime, now: datetime) -> list[Problem]:
    """Cached problem list, refreshed when older than `problems_cache_days`."""
    cfg = rt.cfg
    problems, fetched_at = load_problems_cache(cfg.problems_path)
    if not cache_is_stale(fetched_at, now, cfg.problems_cache_days):
        return problems
    try:
        fresh, source = rt.leetcode.get_problem_list()
    except LeetCodeError as exc:
        if problems:
            rt.log(f"[morning] problem list refresh failed, using stale cache: {exc}")
            return problems
        raise
    rt.log(f"[morning] refreshed problem list: {len(fresh)} problems via {source}")
    if not rt.dry_run:
        save_problems_cache(cfg.problems_path, fresh, source, now)
    return fresh


def _generate_solution(
    rt: Runtime, detail: QuestionDetail, lang: Language, day: int, utc_date: str
) -> tuple[str, str, str | None]:
    """Ask the LLM and write the Markdown. Returns (model, path, hint);
    model is "none" and path empty if generation failed."""
    cfg = rt.cfg
    tags = [t.name for t in detail.tags]
    messages = build_messages(
        frontend_id=detail.frontend_id,
        title=detail.title,
        difficulty=detail.difficulty,
        tags=tags,
        statement=html_to_text(detail.content_html),
        example_testcases=detail.example_testcases,
        snippet=detail.code_snippets.get(lang.leetcode_slug, ""),
        language_display=lang.display,
        fence=lang.fence,
    )
    result = rt.llm.generate(messages)
    if result is None:
        return "none", "", None
    path = solution_path(detail.difficulty, detail.frontend_id, detail.slug)
    markdown = render_solution(
        frontend_id=detail.frontend_id,
        title=detail.title,
        slug=detail.slug,
        difficulty=detail.difficulty,
        tags=tags,
        language=lang,
        day=day,
        date=utc_date,
        model=result.model,
        solution=result.data,
    )
    root = cfg.root / DRY_RUN_DIR if rt.dry_run else cfg.root
    written = write_solution(root, path, markdown)
    rt.log(f"[morning] solution by {result.model} written to {written.relative_to(cfg.root)}")
    return result.model, path, result.data.get("hint") or None


def _yesterday(prev: LogRow | None) -> dict[str, Any] | None:
    if prev is None:
        return None
    status = ("late" if prev.late else "solved") if prev.solved else "unsolved"
    return {"frontend_id": prev.frontend_id, "status": status}


def build_context(
    rt: Runtime,
    *,
    row: LogRow,
    rows: list[LogRow],
    user: UserStats,
    snapshot: Snapshot,
    history: list[Snapshot],
    now: datetime,
    hint: str | None,
) -> dict[str, Any]:
    """Everything needed to (re-)render this morning's message."""
    cfg = rt.cfg
    today = now.date()
    lang = language_by_key(row.language)
    prev_rows = [r for r in rows if r.day < row.day]
    prev = prev_rows[-1] if prev_rows else None
    sunday = now.astimezone(cfg.timezone).weekday() == 6
    week_solved, bar = week_progress(rows, today)
    url = solution_url(cfg.github_repository, row.solution_path) if row.has_solution else None
    missed = prev is not None and not prev.solved
    ctx: dict[str, Any] = {
        "version": 1,
        "date": row.date,
        "day": row.day,
        "greeting": greeting_for_day(load_greetings(cfg.greetings_path), row.day, cfg.owner_name),
        "problem": {
            "frontend_id": row.frontend_id,
            "title": row.title,
            "slug": row.slug,
            "difficulty": row.difficulty,
            "tags": row.tag_list,
            "url": problem_url(row.slug),
            "source": row.source,
        },
        "language": {
            "key": lang.key,
            "display": lang.display,
            "k": ((row.day - 1) % cfg.block_size) + 1,
            "block_size": cfg.block_size,
        },
        "stats": {
            "total": user.total,
            "easy": user.easy,
            "medium": user.medium,
            "hard": user.hard,
            "ranking": user.ranking,
            "active_days": user.active_days,
            "streak": snapshot.streak,
        },
        "week": {"solved": week_solved, "bar": bar},
        "yesterday": _yesterday(prev),
        "milestones": milestones(
            previous_snapshot(history, snapshot.date), snapshot, cfg.milestone_solved_every, cfg.milestone_streak_days
        ),
        "sunday": sunday,
        "missed": missed,
        "recap": week_recap(rows, today, snapshot, history) if sunday else None,
        "variant": choose_variant(has_solution=url is not None, missed=missed, sunday=sunday),
        "hint": hint,
        "solution_url": url,
        "solution_path": row.solution_path or None,
        "model": row.model,
        "message_id": None,
        "sent_at": None,
    }
    return ctx


def _persist_issue(rt: Runtime, rows: list[LogRow], history: list[Snapshot], row: LogRow, now: datetime) -> None:
    cfg = rt.cfg
    if rt.dry_run:
        return
    write_log(cfg.log_path, rows)
    save_history(cfg.stats_history_path, history)
    update_readme(cfg.readme_path, rows, history[-1].streak if history else 0, now.date())


def issue(rt: Runtime, resume: LogRow | None = None) -> int:
    """Steps 2-10 of §12: sync, stats, pick, generate, log, commit, send, commit.

    With `resume`, re-use that row (its problem, day and language) instead of
    picking a new one: used when today's message was never sent.
    """
    cfg = rt.cfg
    username = cfg.leetcode_username
    now = rt.now()
    today = now.date()
    today_iso = today.isoformat()

    rows = run_sync(rt)
    if resume is not None:
        resume = next(r for r in rows if r.day == resume.day)

    user = rt.leetcode.get_user_stats(username)
    recent_ac = {ac.slug for ac in rt.leetcode.get_recent_ac(username)}
    streak = compute_streak(user.calendar, today, load_year=lambda y: rt.leetcode.get_calendar(username, y))
    snapshot = Snapshot(today_iso, user.total, user.easy, user.medium, user.hard, user.ranking, streak)
    history = upsert_snapshot(load_history(cfg.stats_history_path), snapshot)

    if resume is None:
        try:
            problems: list[Problem] | None = _ensure_problems(rt, now)
        except LeetCodeError as exc:
            rt.log(f"[morning] problem list unavailable: {exc}")
            problems = None
        try:
            daily = rt.leetcode.get_daily()
        except LeetCodeError as exc:
            rt.log(f"[morning] daily unavailable: {exc}")
            daily = None

        def load_problems() -> list[Problem]:
            return problems if problems is not None else _ensure_problems(rt, now)

        pick = pick_problem(
            daily=daily,
            load_problems=load_problems,
            rows=rows,
            recent_ac=recent_ac,
            difficulty_by_weekday=cfg.difficulty_by_weekday,
            core_patterns=cfg.core_patterns,
            acrate_ranges=cfg.acrate_ranges,
            utc_date=today,
            local_weekday=now.astimezone(cfg.timezone).weekday(),
        )
        rt.log(f"[morning] picked {pick.slug} ({pick.source}: {pick.reason})")
        slug, source, day = pick.slug, pick.source, len(rows) + 1
        lang, _ = language_for_day(day, cfg.block_size, cfg.language_cycle)
    else:
        slug, source, day = resume.slug, resume.source, resume.day
        lang = language_by_key(resume.language)
        rt.log(f"[morning] resuming day {day} ({slug})")

    detail = rt.leetcode.get_question(slug)

    hint: str | None = None
    if resume is not None and resume.has_solution and (cfg.root / resume.solution_path).exists():
        model, path = resume.model, resume.solution_path
        hint = read_hint((cfg.root / path).read_text(encoding="utf-8")) or None
    else:
        model, path, hint = _generate_solution(rt, detail, lang, day, today_iso)

    if resume is None:
        row = LogRow(
            day=day,
            date=today_iso,
            frontend_id=detail.frontend_id,
            title=detail.title,
            slug=detail.slug,
            difficulty=detail.difficulty,
            tags=join_tags([t.name for t in detail.tags]),
            source=source,
            language=lang.key,
            model=model,
            solution_path=path,
        )
        rows.append(row)
    else:
        row = resume
        row.model, row.solution_path = model, path

    _persist_issue(rt, rows, history, row, now)
    rt.commit_and_push(f"chore: day {day} #{row.frontend_id} {row.slug}")

    ctx = build_context(rt, row=row, rows=rows, user=user, snapshot=snapshot, history=history, now=now, hint=hint)
    rendered = render_morning(ctx, cfg.timezone)
    message_id = rt.telegram.send_message(rendered.text, rendered.buttons)
    sent_at = to_iso(rt.now())
    rt.log(f"[morning] sent day {day} ({ctx['variant']}), message_id={message_id}")

    ctx["message_id"], ctx["sent_at"] = message_id, sent_at
    row.message_id, row.sent_at = str(message_id), sent_at
    if not rt.dry_run:
        save_message_context(message_context_path(cfg, rows, row), ctx)
        write_log(cfg.log_path, rows)
    rt.commit_and_push(f"chore: day {day} message id")
    return 0


def repair_solution(rt: Runtime, row: LogRow) -> int:
    """Today's message was sent without a solution: retry the LLM and, on
    success, commit the file and edit the message through the same renderer."""
    cfg = rt.cfg
    rows = read_log(cfg.log_path)
    row = next(r for r in rows if r.day == row.day)
    ctx_path = message_context_path(cfg, rows, row)
    ctx = load_message_context(ctx_path)
    if ctx is None:
        rt.log(f"[morning] cannot repair day {row.day}: {ctx_path.name} missing")
        return 0
    rt.log(f"[morning] retrying solution for day {row.day} ({row.slug})")
    detail = rt.leetcode.get_question(row.slug)
    model, path, hint = _generate_solution(rt, detail, language_by_key(row.language), row.day, row.date)
    if model == "none":
        rt.log("[morning] solution still unavailable")
        return 0

    row.model, row.solution_path = model, path
    url = solution_url(cfg.github_repository, path)
    ctx.update(
        hint=hint,
        solution_url=url,
        solution_path=path,
        model=model,
        variant=choose_variant(has_solution=True, missed=bool(ctx.get("missed")), sunday=bool(ctx.get("sunday"))),
    )
    if not rt.dry_run:
        write_log(cfg.log_path, rows)
        save_message_context(ctx_path, ctx)
    rt.commit_and_push(f"chore: day {row.day} #{row.frontend_id} solution")

    solved = None
    if row.solved:
        solved = SolvedInfo(solved_at=row.solved_at, late=row.late, submission_id=row.submission_id, sent_at=row.sent_at)
    full = render_morning(ctx, cfg.timezone, solved)
    if solved:
        reply = render_solved_reply(ctx, cfg.timezone, solved)
    else:
        reply = render_morning(ctx, cfg.timezone)
    how = rt.telegram.edit_with_fallback(int(row.message_id), full.text, full.buttons, reply.text, reply.buttons)
    rt.log(f"[morning] day {row.day} message {how} with solution")
    return 0


def run_morning(rt: Runtime) -> int:
    """Time gate + idempotency, then issue (or repair) today's problem."""
    cfg = rt.cfg
    now = rt.now()
    rows = read_log(cfg.log_path)
    existing = latest_row_for_date(rows, now.date().isoformat())

    if existing is not None and needs_repair(existing):
        # A rerun fixes today's row instead of issuing a second problem.
        if existing.message_id:
            return repair_solution(rt, existing)
        return issue(rt, resume=existing)

    if not rt.force:
        ok, why = morning_gate(now, cfg.timezone, cfg.morning_local_hour, rows)
        if not ok:
            rt.log(f"[morning] skip: {why}")
            return 0
    return issue(rt)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    args = parse_args("Issue today's LeetCode problem.", argv)
    return run_morning(build_runtime(args))


if __name__ == "__main__":
    sys.exit(main())
