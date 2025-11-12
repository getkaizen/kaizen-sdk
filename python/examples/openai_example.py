"""OpenAI example that compresses prompts before sending to GPT models."""

from __future__ import annotations

import asyncio
import os
from pprint import pprint

from kaizen_client import KaizenClient, KaizenClientConfig
from kaizen_client.integrations.openai import OpenAIKaizenWrapper


def _build_client() -> KaizenClient:
    config = KaizenClientConfig(
        base_url=os.getenv("KAIZEN_BASE_URL", "https://api.getkaizen.io/"),
        api_key=os.getenv("KAIZEN_API_KEY"),
    )
    return KaizenClient(config)


async def main() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY must be set to run the OpenAI example.")
    client = _build_client()
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    wrapper = OpenAIKaizenWrapper(client, model=model)
    messages = [
        {"role": "system", "content": "You are concise."},
        {"role": "user", "content": "List 3 Kaizen benefits."},
    ]
    result = await wrapper.chat(messages, temperature=0)
    print("--- Kaizen stats before hitting OpenAI ---")
    pprint(result["encoded"].get("stats"))
    print("--- Decoded provider response ---")
    pprint(result["decoded"]["result"])
    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
