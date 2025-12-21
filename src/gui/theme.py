class Theme:
    COLORS = {'bg_primary': '#f8f9fa', 'bg_secondary': '#ffffff', 'bg_sidebar': '#e3eaf2', 'accent_primary': '#b5d6fc', 'accent_secondary': '#d0e6fa', 'text_primary': '#22223b', 'text_secondary': '#666666', 'success': '#28a745', 'warning': '#ffc107', 'danger': '#dc3545', 'info': '#17a2b8', 'section_simulation': '#f0fff0', 'section_network': '#f0f8ff', 'section_actors': '#fff8f0', 'section_results': '#f8f0ff', 'input_bg': '#eaf1fb', 'input_border': '#cccccc', 'input_focus': '#007bff'}
    FONTS = {'heading_large': ('Arial', 12, 'bold'), 'heading_medium': ('Arial', 10, 'bold'), 'heading_small': ('Arial', 10, 'bold'), 'body': ('Arial', 9), 'body_small': ('Arial', 8), 'monospace': ('Consolas', 9)}
    SPACING = {'xs': 2, 'sm': 5, 'md': 10, 'lg': 20, 'xl': 50}
    BORDERS = {'none': {'relief': 'flat', 'bd': 0}, 'light': {'relief': 'ridge', 'bd': 1}, 'medium': {'relief': 'ridge', 'bd': 2}, 'heavy': {'relief': 'ridge', 'bd': 3}, 'sunken': {'relief': 'sunken', 'bd': 1}, 'raised': {'relief': 'raised', 'bd': 1}}
    SIZES = {'button_width': 12, 'entry_width': 10, 'entry_wide': 20, 'label_width': 12, 'dropdown_width': 10}

    @classmethod
    def get_theme_colors(cls):
        return {'bg_color': cls.COLORS['bg_primary'], 'tab_color': cls.COLORS['bg_secondary'], 'sidebar_color': cls.COLORS['bg_sidebar'], 'highlight_color': cls.COLORS['accent_primary'], 'button_color': cls.COLORS['accent_secondary'], 'button_fg': cls.COLORS['text_primary']}

    @classmethod
    def get_section_color(cls, section_type):
        section_colors = {'simulation': cls.COLORS['section_simulation'], 'network': cls.COLORS['section_network'], 'attackers': cls.COLORS['section_actors'], 'defenders': cls.COLORS['section_actors'], 'results': cls.COLORS['section_results']}
        return section_colors.get(section_type, cls.COLORS['section_network'])

    @classmethod
    def get_button_style(cls, style_type='default'):
        base_style = {'bg': cls.COLORS['accent_secondary'], 'fg': cls.COLORS['text_primary'], 'activebackground': cls.COLORS['accent_primary'], 'activeforeground': cls.COLORS['text_primary'], 'font': cls.FONTS['body'], 'relief': 'flat', 'bd': 1, 'padx': cls.SPACING['md'], 'pady': cls.SPACING['sm']}
        style_variants = {'primary': {'bg': cls.COLORS['accent_primary'], 'font': cls.FONTS['heading_small']}, 'success': {'bg': cls.COLORS['success'], 'fg': '#ffffff', 'activebackground': '#1e7e34'}, 'danger': {'bg': cls.COLORS['danger'], 'fg': '#ffffff', 'activebackground': '#c82333'}, 'warning': {'bg': cls.COLORS['warning'], 'fg': cls.COLORS['text_primary'], 'activebackground': '#e0a800'}}
        if style_type in style_variants:
            base_style.update(style_variants[style_type])
        return base_style

    @classmethod
    def get_entry_style(cls):
        return {'bg': cls.COLORS['input_bg'], 'fg': cls.COLORS['text_primary'], 'insertbackground': cls.COLORS['text_primary'], 'relief': 'solid', 'bd': 1, 'font': cls.FONTS['body']}

    @classmethod
    def get_label_style(cls, style_type='default'):
        base_style = {'fg': cls.COLORS['text_primary'], 'font': cls.FONTS['body']}
        style_variants = {'heading': {'font': cls.FONTS['heading_medium']}, 'subheading': {'font': cls.FONTS['heading_small']}, 'secondary': {'fg': cls.COLORS['text_secondary'], 'font': cls.FONTS['body_small']}}
        if style_type in style_variants:
            base_style.update(style_variants[style_type])
        return base_style