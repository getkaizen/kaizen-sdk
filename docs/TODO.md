# Kaizen SDK TODOs

Tracked gaps that need follow-up without immediately altering the core client runtime.

---

## P0 - Critical (Blocking production scale)

### Core Functionality
- **Streaming support**: Add `prompts_encode_stream()` and `prompts_decode_stream()` methods for incremental results
- **Async provider clients**: Update OpenAI/Anthropic/Gemini wrappers to use `AsyncOpenAI`, `AsyncAnthropic`, async Gemini (or wrap in `asyncio.to_thread`)

---

## P1 - High Priority (Needed for production readiness)

### Error Handling & Observability
- **Structured error responses**: Make `KaizenAPIError` parse structured error codes, messages, and request IDs from API
- **Logging infrastructure**: Add structured logging throughout client (request/response/timing)
- **Request ID tracking**: Auto-inject `X-Request-ID` headers and expose in responses for debugging
- **Provider error mapping**: Catch vendor-specific exceptions (e.g., `openai.RateLimitError`) and wrap in Kaizen exceptions

### API Features
- **Batch operations**: Add `prompts_encode_batch()` for encoding multiple prompts in one request
- **Retry logic**: Add configurable retry with exponential backoff for transient failures (503, network errors)
- **Rate limit handling**: Auto-retry on 429 with `Retry-After` header support, or raise specific `KaizenRateLimitError`

### Testing
- **Integration tests**: Create `tests/integration/` with tests against real/staging API (run when `KAIZEN_API_KEY` set)
- **Provider wrapper tests**: Add encode/decode wrapper tests using dummy vendor clients
- **Error scenario tests**: Test network timeouts, malformed responses, partial data, rate limits

### Type Safety
- **Typed response models**: Return structured Pydantic models instead of `Dict[str, Any]`
- **Add py.typed marker**: Include `python/kaizen_client/py.typed` file for type checker support
- **Health check response model**: Create `HealthResponse` model instead of generic dict

---

## P2 - Medium Priority (Quality of life improvements)

### Developer Experience
- **Decorator improvements**: Support positional `kaizen` argument injection, not just keyword
- **Token estimation utility**: Add client-side `estimate_tokens()` using tiktoken for pre-flight checks
- **Connection pooling config**: Expose `max_connections`, `max_keepalive_connections`, `keepalive_expiry`
- **Timeout granularity**: Split timeout into `connect_timeout`, `read_timeout`, `write_timeout`, `pool_timeout`

### Observability & Metrics
- **Metrics collection interface**: Add optional `MetricsCollector` protocol for tracking latency, errors, token usage
- **Cost tracking helpers**: Provide utilities to calculate monthly cost estimates based on usage patterns

### Configuration
- **Proxy support**: Add `proxy` and `proxy_auth` configuration for enterprise environments
- **Custom CA certificates**: Support `ca_bundle` path for self-hosted deployments with custom TLS
- **Caching layer**: Optional caching backend (in-memory, Redis) to avoid re-encoding identical prompts

### Documentation
- **Document sync wrapper caveats**: Warn in README that current wrappers use sync vendor SDKs
- **API reference docs**: Auto-generate docs from docstrings using Sphinx/MkDocs
- **Troubleshooting guide**: Document common errors and how to debug them
- **Architecture diagrams**: Add sequence diagrams for encode→provider→decode flows

---

## P3 - Nice to Have (Future enhancements)

### Provider Coverage
- Add wrappers for: Cohere, Mistral AI, Azure OpenAI, AWS Bedrock, Hugging Face, Together AI, Fireworks AI
- **Streaming in wrappers**: Expose streaming methods in provider wrappers when base client supports it

### User Experience
- **CLI tool**: Create `kaizen` command-line tool for testing encode/decode from terminal
- **Interactive examples**: Add Jupyter notebook with real-world usage examples
- **Cost calculator**: Standalone tool to estimate monthly costs based on usage patterns

### Security & Resilience
- **Secrets redaction**: Automatically redact API keys in logs and error messages
- **Client-side rate limiting**: Add `max_requests_per_second` config to prevent hitting API limits
- **Input validation**: Add checks for excessively large payloads or malicious input

### Development Workflow
- **Pre-commit hooks**: Set up Black, Ruff, mypy, Bandit for automated code quality
- **CI/CD pipelines**: Add GitHub Actions for testing, linting, docs generation, PyPI publishing
- **Changelog**: Maintain `CHANGELOG.md` tracking changes between versions
- **Migration guides**: Create `docs/MIGRATION.md` for breaking changes between major versions

### Testing
- **Load/performance tests**: Benchmark concurrent request handling, memory usage, connection pooling
- **Contract tests**: Validate API responses match OpenAPI schema

### Middleware & Extensibility
- **Request/response middleware**: Add middleware protocol for custom logic (audit logging, auth, telemetry)
- **Plugin system**: Allow third-party extensions for custom providers or transformations

---

## Integrations
- Update OpenAI/Anthropic/Gemini wrappers to rely on the vendors' async clients (e.g., `AsyncOpenAI`, `AsyncAnthropic`, `genai.aio`). If synchronous calls must remain, run them in `asyncio.to_thread` to avoid blocking the event loop.

## Testing
- Add integration-style tests (using dummy transports) for each provider wrapper to ensure encode/decode happens around the vendor SDK calls.
