from typing import Any

import matplotlib.pyplot as plt
import numpy as np

from .base import BaseViolinPlotEngine


class ViolinPlotEngine(BaseViolinPlotEngine):
    def __init__(self, output_dir: str = "plots"):
        super().__init__(output_dir)

    def create_damage_distribution_plot(
        self,
        simulation_results: list[dict[str, Any]],
        parameter_name: str,
        parameter_values: list[float],
        title: str = "Damage Distribution Analysis",
    ) -> plt.Figure:
        damage_by_param = self._group_results_by_parameter(
            simulation_results, parameter_name, parameter_values
        )

        fig, ax = plt.subplots(figsize=(10, 6))
        self._draw_violin(
            ax,
            damage_by_param,
            positions=list(range(len(parameter_values))),
            color=self.economic_colors["damage"],
        )

        ax.set_xlabel(f"Duration of {parameter_name.replace('_', ' ').title()} (hours)")
        self._setup_violin_axes(
            ax,
            title,
            "Damage [USD]",
            list(range(len(parameter_values))),
            [f"{val:.0f}" for val in parameter_values],
        )

        plt.tight_layout()
        return fig

    def create_economic_comparison_plot(
        self,
        simulation_results: list[dict[str, Any]],
        title: str = "Economic Impact Comparison",
    ) -> plt.Figure:
        damages = [r.get("total_damage", 0) for r in simulation_results]
        gains = [r.get("total_attacker_gains", 0) for r in simulation_results]
        costs = [r.get("total_costs", 0) for r in simulation_results]

        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 5))
        fig.suptitle(title, fontsize=14)

        if damages and any(d > 0 for d in damages):
            self._draw_violin(ax1, [damages], positions=[1], color=self.economic_colors["damage"])
        self._setup_violin_axes(ax1, "System Damage", "Damage ($)", [1], ["Damage"])

        if gains and any(g > 0 for g in gains):
            self._draw_violin(ax2, [gains], positions=[1], color=self.economic_colors["gain"])
        self._setup_violin_axes(ax2, "Attacker Gains", "Gains ($)", [1], ["Gains"])

        if costs and any(c > 0 for c in costs):
            self._draw_violin(ax3, [costs], positions=[1], color=self.economic_colors["cost"])
        self._setup_violin_axes(ax3, "Total Costs", "Costs ($)", [1], ["Costs"])

        plt.tight_layout()
        return fig

    def create_parameter_sensitivity_plot(
        self,
        simulation_results: list[dict[str, Any]],
        parameters: list[str],
        title: str = "Parameter Sensitivity Analysis",
    ) -> plt.Figure:
        n_params = len(parameters)
        fig, axes = plt.subplots(1, n_params, figsize=(5 * n_params, 6))
        if n_params == 1:
            axes = [axes]
        fig.suptitle(title, fontsize=14)

        for i, param in enumerate(parameters):
            param_values = sorted(
                {r.get("parameters", {}).get(param, 0) for r in simulation_results}
            )
            damage_by_param = self._group_results_by_parameter(
                simulation_results, param, param_values
            )

            if damage_by_param:
                self._draw_violin(
                    axes[i],
                    damage_by_param,
                    positions=list(range(len(param_values))),
                    color=self.economic_colors["damage"],
                )
                self._setup_violin_axes(
                    axes[i],
                    "",
                    "Damage ($)" if i == 0 else "",
                    list(range(len(param_values))),
                    [f"{val:.1f}" for val in param_values],
                )
                axes[i].set_xlabel(f"{param.replace('_', ' ').title()}")

        plt.tight_layout()
        return fig


def create_sample_data() -> list[dict[str, Any]]:
    np.random.seed(42)
    results = []
    for detection_time in [1, 3, 6, 12, 24]:
        for _run in range(20):
            base_damage = 10000 + detection_time * 2000
            noise = np.random.normal(0, base_damage * 0.3)
            damage = max(0, base_damage + noise)
            results.append(
                {
                    "total_damage": damage,
                    "total_attacker_gains": damage * 0.3,
                    "total_costs": damage * 0.1,
                    "parameters": {"detection_time": detection_time},
                }
            )
    return results


if __name__ == "__main__":
    plotter = ViolinPlotEngine()
    sample_data = create_sample_data()
    fig1 = plotter.create_damage_distribution_plot(
        sample_data,
        "detection_time",
        [1, 3, 6, 12, 24],
        "TIM Simulation: Impact of Detection Time on Damage",
    )
    plotter.save_plot(fig1, "damage_by_detection_time.png")
    fig2 = plotter.create_economic_comparison_plot(sample_data)
    plotter.save_plot(fig2, "economic_comparison.png")
    fig3 = plotter.create_parameter_sensitivity_plot(sample_data, ["detection_time"])
    plotter.save_plot(fig3, "parameter_sensitivity.png")
    print("Sample plots created successfully!")
