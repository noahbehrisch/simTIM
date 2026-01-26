from typing import Any

from src.actors.strategies.base import AttackerStrategy


class GreedyAttackerStrategy(AttackerStrategy):
    def __init__(self, consider_cost: bool = True, consider_time_gain: bool = True):
        super().__init__("greedy")
        self.consider_cost = consider_cost
        self.consider_time_gain = consider_time_gain

    def get_priority(self, action: Any, node: Any, access: Any, attacker: Any) -> float:
        one_off_gain = action.get_one_off_gain(node, access, attacker.id)

        if self.consider_time_gain:
            time_gain = action.get_time_gain(node, access, attacker.id)
            total_expected_gain = one_off_gain + (time_gain * action.duration)
        else:
            total_expected_gain = one_off_gain

        expected_gain = total_expected_gain * action.success_probability

        if self.consider_cost:
            return expected_gain - action.cost

        return expected_gain
