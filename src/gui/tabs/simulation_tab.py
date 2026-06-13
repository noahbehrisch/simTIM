import tkinter as tk
from tkinter import ttk

from src.config import sim_config
from src.detection.registry import get_detection_registry
from src.gui.help_content import TOOLTIPS
from src.gui.help_window import ToolTip

from .base_tab import BaseTab


class SimulationTab(BaseTab):
    def __init__(self, parent, theme_colors):
        self.available_engines = self._get_available_detection_engines()
        self.sim_runs_var = tk.IntVar(value=sim_config.default_sim_runs)
        self.sim_days_var = tk.IntVar(value=sim_config.default_sim_time // 24)
        self.sim_hours_var = tk.IntVar(value=sim_config.default_sim_time % 24)
        self.detection_engine_var = tk.StringVar(value=sim_config.default_detection_engine)
        super().__init__(parent, theme_colors)

    def _get_available_detection_engines(self):
        registry = get_detection_registry()
        engines = {}
        for name in registry.get_available():
            info = registry.get_engine_info(name)
            if info:
                engines[name] = {
                    "name": info["class"].replace("DetectionEngine", " Detection"),
                    "description": info.get("docstring", "").split("\n")[0]
                    if info.get("docstring")
                    else name,
                }
        return engines

    def create_widgets(self):
        self.create_section_header(
            self.pad_frame, "Simulation Parameters:", section_type="simulation"
        )
        params_frame = tk.Frame(self.pad_frame, bg=self.tab_color)
        params_frame.pack(fill="x", padx=10, pady=10)
        tk.Label(params_frame, text="Simulation Runs:", bg=self.tab_color, fg=self.button_fg).grid(
            row=0, column=0, padx=10, pady=10, sticky="w"
        )
        self.sim_runs_entry = self.create_styled_entry(params_frame, self.sim_runs_var, width=10)
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

        sim_days_entry = self.create_styled_entry(duration_frame, self.sim_days_var, width=5)
        sim_days_entry.pack(side="left")
        tk.Label(duration_frame, text="days", bg=self.tab_color, fg=self.button_fg).pack(
            side="left", padx=(2, 10)
        )

        sim_hours_entry = self.create_styled_entry(duration_frame, self.sim_hours_var, width=5)
        sim_hours_entry.pack(side="left")
        tk.Label(duration_frame, text="hours", bg=self.tab_color, fg=self.button_fg).pack(
            side="left", padx=2
        )

        ToolTip(sim_days_entry, "Number of days for the simulation")
        ToolTip(sim_hours_entry, "Additional hours for the simulation")

        self.create_section_header(self.pad_frame, "Detection Engine:", section_type="network")
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
            total_runs = sum(s["runs"] for s in variable_scenarios)
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
