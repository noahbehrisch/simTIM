import os
from typing import Any

import matplotlib.pyplot as plt

from .theme import get_theme


class BasePlotEngine:
    def __init__(self, output_dir: str = "plots"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.theme = get_theme()
        self.colors = self.theme.colors
        plt.style.use("default")

    def save_plot(self, fig: plt.Figure, filename: str, dpi: int = 300) -> None:
        filepath = os.path.join(self.output_dir, filename)
        fig.savefig(filepath, dpi=dpi, bbox_inches="tight")
        print(f"Plot saved to {filepath}")

    def show_plot(self, fig: plt.Figure) -> None:
        plt.show()

    def _setup_axes(
        self,
        ax: plt.Axes,
        xlabel: str,
        ylabel: str,
        title: str,
        max_time: float | None = None,
    ) -> None:
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.grid(True, alpha=0.3)
        if max_time:
            ax.set_xlim(0, max_time * 1.05)

    def _format_currency_axis(self, ax: plt.Axes, axis: str = "y") -> None:
        formatter = plt.FuncFormatter(lambda x, p: f"${x:,.0f}")
        if axis == "y":
            ax.yaxis.set_major_formatter(formatter)
        else:
            ax.xaxis.set_major_formatter(formatter)

    def _create_empty_plot(
        self, message: str, title: str, figsize: tuple[int, int] = (12, 6)
    ) -> plt.Figure:
        fig, ax = plt.subplots(figsize=figsize)
        ax.text(0.5, 0.5, message, ha="center", va="center", transform=ax.transAxes, fontsize=14)
        ax.set_title(title)
        return fig


class BaseTimelinePlotEngine(BasePlotEngine):
    def __init__(self, output_dir: str = "plots"):
        super().__init__(output_dir)
        self.event_types = self.theme.event_types

    def _get_max_time(self, history: list) -> float:
        max_time: float = 0
        for entry in history:
            if len(entry) >= 1 and isinstance(entry[0], int | float):
                max_time = max(max_time, float(entry[0]))
        return max_time

    def _extract_events(self, history: list) -> dict[str, list[dict[str, Any]]]:
        events: dict[str, list[dict[str, Any]]] = {et[0]: [] for et in self.event_types}
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

    def _extract_money(self, history: list, actors: list) -> dict[str, list]:
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
            "system_damage": [],
            "attacker_gain": [],
            "defender_cost": [],
        }
        totals = {"gain": 0, "damage": 0, "attacker_cost": 0, "defender_cost": 0}

        for event in economic_events:
            if event["type"] == "cost":
                if event["actor_type"] == "attacker":
                    totals["attacker_cost"] += event["value"]
                else:
                    totals["defender_cost"] += event["value"]
            elif event["type"] == "gain":
                totals["gain"] += event["value"]
            elif event["type"] == "damage":
                totals["damage"] += event["value"]

            timeline["times"].append(event["time"])
            timeline["system_damage"].append(totals["damage"])
            timeline["attacker_gain"].append(totals["gain"] - totals["attacker_cost"])
            timeline["defender_cost"].append(totals["defender_cost"])

        return timeline

    def _extract_nodes(self, history: list) -> dict[str, list[Any]]:
        timeline: dict[str, list[Any]] = {
            "times": [],
            "nodes_compromised": [],
            "nodes_admin": [],
            "nodes_visible": [],
        }

        ACCESS_RANK = {"NONE": 0, "VISIBLE": 1, "USER": 2, "ADMIN": 3}

        access_events = []
        for entry in history:
            if len(entry) >= 3:
                time, event_type, data = entry[0], entry[1], entry[2]
                if event_type == "access_changed" and isinstance(data, dict):
                    raw_access = data.get("new_access", "NONE")
                    access_str = raw_access.name if hasattr(raw_access, "name") else str(raw_access)
                    actor_id = data.get("actor_id", "")
                    access_events.append((time, data.get("node_id"), actor_id, access_str))

        if not access_events:
            return timeline

        access_map: dict[tuple[str, str], str] = {}
        for t in sorted({e[0] for e in access_events}):
            for event_time, node_id, actor_id, new_access in access_events:
                if event_time == t and node_id:
                    access_map[(node_id, actor_id)] = new_access

            node_max: dict[str, str] = {}
            for (nid, _aid), acc in access_map.items():
                prev = node_max.get(nid, "NONE")
                if ACCESS_RANK.get(acc.upper(), 0) > ACCESS_RANK.get(prev.upper(), 0):
                    node_max[nid] = acc

            admin = sum(1 for s in node_max.values() if s.upper() == "ADMIN")
            compromised = sum(1 for s in node_max.values() if s.upper() in ("USER", "ADMIN"))
            visible = sum(1 for s in node_max.values() if s.upper() == "VISIBLE")

            timeline["times"].append(t)
            timeline["nodes_admin"].append(admin)
            timeline["nodes_compromised"].append(compromised)
            timeline["nodes_visible"].append(visible)

        return timeline

    def _draw_step_line(
        self,
        ax: plt.Axes,
        times: list,
        values: list,
        label: str,
        color: str,
        linewidth: int = 2,
        linestyle: str = "-",
    ) -> None:
        ax.step(
            times,
            values,
            where="post",
            label=label,
            color=color,
            linewidth=linewidth,
            linestyle=linestyle,
        )

    def _draw_stacked_area(
        self,
        ax: plt.Axes,
        times: list,
        y_bottom: list,
        y_top: list,
        label: str,
        color: str,
        alpha: float = 0.7,
    ) -> None:
        ax.fill_between(
            times,
            y_bottom,
            y_top,
            label=label,
            color=color,
            alpha=alpha,
            step="post",
        )

    def _draw_event_scatter(
        self,
        ax: plt.Axes,
        events: dict[str, list[dict[str, Any]]],
        y_positions: dict[str, int],
        marker_size: int = 80,
        alpha: float = 0.7,
    ) -> None:
        for event_type, label, marker in self.event_types:
            event_list = events.get(event_type, [])
            if not event_list:
                continue
            times = [e["time"] for e in event_list]
            ys = [y_positions[e["actor_type"]] for e in event_list]
            ax.scatter(
                times,
                ys,
                label=label,
                marker=marker,
                c=self.colors.get(event_type, "#333333"),
                s=marker_size,
                alpha=alpha,
            )


class BaseViolinPlotEngine(BasePlotEngine):
    def __init__(self, output_dir: str = "plots"):
        super().__init__(output_dir)
        self.economic_colors = self.theme.get_economic_colors()

    def _draw_violin(
        self,
        ax: plt.Axes,
        data: list,
        positions: list | None = None,
        color: str | None = None,
        alpha: float = 0.7,
        show_means: bool = True,
        show_medians: bool = True,
        show_extrema: bool = True,
    ) -> dict | None:
        if not data or not any(len(d) > 0 for d in data if isinstance(d, list)):
            return None

        if positions is None:
            positions = list(range(len(data)))

        parts = ax.violinplot(
            data,
            positions=positions,
            showmeans=show_means,
            showmedians=show_medians,
            showextrema=show_extrema,
        )

        if color and "bodies" in parts:
            for pc in parts["bodies"]:
                pc.set_facecolor(color)
                pc.set_alpha(alpha)

        if "cmeans" in parts:
            parts["cmeans"].set_color("black")
            parts["cmeans"].set_linewidth(2)

        return parts

    def _setup_violin_axes(
        self,
        ax: plt.Axes,
        title: str,
        ylabel: str,
        xticks: list,
        xticklabels: list,
        currency_format: bool = True,
    ) -> None:
        ax.set_title(title)
        ax.set_ylabel(ylabel)
        ax.set_xticks(xticks)
        ax.set_xticklabels(xticklabels)
        if currency_format:
            self._format_currency_axis(ax)
        ax.grid(True, alpha=0.3)

    def _group_results_by_parameter(
        self, results: list[dict[str, Any]], parameter: str, values: list[float]
    ) -> list[list[float]]:
        grouped = []
        for val in values:
            matching = [
                r.get("total_damage", 0)
                for r in results
                if abs(r.get("parameters", {}).get(parameter, 0) - val) < 0.01
            ]
            grouped.append(matching)
        return grouped
