from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any
from urllib import error, request

from bot_service.config import AppConfig
from bot_service.logic import MessageContext


class CozeAPIError(RuntimeError):
    pass


@dataclass
class ChatResult:
    text: str
    conversation_id: str


class ConversationStore:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._items = self._load()

    def get(self, key: str) -> str:
        return self._items.get(key, "")

    def set(self, key: str, conversation_id: str) -> None:
        if not conversation_id:
            return
        self._items[key] = conversation_id
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps(self._items, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _load(self) -> dict[str, str]:
        if not self._path.exists():
            return {}
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        if not isinstance(data, dict):
            return {}
        return {str(key): str(value) for key, value in data.items()}


class CozeAPI:
    def __init__(self, config: AppConfig) -> None:
        self._base_url = config.coze_api_base_url
        self._access_token = config.coze_access_token
        self._bot_id = config.coze_bot_id
        self._timeout = config.coze_timeout_seconds

    @property
    def enabled(self) -> bool:
        return bool(self._access_token and self._bot_id)

    def send_message(self, ctx: MessageContext, conversation_id: str = "") -> ChatResult:
        if not self.enabled:
            raise CozeAPIError("Missing COZE_ACCESS_TOKEN or COZE_BOT_ID")

        payload: dict[str, Any] = {
            "bot_id": self._bot_id,
            "user_id": ctx.sender_open_id or ctx.chat_id,
            "stream": True,
            "auto_save_history": True,
            "additional_messages": [
                {
                    "role": "user",
                    "content": ctx.text,
                    "content_type": "text",
                }
            ],
        }
        if conversation_id:
            payload["conversation_id"] = conversation_id

        response = self._post_stream("/v3/chat", payload)
        text = response.text.strip()
        if not text:
            raise CozeAPIError("Coze returned an empty answer")
        return response

    def _post_stream(self, path: str, payload: dict[str, Any]) -> ChatResult:
        req = request.Request(
            url=self._base_url + path,
            method="POST",
            headers={
                "Authorization": f"Bearer {self._access_token}",
                "Content-Type": "application/json; charset=utf-8",
            },
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        )

        try:
            with request.urlopen(req, timeout=self._timeout) as resp:
                return self._read_sse(resp)
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise CozeAPIError(f"HTTP {exc.code} calling {path}: {detail}") from exc
        except error.URLError as exc:
            raise CozeAPIError(f"Network error calling {path}: {exc}") from exc

    def _read_sse(self, resp: Any) -> ChatResult:
        event = ""
        data_lines: list[str] = []
        answer_parts: list[str] = []
        conversation_id = ""

        def flush() -> None:
            nonlocal event, data_lines, conversation_id
            if not data_lines:
                event = ""
                return

            raw_data = "\n".join(data_lines).strip()
            data_lines.clear()
            if raw_data == "[DONE]":
                event = ""
                return

            try:
                data = json.loads(raw_data)
            except json.JSONDecodeError:
                event = ""
                return

            if isinstance(data, dict):
                conversation_id = str(data.get("conversation_id") or conversation_id)
                if event == "conversation.chat.failed":
                    raise CozeAPIError(
                        data.get("last_error", {}).get("msg")
                        or data.get("msg")
                        or "Coze chat failed"
                    )
                if event == "conversation.message.completed":
                    if data.get("type") == "answer" and data.get("content_type") == "text":
                        content = str(data.get("content") or "").strip()
                        if content:
                            answer_parts.append(content)
            event = ""

        while True:
            line = resp.readline()
            if not line:
                flush()
                break

            decoded = line.decode("utf-8", errors="replace").rstrip("\r\n")
            if decoded == "":
                flush()
            elif decoded.startswith("event:"):
                event = decoded.removeprefix("event:").strip()
            elif decoded.startswith("data:"):
                data_lines.append(decoded.removeprefix("data:").strip())

        return ChatResult(text="\n".join(answer_parts), conversation_id=conversation_id)
