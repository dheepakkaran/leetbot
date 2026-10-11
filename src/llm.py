"""OpenAI-compatible chat client (Gemini by default) with a model fallback chain and JSON parsing."""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from typing import Any, Callable

import requests

SYSTEM_PROMPT = (
    "You are an expert competitive programmer and interview coach. "
    "You write correct, idiomatic, interview-quality solutions."
)

JSON_SCHEMA = """{
  "hint": "one short line, no spoilers of the full approach",
  "pattern": "e.g. Binary Search",
  "brute_force": {"idea": "...", "time": "O(...)", "space": "O(...)", "code": "..."},
  "optimal": {"idea": "...", "steps": ["...", "..."], "time": "O(...)", "space": "O(...)", "code": "..."},
  "edge_cases": ["...", "..."],
  "dry_run": "walkthrough of example 1 with concrete values"
}"""

REASK = "Return ONLY valid JSON."
MAX_STATEMENT_CHARS = 12_000
MAX_EXAMPLE_CHARS = 3_000
BACKOFF_BASE_SECONDS = 2
MAX_RETRY_AFTER_SECONDS = 30
TIMEOUT_SECONDS = 180


class LLMError(RuntimeError):
    """A request to one model failed."""


class ModelUnavailable(LLMError):
    """The model ID is unknown/unavailable (404 or unknown_model): try the next one."""


@dataclass(frozen=True)
class LLMResult:
    data: dict[str, Any]
    model: str


def build_messages(
    *,
    frontend_id: str,
    title: str,
    difficulty: str,
    tags: list[str],
    statement: str,
    example_testcases: str,
    snippet: str,
    language_display: str,
    fence: str,
) -> list[dict[str, str]]:
    """Build the chat messages for one solution request (§10 prompt)."""
    statement = statement[:MAX_STATEMENT_CHARS]
    examples = example_testcases.strip()[:MAX_EXAMPLE_CHARS] or "(none provided)"
    starter = snippet.strip() or f"(no {language_display} snippet available; use LeetCode's standard Solution class)"
    user = f"""Solve this LeetCode problem in {language_display}.

Title: {frontend_id}. {title}
Difficulty: {difficulty}
Tags: {", ".join(tags) or "none"}

Problem statement:
{statement}

Example test cases (raw LeetCode input, one argument per line):
{examples}

Exact LeetCode starter code for {language_display}. Your solution MUST use this exact class and method signature:
```{fence}
{starter}
```

Target language: {language_display}

Return a single JSON object with exactly this schema:
{JSON_SCHEMA}

Rules:
- The code must compile/run on LeetCode as-is: only the Solution class plus any helpers it needs, no main(), no I/O.
- Both "code" fields must be {language_display} and use the starter signature above.
- Mentally verify the optimal code on every example before answering.
- If brute force is already optimal, set "brute_force" to null.
- "hint" is one short line that nudges without spoiling the full approach.
- Return only the JSON object, with no Markdown and no commentary."""
    return [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user}]


_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)
_FENCE_RE = re.compile(r"```[a-zA-Z0-9_-]*[ \t]*\n(.*?)\n?```", re.DOTALL)


def strip_think(text: str) -> str:
    """Remove `<think>…</think>` reasoning blocks."""
    return _THINK_RE.sub("", text)


def extract_json(text: str) -> dict[str, Any]:
    """Parse the model's reply into a JSON object.

    Strips think blocks and code fences first, then falls back to the
    outermost `{...}` span. Raises ValueError if nothing parses.
    """
    cleaned = strip_think(text).strip()
    candidates: list[str] = []
    if cleaned.startswith("```"):
        body = cleaned.split("\n", 1)[1] if "\n" in cleaned else ""
        body = body.rstrip()
        if body.endswith("```"):
            body = body[:-3]
        candidates.append(body.strip())
    candidates.append(cleaned)
    match = _FENCE_RE.search(cleaned)
    if match:
        candidates.append(match.group(1).strip())
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if 0 <= start < end:
        candidates.append(cleaned[start:end + 1])
    for candidate in candidates:
        try:
            data = json.loads(candidate, strict=False)
        except ValueError:
            continue
        if isinstance(data, dict):
            return data
    raise ValueError("no JSON object found in model output")


def _as_str(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _as_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [_as_str(v) for v in value if _as_str(v)]
    return [_as_str(value)] if _as_str(value) else []


def normalize_solution(data: dict[str, Any]) -> dict[str, Any]:
    """Validate and normalize a parsed solution. Raises ValueError if unusable."""
    optimal = data.get("optimal")
    if not isinstance(optimal, dict) or not _as_str(optimal.get("code")):
        raise ValueError("missing optimal.code")
    brute = data.get("brute_force")
    if not isinstance(brute, dict) or not _as_str(brute.get("code")):
        brute = None
    out: dict[str, Any] = {
        "hint": _as_str(data.get("hint")),
        "pattern": _as_str(data.get("pattern")) or "Optimal approach",
        "brute_force": None,
        "optimal": {
            "idea": _as_str(optimal.get("idea")),
            "steps": _as_list(optimal.get("steps")),
            "time": _as_str(optimal.get("time")) or "?",
            "space": _as_str(optimal.get("space")) or "?",
            "code": _as_str(optimal.get("code")),
        },
        "edge_cases": _as_list(data.get("edge_cases")),
        "dry_run": _as_str(data.get("dry_run")),
    }
    if brute is not None:
        out["brute_force"] = {
            "idea": _as_str(brute.get("idea")),
            "time": _as_str(brute.get("time")) or "?",
            "space": _as_str(brute.get("space")) or "?",
            "code": _as_str(brute.get("code")),
        }
    return out


def parse_solution(text: str) -> dict[str, Any]:
    """extract_json + normalize_solution."""
    return normalize_solution(extract_json(text))


class LLMClient:
    """OpenAI-compatible chat completions client (Gemini's endpoint by default)."""

    def __init__(
        self,
        *,
        endpoint: str,
        models: list[str],
        api_key: str,
        temperature: float,
        max_retries_per_model: int,
        api_key_name: str = "API key",
        reasoning_effort: str | None = None,
        max_output_tokens: int = 4000,
        session: requests.Session | None = None,
        sleep: Callable[[float], None] = time.sleep,
        log: Callable[[str], None] = print,
    ) -> None:
        self.endpoint = endpoint
        self.models = models
        self.api_key = api_key
        self.api_key_name = api_key_name
        self.temperature = temperature
        self.reasoning_effort = reasoning_effort
        self.max_output_tokens = max_output_tokens
        self.max_retries = max_retries_per_model
        self.session = session or requests.Session()
        self.sleep = sleep
        self.log = log

    def _chat_once(self, model: str, messages: list[dict[str, str]]) -> str:
        """One HTTP call. Returns the reply text or raises (Retryable)LLMError."""
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_output_tokens,
        }
        if self.reasoning_effort:
            payload["reasoning_effort"] = self.reasoning_effort
        resp = self.session.post(
            self.endpoint,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            json=payload,
            timeout=TIMEOUT_SECONDS,
        )
        status = resp.status_code
        if status == 200:
            try:
                return resp.json()["choices"][0]["message"]["content"] or ""
            except (ValueError, KeyError, IndexError, TypeError) as exc:
                raise LLMError(f"{model}: malformed response ({exc})") from exc
        body = resp.text[:300]
        if status == 404 or "unknown_model" in body or "Unknown model" in body:
            raise ModelUnavailable(f"{model}: unavailable (HTTP {status})")
        if status == 429 or status >= 500:
            raise _Retryable(f"{model}: HTTP {status}: {body}", _retry_after(resp))
        raise LLMError(f"{model}: HTTP {status}: {body}")

    def _chat(self, model: str, messages: list[dict[str, str]]) -> str:
        """Call one model, retrying up to `max_retries` times on 429/5xx/network errors."""
        for attempt in range(self.max_retries + 1):
            try:
                return self._chat_once(model, messages)
            except requests.RequestException as exc:
                error: LLMError = _Retryable(f"{model}: {type(exc).__name__}: {exc}", None)
            except _Retryable as exc:
                error = exc
            if attempt == self.max_retries:
                raise LLMError(str(error))
            delay = BACKOFF_BASE_SECONDS * 2**attempt
            if isinstance(error, _Retryable) and error.retry_after is not None:
                if error.retry_after > MAX_RETRY_AFTER_SECONDS:
                    # e.g. a daily quota: waiting won't help, move to the next model
                    raise LLMError(f"{error} (Retry-After {error.retry_after:g}s)")
                delay = max(delay, error.retry_after)
            self.log(f"[llm] {error}; retrying in {delay:g}s")
            self.sleep(delay)
        raise LLMError(f"{model}: retries exhausted")  # pragma: no cover

    def generate(self, messages: list[dict[str, str]]) -> LLMResult | None:
        """Try each model in order. Returns None if every model fails."""
        if not self.api_key:
            self.log(f"[llm] {self.api_key_name} is not set; skipping solution generation")
            return None
        for model in self.models:
            try:
                reply = self._chat(model, messages)
            except LLMError as exc:
                self.log(f"[llm] {exc}; trying next model")
                continue
            try:
                return LLMResult(data=parse_solution(reply), model=model)
            except ValueError as exc:
                self.log(f"[llm] {model}: unparseable reply ({exc}); re-asking once")
            followup = messages + [
                {"role": "assistant", "content": reply},
                {"role": "user", "content": REASK},
            ]
            try:
                return LLMResult(data=parse_solution(self._chat(model, followup)), model=model)
            except (LLMError, ValueError) as exc:
                self.log(f"[llm] {model}: still unusable ({exc}); trying next model")
        self.log("[llm] all models failed")
        return None


class _Retryable(LLMError):
    def __init__(self, message: str, retry_after: float | None) -> None:
        super().__init__(message)
        self.retry_after = retry_after


def _retry_after(resp: requests.Response) -> float | None:
    try:
        return float(resp.headers.get("Retry-After", ""))
    except ValueError:
        return None
