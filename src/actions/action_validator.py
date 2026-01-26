"""
Action validation module.

Provides validation for action JSON configurations with detailed error reporting.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ValidationResult:
    """Result of a validation operation."""

    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def __bool__(self) -> bool:
        return self.valid

    def merge(self, other: "ValidationResult") -> "ValidationResult":
        """Merge another validation result into this one."""
        return ValidationResult(
            valid=self.valid and other.valid,
            errors=self.errors + other.errors,
            warnings=self.warnings + other.warnings,
        )


class ActionValidator:
    """
    Validates action JSON configurations.

    Separates validation logic from action creation, allowing for:
    - Reusable validation rules
    - Custom validation extensions
    - Clear error reporting
    """

    REQUIRED_FIELDS = [
        "name",
        "action_type",
        "cost",
        "duration",
        "success_probability",
        "precondition",
        "postcondition",
        "detection_probability",
        "damage_gain",
    ]

    DAMAGE_GAIN_FIELDS = [
        "one_off_damage",
        "one_off_gain",
        "time_damage",
        "time_gain",
    ]

    VALID_ACTION_TYPES = ["node", "link"]

    VALID_CONDITION_TYPES = [
        "json_condition",
        "compound",
        "access_check",
        "software_check",
        "version_check",
        "property_check",
        "vulnerability_check",
        "assets_check",
        "constant",
        "zero",
        "node_property_based",
    ]

    VALID_POSTCONDITION_TYPES = [
        "compound",
        "set_access",
        "set_access_if_none",
        "set_property",
        "set_software",
        "add_vulnerability",
        "remove_vulnerability",
        "increment_counter",
        "set_links_access",
        "set_access_neighbors",
        "clear_assets",
    ] + VALID_CONDITION_TYPES

    def validate(self, action_data: dict[str, Any]) -> ValidationResult:
        """
        Validate an action configuration.

        Args:
            action_data: Dictionary containing action configuration

        Returns:
            ValidationResult with errors and warnings
        """
        result = ValidationResult(valid=True)

        # Check required fields
        result = result.merge(self._validate_required_fields(action_data))

        # Validate individual fields
        result = result.merge(self._validate_name(action_data))
        result = result.merge(self._validate_action_type(action_data))
        result = result.merge(self._validate_cost(action_data))
        result = result.merge(self._validate_duration(action_data))
        result = result.merge(self._validate_success_probability(action_data))
        result = result.merge(self._validate_damage_gain(action_data))
        result = result.merge(self._validate_precondition(action_data))
        result = result.merge(self._validate_postcondition(action_data))
        result = result.merge(self._validate_detection_probability(action_data))

        return result

    def _validate_required_fields(self, action_data: dict[str, Any]) -> ValidationResult:
        """Check that all required fields are present."""
        errors = []
        for field_name in self.REQUIRED_FIELDS:
            if field_name not in action_data:
                errors.append(f"Missing required field: {field_name}")
        return ValidationResult(valid=len(errors) == 0, errors=errors)

    def _validate_name(self, action_data: dict[str, Any]) -> ValidationResult:
        """Validate the name field."""
        if "name" not in action_data:
            return ValidationResult(valid=True)  # Already caught by required fields

        if not isinstance(action_data["name"], str):
            return ValidationResult(valid=False, errors=["'name' must be a string"])

        if not action_data["name"].strip():
            return ValidationResult(valid=False, errors=["'name' must not be empty"])

        return ValidationResult(valid=True)

    def _validate_action_type(self, action_data: dict[str, Any]) -> ValidationResult:
        """Validate the action_type field."""
        if "action_type" not in action_data:
            return ValidationResult(valid=True)

        if action_data["action_type"] not in self.VALID_ACTION_TYPES:
            return ValidationResult(
                valid=False,
                errors=[f"'action_type' must be one of: {self.VALID_ACTION_TYPES}"],
            )

        return ValidationResult(valid=True)

    def _validate_cost(self, action_data: dict[str, Any]) -> ValidationResult:
        """Validate the cost field."""
        if "cost" not in action_data:
            return ValidationResult(valid=True)

        cost = action_data["cost"]
        if not isinstance(cost, (int, float)):
            return ValidationResult(valid=False, errors=["'cost' must be a number"])

        if cost < 0:
            return ValidationResult(valid=False, errors=["'cost' must be non-negative"])

        return ValidationResult(valid=True)

    def _validate_duration(self, action_data: dict[str, Any]) -> ValidationResult:
        """Validate the duration field."""
        if "duration" not in action_data:
            return ValidationResult(valid=True)

        duration = action_data["duration"]
        if not isinstance(duration, (int, float)):
            return ValidationResult(valid=False, errors=["'duration' must be a number"])

        if duration <= 0:
            return ValidationResult(valid=False, errors=["'duration' must be positive"])

        return ValidationResult(valid=True)

    def _validate_success_probability(self, action_data: dict[str, Any]) -> ValidationResult:
        """Validate the success_probability field."""
        if "success_probability" not in action_data:
            return ValidationResult(valid=True)

        prob = action_data["success_probability"]
        if not isinstance(prob, (int, float)):
            return ValidationResult(valid=False, errors=["'success_probability' must be a number"])

        if not 0 <= prob <= 1:
            return ValidationResult(
                valid=False, errors=["'success_probability' must be between 0 and 1"]
            )

        return ValidationResult(valid=True)

    def _validate_damage_gain(self, action_data: dict[str, Any]) -> ValidationResult:
        """Validate the damage_gain field."""
        if "damage_gain" not in action_data:
            return ValidationResult(valid=True)

        dg = action_data["damage_gain"]
        if not isinstance(dg, dict):
            return ValidationResult(valid=False, errors=["'damage_gain' must be a dictionary"])

        errors = []
        for field_name in self.DAMAGE_GAIN_FIELDS:
            if field_name not in dg:
                errors.append(f"'damage_gain' missing required field: {field_name}")
            elif not isinstance(dg[field_name], (int, float)):
                errors.append(f"'damage_gain.{field_name}' must be a number")

        return ValidationResult(valid=len(errors) == 0, errors=errors)

    def _validate_precondition(self, action_data: dict[str, Any]) -> ValidationResult:
        """Validate the precondition field."""
        if "precondition" not in action_data:
            return ValidationResult(valid=True)

        precondition = action_data["precondition"]
        if not isinstance(precondition, dict):
            return ValidationResult(valid=False, errors=["'precondition' must be a dictionary"])

        return self._validate_condition_spec(precondition, "precondition")

    def _validate_postcondition(self, action_data: dict[str, Any]) -> ValidationResult:
        """Validate the postcondition field."""
        if "postcondition" not in action_data:
            return ValidationResult(valid=True)

        postcondition = action_data["postcondition"]
        if not isinstance(postcondition, dict):
            return ValidationResult(valid=False, errors=["'postcondition' must be a dictionary"])

        return self._validate_postcondition_spec(postcondition)

    def _validate_detection_probability(self, action_data: dict[str, Any]) -> ValidationResult:
        """Validate the detection_probability field."""
        if "detection_probability" not in action_data:
            return ValidationResult(valid=True)

        detection = action_data["detection_probability"]
        if not isinstance(detection, dict):
            return ValidationResult(
                valid=False, errors=["'detection_probability' must be a dictionary"]
            )

        return self._validate_condition_spec(detection, "detection_probability")

    def _validate_condition_spec(self, spec: dict[str, Any], field_name: str) -> ValidationResult:
        """Validate a condition specification."""
        warnings = []

        if "type" not in spec:
            return ValidationResult(
                valid=False, errors=[f"'{field_name}' must have a 'type' field"]
            )

        spec_type = spec["type"]

        if spec_type not in self.VALID_CONDITION_TYPES:
            warnings.append(
                f"'{field_name}': Unknown condition type '{spec_type}'. "
                f"Valid types: {self.VALID_CONDITION_TYPES}"
            )

        return ValidationResult(valid=True, warnings=warnings)

    def _validate_postcondition_spec(self, spec: dict[str, Any]) -> ValidationResult:
        """Validate a postcondition specification."""
        if "type" not in spec:
            return ValidationResult(
                valid=False, errors=["'postcondition' must have a 'type' field"]
            )

        return ValidationResult(valid=True)
