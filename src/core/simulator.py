import heapq
import logging
import random
from typing import Any

from .access_levels import NodeAccessLevel
from .access_utils import (
    get_node_access,
    set_node_access,
    validate_actor,
    validate_node,
)
from .action_index import OngoingActionsIndex
from .economic_model import SimpleEconomicModel
from .events import EventBus, EventType, HistoryRecorder, SimulationEvent
from .exceptions import (
    ActorValidationError,
    CapacityError,
    NodeValidationError,
    PreconditionError,
)
from .network import Link, Network

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
    }

    def __init__(self, time: float, event_type: str, data: dict[str, Any]):
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
        detection_engine_type="early_weighted",
        economic_model_instance=None,
        detection_engine=None,
        event_bus: EventBus | None = None,
    ):
        self.current_time = 0.0
        self.event_queue: list[Event] = []
        self.network = network if network is not None else Network()
        self.actors: list[Any] = []
        self._ongoing_actions_index = OngoingActionsIndex()

        self._event_bus = event_bus or EventBus()
        self._history_recorder = HistoryRecorder(self._event_bus)
        self._history_recorder.register()

        if economic_model_instance is not None:
            self._economic_model = economic_model_instance
        else:
            self._economic_model = SimpleEconomicModel()

        if detection_engine is not None:
            self.detection_engine = detection_engine
            config = self.detection_engine.get_configuration_summary()
            logger.info(f"Using custom detection engine: {config['engine_type']}")
        else:
            from src.detection.registry import create_detection_engine

            self.detection_engine = create_detection_engine(detection_engine_type)
            config = self.detection_engine.get_configuration_summary()
            logger.info(f"Using {config['engine_type']}: {config['cdf_formula']}")

        from src.actions.json_conditions import action_executor, condition_evaluator

        action_executor.set_simulator(self)
        condition_evaluator.set_simulator(self)

    @property
    def event_bus(self) -> EventBus:
        return self._event_bus

    @property
    def history(self) -> list:
        return self._history_recorder.history

    @property
    def ongoing_actions(self) -> list:
        return self._ongoing_actions_index.to_list()

    @ongoing_actions.setter
    def ongoing_actions(self, value: list):
        self._ongoing_actions_index.clear()
        for action_data in value:
            self._ongoing_actions_index.add(action_data)

    @property
    def economic_model(self):
        return self._economic_model

    def _publish_event(self, event_type: EventType, data: dict[str, Any]) -> None:
        event = SimulationEvent(event_type=event_type, time=self.current_time, data=data)
        self._event_bus.publish(event)

    def run(self, until: float):
        self._publish_event(
            EventType.SIMULATION_STARTED,
            {
                "until": until,
                "network": self.network,
            },
        )
        self._emit_initial_access_events()
        for actor in self.get_all_actors():
            actor.simulator = self
            actor.running = True
            self.schedule_event(self.current_time, "actor_run", {"actor": actor})
        self._schedule_periodic_accumulation(until)

        # Main simulation loop
        while self.event_queue and self.current_time <= until:
            event = heapq.heappop(self.event_queue)
            self.current_time = event.time
            self.process_event((event.time, event.event_type, event.data))
        self._accumulate_time_proportional_impact()
        economic_summary = self.get_tim_economic_summary()
        self._publish_event(
            EventType.SIMULATION_ENDED,
            {
                "final_time": self.current_time,
                "economic_summary": economic_summary,
            },
        )

    def _schedule_periodic_accumulation(self, until: float):
        accumulation_interval = 0.5
        time = accumulation_interval
        while time <= until:
            self.schedule_event(time, "accumulate_time_proportional", {})
            time += accumulation_interval

    def handle_accumulate_time_proportional(self, time, data):
        self._accumulate_time_proportional_impact()

    def _accumulate_time_proportional_impact(self):
        self._economic_model.accumulate_time_proportional_impact(self.current_time)

    def schedule_event(self, time: float, event_type: str, data: dict[str, Any]):
        heapq.heappush(self.event_queue, Event(time, event_type, data))

    def get_all_actors(self):
        return self.actors

    def process_event(self, event):
        time, event_type, data = event
        handler = getattr(self, f"handle_{event_type}", None)
        if handler:
            handler(time, data)
        else:
            self._publish_event(EventType.STATE_CHANGED, {"event_type": event_type, **data})

    def handle_actor_run(self, time, data):
        actor = data["actor"]
        if hasattr(actor, "run") and getattr(actor, "running", True):
            actor.run()

    def handle_start_action(self, time, event_data):
        action = event_data["action"]
        actor = event_data["actor"]
        target = event_data["target"]

        actor_validation = validate_actor(actor)
        if not actor_validation["valid"]:
            error = ActorValidationError(
                actor_id=getattr(actor, "id", None),
                errors=actor_validation["errors"],
            )
            logger.error(str(error))
            self._publish_event(
                EventType.ACTION_ERROR,
                {"error": error.to_dict() if hasattr(error, "to_dict") else str(error)},
            )
            return

        is_link_action = action.is_link_action() if hasattr(action, "is_link_action") else False

        if is_link_action:
            if isinstance(target, Link):
                link = target
                end_node = link.node2
                start_node = link.node1
                start_access = get_node_access(start_node, actor.id)
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
                error = NodeValidationError(
                    node_id=getattr(target, "id", None),
                    errors=target_validation["errors"],
                )
                logger.error(str(error))
                self._publish_event(EventType.ACTION_ERROR, {"error": str(error)})
                return
            current_access = get_node_access(target, actor.id)
            precondition_target = target
            postcondition_target = target

        # Decrement pending count BEFORE capacity check — this action was already
        # counted as pending when make_decision() scheduled it.  Without this,
        # actors with capacity=1 always fail the re-check (pending=1, 1 < 1 is False).
        if hasattr(actor, "pending_action_count") and actor.pending_action_count > 0:
            actor.pending_action_count -= 1

        if not actor.can_schedule_action():
            error = CapacityError(
                actor_id=actor.id,
                current_capacity=len(actor.ongoing_actions)
                + getattr(actor, "pending_action_count", 0),
                max_capacity=actor.capacity,
            )
            logger.debug(str(error))
            self._publish_event(
                EventType.ACTION_CAPACITY_EXCEEDED, {**event_data, "error": error.to_dict()}
            )
            return

        if not action.precondition(precondition_target, current_access, actor.id):
            error = PreconditionError(
                action_name=action.name,
                reason="precondition_false_at_start",
                target=getattr(target, "id", str(target)),
                actor=actor.id,
            )
            logger.debug(str(error))
            self._publish_event(
                EventType.ACTION_ABORTED,
                {
                    "actor": actor,
                    "action": action,
                    "target": target,
                    "error": error.to_dict(),
                },
            )
            return

        action_instance_id = (
            id(action) + int(self.current_time * 1000000) + len(self._ongoing_actions_index)
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
        self._ongoing_actions_index.add(ongoing_action)

        event_data["postcondition_target"] = postcondition_target
        event_data["is_link_action"] = is_link_action

        self.schedule_event(self.current_time + action.duration, "action_finished", event_data)
        if hasattr(actor, "is_attacker") and actor.is_attacker:
            self._schedule_detection_check(event_data)
        self._publish_event(EventType.ACTION_STARTED, event_data)
        actor.schedule_action(action)

    def handle_action_finished(self, time, data):
        ongoing = self._ongoing_actions_index.find(
            actor=data["actor"],
            action=data["action"],
            target=data["target"],
        )
        if ongoing:
            # Remove from index FIRST to prevent self-interrupt: the postcondition
            # may change access, triggering _check_ongoing_actions_for_node which
            # would otherwise find and interrupt this same action.
            self._ongoing_actions_index.remove(ongoing)

            precond = data["action"].precondition(
                data["target"], data.get("actor_access"), data["actor"].id
            )
            if precond:
                if random.random() < data["action"].success_probability:
                    postcondition_target = data.get("postcondition_target", data["target"])

                    previous_access = get_node_access(postcondition_target, data["actor"].id)

                    data["action"].postcondition(
                        postcondition_target, data.get("actor_access"), data["actor"].id
                    )

                    new_access = get_node_access(postcondition_target, data["actor"].id)

                    data["previous_access"] = (
                        previous_access.name
                        if hasattr(previous_access, "name")
                        else str(previous_access)
                    )
                    data["new_access"] = (
                        new_access.name if hasattr(new_access, "name") else str(new_access)
                    )

                    self._accumulate_time_proportional_impact()
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
                    self._publish_event(EventType.ACTION_SUCCEEDED, data)
                else:
                    if hasattr(data["actor"], "on_action_finished"):
                        data["actor"].on_action_finished(data["action"], "failure", data["target"])
                    self._publish_event(EventType.ACTION_FAILED, data)
            else:
                if hasattr(data["actor"], "on_action_finished"):
                    data["actor"].on_action_finished(data["action"], "aborted", data["target"])
                self._publish_event(EventType.ACTION_ABORTED, data)

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
        self._publish_event(EventType.ATTACK_DETECTED, data)

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
        self._ongoing_actions_index.remove(action_data)
        if hasattr(actor, "on_action_finished"):
            actor.on_action_finished(action, "interrupted", target)
        if hasattr(actor, "ongoing_actions") and action in actor.ongoing_actions:
            actor.ongoing_actions.remove(action)
        self._publish_event(
            EventType.ACTION_INTERRUPTED,
            {
                "actor": actor,
                "action": action,
                "target": target,
                "reason": reason,
                "interrupted_at": self.current_time,
            },
        )

    def _check_ongoing_actions_for_node(self, node):
        ongoing_for_node = self._ongoing_actions_index.find_all(target=node)
        for ongoing in ongoing_for_node:
            action = ongoing["action"]
            target = ongoing["target"]
            actor = ongoing["actor"]
            current_access = get_node_access(target, actor.id)
            if not action.precondition(target, current_access, actor.id):
                self._interrupt_action(ongoing, "precondition_failed")

    def _calculate_economic_impact(self, action_data):
        action = action_data["action"]
        target = action_data["target"]
        actor = action_data["actor"]
        actor_access = action_data.get("actor_access")

        damage = action.get_one_off_damage(target, actor_access, actor.id)
        gain = action.get_one_off_gain(target, actor_access, actor.id)
        time_damage = action.get_time_damage(target, actor_access, actor.id)
        time_gain = action.get_time_gain(target, actor_access, actor.id)

        self._economic_model.record_action_outcome(
            self.current_time, actor.id, action.name, damage, gain
        )
        self._economic_model.register_time_rate(actor.id, time_damage, time_gain)

    def _emit_initial_access_events(self):
        """Emit access_changed events for attacker initial access at t=0."""
        if not self.network:
            return
        attacker_ids = {
            actor.id for actor in self.get_all_actors() if getattr(actor, "is_attacker", False)
        }
        for node in self.network.nodes_list:
            for actor_id, access_level in node.access.items():
                if actor_id in attacker_ids and access_level != NodeAccessLevel.NONE:
                    self._publish_event(
                        EventType.ACCESS_CHANGED,
                        {
                            "node_id": node.id,
                            "actor_id": actor_id,
                            "old_access": NodeAccessLevel.NONE.name,
                            "new_access": access_level.name,
                        },
                    )

    def record_access_change(self, node, actor_id: str, old_access, new_access):
        self._publish_event(
            EventType.ACCESS_CHANGED,
            {
                "node_id": node.id,
                "actor_id": actor_id,
                "old_access": old_access.name,
                "new_access": new_access.name,
            },
        )
        logger.debug(
            f"Access change recorded: {actor_id} on {node.id}: {old_access} -> {new_access}"
        )
        self._check_ongoing_actions_for_node(node)

    def record_property_change(self, node, property_name: str, old_value, new_value):
        self._publish_event(
            EventType.PROPERTY_CHANGED,
            {
                "node_id": node.id,
                "property_name": property_name,
                "old_value": old_value,
                "new_value": new_value,
            },
        )
        logger.debug(
            f"Property change recorded: {node.id}.{property_name}: {old_value} -> {new_value}"
        )
        self._check_ongoing_actions_for_node(node)

    def get_tim_economic_summary(self, time_interval=None):
        if time_interval is None:
            time_interval = (0.0, self.current_time)
        all_actors = self.get_all_actors()
        attackers = [
            actor for actor in all_actors if hasattr(actor, "is_attacker") and actor.is_attacker
        ]
        defenders = [
            actor for actor in all_actors if hasattr(actor, "is_defender") and actor.is_defender
        ]
        attacker_objectives = {}
        for attacker in attackers:
            attacker_objectives[attacker.id] = self._economic_model.get_attacker_objective(
                attacker.id, attacker.incurred_cost
            )
        defender_objectives = {}
        for defender in defenders:
            defender_objectives[defender.id] = self._economic_model.get_defender_objective(
                defender.id, defender.incurred_cost
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
                        current_access = get_node_access(node, actor_id)
                        if current_access == NodeAccessLevel.NONE:
                            set_node_access(node, actor_id, NodeAccessLevel.VISIBLE)
                            logger.debug(f"Set {node.id} access to VISIBLE for {actor_id}")
                after_count = len(actor.visible_nodes)
                logger.debug(f"{actor_id} visible_nodes: {before_count} → {after_count}")

    def notify_links_discovered(self, actor_id: str, discovered_links: list):
        for actor in self.get_all_actors():
            if actor.id == actor_id and hasattr(actor, "visible_links"):
                for link in discovered_links:
                    if link not in actor.visible_links:
                        actor.visible_links.add(link)
