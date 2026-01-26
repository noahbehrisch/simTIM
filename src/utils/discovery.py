import glob
import logging
import os

logger = logging.getLogger(__name__)


def get_src_path() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def discover_modules_in_directory(directory: str) -> list[str]:
    if not os.path.exists(directory):
        return []

    py_files = glob.glob(os.path.join(directory, "*.py"))
    modules = []
    for f in py_files:
        name = os.path.basename(f)[:-3]  # Remove .py
        if not name.startswith("_"):
            modules.append(name)
    return sorted(modules)


def list_available_strategies(strategy_type: str) -> list[str]:
    src_path = get_src_path()
    strategy_dir = os.path.join(src_path, "actors", "strategies", strategy_type)
    return discover_modules_in_directory(strategy_dir)


def list_attacker_strategies() -> list[str]:
    return list_available_strategies("attackers")


def list_defender_strategies() -> list[str]:
    return list_available_strategies("defenders")


def list_available_networks() -> list[str]:
    src_path = get_src_path()
    library_path = os.path.join(src_path, "networks", "library")

    if not os.path.exists(library_path):
        return []

    json_files = glob.glob(os.path.join(library_path, "*.json"))
    return sorted([os.path.basename(f) for f in json_files])


def list_available_detection_engines() -> list[str]:
    src_path = get_src_path()
    detection_dir = os.path.join(src_path, "detection")

    modules = discover_modules_in_directory(detection_dir)
    engines = []
    for mod in modules:
        if mod.endswith("_detection") and mod != "base_detection":
            engines.append(mod.replace("_detection", ""))
    return sorted(engines)


def list_available_actions(action_type: str) -> list[str]:
    src_path = get_src_path()
    action_dir = os.path.join(src_path, "actions", "library", action_type)

    if not os.path.exists(action_dir):
        return []

    json_files = []

    for item in os.listdir(action_dir):
        item_path = os.path.join(action_dir, item)

        if os.path.isdir(item_path):
            subdir_files = glob.glob(os.path.join(item_path, "*.json"))
            json_files.extend(subdir_files)
        elif item.endswith(".json"):
            json_files.append(item_path)

    return sorted([os.path.basename(f) for f in json_files])
