"""OpenAI helper that runs Kaizen encode/decode around Chat Completions."""

from __future__ import annotations

from typing import Any, Dict

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover
    OpenAI = None  # type: ignore

from ..client import KaizenClient


class OpenAIKaizenWrapper:
    def __init__(self, kaizen: KaizenClient, *, model: str = "gpt-4o-mini") -> None:
        if OpenAI is None:
            raise RuntimeError("openai package missing. Install kaizen-client[openai].")
        self._kaizen = kaizen
        self._model = model
        self._client = OpenAI()

    async def chat(self, messages: list[Dict[str, str]], **options: Any) -> Dict[str, Any]:
        encoded = await self._kaizen.prompts_encode({"prompt": {"messages": messages}})
        ktof_prompt = encoded["result"]
        completion = self._client.responses.create(model=self._model, input=ktof_prompt, **options)
        decoded = await self._kaizen.prompts_decode({"ktof": completion.output_text})
        return {
            "encoded": encoded,
            "openai_response": completion,
            "decoded": decoded,
        }
