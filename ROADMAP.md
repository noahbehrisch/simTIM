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

## Documentation

- User Documentation -> README.md and Help in the GUI suffices
- Developer Documenation -> Comments/Docstrings in tricky parts of the code, Document that explains the bigger pictures

## Core

- Better implementation of scenario comparison -> see simulation_orchestrator.py
- Simulation Behavior
- Different instances for every run -> check economic model especially

## GUI

- Help
- Enforcing the use of theme
- Colorblind friendly colors

## Visualization

- Path through network visualizer
- export visualizations

## Network

- Implement the ability to change node properties in the network creator
- Change Properties in the GUI
- mapping versions to vulnerabilities
- Make the canvas of the network creator scrollable and zoomable
- Dynamic Behavior
- saving network layout -> Coordinates of nodes -> 10 grid snap

## Software Architecture

- using and explaining design patterns where useful -> write clean code and refactor bad code

## Actions

- Modifiable Actions
- Action Creator
- Puzzling Actions together with properties

## Strategies

- unified priority system to build strategies more easily
- using the MITRE ATT&CK and D3EFEND matrizes

## Testing

- create a tests/ folder with tests for every part of the simulator
- more demo/test networks
- Test the app on different operating systems (Arch, Ubuntu, Windows, MacOS)
- Test compatibility of different versions (Python, Numpy, Matpotlib) -> already found a deepcopy compatability issue with Python 3.14 and an older matplotlib version

## Performance

- Multithreading with diables GIL or Multiprocessing -> one simulation per thread with its own instances (no global instances)
