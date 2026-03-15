from koebe.geometries.euclidean2 import *
from math import *
from random import *
from collections import deque

from koebe.graphics.flask.multiviewserver import viewer, set_key_pressed_handler, set_key_released_handler
from koebe.graphics.scenes.euclidean2scene import E2Scene, makeStyle
from koebe.algorithms.convexHullE2 import *

# Styles for drawing
blackStyle = makeStyle(stroke=(0,0,0), fill=(255, 255, 255), strokeWeight=4.0)
redStyle = makeStyle(stroke=(255,0,0), fill=(255, 0, 0), strokeWeight=2.0)
grayStyle = makeStyle(stroke=(200, 200, 200), fill=(255, 255, 255), strokeWeight=1.0)
blueStyle = makeStyle(stroke=(0,0,255), fill=(255, 255, 255), strokeWeight=2.0)

# Initial polygon vertices
vertices = [PointE2(0, 0), PointE2(100, 0), PointE2(100, 100), PointE2(0, 100)]

# TODO
#
# 1. Compute the convex hull of the polygon defined by `vertices` in the draw
#    function and draw it in a light gray. (See koebe.algorithms.convexHullE2)
# 2. Add a function that finds an edge of the convex hull that is not
#    part of the polygon, and returns the indices of the two vertices
#    of that edge. Call this function `find_chull_edge()`. It will be helpful here
#    to have the same orientation of two polygons, which you can get with ccwOrientation()
# 3. When the user clicks the 'f' key, flip the vertices across the chain of the 
#    polygon edge returned by find_chull_edge. Show the old flip edge in red, 
#    the old chain in blue, and the new chain in black.


def find_chull_edge(vertices):
    hull = convex_hull(vertices)
    hv = hull.vertices
    polygon_edges = {(vertices[i], vertices[(i+1) % len(vertices)]) for i in range(len(vertices))}
    polygon_edges |= {(b, a) for (a, b) in polygon_edges} 

    for i in range(len(hv)):
        e = (hv[i], hv[(i+1) % len(hv)])
        if e not in polygon_edges:
            return e
    return None

def flip_polygon(vertices, edge):
    p1, p2 = edge
    # Line equation
    dx = p2.x - p1.x
    dy = p2.y - p1.y
    length_sq = dx*dx + dy*dy

    new_vertices = []
    for v in vertices:
        # Vector from p1 to v
        vx = v.x - p1.x
        vy = v.y - p1.y
        # Projection factor
        dot = (vx*dx + vy*dy) / length_sq
        projx = p1.x + dot * dx
        projy = p1.y + dot * dy
        # Reflection
        rx = 2*projx - v.x
        ry = 2*projy - v.y
        new_vertices.append(PointE2(rx, ry))
    return new_vertices

def redraw():
    global graph_editor_scene, vertices, selected_vertex_idx, selected_end_vertex_idx, last_flip_edge
    graph_editor_scene.clear()

    # Draw polygon edges
    graph_editor_scene.addAll([
        (SegmentE2(vertices[i], vertices[(i + 1) % len(vertices)]), blackStyle) 
        for i in range(len(vertices))
    ])

    # Draw convex hull in gray
    hull = convex_hull(vertices)
    hv = hull.vertices
    for i in range(len(hv)):
        graph_editor_scene.add((SegmentE2(hv[i], hv[(i + 1) % len(hv)]), grayStyle))

    # Draw vertices
    graph_editor_scene.addAll([
        (vertices[i], blackStyle if i != selected_vertex_idx and i != selected_end_vertex_idx else redStyle)
        for i in range(len(vertices))
    ])

    # If last flip edge exists, show it in red
    if last_flip_edge:
        graph_editor_scene.add((SegmentE2(last_flip_edge[0], last_flip_edge[1]), redStyle))


mode = "vertex"
selected_vertex_idx = -1
selected_end_vertex_idx = -1
option_key_down = False 
mouse_position = None
last_flip_edge = None

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
    global vertices, selected_vertex_idx
    if mode == "vertex":
        if option_key_down:
            vertices.append(PointE2(event["x"], event["y"]))
            selected_vertex_idx = len(vertices) - 1
        else:
            selected_vertex_idx = nearest_vertex_idx_of(event["x"], event["y"])
    redraw()

def mouse_dragged(event):
    global vertices, selected_vertex_idx
    if selected_vertex_idx != -1 and mode == "vertex":
        vertices[selected_vertex_idx] = PointE2(event["x"], event["y"])
        redraw()

def mouse_released(event):
    global selected_vertex_idx, selected_end_vertex_idx, mouse_position
    selected_vertex_idx = -1
    selected_end_vertex_idx = -1
    mouse_position = None
    redraw()

def key_pressed(key):
    global option_key_down, vertices, last_flip_edge
    print(f"Key pressed: {key}")
    if key in ("Option", "Alt"):
        option_key_down = True
    elif key == "f":
        edge = find_chull_edge(vertices)
        if edge:
            last_flip_edge = edge
            flipped = flip_polygon(vertices, edge)
            vertices[:] = flipped
        redraw()

def key_released(key):
    global option_key_down, mode
    if key in ("Option", "Alt"):
        option_key_down = False
    elif key == "v":
        mode = "vertex"
        print("Switched to vertex mode")

graph_editor_scene = E2Scene(title="Polygon Editor")
graph_editor_scene.set_mouse_pressed(mouse_pressed)
graph_editor_scene.set_mouse_dragged(mouse_dragged)
graph_editor_scene.set_mouse_released(mouse_released)

set_key_pressed_handler(key_pressed)
set_key_released_handler(key_released)

viewer.add_scene(graph_editor_scene)
redraw()
viewer.run()