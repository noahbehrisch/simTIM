"""
Networks module.

Provides network loading, validation, and creation functionality.

Main Classes:
- Network: Typed container for network topology (from core.network)
- NetworkValidator: Validates network configurations
- NetworkFactory: Creates Network objects from configs
- NetworkLoader: Handles file I/O for networks

Global Instance:
- network_loader: Pre-configured NetworkLoader instance
"""

from src.core.network import Network
from src.networks.factory import (
    NetworkCreationError,
    NetworkFactory,
)
from src.networks.network_loader import (
    NetworkLoader,
    NetworkLoadError,
    network_loader,
)
from src.networks.validation import (
    NetworkValidationResult,
    NetworkValidator,
)

__all__ = [
    # Core class
    "Network",
    # Validator
    "NetworkValidationResult",
    "NetworkValidator",
    # Factory
    "NetworkFactory",
    "NetworkCreationError",
    # Loader
    "NetworkLoader",
    "NetworkLoadError",
    "network_loader",
]
