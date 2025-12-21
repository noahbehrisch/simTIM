from typing import Dict, Any, List, Tuple
from src.core.graph import Node
from src.core.access_utils import get_node_access
from src.core.access_levels import NodeAccessLevel

class EconomicParameters:

    def __init__(self):
        self.admin_access_damage_rate = 50.0
        self.user_access_damage_rate = 10.0
        self.data_sensitivity_multipliers = {'high': 3.0, 'medium': 1.5, 'low': 1.0}
        self.criticality_multipliers = {'critical': 2.0, 'high': 1.5, 'medium': 1.3, 'low': 1.0}
        self.asset_value_factor = 0.5
        self.attacker_gain_ratio = 0.35
        self.critical_system_base_damage = 1000.0
        self.critical_system_multiplier = 5.0

    def to_dict(self) -> dict:
        return {'admin_access_damage_rate': self.admin_access_damage_rate, 'user_access_damage_rate': self.user_access_damage_rate, 'data_sensitivity_multipliers': self.data_sensitivity_multipliers.copy(), 'criticality_multipliers': self.criticality_multipliers.copy(), 'asset_value_factor': self.asset_value_factor, 'attacker_gain_ratio': self.attacker_gain_ratio, 'critical_system_base_damage': self.critical_system_base_damage, 'critical_system_multiplier': self.critical_system_multiplier}

    @classmethod
    def from_dict(cls, config: dict):
        params = cls()
        for key, value in config.items():
            if hasattr(params, key):
                setattr(params, key, value)
        return params

class SimpleEconomicModel:

    def __init__(self, parameters: EconomicParameters=None):
        self.parameters = parameters or EconomicParameters()
        self.total_damage = 0.0
        self.actor_costs = {}
        self.actor_gains = {}
        self.action_history = []
        self.time_proportional_damage = 0.0
        self.time_proportional_gains = {}
        self.access_state_changes = []
        self.property_state_changes = []
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

    def record_action_impact(self, time: float, actor_id: str, action_name: str, cost: float, damage: float=0.0, gain: float=0.0):
        self.record_action_cost(actor_id, cost)
        if damage > 0:
            self.record_damage(damage)
        if gain > 0:
            self.record_gain(actor_id, gain)
        self.action_history.append((time, actor_id, action_name, cost, damage, gain))

    def record_access_change(self, time: float, node_id: str, actor_id: str, old_access: str, new_access: str):
        self.access_state_changes.append((time, node_id, actor_id, old_access, new_access))

    def record_property_change(self, time: float, node_id: str, property_name: str, old_value: Any, new_value: Any):
        self.property_state_changes.append((time, node_id, property_name, old_value, new_value))

    def accumulate_time_proportional_impact(self, current_time: float, all_nodes: List[Node], attacker_actors: List[Any]):
        if current_time <= self.last_accumulation_time:
            return
        delta_t = current_time - self.last_accumulation_time
        for attacker in attacker_actors:
            attacker_id = attacker.id
            for node in all_nodes:
                access = get_node_access(node, attacker_id)
                damage_rate = self.calculate_delta(access, node)
                gain_rate = self.calculate_gamma(access, node)
                if damage_rate > 0:
                    self.time_proportional_damage += damage_rate * delta_t
                    self.total_damage += damage_rate * delta_t
                if gain_rate > 0:
                    if attacker_id not in self.time_proportional_gains:
                        self.time_proportional_gains[attacker_id] = 0.0
                    self.time_proportional_gains[attacker_id] += gain_rate * delta_t
                    if attacker_id not in self.actor_gains:
                        self.actor_gains[attacker_id] = 0.0
                    self.actor_gains[attacker_id] += gain_rate * delta_t
        self.last_accumulation_time = current_time

    def get_attacker_objective(self, actor_id: str) -> float:
        gains = self.actor_gains.get(actor_id, 0.0)
        costs = self.actor_costs.get(actor_id, 0.0)
        return gains - costs

    def get_defender_objective(self, actor_id: str) -> float:
        costs = self.actor_costs.get(actor_id, 0.0)
        return -(self.total_damage + costs)

    def get_total_costs(self, actor_id: str=None) -> float:
        if actor_id:
            return self.actor_costs.get(actor_id, 0.0)
        return sum(self.actor_costs.values())

    def get_total_gains(self, actor_id: str=None) -> float:
        if actor_id:
            return self.actor_gains.get(actor_id, 0.0)
        return sum(self.actor_gains.values())

    def get_summary(self) -> Dict[str, Any]:
        return {'total_damage': self.total_damage, 'time_proportional_damage': self.time_proportional_damage, 'one_off_damage': self.total_damage - self.time_proportional_damage, 'total_costs': self.get_total_costs(), 'total_gains': self.get_total_gains(), 'time_proportional_gains': dict(self.time_proportional_gains), 'actor_costs': dict(self.actor_costs), 'actor_gains': dict(self.actor_gains), 'num_actions': len(self.action_history), 'num_access_changes': len(self.access_state_changes), 'num_property_changes': len(self.property_state_changes)}

    def calculate_delta(self, access: str, node: Node) -> float:
        if isinstance(access, str):
            from src.core.access_levels import validate_node_access
            access = validate_node_access(access)
        if access < NodeAccessLevel.USER:
            return 0.0
        if access == NodeAccessLevel.ADMIN:
            base_rate = self.parameters.admin_access_damage_rate
        elif access == NodeAccessLevel.USER:
            base_rate = self.parameters.user_access_damage_rate
        else:
            return 0.0
        asset_count = len(getattr(node, 'assets', []))
        if asset_count > 0:
            base_rate *= 1 + asset_count * self.parameters.asset_value_factor
        properties = getattr(node, 'properties', {})
        data_sensitivity = properties.get('data_sensitivity', 'low')
        base_rate *= self.parameters.data_sensitivity_multipliers.get(data_sensitivity, 1.0)
        criticality = properties.get('criticality', 'low')
        base_rate *= self.parameters.criticality_multipliers.get(criticality, 1.0)
        data_amount = properties.get('data_amount', 0)
        if data_amount > 0:
            import math
            base_rate *= 1 + math.log10(data_amount + 1) * 0.1
        return base_rate

    def calculate_gamma(self, access: str, node: Node) -> float:
        damage_rate = self.calculate_delta(access, node)
        return damage_rate * self.parameters.attacker_gain_ratio

    def calculate_action_damage(self, action_name: str, node: Node) -> float:
        base_damage = self.parameters.critical_system_base_damage
        asset_multiplier = len(getattr(node, 'assets', [])) * 500.0
        if 'exfiltration' in action_name.lower() or 'tapestry' in action_name.lower():
            base_damage *= self.parameters.critical_system_multiplier
        return base_damage + asset_multiplier

    def calculate_action_gain(self, action_name: str, node: Node) -> float:
        damage = self.calculate_action_damage(action_name, node)
        return damage * 0.3

def calculate_delta(access: str, node: Node, parameters: EconomicParameters=None) -> float:
    if parameters is not None:
        temp_model = SimpleEconomicModel(parameters)
        return temp_model.calculate_delta(access, node)
    return economic_model.calculate_delta(access, node)

def calculate_gamma(access: str, node: Node, parameters: EconomicParameters=None) -> float:
    if parameters is not None:
        temp_model = SimpleEconomicModel(parameters)
        return temp_model.calculate_gamma(access, node)
    return economic_model.calculate_gamma(access, node)

def calculate_action_damage(action_name: str, node: Node, parameters: EconomicParameters=None) -> float:
    if parameters is not None:
        temp_model = SimpleEconomicModel(parameters)
        return temp_model.calculate_action_damage(action_name, node)
    return economic_model.calculate_action_damage(action_name, node)

def calculate_action_gain(action_name: str, node: Node, parameters: EconomicParameters=None) -> float:
    if parameters is not None:
        temp_model = SimpleEconomicModel(parameters)
        return temp_model.calculate_action_gain(action_name, node)
    return economic_model.calculate_action_gain(action_name, node)
economic_model = SimpleEconomicModel()