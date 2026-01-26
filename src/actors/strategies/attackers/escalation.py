from typing import Any

from src.actors.strategies.base import AttackerStrategy
from src.core.access_levels import NodeAccessLevel


class EscalationAttackerStrategy(AttackerStrategy):
    def __init__(self):
        super().__init__("escalation")

    def get_priority(self, action: Any, node: Any, access: Any, attacker: Any) -> float:
        tactic = self.get_mitre_tactic(action)
        priority = 1.0

        if isinstance(access, str):
            access = NodeAccessLevel.from_string(access)

        tactic_priorities = {
            "privilege-escalation": 500,
            "credential-access": 400,
            "initial-access": 300,
            "lateral-movement": 250,
            "execution": 200,
            "persistence": 150,
            "discovery": 100,
            "reconnaissance": 80,
            "defense-evasion": 60,
            "collection": 50,
            "exfiltration": 40,
            "command-and-control": 30,
            "impact": 20,
        }
        priority += tactic_priorities.get(tactic, 10)

        if access == NodeAccessLevel.VISIBLE:
            if tactic in ["initial-access", "reconnaissance"]:
                priority += 200
        elif access == NodeAccessLevel.USER:
            if tactic == "privilege-escalation":
                priority += 300
            elif tactic == "credential-access":
                priority += 200

        priority += len(node.assets) * 5

        return priority
