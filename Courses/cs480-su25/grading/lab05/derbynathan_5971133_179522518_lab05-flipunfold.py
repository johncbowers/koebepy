from koebe.geometries.euclidean2 import *

from math import *
from random import *
from collections import deque

from koebe.graphics.flask.multiviewserver import viewer, set_key_pressed_handler, set_key_released_handler
from koebe.graphics.scenes.euclidean2scene import E2Scene, makeStyle
from koebe.algorithms.convexHullE2 import *

blackStyle = makeStyle(stroke=(0,0,0), fill=(255, 255, 255), strokeWeight=4.0)
redStyle = makeStyle(stroke=(255,0,0), fill=(255, 0, 0), strokeWeight=2.0)
blueStyle = makeStyle(stroke=(0,0,255), fill=(0, 0, 255), strokeWeight=2.0)
grayStyle = makeStyle(stroke=(150, 150, 150), fill=(200, 200, 200), strokeWeight=0.5)

vertices = [PointE2(0, 0), PointE2(100, 0), PointE2(100, 100), PointE2(0, 100)]

def find_chull_edge():
    global vertices 
    if len(vertices) < 3:
        return None, None
        
    chull = convex_hull(vertices).ccwOrientation()
    
    # Create a set of polygon edges for fast lookup
    polygon_edges = set()
    for i in range(len(vertices)):
        v1_idx = i
        v2_idx = (i + 1) % len(vertices)
        # Store the actual vertex objects as tuples for comparison
        edge = (vertices[v1_idx], vertices[v2_idx])
        polygon_edges.add(edge)
        polygon_edges.add((vertices[v2_idx], vertices[v1_idx]))  # Both directions
    
    # Check each edge of the convex hull
    for i in range(len(chull.vertices)):
        v1 = chull.vertices[i]
        v2 = chull.vertices[(i + 1) % len(chull.vertices)]
        
        # Check if this convex hull edge is NOT part of the polygon
        if (v1, v2) not in polygon_edges:
            # Find the indices of these vertices in the original vertices list
            try:
                idx1 = vertices.index(v1)
                idx2 = vertices.index(v2)
                return (v1, v2), (idx1, idx2)  # Return both vertex objects and indices
            except ValueError:
                continue
    
    # If no edge found, return None
    return None, None

# Global variables to store flip state
flip_edge_segment = None
old_chain_segments = []

def redraw():
    global graph_editor_scene, vertices, flip_edge_segment, old_chain_segments
    graph_editor_scene.clear()

    # Draw convex hull in light gray
    if len(vertices) >= 3:
        chull = convex_hull(vertices)
        graph_editor_scene.add(chull, grayStyle)

    # Draw polygon edges
    graph_editor_scene.addAll([(SegmentE2(vertices[i], vertices[(i + 1) % len(vertices)]), blackStyle) for i in range(len(vertices))])

    # Draw the flip edge in red if it exists
    if flip_edge_segment:
        graph_editor_scene.add(flip_edge_segment, redStyle)
    
    # Draw the old chain segments in blue if they exist
    for segment in old_chain_segments:
        graph_editor_scene.add(segment, blueStyle)

    # Draw vertices
    graph_editor_scene.addAll([(vertices[i], blackStyle if i != selected_vertex_idx and i != selected_end_vertex_idx else redStyle) for i in range(len(vertices))])

mode = "vertex"  # or "edge"
selected_vertex_idx = -1
selected_end_vertex_idx = -1
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
    global graph_editor_scene, vertices, mode, option_key_down, selected_vertex_idx, mouse_position

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
    global option_key_down, mode, selected_vertex_idx, vertices, flip_edge_segment, old_chain_segments
    if key == "Option" or key == "Alt":
        option_key_down = False
    elif key == "v":
        mode = "vertex"
        print("Switched to vertex mode")
        # Clear flip visualization when switching modes
        flip_edge_segment = None
        old_chain_segments = []
        redraw()
    elif key == "f":
        mode = "flip"
        print("Flipping...")
        
        # Clear previous flip visualization
        flip_edge_segment = None
        old_chain_segments = []
        
        # Find an edge of the convex hull that is not part of the polygon
        edge_vertices, edge_indices = find_chull_edge()
        
        if edge_vertices is not None and edge_indices is not None:
            v1, v2 = edge_vertices
            idx1, idx2 = edge_indices
            
            print(f"Found convex hull edge to flip: {idx1} -> {idx2}")
            
            # Store the flip edge for visualization
            flip_edge_segment = SegmentE2(v1, v2)
            
            # Try going forward from idx1 to idx2
            chain_forward = []
            current = (idx1 + 1) % len(vertices)
            while current != idx2:
                chain_forward.append(current)
                current = (current + 1) % len(vertices)
            
            # Try going backward from idx1 to idx2
            chain_backward = []
            current = (idx1 - 1) % len(vertices)
            while current != idx2:
                chain_backward.append(current)
                current = (current - 1) % len(vertices)
            
            # Choose the shorter chain (this should be the one inside the polygon)
            if len(chain_forward) <= len(chain_backward):
                chain_indices = chain_forward
            else:
                chain_indices = chain_backward
            
            print(f"Chain to flip: {chain_indices}")
            
            # Store the old chain segments for visualization
            if chain_indices:
                # Add segment from idx1 to first chain vertex
                old_chain_segments.append(SegmentE2(vertices[idx1], vertices[chain_indices[0]]))
                
                # Add segments between chain vertices
                for i in range(len(chain_indices) - 1):
                    old_chain_segments.append(SegmentE2(vertices[chain_indices[i]], vertices[chain_indices[i + 1]]))
                
                # Add segment from last chain vertex to idx2
                old_chain_segments.append(SegmentE2(vertices[chain_indices[-1]], vertices[idx2]))
            
            # Flip only the vertices in the chain across the convex hull edge
            flip_edge = SegmentE2(v1, v2)
            for chain_idx in chain_indices:
                vertices[chain_idx] = flip_edge.reflect(vertices[chain_idx])
            
            redraw()
        else:
            print("No convex hull edge found that's not part of the polygon")

graph_editor_scene = E2Scene(title="Polygon Editor")

graph_editor_scene.set_mouse_pressed(mouse_pressed)
graph_editor_scene.set_mouse_dragged(mouse_dragged)
graph_editor_scene.set_mouse_released(mouse_released)

set_key_pressed_handler(key_pressed)
set_key_released_handler(key_released)

viewer.add_scene(graph_editor_scene)

redraw()
viewer.run()