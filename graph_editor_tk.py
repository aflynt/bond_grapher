import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
import json
from PIL import ImageGrab

class GraphEditorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Interactive Graph Editor (Tkinter)")

        # State
        self.nodes = []  # list of dicts: {id, x, y, label, type}
        self.edges = []  # list of dicts: {id, start, end, label}
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
        btns = [
            ("Select", self.set_select),
            ("Add Node", self.set_node),
            ("Add Junction", self.set_junction),
            ("Add Edge", self.set_edge),
            ("Save Graph", self.save_graph),
            ("Load Graph", self.load_graph),
            ("Report", self.report),
            ("Save PNG", self.save_png),
            ("Delete", self.delete_selected),
            ("Clear", self.clear_canvas)
        ]
        for text, cmd in btns:
            b = tk.Button(toolbar, text=text, width=12, command=cmd)
            b.pack(pady=2)

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
                self.nodes.append({'id': self.next_id, 'x': x, 'y': y, 'label': label, 'type': 'node'})
                self.next_id += 1
                self.draw()
        elif self.current_mode == 'junction':
            label = simpledialog.askstring("Junction Label", "Enter label for new junction:")
            if label:
                self.nodes.append({'id': self.next_id, 'x': x, 'y': y, 'label': label, 'type': 'junction'})
                self.next_id += 1
                self.draw()
        elif self.current_mode == 'edge':
            node = self.get_node_at(x, y)
            if not self.edge_start_node and node:
                self.edge_start_node = node
            elif self.edge_start_node and node and node != self.edge_start_node:
                label = simpledialog.askstring("Edge Label", "Enter label for new edge:")
                if label:
                    self.edges.append({'id': self.next_id, 'start': self.edge_start_node['id'], 'end': node['id'], 'label': label})
                    self.next_id += 1
                self.edge_start_node = None
                self.draw()
        else: # 'select' mode
            node = self.get_node_at(x, y)
            edge = self.get_edge_at(x, y)
            
            # Handle selection
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
            start_node = next((n for n in self.nodes if n['id'] == edge['start']), None)
            end_node = next((n for n in self.nodes if n['id'] == edge['end']), None)
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

    def draw(self):
        self.canvas.delete('all')
        # draw edges
        for edge in self.edges:
            start_node_obj = next((n for n in self.nodes if n['id'] == edge['start']), None)
            end_node_obj = next((n for n in self.nodes if n['id'] == edge['end']), None)
            if not start_node_obj or not end_node_obj:
                continue

            x1, y1 = self.world_to_screen(start_node_obj['x'], start_node_obj['y'])
            x2, y2 = self.world_to_screen(end_node_obj['x'], end_node_obj['y'])
            
            # Set edge color based on selection
            edge_color = self.SELECTION_COLOR if edge == self.selected_edge else self.DEFAULT_COLOR
            self.canvas.create_line(x1, y1, x2, y2, 
                                 arrow=tk.LAST, 
                                 fill=edge_color,
                                 width=2 if edge == self.selected_edge else 1,
                                 tags=("edge", f"edge_{edge['id']}"))
            
            mx, my = (x1+x2)/2, (y1+y2)/2
            self.canvas.create_text(mx, my-10, 
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
            report += f"  - ID: {e['id']}, Label: {e['label']}, From: {e['start']} To: {e['end']}\n"
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
        # Placeholder: no selection in basic port
        pass

    def clear_canvas(self):
        if messagebox.askyesno('Clear Canvas', 'Are you sure?'):
            self.nodes.clear()
            self.edges.clear()
            self.next_id = 1
            self.draw()

if __name__ == '__main__':
    root = tk.Tk()
    app = GraphEditorApp(root)
    root.mainloop()
