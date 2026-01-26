import tkinter as tk
from tkinter import ttk

from src.utils.discovery import list_attacker_strategies

from .base_tab import BaseTab


class AttackerTab(BaseTab):
    def __init__(self, parent, theme_colors):
        self.attacker_entries = []
        self.attacker_list = []
        self.attacker_entries_frame = None
        self.available_strategies = list_attacker_strategies()
        super().__init__(parent, theme_colors)

    def create_widgets(self):
        strategy_info = self.create_section_header(
            self.pad_frame, "Attacker Strategies:", section_type="attackers"
        )
        self.create_info_label(
            strategy_info,
            f"Available: {', '.join(self.available_strategies)}",
            bg_color=self.theme.COLORS["section_actors"],
        ).pack(anchor="w", padx=15)
        self.attacker_entries_frame = tk.Frame(self.pad_frame, bg=self.tab_color)
        self.attacker_entries_frame.pack(fill="both", expand=True, padx=10, pady=(5, 0))
        self.attacker_entries_frame.grid_columnconfigure(0, weight=2, minsize=100)
        self.attacker_entries_frame.grid_columnconfigure(1, weight=2, minsize=100)
        self.attacker_entries_frame.grid_columnconfigure(2, weight=1, minsize=80)
        self.attacker_entries_frame.grid_columnconfigure(3, weight=0, minsize=40)
        self.attacker_entries_frame.grid_columnconfigure(4, weight=1, minsize=100)
        self.attacker_entries_frame.grid_columnconfigure(5, weight=1, minsize=80)
        headers = ["ID", "Strategy", "Capacity", "∞", "Budget ($)", "Actions"]
        for i, text in enumerate(headers):
            label_style = self.theme.get_label_style("subheading")
            label_style.update({"bg": self.sidebar_color, **self.theme.BORDERS["light"]})
            header_label = tk.Label(self.attacker_entries_frame, text=text, **label_style)
            header_label.grid(row=0, column=i, padx=2, pady=2, sticky="ew")
        self.attacker_entries_frame.grid_columnconfigure(5, weight=1, minsize=80)
        self.add_attacker_entry()
        self.create_styled_button(self.pad_frame, "Add Attacker", self.add_attacker_entry).pack(
            padx=10, pady=10, anchor="w"
        )

    def add_attacker_entry(self):
        attacker_id = len(self.attacker_entries) + 1
        row = attacker_id
        id_label = tk.Label(
            self.attacker_entries_frame,
            text=f"Attacker {attacker_id}",
            bg=self.theme.COLORS["input_bg"],
            fg=self.button_fg,
            **self.theme.BORDERS["sunken"],
        )
        id_label.grid(row=row, column=0, padx=2, pady=2, sticky="ew")
        default_strategy = (
            "escalation"
            if "escalation" in self.available_strategies
            else (self.available_strategies[0] if self.available_strategies else "greedy")
        )
        strategy_var = tk.StringVar(value=default_strategy)
        strategy_dropdown = ttk.Combobox(
            self.attacker_entries_frame,
            textvariable=strategy_var,
            values=self.available_strategies,
            state="readonly",
        )
        strategy_dropdown.grid(row=row, column=1, padx=2, pady=2, sticky="ew")
        capacity_var = tk.StringVar(value="3")
        capacity_entry = self.create_styled_entry(self.attacker_entries_frame, capacity_var)
        capacity_entry.grid(row=row, column=2, padx=2, pady=2, sticky="ew")
        infinite_var = tk.BooleanVar(value=True)
        infinite_check = tk.Checkbutton(
            self.attacker_entries_frame,
            text="∞",
            variable=infinite_var,
            bg=self.tab_color,
            fg=self.button_fg,
            command=lambda: self._toggle_capacity(capacity_entry, infinite_var),
        )
        infinite_check.grid(row=row, column=3, padx=2, pady=2, sticky="ew")
        capacity_entry.config(state="disabled")
        budget_var = tk.StringVar(value="100000")
        budget_entry = self.create_styled_entry(self.attacker_entries_frame, budget_var)
        budget_entry.grid(row=row, column=4, padx=2, pady=2, sticky="ew")
        remove_btn = self.create_styled_button(
            self.attacker_entries_frame,
            "Remove",
            lambda: self._remove_attacker(attacker_id),
            style_type="danger",
        )
        remove_btn.grid(row=row, column=5, padx=2, pady=2, sticky="ew")
        attacker_widgets = {
            "id_label": id_label,
            "strategy_var": strategy_var,
            "strategy_dropdown": strategy_dropdown,
            "capacity_var": capacity_var,
            "capacity_entry": capacity_entry,
            "infinite_var": infinite_var,
            "infinite_check": infinite_check,
            "budget_var": budget_var,
            "budget_entry": budget_entry,
            "remove_btn": remove_btn,
            "row": row,
        }
        self.attacker_entries.append(
            (
                attacker_id,
                strategy_var,
                capacity_var,
                infinite_var,
                budget_var,
                attacker_widgets,
            )
        )

    def _toggle_capacity(self, capacity_entry, infinite_var):
        if infinite_var.get():
            capacity_entry.config(state="disabled")
        else:
            capacity_entry.config(state="normal")

    def _remove_attacker(self, attacker_id):
        for i, entry in enumerate(self.attacker_entries):
            if entry[0] == attacker_id:
                widgets = entry[5]
                for widget_name, widget in widgets.items():
                    if widget_name != "row" and hasattr(widget, "destroy"):
                        widget.destroy()
                self.attacker_entries.pop(i)
                break
        self._rebuild_attacker_grid()

    def _rebuild_attacker_grid(self):
        for widget in self.attacker_entries_frame.winfo_children():
            widget.destroy()
        configs = []
        for entry in self.attacker_entries:
            config = {
                "strategy": entry[1].get(),
                "capacity": entry[2].get(),
                "infinite": entry[3].get(),
                "budget": entry[4].get(),
            }
            configs.append(config)
        self.attacker_entries.clear()
        for config in configs:
            self._add_attacker_with_config(config)

    def _add_attacker_with_config(self, config):
        attacker_id = len(self.attacker_entries) + 1
        row = attacker_id
        id_label = tk.Label(
            self.attacker_entries_frame,
            text=f"Attacker {attacker_id}",
            bg=self.theme.COLORS["input_bg"],
            fg=self.button_fg,
            **self.theme.BORDERS["sunken"],
        )
        id_label.grid(row=row, column=0, padx=2, pady=2, sticky="ew")
        strategy_var = tk.StringVar(value=config["strategy"])
        strategy_dropdown = ttk.Combobox(
            self.attacker_entries_frame,
            textvariable=strategy_var,
            values=self.available_strategies,
            state="readonly",
        )
        strategy_dropdown.grid(row=row, column=1, padx=2, pady=2, sticky="ew")
        capacity_var = tk.StringVar(value=config["capacity"])
        capacity_entry = self.create_styled_entry(self.attacker_entries_frame, capacity_var)
        capacity_entry.grid(row=row, column=2, padx=2, pady=2, sticky="ew")
        infinite_var = tk.BooleanVar(value=config["infinite"])
        infinite_check = tk.Checkbutton(
            self.attacker_entries_frame,
            text="∞",
            variable=infinite_var,
            bg=self.tab_color,
            fg=self.button_fg,
            command=lambda: self._toggle_capacity(capacity_entry, infinite_var),
        )
        infinite_check.grid(row=row, column=3, padx=2, pady=2, sticky="ew")
        if infinite_var.get():
            capacity_entry.config(state="disabled")
        else:
            capacity_entry.config(state="normal")
        budget_var = tk.StringVar(value=config["budget"])
        budget_entry = self.create_styled_entry(self.attacker_entries_frame, budget_var)
        budget_entry.grid(row=row, column=4, padx=2, pady=2, sticky="ew")
        remove_btn = self.create_styled_button(
            self.attacker_entries_frame,
            "Remove",
            lambda: self._remove_attacker(attacker_id),
            style_type="danger",
        )
        remove_btn.grid(row=row, column=5, padx=2, pady=2, sticky="ew")
        attacker_widgets = {
            "id_label": id_label,
            "strategy_var": strategy_var,
            "strategy_dropdown": strategy_dropdown,
            "capacity_var": capacity_var,
            "capacity_entry": capacity_entry,
            "infinite_var": infinite_var,
            "infinite_check": infinite_check,
            "budget_var": budget_var,
            "budget_entry": budget_entry,
            "remove_btn": remove_btn,
            "row": row,
        }
        self.attacker_entries.append(
            (
                attacker_id,
                strategy_var,
                capacity_var,
                infinite_var,
                budget_var,
                attacker_widgets,
            )
        )

    def get_attacker_config(self):
        attackers = []
        for entry in self.attacker_entries:
            attacker_id, strategy_var, capacity_var, infinite_var, budget_var, frame = entry
            if infinite_var.get():
                capacity = float("inf")
            else:
                try:
                    capacity = int(capacity_var.get())
                except ValueError:
                    capacity = 3
            try:
                budget = float(budget_var.get())
            except ValueError:
                budget = 1000.0
            attackers.append(
                {
                    "id": f"attacker{attacker_id}",
                    "strategy": strategy_var.get(),
                    "capacity": capacity,
                    "budget": budget,
                }
            )
        return attackers
