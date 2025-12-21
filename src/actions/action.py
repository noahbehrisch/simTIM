from src.core.graph import Node
from typing import Any, Callable, Dict
import json

class Action:

    def __init__(self, name: str, precondition: Callable[[Node, str, str], bool], postcondition: Callable[[Node, str, str], None], cost: float, duration: float, success_probability: float, action_type: str, detection_probability: Callable[[Node, str, str], float], one_off_damage: Callable[[Node, str, str], float], one_off_gain: Callable[[Node, str, str], float], time_damage: Callable[[Node, str, str], float], time_gain: Callable[[Node, str, str], float]):
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

    def get_name(self) -> str:
        return self.name

    def enforce_precondition(self, node, actor_access, actor_id) -> bool:
        return self.precondition(node, actor_access, actor_id)

    def apply_postcondition(self, node, actor_access, actor_id) -> None:
        self.postcondition(node, actor_access, actor_id)

    def get_cost(self) -> float:
        return self.cost

    def get_duration(self) -> float:
        return self.duration

    def get_success_probability(self) -> float:
        return self.success_probability

    def get_action_type(self) -> str:
        return self.action_type

    def get_detection_probability(self, node, actor_access, actor_id) -> float:
        return self.detection_probability(node, actor_access, actor_id)

    def get_one_off_damage(self, node, actor_access, actor_id) -> float:
        return self.one_off_damage(node, actor_access, actor_id)

    def get_one_off_gain(self, node, actor_access, actor_id) -> float:
        return self.one_off_gain(node, actor_access, actor_id)

    def get_time_damage(self, node, actor_access, actor_id) -> float:
        return self.time_damage(node, actor_access, actor_id)

    def get_time_gain(self, node, actor_access, actor_id) -> float:
        return self.time_gain(node, actor_access, actor_id)

    def is_node_action(self) -> bool:
        return self.action_type == 'node'

    def is_link_action(self) -> bool:
        return self.action_type == 'link'

    def to_json(self) -> Dict[str, Any]:
        return {'name': self.name, 'action_type': self.action_type, 'cost': self.cost, 'duration': self.duration, 'success_probability': self.success_probability, 'precondition': {'type': 'function_ref', 'function': getattr(self.precondition, '__name__', 'unknown_function')}, 'postcondition': {'type': 'function_ref', 'function': getattr(self.postcondition, '__name__', 'unknown_function')}, 'detection_probability': {'type': 'function_ref', 'function': getattr(self.detection_probability, '__name__', 'unknown_function')}, 'damage_gain': {'one_off_damage': self.get_one_off_damage(None, None, None) if callable(self.one_off_damage) else 0.0, 'one_off_gain': self.get_one_off_gain(None, None, None) if callable(self.one_off_gain) else 0.0, 'time_damage': self.get_time_damage(None, None, None) if callable(self.time_damage) else 0.0, 'time_gain': self.get_time_gain(None, None, None) if callable(self.time_gain) else 0.0}}

    @classmethod
    def from_json(cls, action_data: Dict[str, Any], function_registry: Dict[str, Callable]=None):
        from src.actions.action_manager import action_manager
        registry = function_registry or action_manager
        if hasattr(registry, 'action_from_json'):
            return registry.action_from_json(action_data)
        else:
            raise ValueError('No action registry available for deserialization')

    def __repr__(self) -> str:
        return f'Action(name={self.name}, type={self.action_type}, cost={self.cost}, duration={self.duration}, success_prob={self.success_probability})'