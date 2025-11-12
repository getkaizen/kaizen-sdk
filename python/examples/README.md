# Examples

Each script assumes you have installed the SDK extras (see below) and exported:

```bash
export KAIZEN_API_KEY="kaizen_xxx"
# optional: override only if Kaizen provisions a dedicated/enterprise host for you
export KAIZEN_BASE_URL="https://api.getkaizen.io/"
```

Provider-specific credentials are also required:

| Example | Extra env vars |
|---------|----------------|
| `openai_example.py` | `OPENAI_API_KEY`, optional `OPENAI_MODEL` |
| `anthropic_example.py` | `ANTHROPIC_API_KEY`, optional `ANTHROPIC_MODEL` |
| `gemini_example.py` | `GOOGLE_API_KEY`, optional `GOOGLE_MODEL` |
| `cost_comparison.py` | `TIKTOKEN_CACHE_DIR` (optional), provider-specific tokens if you extend it |
| `full_lifecycle.py` | No additional vars beyond Kaizen (does not hit providers) |

> ⚠️ **Blocking wrappers:** the provider wrappers currently instantiate synchronous vendor clients. If your app is sensitive to event-loop stalls, invoke the examples inside `asyncio.to_thread` or another executor until the wrappers adopt the async SDKs.

### Installing optional extras

Install only what you need for faster environments:

```bash
uv pip install -e .[openai]      # OpenAI example
uv pip install -e .[anthropic]   # Anthropic example
uv pip install -e .[gemini]      # Gemini example
uv pip install -e .[all]         # Everything (OpenAI + Anthropic + Gemini + tiktoken)
```

If you prefer `pip`, replace `uv pip install -e` with `pip install -e`.

| File | Description |
|------|-------------|
| `full_lifecycle.py` | Demonstrates encode → optimize → decode flow plus health checks using plain `KaizenClient`. |
| `openai_example.py` | Wraps the OpenAI Responses API with `OpenAIKaizenWrapper`. |
| `anthropic_example.py` | Routes prompts through `AnthropicKaizenWrapper` and prints decoded Claude replies. |
| `gemini_example.py` | Shows how to compress prompts before calling Gemini 2.5 Flash. |
| `cost_comparison.py` | Benchmarks token/byte savings for a prompt across providers. |

All scripts are async and rely on `asyncio.run` internally, so you can launch them directly:

```bash
cd python
python -m examples.<name>
# or
python examples/<name>.py
```

`full_lifecycle.py` is the fastest way to verify your environment. It:

1. Encodes a structured chat prompt (`prompts_encode`) and prints size/token stats.
2. Decodes the generated KTOF string (`prompts_decode`) to prove symmetry.
3. Runs `optimize_request`/`optimize_response` so you can see segment metadata before/after a provider call.
4. Calls `compress`/`decompress` on arbitrary JSON and finishes with a `health` probe.
