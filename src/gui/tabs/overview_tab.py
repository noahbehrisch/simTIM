import tkinter as tk

from .base_tab import BaseTab


class OverviewTab(BaseTab):
    def __init__(self, parent, theme_colors):
        self.overview_text = None
        super().__init__(parent, theme_colors)

    def create_widgets(self):
        self.overview_text = tk.Text(
            self.pad_frame,
            width=60,
            height=30,
            state=tk.DISABLED,
            bg="#eaf1fb",
            fg=self.button_fg,
            insertbackground=self.button_fg,
        )
        self.overview_text.pack(expand=True, fill="both", padx=10, pady=10)

    def update(self, sim_config, network_config, attackers, defenders, scenario_config):
        overview = "SIMULATION CONFIGURATION\n"
        overview += "=" * 50 + "\n\n"
        overview += "Simulation Parameters:\n"

        if scenario_config and "scenarios" in scenario_config and scenario_config["scenarios"]:
            scenarios = scenario_config["scenarios"]
            var_type = scenario_config.get("variable_type", "action_duration")
            total_runs = sum(s["runs"] for s in scenarios)

            if var_type == "attack_duration":
                mode_desc = "ATTACK DURATION COMPARISON"
            elif var_type == "defense_duration":
                mode_desc = "DEFENSE DURATION COMPARISON"
            elif var_type == "attacker_strategy":
                mode_desc = "ATTACKER STRATEGY COMPARISON"
            elif var_type == "defender_strategy":
                mode_desc = "DEFENDER STRATEGY COMPARISON"
            else:
                mode_desc = "SCENARIO COMPARISON"

            overview += f"   • Mode: {mode_desc}\n"
            overview += f"   • Scenarios: {len(scenarios)}\n"
            overview += f"   • Total Runs: {total_runs}\n"
            overview += f"   • Time per run: {sim_config['time']} seconds\n"
            overview += f"   • Detection Engine: {sim_config['detection_engine_type']}\n\n"
            overview += "   Scenario Details:\n"

            for idx, scenario in enumerate(scenarios, 1):
                runs = scenario["runs"]
                if var_type == "attack_duration":
                    overview += (
                        f"      {idx}. Attack Duration: {scenario['duration']}h → {runs} runs\n"
                    )
                elif var_type == "defense_duration":
                    overview += (
                        f"      {idx}. Defense Duration: {scenario['duration']}h → {runs} runs\n"
                    )
                elif var_type == "attacker_strategy":
                    overview += (
                        f"      {idx}. Attacker Strategy: {scenario['strategy']} → {runs} runs\n"
                    )
                elif var_type == "defender_strategy":
                    overview += (
                        f"      {idx}. Defender Strategy: {scenario['strategy']} → {runs} runs\n"
                    )
                else:
                    overview += f"      {idx}. Scenario → {runs} runs\n"
            overview += "\n"
        else:
            overview += f"   • Runs: {sim_config['runs']}\n"
            overview += f"   • Time: {sim_config['time']} seconds\n"
            overview += f"   • Detection Engine: {sim_config['detection_engine_type']}\n\n"

        overview += "Network Configuration:\n"
        network_file = network_config["file_path"]
        network_name = network_file.split("/")[-1] if "/" in network_file else network_file
        overview += f"   • File: {network_name}\n"
        overview += f"   • Path: {network_file}\n\n"

        overview += f"Attackers ({len(attackers)}):\n"
        for idx, attacker in enumerate(attackers, 1):
            capacity_text = (
                "∞" if attacker["capacity"] == float("inf") else str(attacker["capacity"])
            )
            overview += f"   {idx}. {attacker['id']}\n"
            overview += f"      Strategy: {attacker['strategy']}\n"
            overview += f"      Capacity: {capacity_text}\n"
            overview += f"      Budget: ${attacker['budget']}\n"
        overview += "\n"

        overview += f"Defenders ({len(defenders)}):\n"
        for idx, defender in enumerate(defenders, 1):
            overview += f"   {idx}. {defender['id']}\n"
            overview += f"      Strategy: {defender['strategy']}\n"
            overview += f"      Capacity: {defender['capacity']}\n"
            overview += f"      Budget: ${defender['budget']}\n"

        overview += "\n" + "=" * 50 + "\n"
        overview += "Ready to run simulation!"

        self.overview_text.config(state=tk.NORMAL)
        self.overview_text.delete(1.0, tk.END)
        self.overview_text.insert(tk.END, overview)
        self.overview_text.config(state=tk.DISABLED)
