from koebe.geometries.euclidean2 import *

from math import *
from random import *
from collections import deque

from koebe.graphics.flask.multiviewserver import viewer, set_key_pressed_handler, set_key_released_handler
from koebe.graphics.scenes.euclidean2scene import E2Scene, makeStyle

from koebe.algorithms.convexHullE2 import *

blackStyle = makeStyle(stroke=(0,0,0), fill=(255, 255, 255), strokeWeight=4.0)
redStyle = makeStyle(stroke=(255,0,0), fill=(255, 0, 0), strokeWeight=2.0)
grayStyle = makeStyle(stroke=(235,235,235), fill=(235,235,235), strokeWeight=1.0)
blueStyle = makeStyle(stroke=(0, 0, 255), fill=(0, 0, 255), strokeWeight=1.0)

vertices = [PointE2(0, 0), PointE2(100, 0), PointE2(100, 100), PointE2(0, 100)]
old_chain = None

# TODO
#
# 3. When the user clicks the 'f' key, flip the vertices across the chain of the 
#    polygon edge returned by find_chull_edge. Show the old flip edge in red, 
#    the old chain in blue, and the new chain in black.

def find_chull_edge():
    global vertices

    cs = convex_hull(vertices).ccwOrientation().vertices
    vs = PolygonE2(vertices).ccwOrientation().vertices
    
    cEdges = set([(cs[i], cs[(i+1)%len(cs)]) for i in range(len(cs))])
    vEdges = set([(vs[i], vs[(i+1)%len(vs)]) for i in range(len(vs))])

    valid_edges = cEdges - vEdges
    
    if valid_edges:
        edge = valid_edges.pop()
        return edge
    else:
        return None, None


flip_edge = (None, None)

def redraw():
    global graph_editor_scene, vertices, edges, flip_edge
    graph_editor_scene.clear()
    
    chull = convex_hull(vertices)
    
    graph_editor_scene.add(chull, grayStyle)

    # Draw polygon
    graph_editor_scene.addAll([(SegmentE2(vertices[i], vertices[(i + 1) % len(vertices)]), blackStyle) for i in range(len(vertices))])

    if flip_edge[0] is not None:
        graph_editor_scene.add(SegmentE2(*flip_edge), redStyle)

    # If there is an old_chain draw it: 
    if old_chain:
        graph_editor_scene.addAll([(SegmentE2(old_chain[i], old_chain[i+1]), blueStyle) 
                                   for i in range(len(old_chain) - 1)])

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
    global graph_editor_scene, vertices, selected_vertex_idx, mouse_position, mode, selected_end_vertex_idx, flip_edge

    if selected_vertex_idx != -1 and mode == "vertex":
        # Move the selected vertex to the mouse position
        print("moving vertex")
        vertices[selected_vertex_idx] = PointE2(event["x"], event["y"])
        flip_edge = (None, None)
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
    global option_key_down, mode, selected_vertex_idx, flip_edge, vertices, old_chain
    if key == "Option" or key == "Alt":
        option_key_down = False
    elif key == "v":
        mode = "vertex"
        print("Switched to vertex mode")
    elif key == "f":
        flip_edge = find_chull_edge()
        if flip_edge[0] is not None:
            pi = vertices.index(flip_edge[0])
            pj = vertices.index(flip_edge[1])
            
            flip_segment = SegmentE2(*flip_edge)
            old_chain = vertices[min(pi, pj):max(pi,pj)+1]
            for i in range(min(pi, pj)+1, max(pi, pj)):
                vertices[i] = flip_segment.reflect(vertices[i])
        
        redraw()

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