import glob
import importlib
import inspect
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


def get_src_path() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def discover_subclasses(
    directory: str,
    package_prefix: str,
    base_class: type,
    *,
    suffix: str = "",
    exclude: str = "",
    extract_defaults: bool = False,
) -> list[tuple[str, type, dict[str, Any]]]:
    if not os.path.exists(directory):
        return []

    glob_pattern = f"*{suffix}.py" if suffix else "*.py"
    pattern = os.path.join(directory, glob_pattern)
    results: list[tuple[str, type, dict[str, Any]]] = []

    for filepath in sorted(glob.glob(pattern)):
        module_name = os.path.basename(filepath)[:-3]
        if module_name.startswith("_") or module_name == exclude:
            continue

        fq_module = f"{package_prefix}.{module_name}"
        try:
            mod = importlib.import_module(fq_module)
        except Exception:
            logger.warning("Failed to import module %s", fq_module, exc_info=True)
            continue

        for attr_name in dir(mod):
            obj = getattr(mod, attr_name)
            if isinstance(obj, type) and issubclass(obj, base_class) and obj is not base_class:
                registry_name = module_name.removesuffix(suffix) if suffix else module_name

                default_params: dict[str, Any] = {}
                if extract_defaults:
                    sig = inspect.signature(obj.__init__)
                    for pname, param in sig.parameters.items():
                        if pname == "self":
                            continue
                        if param.default is not inspect.Parameter.empty:
                            default_params[pname] = param.default

                results.append((registry_name, obj, default_params))
                logger.debug(
                    "Discovered %s: %s -> %s", base_class.__name__, registry_name, obj.__name__
                )

    return results


def discover_modules_in_directory(directory: str) -> list[str]:
    if not os.path.exists(directory):
        return []

    py_files = glob.glob(os.path.join(directory, "*.py"))
    modules = []
    for f in py_files:
        name = os.path.basename(f)[:-3]
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
