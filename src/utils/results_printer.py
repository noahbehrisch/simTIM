"""
Utilities for printing and exporting simulation results.

This module provides functions to display simulation results in the terminal
and export them to various formats (CSV, JSON) for further analysis.
"""

import csv
import json
from pathlib import Path
from typing import Any

from src.utils.time_utils import format_time, parse_event


def print_event_history(
    histories: list[list],
    verbose: bool = False,
    show_timeline: bool = True,
) -> None:
    """
    Print simulation event histories to the terminal in a readable format.

    Args:
        histories: List of simulation run histories
        verbose: If True, show all event details; if False, show summary only
        show_timeline: If True, show chronological event timeline
    """
    print("\n" + "=" * 70)
    print("SIMULATION RESULTS")
    print("=" * 70)

    for run_idx, history in enumerate(histories):
        print(f"\n{'─' * 70}")
        print(f"RUN {run_idx + 1} OF {len(histories)}")
        print(f"{'─' * 70}")

        # Parse and analyze events
        events_by_type: dict[str, list] = {}
        timeline: list[dict[str, Any]] = []
        stats = {
            "successful_attacks": 0,
            "failed_attacks": 0,
            "successful_defenses": 0,
            "failed_defenses": 0,
            "detections": 0,
            "total_damage": 0.0,
            "total_gains": 0.0,
            "total_costs": 0.0,
            "nodes_compromised": set(),
            "actions_executed": [],
        }

        for event in history:
            time, event_type, data = parse_event(event)
            if time is None:
                continue

            # Categorize event
            if event_type not in events_by_type:
                events_by_type[event_type] = []
            events_by_type[event_type].append((time, data))

            # Build timeline entry
            entry = _build_timeline_entry(time, event_type, data, stats)
            if entry:
                timeline.append(entry)

        # Print timeline if requested
        if show_timeline and timeline:
            print("\n📅 EVENT TIMELINE:")
            print("-" * 50)
            for entry in sorted(timeline, key=lambda x: x["time"]):
                _print_timeline_entry(entry, verbose)

        # Print summary statistics
        _print_run_summary(stats, len(history))

    # Print overall summary if multiple runs
    if len(histories) > 1:
        _print_overall_summary(histories)


def _build_timeline_entry(
    time: float, event_type: str, data: dict, stats: dict
) -> dict[str, Any] | None:
    """Build a timeline entry from an event and update stats."""
    if not isinstance(data, dict):
        return None

    entry: dict[str, Any] = {
        "time": time,
        "type": event_type,
        "icon": "❓",
        "description": "",
    }

    action = data.get("action")
    actor = data.get("actor")
    target = data.get("target")

    action_name = getattr(action, "name", "Unknown") if action else "Unknown"
    actor_id = getattr(actor, "id", "Unknown") if actor else "Unknown"
    target_id = getattr(target, "id", "Unknown") if target else "Unknown"

    is_attacker = actor is not None and hasattr(actor, "is_attacker") and actor.is_attacker
    is_defender = actor is not None and hasattr(actor, "is_defender") and actor.is_defender

    if event_type == "action_started":
        entry["icon"] = "🔄" if is_attacker else "🛡️"
        entry["description"] = f"{actor_id} started '{action_name}' on {target_id}"

    elif event_type == "action_succeeded":
        if is_attacker:
            stats["successful_attacks"] += 1
            stats["nodes_compromised"].add(target_id)
            entry["icon"] = "⚔️"
            entry["description"] = f"ATTACK SUCCESS: {actor_id} → '{action_name}' → {target_id}"
        elif is_defender:
            stats["successful_defenses"] += 1
            entry["icon"] = "✅"
            entry["description"] = f"DEFENSE SUCCESS: {actor_id} → '{action_name}' → {target_id}"
        else:
            entry["icon"] = "✓"
            entry["description"] = f"ACTION SUCCESS: {actor_id} → '{action_name}' → {target_id}"

        stats["actions_executed"].append(action_name)

    elif event_type == "action_failed":
        if is_attacker:
            stats["failed_attacks"] += 1
            entry["icon"] = "❌"
            entry["description"] = f"ATTACK FAILED: {actor_id} → '{action_name}' → {target_id}"
        elif is_defender:
            stats["failed_defenses"] += 1
            entry["icon"] = "⚠️"
            entry["description"] = f"DEFENSE FAILED: {actor_id} → '{action_name}' → {target_id}"
        else:
            entry["icon"] = "✗"
            entry["description"] = f"ACTION FAILED: {actor_id} → '{action_name}'"

    elif event_type == "attack_detected":
        stats["detections"] += 1
        entry["icon"] = "🚨"
        detected_action_obj = data.get("detected_action")
        detected_target_obj = data.get("detected_target")
        detected_action_name = (
            getattr(detected_action_obj, "name", "unknown action")
            if detected_action_obj
            else "unknown action"
        )
        detected_target_id = (
            getattr(detected_target_obj, "id", "Unknown") if detected_target_obj else "Unknown"
        )
        entry["description"] = (
            f"DETECTION: '{detected_action_name}' detected on {detected_target_id}"
        )

    elif event_type == "simulation_start":
        entry["icon"] = "🏁"
        entry["description"] = "Simulation started"

    elif event_type == "simulation_ended":
        entry["icon"] = "🏁"
        entry["description"] = "Simulation ended"
        economic_summary = data.get("economic_summary")
        if economic_summary:
            stats["total_damage"] = economic_summary.get("total_damage", stats["total_damage"])
            stats["total_gains"] = economic_summary.get(
                "total_attacker_gains", stats["total_gains"]
            )
            stats["total_costs"] = economic_summary.get("total_costs", stats["total_costs"])

    else:
        entry["description"] = f"{event_type}: {actor_id} on {target_id}"

    return entry


def _print_timeline_entry(entry: dict[str, Any], verbose: bool) -> None:
    """Print a single timeline entry."""
    time_str = format_time(entry["time"])
    print(f"  [{time_str}] {entry['icon']} {entry['description']}")


def _print_run_summary(stats: dict, total_events: int) -> None:
    """Print summary statistics for a single run."""
    print("\n📊 RUN SUMMARY:")
    print("-" * 50)
    print(f"  Total events:         {total_events}")
    print(f"  Successful attacks:   {stats['successful_attacks']}")
    print(f"  Failed attacks:       {stats['failed_attacks']}")
    print(f"  Successful defenses:  {stats['successful_defenses']}")
    print(f"  Failed defenses:      {stats['failed_defenses']}")
    print(f"  Detections:           {stats['detections']}")
    print(f"  Nodes compromised:    {len(stats['nodes_compromised'])}")
    if stats["nodes_compromised"]:
        print(f"    → {', '.join(sorted(stats['nodes_compromised']))}")
    print("\n💰 ECONOMIC IMPACT:")
    print(f"  Total damage:         ${stats['total_damage']:,.2f}")
    print(f"  Attacker gains:       ${stats['total_gains']:,.2f}")
    print(f"  Action costs:         ${stats['total_costs']:,.2f}")

    # Attack success rate
    total_attacks = stats["successful_attacks"] + stats["failed_attacks"]
    if total_attacks > 0:
        success_rate = (stats["successful_attacks"] / total_attacks) * 100
        print(f"\n📈 ATTACK SUCCESS RATE: {success_rate:.1f}%")


def _print_overall_summary(histories: list[list]) -> None:
    """Print overall summary across all runs."""
    print("\n" + "=" * 70)
    print("OVERALL SUMMARY (ALL RUNS)")
    print("=" * 70)

    all_damages = []
    all_gains = []
    all_attacks = []

    for history in histories:
        run_damage = 0.0
        run_gains = 0.0
        run_attacks = 0
        for event in history:
            time, event_type, data = parse_event(event)
            if event_type == "simulation_ended" and isinstance(data, dict):
                economic_summary = data.get("economic_summary")
                if economic_summary:
                    run_damage = economic_summary.get("total_damage", 0.0)
                    run_gains = economic_summary.get("total_attacker_gains", 0.0)
            elif event_type == "action_succeeded" and isinstance(data, dict):
                actor = data.get("actor")
                if actor is not None and hasattr(actor, "is_attacker") and actor.is_attacker:
                    run_attacks += 1
        all_damages.append(run_damage)
        all_gains.append(run_gains)
        all_attacks.append(run_attacks)

    print(f"\n  Runs completed:       {len(histories)}")
    print(f"  Avg damage per run:   ${sum(all_damages) / len(all_damages):,.2f}")
    print(f"  Avg gains per run:    ${sum(all_gains) / len(all_gains):,.2f}")
    print(f"  Avg attacks per run:  {sum(all_attacks) / len(all_attacks):.1f}")
    print(f"  Min damage:           ${min(all_damages):,.2f}")
    print(f"  Max damage:           ${max(all_damages):,.2f}")


def export_to_csv(
    histories: list[list],
    output_path: str | Path,
    include_details: bool = True,
) -> None:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    for run_idx, history in enumerate(histories):
        for event in history:
            time, event_type, data = parse_event(event)
            if time is None:
                continue

            row = {
                "run": run_idx + 1,
                "time": time,
                "time_formatted": format_time(time),
                "event_type": event_type,
            }

            if include_details and isinstance(data, dict):
                action = data.get("action")
                actor = data.get("actor")
                target = data.get("target")

                row["action"] = getattr(action, "name", "") if action else ""
                row["actor"] = getattr(actor, "id", "") if actor else ""
                row["actor_type"] = (
                    "attacker"
                    if actor is not None and hasattr(actor, "is_attacker") and actor.is_attacker
                    else "defender"
                    if actor is not None and hasattr(actor, "is_defender") and actor.is_defender
                    else ""
                )
                row["target"] = getattr(target, "id", "") if target else ""

            rows.append(row)

    if rows:
        with open(output_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        print(f"✅ Results exported to: {output_path}")
    else:
        print("⚠️ No events to export")


def export_to_json(
    histories: list[list],
    output_path: str | Path,
    include_summary: bool = True,
) -> None:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    result: dict[str, Any] = {"runs": []}

    for run_idx, history in enumerate(histories):
        run_data: dict[str, Any] = {
            "run_id": run_idx + 1,
            "events": [],
            "summary": {
                "successful_attacks": 0,
                "failed_attacks": 0,
                "successful_defenses": 0,
                "detections": 0,
                "total_damage": 0.0,
                "total_gains": 0.0,
                "nodes_compromised": [],
            },
        }

        for event in history:
            time, event_type, data = parse_event(event)
            if time is None:
                continue

            event_record: dict[str, Any] = {
                "time": time,
                "time_formatted": format_time(time),
                "type": event_type,
            }

            if isinstance(data, dict):
                action = data.get("action")
                actor = data.get("actor")
                target = data.get("target")

                event_record["action"] = getattr(action, "name", None) if action else None
                event_record["actor"] = getattr(actor, "id", None) if actor else None
                event_record["target"] = getattr(target, "id", None) if target else None

                # Update summary
                is_attacker = (
                    actor is not None and hasattr(actor, "is_attacker") and actor.is_attacker
                )
                is_defender = (
                    actor is not None and hasattr(actor, "is_defender") and actor.is_defender
                )

                if event_type == "simulation_ended":
                    economic_summary = data.get("economic_summary")
                    if economic_summary:
                        run_data["summary"]["total_damage"] = economic_summary.get(
                            "total_damage", 0.0
                        )
                        run_data["summary"]["total_gains"] = economic_summary.get(
                            "total_attacker_gains", 0.0
                        )
                elif event_type == "action_succeeded":
                    if is_attacker:
                        run_data["summary"]["successful_attacks"] += 1
                        target_id = getattr(target, "id", None)
                        if target_id and target_id not in run_data["summary"]["nodes_compromised"]:
                            run_data["summary"]["nodes_compromised"].append(target_id)
                    elif is_defender:
                        run_data["summary"]["successful_defenses"] += 1
                elif event_type == "action_failed" and is_attacker:
                    run_data["summary"]["failed_attacks"] += 1
                elif event_type == "attack_detected":
                    run_data["summary"]["detections"] += 1

            run_data["events"].append(event_record)

        result["runs"].append(run_data)

    # Add overall summary if requested
    if include_summary and result["runs"]:
        total_damage = sum(r["summary"]["total_damage"] for r in result["runs"])
        total_attacks = sum(r["summary"]["successful_attacks"] for r in result["runs"])
        result["overall_summary"] = {
            "total_runs": len(result["runs"]),
            "total_damage": total_damage,
            "average_damage": total_damage / len(result["runs"]),
            "total_successful_attacks": total_attacks,
            "average_attacks_per_run": total_attacks / len(result["runs"]),
        }

    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"✅ Results exported to: {output_path}")


def print_quick_summary(histories: list[list]) -> None:
    print("\n📋 QUICK SUMMARY:")
    print("-" * 70)
    print(f"{'Run':<5} {'Attacks':<10} {'Defenses':<10} {'Detections':<12} {'Damage':<15}")
    print("-" * 70)

    for run_idx, history in enumerate(histories):
        attacks = 0
        defenses = 0
        detections = 0
        damage = 0.0

        for event in history:
            time, event_type, data = parse_event(event)
            if not isinstance(data, dict):
                continue

            actor = data.get("actor")

            if event_type == "simulation_ended":
                economic_summary = data.get("economic_summary")
                if economic_summary:
                    damage = economic_summary.get("total_damage", 0.0)
            elif event_type == "action_succeeded":
                if actor is not None and hasattr(actor, "is_attacker") and actor.is_attacker:
                    attacks += 1
                elif actor is not None and hasattr(actor, "is_defender") and actor.is_defender:
                    defenses += 1
            elif event_type == "attack_detected":
                detections += 1

        print(f"{run_idx + 1:<5} {attacks:<10} {defenses:<10} {detections:<12} ${damage:,.2f}")

    print("-" * 70)
