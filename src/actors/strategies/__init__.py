"""
Strategy Components for simTIM Actors

This module provides strategy components to extract decision-making logic from actor classes.
Each strategy focuses on a specific decision-making approach.
"""
from abc import ABC, abstractmethod
from typing import Any, Tuple, Optional

# Import all strategies for easy access
from .attackers.greedy import GreedyAttackerStrategy
from .attackers.random import RandomAttackerStrategy
from .defenders.reactive import ReactiveDefenderStrategy
from .defenders.proactive import ProactiveDefenderStrategy
from .defenders.monitoring import MonitoringDefenderStrategy


class AttackerStrategy(ABC):
    """Base class for attacker strategies"""
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    def choose_action(self, attacker, network_state) -> Optional[Tuple[Any, Any]]:
        """
        Choose the best action for the attacker given the current state.
        
        Args:
            attacker: The attacker instance
            network_state: Current network state
            
        Returns:
            Tuple of (action, target) or None if no action should be taken
        """
        pass


class DefenderStrategy(ABC):
    """Base class for defender strategies"""
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    def choose_action(self, defender, network_state) -> Optional[Tuple[Any, Any]]:
        """
        Choose the best action for the defender given the current state.
        
        Args:
            defender: The defender instance
            network_state: Current network state
            
        Returns:
            Tuple of (action, target) or None if no action should be taken
        """
        pass
    
    @abstractmethod
    def get_priority(self, action: Any, node: Any) -> float:
        """
        Calculate priority for a specific action-node combination.
        
        Args:
            action: The action being considered
            node: The target node
            
        Returns:
            Priority score (higher = better)
        """
        pass


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
