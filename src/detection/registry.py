"""
Detection engine registry module.

Provides a registry for detection engines with factory methods.
"""

import logging
from typing import Any

from src.detection.base_detection import BaseDetectionEngine
from src.detection.exponential_detection import ExponentialDetectionEngine
from src.detection.linear_detection import LinearDetectionEngine
from src.detection.uniform_detection import UniformDetectionEngine

logger = logging.getLogger(__name__)


class DetectionEngineError(Exception):
    """Raised when detection engine creation fails."""

    pass


class DetectionEngineRegistry:
    """
    Registry for detection engines.

    Provides registration and creation of detection engines by type name.
    Supports built-in engines and custom engine registration.

    Built-in engines:
    - "uniform": UniformDetectionEngine
    - "exponential": ExponentialDetectionEngine
    - "linear": LinearDetectionEngine
    """

    # Default engine configurations
    DEFAULT_CONFIGS: dict[str, dict[str, Any]] = {
        "uniform": {
            "class": UniformDetectionEngine,
            "default_params": {"default_detection_probability": 0.3},
        },
        "exponential": {
            "class": ExponentialDetectionEngine,
            "default_params": {"lambda_param": 4.605, "default_detection_probability": 0.4},
        },
        "linear": {
            "class": LinearDetectionEngine,
            "default_params": {"exponent": 2.0, "default_detection_probability": 0.35},
        },
    }

    def __init__(self):
        """Initialize the registry with built-in engines."""
        self._engines: dict[str, type[BaseDetectionEngine]] = {}
        self._default_params: dict[str, dict[str, Any]] = {}

        # Register built-in engines
        for name, config in self.DEFAULT_CONFIGS.items():
            self.register(name, config["class"], config["default_params"])

    def register(
        self,
        name: str,
        engine_class: type[BaseDetectionEngine],
        default_params: dict[str, Any] | None = None,
    ) -> None:
        """
        Register a detection engine type.

        Args:
            name: Name to register under (e.g., "uniform", "exponential")
            engine_class: Detection engine class (must inherit BaseDetectionEngine)
            default_params: Default parameters for engine creation
        """
        if not issubclass(engine_class, BaseDetectionEngine):
            raise TypeError(
                f"Engine class must inherit from BaseDetectionEngine, got {engine_class}"
            )

        self._engines[name.lower()] = engine_class
        self._default_params[name.lower()] = default_params or {}
        logger.debug(f"Registered detection engine: {name}")

    def unregister(self, name: str) -> bool:
        """
        Unregister a detection engine type.

        Args:
            name: Name of engine to unregister

        Returns:
            True if engine was unregistered, False if not found
        """
        name_lower = name.lower()
        if name_lower in self._engines:
            del self._engines[name_lower]
            del self._default_params[name_lower]
            return True
        return False

    def get_available(self) -> list[str]:
        """
        Get list of available engine types.

        Returns:
            List of registered engine type names
        """
        return list(self._engines.keys())

    def get_engine_class(self, name: str) -> type[BaseDetectionEngine] | None:
        """
        Get engine class by name.

        Args:
            name: Engine type name

        Returns:
            Engine class or None if not found
        """
        return self._engines.get(name.lower())

    def get_default_params(self, name: str) -> dict[str, Any]:
        """
        Get default parameters for an engine type.

        Args:
            name: Engine type name

        Returns:
            Default parameters dictionary
        """
        return self._default_params.get(name.lower(), {}).copy()

    def create(
        self,
        name: str,
        **kwargs: Any,
    ) -> BaseDetectionEngine:
        """
        Create a detection engine instance.

        Args:
            name: Engine type name (e.g., "uniform", "exponential", "linear")
            **kwargs: Override default parameters

        Returns:
            Configured detection engine instance

        Raises:
            DetectionEngineError: If engine type not found or creation fails
        """
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
        """
        Create a detection engine from configuration dictionary.

        Args:
            config: Configuration with "type" and optional parameters
                Example: {"type": "exponential", "lambda_param": 3.0}

        Returns:
            Configured detection engine instance

        Raises:
            DetectionEngineError: If configuration is invalid or creation fails
        """
        if not isinstance(config, dict):
            raise DetectionEngineError(
                f"Detection engine config must be a dictionary, got {type(config)}"
            )

        engine_type = config.get("type")
        if not engine_type:
            raise DetectionEngineError("Detection engine config missing required 'type' field")

        # Extract parameters (everything except 'type')
        params = {k: v for k, v in config.items() if k != "type"}

        return self.create(engine_type, **params)

    def get_engine_info(self, name: str) -> dict[str, Any] | None:
        """
        Get information about an engine type.

        Args:
            name: Engine type name

        Returns:
            Dictionary with engine info or None if not found
        """
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


# =============================================================================
# Global instance and convenience functions
# =============================================================================

_registry = DetectionEngineRegistry()


def get_detection_registry() -> DetectionEngineRegistry:
    """Get the global detection engine registry."""
    return _registry


def create_detection_engine(
    name: str = "uniform",
    **kwargs: Any,
) -> BaseDetectionEngine:
    """
    Create a detection engine (convenience function).

    Args:
        name: Engine type name (default: "uniform")
        **kwargs: Engine parameters

    Returns:
        Configured detection engine
    """
    return _registry.create(name, **kwargs)


def list_detection_engines() -> list[str]:
    """List available detection engine types."""
    return _registry.get_available()
