"""Tests for the TIM economic model."""

import pytest

from src.core.economic_model import SimpleEconomicModel


class TestRecordDamage:
    def test_initial_state_zero(self):
        model = SimpleEconomicModel()
        assert model.total_damage == 0.0

    def test_single_damage(self):
        model = SimpleEconomicModel()
        model.record_damage(500.0)
        assert model.total_damage == 500.0

    def test_cumulative_damage(self):
        model = SimpleEconomicModel()
        model.record_damage(100.0)
        model.record_damage(250.0)
        assert model.total_damage == 350.0

    def test_zero_damage_is_noop(self):
        model = SimpleEconomicModel()
        model.record_damage(0.0)
        assert model.total_damage == 0.0


class TestRecordGain:
    def test_single_actor_gain(self):
        model = SimpleEconomicModel()
        model.record_gain("attacker1", 1000.0)
        assert model.actor_gains["attacker1"] == 1000.0

    def test_cumulative_gain(self):
        model = SimpleEconomicModel()
        model.record_gain("attacker1", 500.0)
        model.record_gain("attacker1", 300.0)
        assert model.actor_gains["attacker1"] == 800.0

    def test_multiple_actors(self):
        model = SimpleEconomicModel()
        model.record_gain("attacker1", 500.0)
        model.record_gain("attacker2", 300.0)
        assert model.actor_gains["attacker1"] == 500.0
        assert model.actor_gains["attacker2"] == 300.0


class TestRecordActionOutcome:
    def test_records_damage_and_gain(self):
        model = SimpleEconomicModel()
        model.record_action_outcome(10.0, "attacker1", "phishing", damage=300.0, gain=500.0)
        assert model.total_damage == 300.0
        assert model.actor_gains["attacker1"] == 500.0

    def test_records_history_entry(self):
        model = SimpleEconomicModel()
        model.record_action_outcome(10.0, "attacker1", "phishing", damage=300.0, gain=500.0)
        assert len(model.action_history) == 1
        time, actor, action, damage, gain = model.action_history[0]
        assert time == 10.0
        assert actor == "attacker1"
        assert action == "phishing"

    def test_zero_damage_skips_record(self):
        model = SimpleEconomicModel()
        model.record_action_outcome(5.0, "defender1", "patch", damage=0.0, gain=0.0)
        assert model.total_damage == 0.0
        assert len(model.actor_gains) == 0

    def test_negative_gain_skips_record(self):
        model = SimpleEconomicModel()
        model.record_action_outcome(5.0, "attacker1", "fail", damage=0.0, gain=-100.0)
        assert "attacker1" not in model.actor_gains


class TestTimeProportionalImpact:
    def test_single_rate_accumulation(self):
        model = SimpleEconomicModel()
        model.register_time_rate("attacker1", time_damage=10.0, time_gain=5.0)
        model.accumulate_time_proportional_impact(1.0)  # delta_t = 1.0
        assert model.time_proportional_damage == pytest.approx(10.0)
        assert model.total_damage == pytest.approx(10.0)
        assert model.actor_gains["attacker1"] == pytest.approx(5.0)

    def test_multiple_accumulations(self):
        model = SimpleEconomicModel()
        model.register_time_rate("attacker1", time_damage=10.0, time_gain=5.0)
        model.accumulate_time_proportional_impact(1.0)
        model.accumulate_time_proportional_impact(3.0)  # delta_t = 2.0
        assert model.time_proportional_damage == pytest.approx(30.0)  # 10*1 + 10*2
        assert model.total_damage == pytest.approx(30.0)
        assert model.actor_gains["attacker1"] == pytest.approx(15.0)

    def test_no_backward_accumulation(self):
        model = SimpleEconomicModel()
        model.register_time_rate("attacker1", time_damage=10.0, time_gain=5.0)
        model.accumulate_time_proportional_impact(5.0)
        damage_at_5 = model.total_damage
        model.accumulate_time_proportional_impact(3.0)  # earlier time, should be ignored
        assert model.total_damage == damage_at_5

    def test_zero_rates_not_registered(self):
        model = SimpleEconomicModel()
        model.register_time_rate("attacker1", time_damage=0.0, time_gain=0.0)
        assert len(model._active_time_rates) == 0

    def test_multiple_rates_stack(self):
        model = SimpleEconomicModel()
        model.register_time_rate("attacker1", time_damage=10.0, time_gain=5.0)
        model.register_time_rate("attacker1", time_damage=20.0, time_gain=10.0)
        model.accumulate_time_proportional_impact(1.0)
        assert model.time_proportional_damage == pytest.approx(30.0)
        assert model.actor_gains["attacker1"] == pytest.approx(15.0)

    def test_mixed_one_off_and_time_proportional(self):
        model = SimpleEconomicModel()
        model.record_damage(100.0)
        model.register_time_rate("attacker1", time_damage=10.0, time_gain=0.0)
        model.accumulate_time_proportional_impact(5.0)
        assert model.total_damage == pytest.approx(150.0)  # 100 + 10*5
        assert model.time_proportional_damage == pytest.approx(50.0)


class TestObjectiveFunctions:
    def test_attacker_objective_gains_minus_cost(self):
        model = SimpleEconomicModel()
        model.record_gain("attacker1", 1000.0)
        assert model.get_attacker_objective("attacker1", actor_cost=300.0) == pytest.approx(700.0)

    def test_attacker_objective_unknown_actor(self):
        model = SimpleEconomicModel()
        assert model.get_attacker_objective("nobody", actor_cost=100.0) == pytest.approx(-100.0)

    def test_defender_objective_negative_damage_plus_cost(self):
        model = SimpleEconomicModel()
        model.record_damage(500.0)
        assert model.get_defender_objective("defender1", actor_cost=200.0) == pytest.approx(-700.0)

    def test_defender_objective_no_damage(self):
        model = SimpleEconomicModel()
        assert model.get_defender_objective("defender1", actor_cost=0.0) == pytest.approx(0.0)


class TestGetTotalGains:
    def test_specific_actor(self):
        model = SimpleEconomicModel()
        model.record_gain("attacker1", 500.0)
        model.record_gain("attacker2", 300.0)
        assert model.get_total_gains("attacker1") == pytest.approx(500.0)

    def test_all_actors(self):
        model = SimpleEconomicModel()
        model.record_gain("attacker1", 500.0)
        model.record_gain("attacker2", 300.0)
        assert model.get_total_gains() == pytest.approx(800.0)

    def test_unknown_actor_returns_zero(self):
        model = SimpleEconomicModel()
        assert model.get_total_gains("nobody") == 0.0


class TestGetSummary:
    def test_summary_keys(self):
        model = SimpleEconomicModel()
        summary = model.get_summary()
        expected_keys = {
            "total_damage",
            "time_proportional_damage",
            "one_off_damage",
            "total_costs",
            "total_gains",
            "time_proportional_gains",
            "actor_costs",
            "actor_gains",
            "num_actions",
        }
        assert set(summary.keys()) == expected_keys

    def test_one_off_damage_calculation(self):
        model = SimpleEconomicModel()
        model.record_damage(100.0)  # one-off
        model.register_time_rate("a", time_damage=10.0, time_gain=0.0)
        model.accumulate_time_proportional_impact(5.0)
        summary = model.get_summary()
        assert summary["one_off_damage"] == pytest.approx(100.0)
        assert summary["time_proportional_damage"] == pytest.approx(50.0)
        assert summary["total_damage"] == pytest.approx(150.0)
