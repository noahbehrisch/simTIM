"""Generates the violin-plot figure used in the ARES presentation.

Reproduces Fig. 2 of the TIM paper (damage vs. duration of the defensive action)
with simTIM's scenario-comparison feature. Run from the repository root:

    python docs/Presentation/make_figures.py
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from src.core import run_variable_scenarios
from src.visualization.analyzer import analyze_simulation_results

OUT_DIR = os.path.join(os.path.dirname(__file__), "figures")
DURATIONS = [2.0, 4.0, 8.0, 16.0]
RUNS = 60

ATTACKER = [
    {"id": "apt_group", "strategy": "escalation", "capacity": float("inf"), "budget": 100000}
]
DEFENDER = [{"id": "security_team", "strategy": "reactive", "capacity": 2, "budget": 100000}]


def main() -> int:
    os.makedirs(OUT_DIR, exist_ok=True)

    results = run_variable_scenarios(
        path_to_network_config="demo_network",
        scenarios=[{"duration": d, "runs": RUNS} for d in DURATIONS],
        variable_type="defense_duration",
        attackers=ATTACKER,
        defenders=DEFENDER,
        sim_time=168,
        detection_engine_type="early_weighted",
    )

    damages, labels = [], []
    for scenario in results["scenarios"]:
        analyzed = analyze_simulation_results(scenario["histories"])
        damages.append([r.get("total_damage", 0) for r in analyzed] or [0])
        labels.append(f"{scenario['duration']:.0f}")

    plt.rcParams.update({"font.size": 15, "axes.titlesize": 17, "axes.labelsize": 15})
    fig, ax = plt.subplots(figsize=(9, 5.2))

    positions = list(range(1, len(damages) + 1))
    parts = ax.violinplot(damages, positions=positions, showmeans=True, showextrema=True)
    for body in parts["bodies"]:
        body.set_facecolor("#C7410F")
        body.set_alpha(0.65)
        body.set_edgecolor("black")
        body.set_linewidth(1.2)
    for name in ("cbars", "cmins", "cmaxes", "cmeans"):
        if name in parts:
            parts[name].set_edgecolor("black")
            parts[name].set_linewidth(1.6)

    rng = np.random.default_rng(7)
    for pos, vals in zip(positions, damages, strict=False):
        ax.scatter(
            rng.normal(pos, 0.045, len(vals)), vals, s=18, color="black", alpha=0.35, zorder=3
        )

    ax.set_xticks(positions)
    ax.set_xticklabels(labels)
    ax.set_xlabel("Duration of the defensive action [hours]")
    ax.set_ylabel("Damage [USD]")
    ax.yaxis.set_major_formatter(lambda v, _: f"${v / 1000:,.0f}k")
    ax.grid(True, axis="y", alpha=0.3)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)

    fig.tight_layout()
    out = os.path.join(OUT_DIR, "violin_defense_duration.pdf")
    fig.savefig(out)
    fig.savefig(out.replace(".pdf", ".png"), dpi=200)

    means = [float(np.mean(d)) for d in damages]
    print(f"\nDamage per defense duration ({RUNS} runs each):")
    for label, vals in zip(labels, damages, strict=False):
        arr = np.array(vals, dtype=float)
        print(
            f"  {label:>3} h -> mean ${arr.mean():>10,.0f}   "
            f"median ${np.median(arr):>10,.0f}   sd ${arr.std():>10,.0f}"
        )
    print(f"\n  ratio last/first (mean): {means[-1] / means[0]:.2f}x")
    print(f"\nWritten: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
