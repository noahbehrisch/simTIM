import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from ...networks.network_creator import NetworkCreator
from .base_tab import BaseTab


class NetworkTab(BaseTab):
    def __init__(self, parent, theme_colors):
        default_network_path = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "..",
                "networks",
                "library",
                "demo_network.json",
            )
        )
        self.network_file_var = tk.StringVar(value=default_network_path)
        super().__init__(parent, theme_colors)

    def create_widgets(self):
        self.create_section_header(self.pad_frame, "Network Selection", section_type="network")
        selection_frame = tk.Frame(self.pad_frame, bg=self.tab_color)
        selection_frame.pack(fill="x", padx=10, pady=5)
        tk.Label(
            selection_frame,
            text="Select Network Source:",
            bg=self.tab_color,
            fg=self.button_fg,
            font=self.theme.FONTS["heading_medium"],
        ).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.network_source = tk.StringVar(value="library")
        tk.Radiobutton(
            selection_frame,
            text="Choose from Library",
            variable=self.network_source,
            value="library",
            bg=self.tab_color,
            fg=self.button_fg,
            selectcolor=self.theme.COLORS["input_bg"],
            command=self._on_source_change,
        ).grid(row=1, column=0, padx=20, pady=2, sticky="w")
        tk.Radiobutton(
            selection_frame,
            text="Choose from File",
            variable=self.network_source,
            value="file",
            bg=self.tab_color,
            fg=self.button_fg,
            selectcolor=self.theme.COLORS["input_bg"],
            command=self._on_source_change,
        ).grid(row=2, column=0, padx=20, pady=2, sticky="w")
        self.selection_content_frame = tk.Frame(self.pad_frame, bg=self.tab_color)
        self.selection_content_frame.pack(fill="x", padx=10, pady=5)
        self.predefined_frame = tk.Frame(self.selection_content_frame, bg=self.tab_color)
        tk.Label(
            self.predefined_frame,
            text="Select from Library:",
            bg=self.tab_color,
            fg=self.button_fg,
        ).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.predefined_var = tk.StringVar(value="demo_network.json")
        self.predefined_dropdown = ttk.Combobox(
            self.predefined_frame,
            textvariable=self.predefined_var,
            values=self._get_available_networks(),
            state="readonly",
            width=30,
        )
        self.predefined_dropdown.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        self.predefined_dropdown.bind("<<ComboboxSelected>>", self._update_network_path)
        self.create_styled_button(self.predefined_frame, "Refresh", self._refresh_networks).grid(
            row=0, column=2, padx=5, pady=5, sticky="w"
        )
        self.create_styled_button(self.predefined_frame, "Refresh", self._refresh_networks).grid(
            row=0, column=2, padx=5, pady=5, sticky="w"
        )
        descriptions_frame = tk.Frame(self.predefined_frame, bg=self.tab_color)
        descriptions_frame.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky="ew")
        self.network_descriptions = {
            "demo_network.json": "Simple 2-node network for testing and demonstrations",
            "healthcare_network.json": "Healthcare facility network with medical devices and systems",
            "realistic_enterprise_network.json": "Large enterprise network with multiple departments",
            "realistic_smb_network.json": "Small-to-medium business network topology",
        }
        self.description_label = tk.Label(
            descriptions_frame,
            text=self.network_descriptions["demo_network.json"],
            bg=self.tab_color,
            fg=self.theme.COLORS["text_secondary"],
            wraplength=400,
            justify="left",
        )
        self.description_label.pack(anchor="w", padx=5, pady=2)
        self.custom_frame = tk.Frame(self.selection_content_frame, bg=self.tab_color)
        tk.Label(
            self.custom_frame,
            text="Select Network File:",
            bg=self.tab_color,
            fg=self.button_fg,
        ).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.custom_entry = self.create_styled_entry(
            self.custom_frame, self.network_file_var, width=35
        )
        self.custom_entry.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        self.browse_button = self.create_styled_button(
            self.custom_frame, "Browse", self.browse_network_file
        )
        self.browse_button.grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.create_section_header(self.pad_frame, "Network Visualization", section_type="network")
        visualization_frame = tk.Frame(self.pad_frame, bg=self.tab_color)
        visualization_frame.pack(fill="x", padx=10, pady=5)
        self.create_styled_button(
            visualization_frame, "Visualize Network", self.launch_visualizer
        ).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self._update_network_path()
        self._on_source_change()
        self.create_section_header(self.pad_frame, "Network Creation", section_type="network")
        creation_frame = tk.Frame(self.pad_frame, bg=self.tab_color)
        creation_frame.pack(fill="x", padx=10, pady=5)
        self.create_styled_button(
            creation_frame, "Create New Network", self.open_create_network_window
        ).grid(row=0, column=0, padx=5, pady=5, sticky="w")

    def _get_available_networks(self):
        try:
            library_dir = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", "..", "networks", "library")
            )
            if not os.path.exists(library_dir):
                return ["demo_network.json"]
            json_files = [f for f in os.listdir(library_dir) if f.endswith(".json")]
            json_files.sort()
            return json_files if json_files else ["demo_network.json"]
        except Exception as e:
            print(f"Error loading network files: {e}")
            return ["demo_network.json"]

    def _refresh_networks(self):
        current_value = self.predefined_var.get()
        available_networks = self._get_available_networks()
        self.predefined_dropdown["values"] = available_networks
        if current_value in available_networks:
            self.predefined_var.set(current_value)
        else:
            self.predefined_var.set(available_networks[0] if available_networks else "")
        self._update_network_path()
        messagebox.showinfo("Refresh Complete", f"Found {len(available_networks)} network files")

    def _on_source_change(self):
        for widget in self.selection_content_frame.winfo_children():
            widget.pack_forget()
        if self.network_source.get() == "library":
            self.predefined_frame.pack(fill="x", padx=0, pady=0)
            self._update_network_path()
        else:
            self.custom_frame.pack(fill="x", padx=0, pady=0)

    def _update_network_path(self, event=None):
        if hasattr(self, "predefined_var"):
            selected_file = self.predefined_var.get()
            network_path = os.path.abspath(
                os.path.join(
                    os.path.dirname(__file__),
                    "..",
                    "..",
                    "networks",
                    "library",
                    selected_file,
                )
            )
            self.network_file_var.set(network_path)
            if hasattr(self, "description_label"):
                description = self.network_descriptions.get(
                    selected_file, f"Custom network file: {selected_file}"
                )
                self.description_label.config(text=description)

    def open_create_network_window(self):
        NetworkCreator(self.parent)

    def browse_network_file(self):
        network_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..",
            "..",
            "networks",
            "library",
        )
        network_dir = os.path.abspath(network_dir)
        file_path = filedialog.askopenfilename(
            title="Select Network File",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
            initialdir=network_dir,
        )
        if file_path:
            self.network_file_var.set(file_path)

    def launch_visualizer(self):
        from networks.network_visualizer import NetworkVisualizer
        from src.core.graph import Graph

        network_path = self.network_file_var.get()
        network = Graph.from_json(network_path)
        visualizer = NetworkVisualizer(network)
        visualizer.visualize()

    def get_network_config(self):
        return {"file_path": self.network_file_var.get()}
