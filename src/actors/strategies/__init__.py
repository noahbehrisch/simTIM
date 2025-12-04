"""
Strategy Components for simTIM Actors

This module provides strategy components to extract decision-making logic from actor classes.
Each strategy focuses on a specific decision-making approach.
"""

# Import base classes from base.py (single source of truth)
from .base import AttackerStrategy, DefenderStrategy

# Import all strategies for easy access
from .attackers.greedy import GreedyAttackerStrategy
from .attackers.random import RandomAttackerStrategy
from .defenders.reactive import ReactiveDefenderStrategy
from .defenders.proactive import ProactiveDefenderStrategy
from .defenders.monitoring import MonitoringDefenderStrategy


# Simple registry - no factory class needed
ATTACKER_STRATEGIES = {
    "greedy": GreedyAttackerStrategy,
    "random": RandomAttackerStrategy,
}

DEFENDER_STRATEGIES = {
    "reactive": ReactiveDefenderStrategy,
    "proactive": ProactiveDefenderStrategy,
    "monitoring": MonitoringDefenderStrategy,
}


def get_attacker_strategy(name: str) -> AttackerStrategy:
    """Get an attacker strategy instance"""
    strategy_class = ATTACKER_STRATEGIES.get(name, GreedyAttackerStrategy)
    return strategy_class()


def get_defender_strategy(name: str) -> DefenderStrategy:
    """Get a defender strategy instance"""
    strategy_class = DEFENDER_STRATEGIES.get(name, ReactiveDefenderStrategy)
    return strategy_class()
