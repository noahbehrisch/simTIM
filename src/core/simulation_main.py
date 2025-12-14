"""
Simulation Main

Contains the main simulation logic that can be used by both CLI and GUI.
Implements TIM paper-compliant initialization with proper access levels.
"""

import logging
from typing import List, Optional, Dict, Any
from src.core.simulator import Simulator
from src.actions.action_manager import get_attack_actions, get_defense_actions
from src.actions.link_actions import get_link_action_library
from src.networks.network_loader import load_network_config, create_network_from_config
from src.actors.attacker import Attacker
from src.actors.defender import Defender
from src.core.access_levels import NodeAccessLevel, LinkAccessLevel

logger = logging.getLogger(__name__)


def simtim_main(
    path_to_network_config: str,
    attackers: Optional[List[Dict[str, Any]]] = None,
    defenders: Optional[List[Dict[str, Any]]] = None,
    sim_time: int = 10,
    sim_runs: int = 1,
    detection_engine_type: str = "exponential",
    action_duration_override: Optional[float] = None,  # Legacy: override all durations
    attack_duration_override: Optional[float] = None,  # Override only attack durations
    defense_duration_override: Optional[float] = None  # Override only defense durations
) -> Optional[List[List]]:
    """
    Run a complete simulation with the given parameters.
    
    Args:
        path_to_network_config: Path to the network configuration file
        sim_runs: Number of simulation runs
        sim_time: Simulation end time
        attackers: List of attacker configurations
        defenders: List of defender configurations
        detection_engine_type: Type of detection engine to use
        action_duration_override: Optional override for all action durations (in hours) - legacy
        attack_duration_override: Optional override for attack action durations only (in hours)
        defense_duration_override: Optional override for defense action durations only (in hours)
        
    Returns:
        List of all simulation histories from all runs, or None if validation fails
    """
    if not path_to_network_config:
        logger.error("No network configuration file provided")
        return None
    if not attackers or not isinstance(attackers, list) or len(attackers) == 0:
        logger.error("No attackers specified")
        return None
    if not defenders or not isinstance(defenders, list) or len(defenders) == 0:
        logger.error("No defenders specified")
        return None
    if sim_time is None:
        logger.error("Simulation end time not provided")
        return None
    if not sim_runs or not isinstance(sim_runs, int) or sim_runs < 1:
        sim_runs = 1
    
    # Log action duration override info before starting runs
    if action_duration_override is not None:
        logger.info(f"All actions will use duration: {action_duration_override} hours")
        
    all_histories = []
    
    for run in range(sim_runs):
        logger.info(f"Running simulation {run + 1}/{sim_runs}")
        
        config = load_network_config(path_to_network_config)
        network = create_network_from_config(config)
        network['nodes_list'] = list(network.values())
        if hasattr(network, 'links'):
            network['links_list'] = list(getattr(network, 'links', []))
        elif 'links' in network:
            network['links_list'] = list(network['links'])
        else:
            links = set()
            for node in network['nodes_list']:
                for link in getattr(node, 'links', []):
                    links.add(link)
            network['links_list'] = list(links)
        
        
        attack_actions = get_attack_actions()
        defense_actions = get_defense_actions()
        # Link actions are now fully integrated into attack strategies
        link_actions = get_link_action_library()
        
        # Apply action duration overrides if specified (for scenario comparison)
        # Legacy: action_duration_override applies to both
        if action_duration_override is not None:
            for action in attack_actions:
                action.duration = action_duration_override
            for action in defense_actions:
                action.duration = action_duration_override
            for action in link_actions.values():
                action.duration = action_duration_override
        
        # Specific overrides (take precedence over legacy override)
        if attack_duration_override is not None:
            for action in attack_actions:
                action.duration = attack_duration_override
            for action in link_actions.values():
                action.duration = attack_duration_override
        
        if defense_duration_override is not None:
            for action in defense_actions:
                action.duration = defense_duration_override
        
        all_attack_actions = attack_actions + list(link_actions.values())
        
        # Create simulator with detection engine
        simulator = Simulator(network, detection_engine_type=detection_engine_type)
        
        # Create attacker objects
        attacker_objs = []
        for i, attacker_config in enumerate(attackers):
            attacker = Attacker(
                id=attacker_config.get('id', f'attacker_{i}'),
                strategy=attacker_config.get('strategy', 'random'),
                capacity=attacker_config.get('capacity', 3),
                budget=float(attacker_config.get('budget', 1000))
            )
            # Provide both node actions and link actions
            attacker.available_actions = all_attack_actions
            attacker_objs.append(attacker)
        
        # Create defender objects
        defender_objs = []
        for i, defender_config in enumerate(defenders):
            defender = Defender(
                id=defender_config.get('id', f'defender_{i}'),
                strategy=defender_config.get('strategy', 'reactive'),
                capacity=defender_config.get('capacity', 1),
                budget=float(defender_config.get('budget', 1000))
            )
            defender.available_actions = defense_actions
            defender_objs.append(defender)
        
        # Add actors to network
        network['actors'] = attacker_objs + defender_objs
        
        for attacker in attacker_objs:
            for node in network['nodes_list']:
                if not hasattr(node, 'access'):
                    node.access = {}
                # Per TIM paper: attackers start with VISIBLE access to internet-exposed nodes
                if hasattr(node, 'properties') and node.properties.get('exposed_to_internet', False):
                    node.access[attacker.id] = NodeAccessLevel.VISIBLE.to_string()
                    # Add exposed nodes to visible set
                    attacker.visible_nodes.add(node)
                else:
                    node.access[attacker.id] = NodeAccessLevel.NONE.to_string()
            
            # Initialize link access ωx(l) per TIM paper Section 4.2
            for link in network.get('links_list', []):
                if not hasattr(link, 'access'):
                    link.access = {}
                link.access[attacker.id] = LinkAccessLevel.NONE.to_string()
                # Note: Links become visible when attacker discovers connected nodes
                
        for defender in defender_objs:
            for node in network['nodes_list']:
                if not hasattr(node, 'access'):
                    node.access = {}
                # Defenders have ADMIN access to all nodes
                node.access[defender.id] = NodeAccessLevel.ADMIN.to_string()
            
            # Initialize link access - defenders see all links (VISIBLE per TIM paper)
            for link in network.get('links_list', []):
                if not hasattr(link, 'access'):
                    link.access = {}
                # Per TIM paper: Ω(link) = {none, visible}
                link.access[defender.id] = LinkAccessLevel.VISIBLE.to_string()
        
        # Update the simulator network with actors  
        simulator.network = network
        simulator.run(until=sim_time)
        
        # Convert history to consistent tuple format
        history_tuples = []
        for event in simulator.history:
            if hasattr(event, 'time'):  # Event object
                history_tuples.append((event.time, event.event_type, event.data))
            else:  # Already a tuple
                history_tuples.append(event)
        
        all_histories.append(history_tuples)
        logger.info(f"Simulation run {run + 1} completed with {len(history_tuples)} events")
        if run + 1 < sim_runs:
            logger.debug("Preparing next simulation run...")
        else:
            logger.debug("Final network state:")
            for n in network.values():
                logger.debug(str(n))
    
    logger.info(f"All {sim_runs} simulation runs completed")
    return all_histories


def run_variable_scenarios(
    path_to_network_config: str,
    scenarios: list,
    variable_type: str = "action_duration",
    attackers: list = None,
    defenders: list = None,
    sim_time: int = 10,
    detection_engine_type="exponential",
):
    """
    Run multiple simulation scenarios with different parameters.
    
    This function runs complete simulation batches for each scenario,
    where each scenario specifies a different parameter value and number of runs.
    Used for scenario comparison and sensitivity analysis.
    
    Args:
        path_to_network_config (str): Path to the network configuration file
        scenarios (list): List of dicts with parameter value and 'runs' keys
                         For action_duration: [{'duration': 1.0, 'runs': 5}, ...]
                         For strategies: [{'strategy': 'greedy', 'runs': 5}, ...]
        variable_type (str): Type of variable being compared ('action_duration', 
                            'attacker_strategy', 'defender_strategy')
        attackers (list): List of attacker configurations
        defenders (list): List of defender configurations
        sim_time (float): Simulation end time
        detection_engine_type (str): Type of detection engine to use
        
    Returns:
        dict: Results grouped by scenario with metadata
              {
                  'scenarios': [
                      {
                          'duration': 1.0,
                          'runs': 5,
                          'histories': [...]  # List of simulation histories
                      },
                      ...
                  ]
    """
    
    # Determine what we're comparing
    if variable_type == "attack_duration":
        comparison_label = "attack action durations"
    elif variable_type == "defense_duration":
        comparison_label = "defense action durations"
    elif variable_type == "attacker_strategy":
        comparison_label = "attacker strategies"
    elif variable_type == "defender_strategy":
        comparison_label = "defender strategies"
    else:
        comparison_label = "parameters"
    
    logger.info(f"{'='*60}")
    logger.info("SCENARIO COMPARISON MODE")
    logger.info(f"Running {len(scenarios)} scenarios with different {comparison_label}")
    logger.info(f"{'='*60}")
    
    results = {'scenarios': [], 'variable_type': variable_type}
    
    for scenario_idx, scenario in enumerate(scenarios, 1):
        runs = scenario['runs']
        
        # Extract the variable value and prepare override parameters
        action_duration_override = None
        attack_duration_override = None
        defense_duration_override = None
        scenario_attackers = attackers
        scenario_defenders = defenders
        
        if variable_type == "attack_duration":
            value = scenario['duration']
            value_label = f"Attack Duration: {value} hours"
            attack_duration_override = value
            
        elif variable_type == "defense_duration":
            value = scenario['duration']
            value_label = f"Defense Duration: {value} hours"
            defense_duration_override = value
            
        elif variable_type == "attacker_strategy":
            value = scenario['strategy']
            value_label = f"Attacker Strategy: {value}"
            # Override attacker strategies for this scenario
            scenario_attackers = [
                {**attacker, 'strategy': value} 
                for attacker in (attackers or [])
            ]
            
        elif variable_type == "defender_strategy":
            value = scenario['strategy']
            value_label = f"Defender Strategy: {value}"
            # Override defender strategies for this scenario
            scenario_defenders = [
                {**defender, 'strategy': value} 
                for defender in (defenders or [])
            ]
        else:
            value = scenario.get('value', 'unknown')
            value_label = f"Parameter: {value}"
        
        logger.info(f"{'─'*60}")
        logger.info(f"SCENARIO {scenario_idx}/{len(scenarios)}")
        logger.info(value_label)
        logger.info(f"Number of Runs: {runs}")
        logger.info(f"{'─'*60}")
        
        # Run simulations for this scenario
        scenario_histories = simtim_main(
            path_to_network_config=path_to_network_config,
            attackers=scenario_attackers,
            defenders=scenario_defenders,
            sim_time=sim_time,
            sim_runs=runs,
            detection_engine_type=detection_engine_type,
            action_duration_override=action_duration_override,
            attack_duration_override=attack_duration_override,
            defense_duration_override=defense_duration_override
        )
        
        # Store results with metadata (preserve original scenario structure)
        scenario_result = {
            'runs': runs,
            'histories': scenario_histories
        }
        
        # Add the variable-specific key
        if variable_type in ["attack_duration", "defense_duration"]:
            scenario_result['duration'] = value
        else:  # Both strategy types
            scenario_result['strategy'] = value
            
        results['scenarios'].append(scenario_result)
        
        logger.info(f"Scenario {scenario_idx} completed: {len(scenario_histories)} simulation runs")
    
    logger.info(f"{'='*60}")
    logger.info("ALL SCENARIOS COMPLETED")
    logger.info(f"Total scenarios: {len(scenarios)}")
    logger.info(f"Total simulation runs: {sum(len(s['histories']) for s in results['scenarios'])}")
    logger.info(f"{'='*60}")
    
    return results
