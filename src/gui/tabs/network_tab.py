"""
Network Tab

Handles network creation, loading, and visualization.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from .base_tab import BaseTab

class NetworkTab(BaseTab):
    """
    Tab for network management and configuration.
    """
    
    def __init__(self, parent, theme_colors):
        """Initialize network tab."""
        # Default network path
        default_network_path = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__), 
                '..', '..', 
                'networks', 
                'library', 
                'realistic_enterprise_network.json'
            )
        )
        self.network_file_var = tk.StringVar(value=default_network_path)
        
        super().__init__(parent, theme_colors)
    
    def create_widgets(self):
        """Create network configuration widgets."""
        # Create Network button
        self.create_styled_button(
            self.pad_frame,
            "Create Network",
            self.open_create_network_window
        ).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        # Load Network File label
        tk.Label(
            self.pad_frame, 
            text="Load Network File:", 
            bg=self.tab_color, 
            fg=self.button_fg
        ).grid(row=1, column=0, padx=10, pady=10, sticky="w")
        
        # Network file path entry
        self.create_styled_entry(
            self.pad_frame,
            self.network_file_var,
            width=30
        ).grid(row=1, column=1, padx=10, pady=10, sticky="w")
        
        # Browse button
        self.create_styled_button(
            self.pad_frame,
            "Browse",
            self.browse_network_file
        ).grid(row=1, column=2, padx=5, pady=10, sticky="w")
        
        # Visualize Network button
        self.create_styled_button(
            self.pad_frame,
            "Visualize Network",
            self.launch_visualizer
        ).grid(row=2, column=0, padx=10, pady=10, sticky="w")
    
    def open_create_network_window(self):
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
