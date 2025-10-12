"""
Base classes for strategy components.
"""
from abc import ABC, abstractmethod
from typing import Any, Tuple, Optional


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
