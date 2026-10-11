"""Shared fixtures and fakes. No test touches the network."""

from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from src.config import Config, load_config
from src.leetcode_client import (
    AcSubmission,
    DailyChallenge,
    Problem,
    QuestionDetail,
    QuestionSummary,
    Submission,
    Tag,
    UserStats,
)
from src.llm import LLMResult
from src.log_store import LogRow
from src.runtime import Runtime

REPO = Path(__file__).resolve().parent.parent


def epoch(y: int, m: int, d: int) -> int:
    return int(datetime(y, m, d, tzinfo=timezone.utc).timestamp())


@pytest.fixture
def root(tmp_path: Path) -> Path:
    """A throwaway repo root with the real config and greetings."""
    shutil.copy(REPO / "config.yaml", tmp_path / "config.yaml")
    (tmp_path / "data" / "messages").mkdir(parents=True)
    shutil.copy(REPO / "data" / "greetings.json", tmp_path / "data" / "greetings.json")
    (tmp_path / "README.md").write_text("# Test\n\n<!-- PROGRESS:START -->\n<!-- PROGRESS:END -->\n", encoding="utf-8")
    return tmp_path


@pytest.fixture
def cfg(root: Path) -> Config:
    return load_config(
        root,
        env={
            "LEETCODE_USERNAME": "someone",
            "TELEGRAM_BOT_TOKEN": "x",
            "TELEGRAM_CHAT_ID": "1",
            "GEMINI_API_KEY": "k",
            "GITHUB_REPOSITORY": "owner/repo",
        },
    )


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
        model="gemini-3.8-flash",
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


class FakeLeetCode:
    """Fixture data matching the owner's state: 67 solved (E37/M30/H0)."""

    def __init__(self) -> None:
        self.daily_slug = "two-sum"
        self.daily_paid = False
        self.acs: list[AcSubmission] = []
        self.subs: list[Submission] = []
        self.calendar: dict[int, int] = {}
        self.problems = [
            Problem("1", "Two Sum", "two-sum", "Easy", 55.0, False, ["array", "hash-table"]),
            Problem("20", "Valid Parentheses", "valid-parentheses", "Easy", 42.0, False, ["string", "stack"]),
            Problem("704", "Binary Search", "binary-search", "Easy", 58.0, False, ["array", "binary-search"]),
            Problem("11", "Container With Most Water", "container-with-most-water", "Medium", 55.0, False,
                    ["array", "two-pointers", "greedy"]),
        ]
        self.calls: list[str] = []

    def get_daily(self) -> DailyChallenge:
        self.calls.append("daily")
        return DailyChallenge(
            date="2026-10-12",
            link=f"/problems/{self.daily_slug}/",
            question=QuestionSummary("1", "Two Sum", self.daily_slug, "Easy", self.daily_paid,
                                     [Tag("Array", "array"), Tag("Hash Table", "hash-table")]),
        )

    def get_question(self, slug: str) -> QuestionDetail:
        self.calls.append(f"question:{slug}")
        p = next(p for p in self.problems if p.slug == slug)
        return QuestionDetail(
            frontend_id=p.frontend_id,
            title=p.title,
            slug=p.slug,
            difficulty=p.difficulty,
            paid_only=False,
            content_html="<p>SECRET-STATEMENT-TEXT given <code>nums</code></p>",
            example_testcases="[2,7,11,15]\n9",
            code_snippets={"cpp": "class Solution {};", "python3": "class Solution:\n    pass", "java": "class Solution {}"},
            tags=[Tag(t.replace("-", " ").title(), t) for t in p.tags],
        )

    def get_problem_list(self) -> tuple[list[Problem], str]:
        self.calls.append("problem_list")
        return self.problems, "questionList"

    def get_user_stats(self, username: str) -> UserStats:
        self.calls.append("stats")
        return UserStats(total=67, easy=37, medium=30, hard=0, ranking=2266342, active_days=4, calendar=self.calendar)

    def get_calendar(self, username: str, year: int) -> dict[int, int]:
        return {}

    def get_recent_ac(self, username: str, limit: int = 20) -> list[AcSubmission]:
        self.calls.append("recent_ac")
        return self.acs

    def get_recent_submissions(self, username: str, limit: int = 20) -> list[Submission]:
        return self.subs


class FakeLLM:
    def __init__(self, result: dict[str, Any] | None = None, model: str = "gemini-3.8-flash") -> None:
        self.result = result
        self.model = model
        self.prompts: list[list[dict[str, str]]] = []

    def generate(self, messages: list[dict[str, str]]) -> LLMResult | None:
        self.prompts.append(messages)
        return LLMResult(self.result, self.model) if self.result is not None else None


class FakeTelegram:
    def __init__(self) -> None:
        self.sent: list[dict[str, Any]] = []
        self.edits: list[dict[str, Any]] = []
        self.reactions: list[tuple[int, str]] = []
        self.next_id = 500

    def send_message(self, text: str, buttons: Any = None, reply_to: int | None = None) -> int:
        self.next_id += 1
        self.sent.append({"text": text, "buttons": buttons, "reply_to": reply_to, "id": self.next_id})
        return self.next_id

    def edit_with_fallback(self, message_id: int, text: str, buttons: Any, reply_text: str, reply_buttons: Any = None) -> str:
        self.edits.append({"message_id": message_id, "text": text, "buttons": buttons, "reply_text": reply_text})
        return "edited"

    def set_reaction(self, message_id: int, emoji: str) -> bool:
        self.reactions.append((message_id, emoji))
        return True


@pytest.fixture
def fakes() -> tuple[FakeLeetCode, FakeLLM, FakeTelegram]:
    return FakeLeetCode(), FakeLLM(solution_json()), FakeTelegram()


@pytest.fixture
def make_runtime(cfg: Config, fakes: tuple[FakeLeetCode, FakeLLM, FakeTelegram]):
    lc, llm, tg = fakes
    commits: list[str] = []

    def build(now: datetime, *, dry_run: bool = False, force: bool = False) -> Runtime:
        clock = {"now": now}
        rt = Runtime(
            cfg=cfg,
            leetcode=lc,
            telegram=tg,
            llm=llm,
            dry_run=dry_run,
            force=force,
            now=lambda: clock["now"],
            commit=lambda msg: commits.append(msg) or True,
            log=lambda msg: None,
        )
        rt.commits = commits  # type: ignore[attr-defined]
        return rt

    return build
