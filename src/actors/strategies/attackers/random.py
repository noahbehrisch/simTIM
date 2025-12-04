import random
from typing import Any, Tuple, Optional
from src.actions.action_manager import would_action_improve_access
from src.core.access_utils import get_node_access


class RandomAttackerStrategy:
    
    def __init__(self):
        self.name = "random"
    
    def choose_action(self, attacker, network_state) -> Optional[Tuple[Any, Any]]:
        visible_nodes = list(attacker.visible_nodes)
        visible_links = list(attacker.visible_links)
        possible_actions = []
        
        print(f"[DEBUG] Attacker {attacker.id} has {len(visible_nodes)} visible nodes, {len(attacker.available_actions)} available actions")
        
        for action in attacker.available_actions:
            if action.is_node_action():
                for node in visible_nodes:
                    # Skip already compromised nodes
                    if hasattr(node, 'id') and node.id in attacker.compromised_nodes:
                        continue
                    
                    actor_access = get_node_access(node, attacker.id)
                    print(f"[DEBUG] Checking action {action.name} on node {getattr(node, 'id', 'unknown')} with access {actor_access}")
                    
                    try:
                        # First check if the action precondition is satisfied
                        if action.precondition(node, actor_access, attacker.id):
                            # Then check if this action would actually be beneficial
                            if would_action_improve_access(action, node, actor_access, attacker.id):
                                possible_actions.append((action, node))
                                print(f"[DEBUG] Action {action.name} is beneficial on node {getattr(node, 'id', 'unknown')}")
                            else:
                                print(f"[DEBUG] Action {action.name} would not improve access on node {getattr(node, 'id', 'unknown')} (current: {actor_access})")
                    except Exception as e:
                        print(f"[DEBUG] Action {action.name} failed precondition check: {e}")
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
        
        print(f"[DEBUG] Attacker {attacker.id} found {len(possible_actions)} possible actions")
        return random.choice(possible_actions) if possible_actions else None
