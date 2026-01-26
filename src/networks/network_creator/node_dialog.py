import random
import tkinter as tk
from tkinter import messagebox, ttk


class NodeDialog:
    def add_node_dialog(self):
        dialog = tk.Toplevel(self)
        dialog.title("Add Node")
        dialog.geometry("1000x900")
        dialog.configure(bg=self.theme.COLORS["bg_primary"])
        dialog.transient(self)
        dialog.grab_set()
        canvas = tk.Canvas(dialog, bg=self.theme.COLORS["bg_primary"], highlightthickness=0)
        scrollbar = tk.Scrollbar(dialog, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.theme.COLORS["bg_primary"])
        scrollable_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True, padx=(20, 0), pady=20)
        scrollbar.pack(side="right", fill="y", padx=(0, 20), pady=20)

        def on_dialog_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

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
        tk.Label(
            form_frame,
            text="Node ID:",
            bg=self.theme.COLORS["bg_primary"],
            fg=self.theme.COLORS["text_primary"],
        ).grid(row=current_row, column=0, sticky="w", pady=5, padx=5)
        fields["id"] = tk.Entry(form_frame)
        fields["id"].grid(row=current_row, column=1, sticky="ew", pady=5, padx=5)
        fields["id"].insert(0, f"node_{len(self.nodes) + 1}")
        current_row += 1
        tk.Label(
            form_frame,
            text="Name:",
            bg=self.theme.COLORS["bg_primary"],
            fg=self.theme.COLORS["text_primary"],
        ).grid(row=current_row, column=0, sticky="w", pady=5, padx=5)
        fields["name"] = tk.Entry(form_frame)
        fields["name"].grid(row=current_row, column=1, sticky="ew", pady=5, padx=5)
        current_row += 1
        tk.Label(
            form_frame,
            text="Operating System:",
            bg=self.theme.COLORS["bg_primary"],
            fg=self.theme.COLORS["text_primary"],
        ).grid(row=current_row, column=0, sticky="w", pady=5, padx=5)
        os_list = self.load_operating_systems()
        fields["os"] = ttk.Combobox(form_frame, values=os_list, state="readonly")
        fields["os"].grid(row=current_row, column=1, sticky="ew", pady=5, padx=5)
        if os_list:
            if "Ubuntu" in os_list:
                fields["os"].set("Ubuntu")
            else:
                fields["os"].set(os_list[0])
        current_row += 1
        tk.Label(
            form_frame,
            text="OS Version:",
            bg=self.theme.COLORS["bg_primary"],
            fg=self.theme.COLORS["text_primary"],
        ).grid(row=current_row, column=0, sticky="w", pady=5, padx=5)
        fields["version"] = ttk.Combobox(form_frame, state="readonly")
        fields["version"].grid(row=current_row, column=1, sticky="ew", pady=5, padx=5)
        current_row += 1
        tk.Label(
            form_frame,
            text="Category:",
            bg=self.theme.COLORS["bg_primary"],
            fg=self.theme.COLORS["text_primary"],
        ).grid(row=current_row, column=0, sticky="w", pady=5, padx=5)
        categories = self.load_categories()
        fields["category"] = ttk.Combobox(form_frame, values=categories, state="readonly")
        fields["category"].grid(row=current_row, column=1, sticky="ew", pady=5, padx=5)
        if categories:
            fields["category"].set(categories[0])
        current_row += 1
        fields["services_vars"] = {}
        tk.Label(
            form_frame,
            text="Vulnerabilities:",
            bg=self.theme.COLORS["bg_primary"],
            fg=self.theme.COLORS["text_primary"],
            font=self.theme.FONTS["heading_small"],
        ).grid(row=current_row, column=0, sticky="nw", pady=10, padx=5)
        vuln_outer_frame = tk.Frame(
            form_frame, bg=self.theme.COLORS["bg_secondary"], relief=tk.SUNKEN, bd=1
        )
        vuln_outer_frame.grid(row=current_row, column=1, sticky="ew", pady=10, padx=5)
        vuln_canvas = tk.Canvas(
            vuln_outer_frame,
            bg=self.theme.COLORS["bg_primary"],
            height=150,
            highlightthickness=0,
        )
        vuln_scrollbar = tk.Scrollbar(
            vuln_outer_frame, orient="vertical", command=vuln_canvas.yview
        )
        fields["vuln_inner_frame"] = tk.Frame(vuln_canvas, bg=self.theme.COLORS["bg_primary"])
        fields["vuln_inner_frame"].bind(
            "<Configure>",
            lambda e: vuln_canvas.configure(scrollregion=vuln_canvas.bbox("all")),
        )
        vuln_canvas.create_window((0, 0), window=fields["vuln_inner_frame"], anchor="nw")
        vuln_canvas.configure(yscrollcommand=vuln_scrollbar.set)
        vuln_canvas.pack(side="left", fill="both", expand=True)
        vuln_scrollbar.pack(side="right", fill="y")

        def on_vuln_mousewheel(event):
            vuln_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

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
        fields["vuln_vars"] = {}
        current_row += 1
        tk.Label(
            form_frame,
            text="Assets:",
            bg=self.theme.COLORS["bg_primary"],
            fg=self.theme.COLORS["text_primary"],
            font=self.theme.FONTS["heading_small"],
        ).grid(row=current_row, column=0, sticky="nw", pady=10, padx=5)
        assets_outer_frame = tk.Frame(
            form_frame, bg=self.theme.COLORS["bg_secondary"], relief=tk.SUNKEN, bd=1
        )
        assets_outer_frame.grid(row=current_row, column=1, sticky="ew", pady=10, padx=5)
        assets_canvas = tk.Canvas(
            assets_outer_frame,
            bg=self.theme.COLORS["bg_primary"],
            height=150,
            highlightthickness=0,
        )
        assets_scrollbar = tk.Scrollbar(
            assets_outer_frame, orient="vertical", command=assets_canvas.yview
        )
        assets_inner_frame = tk.Frame(assets_canvas, bg=self.theme.COLORS["bg_primary"])
        assets_inner_frame.bind(
            "<Configure>",
            lambda e: assets_canvas.configure(scrollregion=assets_canvas.bbox("all")),
        )
        assets_canvas.create_window((0, 0), window=assets_inner_frame, anchor="nw")
        assets_canvas.configure(yscrollcommand=assets_scrollbar.set)
        assets_canvas.pack(side="left", fill="both", expand=True)
        assets_scrollbar.pack(side="right", fill="y")

        def on_assets_mousewheel(event):
            assets_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

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
        fields["assets_vars"] = {}
        for asset in self.load_assets():
            var = tk.BooleanVar(value=False)
            fields["assets_vars"][asset] = var
            tk.Checkbutton(
                assets_inner_frame,
                text=asset,
                variable=var,
                bg=self.theme.COLORS["bg_primary"],
                fg=self.theme.COLORS["text_primary"],
                anchor="w",
            ).pack(fill="x", padx=5, pady=2)
        current_row += 1
        fields["exposed"] = tk.BooleanVar(value=False)
        tk.Checkbutton(
            form_frame,
            text="Exposed to Internet",
            variable=fields["exposed"],
            bg=self.theme.COLORS["bg_primary"],
            fg=self.theme.COLORS["text_primary"],
        ).grid(row=current_row, column=0, columnspan=2, pady=10)
        current_row += 1

        def on_os_change(event=None):
            os_name = fields["os"].get()
            if not os_name:
                return
            os_data = self.load_os_data(os_name)
            versions = [v["version"] for v in os_data.get("versions", [])]
            fields["version"]["values"] = versions
            if versions:
                fields["version"].set(versions[0])
                on_version_change()
            else:
                fields["version"].set("")
                for widget in fields["vuln_inner_frame"].winfo_children():
                    widget.destroy()
                fields["vuln_vars"] = {}

        def on_version_change(event=None):
            os_name = fields["os"].get()
            version = fields["version"].get()
            if not os_name or not version:
                return
            os_data = self.load_os_data(os_name)
            vulnerabilities = []
            for v in os_data.get("versions", []):
                if v["version"] == version:
                    vulnerabilities = v.get("vulnerabilities", [])
                    break
            for widget in fields["vuln_inner_frame"].winfo_children():
                widget.destroy()
            fields["vuln_vars"] = {}
            for vuln in vulnerabilities:
                var = tk.BooleanVar(value=False)
                fields["vuln_vars"][vuln] = var
                tk.Checkbutton(
                    fields["vuln_inner_frame"],
                    text=vuln,
                    variable=var,
                    bg=self.theme.COLORS["bg_primary"],
                    fg=self.theme.COLORS["text_primary"],
                    anchor="w",
                ).pack(fill="x", padx=5, pady=2)

        fields["os"].bind("<<ComboboxSelected>>", on_os_change)
        fields["version"].bind("<<ComboboxSelected>>", on_version_change)
        on_os_change()

        def create_node():
            node_id = fields["id"].get().strip()
            if not node_id:
                messagebox.showerror("Error", "Node ID is required")
                return
            if node_id in self.nodes:
                messagebox.showerror("Error", f"Node {node_id} already exists")
                return
            services = [service for service, var in fields["services_vars"].items() if var.get()]
            vulnerabilities = [vuln for vuln, var in fields["vuln_vars"].items() if var.get()]
            assets = [asset for asset, var in fields["assets_vars"].items() if var.get()]
            x = random.randint(50, 750)
            y = random.randint(50, 550)
            self.nodes[node_id] = {
                "id": node_id,
                "name": fields["name"].get() or node_id,
                "x": x,
                "y": y,
                "software": {
                    "os": fields["os"].get(),
                    "version": fields["version"].get(),
                    "services": services,
                },
                "vulnerabilities": vulnerabilities,
                "assets": assets,
                "category": fields["category"].get(),
                "properties": {"exposed_to_internet": fields["exposed"].get()},
            }
            self.draw_network()
            self.update_properties_display()
            self.update_button_states()
            self.status_label.config(
                text=f"Node '{node_id}' added successfully. Total nodes: {len(self.nodes)}",
                bg=self.theme.COLORS["bg_sidebar"],
                fg=self.theme.COLORS["text_primary"],
            )
            dialog.destroy()

        tk.Button(
            form_frame,
            text="Create Node",
            command=create_node,
            bg=self.theme.COLORS["success"],
            fg="white",
            font=self.theme.FONTS["body"],
        ).grid(row=current_row, column=0, columnspan=2, pady=20)
