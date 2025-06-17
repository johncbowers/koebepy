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

vertices = [PointE2(0, 0), PointE2(100, 0), PointE2(100, 100), PointE2(0, 100)]
edges = [[0,1], [1, 2], [2, 3], [3, 0]]
pin_edge_idx = 0

# TODO
#
# The starting point for this homework is lab 03. The goal of this homework is 
# to visualize the motion of a 1 degree of freedom framework. 
#
# A basic algorithm for doing this is Euler's method, which is a numerical algorithm
# for integrating an ordinary differential equation. 
#
# The idea is to do the following. Given your framework (G, p), first compute the pinned rigidity
# matrix R of (G, p). Find the null space of R. In principle we could do this as long as the 
# null space had any positive dimension, but for this homework we will only produce a motion
# if the null space is 1-dimensional. 
#
# In the case that null space is one dimensional, extract the null space vector (which we 
# visualized in lab 03), and push each vertex of the framework by a small step along 
# this vector. Then recompute the rigidity matrix, and repeat the process. 
#
# That's the basic idea. I've added a second scene, motion_scene to add your animation to. 
# You should clear motion_scene in the redraw function, then if the null space is one dimensional
# use the method described above to compute a motion. Each time you take a small step along 
# the motion, add a drawing of it to motion_scene and then pushAnimFrame to start a new 
# frame of the animation. 
#
# Hints: 
#
# 1. You will need to make the rigidity matrix computation stop using global vertices, but instead
#    use a parameter. 
# 2. You may want to create a graph drawing function that takes a scene and draws a graph to it. 
#

def rigidity_matrix_row(i, j):
    global vertices
    row = [(0, 0) for _ in vertices]
    row[i] = tuple(vertices[j]-vertices[i])
    row[j] = tuple(vertices[i]-vertices[j])
    return row

def pinning_rows(i):
    global vertices
    row1 = [(0, 0) for _ in vertices]
    row2 = [(0, 0) for _ in vertices]
    row1[i] = (1, 0)
    row2[i] = (0, 1)
    return [row1, row2]

def rigidity_matrix():
    global edges, pin_edge_idx
    edge_rows = [rigidity_matrix_row(i, j) for i, j in edges]
    i, j = edges[pin_edge_idx]
    R = edge_rows + pinning_rows(i)+pinning_rows(j)
    return np.array(
        [np.array(row).flatten() for row in R]
    )

def print_dof(R):
    ns = null_space(R)
    print(f"This mechanism has {ns.shape[1]} degrees of freedom.")

# 
# Drawing Code
#

prev_v = None

def redraw():
    global graph_editor_scene, vertices, edges, prev_v
    graph_editor_scene.clear()
    
    print(vertices)
    print(edges)

    R = rigidity_matrix()
    print_dof(R)
    ns = null_space(R)

    if ns.shape[1] > 0:
        v = (ns.T)[0]
        
        if prev_v is not None and prev_v.dot(v) < 0:
            v = -v
        prev_v = v
        
        vs = [VectorE2(float(v[i]), float(v[i+1])) for i in range(0, v.shape[0], 2)]
        graph_editor_scene.addAll([
            (SegmentE2(vertices[i], vertices[i] + 100 * vs[i]), redStyle)
            for i in range(len(vs))
        ])

    # Draw edges
    graph_editor_scene.addAll([(SegmentE2(vertices[e[0]], vertices[e[1]]), purpleStyle if i == pin_edge_idx else blackStyle) for i, e in enumerate(edges)])
    
    if mouse_position is not None and selected_vertex_idx != -1:
        # Draw a temporary edge from the selected vertex to the mouse position
        graph_editor_scene.add(SegmentE2(vertices[selected_vertex_idx], mouse_position if selected_end_vertex_idx == -1 else vertices[selected_end_vertex_idx]), redStyle)

    # Draw vertices
    graph_editor_scene.addAll([(vertices[i], blackStyle if i != selected_vertex_idx and i != selected_end_vertex_idx else redStyle) for i in range(len(vertices))])

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
    global graph_editor_scene, vertices, selected_vertex_idx, mouse_position, mode, selected_end_vertex_idx

    if selected_vertex_idx != -1 and mode == "vertex":
        # Move the selected vertex to the mouse position
        print("moving vertex")
        vertices[selected_vertex_idx] = PointE2(event["x"], event["y"])
        redraw()
    if mode == "edge" and selected_vertex_idx != -1:
        # If in edge mode, update the mouse position to draw a temporary edge
        mouse_position = PointE2(event["x"], event["y"])
        selected_end_vertex_idx = nearest_vertex_idx_of(mouse_position.x, mouse_position.y) 
        redraw()

def mouse_released(event):
    global selected_vertex_idx, mouse_position, selected_end_vertex_idx
    
    if mode == "edge":
        if selected_vertex_idx != -1 and selected_end_vertex_idx != -1 and selected_vertex_idx != selected_end_vertex_idx:
            # Add an edge between the selected vertex and the end vertex
            if [selected_vertex_idx, selected_end_vertex_idx] not in edges and [selected_end_vertex_idx, selected_vertex_idx] not in edges:
                edges.append([selected_vertex_idx, selected_end_vertex_idx])
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
    global option_key_down, mode, selected_vertex_idx
    if key == "Option" or key == "Alt":
        option_key_down = False
    elif key == "v":
        mode = "vertex"
        print("Switched to vertex mode")
    elif key == "e":
        mode = "edge"
        print("Switched to edge mode")
    

# 
# Set up the scenes and bind the mouse and key handlers 
#

graph_editor_scene = E2Scene(title="Graph Editor")
motion_scene = E2Scene(title="Motion Viewer")

graph_editor_scene.set_mouse_pressed(mouse_pressed)
#graph_editor_scene.set_mouse_moved(mouse_moved)
graph_editor_scene.set_mouse_dragged(mouse_dragged)
graph_editor_scene.set_mouse_released(mouse_released)

set_key_pressed_handler(key_pressed)
set_key_released_handler(key_released)

viewer.add_scene(graph_editor_scene)
viewer.add_scene(motion_scene)

redraw()
viewer.run()