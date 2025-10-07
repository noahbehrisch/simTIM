import sys
import os
import json
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from main import simtim_main

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("simTIM GUI")
        self.geometry("1700x800")
        self.minsize(2000, 1200)
        self.bg_color = "#f8f9fa"
        self.sidebar_color = "#e3eaf2"
        self.tab_color = "#ffffff"
        self.highlight_color = "#b5d6fc"
        self.button_color = "#d0e6fa"
        self.button_fg = "#22223b"
        self.configure(bg=self.bg_color)
        self.fullscreen_state = False
        self.bind("<Escape>", self.exit_fullscreen)
        self.bind("<F11>", self.toggle_fullscreen)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.tab_names = ["Simulation", "Network", "Attackers", "Defenders", "Overview"]
        self.tabs = {}
        self.current_tab = None
        self.create_tabs()
        self.sidebar = Sidebar(
            self, self.toggle_fullscreen, self.fullscreen_state, lambda name: self.show_tab(name),
            sidebar_color=self.sidebar_color, highlight_color=self.highlight_color, button_color=self.button_color, button_fg=self.button_fg
        )
        self.sidebar.grid(row=0, column=0, rowspan=3, sticky="nsw")
        self.bottom_frame = tk.Frame(self, bg=self.sidebar_color)
        self.bottom_frame.grid(row=2, column=1, sticky="ew")
        self.bottom_frame.grid_columnconfigure(0, weight=1)
        self.bottom_frame.grid_columnconfigure(1, weight=1)
        self.bottom_frame.grid_columnconfigure(2, weight=1)
        self.help_button = tk.Button(self.bottom_frame, text="Help", command=self.open_help_window, bg=self.button_color, fg=self.button_fg, activebackground=self.highlight_color)
        self.help_button.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        self.results_button = tk.Button(
            self.bottom_frame,
            text="Results",
            state=tk.DISABLED,
            bg=self.button_color,
            fg=self.button_fg,
            activebackground=self.highlight_color
        )
        self.results_button.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        self.start_button = tk.Button(self.bottom_frame, text="Start Simulation", command=self.run_simulation_from_gui, bg=self.button_color, fg=self.button_fg, activebackground=self.highlight_color)
        self.next_button = tk.Button(self.bottom_frame, text="Next", command=self.next_tab, bg=self.button_color, fg=self.button_fg, activebackground=self.highlight_color)
        self.after(0, lambda: self.show_tab("Simulation"))

    def create_tabs(self):
        tab_names = self.tab_names
        for name in tab_names:
            frame = tk.Frame(self, bg=self.tab_color)
            frame.grid(row=1, column=1, sticky="nswe")
            frame.grid_remove()
            self.tabs[name] = frame
            frame.grid_propagate(False)
            pad_frame = tk.Frame(frame, padx=50, pady=50, bg=self.tab_color)
            pad_frame.pack(expand=True, fill="both")
            self.tabs[name + "_pad"] = pad_frame
        sim_frame = self.tabs["Simulation_pad"]
        tk.Label(sim_frame, text="Simulation Runs:", bg=self.tab_color, fg=self.button_fg).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.sim_runs_var = tk.IntVar(value=5)
        tk.Entry(sim_frame, textvariable=self.sim_runs_var, width=10, bg="#eaf1fb", fg=self.button_fg, insertbackground=self.button_fg).grid(row=0, column=1, padx=10, pady=10, sticky="w")
        tk.Label(sim_frame, text="Simulation Time:", bg=self.tab_color, fg=self.button_fg).grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.sim_time_var = tk.DoubleVar(value=20.0)
        tk.Entry(sim_frame, textvariable=self.sim_time_var, width=10, bg="#eaf1fb", fg=self.button_fg, insertbackground=self.button_fg).grid(row=1, column=1, padx=10, pady=10, sticky="w")
        net_frame = self.tabs["Network_pad"]
        tk.Button(net_frame, text="Create Network", command=self.open_create_network_window, bg=self.button_color, fg=self.button_fg, activebackground=self.highlight_color).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        tk.Label(net_frame, text="Load Network File:", bg=self.tab_color, fg=self.button_fg).grid(row=1, column=0, padx=10, pady=10, sticky="w")
        default_network_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'networks', 'library', 'realistic_enterprise_network.json'))
        self.network_file_var = tk.StringVar(value=default_network_path)
        tk.Entry(net_frame, textvariable=self.network_file_var, width=30, bg="#eaf1fb", fg=self.button_fg, insertbackground=self.button_fg).grid(row=1, column=1, padx=10, pady=10, sticky="w")
        tk.Button(net_frame, text="Browse", command=self.browse_network_file, bg=self.button_color, fg=self.button_fg, activebackground=self.highlight_color).grid(row=1, column=2, padx=5, pady=10, sticky="w")
        tk.Button(net_frame, text="Visualize Network", command=self.launch_visualizer, bg=self.button_color, fg=self.button_fg, activebackground=self.highlight_color).grid(row=2, column=0, padx=10, pady=10, sticky="w")
        atk_frame = self.tabs["Attackers_pad"]
        self.attacker_entries = []
        self.attacker_list = []
        
        # Strategy descriptions
        strategy_info = tk.Frame(atk_frame, bg="#f0f8ff", relief="ridge", bd=1)
        strategy_info.pack(fill="x", padx=10, pady=5)
        tk.Label(strategy_info, text="Attacker Strategies:", bg="#f0f8ff", fg=self.button_fg, font=("Arial", 10, "bold")).pack(anchor="w", padx=5)
        tk.Label(strategy_info, text="• Greedy: Chooses actions with highest expected gain", bg="#f0f8ff", fg=self.button_fg, font=("Arial", 9)).pack(anchor="w", padx=15)
        tk.Label(strategy_info, text="• Random: Selects valid actions randomly", bg="#f0f8ff", fg=self.button_fg, font=("Arial", 9)).pack(anchor="w", padx=15)
        
        # Header row
        header_frame = tk.Frame(atk_frame, bg=self.tab_color)
        header_frame.pack(fill="x", padx=10, pady=5)
        tk.Label(header_frame, text="ID", bg=self.sidebar_color, fg=self.button_fg, width=12, relief="ridge").grid(row=0, column=0, padx=1)
        tk.Label(header_frame, text="Strategy", bg=self.sidebar_color, fg=self.button_fg, width=12, relief="ridge").grid(row=0, column=1, padx=1)
        tk.Label(header_frame, text="Capacity", bg=self.sidebar_color, fg=self.button_fg, width=8, relief="ridge").grid(row=0, column=2, padx=1)
        tk.Label(header_frame, text="∞", bg=self.sidebar_color, fg=self.button_fg, width=6, relief="ridge").grid(row=0, column=3, padx=1)
        tk.Label(header_frame, text="Budget ($)", bg=self.sidebar_color, fg=self.button_fg, width=10, relief="ridge").grid(row=0, column=4, padx=1)
        tk.Label(header_frame, text="Actions", bg=self.sidebar_color, fg=self.button_fg, width=8, relief="ridge").grid(row=0, column=5, padx=1)
        
        tk.Button(atk_frame, text="Add Attacker", command=self.add_attacker_entry, bg=self.button_color, fg=self.button_fg, activebackground=self.highlight_color).pack(padx=10, pady=10, anchor="w")
        self.attacker_entries_frame = tk.Frame(atk_frame, bg=self.tab_color)
        self.attacker_entries_frame.pack(fill="both", expand=True)
        def_frame = self.tabs["Defenders_pad"]
        self.defender_entries = []
        self.defender_list = []
        
        # Strategy descriptions
        strategy_info = tk.Frame(def_frame, bg="#f0fff0", relief="ridge", bd=1)
        strategy_info.pack(fill="x", padx=10, pady=5)
        tk.Label(strategy_info, text="Defender Strategies:", bg="#f0fff0", fg=self.button_fg, font=("Arial", 10, "bold")).pack(anchor="w", padx=5)
        tk.Label(strategy_info, text="• Reactive: Responds to detected threats and vulnerabilities", bg="#f0fff0", fg=self.button_fg, font=("Arial", 9)).pack(anchor="w", padx=15)
        tk.Label(strategy_info, text="• Proactive: Actively hardens systems and patches vulnerabilities", bg="#f0fff0", fg=self.button_fg, font=("Arial", 9)).pack(anchor="w", padx=15)
        tk.Label(strategy_info, text="• Monitoring: Focuses on detection and surveillance capabilities", bg="#f0fff0", fg=self.button_fg, font=("Arial", 9)).pack(anchor="w", padx=15)
        
        # Header row
        header_frame = tk.Frame(def_frame, bg=self.tab_color)
        header_frame.pack(fill="x", padx=10, pady=5)
        tk.Label(header_frame, text="ID", bg=self.sidebar_color, fg=self.button_fg, width=12, relief="ridge").grid(row=0, column=0, padx=1)
        tk.Label(header_frame, text="Strategy", bg=self.sidebar_color, fg=self.button_fg, width=12, relief="ridge").grid(row=0, column=1, padx=1)
        tk.Label(header_frame, text="Capacity", bg=self.sidebar_color, fg=self.button_fg, width=8, relief="ridge").grid(row=0, column=2, padx=1)
        tk.Label(header_frame, text="Budget ($)", bg=self.sidebar_color, fg=self.button_fg, width=10, relief="ridge").grid(row=0, column=3, padx=1)
        tk.Label(header_frame, text="Actions", bg=self.sidebar_color, fg=self.button_fg, width=8, relief="ridge").grid(row=0, column=4, padx=1)
        
        tk.Button(def_frame, text="Add Defender", command=self.add_defender_entry, bg=self.button_color, fg=self.button_fg, activebackground=self.highlight_color).pack(padx=10, pady=10, anchor="w")
        self.defender_entries_frame = tk.Frame(def_frame, bg=self.tab_color)
        self.defender_entries_frame.pack(fill="both", expand=True)
        self.add_attacker_entry()
        self.add_defender_entry()
        overview_frame = self.tabs["Overview_pad"]
        self.overview_text = tk.Text(overview_frame, width=60, height=30, state=tk.DISABLED, bg="#eaf1fb", fg=self.button_fg, insertbackground=self.button_fg)
        self.overview_text.pack(expand=True, fill="both", padx=10, pady=10)
        self.node_options = []
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
        network_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'networks', 'library')
        network_dir = os.path.abspath(network_dir)
        file_path = filedialog.askopenfilename(
            title="Select Network File",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
            initialdir=network_dir
        )
        if file_path:
            self.network_file_var.set(file_path)
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                if 'nodes' in data:
                    self.node_options = [n['id'] for n in data['nodes'] if 'id' in n]
                else:
                    self.node_options = []
            except Exception as e:
                self.node_options = []

    def add_attacker_entry(self):
        frame = tk.Frame(self.attacker_entries_frame, bg=self.tab_color)
        frame.pack(fill="x", padx=10, pady=2)
        
        attacker_id = len(self.attacker_entries) + 1
        
        # ID
        id_label = tk.Label(frame, text=f"Attacker {attacker_id}", bg="#eaf1fb", fg=self.button_fg, width=12, relief="sunken")
        id_label.grid(row=0, column=0, padx=1, sticky="w")
        
        # Strategy
        strategy_var = tk.StringVar(value="greedy")
        strategy_dropdown = ttk.Combobox(frame, textvariable=strategy_var, values=["greedy", "random"], state="readonly", width=10)
        strategy_dropdown.grid(row=0, column=1, padx=1, sticky="w")
        
        # Capacity
        capacity_var = tk.StringVar(value="3")
        capacity_entry = tk.Entry(frame, textvariable=capacity_var, width=6, bg="#eaf1fb", fg=self.button_fg)
        capacity_entry.grid(row=0, column=2, padx=1, sticky="w")
        
        # Infinite capacity checkbox
        infinite_var = tk.BooleanVar(value=False)
        infinite_check = tk.Checkbutton(frame, text="", variable=infinite_var, bg=self.tab_color, fg=self.button_fg,
                                       command=lambda: self._toggle_capacity(capacity_entry, infinite_var))
        infinite_check.grid(row=0, column=3, padx=1, sticky="w")
        
        # Budget
        budget_var = tk.StringVar(value="1000")
        budget_entry = tk.Entry(frame, textvariable=budget_var, width=8, bg="#eaf1fb", fg=self.button_fg)
        budget_entry.grid(row=0, column=4, padx=1, sticky="w")
        
        # Remove button
        remove_btn = tk.Button(frame, text="Remove", command=lambda: self._remove_attacker(frame), 
                              bg="#ffcccc", fg=self.button_fg, activebackground="#ff9999", width=6)
        remove_btn.grid(row=0, column=5, padx=1, sticky="w")
        
        self.attacker_entries.append((attacker_id, strategy_var, capacity_var, infinite_var, budget_var, frame))

    def _toggle_capacity(self, capacity_entry, infinite_var):
        if infinite_var.get():
            capacity_entry.config(state="disabled")
        else:
            capacity_entry.config(state="normal")
    
    def _remove_attacker(self, frame):
        # Find and remove the entry
        for i, entry in enumerate(self.attacker_entries):
            if entry[5] == frame:  # frame is the last element
                self.attacker_entries.pop(i)
                frame.destroy()
                break

    def add_defender_entry(self):
        frame = tk.Frame(self.defender_entries_frame, bg=self.tab_color)
        frame.pack(fill="x", padx=10, pady=2)
        
        defender_id = len(self.defender_entries) + 1
        
        # ID
        id_label = tk.Label(frame, text=f"Defender {defender_id}", bg="#eaf1fb", fg=self.button_fg, width=12, relief="sunken")
        id_label.grid(row=0, column=0, padx=1, sticky="w")
        
        # Strategy
        strategy_var = tk.StringVar(value="reactive")
        strategy_dropdown = ttk.Combobox(frame, textvariable=strategy_var, values=["reactive", "proactive", "monitoring"], state="readonly", width=10)
        strategy_dropdown.grid(row=0, column=1, padx=1, sticky="w")
        
        # Capacity
        capacity_var = tk.StringVar(value="2")
        capacity_entry = tk.Entry(frame, textvariable=capacity_var, width=6, bg="#eaf1fb", fg=self.button_fg)
        capacity_entry.grid(row=0, column=2, padx=1, sticky="w")
        
        # Budget
        budget_var = tk.StringVar(value="2000")
        budget_entry = tk.Entry(frame, textvariable=budget_var, width=8, bg="#eaf1fb", fg=self.button_fg)
        budget_entry.grid(row=0, column=3, padx=1, sticky="w")
        
        # Remove button
        remove_btn = tk.Button(frame, text="Remove", command=lambda: self._remove_defender(frame), 
                              bg="#ffcccc", fg=self.button_fg, activebackground="#ff9999", width=6)
        remove_btn.grid(row=0, column=4, padx=1, sticky="w")
        
        self.defender_entries.append((defender_id, strategy_var, capacity_var, budget_var, frame))
    
    def _remove_defender(self, frame):
        # Find and remove the entry
        for i, entry in enumerate(self.defender_entries):
            if entry[4] == frame:  # frame is now the 5th element (index 4)
                self.defender_entries.pop(i)
                frame.destroy()
                break

    def show_tab(self, name):
        if self.current_tab:
            self.tabs[self.current_tab].grid_remove()
        self.tabs[name].grid()
        self.current_tab = name
        self.sidebar.highlight_tab(name)
        for tname in self.tab_names:
            pad = self.tabs[tname + "_pad"]
            if tname == name:
                pad.pack(expand=True, fill="both")
            else:
                pad.pack_forget()
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
        overview = (
            f"Simulation Runs: {self.sim_runs_var.get()}\n"
            f"Simulation Time: {self.sim_time_var.get()}\n"
            f"Network File: {self.network_file_var.get()}\n"
        )
        overview += "Attackers:\n"
        for idx, entry in enumerate(self.attacker_entries):
            attacker_id, strategy_var, capacity_var, infinite_var, budget_var, _ = entry
            capacity_text = "∞" if infinite_var.get() else capacity_var.get()
            overview += f"  Attacker #{idx+1}: Strategy={strategy_var.get()}, Capacity={capacity_text}, Budget=${budget_var.get()}\n"
        
        overview += "Defenders:\n"
        for idx, entry in enumerate(self.defender_entries):
            defender_id, strategy_var, capacity_var, budget_var, _ = entry
            overview += f"  Defender #{idx+1}: Strategy={strategy_var.get()}, Capacity={capacity_var.get()}, Budget=${budget_var.get()}\n"
        
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
        win = tk.Toplevel(self)
        win.title("Create Network")
        win.geometry("1800x1200")
        win.configure(bg=self.bg_color)
        tk.Label(win, text="Network creation window", bg=self.tab_color, fg=self.button_fg).pack(padx=20, pady=20)

    def open_results_window(self, all_histories):
        import numpy as np
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        from src.visualization import ViolinPlotEngine, analyze_simulation_results

        win = tk.Toplevel(self)
        win.title("Simulation Results")
        win.geometry("1800x1200")
        win.configure(bg=self.bg_color)
        
        notebook = ttk.Notebook(win)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        logs_frame = tk.Frame(notebook, bg=self.bg_color)
        logs_text = tk.Text(logs_frame, wrap=tk.WORD, bg="#eaf1fb", fg=self.button_fg, state=tk.NORMAL)
        scrollbar = tk.Scrollbar(logs_frame, orient="vertical", command=logs_text.yview)
        logs_text.configure(yscrollcommand=scrollbar.set)
        
        logs_text.pack(side="left", expand=True, fill=tk.BOTH, padx=(10, 0), pady=10)
        scrollbar.pack(side="right", fill="y", padx=(0, 10), pady=10)
        
        notebook.add(logs_frame, text="Event Logs")
        
        logs_text.config(state=tk.NORMAL)
        logs_text.delete(1.0, tk.END)
        
        for run_index, history in enumerate(all_histories, start=1):
            logs_text.insert(tk.END, f"=== Simulation Run {run_index} ===\n")
            event_count = 0
            for entry in history:
                # Handle both Event objects and tuples
                if hasattr(entry, 'time') and hasattr(entry, 'event_type') and hasattr(entry, 'data'):
                    # It's an Event object
                    time = entry.time
                    event_type = entry.event_type
                    data = entry.data
                elif isinstance(entry, (list, tuple)) and len(entry) >= 3:
                    # It's a tuple/list
                    time, event_type, data = entry[:3]
                else:
                    # Unknown format, just display as string
                    logs_text.insert(tk.END, f"  {entry}\n")
                    continue
                
                # Format different event types
                if event_type == "start_action":
                    actor_id = data.get('actor', {}).id if hasattr(data.get('actor', {}), 'id') else 'Unknown'
                    action_name = data.get('action', {}).name if hasattr(data.get('action', {}), 'name') else 'Unknown'
                    target_id = data.get('target', {}).id if hasattr(data.get('target', {}), 'id') else 'Unknown'
                    logs_text.insert(tk.END, f"[{time:6.2f}] {actor_id} starts {action_name} on {target_id}\n")
                elif event_type == "action_succeeded":
                    actor_id = data.get('actor', {}).id if hasattr(data.get('actor', {}), 'id') else 'Unknown'
                    action_name = data.get('action', {}).name if hasattr(data.get('action', {}), 'name') else 'Unknown'
                    logs_text.insert(tk.END, f"[{time:6.2f}] ✓ {actor_id} completed {action_name}\n")
                elif event_type == "action_failed":
                    actor_id = data.get('actor', {}).id if hasattr(data.get('actor', {}), 'id') else 'Unknown'
                    action_name = data.get('action', {}).name if hasattr(data.get('action', {}), 'name') else 'Unknown'
                    logs_text.insert(tk.END, f"[{time:6.2f}] ✗ {actor_id} failed {action_name}\n")
                elif event_type == "attack_detected":
                    detected_actor = data.get('detected_actor', {}).id if hasattr(data.get('detected_actor', {}), 'id') else 'Unknown'
                    detected_action = data.get('detected_action', {}).name if hasattr(data.get('detected_action', {}), 'name') else 'Unknown'
                    logs_text.insert(tk.END, f"[{time:6.2f}] 🚨 Detected: {detected_actor} performing {detected_action}\n")
                elif event_type == "action_interrupted":
                    reason = data.get('reason', 'unknown')
                    actor_id = data.get('actor', {}).id if hasattr(data.get('actor', {}), 'id') else 'Unknown'
                    logs_text.insert(tk.END, f"[{time:6.2f}] ⚠ {actor_id} action interrupted ({reason})\n")
                else:
                    logs_text.insert(tk.END, f"[{time:6.2f}] {event_type}\n")
                
                event_count += 1
            
            logs_text.insert(tk.END, f"Total events in run {run_index}: {event_count}\n\n")
        
        logs_text.config(state=tk.DISABLED)
        
        try:
            simulation_results = analyze_simulation_results(all_histories)
            
            if simulation_results:
                plot_frame = tk.Frame(notebook, bg=self.bg_color)
                notebook.add(plot_frame, text="Economic Analysis")
                
                plotter = ViolinPlotEngine()
                fig = plotter.create_economic_comparison_plot(
                    simulation_results,
                    "TIM Simulation Results: Economic Impact"
                )
                
                canvas = FigureCanvasTkAgg(fig, master=plot_frame)
                canvas.draw()
                canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
                
                summary_frame = tk.Frame(notebook, bg=self.bg_color)
                notebook.add(summary_frame, text="Summary")
                
                summary_text = tk.Text(summary_frame, wrap=tk.WORD, bg="#eaf1fb", fg=self.button_fg)
                summary_text.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
                
                total_damage = sum(r.get('total_damage', 0) for r in simulation_results)
                total_gains = sum(r.get('total_attacker_gains', 0) for r in simulation_results)
                total_costs = sum(r.get('total_costs', 0) for r in simulation_results)
                avg_damage = total_damage / len(simulation_results) if simulation_results else 0
                
                summary_text.insert(tk.END, f"Simulation Summary\n")
                summary_text.insert(tk.END, f"==================\n\n")
                summary_text.insert(tk.END, f"Number of runs: {len(simulation_results)}\n")
                summary_text.insert(tk.END, f"Total system damage: ${total_damage:,.2f}\n")
                summary_text.insert(tk.END, f"Average damage per run: ${avg_damage:,.2f}\n")
                summary_text.insert(tk.END, f"Total attacker gains: ${total_gains:,.2f}\n")
                summary_text.insert(tk.END, f"Total action costs: ${total_costs:,.2f}\n")
                summary_text.insert(tk.END, f"Net attacker benefit: ${total_gains - total_costs:,.2f}\n")
                
                summary_text.config(state=tk.DISABLED)
            else:
                plot_frame = tk.Frame(notebook, bg=self.bg_color)
                tk.Label(plot_frame, text="No simulation data available for visualization", 
                        bg=self.bg_color, fg=self.button_fg).pack(expand=True)
                notebook.add(plot_frame, text="Visualization")
                
        except Exception as e:
            error_frame = tk.Frame(notebook, bg=self.bg_color)
            tk.Label(error_frame, text=f"Error creating visualization: {str(e)}", 
                    bg=self.bg_color, fg="red").pack(expand=True)
            notebook.add(error_frame, text="Visualization Error")

        def on_close():
            try:
                plt.close('all')
            except:
                pass
            win.destroy()
        
        win.protocol("WM_DELETE_WINDOW", on_close)

    def open_help_window(self):
        win = tk.Toplevel(self)
        win.title("Help")
        win.geometry("1800x1400")
        win.configure(bg=self.bg_color)
        tk.Label(win, text="Help!", bg=self.tab_color, fg=self.button_fg).pack(padx=20, pady=20)

    def run_simulation_from_gui(self):
        sim_runs = self.sim_runs_var.get()
        sim_time = self.sim_time_var.get()
        path_to_network_config = self.network_file_var.get()
        
        attackers = []
        for entry in self.attacker_entries:
            attacker_id, strategy_var, capacity_var, infinite_var, budget_var, _ = entry
            
            # Handle infinite capacity
            if infinite_var.get():
                capacity = float('inf')
            else:
                try:
                    capacity = int(capacity_var.get())
                except ValueError:
                    capacity = 3  # fallback
            
            # Handle budget
            try:
                budget = float(budget_var.get())
            except ValueError:
                budget = 1000.0  # fallback
            
            attackers.append({
                'id': f"attacker{attacker_id}",
                'strategy': strategy_var.get(),
                'capacity': capacity,
                'budget': budget
            })
        
        defenders = []
        for entry in self.defender_entries:
            defender_id, strategy_var, capacity_var, budget_var, _ = entry
            
            # Handle capacity
            try:
                capacity = int(capacity_var.get())
            except ValueError:
                capacity = 2  # fallback
            
            # Handle budget
            try:
                budget = float(budget_var.get())
            except ValueError:
                budget = 2000.0  # fallback
            
            defenders.append({
                'id': f"defender{defender_id}",
                'strategy': strategy_var.get(),
                'capacity': capacity,
                'budget': budget
            })
        
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
                defenders=defenders
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
            print("🔍 Full traceback:")
            traceback.print_exc()
            tk.messagebox.showerror("Simulation Error", error_msg)

    def launch_visualizer(self):
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        from src.networks.network_visualizer import NetworkVisualizer
        from src.core.graph import Graph

        network_path = self.network_file_var.get()
        network = Graph.from_json(network_path)
        visualizer = NetworkVisualizer(network)
        visualizer.visualize()

class Sidebar(tk.Frame):
    def __init__(self, master, toggle_fullscreen, fullscreen_state, switch_tab_callback, sidebar_color, highlight_color, button_color, button_fg):
        super().__init__(master, bd=2, relief=tk.RIDGE, bg=sidebar_color)
        self.grid_rowconfigure(6, weight=1)
        self.buttons = {}
        self.tab_names = ["Simulation", "Network", "Attackers", "Defenders", "Overview"]
        self.sidebar_color = sidebar_color
        self.highlight_color = highlight_color
        self.button_fg = button_fg
        for i, name in enumerate(self.tab_names):
            btn = tk.Button(self, text=name, command=lambda n=name: switch_tab_callback(n), bg=sidebar_color, fg=button_fg, activebackground=highlight_color, activeforeground=button_fg, relief=tk.FLAT)
            btn.grid(row=i, column=0, pady=20, padx=20, sticky="ew")
            self.buttons[name] = btn
        self.spacer = tk.Label(self, bg=sidebar_color)
        self.spacer.grid(row=6, column=0, sticky="nswe")
        self.grid_rowconfigure(6, weight=1)
        self.fullscreen_var = tk.BooleanVar(value=fullscreen_state)
        self.fullscreen_switch = tk.Checkbutton(self, text="Fullscreen", variable=self.fullscreen_var, command=toggle_fullscreen, bg=sidebar_color, fg=button_fg, selectcolor=highlight_color, activebackground=highlight_color)
        self.fullscreen_switch.grid(row=7, column=0, pady=(0, 10), padx=20, sticky="s")
        self.highlight_tab("Simulation")

    def highlight_tab(self, tab_name):
        for name, btn in self.buttons.items():
            if name == tab_name:
                btn.config(bg=self.highlight_color, fg=self.button_fg, relief=tk.SUNKEN)
            else:
                btn.config(bg=self.sidebar_color, fg=self.button_fg, relief=tk.FLAT)

    def update_fullscreen_switch(self):
        self.fullscreen_var.set(self.master.fullscreen_state)
if __name__ == "__main__":
    app = App()
    app.mainloop()