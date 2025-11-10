"""Async demo showing how to wrap Gemini with Kaizen."""

import asyncio

from kaizen_client import KaizenClient, KaizenClientConfig
from kaizen_client.integrations.gemini import GeminiKaizenWrapper


async def main() -> None:
    client = KaizenClient(KaizenClientConfig(base_url="http://127.0.0.1:8000/v1"))
    wrapper = GeminiKaizenWrapper(client)
    prompt = {"messages": [{"role": "user", "content": "Summarize the attached report."}]}
    result = await wrapper.invoke(prompt)
    print("Decoded:", result["decoded"]["result"])
    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
