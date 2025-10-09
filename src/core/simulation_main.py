from src.core.simulator import Simulator
from src.actions.action_manager import get_attack_actions, get_defense_actions
from src.networks.network_loader import load_network_config, create_network_from_config
from src.actors.attacker import Attacker
from src.actors.defender import Defender


def simtim_main(
    path_to_network_config=None,
    sim_runs=None,
    sim_time=None,
    attackers=None,
    defenders=None,
    detection_engine_type=None,
):

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
        if hasattr(simulator.detection_engine, 'load_action_detection_rates'):
            simulator.detection_engine.load_action_detection_rates()
        
        attacker_objs = []
        for attacker_config in attackers:
            attacker = Attacker(
                id=attacker_config['id'], 
                strategy=attacker_config.get('strategy', 'none'),
                capacity=attacker_config.get('capacity', 3)
            )
            attacker.available_actions = attack_actions
            attacker_objs.append(attacker)
        defender_objs = []
        for defender_config in defenders:
            defender = Defender(
                id=defender_config['id'], 
                strategy=defender_config.get('strategy', 'none'),
                capacity=defender_config.get('capacity', 2)
            )
            defender.available_actions = defense_actions
            defender_objs.append(defender)
        network['actors'] = attacker_objs + defender_objs
        
        # Initialize access: attackers start with no access, defenders see everything
        for attacker in attacker_objs:
            for node in network['nodes_list']:
                if not hasattr(node, 'access'):
                    node.access = {}
                node.access[attacker.id] = 'NONE'  # Progressive discovery: start with no access
                
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
