import logging
from typing import Any

from src.actions.action_manager import action_manager
from src.actors.attacker import Attacker
from src.actors.defender import Defender
from src.core.access_levels import LinkAccessLevel, NodeAccessLevel
from src.core.economic_model import SimpleEconomicModel
from src.core.simulator import Simulator
from src.networks import NetworkLoader

logger = logging.getLogger(__name__)

# Global network loader instance
_network_loader = NetworkLoader()


def simtim_main(
    path_to_network_config: str,
    attackers: list[dict[str, Any]] | None = None,
    defenders: list[dict[str, Any]] | None = None,
    sim_time: int = 72,
    sim_runs: int = 1,
    detection_engine_type: str = "exponential",
    action_duration_override: float | None = None,
    attack_duration_override: float | None = None,
    defense_duration_override: float | None = None,
) -> list[list] | None:
    if not path_to_network_config:
        logger.error("No network configuration file provided")
        return None
    if not attackers or not isinstance(attackers, list) or len(attackers) == 0:
        logger.error("No attackers specified")
        return None
    if not defenders or not isinstance(defenders, list) or len(defenders) == 0:
        logger.error("No defenders specified")
        return None
    if sim_time is None:
        logger.error("Simulation end time not provided")
        return None
    if not sim_runs or not isinstance(sim_runs, int) or sim_runs < 1:
        sim_runs = 1
    if action_duration_override is not None:
        logger.info(f"All actions will use duration: {action_duration_override} hours")
    all_histories = []
    for run in range(sim_runs):
        logger.info(f"Running simulation {run + 1}/{sim_runs}")
        network = _network_loader.load(path_to_network_config)
        # Links are already populated in the Network object
        attack_actions = action_manager.get_attack_actions()
        defense_actions = action_manager.get_defense_actions()
        if action_duration_override is not None:
            for action in attack_actions:
                action.duration = action_duration_override
            for action in defense_actions:
                action.duration = action_duration_override
        if attack_duration_override is not None:
            for action in attack_actions:
                action.duration = attack_duration_override
        if defense_duration_override is not None:
            for action in defense_actions:
                action.duration = defense_duration_override
        # Create fresh economic model for each run to track economics separately
        run_economic_model = SimpleEconomicModel()
        simulator = Simulator(
            network,
            detection_engine_type=detection_engine_type,
            economic_model_instance=run_economic_model,
        )
        attacker_objs = []
        for i, attacker_config in enumerate(attackers):
            attacker = Attacker(
                id=attacker_config.get("id", f"attacker_{i}"),
                strategy=attacker_config.get("strategy", "random"),
                capacity=attacker_config.get("capacity", 3),
                budget=float(attacker_config.get("budget", 1000)),
            )
            attacker.available_actions = attack_actions
            attacker_objs.append(attacker)
        defender_objs = []
        for i, defender_config in enumerate(defenders):
            defender = Defender(
                id=defender_config.get("id", f"defender_{i}"),
                strategy=defender_config.get("strategy", "reactive"),
                capacity=defender_config.get("capacity", 1),
                budget=float(defender_config.get("budget", 1000)),
            )
            defender.available_actions = defense_actions
            defender_objs.append(defender)
        network.actors = list(attacker_objs) + list(defender_objs)  # type: ignore[assignment]
        for attacker in attacker_objs:
            for node in network.nodes_list:
                if not hasattr(node, "access"):
                    node.access = {}
                if hasattr(node, "properties") and node.properties.get(
                    "exposed_to_internet", False
                ):
                    node.access[attacker.id] = NodeAccessLevel.VISIBLE.to_string()
                    attacker.visible_nodes.add(node)
                else:
                    node.access[attacker.id] = NodeAccessLevel.NONE.to_string()
            for link in network.links_list:
                if not hasattr(link, "access"):
                    link.access = {}
                link.access[attacker.id] = LinkAccessLevel.NONE.to_string()

        for attacker in attacker_objs:
            if not attacker.visible_nodes:
                logger.warning(
                    f"{attacker.id} has no visible nodes - no entry points in network! "
                    f"The simulation will run but this attacker will have no initial access. "
                    f'Ensure at least one node has "exposed_to_internet": true.'
                )

        for defender in defender_objs:
            for node in network.nodes_list:
                if not hasattr(node, "access"):
                    node.access = {}
                node.access[defender.id] = NodeAccessLevel.ADMIN.to_string()
                defender.visible_nodes.add(node)
            for link in network.links_list:
                if not hasattr(link, "access"):
                    link.access = {}
                link.access[defender.id] = LinkAccessLevel.VISIBLE.to_string()
                defender.visible_links.add(link)
        simulator.network = network
        simulator.run(until=sim_time)
        history_tuples = []
        for event in simulator.history:
            if hasattr(event, "time"):
                history_tuples.append((event.time, event.event_type, event.data))
            else:
                history_tuples.append(event)
        all_histories.append(history_tuples)
        logger.info(f"Simulation run {run + 1} completed with {len(history_tuples)} events")
        if run + 1 < sim_runs:
            logger.debug("Preparing next simulation run...")
        else:
            logger.debug("Final network state:")
            for n in network.nodes_list:
                logger.debug(str(n))
    logger.info(f"All {sim_runs} simulation runs completed")
    return all_histories


def run_variable_scenarios(
    path_to_network_config: str,
    scenarios: list,
    variable_type: str = "action_duration",
    attackers: list | None = None,
    defenders: list | None = None,
    sim_time: int = 10,
    detection_engine_type="exponential",
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
        scenario_histories = simtim_main(
            path_to_network_config=path_to_network_config,
            attackers=scenario_attackers,
            defenders=scenario_defenders,
            sim_time=sim_time,
            sim_runs=runs,
            detection_engine_type=detection_engine_type,
            action_duration_override=action_duration_override,
            attack_duration_override=attack_duration_override,
            defense_duration_override=defense_duration_override,
        )
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
    total_runs = sum(len(s.get("histories") or []) for s in results["scenarios"])  # type: ignore[arg-type]
    logger.info(f"Total simulation runs: {total_runs}")
    logger.info(f"{'=' * 60}")
    return results
