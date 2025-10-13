import heapq
import random
import logging
from typing import Any, Dict, List
from src.detection import SimpleTIMDetectionEngine, AdvancedTIMDetectionEngine
from .economic_model import economic_model, calculate_action_damage, calculate_action_gain
logger = logging.getLogger(__name__)
infinity = float('inf') 

class Event:
    def __init__(self, time: float, event_type: str, data: Dict[str, Any]):
        self.time = time
        self.event_type = event_type
        self.data = data

    def __lt__(self, other):
        return self.time < other.time

    def __repr__(self):
        return f"Event(time={self.time}, type={self.event_type}, data={self.data})"

class Simulator:
    def __init__(self, network=None, detection_engine_type="advanced_tim"):
        """
        Initialize simulator with configurable detection engine.
        
        Args:
            network: Network configuration
            detection_engine_type: "simple_tim" or "advanced_tim" (default: "advanced_tim")
        """
        self.current_time = 0.0
        self.event_queue: List[Event] = []
        self.history: List[Event] = []
        self.network = network if network is not None else {}
        self.ongoing_actions = []
        
        # Choose detection engine based on type
        if detection_engine_type == "simple_tim":
            self.detection_engine = SimpleTIMDetectionEngine()
            logger.info("Using SimpleTIM: Pure TIM paper Section 4.5 implementation")
        elif detection_engine_type == "advanced_tim":
            self.detection_engine = AdvancedTIMDetectionEngine()
            logger.info("Using AdvancedTIM: TIM paper + domain knowledge")
        else:
            # Default to advanced
            self.detection_engine = AdvancedTIMDetectionEngine()
            logger.warning(f"Unknown detection engine type '{detection_engine_type}', using advanced_tim")
            
        from src.actions.json_conditions import action_executor
        
        action_executor.set_simulator(self)
    
    def run(self, until: float):
        # Initialize actors and schedule their first decisions
        for actor in self.get_all_actors():
            actor.set_simulator(self)
            if hasattr(actor, 'is_attacker') and actor.is_attacker:
                # Initialize attacker with only internet-exposed nodes
                all_nodes = self.network.get('nodes', self.network.get('nodes_list', []))
                exposed_nodes = [node for node in all_nodes 
                               if hasattr(node, 'properties') and 
                               node.properties.get('exposed_to_internet', False)]
                actor.visible_nodes = exposed_nodes
            
            # Initialize actor and start its decision loop
            actor.running = True
            # Schedule first run cycle
            self.schedule_event(
                self.current_time,
                "actor_run", 
                {"actor": actor}
            )
        
        # Schedule periodic time-proportional impact accumulation
        # Per TIM paper Section 4.7: accumulate δ and γ over time intervals
        self._schedule_periodic_accumulation(until)
        
        while self.event_queue and self.current_time <= until: 
            event = heapq.heappop(self.event_queue)
            self.current_time = event.time
            self.process_event((event.time, event.event_type, event.data))
        
        # Final accumulation at end of simulation
        self._accumulate_time_proportional_impact()
    
    def _schedule_periodic_accumulation(self, until: float):
        """
        Schedule periodic accumulation of time-proportional damage/gain.
        
        Per TIM paper Section 4.7, we need to accumulate δ(ω, π̂) and γ(ω, π̂)
        over time intervals.
        """
        accumulation_interval = 0.5  # Accumulate every 0.5 time units
        time = accumulation_interval
        while time <= until:
            self.schedule_event(time, "accumulate_time_proportional", {})
            time += accumulation_interval
    
    def handle_accumulate_time_proportional(self, time, data):
        """Handle periodic accumulation of time-proportional impact"""
        self._accumulate_time_proportional_impact()
    
    def _accumulate_time_proportional_impact(self):
        """
        Accumulate time-proportional damage and gain.
        Implements TIM paper Section 4.7 formula for δ and γ.
        """
        all_nodes = self.network.get('nodes', self.network.get('nodes_list', []))
        attackers = [actor for actor in self.get_all_actors() 
                    if hasattr(actor, 'is_attacker') and actor.is_attacker]
        
        economic_model.accumulate_time_proportional_impact(
            self.current_time, all_nodes, attackers
        )

    def schedule_event(self, time: float, event_type: str, data: Dict[str, Any]):
        if event_type == "action":
            actor = data["actor"]
            if not actor.can_schedule_action():
                self.history.append((self.current_time, "action_capacity_exceeded", data))
                return
            precond = data["action"].precondition(
                data["target"],
                getattr(data["target"].access, data["actor"].id, None),
                data["actor"].id
            )
            if not precond:
                return
            heapq.heappush(self.event_queue, Event(time, "start_action", data))
            heapq.heappush(self.event_queue, Event(time + data["action"].duration, "complete_action", data))
        else:
            heapq.heappush(self.event_queue, Event(time, event_type, data))

    def timeout(self, delay: float, event_type: str, data: dict):
        self.schedule_event(
            time=self.current_time + delay,
            event_type=event_type,
            data=data
        )

    def print_event_queue(self):
        for event in sorted(self.event_queue, key=lambda e: e[0]):
            pass

    def get_all_actors(self):
        actors = self.network.get('actors', [])
        return actors

    def interrupt(self, actor=None, target=None, action_type=None):
        to_interrupt = []
        for a in self.ongoing_actions:
            if ((actor is None or a.get("actor") == actor) and
                (target is None or a.get("target") == target) and
                (action_type is None or a.get("action") and a["action"].name == action_type)):
                to_interrupt.append(a)
        for a in to_interrupt:
            self.ongoing_actions.remove(a)
            self.history.append((self.current_time, "action_interrupted", a))

    def process_event(self, event):
        time, event_type, data = event
        handler = getattr(self, f"handle_{event_type}", None)
        if handler:
            handler(time, data)
        else:
            self.history.append((time, event_type, data))

    def handle_actor_run(self, time, data):
        actor = data["actor"]
        if hasattr(actor, 'run') and getattr(actor, 'running', True):
            actor.run()

    def handle_start_action(self, time, event_data):
        action = event_data["action"]
        actor = event_data["actor"]
        target = event_data["target"]
        
        # Check if actor has capacity for this action
        if not actor.can_schedule_action():
            self.history.append((self.current_time, "action_capacity_exceeded", event_data))
            return
        
        # Initial precondition check - action must be valid to start
        current_access = target.access.get(actor.id, "NONE")
        if not action.precondition(target, current_access, actor.id):
            self.history.append((self.current_time, "action_aborted_start", {
                "actor": actor,
                "action": action,
                "target": target,
                "reason": "precondition_false_at_start"
            }))
            return
        
        # Add to ongoing actions
        ongoing_action = {
            "action": action,
            "actor": actor,
            "target": target,
            "start_time": self.current_time,
            "end_time": self.current_time + action.duration,
            "actor_access": current_access
        }
        self.ongoing_actions.append(ongoing_action)
        
        # Schedule action completion
        self.schedule_event(
            self.current_time + action.duration,
            "action_finished",
            event_data
        )
        
        # Schedule continuous precondition monitoring as per TIM paper
        # "if at any time in the interval [t_start, t_start + d_a) the precondition becomes false, the action is aborted"
        self._schedule_continuous_precondition_monitoring(ongoing_action)
        
        # Schedule detection check for attack actions
        if hasattr(actor, 'is_attacker') and actor.is_attacker:
            self._schedule_detection_check(event_data)
        
        # Log action start
        self.history.append((self.current_time, "start_action", event_data))
        
        # Update actor's ongoing actions
        actor.schedule_action(action)

    def handle_action_finished(self, time, data):
        """Handle action completion - calls the existing complete_action logic"""
        self.handle_complete_action(time, data)

    def handle_complete_action(self, time, data):
        ongoing = next((a for a in self.ongoing_actions
                        if a["actor"] == data["actor"] and
                           a["action"] == data["action"] and
                           a["target"] == data["target"]), None)
        if ongoing:
            precond = data["action"].precondition(
                data["target"],
                data.get("actor_access"), 
                data["actor"].id
            )
            if precond:
                if random.random() < data["action"].success_probability:
                    data["action"].postcondition(
                        data["target"],
                        data.get("actor_access"),  
                        data["actor"].id
                    )
                    self._calculate_economic_impact(data)
                    
                    if hasattr(data["actor"], "on_action_finished"):
                        data["actor"].on_action_finished(data["action"], "success", data["target"])
                    self.history.append((self.current_time, "action_succeeded", data))
                else:
                    if hasattr(data["actor"], "on_action_finished"):
                        data["actor"].on_action_finished(data["action"], "failure", data["target"])
                    self.history.append((self.current_time, "action_failed", data))
            else:
                if hasattr(data["actor"], "on_action_finished"):
                    data["actor"].on_action_finished(data["action"], "aborted", data["target"])
                self.history.append((self.current_time, "action_aborted", data))
            self.ongoing_actions.remove(ongoing)

    def _schedule_detection_check(self, action_data):
        """
        Schedule detection check for attack actions.
        Supports legacy, simple TIM, and advanced TIM detection engines.
        """
        action = action_data["action"]
        target = action_data["target"]
        actor = action_data["actor"]
        actor_access = action_data.get("actor_access", "NONE")
        
        # Check detection engine type and use appropriate method
        if isinstance(self.detection_engine, (AdvancedTIMDetectionEngine, SimpleTIMDetectionEngine)):
            # TIM-compliant detection (both simple and advanced)
            detection_prob = self.detection_engine.calculate_detection_probability(action, target, actor_access, actor)
            
            # Sample detection time using TIM CDF approach
            detection_time = self.detection_engine.sample_detection_time(action, action.duration, detection_prob)
            
            if detection_time is not None:
                # Schedule detection event at the sampled time
                engine_type = "simple_TIM" if isinstance(self.detection_engine, SimpleTIMDetectionEngine) else "advanced_TIM"
                self.schedule_event(
                    self.current_time + detection_time,
                    "attack_detected",
                    {
                        "detected_action": action,
                        "detected_actor": actor,
                        "detected_target": target,
                        "detection_time": self.current_time + detection_time,
                        "detection_probability": detection_prob,
                        "detection_method": engine_type
                    }
                )
        else:
            # Legacy detection approach
            detection_prob = self.detection_engine.calculate_detection_probability(action, target, actor_access, actor)
            
            if random.random() < detection_prob:
                detection_delay = self.detection_engine.sample_detection_time(action.name, action.duration)
                self.schedule_event(
                    self.current_time + detection_delay,
                    "attack_detected",
                    {
                        "detected_action": action,
                        "detected_actor": actor,
                        "detected_target": target,
                        "detection_time": self.current_time + detection_delay,
                        "detection_probability": detection_prob,
                        "detection_method": "legacy"
                    }
                )

    def handle_attack_detected(self, time, data):
        self.history.append((self.current_time, "attack_detected", data))
        for ongoing in self.ongoing_actions[:]:
            if (ongoing.get("action") == data["detected_action"] and
                ongoing.get("actor") == data["detected_actor"] and 
                ongoing.get("target") == data["detected_target"]):
                self.ongoing_actions.remove(ongoing)
                interruption_event = Event(
                    time=self.current_time,
                    event_type="action_interrupted_by_detection",
                    data={
                        "actor": data["detected_actor"].id,
                        "action": data["detected_action"].__class__.__name__,
                        "target": data["detected_target"],
                        "detection_probability": data.get("detection_probability", 0.0)
                    }
                )
                self.history.append(interruption_event)
        defenders = [actor for actor in self.get_all_actors() 
                    if hasattr(actor, 'is_defender') and actor.is_defender]
        for defender in defenders:
            if hasattr(defender, 'on_attack_detected'):
                defender.on_attack_detected(data)

    def _schedule_precondition_monitoring(self, action_data):
        action = action_data["action"]
        duration = action.duration
        if duration > 0.1:
            check_interval = max(0.05, duration / 3)
            num_checks = max(1, int(duration / check_interval))
            for i in range(1, num_checks + 1):
                check_time = self.current_time + (i * check_interval)
                if check_time < self.current_time + duration:
                    self.schedule_event(
                        check_time,
                        "precondition_check",
                        {
                            "action_data": action_data.copy(),
                            "check_time": check_time
                        }
                    )

    def handle_precondition_check(self, time, data):
        action_data = data["action_data"]
        action = action_data["action"]
        target = action_data["target"]
        actor = action_data["actor"]
        
        # Find the ongoing action to check
        ongoing_action = None
        for ongoing in self.ongoing_actions:
            if (ongoing["actor"] == actor and 
                ongoing["action"] == action and 
                ongoing["target"] == target):
                ongoing_action = ongoing
                break
        
        if ongoing_action is None:
            return
        
        # Check if precondition still holds
        current_access = target.access.get(actor.id, "NONE")
        precond_holds = action.precondition(target, current_access, actor.id)
        if not precond_holds:
            self._interrupt_action(ongoing_action, "precondition_failed")

    def _interrupt_action(self, action_data, reason):
        action = action_data["action"]
        actor = action_data["actor"]
        target = action_data["target"]
        if action_data in self.ongoing_actions:
            self.ongoing_actions.remove(action_data)
        if hasattr(actor, 'on_action_finished'):
            actor.on_action_finished(action, "interrupted", target)
        if hasattr(actor, 'ongoing_actions') and action in actor.ongoing_actions:
            actor.ongoing_actions.remove(action)
        self.history.append((self.current_time, "action_interrupted", {
            "actor": actor,
            "action": action,
            "target": target,
            "reason": reason,
            "interrupted_at": self.current_time
        }))

    def _schedule_continuous_precondition_monitoring(self, ongoing_action):
        """
        Schedule continuous precondition monitoring as per TIM paper:
        'if at any time in the interval [t_start, t_start + d_a) the precondition becomes false, the action is aborted'
        """
        action = ongoing_action["action"]
        start_time = ongoing_action["start_time"]
        duration = action.duration
        
        # Monitor precondition at regular intervals (every 0.1 time units)
        # This ensures we catch precondition violations quickly
        monitoring_interval = min(0.1, duration / 10)  # At least 10 checks per action
        
        check_time = start_time + monitoring_interval
        while check_time < start_time + duration:
            self.schedule_event(
                check_time,
                "precondition_check",
                {
                    "action_data": ongoing_action.copy(),
                    "check_time": check_time
                }
            )
            check_time += monitoring_interval

    def _calculate_economic_impact(self, action_data):
        action = action_data["action"]
        target = action_data["target"]
        actor = action_data["actor"]
        
        cost = action.cost
        damage = calculate_action_damage(action.name, target)
        gain = calculate_action_gain(action.name, target)
        
        if hasattr(actor, 'is_attacker') and actor.is_attacker:
            economic_model.record_action_impact(
                self.current_time, actor.id, action.name, cost, 0, gain
            )
        else:
            economic_model.record_action_impact(
                self.current_time, actor.id, action.name, cost, damage, 0
            )
        
        actor.record_action_cost(action, self.current_time)

    def record_access_change(self, node, actor_id: str, old_access: str, new_access: str):
        """
        Record access level change for time-proportional damage/gain calculation.
        Per TIM paper Section 4.7: track ti (state change times)
        """
        node_id = node.id if hasattr(node, 'id') else str(node)
        economic_model.record_access_change(
            self.current_time, node_id, actor_id, old_access, new_access
        )
        logger.debug(f"Access change recorded: {actor_id} on {node_id}: {old_access} -> {new_access}")

    def record_property_change(self, node, property_name: str, old_value, new_value):
        """
        Record property change for time-proportional damage/gain calculation.
        Per TIM paper Section 4.7: track ti (state change times)
        """
        node_id = node.id if hasattr(node, 'id') else str(node)
        economic_model.record_property_change(
            self.current_time, node_id, property_name, old_value, new_value
        )
        logger.debug(f"Property change recorded: {node_id}.{property_name}: {old_value} -> {new_value}")

    def get_tim_economic_summary(self, time_interval=None):
        if time_interval is None:
            time_interval = (0.0, self.current_time)
        all_actors = self.get_all_actors()
        attackers = [actor for actor in all_actors if hasattr(actor, 'is_attacker') and actor.is_attacker]
        defenders = [actor for actor in all_actors if hasattr(actor, 'is_defender') and actor.is_defender]
        
        attacker_objectives = {}
        for attacker in attackers:
            attacker_objectives[attacker.id] = economic_model.get_attacker_objective(attacker.id)
        
        defender_objectives = {}
        for defender in defenders:
            defender_objectives[defender.id] = economic_model.get_defender_objective(defender.id)
        
        summary = economic_model.get_summary()
        
        return {
            "time_interval": time_interval,
            "total_damage": summary['total_damage'],
            "defender_objectives": defender_objectives,
            "attacker_objectives": attacker_objectives,
            "total_attacker_gains": summary['total_gains'],
            "total_costs": summary['total_costs'],
            "num_actions": summary['num_actions']
        }

    def notify_nodes_discovered(self, actor_id: str, discovered_nodes: list):
        """Notify when an actor discovers new nodes through reconnaissance or scanning"""
        for actor in self.get_all_actors():
            if actor.id == actor_id and hasattr(actor, 'visible_nodes'):
                # Add newly discovered nodes to the actor's visible nodes
                for node in discovered_nodes:
                    if node not in actor.visible_nodes:
                        # Handle both set and list types for backwards compatibility
                        if isinstance(actor.visible_nodes, set):
                            actor.visible_nodes.add(node)
                        else:
                            actor.visible_nodes.append(node)

    def notify_links_discovered(self, actor_id: str, discovered_links: list):
        """Notify when an actor discovers new links through network scanning"""
        for actor in self.get_all_actors():
            if actor.id == actor_id and hasattr(actor, 'visible_links'):
                # Add newly discovered links to the actor's visible links
                for link in discovered_links:
                    if link not in actor.visible_links:
                        # Handle both set and list types for backwards compatibility
                        if isinstance(actor.visible_links, set):
                            actor.visible_links.add(link)
                        else:
                            actor.visible_links.append(link)

    def print_history(self):
        for entry in self.history:
            print(entry)