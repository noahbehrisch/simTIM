from typing import Any, Tuple, Optional
import logging
from src.core.access_levels import NodeAccessLevel
from src.actions.action_manager import would_action_improve_access
from src.core.access_utils import get_node_access

logger = logging.getLogger(__name__)


class GreedyAttackerStrategy:

    def __init__(self):
        self.name = "greedy"

    def _is_action_ongoing(self, attacker, action, target) -> bool:
        """Check if this action is already ongoing on this target."""
        if not hasattr(attacker, "simulator") or not attacker.simulator:
            return False
        target_id = getattr(target, "id", str(target))
        for ongoing in attacker.simulator.ongoing_actions:
            ongoing_action = ongoing.get("action")
            ongoing_target = ongoing.get("target")
            ongoing_actor = ongoing.get("actor")
            if ongoing_actor == attacker and ongoing_action.name == action.name:
                # Check if same target
                ongoing_target_id = getattr(ongoing_target, "id", str(ongoing_target))
                if target_id == ongoing_target_id:
                    return True
        return False

    def choose_action(self, attacker, network_state) -> Optional[Tuple[Any, Any]]:
        visible_nodes = list(attacker.visible_nodes)
        visible_links = list(attacker.visible_links)
        logger.debug(f"[GREEDY] Choosing action for {attacker.id}")
        logger.debug(
            f"[GREEDY]   {len(visible_nodes)} visible nodes, {len(visible_links)} visible links"
        )
        nodes_with_access = []
        for node in visible_nodes:
            access_level = get_node_access(node, attacker.id)
            if access_level >= NodeAccessLevel.USER:
                nodes_with_access.append(node)
        if network_state and "nodes" in network_state:
            for node in network_state["nodes"]:
                if hasattr(node, "id") and node.id in attacker.compromised_nodes:
                    if node not in nodes_with_access:
                        nodes_with_access.append(node)
        for accessed_node in nodes_with_access:
            for link in getattr(accessed_node, "links", []):
                connected_node = (
                    link.node1 if link.node2.id == accessed_node.id else link.node2
                )
                if connected_node not in visible_nodes:
                    visible_nodes.append(connected_node)
        best = None
        best_gain = float("-inf")
        candidates = []
        for action in attacker.available_actions:
            if hasattr(action, "is_link_action") and action.is_link_action():
                continue
            if action.is_node_action():
                for node in visible_nodes:
                    if not hasattr(node, "links"):
                        continue
                    # Skip if this action is already ongoing on this target
                    if self._is_action_ongoing(attacker, action, node):
                        continue
                    actor_access = get_node_access(node, attacker.id)
                    try:
                        precond_ok = action.precondition(
                            node, actor_access, attacker.id
                        )
                        would_improve = would_action_improve_access(
                            action, node, actor_access, attacker.id
                        )
                        if precond_ok and would_improve:
                            gain = action.get_one_off_gain(
                                node, actor_access, attacker.id
                            )
                            candidates.append(
                                (action.name, node.id, gain, actor_access)
                            )
                            if gain > best_gain:
                                best = (action, node)
                                best_gain = gain
                    except Exception as e:
                        continue
        logger.debug(f"[GREEDY]   Found {len(candidates)} candidate node actions")
        if best:
            logger.debug(
                f"[GREEDY]   Best: {best[0].name} on {(best[1].id if hasattr(best[1], 'id') else best[1])} (gain={best_gain})"
            )
        else:
            logger.debug(f"[GREEDY]   No beneficial action found!")
        return best
