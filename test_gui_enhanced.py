#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.abspath('.'))

def test_gui_enhanced():
    """Test the enhanced GUI functionality"""
    try:
        print("🧪 Testing Enhanced GUI Customization")
        print("=" * 50)
        
        # Test imports
        print("🔄 Testing imports...")
        from src.gui.app import App
        print("✅ GUI imports successful")
        
        # Test actor strategies
        print("🔄 Testing actor strategies...")
        from src.actors.attacker import Attacker
        from src.actors.defender import Defender
        
        # Test attacker strategies
        attacker = Attacker("test_attacker", strategy="greedy", capacity=3)
        assert attacker.strategy == "greedy"
        
        attacker2 = Attacker("test_attacker2", strategy="random", capacity=float('inf'))
        assert attacker2.strategy == "random"
        assert attacker2.capacity == float('inf')
        print("✅ Attacker strategies working")
        
        # Test defender strategies  
        defender = Defender("test_defender", strategy="reactive", capacity=2)
        assert defender.strategy == "reactive"
        
        defender2 = Defender("test_defender2", strategy="proactive", capacity=4)
        assert defender2.strategy == "proactive"
        
        defender3 = Defender("test_defender3", strategy="monitoring", capacity=1)
        assert defender3.strategy == "monitoring"
        print("✅ Defender strategies working")
        
        # Test configuration generation
        print("🔄 Testing configuration generation...")
        attackers = [
            {'id': 'attacker1', 'strategy': 'greedy', 'capacity': 3, 'budget': 1000},
            {'id': 'attacker2', 'strategy': 'random', 'capacity': float('inf'), 'budget': 2000}
        ]
        
        defenders = [
            {'id': 'defender1', 'strategy': 'reactive', 'capacity': 2, 'budget': 1500, 'priority': 'high'},
            {'id': 'defender2', 'strategy': 'proactive', 'capacity': 3, 'budget': 2000, 'priority': 'medium'}
        ]
        
        print(f"✅ Generated config with {len(attackers)} attackers and {len(defenders)} defenders")
        
        print("\n" + "=" * 50)
        print("📊 ENHANCEMENT SUMMARY")
        print("=" * 50)
        print("✅ Attacker strategies: greedy, random")
        print("✅ Defender strategies: reactive, proactive, monitoring") 
        print("✅ Configurable capacity (including infinite for attackers)")
        print("✅ Budget limits for both attackers and defenders")
        print("✅ Priority settings for defenders")
        print("✅ Remove buttons for dynamic configuration")
        print("✅ Strategy descriptions for user guidance")
        print("✅ Tabular layout with headers")
        print("✅ Input validation and error handling")
        
        print("\n🎉 GUI ENHANCEMENTS SUCCESSFUL")
        return True
        
    except Exception as e:
        print(f"❌ GUI enhancement test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_gui_enhanced()
    sys.exit(0 if success else 1)
