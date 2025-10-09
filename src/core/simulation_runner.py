"""
Simulation Runner Module

Contains the main simulation logic that can be used by both CLI and GUI.
"""

from src.core.simulator import Simulator
from src.actions.action_manager import get_attack_actions, get_defense_actions
from src.networks.network_loader import load_network_config, create_network_from_config
from src.actors.attacker import Attacker
from src.actors.defender import Defender


def run_simulation(
    path_to_network_config=None,
    sim_runs=None,
    sim_time=None,
    attackers=None,
    defenders=None,
    detection_engine_type="legacy",
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
        
        # Create simulator and load detection rates
        simulator = Simulator(network, detection_engine_type=detection_engine_type)
        
        # Only load action detection rates for legacy detection engine
        if detection_engine_type == "legacy":
            simulator.load_action_detection_rates(attack_actions, defense_actions)
        
        # Create attacker objects
        attacker_objs = []
        for i, attacker_config in enumerate(attackers):
            attacker = Attacker(
                id=attacker_config.get('id', f'attacker_{i}'),
                strategy=attacker_config.get('strategy', 'random'),
                capacity=attacker_config.get('capacity', float('inf')),
                budget=attacker_config.get('budget', 10000)
            )
            attacker_objs.append(attacker)
        
        # Create defender objects
        defender_objs = []
        for i, defender_config in enumerate(defenders):
            defender = Defender(
                id=defender_config.get('id', f'defender_{i}'),
                strategy=defender_config.get('strategy', 'random'),
                capacity=defender_config.get('capacity', 1),
                budget=defender_config.get('budget', 10000)
            )
            defender_objs.append(defender)
                
        for attacker in attacker_objs:
            for node in network['nodes_list']:
                if not hasattr(node, 'access'):
                    node.access = {}
                node.access[attacker.id] = 'NONE'
                
        for defender in defender_objs:
            for node in network['nodes_list']:
                if not hasattr(node, 'access'):
                    node.access = {}
                node.access[defender.id] = 'ADMIN'
        
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
        print("\nFinal network state:")
        for n in network.values():
            print(n)
    return all_histories
