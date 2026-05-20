"""CompactionRouter — inspects token counts and decides whether to passthrough, filter, or compact."""

from ctx_proxy.config import SOFT_LIMIT, HARD_LIMIT
from ctx_proxy.session import Session
from ctx_proxy.strategies.base import Strategy


class CompactionRouter:
    def __init__(self, passthrough: Strategy, filter_strategy: Strategy, compactor: Strategy) -> None:
        self._passthrough = passthrough
        self._filter_strategy = filter_strategy
        self._compactor = compactor

    def select(self, session: Session) -> Strategy:
        if session.is_above(HARD_LIMIT):
            return self._compactor
        if session.is_above(SOFT_LIMIT):
            return self._filter_strategy
        return self._passthrough
