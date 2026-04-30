---
name: feishu-coze-bridge-ops
description: Use when working on this machine's Feishu app, long-running Feishu websocket bot, Coze bot publishing, or the Feishu -> local bot -> Coze bridge. Covers token setup, Coze API publishing, service restart, and end-to-end verification.
---

# Feishu Coze Bridge Ops

Use this skill when the task is to inspect, repair, extend, or verify the local Feishu-to-Coze bridge in this workspace.

## What this skill assumes

- Workspace root is the bridge project root.
- The local Feishu bot runs from `bot_service/`.
- Coze is used through `https://api.coze.cn/v3/chat`.
- Current environment-specific details live in `references/current-setup.md`.

## Core workflow

1. Read `references/current-setup.md` before making assumptions about IDs, paths, or runtime behavior.
2. Inspect local config and service state:
   - `.env`
   - `bot_service/config.py`
   - `bot_service/service.py`
   - `runtime/service.log`
   - `runtime/stdout.log`
   - `runtime/bot.pid`
3. If the task involves Coze API failures, check whether the target bot is published to the `API` channel before changing code.
4. If the task involves browser-side Coze operations, use a controlled Chrome profile instead of assuming access to an already-open personal browser window.
5. For normal message routing issues, verify this order:
   - Feishu websocket connected
   - `.env` contains `COZE_BOT_ID` and `COZE_ACCESS_TOKEN`
   - target Coze bot is published to `API`
   - `v3/chat` returns SSE events including `conversation.message.completed`
6. After changes, verify with the smallest possible end-to-end test.

## Local constraints

- Do not assume you can attach to an arbitrary existing Chrome window.
- Do not expose or print secret values from `.env`.
- On this machine, PowerShell-launched Python network access may behave differently from the existing long-running runtime path. Check `references/current-setup.md` before replacing the launch method.

## References

- For concrete IDs, paths, current launch method, and known quirks: `references/current-setup.md`
- For the repeatable publish-and-verify sequence: `references/publish-and-verify.md`
