from .actor import Actor
from simulator.graph import Node, Link
from actions.action import Action

class Attacker(Actor):
    def __init__(self, id: str, strategy: str = "random"):
        super().__init__(id, "attacker", strategy=strategy)
        self.is_attacker = True
        self.visible_nodes = set()
        self.compromised_nodes = set()
        self.visible_links = set()
        self.compromised_links = set()
        self.available_actions = []
        
        # TIM Economic Model for attackers
        self.time_proportional_gain_rate = 0.0  # γ(ω_x(n), π̂(n)) accumulator

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
                        #print(f"[DEBUG] Valid action: {action}, Link: {link}")
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
            if hasattr(target, 'id'):
                self.compromised_nodes.add(target.id)
            
            # TIM Economic Model: Record successful attack
            if hasattr(self, 'simulator') and self.simulator:
                self.on_successful_attack(action, target, self.simulator.current_time)
    
    # TIM Economic Model Implementation for Attackers
    
    def get_economic_objective(self, time_interval=None):
        """
        TIM Attacker Objective: maximize G[0,T](x) - C_x,[0,T]
        
        Per TIM Section 4.7:
        "The objective of an attacker x ∈ X^(att) is to maximize G[0,T](x) - C_x,[0,T]"
        """
        if time_interval is None:
            # Use total simulation time
            total_gain = self.total_gain
            total_costs = self.incurredCost
        else:
            start_time, end_time = time_interval
            
            # Calculate G[0,T](x) for time interval from economic events
            total_gain = sum(
                event['value'] for event in self.economic_events
                if event['type'] == 'gain' and start_time <= event['timestamp'] <= end_time
            )
            
            # Calculate C_x,[0,T] for time interval from economic events
            total_costs = sum(
                event['value'] for event in self.economic_events
                if event['type'] == 'cost' and start_time <= event['timestamp'] <= end_time
            )
        
        return total_gain - total_costs  # Maximize this value
    
    def on_successful_attack(self, action, target, timestamp):
        """Handle successful attack completion for TIM economic calculations"""
        actor_access = target.access.get(self.id, 'NONE')
        
        # Calculate TIM damage/gain functions
        one_off_damage, one_off_gain = self.calculate_damage_functions(action, target, actor_access)
        
        # Record one-off gain G(a, π̂(n))
        self.total_gain += one_off_gain
        self.record_economic_event(timestamp, 'gain', one_off_gain, {
            'action': action.name,
            'target': target.id,
            'type': 'one_off_gain'
        })
        
        # Update time-proportional gain rate γ(ω_x(n), π̂(n))
        if actor_access in ['USER', 'ADMIN']:
            damage_rate, gain_rate = self.calculate_time_proportional_rates(actor_access, target)
            self.time_proportional_gain_rate += gain_rate
            
            self.record_economic_event(timestamp, 'access_gain', gain_rate, {
                'access_level': actor_access,
                'target': target.id,
                'type': 'time_proportional_rate'
            })
    
    def _calculate_one_off_gain(self, action_name, node_properties):
        """Enhanced G(a, π̂(n)) for attackers based on TIM examples"""
        
        # Tapestry attack gains (per TIM paper example)
        if 'tapestry' in action_name.lower():
            return 2500.0  # Web server compromise value
        
        # Data exfiltration gains (per TIM paper: 100k USD ransom)
        if 'data' in action_name.lower() or 'exfiltration' in action_name.lower():
            assets = node_properties.get('assets', [])
            sensitive_data = [a for a in assets if 'data' in str(a).lower() or 'sensitive' in str(a).lower()]
            if len(sensitive_data) >= 3:  # Large data breach
                return 100000.0  # TIM paper example value
            elif len(sensitive_data) > 0:
                return 25000.0
        
        # Default calculation
        return super()._calculate_one_off_gain(action_name, node_properties)
    
    def _calculate_time_gain_rate(self, access_level, node_properties):
        """Enhanced γ(ω_x(n), π̂(n)) for attackers"""
        if access_level == 'ADMIN':
            assets = node_properties.get('assets', [])
            critical_assets = [a for a in assets if 'critical' in str(a).lower()]
            return len(critical_assets) * 50.0  # $50/time per critical asset under admin control
        elif access_level == 'USER':
            return len(node_properties.get('assets', [])) * 10.0
        
        return 0.0
