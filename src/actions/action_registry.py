import logging
from collections.abc import Iterator
from typing import Any

from src.actions.action import Action

logger = logging.getLogger(__name__)


class ActionRegistry:
    def __init__(self):
        self._actions: dict[str, Action] = {}
        self._by_category: dict[str, set[str]] = {}
        self._by_action_type: dict[str, set[str]] = {}

    def register(self, action: Action, category: str = "general") -> None:
        name = action.name

        if name in self._actions:
            logger.debug(f"Replacing existing action: {name}")

        self._actions[name] = action

        if category not in self._by_category:
            self._by_category[category] = set()
        self._by_category[category].add(name)

        action_type = action.action_type
        if action_type not in self._by_action_type:
            self._by_action_type[action_type] = set()
        self._by_action_type[action_type].add(name)

        logger.debug(f"Registered action '{name}' in category '{category}'")

    def register_many(self, actions: list[Action], category: str = "general") -> int:
        for action in actions:
            self.register(action, category)
        return len(actions)

    def unregister(self, name: str) -> Action | None:
        if name not in self._actions:
            return None

        action = self._actions.pop(name)

        for category_actions in self._by_category.values():
            category_actions.discard(name)

        for type_actions in self._by_action_type.values():
            type_actions.discard(name)

        logger.debug(f"Unregistered action: {name}")
        return action

    def get(self, name: str) -> Action | None:
        return self._actions.get(name)

    def get_all(self) -> list[Action]:
        return list(self._actions.values())

    def get_by_category(self, category: str) -> list[Action]:
        names = self._by_category.get(category, set())
        return [self._actions[name] for name in names if name in self._actions]

    def get_by_type(self, action_type: str) -> list[Action]:
        names = self._by_action_type.get(action_type, set())
        return [self._actions[name] for name in names if name in self._actions]

    def get_attack_actions(self) -> list[Action]:
        return self.get_by_category("attack")

    def get_defense_actions(self) -> list[Action]:
        return self.get_by_category("defense")

    def get_node_actions(self) -> list[Action]:
        return self.get_by_type("node")

    def get_link_actions(self) -> list[Action]:
        return self.get_by_type("link")

    def filter(
        self,
        category: str | None = None,
        action_type: str | None = None,
        name_contains: str | None = None,
    ) -> list[Action]:
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
        return list(self._by_category.keys())

    def get_names(self) -> list[str]:
        return list(self._actions.keys())

    def contains(self, name: str) -> bool:
        return name in self._actions

    def clear(self) -> None:
        self._actions.clear()
        self._by_category.clear()
        self._by_action_type.clear()
        logger.debug("Registry cleared")

    def __len__(self) -> int:
        return len(self._actions)

    def __iter__(self) -> Iterator[Action]:
        return iter(self._actions.values())

    def __contains__(self, name: str) -> bool:
        return name in self._actions

    def summary(self) -> dict[str, Any]:
        return {
            "total": len(self._actions),
            "by_category": {cat: len(names) for cat, names in self._by_category.items()},
            "by_type": {t: len(names) for t, names in self._by_action_type.items()},
        }
