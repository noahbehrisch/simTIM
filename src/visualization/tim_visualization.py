import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional
import os
from datetime import datetime

plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

class TIMVisualizationEngine:
    def __init__(self, output_dir: str = "visualization_output"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.colors = {
            'damage': '#d62728',
            'gain': '#2ca02c',
            'cost': '#ff7f0e',
            'defender': '#1f77b4',
            'attacker': '#d62728',
            'neutral': '#7f7f7f'
        }
    def create_damage_distribution_analysis(self, 
                                          simulation_results: List[Dict[str, Any]], 
                                          parameter_variations: Dict[str, List[float]],
                                          title: str = "TIM Simulation Results: Damage Distribution Analysis") -> plt.Figure:
        param_names = list(parameter_variations.keys())
        n_params = len(param_names)
        fig, axes = plt.subplots(1, n_params, figsize=(5 * n_params, 6))
        if n_params == 1:
            axes = [axes]
        fig.suptitle(title, fontsize=14, y=0.98)
        for i, param_name in enumerate(param_names):
            param_values = parameter_variations[param_name]
            damage_by_param = []
            for param_val in param_values:
                matching_results = [r for r in simulation_results 
                                  if abs(r.get('parameters', {}).get(param_name, 0) - param_val) < 0.01]
                damages = [r.get('total_damage', 0) for r in matching_results]
                damage_by_param.append(damages)
            parts = axes[i].violinplot(damage_by_param, positions=range(len(param_values)),
                                     showmeans=True, showextrema=True, showmedians=True)
            for pc in parts['bodies']:
                pc.set_facecolor(self.colors['damage'])
                pc.set_alpha(0.7)
            parts['cmeans'].set_color('black')
            parts['cmeans'].set_linewidth(2)
            axes[i].set_xlabel(f"Duration of {param_name.replace('_', ' ').title()} (hours)")
            axes[i].set_ylabel("Damage [USD]" if i == 0 else "")
            axes[i].set_xticks(range(len(param_values)))
            axes[i].set_xticklabels([f"{val:.0f}" for val in param_values])
            axes[i].yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
            axes[i].grid(True, alpha=0.3)
        plt.tight_layout()
        return fig
    def create_temporal_impact_analysis(self, 
                                      simulation_results: List[Dict[str, Any]],
                                      time_intervals: List[Tuple[float, float]] = None) -> plt.Figure:
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('TIM Temporal Impact Analysis', fontsize=16)
        times = []
        damages = []
        gains = []
        costs = []
        for result in simulation_results:
            if 'timeline' in result:
                timeline = result['timeline']
                for event in timeline:
                    times.append(event.get('time', 0))
                    damages.append(event.get('cumulative_damage', 0))
                    gains.append(event.get('cumulative_gain', 0))
                    costs.append(event.get('cumulative_cost', 0))
        if times:
            ax1.plot(times, damages, color=self.colors['damage'], linewidth=2, label='Damage')
            ax1.set_title('Cumulative System Damage Over Time')
            ax1.set_xlabel('Time (hours)')
            ax1.set_ylabel('Cumulative Damage ($)')
            ax1.grid(True, alpha=0.3)
            ax1.legend()
            ax2.plot(times, gains, color=self.colors['gain'], linewidth=2, label='Attacker Gains')
            ax2.set_title('Cumulative Attacker Gains Over Time')
            ax2.set_xlabel('Time (hours)')
            ax2.set_ylabel('Cumulative Gains ($)')
            ax2.grid(True, alpha=0.3)
            ax2.legend()
            ax3.plot(times, costs, color=self.colors['cost'], linewidth=2, label='Total Costs')
            ax3.set_title('Cumulative Action Costs Over Time')
            ax3.set_xlabel('Time (hours)')
            ax3.set_ylabel('Cumulative Costs ($)')
            ax3.grid(True, alpha=0.3)
            ax3.legend()
            net_impact = np.array(gains) - np.array(costs)
            ax4.plot(times, net_impact, color=self.colors['attacker'], linewidth=2, label='Net Attacker Benefit')
            ax4.axhline(y=0, color='black', linestyle='--', alpha=0.5)
            ax4.set_title('Net Economic Impact Over Time')
            ax4.set_xlabel('Time (hours)')
            ax4.set_ylabel('Net Benefit ($)')
            ax4.grid(True, alpha=0.3)
            ax4.legend()
        plt.tight_layout()
        return fig
    def create_economic_objective_comparison(self, 
                                           simulation_results: List[Dict[str, Any]]) -> plt.Figure:
        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 6))
        fig.suptitle('TIM Economic Objectives Analysis', fontsize=16)
        attacker_objectives = []
        defender_objectives = []
        success_rates = []
        for result in simulation_results:
            econ_summary = result.get('economic_summary', {})
            att_objs = econ_summary.get('attacker_objectives', {})
            if att_objs:
                attacker_objectives.extend(att_objs.values())
            def_objs = econ_summary.get('defender_objectives', {})
            if def_objs:
                defender_objectives.extend(def_objs.values())
            success_rates.append(result.get('attack_success_rate', 0))
        if attacker_objectives:
            ax1.hist(attacker_objectives, bins=20, alpha=0.7, color=self.colors['attacker'], 
                    edgecolor='black')
            ax1.set_title('Attacker Objectives\n(Maximize G[0,T] - C_x,[0,T])')
            ax1.set_xlabel('Objective Value ($)')
            ax1.set_ylabel('Frequency')
            ax1.axvline(np.mean(attacker_objectives), color='red', linestyle='--', 
                       label=f'Mean: ${np.mean(attacker_objectives):,.0f}')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
        if defender_objectives:
            ax2.hist(defender_objectives, bins=20, alpha=0.7, color=self.colors['defender'],
                    edgecolor='black')
            ax2.set_title('Defender Objectives\n(Minimize D^total_[0,T] + C_defender,[0,T])')
            ax2.set_xlabel('Objective Value ($)')
            ax2.set_ylabel('Frequency')
            ax2.axvline(np.mean(defender_objectives), color='blue', linestyle='--',
                       label=f'Mean: ${np.mean(defender_objectives):,.0f}')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
        if success_rates:
            ax3.hist(success_rates, bins=20, alpha=0.7, color=self.colors['neutral'],
                    edgecolor='black')
            ax3.set_title('Attack Success Rate Distribution')
            ax3.set_xlabel('Success Rate')
            ax3.set_ylabel('Frequency')
            ax3.axvline(np.mean(success_rates), color='orange', linestyle='--',
                       label=f'Mean: {np.mean(success_rates):.2f}')
            ax3.legend()
            ax3.grid(True, alpha=0.3)
        plt.tight_layout()
        return fig
    def create_action_duration_sensitivity_analysis(self, 
                                                   simulation_results: List[Dict[str, Any]]) -> plt.Figure:
        fig, ax = plt.subplots(figsize=(12, 8))
        duration_groups = {}
        for result in simulation_results:
            params = result.get('parameters', {})
            mysql_duration = params.get('mysql_upgrade_duration', 8)
            tapestry_duration = params.get('tapestry_attack_duration', 4)
            mysql_attack_duration = params.get('mysql_attack_duration', 4)
            key = (mysql_duration, tapestry_duration, mysql_attack_duration)
            if key not in duration_groups:
                duration_groups[key] = []
            duration_groups[key].append(result.get('total_damage', 0))
        if duration_groups:
            keys = sorted(duration_groups.keys())
            damages_list = [duration_groups[key] for key in keys]
            parts = ax.violinplot(damages_list, positions=range(len(keys)),
                                showmeans=True, showextrema=True, showmedians=True)
            for pc in parts['bodies']:
                pc.set_facecolor(self.colors['damage'])
                pc.set_alpha(0.6)
            parts['cmeans'].set_color('black')
            parts['cmeans'].set_linewidth(2)
            ax.set_xlabel('Action Duration Configuration\n(MySQL Upgrade, Tapestry Attack, MySQL Attack) [hours]')
            ax.set_ylabel('Damage [USD]')
            ax.set_title('Sensitivity Analysis: Impact of Action Durations on Damage\n(Replicating TIM Paper Figure 2)')
            labels = [f"({key[0]}, {key[1]}, {key[2]})" for key in keys]
            ax.set_xticks(range(len(keys)))
            ax.set_xticklabels(labels, rotation=45, ha='right')
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
            ax.grid(True, alpha=0.3)
        plt.tight_layout()
        return fig
    def create_statistical_summary_report(self, 
                                        simulation_results: List[Dict[str, Any]],
                                        save_to_file: bool = True) -> str:
        report_lines = [
            "TIM Simulation Statistical Analysis Report",
            "=" * 50,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Total simulation runs: {len(simulation_results)}",
            "",
            "ECONOMIC METRICS SUMMARY",
            "-" * 30
        ]
        all_damages = []
        all_gains = []
        all_costs = []
        all_attacker_objectives = []
        all_defender_objectives = []
        for result in simulation_results:
            all_damages.append(result.get('total_damage', 0))
            econ_summary = result.get('economic_summary', {})
            all_gains.append(econ_summary.get('total_attacker_gains', 0))
            all_costs.append(econ_summary.get('total_costs', 0))
            att_objs = econ_summary.get('attacker_objectives', {})
            if att_objs:
                all_attacker_objectives.extend(att_objs.values())
            def_objs = econ_summary.get('defender_objectives', {})
            if def_objs:
                all_defender_objectives.extend(def_objs.values())

        def stats_summary(data, name):
            if not data:
                return f"{name}: No data available"
            return f"""{name}:
  Mean: ${np.mean(data):,.2f}
  Median: ${np.median(data):,.2f}
  Std Dev: ${np.std(data):,.2f}
  Min: ${np.min(data):,.2f}
  Max: ${np.max(data):,.2f}
  95th percentile: ${np.percentile(data, 95):,.2f}"""
        report_lines.extend([
            stats_summary(all_damages, "Total System Damage"),
            "",
            stats_summary(all_gains, "Attacker Gains"),
            "",
            stats_summary(all_costs, "Action Costs"),
            "",
            stats_summary(all_attacker_objectives, "Attacker Objectives (G[0,T] - C_x,[0,T])"),
            "",
            stats_summary(all_defender_objectives, "Defender Objectives (D^total_[0,T] + C_defender,[0,T])"),
            "",
            "TEMPORAL ANALYSIS",
            "-" * 20
        ])
        total_sim_time = np.mean([r.get('simulation_duration', 0) for r in simulation_results])
        avg_actions_per_sim = np.mean([r.get('economic_summary', {}).get('num_actions', 0) 
                                      for r in simulation_results])
        report_lines.extend([
            f"Average simulation duration: {total_sim_time:.2f} time units",
            f"Average actions per simulation: {avg_actions_per_sim:.1f}",
            f"Average action frequency: {avg_actions_per_sim / total_sim_time:.2f} actions/time unit"
        ])
        report_text = "\n".join(report_lines)
        if save_to_file:
            report_path = os.path.join(self.output_dir, "statistical_summary_report.txt")
            with open(report_path, 'w') as f:
                f.write(report_text)
            print(f"Statistical report saved to: {report_path}")
        return report_text

    def save_figure(self, fig: plt.Figure, filename: str, formats: List[str] = ['png', 'pdf']):
        for fmt in formats:
            filepath = os.path.join(self.output_dir, f"{filename}.{fmt}")
            fig.savefig(filepath, format=fmt, dpi=300, bbox_inches='tight')
            print(f"Saved {fmt.upper()} to: {filepath}")
    def create_comprehensive_tim_analysis(self, 
                                        simulation_results: List[Dict[str, Any]],
                                        parameter_variations: Dict[str, List[float]] = None) -> Dict[str, plt.Figure]:
        figures = {}
        print("🎨 Creating TIM-compliant visualization suite...")
        if parameter_variations:
            fig1 = self.create_damage_distribution_analysis(
                simulation_results, parameter_variations,
                "TIM Damage Distribution Analysis (Replicating Paper Figure 2)"
            )
            figures['damage_distribution_analysis'] = fig1
        fig2 = self.create_temporal_impact_analysis(simulation_results)
        figures['temporal_impact_analysis'] = fig2
        fig3 = self.create_economic_objective_comparison(simulation_results)
        figures['economic_objectives_comparison'] = fig3
        fig4 = self.create_action_duration_sensitivity_analysis(simulation_results)
        figures['action_duration_sensitivity'] = fig4
        report = self.create_statistical_summary_report(simulation_results)
        print(f"✅ Generated {len(figures)} TIM-compliant visualizations")
        print(f"📊 Statistical analysis complete")
        return figures

def create_sample_tim_visualization():
    print("🚀 Creating sample TIM visualization...")
    np.random.seed(42)
    sample_results = []
    mysql_upgrade_durations = [1, 2, 4, 6, 8, 10, 12]
    tapestry_durations = [2, 4, 6, 8]
    mysql_attack_durations = [2, 4, 6, 8]
    for mysql_dur in mysql_upgrade_durations:
        for tapestry_dur in tapestry_durations:
            for mysql_att_dur in mysql_attack_durations:
                for run in range(20):
                    if mysql_dur <= 4:
                        damage = np.random.exponential(10000) if np.random.random() > 0.8 else 0
                    else:
                        damage = np.random.exponential(50000) if np.random.random() > 0.3 else np.random.exponential(150000)
                    attacker_gains = damage * 0.6 if damage > 0 else 0
                    attacker_costs = tapestry_dur * 150 + mysql_att_dur * 200
                    defender_costs = mysql_dur * 62.5
                    result = {
                        'parameters': {
                            'mysql_upgrade_duration': mysql_dur,
                            'tapestry_attack_duration': tapestry_dur,
                            'mysql_attack_duration': mysql_att_dur
                        },
                        'total_damage': damage,
                        'simulation_duration': max(mysql_dur, tapestry_dur + mysql_att_dur),
                        'economic_summary': {
                            'total_attacker_gains': attacker_gains,
                            'total_costs': attacker_costs + defender_costs,
                            'attacker_objectives': {'attacker_1': attacker_gains - attacker_costs},
                            'defender_objectives': {'defender_1': damage + defender_costs},
                            'num_actions': 3
                        },
                        'attack_success_rate': 1.0 if damage > 0 else 0.0,
                        'timeline': [
                            {'time': 0, 'cumulative_damage': 0, 'cumulative_gain': 0, 'cumulative_cost': 0},
                            {'time': tapestry_dur, 'cumulative_damage': 0, 'cumulative_gain': 0, 'cumulative_cost': attacker_costs/2},
                            {'time': tapestry_dur + mysql_att_dur, 'cumulative_damage': damage, 'cumulative_gain': attacker_gains, 'cumulative_cost': attacker_costs + defender_costs}
                        ]
                    }
                    sample_results.append(result)
    viz_engine = TIMVisualizationEngine("sample_tim_visualization")
    parameter_variations = {
        'mysql_upgrade_duration': mysql_upgrade_durations,
        'tapestry_attack_duration': tapestry_durations,
        'mysql_attack_duration': mysql_attack_durations
    }
    figures = viz_engine.create_comprehensive_tim_analysis(sample_results, parameter_variations)
    for name, figure in figures.items():
        viz_engine.save_figure(figure, name)
    print(f"✅ Sample TIM visualization complete!")
    print(f"📁 Output directory: {viz_engine.output_dir}")
    return viz_engine, figures, sample_results
if __name__ == "__main__":
    viz_engine, figures, results = create_sample_tim_visualization()
    print(f"\n📊 Sample Statistics:")
    print(f"   Total simulation runs: {len(results)}")
    print(f"   Average damage: ${np.mean([r['total_damage'] for r in results]):,.0f}")
    print(f"   Damage range: ${np.min([r['total_damage'] for r in results]):,.0f} - ${np.max([r['total_damage'] for r in results]):,.0f}")