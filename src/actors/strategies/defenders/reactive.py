from typing import Any, Tuple, Optional
from src.core.access_utils import get_node_access

class ReactiveDefenderStrategy:

    def __init__(self):
        self.name = 'reactive'

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
        if node.compromised and 'Incident Response' in action.name:
            priority += 100
        elif node.compromised:
            priority += 50
        if len(node.vulnerabilities) > 0 and ('Patch' in action.name or 'Remediation' in action.name):
            priority += 30 + len(node.vulnerabilities) * 10
        priority += len(node.assets) * 2
        return priority