import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
import json
from PIL import Image
import io
import math
import lib_bonds as lb
from lib_bonds import FLOWSIDE, FlyEdge, NODETYPE

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
        self.current_mode = 'select'  # 'select', 'edge', or NODETYPE.value
        self.current_nodetype = None  # Will store the NODETYPE when in node creation mode
        self.edge_start_node = None
        self.selected_nodes = set()  # Set of selected node IDs
        self.selected_edges = set()  # Set of selected edge IDs
        self.scale = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self.is_panning = False
        self.last_mouse = (0, 0)
        self.is_dragging = False
        self.drag_start_offsets = {}  # Dictionary of node_id: (offset_x, offset_y)
        self.box_select_start = None   # (x, y) in screen coordinates
        self.box_select_rect = None    # Flag to indicate if we're drawing a box
        self.box_select_last_pos = None  # Store last mouse position for box selection
        self.edge_drag_start = None    # Store start node for edge dragging
        self.edge_drag_end = None      # Store current mouse position for edge preview

        # Colors
        self.SELECTION_COLOR = '#3b82f6'  # blue-500
        self.DEFAULT_COLOR = 'black'
        self.BOX_SELECT_COLOR = '#3b82f6'  # blue-500 for selection box outline
        self.ACTIVE_BTN_BG = '#3b82f6'    # blue-500
        self.ACTIVE_BTN_FG = 'white'      # white text
        self.INACTIVE_BTN_BG = '#f5f5f5'  # gray-100
        self.INACTIVE_BTN_FG = 'black'    # black text

        # Setup UI
        self.create_toolbar()
        self.create_canvas()
        self.setup_context_menu()
        self.draw()        
        # Add keyboard bindings
        self.root.bind('<Delete>', self.handle_delete_key)
        self.root.bind('<BackSpace>', self.handle_delete_key)
        self.root.bind('<Escape>', self.handle_escape_key)
        self.root.bind('<KeyPress-e>', self.handle_e_key)
        self.root.bind('<KeyPress-E>', self.handle_e_key)
        self.root.bind('<KeyPress-s>', self.handle_s_key)
        self.root.bind('<KeyPress-S>', self.handle_s_key)
        self.root.bind('<KeyPress-f>', self.handle_f_key)
        self.root.bind('<KeyPress-F>', self.handle_f_key)
        self.root.bind('<KeyPress-i>', self.handle_i_key)
        self.root.bind('<KeyPress-I>', self.handle_i_key)
        self.root.bind('<KeyPress-c>', self.handle_c_key)
        self.root.bind('<KeyPress-C>', self.handle_c_key)
        self.root.bind('<KeyPress-r>', self.handle_r_key)
        self.root.bind('<KeyPress-R>', self.handle_r_key)
        self.root.bind('<KeyPress-g>', self.handle_g_key)
        self.root.bind('<KeyPress-G>', self.handle_g_key)
        self.root.bind('<KeyPress-t>', self.handle_t_key)
        self.root.bind('<KeyPress-T>', self.handle_t_key)
        self.root.bind('<KeyPress-0>', self.handle_0_key)
        self.root.bind('<KeyPress-1>', self.handle_1_key)

        # Clipboard for copy/paste
        self.clipboard_nodes = []
        self.clipboard_edges = []  # Added clipboard_edges to store copied edges        # Keyboard bindings for copy/paste
        self.root.bind('<Control-c>', self.handle_copy)
        self.root.bind('<Control-C>', self.handle_copy)
        self.root.bind('<Control-v>', self.handle_paste)
        self.root.bind('<Control-V>', self.handle_paste)

    def create_toolbar(self):
        toolbar = tk.Frame(self.main_container)  # Changed from self.root to self.main_container
        toolbar.pack(side=tk.LEFT, fill=tk.Y)
          # Tool buttons
        self.tool_buttons = []
        
        # Select button
        btn = tk.Button(toolbar, text="Select", width=12, command=self.set_select,
                      bg=self.INACTIVE_BTN_BG, fg=self.INACTIVE_BTN_FG)
        btn.pack(pady=2)
        self.tool_buttons.append(btn)
        
        # Node type buttons - one for each NODETYPE
        for nodetype in NODETYPE:
            btn = tk.Button(toolbar, text=f"Add {nodetype.value}", width=12, 
                          command=lambda nt=nodetype: self.set_nodetype(nt),
                          bg=self.INACTIVE_BTN_BG, fg=self.INACTIVE_BTN_FG)
            btn.pack(pady=2)
            self.tool_buttons.append(btn)
        
        # Edge button
        btn = tk.Button(toolbar, text="Add Edge", width=12, command=self.set_edge,
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
        delete_btn = tk.Button(toolbar, text="Delete", width=12, command=self.delete_selected, state=tk.DISABLED)
        delete_btn.pack(pady=2)
        self.delete_btn = delete_btn
        
        tk.Button(toolbar, text="Clear All", width=12, command=self.clear_canvas).pack(pady=2)
        tk.Button(toolbar, text="Clear Causality", width=12, command=self.clear_causality).pack(pady=2)

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
        self.canvas.bind('<Button-3>', self.show_context_menu)  # Right-click context menu

    def setup_context_menu(self):
        """Initialize the right-click context menu"""
        self.context_menu = tk.Menu(self.root, tearoff=0)

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
        self.current_nodetype = None
        # Clear edge state when switching modes
        self.edge_start_node = None
        self.edge_drag_start = None
        self.edge_drag_end = None
        self.update_status()
        self.update_button_colors()

    def set_nodetype(self, nodetype):
        self.current_mode = 'nodetype'
        self.current_nodetype = nodetype
        # Clear edge state when switching modes
        self.edge_start_node = None
        self.edge_drag_start = None
        self.edge_drag_end = None
        self.update_status()
        self.update_button_colors()

    def set_edge(self):
        self.current_mode = 'edge'
        self.current_nodetype = None
        # Clear edge state when switching to edge mode
        self.edge_start_node = None
        self.edge_drag_start = None
        self.edge_drag_end = None
        self.update_status()
        self.update_button_colors()

    def update_status(self):
        """Update the status bar text based on current state."""
        mode_info = {
            'select': "Select Mode: Click to select nodes/edges. Drag to move nodes.",
            'nodetype': f"Add {self.current_nodetype.value} Mode: Click to add a new {self.current_nodetype.value} node." if self.current_nodetype else "Node Mode",
            'edge': "Edge Mode: Click and drag from one node to another to create an edge."
        }

        status_text = mode_info.get(self.current_mode, "Ready")# Add selection information if in select mode
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
        elif self.current_mode == 'edge':
            if self.edge_drag_start:
                status_text += f" | Dragging from: {self.edge_drag_start['label']} | Release on target node to create edge"
            elif self.edge_start_node:
                status_text += f" | Start Node: {self.edge_start_node['label']} | Click another node to complete the edge"

        self.status_bar.config(text=status_text)
        self.update_button_colors()  # Update button colors on mode change

    def update_status_temp(self, message, duration=3000):
        """Update status bar with a message that disappears after duration (ms)"""
        self.status_bar.config(text=message)
        # Schedule reset of status bar
        self.root.after(duration, lambda: self.status_bar.config(text="Ready"))

    def on_mouse_down(self, event):
        x, y = self.screen_to_world(event.x, event.y)
        if self.current_mode == 'nodetype' and self.current_nodetype:
            # Create a node with the current nodetype
            label = self.get_next_node_label(self.current_nodetype.value)
            # Determine if this is a junction (0 or 1) or regular node
            node_type = 'junction' if self.current_nodetype.value in ['0', '1'] else 'node'
            self.nodes.append({
                'id': self.next_id,
                'x': x,
                'y': y,
                'label': label,
                'type': node_type,
                'nodetype': self.current_nodetype.value
            })
            self.next_id += 1
            self.update_status()
            self.draw()
        elif self.current_mode == 'edge':
            node = self.get_node_at(x, y)
            if node:
                # Start edge dragging from this node
                self.edge_drag_start = node
                self.edge_drag_end = (event.x, event.y)  # Store screen coordinates for preview
                self.update_status_temp(f"Dragging edge from: {node['label']}. Drag to target node.")
            elif not self.edge_start_node:
                # If no node clicked and no previous start node, clear any existing edge state
                self.edge_start_node = None
                self.edge_drag_start = None
                self.edge_drag_end = None
        else:  # 'select' mode
            # Check if Ctrl key is pressed for explicit multi-select behavior
            is_multi_select = event.state & 0x4  # 0x4 is the state for Control key
            node = self.get_node_at(x, y)
            edge = self.get_edge_at(x, y)

            if node:
                if is_multi_select:
                    # Ctrl+Click toggles selection
                    if node['id'] in self.selected_nodes:
                        self.selected_nodes.remove(node['id'])
                    else:
                        self.selected_nodes.add(node['id'])
                else:
                    # Standard click: select only this node, unless already selected (then keep all selection)
                    if node['id'] not in self.selected_nodes:
                        self.selected_nodes = {node['id']}
                        self.selected_edges.clear()
                    # else: already selected, keep all selection
                # Set up dragging for all selected nodes
                if node['id'] in self.selected_nodes:
                    self.is_dragging = True
                    self.drag_start_offsets.clear()
                    for n in self.nodes:
                        if n['id'] in self.selected_nodes:
                            self.drag_start_offsets[n['id']] = (x - n['x'], y - n['y'])

            elif edge:
                if is_multi_select:
                    # Ctrl+Click toggles selection
                    if edge['id'] in self.selected_edges:
                        self.selected_edges.remove(edge['id'])
                    else:
                        self.selected_edges.add(edge['id'])
                else:
                    # Standard click: select only this edge, unless already selected (then keep all selection)
                    if edge['id'] not in self.selected_edges:
                        self.selected_edges = {edge['id']}
                        self.selected_nodes.clear()
                    # else: already selected, keep all selection
            else:
                # Click on empty space - start box selection or clear selection
                if not is_multi_select:
                    self.selected_nodes.clear()
                    self.selected_edges.clear()
                # Start box selection
                self.box_select_start = (event.x, event.y)  # Store screen coordinates

            self.update_delete_button_state()
            self.update_status()
            self.draw()

    def on_mouse_move(self, event):
        if self.is_panning: # Pan logic should take precedence if active
            self.do_pan(event)
            return

        if self.is_dragging and self.current_mode == 'select':
            x, y = self.screen_to_world(event.x, event.y)
            # Move all selected nodes
            for node in self.nodes:
                if node['id'] in self.selected_nodes:
                    offset_x, offset_y = self.drag_start_offsets[node['id']]
                    node['x'] = x - offset_x
                    node['y'] = y - offset_y
            self.draw()
        elif self.edge_drag_start and self.current_mode == 'edge':
            # Update edge drag preview
            self.edge_drag_end = (event.x, event.y)
            self.draw()
        elif self.box_select_start and self.current_mode == 'select':
            # Update box selection
            self.box_select_last_pos = (event.x, event.y)
            self.draw()

    def on_mouse_up(self, event):
        if self.is_panning: # Ensure panning state is correctly reset
            self.end_pan(event) # Call existing end_pan
            return

        if self.is_dragging and self.current_mode == 'select':
            self.is_dragging = False
            self.drag_start_offsets.clear()
        elif self.edge_drag_start and self.current_mode == 'edge':
            # Check if we ended on a different node
            x, y = self.screen_to_world(event.x, event.y)
            end_node = self.get_node_at(x, y)
            if end_node and end_node != self.edge_drag_start:
                # Create the edge
                next_number = self.get_next_edge_number()
                self.edges.append({
                    'id': self.next_id,
                    'startNodeId': self.edge_drag_start['id'],
                    'endNodeId': end_node['id'],
                    'label': next_number,
                    'flow_side': FLOWSIDE.IDK.value
                })
                self.next_id += 1
                self.update_status_temp(f"Edge created from {self.edge_drag_start['label']} to {end_node['label']}")
            else:
                self.update_status_temp("Edge creation cancelled - must end on a different node")
            
            # Clean up edge drag state
            self.edge_drag_start = None
            self.edge_drag_end = None
            self.draw()
        elif self.box_select_start and self.current_mode == 'select':
            # Get selection box coordinates in screen space
            x1, y1 = self.box_select_start
            x2, y2 = event.x, event.y
            
            # Convert to world coordinates for checking nodes
            wx1, wy1 = self.screen_to_world(min(x1, x2), min(y1, y2))
            wx2, wy2 = self.screen_to_world(max(x1, x2), max(y1, y2))
            
            # Check for Ctrl key for adding to existing selection
            is_multi_select = event.state & 0x4
            if not is_multi_select:
                self.selected_nodes.clear()
                self.selected_edges.clear()
            
            # Select nodes in box
            for node in self.nodes:
                if wx1 <= node['x'] <= wx2 and wy1 <= node['y'] <= wy2:
                    self.selected_nodes.add(node['id'])
            
            # Select edges with both endpoints in box
            for edge in self.edges:
                start_node = next((n for n in self.nodes if n['id'] == edge['startNodeId']), None)
                end_node = next((n for n in self.nodes if n['id'] == edge['endNodeId']), None)
                if start_node and end_node:
                    if (wx1 <= start_node['x'] <= wx2 and wy1 <= start_node['y'] <= wy2 and
                        wx1 <= end_node['x'] <= wx2 and wy1 <= end_node['y'] <= wy2):
                        self.selected_edges.add(edge['id'])
            
            # Clean up box selection
            self.box_select_start = None
            self.box_select_last_pos = None
            self.draw()
            self.update_status()
            self.update_delete_button_state()

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

    def draw_tee(self, x, y, angle, color, length=12):
        """Draw a Tee (perpendicular line) at (x, y) with given angle and length."""
        # Tee is perpendicular to the edge
        perp_angle = angle + math.pi / 2
        dx = (length / 2) * math.cos(perp_angle)
        dy = (length / 2) * math.sin(perp_angle)
        x1 = x - dx
        y1 = y - dy
        x2 = x + dx
        y2 = y + dy
        self.canvas.create_line(x1, y1, x2, y2, fill=color, width=3)

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

            # Draw Tee at start if flow_side == SRC, at end if flow_side == DEST
            flow_side = edge.get('flow_side', 0)
            angle = math.atan2(y2 - y1, x2 - x1)
            if flow_side == FLOWSIDE.SRC.value:
                self.draw_tee(x1, y1, angle, edge_color)
            elif flow_side == FLOWSIDE.DEST.value:
                self.draw_tee(x2, y2, angle, edge_color)
            
            # Draw label at midpoint
            mx = (x1 + x2) / 2 - 10  # Offset label slightly to the left of the midpoint
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
                                    fill=node_color,                                    tags=("node_label", f"node_label_{node['id']}"))        # Draw edge drag preview if in progress
        if self.edge_drag_start and self.edge_drag_end and self.current_mode == 'edge':
            # Get start node screen position
            start_x, start_y = self.world_to_screen(self.edge_drag_start['x'], self.edge_drag_start['y'])
            # End position is already in screen coordinates
            end_x, end_y = self.edge_drag_end
            
            # Draw preview line with dashed style
            self.canvas.create_line(
                start_x, start_y, end_x, end_y,
                fill='gray',
                width=2,
                dash=(5, 5),  # Dashed line for preview
                tags=('edge_preview',)
            )
            
            # Draw small arrowhead at end
            angle = math.atan2(end_y - start_y, end_x - start_x)
            headlen = 8
            angle_wing = math.pi / 6
            wing_x = end_x - headlen * math.cos(angle - angle_wing)
            wing_y = end_y - headlen * math.sin(angle - angle_wing)
            base_x = end_x - headlen * 0.5 * math.cos(angle)
            base_y = end_y - headlen * 0.5 * math.sin(angle)
            
            self.canvas.create_polygon(
                end_x, end_y,
                wing_x, wing_y,
                base_x, base_y,
                fill='gray', outline='gray',
                tags=('edge_preview_arrow',)
            )

        # Re-draw selection box if it exists (must be drawn last to appear on top)
        if self.box_select_start and self.box_select_last_pos:
            x1, y1 = self.box_select_start
            x2, y2 = self.box_select_last_pos
            self.canvas.create_rectangle(
                min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2),
                outline=self.BOX_SELECT_COLOR,
                width=1,
                dash=(2, 2),  # Creates a dashed line effect
                tags=('selection_box',)
            )

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
                # Ensure all nodes have 'nodetype' set, default based on type or label
                self.nodes = []
                for node in data['nodes']:
                    if 'nodetype' not in node:
                        # Try to infer nodetype from label for backward compatibility
                        label = node.get('label', '')
                        try:
                            node['nodetype'] = NODETYPE.from_string(label).value
                        except ValueError:
                            # Default to SE for regular nodes, 0 for junctions
                            node['nodetype'] = '0' if node.get('type') == 'junction' else 'SE'
                    self.nodes.append(node)
                
                # Ensure all edges have 'flow_side' set, default to 0 (IDK)
                self.edges = [dict(edge, flow_side=edge.get('flow_side', FLOWSIDE.IDK.value)) for edge in data['edges']]
                self.next_id = data.get('next_id', self.next_id)
                self.draw()
    def get_unique_node_identifier(self, node):
        """Generate a unique identifier for a node based on its type and id."""
        nodetype = node.get('nodetype', 'SE')
        id = node.get('id', 0)
        return f"{nodetype}_{id:02d}"  # Format id with leading zeros for consistency

    def report(self):
        # Save the current graph to graph.json in the workspace
        # data = {
        #     'nodes': self.nodes,
        #     'edges': self.edges,
        #     'next_id': self.next_id
        # }

        ns = [ self.get_unique_node_identifier(node) for node in self.nodes ]  # Create unique identifiers for nodes
        ns = list(set(ns))  # Remove duplicates

        # create edge list
        es = []

        for edge in self.edges:
            num = int(edge.get("label", 0))
            start_node_id = 0
            end_node_id = 0

            start_node_id = edge["startNodeId"] if "startNodeId" in edge else 0
            end_node_id = edge["endNodeId"] if "endNodeId" in edge else 0

            start_node_name = "IDK"
            for node in self.nodes:
                if node.get("id", 0) == start_node_id:
                    start_node_name = self.get_unique_node_identifier(node)

            end_node_name = "IDK"
            for node in self.nodes:
                if node.get("id", 0) == end_node_id:
                    end_node_name = self.get_unique_node_identifier(node)

            es.append(FlyEdge(label_num=num, src=start_node_name, dest=end_node_name, pwr_to_dest=1, flow_side=FLOWSIDE.IDK))

        lb.assign_causality_to_all_nodes(es)
        lb.plot_graph(es, ns, f"graph.png")
        lb.report_equations(es, report_all=True, file_name=f"bond_equations.txt")

        
        for e in es:
            target_edge = next((edge for edge in self.edges if int(edge['label']) == e.num), None)
            # print flow_side
            # if e.flow_side == FLOWSIDE.SRC, set edges[num].flow_side = FLOWSIDE.SRC
            if e.flow_side == FLOWSIDE.SRC and target_edge:
                target_edge['flow_side'] = FLOWSIDE.SRC.value
            elif e.flow_side == FLOWSIDE.DEST and target_edge:
                target_edge['flow_side'] = FLOWSIDE.DEST.value
            
            # print edge data
            print(f"Edge {e.num:2d}: {e.src:5s} -> {e.dest:5s}, Flow Side: {e.flow_side.name}")
        
        self.draw()

        # try:
        #     with open('graph.json', 'w') as f:
        #         json.dump(data, f, indent=2)
        #     self.update_status_temp("Graph saved to graph.json")
        # except Exception as e:
        #     self.update_status_temp(f"Error saving graph: {e}")

    def save_png(self):
        path = filedialog.asksaveasfilename(defaultextension='.png', filetypes=[('PNG','*.png')])
        if path:
            # Generate a postscript file in memory
            ps = self.canvas.postscript(colormode='color')
            img = Image.open(io.BytesIO(ps.encode('utf-8')))
            img.save(path, 'png')

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

    def clear_causality(self):
        for edge in self.edges:
            edge['flow_side'] = FLOWSIDE.IDK.value
        self.draw()
        self.update_status_temp("Causality cleared (all flow sides set to IDK)")

    def update_button_colors(self):
        """Update the tool buttons' colors based on the current mode"""
        # Reset all buttons to inactive
        for btn in self.tool_buttons:
            btn.config(bg=self.INACTIVE_BTN_BG, fg=self.INACTIVE_BTN_FG)
        
        # Button 0 is Select
        if self.current_mode == 'select':
            self.tool_buttons[0].config(bg=self.ACTIVE_BTN_BG, fg=self.ACTIVE_BTN_FG)
        # Buttons 1-9 are for nodetypes (in NODETYPE enum order)
        elif self.current_mode == 'nodetype' and self.current_nodetype:
            nodetype_index = list(NODETYPE).index(self.current_nodetype) + 1
            if 0 < nodetype_index < len(self.tool_buttons):
                self.tool_buttons[nodetype_index].config(bg=self.ACTIVE_BTN_BG, fg=self.ACTIVE_BTN_FG)
        # Last button is Add Edge
        elif self.current_mode == 'edge':
            self.tool_buttons[-1].config(bg=self.ACTIVE_BTN_BG, fg=self.ACTIVE_BTN_FG)

    def handle_delete_key(self, event):
        """Handle Delete or Backspace key press"""
        if self.selected_nodes or self.selected_edges:
            self.delete_selected()
            return 'break'  # Prevent the event from propagating

    def handle_escape_key(self, event):
        """Handle Escape key press - change to select mode"""
        self.set_select()
        return 'break'  # Prevent the event from propagating

    def handle_e_key(self, event):
        """Handle 'e' or 'E' key press - change to 'Add Edge' mode"""
        self.set_edge()
        return 'break'  # Prevent the event from propagating

    def handle_s_key(self, event):
        """Handle 's' or 'S' key press - change to 'Add SE' mode"""
        # Find the SE nodetype in the NODETYPE enum
        se_nodetype = None
        for nodetype in NODETYPE:
            if nodetype.value == 'SE':
                se_nodetype = nodetype
                break
        
        if se_nodetype:
            self.set_nodetype(se_nodetype)
        return 'break'  # Prevent the event from propagating

    def handle_f_key(self, event):
        """Handle 'f' or 'F' key press - change to 'Add SF' mode"""
        # Find the SF nodetype in the NODETYPE enum
        sf_nodetype = None
        for nodetype in NODETYPE:
            if nodetype.value == 'SF':
                sf_nodetype = nodetype
                break
        
        if sf_nodetype:
            self.set_nodetype(sf_nodetype)
        return 'break'  # Prevent the event from propagating

    def handle_i_key(self, event):
        """Handle 'i' or 'I' key press - change to 'Add I' mode"""
        self._handle_nodetype_key('I')
        return 'break'

    def handle_c_key(self, event):
        """Handle 'c' or 'C' key press - change to 'Add C' mode"""
        self._handle_nodetype_key('C')
        return 'break'

    def handle_r_key(self, event):
        """Handle 'r' or 'R' key press - change to 'Add R' mode"""
        self._handle_nodetype_key('R')
        return 'break'

    def handle_g_key(self, event):
        """Handle 'g' or 'G' key press - change to 'Add GY' mode"""
        self._handle_nodetype_key('GY')
        return 'break'

    def handle_t_key(self, event):
        """Handle 't' or 'T' key press - change to 'Add TF' mode"""
        self._handle_nodetype_key('TF')
        return 'break'

    def handle_0_key(self, event):
        """Handle '0' key press - change to 'Add 0' mode"""
        self._handle_nodetype_key('0')
        return 'break'

    def handle_1_key(self, event):
        """Handle '1' key press - change to 'Add 1' mode"""
        self._handle_nodetype_key('1')
        return 'break'

    def _handle_nodetype_key(self, nodetype_value):
        """Helper method to find and set nodetype by value"""
        target_nodetype = None
        for nodetype in NODETYPE:
            if nodetype.value == nodetype_value:
                target_nodetype = nodetype
                break
        
        if target_nodetype:
            self.set_nodetype(target_nodetype)

    def get_next_edge_number(self):
        """Find the next available integer value for edge labels"""
        # Get all edge labels that are integers
        used_numbers = set()
        for edge in self.edges:
            try:
                num = int(edge['label'])
                used_numbers.add(num)
            except ValueError:
                continue
        
        # Find the first unused integer starting from 1
        next_num = 1
        while next_num in used_numbers:
            next_num += 1
        return str(next_num)

    def get_next_node_label(self, nodetype):
        """Generate the next available label for a node of the given type"""
        if nodetype in ['0', '1']:
            # For junctions, just use the nodetype as the label
            return nodetype
        else:
            # For other node types, find the next available number
            used_labels = set()
            for node in self.nodes:
                if node.get('nodetype') == nodetype:
                    label = node['label']
                    # Extract number from end of label if it exists
                    if label == nodetype:
                        used_labels.add(1)
                    elif label.startswith(nodetype):
                        try:
                            num = int(label[len(nodetype):])
                            used_labels.add(num)
                        except ValueError:
                            continue
            
            # Find the first unused number starting from 1
            next_num = 1
            while next_num in used_labels:
                next_num += 1
            
            if next_num == 1:
                return nodetype
            else:
                return f"{nodetype}{next_num}"

    def show_context_menu(self, event):
        """Show context menu for right-clicked element"""
        x, y = self.screen_to_world(event.x, event.y)
        
        # Check if we clicked on a node or edge
        node = self.get_node_at(x, y)
        edge = self.get_edge_at(x, y)
        
        if node or edge:
            # Clear existing menu items
            self.context_menu.delete(0, tk.END)
            
            if node:
                self.context_menu.add_command(
                    label=f"Rename {node['type']}", 
                    command=lambda n=node: self.rename_node(n))
            elif edge:
                self.context_menu.add_command(
                    label="Rename edge",
                    command=lambda e=edge: self.rename_edge(e))
            
            self.context_menu.tk_popup(event.x_root, event.y_root)
    
    def rename_node(self, node):
        """Show dialog to rename a node"""
        new_label = simpledialog.askstring(
            "Rename Node", 
            f"Enter new label for {node['type']}:",
            initialvalue=node['label'])
        if new_label:
            node['label'] = new_label
            self.draw()
            self.update_status_temp(f"{node['type'].capitalize()} renamed to: {new_label}")
    
    def rename_edge(self, edge):
        """Show dialog to rename an edge"""
        new_label = simpledialog.askstring(
            "Rename Edge",
            "Enter new label for edge:",
            initialvalue=edge['label'])
        if new_label:
            edge['label'] = new_label
            self.draw()
            self.update_status_temp(f"Edge renamed to: {new_label}")

    def handle_copy(self, event=None):
        # Copy selected nodes and junctions to clipboard
        self.clipboard_nodes = []
        self.clipboard_edges = []
        selected_node_ids = set(self.selected_nodes)
        for node in self.nodes:
            if node['id'] in selected_node_ids:
                self.clipboard_nodes.append(node.copy())
        # Copy edges where both endpoints are in selected nodes
        for edge in self.edges:
            if edge['startNodeId'] in selected_node_ids and edge['endNodeId'] in selected_node_ids:
                self.clipboard_edges.append(edge.copy())
        self.update_status_temp(f"Copied {len(self.clipboard_nodes)} node(s)/junction(s) and {len(self.clipboard_edges)} edge(s)")
        return 'break'

    def handle_paste(self, event=None):
        if not self.clipboard_nodes:
            self.update_status_temp("Clipboard is empty")
            return 'break'
        OFFSET = 30
        new_nodes = []
        id_map = {}
        for node in self.clipboard_nodes:
            new_node = node.copy()
            new_node['id'] = self.next_id
            new_node['x'] += OFFSET
            new_node['y'] += OFFSET
            id_map[node['id']] = self.next_id
            new_nodes.append(new_node)
            self.next_id += 1
        self.nodes.extend(new_nodes)
        # Find the next available edge label number
        used_numbers = set()
        for edge in self.edges:
            try:
                num = int(edge['label'])
                used_numbers.add(num)
            except Exception:
                continue
        next_edge_num = 1
        while next_edge_num in used_numbers:
            next_edge_num += 1
        # Paste edges, updating node IDs and incrementing label numbers
        new_edges = []
        for edge in self.clipboard_edges:
            new_edge = edge.copy()
            new_edge['id'] = self.next_id
            new_edge['startNodeId'] = id_map.get(edge['startNodeId'], edge['startNodeId'])
            new_edge['endNodeId'] = id_map.get(edge['endNodeId'], edge['endNodeId'])
            # Assign incremented label number
            new_edge['label'] = str(next_edge_num)
            used_numbers.add(next_edge_num)
            next_edge_num += 1
            new_edges.append(new_edge)
            self.next_id += 1
        self.edges.extend(new_edges)
        # Select newly pasted nodes and edges
        self.selected_nodes = set(n['id'] for n in new_nodes)
        self.selected_edges = set(e['id'] for e in new_edges)
        self.draw()
        self.update_status_temp(f"Pasted {len(new_nodes)} node(s)/junction(s) and {len(new_edges)} edge(s)")
        return 'break'

if __name__ == '__main__':
    root = tk.Tk()
    app = GraphEditorApp(root)
    root.mainloop()
