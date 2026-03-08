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
    def __init__(self, path: str, message: str, cause: Exception | None = None):
        self.path = path
        self.cause = cause
        super().__init__(f"Failed to load action from '{path}': {message}")


class ActionLoader:
    DEFAULT_LIBRARY_PATH = os.path.join(os.path.dirname(__file__), "library")

    def __init__(
        self,
        factory: ActionFactory | None = None,
        library_path: str | None = None,
    ):
        self._factory = factory or ActionFactory()
        self._library_path = library_path or self.DEFAULT_LIBRARY_PATH

    @property
    def factory(self) -> ActionFactory:
        return self._factory

    @property
    def library_path(self) -> str:
        return self._library_path

    def load_from_file(self, file_path: str) -> Action:
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
        attacks_dir = os.path.join(self._library_path, "attacks")
        return self.load_from_directory(attacks_dir, recursive=True)

    def load_defenses(self) -> list[Action]:
        defenses_dir = os.path.join(self._library_path, "defenses")
        return self.load_from_directory(defenses_dir, recursive=True)

    def load_all(self) -> dict[str, list[Action]]:
        return {
            "attack": self.load_attacks(),
            "defense": self.load_defenses(),
        }

    def load_into_registry(self, registry: ActionRegistry) -> int:
        all_actions = self.load_all()

        count = 0
        count += registry.register_many(all_actions["attack"], category="attack")
        count += registry.register_many(all_actions["defense"], category="defense")

        logger.info(f"Loaded {count} actions into registry")
        return count

    def save_to_file(self, action: Action, file_path: str) -> None:
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
        if action_type:
            target_dir = os.path.join(self._library_path, category, action_type)
        else:
            target_dir = os.path.join(self._library_path, category)

        filename = self._name_to_filename(action.name)
        file_path = os.path.join(target_dir, filename)

        self.save_to_file(action, file_path)
        return file_path

    def save_many(
        self,
        actions: list[Action],
        directory_path: str,
    ) -> int:
        os.makedirs(directory_path, exist_ok=True)

        for action in actions:
            filename = self._name_to_filename(action.name)
            file_path = os.path.join(directory_path, filename)
            self.save_to_file(action, file_path)

        return len(actions)

    def load_from_bundle(self, file_path: str) -> dict[str, list[Action]]:
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
        filename = name.lower().replace(" ", "_").replace("-", "_")
        filename = "".join(c for c in filename if c.isalnum() or c == "_")
        return f"{filename}.json"

    def list_available(self) -> dict[str, list[str]]:
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
