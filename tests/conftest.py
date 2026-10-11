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


def solution_json() -> dict[str, Any]:
    return {
        "hint": "Think about what you've already seen.",
        "pattern": "Hash Map",
        "brute_force": {"idea": "Check every pair.", "time": "O(n^2)", "space": "O(1)", "code": "class Solution {};"},
        "optimal": {
            "idea": "Store complements.",
            "steps": ["Walk the array", "Look up target - x"],
            "time": "O(n)",
            "space": "O(n)",
            "code": "class Solution {\npublic:\n    vector<int> twoSum(vector<int>& nums, int target) { return {}; }\n};",
        },
        "edge_cases": ["Duplicates", "Negative numbers"],
        "dry_run": "nums=[2,7,11,15], target=9 -> [0,1]",
    }
