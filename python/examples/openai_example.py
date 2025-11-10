"""OpenAI example that compresses prompts before sending to GPT models."""

import asyncio
import os

from kaizen_client import KaizenClient, KaizenClientConfig
from kaizen_client.integrations.openai import OpenAIKaizenWrapper


def _build_client() -> KaizenClient:
    config = KaizenClientConfig(
        base_url=os.getenv('KAIZEN_BASE_URL', 'https://api.getkaizen.io/'),
        api_key=os.getenv('KAIZEN_API_KEY'),
    )
    return KaizenClient(config)


async def main() -> None:
    client = _build_client()
    wrapper = OpenAIKaizenWrapper(client, model='gpt-4o-mini')
    messages = [
        {'role': 'system', 'content': 'You are concise.'},
        {'role': 'user', 'content': 'List 3 Kaizen benefits.'},
    ]
    result = await wrapper.chat(messages)
    print(result['decoded']['result'])
    await client.close()


if __name__ == '__main__':
    asyncio.run(main())
