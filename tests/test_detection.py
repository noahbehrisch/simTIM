"""Tests for detection engine CDF math and detection time sampling."""

import random

import pytest

from src.detection.early_weighted_detection import EarlyWeightedDetectionEngine
from src.detection.late_weighted_detection import LateWeightedDetectionEngine
from src.detection.uniform_detection import UniformDetectionEngine

# ── CDF boundary conditions ───────────────────────────────────────


class TestCDFBoundaries:
    """Every valid CDF must satisfy F(0)=0 and F(1)=1 (or close to it)."""

    @pytest.mark.parametrize(
        "engine",
        [
            EarlyWeightedDetectionEngine(exponent=2.0),
            LateWeightedDetectionEngine(exponent=2.0),
            UniformDetectionEngine(),
        ],
        ids=["early", "late", "uniform"],
    )
    def test_cdf_at_zero(self, engine):
        cdf = engine.get_cdf_function(None)
        assert cdf(0.0) == pytest.approx(0.0, abs=1e-10)

    @pytest.mark.parametrize(
        "engine",
        [
            EarlyWeightedDetectionEngine(exponent=2.0),
            LateWeightedDetectionEngine(exponent=2.0),
            UniformDetectionEngine(),
        ],
        ids=["early", "late", "uniform"],
    )
    def test_cdf_at_one(self, engine):
        cdf = engine.get_cdf_function(None)
        assert cdf(1.0) == pytest.approx(1.0, abs=1e-10)


# ── Monotonicity ──────────────────────────────────────────────────


class TestCDFMonotonicity:
    """CDFs must be non-decreasing."""

    @pytest.mark.parametrize(
        "engine",
        [
            EarlyWeightedDetectionEngine(exponent=2.0),
            LateWeightedDetectionEngine(exponent=2.0),
            UniformDetectionEngine(),
        ],
        ids=["early", "late", "uniform"],
    )
    def test_non_decreasing(self, engine):
        cdf = engine.get_cdf_function(None)
        prev = 0.0
        for t in [i / 100.0 for i in range(101)]:
            val = cdf(t)
            assert val >= prev - 1e-12, f"CDF decreased at t={t}: {val} < {prev}"
            prev = val


# ── Early-weighted specific ────────────────────────────────────────


class TestEarlyWeightedEngine:
    """F(t) = 1 - (1-t)^n"""

    def test_formula_n2(self):
        engine = EarlyWeightedDetectionEngine(exponent=2.0)
        cdf = engine.get_cdf_function(None)
        assert cdf(0.5) == pytest.approx(1.0 - (0.5) ** 2)  # 0.75
        assert cdf(0.25) == pytest.approx(1.0 - (0.75) ** 2)  # 0.4375

    def test_formula_n3(self):
        engine = EarlyWeightedDetectionEngine(exponent=3.0)
        cdf = engine.get_cdf_function(None)
        assert cdf(0.5) == pytest.approx(1.0 - (0.5) ** 3)  # 0.875

    def test_inverse_cdf_roundtrip(self):
        engine = EarlyWeightedDetectionEngine(exponent=2.0)
        cdf = engine.get_cdf_function(None)
        for u in [0.0, 0.1, 0.25, 0.5, 0.75, 0.9, 0.99]:
            t = engine.sample_inverse_cdf(u)
            assert cdf(t) == pytest.approx(u, abs=1e-10)

    def test_early_bias(self):
        """Early-weighted should have higher CDF values in [0, 0.5] than uniform."""
        early = EarlyWeightedDetectionEngine(exponent=2.0)
        early_cdf = early.get_cdf_function(None)
        # At t=0.3, early-weighted should be > 0.3 (uniform would be 0.3)
        assert early_cdf(0.3) > 0.3

    def test_exponent_floor_at_one(self):
        engine = EarlyWeightedDetectionEngine(exponent=0.5)  # should be clamped to 1.0
        assert engine.exponent == 1.0

    def test_validate_cdf(self):
        engine = EarlyWeightedDetectionEngine(exponent=2.0)
        cdf = engine.get_cdf_function(None)
        assert engine.validate_cdf(cdf) is True


# ── Late-weighted specific ─────────────────────────────────────────


class TestLateWeightedEngine:
    """F(t) = t^n"""

    def test_formula_n2(self):
        engine = LateWeightedDetectionEngine(exponent=2.0)
        cdf = engine.get_cdf_function(None)
        assert cdf(0.5) == pytest.approx(0.25)
        assert cdf(0.3) == pytest.approx(0.09)

    def test_inverse_cdf_roundtrip(self):
        engine = LateWeightedDetectionEngine(exponent=2.0)
        cdf = engine.get_cdf_function(None)
        for u in [0.0, 0.1, 0.25, 0.5, 0.75, 0.9, 0.99]:
            t = engine.sample_inverse_cdf(u)
            assert cdf(t) == pytest.approx(u, abs=1e-10)

    def test_late_bias(self):
        """Late-weighted should have lower CDF values in [0, 0.5] than uniform."""
        late = LateWeightedDetectionEngine(exponent=2.0)
        late_cdf = late.get_cdf_function(None)
        assert late_cdf(0.3) < 0.3

    def test_exponent_floor_at_one(self):
        engine = LateWeightedDetectionEngine(exponent=0.1)
        assert engine.exponent == 1.0


# ── Uniform specific ──────────────────────────────────────────────


class TestUniformEngine:
    """F(t) = t"""

    def test_identity(self):
        engine = UniformDetectionEngine()
        cdf = engine.get_cdf_function(None)
        for t in [0.0, 0.1, 0.5, 0.73, 1.0]:
            assert cdf(t) == pytest.approx(t)

    def test_inverse_is_identity(self):
        engine = UniformDetectionEngine()
        for u in [0.0, 0.25, 0.5, 0.99]:
            assert engine.sample_inverse_cdf(u) == pytest.approx(u)


# ── Detection time calculation ─────────────────────────────────────


class TestDetectionTimeCalculation:
    def test_returns_none_when_not_detected(self, make_action):
        """If random > detection_prob, no detection occurs."""
        engine = UniformDetectionEngine()
        action = make_action(detection_prob=0.0)
        node = type("N", (), {"access": {}, "properties": {}})()
        # detection_prob=0.0 means random.random() >= 0.0 is always True... wait
        # Actually 0.0 means random.random() >= 0.0 is always true, so never detected
        # Let's use monkeypatch
        result = engine.calculate_detection_time(action, node, None, None, duration=10.0)
        # With prob 0.0, random.random() (0 to 1) >= 0.0 is always True, so None
        assert result is None

    def test_detection_time_within_duration(self, make_action):
        """Detected action should have detection_time in [0, duration]."""
        random.seed(42)
        engine = UniformDetectionEngine()
        action = make_action(detection_prob=1.0)
        node = type("N", (), {"access": {}, "properties": {}})()
        detected_count = 0
        for _ in range(100):
            t = engine.calculate_detection_time(action, node, None, None, duration=10.0)
            if t is not None:
                assert 0.0 <= t <= 10.0
                detected_count += 1
        assert detected_count == 100  # prob=1.0 should always detect

    def test_detection_probability_respected(self, make_action):
        """With ~50% detection probability, roughly half should be detected."""
        random.seed(123)
        engine = UniformDetectionEngine()
        action = make_action(detection_prob=0.5)
        node = type("N", (), {"access": {}, "properties": {}})()
        results = [
            engine.calculate_detection_time(action, node, None, None, duration=10.0)
            for _ in range(1000)
        ]
        detected = sum(1 for r in results if r is not None)
        assert 400 < detected < 600  # ~50% ± reasonable margin


# ── Configuration summary ──────────────────────────────────────────


class TestConfigurationSummary:
    def test_early_weighted_summary(self):
        engine = EarlyWeightedDetectionEngine(exponent=3.0)
        summary = engine.get_configuration_summary()
        assert summary["engine_type"] == "EarlyWeightedDetection"
        assert summary["exponent"] == 3.0
        assert "cdf_formula" in summary

    def test_late_weighted_summary(self):
        engine = LateWeightedDetectionEngine(exponent=2.0)
        summary = engine.get_configuration_summary()
        assert summary["engine_type"] == "LateWeightedDetection"

    def test_uniform_summary(self):
        engine = UniformDetectionEngine()
        summary = engine.get_configuration_summary()
        assert summary["engine_type"] == "UniformDetection"
