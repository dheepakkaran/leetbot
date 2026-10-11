"""Telegram Bot API: send, edit (with fallback chain), react, reply."""

from __future__ import annotations

import time
from typing import Any, Callable, Protocol

import requests

from src.messages import Buttons

ATTEMPTS = 3
TIMEOUT_SECONDS = 30
MAX_RETRY_AFTER_SECONDS = 30


class TelegramError(RuntimeError):
    """A Bot API call failed."""

    def __init__(self, method: str, description: str, status: int | None = None) -> None:
        super().__init__(f"{method}: {description}")
        self.method = method
        self.description = description
        self.status = status


def is_not_modified(err: TelegramError) -> bool:
    """`message is not modified` means the edit is already in place."""
    return "message is not modified" in err.description.lower()


class TelegramClient:
    """Thin wrapper around the Bot API methods this bot uses."""

    def __init__(
        self,
        token: str,
        chat_id: str,
        session: requests.Session | None = None,
        sleep: Callable[[float], None] = time.sleep,
        log: Callable[[str], None] = print,
    ) -> None:
        if not token or not chat_id:
            raise ValueError("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set")
        self.base_url = f"https://api.telegram.org/bot{token}/"
        self.chat_id = chat_id
        self.session = session or requests.Session()
        self.sleep = sleep
        self.log = log

    def _call(self, method: str, payload: dict[str, Any]) -> Any:
        """POST a Bot API method; retries network errors, 429 and 5xx."""
        description = "unknown error"
        status: int | None = None
        for attempt in range(ATTEMPTS):
            delay = 2.0 * 2**attempt
            try:
                resp = self.session.post(self.base_url + method, json=payload, timeout=TIMEOUT_SECONDS)
            except requests.RequestException as exc:
                description = f"{type(exc).__name__}"  # never include the URL: it holds the token
            else:
                status = resp.status_code
                try:
                    body = resp.json()
                except ValueError:
                    body = {"ok": False, "description": f"HTTP {status}: non-JSON response"}
                if body.get("ok"):
                    return body.get("result")
                description = str(body.get("description") or f"HTTP {status}")
                retry_after = (body.get("parameters") or {}).get("retry_after")
                if status == 429 and retry_after is not None:
                    delay = float(retry_after)
                if status != 429 and status < 500:
                    raise TelegramError(method, description, status)
                if delay > MAX_RETRY_AFTER_SECONDS:
                    break
            if attempt < ATTEMPTS - 1:
                self.sleep(delay)
        raise TelegramError(method, description, status)

    @staticmethod
    def _markup(buttons: Buttons | None) -> dict[str, Any] | None:
        return {"inline_keyboard": buttons} if buttons else None

    def _message_payload(self, text: str, buttons: Buttons | None) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML",
            "link_preview_options": {"is_disabled": True},
        }
        markup = self._markup(buttons)
        if markup:
            payload["reply_markup"] = markup
        return payload

    def send_message(self, text: str, buttons: Buttons | None = None, reply_to: int | None = None) -> int:
        """Send an HTML message; returns its message_id."""
        payload = self._message_payload(text, buttons)
        if reply_to is not None:
            payload["reply_parameters"] = {"message_id": int(reply_to)}
        result = self._call("sendMessage", payload)
        return int(result["message_id"])

    def edit_message_text(self, message_id: int, text: str, buttons: Buttons | None = None) -> None:
        """Edit a message. `message is not modified` counts as success."""
        payload = self._message_payload(text, buttons)
        payload["message_id"] = int(message_id)
        try:
            self._call("editMessageText", payload)
        except TelegramError as err:
            if not is_not_modified(err):
                raise

    def set_reaction(self, message_id: int, emoji: str) -> bool:
        """React to a message. Failures are logged and ignored."""
        try:
            self._call(
                "setMessageReaction",
                {"chat_id": self.chat_id, "message_id": int(message_id), "reaction": [{"type": "emoji", "emoji": emoji}]},
            )
            return True
        except TelegramError as err:
            self.log(f"[telegram] reaction ignored: {err}")
            return False

    def edit_with_fallback(
        self,
        message_id: int,
        text: str,
        buttons: Buttons | None,
        reply_text: str,
        reply_buttons: Buttons | None = None,
    ) -> str:
        """Edit the message; if that fails, reply to it; if that fails, send standalone.

        Returns "edited", "replied" or "sent".
        """
        try:
            self.edit_message_text(message_id, text, buttons)
            return "edited"
        except TelegramError as err:
            self.log(f"[telegram] edit failed ({err.description}); replying instead")
        try:
            self.send_message(reply_text, reply_buttons, reply_to=message_id)
            return "replied"
        except TelegramError as err:
            self.log(f"[telegram] reply failed ({err.description}); sending standalone")
        self.send_message(text, buttons)
        return "sent"


class Messenger(Protocol):
    """What the jobs need from Telegram (real client or dry-run printer)."""

    def send_message(self, text: str, buttons: Buttons | None = None, reply_to: int | None = None) -> int: ...

    def edit_with_fallback(
        self, message_id: int, text: str, buttons: Buttons | None, reply_text: str, reply_buttons: Buttons | None = None
    ) -> str: ...

    def set_reaction(self, message_id: int, emoji: str) -> bool: ...


def _print_buttons(buttons: Buttons | None) -> str:
    if not buttons:
        return ""
    return "\n" + "  ".join(f"[{b['text']} → {b['url']}]" for row in buttons for b in row)


class DryRunMessenger:
    """Prints messages instead of sending them."""

    def __init__(self, log: Callable[[str], None] = print) -> None:
        self.log = log

    def send_message(self, text: str, buttons: Buttons | None = None, reply_to: int | None = None) -> int:
        target = f" (reply to {reply_to})" if reply_to else ""
        self.log(f"----- [dry-run] sendMessage{target} -----\n{text}{_print_buttons(buttons)}\n-----")
        return 0

    def edit_with_fallback(
        self, message_id: int, text: str, buttons: Buttons | None, reply_text: str, reply_buttons: Buttons | None = None
    ) -> str:
        self.log(f"----- [dry-run] editMessageText {message_id} -----\n{text}{_print_buttons(buttons)}\n-----")
        return "edited"

    def set_reaction(self, message_id: int, emoji: str) -> bool:
        self.log(f"[dry-run] setMessageReaction {message_id} {emoji}")
        return True
