from typing import Any, Set
from src.actors.strategies.base import DefenderStrategy


class ProactiveDefenderStrategy(DefenderStrategy):
    """
    Proactive: Strongly prioritizes prevention before attacks happen.
    Lower priority for reaction (that's reactive's strength).
    """

    def __init__(self):
        super().__init__(
            "proactive", detection_window_hours=1.0
        )  # Short window - focuses on prevention

    def get_priority(self, action: Any, node: Any, detected_nodes: Set[str]) -> float:
        priority = 1  # Base priority for any valid action

        # Highest: Patch vulnerabilities before they're exploited
        if not node.compromised and len(node.vulnerabilities) > 0:
            if "Patch" in action.name or "Update" in action.name:
                priority += 150 + len(node.vulnerabilities) * 20

        # High: Deploy defensive measures
        defensive_actions = [
            "Firewall",
            "EDR",
            "Detection",
            "Monitoring",
            "Harden",
            "Security",
        ]
        for defensive in defensive_actions:
            if defensive in action.name:
                priority += 80
                break

        # Medium: Protect high-value assets
        priority += len(node.assets) * 10
        priority += len(node.links) * 3

        # Low priority for incident response (that's reactive's job)
        if node.compromised:
            priority += 10  # Still do something, but not the focus

        return priority
