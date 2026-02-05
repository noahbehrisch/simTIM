import tkinter as tk

from src.gui.theme import Theme

from .canvas_handlers import CanvasHandlers
from .data_loaders import DataLoaders
from .file_operations import FileOperations
from .network_generator import NetworkGenerator
from .node_dialog import NodeDialog


class NetworkCreator(
    tk.Toplevel,
    NetworkGenerator,
    NodeDialog,
    DataLoaders,
    FileOperations,
    CanvasHandlers,
):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.theme = Theme()
        self.title("Network Creator")
        self.geometry("1200x800")
        self.configure(bg=self.theme.COLORS["bg_primary"])
        self.nodes = {}
        self.links = []
        self.selected_node = None
        self.selected_nodes = []
        self.selected_links = []
        self.link_start_node = None
        self.link_mode = False
        self.right_click_link_start = None
        self.help_visible = False
        self.dragging_node = None
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.selection_box_active = False
        self.selection_box_start = None
        self.snap_size = 60  # grid_size is already used by tkinter
        self.zoom_scale = 1.0
        self.min_zoom = 0.25
        self.max_zoom = 4.0
        self.canvas_half_extent = 2000
        self.create_widgets()
        self.transient(parent)

    def update_button_states(self):
        if len(self.nodes) < 2:
            self.add_link_button.config(state=tk.DISABLED)
        else:
            self.add_link_button.config(state=tk.NORMAL)
        if len(self.selected_nodes) == 1 or (self.selected_node and len(self.selected_nodes) == 0):
            self.edit_node_button.config(state=tk.NORMAL)
        else:
            self.edit_node_button.config(state=tk.DISABLED)

    def snap_to_grid(self, x: int, y: int) -> tuple[int, int]:
        if self.snap_size <= 0:
            return x, y
        snapped_x = round(x / self.snap_size) * self.snap_size
        snapped_y = round(y / self.snap_size) * self.snap_size
        return snapped_x, snapped_y

    def show_help(self):
        if self.help_visible:
            self.help_frame.pack_forget()
            self.canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
            self.properties_frame.pack(side=tk.RIGHT, fill=tk.Y)
            self.help_visible = False
            self.status_label.config(
                text="Click 'Add Node' to create nodes, then 'Add Link' to connect them.",
                bg=self.theme.COLORS["bg_sidebar"],
                fg=self.theme.COLORS["text_primary"],
                justify=tk.LEFT,
                anchor="w",
            )
        else:
            self.canvas_frame.pack_forget()
            self.properties_frame.pack_forget()
            self.help_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=(0, 5))
            self.help_visible = True
            self.status_label.config(
                text="Help panel shown. Click 'Help' again to hide and return to editor.",
                bg="#fff3cd",
                fg="#856404",
                justify=tk.LEFT,
                anchor="w",
            )

    def update_properties_display(self):
        self.properties_text.delete("1.0", tk.END)
        self.properties_text.insert("1.0", f"Nodes: {len(self.nodes)}\n")
        self.properties_text.insert(tk.END, f"Links: {len(self.links)}\n\n")
        for node_id, node in self.nodes.items():
            self.properties_text.insert(tk.END, f"• {node_id}\n")
            self.properties_text.insert(tk.END, f"  Name: {node['name']}\n")
            os_name = node.get("software", {}).get("os", "Unknown")
            self.properties_text.insert(tk.END, f"  OS: {os_name}\n")
            if node.get("category"):
                self.properties_text.insert(tk.END, f"  Category: {node['category']}\n")
            if node.get("properties", {}).get("exposed_to_internet"):
                self.properties_text.insert(tk.END, "  [EXPOSED]\n")
            self.properties_text.insert(tk.END, "\n")

    def create_widgets(self):
        main_frame = tk.Frame(self, bg=self.theme.COLORS["bg_primary"])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        toolbar_frame = tk.Frame(main_frame, bg=self.theme.COLORS["bg_sidebar"])
        toolbar_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 5))
        tk.Button(
            toolbar_frame,
            text="Add Node",
            command=self.add_node_dialog,
            bg=self.theme.COLORS["accent_secondary"],
            fg=self.theme.COLORS["text_primary"],
            font=self.theme.FONTS["body"],
        ).pack(side=tk.LEFT, padx=5, pady=5)
        self.add_link_button = tk.Button(
            toolbar_frame,
            text="Add Link",
            command=self.start_link_creation,
            bg=self.theme.COLORS["accent_secondary"],
            fg=self.theme.COLORS["text_primary"],
            font=self.theme.FONTS["body"],
            state=tk.DISABLED,
        )
        self.add_link_button.pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(
            toolbar_frame,
            text="Delete Selected",
            command=self.delete_selected,
            bg=self.theme.COLORS["danger"],
            fg="white",
            font=self.theme.FONTS["body"],
        ).pack(side=tk.LEFT, padx=5, pady=5)
        self.edit_node_button = tk.Button(
            toolbar_frame,
            text="Edit Node",
            command=self.edit_selected_node,
            bg=self.theme.COLORS["info"],
            fg="white",
            font=self.theme.FONTS["body"],
            state=tk.DISABLED,
        )
        self.edit_node_button.pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(
            toolbar_frame,
            text="Generate Random",
            command=self.generate_random_dialog,
            bg=self.theme.COLORS["info"],
            fg="white",
            font=self.theme.FONTS["body"],
        ).pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(
            toolbar_frame,
            text="Help",
            command=self.show_help,
            bg=self.theme.COLORS["warning"],
            fg="white",
            font=self.theme.FONTS["body"],
        ).pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(
            toolbar_frame,
            text="Save Network",
            command=self.save_network,
            bg=self.theme.COLORS["success"],
            fg="white",
            font=self.theme.FONTS["body"],
        ).pack(side=tk.RIGHT, padx=5, pady=5)
        tk.Button(
            toolbar_frame,
            text="Load Network",
            command=self.load_network,
            bg=self.theme.COLORS["accent_secondary"],
            fg=self.theme.COLORS["text_primary"],
            font=self.theme.FONTS["body"],
        ).pack(side=tk.RIGHT, padx=5, pady=5)
        content_frame = tk.Frame(main_frame, bg=self.theme.COLORS["bg_primary"])
        content_frame.pack(fill=tk.BOTH, expand=True)
        self.status_label = tk.Label(
            content_frame,
            text="Click 'Add Node' to create nodes, then 'Add Link' to connect them.",
            bg=self.theme.COLORS["bg_sidebar"],
            fg=self.theme.COLORS["text_primary"],
            font=self.theme.FONTS["body"],
            relief=tk.FLAT,
            padx=10,
            pady=5,
        )
        self.status_label.pack(side=tk.TOP, fill=tk.X, pady=(0, 5))
        self.help_frame = tk.Frame(content_frame, bg=self.theme.COLORS["bg_secondary"])
        help_scroll = tk.Scrollbar(self.help_frame)
        help_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.help_text_widget = tk.Text(
            self.help_frame,
            wrap=tk.WORD,
            width=120,
            height=15,
            bg=self.theme.COLORS["bg_secondary"],
            fg=self.theme.COLORS["text_primary"],
            font=self.theme.FONTS["body"],
            padx=10,
            pady=10,
            yscrollcommand=help_scroll.set,
        )
        self.help_text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        help_scroll.config(command=self.help_text_widget.yview)
        help_content = (
            "Network Creator Help\n\nVisual Indicators:\n  • Red node = Exposed to Internet\n"
        )
        self.help_text_widget.insert("1.0", help_content)
        self.help_text_widget.config(state=tk.DISABLED)
        self.canvas_frame = tk.Frame(
            content_frame, bg=self.theme.COLORS["bg_secondary"], relief=tk.SUNKEN, bd=2
        )
        self.canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        self.v_scrollbar = tk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL)
        self.v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.h_scrollbar = tk.Scrollbar(self.canvas_frame, orient=tk.HORIZONTAL)
        self.h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas = tk.Canvas(
            self.canvas_frame,
            bg="white",
            width=800,
            height=600,
            xscrollcommand=self.h_scrollbar.set,
            yscrollcommand=self.v_scrollbar.set,
            scrollregion=(
                -self.canvas_half_extent,
                -self.canvas_half_extent,
                self.canvas_half_extent,
                self.canvas_half_extent,
            ),
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.v_scrollbar.config(command=self.canvas.yview)
        self.h_scrollbar.config(command=self.canvas.xview)
        self.canvas.xview_moveto(0.5)
        self.canvas.yview_moveto(0.5)
        self.canvas.bind("<Button-1>", self.canvas_click)
        self.canvas.bind("<Double-Button-1>", self.canvas_double_click)
        self.canvas.bind("<B1-Motion>", self.canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.canvas_release)
        self.canvas.bind("<Button-3>", self.canvas_right_click)
        self.canvas.bind("<B3-Motion>", self.canvas_right_drag)
        self.canvas.bind("<ButtonRelease-3>", self.canvas_right_release)
        self.canvas.bind("<MouseWheel>", self.on_zoom)
        self.canvas.bind("<Button-4>", self.on_zoom_in)
        self.canvas.bind("<Button-5>", self.on_zoom_out)
        self.canvas.bind("<Button-2>", self.pan_start)
        self.canvas.bind("<B2-Motion>", self.pan_move)
        self.canvas.bind("<ButtonRelease-2>", self.pan_end)
        self.canvas.bind("<Control-Button-1>", self.pan_start)
        self.canvas.bind("<Control-B1-Motion>", self.pan_move)
        self.canvas.bind("<Control-ButtonRelease-1>", self.pan_end)
        self.properties_frame = tk.Frame(
            content_frame, bg=self.theme.COLORS["bg_sidebar"], width=300
        )
        self.properties_frame.pack(side=tk.RIGHT, fill=tk.Y)
        self.properties_frame.pack_propagate(False)
        tk.Label(
            self.properties_frame,
            text="Network Properties",
            font=self.theme.FONTS["heading_medium"],
            bg=self.theme.COLORS["bg_sidebar"],
            fg=self.theme.COLORS["text_primary"],
        ).pack(pady=10)
        self.properties_text = tk.Text(
            self.properties_frame,
            width=35,
            height=40,
            bg=self.theme.COLORS["bg_secondary"],
            fg=self.theme.COLORS["text_primary"],
            font=self.theme.FONTS["body_small"],
        )
        self.properties_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.update_properties_display()
        self.update_button_states()
