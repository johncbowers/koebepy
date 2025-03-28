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
print("\tdone.")

print("Computing a circle packing... ")
I1 = DiskS2(1, 0, 0, 0)

dists = [(v.data - PointE3.O).normSq() for v in tutteGraph.verts]
closestToOriginIdx = dists.index(min(dists))
hyp_packing, _ = maximalPacking(
    tutteGraph, 
    num_passes=n_iterations, 
    centerDartIdx = tutteGraph.darts.index(tutteGraph.verts[closestToOriginIdx].aDart)
)
packing = canonical_spherical_projection(hyp_packing)
packing.markIndices()
print("\tdone.")

compute_tangencies(packing)

# Compute an unfolding
unfolding = packing.duplicate(vdata_transform=lambda _: None, edata_transform=lambda _: None)
unfolding.markIndices()

print(f"Placing vertex {0} ")
unfolding.verts[0].data = CircleE2(PointE2(0, 0), packing.verts[0].data.radiusE3)
nbsS2 = packing.verts[0].neighbors()
edgesS2 = packing.verts[0].edges()
nbsE2 = unfolding.verts[0].neighbors()

# initialize the unfolding parent for each vertex to None
for v in unfolding.verts:
    v.parent = None

# Place the first neighbor
nbsE2[0].data = CircleE2(PointE2(unfolding.verts[0].data.radius + nbsS2[0].data.radiusE3, 0), nbsS2[0].data.radiusE3)
nbsE2[0].parent = unfolding.verts[0]

n = packing.verts[0].data.basis3.normalize()
# Place the rest of the neighbors
for i in range(1, len(nbsE2)):
    v0 = edgesS2[0].data.toVectorE3() - packing.verts[0].data.centerE3
    vi = edgesS2[i].data.toVectorE3() - packing.verts[0].data.centerE3
    print(f"Placing vertex {nbsS2[i].idx} with parent 0")
    theta = math.atan2(v0.cross(vi).dot(n), v0.dot(vi))
    nbsE2[i].data = CircleE2(
        PointE2(
            (packing.verts[0].data.radiusE3 + nbsS2[i].data.radiusE3) * math.cos(theta),
            (packing.verts[0].data.radiusE3 + nbsS2[i].data.radiusE3) * math.sin(theta)
        ),
        nbsS2[i].data.radiusE3
    )
    nbsE2[i].parent = unfolding.verts[0]

# Project all edge data points onto the line through the origin in direction n
for e in packing.edges:
    v = e.data - PointE3.O
    e.key = -v.dot(n)
    
# Create a min priority queue of edge.data keyed by key.data for all edges
pq = [(e.key, random(), e) for e in packing.edges]
heapq.heapify(pq)

# While the queue is not empty remove min and process
while len(pq) > 0:
    _, _, e = heapq.heappop(pq)
    v0_idx, v1_idx = [v.idx for v in e.endPoints()]

    v0 = unfolding.verts[v0_idx]
    v1 = unfolding.verts[v1_idx]
    if v0.data == None and v1.data == None:
        print("Can't place edge because neither endpoint is placed. This should never happen.")
        continue
    if v0.data == None:
        v0, v1 = v1, v0
        v0_idx, v1_idx = v1_idx, v0_idx
    
    if v1.data == None:
        # now v0 has been placed and we need to place v1
        print(f"Placing vertex {v1_idx} with parent {v0_idx}")
        if v0.parent == None:
            print(f"v0 has no parent, this should not happen. v0's index is {v0_idx}")
            break
        parent_idx = v0.neighbors().index(v0.parent)
        parent_dirE2 = (v0.parent.data.center - v0.data.center).normalize()
        
        parent_dirS2 = packing.verts[v0_idx].data.tangentPointWith(packing.verts[v0.parent.idx].data).toVectorE3() - packing.verts[v0_idx].data.centerE3
        v1_dirS2 = packing.verts[v0_idx].data.tangentPointWith(packing.verts[v1_idx].data).toVectorE3() - packing.verts[v0_idx].data.centerE3
        n = packing.verts[v0_idx].data.basis3.normalize()
        theta = math.atan2(parent_dirS2.cross(v1_dirS2).dot(n), parent_dirS2.dot(v1_dirS2))
        
        v = parent_dirE2.rotate(theta).normalize()
        v1.data = CircleE2(
            v0.data.center + (packing.verts[v0_idx].data.radiusE3 + packing.verts[v1_idx].data.radiusE3) * v,
            packing.verts[v1_idx].data.radiusE3
        )
        v1.parent = v0

inversive_distances_sphere = []
inversive_distances_plane = []
for i in range(len(unfolding.verts)-1):
    for j in range(i+1, len(unfolding.verts)):
        if unfolding.verts[j].parent != unfolding.verts[i] and unfolding.verts[i].parent != unfolding.verts[j] and unfolding.verts[i].data != None and unfolding.verts[j].data != None:
            inversive_distances_sphere.append(packing.verts[i].data.inversiveDistTo(packing.verts[j].data))
            inversive_distances_plane.append(unfolding.verts[i].data.inversiveDistTo(unfolding.verts[j].data))

for i in range(len(inversive_distances_plane)):
    if inversive_distances_plane[i] < inversive_distances_sphere[i]:
        print(f"{i} {inversive_distances_plane[i]} {inversive_distances_sphere[i]} {inversive_distances_plane[i] - inversive_distances_sphere[i]} {inversive_distances_plane[i] > inversive_distances_sphere[i]}")


print(f"Passes inversive distance test: {not (False in [inversive_distances_plane[i] > inversive_distances_sphere[i] for i in range(len(inversive_distances_plane))])}")
print(f"Minimum inversive distance detected in the sphere: {min(inversive_distances_sphere)}")
print(f"Minimum inversive distance detected in the plane: {min(inversive_distances_plane)}")

# Create segments for the child-parent relationships: 
segsE2 = []
for v in unfolding.verts:
    if v.parent is not None:
        segsE2.append(SegmentE2(v.data.center, v.parent.data.center))

segsE3 = []
for v in unfolding.verts:
    if v.parent is not None:
        segsE3.append(SegmentE3(packing.verts[v.idx].data.basis3.normalize().toPointE3(), 
                                packing.verts[v.parent.idx].data.basis3.normalize().toPointE3()))

# Put together the visualization

blackStyle = makeStyle(stroke=(0,0,0))
redStyle = makeStyle(stroke=(255,0,0), strokeWeight=2, fill=None)
greenStyle = makeStyle(stroke=(0,255,0), strokeWeight=2, fill=None)
blueStyle = makeStyle(stroke=(0,0,255), strokeWeight=2, fill=None)
grayStyle = makeStyle(stroke=(128,128,128), strokeWeight=0.5, fill=None)

sceneS2 = S2Scene(title="Coin polyhedron", show_sphere=False)
sceneE2 = E2Scene(title="Proposed unfolding", scale=1.5, height=800, width=800, pan_and_zoom=True)

sceneS2.addAll([(v.data, redStyle if v.idx == 0 else greenStyle if v.idx == nbsE2[0].idx else blueStyle if v.idx == nbsE2[1].idx else blackStyle) for v in packing.verts])
sceneS2.addAll([(s, grayStyle) for s in segsE3])


scale = 100
sceneE2.addAll([(scale * v.data, redStyle if v.idx == 0 else greenStyle if v.idx == nbsE2[0].idx else blueStyle if v.idx == nbsE2[1].idx else blackStyle) for v in unfolding.verts if v.data is not None])
#sceneE2.addAll([e.data for e in unfolding.edges if e.data is not None])
sceneE2.addAll([(scale * s, grayStyle) for s in segsE2])

viewer.add_scene(sceneS2)
viewer.add_scene(sceneE2)

viewer.run()

