import os
import json
from simulator.graph import Node, Link
from typing import List, Dict


# TODO: reevaluate need -> graph.py.load_from_json
def load_network_config(path: str) -> dict:
    with open(path, 'r') as f:
        if path.endswith('.json'):
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
