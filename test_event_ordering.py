"""Test event ordering to ensure action_finished is processed before actor_run"""
import sys
sys.path.insert(0, '.')

from src.core.simulator import Event

# Create events at the same timestamp
events = [
    Event(1.0, 'actor_run', {}),
    Event(1.0, 'action_finished', {}),
    Event(1.0, 'start_action', {}),
    Event(1.0, 'attack_detected', {}),
]

print("Events before sorting:")
for e in events:
    print(f"  {e}")

# Sort them (simulates heap ordering)
events.sort()

print("\nEvents after sorting:")
for e in events:
    print(f"  {e}")

print("\n" + "="*60)
print("Event Ordering Test")
print("="*60)

# Verify order
expected_order = ['action_finished', 'attack_detected', 'actor_run', 'start_action']
actual_order = [e.event_type for e in events]

if actual_order == expected_order:
    print("✅ PASS: Events are ordered correctly by priority")
    print(f"   Order: {' → '.join(actual_order)}")
    print("\n✓ action_finished will be processed BEFORE actor_run")
    print("✓ This prevents the race condition!")
else:
    print("❌ FAIL: Events are not in expected order")
    print(f"   Expected: {expected_order}")
    print(f"   Actual:   {actual_order}")
    sys.exit(1)

# Test that different timestamps still work correctly
events2 = [
    Event(2.0, 'actor_run', {}),
    Event(1.0, 'action_finished', {}),
    Event(1.5, 'start_action', {}),
]

events2.sort()
times = [e.time for e in events2]
if times == [1.0, 1.5, 2.0]:
    print("\n✅ PASS: Time ordering still works correctly")
else:
    print(f"\n❌ FAIL: Time ordering broken: {times}")
    sys.exit(1)
