# TIM Visualization System

A comprehensive visualization system for TIM (Temporal Infrastructure Modeling) simulation results, based on the specifications from the TIM academic paper, Section 5 (Simulation) and Figure 2.

## Overview

This visualization system implements the statistical analysis and visualization approaches demonstrated in the TIM paper, focusing on:

- **Violin plots** showing damage distribution analysis (replicating TIM Figure 2)
- **Temporal impact analysis** with cumulative metrics over time
- **Economic objective comparison** between attackers and defenders  
- **Statistical sensitivity analysis** for action duration parameters
- **Academic-quality publication-ready plots**

## Key Features

### 🎯 TIM Paper Compliance
- Replicates TIM paper Figure 2 violin plot style
- Implements Section 5 simulation analysis approach
- Uses TIM economic objective formulations:
  - Attacker: Maximize G[0,T] - C_x,[0,T] (gains minus costs)
  - Defender: Minimize D^total_[0,T] + C_defender,[0,T] (damage plus costs)

### 📊 Comprehensive Analysis
- Multi-parameter sensitivity analysis
- Statistical significance testing across multiple simulation runs
- Temporal progression visualization
- Economic impact comparison
- Damage distribution analysis by action duration

### 🎨 Professional Visualization
- Publication-quality plots (300 DPI PNG/PDF)
- TIM paper color scheme and styling
- Academic formatting and typography
- Grid layouts for multi-dimensional analysis

## Files

### Core Modules
- **`tim_visualization.py`** - Main TIM visualization engine with full analysis suite
- **`plot_results.py`** - Enhanced plotting utilities with TIM integration
- **`tim_demo.py`** - Comprehensive demonstration and testing script

### Generated Outputs
- **PNG/PDF plots** - High-resolution visualization files
- **Statistical reports** - Comprehensive numerical analysis
- **Timeline analysis** - Temporal progression plots

## Usage

### Basic Violin Plot
```python
from visualization.plot_results import plot_violin
import numpy as np

# Create sample damage data
fast_defense = np.random.exponential(10000, 100)
slow_defense = np.random.exponential(80000, 100)

data = [fast_defense, slow_defense]
labels = ['Fast Defense', 'Slow Defense']

plot_violin(data, labels, "TIM Damage Comparison", save_path="damage_analysis.png")
```

### Comprehensive TIM Analysis
```python
from visualization.tim_visualization import TIMVisualizationEngine

# Initialize visualization engine
viz_engine = TIMVisualizationEngine("output_directory")

# Your simulation results (list of dictionaries)
simulation_results = [...]

# Parameter variations for sensitivity analysis  
parameter_variations = {
    'mysql_upgrade_duration': [1, 2, 4, 6, 8, 12],
    'attack_intensity': [0.1, 0.5, 1.0]
}

# Generate complete analysis
figures = viz_engine.create_comprehensive_tim_analysis(
    simulation_results, parameter_variations
)

# Save all figures
for name, figure in figures.items():
    viz_engine.save_figure(figure, name)
```

### Simulation Result Format

The visualization system expects simulation results in this format:

```python
result = {
    'parameters': {
        'mysql_upgrade_duration': 8,        # hours
        'tapestry_attack_duration': 4,      # hours  
        'mysql_attack_duration': 4          # hours
    },
    'total_damage': 75000,                  # USD
    'simulation_duration': 12,              # time units
    'economic_summary': {
        'total_attacker_gains': 45000,      # USD
        'total_defender_costs': 500,        # USD
        'attacker_objectives': {
            'net_gain': 43500               # G[0,T] - C_x,[0,T]
        },
        'defender_objectives': {
            'total_cost': 75500             # D^total_[0,T] + C_defender,[0,T]
        }
    },
    'timeline': [
        {'time': 0, 'cumulative_damage': 0},
        {'time': 4, 'cumulative_damage': 25000},
        {'time': 8, 'cumulative_damage': 75000}
    ]
}
```

## Running the Demo

To see the complete TIM visualization system in action:

```bash
# Ensure Python environment is configured
cd /path/to/simTIM
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install matplotlib seaborn numpy pandas

# Run the comprehensive demo
python visualization/tim_demo.py
```

This generates:
- **5,000 simulation results** across parameter combinations
- **4 main visualization plots** (damage distribution, temporal analysis, economic comparison, sensitivity analysis)
- **Statistical summary report** with TIM metrics
- **Sample timeline analysis**

## TIM Paper Results Replication

The demo reproduces key findings from the TIM paper:

### Key Statistics (Sample Run)
- **Fast defense (≤4h MySQL upgrade)**: 14.6% attack success, $2,254 mean damage
- **Slow defense (>8h MySQL upgrade)**: 100% attack success, $91,804 mean damage  
- **Damage reduction ratio**: 40.7x improvement with fast defense
- **Economic impact**: Strong correlation between defense speed and total cost

### Figure 2 Replication
The `damage_distribution_analysis.png` directly replicates TIM paper Figure 2:
- Violin plots showing damage distribution vs action duration
- Multiple parameter sensitivity (MySQL upgrade, Tapestry attack, MySQL attack durations)
- Statistical significance across multiple simulation runs
- Academic styling matching the paper

## Visualization Types

### 1. Damage Distribution Analysis
- **Purpose**: Replicate TIM Figure 2 
- **Method**: Violin plots with parameter variations
- **Output**: `damage_distribution_analysis.png`
- **Key insight**: Action duration dramatically affects damage distribution

### 2. Temporal Impact Analysis  
- **Purpose**: Show cumulative effects over time
- **Method**: Time-series plots of damage, gains, costs
- **Output**: `temporal_impact_analysis.png`
- **Key insight**: Temporal progression of economic impact

### 3. Economic Objectives Comparison
- **Purpose**: Compare TIM attacker/defender objectives
- **Method**: Histogram analysis of objective values
- **Output**: `economic_objectives_comparison.png` 
- **Key insight**: Distribution of economic outcomes

### 4. Action Duration Sensitivity
- **Purpose**: Multi-parameter sensitivity analysis
- **Method**: Violin plots across parameter combinations
- **Output**: `action_duration_sensitivity.png`
- **Key insight**: Relative importance of different timing parameters

## Statistical Analysis

The system generates comprehensive statistical reports including:

- **Descriptive statistics**: Mean, median, std dev, percentiles
- **Economic metrics**: Attacker gains, defender costs, net objectives
- **Temporal analysis**: Simulation duration, action frequency
- **Success rates**: Attack success by scenario type
- **Comparative analysis**: Fast vs slow defense effectiveness

## Integration with simTIM

To integrate with your simTIM simulation:

1. **Format your results** according to the expected structure
2. **Call the visualization engine** with your results
3. **Specify parameter variations** for sensitivity analysis
4. **Generate publication-ready plots** automatically

```python
# In your simulation code
from visualization.plot_results import plot_simulation_results

# After running simulations
figures = plot_simulation_results(your_simulation_results, "output_folder")
```

## Dependencies

- `matplotlib` >= 3.0 - Core plotting
- `seaborn` >= 0.11 - Statistical visualization
- `numpy` >= 1.20 - Numerical computation  
- `pandas` >= 1.3 - Data manipulation

## Academic Compliance

This visualization system is designed for academic research and publication:
- **Reproducible results** with fixed random seeds
- **Statistical rigor** with multiple simulation runs
- **Publication quality** with 300 DPI output
- **TIM paper compliance** following established methodology
- **Academic styling** matching journal standards

## Output Quality

All plots are generated with:
- **High resolution**: 300 DPI for publication
- **Multiple formats**: PNG for web, PDF for LaTeX
- **Professional styling**: Academic color schemes and typography
- **Statistical annotations**: Means, confidence intervals, correlation lines
- **Proper formatting**: Currency notation, scientific notation where appropriate

## Next Steps

1. **Integrate with your simulator**: Adapt result format to your simulation output
2. **Customize parameters**: Modify parameter variations for your specific analysis
3. **Extend visualizations**: Add domain-specific plots as needed
4. **Publication preparation**: Use generated plots in academic papers or reports

---

*This visualization system implements the TIM (Temporal Infrastructure Modeling) approach from the academic paper, providing comprehensive analysis tools for cybersecurity simulation research.*
