from koebe.geometries.euclidean3 import *
from math import *
from koebe.graphics.flask.multiviewserver import viewer, set_key_pressed_handler, set_key_released_handler
from koebe.graphics.scenes.spherical2scene import S2Scene, makeStyle

import numpy as np
from scipy.linalg import null_space

# vertices of an equilateral triangle in the z=-0.5 plane
vertices = [
    PointE3( 1, -1/sqrt(3), -0.5),
    PointE3(-1, -1/sqrt(3), -0.5), 
    PointE3( 0,  2/sqrt(3), -0.5), 
    PointE3( 2 / sqrt(3), 0, 0.5),
    PointE3(-1 / sqrt(3), -1, 0.5), 
    PointE3(-1 / sqrt(3), 1, 0.5)
]

edges = [
    [0, 1], [1, 2], [2, 0],  # base triangle
    [3, 4], [4, 5], [5, 3],  # top triangle
    [0, 3], [1, 4], [2, 5],   # vertical edges connecting base to top
#    [0, 4], [1, 5], [2, 3]    # diagonal edges connecting base to top
    [0, 5], [1, 3], [2, 4]    # diagonal edges connecting base to top
]

pin_edge_idx = 0

tensegrity_scene = S2Scene(title="Tensegrity")

blackStyle = makeStyle(stroke=(0,0,0), fill=(255, 255, 255))
redStyle = makeStyle(stroke=(255,0,0), fill=(255, 255, 255), strokeWeight=2.0)
blueStyle = makeStyle(stroke=(0,0,255), fill=(255, 255, 255), strokeWeight=2.0)

# TODO
# 1. Build the 3D rigidity matrix for the tensegrity structure (see lab from last time)

def rigidity_matrix_row(i, j):
    global vertices
    row = [(0, 0, 0) for _ in vertices]
    row[i] = tuple(vertices[j]-vertices[i])
    row[j] = tuple(vertices[i]-vertices[j])
    return np.array(row).flatten()

# def pinning_rows(i):
#     global vertices
#     row1= [(0,0) for _ in vertices]
#     row2 = [(0,0) for _ in vertices]
#     row1[i] = (1, 0)
#     row2[i] = (0, 1)
#     return [row1, row2]

def rigidity_matrix():
    global edges, pin_edge_idx
    edge_rows = [rigidity_matrix_row(i, j) for i, j in edges]
    i, j = edges[pin_edge_idx]
    R = edge_rows
    # + pinning_rows(i) + pinning_rows(j)
    return np.array(
        [np.array(row).flatten() for row in R]
    )

# 2. Calculate the null space for the transpose of the rigidity matrix. You should get a
#    one dimensional null space. 

R = rigidity_matrix()
ns = null_space(R.T) 

# 3. Each entry corresponds to an edge. If the value is positive, show the edge in blue, 
#    if it is negative, show the edge in red. If it is zero, show the edge in black.

for idx, (i, j) in enumerate(edges):
    edge_value = ns[idx][0]

    if edge_value < 0:
        style = redStyle
    if edge_value > 0:
        style = blueStyle
    else:
        style = blackStyle

    tensegrity_scene.add(SegmentE3(vertices[i], vertices[j]), style)

# tensegrity_scene.addAll([SegmentE3(vertices[i], vertices[j]) for i, j in edges])

tensegrity_scene.toggleSphere()
viewer.add_scene(tensegrity_scene)
viewer.run()