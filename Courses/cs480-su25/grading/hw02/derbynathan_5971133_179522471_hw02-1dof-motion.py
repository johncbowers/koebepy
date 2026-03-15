from koebe.geometries.euclidean2 import *

from math import *
from random import *
from collections import deque

from koebe.graphics.flask.multiviewserver import viewer, set_key_pressed_handler, set_key_released_handler
from koebe.graphics.scenes.euclidean2scene import E2Scene, makeStyle

import numpy as np
from scipy.linalg import null_space

blackStyle = makeStyle(stroke=(0,0,0), fill=(255, 255, 255))
redStyle = makeStyle(stroke=(255,0,0), fill=(255, 0, 0), strokeWeight=2.0)
purpleStyle = makeStyle(stroke=(128,0,128), fill=(128, 0, 128), strokeWeight=4.0)
greenStyle = makeStyle(stroke=(0,128,0), fill=(0, 128, 0), strokeWeight=2.0)
lightBlueStyle = makeStyle(stroke=(173,216,230), fill=(173, 216, 230), strokeWeight=1.0)

vertices = [PointE2(0, 0), PointE2(100, 0), PointE2(100, 100), PointE2(0, 100)]
edges = [[0,1], [1, 2], [2, 3], [3, 0]]
pin_edge_idx = 0

# Animation parameters
step_size = 1  # How far to move along the null space vector each step
animation_frames = 1000  # Number of frames to generate
is_animating = False

def rigidity_matrix_row(i, j, verts):
    row = [(0, 0) for _ in verts]
    row[i] = tuple(verts[j]-verts[i])
    row[j] = tuple(verts[i]-verts[j])
    return row

def pinning_rows(i, verts):
    row1 = [(0, 0) for _ in verts]
    row2 = [(0, 0) for _ in verts]
    row1[i] = (1, 0)
    row2[i] = (0, 1)
    return [row1, row2]

def rigidity_matrix(verts, edges_list, pin_idx):
    edge_rows = [rigidity_matrix_row(i, j, verts) for i, j in edges_list]
    i, j = edges_list[pin_idx]
    R = edge_rows + pinning_rows(i, verts) + pinning_rows(j, verts)
    return np.array(
        [np.array(row).flatten() for row in R]
    )

def print_dof(R):
    ns = null_space(R)
    print(f"This mechanism has {ns.shape[1]} degrees of freedom.")
    return ns.shape[1]

def draw_graph(scene, verts, edges_list, pin_idx, style=blackStyle, pin_style=purpleStyle):
    """Helper function to draw a graph to any scene"""
    # Draw edges
    scene.addAll([
        (SegmentE2(verts[e[0]], verts[e[1]]), pin_style if i == pin_idx else style) 
        for i, e in enumerate(edges_list)
    ])
    
    # Draw vertices
    scene.addAll([
        (verts[i], style) 
        for i in range(len(verts))
    ])

def animate_motion():
    """Generate animation frames using Euler's method"""
    global motion_scene, vertices, edges, pin_edge_idx, step_size, animation_frames
    
    # Clear both the visual content AND the animation frames
    motion_scene.clear()
    motion_scene.clearAnimFrames()  # This clears old animation frames
    
    # Start with current vertices
    current_verts = [PointE2(v.x, v.y) for v in vertices]  # Make a copy
    prev_v = None
    
    # Generate animation frames
    for frame in range(animation_frames):
        # Compute rigidity matrix for current configuration
        R = rigidity_matrix(current_verts, edges, pin_edge_idx)
        ns = null_space(R)
        
        # Only animate if we have exactly 1 DOF
        if ns.shape[1] != 1:
            print(f"Cannot animate: mechanism has {ns.shape[1]} degrees of freedom (need exactly 1)")
            return
        
        # Get the null space vector
        v = (ns.T)[0]
        
        # avoid flipping
        if prev_v is not None and prev_v.dot(v) < 0:
            v = -v
        prev_v = v.copy()
        
        # Draw current configuration
        # Use different colors/transparency for different frames
        
        
        draw_graph(motion_scene, current_verts, edges, pin_edge_idx, blackStyle, blackStyle)
        
        # Push animation frame
        motion_scene.pushAnimFrame()
        
        # Update vertices along the null space vector
        vs = [VectorE2(float(v[i]), float(v[i+1])) for i in range(0, v.shape[0], 2)]
        
        for i in range(len(current_verts)):
            current_verts[i] = current_verts[i] + step_size * vs[i]
    
    print(f"Generated {animation_frames} animation frames")

prev_v = None

def redraw():
    global graph_editor_scene, vertices, edges, prev_v
    graph_editor_scene.clear()
    
    print(f"Vertices: {[(v.x, v.y) for v in vertices]}")
    print(f"Edges: {edges}")

    R = rigidity_matrix(vertices, edges, pin_edge_idx)
    dof = print_dof(R)
    ns = null_space(R)

    if ns.shape[1] > 0:
        v = (ns.T)[0]
        
        if prev_v is not None and prev_v.dot(v) < 0:
            v = -v
        prev_v = v.copy()
        
        vs = [VectorE2(float(v[i]), float(v[i+1])) for i in range(0, v.shape[0], 2)]
        graph_editor_scene.addAll([
            (SegmentE2(vertices[i], vertices[i] + 100 * vs[i]), redStyle)
            for i in range(len(vs))
        ])

    # Draw the main graph
    draw_graph(graph_editor_scene, vertices, edges, pin_edge_idx)
    
    if mouse_position is not None and selected_vertex_idx != -1:
        # Draw a temporary edge from the selected vertex to the mouse position
        graph_editor_scene.add(SegmentE2(vertices[selected_vertex_idx], mouse_position if selected_end_vertex_idx == -1 else vertices[selected_end_vertex_idx]), redStyle)

    # Highlight selected vertices
    if selected_vertex_idx != -1:
        graph_editor_scene.add(vertices[selected_vertex_idx], redStyle)
    if selected_end_vertex_idx != -1:
        graph_editor_scene.add(vertices[selected_end_vertex_idx], redStyle)

#
# UI Handling
#

mode = "vertex"  # or "edge"
selected_vertex_idx = -1
selected_end_vertex_idx = -1

option_key_down = False 
mouse_position = None

def nearest_vertex_idx_of(x, y, thresh=10):
    """Find the index of the nearest vertex to the given (x, y) position within a threshold distance.
    If no vertex is within the threshold, return -1.
    Args:
        x (float): The x-coordinate of the mouse position.
        y (float): The y-coordinate of the mouse position.
        thresh (float): The threshold distance to consider for finding the nearest vertex.
    Returns:
        int: The index of the nearest vertex, or -1 if no vertex is within the threshold.
    """
    global vertices
    nearest_vertex = -1
    min_distance = float('inf')
    for i, v in enumerate(vertices):
        distance = v.distSqTo(PointE2(x, y))
        if distance < min_distance and distance < thresh*thresh:
            min_distance = distance
            nearest_vertex = i
    return nearest_vertex

# 
# Mouse Handling
#

def mouse_pressed(event):
    global graph_editor_scene, vertices, edges, mode, option_key_down, selected_vertex_idx, nearest_vertex, selected_vertex_idx, mouse_position, prev_v

    if mode == "vertex":
        # if the option key is down, add a vertex at the mouse position
        if option_key_down:
            prev_v = None
            vertices.append(PointE2(event["x"], event["y"]))
            selected_vertex_idx = len(vertices) - 1  # Select the newly added vertex
            redraw()
        else:
            print("selecting vertex")
            selected_vertex_idx = nearest_vertex_idx_of(event["x"], event["y"])
            redraw()
    elif mode == "edge":
        # select the index of the nearest vertex
        selected_vertex_idx = nearest_vertex_idx_of(event["x"], event["y"])
        mouse_position = PointE2(event["x"], event["y"])
        redraw()

def mouse_dragged(event):
    global graph_editor_scene, vertices, selected_vertex_idx, mouse_position, mode, selected_end_vertex_idx, prev_v

    if selected_vertex_idx != -1 and mode == "vertex":
        # Move the selected vertex to the mouse position
        print("moving vertex")
        vertices[selected_vertex_idx] = PointE2(event["x"], event["y"])
        prev_v = None  # Reset null space direction when geometry changes
        redraw()
    if mode == "edge" and selected_vertex_idx != -1:
        # If in edge mode, update the mouse position to draw a temporary edge
        mouse_position = PointE2(event["x"], event["y"])
        selected_end_vertex_idx = nearest_vertex_idx_of(mouse_position.x, mouse_position.y) 
        redraw()

def mouse_released(event):
    global selected_vertex_idx, mouse_position, selected_end_vertex_idx, prev_v
    
    if mode == "edge":
        if selected_vertex_idx != -1 and selected_end_vertex_idx != -1 and selected_vertex_idx != selected_end_vertex_idx:
            # Add an edge between the selected vertex and the end vertex
            if [selected_vertex_idx, selected_end_vertex_idx] not in edges and [selected_end_vertex_idx, selected_vertex_idx] not in edges:
                edges.append([selected_vertex_idx, selected_end_vertex_idx])
                prev_v = None  # Reset null space direction when topology changes
                print(f"Added edge: {selected_vertex_idx} -> {selected_end_vertex_idx}")
        
    selected_vertex_idx = -1
    selected_end_vertex_idx = -1
    mouse_position = None
    redraw()

#
# Key Handling
#

def key_pressed(key):
    global option_key_down, mode, selected_vertex_idx, pin_edge_idx, edges
    print(f"Key pressed: {key}")
    if key == "Option" or key == "Alt":
        option_key_down = True
    elif key == "[":
        pin_edge_idx = (pin_edge_idx + 1) % len(edges)
        redraw()
    elif key == "]":
        pin_edge_idx = (pin_edge_idx - 1) % len(edges)
        redraw()

def key_released(key):
    global option_key_down, mode, selected_vertex_idx, step_size, animation_frames
    if key == "Option" or key == "Alt":
        option_key_down = False
    elif key == "v":
        mode = "vertex"
        print("Switched to vertex mode")
    elif key == "e":
        mode = "edge"
        print("Switched to edge mode")
    elif key == "a":
        print("Starting animation...")
        motion_scene.clearAnimFrames()
        animate_motion() 
    elif key == "r":
        # Reset animation - clear both visual content and animation frames
        motion_scene.clear()
        motion_scene.clearAnimFrames()  # This stops the old animation
        print("Animation cleared")

# 
# Set up the scenes and bind the mouse and key handlers 
#

graph_editor_scene = E2Scene(title="Graph Editor")
motion_scene = E2Scene(title="Motion Viewer")

graph_editor_scene.set_mouse_pressed(mouse_pressed)
graph_editor_scene.set_mouse_dragged(mouse_dragged)
graph_editor_scene.set_mouse_released(mouse_released)

set_key_pressed_handler(key_pressed)
set_key_released_handler(key_released)

viewer.add_scene(graph_editor_scene)
viewer.add_scene(motion_scene)

redraw()
viewer.run()