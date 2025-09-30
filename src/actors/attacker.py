from .actor import Actor
from src.core.graph import Node, Link
from src.actions.action import Action

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

    def run(self, network_state):
        super().run(network_state)
        all_nodes = network_state.get('nodes', network_state.get('nodes_list', []))
        self.visible_nodes = list(all_nodes)

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
        match self.strategy:
            case "greedy":
                return  self.choose_best_action(network_state)
            case "random":
                return self.choose_random_action(network_state)
            case _:
                return self.choose_best_action(network_state)

    def choose_best_action(self, network_state) -> tuple:
        visible_nodes = list(self.visible_nodes)
        visible_links = list(self.visible_links)
        best = None
        best_gain = float('-inf')
        for action in self.available_actions:
            if action.is_node_action():
                for node in visible_nodes:
                    if hasattr(node, 'id') and node.id in self.compromised_nodes:
                        continue
                    actor_access = node.access.get(self.id, None)
                    if action.precondition(node, actor_access, self.id):
                        gain = action.get_one_off_gain(node, actor_access, self.id)
                        if gain > best_gain:
                            best = (action, node)
                            best_gain = gain
            elif action.is_link_action():
                for link in visible_links:
                    if hasattr(link, 'id') and link.id in self.compromised_links:
                        continue
                    actor_access = getattr(link, 'access', {}).get(self.id, None)
                    if action.precondition(link, actor_access, self.id):
                        gain = action.get_one_off_gain(link, actor_access, self.id)
                        if gain > best_gain:
                            best = (action, link)
                            best_gain = gain
        return best

    def choose_random_action(self, network_state) -> tuple:
        import random

        visible_nodes = list(self.visible_nodes)
        visible_links = list(self.visible_links)
        possible_actions = []
        for action in self.available_actions:
            if action.is_node_action():
                for node in visible_nodes:
                    if hasattr(node, 'id') and node.id in self.compromised_nodes:
                        continue
                    actor_access = node.access.get(self.id, None)
                    if action.precondition(node, actor_access, self.id):
                        possible_actions.append((action, node))
            elif action.is_link_action():
                for link in visible_links:
                    if hasattr(link, 'id') and link.id in self.compromised_links:
                        continue
                    actor_access = getattr(link, 'access', {}).get(self.id, None)
                    if action.precondition(link, actor_access, self.id):
                        possible_actions.append((action, link))
        chosen_action = random.choice(possible_actions) if possible_actions else None
        return chosen_action

    def exploit(self, node: Node):
        node.compromised = True
        if hasattr(node, 'id'):
            self.compromised_nodes.add(node.id)

    def gain_visibility(self, node: Node):
        self.visible_nodes.add(node)

    def gain_link_visibility(self, link: Link):
        self.visible_links.add(link)

    def compromise_link(self, link: Link):
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
            'target': target.id,
            'type': 'one_off_gain'
        })
        if actor_access in ['USER', 'ADMIN']:
            damage_rate, gain_rate = self.calculate_time_proportional_rates(actor_access, target)
            self.time_proportional_gain_rate += gain_rate
            self.record_economic_event(timestamp, 'access_gain', gain_rate, {
                'access_level': actor_access,
                'target': target.id,
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