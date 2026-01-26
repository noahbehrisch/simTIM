"""
Action factory module.

Creates Action objects from JSON specifications by converting
condition specs into callable functions.
"""

import logging
from collections.abc import Callable
from typing import Any

from src.actions.action import Action
from src.actions.action_validator import ActionValidator
from src.actions.json_conditions import action_executor, condition_evaluator

logger = logging.getLogger(__name__)


class FunctionSpecError(ValueError):
    """Raised when a function specification is invalid."""

    pass


class ActionCreationError(ValueError):
    """Raised when action creation fails."""

    def __init__(self, action_name: str, message: str, cause: Exception | None = None):
        self.action_name = action_name
        self.cause = cause
        super().__init__(f"Failed to create action '{action_name}': {message}")


class ActionFactory:
    """
    Creates Action objects from JSON specifications.

    Responsible for:
    - Converting JSON specs to callable functions (preconditions, postconditions)
    - Building Action instances
    - Serializing Actions back to JSON

    Does NOT handle:
    - File I/O (see ActionLoader)
    - Storage/retrieval (see ActionRegistry)
    - Validation (see ActionValidator)
    """

    def __init__(self, validator: ActionValidator | None = None):
        """
        Initialize the factory.

        Args:
            validator: Optional validator instance. If None, creates a new one.
        """
        self._validator = validator or ActionValidator()

    @property
    def validator(self) -> ActionValidator:
        """Get the validator instance."""
        return self._validator

    def create(self, action_data: dict[str, Any], validate: bool = True) -> Action:
        """
        Create an Action from JSON data.

        Args:
            action_data: Dictionary containing action configuration
            validate: Whether to validate before creation (default True)

        Returns:
            Configured Action instance

        Raises:
            ActionCreationError: If validation fails or creation encounters an error
        """
        action_name = action_data.get("name", "unknown")

        # Validate if requested
        if validate:
            result = self._validator.validate(action_data)
            if not result.valid:
                error_msg = "\n".join(f"  - {err}" for err in result.errors)
                raise ActionCreationError(action_name, f"Validation failed:\n{error_msg}")

            # Log warnings
            for warning in result.warnings:
                logger.warning(f"Action '{action_name}': {warning}")

        try:
            # Create callable functions from specs
            precondition = self._create_precondition(action_data["precondition"])
            postcondition = self._create_postcondition(action_data["postcondition"])
            detection_probability = self._create_detection_function(
                action_data["detection_probability"]
            )
            damage_functions = self._create_damage_functions(action_data["damage_gain"])

            # Build the Action
            action = Action(
                name=action_data["name"],
                precondition=precondition,
                postcondition=postcondition,
                cost=action_data["cost"],
                duration=action_data["duration"],
                success_probability=action_data["success_probability"],
                action_type=action_data["action_type"],
                detection_probability=detection_probability,
                one_off_damage=damage_functions["one_off_damage"],
                one_off_gain=damage_functions["one_off_gain"],
                time_damage=damage_functions["time_damage"],
                time_gain=damage_functions["time_gain"],
            )

            # Attach original JSON data for introspection
            action._json_data = action_data

            logger.debug(f"Created action: {action.name}")
            return action

        except FunctionSpecError as e:
            raise ActionCreationError(action_name, str(e), e) from e
        except Exception as e:
            raise ActionCreationError(action_name, str(e), e) from e

    def _create_precondition(self, spec: dict[str, Any]) -> Callable:
        """Create a precondition function from a spec."""
        return self._create_condition_function(spec)

    def _create_postcondition(self, spec: dict[str, Any]) -> Callable:
        """Create a postcondition function from a spec."""
        spec_type = spec.get("type")

        # Postcondition-specific types that modify state
        postcondition_types = [
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
        ]

        if spec_type in postcondition_types:
            return lambda node, access, actor: action_executor.execute_postcondition(
                spec, node, access, actor
            )

        # Fall back to condition function for other types
        return self._create_condition_function(spec)

    def _create_detection_function(self, spec: dict[str, Any]) -> Callable:
        """Create a detection probability function from a spec."""
        spec_type = spec.get("type")

        if spec_type == "node_property_based":
            return self._create_property_based_detection(spec)

        return self._create_condition_function(spec)

    def _create_condition_function(self, spec: dict[str, Any]) -> Callable:
        """
        Create a condition evaluation function from a spec.

        Handles: json_condition, compound, access_check, software_check,
                 version_check, property_check, vulnerability_check,
                 assets_check, constant, zero
        """
        spec_type = spec.get("type")

        if spec_type == "constant":
            value = spec.get("value", 0.0)
            return lambda node, access, actor: value

        if spec_type == "zero":
            return lambda node, access, actor: 0.0

        # All other types use the condition evaluator
        condition_types = [
            "json_condition",
            "compound",
            "access_check",
            "software_check",
            "version_check",
            "property_check",
            "vulnerability_check",
            "assets_check",
        ]

        if spec_type in condition_types:
            return lambda node, access, actor: condition_evaluator.evaluate_condition(
                spec, node, access, actor
            )

        raise FunctionSpecError(f"Unknown function spec type: {spec_type}")

    def _create_property_based_detection(self, spec: dict[str, Any]) -> Callable:
        """Create a node-property-based detection function."""
        base_prob = spec.get("base_probability", 0.0)
        modifiers = spec.get("property_modifiers", [])

        def detection_function(node, access, actor) -> float:
            modifier_sum = 0.0

            for modifier in modifiers:
                prop_name = modifier.get("property")
                if not prop_name:
                    continue

                prop_value = None
                if hasattr(node, prop_name):
                    prop_value = getattr(node, prop_name)

                    # Handle nested properties
                    if "nested_property" in modifier and isinstance(prop_value, dict):
                        prop_value = prop_value.get(modifier["nested_property"])

                if prop_value is None:
                    continue

                # Check for value match
                if "value" in modifier:
                    if prop_value == modifier["value"]:
                        modifier_sum += modifier.get("probability_modifier", 0.0)
                elif "values" in modifier:
                    if prop_value in modifier["values"]:
                        modifier_sum += modifier.get("probability_modifier", 0.0)

            return min(1.0, max(0.0, base_prob + modifier_sum))

        return detection_function

    def _create_damage_functions(self, damage_gain: dict[str, Any]) -> dict[str, Callable]:
        """Create damage/gain functions from damage_gain spec."""
        # Extract values to avoid closure issues
        one_off_damage_val = damage_gain.get("one_off_damage", 0.0)
        one_off_gain_val = damage_gain.get("one_off_gain", 0.0)
        time_damage_val = damage_gain.get("time_damage", 0.0)
        time_gain_val = damage_gain.get("time_gain", 0.0)

        # Use default args to capture values by value, not reference
        return {
            "one_off_damage": lambda node, access, actor, v=one_off_damage_val: v,
            "one_off_gain": lambda node, access, actor, v=one_off_gain_val: v,
            "time_damage": lambda node, access, actor, v=time_damage_val: v,
            "time_gain": lambda node, access, actor, v=time_gain_val: v,
        }

    def to_json(self, action: Action) -> dict[str, Any]:
        """
        Convert an Action back to JSON format.

        Args:
            action: Action instance to serialize

        Returns:
            Dictionary representation of the action
        """
        # If we have the original JSON data, use it
        if hasattr(action, "_json_data") and action._json_data:
            return action._json_data.copy()

        # Otherwise, reconstruct from action properties
        action_data = {
            "name": action.name,
            "action_type": action.action_type,
            "cost": action.cost,
            "duration": action.duration,
            "success_probability": action.success_probability,
            "precondition": self._function_to_spec(action.precondition),
            "postcondition": self._function_to_spec(action.postcondition),
            "detection_probability": self._function_to_spec(action.detection_probability),
            "damage_gain": {
                "one_off_damage": self._safe_call(action.one_off_damage),
                "one_off_gain": self._safe_call(action.one_off_gain),
                "time_damage": self._safe_call(action.time_damage),
                "time_gain": self._safe_call(action.time_gain),
            },
        }

        return action_data

    def _function_to_spec(self, func: Callable) -> dict[str, Any]:
        """Convert a function back to a spec (best effort)."""
        # Try to get a constant value
        try:
            result = func(None, None, None)
            if isinstance(result, (int, float)):
                return {"type": "constant", "value": result}
        except (TypeError, AttributeError, ValueError):
            pass

        # Default to a placeholder
        return {"type": "constant", "value": 0.0}

    def _safe_call(self, func: Callable, default: float = 0.0) -> float:
        """Safely call a damage/gain function to extract its value."""
        try:
            result = func(None, None, None)
            return float(result) if result is not None else default
        except (TypeError, AttributeError, ValueError):
            return default
