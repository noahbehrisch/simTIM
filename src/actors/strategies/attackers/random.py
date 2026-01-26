import random
from typing import Any

from src.actors.strategies.base import AttackerStrategy


class RandomAttackerStrategy(AttackerStrategy):
    def __init__(self):
        super().__init__("random")

    def get_priority(self, action: Any, node: Any, access: Any, attacker: Any) -> float:
        return random.random()
