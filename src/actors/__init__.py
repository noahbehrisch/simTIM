"""
Actors module.

Provides actors (attackers and defenders) for simulation.

Main Classes:
- Actor: Base class for all actors
- Attacker: Attack actor with compromise capabilities
- Defender: Defense actor with detection/response capabilities
- ActorFactory: Creates actor instances from configurations
- ActorValidator: Validates actor configurations

Convenience Functions:
- create_actor(): Create actor from config dict
- create_attacker(): Create attacker with parameters
- create_defender(): Create defender with parameters
- get_actor_factory(): Get the global factory instance

Strategies Module:
- See src.actors.strategies for strategy implementations
"""

from .actor import Actor
from .attacker import Attacker
from .defender import Defender
from .factory import (
    ActorCreationError,
    ActorFactory,
    ActorValidationResult,
    ActorValidator,
    create_actor,
    create_attacker,
    create_defender,
    get_actor_factory,
)

__all__ = [
    # Core classes
    "Actor",
    "Attacker",
    "Defender",
    # Factory
    "ActorFactory",
    "ActorValidator",
    "ActorValidationResult",
    "ActorCreationError",
    # Convenience functions
    "create_actor",
    "create_attacker",
    "create_defender",
    "get_actor_factory",
]
