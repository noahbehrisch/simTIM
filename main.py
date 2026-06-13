import os
import sys

from src.gui.app import App


def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == "--demo":
            sys.exit(run_demo())
        elif sys.argv[1] == "--cli":
            sys.exit(run_cli())
        elif sys.argv[1] == "--help":
            print_help()
            sys.exit(0)

    try:
        app = App()
        app.mainloop()
    except ImportError as e:
        print(f"Error: Could not import GUI components: {e}")
        print("Make sure all required packages are installed (requirements.txt)")
        sys.exit(1)
    except Exception as e:
        print(f"Error launching GUI: {e}")
        sys.exit(1)


def print_help():
    print("""
simTIM - Cybersecurity Simulation Tool
======================================

Usage:
  python main.py          Launch the GUI application
  python main.py --demo   Run a quick demo simulation with results
  python main.py --cli    Run an interactive CLI simulation
  python main.py --help   Show this help message

For more information, see README.md
""")


def run_demo():
    from src.core.simulation_runner import SimulationRunner
    from src.utils.results_printer import print_event_history, print_quick_summary

    demo_network = os.path.join(
        os.path.dirname(__file__), "src", "networks", "library", "demo_network.json"
    )

    print("=" * 70)
    print("simTIM Demo Run")
    print("=" * 70)
    print(f"Network: {demo_network}")
    print("Attacker: escalation strategy, infinite capacity, budget 100000")
    print("Defender: balanced strategy, capacity 2, budget 100000")
    print("Duration: 168 hours (1 week)")
    print("Runs: 3")
    print("=" * 70)
    print()

    runner = SimulationRunner()
    histories = runner.run_sync(
        path_to_network_config=demo_network,
        attackers=[
            {
                "id": "apt_group",
                "strategy": "escalation",
                "capacity": float("inf"),
                "budget": 100000,
            }
        ],
        defenders=[
            {
                "id": "security_team",
                "strategy": "balanced",
                "capacity": 2,
                "budget": 100000,
            }
        ],
        sim_time=168,
        sim_runs=3,
        detection_engine_type="early_weighted",
    )

    if histories:
        print_event_history(histories, verbose=False, show_timeline=True)

        print_quick_summary(histories)

        print()
        print("=" * 70)
        print("Demo complete.")
        print("=" * 70)
    else:
        print("Demo run failed!")
        return 1
    return 0


def run_cli():
    from src.core.simulation_runner import SimulationRunner
    from src.networks import NetworkLoader
    from src.utils.results_printer import (
        export_to_csv,
        export_to_json,
        print_event_history,
        print_quick_summary,
    )

    loader = NetworkLoader()
    available_networks = loader.list_available()

    print("\n" + "=" * 70)
    print("simTIM - Interactive CLI Mode")
    print("=" * 70)

    print("\nAvailable networks:")
    for i, network in enumerate(available_networks, 1):
        print(f"  {i}. {network}")

    while True:
        try:
            choice = input("\nSelect network (number or 'q' to quit): ").strip()
            if choice.lower() == "q":
                return 0
            idx = int(choice) - 1
            if 0 <= idx < len(available_networks):
                network_name = available_networks[idx]
                break
            print("Invalid selection. Try again.")
        except ValueError:
            print("Please enter a number.")

    print("\n" + "-" * 50)
    print("Simulation Parameters")
    print("-" * 50)

    try:
        sim_time = int(input("Simulation time (hours) [168]: ").strip() or "168")
        sim_runs = int(input("Number of runs [1]: ").strip() or "1")

        print("\nAttacker strategies: greedy, random, escalation")
        attacker_strategy = input("Attacker strategy [escalation]: ").strip() or "escalation"

        print("Defender strategies: reactive, proactive, monitoring, balanced")
        defender_strategy = input("Defender strategy [balanced]: ").strip() or "balanced"
    except ValueError:
        print("Invalid input. Using defaults.")
        sim_time = 168
        sim_runs = 1
        attacker_strategy = "escalation"
        defender_strategy = "balanced"

    print("\n" + "=" * 70)
    print("Running simulation...")
    print("=" * 70)

    network_path = loader.get_path(network_name)
    runner = SimulationRunner()
    histories = runner.run_sync(
        path_to_network_config=str(network_path),
        attackers=[
            {
                "id": "attacker",
                "strategy": attacker_strategy,
                "capacity": float("inf"),
                "budget": 100000,
            }
        ],
        defenders=[
            {
                "id": "defender",
                "strategy": defender_strategy,
                "capacity": 2,
                "budget": 100000,
            }
        ],
        sim_time=sim_time,
        sim_runs=sim_runs,
        detection_engine_type="early_weighted",
    )

    if not histories:
        print("Simulation failed!")
        return 1

    print_event_history(histories, verbose=False, show_timeline=True)
    print_quick_summary(histories)

    print("\n" + "-" * 50)
    print("Export Options")
    print("-" * 50)

    export_choice = input("Export results? (csv/json/both/no) [no]: ").strip().lower()

    if export_choice in ["csv", "both"]:
        csv_path = input("CSV filename [results.csv]: ").strip() or "results.csv"
        export_to_csv(histories, csv_path)

    if export_choice in ["json", "both"]:
        json_path = input("JSON filename [results.json]: ").strip() or "results.json"
        export_to_json(histories, json_path)

    print("\nDone!")
    return 0


if __name__ == "__main__":
    main()
