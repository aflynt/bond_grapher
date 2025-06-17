import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
import json
from PIL import ImageGrab
import math

class GraphEditorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Interactive Graph Editor (Tkinter)")

        # State
        self.nodes = []  # list of dicts: {id, x, y, label, type}
        self.edges = []  # list of dicts: {id, startNodeId, endNodeId, label}
        self.next_id = 1
        self.current_mode = 'select'  # 'select', 'node', 'junction', 'edge'
        self.edge_start_node = None
        self.selected_node = None  # Currently selected node
        self.selected_edge = None  # Currently selected edge
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

        # Setup UI
        self.create_toolbar()
        self.create_canvas()
        self.draw()

    def create_toolbar(self):
        toolbar = tk.Frame(self.root)
        toolbar.pack(side=tk.LEFT, fill=tk.Y)
        
        # Tool buttons
        self.tool_buttons = []
        for text, cmd in [
            ("Select", self.set_select),
            ("Add Node", self.set_node),
            ("Add Junction", self.set_junction),
            ("Add Edge", self.set_edge)
        ]:
            btn = tk.Button(toolbar, text=text, width=12, command=cmd)
            btn.pack(pady=2)
            self.tool_buttons.append(btn)

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
        self.canvas = tk.Canvas(self.root, bg='#f8fafc')
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

    def on_mouse_down(self, event):
        x, y = self.screen_to_world(event.x, event.y)
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
                self.draw()
        elif self.current_mode == 'junction':
            label = simpledialog.askstring("Junction Label", "Enter label for new junction:")
            if label:
                self.nodes.append({
                    'id': self.next_id,
                    'x': x,
                    'y': y,
                    'label': label,
                    'type': 'junction'
                })
                self.next_id += 1
                self.draw()
        elif self.current_mode == 'edge':
            node = self.get_node_at(x, y)
            if not self.edge_start_node and node:
                self.edge_start_node = node
                messagebox.showinfo("Edge Creation", f"Selected start node: {node['label']}. Click end node.")
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
            node = self.get_node_at(x, y)
            edge = self.get_edge_at(x, y)
            
            if node:
                self.selected_node = node
                self.selected_edge = None
                self.dragging_node = node
                self.drag_start_offset = (x - node['x'], y - node['y'])
            elif edge:
                self.selected_edge = edge
                self.selected_node = None
                self.dragging_node = None
            else:
                self.selected_node = None
                self.selected_edge = None
                self.dragging_node = None
            
            self.update_delete_button_state()
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
            edge_color = self.SELECTION_COLOR if edge == self.selected_edge else self.DEFAULT_COLOR
            self.canvas.create_line(x1, y1, x2, y2, 
                                 arrow=tk.LAST, 
                                 fill=edge_color,
                                 width=2 if edge == self.selected_edge else 1,
                                 tags=("edge", f"edge_{edge['id']}"))
            
            # Draw label at midpoint
            mx = (x1 + x2) / 2
            my = (y1 + y2) / 2 - 10  # Offset label slightly above the line
            self.canvas.create_text(mx, my, 
                                 text=edge['label'], 
                                 font=("Inter", 10),
                                 fill=edge_color,
                                 tags=("edge_label", f"edge_label_{edge['id']}"))
        
        # draw nodes
        for node in self.nodes:
            x, y = self.world_to_screen(node['x'], node['y'])
            # Set node color based on selection
            node_color = self.SELECTION_COLOR if node == self.selected_node else self.DEFAULT_COLOR
            
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

    def set_select(self):
        self.current_mode = 'select'
    def set_node(self):
        self.current_mode = 'node'
    def set_junction(self):
        self.current_mode = 'junction'
    def set_edge(self):
        self.current_mode = 'edge'

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
        messagebox.showinfo('Graph Report', report)

    def save_png(self):
        x = self.root.winfo_rootx() + self.canvas.winfo_x()
        y = self.root.winfo_rooty() + self.canvas.winfo_y()
        x1 = x + self.canvas.winfo_width()
        y1 = y + self.canvas.winfo_height()
        path = filedialog.asksaveasfilename(defaultextension='.png', filetypes=[('PNG','*.png')])
        if path:
            ImageGrab.grab().crop((x, y, x1, y1)).save(path)

    def delete_selected(self):
        if self.selected_node:
            # Remove any edges connected to this node
            original_edge_count = len(self.edges)
            self.edges = [edge for edge in self.edges 
                         if edge['startNodeId'] != self.selected_node['id'] 
                         and edge['endNodeId'] != self.selected_node['id']]
            edges_removed = original_edge_count - len(self.edges)
            
            # Remove the node
            self.nodes = [node for node in self.nodes if node['id'] != self.selected_node['id']]
            self.selected_node = None
            self.dragging_node = None
            
            if edges_removed > 0:
                messagebox.showinfo("Delete", f"Node and {edges_removed} connected edge(s) deleted")
            else:
                messagebox.showinfo("Delete", "Node deleted")
                
        elif self.selected_edge:
            # Remove just the edge
            self.edges = [edge for edge in self.edges if edge['id'] != self.selected_edge['id']]
            self.selected_edge = None
            messagebox.showinfo("Delete", "Edge deleted")
            
        self.update_delete_button_state()
        self.draw()

    def update_delete_button_state(self):
        # Enable/disable delete button based on selection
        if self.selected_node or self.selected_edge:
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
            self.draw()
            messagebox.showinfo("Clear All", "Canvas cleared")

if __name__ == '__main__':
    root = tk.Tk()
    app = GraphEditorApp(root)
    root.mainloop()
