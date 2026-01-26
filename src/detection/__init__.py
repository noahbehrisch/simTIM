"""
Detection module.

Provides detection engines for calculating when attacker actions are detected.

Main Classes:
- BaseDetectionEngine: Abstract base class for detection engines
- UniformDetectionEngine: Uniform distribution detection timing
- ExponentialDetectionEngine: Exponential distribution (early detection bias)
- LinearDetectionEngine: Power-law distribution (configurable bias)
- DetectionEngineRegistry: Registry for engine types

Convenience Functions:
- create_detection_engine(): Create engine by type name
- list_detection_engines(): List available engine types
- get_detection_registry(): Get the global registry
"""

from .base_detection import BaseDetectionEngine
from .exponential_detection import ExponentialDetectionEngine
from .linear_detection import LinearDetectionEngine
from .registry import (
    DetectionEngineError,
    DetectionEngineRegistry,
    create_detection_engine,
    get_detection_registry,
    list_detection_engines,
)
from .uniform_detection import UniformDetectionEngine

__all__ = [
    # Base class
    "BaseDetectionEngine",
    # Engine implementations
    "UniformDetectionEngine",
    "ExponentialDetectionEngine",
    "LinearDetectionEngine",
    # Registry
    "DetectionEngineRegistry",
    "DetectionEngineError",
    # Convenience functions
    "create_detection_engine",
    "list_detection_engines",
    "get_detection_registry",
]
