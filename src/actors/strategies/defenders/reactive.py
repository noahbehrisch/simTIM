"""
Reactive Defender Strategy

Extracted from the existing defender.py implementation.
Responds to detected threats and vulnerabilities with priority on compromised systems.
"""
from typing import Any, Tuple, Optional


class ReactiveDefenderStrategy:
    """Reactive strategy - responds to detected threats and vulnerabilities"""
    
    def __init__(self):
        self.name = "reactive"
    
    def choose_action(self, defender, network_state) -> Optional[Tuple[Any, Any]]:
        """Choose action based on reactive priorities (extracted from _choose_reactive_action)"""
        best = None
        best_priority = -1
        
        for action in defender.available_actions:
            if action.is_node_action():
                for node in network_state.get('nodes_list', []):
                    actor_access = node.access.get(defender.id, None)
                    if action.precondition(node, actor_access, defender.id):
                        priority = self.get_priority(action, node)
                        if priority > best_priority:
                            best = (action, node)
                            best_priority = priority
        
        return best
    
    def get_priority(self, action: Any, node: Any) -> float:
        """Calculate reactive priority (extracted from _get_reactive_priority)"""
        priority = 0
        
        # High priority for incident response on compromised nodes
        if node.compromised and "Incident Response" in action.name:
            priority += 100
        elif node.compromised:
            priority += 50
        
        # Priority for patching vulnerable nodes
        if len(node.vulnerabilities) > 0 and ("Patch" in action.name or "Remediation" in action.name):
            priority += 30 + len(node.vulnerabilities) * 10
        
        # Asset value consideration
        priority += len(node.assets) * 2
        
        return priority
