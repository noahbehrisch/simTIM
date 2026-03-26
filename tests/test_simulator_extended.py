"""Extended tests for Simulator, Event, action_manager helpers, and NetworkFactory."""

import pytest

from src.actions.action import Action
from src.actions.action_factory import ActionCreationError, ActionFactory, FunctionSpecError
from src.actions.action_manager import (
    ActionManager,
    _analyze_postcondition_access,
    analyze_action_access_impact,
)
from src.actions.action_registry import ActionRegistry
from src.core.access_levels import NodeAccessLevel
from src.core.events import EventBus, EventType
from src.core.network import Link, Network, Node
from src.core.simulator import Event, Simulator
from src.detection.uniform_detection import UniformDetectionEngine
from src.networks.factory import NetworkCreationError, NetworkFactory

# ── Helpers ───────────────────────────────────────────────────────


def _const(v):
    return lambda *_args: v


def _make_action(
    name="test_action",
    cost=10,
    duration=1.0,
    success_probability=1.0,
    action_type="node",
    precondition_result=True,
    detection_prob=0.0,
):
    return Action(
        name=name,
        precondition=_const(precondition_result),
        postcondition=lambda node, access, actor_id: None,
        cost=cost,
        duration=duration,
        success_probability=success_probability,
        action_type=action_type,
        detection_probability=_const(detection_prob),
        one_off_damage=_const(0.0),
        one_off_gain=_const(0.0),
        time_damage=_const(0.0),
        time_gain=_const(0.0),
    )


# ── Event ──────────────────────────────────────────────────────────


class TestEvent:
    def test_ordering_by_time(self):
        e1 = Event(1.0, "start_action", {})
        e2 = Event(2.0, "start_action", {})
        assert e1 < e2

    def test_ordering_by_priority(self):
        e_finished = Event(1.0, "action_finished", {})
        e_start = Event(1.0, "start_action", {})
        assert e_finished < e_start  # finished has priority 1, start has 6

    def test_repr(self):
        e = Event(1.0, "start_action", {"key": "val"})
        r = repr(e)
        assert "1.0" in r
        assert "start_action" in r

    def test_unknown_event_default_priority(self):
        e = Event(1.0, "custom_event", {})
        assert e.priority == 50


# ── Simulator ──────────────────────────────────────────────────────


class TestSimulatorInit:
    def test_default_init(self):
        sim = Simulator()
        assert sim.current_time == 0.0
        assert sim.network is not None
        assert sim.actors == []
        assert sim.ongoing_actions == []

    def test_custom_network(self):
        net = Network()
        net.add_node(Node(id="n1", software={}))
        sim = Simulator(network=net)
        assert sim.network.node_count == 1

    def test_custom_detection_engine(self):
        engine = UniformDetectionEngine()
        sim = Simulator(detection_engine=engine)
        assert sim.detection_engine is engine

    def test_custom_event_bus(self):
        bus = EventBus()
        sim = Simulator(event_bus=bus)
        assert sim.event_bus is bus

    def test_history_initially_empty(self):
        sim = Simulator()
        assert sim.history == []


class TestSimulatorScheduling:
    def test_schedule_event(self):
        sim = Simulator()
        sim.schedule_event(1.0, "test_event", {"foo": "bar"})
        assert len(sim.event_queue) == 1

    def test_process_unknown_event(self):
        """Unknown events should be published via STATE_CHANGED."""
        sim = Simulator()
        events = []
        sim.event_bus.subscribe(EventType.STATE_CHANGED, lambda e: events.append(e))
        sim.process_event((0.0, "unknown_type", {"data": 1}))
        assert len(events) == 1

    def test_get_all_actors(self):
        sim = Simulator()
        sim.actors = ["a", "b"]
        assert sim.get_all_actors() == ["a", "b"]


class TestSimulatorOngoing:
    def test_ongoing_actions_setter(self):
        sim = Simulator()
        data1 = {"action": "a", "actor": "b", "target": "c"}
        sim.ongoing_actions = [data1]
        assert len(sim.ongoing_actions) == 1

    def test_ongoing_actions_empty(self):
        sim = Simulator()
        assert sim.ongoing_actions == []


class TestSimulatorEconomics:
    def test_get_tim_economic_summary_empty(self):
        sim = Simulator()
        summary = sim.get_tim_economic_summary()
        assert "total_damage" in summary
        assert "attacker_objectives" in summary
        assert "defender_objectives" in summary

    def test_economic_model_property(self):
        sim = Simulator()
        assert sim.economic_model is not None


class TestSimulatorRun:
    def test_empty_run(self):
        """Run with no actors should complete without error."""
        sim = Simulator()
        sim.run(until=1.0)
        assert sim.current_time >= 0.0
        assert len(sim.history) > 0  # at least start/end events


class TestSimulatorNodeDiscovery:
    def test_notify_nodes_discovered(self):
        net = Network()
        n1 = Node(id="n1", software={})
        n2 = Node(id="n2", software={})
        net.add_node(n1)
        net.add_node(n2)

        sim = Simulator(network=net)

        class FakeAttacker:
            id = "atk"
            is_attacker = True
            visible_nodes = set()

        atk = FakeAttacker()
        n1.access = {"atk": NodeAccessLevel.NONE}
        n2.access = {"atk": NodeAccessLevel.NONE}
        sim.actors = [atk]

        sim.notify_nodes_discovered("atk", [n1, n2])
        assert n1 in atk.visible_nodes
        assert n2 in atk.visible_nodes

    def test_notify_links_discovered(self):
        net = Network()
        n1 = Node(id="n1", software={})
        n2 = Node(id="n2", software={})
        net.add_node(n1)
        net.add_node(n2)
        link = Link(n1, n2, bidirectional=True)
        net.add_link(link)

        sim = Simulator(network=net)

        class FakeAttacker:
            id = "atk"
            is_attacker = True
            visible_links = set()

        atk = FakeAttacker()
        sim.actors = [atk]

        sim.notify_links_discovered("atk", [link])
        assert link in atk.visible_links


# ── ActionRegistry ─────────────────────────────────────────────────


class TestActionRegistry:
    def setup_method(self):
        self.reg = ActionRegistry()

    def test_register_and_get(self):
        a = _make_action("exploit")
        self.reg.register(a, "attack")
        assert self.reg.get("exploit") is a

    def test_register_many(self):
        a1 = _make_action("a1")
        a2 = _make_action("a2")
        count = self.reg.register_many([a1, a2], "attack")
        assert count == 2
        assert len(self.reg) == 2

    def test_unregister(self):
        a = _make_action("exploit")
        self.reg.register(a, "attack")
        removed = self.reg.unregister("exploit")
        assert removed is a
        assert self.reg.get("exploit") is None

    def test_unregister_nonexistent(self):
        assert self.reg.unregister("nope") is None

    def test_get_all(self):
        a = _make_action("a1")
        self.reg.register(a)
        assert len(self.reg.get_all()) == 1

    def test_get_by_category(self):
        a = _make_action("exploit")
        self.reg.register(a, "attack")
        assert len(self.reg.get_by_category("attack")) == 1
        assert len(self.reg.get_by_category("defense")) == 0

    def test_get_by_type(self):
        a = _make_action("exploit", action_type="node")
        self.reg.register(a)
        assert len(self.reg.get_by_type("node")) == 1
        assert len(self.reg.get_by_type("link")) == 0

    def test_get_attack_defense_actions(self):
        a = _make_action("exploit")
        d = _make_action("patch")
        self.reg.register(a, "attack")
        self.reg.register(d, "defense")
        assert len(self.reg.get_attack_actions()) == 1
        assert len(self.reg.get_defense_actions()) == 1

    def test_filter_by_category(self):
        a = _make_action("exploit")
        self.reg.register(a, "attack")
        results = self.reg.filter(category="attack")
        assert len(results) == 1

    def test_filter_by_type(self):
        a = _make_action("exploit", action_type="node")
        self.reg.register(a)
        results = self.reg.filter(action_type="node")
        assert len(results) == 1

    def test_filter_by_name(self):
        a = _make_action("Remote Exploit")
        self.reg.register(a)
        results = self.reg.filter(name_contains="remote")
        assert len(results) == 1

    def test_contains(self):
        a = _make_action("exploit")
        self.reg.register(a)
        assert self.reg.contains("exploit")
        assert "exploit" in self.reg
        assert not self.reg.contains("nope")

    def test_clear(self):
        a = _make_action("exploit")
        self.reg.register(a)
        self.reg.clear()
        assert len(self.reg) == 0

    def test_iter(self):
        a = _make_action("exploit")
        self.reg.register(a)
        items = list(self.reg)
        assert len(items) == 1

    def test_summary(self):
        a = _make_action("exploit")
        self.reg.register(a, "attack")
        s = self.reg.summary()
        assert s["total"] == 1
        assert "attack" in s["by_category"]

    def test_get_categories(self):
        a = _make_action("exploit")
        self.reg.register(a, "attack")
        assert "attack" in self.reg.get_categories()

    def test_get_names(self):
        a = _make_action("exploit")
        self.reg.register(a)
        assert "exploit" in self.reg.get_names()

    def test_get_node_link_actions(self):
        n = _make_action("n_act", action_type="node")
        lnk = _make_action("l_act", action_type="link")
        self.reg.register(n)
        self.reg.register(lnk)
        assert len(self.reg.get_node_actions()) == 1
        assert len(self.reg.get_link_actions()) == 1

    def test_replace_existing(self):
        a1 = _make_action("exploit", cost=10)
        a2 = _make_action("exploit", cost=20)
        self.reg.register(a1, "attack")
        self.reg.register(a2, "attack")
        assert self.reg.get("exploit").cost == 20
        assert len(self.reg) == 1


# ── ActionFactory ──────────────────────────────────────────────────


class TestActionFactory:
    def setup_method(self):
        self.factory = ActionFactory()

    def test_create_from_json(self):
        data = {
            "name": "Test Exploit",
            "action_type": "node",
            "cost": 100,
            "duration": 2.0,
            "success_probability": 0.8,
            "precondition": {"type": "constant", "value": True},
            "postcondition": {"type": "constant", "value": True},
            "detection_probability": {"type": "constant", "value": 0.3},
            "damage_gain": {
                "one_off_damage": 500.0,
                "one_off_gain": 300.0,
                "time_damage": 10.0,
                "time_gain": 5.0,
            },
        }
        action = self.factory.create(data)
        assert action.name == "Test Exploit"
        assert action.cost == 100
        assert action.duration == 2.0
        assert action._json_data is data

    def test_create_invalid_raises(self):
        with pytest.raises(ActionCreationError):
            self.factory.create({"name": "bad"})

    def test_create_with_zero_detection(self):
        data = {
            "name": "Stealth",
            "action_type": "node",
            "cost": 50,
            "duration": 1.0,
            "success_probability": 1.0,
            "precondition": {"type": "constant", "value": True},
            "postcondition": {"type": "constant", "value": True},
            "detection_probability": {"type": "zero"},
            "damage_gain": {
                "one_off_damage": 0.0,
                "one_off_gain": 0.0,
                "time_damage": 0.0,
                "time_gain": 0.0,
            },
        }
        action = self.factory.create(data)
        assert action.detection_probability(None, None, None) == 0.0

    def test_to_json_with_json_data(self):
        data = {
            "name": "X",
            "action_type": "node",
            "cost": 10,
            "duration": 1.0,
            "success_probability": 1.0,
            "precondition": {"type": "constant", "value": True},
            "postcondition": {"type": "constant", "value": True},
            "detection_probability": {"type": "constant", "value": 0.0},
            "damage_gain": {
                "one_off_damage": 0.0,
                "one_off_gain": 0.0,
                "time_damage": 0.0,
                "time_gain": 0.0,
            },
        }
        action = self.factory.create(data)
        j = self.factory.to_json(action)
        assert j["name"] == "X"

    def test_to_json_without_json_data(self):
        a = _make_action("manual")
        f = ActionFactory()
        j = f.to_json(a)
        assert j["name"] == "manual"
        assert "damage_gain" in j

    def test_unknown_spec_type_raises(self):
        with pytest.raises(FunctionSpecError):
            self.factory._create_condition_function({"type": "alien_logic"})

    def test_postcondition_compound(self):
        spec = {"type": "compound", "actions": []}
        func = self.factory._create_postcondition(spec)
        assert callable(func)

    def test_postcondition_set_access(self):
        spec = {"type": "set_access", "value": "USER"}
        func = self.factory._create_postcondition(spec)
        assert callable(func)

    def test_property_based_detection(self):
        spec = {
            "type": "node_property_based",
            "base_probability": 0.2,
            "property_modifiers": [
                {"property": "exposed_to_internet", "value": True, "probability_modifier": 0.3}
            ],
        }
        func = self.factory._create_detection_function(spec)
        node = Node(id="n", software={})
        node.exposed_to_internet = True
        result = func(node, None, None)
        assert result == pytest.approx(0.5)

    def test_property_based_detection_clamped(self):
        spec = {
            "type": "node_property_based",
            "base_probability": 0.9,
            "property_modifiers": [
                {"property": "exposed_to_internet", "value": True, "probability_modifier": 0.5}
            ],
        }
        func = self.factory._create_detection_function(spec)
        node = Node(id="n", software={})
        node.exposed_to_internet = True
        result = func(node, None, None)
        assert result == 1.0  # clamped to max 1.0

    def test_damage_functions(self):
        dg = {
            "one_off_damage": 100.0,
            "one_off_gain": 50.0,
            "time_damage": 10.0,
            "time_gain": 5.0,
        }
        funcs = self.factory._create_damage_functions(dg)
        assert funcs["one_off_damage"](None, None, None) == 100.0
        assert funcs["one_off_gain"](None, None, None) == 50.0
        assert funcs["time_damage"](None, None, None) == 10.0
        assert funcs["time_gain"](None, None, None) == 5.0

    def test_validator_property(self):
        from src.actions.action_validator import ActionValidator

        assert isinstance(self.factory.validator, ActionValidator)


# ── NetworkFactory ─────────────────────────────────────────────────


class TestNetworkFactory:
    def setup_method(self):
        self.factory = NetworkFactory()

    def test_create_simple_network(self):
        config = {
            "nodes": [
                {
                    "id": "web",
                    "software": {"os": "Linux"},
                    "properties": {"exposed_to_internet": True},
                },
                {"id": "db", "software": {"os": "Linux"}},
            ],
            "links": [
                {"node1": "web", "node2": "db", "bidirectional": True},
            ],
        }
        net = self.factory.create(config)
        assert net.node_count == 2
        assert net.link_count == 1

    def test_create_no_links(self):
        config = {"nodes": [{"id": "solo", "software": {}}]}
        net = self.factory.create(config)
        assert net.node_count == 1
        assert net.link_count == 0

    def test_invalid_config_raises(self):
        with pytest.raises(NetworkCreationError):
            self.factory.create({})  # missing nodes

    def test_unknown_node_in_link_raises(self):
        config = {
            "nodes": [{"id": "n1", "software": {}}],
            "links": [{"node1": "n1", "node2": "missing"}],
        }
        with pytest.raises(NetworkCreationError):
            self.factory.create(config)

    def test_to_config(self):
        config = {
            "nodes": [
                {"id": "web", "software": {"os": "Linux"}},
                {"id": "db", "software": {"os": "Linux"}},
            ],
            "links": [{"node1": "web", "node2": "db"}],
        }
        net = self.factory.create(config)
        exported = self.factory.to_config(net)
        assert len(exported["nodes"]) == 2
        assert len(exported["links"]) == 1

    def test_node_properties_set(self):
        config = {
            "nodes": [
                {
                    "id": "web",
                    "software": {"os": "Linux"},
                    "properties": {"exposed_to_internet": True, "custom": "val"},
                }
            ],
        }
        net = self.factory.create(config)
        node = net.get_node("web")
        assert node.exposed_to_internet is True
        assert node.properties.get("custom") == "val"

    def test_node_with_coordinates(self):
        config = {
            "nodes": [
                {"id": "n1", "software": {}, "x": 100, "y": 200},
            ],
        }
        net = self.factory.create(config)
        node = net.get_node("n1")
        assert node.properties.get("x") == 100
        assert node.properties.get("y") == 200

    def test_link_latency(self):
        config = {
            "nodes": [
                {"id": "n1", "software": {}},
                {"id": "n2", "software": {}},
            ],
            "links": [{"node1": "n1", "node2": "n2", "latency": 5.0}],
        }
        net = self.factory.create(config)
        assert net.links[0].latency == 5.0

    def test_skip_validation(self):
        config = {
            "nodes": [{"id": "n1", "software": {}}],
        }
        net = self.factory.create(config, validate=False)
        assert net.node_count == 1

    def test_validator_property(self):
        from src.networks.validation import NetworkValidator

        assert isinstance(self.factory.validator, NetworkValidator)


# ── analyze_action_access_impact ───────────────────────────────────


class TestAnalyzeActionAccessImpact:
    def test_set_access_postcondition(self):
        a = _make_action("exploit")
        a._json_data = {"postcondition": {"type": "set_access", "value": "USER"}}
        result = analyze_action_access_impact(a, "NONE")
        assert result == "USER"

    def test_compound_postcondition(self):
        a = _make_action("exploit")
        a._json_data = {
            "postcondition": {
                "type": "compound",
                "actions": [{"type": "set_access", "value": "ADMIN"}],
            }
        }
        result = analyze_action_access_impact(a, "NONE")
        assert result == "ADMIN"

    def test_no_access_change_type(self):
        a = _make_action("harden")
        a._json_data = {"postcondition": {"type": "set_property"}}
        result = analyze_action_access_impact(a, "NONE")
        assert result == "NO_ACCESS_CHANGE"

    def test_no_json_data(self):
        a = _make_action("x")
        assert analyze_action_access_impact(a, "NONE") is None

    def test_analyze_postcondition_unknown_type(self):
        result = _analyze_postcondition_access({"type": "magic"})
        assert result is None


# ── ActionManager (no auto-load) ───────────────────────────────────


class TestActionManager:
    def setup_method(self):
        self.manager = ActionManager(auto_load=False)

    def test_register_and_get(self):
        a = _make_action("exploit")
        self.manager.register_action(a, "attack")
        assert self.manager.get_action("exploit") is a

    def test_get_all_available(self):
        a = _make_action("exploit")
        self.manager.register_action(a)
        assert len(self.manager.get_all_available_actions()) == 1

    def test_summary(self):
        a = _make_action("exploit")
        self.manager.register_action(a, "attack")
        s = self.manager.summary()
        assert s["total"] == 1

    def test_validate_action_json_valid(self):
        data = {
            "name": "Test",
            "action_type": "node",
            "cost": 10,
            "duration": 1.0,
            "success_probability": 0.5,
            "precondition": {"type": "constant", "value": True},
            "postcondition": {"type": "constant", "value": True},
            "detection_probability": {"type": "constant", "value": 0.1},
            "damage_gain": {
                "one_off_damage": 0.0,
                "one_off_gain": 0.0,
                "time_damage": 0.0,
                "time_gain": 0.0,
            },
        }
        result = self.manager.validate_action_json(data)
        assert result["valid"] is True

    def test_validate_action_json_invalid(self):
        result = self.manager.validate_action_json({"name": "bad"})
        assert result["valid"] is False
        assert len(result["errors"]) > 0

    def test_action_from_json(self):
        data = {
            "name": "Test",
            "action_type": "node",
            "cost": 10,
            "duration": 1.0,
            "success_probability": 0.5,
            "precondition": {"type": "constant", "value": True},
            "postcondition": {"type": "constant", "value": True},
            "detection_probability": {"type": "constant", "value": 0.1},
            "damage_gain": {
                "one_off_damage": 0.0,
                "one_off_gain": 0.0,
                "time_damage": 0.0,
                "time_gain": 0.0,
            },
        }
        a = self.manager.action_from_json(data)
        assert a.name == "Test"

    def test_action_to_json(self):
        a = _make_action("x")
        j = self.manager.action_to_json(a)
        assert j["name"] == "x"

    def test_load_specific_actions(self):
        a = _make_action("exploit")
        self.manager.register_action(a, "attack")
        loaded = self.manager.load_specific_actions(["exploit", "missing"])
        assert len(loaded) == 1

    def test_properties(self):
        from src.actions.action_factory import ActionFactory as AF
        from src.actions.action_loader import ActionLoader as AL
        from src.actions.action_registry import ActionRegistry as AR
        from src.actions.action_validator import ActionValidator

        assert isinstance(self.manager.validator, ActionValidator)
        assert isinstance(self.manager.factory, AF)
        assert isinstance(self.manager.registry, AR)
        assert isinstance(self.manager.loader, AL)
