from koebe.geometries.euclidean2 import *
from koebe.algorithms.convexHullE2 import convex_hull

from math import *
from random import *
from collections import deque

from koebe.graphics.flask.multiviewserver import viewer, set_key_pressed_handler, set_key_released_handler
from koebe.graphics.scenes.euclidean2scene import E2Scene, makeStyle

blackStyle = makeStyle(stroke=(0,0,0), fill=(255, 255, 255), strokeWeight=4.0)
redStyle = makeStyle(stroke=(255,0,0), fill=(255, 0, 0), strokeWeight=2.0)
blueStyle = makeStyle(stroke=(0,0,255), fill=(255, 0, 0), strokeWeight=1.5)

greyStyle = makeStyle(stroke=(150,150,150), fill=(150, 150, 150), strokeWeight=2.0)

vertices = [PointE2(0, 0), PointE2(100, 0), PointE2(100, 100), PointE2(0, 100)]
flip_edge = None
old = None


# TODO
#
# 1. Compute the convex hull of the polygon defined by `vertices` in the draw
#    function and draw it in a light gray. (See koebe.algorithms.convexHullE2)
# 2. Add a function that finds an edge of the convex hull that is not
#    part of the polygon, and returns the indices of the two vertices
#    of that edge. Call this function `find_chull_edge()`. It will be helpful here
#    to have the same orientation of two polygons, which you can get with ccwOrientation()

def find_chull_edge(vertices):
    global flip_edge
    hull = convex_hull(vertices).ccwOrientation()
    vertices2 = PolygonE2(vertices).ccwOrientation().vertices
    temp = set([(vertices2[i], vertices2[(i+1)%len(vertices2)]) for i in range(len(vertices2))])
    hv = hull.vertices
    for i in range(len(hv)):
        v = (hv[i], hv[(i+1)%len(hv)])
        if v not in temp:
            flip_edge = v
            return
    flip_edge = None




def redraw():
    global graph_editor_scene, vertices, edges, old
    graph_editor_scene.clear()
    
    ch = convex_hull(vertices)
    graph_editor_scene.add(ch,greyStyle)
    # Draw polygon
    graph_editor_scene.addAll([(SegmentE2(vertices[i], vertices[(i + 1) % len(vertices)]), blackStyle) for i in range(len(vertices))])

    # Draw vertices
    graph_editor_scene.addAll([(vertices[i], blackStyle if i != selected_vertex_idx and i != selected_end_vertex_idx else redStyle) for i in range(len(vertices))])
    if flip_edge:
        p,q = flip_edge
        graph_editor_scene.add(SegmentE2(p, q), redStyle)
    if old:
        graph_editor_scene.addAll([(SegmentE2(old[i], old[i + 1]), blueStyle) for i in range(len(old)-1)])

    

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

# 3. When the user clicks the 'f' key, flip the vertices across the chain of the 
#    polygon edge returned by find_chull_edge. Show the old flip edge in red, 
#    the old chain in blue, and the new chain in black.
def key_released(key):
    global option_key_down, mode, selected_vertex_idx, flip_edge, vertices, old
    if key == "Option" or key == "Alt":
        option_key_down = False
    elif key == "v":
        mode = "vertex"
        print("Switched to vertex mode")
    elif key == "f":
        flip_edge = None
        find_chull_edge(vertices)
        if flip_edge:
            #do flip stuff
            do_flip()
            redraw()
        if not flip_edge:
            print("Done")
    elif key == "c":
        ctr = (-1 / len(vertices)) * sum([VectorE2(p.x, p.y) for p in vertices], VectorE2(0,0))
        vertices = [p + ctr for p in vertices]
        if flip_edge:
            flip_edge = flip_edge[0]+ctr, flip_edge[1]+ctr
        if old:
            old = [p + ctr for p in old]
        redraw()


def do_flip():
    global vertices, old, flip_edge
    p,q = flip_edge
    pidx, qidx = vertices.index(p), vertices.index(q)
    start, end = min(pidx, qidx), max(pidx, qidx)
    old = vertices[start:end+1]
    flipper = SegmentE2(p, q)
    for i in range(start+1, end):
        vertices[i] = flipper.reflect(vertices[i])


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