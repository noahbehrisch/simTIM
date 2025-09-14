from simulator.simulator import Simulator
from actions.action_attack import all_attack_actions
from actions.action_defense import all_defense_actions
from simulator.graph import Node, Link
from networks.network_loader import load_network_config, create_network_from_config
from actors.attacker import Attacker
from actors.defender import Defender

def simtim_main(
    path_to_network_config=None,
    sim_runs=None,
    sim_time=None,
    attackers=None,
    defenders=None,
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
        # Store a list of nodes in the network dict for Simulator compatibility
        network['nodes_list'] = list(network.values())
        # Store a list of links if available
        if hasattr(network, 'links'):
            network['links_list'] = list(getattr(network, 'links', []))
        elif 'links' in network:
            network['links_list'] = list(network['links'])
        else:
            # Try to collect links from nodes
            links = set()
            for node in network['nodes_list']:
                for link in getattr(node, 'links', []):
                    links.add(link)
            network['links_list'] = list(links)
        print(f"[DEBUG] nodes_list: {network['nodes_list']}")
        print(f"[DEBUG] links_list: {network.get('links_list', [])}")

        attacker_objs = []
        for attacker_config in attackers:
            attacker = Attacker(id=attacker_config['id'])
            attacker.available_actions = all_attack_actions
            attacker_objs.append(attacker)

        defender_objs = []
        for defender_config in defenders:
            defender = Defender(id=defender_config['id'])
            defender.available_actions = all_defense_actions
            defender_objs.append(defender)

        network['actors'] = attacker_objs + defender_objs

        # Give every attacker USER access to all nodes for testing
        for attacker in attacker_objs:
            for node in network['nodes_list']:
                node.access[attacker.id] = 'USER'

        sim = Simulator(network=network)

        sim.run(until=sim_time)
        
        all_histories.append(list(sim.history))
        print(f"\nRun {run+1}/{sim_runs} history:")
        sim.print_history()
        print("\nFinal network state:")
        for n in network.values():
            print(n)
    return all_histories


def main():
    simtim_main()

if __name__ == "__main__":
    main()

# Some general TODO:s :
# BUILDING A WORKING PROTOTYPE!
# reducing external dependencies
# restructuring so make it more maintainable and expandable
# -> should all the network stuff be in a separate folder? 
# remove lost comments
# include logging
# adding lots of error handling
# creating tests
# adding actions
# adding more nodes and links 
# -> maybe a file with a collection of nodes and links
# expanding the gui
# building the network creator
# making networks savable
# building the network visualizer
# implementing the actor creation process
# implementing the action creation process
# find a solution for physical time implementation
# building the simulator
# action_handler???
# writing a README
# main.py is entry point for GUI(graphical user interface) and CLI(command line interface)
# -m add event/result/visualization export
# add example scenarios and usage tutorials -> example in CyberSim py Pira

