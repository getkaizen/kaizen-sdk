from __future__ import annotations

import httpx
import pytest

from kaizen_client import (
    KaizenAPIError,
    KaizenClient,
    KaizenClientConfig,
    KaizenRequestError,
    PromptDecodePayload,
    PromptEncodePayload,
    with_kaizen_client,
)


class DummyResponse:
    def __init__(self, payload: dict[str, object], status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code
        self.headers = {"x-test": "1"}
        self.is_error = status_code >= 400

    def json(self) -> dict[str, object]:
        return self._payload

    @property
    def text(self) -> str:  # pragma: no cover - debugging helper
        return str(self._payload)


class DummyAsyncClient:
    def __init__(self) -> None:
        self.last_request: dict[str, object] | None = None
        self.response: DummyResponse | Exception = DummyResponse({"ok": True})

    async def request(
        self, method: str, url: str, json: dict[str, object] | None = None, headers: dict[str, str] | None = None
    ) -> DummyResponse:
        self.last_request = {"method": method, "url": url, "json": json, "headers": headers}
        if isinstance(self.response, Exception):
            raise self.response
        return self.response

    async def aclose(self) -> None:
        return None


@pytest.mark.asyncio
async def test_prompts_encode_serializes_models() -> None:
    dummy = DummyAsyncClient()
    client = KaizenClient(KaizenClientConfig(api_key="secret"), client=dummy)  # type: ignore[arg-type]
    payload = PromptEncodePayload(prompt={"messages": []})

    result = await client.prompts_encode(payload)

    assert result == {"ok": True}
    assert dummy.last_request is not None
    assert dummy.last_request["url"] == "https://api.getkaizen.io/v1/prompts/encode"
    assert dummy.last_request["json"] == {"prompt": {"messages": []}, "auto_detect_json": True}
    assert dummy.last_request["headers"]["Authorization"] == "Bearer secret"
    await client.close()


@pytest.mark.asyncio
async def test_prompts_decode_validates_input() -> None:
    dummy = DummyAsyncClient()
    client = KaizenClient(client=dummy)  # type: ignore[arg-type]
    payload = PromptDecodePayload(ktof="abc123")

    await client.prompts_decode(payload)
    assert dummy.last_request is not None
    assert dummy.last_request["json"] == {"ktof": "abc123"}


@pytest.mark.asyncio
async def test_http_error_raises_api_exception() -> None:
    dummy = DummyAsyncClient()
    dummy.response = DummyResponse({"detail": "bad"}, status_code=500)
    client = KaizenClient(client=dummy)  # type: ignore[arg-type]

    with pytest.raises(KaizenAPIError):
        await client.prompts_encode({"prompt": {"messages": []}})


@pytest.mark.asyncio
async def test_transport_error_raises_request_exception() -> None:
    dummy = DummyAsyncClient()
    dummy.response = httpx.ConnectError("boom", request=httpx.Request("POST", "http://test"))
    client = KaizenClient(client=dummy)  # type: ignore[arg-type]

    with pytest.raises(KaizenRequestError):
        await client.prompts_encode({"prompt": {"messages": []}})


@pytest.mark.asyncio
async def test_with_kaizen_client_decorator_manages_lifecycle(monkeypatch: pytest.MonkeyPatch) -> None:
    events: list[str] = []

    class DummyManagedClient:
        def __init__(self, *args, **kwargs) -> None:
            events.append("created")

        async def prompts_encode(self, payload):
            events.append("used")
            return payload

        async def close(self) -> None:
            events.append("closed")

    monkeypatch.setattr("kaizen_client.decorators.KaizenClient", DummyManagedClient)

    @with_kaizen_client()
    async def run(*, kaizen):
        return await kaizen.prompts_encode({"prompt": {"messages": []}})

    result = await run()

    assert result == {"prompt": {"messages": []}}
    assert events == ["created", "used", "closed"]
