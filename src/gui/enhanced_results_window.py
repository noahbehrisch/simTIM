import tkinter as tk
from tkinter import ttk
import logging
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from typing import List, Dict, Any, Optional
from src.visualization import (
    ViolinPlotEngine,
    TimeSeriesPlotEngine,
    analyze_simulation_results,
)
from src.utils import format_time
from src.utils.time_utils import parse_event

logger = logging.getLogger(__name__)


class EnhancedResultsWindow:

    def __init__(self, parent, all_histories, theme_colors, scenario_results=None):
        self.parent = parent
        self.all_histories = all_histories
        self.scenario_results = scenario_results
        self.bg_color = theme_colors["bg_color"]
        self.button_fg = theme_colors["button_fg"]
        self.runs_data = []
        self.actors_data = {}
        self.economic_data = {}
        self.window = tk.Toplevel(parent)
        self.window.title("Simulation Results")
        self.window.geometry("1600x1000")
        self.window.configure(bg=self.bg_color)
        self._process_simulation_data()
        self._create_interface()

    def _process_simulation_data(self):
        self.runs_data = []
        self.actors_data = {}
        for run_id, history in enumerate(self.all_histories):
            run_events = []
            for event in history:
                time, event_type, data = parse_event(event)
                if time is None:
                    continue
                actor_id = "Unknown"
                action_name = "Unknown"
                target_id = "Unknown"
                if isinstance(data, dict):
                    if event_type == "attack_detected":
                        if "detected_actor" in data and hasattr(
                            data["detected_actor"], "id"
                        ):
                            actor_id = data["detected_actor"].id
                        if "detected_action" in data and hasattr(
                            data["detected_action"], "name"
                        ):
                            action_name = data["detected_action"].name
                        if "detected_target" in data and hasattr(
                            data["detected_target"], "id"
                        ):
                            target_id = data["detected_target"].id
                    elif event_type == "action_interrupted_by_detection":
                        if "actor" in data:
                            actor_id = (
                                data["actor"]
                                if isinstance(data["actor"], str)
                                else str(data["actor"])
                            )
                        if "action" in data:
                            action_name = (
                                data["action"]
                                if isinstance(data["action"], str)
                                else str(data["action"])
                            )
                        if "target" in data and hasattr(data["target"], "id"):
                            target_id = data["target"].id
                    else:
                        if "actor" in data and hasattr(data["actor"], "id"):
                            actor_id = data["actor"].id
                        if "action" in data and hasattr(data["action"], "name"):
                            action_name = data["action"].name
                        if "target" in data and hasattr(data["target"], "id"):
                            target_id = data["target"].id
                if event_type not in [
                    "action_succeeded",
                    "action_failed",
                    "action_aborted",
                    "action_aborted_start",
                    "action_interrupted",
                    "attack_detected",
                    "action_interrupted_by_detection",
                ]:
                    continue
                if actor_id == "Unknown" and event_type not in [
                    "attack_detected",
                    "action_interrupted_by_detection",
                ]:
                    continue
                is_success = event_type == "action_succeeded"
                is_detection = event_type == "attack_detected"
                is_failure = event_type in [
                    "action_failed",
                    "action_aborted",
                    "action_aborted_start",
                    "action_interrupted",
                    "action_interrupted_by_detection",
                ]
                event_record = {
                    "run_id": run_id,
                    "time": time,
                    "event_type": event_type,
                    "actor_id": actor_id,
                    "action_name": action_name,
                    "target_id": target_id,
                    "success": is_success,
                    "detection": is_detection,
                    "failure": is_failure,
                    "raw_data": data,
                }
                run_events.append(event_record)
                if actor_id not in self.actors_data:
                    self.actors_data[actor_id] = {
                        "actions": [],
                        "economics": {
                            "total_cost": 0,
                            "total_gain": 0,
                            "total_damage": 0,
                            "per_run": {},
                        },
                    }
                self.actors_data[actor_id]["actions"].append(event_record)
                if event_record["success"]:
                    cost = self._extract_cost(
                        event_record
                    ) or self._estimate_cost_fallback(event_record)
                    gain = self._extract_gain(
                        event_record
                    ) or self._estimate_gain_fallback(event_record)
                    damage = self._extract_damage(
                        event_record
                    ) or self._estimate_damage_fallback(event_record)
                    self.actors_data[actor_id]["economics"]["total_cost"] += cost
                    self.actors_data[actor_id]["economics"]["total_gain"] += gain
                    self.actors_data[actor_id]["economics"]["total_damage"] += damage
                    if run_id not in self.actors_data[actor_id]["economics"]["per_run"]:
                        self.actors_data[actor_id]["economics"]["per_run"][run_id] = {
                            "cost": 0,
                            "gain": 0,
                            "damage": 0,
                        }
                    self.actors_data[actor_id]["economics"]["per_run"][run_id][
                        "cost"
                    ] += cost
                    self.actors_data[actor_id]["economics"]["per_run"][run_id][
                        "gain"
                    ] += gain
                    self.actors_data[actor_id]["economics"]["per_run"][run_id][
                        "damage"
                    ] += damage
            self.runs_data.append(run_events)

    def _extract_cost(self, event: Dict[str, Any]) -> float:
        raw_data = event.get("raw_data", {})
        if isinstance(raw_data, dict):
            action = raw_data.get("action")
            if action and hasattr(action, "cost"):
                return float(action.cost)
        return 0.0

    def _extract_gain(self, event: Dict[str, Any]) -> float:
        if "attacker" not in event["actor_id"].lower():
            return 0.0
        raw_data = event.get("raw_data", {})
        if isinstance(raw_data, dict):
            action = raw_data.get("action")
            target = raw_data.get("target")
            if action and hasattr(action, "get_one_off_gain"):
                try:
                    actor_access = raw_data.get("actor_access", "NONE")
                    actor_id = event.get("actor_id", "unknown")
                    return float(
                        action.get_one_off_gain(target, actor_access, actor_id)
                    )
                except (TypeError, AttributeError, ValueError) as e:
                    logger.debug(f"Failed to extract gain via get_one_off_gain: {e}")
            if action and hasattr(action, "one_off_gain"):
                try:
                    return float(action.one_off_gain(target, None, None))
                except (TypeError, AttributeError, ValueError) as e:
                    logger.debug(f"Failed to extract gain via one_off_gain: {e}")
        return 0.0

    def _extract_damage(self, event: Dict[str, Any]) -> float:
        raw_data = event.get("raw_data", {})
        if isinstance(raw_data, dict):
            action = raw_data.get("action")
            target = raw_data.get("target")
            if action and hasattr(action, "get_one_off_damage"):
                try:
                    actor_access = raw_data.get("actor_access", "NONE")
                    actor_id = event.get("actor_id", "unknown")
                    return float(
                        action.get_one_off_damage(target, actor_access, actor_id)
                    )
                except (TypeError, AttributeError, ValueError) as e:
                    logger.debug(
                        f"Failed to extract damage via get_one_off_damage: {e}"
                    )
            if action and hasattr(action, "one_off_damage"):
                try:
                    return float(action.one_off_damage(target, None, None))
                except (TypeError, AttributeError, ValueError) as e:
                    logger.debug(f"Failed to extract damage via one_off_damage: {e}")
        return 0.0


    def _create_interface(self):
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        num_runs = len(self.runs_data)
        num_actors = len(self.actors_data)
        if num_runs <= 5:
            for run_id in range(num_runs):
                self._create_run_tab(run_id)
        else:
            self._create_runs_dropdown_tab()
        if num_actors <= 8:
            for actor_id in self.actors_data.keys():
                self._create_actor_tab(actor_id)
        else:
            self._create_actors_dropdown_tab()
        self._create_events_timeline_tab()
        self._create_money_timeline_tab()
        self._create_nodes_timeline_tab()
        self._create_statistical_tab()
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)

    def _create_run_tab(self, run_id: int):
        tab_frame = tk.Frame(self.notebook, bg=self.bg_color)
        self.notebook.add(tab_frame, text=f"Run {run_id + 1}")
        stats_frame = tk.Frame(tab_frame, bg=self.bg_color, relief=tk.RAISED, bd=1)
        stats_frame.pack(fill=tk.X, padx=10, pady=5)
        events = self.runs_data[run_id]
        total_events = len(events)
        successful_events = len([e for e in events if e["success"]])
        detections = len([e for e in events if e["detection"]])
        tk.Label(
            stats_frame,
            text=f"Run {run_id + 1} Summary:",
            font=("Arial", 12, "bold"),
            bg=self.bg_color,
            fg=self.button_fg,
        ).pack(side=tk.LEFT, padx=10)
        tk.Label(
            stats_frame,
            text=f"Total Events: {total_events}  |  Successful: {successful_events}  |  Detections: {detections}",
            bg=self.bg_color,
            fg=self.button_fg,
        ).pack(side=tk.LEFT, padx=20)
        log_frame = tk.Frame(tab_frame, bg=self.bg_color)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        text_frame = tk.Frame(log_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        logs_text = tk.Text(
            text_frame,
            wrap=tk.WORD,
            bg="#eaf1fb",
            fg=self.button_fg,
            font=("Consolas", 10),
        )
        scrollbar = tk.Scrollbar(
            text_frame, orient=tk.VERTICAL, command=logs_text.yview
        )
        logs_text.configure(yscrollcommand=scrollbar.set)
        logs_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        for event in sorted(events, key=lambda x: x["time"]):
            self._add_event_to_log(logs_text, event)
        logs_text.config(state=tk.DISABLED)

    def _create_runs_dropdown_tab(self):
        tab_frame = tk.Frame(self.notebook, bg=self.bg_color)
        self.notebook.add(tab_frame, text="Event History")
        dropdown_frame = tk.Frame(tab_frame, bg=self.bg_color, relief=tk.RAISED, bd=1)
        dropdown_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(
            dropdown_frame, text="Select Run:", bg=self.bg_color, fg=self.button_fg
        ).pack(side=tk.LEFT, padx=10)
        self.run_selector = tk.StringVar(value="Run 1")
        run_options = [f"Run {i + 1}" for i in range(len(self.runs_data))]
        run_dropdown = ttk.Combobox(
            dropdown_frame,
            textvariable=self.run_selector,
            values=run_options,
            state="readonly",
            width=15,
        )
        run_dropdown.pack(side=tk.LEFT, padx=5)
        run_dropdown.bind("<<ComboboxSelected>>", self._on_run_selected)
        self.run_stats_frame = tk.Frame(
            tab_frame, bg=self.bg_color, relief=tk.RAISED, bd=1
        )
        self.run_stats_frame.pack(fill=tk.X, padx=10, pady=5)
        log_frame = tk.Frame(tab_frame, bg=self.bg_color)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        text_frame = tk.Frame(log_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        self.run_logs_text = tk.Text(
            text_frame,
            wrap=tk.WORD,
            bg="#eaf1fb",
            fg=self.button_fg,
            font=("Consolas", 10),
        )
        run_scrollbar = tk.Scrollbar(
            text_frame, orient=tk.VERTICAL, command=self.run_logs_text.yview
        )
        self.run_logs_text.configure(yscrollcommand=run_scrollbar.set)
        self.run_logs_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        run_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._load_run_data(0)

    def _create_actor_tab(self, actor_id: str):
        tab_frame = tk.Frame(self.notebook, bg=self.bg_color)
        self.notebook.add(tab_frame, text=actor_id)
        paned = tk.PanedWindow(tab_frame, orient=tk.VERTICAL, bg=self.bg_color)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        actions_frame = tk.Frame(paned, bg=self.bg_color, relief=tk.RAISED, bd=1)
        paned.add(actions_frame, minsize=200)
        tk.Label(
            actions_frame,
            text=f"{actor_id} - Actions Timeline",
            font=("Arial", 12, "bold"),
            bg=self.bg_color,
            fg=self.button_fg,
        ).pack(pady=5)
        actions_text = tk.Text(
            actions_frame,
            height=15,
            wrap=tk.WORD,
            bg="#eaf1fb",
            fg=self.button_fg,
            font=("Consolas", 9),
        )
        actions_scrollbar = tk.Scrollbar(
            actions_frame, orient=tk.VERTICAL, command=actions_text.yview
        )
        actions_text.configure(yscrollcommand=actions_scrollbar.set)
        actions_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        actions_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
        actor_actions = sorted(
            self.actors_data[actor_id]["actions"],
            key=lambda x: (x["run_id"], x["time"]),
        )
        for action in actor_actions:
            self._add_action_to_log(actions_text, action)
        actions_text.config(state=tk.DISABLED)
        economics_frame = tk.Frame(paned, bg=self.bg_color, relief=tk.RAISED, bd=1)
        paned.add(economics_frame, minsize=200)
        tk.Label(
            economics_frame,
            text=f"{actor_id} - Economic Impact",
            font=("Arial", 12, "bold"),
            bg=self.bg_color,
            fg=self.button_fg,
        ).pack(pady=5)
        toggle_frame = tk.Frame(economics_frame, bg=self.bg_color)
        toggle_frame.pack(fill=tk.X, padx=10, pady=5)
        self.economics_view = tk.StringVar(value="total")
        ttk.Radiobutton(
            toggle_frame,
            text="Total",
            variable=self.economics_view,
            value="total",
            command=lambda: self._update_economics_view(actor_id, economics_frame),
        ).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(
            toggle_frame,
            text="Per Run",
            variable=self.economics_view,
            value="per_run",
            command=lambda: self._update_economics_view(actor_id, economics_frame),
        ).pack(side=tk.LEFT, padx=5)
        self.economics_content_frame = tk.Frame(economics_frame, bg=self.bg_color)
        self.economics_content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self._update_economics_view(actor_id, economics_frame)

    def _create_actors_dropdown_tab(self):
        tab_frame = tk.Frame(self.notebook, bg=self.bg_color)
        self.notebook.add(tab_frame, text="Actor Analysis")
        dropdown_frame = tk.Frame(tab_frame, bg=self.bg_color, relief=tk.RAISED, bd=1)
        dropdown_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(
            dropdown_frame, text="Select Actor:", bg=self.bg_color, fg=self.button_fg
        ).pack(side=tk.LEFT, padx=10)
        self.actor_selector = tk.StringVar(value=list(self.actors_data.keys())[0])
        actor_options = list(self.actors_data.keys())
        actor_dropdown = ttk.Combobox(
            dropdown_frame,
            textvariable=self.actor_selector,
            values=actor_options,
            state="readonly",
            width=20,
        )
        actor_dropdown.pack(side=tk.LEFT, padx=5)
        actor_dropdown.bind("<<ComboboxSelected>>", self._on_actor_selected)
        self.actor_content_frame = tk.Frame(tab_frame, bg=self.bg_color)
        self.actor_content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self._load_actor_data(list(self.actors_data.keys())[0])

    def _create_events_timeline_tab(self):
        tab_frame = tk.Frame(self.notebook, bg=self.bg_color)
        self.notebook.add(tab_frame, text="Events Timeline")

        if len(self.runs_data) > 1:
            selector_frame = tk.Frame(tab_frame, bg=self.bg_color)
            selector_frame.pack(fill=tk.X, padx=10, pady=5)
            tk.Label(
                selector_frame, text="Select Run:", bg=self.bg_color, fg=self.button_fg
            ).pack(side=tk.LEFT, padx=5)
            self.events_run_var = tk.StringVar(value="Run 1")
            run_options = [f"Run {i + 1}" for i in range(len(self.runs_data))]
            dropdown = ttk.Combobox(
                selector_frame,
                textvariable=self.events_run_var,
                values=run_options,
                state="readonly",
                width=15,
            )
            dropdown.pack(side=tk.LEFT, padx=5)
            dropdown.bind(
                "<<ComboboxSelected>>", lambda e: self._update_events_timeline(0)
            )

        self.events_plot_frame = tk.Frame(tab_frame, bg=self.bg_color)
        self.events_plot_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self._update_events_timeline(0)

    def _update_events_timeline(self, run_id: int):
        for widget in self.events_plot_frame.winfo_children():
            widget.destroy()

        if hasattr(self, "events_run_var"):
            run_id = int(self.events_run_var.get().split()[1]) - 1

        history = self.all_histories[run_id] if run_id < len(self.all_histories) else []

        engine = TimeSeriesPlotEngine()
        fig = engine.create_events_over_time_plot(
            history, title=f"Events Over Time - Run {run_id + 1}"
        )

        canvas = FigureCanvasTkAgg(fig, self.events_plot_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.events_fig = fig
        self.events_canvas = canvas

    def _create_money_timeline_tab(self):
        tab_frame = tk.Frame(self.notebook, bg=self.bg_color)
        self.notebook.add(tab_frame, text="Money Timeline")

        if len(self.runs_data) > 1:
            selector_frame = tk.Frame(tab_frame, bg=self.bg_color)
            selector_frame.pack(fill=tk.X, padx=10, pady=5)
            tk.Label(
                selector_frame, text="Select Run:", bg=self.bg_color, fg=self.button_fg
            ).pack(side=tk.LEFT, padx=5)
            self.money_run_var = tk.StringVar(value="Run 1")
            run_options = [f"Run {i + 1}" for i in range(len(self.runs_data))]
            dropdown = ttk.Combobox(
                selector_frame,
                textvariable=self.money_run_var,
                values=run_options,
                state="readonly",
                width=15,
            )
            dropdown.pack(side=tk.LEFT, padx=5)
            dropdown.bind(
                "<<ComboboxSelected>>", lambda e: self._update_money_timeline(0)
            )

        self.money_plot_frame = tk.Frame(tab_frame, bg=self.bg_color)
        self.money_plot_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self._update_money_timeline(0)

    def _update_money_timeline(self, run_id: int):
        for widget in self.money_plot_frame.winfo_children():
            widget.destroy()

        if hasattr(self, "money_run_var"):
            run_id = int(self.money_run_var.get().split()[1]) - 1

        run_events = self.runs_data[run_id] if run_id < len(self.runs_data) else []

        fig, ax = plt.subplots(figsize=(12, 6))

        if run_events:
            times = []
            cum_cost = []
            cum_gain = []
            cum_damage = []

            sorted_events = sorted(run_events, key=lambda x: x["time"])
            total_cost = 0
            total_gain = 0
            total_damage = 0

            for event in sorted_events:
                if event["success"]:
                    # Use actual simulation data via _extract methods, fall back to estimates if needed
                    total_cost += self._extract_cost(
                        event
                    ) or self._estimate_cost_fallback(event)
                    total_gain += self._extract_gain(
                        event
                    ) or self._estimate_gain_fallback(event)
                    total_damage += self._extract_damage(
                        event
                    ) or self._estimate_damage_fallback(event)
                times.append(event["time"])
                cum_cost.append(total_cost)
                cum_gain.append(total_gain)
                cum_damage.append(total_damage)

            if times:
                ax.step(
                    times,
                    cum_cost,
                    where="post",
                    label="Cumulative Cost",
                    color="#ff7f0e",
                    linewidth=2,
                )
                ax.step(
                    times,
                    cum_gain,
                    where="post",
                    label="Attacker Gain",
                    color="#2ca02c",
                    linewidth=2,
                )
                ax.step(
                    times,
                    cum_damage,
                    where="post",
                    label="System Damage",
                    color="#d62728",
                    linewidth=2,
                )
                ax.set_xlabel("Time (hours)")
                ax.set_ylabel("Value ($)")
                ax.yaxis.set_major_formatter(
                    plt.FuncFormatter(lambda x, p: f"${x:,.0f}")
                )
                ax.legend(loc="upper left")
                ax.grid(True, alpha=0.3)

        ax.set_title(f"Economic Impact Over Time - Run {run_id + 1}")

        canvas = FigureCanvasTkAgg(fig, self.money_plot_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.money_fig = fig
        self.money_canvas = canvas

    def _create_nodes_timeline_tab(self):
        tab_frame = tk.Frame(self.notebook, bg=self.bg_color)
        self.notebook.add(tab_frame, text="Nodes Timeline")

        if len(self.runs_data) > 1:
            selector_frame = tk.Frame(tab_frame, bg=self.bg_color)
            selector_frame.pack(fill=tk.X, padx=10, pady=5)
            tk.Label(
                selector_frame, text="Select Run:", bg=self.bg_color, fg=self.button_fg
            ).pack(side=tk.LEFT, padx=5)
            self.nodes_run_var = tk.StringVar(value="Run 1")
            run_options = [f"Run {i + 1}" for i in range(len(self.runs_data))]
            dropdown = ttk.Combobox(
                selector_frame,
                textvariable=self.nodes_run_var,
                values=run_options,
                state="readonly",
                width=15,
            )
            dropdown.pack(side=tk.LEFT, padx=5)
            dropdown.bind(
                "<<ComboboxSelected>>", lambda e: self._update_nodes_timeline(0)
            )

        self.nodes_plot_frame = tk.Frame(tab_frame, bg=self.bg_color)
        self.nodes_plot_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self._update_nodes_timeline(0)

    def _update_nodes_timeline(self, run_id: int):
        for widget in self.nodes_plot_frame.winfo_children():
            widget.destroy()

        if hasattr(self, "nodes_run_var"):
            run_id = int(self.nodes_run_var.get().split()[1]) - 1

        history = self.all_histories[run_id] if run_id < len(self.all_histories) else []

        fig, ax = plt.subplots(figsize=(12, 6))

        node_states = {}
        times = []
        admin_counts = []
        user_counts = []
        visible_counts = []

        for entry in history:
            if len(entry) >= 3:
                time, event_type, data = entry[0], entry[1], entry[2]
                if event_type == "action_succeeded" and isinstance(data, dict):
                    target = data.get("target")
                    actor = data.get("actor")
                    action = data.get("action")

                    if (
                        target
                        and hasattr(target, "id")
                        and actor
                        and hasattr(actor, "is_attacker")
                        and actor.is_attacker
                    ):
                        node_id = target.id
                        action_name = (
                            action.name.lower()
                            if action and hasattr(action, "name")
                            else ""
                        )

                        if (
                            "admin" in action_name
                            or "privilege" in action_name
                            or "root" in action_name
                        ):
                            node_states[node_id] = "admin"
                        elif "exploit" in action_name or "user" in action_name:
                            if node_states.get(node_id) != "admin":
                                node_states[node_id] = "user"
                        elif "scan" in action_name or "discover" in action_name:
                            if node_id not in node_states:
                                node_states[node_id] = "visible"

                        admin = sum(1 for s in node_states.values() if s == "admin")
                        user = sum(1 for s in node_states.values() if s == "user")
                        visible = sum(1 for s in node_states.values() if s == "visible")

                        times.append(time)
                        admin_counts.append(admin)
                        user_counts.append(user)
                        visible_counts.append(visible)

        if times:
            max_time = max(
                entry[0]
                for entry in history
                if len(entry) >= 1 and isinstance(entry[0], (int, float))
            )
            ax.fill_between(
                times,
                0,
                admin_counts,
                label="Admin Access",
                color="#d62728",
                alpha=0.7,
                step="post",
            )
            ax.fill_between(
                times,
                admin_counts,
                [a + u for a, u in zip(admin_counts, user_counts)],
                label="User Access",
                color="#ff7f0e",
                alpha=0.7,
                step="post",
            )
            ax.fill_between(
                times,
                [a + u for a, u in zip(admin_counts, user_counts)],
                [
                    a + u + v
                    for a, u, v in zip(admin_counts, user_counts, visible_counts)
                ],
                label="Visible",
                color="#ffbb78",
                alpha=0.7,
                step="post",
            )
            ax.legend(loc="upper left")
            ax.set_xlim(0, max_time * 1.05)
        else:
            ax.text(
                0.5,
                0.5,
                "No node compromise data available",
                ha="center",
                va="center",
                transform=ax.transAxes,
                fontsize=12,
                color="gray",
            )

        ax.set_xlabel("Time (hours)")
        ax.set_ylabel("Number of Nodes")
        ax.set_title(f"Node Compromise Over Time - Run {run_id + 1}")
        ax.grid(True, alpha=0.3)

        canvas = FigureCanvasTkAgg(fig, self.nodes_plot_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.nodes_fig = fig
        self.nodes_canvas = canvas

    def _create_statistical_tab(self):
        tab_frame = tk.Frame(self.notebook, bg=self.bg_color)
        self.notebook.add(tab_frame, text="Statistical Analysis")
        if self.scenario_results and "scenarios" in self.scenario_results:
            self.stat_fig, self.stat_ax = plt.subplots(1, 1, figsize=(12, 8))
            self.stat_canvas = FigureCanvasTkAgg(self.stat_fig, tab_frame)
            self.stat_canvas.get_tk_widget().pack(
                fill=tk.BOTH, expand=True, padx=10, pady=5
            )
            self._create_scenario_comparison_plots()
        else:
            empty_label = tk.Label(
                tab_frame,
                text="Enable 'Scenario Comparison' in the Variables tab to see statistical analysis",
                font=("TkDefaultFont", 12),
                foreground="gray",
                bg=self.bg_color,
            )
            empty_label.pack(expand=True)

    def _add_event_to_log(self, text_widget, event):
        time = event["time"]
        actor = event["actor_id"]
        action = event["action_name"]
        target = event["target_id"]
        event_type = event.get("event_type", "")
        if event["success"]:
            icon = "✅"
            status = "succeeded"
        elif event["detection"]:
            icon = "🚨"
            status = "detected"
        elif event_type == "action_aborted_start":
            icon = "⏹️"
            status = "aborted (precondition)"
        elif event_type in ["action_interrupted", "action_interrupted_by_detection"]:
            icon = "🛑"
            status = "interrupted"
        elif event_type == "action_aborted":
            icon = "⏹️"
            status = "aborted"
        else:
            icon = "❌"
            status = "failed"
        log_line = (
            f"[{format_time(time)}] {icon} {actor} {status} {action} → {target}\n"
        )
        text_widget.insert(tk.END, log_line)

    def _add_action_to_log(self, text_widget, action):
        time = action["time"]
        run_id = action["run_id"]
        action_name = action["action_name"]
        target = action["target_id"]
        if action["success"]:
            icon = "✅"
            status = "SUCCESS"
        elif action["detection"]:
            icon = "🚨"
            status = "DETECTED"
        else:
            icon = "❌"
            status = "FAILED"
        log_line = f"Run {run_id + 1} [{format_time(time)}] {icon} {status}: {action_name} → {target}\n"
        text_widget.insert(tk.END, log_line)

    def _on_run_selected(self, event=None):
        selected = self.run_selector.get()
        run_id = int(selected.split()[1]) - 1
        self._load_run_data(run_id)

    def _load_run_data(self, run_id: int):
        for widget in self.run_stats_frame.winfo_children():
            widget.destroy()
        events = self.runs_data[run_id]
        total_events = len(events)
        successful_events = len([e for e in events if e["success"]])
        detections = len([e for e in events if e["detection"]])
        tk.Label(
            self.run_stats_frame,
            text=f"Run {run_id + 1} Summary:",
            font=("Arial", 12, "bold"),
            bg=self.bg_color,
            fg=self.button_fg,
        ).pack(side=tk.LEFT, padx=10)
        tk.Label(
            self.run_stats_frame,
            text=f"Total Events: {total_events}  |  Successful: {successful_events}  |  Detections: {detections}",
            bg=self.bg_color,
            fg=self.button_fg,
        ).pack(side=tk.LEFT, padx=20)
        self.run_logs_text.config(state=tk.NORMAL)
        self.run_logs_text.delete(1.0, tk.END)
        for event in sorted(events, key=lambda x: x["time"]):
            self._add_event_to_log(self.run_logs_text, event)
        self.run_logs_text.config(state=tk.DISABLED)

    def _on_actor_selected(self, event=None):
        selected_actor = self.actor_selector.get()
        self._load_actor_data(selected_actor)

    def _load_actor_data(self, actor_id: str):
        for widget in self.actor_content_frame.winfo_children():
            widget.destroy()
        paned = tk.PanedWindow(
            self.actor_content_frame, orient=tk.VERTICAL, bg=self.bg_color
        )
        paned.pack(fill=tk.BOTH, expand=True)
        actions_frame = tk.Frame(paned, bg=self.bg_color, relief=tk.RAISED, bd=1)
        paned.add(actions_frame, minsize=200)
        tk.Label(
            actions_frame,
            text=f"{actor_id} - Actions Timeline",
            font=("Arial", 12, "bold"),
            bg=self.bg_color,
            fg=self.button_fg,
        ).pack(pady=5)
        actions_text = tk.Text(
            actions_frame,
            height=15,
            wrap=tk.WORD,
            bg="#eaf1fb",
            fg=self.button_fg,
            font=("Consolas", 9),
        )
        actions_scrollbar = tk.Scrollbar(
            actions_frame, orient=tk.VERTICAL, command=actions_text.yview
        )
        actions_text.configure(yscrollcommand=actions_scrollbar.set)
        actions_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        actions_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
        actor_actions = sorted(
            self.actors_data[actor_id]["actions"],
            key=lambda x: (x["run_id"], x["time"]),
        )
        for action in actor_actions:
            self._add_action_to_log(actions_text, action)
        actions_text.config(state=tk.DISABLED)
        economics_frame = tk.Frame(paned, bg=self.bg_color, relief=tk.RAISED, bd=1)
        paned.add(economics_frame, minsize=200)
        tk.Label(
            economics_frame,
            text=f"{actor_id} - Economic Impact",
            font=("Arial", 12, "bold"),
            bg=self.bg_color,
            fg=self.button_fg,
        ).pack(pady=5)
        economics_content = tk.Text(
            economics_frame,
            height=10,
            wrap=tk.WORD,
            bg="#eaf1fb",
            fg=self.button_fg,
            font=("Consolas", 10),
        )
        economics_content.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        economics = self.actors_data[actor_id]["economics"]
        economics_content.insert(tk.END, f"TOTAL ECONOMIC IMPACT\n")
        economics_content.insert(tk.END, f"{'=' * 40}\n")
        economics_content.insert(
            tk.END, f"Total Cost:   ${economics['total_cost']:,.2f}\n"
        )
        economics_content.insert(
            tk.END, f"Total Gain:   ${economics['total_gain']:,.2f}\n"
        )
        economics_content.insert(
            tk.END, f"Total Damage: ${economics['total_damage']:,.2f}\n"
        )
        economics_content.insert(
            tk.END,
            f"Net Profit:   ${economics['total_gain'] - economics['total_cost']:,.2f}\n\n",
        )
        economics_content.insert(tk.END, f"PER-RUN BREAKDOWN\n")
        economics_content.insert(tk.END, f"{'=' * 40}\n")
        for run_id, run_data in economics["per_run"].items():
            economics_content.insert(tk.END, f"Run {run_id + 1}:\n")
            economics_content.insert(tk.END, f"  Cost:   ${run_data['cost']:,.2f}\n")
            economics_content.insert(tk.END, f"  Gain:   ${run_data['gain']:,.2f}\n")
            economics_content.insert(tk.END, f"  Damage: ${run_data['damage']:,.2f}\n")
            economics_content.insert(
                tk.END, f"  Profit: ${run_data['gain'] - run_data['cost']:,.2f}\n\n"
            )
        economics_content.config(state=tk.DISABLED)

    def _update_economics_view(self, actor_id: str, parent_frame):
        pass

    def _create_single_scenario_plots(self):
        try:
            simulation_results = analyze_simulation_results(self.all_histories)
            if not simulation_results:
                for ax in [
                    self.damage_ax,
                    self.cost_ax,
                    self.gain_ax,
                    self.comparison_ax,
                ]:
                    ax.text(
                        0.5,
                        0.5,
                        "No data available",
                        transform=ax.transAxes,
                        ha="center",
                        va="center",
                    )
                self.stat_canvas.draw()
                return
            damages = [r.get("total_damage", 0) for r in simulation_results]
            if damages and any((d > 0 for d in damages)):
                parts = self.damage_ax.violinplot(
                    [damages], showmeans=True, showmedians=True
                )
                for pc in parts["bodies"]:
                    pc.set_facecolor("#d62728")
                    pc.set_alpha(0.7)
                self.damage_ax.set_title("Damage Distribution")
                self.damage_ax.set_ylabel("Damage ($)")
                self.damage_ax.set_xticks([1])
                self.damage_ax.set_xticklabels(["All Runs"])
                self.damage_ax.yaxis.set_major_formatter(
                    plt.FuncFormatter(lambda x, p: f"${x:,.0f}")
                )
            all_costs = []
            for actor_data in self.actors_data.values():
                all_costs.append(actor_data["economics"]["total_cost"])
            if all_costs and any((c > 0 for c in all_costs)):
                parts = self.cost_ax.violinplot(
                    [all_costs], showmeans=True, showmedians=True
                )
                for pc in parts["bodies"]:
                    pc.set_facecolor("#ff7f0e")
                    pc.set_alpha(0.7)
                self.cost_ax.set_title("Cost Distribution")
                self.cost_ax.set_ylabel("Cost ($)")
                self.cost_ax.set_xticks([1])
                self.cost_ax.set_xticklabels(["All Actors"])
                self.cost_ax.yaxis.set_major_formatter(
                    plt.FuncFormatter(lambda x, p: f"${x:,.0f}")
                )
            all_gains = []
            for actor_data in self.actors_data.values():
                if actor_data["economics"]["total_gain"] > 0:
                    all_gains.append(actor_data["economics"]["total_gain"])
            if all_gains and any((g > 0 for g in all_gains)):
                parts = self.gain_ax.violinplot(
                    [all_gains], showmeans=True, showmedians=True
                )
                for pc in parts["bodies"]:
                    pc.set_facecolor("#2ca02c")
                    pc.set_alpha(0.7)
                self.gain_ax.set_title("Attacker Gains Distribution")
                self.gain_ax.set_ylabel("Gains ($)")
                self.gain_ax.set_xticks([1])
                self.gain_ax.set_xticklabels(["Attackers"])
                self.gain_ax.yaxis.set_major_formatter(
                    plt.FuncFormatter(lambda x, p: f"${x:,.0f}")
                )
            attacker_success = []
            defender_success = []
            for actor_id, actor_data in self.actors_data.items():
                actions = actor_data["actions"]
                if actions:
                    success_rate = len([a for a in actions if a["success"]]) / len(
                        actions
                    )
                    if "attacker" in actor_id.lower():
                        attacker_success.append(success_rate)
                    else:
                        defender_success.append(success_rate)
            success_data = []
            labels = []
            if attacker_success:
                success_data.append(attacker_success)
                labels.append("Attackers")
            if defender_success:
                success_data.append(defender_success)
                labels.append("Defenders")
            if success_data:
                parts = self.comparison_ax.violinplot(
                    success_data, showmeans=True, showmedians=True
                )
                colors = ["red", "blue"]
                for i, pc in enumerate(parts["bodies"]):
                    pc.set_facecolor(colors[i % len(colors)])
                    pc.set_alpha(0.7)
                self.comparison_ax.set_title("Success Rate Comparison")
                self.comparison_ax.set_ylabel("Success Rate")
                self.comparison_ax.set_xticks(range(1, len(labels) + 1))
                self.comparison_ax.set_xticklabels(labels)
                self.comparison_ax.set_ylim(0, 1)
            plt.tight_layout()
            self.stat_canvas.draw()
        except Exception as e:
            for ax in [self.damage_ax, self.cost_ax, self.gain_ax, self.comparison_ax]:
                ax.text(
                    0.5,
                    0.5,
                    f"Error creating plots:\n{str(e)}",
                    transform=ax.transAxes,
                    ha="center",
                    va="center",
                )
            self.stat_canvas.draw()

    def _create_scenario_comparison_plots(self):
        try:
            scenarios = self.scenario_results["scenarios"]
            variable_type = self.scenario_results.get(
                "variable_type", "attack_duration"
            )
            scenario_damages = []
            scenario_labels = []
            scenario_values = []
            for scenario in scenarios:
                if variable_type in ["attack_duration", "defense_duration"]:
                    value = scenario["duration"]
                    label = f"{value}h"
                else:
                    value = scenario["strategy"]
                    label = value
                histories = scenario["histories"]
                results = analyze_simulation_results(histories)
                damages = []
                for r in results:
                    damage = r.get("total_damage", 0)
                    if damage > 0:
                        damages.append(damage)
                if damages:
                    scenario_damages.append(damages)
                    scenario_labels.append(label)
                    scenario_values.append(value)
                else:
                    scenario_damages.append([0])
                    scenario_labels.append(label)
                    scenario_values.append(value)
            if not scenario_damages:
                self.stat_ax.text(
                    0.5,
                    0.5,
                    "No damage data available",
                    transform=self.stat_ax.transAxes,
                    ha="center",
                    va="center",
                    fontsize=14,
                )
                self.stat_canvas.draw()
                return
            positions = range(1, len(scenario_damages) + 1)
            parts = self.stat_ax.violinplot(
                scenario_damages,
                positions=positions,
                showmeans=True,
                showmedians=True,
                showextrema=True,
            )
            colors = plt.cm.RdYlGn_r(np.linspace(0.2, 0.8, len(scenarios)))
            for i, pc in enumerate(parts["bodies"]):
                pc.set_facecolor(colors[i])
                pc.set_alpha(0.8)
                pc.set_edgecolor("black")
                pc.set_linewidth(1.5)
            for partname in ("cbars", "cmins", "cmaxes", "cmedians", "cmeans"):
                if partname in parts:
                    vp = parts[partname]
                    vp.set_edgecolor("black")
                    vp.set_linewidth(2)
            for i, (pos, damages) in enumerate(zip(positions, scenario_damages)):
                x_jitter = np.random.normal(pos, 0.04, size=len(damages))
                self.stat_ax.scatter(
                    x_jitter, damages, alpha=0.4, s=30, color="black", zorder=3
                )
            if variable_type == "attack_duration":
                title = "Impact of Attack Action Duration on Total Damage"
                xlabel = "Attack Duration (hours)"
            elif variable_type == "defense_duration":
                title = "Impact of Defense Action Duration on Total Damage"
                xlabel = "Defense Duration (hours)"
            elif variable_type == "attacker_strategy":
                title = "Impact of Attacker Strategy on Total Damage"
                xlabel = "Attacker Strategy"
            elif variable_type == "defender_strategy":
                title = "Impact of Defender Strategy on Total Damage"
                xlabel = "Defender Strategy"
            else:
                title = "Impact of Parameter on Total Damage"
                xlabel = "Parameter Value"
            self.stat_ax.set_title(title, fontsize=16, fontweight="bold", pad=20)
            self.stat_ax.set_xlabel(xlabel, fontsize=14, fontweight="bold")
            self.stat_ax.set_ylabel("Total Damage ($)", fontsize=14, fontweight="bold")
            self.stat_ax.set_xticks(positions)
            self.stat_ax.set_xticklabels(scenario_labels, fontsize=12)
            self.stat_ax.yaxis.set_major_formatter(
                plt.FuncFormatter(lambda x, p: f"${x:,.0f}")
            )
            self.stat_ax.grid(True, alpha=0.3, linestyle="--", linewidth=0.5)
            self.stat_ax.set_axisbelow(True)
            stats_text = "Statistics per scenario:\n"
            for i, (label, damages) in enumerate(
                zip(scenario_labels, scenario_damages)
            ):
                mean_dmg = np.mean(damages)
                median_dmg = np.median(damages)
                runs = len(damages)
                stats_text += f"\n{label}: Mean=${mean_dmg:,.0f}, Median=${median_dmg:,.0f} ({runs} runs)"
            self.stat_ax.text(
                0.02,
                0.98,
                stats_text,
                transform=self.stat_ax.transAxes,
                fontsize=10,
                verticalalignment="top",
                bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.8),
            )
            plt.tight_layout()
            self.stat_canvas.draw()
        except Exception as e:
            self.stat_ax.clear()
            self.stat_ax.text(
                0.5,
                0.5,
                f"Error creating scenario comparison plot:\n{str(e)}",
                transform=self.stat_ax.transAxes,
                ha="center",
                va="center",
                fontsize=12,
                color="red",
            )
            self.stat_canvas.draw()
            print(f"Error in scenario comparison plot: {e}")
            import traceback

            traceback.print_exc()

    def _on_close(self):
        try:
            plt.close("all")
        except Exception as e:
            import logging

            logging.getLogger(__name__).debug(f"Error closing plots: {e}")
        self.window.destroy()
