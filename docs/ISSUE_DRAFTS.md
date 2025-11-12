# GitHub Issue Drafts

Draft language for engineering issues derived from `docs/TODO.md`. Copy/paste each block into GitHub when opening tickets.

---

## P0 - Critical Issues

### Issue #1: Add streaming support for prompts encode/decode
**Labels:** `P0`, `enhancement`, `core`

**Summary:**
Add streaming methods to the SDK for incremental encoding/decoding of large prompts. This enables real-time processing for long-running LLM interactions and reduces latency for users waiting on complete responses.

**Motivation:**
- Modern LLM APIs support streaming responses
- Users need incremental results for better UX (typewriter effects, progress indicators)
- Large prompts benefit from chunked processing

**Proposed API:**
```python
async def prompts_encode_stream(
    self,
    payload: PromptEncodePayload | Mapping[str, Any]
) -> AsyncIterator[Dict[str, Any]]:
    """Stream encoded prompt chunks as they're generated."""

async def prompts_decode_stream(
    self,
    ktof_chunks: AsyncIterator[str]
) -> AsyncIterator[Dict[str, Any]]:
    """Decode streaming KTOF responses incrementally."""
```

**Acceptance Criteria:**
- [ ] `prompts_encode_stream()` method added to `KaizenClient`
- [ ] `prompts_decode_stream()` method added to `KaizenClient`
- [ ] Unit tests with mock streaming responses
- [ ] Example in `python/examples/` demonstrating streaming usage
- [ ] Documentation updated with streaming patterns

**Estimated Effort:** Large (3-5 days)

---

### Issue #2: Make provider wrappers non-blocking
**Labels:** `P0`, `bug`, `integrations`

**Title:** Update provider wrappers to use async vendor SDKs (no sync blocking)

**Summary:**
Refactor the OpenAI, Anthropic, and Gemini wrappers to rely on their async clients (`AsyncOpenAI`, `AsyncAnthropic`, async Gemini) or, if unavailable, run sync calls via `asyncio.to_thread` so the event loop is never blocked.

**Current Problem:**
```python
# python/kaizen_client/integrations/openai.py:21
self._client = OpenAI()  # Sync client!

# openai.py:26
completion = self._client.responses.create(...)  # Blocks event loop!
```

**Impact:**
- High-throughput applications serialize on these blocking calls
- Concurrent requests can't leverage async I/O benefits
- Users experience degraded performance under load

**Proposed Solution:**
```python
from openai import AsyncOpenAI

class OpenAIKaizenWrapper:
    def __init__(self, ...):
        self._client = AsyncOpenAI()  # Async client

    async def chat(self, messages: list[Dict[str, str]], **options: Any):
        encoded = await self._kaizen.prompts_encode(...)
        completion = await self._client.responses.create(...)  # Async!
        decoded = await self._kaizen.prompts_decode(...)
        return {...}
```

**Acceptance Criteria:**
- [ ] `OpenAIKaizenWrapper` uses `AsyncOpenAI`
- [ ] `AnthropicKaizenWrapper` uses `AsyncAnthropic`
- [ ] `GeminiKaizenWrapper` uses async Gemini client (or `asyncio.to_thread`)
- [ ] All wrapper methods are truly async (no blocking I/O)
- [ ] Tests updated to use async vendor clients
- [ ] Documentation calls out any new dependencies
- [ ] Benchmark showing improved concurrent throughput

**Estimated Effort:** Medium (2-3 days)

---

## P1 - High Priority Issues

### Issue #3: Add structured error responses
**Labels:** `P1`, `enhancement`, `error-handling`

**Summary:**
Make `KaizenAPIError` parse and expose structured error information (error codes, messages, request IDs) from the API instead of raw payloads.

**Current Problem:**
```python
# client.py:144
raise KaizenAPIError(response.status_code, payload, response.headers)
# payload is Any - could be dict, string, or malformed JSON
```

**Proposed Solution:**
```python
@dataclass(slots=True)
class KaizenAPIError(KaizenError):
    status_code: int
    error_code: Optional[str]  # e.g., "rate_limit_exceeded"
    message: str
    details: Optional[Dict[str, Any]]
    request_id: Optional[str]  # For support debugging
    headers: Mapping[str, str]

    def __str__(self) -> str:
        return f"Kaizen API error {self.status_code} [{self.error_code}]: {self.message}"
```

**Acceptance Criteria:**
- [ ] Update `KaizenAPIError` dataclass with new fields
- [ ] Parse structured errors from API responses
- [ ] Extract `request_id` from headers (`X-Request-ID`)
- [ ] Add specific exception subclasses: `KaizenRateLimitError`, `KaizenValidationError`
- [ ] Update tests to verify error parsing
- [ ] Document error handling patterns

**Estimated Effort:** Small (1 day)

---

### Issue #4: Add logging infrastructure
**Labels:** `P1`, `enhancement`, `observability`

**Summary:**
Add structured logging throughout the client to provide visibility into requests, responses, timing, and errors.

**Motivation:**
- Users have zero visibility into what the SDK is doing
- Debugging production issues requires instrumenting the SDK manually
- No way to track performance bottlenecks

**Proposed Implementation:**
```python
import logging
logger = logging.getLogger("kaizen_client")

async def _request(self, method: str, path: str, ...) -> Dict[str, Any]:
    url = self._resolve_path(path)
    logger.debug(f"Sending {method} {url}", extra={"payload_size": len(json_payload)})

    start = time.monotonic()
    response = await self._client.request(...)
    duration_ms = (time.monotonic() - start) * 1000

    logger.info(
        f"{method} {url} -> {response.status_code} in {duration_ms:.1f}ms",
        extra={
            "method": method,
            "url": url,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
        }
    )
```

**Acceptance Criteria:**
- [ ] Add logger at module level (`kaizen_client`)
- [ ] Log all outbound requests (DEBUG level)
- [ ] Log responses with status + timing (INFO level)
- [ ] Log errors with context (ERROR level)
- [ ] Redact sensitive headers (Authorization)
- [ ] Add logging configuration example to docs
- [ ] Structured logging format (JSON-friendly)

**Estimated Effort:** Medium (2 days)

---

### Issue #5: Add batch operations
**Labels:** `P1`, `enhancement`, `api`

**Summary:**
Add `prompts_encode_batch()` method to encode multiple prompts in a single API request, reducing round-trips and improving throughput.

**Use Case:**
Users processing 1,000 prompts need to make 1,000 sequential API calls, causing high latency and poor performance.

**Proposed API:**
```python
async def prompts_encode_batch(
    self,
    payloads: List[PromptEncodePayload | Mapping[str, Any]]
) -> List[Dict[str, Any]]:
    """Encode multiple prompts in a single request."""
    return await self._post("v1/prompts/encode/batch", {"items": payloads})
```

**Acceptance Criteria:**
- [ ] API endpoint supports batch encoding (coordinate with backend team)
- [ ] Add `prompts_encode_batch()` method
- [ ] Add `prompts_decode_batch()` method
- [ ] Unit tests with mock batch responses
- [ ] Example demonstrating batch usage + performance comparison
- [ ] Documentation updated

**Estimated Effort:** Medium (depends on API readiness) (2-3 days)

---

### Issue #6: Add retry logic with exponential backoff
**Labels:** `P1`, `enhancement`, `resilience`

**Summary:**
Add configurable retry logic for transient failures (503, network errors) with exponential backoff to improve SDK resilience.

**Current Problem:**
Any transient network error or API hiccup causes immediate failure. Users must implement retry logic themselves.

**Proposed Solution:**
```python
@dataclass(slots=True)
class KaizenClientConfig:
    max_retries: int = 3
    retry_backoff_factor: float = 1.0  # 1s, 2s, 4s
    retry_on_status_codes: Set[int] = field(default_factory=lambda: {429, 500, 502, 503, 504})
```

**Acceptance Criteria:**
- [ ] Add retry configuration to `KaizenClientConfig`
- [ ] Implement exponential backoff in `_request()`
- [ ] Respect `Retry-After` header for 429 responses
- [ ] Log retry attempts
- [ ] Add tests for retry scenarios
- [ ] Document retry behavior

**Estimated Effort:** Medium (2 days)

---

### Issue #7: Add integration tests
**Labels:** `P1`, `testing`

**Summary:**
Create `tests/integration/` directory with tests that run against a real or staging API to validate actual behavior.

**Current Gap:**
All tests use mocks (`DummyAsyncClient`). No validation that the SDK actually works with the real API.

**Proposed Structure:**
```
python/tests/
├── test_client.py           # Unit tests (existing)
└── integration/
    ├── __init__.py
    ├── test_live_api.py      # Real API calls
    ├── test_openai_wrapper.py
    └── test_error_scenarios.py
```

**Acceptance Criteria:**
- [ ] Integration tests run only when `KAIZEN_API_KEY` is set
- [ ] Use `pytest.mark.integration` to skip in CI
- [ ] Test all major endpoints (encode, decode, optimize, health)
- [ ] Test error scenarios (invalid API key, malformed payloads)
- [ ] Test rate limiting behavior
- [ ] Add instructions for running integration tests

**Estimated Effort:** Medium (2-3 days)

---

### Issue #8: Return typed response models instead of dicts
**Labels:** `P1`, `enhancement`, `type-safety`

**Summary:**
Create Pydantic response models for all API methods instead of returning `Dict[str, Any]`.

**Current Problem:**
```python
async def compress(self, ...) -> Dict[str, Any]:  # Untyped!
```

Users have no IDE autocomplete or type checking for response fields.

**Proposed Solution:**
```python
class CompressResponse(_BaseModel):
    operation: str
    status: str
    result: str
    stats: CompressionStats
    metadata: Optional[Dict[str, Any]] = None

async def compress(self, ...) -> CompressResponse:
    return CompressResponse.model_validate(await self._post(...))
```

**Acceptance Criteria:**
- [ ] Create response models in `models.py`:
  - `CompressResponse`
  - `DecompressResponse`
  - `OptimizeResponse`
  - `PromptEncodeResponse`
  - `PromptDecodeResponse`
  - `HealthResponse`
- [ ] Update all client methods to return typed models
- [ ] Add `py.typed` marker file
- [ ] Update tests to assert on model fields
- [ ] Update examples to use typed responses

**Estimated Effort:** Medium (2 days)

---

### Issue #9: Add encode/decode wrapper tests
**Labels:** `P1`, `testing`, `integrations`

**Title:** Add encode/decode wrapper tests using dummy vendor clients

**Summary:**
Create tests that simulate the OpenAI/Anthropic/Gemini wrappers to guarantee they call `prompts_encode` before vendor APIs and `prompts_decode` afterward.

**Acceptance Criteria:**
- [ ] Tests cover happy path for each wrapper with stubbed vendor clients
- [ ] Failing encode/decode surfaces bubble errors appropriately
- [ ] Tests live under `python/tests/` and integrate into existing CI
- [ ] Verify encoding stats are captured
- [ ] Test error scenarios (encoding fails, vendor API fails, decoding fails)

**Estimated Effort:** Small (1 day)

---

## P2 - Medium Priority Issues

### Issue #10: Support positional kaizen argument in decorator
**Labels:** `P2`, `enhancement`, `decorators`

**Summary:**
Update `@with_kaizen_client` decorator to support `kaizen` as a positional argument, not just keyword argument.

**Current Limitation:**
```python
@with_kaizen_client()
async def process(kaizen):  # Only works if passed as kaizen=...
    pass
```

**Proposed Solution:**
```python
# decorators.py
import inspect

def decorator(func: F) -> F:
    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        kaizen = kwargs.get("kaizen")
        if kaizen is None:
            # Check positional args
            sig = inspect.signature(func)
            if "kaizen" in sig.parameters:
                param_names = list(sig.parameters.keys())
                param_index = param_names.index("kaizen")
                if len(args) > param_index:
                    kaizen = args[param_index]
        # ... rest of logic
```

**Acceptance Criteria:**
- [ ] Decorator supports positional `kaizen` argument
- [ ] Tests verify both positional and keyword injection
- [ ] Documentation updated with examples

**Estimated Effort:** Small (0.5 day)

---

### Issue #11: Add token estimation utility
**Labels:** `P2`, `enhancement`, `api`

**Summary:**
Add client-side `estimate_tokens()` method using tiktoken for pre-flight token estimation before calling the API.

**Use Case:**
Users want to know if a prompt will fit within model token limits before paying for API calls.

**Proposed API:**
```python
def estimate_tokens(
    self,
    text: str,
    model: str = "gpt-4o-mini"
) -> int:
    """Estimate token count for text using tiktoken."""
    import tiktoken
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))
```

**Acceptance Criteria:**
- [ ] Add `estimate_tokens()` method (non-async, local only)
- [ ] Add tiktoken as optional dependency
- [ ] Support common models (GPT-4, Claude, etc.)
- [ ] Add example comparing estimated vs actual tokens
- [ ] Document limitations (client-side estimation may differ from API)

**Estimated Effort:** Small (1 day)

---

### Issue #12: Add connection pooling configuration
**Labels:** `P2`, `enhancement`, `config`

**Summary:**
Expose httpx connection pooling parameters in `KaizenClientConfig` for high-throughput applications.

**Proposed Configuration:**
```python
@dataclass(slots=True)
class KaizenClientConfig:
    max_connections: int = 100
    max_keepalive_connections: int = 20
    keepalive_expiry: float = 5.0
```

**Acceptance Criteria:**
- [ ] Add connection pool config fields
- [ ] Pass to `httpx.AsyncClient` constructor
- [ ] Document recommended settings for different use cases
- [ ] Add example for high-concurrency scenarios

**Estimated Effort:** Small (0.5 day)

---

### Issue #13: Add granular timeout configuration
**Labels:** `P2`, `enhancement`, `config`

**Summary:**
Replace single `timeout` with separate `connect_timeout`, `read_timeout`, `write_timeout`, `pool_timeout`.

**Current Limitation:**
```python
timeout: float = DEFAULT_TIMEOUT  # Same for all operations
```

**Proposed Solution:**
```python
@dataclass(slots=True)
class KaizenClientConfig:
    connect_timeout: float = 5.0
    read_timeout: float = 30.0
    write_timeout: float = 10.0
    pool_timeout: float = 5.0
```

**Acceptance Criteria:**
- [ ] Add granular timeout fields
- [ ] Create `httpx.Timeout` object from config
- [ ] Update tests
- [ ] Document timeout tuning guide

**Estimated Effort:** Small (0.5 day)

---

### Issue #14: Add metrics collection interface
**Labels:** `P2`, `enhancement`, `observability`

**Summary:**
Add optional `MetricsCollector` protocol that users can implement to track SDK usage metrics.

**Proposed API:**
```python
from typing import Protocol

class MetricsCollector(Protocol):
    def record_request(
        self,
        endpoint: str,
        duration_ms: float,
        status: int,
        error: Optional[Exception] = None
    ) -> None: ...

@dataclass(slots=True)
class KaizenClientConfig:
    metrics: Optional[MetricsCollector] = None
```

**Acceptance Criteria:**
- [ ] Define `MetricsCollector` protocol
- [ ] Call metrics methods from client
- [ ] Add example implementation (Prometheus, Datadog)
- [ ] Document how to integrate with monitoring systems

**Estimated Effort:** Medium (2 days)

---

### Issue #15: Add proxy support
**Labels:** `P2`, `enhancement`, `config`

**Summary:**
Add proxy configuration for enterprise environments that require HTTP proxies.

**Proposed Configuration:**
```python
@dataclass(slots=True)
class KaizenClientConfig:
    proxy: Optional[str] = None  # "http://proxy.corp.com:8080"
    proxy_auth: Optional[Tuple[str, str]] = None  # (username, password)
```

**Acceptance Criteria:**
- [ ] Add proxy config fields
- [ ] Pass to `httpx.AsyncClient` via `proxies` parameter
- [ ] Test with mock proxy
- [ ] Document proxy configuration

**Estimated Effort:** Small (1 day)

---

### Issue #16: Add custom CA certificate support
**Labels:** `P2`, `enhancement`, `config`

**Summary:**
Support custom CA certificates for self-hosted deployments with custom TLS certificates.

**Proposed Configuration:**
```python
@dataclass(slots=True)
class KaizenClientConfig:
    ca_bundle: Optional[str] = None  # Path to CA cert file
```

**Acceptance Criteria:**
- [ ] Add `ca_bundle` config field
- [ ] Pass to `httpx.AsyncClient` via `verify` parameter
- [ ] Test with self-signed cert
- [ ] Document for self-hosted deployments

**Estimated Effort:** Small (0.5 day)

---

### Issue #17: Add caching layer
**Labels:** `P2`, `enhancement`, `performance`

**Summary:**
Add optional caching backend to avoid re-encoding identical prompts.

**Motivation:**
Production apps often re-encode the same prompts repeatedly, wasting API calls and money.

**Proposed API:**
```python
from typing import Protocol

class CacheBackend(Protocol):
    async def get(self, key: str) -> Optional[str]: ...
    async def set(self, key: str, value: str, ttl: int = 3600) -> None: ...

@dataclass(slots=True)
class KaizenClientConfig:
    enable_cache: bool = False
    cache_backend: Optional[CacheBackend] = None
```

**Acceptance Criteria:**
- [ ] Define `CacheBackend` protocol
- [ ] Implement in-memory cache backend
- [ ] Add Redis cache backend example
- [ ] Cache encode results by prompt hash
- [ ] Add cache hit/miss metrics
- [ ] Document caching strategies

**Estimated Effort:** Large (3-4 days)

---

### Issue #18: Document sync wrapper caveats
**Labels:** `P2`, `documentation`

**Title:** Document current sync behavior of provider wrappers

**Summary:**
Call out in the README(s) and example docs that the existing OpenAI/Anthropic/Gemini wrappers instantiate synchronous vendor clients, so users should avoid running them on latency-sensitive event loops (or wrap them with `asyncio.to_thread`) until the wrappers become fully async.

**Acceptance Criteria:**
- [ ] Root README warns about sync calls in wrappers
- [ ] `python/examples/README.md` includes mitigation strategies
- [ ] Link to tracking issue (#2) for async refactor
- [ ] Add FAQ entry about async/sync behavior

**Estimated Effort:** Small (0.5 day)

---

### Issue #19: Generate API reference docs
**Labels:** `P2`, `documentation`

**Summary:**
Auto-generate API reference documentation from docstrings using Sphinx or MkDocs.

**Acceptance Criteria:**
- [ ] Set up Sphinx or MkDocs
- [ ] Configure autodoc to extract docstrings
- [ ] Generate docs for all public APIs
- [ ] Host on Read the Docs or GitHub Pages
- [ ] Add link to docs in README

**Estimated Effort:** Medium (2-3 days)

---

### Issue #20: Create troubleshooting guide
**Labels:** `P2`, `documentation`

**Summary:**
Document common errors and how to debug them.

**Proposed Content:**
- "Why am I getting `KaizenRequestError`?" (DNS, firewall, proxy issues)
- "How do I debug token count mismatches?"
- "What do error codes mean?"
- "How to enable debug logging"
- "SSL certificate errors in self-hosted deployments"

**Acceptance Criteria:**
- [ ] Create `docs/TROUBLESHOOTING.md`
- [ ] Cover common error scenarios
- [ ] Include debugging commands
- [ ] Link from main README

**Estimated Effort:** Small (1 day)

---

## P3 - Nice to Have Issues

### Issue #21: Add support for more LLM providers
**Labels:** `P3`, `enhancement`, `integrations`

**Summary:**
Add wrappers for additional LLM providers: Cohere, Mistral AI, Azure OpenAI, AWS Bedrock, Hugging Face, Together AI, Fireworks AI.

**Acceptance Criteria:**
- [ ] Create wrapper for each provider
- [ ] Follow same pattern as existing wrappers
- [ ] Add examples for each
- [ ] Add to optional dependencies

**Estimated Effort:** Large (1 week)

---

### Issue #22: Create CLI tool
**Labels:** `P3`, `enhancement`, `tooling`

**Summary:**
Create `kaizen` command-line tool for testing encode/decode from terminal.

**Proposed Commands:**
```bash
kaizen encode --prompt "Hello world" --model gpt-4o-mini
kaizen decode --ktof "KTOF:..."
kaizen optimize --file prompt.json
kaizen health
```

**Acceptance Criteria:**
- [ ] CLI using Click or Typer
- [ ] Support all major operations
- [ ] Install as `kaizen` command
- [ ] Add usage examples

**Estimated Effort:** Medium (2-3 days)

---

### Issue #23: Add secrets redaction in logging
**Labels:** `P3`, `security`, `observability`

**Summary:**
Automatically redact API keys and sensitive headers in logs and error messages.

**Proposed Implementation:**
```python
def _redact_headers(headers: Dict[str, str]) -> Dict[str, str]:
    redacted = dict(headers)
    if "Authorization" in redacted:
        redacted["Authorization"] = "Bearer ***REDACTED***"
    return redacted
```

**Acceptance Criteria:**
- [ ] Redact Authorization header in logs
- [ ] Redact sensitive fields in error messages
- [ ] Add test verifying redaction
- [ ] Document security practices

**Estimated Effort:** Small (0.5 day)

---

### Issue #24: Set up pre-commit hooks
**Labels:** `P3`, `tooling`, `dx`

**Summary:**
Configure pre-commit hooks for automated code quality checks.

**Proposed Tools:**
- Black (formatting)
- Ruff (linting)
- mypy (type checking)
- Bandit (security scanning)

**Acceptance Criteria:**
- [ ] Add `.pre-commit-config.yaml`
- [ ] Configure all tools
- [ ] Add to `CONTRIBUTING.md`
- [ ] Document setup in README

**Estimated Effort:** Small (0.5 day)

---

### Issue #25: Set up CI/CD pipelines
**Labels:** `P3`, `tooling`, `devops`

**Summary:**
Add GitHub Actions workflows for testing, linting, docs generation, and PyPI publishing.

**Proposed Workflows:**
- `.github/workflows/test.yml` - Run tests on PRs
- `.github/workflows/lint.yml` - Run linters
- `.github/workflows/docs.yml` - Build and deploy docs
- `.github/workflows/publish.yml` - Publish to PyPI on release

**Acceptance Criteria:**
- [ ] All workflows configured
- [ ] Badges added to README
- [ ] Publishing workflow tested
- [ ] Document release process

**Estimated Effort:** Medium (2 days)

---

### Issue #26: Create CHANGELOG
**Labels:** `P3`, `documentation`

**Summary:**
Maintain `CHANGELOG.md` tracking changes between versions following Keep a Changelog format.

**Acceptance Criteria:**
- [ ] Create `CHANGELOG.md`
- [ ] Document format (Keep a Changelog)
- [ ] Add to release checklist
- [ ] Automate with changelog generator

**Estimated Effort:** Small (0.5 day)
