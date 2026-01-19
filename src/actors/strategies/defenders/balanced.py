from typing import Any, Set
from src.actors.strategies.base import DefenderStrategy


class BalancedDefenderStrategy(DefenderStrategy):

    def __init__(self):
        super().__init__("balanced", detection_window_hours=3.0)

    def get_priority(self, action: Any, node: Any, detected_nodes: Set[str]) -> float:
        priority = 1
        node_id = getattr(node, "id", str(node))

        if detected_nodes and node_id in detected_nodes:
            priority += 150
            if "Incident Response" in action.name or "Isolation" in action.name:
                priority += 50

        if node.compromised:
            if "Incident Response" in action.name:
                priority += 100
            elif "Patch" in action.name:
                priority += 60
            else:
                priority += 20

        if not node.compromised and len(node.vulnerabilities) > 0:
            if "Patch" in action.name or "Update" in action.name:
                priority += 80 + len(node.vulnerabilities) * 10

        if "Firewall" in action.name or "EDR" in action.name or "Harden" in action.name:
            priority += 40

        if (
            "Monitoring" in action.name
            or "Detection" in action.name
            or "Log" in action.name
        ):
            priority += 50

        priority += len(node.assets) * 5

        return priority
