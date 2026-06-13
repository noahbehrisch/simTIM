import logging
import os
from collections.abc import Mapping
from typing import Any

from src.actors.strategies.base import AttackerStrategy, DefenderStrategy
from src.utils.discovery import discover_subclasses

logger = logging.getLogger(__name__)


class StrategyError(Exception):
    pass


class StrategyRegistry:
    def __init__(self):
        self._attacker_strategies: dict[str, type[AttackerStrategy]] = {}
        self._defender_strategies: dict[str, type[DefenderStrategy]] = {}

        strategies_dir = os.path.dirname(os.path.abspath(__file__))

        attacker_dir = os.path.join(strategies_dir, "attackers")
        for name, cls, _params in discover_subclasses(
            attacker_dir, "src.actors.strategies.attackers", AttackerStrategy
        ):
            self.register_attacker_strategy(name, cls)

        defender_dir = os.path.join(strategies_dir, "defenders")
        for name, cls, _params in discover_subclasses(
            defender_dir, "src.actors.strategies.defenders", DefenderStrategy
        ):
            self.register_defender_strategy(name, cls)

    def register_attacker_strategy(
        self,
        name: str,
        strategy_class: type[AttackerStrategy],
    ) -> None:
        if not issubclass(strategy_class, AttackerStrategy):
            raise TypeError(
                f"Strategy class must inherit from AttackerStrategy, got {strategy_class}"
            )

        self._attacker_strategies[name.lower()] = strategy_class
        logger.debug(f"Registered attacker strategy: {name}")

    def unregister_attacker_strategy(self, name: str) -> bool:
        name_lower = name.lower()
        if name_lower in self._attacker_strategies:
            del self._attacker_strategies[name_lower]
            return True
        return False

    def get_attacker_strategies(self) -> list[str]:
        return list(self._attacker_strategies.keys())

    def get_attacker_strategy_class(self, name: str) -> type[AttackerStrategy] | None:
        return self._attacker_strategies.get(name.lower())

    def create_attacker_strategy(
        self,
        name: str,
        **kwargs: Any,
    ) -> AttackerStrategy:
        name_lower = name.lower()

        if name_lower not in self._attacker_strategies:
            available = ", ".join(self.get_attacker_strategies())
            raise StrategyError(f"Unknown attacker strategy: '{name}'. Available: {available}")

        strategy_class = self._attacker_strategies[name_lower]
        try:
            strategy = strategy_class(**kwargs) if kwargs else strategy_class()  # type: ignore[call-arg]
            logger.debug(f"Created attacker strategy: {name}")
            return strategy
        except Exception as e:
            raise StrategyError(f"Failed to create attacker strategy '{name}': {e}") from e

    def register_defender_strategy(
        self,
        name: str,
        strategy_class: type[DefenderStrategy],
    ) -> None:
        if not issubclass(strategy_class, DefenderStrategy):
            raise TypeError(
                f"Strategy class must inherit from DefenderStrategy, got {strategy_class}"
            )

        self._defender_strategies[name.lower()] = strategy_class
        logger.debug(f"Registered defender strategy: {name}")

    def unregister_defender_strategy(self, name: str) -> bool:
        name_lower = name.lower()
        if name_lower in self._defender_strategies:
            del self._defender_strategies[name_lower]
            return True
        return False

    def get_defender_strategies(self) -> list[str]:
        return list(self._defender_strategies.keys())

    def get_defender_strategy_class(self, name: str) -> type[DefenderStrategy] | None:
        return self._defender_strategies.get(name.lower())

    def create_defender_strategy(
        self,
        name: str,
        **kwargs: Any,
    ) -> DefenderStrategy:
        name_lower = name.lower()

        if name_lower not in self._defender_strategies:
            available = ", ".join(self.get_defender_strategies())
            raise StrategyError(f"Unknown defender strategy: '{name}'. Available: {available}")

        strategy_class = self._defender_strategies[name_lower]
        try:
            strategy = strategy_class(**kwargs) if kwargs else strategy_class()  # type: ignore[call-arg]
            logger.debug(f"Created defender strategy: {name}")
            return strategy
        except Exception as e:
            raise StrategyError(f"Failed to create defender strategy '{name}': {e}") from e

    def get_strategy_info(self, name: str, role: str = "attacker") -> dict[str, Any] | None:
        name_lower = name.lower()
        strategies: Mapping[str, type[AttackerStrategy] | type[DefenderStrategy]]
        if role == "attacker":
            strategies = self._attacker_strategies
        else:
            strategies = self._defender_strategies

        if name_lower not in strategies:
            return None

        strategy_class = strategies[name_lower]
        return {
            "name": name_lower,
            "role": role,
            "class": strategy_class.__name__,
            "module": strategy_class.__module__,
            "docstring": strategy_class.__doc__,
        }


_registry = StrategyRegistry()


def get_strategy_registry() -> StrategyRegistry:
    return _registry


def get_attacker_strategy(name: str) -> AttackerStrategy:
    try:
        return _registry.create_attacker_strategy(name)
    except StrategyError:
        logger.warning(f"Unknown attacker strategy '{name}', using 'greedy'")
        return _registry.create_attacker_strategy("greedy")


def get_defender_strategy(name: str) -> DefenderStrategy:
    try:
        return _registry.create_defender_strategy(name)
    except StrategyError:
        logger.warning(f"Unknown defender strategy '{name}', using 'reactive'")
        return _registry.create_defender_strategy("reactive")


def list_attacker_strategies() -> list[str]:
    return _registry.get_attacker_strategies()


def list_defender_strategies() -> list[str]:
    return _registry.get_defender_strategies()
