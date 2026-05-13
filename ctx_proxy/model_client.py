"""Thin non-streaming LLM client for internal compaction calls."""

import warnings

import httpx


class ModelClient:
    def __init__(self, api_key: str, upstream_url: str, timeout: float = 30.0):
        self.api_key = api_key
        self.upstream_url = upstream_url
        self.timeout = timeout

    async def complete(self, messages: list[dict], model: str) -> str:
        """Send a non-streaming completion request and return extracted text."""
        payload = {
            "model": model,
            "max_tokens": 1024,
            "messages": messages,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.upstream_url,
                    json=payload,
                    headers=headers,
                )
            data = response.json()
            content = data.get("content")
            if isinstance(content, list) and content:
                text = content[0].get("text")
                if isinstance(text, str):
                    return text
            choices = data.get("choices")
            if isinstance(choices, list) and choices:
                message = choices[0].get("message", {})
                text = message.get("content")
                if isinstance(text, str):
                    return text
        except Exception as e:
            warnings.warn(f"model completion failed: {e}", RuntimeWarning, stacklevel=2)
            return ""
        return ""
