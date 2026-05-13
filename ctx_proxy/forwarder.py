"""Async streaming forwarder — proxies requests to the real LLM API via httpx and streams responses back."""

import warnings
import httpx
from fastapi.responses import StreamingResponse
from ctx_proxy.session import Session

SAFE_HEADERS = {
    "authorization",
    "x-api-key",
    "content-type",
    "accept",
    "anthropic-version",
    "openai-beta",
}


class Forwarder:
    def __init__(self, upstream_url: str):
        """Initialize forwarder with upstream URL and timeout.
        
        Args:
            upstream_url: Full endpoint URL to forward requests to
        """
        self.upstream_url = upstream_url
        self.timeout = httpx.Timeout(60.0)

    async def forward(
        self, request: dict, session: Session, headers: dict = None
    ) -> StreamingResponse:
        clean_headers = {
            k: v for k, v in (headers or {}).items()
            if k.lower() in SAFE_HEADERS
        }
        if "authorization" in clean_headers and "x-api-key" not in clean_headers:
            token = clean_headers.pop("authorization").removeprefix("Bearer ").removeprefix("bearer ")
            clean_headers["x-api-key"] = token

        async def generator():
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    async with client.stream(
                        "POST", self.upstream_url, json=request, headers=clean_headers
                    ) as response:
                        async for chunk in response.aiter_bytes():
                            yield chunk
            except Exception as e:
                warnings.warn(
                    f"Upstream request failed: {e}",
                    RuntimeWarning,
                    stacklevel=2,
                )

        return StreamingResponse(
            generator(),
            media_type="application/octet-stream",
        )
