"""
Variables Tab

Configure variable parameters for simulations
"""

import tkinter as tk
from tkinter import ttk, messagebox
from .base_tab import BaseTab


class VariablesTab(BaseTab):
    def __init__(self, parent, theme_colors):
        self.scenarios = []  # List of (duration, num_runs) tuples
        self.on_scenarios_changed = None  # Callback for when scenarios change
        self.enabled_var = tk.BooleanVar(value=False)  # Default: disabled
        self.variable_type = tk.StringVar(value="attack_duration")  # Which parameter to vary
        self.app = parent  # Store reference to parent app for accessing other tabs
        super().__init__(parent, theme_colors)
    
    def create_widgets(self):
        """Create the variables tab interface"""
        
        # Title
        title = tk.Label(
            self.pad_frame,
            text="Variable Scenarios",
            font=("Arial", 14, "bold"),
            bg=self.tab_color,
            fg=self.button_fg
        )
        title.pack(pady=20)
        
        # Enable/Disable checkbox
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
            activeforeground=self.button_fg
        )
        enable_check.pack()
        
        # Variable type selector (dropdown)
        variable_frame = tk.Frame(self.pad_frame, bg=self.tab_color)
        variable_frame.pack(pady=15)
        
        tk.Label(
            variable_frame,
            text="Parameter to vary:",
            font=("Arial", 10, "bold"),
            bg=self.tab_color,
            fg=self.button_fg
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        self.variable_dropdown = ttk.Combobox(
            variable_frame,
            textvariable=self.variable_type,
            values=["attack_duration", "defense_duration", "attacker_strategy", "defender_strategy"],
            state="readonly",
            width=20,
            font=("Arial", 10)
        )
        self.variable_dropdown.pack(side=tk.LEFT)
        self.variable_dropdown.bind('<<ComboboxSelected>>', self._on_variable_type_changed)
        
        # Description (dynamically updated based on variable type)
        self.description_label = tk.Label(
            self.pad_frame,
            text="",
            font=("Arial", 9),
            bg=self.tab_color,
            fg=self.button_fg,
            justify=tk.CENTER
        )
        self.description_label.pack(pady=5)
        self._update_description()
        
        # Scenarios configuration (initially disabled)
        self.config_frame = tk.Frame(self.pad_frame, bg=self.tab_color)
        self.config_frame.pack(fill=tk.BOTH, expand=True, padx=50, pady=20)
        
        # Scenarios frame with scrollbar
        canvas = tk.Canvas(self.config_frame, bg=self.tab_color, highlightthickness=0, height=250)
        scrollbar = ttk.Scrollbar(self.config_frame, orient="vertical", command=canvas.yview)
        
        self.scenarios_frame = tk.Frame(canvas, bg=self.tab_color)
        
        self.scenarios_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scenarios_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Control buttons
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
            pady=3
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            self.button_frame,
            text="Clear All",
            command=self._clear_all,
            bg="#f44336",
            fg="white",
            font=("Arial", 10),
            padx=15,
            pady=3
        ).pack(side=tk.LEFT, padx=5)
        
        # Status
        self.status_label = tk.Label(
            self.pad_frame,
            text="",
            bg=self.tab_color,
            fg=self.button_fg,
            font=("Arial", 10, "bold")
        )
        self.status_label.pack(pady=10)
        
        # Start with scenarios disabled
        self._set_config_state('disabled')
    
    def _on_enabled_changed(self):
        """Handle enable/disable checkbox"""
        if self.enabled_var.get():
            # Enabled - show config and add default scenarios if none exist
            self._set_config_state('normal')
            self.variable_dropdown.config(state="readonly")
            if not self.scenarios:
                self._add_default_scenarios()
            self._update_status()
        else:
            # Disabled - gray out config
            self._set_config_state('disabled')
            self.variable_dropdown.config(state="disabled")
            self._update_status()
    
    def _on_variable_type_changed(self, event=None):
        """Handle variable type dropdown change"""
        # Clear existing scenarios and reload defaults for new type
        self._clear_all()
        self._add_default_scenarios()
        self._update_description()
    
    def _add_default_scenarios(self):
        """Add default scenarios based on variable type"""
        var_type = self.variable_type.get()
        
        if var_type == "attack_duration":
            # Default attack durations: 1h, 3h, 5h
            self._add_scenario_with_values(1.0, 20)
            self._add_scenario_with_values(3.0, 20)
            self._add_scenario_with_values(5.0, 20)
        elif var_type == "defense_duration":
            # Default defense durations: 0.5h, 1h, 2h
            self._add_scenario_with_values(0.5, 20)
            self._add_scenario_with_values(1.0, 20)
            self._add_scenario_with_values(2.0, 20)
        elif var_type == "attacker_strategy":
            # Get available attacker strategies
            strategies = ["greedy", "random"]
            for strategy in strategies:
                self._add_scenario_with_values(strategy, 20)
        elif var_type == "defender_strategy":
            # Get available defender strategies
            strategies = ["reactive", "proactive", "monitoring"]
            for strategy in strategies:
                self._add_scenario_with_values(strategy, 20)
    
    def _update_description(self):
        """Update description based on variable type"""
        var_type = self.variable_type.get()
        
        if var_type == "attack_duration":
            text = "When disabled, simulations use attack action durations from JSON files.\n" \
                   "When enabled, compare different attack action duration scenarios."
        elif var_type == "defense_duration":
            text = "When disabled, simulations use defense action durations from JSON files.\n" \
                   "When enabled, compare different defense action duration scenarios."
        elif var_type == "attacker_strategy":
            text = "When disabled, simulations use attacker strategies from Attacker tab.\n" \
                   "When enabled, compare different attacker strategy scenarios."
        elif var_type == "defender_strategy":
            text = "When disabled, simulations use defender strategies from Defender tab.\n" \
                   "When enabled, compare different defender strategy scenarios."
        else:
            text = "Select a parameter to vary and configure scenarios below."
        
        self.description_label.config(text=text)
    
    def _set_config_state(self, state):
        """Enable or disable the configuration widgets"""
        # State can be 'normal' or 'disabled'
        for widget in self.config_frame.winfo_children():
            if isinstance(widget, (tk.Frame, tk.Canvas)):
                self._set_widget_state_recursive(widget, state)
            else:
                try:
                    widget.config(state=state)
                except:
                    pass
    
    def _set_widget_state_recursive(self, widget, state):
        """Recursively set state of all child widgets"""
        for child in widget.winfo_children():
            if isinstance(child, (tk.Frame, tk.Canvas)):
                self._set_widget_state_recursive(child, state)
            else:
                try:
                    child.config(state=state)
                except:
                    pass
    
    def _add_scenario(self):
        """Add a new scenario row"""
        var_type = self.variable_type.get()
        if var_type == "attack_duration":
            self._add_scenario_with_values(4.0, 20)
        elif var_type == "defense_duration":
            self._add_scenario_with_values(1.5, 20)
        elif var_type == "attacker_strategy":
            self._add_scenario_with_values("greedy", 20)
        elif var_type == "defender_strategy":
            self._add_scenario_with_values("reactive", 20)
    
    def _add_scenario_with_values(self, value, runs=20):
        """Add a scenario with specific values"""
        var_type = self.variable_type.get()
        
        row_frame = tk.Frame(
            self.scenarios_frame,
            bg="white",
            relief=tk.RAISED,
            bd=1
        )
        row_frame.pack(fill=tk.X, pady=2, padx=5)
        
        # Scenario number
        scenario_num = len(self.scenarios) + 1
        tk.Label(
            row_frame,
            text=f"#{scenario_num}",
            bg="white",
            fg=self.button_fg,
            font=("Arial", 10, "bold"),
            width=4
        ).pack(side=tk.LEFT, padx=5, pady=5)
        
        # Value input (changes based on variable type)
        if var_type in ["attack_duration", "defense_duration"]:
            label_text = "Attack Duration (hours):" if var_type == "attack_duration" else "Defense Duration (hours):"
            tk.Label(
                row_frame,
                text=label_text,
                bg="white",
                fg=self.button_fg,
                font=("Arial", 9)
            ).pack(side=tk.LEFT, padx=5)
            
            value_var = tk.StringVar(value=str(value))
            value_entry = tk.Entry(row_frame, textvariable=value_var, width=8, font=("Arial", 9))
            value_entry.pack(side=tk.LEFT, padx=5)
        
        elif var_type == "attacker_strategy":
            tk.Label(
                row_frame,
                text="Attacker Strategy:",
                bg="white",
                fg=self.button_fg,
                font=("Arial", 9)
            ).pack(side=tk.LEFT, padx=5)
            
            value_var = tk.StringVar(value=str(value))
            value_dropdown = ttk.Combobox(
                row_frame,
                textvariable=value_var,
                values=["greedy", "random"],
                state="readonly",
                width=12,
                font=("Arial", 9)
            )
            value_dropdown.pack(side=tk.LEFT, padx=5)
        
        elif var_type == "defender_strategy":
            tk.Label(
                row_frame,
                text="Defender Strategy:",
                bg="white",
                fg=self.button_fg,
                font=("Arial", 9)
            ).pack(side=tk.LEFT, padx=5)
            
            value_var = tk.StringVar(value=str(value))
            value_dropdown = ttk.Combobox(
                row_frame,
                textvariable=value_var,
                values=["reactive", "proactive", "monitoring"],
                state="readonly",
                width=12,
                font=("Arial", 9)
            )
            value_dropdown.pack(side=tk.LEFT, padx=5)
        
        # Runs input
        tk.Label(
            row_frame,
            text="Runs:",
            bg="white",
            fg=self.button_fg,
            font=("Arial", 9)
        ).pack(side=tk.LEFT, padx=(15, 5))
        
        runs_var = tk.StringVar(value=str(runs))
        runs_entry = tk.Entry(row_frame, textvariable=runs_var, width=6, font=("Arial", 9))
        runs_entry.pack(side=tk.LEFT, padx=5)
        
        # Remove button
        remove_btn = tk.Button(
            row_frame,
            text="✕",
            command=lambda: self._remove_scenario(row_frame),
            bg="#d32f2f",
            fg="white",
            font=("Arial", 8, "bold"),
            width=3,
            pady=0
        )
        remove_btn.pack(side=tk.RIGHT, padx=5)
        
        # Store scenario data
        scenario_data = {
            'frame': row_frame,
            'value_var': value_var,
            'runs_var': runs_var
        }
        self.scenarios.append(scenario_data)
        
        # Update status when values change
        value_var.trace_add('write', lambda *args: self._update_status())
        runs_var.trace_add('write', lambda *args: self._update_status())
        
        self._update_status()
    
    def _remove_scenario(self, frame):
        """Remove a scenario row"""
        # Find and remove from list
        self.scenarios = [s for s in self.scenarios if s['frame'] != frame]
        frame.destroy()
        
        # Renumber remaining scenarios
        for i, scenario in enumerate(self.scenarios, 1):
            # Find the label in the frame and update it
            for widget in scenario['frame'].winfo_children():
                if isinstance(widget, tk.Label) and widget.cget('text').startswith('#'):
                    widget.config(text=f"#{i}")
                    break
        
        self._update_status()
    
    def _clear_all(self):
        """Remove all scenarios"""
        for scenario in self.scenarios:
            scenario['frame'].destroy()
        self.scenarios = []
        self._update_status()
    
    def _parse_scenarios(self):
        """Parse all scenario configurations. Returns list of (value, runs) tuples or None if invalid."""
        var_type = self.variable_type.get()
        result = []
        
        for scenario in self.scenarios:
            try:
                value = scenario['value_var'].get()
                runs = int(scenario['runs_var'].get())
                
                if runs <= 0:
                    return None
                
                # Validate based on variable type
                if var_type in ["attack_duration", "defense_duration"]:
                    duration = float(value)
                    if duration <= 0:
                        return None
                    result.append((duration, runs))
                elif var_type == "attacker_strategy":
                    if value not in ["greedy", "random"]:
                        return None
                    result.append((value, runs))
                elif var_type == "defender_strategy":
                    if value not in ["reactive", "proactive", "monitoring"]:
                        return None
                    result.append((value, runs))
                
            except ValueError:
                return None
        
        return result if result else []
    
    def _update_status(self):
        """Update the status label based on current scenarios"""
        if not hasattr(self, 'status_label'):
            return
        
        # Check if scenarios are enabled
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
            
            # Notify parent that scenarios are disabled
            if self.on_scenarios_changed:
                self.on_scenarios_changed([])
            return
            
        scenarios = self._parse_scenarios()
        var_type = self.variable_type.get()
        
        if scenarios is None:
            self.status_label.config(
                text="❌ Invalid input - check values and run counts",
                fg="#d32f2f"
            )
        elif not scenarios:
            self.status_label.config(
                text="⚠️ Enabled but no scenarios configured - add scenarios below",
                fg="#FF9800"
            )
        else:
            total_runs = sum(runs for _, runs in scenarios)
            
            if var_type in ["attack_duration", "defense_duration"]:
                value_str = ", ".join(f"{v}h" for v, _ in scenarios)
                label = "attack duration(s)" if var_type == "attack_duration" else "defense duration(s)"
            elif var_type == "attacker_strategy":
                value_str = ", ".join(f"{v}" for v, _ in scenarios)
                label = "attacker strateg(ies)"
            elif var_type == "defender_strategy":
                value_str = ", ".join(f"{v}" for v, _ in scenarios)
                label = "defender strateg(ies)"
            else:
                value_str = ", ".join(f"{v}" for v, _ in scenarios)
                label = "scenario(s)"
            
            self.status_label.config(
                text=f"✓ {len(scenarios)} {label}: {value_str} | Total runs: {total_runs}",
                fg="#2e7d32"
            )
        
        # Notify parent about scenario changes (only if enabled)
        if self.on_scenarios_changed:
            config = self.get_variables_config()
            self.on_scenarios_changed(config.get('scenarios', []))
    
    def get_variables_config(self):
        """Returns the variables configuration for scenario comparison"""
        # Return empty if disabled
        if not self.enabled_var.get():
            return {}
        
        scenarios = self._parse_scenarios()
        if scenarios is None or not scenarios:
            return {}
        
        var_type = self.variable_type.get()
        
        # Build config based on variable type
        if var_type in ["attack_duration", "defense_duration"]:
            return {
                'variable_type': var_type,
                'scenarios': [
                    {'duration': value, 'runs': runs} 
                    for value, runs in scenarios
                ]
            }
        elif var_type == "attacker_strategy":
            return {
                'variable_type': 'attacker_strategy',
                'scenarios': [
                    {'strategy': value, 'runs': runs} 
                    for value, runs in scenarios
                ]
            }
        elif var_type == "defender_strategy":
            return {
                'variable_type': 'defender_strategy',
                'scenarios': [
                    {'strategy': value, 'runs': runs} 
                    for value, runs in scenarios
                ]
            }
        else:
            return {}

