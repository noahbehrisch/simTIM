"""
Centralized configuration management for simTIM.

This module provides configuration dataclasses for various aspects
of the simulation system.
"""

from dataclasses import dataclass, field
from typing import Optional
import os


@dataclass
class SimConfig:
    """Centralized simulation configuration."""
    
    # Default simulation parameters
    default_detection_engine: str = "exponential"
    default_sim_time: int = 10
    default_sim_runs: int = 1
    
    # Logging configuration
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Performance settings
    max_event_queue_size: int = 10000
    event_history_limit: Optional[int] = None  # None = unlimited
    
    # Actor settings
    default_attacker_capacity: int = 3
    default_defender_capacity: int = 3
    default_budget: float = float('inf')
    
    # Economic model settings
    damage_multiplier: float = 1.0
    gain_multiplier: float = 1.0
    

@dataclass
class PathConfig:
    """Path configurations for libraries and resources."""
    
    # Library paths (relative to project root)
    actions_library: str = "src/actions/library"
    networks_library: str = "src/networks/library"
    
    # Subdirectories
    attacks_dir: str = "attacks"
    defenses_dir: str = "defenses"
    
    # Output paths
    output_dir: str = "output"
    plots_dir: str = "simulation_plots"
    logs_dir: str = "logs"
    
    def get_attacks_path(self) -> str:
        """Get full path to attacks library."""
        return os.path.join(self.actions_library, self.attacks_dir)
    
    def get_defenses_path(self) -> str:
        """Get full path to defenses library."""
        return os.path.join(self.actions_library, self.defenses_dir)
    
    def ensure_output_dirs(self):
        """Create output directories if they don't exist."""
        for dir_path in [self.output_dir, self.plots_dir, self.logs_dir]:
            os.makedirs(dir_path, exist_ok=True)


@dataclass
class DetectionConfig:
    """Configuration for detection engines."""
    
    # Detection engine parameters
    exponential_lambda: float = 2.0  # Rate parameter for exponential detection
    linear_slope: float = 1.0  # Slope for linear detection
    uniform_rate: float = 1.0  # Rate for uniform detection
    
    # Detection validation
    cdf_tolerance: float = 0.02
    validate_cdf: bool = True


@dataclass
class GUIConfig:
    """GUI-related configuration."""
    
    # Window settings
    window_title: str = "simTIM - Temporal Information Management Simulator"
    min_window_width: int = 800
    min_window_height: int = 600
    
    # Theme settings
    default_theme: str = "dark"
    enable_animations: bool = True
    
    # Tab settings
    default_tab: str = "simulation"
    

# Global configuration instances
sim_config = SimConfig()
path_config = PathConfig()
detection_config = DetectionConfig()
gui_config = GUIConfig()


def load_config_from_file(filepath: str):
    """
    Load configuration from a JSON/YAML file.
    
    Args:
        filepath: Path to configuration file
        
    Note: This is a placeholder for future implementation.
    """
    # TODO: Implement configuration file loading
    pass


def save_config_to_file(filepath: str):
    """
    Save current configuration to a file.
    
    Args:
        filepath: Path to save configuration
        
    Note: This is a placeholder for future implementation.
    """
    # TODO: Implement configuration file saving
    pass
