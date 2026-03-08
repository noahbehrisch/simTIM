import logging
from dataclasses import dataclass, field
from typing import Any

from src.actors.actor import Actor
from src.actors.attacker import Attacker
from src.actors.defender import Defender

logger = logging.getLogger(__name__)


class ActorCreationError(Exception):
    pass


@dataclass
class ActorValidationResult:
    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class ActorValidator:
    VALID_ROLES = {"attacker", "defender"}
    REQUIRED_FIELDS = {"id", "role"}

    def validate(self, config: dict[str, Any]) -> ActorValidationResult:
        errors: list[str] = []
        warnings: list[str] = []

        if not isinstance(config, dict):
            return ActorValidationResult(
                valid=False,
                errors=["Actor configuration must be a dictionary"],
            )

        for field_name in self.REQUIRED_FIELDS:
            if field_name not in config:
                errors.append(f"Missing required field: {field_name}")

        actor_id = config.get("id")
        if actor_id is not None:
            if not isinstance(actor_id, str) or not actor_id.strip():
                errors.append("'id' must be a non-empty string")

        role = config.get("role")
        if role is not None:
            if not isinstance(role, str):
                errors.append("'role' must be a string")
            elif role.lower() not in self.VALID_ROLES:
                errors.append(f"Invalid role '{role}'. Must be one of: {self.VALID_ROLES}")

        self._validate_capacity(config, errors, warnings)
        self._validate_budget(config, errors, warnings)
        self._validate_strategy(config, errors, warnings)

        return ActorValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    def _validate_capacity(
        self,
        config: dict[str, Any],
        errors: list[str],
        warnings: list[str],
    ) -> None:
        capacity = config.get("capacity")
        if capacity is not None:
            if capacity != float("inf"):
                if not isinstance(capacity, int | float):
                    errors.append("'capacity' must be a number or infinity")
                elif capacity < 1:
                    warnings.append("'capacity' less than 1 may prevent actions")

    def _validate_budget(
        self,
        config: dict[str, Any],
        errors: list[str],
        warnings: list[str],
    ) -> None:
        budget = config.get("budget")
        if budget is not None:
            if budget != float("inf"):
                if not isinstance(budget, int | float):
                    errors.append("'budget' must be a number or infinity")
                elif budget <= 0:
                    warnings.append("'budget' <= 0 will prevent actions")

    def _validate_strategy(
        self,
        config: dict[str, Any],
        errors: list[str],
        warnings: list[str],
    ) -> None:
        strategy = config.get("strategy")
        if strategy is not None and not isinstance(strategy, str):
            errors.append("'strategy' must be a string")


class ActorFactory:
    def __init__(self, validator: ActorValidator | None = None):
        self._validator = validator or ActorValidator()

    @property
    def validator(self) -> ActorValidator:
        return self._validator

    def create(
        self,
        config: dict[str, Any],
        validate: bool = True,
    ) -> Actor:
        if validate:
            result = self._validator.validate(config)
            if not result.valid:
                error_msg = "Actor configuration validation failed:\n"
                error_msg += "\n".join(f"  - {err}" for err in result.errors)
                raise ActorCreationError(error_msg)

            for warning in result.warnings:
                logger.warning(f"Actor config: {warning}")

        try:
            role = config["role"].lower()

            if role == "attacker":
                return self._create_attacker(config)
            elif role == "defender":
                return self._create_defender(config)
            else:
                raise ActorCreationError(f"Unknown actor role: {role}")

        except ActorCreationError:
            raise
        except Exception as e:
            raise ActorCreationError(f"Error creating actor: {e}") from e

    def _create_attacker(self, config: dict[str, Any]) -> Attacker:
        attacker = Attacker(
            id=config["id"],
            strategy=config.get("strategy", "greedy"),
            capacity=config.get("capacity", float("inf")),
            budget=config.get("budget", float("inf")),
        )

        if "decision_interval" in config:
            attacker.decision_interval = config["decision_interval"]

        logger.debug(f"Created attacker: {attacker.id}")
        return attacker

    def _create_defender(self, config: dict[str, Any]) -> Defender:
        defender = Defender(
            id=config["id"],
            strategy=config.get("strategy", "reactive"),
            capacity=config.get("capacity", float("inf")),
            budget=config.get("budget", float("inf")),
        )

        if "decision_interval" in config:
            defender.decision_interval = config["decision_interval"]

        logger.debug(f"Created defender: {defender.id}")
        return defender

    def create_attacker(
        self,
        id: str,
        strategy: str = "greedy",
        capacity: float = float("inf"),
        budget: float = float("inf"),
        **kwargs: Any,
    ) -> Attacker:
        config = {
            "id": id,
            "role": "attacker",
            "strategy": strategy,
            "capacity": capacity,
            "budget": budget,
            **kwargs,
        }
        return self.create(config)  # type: ignore[return-value]

    def create_defender(
        self,
        id: str,
        strategy: str = "reactive",
        capacity: float = float("inf"),
        budget: float = float("inf"),
        **kwargs: Any,
    ) -> Defender:
        config = {
            "id": id,
            "role": "defender",
            "strategy": strategy,
            "capacity": capacity,
            "budget": budget,
            **kwargs,
        }
        return self.create(config)  # type: ignore[return-value]

    def to_config(self, actor: Actor) -> dict[str, Any]:
        config = {
            "id": actor.id,
            "role": actor.role,
            "capacity": actor.capacity,
            "budget": actor.budget,
            "strategy": actor.strategy,
        }

        if hasattr(actor, "decision_interval"):
            config["decision_interval"] = actor.decision_interval

        return config


_factory = ActorFactory()


def get_actor_factory() -> ActorFactory:
    return _factory


def create_actor(config: dict[str, Any]) -> Actor:
    return _factory.create(config)


def create_attacker(
    id: str,
    strategy: str = "greedy",
    **kwargs: Any,
) -> Attacker:
    return _factory.create_attacker(id, strategy, **kwargs)


def create_defender(
    id: str,
    strategy: str = "reactive",
    **kwargs: Any,
) -> Defender:
    return _factory.create_defender(id, strategy, **kwargs)
