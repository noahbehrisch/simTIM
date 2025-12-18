import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import random
import math
import os
import glob
from src.gui.theme import Theme

class NetworkCreator(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.theme = Theme()
        
        self.title("Network Creator")
        self.geometry("1200x800")
        self.configure(bg=self.theme.COLORS['bg_primary'])
        
        self.nodes = {}
        self.links = []
        self.selected_node = None
        self.selected_nodes = []
        self.link_start_node = None
        self.link_mode = False
        self.right_click_link_start = None
        self.help_visible = False
        self.dragging_node = None
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.selection_box_active = False
        self.selection_box_start = None
        
        self.create_widgets()
        self.transient(parent)
        
    def create_widgets(self):
        main_frame = tk.Frame(self, bg=self.theme.COLORS['bg_primary'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        toolbar_frame = tk.Frame(main_frame, bg=self.theme.COLORS['bg_sidebar'])
        toolbar_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 5))
        
        tk.Button(
            toolbar_frame,
            text="Add Node",
            command=self.add_node_dialog,
            bg=self.theme.COLORS['accent_secondary'],
            fg=self.theme.COLORS['text_primary'],
            font=self.theme.FONTS['body']
        ).pack(side=tk.LEFT, padx=5, pady=5)
        
        self.add_link_button = tk.Button(
            toolbar_frame,
            text="Add Link",
            command=self.start_link_creation,
            bg=self.theme.COLORS['accent_secondary'],
            fg=self.theme.COLORS['text_primary'],
            font=self.theme.FONTS['body'],
            state=tk.DISABLED
        )
        self.add_link_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        tk.Button(
            toolbar_frame,
            text="Delete Selected",
            command=self.delete_selected,
            bg=self.theme.COLORS['danger'],
            fg='white',
            font=self.theme.FONTS['body']
        ).pack(side=tk.LEFT, padx=5, pady=5)
        
        tk.Button(
            toolbar_frame,
            text="Generate Random",
            command=self.generate_random_dialog,
            bg=self.theme.COLORS['info'],
            fg='white',
            font=self.theme.FONTS['body']
        ).pack(side=tk.LEFT, padx=5, pady=5)
        
        tk.Button(
            toolbar_frame,
            text="Help",
            command=self.show_help,
            bg=self.theme.COLORS['warning'],
            fg='white',
            font=self.theme.FONTS['body']
        ).pack(side=tk.LEFT, padx=5, pady=5)
        
        tk.Button(
            toolbar_frame,
            text="Save Network",
            command=self.save_network,
            bg=self.theme.COLORS['success'],
            fg='white',
            font=self.theme.FONTS['body']
        ).pack(side=tk.RIGHT, padx=5, pady=5)
        
        tk.Button(
            toolbar_frame,
            text="Load Network",
            command=self.load_network,
            bg=self.theme.COLORS['accent_secondary'],
            fg=self.theme.COLORS['text_primary'],
            font=self.theme.FONTS['body']
        ).pack(side=tk.RIGHT, padx=5, pady=5)
        
        content_frame = tk.Frame(main_frame, bg=self.theme.COLORS['bg_primary'])
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        self.status_label = tk.Label(
            content_frame,
            text="Click 'Add Node' to create nodes, then 'Add Link' to connect them.",
            bg=self.theme.COLORS['bg_sidebar'],
            fg=self.theme.COLORS['text_primary'],
            font=self.theme.FONTS['body'],
            relief=tk.FLAT,
            padx=10,
            pady=5
        )
        self.status_label.pack(side=tk.TOP, fill=tk.X, pady=(0, 5))
        
        self.help_frame = tk.Frame(content_frame, bg=self.theme.COLORS['bg_secondary'])
        
        help_scroll = tk.Scrollbar(self.help_frame)
        help_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.help_text_widget = tk.Text(
            self.help_frame,
            wrap=tk.WORD,
            width=120,
            height=15,
            bg=self.theme.COLORS['bg_secondary'],
            fg=self.theme.COLORS['text_primary'],
            font=self.theme.FONTS['body'],
            padx=10,
            pady=10,
            yscrollcommand=help_scroll.set
        )
        self.help_text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        help_scroll.config(command=self.help_text_widget.yview)
        
        help_content = """Network Creator Help

Visual Indicators:
  • Red node = Exposed to Internet
"""
        
        self.help_text_widget.insert('1.0', help_content)
        self.help_text_widget.config(state=tk.DISABLED)
        
        self.canvas_frame = tk.Frame(content_frame, bg=self.theme.COLORS['bg_secondary'], relief=tk.SUNKEN, bd=2)
        self.canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        self.canvas = tk.Canvas(
            self.canvas_frame,
            bg='white',
            width=800,
            height=600
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Button-1>", self.canvas_click)
        self.canvas.bind("<B1-Motion>", self.canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.canvas_release)
        self.canvas.bind("<Button-3>", self.canvas_right_click)
        self.canvas.bind("<B3-Motion>", self.canvas_right_drag)
        self.canvas.bind("<ButtonRelease-3>", self.canvas_right_release)
        
        self.properties_frame = tk.Frame(content_frame, bg=self.theme.COLORS['bg_sidebar'], width=300)
        self.properties_frame.pack(side=tk.RIGHT, fill=tk.Y)
        self.properties_frame.pack_propagate(False)
        
        tk.Label(
            self.properties_frame,
            text="Network Properties",
            font=self.theme.FONTS['heading_medium'],
            bg=self.theme.COLORS['bg_sidebar'],
            fg=self.theme.COLORS['text_primary']
        ).pack(pady=10)
        
        self.properties_text = tk.Text(
            self.properties_frame,
            width=35,
            height=40,
            bg=self.theme.COLORS['bg_secondary'],
            fg=self.theme.COLORS['text_primary'],
            font=self.theme.FONTS['body_small']
        )
        self.properties_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.update_properties_display()
        self.update_button_states()
    
    def load_operating_systems(self):
        
        os_dir = "src/networks/node_properties/operating_systems"
        os_list = []
        for filepath in glob.glob(os.path.join(os_dir, "*.json")):
            try:
                with open(filepath, 'r') as f:
                    os_data = json.load(f)
                    os_list.append(os_data['name'])
            except Exception as e:
                print(f"Error loading {filepath}: {e}")
        
        priority_os = []
        other_os = []
        
        for os_name in sorted(os_list):
            if os_name == "Ubuntu":
                priority_os.insert(0, os_name)
            elif os_name == "Windows Server":
                priority_os.append(os_name)
            else:
                other_os.append(os_name)
        
        return priority_os + other_os
    
    def load_os_data(self, os_name):
        
        os_dir = "src/networks/node_properties/operating_systems"

        filename = os_name.replace(" ", "_") + ".json"
        filepath = os.path.join(os_dir, filename)
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading OS data for {os_name}: {e}")
            return {"name": os_name, "versions": []}
    
    def load_services(self):
        
        try:
            with open("src/networks/node_properties/services/services.json", 'r') as f:
                data = json.load(f)
                return data['services']
        except Exception as e:
            print(f"Error loading services: {e}")
            return []
    
    def load_assets(self):
        
        try:
            with open("src/networks/node_properties/assets/assets.json", 'r') as f:
                data = json.load(f)
                return data['assets']
        except Exception as e:
            print(f"Error loading assets: {e}")
            return []
    
    def load_categories(self):
        
        try:
            with open("src/networks/node_properties/categories/categories.json", 'r') as f:
                data = json.load(f)
                return data['categories']
        except Exception as e:
            print(f"Error loading categories: {e}")
            return []
    
    def update_button_states(self):
        if len(self.nodes) < 2:
            self.add_link_button.config(state=tk.DISABLED)
        else:
            self.add_link_button.config(state=tk.NORMAL)
    
    def show_help(self):
        if self.help_visible:
            self.help_frame.pack_forget()
            self.canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
            self.properties_frame.pack(side=tk.RIGHT, fill=tk.Y)
            self.help_visible = False
            self.status_label.config(
                text="Click 'Add Node' to create nodes, then 'Add Link' to connect them.",
                bg=self.theme.COLORS['bg_sidebar'],
                fg=self.theme.COLORS['text_primary'],
                justify=tk.LEFT,
                anchor='w'
            )
        else:
            self.canvas_frame.pack_forget()
            self.properties_frame.pack_forget()
            self.help_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=(0, 5))
            self.help_visible = True
            self.status_label.config(
                text="Help panel shown. Click 'Help' again to hide and return to editor.",
                bg='#fff3cd',
                fg='#856404',
                justify=tk.LEFT,
                anchor='w'
            )
    
    def add_node_dialog(self):
        dialog = tk.Toplevel(self)
        dialog.title("Add Node")
        dialog.geometry("1000x900")
        dialog.configure(bg=self.theme.COLORS['bg_primary'])
        dialog.transient(self)
        dialog.grab_set()
        
        canvas = tk.Canvas(dialog, bg=self.theme.COLORS['bg_primary'], highlightthickness=0)
        scrollbar = tk.Scrollbar(dialog, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.theme.COLORS['bg_primary'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True, padx=(20, 0), pady=20)
        scrollbar.pack(side="right", fill="y", padx=(0, 20), pady=20)
        
        def on_dialog_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        def on_dialog_mousewheel_linux(event):
            if event.num == 4:
                canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                canvas.yview_scroll(1, "units")
        
        dialog.bind("<MouseWheel>", on_dialog_mousewheel)
        dialog.bind("<Button-4>", on_dialog_mousewheel_linux)
        dialog.bind("<Button-5>", on_dialog_mousewheel_linux)
        
        form_frame = scrollable_frame
        
        form_frame.columnconfigure(1, weight=1)
        
        fields = {}
        current_row = 0
        
        tk.Label(form_frame, text="Node ID:", bg=self.theme.COLORS['bg_primary'], fg=self.theme.COLORS['text_primary']).grid(row=current_row, column=0, sticky='w', pady=5, padx=5)
        fields['id'] = tk.Entry(form_frame)
        fields['id'].grid(row=current_row, column=1, sticky='ew', pady=5, padx=5)
        fields['id'].insert(0, f"node_{len(self.nodes) + 1}")
        current_row += 1
        
        tk.Label(form_frame, text="Name:", bg=self.theme.COLORS['bg_primary'], fg=self.theme.COLORS['text_primary']).grid(row=current_row, column=0, sticky='w', pady=5, padx=5)
        fields['name'] = tk.Entry(form_frame)
        fields['name'].grid(row=current_row, column=1, sticky='ew', pady=5, padx=5)
        current_row += 1
        
        tk.Label(form_frame, text="Operating System:", bg=self.theme.COLORS['bg_primary'], fg=self.theme.COLORS['text_primary']).grid(row=current_row, column=0, sticky='w', pady=5, padx=5)
        os_list = self.load_operating_systems()
        fields['os'] = ttk.Combobox(form_frame, values=os_list, state='readonly')
        fields['os'].grid(row=current_row, column=1, sticky='ew', pady=5, padx=5)
        if os_list:

            if 'Ubuntu' in os_list:
                fields['os'].set('Ubuntu')
            else:
                fields['os'].set(os_list[0])
        current_row += 1
        
        tk.Label(form_frame, text="OS Version:", bg=self.theme.COLORS['bg_primary'], fg=self.theme.COLORS['text_primary']).grid(row=current_row, column=0, sticky='w', pady=5, padx=5)
        fields['version'] = ttk.Combobox(form_frame, state='readonly')
        fields['version'].grid(row=current_row, column=1, sticky='ew', pady=5, padx=5)
        current_row += 1
        
        tk.Label(form_frame, text="Category:", bg=self.theme.COLORS['bg_primary'], fg=self.theme.COLORS['text_primary']).grid(row=current_row, column=0, sticky='w', pady=5, padx=5)
        categories = self.load_categories()
        fields['category'] = ttk.Combobox(form_frame, values=categories, state='readonly')
        fields['category'].grid(row=current_row, column=1, sticky='ew', pady=5, padx=5)
        if categories:
            fields['category'].set(categories[0])
        current_row += 1
        
        # tk.Label(form_frame, text="Services:", bg=self.theme.COLORS['bg_primary'], fg=self.theme.COLORS['text_primary'], font=self.theme.FONTS['heading_small']).grid(row=current_row, column=0, sticky='nw', pady=10, padx=5)
        # 
        # services_outer_frame = tk.Frame(form_frame, bg=self.theme.COLORS['bg_secondary'], relief=tk.SUNKEN, bd=1)
        # services_outer_frame.grid(row=current_row, column=1, sticky='ew', pady=10, padx=5)
        # 
        # services_canvas = tk.Canvas(services_outer_frame, bg=self.theme.COLORS['bg_primary'], height=150, highlightthickness=0)
        # services_scrollbar = tk.Scrollbar(services_outer_frame, orient="vertical", command=services_canvas.yview)
        # services_inner_frame = tk.Frame(services_canvas, bg=self.theme.COLORS['bg_primary'])
        # 
        # services_inner_frame.bind(
        #     "<Configure>",
        #     lambda e: services_canvas.configure(scrollregion=services_canvas.bbox("all"))
        # )
        # 
        # services_canvas.create_window((0, 0), window=services_inner_frame, anchor="nw")
        # services_canvas.configure(yscrollcommand=services_scrollbar.set)
        # 
        # services_canvas.pack(side="left", fill="both", expand=True)
        # services_scrollbar.pack(side="right", fill="y")
        # 
        # def on_services_mousewheel(event):
        #     services_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        # def on_services_mousewheel_linux(event):
        #     if event.num == 4:
        #         services_canvas.yview_scroll(-1, "units")
        #     elif event.num == 5:
        #         services_canvas.yview_scroll(1, "units")
        # 
        # def bind_services_scroll(event):
        #     dialog.unbind("<MouseWheel>")
        #     dialog.unbind("<Button-4>")
        #     dialog.unbind("<Button-5>")
        #     dialog.bind("<MouseWheel>", on_services_mousewheel)
        #     dialog.bind("<Button-4>", on_services_mousewheel_linux)
        #     dialog.bind("<Button-5>", on_services_mousewheel_linux)
        # 
        # def unbind_services_scroll(event):
        #     dialog.unbind("<MouseWheel>")
        #     dialog.unbind("<Button-4>")
        #     dialog.unbind("<Button-5>")
        #     dialog.bind("<MouseWheel>", on_dialog_mousewheel)
        #     dialog.bind("<Button-4>", on_dialog_mousewheel_linux)
        #     dialog.bind("<Button-5>", on_dialog_mousewheel_linux)
        # 
        # services_outer_frame.bind("<Enter>", bind_services_scroll)
        # services_outer_frame.bind("<Leave>", unbind_services_scroll)
        # 
        # fields['services_vars'] = {}
        # for service in self.load_services():
        #     var = tk.BooleanVar(value=False)
        #     fields['services_vars'][service] = var
        #     tk.Checkbutton(services_inner_frame, text=service, variable=var, 
        #                   bg=self.theme.COLORS['bg_primary'], 
        #                   fg=self.theme.COLORS['text_primary'],
        #                   anchor='w').pack(fill='x', padx=5, pady=2)
        # current_row += 1
        
        fields['services_vars'] = {}
        
        tk.Label(form_frame, text="Vulnerabilities:", bg=self.theme.COLORS['bg_primary'], fg=self.theme.COLORS['text_primary'], font=self.theme.FONTS['heading_small']).grid(row=current_row, column=0, sticky='nw', pady=10, padx=5)
        
        vuln_outer_frame = tk.Frame(form_frame, bg=self.theme.COLORS['bg_secondary'], relief=tk.SUNKEN, bd=1)
        vuln_outer_frame.grid(row=current_row, column=1, sticky='ew', pady=10, padx=5)
        
        vuln_canvas = tk.Canvas(vuln_outer_frame, bg=self.theme.COLORS['bg_primary'], height=150, highlightthickness=0)
        vuln_scrollbar = tk.Scrollbar(vuln_outer_frame, orient="vertical", command=vuln_canvas.yview)
        fields['vuln_inner_frame'] = tk.Frame(vuln_canvas, bg=self.theme.COLORS['bg_primary'])
        
        fields['vuln_inner_frame'].bind(
            "<Configure>",
            lambda e: vuln_canvas.configure(scrollregion=vuln_canvas.bbox("all"))
        )
        
        vuln_canvas.create_window((0, 0), window=fields['vuln_inner_frame'], anchor="nw")
        vuln_canvas.configure(yscrollcommand=vuln_scrollbar.set)
        
        vuln_canvas.pack(side="left", fill="both", expand=True)
        vuln_scrollbar.pack(side="right", fill="y")
        
        def on_vuln_mousewheel(event):
            vuln_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        def on_vuln_mousewheel_linux(event):
            if event.num == 4:
                vuln_canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                vuln_canvas.yview_scroll(1, "units")
        
        def bind_vuln_scroll(event):
            dialog.unbind("<MouseWheel>")
            dialog.unbind("<Button-4>")
            dialog.unbind("<Button-5>")
            dialog.bind("<MouseWheel>", on_vuln_mousewheel)
            dialog.bind("<Button-4>", on_vuln_mousewheel_linux)
            dialog.bind("<Button-5>", on_vuln_mousewheel_linux)
        
        def unbind_vuln_scroll(event):
            dialog.unbind("<MouseWheel>")
            dialog.unbind("<Button-4>")
            dialog.unbind("<Button-5>")
            dialog.bind("<MouseWheel>", on_dialog_mousewheel)
            dialog.bind("<Button-4>", on_dialog_mousewheel_linux)
            dialog.bind("<Button-5>", on_dialog_mousewheel_linux)
        
        vuln_outer_frame.bind("<Enter>", bind_vuln_scroll)
        vuln_outer_frame.bind("<Leave>", unbind_vuln_scroll)
        
        fields['vuln_vars'] = {}
        current_row += 1
        
        tk.Label(form_frame, text="Assets:", bg=self.theme.COLORS['bg_primary'], fg=self.theme.COLORS['text_primary'], font=self.theme.FONTS['heading_small']).grid(row=current_row, column=0, sticky='nw', pady=10, padx=5)
        
        assets_outer_frame = tk.Frame(form_frame, bg=self.theme.COLORS['bg_secondary'], relief=tk.SUNKEN, bd=1)
        assets_outer_frame.grid(row=current_row, column=1, sticky='ew', pady=10, padx=5)
        
        assets_canvas = tk.Canvas(assets_outer_frame, bg=self.theme.COLORS['bg_primary'], height=150, highlightthickness=0)
        assets_scrollbar = tk.Scrollbar(assets_outer_frame, orient="vertical", command=assets_canvas.yview)
        assets_inner_frame = tk.Frame(assets_canvas, bg=self.theme.COLORS['bg_primary'])
        
        assets_inner_frame.bind(
            "<Configure>",
            lambda e: assets_canvas.configure(scrollregion=assets_canvas.bbox("all"))
        )
        
        assets_canvas.create_window((0, 0), window=assets_inner_frame, anchor="nw")
        assets_canvas.configure(yscrollcommand=assets_scrollbar.set)
        
        assets_canvas.pack(side="left", fill="both", expand=True)
        assets_scrollbar.pack(side="right", fill="y")
        
        def on_assets_mousewheel(event):
            assets_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        def on_assets_mousewheel_linux(event):
            if event.num == 4:
                assets_canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                assets_canvas.yview_scroll(1, "units")
        
        def bind_assets_scroll(event):
            dialog.unbind("<MouseWheel>")
            dialog.unbind("<Button-4>")
            dialog.unbind("<Button-5>")
            dialog.bind("<MouseWheel>", on_assets_mousewheel)
            dialog.bind("<Button-4>", on_assets_mousewheel_linux)
            dialog.bind("<Button-5>", on_assets_mousewheel_linux)
        
        def unbind_assets_scroll(event):
            dialog.unbind("<MouseWheel>")
            dialog.unbind("<Button-4>")
            dialog.unbind("<Button-5>")
            dialog.bind("<MouseWheel>", on_dialog_mousewheel)
            dialog.bind("<Button-4>", on_dialog_mousewheel_linux)
            dialog.bind("<Button-5>", on_dialog_mousewheel_linux)
        
        assets_outer_frame.bind("<Enter>", bind_assets_scroll)
        assets_outer_frame.bind("<Leave>", unbind_assets_scroll)
        
        fields['assets_vars'] = {}
        for asset in self.load_assets():
            var = tk.BooleanVar(value=False)
            fields['assets_vars'][asset] = var
            tk.Checkbutton(assets_inner_frame, text=asset, variable=var, 
                          bg=self.theme.COLORS['bg_primary'], 
                          fg=self.theme.COLORS['text_primary'],
                          anchor='w').pack(fill='x', padx=5, pady=2)
        current_row += 1
        
        fields['exposed'] = tk.BooleanVar(value=False)
        tk.Checkbutton(form_frame, text="Exposed to Internet", variable=fields['exposed'], bg=self.theme.COLORS['bg_primary'], fg=self.theme.COLORS['text_primary']).grid(row=current_row, column=0, columnspan=2, pady=10)
        current_row += 1
        
        def on_os_change(event=None):
            os_name = fields['os'].get()
            if not os_name:
                return
            
            os_data = self.load_os_data(os_name)
            versions = [v['version'] for v in os_data.get('versions', [])]
            fields['version']['values'] = versions
            if versions:
                fields['version'].set(versions[0])
                on_version_change()
            else:
                fields['version'].set('')

                for widget in fields['vuln_inner_frame'].winfo_children():
                    widget.destroy()
                fields['vuln_vars'] = {}
        
        def on_version_change(event=None):
            os_name = fields['os'].get()
            version = fields['version'].get()
            if not os_name or not version:
                return
            
            os_data = self.load_os_data(os_name)
            vulnerabilities = []
            for v in os_data.get('versions', []):
                if v['version'] == version:
                    vulnerabilities = v.get('vulnerabilities', [])
                    break
            
            for widget in fields['vuln_inner_frame'].winfo_children():
                widget.destroy()
            fields['vuln_vars'] = {}
            
            for vuln in vulnerabilities:
                var = tk.BooleanVar(value=False)
                fields['vuln_vars'][vuln] = var
                tk.Checkbutton(fields['vuln_inner_frame'], text=vuln, variable=var, 
                              bg=self.theme.COLORS['bg_primary'], 
                              fg=self.theme.COLORS['text_primary'],
                              anchor='w').pack(fill='x', padx=5, pady=2)
        
        fields['os'].bind('<<ComboboxSelected>>', on_os_change)
        fields['version'].bind('<<ComboboxSelected>>', on_version_change)
        
        on_os_change()
        
        def create_node():
            node_id = fields['id'].get().strip()
            if not node_id:
                messagebox.showerror("Error", "Node ID is required")
                return
            if node_id in self.nodes:
                messagebox.showerror("Error", f"Node {node_id} already exists")
                return
            
            services = [service for service, var in fields['services_vars'].items() if var.get()]
            
            vulnerabilities = [vuln for vuln, var in fields['vuln_vars'].items() if var.get()]
            
            assets = [asset for asset, var in fields['assets_vars'].items() if var.get()]
            
            x = random.randint(50, 750)
            y = random.randint(50, 550)
            
            self.nodes[node_id] = {
                'id': node_id,
                'name': fields['name'].get() or node_id,
                'x': x,
                'y': y,
                'software': {
                    'os': fields['os'].get(),
                    'version': fields['version'].get(),
                    'services': services
                },
                'vulnerabilities': vulnerabilities,
                'assets': assets,
                'category': fields['category'].get(),
                'properties': {
                    'exposed_to_internet': fields['exposed'].get()
                }
            }
            
            self.draw_network()
            self.update_properties_display()
            self.update_button_states()
            self.status_label.config(
                text=f"Node '{node_id}' added successfully. Total nodes: {len(self.nodes)}",
                bg=self.theme.COLORS['bg_sidebar'],
                fg=self.theme.COLORS['text_primary']
            )
            dialog.destroy()
        
        tk.Button(
            form_frame,
            text="Create Node",
            command=create_node,
            bg=self.theme.COLORS['success'],
            fg='white',
            font=self.theme.FONTS['body']
        ).grid(row=current_row, column=0, columnspan=2, pady=20)
    
    def start_link_creation(self):
        if len(self.nodes) < 2:
            return
        
        self.link_mode = True
        self.link_start_node = None
        self.status_label.config(
            text="LINK MODE: Click the first node, then click the second node. You can also right-click + drag.",
            bg='#fff3cd',
            fg='#856404'
        )
    
    def canvas_click(self, event):
        clicked_node = self.find_node_at(event.x, event.y)
        
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        
        if self.link_mode:
            if self.link_start_node is None:

                if clicked_node:
                    self.link_start_node = clicked_node
                    self.draw_network()

                    self.canvas.create_oval(
                        self.nodes[clicked_node]['x'] - 22,
                        self.nodes[clicked_node]['y'] - 22,
                        self.nodes[clicked_node]['x'] + 22,
                        self.nodes[clicked_node]['y'] + 22,
                        outline='red',
                        width=3,
                        tags='link_highlight'
                    )
                    self.status_label.config(
                        text=f"First node selected: {clicked_node}. Now click the second node.",
                        bg='#d1ecf1',
                        fg='#0c5460'
                    )
            else:

                if clicked_node and clicked_node != self.link_start_node:

                    link_exists = any(
                        (l['node1'] == self.link_start_node and l['node2'] == clicked_node) or
                        (l['node1'] == clicked_node and l['node2'] == self.link_start_node)
                        for l in self.links
                    )
                    
                    if link_exists:
                        self.status_label.config(
                            text=f"Link already exists between {self.link_start_node} and {clicked_node}.",
                            bg='#f8d7da',
                            fg='#721c24'
                        )
                    else:
                        self.links.append({
                            'node1': self.link_start_node,
                            'node2': clicked_node,
                            'bidirectional': True
                        })
                        self.draw_network()
                        self.update_properties_display()
                        self.update_button_states()
                        self.status_label.config(
                            text=f"Link created: {self.link_start_node} ↔ {clicked_node}",
                            bg=self.theme.COLORS['bg_sidebar'],
                            fg=self.theme.COLORS['text_primary']
                        )

                    self.link_mode = False
                    self.link_start_node = None
                elif clicked_node == self.link_start_node:
                    self.status_label.config(
                        text="Cannot create link to the same node. Click a different node.",
                        bg='#f8d7da',
                        fg='#721c24'
                    )
                else:

                    self.link_mode = False
                    self.link_start_node = None
                    self.draw_network()
                    self.status_label.config(
                        text="Link creation cancelled.",
                        bg=self.theme.COLORS['bg_sidebar'],
                        fg=self.theme.COLORS['text_primary']
                    )
        else:

            if clicked_node:
                self.selected_node = clicked_node
                self.selected_nodes = [clicked_node]
                self.dragging_node = clicked_node
                self.selection_box_active = False
                self.draw_network()
                self.update_button_states()
                self.status_label.config(
                    text=f"Node '{clicked_node}' selected. Drag to move or click 'Delete Selected' to remove.",
                    bg='#d1ecf1',
                    fg='#0c5460'
                )
            else:

                self.selected_node = None
                self.selected_nodes = []
                self.dragging_node = None
                self.selection_box_active = True
                self.selection_box_start = (event.x, event.y)
                self.draw_network()
                self.update_button_states()
                self.status_label.config(
                    text="Drag to create selection box...",
                    bg='#fff3cd',
                    fg='#856404'
                )
    
    def find_node_at(self, x, y):
        for node_id, node in self.nodes.items():
            dx = node['x'] - x
            dy = node['y'] - y
            if dx*dx + dy*dy <= 400:
                return node_id
        return None
    
    def canvas_drag(self, event):

        if self.selection_box_active and self.selection_box_start:

            self.draw_network()
            x1, y1 = self.selection_box_start
            self.canvas.create_rectangle(
                x1, y1, event.x, event.y,
                outline='blue',
                width=2,
                dash=(4, 4),
                tags='selection_box'
            )

        elif not self.link_mode and self.dragging_node:

            dx = event.x - self.drag_start_x
            dy = event.y - self.drag_start_y
            
            if abs(dx) > 3 or abs(dy) > 3:

                self.nodes[self.dragging_node]['x'] = event.x
                self.nodes[self.dragging_node]['y'] = event.y
                
                self.draw_network()
                
                self.drag_start_x = event.x
                self.drag_start_y = event.y
    
    def canvas_release(self, event):

        if self.selection_box_active and self.selection_box_start:
            x1, y1 = self.selection_box_start
            x2, y2 = event.x, event.y
            
            min_x, max_x = min(x1, x2), max(x1, x2)
            min_y, max_y = min(y1, y2), max(y1, y2)
            
            self.selected_nodes = []
            for node_id, node in self.nodes.items():
                if min_x <= node['x'] <= max_x and min_y <= node['y'] <= max_y:
                    self.selected_nodes.append(node_id)
            
            self.selection_box_active = False
            self.selection_box_start = None
            self.draw_network()
            
            if self.selected_nodes:
                self.status_label.config(
                    text=f"{len(self.selected_nodes)} node(s) selected. Click 'Delete Selected' to remove them.",
                    bg='#d1ecf1',
                    fg='#0c5460'
                )
            else:
                self.status_label.config(
                    text="No nodes in selection area.",
                    bg=self.theme.COLORS['bg_sidebar'],
                    fg=self.theme.COLORS['text_primary']
                )

        elif self.dragging_node and not self.link_mode:

            self.nodes[self.dragging_node]['x'] = event.x
            self.nodes[self.dragging_node]['y'] = event.y
            self.draw_network()
            self.status_label.config(
                text=f"Node '{self.dragging_node}' moved to ({event.x}, {event.y})",
                bg='#d1ecf1',
                fg='#0c5460'
            )
            self.dragging_node = None
        else:
            self.dragging_node = None
    
    def canvas_right_click(self, event):
        
        clicked_node = self.find_node_at(event.x, event.y)
        if clicked_node:
            self.right_click_link_start = clicked_node
            self.status_label.config(
                text=f"Creating link from '{clicked_node}'... Drag to target node and release.",
                bg='#fff3cd',
                fg='#856404'
            )
    
    def canvas_right_drag(self, event):
        
        if self.right_click_link_start:

            self.draw_network()

            start_node = self.nodes[self.right_click_link_start]
            self.canvas.create_line(
                start_node['x'], start_node['y'],
                event.x, event.y,
                fill='red',
                width=2,
                dash=(4, 4),
                tags='temp_link'
            )
    
    def canvas_right_release(self, event):
        
        if self.right_click_link_start:
            target_node = self.find_node_at(event.x, event.y)
            
            if target_node and target_node != self.right_click_link_start:

                link_exists = any(
                    (l['node1'] == self.right_click_link_start and l['node2'] == target_node) or
                    (l['node1'] == target_node and l['node2'] == self.right_click_link_start)
                    for l in self.links
                )
                
                if link_exists:
                    self.status_label.config(
                        text=f"Link already exists between {self.right_click_link_start} and {target_node}.",
                        bg='#f8d7da',
                        fg='#721c24'
                    )
                else:

                    self.links.append({
                        'node1': self.right_click_link_start,
                        'node2': target_node,
                        'bidirectional': True
                    })
                    self.draw_network()
                    self.update_properties_display()
                    self.update_button_states()
                    self.status_label.config(
                        text=f"Link created: {self.right_click_link_start} ↔ {target_node}",
                        bg=self.theme.COLORS['bg_sidebar'],
                        fg=self.theme.COLORS['text_primary']
                    )
            elif target_node == self.right_click_link_start:
                self.status_label.config(
                    text="Cannot create link to the same node.",
                    bg='#f8d7da',
                    fg='#721c24'
                )
            else:

                self.status_label.config(
                    text="Link creation cancelled - no target node.",
                    bg=self.theme.COLORS['bg_sidebar'],
                    fg=self.theme.COLORS['text_primary']
                )
            
            self.right_click_link_start = None
            self.draw_network()
    
    def delete_selected(self):

        if self.selected_nodes:
            num_deleted = len(self.selected_nodes)
            for node_id in self.selected_nodes:
                if node_id in self.nodes:
                    del self.nodes[node_id]

            self.links = [l for l in self.links 
                         if l['node1'] not in self.selected_nodes and l['node2'] not in self.selected_nodes]
            self.selected_nodes = []
            self.selected_node = None
            self.draw_network()
            self.update_properties_display()
            self.update_button_states()
            self.status_label.config(
                text=f"{num_deleted} node(s) deleted. Total nodes: {len(self.nodes)}",
                bg=self.theme.COLORS['bg_sidebar'],
                fg=self.theme.COLORS['text_primary']
            )

        elif self.selected_node:
            node_id = self.selected_node
            del self.nodes[self.selected_node]
            self.links = [l for l in self.links if l['node1'] != self.selected_node and l['node2'] != self.selected_node]
            self.selected_node = None
            self.draw_network()
            self.update_properties_display()
            self.update_button_states()
            self.status_label.config(
                text=f"Node '{node_id}' deleted. Total nodes: {len(self.nodes)}",
                bg=self.theme.COLORS['bg_sidebar'],
                fg=self.theme.COLORS['text_primary']
            )
    
    def draw_network(self):
        self.canvas.delete('all')
        
        for link in self.links:
            n1 = self.nodes[link['node1']]
            n2 = self.nodes[link['node2']]
            self.canvas.create_line(
                n1['x'], n1['y'], n2['x'], n2['y'],
                fill='gray',
                width=2
            )
        
        for node_id, node in self.nodes.items():

            color = '#ff6b6b' if node['properties'].get('exposed_to_internet') else '#4ecdc4'
            
            is_selected = node_id == self.selected_node or node_id in self.selected_nodes
            outline_color = 'blue' if is_selected else 'black'
            outline_width = 4 if is_selected else 2
            
            self.canvas.create_oval(
                node['x'] - 20, node['y'] - 20,
                node['x'] + 20, node['y'] + 20,
                fill=color,
                outline=outline_color,
                width=outline_width
            )
            self.canvas.create_text(
                node['x'], node['y'],
                text=node['id'][:8],
                font=self.theme.FONTS['body_small']
            )
    
    def update_properties_display(self):
        self.properties_text.delete('1.0', tk.END)
        self.properties_text.insert('1.0', f"Nodes: {len(self.nodes)}\n")
        self.properties_text.insert(tk.END, f"Links: {len(self.links)}\n\n")
        
        for node_id, node in self.nodes.items():
            self.properties_text.insert(tk.END, f"• {node_id}\n")
            self.properties_text.insert(tk.END, f"  Name: {node['name']}\n")
            self.properties_text.insert(tk.END, f"  OS: {node['software']['os']}\n")
            if node.get('category'):
                self.properties_text.insert(tk.END, f"  Category: {node['category']}\n")
            if node['properties'].get('exposed_to_internet'):
                self.properties_text.insert(tk.END, "  [EXPOSED]\n")
            self.properties_text.insert(tk.END, "\n")
    
    def generate_random_dialog(self):
        dialog = tk.Toplevel(self)
        dialog.title("Generate Random Network")
        dialog.geometry("700x500")
        dialog.configure(bg=self.theme.COLORS['bg_primary'])
        dialog.transient(self)
        dialog.grab_set()
        
        form_frame = tk.Frame(dialog, bg=self.theme.COLORS['bg_primary'])
        form_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        form_frame.columnconfigure(1, weight=1)
        
        tk.Label(
            form_frame,
            text="Generate Network (Barabási-Albert Model)",
            font=self.theme.FONTS['heading_medium'],
            bg=self.theme.COLORS['bg_primary'],
            fg=self.theme.COLORS['text_primary']
        ).grid(row=0, column=0, columnspan=3, pady=10)
        
        help_text = tk.Label(
            form_frame,
            text="Scale-free network with preferential attachment.",
            font=self.theme.FONTS['body_small'],
            bg=self.theme.COLORS['bg_primary'],
            fg=self.theme.COLORS['text_secondary'],
            justify=tk.LEFT
        )
        help_text.grid(row=1, column=0, columnspan=3, pady=5, sticky='w')
        
        tk.Label(form_frame, text="Number of Nodes:", bg=self.theme.COLORS['bg_primary'], fg=self.theme.COLORS['text_primary']).grid(row=2, column=0, sticky='w', pady=8)
        num_nodes_var = tk.IntVar(value=20)
        tk.Entry(form_frame, textvariable=num_nodes_var).grid(row=2, column=1, sticky='ew', pady=8, padx=5)
        
        tk.Label(form_frame, text="Exposed Nodes %:", bg=self.theme.COLORS['bg_primary'], fg=self.theme.COLORS['text_primary']).grid(row=3, column=0, sticky='w', pady=8)
        exposed_percent_var = tk.IntVar(value=10)
        tk.Entry(form_frame, textvariable=exposed_percent_var).grid(row=3, column=1, sticky='ew', pady=8, padx=5)
        
        def generate():
            try:
                num_nodes = num_nodes_var.get()
                exposed_percent = exposed_percent_var.get()
                
                if num_nodes < 2:
                    messagebox.showerror("Error", "Need at least 2 nodes")
                    return
                
                self.generate_scale_free_network(num_nodes, exposed_percent)
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to generate network: {str(e)}")
        
        tk.Button(
            form_frame,
            text="Generate",
            command=generate,
            bg=self.theme.COLORS['success'],
            fg='white',
            font=self.theme.FONTS['body']
        ).grid(row=7, column=0, columnspan=3, pady=20)
    
    def generate_scale_free_network(self, num_nodes, exposed_percent):
        
        self.nodes = {}
        self.links = []
        
        initial_nodes = min(3, num_nodes)
        edges_per_node = min(2, initial_nodes)
        
        os_list = self.load_operating_systems()
        services = self.load_services()
        assets = self.load_assets()
        categories = self.load_categories()
        
        width, height = 800, 600
        radius = 250
        
        for i in range(num_nodes):
            angle = 2 * math.pi * i / num_nodes
            x = width / 2 + radius * math.cos(angle)
            y = height / 2 + radius * math.sin(angle)
            
            chosen_os = random.choice(os_list) if os_list else "Linux"
            os_data = self.load_os_data(chosen_os)
            
            versions = os_data.get('versions', [])
            if versions:
                chosen_version_data = random.choice(versions)
                chosen_version = chosen_version_data['version']
                available_vulns = chosen_version_data.get('vulnerabilities', [])
                chosen_vulns = random.sample(available_vulns, min(len(available_vulns), random.randint(0, 3)))
            else:
                chosen_version = "1.0"
                chosen_vulns = []
            
            num_services = random.randint(1, min(4, len(services))) if services else 0
            chosen_services = random.sample(services, num_services) if num_services > 0 else []
            
            num_assets = random.randint(0, min(2, len(assets))) if assets else 0
            chosen_assets = random.sample(assets, num_assets) if num_assets > 0 else []
            
            chosen_category = random.choice(categories) if categories else "Server"
            
            node_id = f"node_{i+1}"
            self.nodes[node_id] = {
                'id': node_id,
                'name': f"Node {i+1}",
                'x': int(x),
                'y': int(y),
                'software': {
                    'os': chosen_os,
                    'version': chosen_version,
                    'services': chosen_services
                },
                'vulnerabilities': chosen_vulns,
                'assets': chosen_assets,
                'category': chosen_category,
                'properties': {
                    'exposed_to_internet': False
                }
            }
        
        for i in range(initial_nodes):
            for j in range(i+1, initial_nodes):
                self.links.append({
                    'node1': f"node_{i+1}",
                    'node2': f"node_{j+1}",
                    'bidirectional': True
                })
        
        node_degrees = {f"node_{i+1}": 0 for i in range(num_nodes)}
        for link in self.links:
            node_degrees[link['node1']] += 1
            node_degrees[link['node2']] += 1
        
        for i in range(initial_nodes, num_nodes):
            node_id = f"node_{i+1}"
            
            total_degree = sum(node_degrees.values())
            targets = []
            for _ in range(min(edges_per_node, len(self.nodes) - 1)):
                if total_degree == 0:

                    target = random.choice([n for n in node_degrees.keys() if n != node_id and n not in targets])
                else:

                    r = random.uniform(0, total_degree)
                    cumsum = 0
                    target = None
                    for nid, degree in node_degrees.items():
                        if nid != node_id and nid not in targets:
                            cumsum += degree
                            if cumsum >= r:
                                target = nid
                                break
                    if target is None:
                        available = [n for n in node_degrees.keys() if n != node_id and n not in targets]
                        if available:
                            target = random.choice(available)
                
                if target:
                    targets.append(target)
                    self.links.append({
                        'node1': node_id,
                        'node2': target,
                        'bidirectional': True
                    })
                    node_degrees[node_id] += 1
                    node_degrees[target] += 1
                    total_degree += 2
        
        num_exposed = max(1, int(num_nodes * exposed_percent / 100))
        exposed_nodes = random.sample(list(self.nodes.keys()), num_exposed)
        for node_id in exposed_nodes:
            self.nodes[node_id]['properties']['exposed_to_internet'] = True
        
        self.draw_network()
        self.update_properties_display()
        self.update_button_states()
        self.status_label.config(
            text=f"Network generated: {num_nodes} nodes, {len(self.links)} links (BA model: m=3, m0={edges_per_node})",
            bg=self.theme.COLORS['bg_sidebar'],
            fg=self.theme.COLORS['text_primary']
        )
    
    def save_network(self):
        if not self.nodes:
            self.status_label.config(
                text="No network to save. Add nodes first.",
                bg='#f8d7da',
                fg='#721c24'
            )
            return
        
        self.lift()
        self.focus_force()
        
        filename = filedialog.asksaveasfilename(
            parent=self,
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialdir="src/networks/library"
        )
        
        if filename:
            network_data = {
                "name": "Custom Network",
                "description": f"Custom network with {len(self.nodes)} nodes and {len(self.links)} links",
                "nodes": [],
                "links": []
            }
            
            for node_id, node in self.nodes.items():
                network_data["nodes"].append({
                    "id": node['id'],
                    "name": node['name'],
                    "software": node['software'],
                    "vulnerabilities": node['vulnerabilities'],
                    "assets": node['assets'],
                    "properties": node['properties']
                })
            
            for link in self.links:
                network_data["links"].append({
                    "node1": link['node1'],
                    "node2": link['node2'],
                    "bidirectional": link['bidirectional']
                })
            
            try:
                with open(filename, 'w') as f:
                    json.dump(network_data, f, indent=2)
                
                self.status_label.config(
                    text=f"Network saved to {filename}",
                    bg='#d4edda',
                    fg='#155724'
                )
            except Exception as e:
                self.status_label.config(
                    text=f"Error saving network: {str(e)}",
                    bg='#f8d7da',
                    fg='#721c24'
                )
    
    def load_network(self):

        self.lift()
        self.focus_force()
        
        filename = filedialog.askopenfilename(
            parent=self,
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialdir="src/networks/library"
        )
        
        if filename:
            try:
                with open(filename, 'r') as f:
                    data = json.load(f)
                
                self.nodes = {}
                self.links = []
                
                for i, node in enumerate(data.get('nodes', [])):
                    node_id = node['id']
                    angle = 2 * math.pi * i / len(data['nodes'])
                    x = 400 + 200 * math.cos(angle)
                    y = 300 + 200 * math.sin(angle)
                    
                    self.nodes[node_id] = {
                        'id': node_id,
                        'name': node.get('name', node_id),
                        'x': int(x),
                        'y': int(y),
                        'software': node.get('software', {}),
                        'vulnerabilities': node.get('vulnerabilities', []),
                        'assets': node.get('assets', []),
                        'properties': node.get('properties', {})
                    }
                
                for link in data.get('links', []):
                    self.links.append({
                        'node1': link['node1'],
                        'node2': link['node2'],
                        'bidirectional': link.get('bidirectional', True)
                    })
                
                self.draw_network()
                self.update_properties_display()
                self.update_button_states()
                
                self.status_label.config(
                    text=f"Network loaded from {filename}",
                    bg='#d4edda',
                    fg='#155724'
                )
                
            except Exception as e:
                self.status_label.config(
                    text=f"Failed to load network: {str(e)}",
                    bg='#f8d7da',
                    fg='#721c24'
                )
