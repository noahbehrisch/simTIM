"""
Network domain model.

Provides typed Network class to replace dict-based network passing,
improving type safety, IDE support, and code clarity.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from src.core.graph import Link, Node

if TYPE_CHECKING:
    from src.actors.actor import Actor


@dataclass
class Network:
    """
    Typed container for network topology and state.

    Replaces the dict-based network passing used throughout the codebase,
    providing:
    - Type safety and IDE autocomplete
    - Clear interface contract
    - Domain methods for common operations
    - Easier refactoring and maintenance
    """

    nodes: dict[str, Node] = field(default_factory=dict)
    links: list[Link] = field(default_factory=list)
    actors: list[Actor] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    # =========================================================================
    # Node Operations
    # =========================================================================

    @property
    def nodes_list(self) -> list[Node]:
        """Get all nodes as a list."""
        return list(self.nodes.values())

    @property
    def links_list(self) -> list[Link]:
        """Get all links as a list."""
        return self.links

    def get_node(self, node_id: str) -> Node | None:
        """Get a node by ID."""
        return self.nodes.get(node_id)

    def add_node(self, node: Node) -> None:
        """Add a node to the network."""
        self.nodes[node.id] = node

    def remove_node(self, node_id: str) -> Node | None:
        """Remove a node and its links."""
        node = self.nodes.pop(node_id, None)
        if node:
            # Remove links involving this node
            self.links = [
                link for link in self.links if link.node1.id != node_id and link.node2.id != node_id
            ]
        return node

    def has_node(self, node_id: str) -> bool:
        """Check if a node exists."""
        return node_id in self.nodes

    # =========================================================================
    # Link Operations
    # =========================================================================

    def add_link(self, link: Link) -> None:
        """Add a link to the network."""
        if link not in self.links:
            self.links.append(link)

    def remove_link(self, link: Link) -> bool:
        """Remove a link from the network."""
        if link in self.links:
            self.links.remove(link)
            return True
        return False

    def get_links_for_node(self, node_id: str) -> list[Link]:
        """Get all links connected to a node."""
        return [link for link in self.links if link.node1.id == node_id or link.node2.id == node_id]

    # =========================================================================
    # Actor Operations
    # =========================================================================

    def add_actor(self, actor: Actor) -> None:
        """Add an actor to the network."""
        self.actors.append(actor)

    def get_actor(self, actor_id: str) -> Actor | None:
        """Get an actor by ID."""
        for actor in self.actors:
            if actor.id == actor_id:
                return actor
        return None

    def get_attackers(self) -> list[Actor]:
        """Get all attacker actors."""
        return [a for a in self.actors if getattr(a, "is_attacker", False)]

    def get_defenders(self) -> list[Actor]:
        """Get all defender actors."""
        return [a for a in self.actors if getattr(a, "is_defender", False)]

    # =========================================================================
    # Query Operations
    # =========================================================================

    def get_exposed_nodes(self) -> list[Node]:
        """Get all nodes exposed to the internet."""
        return [
            node
            for node in self.nodes.values()
            if node.properties.get("exposed_to_internet", False)
        ]

    def get_compromised_nodes(self) -> list[Node]:
        """Get all compromised nodes."""
        return [node for node in self.nodes.values() if node.compromised]

    def get_neighbors(self, node: Node) -> list[Node]:
        """Get all nodes directly connected to a node."""
        neighbors = []
        for link in node.links:
            other = link.get_other_node(node)
            if other:
                neighbors.append(other)
        return neighbors

    def get_nodes_by_property(self, prop_name: str, prop_value: Any) -> list[Node]:
        """Get all nodes with a specific property value."""
        return [
            node for node in self.nodes.values() if node.properties.get(prop_name) == prop_value
        ]

    def get_nodes_with_vulnerability(self, vuln: str) -> list[Node]:
        """Get all nodes with a specific vulnerability."""
        return [node for node in self.nodes.values() if vuln in node.vulnerabilities]

    def get_nodes_with_software(self, software_name: str) -> list[Node]:
        """Get all nodes running specific software."""
        return [node for node in self.nodes.values() if software_name in node.software]

    # =========================================================================
    # Statistics
    # =========================================================================

    @property
    def node_count(self) -> int:
        """Get the number of nodes."""
        return len(self.nodes)

    @property
    def link_count(self) -> int:
        """Get the number of links."""
        return len(self.links)

    @property
    def actor_count(self) -> int:
        """Get the number of actors."""
        return len(self.actors)

    def get_statistics(self) -> dict[str, Any]:
        """Get network statistics."""
        return {
            "node_count": self.node_count,
            "link_count": self.link_count,
            "actor_count": self.actor_count,
            "exposed_nodes": len(self.get_exposed_nodes()),
            "compromised_nodes": len(self.get_compromised_nodes()),
            "attacker_count": len(self.get_attackers()),
            "defender_count": len(self.get_defenders()),
        }

    # =========================================================================
    # Serialization Methods
    # =========================================================================

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary format for serialization."""
        return {
            "nodes": self.nodes,
            "nodes_list": self.nodes_list,
            "links": self.links,
            "links_list": self.links_list,
            "actors": self.actors,
            **self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Network:
        """Create Network from dictionary format."""
        network = cls()

        # Handle nodes
        if "nodes" in data:
            if isinstance(data["nodes"], dict):
                network.nodes = data["nodes"]
            elif isinstance(data["nodes"], list):
                for node in data["nodes"]:
                    if isinstance(node, Node):
                        network.nodes[node.id] = node

        # Handle links
        if "links" in data:
            network.links = list(data["links"])
        elif "links_list" in data:
            network.links = list(data["links_list"])

        # Handle actors
        if "actors" in data:
            network.actors = list(data["actors"])

        return network

    # =========================================================================
    # Standard Python Interface
    # =========================================================================

    def __len__(self) -> int:
        """Return number of nodes."""
        return len(self.nodes)

    def __repr__(self) -> str:
        return (
            f"Network(nodes={self.node_count}, links={self.link_count}, actors={self.actor_count})"
        )
