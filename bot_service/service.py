from __future__ import annotations

from datetime import datetime
import json
import logging
from pathlib import Path
from typing import Any

import lark_oapi as lark

from bot_service.config import AppConfig, load_config
from bot_service.coze_api import CozeAPI, CozeAPIError, ConversationStore
from bot_service.feishu_api import FeishuAPI, FeishuAPIError
from bot_service.logic import MessageContext, ReplyEngine, parse_text_content


def _sdk_log_level(level_name: str) -> lark.LogLevel:
    return getattr(lark.LogLevel, level_name.upper(), lark.LogLevel.INFO)


class FeishuBotService:
    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._api = FeishuAPI(config.app_id, config.app_secret)
        self._coze = CozeAPI(config)
        self._engine = ReplyEngine(config)
        self._logger = self._build_logger(config.runtime_dir)
        self._event_log_path = config.runtime_dir / "events.jsonl"
        self._conversation_store = ConversationStore(
            config.runtime_dir / "coze_conversations.json"
        )

        self._dispatcher = (
            lark.EventDispatcherHandler.builder("", "")
            .register_p2_im_message_receive_v1(self._handle_message_event)
            .build()
        )

    def start(self) -> None:
        self._logger.info("Starting Feishu WebSocket bot service")
        client = lark.ws.Client(
            self._config.app_id,
            self._config.app_secret,
            event_handler=self._dispatcher,
            log_level=_sdk_log_level(self._config.log_level),
        )
        client.start()

    def _handle_message_event(self, data: lark.im.v1.P2ImMessageReceiveV1) -> None:
        payload = json.loads(lark.JSON.marshal(data))
        self._write_event(payload)

        event = payload.get("event", {})
        message = event.get("message", {})
        sender = event.get("sender", {})
        sender_id = sender.get("sender_id", {})

        sender_app_id = sender_id.get("app_id", "")
        sender_open_id = sender_id.get("open_id", "")
        chat_id = str(message.get("chat_id", ""))
        chat_type = str(message.get("chat_type", ""))
        message_id = str(message.get("message_id", ""))
        message_type = str(message.get("message_type", ""))
        raw_content = str(message.get("content", ""))
        mentions = message.get("mentions") or []

        if sender_app_id == self._config.app_id:
            self._logger.info("Ignoring self-sent app message %s", message_id)
            return

        ctx = MessageContext(
            sender_open_id=sender_open_id,
            chat_id=chat_id,
            chat_type=chat_type,
            message_id=message_id,
            message_type=message_type,
            text=parse_text_content(raw_content, message_type),
            is_mentioned=bool(mentions),
        )

        self._logger.info(
            "Received message %s from chat=%s chat_type=%s text=%r",
            ctx.message_id,
            ctx.chat_id,
            ctx.chat_type,
            ctx.text,
        )

        reply = self._build_reply(ctx)
        if not reply:
            self._logger.info("No reply generated for message %s", ctx.message_id)
            return

        try:
            self._api.send_text_to_chat(ctx.chat_id, reply)
            self._logger.info("Reply sent for message %s", ctx.message_id)
        except FeishuAPIError as exc:
            self._logger.exception("Reply failed for message %s: %s", ctx.message_id, exc)

    def _build_reply(self, ctx: MessageContext) -> str | None:
        if not self._engine.should_reply(ctx):
            return None

        command_reply = self._engine.build_command_reply(ctx)
        if command_reply is not None:
            return command_reply

        if not self._coze.enabled:
            return self._engine.build_reply(ctx)

        conversation_key = f"{ctx.chat_id}:{ctx.sender_open_id or 'unknown'}"
        conversation_id = self._conversation_store.get(conversation_key)
        try:
            result = self._coze.send_message(ctx, conversation_id=conversation_id)
        except CozeAPIError as exc:
            self._logger.exception("Coze reply failed for message %s: %s", ctx.message_id, exc)
            return "扣子智能体调用失败，已记录到本地日志。"

        self._conversation_store.set(conversation_key, result.conversation_id)
        return result.text

    def _build_logger(self, runtime_dir: Path) -> logging.Logger:
        logger = logging.getLogger("feishu_bot_service")
        if logger.handlers:
            return logger

        logger.setLevel(getattr(logging, self._config.log_level, logging.INFO))

        formatter = logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s - %(message)s"
        )

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

        file_handler = logging.FileHandler(runtime_dir / "service.log", encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        return logger

    def _write_event(self, payload: dict[str, Any]) -> None:
        record = {
            "received_at": datetime.now().isoformat(timespec="seconds"),
            "payload": payload,
        }
        with self._event_log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def main() -> None:
    config = load_config()
    service = FeishuBotService(config)
    service.start()


if __name__ == "__main__":
    main()
