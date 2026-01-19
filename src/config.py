from dataclasses import dataclass, field
from typing import Optional
import os


@dataclass
class SimConfig:
    default_detection_engine: str = "exponential"
    default_sim_time: int = 72
    default_sim_runs: int = 1
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    max_event_queue_size: int = 10000
    event_history_limit: Optional[int] = None
    default_attacker_capacity: int = 3
    default_defender_capacity: int = 3
    default_budget: float = float("inf")
    damage_multiplier: float = 1.0
    gain_multiplier: float = 1.0


@dataclass
class PathConfig:
    actions_library: str = "src/actions/library"
    networks_library: str = "src/networks/library"
    attacks_dir: str = "attacks"
    defenses_dir: str = "defenses"
    output_dir: str = "output"
    plots_dir: str = "simulation_plots"
    logs_dir: str = "logs"

    def get_attacks_path(self) -> str:
        return os.path.join(self.actions_library, self.attacks_dir)

    def get_defenses_path(self) -> str:
        return os.path.join(self.actions_library, self.defenses_dir)

    def ensure_output_dirs(self):
        for dir_path in [self.output_dir, self.plots_dir, self.logs_dir]:
            os.makedirs(dir_path, exist_ok=True)


@dataclass
class DetectionConfig:
    exponential_lambda: float = 2.0
    linear_slope: float = 1.0
    uniform_rate: float = 1.0
    cdf_tolerance: float = 0.02
    validate_cdf: bool = True


@dataclass
class GUIConfig:
    window_title: str = "simTIM - Temporal Information Management Simulator"
    min_window_width: int = 800
    min_window_height: int = 600
    default_theme: str = "dark"
    enable_animations: bool = True
    default_tab: str = "simulation"


sim_config = SimConfig()
path_config = PathConfig()
detection_config = DetectionConfig()
gui_config = GUIConfig()

# TODO: add config loading and saving


def load_config_from_file(filepath: str):
    pass


def save_config_to_file(filepath: str):
    pass
