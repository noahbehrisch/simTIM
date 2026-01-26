"""
Action loader module.

Handles file I/O operations for loading and saving actions.
"""

import glob
import json
import logging
import os
from typing import Any

from src.actions.action import Action
from src.actions.action_factory import ActionFactory
from src.actions.action_registry import ActionRegistry

logger = logging.getLogger(__name__)


class ActionLoadError(Exception):
    """Raised when action loading fails."""

    def __init__(self, path: str, message: str, cause: Exception | None = None):
        self.path = path
        self.cause = cause
        super().__init__(f"Failed to load action from '{path}': {message}")


class ActionLoader:
    """
    Handles file I/O for actions.

    Responsibilities:
    - Load actions from JSON files
    - Save actions to JSON files
    - Discover action files in directories
    - Populate registries from file system

    Does NOT handle:
    - Action creation (delegates to ActionFactory)
    - Action storage (delegates to ActionRegistry)
    - Validation (delegates to ActionValidator via Factory)
    """

    DEFAULT_LIBRARY_PATH = os.path.join(os.path.dirname(__file__), "library")

    def __init__(
        self,
        factory: ActionFactory | None = None,
        library_path: str | None = None,
    ):
        """
        Initialize the loader.

        Args:
            factory: Factory for creating actions. Creates new if None.
            library_path: Base path for action library. Uses default if None.
        """
        self._factory = factory or ActionFactory()
        self._library_path = library_path or self.DEFAULT_LIBRARY_PATH

    @property
    def factory(self) -> ActionFactory:
        """Get the factory instance."""
        return self._factory

    @property
    def library_path(self) -> str:
        """Get the library base path."""
        return self._library_path

    def load_from_file(self, file_path: str) -> Action:
        """
        Load a single action from a JSON file.

        Args:
            file_path: Path to the JSON file

        Returns:
            Loaded Action instance

        Raises:
            ActionLoadError: If loading fails
        """
        try:
            with open(file_path, encoding="utf-8") as f:
                action_data = json.load(f)
            return self._factory.create(action_data)
        except json.JSONDecodeError as e:
            raise ActionLoadError(file_path, f"Invalid JSON: {e}", e) from e
        except Exception as e:
            raise ActionLoadError(file_path, str(e), e) from e

    def load_from_directory(
        self,
        directory_path: str,
        recursive: bool = False,
    ) -> list[Action]:
        """
        Load all actions from a directory.

        Args:
            directory_path: Path to directory containing JSON files
            recursive: Whether to search subdirectories

        Returns:
            List of loaded actions (skips failures with warnings)
        """
        actions: list[Action] = []

        if not os.path.exists(directory_path):
            logger.warning(f"Directory does not exist: {directory_path}")
            return actions

        pattern = "**/*.json" if recursive else "*.json"
        json_files = glob.glob(os.path.join(directory_path, pattern), recursive=recursive)

        for json_file in json_files:
            try:
                action = self.load_from_file(json_file)
                actions.append(action)
            except ActionLoadError as e:
                logger.warning(str(e))
            except Exception as e:
                logger.warning(f"Failed to load action from {json_file}: {e}")

        logger.debug(f"Loaded {len(actions)} actions from {directory_path}")
        return actions

    def load_attacks(self) -> list[Action]:
        """Load all attack actions from the library."""
        attacks_dir = os.path.join(self._library_path, "attacks")
        return self.load_from_directory(attacks_dir, recursive=True)

    def load_defenses(self) -> list[Action]:
        """Load all defense actions from the library."""
        defenses_dir = os.path.join(self._library_path, "defenses")
        return self.load_from_directory(defenses_dir, recursive=True)

    def load_all(self) -> dict[str, list[Action]]:
        """
        Load all actions from the library.

        Returns:
            Dictionary with 'attack' and 'defense' keys
        """
        return {
            "attack": self.load_attacks(),
            "defense": self.load_defenses(),
        }

    def load_into_registry(self, registry: ActionRegistry) -> int:
        """
        Load all actions from library into a registry.

        Args:
            registry: Registry to populate

        Returns:
            Total number of actions loaded
        """
        all_actions = self.load_all()

        count = 0
        count += registry.register_many(all_actions["attack"], category="attack")
        count += registry.register_many(all_actions["defense"], category="defense")

        logger.info(f"Loaded {count} actions into registry")
        return count

    def save_to_file(self, action: Action, file_path: str) -> None:
        """
        Save an action to a JSON file.

        Args:
            action: Action to save
            file_path: Destination path
        """
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        action_data = self._factory.to_json(action)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(action_data, f, indent=2)

        logger.debug(f"Saved action '{action.name}' to {file_path}")

    def save_to_library(
        self,
        action: Action,
        category: str = "attacks",
        action_type: str | None = None,
    ) -> str:
        """
        Save an action to the library.

        Args:
            action: Action to save
            category: "attacks" or "defenses"
            action_type: Optional subdirectory ("node" or "link")

        Returns:
            Path where the action was saved
        """
        # Build path
        if action_type:
            target_dir = os.path.join(self._library_path, category, action_type)
        else:
            target_dir = os.path.join(self._library_path, category)

        # Generate filename from action name
        filename = self._name_to_filename(action.name)
        file_path = os.path.join(target_dir, filename)

        self.save_to_file(action, file_path)
        return file_path

    def save_many(
        self,
        actions: list[Action],
        directory_path: str,
    ) -> int:
        """
        Save multiple actions to a directory.

        Args:
            actions: Actions to save
            directory_path: Target directory

        Returns:
            Number of actions saved
        """
        os.makedirs(directory_path, exist_ok=True)

        for action in actions:
            filename = self._name_to_filename(action.name)
            file_path = os.path.join(directory_path, filename)
            self.save_to_file(action, file_path)

        return len(actions)

    def load_from_bundle(self, file_path: str) -> dict[str, list[Action]]:
        """
        Load actions from a bundled JSON file (multiple actions).

        Expected format:
        {
            "action_types": {
                "category_name": [action1, action2, ...]
            }
        }

        Args:
            file_path: Path to bundle file

        Returns:
            Dictionary mapping category to action lists
        """
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)

        result: dict[str, list[Action]] = {}

        for category, action_list in data.get("action_types", {}).items():
            result[category] = []
            for action_data in action_list:
                try:
                    action = self._factory.create(action_data)
                    result[category].append(action)
                except Exception as e:
                    logger.warning(f"Failed to create action from bundle: {e}")

        return result

    def save_as_bundle(
        self,
        actions: dict[str, list[Action]],
        file_path: str,
    ) -> None:
        """
        Save actions to a bundled JSON file.

        Args:
            actions: Dictionary mapping category to action lists
            file_path: Destination path
        """
        data: dict[str, Any] = {"action_types": {}}

        for category, action_list in actions.items():
            data["action_types"][category] = [
                self._factory.to_json(action) for action in action_list
            ]

        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        logger.debug(f"Saved action bundle to {file_path}")

    def _name_to_filename(self, name: str) -> str:
        """Convert an action name to a valid filename."""
        # Replace spaces and hyphens with underscores, lowercase
        filename = name.lower().replace(" ", "_").replace("-", "_")
        # Remove any characters that aren't alphanumeric or underscore
        filename = "".join(c for c in filename if c.isalnum() or c == "_")
        return f"{filename}.json"

    def list_available(self) -> dict[str, list[str]]:
        """
        List available action files in the library.

        Returns:
            Dictionary with category keys and lists of filenames
        """
        result = {}

        for category in ["attacks", "defenses"]:
            category_path = os.path.join(self._library_path, category)
            if os.path.exists(category_path):
                files = glob.glob(
                    os.path.join(category_path, "**/*.json"),
                    recursive=True,
                )
                result[category] = [os.path.relpath(f, category_path) for f in files]
            else:
                result[category] = []

        return result
