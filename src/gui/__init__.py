"""
GUI module.

Provides the graphical user interface for simTIM.

Main Classes:
- App: Main application window
- Sidebar: Navigation sidebar
- ResultsWindow: Simulation results display
- HelpWindow: Help and documentation window
- Theme: UI theme configuration

Tabs:
- SimulationTab: Simulation configuration
- NetworkTab: Network visualization
- ActionTab: Action management
- AttackerTab: Attacker configuration
- DefenderTab: Defender configuration
- VariablesTab: Variable management
"""

from .app import App
from .help_window import HelpWindow, ToolTip
from .results_window import ResultsWindow
from .sidebar import Sidebar
from .theme import Theme

__all__ = [
    "App",
    "Sidebar",
    "ResultsWindow",
    "HelpWindow",
    "ToolTip",
    "Theme",
]
