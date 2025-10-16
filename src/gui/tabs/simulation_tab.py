import tkinter as tk
from tkinter import ttk
import importlib
import inspect
from pathlib import Path
from .base_tab import BaseTab

class SimulationTab(BaseTab):
    def __init__(self, parent, theme_colors):
        """Initialize simulation tab."""
        # Get available detection engines
        self.available_engines = self._get_available_detection_engines()
        
        # Variables for simulation parameters
        self.sim_runs_var = tk.IntVar(value=5)
        self.sim_time_var = tk.DoubleVar(value=20.0)
        self.detection_engine_var = tk.StringVar(value=self._get_default_engine())
        
        super().__init__(parent, theme_colors)
    
    def _get_available_detection_engines(self):
        """
        Dynamically scan the detection folder for available engines.
        
        Returns:
            dict: Mapping of engine names to their display info
        """
        engines = {}
        
        try:
            # Import the detection package to get available engines
            from src.detection import SimpleTIMDetectionEngine, AdvancedTIMDetectionEngine
            
            # Map engine classes to their identifiers and descriptions
            engine_mapping = {
                'simple_detection_engine': {
                    'class': SimpleTIMDetectionEngine,
                    'name': 'Simple Detection',
                    'description': 'Bare Bones Detection Engine'
                },
                'advanced_detection_engine': {
                    'class': AdvancedTIMDetectionEngine, 
                    'name': 'Advanced Detection',
                    'description': 'Advanced Detection Engine (!WIP)'
                }
            }
            
            # Verify each engine can be instantiated
            for engine_id, info in engine_mapping.items():
                try:
                    # Test instantiation
                    engine_instance = info['class']()
                    engines[engine_id] = info
                except Exception as e:
                    print(f"Warning: Detection engine {engine_id} not available: {e}")
            
        except ImportError as e:
            print(f"Warning: Could not import detection engines: {e}")
            # Fallback to basic set
            engines = {
                'advanced_detection_engine': {
                    'name': 'Advanced TIM',
                    'description': 'WIP detection engine'
                }
            }
        
        return engines
    
    def _get_default_engine(self):
        """Get the default detection engine."""
        if 'simple_detection_engine' in self.available_engines:
            return 'simple_detection_engine'
        elif 'advanced_detection_engine' in self.available_engines:
            return 'advanced_detection_engine'
        else:
            return list(self.available_engines.keys())[0] if self.available_engines else 'simple_detection_engine'
    
    def create_widgets(self):
        """Create simulation configuration widgets."""
        # Simulation Parameters section (moved to top)
        self.create_section_header(
            self.pad_frame, 
            "Simulation Parameters:", 
            section_type="simulation"
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
            section_type="network"
        )
        
        # Detection engine descriptions
        engine_info_frame = tk.Frame(
            self.pad_frame, 
            bg=self.theme.COLORS['section_network'], 
            **self.theme.BORDERS['light']
        )
        engine_info_frame.pack(fill="x", padx=self.theme.SPACING['md'], pady=self.theme.SPACING['sm'])
        
        # Dynamically create engine descriptions
        for engine_key, engine_info in self.available_engines.items():
            description = engine_info.get('description', f'{engine_key.replace("_", " ").title()}: No description available')
            self.create_info_label(
                engine_info_frame, 
                f"• {description}",
                bg_color=self.theme.COLORS['section_network']
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
            values=list(self.available_engines.keys()), 
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
