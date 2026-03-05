from typing import Any

from src.actors.strategies.base import AttackerStrategy
from src.core.access_levels import NodeAccessLevel


class EscalationAttackerStrategy(AttackerStrategy):
    """Simple escalation loop: gain initial access, escalate to admin,
    scan for new nodes, repeat on each discovered node."""

    def __init__(self):
        super().__init__("escalation")

    def get_priority(
        self, action: Any, target: Any, access: NodeAccessLevel, attacker: Any
    ) -> float:
        tactic = self.get_mitre_tactic(action)

        # --- Link actions (e.g. Network Scan) ---
        if hasattr(action, "is_link_action") and action.is_link_action():
            if access >= NodeAccessLevel.ADMIN:
                return 800.0  # Fully escalated — discover next
            if access >= NodeAccessLevel.USER:
                return 400.0
            return 100.0

        # --- Node actions: escalate access ---
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
            # Already admin — node actions are low priority
            return 10.0

        return 1.0

    def get_minimum_threshold(self, ongoing_count: int) -> float:
        """Each concurrent action requires higher tactical value."""
        return 100.0 * ongoing_count
