from typing import Any

from src.actors.strategies.base import AttackerStrategy
from src.core.access_levels import NodeAccessLevel


class EscalationAttackerStrategy(AttackerStrategy):
    def __init__(self):
        super().__init__("escalation")

    def get_priority(
        self, action: Any, target: Any, access: NodeAccessLevel, attacker: Any
    ) -> float:
        tactic = self.get_mitre_tactic(action)

        if hasattr(action, "is_link_action") and action.is_link_action():
            if access >= NodeAccessLevel.ADMIN:
                return 800.0
            if access >= NodeAccessLevel.USER:
                return 400.0
            return 100.0

        if access == NodeAccessLevel.VISIBLE:
            if tactic in ("initial-access", "reconnaissance"):
                return 1000.0
            return 50.0

        if access == NodeAccessLevel.USER:
            if tactic == "privilege-escalation":
                return 900.0
            if tactic == "credential-access":
                return 700.0
            return 50.0

        if access == NodeAccessLevel.ADMIN:
            if tactic == "credential-access":
                return 500.0
            if tactic == "defense-evasion":
                return 400.0
            if tactic == "command-and-control":
                return 350.0
            if tactic == "collection":
                return 300.0
            if tactic == "exfiltration":
                return 250.0
            if tactic == "impact":
                return 200.0
            if tactic == "persistence":
                return 150.0
            return 10.0

        return 1.0

    def get_minimum_threshold(self, ongoing_count: int) -> float:
        return 100.0 * ongoing_count
