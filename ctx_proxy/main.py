"""FastAPI application factory — instantiates the app and registers all route handlers."""

import os
import warnings

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

from ctx_proxy.forwarder import Forwarder
from ctx_proxy.handler import Handler
from ctx_proxy.model_client import ModelClient
from ctx_proxy.router import CompactionRouter
from ctx_proxy.session import SessionManager
from ctx_proxy.snapshot import SnapshotManager
from ctx_proxy.snapshot_loader import load_snapshot, load_snapshot_meta
from ctx_proxy.strategies.compactor import CompactorStrategy
from ctx_proxy.strategies.filter import FilterStrategy
from ctx_proxy.strategies.passthrough import PassthroughStrategy


def create_app() -> FastAPI:
    """Create FastAPI app and wire dependencies."""
    upstream_url = os.getenv("UPSTREAM_URL", "https://api.anthropic.com/v1/messages")
    api_key = os.getenv("API_KEY", "")
    resume_session_id = os.getenv("RESUME_SESSION_ID")

    resume_context: str | None = None
    if resume_session_id is not None:
        try:
            resume_context = load_snapshot(resume_session_id)
            if resume_context is None:
                warnings.warn(
                    "No snapshot content found for session, starting fresh.",
                    RuntimeWarning,
                )
        except FileNotFoundError as exc:
            warnings.warn(str(exc), RuntimeWarning)

    session_manager = SessionManager()
    if resume_context is not None:
        meta = load_snapshot_meta(resume_session_id)
        resumed_session = session_manager.get_or_create(
            [{"role": "system", "content": resume_context}],
            provider=meta.get("provider", "openai"),
            model=meta.get("model", "gpt-4o-mini"),
        )
        resumed_session.snapshot = resume_context
    forwarder = Forwarder(upstream_url)
    model_client = ModelClient(api_key=api_key, upstream_url=upstream_url)
    snapshot_manager = SnapshotManager()
    passthrough = PassthroughStrategy(session_manager=session_manager, forwarder=forwarder)
    filter_strategy = FilterStrategy(session_manager=session_manager, forwarder=forwarder)
    compactor = CompactorStrategy(
        session_manager=session_manager,
        forwarder=forwarder,
        model_client=model_client,
        snapshot_manager=snapshot_manager,
    )
    router = CompactionRouter(passthrough=passthrough, filter_strategy=filter_strategy, compactor=compactor)
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
