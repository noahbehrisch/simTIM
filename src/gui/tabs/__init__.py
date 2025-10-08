"""
GUI Tabs Package

Contains modular tab implementations for the GUI.
"""

from .base_tab import BaseTab
from .simulation_tab import SimulationTab
from .network_tab import NetworkTab
from .attacker_tab import AttackerTab  
from .defender_tab import DefenderTab

__all__ = [
    'BaseTab',
    'SimulationTab',
    'NetworkTab', 
    'AttackerTab',
    'DefenderTab'
]
