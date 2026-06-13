import logging
from abc import ABC, abstractmethod
from typing import Any

from src.core.access_levels import NodeAccessLevel
from src.core.access_utils import get_node_access

logger = logging.getLogger(__name__)


class AttackerStrategy(ABC):
    def __init__(self, name: str):
        self.name = name

    def choose_action(self, attacker: Any, network_state: Any) -> tuple[Any, Any] | None:
        ongoing_count = 0
        if hasattr(attacker, "simulator") and attacker.simulator:
            ongoing_count = sum(
                1 for oa in attacker.simulator.ongoing_actions if oa.get("actor") == attacker
            )
        ongoing_count += getattr(attacker, "pending_action_count", 0)
        threshold = self.get_minimum_threshold(ongoing_count)

        visible_nodes = list(attacker.visible_nodes)

        if not attacker.available_actions:
            return None

        best: tuple[Any, Any] | None = None
        best_priority: float = -1

        visible_links = list(getattr(attacker, "visible_links", set()))
        for action in attacker.available_actions:
            if hasattr(action, "is_link_action") and action.is_link_action():
                for link in visible_links:
                    if self._is_action_ongoing(attacker, action, link):
                        continue
                    start_access = get_node_access(link.node1, attacker.id)
                    try:
                        if action.precondition(link, start_access, attacker.id):
                            priority = self.get_priority(action, link, start_access, attacker)
                            if priority > best_priority:
                                best = (action, link)
                                best_priority = priority
                    except Exception:
                        logger.debug(
                            "Error evaluating link action %s on %s",
                            action.name,
                            link,
                            exc_info=True,
                        )
                        continue

        for action in attacker.available_actions:
            if hasattr(action, "is_link_action") and action.is_link_action():
                continue
            if action.is_node_action():
                for node in visible_nodes:
                    if self._is_action_ongoing(attacker, action, node):
                        continue
                    actor_access = get_node_access(node, attacker.id)
                    try:
                        if action.precondition(node, actor_access, attacker.id):
                            priority = self.get_priority(action, node, actor_access, attacker)
                            if priority > best_priority:
                                best = (action, node)
                                best_priority = priority
                    except Exception:
                        logger.debug(
                            "Error evaluating node action %s on %s",
                            action.name,
                            node.id,
                            exc_info=True,
                        )
                        continue

        if best and best_priority >= threshold:
            return best
        if best:
            logger.debug(
                f"Best action {best[0].name} on {getattr(best[1], 'id', best[1])} "
                f"has priority {best_priority:.1f} below threshold {threshold:.1f}"
            )
        return None

    def _is_action_ongoing(self, attacker, action, target) -> bool:
        target_id = getattr(target, "id", str(target))
        if (action.name, target_id) in getattr(attacker, "_pending_pairs", set()):
            return True
        if not hasattr(attacker, "simulator") or not attacker.simulator:
            return False
        for ongoing in attacker.simulator.ongoing_actions:
            if ongoing.get("actor") == attacker and ongoing.get("action").name == action.name:
                if getattr(ongoing.get("target"), "id", "") == target_id:
                    return True
        return False

    def get_mitre_tactic(self, action: Any) -> str:
        if hasattr(action, "_json_data"):
            mitre = action._json_data.get("mitre_attack", {})
            return mitre.get("tactic", "unknown")
        return "unknown"

    def get_minimum_threshold(self, ongoing_count: int) -> float:
        return 50.0 * ongoing_count

    @abstractmethod
    def get_priority(self, action: Any, node: Any, access: NodeAccessLevel, attacker: Any) -> float:
        pass


class DefenderStrategy(ABC):
    def __init__(self, name: str, detection_window_hours: float = 4.0):
        self.name = name
        self.detection_window_hours = detection_window_hours

    def choose_action(self, defender: Any, network_state: Any) -> tuple[Any, Any] | None:
        ongoing_count = 0
        if hasattr(defender, "simulator") and defender.simulator:
            ongoing_count = sum(
                1 for oa in defender.simulator.ongoing_actions if oa.get("actor") == defender
            )
        ongoing_count += getattr(defender, "pending_action_count", 0)
        threshold = self.get_minimum_threshold(ongoing_count)

        best: tuple[Any, Any] | None = None
        best_priority: float = -1

        detected_node_ids = self._get_detected_nodes(defender)

        if not defender.available_actions:
            logger.debug(f"Defender {defender.id} has no available actions")
            return None

        nodes_list = network_state.nodes_list if network_state else []
        if not nodes_list:
            logger.warning(f"Defender {defender.id}: No nodes in network_state!")
            return None

        for action in defender.available_actions:
            if action.is_node_action():
                for node in nodes_list:
                    if self._is_action_ongoing(defender, action, node):
                        continue
                    actor_access = get_node_access(node, defender.id)
                    try:
                        if action.precondition(node, actor_access, defender.id):
                            priority = self.get_priority(
                                action, node, detected_node_ids, network_state
                            )
                            if priority > best_priority:
                                best = (action, node)
                                best_priority = priority
                    except Exception as e:
                        logger.debug(
                            f"Precondition check failed for {action.name} on {node.id}: {e}"
                        )
                        continue

        visible_links = list(getattr(defender, "visible_links", set()))
        for action in defender.available_actions:
            if hasattr(action, "is_link_action") and action.is_link_action():
                for link in visible_links:
                    if self._is_action_ongoing(defender, action, link):
                        continue
                    start_access = get_node_access(link.node1, defender.id)
                    try:
                        if action.precondition(link, start_access, defender.id):
                            priority = self.get_priority(
                                action, link.node1, detected_node_ids, network_state
                            )
                            if priority > best_priority:
                                best = (action, link)
                                best_priority = priority
                    except Exception as e:
                        logger.debug(f"Precondition check failed for {action.name} on {link}: {e}")
                        continue

        if best and best_priority >= threshold:
            logger.debug(
                f"Defender {defender.id} chose {best[0].name} on {getattr(best[1], 'id', str(best[1]))} "
                f"with priority {best_priority} (threshold {threshold})"
            )
            return best
        elif best:
            logger.debug(
                f"Defender {defender.id} found {best[0].name} on {getattr(best[1], 'id', str(best[1]))} "
                f"but priority {best_priority:.1f} below threshold {threshold:.1f}"
            )
        else:
            logger.debug(f"Defender {defender.id} found no valid action")
        return None

    def _is_action_ongoing(self, defender, action, target) -> bool:
        target_id = getattr(target, "id", str(target))
        if (action.name, target_id) in getattr(defender, "_pending_pairs", set()):
            return True
        if not hasattr(defender, "simulator") or not defender.simulator:
            return False
        for ongoing in defender.simulator.ongoing_actions:
            if ongoing.get("actor") == defender and ongoing.get("action").name == action.name:
                if getattr(ongoing.get("target"), "id", "") == target_id:
                    return True
        return False

    def _get_detected_nodes(self, defender) -> set[str]:
        detected_nodes = set()
        if hasattr(defender, "detected_attacks"):
            current_time = (
                getattr(defender.simulator, "current_time", 0.0) if defender.simulator else 0.0
            )
            for detection in defender.detected_attacks:
                if current_time - detection.get("timestamp", 0) < self.detection_window_hours:
                    target = detection.get("detected_target")
                    if target:
                        node_id = getattr(target, "id", str(target))
                        detected_nodes.add(node_id)
        return detected_nodes

    def get_d3fend_tactic(self, action: Any) -> str:
        if hasattr(action, "_json_data"):
            d3fend = action._json_data.get("d3fend", {})
            return d3fend.get("tactic", "Unknown")
        return "Unknown"

    def get_minimum_threshold(self, ongoing_count: int) -> float:
        return 30.0 * ongoing_count

    @abstractmethod
    def get_priority(
        self, action: Any, node: Any, detected_nodes: set[str] | None = None, network: Any = None
    ) -> float:
        pass
