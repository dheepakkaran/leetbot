"""Shared fixtures and helpers. No test touches the network."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.log_store import LogRow

REPO = Path(__file__).resolve().parent.parent


def epoch(y: int, m: int, d: int) -> int:
    return int(datetime(y, m, d, tzinfo=timezone.utc).timestamp())


def make_row(day: int, date: str, slug: str = "", **kw: Any) -> LogRow:
    base: dict[str, Any] = dict(
        day=day,
        date=date,
        frontend_id=str(100 + day),
        title=f"Problem {day}",
        slug=slug or f"problem-{day}",
        difficulty="Easy",
        tags="Array",
        source="daily",
        language="cpp",
        model="openai/gpt-4.1",
        solution_path=f"easy/{100 + day:04d}-problem-{day}.md",
        sent_at=f"{date}T12:20:00Z",
        message_id=str(1000 + day),
    )
    base.update(kw)
    return LogRow(**base)
