from koebe.geometries.euclidean2 import *

from math import *
from random import *
from collections import deque

from koebe.graphics.flask.multiviewserver import viewer, set_key_pressed_handler, set_key_released_handler
from koebe.graphics.scenes.euclidean2scene import E2Scene, makeStyle
from koebe.algorithms.convexHullE2 import convex_hull
from koebe.geometries.euclidean2 import *

blackStyle = makeStyle(stroke=(0,0,0), fill=(255, 255, 255), strokeWeight=4.0)
redStyle = makeStyle(stroke=(255,0,0), fill=(255, 0, 0), strokeWeight=2.0)
lightGrayStyle = makeStyle(stroke=(211,211,211), fill=(211, 211, 211), strokeWeight=2.0)
blueStyle = makeStyle(stroke=(100,100,100), fill=(100,100,100), strokeWeight=2.0)

vertices = [PointE2(0, 0), PointE2(100, 0), PointE2(100, 100), PointE2(0, 100)]

# TODO
#
# 2. Add a function that finds an edge of the convex hull that is not
#    part of the polygon, and returns the indices of the two vertices
#    of that edge. Call this function `find_chull_edge()`. 
#ignore the following comment
#    It will be helpful here to have the same orientation of two polygons, which you can get with ccwOrientation()

def find_chull_edge(ch):
    global vertices #?

    #create set of edges
    poly_edges = set([(vertices[i], vertices[(i + 1)%len(vertices)]) for i in range(len(vertices))])
    #do with convex hull also
    ch_edges = set([(ch.vertices[i], ch.vertices[(i + 1)%len(ch.vertices)]) for i in range(len(ch.vertices))])
    #subtract the sets to get the flip edge
    flip_verts = poly_edges - ch_edges
    #get index of the two vertices in polygon.vertices

    for v1, v2 in flip_verts:
        idx1 = vertices.index(v1)
        idx2 = vertices.index(v2)
        flip_edge = [idx1, idx2]

    return flip_edge
            
#convex_hull()
#reflect

flip_edge = (None, None)
old_chain = (None, None)

def redraw():
    global graph_editor_scene, vertices, edges, flip_edge, old_chain
    graph_editor_scene.clear()

    # 1. Compute the convex hull of the polygon defined by `vertices` in the draw
    #    function and draw it in a light gray. (See koebe.algorithms.convexHullE2)

    # convex_hull(points)
    ch = convex_hull(vertices)
    # draw convex hull in light gray
    graph_editor_scene.add(ch, lightGrayStyle)

    #get a edge that is only in the convex hull
    flip_edge = find_chull_edge(ch)
    
    # Draw polygon
    graph_editor_scene.addAll([(SegmentE2(vertices[i], vertices[(i + 1) % len(vertices)]), blackStyle) for i in range(len(vertices))])

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
    global option_key_down, mode, selected_vertex_idx
    if key == "Option" or key == "Alt":
        option_key_down = False
    elif key == "v":
        mode = "vertex"
        print("Switched to vertex mode")
    # 3. When the user clicks the 'f' key, flip the vertices across the chain of the 
#    polygon edge returned by find_chull_edge. Show the old flip edge in red, 
    elif key == "f":
        
        #get the vertices be between the two flip vertices from step two
        #those are the ones you need to flip
        ch = convex_hull(vertices)
        flip_edges = find_chull_edge(ch)

        flip_segment = SegmentE2(vertices[flip_edges[0]], vertices[flip_edges[1]])

        minv = min(flip_edges[0], flip_edges[1])+1
        maxv = max(flip_edges[0], flip_edges[1])
        to_flip = list(range(minv, maxv))

        for i in to_flip:
            vertices[i] = flip_segment.reflect(vertices[i])

        graph_editor_scene.add(flip_segment, redStyle)

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