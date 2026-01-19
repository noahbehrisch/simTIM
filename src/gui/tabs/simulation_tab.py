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
        self.available_engines = self._get_available_detection_engines()
        self.sim_runs_var = tk.IntVar(value=5)
        self.sim_days_var = tk.IntVar(value=3)
        self.sim_hours_var = tk.IntVar(value=0)
        self.detection_engine_var = tk.StringVar(value=self._get_default_engine())
        super().__init__(parent, theme_colors)

    def _get_available_detection_engines(self):
        engines = {}
        try:
            detection_dir = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", "..", "detection")
            )
            if not os.path.exists(detection_dir):
                print(f"Warning: Detection directory not found at {detection_dir}")
                return self._get_fallback_engines()
            from src.detection.base_detection import BaseDetectionEngine

            python_files = [
                f
                for f in os.listdir(detection_dir)
                if f.endswith("_detection.py") and f != "base_detection.py"
            ]
            for filename in python_files:
                try:
                    module_name = filename[:-3]
                    module = importlib.import_module(f"src.detection.{module_name}")
                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        if (
                            issubclass(obj, BaseDetectionEngine)
                            and obj != BaseDetectionEngine
                            and (obj.__module__ == f"src.detection.{module_name}")
                        ):
                            try:
                                engine_instance = obj()
                                engine_id = name.replace("DetectionEngine", "").lower()
                                docstring = inspect.getdoc(obj) or ""
                                first_line = (
                                    docstring.split("\n")[0] if docstring else name
                                )
                                description = first_line
                                if "Fa(t)" in docstring:
                                    for line in docstring.split("\n"):
                                        if "Fa(t)" in line and "=" in line:
                                            description = line.strip()
                                            break
                                engines[engine_id] = {
                                    "class": obj,
                                    "name": name.replace(
                                        "DetectionEngine", " Detection"
                                    ),
                                    "description": description,
                                    "module": module_name,
                                }
                            except Exception as e:
                                print(f"Warning: Could not instantiate {name}: {e}")
                except Exception as e:
                    print(f"Warning: Could not import {filename}: {e}")
            if not engines:
                print("No detection engines found, using fallback")
                return self._get_fallback_engines()
        except Exception as e:
            print(f"Error scanning detection folder: {e}")
            return self._get_fallback_engines()
        return engines

    def _get_fallback_engines(self):
        try:
            from src.detection import (
                UniformDetectionEngine,
                ExponentialDetectionEngine,
                LinearDetectionEngine,
            )

            return {
                "uniform": {
                    "class": UniformDetectionEngine,
                    "name": "Uniform Detection",
                    "description": "Fa(t) = t - Constant detection rate",
                },
                "exponential": {
                    "class": ExponentialDetectionEngine,
                    "name": "Exponential Detection",
                    "description": "Fa(t) = 1 - e^(-λt) - Early detection bias",
                },
                "linear": {
                    "class": LinearDetectionEngine,
                    "name": "Linear Detection",
                    "description": "Fa(t) = t^n - Linear detection rate increase (n=2)",
                },
            }
        except ImportError:
            return {
                "exponential": {
                    "name": "Exponential Detection",
                    "description": "Default detection engine",
                }
            }

    def _get_default_engine(self):
        if "exponential" in self.available_engines:
            return "exponential"
        elif "uniform" in self.available_engines:
            return "uniform"
        else:
            return (
                list(self.available_engines.keys())[0]
                if self.available_engines
                else "exponential"
            )

    def create_widgets(self):
        self.create_section_header(
            self.pad_frame, "Simulation Parameters:", section_type="simulation"
        )
        params_frame = tk.Frame(self.pad_frame, bg=self.tab_color)
        params_frame.pack(fill="x", padx=10, pady=10)
        tk.Label(
            params_frame, text="Simulation Runs:", bg=self.tab_color, fg=self.button_fg
        ).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.sim_runs_entry = self.create_styled_entry(
            params_frame, self.sim_runs_var, width=10
        )
        self.sim_runs_entry.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        ToolTip(self.sim_runs_entry, TOOLTIPS.get("sim_runs", ""))
        self.runs_info_label = tk.Label(
            params_frame,
            text="",
            bg=self.tab_color,
            fg="#FF9800",
            font=("Arial", 9, "italic"),
        )
        self.runs_info_label.grid(row=0, column=2, padx=10, pady=10, sticky="w")

        tk.Label(
            params_frame,
            text="Simulation Duration:",
            bg=self.tab_color,
            fg=self.button_fg,
        ).grid(row=1, column=0, padx=10, pady=10, sticky="w")
        duration_frame = tk.Frame(params_frame, bg=self.tab_color)
        duration_frame.grid(row=1, column=1, columnspan=2, padx=10, pady=10, sticky="w")

        sim_days_entry = self.create_styled_entry(
            duration_frame, self.sim_days_var, width=5
        )
        sim_days_entry.pack(side="left")
        tk.Label(
            duration_frame, text="days", bg=self.tab_color, fg=self.button_fg
        ).pack(side="left", padx=(2, 10))

        sim_hours_entry = self.create_styled_entry(
            duration_frame, self.sim_hours_var, width=5
        )
        sim_hours_entry.pack(side="left")
        tk.Label(
            duration_frame, text="hours", bg=self.tab_color, fg=self.button_fg
        ).pack(side="left", padx=2)

        ToolTip(sim_days_entry, "Number of days for the simulation")
        ToolTip(sim_hours_entry, "Additional hours for the simulation")

        self.create_section_header(
            self.pad_frame, "Detection Engine:", section_type="network"
        )
        engine_frame = tk.Frame(self.pad_frame, bg=self.tab_color)
        engine_frame.pack(fill="x", padx=10, pady=10)
        tk.Label(
            engine_frame,
            text="Detection Engine:",
            bg=self.tab_color,
            fg=self.button_fg,
            font=("Arial", 10, "bold"),
        ).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        detection_dropdown = ttk.Combobox(
            engine_frame,
            textvariable=self.detection_engine_var,
            values=list(self.available_engines.keys()),
            state="readonly",
            width=15,
        )
        detection_dropdown.grid(row=0, column=1, padx=10, pady=10, sticky="w")

    def update_runs_info(self, variable_scenarios=None):
        if not hasattr(self, "runs_info_label"):
            return
        if variable_scenarios and len(variable_scenarios) > 0:
            total_runs = sum((s["runs"] for s in variable_scenarios))
            scenario_count = len(variable_scenarios)
            info_text = f"⚠ Overridden by Variables tab: {scenario_count} scenario(s), {total_runs} total runs"
            self.runs_info_label.config(text=info_text)
            if hasattr(self, "sim_runs_entry"):
                self.sim_runs_entry.config(state="readonly")
        else:
            self.runs_info_label.config(text="")
            if hasattr(self, "sim_runs_entry"):
                self.sim_runs_entry.config(state="normal")

    def get_sim_time_hours(self):
        return self.sim_days_var.get() * 24 + self.sim_hours_var.get()

    def get_simulation_config(self):
        return {
            "runs": self.sim_runs_var.get(),
            "time": self.get_sim_time_hours(),
            "detection_engine_type": self.detection_engine_var.get(),
        }
