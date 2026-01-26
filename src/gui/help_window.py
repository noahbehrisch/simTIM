import tkinter as tk
from tkinter import scrolledtext

from src.gui.help_content import HELP_CONTENT
from src.gui.theme import Theme


class HelpWindow(tk.Toplevel):
    def __init__(self, parent, tab_name=None):
        super().__init__(parent)
        self.parent = parent
        self.tab_name = tab_name or "Simulation"
        self.theme = Theme()
        self.title(f"Help - {self.tab_name}")
        self.geometry("700x600")
        self.configure(bg=self.theme.COLORS["bg_primary"])
        main_frame = tk.Frame(self, bg=self.theme.COLORS["bg_primary"])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        title_label = tk.Label(
            main_frame,
            text=HELP_CONTENT[self.tab_name]["title"],
            font=self.theme.FONTS["heading_large"],
            bg=self.theme.COLORS["bg_primary"],
            fg=self.theme.COLORS["text_primary"],
        )
        title_label.pack(pady=(0, 10))
        text_frame = tk.Frame(main_frame, bg=self.theme.COLORS["bg_primary"])
        text_frame.pack(fill=tk.BOTH, expand=True)
        self.text_widget = scrolledtext.ScrolledText(
            text_frame,
            wrap=tk.WORD,
            width=80,
            height=30,
            font=self.theme.FONTS["body"],
            bg=self.theme.COLORS["bg_secondary"],
            fg=self.theme.COLORS["text_primary"],
            insertbackground=self.theme.COLORS["text_primary"],
            relief=tk.FLAT,
            padx=15,
            pady=15,
        )
        self.text_widget.pack(fill=tk.BOTH, expand=True)
        self.text_widget.insert("1.0", HELP_CONTENT[self.tab_name]["content"])
        self.text_widget.config(state=tk.DISABLED)
        button_frame = tk.Frame(main_frame, bg=self.theme.COLORS["bg_primary"])
        button_frame.pack(pady=(10, 0))
        close_button = tk.Button(
            button_frame,
            text="Close",
            command=self.destroy,
            bg=self.theme.COLORS["accent_secondary"],
            fg=self.theme.COLORS["text_primary"],
            font=self.theme.FONTS["body"],
            relief=tk.FLAT,
            padx=20,
            pady=8,
            cursor="hand2",
        )
        close_button.pack()
        self.transient(parent)
        self.grab_set()
        self.update_idletasks()
        x = parent.winfo_x() + parent.winfo_width() // 2 - self.winfo_width() // 2
        y = parent.winfo_y() + parent.winfo_height() // 2 - self.winfo_height() // 2
        self.geometry(f"+{x}+{y}")


class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None):
        if self.tooltip_window or not self.text:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        self.tooltip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            tw,
            text=self.text,
            justify=tk.LEFT,
            background="#ffffe0",
            foreground="#000000",
            relief=tk.SOLID,
            borderwidth=1,
            font=("Arial", 9),
            padx=8,
            pady=6,
        )
        label.pack()

    def hide_tooltip(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None
