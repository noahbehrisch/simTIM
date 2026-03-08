import logging
from typing import Any

from src.core.network import Link, Network, Node
from src.networks.validation import NetworkValidator

logger = logging.getLogger(__name__)


class NetworkCreationError(Exception):
    def __init__(self, message: str, cause: Exception | None = None):
        self.cause = cause
        super().__init__(message)


class NetworkFactory:
    def __init__(self, validator: NetworkValidator | None = None):
        self._validator = validator or NetworkValidator()

    @property
    def validator(self) -> NetworkValidator:
        return self._validator

    def create(self, config: dict[str, Any], validate: bool = True) -> Network:
        if validate:
            result = self._validator.validate(config)
            if not result.valid:
                error_msg = "Network configuration validation failed:\n"
                error_msg += "\n".join(f"  - {err}" for err in result.errors)
                raise NetworkCreationError(error_msg)

            for warning in result.warnings:
                logger.warning(f"Network config: {warning}")

        try:
            network = Network()

            self._create_nodes(config, network)

            self._create_links(config, network)

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
        node = Node(
            id=node_config["id"],
            software=node_config.get("software", {}),
            vulnerabilities=node_config.get("vulnerabilities", []),
            assets=node_config.get("assets", []),
        )

        properties = node_config.get("properties", {})
        node.properties.update(properties)

        if "x" in node_config:
            node.properties["x"] = node_config["x"]
        if "y" in node_config:
            node.properties["y"] = node_config["y"]

        node.exposed_to_internet = properties.get("exposed_to_internet", False)
        node.exposed_services = node_config.get(
            "exposed_services", properties.get("exposed_services", [])
        )

        node.access = {}

        return node

    def _create_links(self, config: dict[str, Any], network: Network) -> None:
        for link_config in config.get("links", []):
            try:
                link = self._create_single_link(link_config, network)
                network.add_link(link)
                logger.debug(f"Created link: {link.node1.id} <-> {link.node2.id}")
            except Exception as e:
                raise NetworkCreationError(f"Error creating link: {e}", e) from e

    def _create_single_link(self, link_config: dict[str, Any], network: Network) -> Link:
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

        link.access = {}

        return link

    def to_config(self, network: Network) -> dict[str, Any]:
        config = {
            "nodes": [self._node_to_config(node) for node in network.nodes.values()],
            "links": [self._link_to_config(link) for link in network.links],
        }

        return config

    def _node_to_config(self, node: Node) -> dict[str, Any]:
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
        return {
            "node1": link.node1.id,
            "node2": link.node2.id,
            "bidirectional": link.bidirectional,
            "latency": link.latency,
        }
