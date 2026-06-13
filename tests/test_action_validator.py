"""Tests for action JSON schema validation."""

import pytest

from src.actions.action_validator import ActionValidator, ValidationResult


@pytest.fixture
def validator():
    return ActionValidator()


def _valid_action_data(**overrides):
    """Return a minimal valid action dict, with optional overrides."""
    base = {
        "name": "test_action",
        "action_type": "node",
        "cost": 10,
        "duration": 1,
        "success_probability": 0.5,
        "precondition": {"type": "constant"},
        "postcondition": {"type": "set_access"},
        "detection_probability": {"type": "constant"},
        "damage_gain": {
            "one_off_damage": 0,
            "one_off_gain": 100,
            "time_damage": 0,
            "time_gain": 0,
        },
    }
    base.update(overrides)
    return base


# ── Required fields ───────────────────────────────────────────────


class TestRequiredFields:
    def test_all_present(self, validator):
        assert validator.validate(_valid_action_data()).valid

    @pytest.mark.parametrize("missing", ActionValidator.REQUIRED_FIELDS)
    def test_missing_field(self, validator, missing):
        data = _valid_action_data()
        del data[missing]
        result = validator.validate(data)
        assert not result.valid
        assert any(missing in e for e in result.errors)


# ── Name validation ──────────────────────────────────────────────


class TestNameValidation:
    def test_valid_name(self, validator):
        assert validator.validate(_valid_action_data(name="recon")).valid

    def test_name_not_string(self, validator):
        result = validator.validate(_valid_action_data(name=42))
        assert not result.valid

    def test_empty_name(self, validator):
        result = validator.validate(_valid_action_data(name="   "))
        assert not result.valid


# ── Action type validation ───────────────────────────────────────


class TestActionTypeValidation:
    @pytest.mark.parametrize("atype", ["node", "link"])
    def test_valid_types(self, validator, atype):
        assert validator.validate(_valid_action_data(action_type=atype)).valid

    def test_invalid_type(self, validator):
        result = validator.validate(_valid_action_data(action_type="global"))
        assert not result.valid


# ── Cost validation ──────────────────────────────────────────────


class TestCostValidation:
    def test_zero_cost(self, validator):
        assert validator.validate(_valid_action_data(cost=0)).valid

    def test_negative_cost(self, validator):
        assert not validator.validate(_valid_action_data(cost=-1)).valid

    def test_float_cost(self, validator):
        assert validator.validate(_valid_action_data(cost=5.5)).valid

    def test_string_cost(self, validator):
        assert not validator.validate(_valid_action_data(cost="ten")).valid


# ── Duration validation ─────────────────────────────────────────


class TestDurationValidation:
    def test_positive_duration(self, validator):
        assert validator.validate(_valid_action_data(duration=0.5)).valid

    def test_zero_duration(self, validator):
        assert not validator.validate(_valid_action_data(duration=0)).valid

    def test_negative_duration(self, validator):
        assert not validator.validate(_valid_action_data(duration=-1)).valid

    def test_string_duration(self, validator):
        assert not validator.validate(_valid_action_data(duration="fast")).valid


# ── Success probability validation ───────────────────────────────


class TestSuccessProbabilityValidation:
    @pytest.mark.parametrize("p", [0, 0.5, 1])
    def test_valid_range(self, validator, p):
        assert validator.validate(_valid_action_data(success_probability=p)).valid

    def test_over_one(self, validator):
        assert not validator.validate(_valid_action_data(success_probability=1.1)).valid

    def test_below_zero(self, validator):
        assert not validator.validate(_valid_action_data(success_probability=-0.1)).valid

    def test_not_number(self, validator):
        assert not validator.validate(_valid_action_data(success_probability="high")).valid


# ── Damage/gain validation ───────────────────────────────────────


class TestDamageGainValidation:
    def test_valid_damage_gain(self, validator):
        assert validator.validate(_valid_action_data()).valid

    def test_not_a_dict(self, validator):
        assert not validator.validate(_valid_action_data(damage_gain="none")).valid

    @pytest.mark.parametrize("field", ActionValidator.DAMAGE_GAIN_FIELDS)
    def test_missing_subfield(self, validator, field):
        dg = {
            "one_off_damage": 0,
            "one_off_gain": 0,
            "time_damage": 0,
            "time_gain": 0,
        }
        del dg[field]
        result = validator.validate(_valid_action_data(damage_gain=dg))
        assert not result.valid

    def test_non_numeric_subfield(self, validator):
        dg = {
            "one_off_damage": "big",
            "one_off_gain": 0,
            "time_damage": 0,
            "time_gain": 0,
        }
        result = validator.validate(_valid_action_data(damage_gain=dg))
        assert not result.valid


# ── Precondition validation ──────────────────────────────────────


class TestPreconditionValidation:
    def test_valid_precondition(self, validator):
        pre = {"type": "access_check"}
        assert validator.validate(_valid_action_data(precondition=pre)).valid

    def test_not_a_dict(self, validator):
        assert not validator.validate(_valid_action_data(precondition="true")).valid

    def test_missing_type(self, validator):
        assert not validator.validate(_valid_action_data(precondition={})).valid

    def test_unknown_type_warns(self, validator):
        pre = {"type": "future_type_xxx"}
        result = validator.validate(_valid_action_data(precondition=pre))
        assert result.valid  # warning, not error
        assert len(result.warnings) > 0


# ── Postcondition validation ─────────────────────────────────────


class TestPostconditionValidation:
    def test_valid_postcondition(self, validator):
        post = {"type": "set_access"}
        assert validator.validate(_valid_action_data(postcondition=post)).valid

    def test_not_a_dict(self, validator):
        assert not validator.validate(_valid_action_data(postcondition="set")).valid

    def test_missing_type(self, validator):
        assert not validator.validate(_valid_action_data(postcondition={})).valid


# ── Detection probability validation ─────────────────────────────


class TestDetectionProbabilityValidation:
    def test_valid(self, validator):
        det = {"type": "constant"}
        assert validator.validate(_valid_action_data(detection_probability=det)).valid

    def test_not_a_dict(self, validator):
        assert not validator.validate(_valid_action_data(detection_probability=0.5)).valid

    def test_missing_type(self, validator):
        assert not validator.validate(_valid_action_data(detection_probability={})).valid


# ── ValidationResult ─────────────────────────────────────────────


class TestValidationResult:
    def test_bool_true(self):
        assert bool(ValidationResult(valid=True)) is True

    def test_bool_false(self):
        assert bool(ValidationResult(valid=False)) is False

    def test_merge_collects_all(self):
        a = ValidationResult(valid=True, warnings=["w1"])
        b = ValidationResult(valid=False, errors=["e1"])
        m = a.merge(b)
        assert not m.valid
        assert "e1" in m.errors
        assert "w1" in m.warnings
