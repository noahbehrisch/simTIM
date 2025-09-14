import sys
import os
import json
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog

# Does not find main without this TODO: -m an easier solution?
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import simtim_main


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        # ---- Window Setup ----
        self.title("simTIM GUI")
        self.geometry("1200x800")
        self.minsize(1000, 600)
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

        # ---- Tabs and Sidebar ----
        self.tab_names = ["Simulation", "Network", "Attackers", "Defenders", "Overview"]
        self.tabs = {}
        self.current_tab = None
        self.create_tabs()
        self.sidebar = Sidebar(
            self, self.toggle_fullscreen, self.fullscreen_state, lambda name: self.show_tab(name),
            sidebar_color=self.sidebar_color, highlight_color=self.highlight_color, button_color=self.button_color, button_fg=self.button_fg
        )
        self.sidebar.grid(row=0, column=0, rowspan=3, sticky="nsw")

        # ---- Bottom Bar ----
        self.bottom_frame = tk.Frame(self, bg=self.sidebar_color)
        self.bottom_frame.grid(row=2, column=1, sticky="ew")
        self.bottom_frame.grid_columnconfigure(0, weight=1)
        self.bottom_frame.grid_columnconfigure(1, weight=1)
        self.bottom_frame.grid_columnconfigure(2, weight=1)
        self.help_button = tk.Button(self.bottom_frame, text="Help", command=self.open_help_window, bg=self.button_color, fg=self.button_fg, activebackground=self.highlight_color)
        self.help_button.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        self.results_button = tk.Button(self.bottom_frame, text="Results", bg=self.button_color, fg=self.button_fg, activebackground=self.highlight_color)
        self.start_button = tk.Button(self.bottom_frame, text="Start Simulation", command=self.run_simulation_from_gui, bg=self.button_color, fg=self.button_fg, activebackground=self.highlight_color)
        self.next_button = tk.Button(self.bottom_frame, text="Next", command=self.next_tab, bg=self.button_color, fg=self.button_fg, activebackground=self.highlight_color)
        self.after(0, lambda: self.show_tab("Simulation"))

    # ---- Tab Creation ----
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

        # ---- Simulation Tab ----
        sim_frame = self.tabs["Simulation_pad"]
        tk.Label(sim_frame, text="Simulation Runs:", bg=self.tab_color, fg=self.button_fg).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.sim_runs_var = tk.IntVar(value=1)
        tk.Entry(sim_frame, textvariable=self.sim_runs_var, width=10, bg="#eaf1fb", fg=self.button_fg, insertbackground=self.button_fg).grid(row=0, column=1, padx=10, pady=10, sticky="w")
        tk.Label(sim_frame, text="Simulation Time:", bg=self.tab_color, fg=self.button_fg).grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.sim_time_var = tk.DoubleVar(value=10.0)
        tk.Entry(sim_frame, textvariable=self.sim_time_var, width=10, bg="#eaf1fb", fg=self.button_fg, insertbackground=self.button_fg).grid(row=1, column=1, padx=10, pady=10, sticky="w")

        # ---- Network Tab ----
        net_frame = self.tabs["Network_pad"]
        tk.Button(net_frame, text="Create Network", command=self.open_create_network_window, bg=self.button_color, fg=self.button_fg, activebackground=self.highlight_color).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        tk.Label(net_frame, text="Load Network File:", bg=self.tab_color, fg=self.button_fg).grid(row=1, column=0, padx=10, pady=10, sticky="w")
        # Set default network file to network1.json
        default_network_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'networks', 'network1.json'))
        self.network_file_var = tk.StringVar(value=default_network_path)
        tk.Entry(net_frame, textvariable=self.network_file_var, width=30, bg="#eaf1fb", fg=self.button_fg, insertbackground=self.button_fg).grid(row=1, column=1, padx=10, pady=10, sticky="w")
        tk.Button(net_frame, text="Browse", command=self.browse_network_file, bg=self.button_color, fg=self.button_fg, activebackground=self.highlight_color).grid(row=1, column=2, padx=5, pady=10, sticky="w")
        # Add Visualize Network button to the Network Tab
        tk.Button(net_frame, text="Visualize Network", command=self.launch_visualizer, bg=self.button_color, fg=self.button_fg, activebackground=self.highlight_color).grid(row=2, column=0, padx=10, pady=10, sticky="w")

        # ---- Attackers Tab ----
        atk_frame = self.tabs["Attackers_pad"]
        self.attacker_entries = []
        self.attacker_list = []
        tk.Button(atk_frame, text="Add Attacker", command=self.add_attacker_entry, bg=self.button_color, fg=self.button_fg, activebackground=self.highlight_color).pack(padx=10, pady=10, anchor="w")
        self.attacker_entries_frame = tk.Frame(atk_frame, bg=self.tab_color)
        self.attacker_entries_frame.pack(fill="both", expand=True)

        # ---- Defenders Tab ----
        def_frame = self.tabs["Defenders_pad"]
        self.defender_entries = []
        self.defender_list = []
        tk.Button(def_frame, text="Add Defender", command=self.add_defender_entry, bg=self.button_color, fg=self.button_fg, activebackground=self.highlight_color).pack(padx=10, pady=10, anchor="w")
        self.defender_entries_frame = tk.Frame(def_frame, bg=self.tab_color)
        self.defender_entries_frame.pack(fill="both", expand=True)

        self.add_attacker_entry()
        self.add_defender_entry()

        # ---- Overview Tab ----
        overview_frame = self.tabs["Overview_pad"]
        self.overview_text = tk.Text(overview_frame, width=60, height=30, state=tk.DISABLED, bg="#eaf1fb", fg=self.button_fg, insertbackground=self.button_fg)
        self.overview_text.pack(expand=True, fill="both", padx=10, pady=10)


        # ---- Node options ----
        self.node_options = []
        # For default TODO: delete later
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

        network_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'networks')
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
        idx = len(self.attacker_entries)
        frame = tk.Frame(self.attacker_entries_frame, bg=self.tab_color, bd=1, relief=tk.GROOVE)
        frame.pack(fill="x", padx=5, pady=5)
        id_var = tk.StringVar(value=f"A{idx+1}")
        tk.Label(frame, text=f"Attacker #{idx+1} ID:", bg=self.tab_color).grid(row=0, column=0, sticky="w")
        tk.Entry(frame, textvariable=id_var, width=10, state='readonly').grid(row=0, column=1, sticky="w")
        self.attacker_entries.append({'id': id_var})

    def add_defender_entry(self):
        idx = len(self.defender_entries)
        frame = tk.Frame(self.defender_entries_frame, bg=self.tab_color, bd=1, relief=tk.GROOVE)
        frame.pack(fill="x", padx=5, pady=5)
        id_var = tk.StringVar(value=f"D{idx+1}")
        tk.Label(frame, text=f"Defender #{idx+1} ID:", bg=self.tab_color).grid(row=0, column=0, sticky="w")
        tk.Entry(frame, textvariable=id_var, width=10, state='readonly').grid(row=0, column=1, sticky="w")
        self.defender_entries.append({'id': id_var})

    # ---- Tab Logic ----
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
            self.results_button.config(command=self.open_results_window)
        else:
            self.results_button.grid_remove()
            self.start_button.grid_remove()
            self.next_button.grid(row=0, column=2, padx=10, pady=5, sticky="ew")

    # ---- Overview Variables ----
    def update_overview(self):
        overview = (
            f"Simulation Runs: {self.sim_runs_var.get()}\n"
            f"Simulation Time: {self.sim_time_var.get()}\n"
            f"Network File: {self.network_file_var.get()}\n"
        )
        overview += "Attackers:\n"
        for idx, entry in enumerate(self.attacker_entries):
            overview += (
                f"  Attacker #{idx+1}: ID={entry['id'].get()}\n"
            )
        overview += "Defenders:\n"
        for idx, entry in enumerate(self.defender_entries):
            overview += (
                f"  Defender #{idx+1}: ID={entry['id'].get()}\n"
            )
        self.overview_text.config(state=tk.NORMAL)
        self.overview_text.delete(1.0, tk.END)
        self.overview_text.insert(tk.END, overview)
        self.overview_text.config(state=tk.DISABLED)

    # ---- Tab Actions ----
    def set_attacker_info(self):
        self.attacker_info_var.set("Attacker created")

    def set_defender_info(self):
        self.defender_info_var.set("Defender created")

    # ---- Window Controls ----
    def exit_fullscreen(self, event=None):
        self.attributes("-fullscreen", False)
        self.fullscreen_state = False
        self.sidebar.update_fullscreen_switch()

    def toggle_fullscreen(self, event=None):
        self.fullscreen_state = not self.fullscreen_state
        self.attributes("-fullscreen", self.fullscreen_state)
        self.sidebar.update_fullscreen_switch()

    # ---- Navigation ----
    def next_tab(self):
        if self.current_tab in self.tab_names:
            idx = self.tab_names.index(self.current_tab)
            if idx < len(self.tab_names) - 1:
                self.show_tab(self.tab_names[idx + 1])

    # ---- Pop-up Windows ----
    def open_create_network_window(self):
        win = tk.Toplevel(self)
        win.title("Create Network")
        win.geometry("900x700")
        win.configure(bg=self.bg_color)
        tk.Label(win, text="Network creation window", bg=self.tab_color, fg=self.button_fg).pack(padx=20, pady=20)

    def open_results_window(self):
        win = tk.Toplevel(self)
        win.title("Results")
        win.geometry("900x700")
        win.configure(bg=self.bg_color)
        tk.Label(win, text="Results window", bg=self.tab_color, fg=self.button_fg).pack(padx=20, pady=20)

    def open_help_window(self):
        win = tk.Toplevel(self)
        win.title("Help")
        win.geometry("900x700")
        win.configure(bg=self.bg_color)
        tk.Label(win, text="Help!", bg=self.tab_color, fg=self.button_fg).pack(padx=20, pady=20)

    def run_simulation_from_gui(self):
        sim_runs = self.sim_runs_var.get()
        sim_time = self.sim_time_var.get()
        path_to_network_config = self.network_file_var.get()

        attackers = []
        for entry in self.attacker_entries:
            attackers.append({
                'id': entry['id'].get()
            })

        defenders = []
        for entry in self.defender_entries:
            defenders.append({
                'id': entry['id'].get()
            })
        # TODO: Add action selection per attacker/defender if needed
        simtim_main(
            path_to_network_config=path_to_network_config,
            sim_runs=sim_runs,
            sim_time=sim_time,
            attackers=attackers,
            defenders=defenders
        )
        sys.exit(0)

    def launch_visualizer(self):
        from networks.network_visualizer import NetworkVisualizer
        from simulator.graph import Graph

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
