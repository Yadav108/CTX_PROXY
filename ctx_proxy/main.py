"""FastAPI application factory — instantiates the app and registers all route handlers."""

import os

from ctx_proxy.config import UPSTREAM_URL as DEFAULT_UPSTREAM_URL

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

from ctx_proxy.forwarder import Forwarder
from ctx_proxy.handler import Handler
from ctx_proxy.model_client import ModelClient
from ctx_proxy.router import CompactionRouter
from ctx_proxy.session import SessionManager
from ctx_proxy.snapshot import SnapshotManager
from ctx_proxy.strategies.compactor import CompactorStrategy
from ctx_proxy.strategies.passthrough import PassthroughStrategy


def create_app() -> FastAPI:
    """Create FastAPI app and wire dependencies."""
    upstream_url = os.getenv("UPSTREAM_URL", DEFAULT_UPSTREAM_URL)
    api_key = os.getenv("API_KEY", "")

    snapshot_manager = SnapshotManager()
    session_manager = SessionManager(snapshot_manager=snapshot_manager)
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

    @app.post("/chat/completions")
    async def chat_completions_endpoint(request: Request) -> Response:
        try:
            payload = await request.json()
        except Exception:
            return JSONResponse({"error": "Invalid JSON body"}, status_code=400)
        headers = dict(request.headers)
        return await handler.handle(payload, headers)

    return app


app = create_app()
