import math
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

class NetworkVisualizer:
    def __init__(self, network):
        self.network = network
        self.node_positions = {}
        self._initialize_positions()

    def _initialize_positions(self):
        num_nodes = len(self.network.nodes)
        radius = 5
        for i, node_id in enumerate(self.network.nodes):
            angle = 2 * math.pi * i / num_nodes
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            self.node_positions[node_id] = (x, y)

    def _draw_network(self):
        plt.clf()
        ax = plt.gca()
        ax.set_aspect('equal', adjustable='datalim')
        ax.set_xlim(-6, 6)
        ax.set_ylim(-6, 6)

        for link in self.network.links:
            node1_pos = self.node_positions[link.node1.id]
            node2_pos = self.node_positions[link.node2.id]
            ax.plot(
                [node1_pos[0], node2_pos[0]],
                [node1_pos[1], node2_pos[1]],
                color='gray', linestyle='-', linewidth=1
            )

        for node_id, position in self.node_positions.items():
            ax.scatter(position[0], position[1], color='lightblue', s=200, zorder=2)
            ax.text(
                position[0], position[1], node_id,
                fontsize=10, ha='center', va='center', zorder=3
            )

    def _update(self, frame):
        self._draw_network()

    def visualize(self):
        fig, ax = plt.subplots(figsize=(8, 6))
        ani = FuncAnimation(fig, self._update, interval=1000)
        plt.show()