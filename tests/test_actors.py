"""Tests for actors: Actor, Attacker, Defender, ActorFactory, ActorValidator."""

import pytest

from src.actors.actor import Actor
from src.actors.attacker import Attacker
from src.actors.defender import Defender
from src.actors.factory import (
    ActorCreationError,
    ActorFactory,
    ActorValidator,
    create_actor,
    create_attacker,
    create_defender,
    get_actor_factory,
)

# ── Actor base class ──────────────────────────────────────────────


class TestActor:
    def test_init_defaults(self):
        a = Actor("a1", "attacker")
        assert a.id == "a1"
        assert a.role == "attacker"
        assert a.capacity == 1
        assert a.budget == float("inf")
        assert a.incurred_cost == 0.0
        assert a.running is False
        assert a.decision_interval == 1.0

    def test_init_custom(self):
        a = Actor("a2", "defender", capacity=5, strategy="reactive", budget=1000.0)
        assert a.capacity == 5
        assert a.strategy == "reactive"
        assert a.budget == 1000.0

    def test_can_schedule_action_capacity(self):
        a = Actor("a1", "attacker", capacity=2)
        assert a.can_schedule_action() is True
        # Simulate filling capacity via pending count
        a.pending_action_count = 2
        assert a.can_schedule_action() is False

    def test_can_schedule_action_budget(self):
        a = Actor("a1", "attacker", capacity=5, budget=100.0)
        a.incurred_cost = 100.0
        assert a.can_schedule_action() is False

    def test_can_schedule_action_infinite(self):
        a = Actor("a1", "attacker", capacity=float("inf"), budget=float("inf"))
        assert a.can_schedule_action() is True

    def test_run_not_running(self):
        a = Actor("a1", "attacker")
        a.running = False
        # Should return immediately without error
        a.run()

    def test_record_action_cost(self, make_action):
        a = Actor("a1", "attacker", budget=500.0)
        action = make_action(name="exploit", cost=100)
        a.record_action_cost(action, 1.0)
        assert a.incurred_cost == 100
        action2 = make_action(name="scan", cost=50)
        a.record_action_cost(action2, 2.0)
        assert a.incurred_cost == 150
        assert len(a.action_history) == 2

    def test_record_economic_event(self):
        a = Actor("a1", "attacker")
        a.record_economic_event(1.0, "cost", 100.0, {"action": "exploit"})
        assert len(a.economic_events) == 1
        assert a.economic_events[0]["timestamp"] == 1.0
        assert a.economic_events[0]["type"] == "cost"
        assert a.economic_events[0]["value"] == 100.0

    def test_record_economic_event_no_details(self):
        a = Actor("a1", "attacker")
        a.record_economic_event(0.0, "gain", 50.0)
        assert a.economic_events[0]["details"] == {}

    def test_get_concurrent_actions_count(self):
        a = Actor("a1", "attacker")
        assert a.get_concurrent_actions_count() == 0

    def test_schedule_action(self):
        a = Actor("a1", "attacker", capacity=2)

        class FakeAction:
            name = "fake"

        action = FakeAction()
        a.schedule_action(action)
        assert action in a.ongoing_actions
        assert a.get_concurrent_actions_count() == 1

    def test_notify_action_finished(self):
        a = Actor("a1", "attacker")

        class FakeAction:
            name = "fake"

        action = FakeAction()
        a.schedule_action(action)
        a.notify_action_finished(action, "success")
        assert action not in a.ongoing_actions


# ── Attacker ───────────────────────────────────────────────────────


class TestAttacker:
    def test_init_defaults(self):
        att = Attacker("att1")
        assert att.id == "att1"
        assert att.role == "attacker"
        assert att.is_attacker is True
        assert att.capacity == float("inf")
        assert att.budget == float("inf")
        assert att.strategy == "random"
        assert att.compromised_nodes == set()

    def test_init_custom(self):
        att = Attacker("att2", strategy="greedy", capacity=3, budget=500.0)
        assert att.strategy == "greedy"
        assert att.capacity == 3
        assert att.budget == 500.0

    def test_change_strategy(self):
        att = Attacker("att1", strategy="random")
        att.change_strategy("greedy")
        assert att.strategy == "greedy"

    def test_on_action_finished_removes(self):
        att = Attacker("att1")

        class FakeAction:
            name = "exploit"

        action = FakeAction()
        att.ongoing_actions.add(action)
        att.on_action_finished(action, "failure")
        assert action not in att.ongoing_actions


# ── Defender ───────────────────────────────────────────────────────


class TestDefender:
    def test_init_defaults(self):
        d = Defender("def1")
        assert d.id == "def1"
        assert d.role == "defender"
        assert d.is_defender is True
        assert d.is_attacker is False
        assert d.capacity == 2
        assert d.strategy == "reactive"
        assert d.detected_attacks == []

    def test_init_custom(self):
        d = Defender("def2", strategy="reactive", capacity=5, budget=2000.0)
        assert d.capacity == 5
        assert d.budget == 2000.0

    def test_change_strategy(self):
        d = Defender("def1")
        d.change_strategy("reactive")
        assert d.strategy == "reactive"

    def test_on_action_finished_removes(self):
        d = Defender("def1")

        class FakeAction:
            name = "patch"

        action = FakeAction()
        d.ongoing_actions.add(action)
        d.on_action_finished(action, "success")
        assert action not in d.ongoing_actions

    def test_on_attack_detected_invalid_data(self):
        d = Defender("def1")
        # Missing required keys — should warn and return
        d.on_attack_detected({})
        assert len(d.detected_attacks) == 0

    def test_record_detection_economics(self):
        d = Defender("def1")
        d.simulator = None  # getattr handles None
        d.record_detection_economics("attacker1", damage_prevented=100.0, detection_cost=25.0)
        assert d.incurred_cost == 25.0
        assert len(d.economic_events) == 2


# ── ActorValidator ─────────────────────────────────────────────────


class TestActorValidator:
    def setup_method(self):
        self.validator = ActorValidator()

    def test_valid_attacker(self):
        r = self.validator.validate({"id": "att1", "role": "attacker"})
        assert r.valid is True
        assert r.errors == []

    def test_valid_defender(self):
        r = self.validator.validate({"id": "def1", "role": "defender"})
        assert r.valid is True

    def test_missing_id(self):
        r = self.validator.validate({"role": "attacker"})
        assert r.valid is False
        assert any("id" in e for e in r.errors)

    def test_missing_role(self):
        r = self.validator.validate({"id": "x"})
        assert r.valid is False
        assert any("role" in e for e in r.errors)

    def test_empty_id(self):
        r = self.validator.validate({"id": "", "role": "attacker"})
        assert r.valid is False

    def test_invalid_role(self):
        r = self.validator.validate({"id": "x", "role": "wizard"})
        assert r.valid is False
        assert any("Invalid role" in e for e in r.errors)

    def test_non_dict(self):
        r = self.validator.validate("not a dict")
        assert r.valid is False
        assert any("dictionary" in e for e in r.errors)

    def test_capacity_warning(self):
        r = self.validator.validate({"id": "x", "role": "attacker", "capacity": 0})
        assert r.valid is True
        assert any("capacity" in w for w in r.warnings)

    def test_budget_warning(self):
        r = self.validator.validate({"id": "x", "role": "attacker", "budget": 0})
        assert r.valid is True
        assert any("budget" in w for w in r.warnings)

    def test_invalid_capacity_type(self):
        r = self.validator.validate({"id": "x", "role": "attacker", "capacity": "many"})
        assert r.valid is False

    def test_invalid_budget_type(self):
        r = self.validator.validate({"id": "x", "role": "attacker", "budget": "rich"})
        assert r.valid is False

    def test_invalid_strategy_type(self):
        r = self.validator.validate({"id": "x", "role": "attacker", "strategy": 42})
        assert r.valid is False

    def test_infinity_capacity(self):
        r = self.validator.validate({"id": "x", "role": "attacker", "capacity": float("inf")})
        assert r.valid is True

    def test_infinity_budget(self):
        r = self.validator.validate({"id": "x", "role": "attacker", "budget": float("inf")})
        assert r.valid is True

    def test_non_string_role(self):
        r = self.validator.validate({"id": "x", "role": 123})
        assert r.valid is False

    def test_non_string_id(self):
        r = self.validator.validate({"id": 123, "role": "attacker"})
        assert r.valid is False


# ── ActorFactory ───────────────────────────────────────────────────


class TestActorFactory:
    def setup_method(self):
        self.factory = ActorFactory()

    def test_create_attacker_from_config(self):
        actor = self.factory.create({"id": "att1", "role": "attacker", "strategy": "random"})
        assert isinstance(actor, Attacker)
        assert actor.id == "att1"

    def test_create_defender_from_config(self):
        actor = self.factory.create({"id": "def1", "role": "defender"})
        assert isinstance(actor, Defender)

    def test_create_attacker_convenience(self):
        att = self.factory.create_attacker("att1", strategy="greedy")
        assert isinstance(att, Attacker)
        assert att.strategy == "greedy"

    def test_create_defender_convenience(self):
        d = self.factory.create_defender("def1")
        assert isinstance(d, Defender)

    def test_invalid_config_raises(self):
        with pytest.raises(ActorCreationError):
            self.factory.create({"role": "attacker"})  # missing id

    def test_unknown_role_raises(self):
        with pytest.raises(ActorCreationError):
            self.factory.create({"id": "x", "role": "wizard"})

    def test_to_config(self):
        att = self.factory.create_attacker("att1", strategy="greedy", capacity=3, budget=500.0)
        config = self.factory.to_config(att)
        assert config["id"] == "att1"
        assert config["role"] == "attacker"
        assert config["strategy"] == "greedy"
        assert config["capacity"] == 3

    def test_decision_interval_in_config(self):
        actor = self.factory.create({"id": "att1", "role": "attacker", "decision_interval": 2.5})
        assert actor.decision_interval == 2.5

    def test_skip_validation(self):
        # Even invalid config should work with validate=False (will fail later)
        with pytest.raises(ActorCreationError):
            self.factory.create({"id": "", "role": "wizard"}, validate=False)

    def test_validator_property(self):
        assert isinstance(self.factory.validator, ActorValidator)


# ── Module-level convenience functions ─────────────────────────────


class TestModuleFunctions:
    def test_get_actor_factory(self):
        f = get_actor_factory()
        assert isinstance(f, ActorFactory)

    def test_create_actor(self):
        actor = create_actor({"id": "a1", "role": "attacker"})
        assert isinstance(actor, Attacker)

    def test_create_attacker_func(self):
        att = create_attacker("a1")
        assert isinstance(att, Attacker)

    def test_create_defender_func(self):
        d = create_defender("d1")
        assert isinstance(d, Defender)
