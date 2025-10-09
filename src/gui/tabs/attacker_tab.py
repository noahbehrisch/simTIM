"""
Attacker Tab

Handles attacker configuration and strategy settings.
"""

import tkinter as tk
from tkinter import ttk
from .base_tab import BaseTab

class AttackerTab(BaseTab):
    """
    Tab for configuring attackers and their strategies.
    """
    
    def __init__(self, parent, theme_colors):
        """Initialize attacker tab."""
        # Lists to track attacker entries
        self.attacker_entries = []
        self.attacker_list = []
        self.attacker_entries_frame = None
        
        super().__init__(parent, theme_colors)
    
    def create_widgets(self):
        """Create attacker configuration widgets."""
        # Strategy descriptions
        strategy_info = self.create_section_header(
            self.pad_frame, 
            "Attacker Strategies:", 
            section_type="attackers"
        )
        
        # Remove the header label since create_section_header already adds it
        self.create_info_label(
            strategy_info, 
            "• Greedy: Chooses actions with highest expected gain",
            bg_color=self.theme.COLORS['section_actors']
        ).pack(anchor="w", padx=15)
        
        self.create_info_label(
            strategy_info, 
            "• Random: Selects valid actions randomly",
            bg_color=self.theme.COLORS['section_actors']
        ).pack(anchor="w", padx=15)
        
        # Create unified table frame for both headers and entries
        self.attacker_entries_frame = tk.Frame(self.pad_frame, bg=self.tab_color)
        self.attacker_entries_frame.pack(fill="both", expand=True, padx=10, pady=(5, 0))
        
        # Configure grid columns to be responsive
        self.attacker_entries_frame.grid_columnconfigure(0, weight=2, minsize=100)  # ID
        self.attacker_entries_frame.grid_columnconfigure(1, weight=2, minsize=100)  # Strategy  
        self.attacker_entries_frame.grid_columnconfigure(2, weight=1, minsize=80)   # Capacity
        self.attacker_entries_frame.grid_columnconfigure(3, weight=0, minsize=40)   # ∞ checkbox
        self.attacker_entries_frame.grid_columnconfigure(4, weight=1, minsize=100)  # Budget
        self.attacker_entries_frame.grid_columnconfigure(5, weight=1, minsize=80)   # Actions
        
        # Create header labels in row 0
        headers = ["ID", "Strategy", "Capacity", "∞", "Budget ($)", "Actions"]
        for i, text in enumerate(headers):
            label_style = self.theme.get_label_style('subheading')
            label_style.update({
                'bg': self.sidebar_color,
                **self.theme.BORDERS['light']
            })
            
            header_label = tk.Label(self.attacker_entries_frame, text=text, **label_style)
            header_label.grid(row=0, column=i, padx=2, pady=2, sticky="ew")
        self.attacker_entries_frame.grid_columnconfigure(5, weight=1, minsize=80)   # Actions
        
        # Add initial attacker
        self.add_attacker_entry()
        
        # Add attacker button (moved below the entries)
        self.create_styled_button(
            self.pad_frame,
            "Add Attacker",
            self.add_attacker_entry
        ).pack(padx=10, pady=10, anchor="w")
    
    def add_attacker_entry(self):
        """Add a new attacker entry row."""
        attacker_id = len(self.attacker_entries) + 1
        row = attacker_id  # Grid row index (1-based since row 0 is header)
        
        # ID - column 0
        id_label = tk.Label(
            self.attacker_entries_frame, 
            text=f"Attacker {attacker_id}", 
            bg=self.theme.COLORS['input_bg'], 
            fg=self.button_fg, 
            **self.theme.BORDERS['sunken']
        )
        id_label.grid(row=row, column=0, padx=2, pady=2, sticky="ew")
        
        # Strategy - column 1
        strategy_var = tk.StringVar(value="greedy")
        strategy_dropdown = ttk.Combobox(
            self.attacker_entries_frame, 
            textvariable=strategy_var, 
            values=["greedy", "random"], 
            state="readonly"
        )
        strategy_dropdown.grid(row=row, column=1, padx=2, pady=2, sticky="ew")
        
        # Capacity - column 2
        capacity_var = tk.StringVar(value="3")
        capacity_entry = self.create_styled_entry(
            self.attacker_entries_frame, 
            capacity_var
        )
        capacity_entry.grid(row=row, column=2, padx=2, pady=2, sticky="ew")
        
        # Infinite capacity checkbox - column 3
        infinite_var = tk.BooleanVar(value=True)
        infinite_check = tk.Checkbutton(
            self.attacker_entries_frame, 
            text="∞", 
            variable=infinite_var, 
            bg=self.tab_color, 
            fg=self.button_fg,
            command=lambda: self._toggle_capacity(capacity_entry, infinite_var)
        )
        infinite_check.grid(row=row, column=3, padx=2, pady=2, sticky="ew")
        
        # Disable capacity entry initially since infinite is checked
        capacity_entry.config(state="disabled")
        
        # Budget - column 4
        budget_var = tk.StringVar(value="1000")
        budget_entry = self.create_styled_entry(
            self.attacker_entries_frame, 
            budget_var
        )
        budget_entry.grid(row=row, column=4, padx=2, pady=2, sticky="ew")
        
        # Remove button - column 5
        remove_btn = self.create_styled_button(
            self.attacker_entries_frame, 
            "Remove", 
            lambda: self._remove_attacker(attacker_id), 
            style_type="danger"
        )
        remove_btn.grid(row=row, column=5, padx=2, pady=2, sticky="ew")
        
        # Store references for later removal
        attacker_widgets = {
            'id_label': id_label,
            'strategy_var': strategy_var,
            'strategy_dropdown': strategy_dropdown,
            'capacity_var': capacity_var,
            'capacity_entry': capacity_entry,
            'infinite_var': infinite_var,
            'infinite_check': infinite_check,
            'budget_var': budget_var,
            'budget_entry': budget_entry,
            'remove_btn': remove_btn,
            'row': row
        }
        
        self.attacker_entries.append((attacker_id, strategy_var, capacity_var, infinite_var, budget_var, attacker_widgets))
    
    def _toggle_capacity(self, capacity_entry, infinite_var):
        """Toggle capacity entry state based on infinite checkbox."""
        if infinite_var.get():
            capacity_entry.config(state="disabled")
        else:
            capacity_entry.config(state="normal")
    
    def _remove_attacker(self, attacker_id):
        """Remove an attacker entry."""
        # Find and remove the entry
        for i, entry in enumerate(self.attacker_entries):
            if entry[0] == attacker_id:  # attacker_id is the first element
                widgets = entry[5]  # widgets dict is the last element
                
                # Destroy all widgets for this attacker
                for widget_name, widget in widgets.items():
                    if widget_name != 'row' and hasattr(widget, 'destroy'):
                        widget.destroy()
                
                self.attacker_entries.pop(i)
                break
        
        # Rebuild the grid to fix row indices
        self._rebuild_attacker_grid()
    
    def _rebuild_attacker_grid(self):
        """Rebuild the attacker grid after removal to fix row indices."""
        # Clear all widgets from the grid
        for widget in self.attacker_entries_frame.winfo_children():
            widget.destroy()
        
        # Store current configurations
        configs = []
        for entry in self.attacker_entries:
            config = {
                'strategy': entry[1].get(),
                'capacity': entry[2].get(),
                'infinite': entry[3].get(),
                'budget': entry[4].get()
            }
            configs.append(config)
        
        # Clear entries list
        self.attacker_entries.clear()
        
        # Recreate entries with stored configurations
        for config in configs:
            self._add_attacker_with_config(config)
    
    def _add_attacker_with_config(self, config):
        """Add an attacker entry with specific configuration."""
        attacker_id = len(self.attacker_entries) + 1
        row = attacker_id  # Grid row index (1-based since row 0 is header)
        
        # ID - column 0
        id_label = tk.Label(
            self.attacker_entries_frame, 
            text=f"Attacker {attacker_id}", 
            bg=self.theme.COLORS['input_bg'], 
            fg=self.button_fg, 
            **self.theme.BORDERS['sunken']
        )
        id_label.grid(row=row, column=0, padx=2, pady=2, sticky="ew")
        
        # Strategy - column 1
        strategy_var = tk.StringVar(value=config['strategy'])
        strategy_dropdown = ttk.Combobox(
            self.attacker_entries_frame, 
            textvariable=strategy_var, 
            values=["greedy", "random"], 
            state="readonly"
        )
        strategy_dropdown.grid(row=row, column=1, padx=2, pady=2, sticky="ew")
        
        # Capacity - column 2
        capacity_var = tk.StringVar(value=config['capacity'])
        capacity_entry = self.create_styled_entry(
            self.attacker_entries_frame, 
            capacity_var
        )
        capacity_entry.grid(row=row, column=2, padx=2, pady=2, sticky="ew")
        
        # Infinite capacity checkbox - column 3
        infinite_var = tk.BooleanVar(value=config['infinite'])
        infinite_check = tk.Checkbutton(
            self.attacker_entries_frame, 
            text="∞", 
            variable=infinite_var, 
            bg=self.tab_color, 
            fg=self.button_fg,
            command=lambda: self._toggle_capacity(capacity_entry, infinite_var)
        )
        infinite_check.grid(row=row, column=3, padx=2, pady=2, sticky="ew")
        
        # Set initial state
        if infinite_var.get():
            capacity_entry.config(state="disabled")
        else:
            capacity_entry.config(state="normal")
        
        # Budget - column 4
        budget_var = tk.StringVar(value=config['budget'])
        budget_entry = self.create_styled_entry(
            self.attacker_entries_frame, 
            budget_var
        )
        budget_entry.grid(row=row, column=4, padx=2, pady=2, sticky="ew")
        
        # Remove button - column 5
        remove_btn = self.create_styled_button(
            self.attacker_entries_frame, 
            "Remove", 
            lambda: self._remove_attacker(attacker_id), 
            style_type="danger"
        )
        remove_btn.grid(row=row, column=5, padx=2, pady=2, sticky="ew")
        
        # Store references
        attacker_widgets = {
            'id_label': id_label,
            'strategy_var': strategy_var,
            'strategy_dropdown': strategy_dropdown,
            'capacity_var': capacity_var,
            'capacity_entry': capacity_entry,
            'infinite_var': infinite_var,
            'infinite_check': infinite_check,
            'budget_var': budget_var,
            'budget_entry': budget_entry,
            'remove_btn': remove_btn,
            'row': row
        }
        
        self.attacker_entries.append((attacker_id, strategy_var, capacity_var, infinite_var, budget_var, attacker_widgets))
    
    def get_attacker_config(self):
        """
        Get the current attacker configuration.
        
        Returns:
            list: List of attacker configurations
        """
        attackers = []
        for entry in self.attacker_entries:
            attacker_id, strategy_var, capacity_var, infinite_var, budget_var, frame = entry
            
            # Handle infinite capacity
            if infinite_var.get():
                capacity = float('inf')
            else:
                try:
                    capacity = int(capacity_var.get())
                except ValueError:
                    capacity = 3  # fallback
            
            # Handle budget
            try:
                budget = float(budget_var.get())
            except ValueError:
                budget = 1000.0  # fallback
            
            attackers.append({
                'id': f"attacker{attacker_id}",
                'strategy': strategy_var.get(),
                'capacity': capacity,
                'budget': budget
            })
        
        return attackers
