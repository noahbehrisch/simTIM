from typing import Any, Tuple, Optional
from src.core.access_levels import NodeAccessLevel
from src.actions.action_manager import would_action_improve_access
from src.core.access_utils import get_node_access

class GreedyAttackerStrategy:

    def __init__(self):
        self.name = 'greedy'

    def choose_action(self, attacker, network_state) -> Optional[Tuple[Any, Any]]:
        visible_nodes = list(attacker.visible_nodes)
        visible_links = list(attacker.visible_links)
        print(f'[GREEDY] Choosing action for {attacker.id}')
        print(f'[GREEDY]   {len(visible_nodes)} visible nodes, {len(visible_links)} visible links')
        nodes_with_access = []
        for node in visible_nodes:
            access_level = get_node_access(node, attacker.id)
            if access_level >= NodeAccessLevel.USER:
                nodes_with_access.append(node)
        if network_state and 'nodes' in network_state:
            for node in network_state['nodes']:
                if hasattr(node, 'id') and node.id in attacker.compromised_nodes:
                    if node not in nodes_with_access:
                        nodes_with_access.append(node)
        for accessed_node in nodes_with_access:
            for link in getattr(accessed_node, 'links', []):
                connected_node = link.node1 if link.node2.id == accessed_node.id else link.node2
                if connected_node not in visible_nodes:
                    visible_nodes.append(connected_node)
        best = None
        best_gain = float('-inf')
        candidates = []
        for action in attacker.available_actions:
            if hasattr(action, 'is_link_action') and action.is_link_action():
                continue
            if action.is_node_action():
                for node in visible_nodes:
                    if not hasattr(node, 'links'):
                        continue
                    actor_access = get_node_access(node, attacker.id)
                    try:
                        precond_ok = action.precondition(node, actor_access, attacker.id)
                        would_improve = would_action_improve_access(action, node, actor_access, attacker.id)
                        if precond_ok and would_improve:
                            gain = action.get_one_off_gain(node, actor_access, attacker.id)
                            candidates.append((action.name, node.id, gain, actor_access))
                            if gain > best_gain:
                                best = (action, node)
                                best_gain = gain
                    except Exception as e:
                        continue
        print(f'[GREEDY]   Found {len(candidates)} candidate node actions:')
        for cname, nid, gain, access in candidates[:10]:
            print(f'[GREEDY]     {cname} on {nid} (gain={gain}, access={access})')
        if best:
            print(f"[GREEDY]   Best: {best[0].name} on {(best[1].id if hasattr(best[1], 'id') else best[1])} (gain={best_gain})")
        else:
            print(f'[GREEDY]   No beneficial action found!')
        return best