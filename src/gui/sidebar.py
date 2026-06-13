import tkinter as tk


class Sidebar(tk.Frame):
    def __init__(
        self,
        master,
        toggle_fullscreen,
        fullscreen_state,
        switch_tab_callback,
        theme_colors,
    ):
        self.sidebar_color = theme_colors.get("sidebar_color", "#e3eaf2")
        self.highlight_color = theme_colors.get("highlight_color", "#b5d6fc")
        self.button_fg = theme_colors.get("button_fg", "#22223b")
        super().__init__(master, bd=2, relief=tk.RIDGE, bg=self.sidebar_color)
        self.buttons = {}
        self.tab_names = [
            "Simulation",
            "Network",
            "Attackers",
            "Defenders",
            "Actions",
            "Scenarios",
            "Overview",
        ]
        self._create_tab_buttons(switch_tab_callback)
        self._create_spacer()
        self._create_fullscreen_toggle(toggle_fullscreen, fullscreen_state)
        self.highlight_tab("Simulation")

    def _create_tab_buttons(self, switch_tab_callback):
        for i, name in enumerate(self.tab_names):
            btn = tk.Button(
                self,
                text=name,
                command=lambda n=name: switch_tab_callback(n),
                bg=self.sidebar_color,
                fg=self.button_fg,
                activebackground=self.highlight_color,
                activeforeground=self.button_fg,
                relief=tk.FLAT,
                font=("Arial", 10, "bold"),
                width=12,
                pady=5,
            )
            btn.grid(row=i, column=0, pady=10, padx=15, sticky="ew")
            self.buttons[name] = btn

    def _create_spacer(self):
        self.spacer = tk.Label(self, bg=self.sidebar_color)
        self.spacer.grid(row=7, column=0, sticky="nswe")
        self.grid_rowconfigure(7, weight=1)

    def _create_fullscreen_toggle(self, toggle_fullscreen, fullscreen_state):
        self.fullscreen_var = tk.BooleanVar(value=fullscreen_state)
        self.fullscreen_switch = tk.Checkbutton(
            self,
            text="Fullscreen",
            variable=self.fullscreen_var,
            command=toggle_fullscreen,
            bg=self.sidebar_color,
            fg=self.button_fg,
            selectcolor=self.highlight_color,
            activebackground=self.highlight_color,
            font=("Arial", 9),
        )
        self.fullscreen_switch.grid(row=8, column=0, pady=(5, 15), padx=15, sticky="s")

    def highlight_tab(self, tab_name):
        for name, btn in self.buttons.items():
            if name == tab_name:
                btn.config(
                    bg=self.highlight_color,
                    fg=self.button_fg,
                    relief=tk.SUNKEN,
                    font=("Arial", 10, "bold"),
                )
            else:
                btn.config(
                    bg=self.sidebar_color,
                    fg=self.button_fg,
                    relief=tk.FLAT,
                    font=("Arial", 10, "normal"),
                )

    def update_fullscreen_switch(self):
        self.fullscreen_var.set(self.master.fullscreen_state)
