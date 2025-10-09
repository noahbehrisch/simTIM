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
        self.detection_engine_var = tk.StringVar(value="simple_tim")
        
        super().__init__(parent, theme_colors)
    
    def create_widgets(self):
        """Create simulation configuration widgets."""
        # Simulation Parameters section (moved to top)
        self.create_section_header(
            self.pad_frame, 
            "Simulation Parameters:", 
            bg_color="#f0fff0"
        )
        
        params_frame = tk.Frame(self.pad_frame, bg=self.tab_color)
        params_frame.pack(fill="x", padx=10, pady=10)
        
        # Simulation runs input
        tk.Label(
            params_frame, 
            text="Simulation Runs:", 
            bg=self.tab_color, 
            fg=self.button_fg
        ).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        self.create_styled_entry(
            params_frame, 
            self.sim_runs_var,
            width=10
        ).grid(row=0, column=1, padx=10, pady=10, sticky="w")
        
        # Simulation time input
        tk.Label(
            params_frame, 
            text="Simulation Time:", 
            bg=self.tab_color, 
            fg=self.button_fg
        ).grid(row=1, column=0, padx=10, pady=10, sticky="w")
        
        self.create_styled_entry(
            params_frame, 
            self.sim_time_var,
            width=10
        ).grid(row=1, column=1, padx=10, pady=10, sticky="w")
        
        # Detection Engine section (moved below parameters)
        self.create_section_header(
            self.pad_frame, 
            "Detection Engine:", 
            bg_color="#f0f8ff"
        )
        
        # Detection engine descriptions
        engine_info_frame = tk.Frame(self.pad_frame, bg="#f0f8ff", relief="ridge", bd=1)
        engine_info_frame.pack(fill="x", padx=10, pady=5)
        
        self.create_info_label(
            engine_info_frame, 
            "• Legacy: Original simple detection (random-based, backward compatible)",
            bg_color="#f0f8ff"
        ).pack(anchor="w", padx=15)
        
        self.create_info_label(
            engine_info_frame, 
            "• Simple TIM: Minimal TIM paper compliance (mathematical framework)",
            bg_color="#f0f8ff"
        ).pack(anchor="w", padx=15)
        
        self.create_info_label(
            engine_info_frame, 
            "• Advanced TIM: Full TIM compliance + cybersecurity domain knowledge",
            bg_color="#f0f8ff"
        ).pack(anchor="w", padx=15)
        
        # Detection engine selection
        engine_frame = tk.Frame(self.pad_frame, bg=self.tab_color)
        engine_frame.pack(fill="x", padx=10, pady=10)
        
        tk.Label(
            engine_frame, 
            text="Detection Engine:", 
            bg=self.tab_color, 
            fg=self.button_fg,
            font=("Arial", 10, "bold")
        ).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        detection_dropdown = ttk.Combobox(
            engine_frame, 
            textvariable=self.detection_engine_var, 
            values=["legacy", "simple_tim", "advanced_tim"], 
            state="readonly", 
            width=15
        )
        detection_dropdown.grid(row=0, column=1, padx=10, pady=10, sticky="w")
    
    def get_simulation_config(self):
        """
        Get the current simulation configuration.
        
        Returns:
            dict: Simulation configuration with runs, time, and detection engine
        """
        return {
            'runs': self.sim_runs_var.get(),
            'time': self.sim_time_var.get(),
            'detection_engine_type': self.detection_engine_var.get()
        }
