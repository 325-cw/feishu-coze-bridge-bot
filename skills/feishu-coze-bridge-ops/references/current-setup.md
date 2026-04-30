# Current Setup

## Project root

- `<workspace-root>`

## Feishu side

- App type: internal Feishu app with websocket callback mode
- Feishu app credentials are stored in `.env`
- Running service entry: `python -m bot_service.service`
- Runtime logs:
  - `runtime/service.log`
  - `runtime/stdout.log`
  - `runtime/stderr.log`
  - `runtime/events.jsonl`
- Conversation persistence:
  - `runtime/coze_conversations.json`

## Coze side

- Bot name: use your own published Coze bot
- Bot id: store in `.env` as `COZE_BOT_ID`
- Coze API base: `https://api.coze.cn`
- Required API route: `POST /v3/chat`
- Required auth header:
  - `Authorization: Bearer <COZE_ACCESS_TOKEN>`
- Store the actual PAT only in `.env`

## Local service behavior

- Local command replies still handled in `bot_service/logic.py`:
  - `help`
  - `ping`
  - `status`
  - `id`
  - `echo ...`
- All other normal text messages route to Coze through `bot_service/coze_api.py`
- Coze replies are parsed from SSE and finalized from `conversation.message.completed`

## Known machine-specific quirks

1. Browser control
   - Reusing an arbitrary already-open Chrome window is unreliable.
   - A controlled Chrome profile under `runtime/coze-chrome-profile` worked for Coze console operations.

2. Chrome remote debugging
   - Current Chrome did not expose a usable debug endpoint from the default user profile.
   - Launching a separate controlled profile was the reliable path.

3. Bot launch path
   - Existing stable runtime path used a detached background launch.
   - Direct PowerShell process control hit permission issues against an older Python process.
   - `start_bot.ps1` also needed a fix for `Path`/`PATH` duplication during `Start-Process`.

4. Network verification
   - Shell-launched Python direct network tests hit socket permission issues on this machine.
   - Node runtime `fetch` was the reliable way to verify Coze API reachability.

5. Coze API publishing
   - A valid PAT was not sufficient by itself.
   - The bot had to be published to the `API` channel first.
   - After publish, Coze still took a short time to propagate before `v3/chat` succeeded.
