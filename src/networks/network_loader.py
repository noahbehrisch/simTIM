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
    def __init__(self, message: str, path: str | None = None, cause: Exception | None = None):
        self.path = path
        self.cause = cause
        super().__init__(message)


class NetworkLoader:
    DEFAULT_LIBRARY_PATH = os.path.join(os.path.dirname(__file__), "library")

    def __init__(
        self,
        factory: NetworkFactory | None = None,
        library_path: str | None = None,
    ):
        self._factory = factory or NetworkFactory()
        self._library_path = library_path or self.DEFAULT_LIBRARY_PATH

    @property
    def factory(self) -> NetworkFactory:
        return self._factory

    @property
    def validator(self) -> NetworkValidator:
        return self._factory.validator

    @property
    def library_path(self) -> str:
        return self._library_path

    def list_available(self) -> list[str]:
        if not os.path.exists(self._library_path):
            return []
        json_files = glob.glob(os.path.join(self._library_path, "*.json"))
        return [os.path.basename(f) for f in json_files]

    def resolve_path(self, path: str) -> str:
        if os.path.sep in path or os.path.isabs(path):
            return path

        try:
            return self.find_in_library(path)
        except FileNotFoundError:
            return path

    def find_in_library(self, filename: str) -> str:
        if not filename.endswith(".json"):
            filename += ".json"

        full_path = os.path.join(self._library_path, filename)
        if os.path.exists(full_path):
            return full_path
        raise FileNotFoundError(f"Network file '{filename}' not found in {self._library_path}")

    def load_config(self, path: str, validate: bool = True) -> dict[str, Any]:
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
        config = self.load_config(path, validate=False)
        network = self._factory.create(config, validate=True)
        network.metadata["source_file"] = self.resolve_path(path)
        return network

    def save(self, network: Network, path: str) -> None:
        config = self._factory.to_config(network)

        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

        with open(path, "w") as f:
            json.dump(config, f, indent=2)

        logger.info(f"Saved network to {path}")

    def save_to_library(self, network: Network, filename: str) -> str:
        if not filename.endswith(".json"):
            filename += ".json"

        full_path = os.path.join(self._library_path, filename)
        self.save(network, full_path)
        return full_path


network_loader = NetworkLoader()
