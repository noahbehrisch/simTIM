import random
from typing import Any

from src.actors.strategies.base import AttackerStrategy
from src.core.access_levels import NodeAccessLevel


class RandomAttackerStrategy(AttackerStrategy):
    def __init__(self):
        super().__init__("random")

    def get_priority(self, action: Any, node: Any, access: NodeAccessLevel, attacker: Any) -> float:
        return random.random()
