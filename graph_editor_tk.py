import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
import json
from PIL import ImageGrab
import math

class GraphEditorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Interactive Graph Editor (Tkinter)")

        # Create main container
        self.main_container = tk.Frame(self.root)
        self.main_container.pack(fill=tk.BOTH, expand=True)

        # Status bar
        self.status_bar = tk.Label(
            self.root, 
            text="Ready", 
            bd=1, 
            relief=tk.SUNKEN, 
            anchor=tk.W,
            font=("Inter", 10),
            padx=5,
            pady=3
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # State
        self.nodes = []  # list of dicts: {id, x, y, label, type}
        self.edges = []  # list of dicts: {id, startNodeId, endNodeId, label}
        self.next_id = 1
        self.current_mode = 'select'  # 'select', 'node', 'junction', 'edge'        self.edge_start_node = None
        self.selected_nodes = set()  # Set of selected node IDs
        self.selected_edges = set()  # Set of selected edge IDs
        self.scale = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self.is_panning = False
        self.last_mouse = (0, 0)
        self.dragging_node = None
        self.drag_start_offset = (0, 0)

        # Colors
        self.SELECTION_COLOR = '#3b82f6'  # blue-500
        self.DEFAULT_COLOR = 'black'
        self.ACTIVE_BTN_BG = '#3b82f6'    # blue-500
        self.ACTIVE_BTN_FG = 'white'      # white text
        self.INACTIVE_BTN_BG = '#f5f5f5'  # gray-100
        self.INACTIVE_BTN_FG = 'black'    # black text

        # Setup UI
        self.create_toolbar()
        self.create_canvas()
        self.draw()

    def create_toolbar(self):
        toolbar = tk.Frame(self.main_container)  # Changed from self.root to self.main_container
        toolbar.pack(side=tk.LEFT, fill=tk.Y)
          # Tool buttons
        self.tool_buttons = []
        for text, cmd in [
            ("Select", self.set_select),
            ("Add Node", self.set_node),
            ("Add Junction", self.set_junction),
            ("Add Edge", self.set_edge)
        ]:
            btn = tk.Button(toolbar, text=text, width=12, command=cmd,
                          bg=self.INACTIVE_BTN_BG, fg=self.INACTIVE_BTN_FG)
            btn.pack(pady=2)
            self.tool_buttons.append(btn)
        
        # Set initial button state for 'select' mode
        self.tool_buttons[0].config(bg=self.ACTIVE_BTN_BG, fg=self.ACTIVE_BTN_FG)

        # Action buttons
        tk.Button(toolbar, text="Save Graph", width=12, command=self.save_graph).pack(pady=2)
        tk.Button(toolbar, text="Load Graph", width=12, command=self.load_graph).pack(pady=2)
        tk.Button(toolbar, text="Report", width=12, command=self.report).pack(pady=2)
        tk.Button(toolbar, text="Save PNG", width=12, command=self.save_png).pack(pady=2)
        
        # Delete and Clear buttons
        self.delete_btn = tk.Button(toolbar, text="Delete", width=12, 
                                  command=self.delete_selected, 
                                  state=tk.DISABLED)
        self.delete_btn.pack(pady=2)
        
        tk.Button(toolbar, text="Clear All", width=12, 
                 command=self.clear_canvas).pack(pady=2)

    def create_canvas(self):
        self.canvas = tk.Canvas(self.main_container)  # Changed from self.root to self.main_container
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind('<ButtonPress-1>', self.on_mouse_down)
        self.canvas.bind('<B1-Motion>', self.on_mouse_move)
        self.canvas.bind('<ButtonRelease-1>', self.on_mouse_up)
        self.canvas.bind('<MouseWheel>', self.on_mouse_wheel)
        self.canvas.bind('<ButtonPress-2>', self.start_pan)
        self.canvas.bind('<B2-Motion>', self.do_pan)
        self.canvas.bind('<ButtonRelease-2>', self.end_pan)

    def world_to_screen(self, x, y):
        sx = x * self.scale + self.pan_x
        sy = y * self.scale + self.pan_y
        return sx, sy

    def screen_to_world(self, sx, sy):
        x = (sx - self.pan_x) / self.scale
        y = (sy - self.pan_y) / self.scale
        return x, y

    def set_select(self):
        self.current_mode = 'select'
        self.update_status()
        self.update_button_colors()

    def set_node(self):
        self.current_mode = 'node'
        self.update_status()
        self.update_button_colors()

    def set_junction(self):
        self.current_mode = 'junction'
        self.update_status()
        self.update_button_colors()

    def set_edge(self):
        self.current_mode = 'edge'
        self.update_status()
        self.update_button_colors()

    def update_status(self):
        """Update the status bar text based on current state."""
        mode_info = {
            'select': "Select Mode: Click to select nodes/edges. Drag to move nodes.",
            'node': "Node Mode: Click to add a new node.",
            'junction': "Junction Mode: Click to add a new junction.",
            'edge': "Edge Mode: Click two nodes to create an edge between them."
        }

        status_text = mode_info.get(self.current_mode, "Ready")        # Add selection information if in select mode
        if self.current_mode == 'select':
            if self.selected_nodes:
                selected_nodes = [node for node in self.nodes if node['id'] in self.selected_nodes]
                if len(selected_nodes) == 1:
                    status_text += f" | Selected Node: {selected_nodes[0]['label']}"
                else:
                    status_text += f" | Selected {len(selected_nodes)} Nodes"
            if self.selected_edges:
                selected_edges = [edge for edge in self.edges if edge['id'] in self.selected_edges]
                if len(selected_edges) == 1:
                    status_text += f" | Selected Edge: {selected_edges[0]['label']}"
                else:
                    status_text += f" | Selected {len(selected_edges)} Edges"
        # Add edge creation progress if in edge mode
        elif self.current_mode == 'edge' and self.edge_start_node:
            status_text += f" | Start Node: {self.edge_start_node['label']} | Click another node to complete the edge"

        self.status_bar.config(text=status_text)
        self.update_button_colors()  # Update button colors on mode change

    def update_status_temp(self, message, duration=3000):
        """Update status bar with a message that disappears after duration (ms)"""
        self.status_bar.config(text=message)
        # Schedule reset of status bar        self.root.after(duration, lambda: self.status_bar.config(text="Ready"))

    def on_mouse_down(self, event):
        x, y = self.screen_to_world(event.x, event.y)
        # Check if Ctrl key is pressed for multi-select
        is_multi_select = event.state & 0x4  # 0x4 is the state for Control key
        if self.current_mode == 'node':
            label = simpledialog.askstring("Node Label", "Enter label for new node:")
            if label:
                self.nodes.append({
                    'id': self.next_id,
                    'x': x,
                    'y': y,
                    'label': label,
                    'type': 'node'
                })
                self.next_id += 1
                self.update_status()
                self.draw()
        elif self.current_mode == 'junction':
            label = simpledialog.askstring("Junction Label", "Enter label for new junction:")
            if label:
                self.nodes.append({                    'id': self.next_id,
                    'x': x,
                    'y': y,
                    'label': label,
                    'type': 'junction'
                })
                self.next_id += 1
                self.update_status()
                self.draw()
        elif self.current_mode == 'edge':
            node = self.get_node_at(x, y)
            if not self.edge_start_node and node:
                self.edge_start_node = node
                self.update_status_temp(f"Selected start node: {node['label']}. Click end node.")
            elif self.edge_start_node and node and node != self.edge_start_node:
                label = simpledialog.askstring("Edge Label", "Enter label for new edge:")
                if label:
                    self.edges.append({
                        'id': self.next_id,
                        'startNodeId': self.edge_start_node['id'],
                        'endNodeId': node['id'],
                        'label': label
                    })
                    self.next_id += 1
                    self.draw()
                self.edge_start_node = None
        else:  # 'select' mode
            # Check if Ctrl key is pressed for multi-select
            is_multi_select = event.state & 0x4  # 0x4 is the state for Control key
            node = self.get_node_at(x, y)
            edge = self.get_edge_at(x, y)
            
            if node:
                if is_multi_select:
                    # Toggle node selection
                    if node['id'] in self.selected_nodes:
                        self.selected_nodes.remove(node['id'])
                    else:
                        self.selected_nodes.add(node['id'])
                else:
                    # Single select, clear previous selections
                    self.selected_nodes = {node['id']}
                    self.selected_edges.clear()
                    self.dragging_node = node
                    self.drag_start_offset = (x - node['x'], y - node['y'])
            elif edge:
                if is_multi_select:
                    # Toggle edge selection
                    if edge['id'] in self.selected_edges:
                        self.selected_edges.remove(edge['id'])
                    else:
                        self.selected_edges.add(edge['id'])
                else:
                    # Single select, clear previous selections
                    self.selected_edges = {edge['id']}
                    self.selected_nodes.clear()
                    self.dragging_node = None
            elif not is_multi_select:
                # Click on empty space without Ctrl - clear all selections
                self.selected_nodes.clear()
                self.selected_edges.clear()
                self.dragging_node = None
            
            self.update_delete_button_state()
            self.update_status()
            self.draw()

    def on_mouse_move(self, event):
        if self.is_panning: # Pan logic should take precedence if active
            self.do_pan(event) # Call existing do_pan directly
            return

        if self.dragging_node and self.current_mode == 'select':
            x, y = self.screen_to_world(event.x, event.y)
            self.dragging_node['x'] = x - self.drag_start_offset[0]
            self.dragging_node['y'] = y - self.drag_start_offset[1]
            self.draw()

    def on_mouse_up(self, event):
        if self.is_panning: # Ensure panning state is correctly reset
            self.end_pan(event) # Call existing end_pan
            # Do not reset dragging_node here if panning was the primary action
            return

        if self.dragging_node and self.current_mode == 'select':
            self.dragging_node = None
            # self.draw() # Optional: draw if needed, though mouse_move usually covers it

    def start_pan(self, event):
        self.is_panning = True
        self.last_mouse = (event.x, event.y)

    def do_pan(self, event):
        if self.is_panning:
            dx = event.x - self.last_mouse[0]
            dy = event.y - self.last_mouse[1]
            self.pan_x += dx
            self.pan_y += dy
            self.last_mouse = (event.x, event.y)
            self.draw()

    def end_pan(self, event):
        self.is_panning = False

    def on_mouse_wheel(self, event):
        factor = 1.0 + event.delta * 0.001
        # get mouse world coord
        wx, wy = self.screen_to_world(event.x, event.y)
        self.scale = min(max(self.scale * factor, 0.1), 5)
        # adjust pan to zoom on cursor
        self.pan_x = event.x - wx * self.scale
        self.pan_y = event.y - wy * self.scale
        self.draw()

    def get_node_at(self, x, y):
        # Check in reverse order so top nodes are found first (if overlapping)
        for node in reversed(self.nodes):
            # Define hit area based on node type, in world coordinates
            if node['type'] == 'junction':
                # Junction: rectangle centered at node['x'], node['y']
                # Dimensions are fixed in screen pixels, so convert to world for hit check
                half_width_world = (15) / self.scale # 15 is half of JUNCTION_WIDTH in HTML
                half_height_world = (3) / self.scale # 3 is half of JUNCTION_HEIGHT in HTML
                if (node['x'] - half_width_world <= x <= node['x'] + half_width_world and
                    node['y'] - half_height_world <= y <= node['y'] + half_height_world):
                    return node
            else: # 'node' type
                # Node: circle centered at node['x'], node['y']
                # Radius is fixed in screen pixels (5), so convert to world for hit check
                # Using a slightly larger hit radius for easier selection, e.g., 10 screen pixels
                hit_radius_world = 10 / self.scale 
                dist_sq = (x - node['x'])**2 + (y - node['y'])**2
                if dist_sq < hit_radius_world**2:
                    return node
        return None

    def get_edge_at(self, x, y):
        # Convert world coordinates to screen coordinates for hit testing
        tolerance = 5 / self.scale  # 5 pixels tolerance in world coordinates
        for edge in reversed(self.edges):
            start_node = next((n for n in self.nodes if n['id'] == edge['startNodeId']), None)
            end_node = next((n for n in self.nodes if n['id'] == edge['endNodeId']), None)
            if not start_node or not end_node:
                continue

            # Calculate distance from point to line segment
            x1, y1 = start_node['x'], start_node['y']
            x2, y2 = end_node['x'], end_node['y']
            
            # Vector math for point-to-line-segment distance
            px, py = x, y
            line_length_sq = (x2-x1)**2 + (y2-y1)**2
            if line_length_sq == 0:
                continue
            
            t = max(0, min(1, ((px-x1)*(x2-x1) + (py-y1)*(y2-y1)) / line_length_sq))
            proj_x = x1 + t*(x2-x1)
            proj_y = y1 + t*(y2-y1)
            
            dist_sq = (px-proj_x)**2 + (py-proj_y)**2
            if dist_sq <= tolerance**2:
                return edge
        return None

    def get_edge_connection_point(self, source_node, target_node):
        """Calculate the point where an edge should connect to a node, with appropriate offset."""
        # Calculate direction vector from source to target
        dx = target_node['x'] - source_node['x']
        dy = target_node['y'] - source_node['y']
        angle = math.atan2(dy, dx)
        
        # Different offsets based on node type
        if source_node['type'] == 'junction':
            # For junctions, use rectangular hit detection
            w = 15  # half width
            h = 3   # half height
            
            # Calculate intersection with junction rectangle
            if w * abs(math.sin(angle)) > h * abs(math.cos(angle)):
                # Intersects top/bottom edge
                intersect_x = source_node['x'] + h * math.cos(angle) / abs(math.sin(angle)) * math.copysign(1, math.sin(angle))
                intersect_y = source_node['y'] + h * math.copysign(1, math.sin(angle))
            else:
                # Intersects left/right edge
                intersect_x = source_node['x'] + w * math.copysign(1, math.cos(angle))
                intersect_y = source_node['y'] + w * math.sin(angle) / abs(math.cos(angle)) * math.copysign(1, math.cos(angle))
            
            # Add extra offset
            JUNCTION_CONNECTION_OFFSET = 25
            return {
                'x': intersect_x + JUNCTION_CONNECTION_OFFSET * math.cos(angle),
                'y': intersect_y + JUNCTION_CONNECTION_OFFSET * math.sin(angle)
            }
        else:
            # For regular nodes, use circular offset
            NODE_CONNECTION_OFFSET = 30
            return {
                'x': source_node['x'] + NODE_CONNECTION_OFFSET * math.cos(angle),
                'y': source_node['y'] + NODE_CONNECTION_OFFSET * math.sin(angle)
            }

    def draw_arrowhead(self, x1, y1, x2, y2, color):
        """Draw a single-wing arrowhead at point (x2, y2)."""
        # Calculate angle of the line
        angle = math.atan2(y2 - y1, x2 - x1)
        
        # Arrowhead parameters
        headlen = 10  # Length of arrowhead
        angle_wing = math.pi / 7  # Angle of the wing (about 25.7 degrees)
        
        # Calculate the point for the single wing
        wing_x = x2 - headlen * math.cos(angle - angle_wing)
        wing_y = y2 - headlen * math.sin(angle - angle_wing)
        
        # Calculate a point halfway back along the edge for the base of the arrowhead
        base_x = x2 - headlen * 0.5 * math.cos(angle)
        base_y = y2 - headlen * 0.5 * math.sin(angle)
        
        # Draw filled arrowhead
        self.canvas.create_polygon(
            x2, y2,  # Tip
            wing_x, wing_y,  # Wing point
            base_x, base_y,  # Base point
            fill=color, outline=color
        )

    def draw(self):
        self.canvas.delete('all')
        # draw edges
        for edge in self.edges:
            start_node_obj = next((n for n in self.nodes if n['id'] == edge['startNodeId']), None)
            end_node_obj = next((n for n in self.nodes if n['id'] == edge['endNodeId']), None)
            if not start_node_obj or not end_node_obj:
                continue

            # Get connection points with offsets
            start_point = self.get_edge_connection_point(start_node_obj, end_node_obj)
            end_point = self.get_edge_connection_point(end_node_obj, start_node_obj)
            
            # Convert to screen coordinates
            x1, y1 = self.world_to_screen(start_point['x'], start_point['y'])
            x2, y2 = self.world_to_screen(end_point['x'], end_point['y'])
              # Set edge color based on selection
            is_selected = edge['id'] in self.selected_edges
            edge_color = self.SELECTION_COLOR if is_selected else self.DEFAULT_COLOR
            
            # Draw the edge line
            self.canvas.create_line(
                x1, y1, x2, y2,
                fill=edge_color,
                width=2 if is_selected else 1,
                tags=("edge", f"edge_{edge['id']}")
            )
            
            # Draw custom arrowhead
            self.draw_arrowhead(x1, y1, x2, y2, edge_color)
            
            # Draw label at midpoint
            mx = (x1 + x2) / 2
            my = (y1 + y2) / 2 - 10  # Offset label slightly above the line
            self.canvas.create_text(
                mx, my,
                text=edge['label'],
                font=("Inter", 10),
                fill=edge_color,
                tags=("edge_label", f"edge_label_{edge['id']}"))
        
        # draw nodes
        for node in self.nodes:
            x, y = self.world_to_screen(node['x'], node['y'])            # Set node color based on selection
            is_selected = node['id'] in self.selected_nodes
            node_color = self.SELECTION_COLOR if is_selected else self.DEFAULT_COLOR
            
            if node['type']=='junction':
                self.canvas.create_rectangle(x-15, y-3, x+15, y+3, 
                                         fill=node_color,
                                         tags=("node", f"node_{node['id']}"))
                self.canvas.create_text(x, y-15, 
                                    text=node['label'], 
                                    font=("Inter", 10),
                                    fill=node_color,
                                    tags=("node_label", f"node_label_{node['id']}"))
            else:
                self.canvas.create_oval(x-5, y-5, x+5, y+5, 
                                    fill=node_color,
                                    tags=("node", f"node_{node['id']}"))
                self.canvas.create_text(x, y+15, 
                                    text=node['label'], 
                                    font=("Inter", 10),
                                    fill=node_color,
                                    tags=("node_label", f"node_label_{node['id']}"))

    def save_graph(self):
        data = {'nodes': self.nodes, 'edges': self.edges, 'next_id': self.next_id}
        path = filedialog.asksaveasfilename(defaultextension='.json', filetypes=[('JSON','*.json')])
        if path:
            with open(path, 'w') as f:
                json.dump(data, f, indent=2)

    def load_graph(self):
        path = filedialog.askopenfilename(filetypes=[('JSON','*.json')])
        if path:
            with open(path) as f:
                data = json.load(f)
                self.nodes = data['nodes']
                self.edges = data['edges']
                self.next_id = data.get('next_id', self.next_id)
                self.draw()

    def report(self):
        report = 'Nodes:\n'
        for n in self.nodes:
            report += f"  - ID: {n['id']}, Label: {n['label']}, Type: {n['type']}, X: {n['x']:.1f}, Y: {n['y']:.1f}\n"
        report += '\nEdges:\n'
        for e in self.edges:
            start_node = next((n for n in self.nodes if n['id'] == e['startNodeId']), None)
            end_node = next((n for n in self.nodes if n['id'] == e['endNodeId']), None)
            start_label = start_node['label'] if start_node else 'N/A'
            end_label = end_node['label'] if end_node else 'N/A'
            report += f"  - ID: {e['id']}, Label: {e['label']}, From: {start_label} (ID: {e['startNodeId']}) To: {end_label} (ID: {e['endNodeId']})\n"
        path = filedialog.asksaveasfilename(defaultextension='.txt', filetypes=[('Text','*.txt')])
        if path:
            with open(path, 'w') as f:
                f.write(report)
            self.update_status_temp("Report saved to text file")

    def save_png(self):
        x = self.root.winfo_rootx() + self.canvas.winfo_x()
        y = self.root.winfo_rooty() + self.canvas.winfo_y()
        x1 = x + self.canvas.winfo_width()
        y1 = y + self.canvas.winfo_height()
        path = filedialog.asksaveasfilename(defaultextension='.png', filetypes=[('PNG','*.png')])
        if path:
            ImageGrab.grab().crop((x, y, x1, y1)).save(path)

    def delete_selected(self):
        total_nodes_deleted = 0
        total_edges_deleted = 0
        
        # Delete selected nodes and their connected edges
        if self.selected_nodes:
            original_edge_count = len(self.edges)
            # Remove any edges connected to any selected node
            self.edges = [edge for edge in self.edges 
                         if edge['startNodeId'] not in self.selected_nodes 
                         and edge['endNodeId'] not in self.selected_nodes]
            total_edges_deleted = original_edge_count - len(self.edges)
            
            # Remove the selected nodes
            original_node_count = len(self.nodes)
            self.nodes = [node for node in self.nodes if node['id'] not in self.selected_nodes]
            total_nodes_deleted = original_node_count - len(self.nodes)
            self.selected_nodes.clear()
            self.dragging_node = None
            
        # Delete selected edges
        if self.selected_edges:
            original_edge_count = len(self.edges)
            self.edges = [edge for edge in self.edges if edge['id'] not in self.selected_edges]
            total_edges_deleted += original_edge_count - len(self.edges)
            self.selected_edges.clear()
            
        # Update status message
        if total_nodes_deleted and total_edges_deleted:
            self.update_status_temp(f"Deleted {total_nodes_deleted} node(s) and {total_edges_deleted} edge(s)")
        elif total_nodes_deleted:
            self.update_status_temp(f"Deleted {total_nodes_deleted} node(s)")
        elif total_edges_deleted:
            self.update_status_temp(f"Deleted {total_edges_deleted} edge(s)")
            
        self.update_delete_button_state()
        self.update_status()
        self.draw()

    def update_delete_button_state(self):
        # Enable/disable delete button based on selection
        if self.selected_nodes or self.selected_edges:
            self.delete_btn.config(state=tk.NORMAL)
        else:
            self.delete_btn.config(state=tk.DISABLED)

    def clear_canvas(self):
        if messagebox.askyesno("Clear All", "Are you sure you want to clear the entire canvas?"):
            self.nodes = []
            self.edges = []
            self.next_id = 1
            self.selected_node = None
            self.selected_edge = None
            self.dragging_node = None
            self.edge_start_node = None
            self.update_delete_button_state()
            self.update_status()
            self.draw()
            self.update_status_temp("Canvas cleared")

    def update_button_colors(self):
        """Update the tool buttons' colors based on the current mode"""
        mode_to_index = {'select': 0, 'node': 1, 'junction': 2, 'edge': 3}
        current_index = mode_to_index.get(self.current_mode, -1)
        
        for i, btn in enumerate(self.tool_buttons):
            if i == current_index:
                btn.config(bg=self.ACTIVE_BTN_BG, fg=self.ACTIVE_BTN_FG)
            else:
                btn.config(bg=self.INACTIVE_BTN_BG, fg=self.INACTIVE_BTN_FG)

if __name__ == '__main__':
    root = tk.Tk()
    app = GraphEditorApp(root)
    root.mainloop()
