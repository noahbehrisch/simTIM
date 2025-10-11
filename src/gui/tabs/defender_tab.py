"""
Defender Tab

Handles defender configuration and strategy settings.
"""

import tkinter as tk
from tkinter import ttk
from .base_tab import BaseTab

class DefenderTab(BaseTab):
    def __init__(self, parent, theme_colors):
        """Initialize defender tab."""
        # Lists to track defender entries
        self.defender_entries = []
        self.defender_list = []
        self.defender_entries_frame = None
        
        super().__init__(parent, theme_colors)
    
    def create_widgets(self):
        """Create defender configuration widgets."""
        # Strategy descriptions
        strategy_info = self.create_section_header(
            self.pad_frame, 
            "Defender Strategies:", 
            section_type="defenders"
        )
        
        # Remove the header label since create_section_header already adds it
        self.create_info_label(
            strategy_info, 
            "• Reactive: Responds to detected threats immediately",
            bg_color=self.theme.COLORS['section_actors']
        ).pack(anchor="w", padx=15)
        
        self.create_info_label(
            strategy_info, 
            "• Proactive: Takes preventive measures based on risk assessment",
            bg_color=self.theme.COLORS['section_actors']
        ).pack(anchor="w", padx=15)
        
        self.create_info_label(
            strategy_info, 
            "• Monitoring: Focuses on detection and surveillance",
            bg_color=self.theme.COLORS['section_actors']
        ).pack(anchor="w", padx=15)
        
        # Create unified table frame for both headers and entries
        self.defender_entries_frame = tk.Frame(self.pad_frame, bg=self.tab_color)
        self.defender_entries_frame.pack(fill="both", expand=True, padx=10, pady=(5, 0))
        
        # Configure grid columns to be responsive
        self.defender_entries_frame.grid_columnconfigure(0, weight=2, minsize=100)  # ID
        self.defender_entries_frame.grid_columnconfigure(1, weight=2, minsize=100)  # Strategy  
        self.defender_entries_frame.grid_columnconfigure(2, weight=1, minsize=80)   # Capacity
        self.defender_entries_frame.grid_columnconfigure(3, weight=1, minsize=100)  # Budget
        self.defender_entries_frame.grid_columnconfigure(4, weight=1, minsize=80)   # Actions
        
        # Create header labels in row 0
        headers = ["ID", "Strategy", "Capacity", "Budget ($)", "Actions"]
        for i, text in enumerate(headers):
            label_style = self.theme.get_label_style('subheading')
            label_style.update({
                'bg': self.sidebar_color,
                **self.theme.BORDERS['light']
            })
            
            header_label = tk.Label(self.defender_entries_frame, text=text, **label_style)
            header_label.grid(row=0, column=i, padx=2, pady=2, sticky="ew")
        
        # Add initial defender
        self.add_defender_entry()
        
        # Add defender button (moved below the entries)
        self.create_styled_button(
            self.pad_frame,
            "Add Defender",
            self.add_defender_entry
        ).pack(padx=10, pady=10, anchor="w")
    
    def add_defender_entry(self):
        """Add a new defender entry row."""
        defender_id = len(self.defender_entries) + 1
        row = defender_id  # Grid row index (1-based since row 0 is header)
        
        # ID - column 0
        id_label = tk.Label(
            self.defender_entries_frame, 
            text=f"Defender {defender_id}", 
            bg=self.theme.COLORS['input_bg'], 
            fg=self.button_fg, 
            **self.theme.BORDERS['sunken']
        )
        id_label.grid(row=row, column=0, padx=2, pady=2, sticky="ew")
        
        # Strategy - column 1
        strategy_var = tk.StringVar(value="reactive")
        strategy_dropdown = ttk.Combobox(
            self.defender_entries_frame, 
            textvariable=strategy_var, 
            values=["reactive", "proactive", "monitoring"], 
            state="readonly"
        )
        strategy_dropdown.grid(row=row, column=1, padx=2, pady=2, sticky="ew")
        
        # Capacity - column 2
        capacity_var = tk.StringVar(value="1")
        capacity_entry = self.create_styled_entry(
            self.defender_entries_frame, 
            capacity_var
        )
        capacity_entry.grid(row=row, column=2, padx=2, pady=2, sticky="ew")
        
        # Budget - column 3
        budget_var = tk.StringVar(value="2000")
        budget_entry = self.create_styled_entry(
            self.defender_entries_frame, 
            budget_var
        )
        budget_entry.grid(row=row, column=3, padx=2, pady=2, sticky="ew")
        
        # Remove button - column 4
        remove_btn = self.create_styled_button(
            self.defender_entries_frame, 
            "Remove", 
            lambda: self._remove_defender(defender_id), 
            style_type="danger"
        )
        remove_btn.grid(row=row, column=4, padx=2, pady=2, sticky="ew")
        
        # Store references for later removal
        defender_widgets = {
            'id_label': id_label,
            'strategy_var': strategy_var,
            'strategy_dropdown': strategy_dropdown,
            'capacity_var': capacity_var,
            'capacity_entry': capacity_entry,
            'budget_var': budget_var,
            'budget_entry': budget_entry,
            'remove_btn': remove_btn,
            'row': row
        }
        
        self.defender_entries.append((defender_id, strategy_var, capacity_var, budget_var, defender_widgets))
    
    def _remove_defender(self, defender_id):
        """Remove a defender entry."""
        # Find and remove the entry
        for i, entry in enumerate(self.defender_entries):
            if entry[0] == defender_id:  # defender_id is the first element
                widgets = entry[4]  # widgets dict is the last element
                
                # Destroy all widgets for this defender
                for widget_name, widget in widgets.items():
                    if widget_name != 'row' and hasattr(widget, 'destroy'):
                        widget.destroy()
                
                self.defender_entries.pop(i)
                break
        
        # Rebuild the grid to fix row indices
        self._rebuild_defender_grid()
    
    def _rebuild_defender_grid(self):
        """Rebuild the defender grid after removal to fix row indices."""
        # Clear all widgets from the grid
        for widget in self.defender_entries_frame.winfo_children():
            widget.destroy()
        
        # Store current configurations
        configs = []
        for entry in self.defender_entries:
            config = {
                'strategy': entry[1].get(),
                'capacity': entry[2].get(),
                'budget': entry[3].get()
            }
            configs.append(config)
        
        # Clear entries list
        self.defender_entries.clear()
        
        # Recreate entries with stored configurations
        for config in configs:
            self._add_defender_with_config(config)
    
    def _add_defender_with_config(self, config):
        """Add a defender entry with specific configuration."""
        defender_id = len(self.defender_entries) + 1
        row = defender_id  # Grid row index (1-based since row 0 is header)
        
        # ID - column 0
        id_label = tk.Label(
            self.defender_entries_frame, 
            text=f"Defender {defender_id}", 
            bg=self.theme.COLORS['input_bg'], 
            fg=self.button_fg, 
            **self.theme.BORDERS['sunken']
        )
        id_label.grid(row=row, column=0, padx=2, pady=2, sticky="ew")
        
        # Strategy - column 1
        strategy_var = tk.StringVar(value=config['strategy'])
        strategy_dropdown = ttk.Combobox(
            self.defender_entries_frame, 
            textvariable=strategy_var, 
            values=["reactive", "proactive", "monitoring"], 
            state="readonly"
        )
        strategy_dropdown.grid(row=row, column=1, padx=2, pady=2, sticky="ew")
        
        # Capacity - column 2
        capacity_var = tk.StringVar(value=config['capacity'])
        capacity_entry = self.create_styled_entry(
            self.defender_entries_frame, 
            capacity_var
        )
        capacity_entry.grid(row=row, column=2, padx=2, pady=2, sticky="ew")
        
        # Budget - column 3
        budget_var = tk.StringVar(value=config['budget'])
        budget_entry = self.create_styled_entry(
            self.defender_entries_frame, 
            budget_var
        )
        budget_entry.grid(row=row, column=3, padx=2, pady=2, sticky="ew")
        
        # Remove button - column 4
        remove_btn = self.create_styled_button(
            self.defender_entries_frame, 
            "Remove", 
            lambda: self._remove_defender(defender_id), 
            style_type="danger"
        )
        remove_btn.grid(row=row, column=4, padx=2, pady=2, sticky="ew")
        
        # Store references
        defender_widgets = {
            'id_label': id_label,
            'strategy_var': strategy_var,
            'strategy_dropdown': strategy_dropdown,
            'capacity_var': capacity_var,
            'capacity_entry': capacity_entry,
            'budget_var': budget_var,
            'budget_entry': budget_entry,
            'remove_btn': remove_btn,
            'row': row
        }
        
        self.defender_entries.append((defender_id, strategy_var, capacity_var, budget_var, defender_widgets))
    
    def get_defender_config(self):
        """
        Get the current defender configuration.
        
        Returns:
            list: List of defender configurations
        """
        defenders = []
        for entry in self.defender_entries:
            defender_id, strategy_var, capacity_var, budget_var, frame = entry
            
            # Handle capacity
            try:
                capacity = int(capacity_var.get())
            except ValueError:
                capacity = 2  # fallback
            
            # Handle budget
            try:
                budget = float(budget_var.get())
            except ValueError:
                budget = 2000.0  # fallback
            
            defenders.append({
                'id': f"defender{defender_id}",
                'strategy': strategy_var.get(),
                'capacity': capacity,
                'budget': budget
            })
        
        return defenders
