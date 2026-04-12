"""Tests for duck-typed access utility functions."""

from types import SimpleNamespace

import pytest

from src.core.access_levels import LinkAccessLevel, NodeAccessLevel
from src.core.access_utils import (
    get_link_access,
    get_link_access_string,
    get_node_access,
    get_node_access_string,
    get_node_assets,
    get_node_property,
    get_node_software,
    set_link_access,
    set_node_access,
    set_node_property,
    validate_actor,
    validate_node,
)

# ── Helpers ───────────────────────────────────────────────────────


def _bare():
    """Object with no attributes at all."""
    return SimpleNamespace()


def _node(**kw):
    defaults = {
        "id": "n1",
        "access": {},
        "properties": {},
        "software": {},
        "assets": [],
    }
    defaults.update(kw)
    return SimpleNamespace(**defaults)


# ── Node access ──────────────────────────────────────────────────


class TestGetNodeAccess:
    def test_returns_default_when_no_access_attr(self):
        obj = _bare()
        assert get_node_access(obj, "atk") == NodeAccessLevel.NONE

    def test_custom_default(self):
        obj = _bare()
        assert get_node_access(obj, "atk", NodeAccessLevel.VISIBLE) == NodeAccessLevel.VISIBLE

    def test_returns_stored_level(self):
        node = _node(access={"atk": NodeAccessLevel.ADMIN})
        assert get_node_access(node, "atk") == NodeAccessLevel.ADMIN

    def test_converts_string_to_enum(self):
        node = _node(access={"atk": "USER"})
        level = get_node_access(node, "atk")
        assert level == NodeAccessLevel.USER
        # should also have mutated in-place
        assert node.access["atk"] is NodeAccessLevel.USER


class TestSetNodeAccess:
    def test_set_on_node(self):
        node = _node()
        set_node_access(node, "atk", NodeAccessLevel.ADMIN)
        assert node.access["atk"] == NodeAccessLevel.ADMIN

    def test_creates_access_dict_if_missing(self):
        obj = _bare()
        set_node_access(obj, "atk", NodeAccessLevel.USER)
        assert obj.access["atk"] == NodeAccessLevel.USER

    def test_rejects_wrong_type(self):
        with pytest.raises(TypeError):
            set_node_access(_node(), "atk", "ADMIN")


class TestGetNodeAccessString:
    def test_returns_string(self):
        node = _node(access={"atk": NodeAccessLevel.VISIBLE})
        assert get_node_access_string(node, "atk") == "VISIBLE"

    def test_default_is_none_string(self):
        assert get_node_access_string(_bare(), "atk") == "NONE"


# ── Link access ──────────────────────────────────────────────────


class TestGetLinkAccess:
    def test_returns_default(self):
        assert get_link_access(_bare(), "atk") == LinkAccessLevel.NONE

    def test_converts_string(self):
        link = SimpleNamespace(access={"atk": "VISIBLE"})
        assert get_link_access(link, "atk") == LinkAccessLevel.VISIBLE


class TestSetLinkAccess:
    def test_set_on_link(self):
        link = SimpleNamespace(access={})
        set_link_access(link, "atk", LinkAccessLevel.VISIBLE)
        assert link.access["atk"] == LinkAccessLevel.VISIBLE

    def test_rejects_wrong_type(self):
        with pytest.raises(TypeError):
            set_link_access(SimpleNamespace(access={}), "atk", "VISIBLE")


class TestGetLinkAccessString:
    def test_returns_string(self):
        link = SimpleNamespace(access={"atk": LinkAccessLevel.VISIBLE})
        assert get_link_access_string(link, "atk") == "VISIBLE"


# ── Property / software helpers ──────────────────────────────────


class TestNodePropertyHelpers:
    def test_get_existing_property(self):
        node = _node(properties={"critical": True})
        assert get_node_property(node, "critical") is True

    def test_get_missing_property_returns_default(self):
        assert get_node_property(_node(), "xyz", 42) == 42

    def test_get_property_no_properties_attr(self):
        assert get_node_property(_bare(), "key") is None

    def test_set_property(self):
        node = _node()
        set_node_property(node, "patched", True)
        assert node.properties["patched"] is True

    def test_set_property_creates_dict(self):
        obj = _bare()
        set_node_property(obj, "x", 1)
        assert obj.properties["x"] == 1


class TestSoftwareHelper:
    def test_get_existing(self):
        node = _node(software={"os": "Linux"})
        assert get_node_software(node, "os") == "Linux"

    def test_missing_key(self):
        assert get_node_software(_node(), "db", "none") == "none"

    def test_no_software_attr(self):
        assert get_node_software(_bare(), "os") is None


class TestAssetHelpers:
    def test_get_assets(self):
        node = _node(assets=["customer_data"])
        assert get_node_assets(node) == ["customer_data"]

    def test_empty_when_missing(self):
        assert get_node_assets(_bare()) == []


# ── validate_actor / validate_node ───────────────────────────────


class TestValidateActor:
    def test_valid(self):
        actor = SimpleNamespace(id="a1", role="attacker", capacity=1)
        assert validate_actor(actor)["valid"]

    def test_missing_id(self):
        actor = SimpleNamespace(role="attacker", capacity=1)
        result = validate_actor(actor)
        assert not result["valid"]

    def test_missing_role(self):
        actor = SimpleNamespace(id="a1", capacity=1)
        result = validate_actor(actor)
        assert not result["valid"]

    def test_missing_capacity(self):
        actor = SimpleNamespace(id="a1", role="attacker")
        result = validate_actor(actor)
        assert not result["valid"]


class TestValidateNode:
    def test_valid_node(self):
        node = _node()
        assert validate_node(node)["valid"]

    def test_missing_id_fails(self):
        obj = _bare()
        result = validate_node(obj)
        assert not result["valid"]

    def test_initialises_missing_attrs(self):
        obj = SimpleNamespace(id="n1")
        validate_node(obj)
        assert hasattr(obj, "access")
        assert hasattr(obj, "properties")
        assert hasattr(obj, "software")
        assert hasattr(obj, "assets")
