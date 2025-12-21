from abc import ABC, abstractmethod
from typing import Any, Tuple, Optional

class AttackerStrategy(ABC):

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def choose_action(self, attacker, network_state) -> Optional[Tuple[Any, Any]]:
        pass

class DefenderStrategy(ABC):

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def choose_action(self, defender, network_state) -> Optional[Tuple[Any, Any]]:
        pass

    @abstractmethod
    def get_priority(self, action: Any, node: Any) -> float:
        pass