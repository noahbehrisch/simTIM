"""Test attacker kill chain progression"""
import sys
sys.path.insert(0, '.')

from src.core.graph import Node
from src.actions.action_manager import action_manager, would_action_improve_access
from src.core.access_levels import NodeAccessLevel
from src.core.access_utils import set_node_access

# Load actions
actions = action_manager.load_actions_from_directory('src/actions/library/attacks')
scan_action = next((a for a in actions if a.name == "Active Network Scan"), None)
phishing_action = next((a for a in actions if a.name == "Spear Phishing Attack"), None)
privesc_action = next((a for a in actions if a.name == "Windows Privilege Escalation"), None)
exfil_action = next((a for a in actions if a.name == "Data Exfiltration"), None)

print("=== KILL CHAIN TEST ===\n")

# Create test node
node = Node(
    id="target_server",
    software={"os": "Windows Server"},
    vulnerabilities=["CVE-2023-1234"],
    assets=["customer_data", "financial_records"]
)
node.properties = {"exposed_to_internet": True}
node.links = []

actor_id = "attacker1"

# Stage 0: Initial reconnaissance (NONE → VISIBLE)
print("Stage 0: Initial State")
print(f"  Access Level: NONE")
set_node_access(node, actor_id, NodeAccessLevel.NONE)
print()

# Stage 1: Network scanning
print("Stage 1: Network Scanning (discovers the target)")
set_node_access(node, actor_id, NodeAccessLevel.VISIBLE)
access = NodeAccessLevel.VISIBLE
print(f"  Access Level: {access.to_string()}")
if scan_action:
    can_scan = would_action_improve_access(scan_action, node, access, actor_id)
    print(f"  Can perform Network Scan? {can_scan}")
    if can_scan:
        print("  ✓ Scanning to discover network topology...")
        node.successful_actions_by_actor = {actor_id: {"Active Network Scan"}}
print()

# Stage 2: Initial access (VISIBLE → USER)
print("Stage 2: Initial Access Attack")
print(f"  Access Level: {access.to_string()}")
if phishing_action:
    can_phish = would_action_improve_access(phishing_action, node, access, actor_id)
    print(f"  Can perform Phishing Attack? {can_phish}")
    if can_phish:
        print("  ✓ Sending spear phishing email...")
        set_node_access(node, actor_id, NodeAccessLevel.USER)
        access = NodeAccessLevel.USER
        print(f"  → Access escalated to: {access.to_string()}")
print()

# Stage 3: Privilege escalation (USER → ADMIN)
print("Stage 3: Privilege Escalation")
print(f"  Access Level: {access.to_string()}")
if privesc_action:
    can_escalate = would_action_improve_access(privesc_action, node, access, actor_id)
    print(f"  Can perform Privilege Escalation? {can_escalate}")
    if can_escalate:
        print("  ✓ Exploiting Windows vulnerability...")
        set_node_access(node, actor_id, NodeAccessLevel.ADMIN)
        access = NodeAccessLevel.ADMIN
        print(f"  → Access escalated to: {access.to_string()}")
print()

# Stage 4: Data exfiltration
print("Stage 4: Data Exfiltration")
print(f"  Access Level: {access.to_string()}")
print(f"  Assets on node: {node.assets}")
if exfil_action:
    can_exfil = would_action_improve_access(exfil_action, node, access, actor_id)
    print(f"  Can perform Data Exfiltration? {can_exfil}")
    if can_exfil:
        print("  ✓ Exfiltrating sensitive data...")
        if actor_id not in node.successful_actions_by_actor:
            node.successful_actions_by_actor[actor_id] = set()
        node.successful_actions_by_actor[actor_id].add("Data Exfiltration")
        node.assets.clear()
        print(f"  → Assets exfiltrated, remaining: {node.assets}")
print()

# Stage 5: Try exfiltration again (should fail - no assets left)
print("Stage 5: Attempt Repeated Exfiltration")
print(f"  Access Level: {access.to_string()}")
print(f"  Assets on node: {node.assets}")
if exfil_action:
    can_exfil_again = would_action_improve_access(exfil_action, node, access, actor_id)
    print(f"  Can perform Data Exfiltration again? {can_exfil_again}")
    if not can_exfil_again:
        print("  ✓ Correctly prevented (no assets remaining)")
    else:
        print("  ❌ ERROR: Should not allow re-exfiltration!")
print()

print("="*60)
print("KILL CHAIN VALIDATION")
print("="*60)

success_count = 0
total_tests = 5

# Test 1: Network scan should work once
if scan_action and would_action_improve_access(scan_action, node, NodeAccessLevel.VISIBLE, "test"):
    print("✓ Test 1: Network scanning enabled")
    success_count += 1
else:
    print("❌ Test 1: Network scanning broken")

# Test 2: Phishing from VISIBLE should work
test_node = Node(id="test", software={}, vulnerabilities=[], assets=[])
test_node.links = []
set_node_access(test_node, "test", NodeAccessLevel.VISIBLE)
if phishing_action and would_action_improve_access(phishing_action, test_node, NodeAccessLevel.VISIBLE, "test"):
    print("✓ Test 2: Initial access (phishing) enabled")
    success_count += 1
else:
    print("❌ Test 2: Initial access broken")

# Test 3: Privilege escalation from USER should work
test_node2 = Node(id="test2", software={"os": "Windows"}, vulnerabilities=["test"], assets=[])
test_node2.links = []
set_node_access(test_node2, "test", NodeAccessLevel.USER)
if privesc_action and would_action_improve_access(privesc_action, test_node2, NodeAccessLevel.USER, "test"):
    print("✓ Test 3: Privilege escalation enabled")
    success_count += 1
else:
    print("❌ Test 3: Privilege escalation broken")

# Test 4: Data exfiltration from ADMIN with assets should work
test_node3 = Node(id="test3", software={}, vulnerabilities=[], assets=["data"])
test_node3.links = []
set_node_access(test_node3, "test", NodeAccessLevel.ADMIN)
if exfil_action and would_action_improve_access(exfil_action, test_node3, NodeAccessLevel.ADMIN, "test"):
    print("✓ Test 4: Data exfiltration enabled")
    success_count += 1
else:
    print("❌ Test 4: Data exfiltration broken")

# Test 5: Data exfiltration without assets should NOT work
test_node4 = Node(id="test4", software={}, vulnerabilities=[], assets=[])
test_node4.links = []
set_node_access(test_node4, "test", NodeAccessLevel.ADMIN)
if exfil_action and not would_action_improve_access(exfil_action, test_node4, NodeAccessLevel.ADMIN, "test"):
    print("✓ Test 5: Repeated exfiltration prevented")
    success_count += 1
else:
    print("❌ Test 5: Repeated exfiltration not prevented")

print()
if success_count == total_tests:
    print(f"✅ ALL {total_tests} TESTS PASSED - Kill chain works correctly!")
    print("\nExpected attack progression:")
    print("  1. Network Scan (VISIBLE)")
    print("  2. Spear Phishing (VISIBLE → USER)")
    print("  3. Privilege Escalation (USER → ADMIN)")
    print("  4. Data Exfiltration (ADMIN)")
    print("  5. Lateral Movement to next target")
else:
    print(f"❌ FAILED: {success_count}/{total_tests} tests passed")
    sys.exit(1)
