"""Tests for src.core.exceptions."""

from src.core.exceptions import (
    ActionConfigError,
    ActionError,
    ActorValidationError,
    BudgetError,
    CapacityError,
    ConfigurationError,
    DetectionError,
    NetworkConfigError,
    NodeValidationError,
    PreconditionError,
    SimTIMError,
    SimulationError,
    ValidationError,
)


class TestExceptionHierarchy:
    def test_simtim_inherits_exception(self):
        assert issubclass(SimTIMError, Exception)

    def test_config_inherits_simtim(self):
        assert issubclass(ConfigurationError, SimTIMError)

    def test_network_config_inherits_config(self):
        assert issubclass(NetworkConfigError, ConfigurationError)

    def test_action_config_inherits_config(self):
        assert issubclass(ActionConfigError, ConfigurationError)

    def test_simulation_inherits_simtim(self):
        assert issubclass(SimulationError, SimTIMError)

    def test_validation_inherits_simtim(self):
        assert issubclass(ValidationError, SimTIMError)

    def test_detection_inherits_simulation(self):
        assert issubclass(DetectionError, SimulationError)


class TestActionError:
    def test_str(self):
        e = ActionError(action_name="exploit", reason="failed", target="web", actor="att1")
        s = str(e)
        assert "exploit" in s
        assert "failed" in s
        assert "web" in s
        assert "att1" in s

    def test_str_no_target_actor(self):
        e = ActionError(action_name="scan", reason="timeout")
        s = str(e)
        assert "scan" in s
        assert "timeout" in s

    def test_to_dict(self):
        e = ActionError(action_name="exploit", reason="failed", target="web", actor="att1")
        d = e.to_dict()
        assert d["action_name"] == "exploit"
        assert d["reason"] == "failed"
        assert d["target"] == "web"
        assert d["actor"] == "att1"
        assert d["details"] == {}


class TestPreconditionError:
    def test_str_with_condition(self):
        e = PreconditionError(
            action_name="exploit",
            reason="access denied",
            condition_type="access_check",
        )
        s = str(e)
        assert "access_check" in s
        assert "exploit" in s

    def test_str_without_condition(self):
        e = PreconditionError(action_name="scan", reason="no target")
        s = str(e)
        assert "scan" in s
        assert "condition" not in s

    def test_inherits_action_error(self):
        assert issubclass(PreconditionError, ActionError)


class TestCapacityError:
    def test_str(self):
        e = CapacityError(actor_id="att1", current_capacity=3, max_capacity=2)
        s = str(e)
        assert "att1" in s
        assert "3" in s
        assert "2" in s

    def test_to_dict(self):
        e = CapacityError(actor_id="att1", current_capacity=3, max_capacity=2)
        d = e.to_dict()
        assert d["actor_id"] == "att1"
        assert d["current_capacity"] == 3
        assert d["max_capacity"] == 2


class TestBudgetError:
    def test_str(self):
        e = BudgetError(actor_id="att1", incurred_cost=150.0, budget=100.0)
        s = str(e)
        assert "att1" in s
        assert "150" in s
        assert "100" in s

    def test_to_dict(self):
        e = BudgetError(actor_id="att1", incurred_cost=150.0, budget=100.0)
        d = e.to_dict()
        assert d["actor_id"] == "att1"
        assert d["incurred_cost"] == 150.0
        assert d["budget"] == 100.0


class TestActorValidationError:
    def test_str(self):
        e = ActorValidationError(actor_id="att1", errors=["bad id", "bad role"])
        s = str(e)
        assert "att1" in s
        assert "bad id" in s


class TestNodeValidationError:
    def test_str(self):
        e = NodeValidationError(node_id="web", errors=["missing software"])
        s = str(e)
        assert "web" in s
        assert "missing software" in s
