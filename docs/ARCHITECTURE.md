# Kaizen SDKs Architecture

This repository is a mono-repo that houses every officially supported Kaizen client and CLI. The current structure keeps the Python SDK self-contained inside `python/` while leaving room for additional languages.

```
kaizen-sdks/
├── python/
│   ├── kaizen_client/          # Runtime package (async client, integrations, models)
│   ├── examples/               # Provider walkthroughs and benchmarking utilities
│   ├── tests/                  # Unit tests executed by CI
│   ├── pyproject.toml          # Packaging + dependency metadata
│   └── README.md               # Python-specific quickstart + API table
├── docs/                       # Specs, proposal docs, design records
├── openapi.json                # Canonical HTTP schema consumed by every SDK
├── CODE_OF_CONDUCT.md          # Community guidelines
├── CONTRIBUTING.md             # Contribution workflow + release notes
└── LICENSE                     # Repository-wide license
```

Upcoming SDKs (JavaScript/TypeScript, Go, CLI) will introduce sibling directories (`js/`, `go/`, `cli/`, etc.) that follow the same pattern: language-specific README + build files + tests + examples. Shared fixtures or schemas will live under `shared/` once introduced.

## Guiding Principles

1. **Single source of truth** – The OpenAPI spec (`openapi.json`) and shared schemas live once and are consumed by every SDK.
2. **Language autonomy** – Each SDK manages its own toolchain (pip, npm, go modules) but follows the same contribution and release playbook.
3. **Contract tests** – Cross-language tests (to be added under `shared/`) ensure every SDK encodes/decodes prompts in the same way.
4. **Provider adapters** – Integrations (OpenAI, Anthropic, Gemini, etc.) should expose consistent ergonomics regardless of language. New adapters should live alongside the core client in each language directory.

## Roadmap Snapshot

- [x] Typed Python client, decorators, integrations, and tests under `python/`
- [ ] Generate strongly typed clients from `openapi.json`
- [ ] Introduce contract-test fixtures in `shared/`
- [ ] Spin up JS/TS and Go SDK folders mirroring the Python layout
- [ ] Ship CLI package powered by the shared HTTP core

Have ideas? Open an RFC issue using the feature-request template.
