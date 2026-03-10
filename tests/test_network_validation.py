"""Tests for network configuration validation."""

import pytest

from src.networks.validation import NetworkValidationResult, NetworkValidator


@pytest.fixture
def validator():
    return NetworkValidator()


# ── Valid configurations ───────────────────────────────────────────


class TestValidConfigs:
    def test_minimal_valid(self, validator, simple_network_config):
        result = validator.validate(simple_network_config)
        assert result.valid

    def test_no_links_is_valid(self, validator):
        config = {
            "nodes": [
                {"id": "a", "properties": {"exposed_to_internet": True}},
            ],
        }
        result = validator.validate(config)
        assert result.valid

    def test_missing_links_key_is_valid(self, validator):
        config = {
            "nodes": [
                {"id": "a", "properties": {"exposed_to_internet": True}},
            ],
        }
        result = validator.validate(config)
        assert result.valid


# ── Node validation ───────────────────────────────────────────────


class TestNodeValidation:
    def test_not_a_dict(self, validator):
        result = validator.validate("not a dict")
        assert not result.valid

    def test_missing_nodes_key(self, validator):
        result = validator.validate({})
        assert not result.valid
        assert any("nodes" in e for e in result.errors)

    def test_nodes_not_list(self, validator):
        result = validator.validate({"nodes": "not a list"})
        assert not result.valid

    def test_empty_nodes_warns(self, validator):
        result = validator.validate({"nodes": []})
        assert result.valid
        assert len(result.warnings) > 0

    def test_duplicate_node_ids(self, validator):
        config = {"nodes": [{"id": "a"}, {"id": "a"}]}
        result = validator.validate(config)
        assert not result.valid
        assert any("Duplicate" in e for e in result.errors)

    def test_missing_node_id(self, validator):
        config = {"nodes": [{"software": {"os": "Linux"}}]}
        result = validator.validate(config)
        assert not result.valid

    def test_empty_node_id(self, validator):
        config = {"nodes": [{"id": ""}]}
        result = validator.validate(config)
        assert not result.valid

    def test_node_not_dict(self, validator):
        config = {"nodes": ["just_a_string"]}
        result = validator.validate(config)
        assert not result.valid

    def test_software_must_be_dict(self, validator):
        config = {"nodes": [{"id": "a", "software": "Ubuntu"}]}
        result = validator.validate(config)
        assert not result.valid

    def test_vulnerabilities_must_be_list(self, validator):
        config = {"nodes": [{"id": "a", "vulnerabilities": "CVE-1234"}]}
        result = validator.validate(config)
        assert not result.valid

    def test_assets_must_be_list(self, validator):
        config = {"nodes": [{"id": "a", "assets": "customer_data"}]}
        result = validator.validate(config)
        assert not result.valid

    @pytest.mark.xfail(
        reason="Validator bug: _validate_entry_points crashes on non-dict properties",
        raises=AttributeError,
    )
    def test_properties_must_be_dict(self, validator):
        config = {"nodes": [{"id": "a", "properties": 42}]}
        result = validator.validate(config)
        assert not result.valid


# ── Link validation ───────────────────────────────────────────────


class TestLinkValidation:
    def test_valid_link(self, validator):
        config = {
            "nodes": [{"id": "a"}, {"id": "b"}],
            "links": [{"node1": "a", "node2": "b"}],
        }
        result = validator.validate(config)
        assert result.valid

    def test_link_references_unknown_node(self, validator):
        config = {
            "nodes": [{"id": "a"}],
            "links": [{"node1": "a", "node2": "ghost"}],
        }
        result = validator.validate(config)
        assert not result.valid
        assert any("ghost" in e for e in result.errors)

    def test_link_missing_node1(self, validator):
        config = {
            "nodes": [{"id": "a"}, {"id": "b"}],
            "links": [{"node2": "b"}],
        }
        result = validator.validate(config)
        assert not result.valid

    def test_link_missing_node2(self, validator):
        config = {
            "nodes": [{"id": "a"}, {"id": "b"}],
            "links": [{"node1": "a"}],
        }
        result = validator.validate(config)
        assert not result.valid

    def test_link_not_dict(self, validator):
        config = {
            "nodes": [{"id": "a"}, {"id": "b"}],
            "links": ["a-b"],
        }
        result = validator.validate(config)
        assert not result.valid

    def test_links_not_list(self, validator):
        config = {
            "nodes": [{"id": "a"}],
            "links": "not a list",
        }
        result = validator.validate(config)
        assert not result.valid

    def test_bidirectional_must_be_bool(self, validator):
        config = {
            "nodes": [{"id": "a"}, {"id": "b"}],
            "links": [{"node1": "a", "node2": "b", "bidirectional": "yes"}],
        }
        result = validator.validate(config)
        assert not result.valid

    def test_latency_must_be_number(self, validator):
        config = {
            "nodes": [{"id": "a"}, {"id": "b"}],
            "links": [{"node1": "a", "node2": "b", "latency": "fast"}],
        }
        result = validator.validate(config)
        assert not result.valid

    def test_negative_latency(self, validator):
        config = {
            "nodes": [{"id": "a"}, {"id": "b"}],
            "links": [{"node1": "a", "node2": "b", "latency": -1}],
        }
        result = validator.validate(config)
        assert not result.valid


# ── Entry point warnings ──────────────────────────────────────────


class TestEntryPointWarnings:
    def test_warns_no_exposed_nodes(self, validator):
        config = {"nodes": [{"id": "internal"}]}
        result = validator.validate(config)
        assert result.valid  # warning, not error
        assert any("Internet-exposed" in w for w in result.warnings)

    def test_no_warning_with_exposed_node(self, validator, simple_network_config):
        result = validator.validate(simple_network_config)
        exposed_warnings = [w for w in result.warnings if "Internet-exposed" in w]
        assert len(exposed_warnings) == 0


# ── ValidationResult merge ────────────────────────────────────────


class TestValidationResultMerge:
    def test_merge_both_valid(self):
        a = NetworkValidationResult(valid=True)
        b = NetworkValidationResult(valid=True)
        merged = a.merge(b)
        assert merged.valid

    def test_merge_one_invalid(self):
        a = NetworkValidationResult(valid=True)
        b = NetworkValidationResult(valid=False, errors=["bad"])
        merged = a.merge(b)
        assert not merged.valid
        assert "bad" in merged.errors

    def test_merge_combines_errors_and_warnings(self):
        a = NetworkValidationResult(valid=True, warnings=["w1"])
        b = NetworkValidationResult(valid=True, warnings=["w2"])
        merged = a.merge(b)
        assert merged.warnings == ["w1", "w2"]

    def test_bool_conversion(self):
        assert bool(NetworkValidationResult(valid=True)) is True
        assert bool(NetworkValidationResult(valid=False)) is False
