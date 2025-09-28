"""
Enhanced Plot Results Module for TIM Simulation
Integrates with TIM visualization system for comprehensive analysis
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional
import os
import sys

# Import the TIM visualization engine
try:
    from .tim_visualization import TIMVisualizationEngine
except ImportError:
    # If running as standalone, add the current directory
    sys.path.append(os.path.dirname(__file__))
    from tim_visualization import TIMVisualizationEngine

def plot_violin(data, labels=None, title="Distribution Analysis", save_path=None, return_figure=False):
    """
    Create violin plots for data distribution
    Enhanced version with TIM paper styling
    
    Args:
        data: List of data arrays or single array
        labels: List of labels for each dataset
        title: Plot title
        save_path: Optional path to save the plot
        return_figure: Whether to return the figure object
    
    Returns:
        matplotlib Figure object if return_figure=True
    """
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Handle single array vs list of arrays
    if isinstance(data, (list, tuple)) and len(data) > 0 and isinstance(data[0], (list, np.ndarray)):
        plot_data = data
        if labels is None:
            labels = [f'Dataset {i+1}' for i in range(len(data))]
    else:
        plot_data = [data]
        if labels is None:
            labels = ['Data']
    
    # Create violin plot with TIM styling
    parts = ax.violinplot(plot_data, showmeans=True, showextrema=True, showmedians=True)
    
    # Customize appearance to match TIM paper
    colors = ['#d62728', '#2ca02c', '#ff7f0e', '#1f77b4', '#9467bd']
    for i, pc in enumerate(parts['bodies']):
        color = colors[i % len(colors)]
        pc.set_facecolor(color)
        pc.set_alpha(0.7)
        pc.set_edgecolor('black')
    
    # Style the statistical lines
    parts['cmeans'].set_color('black')
    parts['cmeans'].set_linewidth(2)
    parts['cmedians'].set_color('red')
    parts['cmedians'].set_linewidth(1.5)
    
    # Set labels and formatting
    ax.set_xticks(range(1, len(labels) + 1))
    ax.set_xticklabels(labels, rotation=45, ha='right')
    ax.set_ylabel('Values')
    ax.set_title(title, fontsize=14, pad=20)
    
    # Add grid for better readability
    ax.grid(True, alpha=0.3)
    
    # Tight layout
    plt.tight_layout()
    
    # Save if requested
    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Plot saved to: {save_path}")
    
    if return_figure:
        return fig
    else:
        plt.show()
        plt.close(fig)

def plot_simulation_results(simulation_results: List[Dict[str, Any]], 
                          output_dir: str = "simulation_plots"):
    """
    Plot comprehensive simulation results using TIM visualization engine
    
    Args:
        simulation_results: List of simulation result dictionaries
        output_dir: Directory to save plots
    
    Returns:
        Dictionary of generated figures
    """
    print("📊 Generating TIM simulation result plots...")
    
    # Create TIM visualization engine
    viz_engine = TIMVisualizationEngine(output_dir)
    
    # Extract parameter variations from results
    parameter_variations = extract_parameter_variations(simulation_results)
    
    # Generate comprehensive analysis
    figures = viz_engine.create_comprehensive_tim_analysis(
        simulation_results, parameter_variations
    )
    
    # Save all figures
    for name, figure in figures.items():
        viz_engine.save_figure(figure, name)
    
    print(f"✅ Generated {len(figures)} visualization plots")
    print(f"📁 Saved to directory: {output_dir}")
    
    return figures

def extract_parameter_variations(simulation_results: List[Dict[str, Any]]) -> Dict[str, List[float]]:
    """
    Extract parameter variations from simulation results
    
    Args:
        simulation_results: List of simulation results
    
    Returns:
        Dictionary mapping parameter names to their unique values
    """
    parameter_variations = {}
    
    for result in simulation_results:
        params = result.get('parameters', {})
        for param_name, param_value in params.items():
            if param_name not in parameter_variations:
                parameter_variations[param_name] = []
            if param_value not in parameter_variations[param_name]:
                parameter_variations[param_name].append(param_value)
    
    # Sort each parameter's values
    for param_name in parameter_variations:
        parameter_variations[param_name].sort()
    
    return parameter_variations

def plot_damage_over_time(timeline_data: List[Dict[str, Any]], 
                         title: str = "System Damage Over Time"):
    """
    Plot damage accumulation over time from timeline data
    
    Args:
        timeline_data: List of timeline events with time and damage data
        title: Plot title
    
    Returns:
        matplotlib Figure object
    """
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Extract time and cumulative damage
    times = [event.get('time', 0) for event in timeline_data]
    damages = [event.get('cumulative_damage', 0) for event in timeline_data]
    
    # Plot damage over time
    ax.plot(times, damages, linewidth=2, marker='o', color='#d62728', 
            markersize=4, label='Cumulative Damage')
    
    # Format plot
    ax.set_xlabel('Time (hours)')
    ax.set_ylabel('Cumulative Damage ($)')
    ax.set_title(title)
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    # Format y-axis as currency
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
    
    plt.tight_layout()
    return fig

def plot_economic_comparison(simulation_results: List[Dict[str, Any]]):
    """
    Plot comparison of economic metrics between attackers and defenders
    
    Args:
        simulation_results: List of simulation results
    
    Returns:
        matplotlib Figure object
    """
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 6))
    fig.suptitle('TIM Economic Analysis Comparison', fontsize=16)
    
    # Extract economic data
    damages = []
    attacker_gains = []
    defender_costs = []
    
    for result in simulation_results:
        damages.append(result.get('total_damage', 0))
        
        econ_summary = result.get('economic_summary', {})
        attacker_gains.append(econ_summary.get('total_attacker_gains', 0))
        defender_costs.append(econ_summary.get('total_defender_costs', 0))
    
    # 1. System damage distribution
    ax1.hist(damages, bins=20, alpha=0.7, color='#d62728', edgecolor='black')
    ax1.set_title('System Damage Distribution')
    ax1.set_xlabel('Total Damage ($)')
    ax1.set_ylabel('Frequency')
    ax1.axvline(np.mean(damages), color='red', linestyle='--', 
               label=f'Mean: ${np.mean(damages):,.0f}')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. Attacker gains vs system damage
    ax2.scatter(damages, attacker_gains, alpha=0.6, color='#ff7f0e')
    ax2.set_xlabel('System Damage ($)')
    ax2.set_ylabel('Attacker Gains ($)')
    ax2.set_title('Attacker Gains vs System Damage')
    ax2.grid(True, alpha=0.3)
    
    # Add correlation line
    if len(damages) > 1:
        z = np.polyfit(damages, attacker_gains, 1)
        p = np.poly1d(z)
        ax2.plot(damages, p(damages), "r--", alpha=0.8, label=f'Correlation')
        ax2.legend()
    
    # 3. Cost comparison
    if defender_costs and any(defender_costs):
        cost_comparison = [attacker_gains, defender_costs]
        cost_labels = ['Attacker Gains', 'Defender Costs']
        
        box_plot = ax3.boxplot(cost_comparison, labels=cost_labels, patch_artist=True)
        box_plot['boxes'][0].set_facecolor('#ff7f0e')  # Orange for attackers
        box_plot['boxes'][1].set_facecolor('#1f77b4')  # Blue for defenders
        
        ax3.set_title('Economic Impact Comparison')
        ax3.set_ylabel('Cost/Gain ($)')
        ax3.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig
