# Kaizen Python SDK

Typed async client, provider adapters, and helpers for working with the Kaizen Token Optimized Format (KTOF) service. This package lives inside the `kaizen-sdks` monorepo under `python/` and mirrors the public Kaizen REST API exactly.

## Before you start

1. **Request access** – Email `hello@getkaizen.ai` for a production API key.
2. **Environment variables** – Export the following (or pass via `KaizenClientConfig`):
   - `KAIZEN_BASE_URL` – defaults to `https://api.getkaizen.io/`; override only when Kaizen provisions a dedicated host for you or you have an approved self-hosted deployment.
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

## Managing the client lifecycle

Many apps only need a Kaizen client for the duration of a single workflow. Use the provided `with_kaizen_client` decorator to ensure the client is created (if missing) and closed automatically:

```python
from kaizen_client import with_kaizen_client

@with_kaizen_client()
async def compress_prompt(*, kaizen, messages):
    encoded = await kaizen.prompts_encode({"prompt": {"messages": messages}})
    return encoded["result"], encoded["stats"]

# Callers can optionally pass their own KaizenClient:
# await compress_prompt(messages=msgs, kaizen=my_existing_client)
```

Behind the scenes the decorator injects a `kaizen` keyword argument, so you can override it in tests or when reusing a long-lived client.
```

## Environment targets

- **Production (default):** `https://api.getkaizen.io/`.
- **Managed staging/internal:** if Kaizen hosts a dedicated env for you, set `KAIZEN_BASE_URL` to that URL.
- **Self-hosted / air-gapped (Enterprise tier):** contact `hello@getkaizen.ai` to obtain the FastAPI build + deployment checklist before pointing `KAIZEN_BASE_URL` at your infrastructure.

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

### Sample `prompts_encode` response

```json
{
  "operation": "prompts.encode",
  "status": "ok",
  "result": "KTOF:....",
  "stats": {"original_bytes": 1024, "compressed_bytes": 312, "reduction_ratio": 0.304},
  "token_stats": {"gpt-4o-mini": {"original": 210, "compressed": 68}},
  "metadata": {"example": "full-lifecycle"}
}
```

You can pass `token_models` to receive the `token_stats` block or omit it to skip tokenization entirely.
## Provider integrations

`kaizen_client.integrations` exposes thin wrappers so you can keep your existing LLM client code and let Kaizen handle payload compression transparently:

- `kaizen_client.integrations.openai.OpenAIKaizenWrapper`: wraps `openai.AsyncOpenAI` / `OpenAI`.
- `kaizen_client.integrations.anthropic.AnthropicKaizenWrapper`: wraps `anthropic.AsyncAnthropic` / `Anthropic`.
- `kaizen_client.integrations.gemini.GeminiKaizenWrapper`: wraps `google.generativeai.GenerativeModel`.

Each integration accepts a `KaizenClient` (or config options) plus the vendor client. The decorators/mixins ensure `prompts_encode` is invoked before outbound calls and `prompts_decode` is applied to responses when needed. See the runnable snippets documented in [`examples/README.md`](examples/README.md) for end-to-end usage.

### Provider prerequisites

| Integration | Extra dependency | Environment variables |
|-------------|------------------|-----------------------|
| OpenAI | `openai` | `OPENAI_API_KEY`, optional `OPENAI_MODEL` override |
| Anthropic | `anthropic` | `ANTHROPIC_API_KEY`, optional `ANTHROPIC_MODEL` override |
| Gemini | `google-generativeai` | `GOOGLE_API_KEY`, optional `GOOGLE_MODEL` override |

`KAIZEN_API_KEY` is still required for every example; the additional keys authenticate with the respective LLM vendor. Configure them via `.env`, your process manager, or cloud secret manager before running the scripts.

> ⚠️ **Current limitation:** the Python wrappers instantiate the vendors' synchronous clients (`OpenAI`, `anthropic.Anthropic`, `google.generativeai.GenerativeModel`) inside async functions. Until the wrappers are refactored to their async equivalents, avoid calling them on a latency-sensitive event loop. Run them in worker threads via `asyncio.to_thread` or dedicate a background task/executor so they do not block other coroutines.

## Testing & development

```bash
cd python
uv pip install -e .[all]
pytest
```

Key tests live in `tests/test_client.py` and rely on in-memory HTTPX doubles, so the suite runs offline.

When handling failures, catch `KaizenAPIError` for non-2xx responses (inspect `status_code`, `payload`, and `headers`) and `KaizenRequestError` for transport issues (timeouts, DNS, TLS errors).

## References

- [`../README.md`](../README.md) – repository-wide overview and roadmap.
- [`../docs/TODO.md`](../docs/TODO.md) – prioritized backlog and upcoming documentation plans.
- [`../docs/ISSUE_DRAFTS.md`](../docs/ISSUE_DRAFTS.md) – GitHub issue drafts ready for filing.
- [`../openapi.json`](../openapi.json) – machine-readable schema for generated clients.
