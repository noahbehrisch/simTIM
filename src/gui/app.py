import sys
import os
import json
import tkinter as tk
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.core.simulation_main import simtim_main
from src.gui.enhanced_results_window import EnhancedResultsWindow
from src.gui.tabs import SimulationTab, NetworkTab, AttackerTab, DefenderTab, ActionTab, VariablesTab
from src.gui.sidebar import Sidebar
from src.gui.theme import Theme

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.theme = Theme()
        
        # Window configuration (making it narrower)
        self.title("simTIM GUI")
        self.geometry("1400x800")
        self.minsize(1600, 1000)
        
        # Use theme colors
        self.bg_color = self.theme.COLORS['bg_primary']
        self.sidebar_color = self.theme.COLORS['bg_sidebar']
        self.tab_color = self.theme.COLORS['bg_secondary']
        self.highlight_color = self.theme.COLORS['accent_primary']
        self.button_color = self.theme.COLORS['accent_secondary']
        self.button_fg = self.theme.COLORS['text_primary']
        
        self.configure(bg=self.bg_color)
        self.fullscreen_state = False
        self.bind("<Escape>", self.exit_fullscreen)
        self.bind("<F11>", self.toggle_fullscreen)
        
        # Grid configuration
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        
        # Tab management
        self.tab_names = ["Simulation", "Network", "Attackers", "Defenders", "Actions", "Variables", "Overview"]
        self.tabs = {}
        self.current_tab = None
        
        self.theme_colors = self.theme.get_theme_colors()
        
        self.create_tabs()
        self.sidebar = Sidebar(
            self, self.toggle_fullscreen, self.fullscreen_state, lambda name: self.show_tab(name),
            self.theme_colors
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
            **self.theme.get_button_style('default')
        )
        self.help_button.grid(row=0, column=0, padx=self.theme.SPACING['md'], pady=self.theme.SPACING['sm'], sticky="ew")
        
        results_style = self.theme.get_button_style('default')
        self.results_button = tk.Button(
            self.bottom_frame,
            text="Results",
            state=tk.DISABLED,
            **results_style
        )
        self.results_button.grid(row=0, column=1, padx=self.theme.SPACING['md'], pady=self.theme.SPACING['sm'], sticky="ew")
        
        self.start_button = tk.Button(
            self.bottom_frame, 
            text="Start Simulation", 
            command=self.run_simulation_from_gui, 
            **self.theme.get_button_style('primary')
        )
        self.start_button.grid(row=0, column=2, padx=self.theme.SPACING['md'], pady=self.theme.SPACING['sm'], sticky="ew")
        
        self.next_button = tk.Button(
            self.bottom_frame, 
            text="Next", 
            command=self.next_tab, 
            **self.theme.get_button_style('default')
        )
        self.after(0, lambda: self.show_tab("Simulation"))

    def create_tabs(self):
        """Create modular tabs using the new tab system."""
        # Create individual tab objects
        self.simulation_tab = SimulationTab(self, self.theme_colors)
        self.network_tab = NetworkTab(self, self.theme_colors)
        self.attacker_tab = AttackerTab(self, self.theme_colors)
        self.defender_tab = DefenderTab(self, self.theme_colors)
        self.action_tab = ActionTab(self, self.theme_colors)
        self.variables_tab = VariablesTab(self, self.theme_colors)
        
        # Store tab objects in tabs dict for easy access
        self.tabs["Simulation"] = self.simulation_tab.frame
        self.tabs["Network"] = self.network_tab.frame
        self.tabs["Attackers"] = self.attacker_tab.frame
        self.tabs["Defenders"] = self.defender_tab.frame
        self.tabs["Actions"] = self.action_tab.frame
        self.tabs["Variables"] = self.variables_tab.frame
        
        # Create Overview tab (keeping it in main app as it summarizes all tabs)
        overview_frame = tk.Frame(self, bg=self.tab_color)
        overview_frame.grid(row=1, column=1, sticky="nswe")
        overview_frame.grid_remove()
        overview_frame.grid_propagate(False)
        
        # Overview tab content
        overview_pad_frame = tk.Frame(overview_frame, padx=50, pady=50, bg=self.tab_color)
        overview_pad_frame.pack(expand=True, fill="both")
        
        self.overview_text = tk.Text(
            overview_pad_frame, 
            width=60, 
            height=30, 
            state=tk.DISABLED, 
            bg="#eaf1fb", 
            fg=self.button_fg, 
            insertbackground=self.button_fg
        )
        self.overview_text.pack(expand=True, fill="both", padx=10, pady=10)
        
        self.tabs["Overview"] = overview_frame
        
        # Load initial node options from default network
        self._load_default_network_nodes()
    
    def _load_default_network_nodes(self):
        """Load node options from the default network file."""
        self.node_options = []
        default_network_path = self.network_tab.network_file_var.get()
        try:
            with open(default_network_path, 'r') as f:
                data = json.load(f)
            if 'nodes' in data:
                self.node_options = [n['id'] for n in data['nodes'] if 'id' in n]
            else:
                self.node_options = []
        except Exception as e:
            self.node_options = []

    def browse_network_file(self):
        """Delegate to network tab."""
        self.network_tab.browse_network_file()

    def add_attacker_entry(self):
        """Delegate to attacker tab."""
        self.attacker_tab.add_attacker_entry()

    def add_defender_entry(self):
        """Delegate to defender tab."""
        self.defender_tab.add_defender_entry()

    def show_tab(self, name):
        """Show the specified tab and hide others."""
        # Hide current tab
        if self.current_tab:
            tab_name_map = {
                "Simulation": "simulation_tab",
                "Network": "network_tab", 
                "Attackers": "attacker_tab",
                "Defenders": "defender_tab"
            }
            
            if self.current_tab in tab_name_map:
                # Use new tab system
                tab_obj = getattr(self, tab_name_map[self.current_tab])
                tab_obj.hide()
            elif self.current_tab in self.tabs:
                # Use old tab system for Overview
                self.tabs[self.current_tab].grid_remove()
        
        # Show new tab
        tab_name_map = {
            "Simulation": "simulation_tab",
            "Network": "network_tab", 
            "Attackers": "attacker_tab",
            "Defenders": "defender_tab"
        }
        
        if name in tab_name_map:
            # Use new tab system
            tab_obj = getattr(self, tab_name_map[name])
            tab_obj.show()
        elif name in self.tabs:
            # Use old tab system for Overview
            self.tabs[name].grid()
        
        self.current_tab = name
        self.sidebar.highlight_tab(name)
        
        # Handle Overview tab special behavior
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
        """Update overview tab with current configuration from all tabs."""
        # Get configuration from all tabs
        sim_config = self.simulation_tab.get_simulation_config()
        network_config = self.network_tab.get_network_config()
        attackers = self.attacker_tab.get_attacker_config()
        defenders = self.defender_tab.get_defender_config()
        
        # Build overview text
        overview = "SIMULATION CONFIGURATION\n"
        overview += "=" * 50 + "\n\n"
        
        # Simulation parameters
        overview += "Simulation Parameters:\n"
        overview += f"   • Runs: {sim_config['runs']}\n"
        overview += f"   • Time: {sim_config['time']} seconds\n"
        overview += f"   • Detection Engine: {sim_config['detection_engine_type']}\n\n"
        
        # Network configuration
        overview += "Network Configuration:\n"
        network_file = network_config['file_path']
        network_name = network_file.split('/')[-1] if '/' in network_file else network_file
        overview += f"   • File: {network_name}\n"
        overview += f"   • Path: {network_file}\n\n"
        
        # Attackers
        overview += f"Attackers ({len(attackers)}):\n"
        for idx, attacker in enumerate(attackers, 1):
            capacity_text = "∞" if attacker['capacity'] == float('inf') else str(attacker['capacity'])
            overview += f"   {idx}. {attacker['id']}\n"
            overview += f"      Strategy: {attacker['strategy']}\n"
            overview += f"      Capacity: {capacity_text}\n"
            overview += f"      Budget: ${attacker['budget']}\n"
        
        overview += "\n"
        
        # Defenders
        overview += f"Defenders ({len(defenders)}):\n"
        for idx, defender in enumerate(defenders, 1):
            overview += f"   {idx}. {defender['id']}\n"
            overview += f"      Strategy: {defender['strategy']}\n"
            overview += f"      Capacity: {defender['capacity']}\n"
            overview += f"      Budget: ${defender['budget']}\n"
        
        overview += "\n" + "=" * 50 + "\n"
        overview += "Ready to run simulation!"
        
        # Update the overview text widget
        self.overview_text.config(state=tk.NORMAL)
        self.overview_text.delete(1.0, tk.END)
        self.overview_text.insert(tk.END, overview)
        self.overview_text.config(state=tk.DISABLED)

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

    def open_create_network_window(self):
        """Delegate to network tab."""
        self.network_tab.open_create_network_window()

    def open_results_window(self, all_histories):
        theme_colors = {
            'bg_color': self.bg_color,
            'button_fg': self.button_fg
        }
        results_window = EnhancedResultsWindow(self, all_histories, theme_colors)

    def open_help_window(self):
        win = tk.Toplevel(self)
        win.title("Help")
        win.geometry("1800x1400")
        win.configure(bg=self.bg_color)
        tk.Label(win, text="Help!", bg=self.tab_color, fg=self.button_fg).pack(padx=20, pady=20)

    def run_simulation_from_gui(self):
        # Get configuration from all tabs
        sim_config = self.simulation_tab.get_simulation_config()
        network_config = self.network_tab.get_network_config()
        attackers = self.attacker_tab.get_attacker_config()
        defenders = self.defender_tab.get_defender_config()
        variables_config = self.variables_tab.get_variables_config()
        
        # Extract values
        sim_runs = sim_config['runs']
        sim_time = sim_config['time']
        detection_engine_type = sim_config['detection_engine_type']
        path_to_network_config = network_config['file_path']
        
        # Validate inputs
        if not attackers:
            tk.messagebox.showerror("Error", "At least one attacker is required!")
            return
        if not defenders:
            tk.messagebox.showerror("Error", "At least one defender is required!")
            return
        
        try:
            all_histories = simtim_main(
                path_to_network_config=path_to_network_config,
                sim_runs=sim_runs,
                sim_time=sim_time,
                attackers=attackers,
                defenders=defenders,
                detection_engine_type=detection_engine_type
            )
            self.all_histories = all_histories
            self.results_button.config(state=tk.NORMAL, command=lambda: self.open_results_window(all_histories))
            
            custom_messagebox = tk.Toplevel(self)
            custom_messagebox.title("Simulation Complete")
            custom_messagebox.geometry("800x400")
            custom_messagebox.configure(bg=self.bg_color)
            tk.Label(custom_messagebox, text="Simulation Complete", bg=self.bg_color, fg=self.button_fg, font=("Arial", 16)).pack(expand=True, fill=tk.BOTH, padx=20, pady=20)
            tk.Button(custom_messagebox, text="OK", command=custom_messagebox.destroy, bg=self.button_color, fg=self.button_fg).pack(pady=10)
            
        except Exception as e:
            import traceback
            error_msg = f"Failed to run simulation:\n{str(e)}"
            print(f"\n🚨 SIMULATION ERROR: {error_msg}")
            print("Full traceback:")
            traceback.print_exc()
            tk.messagebox.showerror("Simulation Error", error_msg)

    def launch_visualizer(self):
        """Delegate to network tab."""
        self.network_tab.launch_visualizer()


if __name__ == "__main__":
    app = App()
    app.mainloop()