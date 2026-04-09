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

## GUI

- Help windows: -> More descriptive and user-friendly

## Visualization

- seperation into different files for each plot for better modularity

## Network

- Adding new Node properties in the GUI
- mapping versions to vulnerabilities using jsons
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

- Multithreading with diables GIL or Multiprocessing -> one simulation per thread with its own instances (no global instances)

## Github

- securing main branch -> rulesets?
