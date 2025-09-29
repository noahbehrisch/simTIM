#!/usr/bin/env python3
"""
TIM Economic Model Implementation
Based on Section 4.7 of the TIM paper: Optimization objectives

Implements the formal mathematical functions:
- D(a, π̂(n)): One-off damage function  
- G(a, π̂(n)): One-off gain function
- δ(ωx(n), π̂(n)): Time-proportional damage rate
- γ(ωx(n), π̂(n)): Time-proportional gain rate
- D^total_[0,T]: Total damage calculation with time integration
- G[0,T](x): Attacker gain calculation with time integration  
- Cx,[0,T]: Action cost calculation
"""

from typing import Dict, List, Tuple, Any, Callable
from dataclasses import dataclass, field
from collections import defaultdict
import math
from src.core.graph import Node


@dataclass
class StateChangeEvent:
    """Represents a point in time when system state changed"""
    time: float
    node: Node
    actor_id: str
    change_type: str  # 'property', 'access', 'action_completion'
    old_value: Any = None
    new_value: Any = None
    action_name: str = None


@dataclass
class EconomicState:
    """Tracks economic state for TIM calculations"""
    # Time intervals where state is constant
    state_change_times: List[float] = field(default_factory=list)
    
    # Track successful attack completions per attacker
    attack_completions: Dict[str, List[Tuple[float, str, Node]]] = field(default_factory=lambda: defaultdict(list))
    
    # Track action costs per actor
    action_costs: Dict[str, List[Tuple[float, float]]] = field(default_factory=lambda: defaultdict(list))
    
    # Track state changes for time integration
    state_changes: List[StateChangeEvent] = field(default_factory=list)
    
    def add_state_change(self, time: float, node: Node, actor_id: str, change_type: str, 
                        old_value: Any = None, new_value: Any = None, action_name: str = None):
        """Record a state change event"""
        event = StateChangeEvent(time, node, actor_id, change_type, old_value, new_value, action_name)
        self.state_changes.append(event)
        
        # Update state change times for interval calculation
        if time not in self.state_change_times:
            self.state_change_times.append(time)
            self.state_change_times.sort()
    
    def add_attack_completion(self, time: float, attacker_id: str, action_name: str, target_node: Node):
        """Record successful attack completion"""
        self.attack_completions[attacker_id].append((time, action_name, target_node))
    
    def add_action_cost(self, time: float, actor_id: str, cost: float):
        """Record action cost incurred by actor"""
        self.action_costs[actor_id].append((time, cost))


class TIMEconomicEngine:
    """
    TIM Economic Model Implementation
    
    Implements the formal economic functions from TIM Section 4.7
    """
    
    def __init__(self):
        self.economic_state = EconomicState()
        
        # Economic function registries
        self.one_off_damage_functions: Dict[str, Callable] = {}
        self.one_off_gain_functions: Dict[str, Callable] = {}
        self.time_damage_functions: Dict[str, Callable] = {}
        self.time_gain_functions: Dict[str, Callable] = {}
    
    def register_economic_functions(self, action_name: str,
                                   one_off_damage_fn: Callable = None,
                                   one_off_gain_fn: Callable = None,
                                   time_damage_fn: Callable = None,
                                   time_gain_fn: Callable = None):
        """Register economic functions for a specific action"""
        if one_off_damage_fn:
            self.one_off_damage_functions[action_name] = one_off_damage_fn
        if one_off_gain_fn:
            self.one_off_gain_functions[action_name] = one_off_gain_fn
        if time_damage_fn:
            self.time_damage_functions[action_name] = time_damage_fn
        if time_gain_fn:
            self.time_gain_functions[action_name] = time_gain_fn
    
    def register_access_economic_functions(self, access_level: str,
                                         time_damage_fn: Callable = None,
                                         time_gain_fn: Callable = None):
        """Register time-proportional functions for access levels"""
        if time_damage_fn:
            self.time_damage_functions[f"access_{access_level}"] = time_damage_fn
        if time_gain_fn:
            self.time_gain_functions[f"access_{access_level}"] = time_gain_fn
    
    # Core TIM Economic Functions
    
    def D(self, action_name: str, node_properties: Dict[str, Any]) -> float:
        """
        One-off damage function: D(a, π̂(n))
        
        Args:
            action_name: Name of the attack action
            node_properties: Properties π̂(n) of the target node
            
        Returns:
            One-off damage amount
        """
        damage_fn = self.one_off_damage_functions.get(action_name, self._default_damage_function)
        return damage_fn(node_properties)
    
    def G(self, action_name: str, node_properties: Dict[str, Any]) -> float:
        """
        One-off gain function: G(a, π̂(n))
        
        Args:
            action_name: Name of the attack action  
            node_properties: Properties π̂(n) of the target node
            
        Returns:
            One-off gain amount
        """
        gain_fn = self.one_off_gain_functions.get(action_name, self._default_gain_function)
        return gain_fn(node_properties)
    
    def delta(self, access_level: str, node_properties: Dict[str, Any]) -> float:
        """
        Time-proportional damage rate: δ(ωx(n), π̂(n))
        
        Args:
            access_level: Attacker's access level ωx(n)
            node_properties: Properties π̂(n) of the node
            
        Returns:
            Damage rate per unit time
        """
        damage_fn = self.time_damage_functions.get(f"access_{access_level}", self._default_time_damage_function)
        return damage_fn(access_level, node_properties)
    
    def gamma(self, access_level: str, node_properties: Dict[str, Any]) -> float:
        """
        Time-proportional gain rate: γ(ωx(n), π̂(n))
        
        Args:
            access_level: Attacker's access level ωx(n)  
            node_properties: Properties π̂(n) of the node
            
        Returns:
            Gain rate per unit time
        """
        gain_fn = self.time_gain_functions.get(f"access_{access_level}", self._default_time_gain_function)
        return gain_fn(access_level, node_properties)
    
    # TIM Integration Formulas
    
    def calculate_total_damage(self, time_interval: Tuple[float, float], 
                              network_nodes: List[Node],
                              attacker_ids: List[str]) -> float:
        """
        Calculate D^total_[0,T] per TIM formula:
        
        D^total_[0,T] = Σ_n Σ_x Σ_i δ(ti ωx(n), ti π̂(n)) · (ti+1 - ti) + 
                       Σ_x Σ_j D(ax,j, τx,j π̂(nx,j))
        
        Args:
            time_interval: [0, T] time interval
            network_nodes: All nodes N in the network  
            attacker_ids: All attacker IDs X^(att)
            
        Returns:
            Total damage in time interval
        """
        t_start, t_end = time_interval
        
        # Get time points where state changed
        state_times = [t for t in self.economic_state.state_change_times 
                      if t_start <= t <= t_end]
        
        # Add interval boundaries
        if t_start not in state_times:
            state_times.insert(0, t_start)
        if t_end not in state_times:
            state_times.append(t_end)
        
        total_damage = 0.0
        
        # Part 1: Time-proportional damage integration
        # Σ_n Σ_x Σ_i δ(ti ωx(n), ti π̂(n)) · (ti+1 - ti)
        for i in range(len(state_times) - 1):
            ti = state_times[i]
            ti_plus_1 = state_times[i + 1] 
            interval_duration = ti_plus_1 - ti
            
            for node in network_nodes:
                for attacker_id in attacker_ids:
                    # Get access level at time ti
                    access_level = self._get_access_at_time(attacker_id, node, ti)
                    # Get node properties at time ti  
                    node_props = self._get_node_properties_at_time(node, ti)
                    
                    # Calculate time-proportional damage
                    damage_rate = self.delta(access_level, node_props)
                    interval_damage = damage_rate * interval_duration
                    total_damage += interval_damage
        
        # Part 2: One-off damage from successful attacks
        # Σ_x Σ_j D(ax,j, τx,j π̂(nx,j))
        for attacker_id in attacker_ids:
            completions = self.economic_state.attack_completions.get(attacker_id, [])
            for completion_time, action_name, target_node in completions:
                if t_start <= completion_time <= t_end:
                    # Get node properties at completion time
                    node_props = self._get_node_properties_at_time(target_node, completion_time)
                    one_off_damage = self.D(action_name, node_props)
                    total_damage += one_off_damage
        
        return total_damage
    
    def calculate_attacker_gain(self, attacker_id: str, time_interval: Tuple[float, float],
                               network_nodes: List[Node]) -> float:
        """
        Calculate G[0,T](x) per TIM formula:
        
        G[0,T](x) = Σ_n Σ_i γ(ti ωx(n), ti π̂(n)) · (ti+1 - ti) + 
                   Σ_j G(ax,j, τx,j π̂(nx,j))
        
        Args:
            attacker_id: Attacker ID x
            time_interval: [0, T] time interval
            network_nodes: All nodes N in network
            
        Returns:
            Total gain for attacker in time interval
        """
        t_start, t_end = time_interval
        
        # Get time points where state changed
        state_times = [t for t in self.economic_state.state_change_times 
                      if t_start <= t <= t_end]
        
        # Add interval boundaries
        if t_start not in state_times:
            state_times.insert(0, t_start)
        if t_end not in state_times:
            state_times.append(t_end)
        
        total_gain = 0.0
        
        # Part 1: Time-proportional gain integration  
        # Σ_n Σ_i γ(ti ωx(n), ti π̂(n)) · (ti+1 - ti)
        for i in range(len(state_times) - 1):
            ti = state_times[i]
            ti_plus_1 = state_times[i + 1]
            interval_duration = ti_plus_1 - ti
            
            for node in network_nodes:
                # Get access level at time ti
                access_level = self._get_access_at_time(attacker_id, node, ti)
                # Get node properties at time ti
                node_props = self._get_node_properties_at_time(node, ti)
                
                # Calculate time-proportional gain
                gain_rate = self.gamma(access_level, node_props)
                interval_gain = gain_rate * interval_duration
                total_gain += interval_gain
        
        # Part 2: One-off gain from successful attacks
        # Σ_j G(ax,j, τx,j π̂(nx,j))
        completions = self.economic_state.attack_completions.get(attacker_id, [])
        for completion_time, action_name, target_node in completions:
            if t_start <= completion_time <= t_end:
                # Get node properties at completion time
                node_props = self._get_node_properties_at_time(target_node, completion_time)
                one_off_gain = self.G(action_name, node_props)
                total_gain += one_off_gain
        
        return total_gain
    
    def calculate_actor_costs(self, actor_id: str, time_interval: Tuple[float, float]) -> float:
        """
        Calculate Cx,[0,T] per TIM formula:
        
        Cx,[0,T] = Σ_{a∈Ax,[0,T]} ca
        
        Args:
            actor_id: Actor ID x
            time_interval: [0, T] time interval
            
        Returns:
            Total cost incurred by actor in time interval
        """
        t_start, t_end = time_interval
        
        costs = self.economic_state.action_costs.get(actor_id, [])
        total_cost = sum(cost for time, cost in costs 
                        if t_start <= time <= t_end)
        
        return total_cost
    
    # TIM Optimization Objectives
    
    def defender_objective(self, time_interval: Tuple[float, float],
                          network_nodes: List[Node], attacker_ids: List[str]) -> float:
        """
        Defender objective: minimize D^total_[0,T] + Cdefender,[0,T]
        
        Returns:
            Value to minimize (damage + defense costs)
        """
        total_damage = self.calculate_total_damage(time_interval, network_nodes, attacker_ids)
        defense_costs = self.calculate_actor_costs("defender", time_interval)
        
        return total_damage + defense_costs
    
    def attacker_objective(self, attacker_id: str, time_interval: Tuple[float, float],
                          network_nodes: List[Node]) -> float:
        """
        Attacker objective: maximize G[0,T](x) - Cx,[0,T]
        
        Args:
            attacker_id: Attacker ID x
            
        Returns:
            Value to maximize (gain - attack costs)
        """
        total_gain = self.calculate_attacker_gain(attacker_id, time_interval, network_nodes)
        attack_costs = self.calculate_actor_costs(attacker_id, time_interval)
        
        return total_gain - attack_costs
    
    # Event Recording Interface
    
    def record_property_change(self, time: float, node: Node, property_name: str, 
                             old_value: Any, new_value: Any):
        """Record node property change for economic calculations"""
        self.economic_state.add_state_change(
            time, node, "system", "property", old_value, new_value
        )
    
    def record_access_change(self, time: float, node: Node, actor_id: str,
                           old_access: str, new_access: str):
        """Record access level change for economic calculations"""  
        self.economic_state.add_state_change(
            time, node, actor_id, "access", old_access, new_access
        )
    
    def record_action_completion(self, time: float, attacker_id: str, action_name: str,
                               target_node: Node, success: bool):
        """Record action completion for economic calculations"""
        if success:
            self.economic_state.add_attack_completion(time, attacker_id, action_name, target_node)
    
    def record_action_cost(self, time: float, actor_id: str, cost: float):
        """Record action cost for economic calculations"""
        self.economic_state.add_action_cost(time, actor_id, cost)
    
    # Helper Methods
    
    def _get_access_at_time(self, actor_id: str, node: Node, time: float) -> str:
        """Get actor's access level to node at specific time"""
        # Find most recent access change before or at time
        relevant_changes = [
            change for change in self.economic_state.state_changes
            if (change.time <= time and change.node == node and 
                change.actor_id == actor_id and change.change_type == "access")
        ]
        
        if relevant_changes:
            # Get most recent change
            latest_change = max(relevant_changes, key=lambda c: c.time)
            return latest_change.new_value
        else:
            # Default access level
            return node.access.get(actor_id, "NONE")
    
    def _get_node_properties_at_time(self, node: Node, time: float) -> Dict[str, Any]:
        """Get node properties at specific time"""
        # Start with current properties
        properties = {
            'vulnerabilities': list(getattr(node, 'vulnerabilities', [])),
            'assets': list(getattr(node, 'assets', [])),
            'software': dict(getattr(node, 'software', {})),
            'compromised': getattr(node, 'compromised', False),
            'repaired': getattr(node, 'repaired', False)
        }
        
        # Apply any property changes that occurred before or at this time
        relevant_changes = [
            change for change in self.economic_state.state_changes
            if (change.time <= time and change.node == node and 
                change.change_type == "property")
        ]
        
        # Apply changes in chronological order
        for change in sorted(relevant_changes, key=lambda c: c.time):
            # This would need to be enhanced based on specific property change tracking
            pass
        
        return properties
    
    # Default Economic Functions
    
    def _default_damage_function(self, node_properties: Dict[str, Any]) -> float:
        """Default one-off damage calculation"""
        # Base damage varies by asset sensitivity
        assets = node_properties.get('assets', [])
        base_damage = len(assets) * 1000.0  # $1k per asset
        
        # Multiplier for high-value assets
        if any('sensitive' in str(asset).lower() or 'critical' in str(asset).lower() 
               for asset in assets):
            base_damage *= 10.0
        
        return base_damage
    
    def _default_gain_function(self, node_properties: Dict[str, Any]) -> float:
        """Default one-off gain calculation"""
        # Attacker gain is typically less than defender damage
        return self._default_damage_function(node_properties) * 0.3
    
    def _default_time_damage_function(self, access_level: str, node_properties: Dict[str, Any]) -> float:
        """Default time-proportional damage rate"""
        if access_level in ["NONE", "VISIBLE"]:
            return 0.0
        
        assets = node_properties.get('assets', [])
        base_rate = len(assets) * 10.0  # $10 per asset per time unit
        
        # Higher damage for admin access
        if access_level == "ADMIN":
            base_rate *= 5.0
        elif access_level == "USER":
            base_rate *= 2.0
        
        return base_rate
    
    def _default_time_gain_function(self, access_level: str, node_properties: Dict[str, Any]) -> float:
        """Default time-proportional gain rate"""
        # Attacker gain rate is typically less than damage rate
        return self._default_time_damage_function(access_level, node_properties) * 0.2


def register_realistic_economic_functions():
    """Register TIM-compliant economic functions for common attack scenarios"""
    
    # Tapestry Attack (Remote Code Execution)
    def tapestry_damage(node_props):
        """Tapestry RCE causes significant damage due to web server compromise"""
        base_damage = 5000.0  # Base web server compromise cost
        
        # Additional damage for hosted applications and data
        assets = node_props.get('assets', [])
        asset_damage = len(assets) * 2500.0
        
        # Critical multiplier for customer-facing services
        if any('website' in str(asset).lower() or 'portal' in str(asset).lower() 
               for asset in assets):
            asset_damage *= 3.0
            
        return base_damage + asset_damage
    
    def tapestry_gain(node_props):
        """Attacker gains from Tapestry compromise (data, access)"""
        return tapestry_damage(node_props) * 0.25  # 25% of damage as gain
    
    # Data Exfiltration  
    def data_exfiltration_damage(node_props):
        """Data breach causes massive damage per TIM example (150k USD)"""
        assets = node_props.get('assets', [])
        
        # Base damage for any data breach
        base_damage = 50000.0
        
        # Scale by data volume and sensitivity
        sensitive_assets = [a for a in assets if 'sensitive' in str(a).lower() or 'data' in str(a).lower()]
        damage_per_asset = 25000.0  # $25k per sensitive data asset
        
        total_damage = base_damage + len(sensitive_assets) * damage_per_asset
        
        # Cap at realistic maximum
        return min(total_damage, 500000.0)
    
    def data_exfiltration_gain(node_props):
        """Ransom/sale value per TIM example (100k USD)"""  
        damage = data_exfiltration_damage(node_props)
        return min(damage * 0.6, 100000.0)  # Cap at TIM example value
    
    # Administrative access ongoing damage
    def admin_access_time_damage(access_level, node_props):
        """Ongoing damage while attacker has admin access"""
        if access_level != "ADMIN":
            return 0.0
            
        # Continuous operational disruption
        assets = node_props.get('assets', [])
        base_rate = 100.0  # $100/time unit for disruption
        
        # Scale by asset criticality
        critical_assets = [a for a in assets if 'critical' in str(a).lower()]
        asset_rate = len(critical_assets) * 250.0
        
        return base_rate + asset_rate
    
    def admin_access_time_gain(access_level, node_props):
        """Ongoing gain while attacker maintains access"""
        if access_level != "ADMIN":
            return 0.0
            
        # Lower gain rate than damage rate
        damage_rate = admin_access_time_damage(access_level, node_props)
        return damage_rate * 0.15
    
    # Register functions with the economic engine
    tim_economic_engine.register_economic_functions(
        "Tapestry attack",
        one_off_damage_fn=tapestry_damage,
        one_off_gain_fn=tapestry_gain
    )
    
    tim_economic_engine.register_economic_functions(
        "Data exfiltration",  
        one_off_damage_fn=data_exfiltration_damage,
        one_off_gain_fn=data_exfiltration_gain
    )
    
    tim_economic_engine.register_access_economic_functions(
        "ADMIN",
        time_damage_fn=admin_access_time_damage,
        time_gain_fn=admin_access_time_gain
    )


# Economic functions will be registered when first used


# Global economic engine instance
tim_economic_engine = TIMEconomicEngine()

def register_realistic_economic_functions():
    """Register realistic economic functions for TIM analysis"""
    pass
