# Kaizen SDKs Architecture

This repository is a mono-repo that houses every officially supported Kaizen client and CLI. The structure is intentionally simple:

```
kaizen-sdks/
├── python/            # Future home for Python packages (current code lives in kaizen_client/)
├── js/                # Placeholder for the JavaScript/TypeScript SDK
├── go/                # Placeholder for the Go SDK
├── cli/               # Cross-language CLI utilities
├── shared/            # JSON schema, protocol docs, fixtures
└── docs/              # Specs, proposal docs, decision records
```

## Guiding Principles

1. **Single source of truth** – The OpenAPI spec (`openapi.json`) and shared schemas live once and are consumed by every SDK.
2. **Language autonomy** – Each SDK manages its own toolchain (pip, npm, go modules) but follows the same contribution and release playbook.
3. **Contract tests** – Cross-language tests ensure every SDK encodes/decodes prompts in the same way.
4. **Provider adapters** – Integrations (OpenAI, Anthropic, Gemini, etc.) should expose the same decorator-based ergonomics regardless of language.

## Roadmap Snapshot

- [x] Typed Python client, decorators, and tests
- [ ] Move Python sources under `python/` with per-package READMEs
- [ ] Generate strongly typed clients from `openapi.json`
- [ ] Introduce contract-test fixtures in `shared/`
- [ ] Spin up JS/TS and Go SDK folders
- [ ] Ship CLI package powered by the Python core

Have ideas? Open an RFC issue using the feature-request template.
