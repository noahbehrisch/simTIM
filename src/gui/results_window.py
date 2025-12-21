import tkinter as tk
from tkinter import ttk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from src.visualization import ViolinPlotEngine, analyze_simulation_results

class ResultsWindow:

    def __init__(self, parent, all_histories, theme_colors):
        self.parent = parent
        self.all_histories = all_histories
        self.bg_color = theme_colors['bg_color']
        self.button_fg = theme_colors['button_fg']
        self.window = tk.Toplevel(parent)
        self.window.title('Comprehensive Simulation Results')
        self.window.geometry('1800x1200')
        self.window.configure(bg=self.bg_color)
        self._create_interface()

    def _create_interface(self):
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill=tk.BOTH, expand=True)
        self._create_event_logs_tab(notebook)
        self._create_detailed_analysis_tab(notebook)
        self._create_visualization_tabs(notebook)
        self.window.protocol('WM_DELETE_WINDOW', self._on_close)

    def _create_event_logs_tab(self, notebook):
        logs_frame = tk.Frame(notebook, bg=self.bg_color)
        logs_text = tk.Text(logs_frame, wrap=tk.WORD, bg='#eaf1fb', fg=self.button_fg, state=tk.NORMAL)
        scrollbar = tk.Scrollbar(logs_frame, orient='vertical', command=logs_text.yview)
        logs_text.configure(yscrollcommand=scrollbar.set)
        logs_text.pack(side='left', expand=True, fill=tk.BOTH, padx=(10, 0), pady=10)
        scrollbar.pack(side='right', fill='y', padx=(0, 10), pady=10)
        notebook.add(logs_frame, text='Event Logs')
        logs_text.config(state=tk.NORMAL)
        logs_text.delete(1.0, tk.END)
        for run_index, history in enumerate(self.all_histories, start=1):
            logs_text.insert(tk.END, f'=== Simulation Run {run_index} ===\n')
            event_count = 0
            for entry in history:
                if hasattr(entry, 'time') and hasattr(entry, 'event_type') and hasattr(entry, 'data'):
                    time = entry.time
                    event_type = entry.event_type
                    data = entry.data
                elif isinstance(entry, (list, tuple)) and len(entry) >= 3:
                    time, event_type, data = entry[:3]
                else:
                    logs_text.insert(tk.END, f'  {entry}\n')
                    continue
                if event_type == 'start_action':
                    actor_id = data.get('actor', {}).id if hasattr(data.get('actor', {}), 'id') else 'Unknown'
                    action_name = data.get('action', {}).name if hasattr(data.get('action', {}), 'name') else 'Unknown'
                    target_id = data.get('target', {}).id if hasattr(data.get('target', {}), 'id') else 'Unknown'
                    logs_text.insert(tk.END, f'[{time:6.2f}] {actor_id} starts {action_name} on {target_id}\n')
                elif event_type == 'action_succeeded':
                    actor_id = data.get('actor', {}).id if hasattr(data.get('actor', {}), 'id') else 'Unknown'
                    action_name = data.get('action', {}).name if hasattr(data.get('action', {}), 'name') else 'Unknown'
                    logs_text.insert(tk.END, f'[{time:6.2f}] ✓ {actor_id} completed {action_name}\n')
                elif event_type == 'action_failed':
                    actor_id = data.get('actor', {}).id if hasattr(data.get('actor', {}), 'id') else 'Unknown'
                    action_name = data.get('action', {}).name if hasattr(data.get('action', {}), 'name') else 'Unknown'
                    logs_text.insert(tk.END, f'[{time:6.2f}] ✗ {actor_id} failed {action_name}\n')
                elif event_type == 'attack_detected':
                    detected_actor = data.get('detected_actor', {}).id if hasattr(data.get('detected_actor', {}), 'id') else 'Unknown'
                    detected_action = data.get('detected_action', {}).name if hasattr(data.get('detected_action', {}), 'name') else 'Unknown'
                    logs_text.insert(tk.END, f'[{time:6.2f}] 🚨 Detected: {detected_actor} performing {detected_action}\n')
                elif event_type == 'action_interrupted':
                    reason = data.get('reason', 'unknown')
                    actor_id = data.get('actor', {}).id if hasattr(data.get('actor', {}), 'id') else 'Unknown'
                    logs_text.insert(tk.END, f'[{time:6.2f}] ⚠ {actor_id} action interrupted ({reason})\n')
                else:
                    logs_text.insert(tk.END, f'[{time:6.2f}] {event_type}\n')
                event_count += 1
            logs_text.insert(tk.END, f'Total events in run {run_index}: {event_count}\n\n')
        logs_text.config(state=tk.DISABLED)

    def _create_detailed_analysis_tab(self, notebook):
        analysis_frame = tk.Frame(notebook, bg=self.bg_color)
        analysis_canvas = tk.Canvas(analysis_frame, bg=self.bg_color)
        scrollbar_analysis = tk.Scrollbar(analysis_frame, orient='vertical', command=analysis_canvas.yview)
        scrollable_frame = tk.Frame(analysis_canvas, bg=self.bg_color)
        scrollable_frame.bind('<Configure>', lambda e: analysis_canvas.configure(scrollregion=analysis_canvas.bbox('all')))
        analysis_canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')
        analysis_canvas.configure(yscrollcommand=scrollbar_analysis.set)
        analysis_canvas.pack(side='left', fill='both', expand=True, padx=(10, 0), pady=10)
        scrollbar_analysis.pack(side='right', fill='y', padx=(0, 10), pady=10)
        notebook.add(analysis_frame, text='Detailed Analysis')
        self._create_detailed_analysis(scrollable_frame)

    def _create_detailed_analysis(self, parent_frame):
        title_label = tk.Label(parent_frame, text='Comprehensive Simulation Analysis', bg=self.bg_color, fg=self.button_fg, font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 20))
        for run_idx, history in enumerate(self.all_histories, 1):
            run_frame = tk.Frame(parent_frame, bg='#f0f8ff', relief='ridge', bd=2)
            run_frame.pack(fill='x', padx=10, pady=5)
            run_header = tk.Label(run_frame, text=f'Simulation Run {run_idx}', bg='#f0f8ff', fg=self.button_fg, font=('Arial', 14, 'bold'))
            run_header.pack(pady=5)
            attacker_stats = {}
            defender_stats = {}
            node_compromises = {}
            attack_timeline = []
            defense_timeline = []
            for event in history:
                if hasattr(event, 'time') and hasattr(event, 'event_type') and hasattr(event, 'data'):
                    time, event_type, data = (event.time, event.event_type, event.data)
                elif isinstance(event, (list, tuple)) and len(event) >= 3:
                    time, event_type, data = event[:3]
                else:
                    continue
                if event_type in ['start_action', 'action_succeeded', 'action_failed']:
                    actor = data.get('actor')
                    action = data.get('action')
                    target = data.get('target')
                    if actor and hasattr(actor, 'id'):
                        actor_id = actor.id
                        if hasattr(actor, 'is_attacker') and actor.is_attacker:
                            if actor_id not in attacker_stats:
                                attacker_stats[actor_id] = {'actions_attempted': 0, 'actions_succeeded': 0, 'actions_failed': 0, 'targets_attacked': set(), 'total_gain': 0, 'total_cost': 0, 'attack_details': []}
                            if event_type == 'start_action':
                                attacker_stats[actor_id]['actions_attempted'] += 1
                                if target and hasattr(target, 'id'):
                                    attacker_stats[actor_id]['targets_attacked'].add(target.id)
                            elif event_type == 'action_succeeded':
                                attacker_stats[actor_id]['actions_succeeded'] += 1
                                if action and hasattr(action, 'cost'):
                                    attacker_stats[actor_id]['total_cost'] += action.cost
                                estimated_gain = 0
                                if action and hasattr(action, 'name'):
                                    if 'exploit' in action.name.lower():
                                        estimated_gain = 300
                                    elif 'scan' in action.name.lower():
                                        estimated_gain = 50
                                    elif 'reconnaissance' in action.name.lower():
                                        estimated_gain = 100
                                attacker_stats[actor_id]['total_gain'] += estimated_gain
                                attack_detail = {'time': time, 'action': action.name if action and hasattr(action, 'name') else 'Unknown', 'target': target.id if target and hasattr(target, 'id') else 'Unknown', 'result': 'SUCCESS', 'gain': estimated_gain}
                                attacker_stats[actor_id]['attack_details'].append(attack_detail)
                                attack_timeline.append(attack_detail)
                                if target and hasattr(target, 'id'):
                                    if target.id not in node_compromises:
                                        node_compromises[target.id] = {'first_compromise_time': time, 'compromise_count': 0, 'compromising_attackers': set()}
                                    node_compromises[target.id]['compromise_count'] += 1
                                    node_compromises[target.id]['compromising_attackers'].add(actor_id)
                            elif event_type == 'action_failed':
                                attacker_stats[actor_id]['actions_failed'] += 1
                                attack_detail = {'time': time, 'action': action.name if action and hasattr(action, 'name') else 'Unknown', 'target': target.id if target and hasattr(target, 'id') else 'Unknown', 'result': 'FAILED', 'gain': 0}
                                attacker_stats[actor_id]['attack_details'].append(attack_detail)
                        elif hasattr(actor, 'is_defender') and actor.is_defender:
                            if actor_id not in defender_stats:
                                defender_stats[actor_id] = {'actions_attempted': 0, 'actions_succeeded': 0, 'defensive_actions': []}
                            if event_type == 'start_action':
                                defender_stats[actor_id]['actions_attempted'] += 1
                            elif event_type == 'action_succeeded':
                                defender_stats[actor_id]['actions_succeeded'] += 1
                                defense_detail = {'time': time, 'action': action.name if action and hasattr(action, 'name') else 'Unknown', 'target': target.id if target and hasattr(target, 'id') else 'Unknown'}
                                defender_stats[actor_id]['defensive_actions'].append(defense_detail)
                                defense_timeline.append(defense_detail)
            if attacker_stats:
                attacker_frame = tk.Frame(run_frame, bg='#ffe6e6', relief='groove', bd=1)
                attacker_frame.pack(fill='x', padx=10, pady=5)
                tk.Label(attacker_frame, text='🔴 Attacker Performance Analysis', bg='#ffe6e6', fg=self.button_fg, font=('Arial', 12, 'bold')).pack(pady=5)
                for attacker_id, stats in attacker_stats.items():
                    success_rate = stats['actions_succeeded'] / max(stats['actions_attempted'], 1) * 100
                    net_profit = stats['total_gain'] - stats['total_cost']
                    attacker_text = tk.Text(attacker_frame, height=8, bg='#fff5f5', fg=self.button_fg, wrap=tk.WORD)
                    attacker_text.pack(fill='x', padx=10, pady=5)
                    attacker_text.insert(tk.END, f'👤 Attacker: {attacker_id}\n')
                    attacker_text.insert(tk.END, f'═══════════════════════════════════════\n')
                    attacker_text.insert(tk.END, f"Actions Attempted: {stats['actions_attempted']}\n")
                    attacker_text.insert(tk.END, f"✅ Actions Succeeded: {stats['actions_succeeded']}\n")
                    attacker_text.insert(tk.END, f"❌ Actions Failed: {stats['actions_failed']}\n")
                    attacker_text.insert(tk.END, f'🎯 Success Rate: {success_rate:.1f}%\n')
                    attacker_text.insert(tk.END, f"🏢 Unique Targets: {len(stats['targets_attacked'])}\n")
                    attacker_text.insert(tk.END, f"💰 Total Gain: ${stats['total_gain']:,.2f}\n")
                    attacker_text.insert(tk.END, f"💸 Total Cost: ${stats['total_cost']:,.2f}\n")
                    attacker_text.insert(tk.END, f'Net Profit: ${net_profit:,.2f}\n\n')
                    attacker_text.insert(tk.END, f'🕒 Attack Timeline:\n')
                    for detail in sorted(stats['attack_details'], key=lambda x: x['time']):
                        status_icon = '✅' if detail['result'] == 'SUCCESS' else '❌'
                        attacker_text.insert(tk.END, f"  [{detail['time']:6.2f}] {status_icon} {detail['action']} → {detail['target']} (${detail['gain']})\n")
                    attacker_text.config(state=tk.DISABLED)
            if defender_stats:
                defender_frame = tk.Frame(run_frame, bg='#e6ffe6', relief='groove', bd=1)
                defender_frame.pack(fill='x', padx=10, pady=5)
                tk.Label(defender_frame, text='🟢 Defender Performance Analysis', bg='#e6ffe6', fg=self.button_fg, font=('Arial', 12, 'bold')).pack(pady=5)
                for defender_id, stats in defender_stats.items():
                    success_rate = stats['actions_succeeded'] / max(stats['actions_attempted'], 1) * 100
                    defender_text = tk.Text(defender_frame, height=6, bg='#f5fff5', fg=self.button_fg, wrap=tk.WORD)
                    defender_text.pack(fill='x', padx=10, pady=5)
                    defender_text.insert(tk.END, f'Defender: {defender_id}\n')
                    defender_text.insert(tk.END, f'═══════════════════════════════════════\n')
                    defender_text.insert(tk.END, f"Actions Attempted: {stats['actions_attempted']}\n")
                    defender_text.insert(tk.END, f"✅ Actions Succeeded: {stats['actions_succeeded']}\n")
                    defender_text.insert(tk.END, f'🎯 Success Rate: {success_rate:.1f}%\n\n')
                    defender_text.insert(tk.END, f'🕒 Defense Timeline:\n')
                    for detail in sorted(stats['defensive_actions'], key=lambda x: x['time']):
                        defender_text.insert(tk.END, f"  [{detail['time']:6.2f}] {detail['action']} → {detail['target']}\n")
                    defender_text.config(state=tk.DISABLED)
            if node_compromises:
                node_frame = tk.Frame(run_frame, bg='#e6f3ff', relief='groove', bd=1)
                node_frame.pack(fill='x', padx=10, pady=5)
                tk.Label(node_frame, text='Node Compromise Analysis', bg='#e6f3ff', fg=self.button_fg, font=('Arial', 12, 'bold')).pack(pady=5)
                node_text = tk.Text(node_frame, height=6, bg='#f5faff', fg=self.button_fg, wrap=tk.WORD)
                node_text.pack(fill='x', padx=10, pady=5)
                node_text.insert(tk.END, f'🎯 Node Compromise Summary:\n')
                node_text.insert(tk.END, f'═══════════════════════════════════════\n')
                for node_id, compromise_info in sorted(node_compromises.items(), key=lambda x: x[1]['first_compromise_time']):
                    node_text.insert(tk.END, f'{node_id}:\n')
                    node_text.insert(tk.END, f"  ⏰ First Compromise: {compromise_info['first_compromise_time']:.2f}s\n")
                    node_text.insert(tk.END, f"  🔢 Total Compromises: {compromise_info['compromise_count']}\n")
                    node_text.insert(tk.END, f"  👥 Attackers: {', '.join(compromise_info['compromising_attackers'])}\n\n")
                node_text.config(state=tk.DISABLED)
            summary_frame = tk.Frame(run_frame, bg='#fff9e6', relief='groove', bd=1)
            summary_frame.pack(fill='x', padx=10, pady=5)
            tk.Label(summary_frame, text='Run Summary', bg='#fff9e6', fg=self.button_fg, font=('Arial', 12, 'bold')).pack(pady=5)
            summary_text = tk.Text(summary_frame, height=4, bg='#fffef5', fg=self.button_fg, wrap=tk.WORD)
            summary_text.pack(fill='x', padx=10, pady=5)
            total_attacks = sum((stats['actions_succeeded'] for stats in attacker_stats.values()))
            total_defenses = sum((stats['actions_succeeded'] for stats in defender_stats.values()))
            total_profit = sum((stats['total_gain'] - stats['total_cost'] for stats in attacker_stats.values()))
            summary_text.insert(tk.END, f'🎯 Total Successful Attacks: {total_attacks}\n')
            summary_text.insert(tk.END, f'Total Successful Defenses: {total_defenses}\n')
            summary_text.insert(tk.END, f'Nodes Compromised: {len(node_compromises)}\n')
            summary_text.insert(tk.END, f'💰 Total Attacker Profit: ${total_profit:,.2f}')
            summary_text.config(state=tk.DISABLED)

    def _create_visualization_tabs(self, notebook):
        try:
            simulation_results = analyze_simulation_results(self.all_histories)
            if simulation_results:
                plot_frame = tk.Frame(notebook, bg=self.bg_color)
                notebook.add(plot_frame, text='Economic Analysis')
                plotter = ViolinPlotEngine()
                fig = plotter.create_economic_comparison_plot(simulation_results, 'TIM Simulation Results: Economic Impact')
                canvas = FigureCanvasTkAgg(fig, master=plot_frame)
                canvas.draw()
                canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
                summary_frame = tk.Frame(notebook, bg=self.bg_color)
                notebook.add(summary_frame, text='Summary')
                summary_text = tk.Text(summary_frame, wrap=tk.WORD, bg='#eaf1fb', fg=self.button_fg)
                summary_text.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
                total_damage = sum((r.get('total_damage', 0) for r in simulation_results))
                total_gains = sum((r.get('total_attacker_gains', 0) for r in simulation_results))
                total_costs = sum((r.get('total_costs', 0) for r in simulation_results))
                avg_damage = total_damage / len(simulation_results) if simulation_results else 0
                summary_text.insert(tk.END, f'Simulation Summary\n')
                summary_text.insert(tk.END, f'==================\n\n')
                summary_text.insert(tk.END, f'Number of runs: {len(simulation_results)}\n')
                summary_text.insert(tk.END, f'Total system damage: ${total_damage:,.2f}\n')
                summary_text.insert(tk.END, f'Average damage per run: ${avg_damage:,.2f}\n')
                summary_text.insert(tk.END, f'Total attacker gains: ${total_gains:,.2f}\n')
                summary_text.insert(tk.END, f'Total action costs: ${total_costs:,.2f}\n')
                summary_text.insert(tk.END, f'Net attacker benefit: ${total_gains - total_costs:,.2f}\n')
                summary_text.config(state=tk.DISABLED)
            else:
                plot_frame = tk.Frame(notebook, bg=self.bg_color)
                tk.Label(plot_frame, text='No simulation data available for visualization', bg=self.bg_color, fg=self.button_fg).pack(expand=True)
                notebook.add(plot_frame, text='Visualization')
        except Exception as e:
            error_frame = tk.Frame(notebook, bg=self.bg_color)
            tk.Label(error_frame, text=f'Error creating visualization: {str(e)}', bg=self.bg_color, fg='red').pack(expand=True)
            notebook.add(error_frame, text='Visualization Error')

    def _on_close(self):
        try:
            plt.close('all')
        except:
            pass
        self.window.destroy()