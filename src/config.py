import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path


def _get_env(key: str, default: str, cast_type: type = str):
    """Get environment variable with SIMTIM_ prefix."""
    env_key = f"SIMTIM_{key.upper()}"
    value = os.environ.get(env_key, default)
    if cast_type is bool:
        return value.lower() in ("true", "1", "yes", "on")
    if cast_type is float and value == "inf":
        return float("inf")
    return cast_type(value)


@dataclass
class SimConfig:
    default_detection_engine: str = field(
        default_factory=lambda: _get_env("DETECTION_ENGINE", "exponential")
    )
    default_sim_time: int = field(default_factory=lambda: _get_env("SIM_TIME", "72", int))
    default_sim_runs: int = field(default_factory=lambda: _get_env("SIM_RUNS", "1", int))
    log_level: str = field(default_factory=lambda: _get_env("LOG_LEVEL", "INFO"))
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    max_event_queue_size: int = field(
        default_factory=lambda: _get_env("MAX_EVENT_QUEUE_SIZE", "10000", int)
    )
    event_history_limit: int | None = None
    default_attacker_capacity: int = field(
        default_factory=lambda: _get_env("ATTACKER_CAPACITY", "3", int)
    )
    default_defender_capacity: int = field(
        default_factory=lambda: _get_env("DEFENDER_CAPACITY", "3", int)
    )
    default_budget: float = field(default_factory=lambda: _get_env("DEFAULT_BUDGET", "inf", float))
    damage_multiplier: float = field(
        default_factory=lambda: _get_env("DAMAGE_MULTIPLIER", "1.0", float)
    )
    gain_multiplier: float = field(
        default_factory=lambda: _get_env("GAIN_MULTIPLIER", "1.0", float)
    )


@dataclass
class PathConfig:
    actions_library: str = "src/actions/library"
    networks_library: str = "src/networks/library"
    attacks_dir: str = "attacks"
    defenses_dir: str = "defenses"
    output_dir: str = field(default_factory=lambda: _get_env("OUTPUT_DIR", "output"))
    plots_dir: str = field(default_factory=lambda: _get_env("PLOTS_DIR", "simulation_plots"))
    logs_dir: str = field(default_factory=lambda: _get_env("LOGS_DIR", "logs"))

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
    default_theme: str = field(default_factory=lambda: _get_env("GUI_THEME", "dark"))
    enable_animations: bool = True
    default_tab: str = "simulation"


# Global config instances
sim_config = SimConfig()
path_config = PathConfig()
detection_config = DetectionConfig()
gui_config = GUIConfig()


def load_config_from_file(filepath: str) -> dict:
    """Load configuration from JSON file."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {filepath}")

    with open(path) as f:
        return json.load(f)


def save_config_to_file(filepath: str) -> None:
    """Save current configuration to JSON file."""
    config = {
        "simulation": asdict(sim_config),
        "paths": asdict(path_config),
        "detection": asdict(detection_config),
        "gui": asdict(gui_config),
    }
    # Handle infinity serialization
    config["simulation"]["default_budget"] = (
        "inf"
        if config["simulation"]["default_budget"] == float("inf")
        else config["simulation"]["default_budget"]
    )

    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(config, f, indent=2)


def get_config_summary() -> dict:
    """Get a summary of all configuration values."""
    return {
        "simulation": asdict(sim_config),
        "paths": asdict(path_config),
        "detection": asdict(detection_config),
        "gui": asdict(gui_config),
    }
