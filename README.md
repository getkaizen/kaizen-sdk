# Kaizen SDKs

Official multi-language clients, CLIs, and tooling for the Kaizen Token Optimized Format (KTOF) service. Start here to compress prompts before calling model providers and to decode KTOF responses back into structured JSON.

> **Status:** Python SDK is live; JavaScript, Go, and CLI packages are on the roadmap.

## Highlights

- Shared repository for every Kaizen client to keep docs, schemas, and release processes in sync.
- Production-ready HTTP helpers with retries, timeouts, and structured errors.
- Drop-in provider wrappers for Gemini 2.5 Flash, OpenAI GPT-4/o-series, and Anthropic Claude.
- Examples plus cost/latency comparison tooling to demonstrate savings.

## Repository Layout

| Path | Description |
| ---- | ----------- |
| `kaizen_client/` | Current Python SDK source. |
| `examples/` | Provider walkthroughs, benchmarking, and quickstarts. |
| `docs/` | Supplemental design notes and integration guides. |
| `tests/` | Unit and integration tests that run in CI. |

As additional SDKs are added, each language will gain its own top-level directory (e.g. `python/`, `js/`, `go/`) with shared specs and fixtures under `shared/`.

## Python Quickstart

```bash
uv pip install -e .[all]  # or: pip install -e .[all]
```

```python
from kaizen_client import KaizenClient

client = KaizenClient(base_url="http://127.0.0.1:8000")
encoded = await client.prompts_encode([{"role": "user", "content": "Compress me"}])
decoded = await client.prompts_decode(encoded.payload_id)
```

### Configuration

1. Set `KAIZEN_BASE_URL` or pass `base_url` when instantiating `KaizenClient` (defaults to `http://127.0.0.1:8000`).
2. Provide an API key if your deployment enforces authentication (`KaizenClient(api_key="...")`).
3. Drop in the provider wrapper that matches your LLM vendor to transparently compress/expand requests.

## Development Workflow

1. Install dependencies: `uv pip install -e .[all]` (or `pip install -e .[all]`).
2. Run the suite: `pytest`.
3. Lint/format (coming soon for each SDK family).
4. Add or update examples under `examples/` to document new features.

## Contributing

We follow the usual OSS flow:

1. Fork + create a topic branch.
2. Write tests/docs alongside code.
3. Open a PR that references an issue or proposal.

See `CONTRIBUTING.md` (to be added) for language-specific guidelines, release instructions, and RFC templates.

## Roadmap

- [ ] Publish Python SDK to PyPI under the `kaizen-sdks` org.
- [ ] Scaffold JavaScript/TypeScript client with fetch-based transport.
- [ ] Ship a lightweight CLI for manual KTOF encode/decode inspection.
- [ ] Generate shared protocol docs and JSON schema artifacts for every SDK.

## License

TBD (final choice pending). Let us know if you have requirements or expectations here.
