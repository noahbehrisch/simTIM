import logging
from collections.abc import Callable
from typing import Any

from src.actions.action_manager import action_manager
from src.actors.attacker import Attacker
from src.actors.defender import Defender
from src.config import sim_config
from src.core.access_levels import LinkAccessLevel, NodeAccessLevel
from src.core.economic_model import SimpleEconomicModel
from src.core.simulator import Simulator
from src.networks import NetworkLoader

logger = logging.getLogger(__name__)
_network_loader = NetworkLoader()


class SimulationOrchestrator:
    """
    Called by SimulationRunner. Sets up config, actors, network, then runs Simulator.
    """

    def __init__(
        self,
        path_to_network_config: str,
        attackers: list[dict[str, Any]],
        defenders: list[dict[str, Any]],
        sim_time: int | None = None,
        sim_runs: int | None = None,
        detection_engine_type: str | None = None,
        action_duration_override: float | None = None,
        attack_duration_override: float | None = None,
        defense_duration_override: float | None = None,
        progress_callback: Callable[[int, int], None] | None = None,
        enabled_actions: dict[str, list[str]] | None = None,
    ):
        self.path_to_network_config = path_to_network_config
        self.attackers_config = attackers
        self.defenders_config = defenders
        self.sim_time = sim_time if sim_time is not None else sim_config.default_sim_time
        self.sim_runs = sim_runs if sim_runs is not None else sim_config.default_sim_runs
        self.detection_engine_type = detection_engine_type or sim_config.default_detection_engine
        self.action_duration_override = action_duration_override
        self.attack_duration_override = attack_duration_override
        self.defense_duration_override = defense_duration_override
        self.progress_callback = progress_callback
        self.enabled_actions = enabled_actions

    def run(self) -> list[list] | None:
        if not self._validate():
            return None

        if self.action_duration_override is not None:
            logger.info(f"All actions will use duration: {self.action_duration_override} hours")

        all_histories = []

        for run in range(self.sim_runs):
            if self.progress_callback:
                self.progress_callback(run + 1, self.sim_runs)
            logger.info(f"Running simulation {run + 1}/{self.sim_runs}")

            network = _network_loader.load(self.path_to_network_config)
            attack_actions, defense_actions = self._load_actions()
            economic_model = SimpleEconomicModel()

            simulator = Simulator(
                network,
                detection_engine_type=self.detection_engine_type,
                economic_model_instance=economic_model,
            )

            attacker_objs = self._create_attackers(attack_actions)
            self._init_attacker_access(attacker_objs, network)

            defender_objs = self._create_defenders(defense_actions)
            simulator.actors = list(attacker_objs) + list(defender_objs)
            self._init_defender_access(defender_objs, network)

            simulator.network = network
            simulator.run(until=self.sim_time)

            history_tuples = self._extract_history(simulator)
            all_histories.append(history_tuples)

            logger.info(f"Simulation run {run + 1} completed with {len(history_tuples)} events")
            if run + 1 < self.sim_runs:
                logger.debug("Preparing next simulation run...")
            else:
                logger.debug("Final network state:")
                for n in network.nodes_list:
                    logger.debug(str(n))

        logger.info(f"All {self.sim_runs} simulation runs completed")
        return all_histories

    def _validate(self) -> bool:
        if not self.path_to_network_config:
            logger.error("No network configuration file provided")
            return False
        if not self.attackers_config or len(self.attackers_config) == 0:
            logger.error("No attackers specified")
            return False
        if not self.defenders_config or len(self.defenders_config) == 0:
            logger.info("No defenders specified — running attacker-only simulation")
        if self.sim_time is None:
            logger.error("Simulation end time not provided")
            return False
        if not self.sim_runs or self.sim_runs < 1:
            self.sim_runs = 1
        return True

    def _load_actions(self):
        attack_actions = action_manager.get_attack_actions()
        defense_actions = action_manager.get_defense_actions()

        if self.enabled_actions is not None:
            enabled_attacks = self.enabled_actions.get("attack_actions")
            enabled_defenses = self.enabled_actions.get("defense_actions")
            if enabled_attacks is not None:
                attack_actions = [a for a in attack_actions if a.name in enabled_attacks]
            if enabled_defenses is not None:
                defense_actions = [a for a in defense_actions if a.name in enabled_defenses]

        if self.action_duration_override is not None:
            for action in attack_actions:
                action.duration = self.action_duration_override
            for action in defense_actions:
                action.duration = self.action_duration_override
        if self.attack_duration_override is not None:
            for action in attack_actions:
                action.duration = self.attack_duration_override
        if self.defense_duration_override is not None:
            for action in defense_actions:
                action.duration = self.defense_duration_override

        return attack_actions, defense_actions

    def _create_attackers(self, attack_actions) -> list[Attacker]:
        attacker_objs = []
        for i, config in enumerate(self.attackers_config):
            attacker = Attacker(
                id=config.get("id", f"attacker_{i}"),
                strategy=config.get("strategy", "random"),
                capacity=config.get("capacity", 3),
                budget=float(config.get("budget", 1000)),
            )
            attacker.available_actions = attack_actions
            attacker_objs.append(attacker)
        return attacker_objs

    def _init_attacker_access(self, attackers: list[Attacker], network) -> None:
        for attacker in attackers:
            for node in network.nodes_list:
                if node.properties.get("exposed_to_internet", False):
                    node.access[attacker.id] = NodeAccessLevel.VISIBLE
                    attacker.visible_nodes.add(node)
                else:
                    node.access[attacker.id] = NodeAccessLevel.NONE
            for link in network.links_list:
                link.access[attacker.id] = LinkAccessLevel.NONE

        for attacker in attackers:
            if not attacker.visible_nodes:
                logger.warning(
                    f"{attacker.id} has no visible nodes - no entry points in network! "
                    f"The simulation will run but this attacker will have no initial access. "
                    f'Ensure at least one node has "exposed_to_internet": true.'
                )

    def _create_defenders(self, defense_actions) -> list[Defender]:
        defender_objs = []
        for i, config in enumerate(self.defenders_config or []):
            defender = Defender(
                id=config.get("id", f"defender_{i}"),
                strategy=config.get("strategy", "reactive"),
                capacity=config.get("capacity", 1),
                budget=float(config.get("budget", 1000)),
            )
            defender.available_actions = defense_actions
            defender_objs.append(defender)
        return defender_objs

    def _init_defender_access(self, defenders: list[Defender], network) -> None:
        for defender in defenders:
            for node in network.nodes_list:
                node.access[defender.id] = NodeAccessLevel.ADMIN
                defender.visible_nodes.add(node)
            for link in network.links_list:
                link.access[defender.id] = LinkAccessLevel.VISIBLE
                defender.visible_links.add(link)

    def _extract_history(self, simulator: Simulator) -> list:
        history_tuples = []
        for event in simulator.history:
            if hasattr(event, "time"):
                history_tuples.append((event.time, event.event_type, event.data))
            else:
                history_tuples.append(event)
        return history_tuples


def run_variable_scenarios(
    path_to_network_config: str,
    scenarios: list,
    variable_type: str = "action_duration",
    attackers: list | None = None,
    defenders: list | None = None,
    sim_time: int = 10,
    detection_engine_type: str = "early_weighted",
    progress_callback: Callable[[int, int], None] | None = None,
    enabled_actions: dict[str, list[str]] | None = None,
):
    if variable_type == "attack_duration":
        comparison_label = "attack action durations"
    elif variable_type == "defense_duration":
        comparison_label = "defense action durations"
    elif variable_type == "attacker_strategy":
        comparison_label = "attacker strategies"
    elif variable_type == "defender_strategy":
        comparison_label = "defender strategies"
    else:
        comparison_label = "parameters"

    logger.info(f"{'=' * 60}")
    logger.info("SCENARIO COMPARISON MODE")
    logger.info(f"Running {len(scenarios)} scenarios with different {comparison_label}")
    logger.info(f"{'=' * 60}")
    results: dict[str, Any] = {"scenarios": [], "variable_type": variable_type}

    total_runs = sum(s.get("runs", 1) for s in scenarios)
    completed_runs = 0

    for scenario_idx, scenario in enumerate(scenarios, 1):
        runs = scenario["runs"]
        action_duration_override = None
        attack_duration_override = None
        defense_duration_override = None
        scenario_attackers = attackers
        scenario_defenders = defenders

        if variable_type == "attack_duration":
            value = scenario["duration"]
            value_label = f"Attack Duration: {value} hours"
            attack_duration_override = value
        elif variable_type == "defense_duration":
            value = scenario["duration"]
            value_label = f"Defense Duration: {value} hours"
            defense_duration_override = value
        elif variable_type == "attacker_strategy":
            value = scenario["strategy"]
            value_label = f"Attacker Strategy: {value}"
            scenario_attackers = [{**attacker, "strategy": value} for attacker in attackers or []]
        elif variable_type == "defender_strategy":
            value = scenario["strategy"]
            value_label = f"Defender Strategy: {value}"
            scenario_defenders = [{**defender, "strategy": value} for defender in defenders or []]
        else:
            value = scenario.get("value", "unknown")
            value_label = f"Parameter: {value}"

        logger.info(f"{'─' * 60}")
        logger.info(f"SCENARIO {scenario_idx}/{len(scenarios)}")
        logger.info(value_label)
        logger.info(f"Number of Runs: {runs}")
        logger.info(f"{'─' * 60}")

        def scenario_progress_callback(
            run: int, scenario_runs: int, _completed: int = completed_runs
        ):
            if progress_callback:
                progress_callback(_completed + run, total_runs)

        orchestrator = SimulationOrchestrator(
            path_to_network_config=path_to_network_config,
            attackers=scenario_attackers or [],
            defenders=scenario_defenders or [],
            sim_time=sim_time,
            sim_runs=runs,
            detection_engine_type=detection_engine_type,
            action_duration_override=action_duration_override,
            attack_duration_override=attack_duration_override,
            defense_duration_override=defense_duration_override,
            progress_callback=scenario_progress_callback,
            enabled_actions=enabled_actions,
        )
        scenario_histories = orchestrator.run()

        completed_runs += runs
        scenario_result = {"runs": runs, "histories": scenario_histories}
        if variable_type in ["attack_duration", "defense_duration"]:
            scenario_result["duration"] = value
        else:
            scenario_result["strategy"] = value
        results["scenarios"].append(scenario_result)
        histories_count = len(scenario_histories) if scenario_histories else 0
        logger.info(f"Scenario {scenario_idx} completed: {histories_count} simulation runs")

    logger.info(f"{'=' * 60}")
    logger.info("ALL SCENARIOS COMPLETED")
    logger.info(f"Total scenarios: {len(scenarios)}")
    total_runs = sum(len(s.get("histories") or []) for s in results["scenarios"])
    logger.info(f"Total simulation runs: {total_runs}")
    logger.info(f"{'=' * 60}")
    return results
