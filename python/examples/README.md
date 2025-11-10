# Examples

Each script assumes you have installed the SDK extras (`uv pip install -e .[all]`) and exported:

```bash
export KAIZEN_API_KEY="kaizen_xxx"
# optional: override only if you are targeting staging/local instead of the hosted API
export KAIZEN_BASE_URL="https://api.getkaizen.io/"
```

| File | Description |
|------|-------------|
| `openai_example.py` | Wraps the OpenAI Responses API with `OpenAIKaizenWrapper`. |
| `gemini_example.py` | Shows how to compress prompts before calling Gemini 2.5 Flash. |
| `cost_comparison.py` | Benchmarks token/byte savings for a prompt across providers. |

Run an example via `python -m examples.<name>` or `python examples/<name>.py` from the `python/` directory.
