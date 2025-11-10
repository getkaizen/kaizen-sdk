"""End-to-end Kaizen example that encodes, optimizes, and decodes a prompt."""

from __future__ import annotations

import asyncio
import os
from pprint import pprint

from kaizen_client import KaizenClient, KaizenClientConfig


def _build_client() -> KaizenClient:
    api_key = os.getenv("KAIZEN_API_KEY")
    if not api_key:
        raise RuntimeError("KAIZEN_API_KEY must be set to run the lifecycle example.")
    config = KaizenClientConfig(
        api_key=api_key,
        base_url=os.getenv("KAIZEN_BASE_URL", "https://api.getkaizen.io/"),
    )
    return KaizenClient(config)


async def main() -> None:
    client = _build_client()
    prompt = {
        "messages": [
            {"role": "system", "content": "You are Kaizen's technical writer."},
            {"role": "user", "content": "Summarize the savings this prompt would get."},
        ],
        "metadata": {"source": "full-lifecycle"},
    }

    encode_payload = {
        "prompt": prompt,
        "token_models": ["gpt-4o-mini"],
        "metadata": {"example": "full-lifecycle"},
    }
    print("\n=== prompts.encode => ktof result + stats ===")
    encoded = await client.prompts_encode(encode_payload)
    pprint({"result": encoded["result"], "stats": encoded.get("stats"), "token_stats": encoded.get("token_stats")})

    print("\n=== prompts.decode => hydrate ktof back into JSON ===")
    decoded = await client.prompts_decode({"ktof": encoded["result"]})
    pprint(decoded["result"])

    print("\n=== optimize.request => compress before provider call ===")
    optimized_request = await client.optimize_request({"prompt": prompt, "token_models": ["gpt-4o-mini"]})
    pprint(optimized_request.get("stats"))

    print("\n=== optimize.response => decompress provider reply ===")
    optimized_response = await client.optimize_response({"ktof": encoded["result"]})
    pprint(optimized_response.get("result"))

    print("\n=== compress/decompress => generic data helpers ===")
    generic = await client.compress({"data": prompt})
    pprint(generic.get("stats"))
    restored = await client.decompress({"data": generic["result"]})
    pprint(restored.get("data"))

    print("\n=== health check ===")
    pprint(await client.health())

    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
