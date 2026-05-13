"""FastAPI application factory — instantiates the app and registers all route handlers."""

import os

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

from ctx_proxy.forwarder import Forwarder
from ctx_proxy.handler import Handler
from ctx_proxy.model_client import ModelClient
from ctx_proxy.router import CompactionRouter
from ctx_proxy.session import SessionManager
from ctx_proxy.strategies.compactor import CompactorStrategy
from ctx_proxy.strategies.passthrough import PassthroughStrategy


def create_app() -> FastAPI:
    """Create FastAPI app and wire dependencies."""
    upstream_url = os.getenv("UPSTREAM_URL", "https://api.anthropic.com/v1/messages")
    api_key = os.getenv("API_KEY", "")

    session_manager = SessionManager()
    forwarder = Forwarder(upstream_url)
    model_client = ModelClient(api_key=api_key, upstream_url=upstream_url)
    passthrough = PassthroughStrategy(session_manager=session_manager, forwarder=forwarder)
    compactor = CompactorStrategy(
        session_manager=session_manager,
        forwarder=forwarder,
        model_client=model_client,
    )
    router = CompactionRouter(passthrough=passthrough, compactor=compactor)
    handler = Handler(router=router, session_manager=session_manager)

    app = FastAPI()

    @app.post("/v1/messages")
    async def messages_endpoint(request: Request) -> Response:
        try:
            payload = await request.json()
        except Exception:
            return JSONResponse({"error": "Invalid JSON body"}, status_code=400)
        headers = dict(request.headers)
        return await handler.handle(payload, headers)

    return app


app = create_app()
