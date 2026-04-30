from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_csv(name: str) -> tuple[str, ...]:
    raw = os.getenv(name, "")
    if not raw.strip():
        return ()
    return tuple(part.strip() for part in raw.split(",") if part.strip())


@dataclass(frozen=True)
class AppConfig:
    app_id: str
    app_secret: str
    log_level: str
    default_reply: str
    group_reply_requires_mention: bool
    allowed_chat_ids: tuple[str, ...]
    runtime_dir: Path
    coze_api_base_url: str
    coze_access_token: str
    coze_bot_id: str
    coze_timeout_seconds: int


def load_config() -> AppConfig:
    _load_dotenv(ENV_FILE)

    app_id = os.getenv("FEISHU_APP_ID", "").strip()
    app_secret = os.getenv("FEISHU_APP_SECRET", "").strip()
    if not app_id or not app_secret:
        raise ValueError(
            "Missing FEISHU_APP_ID or FEISHU_APP_SECRET. "
            "Copy .env.example to .env and fill in your credentials."
        )

    runtime_dir = PROJECT_ROOT / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)

    return AppConfig(
        app_id=app_id,
        app_secret=app_secret,
        log_level=os.getenv("FEISHU_LOG_LEVEL", "INFO").strip().upper(),
        default_reply=os.getenv(
            "FEISHU_DEFAULT_REPLY",
            "已收到你的消息。发送 help 查看可用命令。",
        ).strip(),
        group_reply_requires_mention=_env_bool(
            "FEISHU_GROUP_REPLY_REQUIRES_MENTION",
            True,
        ),
        allowed_chat_ids=_env_csv("FEISHU_ALLOWED_CHAT_IDS"),
        runtime_dir=runtime_dir,
        coze_api_base_url=os.getenv(
            "COZE_API_BASE_URL",
            "https://api.coze.cn",
        ).strip().rstrip("/"),
        coze_access_token=os.getenv("COZE_ACCESS_TOKEN", "").strip(),
        coze_bot_id=os.getenv("COZE_BOT_ID", "").strip(),
        coze_timeout_seconds=int(
            os.getenv("COZE_TIMEOUT_SECONDS", "120").strip() or "120"
        ),
    )
