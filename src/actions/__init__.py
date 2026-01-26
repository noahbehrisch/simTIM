"""
Actions module.

Provides action management including loading, validation, creation, and registry.

Main Classes:
- Action: Core action class representing attack/defense actions
- ActionValidator: Validates action configurations
- ActionFactory: Creates Action instances from JSON specs
- ActionRegistry: Stores and retrieves actions
- ActionLoader: Handles file I/O for actions
- ActionManager: Facade coordinating all components

Global Instance:
- action_manager: Pre-configured ActionManager instance
"""

from .action import Action
from .action_factory import ActionCreationError, ActionFactory, FunctionSpecError
from .action_loader import ActionLoader, ActionLoadError
from .action_manager import ActionManager, action_manager
from .action_registry import ActionRegistry
from .action_validator import ActionValidator, ValidationResult

__all__ = [
    # Core action class
    "Action",
    # Validation
    "ActionValidator",
    "ValidationResult",
    # Factory
    "ActionFactory",
    "ActionCreationError",
    "FunctionSpecError",
    # Registry
    "ActionRegistry",
    # Loader
    "ActionLoader",
    "ActionLoadError",
    # Manager (facade)
    "ActionManager",
    "action_manager",
]
