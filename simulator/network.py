class Node:
    def __init__(
        self,
        id: str,
        software: dict[str, str] | None = None,
        vulnerabilities: list[str] | None = None,
        assets: list[str] | None = None, #TODO: encryption of assets?
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

    def get(self, key, default=None):
        if hasattr(self, key):
            return getattr(self, key, default)
        return default

    def get_latency(self):
        return self.latency

    def get_nodes(self):
        return (self.node1, self.node2)

    def __repr__(self) -> str:
        direction = "<->" if self.bidirectional else "->"
        return f"Link({self.node1.id} {direction} {self.node2.id})"
