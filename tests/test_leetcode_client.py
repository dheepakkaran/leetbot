from typing import Any

import pytest
import requests

from src.leetcode_client import LeetCodeClient, LeetCodeError, html_to_text, normalize_difficulty, parse_calendar


class Resp:
    def __init__(self, status: int, body: Any) -> None:
        self.status_code = status
        self._body = body
        self.text = str(body)

    def json(self) -> Any:
        if isinstance(self._body, Exception):
            raise self._body
        return self._body


class Session:
    def __init__(self, script: list[Any]) -> None:
        self.script = script
        self.calls: list[tuple[str, str, dict[str, Any]]] = []

    def request(self, method: str, url: str, headers: dict[str, str], timeout: int, **kw: Any) -> Resp:
        self.calls.append((method, url, {"headers": headers, **kw}))
        item = self.script.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def client(script: list[Any]) -> tuple[LeetCodeClient, Session, list[float]]:
    sleeps: list[float] = []
    session = Session(script)
    return LeetCodeClient(session=session, sleep=sleeps.append), session, sleeps


def test_headers_and_daily_parsing() -> None:
    body = {"data": {"activeDailyCodingChallengeQuestion": {"date": "2026-10-10", "link": "/problems/x/", "question": {
        "questionFrontendId": "2333", "title": "  Trailing Space ", "titleSlug": "x", "difficulty": "Medium", "isPaidOnly": False,
        "topicTags": [{"name": "Array", "slug": "array"}]}}}}
    lc, session, _ = client([Resp(200, body)])
    daily = lc.get_daily()
    assert daily.question.frontend_id == "2333" and daily.question.tags[0].slug == "array"
    assert daily.question.title == "Trailing Space"  # LeetCode titles can carry stray whitespace
    method, url, kw = session.calls[0]
    assert (method, url) == ("POST", "https://leetcode.com/graphql")
    assert kw["headers"]["Referer"] == "https://leetcode.com"
    assert kw["headers"]["Content-Type"] == "application/json"
    assert "Mozilla/5.0" in kw["headers"]["User-Agent"]


def test_retries_with_exponential_backoff_then_clear_error() -> None:
    lc, session, sleeps = client([requests.ConnectionError("x"), Resp(502, {}), Resp(429, {})])
    with pytest.raises(LeetCodeError, match="after 3 attempts"):
        lc.get_daily()
    assert len(session.calls) == 3 and sleeps == [2, 4]


def test_retry_then_success() -> None:
    body = {"data": {"recentAcSubmissionList": [{"id": "9", "title": "A", "titleSlug": "a", "timestamp": "1781923206"}]}}
    lc, _, sleeps = client([Resp(503, {}), Resp(200, body)])
    [ac] = lc.get_recent_ac("u")
    assert (ac.id, ac.slug, ac.timestamp) == ("9", "a", 1781923206) and sleeps == [2]


def test_graphql_errors_are_not_retried() -> None:
    lc, session, _ = client([Resp(400, {"errors": [{"message": "Cannot query field"}]})])
    with pytest.raises(LeetCodeError, match="Cannot query field"):
        lc.get_daily()
    assert len(session.calls) == 1


def test_user_stats() -> None:
    body = {"data": {"allQuestionsCount": [], "matchedUser": {
        "profile": {"ranking": 2266342},
        "submitStatsGlobal": {"acSubmissionNum": [
            {"difficulty": "All", "count": 67}, {"difficulty": "Easy", "count": 37},
            {"difficulty": "Medium", "count": 30}, {"difficulty": "Hard", "count": 0}]},
        "userCalendar": {"streak": 4, "totalActiveDays": 4, "submissionCalendar": "{\"1781654400\": 1}"}}}}
    lc, _, _ = client([Resp(200, body)])
    s = lc.get_user_stats("u")
    assert (s.total, s.easy, s.medium, s.hard, s.ranking, s.active_days) == (67, 37, 30, 0, 2266342, 4)
    assert s.calendar == {1781654400: 1}


def test_unknown_user() -> None:
    lc, _, _ = client([Resp(200, {"data": {"allQuestionsCount": [], "matchedUser": None}})])
    with pytest.raises(LeetCodeError, match="not found"):
        lc.get_user_stats("nobody")


def test_problem_list_fallback_chain_normalizes() -> None:
    v1_fail = Resp(400, {"errors": [{"message": "boom"}]})
    v2_page = {"data": {"problemsetQuestionListV2": {"totalLength": 1, "hasMore": False, "questions": [
        {"questionFrontendId": "1", "title": "Two Sum", "titleSlug": "two-sum", "difficulty": "EASY",
         "acRate": 0.58, "paidOnly": False, "topicTags": [{"slug": "array"}]}]}}}
    lc, _, _ = client([v1_fail, Resp(200, v2_page)])
    problems, source = lc.get_problem_list()
    assert source == "problemsetQuestionListV2"
    p = problems[0]
    assert (p.difficulty, p.ac_rate, p.tags, p.paid_only) == ("Easy", 58.0, ["array"], False)

    rest = {"stat_status_pairs": [{"stat": {"question__title": "Two Sum", "question__title_slug": "two-sum",
            "frontend_question_id": 1, "total_acs": 58, "total_submitted": 100, "question__hide": False},
            "difficulty": {"level": 1}, "paid_only": False}]}
    lc, _, _ = client([v1_fail, Resp(400, {"errors": [{"message": "v2 gone"}]}), Resp(200, rest)])
    problems, source = lc.get_problem_list()
    assert source == "rest" and problems[0].ac_rate == 58.0 and problems[0].difficulty == "Easy"


def test_helpers() -> None:
    assert normalize_difficulty("MEDIUM") == "Medium" and normalize_difficulty("3") == "Hard"
    assert parse_calendar('{"10": 2}') == {10: 2} and parse_calendar(None) == {}
    text = html_to_text("<p>Given <code>nums</code>&nbsp;and x<sup>2</sup>.</p><ul><li>one</li><li>two</li></ul>")
    assert "Given nums and x^2." in text and "- one" in text and "- two" in text
