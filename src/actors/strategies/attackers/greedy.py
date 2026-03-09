from typing import Any

from src.actors.strategies.base import AttackerStrategy
from src.core.access_levels import NodeAccessLevel


class GreedyAttackerStrategy(AttackerStrategy):
    def __init__(self, consider_cost: bool = True, consider_time_gain: bool = True):
        super().__init__("greedy")
        self.consider_cost = consider_cost
        self.consider_time_gain = consider_time_gain

    def get_priority(
        self, action: Any, target: Any, access: NodeAccessLevel, attacker: Any
    ) -> float:
        if hasattr(action, "is_link_action") and action.is_link_action():
            one_off_gain = action.get_one_off_gain(target, access, attacker.id)
            expected_gain = one_off_gain * action.success_probability
            if self.consider_cost:
                return expected_gain - action.cost
            return expected_gain

        one_off_gain = action.get_one_off_gain(target, access, attacker.id)

        if self.consider_time_gain:
            time_gain = action.get_time_gain(target, access, attacker.id)
            total_expected_gain = one_off_gain + (time_gain * action.duration)
        else:
            total_expected_gain = one_off_gain

        expected_gain = total_expected_gain * action.success_probability

        if self.consider_cost:
            return expected_gain - action.cost

        return expected_gain

    def get_minimum_threshold(self, ongoing_count: int) -> float:
        return 5.0 * ongoing_count
