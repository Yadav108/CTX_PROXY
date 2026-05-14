"""Typer-based CLI entry point exposing `ctx-proxy start` and `ctx-proxy clear` commands."""

import os

import typer
import uvicorn


app = typer.Typer(help="ctx-proxy command line interface")


@app.command("start")
def start(
    host: str = "127.0.0.1",
    port: int = 8000,
    resume: str | None = typer.Option(
        None,
        "--resume",
        help="Resume a previous session by ID, or 'latest' for the most recent snapshot",
    ),
) -> None:
    """Start the ctx-proxy server."""
    if resume is not None:
        os.environ["RESUME_SESSION_ID"] = resume
    uvicorn.run("ctx_proxy.main:app", host=host, port=port, reload=False)


@app.command("clear")
def clear() -> None:
    """Clear all saved sessions."""
    import shutil
    from pathlib import Path

    storage = Path.home() / ".ctx-proxy" / "sessions"
    if storage.exists():
        shutil.rmtree(storage)
        typer.echo(f"Cleared {storage}")
    else:
        typer.echo("Nothing to clear.")
