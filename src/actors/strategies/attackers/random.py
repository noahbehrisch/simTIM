"""
Random Attacker Strategy

Extracted from the existing attacker.py implementation.
Selects valid actions randomly for unpredictable behavior.
"""
import random
from typing import Any, Tuple, Optional


class RandomAttackerStrategy:
    """Random strategy - selects valid actions randomly"""
    
    def __init__(self):
        self.name = "random"
    
    def choose_action(self, attacker, network_state) -> Optional[Tuple[Any, Any]]:
        """Choose action randomly from valid options (extracted from choose_random_action)"""
        visible_nodes = list(attacker.visible_nodes)
        visible_links = list(attacker.visible_links)
        possible_actions = []
        
        for action in attacker.available_actions:
            if action.is_node_action():
                for node in visible_nodes:
                    # Skip already compromised nodes
                    if hasattr(node, 'id') and node.id in attacker.compromised_nodes:
                        continue
                    actor_access = node.access.get(attacker.id, None)
                    try:
                        if action.precondition(node, actor_access, attacker.id):
                            possible_actions.append((action, node))
                    except Exception as e:
                        # Skip actions that fail precondition check
                        continue
            elif action.is_link_action():
                for link in visible_links:
                    # Links don't have id attribute, so check differently
                    if link in attacker.compromised_links:
                        continue
                    actor_access = getattr(link, 'access', {}).get(attacker.id, None)
                    try:
                        if action.precondition(link, actor_access, attacker.id):
                            possible_actions.append((action, link))
                    except Exception as e:
                        # Skip actions that fail precondition check
                        continue
        
        return random.choice(possible_actions) if possible_actions else None
