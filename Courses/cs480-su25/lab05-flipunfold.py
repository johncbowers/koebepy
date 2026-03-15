from koebe.geometries.euclidean2 import *

from math import *
from random import *
from collections import deque

from koebe.graphics.flask.multiviewserver import viewer, set_key_pressed_handler, set_key_released_handler
from koebe.graphics.scenes.euclidean2scene import E2Scene, makeStyle

from koebe.algorithms.convexHullE2 import *

blackStyle = makeStyle(stroke=(0,0,0), fill=(255, 255, 255), strokeWeight=4.0)
redStyle = makeStyle(stroke=(255,0,0), fill=(255, 0, 0), strokeWeight=2.5)
lightgraystyle =  makeStyle(stroke=(200,200,200), fill=(240, 240, 240), strokeWeight=0.5)
blueStyle = makeStyle(stroke=(0,0,255), fill=(0, 0, 255), strokeWeight=2.5)

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

old_chain = None
flipped_edge = None

def find_chull_edge():
    global flipped_edge, vertices

    # edges = set([(vertices[i], vertices[(i+1)%len(vertices)]) for i in range(len(vertices))])
    # print (f"edges : {edges}")
    chull = convex_hull(vertices).ccwOrientation()

    currV = PolygonE2(vertices).ccwOrientation().vertices

    edges = set([(currV[i], currV[(i+1)%len(currV)]) for i in range(len(currV))])

    for j in range(chull.vertexCount):
        p = chull.vertices[j]
        q = chull.vertices[(j+1)%len(chull.vertices)]
        # print(f"{p},{q}")
        # return the edge that is not a part of the polygon
        if (p,q) not in edges:
            flipped_edge = p, q
            return

    flipped_edge = None


def redraw():
    global graph_editor_scene, vertices, edges, flipped_edge, old_chain
    graph_editor_scene.clear()

    # Draw convex hull
    chull = convex_hull(vertices)
    graph_editor_scene.add(chull, lightgraystyle)

    # Draw polygon
    graph_editor_scene.addAll([(SegmentE2(vertices[i], vertices[(i + 1) % len(vertices)]), blackStyle) for i in range(len(vertices))])

    if flipped_edge:
        p, q = flipped_edge
        graph_editor_scene.add(SegmentE2(p,q), redStyle)

    if old_chain:
        graph_editor_scene.addAll([(SegmentE2(old_chain[i], old_chain[i+1]), blueStyle) for i in range(len(old_chain) - 1)])

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

def mouse_dragged(event):
    global graph_editor_scene, vertices, selected_vertex_idx, mouse_position, mode, selected_end_vertex_idx

    if selected_vertex_idx != -1 and mode == "vertex":
        # Move the selected vertex to the mouse position
        print("moving vertex")
        vertices[selected_vertex_idx] = PointE2(event["x"], event["y"])
        redraw()

def mouse_released(event):
    global selected_vertex_idx, mouse_position, selected_end_vertex_idx

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
    global option_key_down, mode, selected_vertex_idx, old_chain, flipped_edge, vertices
    if key == "Option" or key == "Alt":
        option_key_down = False
    elif key == "v":
        mode = "vertex"
        print("Switched to vertex mode")
    elif key == "f":
        flipped_edge = None
        find_chull_edge()
        if flipped_edge:
            p1, p2 = flipped_edge
            # store the two verticies to use
            idx1 = vertices.index(p1)
            idx2 = vertices.index(p2)

            # store the old chain
            old_chain = vertices[min(idx1, idx2):max(idx1, idx2)+1]

            line = SegmentE2(p1, p2)
            for i in range(min(idx1, idx2) + 1, max(idx1, idx2)):
                vertices[i] = line.reflect(vertices[i])

            redraw()
        else:
            print("cant flip anymore")

graph_editor_scene = E2Scene(title="Polygon Editor")

graph_editor_scene.set_mouse_pressed(mouse_pressed)
#graph_editor_scene.set_mouse_moved(mouse_moved)
graph_editor_scene.set_mouse_dragged(mouse_dragged)
graph_editor_scene.set_mouse_released(mouse_released)

set_key_pressed_handler(key_pressed)
set_key_released_handler(key_released)

viewer.add_scene(graph_editor_scene)

redraw()
viewer.run()
