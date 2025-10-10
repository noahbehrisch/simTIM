from typing import Dict, Any, List, Tuple
from src.core.graph import Node

class EconomicParameters:
    """Configuration parameters for economic calculations."""
    def __init__(self):
        # Time-proportional damage rates (per time unit)
        self.admin_access_damage_rate = 50.0
        self.user_access_damage_rate = 10.0
        
        # Property multipliers
        self.data_sensitivity_multipliers = {
            'high': 3.0,
            'medium': 1.5,
            'low': 1.0
        }
        
        self.criticality_multipliers = {
            'critical': 2.0,
            'high': 1.5,
            'medium': 1.3,
            'low': 1.0
        }
        
        # Asset value scaling
        self.asset_value_factor = 0.5  # Additional multiplier per asset
        
        # Attacker gain as fraction of defender damage
        self.attacker_gain_ratio = 0.35
        
        # Base damage for critical system compromise
        self.critical_system_base_damage = 1000.0
        self.critical_system_multiplier = 5.0
    
    def to_dict(self) -> dict:
        """Export parameters as dictionary for easy customization."""
        return {
            'admin_access_damage_rate': self.admin_access_damage_rate,
            'user_access_damage_rate': self.user_access_damage_rate,
            'data_sensitivity_multipliers': self.data_sensitivity_multipliers.copy(),
            'criticality_multipliers': self.criticality_multipliers.copy(),
            'asset_value_factor': self.asset_value_factor,
            'attacker_gain_ratio': self.attacker_gain_ratio,
            'critical_system_base_damage': self.critical_system_base_damage,
            'critical_system_multiplier': self.critical_system_multiplier
        }
    
    @classmethod
    def from_dict(cls, config: dict):
        """Create parameters from dictionary configuration."""
        params = cls()
        for key, value in config.items():
            if hasattr(params, key):
                setattr(params, key, value)
        return params


class SimpleEconomicModel:
    """
    Economic model implementing TIM paper Section 4.7 "Optimization Objectives"
    
    Tracks both:
    - One-off damage/gain: D(a, π̂) and G(a, π̂) from successful attacks
    - Time-proportional damage/gain: δ(ω, π̂) and γ(ω, π̂) accumulated over time
    
    Reference: TIM paper equations for D[0,T]^total and G[0,T](x)
    """
    
    def __init__(self, parameters: EconomicParameters = None):
        """Initialize economic model with configurable parameters."""
        self.parameters = parameters or EconomicParameters()
        
        self.total_damage = 0.0
        self.actor_costs = {}
        self.actor_gains = {}
        self.action_history = []
        
        # Time-proportional tracking (TIM paper Section 4.7)
        self.time_proportional_damage = 0.0
        self.time_proportional_gains = {}  # Per attacker
        
        # Track access state changes for time-interval calculations
        self.access_state_changes = []  # List of (time, node_id, actor_id, old_access, new_access)
        self.property_state_changes = []  # List of (time, node_id, property, old_value, new_value)
        
        # Last time we accumulated time-proportional impact
        self.last_accumulation_time = 0.0
    
    def record_action_cost(self, actor_id: str, cost: float):
        if actor_id not in self.actor_costs:
            self.actor_costs[actor_id] = 0.0
        self.actor_costs[actor_id] += cost
    
    def record_damage(self, damage: float):
        self.total_damage += damage
    
    def record_gain(self, actor_id: str, gain: float):
        if actor_id not in self.actor_gains:
            self.actor_gains[actor_id] = 0.0
        self.actor_gains[actor_id] += gain
    
    def record_action_impact(self, time: float, actor_id: str, action_name: str, 
                           cost: float, damage: float = 0.0, gain: float = 0.0):
        self.record_action_cost(actor_id, cost)
        if damage > 0:
            self.record_damage(damage)
        if gain > 0:
            self.record_gain(actor_id, gain)
        
        self.action_history.append((time, actor_id, action_name, cost, damage, gain))
    
    def record_access_change(self, time: float, node_id: str, actor_id: str, 
                            old_access: str, new_access: str):
        """
        Record when an actor's access to a node changes.
        Critical for calculating time-proportional damage/gain per TIM paper.
        
        Reference: TIM paper Section 4.7 - tracks ti (state change times)
        """
        self.access_state_changes.append((time, node_id, actor_id, old_access, new_access))
    
    def record_property_change(self, time: float, node_id: str, property_name: str,
                              old_value: Any, new_value: Any):
        """
        Record when a node property changes.
        Critical for calculating time-proportional damage/gain per TIM paper.
        
        Reference: TIM paper Section 4.7 - tracks ti (state change times)
        """
        self.property_state_changes.append((time, node_id, property_name, old_value, new_value))
    
    def accumulate_time_proportional_impact(self, current_time: float, 
                                           all_nodes: List[Node],
                                           attacker_actors: List[Any]):
        """
        Accumulate time-proportional damage and gain since last accumulation.
        
        Implements TIM paper Section 4.7 formula:
        D[0,T]^total = Σ(i=0 to k) Σ(n∈N) Σ(x∈X^att) δ(ti·ωx(n), ti·π̂(n)) · (ti+1 - ti)
        
        Args:
            current_time: Current simulation time
            all_nodes: All nodes in the system
            attacker_actors: List of attacker actors
        """
        if current_time <= self.last_accumulation_time:
            return
        
        delta_t = current_time - self.last_accumulation_time
        
        # For each attacker
        for attacker in attacker_actors:
            attacker_id = attacker.id
            
            # For each node
            for node in all_nodes:
                # Get attacker's current access to this node
                access = node.access.get(attacker_id, "NONE")
                
                # Calculate δ(ω, π̂) - damage rate for this access/property combination
                damage_rate = calculate_delta(access, node, self.parameters)
                
                # Calculate γ(ω, π̂) - gain rate for this access/property combination
                gain_rate = calculate_gamma(access, node, self.parameters)
                
                # Accumulate over time interval [last_time, current_time)
                if damage_rate > 0:
                    self.time_proportional_damage += damage_rate * delta_t
                    self.total_damage += damage_rate * delta_t
                
                if gain_rate > 0:
                    if attacker_id not in self.time_proportional_gains:
                        self.time_proportional_gains[attacker_id] = 0.0
                    self.time_proportional_gains[attacker_id] += gain_rate * delta_t
                    
                    # Also add to total gains
                    if attacker_id not in self.actor_gains:
                        self.actor_gains[attacker_id] = 0.0
                    self.actor_gains[attacker_id] += gain_rate * delta_t
        
        self.last_accumulation_time = current_time
    
    def get_attacker_objective(self, actor_id: str) -> float:
        """
        Calculate attacker objective: G[0,T](x) - Cx,[0,T]
        
        Reference: TIM paper Section 4.7
        """
        gains = self.actor_gains.get(actor_id, 0.0)
        costs = self.actor_costs.get(actor_id, 0.0)
        return gains - costs
    
    def get_defender_objective(self, actor_id: str) -> float:
        """
        Calculate defender objective: -(D[0,T]^total + Cdefender,[0,T])
        
        Reference: TIM paper Section 4.7
        """
        costs = self.actor_costs.get(actor_id, 0.0)
        return -(self.total_damage + costs)
    
    def get_total_costs(self, actor_id: str = None) -> float:
        if actor_id:
            return self.actor_costs.get(actor_id, 0.0)
        return sum(self.actor_costs.values())
    
    def get_total_gains(self, actor_id: str = None) -> float:
        if actor_id:
            return self.actor_gains.get(actor_id, 0.0)
        return sum(self.actor_gains.values())
    
    def get_summary(self) -> Dict[str, Any]:
        return {
            'total_damage': self.total_damage,
            'time_proportional_damage': self.time_proportional_damage,
            'one_off_damage': self.total_damage - self.time_proportional_damage,
            'total_costs': self.get_total_costs(),
            'total_gains': self.get_total_gains(),
            'time_proportional_gains': dict(self.time_proportional_gains),
            'actor_costs': dict(self.actor_costs),
            'actor_gains': dict(self.actor_gains),
            'num_actions': len(self.action_history),
            'num_access_changes': len(self.access_state_changes),
            'num_property_changes': len(self.property_state_changes)
        }


def calculate_delta(access: str, node: Node, parameters: EconomicParameters = None) -> float:
    """
    Calculate time-proportional damage rate δ(ω, π̂(n)).
    
    Per TIM paper Section 4.7:
    "δ(ωx(n), π̂(n)) is the amount of damage that x generates via node n per unit time"
    
    Args:
        access: Actor's access level to the node (NONE, VISIBLE, USER, ADMIN)
        node: The node being accessed
        parameters: Economic parameters (uses defaults if None)
        
    Returns:
        Damage rate per time unit (e.g., USD per day)
    """
    if parameters is None:
        parameters = EconomicParameters()
        
    # No damage if no access
    if access in ["NONE", "VISIBLE"]:
        return 0.0
    
    # Base damage rate depends on access level
    if access == "ADMIN":
        base_rate = parameters.admin_access_damage_rate
    elif access == "USER":
        base_rate = parameters.user_access_damage_rate
    else:
        return 0.0
    
    # Multiply by node value factors
    asset_count = len(getattr(node, 'assets', []))
    if asset_count > 0:
        base_rate *= (1 + asset_count * parameters.asset_value_factor)
    
    # High-value properties increase damage rate
    properties = getattr(node, 'properties', {})
    
    # Data sensitivity multiplier
    data_sensitivity = properties.get('data_sensitivity', 'low')
    base_rate *= parameters.data_sensitivity_multipliers.get(data_sensitivity, 1.0)
    
    # Criticality multiplier
    criticality = properties.get('criticality', 'low')
    base_rate *= parameters.criticality_multipliers.get(criticality, 1.0)
    
    # Data amount affects ongoing damage (e.g., ongoing data exfiltration)
    data_amount = properties.get('data_amount', 0)
    if data_amount > 0:
        # Scale with log to avoid excessive values
        import math
        base_rate *= (1 + math.log10(data_amount + 1) * 0.1)
    
    return base_rate


def calculate_gamma(access: str, node: Node, parameters: EconomicParameters = None) -> float:
    """
    Calculate time-proportional gain rate γ(ω, π̂(n)).
    
    Per TIM paper Section 4.7:
    "γ(ωx(n), π̂(n)) is the gain of x from n per unit time"
    
    Args:
        access: Actor's access level to the node (NONE, VISIBLE, USER, ADMIN)
        node: The node being accessed
        parameters: Economic parameters (uses defaults if None)
        
    Returns:
        Gain rate per time unit (e.g., USD per day)
    """
    if parameters is None:
        parameters = EconomicParameters()
        
    # Attacker gain is typically a fraction of defender damage
    damage_rate = calculate_delta(access, node, parameters)
    
    # Use configurable gain ratio
    return damage_rate * parameters.attacker_gain_ratio


def calculate_action_damage(action_name: str, node: Node, parameters: EconomicParameters = None) -> float:
    """
    Calculate one-off damage D(a, π̂(n)) from successful attack action.
    
    Per TIM paper Section 4.7:
    "D(a, π̂(n)) is the amount of one-off damage that x generates by 
    successfully performing attack a on node n"
    
    Args:
        action_name: Name of the attack action
        node: The target node
        parameters: Economic parameters (uses defaults if None)
        
    Returns:
        One-off damage amount (e.g., USD)
    """
    if parameters is None:
        parameters = EconomicParameters()
        
    base_damage = parameters.critical_system_base_damage
    
    asset_multiplier = len(getattr(node, 'assets', [])) * 500.0
    
    if 'exfiltration' in action_name.lower() or 'tapestry' in action_name.lower():
        base_damage *= parameters.critical_system_multiplier
    
    return base_damage + asset_multiplier


def calculate_action_gain(action_name: str, node: Node, parameters: EconomicParameters = None) -> float:
    """
    Calculate one-off gain G(a, π̂(n)) from successful attack action.
    
    Per TIM paper Section 4.7:
    "G(a, π̂(n)) is the one-off gain of x from successfully performing attack a on node n"
    
    Args:
        action_name: Name of the attack action
        node: The target node
        
    Returns:
        One-off gain amount (e.g., USD)
    """
    damage = calculate_action_damage(action_name, node)
    return damage * 0.3


economic_model = SimpleEconomicModel()