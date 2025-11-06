"""
Action Tab

GUI tab for configuring and managing actions in the simulation.
"""

import tkinter as tk
from tkinter import ttk
import os
import json
from .base_tab import BaseTab


class ActionTab(BaseTab):
    """
    Tab for configuring actions in the simulation.
    """
    
    def __init__(self, parent, theme_colors):
        """
        Initialize action tab.
        
        Args:
            parent: Parent widget (usually the main app)
            theme_colors: Dictionary containing theme colors
        """
        # Initialize action states (all enabled by default)
        self.action_states = {}  # {action_name: BooleanVar}
        self.attack_actions = []
        self.defense_actions = []
        self.attack_canvas = None
        self.defense_canvas = None
        
        super().__init__(parent, theme_colors)
        
    def create_widgets(self):
        """
        Create action tab widgets.
        """
        # Create main heading
        self.create_styled_label(
            self.pad_frame,
            "Actions Configuration",
            style_type='heading'
        ).pack(anchor="w", pady=(0, self.theme.SPACING['lg']))
        
        # Create info label
        info_label = self.create_styled_label(
            self.pad_frame,
            "Enable or disable actions for the simulation. Disabled actions will not be available to actors.",
            style_type='secondary'
        )
        info_label.pack(anchor="w", pady=(0, self.theme.SPACING['md']))
        
        # Create main container with two columns
        container = tk.Frame(self.pad_frame, bg=self.tab_color)
        container.pack(fill="both", expand=True, pady=self.theme.SPACING['md'])
        
        # Configure grid columns
        container.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=1)
        
        # Create Attack Actions Section (Left Column)
        self._create_attack_section(container)
        
        # Create Defense Actions Section (Right Column)
        self._create_defense_section(container)
        
        # Create control buttons at the bottom
        self._create_control_buttons()
        
    def _create_attack_section(self, parent):
        """Create the attack actions section."""
        attack_frame = tk.Frame(parent, bg=self.tab_color)
        attack_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        
        # Section header
        header = self.create_section_header(attack_frame, "Attack Actions", section_type="attacker")
        
        # Scan for attack actions
        self.attack_actions = self._scan_actions("attacks")
        
        # Create scrollable frame for attack actions
        scroll_frame, canvas = self._create_scrollable_frame(attack_frame)
        self.attack_canvas = canvas
        
        # Add checkboxes for each attack action
        for action_name, action_data in self.attack_actions:
            self._create_action_checkbox(scroll_frame, action_name, action_data, "attack")
            
    def _create_defense_section(self, parent):
        """Create the defense actions section."""
        defense_frame = tk.Frame(parent, bg=self.tab_color)
        defense_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        
        # Section header
        header = self.create_section_header(defense_frame, "Defense Actions", section_type="defender")
        
        # Scan for defense actions
        self.defense_actions = self._scan_actions("defenses")
        
        # Create scrollable frame for defense actions
        scroll_frame, canvas = self._create_scrollable_frame(defense_frame)
        self.defense_canvas = canvas
        
        # Add checkboxes for each defense action
        for action_name, action_data in self.defense_actions:
            self._create_action_checkbox(scroll_frame, action_name, action_data, "defense")
            
    def _scan_actions(self, action_type):
        """
        Scan the action library directory for available actions.
        
        Args:
            action_type: "attacks" or "defenses"
            
        Returns:
            List of tuples: (action_name, action_data)
        """
        actions = []
        
        # Get the actions directory
        actions_dir = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__), 
                '..', '..', 
                'actions', 
                'library',
                action_type
            )
        )
        
        if not os.path.exists(actions_dir):
            return actions
            
        # Get all JSON files in the directory
        try:
            json_files = [f for f in os.listdir(actions_dir) if f.endswith('.json')]
            
            for json_file in sorted(json_files):
                file_path = os.path.join(actions_dir, json_file)
                try:
                    with open(file_path, 'r') as f:
                        action_data = json.load(f)
                        action_name = action_data.get('name', json_file[:-5])
                        actions.append((action_name, action_data))
                except Exception as e:
                    print(f"Warning: Could not load action from {json_file}: {e}")
                    
        except Exception as e:
            print(f"Error scanning {action_type} directory: {e}")
            
        return actions
    
    def _create_scrollable_frame(self, parent):
        """Create a scrollable frame for action checkboxes."""
        # Create canvas and scrollbar
        canvas = tk.Canvas(parent, bg=self.tab_color, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.tab_color)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="right", fill="y")
        
        return scrollable_frame, canvas
    
    def _bind_to_mousewheel(self, widget, canvas):
        """Bind mousewheel event to widget and all its children recursively."""
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        widget.bind("<MouseWheel>", _on_mousewheel)
        
        # Recursively bind to all children
        for child in widget.winfo_children():
            self._bind_to_mousewheel(child, canvas)
    
    def _create_action_checkbox(self, parent, action_name, action_data, action_category):
        """
        Create a checkbox for an action with its details.
        
        Args:
            parent: Parent frame
            action_name: Name of the action
            action_data: Action data dictionary
            action_category: "attack" or "defense"
        """
        # Create frame for this action
        action_frame = tk.Frame(parent, bg=self.tab_color)
        action_frame.pack(fill="x", padx=5, pady=3)
        
        # Create checkbox variable
        if action_name not in self.action_states:
            self.action_states[action_name] = tk.BooleanVar(value=True)
        
        # Create checkbox
        checkbox = tk.Checkbutton(
            action_frame,
            text=action_name,
            variable=self.action_states[action_name],
            bg=self.tab_color,
            fg=self.theme.COLORS['text_primary'],
            selectcolor=self.theme.COLORS['input_bg'],
            font=self.theme.FONTS['body'],
            anchor="w"
        )
        checkbox.pack(side="left", fill="x", expand=True)
        
        return action_frame
        
    def _create_control_buttons(self):
        """Create control buttons for bulk operations."""
        button_frame = tk.Frame(self.pad_frame, bg=self.tab_color)
        button_frame.pack(fill="x", pady=self.theme.SPACING['md'])
        
        # Enable All Attacks button
        enable_attacks_btn = tk.Button(
            button_frame,
            text="Enable All Attacks",
            command=lambda: self._set_all_actions(True, "attack"),
            bg=self.theme.COLORS['accent_secondary'],
            fg=self.theme.COLORS['text_primary'],
            font=self.theme.FONTS['body'],
            padx=15,
            pady=5,
            cursor="hand2"
        )
        enable_attacks_btn.pack(side="left", padx=5)
        
        # Disable All Attacks button
        disable_attacks_btn = tk.Button(
            button_frame,
            text="Disable All Attacks",
            command=lambda: self._set_all_actions(False, "attack"),
            bg=self.theme.COLORS['accent_secondary'],
            fg=self.theme.COLORS['text_primary'],
            font=self.theme.FONTS['body'],
            padx=15,
            pady=5,
            cursor="hand2"
        )
        disable_attacks_btn.pack(side="left", padx=5)
        
        # Enable All Defenses button
        enable_defenses_btn = tk.Button(
            button_frame,
            text="Enable All Defenses",
            command=lambda: self._set_all_actions(True, "defense"),
            bg=self.theme.COLORS['accent_secondary'],
            fg=self.theme.COLORS['text_primary'],
            font=self.theme.FONTS['body'],
            padx=15,
            pady=5,
            cursor="hand2"
        )
        enable_defenses_btn.pack(side="left", padx=5)
        
        # Disable All Defenses button
        disable_defenses_btn = tk.Button(
            button_frame,
            text="Disable All Defenses",
            command=lambda: self._set_all_actions(False, "defense"),
            bg=self.theme.COLORS['accent_secondary'],
            fg=self.theme.COLORS['text_primary'],
            font=self.theme.FONTS['body'],
            padx=15,
            pady=5,
            cursor="hand2"
        )
        disable_defenses_btn.pack(side="left", padx=5)
        
    def _set_all_actions(self, enabled, action_category):
        """
        Enable or disable all actions of a specific category.
        
        Args:
            enabled: True to enable, False to disable
            action_category: "attack" or "defense"
        """
        actions_list = self.attack_actions if action_category == "attack" else self.defense_actions
        
        for action_name, _ in actions_list:
            if action_name in self.action_states:
                self.action_states[action_name].set(enabled)
    
    def get_enabled_actions(self):
        """
        Get lists of enabled attack and defense actions.
        
        Returns:
            dict: {'attack_actions': [...], 'defense_actions': [...]}
        """
        enabled_attacks = [
            action_name for action_name, _ in self.attack_actions 
            if self.action_states.get(action_name, tk.BooleanVar(value=True)).get()
        ]
        
        enabled_defenses = [
            action_name for action_name, _ in self.defense_actions 
            if self.action_states.get(action_name, tk.BooleanVar(value=True)).get()
        ]
        
        return {
            'attack_actions': enabled_attacks,
            'defense_actions': enabled_defenses
        }
