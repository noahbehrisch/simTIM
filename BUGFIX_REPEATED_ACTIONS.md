# Bug Fix: Attacker Repeating Same Action

## Problem Analysis

### Observed Behavior
The attacker was repeatedly executing the same "Active Network Scan" action on the same node (`web_server`), as seen in the event queue:

```
[  0.00] ❌ attacker1 failed Active Network Scan → web_server
[  2.00] ✅ attacker1 succeeded Active Network Scan → web_server
[  2.00] ❌ attacker1 failed Active Network Scan → web_server  # Immediate retry!
[  3.00] ✅ attacker1 succeeded Active Network Scan → web_server
[  3.00] ❌ attacker1 failed Active Network Scan → web_server  # Immediate retry!
```

### Root Cause

The issue was in the `would_action_improve_access()` function in `src/actions/action_manager.py`. This function determines if an action would be beneficial for the attacker to execute.

**"Active Network Scan" action characteristics:**
- **Precondition**: `access >= VISIBLE` ✓
- **Postcondition**: `set_links_access` to `VISIBLE` (makes links visible)
- **Does NOT change node access level** - only discovers network topology

**The bug chain:**

1. The action's postcondition type is `set_links_access`, which doesn't modify node access
2. `analyze_action_access_impact()` correctly returns `None` (can't determine access impact)
3. Falls back to heuristic analysis based on action name
4. Sees "scan" keyword in "Active Network Scan"
5. **Incorrectly** categorizes it as targeting `USER` access level
6. Compares: current (`VISIBLE`) < target (`USER`)? → True
7. Returns `True` - action appears beneficial
8. **Repeats indefinitely** even after successful execution!

### Why This Is Wrong

Network scan actions provide **information/discovery**, not **access escalation**:
- They discover links and connected nodes
- Once discovered, re-scanning provides no benefit
- Should only be executed **once per node**

## Solution

### Changes Made

#### 1. Enhanced `_analyze_postcondition_access()` (action_manager.py)

Added explicit detection of non-access-changing postconditions:

```python
elif postcondition.get('type') in ['set_links_access', 'set_property', 'clear_assets', 
                                    'add_vulnerability', 'remove_vulnerability', 
                                    'increment_counter', 'set_software']:
    # These postconditions don't change node access level
    return 'NO_ACCESS_CHANGE'
```

#### 2. Updated `would_action_improve_access()` (action_manager.py)

Now handles three cases:

**Case 1: Actions that don't change node access**
```python
if predicted_access == 'NO_ACCESS_CHANGE':
    # Check if already executed successfully on this node
    if hasattr(node, 'successful_actions_by_actor'):
        actor_actions = node.successful_actions_by_actor.get(actor_id, set())
        if action.name in actor_actions:
            return False  # Already done, not beneficial
    return True  # First time is beneficial
```

**Case 2: Scan/discovery actions (heuristic fallback)**
```python
if any(keyword in action_name_lower for keyword in ['scan', 'reconnaissance', 'discovery']):
    if hasattr(node, 'successful_actions_by_actor'):
        actor_actions = node.successful_actions_by_actor.get(actor_id, set())
        if action.name in actor_actions:
            return False  # Already scanned
    return True  # First scan is beneficial
```

**Case 3: Access escalation actions (existing logic)**
- Phishing, exploitation → target USER level
- Privilege escalation → target ADMIN level
- Data exfiltration → requires USER, doesn't improve access

#### 3. Track Successful Actions (simulator.py)

Added tracking in `handle_action_finished()`:

```python
# Track successful action execution on this node
target = data["target"]
actor_id = data["actor"].id
action_name = data["action"].name
if hasattr(target, 'id'):  # Only for node targets
    if not hasattr(target, 'successful_actions_by_actor'):
        target.successful_actions_by_actor = {}
    if actor_id not in target.successful_actions_by_actor:
        target.successful_actions_by_actor[actor_id] = set()
    target.successful_actions_by_actor[actor_id].add(action_name)
```

## Expected Behavior After Fix

1. Attacker performs "Active Network Scan" on `web_server` → Success
2. Links become visible, connected nodes discovered
3. Action marked as successfully completed on this node
4. `would_action_improve_access()` checks history
5. Returns `False` - already scanned this node
6. Attacker chooses **different action** or **different target**

## Impact

- **Fixes repeated action bug**: Actions are no longer executed multiple times unnecessarily
- **Better strategy**: Attackers will now pursue diverse attack paths
- **Performance**: Reduces wasted simulation cycles on redundant actions
- **Realism**: Matches actual attacker behavior (don't re-scan the same system)

## Action Categories Affected

### Non-Access-Changing (execute once per node):
- Network scanning/reconnaissance
- Data exfiltration
- Property modifications
- Vulnerability management

### Access-Changing (can repeat to escalate):
- Initial access (phishing, exploitation)
- Privilege escalation
- Lateral movement

## Testing Recommendations

1. Run simulation with attacker strategy (random/greedy)
2. Verify diverse actions in event queue
3. Check that network scans only execute once per node
4. Confirm access escalation still works (VISIBLE → USER → ADMIN)
5. Monitor attacker decision-making debug output
