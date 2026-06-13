"""Tests for the Action class."""

import pytest

from src.actions.action import Action
from src.core.access_levels import NodeAccessLevel
from src.core.network import Node


@pytest.fixture
def dummy_node():
    return Node(id="web", software={"os": "Linux"})


def _const(value):
    """Return a 3-arg callable that always returns *value*."""
    return lambda node, access, actor_id: value


def _make_action(**overrides):
    defaults = {
        "name": "test",
        "precondition": _const(True),
        "postcondition": _const(None),
        "cost": 10.0,
        "duration": 1.0,
        "success_probability": 0.8,
        "action_type": "node",
        "detection_probability": _const(0.5),
        "one_off_damage": _const(100.0),
        "one_off_gain": _const(50.0),
        "time_damage": _const(10.0),
        "time_gain": _const(5.0),
    }
    defaults.update(overrides)
    return Action(**defaults)


class TestActionConstruction:
    def test_attributes_stored(self):
        a = _make_action(name="recon", cost=15)
        assert a.name == "recon"
        assert a.cost == 15

    def test_repr(self):
        a = _make_action(name="scan")
        r = repr(a)
        assert "scan" in r
        assert "node" in r


class TestActionType:
    def test_node_action(self):
        a = _make_action(action_type="node")
        assert a.is_node_action()
        assert not a.is_link_action()

    def test_link_action(self):
        a = _make_action(action_type="link")
        assert a.is_link_action()
        assert not a.is_node_action()


class TestCallableDelegation:
    def test_detection_probability(self, dummy_node):
        a = _make_action(detection_probability=_const(0.42))
        assert a.get_detection_probability(dummy_node, NodeAccessLevel.NONE, "atk") == 0.42

    def test_one_off_damage(self, dummy_node):
        a = _make_action(one_off_damage=_const(99))
        assert a.get_one_off_damage(dummy_node, NodeAccessLevel.NONE, "atk") == 99

    def test_one_off_gain(self, dummy_node):
        a = _make_action(one_off_gain=_const(77))
        assert a.get_one_off_gain(dummy_node, NodeAccessLevel.NONE, "atk") == 77

    def test_time_damage(self, dummy_node):
        a = _make_action(time_damage=_const(3.5))
        assert a.get_time_damage(dummy_node, NodeAccessLevel.NONE, "atk") == 3.5

    def test_time_gain(self, dummy_node):
        a = _make_action(time_gain=_const(2.5))
        assert a.get_time_gain(dummy_node, NodeAccessLevel.NONE, "atk") == 2.5


class TestPreconditionPostcondition:
    def test_precondition_called(self, dummy_node):
        a = _make_action(precondition=_const(False))
        assert a.precondition(dummy_node, NodeAccessLevel.NONE, "atk") is False

    def test_postcondition_callable(self, dummy_node):
        effects = []
        a = _make_action(postcondition=lambda n, a, aid: effects.append(n.id))
        a.postcondition(dummy_node, NodeAccessLevel.NONE, "atk")
        assert effects == ["web"]


class TestToJson:
    def test_raises_without_json_data(self):
        a = _make_action()
        with pytest.raises(ValueError, match="programmatically"):
            a.to_json()

    def test_returns_copy_when_json_data_set(self):
        a = _make_action()
        a._json_data = {"name": "test", "cost": 10}
        result = a.to_json()
        assert result == {"name": "test", "cost": 10}
        # must be a copy
        result["name"] = "modified"
        assert a._json_data["name"] == "test"
