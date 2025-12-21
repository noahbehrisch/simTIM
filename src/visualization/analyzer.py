from .plots import ViolinPlotEngine
from typing import List, Dict, Any
from src.core.economic_model import calculate_action_damage, calculate_action_gain

def analyze_simulation_results(simulation_histories: List[List], parameters: Dict[str, Any]=None) -> List[Dict[str, Any]]:
    results = []
    for i, history in enumerate(simulation_histories):
        damage = 0
        gains = 0
        costs = 0
        num_successful_attacks = 0
        num_successful_defenses = 0
        num_detections = 0
        for event in history:
            if hasattr(event, 'time') and hasattr(event, 'event_type') and hasattr(event, 'data'):
                time = event.time
                event_type = event.event_type
                data = event.data
            elif isinstance(event, (list, tuple)) and len(event) >= 3:
                time, event_type, data = event[:3]
            else:
                continue
            if event_type == 'action_succeeded' and isinstance(data, dict):
                action = data.get('action')
                actor = data.get('actor')
                target = data.get('target')
                if action and target:
                    if hasattr(action, 'cost'):
                        costs += action.cost
                    if actor and hasattr(actor, 'is_attacker') and actor.is_attacker:
                        num_successful_attacks += 1
                        action_damage = calculate_action_damage(action.name, target)
                        action_gain = calculate_action_gain(action.name, target)
                        damage += action_damage
                        gains += action_gain
                    elif actor and hasattr(actor, 'is_defender') and actor.is_defender:
                        num_successful_defenses += 1
                    else:
                        action_damage = calculate_action_damage(action.name, target)
                        damage += action_damage
            elif event_type == 'attack_detected':
                num_detections += 1
        result = {'run_id': i, 'total_damage': damage, 'total_attacker_gains': gains, 'total_costs': costs, 'num_successful_attacks': num_successful_attacks, 'num_successful_defenses': num_successful_defenses, 'num_detections': num_detections, 'parameters': parameters or {}}
        results.append(result)
    return results

def create_visualization_report(simulation_results: List[Dict[str, Any]], output_dir: str='simulation_plots'):
    plotter = ViolinPlotEngine(output_dir)
    if not simulation_results:
        print('No simulation results to visualize')
        return
    fig1 = plotter.create_economic_comparison_plot(simulation_results, 'TIM Simulation Results: Economic Impact Overview')
    plotter.save_plot(fig1, 'economic_overview.png')
    params = list(simulation_results[0].get('parameters', {}).keys())
    if params:
        fig2 = plotter.create_parameter_sensitivity_plot(simulation_results, params, 'Parameter Sensitivity Analysis')
        plotter.save_plot(fig2, 'parameter_sensitivity.png')
        for param in params:
            param_values = sorted(list(set((r.get('parameters', {}).get(param, 0) for r in simulation_results))))
            if len(param_values) > 1:
                fig3 = plotter.create_damage_distribution_plot(simulation_results, param, param_values, f"Impact of {param.replace('_', ' ').title()} on System Damage")
                plotter.save_plot(fig3, f'damage_by_{param}.png')
    print(f'Visualization report created in {output_dir}/')
    return plotter