import heapq
import random
from typing import Any, Dict, List

# Aliases:
infinity = float('inf') 

class Event:
    def __init__(self, time: float, event_type: str, data: Dict[str, Any]):
        self.time = time # TODO: reform time tracking
        self.event_type = event_type
        self.data = data # Dict holding important information about the event TODO: is it a good idea?
    # Less than comparison for priority queue, essential for heapq TODO: learn more
    def __lt__(self, other):
        return self.time < other.time
    def __repr__(self):
        return f"Event(time={self.time}, type={self.event_type}, data={self.data})"

class Simulator:
    def __init__(self, network=None):
        self.current_time = 0.0
        self.event_queue: List[Event] = []
        self.history: List[Event] = []
        self.network = network if network is not None else {}
        self.ongoing_actions = []
        
    def run(self, until: float):
        # For testing: all attackers see every node
        all_nodes = self.network.get('nodes', self.network.get('nodes_list', []))
        for actor in self.get_all_actors():
            if hasattr(actor, 'is_attacker') and actor.is_attacker:
                actor.visible_nodes = list(all_nodes)
        for actor in self.get_all_actors():
            self.schedule_event(self.current_time, "actor_decide", {"actor": actor})
        while self.event_queue and self.current_time <= until: 
            event = heapq.heappop(self.event_queue)
            self.current_time = event.time
            self.process_event((event.time, event.event_type, event.data))

    # --- Event Queue Management ---
    def schedule_event(self, time: float, event_type: str, data: Dict[str, Any]):
        if event_type == "action":
            # Check precondition before scheduling start
            precond = data["action"].precondition(
                data["target"],
                getattr(data["target"].access, data["actor"].id, None),
                data["actor"].id
            )
            if not precond:
                return
            # Schedule start
            heapq.heappush(self.event_queue, Event(time, "start_action", data))
            # Schedule completion
            heapq.heappush(self.event_queue, Event(time + data["action"].duration, "complete_action", data))
        else:
            # Schedule other events [not used yet]
            heapq.heappush(self.event_queue, Event(time, event_type, data))

    # convenience function for timeouts, delays, etc.
    def timeout(self, delay: float, event_type: str, data: dict):
        self.schedule_event(
            time=self.current_time + delay,
            event_type=event_type,
            data=data
        )

    # just for debugging, TODO: -m delete later
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

    # --- Event Processing ---
    def process_event(self, event):
        # Event processing function. TODO: rework
        time, event_type, data = event
        handler = getattr(self, f"handle_{event_type}", None)
        if handler:
            handler(time, data)
        else:
            self.history.append((time, event_type, data))

    def handle_actor_decide(self, time, data):
        actor = data["actor"]
        busy = any(a["actor"] == actor for a in self.ongoing_actions)
        if not busy:
            if hasattr(actor, "is_attacker") and actor.is_attacker:
                self.attacker_decision(actor)
            elif hasattr(actor, "is_defender") and actor.is_defender:
                self.defender_decision(actor)
        self.schedule_event(self.current_time + 1, "actor_decide", {"actor": actor})

    def attacker_decision(self, attacker):
        decision = attacker.choose_best_action(self.network)
        if decision:
            action, target = decision
            actor_access = target.access.get(attacker.id, None)
            if action.precondition(target, actor_access, attacker.id):
                self.schedule_event(self.current_time, "start_action", {
                    "actor": attacker,
                    "action": action,
                    "target": target,
                    "actor_access": actor_access 
                })
                self.schedule_event(self.current_time + action.duration, "complete_action", {
                    "actor": attacker,
                    "action": action,
                    "target": target,
                    "actor_access": actor_access
                })
            else:
                pass

    def defender_decision(self, defender):
        decision = defender.choose_best_action(self.network)
        if decision:
            action, target = decision
            actor_access = target.access.get(defender.id, None) 
            if action.precondition(target, actor_access, defender.id):
                self.schedule_event(self.current_time, "start_action", {
                    "actor": defender,
                    "action": action,
                    "target": target,
                    "actor_access": actor_access 
                })
                self.schedule_event(self.current_time + action.duration, "complete_action", {
                    "actor": defender,
                    "action": action,
                    "target": target,
                    "actor_access": actor_access
                })
            else:
                pass

    def handle_start_action(self, time, data):
        precond = data["action"].precondition(
            data["target"],
            data.get("actor_access"),
            data["actor"].id
        )
        if not precond:
            self.history.append((self.current_time, "action_aborted", data))
            return
        self.ongoing_actions.append(data)
        self.history.append((self.current_time, "start_action", data))

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
                    if hasattr(data["actor"], "on_action_finished"):
                        data["actor"].on_action_finished(data["action"], "success", data["target"])
                    self.history.append((self.current_time, "action_succeeded", data))
                else:
                    if hasattr(data["actor"], "on_action_finished"):
                        data["actor"].on_action_finished(data["action"], "failure", data["target"])
                    self.history.append((self.current_time, "action_failed", data))
            else:
                self.history.append((self.current_time, "action_aborted", data))
            self.ongoing_actions.remove(ongoing)
        self.schedule_event(self.current_time, "actor_decide", {"actor": data["actor"]})

    # --- History/Debug ---
    def print_history(self):
        for entry in self.history:
            print(entry)
