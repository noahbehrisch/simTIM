#!/usr/bin/env python3
"""
Simple Showcase Demo: 3-Node Attack Progression

This demo shows how the simTIM simulator works with a minimal network:
1. Internet-facing web server (entry point)
2. Internal application server (lateral movement target)  
3. Database server with sensitive data (final target)

The demo illustrates the complete attack chain:
Reconnaissance → Exploitation → Privilege Escalation → Lateral Movement → Data Exfiltration
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.simulator import Simulator
from src.networks.network_loader import load_network_config, create_network_from_config
from src.actors.attacker import Attacker
from src.actors.defender import Defender
from src.actions.action_manager import get_attack_actions, get_defense_actions


def print_network_status(network, title="Network Status"):
    """Print current network status in a readable format"""
    print(f"\n{'='*60}")
    print(f"📊 {title}")
    print(f"{'='*60}")
    
    for node in network['nodes_list']:
        # Use id if name is not available
        display_name = getattr(node, 'name', node.id)
        print(f"\n🖥️  {display_name} ({node.id})")
        print(f"   Software: {node.software.get('os', 'Unknown')} {node.software.get('version', '')}")
        print(f"   Vulnerabilities: {len(node.vulnerabilities)} ({', '.join(node.vulnerabilities[:2])}{'...' if len(node.vulnerabilities) > 2 else ''})")
        print(f"   Assets: {len(node.assets)} ({', '.join(node.assets[:2])}{'...' if len(node.assets) > 2 else ''})")
        print(f"   Compromised: {'❌ YES' if getattr(node, 'compromised', False) else '✅ No'}")
        
        # Show access levels for each actor
        print(f"   Access Levels:")
        for actor_id, access_level in node.access.items():
            icon = "🔓" if access_level in ["USER", "ADMIN"] else "🔒"
            print(f"     {icon} {actor_id}: {access_level}")


def print_attack_chain_progress(attacker, network):
    """Show the attacker's progress through the network"""
    print(f"\n🎯 Attacker Progress:")
    print(f"   Visible Nodes: {len(attacker.visible_nodes)}")
    print(f"   Compromised Nodes: {len(attacker.compromised_nodes)}")
    print(f"   Total Gain: ${attacker.total_gain:.2f}")
    print(f"   Total Costs: ${attacker.incurredCost:.2f}")
    print(f"   Net Profit: ${attacker.total_gain - attacker.incurredCost:.2f}")


def run_showcase_demo():
    """Run the complete showcase demonstration"""
    print("🧪 simTIM Showcase Demo: 3-Node Attack Progression")
    print("=" * 80)
    
    # Load the showcase network
    try:
        print("📋 Loading showcase network...")
        config = load_network_config("src/networks/library/showcase_network.json")
        network = create_network_from_config(config)
        
        # Convert to proper format
        if isinstance(network, dict) and 'nodes_list' not in network:
            nodes_list = list(network.values())
            network = {'nodes_list': nodes_list}
        
        # Create links from config
        links = set()
        for node in network['nodes_list']:
            if hasattr(node, 'links'):
                for link in node.links:
                    links.add(link)
        network['links_list'] = list(links)
        
        print(f"✅ Network loaded: {len(network['nodes_list'])} nodes, {len(network['links_list'])} links")
        
    except Exception as e:
        print(f"❌ Failed to load network: {e}")
        return False
    
    # Create actors
    print("\n👥 Creating actors...")
    
    # Load actions
    attack_actions = get_attack_actions()
    defense_actions = get_defense_actions()
    
    if not attack_actions:
        print("⚠️ No attack actions available")
        return False
    
    # Create attacker with greedy strategy (chooses highest-gain actions)
    attacker = Attacker("showcase_attacker", "greedy", capacity=3)
    attacker.available_actions = attack_actions
    
    # Create reactive defender
    defender = Defender("showcase_defender", "reactive", capacity=2)
    defender.available_actions = defense_actions
    
    network['actors'] = [attacker, defender]
    
    # Initialize access levels
    print("🔐 Setting up initial access levels...")
    for node in network['nodes_list']:
        node.access = {}
        node.access[attacker.id] = 'NONE'  # Attacker starts with no access
        node.access[defender.id] = 'ADMIN'  # Defender has admin access everywhere
    
    # Make internet-exposed nodes visible to attacker
    internet_exposed = 0
    for node in network['nodes_list']:
        if hasattr(node, 'properties') and node.properties.get('exposed_to_internet', False):
            node.access[attacker.id] = 'VISIBLE'
            attacker.visible_nodes.add(node)
            internet_exposed += 1
            display_name = getattr(node, 'name', node.id)
            print(f"🌐 {display_name} is internet-exposed → visible to attacker")
    
    if internet_exposed == 0:
        # Fallback: make first node visible
        first_node = network['nodes_list'][0]
        first_node.access[attacker.id] = 'VISIBLE'
        attacker.visible_nodes.add(first_node)
        display_name = getattr(first_node, 'name', first_node.id)
        print(f"🌐 {display_name} made visible (fallback)")
    
    print(f"✅ Actors created: 1 attacker, 1 defender")
    
    # Show initial network status
    print_network_status(network, "Initial Network State")
    print_attack_chain_progress(attacker, network)
    
    # Create and run simulator
    print(f"\n🚀 Starting simulation...")
    simulator = Simulator(network)
    
    # Run simulation for a reasonable time
    simulation_time = 20.0  # 20 simulated seconds
    print(f"⏱️ Running simulation for {simulation_time} seconds...")
    
    try:
        simulator.run(until=simulation_time)
        final_time = simulator.current_time  # Get the current time instead
        print(f"✅ Simulation completed at time {final_time:.2f}")
        
    except Exception as e:
        print(f"❌ Simulation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Show final results
    print_network_status(network, "Final Network State")
    print_attack_chain_progress(attacker, network)
    
    # Analyze what happened
    print(f"\n📈 Simulation Analysis:")
    print(f"{'='*60}")
    
    # Count compromised nodes
    compromised_nodes = [node for node in network['nodes_list'] if getattr(node, 'compromised', False)]
    print(f"🔴 Compromised Nodes: {len(compromised_nodes)}/{len(network['nodes_list'])}")
    
    for node in compromised_nodes:
        display_name = getattr(node, 'name', node.id)
        print(f"   ❌ {display_name} - Attacker Access: {node.access.get(attacker.id, 'NONE')}")
    
    # Show attacker's final access levels
    print(f"\n🎯 Attacker's Network Penetration:")
    for node in network['nodes_list']:
        access = node.access.get(attacker.id, 'NONE')
        if access != 'NONE':
            icon = "🔓" if access in ["USER", "ADMIN"] else "👁️"
            display_name = getattr(node, 'name', node.id)
            print(f"   {icon} {display_name}: {access}")
    
    # Economic summary
    net_profit = attacker.total_gain - attacker.incurredCost
    print(f"\n💰 Economic Impact:")
    print(f"   Attacker Gain: ${attacker.total_gain:.2f}")
    print(f"   Attacker Costs: ${attacker.incurredCost:.2f}")
    print(f"   Net Profit: ${net_profit:.2f}")
    
    if net_profit > 0:
        print(f"   📈 Attack was profitable!")
    else:
        print(f"   📉 Attack was not profitable")
    
    # Success assessment
    database_compromised = False
    high_value_accessed = False
    
    for node in network['nodes_list']:
        if 'database' in node.id.lower():
            if getattr(node, 'compromised', False) or node.access.get(attacker.id, 'NONE') == 'ADMIN':
                database_compromised = True
        
        if hasattr(node, 'properties') and node.properties.get('high_value_target', False):
            if node.access.get(attacker.id, 'NONE') in ['USER', 'ADMIN']:
                high_value_accessed = True
    
    print(f"\n🏆 Attack Success Metrics:")
    print(f"   Internet Entry: {'✅' if any(node.access.get(attacker.id, 'NONE') != 'NONE' for node in network['nodes_list']) else '❌'}")
    print(f"   Lateral Movement: {'✅' if len(attacker.compromised_nodes) > 1 else '❌'}")
    print(f"   High-Value Access: {'✅' if high_value_accessed else '❌'}")
    print(f"   Database Compromise: {'✅' if database_compromised else '❌'}")
    
    return True


def main():
    """Main entry point"""
    print("🎬 Starting simTIM Showcase Demo...")
    
    success = run_showcase_demo()
    
    if success:
        print(f"\n🎉 Showcase demo completed successfully!")
        print(f"📚 This demonstrates how simTIM simulates realistic attack progressions")
        print(f"🔍 Try running with different strategies or time limits to see variations")
    else:
        print(f"\n❌ Showcase demo failed")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
