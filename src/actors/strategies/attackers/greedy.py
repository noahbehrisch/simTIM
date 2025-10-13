from typing import Any, Tuple, Optional


class GreedyAttackerStrategy:

    def __init__(self):
        self.name = "greedy"
    
    def choose_action(self, attacker, network_state) -> Optional[Tuple[Any, Any]]:
        visible_nodes = list(attacker.visible_nodes)
        visible_links = list(attacker.visible_links)
        
        # Expand visibility to include nodes connected to compromised nodes
        # This simulates network discovery from systems with USER or ADMIN access
        from src.core.access_levels import NodeAccessLevel
        
        # Check all visible nodes for USER/ADMIN access (not just compromised_nodes)
        nodes_with_access = []
        for node in visible_nodes:
            if hasattr(node, 'access') and attacker.id in node.access:
                access_level = node.access[attacker.id]
                if access_level in [NodeAccessLevel.USER, NodeAccessLevel.ADMIN]:
                    nodes_with_access.append(node)
        
        # Add compromised nodes from the tracking set
        if network_state and 'nodes' in network_state:
            for node in network_state['nodes']:
                if hasattr(node, 'id') and node.id in attacker.compromised_nodes:
                    if node not in nodes_with_access:
                        nodes_with_access.append(node)
        
        # Discover connected nodes from all nodes we have access to
        for accessed_node in nodes_with_access:
            for link in getattr(accessed_node, 'links', []):
                connected_node = link.node1 if link.node2.id == accessed_node.id else link.node2
                if connected_node not in visible_nodes:
                    visible_nodes.append(connected_node)
        
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
