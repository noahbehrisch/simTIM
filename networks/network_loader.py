import os
import json
import glob
from simulator.graph import Node, Link
from typing import List, Dict


def get_network_library_path() -> str:
    """Get the path to the network library folder."""
    return os.path.join(os.path.dirname(__file__), 'library')


def find_network_file(filename: str) -> str:
    """Find a network file in the library folder. Supports both with and without .json extension."""
    if not filename.endswith('.json'):
        filename += '.json'
    
    library_path = get_network_library_path()
    full_path = os.path.join(library_path, filename)
    
    if os.path.exists(full_path):
        return full_path
    else:
        raise FileNotFoundError(f"Network file '{filename}' not found in {library_path}")


def list_available_networks() -> List[str]:
    """List all available network files in the library folder."""
    library_path = get_network_library_path()
    if not os.path.exists(library_path):
        return []
    
    json_files = glob.glob(os.path.join(library_path, "*.json"))
    return [os.path.basename(f) for f in json_files]


def resolve_network_path(path: str) -> str:
    """Resolve a network path. If it's just a filename, look in the library folder."""
    # If it's already an absolute path or relative path with directory, use as-is
    if os.path.sep in path or os.path.isabs(path):
        return path
    
    # Otherwise, try to find it in the library folder
    try:
        return find_network_file(path)
    except FileNotFoundError:
        # If not found in library, return original path (might be relative to cwd)
        return path


# TODO: reevaluate need -> graph.py.load_from_json
def load_network_config(path: str) -> dict:
    resolved_path = resolve_network_path(path)
    with open(resolved_path, 'r') as f:
        if resolved_path.endswith('.json'):
            return json.load(f)
        raise ValueError('Only json files')
    

# TODO: rework, add error handling
def create_network_from_config(config: dict) -> Dict[str, Node]:
    nodes = {}
    for node_config in config.get('nodes', []):
        node = Node(
            id=node_config['id'],
            software=node_config.get('software', {}),
            vulnerabilities=node_config.get('vulnerabilities', []),
            assets=node_config.get('assets', [])
        )
        
        # Load node properties including internet exposure
        properties = node_config.get('properties', {})
        node.properties.update(properties)
        
        # Set internet exposure flag for access control
        node.exposed_to_internet = properties.get('exposed_to_internet', False)
        
        # Load exposed services for network checks
        node.exposed_services = node_config.get('exposed_services', 
                                               properties.get('exposed_services', []))
        
        nodes[node.id] = node
    for link_config in config.get('links', []):
        node1 = nodes[link_config['node1']]
        node2 = nodes[link_config['node2']]
        Link(
            node1=node1,
            node2=node2,
            bidirectional=link_config.get('bidirectional', True),
            latency=link_config.get('latency', 0.0)
        )
    return nodes

