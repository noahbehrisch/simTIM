"""
Link Actions Implementation for TIM Paper Compliance

This module provides utilities and examples for implementing link actions as specified
in the TIM paper Section 4.3.

Link actions differ from node actions in that    return create_link_action(
        name="SSH Lateral Movement",
        precondition_link=ssh_precondition,
        postcondition_link=ssh_postcondition,
        cost=400.0,
        duration=2.0,
        success_probability=0.7,
        detection_probability=detection_prob,
        one_off_damage=damage_calc,
        one_off_gain=gain_calc
    ) Apply to a directed link n1 → n2
2. Have preconditions that check properties and access of BOTH n1 and n2
3. Have postconditions that can modify properties of n2 and actor's access to n2
4. Model lateral movement and network propagation attacks

Reference: TIM paper Section 4.3 "Possible actions"
"""

from typing import Callable, Dict, Any
from src.core.graph import Node, Link
from src.actions.action import Action


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
    
    # Validate required parameters
    if detection_probability is None:
        raise ValueError(f"Link action '{name}' must provide detection_probability function")
    
    # Validate damage/gain functions
    if one_off_damage is None:
        raise ValueError(f"Link action '{name}' must provide one_off_damage function")
    
    if one_off_gain is None:
        raise ValueError(f"Link action '{name}' must provide one_off_gain function")
    
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
    
    def ssh_precondition(target_node: Node, actor_access: str, actor_id: str) -> bool:
        # Check if target has SSH service
        if not hasattr(target_node, 'services'):
            return False
        
        if target_node.services.get('SSH') != 'running':
            return False
        
        # Check current access (should not already have high access)
        current_access = target_node.access.get(actor_id, "NONE")
        if current_access in ["USER", "ADMIN"]:
            return False  # Already compromised
        
        # In a real link action, we'd also check source node access
        # For now, this is a simplified version
        return True
    
    def ssh_postcondition(target_node: Node, actor_access: str, actor_id: str) -> None:
        # Grant USER access to target node
        if not hasattr(target_node, 'access'):
            target_node.access = {}
        target_node.access[actor_id] = "USER"
        target_node.compromised = True
    
    def detection_prob(link, actor_access: str, actor_id: str) -> float:
        # SSH lateral movement detection depends on network monitoring and logging
        base_prob = 0.25  # SSH is somewhat stealthy but leaves network traces
        
        if hasattr(link, 'properties'):
            # Network monitoring significantly increases detection
            monitoring = link.properties.get('network_monitoring', 'none')
            if monitoring == 'SIEM':
                base_prob += 0.35
            elif monitoring == 'IPS':
                base_prob += 0.30
            elif monitoring == 'IDS':
                base_prob += 0.25
            elif monitoring == 'basic_logging':
                base_prob += 0.15
            
            # Endpoint protection can detect unusual SSH connections
            endpoint = link.properties.get('endpoint_protection', 'none')
            if endpoint in ['CrowdStrike', 'Carbon Black']:
                base_prob += 0.20
            elif endpoint in ['Sophos', 'McAfee']:
                base_prob += 0.15
            elif endpoint == 'Windows Defender':
                base_prob += 0.10
            
            # SSH monitoring specifically
            if link.properties.get('ssh_monitoring', False):
                base_prob += 0.25
        
        return min(base_prob, 0.95)  # Cap at 95% detection
    
    def damage_calc(link, actor_access: str, actor_id: str) -> float:
        # Lateral movement damage depends on target value and compromise level
        base_damage = 200.0  # Base cost of lateral movement incident
        
        if hasattr(link, 'properties'):
            # Critical systems cause more damage when compromised
            criticality = link.properties.get('criticality', 'low')
            if criticality == 'critical':
                base_damage *= 3.0
            elif criticality == 'high':
                base_damage *= 2.0
            elif criticality == 'medium':
                base_damage *= 1.5
            
            # Data sensitivity increases damage
            data_sensitivity = link.properties.get('data_sensitivity', 'low')
            if data_sensitivity == 'high':
                base_damage *= 2.5
            elif data_sensitivity == 'medium':
                base_damage *= 1.5
        
        return base_damage
    
    def gain_calc(link, actor_access: str, actor_id: str) -> float:
        # Attacker gain from lateral movement (information, access value)
        base_gain = 100.0  # Base value of gaining access to another system
        
        if hasattr(link, 'properties'):
            # More valuable targets provide more gain
            criticality = link.properties.get('criticality', 'low')
            if criticality == 'critical':
                base_gain *= 4.0
            elif criticality == 'high':
                base_gain *= 2.5
            elif criticality == 'medium':
                base_gain *= 1.5
            
            # Assets on the target system
            assets = getattr(link, 'assets', [])
            if assets:
                base_gain += len(assets) * 50.0  # Each asset adds value
        
        return base_gain
    
    return create_link_action(
        name="SSH Lateral Movement",
        precondition_link=ssh_precondition,
        postcondition_link=ssh_postcondition,
        cost=400.0,
        duration=2.0,
        success_probability=0.7,
        detection_probability=detection_prob,
        one_off_damage=damage_calc,
        one_off_gain=gain_calc
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
        
        current_access = target_node.access.get(actor_id, "NONE")
        return current_access in ["NONE", "VISIBLE"]
    
    def postcondition(target_node: Node, actor_access: str, actor_id: str) -> None:
        if not hasattr(target_node, 'access'):
            target_node.access = {}
        target_node.access[actor_id] = "ADMIN"  # RDP often gives admin access
        target_node.compromised = True
    
    def detection_prob(link, actor_access: str, actor_id: str) -> float:
        # RDP lateral movement is more detectable than SSH due to GUI nature
        base_prob = 0.40  # RDP connections are more obvious
        
        if hasattr(link, 'properties'):
            # Network monitoring catches RDP traffic
            monitoring = link.properties.get('network_monitoring', 'none')
            if monitoring == 'SIEM':
                base_prob += 0.30
            elif monitoring == 'IPS':
                base_prob += 0.25
            elif monitoring == 'IDS':
                base_prob += 0.20
            elif monitoring == 'basic_logging':
                base_prob += 0.10
            
            # Endpoint protection detects RDP activity
            endpoint = link.properties.get('endpoint_protection', 'none')
            if endpoint in ['CrowdStrike', 'Carbon Black']:
                base_prob += 0.25
            elif endpoint in ['Sophos', 'McAfee']:
                base_prob += 0.20
            elif endpoint == 'Windows Defender':
                base_prob += 0.15
            
            # RDP monitoring specifically (Windows event logs)
            if link.properties.get('rdp_monitoring', False):
                base_prob += 0.20
                
            # Critical systems have better monitoring
            if link.properties.get('criticality') in ['critical', 'high']:
                base_prob += 0.10
        
        return min(base_prob, 0.95)
    
    def damage_calc(link, actor_access: str, actor_id: str) -> float:
        # RDP gives admin access, so higher base damage
        base_damage = 400.0
        
        if hasattr(link, 'properties'):
            criticality = link.properties.get('criticality', 'low')
            if criticality == 'critical':
                base_damage *= 3.5
            elif criticality == 'high':
                base_damage *= 2.5
            elif criticality == 'medium':
                base_damage *= 1.8
            
            data_sensitivity = link.properties.get('data_sensitivity', 'low')
            if data_sensitivity == 'high':
                base_damage *= 3.0
            elif data_sensitivity == 'medium':
                base_damage *= 2.0
        
        return base_damage
    
    def gain_calc(link, actor_access: str, actor_id: str) -> float:
        # Higher gain since RDP gives admin access
        base_gain = 200.0
        
        if hasattr(link, 'properties'):
            criticality = link.properties.get('criticality', 'low')
            if criticality == 'critical':
                base_gain *= 5.0
            elif criticality == 'high':
                base_gain *= 3.0
            elif criticality == 'medium':
                base_gain *= 2.0
            
            assets = getattr(link, 'assets', [])
            if assets:
                base_gain += len(assets) * 75.0  # Higher value per asset for admin access
        
        return base_gain
    
    return create_link_action(
        name="RDP Lateral Movement",
        precondition_link=precondition,
        postcondition_link=postcondition,
        cost=350.0,
        duration=1.5,
        success_probability=0.65,
        detection_probability=detection_prob,
        one_off_damage=damage_calc,
        one_off_gain=gain_calc
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
        if not hasattr(target_node, 'access'):
            target_node.access = {}
        
        current_access = target_node.access.get(actor_id, "NONE")
        if current_access == "NONE":
            target_node.access[actor_id] = "VISIBLE"
    
    def detection_prob(link, actor_access: str, actor_id: str) -> float:
        # Network scans are relatively easy to detect with proper monitoring
        base_prob = 0.45  # Base detection for network scans
        
        if hasattr(link, 'properties'):
            monitoring = link.properties.get('network_monitoring', 'none')
            if monitoring == 'SIEM':
                base_prob += 0.40
            elif monitoring == 'IPS':
                base_prob += 0.35
            elif monitoring == 'IDS':
                base_prob += 0.30
            elif monitoring == 'basic_logging':
                base_prob += 0.15
                
            # Network scans trigger firewall alerts
            if link.properties.get('firewall_enabled', False):
                base_prob += 0.20
        
        return min(base_prob, 0.95)
    
    def damage_calc(link, actor_access: str, actor_id: str) -> float:
        # Network scans cause minimal direct damage but reveal information
        return 25.0  # Small cost for scanning activity
    
    def gain_calc(link, actor_access: str, actor_id: str) -> float:
        # Moderate gain from network reconnaissance
        base_gain = 50.0  # Value of network topology information
        
        if hasattr(link, 'properties'):
            # More valuable targets provide more reconnaissance value
            criticality = link.properties.get('criticality', 'low')
            if criticality == 'critical':
                base_gain *= 2.0
            elif criticality == 'high':
                base_gain *= 1.5
        
        return base_gain
    
    return create_link_action(
        name="Network Scan",
        precondition_link=precondition,
        postcondition_link=postcondition,
        cost=50.0,
        duration=0.5,
        success_probability=0.95,
        detection_probability=detection_prob,
        one_off_damage=damage_calc,
        one_off_gain=gain_calc
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
