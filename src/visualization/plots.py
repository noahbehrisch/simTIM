import matplotlib.pyplot as plt
import numpy as np
from typing import List, Dict, Any
import os

class ViolinPlotEngine:
    
    def __init__(self, output_dir: str = "plots"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        plt.style.use('default')
        self.colors = {
            'damage': '#d62728',
            'gain': '#2ca02c', 
            'cost': '#ff7f0e'
        }
    
    def create_damage_distribution_plot(self, 
                                      simulation_results: List[Dict[str, Any]], 
                                      parameter_name: str,
                                      parameter_values: List[float],
                                      title: str = "Damage Distribution Analysis") -> plt.Figure:
        
        damage_by_param = []
        for param_val in parameter_values:
            matching_results = [r for r in simulation_results 
                              if abs(r.get('parameters', {}).get(parameter_name, 0) - param_val) < 0.01]
            damages = [r.get('total_damage', 0) for r in matching_results]
            damage_by_param.append(damages)
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        parts = ax.violinplot(damage_by_param, positions=range(len(parameter_values)),
                             showmeans=True, showextrema=True, showmedians=True)
        
        for pc in parts['bodies']:
            pc.set_facecolor(self.colors['damage'])
            pc.set_alpha(0.7)
        
        parts['cmeans'].set_color('black')
        parts['cmeans'].set_linewidth(2)
        
        ax.set_xlabel(f"Duration of {parameter_name.replace('_', ' ').title()} (hours)")
        ax.set_ylabel("Damage [USD]")
        ax.set_title(title)
        ax.set_xticks(range(len(parameter_values)))
        ax.set_xticklabels([f"{val:.0f}" for val in parameter_values])
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig
    
    def create_economic_comparison_plot(self, 
                                      simulation_results: List[Dict[str, Any]],
                                      title: str = "Economic Impact Comparison") -> plt.Figure:
        
        damages = [r.get('total_damage', 0) for r in simulation_results]
        gains = [r.get('total_attacker_gains', 0) for r in simulation_results]
        costs = [r.get('total_costs', 0) for r in simulation_results]
        
        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 5))
        fig.suptitle(title, fontsize=14)
        
        # Damage plot
        if damages and any(d > 0 for d in damages):
            parts1 = ax1.violinplot([damages], showmeans=True, showmedians=True)
            for pc in parts1['bodies']:
                pc.set_facecolor(self.colors['damage'])
                pc.set_alpha(0.7)
        ax1.set_title('System Damage')
        ax1.set_ylabel('Damage ($)')
        ax1.set_xticks([1])
        ax1.set_xticklabels(['Damage'])
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        ax1.grid(True, alpha=0.3)
        
        # Gains plot
        if gains and any(g > 0 for g in gains):
            parts2 = ax2.violinplot([gains], showmeans=True, showmedians=True)
            for pc in parts2['bodies']:
                pc.set_facecolor(self.colors['gain'])
                pc.set_alpha(0.7)
        ax2.set_title('Attacker Gains')
        ax2.set_ylabel('Gains ($)')
        ax2.set_xticks([1])
        ax2.set_xticklabels(['Gains'])
        ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        ax2.grid(True, alpha=0.3)
        
        # Costs plot
        if costs and any(c > 0 for c in costs):
            parts3 = ax3.violinplot([costs], showmeans=True, showmedians=True)
            for pc in parts3['bodies']:
                pc.set_facecolor(self.colors['cost'])
                pc.set_alpha(0.7)
        ax3.set_title('Total Costs')
        ax3.set_ylabel('Costs ($)')
        ax3.set_xticks([1])
        ax3.set_xticklabels(['Costs'])
        ax3.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        ax3.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig
    
    def create_parameter_sensitivity_plot(self,
                                        simulation_results: List[Dict[str, Any]],
                                        parameters: List[str],
                                        title: str = "Parameter Sensitivity Analysis") -> plt.Figure:
        
        n_params = len(parameters)
        fig, axes = plt.subplots(1, n_params, figsize=(5 * n_params, 6))
        if n_params == 1:
            axes = [axes]
        
        fig.suptitle(title, fontsize=14)
        
        for i, param in enumerate(parameters):
            param_values = sorted(list(set(r.get('parameters', {}).get(param, 0) 
                                           for r in simulation_results)))
            
            damage_by_param = []
            for param_val in param_values:
                matching_results = [r for r in simulation_results 
                                  if abs(r.get('parameters', {}).get(param, 0) - param_val) < 0.01]
                damages = [r.get('total_damage', 0) for r in matching_results]
                damage_by_param.append(damages)
            
            if damage_by_param:
                parts = axes[i].violinplot(damage_by_param, positions=range(len(param_values)),
                                         showmeans=True, showmedians=True)
                
                for pc in parts['bodies']:
                    pc.set_facecolor(self.colors['damage'])
                    pc.set_alpha(0.7)
                
                axes[i].set_xlabel(f"{param.replace('_', ' ').title()}")
                axes[i].set_ylabel("Damage ($)" if i == 0 else "")
                axes[i].set_xticks(range(len(param_values)))
                axes[i].set_xticklabels([f"{val:.1f}" for val in param_values])
                axes[i].yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
                axes[i].grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig
    
    def save_plot(self, fig: plt.Figure, filename: str, dpi: int = 300):
        filepath = os.path.join(self.output_dir, filename)
        fig.savefig(filepath, dpi=dpi, bbox_inches='tight')
        print(f"Plot saved to {filepath}")
    
    def show_plot(self, fig: plt.Figure):
        plt.show()

def create_sample_data():
    np.random.seed(42)
    results = []
    
    for detection_time in [1, 3, 6, 12, 24]:
        for run in range(20):
            base_damage = 10000 + detection_time * 2000
            noise = np.random.normal(0, base_damage * 0.3)
            damage = max(0, base_damage + noise)
            
            results.append({
                'total_damage': damage,
                'total_attacker_gains': damage * 0.3,
                'total_costs': damage * 0.1,
                'parameters': {'detection_time': detection_time}
            })
    
    return results

if __name__ == "__main__":
    plotter = ViolinPlotEngine()
    sample_data = create_sample_data()
    
    fig1 = plotter.create_damage_distribution_plot(
        sample_data, 
        'detection_time', 
        [1, 3, 6, 12, 24],
        "TIM Simulation: Impact of Detection Time on Damage"
    )
    plotter.save_plot(fig1, "damage_by_detection_time.png")
    
    fig2 = plotter.create_economic_comparison_plot(sample_data)
    plotter.save_plot(fig2, "economic_comparison.png")
    
    fig3 = plotter.create_parameter_sensitivity_plot(sample_data, ['detection_time'])
    plotter.save_plot(fig3, "parameter_sensitivity.png")
    
    print("Sample plots created successfully!")
