# Contributing to ctx-proxy

## Getting started

- Fork the repo
- Clone locally
- `pip install -e ".[dev]"`

## Development workflow

- One file, one job — keep modules focused
- All new code must have type hints
- Run ruff before committing: `ruff check .`
- Run tests: `pytest`

## Adding a new LLM provider

Providers are handled via the `UPSTREAM_URL` environment variable, so no code changes are needed for OpenAI-compatible APIs. For non-compatible APIs, add a new strategy in `ctx_proxy/strategies/`.

## Submitting a PR

- Keep PRs small and focused
- Describe what changed and why
- Reference any related issues
