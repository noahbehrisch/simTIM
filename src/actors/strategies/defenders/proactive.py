"""
Proactive Defender Strategy

Extracted from the existing defender.py implementation.
Actively hardens systems and patches vulnerabilities before they are exploited.
"""
from typing import Any, Tuple, Optional
from src.core.access_utils import get_node_access


class ProactiveDefenderStrategy:
    """Proactive strategy - actively hardens systems and patches vulnerabilities"""
    
    def __init__(self):
        self.name = "proactive"
    
    def choose_action(self, defender, network_state) -> Optional[Tuple[Any, Any]]:
        """Choose action based on proactive priorities (extracted from _choose_proactive_action)"""
        best = None
        best_priority = -1
        
        for action in defender.available_actions:
            if action.is_node_action():
                for node in network_state.get('nodes_list', []):
                    # Ensure we're only processing Node objects, not Link objects
                    if not hasattr(node, 'links'):
                        continue  # Skip Link objects or other invalid types
                    
                    actor_access = get_node_access(node, defender.id)
                    try:
                        if action.precondition(node, actor_access, defender.id):
                            priority = self.get_priority(action, node)
                            if priority > best_priority:
                                best = (action, node)
                                best_priority = priority
                    except Exception as e:
                        # Skip actions that fail precondition check or priority calculation
                        continue
        
        return best
    
    def get_priority(self, action: Any, node: Any) -> float:
        """Calculate proactive priority (extracted from _get_proactive_priority)"""
        priority = 0
        
        # High priority for patching uncompromised vulnerable nodes
        if not node.compromised and len(node.vulnerabilities) > 0:
            if "Patch" in action.name or "Remediation" in action.name:
                priority += 80 + len(node.vulnerabilities) * 15
        
        # Priority for security infrastructure
        if "Firewall" in action.name or "Detection" in action.name:
            priority += 60
        
        # High-value assets get priority
        if len(node.assets) > 2:
            priority += len(node.assets) * 10
        
        # Critical system categories
        if hasattr(node, 'category'):
            if node.category in ['Security', 'Servers']:
                priority += 40
        
        return priority
