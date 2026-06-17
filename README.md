# simTIM

This repository contains the code corresponding to the following paper:
Noah Niclas Behrisch, Zoltán Ádám Mann. SimTIM: A Temporal Cybersecurity Simulator. 21st International Conference on Availability, Reliability and Security (ARES), 2026

## Quick Start

### Prerequisites

- Python 3.10+
- pip
- make

### Installation

```bash
# Clone the repository
git clone https://github.com/noahbehrisch/simTIM.git

# Install core dependencies (creates venv automatically)
make install

# Or install development dependencies (includes testing, linting tools)
make install-dev
```

### Running the GUI

```bash
make run
```

### Running a Demo

```bash
make demo
```

## Available Make Commands

Run `make help` to see all available commands:

| Command | Description |
|---------|-------------|
| `make install` | Install production dependencies |
| `make install-dev` | Install development dependencies |
| `make run` | Run the GUI application |
| `make demo` | Run demo simulation |
| `make test` | Run tests |
| `make test-cov` | Run tests with coverage report |
| `make lint` | Run linting checks |
| `make format` | Format code with ruff |

**Windows users**: If you don't have `make`, see the [Makefile](Makefile) for the underlying commands, or use WSL.

## Running Tests

```bash
# Run all tests
make test

# Run tests with coverage report
make test-cov
```

## Code Quality

```bash
# Run linting
make lint

# Format code
make format

# Type checking
make type-check
```

## Acknowledgments

Based on the paper "Time is money: A temporal model of cybersecurity" by Zoltán Ádám Mann.
