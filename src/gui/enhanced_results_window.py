import tkinter as tk
from tkinter import ttk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from typing import List, Dict, Any, Optional
from src.visualization import ViolinPlotEngine, analyze_simulation_results


class EnhancedResultsWindow:
    def __init__(self, parent, all_histories, theme_colors):
        self.parent = parent
        self.all_histories = all_histories
        self.bg_color = theme_colors['bg_color']
        self.button_fg = theme_colors['button_fg']
        
        # Processed data
        self.runs_data = []
        self.actors_data = {}
        self.economic_data = {}
        
        # Create window
        self.window = tk.Toplevel(parent)
        self.window.title("Simulation Results")
        self.window.geometry("1600x1000")
        self.window.configure(bg=self.bg_color)
        
        # Process simulation data
        self._process_simulation_data()
        
        # Create interface
        self._create_interface()
    
    def _process_simulation_data(self):
        """Process raw simulation histories into structured data"""
        self.runs_data = []
        self.actors_data = {}
        
        for run_id, history in enumerate(self.all_histories):
            run_events = []
            
            for event in history:
                # Handle both Event objects and tuples
                if hasattr(event, 'time') and hasattr(event, 'event_type') and hasattr(event, 'data'):
                    # Event object
                    time = event.time
                    event_type = event.event_type
                    data = event.data
                elif isinstance(event, (list, tuple)) and len(event) >= 3:
                    # Tuple format: (time, event_type, data)
                    time, event_type, data = event[:3]
                else:
                    continue
                
                # Extract actor information
                actor_id = 'Unknown'
                action_name = 'Unknown'
                target_id = 'Unknown'
                
                if isinstance(data, dict):
                    # Handle different event structures
                    if event_type == 'attack_detected':
                        # Detection events use 'detected_actor', 'detected_action', 'detected_target'
                        if 'detected_actor' in data and hasattr(data['detected_actor'], 'id'):
                            actor_id = data['detected_actor'].id
                        if 'detected_action' in data and hasattr(data['detected_action'], 'name'):
                            action_name = data['detected_action'].name
                        if 'detected_target' in data and hasattr(data['detected_target'], 'id'):
                            target_id = data['detected_target'].id
                    elif event_type == 'action_interrupted_by_detection':
                        # Interrupted events have 'actor' as string, 'action' as string, 'target' as object
                        if 'actor' in data:
                            actor_id = data['actor'] if isinstance(data['actor'], str) else str(data['actor'])
                        if 'action' in data:
                            action_name = data['action'] if isinstance(data['action'], str) else str(data['action'])
                        if 'target' in data and hasattr(data['target'], 'id'):
                            target_id = data['target'].id
                    else:
                        # Regular action events use 'actor', 'action', 'target'
                        if 'actor' in data and hasattr(data['actor'], 'id'):
                            actor_id = data['actor'].id
                        if 'action' in data and hasattr(data['action'], 'name'):
                            action_name = data['action'].name
                        if 'target' in data and hasattr(data['target'], 'id'):
                            target_id = data['target'].id
                
                # Only skip events that truly have no actor information
                if actor_id == 'Unknown' and event_type not in ['attack_detected', 'action_interrupted_by_detection']:
                    continue
                
                # Create event record
                event_record = {
                    'run_id': run_id,
                    'time': time,
                    'event_type': event_type,
                    'actor_id': actor_id,
                    'action_name': action_name,
                    'target_id': target_id,
                    'success': event_type == 'action_succeeded',
                    'detection': event_type == 'attack_detected',
                    'raw_data': data
                }
                
                run_events.append(event_record)
                
                # Add to actor data
                if actor_id not in self.actors_data:
                    self.actors_data[actor_id] = {
                        'actions': [],
                        'economics': {
                            'total_cost': 0,
                            'total_gain': 0,
                            'total_damage': 0,
                            'per_run': {}
                        }
                    }
                
                self.actors_data[actor_id]['actions'].append(event_record)
                
                # Calculate economic impact
                if event_record['success']:
                    cost = self._estimate_cost(event_record)
                    gain = self._estimate_gain(event_record)
                    damage = self._estimate_damage(event_record)
                    
                    self.actors_data[actor_id]['economics']['total_cost'] += cost
                    self.actors_data[actor_id]['economics']['total_gain'] += gain
                    self.actors_data[actor_id]['economics']['total_damage'] += damage
                    
                    # Per-run tracking
                    if run_id not in self.actors_data[actor_id]['economics']['per_run']:
                        self.actors_data[actor_id]['economics']['per_run'][run_id] = {
                            'cost': 0, 'gain': 0, 'damage': 0
                        }
                    
                    self.actors_data[actor_id]['economics']['per_run'][run_id]['cost'] += cost
                    self.actors_data[actor_id]['economics']['per_run'][run_id]['gain'] += gain
                    self.actors_data[actor_id]['economics']['per_run'][run_id]['damage'] += damage
            
            self.runs_data.append(run_events)
    
    def _estimate_cost(self, event: Dict[str, Any]) -> float:
        """Estimate action cost"""
        action_name = event['action_name'].lower()
        if 'exploit' in action_name:
            return np.random.normal(200, 50)
        elif 'scan' in action_name:
            return np.random.normal(50, 10)
        elif 'lateral' in action_name:
            return np.random.normal(150, 30)
        else:
            return np.random.normal(100, 20)
    
    def _estimate_gain(self, event: Dict[str, Any]) -> float:
        """Estimate attacker gain"""
        if 'attacker' not in event['actor_id'].lower():
            return 0
        
        action_name = event['action_name'].lower()
        if 'exploit' in action_name:
            return np.random.normal(1500, 300)
        elif 'lateral' in action_name:
            return np.random.normal(800, 150)
        elif 'scan' in action_name:
            return np.random.normal(200, 50)
        else:
            return np.random.normal(400, 80)
    
    def _estimate_damage(self, event: Dict[str, Any]) -> float:
        """Estimate system damage"""
        action_name = event['action_name'].lower()
        if 'exploit' in action_name:
            return np.random.normal(5000, 1000)
        elif 'lateral' in action_name:
            return np.random.normal(3000, 500)
        elif 'scan' in action_name:
            return np.random.normal(500, 100)
        else:
            return np.random.normal(1000, 200)
    
    def _create_interface(self):
        """Create the main interface"""
        # Main notebook
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Determine if we need dropdowns
        num_runs = len(self.runs_data)
        num_actors = len(self.actors_data)
        
        # Create run tabs
        if num_runs <= 5:
            # Create individual tabs for each run
            for run_id in range(num_runs):
                self._create_run_tab(run_id)
        else:
            # Create single tab with dropdown selector
            self._create_runs_dropdown_tab()
        
        # Create actor tabs
        if num_actors <= 8:
            # Create individual tabs for each actor
            for actor_id in self.actors_data.keys():
                self._create_actor_tab(actor_id)
        else:
            # Create single tab with dropdown selector
            self._create_actors_dropdown_tab()
        
        # Create statistical analysis tab
        #TODO: uncomment stat tab when working ready
        #self._create_statistical_tab()
        
        # Window close handler
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _create_run_tab(self, run_id: int):
        """Create a tab for a specific simulation run"""
        tab_frame = tk.Frame(self.notebook, bg=self.bg_color)
        self.notebook.add(tab_frame, text=f"Run {run_id + 1}")
        
        # Add basic stats at top
        stats_frame = tk.Frame(tab_frame, bg=self.bg_color, relief=tk.RAISED, bd=1)
        stats_frame.pack(fill=tk.X, padx=10, pady=5)
        
        events = self.runs_data[run_id]
        total_events = len(events)
        successful_events = len([e for e in events if e['success']])
        detections = len([e for e in events if e['detection']])
        
        tk.Label(stats_frame, text=f"Run {run_id + 1} Summary:", font=('Arial', 12, 'bold'),
                bg=self.bg_color, fg=self.button_fg).pack(side=tk.LEFT, padx=10)
        tk.Label(stats_frame, text=f"Total Events: {total_events}  |  Successful: {successful_events}  |  Detections: {detections}",
                bg=self.bg_color, fg=self.button_fg).pack(side=tk.LEFT, padx=20)
        
        # Event log
        log_frame = tk.Frame(tab_frame, bg=self.bg_color)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Create text widget with scrollbar
        text_frame = tk.Frame(log_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        logs_text = tk.Text(text_frame, wrap=tk.WORD, bg="#eaf1fb", fg=self.button_fg, 
                           font=('Consolas', 10))
        scrollbar = tk.Scrollbar(text_frame, orient=tk.VERTICAL, command=logs_text.yview)
        logs_text.configure(yscrollcommand=scrollbar.set)
        
        logs_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Populate event log
        for event in sorted(events, key=lambda x: x['time']):
            self._add_event_to_log(logs_text, event)
        
        logs_text.config(state=tk.DISABLED)
    
    def _create_runs_dropdown_tab(self):
        """Create a single tab with dropdown for run selection"""
        tab_frame = tk.Frame(self.notebook, bg=self.bg_color)
        self.notebook.add(tab_frame, text="Event History")
        
        # Dropdown frame
        dropdown_frame = tk.Frame(tab_frame, bg=self.bg_color, relief=tk.RAISED, bd=1)
        dropdown_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(dropdown_frame, text="Select Run:", bg=self.bg_color, fg=self.button_fg).pack(side=tk.LEFT, padx=10)
        
        self.run_selector = tk.StringVar(value="Run 1")
        run_options = [f"Run {i+1}" for i in range(len(self.runs_data))]
        run_dropdown = ttk.Combobox(dropdown_frame, textvariable=self.run_selector, 
                                   values=run_options, state="readonly", width=15)
        run_dropdown.pack(side=tk.LEFT, padx=5)
        run_dropdown.bind('<<ComboboxSelected>>', self._on_run_selected)
        
        # Stats frame
        self.run_stats_frame = tk.Frame(tab_frame, bg=self.bg_color, relief=tk.RAISED, bd=1)
        self.run_stats_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Event log frame
        log_frame = tk.Frame(tab_frame, bg=self.bg_color)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        text_frame = tk.Frame(log_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        self.run_logs_text = tk.Text(text_frame, wrap=tk.WORD, bg="#eaf1fb", fg=self.button_fg, 
                                    font=('Consolas', 10))
        run_scrollbar = tk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.run_logs_text.yview)
        self.run_logs_text.configure(yscrollcommand=run_scrollbar.set)
        
        self.run_logs_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        run_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Load initial run
        self._load_run_data(0)
    
    def _create_actor_tab(self, actor_id: str):
        """Create a tab for a specific actor"""
        tab_frame = tk.Frame(self.notebook, bg=self.bg_color)
        self.notebook.add(tab_frame, text=actor_id)
        
        # Create paned window for actions and economics
        paned = tk.PanedWindow(tab_frame, orient=tk.VERTICAL, bg=self.bg_color)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Actions section
        actions_frame = tk.Frame(paned, bg=self.bg_color, relief=tk.RAISED, bd=1)
        paned.add(actions_frame, minsize=200)
        
        tk.Label(actions_frame, text=f"{actor_id} - Actions Timeline", 
                font=('Arial', 12, 'bold'), bg=self.bg_color, fg=self.button_fg).pack(pady=5)
        
        # Actions list
        actions_text = tk.Text(actions_frame, height=15, wrap=tk.WORD, bg="#eaf1fb", fg=self.button_fg,
                              font=('Consolas', 9))
        actions_scrollbar = tk.Scrollbar(actions_frame, orient=tk.VERTICAL, command=actions_text.yview)
        actions_text.configure(yscrollcommand=actions_scrollbar.set)
        
        actions_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        actions_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
        
        # Populate actions
        actor_actions = sorted(self.actors_data[actor_id]['actions'], key=lambda x: (x['run_id'], x['time']))
        for action in actor_actions:
            self._add_action_to_log(actions_text, action)
        
        actions_text.config(state=tk.DISABLED)
        
        # Economics section
        economics_frame = tk.Frame(paned, bg=self.bg_color, relief=tk.RAISED, bd=1)
        paned.add(economics_frame, minsize=200)
        
        tk.Label(economics_frame, text=f"{actor_id} - Economic Impact", 
                font=('Arial', 12, 'bold'), bg=self.bg_color, fg=self.button_fg).pack(pady=5)
        
        # Economics toggle
        toggle_frame = tk.Frame(economics_frame, bg=self.bg_color)
        toggle_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.economics_view = tk.StringVar(value="total")
        ttk.Radiobutton(toggle_frame, text="Total", variable=self.economics_view, value="total",
                       command=lambda: self._update_economics_view(actor_id, economics_frame)).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(toggle_frame, text="Per Run", variable=self.economics_view, value="per_run",
                       command=lambda: self._update_economics_view(actor_id, economics_frame)).pack(side=tk.LEFT, padx=5)
        
        # Economics content frame
        self.economics_content_frame = tk.Frame(economics_frame, bg=self.bg_color)
        self.economics_content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Load initial economics view
        self._update_economics_view(actor_id, economics_frame)
    
    def _create_actors_dropdown_tab(self):
        """Create a single tab with dropdown for actor selection"""
        tab_frame = tk.Frame(self.notebook, bg=self.bg_color)
        self.notebook.add(tab_frame, text="Actor Analysis")
        
        # Dropdown frame
        dropdown_frame = tk.Frame(tab_frame, bg=self.bg_color, relief=tk.RAISED, bd=1)
        dropdown_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(dropdown_frame, text="Select Actor:", bg=self.bg_color, fg=self.button_fg).pack(side=tk.LEFT, padx=10)
        
        self.actor_selector = tk.StringVar(value=list(self.actors_data.keys())[0])
        actor_options = list(self.actors_data.keys())
        actor_dropdown = ttk.Combobox(dropdown_frame, textvariable=self.actor_selector, 
                                     values=actor_options, state="readonly", width=20)
        actor_dropdown.pack(side=tk.LEFT, padx=5)
        actor_dropdown.bind('<<ComboboxSelected>>', self._on_actor_selected)
        
        # Actor content frame
        self.actor_content_frame = tk.Frame(tab_frame, bg=self.bg_color)
        self.actor_content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Load initial actor
        self._load_actor_data(list(self.actors_data.keys())[0])
    
    def _create_statistical_tab(self):
        """Create statistical analysis tab with violin plots"""
        tab_frame = tk.Frame(self.notebook, bg=self.bg_color)
        self.notebook.add(tab_frame, text="Statistical Analysis")
        
        # Create matplotlib figure
        self.stat_fig, ((self.damage_ax, self.cost_ax), 
                       (self.gain_ax, self.comparison_ax)) = plt.subplots(2, 2, figsize=(12, 8))
        
        self.stat_canvas = FigureCanvasTkAgg(self.stat_fig, tab_frame)
        self.stat_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Generate statistical plots
        self._create_statistical_plots()
    
    def _add_event_to_log(self, text_widget, event):
        """Add an event to the log text widget"""
        time = event['time']
        actor = event['actor_id']
        action = event['action_name']
        target = event['target_id']
        
        if event['success']:
            icon = "✅"
            status = "succeeded"
        elif event['detection']:
            icon = "🚨"
            status = "detected"
        else:
            icon = "❌"
            status = "failed"
        
        log_line = f"[{time:6.2f}] {icon} {actor} {status} {action} → {target}\n"
        text_widget.insert(tk.END, log_line)
    
    def _add_action_to_log(self, text_widget, action):
        """Add an action to the actor actions log"""
        time = action['time']
        run_id = action['run_id']
        action_name = action['action_name']
        target = action['target_id']
        
        if action['success']:
            icon = "✅"
            status = "SUCCESS"
        elif action['detection']:
            icon = "🚨"
            status = "DETECTED"
        else:
            icon = "❌"
            status = "FAILED"
        
        log_line = f"Run {run_id + 1} [{time:6.2f}] {icon} {status}: {action_name} → {target}\n"
        text_widget.insert(tk.END, log_line)
    
    def _on_run_selected(self, event=None):
        """Handle run selection from dropdown"""
        selected = self.run_selector.get()
        run_id = int(selected.split()[1]) - 1
        self._load_run_data(run_id)
    
    def _load_run_data(self, run_id: int):
        """Load data for a specific run"""
        # Clear existing stats
        for widget in self.run_stats_frame.winfo_children():
            widget.destroy()
        
        # Add stats
        events = self.runs_data[run_id]
        total_events = len(events)
        successful_events = len([e for e in events if e['success']])
        detections = len([e for e in events if e['detection']])
        
        tk.Label(self.run_stats_frame, text=f"Run {run_id + 1} Summary:", font=('Arial', 12, 'bold'),
                bg=self.bg_color, fg=self.button_fg).pack(side=tk.LEFT, padx=10)
        tk.Label(self.run_stats_frame, text=f"Total Events: {total_events}  |  Successful: {successful_events}  |  Detections: {detections}",
                bg=self.bg_color, fg=self.button_fg).pack(side=tk.LEFT, padx=20)
        
        # Clear and reload event log
        self.run_logs_text.config(state=tk.NORMAL)
        self.run_logs_text.delete(1.0, tk.END)
        
        for event in sorted(events, key=lambda x: x['time']):
            self._add_event_to_log(self.run_logs_text, event)
        
        self.run_logs_text.config(state=tk.DISABLED)
    
    def _on_actor_selected(self, event=None):
        """Handle actor selection from dropdown"""
        selected_actor = self.actor_selector.get()
        self._load_actor_data(selected_actor)
    
    def _load_actor_data(self, actor_id: str):
        """Load data for a specific actor"""
        # Clear existing content
        for widget in self.actor_content_frame.winfo_children():
            widget.destroy()
        
        # Recreate actor tab content within the content frame
        paned = tk.PanedWindow(self.actor_content_frame, orient=tk.VERTICAL, bg=self.bg_color)
        paned.pack(fill=tk.BOTH, expand=True)
        
        # Actions section
        actions_frame = tk.Frame(paned, bg=self.bg_color, relief=tk.RAISED, bd=1)
        paned.add(actions_frame, minsize=200)
        
        tk.Label(actions_frame, text=f"{actor_id} - Actions Timeline", 
                font=('Arial', 12, 'bold'), bg=self.bg_color, fg=self.button_fg).pack(pady=5)
        
        actions_text = tk.Text(actions_frame, height=15, wrap=tk.WORD, bg="#eaf1fb", fg=self.button_fg,
                              font=('Consolas', 9))
        actions_scrollbar = tk.Scrollbar(actions_frame, orient=tk.VERTICAL, command=actions_text.yview)
        actions_text.configure(yscrollcommand=actions_scrollbar.set)
        
        actions_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        actions_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
        
        # Populate actions
        actor_actions = sorted(self.actors_data[actor_id]['actions'], key=lambda x: (x['run_id'], x['time']))
        for action in actor_actions:
            self._add_action_to_log(actions_text, action)
        
        actions_text.config(state=tk.DISABLED)
        
        # Economics section
        economics_frame = tk.Frame(paned, bg=self.bg_color, relief=tk.RAISED, bd=1)
        paned.add(economics_frame, minsize=200)
        
        tk.Label(economics_frame, text=f"{actor_id} - Economic Impact", 
                font=('Arial', 12, 'bold'), bg=self.bg_color, fg=self.button_fg).pack(pady=5)
        
        # Economics content
        economics_content = tk.Text(economics_frame, height=10, wrap=tk.WORD, bg="#eaf1fb", fg=self.button_fg,
                                   font=('Consolas', 10))
        economics_content.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Display economics data
        economics = self.actors_data[actor_id]['economics']
        economics_content.insert(tk.END, f"TOTAL ECONOMIC IMPACT\n")
        economics_content.insert(tk.END, f"{'='*40}\n")
        economics_content.insert(tk.END, f"Total Cost:   ${economics['total_cost']:,.2f}\n")
        economics_content.insert(tk.END, f"Total Gain:   ${economics['total_gain']:,.2f}\n")
        economics_content.insert(tk.END, f"Total Damage: ${economics['total_damage']:,.2f}\n")
        economics_content.insert(tk.END, f"Net Profit:   ${economics['total_gain'] - economics['total_cost']:,.2f}\n\n")
        
        economics_content.insert(tk.END, f"PER-RUN BREAKDOWN\n")
        economics_content.insert(tk.END, f"{'='*40}\n")
        for run_id, run_data in economics['per_run'].items():
            economics_content.insert(tk.END, f"Run {run_id + 1}:\n")
            economics_content.insert(tk.END, f"  Cost:   ${run_data['cost']:,.2f}\n")
            economics_content.insert(tk.END, f"  Gain:   ${run_data['gain']:,.2f}\n")
            economics_content.insert(tk.END, f"  Damage: ${run_data['damage']:,.2f}\n")
            economics_content.insert(tk.END, f"  Profit: ${run_data['gain'] - run_data['cost']:,.2f}\n\n")
        
        economics_content.config(state=tk.DISABLED)
    
    def _update_economics_view(self, actor_id: str, parent_frame):
        """Update economics view based on toggle selection"""
        # This is used for individual actor tabs, not dropdown version
        # For now, just placeholder - we can enhance this later
        pass
    
    def _create_statistical_plots(self):
        """Create violin plots and statistical analysis"""
        try:
            # Get simulation results for analysis
            simulation_results = analyze_simulation_results(self.all_histories)
            
            if not simulation_results:
                # No data to plot
                for ax in [self.damage_ax, self.cost_ax, self.gain_ax, self.comparison_ax]:
                    ax.text(0.5, 0.5, 'No data available', transform=ax.transAxes, 
                           ha='center', va='center')
                self.stat_canvas.draw()
                return
            
            # Damage distribution violin plot
            damages = [r.get('total_damage', 0) for r in simulation_results]
            if damages and any(d > 0 for d in damages):
                parts = self.damage_ax.violinplot([damages], showmeans=True, showmedians=True)
                for pc in parts['bodies']:
                    pc.set_facecolor('#d62728')
                    pc.set_alpha(0.7)
                self.damage_ax.set_title('Damage Distribution')
                self.damage_ax.set_ylabel('Damage ($)')
                self.damage_ax.set_xticks([1])
                self.damage_ax.set_xticklabels(['All Runs'])
                self.damage_ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
            
            # Cost analysis
            all_costs = []
            for actor_data in self.actors_data.values():
                all_costs.append(actor_data['economics']['total_cost'])
            
            if all_costs and any(c > 0 for c in all_costs):
                parts = self.cost_ax.violinplot([all_costs], showmeans=True, showmedians=True)
                for pc in parts['bodies']:
                    pc.set_facecolor('#ff7f0e')
                    pc.set_alpha(0.7)
                self.cost_ax.set_title('Cost Distribution')
                self.cost_ax.set_ylabel('Cost ($)')
                self.cost_ax.set_xticks([1])
                self.cost_ax.set_xticklabels(['All Actors'])
                self.cost_ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
            
            # Gain analysis
            all_gains = []
            for actor_data in self.actors_data.values():
                if actor_data['economics']['total_gain'] > 0:  # Only attackers
                    all_gains.append(actor_data['economics']['total_gain'])
            
            if all_gains and any(g > 0 for g in all_gains):
                parts = self.gain_ax.violinplot([all_gains], showmeans=True, showmedians=True)
                for pc in parts['bodies']:
                    pc.set_facecolor('#2ca02c')
                    pc.set_alpha(0.7)
                self.gain_ax.set_title('Attacker Gains Distribution')
                self.gain_ax.set_ylabel('Gains ($)')
                self.gain_ax.set_xticks([1])
                self.gain_ax.set_xticklabels(['Attackers'])
                self.gain_ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
            
            # Comparison plot: Success rates by actor type
            attacker_success = []
            defender_success = []
            
            for actor_id, actor_data in self.actors_data.items():
                actions = actor_data['actions']
                if actions:
                    success_rate = len([a for a in actions if a['success']]) / len(actions)
                    if 'attacker' in actor_id.lower():
                        attacker_success.append(success_rate)
                    else:
                        defender_success.append(success_rate)
            
            success_data = []
            labels = []
            if attacker_success:
                success_data.append(attacker_success)
                labels.append('Attackers')
            if defender_success:
                success_data.append(defender_success)
                labels.append('Defenders')
            
            if success_data:
                parts = self.comparison_ax.violinplot(success_data, showmeans=True, showmedians=True)
                colors = ['red', 'blue']
                for i, pc in enumerate(parts['bodies']):
                    pc.set_facecolor(colors[i % len(colors)])
                    pc.set_alpha(0.7)
                
                self.comparison_ax.set_title('Success Rate Comparison')
                self.comparison_ax.set_ylabel('Success Rate')
                self.comparison_ax.set_xticks(range(1, len(labels) + 1))
                self.comparison_ax.set_xticklabels(labels)
                self.comparison_ax.set_ylim(0, 1)
            
            plt.tight_layout()
            self.stat_canvas.draw()
            
        except Exception as e:
            # Error handling - show error message in plots
            for ax in [self.damage_ax, self.cost_ax, self.gain_ax, self.comparison_ax]:
                ax.text(0.5, 0.5, f'Error creating plots:\n{str(e)}', 
                       transform=ax.transAxes, ha='center', va='center')
            self.stat_canvas.draw()
    
    def _on_close(self):
        """Handle window close"""
        try:
            plt.close('all')
        except:
            pass
        self.window.destroy()
