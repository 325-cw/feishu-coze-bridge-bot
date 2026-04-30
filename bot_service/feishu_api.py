from __future__ import annotations

from dataclasses import dataclass
import json
import time
from typing import Any
from urllib import error, parse, request


BASE_URL = "https://open.feishu.cn"


class FeishuAPIError(RuntimeError):
    pass


@dataclass
class TokenCache:
    token: str = ""
    expires_at: float = 0.0


class FeishuAPI:
    def __init__(self, app_id: str, app_secret: str) -> None:
        self._app_id = app_id
        self._app_secret = app_secret
        self._token_cache = TokenCache()

    def send_text_to_chat(self, chat_id: str, text: str) -> dict[str, Any]:
        payload = {
            "receive_id": chat_id,
            "msg_type": "text",
            "content": json.dumps({"text": text}, ensure_ascii=False),
        }
        return self._request_json(
            method="POST",
            path="/open-apis/im/v1/messages",
            query={"receive_id_type": "chat_id"},
            body=payload,
            auth=True,
        )

    def _tenant_access_token(self) -> str:
        now = time.time()
        if self._token_cache.token and now < self._token_cache.expires_at:
            return self._token_cache.token

        response = self._request_json(
            method="POST",
            path="/open-apis/auth/v3/tenant_access_token/internal",
            body={
                "app_id": self._app_id,
                "app_secret": self._app_secret,
            },
            auth=False,
        )
        token = response["tenant_access_token"]
        expire_seconds = int(response.get("expire", 7200))
        self._token_cache = TokenCache(
            token=token,
            expires_at=now + max(expire_seconds - 60, 60),
        )
        return token

    def _request_json(
        self,
        *,
        method: str,
        path: str,
        body: dict[str, Any] | None = None,
        query: dict[str, str] | None = None,
        auth: bool,
    ) -> dict[str, Any]:
        url = BASE_URL + path
        if query:
            url += "?" + parse.urlencode(query)

        headers = {
            "Content-Type": "application/json; charset=utf-8",
        }
        if auth:
            headers["Authorization"] = f"Bearer {self._tenant_access_token()}"

        data = None
        if body is not None:
            data = json.dumps(body, ensure_ascii=False).encode("utf-8")

        req = request.Request(url=url, method=method, headers=headers, data=data)
        try:
            with request.urlopen(req, timeout=30) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise FeishuAPIError(
                f"HTTP {exc.code} calling {path}: {detail}"
            ) from exc
        except error.URLError as exc:
            raise FeishuAPIError(f"Network error calling {path}: {exc}") from exc

        code = payload.get("code", 0)
        if code != 0:
            raise FeishuAPIError(
                f"Feishu API returned code={code} msg={payload.get('msg', '')}"
            )
        return payload.get("data", payload)

