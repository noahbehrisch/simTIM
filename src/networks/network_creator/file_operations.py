import json
import math
from tkinter import filedialog


class FileOperations:
    def save_network(self):
        if not self.nodes:
            self.status_label.config(
                text="No network to save. Add nodes first.", bg="#f8d7da", fg="#721c24"
            )
            return
        self.lift()
        self.focus_force()
        filename = filedialog.asksaveasfilename(
            parent=self,
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialdir="src/networks/library",
        )
        if filename:
            network_data = {
                "name": "Custom Network",
                "description": f"Custom network with {len(self.nodes)} nodes and {len(self.links)} links",
                "nodes": [],
                "links": [],
            }
            for _node_id, node in self.nodes.items():
                network_data["nodes"].append(
                    {
                        "id": node["id"],
                        "name": node["name"],
                        "x": node["x"],
                        "y": node["y"],
                        "software": node["software"],
                        "assets": node.get("assets", []),
                        "properties": node["properties"],
                    }
                )
            for link in self.links:
                network_data["links"].append(
                    {
                        "node1": link["node1"],
                        "node2": link["node2"],
                        "bidirectional": link["bidirectional"],
                    }
                )
            try:
                with open(filename, "w") as f:
                    json.dump(network_data, f, indent=2)
                self.status_label.config(
                    text=f"Network saved to {filename}", bg="#d4edda", fg="#155724"
                )
            except Exception as e:
                self.status_label.config(
                    text=f"Error saving network: {str(e)}", bg="#f8d7da", fg="#721c24"
                )

    def load_network(self):
        self.lift()
        self.focus_force()
        filename = filedialog.askopenfilename(
            parent=self,
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialdir="src/networks/library",
        )
        if filename:
            try:
                with open(filename) as f:
                    data = json.load(f)
                self.nodes = {}
                self.links = []
                for i, node in enumerate(data.get("nodes", [])):
                    node_id = node["id"]
                    # Use saved coordinates if available, otherwise calculate circular layout
                    if "x" in node and "y" in node:
                        x = node["x"]
                        y = node["y"]
                    else:
                        angle = 2 * math.pi * i / len(data["nodes"])
                        x = 400 + 200 * math.cos(angle)
                        y = 300 + 200 * math.sin(angle)
                    self.nodes[node_id] = {
                        "id": node_id,
                        "name": node.get("name", node_id),
                        "x": int(x),
                        "y": int(y),
                        "software": node.get("software", {}),
                        "assets": node.get("assets", []),
                        "properties": node.get("properties", {}),
                    }
                for link in data.get("links", []):
                    self.links.append(
                        {
                            "node1": link["node1"],
                            "node2": link["node2"],
                            "bidirectional": link.get("bidirectional", True),
                        }
                    )
                self.draw_network()
                self.update_properties_display()
                self.update_button_states()
                self.status_label.config(
                    text=f"Network loaded from {filename}", bg="#d4edda", fg="#155724"
                )
            except Exception as e:
                self.status_label.config(
                    text=f"Failed to load network: {str(e)}", bg="#f8d7da", fg="#721c24"
                )
