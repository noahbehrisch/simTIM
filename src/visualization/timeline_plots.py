import os
from typing import Any

import matplotlib.pyplot as plt

from .theme import get_theme

_theme = get_theme()
COLORS = _theme.colors
EVENT_TYPES = _theme.event_types


def _get_max_time(history: list) -> float:
    max_time: float = 0
    for entry in history:
        if len(entry) >= 1 and isinstance(entry[0], int | float):
            max_time = max(max_time, float(entry[0]))
    return max_time


def _extract_events(history: list) -> dict[str, list[dict[str, Any]]]:
    events: dict[str, list[dict[str, Any]]] = {et[0]: [] for et in EVENT_TYPES}
    events["action_aborted"] = []

    for entry in history:
        if len(entry) < 3:
            continue
        time, event_type, data = entry[0], entry[1], entry[2]
        if event_type not in events:
            continue
        if not isinstance(data, dict) or "actor" not in data:
            continue
        actor = data["actor"]
        if hasattr(actor, "is_attacker") and actor.is_attacker:
            actor_type = "attacker"
        elif hasattr(actor, "is_defender") and actor.is_defender:
            actor_type = "defender"
        else:
            continue
        events[event_type].append({"time": time, "actor_type": actor_type, "data": data})
    return events


def _extract_money(history: list, actors: list) -> dict[str, list]:
    economic_events = []

    for actor in actors:
        is_attacker = hasattr(actor, "is_attacker") and actor.is_attacker
        actor_type = "attacker" if is_attacker else "defender"

        for event in getattr(actor, "action_history", []):
            economic_events.append(
                {
                    "time": event["timestamp"],
                    "type": "cost",
                    "value": event["cost"],
                    "actor_type": actor_type,
                }
            )
        for event in getattr(actor, "economic_events", []):
            economic_events.append(
                {
                    "time": event["timestamp"],
                    "type": event["type"],
                    "value": event["value"],
                    "actor_type": actor_type,
                }
            )

    economic_events.sort(key=lambda e: e["time"])

    timeline: dict[str, list[Any]] = {
        "times": [],
        "cumulative_costs": [],
        "cumulative_gains": [],
        "cumulative_damage": [],
        "attacker_costs": [],
        "defender_costs": [],
    }
    totals = {"cost": 0, "gain": 0, "damage": 0, "attacker_cost": 0, "defender_cost": 0}

    for event in economic_events:
        if event["type"] == "cost":
            totals["cost"] += event["value"]
            if event["actor_type"] == "attacker":
                totals["attacker_cost"] += event["value"]
            else:
                totals["defender_cost"] += event["value"]
        elif event["type"] == "gain":
            totals["gain"] += event["value"]
        elif event["type"] == "damage":
            totals["damage"] += event["value"]

        timeline["times"].append(event["time"])
        timeline["cumulative_costs"].append(totals["cost"])
        timeline["cumulative_gains"].append(totals["gain"])
        timeline["cumulative_damage"].append(totals["damage"])
        timeline["attacker_costs"].append(totals["attacker_cost"])
        timeline["defender_costs"].append(totals["defender_cost"])

    return timeline


def _extract_nodes(economic_model: Any) -> dict[str, list[Any]]:
    access_changes = getattr(economic_model, "access_state_changes", [])
    timeline: dict[str, list[Any]] = {
        "times": [],
        "nodes_compromised": [],
        "nodes_admin": [],
        "nodes_visible": [],
    }

    if not access_changes:
        return timeline

    node_states = {}
    for t in sorted({c[0] for c in access_changes}):
        for change in access_changes:
            if change[0] == t:
                node_states[change[1]] = change[4]

        admin = sum(1 for s in node_states.values() if s in ["ADMIN", "admin", 3])
        compromised = sum(
            1 for s in node_states.values() if s in ["USER", "ADMIN", "user", "admin", 2, 3]
        )
        visible = sum(1 for s in node_states.values() if s in ["VISIBLE", "visible", 1])

        timeline["times"].append(t)
        timeline["nodes_admin"].append(admin)
        timeline["nodes_compromised"].append(compromised)
        timeline["nodes_visible"].append(visible)

    return timeline


def _setup_axes(ax, xlabel, ylabel, title, max_time=None):
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(True, alpha=0.3)
    if max_time:
        ax.set_xlim(0, max_time * 1.05)


class TimeSeriesPlotEngine:
    def __init__(self, output_dir="plots"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        plt.style.use("default")
        self.colors = COLORS

    def create_events_over_time_plot(self, history, title="Events Over Time", sim_time=None):
        events = _extract_events(history)
        max_time = sim_time if sim_time else _get_max_time(history)

        fig, ax = plt.subplots(figsize=(12, 6))
        y_pos = {"attacker": 1, "defender": 0}

        for event_type, label, marker in EVENT_TYPES:
            event_list = events.get(event_type, [])
            if not event_list:
                continue
            times = [e["time"] for e in event_list]
            ys = [y_pos[e["actor_type"]] for e in event_list]
            ax.scatter(
                times,
                ys,
                label=label,
                marker=marker,
                c=self.colors.get(event_type, "#333333"),
                s=80,
                alpha=0.7,
            )

        ax.set_yticks([0, 1])
        ax.set_yticklabels(["Defender", "Attacker"])
        ax.set_ylim(-0.3, 1.3)
        ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1))
        _setup_axes(ax, "Time (hours)", "Actor Type", title, max_time)

        plt.tight_layout()
        return fig

    def create_money_over_time_plot(self, history, actors, title="Economic Impact Over Time"):
        timeline = _extract_money(history, actors)
        max_time = _get_max_time(history)

        if not timeline["times"]:
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.text(
                0.5,
                0.5,
                "No economic data available",
                ha="center",
                va="center",
                transform=ax.transAxes,
                fontsize=14,
            )
            ax.set_title(title)
            return fig

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
        fig.suptitle(title, fontsize=14)
        times = timeline["times"]

        ax1.step(
            times,
            timeline["attacker_costs"],
            where="post",
            label="Attacker Costs",
            color=self.colors["attacker"],
            linewidth=2,
        )
        ax1.step(
            times,
            timeline["defender_costs"],
            where="post",
            label="Defender Costs",
            color=self.colors["defender"],
            linewidth=2,
        )
        ax1.step(
            times,
            timeline["cumulative_costs"],
            where="post",
            label="Total Costs",
            color=self.colors["cost"],
            linewidth=2,
            linestyle="--",
        )
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"${x:,.0f}"))
        ax1.legend(loc="upper left")
        _setup_axes(ax1, "", "Cumulative Cost ($)", "", max_time)

        ax2.step(
            times,
            timeline["cumulative_gains"],
            where="post",
            label="Attacker Gains",
            color=self.colors["gain"],
            linewidth=2,
        )
        ax2.step(
            times,
            timeline["cumulative_damage"],
            where="post",
            label="System Damage",
            color=self.colors["damage"],
            linewidth=2,
        )
        ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"${x:,.0f}"))
        ax2.legend(loc="upper left")
        _setup_axes(ax2, "Time (hours)", "Cumulative Value ($)", "", max_time)

        plt.tight_layout()
        return fig

    def create_nodes_over_time_plot(
        self,
        economic_model,
        total_nodes=None,
        title="Node Compromise Over Time",
        max_time=None,
    ):
        timeline = _extract_nodes(economic_model)

        if not timeline["times"]:
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.text(
                0.5,
                0.5,
                "No node access changes recorded",
                ha="center",
                va="center",
                transform=ax.transAxes,
                fontsize=14,
            )
            ax.set_title(title)
            return fig

        fig, ax = plt.subplots(figsize=(12, 6))
        times = timeline["times"]
        admin = timeline["nodes_admin"]
        compromised = timeline["nodes_compromised"]
        visible = timeline["nodes_visible"]

        ax.fill_between(
            times,
            0,
            admin,
            label="Admin Access",
            color=self.colors["admin"],
            alpha=0.7,
            step="post",
        )
        ax.fill_between(
            times,
            admin,
            compromised,
            label="User Access",
            color=self.colors["user"],
            alpha=0.7,
            step="post",
        )
        ax.fill_between(
            times,
            compromised,
            [c + v for c, v in zip(compromised, visible, strict=False)],
            label="Visible",
            color=self.colors["visible"],
            alpha=0.7,
            step="post",
        )

        if total_nodes:
            safe = [total_nodes - c - v for c, v in zip(compromised, visible, strict=False)]
            ax.fill_between(
                times,
                [c + v for c, v in zip(compromised, visible, strict=False)],
                [c + v + s for c, v, s in zip(compromised, visible, safe, strict=False)],
                label="Safe",
                color=self.colors["none"],
                alpha=0.5,
                step="post",
            )
            ax.set_ylim(0, total_nodes)

        ax.legend(loc="upper left")
        if not max_time and times:
            max_time = max(times)
        _setup_axes(ax, "Time (hours)", "Number of Nodes", title, max_time)

        plt.tight_layout()
        return fig

    def create_combined_timeline_plot(
        self,
        history,
        actors,
        economic_model,
        total_nodes=None,
        title="Simulation Timeline",
    ):
        events = _extract_events(history)
        money = _extract_money(history, actors)
        nodes = _extract_nodes(economic_model)
        max_time = _get_max_time(history)

        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(14, 12), sharex=True)
        fig.suptitle(title, fontsize=16)

        y_pos = {"attacker": 1, "defender": 0}
        for event_type, label, marker in EVENT_TYPES:
            event_list = events.get(event_type, [])
            if not event_list:
                continue
            times = [e["time"] for e in event_list]
            ys = [y_pos[e["actor_type"]] for e in event_list]
            ax1.scatter(
                times,
                ys,
                label=label,
                marker=marker,
                c=self.colors.get(event_type, "#333333"),
                s=60,
                alpha=0.7,
            )
        ax1.set_yticks([0, 1])
        ax1.set_yticklabels(["Defender", "Attacker"])
        ax1.set_ylim(-0.3, 1.3)
        ax1.legend(loc="upper right", ncol=5, fontsize=8)
        _setup_axes(ax1, "", "Actor", "Events Timeline", max_time)

        if money["times"]:
            ax2.step(
                money["times"],
                money["attacker_costs"],
                where="post",
                label="Attacker Cost",
                color=self.colors["attacker"],
                linewidth=2,
            )
            ax2.step(
                money["times"],
                money["defender_costs"],
                where="post",
                label="Defender Cost",
                color=self.colors["defender"],
                linewidth=2,
            )
            ax2.step(
                money["times"],
                money["cumulative_gains"],
                where="post",
                label="Attacker Gain",
                color=self.colors["gain"],
                linewidth=2,
                linestyle="--",
            )
        ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"${x:,.0f}"))
        ax2.legend(loc="upper left", ncol=3, fontsize=8)
        _setup_axes(ax2, "", "Value ($)", "Economic Timeline", max_time)

        if nodes["times"]:
            times = nodes["times"]
            ax3.fill_between(
                times,
                0,
                nodes["nodes_admin"],
                label="Admin",
                color=self.colors["admin"],
                alpha=0.7,
                step="post",
            )
            ax3.fill_between(
                times,
                nodes["nodes_admin"],
                nodes["nodes_compromised"],
                label="User",
                color=self.colors["user"],
                alpha=0.7,
                step="post",
            )
            if total_nodes:
                ax3.axhline(
                    y=total_nodes,
                    color="gray",
                    linestyle="--",
                    label=f"Total ({total_nodes})",
                    alpha=0.5,
                )
        ax3.legend(loc="upper left", ncol=3, fontsize=8)
        _setup_axes(
            ax3,
            "Time (hours)",
            "Nodes Compromised",
            "Node Compromise Timeline",
            max_time,
        )

        plt.tight_layout()
        return fig

    def save_plot(self, fig, filename, dpi=300):
        filepath = os.path.join(self.output_dir, filename)
        fig.savefig(filepath, dpi=dpi, bbox_inches="tight")
        print(f"Plot saved to {filepath}")

    def show_plot(self, fig):
        plt.show()
