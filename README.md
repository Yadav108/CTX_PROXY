# ctx-proxy

A local reverse proxy that sits between your code and LLM APIs, auto-compacting context before hitting token limits.

## What it does

- Intercepts LLM API calls transparently
- Tracks token usage per session
- Filters noisy history at 75% utilization (no model call)
- Compacts context via a summary model at 90% utilization
- Exports session snapshots as `.ctx` and `.md` files
- Works with Anthropic, OpenAI, and any OpenAI-compatible API

## Installation

```bash
pip install ctx-proxy
```

For development:

```bash
git clone https://github.com/Yadav108/CTX_PROXY.git
cd CTX_PROXY
pip install -e ".[dev]"
```

## Quick start

### 1. Set environment variables

**Windows (PowerShell):**
```powershell
$env:UPSTREAM_URL = "https://openrouter.ai/api/v1/chat/completions"
$env:API_KEY = "your-api-key-here"
```

**Linux/macOS:**
```bash
export UPSTREAM_URL="https://openrouter.ai/api/v1/chat/completions"
export API_KEY="your-api-key-here"
```

`UPSTREAM_URL` can point to any OpenAI-compatible endpoint (OpenRouter, OpenAI, Anthropic, Ollama, etc.)

### 2. Start the proxy

```bash
ctx-proxy start
```

Proxy runs at `http://localhost:8000`

### 3. Change one line in your code

Before:
```python
client = openai.OpenAI(api_key="your-key")
```

After:
```python
client = openai.OpenAI(base_url="http://localhost:8000", api_key="your-key")
```

That's it. ctx-proxy handles everything else transparently.

## CLI commands

```bash
ctx-proxy start                  # start the proxy on localhost:8000
ctx-proxy start --port 9000      # custom port
ctx-proxy start --resume latest  # resume the most recent session
ctx-proxy clear                  # evict stale sessions
```

## Environment variables

| Variable | Default | What it does |
|---|---|---|
| `UPSTREAM_URL` | `https://api.anthropic.com/v1/messages` | Upstream LLM API endpoint |
| `API_KEY` | _(empty)_ | API key forwarded upstream |
| `COMPACT_MODEL` | `gpt-4o-mini` | Model used for context compaction |
| `SOFT_LIMIT` | `0.75` | Utilization threshold for filter-only compaction |
| `HARD_LIMIT` | `0.90` | Utilization threshold for full model compaction |

## Session files

Session files live in `~/.ctx-proxy/sessions/`.

- `.ctx` — structured session snapshot (JSON)
- `.md` — human-readable snapshot sidecar
- `.json` — live session state used by the proxy

## License

MIT
````"
