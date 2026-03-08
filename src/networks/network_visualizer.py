import math

import matplotlib.pyplot as plt

from src.visualization.theme import get_theme


class NetworkVisualizer:
    def __init__(self, network):
        self.network = network
        self.node_positions = {}
        theme = get_theme()
        network_colors = theme.get_network_colors()
        self.COLOR_EXPOSED = network_colors["exposed"]
        self.COLOR_INTERNAL = network_colors["internal"]
        self.COLOR_LINK = network_colors["link"]
        self._initialize_positions()

    def _initialize_positions(self):
        num_nodes = len(self.network.nodes)
        if num_nodes == 0:
            return

        radius = 5
        for i, node_id in enumerate(self.network.nodes):
            node = self.network.nodes[node_id]
            x = node.properties.get("x")
            y = node.properties.get("y")

            if x is not None and y is not None:
                self.node_positions[node_id] = (x / 50, y / 50)
            else:
                angle = 2 * math.pi * i / num_nodes
                self.node_positions[node_id] = (
                    radius * math.cos(angle),
                    radius * math.sin(angle),
                )

    def _get_node_color(self, node_id):
        node = self.network.nodes[node_id]
        exposed = node.exposed_to_internet or node.properties.get("exposed_to_internet", False)
        return self.COLOR_EXPOSED if exposed else self.COLOR_INTERNAL

    def _draw_network(self, ax=None):
        if ax is None:
            ax = plt.gca()

        ax.clear()
        ax.set_aspect("equal", adjustable="datalim")

        if not self.node_positions:
            ax.text(0.5, 0.5, "No nodes to display", ha="center", va="center")
            return

        all_x = [pos[0] for pos in self.node_positions.values()]
        all_y = [pos[1] for pos in self.node_positions.values()]
        margin = 1.5
        ax.set_xlim(min(all_x) - margin, max(all_x) + margin)
        ax.set_ylim(min(all_y) - margin, max(all_y) + margin)

        for link in self.network.links:
            node1_pos = self.node_positions.get(link.node1.id)
            node2_pos = self.node_positions.get(link.node2.id)
            if node1_pos and node2_pos:
                ax.plot(
                    [node1_pos[0], node2_pos[0]],
                    [node1_pos[1], node2_pos[1]],
                    color=self.COLOR_LINK,
                    linestyle="-",
                    linewidth=2,
                    zorder=1,
                )

        for node_id, position in self.node_positions.items():
            color = self._get_node_color(node_id)
            ax.scatter(
                position[0],
                position[1],
                color=color,
                s=400,
                zorder=2,
                edgecolors="black",
                linewidths=1.5,
            )
            ax.text(
                position[0],
                position[1],
                node_id[:10],
                fontsize=8,
                ha="center",
                va="center",
                zorder=3,
                fontweight="bold",
            )

        ax.set_xticks([])
        ax.set_yticks([])
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["bottom"].set_visible(False)
        ax.spines["left"].set_visible(False)

    def visualize(self):
        fig, ax = plt.subplots(figsize=(10, 8))
        fig.suptitle("Network Topology", fontsize=14, fontweight="bold")
        self._draw_network(ax)

        from matplotlib.patches import Patch

        legend_elements = [
            Patch(facecolor=self.COLOR_EXPOSED, edgecolor="black", label="Exposed to Internet"),
            Patch(facecolor=self.COLOR_INTERNAL, edgecolor="black", label="Internal"),
        ]
        ax.legend(handles=legend_elements, loc="upper right")

        plt.tight_layout()
        plt.show()

    def update_plot(self):
        plt.clf()
        self.visualize()
