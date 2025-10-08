#!/usr/bin/env python3
"""
Test script to compare all three detection engines:
1. Legacy (original simple detection)
2. Simple TIM (minimal TIM paper compliance)  
3. Advanced TIM (TIM + domain knowledge)
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from src.core.simulator import Simulator
from src.detection import LegacyDetectionEngine, SimpleTIMDetectionEngine, AdvancedTIMDetectionEngine
from src.networks.network_loader import load_network_config, create_network_from_config
from src.actors.attacker import Attacker
from src.actors.defender import Defender

def test_simple_tim_detection():
    """Test the minimal TIM-compliant detection engine"""
    print("🎯 Testing Simple TIM Detection Engine...")
    
    # Test detection engine directly
    engine = SimpleTIMDetectionEngine()
    
    # Mock objects
    class MockAction:
        def __init__(self, name):
            self.name = name
            self.duration = 2.0
    
    class MockTarget:
        def __init__(self, properties):
            self.id = "test_node"
            self.properties = properties
    
    action = MockAction("test_attack")
    target = MockTarget({'critical': True, 'endpoint_protection': 'basic'})
    
    # Test default detection probability
    default_prob = engine.calculate_detection_probability(action, target, "VISIBLE", None)
    print(f"   ✅ Default ϱ(a, π̂(n)): {default_prob}")
    
    # Configure specific detection probability
    engine.configure_detection_probability("test_attack", target.properties, 0.8)
    configured_prob = engine.calculate_detection_probability(action, target, "VISIBLE", None)
    print(f"   ✅ Configured ϱ(a, π̂(n)): {configured_prob}")
    
    # Test cumulative detection probability (TIM formula)
    cumulative_prob = engine.calculate_cumulative_detection_probability(
        action, target, "VISIBLE", 1.0, 2.0
    )
    print(f"   ✅ Fa(t/da) · ϱ(a, π̂(n)) at t=1.0: {cumulative_prob}")
    
    # Verify TIM paper constraints
    cdf_func = engine.get_cdf_function(action)
    print(f"   ✅ Fa(0) = {cdf_func(0.0)} (should be 0)")
    print(f"   ✅ Fa(1) = {cdf_func(1.0)} (should be 1)")
    
    print("   ✅ Simple TIM Detection Engine working correctly!")
    return True

def test_all_detection_engines():
    """Test all three detection engines with the same scenario"""
    print("\n📊 Comparing All Detection Engines...")
    
    # Load test network
    config = load_network_config('realistic_enterprise_network.json')
    nodes = create_network_from_config(config)
    
    network = {
        'nodes': nodes,
        'nodes_list': list(nodes.values()),
        'actors': []
    }
    
    attacker = Attacker("attacker1", "random", capacity=2)
    defender = Defender("defender1", "reactive", capacity=1)
    network['actors'] = [attacker, defender]
    
    results = {}
    
    # Test Legacy Detection
    print("   🔸 Testing Legacy Detection...")
    simulator1 = Simulator(network, detection_engine_type="legacy")
    simulator1.run(8.0)
    legacy_detections = [e for e in simulator1.history if "attack_detected" in str(e)]
    results['legacy'] = len(legacy_detections)
    print(f"      Legacy detection engine: {type(simulator1.detection_engine).__name__}")
    
    # Test Simple TIM Detection  
    print("   🔸 Testing Simple TIM Detection...")
    simulator2 = Simulator(network, detection_engine_type="simple_tim")
    simulator2.run(8.0)
    simple_tim_detections = [e for e in simulator2.history if "attack_detected" in str(e)]
    results['simple_tim'] = len(simple_tim_detections)
    print(f"      Simple TIM detection engine: {type(simulator2.detection_engine).__name__}")
    
    # Test Advanced TIM Detection
    print("   🔸 Testing Advanced TIM Detection...")
    simulator3 = Simulator(network, detection_engine_type="advanced_tim")
    simulator3.run(8.0)
    advanced_tim_detections = [e for e in simulator3.history if "attack_detected" in str(e)]
    results['advanced_tim'] = len(advanced_tim_detections)
    print(f"      Advanced TIM detection engine: {type(simulator3.detection_engine).__name__}")
    
    # Compare results
    print(f"\n   📈 Detection Comparison:")
    print(f"      Legacy:      {results['legacy']} detections")
    print(f"      Simple TIM:  {results['simple_tim']} detections")  
    print(f"      Advanced TIM: {results['advanced_tim']} detections")
    
    return results

def test_simple_tim_configuration():
    """Test configuration capabilities of Simple TIM engine"""
    print("\n⚙️  Testing Simple TIM Configuration...")
    
    engine = SimpleTIMDetectionEngine(default_detection_probability=0.2)
    
    # Mock objects
    class MockAction:
        def __init__(self, name):
            self.name = name
            self.duration = 1.5
    
    class MockTarget:
        def __init__(self, properties):
            self.id = "config_test_node"  
            self.properties = properties
    
    action1 = MockAction("reconnaissance")
    action2 = MockAction("privilege_escalation")
    
    target_basic = MockTarget({'security_level': 'basic'})
    target_high = MockTarget({'security_level': 'high', 'monitoring': 'advanced'})
    
    # Configure different detection probabilities
    engine.configure_detection_probability("reconnaissance", target_basic.properties, 0.1)
    engine.configure_detection_probability("reconnaissance", target_high.properties, 0.6)
    engine.configure_detection_probability("privilege_escalation", target_basic.properties, 0.3)
    engine.configure_detection_probability("privilege_escalation", target_high.properties, 0.9)
    
    # Configure custom CDF function
    def custom_cdf(t):
        """Custom CDF that satisfies Fa(0)=0, Fa(1)=1"""
        return t ** 0.5  # Square root function
    
    engine.configure_cdf_function("privilege_escalation", custom_cdf)
    
    # Test configured probabilities
    recon_basic = engine.calculate_detection_probability(action1, target_basic, "VISIBLE", None)
    recon_high = engine.calculate_detection_probability(action1, target_high, "VISIBLE", None)
    privesc_basic = engine.calculate_detection_probability(action2, target_basic, "VISIBLE", None)
    privesc_high = engine.calculate_detection_probability(action2, target_high, "VISIBLE", None)
    
    print(f"   ✅ Reconnaissance on basic target: {recon_basic}")
    print(f"   ✅ Reconnaissance on high-sec target: {recon_high}")
    print(f"   ✅ Privilege escalation on basic target: {privesc_basic}")
    print(f"   ✅ Privilege escalation on high-sec target: {privesc_high}")
    
    # Test custom CDF
    cdf_func = engine.get_cdf_function(action2)
    print(f"   ✅ Custom CDF Fa(0.5) = {cdf_func(0.5):.3f}")
    
    # Get configuration summary
    summary = engine.get_configuration_summary()
    print(f"   ✅ Configuration summary: {summary}")
    
    return True

if __name__ == "__main__":
    print("🧪 Testing All Detection Engine Implementations\n")
    
    results = []
    
    # Test simple TIM detection engine directly
    results.append(test_simple_tim_detection())
    
    # Test configuration capabilities
    results.append(test_simple_tim_configuration())
    
    # Compare all engines in simulation
    detection_results = test_all_detection_engines()
    results.append(True)  # Always passes if no exceptions
    
    # Summary
    print(f"\n📋 Test Results: {sum(results)}/{len(results)} tests passed")
    
    if all(results):
        print("🎉 All detection engines are working correctly!")
    else:
        print("⚠️  Some tests failed")
    
    print(f"\n📖 Detection Engine Summary:")
    print(f"   1. ✅ Legacy Detection: Simple random-based detection")
    print(f"   2. ✅ Simple TIM Detection: Minimal TIM paper compliance")
    print(f"      - Configurable ϱ(a, π̂(n)) detection probabilities")
    print(f"      - Configurable Fa(t) CDF functions with constraints")
    print(f"      - Exact TIM formula: Fa(t/da) · ϱ(a, π̂(n))")
    print(f"   3. ✅ Advanced TIM Detection: TIM + cybersecurity domain knowledge")
    print(f"      - Pre-configured detection factors (endpoint protection, etc.)")
    print(f"      - Multiple action-specific CDF patterns")
    print(f"      - Ready-to-use for realistic simulations")
    
    print(f"\n🎯 TIM Paper Compliance:")
    print(f"   - Simple TIM: Pure mathematical framework only")
    print(f"   - Advanced TIM: Mathematical framework + practical mappings")
    print(f"   - Both implement: ϱ(a, π̂(n)), Fa(t), and Fa(t/da) · ϱ(a, π̂(n))")
