"""
Strategy registry module.

Provides a registry for actor strategies with factory methods.
"""

import logging
from typing import Any

from src.actors.strategies.attackers.escalation import EscalationAttackerStrategy
from src.actors.strategies.attackers.greedy import GreedyAttackerStrategy
from src.actors.strategies.attackers.random import RandomAttackerStrategy
from src.actors.strategies.base import AttackerStrategy, DefenderStrategy
from src.actors.strategies.defenders.balanced import BalancedDefenderStrategy
from src.actors.strategies.defenders.monitoring import MonitoringDefenderStrategy
from src.actors.strategies.defenders.proactive import ProactiveDefenderStrategy
from src.actors.strategies.defenders.reactive import ReactiveDefenderStrategy

logger = logging.getLogger(__name__)


class StrategyError(Exception):
    """Raised when strategy creation or lookup fails."""

    pass


class StrategyRegistry:
    """
    Registry for actor strategies.

    Provides registration and creation of strategies by type name.
    Supports both attacker and defender strategies.

    Built-in attacker strategies:
    - "greedy": Prioritizes highest-value targets
    - "random": Random target selection
    - "escalation": Follows MITRE ATT&CK tactics progression

    Built-in defender strategies:
    - "reactive": Responds to detected threats
    - "proactive": Anticipates and prevents attacks
    - "monitoring": Focuses on detection and visibility
    - "balanced": Combination of reactive and proactive
    """

    # Default strategy configurations
    DEFAULT_ATTACKER_STRATEGIES: dict[str, type[AttackerStrategy]] = {
        "greedy": GreedyAttackerStrategy,
        "random": RandomAttackerStrategy,
        "escalation": EscalationAttackerStrategy,
    }

    DEFAULT_DEFENDER_STRATEGIES: dict[str, type[DefenderStrategy]] = {
        "reactive": ReactiveDefenderStrategy,
        "proactive": ProactiveDefenderStrategy,
        "monitoring": MonitoringDefenderStrategy,
        "balanced": BalancedDefenderStrategy,
    }

    def __init__(self):
        """Initialize the registry with built-in strategies."""
        self._attacker_strategies: dict[str, type[AttackerStrategy]] = {}
        self._defender_strategies: dict[str, type[DefenderStrategy]] = {}

        # Register built-in strategies
        for name, cls in self.DEFAULT_ATTACKER_STRATEGIES.items():
            self.register_attacker_strategy(name, cls)

        for name, cls in self.DEFAULT_DEFENDER_STRATEGIES.items():
            self.register_defender_strategy(name, cls)

    # =========================================================================
    # Attacker Strategy Registration
    # =========================================================================

    def register_attacker_strategy(
        self,
        name: str,
        strategy_class: type[AttackerStrategy],
    ) -> None:
        """
        Register an attacker strategy type.

        Args:
            name: Name to register under (e.g., "greedy", "random")
            strategy_class: Strategy class (must inherit AttackerStrategy)
        """
        if not issubclass(strategy_class, AttackerStrategy):
            raise TypeError(
                f"Strategy class must inherit from AttackerStrategy, got {strategy_class}"
            )

        self._attacker_strategies[name.lower()] = strategy_class
        logger.debug(f"Registered attacker strategy: {name}")

    def unregister_attacker_strategy(self, name: str) -> bool:
        """Unregister an attacker strategy."""
        name_lower = name.lower()
        if name_lower in self._attacker_strategies:
            del self._attacker_strategies[name_lower]
            return True
        return False

    def get_attacker_strategies(self) -> list[str]:
        """Get list of available attacker strategy names."""
        return list(self._attacker_strategies.keys())

    def get_attacker_strategy_class(self, name: str) -> type[AttackerStrategy] | None:
        """Get attacker strategy class by name."""
        return self._attacker_strategies.get(name.lower())

    def create_attacker_strategy(
        self,
        name: str,
        **kwargs: Any,
    ) -> AttackerStrategy:
        """
        Create an attacker strategy instance.

        Args:
            name: Strategy type name
            **kwargs: Additional parameters for the strategy

        Returns:
            Configured strategy instance

        Raises:
            StrategyError: If strategy type not found
        """
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

    # =========================================================================
    # Defender Strategy Registration
    # =========================================================================

    def register_defender_strategy(
        self,
        name: str,
        strategy_class: type[DefenderStrategy],
    ) -> None:
        """
        Register a defender strategy type.

        Args:
            name: Name to register under (e.g., "reactive", "proactive")
            strategy_class: Strategy class (must inherit DefenderStrategy)
        """
        if not issubclass(strategy_class, DefenderStrategy):
            raise TypeError(
                f"Strategy class must inherit from DefenderStrategy, got {strategy_class}"
            )

        self._defender_strategies[name.lower()] = strategy_class
        logger.debug(f"Registered defender strategy: {name}")

    def unregister_defender_strategy(self, name: str) -> bool:
        """Unregister a defender strategy."""
        name_lower = name.lower()
        if name_lower in self._defender_strategies:
            del self._defender_strategies[name_lower]
            return True
        return False

    def get_defender_strategies(self) -> list[str]:
        """Get list of available defender strategy names."""
        return list(self._defender_strategies.keys())

    def get_defender_strategy_class(self, name: str) -> type[DefenderStrategy] | None:
        """Get defender strategy class by name."""
        return self._defender_strategies.get(name.lower())

    def create_defender_strategy(
        self,
        name: str,
        **kwargs: Any,
    ) -> DefenderStrategy:
        """
        Create a defender strategy instance.

        Args:
            name: Strategy type name
            **kwargs: Additional parameters for the strategy

        Returns:
            Configured strategy instance

        Raises:
            StrategyError: If strategy type not found
        """
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

    # =========================================================================
    # Generic methods
    # =========================================================================

    def get_strategy_info(self, name: str, role: str = "attacker") -> dict[str, Any] | None:
        """
        Get information about a strategy type.

        Args:
            name: Strategy type name
            role: "attacker" or "defender"

        Returns:
            Dictionary with strategy info or None if not found
        """
        name_lower = name.lower()
        strategies: dict[str, type[AttackerStrategy] | type[DefenderStrategy]]
        if role == "attacker":
            strategies = self._attacker_strategies  # type: ignore[assignment]
        else:
            strategies = self._defender_strategies  # type: ignore[assignment]

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


# =============================================================================
# Global instance and convenience functions
# =============================================================================

_registry = StrategyRegistry()


def get_strategy_registry() -> StrategyRegistry:
    """Get the global strategy registry."""
    return _registry


def get_attacker_strategy(name: str) -> AttackerStrategy:
    """
    Get an attacker strategy by name.

    Falls back to greedy if not found.
    """
    try:
        return _registry.create_attacker_strategy(name)
    except StrategyError:
        logger.warning(f"Unknown attacker strategy '{name}', using 'greedy'")
        return _registry.create_attacker_strategy("greedy")


def get_defender_strategy(name: str) -> DefenderStrategy:
    """
    Get a defender strategy by name.

    Falls back to reactive if not found.
    """
    try:
        return _registry.create_defender_strategy(name)
    except StrategyError:
        logger.warning(f"Unknown defender strategy '{name}', using 'reactive'")
        return _registry.create_defender_strategy("reactive")


def list_attacker_strategies() -> list[str]:
    """List available attacker strategy names."""
    return _registry.get_attacker_strategies()


def list_defender_strategies() -> list[str]:
    """List available defender strategy names."""
    return _registry.get_defender_strategies()
