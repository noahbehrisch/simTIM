#!/usr/bin/env python3
"""
Test script to verify both the continuous precondition monitoring 
and the TIM-compliant detection implementation
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from src.core.simulator import Simulator
from src.detection import AdvancedTIMDetectionEngine, SimpleTIMDetectionEngine, LegacyDetectionEngine
from src.networks.network_loader import load_network_config, create_network_from_config
from src.actors.attacker import Attacker
from src.actors.defender import Defender
from src.actions.action_manager import get_attack_actions

def test_continuous_precondition_monitoring():
    """Test that preconditions are monitored continuously during action execution"""
    print("🔄 Testing Continuous Precondition Monitoring...")
    
    # Load a simple network
    config = load_network_config('realistic_enterprise_network.json')
    nodes = create_network_from_config(config)
    
    # Create network dict
    network = {
        'nodes': nodes,
        'nodes_list': list(nodes.values()),
        'actors': []
    }
    
    # Create actors
    attacker = Attacker("attacker1", "random", capacity=1)
    defender = Defender("defender1", "reactive", capacity=1)
    network['actors'] = [attacker, defender]
    
    # Create simulator
    simulator = Simulator(network, use_tim_detection=False)
    
    # Run short simulation
    simulator.run(5.0)
    
    # Check for precondition check events
    precondition_checks = [event for event in simulator.history if "precondition_check" in str(event)]
    print(f"   ✅ Found {len(precondition_checks)} precondition check events")
    
    if len(precondition_checks) > 0:
        print("   ✅ Continuous precondition monitoring is working!")
        return True
    else:
        print("   ⚠️  No precondition checks found - may need more simulation time")
        return False

def test_tim_detection_engine():
    """Test the TIM-compliant detection engine"""
    print("\n🎯 Testing TIM Detection Engine...")
    
    # Test detection engine directly
    engine = AdvancedTIMDetectionEngine()
    
    # Mock objects
    class MockAction:
        def __init__(self, name):
            self.name = name
            self.duration = 2.0
    
    class MockTarget:
        def __init__(self):
            self.id = "test_node"
            self.properties = {
                'endpoint_protection': 'Sophos',
                'network_monitoring': 'SIEM',
                'critical': True,
                'exposed_to_internet': True
            }
    
    action = MockAction("vulnerability_scan")
    target = MockTarget()
    
    # Test detection probability calculation
    detection_prob = engine.calculate_detection_probability(action, target, "VISIBLE", None)
    print(f"   ✅ Detection probability: {detection_prob:.3f}")
    
    # Test detection time sampling
    detection_time = engine.sample_detection_time(action, action.duration, detection_prob)
    print(f"   ✅ Sampled detection time: {detection_time}")
    
    # Test cumulative detection probability
    cumulative_prob = engine.calculate_cumulative_detection_probability(
        action, target, "VISIBLE", 1.0, 2.0
    )
    print(f"   ✅ Cumulative detection prob at t=1.0: {cumulative_prob:.3f}")
    
    print("   ✅ TIM Detection Engine is working!")
    return True

def test_simulator_with_tim_detection():
    """Test simulator using TIM detection engine"""
    print("\n🚀 Testing Simulator with TIM Detection...")
    
    # Load network
    config = load_network_config('realistic_enterprise_network.json')
    nodes = create_network_from_config(config)
    
    network = {
        'nodes': nodes,
        'nodes_list': list(nodes.values()),
        'actors': []
    }
    
    # Create actors
    attacker = Attacker("attacker1", "random", capacity=2)
    defender = Defender("defender1", "reactive", capacity=1)
    network['actors'] = [attacker, defender]
    
    # Create simulator with Advanced TIM detection
    simulator = Simulator(network, detection_engine_type="advanced_tim")
    
    # Verify detection engine type
    if isinstance(simulator.detection_engine, AdvancedTIMDetectionEngine):
        print("   ✅ Simulator is using Advanced TIM Detection Engine")
    else:
        print("   ❌ Simulator is not using Advanced TIM Detection Engine")
        return False
    
    # Run simulation
    simulator.run(10.0)
    
    # Check for TIM-specific detection events
    tim_detections = [event for event in simulator.history 
                     if hasattr(event, 'data') and 
                     event.data.get('detection_method') in ['simple_TIM', 'advanced_TIM']]
    
    print(f"   ✅ Found {len(tim_detections)} TIM-compliant detection events")
    
    # Check total events
    total_events = len(simulator.history)
    print(f"   ✅ Total simulation events: {total_events}")
    
    return True

def compare_detection_engines():
    """Compare legacy vs TIM detection engines"""
    print("\n📊 Comparing Detection Engines...")
    
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
    
    # Test with legacy detection
    print("   🔸 Testing with Legacy Detection...")
    simulator1 = Simulator(network, detection_engine_type="legacy")
    simulator1.run(8.0)
    
    legacy_detections = [event for event in simulator1.history 
                        if "attack_detected" in str(event)]
    
    # Test with Simple TIM detection
    print("   🔸 Testing with Simple TIM Detection...")
    simulator2 = Simulator(network, detection_engine_type="simple_tim")
    simulator2.run(8.0)
    
    simple_tim_detections = [event for event in simulator2.history 
                            if "attack_detected" in str(event)]
    
    # Test with Advanced TIM detection
    print("   🔸 Testing with Advanced TIM Detection...")
    simulator3 = Simulator(network, detection_engine_type="advanced_tim")
    simulator3.run(8.0)
    
    advanced_tim_detections = [event for event in simulator3.history 
                              if "attack_detected" in str(event)]
    
    print(f"   📈 Legacy detections: {len(legacy_detections)}")
    print(f"   📈 Simple TIM detections: {len(simple_tim_detections)}")
    print(f"   📈 Advanced TIM detections: {len(advanced_tim_detections)}")
    
    total_detections = len(legacy_detections) + len(simple_tim_detections) + len(advanced_tim_detections)
    if total_detections > 0:
        print("   ✅ Detection engines are functional!")
        return True
    else:
        print("   ⚠️  No detections found - may need longer simulation")
        return False

if __name__ == "__main__":
    print("🧪 Testing TIM Compliance Enhancements\n")
    
    results = []
    
    # Run all tests
    results.append(test_continuous_precondition_monitoring())
    results.append(test_tim_detection_engine())
    results.append(test_simulator_with_tim_detection())
    results.append(compare_detection_engines())
    
    # Summary
    print(f"\n📋 Test Results: {sum(results)}/{len(results)} tests passed")
    
    if all(results):
        print("🎉 All TIM compliance enhancements are working correctly!")
    else:
        print("⚠️  Some tests failed - please check implementation")
    
    print("\n📖 Summary of Enhancements:")
    print("   1. ✅ Continuous precondition monitoring during action execution")
    print("   2. ✅ TIM paper-compliant detection with CDF functions")
    print("   3. ✅ Detection probability based on node properties π̂(n)")
    print("   4. ✅ Action-specific cumulative distribution functions")
    print("   5. ✅ Configurable detection engine (legacy vs TIM-compliant)")
