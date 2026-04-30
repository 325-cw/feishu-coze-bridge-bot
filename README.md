# Feishu WebSocket Bot Service

This project runs a long-lived Feishu bot service over the official WebSocket event channel. It listens for message events, logs them locally, and sends automatic replies back to the chat.

## What It Does

- Connects to Feishu with your `App ID` and `App Secret`
- Subscribes to message events over WebSocket
- Ignores its own outbound messages to avoid reply loops
- Replies automatically in 1:1 chats
- Replies in group chats only when the bot is mentioned
- For normal text messages, forwards the message to the configured Coze bot when `COZE_ACCESS_TOKEN` and `COZE_BOT_ID` are set
- Stores runtime logs and raw event snapshots under `runtime/`

## Project Files

- `bot_service/config.py`: reads environment variables and `.env`
- `bot_service/coze_api.py`: Coze `v3/chat` streaming API helper and conversation storage
- `bot_service/feishu_api.py`: small Feishu HTTP helper for token and message sending
- `bot_service/logic.py`: command parsing and auto-reply logic
- `bot_service/service.py`: WebSocket bot entrypoint

## Reusable Ops Skill

This workspace now includes a reusable local skill bundle for future Feishu + Coze bridge work:

- `skills/feishu-coze-bridge-ops/SKILL.md`
- `skills/feishu-coze-bridge-ops/references/current-setup.md`
- `skills/feishu-coze-bridge-ops/references/publish-and-verify.md`

## Setup

1. Copy `.env.example` to `.env`
2. Fill in your real `FEISHU_APP_ID` and `FEISHU_APP_SECRET`
3. Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

4. Start the bot:

```powershell
python -m bot_service.service
```

## Built-In Commands

Send these to the bot in Feishu:

- `help`: list supported commands
- `ping`: health check
- `status`: show service status
- `id`: show chat and sender identifiers
- `echo anything`: echo back the message tail

Any other plain-text message gets an acknowledgement reply by default.

## Coze Integration

Set these values in `.env` to route normal messages through a Coze bot:

```powershell
COZE_API_BASE_URL=https://api.coze.cn
COZE_BOT_ID=bot_your_coze_bot_id
COZE_ACCESS_TOKEN=your_coze_access_token
COZE_TIMEOUT_SECONDS=120
```

The service stores Coze conversation IDs in `runtime/coze_conversations.json` so each Feishu chat participant can keep a separate Coze conversation.

## Open Source Notes

- `.env`, `runtime/`, `.venv/`, and `wheelhouse/` are local-only and should not be published.
- Keep `.env.example` as placeholders only.
- Replace `COZE_BOT_ID` and `COZE_ACCESS_TOKEN` with your own values before running the project.

## Always-On Options

This repo creates the bot service itself, but does not automatically register it as a Windows service or scheduled task.

Common next steps:

- run it inside a persistent terminal session
- use Task Scheduler to start it on login
- wrap it with a Windows service manager later if you want machine-level startup

## Windows Helpers

This repo also includes helper launchers:

- `start_bot.cmd`
- `stop_bot.cmd`
- `status_bot.cmd`

They call the matching PowerShell scripts with execution policy bypass, which is useful on machines that block direct `.ps1` execution.

## Notes

- The service assumes your Feishu app is already configured for WebSocket event delivery.
- The bot only auto-replies to text messages in this starter version.
- Runtime logs are written locally under `runtime/` for easier debugging.
