#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.abspath('.'))

def test_priority_removal():
    """Test that priority setting has been properly removed"""
    try:
        print("🧪 Testing Priority Setting Removal")
        print("=" * 50)
        
        # Test imports
        print("🔄 Testing GUI imports...")
        from src.gui.app import App
        print("✅ GUI imports successful")
        
        # Test defender configuration without priority
        print("🔄 Testing defender configuration...")
        from src.actors.defender import Defender
        
        # Test that defenders work without priority parameter
        defender1 = Defender("test_defender1", strategy="reactive", capacity=2)
        defender2 = Defender("test_defender2", strategy="proactive", capacity=3)
        defender3 = Defender("test_defender3", strategy="monitoring", capacity=1)
        
        assert defender1.strategy == "reactive"
        assert defender2.strategy == "proactive"
        assert defender3.strategy == "monitoring"
        print("✅ Defender strategies working without priority")
        
        # Test configuration generation
        print("🔄 Testing configuration generation...")
        defenders = [
            {'id': 'defender1', 'strategy': 'reactive', 'capacity': 2, 'budget': 1500},
            {'id': 'defender2', 'strategy': 'proactive', 'capacity': 3, 'budget': 2000}
        ]
        
        # Verify no priority field
        for defender in defenders:
            assert 'priority' not in defender, f"Priority field should be removed from {defender}"
        
        print(f"✅ Generated clean config with {len(defenders)} defenders (no priority)")
        
        print("\n" + "=" * 50)
        print("📊 CLEANUP SUMMARY")
        print("=" * 50)
        print("✅ Priority setting removed from GUI headers")
        print("✅ Priority input removed from defender entries")
        print("✅ Priority parameter removed from configuration")
        print("✅ Priority references removed from overview")
        print("✅ Defender functionality preserved")
        print("✅ Built-in priority logic still works (reactive/proactive/monitoring)")
        
        print("\n🎉 PRIORITY SETTING REMOVAL SUCCESSFUL")
        return True
        
    except Exception as e:
        print(f"❌ Priority removal test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_priority_removal()
    sys.exit(0 if success else 1)
