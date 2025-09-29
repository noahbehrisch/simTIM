from typing import Dict, List, Tuple, Any, Callable
from dataclasses import dataclass, field
from collections import defaultdict
import math
from src.core.graph import Node

@dataclass

class StateChangeEvent:
    time: float
    node: Node
    actor_id: str
    change_type: str
    old_value: Any = None
    new_value: Any = None
    action_name: str = None
@dataclass

class EconomicState:
    state_change_times: List[float] = field(default_factory=list)
    attack_completions: Dict[str, List[Tuple[float, str, Node]]] = field(default_factory=lambda: defaultdict(list))
    action_costs: Dict[str, List[Tuple[float, float]]] = field(default_factory=lambda: defaultdict(list))
    state_changes: List[StateChangeEvent] = field(default_factory=list)
    def add_state_change(self, time: float, node: Node, actor_id: str, change_type: str, 
                        old_value: Any = None, new_value: Any = None, action_name: str = None):
        event = StateChangeEvent(time, node, actor_id, change_type, old_value, new_value, action_name)
        self.state_changes.append(event)
        if time not in self.state_change_times:
            self.state_change_times.append(time)
            self.state_change_times.sort()

    def add_attack_completion(self, time: float, attacker_id: str, action_name: str, target_node: Node):
        self.attack_completions[attacker_id].append((time, action_name, target_node))

    def add_action_cost(self, time: float, actor_id: str, cost: float):
        self.action_costs[actor_id].append((time, cost))

class TIMEconomicEngine:
    def __init__(self):
        self.economic_state = EconomicState()
        self.one_off_damage_functions: Dict[str, Callable] = {}
        self.one_off_gain_functions: Dict[str, Callable] = {}
        self.time_damage_functions: Dict[str, Callable] = {}
        self.time_gain_functions: Dict[str, Callable] = {}
    def register_economic_functions(self, action_name: str,
                                   one_off_damage_fn: Callable = None,
                                   one_off_gain_fn: Callable = None,
                                   time_damage_fn: Callable = None,
                                   time_gain_fn: Callable = None):
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
        if time_damage_fn:
            self.time_damage_functions[f"access_{access_level}"] = time_damage_fn
        if time_gain_fn:
            self.time_gain_functions[f"access_{access_level}"] = time_gain_fn

    def D(self, action_name: str, node_properties: Dict[str, Any]) -> float:
        damage_fn = self.one_off_damage_functions.get(action_name, self._default_damage_function)
        return damage_fn(node_properties)

    def G(self, action_name: str, node_properties: Dict[str, Any]) -> float:
        gain_fn = self.one_off_gain_functions.get(action_name, self._default_gain_function)
        return gain_fn(node_properties)

    def delta(self, access_level: str, node_properties: Dict[str, Any]) -> float:
        damage_fn = self.time_damage_functions.get(f"access_{access_level}", self._default_time_damage_function)
        return damage_fn(access_level, node_properties)

    def gamma(self, access_level: str, node_properties: Dict[str, Any]) -> float:
        gain_fn = self.time_gain_functions.get(f"access_{access_level}", self._default_time_gain_function)
        return gain_fn(access_level, node_properties)
    def calculate_total_damage(self, time_interval: Tuple[float, float], 
                              network_nodes: List[Node],
                              attacker_ids: List[str]) -> float:
        t_start, t_end = time_interval
        state_times = [t for t in self.economic_state.state_change_times 
                      if t_start <= t <= t_end]
        if t_start not in state_times:
            state_times.insert(0, t_start)
        if t_end not in state_times:
            state_times.append(t_end)
        total_damage = 0.0
        for i in range(len(state_times) - 1):
            ti = state_times[i]
            ti_plus_1 = state_times[i + 1] 
            interval_duration = ti_plus_1 - ti
            for node in network_nodes:
                for attacker_id in attacker_ids:
                    access_level = self._get_access_at_time(attacker_id, node, ti)
                    node_props = self._get_node_properties_at_time(node, ti)
                    damage_rate = self.delta(access_level, node_props)
                    interval_damage = damage_rate * interval_duration
                    total_damage += interval_damage
        for attacker_id in attacker_ids:
            completions = self.economic_state.attack_completions.get(attacker_id, [])
            for completion_time, action_name, target_node in completions:
                if t_start <= completion_time <= t_end:
                    node_props = self._get_node_properties_at_time(target_node, completion_time)
                    one_off_damage = self.D(action_name, node_props)
                    total_damage += one_off_damage
        return total_damage
    def calculate_attacker_gain(self, attacker_id: str, time_interval: Tuple[float, float],
                               network_nodes: List[Node]) -> float:
        t_start, t_end = time_interval
        state_times = [t for t in self.economic_state.state_change_times 
                      if t_start <= t <= t_end]
        if t_start not in state_times:
            state_times.insert(0, t_start)
        if t_end not in state_times:
            state_times.append(t_end)
        total_gain = 0.0
        for i in range(len(state_times) - 1):
            ti = state_times[i]
            ti_plus_1 = state_times[i + 1]
            interval_duration = ti_plus_1 - ti
            for node in network_nodes:
                access_level = self._get_access_at_time(attacker_id, node, ti)
                node_props = self._get_node_properties_at_time(node, ti)
                gain_rate = self.gamma(access_level, node_props)
                interval_gain = gain_rate * interval_duration
                total_gain += interval_gain
        completions = self.economic_state.attack_completions.get(attacker_id, [])
        for completion_time, action_name, target_node in completions:
            if t_start <= completion_time <= t_end:
                node_props = self._get_node_properties_at_time(target_node, completion_time)
                one_off_gain = self.G(action_name, node_props)
                total_gain += one_off_gain
        return total_gain

    def calculate_actor_costs(self, actor_id: str, time_interval: Tuple[float, float]) -> float:
        t_start, t_end = time_interval
        costs = self.economic_state.action_costs.get(actor_id, [])
        total_cost = sum(cost for time, cost in costs 
                        if t_start <= time <= t_end)
        return total_cost
    def defender_objective(self, time_interval: Tuple[float, float],
                          network_nodes: List[Node], attacker_ids: List[str]) -> float:
        total_damage = self.calculate_total_damage(time_interval, network_nodes, attacker_ids)
        defense_costs = self.calculate_actor_costs("defender", time_interval)
        return total_damage + defense_costs
    def attacker_objective(self, attacker_id: str, time_interval: Tuple[float, float],
                          network_nodes: List[Node]) -> float:
        total_gain = self.calculate_attacker_gain(attacker_id, time_interval, network_nodes)
        attack_costs = self.calculate_actor_costs(attacker_id, time_interval)
        return total_gain - attack_costs
    def record_property_change(self, time: float, node: Node, property_name: str, 
                             old_value: Any, new_value: Any):
        self.economic_state.add_state_change(
            time, node, "system", "property", old_value, new_value
        )
    def record_access_change(self, time: float, node: Node, actor_id: str,
                           old_access: str, new_access: str):
        self.economic_state.add_state_change(
            time, node, actor_id, "access", old_access, new_access
        )
    def record_action_completion(self, time: float, attacker_id: str, action_name: str,
                               target_node: Node, success: bool):
        if success:
            self.economic_state.add_attack_completion(time, attacker_id, action_name, target_node)

    def record_action_cost(self, time: float, actor_id: str, cost: float):
        self.economic_state.add_action_cost(time, actor_id, cost)

    def _get_access_at_time(self, actor_id: str, node: Node, time: float) -> str:
        relevant_changes = [
            change for change in self.economic_state.state_changes
            if (change.time <= time and change.node == node and 
                change.actor_id == actor_id and change.change_type == "access")
        ]
        if relevant_changes:
            latest_change = max(relevant_changes, key=lambda c: c.time)
            return latest_change.new_value
        else:
            return node.access.get(actor_id, "NONE")

    def _get_node_properties_at_time(self, node: Node, time: float) -> Dict[str, Any]:
        properties = {
            'vulnerabilities': list(getattr(node, 'vulnerabilities', [])),
            'assets': list(getattr(node, 'assets', [])),
            'software': dict(getattr(node, 'software', {})),
            'compromised': getattr(node, 'compromised', False),
            'repaired': getattr(node, 'repaired', False)
        }
        relevant_changes = [
            change for change in self.economic_state.state_changes
            if (change.time <= time and change.node == node and 
                change.change_type == "property")
        ]
        for change in sorted(relevant_changes, key=lambda c: c.time):
            pass
        return properties

    def _default_damage_function(self, node_properties: Dict[str, Any]) -> float:
        assets = node_properties.get('assets', [])
        base_damage = len(assets) * 1000.0
        if any('sensitive' in str(asset).lower() or 'critical' in str(asset).lower() 
               for asset in assets):
            base_damage *= 10.0
        return base_damage

    def _default_gain_function(self, node_properties: Dict[str, Any]) -> float:
        return self._default_damage_function(node_properties) * 0.3

    def _default_time_damage_function(self, access_level: str, node_properties: Dict[str, Any]) -> float:
        if access_level in ["NONE", "VISIBLE"]:
            return 0.0
        assets = node_properties.get('assets', [])
        base_rate = len(assets) * 10.0
        if access_level == "ADMIN":
            base_rate *= 5.0
        elif access_level == "USER":
            base_rate *= 2.0
        return base_rate

    def _default_time_gain_function(self, access_level: str, node_properties: Dict[str, Any]) -> float:
        return self._default_time_damage_function(access_level, node_properties) * 0.2

def register_realistic_economic_functions():
    def tapestry_damage(node_props):
        base_damage = 5000.0
        assets = node_props.get('assets', [])
        asset_damage = len(assets) * 2500.0
        if any('website' in str(asset).lower() or 'portal' in str(asset).lower() 
               for asset in assets):
            asset_damage *= 3.0
        return base_damage + asset_damage

    def tapestry_gain(node_props):
        return tapestry_damage(node_props) * 0.25

    def data_exfiltration_damage(node_props):
        assets = node_props.get('assets', [])
        base_damage = 50000.0
        sensitive_assets = [a for a in assets if 'sensitive' in str(a).lower() or 'data' in str(a).lower()]
        damage_per_asset = 25000.0
        total_damage = base_damage + len(sensitive_assets) * damage_per_asset
        return min(total_damage, 500000.0)

    def data_exfiltration_gain(node_props):
        damage = data_exfiltration_damage(node_props)
        return min(damage * 0.6, 100000.0)

    def admin_access_time_damage(access_level, node_props):
        if access_level != "ADMIN":
            return 0.0
        assets = node_props.get('assets', [])
        base_rate = 100.0
        critical_assets = [a for a in assets if 'critical' in str(a).lower()]
        asset_rate = len(critical_assets) * 250.0
        return base_rate + asset_rate

    def admin_access_time_gain(access_level, node_props):
        if access_level != "ADMIN":
            return 0.0
        damage_rate = admin_access_time_damage(access_level, node_props)
        return damage_rate * 0.15
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
tim_economic_engine = TIMEconomicEngine()

def register_realistic_economic_functions():
    pass