import tkinter as tk
from tkinter import ttk
from .base_tab import BaseTab
from src.utils.discovery import list_defender_strategies


class DefenderTab(BaseTab):

    def __init__(self, parent, theme_colors):
        self.defender_entries = []
        self.defender_list = []
        self.defender_entries_frame = None
        self.available_strategies = list_defender_strategies()
        super().__init__(parent, theme_colors)

    def create_widgets(self):
        strategy_info = self.create_section_header(
            self.pad_frame, "Defender Strategies:", section_type="defenders"
        )
        self.create_info_label(
            strategy_info,
            f'Available: {", ".join(self.available_strategies)}',
            bg_color=self.theme.COLORS["section_actors"],
        ).pack(anchor="w", padx=15)
        self.defender_entries_frame = tk.Frame(self.pad_frame, bg=self.tab_color)
        self.defender_entries_frame.pack(fill="both", expand=True, padx=10, pady=(5, 0))
        self.defender_entries_frame.grid_columnconfigure(0, weight=2, minsize=100)
        self.defender_entries_frame.grid_columnconfigure(1, weight=2, minsize=100)
        self.defender_entries_frame.grid_columnconfigure(2, weight=1, minsize=80)
        self.defender_entries_frame.grid_columnconfigure(3, weight=1, minsize=100)
        self.defender_entries_frame.grid_columnconfigure(4, weight=1, minsize=80)
        headers = ["ID", "Strategy", "Capacity", "Budget ($)", "Actions"]
        for i, text in enumerate(headers):
            label_style = self.theme.get_label_style("subheading")
            label_style.update(
                {"bg": self.sidebar_color, **self.theme.BORDERS["light"]}
            )
            header_label = tk.Label(
                self.defender_entries_frame, text=text, **label_style
            )
            header_label.grid(row=0, column=i, padx=2, pady=2, sticky="ew")
        self.add_defender_entry()
        self.create_styled_button(
            self.pad_frame, "Add Defender", self.add_defender_entry
        ).pack(padx=10, pady=10, anchor="w")

    def add_defender_entry(self):
        defender_id = len(self.defender_entries) + 1
        row = defender_id
        id_label = tk.Label(
            self.defender_entries_frame,
            text=f"Defender {defender_id}",
            bg=self.theme.COLORS["input_bg"],
            fg=self.button_fg,
            **self.theme.BORDERS["sunken"],
        )
        id_label.grid(row=row, column=0, padx=2, pady=2, sticky="ew")
        default_strategy = (
            self.available_strategies[0] if self.available_strategies else "reactive"
        )
        strategy_var = tk.StringVar(value=default_strategy)
        strategy_dropdown = ttk.Combobox(
            self.defender_entries_frame,
            textvariable=strategy_var,
            values=self.available_strategies,
            state="readonly",
        )
        strategy_dropdown.grid(row=row, column=1, padx=2, pady=2, sticky="ew")
        capacity_var = tk.StringVar(value="3")
        capacity_entry = self.create_styled_entry(
            self.defender_entries_frame, capacity_var
        )
        capacity_entry.grid(row=row, column=2, padx=2, pady=2, sticky="ew")
        budget_var = tk.StringVar(value="10000")
        budget_entry = self.create_styled_entry(self.defender_entries_frame, budget_var)
        budget_entry.grid(row=row, column=3, padx=2, pady=2, sticky="ew")
        remove_btn = self.create_styled_button(
            self.defender_entries_frame,
            "Remove",
            lambda: self._remove_defender(defender_id),
            style_type="danger",
        )
        remove_btn.grid(row=row, column=4, padx=2, pady=2, sticky="ew")
        defender_widgets = {
            "id_label": id_label,
            "strategy_var": strategy_var,
            "strategy_dropdown": strategy_dropdown,
            "capacity_var": capacity_var,
            "capacity_entry": capacity_entry,
            "budget_var": budget_var,
            "budget_entry": budget_entry,
            "remove_btn": remove_btn,
            "row": row,
        }
        self.defender_entries.append(
            (defender_id, strategy_var, capacity_var, budget_var, defender_widgets)
        )

    def _remove_defender(self, defender_id):
        for i, entry in enumerate(self.defender_entries):
            if entry[0] == defender_id:
                widgets = entry[4]
                for widget_name, widget in widgets.items():
                    if widget_name != "row" and hasattr(widget, "destroy"):
                        widget.destroy()
                self.defender_entries.pop(i)
                break
        self._rebuild_defender_grid()

    def _rebuild_defender_grid(self):
        for widget in self.defender_entries_frame.winfo_children():
            widget.destroy()
        configs = []
        for entry in self.defender_entries:
            config = {
                "strategy": entry[1].get(),
                "capacity": entry[2].get(),
                "budget": entry[3].get(),
            }
            configs.append(config)
        self.defender_entries.clear()
        for config in configs:
            self._add_defender_with_config(config)

    def _add_defender_with_config(self, config):
        defender_id = len(self.defender_entries) + 1
        row = defender_id
        id_label = tk.Label(
            self.defender_entries_frame,
            text=f"Defender {defender_id}",
            bg=self.theme.COLORS["input_bg"],
            fg=self.button_fg,
            **self.theme.BORDERS["sunken"],
        )
        id_label.grid(row=row, column=0, padx=2, pady=2, sticky="ew")
        strategy_var = tk.StringVar(value=config["strategy"])
        strategy_dropdown = ttk.Combobox(
            self.defender_entries_frame,
            textvariable=strategy_var,
            values=self.available_strategies,
            state="readonly",
        )
        strategy_dropdown.grid(row=row, column=1, padx=2, pady=2, sticky="ew")
        capacity_var = tk.StringVar(value=config["capacity"])
        capacity_entry = self.create_styled_entry(
            self.defender_entries_frame, capacity_var
        )
        capacity_entry.grid(row=row, column=2, padx=2, pady=2, sticky="ew")
        budget_var = tk.StringVar(value=config["budget"])
        budget_entry = self.create_styled_entry(self.defender_entries_frame, budget_var)
        budget_entry.grid(row=row, column=3, padx=2, pady=2, sticky="ew")
        remove_btn = self.create_styled_button(
            self.defender_entries_frame,
            "Remove",
            lambda: self._remove_defender(defender_id),
            style_type="danger",
        )
        remove_btn.grid(row=row, column=4, padx=2, pady=2, sticky="ew")
        defender_widgets = {
            "id_label": id_label,
            "strategy_var": strategy_var,
            "strategy_dropdown": strategy_dropdown,
            "capacity_var": capacity_var,
            "capacity_entry": capacity_entry,
            "budget_var": budget_var,
            "budget_entry": budget_entry,
            "remove_btn": remove_btn,
            "row": row,
        }
        self.defender_entries.append(
            (defender_id, strategy_var, capacity_var, budget_var, defender_widgets)
        )

    def get_defender_config(self):
        defenders = []
        for entry in self.defender_entries:
            defender_id, strategy_var, capacity_var, budget_var, frame = entry
            try:
                capacity = int(capacity_var.get())
            except ValueError:
                capacity = 2
            try:
                budget = float(budget_var.get())
            except ValueError:
                budget = 2000.0
            defenders.append(
                {
                    "id": f"defender{defender_id}",
                    "strategy": strategy_var.get(),
                    "capacity": capacity,
                    "budget": budget,
                }
            )
        return defenders
