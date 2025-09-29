from .actor import Actor
from src.core.graph import Node
from src.actions.action import Action

class Defender(Actor):

    def __init__(self, id: str, strategy: str = "reactive"):

        super().__init__(id, "defender", strategy=strategy)
        self.is_defender = True
        self.visible_nodes = set()
        self.compromised_nodes = set()
        self.visible_links = set()
        self.compromised_links = set()
        self.available_actions = []
        self.system_damage_prevented = 0.0
        self.detected_attacks = []
    def run(self, network_state):

        super().run(network_state)
    def make_decision(self, network_state):

        if not self.can_schedule_action():
            self.schedule_next_decision()
            return
        decision = self.choose_best_action(network_state)
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
    def choose_best_action(self, network_state) -> tuple:

        if self.strategy == "reactive":
            return self._choose_reactive_action(network_state)
        elif self.strategy == "proactive":
            return self._choose_proactive_action(network_state)
        elif self.strategy == "monitoring":
            return self._choose_monitoring_action(network_state)
        else:
            return self._choose_default_action(network_state)
    def _choose_reactive_action(self, network_state) -> tuple:

        best = None
        best_priority = -1
        for action in self.available_actions:
            if action.is_node_action():
                for node in network_state.get('nodes_list', []):
                    actor_access = node.access.get(self.id, None)
                    if action.precondition(node, actor_access, self.id):
                        priority = self._get_reactive_priority(action, node)
                        if priority > best_priority:
                            best = (action, node)
                            best_priority = priority
        return best
    def _choose_proactive_action(self, network_state) -> tuple:

        best = None
        best_priority = -1
        for action in self.available_actions:
            if action.is_node_action():
                for node in network_state.get('nodes_list', []):
                    actor_access = node.access.get(self.id, None)
                    if action.precondition(node, actor_access, self.id):
                        priority = self._get_proactive_priority(action, node)
                        if priority > best_priority:
                            best = (action, node)
                            best_priority = priority
        return best
    def _choose_monitoring_action(self, network_state) -> tuple:

        best = None
        best_priority = -1
        for action in self.available_actions:
            if action.is_node_action():
                for node in network_state.get('nodes_list', []):
                    actor_access = node.access.get(self.id, None)
                    if action.precondition(node, actor_access, self.id):
                        priority = self._get_monitoring_priority(action, node)
                        if priority > best_priority:
                            best = (action, node)
                            best_priority = priority
        return best
    def _choose_default_action(self, network_state) -> tuple:

        best = None
        best_cost = float('inf')
        for action in self.available_actions:
            if action.is_node_action():
                for node in network_state.get('nodes_list', []):
                    actor_access = node.access.get(self.id, None)
                    if action.precondition(node, actor_access, self.id):
                        cost = action.get_cost()
                        if cost < best_cost:
                            best = (action, node)
                            best_cost = cost
            elif action.is_link_action():
                for link in network_state.get('links_list', []):
                    actor_access = getattr(link, 'access', {}).get(self.id, None)
                    if action.precondition(link, actor_access, self.id):
                        cost = action.get_cost()
                        if cost < best_cost:
                            best = (action, link)
                            best_cost = cost
        return best
    def _get_reactive_priority(self, action, node):

        priority = 0
        if node.compromised and "Incident Response" in action.name:
            priority += 100
        elif node.compromised:
            priority += 50
        if len(node.vulnerabilities) > 0 and ("Patch" in action.name or "Remediation" in action.name):
            priority += 30 + len(node.vulnerabilities) * 10
        priority += len(node.assets) * 2
        return priority
    def _get_proactive_priority(self, action, node):

        priority = 0
        if not node.compromised and len(node.vulnerabilities) > 0:
            if "Patch" in action.name or "Remediation" in action.name:
                priority += 80 + len(node.vulnerabilities) * 15
        if "Firewall" in action.name or "Detection" in action.name:
            priority += 60
        if len(node.assets) > 2:
            priority += len(node.assets) * 10
        if hasattr(node, 'category'):
            if node.category in ['Security', 'Servers']:
                priority += 40
        return priority
    def _get_monitoring_priority(self, action, node):

        priority = 0
        if "Monitoring" in action.name or "Detection" in action.name:
            priority += 90
        if len(node.assets) > 2:
            priority += len(node.assets) * 15
        priority += len(node.links) * 5
        if node.compromised:
            priority += 70
        return priority
    def repair(self, node: Node):

        node.compromised = False
        node.repaired = True
    def on_action_finished(self, action, status, target=None):

        if action in self.ongoing_actions:
            self.ongoing_actions.remove(action)
    def on_attack_detected(self, detection_data):

        detected_action = detection_data.get("detected_action")
        detected_target = detection_data.get("detected_target")
        detected_actor = detection_data.get("detected_actor")
        print(f"🚨 Defender {self.id}: Detected {detected_action.name} by {detected_actor.id} on {detected_target.id}")
        if hasattr(self, 'available_actions'):
            defensive_actions = [action for action in self.available_actions 
                               if 'patch' in action.name.lower() or 'firewall' in action.name.lower()]
            if defensive_actions and self.can_schedule_action():
                response_action = defensive_actions[0]
                self._execute_defensive_action(response_action, detected_target)
    def _execute_defensive_action(self, action, target):

        if self.simulator and self.can_schedule_action():
            action_data = {
                "actor": self,
                "action": action,
                "target": target,
                "actor_access": target.access.get(self.id, "ADMIN")
            }
            self.simulator.schedule_event(
                self.simulator.current_time,
                "action",
                action_data
            )
            self.ongoing_actions.add(action)
    def get_economic_objective(self, time_interval=None):

        defender_costs = self.calculate_total_costs(time_interval)
        system_damage = self._calculate_total_system_damage(time_interval)
        damage_from_events = 0.0
        if time_interval:
            start, end = time_interval
            for event in self.economic_events:
                if (start <= event['timestamp'] <= end and 
                    event['type'] == 'damage'):
                    damage_from_events += event['value']
        total_damage = system_damage + damage_from_events
        return total_damage + defender_costs
    def _calculate_total_system_damage(self, time_interval=None):

        if hasattr(self.simulator, 'get_total_system_damage'):
            return self.simulator.get_total_system_damage(time_interval)
        estimated_damage = 0.0
        for detection in self.detected_attacks:
            if time_interval is None or (time_interval[0] <= detection.get('timestamp', 0) <= time_interval[1]):
                estimated_damage += 5000.0
        if hasattr(self.simulator, 'network') and self.simulator.network:
            nodes = self.simulator.network.get('nodes', {}).values()
            for node in nodes:
                if getattr(node, 'compromised', False):
                    assets = getattr(node, 'assets', [])
                    damage_rate = len(assets) * 100.0
                    if time_interval:
                        duration = time_interval[1] - time_interval[0]
                        estimated_damage += damage_rate * duration
                    else:
                        estimated_damage += damage_rate * getattr(self.simulator, 'current_time', 1.0)
        return estimated_damage
    def on_attack_detected(self, attack_source, damage_prevented=0.0, detection_cost=0.0):

        timestamp = getattr(self.simulator, 'current_time', 0.0)
        self.incurredCost += detection_cost
        self.record_economic_event(timestamp, 'cost', detection_cost, {
            'attacker': attack_source,
            'type': 'detection_cost'
        })
        if damage_prevented > 0:
            self.record_economic_event(timestamp, 'damage_prevented', -damage_prevented, {
                'attacker': attack_source,
                'type': 'mitigation'
            })
        self.detected_attacks.append({
            'timestamp': timestamp,
            'attacker': attack_source,
            'damage_prevented': damage_prevented,
            'detection_cost': detection_cost
        })
    def record_system_damage(self, damage_amount, timestamp=None, metadata=None):

        if timestamp is None:
            timestamp = getattr(self.simulator, 'current_time', 0.0)
        self.record_economic_event(timestamp, 'damage', damage_amount, 
                                 metadata or {'type': 'system_damage'})
    def _calculate_one_off_damage(self, action_name, node_properties):

        if 'data' in action_name.lower() or 'exfiltration' in action_name.lower():
            assets = node_properties.get('assets', [])
            sensitive_data = [a for a in assets if 'data' in str(a).lower() or 'sensitive' in str(a).lower()]
            if len(sensitive_data) >= 3:
                return 150000.0
            elif len(sensitive_data) > 0:
                return 50000.0
        if 'tapestry' in action_name.lower():
            return 8000.0
        return super()._calculate_one_off_damage(action_name, node_properties)