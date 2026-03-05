import math
import random
import tkinter as tk
from tkinter import messagebox


class NetworkGenerator:
    def generate_scale_free_network(self, num_nodes, exposed_percent):
        self.nodes = {}
        self.links = []
        initial_nodes = min(3, num_nodes)
        edges_per_node = min(2, initial_nodes)
        os_list = self.load_operating_systems()
        services = self.load_services()
        assets = self.load_assets()
        categories = self.load_categories()
        width, height = (800, 600)
        radius = 250
        for i in range(num_nodes):
            angle = 2 * math.pi * i / num_nodes
            x = width / 2 + radius * math.cos(angle)
            y = height / 2 + radius * math.sin(angle)
            chosen_os = random.choice(os_list) if os_list else "Linux"
            os_data = self.load_os_data(chosen_os)
            versions = os_data.get("versions", [])
            if versions:
                chosen_version_data = random.choice(versions)
                chosen_version = chosen_version_data["version"]
            else:
                chosen_version = "1.0"
            num_services = random.randint(1, min(4, len(services))) if services else 0
            chosen_services = random.sample(services, num_services) if num_services > 0 else []
            num_assets = random.randint(0, min(2, len(assets))) if assets else 0
            chosen_assets = random.sample(assets, num_assets) if num_assets > 0 else []
            chosen_category = random.choice(categories) if categories else "Server"
            node_id = f"node_{i + 1}"
            self.nodes[node_id] = {
                "id": node_id,
                "name": f"Node {i + 1}",
                "x": int(x),
                "y": int(y),
                "software": {
                    "os": chosen_os,
                    "version": chosen_version,
                    "services": chosen_services,
                },
                "assets": chosen_assets,
                "category": chosen_category,
                "properties": {"exposed_to_internet": False},
            }
        for i in range(initial_nodes):
            for j in range(i + 1, initial_nodes):
                self.links.append(
                    {
                        "node1": f"node_{i + 1}",
                        "node2": f"node_{j + 1}",
                        "bidirectional": True,
                    }
                )
        node_degrees = {f"node_{i + 1}": 0 for i in range(num_nodes)}
        for link in self.links:
            node_degrees[link["node1"]] += 1
            node_degrees[link["node2"]] += 1
        for i in range(initial_nodes, num_nodes):
            node_id = f"node_{i + 1}"
            total_degree = sum(node_degrees.values())
            targets = []
            for _ in range(min(edges_per_node, len(self.nodes) - 1)):
                if total_degree == 0:
                    target = random.choice(
                        [n for n in node_degrees.keys() if n != node_id and n not in targets]
                    )
                else:
                    r = random.uniform(0, total_degree)
                    cumsum = 0
                    target = None
                    for nid, degree in node_degrees.items():
                        if nid != node_id and nid not in targets:
                            cumsum += degree
                            if cumsum >= r:
                                target = nid
                                break
                    if target is None:
                        available = [
                            n for n in node_degrees.keys() if n != node_id and n not in targets
                        ]
                        if available:
                            target = random.choice(available)
                if target:
                    targets.append(target)
                    self.links.append({"node1": node_id, "node2": target, "bidirectional": True})
                    node_degrees[node_id] += 1
                    node_degrees[target] += 1
                    total_degree += 2
        num_exposed = max(1, int(num_nodes * exposed_percent / 100))
        exposed_nodes = random.sample(list(self.nodes.keys()), num_exposed)
        for node_id in exposed_nodes:
            self.nodes[node_id]["properties"]["exposed_to_internet"] = True
        self.draw_network()
        self.update_properties_display()
        self.update_button_states()
        self.status_label.config(
            text=f"Network generated: {num_nodes} nodes, {len(self.links)} links (Barabási-Albert model, m={edges_per_node})",
            bg=self.theme.COLORS["bg_sidebar"],
            fg=self.theme.COLORS["text_primary"],
        )

    def generate_random_network(self, num_nodes, exposed_percent, connection_probability):
        self.nodes = {}
        self.links = []
        os_list = self.load_operating_systems()
        services = self.load_services()
        assets = self.load_assets()
        categories = self.load_categories()
        width, height = (800, 600)
        radius = 250
        for i in range(num_nodes):
            angle = 2 * math.pi * i / num_nodes
            x = width / 2 + radius * math.cos(angle)
            y = height / 2 + radius * math.sin(angle)
            chosen_os = random.choice(os_list) if os_list else "Linux"
            os_data = self.load_os_data(chosen_os)
            versions = os_data.get("versions", [])
            if versions:
                chosen_version_data = random.choice(versions)
                chosen_version = chosen_version_data["version"]
            else:
                chosen_version = "1.0"
            num_services = random.randint(1, min(4, len(services))) if services else 0
            chosen_services = random.sample(services, num_services) if num_services > 0 else []
            num_assets = random.randint(0, min(2, len(assets))) if assets else 0
            chosen_assets = random.sample(assets, num_assets) if num_assets > 0 else []
            chosen_category = random.choice(categories) if categories else "Server"
            node_id = f"node_{i + 1}"
            self.nodes[node_id] = {
                "id": node_id,
                "name": f"Node {i + 1}",
                "x": int(x),
                "y": int(y),
                "software": {
                    "os": chosen_os,
                    "version": chosen_version,
                    "services": chosen_services,
                },
                "assets": chosen_assets,
                "category": chosen_category,
                "properties": {"exposed_to_internet": False},
            }
        for i in range(num_nodes):
            for j in range(i + 1, num_nodes):
                if random.random() < connection_probability:
                    self.links.append(
                        {
                            "node1": f"node_{i + 1}",
                            "node2": f"node_{j + 1}",
                            "bidirectional": True,
                        }
                    )
        num_exposed = max(1, int(num_nodes * exposed_percent / 100))
        exposed_nodes = random.sample(list(self.nodes.keys()), num_exposed)
        for node_id in exposed_nodes:
            self.nodes[node_id]["properties"]["exposed_to_internet"] = True
        self.draw_network()
        self.update_properties_display()
        self.update_button_states()
        self.status_label.config(
            text=f"Network generated: {num_nodes} nodes, {len(self.links)} links (Erdős-Rényi model, p={connection_probability:.2f})",
            bg=self.theme.COLORS["bg_sidebar"],
            fg=self.theme.COLORS["text_primary"],
        )

    def generate_random_dialog(self):
        dialog = tk.Toplevel(self)
        dialog.title("Generate Network")
        dialog.geometry("700x600")
        dialog.configure(bg=self.theme.COLORS["bg_primary"])
        dialog.transient(self)
        dialog.grab_set()
        form_frame = tk.Frame(dialog, bg=self.theme.COLORS["bg_primary"])
        form_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        form_frame.columnconfigure(1, weight=1)
        tk.Label(
            form_frame,
            text="Generate Network",
            font=self.theme.FONTS["heading_medium"],
            bg=self.theme.COLORS["bg_primary"],
            fg=self.theme.COLORS["text_primary"],
        ).grid(row=0, column=0, columnspan=3, pady=10)
        tk.Label(
            form_frame,
            text="Network Type:",
            bg=self.theme.COLORS["bg_primary"],
            fg=self.theme.COLORS["text_primary"],
        ).grid(row=1, column=0, sticky="w", pady=8)
        network_type_var = tk.StringVar(value="scale_free")
        type_frame = tk.Frame(form_frame, bg=self.theme.COLORS["bg_primary"])
        type_frame.grid(row=1, column=1, sticky="ew", pady=8, padx=5)
        tk.Radiobutton(
            type_frame,
            text="Scale-Free (Barabási-Albert)",
            variable=network_type_var,
            value="scale_free",
            bg=self.theme.COLORS["bg_primary"],
            fg=self.theme.COLORS["text_primary"],
            selectcolor=self.theme.COLORS["bg_secondary"],
            activebackground=self.theme.COLORS["bg_primary"],
            activeforeground=self.theme.COLORS["text_primary"],
        ).pack(anchor="w")
        tk.Radiobutton(
            type_frame,
            text="Random (Erdős-Rényi)",
            variable=network_type_var,
            value="random",
            bg=self.theme.COLORS["bg_primary"],
            fg=self.theme.COLORS["text_primary"],
            selectcolor=self.theme.COLORS["bg_secondary"],
            activebackground=self.theme.COLORS["bg_primary"],
            activeforeground=self.theme.COLORS["text_primary"],
        ).pack(anchor="w")
        help_text = tk.Label(
            form_frame,
            text="Scale-free network with preferential attachment (power-law degree distribution).",
            font=self.theme.FONTS["body_small"],
            bg=self.theme.COLORS["bg_primary"],
            fg=self.theme.COLORS["text_secondary"],
            justify=tk.LEFT,
            wraplength=600,
        )
        help_text.grid(row=2, column=0, columnspan=3, pady=5, sticky="w")

        def update_help(*args):
            if network_type_var.get() == "scale_free":
                help_text.config(
                    text="Scale-free network with preferential attachment (power-law degree distribution)."
                )
                prob_label.grid_remove()
                prob_entry.grid_remove()
            else:
                help_text.config(
                    text="Random network where each pair of nodes is connected with equal probability."
                )
                prob_label.grid(row=4, column=0, sticky="w", pady=8)
                prob_entry.grid(row=4, column=1, sticky="ew", pady=8, padx=5)

        network_type_var.trace("w", update_help)
        tk.Label(
            form_frame,
            text="Number of Nodes:",
            bg=self.theme.COLORS["bg_primary"],
            fg=self.theme.COLORS["text_primary"],
        ).grid(row=3, column=0, sticky="w", pady=8)
        num_nodes_var = tk.IntVar(value=20)
        tk.Entry(form_frame, textvariable=num_nodes_var).grid(
            row=3, column=1, sticky="ew", pady=8, padx=5
        )
        prob_label = tk.Label(
            form_frame,
            text="Connection Probability:",
            bg=self.theme.COLORS["bg_primary"],
            fg=self.theme.COLORS["text_primary"],
        )
        prob_var = tk.DoubleVar(value=0.15)
        prob_entry = tk.Entry(form_frame, textvariable=prob_var)
        tk.Label(
            form_frame,
            text="Exposed Nodes %:",
            bg=self.theme.COLORS["bg_primary"],
            fg=self.theme.COLORS["text_primary"],
        ).grid(row=5, column=0, sticky="w", pady=8)
        exposed_percent_var = tk.IntVar(value=10)
        tk.Entry(form_frame, textvariable=exposed_percent_var).grid(
            row=5, column=1, sticky="ew", pady=8, padx=5
        )

        def generate():
            try:
                num_nodes = num_nodes_var.get()
                exposed_percent = exposed_percent_var.get()
                if num_nodes < 2:
                    messagebox.showerror("Error", "Need at least 2 nodes")
                    return
                if network_type_var.get() == "scale_free":
                    self.generate_scale_free_network(num_nodes, exposed_percent)
                else:
                    connection_prob = prob_var.get()
                    if connection_prob < 0 or connection_prob > 1:
                        messagebox.showerror(
                            "Error", "Connection probability must be between 0 and 1"
                        )
                        return
                    self.generate_random_network(num_nodes, exposed_percent, connection_prob)
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to generate network: {str(e)}")

        tk.Button(
            form_frame,
            text="Generate",
            command=generate,
            bg=self.theme.COLORS["success"],
            fg="white",
            font=self.theme.FONTS["body"],
        ).grid(row=7, column=0, columnspan=3, pady=20)
