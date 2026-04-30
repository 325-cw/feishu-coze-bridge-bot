# Publish And Verify

## When Coze says the bot is not published

Typical error:

- `The bot_id ... has not been published to the channel Agent As API`

Resolution:

1. Open the target Coze bot editor.
2. Click `Publish`.
3. If prompted for greeting content, use `Skip and publish directly`.
4. On the publish page, select the `API` channel.
5. Submit publish.
6. Wait briefly for propagation.
7. Re-test `POST https://api.coze.cn/v3/chat`.

## Minimum working Coze request shape

```json
{
  "bot_id": "<your_coze_bot_id>",
  "user_id": "some-stable-user-id",
  "stream": true,
  "auto_save_history": true,
  "additional_messages": [
    {
      "role": "user",
      "content": "Reply with only \"connected\".",
      "content_type": "text"
    }
  ]
}
```

## Success signal

Successful SSE output contains events like:

- `conversation.chat.created`
- `conversation.chat.in_progress`
- `conversation.message.delta`
- `conversation.message.completed`

The usable final assistant text should be taken from the payload of `conversation.message.completed` when:

- `type == "answer"`
- `content_type == "text"`

## End-to-end verification order

1. Confirm the Feishu websocket service is connected in `runtime/stdout.log`.
2. Confirm `.env` contains non-empty `COZE_BOT_ID` and `COZE_ACCESS_TOKEN`.
3. Confirm the Coze bot is published to `API`.
4. Verify `v3/chat` returns SSE instead of a JSON error.
5. Send a normal text message in Feishu and confirm the reply is no longer the local fallback text.
