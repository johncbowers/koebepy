# Import geometries
from koebe.algorithms.circlepackings.layout import canonical_spherical_projection, compute_tangencies
from koebe.geometries.spherical2 import *
from koebe.geometries.euclidean2 import *
from koebe.geometries.euclidean3 import *
from koebe.geometries.orientedProjective2 import *

# Import convex hull, circle packing, and tutte embedding algorithms
from koebe.algorithms.incrementalConvexHull import incrConvexHull, orientationPointE3, randomConvexHullE3
from koebe.algorithms.hypPacker import *
from koebe.algorithms.tutteEmbeddings import tutteEmbeddingE2

# General imports
from math import *
from random import *
import heapq

# Scene and Visualization libraries
from koebe.graphics.flask.multiviewserver import viewer
from koebe.graphics.scenes.spherical2scene import S2Scene, makeStyle
from koebe.graphics.scenes.euclidean2scene import E2Scene

n_points = 100
n_iterations = 10000

print(f"Generating random convex hull of {n_points} points and computing a Tutte embedding... ")
poly = randomConvexHullE3(n_points) # Generate a random polyhedron with 16 vertices. 
poly.outerFace = poly.faces[0] # Arbitrarily select an outer face. 
tutteGraph = tutteEmbeddingE2(poly) # Compute the tutte embedding of the polyhedron. 

tutteGraph = tutteGraph.duplicate(vdata_transform=lambda p: PointE2(p.x * 100, p.y * 100))

print("\tdone.")

blackStyle = makeStyle(stroke=(0,0,0))
redStyle = makeStyle(stroke=(255,0,0), strokeWeight=2, fill=None)
greenStyle = makeStyle(stroke=(0,255,0), strokeWeight=2, fill=None)
blueStyle = makeStyle(stroke=(0,0,255), strokeWeight=2, fill=None)
grayStyle = makeStyle(stroke=(128,128,128), strokeWeight=0.5, fill=None)

sceneS2 = S2Scene(title="Coin polyhedron", show_sphere=False)

sceneS2.add(poly)
sceneE2 = E2Scene(title="Proposed unfolding", scale=1.5, height=800, width=800, pan_and_zoom=True)

scale = 100


sceneE2.add(tutteGraph)
#sceneS2.addAll([(v.data, redStyle if v.idx == 0 else greenStyle if v.idx == nbsE2[0].idx else blueStyle if v.idx == nbsE2[1].idx else blackStyle) for v in packing.verts])
#sceneS2.addAll([(s, grayStyle) for s in segsE3])


# scale = 100
# sceneE2.addAll([(scale * v.data, redStyle if v.idx == 0 else greenStyle if v.idx == nbsE2[0].idx else blueStyle if v.idx == nbsE2[1].idx else blackStyle) for v in unfolding.verts if v.data is not None])
# #sceneE2.addAll([e.data for e in unfolding.edges if e.data is not None])
# sceneE2.addAll([(scale * s, grayStyle) for s in segsE2])

viewer.add_scene(sceneS2)
viewer.add_scene(sceneE2)

viewer.run()