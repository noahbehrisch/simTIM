"""
Network factory module.

Creates Network objects from JSON configurations.
"""

import logging
from typing import Any

from src.core.graph import Link, Node
from src.core.network import Network
from src.networks.validation import NetworkValidator

logger = logging.getLogger(__name__)


class NetworkCreationError(Exception):
    """Raised when network creation fails."""

    def __init__(self, message: str, cause: Exception | None = None):
        self.cause = cause
        super().__init__(message)


class NetworkFactory:
    """
    Creates Network objects from configurations.

    Responsibilities:
    - Convert JSON config to Node and Link objects
    - Build Network instances
    - Serialize Networks back to JSON

    Does NOT handle:
    - File I/O (see NetworkLoader)
    - Validation (see NetworkValidator)
    """

    def __init__(self, validator: NetworkValidator | None = None):
        """
        Initialize the factory.

        Args:
            validator: Optional validator instance. Creates new if None.
        """
        self._validator = validator or NetworkValidator()

    @property
    def validator(self) -> NetworkValidator:
        """Get the validator instance."""
        return self._validator

    def create(self, config: dict[str, Any], validate: bool = True) -> Network:
        """
        Create a Network from configuration.

        Args:
            config: Dictionary containing network configuration
            validate: Whether to validate before creation (default True)

        Returns:
            Configured Network instance

        Raises:
            NetworkCreationError: If validation fails or creation encounters an error
        """
        # Validate if requested
        if validate:
            result = self._validator.validate(config)
            if not result.valid:
                error_msg = "Network configuration validation failed:\n"
                error_msg += "\n".join(f"  - {err}" for err in result.errors)
                raise NetworkCreationError(error_msg)

            # Log warnings
            for warning in result.warnings:
                logger.warning(f"Network config: {warning}")

        try:
            network = Network()

            # Create nodes
            self._create_nodes(config, network)

            # Create links
            self._create_links(config, network)

            # Store metadata
            network.metadata["source_config"] = config

            logger.info(
                f"Created network with {network.node_count} nodes and {network.link_count} links"
            )

            return network

        except NetworkCreationError:
            raise
        except Exception as e:
            raise NetworkCreationError(f"Error creating network: {e}", e) from e

    def _create_nodes(self, config: dict[str, Any], network: Network) -> None:
        """Create nodes from configuration."""
        for node_config in config.get("nodes", []):
            try:
                node = self._create_single_node(node_config)
                network.add_node(node)
                logger.debug(f"Created node: {node.id}")
            except Exception as e:
                raise NetworkCreationError(
                    f"Error creating node '{node_config.get('id', '?')}': {e}", e
                ) from e

    def _create_single_node(self, node_config: dict[str, Any]) -> Node:
        """Create a single Node from configuration."""
        node = Node(
            id=node_config["id"],
            software=node_config.get("software", {}),
            vulnerabilities=node_config.get("vulnerabilities", []),
            assets=node_config.get("assets", []),
        )

        # Set properties
        properties = node_config.get("properties", {})
        node.properties.update(properties)

        # Copy x, y coordinates if present (for visualization)
        if "x" in node_config:
            node.properties["x"] = node_config["x"]
        if "y" in node_config:
            node.properties["y"] = node_config["y"]

        # Handle special properties
        node.exposed_to_internet = properties.get("exposed_to_internet", False)
        node.exposed_services = node_config.get(
            "exposed_services", properties.get("exposed_services", [])
        )

        # Initialize access dict
        node.access = {}

        return node

    def _create_links(self, config: dict[str, Any], network: Network) -> None:
        """Create links from configuration."""
        for link_config in config.get("links", []):
            try:
                link = self._create_single_link(link_config, network)
                network.add_link(link)
                logger.debug(f"Created link: {link.node1.id} <-> {link.node2.id}")
            except Exception as e:
                raise NetworkCreationError(f"Error creating link: {e}", e) from e

    def _create_single_link(self, link_config: dict[str, Any], network: Network) -> Link:
        """Create a single Link from configuration."""
        node1_id = link_config["node1"]
        node2_id = link_config["node2"]

        node1 = network.get_node(node1_id)
        node2 = network.get_node(node2_id)

        if node1 is None:
            raise NetworkCreationError(f"Link references unknown node: {node1_id}")
        if node2 is None:
            raise NetworkCreationError(f"Link references unknown node: {node2_id}")

        link = Link(
            node1=node1,
            node2=node2,
            bidirectional=link_config.get("bidirectional", True),
            latency=link_config.get("latency", 0.0),
        )

        # Initialize access dict
        link.access = {}

        return link

    def to_config(self, network: Network) -> dict[str, Any]:
        """
        Convert a Network back to configuration format.

        Args:
            network: Network to serialize

        Returns:
            Dictionary configuration
        """
        config = {
            "nodes": [self._node_to_config(node) for node in network.nodes.values()],
            "links": [self._link_to_config(link) for link in network.links],
        }

        return config

    def _node_to_config(self, node: Node) -> dict[str, Any]:
        """Convert a Node to configuration format."""
        config = {
            "id": node.id,
            "software": dict(node.software),
            "vulnerabilities": list(node.vulnerabilities),
            "assets": list(node.assets),
            "properties": dict(node.properties),
        }

        if node.exposed_services:
            config["exposed_services"] = list(node.exposed_services)

        return config

    def _link_to_config(self, link: Link) -> dict[str, Any]:
        """Convert a Link to configuration format."""
        return {
            "node1": link.node1.id,
            "node2": link.node2.id,
            "bidirectional": link.bidirectional,
            "latency": link.latency,
        }
