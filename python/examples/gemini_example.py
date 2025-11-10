"""Async demo showing how to wrap Gemini with Kaizen."""

from __future__ import annotations

import asyncio
import os
from pprint import pprint

from kaizen_client import KaizenClient, KaizenClientConfig
from kaizen_client.integrations.gemini import GeminiKaizenWrapper


async def main() -> None:
    if not os.getenv("GOOGLE_API_KEY"):
        raise RuntimeError("GOOGLE_API_KEY must be set to run the Gemini example.")
    client = KaizenClient(KaizenClientConfig(base_url=os.getenv("KAIZEN_BASE_URL", "https://api.getkaizen.io/")))
    model = os.getenv("GOOGLE_MODEL", "models/gemini-2.5-flash")
    wrapper = GeminiKaizenWrapper(client, model=model)
    prompt = {"messages": [{"role": "user", "content": "Summarize the attached report."}]}
    result = await wrapper.invoke(prompt)
    print("--- Kaizen encoded stats ---")
    pprint(result["encoded"].get("stats"))
    print("--- Gemini response decoded ---")
    pprint(result["decoded"]["result"])
    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
