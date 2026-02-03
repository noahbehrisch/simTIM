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
        self.repaired = False
        self.links: list[Link] = []
        self.access: dict[str, NodeAccessLevel] = {}
        self.properties: dict[str, Any] = {}
        self.exposed_services: list[str] = []
        self.services: dict[str, str] = {}
        self.capabilities: list[str] = []
        self.exposed_to_internet: bool = False

    def add_link(self, link: "Link") -> None:
        self.links.append(link)

    def get_software(self, key, default=None):
        return self.software.get(key, default)

    def get_vulnerability(self, vuln):
        return vuln in self.vulnerabilities

    def get_asset(self, asset):
        return asset in self.assets

    def get_property(self, key, default=None):
        return self.properties.get(key, default)

    def __repr__(self) -> str:
        return f"Node(id={self.id}, compromised={self.compromised}, assets={len(self.assets)}, vulnerabilities={len(self.vulnerabilities)}, links={len(self.links)})"


class Link:
    def __init__(self, node1: Node, node2: Node, bidirectional: bool = True, latency: float = 0.0):
        self.node1 = node1
        self.node2 = node2
        self.bidirectional = bidirectional
        self.latency = latency
        self.access: dict[str, LinkAccessLevel] = {}
        node1.add_link(self)
        if bidirectional:
            node2.add_link(self)

    def get_latency(self):
        return self.latency

    def get_nodes(self):
        return (self.node1, self.node2)

    def get_other_node(self, node):
        if node == self.node1:
            return self.node2
        elif node == self.node2:
            return self.node1
        else:
            return None

    def __repr__(self) -> str:
        direction = "<->" if self.bidirectional else "->"
        return f"Link({self.node1.id} {direction} {self.node2.id})"
