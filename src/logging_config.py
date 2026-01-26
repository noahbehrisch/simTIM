import logging
import sys
from pathlib import Path

from src.config import path_config, sim_config


def setup_logging(
    log_file: str | None = None,
    log_level: str | None = None,
    json_format: bool = False,
) -> None:
    level = getattr(logging, (log_level or sim_config.log_level).upper())

    formatter: logging.Formatter
    if json_format:
        import json

        class JSONFormatter(logging.Formatter):
            def format(self, record):
                log_obj = {
                    "timestamp": self.formatTime(record),
                    "level": record.levelname,
                    "logger": record.name,
                    "message": record.getMessage(),
                    "module": record.module,
                    "function": record.funcName,
                    "line": record.lineno,
                }
                if hasattr(record, "sim_id"):
                    log_obj["sim_id"] = record.sim_id
                if record.exc_info:
                    log_obj["exception"] = self.formatException(record.exc_info)
                return json.dumps(log_obj)

        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(sim_config.log_format)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers.clear()

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    if log_file:
        log_path = Path(path_config.logs_dir) / log_file
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


simulation_logger = get_logger("simTIM.simulation")
network_logger = get_logger("simTIM.network")
action_logger = get_logger("simTIM.action")
detection_logger = get_logger("simTIM.detection")
