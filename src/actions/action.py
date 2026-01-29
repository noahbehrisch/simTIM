"""
Action classes for TIM simulation.

This module defines the Action base class as described in the TIM paper (Section 4.3-4.4).

Per TIM paper:
- An action a ∈ A is represented as a tuple a = (φa, ψa, ca, da, pa)
  - φa: precondition (SMT formula, implemented via JSON conditions)
  - ψa: postcondition (set of assignments)
  - ca: cost of performing the action
  - da: duration of the action
  - pa: success probability

Action Types:
- Node actions (A^(node)): Applied to a single node
- Link actions (A^(link)): Applied to a link, postcondition affects the END node
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

# Use TYPE_CHECKING to avoid circular imports
# Node is only needed for type hints, not at runtime
if TYPE_CHECKING:
    from src.core.access_levels import NodeAccessLevel
    from src.core.graph import Node

# Type alias for the callback signature used in preconditions/postconditions
AccessCallback = Callable[["Node", "NodeAccessLevel", str], Any]


class Action:
    def __init__(
        self,
        name: str,
        precondition: Callable[[Node, NodeAccessLevel, str], bool],
        postcondition: Callable[[Node, NodeAccessLevel, str], None],
        cost: float,
        duration: float,
        success_probability: float,
        action_type: str,
        detection_probability: Callable[[Node, NodeAccessLevel, str], float],
        one_off_damage: Callable[[Node, NodeAccessLevel, str], float],
        one_off_gain: Callable[[Node, NodeAccessLevel, str], float],
        time_damage: Callable[[Node, NodeAccessLevel, str], float],
        time_gain: Callable[[Node, NodeAccessLevel, str], float],
    ):
        self.name = name
        self.precondition = precondition
        self.postcondition = postcondition
        self.cost = cost
        self.duration = duration
        self.success_probability = success_probability
        self.action_type = action_type
        self.detection_probability = detection_probability
        self.one_off_damage = one_off_damage
        self.one_off_gain = one_off_gain
        self.time_damage = time_damage
        self.time_gain = time_gain
        self._json_data: dict[str, Any] | None = None

    def get_detection_probability(
        self, node: Node, actor_access: NodeAccessLevel, actor_id: str
    ) -> float:
        return self.detection_probability(node, actor_access, actor_id)

    def get_one_off_damage(self, node: Node, actor_access: NodeAccessLevel, actor_id: str) -> float:
        return self.one_off_damage(node, actor_access, actor_id)

    def get_one_off_gain(self, node: Node, actor_access: NodeAccessLevel, actor_id: str) -> float:
        return self.one_off_gain(node, actor_access, actor_id)

    def get_time_damage(self, node: Node, actor_access: NodeAccessLevel, actor_id: str) -> float:
        return self.time_damage(node, actor_access, actor_id)

    def get_time_gain(self, node: Node, actor_access: NodeAccessLevel, actor_id: str) -> float:
        return self.time_gain(node, actor_access, actor_id)

    def is_node_action(self) -> bool:
        return self.action_type == "node"

    def is_link_action(self) -> bool:
        return self.action_type == "link"

    def to_json(self) -> dict[str, Any]:
        """Convert action to JSON-serializable dict.

        Returns:
            Dictionary containing action configuration.

        Raises:
            ValueError: If action was created programmatically without JSON source data.
        """
        if hasattr(self, "_json_data") and self._json_data:
            return self._json_data.copy()

        raise ValueError(
            f"Action '{self.name}' was created programmatically and cannot be serialized. "
            "Only actions loaded from JSON support to_json()."
        )

    @classmethod
    def from_json(
        cls, action_data: dict[str, Any], function_registry: dict[str, Callable] | None = None
    ):
        from src.actions.action_manager import action_manager

        registry = function_registry or action_manager
        if hasattr(registry, "action_from_json"):
            return registry.action_from_json(action_data)
        else:
            raise ValueError("No action registry available for deserialization")

    def __repr__(self) -> str:
        return f"Action(name={self.name}, type={self.action_type}, cost={self.cost}, duration={self.duration}, success_prob={self.success_probability})"
