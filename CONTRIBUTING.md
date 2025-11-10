# Contributing to Kaizen SDKs

First off, thanks for considering a contribution! This repository unifies every Kaizen client and CLI, so a little structure keeps things friendly for everyone.

## Ground Rules

- Be excellent to each other. See the [Code of Conduct](CODE_OF_CONDUCT.md).
- Every change needs tests and docs that explain *why* the change exists.
- Keep the public API stable. If you need to ship a breaking change, open an RFC issue first.

## Getting Started

```bash
cd python
uv pip install -e .[all]
pytest
```

For SDKs written in other languages, check the language-specific `README` inside `python/`, `js/`, etc. (coming soon).

### Running Checks

- `pytest` – Unit and integration tests for Python packages.
- `ruff check` / `ruff format` – Coming soon for linting.
- `mypy` – Coming soon for type checking.

Please keep CI green locally before opening a PR.

## Development Flow

1. Fork the repo and create a topic branch: `feat/short-description`.
2. Commit small, reviewable changes with clear messages.
3. Run tests + linters.
4. Open a PR that links to an issue or discussion and fill in the template.
5. Expect a short review focusing on correctness, backwards compatibility, and documentation.

## Release Process

1. Update `CHANGELOG.md` (to be added) with user-facing notes.
2. Bump versions (per-language) following semver.
3. Tag releases as `vX.Y.Z`.
4. Publish packages to the appropriate registries (PyPI/NPM/etc.).

## Reporting Issues & Requesting Features

Use the templates under `.github/ISSUE_TEMPLATE`. Please include reproduction steps, observed vs expected behavior, and environment details.

## Security

If you discover a vulnerability, **do not** open a public issue. Email security@kaizen so we can coordinate a fix first.

Happy hacking! 🚀
