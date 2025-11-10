"""Rudimentary token/cost comparison script."""

import asyncio
import tiktoken

from kaizen_client import KaizenClient


async def main() -> None:
    client = KaizenClient()
    prompt = {
        "messages": [{"role": "user", "content": "Summarize quarterly metrics in a table."}],
        "metadata": {"source": "cost-demo"},
    }
    encoded = await client.prompts_encode({"prompt": prompt, "token_models": ["gpt-4o"]})
    print("Stats:", encoded["stats"])
    print("Token stats:", encoded.get("token_stats"))
    encoder = tiktoken.encoding_for_model("gpt-4o")
    raw_tokens = len(encoder.encode(str(prompt)))
    optimized_tokens = len(encoder.encode(encoded["result"]))
    print(f"Raw tokens: {raw_tokens}, Optimized tokens: {optimized_tokens}")
    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
