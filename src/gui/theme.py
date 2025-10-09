"""
simTIM GUI Theme

This file defines the consistent design standards for the simTIM GUI application.
All components should follow these guidelines for a cohesive user experience.
"""

class Theme:
    """
    Centralized theme system for consistent GUI styling.
    """
    
    # Color Palette
    COLORS = {
        # Background colors
        'bg_primary': '#f8f9fa',      # Main background (light gray)
        'bg_secondary': '#ffffff',     # Tab/content background (white)
        'bg_sidebar': '#e3eaf2',      # Sidebar background (light blue-gray)
        
        # Accent colors
        'accent_primary': '#b5d6fc',   # Primary highlight (blue)
        'accent_secondary': '#d0e6fa', # Secondary accent (light blue)
        
        # Text colors
        'text_primary': '#22223b',     # Primary text (dark navy)
        'text_secondary': '#666666',   # Secondary text (gray)
        
        # Status colors
        'success': '#28a745',          # Success/positive actions
        'warning': '#ffc107',          # Warning/caution
        'danger': '#dc3545',           # Error/negative actions
        'info': '#17a2b8',             # Information
        
        # Section colors
        'section_simulation': '#f0fff0',  # Light green for simulation
        'section_network': '#f0f8ff',     # Light blue for network
        'section_actors': '#fff8f0',      # Light orange for actors
        'section_results': '#f8f0ff',     # Light purple for results
        
        # Input colors
        'input_bg': '#eaf1fb',         # Input field background
        'input_border': '#cccccc',     # Input field border
        'input_focus': '#007bff',      # Input field focus border
    }
    
    # Typography (reverted to original fonts)
    FONTS = {
        'heading_large': ('Arial', 12, 'bold'),    # Main headings  
        'heading_medium': ('Arial', 10, 'bold'),   # Section headings
        'heading_small': ('Arial', 10, 'bold'),    # Subsection headings
        'body': ('Arial', 9),                      # Regular text
        'body_small': ('Arial', 8),                # Small text
        'monospace': ('Consolas', 9),              # Code/data display
    }
    
    # Spacing
    SPACING = {
        'xs': 2,    # Very small spacing
        'sm': 5,    # Small spacing
        'md': 10,   # Medium spacing (default)
        'lg': 20,   # Large spacing
        'xl': 50,   # Extra large spacing (tab padding)
    }
    
    # Border styles
    BORDERS = {
        'none': {'relief': 'flat', 'bd': 0},
        'light': {'relief': 'ridge', 'bd': 1},
        'medium': {'relief': 'ridge', 'bd': 2},
        'heavy': {'relief': 'ridge', 'bd': 3},
        'sunken': {'relief': 'sunken', 'bd': 1},
        'raised': {'relief': 'raised', 'bd': 1},
    }
    
    # Component sizes
    SIZES = {
        'button_width': 12,
        'entry_width': 10,
        'entry_wide': 20,
        'label_width': 12,
        'dropdown_width': 10,
    }
    
    @classmethod
    def get_theme_colors(cls):
        """Get theme colors in the format expected by existing components."""
        return {
            'bg_color': cls.COLORS['bg_primary'],
            'tab_color': cls.COLORS['bg_secondary'],
            'sidebar_color': cls.COLORS['bg_sidebar'],
            'highlight_color': cls.COLORS['accent_primary'],
            'button_color': cls.COLORS['accent_secondary'],
            'button_fg': cls.COLORS['text_primary']
        }
    
    @classmethod
    def get_section_color(cls, section_type):
        """Get appropriate section background color."""
        section_colors = {
            'simulation': cls.COLORS['section_simulation'],
            'network': cls.COLORS['section_network'],
            'attackers': cls.COLORS['section_actors'],
            'defenders': cls.COLORS['section_actors'],
            'results': cls.COLORS['section_results'],
        }
        return section_colors.get(section_type, cls.COLORS['section_network'])
    
    @classmethod
    def get_button_style(cls, style_type='default'):
        """Get button styling options."""
        base_style = {
            'bg': cls.COLORS['accent_secondary'],
            'fg': cls.COLORS['text_primary'],
            'activebackground': cls.COLORS['accent_primary'],
            'activeforeground': cls.COLORS['text_primary'],
            'font': cls.FONTS['body'],
            'relief': 'flat',
            'bd': 1,
            'padx': cls.SPACING['md'],
            'pady': cls.SPACING['sm']
        }
        
        style_variants = {
            'primary': {
                'bg': cls.COLORS['accent_primary'],
                'font': cls.FONTS['heading_small']
            },
            'success': {
                'bg': cls.COLORS['success'],
                'fg': '#ffffff',
                'activebackground': '#1e7e34'
            },
            'danger': {
                'bg': cls.COLORS['danger'],
                'fg': '#ffffff',
                'activebackground': '#c82333'
            },
            'warning': {
                'bg': cls.COLORS['warning'],
                'fg': cls.COLORS['text_primary'],
                'activebackground': '#e0a800'
            }
        }
        
        if style_type in style_variants:
            base_style.update(style_variants[style_type])
        
        return base_style
    
    @classmethod
    def get_entry_style(cls):
        """Get entry field styling options."""
        return {
            'bg': cls.COLORS['input_bg'],
            'fg': cls.COLORS['text_primary'],
            'insertbackground': cls.COLORS['text_primary'],
            'relief': 'solid',
            'bd': 1,
            'font': cls.FONTS['body']
        }
    
    @classmethod
    def get_label_style(cls, style_type='default'):
        """Get label styling options."""
        base_style = {
            'fg': cls.COLORS['text_primary'],
            'font': cls.FONTS['body']
        }
        
        style_variants = {
            'heading': {
                'font': cls.FONTS['heading_medium']
            },
            'subheading': {
                'font': cls.FONTS['heading_small']
            },
            'secondary': {
                'fg': cls.COLORS['text_secondary'],
                'font': cls.FONTS['body_small']
            }
        }
        
        if style_type in style_variants:
            base_style.update(style_variants[style_type])
        
        return base_style
