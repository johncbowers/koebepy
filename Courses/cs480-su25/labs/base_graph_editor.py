from koebe.geometries.euclidean2 import *

from math import *
from random import *
from collections import deque

from koebe.graphics.flask.multiviewserver import viewer, set_key_pressed_handler, set_key_released_handler
from koebe.graphics.scenes.euclidean2scene import E2Scene, makeStyle

blackStyle = makeStyle(stroke=(0,0,0), fill=(255, 255, 255))
redStyle = makeStyle(stroke=(255,0,0), fill=(255, 0, 0), strokeWeight=2.0)

vertices = [PointE2(0, 0), PointE2(100, 0), PointE2(100, 100)]
edges = [[0,1]]

def redraw():
    global graph_editor_scene, vertices, edges
    graph_editor_scene.clear()
    
    # Draw edges
    for e in edges:
        graph_editor_scene.add(SegmentE2(vertices[e[0]], vertices[e[1]]), makeStyle(stroke=(0, 0, 255)))

    if mouse_position is not None and selected_vertex_idx != -1:
        # Draw a temporary edge from the selected vertex to the mouse position
        graph_editor_scene.add(SegmentE2(vertices[selected_vertex_idx], mouse_position if selected_end_vertex_idx == -1 else vertices[selected_end_vertex_idx]), redStyle)

    # Draw vertices
    graph_editor_scene.addAll([(vertices[i], blackStyle if i != selected_vertex_idx and i != selected_end_vertex_idx else redStyle) for i in range(len(vertices))])

mode = "vertex"  # or "edge"
selected_vertex_idx = -1
selected_end_vertex_idx = -1
#pin_edge_idx = 0
option_key_down = False 
mouse_position = None

def nearest_vertex_idx_of(x, y, thresh=10):
    global vertices
    nearest_vertex = -1
    min_distance = float('inf')
    for i, v in enumerate(vertices):
        distance = v.distSqTo(PointE2(x, y))
        if distance < min_distance and distance < thresh*thresh:
            min_distance = distance
            nearest_vertex = i
    return nearest_vertex

def mouse_pressed(event):
    global graph_editor_scene, vertices, edges, mode, option_key_down, selected_vertex_idx, nearest_vertex, selected_vertex_idx, mouse_position

    if mode == "vertex":
        # if the option key is down, add a vertex at the mouse position
        if option_key_down:
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

def key_pressed(key):
    print(f"Key pressed: {key}")
    if key == "Option" or key == "Alt":
        global option_key_down
        option_key_down = True

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
    

graph_editor_scene = E2Scene(title="Graph Editor")

graph_editor_scene.set_mouse_pressed(mouse_pressed)
#graph_editor_scene.set_mouse_moved(mouse_moved)
graph_editor_scene.set_mouse_dragged(mouse_dragged)
graph_editor_scene.set_mouse_released(mouse_released)

set_key_pressed_handler(key_pressed)
set_key_released_handler(key_released)

viewer.add_scene(graph_editor_scene)

redraw()
viewer.run()