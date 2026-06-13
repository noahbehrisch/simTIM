"""Tests for ActionLoader, NetworkLoader, and discovery utilities."""

import json
import os

import pytest

from src.actions.action_factory import ActionFactory
from src.actions.action_loader import ActionLoader, ActionLoadError
from src.actions.action_registry import ActionRegistry
from src.networks.factory import NetworkFactory
from src.networks.network_loader import NetworkLoader, NetworkLoadError
from src.utils.discovery import (
    discover_modules_in_directory,
    list_attacker_strategies,
    list_available_actions,
    list_available_detection_engines,
    list_available_networks,
    list_defender_strategies,
)

# ── Helpers ───────────────────────────────────────────────────────

VALID_ACTION_JSON = {
    "name": "Test Action",
    "action_type": "node",
    "cost": 10,
    "duration": 1.0,
    "success_probability": 0.5,
    "precondition": {"type": "constant", "value": True},
    "postcondition": {"type": "constant", "value": True},
    "detection_probability": {"type": "constant", "value": 0.1},
    "damage_gain": {
        "one_off_damage": 0.0,
        "one_off_gain": 0.0,
        "time_damage": 0.0,
        "time_gain": 0.0,
    },
}


# ── ActionLoader ───────────────────────────────────────────────────


class TestActionLoader:
    def setup_method(self):
        self.loader = ActionLoader()

    def test_default_library_path(self):
        assert os.path.isdir(self.loader.library_path)

    def test_factory_property(self):
        assert isinstance(self.loader.factory, ActionFactory)

    def test_load_from_file(self, tmp_path):
        action_file = tmp_path / "test_action.json"
        action_file.write_text(json.dumps(VALID_ACTION_JSON))
        action = self.loader.load_from_file(str(action_file))
        assert action.name == "Test Action"

    def test_load_from_file_invalid_json(self, tmp_path):
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("not json {{{")
        with pytest.raises(ActionLoadError):
            self.loader.load_from_file(str(bad_file))

    def test_load_from_file_invalid_action(self, tmp_path):
        bad_file = tmp_path / "bad_action.json"
        bad_file.write_text(json.dumps({"name": "incomplete"}))
        with pytest.raises(ActionLoadError):
            self.loader.load_from_file(str(bad_file))

    def test_load_from_directory(self, tmp_path):
        for i in range(3):
            data = {**VALID_ACTION_JSON, "name": f"Action {i}"}
            (tmp_path / f"action_{i}.json").write_text(json.dumps(data))
        actions = self.loader.load_from_directory(str(tmp_path))
        assert len(actions) == 3

    def test_load_from_directory_nonexistent(self):
        actions = self.loader.load_from_directory("/nonexistent/path")
        assert actions == []

    def test_load_from_directory_with_bad_file(self, tmp_path):
        (tmp_path / "good.json").write_text(json.dumps(VALID_ACTION_JSON))
        (tmp_path / "bad.json").write_text("not json")
        actions = self.loader.load_from_directory(str(tmp_path))
        assert len(actions) == 1  # only the good one

    def test_load_from_directory_recursive(self, tmp_path):
        sub = tmp_path / "subdir"
        sub.mkdir()
        (sub / "nested.json").write_text(json.dumps(VALID_ACTION_JSON))
        actions = self.loader.load_from_directory(str(tmp_path), recursive=True)
        assert len(actions) == 1

    def test_load_attacks(self):
        attacks = self.loader.load_attacks()
        assert isinstance(attacks, list)

    def test_load_defenses(self):
        defenses = self.loader.load_defenses()
        assert isinstance(defenses, list)

    def test_load_all(self):
        all_actions = self.loader.load_all()
        assert "attack" in all_actions
        assert "defense" in all_actions

    def test_load_into_registry(self):
        reg = ActionRegistry()
        count = self.loader.load_into_registry(reg)
        assert count >= 0
        assert len(reg) == count

    def test_save_to_file(self, tmp_path):
        data = {**VALID_ACTION_JSON}
        action = self.loader.factory.create(data)
        out_path = str(tmp_path / "saved.json")
        self.loader.save_to_file(action, out_path)
        assert os.path.exists(out_path)
        with open(out_path) as f:
            saved = json.load(f)
        assert saved["name"] == "Test Action"

    def test_save_many(self, tmp_path):
        actions = []
        for i in range(2):
            data = {**VALID_ACTION_JSON, "name": f"Action {i}"}
            actions.append(self.loader.factory.create(data))
        out_dir = str(tmp_path / "batch")
        count = self.loader.save_many(actions, out_dir)
        assert count == 2
        assert len(os.listdir(out_dir)) == 2

    def test_name_to_filename(self):
        assert self.loader._name_to_filename("Remote Exploit") == "remote_exploit.json"
        assert self.loader._name_to_filename("Brute-Force") == "brute_force.json"

    def test_list_available(self):
        available = self.loader.list_available()
        assert "attacks" in available
        assert "defenses" in available

    def test_save_and_load_bundle(self, tmp_path):
        data1 = {**VALID_ACTION_JSON, "name": "Attack1"}
        data2 = {**VALID_ACTION_JSON, "name": "Defense1"}
        a1 = self.loader.factory.create(data1)
        d1 = self.loader.factory.create(data2)

        bundle_path = str(tmp_path / "bundle.json")
        self.loader.save_as_bundle({"attack": [a1], "defense": [d1]}, bundle_path)
        assert os.path.exists(bundle_path)

        loaded = self.loader.load_from_bundle(bundle_path)
        assert "attack" in loaded
        assert len(loaded["attack"]) == 1


# ── ActionLoadError ────────────────────────────────────────────────


class TestActionLoadError:
    def test_str(self):
        e = ActionLoadError("/path/to/file.json", "bad format")
        assert "/path/to/file.json" in str(e)
        assert "bad format" in str(e)

    def test_with_cause(self):
        cause = ValueError("inner")
        e = ActionLoadError("/path", "msg", cause)
        assert e.cause is cause


# ── NetworkLoader ──────────────────────────────────────────────────


class TestNetworkLoader:
    def setup_method(self):
        self.loader = NetworkLoader()

    def test_factory_property(self):
        assert isinstance(self.loader.factory, NetworkFactory)

    def test_library_path(self):
        assert isinstance(self.loader.library_path, str)

    def test_list_available(self):
        available = self.loader.list_available()
        assert isinstance(available, list)

    def test_resolve_absolute_path(self):
        assert self.loader.resolve_path("/absolute/path") == "/absolute/path"

    def test_find_in_library_not_found(self):
        with pytest.raises(FileNotFoundError):
            self.loader.find_in_library("nonexistent_network")

    def test_load_config_file_not_found(self):
        with pytest.raises(NetworkLoadError):
            self.loader.load_config("/nonexistent/network.json")

    def test_load_config_invalid_json(self, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text("not json {{")
        with pytest.raises(NetworkLoadError):
            self.loader.load_config(str(bad))

    def test_load_config_unsupported_format(self, tmp_path):
        txt = tmp_path / "net.yaml"
        txt.write_text("nodes: []")
        with pytest.raises(NetworkLoadError):
            self.loader.load_config(str(txt))

    def test_load_and_save(self, tmp_path):
        config = {
            "nodes": [
                {"id": "n1", "software": {"os": "Linux"}},
                {"id": "n2", "software": {"os": "Linux"}},
            ],
            "links": [{"node1": "n1", "node2": "n2"}],
        }
        config_path = tmp_path / "net.json"
        config_path.write_text(json.dumps(config))

        net = self.loader.load(str(config_path))
        assert net.node_count == 2

        save_path = str(tmp_path / "saved_net.json")
        self.loader.save(net, save_path)
        assert os.path.exists(save_path)

    def test_load_config_valid(self, tmp_path):
        config = {
            "nodes": [{"id": "n1", "software": {"os": "Linux"}}],
            "links": [],
        }
        config_path = tmp_path / "net.json"
        config_path.write_text(json.dumps(config))
        loaded = self.loader.load_config(str(config_path))
        assert loaded["nodes"][0]["id"] == "n1"

    def test_load_config_validation_failure(self, tmp_path):
        config = {"links": []}  # missing nodes
        config_path = tmp_path / "bad_net.json"
        config_path.write_text(json.dumps(config))
        with pytest.raises(NetworkLoadError):
            self.loader.load_config(str(config_path))


# ── NetworkLoadError ───────────────────────────────────────────────


class TestNetworkLoadError:
    def test_str(self):
        e = NetworkLoadError("network not found", path="/path")
        assert "network not found" in str(e)
        assert e.path == "/path"

    def test_with_cause(self):
        cause = ValueError("inner")
        e = NetworkLoadError("msg", cause=cause)
        assert e.cause is cause


# ── Discovery utilities ────────────────────────────────────────────


class TestDiscovery:
    def test_discover_modules_in_directory(self, tmp_path):
        (tmp_path / "module_a.py").write_text("# module a")
        (tmp_path / "module_b.py").write_text("# module b")
        (tmp_path / "__init__.py").write_text("")  # should be excluded
        modules = discover_modules_in_directory(str(tmp_path))
        assert "module_a" in modules
        assert "module_b" in modules
        assert "__init__" not in modules

    def test_discover_modules_nonexistent(self):
        modules = discover_modules_in_directory("/nonexistent")
        assert modules == []

    def test_list_attacker_strategies(self):
        strategies = list_attacker_strategies()
        assert isinstance(strategies, list)
        assert len(strategies) > 0

    def test_list_defender_strategies(self):
        strategies = list_defender_strategies()
        assert isinstance(strategies, list)
        assert len(strategies) > 0

    def test_list_available_networks(self):
        networks = list_available_networks()
        assert isinstance(networks, list)

    def test_list_available_detection_engines(self):
        engines = list_available_detection_engines()
        assert isinstance(engines, list)
        assert len(engines) > 0

    def test_list_available_actions_attacks(self):
        actions = list_available_actions("attacks")
        assert isinstance(actions, list)

    def test_list_available_actions_defenses(self):
        actions = list_available_actions("defenses")
        assert isinstance(actions, list)

    def test_list_available_actions_nonexistent(self):
        actions = list_available_actions("nonexistent_type")
        assert actions == []
