from .actor import Actor
from simulator.graph import Node
from actions.action import Action

class Defender(Actor):
    def __init__(self, id: str, role: str = "defender", capacity: int = 2, strategy: str = "none") -> None:
        super().__init__(id, role, capacity, strategy)
        self.is_defender = True
        self.visible_nodes = set()
        self.compromised_nodes = set()
        self.visible_links = set()
        self.compromised_links = set()
        self.available_actions = []

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

        self.schedule_next_decision()  # List[Action] assigned externally

    def choose_best_action(self, network_state) -> tuple:
        """Choose the best defensive action based on strategy"""
        if self.strategy == "reactive":
            return self._choose_reactive_action(network_state)
        elif self.strategy == "proactive":
            return self._choose_proactive_action(network_state)
        elif self.strategy == "monitoring":
            return self._choose_monitoring_action(network_state)
        else:
            return self._choose_default_action(network_state)
    
    def _choose_reactive_action(self, network_state) -> tuple:
        """Reactive strategy: prioritize responding to compromised nodes"""
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
        """Proactive strategy: prioritize preventing attacks on vulnerable nodes"""
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
        """Monitoring strategy: prioritize detection and monitoring capabilities"""
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
        """Default strategy: choose lowest cost action"""
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
        """Calculate priority for reactive strategy"""
        priority = 0
        
        # Highest priority: respond to compromised nodes
        if node.compromised and "Incident Response" in action.name:
            priority += 100
        elif node.compromised:
            priority += 50
            
        # High priority: patch vulnerabilities on compromised or high-value nodes
        if len(node.vulnerabilities) > 0 and ("Patch" in action.name or "Remediation" in action.name):
            priority += 30 + len(node.vulnerabilities) * 10
            
        # Consider node value (assets)
        priority += len(node.assets) * 2
        
        return priority
    
    def _get_proactive_priority(self, action, node):
        """Calculate priority for proactive strategy"""
        priority = 0
        
        # Prioritize patching vulnerabilities before compromise
        if not node.compromised and len(node.vulnerabilities) > 0:
            if "Patch" in action.name or "Remediation" in action.name:
                priority += 80 + len(node.vulnerabilities) * 15
                
        # Deploy protective measures
        if "Firewall" in action.name or "Detection" in action.name:
            priority += 60
            
        # Consider high-value targets
        if len(node.assets) > 2:
            priority += len(node.assets) * 10
            
        # Prioritize security and server nodes
        if hasattr(node, 'category'):
            if node.category in ['Security', 'Servers']:
                priority += 40
                
        return priority
    
    def _get_monitoring_priority(self, action, node):
        """Calculate priority for monitoring strategy"""
        priority = 0
        
        # Prioritize monitoring and detection actions
        if "Monitoring" in action.name or "Detection" in action.name:
            priority += 90
            
        # Monitor high-value nodes
        if len(node.assets) > 2:
            priority += len(node.assets) * 15
            
        # Monitor nodes with many connections (central nodes)
        priority += len(node.links) * 5
        
        # Monitor compromised nodes for further activity
        if node.compromised:
            priority += 70
            
        return priority

    def repair(self, node: Node):
        node.compromised = False
        node.repaired = True

    def on_action_finished(self, action, status, target=None):
        if action in self.ongoing_actions:
            self.ongoing_actions.remove(action)