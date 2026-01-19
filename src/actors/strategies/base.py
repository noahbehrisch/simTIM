from abc import ABC, abstractmethod
from typing import Any, Tuple, Optional, Set
import logging
from src.core.access_utils import get_node_access

logger = logging.getLogger(__name__)


class AttackerStrategy(ABC):

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def choose_action(self, attacker, network_state) -> Optional[Tuple[Any, Any]]:
        pass


class DefenderStrategy(ABC):
    """
    Base class for defender strategies.

    Subclasses only need to implement get_priority() - the choose_action() logic
    is shared across all defender strategies.
    """

    def __init__(self, name: str, detection_window_hours: float = 4.0):
        self.name = name
        self.detection_window_hours = detection_window_hours

    def choose_action(self, defender, network_state) -> Optional[Tuple[Any, Any]]:
        """
        Common action selection loop for all defender strategies.
        Iterates through available actions and nodes, selecting the highest priority.
        """
        best = None
        best_priority = -1

        # Get nodes with recent detections for priority boost
        detected_node_ids = self._get_detected_nodes(defender)

        if not defender.available_actions:
            logger.warning(f"Defender {defender.id} has no available actions!")
            return None

        nodes_list = network_state.get("nodes_list", []) if network_state else []
        if not nodes_list:
            logger.warning(f"Defender {defender.id}: No nodes in network_state!")
            return None

        for action in defender.available_actions:
            if action.is_node_action():
                for node in nodes_list:
                    if not hasattr(node, "links"):
                        continue
                    actor_access = get_node_access(node, defender.id)
                    try:
                        if action.precondition(node, actor_access, defender.id):
                            priority = self.get_priority(
                                action, node, detected_node_ids
                            )
                            if priority > best_priority:
                                best = (action, node)
                                best_priority = priority
                    except Exception as e:
                        logger.debug(
                            f"Precondition check failed for {action.name} on {node.id}: {e}"
                        )
                        continue

        if best:
            logger.debug(
                f"Defender {defender.id} chose {best[0].name} on {best[1].id} with priority {best_priority}"
            )
        else:
            logger.debug(f"Defender {defender.id} found no valid action")
        return best

    def _get_detected_nodes(self, defender) -> Set[str]:
        """
        Get set of node IDs that have recent attack detections.

        Uses detection_window_hours to determine what counts as "recent".
        """
        detected_nodes = set()
        if hasattr(defender, "detected_attacks"):
            current_time = (
                getattr(defender.simulator, "current_time", 0.0)
                if defender.simulator
                else 0.0
            )
            for detection in defender.detected_attacks:
                if (
                    current_time - detection.get("timestamp", 0)
                    < self.detection_window_hours
                ):
                    target = detection.get("detected_target")
                    if target:
                        node_id = getattr(target, "id", str(target))
                        detected_nodes.add(node_id)
        return detected_nodes

    @abstractmethod
    def get_priority(
        self, action: Any, node: Any, detected_nodes: Set[str] = None
    ) -> float:
        """
        Calculate priority for an action on a node.

        Args:
            action: The action to evaluate
            node: The target node
            detected_nodes: Set of node IDs with recent attack detections

        Returns:
            Priority score (higher = more preferred)
        """
        pass
