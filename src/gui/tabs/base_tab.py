"""
Base Tab Class

Provides common functionality for all GUI tabs.
"""

import tkinter as tk
from tkinter import ttk

class BaseTab:
    """
    Base class for all GUI tabs providing common functionality.
    """
    
    def __init__(self, parent, theme_colors):
        """
        Initialize base tab.
        
        Args:
            parent: Parent widget (usually the main app)
            theme_colors: Dictionary containing theme colors
        """
        self.parent = parent
        self.theme_colors = theme_colors
        
        # Extract theme colors
        self.bg_color = theme_colors.get('bg_color', '#f8f9fa')
        self.tab_color = theme_colors.get('tab_color', '#ffffff')
        self.sidebar_color = theme_colors.get('sidebar_color', '#e3eaf2')
        self.highlight_color = theme_colors.get('highlight_color', '#b5d6fc')
        self.button_color = theme_colors.get('button_color', '#d0e6fa')
        self.button_fg = theme_colors.get('button_fg', '#22223b')
        
        # Create the main frame
        self.frame = tk.Frame(parent, bg=self.tab_color)
        self.frame.grid(row=1, column=1, sticky="nswe")
        self.frame.grid_remove()  # Initially hidden
        self.frame.grid_propagate(False)
        
        # Create padded inner frame
        self.pad_frame = tk.Frame(self.frame, padx=50, pady=50, bg=self.tab_color)
        self.pad_frame.pack(expand=True, fill="both")
        
        # Initialize tab content (to be overridden by subclasses)
        self.create_widgets()
    
    def create_widgets(self):
        """
        Create tab-specific widgets.
        Must be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement create_widgets()")
    
    def show(self):
        """Show this tab."""
        self.frame.grid()
    
    def hide(self):
        """Hide this tab."""
        self.frame.grid_remove()
    
    def create_section_header(self, parent, text, bg_color=None):
        """
        Create a styled section header.
        
        Args:
            parent: Parent widget
            text: Header text
            bg_color: Background color (defaults to light blue)
            
        Returns:
            Header frame widget
        """
        bg = bg_color or "#f0f8ff"
        header_frame = tk.Frame(parent, bg=bg, relief="ridge", bd=1)
        header_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Label(
            header_frame, 
            text=text, 
            bg=bg, 
            fg=self.button_fg, 
            font=("Arial", 10, "bold")
        ).pack(anchor="w", padx=5)
        
        return header_frame
    
    def create_info_label(self, parent, text, bg_color=None):
        """
        Create an informational label with consistent styling.
        
        Args:
            parent: Parent widget
            text: Label text
            bg_color: Background color
            
        Returns:
            Label widget
        """
        bg = bg_color or "#f0f8ff"
        return tk.Label(
            parent,
            text=text,
            bg=bg,
            fg=self.button_fg,
            font=("Arial", 9)
        )
    
    def create_styled_button(self, parent, text, command, **kwargs):
        """
        Create a button with consistent styling.
        
        Args:
            parent: Parent widget
            text: Button text
            command: Button command
            **kwargs: Additional button options
            
        Returns:
            Button widget
        """
        default_options = {
            'bg': self.button_color,
            'fg': self.button_fg,
            'activebackground': self.highlight_color
        }
        default_options.update(kwargs)
        
        return tk.Button(parent, text=text, command=command, **default_options)
    
    def create_styled_entry(self, parent, textvariable, width=10, **kwargs):
        """
        Create an entry widget with consistent styling.
        
        Args:
            parent: Parent widget
            textvariable: Tkinter variable
            width: Entry width
            **kwargs: Additional entry options
            
        Returns:
            Entry widget
        """
        default_options = {
            'width': width,
            'bg': '#eaf1fb',
            'fg': self.button_fg,
            'insertbackground': self.button_fg
        }
        default_options.update(kwargs)
        
        return tk.Entry(parent, textvariable=textvariable, **default_options)
    
    def create_table_header(self, parent, columns):
        """
        Create a table header with styled column labels.
        
        Args:
            parent: Parent widget
            columns: List of (text, width) tuples
            
        Returns:
            Header frame widget
        """
        header_frame = tk.Frame(parent, bg=self.tab_color)
        header_frame.pack(fill="x", padx=10, pady=5)
        
        for i, (text, width) in enumerate(columns):
            tk.Label(
                header_frame,
                text=text,
                bg=self.sidebar_color,
                fg=self.button_fg,
                width=width,
                relief="ridge"
            ).grid(row=0, column=i, padx=1)
        
        return header_frame
