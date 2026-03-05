import random
from typing import Any

from src.actors.strategies.base import AttackerStrategy
from src.core.access_levels import NodeAccessLevel


class RandomAttackerStrategy(AttackerStrategy):
    def __init__(self):
        super().__init__("random")

    def get_priority(self, action: Any, node: Any, access: NodeAccessLevel, attacker: Any) -> float:
        return random.random()

    def get_minimum_threshold(self, ongoing_count: int) -> float:
        """Random strategy hard-caps at 3 concurrent actions since
        action selection has no strategic basis for prioritization."""
        if ongoing_count >= 3:
            return float("inf")
        return 0.0
