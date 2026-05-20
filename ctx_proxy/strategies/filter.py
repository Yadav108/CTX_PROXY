"""FilterStrategy — drops low-signal historical messages without calling any model."""

from typing import TYPE_CHECKING

from fastapi import Response

from ctx_proxy.session import Session, SessionManager
from ctx_proxy.strategies.base import Strategy
from ctx_proxy.strategies.compactor import _should_keep
from ctx_proxy.tokenizer import count_tokens_delta

if TYPE_CHECKING:
    from ctx_proxy.forwarder import Forwarder


class FilterStrategy(Strategy):
    def __init__(self, session_manager: SessionManager, forwarder: "Forwarder") -> None:
        self.session_manager = session_manager
        self.forwarder = forwarder

    async def handle(
        self, request: dict, session: Session, headers: dict | None = None
    ) -> Response:
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

        preserved = {current_idx}
        if system_msg is not None:
            preserved.add(0)
        if last_user_idx is not None:
            preserved.add(last_user_idx)
        if last_assistant_idx is not None:
            preserved.add(last_assistant_idx)

        new_messages: list[dict] = []
        for i, m in enumerate(messages):
            if i in preserved or _should_keep(m):
                new_messages.append(m)

        new_token_total = count_tokens_delta(new_messages, 0, 0)
        self.session_manager.update(
            session,
            token_estimate=new_token_total,
            message_count=len(new_messages),
        )

        rebuilt_request = {**request, "messages": new_messages}
        return await self.forwarder.forward(rebuilt_request, session, headers=headers)
