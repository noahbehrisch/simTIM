from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.core.access_levels import LinkAccessLevel, NodeAccessLevel


class Node:
    def __init__(
        self,
        id: str,
        software: dict[str, str] | None = None,
        vulnerabilities: list[str] | None = None,
        assets: list[str] | None = None,
    ):
        self.id = id
        self.software = software or {}
        self.vulnerabilities = vulnerabilities or []
        self.assets = assets or []
        self.compromised = False
        self.access: dict[str, NodeAccessLevel] = {}
        self.properties: dict[str, Any] = {}
        self.exposed_services: list[str] = []
        self.services: dict[str, str] = {}
        self.capabilities: list[str] = []
        self.exposed_to_internet: bool = False

    def get_software(self, key: str, default: str | None = None) -> str | None:
        return self.software.get(key, default)

    def get_vulnerability(self, vuln: str) -> bool:
        return vuln in self.vulnerabilities

    def get_asset(self, asset: str) -> bool:
        return asset in self.assets

    def get_property(self, key: str, default: Any = None) -> Any:
        return self.properties.get(key, default)

    def __repr__(self) -> str:
        return f"Node(id={self.id}, compromised={self.compromised}, assets={len(self.assets)}, vulnerabilities={len(self.vulnerabilities)})"


class Link:
    def __init__(self, node1: Node, node2: Node, bidirectional: bool = True, latency: float = 0.0):
        self.node1 = node1
        self.node2 = node2
        self.bidirectional = bidirectional
        self.latency = latency
        self.access: dict[str, LinkAccessLevel] = {}

    @property
    def id(self) -> str:
        direction = "<->" if self.bidirectional else "->"
        return f"{self.node1.id}{direction}{self.node2.id}"

    def get_other_node(self, node: Node) -> Node | None:
        if self.node1.id == node.id:
            return self.node2
        elif self.node2.id == node.id:
            return self.node1
        return None

    def __repr__(self) -> str:
        direction = "<->" if self.bidirectional else "->"
        return f"{self.node1.id}{direction}{self.node2.id}"


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

    @property
    def node_count(self) -> int:
        return len(self.nodes)

    @property
    def link_count(self) -> int:
        return len(self.links)

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

    def __len__(self) -> int:
        return len(self.nodes)

    def __repr__(self) -> str:
        return f"Network(nodes={self.node_count}, links={self.link_count})"
