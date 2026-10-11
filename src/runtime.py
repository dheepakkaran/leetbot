"""Shared plumbing for the entry points: CLI flags, clients, message contexts."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from src.config import Config, load_config
from src.git_ops import commit_and_push
from src.leetcode_client import LeetCodeClient
from src.llm import LLMClient
from src.log_store import LogRow, rows_for_date
from src.telegram_client import DryRunMessenger, Messenger, TelegramClient


@dataclass
class Runtime:
    """Everything a job needs; tests build one with fakes."""

    cfg: Config
    leetcode: Any                       # LeetCodeClient-compatible
    telegram: Messenger
    llm: Any                            # LLMClient-compatible
    dry_run: bool = False
    force: bool = False
    now: Callable[[], datetime] = field(default=lambda: datetime.now(timezone.utc))
    commit: Callable[[str], bool] | None = None
    log: Callable[[str], None] = print

    def commit_and_push(self, message: str) -> bool:
        """Commit + push unless dry-run."""
        if self.dry_run:
            self.log(f"[dry-run] would commit: {message}")
            return False
        if self.commit is not None:
            return self.commit(message)
        return commit_and_push(message, self.cfg.root, log=self.log)


def parse_args(description: str, argv: list[str] | None = None) -> argparse.Namespace:
    """Shared `--dry-run` / `--force` flags."""
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--dry-run", action="store_true", help="print messages; no Telegram, no git, no file writes")
    parser.add_argument("--force", action="store_true", help="skip time gating and idempotency checks")
    return parser.parse_args(argv)


def build_runtime(args: argparse.Namespace, cfg: Config | None = None) -> Runtime:
    """Real clients from config + environment. Fails fast on missing settings."""
    cfg = cfg or load_config()
    if not cfg.leetcode_username:
        raise SystemExit("LEETCODE_USERNAME is not set (repo variable in Actions, .env locally)")
    if args.dry_run:
        telegram: Messenger = DryRunMessenger()
    else:
        telegram = TelegramClient(cfg.telegram_bot_token, cfg.telegram_chat_id)
    llm = LLMClient(
        endpoint=cfg.llm_endpoint,
        models=cfg.llm_models,
        token=cfg.github_token,
        temperature=cfg.llm_temperature,
        max_retries_per_model=cfg.llm_max_retries_per_model,
    )
    return Runtime(cfg=cfg, leetcode=LeetCodeClient(), telegram=telegram, llm=llm, dry_run=args.dry_run, force=args.force)


# ---- data/messages/{date}.json ---------------------------------------------------


def message_context_path(cfg: Config, rows: list[LogRow], row: LogRow) -> Path:
    """`{date}.json` for the first row of a date; `{date}-day{n}.json` for
    extra rows issued the same UTC date with --force."""
    same_day = sorted(rows_for_date(rows, row.date), key=lambda r: r.day)
    if not same_day or same_day[0].day == row.day:
        return cfg.messages_dir / f"{row.date}.json"
    return cfg.messages_dir / f"{row.date}-day{row.day}.json"


def load_message_context(path: Path) -> dict[str, Any] | None:
    """Read a saved render context, or None if missing."""
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def save_message_context(path: Path, ctx: dict[str, Any]) -> None:
    """Write a render context (pretty JSON, UTF-8)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(ctx, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_greetings(path: Path) -> list[str]:
    """The 30 greeting templates (each contains `{name}`)."""
    return list(json.loads(path.read_text(encoding="utf-8")))


def greeting_for_day(greetings: list[str], day: int, name: str) -> str:
    """Pick by `(day - 1) % len(greetings)`."""
    return greetings[(day - 1) % len(greetings)].format(name=name)
