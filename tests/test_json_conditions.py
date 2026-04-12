"""Tests for the JSON condition DSL evaluator and postcondition executor."""

import pytest

from src.actions.json_conditions import ActionExecutor, ConditionEvaluator
from src.core.access_levels import NodeAccessLevel
from src.core.network import Node


@pytest.fixture
def evaluator():
    return ConditionEvaluator()


@pytest.fixture
def executor():
    return ActionExecutor()


@pytest.fixture
def node():
    n = Node(
        id="web",
        software={"os": "Linux", "web_server": "Apache"},
        assets=["customer_data"],
    )
    n.properties = {"exposed_to_internet": True, "critical": True}
    return n


ACCESS_NONE = NodeAccessLevel.NONE
ACCESS_VISIBLE = NodeAccessLevel.VISIBLE
ACCESS_USER = NodeAccessLevel.USER
ACCESS_ADMIN = NodeAccessLevel.ADMIN


# ── access_check ─────────────────────────────────────────────────


class TestAccessCheck:
    def test_equals(self, evaluator, node):
        cond = {"type": "access_check", "operator": "equals", "value": "NONE"}
        assert evaluator.evaluate_condition(cond, node, ACCESS_NONE, "atk") is True
        assert evaluator.evaluate_condition(cond, node, ACCESS_USER, "atk") is False

    def test_not_equals(self, evaluator, node):
        cond = {"type": "access_check", "operator": "not_equals", "value": "NONE"}
        assert evaluator.evaluate_condition(cond, node, ACCESS_USER, "atk") is True

    def test_greater_equal(self, evaluator, node):
        cond = {"type": "access_check", "operator": "greater_equal", "value": "USER"}
        assert evaluator.evaluate_condition(cond, node, ACCESS_ADMIN, "atk") is True
        assert evaluator.evaluate_condition(cond, node, ACCESS_USER, "atk") is True
        assert evaluator.evaluate_condition(cond, node, ACCESS_VISIBLE, "atk") is False

    def test_in(self, evaluator, node):
        cond = {"type": "access_check", "operator": "in", "values": ["NONE", "VISIBLE"]}
        assert evaluator.evaluate_condition(cond, node, ACCESS_VISIBLE, "atk") is True
        assert evaluator.evaluate_condition(cond, node, ACCESS_ADMIN, "atk") is False


# ── software_check ───────────────────────────────────────────────


class TestSoftwareCheck:
    def test_equals(self, evaluator, node):
        cond = {
            "type": "software_check",
            "software_key": "os",
            "operator": "equals",
            "value": "Linux",
        }
        assert evaluator.evaluate_condition(cond, node, ACCESS_NONE, "atk") is True

    def test_not_equals(self, evaluator, node):
        cond = {
            "type": "software_check",
            "software_key": "os",
            "operator": "not_equals",
            "value": "Windows",
        }
        assert evaluator.evaluate_condition(cond, node, ACCESS_NONE, "atk") is True

    def test_exists(self, evaluator, node):
        cond = {"type": "software_check", "software_key": "web_server", "operator": "exists"}
        assert evaluator.evaluate_condition(cond, node, ACCESS_NONE, "atk") is True

    def test_not_exists(self, evaluator, node):
        cond = {"type": "software_check", "software_key": "database", "operator": "not_exists"}
        assert evaluator.evaluate_condition(cond, node, ACCESS_NONE, "atk") is True

    def test_in_list(self, evaluator, node):
        cond = {
            "type": "software_check",
            "software_key": "os",
            "operator": "in",
            "values": ["Linux", "MacOS"],
        }
        assert evaluator.evaluate_condition(cond, node, ACCESS_NONE, "atk") is True

    def test_not_in_list(self, evaluator, node):
        cond = {
            "type": "software_check",
            "software_key": "os",
            "operator": "not_in",
            "values": ["Windows", "FreeBSD"],
        }
        assert evaluator.evaluate_condition(cond, node, ACCESS_NONE, "atk") is True


# ── property_check ───────────────────────────────────────────────


class TestPropertyCheck:
    def test_equals(self, evaluator, node):
        cond = {
            "type": "property_check",
            "property": "exposed_to_internet",
            "operator": "equals",
            "value": True,
        }
        assert evaluator.evaluate_condition(cond, node, ACCESS_NONE, "atk") is True

    def test_not_equals(self, evaluator, node):
        cond = {
            "type": "property_check",
            "property": "critical",
            "operator": "not_equals",
            "value": False,
        }
        assert evaluator.evaluate_condition(cond, node, ACCESS_NONE, "atk") is True

    def test_exists(self, evaluator, node):
        cond = {
            "type": "property_check",
            "property": "critical",
            "operator": "exists",
            "value": None,
        }
        assert evaluator.evaluate_condition(cond, node, ACCESS_NONE, "atk") is True

    def test_not_exists(self, evaluator, node):
        cond = {
            "type": "property_check",
            "property": "nonexistent",
            "operator": "not_exists",
            "value": None,
        }
        assert evaluator.evaluate_condition(cond, node, ACCESS_NONE, "atk") is True


# ── assets_check ─────────────────────────────────────────────────


class TestAssetsCheck:
    def test_count_equals(self, evaluator, node):
        cond = {"type": "assets_check", "check_type": "count", "operator": "equals", "value": 1}
        assert evaluator.evaluate_condition(cond, node, ACCESS_NONE, "atk") is True

    def test_count_greater_than(self, evaluator, node):
        cond = {
            "type": "assets_check",
            "check_type": "count",
            "operator": "greater_than",
            "value": 0,
        }
        assert evaluator.evaluate_condition(cond, node, ACCESS_NONE, "atk") is True


# ── compound ─────────────────────────────────────────────────────


class TestCompound:
    def _access_eq(self, val):
        return {"type": "access_check", "operator": "equals", "value": val}

    def test_and_true(self, evaluator, node):
        cond = {
            "type": "compound",
            "operator": "AND",
            "conditions": [
                self._access_eq("NONE"),
                {
                    "type": "property_check",
                    "property": "critical",
                    "operator": "equals",
                    "value": True,
                },
            ],
        }
        assert evaluator.evaluate_condition(cond, node, ACCESS_NONE, "atk") is True

    def test_and_false(self, evaluator, node):
        cond = {
            "type": "compound",
            "operator": "AND",
            "conditions": [
                self._access_eq("NONE"),
                self._access_eq("USER"),
            ],
        }
        assert evaluator.evaluate_condition(cond, node, ACCESS_NONE, "atk") is False

    def test_or(self, evaluator, node):
        cond = {
            "type": "compound",
            "operator": "OR",
            "conditions": [
                self._access_eq("NONE"),
                self._access_eq("USER"),
            ],
        }
        assert evaluator.evaluate_condition(cond, node, ACCESS_NONE, "atk") is True

    def test_xor_one_true(self, evaluator, node):
        cond = {
            "type": "compound",
            "operator": "XOR",
            "conditions": [
                self._access_eq("NONE"),
                self._access_eq("USER"),
            ],
        }
        assert evaluator.evaluate_condition(cond, node, ACCESS_NONE, "atk") is True

    def test_xor_both_true(self, evaluator, node):
        cond = {
            "type": "compound",
            "operator": "XOR",
            "conditions": [
                self._access_eq("NONE"),
                self._access_eq("NONE"),
            ],
        }
        assert evaluator.evaluate_condition(cond, node, ACCESS_NONE, "atk") is False

    def test_nand(self, evaluator, node):
        cond = {
            "type": "compound",
            "operator": "NAND",
            "conditions": [
                self._access_eq("NONE"),
                self._access_eq("NONE"),
            ],
        }
        assert evaluator.evaluate_condition(cond, node, ACCESS_NONE, "atk") is False

    def test_nor(self, evaluator, node):
        cond = {
            "type": "compound",
            "operator": "NOR",
            "conditions": [
                self._access_eq("USER"),
                self._access_eq("ADMIN"),
            ],
        }
        assert evaluator.evaluate_condition(cond, node, ACCESS_NONE, "atk") is True


# ── negation ─────────────────────────────────────────────────────


class TestNegation:
    def test_negation(self, evaluator, node):
        cond = {
            "type": "negation",
            "condition": {
                "type": "access_check",
                "operator": "equals",
                "value": "USER",
            },
        }
        assert evaluator.evaluate_condition(cond, node, ACCESS_NONE, "atk") is True


# ── implication ──────────────────────────────────────────────────


class TestImplication:
    def test_false_premise(self, evaluator, node):
        # false → anything is true
        cond = {
            "type": "implication",
            "premise": {"type": "access_check", "operator": "equals", "value": "ADMIN"},
            "conclusion": {"type": "access_check", "operator": "equals", "value": "USER"},
        }
        assert evaluator.evaluate_condition(cond, node, ACCESS_NONE, "atk") is True

    def test_true_premise_true_conclusion(self, evaluator, node):
        cond = {
            "type": "implication",
            "premise": {"type": "access_check", "operator": "equals", "value": "NONE"},
            "conclusion": {
                "type": "property_check",
                "property": "critical",
                "operator": "equals",
                "value": True,
            },
        }
        assert evaluator.evaluate_condition(cond, node, ACCESS_NONE, "atk") is True


# ── Unknown type ─────────────────────────────────────────────────


class TestUnknownCondition:
    def test_raises(self, evaluator, node):
        with pytest.raises(ValueError, match="Unknown condition type"):
            evaluator.evaluate_condition({"type": "magic"}, node, ACCESS_NONE, "atk")


# ── ActionExecutor postconditions ────────────────────────────────


class TestSetAccessPostcondition:
    def test_set_access(self, executor, node):
        executor.execute_postcondition(
            {"type": "set_access", "access_value": "USER"},
            node,
            "NONE",
            "atk",
        )
        assert node.access.get("atk") == NodeAccessLevel.USER

    def test_set_access_if_none_when_none(self, executor, node):
        executor.execute_postcondition(
            {"type": "set_access_if_none", "access_value": "VISIBLE"},
            node,
            "NONE",
            "atk",
        )
        assert node.access.get("atk") == NodeAccessLevel.VISIBLE

    def test_set_access_if_none_when_already_set(self, executor, node):
        node.access["atk"] = NodeAccessLevel.ADMIN
        executor.execute_postcondition(
            {"type": "set_access_if_none", "access_value": "VISIBLE"},
            node,
            "NONE",
            "atk",
        )
        assert node.access["atk"] == NodeAccessLevel.ADMIN


class TestPropertyPostcondition:
    def test_set_property(self, executor, node):
        executor.execute_postcondition(
            {"type": "set_property", "property": "patched", "value": True},
            node,
            "NONE",
            "atk",
        )
        assert node.properties["patched"] is True

    def test_increment_counter(self, executor, node):
        node.login_attempts = 3
        executor.execute_postcondition(
            {"type": "increment_counter", "counter": "login_attempts", "increment": 2},
            node,
            "NONE",
            "atk",
        )
        assert node.login_attempts == 5


class TestClearAssetsPostcondition:
    def test_clear_assets(self, executor, node):
        executor.execute_postcondition(
            {"type": "clear_assets"},
            node,
            "NONE",
            "atk",
        )
        assert node.assets == []


class TestCompoundPostcondition:
    def test_executes_all(self, executor, node):
        executor.execute_postcondition(
            {
                "type": "compound",
                "actions": [
                    {"type": "set_access", "access_value": "USER"},
                    {"type": "set_property", "property": "flag", "value": True},
                ],
            },
            node,
            "NONE",
            "atk",
        )
        assert node.access.get("atk") == NodeAccessLevel.USER
        assert node.properties["flag"] is True


class TestUnknownPostcondition:
    def test_raises(self, executor, node):
        with pytest.raises(ValueError, match="Unknown postcondition type"):
            executor.execute_postcondition(
                {"type": "do_magic"},
                node,
                "NONE",
                "atk",
            )
