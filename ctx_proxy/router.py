"""CompactionRouter — inspects token counts and decides whether to passthrough or trigger compaction."""

from ctx_proxy.config import SOFT_LIMIT, HARD_LIMIT
from ctx_proxy.session import Session
from ctx_proxy.strategies.base import Strategy


class CompactionRouter:
    def __init__(self, passthrough: Strategy, compactor: Strategy) -> None:
        self._passthrough = passthrough
        self._compactor = compactor

    def select(self, session: Session) -> Strategy:
        """Select a strategy based on session utilization.
        
        Args:
            session: Session object with token utilization
            
        Returns:
            CompactorStrategy if utilization >= SOFT_LIMIT, otherwise PassthroughStrategy
        """
        if session.is_above(HARD_LIMIT) or session.is_above(SOFT_LIMIT):
            return self._compactor
        return self._passthrough
