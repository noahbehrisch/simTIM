"""
Action registry module.

Provides storage and retrieval of Action objects with categorization
and filtering capabilities.
"""

import logging
from collections.abc import Iterator
from typing import Any

from src.actions.action import Action

logger = logging.getLogger(__name__)


class ActionRegistry:
    """
    Stores and retrieves Action objects.

    Responsibilities:
    - Store actions by name and category
    - Provide filtered retrieval (by type, category)
    - Track action metadata

    Does NOT handle:
    - Action creation (see ActionFactory)
    - File I/O (see ActionLoader)
    - Validation (see ActionValidator)
    """

    def __init__(self):
        """Initialize an empty registry."""
        self._actions: dict[str, Action] = {}
        self._by_category: dict[str, set[str]] = {}
        self._by_action_type: dict[str, set[str]] = {}  # "node" or "link"

    def register(self, action: Action, category: str = "general") -> None:
        """
        Register an action in the registry.

        Args:
            action: Action to register
            category: Category for the action (e.g., "attack", "defense")
        """
        name = action.name

        if name in self._actions:
            logger.debug(f"Replacing existing action: {name}")

        self._actions[name] = action

        # Index by category
        if category not in self._by_category:
            self._by_category[category] = set()
        self._by_category[category].add(name)

        # Index by action type (node/link)
        action_type = action.action_type
        if action_type not in self._by_action_type:
            self._by_action_type[action_type] = set()
        self._by_action_type[action_type].add(name)

        logger.debug(f"Registered action '{name}' in category '{category}'")

    def register_many(self, actions: list[Action], category: str = "general") -> int:
        """
        Register multiple actions.

        Args:
            actions: List of actions to register
            category: Category for all actions

        Returns:
            Number of actions registered
        """
        for action in actions:
            self.register(action, category)
        return len(actions)

    def unregister(self, name: str) -> Action | None:
        """
        Remove an action from the registry.

        Args:
            name: Name of the action to remove

        Returns:
            The removed action, or None if not found
        """
        if name not in self._actions:
            return None

        action = self._actions.pop(name)

        # Remove from category index
        for category_actions in self._by_category.values():
            category_actions.discard(name)

        # Remove from type index
        for type_actions in self._by_action_type.values():
            type_actions.discard(name)

        logger.debug(f"Unregistered action: {name}")
        return action

    def get(self, name: str) -> Action | None:
        """
        Get an action by name.

        Args:
            name: Action name

        Returns:
            Action or None if not found
        """
        return self._actions.get(name)

    def get_all(self) -> list[Action]:
        """Get all registered actions."""
        return list(self._actions.values())

    def get_by_category(self, category: str) -> list[Action]:
        """
        Get all actions in a category.

        Args:
            category: Category name (e.g., "attack", "defense")

        Returns:
            List of actions in the category
        """
        names = self._by_category.get(category, set())
        return [self._actions[name] for name in names if name in self._actions]

    def get_by_type(self, action_type: str) -> list[Action]:
        """
        Get all actions of a specific type.

        Args:
            action_type: "node" or "link"

        Returns:
            List of actions of that type
        """
        names = self._by_action_type.get(action_type, set())
        return [self._actions[name] for name in names if name in self._actions]

    def get_attack_actions(self) -> list[Action]:
        """Get all attack actions."""
        return self.get_by_category("attack")

    def get_defense_actions(self) -> list[Action]:
        """Get all defense actions."""
        return self.get_by_category("defense")

    def get_node_actions(self) -> list[Action]:
        """Get all node-type actions."""
        return self.get_by_type("node")

    def get_link_actions(self) -> list[Action]:
        """Get all link-type actions."""
        return self.get_by_type("link")

    def filter(
        self,
        category: str | None = None,
        action_type: str | None = None,
        name_contains: str | None = None,
    ) -> list[Action]:
        """
        Filter actions by multiple criteria.

        Args:
            category: Filter by category
            action_type: Filter by type ("node" or "link")
            name_contains: Filter by name substring (case-insensitive)

        Returns:
            List of matching actions
        """
        results = self.get_all()

        if category is not None:
            category_names = self._by_category.get(category, set())
            results = [a for a in results if a.name in category_names]

        if action_type is not None:
            results = [a for a in results if a.action_type == action_type]

        if name_contains is not None:
            search_lower = name_contains.lower()
            results = [a for a in results if search_lower in a.name.lower()]

        return results

    def get_categories(self) -> list[str]:
        """Get all registered categories."""
        return list(self._by_category.keys())

    def get_names(self) -> list[str]:
        """Get all registered action names."""
        return list(self._actions.keys())

    def contains(self, name: str) -> bool:
        """Check if an action is registered."""
        return name in self._actions

    def clear(self) -> None:
        """Clear all registered actions."""
        self._actions.clear()
        self._by_category.clear()
        self._by_action_type.clear()
        logger.debug("Registry cleared")

    def __len__(self) -> int:
        """Get the number of registered actions."""
        return len(self._actions)

    def __iter__(self) -> Iterator[Action]:
        """Iterate over all actions."""
        return iter(self._actions.values())

    def __contains__(self, name: str) -> bool:
        """Check if an action is registered."""
        return name in self._actions

    def summary(self) -> dict[str, Any]:
        """
        Get a summary of the registry contents.

        Returns:
            Dictionary with counts by category and type
        """
        return {
            "total": len(self._actions),
            "by_category": {cat: len(names) for cat, names in self._by_category.items()},
            "by_type": {t: len(names) for t, names in self._by_action_type.items()},
        }
