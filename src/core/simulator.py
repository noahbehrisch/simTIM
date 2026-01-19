import heapq
import random
import logging
from typing import Any, Dict, List, Optional, Union
from .economic_model import (
    economic_model,
    calculate_action_damage,
    calculate_action_gain,
)
from .access_utils import (
    get_node_access,
    get_link_access,
    validate_node,
    validate_actor,
)
from .graph import Node, Link

logger = logging.getLogger(__name__)
infinity = float("inf")


class Event:
    EVENT_PRIORITY = {
        "action_finished": 1,
        "action_succeeded": 2,
        "action_failed": 3,
        "attack_detected": 4,
        "action_interrupted_by_detection": 5,
        "start_action": 6,
        "accumulate_time_proportional": 7,
        "actor_run": 8,
        "complete_action": 9,
    }

    def __init__(self, time: float, event_type: str, data: Dict[str, Any]):
        self.time = time
        self.event_type = event_type
        self.data = data
        self.priority = self.EVENT_PRIORITY.get(event_type, 50)

    def __lt__(self, other):
        if self.time != other.time:
            return self.time < other.time
        return self.priority < other.priority

    def __repr__(self):
        return f"Event(time={self.time}, type={self.event_type}, priority={self.priority}, data={self.data})"


class Simulator:

    def __init__(
        self,
        network=None,
        detection_engine_type="exponential",
        economic_model_instance=None,
        detection_engine=None,
    ):
        self.current_time = 0.0
        self.event_queue: List[Event] = []
        self.history: List[Event] = []
        self.network = network if network is not None else {}
        self.ongoing_actions = []

        if economic_model_instance is not None:
            self._economic_model = economic_model_instance
        else:
            self._economic_model = economic_model

        if detection_engine is not None:
            self.detection_engine = detection_engine
            config = self.detection_engine.get_configuration_summary()
            logger.info(f"Using custom detection engine: {config['engine_type']}")
        else:
            from ..detection import (
                UniformDetectionEngine,
                ExponentialDetectionEngine,
                LinearDetectionEngine,
            )

            engine_map = {
                "uniform": UniformDetectionEngine,
                "exponential": ExponentialDetectionEngine,
                "linear": LinearDetectionEngine,
                "polynomial": LinearDetectionEngine,
            }
            engine_type_lower = detection_engine_type.lower()
            if engine_type_lower in engine_map:
                engine_class = engine_map[engine_type_lower]
                self.detection_engine = engine_class()
                config = self.detection_engine.get_configuration_summary()
                logger.info(f"Using {config['engine_type']}: {config['cdf_formula']}")
            else:
                self.detection_engine = ExponentialDetectionEngine()
                logger.warning(
                    f"Unknown detection engine '{detection_engine_type}', using exponential"
                )

        from src.actions.json_conditions import action_executor, condition_evaluator

        action_executor.set_simulator(self)
        condition_evaluator.set_simulator(self)

    @property
    def economic_model(self):
        return self._economic_model

    def run(self, until: float):
        for actor in self.get_all_actors():
            actor.simulator = self
            actor.running = True
            self.schedule_event(self.current_time, "actor_run", {"actor": actor})
        self._schedule_periodic_accumulation(until)
        while self.event_queue and self.current_time <= until:
            event = heapq.heappop(self.event_queue)
            self.current_time = event.time
            self.process_event((event.time, event.event_type, event.data))
        self._accumulate_time_proportional_impact()

    def _schedule_periodic_accumulation(self, until: float):
        accumulation_interval = 0.5
        time = accumulation_interval
        while time <= until:
            self.schedule_event(time, "accumulate_time_proportional", {})
            time += accumulation_interval

    def handle_accumulate_time_proportional(self, time, data):
        self._accumulate_time_proportional_impact()

    def _accumulate_time_proportional_impact(self):
        all_nodes = self.network.get("nodes", self.network.get("nodes_list", []))
        attackers = [
            actor
            for actor in self.get_all_actors()
            if hasattr(actor, "is_attacker") and actor.is_attacker
        ]
        self._economic_model.accumulate_time_proportional_impact(
            self.current_time, all_nodes, attackers
        )

    def schedule_event(self, time: float, event_type: str, data: Dict[str, Any]):
        if event_type == "action":
            actor = data["actor"]
            if not actor.can_schedule_action():
                self.history.append(
                    (self.current_time, "action_capacity_exceeded", data)
                )
                return
            precond = data["action"].precondition(
                data["target"],
                getattr(data["target"].access, data["actor"].id, None),
                data["actor"].id,
            )
            if not precond:
                return
            heapq.heappush(self.event_queue, Event(time, "start_action", data))
            heapq.heappush(
                self.event_queue,
                Event(time + data["action"].duration, "complete_action", data),
            )
        else:
            heapq.heappush(self.event_queue, Event(time, event_type, data))

    def timeout(self, delay: float, event_type: str, data: dict):
        self.schedule_event(
            time=self.current_time + delay, event_type=event_type, data=data
        )

    def print_event_queue(self):
        for event in sorted(self.event_queue, key=lambda e: e[0]):
            pass

    def get_all_actors(self):
        actors = self.network.get("actors", [])
        return actors

    def interrupt(self, actor=None, target=None, action_type=None):
        to_interrupt = []
        for a in self.ongoing_actions:
            if (
                (actor is None or a.get("actor") == actor)
                and (target is None or a.get("target") == target)
                and (
                    action_type is None
                    or (a.get("action") and a["action"].name == action_type)
                )
            ):
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
        if hasattr(actor, "run") and getattr(actor, "running", True):
            actor.run()

    def handle_start_action(self, time, event_data):
        """
        Handle the start of an action (node or link action).

        Per TIM paper Section 4.4:
        - Node actions: target is a Node, precondition/postcondition apply to that node
        - Link actions: target is a Link (n1→n2), precondition uses both nodes' properties,
                        postcondition applies to the END node (n2) and actor's access to n2
        """
        action = event_data["action"]
        actor = event_data["actor"]
        target = event_data["target"]

        actor_validation = validate_actor(actor)
        if not actor_validation["valid"]:
            logger.error(f"Invalid actor: {actor_validation['errors']}")
            self.history.append(
                (
                    self.current_time,
                    "action_error",
                    {"reason": "invalid_actor", "errors": actor_validation["errors"]},
                )
            )
            return

        is_link_action = (
            action.is_link_action() if hasattr(action, "is_link_action") else False
        )

        if is_link_action:
            if isinstance(target, Link):
                link = target
                end_node = link.node2
                start_node = link.node1
                start_access = get_node_access(start_node, actor.id)
                end_access = get_node_access(end_node, actor.id)
                current_access = start_access
                precondition_target = link
                postcondition_target = end_node
            else:
                end_node = target
                current_access = get_node_access(target, actor.id)
                precondition_target = target
                postcondition_target = target
                logger.debug(
                    f"Link action {action.name} received node target, treating as end node"
                )
        else:
            target_validation = validate_node(target)
            if not target_validation["valid"]:
                logger.error(f"Invalid target node: {target_validation['errors']}")
                self.history.append(
                    (
                        self.current_time,
                        "action_error",
                        {
                            "reason": "invalid_target",
                            "errors": target_validation["errors"],
                        },
                    )
                )
                return
            current_access = get_node_access(target, actor.id)
            precondition_target = target
            postcondition_target = target

        if not actor.can_schedule_action():
            logger.warning(f"Actor {actor.id} capacity exceeded")
            if (
                hasattr(actor, "pending_action_count")
                and actor.pending_action_count > 0
            ):
                actor.pending_action_count -= 1
            self.history.append(
                (self.current_time, "action_capacity_exceeded", event_data)
            )
            return

        if not action.precondition(precondition_target, current_access, actor.id):
            logger.debug(
                f"Action {action.name} precondition failed at start for actor {actor.id}"
            )
            if (
                hasattr(actor, "pending_action_count")
                and actor.pending_action_count > 0
            ):
                actor.pending_action_count -= 1
            self.history.append(
                (
                    self.current_time,
                    "action_aborted_start",
                    {
                        "actor": actor,
                        "action": action,
                        "target": target,
                        "reason": "precondition_false_at_start",
                    },
                )
            )
            return

        action_instance_id = (
            id(action) + int(self.current_time * 1000000) + len(self.ongoing_actions)
        )

        ongoing_action = {
            "action": action,
            "actor": actor,
            "target": target,
            "postcondition_target": postcondition_target,
            "is_link_action": is_link_action,
            "start_time": self.current_time,
            "end_time": self.current_time + action.duration,
            "actor_access": current_access,
            "action_instance_id": action_instance_id,
        }
        self.ongoing_actions.append(ongoing_action)

        actor.record_action_cost(action, self.current_time)

        if hasattr(actor, "pending_action_count") and actor.pending_action_count > 0:
            actor.pending_action_count -= 1

        event_data["postcondition_target"] = postcondition_target
        event_data["is_link_action"] = is_link_action

        self.schedule_event(
            self.current_time + action.duration, "action_finished", event_data
        )
        if hasattr(actor, "is_attacker") and actor.is_attacker:
            self._schedule_detection_check(event_data)
        self.history.append((self.current_time, "start_action", event_data))
        actor.schedule_action(action)

    def handle_action_finished(self, time, data):
        ongoing = next(
            (
                a
                for a in self.ongoing_actions
                if a["actor"] == data["actor"]
                and a["action"] == data["action"]
                and (a["target"] == data["target"])
            ),
            None,
        )
        if ongoing:
            precond = data["action"].precondition(
                data["target"], data.get("actor_access"), data["actor"].id
            )
            if precond:
                if random.random() < data["action"].success_probability:
                    postcondition_target = data.get(
                        "postcondition_target", data["target"]
                    )
                    is_link_action = data.get("is_link_action", False)

                    data["action"].postcondition(
                        postcondition_target, data.get("actor_access"), data["actor"].id
                    )

                    self._record_state_change(
                        postcondition_target, data["actor"].id, data["action"]
                    )

                    self._calculate_economic_impact(data)

                    target = postcondition_target
                    actor_id = data["actor"].id
                    action_name = data["action"].name
                    if hasattr(target, "id"):
                        if not hasattr(target, "successful_actions_by_actor"):
                            target.successful_actions_by_actor = {}
                        if actor_id not in target.successful_actions_by_actor:
                            target.successful_actions_by_actor[actor_id] = set()
                        target.successful_actions_by_actor[actor_id].add(action_name)
                        logger.debug(
                            f"Tracked successful action: {action_name} on {target.id} by {actor_id}"
                        )

                    if hasattr(data["actor"], "on_action_finished"):
                        data["actor"].on_action_finished(
                            data["action"], "success", postcondition_target
                        )
                    self.history.append((self.current_time, "action_succeeded", data))
                else:
                    if hasattr(data["actor"], "on_action_finished"):
                        data["actor"].on_action_finished(
                            data["action"], "failure", data["target"]
                        )
                    self.history.append((self.current_time, "action_failed", data))
            else:
                if hasattr(data["actor"], "on_action_finished"):
                    data["actor"].on_action_finished(
                        data["action"], "aborted", data["target"]
                    )
                self.history.append((self.current_time, "action_aborted", data))
            if ongoing in self.ongoing_actions:
                self.ongoing_actions.remove(ongoing)

    def _record_state_change(self, node, actor_id: str, action):
        self._accumulate_time_proportional_impact()

        current_access = get_node_access(node, actor_id)
        self._economic_model.record_access_change(
            self.current_time,
            node.id if hasattr(node, "id") else str(node),
            actor_id,
            "CHANGED",  # Previous access
            (
                current_access.name
                if hasattr(current_access, "name")
                else str(current_access)
            ),
        )

    def _schedule_detection_check(self, action_data):
        action = action_data["action"]
        target = action_data["target"]
        actor = action_data["actor"]
        actor_access = action_data.get("actor_access", "NONE")
        detection_time = self.detection_engine.calculate_detection_time(
            action, target, actor_access, actor, action.duration
        )
        if detection_time is not None:
            engine_config = self.detection_engine.get_configuration_summary()
            self.schedule_event(
                self.current_time + detection_time,
                "attack_detected",
                {
                    "detected_action": action,
                    "detected_actor": actor,
                    "detected_target": target,
                    "detection_time": self.current_time + detection_time,
                    "detection_method": engine_config["engine_type"],
                    "cdf_type": engine_config.get("cdf_formula", "unknown"),
                },
            )

    def handle_attack_detected(self, time, data):
        self.history.append((self.current_time, "attack_detected", data))

        logger.info(
            f"Attack detected: {data['detected_action'].name} by {data['detected_actor'].id} on {data['detected_target']}"
        )

        defenders = [
            actor
            for actor in self.get_all_actors()
            if hasattr(actor, "is_defender") and actor.is_defender
        ]
        for defender in defenders:
            if hasattr(defender, "on_attack_detected"):
                defender.on_attack_detected(data)

    def _interrupt_action(self, action_data, reason):
        action = action_data["action"]
        actor = action_data["actor"]
        target = action_data["target"]
        if action_data in self.ongoing_actions:
            self.ongoing_actions.remove(action_data)
        if hasattr(actor, "on_action_finished"):
            actor.on_action_finished(action, "interrupted", target)
        if hasattr(actor, "ongoing_actions") and action in actor.ongoing_actions:
            actor.ongoing_actions.remove(action)
        self.history.append(
            (
                self.current_time,
                "action_interrupted",
                {
                    "actor": actor,
                    "action": action,
                    "target": target,
                    "reason": reason,
                    "interrupted_at": self.current_time,
                },
            )
        )

    def _check_ongoing_actions_for_node(self, node):
        for ongoing in list(self.ongoing_actions):
            if ongoing["target"] == node or ongoing.get("postcondition_target") == node:
                action = ongoing["action"]
                target = ongoing["target"]
                actor = ongoing["actor"]
                current_access = get_node_access(target, actor.id)
                if not action.precondition(target, current_access, actor.id):
                    self._interrupt_action(ongoing, "precondition_failed")

    def _calculate_economic_impact(self, action_data):
        """Record economic impact of a successful action (cost already recorded at start)."""
        action = action_data["action"]
        target = action_data["target"]
        actor = action_data["actor"]
        damage = calculate_action_damage(action.name, target)
        gain = calculate_action_gain(action.name, target)
        if hasattr(actor, "is_attacker") and actor.is_attacker:
            self._economic_model.record_action_outcome(
                self.current_time, actor.id, action.name, 0, gain
            )
        else:
            self._economic_model.record_action_outcome(
                self.current_time, actor.id, action.name, damage, 0
            )

    def record_access_change(
        self, node, actor_id: str, old_access: str, new_access: str
    ):
        node_id = node.id if hasattr(node, "id") else str(node)
        self._economic_model.record_access_change(
            self.current_time, node_id, actor_id, old_access, new_access
        )
        logger.debug(
            f"Access change recorded: {actor_id} on {node_id}: {old_access} -> {new_access}"
        )
        self._check_ongoing_actions_for_node(node)

    def record_property_change(self, node, property_name: str, old_value, new_value):
        node_id = node.id if hasattr(node, "id") else str(node)
        self._economic_model.record_property_change(
            self.current_time, node_id, property_name, old_value, new_value
        )
        logger.debug(
            f"Property change recorded: {node_id}.{property_name}: {old_value} -> {new_value}"
        )
        self._check_ongoing_actions_for_node(node)

    def get_tim_economic_summary(self, time_interval=None):
        if time_interval is None:
            time_interval = (0.0, self.current_time)
        all_actors = self.get_all_actors()
        attackers = [
            actor
            for actor in all_actors
            if hasattr(actor, "is_attacker") and actor.is_attacker
        ]
        defenders = [
            actor
            for actor in all_actors
            if hasattr(actor, "is_defender") and actor.is_defender
        ]
        attacker_objectives = {}
        for attacker in attackers:
            attacker_objectives[attacker.id] = (
                self._economic_model.get_attacker_objective(
                    attacker.id, attacker.incurredCost
                )
            )
        defender_objectives = {}
        for defender in defenders:
            defender_objectives[defender.id] = (
                self._economic_model.get_defender_objective(
                    defender.id, defender.incurredCost
                )
            )
        summary = self._economic_model.get_summary(all_actors)
        return {
            "time_interval": time_interval,
            "total_damage": summary["total_damage"],
            "defender_objectives": defender_objectives,
            "attacker_objectives": attacker_objectives,
            "total_attacker_gains": summary["total_gains"],
            "total_costs": summary["total_costs"],
            "num_actions": summary["num_actions"],
        }

    def notify_nodes_discovered(self, actor_id: str, discovered_nodes: list):
        logger.debug(
            f"notify_nodes_discovered called for {actor_id}, {len(discovered_nodes)} nodes"
        )
        for actor in self.get_all_actors():
            if actor.id == actor_id and hasattr(actor, "visible_nodes"):
                before_count = len(actor.visible_nodes)
                for node in discovered_nodes:
                    if node not in actor.visible_nodes:
                        actor.visible_nodes.add(node)
                        logger.debug(f"Added {node.id} to {actor_id}'s visible_nodes")
                        from src.core.access_utils import (
                            set_node_access,
                            get_node_access,
                        )
                        from src.core.access_levels import NodeAccessLevel

                        current_access = get_node_access(node, actor_id)
                        if current_access == NodeAccessLevel.NONE:
                            set_node_access(node, actor_id, NodeAccessLevel.VISIBLE)
                            logger.debug(
                                f"Set {node.id} access to VISIBLE for {actor_id}"
                            )
                after_count = len(actor.visible_nodes)
                logger.debug(
                    f"{actor_id} visible_nodes: {before_count} → {after_count}"
                )

    def notify_links_discovered(self, actor_id: str, discovered_links: list):
        for actor in self.get_all_actors():
            if actor.id == actor_id and hasattr(actor, "visible_links"):
                for link in discovered_links:
                    if link not in actor.visible_links:
                        actor.visible_links.add(link)

    def print_history(self):
        for entry in self.history:
            logger.info(entry)
