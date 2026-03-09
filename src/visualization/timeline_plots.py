import matplotlib.pyplot as plt

from .base import BaseTimelinePlotEngine


class TimeSeriesPlotEngine(BaseTimelinePlotEngine):
    def __init__(self, output_dir: str = "plots"):
        super().__init__(output_dir)

    def create_events_over_time_plot(
        self, history: list, title: str = "Events Over Time", sim_time: float | None = None
    ) -> plt.Figure:
        events = self._extract_events(history)
        max_time = sim_time if sim_time else self._get_max_time(history)

        fig, ax = plt.subplots(figsize=(12, 6))
        y_pos = {"attacker": 1, "defender": 0}

        self._draw_event_scatter(ax, events, y_pos)

        ax.set_yticks([0, 1])
        ax.set_yticklabels(["Defender", "Attacker"])
        ax.set_ylim(-0.3, 1.3)
        ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1))
        self._setup_axes(ax, "Time (hours)", "Actor Type", title, max_time)

        plt.tight_layout()
        return fig

    def create_money_over_time_plot(
        self, history: list, actors: list, title: str = "Economic Impact Over Time"
    ) -> plt.Figure:
        timeline = self._extract_money(history, actors)
        max_time = self._get_max_time(history)

        if not timeline["times"]:
            return self._create_empty_plot("No economic data available", title)

        fig, ax = plt.subplots(figsize=(12, 6))
        times = timeline["times"]

        self._draw_step_line(
            ax, times, timeline["system_damage"], "System Damage", self.colors["damage"]
        )
        self._draw_step_line(
            ax, times, timeline["attacker_gain"], "Attacker Gain", self.colors["gain"]
        )
        self._draw_step_line(
            ax, times, timeline["defender_cost"], "Defender Cost", self.colors["defender"]
        )
        self._format_currency_axis(ax)
        ax.legend(loc="upper left")
        self._setup_axes(ax, "Time (hours)", "Value ($)", title, max_time)

        plt.tight_layout()
        return fig

    def create_nodes_over_time_plot(
        self,
        history: list,
        total_nodes: int | None = None,
        title: str = "Node Compromise Over Time",
        max_time: float | None = None,
    ) -> plt.Figure:
        timeline = self._extract_nodes(history)

        if not timeline["times"]:
            return self._create_empty_plot("No node access changes recorded", title)

        fig, ax = plt.subplots(figsize=(12, 6))
        times = timeline["times"]
        admin = timeline["nodes_admin"]
        compromised = timeline["nodes_compromised"]
        visible = timeline["nodes_visible"]

        self._draw_stacked_area(
            ax, times, [0] * len(times), admin, "Admin Access", self.colors["admin"]
        )
        self._draw_stacked_area(ax, times, admin, compromised, "User Access", self.colors["user"])

        visible_top = [c + v for c, v in zip(compromised, visible, strict=False)]
        self._draw_stacked_area(
            ax, times, compromised, visible_top, "Visible", self.colors["visible"]
        )

        if total_nodes:
            safe = [total_nodes - c - v for c, v in zip(compromised, visible, strict=False)]
            safe_top = [c + v + s for c, v, s in zip(compromised, visible, safe, strict=False)]
            self._draw_stacked_area(
                ax, times, visible_top, safe_top, "Safe", self.colors["none"], alpha=0.5
            )
            ax.set_ylim(0, total_nodes)

        ax.legend(loc="upper left")
        if not max_time and times:
            max_time = max(times)
        self._setup_axes(ax, "Time (hours)", "Number of Nodes", title, max_time)

        plt.tight_layout()
        return fig

    def create_combined_timeline_plot(
        self,
        history: list,
        actors: list,
        total_nodes: int | None = None,
        title: str = "Simulation Timeline",
    ) -> plt.Figure:
        events = self._extract_events(history)
        money = self._extract_money(history, actors)
        nodes = self._extract_nodes(history)
        max_time = self._get_max_time(history)

        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(14, 12), sharex=True)
        fig.suptitle(title, fontsize=16)

        y_pos = {"attacker": 1, "defender": 0}
        self._draw_event_scatter(ax1, events, y_pos, marker_size=60)
        ax1.set_yticks([0, 1])
        ax1.set_yticklabels(["Defender", "Attacker"])
        ax1.set_ylim(-0.3, 1.3)
        ax1.legend(loc="upper right", ncol=5, fontsize=8)
        self._setup_axes(ax1, "", "Actor", "Events Timeline", max_time)

        if money["times"]:
            self._draw_step_line(
                ax2,
                money["times"],
                money["system_damage"],
                "System Damage",
                self.colors["damage"],
            )
            self._draw_step_line(
                ax2,
                money["times"],
                money["attacker_gain"],
                "Attacker Gain",
                self.colors["gain"],
            )
            self._draw_step_line(
                ax2,
                money["times"],
                money["defender_cost"],
                "Defender Cost",
                self.colors["defender"],
            )
        self._format_currency_axis(ax2)
        ax2.legend(loc="upper left", ncol=3, fontsize=8)
        self._setup_axes(ax2, "", "Value ($)", "Economic Timeline", max_time)

        if nodes["times"]:
            times = nodes["times"]
            self._draw_stacked_area(
                ax3, times, [0] * len(times), nodes["nodes_admin"], "Admin", self.colors["admin"]
            )
            self._draw_stacked_area(
                ax3,
                times,
                nodes["nodes_admin"],
                nodes["nodes_compromised"],
                "User",
                self.colors["user"],
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
        self._setup_axes(
            ax3, "Time (hours)", "Nodes Compromised", "Node Compromise Timeline", max_time
        )

        plt.tight_layout()
        return fig
