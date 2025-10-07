"""
Monitoring Defender Strategy

Extracted from the existing defender.py implementation.
Focuses on detection and surveillance capabilities to monitor network activity.
"""
from typing import Any, Tuple, Optional


class MonitoringDefenderStrategy:
    """Monitoring strategy - focuses on detection and surveillance capabilities"""
    
    def __init__(self):
        self.name = "monitoring"
    
    def choose_action(self, defender, network_state) -> Optional[Tuple[Any, Any]]:
        """Choose action based on monitoring priorities (extracted from _choose_monitoring_action)"""
        best = None
        best_priority = -1
        
        for action in defender.available_actions:
            if action.is_node_action():
                for node in network_state.get('nodes_list', []):
                    # Ensure we're only processing Node objects, not Link objects
                    if not hasattr(node, 'links'):
                        continue  # Skip Link objects or other invalid types
                    
                    actor_access = node.access.get(defender.id, None)
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
        """Calculate monitoring priority (extracted from _get_monitoring_priority)"""
        priority = 0
        
        # High priority for monitoring and detection systems
        if "Monitoring" in action.name or "Detection" in action.name:
            priority += 90
        
        # Focus on high-value assets
        if len(node.assets) > 2:
            priority += len(node.assets) * 15
        
        # Priority for well-connected nodes (network visibility)
        priority += len(node.links) * 5
        
        # High priority if node is compromised (need monitoring)
        if node.compromised:
            priority += 70
        
        return priority
