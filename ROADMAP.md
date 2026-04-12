# Project Roadmap

## Commit Types

Commits adhere to [Commit conventions](https://www.conventionalcommits.org/en/v1.0.0/):
| Type      | Description |
|-----------|-------------|
| feat      | A new feature |
| fix       | A bug fix |
| docs      | Documentation-only changes |
| style     | Formatting changes (no logic changes) |
| refactor  | Code changes that neither fix a bug nor add a feature |
| test      | Adding or updating tests |
| chore     | Maintenance, tooling, config, dependencies |
| perf      | Performance improvements |
| ci        | CI/CD-related changes |
| build     | Build system or dependency changes |

## Core

- Scenario Comparison:
    - Extend for Network, Budget, Capacity, Action parameters besides duration, etc.
    - Maybe it would be reasonable to build a wrapper
- Add random seed control for reproducibility

## Bugs

- handle_action_finished uses stale actor_access from decision time -> recalculate from node at finish time
- Time-proportional economic rates never removed after eviction -> damage accumulates forever
- Duration overrides mutate shared Action objects in action_manager singleton -> deep-copy before mutating
- ongoing_actions is a set, can't track same action on multiple targets -> actors exceed capacity
- set_access_neighbors bypasses access tracking (raw string, no record_access_change, marks all neighbors compromised)
- Simulation loop processes events past deadline -> check event.time > until after pop
- Duplicate economic calculation block in _calculate_economic_impact (copy-paste)
- property_check missing numeric comparison operators (greater_than, less_than)
- modify_property uses setattr instead of node.properties dict
- No tiebreaker for same-time same-priority events in heapq

## GUI

- Help windows: -> More descriptive and user-friendly

## Visualization

- seperation into different files for each plot for better modularity

## Network

- Adding new Node properties in the GUI
- Dynamic Behavior as per TIM Model
    - Removing and adding Nodes and Links

## Software Architecture

- Safe imports everywhere -> typecheck

## Actions

- Modifiable Actions in the GUI
- Action Creator in the GUI
- Tweaking actions to make them as realistic as possible is an ongoing chore

## Strategies

- using the MITRE ATT&CK and D3EFEND matrizes as the basis for strategies
- reinforcement learning as a strategy

## Testing

- Build a big test network
- more demo/test networks
- Test the app on different operating systems (Arch, Ubuntu, Windows, MacOS)
- Test compatibility of different versions (Python, Numpy, Matpotlib)

## Performance

- Multithreading with disabled GIL or Multiprocessing -> one simulation per thread with its own instances (no global instances)
