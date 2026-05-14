"""Typer-based CLI entry point exposing `ctx-proxy start` and `ctx-proxy clear` commands."""

import typer
import uvicorn

from ctx_proxy.session import SessionManager
from ctx_proxy.snapshot import SnapshotManager


app = typer.Typer(help="ctx-proxy command line interface")


@app.command("start")
def start(host: str = "127.0.0.1", port: int = 8000) -> None:
    """Start the ctx-proxy server."""
    uvicorn.run("ctx_proxy.main:app", host=host, port=port, reload=False)


@app.command("clear")
def clear() -> None:
    """Clear all saved sessions."""
    snapshot_manager = SnapshotManager()
    session_manager = SessionManager(snapshot_manager=snapshot_manager)
    evicted_sessions = session_manager.evict_stale_sessions()
    storage = snapshot_manager.storage_dir
    deleted_json_files = 0
    if storage.exists():
        for json_path in storage.glob("*.json"):
            if not (storage / f"{json_path.stem}.ctx").exists():
                json_path.unlink()
                deleted_json_files += 1
    typer.echo(
        f"Evicted {len(evicted_sessions)} sessions, deleted {deleted_json_files} .json files."
    )
