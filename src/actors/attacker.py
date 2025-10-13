from .actor import Actor
from src.core.graph import Node, Link
from .strategies import get_attacker_strategy

class Attacker(Actor):
    def __init__(self, id: str, strategy: str = "random", capacity: int = 3, budget: float = float('inf')):
        super().__init__(id, "attacker", capacity=capacity, strategy=strategy, budget=budget)
        self.is_attacker = True
        self.visible_nodes = set()
        self.compromised_nodes = set()
        self.visible_links = set()
        self.compromised_links = set()
        self.available_actions = []
        self.time_proportional_gain_rate = 0.0
        self._strategy_component = get_attacker_strategy(strategy)

    def make_decision(self, network_state):
        if not self.can_schedule_action():
            return False  # No capacity for more actions
            
        decision = self.choose_action(network_state)
        if decision:
            action, target = decision
            actor_access = target.access.get(self.id, None)
            if action.precondition(target, actor_access, self.id):
                self.simulator.schedule_event(self.simulator.current_time, "start_action", {
                    "actor": self,
                    "action": action,
                    "target": target,
                    "actor_access": actor_access 
                })
                self.simulator.schedule_event(self.simulator.current_time + action.duration, "complete_action", {
                    "actor": self,
                    "action": action,
                    "target": target,
                    "actor_access": actor_access
                })
                self.ongoing_actions.add(action)
                return True  # Action was scheduled
        return False  # No valid action found

    def choose_action(self, network_state):
        # Delegate to strategy component
        return self._strategy_component.choose_action(self, network_state)

    def change_strategy(self, new_strategy: str):
        """Allow runtime strategy changes"""
        self.strategy = new_strategy
        self._strategy_component = get_attacker_strategy(new_strategy)

    def on_action_finished(self, action, status, target=None):
        if action in self.ongoing_actions:
            self.ongoing_actions.remove(action)
        if status == "success" and target is not None:
            # Add to compromised_nodes if we have USER or ADMIN access
            if hasattr(target, 'access') and hasattr(target, 'id'):
                from src.core.access_levels import NodeAccessLevel
                access_level = target.access.get(self.id)
                if access_level in [NodeAccessLevel.USER, NodeAccessLevel.ADMIN]:
                    self.compromised_nodes.add(target.id)
            # Also check the old compromised flag for backward compatibility
            elif hasattr(target, 'compromised') and target.compromised and hasattr(target, 'id'):
                self.compromised_nodes.add(target.id)
            if hasattr(self, 'simulator') and self.simulator:
                self.on_successful_attack(action, target, self.simulator.current_time)

    def get_economic_objective(self, time_interval=None):
        if time_interval is None:
            total_gain = self.total_gain
            total_costs = self.incurredCost
        else:
            start_time, end_time = time_interval
            total_gain = sum(
                event['value'] for event in self.economic_events
                if event['type'] == 'gain' and start_time <= event['timestamp'] <= end_time
            )
            total_costs = sum(
                event['value'] for event in self.economic_events
                if event['type'] == 'cost' and start_time <= event['timestamp'] <= end_time
            )
        return total_gain - total_costs

    def on_successful_attack(self, action, target, timestamp):
        from src.core.economic_model import calculate_action_gain
        
        actor_access = target.access.get(self.id, 'NONE')
        one_off_gain = calculate_action_gain(action.name, target)
        self.total_gain += one_off_gain
        self.record_economic_event(timestamp, 'gain', one_off_gain, {
            'action': action.name,
            'target': getattr(target, 'id', str(target)),  # Handle both Node and Link objects
            'type': 'one_off_gain'
        })

