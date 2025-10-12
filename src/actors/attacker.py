from .actor import Actor
from src.core.graph import Node, Link
from .strategies import get_attacker_strategy

class Attacker(Actor):
    def __init__(self, id: str, strategy: str = "random", capacity: int = 3):
        super().__init__(id, "attacker", capacity=capacity, strategy=strategy)
        self.is_attacker = True
        self.visible_nodes = set()
        self.compromised_nodes = set()
        self.visible_links = set()
        self.compromised_links = set()
        self.available_actions = []
        self.time_proportional_gain_rate = 0.0
        self._strategy_component = get_attacker_strategy(strategy)

    def run(self, network_state):
        super().run(network_state)

    def make_decision(self, network_state):
        if not self.can_schedule_action():
            self.schedule_next_decision()
            return
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
        self.schedule_next_decision()

    def choose_action(self, network_state):
        # Delegate to strategy component
        return self._strategy_component.choose_action(self, network_state)

    def change_strategy(self, new_strategy: str):
        """Allow runtime strategy changes"""
        self.strategy = new_strategy
        self._strategy_component = get_attacker_strategy(new_strategy)

    # Legacy methods - kept for potential future use but marked for cleanup
    def exploit(self, node: Node):
        """DEPRECATED: Use action system instead"""
        import warnings
        warnings.warn("exploit() method is deprecated, use action system instead", DeprecationWarning)
        node.compromised = True
        if hasattr(node, 'id'):
            self.compromised_nodes.add(node.id)

    def gain_visibility(self, node: Node):
        """DEPRECATED: Visibility is now handled through action postconditions"""
        import warnings
        warnings.warn("gain_visibility() method is deprecated", DeprecationWarning)
        self.visible_nodes.add(node)

    def gain_link_visibility(self, link: Link):
        """DEPRECATED: Link visibility is now handled through action postconditions"""
        import warnings
        warnings.warn("gain_link_visibility() method is deprecated", DeprecationWarning)
        self.visible_links.add(link)

    def compromise_link(self, link: Link):
        """DEPRECATED: Use action system instead"""
        import warnings
        warnings.warn("compromise_link() method is deprecated", DeprecationWarning)
        self.compromised_links.add(link)

    def on_action_finished(self, action, status, target=None):
        if action in self.ongoing_actions:
            self.ongoing_actions.remove(action)
        if status == "success" and target is not None:
            # Only add to compromised_nodes if the target is actually compromised
            if hasattr(target, 'compromised') and target.compromised:
                if hasattr(target, 'id'):
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
        actor_access = target.access.get(self.id, 'NONE')
        one_off_damage, one_off_gain = self.calculate_damage_functions(action, target, actor_access)
        self.total_gain += one_off_gain
        self.record_economic_event(timestamp, 'gain', one_off_gain, {
            'action': action.name,
            'target': getattr(target, 'id', str(target)),  # Handle both Node and Link objects
            'type': 'one_off_gain'
        })
        if actor_access in ['USER', 'ADMIN']:
            damage_rate, gain_rate = self.calculate_time_proportional_rates(actor_access, target)
            self.time_proportional_gain_rate += gain_rate
            self.record_economic_event(timestamp, 'access_gain', gain_rate, {
                'access_level': actor_access,
                'target': getattr(target, 'id', str(target)),  # Handle both Node and Link objects
                'type': 'time_proportional_rate'
            })

    def _calculate_one_off_gain(self, action_name, node_properties):
        if 'tapestry' in action_name.lower():
            return 2500.0
        if 'data' in action_name.lower() or 'exfiltration' in action_name.lower():
            assets = node_properties.get('assets', [])
            sensitive_data = [a for a in assets if 'data' in str(a).lower() or 'sensitive' in str(a).lower()]
            if len(sensitive_data) >= 3:
                return 100000.0
            elif len(sensitive_data) > 0:
                return 25000.0
        return super()._calculate_one_off_gain(action_name, node_properties)

    def _calculate_time_gain_rate(self, access_level, node_properties):
        if access_level == 'ADMIN':
            assets = node_properties.get('assets', [])
            critical_assets = [a for a in assets if 'critical' in str(a).lower()]
            return len(critical_assets) * 50.0
        elif access_level == 'USER':
            return len(node_properties.get('assets', [])) * 10.0
        return 0.0