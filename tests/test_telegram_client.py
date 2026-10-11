"""Telegram client: request options, "not modified", retries and the edit fallback chain."""

from typing import Any

import pytest

from src.telegram_client import DryRunMessenger, TelegramClient, TelegramError


class FakeResponse:
    def __init__(self, status: int, body: dict[str, Any]) -> None:
        self.status_code = status
        self._body = body

    def json(self) -> dict[str, Any]:
        return self._body


class FakeSession:
    def __init__(self, responses: dict[str, list[FakeResponse]]) -> None:
        self.responses = responses
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def post(self, url: str, json: dict[str, Any], timeout: int) -> FakeResponse:
        method = url.rsplit("/", 1)[1]
        self.calls.append((method, json))
        return self.responses[method].pop(0)


def ok(result: Any = True) -> FakeResponse:
    return FakeResponse(200, {"ok": True, "result": result})


def err(desc: str, status: int = 400) -> FakeResponse:
    return FakeResponse(status, {"ok": False, "error_code": status, "description": desc})


def client(responses) -> tuple[TelegramClient, FakeSession]:
    session = FakeSession(responses)
    return TelegramClient("TOKEN", "42", session=session, sleep=lambda s: None, log=lambda m: None), session


def test_message_not_modified_counts_as_success() -> None:
    tg, session = client({"editMessageText": [err("Bad Request: message is not modified: specified new message content ...")]})
    assert tg.edit_with_fallback(5, "text", None, "reply") == "edited"
    assert [m for m, _ in session.calls] == ["editMessageText"]


def test_fallback_chain_order_reply_then_standalone() -> None:
    tg, session = client({
        "editMessageText": [err("Bad Request: message to edit not found")],
        "sendMessage": [err("Bad Request: message to be replied not found"), ok({"message_id": 9})],
    })
    assert tg.edit_with_fallback(5, "full text", [[{"text": "x", "url": "https://x"}]], "short reply") == "sent"
    methods = [m for m, _ in session.calls]
    assert methods == ["editMessageText", "sendMessage", "sendMessage"]
    assert session.calls[1][1]["reply_parameters"] == {"message_id": 5}
    assert session.calls[1][1]["text"] == "short reply"
    assert "reply_parameters" not in session.calls[2][1]
    assert session.calls[2][1]["text"] == "full text"


def test_fallback_reply_succeeds() -> None:
    tg, session = client({
        "editMessageText": [err("Bad Request: message can't be edited")],
        "sendMessage": [ok({"message_id": 10})],
    })
    assert tg.edit_with_fallback(5, "full", None, "short") == "replied"
    assert [m for m, _ in session.calls] == ["editMessageText", "sendMessage"]


def test_send_options_and_reaction_failure_ignored() -> None:
    tg, session = client({"sendMessage": [ok({"message_id": 77})], "setMessageReaction": [err("REACTION_INVALID")]})
    buttons = [[{"text": "Open problem", "url": "https://leetcode.com/problems/a/"}]]
    assert tg.send_message("<b>hi</b>", buttons) == 77
    payload = session.calls[0][1]
    assert payload["parse_mode"] == "HTML"
    assert payload["link_preview_options"] == {"is_disabled": True}
    assert payload["reply_markup"] == {"inline_keyboard": buttons}
    assert tg.set_reaction(77, "💯") is False
    assert session.calls[1][1]["reaction"] == [{"type": "emoji", "emoji": "💯"}]


def test_retries_on_429_then_raises() -> None:
    tg, session = client({"sendMessage": [err("Too Many Requests", 429)] * 3})
    with pytest.raises(TelegramError):
        tg.send_message("x")
    assert len(session.calls) == 3


def test_client_requires_credentials() -> None:
    with pytest.raises(ValueError):
        TelegramClient("", "42")


def test_dry_run_messenger_prints() -> None:
    out: list[str] = []
    m = DryRunMessenger(log=out.append)
    assert m.send_message("hi", [[{"text": "Open", "url": "https://x"}]]) == 0
    assert m.edit_with_fallback(3, "edited", None, "reply") == "edited"
    assert m.set_reaction(3, "💯")
    assert "hi" in out[0] and "[Open → https://x]" in out[0] and "editMessageText 3" in out[1]
