import matplotlib.pyplot as plt
from simulator.graph import Node, Link
import json

class NetworkCreator:
    def __init__(self):
        self.nodes = {}
        self.links = []
        self.figure, self.ax = plt.subplots()
        plt.ion() # Interactive mode

    def add_node(self, node_id, **attributes):
        if node_id not in self.nodes:
            node = Node(id=node_id, **attributes)
            self.nodes[node_id] = node
            self._draw_graph()

    def delete_node(self, node_id):
        if node_id in self.nodes:
            node = self.nodes[node_id]
            self.links = [link for link in self.links if link.node1 != node and link.node2 != node]
            del self.nodes[node_id]
            self._draw_graph()

    def add_link(self, node1_id, node2_id, **attributes):
        if node1_id in self.nodes and node2_id in self.nodes:
            node1 = self.nodes[node1_id]
            node2 = self.nodes[node2_id]
            link = Link(node1=node1, node2=node2, **attributes)
            self.links.append(link)
            self._draw_graph()

    def delete_link(self, node1_id, node2_id):
        self.links = [link for link in self.links if not (link.node1.id == node1_id and link.node2.id == node2_id)]
        self._draw_graph()

    def update_node_attributes(self, node_id, **attributes):
        if node_id in self.nodes:
            node = self.nodes[node_id]
            for key, value in attributes.items():
                if hasattr(node, key):
                    setattr(node, key, value)
                else:
                    node.properties[key] = value
            self._draw_graph()

    def update_link_attributes(self, node1_id, node2_id, **attributes):
        for link in self.links:
            if link.node1.id == node1_id and link.node2.id == node2_id:
                for key, value in attributes.items():
                    if hasattr(link, key):
                        setattr(link, key, value)
                break
        self._draw_graph()

    def save_to_json(self, file_path):
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
        with open(file_path, "w") as json_file:
            json.dump(graph_data, json_file, indent=4)

    def _draw_graph(self):
        self.ax.clear()
        for node in self.nodes.values():
            pos = node.properties.get('pos', (0, 0))
            self.ax.scatter(*pos, label=node.id)
            self.ax.text(*pos, node.id, fontsize=12, ha='right')

        for link in self.links:
            pos1 = link.node1.properties.get('pos', (0, 0))
            pos2 = link.node2.properties.get('pos', (0, 0))
            self.ax.plot([pos1[0], pos2[0]], [pos1[1], pos2[1]], 'k-')

        self.ax.legend()
        plt.draw()
        plt.pause(0.1)

if __name__ == "__main__":
    creator = NetworkCreator()
    creator.add_node("A", pos=(0, 0), software={"OS": "Linux"}, vulnerabilities=["vuln1"], assets=["asset1"])
    creator.add_node("B", pos=(1, 1), software={"OS": "Windows"}, vulnerabilities=["vuln2"], assets=["asset2"])
    creator.add_link("A", "B", bidirectional=True, latency=10.0)
    creator.save_to_json("graph.json")
