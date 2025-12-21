from typing import Callable, Dict, Any
from src.core.graph import Node, Link
from src.actions.action import Action
from src.core.access_utils import get_node_access, set_node_access
from src.core.access_levels import NodeAccessLevel

def create_link_action(name: str, precondition_link: Callable[[Link, str, str], bool], postcondition_link: Callable[[Link, str, str], None], cost: float, duration: float, success_probability: float, detection_probability: Callable[[Link, str, str], float]=None, one_off_damage: Callable[[Link, str, str], float]=None, one_off_gain: Callable[[Link, str, str], float]=None) -> Action:

    def node_precondition(node: Node, actor_access: str, actor_id: str) -> bool:
        return precondition_link(node, actor_access, actor_id)

    def node_postcondition(node: Node, actor_access: str, actor_id: str) -> None:
        postcondition_link(node, actor_access, actor_id)
    if detection_probability is None:
        detection_probability = lambda link, access, actor: 0.3
    if one_off_damage is None:
        one_off_damage = lambda link, access, actor: 500.0
    if one_off_gain is None:
        one_off_gain = lambda link, access, actor: 150.0

    def wrapped_detection(node, access, actor):
        return detection_probability(node, access, actor)

    def wrapped_damage(node, access, actor):
        return one_off_damage(node, access, actor)

    def wrapped_gain(node, access, actor):
        return one_off_gain(node, access, actor)

    def no_time_damage(node, access, actor):
        return 0.0

    def no_time_gain(node, access, actor):
        return 0.0
    return Action(name=name, precondition=node_precondition, postcondition=node_postcondition, cost=cost, duration=duration, success_probability=success_probability, action_type='link', detection_probability=wrapped_detection, one_off_damage=wrapped_damage, one_off_gain=wrapped_gain, time_damage=no_time_damage, time_gain=no_time_gain)

def create_ssh_lateral_movement_action() -> Action:

    def precondition(target_node: Node, actor_access: str, actor_id: str) -> bool:
        if not hasattr(target_node, 'services'):
            return False
        if target_node.services.get('SSH') != 'running':
            return False
        current_access = get_node_access(target_node, actor_id)
        if current_access >= NodeAccessLevel.USER:
            return False
        return True

    def postcondition(target_node: Node, actor_access: str, actor_id: str) -> None:
        set_node_access(target_node, actor_id, NodeAccessLevel.USER)
        target_node.compromised = True

    def detection_prob(target_node: Node, actor_access: str, actor_id: str) -> float:
        base_prob = 0.4
        if hasattr(target_node, 'properties'):
            if target_node.properties.get('network_monitoring'):
                base_prob += 0.3
            if target_node.properties.get('endpoint_protection'):
                base_prob += 0.2
        return min(base_prob, 1.0)
    return create_link_action(name='SSH Lateral Movement', precondition_link=precondition, postcondition_link=postcondition, cost=400.0, duration=2.0, success_probability=0.7, detection_probability=detection_prob)

def create_rdp_lateral_movement_action() -> Action:

    def precondition(target_node: Node, actor_access: str, actor_id: str) -> bool:
        if not hasattr(target_node, 'services'):
            return False
        if target_node.services.get('RDP') != 'running':
            return False
        current_access = get_node_access(target_node, actor_id)
        return current_access < NodeAccessLevel.USER

    def postcondition(target_node: Node, actor_access: str, actor_id: str) -> None:
        set_node_access(target_node, actor_id, NodeAccessLevel.ADMIN)
        target_node.compromised = True
    return create_link_action(name='RDP Lateral Movement', precondition_link=precondition, postcondition_link=postcondition, cost=350.0, duration=1.5, success_probability=0.65)

def create_network_scan_action() -> Action:

    def precondition(target_node: Node, actor_access: str, actor_id: str) -> bool:
        return True

    def postcondition(target_node: Node, actor_access: str, actor_id: str) -> None:
        current_access = get_node_access(target_node, actor_id)
        if current_access == NodeAccessLevel.NONE:
            set_node_access(target_node, actor_id, NodeAccessLevel.VISIBLE)

    def detection_prob(target_node: Node, actor_access: str, actor_id: str) -> float:
        return 0.6
    return create_link_action(name='Network Scan', precondition_link=precondition, postcondition_link=postcondition, cost=50.0, duration=0.5, success_probability=0.95, detection_probability=detection_prob)

def get_link_action_library() -> Dict[str, Action]:
    return {'ssh_lateral_movement': create_ssh_lateral_movement_action(), 'rdp_lateral_movement': create_rdp_lateral_movement_action(), 'network_scan': create_network_scan_action()}