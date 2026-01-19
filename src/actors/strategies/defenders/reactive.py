from typing import Any, Set
from src.actors.strategies.base import DefenderStrategy


class ReactiveDefenderStrategy(DefenderStrategy):
    """
    Reactive: Strongly prioritizes responding to detected attacks and compromised nodes.
    Prioritizes patching, firewall updates, and incident response when threats detected.
    """

    def __init__(self):
        super().__init__("reactive", detection_window_hours=4.0)

    def get_priority(self, action: Any, node: Any, detected_nodes: Set[str]) -> float:
        node_id = getattr(node, "id", str(node))
        priority = 1

        has_detection = detected_nodes and node_id in detected_nodes
        is_compromised = node.compromised

        if has_detection:
            priority += 100

            if "Patch" in action.name or "Remediation" in action.name:
                priority += 150
            elif "Firewall" in action.name:
                priority += 120
            elif "Detection" in action.name or "Monitoring" in action.name:
                priority += 50

        if is_compromised:
            if "Incident Response" in action.name:
                priority += 300
            elif "Patch" in action.name or "Remediation" in action.name:
                priority += 100
            elif "Firewall" in action.name:
                priority += 80
            else:
                priority += 20

        priority += len(node.assets) * 2

        return priority
