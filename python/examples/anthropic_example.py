"""Anthropic example showing Kaizen encode/decode around Claude messages."""

from __future__ import annotations

import asyncio
import os
from pprint import pprint

from kaizen_client import KaizenClient, KaizenClientConfig
from kaizen_client.integrations.anthropic import AnthropicKaizenWrapper


async def main() -> None:
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise RuntimeError("ANTHROPIC_API_KEY must be set to run the Anthropic example.")
    client = KaizenClient(KaizenClientConfig(base_url=os.getenv("KAIZEN_BASE_URL", "https://api.getkaizen.io/")))
    model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20240620")
    wrapper = AnthropicKaizenWrapper(client, model=model)
    messages = [
        {"role": "user", "content": "Draft a Kaizen release note in three bullet points."},
    ]
    result = await wrapper.chat(messages)
    print("--- Kaizen encoded stats ---")
    pprint(result["encoded"].get("stats"))
    print("--- Claude response decoded ---")
    pprint(result["decoded"]["result"])
    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
