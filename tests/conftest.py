"""Shared fixtures for simTIM tests."""

import pytest

from src.core.network import Link, Network, Node

# ── Nodes ──────────────────────────────────────────────────────────


@pytest.fixture
def web_server():
    node = Node(
        id="webserver",
        software={"os": "Ubuntu", "web_server": "Apache"},
        assets=["web_application"],
    )
    node.exposed_to_internet = True
    node.properties["exposed_to_internet"] = True
    return node


@pytest.fixture
def db_server():
    return Node(
        id="database",
        software={"os": "Ubuntu", "database": "PostgreSQL"},
        assets=["customer_data", "financial_records"],
    )


@pytest.fixture
def workstation():
    return Node(
        id="workstation",
        software={"os": "Windows 10"},
        assets=[],
    )


@pytest.fixture
def clean_node():
    """A node with no assets or special properties."""
    return Node(id="clean", software={"os": "Linux"})


# ── Networks ───────────────────────────────────────────────────────


@pytest.fixture
def simple_network(web_server, db_server, workstation):
    net = Network()
    net.add_node(web_server)
    net.add_node(db_server)
    net.add_node(workstation)
    link1 = Link(web_server, workstation, bidirectional=True)
    link2 = Link(workstation, db_server, bidirectional=True)
    net.add_link(link1)
    net.add_link(link2)
    return net


@pytest.fixture
def simple_network_config():
    """Raw JSON-style dict config for network validation tests."""
    return {
        "nodes": [
            {
                "id": "webserver",
                "software": {"os": "Ubuntu"},
                "properties": {"exposed_to_internet": True},
            },
            {
                "id": "database",
                "software": {"os": "Ubuntu"},
            },
        ],
        "links": [
            {"node1": "webserver", "node2": "database", "bidirectional": True},
        ],
    }


# ── Actions ────────────────────────────────────────────────────────


def _const(val):
    """Return a callable that ignores all args and returns val."""
    return lambda node, access, actor_id: val


@pytest.fixture
def stub_action_data():
    """Minimal valid action JSON data for validator tests."""
    return {
        "name": "Test Action",
        "action_type": "node",
        "cost": 100,
        "duration": 2.0,
        "success_probability": 0.5,
        "precondition": {"type": "access_check", "operator": "equals", "value": "VISIBLE"},
        "postcondition": {"type": "set_access", "value": "USER"},
        "detection_probability": {"type": "constant", "value": 0.3},
        "damage_gain": {
            "one_off_damage": 500.0,
            "one_off_gain": 300.0,
            "time_damage": 10.0,
            "time_gain": 5.0,
        },
    }


@pytest.fixture
def make_action():
    """Factory fixture to create Action objects with stub callables."""
    from src.actions.action import Action

    def _make(
        name="test_action",
        cost=100,
        duration=2.0,
        success_probability=0.5,
        action_type="node",
        precondition_result=True,
        detection_prob=0.3,
        one_off_damage=500.0,
        one_off_gain=300.0,
        time_damage=10.0,
        time_gain=5.0,
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
            one_off_damage=_const(one_off_damage),
            one_off_gain=_const(one_off_gain),
            time_damage=_const(time_damage),
            time_gain=_const(time_gain),
        )

    return _make
