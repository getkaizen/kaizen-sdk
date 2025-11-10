# Kaizen Python SDK

Typed async client, provider adapters, and helpers for working with the Kaizen Token Optimized Format (KTOF) service. This package lives inside the `kaizen-sdks` monorepo under `python/` and mirrors the public Kaizen REST API exactly.

## Before you start

1. **Request access** – Email `hello@getkaizen.ai` for a production API key.
2. **Environment variables** – Export the following (or pass via `KaizenClientConfig`):
   - `KAIZEN_BASE_URL` – defaults to `https://api.getkaizen.io/`; point it at staging/local (e.g., `http://127.0.0.1:8000`) only when needed.
   - `KAIZEN_API_KEY` – bearer token used by the SDK.
   - `KAIZEN_TIMEOUT` – float seconds, default `30`.

> Tip: keep API keys in a `.env` file (gitignored) or your secret manager rather than hardcoding them.
3. **Python version** – 3.10 or newer.

## Installation

```bash
cd python
uv pip install -e .[all]   # or: pip install -e .[all]
```

Optional extras enable provider adapters:

| Extra | Purpose |
|-------|---------|
| `gemini` | Installs `google-generativeai` so `kaizen_client.integrations.gemini` can wrap Gemini 2.5 Flash. |
| `openai` | Installs `openai` for GPT-4/o integrations. |
| `anthropic` | Installs `anthropic` for Claude adapters. |
| `all` | Pulls every optional dependency plus `tiktoken` for token stats. |

## Hello, Kaizen!

```python
import asyncio
import os

from kaizen_client import KaizenClient, KaizenClientConfig

async def main() -> None:
    config = KaizenClientConfig(
        api_key=os.environ["KAIZEN_API_KEY"],
        base_url=os.getenv("KAIZEN_BASE_URL", "https://api.getkaizen.io/"),
        timeout=float(os.getenv("KAIZEN_TIMEOUT", "30")),
    )
    async with KaizenClient(config) as client:
        encoded = await client.prompts_encode({
            "prompt": {
                "messages": [
                    {"role": "system", "content": "You are concise."},
                    {"role": "user", "content": "List 3 Kaizen benefits."},
                ]
            }
        })
        decoded = await client.prompts_decode({"ktof": encoded["result"]})
        print(decoded["result"])

asyncio.run(main())
```

## Environment targets

- **Production (default):** `https://api.getkaizen.io/`.
- **Staging/Internal:** set `KAIZEN_BASE_URL` to your internal host (e.g., `https://internal.getkaizen.ai`).
- **Local dev:** `KAIZEN_BASE_URL=http://127.0.0.1:8000` pairs nicely with a locally running Kaizen service.

Rotate API keys regularly and keep them in `.env` or your secret manager—never commit them to source control.

## High-level API surface

| Method | Endpoint | Description | Payload model |
|--------|----------|-------------|---------------|
| `compress()` | `POST /v1/compress` | Convert arbitrary JSON to KTOF while returning size stats. | `EncodeRequest` |
| `decompress()` | `POST /v1/decompress` | Expand KTOF back into structured JSON. | `DecodeRequest` |
| `optimize()` | `POST /v1/optimize` | Encode + compute `token_stats` in a single call. | `EncodeRequest` |
| `optimize_request()` | `POST /v1/optimize/request` | Compress an outbound provider request payload. | `OptimizeRequestPayload` |
| `optimize_response()` | `POST /v1/optimize/response` | Decompress a provider response payload. | `OptimizeResponsePayload` |
| `prompts_encode()` | `POST /v1/prompts/encode` | Auto-detect structured snippets in prompts and compress them. | `PromptEncodePayload` |
| `prompts_decode()` | `POST /v1/prompts/decode` | Retrieve a previously encoded prompt via `payload_id`/`ktof`. | `PromptDecodePayload` |
| `health()` | `GET /` | Lightweight liveness check against the Kaizen deployment. | None |

All methods accept either fully typed models from `kaizen_client.models` or plain dictionaries. Responses default to raw `dict` objects but can be validated into models by passing `response_model=...` to the private `_post` helper if you fork the client.

## Provider integrations

`kaizen_client.integrations` exposes thin wrappers so you can keep your existing LLM client code and let Kaizen handle payload compression transparently:

- `kaizen_client.integrations.openai.OpenAIKaizenWrapper`: wraps `openai.AsyncOpenAI` / `OpenAI`.
- `kaizen_client.integrations.anthropic.AnthropicKaizenWrapper`: wraps `anthropic.AsyncAnthropic` / `Anthropic`.
- `kaizen_client.integrations.gemini.GeminiKaizenWrapper`: wraps `google.generativeai.GenerativeModel`.

Each integration accepts a `KaizenClient` (or config options) plus the vendor client. The decorators/mixins ensure `prompts_encode` is invoked before outbound calls and `prompts_decode` is applied to responses when needed. See the runnable snippets documented in [`examples/README.md`](examples/README.md) for end-to-end usage.

## Testing & development

```bash
cd python
uv pip install -e .[all]
pytest
```

Key tests live in `tests/test_client.py` and rely on in-memory HTTPX doubles, so the suite runs offline.

## References

- [`../README.md`](../README.md) – repository-wide overview and roadmap.
- [`../docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md) – structure + guiding principles.
- [`../docs/sdk_reference.md`](../docs/sdk_reference.md) – exhaustive API contract (a.k.a. “Kaizen SDK Knowledge Transfer”).
- [`../openapi.json`](../openapi.json) – machine-readable schema for generated clients.
