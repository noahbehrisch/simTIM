"""
Variables Tab

Configure variable parameters for simulations
"""

import tkinter as tk
from .base_tab import BaseTab


class VariablesTab(BaseTab):
    def __init__(self, parent, theme_colors):
        super().__init__(parent, theme_colors)
    
    def create_widgets(self):
        """Create the variables tab interface"""
        
        # Title
        title = tk.Label(
            self.pad_frame,
            text="Variable Parameters",
            font=("Arial", 14, "bold"),
            bg=self.tab_color,
            fg=self.button_fg
        )
        title.pack(pady=20)
        
        # Placeholder content
        placeholder = tk.Label(
            self.pad_frame,
            text="Variable parameter configuration will be added here",
            font=("Arial", 12),
            bg=self.tab_color,
            fg=self.button_fg
        )
        placeholder.pack(pady=20)
    
    def get_variables_config(self):
        """
        Get variable parameter configuration.
        Returns empty dict for now (no variables configured).
        """
        return {}
