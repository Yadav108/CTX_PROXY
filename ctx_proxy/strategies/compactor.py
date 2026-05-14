"""CompactionStrategy — two-stage pipeline that compresses conversation history then rebuilds a minimal context window."""

from typing import TYPE_CHECKING

from fastapi import Response

from ctx_proxy.config import COMPACT_MODEL
from ctx_proxy.model_client import ModelClient
from ctx_proxy.session import Session, SessionManager
from ctx_proxy.strategies.base import Strategy
from ctx_proxy.tokenizer import count_tokens_delta

if TYPE_CHECKING:
    from ctx_proxy.forwarder import Forwarder

KEEP_KEYWORDS = {"decided", "fixed", "error", "architecture", "todo", "breaking"}

COMPACTION_PROMPT = """You are a context compactor. Summarize the conversation into a structured snapshot.
Output format:
DECISIONS: <key decisions made>
STATE: <current working state>
OPEN_THREADS: <unresolved questions>
CODE_ARTIFACTS: <important code produced>
BUGS_RESOLVED: <bugs fixed>
Be concise. Preserve technical specifics."""


class CompactorStrategy(Strategy):
    def __init__(
        self,
        session_manager: SessionManager,
        forwarder: "Forwarder",
        model_client: ModelClient,
    ) -> None:
        self.session_manager = session_manager
        self.forwarder = forwarder
        self.model_client = model_client

    async def handle(
        self, request: dict, session: Session, headers: dict | None = None
    ) -> Response:
        """Compact historical context, rebuild message list, then forward."""
        messages = request.get("messages", [])
        if not messages:
            return await self.forwarder.forward(request, session, headers=headers)

        system_msg = messages[0] if messages[0].get("role") == "system" else None
        current_idx = len(messages) - 1
        current_msg = messages[current_idx]
        last_user_idx = next(
            (i for i in range(len(messages) - 2, -1, -1) if messages[i].get("role") == "user"),
            None,
        )
        last_assistant_idx = next(
            (i for i in range(len(messages) - 2, -1, -1) if messages[i].get("role") == "assistant"),
            None,
        )
        last_user = messages[last_user_idx] if last_user_idx is not None else None
        last_assistant = messages[last_assistant_idx] if last_assistant_idx is not None else None

        excluded = {current_idx}
        if system_msg is not None:
            excluded.add(0)
        if last_user_idx is not None:
            excluded.add(last_user_idx)
        if last_assistant_idx is not None:
            excluded.add(last_assistant_idx)
        candidates = [m for i, m in enumerate(messages) if i not in excluded]
        filtered = [m for m in candidates if _should_keep(m)]

        snapshot_text = await self.model_client.complete(
            messages=[
                {
                    "role": "user",
                    "content": COMPACTION_PROMPT + "\n\n" + _format_for_summary(filtered),
                }
            ],
            model=COMPACT_MODEL,
        )
        if snapshot_text == "":
            return await self.forwarder.forward(request, session, headers=headers)

        new_messages: list[dict] = []
        if system_msg is not None:
            new_messages.append(system_msg)
        new_messages.append({"role": "system", "content": f"CONTEXT SNAPSHOT:\n{snapshot_text}"})
        if last_assistant is not None:
            new_messages.append(last_assistant)
        if last_user is not None:
            new_messages.append(last_user)
        new_messages.append(current_msg)

        rebuilt_request = {**request, "messages": new_messages}
        new_token_total = count_tokens_delta(new_messages, 0, 0)
        self.session_manager.update(
            session,
            token_estimate=new_token_total,
            message_count=len(new_messages),
        )
        return await self.forwarder.forward(rebuilt_request, session, headers=headers)


def _should_keep(message: dict) -> bool:
    content = str(message.get("content") or "")
    if len(content.strip()) < 20:
        return False
    lowered = content.lower()
    if "```" in content:
        return True
    return any(keyword in lowered for keyword in KEEP_KEYWORDS)


def _format_for_summary(messages: list[dict]) -> str:
    if not messages:
        return "No retained historical context."
    return "\n".join(
        f"{(m.get('role') or 'unknown').upper()}: {str(m.get('content') or '').strip()}"
        for m in messages
    )
