from .actor import Actor
from src.core.graph import Node, Link
from .strategies import get_attacker_strategy
from src.core.access_utils import get_node_access
from src.core.access_levels import NodeAccessLevel

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
            print(f"[DEBUG] {self.id} cannot schedule action (capacity: {len(self.ongoing_actions)}/{self.capacity})")
            return False  # No capacity for more actions
            
        print(f"[DEBUG] {self.id} making decision at t={self.simulator.current_time if self.simulator else '?'}")
        print(f"[DEBUG]   Visible nodes: {[n.id if hasattr(n, 'id') else str(n) for n in self.visible_nodes]}")
        print(f"[DEBUG]   Available actions: {len(self.available_actions)}")
        
        decision = self.choose_action(network_state)
        if decision:
            action, target = decision
            actor_access = get_node_access(target, self.id)
            print(f"[DEBUG]   Chose: {action.name} on {getattr(target, 'id', str(target))} (access: {actor_access})")
            if action.precondition(target, actor_access, self.id):
                self.simulator.schedule_event(self.simulator.current_time, "start_action", {
                    "actor": self,
                    "action": action,
                    "target": target,
                    "actor_access": actor_access 
                })
                self.simulator.schedule_event(self.simulator.current_time + action.duration, "action_finished", {
                    "actor": self,
                    "action": action,
                    "target": target,
                    "actor_access": actor_access
                })
                self.ongoing_actions.add(action)
                return True  # Action was scheduled
        else:
            print(f"[DEBUG]   No valid action found!")
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
                access_level = get_node_access(target, self.id)
                if access_level >= NodeAccessLevel.USER:
                    self.compromised_nodes.add(target.id)
                    # Discover links from compromised nodes (TIM paper R5: discovery)
                    self._discover_links_from_node(target)
            if hasattr(self, 'simulator') and self.simulator:
                self.on_successful_attack(action, target, self.simulator.current_time)

    def _discover_links_from_node(self, node: Node):
        """
        When an attacker compromises a node, they discover connected links.
        Per TIM paper Section 4.6: "port scan... leading to discovery of link"
        """
        if not hasattr(node, 'links'):
            return
        
        for link in node.links:
            # Make link visible to attacker
            if link not in self.visible_links:
                self.visible_links.add(link)
                
            # Discover connected nodes (make them at least VISIBLE)
            connected_node = link.node1 if link.node2.id == node.id else link.node2
            if connected_node not in self.visible_nodes:
                self.visible_nodes.add(connected_node)
                # Update access if currently NONE
                current_access = get_node_access(connected_node, self.id)
                if current_access == NodeAccessLevel.NONE:
                    from src.core.access_utils import set_node_access
                    set_node_access(connected_node, self.id, NodeAccessLevel.VISIBLE)

    def on_successful_attack(self, action, target, timestamp):
        from src.core.economic_model import calculate_action_gain
        
        actor_access = get_node_access(target, self.id)
        one_off_gain = calculate_action_gain(action.name, target)
        self.total_gain += one_off_gain
        self.record_economic_event(timestamp, 'gain', one_off_gain, {
            'action': action.name,
            'target': getattr(target, 'id', str(target)),  # Handle both Node and Link objects
            'type': 'one_off_gain'
        })

