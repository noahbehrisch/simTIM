"""Integration test — run a small simulation end-to-end.

This test uses a 3-node network with a single attacker and verifies that
the simulator executes correctly: events fire, economics accumulate, and
access levels change as expected.
"""

import pytest

from src.actions.action import Action
from src.core.access_levels import NodeAccessLevel
from src.core.access_utils import get_node_access, set_node_access
from src.core.events import EventBus, EventType
from src.core.network import Link, Network, Node
from src.core.simulator import Simulator
from src.detection.uniform_detection import UniformDetectionEngine

# ── Helpers ───────────────────────────────────────────────────────


def _const(v):
    return lambda *_args: v


class FakeActor:
    """Minimal actor that schedules one action then stops."""

    def __init__(self, actor_id, action, target):
        self.id = actor_id
        self.role = "attacker"
        self.is_attacker = True
        self.is_defender = False
        self.capacity = 10
        self.ongoing_actions = []
        self.pending_action_count = 0
        self.running = True
        self._action = action
        self._target = target
        self._scheduled = False
        self.simulator = None
        self.compromised_nodes: set = set()

    def run(self):
        if not self._scheduled:
            self._scheduled = True
            from src.core.access_utils import get_node_access

            actor_access = get_node_access(self._target, self.id)
            self.simulator.schedule_event(
                self.simulator.current_time,
                "start_action",
                {
                    "action": self._action,
                    "actor": self,
                    "target": self._target,
                    "actor_access": actor_access,
                },
            )

    def can_schedule_action(self):
        return len(self.ongoing_actions) < self.capacity

    def schedule_action(self, action):
        self.ongoing_actions.append(action)

    def record_action_cost(self, action, time):
        self.incurred_cost = getattr(self, "incurred_cost", 0) + action.cost
        self.action_history = getattr(self, "action_history", [])
        self.action_history.append({"timestamp": time, "action": action.name, "cost": action.cost})

    def on_action_finished(self, action, outcome, target):
        if action in self.ongoing_actions:
            self.ongoing_actions.remove(action)


# ── Tests ─────────────────────────────────────────────────────────


class TestMiniSimulation:
    @pytest.fixture
    def network(self):
        n1 = Node(id="internet", software={"os": "Linux"})
        n1.properties = {"exposed_to_internet": True}
        n2 = Node(id="web", software={"os": "Linux", "web_server": "Apache"})
        n2.properties = {}
        n3 = Node(id="db", software={"os": "Linux", "db": "Postgres"})
        n3.properties = {}
        net = Network()
        net.add_node(n1)
        net.add_node(n2)
        net.add_node(n3)
        net.add_link(Link(n1, n2, bidirectional=True))
        net.add_link(Link(n2, n3, bidirectional=True))
        return net

    @pytest.fixture
    def recon_action(self):
        """An action that sets access to VISIBLE when precondition is NONE."""
        return Action(
            name="recon",
            precondition=lambda node, access, aid: access == NodeAccessLevel.NONE,
            postcondition=lambda node, access, aid: set_node_access(
                node, aid, NodeAccessLevel.VISIBLE
            ),
            cost=5.0,
            duration=1.0,
            success_probability=1.0,
            action_type="node",
            detection_probability=_const(0.0),
            one_off_damage=_const(0.0),
            one_off_gain=_const(10.0),
            time_damage=_const(0.0),
            time_gain=_const(0.0),
        )

    def test_simulation_runs_and_produces_history(self, network, recon_action):
        web = network.get_node("web")
        actor = FakeActor("atk", recon_action, web)

        sim = Simulator(
            network=network,
            detection_engine=UniformDetectionEngine(),
        )
        sim.actors = [actor]
        sim.run(until=5.0)

        # Should have produced history events
        assert len(sim.history) > 0

    def test_access_changes_after_successful_action(self, network, recon_action):
        web = network.get_node("web")
        actor = FakeActor("atk", recon_action, web)

        sim = Simulator(
            network=network,
            detection_engine=UniformDetectionEngine(),
        )
        sim.actors = [actor]
        sim.run(until=5.0)

        # Recon postcondition sets VISIBLE
        assert get_node_access(web, "atk") == NodeAccessLevel.VISIBLE

    def test_economic_model_tracks_cost(self, network, recon_action):
        web = network.get_node("web")
        actor = FakeActor("atk", recon_action, web)

        sim = Simulator(
            network=network,
            detection_engine=UniformDetectionEngine(),
        )
        sim.actors = [actor]
        sim.run(until=5.0)

        # Attacker incurred cost via record_action_cost
        assert actor.incurred_cost == pytest.approx(5.0)

    def test_event_bus_records_start_and_end(self, network, recon_action):
        web = network.get_node("web")
        actor = FakeActor("atk", recon_action, web)

        bus = EventBus()
        bus.enable_history()

        sim = Simulator(
            network=network,
            detection_engine=UniformDetectionEngine(),
            event_bus=bus,
        )
        sim.actors = [actor]
        sim.run(until=5.0)

        types = [e.event_type for e in bus.get_history()]
        assert EventType.SIMULATION_STARTED in types
        assert EventType.SIMULATION_ENDED in types
        assert EventType.ACTION_STARTED in types

    def test_no_actors_simulation_still_completes(self, network):
        sim = Simulator(
            network=network,
            detection_engine=UniformDetectionEngine(),
        )
        sim.run(until=2.0)
        # Should complete without error
        assert sim.current_time <= 2.0
