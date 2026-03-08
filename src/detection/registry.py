import logging
import os
from typing import Any

from src.detection.base_detection import BaseDetectionEngine
from src.utils.discovery import discover_subclasses

logger = logging.getLogger(__name__)


class DetectionEngineError(Exception):
    pass


class DetectionEngineRegistry:
    def __init__(self):
        self._engines: dict[str, type[BaseDetectionEngine]] = {}
        self._default_params: dict[str, dict[str, Any]] = {}

        detection_dir = os.path.dirname(os.path.abspath(__file__))
        for name, engine_class, default_params in discover_subclasses(
            detection_dir,
            "src.detection",
            BaseDetectionEngine,
            suffix="_detection",
            exclude="base_detection",
            extract_defaults=True,
        ):
            self.register(name, engine_class, default_params)

    def register(
        self,
        name: str,
        engine_class: type[BaseDetectionEngine],
        default_params: dict[str, Any] | None = None,
    ) -> None:
        if not issubclass(engine_class, BaseDetectionEngine):
            raise TypeError(
                f"Engine class must inherit from BaseDetectionEngine, got {engine_class}"
            )

        self._engines[name.lower()] = engine_class
        self._default_params[name.lower()] = default_params or {}
        logger.debug(f"Registered detection engine: {name}")

    def unregister(self, name: str) -> bool:
        name_lower = name.lower()
        if name_lower in self._engines:
            del self._engines[name_lower]
            del self._default_params[name_lower]
            return True
        return False

    def get_available(self) -> list[str]:
        return list(self._engines.keys())

    def get_engine_class(self, name: str) -> type[BaseDetectionEngine] | None:
        return self._engines.get(name.lower())

    def get_default_params(self, name: str) -> dict[str, Any]:
        return self._default_params.get(name.lower(), {}).copy()

    def create(
        self,
        name: str,
        **kwargs: Any,
    ) -> BaseDetectionEngine:
        name_lower = name.lower()

        if name_lower not in self._engines:
            available = ", ".join(self.get_available())
            raise DetectionEngineError(
                f"Unknown detection engine type: '{name}'. Available: {available}"
            )

        engine_class = self._engines[name_lower]
        params = self._default_params[name_lower].copy()
        params.update(kwargs)

        try:
            engine = engine_class(**params)
            logger.info(f"Created {name} detection engine")
            return engine
        except Exception as e:
            raise DetectionEngineError(f"Failed to create {name} detection engine: {e}") from e

    def create_from_config(self, config: dict[str, Any]) -> BaseDetectionEngine:
        if not isinstance(config, dict):
            raise DetectionEngineError(
                f"Detection engine config must be a dictionary, got {type(config)}"
            )

        engine_type = config.get("type")
        if not engine_type:
            raise DetectionEngineError("Detection engine config missing required 'type' field")

        params = {k: v for k, v in config.items() if k != "type"}

        return self.create(engine_type, **params)

    def get_engine_info(self, name: str) -> dict[str, Any] | None:
        name_lower = name.lower()
        if name_lower not in self._engines:
            return None

        engine_class = self._engines[name_lower]
        return {
            "name": name_lower,
            "class": engine_class.__name__,
            "module": engine_class.__module__,
            "default_params": self._default_params[name_lower],
            "docstring": engine_class.__doc__,
        }


_registry = DetectionEngineRegistry()


def get_detection_registry() -> DetectionEngineRegistry:
    return _registry


def create_detection_engine(
    name: str = "uniform",
    **kwargs: Any,
) -> BaseDetectionEngine:
    return _registry.create(name, **kwargs)


def list_detection_engines() -> list[str]:
    return _registry.get_available()
