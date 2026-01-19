# Core module exports
# Note: simulation_main is imported lazily to avoid circular imports with action modules
from .simulator import Simulator, Event
from .graph import Node, Link
from .access_levels import NodeAccessLevel, LinkAccessLevel
from .access_utils import (
    get_node_access,
    set_node_access,
    get_link_access,
    set_link_access,
)
from .economic_model import (
    economic_model,
    calculate_action_damage,
    calculate_action_gain,
)


def get_simtim_main():
    """Lazy import of simtim_main to avoid circular imports."""
    from .simulation_main import simtim_main

    return simtim_main


# For backward compatibility, try to import simtim_main but don't fail if circular
try:
    from .simulation_main import simtim_main
except ImportError:
    simtim_main = None  # Will be available via get_simtim_main()

__all__ = [
    "Simulator",
    "Event",
    "Node",
    "Link",
    "NodeAccessLevel",
    "LinkAccessLevel",
    "get_node_access",
    "set_node_access",
    "get_link_access",
    "set_link_access",
    "economic_model",
    "calculate_action_damage",
    "calculate_action_gain",
    "simtim_main",
    "get_simtim_main",
]
