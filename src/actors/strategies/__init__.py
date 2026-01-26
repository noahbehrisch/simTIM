"""
Strategy module.

Provides actor strategies for decision making during simulation.

Main Classes:
- AttackerStrategy: Abstract base class for attacker strategies
- DefenderStrategy: Abstract base class for defender strategies
- StrategyRegistry: Registry for strategy types

Attacker Strategies:
- GreedyAttackerStrategy: Prioritizes highest-value targets
- RandomAttackerStrategy: Random target selection
- EscalationAttackerStrategy: Follows MITRE ATT&CK progression

Defender Strategies:
- ReactiveDefenderStrategy: Responds to detected threats
- ProactiveDefenderStrategy: Anticipates and prevents attacks
- MonitoringDefenderStrategy: Focuses on detection
- BalancedDefenderStrategy: Combination approach

Convenience Functions:
- get_attacker_strategy(): Create attacker strategy by name
- get_defender_strategy(): Create defender strategy by name
- list_attacker_strategies(): List available attacker strategies
- list_defender_strategies(): List available defender strategies
"""

from .attackers.escalation import EscalationAttackerStrategy
from .attackers.greedy import GreedyAttackerStrategy
from .attackers.random import RandomAttackerStrategy
from .base import AttackerStrategy, DefenderStrategy
from .defenders.balanced import BalancedDefenderStrategy
from .defenders.monitoring import MonitoringDefenderStrategy
from .defenders.proactive import ProactiveDefenderStrategy
from .defenders.reactive import ReactiveDefenderStrategy
from .registry import (
    StrategyError,
    StrategyRegistry,
    get_attacker_strategy,
    get_defender_strategy,
    get_strategy_registry,
    list_attacker_strategies,
    list_defender_strategies,
)

__all__ = [
    # Base classes
    "AttackerStrategy",
    "DefenderStrategy",
    # Attacker implementations
    "GreedyAttackerStrategy",
    "RandomAttackerStrategy",
    "EscalationAttackerStrategy",
    # Defender implementations
    "ReactiveDefenderStrategy",
    "ProactiveDefenderStrategy",
    "MonitoringDefenderStrategy",
    "BalancedDefenderStrategy",
    # Registry
    "StrategyRegistry",
    "StrategyError",
    "get_strategy_registry",
    # Convenience functions
    "get_attacker_strategy",
    "get_defender_strategy",
    "list_attacker_strategies",
    "list_defender_strategies",
]
