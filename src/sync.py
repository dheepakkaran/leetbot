"""Entry point: `python -m src.sync`. Marks issued problems as solved."""

from __future__ import annotations

import sys

from src.leetcode_client import AcSubmission, LeetCodeError
from src.log_store import LogRow, read_log, write_log
from src.messages import SolvedInfo, render_morning, render_solved_reply
from src.readme_progress import update_readme
from src.runtime import (
    Runtime,
    build_runtime,
    load_message_context,
    message_context_path,
    parse_args,
    save_message_context,
)
from src.stats import from_epoch, is_late, load_history, parse_iso, to_iso


def match_submissions(pending: list[LogRow], acs: list[AcSubmission]) -> list[tuple[LogRow, AcSubmission]]:
    """Pair each pending row with its earliest AC where slug matches and
    `timestamp >= sent_at` (older ACs never count)."""
    matches = []
    for row in pending:
        if not row.sent_at:
            continue
        sent = parse_iso(row.sent_at)
        candidates = [ac for ac in acs if ac.slug == row.slug and from_epoch(ac.timestamp) >= sent]
        if candidates:
            matches.append((row, min(candidates, key=lambda ac: ac.timestamp)))
    return matches


def _languages_used(rt: Runtime, matches: list[tuple[LogRow, AcSubmission]]) -> dict[tuple[str, int], str]:
    """(slug, timestamp) -> LeetCode lang slug for matched ACs, best effort."""
    try:
        subs = rt.leetcode.get_recent_submissions(rt.cfg.leetcode_username)
    except LeetCodeError as exc:
        rt.log(f"[sync] language check skipped: {exc}")
        return {}
    wanted = {(row.slug, ac.timestamp) for row, ac in matches}
    return {
        (s.slug, s.timestamp): s.lang
        for s in subs
        if (s.slug, s.timestamp) in wanted and s.status == "Accepted" and s.lang
    }


def _notify_solved(rt: Runtime, rows: list[LogRow], row: LogRow, lang_used: str | None) -> None:
    """Edit the morning message into its solved version (with fallbacks) and react."""
    cfg = rt.cfg
    solved = SolvedInfo(solved_at=row.solved_at, late=row.late, submission_id=row.submission_id, sent_at=row.sent_at)
    ctx_path = message_context_path(cfg, rows, row)
    ctx = load_message_context(ctx_path)
    message_id = int(row.message_id)
    if ctx is None:
        # No saved context: we can't re-render, so only reply.
        rt.log(f"[sync] missing {ctx_path.name}; replying instead of editing")
        ctx = {
            "problem": {"frontend_id": row.frontend_id, "title": row.title},
            "solution_url": None,
        }
        reply = render_solved_reply(ctx, cfg.timezone, solved)
        try:
            rt.telegram.send_message(reply.text, reply.buttons, reply_to=message_id)
        except Exception as exc:  # noqa: BLE001 - any failure falls back to standalone
            rt.log(f"[sync] reply failed ({exc}); sending standalone")
            rt.telegram.send_message(reply.text, reply.buttons)
    else:
        if lang_used:
            ctx["actual_language"] = lang_used
            if not rt.dry_run:
                save_message_context(ctx_path, ctx)
        full = render_morning(ctx, cfg.timezone, solved)
        reply = render_solved_reply(ctx, cfg.timezone, solved)
        how = rt.telegram.edit_with_fallback(message_id, full.text, full.buttons, reply.text, reply.buttons)
        rt.log(f"[sync] day {row.day} #{row.frontend_id}: message {how}")
    rt.telegram.set_reaction(message_id, cfg.reaction_on_solve)


def run_sync(rt: Runtime) -> list[LogRow]:
    """Mark solved rows, update Telegram, commit if anything changed.

    Returns the (possibly updated) rows, so callers see fresh state even in dry-run.
    """
    cfg = rt.cfg
    rows = read_log(cfg.log_path)
    pending = [r for r in rows if not r.solved and r.message_id]
    if not pending:
        rt.log("[sync] nothing pending")
        return rows

    acs = rt.leetcode.get_recent_ac(cfg.leetcode_username)
    matches = match_submissions(pending, acs)
    if not matches:
        rt.log(f"[sync] {len(pending)} pending, no new accepted submissions")
        return rows

    langs = _languages_used(rt, matches)
    for row, ac in matches:
        solved_at = from_epoch(ac.timestamp)
        row.solved = True
        row.solved_at = to_iso(solved_at)
        row.submission_id = ac.id
        row.late = is_late(row.date, solved_at)
        rt.log(f"[sync] day {row.day} #{row.frontend_id} solved at {row.solved_at}{' (late)' if row.late else ''}")
        _notify_solved(rt, rows, row, langs.get((row.slug, ac.timestamp)))

    if not rt.dry_run:
        write_log(cfg.log_path, rows)
        history = load_history(cfg.stats_history_path)
        streak = history[-1].streak if history else 0
        update_readme(cfg.readme_path, rows, streak, rt.now().date())
    ids = ",".join(f"#{row.frontend_id}" for row, _ in matches)
    rt.commit_and_push(f"chore: sync solved {ids}")
    return rows


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    args = parse_args("Check LeetCode for solved problems and update Telegram.", argv)
    rt = build_runtime(args)
    run_sync(rt)
    return 0


if __name__ == "__main__":
    sys.exit(main())
