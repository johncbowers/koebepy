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
scale = 250

print(f"Generating random convex hull of {n_points} points and computing a Tutte embedding... ")
poly = randomConvexHullE3(n_points) # Generate a random polyhedron with 16 vertices. 
poly.outerFace = poly.faces[0] # Arbitrarily select an outer face. 
tutteGraph = tutteEmbeddingE2(poly) # Compute the tutte embedding of the polyhedron. 

frames = []

for th in [2*math.pi*x/600 for x in range(601)]:
    l = (math.cos(th)+1)/2
    for edge in tutteGraph.edges:
        w = (1-l)*1 + l*edge.u.data.distTo(edge.v.data)
        edge.dart1.data = w
        edge.dart2.data = w
    weightedTutteGraph = tutteEmbeddingE2(tutteGraph, weighted=True) 
    frames.append([SegmentE2(e.u.data * scale, e.v.data * scale) for e in weightedTutteGraph.edges])

print("\tdone.")

# Extract Geometry

# tutte_segs = [SegmentE2(e.u.data * scale, e.v.data * scale) for e in tutteGraph.edges]
# weighted_tutte_segs = [SegmentE2(e.u.data * scale, e.v.data * scale) for e in weightedTutteGraph.edges]

blackStyle = makeStyle(stroke=(0,0,0))
redStyle = makeStyle(stroke=(255,0,0), strokeWeight=2, fill=None)
greenStyle = makeStyle(stroke=(0,255,0), strokeWeight=2, fill=None)
blueStyle = makeStyle(stroke=(0,0,255), strokeWeight=2, fill=None)
grayStyle = makeStyle(stroke=(128,128,128), strokeWeight=0.5, fill=None)

sceneE2 = E2Scene(title="Tutte Embeddings", scale=1.5, height=800, width=800, pan_and_zoom=True)

# sceneE2.addAll(tutte_segs)
# sceneE2.addAll([(s, redStyle) for s in weighted_tutte_segs])

for frame in frames[:-1]:
    sceneE2.addAll(frame)
    sceneE2.pushAnimFrame()
sceneE2.addAll(frames[-1])

viewer.add_scene(sceneE2)

viewer.run()