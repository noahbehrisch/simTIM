"""Attack path visualizer — replays event history on the network topology.

For a selected simulation run, colours each node by the highest access level
any attacker achieved on it *up to the chosen time* and highlights links
traversed by lateral-movement (link) actions.  A time slider and play/pause
button let users animate the attack progression.
"""

import json
import logging
import math
import tkinter as tk
from tkinter import ttk

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

from src.visualization.theme import get_theme

logger = logging.getLogger(__name__)

ACCESS_RANK = {"NONE": 0, "VISIBLE": 1, "USER": 2, "ADMIN": 3}
ACCESS_LABELS = {0: "NONE", 1: "VISIBLE", 2: "USER", 3: "ADMIN"}

# Animation speed: how many simulation-hours advance per real-time tick
_PLAY_STEP_HOURS = 0.5
_PLAY_INTERVAL_MS = 80  # milliseconds between ticks


def _normalise_access(value) -> str:
    """Accept enum, string, or int and return upper-case access name."""
    if hasattr(value, "name"):
        return value.name.upper()
    s = str(value).upper()
    if s in ACCESS_RANK:
        return s
    return "NONE"


def _load_network_topology(network_path: str) -> dict:
    """Load node positions and link info from the network JSON."""
    with open(network_path) as f:
        data = json.load(f)

    nodes: dict[str, dict] = {}
    for node in data.get("nodes", []):
        nid = node["id"]
        nodes[nid] = {
            "name": node.get("name", nid),
            "exposed": node.get("exposed_to_internet", False),
            "x": node.get("properties", {}).get("x"),
            "y": node.get("properties", {}).get("y"),
        }

    links: list[tuple[str, str]] = []
    for link in data.get("links", []):
        n1 = link.get("node1") or link.get("source")
        n2 = link.get("node2") or link.get("target")
        if n1 and n2:
            links.append((n1, n2))

    return {"nodes": nodes, "links": links}


def _compute_positions(nodes: dict[str, dict]) -> dict[str, tuple[float, float]]:
    """Return {node_id: (x, y)}, using saved coords or circular fallback."""
    positions: dict[str, tuple[float, float]] = {}
    ids = list(nodes.keys())
    n = len(ids)
    radius = 5
    for i, nid in enumerate(ids):
        nd = nodes[nid]
        if nd["x"] is not None and nd["y"] is not None:
            positions[nid] = (nd["x"] / 50, nd["y"] / 50)
        else:
            angle = 2 * math.pi * i / max(n, 1)
            positions[nid] = (radius * math.cos(angle), radius * math.sin(angle))
    return positions


def _get_max_time(history: list) -> float:
    """Return the latest timestamp in a history list."""
    max_t = 0.0
    for entry in history:
        if len(entry) >= 1 and isinstance(entry[0], (int, float)):
            max_t = max(max_t, float(entry[0]))
    return max_t


def extract_attack_path(history: list, up_to_time: float | None = None) -> dict:
    """Replay one run's history and return per-node max access + traversed links.

    Parameters
    ----------
    history : list
        Event history for one simulation run.
    up_to_time : float or None
        If given, only consider events with timestamp <= this value.

    Returns
    -------
    dict with keys:
        node_access : dict[str, str]   – highest access name per node
        traversed   : set[tuple[str,str]] – (source, target) link pairs used
    """
    node_access: dict[str, int] = {}  # node_id -> max rank
    traversed: set[tuple[str, str]] = set()

    for entry in history:
        if len(entry) < 3:
            continue
        event_time, event_type, data = entry[0], entry[1], entry[2]
        if not isinstance(data, dict):
            continue

        # Time filter
        if up_to_time is not None and isinstance(event_time, (int, float)):
            if event_time > up_to_time:
                continue

        # Track access changes
        if event_type == "access_changed":
            nid = data.get("node_id")
            new = _normalise_access(data.get("new_access", "NONE"))
            rank = ACCESS_RANK.get(new, 0)
            if nid and rank > node_access.get(nid, 0):
                node_access[nid] = rank

        # Track link traversals (successful link actions)
        if event_type == "action_succeeded" and data.get("is_link_action"):
            target = data.get("target")
            postcond_target = data.get("postcondition_target")
            actor = data.get("actor")

            source_id = None
            target_id = None

            # Link object
            if target is not None and hasattr(target, "node1") and hasattr(target, "node2"):
                source_id = target.node1.id
                target_id = target.node2.id
            elif postcond_target and hasattr(postcond_target, "id"):
                target_id = postcond_target.id
                # Try to find source from actor's visible nodes
                if actor is not None and hasattr(actor, "visible_nodes"):
                    for vn in actor.visible_nodes:
                        nid = vn.id if hasattr(vn, "id") else str(vn)
                        if nid != target_id:
                            source_id = nid
                            break

            if source_id and target_id:
                traversed.add((source_id, target_id))

    named: dict[str, str] = {
        nid: ACCESS_LABELS.get(rank, "NONE") for nid, rank in node_access.items()
    }
    return {"node_access": named, "traversed": traversed}


class AttackPathPanel:
    """Tkinter panel that draws the network with attack-path colouring.

    Includes a time slider and play/pause button to animate the attack
    progression through simulation time.
    """

    def __init__(
        self,
        parent: tk.Widget,
        network_path: str,
        all_histories: list,
        bg_color: str = "#f0f0f0",
        sim_time: float | None = None,
    ):
        self.parent = parent
        self.all_histories = all_histories
        self.bg_color = bg_color
        self.sim_time = sim_time
        self.theme = get_theme()
        self._playing = False
        self._after_id: str | None = None

        # Load topology once
        topo = _load_network_topology(network_path)
        self.topo_nodes = topo["nodes"]
        self.topo_links = topo["links"]
        self.positions = _compute_positions(self.topo_nodes)

        access_colors = self.theme.get_access_level_colors()
        network_colors = self.theme.get_network_colors()
        self.color_map = {
            "ADMIN": access_colors["admin"],
            "USER": access_colors["user"],
            "VISIBLE": access_colors["visible"],
            "NONE": network_colors["internal"],
        }
        self.link_color = network_colors["link"]
        self.attack_link_color = network_colors["attack_path"]

        self._build_ui()

    # ── UI ─────────────────────────────────────────────────────────────
    def _build_ui(self):
        self.frame = tk.Frame(self.parent, bg=self.bg_color)
        self.frame.pack(fill=tk.BOTH, expand=True)

        # ── Top controls row: run selector ──
        top_frame = tk.Frame(self.frame, bg=self.bg_color)
        top_frame.pack(fill=tk.X, padx=10, pady=5)

        if len(self.all_histories) > 1:
            tk.Label(top_frame, text="Select Run:", bg=self.bg_color).pack(side=tk.LEFT, padx=5)
            self.run_var = tk.StringVar(value="Run 1")
            options = [f"Run {i + 1}" for i in range(len(self.all_histories))]
            combo = ttk.Combobox(
                top_frame,
                textvariable=self.run_var,
                values=options,
                state="readonly",
                width=15,
            )
            combo.pack(side=tk.LEFT, padx=5)
            combo.bind("<<ComboboxSelected>>", lambda _e: self._on_run_changed())

        # ── Matplotlib figure ──
        self.fig, self.ax = plt.subplots(figsize=(10, 8))
        self.canvas = FigureCanvasTkAgg(self.fig, self.frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # ── Bottom controls: play button + time slider ──
        controls_frame = tk.Frame(self.frame, bg=self.bg_color)
        controls_frame.pack(fill=tk.X, padx=10, pady=(0, 2))

        # Play / Pause button
        self.play_btn = tk.Button(
            controls_frame,
            text="\u25b6 Play",
            command=self._toggle_play,
            width=8,
            font=("TkDefaultFont", 10),
        )
        self.play_btn.pack(side=tk.LEFT, padx=(0, 8))

        # Time label (left of slider)
        self.time_label = tk.Label(
            controls_frame,
            text="t = 0.0 h",
            bg=self.bg_color,
            font=("TkDefaultFont", 10),
        )
        self.time_label.pack(side=tk.LEFT, padx=(0, 5))

        # Time slider
        max_time = self._current_max_time()
        self.time_var = tk.DoubleVar(value=max_time)
        self.slider = ttk.Scale(
            controls_frame,
            from_=0.0,
            to=max_time if max_time > 0 else 1.0,
            orient=tk.HORIZONTAL,
            variable=self.time_var,
            command=self._on_slider_moved,
        )
        self.slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Max-time label (right of slider)
        self.max_label = tk.Label(
            controls_frame,
            text=f"/ {max_time:.1f} h",
            bg=self.bg_color,
            font=("TkDefaultFont", 10),
        )
        self.max_label.pack(side=tk.LEFT, padx=(0, 5))

        # ── Matplotlib toolbar (save / zoom / pan) ──
        toolbar_frame = tk.Frame(self.frame)
        toolbar_frame.pack(fill=tk.X, side=tk.BOTTOM)
        self.toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        self.toolbar.update()

        # Initial draw at full time
        self._redraw()

    # ── Helpers ────────────────────────────────────────────────────────
    def _get_run_id(self) -> int:
        if hasattr(self, "run_var"):
            return int(self.run_var.get().split()[1]) - 1
        return 0

    def _current_max_time(self) -> float:
        """Max time for the currently selected run."""
        run_id = self._get_run_id()
        history = self.all_histories[run_id] if run_id < len(self.all_histories) else []
        t = _get_max_time(history)
        if self.sim_time and self.sim_time > t:
            t = self.sim_time
        return t

    def _on_run_changed(self):
        """Called when user picks a different run."""
        self._stop_play()
        max_time = self._current_max_time()
        self.slider.configure(to=max_time if max_time > 0 else 1.0)
        self.time_var.set(max_time)
        self.max_label.configure(text=f"/ {max_time:.1f} h")
        self._redraw()

    def _on_slider_moved(self, _value=None):
        """Called on every slider drag tick."""
        self._redraw()

    # ── Play / Pause ──────────────────────────────────────────────────
    def _toggle_play(self):
        if self._playing:
            self._stop_play()
        else:
            self._start_play()

    def _start_play(self):
        self._playing = True
        self.play_btn.configure(text="\u23f8 Pause")
        # If already at the end, restart from 0
        max_t = self._current_max_time()
        if self.time_var.get() >= max_t - 0.01:
            self.time_var.set(0.0)
        self._play_tick()

    def _stop_play(self):
        self._playing = False
        self.play_btn.configure(text="\u25b6 Play")
        if self._after_id is not None:
            try:
                self.frame.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None

    def _play_tick(self):
        if not self._playing:
            return
        max_t = self._current_max_time()
        current = self.time_var.get()
        next_t = current + _PLAY_STEP_HOURS
        if next_t >= max_t:
            next_t = max_t
            self.time_var.set(next_t)
            self._redraw()
            self._stop_play()
            return
        self.time_var.set(next_t)
        self._redraw()
        self._after_id = self.frame.after(_PLAY_INTERVAL_MS, self._play_tick)

    # ── Drawing ────────────────────────────────────────────────────────
    def _redraw(self):
        run_id = self._get_run_id()
        history = self.all_histories[run_id] if run_id < len(self.all_histories) else []
        current_time = self.time_var.get()
        path_info = extract_attack_path(history, up_to_time=current_time)

        # Update time label
        self.time_label.configure(text=f"t = {current_time:.1f} h")

        ax = self.ax
        ax.clear()
        ax.set_aspect("equal", adjustable="datalim")

        if not self.positions:
            ax.text(0.5, 0.5, "No nodes to display", ha="center", va="center")
            self.canvas.draw()
            return

        # Bounds
        xs = [p[0] for p in self.positions.values()]
        ys = [p[1] for p in self.positions.values()]
        margin = 1.5
        ax.set_xlim(min(xs) - margin, max(xs) + margin)
        ax.set_ylim(min(ys) - margin, max(ys) + margin)

        # Draw links
        traversed = path_info["traversed"]
        for n1, n2 in self.topo_links:
            p1 = self.positions.get(n1)
            p2 = self.positions.get(n2)
            if not p1 or not p2:
                continue
            is_traversed = (n1, n2) in traversed or (n2, n1) in traversed
            color = self.attack_link_color if is_traversed else self.link_color
            width = 3.5 if is_traversed else 1.5
            alpha = 1.0 if is_traversed else 0.5
            ax.plot(
                [p1[0], p2[0]],
                [p1[1], p2[1]],
                color=color,
                linewidth=width,
                alpha=alpha,
                zorder=1,
            )

        # Draw nodes
        node_access = path_info["node_access"]
        for nid, pos in self.positions.items():
            access = node_access.get(nid, "NONE")
            color = self.color_map.get(access, self.color_map["NONE"])
            ax.scatter(
                pos[0],
                pos[1],
                color=color,
                s=500,
                zorder=2,
                edgecolors="black",
                linewidths=1.5,
            )
            label = nid[:12]
            ax.text(
                pos[0],
                pos[1],
                label,
                fontsize=8,
                ha="center",
                va="center",
                zorder=3,
                fontweight="bold",
            )

        # Legend
        from matplotlib.lines import Line2D

        handles = [
            Line2D(
                [0],
                [0],
                marker="o",
                color="w",
                markerfacecolor=self.color_map["ADMIN"],
                markersize=10,
                label="Admin",
            ),
            Line2D(
                [0],
                [0],
                marker="o",
                color="w",
                markerfacecolor=self.color_map["USER"],
                markersize=10,
                label="User",
            ),
            Line2D(
                [0],
                [0],
                marker="o",
                color="w",
                markerfacecolor=self.color_map["VISIBLE"],
                markersize=10,
                label="Visible",
            ),
            Line2D(
                [0],
                [0],
                marker="o",
                color="w",
                markerfacecolor=self.color_map["NONE"],
                markersize=10,
                label="No Access",
            ),
            Line2D([0], [0], color=self.attack_link_color, linewidth=3, label="Traversed Link"),
            Line2D([0], [0], color=self.link_color, linewidth=1.5, alpha=0.5, label="Network Link"),
        ]
        ax.legend(handles=handles, loc="upper left", bbox_to_anchor=(1.01, 1), frameon=True)

        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.set_title(
            f"Attack Path \u2014 Run {run_id + 1}  [t = {current_time:.1f} h]",
            fontsize=14,
            fontweight="bold",
        )

        self.fig.tight_layout()
        self.canvas.draw()

    # ── Cleanup ────────────────────────────────────────────────────────
    def destroy(self):
        self._stop_play()
        try:
            if hasattr(self, "toolbar"):
                self.toolbar.destroy()
            if hasattr(self, "canvas"):
                self.canvas.get_tk_widget().destroy()
            plt.close(self.fig)
        except Exception:
            pass
        try:
            self.frame.destroy()
        except Exception:
            pass
