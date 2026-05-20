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

        client = httpx.AsyncClient(timeout=self.timeout)
        response = await client.send(
            client.build_request("POST", self.upstream_url, json=request, headers=clean_headers),
            stream=True,
        )
        status_code = response.status_code
        content_type = response.headers.get("content-type", "application/octet-stream")

        async def generator():
            try:
                async for chunk in response.aiter_bytes():
                    yield chunk
            except Exception as e:
                warnings.warn(
                    f"Upstream request failed: {e}",
                    RuntimeWarning,
                    stacklevel=2,
                )
            finally:
                await response.aclose()
                await client.aclose()

        return StreamingResponse(
            generator(),
            status_code=status_code,
            media_type=content_type,
        )
