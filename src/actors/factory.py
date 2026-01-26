"""
Actor factory module.

Creates Actor instances from configurations.
"""

import logging
from dataclasses import dataclass, field
from typing import Any

from src.actors.actor import Actor
from src.actors.attacker import Attacker
from src.actors.defender import Defender

logger = logging.getLogger(__name__)


class ActorCreationError(Exception):
    """Raised when actor creation fails."""

    pass


@dataclass
class ActorValidationResult:
    """Result of actor configuration validation."""

    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class ActorValidator:
    """Validates actor configurations."""

    VALID_ROLES = {"attacker", "defender"}
    REQUIRED_FIELDS = {"id", "role"}

    def validate(self, config: dict[str, Any]) -> ActorValidationResult:
        """
        Validate an actor configuration.

        Args:
            config: Actor configuration dictionary

        Returns:
            ActorValidationResult with validation status
        """
        errors: list[str] = []
        warnings: list[str] = []

        # Check type
        if not isinstance(config, dict):
            return ActorValidationResult(
                valid=False,
                errors=["Actor configuration must be a dictionary"],
            )

        # Check required fields
        for field_name in self.REQUIRED_FIELDS:
            if field_name not in config:
                errors.append(f"Missing required field: {field_name}")

        # Validate id
        actor_id = config.get("id")
        if actor_id is not None:
            if not isinstance(actor_id, str) or not actor_id.strip():
                errors.append("'id' must be a non-empty string")

        # Validate role
        role = config.get("role")
        if role is not None:
            if not isinstance(role, str):
                errors.append("'role' must be a string")
            elif role.lower() not in self.VALID_ROLES:
                errors.append(f"Invalid role '{role}'. Must be one of: {self.VALID_ROLES}")

        # Validate optional fields
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
        """Validate capacity field."""
        capacity = config.get("capacity")
        if capacity is not None:
            if capacity != float("inf"):
                if not isinstance(capacity, (int, float)):
                    errors.append("'capacity' must be a number or infinity")
                elif capacity < 1:
                    warnings.append("'capacity' less than 1 may prevent actions")

    def _validate_budget(
        self,
        config: dict[str, Any],
        errors: list[str],
        warnings: list[str],
    ) -> None:
        """Validate budget field."""
        budget = config.get("budget")
        if budget is not None:
            if budget != float("inf"):
                if not isinstance(budget, (int, float)):
                    errors.append("'budget' must be a number or infinity")
                elif budget <= 0:
                    warnings.append("'budget' <= 0 will prevent actions")

    def _validate_strategy(
        self,
        config: dict[str, Any],
        errors: list[str],
        warnings: list[str],
    ) -> None:
        """Validate strategy field."""
        strategy = config.get("strategy")
        if strategy is not None and not isinstance(strategy, str):
            errors.append("'strategy' must be a string")


class ActorFactory:
    """
    Creates Actor instances from configurations.

    Responsibilities:
    - Create Attacker and Defender instances
    - Apply strategy components
    - Validate configurations

    Does NOT handle:
    - Actor registration or management
    - Simulation integration
    """

    def __init__(self, validator: ActorValidator | None = None):
        """
        Initialize the factory.

        Args:
            validator: Optional validator instance
        """
        self._validator = validator or ActorValidator()

    @property
    def validator(self) -> ActorValidator:
        """Get the validator instance."""
        return self._validator

    def create(
        self,
        config: dict[str, Any],
        validate: bool = True,
    ) -> Actor:
        """
        Create an Actor from configuration.

        Args:
            config: Actor configuration dictionary
            validate: Whether to validate before creation

        Returns:
            Configured Actor instance (Attacker or Defender)

        Raises:
            ActorCreationError: If validation fails or creation encounters error
        """
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
        """Create an Attacker from configuration."""
        attacker = Attacker(
            id=config["id"],
            strategy=config.get("strategy", "greedy"),
            capacity=config.get("capacity", float("inf")),
            budget=config.get("budget", float("inf")),
        )

        # Apply additional properties
        if "decision_interval" in config:
            attacker.decision_interval = config["decision_interval"]

        logger.debug(f"Created attacker: {attacker.id}")
        return attacker

    def _create_defender(self, config: dict[str, Any]) -> Defender:
        """Create a Defender from configuration."""
        defender = Defender(
            id=config["id"],
            strategy=config.get("strategy", "reactive"),
            capacity=config.get("capacity", float("inf")),
            budget=config.get("budget", float("inf")),
        )

        # Apply additional properties
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
        """
        Create an Attacker with explicit parameters.

        Convenience method for creating attackers without config dict.
        """
        config = {
            "id": id,
            "role": "attacker",
            "strategy": strategy,
            "capacity": capacity,
            "budget": budget,
            **kwargs,
        }
        return self.create(config)  # type: ignore

    def create_defender(
        self,
        id: str,
        strategy: str = "reactive",
        capacity: float = float("inf"),
        budget: float = float("inf"),
        **kwargs: Any,
    ) -> Defender:
        """
        Create a Defender with explicit parameters.

        Convenience method for creating defenders without config dict.
        """
        config = {
            "id": id,
            "role": "defender",
            "strategy": strategy,
            "capacity": capacity,
            "budget": budget,
            **kwargs,
        }
        return self.create(config)  # type: ignore

    def to_config(self, actor: Actor) -> dict[str, Any]:
        """
        Convert an Actor back to configuration format.

        Args:
            actor: Actor to serialize

        Returns:
            Configuration dictionary
        """
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


# =============================================================================
# Global instance and convenience functions
# =============================================================================

_factory = ActorFactory()


def get_actor_factory() -> ActorFactory:
    """Get the global actor factory."""
    return _factory


def create_actor(config: dict[str, Any]) -> Actor:
    """Create an actor from configuration (convenience function)."""
    return _factory.create(config)


def create_attacker(
    id: str,
    strategy: str = "greedy",
    **kwargs: Any,
) -> Attacker:
    """Create an attacker (convenience function)."""
    return _factory.create_attacker(id, strategy, **kwargs)


def create_defender(
    id: str,
    strategy: str = "reactive",
    **kwargs: Any,
) -> Defender:
    """Create a defender (convenience function)."""
    return _factory.create_defender(id, strategy, **kwargs)
