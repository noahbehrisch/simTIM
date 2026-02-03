from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.core.graph import Link, Node


@dataclass
class Network:
    nodes: dict[str, Node] = field(default_factory=dict)
    links: list[Link] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    # Properties
    @property
    def nodes_list(self) -> list[Node]:
        return list(self.nodes.values())

    @property
    def links_list(self) -> list[Link]:
        return self.links

    @property
    def node_count(self) -> int:
        return len(self.nodes)

    @property
    def link_count(self) -> int:
        return len(self.links)

    # Node functions
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

    # Link functions
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

    # Dunder methods
    def __len__(self) -> int:
        return len(self.nodes)

    def __repr__(self) -> str:
        return f"Network(nodes={self.node_count}, links={self.link_count})"
