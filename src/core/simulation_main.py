"""
Simulation Main Module

Contains the main simulation logic that can be used by both CLI and GUI.
Implements TIM paper-compliant initialization with proper access levels.

This module replaces the old simulation_runner.py with better integration
of TIM paper compliance improvements (v0.5.0).
"""

from src.core.simulator import Simulator
from src.actions.action_manager import get_attack_actions, get_defense_actions
from src.actions.link_actions import get_link_action_library
from src.networks.network_loader import load_network_config, create_network_from_config
from src.actors.attacker import Attacker
from src.actors.defender import Defender
from src.core.access_levels import NodeAccessLevel, LinkAccessLevel


def simtim_main(
    path_to_network_config: str,
    attackers: list = None,
    defenders: list = None,
    sim_time: int = 10,
    sim_runs: int = 1,
    detection_engine_type="advanced_tim",
):
    """
    Run a complete simulation with the given parameters.
    
    Args:
        path_to_network_config (str): Path to the network configuration file
        sim_runs (int): Number of simulation runs
        sim_time (float): Simulation end time
        attackers (list): List of attacker configurations
        defenders (list): List of defender configurations
        detection_engine_type (str): Type of detection engine to use
        
    Returns:
        list: All simulation histories from all runs
    """
    if not path_to_network_config:
        print("Error: No network configuration file provided.")
        return
    if not attackers or not isinstance(attackers, list) or len(attackers) == 0:
        print("Error: No attackers specified.")
        return
    if not defenders or not isinstance(defenders, list) or len(defenders) == 0:
        print("Error: No defenders specified.")
        return
    if sim_time is None:
        print("Error: Simulation end time not provided.")
        return
    if not sim_runs or not isinstance(sim_runs, int) or sim_runs < 1:
        sim_runs = 1
        
    all_histories = []
    
    for run in range(sim_runs):
        print(f"\n=== Running simulation {run + 1}/{sim_runs} ===")
        
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
        
        # Add link actions (TIM paper Section 4.3)
        link_actions = get_link_action_library()
        all_attack_actions = attack_actions + list(link_actions.values())
        
        # Create simulator with detection engine
        simulator = Simulator(network, detection_engine_type=detection_engine_type)
        
        # Create attacker objects
        attacker_objs = []
        for i, attacker_config in enumerate(attackers):
            attacker = Attacker(
                id=attacker_config.get('id', f'attacker_{i}'),
                strategy=attacker_config.get('strategy', 'random'),
                capacity=attacker_config.get('capacity', 3)
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
                capacity=defender_config.get('capacity', 1)
            )
            defender.available_actions = defense_actions
            defender_objs.append(defender)
        
        # Add actors to network
        network['actors'] = attacker_objs + defender_objs
        
        # Initialize access levels per TIM paper Section 4.2
        # Attackers start with NONE access (progressive discovery per R5)
        # Defenders start with ADMIN access to all nodes
        # Initialize access levels per TIM paper Section 4.2
        # Attackers start with NONE access (progressive discovery per R5)
        # Defenders start with ADMIN access to all nodes
        for attacker in attacker_objs:
            for node in network['nodes_list']:
                if not hasattr(node, 'access'):
                    node.access = {}
                # Use enum but store as string for backward compatibility
                node.access[attacker.id] = NodeAccessLevel.NONE.to_string()
            
            # Initialize link access ωx(l) per TIM paper Section 4.2
            for link in network.get('links_list', []):
                if not hasattr(link, 'access'):
                    link.access = {}
                link.access[attacker.id] = LinkAccessLevel.NONE.to_string()
                
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
        print(f"Simulation run {run + 1} completed with {len(history_tuples)} events")
        if run + 1 < sim_runs:
            print("Preparing next simulation run...")
        else:
            print("\nFinal network state:")
            for n in network.values():
                print(n)
    
    print(f"\n=== All {sim_runs} simulation runs completed ===")
    return all_histories
