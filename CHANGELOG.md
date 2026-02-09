# Changelog

All notable changes to simTIM will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.6.1] - 2026-01-29

### Added

- ROADMAP.md
- Progress Bar
- Simulation Runner with threads
- Grid in Network Creator canvas
- Network creator saves and loads coordinates
- Network creator canvas scrollable and zoomable
- Visualization Theme (colorblind friendly)

### Fixed

- Replaced access str with access level enums

## Changed

- simulation_main got refactored into simulation_orchestrator
- network visualizer now uses coordinates and unified color scheme

## [0.6.0] - 2026-01-26

### Added

- Makefile with linting, typechecking, and other development commands
- `pyproject.toml` for modern Python project configuration
- `pre-commit-config.yaml` for pre-commit hooks
- `dependabot.yaml` for automated dependency updates
- `requirements-dev.txt` for development dependencies
- README documentation
- Demo mode and CLI extension to `main.py`
- Logging system

### Fixed

- X-axis now maps to simulation time

### Changed

- Refactored codebase using design patterns
