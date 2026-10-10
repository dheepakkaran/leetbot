"""Entry point: `python -m src.preview`. Sends one sample of every variant.

Uses fixture data only. Never touches log.csv, data files or git.
"""

from __future__ import annotations

import argparse
import copy
import sys
import time
from datetime import datetime, timedelta, timezone
from typing import Any

from src.config import load_config
from src.messages import SolvedInfo, render_morning, render_nudge, render_solved_reply
from src.solution_writer import problem_url, solution_url
from src.stats import to_iso
from src.telegram_client import DryRunMessenger, Messenger, TelegramClient


def sample_context(repo: str, owner: str = "Dheepak") -> dict[str, Any]:
    """A realistic `normal` morning context (fixture: 67 solved, E37/M30/H0)."""
    path = "medium/0011-container-with-most-water.md"
    return {
        "version": 1,
        "date": "2026-10-13",
        "day": 12,
        "greeting": f"Good morning, {owner}",
        "problem": {
            "frontend_id": "11",
            "title": "Container With Most Water",
            "slug": "container-with-most-water",
            "difficulty": "Medium",
            "tags": ["Array", "Two Pointers", "Greedy"],
            "url": problem_url("container-with-most-water"),
            "source": "daily",
        },
        "language": {"key": "python", "display": "Python", "k": 2, "block_size": 10},
        "stats": {
            "total": 67, "easy": 37, "medium": 30, "hard": 0,
            "ranking": 2266342, "active_days": 41, "streak": 4,
        },
        "week": {"solved": 1, "bar": "▰▱▱▱▱▱▱"},
        "yesterday": {"frontend_id": "167", "status": "solved"},
        "milestones": [],
        "sunday": False,
        "missed": False,
        "recap": None,
        "variant": "normal",
        "hint": "Start wide. Which side should move to have any chance of a bigger area?",
        "solution_url": solution_url(repo, path),
        "solution_path": path,
        "model": "deepseek/DeepSeek-V3-0324",
        "message_id": None,
        "sent_at": None,
    }


def variants(repo: str, owner: str) -> list[tuple[str, dict[str, Any]]]:
    """(label, context) for every morning variant."""
    base = sample_context(repo, owner)

    missed = copy.deepcopy(base)
    missed.update(variant="missed", missed=True, yesterday={"frontend_id": "167", "status": "unsolved"})
    missed["stats"]["streak"] = 0

    sunday = copy.deepcopy(base)
    sunday.update(
        variant="sunday",
        sunday=True,
        day=18,
        greeting=f"Rise and grind, {owner}",
        week={"solved": 5, "bar": "▰▰▱▰▰▰▱"},
        recap={
            "solved": 5, "easy": 2, "medium": 3, "hard": 0,
            "total": 74, "total_delta": 7, "rank_delta": -18234,
            "fastest": {"frontend_id": "125", "duration": "38 min"},
        },
    )
    sunday["language"]["k"] = 8

    no_solution = copy.deepcopy(base)
    no_solution.update(variant="no_solution", hint=None, solution_url=None, solution_path=None, model="none")

    milestone = copy.deepcopy(base)
    milestone.update(variant="normal", milestones=["7-day streak!"])
    milestone["stats"]["streak"] = 7

    return [
        ("normal", base),
        ("missed", missed),
        ("sunday", sunday),
        ("no_solution", no_solution),
        ("milestone", milestone),
    ]


def run_preview(tg: Messenger, repo: str, owner: str, tz: Any, reaction: str, pause: float = 1.0) -> None:
    """Send every variant, then a pending message edited into its solved form, then a nudge."""
    tg.send_message("🧪 <b>Preview</b>: one sample of every message variant follows.")
    for label, ctx in variants(repo, owner):
        rendered = render_morning(ctx, tz)
        tg.send_message(rendered.text, rendered.buttons)
        time.sleep(pause)

    # Solved edit: send the pending version, then edit it exactly like sync does.
    ctx = sample_context(repo, owner)
    pending = render_morning(ctx, tz)
    message_id = tg.send_message(pending.text, pending.buttons)
    sent = datetime.now(timezone.utc)
    solved = SolvedInfo(
        solved_at=to_iso(sent + timedelta(minutes=38)),
        late=False,
        submission_id="1234567890",
        sent_at=to_iso(sent),
    )
    time.sleep(pause * 2)
    full = render_morning(ctx, tz, solved)
    reply = render_solved_reply(ctx, tz, solved)
    tg.edit_with_fallback(message_id, full.text, full.buttons, reply.text, reply.buttons)
    tg.set_reaction(message_id, reaction)
    time.sleep(pause)

    # Evening nudge, rendered as if it were 18:03 local today.
    local_now = datetime.now(tz).replace(hour=18, minute=3, second=0, microsecond=0)
    nudge = render_nudge(
        frontend_id="11", title="Container With Most Water", slug="container-with-most-water",
        streak=4, now=local_now.astimezone(timezone.utc), tz=tz,
    )
    tg.send_message(nudge.text, nudge.buttons)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Send sample messages of every variant to the owner's chat.")
    parser.add_argument("--dry-run", action="store_true", help="print instead of sending")
    args = parser.parse_args(argv)
    cfg = load_config()
    if args.dry_run:
        tg: Messenger = DryRunMessenger()
        pause = 0.0
    else:
        tg = TelegramClient(cfg.telegram_bot_token, cfg.telegram_chat_id)
        pause = 1.0
    run_preview(tg, cfg.github_repository, cfg.owner_name, cfg.timezone, cfg.reaction_on_solve, pause)
    print("[preview] done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
