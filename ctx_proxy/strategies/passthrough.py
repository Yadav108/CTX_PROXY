"""PassthroughStrategy — forwards the message list to the LLM unchanged, with no compaction."""

from fastapi import Response
from ctx_proxy.strategies.base import Strategy
from ctx_proxy.session import Session, SessionManager
from ctx_proxy.tokenizer import count_tokens_delta


class PassthroughStrategy(Strategy):
    def __init__(self, session_manager: SessionManager, forwarder: "Forwarder"):
        """Initialize passthrough strategy with dependencies.
        
        Args:
            session_manager: SessionManager for updating session token counts
            forwarder: Forwarder for proxying requests to the LLM API
        """
        self.session_manager = session_manager
        self.forwarder = forwarder

    async def handle(
        self, request: dict, session: Session, headers: dict | None = None
    ) -> Response:
        """Handle request with passthrough strategy.
        
        Extract messages, update token accounting, and forward unchanged.
        
        Args:
            request: Request payload dict
            session: Session object with token counts and limits
            
        Returns:
            StreamingResponse from forwarder
        """
        messages = request.get("messages", [])
        
        try:
            new_token_total = count_tokens_delta(
                messages,
                prev_token_total=session.token_estimate,
                prev_msg_count=session.message_count,
            )
        except Exception:
            new_token_total = session.token_estimate
        
        self.session_manager.update(
            session.session_id,
            new_message_count=len(messages),
            new_token_estimate=new_token_total,
        )
        
        return await self.forwarder.forward(request, session, headers=headers)
