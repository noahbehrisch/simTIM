"""
Actor components for simTIM.

This module provides the actor classes (Attacker, Defender) and their
associated strategies for decision-making in the simulation.
"""

from .actor import Actor
from .attacker import Attacker
from .defender import Defender

__all__ = [
    'Actor',
    'Attacker',
    'Defender',
]
