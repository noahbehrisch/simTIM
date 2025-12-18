import tkinter as tk
from tkinter import ttk
import importlib
import inspect
import os
from pathlib import Path
from .base_tab import BaseTab
from src.gui.help_content import TOOLTIPS
from src.gui.help_window import ToolTip

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
        Similar to how NetworkTab scans for available networks.
        
        Returns:
            dict: Mapping of engine names to their display info
        """
        engines = {}
        
        try:
            # Get the detection directory
            detection_dir = os.path.abspath(
                os.path.join(
                    os.path.dirname(__file__), 
                    '..', '..', 
                    'detection'
                )
            )
            
            if not os.path.exists(detection_dir):
                print(f"Warning: Detection directory not found at {detection_dir}")
                return self._get_fallback_engines()
            
            # Import the base detection engine for type checking
            from src.detection.base_detection import BaseDetectionEngine
            
            # Get all Python files in the detection directory (excluding base and __init__)
            python_files = [
                f for f in os.listdir(detection_dir) 
                if f.endswith('_detection.py') and f != 'base_detection.py'
            ]
            
            # Try to import each detection engine
            for filename in python_files:
                try:
                    module_name = filename[:-3]  # Remove .py extension
                    module = importlib.import_module(f'src.detection.{module_name}')
                    
                    # Find all classes in the module that inherit from BaseDetectionEngine
                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        # Check if it's a detection engine (not the base class itself)
                        if (issubclass(obj, BaseDetectionEngine) and 
                            obj != BaseDetectionEngine and
                            obj.__module__ == f'src.detection.{module_name}'):
                            
                            # Try to instantiate to verify it works
                            try:
                                engine_instance = obj()
                                
                                # Generate engine ID from class name
                                # UniformDetectionEngine -> uniform
                                engine_id = name.replace('DetectionEngine', '').lower()
                                
                                # Extract description from docstring
                                docstring = inspect.getdoc(obj) or ""
                                first_line = docstring.split('\n')[0] if docstring else name
                                
                                # Try to get a more detailed description from docstring
                                description = first_line
                                if 'Fa(t)' in docstring:
                                    # Extract the CDF formula line
                                    for line in docstring.split('\n'):
                                        if 'Fa(t)' in line and '=' in line:
                                            description = line.strip()
                                            break
                                
                                engines[engine_id] = {
                                    'class': obj,
                                    'name': name.replace('DetectionEngine', ' Detection'),
                                    'description': description,
                                    'module': module_name
                                }
                                
                            except Exception as e:
                                print(f"Warning: Could not instantiate {name}: {e}")
                                
                except Exception as e:
                    print(f"Warning: Could not import {filename}: {e}")
            
            # If no engines were found, use fallback
            if not engines:
                print("No detection engines found, using fallback")
                return self._get_fallback_engines()
            
        except Exception as e:
            print(f"Error scanning detection folder: {e}")
            return self._get_fallback_engines()
        
        return engines
    
    def _get_fallback_engines(self):
        """Fallback engines if dynamic scanning fails."""
        try:
            from src.detection import (UniformDetectionEngine, 
                                      ExponentialDetectionEngine, 
                                      LinearDetectionEngine)
            return {
                'uniform': {
                    'class': UniformDetectionEngine,
                    'name': 'Uniform Detection',
                    'description': 'Fa(t) = t - Constant detection rate'
                },
                'exponential': {
                    'class': ExponentialDetectionEngine, 
                    'name': 'Exponential Detection',
                    'description': 'Fa(t) = 1 - e^(-λt) - Early detection bias'
                },
                'linear': {
                    'class': LinearDetectionEngine,
                    'name': 'Linear Detection',
                    'description': 'Fa(t) = t^n - Linear detection rate increase (n=2)'
                }
            }
        except ImportError:
            return {
                'exponential': {
                    'name': 'Exponential Detection',
                    'description': 'Default detection engine'
                }
            }
    
    def _get_default_engine(self):
        """Get the default detection engine (exponential)."""
        if 'exponential' in self.available_engines:
            return 'exponential'
        elif 'uniform' in self.available_engines:
            return 'uniform'
        else:
            return list(self.available_engines.keys())[0] if self.available_engines else 'exponential'
    
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
        
        self.sim_runs_entry = self.create_styled_entry(
            params_frame, 
            self.sim_runs_var,
            width=10
        )
        self.sim_runs_entry.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        ToolTip(self.sim_runs_entry, TOOLTIPS.get("sim_runs", ""))
        
        # Info label for variable scenarios
        self.runs_info_label = tk.Label(
            params_frame,
            text="",
            bg=self.tab_color,
            fg="#FF9800",  # Orange color for info
            font=("Arial", 9, "italic")
        )
        self.runs_info_label.grid(row=0, column=2, padx=10, pady=10, sticky="w")
        
        # Simulation time input
        tk.Label(
            params_frame, 
            text="Simulation Time:", 
            bg=self.tab_color, 
            fg=self.button_fg
        ).grid(row=1, column=0, padx=10, pady=10, sticky="w")
        
        sim_time_entry = self.create_styled_entry(
            params_frame, 
            self.sim_time_var,
            width=10
        )
        sim_time_entry.grid(row=1, column=1, padx=10, pady=10, sticky="w")
        ToolTip(sim_time_entry, TOOLTIPS.get("sim_time", ""))
        
        # Detection Engine section (moved below parameters)
        self.create_section_header(
            self.pad_frame, 
            "Detection Engine:", 
            section_type="network"
        )
        
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
    
    def update_runs_info(self, variable_scenarios=None):
        """
        Update the info label to show variable scenario information.
        
        Args:
            variable_scenarios: List of scenario dicts or None
        """
        if not hasattr(self, 'runs_info_label'):
            return
            
        if variable_scenarios and len(variable_scenarios) > 0:
            total_runs = sum(s['runs'] for s in variable_scenarios)
            scenario_count = len(variable_scenarios)
            
            info_text = f"⚠ Overridden by Variables tab: {scenario_count} scenario(s), {total_runs} total runs"
            self.runs_info_label.config(text=info_text)
            
            # Disable the runs entry since it's overridden
            if hasattr(self, 'sim_runs_entry'):
                self.sim_runs_entry.config(state='readonly')
        else:
            self.runs_info_label.config(text="")
            
            # Re-enable the runs entry
            if hasattr(self, 'sim_runs_entry'):
                self.sim_runs_entry.config(state='normal')

    
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
