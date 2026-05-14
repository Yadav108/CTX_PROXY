# ctx-proxy

A local reverse proxy that sits between your code and LLM APIs, auto-compacting context before hitting token limits.

## What it does

- Intercepts LLM API calls transparently
- Tracks token usage per session
- Auto-compacts context when approaching limits (soft: 75%, hard: 85%)
- Exports session snapshots as .ctx + .md files
- Works with Anthropic, OpenAI, and any OpenAI-compatible API (e.g. OpenRouter)

## Installation

```bash
pip install ctx-proxy
pip install -e ".[dev]"
```

## Quick start

```bash
export UPSTREAM_URL="https://api.openai.com"
export API_KEY="your-api-key"
ctx-proxy start
```

In your code, change one line:

```python
base_url = "http://localhost:8000"
```

## CLI commands

- `ctx-proxy start`
- `ctx-proxy clear`

## Environment variables

| Variable | Default | What it does |
| --- | --- | --- |
| `UPSTREAM_URL` | `https://api.openai.com` | Upstream LLM API endpoint the proxy forwards to. |
| `API_KEY` | empty | API key used when forwarding requests upstream. |
| `COMPACT_MODEL` | unset | Model used for context compaction when set. |

## Session files

Session files live in `~/.ctx-proxy/sessions/`.

- `.ctx` files store structured session snapshots.
- `.md` files store a human-readable snapshot alongside the `.ctx` file.
- `.json` files store session state used by the proxy.

## Contributing

See `CONTRIBUTING.md` (to be added).
