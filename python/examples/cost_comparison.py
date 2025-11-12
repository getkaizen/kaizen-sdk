"""Rudimentary token/cost comparison script."""

from __future__ import annotations

import asyncio
from pprint import pprint

import tiktoken

from kaizen_client import KaizenClient


async def main() -> None:
    client = KaizenClient()
    prompt = {
        "messages": [{"role": "user", "content": "Summarize quarterly metrics in a table."}],
        "metadata": {"source": "cost-demo"},
    }
    token_model = "gpt-4o"
    encoded = await client.prompts_encode({"prompt": prompt, "token_models": [token_model]})
    print("--- Raw vs optimized bytes ---")
    pprint(encoded["stats"])
    print(f"--- Token stats reported by Kaizen for {token_model} ---")
    pprint(encoded.get("token_stats", {}).get(token_model))

    # Local verification using tiktoken for transparency
    encoder = tiktoken.encoding_for_model(token_model)
    raw_tokens = len(encoder.encode(str(prompt)))
    optimized_tokens = len(encoder.encode(encoded["result"]))
    print(f"Local token check -> raw: {raw_tokens}, optimized: {optimized_tokens}")
    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
