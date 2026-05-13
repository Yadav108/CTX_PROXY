"""Global configuration — SOFT_LIMIT, HARD_LIMIT, STORAGE_DIR, default port, and environment variable overrides."""

import os

SOFT_LIMIT = float(os.getenv("SOFT_LIMIT", "0.75"))
HARD_LIMIT = float(os.getenv("HARD_LIMIT", "0.90"))
COMPACT_MODEL = os.getenv("COMPACT_MODEL", "gpt-4o-mini")
