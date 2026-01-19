import tkinter as tk
from tkinter import ttk, messagebox
from .base_tab import BaseTab
from src.utils.discovery import list_attacker_strategies, list_defender_strategies


class VariablesTab(BaseTab):

    def __init__(self, parent, theme_colors):
        self.scenarios = []
        self.on_scenarios_changed = None
        self.enabled_var = tk.BooleanVar(value=False)
        self.variable_type = tk.StringVar(value="attack_duration")
        self.app = parent
        self.attacker_strategies = list_attacker_strategies()
        self.defender_strategies = list_defender_strategies()
        super().__init__(parent, theme_colors)

    def create_widgets(self):
        title = tk.Label(
            self.pad_frame,
            text="Variable Scenarios",
            font=("Arial", 14, "bold"),
            bg=self.tab_color,
            fg=self.button_fg,
        )
        title.pack(pady=20)
        enable_frame = tk.Frame(self.pad_frame, bg=self.tab_color)
        enable_frame.pack(pady=10)
        enable_check = tk.Checkbutton(
            enable_frame,
            text="Enable Scenario Comparison",
            variable=self.enabled_var,
            command=self._on_enabled_changed,
            bg=self.tab_color,
            fg=self.button_fg,
            font=("Arial", 11, "bold"),
            selectcolor=self.tab_color,
            activebackground=self.tab_color,
            activeforeground=self.button_fg,
        )
        enable_check.pack()
        variable_frame = tk.Frame(self.pad_frame, bg=self.tab_color)
        variable_frame.pack(pady=15)
        tk.Label(
            variable_frame,
            text="Parameter to vary:",
            font=("Arial", 10, "bold"),
            bg=self.tab_color,
            fg=self.button_fg,
        ).pack(side=tk.LEFT, padx=(0, 10))
        self.variable_dropdown = ttk.Combobox(
            variable_frame,
            textvariable=self.variable_type,
            values=[
                "attack_duration",
                "defense_duration",
                "attacker_strategy",
                "defender_strategy",
            ],
            state="readonly",
            width=20,
            font=("Arial", 10),
        )
        self.variable_dropdown.pack(side=tk.LEFT)
        self.variable_dropdown.bind(
            "<<ComboboxSelected>>", self._on_variable_type_changed
        )
        self.description_label = tk.Label(
            self.pad_frame,
            text="",
            font=("Arial", 9),
            bg=self.tab_color,
            fg=self.button_fg,
            justify=tk.CENTER,
        )
        self.description_label.pack(pady=5)
        self._update_description()
        self.config_frame = tk.Frame(self.pad_frame, bg=self.tab_color)
        self.config_frame.pack(fill=tk.BOTH, expand=True, padx=50, pady=20)
        canvas = tk.Canvas(
            self.config_frame, bg=self.tab_color, highlightthickness=0, height=250
        )
        scrollbar = ttk.Scrollbar(
            self.config_frame, orient="vertical", command=canvas.yview
        )
        self.scenarios_frame = tk.Frame(canvas, bg=self.tab_color)
        self.scenarios_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self.scenarios_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.button_frame = tk.Frame(self.config_frame, bg=self.tab_color)
        self.button_frame.pack(pady=10)
        tk.Button(
            self.button_frame,
            text="+ Add Scenario",
            command=self._add_scenario,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 10),
            padx=15,
            pady=3,
        ).pack(side=tk.LEFT, padx=5)
        tk.Button(
            self.button_frame,
            text="Clear All",
            command=self._clear_all,
            bg="#f44336",
            fg="white",
            font=("Arial", 10),
            padx=15,
            pady=3,
        ).pack(side=tk.LEFT, padx=5)
        self.status_label = tk.Label(
            self.pad_frame,
            text="",
            bg=self.tab_color,
            fg=self.button_fg,
            font=("Arial", 10, "bold"),
        )
        self.status_label.pack(pady=10)
        self._set_config_state("disabled")

    def _on_enabled_changed(self):
        if self.enabled_var.get():
            self._set_config_state("normal")
            self.variable_dropdown.config(state="readonly")
            if not self.scenarios:
                self._add_default_scenarios()
            self._update_status()
        else:
            self._set_config_state("disabled")
            self.variable_dropdown.config(state="disabled")
            self._update_status()

    def _on_variable_type_changed(self, event=None):
        self._clear_all()
        self._add_default_scenarios()
        self._update_description()

    def _add_default_scenarios(self):
        var_type = self.variable_type.get()
        if var_type == "attack_duration":
            self._add_scenario_with_values(1.0, 20)
            self._add_scenario_with_values(3.0, 20)
            self._add_scenario_with_values(5.0, 20)
        elif var_type == "defense_duration":
            self._add_scenario_with_values(0.5, 20)
            self._add_scenario_with_values(1.0, 20)
            self._add_scenario_with_values(2.0, 20)
        elif var_type == "attacker_strategy":
            for strategy in self.attacker_strategies:
                self._add_scenario_with_values(strategy, 20)
        elif var_type == "defender_strategy":
            for strategy in self.defender_strategies:
                self._add_scenario_with_values(strategy, 20)

    def _update_description(self):
        var_type = self.variable_type.get()
        if var_type == "attack_duration":
            text = "When disabled, simulations use attack action durations from JSON files.\nWhen enabled, compare different attack action duration scenarios."
        elif var_type == "defense_duration":
            text = "When disabled, simulations use defense action durations from JSON files.\nWhen enabled, compare different defense action duration scenarios."
        elif var_type == "attacker_strategy":
            text = "When disabled, simulations use attacker strategies from Attacker tab.\nWhen enabled, compare different attacker strategy scenarios."
        elif var_type == "defender_strategy":
            text = "When disabled, simulations use defender strategies from Defender tab.\nWhen enabled, compare different defender strategy scenarios."
        else:
            text = "Select a parameter to vary and configure scenarios below."
        self.description_label.config(text=text)

    def _set_config_state(self, state):
        for widget in self.config_frame.winfo_children():
            if isinstance(widget, (tk.Frame, tk.Canvas)):
                self._set_widget_state_recursive(widget, state)
            else:
                try:
                    widget.config(state=state)
                except tk.TclError:
                    # Some widgets don't support state changes (e.g., Frame, Label)
                    pass

    def _set_widget_state_recursive(self, widget, state):
        for child in widget.winfo_children():
            if isinstance(child, (tk.Frame, tk.Canvas)):
                self._set_widget_state_recursive(child, state)
            else:
                try:
                    child.config(state=state)
                except tk.TclError:
                    # Some widgets don't support state changes (e.g., Frame, Label)
                    pass

    def _add_scenario(self):
        var_type = self.variable_type.get()
        if var_type == "attack_duration":
            self._add_scenario_with_values(4.0, 20)
        elif var_type == "defense_duration":
            self._add_scenario_with_values(1.5, 20)
        elif var_type == "attacker_strategy":
            default_strategy = (
                self.attacker_strategies[0] if self.attacker_strategies else "greedy"
            )
            self._add_scenario_with_values(default_strategy, 20)
        elif var_type == "defender_strategy":
            default_strategy = (
                self.defender_strategies[0] if self.defender_strategies else "reactive"
            )
            self._add_scenario_with_values(default_strategy, 20)

    def _add_scenario_with_values(self, value, runs=20):
        var_type = self.variable_type.get()
        row_frame = tk.Frame(self.scenarios_frame, bg="white", relief=tk.RAISED, bd=1)
        row_frame.pack(fill=tk.X, pady=2, padx=5)
        scenario_num = len(self.scenarios) + 1
        tk.Label(
            row_frame,
            text=f"#{scenario_num}",
            bg="white",
            fg=self.button_fg,
            font=("Arial", 10, "bold"),
            width=4,
        ).pack(side=tk.LEFT, padx=5, pady=5)
        if var_type in ["attack_duration", "defense_duration"]:
            label_text = (
                "Attack Duration (hours):"
                if var_type == "attack_duration"
                else "Defense Duration (hours):"
            )
            tk.Label(
                row_frame,
                text=label_text,
                bg="white",
                fg=self.button_fg,
                font=("Arial", 9),
            ).pack(side=tk.LEFT, padx=5)
            value_var = tk.StringVar(value=str(value))
            value_entry = tk.Entry(
                row_frame, textvariable=value_var, width=8, font=("Arial", 9)
            )
            value_entry.pack(side=tk.LEFT, padx=5)
        elif var_type == "attacker_strategy":
            tk.Label(
                row_frame,
                text="Attacker Strategy:",
                bg="white",
                fg=self.button_fg,
                font=("Arial", 9),
            ).pack(side=tk.LEFT, padx=5)
            value_var = tk.StringVar(value=str(value))
            value_dropdown = ttk.Combobox(
                row_frame,
                textvariable=value_var,
                values=self.attacker_strategies,
                state="readonly",
                width=12,
                font=("Arial", 9),
            )
            value_dropdown.pack(side=tk.LEFT, padx=5)
        elif var_type == "defender_strategy":
            tk.Label(
                row_frame,
                text="Defender Strategy:",
                bg="white",
                fg=self.button_fg,
                font=("Arial", 9),
            ).pack(side=tk.LEFT, padx=5)
            value_var = tk.StringVar(value=str(value))
            value_dropdown = ttk.Combobox(
                row_frame,
                textvariable=value_var,
                values=self.defender_strategies,
                state="readonly",
                width=12,
                font=("Arial", 9),
            )
            value_dropdown.pack(side=tk.LEFT, padx=5)
        tk.Label(
            row_frame, text="Runs:", bg="white", fg=self.button_fg, font=("Arial", 9)
        ).pack(side=tk.LEFT, padx=(15, 5))
        runs_var = tk.StringVar(value=str(runs))
        runs_entry = tk.Entry(
            row_frame, textvariable=runs_var, width=6, font=("Arial", 9)
        )
        runs_entry.pack(side=tk.LEFT, padx=5)
        remove_btn = tk.Button(
            row_frame,
            text="✕",
            command=lambda: self._remove_scenario(row_frame),
            bg="#d32f2f",
            fg="white",
            font=("Arial", 8, "bold"),
            width=3,
            pady=0,
        )
        remove_btn.pack(side=tk.RIGHT, padx=5)
        scenario_data = {
            "frame": row_frame,
            "value_var": value_var,
            "runs_var": runs_var,
        }
        self.scenarios.append(scenario_data)
        value_var.trace_add("write", lambda *args: self._update_status())
        runs_var.trace_add("write", lambda *args: self._update_status())
        self._update_status()

    def _remove_scenario(self, frame):
        self.scenarios = [s for s in self.scenarios if s["frame"] != frame]
        frame.destroy()
        for i, scenario in enumerate(self.scenarios, 1):
            for widget in scenario["frame"].winfo_children():
                if isinstance(widget, tk.Label) and widget.cget("text").startswith("#"):
                    widget.config(text=f"#{i}")
                    break
        self._update_status()

    def _clear_all(self):
        for scenario in self.scenarios:
            scenario["frame"].destroy()
        self.scenarios = []
        self._update_status()

    def _parse_scenarios(self):
        var_type = self.variable_type.get()
        result = []
        for scenario in self.scenarios:
            try:
                value = scenario["value_var"].get()
                runs = int(scenario["runs_var"].get())
                if runs <= 0:
                    return None
                if var_type in ["attack_duration", "defense_duration"]:
                    duration = float(value)
                    if duration <= 0:
                        return None
                    result.append((duration, runs))
                elif var_type == "attacker_strategy":
                    if value not in self.attacker_strategies:
                        return None
                    result.append((value, runs))
                elif var_type == "defender_strategy":
                    if value not in self.defender_strategies:
                        return None
                    result.append((value, runs))
            except ValueError:
                return None
        return result if result else []

    def _update_status(self):
        if not hasattr(self, "status_label"):
            return
        if not self.enabled_var.get():
            var_type = self.variable_type.get()
            if var_type == "attack_duration":
                msg = "Scenario comparison disabled - using default attack action durations"
            elif var_type == "defense_duration":
                msg = "Scenario comparison disabled - using default defense action durations"
            elif var_type == "attacker_strategy":
                msg = "Scenario comparison disabled - using attacker strategies from Attacker tab"
            elif var_type == "defender_strategy":
                msg = "Scenario comparison disabled - using defender strategies from Defender tab"
            else:
                msg = "Scenario comparison disabled"
            self.status_label.config(text=msg, fg=self.button_fg)
            if self.on_scenarios_changed:
                self.on_scenarios_changed([])
            return
        scenarios = self._parse_scenarios()
        var_type = self.variable_type.get()
        if scenarios is None:
            self.status_label.config(
                text="❌ Invalid input - check values and run counts", fg="#d32f2f"
            )
        elif not scenarios:
            self.status_label.config(
                text="⚠️ Enabled but no scenarios configured - add scenarios below",
                fg="#FF9800",
            )
        else:
            total_runs = sum((runs for _, runs in scenarios))
            if var_type in ["attack_duration", "defense_duration"]:
                value_str = ", ".join((f"{v}h" for v, _ in scenarios))
                label = (
                    "attack duration(s)"
                    if var_type == "attack_duration"
                    else "defense duration(s)"
                )
            elif var_type == "attacker_strategy":
                value_str = ", ".join((f"{v}" for v, _ in scenarios))
                label = "attacker strateg(ies)"
            elif var_type == "defender_strategy":
                value_str = ", ".join((f"{v}" for v, _ in scenarios))
                label = "defender strateg(ies)"
            else:
                value_str = ", ".join((f"{v}" for v, _ in scenarios))
                label = "scenario(s)"
            self.status_label.config(
                text=f"✓ {len(scenarios)} {label}: {value_str} | Total runs: {total_runs}",
                fg="#2e7d32",
            )
        if self.on_scenarios_changed:
            config = self.get_variables_config()
            self.on_scenarios_changed(config.get("scenarios", []))

    def get_variables_config(self):
        if not self.enabled_var.get():
            return {}
        scenarios = self._parse_scenarios()
        if scenarios is None or not scenarios:
            return {}
        var_type = self.variable_type.get()
        if var_type in ["attack_duration", "defense_duration"]:
            return {
                "variable_type": var_type,
                "scenarios": [
                    {"duration": value, "runs": runs} for value, runs in scenarios
                ],
            }
        elif var_type == "attacker_strategy":
            return {
                "variable_type": "attacker_strategy",
                "scenarios": [
                    {"strategy": value, "runs": runs} for value, runs in scenarios
                ],
            }
        elif var_type == "defender_strategy":
            return {
                "variable_type": "defender_strategy",
                "scenarios": [
                    {"strategy": value, "runs": runs} for value, runs in scenarios
                ],
            }
        else:
            return {}
