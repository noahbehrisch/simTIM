from typing import Any, Tuple, Optional
from src.core.access_utils import get_node_access

class MonitoringDefenderStrategy:

    def __init__(self):
        self.name = 'monitoring'

    def choose_action(self, defender, network_state) -> Optional[Tuple[Any, Any]]:
        best = None
        best_priority = -1
        for action in defender.available_actions:
            if action.is_node_action():
                for node in network_state.get('nodes_list', []):
                    if not hasattr(node, 'links'):
                        continue
                    actor_access = get_node_access(node, defender.id)
                    try:
                        if action.precondition(node, actor_access, defender.id):
                            priority = self.get_priority(action, node)
                            if priority > best_priority:
                                best = (action, node)
                                best_priority = priority
                    except Exception as e:
                        continue
        return best

    def get_priority(self, action: Any, node: Any) -> float:
        priority = 0
        if 'Monitoring' in action.name or 'Detection' in action.name:
            priority += 90
        if len(node.assets) > 2:
            priority += len(node.assets) * 15
        priority += len(node.links) * 5
        if node.compromised:
            priority += 70
        return priority