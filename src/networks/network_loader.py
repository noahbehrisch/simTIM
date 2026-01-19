import os
import json
import glob
import logging
from src.core.graph import Node, Link
from typing import List, Dict

logger = logging.getLogger(__name__)


class NetworkConfigError(Exception):
    pass


def validate_network_config(config: dict) -> Dict[str, any]:
    errors = []
    warnings = []
    if not isinstance(config, dict):
        raise NetworkConfigError("Network configuration must be a dictionary")
    if "nodes" not in config:
        errors.append("Missing required 'nodes' key")
    elif not isinstance(config["nodes"], list):
        errors.append("'nodes' must be a list")
    elif len(config["nodes"]) == 0:
        warnings.append("Network has no nodes")
    node_ids = set()
    for i, node in enumerate(config.get("nodes", [])):
        if not isinstance(node, dict):
            errors.append(f"Node {i} must be a dictionary")
            continue
        if "id" not in node:
            errors.append(f"Node {i} missing required 'id' field")
        elif not isinstance(node["id"], str) or not node["id"]:
            errors.append(f"Node {i} 'id' must be a non-empty string")
        else:
            if node["id"] in node_ids:
                errors.append(f"Duplicate node ID: {node['id']}")
            node_ids.add(node["id"])
        if "software" in node and (not isinstance(node["software"], dict)):
            errors.append(f"Node {node.get('id', i)}: 'software' must be a dictionary")
        if "vulnerabilities" in node and (
            not isinstance(node["vulnerabilities"], list)
        ):
            errors.append(f"Node {node.get('id', i)}: 'vulnerabilities' must be a list")
        if "assets" in node and (not isinstance(node["assets"], list)):
            errors.append(f"Node {node.get('id', i)}: 'assets' must be a list")
        if "properties" in node and (not isinstance(node["properties"], dict)):
            errors.append(
                f"Node {node.get('id', i)}: 'properties' must be a dictionary"
            )
    if "links" in config:
        if not isinstance(config["links"], list):
            errors.append("'links' must be a list")
        else:
            for i, link in enumerate(config["links"]):
                if not isinstance(link, dict):
                    errors.append(f"Link {i} must be a dictionary")
                    continue
                if "node1" not in link:
                    errors.append(f"Link {i} missing required 'node1' field")
                elif link["node1"] not in node_ids:
                    errors.append(f"Link {i} references unknown node: {link['node1']}")
                if "node2" not in link:
                    errors.append(f"Link {i} missing required 'node2' field")
                elif link["node2"] not in node_ids:
                    errors.append(f"Link {i} references unknown node: {link['node2']}")

    has_exposed = any(
        node.get("properties", {}).get("exposed_to_internet", False)
        for node in config.get("nodes", [])
    )
    if not has_exposed:
        warnings.append(
            "Network has no Internet-exposed nodes - attackers will have no entry points! "
            'At least one node should have "exposed_to_internet": true in its properties.'
        )

    return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}


def get_network_library_path() -> str:
    return os.path.join(os.path.dirname(__file__), "library")


def find_network_file(filename: str) -> str:
    if not filename.endswith(".json"):
        filename += ".json"
    library_path = get_network_library_path()
    full_path = os.path.join(library_path, filename)
    if os.path.exists(full_path):
        return full_path
    else:
        raise FileNotFoundError(
            f"Network file '{filename}' not found in {library_path}"
        )


def list_available_networks() -> List[str]:
    library_path = get_network_library_path()
    if not os.path.exists(library_path):
        return []
    json_files = glob.glob(os.path.join(library_path, "*.json"))
    return [os.path.basename(f) for f in json_files]


def resolve_network_path(path: str) -> str:
    if os.path.sep in path or os.path.isabs(path):
        return path
    try:
        return find_network_file(path)
    except FileNotFoundError:
        return path


def load_network_config(path: str) -> dict:
    resolved_path = resolve_network_path(path)
    if not os.path.exists(resolved_path):
        raise FileNotFoundError(f"Network file not found: {resolved_path}")
    try:
        with open(resolved_path, "r") as f:
            if resolved_path.endswith(".json"):
                config = json.load(f)
            else:
                raise ValueError(
                    f"Unsupported file format. Only .json files are supported"
                )
    except json.JSONDecodeError as e:
        raise NetworkConfigError(f"Invalid JSON in {resolved_path}: {e}")
    except Exception as e:
        raise NetworkConfigError(f"Error loading network config: {e}")
    validation = validate_network_config(config)
    if not validation["valid"]:
        error_msg = "Network configuration validation failed:\n"
        error_msg += "\n".join((f"  - {err}" for err in validation["errors"]))
        logger.error(error_msg)
        raise NetworkConfigError(error_msg)
    if validation["warnings"]:
        for warning in validation["warnings"]:
            logger.warning(f"Network config warning: {warning}")
    return config


def create_network_from_config(config: dict) -> Dict[str, Node]:
    validation = validate_network_config(config)
    if not validation["valid"]:
        raise NetworkConfigError(f"Invalid configuration: {validation['errors']}")
    nodes = {}
    try:
        for node_config in config.get("nodes", []):
            node = Node(
                id=node_config["id"],
                software=node_config.get("software", {}),
                vulnerabilities=node_config.get("vulnerabilities", []),
                assets=node_config.get("assets", []),
            )
            properties = node_config.get("properties", {})
            node.properties.update(properties)
            node.exposed_to_internet = properties.get("exposed_to_internet", False)
            node.exposed_services = node_config.get(
                "exposed_services", properties.get("exposed_services", [])
            )
            node.access = {}
            nodes[node.id] = node
            logger.debug(f"Created node: {node.id}")
    except KeyError as e:
        raise NetworkConfigError(f"Missing required field in node configuration: {e}")
    except Exception as e:
        raise NetworkConfigError(f"Error creating nodes: {e}")
    try:
        for link_config in config.get("links", []):
            node1_id = link_config["node1"]
            node2_id = link_config["node2"]
            if node1_id not in nodes:
                raise NetworkConfigError(f"Link references unknown node: {node1_id}")
            if node2_id not in nodes:
                raise NetworkConfigError(f"Link references unknown node: {node2_id}")
            node1 = nodes[node1_id]
            node2 = nodes[node2_id]
            link = Link(
                node1=node1,
                node2=node2,
                bidirectional=link_config.get("bidirectional", True),
                latency=link_config.get("latency", 0.0),
            )
            link.access = {}
            logger.debug(f"Created link: {node1_id} <-> {node2_id}")
    except KeyError as e:
        raise NetworkConfigError(f"Missing required field in link configuration: {e}")
    except Exception as e:
        raise NetworkConfigError(f"Error creating links: {e}")
    logger.info(
        f"Created network with {len(nodes)} nodes and {len(config.get('links', []))} links"
    )
    return nodes
