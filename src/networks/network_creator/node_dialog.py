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
            else:
                fields["version"].set("")

        fields["os"].bind("<<ComboboxSelected>>", on_os_change)
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
            assets = [asset for asset, var in fields["assets_vars"].items() if var.get()]
            x = random.randint(50, 750)
            y = random.randint(50, 550)
            x, y = self.snap_to_grid(x, y)
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

    def edit_node_dialog(self, node_id):
        """Open a dialog to edit an existing node."""
        if node_id not in self.nodes:
            return

        node = self.nodes[node_id]
        dialog = tk.Toplevel(self)
        dialog.title(f"Edit Node: {node_id}")
        dialog.geometry("1000x900")
        dialog.configure(bg=self.theme.COLORS["bg_primary"])
        dialog.transient(self)
        dialog.wait_visibility()
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
        fields["id"] = tk.Entry(form_frame, state="readonly")
        fields["id"].grid(row=current_row, column=1, sticky="ew", pady=5, padx=5)
        fields["id"].config(state="normal")
        fields["id"].insert(0, node_id)
        fields["id"].config(state="readonly")
        current_row += 1

        tk.Label(
            form_frame,
            text="Name:",
            bg=self.theme.COLORS["bg_primary"],
            fg=self.theme.COLORS["text_primary"],
        ).grid(row=current_row, column=0, sticky="w", pady=5, padx=5)
        fields["name"] = tk.Entry(form_frame)
        fields["name"].grid(row=current_row, column=1, sticky="ew", pady=5, padx=5)
        fields["name"].insert(0, node.get("name", ""))
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
        current_os = node.get("software", {}).get("os", "")
        if current_os in os_list:
            fields["os"].set(current_os)
        elif os_list:
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
        current_category = node.get("category", "")
        if current_category in categories:
            fields["category"].set(current_category)
        elif categories:
            fields["category"].set(categories[0])
        current_row += 1

        fields["services_vars"] = {}

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
        current_assets = node.get("assets", [])
        for asset in self.load_assets():
            var = tk.BooleanVar(value=asset in current_assets)
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

        fields["exposed"] = tk.BooleanVar(
            value=node.get("properties", {}).get("exposed_to_internet", False)
        )
        tk.Checkbutton(
            form_frame,
            text="Exposed to Internet",
            variable=fields["exposed"],
            bg=self.theme.COLORS["bg_primary"],
            fg=self.theme.COLORS["text_primary"],
        ).grid(row=current_row, column=0, columnspan=2, pady=10)
        current_row += 1

        def on_os_change(event=None, restore_version=False):
            os_name = fields["os"].get()
            if not os_name:
                return
            os_data = self.load_os_data(os_name)
            versions = [v["version"] for v in os_data.get("versions", [])]
            fields["version"]["values"] = versions
            if restore_version:
                current_version = node.get("software", {}).get("version", "")
                if current_version in versions:
                    fields["version"].set(current_version)
                elif versions:
                    fields["version"].set(versions[0])
            elif versions:
                fields["version"].set(versions[0])
            else:
                fields["version"].set("")

        fields["os"].bind("<<ComboboxSelected>>", on_os_change)
        on_os_change(restore_version=True)

        def update_node():
            services = [service for service, var in fields["services_vars"].items() if var.get()]
            assets = [asset for asset, var in fields["assets_vars"].items() if var.get()]

            # Preserve position
            x = node.get("x", 0)
            y = node.get("y", 0)

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
                "assets": assets,
                "category": fields["category"].get(),
                "properties": {"exposed_to_internet": fields["exposed"].get()},
            }
            self.draw_network()
            self.update_properties_display()
            self.status_label.config(
                text=f"Node '{node_id}' updated successfully.",
                bg=self.theme.COLORS["bg_sidebar"],
                fg=self.theme.COLORS["text_primary"],
            )
            dialog.destroy()

        tk.Button(
            form_frame,
            text="Update Node",
            command=update_node,
            bg=self.theme.COLORS["success"],
            fg="white",
            font=self.theme.FONTS["body"],
        ).grid(row=current_row, column=0, columnspan=2, pady=20)
