from .base import AttackerStrategy, DefenderStrategy
from .attackers.greedy import GreedyAttackerStrategy
from .attackers.random import RandomAttackerStrategy
from .defenders.reactive import ReactiveDefenderStrategy
from .defenders.proactive import ProactiveDefenderStrategy
from .defenders.monitoring import MonitoringDefenderStrategy

ATTACKER_STRATEGIES = {
    "greedy": GreedyAttackerStrategy,
    "random": RandomAttackerStrategy,
}
DEFENDER_STRATEGIES = {
    "reactive": ReactiveDefenderStrategy,
    "proactive": ProactiveDefenderStrategy,
    "monitoring": MonitoringDefenderStrategy,
}


def get_attacker_strategy(name: str) -> AttackerStrategy:
    strategy_class = ATTACKER_STRATEGIES.get(name, GreedyAttackerStrategy)
    return strategy_class()


def get_defender_strategy(name: str) -> DefenderStrategy:
    strategy_class = DEFENDER_STRATEGIES.get(name, ReactiveDefenderStrategy)
    return strategy_class()
