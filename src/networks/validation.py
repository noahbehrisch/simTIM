"""
Network validation module.

Provides validation for network JSON configurations with detailed error reporting.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class NetworkValidationResult:
    """Result of a network validation operation."""

    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def __bool__(self) -> bool:
        return self.valid

    def merge(self, other: "NetworkValidationResult") -> "NetworkValidationResult":
        """Merge another validation result into this one."""
        return NetworkValidationResult(
            valid=self.valid and other.valid,
            errors=self.errors + other.errors,
            warnings=self.warnings + other.warnings,
        )


class NetworkValidator:
    """
    Validates network JSON configurations.

    Separates validation logic from network creation, allowing for:
    - Reusable validation rules
    - Custom validation extensions
    - Clear error reporting
    """

    def validate(self, config: dict[str, Any]) -> NetworkValidationResult:
        """
        Validate a network configuration.

        Args:
            config: Dictionary containing network configuration

        Returns:
            NetworkValidationResult with errors and warnings
        """
        result = NetworkValidationResult(valid=True)

        # Basic structure check
        if not isinstance(config, dict):
            return NetworkValidationResult(
                valid=False,
                errors=["Network configuration must be a dictionary"],
            )

        # Validate nodes
        result = result.merge(self._validate_nodes(config))

        # Validate links
        result = result.merge(self._validate_links(config))

        # Check for exposed nodes
        result = result.merge(self._validate_entry_points(config))

        return result

    def _validate_nodes(self, config: dict[str, Any]) -> NetworkValidationResult:
        """Validate the nodes section."""
        errors = []
        warnings = []

        if "nodes" not in config:
            errors.append("Missing required 'nodes' key")
            return NetworkValidationResult(valid=False, errors=errors)

        if not isinstance(config["nodes"], list):
            errors.append("'nodes' must be a list")
            return NetworkValidationResult(valid=False, errors=errors)

        if len(config["nodes"]) == 0:
            warnings.append("Network has no nodes")
            return NetworkValidationResult(valid=True, warnings=warnings)

        node_ids: set[str] = set()

        for i, node in enumerate(config["nodes"]):
            node_errors = self._validate_single_node(node, i, node_ids)
            errors.extend(node_errors)

        return NetworkValidationResult(valid=len(errors) == 0, errors=errors, warnings=warnings)

    def _validate_single_node(self, node: Any, index: int, seen_ids: set[str]) -> list[str]:
        """Validate a single node configuration."""
        errors = []

        if not isinstance(node, dict):
            errors.append(f"Node {index} must be a dictionary")
            return errors

        # Validate ID
        if "id" not in node:
            errors.append(f"Node {index} missing required 'id' field")
        elif not isinstance(node["id"], str) or not node["id"]:
            errors.append(f"Node {index} 'id' must be a non-empty string")
        else:
            if node["id"] in seen_ids:
                errors.append(f"Duplicate node ID: {node['id']}")
            seen_ids.add(node["id"])

        node_ref = node.get("id", index)

        # Validate optional fields
        if "software" in node and not isinstance(node["software"], dict):
            errors.append(f"Node {node_ref}: 'software' must be a dictionary")

        if "vulnerabilities" in node and not isinstance(node["vulnerabilities"], list):
            errors.append(f"Node {node_ref}: 'vulnerabilities' must be a list")

        if "assets" in node and not isinstance(node["assets"], list):
            errors.append(f"Node {node_ref}: 'assets' must be a list")

        if "properties" in node and not isinstance(node["properties"], dict):
            errors.append(f"Node {node_ref}: 'properties' must be a dictionary")

        if "exposed_services" in node and not isinstance(node["exposed_services"], list):
            errors.append(f"Node {node_ref}: 'exposed_services' must be a list")

        return errors

    def _validate_links(self, config: dict[str, Any]) -> NetworkValidationResult:
        """Validate the links section."""
        errors = []

        if "links" not in config:
            return NetworkValidationResult(valid=True)  # Links are optional

        if not isinstance(config["links"], list):
            return NetworkValidationResult(valid=False, errors=["'links' must be a list"])

        # Collect valid node IDs
        node_ids = {
            node["id"]
            for node in config.get("nodes", [])
            if isinstance(node, dict) and "id" in node
        }

        for i, link in enumerate(config["links"]):
            link_errors = self._validate_single_link(link, i, node_ids)
            errors.extend(link_errors)

        return NetworkValidationResult(valid=len(errors) == 0, errors=errors)

    def _validate_single_link(self, link: Any, index: int, node_ids: set[str]) -> list[str]:
        """Validate a single link configuration."""
        errors = []

        if not isinstance(link, dict):
            errors.append(f"Link {index} must be a dictionary")
            return errors

        # Validate node references
        if "node1" not in link:
            errors.append(f"Link {index} missing required 'node1' field")
        elif link["node1"] not in node_ids:
            errors.append(f"Link {index} references unknown node: {link['node1']}")

        if "node2" not in link:
            errors.append(f"Link {index} missing required 'node2' field")
        elif link["node2"] not in node_ids:
            errors.append(f"Link {index} references unknown node: {link['node2']}")

        # Validate optional fields
        if "bidirectional" in link and not isinstance(link["bidirectional"], bool):
            errors.append(f"Link {index}: 'bidirectional' must be a boolean")

        if "latency" in link:
            if not isinstance(link["latency"], (int, float)):
                errors.append(f"Link {index}: 'latency' must be a number")
            elif link["latency"] < 0:
                errors.append(f"Link {index}: 'latency' must be non-negative")

        return errors

    def _validate_entry_points(self, config: dict[str, Any]) -> NetworkValidationResult:
        """Check that the network has at least one entry point for attackers."""
        warnings = []

        has_exposed = any(
            node.get("properties", {}).get("exposed_to_internet", False)
            for node in config.get("nodes", [])
            if isinstance(node, dict)
        )

        if not has_exposed:
            warnings.append(
                "Network has no Internet-exposed nodes - attackers will have no entry points! "
                'At least one node should have "exposed_to_internet": true in its properties.'
            )

        return NetworkValidationResult(valid=True, warnings=warnings)
