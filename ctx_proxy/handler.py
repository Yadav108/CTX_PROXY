"""POST /v1/messages request handler — owns the full request lifecycle from receipt to streaming response."""

from fastapi import Response

from ctx_proxy.router import CompactionRouter
from ctx_proxy.session import SessionManager


class Handler:
    """Request orchestration pipeline over injected capabilities."""

    def __init__(self, router: CompactionRouter, session_manager: SessionManager) -> None:
        self.router = router
        self.session_manager = session_manager

    async def handle(self, request: dict, headers: dict) -> Response:
        self.session_manager.evict_stale_sessions()
        messages = request.get("messages", [])
        provider = request.get("provider", "openai")
        model = request.get("model", "gpt-4o")
        session = self.session_manager.get_or_create(messages, provider, model)
        strategy = self.router.select(session)
        return await strategy.handle(request, session, headers)
