"""Abstract base Strategy class defining the interface all compaction strategies must implement."""

from abc import ABC, abstractmethod
from fastapi import Response
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ctx_proxy.session import Session


class Strategy(ABC):
    @abstractmethod
    async def handle(
        self, request: dict, session: "Session", headers: dict | None = None
    ) -> Response:
        """Handle a request with this strategy.
        
        Args:
            request: Request payload dict
            session: Session object with token counts and limits
            
        Returns:
            FastAPI Response object
        """
        ...
