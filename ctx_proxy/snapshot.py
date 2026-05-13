"""Persistence layer — reads and writes .ctx snapshot files and exports human-readable markdown sidecars."""

from pathlib import Path
import json
import warnings

from ctx_proxy.session import Session


class SnapshotManager:
    def __init__(self, storage_dir: Path = Path.home() / ".ctx-proxy" / "sessions"):
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def save(self, session: Session) -> None:
        data = {
            "session_id": session.session_id,
            "provider": session.provider,
            "model": session.model,
            "token_estimate": session.token_estimate,
            "token_limit": session.token_limit,
            "utilization": round(session.utilization(), 4),
            "created_at": session.created_at.isoformat(),
            "last_seen": session.last_seen.isoformat(),
            "snapshot": session.snapshot,
        }
        ctx_path = self.storage_dir / f"{session.session_id}.ctx"
        try:
            ctx_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception as e:
            warnings.warn(f"failed to write snapshot ctx file: {e}", RuntimeWarning, stacklevel=2)
        self._write_md(session, data)

    def load(self, session_id: str) -> dict | None:
        path = self.storage_dir / f"{session_id}.ctx"
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            warnings.warn(f"failed to load snapshot ctx file: {e}", RuntimeWarning, stacklevel=2)
            return None

    def _write_md(self, session: Session, data: dict) -> None:
        md_path = self.storage_dir / f"{session.session_id}.md"
        snapshot_text = data["snapshot"] if data.get("snapshot") else "_No snapshot generated yet._"
        md = (
            "# Session Overview\n"
            f"- **Session ID:** {data['session_id']}\n"
            f"- **Provider:** {data['provider']}\n"
            f"- **Model:** {data['model']}\n\n"
            "# State Summary\n"
            f"- **Tokens used:** {data['token_estimate']} / {data['token_limit']}\n"
            f"- **Utilization:** {data['utilization'] * 100:.1f}%\n"
            f"- **Created:** {data['created_at']}\n"
            f"- **Last seen:** {data['last_seen']}\n\n"
            "# Context Snapshot\n"
            f"{snapshot_text}\n\n"
            "# Session Timeline\n"
            "_No events recorded yet._\n\n"
            "# Debug Metadata\n"
            "```json\n"
            f"{json.dumps(data, indent=2)}\n"
            "```\n"
        )
        try:
            md_path.write_text(md, encoding="utf-8")
        except Exception as e:
            warnings.warn(f"failed to write snapshot markdown file: {e}", RuntimeWarning, stacklevel=2)
