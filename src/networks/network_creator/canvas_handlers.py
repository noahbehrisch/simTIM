class CanvasHandlers:
    def start_link_creation(self):
        if len(self.nodes) < 2:
            return
        self.link_mode = True
        self.link_start_node = None
        self.status_label.config(
            text="LINK MODE: Click the first node, then click the second node. You can also right-click + drag.",
            bg="#fff3cd",
            fg="#856404",
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
                        self.nodes[clicked_node]["x"] - 22,
                        self.nodes[clicked_node]["y"] - 22,
                        self.nodes[clicked_node]["x"] + 22,
                        self.nodes[clicked_node]["y"] + 22,
                        outline="red",
                        width=3,
                        tags="link_highlight",
                    )
                    self.status_label.config(
                        text=f"First node selected: {clicked_node}. Now click the second node.",
                        bg="#d1ecf1",
                        fg="#0c5460",
                    )
            elif clicked_node and clicked_node != self.link_start_node:
                link_exists = any(
                    link["node1"] == self.link_start_node
                    and link["node2"] == clicked_node
                    or (link["node1"] == clicked_node and link["node2"] == self.link_start_node)
                    for link in self.links
                )
                if link_exists:
                    self.status_label.config(
                        text=f"Link already exists between {self.link_start_node} and {clicked_node}.",
                        bg="#f8d7da",
                        fg="#721c24",
                    )
                else:
                    self.links.append(
                        {
                            "node1": self.link_start_node,
                            "node2": clicked_node,
                            "bidirectional": True,
                        }
                    )
                    self.draw_network()
                    self.update_properties_display()
                    self.update_button_states()
                    self.status_label.config(
                        text=f"Link created: {self.link_start_node} ↔ {clicked_node}",
                        bg=self.theme.COLORS["bg_sidebar"],
                        fg=self.theme.COLORS["text_primary"],
                    )
                self.link_mode = False
                self.link_start_node = None
            elif clicked_node == self.link_start_node:
                self.status_label.config(
                    text="Cannot create link to the same node. Click a different node.",
                    bg="#f8d7da",
                    fg="#721c24",
                )
            else:
                self.link_mode = False
                self.link_start_node = None
                self.draw_network()
                self.status_label.config(
                    text="Link creation cancelled.",
                    bg=self.theme.COLORS["bg_sidebar"],
                    fg=self.theme.COLORS["text_primary"],
                )
        elif clicked_node:
            self.selected_node = clicked_node
            self.selected_nodes = [clicked_node]
            self.dragging_node = clicked_node
            self.selection_box_active = False
            self.draw_network()
            self.update_button_states()
            self.status_label.config(
                text=f"Node '{clicked_node}' selected. Drag to move or click 'Delete Selected' to remove.",
                bg="#d1ecf1",
                fg="#0c5460",
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
                text="Drag to create selection box...", bg="#fff3cd", fg="#856404"
            )

    def find_node_at(self, x, y):
        for node_id, node in self.nodes.items():
            dx = node["x"] - x
            dy = node["y"] - y
            if dx * dx + dy * dy <= 400:
                return node_id
        return None

    def canvas_drag(self, event):
        if self.selection_box_active and self.selection_box_start:
            self.draw_network()
            x1, y1 = self.selection_box_start
            self.canvas.create_rectangle(
                x1,
                y1,
                event.x,
                event.y,
                outline="blue",
                width=2,
                dash=(4, 4),
                tags="selection_box",
            )
        elif not self.link_mode and self.dragging_node:
            dx = event.x - self.drag_start_x
            dy = event.y - self.drag_start_y
            if abs(dx) > 3 or abs(dy) > 3:
                snapped_x, snapped_y = self.snap_to_grid(event.x, event.y)
                self.nodes[self.dragging_node]["x"] = snapped_x
                self.nodes[self.dragging_node]["y"] = snapped_y
                self.draw_network()
                self.drag_start_x = event.x
                self.drag_start_y = event.y

    def canvas_release(self, event):
        if self.selection_box_active and self.selection_box_start:
            x1, y1 = self.selection_box_start
            x2, y2 = (event.x, event.y)
            min_x, max_x = (min(x1, x2), max(x1, x2))
            min_y, max_y = (min(y1, y2), max(y1, y2))
            self.selected_nodes = []
            for node_id, node in self.nodes.items():
                if min_x <= node["x"] <= max_x and min_y <= node["y"] <= max_y:
                    self.selected_nodes.append(node_id)
            self.selection_box_active = False
            self.selection_box_start = None
            self.draw_network()
            if self.selected_nodes:
                self.status_label.config(
                    text=f"{len(self.selected_nodes)} node(s) selected. Click 'Delete Selected' to remove them.",
                    bg="#d1ecf1",
                    fg="#0c5460",
                )
            else:
                self.status_label.config(
                    text="No nodes in selection area.",
                    bg=self.theme.COLORS["bg_sidebar"],
                    fg=self.theme.COLORS["text_primary"],
                )
        elif self.dragging_node and (not self.link_mode):
            snapped_x, snapped_y = self.snap_to_grid(event.x, event.y)
            self.nodes[self.dragging_node]["x"] = snapped_x
            self.nodes[self.dragging_node]["y"] = snapped_y
            self.draw_network()
            self.status_label.config(
                text=f"Node '{self.dragging_node}' moved to ({snapped_x}, {snapped_y})",
                bg="#d1ecf1",
                fg="#0c5460",
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
                bg="#fff3cd",
                fg="#856404",
            )

    def canvas_right_drag(self, event):
        if self.right_click_link_start:
            self.draw_network()
            start_node = self.nodes[self.right_click_link_start]
            self.canvas.create_line(
                start_node["x"],
                start_node["y"],
                event.x,
                event.y,
                fill="red",
                width=2,
                dash=(4, 4),
                tags="temp_link",
            )

    def canvas_right_release(self, event):
        if self.right_click_link_start:
            target_node = self.find_node_at(event.x, event.y)
            if target_node and target_node != self.right_click_link_start:
                link_exists = any(
                    link["node1"] == self.right_click_link_start
                    and link["node2"] == target_node
                    or (
                        link["node1"] == target_node
                        and link["node2"] == self.right_click_link_start
                    )
                    for link in self.links
                )
                if link_exists:
                    self.status_label.config(
                        text=f"Link already exists between {self.right_click_link_start} and {target_node}.",
                        bg="#f8d7da",
                        fg="#721c24",
                    )
                else:
                    self.links.append(
                        {
                            "node1": self.right_click_link_start,
                            "node2": target_node,
                            "bidirectional": True,
                        }
                    )
                    self.draw_network()
                    self.update_properties_display()
                    self.update_button_states()
                    self.status_label.config(
                        text=f"Link created: {self.right_click_link_start} ↔ {target_node}",
                        bg=self.theme.COLORS["bg_sidebar"],
                        fg=self.theme.COLORS["text_primary"],
                    )
            elif target_node == self.right_click_link_start:
                self.status_label.config(
                    text="Cannot create link to the same node.",
                    bg="#f8d7da",
                    fg="#721c24",
                )
            else:
                self.status_label.config(
                    text="Link creation cancelled - no target node.",
                    bg=self.theme.COLORS["bg_sidebar"],
                    fg=self.theme.COLORS["text_primary"],
                )
            self.right_click_link_start = None
            self.draw_network()

    def delete_selected(self):
        if self.selected_nodes:
            num_deleted = len(self.selected_nodes)
            for node_id in self.selected_nodes:
                if node_id in self.nodes:
                    del self.nodes[node_id]
            self.links = [
                link
                for link in self.links
                if link["node1"] not in self.selected_nodes
                and link["node2"] not in self.selected_nodes
            ]
            self.selected_nodes = []
            self.selected_node = None
            self.draw_network()
            self.update_properties_display()
            self.update_button_states()
            self.status_label.config(
                text=f"{num_deleted} node(s) deleted. Total nodes: {len(self.nodes)}",
                bg=self.theme.COLORS["bg_sidebar"],
                fg=self.theme.COLORS["text_primary"],
            )
        elif self.selected_node:
            node_id = self.selected_node
            del self.nodes[self.selected_node]
            self.links = [
                link
                for link in self.links
                if link["node1"] != self.selected_node and link["node2"] != self.selected_node
            ]
            self.selected_node = None
            self.draw_network()
            self.update_properties_display()
            self.update_button_states()
            self.status_label.config(
                text=f"Node '{node_id}' deleted. Total nodes: {len(self.nodes)}",
                bg=self.theme.COLORS["bg_sidebar"],
                fg=self.theme.COLORS["text_primary"],
            )

    def draw_network(self):
        self.canvas.delete("all")
        for link in self.links:
            n1 = self.nodes[link["node1"]]
            n2 = self.nodes[link["node2"]]
            self.canvas.create_line(n1["x"], n1["y"], n2["x"], n2["y"], fill="gray", width=2)
        for node_id, node in self.nodes.items():
            color = "#ff6b6b" if node["properties"].get("exposed_to_internet") else "#4ecdc4"
            is_selected = node_id == self.selected_node or node_id in self.selected_nodes
            outline_color = "blue" if is_selected else "black"
            outline_width = 4 if is_selected else 2
            self.canvas.create_oval(
                node["x"] - 20,
                node["y"] - 20,
                node["x"] + 20,
                node["y"] + 20,
                fill=color,
                outline=outline_color,
                width=outline_width,
            )
            self.canvas.create_text(
                node["x"],
                node["y"],
                text=node["id"][:8],
                font=self.theme.FONTS["body_small"],
            )
