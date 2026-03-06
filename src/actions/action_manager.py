"""
Action management module.

Provides a unified interface (facade) for action operations, coordinating
the validator, factory, registry, and loader components.

Architecture:
    ActionManager (Facade)
        ├── ActionValidator  - Validates JSON configurations
        ├── ActionFactory    - Creates Action objects
        ├── ActionRegistry   - Stores and retrieves actions
        └── ActionLoader     - Handles file I/O
"""

import logging
from typing import Any

from src.actions.action import Action
from src.actions.action_factory import ActionFactory
from src.actions.action_loader import ActionLoader
from src.actions.action_registry import ActionRegistry
from src.actions.action_validator import ActionValidator
from src.core.access_levels import NodeAccessLevel

logger = logging.getLogger(__name__)


class ActionManager:
    """
    Facade for action management operations.

    Provides a unified API while delegating to specialized components:
    - Validation → ActionValidator
    - Creation → ActionFactory
    - Storage → ActionRegistry
    - File I/O → ActionLoader
    """

    def __init__(
        self,
        validator: ActionValidator | None = None,
        factory: ActionFactory | None = None,
        registry: ActionRegistry | None = None,
        loader: ActionLoader | None = None,
        auto_load: bool = True,
    ):
        """
        Initialize the action manager.

        Args:
            validator: Custom validator instance
            factory: Custom factory instance
            registry: Custom registry instance
            loader: Custom loader instance
            auto_load: Whether to automatically load actions from library
        """
        # Initialize components
        self._validator = validator or ActionValidator()
        self._factory = factory or ActionFactory(self._validator)
        self._registry = registry or ActionRegistry()
        self._loader = loader or ActionLoader(self._factory)

        # Auto-load actions from library
        if auto_load:
            self._auto_load()

    def _auto_load(self) -> None:
        """Load all actions from the library into the registry."""
        try:
            self._loader.load_into_registry(self._registry)
        except Exception as e:
            logger.warning(f"Failed to auto-load actions: {e}")

    # =========================================================================
    # Component Access
    # =========================================================================

    @property
    def validator(self) -> ActionValidator:
        """Get the validator component."""
        return self._validator

    @property
    def factory(self) -> ActionFactory:
        """Get the factory component."""
        return self._factory

    @property
    def registry(self) -> ActionRegistry:
        """Get the registry component."""
        return self._registry

    @property
    def loader(self) -> ActionLoader:
        """Get the loader component."""
        return self._loader

    # =========================================================================
    # Validation and Creation
    # =========================================================================

    def validate_action_json(self, action_data: dict[str, Any]) -> dict[str, Any]:
        """
        Validate an action JSON configuration.

        Args:
            action_data: Action configuration dictionary

        Returns:
            Dictionary with 'valid', 'errors', and 'warnings' keys
        """
        result = self._validator.validate(action_data)
        return {
            "valid": result.valid,
            "errors": result.errors,
            "warnings": result.warnings,
        }

    def action_from_json(self, action_data: dict[str, Any]) -> Action:
        """
        Create an Action from JSON data.

        Args:
            action_data: Action configuration dictionary

        Returns:
            Configured Action instance

        Raises:
            ValueError: If validation fails or creation encounters an error
        """
        return self._factory.create(action_data)

    def action_to_json(self, action: Action) -> dict[str, Any]:
        """
        Convert an Action to JSON format.

        Args:
            action: Action to serialize

        Returns:
            Dictionary representation
        """
        return self._factory.to_json(action)

    # =========================================================================
    # Loading Operations (delegates to loader)
    # =========================================================================

    def load_actions_from_directory(self, directory_path: str) -> list[Action]:
        """Load actions from a directory."""
        return self._loader.load_from_directory(directory_path)

    def load_all_actions(self) -> dict[str, list[Action]]:
        """
        Load all actions from the library.

        Returns:
            Dictionary with 'attack_actions' and 'defense_actions' keys
        """
        actions = self._loader.load_all()
        return {
            "attack_actions": actions.get("attack", []),
            "defense_actions": actions.get("defense", []),
        }

    def load_actions_from_file(self, file_path: str) -> dict[str, list[Action]]:
        """Load actions from a bundled JSON file."""
        return self._loader.load_from_bundle(file_path)

    def load_specific_actions(self, action_names: list[str]) -> list[Action]:
        """Load specific actions by name."""
        result: list[Action] = []
        for name in action_names:
            if self._registry.contains(name):
                action = self._registry.get(name)
                if action is not None:
                    result.append(action)
        return result

    # =========================================================================
    # Registry Operations (delegates to registry)
    # =========================================================================

    def get_attack_actions(self) -> list[Action]:
        """Get all attack actions from the registry."""
        actions = self._registry.get_attack_actions()
        if not actions:
            # Fallback to loading if registry is empty
            return self._loader.load_attacks()
        return actions

    def get_defense_actions(self) -> list[Action]:
        """Get all defense actions from the registry."""
        actions = self._registry.get_defense_actions()
        if not actions:
            return self._loader.load_defenses()
        return actions

    def get_all_available_actions(self) -> list[Action]:
        """Get all available actions."""
        return self._registry.get_all()

    def get_action(self, name: str) -> Action | None:
        """Get an action by name."""
        return self._registry.get(name)

    def register_action(self, action: Action, category: str = "general") -> None:
        """Register an action in the registry."""
        self._registry.register(action, category)

    # =========================================================================
    # Saving Operations (delegates to loader)
    # =========================================================================

    def save_action_to_file(self, action: Action, file_path: str) -> None:
        """Save an action to a JSON file."""
        self._loader.save_to_file(action, file_path)

    def save_action_to_library(self, action: Action, action_type: str = "attacks") -> str:
        """Save an action to the library."""
        return self._loader.save_to_library(action, category=action_type)

    def save_actions_to_file(self, actions: dict[str, list[Action]], file_path: str) -> None:
        """Save actions to a bundled JSON file."""
        self._loader.save_as_bundle(actions, file_path)

    def save_actions(
        self,
        attack_actions: list[Action],
        defense_actions: list[Action],
        file_path: str | None = None,
    ) -> None:
        """Save attack and defense actions."""
        if file_path:
            actions = {
                "attack_actions": attack_actions,
                "defense_actions": defense_actions,
            }
            self._loader.save_as_bundle(actions, file_path)
        else:
            for action in attack_actions:
                self._loader.save_to_library(action, "attacks")
            for action in defense_actions:
                self._loader.save_to_library(action, "defenses")

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def reload(self) -> None:
        """Reload all actions from the library."""
        self._registry.clear()
        self._loader.load_into_registry(self._registry)

    def summary(self) -> dict[str, Any]:
        """Get a summary of available actions."""
        return self._registry.summary()


# =============================================================================
# Global Instance
# =============================================================================

action_manager = ActionManager()


# =============================================================================
# Utility Functions (unchanged from original)
# =============================================================================


def analyze_action_access_impact(action: Action, current_access: str) -> str | None:
    """
    Analyze what access level an action would grant.

    Args:
        action: The action to analyze
        current_access: Current access level string

    Returns:
        Predicted access level string, "NO_ACCESS_CHANGE", or None
    """
    try:
        if hasattr(action, "_json_data") and action._json_data is not None:
            postcondition = action._json_data.get("postcondition", {})
        else:
            return None
        return _analyze_postcondition_access(postcondition)
    except Exception:
        return None


def _analyze_postcondition_access(postcondition: dict[str, Any]) -> str | None:
    """Extract access level changes from a postcondition spec."""
    post_type = postcondition.get("type")

    if post_type == "compound":
        for action in postcondition.get("actions", []):
            if action.get("type") == "set_access":
                return action.get("value")

    elif post_type == "set_access":
        return postcondition.get("value")

    elif post_type in [
        "set_links_access",
        "set_property",
        "clear_assets",
        "add_vulnerability",
        "remove_vulnerability",
        "increment_counter",
        "set_software",
    ]:
        return "NO_ACCESS_CHANGE"

    return None


def would_action_improve_access(
    action: Action,
    node: Any,
    current_access: Any,
    actor_id: str,
) -> bool:
    """
    Determine if an action would improve the actor's access level.

    Args:
        action: The action to evaluate
        node: Target node
        current_access: Current access level (string or NodeAccessLevel)
        actor_id: ID of the acting entity

    Returns:
        True if the action would improve access
    """
    # Handle link actions
    if hasattr(action, "is_link_action") and action.is_link_action():
        if hasattr(node, "successful_actions_by_actor"):
            actor_actions = node.successful_actions_by_actor.get(actor_id, set())
            if action.name in actor_actions:
                return False
        return True

    if not hasattr(node, "id") or not hasattr(node, "access"):
        return False

    try:
        # current_access should already be NodeAccessLevel
        current_level = current_access

        current_access_str = current_level.to_string()

        predicted_access = analyze_action_access_impact(action, current_access_str)

        if predicted_access == "NO_ACCESS_CHANGE":
            return _check_non_access_action(action, node, actor_id)

        elif predicted_access:
            predicted_level = NodeAccessLevel.from_string(predicted_access)
            return predicted_level > current_level

        # Heuristic based on action name
        return _heuristic_access_improvement(action, node, current_level, actor_id)

    except Exception:
        current_level = NodeAccessLevel.from_string(current_access)
        return current_level < NodeAccessLevel.ADMIN


def _check_non_access_action(action: Action, node: Any, actor_id: str) -> bool:
    """Check if a non-access-changing action should still be executed."""
    if hasattr(node, "successful_actions_by_actor"):
        actor_actions = node.successful_actions_by_actor.get(actor_id, set())
        if action.name in actor_actions:
            logger.debug(f"{action.name} on {getattr(node, 'id', '?')}: Already executed")
            return False
    return True


def _heuristic_access_improvement(
    action: Action,
    node: Any,
    current_level: NodeAccessLevel,
    actor_id: str,
) -> bool:
    """Use heuristics based on action name to determine access improvement."""
    action_name_lower = action.name.lower()
    target_level: NodeAccessLevel | None = None

    # Reconnaissance actions
    if any(kw in action_name_lower for kw in ["scan", "reconnaissance", "discovery"]):
        if hasattr(node, "successful_actions_by_actor"):
            if action.name in node.successful_actions_by_actor.get(actor_id, set()):
                return False
        return True

    # Privilege escalation (check before initial access since "exploit" matches both)
    if any(kw in action_name_lower for kw in ["privilege", "escalation", "admin"]):
        target_level = NodeAccessLevel.ADMIN

    # Initial access actions
    elif any(kw in action_name_lower for kw in ["phishing", "exploit", "brute"]):
        target_level = NodeAccessLevel.USER

    # Data exfiltration / collection (exclude ransomware "Data Encrypted for Impact")
    elif (
        any(kw in action_name_lower for kw in ["exfiltration", "data", "steal"])
        and "encrypted" not in action_name_lower
    ):
        return current_level >= NodeAccessLevel.USER and not _has_already_exfiltrated(
            node, actor_id
        )

    # Default progression
    elif current_level == NodeAccessLevel.VISIBLE:
        target_level = NodeAccessLevel.USER
    elif current_level == NodeAccessLevel.USER:
        target_level = NodeAccessLevel.ADMIN
    else:
        return False

    return target_level > current_level


def _has_already_exfiltrated(node: Any, actor_id: str) -> bool:
    """Check if data has already been exfiltrated from a node."""
    if not hasattr(node, "assets") or len(node.assets) == 0:
        return True

    if hasattr(node, "successful_actions_by_actor"):
        actor_actions = node.successful_actions_by_actor.get(actor_id, set())
        if "Exfiltration Over C2 Channel" in actor_actions:
            return True

    return False
