"""Anthropic helper for Claude models."""

from __future__ import annotations

from typing import Any, Dict

try:
    import anthropic
except ImportError:  # pragma: no cover
    anthropic = None  # type: ignore

from ..client import KaizenClient


class AnthropicKaizenWrapper:
    def __init__(self, kaizen: KaizenClient, *, model: str = "claude-3-5-sonnet-20240620") -> None:
        if anthropic is None:
            raise RuntimeError("anthropic package missing. Install kaizen-client[anthropic].")
        self._kaizen = kaizen
        self._client = anthropic.Anthropic()
        self._model = model

    async def chat(self, messages: list[Dict[str, str]], **options: Any) -> Dict[str, Any]:
        encoded = await self._kaizen.prompts_encode({"prompt": {"messages": messages}})
        ktof_prompt = encoded["result"]
        completion = self._client.messages.create(model=self._model, messages=[{"role": "user", "content": ktof_prompt}], **options)
        decoded = await self._kaizen.prompts_decode({"ktof": completion.content[0].text})
        return {
            "encoded": encoded,
            "anthropic_response": completion,
            "decoded": decoded,
        }
