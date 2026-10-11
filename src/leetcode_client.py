"""LeetCode HTTP client: GraphQL + REST, retries, typed results."""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from html.parser import HTMLParser
from typing import Any, Callable

import requests

from src import leetcode_queries as Q

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)
HEADERS = {
    "Content-Type": "application/json",
    "Referer": "https://leetcode.com",
    "User-Agent": USER_AGENT,
}
ATTEMPTS = 3
BACKOFF_BASE_SECONDS = 2
TIMEOUT_SECONDS = 60
DIFFICULTIES = ("Easy", "Medium", "Hard")


class LeetCodeError(RuntimeError):
    """Raised when LeetCode can't be reached or returns an unusable response."""


@dataclass(frozen=True)
class Tag:
    name: str
    slug: str


@dataclass(frozen=True)
class QuestionSummary:
    frontend_id: str
    title: str
    slug: str
    difficulty: str
    paid_only: bool
    tags: list[Tag]


@dataclass(frozen=True)
class DailyChallenge:
    date: str
    link: str
    question: QuestionSummary


@dataclass(frozen=True)
class QuestionDetail:
    frontend_id: str
    title: str
    slug: str
    difficulty: str
    paid_only: bool
    content_html: str
    example_testcases: str
    code_snippets: dict[str, str]
    tags: list[Tag]


@dataclass(frozen=True)
class Problem:
    """One entry of the normalized problem list (same schema for all sources)."""

    frontend_id: str
    title: str
    slug: str
    difficulty: str
    ac_rate: float
    paid_only: bool
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Problem":
        return cls(
            frontend_id=str(d["frontend_id"]),
            title=str(d["title"]),
            slug=str(d["slug"]),
            difficulty=str(d["difficulty"]),
            ac_rate=float(d["ac_rate"]),
            paid_only=bool(d["paid_only"]),
            tags=[str(t) for t in d.get("tags", [])],
        )


@dataclass(frozen=True)
class UserStats:
    total: int
    easy: int
    medium: int
    hard: int
    ranking: int | None
    active_days: int
    calendar: dict[int, int]  # UTC-midnight epoch seconds -> submission count


@dataclass(frozen=True)
class AcSubmission:
    id: str
    title: str
    slug: str
    timestamp: int


@dataclass(frozen=True)
class Submission:
    slug: str
    timestamp: int
    status: str
    lang: str


def normalize_difficulty(value: str) -> str:
    """Map `EASY`/`easy`/`Easy` (or REST levels 1-3) to `Easy`/`Medium`/`Hard`."""
    text = str(value).strip()
    if text in ("1", "2", "3"):
        return DIFFICULTIES[int(text) - 1]
    return text.capitalize()


def parse_calendar(raw: str | dict | None) -> dict[int, int]:
    """Parse `submissionCalendar` (a JSON string of epoch -> count) into ints."""
    if not raw:
        return {}
    data = json.loads(raw) if isinstance(raw, str) else raw
    return {int(k): int(v) for k, v in data.items()}


class _TextExtractor(HTMLParser):
    BLOCK_TAGS = {"p", "div", "br", "li", "pre", "ul", "ol", "h1", "h2", "h3", "h4", "tr"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "li":
            self.parts.append("\n- ")
        elif tag == "sup":
            self.parts.append("^")
        elif tag in self.BLOCK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in self.BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def html_to_text(content: str | None) -> str:
    """Convert LeetCode's statement HTML to plain text for the LLM prompt only.

    The result must never be written to disk.
    """
    if not content:
        return ""
    parser = _TextExtractor()
    parser.feed(content)
    parser.close()
    text = "".join(parser.parts).replace("\xa0", " ")
    lines = [line.rstrip() for line in text.splitlines()]
    out: list[str] = []
    for line in lines:
        if line or (out and out[-1]):
            out.append(line)
    return "\n".join(out).strip()


def _tags(raw: list[dict] | None) -> list[Tag]:
    return [Tag(name=t.get("name", t["slug"]), slug=t["slug"]) for t in (raw or [])]


class LeetCodeClient:
    """Minimal LeetCode client with retries and typed results."""

    def __init__(
        self,
        session: requests.Session | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.session = session or requests.Session()
        self.sleep = sleep

    # ---- transport ---------------------------------------------------------

    def _request(self, method: str, url: str, **kwargs: Any) -> Any:
        """Send a request, retrying network errors, 403/429 and 5xx with backoff."""
        last_error = "unknown error"
        for attempt in range(ATTEMPTS):
            try:
                resp = self.session.request(method, url, headers=HEADERS, timeout=TIMEOUT_SECONDS, **kwargs)
            except requests.RequestException as exc:
                last_error = f"{type(exc).__name__}: {exc}"
            else:
                status = resp.status_code
                if status in (403, 429) or status >= 500:
                    last_error = f"HTTP {status}"
                elif status > 400:
                    raise LeetCodeError(f"{method} {url} failed: HTTP {status}: {resp.text[:200]}")
                else:
                    # 2xx, or 400 which carries GraphQL validation errors as JSON.
                    try:
                        return resp.json()
                    except ValueError:
                        if status == 400:
                            raise LeetCodeError(f"{method} {url} failed: HTTP 400: {resp.text[:200]}") from None
                        last_error = f"HTTP {status}: non-JSON response"  # e.g. a bot-check page
            if attempt < ATTEMPTS - 1:
                self.sleep(BACKOFF_BASE_SECONDS * 2**attempt)
        raise LeetCodeError(f"{method} {url} failed after {ATTEMPTS} attempts: {last_error}")

    def graphql(self, query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
        """Run a GraphQL query and return its `data` object.

        Raises LeetCodeError if the response carries `errors` or no data.
        """
        payload = self._request("POST", Q.GRAPHQL_URL, json={"query": query, "variables": variables or {}})
        if not isinstance(payload, dict):
            raise LeetCodeError("GraphQL response is not an object")
        if payload.get("errors"):
            messages = "; ".join(str(e.get("message", e)) for e in payload["errors"])
            raise LeetCodeError(f"GraphQL error: {messages}")
        data = payload.get("data")
        if not isinstance(data, dict):
            raise LeetCodeError("GraphQL response has no data")
        return data

    # ---- queries -----------------------------------------------------------

    def get_daily(self) -> DailyChallenge:
        """Today's official daily challenge."""
        d = self.graphql(Q.DAILY_PROBLEM)["activeDailyCodingChallengeQuestion"]
        if not d:
            raise LeetCodeError("no active daily challenge")
        q = d["question"]
        return DailyChallenge(
            date=d["date"],
            link=d["link"],
            question=QuestionSummary(
                frontend_id=str(q["questionFrontendId"]),
                title=q["title"],
                slug=q["titleSlug"],
                difficulty=normalize_difficulty(q["difficulty"]),
                paid_only=bool(q["isPaidOnly"]),
                tags=_tags(q.get("topicTags")),
            ),
        )

    def get_question(self, slug: str) -> QuestionDetail:
        """Full question detail, including statement HTML and code snippets."""
        q = self.graphql(Q.QUESTION_DETAIL, {"titleSlug": slug})["question"]
        if not q:
            raise LeetCodeError(f"question not found: {slug}")
        return QuestionDetail(
            frontend_id=str(q["questionFrontendId"]),
            title=q["title"],
            slug=q["titleSlug"],
            difficulty=normalize_difficulty(q["difficulty"]),
            paid_only=bool(q["isPaidOnly"]),
            content_html=q.get("content") or "",
            example_testcases=q.get("exampleTestcases") or "",
            code_snippets={s["langSlug"]: s["code"] for s in (q.get("codeSnippets") or [])},
            tags=_tags(q.get("topicTags")),
        )

    def get_problem_list(self) -> tuple[list[Problem], str]:
        """All algorithm problems, normalized. Returns (problems, source).

        Tries `questionList`, then `problemsetQuestionListV2`, then the REST
        endpoint. Raises LeetCodeError only if all three fail.
        """
        errors: list[str] = []
        for name, fetch in (
            ("questionList", self._problem_list_v1),
            ("problemsetQuestionListV2", self._problem_list_v2),
            ("rest", self._problem_list_rest),
        ):
            try:
                problems = fetch()
            except (LeetCodeError, KeyError, TypeError, ValueError) as exc:
                errors.append(f"{name}: {exc}")
                continue
            if problems:
                return problems, name
            errors.append(f"{name}: empty list")
        raise LeetCodeError("all problem list sources failed: " + " | ".join(errors))

    def _problem_list_v1(self) -> list[Problem]:
        data = self.graphql(Q.PROBLEM_LIST, {"categorySlug": Q.PROBLEM_CATEGORY})
        return [
            Problem(
                frontend_id=str(q["questionFrontendId"]),
                title=q["title"],
                slug=q["titleSlug"],
                difficulty=normalize_difficulty(q["difficulty"]),
                ac_rate=round(float(q["acRate"] or 0.0), 2),
                paid_only=bool(q["isPaidOnly"]),
                tags=[t["slug"] for t in (q.get("topicTags") or [])],
            )
            for q in data["problemsetQuestionList"]["questions"]
        ]

    def _problem_list_v2(self) -> list[Problem]:
        problems: list[Problem] = []
        skip, limit = 0, 100
        while True:
            data = self.graphql(
                Q.PROBLEM_LIST_V2, {"categorySlug": Q.PROBLEM_CATEGORY, "skip": skip, "limit": limit}
            )["problemsetQuestionListV2"]
            for q in data["questions"]:
                problems.append(
                    Problem(
                        frontend_id=str(q["questionFrontendId"]),
                        title=q["title"],
                        slug=q["titleSlug"],
                        difficulty=normalize_difficulty(q["difficulty"]),
                        ac_rate=round(float(q["acRate"] or 0.0) * 100, 2),
                        paid_only=bool(q["paidOnly"]),
                        tags=[t["slug"] for t in (q.get("topicTags") or [])],
                    )
                )
            skip += limit
            if not data.get("hasMore") or not data["questions"]:
                return problems

    def _problem_list_rest(self) -> list[Problem]:
        data = self._request("GET", Q.REST_PROBLEMS_URL)
        problems = []
        for pair in data["stat_status_pairs"]:
            stat = pair["stat"]
            if stat.get("question__hide"):
                continue
            submitted = stat.get("total_submitted") or 0
            problems.append(
                Problem(
                    frontend_id=str(stat["frontend_question_id"]),
                    title=stat["question__title"],
                    slug=stat["question__title_slug"],
                    difficulty=normalize_difficulty(str(pair["difficulty"]["level"])),
                    ac_rate=round(100.0 * (stat.get("total_acs") or 0) / submitted, 2) if submitted else 0.0,
                    paid_only=bool(pair["paid_only"]),
                    tags=[],  # REST has no topic tags; picker falls back to "any candidate"
                )
            )
        problems.sort(key=lambda p: int(p.frontend_id) if p.frontend_id.isdigit() else 10**9)
        return problems

    def get_user_stats(self, username: str) -> UserStats:
        """Solved counts, ranking, active days and submission calendar."""
        user = self.graphql(Q.USER_STATS, {"u": username})["matchedUser"]
        if not user:
            raise LeetCodeError(f"LeetCode user not found: {username!r}")
        counts = {c["difficulty"]: int(c["count"]) for c in user["submitStatsGlobal"]["acSubmissionNum"]}
        easy, medium, hard = counts.get("Easy", 0), counts.get("Medium", 0), counts.get("Hard", 0)
        calendar = user.get("userCalendar") or {}
        ranking = (user.get("profile") or {}).get("ranking")
        return UserStats(
            total=counts.get("All", easy + medium + hard),
            easy=easy,
            medium=medium,
            hard=hard,
            ranking=int(ranking) if ranking else None,
            active_days=int(calendar.get("totalActiveDays") or 0),
            calendar=parse_calendar(calendar.get("submissionCalendar")),
        )

    def get_calendar(self, username: str, year: int) -> dict[int, int]:
        """Submission calendar for one specific year."""
        user = self.graphql(Q.USER_CALENDAR_YEAR, {"u": username, "year": year})["matchedUser"]
        if not user:
            raise LeetCodeError(f"LeetCode user not found: {username!r}")
        return parse_calendar((user.get("userCalendar") or {}).get("submissionCalendar"))

    def get_recent_ac(self, username: str, limit: int = 20) -> list[AcSubmission]:
        """Most recent accepted submissions (public profile, newest first)."""
        items = self.graphql(Q.RECENT_AC, {"u": username, "limit": limit})["recentAcSubmissionList"] or []
        return [
            AcSubmission(id=str(s["id"]), title=s["title"], slug=s["titleSlug"], timestamp=int(s["timestamp"]))
            for s in items
        ]

    def get_recent_submissions(self, username: str, limit: int = 20) -> list[Submission]:
        """Most recent submissions of any status, with the language used."""
        items = self.graphql(Q.RECENT_SUBMISSIONS, {"u": username, "limit": limit})["recentSubmissionList"] or []
        return [
            Submission(
                slug=s["titleSlug"], timestamp=int(s["timestamp"]), status=s.get("statusDisplay") or "", lang=s.get("lang") or ""
            )
            for s in items
        ]
