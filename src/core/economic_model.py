from typing import Any


class SimpleEconomicModel:
    def __init__(self):
        self.total_damage = 0.0
        self.actor_gains: dict[str, float] = {}
        self.action_history: list[tuple[float, str, str, float, float]] = []
        self.time_proportional_damage = 0.0
        self.time_proportional_gains: dict[str, float] = {}
        self.last_accumulation_time = 0.0
        self._active_time_rates: list[tuple[float, float, str]] = []

    def record_damage(self, damage: float):
        self.total_damage += damage

    def record_gain(self, actor_id: str, gain: float):
        if actor_id not in self.actor_gains:
            self.actor_gains[actor_id] = 0.0
        self.actor_gains[actor_id] += gain

    def record_action_outcome(
        self,
        time: float,
        actor_id: str,
        action_name: str,
        damage: float = 0.0,
        gain: float = 0.0,
    ):
        if damage != 0:
            self.record_damage(damage)
        if gain > 0:
            self.record_gain(actor_id, gain)
        self.action_history.append((time, actor_id, action_name, damage, gain))

    def register_time_rate(self, actor_id: str, time_damage: float, time_gain: float):
        if time_damage != 0 or time_gain != 0:
            self._active_time_rates.append((time_damage, time_gain, actor_id))

    def accumulate_time_proportional_impact(self, current_time: float):
        if current_time <= self.last_accumulation_time:
            return
        delta_t = current_time - self.last_accumulation_time
        for damage_rate, gain_rate, actor_id in self._active_time_rates:
            if damage_rate != 0:
                time_damage = damage_rate * delta_t
                self.time_proportional_damage += time_damage
                self.total_damage += time_damage
            if gain_rate > 0:
                time_gain = gain_rate * delta_t
                if actor_id not in self.time_proportional_gains:
                    self.time_proportional_gains[actor_id] = 0.0
                self.time_proportional_gains[actor_id] += time_gain
                if actor_id not in self.actor_gains:
                    self.actor_gains[actor_id] = 0.0
                self.actor_gains[actor_id] += time_gain
        self.last_accumulation_time = current_time

    def get_attacker_objective(self, actor_id: str, actor_cost: float = 0.0) -> float:
        gains = self.actor_gains.get(actor_id, 0.0)
        return gains - actor_cost

    def get_defender_objective(self, actor_id: str, actor_cost: float = 0.0) -> float:
        return -(self.total_damage + actor_cost)

    def get_total_gains(self, actor_id: str | None = None) -> float:
        if actor_id:
            return self.actor_gains.get(actor_id, 0.0)
        return sum(self.actor_gains.values())

    def get_summary(self, actors: list | None = None) -> dict[str, Any]:
        total_costs = 0.0
        actor_costs = {}
        if actors:
            for actor in actors:
                actor_costs[actor.id] = actor.incurred_cost
                total_costs += actor.incurred_cost

        return {
            "total_damage": self.total_damage,
            "time_proportional_damage": self.time_proportional_damage,
            "one_off_damage": self.total_damage - self.time_proportional_damage,
            "total_costs": total_costs,
            "total_gains": self.get_total_gains(),
            "time_proportional_gains": dict(self.time_proportional_gains),
            "actor_costs": actor_costs,
            "actor_gains": dict(self.actor_gains),
            "num_actions": len(self.action_history),
        }
