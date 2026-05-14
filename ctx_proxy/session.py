"""Session dataclass, SessionManager for per-conversation state, and CONTEXT_LIMITS mapping."""

from __future__ import annotations

import hashlib
import json
import warnings
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

CONTEXT_LIMITS: dict[str, int] = {
    "claude-opus-4-5":    200_000,
    "claude-sonnet-4-5":  200_000,
    "claude-haiku-4-5":   200_000,
    "gpt-4o":             128_000,
    "gpt-4o-mini":        128_000,
    "gemini-1.5-pro":   1_000_000,
    "gemini-1.5-flash": 1_000_000,
}

MODEL_ALIASES: dict[str, str] = {
    # Anthropic dated releases
    "claude-opus-4-5-20251101":   "claude-opus-4-5",
    "claude-sonnet-4-5-20251022": "claude-sonnet-4-5",
    "claude-haiku-4-5-20251001":  "claude-haiku-4-5",
    # OpenAI dated releases
    "gpt-4o-2024-05-13":      "gpt-4o",
    "gpt-4o-2024-08-06":      "gpt-4o",
    "gpt-4o-2024-11-20":      "gpt-4o",
    "gpt-4o-mini-2024-07-18": "gpt-4o-mini",
    # Google versioned / latest aliases
    "gemini-1.5-pro-latest":  "gemini-1.5-pro",
    "gemini-1.5-pro-001":     "gemini-1.5-pro",
    "gemini-1.5-pro-002":     "gemini-1.5-pro",
    "gemini-1.5-flash-latest": "gemini-1.5-flash",
    "gemini-1.5-flash-001":   "gemini-1.5-flash",
    "gemini-1.5-flash-002":   "gemini-1.5-flash",
}

_STORAGE_DIR = Path.home() / ".ctx-proxy" / "sessions"

_24H = 86_400
_7D  = 7 * _24H


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class Session:
    session_id:     str
    provider:       str
    model:          str
    token_limit:    int
    message_count:  int = 0
    token_estimate: int = 0
    snapshot:       Optional[str] = None
    persisted:      bool = False
    created_at:     datetime = field(default_factory=_utcnow)
    last_seen:      datetime = field(default_factory=_utcnow)

    def utilization(self) -> float:
        if self.token_limit == 0:
            return 0.0
        return self.token_estimate / self.token_limit

    def is_above(self, threshold: float) -> bool:
        return self.utilization() >= threshold


class SessionManager:
    def __init__(self) -> None:
        _STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        self._sessions: dict[str, Session] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_or_create(self, messages: list, provider: str, model: str) -> Session:
        canonical = MODEL_ALIASES.get(model, model)
        if canonical not in CONTEXT_LIMITS:
            warnings.warn(
                f"Unknown model '{model}' (resolved to '{canonical}'); "
                "token_limit set to 0.",
                stacklevel=2,
            )
        token_limit = CONTEXT_LIMITS.get(canonical, 0)
        session_id = self._compute_hash(messages, provider, model)

        if session_id in self._sessions:
            return self._sessions[session_id]

        on_disk = self._load_from_disk(session_id)
        if on_disk is not None:
            self._sessions[session_id] = on_disk
            return on_disk

        session = Session(
            session_id=session_id,
            provider=provider,
            model=canonical,
            token_limit=token_limit,
        )
        self._sessions[session_id] = session
        return session

    def update(
        self,
        session_or_id: Session | str,
        message_count: int | None = None,
        token_estimate: int | None = None,
        *,
        new_message_count: int | None = None,
        new_token_estimate: int | None = None,
    ) -> None:
        if isinstance(session_or_id, Session):
            session_id = session_or_id.session_id
        else:
            session_id = session_or_id
        next_message_count = (
            message_count if message_count is not None else new_message_count
        )
        next_token_estimate = (
            token_estimate if token_estimate is not None else new_token_estimate
        )
        if next_message_count is None or next_token_estimate is None:
            raise ValueError("Both message_count and token_estimate are required.")
        session = self._sessions[session_id]
        session.message_count = next_message_count
        session.token_estimate = next_token_estimate
        session.last_seen      = _utcnow()
        self._write_to_disk(session)

    def evict_stale(self) -> None:
        now = _utcnow()
        to_evict = [
            sid
            for sid, s in self._sessions.items()
            if (s.snapshot is None and (now - s.created_at).total_seconds() > _24H)
            or (now - s.created_at).total_seconds() > _7D
        ]
        for sid in to_evict:
            del self._sessions[sid]
            (_STORAGE_DIR / f"{sid}.json").unlink(missing_ok=True)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _compute_hash(self, messages: list, provider: str, model: str) -> str:
        def _content_at(index: int) -> str:
            if index >= len(messages):
                return ""
            message = messages[index]
            if isinstance(message, dict):
                return str(message.get("content") or "")
            return str(getattr(message, "content", "") or "")

        raw = (
            provider + "::" + model + "::"
            + _content_at(0) + "::"
            + _content_at(1)
        )
        return hashlib.sha256(raw.encode()).hexdigest()

    def _write_to_disk(self, session: Session) -> None:
        session.persisted = True
        data = asdict(session)
        data["created_at"] = session.created_at.isoformat()
        data["last_seen"]  = session.last_seen.isoformat()
        (_STORAGE_DIR / f"{session.session_id}.json").write_text(
            json.dumps(data, indent=2)
        )

    def _load_from_disk(self, session_id: str) -> Optional[Session]:
        path = _STORAGE_DIR / f"{session_id}.json"
        if not path.exists():
            return None
        data = json.loads(path.read_text())
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        data["last_seen"]  = datetime.fromisoformat(data["last_seen"])
        return Session(**data)
