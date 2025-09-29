from typing import Dict, Any
from src.core.graph import Node

class SimpleEconomicModel:
    
    def __init__(self):
        self.total_damage = 0.0
        self.actor_costs = {}
        self.actor_gains = {}
        self.action_history = []
    
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
    
    def get_attacker_objective(self, actor_id: str) -> float:
        gains = self.actor_gains.get(actor_id, 0.0)
        costs = self.actor_costs.get(actor_id, 0.0)
        return gains - costs
    
    def get_defender_objective(self, actor_id: str) -> float:
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
            'total_costs': self.get_total_costs(),
            'total_gains': self.get_total_gains(),
            'actor_costs': dict(self.actor_costs),
            'actor_gains': dict(self.actor_gains),
            'num_actions': len(self.action_history)
        }

def calculate_action_damage(action_name: str, node: Node) -> float:
    base_damage = 1000.0
    
    asset_multiplier = len(getattr(node, 'assets', [])) * 500.0
    
    if 'exfiltration' in action_name.lower() or 'tapestry' in action_name.lower():
        base_damage *= 5.0
    
    return base_damage + asset_multiplier

def calculate_action_gain(action_name: str, node: Node) -> float:
    damage = calculate_action_damage(action_name, node)
    return damage * 0.3
economic_model = SimpleEconomicModel()