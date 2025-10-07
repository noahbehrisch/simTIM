"""
Greedy Attacker Strategy

Extracted from the existing attacker.py implementation.
Chooses actions with the highest expected gain.
"""
import random
from typing import Any, Tuple, Optional


class GreedyAttackerStrategy:
    """Greedy strategy - chooses action with highest expected gain"""
    
    def __init__(self):
        self.name = "greedy"
    
    def choose_action(self, attacker, network_state) -> Optional[Tuple[Any, Any]]:
        """Choose action with highest gain (extracted from choose_best_action)"""
        visible_nodes = list(attacker.visible_nodes)
        visible_links = list(attacker.visible_links)
        best = None
        best_gain = float('-inf')
        
        for action in attacker.available_actions:
            if action.is_node_action():
                for node in visible_nodes:
                    if hasattr(node, 'id') and node.id in attacker.compromised_nodes:
                        continue
                    actor_access = node.access.get(attacker.id, None)
                    if action.precondition(node, actor_access, attacker.id):
                        gain = action.get_one_off_gain(node, actor_access, attacker.id)
                        if gain > best_gain:
                            best = (action, node)
                            best_gain = gain
            elif action.is_link_action():
                for link in visible_links:
                    if hasattr(link, 'id') and link.id in attacker.compromised_links:
                        continue
                    actor_access = getattr(link, 'access', {}).get(attacker.id, None)
                    if action.precondition(link, actor_access, attacker.id):
                        gain = action.get_one_off_gain(link, actor_access, attacker.id)
                        if gain > best_gain:
                            best = (action, link)
                            best_gain = gain
        
        return best
