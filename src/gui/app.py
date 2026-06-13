import json
import os
import sys
import tkinter as tk

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from src.core.simulation_runner import SimulationRunner
from src.gui.help_window import HelpWindow
from src.gui.progress_window import ProgressWindow
from src.gui.results_window import ResultsWindow
from src.gui.sidebar import Sidebar
from src.gui.tabs import (
    ActionTab,
    AttackerTab,
    DefenderTab,
    NetworkTab,
    OverviewTab,
    ScenarioTab,
    SimulationTab,
)
from src.gui.theme import Theme


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self._is_closing = False
        self._results_window = None
        self.theme = Theme()
        self.title("simTIM GUI")
        self.geometry("1400x800")
        self.minsize(1600, 1000)
        self.bg_color = self.theme.COLORS["bg_primary"]
        self.sidebar_color = self.theme.COLORS["bg_sidebar"]
        self.tab_color = self.theme.COLORS["bg_secondary"]
        self.highlight_color = self.theme.COLORS["accent_primary"]
        self.button_color = self.theme.COLORS["accent_secondary"]
        self.button_fg = self.theme.COLORS["text_primary"]
        self.configure(bg=self.bg_color)
        self.fullscreen_state = False
        self.bind("<Escape>", self.exit_fullscreen)
        self.bind("<F11>", self.toggle_fullscreen)
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.tab_names = [
            "Simulation",
            "Network",
            "Attackers",
            "Defenders",
            "Actions",
            "Scenarios",
            "Overview",
        ]
        self.tabs = {}
        self.current_tab = None
        self.last_sim_time = None
        self.last_total_nodes = None
        self.theme_colors = self.theme.get_theme_colors()
        self.create_tabs()
        self.sidebar = Sidebar(
            self,
            self.toggle_fullscreen,
            self.fullscreen_state,
            lambda name: self.show_tab(name),
            self.theme_colors,
        )
        self.sidebar.grid(row=0, column=0, rowspan=3, sticky="nsw")
        self.bottom_frame = tk.Frame(self, bg=self.sidebar_color)
        self.bottom_frame.grid(row=2, column=1, sticky="ew")
        self.bottom_frame.grid_columnconfigure(0, weight=1)
        self.bottom_frame.grid_columnconfigure(1, weight=1)
        self.bottom_frame.grid_columnconfigure(2, weight=1)
        self.help_button = tk.Button(
            self.bottom_frame,
            text="Help",
            command=self.open_help_window,
            **self.theme.get_button_style("default"),
        )
        self.help_button.grid(
            row=0,
            column=0,
            padx=self.theme.SPACING["md"],
            pady=self.theme.SPACING["sm"],
            sticky="ew",
        )
        results_style = self.theme.get_button_style("default")
        self.results_button = tk.Button(
            self.bottom_frame, text="Results", state=tk.DISABLED, **results_style
        )
        self.results_button.grid(
            row=0,
            column=1,
            padx=self.theme.SPACING["md"],
            pady=self.theme.SPACING["sm"],
            sticky="ew",
        )
        self.start_button = tk.Button(
            self.bottom_frame,
            text="Start Simulation",
            command=self.run_simulation_from_gui,
            **self.theme.get_button_style("primary"),
        )
        self.start_button.grid(
            row=0,
            column=2,
            padx=self.theme.SPACING["md"],
            pady=self.theme.SPACING["sm"],
            sticky="ew",
        )
        self.next_button = tk.Button(
            self.bottom_frame,
            text="Next",
            command=self.next_tab,
            **self.theme.get_button_style("default"),
        )
        self.after(0, lambda: self.show_tab("Simulation"))

    def create_tabs(self):
        self.simulation_tab = SimulationTab(self, self.theme_colors)
        self.network_tab = NetworkTab(self, self.theme_colors)
        self.attacker_tab = AttackerTab(self, self.theme_colors)
        self.defender_tab = DefenderTab(self, self.theme_colors)
        self.action_tab = ActionTab(self, self.theme_colors)
        self.scenario_tab = ScenarioTab(self, self.theme_colors)
        self.scenario_tab.on_scenarios_changed = self._on_variable_scenarios_changed
        self.overview_tab = OverviewTab(self, self.theme_colors)
        self.tabs["Simulation"] = self.simulation_tab.frame
        self.tabs["Network"] = self.network_tab.frame
        self.tabs["Attackers"] = self.attacker_tab.frame
        self.tabs["Defenders"] = self.defender_tab.frame
        self.tabs["Actions"] = self.action_tab.frame
        self.tabs["Scenarios"] = self.scenario_tab.frame
        self.tabs["Overview"] = self.overview_tab.frame
        self._load_default_network_nodes()

    def _load_default_network_nodes(self):
        self.node_options = []
        default_network_path = self.network_tab.network_file_var.get()
        try:
            with open(default_network_path) as f:
                data = json.load(f)
            if "nodes" in data:
                self.node_options = [n["id"] for n in data["nodes"] if "id" in n]
            else:
                self.node_options = []
        except Exception:
            self.node_options = []

    def _on_closing(self):
        self._is_closing = True
        self._close_results_window()
        try:
            import matplotlib.pyplot as plt

            plt.close("all")
        except Exception:
            pass
        self.quit()
        self.destroy()

    def browse_network_file(self):
        self.network_tab.browse_network_file()

    def add_attacker_entry(self):
        self.attacker_tab.add_attacker_entry()

    def add_defender_entry(self):
        self.defender_tab.add_defender_entry()

    def show_tab(self, name):
        if self.current_tab:
            tab_name_map = {
                "Simulation": "simulation_tab",
                "Network": "network_tab",
                "Attackers": "attacker_tab",
                "Defenders": "defender_tab",
            }
            if self.current_tab in tab_name_map:
                tab_obj = getattr(self, tab_name_map[self.current_tab])
                tab_obj.hide()
            elif self.current_tab in self.tabs:
                self.tabs[self.current_tab].grid_remove()
        tab_name_map = {
            "Simulation": "simulation_tab",
            "Network": "network_tab",
            "Attackers": "attacker_tab",
            "Defenders": "defender_tab",
        }
        if name in tab_name_map:
            tab_obj = getattr(self, tab_name_map[name])
            tab_obj.show()
        elif name in self.tabs:
            self.tabs[name].grid()
        self.current_tab = name
        self.sidebar.highlight_tab(name)
        if name == "Overview":
            self.update_overview()
            self.results_button.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
            self.start_button.grid(row=0, column=2, padx=10, pady=5, sticky="ew")
            self.next_button.grid_remove()
            self.results_button.config(command=lambda: self.open_results_window(self.all_histories))
        else:
            self.results_button.grid_remove()
            self.start_button.grid_remove()
            self.next_button.grid(row=0, column=2, padx=10, pady=5, sticky="ew")

    def update_overview(self):
        sim_config = self.simulation_tab.get_simulation_config()
        network_config = self.network_tab.get_network_config()
        attackers = self.attacker_tab.get_attacker_config()
        defenders = self.defender_tab.get_defender_config()
        scenario_config = self.scenario_tab.get_variables_config()
        self.overview_tab.update(sim_config, network_config, attackers, defenders, scenario_config)

    def set_attacker_info(self):
        self.attacker_info_var.set("Attacker created")

    def set_defender_info(self):
        self.defender_info_var.set("Defender created")

    def exit_fullscreen(self, event=None):
        self.attributes("-fullscreen", False)
        self.fullscreen_state = False
        self.sidebar.update_fullscreen_switch()

    def toggle_fullscreen(self, event=None):
        self.fullscreen_state = not self.fullscreen_state
        self.attributes("-fullscreen", self.fullscreen_state)
        self.sidebar.update_fullscreen_switch()

    def next_tab(self):
        if self.current_tab in self.tab_names:
            idx = self.tab_names.index(self.current_tab)
            if idx < len(self.tab_names) - 1:
                self.show_tab(self.tab_names[idx + 1])

    def _on_variable_scenarios_changed(self, scenarios):
        self.simulation_tab.update_runs_info(scenarios)

    def open_create_network_window(self):
        self.network_tab.open_create_network_window()

    def _close_results_window(self):
        if self._results_window is not None:
            try:
                self._results_window._on_close()
            except Exception:
                pass
            self._results_window = None

    def open_results_window(self, all_histories):
        self._close_results_window()
        theme_colors = {"bg_color": self.bg_color, "button_fg": self.button_fg}
        self._results_window = ResultsWindow(
            self,
            all_histories,
            theme_colors,
            sim_time=self.last_sim_time,
            total_nodes=self.last_total_nodes,
            network_path=getattr(self, "last_network_path", None),
        )

    def open_results_window_scenarios(self, scenario_results):
        self._close_results_window()
        theme_colors = {"bg_color": self.bg_color, "button_fg": self.button_fg}
        all_histories = []
        for scenario in scenario_results["scenarios"]:
            all_histories.extend(scenario["histories"])
        self._results_window = ResultsWindow(
            self,
            all_histories,
            theme_colors,
            scenario_results=scenario_results,
            sim_time=self.last_sim_time,
            total_nodes=self.last_total_nodes,
            network_path=getattr(self, "last_network_path", None),
        )

    def open_help_window(self):
        HelpWindow(self, self.current_tab)

    def run_simulation_from_gui(self):
        sim_config = self.simulation_tab.get_simulation_config()
        network_config = self.network_tab.get_network_config()
        attackers = self.attacker_tab.get_attacker_config()
        defenders = self.defender_tab.get_defender_config()
        scenario_config = self.scenario_tab.get_variables_config()
        enabled_actions = self.action_tab.get_enabled_actions()
        sim_runs = sim_config["runs"]
        sim_time = sim_config["time"]
        self.last_sim_time = sim_time
        detection_engine_type = sim_config["detection_engine_type"]
        path_to_network_config = network_config["file_path"]
        self.last_network_path = path_to_network_config

        try:
            import json

            with open(path_to_network_config) as f:
                net_data = json.load(f)
            self.last_total_nodes = len(net_data.get("nodes", []))
        except Exception:
            self.last_total_nodes = None

        if not attackers:
            tk.messagebox.showerror("Error", "At least one attacker is required!")
            return
        try:
            if scenario_config and "scenarios" in scenario_config and scenario_config["scenarios"]:
                scenarios = scenario_config["scenarios"]
                variable_type = scenario_config.get("variable_type", "action_duration")
                total_runs = sum(s.get("runs", 1) for s in scenarios)

                progress_window = ProgressWindow(self, total_runs=total_runs)

                def on_progress(current, total):
                    if not self._is_closing:
                        self.after(
                            0, lambda c=current, t=total: progress_window.update_progress(c, t)
                        )

                def on_complete(results):
                    if not self._is_closing:
                        self.after(
                            0, lambda: self._handle_scenario_complete(results, progress_window)
                        )

                def on_error(msg):
                    if not self._is_closing:
                        self.after(0, lambda: progress_window.show_error(msg))

                runner = SimulationRunner(
                    on_progress=on_progress,
                    on_complete=on_complete,
                    on_error=on_error,
                )
                runner.run_scenarios_async(
                    path_to_network_config=path_to_network_config,
                    scenarios=scenarios,
                    variable_type=variable_type,
                    attackers=attackers,
                    defenders=defenders,
                    sim_time=sim_time,
                    detection_engine_type=detection_engine_type,
                    enabled_actions=enabled_actions,
                )
            else:
                progress_window = ProgressWindow(self, total_runs=sim_runs)

                def on_progress(current, total):
                    if not self._is_closing:
                        self.after(
                            0, lambda c=current, t=total: progress_window.update_progress(c, t)
                        )

                def on_complete(all_histories):
                    if not self._is_closing:
                        self.after(
                            0,
                            lambda: self._handle_simulation_complete(
                                all_histories, progress_window
                            ),
                        )

                def on_error(msg):
                    if not self._is_closing:
                        self.after(0, lambda: progress_window.show_error(msg))

                runner = SimulationRunner(
                    on_progress=on_progress,
                    on_complete=on_complete,
                    on_error=on_error,
                )
                runner.run_async(
                    path_to_network_config=path_to_network_config,
                    sim_runs=sim_runs,
                    sim_time=sim_time,
                    attackers=attackers,
                    defenders=defenders,
                    detection_engine_type=detection_engine_type,
                    enabled_actions=enabled_actions,
                )
        except Exception as e:
            import traceback

            error_msg = f"Failed to run simulation:\n{str(e)}"
            print(f"\n🚨 SIMULATION ERROR: {error_msg}")
            print("Full traceback:")
            traceback.print_exc()
            tk.messagebox.showerror("Simulation Error", error_msg)

    def _handle_simulation_complete(self, all_histories, progress_window):
        self.all_histories = all_histories
        self.results_button.config(
            state=tk.NORMAL,
            command=lambda: self.open_results_window(all_histories),
        )
        progress_window.show_completion()

    def _handle_scenario_complete(self, results, progress_window):
        self.scenario_results = results
        self.all_histories = []
        for scenario in results["scenarios"]:
            self.all_histories.extend(scenario["histories"])
        self.results_button.config(
            state=tk.NORMAL,
            command=lambda: self.open_results_window_scenarios(results),
        )
        progress_window.show_completion()

    def launch_visualizer(self):
        self.network_tab.launch_visualizer()


if __name__ == "__main__":
    app = App()
    app.mainloop()
