"""
Defender Tab

Handles defender configuration and strategy settings.
"""

import tkinter as tk
from tkinter import ttk
from .base_tab import BaseTab

class DefenderTab(BaseTab):
    """
    Tab for configuring defenders and their strategies.
    """
    
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
            bg_color="#f0fff0"
        )
        
        # Remove the header label since create_section_header already adds it
        self.create_info_label(
            strategy_info, 
            "• Reactive: Responds to detected threats and vulnerabilities",
            bg_color="#f0fff0"
        ).pack(anchor="w", padx=15)
        
        self.create_info_label(
            strategy_info, 
            "• Proactive: Actively hardens systems and patches vulnerabilities",
            bg_color="#f0fff0"
        ).pack(anchor="w", padx=15)
        
        self.create_info_label(
            strategy_info, 
            "• Monitoring: Focuses on detection and surveillance capabilities",
            bg_color="#f0fff0"
        ).pack(anchor="w", padx=15)
        
        # Create table header
        columns = [
            ("ID", 12),
            ("Strategy", 12),
            ("Capacity", 8),
            ("Budget ($)", 10),
            ("Actions", 8)
        ]
        self.create_table_header(self.pad_frame, columns)
        
        # Add defender button
        self.create_styled_button(
            self.pad_frame,
            "Add Defender",
            self.add_defender_entry
        ).pack(padx=10, pady=10, anchor="w")
        
        # Frame for defender entries
        self.defender_entries_frame = tk.Frame(self.pad_frame, bg=self.tab_color)
        self.defender_entries_frame.pack(fill="both", expand=True)
        
        # Add initial defender
        self.add_defender_entry()
    
    def add_defender_entry(self):
        """Add a new defender entry row."""
        frame = tk.Frame(self.defender_entries_frame, bg=self.tab_color)
        frame.pack(fill="x", padx=10, pady=2)
        
        defender_id = len(self.defender_entries) + 1
        
        # ID
        id_label = tk.Label(
            frame, 
            text=f"Defender {defender_id}", 
            bg="#eaf1fb", 
            fg=self.button_fg, 
            width=12, 
            relief="sunken"
        )
        id_label.grid(row=0, column=0, padx=1, sticky="w")
        
        # Strategy
        strategy_var = tk.StringVar(value="reactive")
        strategy_dropdown = ttk.Combobox(
            frame, 
            textvariable=strategy_var, 
            values=["reactive", "proactive", "monitoring"], 
            state="readonly", 
            width=10
        )
        strategy_dropdown.grid(row=0, column=1, padx=1, sticky="w")
        
        # Capacity
        capacity_var = tk.StringVar(value="2")
        capacity_entry = tk.Entry(
            frame, 
            textvariable=capacity_var, 
            width=6, 
            bg="#eaf1fb", 
            fg=self.button_fg
        )
        capacity_entry.grid(row=0, column=2, padx=1, sticky="w")
        
        # Budget
        budget_var = tk.StringVar(value="2000")
        budget_entry = tk.Entry(
            frame, 
            textvariable=budget_var, 
            width=8, 
            bg="#eaf1fb", 
            fg=self.button_fg
        )
        budget_entry.grid(row=0, column=3, padx=1, sticky="w")
        
        # Remove button
        remove_btn = tk.Button(
            frame, 
            text="Remove", 
            command=lambda: self._remove_defender(frame), 
            bg="#ffcccc", 
            fg=self.button_fg, 
            activebackground="#ff9999", 
            width=6
        )
        remove_btn.grid(row=0, column=4, padx=1, sticky="w")
        
        self.defender_entries.append((defender_id, strategy_var, capacity_var, budget_var, frame))
    
    def _remove_defender(self, frame):
        """Remove a defender entry."""
        # Find and remove the entry
        for i, entry in enumerate(self.defender_entries):
            if entry[4] == frame:  # frame is now the 5th element (index 4)
                self.defender_entries.pop(i)
                frame.destroy()
                break
    
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
