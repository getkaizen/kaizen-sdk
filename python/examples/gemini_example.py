"""Async demo showing how to wrap Gemini with Kaizen."""

import asyncio
import os

from kaizen_client import KaizenClient, KaizenClientConfig
from kaizen_client.integrations.gemini import GeminiKaizenWrapper


async def main() -> None:
    client = KaizenClient(KaizenClientConfig(base_url=os.getenv("KAIZEN_BASE_URL", "https://api.getkaizen.io/")))
    wrapper = GeminiKaizenWrapper(client)
    prompt = {"messages": [{"role": "user", "content": "Summarize the attached report."}]}
    result = await wrapper.invoke(prompt)
    print("Decoded:", result["decoded"]["result"])
    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
