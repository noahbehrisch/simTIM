"""
Simulation Tab

Handles simulation run configuration and parameters.
"""

import tkinter as tk
from tkinter import ttk
from .base_tab import BaseTab

class SimulationTab(BaseTab):
    """
    Tab for configuring simulation parameters.
    """
    
    def __init__(self, parent, theme_colors):
        """Initialize simulation tab."""
        # Variables for simulation parameters
        self.sim_runs_var = tk.IntVar(value=5)
        self.sim_time_var = tk.DoubleVar(value=20.0)
        
        super().__init__(parent, theme_colors)
    
    def create_widgets(self):
        """Create simulation configuration widgets."""
        # Simulation runs input
        tk.Label(
            self.pad_frame, 
            text="Simulation Runs:", 
            bg=self.tab_color, 
            fg=self.button_fg
        ).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        self.create_styled_entry(
            self.pad_frame, 
            self.sim_runs_var,
            width=10
        ).grid(row=0, column=1, padx=10, pady=10, sticky="w")
        
        # Simulation time input
        tk.Label(
            self.pad_frame, 
            text="Simulation Time:", 
            bg=self.tab_color, 
            fg=self.button_fg
        ).grid(row=1, column=0, padx=10, pady=10, sticky="w")
        
        self.create_styled_entry(
            self.pad_frame, 
            self.sim_time_var,
            width=10
        ).grid(row=1, column=1, padx=10, pady=10, sticky="w")
    
    def get_simulation_config(self):
        """
        Get the current simulation configuration.
        
        Returns:
            dict: Simulation configuration with runs and time
        """
        return {
            'runs': self.sim_runs_var.get(),
            'time': self.sim_time_var.get()
        }
