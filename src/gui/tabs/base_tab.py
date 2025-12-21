import tkinter as tk
from tkinter import ttk
from ..theme import Theme

class BaseTab:

    def __init__(self, parent, theme_colors):
        self.parent = parent
        self.theme_colors = theme_colors
        self.theme = Theme()
        self.bg_color = theme_colors.get('bg_color', self.theme.COLORS['bg_primary'])
        self.tab_color = theme_colors.get('tab_color', self.theme.COLORS['bg_secondary'])
        self.sidebar_color = theme_colors.get('sidebar_color', self.theme.COLORS['bg_sidebar'])
        self.highlight_color = theme_colors.get('highlight_color', self.theme.COLORS['accent_primary'])
        self.button_color = theme_colors.get('button_color', self.theme.COLORS['accent_secondary'])
        self.button_fg = theme_colors.get('button_fg', self.theme.COLORS['text_primary'])
        self.frame = tk.Frame(parent, bg=self.tab_color)
        self.frame.grid(row=1, column=1, sticky='nswe')
        self.frame.grid_remove()
        self.frame.grid_propagate(False)
        self.pad_frame = tk.Frame(self.frame, padx=self.theme.SPACING['xl'], pady=self.theme.SPACING['xl'], bg=self.tab_color)
        self.pad_frame.pack(expand=True, fill='both')
        self.create_widgets()

    def create_widgets(self):
        raise NotImplementedError('Subclasses must implement create_widgets()')

    def show(self):
        self.frame.grid()

    def hide(self):
        self.frame.grid_remove()

    def create_section_header(self, parent, text, section_type=None, bg_color=None):
        if bg_color:
            bg = bg_color
        elif section_type:
            bg = self.theme.get_section_color(section_type)
        else:
            bg = self.theme.COLORS['section_network']
        header_frame = tk.Frame(parent, bg=bg, **self.theme.BORDERS['light'])
        header_frame.pack(fill='x', padx=self.theme.SPACING['md'], pady=self.theme.SPACING['sm'])
        label_style = self.theme.get_label_style('subheading')
        label_style['bg'] = bg
        tk.Label(header_frame, text=text, **label_style).pack(anchor='w', padx=self.theme.SPACING['sm'])
        return header_frame

    def create_info_label(self, parent, text, bg_color=None):
        bg = bg_color or self.theme.COLORS['section_network']
        label_style = self.theme.get_label_style('secondary')
        label_style['bg'] = bg
        return tk.Label(parent, text=text, **label_style)

    def create_styled_button(self, parent, text, command, style_type='default', **kwargs):
        button_style = self.theme.get_button_style(style_type)
        button_style.update(kwargs)
        return tk.Button(parent, text=text, command=command, **button_style)

    def create_styled_entry(self, parent, textvariable, width=None, **kwargs):
        entry_style = self.theme.get_entry_style()
        if width:
            entry_style['width'] = width
        else:
            entry_style['width'] = self.theme.SIZES['entry_width']
        entry_style.update(kwargs)
        return tk.Entry(parent, textvariable=textvariable, **entry_style)

    def create_styled_label(self, parent, text, style_type='default', **kwargs):
        label_style = self.theme.get_label_style(style_type)
        label_style.update(kwargs)
        return tk.Label(parent, text=text, **label_style)

    def create_table_header(self, parent, columns):
        header_frame = tk.Frame(parent, bg=self.tab_color)
        header_frame.pack(fill='x', padx=self.theme.SPACING['md'], pady=self.theme.SPACING['sm'])
        for i, (text, width) in enumerate(columns):
            label_style = self.theme.get_label_style('subheading')
            label_style.update({'bg': self.sidebar_color, 'width': width, **self.theme.BORDERS['light']})
            tk.Label(header_frame, text=text, **label_style).grid(row=0, column=i, padx=1)
        return header_frame