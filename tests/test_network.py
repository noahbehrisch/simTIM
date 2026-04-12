"""Tests for network data model (Node, Link, Network)."""

from src.core.network import Link, Network, Node

# ── Node ──────────────────────────────────────────────────────────


class TestNode:
    def test_creation_defaults(self):
        node = Node("server1")
        assert node.id == "server1"
        assert node.software == {}
        assert node.assets == []
        assert node.compromised is False
        assert node.access == {}
        assert node.properties == {}

    def test_creation_with_data(self):
        node = Node(
            id="db",
            software={"os": "Ubuntu", "db": "PostgreSQL"},
            assets=["customer_data"],
        )
        assert node.software["os"] == "Ubuntu"
        assert "customer_data" in node.assets

    def test_get_software(self):
        node = Node("n", software={"os": "Linux"})
        assert node.get_software("os") == "Linux"
        assert node.get_software("db") is None
        assert node.get_software("db", "none") == "none"

    def test_get_asset(self):
        node = Node("n", assets=["data"])
        assert node.get_asset("data") is True
        assert node.get_asset("missing") is False

    def test_get_property(self):
        node = Node("n")
        node.properties["key"] = "value"
        assert node.get_property("key") == "value"
        assert node.get_property("missing") is None
        assert node.get_property("missing", "default") == "default"

    def test_repr(self):
        node = Node("web", software={"os": "Linux"})
        r = repr(node)
        assert "web" in r

    def test_none_args_become_empty(self):
        node = Node("n", software=None, assets=None)
        assert node.software == {}
        assert node.assets == []


# ── Link ──────────────────────────────────────────────────────────


class TestLink:
    def test_bidirectional_id(self):
        n1, n2 = Node("a"), Node("b")
        link = Link(n1, n2, bidirectional=True)
        assert link.id == "a<->b"

    def test_unidirectional_id(self):
        n1, n2 = Node("a"), Node("b")
        link = Link(n1, n2, bidirectional=False)
        assert link.id == "a->b"

    def test_get_other_node(self):
        n1, n2 = Node("a"), Node("b")
        link = Link(n1, n2)
        assert link.get_other_node(n1) is n2
        assert link.get_other_node(n2) is n1

    def test_get_other_node_unknown(self):
        n1, n2, n3 = Node("a"), Node("b"), Node("c")
        link = Link(n1, n2)
        assert link.get_other_node(n3) is None

    def test_default_latency(self):
        link = Link(Node("a"), Node("b"))
        assert link.latency == 0.0

    def test_repr(self):
        link = Link(Node("a"), Node("b"), bidirectional=True)
        assert repr(link) == "a<->b"


# ── Network ───────────────────────────────────────────────────────


class TestNetwork:
    def test_empty_network(self):
        net = Network()
        assert net.node_count == 0
        assert net.link_count == 0
        assert len(net) == 0

    def test_add_node(self):
        net = Network()
        net.add_node(Node("a"))
        assert net.node_count == 1
        assert net.get_node("a") is not None

    def test_add_duplicate_node_overwrites(self):
        net = Network()
        n1 = Node("a", software={"os": "Linux"})
        n2 = Node("a", software={"os": "Windows"})
        net.add_node(n1)
        net.add_node(n2)
        assert net.node_count == 1
        assert net.get_node("a").software["os"] == "Windows"

    def test_remove_node(self):
        net = Network()
        n1, n2 = Node("a"), Node("b")
        net.add_node(n1)
        net.add_node(n2)
        net.add_link(Link(n1, n2))
        removed = net.remove_node("a")
        assert removed is n1
        assert net.node_count == 1
        assert net.link_count == 0  # link should be removed too

    def test_remove_nonexistent_node(self):
        net = Network()
        assert net.remove_node("ghost") is None

    def test_add_link(self):
        net = Network()
        n1, n2 = Node("a"), Node("b")
        net.add_node(n1)
        net.add_node(n2)
        link = Link(n1, n2)
        net.add_link(link)
        assert net.link_count == 1

    def test_add_duplicate_link_ignored(self):
        net = Network()
        n1, n2 = Node("a"), Node("b")
        link = Link(n1, n2)
        net.add_link(link)
        net.add_link(link)  # same object
        assert net.link_count == 1

    def test_remove_link(self):
        net = Network()
        n1, n2 = Node("a"), Node("b")
        link = Link(n1, n2)
        net.add_link(link)
        assert net.remove_link(link) is True
        assert net.link_count == 0

    def test_remove_nonexistent_link(self):
        net = Network()
        assert net.remove_link(Link(Node("a"), Node("b"))) is False

    def test_get_links_for_node(self):
        net = Network()
        n1, n2, n3 = Node("a"), Node("b"), Node("c")
        link1 = Link(n1, n2)
        link2 = Link(n2, n3)
        net.add_link(link1)
        net.add_link(link2)
        assert len(net.get_links_for_node("b")) == 2
        assert len(net.get_links_for_node("a")) == 1
        assert len(net.get_links_for_node("c")) == 1

    def test_get_nonexistent_node(self):
        net = Network()
        assert net.get_node("nope") is None

    def test_nodes_list_property(self):
        net = Network()
        net.add_node(Node("a"))
        net.add_node(Node("b"))
        ids = {n.id for n in net.nodes_list}
        assert ids == {"a", "b"}

    def test_repr(self):
        net = Network()
        net.add_node(Node("a"))
        assert "nodes=1" in repr(net)
