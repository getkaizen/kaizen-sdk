"""OpenAI example that compresses prompts before sending to GPT models."""

import asyncio

from kaizen_client import KaizenClient
from kaizen_client.integrations.openai import OpenAIKaizenWrapper


async def main() -> None:
    client = KaizenClient()
    wrapper = OpenAIKaizenWrapper(client, model="gpt-4o-mini")
    messages = [
        {"role": "system", "content": "You are concise."},
        {"role": "user", "content": "List 3 Kaizen benefits."},
    ]
    result = await wrapper.chat(messages)
    print(result["decoded"]["result"])
    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
