from dataclasses import dataclass, field
from typing import Any


class SimTIMError(Exception):
    pass


class ConfigurationError(SimTIMError):
    pass


class NetworkConfigError(ConfigurationError):
    pass


class ActionConfigError(ConfigurationError):
    pass


class SimulationError(SimTIMError):
    pass


@dataclass
class ActionError(SimulationError):
    action_name: str
    reason: str
    target: str | None = None
    actor: str | None = None
    details: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        msg = f"Action '{self.action_name}' failed: {self.reason}"
        if self.target:
            msg += f" (target: {self.target})"
        if self.actor:
            msg += f" (actor: {self.actor})"
        return msg

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_name": self.action_name,
            "reason": self.reason,
            "target": self.target,
            "actor": self.actor,
            "details": self.details,
        }


@dataclass
class PreconditionError(ActionError):
    condition_type: str | None = None

    def __str__(self) -> str:
        base = super().__str__()
        if self.condition_type:
            base += f" [condition: {self.condition_type}]"
        return base


@dataclass
class CapacityError(SimulationError):
    actor_id: str
    current_capacity: int
    max_capacity: int | float

    def __str__(self) -> str:
        return f"Actor '{self.actor_id}' capacity exceeded: {self.current_capacity}/{self.max_capacity}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "actor_id": self.actor_id,
            "current_capacity": self.current_capacity,
            "max_capacity": self.max_capacity,
        }


@dataclass
class BudgetError(SimulationError):
    actor_id: str
    incurred_cost: float
    budget: float

    def __str__(self) -> str:
        return f"Actor '{self.actor_id}' budget exceeded: {self.incurred_cost}/{self.budget}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "actor_id": self.actor_id,
            "incurred_cost": self.incurred_cost,
            "budget": self.budget,
        }


class DetectionError(SimulationError):
    pass


class ValidationError(SimTIMError):
    pass


@dataclass
class ActorValidationError(ValidationError):
    actor_id: str | None
    errors: list[str] = field(default_factory=list)

    def __str__(self) -> str:
        return f"Invalid actor '{self.actor_id}': {', '.join(self.errors)}"


@dataclass
class NodeValidationError(ValidationError):
    node_id: str | None
    errors: list[str] = field(default_factory=list)

    def __str__(self) -> str:
        return f"Invalid node '{self.node_id}': {', '.join(self.errors)}"
