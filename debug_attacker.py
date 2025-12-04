"""Debug script to test attacker decision making"""
import sys
sys.path.insert(0, '.')

from src.actors.attacker import Attacker
from src.networks.network_loader import load_network_config, create_network_from_config
from src.actions.action_manager import get_attack_actions
from src.actions.link_actions import get_link_action_library
from src.core.access_levels import NodeAccessLevel

# Load network
config = load_network_config('src/networks/library/demo_network.json')
network = create_network_from_config(config)
network['nodes_list'] = list(network.values())

# Create attacker
attacker = Attacker(id='test_attacker', strategy='greedy', capacity=3, budget=1000)

# Give attacker actions
attack_actions = get_attack_actions()
link_actions = get_link_action_library()
attacker.available_actions = attack_actions + list(link_actions.values())

print(f"Attacker has {len(attacker.available_actions)} actions")

# Initialize visible nodes (simulate what simulation_main does)
for node in network['nodes_list']:
    if not hasattr(node, 'access'):
        node.access = {}
    if hasattr(node, 'properties') and node.properties.get('exposed_to_internet', False):
        node.access[attacker.id] = NodeAccessLevel.VISIBLE.to_string()
        attacker.visible_nodes.add(node)
        print(f"Added {node.id} to visible_nodes")
    else:
        node.access[attacker.id] = NodeAccessLevel.NONE.to_string()

print(f"\nAttacker visible_nodes: {len(attacker.visible_nodes)}")
for node in attacker.visible_nodes:
    print(f"  - {node.id}")

# Try to choose an action
network_state = {'nodes': network['nodes_list']}
decision = attacker.choose_action(network_state)

if decision:
    action, target = decision
    print(f"\nDecision: {action.name} on {target.id if hasattr(target, 'id') else target}")
else:
    print("\nNo decision made!")
    
# Check why no decision - test preconditions manually
print("\nChecking preconditions for visible nodes:")
for node in attacker.visible_nodes:
    print(f"\nNode: {node.id}")
    from src.core.access_utils import get_node_access
    from src.actions.action_manager import would_action_improve_access
    access = get_node_access(node, attacker.id)
    print(f"  Access level: {access}")
    
    for action in attacker.available_actions[:5]:  # Check first 5 actions
        if action.is_node_action():
            try:
                can_apply = action.precondition(node, access, attacker.id)
                would_improve = would_action_improve_access(action, node, access, attacker.id)
                has_json = hasattr(action, '_json_data')
                gain = action.get_one_off_gain(node, access, attacker.id)
                print(f"  {action.name}: precond={can_apply}, improve={would_improve}, json={has_json}, gain={gain}")
            except Exception as e:
                print(f"  {action.name}: ERROR - {e}")
