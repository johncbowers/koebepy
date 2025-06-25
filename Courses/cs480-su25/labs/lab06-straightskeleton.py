from koebe.geometries.euclidean2 import *

from math import *
from random import *
from collections import deque

from koebe.graphics.flask.multiviewserver import viewer, set_key_pressed_handler, set_key_released_handler
from koebe.graphics.scenes.euclidean2scene import E2Scene, makeStyle

blackStyle = makeStyle(stroke=(0,0,0), fill=(255, 255, 255))
redStyle = makeStyle(stroke=(255,0,0), fill=(255, 0, 0), strokeWeight=2.0)

vertices = [PointE2(0, 0), PointE2(100, 0), PointE2(100, 100), PointE2(0, 100)]


blackStyle = makeStyle(stroke=(0,0,0), fill=(255, 255, 255))
redStyle = makeStyle(stroke=(255,0,0), fill=(255, 0, 0), strokeWeight=2.0)
blueStyle = makeStyle(stroke=(0,0,255), fill=(255, 0, 0), strokeWeight=2.0)
greyStyle = makeStyle(stroke=(128,128,128), fill=None, strokeWeight=2.0)
vertices = [PointE2(0, 0), PointE2(100, 0), PointE2(100, 150), PointE2(0, 100)]

def vertex_bisector_vector(polygon, idx):
    """
    Returns a normalized vector pointing along the angle bisector. 
    """
    return None

def vertex_angle(polygon, idx):
    """
    Return the angle measure at the vertex. 
    """
    return None

def advance_vertex(polygon, idx, height):
    """
    Advances the vertex along the sweep such that it has moved a perpendicular distance of
    height.
    """
    return None

def vertex_bisector_line(polygon, idx):
    """
    Returns a LineE2 object representing the angle bisector.
    """
    return None

def edge_contraction_point(polygon, idx):
    """
    Calculates the point where the edge from vertex idx to (idx + 1) % len(polygon.vertices)
    contracts. This is at the intersection of the bisector lines of the two vertices.
    """
    return None

def edge_perpendicular_segment(polygon, idx):
    """
    Returns the line segment from the contraction point to the nearest point on the edge. 
    The length of this segment will be used to find the contraction events.
    """
    return None

def next_contraction_event(polygon):
    """
    Returns min_idx, min_distance where min_idx is the index of the edge with the next
    contraction event and min_distance is the distance the sweep needs to move to get there.
    """
    return -1, float('inf')  # Placeholder implementation

def advance_polygon(polygon):
    """
    Advances the polygon to the next contraction event. 
    Returns the Polygon and the index of the edge that was contracted.
    """
    return None, -1

# TODO
# 
# 1. Implement the functions above to compute the next contraction event and advance the polygon.
# 2. Show the contraction events as red points and a perpendicular segment from each contraction edge to 
# the polygon edge that contracts to it.
# 3. Advance the polygon to the first contraction event and draw it gray.

def redraw():
    global graph_editor_scene, vertices, edges
    graph_editor_scene.clear()
    
    # Draw polygon
    is_convex = PolygonE2(vertices).isConvex()
    graph_editor_scene.addAll([(SegmentE2(vertices[i], vertices[(i + 1) % len(vertices)]), blackStyle if is_convex else redStyle) for i in range(len(vertices))])

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