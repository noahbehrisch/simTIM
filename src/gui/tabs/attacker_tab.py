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
            bg_color="#f0f8ff"
        )
        
        # Remove the header label since create_section_header already adds it
        self.create_info_label(
            strategy_info, 
            "• Greedy: Chooses actions with highest expected gain",
            bg_color="#f0f8ff"
        ).pack(anchor="w", padx=15)
        
        self.create_info_label(
            strategy_info, 
            "• Random: Selects valid actions randomly",
            bg_color="#f0f8ff"
        ).pack(anchor="w", padx=15)
        
        # Create table header
        columns = [
            ("ID", 12),
            ("Strategy", 12),
            ("Capacity", 8),
            ("∞", 6),
            ("Budget ($)", 10),
            ("Actions", 8)
        ]
        self.create_table_header(self.pad_frame, columns)
        
        # Add attacker button
        self.create_styled_button(
            self.pad_frame,
            "Add Attacker",
            self.add_attacker_entry
        ).pack(padx=10, pady=10, anchor="w")
        
        # Frame for attacker entries
        self.attacker_entries_frame = tk.Frame(self.pad_frame, bg=self.tab_color)
        self.attacker_entries_frame.pack(fill="both", expand=True)
        
        # Add initial attacker
        self.add_attacker_entry()
    
    def add_attacker_entry(self):
        """Add a new attacker entry row."""
        frame = tk.Frame(self.attacker_entries_frame, bg=self.tab_color)
        frame.pack(fill="x", padx=10, pady=2)
        
        attacker_id = len(self.attacker_entries) + 1
        
        # ID
        id_label = tk.Label(
            frame, 
            text=f"Attacker {attacker_id}", 
            bg="#eaf1fb", 
            fg=self.button_fg, 
            width=12, 
            relief="sunken"
        )
        id_label.grid(row=0, column=0, padx=1, sticky="w")
        
        # Strategy
        strategy_var = tk.StringVar(value="greedy")
        strategy_dropdown = ttk.Combobox(
            frame, 
            textvariable=strategy_var, 
            values=["greedy", "random"], 
            state="readonly", 
            width=10
        )
        strategy_dropdown.grid(row=0, column=1, padx=1, sticky="w")
        
        # Capacity
        capacity_var = tk.StringVar(value="3")
        capacity_entry = tk.Entry(
            frame, 
            textvariable=capacity_var, 
            width=6, 
            bg="#eaf1fb", 
            fg=self.button_fg
        )
        capacity_entry.grid(row=0, column=2, padx=1, sticky="w")
        
        # Infinite capacity checkbox
        infinite_var = tk.BooleanVar(value=False)
        infinite_check = tk.Checkbutton(
            frame, 
            text="", 
            variable=infinite_var, 
            bg=self.tab_color, 
            fg=self.button_fg,
            command=lambda: self._toggle_capacity(capacity_entry, infinite_var)
        )
        infinite_check.grid(row=0, column=3, padx=1, sticky="w")
        
        # Budget
        budget_var = tk.StringVar(value="1000")
        budget_entry = tk.Entry(
            frame, 
            textvariable=budget_var, 
            width=8, 
            bg="#eaf1fb", 
            fg=self.button_fg
        )
        budget_entry.grid(row=0, column=4, padx=1, sticky="w")
        
        # Remove button
        remove_btn = tk.Button(
            frame, 
            text="Remove", 
            command=lambda: self._remove_attacker(frame), 
            bg="#ffcccc", 
            fg=self.button_fg, 
            activebackground="#ff9999", 
            width=6
        )
        remove_btn.grid(row=0, column=5, padx=1, sticky="w")
        
        self.attacker_entries.append((attacker_id, strategy_var, capacity_var, infinite_var, budget_var, frame))
    
    def _toggle_capacity(self, capacity_entry, infinite_var):
        """Toggle capacity entry state based on infinite checkbox."""
        if infinite_var.get():
            capacity_entry.config(state="disabled")
        else:
            capacity_entry.config(state="normal")
    
    def _remove_attacker(self, frame):
        """Remove an attacker entry."""
        # Find and remove the entry
        for i, entry in enumerate(self.attacker_entries):
            if entry[5] == frame:  # frame is the last element
                self.attacker_entries.pop(i)
                frame.destroy()
                break
    
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
