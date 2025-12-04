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
        
        # Description
        self.description_label = tk.Label(
            self.pad_frame,
            text="When disabled, simulations use action durations from JSON files.\n"
                 "When enabled, compare different action duration scenarios.",
            font=("Arial", 9),
            bg=self.tab_color,
            fg=self.button_fg,
            justify=tk.CENTER
        )
        self.description_label.pack(pady=5)
        
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
            if not self.scenarios:
                self._add_scenario_with_values(1.0, 5)
                self._add_scenario_with_values(3.0, 5)
                self._add_scenario_with_values(5.0, 5)
            self._update_status()
        else:
            # Disabled - gray out config
            self._set_config_state('disabled')
            self._update_status()
    
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
        self._add_scenario_with_values(4.0, 5)
    
    def _add_scenario_with_values(self, duration=4.0, runs=5):
        """Add a scenario with specific values"""
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
        
        # Duration input
        tk.Label(
            row_frame,
            text="Duration (hours):",
            bg="white",
            fg=self.button_fg,
            font=("Arial", 9)
        ).pack(side=tk.LEFT, padx=5)
        
        duration_var = tk.StringVar(value=str(duration))
        duration_entry = tk.Entry(row_frame, textvariable=duration_var, width=8, font=("Arial", 9))
        duration_entry.pack(side=tk.LEFT, padx=5)
        
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
            'duration_var': duration_var,
            'runs_var': runs_var
        }
        self.scenarios.append(scenario_data)
        
        # Update status when values change
        duration_var.trace_add('write', lambda *args: self._update_status())
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
        """Parse all scenario configurations. Returns list of (duration, runs) tuples or None if invalid."""
        result = []
        for scenario in self.scenarios:
            try:
                duration = float(scenario['duration_var'].get())
                runs = int(scenario['runs_var'].get())
                if duration <= 0 or runs <= 0:
                    return None
                result.append((duration, runs))
            except ValueError:
                return None
        return result if result else []
    
    def _update_status(self):
        """Update the status label based on current scenarios"""
        if not hasattr(self, 'status_label'):
            return
        
        # Check if scenarios are enabled
        if not self.enabled_var.get():
            self.status_label.config(
                text="Scenario comparison disabled - using default action durations",
                fg=self.button_fg
            )
            # Notify parent that scenarios are disabled
            if self.on_scenarios_changed:
                self.on_scenarios_changed([])
            return
            
        scenarios = self._parse_scenarios()
        if scenarios is None:
            self.status_label.config(
                text="❌ Invalid input - check duration and run values",
                fg="#d32f2f"
            )
        elif not scenarios:
            self.status_label.config(
                text="⚠️ Enabled but no scenarios configured - add scenarios below",
                fg="#FF9800"
            )
        else:
            total_runs = sum(runs for _, runs in scenarios)
            duration_str = ", ".join(f"{d}h" for d, _ in scenarios)
            self.status_label.config(
                text=f"✓ {len(scenarios)} scenario(s): {duration_str} | Total runs: {total_runs}",
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
        
        return {
            'scenarios': [
                {'duration': duration, 'runs': runs} 
                for duration, runs in scenarios
            ]
        }

