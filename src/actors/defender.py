from .actor import Actor
from src.core.graph import Node
from .strategies import get_defender_strategy
from src.core.access_utils import get_node_access

class Defender(Actor):
    def __init__(self, id: str, strategy: str = "reactive", capacity: int = 2, budget: float = float('inf')):
        super().__init__(id, "defender", capacity=capacity, strategy=strategy, budget=budget)
        self.is_defender = True
        self.is_attacker = False
        self.visible_nodes = set()
        self.compromised_nodes = set()
        self.visible_links = set()
        self.compromised_links = set()
        self.available_actions = []
        self.system_damage_prevented = 0.0
        self.detected_attacks = []
        self._strategy_component = get_defender_strategy(strategy)

    def make_decision(self, network_state):
        if not self.can_schedule_action():
            return False  # No capacity for more actions
            
        decision = self.choose_best_action(network_state)
        if decision:
            action, target = decision
            actor_access = get_node_access(target, self.id)
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
        return False  # No valid action found
        # No need to schedule next decision - simulator handles it automatically

    def choose_best_action(self, network_state) -> tuple:
        # Delegate to strategy component
        return self._strategy_component.choose_action(self, network_state)

    def change_strategy(self, new_strategy: str):
        """Allow runtime strategy changes"""
        self.strategy = new_strategy
        self._strategy_component = get_defender_strategy(new_strategy)



    def on_action_finished(self, action, status, target=None):
        if action in self.ongoing_actions:
            self.ongoing_actions.remove(action)

    def on_attack_detected(self, detection_data):
        """
        Handle attack detection event.
        
        Args:
            detection_data: Dict containing:
                - detected_action: The action that was detected
                - detected_target: The target of the detected action
                - detected_actor: The actor performing the detected action
                - detection_time: When the detection occurred
                - detection_probability: Probability that led to detection
                - detection_method: Method used for detection
        """
        detected_action = detection_data.get("detected_action")
        detected_target = detection_data.get("detected_target")
        detected_actor = detection_data.get("detected_actor")
        
        if not all([detected_action, detected_target, detected_actor]):
            print(f"⚠️  Defender {self.id}: Invalid detection data received")
            return
            
        timestamp = getattr(self.simulator, 'current_time', 0.0)
        
        print(f"🚨 Defender {self.id}: Detected {detected_action.name} by {detected_actor.id} on {getattr(detected_target, 'id', str(detected_target))}")
        
        # Record the detection for economic tracking
        self.detected_attacks.append({
            'timestamp': timestamp,
            'detected_action': detected_action.name,
            'detected_actor': detected_actor.id,
            'detected_target': getattr(detected_target, 'id', str(detected_target)),
            'detection_method': detection_data.get('detection_method', 'unknown')
        })
        
        # Try to respond with defensive actions
        if hasattr(self, 'available_actions'):
            defensive_actions = [action for action in self.available_actions 
                               if 'patch' in action.name.lower() or 'firewall' in action.name.lower()]
            if defensive_actions and self.can_schedule_action():
                response_action = defensive_actions[0]
                self._execute_defensive_action(response_action, detected_target)

    def record_detection_economics(self, attack_source, damage_prevented=0.0, detection_cost=0.0):
        """
        Record economic impact from detection activities.
        Separate method for when economic tracking is needed independently of detection events.
        
        Args:
            attack_source: ID of the attacker
            damage_prevented: Economic damage prevented by the detection
            detection_cost: Cost incurred for the detection
        """
        timestamp = getattr(self.simulator, 'current_time', 0.0)
        
        if detection_cost > 0:
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

    def _execute_defensive_action(self, action, target):
        if self.simulator and self.can_schedule_action():
            action_data = {
                "actor": self,
                "action": action,
                "target": target,
                "actor_access": get_node_access(target, self.id)
            }
            self.simulator.schedule_event(
                self.simulator.current_time,
                "action",
                action_data
            )
            self.ongoing_actions.add(action)


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

    def record_system_damage(self, damage_amount, timestamp=None, metadata=None):
        if timestamp is None:
            timestamp = getattr(self.simulator, 'current_time', 0.0)
        self.record_economic_event(timestamp, 'damage', damage_amount, 
                                 metadata or {'type': 'system_damage'})

