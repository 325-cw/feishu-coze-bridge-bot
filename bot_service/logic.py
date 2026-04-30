from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json

from bot_service.config import AppConfig


@dataclass
class MessageContext:
    sender_open_id: str
    chat_id: str
    chat_type: str
    message_id: str
    message_type: str
    text: str
    is_mentioned: bool


def parse_text_content(raw_content: str, message_type: str) -> str:
    if message_type != "text":
        return ""
    try:
        parsed = json.loads(raw_content)
    except json.JSONDecodeError:
        return raw_content.strip()
    return str(parsed.get("text", "")).strip()


class ReplyEngine:
    def __init__(self, config: AppConfig) -> None:
        self._config = config

    def should_reply(self, ctx: MessageContext) -> bool:
        if self._config.allowed_chat_ids and ctx.chat_id not in self._config.allowed_chat_ids:
            return False
        if ctx.chat_type != "p2p" and self._config.group_reply_requires_mention and not ctx.is_mentioned:
            return False
        return True

    def build_reply(self, ctx: MessageContext) -> str | None:
        if not self.should_reply(ctx):
            return None

        command_reply = self.build_command_reply(ctx)
        if command_reply is not None:
            return command_reply

        normalized = ctx.text.strip()
        return f"{self._config.default_reply}\n\n你刚刚说的是：{normalized}"

    def build_command_reply(self, ctx: MessageContext) -> str | None:
        if ctx.message_type != "text":
            return "我现在只会处理文本消息。你可以发送 help 查看可用命令。"

        normalized = ctx.text.strip()
        lowered = normalized.lower()

        if not normalized:
            return "我收到了空消息。你可以发送 help 查看可用命令。"
        if lowered == "help":
            return (
                "可用命令:\n"
                "- help\n"
                "- ping\n"
                "- status\n"
                "- id\n"
                "- echo 你的内容"
            )
        if lowered == "ping":
            return "pong"
        if lowered == "status":
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return f"服务在线中。当前时间: {now}"
        if lowered == "id":
            return (
                f"chat_id={ctx.chat_id}\n"
                f"sender_open_id={ctx.sender_open_id}\n"
                f"message_id={ctx.message_id}"
            )
        if lowered.startswith("echo "):
            return normalized[5:].strip() or "你没有提供要回显的内容。"

        return None
