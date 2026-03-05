"""
Detection module.

Provides detection engines for calculating when attacker actions are detected.

Main Classes:
- BaseDetectionEngine: Abstract base class for detection engines
- UniformDetectionEngine: Uniform distribution detection timing
- EarlyWeightedDetectionEngine: Early-biased detection (front-loaded)
- LateWeightedDetectionEngine: Late-biased detection (back-loaded)
- DetectionEngineRegistry: Registry for engine types

Convenience Functions:
- create_detection_engine(): Create engine by type name
- list_detection_engines(): List available engine types
- get_detection_registry(): Get the global registry
"""

from .base_detection import BaseDetectionEngine
from .early_weighted_detection import EarlyWeightedDetectionEngine
from .late_weighted_detection import LateWeightedDetectionEngine
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
    "EarlyWeightedDetectionEngine",
    "LateWeightedDetectionEngine",
    # Registry
    "DetectionEngineRegistry",
    "DetectionEngineError",
    # Convenience functions
    "create_detection_engine",
    "list_detection_engines",
    "get_detection_registry",
]
