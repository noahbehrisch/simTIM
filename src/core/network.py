from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.core.graph import Link, Node


@dataclass
class Network:
    nodes: dict[str, Node] = field(default_factory=dict)
    links: list[Link] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def nodes_list(self) -> list[Node]:
        return list(self.nodes.values())

    @property
    def links_list(self) -> list[Link]:
        return self.links

    def get_node(self, node_id: str) -> Node | None:
        return self.nodes.get(node_id)

    def add_node(self, node: Node) -> None:
        self.nodes[node.id] = node

    def remove_node(self, node_id: str) -> Node | None:
        node = self.nodes.pop(node_id, None)
        if node:
            self.links = [
                link for link in self.links if link.node1.id != node_id and link.node2.id != node_id
            ]
        return node

    def has_node(self, node_id: str) -> bool:
        return node_id in self.nodes

    def add_link(self, link: Link) -> None:
        if link not in self.links:
            self.links.append(link)

    def remove_link(self, link: Link) -> bool:
        if link in self.links:
            self.links.remove(link)
            return True
        return False

    def get_links_for_node(self, node_id: str) -> list[Link]:
        return [link for link in self.links if link.node1.id == node_id or link.node2.id == node_id]

    def get_exposed_nodes(self) -> list[Node]:
        return [
            node
            for node in self.nodes.values()
            if node.properties.get("exposed_to_internet", False)
        ]

    def get_compromised_nodes(self) -> list[Node]:
        return [node for node in self.nodes.values() if node.compromised]

    def get_neighbors(self, node: Node) -> list[Node]:
        neighbors = []
        for link in node.links:
            other = link.get_other_node(node)
            if other:
                neighbors.append(other)
        return neighbors

    def get_nodes_by_property(self, prop_name: str, prop_value: Any) -> list[Node]:
        return [
            node for node in self.nodes.values() if node.properties.get(prop_name) == prop_value
        ]

    def get_nodes_with_vulnerability(self, vuln: str) -> list[Node]:
        return [node for node in self.nodes.values() if vuln in node.vulnerabilities]

    def get_nodes_with_software(self, software_name: str) -> list[Node]:
        return [node for node in self.nodes.values() if software_name in node.software]

    @property
    def node_count(self) -> int:
        return len(self.nodes)

    @property
    def link_count(self) -> int:
        return len(self.links)

    def get_statistics(self) -> dict[str, Any]:
        return {
            "node_count": self.node_count,
            "link_count": self.link_count,
            "exposed_nodes": len(self.get_exposed_nodes()),
            "compromised_nodes": len(self.get_compromised_nodes()),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": self.nodes,
            "nodes_list": self.nodes_list,
            "links": self.links,
            "links_list": self.links_list,
            **self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Network:
        network = cls()

        if "nodes" in data:
            if isinstance(data["nodes"], dict):
                network.nodes = data["nodes"]
            elif isinstance(data["nodes"], list):
                for node in data["nodes"]:
                    if isinstance(node, Node):
                        network.nodes[node.id] = node

        if "links" in data:
            network.links = list(data["links"])
        elif "links_list" in data:
            network.links = list(data["links_list"])

        return network

    def __len__(self) -> int:
        return len(self.nodes)

    def __repr__(self) -> str:
        return f"Network(nodes={self.node_count}, links={self.link_count})"
