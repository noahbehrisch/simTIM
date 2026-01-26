"""
Network loading module.

Handles file I/O for network configurations. Uses NetworkValidator and
NetworkFactory for validation and creation.
"""

import glob
import json
import logging
import os
from typing import Any

from src.core.network import Network
from src.networks.factory import NetworkFactory
from src.networks.validation import NetworkValidator

logger = logging.getLogger(__name__)


class NetworkLoadError(Exception):
    """Raised when network loading fails."""

    def __init__(self, message: str, path: str | None = None, cause: Exception | None = None):
        self.path = path
        self.cause = cause
        super().__init__(message)


class NetworkLoader:
    """
    Handles loading and saving network configurations.

    Responsibilities:
    - File I/O operations
    - Path resolution (library vs absolute)
    - JSON parsing

    Does NOT handle:
    - Validation (see NetworkValidator)
    - Network creation (see NetworkFactory)
    """

    DEFAULT_LIBRARY_PATH = os.path.join(os.path.dirname(__file__), "library")

    def __init__(
        self,
        factory: NetworkFactory | None = None,
        library_path: str | None = None,
    ):
        """
        Initialize the loader.

        Args:
            factory: Optional NetworkFactory instance
            library_path: Optional custom library path
        """
        self._factory = factory or NetworkFactory()
        self._library_path = library_path or self.DEFAULT_LIBRARY_PATH

    @property
    def factory(self) -> NetworkFactory:
        """Get the factory instance."""
        return self._factory

    @property
    def validator(self) -> NetworkValidator:
        """Get the validator instance (from factory)."""
        return self._factory.validator

    @property
    def library_path(self) -> str:
        """Get the network library path."""
        return self._library_path

    def list_available(self) -> list[str]:
        """
        List available networks in the library.

        Returns:
            List of network filenames
        """
        if not os.path.exists(self._library_path):
            return []
        json_files = glob.glob(os.path.join(self._library_path, "*.json"))
        return [os.path.basename(f) for f in json_files]

    def resolve_path(self, path: str) -> str:
        """
        Resolve a network path.

        If path contains separators or is absolute, returns as-is.
        Otherwise, tries to find in library.

        Args:
            path: Path or filename to resolve

        Returns:
            Resolved absolute path
        """
        if os.path.sep in path or os.path.isabs(path):
            return path

        # Try library
        try:
            return self.find_in_library(path)
        except FileNotFoundError:
            return path

    def find_in_library(self, filename: str) -> str:
        """
        Find a network file in the library.

        Args:
            filename: Network filename (with or without .json)

        Returns:
            Full path to the network file

        Raises:
            FileNotFoundError: If file not found in library
        """
        if not filename.endswith(".json"):
            filename += ".json"

        full_path = os.path.join(self._library_path, filename)
        if os.path.exists(full_path):
            return full_path
        raise FileNotFoundError(f"Network file '{filename}' not found in {self._library_path}")

    def load_config(self, path: str, validate: bool = True) -> dict[str, Any]:
        """
        Load network configuration from file.

        Args:
            path: Path to network file (can be library name or full path)
            validate: Whether to validate the configuration

        Returns:
            Network configuration dictionary

        Raises:
            NetworkLoadError: If loading or validation fails
        """
        resolved_path = self.resolve_path(path)

        if not os.path.exists(resolved_path):
            raise NetworkLoadError(
                f"Network file not found: {resolved_path}",
                path=resolved_path,
            )

        try:
            with open(resolved_path) as f:
                if resolved_path.endswith(".json"):
                    config = json.load(f)
                else:
                    raise NetworkLoadError(
                        "Unsupported file format. Only .json files are supported",
                        path=resolved_path,
                    )
        except json.JSONDecodeError as e:
            raise NetworkLoadError(
                f"Invalid JSON in {resolved_path}: {e}",
                path=resolved_path,
                cause=e,
            ) from e

        if validate:
            result = self.validator.validate(config)
            if not result.valid:
                error_msg = "Network configuration validation failed:\n"
                error_msg += "\n".join(f"  - {err}" for err in result.errors)
                logger.error(error_msg)
                raise NetworkLoadError(error_msg, path=resolved_path)

            for warning in result.warnings:
                logger.warning(f"Network config warning: {warning}")

        return config

    def load(self, path: str) -> Network:
        """
        Load and create a Network from file.

        Args:
            path: Path to network file

        Returns:
            Configured Network instance

        Raises:
            NetworkLoadError: If loading fails
            NetworkCreationError: If network creation fails
        """
        config = self.load_config(path, validate=False)
        network = self._factory.create(config, validate=True)
        network.metadata["source_file"] = self.resolve_path(path)
        return network

    def save(self, network: Network, path: str) -> None:
        """
        Save a network to file.

        Args:
            network: Network to save
            path: Output file path
        """
        config = self._factory.to_config(network)

        # Ensure directory exists
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

        with open(path, "w") as f:
            json.dump(config, f, indent=2)

        logger.info(f"Saved network to {path}")

    def save_to_library(self, network: Network, filename: str) -> str:
        """
        Save a network to the library.

        Args:
            network: Network to save
            filename: Filename (with or without .json)

        Returns:
            Full path to saved file
        """
        if not filename.endswith(".json"):
            filename += ".json"

        full_path = os.path.join(self._library_path, filename)
        self.save(network, full_path)
        return full_path


# =============================================================================
# Global Instance
# =============================================================================

network_loader = NetworkLoader()
