"""Gemini helper that compresses prompts before invoking Gemini 2.5 Flash."""

from __future__ import annotations

from typing import Any, Dict

try:
    import google.generativeai as genai
except ImportError:  # pragma: no cover
    genai = None  # type: ignore

from ..client import KaizenClient


class GeminiKaizenWrapper:
    """Simple wrapper that calls Kaizen before sending data to Gemini."""

    def __init__(self, kaizen: KaizenClient, *, model: str = "models/gemini-2.5-flash") -> None:
        if genai is None:  # pragma: no cover - missing optional dep
            raise RuntimeError("google-generativeai is not installed. Install kaizen-client[gemini].")
        self._kaizen = kaizen
        self._model = model

    async def invoke(self, prompt: Dict[str, Any]) -> Dict[str, Any]:
        encoded = await self._kaizen.prompts_encode({"prompt": prompt})
        ktof_prompt = encoded["result"]
        model = genai.GenerativeModel(self._model)
        response = model.generate_content(ktof_prompt)
        decoded = await self._kaizen.prompts_decode({"ktof": response.text})
        return {
            "encoded": encoded,
            "gemini_response": response,
            "decoded": decoded,
        }
