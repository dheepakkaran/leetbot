import json
from typing import Any

import pytest
import requests

from src.llm import LLMClient, build_messages, extract_json, parse_solution, strip_think
from tests.conftest import solution_json


def test_strip_think() -> None:
    assert strip_think("<think>long\nreasoning</think>{\"a\": 1}") == '{"a": 1}'
    assert extract_json("<think>{not json}</think>\n{\"a\": 1}") == {"a": 1}


def test_fenced_json() -> None:
    payload = json.dumps(solution_json())
    assert extract_json(f"```json\n{payload}\n```") == solution_json()
    assert extract_json(f"Here you go:\n```\n{payload}\n```\nGood luck!") == solution_json()
    assert extract_json(f"<think>hmm</think>\n```json\n{payload}\n```") == solution_json()


def test_raw_newlines_inside_strings_are_tolerated() -> None:
    text = '{"hint": "h", "optimal": {"code": "line1\nline2"}}'
    assert parse_solution(text)["optimal"]["code"] == "line1\nline2"


def test_null_brute_force_and_validation() -> None:
    data = solution_json() | {"brute_force": None}
    assert parse_solution(json.dumps(data))["brute_force"] is None
    with pytest.raises(ValueError):
        parse_solution('{"hint": "no optimal"}')
    with pytest.raises(ValueError):
        extract_json("no json at all")


class Resp:
    def __init__(self, status: int, body: Any = None, headers: dict[str, str] | None = None) -> None:
        self.status_code = status
        self._body = body
        self.text = json.dumps(body) if body is not None else ""
        self.headers = headers or {}

    def json(self) -> Any:
        return self._body


def chat(content: str) -> Resp:
    return Resp(200, {"choices": [{"message": {"content": content}}]})


class Session:
    def __init__(self, script: list[Any]) -> None:
        self.script = script
        self.calls: list[dict[str, Any]] = []

    def post(self, url: str, headers: dict[str, str], json: dict[str, Any], timeout: int) -> Resp:
        self.calls.append({"model": json["model"], "messages": json["messages"], "auth": headers["Authorization"], "payload": json})
        item = self.script.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def client(script: list[Any], models=("m1", "m2", "m3"), api_key: str = "tok", **kw: Any) -> tuple[LLMClient, Session]:
    session = Session(script)
    return (
        LLMClient(
            endpoint="https://models.github.ai/inference/chat/completions",
            models=list(models),
            api_key=api_key,
            temperature=0.2,
            max_retries_per_model=2,
            session=session,
            sleep=lambda s: None,
            log=lambda m: None,
            **kw,
        ),
        session,
    )


GOOD = json.dumps(solution_json())


def test_first_model_success() -> None:
    llm, session = client([chat(GOOD)])
    result = llm.generate([{"role": "user", "content": "x"}])
    assert result.model == "m1" and result.data["pattern"] == "Hash Map"
    assert session.calls[0]["auth"] == "Bearer tok"


def test_404_falls_back_to_next_model() -> None:
    llm, session = client([Resp(404, {"error": {"code": "unknown_model"}}), chat(GOOD)])
    result = llm.generate([{"role": "user", "content": "x"}])
    assert result.model == "m2"
    assert [c["model"] for c in session.calls] == ["m1", "m2"]


def test_unknown_model_400_falls_back() -> None:
    llm, _ = client([Resp(400, {"error": {"code": "unknown_model", "message": "Unknown model: m1"}}), chat(GOOD)])
    assert llm.generate([{"role": "user", "content": "x"}]).model == "m2"


def test_retries_429_and_5xx_then_next_model() -> None:
    llm, session = client([Resp(429, {}), Resp(503, {}), Resp(500, {}), chat(GOOD)])
    result = llm.generate([{"role": "user", "content": "x"}])
    assert result.model == "m2"
    assert [c["model"] for c in session.calls] == ["m1", "m1", "m1", "m2"]  # 1 try + 2 retries


def test_reasks_once_on_bad_json() -> None:
    llm, session = client([chat("Sure! Here's the idea..."), chat(f"```json\n{GOOD}\n```")])
    result = llm.generate([{"role": "user", "content": "x"}])
    assert result.model == "m1"
    assert session.calls[1]["messages"][-1] == {"role": "user", "content": "Return ONLY valid JSON."}


def test_none_after_all_models_fail() -> None:
    llm, _ = client([
        Resp(404, {}),
        chat("garbage"), chat("still garbage"),
        requests.ConnectionError("down"), requests.ConnectionError("down"), requests.ConnectionError("down"),
    ])
    assert llm.generate([{"role": "user", "content": "x"}]) is None


def test_no_key_returns_none_without_calls() -> None:
    logs: list[str] = []
    llm, session = client([], api_key="", api_key_name="GEMINI_API_KEY")
    llm.log = logs.append
    assert llm.generate([{"role": "user", "content": "x"}]) is None
    assert session.calls == [] and "GEMINI_API_KEY is not set" in logs[0]


def test_payload_includes_reasoning_effort_and_max_tokens() -> None:
    llm, session = client([chat(GOOD)], reasoning_effort="medium", max_output_tokens=16000)
    llm.generate([{"role": "user", "content": "x"}])
    payload = session.calls[0]["payload"]
    assert payload["reasoning_effort"] == "medium" and payload["max_tokens"] == 16000
    assert payload["temperature"] == 0.2


def test_reasoning_effort_omitted_when_unset() -> None:
    llm, session = client([chat(GOOD)])
    llm.generate([{"role": "user", "content": "x"}])
    assert "reasoning_effort" not in session.calls[0]["payload"]


def test_prompt_contents() -> None:
    msgs = build_messages(
        frontend_id="1", title="Two Sum", difficulty="Easy", tags=["Array", "Hash Table"],
        statement="Given nums...", example_testcases="[2,7]\n9", snippet="class Solution {\npublic:\n};",
        language_display="C++", fence="cpp",
    )
    assert msgs[0]["content"].startswith("You are an expert competitive programmer and interview coach.")
    user = msgs[1]["content"]
    for needle in ("Two Sum", "Easy", "Array, Hash Table", "Given nums...", "[2,7]\n9", "class Solution {",
                   "Target language: C++", '"brute_force"', "compile/run on LeetCode as-is",
                   "Mentally verify", 'set "brute_force" to null'):
        assert needle in user
