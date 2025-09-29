import json

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
        self.access: dict[str, str] = {} 
        self.properties: dict[str, any] = {}
        self.exposed_services: list[str] = []
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

        return (f"Node(id={self.id}, compromised={self.compromised}, "
                f"assets={len(self.assets)}, vulnerabilities={len(self.vulnerabilities)}, "
                f"links={len(self.links)})")
class Link:

    def __init__(
        self,
        node1: Node,
        node2: Node,
        bidirectional: bool = True,
        latency: float = 0.0,
    ):
        self.node1 = node1
        self.node2 = node2
        self.bidirectional = bidirectional
        self.latency = latency
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
class Graph:

    def __init__(self):

        self.nodes = {}
        self.links = []
    def insert_node(self, node: Node):

        if node.id not in self.nodes:
            self.nodes[node.id] = node
    def insert_link(self, link: Link):

        if link not in self.links:
            self.links.append(link)
    def remove_node(self, node: Node):

        if node.id in self.nodes:
            del self.nodes[node.id]
            self.links = [link for link in self.links if link.node1 != node and link.node2 != node]
    def remove_link(self, link: Link):

        if link in self.links:
            self.links.remove(link)
    def to_json(self, file_path):

        graph_data = {
            "nodes": [
                {
                    "id": node.id,
                    "software": node.software,
                    "vulnerabilities": node.vulnerabilities,
                    "assets": node.assets,
                    "compromised": node.compromised,
                    "repaired": node.repaired,
                    "properties": node.properties
                }
                for node in self.nodes.values()
            ],
            "links": [
                {
                    "node1": link.node1.id,
                    "node2": link.node2.id,
                    "bidirectional": link.bidirectional,
                    "latency": link.latency
                }
                for link in self.links
            ]
        }
        with open(file_path, "w") as file:
            json.dump(graph_data, file, indent=4)
    @classmethod
    def from_json(cls, file_path):

        with open(file_path, "r") as file:
            graph_data = json.load(file)
        graph = cls()
        id_to_node = {}
        for node_data in graph_data["nodes"]:
            node = Node(
                id=node_data["id"],
                software=node_data.get("software"),
                vulnerabilities=node_data.get("vulnerabilities"),
                assets=node_data.get("assets")
            )
            node.compromised = node_data.get("compromised", False)
            node.repaired = node_data.get("repaired", False)
            node.properties = node_data.get("properties", {})
            if "exposed_services" in node.properties:
                node.exposed_services = node.properties["exposed_services"]
            graph.insert_node(node)
            id_to_node[node.id] = node
        for link_data in graph_data["links"]:
            node1 = id_to_node[link_data["node1"]]
            node2 = id_to_node[link_data["node2"]]
            link = Link(
                node1=node1,
                node2=node2,
                bidirectional=link_data.get("bidirectional", True),
                latency=link_data.get("latency", 0.0)
            )
            graph.insert_link(link)
        return graph
    def __repr__(self):

        return f"Graph(nodes={len(self.nodes)}, links={len(self.links)})"