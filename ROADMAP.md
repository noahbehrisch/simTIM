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
- reactive/balanced defender strategies read node.compromised directly, bypassing the detection_window filter -> use _get_detected_nodes so defender acts only on what it actually detected
- base_detection.py passes the Actor object (or "unknown") to action.get_detection_probability instead of actor.id -> pass actor.id
- _create_damage_functions returns constant lambdas that ignore the (node, access, actor) parameters -> damage cannot depend on target assets or actor; allow asset-based / actor-dependent specs in the validator
- AttackerStrategy.choose_action accepts network_state but never reads it, while DefenderStrategy.choose_action does -> asymmetric API, attacker subclass can silently leak ground truth; either drop the parameter or wrap as a per-actor view
- Defender reaches the network both via the network_state parameter and via self.simulator.network directly (defender.py L165) -> single source
- DefenderStrategy.get_priority signature carries network, but reactive.py and balanced.py never read it (only proactive.py and monitoring.py do) -> inconsistent across defender strategies
- SimulationObserver base class is unused; HistoryRecorder bypasses it via subscribe_all; DefenderAlertObserver is defined but never instantiated -> wire observers up or remove the dead abstraction
- EventType.STATE_CHANGED defined but never published -> remove
- Node.services: dict is read by the service_check JSON condition but never populated by the network loader -> service_check is dead
- Node.capabilities: list is neither populated nor read -> dead field
- port_access JSON condition reads node.exposed_services but no Action JSON triggers port_access -> half-dead feature; either use it in an Action or remove the loader/saver/validator code
- Actor.economic_events is appended only by the Attacker (attacker.py L115); Defender never writes to it -> dead storage for defenders
- Defender priority heuristic damage_rate = len(assets) * 100.0 (defender.py L169) is disconnected from the economic model and from action damage specs -> two parallel notions of damage; unify with action-derived values
- All defense JSONs set one_off_gain and time_gain to 0.0 -> defender Total Gain is structurally always $0 in the GUI Economic Impact panel; either define meaningful defender gain (e.g. prevented damage) or hide the field
- Three parallel economic aggregation paths (SimpleEconomicModel, per-event economics dict in results_window, actor.incurred_cost) can drift apart (e.g. time-proportional damage only flows into SimpleEconomicModel) -> one source of truth
- ResultsWindow._update_economics_view is an empty stub (results_window.py L1385) -> per-actor "Economic Impact" panel renders blank in the <=8-actors code path while the >8-actors dropdown path (_load_actor_data) renders the same data correctly; port the rendering logic into the stub

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
