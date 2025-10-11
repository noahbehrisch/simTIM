"""
Network Tab

Handles network creation, loading, and visualization.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from .base_tab import BaseTab

class NetworkTab(BaseTab):
    def __init__(self, parent, theme_colors):
        """Initialize network tab."""
        # Default network path (updated to demo network)
        default_network_path = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__), 
                '..', '..', 
                'networks', 
                'library', 
                'demo_network.json'
            )
        )
        self.network_file_var = tk.StringVar(value=default_network_path)
        
        super().__init__(parent, theme_colors)
    
    def create_widgets(self):
        """Create network configuration widgets."""
        # Network Selection Section
        selection_section = self.create_section_header(
            self.pad_frame, 
            "Network Selection", 
            section_type="network"
        )
        
        # Create network selection frame
        selection_frame = tk.Frame(self.pad_frame, bg=self.tab_color)
        selection_frame.pack(fill="x", padx=10, pady=5)
        
        # Network source selection
        tk.Label(
            selection_frame, 
            text="Select Network Source:", 
            bg=self.tab_color, 
            fg=self.button_fg,
            font=self.theme.FONTS['heading_medium']
        ).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        # Radio buttons for network source
        self.network_source = tk.StringVar(value="library")
        
        tk.Radiobutton(
            selection_frame,
            text="Choose from Library",
            variable=self.network_source,
            value="library",
            bg=self.tab_color,
            fg=self.button_fg,
            selectcolor=self.theme.COLORS['input_bg'],
            command=self._on_source_change
        ).grid(row=1, column=0, padx=20, pady=2, sticky="w")
        
        tk.Radiobutton(
            selection_frame,
            text="Choose from File",
            variable=self.network_source,
            value="file",
            bg=self.tab_color,
            fg=self.button_fg,
            selectcolor=self.theme.COLORS['input_bg'],
            command=self._on_source_change
        ).grid(row=2, column=0, padx=20, pady=2, sticky="w")
        
        # Create a placeholder frame that will contain either library or file selection
        self.selection_content_frame = tk.Frame(self.pad_frame, bg=self.tab_color)
        self.selection_content_frame.pack(fill="x", padx=10, pady=5)
        
        # Library Networks Section
        self.predefined_frame = tk.Frame(self.selection_content_frame, bg=self.tab_color)
        
        tk.Label(
            self.predefined_frame, 
            text="Select from Library:", 
            bg=self.tab_color, 
            fg=self.button_fg
        ).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        # Network dropdown - dynamically populated from library directory
        self.predefined_var = tk.StringVar(value="demo_network.json")
        self.predefined_dropdown = ttk.Combobox(
            self.predefined_frame,
            textvariable=self.predefined_var,
            values=self._get_available_networks(),
            state="readonly",
            width=30
        )
        self.predefined_dropdown.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        self.predefined_dropdown.bind('<<ComboboxSelected>>', self._update_network_path)
        
        # Add refresh button for predefined networks
        self.create_styled_button(
            self.predefined_frame,
            "Refresh",
            self._refresh_networks
        ).grid(row=0, column=2, padx=5, pady=5, sticky="w")
        
        # Network descriptions
        descriptions_frame = tk.Frame(self.predefined_frame, bg=self.tab_color)
        descriptions_frame.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky="ew")
        
        self.network_descriptions = {
            "demo_network.json": "Simple 2-node network for testing and demonstrations",
            "healthcare_network.json": "Healthcare facility network with medical devices and systems",
            "realistic_enterprise_network.json": "Large enterprise network with multiple departments",
            "realistic_smb_network.json": "Small-to-medium business network topology"
        }
        
        self.description_label = tk.Label(
            descriptions_frame,
            text=self.network_descriptions["demo_network.json"],
            bg=self.tab_color,
            fg=self.theme.COLORS['text_secondary'],
            wraplength=400,
            justify="left"
        )
        self.description_label.pack(anchor="w", padx=5, pady=2)
        
        # File Selection Section
        self.custom_frame = tk.Frame(self.selection_content_frame, bg=self.tab_color)
        
        tk.Label(
            self.custom_frame, 
            text="Select Network File:", 
            bg=self.tab_color, 
            fg=self.button_fg
        ).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        # Network file path entry
        self.custom_entry = self.create_styled_entry(
            self.custom_frame,
            self.network_file_var,
            width=35
        )
        self.custom_entry.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        
        # Browse button
        self.browse_button = self.create_styled_button(
            self.custom_frame,
            "Browse",
            self.browse_network_file
        )
        self.browse_button.grid(row=0, column=2, padx=5, pady=5, sticky="w")
        
        # Network Visualization Section
        visualization_section = self.create_section_header(
            self.pad_frame, 
            "Network Visualization", 
            section_type="network"
        )
        
        visualization_frame = tk.Frame(self.pad_frame, bg=self.tab_color)
        visualization_frame.pack(fill="x", padx=10, pady=5)
        
        self.create_styled_button(
            visualization_frame,
            "Visualize Network",
            self.launch_visualizer
        ).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        # Initialize the UI state
        self._update_network_path()
        self._on_source_change()
        
        # Network Creation Section (at the very end)
        creation_section = self.create_section_header(
            self.pad_frame, 
            "Network Creation", 
            section_type="network"
        )
        
        creation_frame = tk.Frame(self.pad_frame, bg=self.tab_color)
        creation_frame.pack(fill="x", padx=10, pady=5)
        
        self.create_styled_button(
            creation_frame,
            "Create New Network",
            self.open_create_network_window
        ).grid(row=0, column=0, padx=5, pady=5, sticky="w")
    
    def _get_available_networks(self):
        """Dynamically get all JSON files from the networks library directory."""
        try:
            library_dir = os.path.abspath(
                os.path.join(
                    os.path.dirname(__file__), 
                    '..', '..', 
                    'networks', 
                    'library'
                )
            )
            
            if not os.path.exists(library_dir):
                return ["demo_network.json"]  # fallback
            
            # Get all JSON files in the library directory
            json_files = [f for f in os.listdir(library_dir) if f.endswith('.json')]
            json_files.sort()  # Sort alphabetically
            
            return json_files if json_files else ["demo_network.json"]
            
        except Exception as e:
            print(f"Error loading network files: {e}")
            return ["demo_network.json"]  # fallback
    
    def _refresh_networks(self):
        """Refresh the list of available predefined networks."""
        current_value = self.predefined_var.get()
        available_networks = self._get_available_networks()
        
        # Update dropdown values
        self.predefined_dropdown['values'] = available_networks
        
        # Keep current selection if it still exists, otherwise use first available
        if current_value in available_networks:
            self.predefined_var.set(current_value)
        else:
            self.predefined_var.set(available_networks[0] if available_networks else "")
        
        # Update path and description
        self._update_network_path()
        
        # Show a brief message
        messagebox.showinfo("Refresh Complete", f"Found {len(available_networks)} network files")

    def _on_source_change(self):
        """Handle network source selection change."""
        # Clear the content frame
        for widget in self.selection_content_frame.winfo_children():
            widget.pack_forget()
            
        if self.network_source.get() == "library":
            # Show predefined frame
            self.predefined_frame.pack(fill="x", padx=0, pady=0)
            self._update_network_path()
        else:
            # Show custom frame
            self.custom_frame.pack(fill="x", padx=0, pady=0)
    
    def _update_network_path(self, event=None):
        """Update the network file path based on predefined selection."""
        if hasattr(self, 'predefined_var'):
            selected_file = self.predefined_var.get()
            network_path = os.path.abspath(
                os.path.join(
                    os.path.dirname(__file__), 
                    '..', '..', 
                    'networks', 
                    'library', 
                    selected_file
                )
            )
            self.network_file_var.set(network_path)
            
            # Update description (with fallback for unknown networks)
            if hasattr(self, 'description_label'):
                description = self.network_descriptions.get(
                    selected_file, 
                    f"Custom network file: {selected_file}"
                )
                self.description_label.config(text=description)
    
    def open_create_network_window(self):
        """Open network creation window."""
        win = tk.Toplevel(self.parent)
        win.title("Create Network")
        win.geometry("1800x1200")
        win.configure(bg=self.bg_color)
        tk.Label(win, text="Network creation window", bg=self.tab_color, fg=self.button_fg).pack(padx=20, pady=20)
        """Open network creation window."""
        win = tk.Toplevel(self.parent)
        win.title("Create Network")
        win.geometry("1800x1200")
        win.configure(bg=self.bg_color)
        tk.Label(win, text="Network creation window", bg=self.tab_color, fg=self.button_fg).pack(padx=20, pady=20)
    
    def browse_network_file(self):
        """Open file dialog to select network file."""
        network_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'networks', 'library')
        network_dir = os.path.abspath(network_dir)
        file_path = filedialog.askopenfilename(
            title="Select Network File",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
            initialdir=network_dir
        )
        if file_path:
            self.network_file_var.set(file_path)
    
    def launch_visualizer(self):
        """Launch network visualizer."""
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        from src.networks.network_visualizer import NetworkVisualizer
        from src.core.graph import Graph

        network_path = self.network_file_var.get()
        network = Graph.from_json(network_path)
        visualizer = NetworkVisualizer(network)
        visualizer.visualize()
    
    def get_network_config(self):
        """
        Get the current network configuration.
        
        Returns:
            dict: Network configuration with file path
        """
        return {
            'file_path': self.network_file_var.get()
        }
