"""Load persisted .ctx snapshots and reconstruct session-resume context."""

from __future__ import annotations

import json
from pathlib import Path

_STORAGE_DIR = Path.home() / ".ctx-proxy" / "sessions"


def _resolve_ctx_path(session_id: str) -> Path:
    if session_id == "latest":
        ctx_files = sorted(
            _STORAGE_DIR.glob("*.ctx"),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
        if not ctx_files:
            raise FileNotFoundError(f"No .ctx snapshot files found in {_STORAGE_DIR}.")
        return ctx_files[0]

    path = _STORAGE_DIR / f"{session_id}.ctx"
    if not path.exists():
        raise FileNotFoundError(f"Snapshot file not found: {path}")
    return path


def load_snapshot(session_id: str) -> str | None:
    path = _resolve_ctx_path(session_id)
    data = json.loads(path.read_text(encoding="utf-8"))
    snapshot_content = data.get("snapshot")
    if not snapshot_content:
        return None
    return "Recovered session context:\n\n" + snapshot_content


def load_snapshot_meta(session_id: str) -> dict:
    path = _resolve_ctx_path(session_id)
    return json.loads(path.read_text(encoding="utf-8"))
