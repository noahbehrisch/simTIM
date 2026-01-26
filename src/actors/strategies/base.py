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
        visible_nodes = list(attacker.visible_nodes)

        for node in list(visible_nodes):
            access_level_raw = get_node_access(node, attacker.id)
            access_level: NodeAccessLevel
            if isinstance(access_level_raw, str):
                access_level = NodeAccessLevel.from_string(access_level_raw)
            elif isinstance(access_level_raw, NodeAccessLevel):
                access_level = access_level_raw
            else:
                access_level = NodeAccessLevel.NONE
            if access_level >= NodeAccessLevel.USER:
                for link in getattr(node, "links", []):
                    connected = link.node1 if link.node2.id == node.id else link.node2
                    if connected not in visible_nodes:
                        visible_nodes.append(connected)

        if not attacker.available_actions:
            return None

        best: tuple[Any, Any] | None = None
        best_priority: float = -1

        for action in attacker.available_actions:
            if hasattr(action, "is_link_action") and action.is_link_action():
                continue
            if action.is_node_action():
                for node in visible_nodes:
                    if not hasattr(node, "links"):
                        continue
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
                        continue

        return best

    def _is_action_ongoing(self, attacker, action, target) -> bool:
        if not hasattr(attacker, "simulator") or not attacker.simulator:
            return False
        target_id = getattr(target, "id", str(target))
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

    @abstractmethod
    def get_priority(self, action: Any, node: Any, access: Any, attacker: Any) -> float:
        pass


class DefenderStrategy(ABC):
    def __init__(self, name: str, detection_window_hours: float = 4.0):
        self.name = name
        self.detection_window_hours = detection_window_hours

    def choose_action(self, defender: Any, network_state: Any) -> tuple[Any, Any] | None:
        best: tuple[Any, Any] | None = None
        best_priority: float = -1

        detected_node_ids = self._get_detected_nodes(defender)

        if not defender.available_actions:
            logger.warning(f"Defender {defender.id} has no available actions!")
            return None

        nodes_list = network_state.nodes_list if network_state else []
        if not nodes_list:
            logger.warning(f"Defender {defender.id}: No nodes in network_state!")
            return None

        for action in defender.available_actions:
            if action.is_node_action():
                for node in nodes_list:
                    if not hasattr(node, "links"):
                        continue
                    if self._is_action_ongoing(defender, action, node):
                        continue
                    actor_access = get_node_access(node, defender.id)
                    try:
                        if action.precondition(node, actor_access, defender.id):
                            priority = self.get_priority(action, node, detected_node_ids)
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

    def _is_action_ongoing(self, defender, action, target) -> bool:
        if not hasattr(defender, "simulator") or not defender.simulator:
            return False
        target_id = getattr(target, "id", str(target))
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

    @abstractmethod
    def get_priority(self, action: Any, node: Any, detected_nodes: set[str] | None = None) -> float:
        pass
