"""Test to verify the repeated action bug is fixed"""
import sys
sys.path.insert(0, '.')

from src.core.graph import Node
from src.actions.action_manager import action_manager, would_action_improve_access
from src.core.access_levels import NodeAccessLevel

# Load the Active Network Scan action
actions = action_manager.load_actions_from_directory('src/actions/library/attacks')
scan_action = next((a for a in actions if a.name == "Active Network Scan"), None)

if not scan_action:
    print("❌ Could not find Active Network Scan action")
    sys.exit(1)

print("✓ Loaded Active Network Scan action")

# Create a test node
node = Node(
    id="test_node",
    software={"os": "Linux"},
    vulnerabilities=[],
    assets=[]
)
node.properties = {"exposed_to_internet": True}
node.access = {"attacker1": NodeAccessLevel.VISIBLE.to_string()}

print(f"✓ Created test node with VISIBLE access")

# Test 1: First execution should be beneficial
current_access = NodeAccessLevel.VISIBLE
is_beneficial = would_action_improve_access(scan_action, node, current_access, "attacker1")
print(f"\nTest 1: First scan on node")
print(f"  Would action improve access? {is_beneficial}")
if is_beneficial:
    print("  ✓ PASS: First scan is considered beneficial")
else:
    print("  ❌ FAIL: First scan should be beneficial")

# Test 2: Simulate successful execution
print(f"\nSimulating successful execution...")
node.successful_actions_by_actor = {"attacker1": {"Active Network Scan"}}
print(f"  ✓ Marked action as successfully completed")

# Test 3: Second execution should NOT be beneficial
is_beneficial_2 = would_action_improve_access(scan_action, node, current_access, "attacker1")
print(f"\nTest 2: Second scan on same node")
print(f"  Would action improve access? {is_beneficial_2}")
if not is_beneficial_2:
    print("  ✓ PASS: Repeated scan is NOT beneficial")
else:
    print("  ❌ FAIL: Repeated scan should not be beneficial")

# Test 4: Check postcondition analysis
from src.actions.action_manager import analyze_action_access_impact
predicted = analyze_action_access_impact(scan_action, "VISIBLE")
print(f"\nTest 3: Postcondition analysis")
print(f"  Predicted access impact: {predicted}")
if predicted == "NO_ACCESS_CHANGE":
    print("  ✓ PASS: Correctly identifies scan doesn't change node access")
else:
    print(f"  ❌ FAIL: Should return 'NO_ACCESS_CHANGE', got '{predicted}'")

# Summary
print("\n" + "="*60)
print("Bug Fix Verification Summary")
print("="*60)
if is_beneficial and not is_beneficial_2 and predicted == "NO_ACCESS_CHANGE":
    print("✅ ALL TESTS PASSED - Bug is fixed!")
    print("\nThe attacker will now:")
    print("  • Execute network scans once per node")
    print("  • Skip nodes that have already been scanned")
    print("  • Choose different actions or targets")
else:
    print("❌ SOME TESTS FAILED - Bug may still exist")
    sys.exit(1)
