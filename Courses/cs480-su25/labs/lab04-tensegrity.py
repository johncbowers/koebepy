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

tensegrity_scene = S2Scene(title="Tensegrity")

blackStyle = makeStyle(stroke=(0,0,0), fill=(255, 255, 255))
redStyle = makeStyle(stroke=(255,0,0), fill=(255, 255, 255), strokeWeight=2.0)
blueStyle = makeStyle(stroke=(0,0,255), fill=(255, 255, 255), strokeWeight=2.0)

# TODO
# 1. Build the 3D rigidity matrix for the tensegrity structure (see lab from last time)
# 2. Calculate the null space for the transpose of the rigidity matrix. You should get a
#    one dimensional null space. 
# 3. Each entry corresponds to an edge. If the value is positive, show the edge in blue, 
#    if it is negative, show the edge in red. If it is zero, show the edge in black.

tensegrity_scene.addAll([SegmentE3(vertices[i], vertices[j]) for i, j in edges])

tensegrity_scene.toggleSphere()
viewer.add_scene(tensegrity_scene)
viewer.run()