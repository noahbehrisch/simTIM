from typing import Any, Tuple, Optional


class GreedyAttackerStrategy:

    def __init__(self):
        self.name = "greedy"
    
    def choose_action(self, attacker, network_state) -> Optional[Tuple[Any, Any]]:
        visible_nodes = list(attacker.visible_nodes)
        visible_links = list(attacker.visible_links)
        best = None
        best_gain = float('-inf')
        
        for action in attacker.available_actions:
            if action.is_node_action():
                for node in visible_nodes:
                    # Ensure we're only processing Node objects, not Link objects
                    if not hasattr(node, 'links'):
                        continue  # Skip Link objects or other invalid types
                    
                    # Skip already compromised nodes
                    if hasattr(node, 'id') and node.id in attacker.compromised_nodes:
                        continue
                    actor_access = node.access.get(attacker.id, None)
                    try:
                        if action.precondition(node, actor_access, attacker.id):
                            gain = action.get_one_off_gain(node, actor_access, attacker.id)
                            if gain > best_gain:
                                best = (action, node)
                                best_gain = gain
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
                            gain = action.get_one_off_gain(link, actor_access, attacker.id)
                            if gain > best_gain:
                                best = (action, link)
                                best_gain = gain
                    except Exception as e:
                        # Skip actions that fail precondition check
                        continue
        
        return best
