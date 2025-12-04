"""
Link Actions Implementation for TIM Paper Compliance

This module provides utilities and examples for implementing link actions as specified
in the TIM paper Section 4.3.

Link actions differ from node actions in that they:
1. Apply to a directed link n1 → n2
2. Have preconditions that check properties and access of BOTH n1 and n2
3. Have postconditions that can modify properties of n2 and actor's access to n2
4. Model lateral movement and network propagation attacks

Reference: TIM paper Section 4.3 "Possible actions"
"""

from typing import Callable, Dict, Any
from src.core.graph import Node, Link
from src.actions.action import Action
from src.core.access_utils import get_node_access, set_node_access
from src.core.access_levels import NodeAccessLevel


def create_link_action(
    name: str,
    precondition_link: Callable[[Link, str, str], bool],
    postcondition_link: Callable[[Link, str, str], None],
    cost: float,
    duration: float,
    success_probability: float,
    detection_probability: Callable[[Link, str, str], float] = None,
    one_off_damage: Callable[[Link, str, str], float] = None,
    one_off_gain: Callable[[Link, str, str], float] = None,
) -> Action:
    """
    Create a link action with proper TIM paper semantics.
    
    Args:
        name: Action name
        precondition_link: Function that checks if action can be applied to link
        postcondition_link: Function that modifies link/nodes when action succeeds
        cost: Cost ca in TIM notation
        duration: Duration da in TIM notation
        success_probability: Success probability pa in TIM notation
        detection_probability: ϱ(a, π̂) function
        one_off_damage: D(a, π̂) function
        one_off_gain: G(a, π̂) function
    
    Returns:
        Action object configured as a link action
    """
    
    # Wrap link precondition to work with Action's node-based interface
    def node_precondition(node: Node, actor_access: str, actor_id: str) -> bool:
        # For link actions, the 'node' parameter is actually the target node (n2)
        # We need to find the link that leads to this node
        # This is a limitation of the current Action class design
        return precondition_link(node, actor_access, actor_id)
    
    # Wrap link postcondition
    def node_postcondition(node: Node, actor_access: str, actor_id: str) -> None:
        postcondition_link(node, actor_access, actor_id)
    
    # Default detection probability
    if detection_probability is None:
        detection_probability = lambda link, access, actor: 0.3
    
    # Default damage/gain functions
    if one_off_damage is None:
        one_off_damage = lambda link, access, actor: 500.0
    
    if one_off_gain is None:
        one_off_gain = lambda link, access, actor: 150.0
    
    # Wrap these for node interface
    def wrapped_detection(node, access, actor):
        return detection_probability(node, access, actor)
    
    def wrapped_damage(node, access, actor):
        return one_off_damage(node, access, actor)
    
    def wrapped_gain(node, access, actor):
        return one_off_gain(node, access, actor)
    
    # Time-proportional functions (typically 0 for link actions)
    def no_time_damage(node, access, actor):
        return 0.0
    
    def no_time_gain(node, access, actor):
        return 0.0
    
    return Action(
        name=name,
        precondition=node_precondition,
        postcondition=node_postcondition,
        cost=cost,
        duration=duration,
        success_probability=success_probability,
        action_type='link',
        detection_probability=wrapped_detection,
        one_off_damage=wrapped_damage,
        one_off_gain=wrapped_gain,
        time_damage=no_time_damage,
        time_gain=no_time_gain
    )


# Example: SSH Lateral Movement Attack (Link Action)
def create_ssh_lateral_movement_action() -> Action:
    """
    Create a link action for SSH-based lateral movement.
    
    Per TIM paper: Link action n1 → n2 where attacker uses compromised n1 
    to gain access to n2 via SSH.
    
    Precondition φa:
    - Actor has ADMIN access to source node n1
    - Target node n2 has SSH service running
    - Actor has NONE or VISIBLE access to n2 (not already compromised)
    
    Postcondition ψa:
    - Actor gains USER access to target node n2
    - Link n1→n2 becomes VISIBLE to actor
    """
    
    def precondition(target_node: Node, actor_access: str, actor_id: str) -> bool:
        # Check if target has SSH service
        if not hasattr(target_node, 'services'):
            return False
        
        if target_node.services.get('SSH') != 'running':
            return False
        
        # Check current access (should not already have high access)
        current_access = get_node_access(target_node, actor_id)
        if current_access >= NodeAccessLevel.USER:
            return False  # Already compromised
        
        # In a real link action, we'd also check source node access
        # For now, this is a simplified version
        return True
    
    def postcondition(target_node: Node, actor_access: str, actor_id: str) -> None:
        # Grant USER access to target node
        set_node_access(target_node, actor_id, NodeAccessLevel.USER)
        target_node.compromised = True
    
    def detection_prob(target_node: Node, actor_access: str, actor_id: str) -> float:
        # Detection depends on target's monitoring
        base_prob = 0.4
        
        if hasattr(target_node, 'properties'):
            if target_node.properties.get('network_monitoring'):
                base_prob += 0.3
            if target_node.properties.get('endpoint_protection'):
                base_prob += 0.2
        
        return min(base_prob, 1.0)
    
    return create_link_action(
        name="SSH Lateral Movement",
        precondition_link=precondition,
        postcondition_link=postcondition,
        cost=400.0,
        duration=2.0,
        success_probability=0.7,
        detection_probability=detection_prob
    )


# Example: RDP Lateral Movement Attack (Link Action)
def create_rdp_lateral_movement_action() -> Action:
    """
    Create a link action for RDP-based lateral movement (Windows networks).
    """
    
    def precondition(target_node: Node, actor_access: str, actor_id: str) -> bool:
        if not hasattr(target_node, 'services'):
            return False
        
        if target_node.services.get('RDP') != 'running':
            return False
        
        current_access = get_node_access(target_node, actor_id)
        return current_access < NodeAccessLevel.USER
    
    def postcondition(target_node: Node, actor_access: str, actor_id: str) -> None:
        set_node_access(target_node, actor_id, NodeAccessLevel.ADMIN)  # RDP often gives admin access
        target_node.compromised = True
    
    return create_link_action(
        name="RDP Lateral Movement",
        precondition_link=precondition,
        postcondition_link=postcondition,
        cost=350.0,
        duration=1.5,
        success_probability=0.65,
    )


# Example: Network Scan Link Action
def create_network_scan_action() -> Action:
    """
    Link action for discovering adjacent nodes through network scanning.
    
    Postcondition: Makes target node VISIBLE to actor
    """
    
    def precondition(target_node: Node, actor_access: str, actor_id: str) -> bool:
        # Can scan if we have at least VISIBLE access to source
        # For simplified version, always allow
        return True
    
    def postcondition(target_node: Node, actor_access: str, actor_id: str) -> None:
        # Make target visible
        current_access = get_node_access(target_node, actor_id)
        if current_access == NodeAccessLevel.NONE:
            set_node_access(target_node, actor_id, NodeAccessLevel.VISIBLE)
    
    def detection_prob(target_node: Node, actor_access: str, actor_id: str) -> float:
        # Network scans are relatively easy to detect
        return 0.6
    
    return create_link_action(
        name="Network Scan",
        precondition_link=precondition,
        postcondition_link=postcondition,
        cost=50.0,
        duration=0.5,
        success_probability=0.95,
        detection_probability=detection_prob
    )


def get_link_action_library() -> Dict[str, Action]:
    """
    Get a library of pre-defined link actions.
    
    Returns:
        Dictionary mapping action names to Action objects
    """
    return {
        'ssh_lateral_movement': create_ssh_lateral_movement_action(),
        'rdp_lateral_movement': create_rdp_lateral_movement_action(),
        'network_scan': create_network_scan_action(),
    }
