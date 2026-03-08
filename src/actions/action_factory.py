import logging
from collections.abc import Callable
from typing import Any

from src.actions.action import Action
from src.actions.action_validator import ActionValidator
from src.actions.json_conditions import action_executor, condition_evaluator

logger = logging.getLogger(__name__)


class FunctionSpecError(ValueError):
    pass


class ActionCreationError(ValueError):
    def __init__(self, action_name: str, message: str, cause: Exception | None = None):
        self.action_name = action_name
        self.cause = cause
        super().__init__(f"Failed to create action '{action_name}': {message}")


class ActionFactory:
    def __init__(self, validator: ActionValidator | None = None):
        self._validator = validator or ActionValidator()

    @property
    def validator(self) -> ActionValidator:
        return self._validator

    def create(self, action_data: dict[str, Any], validate: bool = True) -> Action:
        action_name = action_data.get("name", "unknown")

        if validate:
            result = self._validator.validate(action_data)
            if not result.valid:
                error_msg = "\n".join(f"  - {err}" for err in result.errors)
                raise ActionCreationError(action_name, f"Validation failed:\n{error_msg}")

            for warning in result.warnings:
                logger.warning(f"Action '{action_name}': {warning}")

        try:
            precondition = self._create_precondition(action_data["precondition"])
            postcondition = self._create_postcondition(action_data["postcondition"])
            detection_probability = self._create_detection_function(
                action_data["detection_probability"]
            )
            damage_functions = self._create_damage_functions(action_data["damage_gain"])

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

            action._json_data = action_data

            logger.debug(f"Created action: {action.name}")
            return action

        except FunctionSpecError as e:
            raise ActionCreationError(action_name, str(e), e) from e
        except Exception as e:
            raise ActionCreationError(action_name, str(e), e) from e

    def _create_precondition(self, spec: dict[str, Any]) -> Callable:
        return self._create_condition_function(spec)

    def _create_postcondition(self, spec: dict[str, Any]) -> Callable:
        spec_type = spec.get("type")

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

        return self._create_condition_function(spec)

    def _create_detection_function(self, spec: dict[str, Any]) -> Callable:
        spec_type = spec.get("type")

        if spec_type == "node_property_based":
            return self._create_property_based_detection(spec)

        return self._create_condition_function(spec)

    def _create_condition_function(self, spec: dict[str, Any]) -> Callable:
        spec_type = spec.get("type")

        if spec_type == "constant":
            value = spec.get("value", 0.0)
            return lambda node, access, actor: value

        if spec_type == "zero":
            return lambda node, access, actor: 0.0

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

                    if "nested_property" in modifier and isinstance(prop_value, dict):
                        prop_value = prop_value.get(modifier["nested_property"])

                if prop_value is None:
                    continue

                if "value" in modifier:
                    if prop_value == modifier["value"]:
                        modifier_sum += modifier.get("probability_modifier", 0.0)
                elif "values" in modifier:
                    if prop_value in modifier["values"]:
                        modifier_sum += modifier.get("probability_modifier", 0.0)

            return min(1.0, max(0.0, base_prob + modifier_sum))

        return detection_function

    def _create_damage_functions(self, damage_gain: dict[str, Any]) -> dict[str, Callable]:
        one_off_damage_val = damage_gain.get("one_off_damage", 0.0)
        one_off_gain_val = damage_gain.get("one_off_gain", 0.0)
        time_damage_val = damage_gain.get("time_damage", 0.0)
        time_gain_val = damage_gain.get("time_gain", 0.0)

        return {
            "one_off_damage": lambda node, access, actor, v=one_off_damage_val: v,
            "one_off_gain": lambda node, access, actor, v=one_off_gain_val: v,
            "time_damage": lambda node, access, actor, v=time_damage_val: v,
            "time_gain": lambda node, access, actor, v=time_gain_val: v,
        }

    def to_json(self, action: Action) -> dict[str, Any]:
        if hasattr(action, "_json_data") and action._json_data:
            return action._json_data.copy()

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
        try:
            result = func(None, None, None)
            if isinstance(result, int | float):
                return {"type": "constant", "value": result}
        except (TypeError, AttributeError, ValueError):
            pass

        return {"type": "constant", "value": 0.0}

    def _safe_call(self, func: Callable, default: float = 0.0) -> float:
        try:
            result = func(None, None, None)
            return float(result) if result is not None else default
        except (TypeError, AttributeError, ValueError):
            return default
