# ctx-proxy

A local reverse proxy that sits between your code and LLM APIs, auto-compacting context before hitting token limits.

## What it does

- Intercepts LLM API calls transparently
- Tracks token usage per session
- Auto-compacts context when approaching limits (soft: 75%, hard: 90%)
- Exports session snapshots as .ctx + .md files
- Works with Anthropic, OpenAI, and any OpenAI-compatible API (e.g. OpenRouter)

## Installation

```bash
pip install ctx-proxy
pip install -e ".[dev]"
```

## Quick start

### 1. Install
pip install ctx-proxy

For development:
git clone https://github.com/Yadav108/CTX_PROXY.git
cd CTX_PROXY
pip install -e ".[dev]"

### 2. Set environment variables
Set these before starting the proxy:

Windows (PowerShell):
$env:UPSTREAM_URL = "https://openrouter.ai/api/v1/chat/completions"
$env:API_KEY = "your-api-key-here"

Linux/macOS:
export UPSTREAM_URL="https://openrouter.ai/api/v1/chat/completions"
export API_KEY="your-api-key-here"

UPSTREAM_URL can point to any OpenAI-compatible endpoint (OpenRouter, OpenAI, Anthropic, local models via Ollama, etc.)

### 3. Start the proxy
ctx-proxy start

Proxy runs at http://localhost:8000

### 4. Change one line in your code
Before:
client = openai.OpenAI(api_key="your-key")

After:
client = openai.OpenAI(base_url="http://localhost:8000", api_key="your-key")

That's it. ctx-proxy handles everything else transparently.

## CLI commands

- `ctx-proxy start`
- `ctx-proxy clear` (evicts stale sessions and removes orphaned `.json` files)

## Environment variables

| Variable | Default | What it does |
| --- | --- | --- |
| `UPSTREAM_URL` | `https://api.anthropic.com/v1/messages` | Upstream LLM API endpoint the proxy forwards to. |
| `API_KEY` | empty | API key used when forwarding requests upstream. |
| `COMPACT_MODEL` | `gpt-4o-mini` | Model used for context compaction. |

## Session files

Session files live in `~/.ctx-proxy/sessions/`.

- `.ctx` files store structured session snapshots.
- `.md` files store a human-readable snapshot alongside the `.ctx` file.
- `.json` files store session state used by the proxy.

## Contributing

See `CONTRIBUTING.md` (to be added).
