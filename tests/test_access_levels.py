"""Tests for access level enums, ordering, and validation."""

import pytest

from src.core.access_levels import (
    LinkAccessLevel,
    NodeAccessLevel,
    validate_link_access,
    validate_node_access,
)

# ── NodeAccessLevel ordering ───────────────────────────────────────


class TestNodeAccessLevelOrdering:
    def test_strict_ordering(self):
        assert NodeAccessLevel.NONE < NodeAccessLevel.VISIBLE
        assert NodeAccessLevel.VISIBLE < NodeAccessLevel.USER
        assert NodeAccessLevel.USER < NodeAccessLevel.ADMIN

    def test_equality(self):
        assert NodeAccessLevel.ADMIN == NodeAccessLevel.ADMIN
        assert NodeAccessLevel.NONE == NodeAccessLevel.NONE

    def test_ge_operator(self):
        assert NodeAccessLevel.ADMIN >= NodeAccessLevel.USER
        assert NodeAccessLevel.USER >= NodeAccessLevel.USER
        assert not (NodeAccessLevel.VISIBLE >= NodeAccessLevel.USER)

    def test_not_less_than_equal(self):
        assert not (NodeAccessLevel.ADMIN < NodeAccessLevel.VISIBLE)

    def test_cross_type_returns_not_implemented(self):
        assert NodeAccessLevel.ADMIN.__lt__(42) is NotImplemented
        assert NodeAccessLevel.ADMIN.__ge__("ADMIN") is NotImplemented

    def test_transitivity(self):
        levels = [
            NodeAccessLevel.NONE,
            NodeAccessLevel.VISIBLE,
            NodeAccessLevel.USER,
            NodeAccessLevel.ADMIN,
        ]
        for i in range(len(levels)):
            for j in range(i + 1, len(levels)):
                assert levels[i] < levels[j]
                assert levels[j] >= levels[i]


# ── NodeAccessLevel from_string ────────────────────────────────────


class TestNodeAccessLevelFromString:
    @pytest.mark.parametrize(
        "input_str, expected",
        [
            ("NONE", NodeAccessLevel.NONE),
            ("VISIBLE", NodeAccessLevel.VISIBLE),
            ("USER", NodeAccessLevel.USER),
            ("ADMIN", NodeAccessLevel.ADMIN),
            ("admin", NodeAccessLevel.ADMIN),
            ("Admin", NodeAccessLevel.ADMIN),
            ("visible", NodeAccessLevel.VISIBLE),
        ],
    )
    def test_valid_strings(self, input_str, expected):
        assert NodeAccessLevel.from_string(input_str) == expected

    def test_none_input(self):
        assert NodeAccessLevel.from_string(None) == NodeAccessLevel.NONE

    def test_unknown_string_defaults_to_none(self):
        assert NodeAccessLevel.from_string("ROOT") == NodeAccessLevel.NONE
        assert NodeAccessLevel.from_string("") == NodeAccessLevel.NONE

    def test_to_string_roundtrip(self):
        for level in NodeAccessLevel:
            assert NodeAccessLevel.from_string(level.to_string()) == level


# ── LinkAccessLevel ────────────────────────────────────────────────


class TestLinkAccessLevel:
    def test_ordering(self):
        assert LinkAccessLevel.NONE < LinkAccessLevel.VISIBLE
        assert not (LinkAccessLevel.VISIBLE < LinkAccessLevel.NONE)

    def test_from_string(self):
        assert LinkAccessLevel.from_string("NONE") == LinkAccessLevel.NONE
        assert LinkAccessLevel.from_string("VISIBLE") == LinkAccessLevel.VISIBLE
        assert LinkAccessLevel.from_string("visible") == LinkAccessLevel.VISIBLE
        assert LinkAccessLevel.from_string(None) == LinkAccessLevel.NONE

    def test_unknown_string_defaults_to_none(self):
        assert LinkAccessLevel.from_string("ADMIN") == LinkAccessLevel.NONE

    def test_to_string_roundtrip(self):
        for level in LinkAccessLevel:
            assert LinkAccessLevel.from_string(level.to_string()) == level


# ── Validators ─────────────────────────────────────────────────────


class TestValidateNodeAccess:
    def test_passthrough_enum(self):
        assert validate_node_access(NodeAccessLevel.ADMIN) == NodeAccessLevel.ADMIN

    def test_from_string(self):
        assert validate_node_access("ADMIN") == NodeAccessLevel.ADMIN

    def test_none_gives_none(self):
        assert validate_node_access(None) == NodeAccessLevel.NONE

    def test_invalid_type_raises(self):
        with pytest.raises(TypeError, match="Invalid node access type"):
            validate_node_access(42)


class TestValidateLinkAccess:
    def test_passthrough_enum(self):
        assert validate_link_access(LinkAccessLevel.VISIBLE) == LinkAccessLevel.VISIBLE

    def test_from_string(self):
        assert validate_link_access("VISIBLE") == LinkAccessLevel.VISIBLE

    def test_none_gives_none(self):
        assert validate_link_access(None) == LinkAccessLevel.NONE

    def test_invalid_type_raises(self):
        with pytest.raises(TypeError, match="Invalid link access type"):
            validate_link_access(3.14)
