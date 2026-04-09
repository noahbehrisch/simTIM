# simTIM Developer Documentation

## Table of Contents

- [Getting Started](#getting-started)
- [Architecture](#architecture)
- [Developing Actions](#developing-actions)
- [Developing Strategies](#developing-strategies)
- [Simulator Core](#simulator-core)

---

## Getting Started

```bash
git clone https://github.com/noahbehrisch/simTIM.git
make install-dev    # creates venv, installs all deps + dev tools
make run            # GUI
make demo           # CLI demo run
make test           # pytest
make lint           # ruff + mypy
make format         # auto-format
```

---

## Architecture

```
SimulationRunner → SimulationOrchestrator → Simulator (event loop)
                                             ├── Attacker (strategy → choose actions)
                                             ├── Defender (strategy → choose actions)
                                             ├── DetectionEngine (CDF-based timing)
                                             ├── EconomicModel (damage/gains tracking)
                                             └── Network (nodes + links)
```

All extension points are auto-discovered:
- `src/actions/library/{attacks,defenses}/{node,link}/` — JSON action definitions
- `src/actors/strategies/{attackers,defenders}/` — Python strategy classes
- `src/networks/library/` — JSON network definitions

---

## Developing Actions

Add a JSON file to the appropriate `src/actions/library/` subdirectory. Use existing actions as templates (e.g., `attacks/node/phishing.json`, `defenses/node/incident_response.json`).

### Precondition Types

All defined in `ConditionEvaluator` in `src/actions/json_conditions.py`.

| Type | Key fields | Meaning |
|---|---|---|
| `compound` | `operator` (`AND`/`OR`/`XOR`/`NAND`/`NOR`), `conditions` | Combine multiple conditions |
| `negation` | `condition` | Negate a condition |
| `implication` | `premise`, `conclusion` | If A then B |
| `access_check` | `operator`, `value` | Check actor's access level |
| `property_check` | `property`, `operator`, `value` | Check a node property |
| `vulnerability_check` | `cve`, `status` (opt) OR `check_type`, `operator`, `value` | Check CVE presence or vuln count |
| `software_check` | `software_key`, `operator`, + per-operator fields | Check software value/presence |
| `service_check` | `service`, `status` (opt, default `running`) | Check service state |
| `version_check` | `software_key`, `operator`, `value` | Compare software version |
| `assets_check` | `check_type` (opt), `operator`, `value` | Check asset count |
| `network_check` | `check_type` + type-specific fields | Check network-level context (port_access, neighbor_count, path_exists) |
| `time_check` | `property`, `operator`, `value` | Check time since a node property timestamp |
| `start_node_access_check` | `operator`, `value` | Link actions: check access on start node |
| `end_node_access_check` | `operator`, `value` | Link actions: check access on end node |
| `start_node_property_check` | `property`, `operator`, `value` | Link actions: check start node property |
| `end_node_property_check` | `property`, `operator`, `value` | Link actions: check end node property |
| `link_property_check` | `property`, `operator`, `value` | Link actions: check link property |
| `exists` | `variable`, `domain`, `formula` | Any element matches |
| `forall` | `variable`, `domain`, `formula` | All elements match |
| `variable_ref` | `variable`, `property`, `operator`, `value` | Compare a scoped variable's property |

### Postcondition Types

All defined in `ActionExecutor` in `src/actions/json_conditions.py`.

| Type | Key fields | Meaning |
|---|---|---|
| `compound` | `actions` | Execute multiple postconditions |
| `set_access` | `access_value` (or `value`) | Set the acting actor's access level |
| `set_access_if_none` | `access_value` (or `value`) | Set access only if currently `NONE` |
| `reduce_attacker_access` | `access_value` | Reduce all attackers' access (for defenses) |
| `set_property` | `property`, `value` | Set a node property |
| `modify_property` | `property`, `operation`, `value` | Arithmetic on a property (add/subtract/etc.) |
| `set_software` | `software_key`, `value` | Set software on node |
| `add_vulnerability` | `vulnerability` | Add a CVE to the node |
| `remove_vulnerability` | `vulnerability` | Remove a CVE from the node |
| `increment_counter` | `counter`, `increment` | Increment a numeric property |
| `set_links_access` | `access_value` | Set access on connected links |
| `set_access_neighbors` | `access_value` | Discover neighboring nodes |
| `clear_assets` | — | Remove all assets from node |
| `add_capability` | `capability` | Add a capability to node |
| `remove_capability` | `capability` | Remove a capability from node |

### Adding New Condition/Postcondition Types

Both are in `src/actions/json_conditions.py`:
- **New precondition:** Add an `elif` in `ConditionEvaluator.evaluate_condition()` and implement the check method.
- **New postcondition:** Add an `elif` in `ActionExecutor.execute_postcondition()` and implement the mutation method.

Both classes are singletons injected with a `Simulator` reference at startup, so they can access actors, network, and current time.

Attacks use `set_access` to raise *their own* access. Defenses use `reduce_attacker_access` to lower *all attackers'* access on a node.

Access levels (ascending): `NONE` → `VISIBLE` → `USER` → `ADMIN`. Attackers start at `VISIBLE` on internet-facing nodes; defenders start at `ADMIN` on all nodes.

---

## Developing Strategies

Create a Python file in `src/actors/strategies/attackers/` or `defenders/`. Implement one method: `get_priority()`.

### Attacker Strategy Template

`src/actors/strategies/attackers/my_strategy.py`:

```python
from src.actors.strategies.base import AttackerStrategy
from src.core.access_levels import NodeAccessLevel
from typing import Any

class MyStrategy(AttackerStrategy):
    """One-line description shown in GUI."""

    def get_priority(self, action: Any, node: Any, access: NodeAccessLevel, attacker: Any) -> float:
        """Higher = chosen first. Return -inf to skip."""
        return 1.0
```

### Defender Strategy Template

`src/actors/strategies/defenders/my_strategy.py`:

```python
from src.actors.strategies.base import DefenderStrategy
from typing import Any

class MyStrategy(DefenderStrategy):
    """One-line description shown in GUI."""

    def get_priority(self, action: Any, node: Any, detected_nodes: set[str] | None, network: Any) -> float:
        """Higher = chosen first. Return -inf to skip."""
        return 1.0
```

### How It Works

The base class `choose_action()` iterates all valid (action, target) pairs, calls your `get_priority()`, and picks the highest. Override `get_minimum_threshold(ongoing_count: int)` to set a floor below which actions are skipped.

**Useful attributes:**
- `actor.visible_nodes`, `actor.compromised_nodes`, `actor.visible_links`, `actor.compromised_links` (attacker)
- `actor.detected_attacks` (defender)
- `actor.budget`, `actor.capacity`, `actor.ongoing_actions`
- `action.cost`, `action.duration`, `action.success_probability`
- `self.get_mitre_tactic(action)` (attacker) / `self.get_d3fend_tactic(action)` (defender)
- `target.properties`, `target.vulnerabilities`, `target.assets`

---

## Simulator Core

### Event Loop (`src/core/simulator.py`)

Priority-queue loop processing events in time order:

1. `actor_run` — actor's strategy picks an action → schedules `start_action`
2. `start_action` — validates preconditions, schedules `action_finished` at `now + duration`
3. `action_finished` — re-checks preconditions, applies postconditions, records economics
4. `attack_detected` — detection engine fires, alerts defender via `on_attack_detected()`
5. `accumulate_time_proportional` — periodic time-proportional damage/gain tally

Action events (started/finished/succeeded/failed) are published to the `EventBus` (pub/sub in `src/core/events.py`). Internal scheduling events (`actor_run`, `accumulate_time_proportional`) are not published.

### Key Classes

| Class | File | Role |
|---|---|---|
| `Simulator` | `src/core/simulator.py` | Event loop, scheduling, handlers |
| `SimulationOrchestrator` | `src/core/simulation_orchestrator.py` | Configures and runs multiple simulation runs |
| `SimulationRunner` | `src/core/simulation_runner.py` | Multi-run + async wrapper |
| `EconomicModel` | `src/core/economic_model.py` | Tracks damage/gains/costs |
| `EventBus` | `src/core/events.py` | Pub/sub for simulation events |
| `Network` / `Node` / `Link` | `src/core/network.py` | Graph structure |
| `BaseDetectionEngine` | `src/detection/base_detection.py` | Abstract detection with CDF sampling |
| `Action` | `src/actions/action.py` | Wraps JSON into callable pre/postconditions |
| `AttackerStrategy` / `DefenderStrategy` | `src/actors/strategies/base.py` | ABC with `choose_action()` + `get_priority()` |

### Adding a Detection Engine

Add a `*_detection.py` file in `src/detection/`. Subclass `BaseDetectionEngine` and implement:
- `get_cdf_function(self, action)` → `Callable[[float], float]` — CDF over [0,1]
- `sample_inverse_cdf(self, u: float)` → `float` — inverse CDF sample
- `get_configuration_summary(self)` → `dict[str, Any]` — engine metadata

Engines are auto-discovered from `*_detection.py` files (no manual registration needed).

### Testing

```bash
make test                          # all tests
pytest tests/test_simulation.py -v # single file
```
